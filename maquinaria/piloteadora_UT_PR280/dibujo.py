"""
Utilidades de dibujo técnico sobre matplotlib (formato A3, cotas, cajetín)

Las vistas se crean con escala real: 1 mm de papel = `escala` mm del objeto
cuando el PDF se imprime en A3 (420 × 297 mm) al 100 %.
"""

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon, Circle, FancyArrowPatch
import numpy as np

A3 = (420.0, 297.0)
MM = 1 / 25.4

LW_VIS = 0.7    # arista visible
LW_FINA = 0.3   # cotas, rayado
LW_EJE = 0.3
COLOR = "black"
PROYECTO = "PERFORADORA ROTATIVA PARA PILOTES UT-PR280"


def nueva_hoja():
    fig = plt.figure(figsize=(A3[0] * MM, A3[1] * MM))
    marco = fig.add_axes([0, 0, 1, 1])
    marco.set_xlim(0, A3[0])
    marco.set_ylim(0, A3[1])
    marco.axis("off")
    marco.add_patch(Rectangle((20, 10), 390, 277, fill=False, lw=1.0))
    # marcas de zona
    for i in range(1, 9):
        x = 20 + i * 390 / 8
        marco.plot([x, x], [282, 287], lw=0.3, color=COLOR)
        marco.text(x - 390 / 16, 284.5, str(i), ha="center", va="center", fontsize=6)
    return fig, marco


def cajetin(marco, titulo, numero, escala, hoja, total, rev="A", fecha="2026-09-30"):
    x0, y0, w, h = 250, 10, 160, 42
    marco.add_patch(Rectangle((x0, y0), w, h, fill=False, lw=0.9))
    filas = [y0 + 32, y0 + 22, y0 + 12]
    for y in filas:
        marco.plot([x0, x0 + w], [y, y], lw=0.4, color=COLOR)
    marco.plot([x0 + 100, x0 + 100], [y0, y0 + 22], lw=0.4, color=COLOR)
    marco.plot([x0 + 130, x0 + 130], [y0, y0 + 22], lw=0.4, color=COLOR)
    marco.text(x0 + 3, y0 + 38.5, "UTECH · INGENIERÍA DE CIMENTACIONES", fontsize=7.5, weight="bold", va="center")
    marco.text(x0 + 3, y0 + 34.3, PROYECTO, fontsize=6, va="center")
    marco.text(x0 + 3, y0 + 27, titulo, fontsize=9, weight="bold", va="center")
    marco.text(x0 + 3, y0 + 18.5, "Dibujó: Utech / Claude Code   Revisó: —   Aprobó: —", fontsize=5.5, va="center")
    marco.text(x0 + 3, y0 + 14, "Cotas en mm salvo indicación. No medir sobre el plano.", fontsize=5.5, va="center")
    marco.text(x0 + 3, y0 + 6, f"Fecha: {fecha}   Rev.: {rev}   Diedro europeo (ISO 128)", fontsize=5.5, va="center")
    marco.text(x0 + 115, y0 + 18.5, "ESCALA", fontsize=5, ha="center", va="center")
    marco.text(x0 + 115, y0 + 13.5, escala, fontsize=8, ha="center", va="center", weight="bold")
    marco.text(x0 + 115, y0 + 6, f"HOJA {hoja}/{total}", fontsize=6, ha="center", va="center")
    marco.text(x0 + 145, y0 + 18.5, "PLANO N.º", fontsize=5, ha="center", va="center")
    marco.text(x0 + 145, y0 + 11, numero, fontsize=10, ha="center", va="center", weight="bold")
    marco.text(x0 + 145, y0 + 4, "A3", fontsize=6, ha="center", va="center")


def vista(fig, x_papel, y_papel, xlim, ylim, escala, titulo=None):
    """Crea unos ejes a escala real. xlim/ylim en mm del objeto."""
    w = (xlim[1] - xlim[0]) / escala
    h = (ylim[1] - ylim[0]) / escala
    ax = fig.add_axes([x_papel / A3[0], y_papel / A3[1], w / A3[0], h / A3[1]])
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.escala = escala
    if titulo:
        ax.text(0.5, -0.01, titulo, transform=ax.transAxes, ha="center", va="top",
                fontsize=7.5, weight="bold")
    return ax


def fs(ax, papel_mm):
    """Convierte una longitud en papel (mm) a unidades del objeto"""
    return papel_mm * ax.escala


# ---------------------------------------------------------------------------
# Primitivas
# ---------------------------------------------------------------------------
def rect(ax, x, y, w, h, lw=LW_VIS, hatch=None, fill=False, fc="white", z=2, ls="-"):
    p = Rectangle((x, y), w, h, fill=fill or hatch is not None, fc=fc if (fill or hatch) else "none",
                  ec=COLOR, lw=lw, hatch=hatch, zorder=z, ls=ls)
    ax.add_patch(p)
    return p


def poly(ax, pts, lw=LW_VIS, hatch=None, fill=False, fc="white", z=2, closed=True, ls="-"):
    p = Polygon(pts, closed=closed, fill=fill or hatch is not None, fc=fc if (fill or hatch) else "none",
                ec=COLOR, lw=lw, hatch=hatch, zorder=z, ls=ls)
    ax.add_patch(p)
    return p


def circ(ax, x, y, r, lw=LW_VIS, fill=False, fc="white", z=3, hatch=None, ls="-"):
    p = Circle((x, y), r, fill=fill or hatch is not None, fc=fc if (fill or hatch) else "none",
               ec=COLOR, lw=lw, zorder=z, hatch=hatch, ls=ls)
    ax.add_patch(p)
    return p


