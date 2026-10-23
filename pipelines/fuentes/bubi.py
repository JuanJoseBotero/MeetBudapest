"""MOL Bubi: feed en vivo del operador (nextbike, dominio bh).

La fuente solo cuenta como integrada si el feed publica estaciones. Hoy solo trae los totales del sistema,
así que queda como CANDIDATA: su respuesta se guarda en bronze para vigilar cuándo vuelve a publicarlas,
pero no se escribe nada suyo en silver. Las ubicaciones de las estaciones salen de OSM (osm_poi,
amenity=bicycle_rental con red MOL Bubi) y no tienen disponibilidad.
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
    sistema, vivas = {}, []
    for pais in d.get("countries", []):
        sistema = pais
        for ciudad in pais.get("cities", []):
            vivas += [e for e in ciudad.get("places", []) if not e.get("bike") and e.get("number")]  # sin bicis sueltas

    if not vivas:
        # Candidata: no se guarda nada de F07 en silver; las estaciones vienen de OSM (F02)
        estaciones = [{"estacion_id": e["osm_id"], "nombre": e["nombre"], "lat": e["lat"], "lon": e["lon"], "origen": "osm",
                       "distrito_id": e["distrito_id"]}
                      for e in lago.consultar(con, """SELECT osm_id, nombre, lat, lon, distrito_id FROM osm_poi
                                                     WHERE subcategoria='bicycle_rental' AND lower(red) LIKE '%bubi%'""")]
        lago.escribir_tabla(con, "bubi_estaciones", estaciones)
        con.execute("DROP TABLE IF EXISTS bubi_disponibilidad")
        if lago.tabla_existe(con, "bubi_historico"):  # instantáneas sin estaciones no son datos integrados
            con.execute("DELETE FROM bubi_historico WHERE estaciones = 0 OR estaciones IS NULL")
        con.commit()
        lago.log(F, f"CANDIDATA: el feed no publica estaciones (flota declarada {sistema.get('set_point_bikes')}); "
                    f"{len(estaciones)} estaciones MOL Bubi desde OSM")
        return "candidata"

    lago.escribir_tabla(con, "bubi_estaciones", [
        {"estacion_id": e["uid"], "nombre": e.get("name"), "lat": e["lat"], "lon": e["lng"], "origen": "nextbike_vivo",
         "distrito_id": asignar(e["lng"], e["lat"])} for e in vivas])
    disp = [{"estacion_id": e["uid"], "numero": str(e.get("number")), "bicis": e.get("bikes_available_to_rent", e.get("bikes")),
             "anclajes": e.get("bike_racks"), "anclajes_libres": e.get("free_racks"), "ts": ts} for e in vivas]
    lago.escribir_tabla(con, "bubi_disponibilidad", disp)
    ya = lago.tabla_existe(con, "bubi_historico") and con.execute("SELECT 1 FROM bubi_historico WHERE ts=?", (ts,)).fetchone()
    if not ya:
        lago.escribir_tabla(con, "bubi_historico", [{"ts": ts, "estaciones": len(vivas), "bicis": sum(x["bicis"] or 0 for x in disp),
                                                     "anclajes": sum(x["anclajes"] or 0 for x in disp),
                                                     "flota_objetivo": sistema.get("set_point_bikes")}], modo="anexar")
    lago.log(F, f"silver bubi: {len(vivas)} estaciones con disponibilidad en vivo")
    return "ok"
