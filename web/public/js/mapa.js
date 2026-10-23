// Gemelo territorial 3D (MapLibre): lentes temáticas, capas del lago, bases oscura/satélite, rásteres Copernicus,
// análisis de entorno por clic (500 m / 1 km), HUD y búsqueda de lugares.
(function () {
  const $ = s => document.querySelector(s);
  const CENTRO = [19.0402, 47.4979];
  const CAT_COLOR = { educacion: '#9b8cf0', salud: '#e5664f', cultura: '#e56f9c', turismo: '#e8a33d', alojamiento: '#f3c77a', gastronomia: '#c9c35a', comercio: '#3fb8c9', verde: '#6fcf6a', deporte: '#58a6ff', seguridad: '#ff8a65', administracion: '#a9b7c4', movilidad: '#7fdbca' };
  const MODO_ANCHO = { metro: 3.2, hev: 2.6, tranvia: 2.2, trolebus: 1.6, ferry: 1.6, funicular: 2, teleferico: 2 };
  const COP = 'https://image.discomap.eea.europa.eu/arcgis/rest/services/GioLandPublic/{s}/ImageServer/exportImage?bbox={bbox-epsg-3857}&bboxSR=3857&imageSR=3857&size=256,256&format=png&transparent=true&f=image';

  // capa -> definición para el panel
  const CAPAS = {
    distritos: { t: 'Distritos (coropleta) · F02 F08', c: '#3fb8c9' },
    lineas: { t: 'Líneas guiadas (GTFS) · F05', c: '#e8a33d' },
    paradas: { t: 'Paradas por salidas/día · F05', c: '#f3c77a' },
    bubi: { t: 'Estaciones MOL Bubi · F02', c: '#6fcf6a' },
    poi: { t: 'Equipamientos OSM · F02', c: '#9b8cf0' },
    sensores: { t: 'Sensores PM2.5 (bajo costo) · F11 F12', c: '#c9c35a' },
    eea: { t: 'Estaciones oficiales EEA · F13', c: '#e5664f' },
    edificios: { t: 'Edificios 3D (OpenFreeMap, OSM)', c: '#a9b7c4' },
    sellado: { t: 'Suelo sellado · F04 (ráster)', c: '#e56f9c' },
    arbolado: { t: 'Cobertura arbórea · F04 (ráster)', c: '#6fcf6a' },
  };
  const LENTES = {
    cruce: { t: '◎ Cruce urbano', metrica: 'indice', capas: ['distritos', 'lineas', 'edificios'], pitch: 45, poi: null, ley: 'Índice de equilibrio (promedio de las 5 dimensiones, 0–100)' },
    movilidad: { t: '⇄ Movilidad', metrica: 'score_movilidad', capas: ['distritos', 'lineas', 'paradas', 'bubi'], pitch: 30, poi: null, ley: 'Puntaje de movilidad 0–100' },
    densidad: { t: '▥ Densidad', metrica: 'densidad', capas: ['distritos', 'edificios'], pitch: 58, poi: null, ley: 'Habitantes por km² (KSH)' },
    servicios: { t: '✚ Servicios', metrica: 'score_servicios', capas: ['distritos', 'poi'], pitch: 20, poi: ['educacion', 'salud', 'cultura', 'comercio', 'administracion'], ley: 'Puntaje de servicios 0–100' },
    verde: { t: '❋ Verde', metrica: 'arbolado', capas: ['distritos', 'arbolado', 'poi'], pitch: 20, poi: ['verde', 'deporte'], ley: 'Cobertura arbórea media % (Copernicus 2018)' },
    aire: { t: '≋ Aire', metrica: 'sellado', capas: ['distritos', 'sensores', 'eea'], pitch: 0, poi: null, ley: 'Suelo sellado % (Copernicus 2018)' },
  };
  let map, datos = {}, lente = 'cruce', activas = new Set(), base = 'oscuro', lugares = [], rango = [0, 1];
  let PROBADAS = '';  // fechas de prueba de las fuentes del mapa, leídas del catálogo del lago

  const R = 6371008.8, rad = x => x * Math.PI / 180;
  const dist = (a, b) => { const dl = rad(b[1] - a[1]), dn = rad(b[0] - a[0]), h = Math.sin(dl / 2) ** 2 + Math.cos(rad(a[1])) * Math.cos(rad(b[1])) * Math.sin(dn / 2) ** 2; return 2 * R * Math.asin(Math.sqrt(h)); };
  function circulo(c, m) {
    const pts = []; for (let i = 0; i <= 64; i++) { const t = i / 64 * 2 * Math.PI; pts.push([c[0] + m * Math.cos(t) / (111320 * Math.cos(rad(c[1]))), c[1] + m * Math.sin(t) / 110540]); }
    return { type: 'Feature', geometry: { type: 'Polygon', coordinates: [pts] }, properties: { m } };
  }
  function dentro(p, gj) { // punto en (Multi)Polygon
    const polis = gj.type === 'Polygon' ? [gj.coordinates] : gj.coordinates;
    const enAnillo = a => { let d = false; for (let i = 0, j = a.length - 1; i < a.length; j = i++) { if ((a[i][1] > p[1]) !== (a[j][1] > p[1]) && p[0] < (a[j][0] - a[i][0]) * (p[1] - a[i][1]) / (a[j][1] - a[i][1]) + a[i][0]) d = !d; } return d; };
    return polis.some(poli => enAnillo(poli[0]) && !poli.slice(1).some(enAnillo));
  }

  // ---------------------------------------------------------------- estilo base propio (OpenFreeMap / OpenMapTiles)
  function estilo() {
    const vis = v => ({ visibility: v ? 'visible' : 'none' });
    return {
      version: 8,
      glyphs: 'https://tiles.openfreemap.org/fonts/{fontstack}/{range}.pbf',
      sources: {
        ofm: { type: 'vector', url: 'https://tiles.openfreemap.org/planet', attribution: '© OpenFreeMap · © OpenStreetMap' },
        esri: { type: 'raster', tiles: ['https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'], tileSize: 256, maxzoom: 19, attribution: 'Imágenes © Esri' },
        sellado: { type: 'raster', tiles: [COP.replace('{s}', 'HRL_ImperviousnessDensity_2018')], tileSize: 256, attribution: 'Copernicus HRL © EEA' },
        arbolado: { type: 'raster', tiles: [COP.replace('{s}', 'HRL_TreeCoverDensity_2018')], tileSize: 256, attribution: 'Copernicus HRL © EEA' },
      },
      layers: [
        { id: 'fondo', type: 'background', paint: { 'background-color': '#0a1016' } },
        { id: 'satelite', type: 'raster', source: 'esri', layout: vis(false), paint: { 'raster-saturation': -0.25, 'raster-brightness-max': 0.85 } },
        { id: 'cobertura', type: 'fill', source: 'ofm', 'source-layer': 'landcover', paint: { 'fill-color': '#0f1f18', 'fill-opacity': 0.7 } },
        { id: 'parques', type: 'fill', source: 'ofm', 'source-layer': 'park', paint: { 'fill-color': '#12281d', 'fill-opacity': 0.8 } },
        { id: 'agua', type: 'fill', source: 'ofm', 'source-layer': 'water', paint: { 'fill-color': '#0c2433' } },
        { id: 'sellado', type: 'raster', source: 'sellado', layout: vis(false), paint: { 'raster-opacity': 0.7 } },
        { id: 'arbolado', type: 'raster', source: 'arbolado', layout: vis(false), paint: { 'raster-opacity': 0.75 } },
        { id: 'vias-menores', type: 'line', source: 'ofm', 'source-layer': 'transportation', minzoom: 12, filter: ['in', ['get', 'class'], ['literal', ['minor', 'service', 'tertiary']]], paint: { 'line-color': '#1c2a36', 'line-width': ['interpolate', ['linear'], ['zoom'], 12, 0.4, 16, 2.5] } },
        { id: 'vias', type: 'line', source: 'ofm', 'source-layer': 'transportation', filter: ['in', ['get', 'class'], ['literal', ['motorway', 'trunk', 'primary', 'secondary']]], paint: { 'line-color': '#2a3a48', 'line-width': ['interpolate', ['linear'], ['zoom'], 10, 0.6, 16, 5] } },
        { id: 'edificios', type: 'fill-extrusion', source: 'ofm', 'source-layer': 'building', minzoom: 12.5, paint: {
          'fill-extrusion-color': ['interpolate', ['linear'], ['coalesce', ['get', 'render_height'], 6], 0, '#1d2b38', 20, '#2b4150', 45, '#3f6070', 90, '#6d8f9a'],
          'fill-extrusion-height': ['coalesce', ['get', 'render_height'], 6], 'fill-extrusion-base': ['coalesce', ['get', 'render_min_height'], 0], 'fill-extrusion-opacity': 0.85 } },
        { id: 'nombres-agua', type: 'symbol', source: 'ofm', 'source-layer': 'water_name', layout: { 'text-field': ['get', 'name'], 'text-font': ['Noto Sans Italic'], 'text-size': 12 }, paint: { 'text-color': '#4d88a3' } },
        { id: 'lugares', type: 'symbol', source: 'ofm', 'source-layer': 'place', minzoom: 12, filter: ['in', ['get', 'class'], ['literal', ['suburb', 'quarter', 'neighbourhood']]],
          layout: { 'text-field': ['get', 'name'], 'text-font': ['Noto Sans Regular'], 'text-size': 11, 'text-transform': 'uppercase', 'text-letter-spacing': 0.08 }, paint: { 'text-color': '#6f8091', 'text-halo-color': '#0a1016', 'text-halo-width': 1.2 } },
      ],
    };
  }

  // ---------------------------------------------------------------- capas del lago
  function rampa(key) {
    const vals = datos.distritos.features.map(f => f.properties[key]).filter(v => v != null);
    const lo = Math.min(...vals), hi = Math.max(...vals); rango = [lo, hi];
    const stops = G.RAMPA.flatMap((c, i) => [lo + (hi - lo) * i / (G.RAMPA.length - 1), c]);
    return ['case', ['==', ['get', key], null], '#1b2632', ['interpolate', ['linear'], ['get', key], ...stops]];
  }

  function agregarCapas() {
    const antes = 'nombres-agua';
    map.addSource('distritos', { type: 'geojson', data: datos.distritos });
    map.addLayer({ id: 'distritos', type: 'fill', source: 'distritos', paint: { 'fill-color': rampa('indice'), 'fill-opacity': 0.42 } }, 'vias-menores');
    map.addLayer({ id: 'distritos-borde', type: 'line', source: 'distritos', paint: { 'line-color': '#e6edf3', 'line-opacity': 0.35, 'line-width': 1 } }, antes);
    map.addSource('distritos-etq', { type: 'geojson', data: { type: 'FeatureCollection', features: datos.distritos.features.map(f => ({ type: 'Feature', geometry: { type: 'Point', coordinates: f.properties.centro }, properties: { t: f.properties.romano } })) } });
    map.addLayer({ id: 'distritos-etq', type: 'symbol', source: 'distritos-etq', maxzoom: 14, layout: { 'text-field': ['get', 't'], 'text-font': ['Noto Sans Bold'], 'text-size': 15 }, paint: { 'text-color': '#e6edf3', 'text-halo-color': '#0a1016', 'text-halo-width': 2 } });
    if (datos.lineas) {
      map.addSource('lineas', { type: 'geojson', data: datos.lineas });
      map.addLayer({ id: 'lineas', type: 'line', source: 'lineas', layout: { 'line-cap': 'round', 'line-join': 'round' }, paint: { 'line-color': ['get', 'color'], 'line-width': ['match', ['get', 'modo'], ...Object.entries(MODO_ANCHO).flat(), 1.4], 'line-opacity': 0.9 } }, antes);
    }
    if (datos.paradas) {
      map.addSource('paradas', { type: 'geojson', data: datos.paradas });
      map.addLayer({ id: 'paradas', type: 'circle', source: 'paradas', paint: {
        'circle-radius': ['interpolate', ['linear'], ['zoom'], 10, ['interpolate', ['linear'], ['get', 's'], 0, 0.8, 2000, 5], 15, ['interpolate', ['linear'], ['get', 's'], 0, 2.5, 2000, 12]],
        'circle-color': ['interpolate', ['linear'], ['get', 's'], 0, '#5b6b78', 200, '#3fb8c9', 800, '#f3c77a', 2000, '#e8a33d'], 'circle-opacity': 0.85, 'circle-stroke-color': '#0a1016', 'circle-stroke-width': 0.5 } });
    }
    const puntos = (id, paint) => { if (!datos[id]) return; map.addSource(id, { type: 'geojson', data: datos[id] }); map.addLayer({ id, type: 'circle', source: id, paint }); };
    puntos('bubi', { 'circle-radius': ['interpolate', ['linear'], ['zoom'], 10, 2.5, 15, 7], 'circle-color': '#6fcf6a', 'circle-stroke-color': '#0a1016', 'circle-stroke-width': 1 });
    puntos('poi', { 'circle-radius': ['interpolate', ['linear'], ['zoom'], 10, 1.6, 16, 6], 'circle-color': ['match', ['get', 'c'], ...Object.entries(CAT_COLOR).flat(), '#a9b7c4'], 'circle-opacity': 0.9, 'circle-stroke-color': '#0a1016', 'circle-stroke-width': 0.4 });
    const pmColor = k => ['case', ['==', ['get', k], null], '#5b6b78', ['step', ['get', k], '#3cbf7a', 5, '#c9c35a', 15, '#e8a33d', 25, '#e5664f', 50, '#b0306a']];
    puntos('sensores', { 'circle-radius': ['interpolate', ['linear'], ['zoom'], 10, 4, 15, 9], 'circle-color': pmColor('pm25'), 'circle-stroke-color': ['match', ['get', 'f'], 'opensensemap', '#e6edf3', '#0a1016'], 'circle-stroke-width': 1.2 });
    puntos('eea', { 'circle-radius': ['interpolate', ['linear'], ['zoom'], 10, 7, 15, 13], 'circle-color': pmColor('PM25'), 'circle-stroke-color': '#e6edf3', 'circle-stroke-width': 2 });
    map.addSource('radio', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } });
    map.addLayer({ id: 'radio', type: 'line', source: 'radio', paint: { 'line-color': '#e8a33d', 'line-width': 1.5, 'line-dasharray': [3, 2] } });
    map.addLayer({ id: 'radio-fill', type: 'fill', source: 'radio', filter: ['==', ['get', 'm'], 500], paint: { 'fill-color': '#e8a33d', 'fill-opacity': 0.07 } });

    ['paradas', 'bubi', 'poi', 'sensores', 'eea', 'lineas'].forEach(id => {
      if (!map.getLayer(id)) return;
      map.on('mouseenter', id, () => { map.getCanvas().style.cursor = 'pointer'; });
      map.on('mouseleave', id, () => { map.getCanvas().style.cursor = ''; });
    });
  }

  // ---------------------------------------------------------------- lentes, capas y bases
  function aplicarLente(k, volar) {
    lente = k; const L = LENTES[k];
    activas = new Set(L.capas);
    $('#lentes').querySelectorAll('button').forEach(b => b.classList.toggle('on', b.dataset.l === k));
    if (map.getLayer('distritos')) map.setPaintProperty('distritos', 'fill-color', rampa(L.metrica));
    if (map.getLayer('poi')) map.setFilter('poi', L.poi ? ['in', ['get', 'c'], ['literal', L.poi]] : null);
    sincronizar(); leyenda();
    if (volar) map.easeTo({ pitch: L.pitch, duration: 900 });
  }
  function sincronizar() {
    const capa = { distritos: ['distritos', 'distritos-borde', 'distritos-etq'], lineas: ['lineas'], paradas: ['paradas'], bubi: ['bubi'], poi: ['poi'], sensores: ['sensores'], eea: ['eea'], edificios: ['edificios'], sellado: ['sellado'], arbolado: ['arbolado'] };
    for (const [k, ids] of Object.entries(capa)) ids.forEach(id => map.getLayer(id) && map.setLayoutProperty(id, 'visibility', activas.has(k) ? 'visible' : 'none'));
    $('#capas').querySelectorAll('input').forEach(i => { i.checked = activas.has(i.value); });
  }
  function cambiarBase(b) {
    base = b; const sat = b === 'satelite';
    map.setLayoutProperty('satelite', 'visibility', sat ? 'visible' : 'none');
    ['cobertura', 'parques', 'agua'].forEach(id => map.setLayoutProperty(id, 'visibility', sat ? 'none' : 'visible'));
    if (map.getLayer('distritos')) map.setPaintProperty('distritos', 'fill-opacity', sat ? 0.25 : 0.42);
  }
  function leyenda() {
    const L = LENTES[lente], f = v => G.fmt.n(v, Math.abs(v) < 10 ? 1 : 0);
    let h = `<b>${G.esc(L.ley)}</b><div class="rampa" style="background:linear-gradient(90deg,${G.RAMPA.join(',')})"></div><div class="extremos"><span>${f(rango[0])}</span><span>${f(rango[1])}</span></div>`;
    if (activas.has('paradas')) h += `<div style="margin-top:8px">● Paradas: tamaño y color = salidas del día laborable</div>`;
    if (activas.has('sensores') || activas.has('eea')) h += `<div style="margin-top:8px">PM2.5 µg/m³: <span style="color:#3cbf7a">●</span>&lt;5 <span style="color:#c9c35a">●</span>&lt;15 <span style="color:#e8a33d">●</span>&lt;25 <span style="color:#e5664f">●</span>&lt;50 <span style="color:#b0306a">●</span>50+<br><small>Aro blanco grueso: estación oficial EEA (media anual). Puntos pequeños: sensores ciudadanos de bajo costo (instantánea).</small></div>`;
    if (activas.has('poi') && L.poi) h += `<div style="margin-top:8px">${L.poi.map(c => `<span style="color:${CAT_COLOR[c]}">●</span> ${G.esc(SECCIONES.CATEG[c] || c)}`).join(' ')}</div>`;
    if (activas.has('sellado') || activas.has('arbolado')) h += `<div style="margin-top:8px"><small>Ráster Copernicus HRL 2018 (10 m) servido por la EEA</small></div>`;
    $('#leyenda').innerHTML = h;
  }

  // ---------------------------------------------------------------- análisis de entorno
  function analizar(ll, feat) {
    const p = [ll.lng, ll.lat];
    map.getSource('radio').setData({ type: 'FeatureCollection', features: [circulo(p, 500), circulo(p, 1000)] });
    const cerca = (gj, m) => (gj ? gj.features : []).filter(f => dist(p, f.geometry.coordinates) <= m);
    const par5 = cerca(datos.paradas, 500), par10 = cerca(datos.paradas, 1000);
    const sal5 = par5.reduce((a, f) => a + (f.properties.s || 0), 0);
    const modos = [...new Set(par5.flatMap(f => (f.properties.m || '').split(',').filter(Boolean)))];
    const poi5 = cerca(datos.poi, 500), porCat = {};
    poi5.forEach(f => { porCat[f.properties.c] = (porCat[f.properties.c] || 0) + 1; });
    const bubi5 = cerca(datos.bubi, 500).length;
    const masCercano = (gj, filtro) => { let best = null, d = Infinity; (gj ? gj.features : []).forEach(f => { if (filtro && !filtro(f)) return; const x = dist(p, f.geometry.coordinates); if (x < d) { d = x; best = f; } }); return best ? [best, d] : [null, null]; };
    const [sen, dsen] = masCercano(datos.sensores, f => f.properties.pm25 != null);
    const [est, dest] = masCercano(datos.eea, f => f.properties.PM25 != null || f.properties.NO2 != null);
    const dis = datos.distritos.features.find(f => dentro(p, f.geometry));
    const dp = dis && dis.properties;
    const cab = feat ? descripcion(feat) : '';
    const n = G.fmt.n;
    $('#ficha').innerHTML = `<button class="cerrar" type="button" aria-label="Cerrar">×</button>
      ${cab}<h4>${dp ? `${G.esc(dp.romano)}. ${G.esc(dp.apodo)}` : 'Fuera de Budapest'}</h4>
      <div class="mono" style="color:var(--tinta-3);font-size:11px">${ll.lat.toFixed(5)}, ${ll.lng.toFixed(5)} · radio 500 m</div>
      <dl>
        <dt>Paradas (500 m · 1 km)</dt><dd>${par5.length} · ${par10.length}</dd>
        <dt>Salidas/día en 500 m</dt><dd>${n(sal5)}</dd>
        <dt>Modos</dt><dd>${modos.map(m => SECCIONES.MODOS[m] || m).join(', ') || '—'}</dd>
        <dt>Estaciones Bubi</dt><dd>${bubi5}</dd>
        ${Object.entries(porCat).sort((a, b) => b[1] - a[1]).slice(0, 6).map(([c, k]) => `<dt><span style="color:${CAT_COLOR[c]}">●</span> ${G.esc(SECCIONES.CATEG[c] || c)}</dt><dd>${k}</dd>`).join('')}
        <dt>PM2.5 sensor ciudadano (bajo costo)</dt><dd>${sen ? `${n(sen.properties.pm25, 1)} µg/m³ <small>(${n(dsen / 1000, 1)} km)</small>` : '—'}</dd>
        <dt>Estación oficial más cercana</dt><dd>${est ? `${G.esc(est.properties.nombre)} <small>(${n(dest / 1000, 1)} km)</small>` : '—'}</dd>
        ${est ? `<dt>NO₂ · PM2.5 anual</dt><dd>${n(est.properties.NO2, 1)} · ${n(est.properties.PM25, 1)} <small>${est.properties.anio || ''}</small></dd>` : ''}
        ${dp ? `<dt>Densidad del distrito</dt><dd>${n(dp.densidad)} hab/km²</dd><dt>Arbolado · sellado</dt><dd>${n(dp.arbolado, 1)} % · ${n(dp.sellado, 1)} %</dd>` : ''}
      </dl>
      <div class="src">F05 GTFS BKK (miércoles ref.) · F02 OSM (equipamientos, Bubi, distritos) · F08 KSH (población) · F11/F12 sensores de bajo costo (instantánea) · F13 EEA (media anual) · F04 Copernicus 2018 · probadas ${G.esc(PROBADAS)}</div>
      ${dp ? `<button class="ghost" type="button" id="fichaDiag" style="margin-top:10px;width:100%">Ver ${G.esc(dp.romano)} en el diagnóstico</button>` : ''}`;
    $('#ficha').hidden = false;
    $('#ficha .cerrar').onclick = () => { $('#ficha').hidden = true; map.getSource('radio').setData({ type: 'FeatureCollection', features: [] }); };
    const bd = $('#fichaDiag'); if (bd) bd.onclick = () => DIAGNOSTICO.seleccionar(dp.distrito_id);
  }
  function descripcion(f) {
    const p = f.properties, n = G.fmt.n, l = f.layer.id;
    const t = { paradas: `Parada <b>${G.esc(p.n)}</b> · ${n(p.s)} salidas/día · ${p.r} rutas`, bubi: `MOL Bubi <b>${G.esc(p.n || 'estación')}</b>${p.b != null ? ` · ${p.b} bicis` : ''}`,
      poi: `<b>${G.esc(p.n || SECCIONES.SUB[p.s] || p.s)}</b> · ${G.esc(SECCIONES.CATEG[p.c] || p.c)}`, sensores: `Sensor ${G.esc(p.f)} ${G.esc(p.id)} · PM2.5 <b>${n(p.pm25, 1)}</b> µg/m³`,
      eea: `Estación EEA <b>${G.esc(p.nombre)}</b> · ${G.esc(p.tipo)}`, lineas: `Línea <b>${G.esc(p.linea)}</b> · ${G.esc(SECCIONES.MODOS[p.modo] || p.modo)}` }[l];
    return t ? `<div style="border-bottom:1px solid var(--borde);padding-bottom:8px;margin-bottom:8px">${t}</div>` : '';
  }

  // ---------------------------------------------------------------- HUD, panel y búsqueda
  function hud() {
    const c = map.getCenter(), z = map.getZoom(), m = 40075016 * Math.cos(rad(c.lat)) / Math.pow(2, z + 8) * 100;
    $('#hud').innerHTML = `<span>LAT <b>${c.lat.toFixed(4)}</b></span><span>LON <b>${c.lng.toFixed(4)}</b></span><span>ZOOM <b>${z.toFixed(1)}</b></span><span>RUMBO <b>${Math.round(map.getBearing())}°</b></span><span>INCL. <b>${Math.round(map.getPitch())}°</b></span><span>100 px ≈ <b>${m >= 1000 ? G.fmt.n(m / 1000, 1) + ' km' : Math.round(m) + ' m'}</b></span>`;
  }
  function panel() {
    // En el teléfono el panel empieza plegado para no tapar el mapa; se abre con un toque.
    const btn = $('#plegarPanel'), cuerpo = $('#mapaPanelCuerpo');
    const fijar = abierto => { cuerpo.hidden = !abierto; btn.setAttribute('aria-expanded', String(abierto)); btn.classList.toggle('abierto', abierto); };
    fijar(!matchMedia('(max-width: 960px)').matches);
    btn.addEventListener('click', () => fijar(cuerpo.hidden));
    $('#lentes').innerHTML = Object.entries(LENTES).map(([k, l]) => `<button type="button" data-l="${k}">${l.t}</button>`).join('');
    $('#lentes').addEventListener('click', e => { const b = e.target.closest('[data-l]'); if (b) aplicarLente(b.dataset.l, true); });
    $('#capas').innerHTML = Object.entries(CAPAS).map(([k, c]) => `<label><input type="checkbox" value="${k}"><i style="background:${c.c}"></i>${G.esc(c.t)}</label>`).join('');
    $('#capas').addEventListener('change', e => { const v = e.target.value; e.target.checked ? activas.add(v) : activas.delete(v); sincronizar(); leyenda(); });
    $('#bases').innerHTML = [['oscuro', 'Oscuro (OSM)'], ['satelite', 'Satélite (Esri)']].map(([k, t]) => `<label><input type="radio" name="base" value="${k}" ${k === base ? 'checked' : ''}>${t}</label>`).join('');
    $('#bases').addEventListener('change', e => cambiarBase(e.target.value));
    $('#mapaBuscar').addEventListener('input', e => {
      const q = e.target.value.toLowerCase().normalize('NFD').replace(/\p{Diacritic}/gu, '');
      const r = q.length < 2 ? [] : lugares.filter(l => l.clave.includes(q)).slice(0, 8);
      $('#mapaResultados').innerHTML = r.map((l, i) => `<button type="button" data-i="${i}">${G.esc(l.nombre)}<small>${G.esc(l.tipo)}</small></button>`).join('');
      $('#mapaResultados').querySelectorAll('button').forEach((b, i) => b.onclick = () => irA(r[i]));
    });
  }
  function indexarLugares() {
    const norm = s => (s || '').toLowerCase().normalize('NFD').replace(/\p{Diacritic}/gu, '');
    const vistos = new Set();
    lugares = datos.distritos.features.map(f => ({ nombre: `${f.properties.romano}. kerület · ${f.properties.apodo}`, tipo: 'distrito', c: f.properties.centro, z: 13 }));
    (datos.paradas ? datos.paradas.features : []).filter(f => f.properties.s >= 150).forEach(f => { if (!vistos.has(f.properties.n)) { vistos.add(f.properties.n); lugares.push({ nombre: f.properties.n, tipo: 'parada BKK', c: f.geometry.coordinates, z: 16 }); } });
    (datos.poi ? datos.poi.features : []).filter(f => f.properties.n && ['turismo', 'cultura', 'salud', 'educacion', 'verde'].includes(f.properties.c)).forEach(f => lugares.push({ nombre: f.properties.n, tipo: SECCIONES.CATEG[f.properties.c] || f.properties.c, c: f.geometry.coordinates, z: 16.5 }));
    lugares.forEach(l => { l.clave = norm(l.nombre); });
  }
  function irA(l) { map.flyTo({ center: l.c, zoom: l.z || 15, pitch: 45, duration: 1400 }); analizar({ lng: l.c[0], lat: l.c[1] }); }

  window.MAPA = {
    lugares: () => lugares, irA,
    async init(L) {
      const usadas = ['F02', 'F04', 'F05', 'F08', 'F11', 'F12', 'F13'];
      PROBADAS = [...new Set(((L.catalogo && L.catalogo.listas.fuentes) || []).filter(f => usadas.includes(f.codigo)).map(f => f.probada).filter(Boolean))].sort().join(', ') || '—';
      if (!window.maplibregl) { $('#mapaWrap').innerHTML = '<p class="notas" style="padding:20px">No se pudo cargar MapLibre GL.</p>'; return; }
      panel();
      map = new maplibregl.Map({ container: 'mapa', style: estilo(), center: CENTRO, zoom: 11.3, pitch: 45, bearing: -12, maxPitch: 75, attributionControl: { compact: true }, hash: false });
      map.addControl(new maplibregl.NavigationControl({ visualizePitch: true }), 'bottom-right');
      map.on('move', hud);
      const nombres = ['distritos', 'lineas', 'paradas', 'bubi', 'poi', 'sensores', 'eea'];
      const res = await Promise.allSettled(nombres.map(n => cargarGeo(n)));
      res.forEach((r, i) => { if (r.status === 'fulfilled') datos[nombres[i]] = r.value; else console.warn('capa', nombres[i], r.reason); });
      if (!datos.distritos) return;
      const dims = (L.distritos && L.distritos.listas.dimensiones || []).map(d => 'score_' + d.id);
      datos.distritos.features.forEach(f => { const v = dims.map(k => f.properties[k]).filter(x => x != null); f.properties.indice = v.length ? v.reduce((a, b) => a + b, 0) / v.length : null; });
      indexarLugares();
      const listo = () => {
        agregarCapas(); aplicarLente('cruce', false); hud();
        map.on('click', e => {
          const capas = ['paradas', 'bubi', 'eea', 'sensores', 'poi', 'lineas'].filter(id => map.getLayer(id) && map.getLayoutProperty(id, 'visibility') !== 'none');
          const f = map.queryRenderedFeatures(e.point, { layers: capas })[0];
          analizar(e.lngLat, f);
        });
      };
      map.loaded() ? listo() : map.on('load', listo);
    },
  };
})();
