// GET /api/datos?f=temas/demografia.json → archivo de la capa gold, solo con sesión válida.
const fs = require('fs');
const path = require('path');
const { sesionValida } = require('./_sesion');

const PERMITIDO = /^(temas|geo)\/[a-z0-9_]+\.(json|geojson)$/;
const RAIZ = path.join(process.cwd(), 'lago');

module.exports = (req, res) => {
  res.setHeader('Cache-Control', 'private, no-store');
  if (!sesionValida(req)) return res.status(401).json({ error: 'Sesión requerida' });
  const f = String((req.query && req.query.f) || '');
  if (!PERMITIDO.test(f)) return res.status(400).json({ error: 'Archivo no permitido' });
  const ruta = path.join(RAIZ, f);
  if (!ruta.startsWith(RAIZ) || !fs.existsSync(ruta)) return res.status(404).json({ error: 'No existe en el lago' });
  res.setHeader('Content-Type', f.endsWith('.geojson') ? 'application/geo+json; charset=utf-8' : 'application/json; charset=utf-8');
  return res.status(200).send(fs.readFileSync(ruta));
};
