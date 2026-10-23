// Explorador de asociaciones entre las métricas de los 23 distritos: dispersión con valores originales,
// Pearson y Spearman sobre casos completos, recta de mínimos cuadrados y pares más asociados. Sin lenguaje causal.
(function () {
  const $ = s => document.querySelector(s);
  let D = [], M = {}, pares = [], FU = {};
  const cod = id => FU[id] ? `${FU[id].codigo} ${FU[id].nombre.replace(/\s*[·(].*$/, '')}, probada ${FU[id].probada}` : id;

  function pearson(x, y) {
    const n = x.length, mx = x.reduce((a, b) => a + b, 0) / n, my = y.reduce((a, b) => a + b, 0) / n;
    let sxy = 0, sxx = 0, syy = 0;
    for (let i = 0; i < n; i++) { sxy += (x[i] - mx) * (y[i] - my); sxx += (x[i] - mx) ** 2; syy += (y[i] - my) ** 2; }
    return { r: sxx && syy ? sxy / Math.sqrt(sxx * syy) : 0, b: sxx ? sxy / sxx : 0, a: my - (sxx ? sxy / sxx : 0) * mx };
  }
  function rangos(v) {
    const o = v.map((x, i) => [x, i]).sort((a, b) => a[0] - b[0]), r = new Array(v.length);
    for (let i = 0; i < o.length;) { let j = i; while (j + 1 < o.length && o[j + 1][0] === o[i][0]) j++; for (let k = i; k <= j; k++) r[o[k][1]] = (i + j) / 2 + 1; i = j + 1; }
    return r;
  }
  const fuerza = r => { const a = Math.abs(r); return a >= .8 ? 'muy fuerte' : a >= .6 ? 'fuerte' : a >= .4 ? 'moderada' : a >= .2 ? 'débil' : 'muy débil'; };
  const et = id => M[id] ? M[id].etiqueta : id;

  function pintar() {
    const kx = $('#corrX').value, ky = $('#corrY').value, mx = M[kx], my = M[ky];
    const casos = D.filter(d => d[kx] != null && d[ky] != null);
    const xs = casos.map(d => d[kx]), ys = casos.map(d => d[ky]);
    if (casos.length < 5) { $('#corrLectura').innerHTML = '<p>No hay suficientes distritos con ambos datos.</p>'; $('#corrGrafico').innerHTML = ''; return; }
    const p = pearson(xs, ys), s = pearson(rangos(xs), rangos(ys)).r;
    G.dispersion($('#corrGrafico'), casos.map(d => ({ x: d[kx], y: d[ky], etiqueta: `${d.romano}. ${d.apodo}`, corta: d.romano, destacado: d.lado === 'Buda' })),
      { tx: `${mx.etiqueta} (${mx.unidad})`, ty: `${my.etiqueta} (${my.unidad})`, recta: [p.a, p.b] });
    const signo = p.r > 0 ? 'a más' : 'a menos';
    $('#corrLectura').innerHTML = `<div class="corr-r">r = ${G.fmt.n(p.r, 2)}</div>
      <p>Asociación <b>${fuerza(p.r)}</b> y ${p.r >= 0 ? 'positiva' : 'negativa'} entre <b>${G.esc(mx.etiqueta.toLowerCase())}</b> y <b>${G.esc(my.etiqueta.toLowerCase())}</b>: los distritos con más de lo primero tienden a tener ${signo} de lo segundo.
      Spearman (por rangos, resistente a extremos): <b class="mono">${G.fmt.n(s, 2)}</b> · n = ${casos.length}.</p>
      <p class="notas">Puntos ámbar: Buda · cian: Pest y Csepel. Fuentes: ${G.esc(cod(mx.fuente))} (${G.esc(mx.estado.replace('_', ' '))}) y ${G.esc(cod(my.fuente))} (${G.esc(my.estado.replace('_', ' '))}). Con 23 casos, |r| &lt; 0,41 no es distinguible de cero al 5 %. <b>Correlación no implica causalidad.</b></p>`;
  }

  window.CORRELACIONES = {
    init(L) {
      const j = L.distritos; if (!j) return;
      D = j.listas.distritos; pares = j.listas.pares || [];
      M = Object.fromEntries(j.listas.metricas.map(m => [m.id, m]));
      FU = Object.fromEntries((j.fuentes || []).map(f => [f.id, f]));
      $('#correlacionesLead').innerHTML = `Cruza <b>${j.listas.metricas.length} métricas trazables</b> de los 23 distritos —demografía, vivienda, transporte, servicios, verde, suelo y aire— y calcula Pearson y Spearman sobre casos completos. ` +
        `Sirve para formular preguntas y detectar relaciones que merecen análisis, no para afirmar causas.`;
      const opts = sel => j.listas.metricas.map(m => `<option value="${m.id}" ${m.id === sel ? 'selected' : ''}>${G.esc(m.etiqueta)} (${G.esc(m.unidad)})</option>`).join('');
      $('#corrX').innerHTML = opts('densidad'); $('#corrY').innerHTML = opts('arbolado');
      $('#corrX').addEventListener('change', pintar); $('#corrY').addEventListener('change', pintar);
      const excluir = new Set(['sellado_alto', 'viviendas_km2']); // casi idénticas a otra métrica: ocultan pares informativos
      $('#corrPares').innerHTML = pares.filter(p => !excluir.has(p.x) && !excluir.has(p.y)).slice(0, 12).map(p =>
        `<button type="button" data-x="${p.x}" data-y="${p.y}"><span>${G.esc(et(p.x))} × ${G.esc(et(p.y))}</span><b>${G.fmt.n(p.pearson, 2)}</b></button>`).join('');
      $('#corrPares').addEventListener('click', e => { const b = e.target.closest('[data-x]'); if (!b) return; $('#corrX').value = b.dataset.x; $('#corrY').value = b.dataset.y; pintar(); });
      pintar();
    },
  };
})();
