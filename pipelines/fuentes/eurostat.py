"""Eurostat: indicadores regionales (NUTS 2/3) y de ciudad (Urban Audit) para Budapest vía API JSON-stat."""
import json
import urllib.parse

from pipelines.lib import formatos, lago

F = "eurostat"
API = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/"

# clave del sitio -> (dataset, filtros, unidad legible)
CONSULTAS = {
    "pib_hab_eur": ("nama_10r_3gdp", {"geo": "HU110", "unit": "EUR_HAB"}, "€/hab"),
    "pib_hab_pps_ue": ("nama_10r_2gdp", {"geo": "HU11", "unit": "PPS_EU27_2020_HAB_EU27_2020"}, "% media UE27 (PPS)"),
    "pib_meur": ("nama_10r_3gdp", {"geo": "HU110", "unit": "MIO_EUR"}, "M€"),
    "desempleo": ("lfst_r_lfu3rt", {"geo": "HU11", "sex": "T", "age": "Y20-64", "isced11": "TOTAL"}, "%"),
    "empleo": ("lfst_r_lfe2emprt", {"geo": "HU11", "sex": "T", "age": "Y20-64"}, "%"),
    "ingreso_disponible": ("tgs00026", {"geo": "HU11"}, "PPS/hab"),
    "riesgo_pobreza_exclusion": ("ilc_peps11n", {"geo": "HU11", "unit": "PC"}, "%"),
    "educacion_terciaria": ("edat_lfse_04", {"geo": "HU11", "sex": "T", "age": "Y25-64", "isced11": "ED5-8"}, "%"),
    "gasto_id_pib": ("rd_e_gerdreg", {"geo": "HU11", "sectperf": "TOTAL", "unit": "PC_GDP"}, "% PIB"),
    "densidad": ("demo_r_d3dens", {"geo": "HU110"}, "hab/km²"),
    "esperanza_vida_ue": ("demo_r_mlifexp", {"geo": "HU11", "sex": "T", "age": "Y_LT1"}, "años"),
    "pernoctaciones": ("tour_occ_nin2", {"geo": "HU11", "unit": "NR", "nace_r2": "I551-I553", "c_resid": ["TOTAL", "FOR", "DOM"]}, "noches"),
    "llegadas": ("tour_occ_arn2", {"geo": "HU11", "unit": "NR", "nace_r2": "I551-I553", "c_resid": ["TOTAL", "FOR", "DOM"]}, "llegadas"),
    "vehiculos": ("tran_r_vehst", {"geo": "HU11", "unit": "NR"}, "vehículos"),
    "precio_vivienda_hu": ("prc_hpi_q", {"geo": "HU", "purchase": "TOTAL", "unit": "I15_Q"}, "índice 2015=100"),
    "empresas": ("bd_hgnace2_r3", {"geo": "HU110", "nace_r2": "B-S_X_K642", "indic_sb": ["V11910", "V11920", "V11930"]}, "empresas"),
    "ua_poblacion": ("urb_cpop1", {"cities": "HU001C"}, "según indicador"),
    "ua_turismo": ("urb_ctour", {"cities": "HU001C"}, "según indicador"),
    "ua_trabajo": ("urb_clma", {"cities": "HU001C"}, "según indicador"),
    "ua_ambiente": ("urb_cenv", {"cities": "HU001C"}, "según indicador"),
    "ua_transporte": ("urb_ctran", {"cities": "HU001C"}, "según indicador"),
}


def _params(filtros):
    ps = [("format", "JSON"), ("lang", "en")]
    for k, v in filtros.items():
        for x in (v if isinstance(v, list) else [v]):
            ps.append((k, x))
    return ps


def ingestar():
    n = 0
    for clave, (ds, filtros, _) in CONSULTAS.items():
        url = API + ds + "?" + urllib.parse.urlencode(_params(filtros))
        try:
            lago.guardar_bronze(F, f"{clave}.json", lago.http(url, timeout=180), url)
            n += 1
        except Exception as e:  # noqa: BLE001
            lago.log(F, f"{clave} ({ds}) ERROR {e}")
    lago.log(F, f"{n}/{len(CONSULTAS)} consultas")
    return {"archivos": n}


def silver(con):
    filas = []
    for clave, (ds, _, unidad) in CONSULTAS.items():
        d, _f = lago.leer_bronze_json(F, f"{clave}.json")
        if not d:
            continue
        for r in formatos.jsonstat_filas(d):
            geo = r.get("geo") or r.get("cities")
            dims = {k: v for k, v in r.items() if k not in ("geo", "cities", "time", "freq", "valor", "flag", "_etiquetas")}
            et = r["_etiquetas"]
            etiqueta = et.get("indic_ur") or et.get("indic_sb") or et.get("vehicle") or et.get("c_resid") or d.get("label")
            filas.append({"dataset": ds, "clave": clave, "geo": geo, "periodo": r["time"], "dimensiones": json.dumps(dims),
                          "etiqueta": etiqueta, "unidad": unidad, "valor": r["valor"], "flag": r["flag"]})
    lago.escribir_tabla(con, "eurostat_obs", filas)
    lago.log(F, f"silver eurostat_obs: {len(filas)}")
