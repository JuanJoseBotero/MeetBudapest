"""Capa GOLD: temas JSON y capas GeoJSON que consume el sitio, derivados solo de SILVER.

Contrato de cada tema:
  {tema, titulo, probado, fuentes:[{id,nombre,url,licencia}],
   cifras:{clave:{valor,unidad,etiqueta,fuente,vigencia,estado,nota?}},
   series:{clave:{etiqueta,unidad,fuente,vigencia,puntos:[[x,y]] | series:[{nombre,puntos}], nota?}},
   listas:{clave:[{...}]}}
estado ∈ observado (medido por la fuente) · derivado (cálculo propio sobre datos observados) ·
         modelo (salida de un modelo, no medición: Open-Meteo/ERA5, CAMS) · bajo_costo (sensores ciudadanos de bajo costo,
         sin calibración oficial) · en_vivo (instantánea del momento de ingesta) · proxy.
Las series llevan el mismo campo «estado» para que los gráficos muestren si son medición, modelo o bajo costo.
"""
import datetime as dt
import json
import math
import shutil
import statistics
from collections import Counter, defaultdict

from pipelines import config
from pipelines.lib import geo, lago

T = config.GOLD / "temas"
G = config.GOLD / "geo"


ESTADO = {}  # estado_fuentes.json de la ejecución; lo fija publicar()


# ------------------------------------------------------------------ utilidades
def probada(fid):
    """Fecha (hora local) en que la fuente respondió por última vez: la «fecha en que la probaron» del Excel."""
    if fid == "lago":
        return lago.HOY
    modulo = config.FUENTES.get(fid, {}).get("modulo", fid)
    ts = ESTADO.get(modulo, {}).get("ultima_ingesta")
    return dt.datetime.fromisoformat(ts).astimezone().date().isoformat() if ts else None


def fuente(fid):
    """Ficha de procedencia que el sitio muestra a un clic: ID F, nombre, enlace, licencia y fecha de prueba."""
    if fid == "lago":
        return {"id": "lago", "codigo": "Lago", "nombre": "Cálculo propio del lago sobre las fuentes F02–F14", "url": "",
                "licencia": "—", "probada": lago.HOY, "estado": "ok"}
    f = config.FUENTES[fid]
    modulo = f.get("modulo", fid)
    return {"id": fid, "codigo": f["codigo"], "nombre": f["nombre"], "url": f["url"], "licencia": f["licencia"],
            "probada": probada(fid), "estado": ESTADO.get(modulo, {}).get("estado", "pendiente")}


def completar_fuentes(t):
    """Toda fuente citada por una cifra o serie del tema queda en su lista de fuentes (con ID y fecha de prueba)."""
    usadas = {c["fuente"] for c in t["cifras"].values()} | {x["fuente"] for x in t["series"].values()}
    ya = {f["id"] for f in t["fuentes"]}
    t["fuentes"] += [fuente(f) for f in sorted(usadas - ya)]
    return t


def tema(nombre, titulo, fuentes):
    return {"tema": nombre, "titulo": titulo, "probado": lago.HOY, "fuentes": [fuente(f) for f in fuentes],
            "cifras": {}, "series": {}, "listas": {}}


def etiqueta_periodo(x):
    """2026.25 → '2026-T2'; 2024 → '2024'; textos sin cambio."""
    if isinstance(x, float):
        return f"{int(x)}-T{round((x - int(x)) * 4) + 1}" if x != int(x) else str(int(x))
    return str(x)


def cifra(t, clave, valor, unidad, etiqueta, fid, vigencia, estado="observado", nota=None, decimales=None):
    if valor is None:
        return
    c = {"valor": valor, "unidad": unidad, "etiqueta": etiqueta, "fuente": fid, "vigencia": etiqueta_periodo(vigencia), "estado": estado}
    if nota:
        c["nota"] = nota
    if decimales is not None:
        c["decimales"] = decimales
    t["cifras"][clave] = c


def serie(t, clave, etiqueta, unidad, fid, puntos=None, series=None, nota=None, tipo=None, estado=None):
    ps = puntos or (series[0]["puntos"] if series else [])
    if not ps:
        return
    s = {"etiqueta": etiqueta, "unidad": unidad, "fuente": fid, "vigencia": f"{etiqueta_periodo(ps[0][0])} – {etiqueta_periodo(ps[-1][0])}"}
    if series:
        s["series"] = series
        s["puntos"] = series[0]["puntos"]
    else:
        s["puntos"] = puntos
    if nota:
        s["nota"] = nota
    if tipo:
        s["tipo"] = tipo
    if estado:
        s["estado"] = estado
    t["series"][clave] = s


def r(v, d=1):
    return None if v is None else round(v, d)


def periodo_x(p):
    """'2024' → 2024; '2025-Q2' → 2025.25 (eje continuo)."""
    if "-Q" in p:
        a, q = p.split("-Q")
        return round(int(a) + (int(q) - 1) / 4, 2)
    return int(p) if p.isdigit() else p


def eu(con, clave, **dims):
    """Serie Eurostat [[x, valor]] filtrando por dimensiones exactas."""
    filas = lago.consultar(con, "SELECT periodo, valor, dimensiones, etiqueta FROM eurostat_obs WHERE clave=? ORDER BY periodo", clave)
    out = []
    for f in filas:
        d = json.loads(f["dimensiones"])
        if all(d.get(k) == v for k, v in dims.items()):
            out.append([periodo_x(f["periodo"]), f["valor"]])
    return out


def ultimo(puntos):
    return puntos[-1] if puntos else (None, None)


def ksh(con, indicador, geo_="HU110", sexo="T", edad="TOTAL"):
    return [[f["anio"], f["valor"]] for f in lago.consultar(
        con, "SELECT anio, valor FROM ksh_hvd WHERE indicador=? AND geo=? AND sexo=? AND edad=? ORDER BY anio",
        indicador, geo_, sexo, edad)]


def seguro(con, tabla, sql, *args):
    return lago.consultar(con, sql, *args) if lago.tabla_existe(con, tabla) else []


