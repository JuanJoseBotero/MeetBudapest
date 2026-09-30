"""Geofabrik: versión del extracto OSM de Hungría (state.txt), polígono de recorte y, opcionalmente, el .osm.pbf.

El .osm.pbf (~350 MB) solo se descarga con --pbf: queda en bronze como instantánea reproducible para
procesarlo con osmium/ogr2ogr fuera de este pipeline (la biblioteca estándar no decodifica PBF).
"""
import urllib.request

from pipelines import config
from pipelines.lib import lago

F = "geofabrik"
BASE = "https://download.geofabrik.de/europe/"
PBF = BASE + "hungary-latest.osm.pbf"
DESCARGAR_PBF = False  # el orquestador lo activa con --pbf


def ingestar():
    lago.guardar_bronze(F, "state.txt", lago.http(BASE + "hungary-updates/state.txt"), BASE + "hungary-updates/state.txt")
    lago.guardar_bronze(F, "hungary.poly", lago.http(BASE + "hungary.poly"), BASE + "hungary.poly")
    req = urllib.request.Request(PBF, method="HEAD", headers={"User-Agent": config.USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as r:
        tam = r.headers.get("Content-Length")
    lago.guardar_bronze(F, "pbf_head.txt", f"{PBF}\n{tam}\n", PBF)
    if DESCARGAR_PBF:
        lago.log(F, f"descargando .osm.pbf ({int(tam or 0)/1e6:.0f} MB)")
        destino = lago.ruta_bronze(F, "hungary-latest.osm.pbf")
        with urllib.request.urlopen(urllib.request.Request(PBF, headers={"User-Agent": config.USER_AGENT}), timeout=1800) as r, open(destino, "wb") as f:
            while bloque := r.read(1 << 20):
                f.write(bloque)
        lago.registrar_linaje(F, destino, PBF, destino.stat().st_size, "no-calculado")
    return {"archivos": 3 + DESCARGAR_PBF}


def silver(con):
    estado = dict(l.split("=", 1) for l in lago.ultimo_bronze(F, "state.txt").read_text().splitlines() if "=" in l and not l.startswith("#"))
    head = lago.ultimo_bronze(F, "pbf_head.txt").read_text().splitlines()
    poly = lago.ultimo_bronze(F, "hungary.poly")
    vertices = sum(1 for l in poly.read_text().splitlines() if len(l.split()) == 2 and all(lago.num(x) is not None for x in l.split()))
    fila = {"fecha_replica": estado.get("timestamp", "").replace("\\", ""), "secuencia": int(estado.get("sequenceNumber", 0)),
            "url_pbf": head[0], "pbf_bytes": int(head[1]) if len(head) > 1 and head[1].isdigit() else None,
            "pbf_en_bronze": 1 if lago.ultimo_bronze(F, "hungary-latest.osm.pbf") else 0,
            "poly_vertices": vertices, "ingesta": poly.parent.name}
    lago.escribir_tabla(con, "geofabrik_extracto", [fila])
    lago.log(F, f"silver geofabrik_extracto: réplica {fila['fecha_replica']}")
