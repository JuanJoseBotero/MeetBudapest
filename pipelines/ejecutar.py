"""Orquestador del lago: bronze (ingesta) → silver (SQLite) → gold (temas del sitio) → catálogo y diccionario.

Uso (desde la raíz del proyecto):
    python -m pipelines.ejecutar                  # todo
    python -m pipelines.ejecutar --solo bubi,sensor_community   # refresco de fuentes en vivo
    python -m pipelines.ejecutar --sin-descarga   # reconstruye silver/gold desde el último bronze
    python -m pipelines.ejecutar --pbf            # además descarga el .osm.pbf de Geofabrik a bronze
"""
import argparse
import json
import sys
import time
import traceback

from pipelines import config
from pipelines.fuentes import (bkk_gtfs, bubi, copernicus, eea, eurostat, geofabrik, ksh, mobilitydb, open_meteo,
                               opensensemap, osm_overpass, sensor_community)
from pipelines.lib import lago

# El orden importa: KSH alimenta la tabla distritos, y los límites OSM se usan para asignar distrito al resto.
ORDEN = [ksh, osm_overpass, geofabrik, copernicus, mobilitydb, bkk_gtfs, bubi, eurostat, eea, sensor_community,
         opensensemap, open_meteo]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--solo", help="fuentes separadas por coma (ids de config.FUENTES)")
    ap.add_argument("--sin-descarga", action="store_true", help="no llama a las APIs; usa el último bronze")
    ap.add_argument("--sin-gold", action="store_true")
    ap.add_argument("--pbf", action="store_true", help="descarga hungary-latest.osm.pbf (~350 MB)")
    a = ap.parse_args(argv)
    geofabrik.DESCARGAR_PBF = a.pbf
    solo = set(a.solo.split(",")) if a.solo else None

    con = lago.conectar()
    estado_path = config.CATALOGO / "estado_fuentes.json"
    estado = json.loads(estado_path.read_text(encoding="utf-8")) if estado_path.exists() else {}
    for mod in ORDEN:
        fid = mod.F
        if solo and fid not in solo:
            continue
        t0 = time.time()
        e = estado.setdefault(fid, {})
        try:
            if not a.sin_descarga:
                lago.log(fid, "ingesta → bronze")
                e["ingesta"] = mod.ingestar()
                e["ultima_ingesta"] = lago.ahora()
            # silver() puede devolver "candidata": la fuente responde pero aún no aporta datos utilizables al lago
            e.update(estado=mod.silver(con) or "ok", error=None, ultima_silver=lago.ahora())
        except Exception as ex:  # noqa: BLE001 - una fuente caída no detiene el lago
            traceback.print_exc()
            e.update(estado="error", error=f"{type(ex).__name__}: {ex}"[:400], ultimo_intento=lago.ahora())
        e["segundos"] = round(time.time() - t0, 1)
        lago.escribir_json(estado_path, estado)

    if not a.sin_gold:
        from pipelines import gold, diccionario
        gold.publicar(con, estado)
        diccionario.generar(con)
    errores = [k for k, v in estado.items() if v.get("estado") == "error"]
    print("\nFuentes con error:", ", ".join(errores) if errores else "ninguna")
    return 1 if errores else 0


if __name__ == "__main__":
    sys.exit(main())
