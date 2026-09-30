"""MOL Bubi: estaciones y disponibilidad de la bicicleta pública (feed en vivo del operador nextbike, dominio bh).

Desde 2025 el feed público de MOL Bubi solo publica los totales del sistema (flota objetivo) y no las estaciones.
Cuando eso ocurre, las estaciones se toman de OSM (amenity=bicycle_rental ya ingestado por osm_overpass) y se
marcan con origen='osm' y disponibilidad NULL: la ubicación es observada, la disponibilidad no existe.
"""
import json

from pipelines import config
from pipelines.fuentes import osm_overpass
from pipelines.lib import lago

F = "bubi"


def ingestar():
    url = config.FUENTES[F]["endpoint"]
    lago.guardar_bronze(F, f"nextbike_bh_{lago.ahora()[11:16].replace(':', '')}.json", lago.http(url, timeout=90), url)
    return {"archivos": 1}


def _ultimo():
    carpetas = sorted((config.BRONZE / F).glob("*/nextbike_bh_*.json"))
    return carpetas[-1] if carpetas else None


def silver(con):
    p = _ultimo()
    d = json.loads(p.read_text(encoding="utf-8"))
    ts = f"{p.parent.name}T{p.stem[-4:-2]}:{p.stem[-2:]}:00Z"
    asignar = osm_overpass.asignador(con)
    filas, sistema = [], {}
    for pais in d.get("countries", []):
        sistema = pais
        for ciudad in pais.get("cities", []):
            for e in ciudad.get("places", []):
                if e.get("bike") or not e.get("number"):  # bicicletas sueltas no son estaciones
                    continue
                filas.append({"estacion_id": e["uid"], "numero": str(e.get("number")), "nombre": e.get("name"),
                              "lat": e["lat"], "lon": e["lng"], "bicis": e.get("bikes_available_to_rent", e.get("bikes")),
                              "anclajes": e.get("bike_racks"), "anclajes_libres": e.get("free_racks"), "ts": ts,
                              "origen": "nextbike_vivo", "distrito_id": asignar(e["lng"], e["lat"])})
    en_vivo = len(filas)
    if not filas:
        for e in lago.consultar(con, "SELECT osm_id, nombre, lat, lon, distrito_id FROM osm_poi WHERE subcategoria='bicycle_rental'"):
            filas.append({"estacion_id": e["osm_id"], "numero": None, "nombre": e["nombre"], "lat": e["lat"], "lon": e["lon"],
                          "bicis": None, "anclajes": None, "anclajes_libres": None, "ts": ts, "origen": "osm",
                          "distrito_id": e["distrito_id"]})
        lago.log(F, "el feed no publica estaciones: respaldo con amenity=bicycle_rental de OSM")
    lago.escribir_tabla(con, "bubi_estaciones", filas)
    ya = lago.tabla_existe(con, "bubi_historico") and con.execute("SELECT 1 FROM bubi_historico WHERE ts=?", (ts,)).fetchone()
    if not ya:
        lago.escribir_tabla(con, "bubi_historico", [{
            "ts": ts, "estaciones": en_vivo,
            "bicis": sum(f["bicis"] or 0 for f in filas) if en_vivo else None,  # sin estaciones, available_bikes llega en 0 aunque haya flota
            "anclajes": sum(f["anclajes"] or 0 for f in filas) if en_vivo else None,
            "flota_objetivo": sistema.get("set_point_bikes")}], modo="anexar")
    lago.log(F, f"silver bubi_estaciones: {len(filas)} (en vivo: {en_vivo})")