def linea(ax, xs, ys, lw=LW_VIS, ls="-", z=3, color=COLOR):
    ax.plot(xs, ys, lw=lw, ls=ls, color=color, zorder=z, solid_capstyle="butt")


def eje(ax, x1, y1, x2, y2):
    ax.plot([x1, x2], [y1, y2], lw=LW_EJE, color=COLOR, ls=(0, (12, 3, 2, 3)), zorder=1)


def oculta(ax, xs, ys):
    ax.plot(xs, ys, lw=LW_FINA, color=COLOR, ls=(0, (4, 2)), zorder=2)


def texto(ax, x, y, s, size=6, **kw):
    kw.setdefault("ha", "center")
    kw.setdefault("va", "center")
    ax.text(x, y, s, fontsize=size, zorder=6, **kw)


def _flecha(ax, x, y, dx, dy):
    L = fs(ax, 2.2)
    n = np.hypot(dx, dy)
    ux, uy = dx / n, dy / n
    px, py = -uy, ux
    w = L * 0.28
    poly(ax, [(x, y), (x - ux * L + px * w, y - uy * L + py * w),
              (x - ux * L - px * w, y - uy * L - py * w)], lw=0.1, fill=True, fc=COLOR, z=6)


def cota_h(ax, x1, x2, y_obj, y_cota, txt=None, size=5.5, arriba=True):
    """Cota horizontal entre x1 y x2 medida en y_obj, dibujada en y_cota"""
    ext = fs(ax, 1.5) * (1 if y_cota > y_obj else -1)
    for x in (x1, x2):
        linea(ax, [x, x], [y_obj, y_cota + ext], lw=LW_FINA, z=5)
    linea(ax, [x1, x2], [y_cota, y_cota], lw=LW_FINA, z=5)
    _flecha(ax, x1, y_cota, -1, 0)
    _flecha(ax, x2, y_cota, 1, 0)
    if txt is None:
        txt = f"{abs(x2 - x1):.0f}"
    off = fs(ax, 1.4) * (1 if arriba else -1)
    texto(ax, (x1 + x2) / 2, y_cota + off, txt, size=size, va="bottom" if arriba else "top",
          bbox=dict(fc="white", ec="none", pad=0.3))


def cota_v(ax, y1, y2, x_obj, x_cota, txt=None, size=5.5):
    ext = fs(ax, 1.5) * (1 if x_cota > x_obj else -1)
    for y in (y1, y2):
        linea(ax, [x_obj, x_cota + ext], [y, y], lw=LW_FINA, z=5)
    linea(ax, [x_cota, x_cota], [y1, y2], lw=LW_FINA, z=5)
    _flecha(ax, x_cota, y1, 0, -1 if y1 < y2 else 1)
    _flecha(ax, x_cota, y2, 0, 1 if y2 > y1 else -1)
    if txt is None:
        txt = f"{abs(y2 - y1):.0f}"
    texto(ax, x_cota - fs(ax, 1.2), (y1 + y2) / 2, txt, size=size, rotation=90, ha="right",
          bbox=dict(fc="white", ec="none", pad=0.3))


def marca(ax, x, y, n, dx, dy):
    """Globo de referencia de pieza: línea desde (x,y) hasta globo desplazado dx,dy (mm papel)"""
    X, Y = x + fs(ax, dx), y + fs(ax, dy)
    r = fs(ax, 2.6)
    linea(ax, [x, X], [y, Y], lw=LW_FINA, z=6)
    circ(ax, x, y, fs(ax, 0.4), fill=True, fc=COLOR, lw=0.1, z=7)
    circ(ax, X, Y, r, lw=0.5, fill=True, fc="white", z=7)
    ax.text(X, Y, str(n), fontsize=5.5, weight="bold", ha="center", va="center", zorder=8)


def corte(ax, x1, y1, x2, y2, letra):
    """Indicador de plano de corte"""
    ax.plot([x1, x2], [y1, y2], lw=1.1, color=COLOR, ls=(0, (10, 3, 2, 3)), zorder=6)
    for (x, y) in ((x1, y1), (x2, y2)):
        texto(ax, x, y + fs(ax, 3), letra, size=8, weight="bold")


def tabla(marco, x, y, filas, anchos, alto=4.2, titulo=None, size=5.5, negrita_primera=True):
    """Tabla en coordenadas de papel. (x,y) = esquina superior izquierda."""
    if titulo:
        marco.text(x, y + 1.5, titulo, fontsize=7, weight="bold", va="bottom")
    W = sum(anchos)
    for i, fila in enumerate(filas):
        yy = y - (i + 1) * alto
        marco.add_patch(Rectangle((x, yy), W, alto, fill=(i == 0 and negrita_primera),
                                  fc="#e6e6e6", ec=COLOR, lw=0.35))
        xx = x
        for j, c in enumerate(fila):
            marco.plot([xx, xx], [yy, yy + alto], lw=0.35, color=COLOR)
            marco.text(xx + 1.2, yy + alto / 2, str(c), fontsize=size, va="center",
                       weight="bold" if (i == 0 and negrita_primera) else "normal")
            xx += anchos[j]
        marco.plot([xx, xx], [yy, yy + alto], lw=0.35, color=COLOR)
    return y - len(filas) * alto


def notas(marco, x, y, lineas, titulo="NOTAS", size=5.8, paso=3.4):
    marco.text(x, y, titulo, fontsize=7, weight="bold", va="top")
    for i, l in enumerate(lineas):
        marco.text(x, y - 4.5 - i * paso, l, fontsize=size, va="top")
