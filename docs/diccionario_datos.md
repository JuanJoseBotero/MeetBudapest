# Diccionario de datos · Cerebro Budapest

Generado automáticamente el 2026-10-26 por `pipelines/diccionario.py` a partir del catálogo real del lago (no se edita a mano: se regenera en cada ejecución del pipeline).

## 1. Convenciones

- **Territorio**: Budapest (NUTS2 `HU11`, NUTS3 `HU110`, ciudad Urban Audit `HU001C`), 23 distritos (*kerületek*) identificados por `distrito_id` 1–23.
- **Coordenadas**: WGS84 (EPSG:4326), grados decimales. Superficies en km² salvo que se indique ha.
- **Fechas**: ISO 8601. `vigencia` = periodo al que se refiere el dato; `probado` = fecha en que el lago lo verificó.
- **Zonas del lago**: `bronze` (crudo, inmutable, particionado `bronze/<fuente>/<AAAA-MM-DD>/`), `silver` (SQLite tipado), `gold` (temas JSON y GeoJSON para el sitio), `catalogo` (linaje, estado, diccionario).

### Estados de una cifra

| estado | significado |
|---|---|
| observado | Valor publicado o medido por la fuente, sin transformación más allá de filtrado y tipado. |
| derivado | Cálculo propio sobre datos observados (tasas, densidades, promedios, índices). La fórmula se documenta. |
| modelo | Salida de un modelo, no una medición: reanálisis ERA5, pronóstico de Open-Meteo y calidad del aire CAMS. |
| bajo_costo | Medición de sensores ciudadanos de bajo costo (Sensor.Community, openSenseMap), sin calibración oficial; instantánea en vivo. |
| en_vivo | Instantánea del momento de ingesta de una fuente en tiempo real; cambia en cada ejecución. |
| proxy | Indicador indirecto de un fenómeno que no se mide directamente. |

## 2. Fuentes

| id | fuente | organismo | acceso | licencia | frecuencia | URL |
|---|---|---|---|---|---|---|
| osm_overpass | OpenStreetMap vía Overpass API | OpenStreetMap contributors | API pública (consulta Overpass QL) | Open Data Commons Open Database License (ODbL) | semanal | https://overpass-turbo.eu/ |
| geofabrik | Geofabrik · extracto OSM de Hungría | Geofabrik GmbH | Descarga directa (.poly, state.txt; .osm.pbf opcional con --pbf) | Open Data Commons Open Database License (ODbL) (datos de OpenStreetMap) | diaria (réplica) | https://download.geofabrik.de/europe/hungary.html |
| copernicus | Copernicus Land Monitoring Service · HRL 2018 | EEA / Copernicus | ArcGIS ImageServer · computeStatisticsHistograms por polígono | Full, open and free access (Reglamento Delegado (UE) 1159/2013) | trienal (producto 2018) | https://land.copernicus.eu/ |
| bkk_gtfs | BKK · GTFS estático de Budapest | Budapesti Közlekedési Központ (BKK) | Descarga directa ZIP (GTFS-RT requiere clave: no usado) | CC BY 4.0 («Data source: BKK Zrt., CC BY 4.0») | diaria | https://opendata.bkk.hu/ |
| mobilitydb | Mobility Database · catálogo de feeds | MobilityData | CSV público del catálogo; espejo del GTFS en files.mobilitydatabase.org | Apache License 2.0 (catálogo mobility-database-catalogs) | diaria | https://mobilitydatabase.org/feeds/gtfs/tfs-42 |
| bubi | MOL Bubi · feed del operador nextbike (candidata: no publica estaciones) | BKK / nextbike | JSON en vivo del operador (dominio bh) | no declara | en vivo (instantánea por ejecución) | https://bubi.freewb.hu/ |
| ksh | KSH · Helységnévtár (población, superficie y viviendas por distrito) | Központi Statisztikai Hivatal | Descarga directa (XLSX, una edición por año) | no declara | anual | https://www.ksh.hu/?lang=en |
| ksh_hvd | KSH · conjuntos de datos de alto valor (HVD) | Központi Statisztikai Hivatal | API sin llave (SDMX-CSV) | CC BY 4.0 (declarada en el RDF de los datasets HVD) | anual | https://data.ksh.hu/openapi/ |
| eurostat | Eurostat · base de datos | Comisión Europea | API JSON-stat 2.0 | Creative Commons Attribution 4.0 International licence | anual / trimestral | https://ec.europa.eu/eurostat/web/main/data/database |
| sensor_community | Sensor.Community · red ciudadana de sensores de bajo costo | Sensor.Community (OK Lab Stuttgart) | API pública (promedio 5 min) | Open Data Commons DbCL 1.0 (DB Contents License) | en vivo (instantánea por ejecución) | https://sensor.community/en/ |
| opensensemap | openSenseMap · senseBoxes ciudadanas de bajo costo | Reedu GmbH / Universität Münster | API pública REST | Public Domain Dedication and License 1.0 (PDDL) | en vivo (instantánea por ejecución) | https://opensensemap.org/ |
| eea | EEA · Air Quality e-Reporting (AQ statistics) | Agencia Europea de Medio Ambiente | DiscoData SQL (AirQualityDataFlows.latest.AirQualityStatistics) | Reutilización libre y gratuita, citando siempre a la EEA como fuente (aviso legal de la EEA) | anual (E1a validado) + año en curso (E2a) | https://www.eea.europa.eu/data-and-maps/data/aqereporting-9 |
| open_meteo | Open-Meteo · modelos: reanálisis ERA5, pronóstico y calidad del aire CAMS | Open-Meteo.com | API pública JSON | Attribution 4.0 International (CC BY 4.0) | horaria / diaria | https://open-meteo.com/ |

## 3. Bronze · archivos crudos

Cada descarga se escribe tal cual llega y se registra en `datalake/catalogo/linaje.jsonl` con URL, bytes y sha256.

### `osm_overpass`

| archivo | bytes | ingesta | origen |
|---|---|---|---|
| distritos.json | 705.499 | 2026-10-27T00:01 | https://overpass-api.de/api/interpreter :: [out:json][timeout:240];area["name"="Budapest"]["boundary"="administrative"]->.bp;rel(area.bp)["b |
| edificios_conteo.json | 7.207 | 2026-10-27T00:07 | https://overpass-api.de/api/interpreter :: [out:json][timeout:900];area(id:3600215618)->.a;way["building"](area.a)->.w;rel["building"](area. |
| poi.json | 7.169.489 | 2026-10-27T00:03 | https://overpass-api.de/api/interpreter :: [out:json][timeout:600];area["name"="Budapest"]["boundary"="administrative"]->.bp;(nwr["amenity"~ |

### `geofabrik`

| archivo | bytes | ingesta | origen |
|---|---|---|---|
| hungary.poly | 11.547 | 2026-10-27T00:07 | https://download.geofabrik.de/europe/hungary.poly |
| pbf_head.txt | 70 | 2026-10-27T00:07 | https://download.geofabrik.de/europe/hungary-latest.osm.pbf |
| state.txt | 113 | 2026-10-27T00:07 | https://download.geofabrik.de/europe/hungary-updates/state.txt |

### `copernicus`