# ------------------------------------------------------------------ métricas por distrito (base de atlas, correlaciones y diagnóstico)
METRICAS = [
    # id, etiqueta, unidad, fuente, estado, dimensión, dirección (dir: más es mejor para el índice; inv: menos es mejor), fórmula
    ("poblacion", "Población residente", "hab", "ksh", "observado", None, None, "Helységnévtár, lakónépesség al 1 de enero"),
    ("densidad", "Densidad de población", "hab/km²", "ksh", "derivado", "vivienda", "dir", "poblacion / (area_ha_ksh / 100)"),
    ("var_poblacion", "Variación de población (5 años)", "%", "ksh", "derivado", "vivienda", "dir", "(pob_año / pob_año−5 − 1) × 100"),
    ("hab_vivienda", "Habitantes por vivienda", "hab/viv", "ksh", "derivado", None, None, "poblacion / viviendas"),
    ("viviendas_km2", "Viviendas por km²", "viv/km²", "ksh", "derivado", "vivienda", "dir", "viviendas / km²"),
    ("paradas_km2", "Paradas con servicio por km²", "paradas/km²", "bkk_gtfs", "derivado", "movilidad", "dir", "paradas (location_type 0) con ≥1 salida el día de referencia / km²"),
    ("salidas_1000", "Salidas de transporte público por 1.000 hab", "salidas/día", "bkk_gtfs", "derivado", "movilidad", "dir", "Σ stop_times del día laborable de referencia / población × 1.000"),
    ("guiado_pct", "Paradas servidas por modo guiado", "%", "bkk_gtfs", "derivado", "movilidad", "dir", "paradas con metro, tranvía, trolebús o HÉV / paradas con servicio"),
    ("bubi_km2", "Estaciones MOL Bubi por km²", "est/km²", "osm_overpass", "observado", "movilidad", "dir", "estaciones OSM amenity=bicycle_rental de la red MOL Bubi / km²"),
    ("educacion_10k", "Centros educativos por 10.000 hab", "centros", "osm_overpass", "derivado", "servicios", "dir", "POI categoría educacion / población × 10.000"),
    ("salud_10k", "Equipamientos de salud por 10.000 hab", "equip.", "osm_overpass", "derivado", "servicios", "dir", "POI categoría salud / población × 10.000"),
    ("cultura_km2", "Cultura y turismo por km²", "POI/km²", "osm_overpass", "derivado", "servicios", "dir", "POI cultura + turismo / km²"),
    ("comercio_10k", "Comercio de proximidad por 10.000 hab", "tiendas", "osm_overpass", "derivado", "servicios", "dir", "POI categoría comercio / población × 10.000"),
    ("gastronomia_km2", "Gastronomía por km²", "locales/km²", "osm_overpass", "derivado", None, None, "POI categoría gastronomia / km²"),
    ("alojamiento", "Alojamientos turísticos (OSM)", "establec.", "osm_overpass", "observado", None, None, "POI categoría alojamiento"),
    ("arbolado", "Cobertura arbórea media", "%", "copernicus", "observado", "verde", "dir", "Media de Tree Cover Density 2018 (0–100) en el polígono"),
    ("verde_10k", "Parques y jardines por 10.000 hab", "espacios", "osm_overpass", "derivado", "verde", "dir", "POI leisure=park|garden|nature_reserve / población × 10.000"),
    ("sellado", "Suelo sellado medio", "%", "copernicus", "observado", "verde", "inv", "Media de Imperviousness Density 2018 (0–100)"),
    ("sellado_alto", "Superficie muy sellada (≥80 %)", "% sup.", "copernicus", "observado", None, None, "Píxeles con IMD ≥ 80 / píxeles válidos"),
    ("edificios_km2", "Edificios OSM por km²", "edif./km²", "osm_overpass", "derivado", None, None, "building=* (vías + relaciones) / km²"),
    ("pm25_sensores", "PM2.5 ciudadano de bajo costo (mediana)", "µg/m³", "sensor_community", "bajo_costo", "ambiente", "inv", "Mediana de sensores ciudadanos exteriores de bajo costo del distrito en la instantánea (mínimo 2)"),
]
DIMENSIONES = {
    "movilidad": {"nombre": "Movilidad", "descripcion": "Oferta de transporte público y bicicleta"},
    "servicios": {"nombre": "Servicios", "descripcion": "Educación, salud, cultura y comercio de proximidad"},
    "verde": {"nombre": "Verde", "descripcion": "Arbolado, parques y suelo no sellado"},
    "vivienda": {"nombre": "Vivienda y densidad", "descripcion": "Intensidad residencial y dinámica demográfica"},
    "ambiente": {"nombre": "Aire", "descripcion": "Partículas finas medidas por la red ciudadana (instantánea)"},
}


def metricas_distrito(con):
    ds = lago.consultar(con, "SELECT * FROM distritos ORDER BY distrito_id")
    hist = defaultdict(dict)
    for h in seguro(con, "ksh_distritos_historico", "SELECT distrito_id, anio, poblacion FROM ksh_distritos_historico"):
        hist[h["distrito_id"]][h["anio"]] = h["poblacion"]
    poi = defaultdict(Counter)
    for p in seguro(con, "osm_poi", "SELECT distrito_id, categoria, subcategoria FROM osm_poi WHERE distrito_id IS NOT NULL"):
        poi[p["distrito_id"]][p["categoria"]] += 1
        if p["subcategoria"] in ("park", "garden", "nature_reserve"):
            poi[p["distrito_id"]]["verde_parques"] += 1
    par = {x["distrito_id"]: x for x in seguro(con, "gtfs_paradas", """
        SELECT distrito_id, COUNT(*) paradas, SUM(salidas_dia_ref) salidas,
               SUM(CASE WHEN modos LIKE '%metro%' OR modos LIKE '%tranvia%' OR modos LIKE '%trolebus%' OR modos LIKE '%hev%' THEN 1 ELSE 0 END) guiadas
        FROM gtfs_paradas WHERE salidas_dia_ref > 0 AND tipo_ubicacion = 0 GROUP BY distrito_id""")}
    bubi = Counter(x["distrito_id"] for x in seguro(con, "bubi_estaciones", "SELECT distrito_id FROM bubi_estaciones"))
    cop = defaultdict(dict)
    for c in seguro(con, "copernicus_distrito", "SELECT * FROM copernicus_distrito"):
        cop[c["distrito_id"]][c["capa"]] = c
    edif = {x["distrito_id"]: x["edificios"] for x in seguro(con, "osm_edificios_distrito", "SELECT * FROM osm_edificios_distrito")}
    pm = defaultdict(list)
    for s in seguro(con, "sc_sensores", "SELECT distrito_id, pm25 FROM sc_sensores WHERE pm25 IS NOT NULL AND distrito_id IS NOT NULL"):
        pm[s["distrito_id"]].append(s["pm25"])

    filas = []
    for d in ds:
        i = d["distrito_id"]
        km2 = (d["area_ha_ksh"] or d["area_km2"] * 100) / 100
        pob = d["poblacion"]
        h = hist.get(i, {})
        anios = sorted(h)
        var = None
        if len(anios) >= 2:
            a1 = anios[-1]
            a0 = a1 - 5 if (a1 - 5) in h else anios[0]
            var = (h[a1] / h[a0] - 1) * 100 if h[a0] else None
        p = par.get(i, {})
        per10k = (lambda n: n / pob * 1e4 if pob else None)
        f = {
            "distrito_id": i, "nombre": d["nombre"], "romano": d["romano"], "apodo": d["apodo"], "lado": d["lado"],
            "area_km2": r(km2, 2), "poblacion": pob, "viviendas": d["viviendas"],
            "densidad": r(pob / km2, 0) if pob else None, "var_poblacion": r(var, 2),
            "hab_vivienda": r(pob / d["viviendas"], 2) if pob and d["viviendas"] else None,
            "viviendas_km2": r(d["viviendas"] / km2, 0) if d["viviendas"] else None,
            "paradas_km2": r(p.get("paradas", 0) / km2, 2) if p else None,
            "salidas_1000": r(p.get("salidas", 0) / pob * 1000, 0) if p and pob else None,
            "guiado_pct": r(100 * p.get("guiadas", 0) / p["paradas"], 1) if p.get("paradas") else None,
            "bubi_km2": r(bubi.get(i, 0) / km2, 2),
            "educacion_10k": r(per10k(poi[i]["educacion"]), 1), "salud_10k": r(per10k(poi[i]["salud"]), 1),
            "cultura_km2": r((poi[i]["cultura"] + poi[i]["turismo"]) / km2, 2),
            "comercio_10k": r(per10k(poi[i]["comercio"]), 1), "gastronomia_km2": r(poi[i]["gastronomia"] / km2, 1),
            "alojamiento": poi[i]["alojamiento"], "verde_10k": r(per10k(poi[i]["verde_parques"]), 1),
            "arbolado": r(cop[i].get("tree_cover_2018", {}).get("media"), 1),
            "sellado": r(cop[i].get("imperviousness_2018", {}).get("media"), 1),
            "sellado_alto": r(cop[i].get("imperviousness_2018", {}).get("pct_alto"), 1),
            "edificios_km2": r(edif[i] / km2, 0) if i in edif else None,
            "pm25_sensores": r(statistics.median(pm[i]), 1) if len(pm[i]) >= 2 else None,
            "pm25_sensores_n": len(pm[i]),
            "paradas": p.get("paradas"), "salidas": p.get("salidas"), "bubi": bubi.get(i, 0),
            "poi": dict(poi[i]), "centro": [d["centro_lon"], d["centro_lat"]],
        }
        filas.append(f)
    # puntajes 0–100 por dimensión (min–max entre los 23 distritos; inversa cuando menos es mejor)
    for dim in DIMENSIONES:
        ms = [(m[0], m[6]) for m in METRICAS if m[5] == dim]
        normas = {}
        for mid, sentido in ms:
            vals = [f[mid] for f in filas if f[mid] is not None]
            if len(vals) < 3:
                continue
            lo, hi = min(vals), max(vals)
            normas[mid] = (lo, hi, sentido)
        for f in filas:
            vs = []
            for mid, (lo, hi, sentido) in normas.items():
                if f[mid] is None or hi == lo:
                    continue
                x = (f[mid] - lo) / (hi - lo)
                vs.append(100 * (1 - x if sentido == "inv" else x))
            f["score_" + dim] = r(sum(vs) / len(vs), 1) if vs else None
    return filas


