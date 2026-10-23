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
        "codigo": "F02",
        "nombre": "OpenStreetMap vía Overpass API",
        "organismo": "OpenStreetMap contributors",
        "url": "https://overpass-turbo.eu/",
        "endpoint": "https://overpass-api.de/api/interpreter",
        "licencia": "Open Data Commons Open Database License (ODbL)",
        "acceso": "API pública (consulta Overpass QL)",
        "frecuencia": "semanal",
    },
    "geofabrik": {
        "codigo": "F03",
        "nombre": "Geofabrik · extracto OSM de Hungría",
        "organismo": "Geofabrik GmbH",
        "url": "https://download.geofabrik.de/europe/hungary.html",
        "endpoint": "https://download.geofabrik.de/europe/",
        "licencia": "Open Data Commons Open Database License (ODbL) (datos de OpenStreetMap)",
        "acceso": "Descarga directa (.poly, state.txt; .osm.pbf opcional con --pbf)",
        "frecuencia": "diaria (réplica)",
    },
    "copernicus": {
        "codigo": "F04",
        "nombre": "Copernicus Land Monitoring Service · HRL 2018",
        "organismo": "EEA / Copernicus",
        "url": "https://land.copernicus.eu/",
        "endpoint": "https://image.discomap.eea.europa.eu/arcgis/rest/services/GioLandPublic/",
        "licencia": "Full, open and free access (Reglamento Delegado (UE) 1159/2013)",
        "acceso": "ArcGIS ImageServer · computeStatisticsHistograms por polígono",
        "frecuencia": "trienal (producto 2018)",
    },
    "bkk_gtfs": {
        "codigo": "F05",
        "nombre": "BKK · GTFS estático de Budapest",
        "organismo": "Budapesti Közlekedési Központ (BKK)",
        "url": "https://opendata.bkk.hu/",
        "endpoint": "https://go.bkk.hu/api/static/v1/public-gtfs/budapest_gtfs.zip",
        "licencia": "CC BY 4.0 («Data source: BKK Zrt., CC BY 4.0»)",
        "acceso": "Descarga directa ZIP (GTFS-RT requiere clave: no usado)",
        "frecuencia": "diaria",
    },
    "mobilitydb": {
        "codigo": "F06",
        "nombre": "Mobility Database · catálogo de feeds",
        "organismo": "MobilityData",
        "url": "https://mobilitydatabase.org/feeds/gtfs/tfs-42",
        "endpoint": "https://files.mobilitydatabase.org/feeds_v2.csv",
        "licencia": "Apache License 2.0 (catálogo mobility-database-catalogs)",
        "acceso": "CSV público del catálogo; espejo del GTFS en files.mobilitydatabase.org",
        "frecuencia": "diaria",
    },
    "bubi": {
        "codigo": "F07",
        "nombre": "MOL Bubi · feed del operador nextbike (candidata: no publica estaciones)",
        "organismo": "BKK / nextbike",
        "url": "https://bubi.freewb.hu/",
        "endpoint": "https://maps2.nextbike.net/maps/nextbike-live.json?domains=bh",
        "licencia": "no declara",
        "acceso": "JSON en vivo del operador (dominio bh)",
        "frecuencia": "en vivo (instantánea por ejecución)",
    },
    "ksh": {
        "codigo": "F08",
        "nombre": "KSH · Helységnévtár (población, superficie y viviendas por distrito)",
        "organismo": "Központi Statisztikai Hivatal",
        "url": "https://www.ksh.hu/?lang=en",
        "endpoint": "https://www.ksh.hu/docs/helysegnevtar/hnt_letoltes_AAAA.xlsx",
        "licencia": "no declara",
        "acceso": "Descarga directa (XLSX, una edición por año)",
        "frecuencia": "anual",
    },
    # Misma ingesta que «ksh» (módulo pipelines/fuentes/ksh.py), pero es otra fuente en el catálogo (F09)
    "ksh_hvd": {
        "codigo": "F09",
        "modulo": "ksh",
        "nombre": "KSH · conjuntos de datos de alto valor (HVD)",
        "organismo": "Központi Statisztikai Hivatal",
        "url": "https://data.ksh.hu/openapi/",
        "endpoint": "https://data.ksh.hu/datasets/{id}/data/{recurso}.csv",
        "licencia": "CC BY 4.0 (declarada en el RDF de los datasets HVD)",
        "acceso": "API sin llave (SDMX-CSV)",
        "frecuencia": "anual",
    },
    "eurostat": {
        "codigo": "F10",
        "nombre": "Eurostat · base de datos",
        "organismo": "Comisión Europea",
        "url": "https://ec.europa.eu/eurostat/web/main/data/database",
        "endpoint": "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/",
        "licencia": "Creative Commons Attribution 4.0 International licence",
        "acceso": "API JSON-stat 2.0",
        "frecuencia": "anual / trimestral",
    },
    "sensor_community": {
        "codigo": "F11",
        "nombre": "Sensor.Community · red ciudadana de sensores de bajo costo",
        "organismo": "Sensor.Community (OK Lab Stuttgart)",
        "url": "https://sensor.community/en/",
        "endpoint": "https://data.sensor.community/airrohr/v1/filter/",
        "licencia": "Open Data Commons DbCL 1.0 (DB Contents License)",
        "acceso": "API pública (promedio 5 min)",
        "frecuencia": "en vivo (instantánea por ejecución)",
    },
    "opensensemap": {
        "codigo": "F12",
        "nombre": "openSenseMap · senseBoxes ciudadanas de bajo costo",
        "organismo": "Reedu GmbH / Universität Münster",
        "url": "https://opensensemap.org/",
        "endpoint": "https://api.opensensemap.org/boxes",
        "licencia": "Public Domain Dedication and License 1.0 (PDDL)",
        "acceso": "API pública REST",
        "frecuencia": "en vivo (instantánea por ejecución)",
    },
    "eea": {
        "codigo": "F13",
        "nombre": "EEA · Air Quality e-Reporting (AQ statistics)",
        "organismo": "Agencia Europea de Medio Ambiente",
        "url": "https://www.eea.europa.eu/data-and-maps/data/aqereporting-9",
        "endpoint": "https://discodata.eea.europa.eu/sql",
        "licencia": "Reutilización libre y gratuita, citando siempre a la EEA como fuente (aviso legal de la EEA)",
        "acceso": "DiscoData SQL (AirQualityDataFlows.latest.AirQualityStatistics)",
        "frecuencia": "anual (E1a validado) + año en curso (E2a)",
    },
    "open_meteo": {
        "codigo": "F14",
        "nombre": "Open-Meteo · modelos: reanálisis ERA5, pronóstico y calidad del aire CAMS",
        "organismo": "Open-Meteo.com",
        "url": "https://open-meteo.com/",
        "endpoint": "https://api.open-meteo.com/v1/ · archive-api · air-quality-api",
        "licencia": "Attribution 4.0 International (CC BY 4.0)",
        "acceso": "API pública JSON",
        "frecuencia": "horaria / diaria",
    },
}

# Guías OMS 2021 (media anual, µg/m³) para lectura de calidad del aire
OMS_ANUAL = {"PM2.5": 5, "PM10": 15, "NO2": 10}
LIMITE_UE_ANUAL = {"PM2.5": 25, "PM10": 40, "NO2": 40}
