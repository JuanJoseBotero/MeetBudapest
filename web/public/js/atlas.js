// Atlas de los 23 distritos: índice compuesto con pesos ajustables por dimensión, coropleta SVG y tabla ordenable.
(function () {
  const $ = s => document.querySelector(s);
  let FUENTES = [], PROBADO = '';
  let D = [], dims = [], metricas = [], gj = null, pesos = {}, vista = 'indice', orden = { k: 'indice', desc: true };

  function indice(d) {
    let s = 0, w = 0;
    dims.forEach(x => { const v = d['score_' + x.id], p = pesos[x.id]; if (v != null && p > 0) { s += v * p; w += p; } });
    return w ? s / w : null;
  }
  const valor = (d, k) => k === 'indice' ? indice(d) : (k.startsWith('score_') ? d[k] : d[k]);

  function etiquetaVista(k) {
    if (k === 'indice') return ['Índice compuesto', '0–100'];
    if (k.startsWith('score_')) { const x = dims.find(y => 'score_' + y.id === k); return [x.nombre, '0–100']; }
    const m = metricas.find(y => y.id === k); return [m.etiqueta, m.unidad];
  }

  function pintar() {
    const [et, un] = etiquetaVista(vista);
    if (gj) {
      const por = Object.fromEntries(D.map(d => [d.distrito_id, d]));
      G.coropleta($('#atlasMapa'), gj, f => { const d = por[f.properties.distrito_id]; return d ? valor(d, vista) : null; }, {
        unidad: un, aria: et + ' por distrito',
        tip: (f, v) => `<b>${G.esc(f.properties.romano)}. ${G.esc(f.properties.apodo)}</b><div>${G.esc(et)}: <b>${G.fmt.n(v)}</b> ${G.esc(un)}</div><div class="mono" style="color:var(--tinta-3)">clic: ver en el diagnóstico</div>`,
        onClick: f => window.DIAGNOSTICO && DIAGNOSTICO.seleccionar(f.properties.distrito_id),
      });
    }
    const filas = D.map(d => ({ ...d, indice: indice(d) }));
    filas.sort((a, b) => { const x = a[orden.k], y = b[orden.k]; if (x == null) return 1; if (y == null) return -1; return (typeof x === 'string' ? x.localeCompare(y) : x - y) * (orden.desc ? -1 : 1); });
    filas.forEach((f, i) => { f.pos = i + 1; });
    const cols = [{ k: 'pos', t: '#', n: true }, { k: 'romano', t: 'Distrito', html: (v, f) => `<b>${G.esc(v)}</b> ${G.esc(f.apodo)} <small style="color:var(--tinta-3)">${G.esc(f.lado)}</small>` },
      { k: 'indice', t: 'Índice', n: true, html: v => v == null ? '—' : `<span class="barra-h" style="width:${v * .6}px;background:${G.color(v / 100)}"></span> <b class="mono">${Math.round(v)}</b>` },
      ...dims.map(x => ({ k: 'score_' + x.id, t: x.nombre, n: true, fmt: v => v == null ? '—' : Math.round(v) })),
      { k: 'poblacion', t: 'Población', n: true }, { k: 'densidad', t: 'hab/km²', n: true }];
    const cont = $('#atlasTabla'); cont.innerHTML = '';
    const t = G.tabla(cont, cols, filas);
    const pie = document.createElement('div'); pie.className = 'fuente';
    pie.textContent = 'Fuentes de las métricas: ' + FUENTES.map(f => `${f.codigo} ${f.nombre.replace(/\s*[·(].*$/, '')}`).join(', ')
      + ` · probadas ${[...new Set(FUENTES.map(f => f.probada))].join(', ')} · cálculo del lago ${PROBADO}`;
    cont.appendChild(pie);
    t.style.maxHeight = 'none';
    t.querySelectorAll('th').forEach((th, i) => {
      const k = cols[i].k; if (k === 'pos') return; th.style.cursor = 'pointer'; th.title = 'Ordenar';
      if (orden.k === k) th.textContent += orden.desc ? ' ↓' : ' ↑';
      th.addEventListener('click', () => { orden = { k, desc: orden.k === k ? !orden.desc : true }; pintar(); });
    });
  }

  window.ATLAS = {
    async init(L) {
      const j = L.distritos; if (!j) return;
      D = j.listas.distritos; dims = j.listas.dimensiones; metricas = j.listas.metricas;
      FUENTES = (j.fuentes || []).filter(f => f.id !== 'lago'); PROBADO = j.probado;
      dims.forEach(x => { pesos[x.id] = x.id === 'ambiente' ? 0.5 : 1; });
      $('#atlasLead').innerHTML = `Índice compuesto de <b>${dims.length} dimensiones</b> construidas con <b>${metricas.filter(m => m.dimension).length} métricas</b>. Cada métrica se normaliza min–max 0–100 entre los 23 distritos (invertida cuando menos es mejor, como el suelo sellado o el PM2.5); cada dimensión promedia sus métricas y el índice pondera las dimensiones con tus pesos. ` +
        `Haz clic en un distrito del mapa para llevarlo al diagnóstico. <b>No es un ranking oficial</b>: es una herramienta para ver cómo cambian las conclusiones al cambiar lo que se valora.`;
      $('#atlasPesos').innerHTML = dims.map(x => `<label>${G.esc(x.nombre)}<output id="po_${x.id}">${pesos[x.id]}</output><input type="range" min="0" max="3" step="0.5" value="${pesos[x.id]}" data-d="${x.id}" title="${G.esc(x.descripcion)}"></label>`).join('');
      $('#atlasPesos').addEventListener('input', e => { const d = e.target.dataset.d; if (!d) return; pesos[d] = +e.target.value; $('#po_' + d).textContent = e.target.value; pintar(); });
      const opciones = [['indice', 'Índice'], ...dims.map(x => ['score_' + x.id, x.nombre]), ['densidad', 'Densidad'], ['salidas_1000', 'Transporte/1.000 hab'], ['arbolado', 'Arbolado'], ['sellado', 'Suelo sellado']];
      $('#atlasMetrica').innerHTML = opciones.map(([k, t]) => `<button type="button" class="chip${k === vista ? ' on' : ''}" data-k="${k}">${G.esc(t)}</button>`).join('');
      $('#atlasMetrica').addEventListener('click', e => {
        const b = e.target.closest('[data-k]'); if (!b) return; vista = b.dataset.k;
        $('#atlasMetrica').querySelectorAll('.chip').forEach(c => c.classList.toggle('on', c === b)); pintar();
      });
      pintar();
      try { gj = await cargarGeo('distritos'); pintar(); } catch (e) { console.error('atlas geo', e); }
    },
  };
})();
