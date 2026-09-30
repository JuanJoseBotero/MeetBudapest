# Cerebro Budapest

Gemelo territorial privado de Budapest (23 distritos) inspirado en *Cerebro Lima*: un **lago de datos**
que federa 12 fuentes abiertas y un **sitio web** con compuerta de clave que lee solo la capa gold.

Todo funciona con la **biblioteca estándar de Python ≥ 3.10** y JavaScript sin dependencias
(MapLibre GL se carga desde CDN). No hace falta `pip`, ni entornos virtuales, ni `npm install`.

```
Entrega1/
├── pipelines/                 # ETL: bronze → silver → gold → diccionario
│   ├── config.py              # rutas, territorio (HU11/HU110/HU001C) y registro de las 12 fuentes
│   ├── esquema.py             # esquema de las 22 tablas silver = fuente del diccionario
│   ├── ejecutar.py            # orquestador (CLI)
│   ├── gold.py                # temas JSON + capas GeoJSON + métricas por distrito
│   ├── diccionario.py         # genera docs/diccionario_datos.md y catalogo/diccionario.json
│   ├── lib/                   # http+linaje, SQLite, geometría (PIP, áreas, Douglas-Peucker), XLSX, JSON-stat
│   └── fuentes/               # un módulo por fuente: ingestar() → bronze, silver(con) → tablas
├── datalake/
│   ├── bronze/<fuente>/<AAAA-MM-DD>/   # crudo e inmutable (JSON, CSV, XLSX, ZIP)
│   ├── silver/budapest.sqlite          # tablas tipadas; cada punto con su distrito_id
│   ├── gold/temas/*.json · gold/geo/*.geojson
│   └── catalogo/                       # linaje.jsonl (url, bytes, sha256), estado_fuentes.json, diccionario.json
├── docs/diccionario_datos.md  # DICCIONARIO DE DATOS (generado en cada ejecución)
└── web/
    ├── public/                # sitio estático: index.html, estilos.css, js/
    ├── api/                   # funciones Vercel: /api/entrar, /api/sesion, /api/datos
    ├── lago/                  # copia privada de gold (solo se sirve con sesión válida)
    ├── servidor_local.py      # servidor de desarrollo que replica /api/*
    └── vercel.json
```

## Fuentes

| id | Fuente | Qué aporta |
|---|---|---|
| `osm_overpass` | Overpass API (overpass-turbo) | Límites de los 23 distritos, 16 970 equipamientos en 12 categorías, conteo de edificios |
| `geofabrik` | Extracto OSM de Hungría | Versión/fecha de la réplica OSM de referencia; `.osm.pbf` opcional (`--pbf`) |
| `copernicus` | Copernicus Land HRL 2018 | Suelo sellado y cobertura arbórea por distrito (estadística zonal en el ImageServer de la EEA) + rásteres en el mapa |
| `bkk_gtfs` | BKK GTFS estático | Líneas, paradas, oferta de un miércoles laborable, trazados de metro/tranvía/trolebús/HÉV |
| `mobilitydb` | Mobility Database (tfs-42 → mdb-990) | Catálogo de feeds de Budapest y espejo del GTFS (se usó cuando BKK no respondió) |
| `bubi` | MOL Bubi (feed nextbike `bh`) | Flota del sistema; las estaciones salen de OSM porque el operador ya no las publica |
| `ksh` | KSH: API HVD + Helységnévtár | Población por edad/sexo, edad mediana, dependencia, natalidad, mortalidad, esperanza de vida; población, superficie y viviendas por distrito 2020–2025 |
| `eurostat` | API JSON-stat | PIB, empleo, desempleo, ingreso, pobreza, educación, I+D, turismo, vehículos, precios de vivienda, Urban Audit |
| `sensor_community` | Sensor.Community | PM2.5/PM10 ciudadano en vivo |
| `opensensemap` | openSenseMap | senseBoxes activas y sus últimos valores |
| `eea` | EEA AQ e-Reporting (DiscoData) | Medias anuales oficiales PM2.5/PM10/NO₂/O₃ por estación desde 1997 |
| `open_meteo` | Open-Meteo | ERA5 diario desde 2000, pronóstico horario y calidad del aire CAMS |

## Uso

```bash
python -m pipelines.ejecutar
```

Variantes:

```bash
python -m pipelines.ejecutar --solo bubi,sensor_community,opensensemap,open_meteo
```

```bash
python -m pipelines.ejecutar --sin-descarga
```

- Sin argumentos: descarga todo, construye silver/gold, copia gold a `web/lago` y regenera el diccionario (≈10 min).
- `--solo`: refresca solo las fuentes en vivo.
- `--sin-descarga`: reconstruye silver y gold desde el último bronze, sin red.
- `--pbf`: añade el `.osm.pbf` de Hungría (~350 MB) a bronze.

Una fuente caída no detiene el lago: queda marcada como `error` en `catalogo/estado_fuentes.json` y en la sección *Fuentes y método*.

### Sitio en local

```bash
python web/servidor_local.py
```

Abre http://localhost:8080. La clave se lee de `web/.env`; si no existe, se usa la clave de prueba de `web/.env.example`.

### Despliegue en Vercel

1. Importa el repositorio con **Root Directory = `web`** (framework: *Other*, sin comando de build).
2. En *Settings → Environment Variables* define `CLAVE_ACCESO` y `SECRETO_SESION` (largo y aleatorio).
3. Despliega. `vercel.json` publica `public/` y empaqueta `lago/**` dentro de la función `/api/datos`,
   así los datos nunca son públicos: solo se entregan con la cookie de sesión firmada (HMAC, HttpOnly, 7 días).

Tras cada ejecución del pipeline, vuelve a desplegar para publicar el nuevo `web/lago`.

## Secciones del sitio

Panorama con diagnóstico comparativo por distrito y prueba de sensibilidad por prioridad · Gemelo territorial 3D
(6 lentes, 10 capas, base oscura/satélite, análisis de 500 m/1 km por clic, HUD, búsqueda) · Gente · Economía y
vivienda · Turismo · Movilidad · Ambiente y clima · Correlaciones (Pearson/Spearman entre 21 métricas) ·
Atlas de los 23 distritos (índice con pesos ajustables) · Fuentes y método (catálogo, estado, brechas, fórmulas).

Cada cifra lleva fuente, vigencia y estado: **observado**, **derivado**, **modelado** o **en vivo**.

## Brechas conocidas

Las secciones *Seguridad*, *Municipio* y *Escucha social* del sitio original no tienen equivalente en las fuentes
entregadas. GTFS-RT/FUTÁR de BKK requiere clave de API, y el Urban Atlas requiere una cuenta de Copernicus.
Además, MOL Bubi ya no publica la disponibilidad por estación.
