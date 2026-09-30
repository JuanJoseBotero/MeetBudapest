// Diagnóstico por distrito: compara dos distritos en cinco dimensiones (scores 0–100 del lago) y prueba
// si la posición del distrito se sostiene al cambiar la prioridad (análisis de sensibilidad).
(function () {
  const $ = s => document.querySelector(s);
  const PERFILES = {
    equilibrio: { nombre: 'Equilibrio', pesos: { movilidad: 1, servicios: 1, verde: 1, vivienda: 1, ambiente: 1 } },
    movilidad: { nombre: 'Movilidad', pesos: { movilidad: 4, servicios: 1, verde: .5, vivienda: 1, ambiente: .5 } },
    habitabilidad: { nombre: 'Habitabilidad', pesos: { movilidad: 1, servicios: 2, verde: 3, vivienda: .5, ambiente: 2 } },
    densificacion: { nombre: 'Densificación', pesos: { movilidad: 2, servicios: 1, verde: .5, vivienda: 4, ambiente: .5 } },
  };
  let D = [], dims = [], metricas = {}, perfil = 'equilibrio';

  const nombre = d => `${d.romano}. ${d.apodo}`;
  const puntaje = (d, p) => {
    let s = 0, w = 0;
    for (const [k, peso] of Object.entries(PERFILES[p].pesos)) { const v = d['score_' + k]; if (v != null) { s += v * peso; w += peso; } }
    return w ? s / w : null;
  };
  const ranking = p => [...D].filter(d => puntaje(d, p) != null).sort((a, b) => puntaje(b, p) - puntaje(a, p));
  const puesto = (d, p) => ranking(p).findIndex(x => x.distrito_id === d.distrito_id) + 1;
  const mediana = vs => { const v = vs.filter(x => x != null).sort((a, b) => a - b), m = v.length >> 1; return v.length ? (v.length % 2 ? v[m] : (v[m - 1] + v[m]) / 2) : null; };

  function fila(dim, a, b) {
    const va = a['score_' + dim.id], vb = b['score_' + dim.id], med = mediana(D.map(d => d['score_' + dim.id]));
    const m0 = metricas[dim.metricas[0]];
    const ref = m0 ? `${m0.etiqueta}: ${G.fmt.n(a[m0.id])} vs ${G.fmt.n(b[m0.id])} ${m0.unidad}` : '';
    return `<div class="diag-fila" title="${G.esc(ref)}"><span>${G.esc(dim.nombre)}</span>
      <div class="diag-pista">${med != null ? `<span class="med" style="left:${med}%"></span>` : ''}${va != null ? `<i class="a" style="left:${va}%"></i>` : ''}${vb != null ? `<i class="b" style="left:${vb}%"></i>` : ''}</div>
      <b class="mono">${va == null ? '—' : Math.round(va)}</b></div>`;
  }

  function pintar() {
    const a = D.find(d => d.distrito_id == $('#diagA').value), b = D.find(d => d.distrito_id == $('#diagB').value);
    if (!a || !b) return;
    const rk = ranking(perfil), pa = puesto(a, perfil), pb = puesto(b, perfil);
    const conDatos = dims.filter(x => a['score_' + x.id] != null).sort((x, y) => a['score_' + y.id] - a['score_' + x.id]);
    const fuerte = conDatos[0], debil = conDatos.at(-1);
    const puestos = Object.keys(PERFILES).map(p => puesto(a, p)), rango = Math.max(...puestos) - Math.min(...puestos);
    const robusto = rango <= 4 ? `<b>La conclusión se sostiene</b>: con cualquier prioridad queda entre los puestos ${Math.min(...puestos)} y ${Math.max(...puestos)}.`
      : `<b>La conclusión depende de la prioridad</b>: su puesto va del ${Math.min(...puestos)} al ${Math.max(...puestos)} según qué se valore.`;
    const dif = puntaje(a, perfil) - puntaje(b, perfil);
    $('#diagResultado').innerHTML = `
      <div>
        <p class="diag-veredicto">Con prioridad <b>${PERFILES[perfil].nombre.toLowerCase()}</b>, <b>${G.esc(nombre(a))}</b> ocupa el <b>puesto ${pa} de ${rk.length}</b>
        (${Math.round(puntaje(a, perfil))}/100). Su fortaleza relativa es <b>${G.esc(fuerte.nombre.toLowerCase())}</b> y su punto débil, <b>${G.esc(debil.nombre.toLowerCase())}</b>.
        Frente a ${G.esc(nombre(b))} (puesto ${pb}) está ${Math.abs(dif) < 3 ? '<b>prácticamente empatado</b>' : `<b>${Math.round(Math.abs(dif))} puntos ${dif > 0 ? 'por encima' : 'por debajo'}</b>`}. ${robusto}</p>
        <p class="notas">Puntajes 0–100 normalizados entre los 23 distritos (línea gris = mediana). <span style="color:var(--acento)">■</span> ${G.esc(a.romano)} · <span style="color:var(--danubio)">■</span> ${G.esc(b.romano)}.
        «Aire» usa sensores ciudadanos en vivo y puede faltar en distritos sin sensores.</p>
      </div>
      <div>${dims.map(x => fila(x, a, b)).join('')}
        <div class="diag-ranking"><h3 style="margin-top:14px">Ranking · ${PERFILES[perfil].nombre}</h3><ol>${rk.map(d => `<li class="${d === a ? 'a' : d === b ? 'b' : ''}">${G.esc(nombre(d))} <span class="mono">${Math.round(puntaje(d, perfil))}</span></li>`).join('')}</ol></div>
      </div>`;
  }

  window.DIAGNOSTICO = {
    init(L) {
      const j = L.distritos; if (!j) return;
      D = j.listas.distritos; dims = j.listas.dimensiones;
      metricas = Object.fromEntries(j.listas.metricas.map(m => [m.id, m]));
      const opts = sel => D.map(d => `<option value="${d.distrito_id}" ${d.distrito_id === sel ? 'selected' : ''}>${G.esc(nombre(d))}</option>`).join('');
      $('#diagA').innerHTML = opts(5); $('#diagB').innerHTML = opts(11);
      $('#diagPerfiles').innerHTML = Object.entries(PERFILES).map(([k, p]) => `<button type="button" class="chip${k === perfil ? ' on' : ''}" data-p="${k}">${p.nombre}</button>`).join('');
      $('#diagPerfiles').addEventListener('click', e => {
        const b = e.target.closest('[data-p]'); if (!b) return; perfil = b.dataset.p;
        $('#diagPerfiles').querySelectorAll('.chip').forEach(c => c.classList.toggle('on', c === b)); pintar();
      });
      $('#diagA').addEventListener('change', pintar); $('#diagB').addEventListener('change', pintar);
      $('#diagSwap').addEventListener('click', () => { const a = $('#diagA').value; $('#diagA').value = $('#diagB').value; $('#diagB').value = a; pintar(); });
      pintar();
    },
    seleccionar(id) { $('#diagA').value = id; pintar(); document.getElementById('panorama').scrollIntoView({ behavior: 'smooth' }); },
  };
})();
