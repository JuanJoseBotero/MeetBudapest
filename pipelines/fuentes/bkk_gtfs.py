"""BKK GTFS estático: rutas, paradas, oferta programada de un día laborable y trazados de modos guiados.

Si el servidor de BKK falla, se usa el espejo de Mobility Database (mdb-990, antes TransitFeeds tfs-42).
"""
import collections
import csv
import datetime as dt
import io
import json
import zipfile

from pipelines import config
from pipelines.fuentes import osm_overpass
from pipelines.lib import geo, lago

F = "bkk_gtfs"
URL_BKK = config.FUENTES[F]["endpoint"]
URL_ESPEJO = "https://files.mobilitydatabase.org/mdb-990/latest.zip"

MODOS = {0: "tranvia", 900: "tranvia", 1: "metro", 401: "metro", 2: "hev", 109: "hev", 100: "tren", 3: "bus",
         4: "ferry", 1000: "ferry", 1200: "ferry", 11: "trolebus", 800: "trolebus", 7: "funicular", 1400: "funicular",
         6: "teleferico", 1300: "teleferico"}
GUIADOS = {"metro", "tranvia", "trolebus", "hev", "ferry", "funicular", "teleferico"}


def modo(t):
    t = int(t)
    return MODOS.get(t) or ("bus" if 700 <= t < 800 else "otro")


def ingestar():
    for url, origen in ((URL_BKK, "bkk"), (URL_ESPEJO, "mobilitydb")):
        try:
            b = lago.http(url, timeout=600)
            zipfile.ZipFile(io.BytesIO(b)).testzip()
            lago.guardar_bronze(F, "budapest_gtfs.zip", b, url)
            lago.guardar_bronze(F, "origen.txt", origen, url)
            lago.log(F, f"GTFS {len(b)/1e6:.1f} MB desde {origen}")
            return {"archivos": 1, "origen": origen}
        except Exception as e:  # noqa: BLE001
            lago.log(F, f"{origen} falló: {e}")
    raise RuntimeError("GTFS no disponible en BKK ni en Mobility Database")


def _leer(z, nombre):
    if nombre not in z.namelist():
        return []
    return csv.DictReader(io.TextIOWrapper(z.open(nombre), encoding="utf-8-sig"))


def _fecha(s):
    return dt.date(int(s[:4]), int(s[4:6]), int(s[6:8]))


