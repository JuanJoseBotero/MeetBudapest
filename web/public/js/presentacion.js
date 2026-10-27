// Presentación del pitch (12 min, 3 turnos de 4 min): 10 diapositivas con teclado, pantalla completa y cronómetro.
// Las cifras son las del guion del 2026-10-27; la versión viva de cada una está en su sección, con fuente y fecha.
(function () {
  const $ = s => document.querySelector(s);
  const TURNOS = {
    1: ['Juan José Botero · el problema y el sistema', '0:00–4:00'],
    2: ['Santiago Idárraga · el lago y lo que no mostramos', '4:00–8:00'],
    3: ['Samuel Villa · herramientas, seguridad e IA', '8:00–12:00'],
  };
  const pill = (txt, cls) => `<span class="pill ${cls}">${txt}</span>`;

  const DIAS = [
    { turno: 1, portada: true, titulo: 'Cerebro Budapest', html: `
      <p class="dia-ante">Taller de datos · Entrega 2</p>
      <h2 class="dia-xl">Cerebro Budapest</h2>
      <p class="dia-lema">Entender un distrito. <span>Decidir con evidencia.</span></p>
      <p class="q">Sistema de información territorial de los 23 distritos, réplica del Cerebro Lima</p>
      <div class="col3 cifras">
        <div class="caja"><b>1 675 777</b><small>habitantes · F08 · 2026</small></div>
        <div class="caja"><b>525 km²</b><small>superficie · F08</small></div>
        <div class="caja"><b>23</b><small>distritos (kerületek)</small></div>
      </div>` },

    { turno: 1, ante: 'Para urbanismo y para un vecino que compara distritos', titulo: 'Tres preguntas que el sistema ya responde', html: `
      <div class="filas">
        <div class="caja fila"><span class="etq">P1</span><div><b class="dia-h">¿Qué distritos tienen peor acceso a transporte y bicicleta?</b>
          <p>Peor movilidad: Soroksár, Rákosmente y Csepel, en la periferia.</p>
          <p class="q">11 de los 23 distritos no tienen estación de bicicleta pública · F05 F02 F08</p></div></div>
        <div class="caja fila"><span class="etq">P2</span><div><b class="dia-h">¿Dónde hay más riesgo de isla de calor?</b>
          <p>Distrito VII: 85 % del suelo sellado. El centro tiene menos de 1 % de arbolado.</p>
          <p class="q">48 días con máximas de 30 °C o más en 2025, según el modelo ERA5 · F04 F14</p></div></div>
        <div class="caja fila"><span class="etq">P3</span><div><b class="dia-h">¿Cumple Budapest con la calidad del aire?</b>
          <p>Cumple los límites anuales de la UE en PM2.5, PM10 y NO₂.</p>
          <p class="q">No cumple ninguna guía de la OMS · F13 (sensores ciudadanos F11 y F12, bajo costo)</p></div></div>
      </div>
      <p class="q">Pendientes, con su motivo: servicio real del transporte, pobreza por distrito y bicis disponibles.</p>` },

    { turno: 1, ante: 'Procedencia y territorio', titulo: 'Ninguna cifra sin su fuente, a un clic', html: `
      <div class="col2">
        <div class="pila">
          <div class="caja"><b class="dia-cifra">1 675 777 hab</b><p>Población residente (23 distritos)</p>
            <p class="acento">observado · F08 · 2026-01-01</p></div>
          <p class="q clic">↓ un clic</p>
          <dl class="caja marcada ficha-dia">
            <dt>Fuente</dt><dd><b>F08 · KSH Helységnévtár</b></dd>
            <dt>Vigencia</dt><dd>2026-01-01</dd>
            <dt>Probada</dt><dd>2026-10-26</dd>
            <dt>Estado</dt><dd>observado</dd>
            <dt>Licencia</dt><dd>no declara (se cita a KSH)</dd>
          </dl>
        </div>
        <div class="caja">
          <b class="dia-h">Gemelo 3D: clic en un punto</b><p class="q">mide su entorno en 500 m y 1 km</p>
          <div class="radar">
            <svg viewBox="0 0 160 160" aria-hidden="true"><circle cx="80" cy="80" r="74" class="r1"/><circle cx="80" cy="80" r="46" class="r2"/><circle cx="80" cy="80" r="5" class="r3"/></svg>
            <ul><li>paradas</li><li>salidas por día</li><li>modos de transporte</li><li>estaciones Bubi</li><li>equipamientos</li><li>sensor más cercano</li></ul>
          </div>
        </div>
      </div>` },

    { turno: 2, ante: 'El lago de datos', titulo: 'Un lago de tres capas: si falla, no se publica', html: `
      <div class="flujo">
        <div class="caja"><b>12 fuentes</b><small>APIs y descargas sin llave ni pago · F02 a F14</small></div><span class="flecha">→</span>
        <div class="caja"><b>Bronze</b><small>tal cual llega, inmutable, con huella sha256</small></div><span class="flecha">→</span>
        <div class="caja"><b>Silver</b><small>limpio y tipado en SQLite, distrito asignado</small></div><span class="flecha">→</span>
        <div class="caja marcada"><b>Gold</b><small>temas y capas que lee el sitio, con ID y fecha</small></div><span class="flecha">→</span>
        <div class="caja"><b>Sitio</b><small>detrás de la compuerta · /api/datos</small></div>
      </div>
      <div class="caja alerta">
        <b class="dia-h">22 de octubre: OpenStreetMap respondió «todo bien» con 0 distritos</b>
        <p>Antes: el lago se quedó sin mapa.</p>
        <p>Ahora: si no llegan los 23 distritos, se rechaza la descarga y se usa la última válida.</p>
        <p class="q">Igual con Copernicus (F04) en la última ejecución: queda en error y el sitio conserva su dato.</p>
      </div>
      <p class="q">Solo Python estándar: 0 paquetes instalados.</p>` },

    { turno: 2, ante: 'Estados visibles en el sitio', titulo: 'Cada cifra dice qué tipo de dato es', html: `
      <div class="col3">
        <div class="caja">${pill('observado', 'estado-observado')}<p>medido o publicado por la propia fuente</p><p class="q">ej. población · F08</p></div>
        <div class="caja">${pill('derivado', 'estado-derivado')}<p>cálculo propio sobre datos observados</p><p class="q">ej. densidad, puntajes</p></div>
        <div class="caja">${pill('modelo', 'estado-modelo')}<p>salida de un modelo, no una medición</p><p class="q">ERA5 y CAMS · F14</p></div>
        <div class="caja">${pill('bajo costo', 'estado-bajo_costo')}<p>sensores ciudadanos sin calibración oficial</p><p class="q">F11 y F12</p></div>
        <div class="caja">${pill('proxy', 'estado-proxy')}<p>aproximación cuando falta el dato real</p><p class="q">vivienda: índice de Hungría</p></div>
        <div class="caja">${pill('candidata', 'candidata')}<p>responde pero no trae datos utilizables</p><p class="q">F07 MOL Bubi</p></div>
      </div>
      <p class="q">La etiqueta aparece en cada cifra y en cada gráfico, junto al ID de su fuente.</p>` },

    { turno: 2, ante: 'Datos delicados y huecos', titulo: 'Lo que decidimos no mostrar, y por qué', html: `
      <div class="col2">
        <div class="caja">${pill('no se publica', 'error')}<b class="dia-h">Sensores en viviendas</b>
          <p>Coordenada + edificio + nombre de la caja pueden señalar una casa y cuándo está vacía.</p>
          <p class="acento">Decisión: a ~110 m, sin nombre y con medianas de al menos 2 sensores.</p></div>
        <div class="caja">${pill('no se publica', 'error')}<b class="dia-h">Tiempo real de BKK (F16)</b>
          <p>Licencia abierta, pero exige registro y una clave personal: no atamos el lago a ella.</p>
          <p class="acento">Costo: medimos lo programado (37 622 viajes), no si el tranvía llega a tiempo.</p></div>
      </div>
      <div class="caja banda">
        <b class="dia-h">Lo que el mapa no ve</b>
        <p>11 distritos, 594 910 habitantes, sin dato de aire ciudadano (menos de 2 sensores).</p>
        <p>El V parece el mejor servido: 877 salidas por 1 000 residentes, pero solo cuenta a 23 508.</p>
      </div>` },

    { turno: 3, ante: 'Tres herramientas, los mismos datos', titulo: 'Casi elegimos Leaflet: perdió solo por el 3D', html: `
      <div class="col3">
        <div class="caja">${pill('elegida', 'estado-derivado')}<b class="dia-h">MapLibre GL JS</b><p class="q">4.7.1 · licencia BSD-3</p>
          <p class="mini">Resolvió</p><p>Edificios 3D, cámara inclinada y Copernicus.</p>
          <p class="mini">No resolvió</p><p>No hace gráficos y necesita WebGL.</p></div>
        <div class="caja">${pill('casi elegida', 'candidata')}<b class="dia-h">Leaflet</b><p class="q">1.9.4 · licencia BSD-2</p>
          <p class="mini">Resolvió</p><p>Mismos datos en 156 ms; código más corto.</p>
          <p class="mini">No resolvió</p><p>Sin 3D ni cámara inclinada salvo con plugins.</p></div>
        <div class="caja">${pill('descartada', 'pendiente')}<b class="dia-h">Observable Plot</b><p class="q">0.6.17 · licencia ISC</p>
          <p class="mini">Resolvió</p><p>3 gráficos en 157 ms, con tooltips.</p>
          <p class="mini">No resolvió</p><p>Suma 2 dependencias para lo que ya hace nuestro SVG.</p></div>
      </div>
      <div class="caja banda">
        <b class="dia-h">¿Qué tendría que cambiar?</b>
        <p>Si el gemelo fuera solo una coropleta, ganaría Leaflet; si crecen los gráficos, entra Plot.</p>
      </div>` },

    { turno: 3, ante: 'Seguridad', titulo: 'Probamos la compuerta como alguien de afuera', html: `
      <div class="col2">
        <div class="caja banda">
          <b class="dia-h">Con curl, sin sesión (2026-10-22)</b>
          <table class="terminal">
            <tr><td>/api/datos?f=temas/…</td><td>401</td></tr>
            <tr><td>/api/datos?f=../.env.example</td><td>401</td></tr>
            <tr><td>/datalake/silver/budapest.sqlite</td><td>404</td></tr>
            <tr><td>/api/entrar, clave errada</td><td>401</td></tr>
            <tr><td>grep -r clave web/public</td><td>no aparece</td></tr>
          </table>
          <p>La clave no viaja al navegador: solo vive en las variables de entorno de Vercel.</p>
        </div>
        <div class="caja">
          <b class="dia-h">Lo que parece protegido sin estarlo</b>
          <ol class="riesgos">
            <li><p>Sin bloqueo por intentos fallidos, solo 0,6 s de espera por intento.</p><p class="acento">Regla: clave larga.</p></li>
            <li><p>La clave de prueba sigue en el historial de commits del repo.</p><p class="acento">Regla: la de producción es otra.</p></li>
            <li><p>Protege nuestro lago curado, no el origen: las 12 fuentes son públicas.</p><p class="acento">Es gobierno de datos, no secreto.</p></li>
          </ol>
        </div>
      </div>` },

    { turno: 3, ante: 'Bitácora de IA', titulo: 'Lo que la IA nos dio mal, y cómo lo supimos', html: `
      <div class="col-ia">
        <div class="caja banda grande"><p><b class="dia-xl acento">7</b> <b class="dia-cifra">de 18</b></p>
          <p>encargos con un error de la IA</p><p class="q">Bitácora del README, #2–#19</p></div>
        <div class="filas">
          <div class="caja fila">${pill('incorrecto', 'error')}<div><b class="dia-h">Licencias escritas de memoria</b><p class="q">5 de 12 no coincidían con el publicador (#9).</p></div></div>
          <div class="caja fila">${pill('inventado', 'candidata')}<div><b class="dia-h">Una URL de Bubi con formato creíble</b><p class="q">Devolvió 404; quedó registrada como F18 (#10).</p></div></div>
          <div class="caja fila">${pill('incorrecto', 'error')}<div><b class="dia-h">Estaciones Bubi contadas desde OSM</b><p class="q">Contó 228; 8 eran tiendas privadas: son 220 (#11).</p></div></div>
          <div class="caja fila">${pill('incorrecto', 'error')}<div><b class="dia-h">Su propio CSS en el teléfono</b><p class="q">Página de 434 px en una pantalla de 375 px (#15).</p></div></div>
        </div>
      </div>
      <div class="caja banda">
        <b class="dia-h">Los encontramos midiendo</b>
        <p>La IA acierta al buscar; falla al afirmar sin comprobar y en el código que escribe.</p>
      </div>` },

    { turno: 3, cierre: true, ante: 'Cierre', titulo: 'Tres respuestas, una regla', html: `
      <dl class="respuestas">
        <dt>¿Qué casi elegimos?</dt><dd>Leaflet: perdió solo porque el gemelo necesita edificios 3D.</dd>
        <dt>¿Qué no mostramos?</dt><dd>Sensores exactos (señalan una casa) y el tiempo real de BKK.</dd>
        <dt>¿Qué lo cambiaría?</dt><dd>Sensores institucionales, tiempo real sin clave o un gemelo sin 3D.</dd>
      </dl>
      <div class="caja banda lema"><b>12 fuentes abiertas · 23 distritos · ninguna cifra sin su fuente</b><p class="q">Gracias. ¿Preguntas?</p></div>` },
  ];

  let i = 0, dias = [];

  function ir(n) {
    i = Math.max(0, Math.min(DIAS.length - 1, n));
    dias.forEach((d, k) => { d.hidden = k !== i; });
    $('#presNum').textContent = `${i + 1} / ${DIAS.length}`;
    $('#presAnt').disabled = i === 0; $('#presSig').disabled = i === DIAS.length - 1;
    $('#presPuntos').querySelectorAll('button').forEach((b, k) => b.setAttribute('aria-current', k === i));
  }

  function cronometro() {
    const b = $('#presReloj'); let inicio = null, acumulado = 0, timer = null;
    const pintar = () => {
      const s = Math.floor((acumulado + (inicio ? Date.now() - inicio : 0)) / 1000);
      b.textContent = `${inicio ? '❚❚' : '▶'} ${String(Math.floor(s / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`;
      b.classList.toggle('error', s >= 12 * 60);
    };
    b.addEventListener('click', () => {
      if (inicio) { acumulado += Date.now() - inicio; inicio = null; clearInterval(timer); }
      else { inicio = Date.now(); timer = setInterval(pintar, 500); }
      pintar();
    });
    $('#presReiniciar').addEventListener('click', () => { acumulado = 0; if (inicio) inicio = Date.now(); pintar(); });
    pintar();
  }

  window.PRESENTACION = {
    init() {
      const lienzo = $('#presLienzo'), escena = $('#presEscena'), sec = $('#presentacion');
      lienzo.innerHTML = DIAS.map((d, k) => {
        const [orador, tiempo] = d.cierre ? ['Juan José Botero · Santiago Idárraga · Samuel Villa', TURNOS[3][1]] : TURNOS[d.turno];
        const cabeza = d.portada ? '' : `<header><p class="dia-ante">${d.ante}</p><h2>${d.titulo}</h2></header>`;
        return `<article class="dia${d.portada ? ' portada' : ''}" role="group" aria-roledescription="diapositiva" aria-label="${k + 1} de ${DIAS.length}: ${d.titulo}" hidden>
          ${cabeza}<div class="dia-cuerpo">${d.html}</div>
          <footer class="dia-pie"><span>${orador}</span><span>${tiempo} · ${k + 1} / ${DIAS.length}</span></footer></article>`;
      }).join('');
      dias = [...lienzo.querySelectorAll('.dia')];
      $('#presPuntos').innerHTML = DIAS.map((d, k) => `<button type="button" title="${k + 1}. ${d.titulo}" aria-label="Ir a la diapositiva ${k + 1}"></button>`).join('');
      $('#presPuntos').querySelectorAll('button').forEach((b, k) => b.addEventListener('click', () => ir(k)));
      $('#presAnt').addEventListener('click', () => ir(i - 1));
      $('#presSig').addEventListener('click', () => ir(i + 1));
      $('#presPantalla').addEventListener('click', () => document.fullscreenElement ? document.exitFullscreen() : escena.requestFullscreen && escena.requestFullscreen());
      document.addEventListener('fullscreenchange', () => { $('#presPantalla').textContent = document.fullscreenElement === escena ? 'Salir de pantalla completa' : 'Pantalla completa'; });
      // Flechas cuando la sección está a la vista; en pantalla completa también Re Pág/Av Pág (los punteros de presentación), espacio, Inicio y Fin
      document.addEventListener('keydown', e => {
        if (/^(input|textarea|select)$/i.test(e.target.tagName) || e.ctrlKey || e.metaKey || e.altKey) return;
        const pantalla = document.fullscreenElement === escena, r = sec.getBoundingClientRect();
        if (!pantalla && !(r.top < innerHeight * .5 && r.bottom > innerHeight * .5)) return;
        const paso = { ArrowRight: 1, ArrowLeft: -1, ...(pantalla ? { PageDown: 1, PageUp: -1, ' ': 1 } : {}) }[e.key];
        if (paso) { e.preventDefault(); ir(i + paso); }
        else if (pantalla && (e.key === 'Home' || e.key === 'End')) { e.preventDefault(); ir(e.key === 'Home' ? 0 : DIAS.length - 1); }
      });
      cronometro();
      ir(0);
    },
  };
})();