| archivo | bytes | ingesta | origen |
|---|---|---|---|
| imperviousness_2018/distrito_01.json | 675 | 2026-10-22T22:45 | https://image.discomap.eea.europa.eu/arcgis/rest/services/GioLandPublic/HRL_ImperviousnessDensity_2018/ImageServer/computeStatisticsHistogra |
| imperviousness_2018/distrito_02.json | 742 | 2026-10-22T22:45 | https://image.discomap.eea.europa.eu/arcgis/rest/services/GioLandPublic/HRL_ImperviousnessDensity_2018/ImageServer/computeStatisticsHistogra |
| imperviousness_2018/distrito_03.json | 775 | 2026-10-22T22:45 | https://image.discomap.eea.europa.eu/arcgis/rest/services/GioLandPublic/HRL_ImperviousnessDensity_2018/ImageServer/computeStatisticsHistogra |
| imperviousness_2018/distrito_04.json | 777 | 2026-10-22T22:45 | https://image.discomap.eea.europa.eu/arcgis/rest/services/GioLandPublic/HRL_ImperviousnessDensity_2018/ImageServer/computeStatisticsHistogra |
| imperviousness_2018/distrito_05.json | 636 | 2026-10-22T22:45 | https://image.discomap.eea.europa.eu/arcgis/rest/services/GioLandPublic/HRL_ImperviousnessDensity_2018/ImageServer/computeStatisticsHistogra |
| imperviousness_2018/distrito_06.json | 679 | 2026-10-22T22:45 | https://image.discomap.eea.europa.eu/arcgis/rest/services/GioLandPublic/HRL_ImperviousnessDensity_2018/ImageServer/computeStatisticsHistogra |
| imperviousness_2018/distrito_07.json | 656 | 2026-10-22T22:45 | https://image.discomap.eea.europa.eu/arcgis/rest/services/GioLandPublic/HRL_ImperviousnessDensity_2018/ImageServer/computeStatisticsHistogra |
| imperviousness_2018/distrito_08.json | 710 | 2026-10-22T22:45 | https://image.discomap.eea.europa.eu/arcgis/rest/services/GioLandPublic/HRL_ImperviousnessDensity_2018/ImageServer/computeStatisticsHistogra |
| imperviousness_2018/distrito_09.json | 775 | 2026-10-22T22:45 | https://image.discomap.eea.europa.eu/arcgis/rest/services/GioLandPublic/HRL_ImperviousnessDensity_2018/ImageServer/computeStatisticsHistogra |
| imperviousness_2018/distrito_10.json | 777 | 2026-10-22T22:45 | https://image.discomap.eea.europa.eu/arcgis/rest/services/GioLandPublic/HRL_ImperviousnessDensity_2018/ImageServer/computeStatisticsHistogra |
| imperviousness_2018/distrito_11.json | 777 | 2026-10-22T22:45 | https://image.discomap.eea.europa.eu/arcgis/rest/services/GioLandPublic/HRL_ImperviousnessDensity_2018/ImageServer/computeStatisticsHistogra |
| imperviousness_2018/distrito_12.json | 735 | 2026-10-22T22:45 | https://image.discomap.eea.europa.eu/arcgis/rest/services/GioLandPublic/HRL_ImperviousnessDensity_2018/ImageServer/computeStatisticsHistogra |
| imperviousness_2018/distrito_13.json | 769 | 2026-10-22T22:45 | https://image.discomap.eea.europa.eu/arcgis/rest/services/GioLandPublic/HRL_ImperviousnessDensity_2018/ImageServer/computeStatisticsHistogra |
| imperviousness_2018/distrito_14.json | 774 | 2026-10-22T22:45 | https://image.discomap.eea.europa.eu/arcgis/rest/services/GioLandPublic/HRL_ImperviousnessDensity_2018/ImageServer/computeStatisticsHistogra |
| imperviousness_2018/distrito_15.json | 776 | 2026-10-22T22:45 | https://image.discomap.eea.europa.eu/arcgis/rest/services/GioLandPublic/HRL_ImperviousnessDensity_2018/ImageServer/computeStatisticsHistogra |
| imperviousness_2018/distrito_16.json | 764 | 2026-10-22T22:45 | https://image.discomap.eea.europa.eu/arcgis/rest/services/GioLandPublic/HRL_ImperviousnessDensity_2018/ImageServer/computeStatisticsHistogra |
| imperviousness_2018/distrito_17.json | 763 | 2026-10-22T22:45 | https://image.discomap.eea.europa.eu/arcgis/rest/services/GioLandPublic/HRL_ImperviousnessDensity_2018/ImageServer/computeStatisticsHistogra |
| imperviousness_2018/distrito_18.json | 775 | 2026-10-22T22:45 | https://image.discomap.eea.europa.eu/arcgis/rest/services/GioLandPublic/HRL_ImperviousnessDensity_2018/ImageServer/computeStatisticsHistogra |
| imperviousness_2018/distrito_19.json | 753 | 2026-10-22T22:46 | https://image.discomap.eea.europa.eu/arcgis/rest/services/GioLandPublic/HRL_ImperviousnessDensity_2018/ImageServer/computeStatisticsHistogra |
| imperviousness_2018/distrito_20.json | 751 | 2026-10-22T22:46 | https://image.discomap.eea.europa.eu/arcgis/rest/services/GioLandPublic/HRL_ImperviousnessDensity_2018/ImageServer/computeStatisticsHistogra |
| imperviousness_2018/distrito_21.json | 776 | 2026-10-22T22:46 | https://image.discomap.eea.europa.eu/arcgis/rest/services/GioLandPublic/HRL_ImperviousnessDensity_2018/ImageServer/computeStatisticsHistogra |
| imperviousness_2018/distrito_22.json | 774 | 2026-10-22T22:46 | https://image.discomap.eea.europa.eu/arcgis/rest/services/GioLandPublic/HRL_ImperviousnessDensity_2018/ImageServer/computeStatisticsHistogra |
| imperviousness_2018/distrito_23.json | 773 | 2026-10-22T22:46 | https://image.discomap.eea.europa.eu/arcgis/rest/services/GioLandPublic/HRL_ImperviousnessDensity_2018/ImageServer/computeStatisticsHistogra |
| tree_cover_2018/distrito_01.json | 545 | 2026-10-22T22:46 | https://image.discomap.eea.europa.eu/arcgis/rest/services/GioLandPublic/HRL_TreeCoverDensity_2018/ImageServer/computeStatisticsHistograms |
| tree_cover_2018/distrito_02.json | 706 | 2026-10-22T22:46 | https://image.discomap.eea.europa.eu/arcgis/rest/services/GioLandPublic/HRL_TreeCoverDensity_2018/ImageServer/computeStatisticsHistograms |
| tree_cover_2018/distrito_03.json | 704 | 2026-10-22T22:46 | https://image.discomap.eea.europa.eu/arcgis/rest/services/GioLandPublic/HRL_TreeCoverDensity_2018/ImageServer/computeStatisticsHistograms |
| tree_cover_2018/distrito_04.json | 687 | 2026-10-22T22:46 | https://image.discomap.eea.europa.eu/arcgis/rest/services/GioLandPublic/HRL_TreeCoverDensity_2018/ImageServer/computeStatisticsHistograms |
| tree_cover_2018/distrito_05.json | 450 | 2026-10-22T22:46 | https://image.discomap.eea.europa.eu/arcgis/rest/services/GioLandPublic/HRL_TreeCoverDensity_2018/ImageServer/computeStatisticsHistograms |
| tree_cover_2018/distrito_06.json | 470 | 2026-10-22T22:46 | https://image.discomap.eea.europa.eu/arcgis/rest/services/GioLandPublic/HRL_TreeCoverDensity_2018/ImageServer/computeStatisticsHistograms |
| tree_cover_2018/distrito_07.json | 461 | 2026-10-22T22:46 | https://image.discomap.eea.europa.eu/arcgis/rest/services/GioLandPublic/HRL_TreeCoverDensity_2018/ImageServer/computeStatisticsHistograms |
| tree_cover_2018/distrito_08.json | 591 | 2026-10-22T22:46 | https://image.discomap.eea.europa.eu/arcgis/rest/services/GioLandPublic/HRL_TreeCoverDensity_2018/ImageServer/computeStatisticsHistograms |
| tree_cover_2018/distrito_09.json | 605 | 2026-10-22T22:46 | https://image.discomap.eea.europa.eu/arcgis/rest/services/GioLandPublic/HRL_TreeCoverDensity_2018/ImageServer/computeStatisticsHistograms |
| tree_cover_2018/distrito_10.json | 700 | 2026-10-22T22:46 | https://image.discomap.eea.europa.eu/arcgis/rest/services/GioLandPublic/HRL_TreeCoverDensity_2018/ImageServer/computeStatisticsHistograms |
| tree_cover_2018/distrito_11.json | 686 | 2026-10-22T22:46 | https://image.discomap.eea.europa.eu/arcgis/rest/services/GioLandPublic/HRL_TreeCoverDensity_2018/ImageServer/computeStatisticsHistograms |
| tree_cover_2018/distrito_12.json | 702 | 2026-10-22T22:46 | https://image.discomap.eea.europa.eu/arcgis/rest/services/GioLandPublic/HRL_TreeCoverDensity_2018/ImageServer/computeStatisticsHistograms |
| tree_cover_2018/distrito_13.json | 601 | 2026-10-22T22:46 | https://image.discomap.eea.europa.eu/arcgis/rest/services/GioLandPublic/HRL_TreeCoverDensity_2018/ImageServer/computeStatisticsHistograms |
| tree_cover_2018/distrito_14.json | 632 | 2026-10-22T22:46 | https://image.discomap.eea.europa.eu/arcgis/rest/services/GioLandPublic/HRL_TreeCoverDensity_2018/ImageServer/computeStatisticsHistograms |
| tree_cover_2018/distrito_15.json | 687 | 2026-10-22T22:46 | https://image.discomap.eea.europa.eu/arcgis/rest/services/GioLandPublic/HRL_TreeCoverDensity_2018/ImageServer/computeStatisticsHistograms |
| tree_cover_2018/distrito_16.json | 699 | 2026-10-22T22:46 | https://image.discomap.eea.europa.eu/arcgis/rest/services/GioLandPublic/HRL_TreeCoverDensity_2018/ImageServer/computeStatisticsHistograms |
| tree_cover_2018/distrito_17.json | 716 | 2026-10-22T22:46 | https://image.discomap.eea.europa.eu/arcgis/rest/services/GioLandPublic/HRL_TreeCoverDensity_2018/ImageServer/computeStatisticsHistograms |

… y 6 archivos más del mismo patrón.

### `bkk_gtfs`

| archivo | bytes | ingesta | origen |
|---|---|---|---|
| budapest_gtfs.zip | 61.967.732 | 2026-10-27T00:09 | https://go.bkk.hu/api/static/v1/public-gtfs/budapest_gtfs.zip |
| origen.txt | 3 | 2026-10-27T00:09 | https://go.bkk.hu/api/static/v1/public-gtfs/budapest_gtfs.zip |

### `mobilitydb`

| archivo | bytes | ingesta | origen |
|---|---|---|---|
| feeds_v2.csv | 2.729.383 | 2026-10-27T00:08 | https://files.mobilitydatabase.org/feeds_v2.csv |

### `bubi`

| archivo | bytes | ingesta | origen |
|---|---|---|---|
| nextbike_bh_0009.json | 1.016 | 2026-10-27T00:09 | https://maps2.nextbike.net/maps/nextbike-live.json?domains=bh |
| nextbike_bh_0313.json | 1.016 | 2026-09-30T03:13 | https://maps2.nextbike.net/maps/nextbike-live.json?domains=bh |
| nextbike_bh_2128.json | 1.016 | 2026-10-20T21:28 | https://maps2.nextbike.net/maps/nextbike-live.json?domains=bh |
| nextbike_bh_2227.json | 1.016 | 2026-09-29T22:27 | https://maps2.nextbike.net/maps/nextbike-live.json?domains=bh |
| nextbike_bh_2235.json | 1.016 | 2026-09-29T22:35 | https://maps2.nextbike.net/maps/nextbike-live.json?domains=bh |
| nextbike_bh_2247.json | 1.016 | 2026-10-22T22:47 | https://maps2.nextbike.net/maps/nextbike-live.json?domains=bh |

### `ksh`

