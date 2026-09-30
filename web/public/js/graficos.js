// Gráficos SVG sin librerías: tiles, tarjetas, líneas, barras, pirámide, tabla, dispersión y coropleta.
// Reglas: un eje Y, marcas finas, leyenda cuando hay ≥ 2 series, tooltip con cruz al pasar el cursor.
(function () {
  const NS = 'http://www.w3.org/2000/svg';
  const css = getComputedStyle(document.documentElement);
  const PAL = ['--s1', '--s2', '--s3', '--s4', '--s5', '--s6'].map(v => css.getPropertyValue(v).trim());
  const tip = document.getElementById('tip');
  const esc = v => String(v == null ? '' : v).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

  const fmt = {
    n(v, d) {
      if (v == null || isNaN(v)) return '—';
      const a = Math.abs(v); if (d == null) d = a >= 100 ? 0 : a >= 10 ? 1 : 2;
      return Number(v).toLocaleString('es-ES', { maximumFractionDigits: d, minimumFractionDigits: 0, useGrouping: 'always' });
    },
    k(v) {
      if (v == null || isNaN(v)) return '—'; const a = Math.abs(v);
      if (a >= 1e9) return fmt.n(v / 1e9, 2) + ' mil M'; if (a >= 1e6) return fmt.n(v / 1e6, 2) + ' M';
      if (a >= 1e4) return fmt.n(v / 1e3, 1) + ' k'; return fmt.n(v);
    },
    pct(v, d) { return v == null ? '—' : fmt.n(v, d == null ? 1 : d) + ' %'; },
    fecha(ms) { return new Date(ms).toLocaleString('es-ES', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit', timeZone: 'Europe/Budapest' }); },
  };

  function el(tag, attrs, padre) { const e = document.createElementNS(NS, tag); for (const k in attrs) e.setAttribute(k, attrs[k]); if (padre) padre.appendChild(e); return e; }
  function mostrarTip(html, x, y) {
    tip.innerHTML = html; tip.hidden = false; const r = tip.getBoundingClientRect();
    let tx = x + 14, ty = y + 14; if (tx + r.width > innerWidth - 8) tx = x - r.width - 14; if (ty + r.height > innerHeight - 8) ty = y - r.height - 14;
    tip.style.left = tx + 'px'; tip.style.top = ty + 'px';
  }
  function ocultarTip() { tip.hidden = true; }
  function marcas(min, max, n) {
    if (min === max) { max = min + 1; }
    const paso0 = (max - min) / Math.max(1, n), mag = Math.pow(10, Math.floor(Math.log10(paso0)));
    const paso = [1, 2, 2.5, 5, 10].map(m => m * mag).find(p => p >= paso0) || paso0;
    const out = []; for (let v = Math.ceil(min / paso) * paso; v <= max + 1e-9; v += paso) out.push(+v.toFixed(10)); return out;
  }

  // ---------------------------------------------------------------- tile y tarjeta
  function tile(cont, o) {
    const d = document.createElement('div'); d.className = 'tile'; if (o.title) d.title = o.title;
    d.innerHTML = `<div class="v">${esc(o.valor)}${o.unidad ? `<small>${esc(o.unidad)}</small>` : ''}</div><div class="l">${esc(o.etiqueta)}</div>
      <div class="f">${o.estado ? `<span class="estado-tag estado-${esc(o.estado)}">${esc(o.estado.replace('_', ' '))}</span>` : ''}<span>${esc(o.fuente || '')}</span>${o.vigencia ? `<span>· ${esc(o.vigencia)}</span>` : ''}</div>`;
    cont.appendChild(d); return d;
  }
  function card(cont, titulo, sub, opts) {
    const c = document.createElement('article'); c.className = 'card' + (opts && opts.ancha ? ' ancha' : '');
    c.innerHTML = `<header><h3>${esc(titulo)}</h3><small>${esc(sub || '')}</small></header><div class="cuerpo"></div>`;
    cont.appendChild(c);
    return {
      el: c, cuerpo: c.querySelector('.cuerpo'),
      nota(t) { const p = document.createElement('p'); p.className = 'nota'; p.textContent = t; c.appendChild(p); },
      fuente(html) { const p = document.createElement('div'); p.className = 'fuente'; p.innerHTML = html; c.appendChild(p); },
    };
  }

  // ---------------------------------------------------------------- líneas
  function aX(x) { return typeof x === 'number' ? x : Date.parse(String(x).length === 16 ? x + ':00' : x); }
  function linea(cont, series, o) {
    o = o || {}; const W = 640, H = o.alto || 240, m = { t: 12, r: 16, b: 26, l: 52 };
    const ss = series.map(s => ({ nombre: s.nombre, pts: s.puntos.map(p => [aX(p[0]), p[1]]).filter(p => p[1] != null && !isNaN(p[0])) })).filter(s => s.pts.length);
    if (!ss.length) return;
    const xs = ss.flatMap(s => s.pts.map(p => p[0])), ys = ss.flatMap(s => s.pts.map(p => p[1])).concat((o.refs || []).map(r => r.y));
    const esFecha = ss.some((s, i) => typeof series[i].puntos[0][0] === 'string');
    let x0 = Math.min(...xs), x1 = Math.max(...xs), y0 = o.cero === false ? Math.min(...ys) : Math.min(0, ...ys), y1 = Math.max(...ys);
    if (o.cero === false) { const pad = (y1 - y0) * .08 || 1; y0 -= pad; y1 += pad; }
    const my = marcas(y0, y1, 4); y0 = Math.min(y0, my[0]); y1 = Math.max(y1, my[my.length - 1]);
    const sx = v => m.l + (x1 === x0 ? .5 : (v - x0) / (x1 - x0)) * (W - m.l - m.r), sy = v => H - m.b - (v - y0) / (y1 - y0 || 1) * (H - m.t - m.b);
    const svg = el('svg', { viewBox: `0 0 ${W} ${H}`, width: '100%', role: 'img', 'aria-label': o.aria || ss.map(s => s.nombre).join(', ') }, cont);
    const rej = el('g', { class: 'rejilla' }, svg);
    const fy = o.fmtY || (v => fmt.k(v));
    my.forEach(v => { el('line', { x1: m.l, x2: W - m.r, y1: sy(v), y2: sy(v) }, rej); el('text', { x: m.l - 6, y: sy(v) + 4, 'text-anchor': 'end' }, svg).textContent = fy(v); });
    const fx = esFecha ? (v => fmt.fecha(v)) : (o.fmtX || (v => Number.isInteger(v) ? String(v) : fmt.n(v, 2)));
    const mx = esFecha ? [x0, (x0 + x1) / 2, x1] : (Number.isInteger(x0) && x1 - x0 <= 12 ? Array.from({ length: x1 - x0 + 1 }, (_, i) => x0 + i) : marcas(x0, x1, 6).filter(v => v >= x0 && v <= x1));
    mx.forEach(v => { el('text', { x: sx(v), y: H - 8, 'text-anchor': 'middle' }, svg).textContent = esFecha ? fmt.fecha(v).replace(/,.*/, '') : fx(v); });
    (o.refs || []).forEach(r => {
      el('line', { x1: m.l, x2: W - m.r, y1: sy(r.y), y2: sy(r.y), stroke: 'var(--alerta)', 'stroke-dasharray': '4 3', 'stroke-width': 1 }, svg);
      el('text', { x: W - m.r, y: sy(r.y) - 4, 'text-anchor': 'end', style: 'fill:var(--alerta)' }, svg).textContent = r.etiqueta;
    });
    ss.forEach((s, i) => {
      const d = s.pts.map((p, k) => (k ? 'L' : 'M') + sx(p[0]).toFixed(1) + ',' + sy(p[1]).toFixed(1)).join('');
      el('path', { d, fill: 'none', stroke: PAL[i % PAL.length], 'stroke-width': 2, 'stroke-linejoin': 'round' }, svg);
      if (s.pts.length <= 40) s.pts.forEach(p => el('circle', { cx: sx(p[0]), cy: sy(p[1]), r: 2.4, fill: PAL[i % PAL.length] }, svg));
    });
    const cruz = el('line', { y1: m.t, y2: H - m.b, stroke: 'var(--tinta-3)', 'stroke-width': 1, visibility: 'hidden' }, svg);
    const zona = el('rect', { x: m.l, y: m.t, width: W - m.l - m.r, height: H - m.t - m.b, fill: 'transparent' }, svg);
    const fv = o.fmtV || fy;
    zona.addEventListener('mousemove', e => {
      const r = svg.getBoundingClientRect(), vx = x0 + ((e.clientX - r.left) / r.width * W - m.l) / (W - m.l - m.r) * (x1 - x0);
      const cerca = xs.reduce((a, b) => Math.abs(b - vx) < Math.abs(a - vx) ? b : a, xs[0]);
      cruz.setAttribute('x1', sx(cerca)); cruz.setAttribute('x2', sx(cerca)); cruz.setAttribute('visibility', 'visible');
      const filas = ss.map((s, i) => { const p = s.pts.find(q => q[0] === cerca); return p ? `<div><i style="display:inline-block;width:8px;height:8px;border-radius:2px;background:${PAL[i % PAL.length]};margin-right:6px"></i>${esc(s.nombre)}: <b>${fv(p[1])}</b></div>` : ''; }).join('');
      mostrarTip(`<b>${esFecha ? fmt.fecha(cerca) : fx(cerca)}</b>${filas}`, e.clientX, e.clientY);
    });
    zona.addEventListener('mouseleave', () => { cruz.setAttribute('visibility', 'hidden'); ocultarTip(); });
    if (ss.length > 1) {
      const l = document.createElement('div'); l.className = 'leyenda-serie';
      l.innerHTML = ss.map((s, i) => `<span><i style="background:${PAL[i % PAL.length]}"></i>${esc(s.nombre)}</span>`).join(''); cont.appendChild(l);
    }
  }

  // ---------------------------------------------------------------- barras
  function barras(cont, items, o) {
    o = o || {}; items = items.filter(i => i.valor != null);
    if (!items.length) return;
    const fv = o.fmtV || (v => fmt.k(v));
    if (o.horizontal !== false) {
      const max = Math.max(...items.map(i => Math.abs(i.valor))) || 1;
      const t = document.createElement('div'); t.className = o.scroll ? 'tabla-scroll' : '';
      t.innerHTML = `<table><tbody>${items.map(i => `<tr${i.destacado ? ' style="color:var(--acento-2)"' : ''}><td>${esc(i.etiqueta)}</td>
        <td style="width:45%"><span class="barra-h" style="width:${(Math.abs(i.valor) / max * 100).toFixed(1)}%;background:${i.color || (i.destacado ? 'var(--acento)' : 'var(--danubio)')}"></span></td>
        <td class="n">${fv(i.valor)}</td></tr>`).join('')}</tbody></table>`;
      cont.appendChild(t); return;
    }
    const W = 640, H = o.alto || 220, m = { t: 12, r: 10, b: 26, l: 48 };
    const vmax = Math.max(0, ...items.map(i => i.valor)), my = marcas(0, vmax, 4), y1 = Math.max(vmax, my[my.length - 1]);
    const bw = (W - m.l - m.r) / items.length, sy = v => H - m.b - v / (y1 || 1) * (H - m.t - m.b);
    const svg = el('svg', { viewBox: `0 0 ${W} ${H}`, width: '100%', role: 'img' }, cont), rej = el('g', { class: 'rejilla' }, svg);
    my.forEach(v => { el('line', { x1: m.l, x2: W - m.r, y1: sy(v), y2: sy(v) }, rej); el('text', { x: m.l - 6, y: sy(v) + 4, 'text-anchor': 'end' }, svg).textContent = fv(v); });
    const cada = Math.ceil(items.length / 12);
    items.forEach((it, k) => {
      const b = el('rect', { x: m.l + k * bw + bw * .15, width: bw * .7, y: sy(it.valor), height: Math.max(0, sy(0) - sy(it.valor)), rx: 2, fill: it.destacado ? 'var(--acento)' : 'var(--danubio)' }, svg);
      b.addEventListener('mousemove', e => mostrarTip(`<b>${esc(it.etiqueta)}</b><div>${fv(it.valor)}</div>`, e.clientX, e.clientY)); b.addEventListener('mouseleave', ocultarTip);
      if (k % cada === 0) el('text', { x: m.l + k * bw + bw / 2, y: H - 8, 'text-anchor': 'middle' }, svg).textContent = it.etiqueta;
    });
  }

  function piramide(cont, filas) {
    const W = 640, fila = 15, H = filas.length * fila + 30, c = W / 2, ancho = W / 2 - 60;
    const max = Math.max(...filas.flatMap(f => [f.hombres || 0, f.mujeres || 0])) || 1;
    const svg = el('svg', { viewBox: `0 0 ${W} ${H}`, width: '100%', role: 'img', 'aria-label': 'Pirámide de población' }, cont);
    [...filas].reverse().forEach((f, i) => {
      const y = 8 + i * fila;
      const h = el('rect', { x: c - 26 - (f.hombres || 0) / max * ancho, y, width: (f.hombres || 0) / max * ancho, height: fila - 3, fill: PAL[0], rx: 1.5 }, svg);
      const m = el('rect', { x: c + 26, y, width: (f.mujeres || 0) / max * ancho, height: fila - 3, fill: PAL[1], rx: 1.5 }, svg);
      el('text', { x: c, y: y + fila - 5, 'text-anchor': 'middle' }, svg).textContent = f.grupo;
      [h, m].forEach(b => { b.addEventListener('mousemove', e => mostrarTip(`<b>${esc(f.grupo)} años</b><div>Hombres: ${fmt.n(f.hombres)}</div><div>Mujeres: ${fmt.n(f.mujeres)}</div>`, e.clientX, e.clientY)); b.addEventListener('mouseleave', ocultarTip); });
    });
    el('text', { x: c - 30, y: H - 4, 'text-anchor': 'end' }, svg).textContent = 'Hombres';
    el('text', { x: c + 30, y: H - 4 }, svg).textContent = 'Mujeres';
  }

  function tabla(cont, cols, filas, o) {
    const d = document.createElement('div'); d.className = 'tabla-scroll';
    d.innerHTML = `<table><thead><tr>${cols.map(c => `<th class="${c.n ? 'n' : ''}">${esc(c.t)}</th>`).join('')}</tr></thead><tbody>${filas.map(f =>
      `<tr>${cols.map(c => { const v = f[c.k]; return `<td class="${c.n ? 'n' : ''}">${c.html ? c.html(v, f) : esc(c.fmt ? c.fmt(v, f) : (typeof v === 'number' ? fmt.n(v) : (v == null ? '—' : v)))}</td>`; }).join('')}</tr>`).join('')}</tbody></table>`;
    cont.appendChild(d); return d;
  }

  // ---------------------------------------------------------------- dispersión
  function dispersion(cont, puntos, o) {
    cont.innerHTML = ''; o = o || {}; const W = 640, H = 380, m = { t: 14, r: 16, b: 40, l: 60 };
    const ps = puntos.filter(p => p.x != null && p.y != null); if (!ps.length) return;
    const xs = ps.map(p => p.x), ys = ps.map(p => p.y);
    const mx = marcas(Math.min(...xs), Math.max(...xs), 5), myy = marcas(Math.min(...ys), Math.max(...ys), 5);
    const x0 = Math.min(mx[0], ...xs), x1 = Math.max(mx[mx.length - 1], ...xs), y0 = Math.min(myy[0], ...ys), y1 = Math.max(myy[myy.length - 1], ...ys);
    const sx = v => m.l + (v - x0) / (x1 - x0 || 1) * (W - m.l - m.r), sy = v => H - m.b - (v - y0) / (y1 - y0 || 1) * (H - m.t - m.b);
    const svg = el('svg', { viewBox: `0 0 ${W} ${H}`, width: '100%', role: 'img' }, cont), rej = el('g', { class: 'rejilla' }, svg);
    myy.forEach(v => { el('line', { x1: m.l, x2: W - m.r, y1: sy(v), y2: sy(v) }, rej); el('text', { x: m.l - 6, y: sy(v) + 4, 'text-anchor': 'end' }, svg).textContent = fmt.k(v); });
    mx.forEach(v => { el('line', { x1: sx(v), x2: sx(v), y1: m.t, y2: H - m.b }, rej); el('text', { x: sx(v), y: H - m.b + 16, 'text-anchor': 'middle' }, svg).textContent = fmt.k(v); });
    el('text', { x: W - m.r, y: H - 4, 'text-anchor': 'end' }, svg).textContent = o.tx || '';
    el('text', { x: 4, y: 10 }, svg).textContent = o.ty || '';
    if (o.recta) { const [a, b] = o.recta; el('line', { x1: sx(x0), y1: sy(a + b * x0), x2: sx(x1), y2: sy(a + b * x1), stroke: 'var(--tinta-3)', 'stroke-dasharray': '5 4' }, svg); }
    ps.forEach(p => {
      const c = el('circle', { cx: sx(p.x), cy: sy(p.y), r: p.destacado ? 7 : 5.5, fill: p.destacado ? 'var(--acento)' : 'var(--danubio)', 'fill-opacity': .85, stroke: 'var(--fondo)' }, svg);
      el('text', { x: sx(p.x) + 8, y: sy(p.y) + 4, style: 'font-size:10px' }, svg).textContent = p.corta || '';
      c.addEventListener('mousemove', e => mostrarTip(`<b>${esc(p.etiqueta)}</b><div>${esc(o.tx)}: ${fmt.n(p.x)}</div><div>${esc(o.ty)}: ${fmt.n(p.y)}</div>`, e.clientX, e.clientY));
      c.addEventListener('mouseleave', ocultarTip);
    });
  }

  // ---------------------------------------------------------------- coropleta SVG (proyección equirectangular local)
  const RAMPA = ['#0e2a36', '#135266', '#1f7f8f', '#3fb8c9', '#9fd9c3', '#f3c77a', '#e8a33d'];
  function color(t) {
    if (t == null || isNaN(t)) return '#1b2632'; t = Math.max(0, Math.min(1, t)); const p = t * (RAMPA.length - 1), i = Math.floor(p), f = p - i;
    const a = RAMPA[i], b = RAMPA[Math.min(i + 1, RAMPA.length - 1)], h = (s, k) => parseInt(s.slice(1 + 2 * k, 3 + 2 * k), 16);
    return '#' + [0, 1, 2].map(k => Math.round(h(a, k) + (h(b, k) - h(a, k)) * f).toString(16).padStart(2, '0')).join('');
  }
  function coropleta(cont, gj, valor, o) {
    cont.innerHTML = ''; o = o || {};
    const coords = gj.features.flatMap(f => f.geometry.coordinates.flat(2));
    const lon0 = Math.min(...coords.map(c => c[0])), lon1 = Math.max(...coords.map(c => c[0])), lat0 = Math.min(...coords.map(c => c[1])), lat1 = Math.max(...coords.map(c => c[1]));
    const k = Math.cos((lat0 + lat1) / 2 * Math.PI / 180), W = 600, H = W * (lat1 - lat0) / ((lon1 - lon0) * k);
    const px = c => [((c[0] - lon0) / (lon1 - lon0) * W).toFixed(1), ((lat1 - c[1]) / (lat1 - lat0) * H).toFixed(1)];
    const vals = gj.features.map(valor).filter(v => v != null), lo = Math.min(...vals), hi = Math.max(...vals);
    const svg = el('svg', { viewBox: `0 0 ${W} ${H.toFixed(0)}`, width: '100%', role: 'img', 'aria-label': o.aria || 'Mapa de distritos' }, cont);
    gj.features.forEach(f => {
      const v = valor(f), d = f.geometry.coordinates.map(poli => poli.map(a => 'M' + a.map(px).join('L') + 'Z').join('')).join('');
      const p = el('path', { d, fill: color(v == null ? null : (v - lo) / (hi - lo || 1)), 'fill-rule': 'evenodd' }, svg);
      p.addEventListener('mousemove', e => mostrarTip(o.tip ? o.tip(f, v) : `<b>${esc(f.properties.romano)}</b> ${fmt.n(v)}`, e.clientX, e.clientY));
      p.addEventListener('mouseleave', ocultarTip);
      if (o.onClick) p.addEventListener('click', () => o.onClick(f));
    });
    gj.features.forEach(f => { const c = f.properties.centro; if (c) el('text', { x: px(c)[0], y: px(c)[1], 'text-anchor': 'middle', style: 'font-size:10px;fill:#e6edf3;pointer-events:none;paint-order:stroke;stroke:#0a1016;stroke-width:3px' }, svg).textContent = f.properties.romano; });
    const l = document.createElement('div'); l.className = 'leyenda-serie';
    l.innerHTML = `<span style="flex:1"><span style="display:block;height:8px;border-radius:4px;background:linear-gradient(90deg,${RAMPA.join(',')})"></span><span style="display:flex;justify-content:space-between" class="mono"><small>${fmt.n(lo)}</small><small>${esc(o.unidad || '')}</small><small>${fmt.n(hi)}</small></span></span>`;
    cont.appendChild(l);
  }

  window.G = { fmt, esc, tile, card, linea, barras, piramide, tabla, dispersion, coropleta, color, RAMPA, PAL, mostrarTip, ocultarTip };
})();
