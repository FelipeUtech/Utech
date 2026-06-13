"""
meshgen.py — Generador de malla estructurada de cuadriláteros + partículas
para cb-geo MPM (formato Ascii2D), independiente de DXF.

NOTA SOBRE LA GEOMETRÍA / DXF:
  La tarea pedía reutilizar el parser DXF de `agente-topografia` y localizar
  la "Sección A" del talud CEMEX. Ese repositorio y ese DXF NO existen en el
  entorno (ver REPORTE.md / SETUP_FAILED.md). Este módulo construye la
  geometría de forma PARAMÉTRICA: define el perfil del talud por una lista de
  vértices (polígono) que es trivial sustituir por los vértices reales de la
  Sección A cuando se disponga del DXF. La función `load_section_polygon()`
  está aislada justamente para ese reemplazo.

Formato de salida (compatible con cb-geo/mpm Ascii2D):
  mesh.txt:
      #! elementShape quadrilateral
      #! elementNumPoints 4
      <nnodes>\t<ncells>
      x y            (x nnodes)
      n0 n1 n2 n3    (x ncells, CCW: BL, BR, TR, TL)
  particles.txt:
      <nparticles>
      x y            (x nparticles)
  entity_sets.json:
      node_sets para condiciones de borde (base, izquierda, derecha)
"""
import json
import numpy as np


def build_grid(Lx, Ly, h, x0=0.0, y0=0.0):
    """Malla cartesiana de cuadriláteros de tamaño h sobre [x0,x0+Lx]x[y0,y0+Ly]."""
    nx = int(round(Lx / h))
    ny = int(round(Ly / h))
    W = nx + 1  # nodos por fila
    xs = x0 + np.arange(W) * h
    ys = y0 + np.arange(ny + 1) * h
    nodes = []
    for j in range(ny + 1):
        for i in range(W):
            nodes.append((xs[i], ys[j]))
    cells = []
    for j in range(ny):
        for i in range(nx):
            n0 = j * W + i
            n1 = j * W + i + 1
            n2 = (j + 1) * W + i + 1
            n3 = (j + 1) * W + i
            cells.append((n0, n1, n2, n3))
    return np.array(nodes), np.array(cells), (nx, ny, W, h, x0, y0)


def point_in_poly(x, y, poly):
    """Ray casting. poly: lista de (x,y) cerrada implícitamente."""
    n = len(poly)
    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if ((yi > y) != (yj > y)) and (
            x < (xj - xi) * (y - yi) / (yj - yi + 1e-300) + xi
        ):
            inside = not inside
        j = i
    return inside


def seed_particles(cells, nodes, grid, region_fn, ppc=2):
    """Coloca ppc x ppc partículas por celda cuyo centroide cae en region_fn.
    Devuelve coords de partículas y los índices de celda activos."""
    nx, ny, W, h, x0, y0 = grid
    pts = []
    # posiciones locales Gauss-like (uniformes) dentro de la celda
    offs = (np.arange(ppc) + 0.5) / ppc
    for c in cells:
        # nodos de la celda
        p0 = nodes[c[0]]
        p2 = nodes[c[2]]
        cx = 0.5 * (p0[0] + p2[0])
        cy = 0.5 * (p0[1] + p2[1])
        if not region_fn(cx, cy):
            continue
        x_lo, y_lo = p0[0], p0[1]
        for a in offs:
            for b in offs:
                pts.append((x_lo + a * h, y_lo + b * h))
    return np.array(pts)


def write_mesh(path, nodes, cells):
    with open(path, "w") as f:
        f.write("#! elementShape quadrilateral\n")
        f.write("#! elementNumPoints 4\n")
        f.write(f"{len(nodes)}\t{len(cells)}\n")
        for x, y in nodes:
            f.write(f"{x:.6f}\t{y:.6f}\n")
        for c in cells:
            f.write(f"{c[0]}\t{c[1]}\t{c[2]}\t{c[3]}\n")


def write_particles(path, pts):
    with open(path, "w") as f:
        f.write(f"{len(pts)}\n")
        for x, y in pts:
            f.write(f"{x:.6f}\t{y:.6f}\n")


def boundary_node_sets(nodes, grid, tol=1e-6):
    """node sets: 0=base (y=y0), 1=izquierda (x=x0), 2=derecha (x=x0+Lx)."""
    nx, ny, W, h, x0, y0 = grid
    ymax = y0 + ny * h
    xmax = x0 + nx * h
    base, left, right = [], [], []
    for idx, (x, y) in enumerate(nodes):
        if abs(y - y0) < tol:
            base.append(idx)
        if abs(x - x0) < tol:
            left.append(idx)
        if abs(x - xmax) < tol:
            right.append(idx)
    return {"base": base, "left": left, "right": right}


def write_entity_sets(path, nsets):
    obj = {"node_sets": [
        {"id": 0, "set": nsets["base"]},
        {"id": 1, "set": nsets["left"]},
        {"id": 2, "set": nsets["right"]},
    ]}
    with open(path, "w") as f:
        json.dump(obj, f)


# ----------------------------------------------------------------------------
# Geometrías
# ----------------------------------------------------------------------------
def region_column(width, height):
    """Columna granular: x in [0,width], y in [0,height]."""
    return lambda x, y: (0.0 <= x <= width) and (0.0 <= y <= height)


def load_section_polygon(crest_h=10.0, slope_angle_deg=60.0, crest_len=6.0,
                         toe_x=8.0, foundation_h=3.0):
    """Perfil 2D del talud — STAND-IN PARAMÉTRICO de la 'Sección A' CEMEX.

    Sustituir el cuerpo de esta función por los vértices reales extraídos del
    DXF de la Sección A cuando esté disponible. Devuelve un polígono (CCW)
    en coordenadas (x,y), metros.

    Geometría por defecto (banco de cantera típico, NF alto):
        - fundación horizontal de altura `foundation_h`
        - cara de talud a `slope_angle_deg` desde la horizontal
        - cresta horizontal de longitud `crest_len`
    """
    import math
    dx = crest_h / math.tan(math.radians(slope_angle_deg))
    x_toe = toe_x
    x_crest_start = x_toe + dx
    x_crest_end = x_crest_start + crest_len
    y0 = 0.0
    y_found = foundation_h
    y_crest = foundation_h + crest_h
    poly = [
        (0.0, y0),                 # base izq
        (x_crest_end + 4.0, y0),   # base der (con runout a la derecha)
        (x_crest_end + 4.0, y_found),
        (x_crest_end, y_found),    # pie derecho de la cresta sobre fundación
        (x_crest_end, y_crest),    # esquina cresta der
        (x_crest_start, y_crest),  # esquina cresta izq
        (x_toe, y_found),          # pie del talud
        (0.0, y_found),            # cara izquierda
    ]
    return poly


if __name__ == "__main__":
    import sys
    # demo rápido
    nodes, cells, grid = build_grid(2.0, 2.0, 0.05)
    print("nodes", len(nodes), "cells", len(cells))