| archivo | bytes | ingesta | origen |
|---|---|---|---|
| helysegnevtar_2020.xlsx | 1.371.696 | 2026-10-27T00:00 | https://www.ksh.hu/docs/helysegnevtar/hnt_letoltes_2020.xlsx |
| helysegnevtar_2021.xlsx | 1.372.947 | 2026-10-27T00:00 | https://www.ksh.hu/docs/helysegnevtar/hnt_letoltes_2021.xlsx |
| helysegnevtar_2022.xlsx | 1.372.185 | 2026-10-27T00:00 | https://www.ksh.hu/docs/helysegnevtar/hnt_letoltes_2022.xlsx |
| helysegnevtar_2023.xlsx | 1.368.113 | 2026-10-27T00:00 | https://www.ksh.hu/docs/helysegnevtar/hnt_letoltes_2023.xlsx |
| helysegnevtar_2024.xlsx | 1.369.720 | 2026-10-27T00:00 | https://www.ksh.hu/docs/helysegnevtar/hnt_letoltes_2024.xlsx |
| helysegnevtar_2025.xlsx | 1.370.790 | 2026-10-27T00:00 | https://www.ksh.hu/docs/helysegnevtar/hnt_letoltes_2025.xlsx |
| helysegnevtar_2026.xlsx | 1.377.826 | 2026-10-27T00:00 | https://www.ksh.hu/docs/helysegnevtar/hnt_letoltes_2026.xlsx |
| hvd_edad_mediana.csv | 109.507 | 2026-10-27T00:00 | https://data.ksh.hu/datasets/f44d314b-bc27-40a7-b34e-af01b3c4ab05/data/093d149c-9951-4dd0-99ae-4a5e858a7b45.csv |
| hvd_esperanza_vida.csv | 1.266.015 | 2026-10-27T00:00 | https://data.ksh.hu/datasets/fc86b7eb-f813-424f-baea-a32d65e1fdec/data/169201f0-24a4-434a-8900-3c035cd4430f.csv |
| hvd_mortalidad.csv | 25.294 | 2026-10-27T00:00 | https://data.ksh.hu/datasets/fc86b7eb-f813-424f-baea-a32d65e1fdec/data/d442dc4c-20fb-4ca8-bfde-9171e04a683d.csv |
| hvd_mortalidad_infantil.csv | 3.507 | 2026-10-27T00:00 | https://data.ksh.hu/datasets/fc86b7eb-f813-424f-baea-a32d65e1fdec/data/99ac9e47-dc1b-44d8-8e69-cd88018c0244.csv |
| hvd_natalidad.csv | 25.294 | 2026-10-27T00:00 | https://data.ksh.hu/datasets/4e8d4137-0962-4dfe-9d06-ca9d38ec6301/data/d96c6d1d-ee4b-483d-bfab-4b0baaae5e55.csv |
| hvd_poblacion_edad_sexo.csv | 1.053.980 | 2026-10-27T00:00 | https://data.ksh.hu/datasets/f44d314b-bc27-40a7-b34e-af01b3c4ab05/data/eb3e481e-6b5a-45d1-8076-18c4ece155c2.csv |

### `eurostat`

| archivo | bytes | ingesta | origen |
|---|---|---|---|
| densidad.json | 3.636 | 2026-10-27T00:09 | https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/demo_r_d3dens?format=JSON&lang=en&geo=HU110 |
| desempleo.json | 4.265 | 2026-10-27T00:09 | https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/lfst_r_lfu3rt?format=JSON&lang=en&geo=HU11&sex=T&age=Y20-64&isced11=TOTA |
| educacion_terciaria.json | 3.692 | 2026-10-27T00:09 | https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/edat_lfse_04?format=JSON&lang=en&geo=HU11&sex=T&age=Y25-64&isced11=ED5-8 |
| empleo.json | 4.069 | 2026-10-27T00:09 | https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/lfst_r_lfe2emprt?format=JSON&lang=en&geo=HU11&sex=T&age=Y20-64 |
| empresas.json | 3.542 | 2026-10-27T00:09 | https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/bd_hgnace2_r3?format=JSON&lang=en&geo=HU110&nace_r2=B-S_X_K642&indic_sb= |
| esperanza_vida_ue.json | 3.766 | 2026-10-27T00:09 | https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/demo_r_mlifexp?format=JSON&lang=en&geo=HU11&sex=T&age=Y_LT1 |
| gasto_id_pib.json | 4.550 | 2026-10-27T00:09 | https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/rd_e_gerdreg?format=JSON&lang=en&geo=HU11&sectperf=TOTAL&unit=PC_GDP |
| ingreso_disponible.json | 4.815 | 2026-10-27T00:09 | https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/tgs00026?format=JSON&lang=en&geo=HU11 |
| llegadas.json | 4.265 | 2026-10-27T00:09 | https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/tour_occ_arn2?format=JSON&lang=en&geo=HU11&unit=NR&nace_r2=I551-I553&c_r |
| pernoctaciones.json | 4.284 | 2026-10-27T00:09 | https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/tour_occ_nin2?format=JSON&lang=en&geo=HU11&unit=NR&nace_r2=I551-I553&c_r |
| pib_hab_eur.json | 3.398 | 2026-10-27T00:09 | https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/nama_10r_3gdp?format=JSON&lang=en&geo=HU110&unit=EUR_HAB |
| pib_hab_pps_ue.json | 3.061 | 2026-10-27T00:09 | https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/nama_10r_2gdp?format=JSON&lang=en&geo=HU11&unit=PPS_EU27_2020_HAB_EU27_2 |
| pib_meur.json | 3.425 | 2026-10-27T00:09 | https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/nama_10r_3gdp?format=JSON&lang=en&geo=HU110&unit=MIO_EUR |
| precio_vivienda_hu.json | 6.794 | 2026-10-27T00:09 | https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/prc_hpi_q?format=JSON&lang=en&geo=HU&purchase=TOTAL&unit=I15_Q |
| riesgo_pobreza_exclusion.json | 3.387 | 2026-10-27T00:09 | https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/ilc_peps11n?format=JSON&lang=en&geo=HU11&unit=PC |
| ua_ambiente.json | 7.513 | 2026-10-27T00:09 | https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/urb_cenv?format=JSON&lang=en&cities=HU001C |
| ua_poblacion.json | 19.908 | 2026-10-27T00:09 | https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/urb_cpop1?format=JSON&lang=en&cities=HU001C |
| ua_trabajo.json | 8.438 | 2026-10-27T00:09 | https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/urb_clma?format=JSON&lang=en&cities=HU001C |
| ua_transporte.json | 6.536 | 2026-10-27T00:10 | https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/urb_ctran?format=JSON&lang=en&cities=HU001C |
| ua_turismo.json | 6.422 | 2026-10-27T00:09 | https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/urb_ctour?format=JSON&lang=en&cities=HU001C |
| vehiculos.json | 4.849 | 2026-10-27T00:09 | https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/tran_r_vehst?format=JSON&lang=en&geo=HU11&unit=NR |

### `sensor_community`

| archivo | bytes | ingesta | origen |
|---|---|---|---|
| filtro_area_0010.json | 286.747 | 2026-10-27T00:10 | https://data.sensor.community/airrohr/v1/filter/area=47.4979,19.0402,20 |
| filtro_area_2128.json | 311.013 | 2026-10-20T21:28 | https://data.sensor.community/airrohr/v1/filter/area=47.4979,19.0402,20 |
| filtro_area_2228.json | 266.902 | 2026-09-29T22:28 | https://data.sensor.community/airrohr/v1/filter/area=47.4979,19.0402,20 |
| filtro_area_2247.json | 305.887 | 2026-10-22T22:47 | https://data.sensor.community/airrohr/v1/filter/area=47.4979,19.0402,20 |

### `opensensemap`

