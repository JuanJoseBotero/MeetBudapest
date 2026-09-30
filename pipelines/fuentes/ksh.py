"""KSH: series de alto valor (API HVD, SDMX-CSV) y Helységnévtár (población/viviendas por distrito)."""
import csv
import datetime as dt
import io
import re

from pipelines import config
from pipelines.lib import formatos, lago

F = "ksh"
BASE = "https://data.ksh.hu/datasets/{ds}/data/{rec}.csv"
# clave -> (dataset, recurso)  (ids descubiertos en metadata.rdf de cada dataset HVD)
RECURSOS = {
    "poblacion_edad_sexo": ("f44d314b-bc27-40a7-b34e-af01b3c4ab05", "eb3e481e-6b5a-45d1-8076-18c4ece155c2"),
    "edad_mediana": ("f44d314b-bc27-40a7-b34e-af01b3c4ab05", "093d149c-9951-4dd0-99ae-4a5e858a7b45"),
    "natalidad": ("4e8d4137-0962-4dfe-9d06-ca9d38ec6301", "d96c6d1d"),
    "mortalidad": ("fc86b7eb-f813-424f-baea-a32d65e1fdec", "d442dc4c"),
    "esperanza_vida": ("fc86b7eb-f813-424f-baea-a32d65e1fdec", "169201f0"),
    "mortalidad_infantil": ("fc86b7eb-f813-424f-baea-a32d65e1fdec", "99ac9e47"),
}
HNT = "https://www.ksh.hu/docs/helysegnevtar/hnt_letoltes_{anio}.xlsx"
GEOS = {"HU", "HU1", "HU11", "HU110"}


def _resolver(ds, prefijo):
    """Algunos ids se guardan abreviados: se resuelven contra el RDF del dataset."""
    if len(prefijo) == 36:
        return prefijo
    rdf = lago.http(f"https://data.ksh.hu/datasets/{ds}/metadata.rdf").decode("utf-8", "replace")
    m = re.search(rf"data/({prefijo}[0-9a-f-]+)\.csv", rdf)
    if not m:
        raise RuntimeError(f"recurso {prefijo} no encontrado en {ds}")
    return m.group(1)


def ingestar():
    n = 0
    for clave, (ds, rec) in RECURSOS.items():
        try:
            rec = _resolver(ds, rec)
            url = BASE.format(ds=ds, rec=rec)
            lago.guardar_bronze(F, f"hvd_{clave}.csv", lago.http(url, timeout=180), url)
            n += 1
            lago.log(F, f"HVD {clave}")
        except Exception as e:  # noqa: BLE001
            lago.log(F, f"HVD {clave} ERROR {e}")
    for anio in range(dt.date.today().year, 2019, -1):
        try:
            url = HNT.format(anio=anio)
            lago.guardar_bronze(F, f"helysegnevtar_{anio}.xlsx", lago.http(url, timeout=180), url)
            lago.log(F, f"Helységnévtár {anio}")
            n += 1
        except Exception:  # noqa: BLE001 - la edición del año puede no existir aún
            continue
    return {"archivos": n}


def silver(con):
    # KSH publica natalidad y mortalidad bruta en un mismo archivo (GBIRTHRT + GDEATHRT) bajo ambos datasets:
    # se deduplica por (indicador, geo, año, sexo, edad) conservando el primer recurso.
    filas, vistos = [], set()
    for clave in RECURSOS:
        p = lago.ultimo_bronze(F, f"hvd_{clave}.csv")
        if not p:
            continue
        lector = csv.DictReader(io.StringIO(p.read_text(encoding="utf-8-sig")), delimiter=";")
        for r in lector:
            if r.get("GEO") not in GEOS or r.get("FREQ", "A") != "A":
                continue
            v = lago.num(r.get("VALUES"))
            if v is None:
                continue
            fila = {"recurso": clave, "indicador": r.get("INDIC_DE") or r.get("UNIT"), "geo": r["GEO"],
                    "anio": int(r["TIME"]), "sexo": r.get("SEX", "T"), "edad": r.get("AGE", "TOTAL"), "valor": v}
            k = (fila["indicador"], r.get("UNIT"), fila["geo"], fila["anio"], fila["sexo"], fila["edad"])
            if k not in vistos:
                vistos.add(k)
                filas.append(fila)
    lago.escribir_tabla(con, "ksh_hvd", filas)
    lago.log(F, f"silver ksh_hvd: {len(filas)}")

    hist = []
    for p in sorted((config.BRONZE / F).glob("*/helysegnevtar_*.xlsx")):
        anio = int(re.search(r"(\d{4})", p.name).group(1))
        if any(h["anio"] == anio for h in hist):
            continue
        for fila in formatos.leer_xlsx(p, 0):
            m = re.match(r"Budapest (\d{2})\. ker\.", fila[0] if fila else "")
            if m:
                hist.append({"distrito_id": int(m.group(1)), "anio": anio, "ksh_codigo": fila[1],
                             "area_ha": lago.num(fila[9]), "poblacion": int(lago.num(fila[10]) or 0) or None,
                             "viviendas": int(lago.num(fila[11]) or 0) or None})
    lago.escribir_tabla(con, "ksh_distritos_historico", hist)
    lago.log(F, f"silver ksh_distritos_historico: {len(hist)}")
