"""Genera el diccionario de datos (docs/diccionario_datos.md + datalake/catalogo/diccionario.json) a partir de:
fuentes (config), linaje de bronze, esquema de silver (esquema.py) y los archivos gold realmente publicados.
"""
import json
from collections import defaultdict

from pipelines import config
from pipelines.esquema import ESQUEMA
from pipelines.lib import lago

ESTADOS = {
    "observado": "Valor publicado o medido por la fuente, sin transformación más allá de filtrado y tipado.",
    "derivado": "Cálculo propio sobre datos observados (tasas, densidades, promedios, índices). La fórmula se documenta.",
    "modelo": "Salida de un modelo, no una medición: reanálisis ERA5, pronóstico de Open-Meteo y calidad del aire CAMS.",
    "bajo_costo": "Medición de sensores ciudadanos de bajo costo (Sensor.Community, openSenseMap), sin calibración oficial; instantánea en vivo.",
    "en_vivo": "Instantánea del momento de ingesta de una fuente en tiempo real; cambia en cada ejecución.",
    "proxy": "Indicador indirecto de un fenómeno que no se mide directamente.",
}

GEO_CAPAS = {
    "distritos.geojson": ("MultiPolygon", "23 distritos simplificados (~13 m) con todas las métricas del atlas y score_<dimensión> 0–100", "distritos + métricas gold"),
    "paradas.geojson": ("Point", "n nombre · s salidas día ref. · r rutas · m modos · d distrito", "gtfs_paradas"),
    "lineas.geojson": ("LineString", "modo · linea · color", "gtfs_lineas_geom"),
    "bubi.geojson": ("Point", "n nombre · b bicicletas y c anclajes (solo si F07 está integrada) · o origen (osm | nextbike_vivo) · d distrito", "bubi_estaciones + bubi_disponibilidad"),
    "sensores.geojson": ("Point", "f fuente (sensor_community|opensensemap) · id · pm25 · pm10 · t temperatura · ts · d distrito. Coordenadas redondeadas a 3 decimales (~110 m) y sin nombre de caja para no exponer viviendas", "sc_sensores + osem_sensores"),
    "eea.geojson": ("Point", "estacion · nombre · tipo · area · PM25 · PM10 · NO2 · O3 (último año) · anio", "eea_estaciones + eea_estadisticas"),
    "poi.geojson": ("Point", "c categoría · s subcategoría OSM · n nombre · d distrito", "osm_poi"),
}


def _md_tabla(cab, filas):
    esc = lambda v: str("" if v is None else v).replace("|", "\\|").replace("\n", " ")
    return "\n".join(["| " + " | ".join(cab) + " |", "|" + "---|" * len(cab)] + ["| " + " | ".join(esc(c) for c in f) + " |" for f in filas])