| archivo | bytes | ingesta | origen |
|---|---|---|---|
| boxes.json | 217.027 | 2026-10-27T00:10 | https://api.opensensemap.org/boxes |
| sensores/5cbb4a4a815d52001ab980f6.json | 415 | 2026-10-27T00:10 | https://api.opensensemap.org/boxes/5cbb4a4a815d52001ab980f6/sensors |
| sensores/5e22cd727993c4001bf78681.json | 994 | 2026-10-27T00:10 | https://api.opensensemap.org/boxes/5e22cd727993c4001bf78681/sensors |
| sensores/5e56763a37f639001bd14bb1.json | 1.169 | 2026-10-27T00:10 | https://api.opensensemap.org/boxes/5e56763a37f639001bd14bb1/sensors |
| sensores/5f15a1e8e8f87e001c7e0eac.json | 859 | 2026-10-27T00:10 | https://api.opensensemap.org/boxes/5f15a1e8e8f87e001c7e0eac/sensors |
| sensores/5f4a2ed8327264001be939e3.json | 996 | 2026-10-27T00:10 | https://api.opensensemap.org/boxes/5f4a2ed8327264001be939e3/sensors |
| sensores/5fee0624576ab7001ccf57c2.json | 991 | 2026-10-27T00:10 | https://api.opensensemap.org/boxes/5fee0624576ab7001ccf57c2/sensors |
| sensores/601ceca9e443a0001bcc9379.json | 992 | 2026-10-27T00:10 | https://api.opensensemap.org/boxes/601ceca9e443a0001bcc9379/sensors |
| sensores/602e845c37bfd7001b97bc76.json | 993 | 2026-10-27T00:10 | https://api.opensensemap.org/boxes/602e845c37bfd7001b97bc76/sensors |
| sensores/6040f4368ad04a001bdbe3c5.json | 992 | 2026-10-27T00:10 | https://api.opensensemap.org/boxes/6040f4368ad04a001bdbe3c5/sensors |
| sensores/6051eafb67c38b001becf5c1.json | 992 | 2026-10-27T00:10 | https://api.opensensemap.org/boxes/6051eafb67c38b001becf5c1/sensors |
| sensores/609ccb6225b716001c46f310.json | 993 | 2026-10-27T00:10 | https://api.opensensemap.org/boxes/609ccb6225b716001c46f310/sensors |
| sensores/609ee46125b716001c53b1f9.json | 991 | 2026-10-27T00:10 | https://api.opensensemap.org/boxes/609ee46125b716001c53b1f9/sensors |
| sensores/60c4dad1e650df001cc49789.json | 992 | 2026-10-27T00:10 | https://api.opensensemap.org/boxes/60c4dad1e650df001cc49789/sensors |
| sensores/60d596f18855dd001cc63c61.json | 993 | 2026-10-27T00:10 | https://api.opensensemap.org/boxes/60d596f18855dd001cc63c61/sensors |
| sensores/60d71dd18855dd001c7c534e.json | 993 | 2026-10-27T00:10 | https://api.opensensemap.org/boxes/60d71dd18855dd001c7c534e/sensors |
| sensores/61126d145f5cac001bb8f7b0.json | 994 | 2026-09-29T22:42 | https://api.opensensemap.org/boxes/61126d145f5cac001bb8f7b0/sensors |
| sensores/61a47f514a7833001b5191c3.json | 796 | 2026-10-27T00:10 | https://api.opensensemap.org/boxes/61a47f514a7833001b5191c3/sensors |
| sensores/61c1093fe2a8da001b202851.json | 994 | 2026-10-27T00:10 | https://api.opensensemap.org/boxes/61c1093fe2a8da001b202851/sensors |
| sensores/61cf17231b17b1001b17e00a.json | 1.020 | 2026-10-27T00:10 | https://api.opensensemap.org/boxes/61cf17231b17b1001b17e00a/sensors |
| sensores/631afd6d46ccc3001c8ef333.json | 648 | 2026-10-27T00:10 | https://api.opensensemap.org/boxes/631afd6d46ccc3001c8ef333/sensors |
| sensores/632accb7b6658f001be047aa.json | 997 | 2026-10-27T00:10 | https://api.opensensemap.org/boxes/632accb7b6658f001be047aa/sensors |
| sensores/633c4150ca8ac8001b7abbf9.json | 991 | 2026-10-27T00:10 | https://api.opensensemap.org/boxes/633c4150ca8ac8001b7abbf9/sensors |
| sensores/63550a8b817d12001b4f5cfd.json | 991 | 2026-10-27T00:10 | https://api.opensensemap.org/boxes/63550a8b817d12001b4f5cfd/sensors |
| sensores/6377557a9b1ef5001b1e6af7.json | 763 | 2026-09-29T22:42 | https://api.opensensemap.org/boxes/6377557a9b1ef5001b1e6af7/sensors |
| sensores/6391c79670c7ae001b0e1985.json | 991 | 2026-10-27T00:10 | https://api.opensensemap.org/boxes/6391c79670c7ae001b0e1985/sensors |
| sensores/63e39c28880265000751e48c.json | 648 | 2026-10-27T00:10 | https://api.opensensemap.org/boxes/63e39c28880265000751e48c/sensors |
| sensores/6411c53df954a70008b20a76.json | 853 | 2026-10-27T00:10 | https://api.opensensemap.org/boxes/6411c53df954a70008b20a76/sensors |
| sensores/641dbb33bbc9860008032fdc.json | 994 | 2026-10-27T00:11 | https://api.opensensemap.org/boxes/641dbb33bbc9860008032fdc/sensors |
| sensores/647650c8ccc90f000712f623.json | 1.897 | 2026-10-27T00:11 | https://api.opensensemap.org/boxes/647650c8ccc90f000712f623/sensors |
| sensores/6478aac1e8df1c00083f7273.json | 1.916 | 2026-10-27T00:11 | https://api.opensensemap.org/boxes/6478aac1e8df1c00083f7273/sensors |
| sensores/65bdde7ae9153000071c692c.json | 4.209 | 2026-10-27T00:11 | https://api.opensensemap.org/boxes/65bdde7ae9153000071c692c/sensors |
| sensores/65c1f984e915300007d96c67.json | 992 | 2026-10-27T00:11 | https://api.opensensemap.org/boxes/65c1f984e915300007d96c67/sensors |
| sensores/65c3b39de91530000718fc8e.json | 4.278 | 2026-10-27T00:11 | https://api.opensensemap.org/boxes/65c3b39de91530000718fc8e/sensors |
| sensores/65c4e177e9153000074a9062.json | 1.710 | 2026-10-27T00:11 | https://api.opensensemap.org/boxes/65c4e177e9153000074a9062/sensors |
| sensores/6606b5e093fed60007627629.json | 990 | 2026-10-22T22:48 | https://api.opensensemap.org/boxes/6606b5e093fed60007627629/sensors |
| sensores/661d6edc1a903a0008c7a494.json | 1.916 | 2026-10-27T00:11 | https://api.opensensemap.org/boxes/661d6edc1a903a0008c7a494/sensors |
| sensores/66431269eb5aad0007b2ed69.json | 1.909 | 2026-10-27T00:11 | https://api.opensensemap.org/boxes/66431269eb5aad0007b2ed69/sensors |
| sensores/664324d0eb5aad0007d39b9c.json | 1.910 | 2026-10-27T00:11 | https://api.opensensemap.org/boxes/664324d0eb5aad0007d39b9c/sensors |
| sensores/665edbba5a5e5e000734f495.json | 1.909 | 2026-10-27T00:11 | https://api.opensensemap.org/boxes/665edbba5a5e5e000734f495/sensors |

… y 12 archivos más del mismo patrón.

### `eea`

| archivo | bytes | ingesta | origen |
|---|---|---|---|
| aq_statistics_p1.json | 361.096 | 2026-10-27T00:10 | https://discodata.eea.europa.eu/sql?query=SELECT AirQualityStationEoICode, AQStationName, AirQualityStationType, AirQualityStationArea, Long |

### `open_meteo`

| archivo | bytes | ingesta | origen |
|---|---|---|---|
| archivo_diario.json | 314.811 | 2026-10-27T00:11 | https://archive-api.open-meteo.com/v1/archive |
| calidad_aire.json | 5.354 | 2026-10-27T00:11 | https://air-quality-api.open-meteo.com/v1/air-quality |
| pronostico.json | 5.032 | 2026-10-27T00:11 | https://api.open-meteo.com/v1/forecast |

## 4. Silver · tablas (datalake/silver/budapest.sqlite)

### `distritos` · 23 filas

Unidad territorial base. Límites OSM (admin_level=9) unidos con el Helységnévtár de KSH.  
**Fuente:** `osm_overpass + ksh` · **Grano:** 1 fila por kerület (23)

| columna | tipo | unidad | descripción |
|---|---|---|---|
| distrito_id | INTEGER PRIMARY KEY | 1–23 | Número de distrito (I–XXIII en arábigo) |
| nombre | TEXT |  | Nombre oficial en húngaro, p. ej. «V. kerület» |
| romano | TEXT |  | Numeral romano del distrito |
| apodo | TEXT |  | Nombre tradicional del distrito (Belváros-Lipótváros, Újbuda…) — etiqueta OSM name:hu alt / curado |
| lado | TEXT | Buda\|Pest\|Csepel | Margen del Danubio |
| osm_rel_id | INTEGER |  | Id de la relación OSM del límite |
| ksh_codigo | TEXT |  | Código KSH de 5 dígitos (Helységnévtár) |
| area_km2 | REAL | km² | Superficie calculada del polígono OSM |
| area_ha_ksh | REAL | ha | Superficie oficial KSH |
| poblacion | INTEGER | hab | Población residente (lakónépesség) al 1 de enero, KSH |
| poblacion_anterior | INTEGER | hab | Población residente del año anterior, KSH |
| viviendas | INTEGER | viviendas | Número de viviendas (lakások), KSH |
| anio_ksh | INTEGER | año | Año de referencia del Helységnévtár |
| centro_lat | REAL | grados | Latitud del centroide |
| centro_lon | REAL | grados | Longitud del centroide |
| geojson | TEXT | GeoJSON | Geometría MultiPolygon completa (WGS84) |

### `osm_poi` · 17.070 filas

Equipamientos, servicios, turismo y verde de OpenStreetMap clasificados en categorías del sitio.  
**Fuente:** `osm_overpass` · **Grano:** 1 fila por elemento OSM (nodo o centroide de vía/relación)

| columna | tipo | unidad | descripción |
|---|---|---|---|
| osm_tipo | TEXT | node\|way\|relation | Tipo de elemento OSM |
| osm_id | INTEGER |  | Id OSM |
| categoria | TEXT |  | Categoría temática: educacion, salud, cultura, turismo, alojamiento, gastronomia, comercio, verde, deporte, seguridad, administracion, movilidad |
| subcategoria | TEXT |  | Valor de la etiqueta OSM (school, hospital, museum, hotel…) |
| nombre | TEXT |  | Etiqueta name |
| lat | REAL | grados | Latitud (nodo o centro) |
| lon | REAL | grados | Longitud |
| estrellas | REAL |  | Etiqueta stars (alojamiento) |
| wikidata | TEXT |  | Etiqueta wikidata |
| red | TEXT |  | Etiqueta network (o brand si falta): red u operador, p. ej. «MOL Bubi» |
| distrito_id | INTEGER | 1–23 | Número de kerület (distrito) de Budapest asignado por punto-en-polígono con los límites OSM; NULL si cae fuera |

### `osm_edificios_distrito` · 23 filas

Conteo de edificios OSM (building=*) por distrito con consulta out count.  
**Fuente:** `osm_overpass` · **Grano:** 1 fila por distrito

| columna | tipo | unidad | descripción |
|---|---|---|---|
| distrito_id | INTEGER | 1–23 | Distrito |
| edificios | INTEGER | edificios | Vías y relaciones con etiqueta building |
| edificios_con_niveles | INTEGER | edificios | Edificios con etiqueta building:levels |
| fecha_osm | TEXT | ISO 8601 | Marca temporal osm_base de Overpass |

### `geofabrik_extracto` · 1 filas

Versión del extracto OSM de Hungría usada como referencia reproducible.  
**Fuente:** `geofabrik` · **Grano:** 1 fila por ejecución

| columna | tipo | unidad | descripción |
|---|---|---|---|
| fecha_replica | TEXT | ISO 8601 | timestamp del state.txt de Geofabrik |
| secuencia | INTEGER |  | sequenceNumber de replicación |
| url_pbf | TEXT |  | URL del extracto .osm.pbf |
| pbf_bytes | INTEGER | bytes | Tamaño del .osm.pbf (cabecera HTTP) |
| pbf_en_bronze | INTEGER | 0/1 | 1 si el .osm.pbf se descargó a bronze (flag --pbf) |
| poly_vertices | INTEGER |  | Vértices del polígono de recorte hungary.poly |
| ingesta | TEXT | fecha | Fecha de la ingesta |