def silver(con):
    p = lago.ultimo_bronze(F, "budapest_gtfs.zip")
    if not p:
        raise RuntimeError("sin GTFS en bronze")
    origen_p = lago.ultimo_bronze(F, "origen.txt")
    z = zipfile.ZipFile(p)

    # -------- calendario: día de referencia = primer miércoles vigente desde la fecha de ingesta
    cal = list(_leer(z, "calendar.txt"))
    excep = collections.defaultdict(dict)
    for r in _leer(z, "calendar_dates.txt"):
        excep[r["date"]][r["service_id"]] = r["exception_type"]
    fechas = [_fecha(r["start_date"]) for r in cal] + [_fecha(r["end_date"]) for r in cal] + [_fecha(d) for d in excep]
    inicio, fin = min(fechas), max(fechas)
    ref = max(dt.date.fromisoformat(p.parent.name), inicio)
    while ref.weekday() != 2 and ref < fin:
        ref += dt.timedelta(days=1)
    clave = ref.strftime("%Y%m%d")
    activos = {r["service_id"] for r in cal if r["wednesday"] == "1" and r["start_date"] <= clave <= r["end_date"]}
    for sid, tipo in excep.get(clave, {}).items():
        (activos.add if tipo == "1" else activos.discard)(sid)

    # -------- rutas y viajes
    rutas = {r["route_id"]: r for r in _leer(z, "routes.txt")}
    viaje_ruta, viajes_por_ruta, formas = {}, collections.Counter(), collections.defaultdict(collections.Counter)
    for t in _leer(z, "trips.txt"):
        if t["service_id"] in activos:
            viaje_ruta[t["trip_id"]] = t["route_id"]
            viajes_por_ruta[t["route_id"]] += 1
            if t.get("shape_id"):
                formas[t["route_id"]][t["shape_id"]] += 1
    lago.log(F, f"día ref {ref} · {len(activos)} servicios · {len(viaje_ruta)} viajes")

    # -------- stop_times en streaming (millones de filas): detenciones y rutas por parada
    salidas, rutas_parada, detenciones = collections.Counter(), collections.defaultdict(set), 0
    for st in _leer(z, "stop_times.txt"):
        rid = viaje_ruta.get(st["trip_id"])
        if rid:
            salidas[st["stop_id"]] += 1
            rutas_parada[st["stop_id"]].add(rid)
            detenciones += 1

    filas_r = [{"route_id": rid, "nombre_corto": r.get("route_short_name"),
                "nombre_largo": r.get("route_long_name") or r.get("route_desc"), "tipo_gtfs": int(r["route_type"]),
                "modo": modo(r["route_type"]), "color": "#" + (r.get("route_color") or "888888"),
                "viajes_dia_ref": viajes_por_ruta.get(rid, 0)} for rid, r in rutas.items()]
    lago.escribir_tabla(con, "gtfs_rutas", filas_r)

    asignar = osm_overpass.asignador(con)
    filas_p = []
    for s in _leer(z, "stops.txt"):
        lat, lon = lago.num(s.get("stop_lat")), lago.num(s.get("stop_lon"))
        sid = s["stop_id"]
        rs = rutas_parada.get(sid, set())
        filas_p.append({"stop_id": sid, "nombre": s.get("stop_name"), "lat": lat, "lon": lon,
                        "tipo_ubicacion": int(s.get("location_type") or 0), "estacion_padre": s.get("parent_station") or None,
                        "accesible": int(s.get("wheelchair_boarding") or 0), "salidas_dia_ref": salidas.get(sid, 0),
                        "rutas_n": len(rs), "modos": ",".join(sorted({modo(rutas[r]["route_type"]) for r in rs})),
                        "distrito_id": asignar(lon, lat)})
    lago.escribir_tabla(con, "gtfs_paradas", filas_p)

    # -------- trazados: shape más frecuente por ruta guiada
    elegidas = {}
    for rid, c in formas.items():
        if modo(rutas[rid]["route_type"]) in GUIADOS and c:
            elegidas[c.most_common(1)[0][0]] = rid
    puntos = collections.defaultdict(list)
    for s in _leer(z, "shapes.txt"):
        if s["shape_id"] in elegidas:
            puntos[s["shape_id"]].append((int(s["shape_pt_sequence"]), float(s["shape_pt_lon"]), float(s["shape_pt_lat"])))
    filas_g = []
    for sh, rid in elegidas.items():
        pts = [[x, y] for _, x, y in sorted(puntos.get(sh, []))]
        if len(pts) >= 2:
            r = rutas[rid]
            filas_g.append({"route_id": rid, "modo": modo(r["route_type"]), "nombre_corto": r.get("route_short_name"),
                            "color": "#" + (r.get("route_color") or "888888"),
                            "geojson": json.dumps({"type": "LineString", "coordinates": geo.simplificar_linea(pts, 0.0001)})})
    lago.escribir_tabla(con, "gtfs_lineas_geom", filas_g)

    info = next(iter(_leer(z, "feed_info.txt")), {})
    lago.escribir_tabla(con, "gtfs_feed", [{
        "editor": info.get("feed_publisher_name"), "version": info.get("feed_version"),
        "inicio": info.get("feed_start_date") or inicio.strftime("%Y%m%d"), "fin": info.get("feed_end_date") or fin.strftime("%Y%m%d"),
        "dia_referencia": ref.isoformat(), "viajes_dia_ref": len(viaje_ruta), "detenciones_dia_ref": detenciones,
        "origen": origen_p.read_text().strip() if origen_p else "bkk"}])
    lago.log(F, f"silver: {len(filas_r)} rutas, {len(filas_p)} paradas, {len(filas_g)} trazados, {detenciones} detenciones")