def pearson(xs, ys):
    n = len(xs)
    if n < 5:
        return None
    mx, my = sum(xs) / n, sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = math.sqrt(sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys))
    return num / den if den else None


def rangos(v):
    orden = sorted(range(len(v)), key=lambda i: v[i])
    rk = [0.0] * len(v)
    i = 0
    while i < len(orden):
        j = i
        while j + 1 < len(orden) and v[orden[j + 1]] == v[orden[i]]:
            j += 1
        for k in range(i, j + 1):
            rk[orden[k]] = (i + j) / 2 + 1
        i = j + 1
    return rk


# ------------------------------------------------------------------ temas
def t_territorio(con, filas, estado):
    t = tema("territorio", "Territorio", ["ksh", "osm_overpass", "geofabrik", "copernicus"])
    pob = sum(f["poblacion"] or 0 for f in filas)
    km2 = sum(f["area_km2"] or 0 for f in filas)
    anio = (lago.consultar(con, "SELECT MAX(anio) a FROM ksh_distritos_historico")[0]["a"]
            if lago.tabla_existe(con, "ksh_distritos_historico") else None)
    cifra(t, "poblacion", pob, "hab", "Población residente (23 distritos)", "ksh", f"{anio}-01-01")
    cifra(t, "superficie", r(km2, 1), "km²", "Superficie", "ksh", f"{anio}-01-01")
    cifra(t, "densidad", r(pob / km2, 0) if km2 else None, "hab/km²", "Densidad media", "ksh", anio, "derivado")
    cifra(t, "viviendas", sum(f["viviendas"] or 0 for f in filas), "viviendas", "Viviendas", "ksh", f"{anio}-01-01")
    cifra(t, "distritos", len(filas), "kerületek", "Distritos", "osm_overpass", lago.HOY)
    e = seguro(con, "osm_edificios_distrito", "SELECT SUM(edificios) n, MAX(fecha_osm) f FROM osm_edificios_distrito")
    if e and e[0]["n"]:
        cifra(t, "edificios", e[0]["n"], "edificios", "Edificios cartografiados en OSM", "osm_overpass", (e[0]["f"] or "")[:10])
    n_poi = seguro(con, "osm_poi", "SELECT categoria, COUNT(*) n FROM osm_poi WHERE distrito_id IS NOT NULL GROUP BY categoria ORDER BY n DESC")
    cifra(t, "poi", sum(x["n"] for x in n_poi), "puntos", "Equipamientos y servicios OSM clasificados", "osm_overpass", lago.HOY)
    gf = seguro(con, "geofabrik_extracto", "SELECT * FROM geofabrik_extracto")
    if gf:
        cifra(t, "osm_replica", gf[0]["fecha_replica"][:10], "", "Réplica OSM de referencia (Geofabrik)", "geofabrik", gf[0]["fecha_replica"][:10],
              nota=f"Extracto Hungría .osm.pbf de {round((gf[0]['pbf_bytes'] or 0) / 1e6)} MB, secuencia {gf[0]['secuencia']}")
    t["listas"]["poi_categorias"] = [{"categoria": x["categoria"], "n": x["n"]} for x in n_poi]
    tot = defaultdict(int)
    for h in seguro(con, "ksh_distritos_historico", "SELECT anio, poblacion FROM ksh_distritos_historico"):
        tot[h["anio"]] += h["poblacion"] or 0
    serie(t, "poblacion_helysegnevtar", "Población de Budapest (suma de distritos)", "hab", "ksh", sorted([a, v] for a, v in tot.items()))
    t["listas"]["distritos"] = [{k: f[k] for k in ("distrito_id", "romano", "apodo", "lado", "poblacion", "area_km2", "densidad",
                                                     "viviendas", "var_poblacion")} for f in filas]
    return t


def t_demografia(con, filas):
    t = tema("demografia", "Gente", ["ksh_hvd", "ksh_hvd", "eurostat"])
    pob = ksh(con, "NR")
    a, v = ultimo(pob)
    cifra(t, "poblacion_nuts3", v, "hab", "Población al 1 de enero (NUTS3 HU110)", "ksh_hvd", a)
    for ind, clave, et, u in (("MEDAGEPOP", "edad_mediana", "Edad mediana", "años"), ("OLDDEP3", "dependencia_vejez", "Dependencia de vejez (65+ / 20–64)", "%"),
                              ("GBIRTHRT", "natalidad", "Tasa bruta de natalidad", "‰"), ("GDEATHRT", "mortalidad", "Tasa bruta de mortalidad", "‰")):
        s = ksh(con, ind) or ksh(con, ind, "HU11")
        a, v = ultimo(s)
        cifra(t, clave, v, u, et, "ksh_hvd", a, decimales=1)
    ev = ksh(con, "YR", "HU11", "T", "Y_LT1")
    a, v = ultimo(ev)
    cifra(t, "esperanza_vida", v, "años", "Esperanza de vida al nacer (HU11)", "ksh_hvd", a, decimales=1)
    mi = ksh(con, "RT", "HU11")
    a, v = ultimo(mi)
    cifra(t, "mortalidad_infantil", v, "‰", "Mortalidad infantil (HU11)", "ksh_hvd", a, decimales=1)

    serie(t, "poblacion", "Población de Budapest (HU110)", "hab", "ksh_hvd", pob)
    serie(t, "edad_mediana", "Edad mediana", "años", "ksh_hvd", series=[
        {"nombre": "Budapest", "puntos": ksh(con, "MEDAGEPOP")}, {"nombre": "Hungría", "puntos": ksh(con, "MEDAGEPOP", "HU")}])
    serie(t, "esperanza_vida", "Esperanza de vida al nacer", "años", "ksh_hvd", series=[
        {"nombre": "Mujeres", "puntos": ksh(con, "YR", "HU11", "F", "Y_LT1")}, {"nombre": "Hombres", "puntos": ksh(con, "YR", "HU11", "M", "Y_LT1")}])
    serie(t, "natalidad_mortalidad", "Natalidad y mortalidad", "‰", "ksh_hvd", series=[
        {"nombre": "Natalidad", "puntos": ksh(con, "GBIRTHRT", "HU11")}, {"nombre": "Mortalidad", "puntos": ksh(con, "GDEATHRT", "HU11")}])
    serie(t, "dependencia", "Dependencia de vejez", "%", "ksh_hvd", series=[
        {"nombre": "Budapest", "puntos": ksh(con, "OLDDEP3")}, {"nombre": "Hungría", "puntos": ksh(con, "OLDDEP3", "HU")}])

    # pirámide del último año con grupos quinquenales
    ult = lago.consultar(con, "SELECT MAX(anio) a FROM ksh_hvd WHERE indicador='NR' AND geo='HU110'")[0]["a"]
    grupos = ["Y_LT5", "Y5-9"] + [f"Y{i}-{i+4}" for i in range(10, 85, 5)] + ["Y_GE85"]
    val = {(f["sexo"], f["edad"]): f["valor"] for f in lago.consultar(
        con, "SELECT sexo, edad, valor FROM ksh_hvd WHERE indicador='NR' AND geo='HU110' AND anio=?", ult)}
    etiqueta = lambda g: "0–4" if g == "Y_LT5" else ("85+" if g == "Y_GE85" else g[1:].replace("-", "–"))
    t["listas"]["piramide"] = [{"grupo": etiqueta(g), "hombres": val.get(("M", g)), "mujeres": val.get(("F", g))} for g in grupos]
    t["listas"]["piramide_meta"] = [{"anio": ult, "fuente": "ksh_hvd"}]
    t["listas"]["poblacion_distritos"] = sorted(
        [{"distrito": f"{f['romano']} · {f['apodo']}", "poblacion": f["poblacion"], "var_poblacion": f["var_poblacion"],
          "densidad": f["densidad"]} for f in filas], key=lambda x: -(x["poblacion"] or 0))
    return t