### `copernicus_distrito` · 46 filas

Estadística zonal de capas HRL 2018 (píxel 10 m) sobre el polígono de cada distrito.  
**Fuente:** `copernicus` · **Grano:** 1 fila por distrito × capa

| columna | tipo | unidad | descripción |
|---|---|---|---|
| distrito_id | INTEGER | 1–23 | Distrito |
| capa | TEXT |  | imperviousness_2018 (IMD, sellado del suelo) \| tree_cover_2018 (TCD, cobertura arbórea) |
| media | REAL | % (0–100) | Media de píxeles válidos 0–100 |
| mediana | REAL | % | Mediana |
| desviacion | REAL | % | Desviación estándar |
| pct_alto | REAL | % de superficie | IMD: píxeles ≥ 80 % sellados; TCD: píxeles con cobertura ≥ 10 % |
| pixeles | INTEGER | píxeles | Píxeles válidos considerados |

### `gtfs_rutas` · 390 filas

Líneas del transporte público de BKK (routes.txt) con viajes programados el día de referencia.  
**Fuente:** `bkk_gtfs` · **Grano:** 1 fila por route_id

| columna | tipo | unidad | descripción |
|---|---|---|---|
| route_id | TEXT PRIMARY KEY |  | Id GTFS de la ruta |
| nombre_corto | TEXT |  | route_short_name (número de línea) |
| nombre_largo | TEXT |  | route_long_name / route_desc |
| tipo_gtfs | INTEGER |  | route_type original (0 tranvía, 1 metro, 3 bus, 4 ferry, 11 trolebús, 109 HÉV…) |
| modo | TEXT |  | Modo normalizado: metro, tranvia, trolebus, bus, hev, ferry, otro |
| color | TEXT | hex | route_color |
| viajes_dia_ref | INTEGER | viajes/día | Viajes activos el día laborable de referencia |

### `gtfs_paradas` · 6.309 filas

Paradas y andenes (stops.txt) con oferta programada del día laborable de referencia.  
**Fuente:** `bkk_gtfs` · **Grano:** 1 fila por stop_id

| columna | tipo | unidad | descripción |
|---|---|---|---|
| stop_id | TEXT PRIMARY KEY |  | Id GTFS de la parada |
| nombre | TEXT |  | stop_name |
| lat | REAL | grados | stop_lat |
| lon | REAL | grados | stop_lon |
| tipo_ubicacion | INTEGER |  | location_type (0 parada, 1 estación…) |
| estacion_padre | TEXT |  | parent_station |
| accesible | INTEGER | 0/1/2 | wheelchair_boarding |
| salidas_dia_ref | INTEGER | salidas/día | Detenciones programadas (stop_times) el día de referencia |
| rutas_n | INTEGER | rutas | Rutas distintas que pasan el día de referencia |
| modos | TEXT |  | Modos que sirven la parada, separados por coma |
| distrito_id | INTEGER | 1–23 | Número de kerület (distrito) de Budapest asignado por punto-en-polígono con los límites OSM; NULL si cae fuera |

### `gtfs_lineas_geom` · 57 filas

Trazado representativo (shape más frecuente) simplificado con Douglas-Peucker (~10 m).  
**Fuente:** `bkk_gtfs` · **Grano:** 1 fila por ruta de modo guiado (metro, tranvía, trolebús, HÉV, ferry)

| columna | tipo | unidad | descripción |
|---|---|---|---|
| route_id | TEXT |  | Ruta |
| modo | TEXT |  | Modo normalizado |
| nombre_corto | TEXT |  | Línea |
| color | TEXT | hex | Color |
| geojson | TEXT | GeoJSON | LineString WGS84 |

### `gtfs_feed` · 1 filas

Metadatos del feed y del día de referencia usado para medir oferta.  
**Fuente:** `bkk_gtfs` · **Grano:** 1 fila por ingesta

| columna | tipo | unidad | descripción |
|---|---|---|---|
| editor | TEXT |  | feed_publisher_name |
| version | TEXT |  | feed_version |
| inicio | TEXT | fecha | feed_start_date / primer servicio |
| fin | TEXT | fecha | feed_end_date / último servicio |
| dia_referencia | TEXT | fecha | Primer miércoles dentro de la vigencia |
| viajes_dia_ref | INTEGER | viajes | Viajes activos el día de referencia |
| detenciones_dia_ref | INTEGER | detenciones | stop_times del día de referencia |
| origen | TEXT |  | bkk (directo) o mobilitydb (espejo) |

### `mdb_feeds` · 5 filas

Registro de feeds GTFS / GTFS-RT de Budapest en Mobility Database (BKK = mdb-990, antes TransitFeeds tfs-42).  
**Fuente:** `mobilitydb` · **Grano:** 1 fila por feed del catálogo cuyo municipio es Budapest

| columna | tipo | unidad | descripción |
|---|---|---|---|
| mdb_id | TEXT |  | Id Mobility Database |
| tipo | TEXT |  | gtfs \| gtfs_rt |
| entidad | TEXT |  | Entidades RT: sa (alertas), tu (trip updates), vp (posiciones) |
| proveedor | TEXT |  | Operador |
| oficial | TEXT |  | is_official |
| estado | TEXT |  | active \| inactive \| deprecated |
| url_directa | TEXT |  | urls.direct_download |
| url_espejo | TEXT |  | urls.latest (copia de MobilityData) |
| requiere_clave | INTEGER | 0/1 | urls.authentication_type > 0 |
| bbox | TEXT |  | min_lat,max_lat,min_lon,max_lon |
| extraido | TEXT | fecha | bounding_box.extracted_on |

### `bubi_estaciones` · 220 filas

Ubicación de las estaciones MOL Bubi. Mientras el feed del operador (bubi, F07) no publique estaciones, salen de OSM: amenity=bicycle_rental con red MOL Bubi (origen = osm).  
**Fuente:** `osm_overpass + bubi` · **Grano:** 1 fila por estación

| columna | tipo | unidad | descripción |
|---|---|---|---|
| estacion_id | INTEGER |  | Id OSM de la estación (o uid nextbike si el feed vuelve a publicarlas) |
| nombre | TEXT |  | Nombre |
| lat | REAL | grados |  |
| lon | REAL | grados |  |
| origen | TEXT |  | osm (OSM, red MOL Bubi) \| nextbike_vivo (feed del operador) |
| distrito_id | INTEGER | 1–23 | Número de kerület (distrito) de Budapest asignado por punto-en-polígono con los límites OSM; NULL si cae fuera |

### `bubi_disponibilidad` · 0 filas

Bicicletas y anclajes por estación según el feed del operador. Hoy no existe: el feed no publica estaciones y la fuente es candidata.  
**Fuente:** `bubi` · **Grano:** 1 fila por estación en la última instantánea (solo si el feed publica estaciones)

| columna | tipo | unidad | descripción |
|---|---|---|---|
| estacion_id | INTEGER |  | uid nextbike |
| numero | TEXT |  | Número de estación |
| bicis | INTEGER | bicicletas | Bicicletas disponibles |
| anclajes | INTEGER | anclajes | bike_racks (capacidad) |
| anclajes_libres | INTEGER | anclajes | free_racks |
| ts | TEXT | ISO 8601 | Hora de la instantánea |

### `bubi_historico` · 0 filas

Serie de instantáneas agregadas del sistema MOL Bubi. Solo se escribe cuando la fuente está integrada.  
**Fuente:** `bubi` · **Grano:** 1 fila por ejecución en que el feed publica estaciones (se acumula)

| columna | tipo | unidad | descripción |
|---|---|---|---|
| ts | TEXT | ISO 8601 | Hora de la instantánea |
| estaciones | INTEGER |  | Estaciones con disponibilidad publicada (0 si el operador no la expone) |
| bicis | INTEGER |  | Bicicletas disponibles (available_bikes del sistema) |
| anclajes | INTEGER |  | Capacidad total |
| flota_objetivo | INTEGER | bicicletas | set_point_bikes: flota objetivo declarada por el operador |

### `ksh_hvd` · 11.436 filas

Series HVD de KSH (SDMX-CSV) filtradas a Hungría (HU), Budapest NUTS2 (HU11) y NUTS3 (HU110).  
**Fuente:** `ksh_hvd` · **Grano:** 1 fila por dataset × indicador × geo × año × sexo × edad

| columna | tipo | unidad | descripción |
|---|---|---|---|
| recurso | TEXT |  | Clave del recurso: poblacion_edad_sexo, edad_mediana, natalidad, mortalidad, esperanza_vida, mortalidad_infantil |
| indicador | TEXT |  | INDIC_DE / UNIT del SDMX (p. ej. FMEDAGEPOP, GBIRTHRT, NR) |
| geo | TEXT | NUTS | HU, HU1, HU11, HU110 |
| anio | INTEGER | año | TIME_PERIOD |
| sexo | TEXT | T\|M\|F | SEX (T si no aplica) |
| edad | TEXT |  | AGE SDMX (Y_LT5, Y5-9…, TOTAL, Y_LT1) |
| valor | REAL | según indicador | OBS_VALUE |

### `eurostat_obs` · 1.835 filas

Observaciones JSON-stat aplanadas para Budapest (HU11, HU110, ciudad HU001C) y Hungría cuando no hay regional.  
**Fuente:** `eurostat` · **Grano:** 1 fila por dataset × combinación de dimensiones × periodo

| columna | tipo | unidad | descripción |
|---|---|---|---|
| dataset | TEXT |  | Código Eurostat (nama_10r_3gdp, urb_ctour…) |
| clave | TEXT |  | Clave estable del indicador dentro del sitio |
| geo | TEXT |  | geo o cities |
| periodo | TEXT |  | time (año o trimestre) |
| dimensiones | TEXT | JSON | Resto de dimensiones {dim: código} |
| etiqueta | TEXT |  | Etiqueta legible del indicador (indic_ur, na_item…) |
| unidad | TEXT |  | Unidad declarada |
| valor | REAL | según unidad | Valor |
| flag | TEXT |  | Estado Eurostat (p provisional, e estimado, b ruptura) |

### `ksh_distritos_historico` · 161 filas

