"""
dxf_to_section.py — Lee un DXF de sección (perfil de talud) y produce el
polígono cerrado (lista de vértices CCW) que consume el modelo MPM, además del
nivel freático (NF) si está en una capa.

Resuelve la integración con la "Sección A-A" real: reemplaza el stand-in
paramétrico de `meshgen.load_section_polygon()`.

Uso CLI (inspección — correr al recibir el DXF):
    python dxf_to_section.py "<ruta.dxf>"
        -> imprime capas, tipos de entidad, polilíneas (capa, #ptos, largo, bbox)

API:
    summarize(path)                      -> dict con capas/entidades/polilíneas
    section_polygon_from_dxf(path, ...)  -> (poly, nf_y, meta)
"""
import sys
import math
import numpy as np

try:
    import ezdxf
except ImportError:
    ezdxf = None


def _poly_points(e):
    """Devuelve [(x,y),...] de LWPOLYLINE / POLYLINE / LINE."""
    t = e.dxftype()
    if t == "LWPOLYLINE":
        return [(p[0], p[1]) for p in e.get_points("xy")]
    if t == "POLYLINE":
        return [(v.dxf.location.x, v.dxf.location.y) for v in e.vertices]
    if t == "LINE":
        return [(e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)]
    return []


def _length(pts):
    return sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))


def extract_polylines(path):
    """Lista de dicts: {layer, type, pts, npts, length, bbox}."""
    doc = ezdxf.readfile(path)
    msp = doc.modelspace()
    out = []
    for e in msp.query("LWPOLYLINE POLYLINE LINE"):
        pts = _poly_points(e)
        if len(pts) < 2:
            continue
        a = np.array(pts)
        out.append({
            "layer": getattr(e.dxf, "layer", "0"),
            "type": e.dxftype(),
            "pts": pts,
            "npts": len(pts),
            "length": _length(pts),
            "bbox": (float(a[:, 0].min()), float(a[:, 1].min()),
                     float(a[:, 0].max()), float(a[:, 1].max())),
        })
    return out


def summarize(path):
    doc = ezdxf.readfile(path)
    msp = doc.modelspace()
    layers = [l.dxf.name for l in doc.layers]
    counts = {}
    for e in msp:
        counts[e.dxftype()] = counts.get(e.dxftype(), 0) + 1
    polys = sorted(extract_polylines(path), key=lambda d: -d["length"])
    return {"layers": layers, "entity_counts": counts, "polylines": polys}


def _normalize(pts, runout_pad, margin):
    """Orienta el perfil con el pie (cota menor) hacia +x para dejar runout a la
    derecha; traslada a origen con margen. Devuelve (surface, base_y, x_left)."""
    P = np.array(sorted(pts, key=lambda p: p[0]), dtype=float)
    # si el perfil desciende hacia la izquierda, espejar en x (pie a la derecha)
    if P[0, 1] < P[-1, 1]:
        P[:, 0] = -P[:, 0]
        P = P[np.argsort(P[:, 0])]
    # trasladar: x_min -> margin, y_min -> 0 (base se calcula aparte)
    P[:, 0] -= P[:, 0].min() - margin
    return P


def section_polygon_from_dxf(path, profile_layer=None, nf_layer=None,
                             base_margin=2.0, side_margin=2.0, runout_pad=12.0):
    """Construye el polígono cerrado del cuerpo de suelo a partir del perfil.

    profile_layer : capa de la superficie del talud (si None, usa la polilínea
                    más larga — heurística robusta para un perfil de sección).
    nf_layer      : capa del nivel freático (opcional).
    Devuelve (poly[CCW], nf_y|None, meta).
    """
    polys = extract_polylines(path)
    if not polys:
        raise SystemExit("DXF sin polilíneas/líneas legibles")

    if profile_layer:
        cand = [p for p in polys if p["layer"] == profile_layer]
        if not cand:
            raise SystemExit(f"capa '{profile_layer}' sin polilíneas")
        surf = max(cand, key=lambda d: d["length"])
    else:
        surf = max(polys, key=lambda d: d["length"])  # la más larga = perfil

    S = _normalize(surf["pts"], runout_pad, side_margin)
    base_y = float(S[:, 1].min()) - base_margin
    # cuerpo de suelo: superficie (izq->der) + baja a base + recorre base a izq
    poly = [(float(x), float(y)) for x, y in S]
    poly.append((float(S[-1, 0]), base_y))   # esquina inferior derecha (pie)
    poly.append((float(S[0, 0]), base_y))    # esquina inferior izquierda
    # nivel freático
    nf_y = None
    if nf_layer:
        nfp = [p for p in polys if p["layer"] == nf_layer]
        if nfp:
            allpts = np.array([pt for p in nfp for pt in p["pts"]], dtype=float)
            nf_y = float(np.median(allpts[:, 1]))  # cota representativa del NF
    meta = {
        "profile_layer": surf["layer"], "npts": len(S),
        "x_range": (float(S[:, 0].min()), float(S[:, 0].max())),
        "y_range": (base_y, float(S[:, 1].max())),
        "runout_pad": runout_pad,
    }
    return poly, nf_y, meta


def _cli(path):
    s = summarize(path)
    print("== CAPAS ==", s["layers"])
    print("== ENTIDADES ==", s["entity_counts"])
    print("== POLILÍNEAS (por largo) ==")
    for p in s["polylines"][:20]:
        bb = p["bbox"]
        print(f"  capa='{p['layer']}' {p['type']} npts={p['npts']} "
              f"len={p['length']:.2f} bbox=({bb[0]:.1f},{bb[1]:.1f})-({bb[2]:.1f},{bb[3]:.1f})")
    poly, nf_y, meta = section_polygon_from_dxf(path)
    print("== SECCIÓN (auto: polilínea más larga) ==")
    print("  meta:", meta, "NF_y:", nf_y)
    print(f"  polígono: {len(poly)} vértices")


if __name__ == "__main__":
    if ezdxf is None:
        raise SystemExit("falta ezdxf: pip install ezdxf")
    if len(sys.argv) < 2:
        raise SystemExit("uso: python dxf_to_section.py <archivo.dxf>")
    _cli(sys.argv[1])
