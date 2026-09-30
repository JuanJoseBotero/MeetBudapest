"""Geometría mínima sin dependencias: ensamblado de anillos OSM, punto-en-polígono, áreas, centroides y simplificación.

Convención: un MultiPolygon es una lista de polígonos; cada polígono es [anillo_exterior, *huecos];
cada anillo es una lista de [lon, lat] cerrada.
"""
import math

R_TIERRA = 6371008.8


def haversine_m(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R_TIERRA * math.asin(math.sqrt(a))


# ---------------------------------------------------------------- ensamblado de relaciones Overpass (out geom)
def _clave(p):
    return (round(p[0], 7), round(p[1], 7))


def ensamblar_anillos(segmentos):
    """Une vías (listas de [lon,lat]) por sus extremos hasta cerrar anillos."""
    pendientes = [list(s) for s in segmentos if len(s) >= 2]
    anillos = []
    while pendientes:
        actual = pendientes.pop(0)
        cambio = True
        while _clave(actual[0]) != _clave(actual[-1]) and cambio:
            cambio = False
            for i, s in enumerate(pendientes):
                if _clave(s[0]) == _clave(actual[-1]):
                    actual += s[1:]
                elif _clave(s[-1]) == _clave(actual[-1]):
                    actual += s[::-1][1:]
                elif _clave(s[-1]) == _clave(actual[0]):
                    actual = s[:-1] + actual
                elif _clave(s[0]) == _clave(actual[0]):
                    actual = s[::-1][:-1] + actual
                else:
                    continue
                pendientes.pop(i)
                cambio = True
                break
        if _clave(actual[0]) == _clave(actual[-1]) and len(actual) >= 4:
            anillos.append(actual)
    return anillos


def relacion_a_multipoligono(rel):
    """Convierte un elemento relation de Overpass (out geom) en MultiPolygon."""
    ext, inte = [], []
    for m in rel.get("members", []):
        if m.get("type") != "way" or not m.get("geometry"):
            continue
        coords = [[g["lon"], g["lat"]] for g in m["geometry"]]
        (inte if m.get("role") == "inner" else ext).append(coords)
    exteriores = ensamblar_anillos(ext)
    huecos = ensamblar_anillos(inte)
    polis = [[e] for e in exteriores]
    for h in huecos:
        for p in polis:
            if punto_en_anillo(h[0][0], h[0][1], p[0]):
                p.append(h)
                break
    return polis


# ---------------------------------------------------------------- punto en polígono
def punto_en_anillo(x, y, anillo):
    dentro = False
    j = len(anillo) - 1
    for i in range(len(anillo)):
        xi, yi = anillo[i]
        xj, yj = anillo[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-15) + xi:
            dentro = not dentro
        j = i
    return dentro


def punto_en_multipoligono(lon, lat, mp):
    for poli in mp:
        if punto_en_anillo(lon, lat, poli[0]) and not any(punto_en_anillo(lon, lat, h) for h in poli[1:]):
            return True
    return False


def bbox(mp):
    xs = [p[0] for poli in mp for p in poli[0]]
    ys = [p[1] for poli in mp for p in poli[0]]
    return min(xs), min(ys), max(xs), max(ys)


class Asignador:
    """Asigna puntos a distritos con prefiltro por bbox."""

    def __init__(self, distritos):  # distritos: [(id, multipoligono)]
        self.d = [(i, mp, bbox(mp)) for i, mp in distritos]

    def __call__(self, lon, lat):
        if lon is None or lat is None:
            return None
        for i, mp, (x0, y0, x1, y1) in self.d:
            if x0 <= lon <= x1 and y0 <= lat <= y1 and punto_en_multipoligono(lon, lat, mp):
                return i
        return None


# ---------------------------------------------------------------- áreas y centroides (proyección equirectangular local)
def _area_anillo_m2(anillo):
    lat0 = math.radians(sum(p[1] for p in anillo) / len(anillo))
    kx = math.cos(lat0) * math.pi / 180 * R_TIERRA
    ky = math.pi / 180 * R_TIERRA
    s = 0.0
    for (x1, y1), (x2, y2) in zip(anillo, anillo[1:]):
        s += (x1 * kx) * (y2 * ky) - (x2 * kx) * (y1 * ky)
    return abs(s) / 2


def area_km2(mp):
    return sum(_area_anillo_m2(p[0]) - sum(_area_anillo_m2(h) for h in p[1:]) for p in mp) / 1e6


def centroide(mp):
    """Centroide ponderado por área del anillo exterior mayor de cada polígono."""
    sx = sy = st = 0.0
    for poli in mp:
        a = poli[0]
        cx = cy = aa = 0.0
        for (x1, y1), (x2, y2) in zip(a, a[1:]):
            c = x1 * y2 - x2 * y1
            aa += c
            cx += (x1 + x2) * c
            cy += (y1 + y2) * c
        if aa:
            w = abs(aa)
            sx += cx / (3 * aa) * w
            sy += cy / (3 * aa) * w
            st += w
    return (sy / st, sx / st) if st else (None, None)  # lat, lon


# ---------------------------------------------------------------- simplificación Douglas-Peucker
def _dp(pts, tol):
    """Douglas-Peucker iterativo (sin recursión: las formas GTFS tienen miles de vértices)."""
    if len(pts) < 3:
        return pts
    conservar = [False] * len(pts)
    conservar[0] = conservar[-1] = True
    pila = [(0, len(pts) - 1)]
    while pila:
        a, b = pila.pop()
        (x0, y0), (x1, y1) = pts[a], pts[b]
        dx, dy = x1 - x0, y1 - y0
        n = math.hypot(dx, dy) or 1e-15
        idx, dmax = 0, 0.0
        for i in range(a + 1, b):
            d = abs(dy * pts[i][0] - dx * pts[i][1] + x1 * y0 - y1 * x0) / n
            if d > dmax:
                idx, dmax = i, d
        if dmax > tol:
            conservar[idx] = True
            pila += [(a, idx), (idx, b)]
    return [p for p, k in zip(pts, conservar) if k]


def simplificar_linea(pts, tol=0.0001, dec=5):
    """Douglas-Peucker; un anillo cerrado se parte por su vértice más lejano al inicio (si no, colapsa a 2 puntos)."""
    if len(pts) > 3 and _clave(pts[0]) == _clave(pts[-1]):
        x0, y0 = pts[0]
        k = max(range(len(pts)), key=lambda i: (pts[i][0] - x0) ** 2 + (pts[i][1] - y0) ** 2)
        s = _dp(pts[: k + 1], tol)[:-1] + _dp(pts[k:], tol)
    else:
        s = _dp(pts, tol)
    return [[round(x, dec), round(y, dec)] for x, y in s]


def simplificar_mp(mp, tol=0.0001, dec=5):
    out = []
    for poli in mp:
        anillos = []
        for a in poli:
            s = simplificar_linea(a, tol, dec)
            if len(s) >= 4:
                anillos.append(s)
        if anillos:
            out.append(anillos)
    return out


def area_firmada(anillo):
    """Shoelace en grados: > 0 antihorario, < 0 horario (x = lon, y = lat)."""
    return sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(anillo, anillo[1:])) / 2


def orientar(anillo, horario):
    return anillo if (area_firmada(anillo) < 0) == horario else anillo[::-1]


def anillos_esri(mp):
    """Anillos para geometrías Esri: exteriores en sentido horario y huecos antihorario (al revés que RFC 7946)."""
    return [orientar(a, i == 0) for poli in mp for i, a in enumerate(poli)]


def geojson_mp(mp):
    return {"type": "MultiPolygon", "coordinates": mp}


def feature(geom, props):
    return {"type": "Feature", "geometry": geom, "properties": props}


def punto(lon, lat, props, dec=5):
    return feature({"type": "Point", "coordinates": [round(lon, dec), round(lat, dec)]}, props)


def coleccion(feats):
    return {"type": "FeatureCollection", "features": list(feats)}
