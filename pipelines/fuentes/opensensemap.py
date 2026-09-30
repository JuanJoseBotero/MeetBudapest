"""openSenseMap: senseBoxes exteriores dentro del bbox de Budapest con su última medición por sensor.

La consulta /boxes?full=true sobre un bbox puede tardar minutos; se piden las cajas (ligero), se filtran las
que midieron en los últimos 7 días y solo para esas se pide /boxes/{id}/sensors, que trae el último valor.
"""
import datetime as dt
import json

from pipelines import config
from pipelines.fuentes import osm_overpass
from pipelines.lib import lago

F = "opensensemap"
URL = "https://api.opensensemap.org/boxes"
DIAS_VIGENCIA = 7


def _norm(titulo):
    t = (titulo or "").lower().replace(" ", "")
    if "pm2.5" in t or "pm25" in t or "pm2,5" in t:
        return "pm25"
    if "pm10" in t:
        return "pm10"
    if "temp" in t:
        return "temperatura"
    if "feucht" in t or "humid" in t or "páratart" in t:
        return "humedad"
    if "druck" in t or "press" in t:
        return "presion"
    return "otro"


def _fecha(s):
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00")) if s else None


def _limite():
    return dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=DIAS_VIGENCIA)


def ingestar():
    params = {"bbox": ",".join(map(str, config.BBOX)), "exposure": "outdoor"}
    b = lago.http(URL, params=params, timeout=120)
    lago.guardar_bronze(F, "boxes.json", b, URL)
    activas = [x["_id"] for x in json.loads(b) if (_fecha(x.get("lastMeasurementAt")) or _limite()) > _limite()]
    for i in activas:
        url = f"{URL}/{i}/sensors"
        try:
            lago.guardar_bronze(F, f"sensores/{i}.json", lago.http(url, timeout=60, reintentos=2), url)
        except Exception as e:  # noqa: BLE001 - una caja caída no invalida el resto
            lago.log(F, f"caja {i}: {e}")
    lago.log(F, f"{len(activas)} cajas activas en los últimos {DIAS_VIGENCIA} días")
    return {"archivos": 1 + len(activas)}


def silver(con):
    d, fecha = lago.leer_bronze_json(F, "boxes.json")
    asignar = osm_overpass.asignador(con)
    limite = _limite()
    filas = []
    for b in d or []:
        lon, lat = (b.get("currentLocation") or {}).get("coordinates", [None, None])[:2]
        detalle = config.BRONZE / F / fecha / "sensores" / f"{b['_id']}.json"
        sensores = json.loads(detalle.read_text(encoding="utf-8")).get("sensors", []) if detalle.exists() else b.get("sensors", [])
        for s in sensores:
            ult = s.get("lastMeasurement") if isinstance(s.get("lastMeasurement"), dict) else {}
            ts = ult.get("createdAt")
            filas.append({"box_id": b["_id"], "box_nombre": b.get("name"), "sensor_id": s.get("_id"), "fenomeno": s.get("title"),
                          "fenomeno_norm": _norm(s.get("title")), "unidad": s.get("unit"), "tipo_sensor": s.get("sensorType"),
                          "valor": lago.num(ult.get("value")), "ts": ts, "vigente": int(bool(ts) and _fecha(ts) >= limite),
                          "lat": lat, "lon": lon, "distrito_id": asignar(lon, lat)})
    lago.escribir_tabla(con, "osem_sensores", filas)
    lago.log(F, f"silver osem_sensores: {len(filas)} sensores en {len(d or [])} cajas")
