"""Utilidades del lago: HTTP con reintentos, escritura en bronze con linaje, SQLite de silver y JSON de gold."""
import datetime as dt
import gzip
import hashlib
import json
import sqlite3
import time
import urllib.error
import urllib.parse
import urllib.request

from pipelines import config
from pipelines.esquema import ESQUEMA

HOY = dt.date.today().isoformat()


def ahora():
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def log(fuente, msg):
    print(f"[{dt.datetime.now():%H:%M:%S}] {fuente:<16} {msg}", flush=True)


# ---------------------------------------------------------------- HTTP
def http(url, params=None, data=None, json_body=None, headers=None, timeout=120, reintentos=3):
    """GET/POST con reintentos exponenciales. Devuelve bytes."""
    if params:
        url += ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
    h = {"User-Agent": config.USER_AGENT, "Accept-Encoding": "gzip"}
    h.update(headers or {})
    cuerpo = None
    if json_body is not None:
        cuerpo = json.dumps(json_body).encode()
        h["Content-Type"] = "application/json"
    elif data is not None:
        cuerpo = urllib.parse.urlencode(data).encode()
        h["Content-Type"] = "application/x-www-form-urlencoded"
    ultimo = None
    for intento in range(reintentos):
        try:
            req = urllib.request.Request(url, data=cuerpo, headers=h)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                b = r.read()
                if r.headers.get("Content-Encoding") == "gzip":
                    b = gzip.decompress(b)
                return b
        except urllib.error.HTTPError as e:
            ultimo = e
            if e.code in (400, 401, 403, 404):
                raise
        except Exception as e:  # red, timeout
            ultimo = e
        time.sleep(4 * (intento + 1))
    raise ultimo


def http_json(url, **kw):
    return json.loads(http(url, **kw).decode("utf-8"))


# ---------------------------------------------------------------- BRONZE
def ruta_bronze(fuente, nombre, fecha=HOY):
    p = config.BRONZE / fuente / fecha / nombre
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def guardar_bronze(fuente, nombre, contenido, url=""):
    """Escribe un archivo crudo e inmutable y registra su linaje (url, bytes, sha256, hora)."""
    if isinstance(contenido, str):
        contenido = contenido.encode("utf-8")
    p = ruta_bronze(fuente, nombre)
    p.write_bytes(contenido)
    registrar_linaje(fuente, p, url, len(contenido), hashlib.sha256(contenido).hexdigest())
    return p


def registrar_linaje(fuente, ruta, url, n_bytes, sha):
    config.CATALOGO.mkdir(parents=True, exist_ok=True)
    fila = {"ts": ahora(), "fuente": fuente, "archivo": ruta.relative_to(config.LAGO).as_posix(),
            "url": url, "bytes": n_bytes, "sha256": sha}
    with open(config.CATALOGO / "linaje.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(fila, ensure_ascii=False) + "\n")


def ultimo_bronze(fuente, nombre):
    """Ruta de la ingesta más reciente de un archivo (las carpetas de fecha ordenan lexicográficamente)."""
    base = config.BRONZE / fuente
    if not base.exists():
        return None
    for fecha in sorted((d.name for d in base.iterdir() if d.is_dir()), reverse=True):
        p = base / fecha / nombre
        if p.exists():
            return p
    return None


def leer_bronze_json(fuente, nombre):
    p = ultimo_bronze(fuente, nombre)
    return (json.loads(p.read_text(encoding="utf-8")), p.parent.name) if p else (None, None)


# ---------------------------------------------------------------- SILVER (SQLite)
def conectar():
    config.SILVER.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(config.SQLITE)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    return con


def _ddl(tabla):
    cols = ESQUEMA[tabla]["columnas"]
    return f'CREATE TABLE IF NOT EXISTS {tabla} (' + ", ".join(f'"{c[0]}" {c[1]}' for c in cols) + ")"


def escribir_tabla(con, tabla, filas, modo="reemplazar"):
    """Escribe filas (dicts) en una tabla declarada en esquema.py. Rechaza columnas no documentadas."""
    if tabla not in ESQUEMA:
        raise KeyError(f"Tabla {tabla} no está en el diccionario (pipelines/esquema.py)")
    nombres = [c[0] for c in ESQUEMA[tabla]["columnas"]]
    if modo == "reemplazar":
        con.execute(f"DROP TABLE IF EXISTS {tabla}")
    con.execute(_ddl(tabla))
    # tablas acumulativas: si el esquema ganó columnas, se añaden sin perder el histórico
    existentes = {r[1] for r in con.execute(f"PRAGMA table_info({tabla})")}
    for c in ESQUEMA[tabla]["columnas"]:
        if c[0] not in existentes:
            con.execute(f'ALTER TABLE {tabla} ADD COLUMN "{c[0]}" {c[1].replace("PRIMARY KEY", "")}')
    filas = list(filas)
    for f in filas[:1]:
        extra = set(f) - set(nombres)
        if extra:
            raise KeyError(f"{tabla}: columnas no documentadas {extra}")
    con.executemany(
        f'INSERT INTO {tabla} VALUES ({",".join("?" * len(nombres))})',
        ([f.get(n) for n in nombres] for f in filas),
    )
    con.commit()
    return len(filas)


def tabla_existe(con, tabla):
    return con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (tabla,)).fetchone() is not None


def consultar(con, sql, *args):
    return [dict(r) for r in con.execute(sql, args)]


# ---------------------------------------------------------------- GOLD
def escribir_json(ruta, obj):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return ruta


def num(v):
    """Convierte textos numéricos de las fuentes (coma decimal, ':' = faltante) a float o None."""
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().strip('"').replace(" ", "").replace(" ", "")
    if s in ("", ":", "-", "..", "NaN", "null"):
        return None
    s = s.split(" ")[0]
    if "," in s and "." not in s:
        s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None
