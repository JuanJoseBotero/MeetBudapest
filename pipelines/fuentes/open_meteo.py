"""Open-Meteo: histórico diario ERA5 (2000→ayer), pronóstico horario y calidad del aire CAMS Europa."""
import datetime as dt

from pipelines import config
from pipelines.lib import lago

F = "open_meteo"
LAT, LON = config.CENTRO


def ingestar():
    ayer = (dt.date.today() - dt.timedelta(days=1)).isoformat()
    urls = {
        "archivo_diario.json": ("https://archive-api.open-meteo.com/v1/archive", {
            "latitude": LAT, "longitude": LON, "start_date": "2000-01-01", "end_date": ayer, "timezone": config.ZONA_HORARIA,
            "daily": "temperature_2m_max,temperature_2m_min,temperature_2m_mean,precipitation_sum"}),
        "pronostico.json": ("https://api.open-meteo.com/v1/forecast", {
            "latitude": LAT, "longitude": LON, "timezone": config.ZONA_HORARIA, "past_days": 2, "forecast_days": 3,
            "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code",
            "hourly": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m"}),
        "calidad_aire.json": ("https://air-quality-api.open-meteo.com/v1/air-quality", {
            "latitude": LAT, "longitude": LON, "timezone": config.ZONA_HORARIA, "past_days": 2, "forecast_days": 3,
            "hourly": "pm2_5,pm10,nitrogen_dioxide,ozone,european_aqi", "domains": "cams_europe"}),
    }
    for nombre, (url, p) in urls.items():
        lago.guardar_bronze(F, nombre, lago.http(url, params=p, timeout=180), url)
    return {"archivos": len(urls)}


def silver(con):
    a, _ = lago.leer_bronze_json(F, "archivo_diario.json")
    dd = a["daily"]
    lago.escribir_tabla(con, "meteo_diario", [
        {"fecha": f, "tmax": dd["temperature_2m_max"][i], "tmin": dd["temperature_2m_min"][i],
         "tmedia": dd["temperature_2m_mean"][i], "precipitacion": dd["precipitation_sum"][i]}
        for i, f in enumerate(dd["time"])])
    p, _ = lago.leer_bronze_json(F, "pronostico.json")
    q, _ = lago.leer_bronze_json(F, "calidad_aire.json")
    ph, qh = p["hourly"], q["hourly"]
    idx_q = {h: i for i, h in enumerate(qh["time"])}
    filas = []
    for i, h in enumerate(ph["time"]):
        j = idx_q.get(h)
        g = (lambda k: qh[k][j] if j is not None else None)
        filas.append({"hora": h, "temperatura": ph["temperature_2m"][i], "humedad": ph["relative_humidity_2m"][i],
                      "precipitacion": ph["precipitation"][i], "viento": ph["wind_speed_10m"][i], "pm25": g("pm2_5"),
                      "pm10": g("pm10"), "no2": g("nitrogen_dioxide"), "o3": g("ozone"), "eaqi": g("european_aqi")})
    lago.escribir_tabla(con, "meteo_horario", filas)
    lago.log(F, f"silver meteo_diario: {len(dd['time'])} días · meteo_horario: {len(filas)} horas")
