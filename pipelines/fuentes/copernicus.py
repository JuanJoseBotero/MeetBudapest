"""Copernicus Land (HRL 2018, 10 m): sellado del suelo y cobertura arbórea por distrito.

Se usa la estadística zonal del ImageServer público de la EEA (computeStatisticsHistograms) con el polígono
de cada distrito, así no hace falta descargar ni leer rásteres GeoTIFF. El Urban Atlas requiere cuenta
en land.copernicus.eu: si se deja su GeoPackage en bronze/copernicus/manual/ queda catalogado igualmente.
"""
import json

from pipelines.lib import geo, lago

F = "copernicus"
SRV = "https://image.discomap.eea.europa.eu/arcgis/rest/services/GioLandPublic/{}/ImageServer"
CAPAS = {"imperviousness_2018": "HRL_ImperviousnessDensity_2018", "tree_cover_2018": "HRL_TreeCoverDensity_2018"}
UMBRAL_ALTO = {"imperviousness_2018": 80, "tree_cover_2018": 10}


def ingestar():
    con = lago.conectar()
    distritos = lago.consultar(con, "SELECT distrito_id, geojson FROM distritos ORDER BY distrito_id")
    if not distritos:
        raise RuntimeError("Copernicus necesita la tabla silver distritos (ejecutar osm_overpass antes)")
    n = 0
    for capa, servicio in CAPAS.items():
        for d in distritos:
            mp = geo.simplificar_mp(json.loads(d["geojson"])["coordinates"], tol=0.0003)
            geometria = json.dumps({"rings": geo.anillos_esri(mp), "spatialReference": {"wkid": 4326}})
            url = SRV.format(servicio) + "/computeStatisticsHistograms"
            b = lago.http(url, data={"geometry": geometria, "geometryType": "esriGeometryPolygon", "f": "json"}, timeout=180)
            if b'"error"' in b[:40] or b'"statistics":[]' in b[:40]:
                raise RuntimeError(f"distrito {d['distrito_id']}: respuesta vacía o error {b[:200]!r}")
            lago.guardar_bronze(F, f"{capa}/distrito_{d['distrito_id']:02d}.json", b, url)
            n += 1
        lago.log(F, f"{capa}: {len(distritos)} distritos")
    return {"archivos": n}


def silver(con):
    filas = []
    for capa in CAPAS:
        for d_id in range(1, 24):
            j, _ = lago.leer_bronze_json(F, f"{capa}/distrito_{d_id:02d}.json")
            if not j or not j.get("histograms"):
                continue
            h = j["histograms"][0]
            conteos = h["counts"]
            # el histograma va de min-0.5 en pasos de 1: el índice es el valor del píxel (0–100 válidos)
            base = int(round(h["min"] + 0.5))
            validos = [(base + i, c) for i, c in enumerate(conteos) if 0 <= base + i <= 100 and c]
            total = sum(c for _, c in validos)
            if not total:
                continue
            media = sum(v * c for v, c in validos) / total
            var = sum(c * (v - media) ** 2 for v, c in validos) / total
            acum, mediana = 0, None
            for v, c in validos:
                acum += c
                if acum >= total / 2:
                    mediana = v
                    break
            alto = sum(c for v, c in validos if v >= UMBRAL_ALTO[capa])
            filas.append({"distrito_id": d_id, "capa": capa, "media": round(media, 2), "mediana": mediana,
                          "desviacion": round(var ** 0.5, 2), "pct_alto": round(100 * alto / total, 2), "pixeles": total})
    lago.escribir_tabla(con, "copernicus_distrito", filas)
    lago.log(F, f"silver copernicus_distrito: {len(filas)}")
