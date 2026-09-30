"""OpenStreetMap vía Overpass: límites de los 23 distritos, puntos de interés y conteo de edificios."""
import json
import time

from pipelines import config
from pipelines.lib import geo, lago

F = "osm_overpass"
ENDPOINTS = ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter"]
AREA_BP = 'area["name"="Budapest"]["boundary"="administrative"]->.bp;'

ROMANOS = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII", "XIII", "XIV", "XV", "XVI",
           "XVII", "XVIII", "XIX", "XX", "XXI", "XXII", "XXIII"]
APODOS = {1: "Várkerület", 2: "Hegyvidék-Pesthidegkút", 3: "Óbuda-Békásmegyer", 4: "Újpest", 5: "Belváros-Lipótváros",
          6: "Terézváros", 7: "Erzsébetváros", 8: "Józsefváros", 9: "Ferencváros", 10: "Kőbánya", 11: "Újbuda",
          12: "Hegyvidék", 13: "Angyalföld-Újlipótváros", 14: "Zugló", 15: "Rákospalota-Pestújhely-Újpalota",
          16: "Mátyásföld-Sashalom", 17: "Rákosmente", 18: "Pestszentlőrinc-Pestszentimre", 19: "Kispest",
          20: "Pesterzsébet", 21: "Csepel", 22: "Budafok-Tétény", 23: "Soroksár"}
BUDA = {1, 2, 3, 11, 12, 22}

# categoría del sitio -> (clave OSM, valores)
CATEGORIAS = {
    "educacion": ("amenity", ["school", "kindergarten", "university", "college", "library"]),
    "salud": ("amenity", ["hospital", "clinic", "doctors", "pharmacy", "dentist"]),
    "cultura": ("amenity", ["theatre", "cinema", "arts_centre", "concert_hall"]),
    "gastronomia": ("amenity", ["restaurant", "cafe", "bar", "pub", "fast_food"]),
    "seguridad": ("amenity", ["police", "fire_station"]),
    "administracion": ("amenity", ["townhall", "courthouse", "post_office", "marketplace"]),
    "movilidad": ("amenity", ["bicycle_rental", "charging_station", "car_sharing"]),
    "turismo": ("tourism", ["museum", "attraction", "viewpoint", "gallery", "zoo", "theme_park"]),
    "alojamiento": ("tourism", ["hotel", "hostel", "guest_house", "apartment", "motel"]),
    "verde": ("leisure", ["park", "garden", "playground", "nature_reserve"]),
    "deporte": ("leisure", ["sports_centre", "fitness_centre", "stadium", "swimming_pool"]),
    "comercio": ("shop", ["supermarket", "mall", "convenience", "department_store"]),
}


def overpass(q, nombre):
    ultimo = None
    for ep in ENDPOINTS:
        try:
            b = lago.http(ep, data={"data": q}, timeout=300)
            lago.guardar_bronze(F, nombre, b, ep + " :: " + q[:300])
            return json.loads(b)
        except Exception as e:  # noqa: BLE001 - probamos el espejo
            ultimo = e
            lago.log(F, f"{ep} falló ({e}); probando espejo")
    raise ultimo


def ingestar():
    lago.log(F, "distritos (admin_level=9, out geom)")
    distritos = overpass(f'[out:json][timeout:240];{AREA_BP}rel(area.bp)["boundary"="administrative"]["admin_level"="9"];out geom;',
                         "distritos.json")
    time.sleep(5)
    lago.log(F, "puntos de interés")
    partes = "".join(f'nwr["{k}"~"^({"|".join(v)})$"](area.bp);' for k, v in CATEGORIAS.values())
    overpass(f"[out:json][timeout:600];{AREA_BP}({partes});out center tags;", "poi.json")
    # conteo de edificios por distrito (una consulta con out count por área)
    lago.log(F, "conteo de edificios por distrito")
    ids = [e["id"] for e in distritos["elements"] if e["type"] == "relation"]
    bloques = "".join(
        f'area(id:{3600000000 + i})->.a;way["building"](area.a)->.w;rel["building"](area.a)->.r;'
        f'(.w;.r;)->.t;.t out count;way["building"]["building:levels"](area.a);out count;' for i in ids)
    overpass(f"[out:json][timeout:900];{bloques}", "edificios_conteo.json")
    return {"archivos": 3}