def generar(con):
    lin = []
    p = config.CATALOGO / "linaje.jsonl"
    if p.exists():
        lin = [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
    ultimo = {}
    for l in lin:  # última versión de cada archivo lógico (sin la carpeta de fecha)
        partes = l["archivo"].split("/")
        clave = (l["fuente"], "/".join(partes[3:]))
        ultimo[clave] = l
    bronze = defaultdict(list)
    for (fid, nombre), l in sorted(ultimo.items()):
        bronze[fid].append(l | {"nombre": nombre})

    temas = {}
    for f in sorted((config.GOLD / "temas").glob("*.json")):
        temas[f.stem] = json.loads(f.read_text(encoding="utf-8"))

    out = ["# Diccionario de datos · Cerebro Budapest", "",
           f"Generado automáticamente el {lago.HOY} por `pipelines/diccionario.py` a partir del catálogo real del lago "
           "(no se edita a mano: se regenera en cada ejecución del pipeline).", "",
           "## 1. Convenciones", "",
           "- **Territorio**: Budapest (NUTS2 `HU11`, NUTS3 `HU110`, ciudad Urban Audit `HU001C`), 23 distritos (*kerületek*) identificados por `distrito_id` 1–23.",
           "- **Coordenadas**: WGS84 (EPSG:4326), grados decimales. Superficies en km² salvo que se indique ha.",
           "- **Fechas**: ISO 8601. `vigencia` = periodo al que se refiere el dato; `probado` = fecha en que el lago lo verificó.",
           "- **Zonas del lago**: `bronze` (crudo, inmutable, particionado `bronze/<fuente>/<AAAA-MM-DD>/`), `silver` (SQLite tipado), `gold` (temas JSON y GeoJSON para el sitio), `catalogo` (linaje, estado, diccionario).",
           "", "### Estados de una cifra", "", _md_tabla(["estado", "significado"], ESTADOS.items()), "",
           "## 2. Fuentes", "",
           _md_tabla(["id", "fuente", "organismo", "acceso", "licencia", "frecuencia", "URL"],
                     [(k, f["nombre"], f["organismo"], f["acceso"], f["licencia"], f["frecuencia"], f["url"]) for k, f in config.FUENTES.items()]),
           "", "## 3. Bronze · archivos crudos", "",
           "Cada descarga se escribe tal cual llega y se registra en `datalake/catalogo/linaje.jsonl` con URL, bytes y sha256.", ""]
    for fid in config.FUENTES:
        if not bronze.get(fid):
            continue
        out += [f"### `{fid}`", "", _md_tabla(["archivo", "bytes", "ingesta", "origen"],
                                              [(b["nombre"], f"{b['bytes']:,}".replace(",", "."), b["ts"][:16], b["url"][:140]) for b in bronze[fid][:40]]), ""]
        if len(bronze[fid]) > 40:
            out += [f"… y {len(bronze[fid]) - 40} archivos más del mismo patrón.", ""]

    out += ["## 4. Silver · tablas (datalake/silver/budapest.sqlite)", ""]
    dic_silver = {}
    for tabla, meta in ESQUEMA.items():
        n = con.execute(f"SELECT COUNT(*) FROM {tabla}").fetchone()[0] if lago.tabla_existe(con, tabla) else 0
        dic_silver[tabla] = {**meta, "filas": n, "columnas": [dict(zip(("nombre", "tipo", "unidad", "descripcion"), c)) for c in meta["columnas"]]}
        out += [f"### `{tabla}` · {n:,} filas".replace(",", "."), "", f"{meta['descripcion']}  ",
                f"**Fuente:** `{meta['fuente']}` · **Grano:** {meta['grano']}", "",
                _md_tabla(["columna", "tipo", "unidad", "descripción"], meta["columnas"]), ""]

    out += ["## 5. Gold · temas del sitio (datalake/gold/temas/*.json)", "",
            "Estructura común: `{tema, titulo, probado, fuentes[], cifras{}, series{}, listas{}}`.", ""]
    dic_gold = {}
    for nombre, t in temas.items():
        dic_gold[nombre] = {"cifras": {}, "series": {}, "listas": {}}
        out += [f"### `{nombre}.json` · {t.get('titulo', '')}", ""]
        if t.get("cifras"):
            filas = []
            for k, c in t["cifras"].items():
                filas.append((k, c["etiqueta"], c.get("unidad", ""), c["fuente"], c["estado"], c.get("vigencia", ""), c.get("nota", "")))
                dic_gold[nombre]["cifras"][k] = {x: c.get(x) for x in ("etiqueta", "unidad", "fuente", "estado", "vigencia", "nota")}
            out += ["**Cifras**", "", _md_tabla(["clave", "etiqueta", "unidad", "fuente", "estado", "vigencia", "nota"], filas), ""]
        if t.get("series"):
            filas = []
            for k, s in t["series"].items():
                nombres = ", ".join(x["nombre"] for x in s.get("series", [])) or "—"
                filas.append((k, s["etiqueta"], s.get("unidad", ""), s["fuente"], len(s["puntos"]), s.get("vigencia", ""), nombres))
                dic_gold[nombre]["series"][k] = {"etiqueta": s["etiqueta"], "unidad": s.get("unidad"), "fuente": s["fuente"], "vigencia": s.get("vigencia")}
            out += ["**Series** (`puntos` = `[[x, y], …]`; con varias series, `series[].puntos`)", "",
                    _md_tabla(["clave", "etiqueta", "unidad", "fuente", "puntos", "rango", "subseries"], filas), ""]
        if t.get("listas"):
            filas = []
            for k, l in t["listas"].items():
                cols = sorted({c for fila in l for c in (fila.keys() if isinstance(fila, dict) else [])}) if l else []
                filas.append((k, len(l), ", ".join(cols)[:300]))
                dic_gold[nombre]["listas"][k] = {"filas": len(l), "columnas": cols}
            out += ["**Listas**", "", _md_tabla(["clave", "filas", "columnas"], filas), ""]

    d = temas.get("distritos")
    if d:
        out += ["## 6. Métricas por distrito (atlas, correlaciones y diagnóstico)", "",
                "Cada `score_<dimensión>` es el promedio de las métricas de esa dimensión normalizadas min–max 0–100 entre los 23 distritos "
                "(invertidas cuando `sentido = inv`, es decir, cuando menos es mejor). El índice del atlas es el promedio ponderado de los scores con los pesos que elige el usuario.", "",
                _md_tabla(["id", "etiqueta", "unidad", "fuente", "estado", "dimensión", "sentido", "fórmula"],
                          [(m["id"], m["etiqueta"], m["unidad"], m["fuente"], m["estado"], m["dimension"] or "—", m["sentido"] or "—", m["formula"]) for m in d["listas"]["metricas"]]), ""]

    out += ["## 7. Gold · capas geográficas (datalake/gold/geo/*.geojson)", "",
            _md_tabla(["archivo", "geometría", "propiedades", "origen silver", "elementos"],
                      [(k, g, props, src, len(json.loads((config.GOLD / "geo" / k).read_text(encoding="utf-8"))["features"]) if (config.GOLD / "geo" / k).exists() else 0)
                       for k, (g, props, src) in GEO_CAPAS.items()]), "",
            "## 8. Capas de mapa externas (no almacenadas)", "",
            _md_tabla(["capa", "proveedor", "uso"], [
                ("Teselas vectoriales OpenFreeMap (esquema OpenMapTiles)", "OpenFreeMap · datos OSM", "Mapa base oscuro y edificios 3D (render_height)"),
                ("World Imagery", "Esri", "Mapa base satelital"),
                ("HRL Imperviousness Density 2018 (exportImage)", "Copernicus / EEA", "Superposición ráster de suelo sellado"),
                ("HRL Tree Cover Density 2018 (exportImage)", "Copernicus / EEA", "Superposición ráster de arbolado"),
                ("Open-Meteo current", "Open-Meteo", "Clima en vivo en la cabecera del sitio (consulta directa del navegador)"),
            ]), ""]

    config.DOCS.mkdir(parents=True, exist_ok=True)
    (config.DOCS / "diccionario_datos.md").write_text("\n".join(out), encoding="utf-8")
    lago.escribir_json(config.CATALOGO / "diccionario.json", {"generado": lago.HOY, "fuentes": config.FUENTES, "estados": ESTADOS,
                                                             "bronze": {k: [{x: b[x] for x in ("nombre", "bytes", "ts", "url", "sha256")} for b in v] for k, v in bronze.items()},
                                                             "silver": dic_silver, "gold": dic_gold, "geo": {k: {"geometria": g, "propiedades": p, "origen": s} for k, (g, p, s) in GEO_CAPAS.items()}})
    lago.log("diccionario", f"docs/diccionario_datos.md ({len(out)} líneas)")
