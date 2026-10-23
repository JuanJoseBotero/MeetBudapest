# Cerebro Budapest

Sistema de información territorial de Budapest (23 distritos), réplica del *Cerebro Lima* para el Taller de datos de
Tópicos de Sistemas de Información. Tiene dos partes: un **lago de datos** que federa fuentes abiertas
(bronze → silver → gold) y un **sitio web** con compuerta de clave que solo lee la capa gold.

Grupo: Juan José Botero · Santiago Idárraga · Samuel Villa. Documentos de la entrega en `docs/`
(`Diccionario_de_datos_TallerDatos_Entrega2.xlsx`, `Preguntas_por_que_estos_datos_Entrega2.docx`); los IDs de fuente
F02–F18 de este README son los de la hoja «1. Fuentes» del Excel.

Todo funciona con la **biblioteca estándar de Python ≥ 3.10** y JavaScript sin dependencias propias: MapLibre GL
y las fuentes tipográficas se cargan desde CDN. No hay `pip`, `npm install` ni ninguna llave de pago.

---

## 1. Lo mínimo que cumple el sistema

| Requisito | Cómo lo cumple | Dónde verlo |
|---|---|---|
| Al menos 3 fuentes integradas que alimentan las vistas, con su script de ingesta | 12 fuentes integradas (F02–F06, F08–F14); cada una tiene su módulo `ingestar()` → bronze y `silver()` → tablas | `pipelines/fuentes/*.py`, `python -m pipelines.ejecutar` |
| Abre bien desde un teléfono | Probado a 375 × 812: el ancho de la página es igual al de la pantalla (sin desplazamiento horizontal), menú lateral plegable y panel de capas del mapa plegado por defecto | cualquier sección en el móvil |
| Cada cifra muestra a un clic su fuente (ID), vigencia y fecha de prueba | Cada tile lleva su ID (F05…) a la vista; un clic despliega fuente con enlace, vigencia, **fecha en que se probó la fuente**, estado y licencia. Gráficos y tablas lo dicen en su pie: «Fuente: F05 · BKK · probada 2026-10-22» | todas las secciones |
| Al menos una vista sobre el territorio | Gemelo 3D por distrito (coropleta, paradas, líneas, sensores, equipamientos) y atlas de los 23 distritos con coropleta | *Gemelo territorial 3D* y *Atlas* |
| Responde al menos dos preguntas de la Entrega 1 y dice cuáles quedan pendientes | Sección *Preguntas del sistema*: las 3 preguntas del Word respondidas con cifras recalculadas en cada ejecución; 3 pendientes con su motivo y lo que tendría que cambiar | *Preguntas del sistema* |
| Ningún dato de personas a la vista | Los sensores ciudadanos se publican redondeados a ~110 m y sin el nombre libre de la caja; las cifras por distrito son medianas con al menos 2 sensores; silver (ubicación exacta) no se publica | decisión de la pregunta 5 del Word |
| Datos simulados o aproximados se ven como tales | Estados visibles en cada cifra y gráfico: **proxy** (índice de vivienda de Hungría usado para Budapest), **modelo** (F14: ERA5, pronóstico y CAMS) y **bajo costo** (F11, F12: sensores ciudadanos) | *Economía*, *Ambiente* |
| Ninguna pieza depende de una llave paga ni de tarjeta | Ninguna API usada pide llave; las teselas (OpenFreeMap, Esri World Imagery) y las librerías (jsDelivr) son de acceso libre; Vercel Hobby no pide tarjeta | sección 6 |

---

## 2. Las cuatro decisiones

**Qué mostrar.** Lo que responde las preguntas de la oficina de urbanismo y de un vecino que compara distritos:
transporte y bicicleta por habitante, suelo sellado y arbolado, y calidad del aire frente a la UE y la OMS, más el
contexto de población, economía y turismo. **No mostramos** la ubicación exacta de los sensores ciudadanos ni los
nombres de las senseBoxes; tampoco el tiempo real de BKK (exige una clave personal) ni la disponibilidad de MOL Bubi
(el feed F07 no la publica y quedó como candidata). Lo que falta lo declara el sitio: *Preguntas pendientes* y
*Brechas* en *Fuentes y método*.

