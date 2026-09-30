// Sesión firmada sin estado: cookie "cb_sesion=<expira>.<hmac>". La clave vive solo en variables de entorno.
const crypto = require('crypto');

const COOKIE = 'cb_sesion';
const DURACION_S = 7 * 24 * 3600;

function secreto() {
  const s = process.env.SECRETO_SESION || process.env.CLAVE_ACCESO;
  if (!s) throw new Error('Falta CLAVE_ACCESO en las variables de entorno');
  return s;
}

function firmar(expira) {
  return crypto.createHmac('sha256', secreto()).update(String(expira)).digest('base64url');
}

function iguales(a, b) {
  const ha = crypto.createHash('sha256').update(String(a)).digest();
  const hb = crypto.createHash('sha256').update(String(b)).digest();
  return crypto.timingSafeEqual(ha, hb);
}

function leerCookie(req) {
  const m = (req.headers.cookie || '').match(new RegExp('(?:^|;\\s*)' + COOKIE + '=([^;]+)'));
  return m ? decodeURIComponent(m[1]) : null;
}

function sesionValida(req) {
  const v = leerCookie(req);
  if (!v) return false;
  const [expira, firma] = v.split('.');
  if (!expira || !firma || Number(expira) < Date.now() / 1000) return false;
  return iguales(firma, firmar(expira));
}

function crearCookie() {
  const expira = Math.floor(Date.now() / 1000) + DURACION_S;
  return `${COOKIE}=${expira}.${firmar(expira)}; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=${DURACION_S}`;
}

function borrarCookie() {
  return `${COOKIE}=; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=0`;
}

module.exports = { sesionValida, crearCookie, borrarCookie, iguales };