Población, superficie y viviendas por distrito según cada edición del Helységnévtár descargada.  
**Fuente:** `ksh` · **Grano:** 1 fila por distrito × año del Helységnévtár

| columna | tipo | unidad | descripción |
|---|---|---|---|
| distrito_id | INTEGER | 1–23 | Distrito |
| anio | INTEGER | año | Edición (estado al 1 de enero) |
| ksh_codigo | TEXT |  | Código KSH |
| area_ha | REAL | ha | Superficie |
| poblacion | INTEGER | hab | Población residente |
| viviendas | INTEGER | viviendas | Viviendas |

### `eea_estaciones` · 15 filas

Estaciones de la red húngara (OMSZ) que reportan a la EEA.  
**Fuente:** `eea` · **Grano:** 1 fila por estación oficial en Budapest

| columna | tipo | unidad | descripción |
|---|---|---|---|
| estacion | TEXT PRIMARY KEY |  | AirQualityStationEoICode (p. ej. HU0022A) |
| nombre | TEXT |  | AQStationName |
| tipo | TEXT |  | Background \| Traffic \| Industrial |
| area | TEXT |  | Urban \| Suburban \| Rural |
| lat | REAL | grados |  |
| lon | REAL | grados |  |
| altitud | REAL | m |  |
| distrito_id | INTEGER | 1–23 | Número de kerület (distrito) de Budapest asignado por punto-en-polígono con los límites OSM; NULL si cae fuera |

### `eea_estadisticas` · 813 filas

Estadísticas anuales oficiales (E1a validado; E2a para el año en curso).  
**Fuente:** `eea` · **Grano:** 1 fila por estación × contaminante × agregación × año

| columna | tipo | unidad | descripción |
|---|---|---|---|
| estacion | TEXT |  | Código EoI |
| contaminante | TEXT |  | PM2.5, PM10, NO2, O3 |
| agregacion | TEXT |  | P1Y media anual; P1Y-daysAbove50 días >50 µg/m³ (PM10); P1Y-hrsAbove200 horas >200 (NO2); P1Y-dmaxAbove120 días (O3); SOMO35 |
| anio | INTEGER | año | YearOfStatistics |
| valor | REAL | µg/m³ \| días \| horas | AirPollutionLevel |
| unidad | TEXT |  | UnitOfAirpollutionLevel |
| cobertura | REAL | % | DataCoverage |
| verificacion | INTEGER | 1/2/3 | 1 verificado, 2 preliminar, 3 no verificado |
| flujo | TEXT |  | SourceDataFlow (E1a / E2a) |

### `sc_sensores` · 187 filas

BAJO COSTO · Promedio de 5 minutos de sensores ciudadanos ópticos de bajo costo (sin calibración oficial) en un radio de 20 km del centro (solo exteriores).  
**Fuente:** `sensor_community` · **Grano:** 1 fila por sensor en la instantánea

| columna | tipo | unidad | descripción |
|---|---|---|---|
| sensor_id | INTEGER |  | Id de sensor |
| ubicacion_id | INTEGER |  | Id de ubicación |
| tipo_sensor | TEXT |  | SDS011, SPS30, BME280, DHT22… |
| lat | REAL | grados |  |
| lon | REAL | grados |  |
| pm25 | REAL | µg/m³ | P2 |
| pm10 | REAL | µg/m³ | P1 |
| temperatura | REAL | °C |  |
| humedad | REAL | % |  |
| ts | TEXT | UTC | timestamp de la medición |
| distrito_id | INTEGER | 1–23 | Número de kerület (distrito) de Budapest asignado por punto-en-polígono con los límites OSM; NULL si cae fuera |

### `sc_historico` · 4 filas

BAJO COSTO · Mediana urbana de PM2.5/PM10 de sensores ciudadanos de bajo costo en cada instantánea.  
**Fuente:** `sensor_community` · **Grano:** 1 fila por ejecución (se acumula)

| columna | tipo | unidad | descripción |
|---|---|---|---|
| ts | TEXT | ISO 8601 | Hora de la ingesta |
| sensores_pm | INTEGER |  | Sensores de partículas con dato |
| pm25_mediana | REAL | µg/m³ |  |
| pm10_mediana | REAL | µg/m³ |  |

### `osem_sensores` · 1.006 filas

BAJO COSTO · Último valor de cada sensor de las senseBoxes exteriores de Budapest (sensores ciudadanos de bajo costo).  
**Fuente:** `opensensemap` · **Grano:** 1 fila por sensor de senseBox dentro del bbox

| columna | tipo | unidad | descripción |
|---|---|---|---|
| box_id | TEXT |  | Id de la senseBox |
| box_nombre | TEXT |  | Nombre |
| sensor_id | TEXT |  | Id del sensor |
| fenomeno | TEXT |  | title (PM2.5, Temperatur…) |
| fenomeno_norm | TEXT |  | pm25, pm10, temperatura, humedad, presion, otro |
| unidad | TEXT |  |  |
| tipo_sensor | TEXT |  | sensorType |
| valor | REAL | según unidad | lastMeasurement.value |
| ts | TEXT | UTC | lastMeasurement.createdAt |
| vigente | INTEGER | 0/1 | 1 si la medición tiene menos de 7 días |
| lat | REAL | grados |  |
| lon | REAL | grados |  |
| distrito_id | INTEGER | 1–23 | Número de kerület (distrito) de Budapest asignado por punto-en-polígono con los límites OSM; NULL si cae fuera |

### `meteo_diario` · 9.795 filas

MODELO · Reanálisis ERA5 (salida de modelo, no medición) vía Open-Meteo Archive en el centro de Budapest.  
**Fuente:** `open_meteo` · **Grano:** 1 fila por día (desde 2000-01-01)

| columna | tipo | unidad | descripción |
|---|---|---|---|
| fecha | TEXT PRIMARY KEY | fecha |  |
| tmax | REAL | °C | temperature_2m_max |
| tmin | REAL | °C | temperature_2m_min |
| tmedia | REAL | °C | temperature_2m_mean |
| precipitacion | REAL | mm | precipitation_sum |

### `meteo_horario` · 120 filas

MODELO · Pronóstico horario de Open-Meteo y calidad del aire del modelo CAMS Europa (~10 km); nada de esta tabla es medición.  
**Fuente:** `open_meteo` · **Grano:** 1 fila por hora (−2 a +3 días)

| columna | tipo | unidad | descripción |
|---|---|---|---|
| hora | TEXT PRIMARY KEY | local |  |
| temperatura | REAL | °C | temperature_2m |
| humedad | REAL | % | relative_humidity_2m |
| precipitacion | REAL | mm |  |
| viento | REAL | km/h | wind_speed_10m |
| pm25 | REAL | µg/m³ | CAMS pm2_5 |
| pm10 | REAL | µg/m³ | CAMS pm10 |
| no2 | REAL | µg/m³ | CAMS nitrogen_dioxide |
| o3 | REAL | µg/m³ | CAMS ozone |
| eaqi | REAL | índice | European AQI |

## 5. Gold · temas del sitio (datalake/gold/temas/*.json)

Estructura común: `{tema, titulo, probado, fuentes[], cifras{}, series{}, listas{}}`.

### `ambiente.json` · Ambiente y clima

**Cifras**

| clave | etiqueta | unidad | fuente | estado | vigencia | nota |
|---|---|---|---|---|---|---|
| pm25_anual | PM2.5 media anual (estaciones oficiales) | µg/m³ | eea | derivado | 2026 | Promedio de 1 estación(es) con cobertura ≥ 75 % en 2026. Guía OMS 2021: 5 µg/m³ · límite UE: 25 µg/m³ |
| pm10_anual | PM10 media anual (estaciones oficiales) | µg/m³ | eea | derivado | 2026 | Promedio de 2 estación(es) con cobertura ≥ 75 % en 2026. Guía OMS 2021: 15 µg/m³ · límite UE: 40 µg/m³ |
| no2_anual | NO2 media anual (estaciones oficiales) | µg/m³ | eea | derivado | 2026 | Promedio de 2 estación(es) con cobertura ≥ 75 % en 2026. Guía OMS 2021: 10 µg/m³ · límite UE: 40 µg/m³ |
| estaciones_eea | Estaciones oficiales con reporte a la EEA | estaciones | eea | observado | 2026 |  |
| pm25_ciudadano | PM2.5 ahora · mediana de sensores ciudadanos | µg/m³ | sensor_community | bajo_costo | 2026-10-27 00:09:58 | Bajo costo: sensores ópticos ciudadanos sin calibración oficial (sobreestiman con humedad alta); promedio de 5 minutos en la instantánea. |
| sensores_ciudadanos | Sensores ciudadanos de partículas (bajo costo) en Budapest | sensores | sensor_community | bajo_costo | 2026-10-27 00:09:58 |  |
| sensebox | senseBoxes (bajo costo) con datos en los últimos 7 días | cajas | opensensemap | bajo_costo | 2026-10-27 | 176 cajas registradas en el área |
| temp_anual | Temperatura media del último año completo | °C | open_meteo | modelo | 2025 | Modelo: reanálisis ERA5 servido por Open-Meteo, no medición de estación. |
| anomalia | Anomalía frente a 2000–2009 | °C | open_meteo | modelo | 2025 | Diferencia calculada sobre el reanálisis ERA5 (modelo). |
| dias_calor | Días con máxima ≥ 30 °C | días | open_meteo | modelo | 2025 | Modelo: reanálisis ERA5 servido por Open-Meteo, no medición de estación. |
| noches_tropicales | Noches tropicales (mínima ≥ 20 °C) | noches | open_meteo | modelo | 2025 | Modelo: reanálisis ERA5 servido por Open-Meteo, no medición de estación. |
| sellado | Suelo sellado medio (ponderado por área) | % | copernicus | derivado | 2018 |  |
| arbolado | Cobertura arbórea media (ponderada por área) | % | copernicus | derivado | 2018 |  |

**Series** (`puntos` = `[[x, y], …]`; con varias series, `series[].puntos`)