def t_economia(con, filas):
    t = tema("economia", "Economía y vivienda", ["eurostat", "ksh"])
    defs = [
        ("pib_hab_eur", "PIB por habitante (HU110)", "€/hab", {}, 0),
        ("pib_hab_pps_ue", "PIB por habitante en PPS", "% UE27", {}, 0),
        ("desempleo", "Tasa de desempleo 20–64", "%", {}, 1),
        ("empleo", "Tasa de empleo 20–64", "%", {}, 1),
        ("ingreso_disponible", "Ingreso disponible de los hogares", "PPS/hab", {"unit": "PPS_EU27_2020_HAB", "na_item": "B6N", "direct": "BAL"}, 0),
        ("riesgo_pobreza_exclusion", "Riesgo de pobreza o exclusión (AROPE)", "%", {}, 1),
        ("educacion_terciaria", "Población 25–64 con estudios terciarios", "%", {}, 1),
        ("gasto_id_pib", "Gasto en I+D", "% PIB", {"sectperf": "TOTAL", "unit": "PC_GDP"}, 2),
    ]
    for clave, et, u, dims, dec in defs:
        s = eu(con, clave, **dims)
        if not s and dims:
            s = eu(con, clave)
        a, v = ultimo(s)
        cifra(t, clave, v, u, et, "eurostat", a, decimales=dec)
        serie(t, clave, et, u, "eurostat", s)
    hpi = eu(con, "precio_vivienda_hu", purchase="TOTAL", unit="I15_Q")
    a, v = ultimo(hpi)
    trimestre = lago.consultar(con, "SELECT MAX(periodo) p FROM eurostat_obs WHERE clave='precio_vivienda_hu'")[0]["p"]
    a = trimestre.replace("-Q", "-T") if trimestre else a  # 2026.0 perdería el trimestre (T1)
    cifra(t, "precio_vivienda", v, "2015 = 100", "Índice de precios de vivienda (Hungría, como proxy de Budapest)", "eurostat", a, "proxy",
          nota="PROXY: Eurostat no publica el índice por región; se usa el de toda Hungría como aproximación para Budapest.", decimales=1)
    serie(t, "precio_vivienda", "Índice de precios de vivienda · Hungría (proxy de Budapest)", "2015 = 100", "eurostat", hpi,
          nota="PROXY: índice nacional usado como aproximación; no existe la serie para Budapest.", estado="proxy")
    emp = eu(con, "empresas", indic_sb="V11910", nace_r2="B-S_X_K642")
    a, v = ultimo(emp)
    cifra(t, "empresas_activas", v, "empresas", "Empresas activas (HU110)", "eurostat", a)
    viv = sum(f["viviendas"] or 0 for f in filas)
    pob = sum(f["poblacion"] or 0 for f in filas)
    cifra(t, "viviendas_1000", r(viv / pob * 1000, 0) if pob else None, "viv/1.000 hab", "Viviendas por 1.000 habitantes", "ksh", lago.HOY[:4], "derivado")
    t["listas"]["vivienda_distritos"] = sorted(
        [{"distrito": f"{f['romano']} · {f['apodo']}", "viviendas": f["viviendas"], "hab_vivienda": f["hab_vivienda"],
          "viviendas_km2": f["viviendas_km2"]} for f in filas], key=lambda x: -(x["viviendas"] or 0))
    t["listas"]["urban_audit_trabajo"] = urban_audit(con, "ua_trabajo")
    return t


def urban_audit(con, clave, maximo=40):
    filas = lago.consultar(con, """SELECT etiqueta, periodo, valor, dimensiones FROM eurostat_obs o
        WHERE clave=? AND periodo = (SELECT MAX(periodo) FROM eurostat_obs p WHERE p.clave=o.clave AND p.etiqueta=o.etiqueta)
        ORDER BY etiqueta""", clave)
    return [{"indicador": f["etiqueta"], "codigo": json.loads(f["dimensiones"]).get("indic_ur"), "anio": f["periodo"], "valor": f["valor"]}
            for f in filas][:maximo]


def t_turismo(con, filas):
    t = tema("turismo", "Turismo", ["eurostat", "osm_overpass"])
    tot, ext, dom = (eu(con, "pernoctaciones", c_resid=c) for c in ("TOTAL", "FOR", "DOM"))
    lt, lx, ld = (eu(con, "llegadas", c_resid=c) for c in ("TOTAL", "FOR", "DOM"))
    a, v = ultimo(tot)
    cifra(t, "pernoctaciones", v, "noches", "Pernoctaciones en alojamiento turístico (HU11)", "eurostat", a)
    a2, vx = ultimo(ext)
    cifra(t, "pct_extranjeros", r(100 * vx / v, 1) if v and vx and a2 == a else None, "%", "Pernoctaciones de no residentes", "eurostat", a, "derivado")
    a3, vl = ultimo(lt)
    cifra(t, "llegadas", vl, "llegadas", "Llegadas de huéspedes (HU11)", "eurostat", a3)
    cifra(t, "estancia_media", r(v / vl, 2) if v and vl and a3 == a else None, "noches", "Estancia media", "eurostat", a, "derivado", decimales=2)
    serie(t, "pernoctaciones", "Pernoctaciones", "noches", "eurostat", series=[
        {"nombre": "Total", "puntos": tot}, {"nombre": "No residentes", "puntos": ext}, {"nombre": "Residentes", "puntos": dom}])
    serie(t, "llegadas", "Llegadas", "llegadas", "eurostat", series=[
        {"nombre": "Total", "puntos": lt}, {"nombre": "No residentes", "puntos": lx}, {"nombre": "Residentes", "puntos": ld}])
    aloj = seguro(con, "osm_poi", "SELECT subcategoria, COUNT(*) n FROM osm_poi WHERE categoria='alojamiento' AND distrito_id IS NOT NULL GROUP BY subcategoria ORDER BY n DESC")
    cifra(t, "alojamientos_osm", sum(x["n"] for x in aloj), "establec.", "Alojamientos cartografiados (OSM)", "osm_overpass", lago.HOY)
    tur = seguro(con, "osm_poi", "SELECT subcategoria, COUNT(*) n FROM osm_poi WHERE categoria IN ('turismo','cultura') AND distrito_id IS NOT NULL GROUP BY subcategoria ORDER BY n DESC")
    cifra(t, "atractivos_osm", sum(x["n"] for x in tur), "lugares", "Museos, atractivos y cultura (OSM)", "osm_overpass", lago.HOY)
    t["listas"]["alojamiento_tipos"] = aloj
    t["listas"]["atractivos_tipos"] = tur
    t["listas"]["turismo_distritos"] = sorted(
        [{"distrito": f"{f['romano']} · {f['apodo']}", "alojamiento": f["alojamiento"],
          "cultura_turismo": (f["poi"].get("cultura", 0) + f["poi"].get("turismo", 0)), "gastronomia": f["poi"].get("gastronomia", 0)}
         for f in filas], key=lambda x: -x["alojamiento"])
    t["listas"]["urban_audit_turismo"] = urban_audit(con, "ua_turismo")
    return t