def _numero(tags):
    ref = tags.get("ref")
    if ref and ref.isdigit():
        return int(ref)
    nombre = tags.get("name", "").split(".")[0].strip()
    return ROMANOS.index(nombre) + 1 if nombre in ROMANOS else None


def silver(con):
    d, fecha = lago.leer_bronze_json(F, "distritos.json")
    if not d:
        raise RuntimeError("sin bronze de distritos")
    # KSH se ingesta antes que OSM en el orquestador; si falta, los campos oficiales quedan NULL
    hist = (lago.consultar(con, "SELECT * FROM ksh_distritos_historico ORDER BY anio")
            if lago.tabla_existe(con, "ksh_distritos_historico") else [])
    ult = {}
    for r in hist:
        ult.setdefault(r["distrito_id"], []).append(r)
    filas = []
    for e in d["elements"]:
        if e["type"] != "relation":
            continue
        n = _numero(e.get("tags", {}))
        if not n:
            continue
        mp = geo.relacion_a_multipoligono(e)
        lat, lon = geo.centroide(mp)
        serie = ult.get(n, [])
        k, k0 = (serie[-1] if serie else {}), (serie[-2] if len(serie) > 1 else {})
        filas.append({
            "distrito_id": n, "nombre": e["tags"].get("name"), "romano": ROMANOS[n - 1], "apodo": APODOS[n],
            "lado": "Csepel" if n == 21 else ("Buda" if n in BUDA else "Pest"), "osm_rel_id": e["id"],
            "ksh_codigo": k.get("ksh_codigo"), "area_km2": round(geo.area_km2(mp), 3), "area_ha_ksh": k.get("area_ha"),
            "poblacion": k.get("poblacion"), "poblacion_anterior": k0.get("poblacion"), "viviendas": k.get("viviendas"),
            "anio_ksh": k.get("anio"), "centro_lat": round(lat, 6), "centro_lon": round(lon, 6),
            "geojson": json.dumps(geo.geojson_mp(mp)),
        })
    filas.sort(key=lambda f: f["distrito_id"])
    lago.escribir_tabla(con, "distritos", filas)
    lago.log(F, f"silver distritos: {len(filas)}")

    asignar = asignador(con)
    p, _ = lago.leer_bronze_json(F, "poi.json")
    inverso = {}
    for cat, (k, vals) in CATEGORIAS.items():
        for v in vals:
            inverso[(k, v)] = cat
    pois = []
    for e in (p or {}).get("elements", []):
        t = e.get("tags", {})
        lat = e.get("lat") or (e.get("center") or {}).get("lat")
        lon = e.get("lon") or (e.get("center") or {}).get("lon")
        if lat is None:
            continue
        cat = sub = None
        for (k, v), c in inverso.items():
            if t.get(k) == v:
                cat, sub = c, v
                break
        if not cat:
            continue
        pois.append({"osm_tipo": e["type"], "osm_id": e["id"], "categoria": cat, "subcategoria": sub,
                     "nombre": t.get("name"), "lat": lat, "lon": lon, "estrellas": lago.num(t.get("stars")),
                     "wikidata": t.get("wikidata"), "distrito_id": asignar(lon, lat)})
    lago.escribir_tabla(con, "osm_poi", pois)
    lago.log(F, f"silver osm_poi: {len(pois)}")

    c, _ = lago.leer_bronze_json(F, "edificios_conteo.json")
    ids = [(e["id"], _numero(e.get("tags", {}))) for e in d["elements"] if e["type"] == "relation"]
    cuentas = [int(e["tags"].get("total", 0)) for e in (c or {}).get("elements", []) if e.get("type") == "count"]
    filas_e = []
    for i, (_, n) in enumerate(ids):
        if n and 2 * i + 1 < len(cuentas):
            filas_e.append({"distrito_id": n, "edificios": cuentas[2 * i], "edificios_con_niveles": cuentas[2 * i + 1],
                            "fecha_osm": (c.get("osm3s") or {}).get("timestamp_osm_base")})
    lago.escribir_tabla(con, "osm_edificios_distrito", filas_e)
    lago.log(F, f"silver osm_edificios_distrito: {len(filas_e)}")


def asignador(con):
    return geo.Asignador([(r["distrito_id"], json.loads(r["geojson"])["coordinates"])
                          for r in lago.consultar(con, "SELECT distrito_id, geojson FROM distritos")])