| clave | etiqueta | unidad | fuente | puntos | rango | subseries |
|---|---|---|---|---|---|---|
| particulas | Partículas: media anual de estaciones oficiales | µg/m³ | eea | 24 | 2003 – 2026 | PM10, PM2.5 |
| no2 | NO₂: media anual de estaciones oficiales | µg/m³ | eea | 25 | 1997 – 2026 | — |
| pm10_dias | Días con PM10 > 50 µg/m³ (estación más expuesta) | días | eea | 24 | 2003 – 2026 | — |
| pm25_ciudadano | PM2.5 ciudadano de bajo costo por instantánea | µg/m³ | sensor_community | 4 | 2026-09-29T22:28:00Z – 2026-10-26T00:10:00Z | — |
| cams_pm25 | PM2.5 y PM10 · modelo CAMS (−2 a +3 días) | µg/m³ | open_meteo | 120 | 2026-10-25T00:00 – 2026-10-29T23:00 | PM2.5, PM10 |
| temperatura_horaria | Temperatura · modelo de pronóstico (−2 a +3 días) | °C | open_meteo | 120 | 2026-10-25T00:00 – 2026-10-29T23:00 | — |
| temperatura_anual | Temperatura media anual · modelo ERA5 | °C | open_meteo | 26 | 2000 – 2025 | — |
| dias_calor | Días con máxima ≥ 30 °C · modelo ERA5 | días | open_meteo | 26 | 2000 – 2025 | — |

**Listas**

| clave | filas | columnas |
|---|---|---|
| estaciones | 15 | NO2, O3, PM10, PM25, anio, area, distrito_id, estacion, nombre, tipo |
| suelo_distritos | 23 | arbolado, distrito, pm25_sensores, sellado, sellado_alto, sensores |
| urban_audit_ambiente | 24 | anio, codigo, indicador, valor |

### `catalogo.json` · Fuentes y método

**Cifras**

| clave | etiqueta | unidad | fuente | estado | vigencia | nota |
|---|---|---|---|---|---|---|
| fuentes_ok | Fuentes operativas | de 13 | lago | derivado | 2026-10-26 |  |
| bronze_mb | Volumen crudo acumulado en bronze | MB | lago | derivado | 2026-10-26 |  |

**Listas**

| clave | filas | columnas |
|---|---|---|
| fuentes | 13 | acceso, bronze_archivos, bronze_mb, codigo, error, estado, frecuencia, id, licencia, nombre, organismo, probada, tablas, ultima_ingesta, url |
| zonas | 4 | contenido, ruta, zona |
| brechas | 5 | motivo, tema |

### `demografia.json` · Gente

**Cifras**

| clave | etiqueta | unidad | fuente | estado | vigencia | nota |
|---|---|---|---|---|---|---|
| poblacion_nuts3 | Población al 1 de enero (NUTS3 HU110) | hab | ksh_hvd | observado | 2024 |  |
| edad_mediana | Edad mediana | años | ksh_hvd | observado | 2024 |  |
| dependencia_vejez | Dependencia de vejez (65+ / 20–64) | % | ksh_hvd | observado | 2024 |  |
| natalidad | Tasa bruta de natalidad | ‰ | ksh_hvd | observado | 2023 |  |
| mortalidad | Tasa bruta de mortalidad | ‰ | ksh_hvd | observado | 2023 |  |
| esperanza_vida | Esperanza de vida al nacer (HU11) | años | ksh_hvd | observado | 2023 |  |
| mortalidad_infantil | Mortalidad infantil (HU11) | ‰ | ksh_hvd | observado | 2023 |  |

**Series** (`puntos` = `[[x, y], …]`; con varias series, `series[].puntos`)

| clave | etiqueta | unidad | fuente | puntos | rango | subseries |
|---|---|---|---|---|---|---|
| poblacion | Población de Budapest (HU110) | hab | ksh_hvd | 11 | 2014 – 2024 | — |
| edad_mediana | Edad mediana | años | ksh_hvd | 11 | 2014 – 2024 | Budapest, Hungría |
| esperanza_vida | Esperanza de vida al nacer | años | ksh_hvd | 10 | 2014 – 2023 | Mujeres, Hombres |
| natalidad_mortalidad | Natalidad y mortalidad | ‰ | ksh_hvd | 11 | 2013 – 2023 | Natalidad, Mortalidad |
| dependencia | Dependencia de vejez | % | ksh_hvd | 11 | 2014 – 2024 | Budapest, Hungría |

**Listas**

| clave | filas | columnas |
|---|---|---|
| piramide | 18 | grupo, hombres, mujeres |
| piramide_meta | 1 | anio, fuente |
| poblacion_distritos | 23 | densidad, distrito, poblacion, var_poblacion |

### `distritos.json` · Atlas de los 23 distritos

**Cifras**

| clave | etiqueta | unidad | fuente | estado | vigencia | nota |
|---|---|---|---|---|---|---|
| metricas_n | Métricas por distrito | métricas | lago | derivado | 2026-10-26 |  |
| pares_n | Pares de métricas comparables | pares | lago | derivado | 2026-10-26 |  |

**Listas**

| clave | filas | columnas |
|---|---|---|
| distritos | 23 | alojamiento, apodo, arbolado, area_km2, bubi, bubi_km2, centro, comercio_10k, cultura_km2, densidad, distrito_id, edificios_km2, educacion_10k, gastronomia_km2, guiado_pct, hab_vivienda, lado, nombre, paradas, paradas_km2, pm25_sensores, pm25_sensores_n, poblacion, poi, romano, salidas, salidas_1000 |
| metricas | 21 | dimension, estado, etiqueta, formula, fuente, id, sentido, unidad |
| dimensiones | 5 | descripcion, id, metricas, nombre |
| pares | 210 | n, pearson, spearman, x, y |

### `economia.json` · Economía y vivienda

**Cifras**

| clave | etiqueta | unidad | fuente | estado | vigencia | nota |
|---|---|---|---|---|---|---|
| pib_hab_eur | PIB por habitante (HU110) | €/hab | eurostat | observado | 2024 |  |
| desempleo | Tasa de desempleo 20–64 | % | eurostat | observado | 2025 |  |
| empleo | Tasa de empleo 20–64 | % | eurostat | observado | 2025 |  |
| ingreso_disponible | Ingreso disponible de los hogares | PPS/hab | eurostat | observado | 2023 |  |
| riesgo_pobreza_exclusion | Riesgo de pobreza o exclusión (AROPE) | % | eurostat | observado | 2025 |  |
| educacion_terciaria | Población 25–64 con estudios terciarios | % | eurostat | observado | 2025 |  |
| gasto_id_pib | Gasto en I+D | % PIB | eurostat | observado | 2024 |  |
| precio_vivienda | Índice de precios de vivienda (Hungría, como proxy de Budapest) | 2015 = 100 | eurostat | proxy | 2026-T2 | PROXY: Eurostat no publica el índice por región; se usa el de toda Hungría como aproximación para Budapest. |
| empresas_activas | Empresas activas (HU110) | empresas | eurostat | observado | 2020 |  |
| viviendas_1000 | Viviendas por 1.000 habitantes | viv/1.000 hab | ksh | derivado | 2026 |  |

**Series** (`puntos` = `[[x, y], …]`; con varias series, `series[].puntos`)

| clave | etiqueta | unidad | fuente | puntos | rango | subseries |
|---|---|---|---|---|---|---|
| pib_hab_eur | PIB por habitante (HU110) | €/hab | eurostat | 25 | 2000 – 2024 | — |
| desempleo | Tasa de desempleo 20–64 | % | eurostat | 13 | 2013 – 2025 | — |
| empleo | Tasa de empleo 20–64 | % | eurostat | 13 | 2013 – 2025 | — |
| ingreso_disponible | Ingreso disponible de los hogares | PPS/hab | eurostat | 11 | 2013 – 2023 | — |
| riesgo_pobreza_exclusion | Riesgo de pobreza o exclusión (AROPE) | % | eurostat | 8 | 2018 – 2025 | — |
| educacion_terciaria | Población 25–64 con estudios terciarios | % | eurostat | 13 | 2013 – 2025 | — |
| gasto_id_pib | Gasto en I+D | % PIB | eurostat | 8 | 2017 – 2024 | — |
| precio_vivienda | Índice de precios de vivienda · Hungría (proxy de Budapest) | 2015 = 100 | eurostat | 78 | 2007 – 2026-T2 | — |

**Listas**

| clave | filas | columnas |
|---|---|---|
| vivienda_distritos | 23 | distrito, hab_vivienda, viviendas, viviendas_km2 |
| urban_audit_trabajo | 34 | anio, codigo, indicador, valor |

### `movilidad.json` · Movilidad

**Cifras**

| clave | etiqueta | unidad | fuente | estado | vigencia | nota |
|---|---|---|---|---|---|---|
| viajes_dia | Viajes programados en un día laborable | viajes | bkk_gtfs | observado | 2026-10-28 | Miércoles de referencia 2026-10-28; feed 2820.20261027 (bkk) |
| detenciones_dia | Detenciones programadas por día laborable | detenciones | bkk_gtfs | observado | 2026-10-28 |  |
| paradas | Paradas y andenes con servicio | paradas | bkk_gtfs | observado | 2026-10-28 |  |
| accesibles | Paradas declaradas accesibles en silla de ruedas | % | bkk_gtfs | observado | 2026-10-28 |  |
| lineas | Líneas con servicio el día de referencia | líneas | bkk_gtfs | observado | 2026-10-28 |  |
| bubi_estaciones | Estaciones MOL Bubi (cartografía OSM) | estaciones | osm_overpass | observado | 2026-10-26 | El feed del operador (F07) no publica estaciones y queda como fuente candidata: ubicaciones de OSM con red MOL Bubi, sin disponibilidad. |
| turismos | Parque de turismos (HU11) | vehículos | eurostat | observado | 2024 |  |
| motorizacion | Motorización | turismos/1.000 hab | eurostat | derivado | 2024 |  |

**Series** (`puntos` = `[[x, y], …]`; con varias series, `series[].puntos`)