def t_movilidad(con, filas):
    t = tema("movilidad", "Movilidad", ["bkk_gtfs", "mobilitydb", "osm_overpass", "bubi", "eurostat"])
    feed = seguro(con, "gtfs_feed", "SELECT * FROM gtfs_feed")
    if feed:
        fd = feed[0]
        ref = fd["dia_referencia"]
        cifra(t, "viajes_dia", fd["viajes_dia_ref"], "viajes", "Viajes programados en un día laborable", "bkk_gtfs", ref,
              nota=f"Miércoles de referencia {ref}; feed {fd['version'] or ''} ({fd['origen']})")
        cifra(t, "detenciones_dia", fd["detenciones_dia_ref"], "detenciones", "Detenciones programadas por día laborable", "bkk_gtfs", ref)
        par = lago.consultar(con, "SELECT COUNT(*) n FROM gtfs_paradas WHERE salidas_dia_ref>0 AND tipo_ubicacion=0")[0]["n"]
        cifra(t, "paradas", par, "paradas", "Paradas y andenes con servicio", "bkk_gtfs", ref)
        acc = lago.consultar(con, "SELECT 100.0*SUM(accesible=1)/COUNT(*) p FROM gtfs_paradas WHERE salidas_dia_ref>0 AND tipo_ubicacion=0")[0]["p"]
        cifra(t, "accesibles", r(acc, 1), "%", "Paradas declaradas accesibles en silla de ruedas", "bkk_gtfs", ref, decimales=1)
        modos = lago.consultar(con, """SELECT modo, COUNT(*) rutas, SUM(viajes_dia_ref) viajes FROM gtfs_rutas
                                       WHERE viajes_dia_ref>0 GROUP BY modo ORDER BY viajes DESC""")
        t["listas"]["modos"] = modos
        cifra(t, "lineas", sum(m["rutas"] for m in modos), "líneas", "Líneas con servicio el día de referencia", "bkk_gtfs", ref)
        top = lago.consultar(con, """SELECT nombre, SUM(salidas_dia_ref) salidas, MAX(rutas_n) rutas, GROUP_CONCAT(DISTINCT modos) modos,
            AVG(lat) lat, AVG(lon) lon, MIN(distrito_id) distrito_id FROM gtfs_paradas WHERE salidas_dia_ref>0
            GROUP BY nombre ORDER BY salidas DESC LIMIT 20""")
        for x in top:
            x["modos"] = ",".join(sorted(set(",".join(filter(None, (x["modos"] or "").split(","))).split(","))))
            x["lat"], x["lon"] = r(x["lat"], 5), r(x["lon"], 5)
        t["listas"]["paradas_top"] = top
    # Bubi: las ubicaciones salen de OSM mientras el feed del operador (F07) sea candidata; la disponibilidad
    # y la flota solo se publican cuando la fuente está integrada (existen bubi_disponibilidad / bubi_historico).
    b = seguro(con, "bubi_estaciones", "SELECT COUNT(*) n, MIN(origen) origen FROM bubi_estaciones")
    if b and b[0]["n"]:
        vivo = b[0]["origen"] == "nextbike_vivo"
        cifra(t, "bubi_estaciones", b[0]["n"], "estaciones", "Estaciones MOL Bubi" + ("" if vivo else " (cartografía OSM)"),
              "bubi" if vivo else "osm_overpass", lago.HOY, "en_vivo" if vivo else "observado",
              nota=None if vivo else "El feed del operador (F07) no publica estaciones y queda como fuente candidata: ubicaciones de OSM con red MOL Bubi, sin disponibilidad.")
    disp = seguro(con, "bubi_disponibilidad", "SELECT SUM(bicis) bicis, SUM(anclajes) anclajes, MAX(ts) ts FROM bubi_disponibilidad")
    if disp and disp[0]["ts"]:
        cifra(t, "bubi_bicis", disp[0]["bicis"], "bicicletas", "Bicicletas disponibles en la instantánea", "bubi", disp[0]["ts"], "en_vivo")
        cifra(t, "bubi_ocupacion", r(100 * disp[0]["bicis"] / disp[0]["anclajes"], 1) if disp[0]["anclajes"] else None, "%",
              "Ocupación de anclajes", "bubi", disp[0]["ts"], "en_vivo")
    hist = seguro(con, "bubi_historico", "SELECT ts, bicis, flota_objetivo FROM bubi_historico WHERE estaciones > 0 ORDER BY ts")
    if hist and hist[-1]["flota_objetivo"]:
        cifra(t, "bubi_flota", hist[-1]["flota_objetivo"], "bicicletas", "Flota objetivo de MOL Bubi declarada por el operador", "bubi", hist[-1]["ts"][:10], "en_vivo")
    if len(hist) > 1:
        serie(t, "bubi_historico", "Bicicletas disponibles por instantánea", "bicicletas", "bubi", [[h["ts"], h["bicis"]] for h in hist])
    veh = eu(con, "vehiculos", vehicle="CAR", unit="NR")
    a, v = ultimo(veh)
    cifra(t, "turismos", v, "vehículos", "Parque de turismos (HU11)", "eurostat", a)
    serie(t, "turismos", "Parque de turismos", "vehículos", "eurostat", veh)
    pob = sum(f["poblacion"] or 0 for f in filas)
    cifra(t, "motorizacion", r(v / pob * 1000, 0) if v and pob else None, "turismos/1.000 hab", "Motorización", "eurostat", a, "derivado")
    t["listas"]["movilidad_distritos"] = [{"distrito": f"{f['romano']} · {f['apodo']}", "paradas": f["paradas"], "salidas": f["salidas"],
                                           "salidas_1000": f["salidas_1000"], "guiado_pct": f["guiado_pct"], "bubi": f["bubi"]} for f in filas]
    t["listas"]["feeds"] = seguro(con, "mdb_feeds", "SELECT mdb_id, tipo, entidad, proveedor, estado, requiere_clave, url_directa FROM mdb_feeds ORDER BY estado, mdb_id")
    t["listas"]["urban_audit_transporte"] = urban_audit(con, "ua_transporte")
    return t


