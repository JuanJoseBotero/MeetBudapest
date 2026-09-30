"""EEA Air Quality e-Reporting: estadísticas anuales oficiales por estación en Budapest (DiscoData SQL)."""
import json

from pipelines.fuentes import osm_overpass
from pipelines.lib import lago

F = "eea"
SQL_URL = "https://discodata.eea.europa.eu/sql"
AGREGACIONES = ("P1Y", "P1Y-daysAbove50", "P1Y-hrsAbove200", "P1Y-dmaxAbove120", "SOMO35")
CONSULTA = ("SELECT AirQualityStationEoICode, AQStationName, AirQualityStationType, AirQualityStationArea, Longitude, Latitude, "
            "Altitude, AirPollutant, DataAggregationProcessId, YearOfStatistics, AirPollutionLevel, UnitOfAirpollutionLevel, "
            "DataCoverage, Verification, SourceDataFlow FROM [AirQualityDataFlows].[latest].[AirQualityStatistics] "
            "WHERE CityCode LIKE 'HU001C%' AND AirPollutant IN ('PM2.5','PM10','NO2','O3') "
            f"AND DataAggregationProcessId IN ({','.join(repr(a) for a in AGREGACIONES)})")


def ingestar():
    pagina, n = 1, 0
    while True:
        b = lago.http(SQL_URL, params={"query": CONSULTA, "p": pagina, "nrOfHits": 1000}, timeout=240)
        lago.guardar_bronze(F, f"aq_statistics_p{pagina}.json", b, SQL_URL + "?query=" + CONSULTA[:120])
        filas = json.loads(b).get("results", [])
        n += len(filas)
        if len(filas) < 1000:
            break
        pagina += 1
    lago.log(F, f"{n} estadísticas en {pagina} páginas")
    return {"archivos": pagina, "filas": n}


def silver(con):
    ultimo = lago.ultimo_bronze(F, "aq_statistics_p1.json")
    filas = []
    for p in sorted(ultimo.parent.glob("aq_statistics_p*.json")):
        filas += json.loads(p.read_text(encoding="utf-8")).get("results", [])
    asignar = osm_overpass.asignador(con)
    est, stats = {}, []
    for r in filas:
        cod = r["AirQualityStationEoICode"].strip()
        est[cod] = {"estacion": cod, "nombre": (r["AQStationName"] or "").strip('"'), "tipo": r["AirQualityStationType"],
                    "area": r["AirQualityStationArea"], "lat": r["Latitude"], "lon": r["Longitude"], "altitud": r["Altitude"],
                    "distrito_id": asignar(r["Longitude"], r["Latitude"])}
        stats.append({"estacion": cod, "contaminante": r["AirPollutant"], "agregacion": r["DataAggregationProcessId"],
                      "anio": r["YearOfStatistics"], "valor": r["AirPollutionLevel"], "unidad": r["UnitOfAirpollutionLevel"],
                      "cobertura": r["DataCoverage"], "verificacion": r["Verification"], "flujo": r["SourceDataFlow"]})
    lago.escribir_tabla(con, "eea_estaciones", est.values())
    lago.escribir_tabla(con, "eea_estadisticas", stats)
    lago.log(F, f"silver eea: {len(est)} estaciones, {len(stats)} estadísticas")