| clave | etiqueta | unidad | fuente | puntos | rango | subseries |
|---|---|---|---|---|---|---|
| turismos | Parque de turismos | vehículos | eurostat | 9 | 2016 – 2024 | — |

**Listas**

| clave | filas | columnas |
|---|---|---|
| modos | 6 | modo, rutas, viajes |
| paradas_top | 20 | distrito_id, lat, lon, modos, nombre, rutas, salidas |
| movilidad_distritos | 23 | bubi, distrito, guiado_pct, paradas, salidas, salidas_1000 |
| feeds | 5 | entidad, estado, mdb_id, proveedor, requiere_clave, tipo, url_directa |
| urban_audit_transporte | 13 | anio, codigo, indicador, valor |

### `preguntas.json` · Preguntas del sistema

**Listas**

| clave | filas | columnas |
|---|---|---|
| preguntas | 6 | cambiaria, estado, fuentes, id, limites, motivo, pregunta, respuesta, seccion |

### `territorio.json` · Territorio

**Cifras**

| clave | etiqueta | unidad | fuente | estado | vigencia | nota |
|---|---|---|---|---|---|---|
| poblacion | Población residente (23 distritos) | hab | ksh | observado | 2026-01-01 |  |
| superficie | Superficie | km² | ksh | observado | 2026-01-01 |  |
| densidad | Densidad media | hab/km² | ksh | derivado | 2026 |  |
| viviendas | Viviendas | viviendas | ksh | observado | 2026-01-01 |  |
| distritos | Distritos | kerületek | osm_overpass | observado | 2026-10-26 |  |
| edificios | Edificios cartografiados en OSM | edificios | osm_overpass | observado | 2026-10-27 |  |
| poi | Equipamientos y servicios OSM clasificados | puntos | osm_overpass | observado | 2026-10-26 |  |
| osm_replica | Réplica OSM de referencia (Geofabrik) |  | geofabrik | observado | 2026-10-25 | Extracto Hungría .osm.pbf de 328 MB, secuencia 4950 |

**Series** (`puntos` = `[[x, y], …]`; con varias series, `series[].puntos`)

| clave | etiqueta | unidad | fuente | puntos | rango | subseries |
|---|---|---|---|---|---|---|
| poblacion_helysegnevtar | Población de Budapest (suma de distritos) | hab | ksh | 7 | 2020 – 2026 | — |

**Listas**

| clave | filas | columnas |
|---|---|---|
| poi_categorias | 12 | categoria, n |
| distritos | 23 | apodo, area_km2, densidad, distrito_id, lado, poblacion, romano, var_poblacion, viviendas |

### `turismo.json` · Turismo

**Cifras**

| clave | etiqueta | unidad | fuente | estado | vigencia | nota |
|---|---|---|---|---|---|---|
| pernoctaciones | Pernoctaciones en alojamiento turístico (HU11) | noches | eurostat | observado | 2025 |  |
| pct_extranjeros | Pernoctaciones de no residentes | % | eurostat | derivado | 2025 |  |
| llegadas | Llegadas de huéspedes (HU11) | llegadas | eurostat | observado | 2025 |  |
| estancia_media | Estancia media | noches | eurostat | derivado | 2025 |  |
| alojamientos_osm | Alojamientos cartografiados (OSM) | establec. | osm_overpass | observado | 2026-10-26 |  |
| atractivos_osm | Museos, atractivos y cultura (OSM) | lugares | osm_overpass | observado | 2026-10-26 |  |

**Series** (`puntos` = `[[x, y], …]`; con varias series, `series[].puntos`)

| clave | etiqueta | unidad | fuente | puntos | rango | subseries |
|---|---|---|---|---|---|---|
| pernoctaciones | Pernoctaciones | noches | eurostat | 11 | 2015 – 2025 | Total, No residentes, Residentes |
| llegadas | Llegadas | llegadas | eurostat | 11 | 2015 – 2025 | Total, No residentes, Residentes |

**Listas**

| clave | filas | columnas |
|---|---|---|
| alojamiento_tipos | 5 | n, subcategoria |
| atractivos_tipos | 9 | n, subcategoria |
| turismo_distritos | 23 | alojamiento, cultura_turismo, distrito, gastronomia |
| urban_audit_turismo | 12 | anio, codigo, indicador, valor |

## 6. Métricas por distrito (atlas, correlaciones y diagnóstico)

Cada `score_<dimensión>` es el promedio de las métricas de esa dimensión normalizadas min–max 0–100 entre los 23 distritos (invertidas cuando `sentido = inv`, es decir, cuando menos es mejor). El índice del atlas es el promedio ponderado de los scores con los pesos que elige el usuario.

| id | etiqueta | unidad | fuente | estado | dimensión | sentido | fórmula |
|---|---|---|---|---|---|---|---|
| poblacion | Población residente | hab | ksh | observado | — | — | Helységnévtár, lakónépesség al 1 de enero |
| densidad | Densidad de población | hab/km² | ksh | derivado | vivienda | dir | poblacion / (area_ha_ksh / 100) |
| var_poblacion | Variación de población (5 años) | % | ksh | derivado | vivienda | dir | (pob_año / pob_año−5 − 1) × 100 |
| hab_vivienda | Habitantes por vivienda | hab/viv | ksh | derivado | — | — | poblacion / viviendas |
| viviendas_km2 | Viviendas por km² | viv/km² | ksh | derivado | vivienda | dir | viviendas / km² |
| paradas_km2 | Paradas con servicio por km² | paradas/km² | bkk_gtfs | derivado | movilidad | dir | paradas (location_type 0) con ≥1 salida el día de referencia / km² |
| salidas_1000 | Salidas de transporte público por 1.000 hab | salidas/día | bkk_gtfs | derivado | movilidad | dir | Σ stop_times del día laborable de referencia / población × 1.000 |
| guiado_pct | Paradas servidas por modo guiado | % | bkk_gtfs | derivado | movilidad | dir | paradas con metro, tranvía, trolebús o HÉV / paradas con servicio |
| bubi_km2 | Estaciones MOL Bubi por km² | est/km² | osm_overpass | observado | movilidad | dir | estaciones OSM amenity=bicycle_rental de la red MOL Bubi / km² |
| educacion_10k | Centros educativos por 10.000 hab | centros | osm_overpass | derivado | servicios | dir | POI categoría educacion / población × 10.000 |
| salud_10k | Equipamientos de salud por 10.000 hab | equip. | osm_overpass | derivado | servicios | dir | POI categoría salud / población × 10.000 |
| cultura_km2 | Cultura y turismo por km² | POI/km² | osm_overpass | derivado | servicios | dir | POI cultura + turismo / km² |
| comercio_10k | Comercio de proximidad por 10.000 hab | tiendas | osm_overpass | derivado | servicios | dir | POI categoría comercio / población × 10.000 |
| gastronomia_km2 | Gastronomía por km² | locales/km² | osm_overpass | derivado | — | — | POI categoría gastronomia / km² |
| alojamiento | Alojamientos turísticos (OSM) | establec. | osm_overpass | observado | — | — | POI categoría alojamiento |
| arbolado | Cobertura arbórea media | % | copernicus | observado | verde | dir | Media de Tree Cover Density 2018 (0–100) en el polígono |
| verde_10k | Parques y jardines por 10.000 hab | espacios | osm_overpass | derivado | verde | dir | POI leisure=park\|garden\|nature_reserve / población × 10.000 |
| sellado | Suelo sellado medio | % | copernicus | observado | verde | inv | Media de Imperviousness Density 2018 (0–100) |
| sellado_alto | Superficie muy sellada (≥80 %) | % sup. | copernicus | observado | — | — | Píxeles con IMD ≥ 80 / píxeles válidos |
| edificios_km2 | Edificios OSM por km² | edif./km² | osm_overpass | derivado | — | — | building=* (vías + relaciones) / km² |
| pm25_sensores | PM2.5 ciudadano de bajo costo (mediana) | µg/m³ | sensor_community | bajo_costo | ambiente | inv | Mediana de sensores ciudadanos exteriores de bajo costo del distrito en la instantánea (mínimo 2) |

## 7. Gold · capas geográficas (datalake/gold/geo/*.geojson)

| archivo | geometría | propiedades | origen silver | elementos |
|---|---|---|---|---|
| distritos.geojson | MultiPolygon | 23 distritos simplificados (~13 m) con todas las métricas del atlas y score_<dimensión> 0–100 | distritos + métricas gold | 23 |
| paradas.geojson | Point | n nombre · s salidas día ref. · r rutas · m modos · d distrito | gtfs_paradas | 5562 |
| lineas.geojson | LineString | modo · linea · color | gtfs_lineas_geom | 57 |
| bubi.geojson | Point | n nombre · b bicicletas y c anclajes (solo si F07 está integrada) · o origen (osm \| nextbike_vivo) · d distrito | bubi_estaciones + bubi_disponibilidad | 220 |
| sensores.geojson | Point | f fuente (sensor_community\|opensensemap) · id · pm25 · pm10 · t temperatura · ts · d distrito. Coordenadas redondeadas a 3 decimales (~110 m) y sin nombre de caja para no exponer viviendas | sc_sensores + osem_sensores | 233 |
| eea.geojson | Point | estacion · nombre · tipo · area · PM25 · PM10 · NO2 · O3 (último año) · anio | eea_estaciones + eea_estadisticas | 15 |
| poi.geojson | Point | c categoría · s subcategoría OSM · n nombre · d distrito | osm_poi | 16989 |

## 8. Capas de mapa externas (no almacenadas)

| capa | proveedor | uso |
|---|---|---|
| Teselas vectoriales OpenFreeMap (esquema OpenMapTiles) | OpenFreeMap · datos OSM | Mapa base oscuro y edificios 3D (render_height) |
| World Imagery | Esri | Mapa base satelital |
| HRL Imperviousness Density 2018 (exportImage) | Copernicus / EEA | Superposición ráster de suelo sellado |
| HRL Tree Cover Density 2018 (exportImage) | Copernicus / EEA | Superposición ráster de arbolado |
| Open-Meteo current | Open-Meteo | Clima en vivo en la cabecera del sitio (consulta directa del navegador) |
