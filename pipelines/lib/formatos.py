"""Lectores de formatos sin dependencias: XLSX (Office Open XML) y JSON-stat 2.0 (Eurostat)."""
import itertools
import re
import xml.etree.ElementTree as ET
import zipfile

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
      "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}


def leer_xlsx(ruta, hoja=0):
    """Devuelve las filas de una hoja como listas de textos (celdas vacías = '')."""
    z = zipfile.ZipFile(ruta)
    comp = []
    if "xl/sharedStrings.xml" in z.namelist():
        comp = ["".join(si.itertext()) for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", NS)]
    wb = ET.fromstring(z.read("xl/workbook.xml"))
    hojas = wb.find("m:sheets", NS)
    rid = list(hojas)[hoja].get("{%s}id" % NS["r"])
    rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    destino = next(r.get("Target") for r in rels if r.get("Id") == rid).lstrip("/")
    destino = destino if destino.startswith("xl/") else "xl/" + destino
    sh = ET.fromstring(z.read(destino))
    filas = []
    for r in sh.find("m:sheetData", NS):
        fila = {}
        for c in r:
            col = re.match(r"[A-Z]+", c.get("r")).group(0)
            idx = 0
            for ch in col:
                idx = idx * 26 + ord(ch) - 64
            v = c.find("m:v", NS)
            if v is None:
                isv = c.find("m:is", NS)
                val = "".join(isv.itertext()) if isv is not None else ""
            else:
                val = comp[int(v.text)] if c.get("t") == "s" else v.text
            fila[idx - 1] = val
        filas.append([fila.get(i, "") for i in range(max(fila) + 1)] if fila else [])
    return filas


def jsonstat_filas(d):
    """Aplana un dataset JSON-stat 2.0 en dicts {dim: código, ..., 'valor': x, 'flag': s}."""
    ids, tam = d["id"], d["size"]
    cats = []
    for dim in ids:
        idx = d["dimension"][dim]["category"]["index"]
        orden = sorted(idx, key=idx.get) if isinstance(idx, dict) else idx
        cats.append(orden)
    valores, estados = d.get("value", {}), d.get("status", {})
    etiquetas = {dim: d["dimension"][dim]["category"].get("label", {}) for dim in ids}
    for pos, combo in enumerate(itertools.product(*cats)):
        v = valores.get(str(pos)) if isinstance(valores, dict) else (valores[pos] if pos < len(valores) else None)
        if v is None:
            continue
        fila = dict(zip(ids, combo))
        fila["valor"] = v
        fila["flag"] = estados.get(str(pos)) if isinstance(estados, dict) else None
        fila["_etiquetas"] = {dim: etiquetas[dim].get(c, c) for dim, c in zip(ids, combo)}
        yield fila