**Si los datos se pueden usar.** La licencia de cada fuente se copió de la página del publicador (no de la IA: ver
la bitácora #9). Once de las 12 fuentes integradas declaran licencias abiertas (ODbL, CC BY 4.0, DbCL, PDDL, Apache 2.0 o la
política de acceso libre de Copernicus y de la EEA). F08 (Helységnévtár de KSH) **no declara** licencia en el XLSX:
la usamos citando a KSH, cuyos datos HVD (F09) sí son CC BY 4.0. F07 tampoco declara y no está integrada.

**Cómo protegerlo.** Tres capas. La **compuerta** se valida en el servidor (cookie firmada con HMAC, HttpOnly, 7 días)
y la clave solo existe en variables de entorno. El **lago** vive fuera de la carpeta pública y solo se entrega por
`/api/datos` con sesión. Los **datos delicados** se minimizan: los sensores ciudadanos se publican a ~110 m y sin nombre,
y silver, con la ubicación exacta, nunca sale del repositorio. Las pruebas con terminal están en la sección 5.

**Con qué herramienta.** MapLibre GL JS para el mapa y gráficos SVG propios (`web/public/js/graficos.js`) para todo lo
demás. MapLibre quedó porque es la única de las probadas que da edificios 3D, cámara inclinada y teselas vectoriales
sin llave; los gráficos propios, porque cada uno debe llevar su estado y su procedencia. La comparación está en la
sección 3.

---

## 3. Bitácora de exploración de herramientas de visualización

MapLibre se eligió al construir el sistema para la Entrega 1. El **2026-10-22** la contrastamos con dos alternativas
sobre **los mismos datos gold** (el lago con descargas del 2026-09-29: 5 586 paradas), servidos por la misma compuerta (`/api/datos`). Los prototipos están en
`web/public/exploracion/` (`leaflet.html`, `plot.html`) y sin sesión no muestran nada. Tiempos medidos en el
navegador integrado contra el servidor local.

| | **MapLibre GL JS 4.7.1** (elegida) | **Leaflet 1.9.4** (casi elegida) | **Observable Plot 0.6.17** + d3 7 |
|---|---|---|---|
| Qué pidió para empezar | Un `<script>` y un `<link>` desde jsDelivr, un estilo base escrito a mano y una fuente de teselas (OpenFreeMap, sin llave) | Un `<script>` y un `<link>` desde jsDelivr y una fuente de teselas ráster (usamos `tile.openstreetmap.org`) | Dos `<script>` (d3 y Plot) desde jsDelivr; nada más |
| Licencia | BSD-3-Clause | BSD-2-Clause | ISC (d3: ISC) |
| Dónde quedan los datos al publicar | En nuestro servidor, detrás de la compuerta; el proveedor de teselas solo entrega el mapa base y no recibe nuestros datos | Igual: nuestro servidor; las teselas las sirve OpenStreetMap | En nuestro servidor; el SVG se genera en el navegador |
| Qué resolvió | Coropleta de 23 distritos, 5 586 paradas, líneas guiadas, edificios 3D extruidos, cámara inclinada, rásteres de Copernicus, análisis de entorno por clic | Coropleta y 5 586 paradas en canvas: 385 ms de descarga y 156 ms de dibujo; código más corto y librería más liviana | Serie de la EEA con las guías de la OMS, barras de transporte por habitante y coropleta de arbolado: 3 gráficos en 157 ms con muy poco código, con tooltips |
| Qué no resolvió | No hace gráficos; obliga a escribir el estilo base; necesita WebGL | Sin edificios 3D ni cámara inclinada; sin teselas vectoriales salvo con un plugin; la política de uso de `tile.openstreetmap.org` no admite tráfico intenso | Sin zoom, desplazamiento ni mapa base; el tema oscuro y la ficha de procedencia por cifra habría que construirlos igual |
| Por qué quedó o no | **Quedó**: la lente de densidad y el gemelo dependen del 3D y de las teselas vectoriales gratuitas | **No quedó** por el 3D. Si el gemelo fuera solo una coropleta, ganaría Leaflet por simplicidad | **No quedó**: preferimos no sumar dos dependencias para gráficos que ya resolvíamos con SVG propio. Es la alternativa si crece el número de gráficos |

