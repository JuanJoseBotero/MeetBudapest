// Arranque: compuerta (validada en servidor), carga de los temas gold vía /api/datos, navegación, buscador, reloj y clima.
(function () {
  const $ = s => document.querySelector(s);
  const TEMAS = ['territorio', 'demografia', 'economia', 'turismo', 'movilidad', 'ambiente', 'distritos', 'catalogo'];
  window.LAGO = {};

  async function datos(ruta) {
    const r = await fetch('/api/datos?f=' + encodeURIComponent(ruta), { cache: 'no-store', credentials: 'same-origin' });
    if (!r.ok) throw new Error(ruta + ' ' + r.status);
    return r.json();
  }
  window.cargarGeo = nombre => datos('geo/' + nombre + '.geojson');

  async function sesionAbierta() {
    try { const r = await fetch('/api/sesion', { cache: 'no-store' }); return (await r.json()).abierta; } catch (_) { return false; }
  }

  async function arrancar() {
    $('#gate').hidden = true; $('#app').hidden = false;
    const res = await Promise.allSettled(TEMAS.map(t => datos('temas/' + t + '.json').then(j => { LAGO[t] = j; })));
    const ok = res.filter(r => r.status === 'fulfilled').length;
    $('#estadoDatos').textContent = `lago: ${ok}/${TEMAS.length} temas`;
    const probados = Object.values(LAGO).map(j => j.probado).filter(Boolean).sort();
    if (probados.length) $('#pieProbado').textContent = 'lago probado ' + probados[0] + (probados.at(-1) !== probados[0] ? ' → ' + probados.at(-1) : '');
    for (const [nombre, mod] of [['secciones', window.SECCIONES], ['diagnostico', window.DIAGNOSTICO], ['atlas', window.ATLAS], ['correlaciones', window.CORRELACIONES], ['mapa', window.MAPA]]) {
      try { mod && mod.init(LAGO); } catch (e) { console.error(nombre, e); }
    }
    navegacion(); buscador(); reloj(); clima();
    if (location.hash) { const s = document.querySelector(location.hash); s && s.scrollIntoView(); }
  }

  $('#gateForm').addEventListener('submit', async e => {
    e.preventDefault(); const msg = $('#gateMsg'); msg.textContent = 'verificando…';
    try {
      const r = await fetch('/api/entrar', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ clave: $('#clave').value }) });
      const j = await r.json();
      if (r.ok && j.ok) { $('#clave').value = ''; msg.textContent = ''; arrancar(); } else msg.textContent = j.error || 'Clave incorrecta';
    } catch (_) { msg.textContent = 'No se pudo contactar el servidor'; }
  });
  $('#btnSalir').addEventListener('click', async () => { await fetch('/api/sesion?salir=1', { method: 'POST' }); location.reload(); });
  sesionAbierta().then(abierta => { if (abierta) arrancar(); else { $('#gate').hidden = false; $('#clave').focus(); } });

  function navegacion() {
    const enlaces = [...document.querySelectorAll('#menu a')], secs = enlaces.map(a => document.getElementById(a.dataset.sec));
    const menu = $('#menu');
    enlaces.forEach(a => a.addEventListener('click', e => {
      e.preventDefault(); history.replaceState(null, '', '#' + a.dataset.sec);
      document.getElementById(a.dataset.sec).scrollIntoView({ behavior: 'smooth' }); menu.classList.remove('abierto');
    }));
    $('#btnMenu').addEventListener('click', () => menu.classList.toggle('abierto'));
    const marcar = () => {
      let mejor = 0, dist = Infinity;
      secs.forEach((s, i) => { const d = Math.abs(s.getBoundingClientRect().top - 70); if (s.getBoundingClientRect().top < innerHeight * .5 && d < dist) { dist = d; mejor = i; } });
      enlaces.forEach((a, i) => a.classList.toggle('activa', i === mejor)); $('#migas').textContent = enlaces[mejor].textContent;
    };
    addEventListener('scroll', () => requestAnimationFrame(marcar), { passive: true }); marcar();
  }

  // Buscador Ctrl/⌘K o «/»: secciones, cifras (tiles) y lugares del mapa
  function buscador() {
    const box = $('#buscador'), inp = $('#buscadorInput'), lista = $('#buscadorLista'); let items = [], vis = [], sel = 0, foco = null;
    const indexar = () => {
      items = [...document.querySelectorAll('#menu a')].map(a => ({ t: a.textContent, s: 'sección', go: () => a.click() }));
      document.querySelectorAll('.tile').forEach(t => {
        const sec = t.closest('.sec'); if (!sec) return;
        items.push({ t: t.querySelector('.l').textContent + ' · ' + t.querySelector('.v').textContent, s: sec.querySelector('h1').textContent,
          go: () => { t.scrollIntoView({ behavior: 'smooth', block: 'center' }); t.animate([{ outline: '2px solid #e8a33d' }, { outline: '2px solid transparent' }], 1600); } });
      });
      (window.MAPA && MAPA.lugares ? MAPA.lugares() : []).forEach(l => items.push({ t: l.nombre, s: l.tipo, go: () => { document.getElementById('gemelo').scrollIntoView({ behavior: 'smooth' }); MAPA.irA(l); } }));
    };
    const pintar = q => {
      q = q.toLowerCase().normalize('NFD').replace(/\p{Diacritic}/gu, '');
      vis = items.filter(i => i.t.toLowerCase().normalize('NFD').replace(/\p{Diacritic}/gu, '').includes(q)).slice(0, 14); sel = 0;
      lista.innerHTML = vis.map((i, k) => `<button type="button" role="option" id="bq${k}" aria-selected="${k === 0}" class="${k === 0 ? 'sel' : ''}"><span>${G.esc(i.t)}</span><small>${G.esc(i.s)}</small></button>`).join('');
      lista.querySelectorAll('button').forEach((b, k) => b.onclick = () => { vis[k].go(); cerrar(); });
    };
    const abrir = () => { foco = document.activeElement; indexar(); box.hidden = false; inp.value = ''; pintar(''); inp.focus(); };
    const cerrar = () => { box.hidden = true; foco && foco.focus && foco.focus(); };
    inp.addEventListener('input', () => pintar(inp.value));
    inp.addEventListener('keydown', e => {
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
        e.preventDefault(); sel = Math.max(0, Math.min(vis.length - 1, sel + (e.key === 'ArrowDown' ? 1 : -1)));
        lista.querySelectorAll('button').forEach((b, k) => { b.classList.toggle('sel', k === sel); b.setAttribute('aria-selected', k === sel); });
        const b = $('#bq' + sel); b && b.scrollIntoView({ block: 'nearest' });
      } else if (e.key === 'Enter') { vis[sel] && vis[sel].go(); cerrar(); } else if (e.key === 'Escape') cerrar();
    });
    document.addEventListener('keydown', e => {
      const escribiendo = /^(input|textarea|select)$/i.test(e.target.tagName);
      if (((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') || (e.key === '/' && !escribiendo)) { e.preventDefault(); box.hidden ? abrir() : cerrar(); }
    });
    $('#btnBuscar').addEventListener('click', abrir);
    document.addEventListener('mousedown', e => { if (!box.hidden && !box.contains(e.target) && e.target !== $('#btnBuscar')) cerrar(); });
  }

  function reloj() {
    const f = () => { $('#reloj').textContent = new Date().toLocaleString('es-ES', { timeZone: 'Europe/Budapest', weekday: 'short', day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' }) + ' · Budapest'; };
    f(); setInterval(f, 30000);
  }
  async function clima() {
    try {
      const r = await fetch('https://api.open-meteo.com/v1/forecast?latitude=47.4979&longitude=19.0402&current=temperature_2m,relative_humidity_2m,wind_speed_10m&timezone=Europe%2FBudapest');
      const c = (await r.json()).current;
      $('#clima').textContent = `${Math.round(c.temperature_2m)} °C · ${c.relative_humidity_2m} % HR · ${Math.round(c.wind_speed_10m)} km/h`;
      $('#clima').title = 'Open-Meteo en vivo · ' + c.time;
    } catch (_) { /* sin clima en vivo: el resto del sitio no depende de él */ }
  }
})();