def t_ambiente(con, filas):
    t = tema("ambiente", "Ambiente y clima", ["eea", "sensor_community", "opensensemap", "open_meteo", "copernicus"])
    # EEA: media urbana anual = promedio de estaciones con cobertura ≥ 75 %
    ser, n_est = {}, {}
    for c in ("PM2.5", "PM10", "NO2"):
        fs = seguro(con, "eea_estadisticas", """SELECT anio, AVG(valor) v, COUNT(*) n FROM eea_estadisticas
             WHERE contaminante=? AND agregacion='P1Y' AND cobertura>=75 GROUP BY anio ORDER BY anio""", c)
        ser[c] = [[f["anio"], r(f["v"], 1)] for f in fs]
        n_est[c] = fs[-1]["n"] if fs else 0
    anio_val = max((p[0] for p in ser.get("PM2.5", [])), default=None)
    for c, clave in (("PM2.5", "pm25_anual"), ("PM10", "pm10_anual"), ("NO2", "no2_anual")):
        a, v = ultimo(ser[c])
        cifra(t, clave, v, "µg/m³", f"{c} media anual (estaciones oficiales)", "eea", a, "derivado",
              nota=(f"Promedio de {n_est[c]} estación(es) con cobertura ≥ 75 % en {a}. "
                    f"Guía OMS 2021: {config.OMS_ANUAL[c]} µg/m³ · límite UE: {config.LIMITE_UE_ANUAL[c]} µg/m³"), decimales=1)
    serie(t, "particulas", "Partículas: media anual de estaciones oficiales", "µg/m³", "eea", estado="observado",
          series=[{"nombre": "PM10", "puntos": ser["PM10"]}, {"nombre": "PM2.5", "puntos": ser["PM2.5"]}],
          nota="Promedio de estaciones con cobertura ≥ 75 %. Guía OMS: PM2.5 5 · PM10 15 µg/m³.")
    serie(t, "no2", "NO₂: media anual de estaciones oficiales", "µg/m³", "eea", ser["NO2"], nota="Guía OMS: 10 µg/m³.", estado="observado")
    dias = seguro(con, "eea_estadisticas", """SELECT anio, MAX(valor) v FROM eea_estadisticas WHERE contaminante='PM10'
          AND agregacion='P1Y-daysAbove50' GROUP BY anio ORDER BY anio""")
    serie(t, "pm10_dias", "Días con PM10 > 50 µg/m³ (estación más expuesta)", "días", "eea", [[d["anio"], d["v"]] for d in dias],
          nota="La normativa UE permite 35 días al año.", tipo="barras", estado="observado")
    est = seguro(con, "eea_estaciones", "SELECT * FROM eea_estaciones")
    ultimos = defaultdict(dict)
    for s in seguro(con, "eea_estadisticas", """SELECT estacion, contaminante, anio, valor FROM eea_estadisticas e WHERE agregacion='P1Y'
            AND anio=(SELECT MAX(anio) FROM eea_estadisticas f WHERE f.estacion=e.estacion AND f.contaminante=e.contaminante AND f.agregacion='P1Y')"""):
        ultimos[s["estacion"]][s["contaminante"]] = [s["anio"], r(s["valor"], 1)]
    t["listas"]["estaciones"] = [{"estacion": e["estacion"], "nombre": e["nombre"], "tipo": e["tipo"], "area": e["area"],
                                  "distrito_id": e["distrito_id"], **{k.replace(".", ""): ultimos[e["estacion"]].get(k, [None, None])[1] for k in ("PM2.5", "PM10", "NO2", "O3")},
                                  "anio": max((v[0] for v in ultimos[e["estacion"]].values()), default=None)} for e in est]
    cifra(t, "estaciones_eea", len(est), "estaciones", "Estaciones oficiales con reporte a la EEA", "eea", anio_val)
    # red ciudadana
    sc = seguro(con, "sc_sensores", "SELECT pm25, pm10, ts FROM sc_sensores WHERE pm25 IS NOT NULL AND distrito_id IS NOT NULL")
    if sc:
        ts = max(s["ts"] for s in sc)
        cifra(t, "pm25_ciudadano", r(statistics.median([s["pm25"] for s in sc]), 1), "µg/m³", "PM2.5 ahora · mediana de sensores ciudadanos",
              "sensor_community", ts, "bajo_costo", nota="Bajo costo: sensores ópticos ciudadanos sin calibración oficial (sobreestiman con humedad alta); promedio de 5 minutos en la instantánea.", decimales=1)
        cifra(t, "sensores_ciudadanos", len(sc), "sensores", "Sensores ciudadanos de partículas (bajo costo) en Budapest", "sensor_community", ts, "bajo_costo")
    hs = seguro(con, "sc_historico", "SELECT ts, pm25_mediana FROM sc_historico ORDER BY ts")
    if len(hs) > 1:
        serie(t, "pm25_ciudadano", "PM2.5 ciudadano de bajo costo por instantánea", "µg/m³", "sensor_community", [[h["ts"], h["pm25_mediana"]] for h in hs], estado="bajo_costo")
    osem = seguro(con, "osem_sensores", "SELECT COUNT(DISTINCT box_id) cajas, SUM(vigente) vig, MAX(ts) ts FROM osem_sensores")
    if osem and osem[0]["cajas"]:
        cajas_vig = lago.consultar(con, "SELECT COUNT(DISTINCT box_id) n FROM osem_sensores WHERE vigente=1")[0]["n"]
        cifra(t, "sensebox", cajas_vig, "cajas", "senseBoxes (bajo costo) con datos en los últimos 7 días", "opensensemap", (osem[0]["ts"] or "")[:10], "bajo_costo",
              nota=f"{osem[0]['cajas']} cajas registradas en el área")
    # CAMS + meteorología
    hor = seguro(con, "meteo_horario", "SELECT * FROM meteo_horario ORDER BY hora")
    if hor:
        serie(t, "cams_pm25", "PM2.5 y PM10 · modelo CAMS (−2 a +3 días)", "µg/m³", "open_meteo", estado="modelo", series=[
            {"nombre": "PM2.5", "puntos": [[h["hora"], h["pm25"]] for h in hor if h["pm25"] is not None]},
            {"nombre": "PM10", "puntos": [[h["hora"], h["pm10"]] for h in hor if h["pm10"] is not None]}],
            nota="Copernicus Atmosphere Monitoring Service, dominio Europa (~10 km).")
        serie(t, "temperatura_horaria", "Temperatura · modelo de pronóstico (−2 a +3 días)", "°C", "open_meteo", [[h["hora"], h["temperatura"]] for h in hor], estado="modelo")
    dia = seguro(con, "meteo_diario", "SELECT substr(fecha,1,4) a, AVG(tmedia) t, SUM(tmax>=30) calor, SUM(tmin>=20) tropical, SUM(precipitacion) p, COUNT(*) n FROM meteo_diario GROUP BY a ORDER BY a")
    completos = [d for d in dia if d["n"] >= 365]
    serie(t, "temperatura_anual", "Temperatura media anual · modelo ERA5", "°C", "open_meteo", [[int(d["a"]), r(d["t"], 2)] for d in completos], estado="modelo",
          nota="Reanálisis ERA5 en el centro de la ciudad.")
    serie(t, "dias_calor", "Días con máxima ≥ 30 °C · modelo ERA5", "días", "open_meteo", [[int(d["a"]), d["calor"]] for d in completos], tipo="barras", estado="modelo")
    if completos:
        base = [d["t"] for d in completos if 2000 <= int(d["a"]) <= 2009]
        u = completos[-1]
        nota_modelo = "Modelo: reanálisis ERA5 servido por Open-Meteo, no medición de estación."
        cifra(t, "temp_anual", r(u["t"], 1), "°C", "Temperatura media del último año completo", "open_meteo", u["a"], "modelo", nota=nota_modelo, decimales=1)
        if base:
            cifra(t, "anomalia", r(u["t"] - sum(base) / len(base), 2), "°C", "Anomalía frente a 2000–2009", "open_meteo", u["a"], "modelo",
                  nota="Diferencia calculada sobre el reanálisis ERA5 (modelo).", decimales=2)
        cifra(t, "dias_calor", u["calor"], "días", "Días con máxima ≥ 30 °C", "open_meteo", u["a"], "modelo", nota=nota_modelo)
        cifra(t, "noches_tropicales", u["tropical"], "noches", "Noches tropicales (mínima ≥ 20 °C)", "open_meteo", u["a"], "modelo", nota=nota_modelo)
    # Copernicus por distrito
    imp = [f["sellado"] for f in filas if f["sellado"] is not None]
    arb = [f["arbolado"] for f in filas if f["arbolado"] is not None]
    pesos = [f["area_km2"] for f in filas if f["sellado"] is not None]
    if imp:
        cifra(t, "sellado", r(sum(i * w for i, w in zip(imp, pesos)) / sum(pesos), 1), "%", "Suelo sellado medio (ponderado por área)", "copernicus", 2018, "derivado", decimales=1)
    if arb:
        pa = [f["area_km2"] for f in filas if f["arbolado"] is not None]
        cifra(t, "arbolado", r(sum(i * w for i, w in zip(arb, pa)) / sum(pa), 1), "%", "Cobertura arbórea media (ponderada por área)", "copernicus", 2018, "derivado", decimales=1)
    t["listas"]["suelo_distritos"] = [{"distrito": f"{f['romano']} · {f['apodo']}", "sellado": f["sellado"], "sellado_alto": f["sellado_alto"],
                                       "arbolado": f["arbolado"], "pm25_sensores": f["pm25_sensores"], "sensores": f["pm25_sensores_n"]} for f in filas]
    t["listas"]["urban_audit_ambiente"] = urban_audit(con, "ua_ambiente")
    return t


def t_distritos(filas):
    t = tema("distritos", "Atlas de los 23 distritos", ["ksh", "osm_overpass", "bkk_gtfs", "copernicus", "sensor_community"])
    t["listas"]["distritos"] = filas
    t["listas"]["metricas"] = [{"id": m[0], "etiqueta": m[1], "unidad": m[2], "fuente": m[3], "estado": m[4], "dimension": m[5],
                                "sentido": m[6], "formula": m[7]} for m in METRICAS]
    t["listas"]["dimensiones"] = [{"id": k, **v, "metricas": [m[0] for m in METRICAS if m[5] == k]} for k, v in DIMENSIONES.items()]
    # pares de correlación (Pearson y Spearman) sobre casos completos
    ids = [m[0] for m in METRICAS]
    pares = []
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            casos = [(f[a], f[b]) for f in filas if f[a] is not None and f[b] is not None]
            if len(casos) < 10:
                continue
            xs, ys = [c[0] for c in casos], [c[1] for c in casos]
            p = pearson(xs, ys)
            s = pearson(rangos(xs), rangos(ys))
            if p is not None:
                pares.append({"x": a, "y": b, "pearson": r(p, 3), "spearman": r(s, 3), "n": len(casos)})
    pares.sort(key=lambda p: -abs(p["pearson"]))
    t["listas"]["pares"] = pares
    cifra(t, "metricas_n", len(METRICAS), "métricas", "Métricas por distrito", "lago", lago.HOY, "derivado")
    cifra(t, "pares_n", len(pares), "pares", "Pares de métricas comparables", "lago", lago.HOY, "derivado")
    return t


