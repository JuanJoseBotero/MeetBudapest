// GET /api/sesion → {abierta}. POST /api/sesion?salir=1 cierra la sesión.
const { sesionValida, borrarCookie } = require('./_sesion');

module.exports = (req, res) => {
  res.setHeader('Cache-Control', 'no-store');
  if (req.method === 'POST' && req.query && req.query.salir) {
    res.setHeader('Set-Cookie', borrarCookie());
    return res.status(200).json({ abierta: false });
  }
  return res.status(200).json({ abierta: sesionValida(req) });
};
