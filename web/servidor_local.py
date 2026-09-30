"""Servidor de desarrollo sin dependencias: sirve web/public y replica /api/entrar, /api/sesion y /api/datos.

    python web/servidor_local.py            → http://localhost:8080
Lee CLAVE_ACCESO y SECRETO_SESION de las variables de entorno, de web/.env o, en su defecto, de web/.env.example.
"""
import base64
import hashlib
import hmac
import http.server
import json
import os
import re
import time
import urllib.parse
from pathlib import Path

WEB = Path(__file__).resolve().parent
PUBLICO, LAGO = WEB / "public", WEB / "lago"
PERMITIDO = re.compile(r"^(temas|geo)/[a-z0-9_]+\.(json|geojson)$")
COOKIE, DURACION = "cb_sesion", 7 * 24 * 3600


def cargar_entorno():
    for nombre in (".env", ".env.example"):
        p = WEB / nombre
        if p.exists():
            for linea in p.read_text(encoding="utf-8").splitlines():
                if "=" in linea and not linea.lstrip().startswith("#"):
                    k, v = linea.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())
            if nombre == ".env.example":
                print("AVISO: usando las credenciales de prueba de web/.env.example")
            return


def _firma(expira):
    s = (os.environ.get("SECRETO_SESION") or os.environ["CLAVE_ACCESO"]).encode()
    return base64.urlsafe_b64encode(hmac.new(s, str(expira).encode(), hashlib.sha256).digest()).rstrip(b"=").decode()


class Manejador(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(PUBLICO), **kw)

    def end_headers(self):
        # en desarrollo, que el navegador revalide siempre los estáticos (evita CSS/JS viejos en caché)
        if not self.path.startswith("/api/"):
            self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def _json(self, codigo, obj, cookie=None):
        b = json.dumps(obj).encode()
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        if cookie:
            self.send_header("Set-Cookie", cookie)
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def _sesion(self):
        m = re.search(COOKIE + r"=([^;]+)", self.headers.get("Cookie", ""))
        if not m or "." not in m.group(1):
            return False
        expira, firma = m.group(1).split(".", 1)
        return expira.isdigit() and int(expira) > time.time() and hmac.compare_digest(firma, _firma(expira))

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        if u.path == "/api/sesion":
            return self._json(200, {"abierta": self._sesion()})
        if u.path == "/api/datos":
            if not self._sesion():
                return self._json(401, {"error": "Sesión requerida"})
            f = urllib.parse.parse_qs(u.query).get("f", [""])[0]
            ruta = (LAGO / f).resolve()
            if not PERMITIDO.match(f) or not str(ruta).startswith(str(LAGO.resolve())) or not ruta.exists():
                return self._json(404, {"error": "No existe en el lago"})
            b = ruta.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "private, no-store")
            self.send_header("Content-Length", str(len(b)))
            self.end_headers()
            return self.wfile.write(b)
        return super().do_GET()

    def do_POST(self):
        u = urllib.parse.urlparse(self.path)
        if u.path == "/api/entrar":
            n = int(self.headers.get("Content-Length") or 0)
            try:
                clave = json.loads(self.rfile.read(n) or b"{}").get("clave", "")
            except ValueError:
                clave = ""
            if not hmac.compare_digest(hashlib.sha256(clave.encode()).digest(), hashlib.sha256(os.environ["CLAVE_ACCESO"].encode()).digest()):
                time.sleep(0.6)
                return self._json(401, {"ok": False, "error": "Clave incorrecta"})
            expira = int(time.time()) + DURACION
            return self._json(200, {"ok": True}, f"{COOKIE}={expira}.{_firma(expira)}; Path=/; HttpOnly; SameSite=Lax; Max-Age={DURACION}")
        if u.path == "/api/sesion":
            return self._json(200, {"abierta": False}, f"{COOKIE}=; Path=/; Max-Age=0")
        self.send_error(404)

    def log_message(self, fmt, *args):
        if "/api/" in (args[0] if args else ""):
            super().log_message(fmt, *args)


if __name__ == "__main__":
    cargar_entorno()
    puerto = int(os.environ.get("PUERTO", "8080"))
    print(f"Cerebro Budapest en http://localhost:{puerto}")
    http.server.ThreadingHTTPServer(("0.0.0.0", puerto), Manejador).serve_forever()