def t_preguntas(filas, ambiente, movilidad):
    """Preguntas de la Entrega 1 (sección 1 del Word): cuáles responde el sistema, con qué cifras, y cuáles quedan pendientes."""
    t = tema("preguntas", "Preguntas del sistema", ["bkk_gtfs", "osm_overpass", "ksh", "copernicus", "open_meteo", "eea", "sensor_community", "eurostat", "bubi"])
    n = lambda f: f"{f['romano']}. {f['apodo']}"  # noqa: E731
    num = lambda v, d=0: f"{v:,.{d}f}".replace(",", " ").replace(".", ",")  # noqa: E731
    con_dato = lambda k: [f for f in filas if f.get(k) is not None]  # noqa: E731

    peor_mov = sorted(con_dato("score_movilidad"), key=lambda f: f["score_movilidad"])[:3]
    menos_sal = sorted(con_dato("salidas_1000"), key=lambda f: f["salidas_1000"])[:3]
    sin_bubi = [f for f in filas if not f["bubi"]]
    mas_sellado = sorted(con_dato("sellado"), key=lambda f: -f["sellado"])[:3]
    menos_arbol = sorted(con_dato("arbolado"), key=lambda f: f["arbolado"])[:3]
    c = ambiente["cifras"]
    aire = []
    for clave, cont in (("pm25_anual", "PM2.5"), ("pm10_anual", "PM10"), ("no2_anual", "NO2")):
        x = c.get(clave)
        if x:
            aire.append((cont, x["valor"], x["vigencia"], x["nota"].split(" con cobertura")[0].replace("Promedio de ", "")))
    cumple_ue = all(v <= config.LIMITE_UE_ANUAL[k] for k, v, *_ in aire)
    cumple_oms = all(v <= config.OMS_ANUAL[k] for k, v, *_ in aire)
    calor = c.get("dias_calor")

    t["listas"]["preguntas"] = [
        {"id": "P1", "estado": "respondida", "seccion": "#atlas",
         "pregunta": "¿Qué distritos tienen peor acceso a transporte público y a bicicleta por habitante?",
         "respuesta": (f"Menor puntaje de movilidad: {', '.join(f'{n(f)} ({num(f['score_movilidad'])}/100)' for f in peor_mov)}. "
                       f"Menos salidas de transporte por cada 1 000 habitantes: {', '.join(f'{n(f)} ({num(f['salidas_1000'])})' for f in menos_sal)}. "
                       f"{len(sin_bubi)} de los 23 distritos no tienen ninguna estación MOL Bubi: {', '.join(f['romano'] for f in sin_bubi)}."),
         "limites": ("Mide la oferta programada un miércoles (F05), no el servicio real. La población es la residente (F08): "
                     "los distritos centrales, con muchos visitantes de día, parecen mejor servidos por habitante de lo que están."),
         "fuentes": ["bkk_gtfs", "osm_overpass", "ksh"]},
        {"id": "P2", "estado": "respondida", "seccion": "#ambiente",
         "pregunta": "¿Qué distritos tienen más suelo sellado y menos arbolado, es decir, más riesgo de isla de calor?",
         "respuesta": (f"Más suelo sellado: {', '.join(f'{n(f)} ({num(f['sellado'], 1)} %)' for f in mas_sellado)}. "
                       f"Menos arbolado: {', '.join(f'{n(f)} ({num(f['arbolado'], 1)} %)' for f in menos_arbol)}. "
                       + (f"Según el modelo ERA5, en {calor['vigencia']} hubo {calor['valor']} días con máximas de 30 °C o más." if calor else "")),
         "limites": "Las capas de Copernicus son de 2018. La temperatura es de modelo (F14) y de un solo punto de la ciudad, no por distrito.",
         "fuentes": ["copernicus", "open_meteo"]},
        {"id": "P3", "estado": "respondida", "seccion": "#ambiente",
         "pregunta": "¿Cumple Budapest los límites de la UE y las guías de la OMS de calidad del aire?",
         "respuesta": (("Sí cumple" if cumple_ue else "No cumple") + " los límites anuales de la UE y "
                       + ("cumple" if cumple_oms else "no cumple") + " las guías de la OMS: "
                       + "; ".join(f"{k} {num(v, 1)} µg/m³ en {vig} ({est}; UE {config.LIMITE_UE_ANUAL[k]}, OMS {config.OMS_ANUAL[k]})" for k, v, vig, est in aire) + "."),
         "limites": ("En el último año el PM2.5 oficial sale de muy pocas estaciones. Los sensores ciudadanos (F11, F12) son de bajo costo "
                     "y la previsión CAMS (F14) es de modelo: ninguno de los dos sirve para verificar el cumplimiento legal."),
         "fuentes": ["eea", "sensor_community", "open_meteo"]},
        {"id": "P4", "estado": "pendiente", "seccion": "#movilidad",
         "pregunta": "¿Qué distritos reciben peor servicio real de transporte (retrasos y cancelaciones)?",
         "motivo": "El tiempo real de BKK (F16, GTFS-Realtime) exige registro y una clave personal; decidimos no atar el lago a una credencial.",
         "cambiaria": "Una clave institucional a nombre del grupo, o que BKK publique el GTFS-Realtime sin registro.",
         "fuentes": ["bkk_gtfs"]},
        {"id": "P5", "estado": "pendiente", "seccion": "#economia",
         "pregunta": "¿Qué distrito es más pobre?",
         "motivo": "Ingreso, pobreza y empleo solo existen para toda la ciudad (F10, NUTS2 y NUTS3); ninguna fuente abierta del lago los da por distrito.",
         "cambiaria": "Que KSH publique ingresos o datos fiscales por kerület en formato abierto.",
         "fuentes": ["eurostat"]},
        {"id": "P6", "estado": "pendiente", "seccion": "#movilidad",
         "pregunta": "¿Dónde hay bicicletas MOL Bubi disponibles ahora?",
         "motivo": "El feed del operador (F07) responde pero no publica estaciones: quedó como fuente candidata y solo se conocen las ubicaciones (OSM, F02).",
         "cambiaria": "Que el operador vuelva a publicar las estaciones: el lago las integra solo en la siguiente ejecución.",
         "fuentes": ["bubi", "osm_overpass"]},
    ]
    return t


