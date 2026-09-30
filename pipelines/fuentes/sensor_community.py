"""Sensor.Community: instantánea (promedio 5 min) de sensores ciudadanos en 20 km alrededor del centro."""
import json
import statistics

from pipelines import config
from pipelines.fuentes import osm_overpass
from pipelines.lib import lago

F = "sensor_community"
URL = "https://data.sensor.community/airrohr/v1/filter/area={},{},20"


def ingestar():
    url = URL.format(*config.CENTRO)
    lago.guardar_bronze(F, f"filtro_area_{lago.ahora()[11:16].replace(':', '')}.json", lago.http(url, timeout=120), url)
    return {"archivos": 1}


def silver(con):
    ultimos = sorted((config.BRONZE / F).glob("*/filtro_area_*.json"))
    p = ultimos[-1]
    d = json.loads(p.read_text(encoding="utf-8"))
    asignar = osm_overpass.asignador(con)
    sensores = {}
    for m in d:
        loc = m.get("location", {})
        if str(loc.get("indoor", 0)) == "1":
            continue
        sid = m["sensor"]["id"]
        lat, lon = lago.num(loc.get("latitude")), lago.num(loc.get("longitude"))
        s = sensores.setdefault(sid, {"sensor_id": sid, "ubicacion_id": loc.get("id"),
                                      "tipo_sensor": m["sensor"].get("sensor_type", {}).get("name"), "lat": lat, "lon": lon,
                                      "pm25": None, "pm10": None, "temperatura": None, "humedad": None, "ts": m.get("timestamp"),
                                      "distrito_id": asignar(lon, lat)})
        for v in m.get("sensordatavalues", []):
            campo = {"P2": "pm25", "P1": "pm10", "temperature": "temperatura", "humidity": "humedad"}.get(v["value_type"])
            if campo:
                s[campo] = lago.num(v["value"])
        s["ts"] = max(s["ts"] or "", m.get("timestamp") or "")
    # filtro de plausibilidad: los SDS011 saturan con niebla (>500 µg/m³ no es un dato utilizable)
    filas = [s for s in sensores.values() if not (s["pm25"] and s["pm25"] > 500)]
    lago.escribir_tabla(con, "sc_sensores", filas)
    pm25 = [s["pm25"] for s in filas if s["pm25"] is not None and s["distrito_id"]]
    pm10 = [s["pm10"] for s in filas if s["pm10"] is not None and s["distrito_id"]]
    ts = f"{p.parent.name}T{p.stem[-4:-2]}:{p.stem[-2:]}:00Z"
    ya = lago.tabla_existe(con, "sc_historico") and con.execute("SELECT 1 FROM sc_historico WHERE ts=?", (ts,)).fetchone()
    if pm25 and not ya:
        lago.escribir_tabla(con, "sc_historico", [{"ts": ts, "sensores_pm": len(pm25),
                                                   "pm25_mediana": round(statistics.median(pm25), 1),
                                                   "pm10_mediana": round(statistics.median(pm10), 1) if pm10 else None}], modo="anexar")
    lago.log(F, f"silver sc_sensores: {len(filas)} ({len(pm25)} de partículas en Budapest)")
