"""Configuración única del lago de datos Cerebro Budapest.

Todo el pipeline usa solo la biblioteca estándar de Python (>= 3.10): sin pip, sin entornos virtuales.
"""
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
LAGO = RAIZ / "datalake"
BRONZE = LAGO / "bronze"      # crudo, inmutable, particionado por fuente/fecha de ingesta
SILVER = LAGO / "silver"      # limpio, tipado, en SQLite + GeoJSON normalizado
GOLD = LAGO / "gold"          # temas listos para el sitio (JSON) + capas geo
CATALOGO = LAGO / "catalogo"  # catálogo, linaje y diccionario generado
SQLITE = SILVER / "budapest.sqlite"
WEB_LAGO = RAIZ / "web" / "lago"   # copia de gold que despliega el sitio (privada, detrás de /api/datos)
DOCS = RAIZ / "docs"

USER_AGENT = "CerebroBudapest/1.0 (datalake academico; python-urllib)"

# Territorio de estudio
CIUDAD = "Budapest"
CENTRO = (47.4979, 19.0402)                 # lat, lon (Deák Ferenc tér aprox.)
BBOX = (18.925, 47.349, 19.335, 47.614)     # lon_min, lat_min, lon_max, lat_max
NUTS2 = "HU11"                               # Budapest (NUTS 2021)
NUTS3 = "HU110"
CIUDAD_UA = "HU001C"                         # código Urban Audit de Eurostat
ZONA_HORARIA = "Europe/Budapest"

# Registro de fuentes: el id es la clave que usan bronze, silver, gold y el diccionario.
FUENTES = {
    "osm_overpass": {
        "nombre": "OpenStreetMap vía Overpass API",
        "organismo": "OpenStreetMap contributors",
        "url": "https://overpass-turbo.eu/",
        "endpoint": "https://overpass-api.de/api/interpreter",
        "licencia": "ODbL 1.0",
        "acceso": "API pública (consulta Overpass QL)",
        "frecuencia": "semanal",
    },
    "geofabrik": {
        "nombre": "Geofabrik · extracto OSM de Hungría",
        "organismo": "Geofabrik GmbH",
        "url": "https://download.geofabrik.de/europe/hungary.html",
        "endpoint": "https://download.geofabrik.de/europe/",
        "licencia": "ODbL 1.0",
        "acceso": "Descarga directa (.poly, state.txt; .osm.pbf opcional con --pbf)",
        "frecuencia": "diaria (réplica)",
    },
    "copernicus": {
        "nombre": "Copernicus Land Monitoring Service · HRL 2018",
        "organismo": "EEA / Copernicus",
        "url": "https://land.copernicus.eu/",
        "endpoint": "https://image.discomap.eea.europa.eu/arcgis/rest/services/GioLandPublic/",
        "licencia": "Copernicus data policy (acceso libre y completo)",
        "acceso": "ArcGIS ImageServer · computeStatisticsHistograms por polígono",
        "frecuencia": "trienal (producto 2018)",
    },
    "bkk_gtfs": {
        "nombre": "BKK · GTFS estático de Budapest",
        "organismo": "Budapesti Közlekedési Központ (BKK)",
        "url": "https://opendata.bkk.hu/",
        "endpoint": "https://go.bkk.hu/api/static/v1/public-gtfs/budapest_gtfs.zip",
        "licencia": "Licencia de datos abiertos BKK",
        "acceso": "Descarga directa ZIP (GTFS-RT requiere clave: no usado)",
        "frecuencia": "diaria",
    },
    "mobilitydb": {
        "nombre": "Mobility Database · catálogo de feeds",
        "organismo": "MobilityData",
        "url": "https://mobilitydatabase.org/feeds/gtfs/tfs-42",
        "endpoint": "https://files.mobilitydatabase.org/feeds_v2.csv",
        "licencia": "CC0 (catálogo)",
        "acceso": "CSV público del catálogo; espejo del GTFS en files.mobilitydatabase.org",
        "frecuencia": "diaria",
    },
    "bubi": {
        "nombre": "MOL Bubi · estaciones de bicicleta pública (nextbike)",
        "organismo": "BKK / nextbike",
        "url": "https://bubi.freewb.hu/",
        "endpoint": "https://maps2.nextbike.net/maps/nextbike-live.json?domains=bh",
        "licencia": "Datos públicos del operador (uso informativo)",
        "acceso": "JSON en vivo del operador (dominio bh)",
        "frecuencia": "en vivo (instantánea por ejecución)",
    },
    "ksh": {
        "nombre": "KSH · Oficina Central de Estadística de Hungría",
        "organismo": "Központi Statisztikai Hivatal",
        "url": "https://www.ksh.hu/?lang=en",
        "endpoint": "https://data.ksh.hu/ (HVD API) · https://www.ksh.hu/docs/helysegnevtar/",
        "licencia": "Reutilización libre citando la fuente (KSH)",
        "acceso": "API HVD (SDMX-CSV) + Helységnévtár (XLSX)",
        "frecuencia": "anual",
    },
    "eurostat": {
        "nombre": "Eurostat · base de datos",
        "organismo": "Comisión Europea",
        "url": "https://ec.europa.eu/eurostat/web/main/data/database",
        "endpoint": "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/",
        "licencia": "CC BY 4.0",
        "acceso": "API JSON-stat 2.0",
        "frecuencia": "anual / trimestral",
    },
    "sensor_community": {
        "nombre": "Sensor.Community · red ciudadana de calidad del aire",
        "organismo": "Sensor.Community (OK Lab Stuttgart)",
        "url": "https://sensor.community/en/",
        "endpoint": "https://data.sensor.community/airrohr/v1/filter/",
        "licencia": "ODbL 1.0",
        "acceso": "API pública (promedio 5 min)",
        "frecuencia": "en vivo (instantánea por ejecución)",
    },
    "opensensemap": {
        "nombre": "openSenseMap · senseBoxes",
        "organismo": "Reedu GmbH / Universität Münster",
        "url": "https://opensensemap.org/",
        "endpoint": "https://api.opensensemap.org/boxes",
        "licencia": "PDDL 1.0",
        "acceso": "API pública REST",
        "frecuencia": "en vivo (instantánea por ejecución)",
    },
    "eea": {
        "nombre": "EEA · Air Quality e-Reporting (AQ statistics)",
        "organismo": "Agencia Europea de Medio Ambiente",
        "url": "https://www.eea.europa.eu/data-and-maps/data/aqereporting-9",
        "endpoint": "https://discodata.eea.europa.eu/sql",
        "licencia": "CC BY 4.0",
        "acceso": "DiscoData SQL (AirQualityDataFlows.latest.AirQualityStatistics)",
        "frecuencia": "anual (E1a validado) + año en curso (E2a)",
    },
    "open_meteo": {
        "nombre": "Open-Meteo · clima, histórico y calidad del aire CAMS",
        "organismo": "Open-Meteo.com",
        "url": "https://open-meteo.com/",
        "endpoint": "https://api.open-meteo.com/v1/ · archive-api · air-quality-api",
        "licencia": "CC BY 4.0",
        "acceso": "API pública JSON",
        "frecuencia": "horaria / diaria",
    },
}

# Guías OMS 2021 (media anual, µg/m³) para lectura de calidad del aire
OMS_ANUAL = {"PM2.5": 5, "PM10": 15, "NO2": 10}
LIMITE_UE_ANUAL = {"PM2.5": 25, "PM10": 40, "NO2": 40}