def t_catalogo(con, estado):
    from pipelines.esquema import ESQUEMA
    t = tema("catalogo", "Fuentes y método", list(config.FUENTES))
    lin = []
    p = config.CATALOGO / "linaje.jsonl"
    if p.exists():
        lin = [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
    por_fuente = defaultdict(lambda: {"archivos": 0, "bytes": 0, "ultimo": None})
    for l in lin:
        x = por_fuente["ksh_hvd" if l["fuente"] == "ksh" and "/hvd_" in l["archivo"] else l["fuente"]]
        x["archivos"] += 1
        x["bytes"] += l["bytes"] or 0
        x["ultimo"] = max(x["ultimo"] or "", l["ts"])
    tablas = defaultdict(list)
    for nombre, meta in ESQUEMA.items():
        n = con.execute(f"SELECT COUNT(*) FROM {nombre}").fetchone()[0] if lago.tabla_existe(con, nombre) else 0
        for fid in [x.strip() for x in meta["fuente"].split("+")]:
            tablas[fid].append({"tabla": nombre, "filas": n})
    t["listas"]["fuentes"] = [{"id": fid, "codigo": f["codigo"], "probada": probada(fid),
                               **{k: f[k] for k in ("nombre", "organismo", "url", "licencia", "acceso", "frecuencia")},
                               "estado": estado.get(f.get("modulo", fid), {}).get("estado", "pendiente"),
                               "error": estado.get(f.get("modulo", fid), {}).get("error"),
                               "ultima_ingesta": estado.get(f.get("modulo", fid), {}).get("ultima_ingesta"), "bronze_archivos": por_fuente[fid]["archivos"],
                               "bronze_mb": r(por_fuente[fid]["bytes"] / 1e6, 2), "tablas": tablas.get(fid, [])}
                              for fid, f in config.FUENTES.items()]
    t["listas"]["zonas"] = [
        {"zona": "bronze", "ruta": "datalake/bronze/<fuente>/<AAAA-MM-DD>/", "contenido": "Respuestas crudas e inmutables de cada API (JSON, CSV, XLSX, ZIP) con linaje sha256."},
        {"zona": "silver", "ruta": "datalake/silver/budapest.sqlite", "contenido": "Tablas limpias y tipadas, una por entidad; cada punto lleva distrito asignado."},
        {"zona": "gold", "ruta": "datalake/gold/{temas,geo}/", "contenido": "Temas JSON y capas GeoJSON con cifras, series y listas listas para el sitio."},
        {"zona": "catalogo", "ruta": "datalake/catalogo/", "contenido": "linaje.jsonl, estado_fuentes.json y diccionario.json generado."},
    ]
    t["listas"]["brechas"] = [
        {"tema": "Seguridad", "motivo": "Ninguna de las fuentes entregadas publica delitos georreferenciados de Budapest; se muestran solo comisarías y bomberos de OSM."},
        {"tema": "Municipio", "motivo": "Presupuesto y gestión de los 23 ayuntamientos de distrito no están en las fuentes entregadas."},
        {"tema": "Escucha social", "motivo": "Sin fuente de redes sociales entre las entregadas."},
        {"tema": "Tráfico en vivo", "motivo": "GTFS-RT y FUTÁR de BKK requieren clave de API (registrada en el catálogo de Mobility Database, no consumida)."},
        {"tema": "Urban Atlas", "motivo": "La descarga requiere cuenta en land.copernicus.eu; se usan las capas HRL 2018 por estadística zonal."},
    ]
    cifra(t, "fuentes_ok", sum(1 for f in t["listas"]["fuentes"] if f["estado"] == "ok"), f"de {len(config.FUENTES)}", "Fuentes operativas", "lago", lago.HOY, "derivado")
    cifra(t, "bronze_mb", r(sum(x["bytes"] for x in por_fuente.values()) / 1e6, 1), "MB", "Volumen crudo acumulado en bronze", "lago", lago.HOY, "derivado")
    return t


# ------------------------------------------------------------------ capas geo
def capas_geo(con, filas):
    por_id = {f["distrito_id"]: f for f in filas}
    feats = []
    for d in lago.consultar(con, "SELECT distrito_id, geojson FROM distritos"):
        f = por_id[d["distrito_id"]]
        mp = geo.simplificar_mp(json.loads(d["geojson"])["coordinates"], tol=0.00012)
        props = {k: f[k] for k in f if k != "poi"}
        feats.append(geo.feature(geo.geojson_mp(mp), props))
    lago.escribir_json(G / "distritos.geojson", geo.coleccion(feats))

    par = seguro(con, "gtfs_paradas", "SELECT stop_id, nombre, lat, lon, salidas_dia_ref s, rutas_n, modos, distrito_id FROM gtfs_paradas WHERE salidas_dia_ref>0 AND tipo_ubicacion=0")
    lago.escribir_json(G / "paradas.geojson", geo.coleccion(
        geo.punto(p["lon"], p["lat"], {"n": p["nombre"], "s": p["s"], "r": p["rutas_n"], "m": p["modos"], "d": p["distrito_id"]}) for p in par))
    lin = seguro(con, "gtfs_lineas_geom", "SELECT * FROM gtfs_lineas_geom")
    orden = {"hev": 1, "ferry": 1, "trolebus": 2, "tranvia": 3, "metro": 4, "funicular": 4, "teleferico": 4}
    lin.sort(key=lambda x: orden.get(x["modo"], 0))
    lago.escribir_json(G / "lineas.geojson", geo.coleccion(
        geo.feature(json.loads(l["geojson"]), {"modo": l["modo"], "linea": l["nombre_corto"], "color": l["color"]}) for l in lin))
    disp = {x["estacion_id"]: x for x in seguro(con, "bubi_disponibilidad", "SELECT * FROM bubi_disponibilidad")}
    bubi = seguro(con, "bubi_estaciones", "SELECT * FROM bubi_estaciones")
    lago.escribir_json(G / "bubi.geojson", geo.coleccion(
        geo.punto(b["lon"], b["lat"], {"n": b["nombre"], "b": disp.get(b["estacion_id"], {}).get("bicis"),
                                       "c": disp.get(b["estacion_id"], {}).get("anclajes"), "o": b["origen"], "d": b["distrito_id"]}) for b in bubi))
    # Los sensores ciudadanos suelen estar en viviendas: en gold se publican redondeados a 3 decimales (~110 m)
    # y sin el nombre libre de la caja. La ubicación exacta queda solo en silver (no publicado) para asignar distrito.
    sens = [geo.punto(s["lon"], s["lat"], {"f": "sensor_community", "id": s["sensor_id"], "pm25": s["pm25"], "pm10": s["pm10"], "t": s["temperatura"], "ts": s["ts"], "d": s["distrito_id"]}, dec=3)
            for s in seguro(con, "sc_sensores", "SELECT * FROM sc_sensores WHERE (pm25 IS NOT NULL OR temperatura IS NOT NULL) AND lat IS NOT NULL")]
    for s in seguro(con, "osem_sensores", "SELECT box_id, box_nombre, lat, lon, distrito_id, MAX(ts) ts, MAX(CASE WHEN fenomeno_norm='pm25' THEN valor END) pm25, MAX(CASE WHEN fenomeno_norm='pm10' THEN valor END) pm10, MAX(CASE WHEN fenomeno_norm='temperatura' THEN valor END) t FROM osem_sensores WHERE vigente=1 AND lat IS NOT NULL GROUP BY box_id"):
        sens.append(geo.punto(s["lon"], s["lat"], {"f": "opensensemap", "id": s["box_id"], "pm25": s["pm25"], "pm10": s["pm10"], "t": s["t"], "ts": s["ts"], "d": s["distrito_id"]}, dec=3))
    lago.escribir_json(G / "sensores.geojson", geo.coleccion(sens))
    amb = {e["estacion"]: e for e in seguro(con, "eea_estaciones", "SELECT * FROM eea_estaciones")}
    t_amb = json.loads((T / "ambiente.json").read_text(encoding="utf-8")) if (T / "ambiente.json").exists() else {"listas": {}}
    lago.escribir_json(G / "eea.geojson", geo.coleccion(
        geo.punto(amb[e["estacion"]]["lon"], amb[e["estacion"]]["lat"], {k: e[k] for k in e}) for e in t_amb["listas"].get("estaciones", []) if e["estacion"] in amb))
    poi = seguro(con, "osm_poi", "SELECT categoria, subcategoria, nombre, lat, lon, distrito_id FROM osm_poi WHERE distrito_id IS NOT NULL")
    lago.escribir_json(G / "poi.geojson", geo.coleccion(
        geo.punto(p["lon"], p["lat"], {"c": p["categoria"], "s": p["subcategoria"], "n": p["nombre"], "d": p["distrito_id"]}) for p in poi))


def publicar(con, estado):
    ESTADO.clear()
    ESTADO.update(estado)
    filas = metricas_distrito(con)
    temas = [t_territorio(con, filas, estado), t_demografia(con, filas), t_economia(con, filas), t_turismo(con, filas),
             t_movilidad(con, filas), t_ambiente(con, filas), t_distritos(filas)]
    por_nombre = {t["tema"]: t for t in temas}
    temas.append(t_preguntas(filas, por_nombre["ambiente"], por_nombre["movilidad"]))
    for t in temas:
        completar_fuentes(t)
        lago.escribir_json(T / f"{t['tema']}.json", t)
    capas_geo(con, filas)
    lago.escribir_json(T / "catalogo.json", completar_fuentes(t_catalogo(con, estado)))
    # copia privada para el sitio (se sirve solo a través de /api/datos)
    if config.WEB_LAGO.exists():
        shutil.rmtree(config.WEB_LAGO)
    shutil.copytree(config.GOLD, config.WEB_LAGO)
    lago.log("gold", f"{len(temas) + 1} temas y {len(list(G.glob('*.geojson')))} capas publicados → web/lago")
