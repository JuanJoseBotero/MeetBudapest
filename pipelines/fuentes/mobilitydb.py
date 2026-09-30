"""Mobility Database: catálogo de feeds GTFS / GTFS-RT de Budapest (linaje y espejo del GTFS de BKK)."""
import csv
import io

from pipelines import config
from pipelines.lib import lago

F = "mobilitydb"


def ingestar():
    url = config.FUENTES[F]["endpoint"]
    lago.guardar_bronze(F, "feeds_v2.csv", lago.http(url, timeout=180), url)
    return {"archivos": 1}


def silver(con):
    p = lago.ultimo_bronze(F, "feeds_v2.csv")
    filas = []
    for r in csv.DictReader(io.StringIO(p.read_text(encoding="utf-8-sig"))):
        if r.get("location.country_code") != "HU" or "Budapest" not in (r.get("location.municipality") or ""):
            continue
        bb = [r.get(f"location.bounding_box.{k}") for k in ("minimum_latitude", "maximum_latitude", "minimum_longitude", "maximum_longitude")]
        filas.append({"mdb_id": r["id"], "tipo": r["data_type"], "entidad": r.get("entity_type") or None,
                      "proveedor": r.get("provider"), "oficial": r.get("is_official"), "estado": r.get("status"),
                      "url_directa": r.get("urls.direct_download"), "url_espejo": r.get("urls.latest") or None,
                      "requiere_clave": 1 if (r.get("urls.authentication_type") or "0") not in ("", "0") else 0,
                      "bbox": ",".join(b for b in bb if b) or None, "extraido": r.get("location.bounding_box.extracted_on")})
    lago.escribir_tabla(con, "mdb_feeds", filas)
    lago.log(F, f"silver mdb_feeds: {len(filas)}")