**No probadas, y por qué:** Datawrapper, Power BI y Looker Studio piden crear una cuenta y subir los datos a sus
servidores, lo que choca con la compuerta; kepler.gl y Streamlit quedaron fuera por tiempo (Streamlit exige instalar
paquetes de Python). No afirmamos nada sobre ellas que no hayamos comprobado.

---

## 4. Bitácora de IA (actualizada)

Numeración de la hoja «3. Bitácora IA» del Excel de la Entrega 2 (#2–#17, la #1 es el ejemplo de la plantilla).
Las entradas #18 y #19 están solo en este README. **Errores de la IA: 7 de 18**, contando los que la IA cometió en el
código del propio sistema.

| # | IA | Encargo | Resultado | Fuentes | Qué aprendimos |
|---|---|---|---|---|---|
| 2 | Gemini | Fuentes geoespaciales sin restricciones (OSM, Geofabrik) | Correcto | F02, F03 | Overpass sirve para consultas puntuales; Geofabrik, para descargar regiones completas |
| 3 | Gemini | Fuentes oficiales de movilidad y de tiempo real | Parcial | F05, F06, F07, F15, F16 | El tiempo real de BKK exige clave y el enlace de Bubi no responde: una lista de fuentes no es una lista de datos |
| 4 | Gemini | Estadística oficial de Hungría | Correcto | F08, F09 | Las oficinas estadísticas tienen API, pero no siempre a la escala que se necesita |
| 5 | Gemini | Observación terrestre (Copernicus) | Correcto | F04 | Las capas satelitales son potentes y exigen formatos geográficos |
| 6 | Gemini | Aire y sensores ciudadanos | Parcial | F11, F12, F13 | Los sensores ciudadanos dan cobertura pero no calibración |
| 7 | Gemini | API meteorológica sin llave | Correcto | F14 | Hay APIs públicas robustas sin registro |
| 8 | Gemini | Estadística europea | Correcto | F10 | Eurostat compara con la UE bajo una misma metodología |
| 9 | Claude | Registrar la licencia de cada fuente | **Incorrecto** | F05, F06, F07, F09, F11 | 5 de 12 licencias escritas de memoria no coincidían con el publicador (primer commit, `pipelines/config.py`) |
| 10 | Claude | Feed de estaciones de MOL Bubi | **Inventado** | F18, F07 | Propuso una URL GBFS con formato creíble que devolvió 404 |
| 11 | Claude | Contar las estaciones Bubi desde OSM | **Incorrecto** | F02, F07 | Contó 228; 8 eran tiendas privadas: son 220 |
| 12 | Claude | Media anual de PM2.5 oficial 2025 | Parcial | F13 | Llamó «media» a una sola estación con cobertura suficiente |
| 13 | Claude | Suelo sellado y arbolado por distrito | **Incorrecto** | F04 | Su código colapsaba los polígonos y dejó 0 filas en la primera ejecución |
| 14 | Claude | Datos oficiales de aire de la EEA | Correcto | F13 | Encontró la API SQL de DiscoData: 813 estadísticas de 15 estaciones |
| 15 | Claude | Que el sitio abriera bien en un teléfono | **Incorrecto** | — | Su propio CSS hacía la página de 434 px en una pantalla de 375 px (subtítulos sin salto de línea); se detectó midiendo el ancho y se corrigió |
| 16 | Claude | Servidor local de desarrollo | **Incorrecto** | — | Su código dejaba sin respuesta toda petición a un archivo inexistente (curl: «HTTP 000» en vez de 404); se detectó al probar la compuerta con terminal |
| 17 | Claude | Vigencia de series trimestrales | **Incorrecto** | F10 | Al pasar trimestres a números perdió el T1: el índice de vivienda decía «2026» en vez de «2026-T1» |
| 18 | Claude | Revisar el sitio contra los mínimos de la Entrega 2 | Correcto | — | Detectó que las cifras no mostraban ID ni fecha de prueba, que las preguntas no estaban en el sitio y que el índice de vivienda era un proxy sin marcar |
| 19 | Claude | Probar alternativas de visualización con los mismos datos | Correcto | F02, F04, F05, F08, F13 | Prototipos de Leaflet y Observable Plot medidos en el navegador (sección 3) |

Lo que sacamos en limpio: la IA acierta al **buscar** (dónde están los datos) y se equivoca al **afirmar sin
comprobar** (licencias, URLs, conteos) y en el **código que escribe**. Todos sus errores se detectaron midiendo:
abriendo la página del publicador, haciendo la petición HTTP o comparando una cifra con una segunda fuente.

---

## 5. Dos reflexiones del taller

### Datos · «Representación: el mapa no es el territorio»

**¿Quién vive en Budapest y no aparece en nuestras fuentes?**

- **13 de los 23 distritos (757 596 habitantes) no tienen dato de aire ciudadano**, porque tienen menos de 2 sensores
  (F11, F12): los sensores están donde viven voluntarios que los compraron, no donde más se necesitan.
- Las tasas por habitante usan la **población residente** del Helységnévtár (F08). No están quienes llegan cada día
  desde el área metropolitana ni los visitantes: 11,7 millones de pernoctaciones en 2025 (F10).
- Las personas **sin domicilio** no figuran en ninguna fuente.

**¿Qué decisión podría tomarse mal por ese hueco?** El distrito V aparece primero en salidas de transporte por cada
1 000 residentes (877), pero tiene solo 23 508 residentes. Quien lea esa cifra podría concluir que el centro está
sobreservido y recortar líneas, cuando quienes las usan son justamente los que no están en el denominador. Por eso la
respuesta P1 del sitio lleva escrita esa limitación, el diagnóstico avisa que «Aire» falta donde no hay sensores y
las preguntas que no podemos responder se publican como pendientes. **Nuestra posición:** el hueco se declara junto a
la cifra que podría engañar, no en un anexo.

### Seguridad · «Apariencia: parecer protegido no es estar protegido»

Probamos la compuerta con terminal, como alguien de afuera (2026-10-22, servidor local; en producción se repite
cambiando la URL):

```bash
curl -s -o /dev/null -w "%{http_code}\n" "http://localhost:8080/api/datos?f=temas/demografia.json"
```

| Prueba | Resultado |
|---|---|
| Pedir un tema del lago sin sesión (`/api/datos?f=temas/demografia.json`) | 401 |
| Intentar salir de la carpeta del lago (`/api/datos?f=../.env.example`) | 401 |
| Pedir el lago o archivos del repositorio como estáticos (`/lago/…`, `/datalake/silver/budapest.sqlite`, `/.env.example`, `/servidor_local.py`) | 404 |
| Clave equivocada en `/api/entrar` | 401 |
| Buscar la clave en el código que recibe el navegador (`grep -r` en `web/public`) | no aparece |

**Lo que parece protegido sin estarlo, dicho por nosotros:**

1. La clave de **prueba** está publicada en el repositorio (`web/.env.example`). Producción no la usa por defecto
   (sin `CLAVE_ACCESO` la API responde 500), pero si alguien la configurara igual, la compuerta sería pura apariencia.
   **Regla:** la clave de producción es distinta y solo vive en las variables de entorno de Vercel.
2. No hay bloqueo por intentos fallidos, solo una espera de 0,6 s por intento. Una clave corta se puede adivinar con
   tiempo. **Regla:** clave larga.
3. La compuerta protege **nuestro lago curado**, no los datos de origen: las 12 fuentes son públicas y cualquiera
   puede reconstruir el lago con este repositorio. Es una decisión de gobierno (qué publicamos y con qué cuidado), no
   de secreto.

---

## 6. Ninguna pieza de pago

| Pieza | Acceso |
|---|---|
| APIs de datos (Overpass, KSH, Eurostat, EEA DiscoData, Sensor.Community, openSenseMap, Open-Meteo, Copernicus ImageServer, BKK GTFS, Mobility Database) | Sin llave |
| Teselas: OpenFreeMap (vectoriales) y Esri World Imagery (satélite) | Sin llave, con atribución |
| Librerías: MapLibre GL JS (jsDelivr) y fuentes de Google Fonts | Gratuitas, sin registro |
| Python | Solo biblioteca estándar: 0 paquetes instalados |
| Alojamiento: Vercel Hobby | Sin tarjeta |

---

## 7. Para la presentación en clase (con el sistema abierto)

- **¿Qué herramienta descartamos y casi elegimos?** Leaflet. Es más simple y liviana, y dibujó los mismos datos en
  156 ms, pero no tiene edificios 3D ni cámara inclinada sin plugins. Mostrar: lente *Densidad* del gemelo.
- **¿Qué decidimos no mostrar?** La ubicación exacta de los sensores ciudadanos y el nombre de las senseBoxes (pueden
  señalar una vivienda), y el tiempo real de BKK (exige atar el sistema a una clave personal). Mostrar: capa de
  sensores y *Preguntas pendientes*.
- **¿Qué tendría que cambiar para que la respuesta fuera otra?**
  - Si los sensores fueran estaciones institucionales y no de viviendas, se podrían publicar exactos.
  - Si BKK publicara el GTFS-Realtime sin registro o el grupo tuviera una clave institucional, mediríamos el servicio
    real.
  - Si el gemelo no necesitara 3D, Leaflet habría ganado.
  - Si el operador de MOL Bubi vuelve a publicar estaciones, el lago integra F07 solo, sin tocar código.

---

## 8. Estructura y uso

```
├── pipelines/                 # ETL: bronze → silver → gold → diccionario
│   ├── config.py              # territorio y registro de fuentes con su ID F del Excel
│   ├── esquema.py             # esquema de las tablas silver = fuente del diccionario
│   ├── ejecutar.py            # orquestador (CLI)
│   ├── gold.py                # temas JSON, capas GeoJSON, métricas por distrito y preguntas
│   ├── diccionario.py         # genera docs/diccionario_datos.md y catalogo/diccionario.json
│   ├── lib/                   # HTTP + linaje, SQLite, geometría, XLSX, JSON-stat
│   └── fuentes/               # un módulo por fuente
├── datalake/{bronze,silver,gold,catalogo}/
├── docs/                      # Excel y Word de la entrega + diccionario generado
└── web/
    ├── public/                # sitio estático (index.html, estilos.css, js/, exploracion/)
    ├── api/                   # funciones Vercel: /api/entrar, /api/sesion, /api/datos
    ├── lago/                  # copia privada de gold (solo con sesión)
    └── servidor_local.py      # servidor de desarrollo que replica /api/*
```

Reconstruir el lago completo (≈10 min):

```bash
python -m pipelines.ejecutar
```

Reconstruir silver y gold sin red, desde el último bronze:

```bash
python -m pipelines.ejecutar --sin-descarga
```

Refrescar solo las fuentes en vivo:

```bash
python -m pipelines.ejecutar --solo bubi,sensor_community,opensensemap,open_meteo
```

Sitio en local (http://localhost:8080; usa `web/.env` o, si no existe, la clave de prueba de `web/.env.example`):

```bash
python web/servidor_local.py
```

Despliegue en Vercel: Root Directory = `web`, sin comando de build; definir `CLAVE_ACCESO` (distinta de la de prueba)
y `SECRETO_SESION` en las variables de entorno. `vercel.json` publica `public/` y empaqueta `lago/**` solo dentro de
la función `/api/datos`. Tras cada ejecución del pipeline hay que volver a desplegar.

Una fuente caída no detiene el lago: queda como `error` en `datalake/catalogo/estado_fuentes.json`. Una fuente que
responde pero no aporta datos utilizables queda como `candidata` y no escribe en silver (hoy, F07).
