// POST /api/entrar {clave} → cookie de sesión si la clave coincide con CLAVE_ACCESO.
const { crearCookie, iguales } = require('./_sesion');

module.exports = async (req, res) => {
  if (req.method !== 'POST') return res.status(405).json({ ok: false, error: 'Método no permitido' });
  let cuerpo = req.body;
  if (typeof cuerpo === 'string') { try { cuerpo = JSON.parse(cuerpo); } catch (_) { cuerpo = {}; } }
  const clave = (cuerpo && cuerpo.clave) || '';
  if (!process.env.CLAVE_ACCESO) return res.status(500).json({ ok: false, error: 'Servidor sin CLAVE_ACCESO configurada' });
  if (!iguales(clave, process.env.CLAVE_ACCESO)) {
    await new Promise(r => setTimeout(r, 600)); // frena la fuerza bruta
    return res.status(401).json({ ok: false, error: 'Clave incorrecta' });
  }
  res.setHeader('Set-Cookie', crearCookie());
  res.setHeader('Cache-Control', 'no-store');
  return res.status(200).json({ ok: true });
};
