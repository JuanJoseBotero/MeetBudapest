// Secciones temáticas renderizadas desde los temas gold. Nada se escribe a mano: si un dato no está en el lago, no se muestra.
(function () {
  const $ = s => document.querySelector(s);
  const F = () => G.fmt;
  const OMS = { 'PM2.5': 5, PM10: 15, NO2: 10 };
  const MODOS = { metro: 'Metro', tranvia: 'Tranvía', trolebus: 'Trolebús', bus: 'Autobús', hev: 'HÉV (tren suburbano)', ferry: 'Barco', funicular: 'Funicular', teleferico: 'Telesilla', tren: 'Tren', otro: 'Otro' };
  const CATEG = { educacion: 'Educación', salud: 'Salud', cultura: 'Cultura', gastronomia: 'Gastronomía', seguridad: 'Seguridad', administracion: 'Administración', movilidad: 'Movilidad', turismo: 'Turismo', alojamiento: 'Alojamiento', verde: 'Verde', deporte: 'Deporte', comercio: 'Comercio' };
  const SUB = { hotel: 'Hotel', hostel: 'Hostal', guest_house: 'Casa de huéspedes', apartment: 'Apartamento', motel: 'Motel', museum: 'Museo', attraction: 'Atractivo', viewpoint: 'Mirador', gallery: 'Galería', zoo: 'Zoológico', theme_park: 'Parque temático', theatre: 'Teatro', cinema: 'Cine', arts_centre: 'Centro de artes', concert_hall: 'Sala de conciertos' };

  let LAGO;
  const fuenteDe = (j, id) => (j.fuentes || []).find(x => x.id === id) || { id, codigo: id === 'lago' ? 'Lago' : '', nombre: id };
  const nombreFuente = (j, id) => fuenteDe(j, id).nombre.replace(/\s*[·(].*$/, '');
  const urlFuente = (j, id) => fuenteDe(j, id).url;
  // «F05 · BKK · probada 2026-09-29»: así se cita una fuente en pies de gráfico y tablas
  const citaFuente = (j, id) => { const f = fuenteDe(j, id); return `${f.codigo ? f.codigo + ' · ' : ''}${nombreFuente(j, id)}${f.probada ? ' · probada ' + f.probada : ''}`; };

  function valorFmt(c) {
    const v = c.valor; if (typeof v !== 'number') return String(v);
    if (c.decimales != null) return F().n(v, c.decimales);
    if (Math.abs(v) >= 1e6) return F().k(v);
    return F().n(v, Math.abs(v) >= 100 ? 0 : 1);
  }
  function tiles(cont, j, claves) {
    if (!j || !j.cifras) return;
    (claves || Object.keys(j.cifras)).forEach(k => {
      const c = j.cifras[k]; if (!c || c.valor == null) return;
      G.tile(cont, { valor: valorFmt(c), unidad: c.unidad, etiqueta: c.etiqueta, fuente: nombreFuente(j, c.fuente), vigencia: c.vigencia, estado: c.estado, title: c.nota || '', proc: fuenteDe(j, c.fuente) });
    });
  }
  function pieFuente(c, j, id, extra) {
    const u = urlFuente(j, id);
    c.fuente(`Fuente: ${G.esc(citaFuente(j, id))}${u ? ` · <a href="${u}" target="_blank" rel="noopener">abrir</a>` : ''}${extra ? ' · ' + G.esc(extra) : ''}`);
  }
  function serieCard(cont, j, k, o) {
    const s = j && j.series && j.series[k]; if (!s || !s.puntos || !s.puntos.length) return null;
    o = o || {};
    const c = G.card(cont, o.titulo || s.etiqueta, (s.unidad || '') + ' · ' + s.vigencia, Object.assign({ estado: s.estado }, o));
    const series = s.series || [{ nombre: s.etiqueta, puntos: s.puntos }];
    if (s.tipo === 'barras' || o.barras) G.barras(c.cuerpo, s.puntos.map(p => ({ etiqueta: String(p[0]), valor: p[1], destacado: o.umbral != null && p[1] > o.umbral })), { horizontal: false, fmtV: o.fmtV });
    else G.linea(c.cuerpo, series, o);
    if (s.nota) c.nota(s.nota);
    pieFuente(c, j, s.fuente);
    return c;
  }
  function uaCard(cont, j, k, titulo) {
    const l = j && j.listas && j.listas[k]; if (!l || !l.length) return;
    const c = G.card(cont, titulo, `${l.length} indicadores · último año disponible`);
    G.tabla(c.cuerpo, [{ k: 'indicador', t: 'Indicador' }, { k: 'anio', t: 'Año' }, { k: 'valor', t: 'Valor', n: true }], l);
    c.fuente(`Fuente: ${G.esc(citaFuente(j, 'eurostat'))} · Urban Audit, ciudad HU001C · <a href="https://ec.europa.eu/eurostat/web/cities/database" target="_blank" rel="noopener">abrir</a>`);
  }
  const pctFmt = v => F().n(v, 1) + ' %';

  // ---------------------------------------------------------------- panorama
  function panorama() {
    const t = LAGO.territorio; if (!t) return;
    const c = t.cifras;
    $('#panoramaLead').innerHTML = `<b>${F().n(c.poblacion.valor)}</b> personas viven en <b>${F().n(c.superficie.valor)} km²</b> repartidos en <b>23 distritos</b> a ambos lados del Danubio. ` +
      `Este gemelo cruza estadística oficial (KSH, Eurostat), transporte programado (BKK), sensores oficiales y ciudadanos (EEA, Sensor.Community, openSenseMap), satélite (Copernicus) y cartografía abierta (OpenStreetMap). Cada cifra indica su fuente, su vigencia y si es observada, derivada, de <b>modelo</b> (Open-Meteo, CAMS), de sensores de <b>bajo costo</b> (red ciudadana) o en vivo.`;
    tiles($('#panoramaTiles'), t, ['poblacion', 'superficie', 'densidad', 'viviendas', 'edificios', 'poi']);
    const m = LAGO.movilidad, a = LAGO.ambiente;
    if (m) tiles($('#panoramaTiles'), m, ['viajes_dia']);
    if (a) tiles($('#panoramaTiles'), a, ['pm25_anual', 'anomalia']);
  }

  // ---------------------------------------------------------------- preguntas de la Entrega 1: respondidas y pendientes
  function preguntas() {
    const j = LAGO.preguntas; if (!j) return;
    const qs = j.listas.preguntas || [], resp = qs.filter(q => q.estado === 'respondida');
    $('#preguntasLead').innerHTML = `El sistema responde <b>las ${resp.length} preguntas</b> que planteamos en la primera entrega y deja <b>${qs.length - resp.length} pendientes</b>, con el motivo y lo que tendría que cambiar para responderlas. Cada respuesta se recalcula con los datos del lago en cada ejecución.`;
    const chips = q => (q.fuentes || []).map(id => { const f = fuenteDe(j, id); return `<span class="chip-fuente" title="${G.esc(f.nombre)} · probada ${G.esc(f.probada || '—')}">${G.esc(f.codigo)}</span>`; }).join('');
    $('#preguntasLista').innerHTML = qs.map(q => `<article class="card pregunta ${q.estado}">
      <header><h3>${G.esc(q.id)} · ${G.esc(q.pregunta)}</h3><span class="estado-pregunta">${q.estado === 'respondida' ? 'respondida' : 'pendiente'}</span></header>
      ${q.estado === 'respondida'
        ? `<p>${G.esc(q.respuesta)}</p><p class="nota"><b>Límites:</b> ${G.esc(q.limites)}</p>`
        : `<p><b>Por qué queda pendiente:</b> ${G.esc(q.motivo)}</p><p class="nota"><b>Qué tendría que cambiar:</b> ${G.esc(q.cambiaria)}</p>`}
      <div class="fuente">Fuentes: ${chips(q)} · <a href="${G.esc(q.seccion)}">ver la sección</a></div></article>`).join('');
  }

  // ---------------------------------------------------------------- gente
  function gente() {
    const j = LAGO.demografia; if (!j) return;
    const c = j.cifras;
    $('#genteLead').innerHTML = `Budapest concentra a <b>${F().k(c.poblacion_nuts3 && c.poblacion_nuts3.valor)}</b> habitantes, con una edad mediana de <b>${F().n(c.edad_mediana && c.edad_mediana.valor, 1)} años</b> y <b>${F().n(c.dependencia_vejez && c.dependencia_vejez.valor, 1)}</b> personas de 65+ por cada 100 en edad de trabajar. La mortalidad supera a la natalidad: el crecimiento depende de la migración interna e internacional.`;
    tiles($('#genteTiles'), j);
    const g = $('#genteGraficos');
    const pir = j.listas.piramide;
    if (pir && pir.length) {
      const cp = G.card(g, 'Pirámide de población', `HU110 · ${(j.listas.piramide_meta || [{}])[0].anio || ''}`);
      G.piramide(cp.cuerpo, pir); pieFuente(cp, j, 'ksh_hvd');
    }
    serieCard(g, j, 'poblacion', { cero: false });
    serieCard(g, j, 'edad_mediana', { cero: false, fmtV: v => F().n(v, 1) + ' años' });
    serieCard(g, j, 'dependencia', { cero: false, fmtV: pctFmt });
    serieCard(g, j, 'esperanza_vida', { cero: false, fmtV: v => F().n(v, 1) + ' años' });
    serieCard(g, j, 'natalidad_mortalidad', { fmtV: v => F().n(v, 1) + ' ‰' });
    const pd = j.listas.poblacion_distritos;
    if (pd) {
      const cd = G.card(g, 'Población por distrito', 'KSH Helységnévtár · variación a 5 años', { ancha: false });
      G.barras(cd.cuerpo, pd.map(d => ({ etiqueta: d.distrito, valor: d.poblacion })), { fmtV: v => F().n(v), scroll: true });
      pieFuente(cd, j, 'ksh');
    }
  }

  // ---------------------------------------------------------------- economía
  function economia() {
    const j = LAGO.economia; if (!j) return;
    const c = j.cifras;
    $('#economiaLead').innerHTML = `Budapest produce <b>${F().n(c.pib_hab_eur && c.pib_hab_eur.valor)} € por habitante</b> (${c.pib_hab_eur && c.pib_hab_eur.vigencia}) y tiene un desempleo de <b>${F().n(c.desempleo && c.desempleo.valor, 1)} %</b>. ` +
      `La vivienda es la presión principal: el índice de precios de Hungría multiplica por <b>${F().n((c.precio_vivienda && c.precio_vivienda.valor || 0) / 100, 1)}</b> el nivel de 2015. Eurostat no publica ese índice por región, por eso se muestra la referencia nacional.`;
    tiles($('#economiaTiles'), j);
    const g = $('#economiaGraficos');
    serieCard(g, j, 'pib_hab_eur', { fmtV: v => F().n(v) + ' €' });
    serieCard(g, j, 'precio_vivienda', { cero: false, fmtV: v => F().n(v, 1) });
    const s = j.series;
    if (s.desempleo && s.empleo) {
      const cd = G.card(g, 'Mercado laboral 20–64', '% · ' + s.empleo.vigencia);
      G.linea(cd.cuerpo, [{ nombre: 'Empleo', puntos: s.empleo.puntos }, { nombre: 'Desempleo', puntos: s.desempleo.puntos }], { fmtV: pctFmt });
      pieFuente(cd, j, 'eurostat');
    }
    serieCard(g, j, 'ingreso_disponible', { cero: false, fmtV: v => F().n(v) + ' PPS' });
    serieCard(g, j, 'riesgo_pobreza_exclusion', { fmtV: pctFmt });
    serieCard(g, j, 'educacion_terciaria', { cero: false, fmtV: pctFmt });
    const vd = j.listas.vivienda_distritos;
    if (vd) {
      const cv = G.card(g, 'Vivienda por distrito', 'KSH Helységnévtár');
      G.tabla(cv.cuerpo, [{ k: 'distrito', t: 'Distrito' }, { k: 'viviendas', t: 'Viviendas', n: true }, { k: 'hab_vivienda', t: 'Hab./viv.', n: true, fmt: v => F().n(v, 2) }, { k: 'viviendas_km2', t: 'Viv./km²', n: true }], vd);
      pieFuente(cv, j, 'ksh');
    }
    uaCard(g, j, 'urban_audit_trabajo', 'Mercado laboral de la ciudad (Urban Audit)');
  }

  // ---------------------------------------------------------------- turismo
  function turismo() {
    const j = LAGO.turismo; if (!j) return;
    const c = j.cifras;
    $('#turismoLead').innerHTML = `Los alojamientos turísticos de Budapest registraron <b>${F().k(c.pernoctaciones && c.pernoctaciones.valor)} pernoctaciones</b> en ${c.pernoctaciones && c.pernoctaciones.vigencia}; <b>${F().n(c.pct_extranjeros && c.pct_extranjeros.valor, 1)} %</b> son de visitantes no residentes y la estancia media es de <b>${F().n(c.estancia_media && c.estancia_media.valor, 2)} noches</b>. La oferta cartografiada se concentra en los distritos centrales de Pest.`;
    tiles($('#turismoTiles'), j);
    const g = $('#turismoGraficos');
    serieCard(g, j, 'pernoctaciones');
    serieCard(g, j, 'llegadas');
    const td = j.listas.turismo_distritos;
    if (td) {
      const ct = G.card(g, 'Alojamiento por distrito', 'OSM · establecimientos cartografiados');
      G.barras(ct.cuerpo, td.filter(d => d.alojamiento).map(d => ({ etiqueta: d.distrito, valor: d.alojamiento })), { fmtV: v => F().n(v), scroll: true });
      pieFuente(ct, j, 'osm_overpass');
      const cc = G.card(g, 'Cultura, turismo y gastronomía por distrito', 'OSM');
      G.tabla(cc.cuerpo, [{ k: 'distrito', t: 'Distrito' }, { k: 'cultura_turismo', t: 'Cultura y turismo', n: true }, { k: 'gastronomia', t: 'Gastronomía', n: true }, { k: 'alojamiento', t: 'Alojamiento', n: true }],
        [...td].sort((a, b) => b.cultura_turismo - a.cultura_turismo));
      pieFuente(cc, j, 'osm_overpass');
    }
    const at = j.listas.atractivos_tipos;
    if (at) {
      const ca = G.card(g, 'Tipos de atractivo', 'OSM · tourism / amenity');
      G.barras(ca.cuerpo, at.map(x => ({ etiqueta: SUB[x.subcategoria] || x.subcategoria, valor: x.n })), { fmtV: v => F().n(v) });
      pieFuente(ca, j, 'osm_overpass');
    }
    uaCard(g, j, 'urban_audit_turismo', 'Cultura y turismo de la ciudad (Urban Audit)');
  }

  // ---------------------------------------------------------------- movilidad
  function movilidad() {
    const j = LAGO.movilidad; if (!j) return;
    const c = j.cifras;
    $('#movilidadLead').innerHTML = `Un miércoles laborable, la red de BKK programa <b>${F().n(c.viajes_dia && c.viajes_dia.valor)} viajes</b> en <b>${F().n(c.lineas && c.lineas.valor)} líneas</b> que se detienen <b>${F().k(c.detenciones_dia && c.detenciones_dia.valor)} veces</b> en ${F().n(c.paradas && c.paradas.valor)} paradas. ` +
      `La oferta se mide sobre el GTFS estático (lo programado, no lo realizado): el tiempo real de BKK requiere una clave de API.`;
    tiles($('#movilidadTiles'), j);
    const g = $('#movilidadGraficos');
    const md = j.listas.modos;
    if (md) {
      const cm = G.card(g, 'Viajes programados por modo', 'día laborable de referencia');
      G.barras(cm.cuerpo, md.map(m => ({ etiqueta: `${MODOS[m.modo] || m.modo} · ${m.rutas} líneas`, valor: m.viajes })), { fmtV: v => F().n(v) });
      pieFuente(cm, j, 'bkk_gtfs');
    }
    const top = j.listas.paradas_top;
    if (top) {
      const ct = G.card(g, 'Paradas con más salidas', 'suma de andenes con el mismo nombre');
      G.barras(ct.cuerpo, top.map(p => ({ etiqueta: p.nombre, valor: p.salidas })), { fmtV: v => F().n(v), scroll: true });
      pieFuente(ct, j, 'bkk_gtfs');
    }
    const dd = j.listas.movilidad_distritos;
    if (dd) {
      const cd = G.card(g, 'Oferta de transporte por distrito', 'salidas del día de referencia', { ancha: true });
      G.tabla(cd.cuerpo, [{ k: 'distrito', t: 'Distrito' }, { k: 'paradas', t: 'Paradas', n: true }, { k: 'salidas', t: 'Salidas/día', n: true }, { k: 'salidas_1000', t: 'Salidas por 1.000 hab.', n: true },
        { k: 'guiado_pct', t: '% paradas con modo guiado', n: true, fmt: v => v == null ? '—' : F().n(v, 1) + ' %' }, { k: 'bubi', t: 'Estaciones Bubi', n: true }], dd);
      pieFuente(cd, j, 'bkk_gtfs', 'Bubi: estaciones de OSM (el feed del operador es fuente candidata)');
    }
    serieCard(g, j, 'turismos', { cero: false });
    const fe = j.listas.feeds;
    if (fe && fe.length) {
      const cf = G.card(g, 'Feeds de transporte registrados', 'Mobility Database · Budapest');
      G.tabla(cf.cuerpo, [{ k: 'mdb_id', t: 'Id' }, { k: 'tipo', t: 'Tipo', fmt: (v, f) => v + (f.entidad ? ' · ' + f.entidad : '') }, { k: 'proveedor', t: 'Proveedor' }, { k: 'estado', t: 'Estado' },
        { k: 'requiere_clave', t: 'Clave', fmt: v => v ? 'sí' : 'no' }], fe);
      pieFuente(cf, j, 'mobilitydb', 'BKK = mdb-990 (TransitFeeds tfs-42)');
    }
    uaCard(g, j, 'urban_audit_transporte', 'Transporte de la ciudad (Urban Audit)');
  }

  // ---------------------------------------------------------------- ambiente
  function ambiente() {
    const j = LAGO.ambiente; if (!j) return;
    const c = j.cifras, p = c.pm25_anual;
    const veces = p ? p.valor / OMS['PM2.5'] : null;
    $('#ambienteLead').innerHTML = p ? `La media anual de PM2.5 en las estaciones oficiales fue <b>${F().n(p.valor, 1)} µg/m³</b> en ${p.vigencia}: cumple el límite legal de la UE (25) pero es <b>${F().n(veces, 1)} veces</b> la guía de la OMS (5). ` +
      `Según el modelo de reanálisis ERA5, el clima se calienta: ${c.anomalia ? `el último año completo estuvo <b>${F().n(c.anomalia.valor, 2)} °C</b> por encima de la media 2000–2009, con` : ''} <b>${c.dias_calor ? c.dias_calor.valor : '—'} días</b> sobre 30 °C. ` +
      `Los datos de Open-Meteo y CAMS se marcan como <b>modelo</b> y los de la red ciudadana como <b>bajo costo</b>.` : '';
    tiles($('#ambienteTiles'), j);
    const g = $('#ambienteGraficos');
    serieCard(g, j, 'particulas', { refs: [{ y: 5, etiqueta: 'OMS PM2.5' }, { y: 15, etiqueta: 'OMS PM10' }], fmtV: v => F().n(v, 1) + ' µg/m³' });
    serieCard(g, j, 'no2', { refs: [{ y: 10, etiqueta: 'OMS' }], fmtV: v => F().n(v, 1) + ' µg/m³' });
    serieCard(g, j, 'pm10_dias', { umbral: 35 });
    serieCard(g, j, 'cams_pm25', { fmtV: v => F().n(v, 1) + ' µg/m³' });
    serieCard(g, j, 'temperatura_anual', { cero: false, fmtV: v => F().n(v, 2) + ' °C' });
    serieCard(g, j, 'dias_calor');
    const est = j.listas.estaciones;
    if (est) {
      const ce = G.card(g, 'Estaciones oficiales', 'última media anual disponible · µg/m³', { ancha: true });
      G.tabla(ce.cuerpo, [{ k: 'nombre', t: 'Estación' }, { k: 'tipo', t: 'Tipo' }, { k: 'area', t: 'Entorno' }, { k: 'distrito_id', t: 'Distrito', n: true },
        { k: 'PM25', t: 'PM2.5', n: true, fmt: v => F().n(v, 1) }, { k: 'PM10', t: 'PM10', n: true, fmt: v => F().n(v, 1) }, { k: 'NO2', t: 'NO₂', n: true, fmt: v => F().n(v, 1) }, { k: 'O3', t: 'O₃', n: true, fmt: v => F().n(v, 1) }, { k: 'anio', t: 'Año', n: true, fmt: v => v || '—' }],
        [...est].sort((a, b) => (b.NO2 || 0) - (a.NO2 || 0)));
      pieFuente(ce, j, 'eea');
    }
    const sd = j.listas.suelo_distritos;
    if (sd) {
      const cs = G.card(g, 'Suelo, arbolado y aire por distrito', 'Copernicus HRL 2018 · sensores ciudadanos', { ancha: true });
      G.tabla(cs.cuerpo, [{ k: 'distrito', t: 'Distrito' }, { k: 'sellado', t: 'Suelo sellado', n: true, fmt: v => v == null ? '—' : F().n(v, 1) + ' %' }, { k: 'sellado_alto', t: 'Muy sellado (≥80)', n: true, fmt: v => v == null ? '—' : F().n(v, 1) + ' %' },
        { k: 'arbolado', t: 'Cobertura arbórea', n: true, fmt: v => v == null ? '—' : F().n(v, 1) + ' %' }, { k: 'pm25_sensores', t: 'PM2.5 ciudadano (bajo costo)', n: true, fmt: v => v == null ? '—' : F().n(v, 1) }, { k: 'sensores', t: 'Sensores', n: true }], sd);
      pieFuente(cs, j, 'copernicus', 'PM2.5: Sensor.Community, sensores de bajo costo (instantánea)');
    }
    uaCard(g, j, 'urban_audit_ambiente', 'Ambiente de la ciudad (Urban Audit)');
  }

  // ---------------------------------------------------------------- fuentes y método
  function fuentes() {
    const j = LAGO.catalogo; if (!j) return;
    const fs = j.listas.fuentes || [];
    $('#fuentesLead').innerHTML = `El sitio lee exclusivamente la capa <b>gold</b> de un lago de datos en tres zonas. Las <b>${fs.length} fuentes</b> se descargan tal cual a <b>bronze</b> (con linaje sha256), se limpian y tipan en <b>silver</b> (SQLite, una tabla por entidad, cada punto con su distrito) y se publican como temas en <b>gold</b>. ` +
      `El diccionario de datos completo se genera en cada ejecución (<span class="mono">docs/diccionario_datos.md</span>).`;
    tiles($('#fuentesTiles'), j);
    if (LAGO.distritos) tiles($('#fuentesTiles'), LAGO.distritos);
    const cont = $('#fuentesCont'), g = document.createElement('div'); g.className = 'grid2'; cont.appendChild(g);
    const cf = G.card(g, 'Fuentes federadas', 'estado de la última ejecución', { ancha: true });
    G.tabla(cf.cuerpo, [
      { k: 'codigo', t: 'ID', html: v => `<b class="mono">${G.esc(v)}</b>` },
      { k: 'nombre', t: 'Fuente', html: (v, f) => `<a href="${G.esc(f.url)}" target="_blank" rel="noopener">${G.esc(v)}</a><br><small class="mono" style="color:var(--tinta-3)">${G.esc(f.organismo)}</small>` },
      { k: 'acceso', t: 'Acceso' }, { k: 'licencia', t: 'Licencia' },
      { k: 'estado', t: 'Estado', html: (v, f) => `<span class="${G.esc(v)}" title="${G.esc(f.error || '')}">${G.esc(v)}</span>` },
      { k: 'probada', t: 'Probada', fmt: v => v || '—' },
      { k: 'bronze_mb', t: 'Bronze (MB)', n: true, fmt: v => F().n(v, 2) },
      { k: 'tablas', t: 'Tablas silver', html: v => (v || []).map(t => `<span class="mono">${G.esc(t.tabla)}</span> <small>(${F().n(t.filas)})</small>`).join('<br>') },
    ], fs);
    const cz = G.card(g, 'Zonas del lago', 'datalake/');
    G.tabla(cz.cuerpo, [{ k: 'zona', t: 'Zona' }, { k: 'ruta', t: 'Ruta' }, { k: 'contenido', t: 'Contenido' }], j.listas.zonas || []);
    const cb = G.card(g, 'Brechas conocidas', 'lo que las fuentes entregadas no cubren');
    G.tabla(cb.cuerpo, [{ k: 'tema', t: 'Tema' }, { k: 'motivo', t: 'Motivo' }], j.listas.brechas || []);
    const d = LAGO.distritos;
    if (d) {
      const cm = G.card(g, 'Métricas por distrito y sus fórmulas', 'base del atlas, las correlaciones y el diagnóstico', { ancha: true });
      G.tabla(cm.cuerpo, [{ k: 'etiqueta', t: 'Métrica' }, { k: 'unidad', t: 'Unidad' }, { k: 'estado', t: 'Estado' }, { k: 'dimension', t: 'Dimensión', fmt: v => v || '—' }, { k: 'formula', t: 'Fórmula' }], d.listas.metricas);
    }
    const ct = G.card(g, 'Estados de una cifra', 'cómo leer las etiquetas');
    G.tabla(ct.cuerpo, [{ k: 'e', t: 'Estado', html: v => `<span class="estado-tag estado-${v}">${v.replace('_', ' ')}</span>` }, { k: 'd', t: 'Significado' }], [
      { e: 'observado', d: 'Publicado o medido por la fuente, sin más transformación que filtrar y tipar.' },
      { e: 'derivado', d: 'Cálculo propio (tasa, densidad, media ponderada, índice) sobre datos observados.' },
      { e: 'modelo', d: 'Salida de un modelo, no una medición: reanálisis ERA5 y pronóstico de Open-Meteo, calidad del aire CAMS.' },
      { e: 'bajo_costo', d: 'Sensores ciudadanos de bajo costo (Sensor.Community, openSenseMap), sin calibración oficial.' },
      { e: 'en_vivo', d: 'Instantánea del momento de ingesta de una fuente en tiempo real.' }]);
    const cc = G.card(g, 'Distribución de equipamientos OSM', 'categorías del sitio');
    G.barras(cc.cuerpo, (LAGO.territorio && LAGO.territorio.listas.poi_categorias || []).map(x => ({ etiqueta: CATEG[x.categoria] || x.categoria, valor: x.n })), { fmtV: v => F().n(v) });
  }

  window.SECCIONES = {
    CATEG, MODOS, SUB,
    init(L) {
      LAGO = L;
      for (const f of [panorama, preguntas, gente, economia, turismo, movilidad, ambiente, fuentes]) {
        try { f(); } catch (e) { console.error(f.name, e); }
      }
    },
  };
})();
