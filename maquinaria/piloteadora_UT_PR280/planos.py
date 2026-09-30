"""
Generador de planos de la perforadora rotativa para pilotes UT-PR280
(Ø1200 mm × 40 m, Kelly de 4 secciones con bloqueo, par 280 kNm)

Uso:
    python planos.py            # genera planos/UT-PR280_planos.pdf y PNG por hoja

Coordenadas de la máquina (mm): x = eje de giro → mástil (hacia delante),
y = lateral (izquierda +), z = altura sobre el terreno.
"""

import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

from dibujo import (nueva_hoja, cajetin, vista, fs, rect, poly, circ, linea, eje, oculta,
                    texto, cota_h, cota_v, marca, corte, tabla, notas, LW_FINA, LW_VIS)
import calculos as C

plt.rcParams["hatch.linewidth"] = 0.3
plt.rcParams["font.family"] = "DejaVu Sans"

SALIDA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "planos")
TOTAL_HOJAS = 8

# ---------------------------------------------------------------------------
# Geometría principal (mm)
# ---------------------------------------------------------------------------
ORUGA_L = 5600          # longitud total de oruga
ORUGA_H = 1050          # altura de oruga
ORUGA_R = ORUGA_H / 2
ZAPATA = 800
TROCHA_T = C.TROCHA_TRABAJO * 1000      # 4400
TROCHA_TR = C.TROCHA_TRANSPORTE * 1000  # 2200
Z_GIRO = 1050           # base de la corona de giro
Z_CUBIERTA = 1950       # cubierta de la superestructura
Z_CAPO = 2700
COLA = 4300             # radio de giro trasero
R_PERF = C.RADIO_PERFORACION * 1000     # 4300 eje de giro → eje Kelly
MASTIL_X0, MASTIL_X1 = 2450, 3250       # caras trasera y delantera del mástil (800)
MASTIL_ANCHO = 650
MASTIL_Z0, MASTIL_Z1 = 800, 22000       # pie y coronación del mástil
Z_UNION_SUP = 16500     # unión atornillada tramo superior del mástil
CABEZA_Z1 = 23400
Z_POLEA = 22750
KELLY_D = C.KELLY[0].D * 1000   # 508
KELLY_RET = C.calcular().L_ret * 1000   # 13400
HERR_H = 1500
ROT_Z0 = 5000           # base de mesa rotaria en la vista general
ROT_H = 1500
CARRERA = 12000


def oruga_lateral(ax, x0=0.0, detalle=True, z=2):
    """Oruga vista de lado centrada en x0"""
    L, H, R = ORUGA_L, ORUGA_H, ORUGA_R
    xa, xb = x0 - L / 2 + R, x0 + L / 2 - R
    t = np.linspace(-np.pi / 2, np.pi / 2, 30)
    pts = [(xb + R * np.cos(a), R + R * np.sin(a)) for a in t]
    pts += [(xa - R * np.cos(a), R - R * np.sin(a)) for a in t]
    poly(ax, pts, z=z, fill=True)
    if not detalle:
        return
    Ri = R - 110
    pts = [(xb + Ri * np.cos(a), R + Ri * np.sin(a)) for a in t]
    pts += [(xa - Ri * np.cos(a), R - Ri * np.sin(a)) for a in t]
    poly(ax, pts, lw=LW_FINA, z=z)
    for xc in (xa, xb):
        circ(ax, xc, R, 400, z=z + 1)
        circ(ax, xc, R, 120, lw=LW_FINA, z=z + 1)
    for xr in np.linspace(xa + 600, xb - 600, 6):
        circ(ax, xr, 245, 130, lw=LW_FINA, z=z + 1)
    for xr in (x0 - 900, x0 + 900):
        circ(ax, xr, H - 230, 110, lw=LW_FINA, z=z + 1)
    for xg in np.arange(xa, xb, 180):
        linea(ax, [xg, xg], [0, 110], lw=LW_FINA, z=z + 1)
    rect(ax, x0 - 1300, R - 170, 2600, 340, lw=LW_FINA, z=z + 1)


def superestructura_lateral(ax, capo=True, z=3):
    # bastidor de oruga central y corona
    rect(ax, -1200, 650, 2400, Z_GIRO - 650, fill=True, z=z - 1)
    rect(ax, -900, Z_GIRO, 1800, 130, hatch="xxxx", z=z)
    # bastidor superior
    poly(ax, [(-3500, Z_GIRO + 130), (1650, Z_GIRO + 130), (1650, Z_CUBIERTA),
              (-3500, Z_CUBIERTA)], fill=True, z=z)
    # contrapeso
    poly(ax, [(-3450, 1250), (-COLA + 250, 1250), (-COLA, 1500), (-COLA, 2450),
              (-COLA + 250, Z_CAPO), (-3300, Z_CAPO), (-3300, 1250)], fill=True, hatch="\\\\\\", z=z + 1)
    if capo:
        # capó motor
        poly(ax, [(-3300, Z_CUBIERTA), (-600, Z_CUBIERTA), (-600, Z_CAPO - 150),
                  (-750, Z_CAPO), (-3300, Z_CAPO)], fill=True, z=z)
        for xr in np.arange(-3100, -900, 160):
            linea(ax, [xr, xr], [Z_CUBIERTA + 250, Z_CAPO - 200], lw=LW_FINA, z=z + 1)
        # escape y filtro
        rect(ax, -2300, Z_CAPO, 120, 350, fill=True, z=z)
        rect(ax, -1500, Z_CAPO, 380, 160, fill=True, z=z)
    # barandilla
    for xr in (-3200, -2000, -800):
        linea(ax, [xr, xr], [Z_CAPO, Z_CAPO + 650], lw=LW_FINA, z=z)
    linea(ax, [-3200, -800], [Z_CAPO + 650, Z_CAPO + 650], lw=LW_FINA, z=z)


def cabina_lateral(ax, z=6):
    poly(ax, [(-450, 1500), (1450, 1500), (1500, 2600), (1300, 3350), (-450, 3350)], fill=True, z=z)
    poly(ax, [(0, 2300), (1350, 2300), (1390, 2600), (1220, 3200), (0, 3200)], lw=LW_FINA, z=z,
         fill=True, fc="#eef3f7")
    linea(ax, [700, 700], [2300, 3200], lw=LW_FINA, z=z)
    rect(ax, -350, 1650, 300, 1500, lw=LW_FINA, z=z)


def mastil_lateral(ax, z=4, cabeza=True, z_rot=ROT_Z0, kelly=True, herramienta=True):
    # mástil (cajón)
    rect(ax, MASTIL_X0, MASTIL_Z0, MASTIL_X1 - MASTIL_X0, MASTIL_Z1 - MASTIL_Z0, fill=True, z=z)
    for zz in np.arange(MASTIL_Z0 + 1500, MASTIL_Z1, 1500):
        linea(ax, [MASTIL_X0 + 60, MASTIL_X1 - 60], [zz, zz], lw=LW_FINA, z=z)
    linea(ax, [MASTIL_X0, MASTIL_X1 + 60], [Z_UNION_SUP, Z_UNION_SUP], lw=1.0, z=z + 1)
    # guías delanteras
    rect(ax, MASTIL_X1, MASTIL_Z0 + 300, 60, MASTIL_Z1 - MASTIL_Z0 - 600, fill=True, fc="#dddddd", z=z)
    # pie de mástil
    poly(ax, [(MASTIL_X0, MASTIL_Z0), (MASTIL_X1, MASTIL_Z0), (MASTIL_X1 - 100, 300),
              (MASTIL_X0 + 100, 300)], fill=True, z=z)
    # guía inferior de Kelly
    poly(ax, [(MASTIL_X1, 1650), (R_PERF + 450, 1650), (R_PERF + 450, 1900), (MASTIL_X1, 2150)],
         fill=True, z=z + 2)
    if cabeza:
        # cabeza de mástil con poleas
        poly(ax, [(MASTIL_X0 - 150, MASTIL_Z1), (R_PERF + 250, MASTIL_Z1), (R_PERF + 250, MASTIL_Z1 + 400),
                  (R_PERF - 150, CABEZA_Z1), (MASTIL_X0 + 150, CABEZA_Z1), (MASTIL_X0 - 150, MASTIL_Z1 + 700)],
             fill=True, z=z)
        circ(ax, R_PERF - 450, Z_POLEA, 450, z=z + 1)
        circ(ax, R_PERF - 450, Z_POLEA, 90, lw=LW_FINA, z=z + 1)
        circ(ax, MASTIL_X0 + 50, Z_POLEA - 150, 300, z=z + 1)
        circ(ax, R_PERF - 150, MASTIL_Z1 + 250, 180, lw=LW_FINA, z=z + 1)  # polea auxiliar
        # luz de balizamiento
        rect(ax, MASTIL_X0 + 300, CABEZA_Z1, 120, 180, fill=True, z=z)
    # cabrestantes en el dorso del mástil
    for zc, r, nom in ((5200, 420, "principal"), (3700, 300, "empuje")):
        rect(ax, MASTIL_X0 - 900, zc - r - 80, 900, 2 * r + 160, fill=True, z=z + 1)
        circ(ax, MASTIL_X0 - 450, zc, r, z=z + 2)
        circ(ax, MASTIL_X0 - 450, zc, r - 120, lw=LW_FINA, z=z + 2)
    # cable principal: cabrestante → polea trasera → polea delantera → giratorio
    linea(ax, [MASTIL_X0 - 450 + 400, MASTIL_X0 - 250], [5200 + 150, Z_POLEA - 150], lw=0.6, z=z + 3)
    linea(ax, [MASTIL_X0 + 50, R_PERF - 450], [Z_POLEA + 150, Z_POLEA + 450], lw=0.6, z=z + 3)
    # mesa rotaria y carro
    rotaria_lateral(ax, z_rot, z=z + 4)
    if kelly:
        zk0 = HERR_H if herramienta else 2400
        zk1 = zk0 + KELLY_RET
        rect(ax, R_PERF - KELLY_D / 2, zk0 + 300, KELLY_D, zk1 - zk0 - 300, fill=True, z=z + 3)
        for zz in np.arange(zk0 + 300, zk1, 3000):
            linea(ax, [R_PERF - KELLY_D / 2, R_PERF + KELLY_D / 2], [zz, zz], lw=LW_FINA, z=z + 3)
        rect(ax, R_PERF - 45, zk0 + 300, 90, zk1 - zk0 - 400, lw=LW_FINA, z=z + 3)  # chaveta
        rect(ax, R_PERF - 100, zk0, 200, 300, fill=True, z=z + 3)  # caja Kelly
        # giratorio
        poly(ax, [(R_PERF - 300, zk1), (R_PERF + 300, zk1), (R_PERF + 200, zk1 + 550),
                  (R_PERF - 200, zk1 + 550)], fill=True, z=z + 3)
        circ(ax, R_PERF, zk1 + 650, 110, z=z + 3)
        linea(ax, [R_PERF, R_PERF], [zk1 + 760, Z_POLEA], lw=0.6, z=z + 2)
        rotaria_lateral(ax, z_rot, z=z + 4)
        if herramienta:
            cubeta_lateral(ax, R_PERF, 0, z=z + 3)


def rotaria_lateral(ax, z0, z=8, fantasma=False):
    ls = (0, (5, 2, 1, 2)) if fantasma else "-"
    lw = LW_FINA if fantasma else LW_VIS
    f = not fantasma
    # carro de guiado
    rect(ax, MASTIL_X1 + 60, z0 - 300, 300, ROT_H + 500, fill=f, z=z, ls=ls, lw=lw)
    # cuerpo reductor
    poly(ax, [(MASTIL_X1 + 360, z0 + 100), (R_PERF + 850, z0 + 100), (R_PERF + 850, z0 + 1300),
              (MASTIL_X1 + 360, z0 + 1300)], fill=f, z=z, ls=ls, lw=lw)
    # camisa de arrastre
    rect(ax, R_PERF - 345, z0 - 150, 690, 250, fill=f, z=z, ls=ls, lw=lw)
    rect(ax, R_PERF - 380, z0 + 1300, 760, 200, fill=f, z=z, ls=ls, lw=lw)
    # motores
    for xm in (R_PERF - 620, R_PERF + 620):
        rect(ax, xm - 180, z0 + 1300, 360, 450, fill=f, z=z, ls=ls, lw=lw)
        rect(ax, xm - 130, z0 + 1750, 260, 420, fill=f, z=z, ls=ls, lw=lw)


def cubeta_lateral(ax, x0, z0, z=6):
    r = 590
    rect(ax, x0 - r, z0 + 150, 2 * r, HERR_H - 350, fill=True, z=z)
    poly(ax, [(x0 - r, z0 + 150), (x0 + r, z0 + 150), (x0 + r - 40, z0), (x0 - r + 40, z0)], fill=True, z=z)
    for xd in np.linspace(x0 - r + 60, x0 + r - 60, 9):
        poly(ax, [(xd - 30, z0 + 40), (xd + 30, z0 + 40), (xd + 10, z0 - 60), (xd - 10, z0 - 60)],
             fill=True, fc="#999999", lw=LW_FINA, z=z)
    poly(ax, [(x0 - r, z0 + HERR_H - 200), (x0 + r, z0 + HERR_H - 200), (x0 + 200, z0 + HERR_H),
              (x0 - 200, z0 + HERR_H)], fill=True, z=z)
    for zz in (z0 + 450, z0 + 900):
        linea(ax, [x0 - r, x0 + r], [zz, zz], lw=LW_FINA, z=z)
    rect(ax, x0 - 50, z0 - 250, 100, 250, fill=True, z=z)  # piloto


def cinematica_lateral(ax, z=5, radio=R_PERF):
    """Paralelogramo y cilindros de inclinación"""
    dx = radio - R_PERF
    pa, pb = (1500, 1850), (1500, 2750)
    ma, mb = (MASTIL_X0 + dx, 2200), (MASTIL_X0 + dx, 3100)
    for p, m in ((pa, ma), (pb, mb)):
        v = np.array(m) - np.array(p)
        n = np.array([-v[1], v[0]]) / np.linalg.norm(v) * 110
        poly(ax, [tuple(np.array(p) + n), tuple(np.array(m) + n), tuple(np.array(m) - n),
                  tuple(np.array(p) - n)], fill=True, z=z)
        circ(ax, *p, 80, z=z + 1)
        circ(ax, *m, 80, z=z + 1)
    # cilindro de ajuste de radio
    linea(ax, [900, 2000], [2300, 2650], lw=2.2, z=z)
    # cilindros de inclinación del mástil (2)
    p0 = np.array([-300, Z_CUBIERTA + 1000])
    p1 = np.array([MASTIL_X0 + dx, 10500])
    v = p1 - p0
    u = v / np.linalg.norm(v)
    n = np.array([-u[1], u[0]])
    pc = p0 + u * 4600
    poly(ax, [tuple(p0 + n * 110), tuple(pc + n * 110), tuple(pc - n * 110), tuple(p0 - n * 110)],
         fill=True, z=z)
    poly(ax, [tuple(pc + n * 55), tuple(p1 + n * 55), tuple(p1 - n * 55), tuple(pc - n * 55)],
         fill=True, z=z)
    circ(ax, *p0, 90, z=z + 1)
    circ(ax, *p1, 90, z=z + 1)
    # soporte del cilindro
    poly(ax, [(-700, Z_CUBIERTA), (100, Z_CUBIERTA), (-150, p0[1] + 200), (-450, p0[1] + 200)],
         fill=True, z=z - 1)


# ---------------------------------------------------------------------------
# HOJA 1 — Disposición general
# ---------------------------------------------------------------------------
def hoja_1(pdf, res):
    fig, marco = nueva_hoja()
    E = 100
    ax = vista(fig, 28, 22, (-5200, 6300), (-800, 24800), E, "ALZADO LATERAL — POSICIÓN DE TRABAJO  E 1:100")
    linea(ax, [-5200, 6300], [0, 0], lw=0.5)
    for xh in np.arange(-5100, 6300, 250):
        linea(ax, [xh, xh - 150], [0, -150], lw=LW_FINA)
    oruga_lateral(ax)
    superestructura_lateral(ax)
    cinematica_lateral(ax)
    mastil_lateral(ax)
    cabina_lateral(ax, z=3)
    # posiciones extremas de la rotaria (fantasma)
    rotaria_lateral(ax, 2400, z=9, fantasma=True)
    rotaria_lateral(ax, 2400 + CARRERA, z=9, fantasma=True)
    eje(ax, 0, -500, 0, 5000)
    eje(ax, R_PERF, -600, R_PERF, 24000)
    # cotas
    cota_v(ax, 0, CABEZA_Z1, -COLA, -COLA - 700, f"{CABEZA_Z1:.0f}  (altura de trabajo)")
    cota_v(ax, 0, ORUGA_H, 2800, 3300 + 400)
    cota_v(ax, 2400, 2400 + CARRERA, R_PERF + 850, R_PERF + 1500, f"Carrera de empuje {CARRERA:.0f}")
    cota_v(ax, HERR_H, HERR_H + KELLY_RET, R_PERF + 300, R_PERF + 700, f"Kelly retraída {KELLY_RET:.0f}")
    cota_h(ax, 0, R_PERF, 0, -600, f"R {R_PERF:.0f}", arriba=False)
    cota_h(ax, -COLA, 0, 0, -600, f"R cola {COLA:.0f}", arriba=False)
    cota_h(ax, -2800, 2800, 1050, 4300 + 400, f"{ORUGA_L:.0f}")
    # referencias de piezas
    for n, (x, y, dx, dy) in enumerate([
            (2850, 18000, -12, 0), (R_PERF + 500, 5800, 8, 5), (R_PERF, 9000, 8, 0),
            (R_PERF, 700, 12, 3), (R_PERF - 450, Z_POLEA, 10, 6), (MASTIL_X0 - 450, 5200, -14, 8),
            (MASTIL_X0 - 450, 3700, -16, 4), (2000, 2600, -6, -18), (1000, 6000, -14, 4),
            (500, 2900, -10, 14), (-2000, 2400, -6, 16), (-3900, 2000, -4, 14),
            (-2600, 500, -14, 2), (R_PERF, 15400, 9, 3)], start=1):
        marca(ax, x, y, n, dx, dy)

    # alzado frontal
    ax2 = vista(fig, 150, 22, (-3000, 3000), (-800, 24800), E, "ALZADO FRONTAL  E 1:100")
    linea(ax2, [-3000, 3000], [0, 0], lw=0.5)
    frontal(ax2)
    cota_h(ax2, -TROCHA_T / 2 - ZAPATA / 2, TROCHA_T / 2 + ZAPATA / 2, 0, -600,
           f"{TROCHA_T + ZAPATA:.0f} (trabajo)", arriba=False)
    cota_h(ax2, -TROCHA_T / 2, TROCHA_T / 2, ORUGA_H, 4000, f"Trocha {TROCHA_T:.0f}")
    cota_h(ax2, -MASTIL_ANCHO / 2, MASTIL_ANCHO / 2, 20000, 20800, f"{MASTIL_ANCHO}")

    # planta
    ax3 = vista(fig, 222, 190, (-4800, 5600), (-3000, 3000), E, "PLANTA  E 1:100")
    planta(ax3)
    cota_h(ax3, -COLA, R_PERF, -2600, -2700, f"{COLA + R_PERF:.0f}", arriba=True)

    # tabla de características
    filas = [("CARACTERÍSTICA", "VALOR"),
             ("Diámetro de perforación nominal / máx.", "1200 / 1500 mm"),
             ("Profundidad requerida / máxima (Kelly 4 secc.)", f"40.0 / {res.prof_max:.1f} m"),
             ("Par nominal mesa rotaria (350 bar)", "280 kNm"),
             ("Velocidad de rotación / centrifugado", "5–30 / 90 rpm"),
             ("Fuerza de empuje / extracción (cabrestante)", "250 / 300 kN"),
             ("Carrera de empuje", f"{CARRERA/1000:.1f} m"),
             ("Cabrestante principal (1.ª capa) / cable", "300 kN · 70 m/min / Ø32 mm"),
             ("Cabrestante auxiliar / cable", "100 kN · 60 m/min / Ø20 mm"),
             ("Motor diésel (Stage V / Tier 4f)", "354 kW @ 1800 rpm"),
             ("Caudal hidráulico total", "2 × 360 + 180 l/min"),
             ("Radio de perforación", "3800 – 4700 mm"),
             ("Inclinación del mástil lat. / long.", "±5° / +15° −5°"),
             ("Ancho zapata / trocha trabajo-transporte", "800 / 4400 – 2200 mm"),
             ("Masa en servicio (con herramienta)", f"{res.W/1000:.1f} t"),
             ("Presión media sobre el terreno", res.tabla["Presión media sobre terreno"])]
    y = tabla(marco, 222, 176, filas, [120, 60], alto=4.9, titulo="CARACTERÍSTICAS PRINCIPALES", size=5.4)
    leyenda = ["1 Mástil cajón 800×650 (S690QL)", "2 Mesa rotaria 280 kNm", "3 Barra Kelly 4 secc. Ø508",
               "4 Cubeta Ø1200", "5 Cabeza de mástil / poleas", "6 Cabrestante principal 300 kN",
               "7 Cabrestante de empuje", "8 Paralelogramo", "9 Cilindros de inclinación",
               "10 Cabina ROPS/FOPS", "11 Grupo motor / bombas", "12 Contrapeso 18 t",
               "13 Tren de oruga telescópico", "14 Giratorio de Kelly"]
    for i, l in enumerate(leyenda):
        marco.text(222 + (i % 2) * 92, y - 5 - (i // 2) * 3.6, l, fontsize=5.3, va="top")
    cajetin(marco, "DISPOSICIÓN GENERAL — POSICIÓN DE TRABAJO", "PR280-01", "1:100", 1, TOTAL_HOJAS)
    guardar(pdf, fig, "PR280-01")


def frontal(ax, trocha=TROCHA_T, mastil=True, z=2):
    for s in (-1, 1):
        yc = s * trocha / 2
        rect(ax, yc - ZAPATA / 2, 0, ZAPATA, ORUGA_H, fill=True, z=z)
        rect(ax, yc - ZAPATA / 2 + 100, 120, ZAPATA - 200, ORUGA_H - 240, lw=LW_FINA, z=z)
    rect(ax, -trocha / 2 + ZAPATA / 2, 650, trocha - ZAPATA, 300, fill=True, z=z)
    rect(ax, -1200, 650, 2400, Z_GIRO - 650, fill=True, z=z + 1)
    rect(ax, -900, Z_GIRO, 1800, 130, hatch="xxxx", z=z + 1)
    rect(ax, -1500, Z_GIRO + 130, 3000, Z_CUBIERTA - Z_GIRO - 130, fill=True, z=z + 1)
    rect(ax, -1500, Z_CUBIERTA, 2600, Z_CAPO - Z_CUBIERTA, fill=True, z=z + 1)
    # cabina a la izquierda del operador (derecha en alzado frontal)
    poly(ax, [(500, 1500), (1500, 1500), (1500, 3350), (500, 3350)], fill=True, z=z + 2)
    rect(ax, 600, 2300, 800, 900, lw=LW_FINA, fill=True, fc="#eef3f7", z=z + 2)
    if not mastil:
        return
    w = MASTIL_ANCHO / 2
    rect(ax, -w, MASTIL_Z0, 2 * w, MASTIL_Z1 - MASTIL_Z0, fill=True, z=z + 3)
    for zz in np.arange(MASTIL_Z0 + 750, MASTIL_Z1, 1500):
        linea(ax, [-w, w], [zz, zz + 1500], lw=LW_FINA, z=z + 3)
        linea(ax, [-w, w], [zz + 1500, zz], lw=LW_FINA, z=z + 3)
    linea(ax, [-w - 60, w + 60], [Z_UNION_SUP, Z_UNION_SUP], lw=1.0, z=z + 4)
    poly(ax, [(-w - 150, MASTIL_Z1), (w + 150, MASTIL_Z1), (w + 50, CABEZA_Z1), (-w - 50, CABEZA_Z1)],
         fill=True, z=z + 3)
    rect(ax, -80, Z_POLEA - 450, 160, 900, lw=LW_FINA, z=z + 4)
    # kelly, giratorio
    rect(ax, -KELLY_D / 2, HERR_H + 300, KELLY_D, KELLY_RET - 300, fill=True, z=z + 4)
    poly(ax, [(-300, HERR_H + KELLY_RET), (300, HERR_H + KELLY_RET), (200, HERR_H + KELLY_RET + 550),
              (-200, HERR_H + KELLY_RET + 550)], fill=True, z=z + 4)
    linea(ax, [0, 0], [HERR_H + KELLY_RET + 550, Z_POLEA], lw=0.6, z=z + 4)
    # rotaria
    rect(ax, -850, ROT_Z0 + 100, 1700, 1200, fill=True, z=z + 5)
    rect(ax, -380, ROT_Z0 + 1300, 760, 200, fill=True, z=z + 5)
    rect(ax, -345, ROT_Z0 - 150, 690, 250, fill=True, z=z + 5)
    for ym in (-540, 0, 540):
        rect(ax, ym - 180, ROT_Z0 + 1300, 360, 450, fill=True, z=z + 5)
        rect(ax, ym - 130, ROT_Z0 + 1750, 260, 420, fill=True, z=z + 5)
    # guía inferior y cubeta
    rect(ax, -450, 1650, 900, 350, fill=True, z=z + 5)
    cubeta_lateral(ax, 0, 0, z=z + 6)
    eje(ax, 0, -500, 0, 24000)


def planta(ax, trocha=TROCHA_T, z=2):
    for s in (-1, 1):
        yc = s * trocha / 2
        rect(ax, -ORUGA_L / 2, yc - ZAPATA / 2, ORUGA_L, ZAPATA, fill=True, z=z)
        for xg in np.arange(-ORUGA_L / 2 + 200, ORUGA_L / 2, 200):
            linea(ax, [xg, xg], [yc - ZAPATA / 2, yc + ZAPATA / 2], lw=0.15, z=z)
    # superestructura con radio de cola
    a0 = np.arcsin(1500 / COLA)
    ang = np.linspace(np.pi - a0, np.pi + a0, 30)
    pts = [(COLA * np.cos(a), COLA * np.sin(a)) for a in ang]
    pts += [(1650, -1500), (1650, 1500)]
    poly(ax, pts, fill=True, z=z + 1)
    rect(ax, -3300, -1300, 2700, 2600, lw=LW_FINA, z=z + 1)
    for yv in np.arange(-1100, 1200, 200):
        linea(ax, [-3100, -900], [yv, yv], lw=0.15, z=z + 1)
    rect(ax, -450, -1500, 1950, 1000, fill=True, z=z + 2)   # cabina (lado derecho)
    rect(ax, -300, -1400, 1650, 800, lw=LW_FINA, fill=True, fc="#eef3f7", z=z + 2)
    # paralelogramo y mástil
    rect(ax, 1500, -400, MASTIL_X0 - 1500, 800, fill=True, z=z + 2)
    rect(ax, MASTIL_X0 - 900, -500, 900, 1000, fill=True, z=z + 3)   # cabrestantes
    rect(ax, MASTIL_X0, -MASTIL_ANCHO / 2, MASTIL_X1 - MASTIL_X0, MASTIL_ANCHO, fill=True, z=z + 3)
    # rotaria
    rect(ax, MASTIL_X1 + 60, -700, 300, 1400, fill=True, z=z + 4)
    circ(ax, R_PERF, 0, 850, fill=True, z=z + 4)
    for a in (0, 120, 240):
        circ(ax, R_PERF + 620 * np.cos(np.radians(a)), 620 * np.sin(np.radians(a)), 180, fill=True, z=z + 5)
    circ(ax, R_PERF, 0, KELLY_D / 2, fill=True, hatch="////", z=z + 6)
    circ(ax, R_PERF, 0, 600, ls=(0, (4, 2)), lw=LW_FINA, z=z + 6)
    circ(ax, 0, 0, COLA, ls=(0, (8, 3, 2, 3)), lw=LW_FINA, z=1)
    eje(ax, -4800, 0, 5600, 0)
    eje(ax, R_PERF, -1200, R_PERF, 1200)
    eje(ax, 0, -2900, 0, 2900)


# ---------------------------------------------------------------------------
# HOJA 2 — Transporte y rango de trabajo
# ---------------------------------------------------------------------------
def hoja_2(pdf, res):
    fig, marco = nueva_hoja()
    E = 75
    X0 = -11800
    ax = vista(fig, 28, 200, (X0, 6000), (-700, 4600), E, "ALZADO LATERAL — CONFIGURACIÓN DE TRANSPORTE  E 1:75")
    linea(ax, [X0, 6000], [0, 0], lw=0.5)
    oruga_lateral(ax)
    superestructura_lateral(ax)
    cabina_lateral(ax, z=3)
    # mástil tumbado hacia atrás sobre soporte, sin tramo superior ni Kelly
    zt0, zt1 = 2750, 3450
    L_base = Z_UNION_SUP - MASTIL_Z0
    x_pie = 4000
    rect(ax, x_pie - L_base, zt0, L_base, zt1 - zt0, fill=True, z=6)
    for xx in np.arange(x_pie - L_base + 1500, x_pie, 1500):
        linea(ax, [xx, xx], [zt0 + 50, zt1 - 50], lw=LW_FINA, z=6)
    # rotaria recogida en el pie del mástil
    poly(ax, [(x_pie - 2100, zt0), (x_pie - 300, zt0), (x_pie - 300, 1500), (x_pie - 2100, 1500)], fill=True, z=7)
    rect(ax, x_pie - 1900, 1500 - 350, 1400, 350, fill=True, z=7)
    # apoyo de transporte sobre contrapeso
    poly(ax, [(-3900, Z_CAPO), (-3500, Z_CAPO), (-3400, zt0), (-4000, zt0)], fill=True, z=7)
    eje(ax, 0, -500, 0, 4200)
    cota_h(ax, x_pie - L_base, x_pie, zt1, zt1 + 600, f"Longitud de transporte {L_base:.0f}")
    cota_v(ax, 0, zt1, x_pie + 200, x_pie + 1300, f"{zt1:.0f}")
    cota_h(ax, -2800, 2800, 0, -500, f"{ORUGA_L:.0f}", arriba=False)
    notas(marco, 28, 190, [
        f"Lote 1 — Máquina base sin tramo superior de mástil, sin Kelly ni herramientas: ≈ {(res.W - res.masa_kelly - 5600 - 3000)/1000:.0f} t",
        "Lote 2 — Tramo superior de mástil (5.5 m) + cabeza con poleas: ≈ 3.0 t",
        f"Lote 3 — Barra Kelly retraída {KELLY_RET/1000:.1f} m: ≈ {res.masa_kelly/1000:.1f} t",
        "Lote 4 — Herramientas (cubeta, hélice, corona, camisas)",
        "Opcional: contrapeso desmontable (18 t) si lo exige la normativa de carreteras.",
        "Ancho de transporte 3000 mm con orugas retraídas (trocha 2200 mm).",
    ], titulo="LOTES DE TRANSPORTE")

    ax2 = vista(fig, 330, 200, (-1700, 1700), (-700, 4600), E, "ALZADO FRONTAL  E 1:75")
    linea(ax2, [-1700, 1700], [0, 0], lw=0.5)
    frontal(ax2, trocha=TROCHA_TR, mastil=False)
    rect(ax2, -MASTIL_ANCHO / 2, zt0, MASTIL_ANCHO, zt1 - zt0, fill=True, z=8)
    cota_h(ax2, -1500, 1500, 0, -500, "3000", arriba=False)

    # rango de trabajo del paralelogramo (E 1:100)
    E2 = 100
    ax3 = vista(fig, 28, 22, (-5000, 6500), (-600, 11500), E2, "RANGO DEL PARALELOGRAMO Y COMPROBACIÓN DE GIRO  E 1:100")
    linea(ax3, [-5000, 6500], [0, 0], lw=0.5)
    oruga_lateral(ax3, detalle=False)
    superestructura_lateral(ax3, capo=True)
    for rr, ls in ((3800, (0, (4, 2))), (4700, (0, (4, 2)))):
        dx = rr - R_PERF
        rect(ax3, MASTIL_X0 + dx, MASTIL_Z0, 800, 10500, ls=ls, lw=LW_FINA, z=4)
        eje(ax3, rr, -300, rr, 11000)
    cinematica_lateral(ax3)
    rect(ax3, MASTIL_X0, MASTIL_Z0, 800, 10500, fill=True, z=4)
    eje(ax3, R_PERF, -300, R_PERF, 11000)
    cota_h(ax3, 0, 3800, 0, -350, "3800", arriba=False)
    cota_h(ax3, 3800, 4700, 5000, 8500, "900")
    texto(ax3, 4250, 9300, "Radio 3800 – 4700", size=6)

    # inclinaciones del mástil
    ax4 = vista(fig, 160, 22, (-3000, 3000), (-600, 11500), E2, "INCLINACIÓN LATERAL ±5°  E 1:100")
    linea(ax4, [-3000, 3000], [0, 0], lw=0.5)
    frontal(ax4, mastil=False)
    for ang in (-5, 0, 5):
        a = np.radians(ang)
        pts = [(-325, 1800), (325, 1800), (325, 10000), (-325, 10000)]
        piv = np.array([0, 2500])
        rot = [(piv[0] + (x - piv[0]) * np.cos(a) - (z - piv[1]) * np.sin(a),
                piv[1] + (x - piv[0]) * np.sin(a) + (z - piv[1]) * np.cos(a)) for x, z in pts]
        poly(ax4, rot, lw=LW_VIS if ang == 0 else LW_FINA, ls="-" if ang == 0 else (0, (4, 2)),
             fill=(ang == 0), z=6 if ang == 0 else 7)
    texto(ax4, 0, 10800, "±5°", size=7)

    notas(marco, 250, 120, [
        "1. Montaje: el mástil se eleva con los cilindros de inclinación sin grúa auxiliar.",
        "2. El tramo superior de mástil se abisagra/atornilla con 2 bulones Ø120 + 16 tornillos M36 10.9.",
        "3. La Kelly se coloca con el cabrestante auxiliar (100 kN).",
        "4. Orugas telescópicas: 2 cilindros Ø125 por lado, carrera 1100 mm.",
        "5. Radio de perforación ajustable sin mover la máquina: 3800 – 4700 mm.",
        "6. Inclinación del mástil: lateral ±5°, longitudinal +15° / −5° (pilotes inclinados).",
        "7. Radio de cola 4300 mm; distancia mínima a obstáculos traseros 500 mm.",
        "8. Rampa máx. de traslación con mástil vertical: 15 % (sin Kelly extendida).",
    ], titulo="NOTAS DE MONTAJE Y OPERACIÓN")
    cajetin(marco, "TRANSPORTE Y RANGOS DE TRABAJO", "PR280-02", "1:75 / 1:100", 2, TOTAL_HOJAS)
    guardar(pdf, fig, "PR280-02")


# ---------------------------------------------------------------------------
# HOJA 3 — Mástil: sección, cabeza y unión
# ---------------------------------------------------------------------------
def hoja_3(pdf, res):
    fig, marco = nueva_hoja()
    # Sección A-A del mástil E 1:15
    E = 15
    ax = vista(fig, 25, 185, (-700, 900), (-500, 700), E, "SECCIÓN A-A — MÁSTIL CON CARRO DE ROTARIA  E 1:15")
    B, H = MASTIL_ANCHO, 800
    t_ala, t_alma = 30, 20
    # cajón (x = profundidad hacia delante, y = ancho)
    rect(ax, -H / 2, -B / 2, H, B, hatch="////", z=2)
    rect(ax, -H / 2 + t_alma, -B / 2 + t_ala, H - 2 * t_alma, B - 2 * t_ala, fill=True, z=3)
    # rigidizadores longitudinales
    for yy in (-B / 4, B / 4):
        rect(ax, -H / 2 + t_alma, yy - 8, 120, 16, hatch="////", z=4)
        rect(ax, H / 2 - t_alma - 120, yy - 8, 120, 16, hatch="////", z=4)
    # guías delanteras (carriles 100×60)
    for yy in (-B / 2 + 40, B / 2 - 140):
        rect(ax, H / 2, yy, 60, 100, hatch="xxxx", z=4)
    # carro de rotaria con patines de bronce/poliamida
    poly(ax, [(H / 2 + 60, -B / 2 - 120), (H / 2 + 380, -B / 2 - 120), (H / 2 + 380, B / 2 + 120),
              (H / 2 + 60, B / 2 + 120), (H / 2 + 60, B / 2 + 60), (H / 2 + 20, B / 2 + 60),
              (H / 2 + 20, B / 2 - 20), (H / 2 + 60, B / 2 - 20), (H / 2 + 60, -B / 2 + 20),
              (H / 2 + 20, -B / 2 + 20), (H / 2 + 20, -B / 2 - 60), (H / 2 + 60, -B / 2 - 60)],
         hatch="\\\\\\\\", z=3)
    for yy in (-B / 2 + 40, B / 2 - 140):
        rect(ax, H / 2 + 60, yy - 15, 25, 130, fill=True, fc="#bbbbbb", z=5)
    # canal de mangueras y cables en dorso
    rect(ax, -H / 2 - 180, -200, 180, 400, lw=LW_FINA, z=3)
    for yy in (-120, -40, 40, 120):
        circ(ax, -H / 2 - 90, yy, 32, lw=LW_FINA)
    eje(ax, -650, 0, 850, 0)
    eje(ax, 0, -450, 0, 450)
    cota_h(ax, -H / 2, H / 2, -B / 2, -B / 2 - 100, "800", arriba=False)
    cota_v(ax, -B / 2, B / 2, -H / 2 - 180, -H / 2 - 320, "650")
    cota_h(ax, H / 2, H / 2 + 380, B / 2 + 120, B / 2 + 250, "380")
    texto(ax, 0, 0, "Chapa S690QL\nalas t=30, almas t=20", size=6)
    texto(ax, H / 2 + 220, 0, "Carro\nrotaria", size=5.5, rotation=90)
    texto(ax, -H / 2 - 90, 280, "Canal\nmangueras", size=5)

    # Cabeza de mástil E 1:25
    E2 = 40
    ax2 = vista(fig, 172, 66, (1900, 5000), (20900, 24300), E2, "DETALLE B — CABEZA DE MÁSTIL  E 1:40")
    poly(ax2, [(MASTIL_X0 - 150, MASTIL_Z1), (R_PERF + 250, MASTIL_Z1), (R_PERF + 250, MASTIL_Z1 + 400),
               (R_PERF - 150, CABEZA_Z1), (MASTIL_X0 + 150, CABEZA_Z1), (MASTIL_X0 - 150, MASTIL_Z1 + 700)],
         fill=True, z=2)
    rect(ax2, MASTIL_X0, 20900, 800, MASTIL_Z1 - 20900, fill=True, z=2)
    for (xc, zc, r, nom) in ((R_PERF - 450, Z_POLEA, 450, "Polea principal Ø900\n(D/d = 28)"),
                             (MASTIL_X0 + 50, Z_POLEA - 150, 300, "Polea desvío Ø600"),
                             (R_PERF - 150, MASTIL_Z1 + 250, 180, "Polea aux. Ø360")):
        circ(ax2, xc, zc, r, z=4)
        circ(ax2, xc, zc, r - 40, lw=LW_FINA, z=4)
        circ(ax2, xc, zc, 90 if r > 200 else 50, hatch="xxxx", z=4)
        eje(ax2, xc - r - 100, zc, xc + r + 100, zc)
        eje(ax2, xc, zc - r - 100, xc, zc + r + 100)
    linea(ax2, [R_PERF, R_PERF], [20900, Z_POLEA], lw=0.8, z=5)
    linea(ax2, [MASTIL_X0 - 250, MASTIL_X0 - 250], [20900, Z_POLEA - 150], lw=0.8, z=5)
    linea(ax2, [MASTIL_X0 + 50, R_PERF - 450], [Z_POLEA + 150, Z_POLEA + 450], lw=0.8, z=5)
    marca(ax2, R_PERF - 450, Z_POLEA + 300, 1, 18, 6)
    marca(ax2, MASTIL_X0 + 50, Z_POLEA, 2, -14, 10)
    marca(ax2, R_PERF - 150, MASTIL_Z1 + 250, 3, 18, -8)
    marca(ax2, R_PERF, 21300, 4, 14, -4)
    cota_v(ax2, MASTIL_Z1, CABEZA_Z1, R_PERF + 250, R_PERF + 550, f"{CABEZA_Z1 - MASTIL_Z1:.0f}")
    texto(ax2, 3350, 21100, "Cable principal Ø32", size=5.5)

    # Unión del tramo superior E 1:20
    E3 = 25
    ax3 = vista(fig, 25, 66, (-800, 1600), (-900, 1500), E3, "DETALLE C — UNIÓN TRAMO SUPERIOR  E 1:25")
    rect(ax3, -400, -900, 800, 880, fill=True, z=2)
    rect(ax3, -400, 20, 800, 880, fill=True, z=2)
    rect(ax3, -460, -60, 920, 40, hatch="////", z=3)
    rect(ax3, -460, 20, 920, 40, hatch="////", z=3)
    for xb in np.linspace(-350, 350, 8):
        rect(ax3, xb - 18, -120, 36, 240, fill=True, fc="#bbbbbb", lw=LW_FINA, z=4)
    circ(ax3, -250, 0, 60, hatch="xxxx", z=5)
    # orejetas de articulación
    poly(ax3, [(-400, -300), (-650, -150), (-650, 150), (-400, 300)], fill=True, z=1)
    circ(ax3, -560, 0, 60, hatch="xxxx", z=5)
    texto(ax3, 900, 700, "Tramo superior\n(abatible)", size=6)
    texto(ax3, 900, -600, "Tramo base", size=6)
    texto(ax3, 900, 0, "Brida t=40\n16 × M36 10.9\npar de apriete 2800 Nm", size=5.5)
    marca(ax3, -560, 0, 5, -8, 16)
    cota_h(ax3, -460, 460, 20, 1100, "920")

    # alzado del mástil con indicación de corte y detalles E 1:150
    E4 = 150
    ax4 = vista(fig, 135, 66, (1500, 5200), (-500, 24300), E4, "MÁSTIL — ALZADO  E 1:150")
    mastil_lateral(ax4, kelly=False, herramienta=False)
    linea(ax4, [1500, 5200], [0, 0], lw=0.5)
    corte(ax4, 1800, 12000, 3900, 12000, "A")
    circ(ax4, 3300, 22500, 1300, lw=LW_FINA, ls=(0, (4, 2)))
    texto(ax4, 3300, 24200, "B", size=8, weight="bold")
    circ(ax4, 2850, Z_UNION_SUP, 800, lw=LW_FINA, ls=(0, (4, 2)))
    texto(ax4, 1900, Z_UNION_SUP + 700, "C", size=8, weight="bold")
    cota_v(ax4, MASTIL_Z0, MASTIL_Z1, MASTIL_X0 - 900, MASTIL_X0 - 1000, f"{MASTIL_Z1 - MASTIL_Z0:.0f}")

    filas = [("POS.", "DESIGNACIÓN", "MATERIAL / NORMA"),
             ("1", "Polea principal Ø900, garganta Ø33", "EN-GJS-600 / EN 13001"),
             ("2", "Polea de desvío Ø600", "EN-GJS-600"),
             ("3", "Polea auxiliar Ø360", "EN-GJS-600"),
             ("4", "Cable principal Ø32 35×K7 1960", "EN 12385-4"),
             ("5", "Bulón de articulación Ø120", "42CrMo4 QT"),
             ("—", "Mástil cajón (alas 30, almas 20)", "S690QL EN 10025-6"),
             ("—", "Carriles guía 100×60", "Hardox 450"),
             ("—", "Patines carro", "PA6 + MoS2")]
    tabla(marco, 262, 278, filas, [12, 72, 60], alto=5.0, titulo="LISTA DE PIEZAS — MÁSTIL")
    notas(marco, 262, 226, [
        "1. Soldaduras de penetración completa en esquinas del cajón, clase B (ISO 5817).",
        "2. Diafragmas interiores t=15 cada 1500 mm.",
        "3. Rectitud de carriles guía: 1 mm / 2 m, 3 mm en toda la longitud.",
        "4. Relación D/d de poleas ≥ 25 (EN 16228-2 / EN 13001-3-2).",
        "5. Pintura: granallado Sa 2½, epoxi-zinc 80 µm + PU 120 µm.",
        "6. Inspección END: 100 % UT en uniones a tope de alas.",
    ])
    cajetin(marco, "MÁSTIL — SECCIÓN Y DETALLES", "PR280-03", "INDICADAS", 3, TOTAL_HOJAS)
    guardar(pdf, fig, "PR280-03")


# ---------------------------------------------------------------------------
# HOJA 4 — Mesa rotaria
# ---------------------------------------------------------------------------
def hoja_4(pdf, res):
    fig, marco = nueva_hoja()
    E = 15
    ax = vista(fig, 28, 60, (-1400, 1100), (-500, 2500), E, "SECCIÓN D-D — MESA ROTARIA 280 kNm  E 1:15")
    # carcasa (sección)
    t = 40
    poly(ax, [(-850, 100), (850, 100), (850, 1300), (-850, 1300)], z=1)
    for (x0, x1) in ((-850, -850 + t), (850 - t, 850)):
        rect(ax, x0, 100, x1 - x0, 1200, hatch="////", z=3)
    rect(ax, -850, 100, 1700 - 0, t, hatch="////", z=3)
    rect(ax, -850, 1300 - t, 1700, t, hatch="////", z=3)
    rect(ax, -850, 700, 1700, 30, hatch="////", z=3)  # diafragma intermedio
    # camisa de arrastre (quill): Kelly Ø508 + chavetas 18 → ID 560
    RK, RQi, RQo = KELLY_D / 2, 280, 345
    for s in (-1, 1):
        def r_(a, b, z0, h, **kw):
            lo, hi = sorted((s * a, s * b))
            rect(ax, lo, z0, hi - lo, h, **kw)
        r_(RQi, RQo, -150, 1650, hatch="\\\\\\\\", z=4)
        # corona dentada (bull gear)
        r_(RQo, RQo + 210, 420, 220, hatch="xxxx", z=4)
        # rodamientos
        r_(RQo, RQo + 140, 930, 160, fill=True, fc="#dddddd", z=4)
        circ(ax, s * (RQo + 70), 1010, 50, z=5)
        r_(RQo, RQo + 140, 160, 140, fill=True, fc="#dddddd", z=4)
        circ(ax, s * (RQo + 70), 230, 45, z=5)
        # amortiguador elastomérico
        r_(RQo, RQo + 120, 1320, 160, hatch="....", z=4)
        # chavetas de arrastre internas
        r_(RQi - 22, RQi, -100, 1500, fill=True, fc="#999999", lw=LW_FINA, z=5)
        # retén inferior
        r_(RQo, RQo + 40, 100, 40, fill=True, fc="#555555", z=6)
        # motores + reductores planetarios
        xm = s * 620
        rect(ax, xm - 180, 1300, 360, 450, fill=True, z=4)
        for zz in (1400, 1520, 1640):
            linea(ax, [xm - 180, xm + 180], [zz, zz], lw=LW_FINA, z=5)
        rect(ax, xm - 130, 1750, 260, 420, fill=True, z=4)
        rect(ax, xm - 60, 2170, 120, 80, fill=True, z=4)
        # piñón
        rect(ax, xm - 70, 440, 140, 180, hatch="xxxx", z=5)
        eje(ax, xm, 350, xm, 2300)
    # carro de guía en el mástil
    rect(ax, -1250, -150, 400, 1650, hatch="////", z=2)
    for zz in (0, 1250):
        rect(ax, -1330, zz, 80, 200, fill=True, fc="#bbbbbb", z=3)
    # kelly (fantasma)
    for s in (-1, 1):
        linea(ax, [s * RK, s * RK], [-500, 2500], lw=LW_FINA, ls=(0, (8, 2, 2, 2)), z=6)
    eje(ax, 0, -500, 0, 2500)
    marca(ax, 850, 900, 1, 14, 6)
    marca(ax, 450, 530, 2, 22, -8)
    marca(ax, 400, 1010, 3, 20, 4)
    marca(ax, -620, 530, 4, -10, -18)
    marca(ax, 620, 1500, 5, 18, 4)
    marca(ax, 620, 1950, 6, 16, 10)
    marca(ax, 390, 1400, 7, 24, 14)
    marca(ax, 310, 0, 8, 22, -12)
    marca(ax, 268, 800, 9, 20, -4)
    marca(ax, -1050, 1000, 10, -6, 14)
    cota_h(ax, -850, 850, 100, -300, "1700", arriba=False)
    cota_v(ax, -150, 2250, 850, 1050, "2400")
    cota_h(ax, -620, 620, 2250, 2380, "1240")
    cota_h(ax, -RK, RK, -150, -450, f"Ø{KELLY_D:.0f} Kelly", arriba=False)

    # planta
    ax2 = vista(fig, 225, 165, (-1400, 1100), (-1100, 1100), 20, "PLANTA — DISPOSICIÓN DE MOTORES  E 1:20")
    circ(ax2, 0, 0, 850, fill=True)
    circ(ax2, 0, 0, 540, lw=LW_FINA, ls=(0, (4, 2)))
    circ(ax2, 0, 0, 490, lw=LW_FINA, ls=(0, (8, 2, 2, 2)))
    circ(ax2, 0, 0, 345, fill=True)
    circ(ax2, 0, 0, 280, fill=True, fc="#f4f4f4")
    for a in (0, 120, 240):
        ar = np.radians(a)
        cx, cy = 620 * np.cos(ar), 620 * np.sin(ar)
        circ(ax2, cx, cy, 180, fill=True, z=4)
        circ(ax2, cx, cy, 130, lw=LW_FINA, z=4)
        circ(ax2, cx, cy, 130 - 60, lw=LW_FINA, ls=(0, (4, 2)), z=4)
        eje(ax2, 0, 0, 800 * np.cos(ar), 800 * np.sin(ar))
    for a in (90, 210, 330):
        ar = np.radians(a)
        c, s_ = np.cos(ar), np.sin(ar)
        pts = [(-20, 254), (20, 254), (20, 272), (-20, 272)]
        poly(ax2, [(x * s_ + y * c, -x * c + y * s_) for x, y in [(p[0], p[1]) for p in pts]],
             fill=True, fc="#999999", z=5)
    circ(ax2, 0, 0, KELLY_D / 2, hatch="////", z=4)
    rect(ax2, -1250, -700, 400, 1400, hatch="////", z=3)
    eje(ax2, -1350, 0, 1000, 0)
    eje(ax2, 0, -1000, 0, 1000)
    corte(ax2, -1350, -40, 1000, -40, "D")
    texto(ax2, 620 * np.cos(np.radians(120)), 620 * np.sin(np.radians(120)) + 260, "M2", size=6)
    texto(ax2, 620, 260, "M1", size=6)
    texto(ax2, 620 * np.cos(np.radians(240)), 620 * np.sin(np.radians(240)) - 260, "M3", size=6)
    texto(ax2, 0, -950, "3 × 120° — distancia entre ejes piñón/corona 620", size=5.5)

    filas = [("POS.", "DESIGNACIÓN", "CANT.", "ESPECIFICACIÓN"),
             ("1", "Carcasa reductor soldada", "1", "S355J2, alivio de tensiones"),
             ("2", "Corona dentada z=98, m=10", "1", "18CrNiMo7-6 cementado 58 HRC"),
             ("3", "Rodamiento axial-radial sup.", "1", "Rodillos cónicos, C0 ≥ 4500 kN"),
             ("4", "Piñón z=26, m=10", "3", "18CrNiMo7-6 cementado"),
             ("5", "Reductor planetario i=38", "3", "Par salida 26 kNm"),
             ("6", "Motor pistones axiales 160 cc", "3", "Desplaz. variable, 350 bar"),
             ("7", "Amortiguador de impactos", "1", "Elastómero PU 90 Sh A"),
             ("8", "Camisa de arrastre (quill)", "1", "42CrMo4 QT, ID 560"),
             ("9", "Chavetas internas de arrastre", "3", "Hardox 500, intercambiables"),
             ("10", "Carro con patines guía", "1", "S690QL + PA6")]
    y = tabla(marco, 215, 152, filas, [11, 58, 11, 75], alto=4.6, titulo="LISTA DE PIEZAS — MESA ROTARIA", size=5.3)
    rel = 98 / 26
    filas2 = [("MODO", "rpm", "Par [kNm]"),
              ("1.ª marcha (3 motores, máx. cilindrada)", "0 – 9", "280"),
              ("2.ª marcha (desplaz. mínimo)", "0 – 18", "150"),
              ("3.ª marcha (2 motores)", "0 – 30", "90"),
              ("Centrifugado (spin-off)", "90", "—")]
    tabla(marco, 215, y - 10, filas2, [90, 25, 40], alto=4.6, titulo=f"CARACTERÍSTICAS — relación total i = {rel:.2f} × 38 = {rel*38:.0f}")
    cajetin(marco, "MESA ROTARIA — SECCIÓN Y PLANTA", "PR280-04", "1:15 / 1:20", 4, TOTAL_HOJAS)
    guardar(pdf, fig, "PR280-04")


# ---------------------------------------------------------------------------
# HOJA 5 — Barra Kelly
# ---------------------------------------------------------------------------
def hoja_5(pdf, res):
    fig, marco = nueva_hoja()
    E = 200
    L_sec = C.KELLY[0].L * 1000
    sol = C.SOLAPE_KELLY * 1000
    L_ext = res.L_ext * 1000
    ztop = 900
    ax = vista(fig, 42, 25, (-2000, 5000), (-L_ext - 1200, 2200), E, "KELLY RETRAÍDA / EXTENDIDA  E 1:200")
    # retraída
    for i, k in enumerate(C.KELLY):
        D = k.D * 1000
        rect(ax, -D / 2, ztop - L_sec - i * 150, D, L_sec, fill=(i == 0), lw=LW_VIS if i == 0 else LW_FINA,
             ls="-" if i == 0 else (0, (4, 2)), z=3)
    rect(ax, -300, ztop, 600, 500, fill=True, z=4)
    texto(ax, 0, 1900, "Retraída", size=6, weight="bold")
    cota_v(ax, ztop - KELLY_RET, ztop, -300, -1100, f"{KELLY_RET:.0f}")
    # extendida
    xe = 3000
    for i, k in enumerate(C.KELLY):
        D = k.D * 1000
        z0 = ztop - i * (L_sec - sol)
        rect(ax, xe - D / 2, z0 - L_sec, D, L_sec, fill=True, z=3 + i)
        texto(ax, xe + 450, z0 - L_sec / 2, f"S{i+1}\nØ{D:.0f}", size=5.5, ha="left")
    rect(ax, xe - 300, ztop, 600, 500, fill=True, z=8)
    zb = ztop - 3 * (L_sec - sol) - L_sec
    rect(ax, xe - 100, zb - 300, 200, 300, fill=True, z=8)
    texto(ax, xe, 1900, "Extendida", size=6, weight="bold")
    cota_v(ax, zb, ztop, xe - 300, xe - 1100, f"{L_ext:.0f}")
    for i in range(1, 4):
        z0 = ztop - i * (L_sec - sol)
        linea(ax, [xe - 250, xe + 250], [z0, z0], lw=0.6, z=9)
    z_ter = ztop - C.SOBRESALIENTE_KELLY * 1000
    linea(ax, [xe - 900, xe + 1900], [z_ter, z_ter], lw=0.6, z=1)
    texto(ax, xe + 450, z_ter + 700, "±0.00 terreno", size=5, ha="left")
    corte(ax, -700, -6000, 700, -6000, "E")

    # sección E-E E 1:5
    E2 = 5
    ax2 = vista(fig, 90, 140, (-330, 330), (-330, 330), E2, "SECCIÓN E-E — KELLY CON BLOQUEO (INTERLOCKING)  E 1:5")
    hatches = ["////", "\\\\\\\\", "////", "xxxx"]
    hk = C.ALTURA_CHAVETA * 1000
    th = np.linspace(0, 2 * np.pi, 160)

    def pieza_polar(ang, r0, r1, ancho, z):
        c, s_ = np.cos(ang), np.sin(ang)
        loc = [(-ancho / 2, r0), (ancho / 2, r0), (ancho / 2, r1), (-ancho / 2, r1)]
        poly(ax2, [(y * c - x * s_, y * s_ + x * c) for x, y in loc], fill=True, fc="#888888",
             lw=LW_FINA, z=z)

    for i, k in enumerate(C.KELLY):
        R, r = k.D * 500, k.D * 500 - k.t * 1000
        pts = [(R * np.cos(a), R * np.sin(a)) for a in th] + [(r * np.cos(a), r * np.sin(a)) for a in th[::-1]]
        poly(ax2, pts, hatch=hatches[i], z=2, lw=LW_VIS)
        for a in (90, 210, 330):
            ar = np.radians(a)
            # chaveta exterior de arrastre (40 × 18)
            pieza_polar(ar, R, R + hk, 40, 4)
            # regletas interiores que abrazan la chaveta de la sección siguiente
            if i < len(C.KELLY) - 1:
                for d in (-1, 1):
                    ang = ar + d * (32 / r)
                    pieza_polar(ang, r - hk, r, 20, 4)
    for i, k in enumerate(C.KELLY):
        ang = np.radians(-35)
        Rm = k.D * 500 - k.t * 500
        marca(ax2, Rm * np.cos(ang), Rm * np.sin(ang), i + 1, 14 + 4 * i, -6 - 7 * i)
    eje(ax2, -320, 0, 320, 0)
    eje(ax2, 0, -320, 0, 320)
    cota_h(ax2, -254, 254, 0, 300, "Ø508")

    # detalle punto de bloqueo E 1:5
    ax3 = vista(fig, 235, 140, (-300, 300), (-330, 330), E2, "DETALLE F — PUNTO DE BLOQUEO  E 1:5")
    k1, k2 = C.KELLY[0], C.KELLY[1]
    r1 = k1.D * 500 - k1.t * 1000
    R2 = k2.D * 500
    x_ext = -150
    rect(ax3, x_ext - k1.t * 1000, -330, k1.t * 1000, 660, hatch="////", z=2)            # tubo S1
    rect(ax3, x_ext, -330, hk, 660, fill=True, fc="#bbbbbb", lw=LW_FINA, z=2)            # regleta S1
    poly(ax3, [(x_ext, -90), (x_ext + hk, -90), (x_ext + hk, 90), (x_ext, 90)], fill=True, z=3)  # bolsillo
    x2 = x_ext + (r1 - R2)
    rect(ax3, x2, -330, k2.t * 1000, 660, hatch="\\\\\\\\", z=2)                      # tubo S2
    poly(ax3, [(x2 - hk, -70), (x2, -70), (x2, 70), (x2 - hk, 70)], hatch="xxxx", z=4)   # tope de S2
    rect(ax3, x2 - hk, 90, hk, 240, fill=True, fc="#888888", lw=LW_FINA, z=3)             # chaveta S2
    texto(ax3, 20, 190, "Tope de la sección 2 alojado en el bolsillo\nde la regleta de S1 al girar a derechas:\n"
                        "transmite el empuje (bloqueo)", size=5.5, ha="left")
    texto(ax3, 20, -180, "Bolsillos: 4 niveles por sección\n(cada 3.0 m), longitud 180 mm.\n"
                         "Giro a izquierdas → desbloqueo", size=5.5, ha="left")
    marca(ax3, x_ext + hk / 2, 0, 1, -12, 18)
    marca(ax3, x2 - hk / 2, 0, 2, -12, -18)

    filas = [("SECCIÓN", "Ø ext. × t [mm]", "L [m]", "J [cm⁴]", "τ(280 kNm) [MPa]", "Masa [kg]")]
    for k in C.KELLY:
        tau = 280e3 * k.D / 2 / k.J / 1e6
        filas.append((k.nombre, f"{k.D*1000:.0f} × {k.t*1000:.0f}", f"{k.L:.1f}", f"{k.J*1e8:,.0f}",
                      f"{tau:.0f}", f"{k.masa:,.0f}"))
    filas.append(("TOTAL", "", "", "", "adm. 267", f"{res.masa_kelly:,.0f}"))
    tabla(marco, 90, 100, filas, [40, 30, 14, 22, 30, 20], alto=4.8,
          titulo="TABLA DE SECCIONES — KELLY 4 × 12.5 m (42CrMo4 QT, fy ≥ 690 MPa)")
    notas(marco, 262, 100, [
        f"Longitud retraída {KELLY_RET/1000:.1f} m; extendida {res.L_ext:.1f} m.",
        f"Profundidad máx. con cubeta: {res.prof_max:.1f} m (requerida 40 m).",
        f"Solape mínimo entre secciones: {C.SOLAPE_KELLY:.1f} m.",
        "Chavetas 3 × 120°, 40 × 18 mm; juego radial 3 mm.",
        "Caja Kelly inferior: cuadrado 200 mm, bulón Ø70.",
        "Giratorio superior con rodamiento axial y muelles.",
        "Rectitud por sección: 1 mm/m, máx. 8 mm.",
    ], titulo="NOTAS — BARRA KELLY")
    cajetin(marco, "BARRA KELLY TELESCÓPICA 4 SECCIONES", "PR280-05", "1:200 / 1:5", 5, TOTAL_HOJAS)
    guardar(pdf, fig, "PR280-05")


# ---------------------------------------------------------------------------
# HOJA 6 — Herramientas de perforación
# ---------------------------------------------------------------------------
def hoja_6(pdf, res):
    fig, marco = nueva_hoja()
    E = 25
    y0 = 112

    # 1) Cubeta
    ax = vista(fig, 25, y0, (-900, 900), (-500, 2100), E, "CUBETA Ø1200 (suelos)  E 1:25")
    cubeta_lateral(ax, 0, 0, z=3)
    rect(ax, -100, HERR_H, 200, 300, fill=True, z=4)
    eje(ax, 0, -450, 0, 2000)
    cota_h(ax, -600, 600, 0, -350, "Ø1200 (corte)", arriba=False)
    cota_v(ax, -60, HERR_H, -590, -780, "1560")
    texto(ax, 0, 700, "V = 1.31 m³", size=6, bbox=dict(fc="white", ec="none"))
    # planta de fondo
    ax_b = vista(fig, 25, 48, (-900, 900), (-700, 700), E, "CUBETA — VISTA INFERIOR  E 1:25")
    circ(ax_b, 0, 0, 600)
    for s in (-1, 1):
        poly(ax_b, [(0, 0)] + [(560 * np.cos(a), 560 * np.sin(a)) for a in
                               np.linspace(np.radians(15 if s > 0 else 195), np.radians(165 if s > 0 else 345), 30)],
             lw=LW_FINA)
        for a in np.linspace(0, 1, 5):
            x = s * (100 + a * 480)
            poly(ax_b, [(x - 30, -s * 20), (x + 30, -s * 20), (x + 30, -s * 90), (x - 30, -s * 90)],
                 fill=True, fc="#999999", lw=LW_FINA)
    rect(ax_b, -50, -50, 100, 100, fill=True)

    # 2) Hélice
    ax2 = vista(fig, 105, y0 - 20, (-900, 900), (-500, 3000), E, "HÉLICE Ø1200 (suelos cohesivos)  E 1:25")
    H = 2500
    rect(ax2, -137, 0, 274, H, fill=True, z=3)
    paso = 600
    for k in range(int(H / paso) + 1):
        zb = k * paso
        if zb + paso / 2 > H:
            break
        poly(ax2, [(-600, zb), (600, zb + paso / 2), (600, zb + paso / 2 + 50), (-600, zb + 50)], fill=True, z=4)
        poly(ax2, [(-600, zb + 50), (-600, zb + 50 + paso / 2 - 50), (600, zb + paso + 0), (600, zb + paso / 2 + 50)],
             lw=LW_FINA, z=2, ls=(0, (4, 2)))
    for xd in np.linspace(-560, 560, 8):
        poly(ax2, [(xd - 25, 20), (xd + 25, 20), (xd + 10, -90), (xd - 10, -90)], fill=True, fc="#999999",
             lw=LW_FINA, z=5)
    rect(ax2, -60, -350, 120, 350, fill=True, z=5)
    rect(ax2, -100, H, 200, 300, fill=True, z=4)
    eje(ax2, 0, -450, 0, 2950)
    cota_h(ax2, -600, 600, 0, -420, "Ø1200", arriba=False)
    cota_v(ax2, 0, paso, 600, 800, "paso 600")
    cota_v(ax2, -350, H + 300, -600, -780, f"{H + 650:.0f}")

    # 3) Corona
    ax3 = vista(fig, 185, y0, (-900, 900), (-500, 2100), E, "CORONA DE CORTE Ø1200 (roca)  E 1:25")
    rect(ax3, -600, 0, 25, 1500, hatch="////", z=3)
    rect(ax3, 575, 0, 25, 1500, hatch="////", z=3)
    rect(ax3, -575, 25, 1150, 1475, lw=LW_FINA, z=2)
    rect(ax3, -600, 1450, 1200, 50, hatch="////", z=3)
    for s in (-1, 1):
        for k in range(3):
            poly(ax3, [(s * 600 - 30, -10), (s * 600 + 30, -10), (s * 600 + 15 * s, -120), (s * 600 - 15 * s, -120)],
                 fill=True, fc="#777777", lw=LW_FINA, z=4)
    for xd in np.linspace(-450, 450, 7):
        rect(ax3, xd - 25, 0, 50, 80, fill=True, fc="#aaaaaa", lw=LW_FINA, z=3)
        poly(ax3, [(xd - 15, 0), (xd + 15, 0), (xd, -110)], fill=True, fc="#777777", lw=LW_FINA, z=4)
    rect(ax3, -100, 1500, 200, 300, fill=True, z=4)
    eje(ax3, 0, -450, 0, 2000)
    cota_h(ax3, -600, 600, 0, -380, "Ø1200", arriba=False)
    texto(ax3, 0, 800, "14 picas cónicas\nØ38 (WC)", size=5.5)

    # 4) Camisa
    ax4 = vista(fig, 265, 76, (-900, 900), (-500, 3700), E, "CAMISA DE ENTUBACIÓN Ø1200/1130  E 1:25")
    for s in (-1, 1):
        rect(ax4, s * 600 - (35 if s > 0 else 0), 0, 35 * (1), 3000, hatch="////", z=3)
    rect(ax4, -600, 1480, 1200, 40, lw=LW_FINA, z=4)
    for zz in (1500,):
        for s in (-1, 1):
            circ(ax4, s * 617, zz + 100, 18, z=5)
            circ(ax4, s * 617, zz - 100, 18, z=5)
    for xd in np.linspace(-560, 560, 10):
        poly(ax4, [(xd - 20, 0), (xd + 20, 0), (xd, -100)], fill=True, fc="#777777", lw=LW_FINA, z=4)
    rect(ax4, -600, 3000, 1200, 200, fill=True, z=4)
    rect(ax4, -100, 3200, 200, 300, fill=True, z=4)
    eje(ax4, 0, -450, 0, 3600)
    cota_h(ax4, -600, 600, 0, -380, "Ø1200 ext.", arriba=False)
    cota_v(ax4, 0, 3000, 600, 780, "3000")
    texto(ax4, 0, 1150, "Unión atornillada\ndoble pared\nt = 35", size=5.5)
    texto(ax4, 0, 3100, "Adaptador de arrastre", size=5)

    filas = [("HERRAMIENTA", "Ø [mm]", "Masa [kg]", "Aplicación"),
             ("Cubeta doble fondo", "1200", "3000", "Arenas, gravas, arcillas blandas"),
             ("Hélice doble entrada", "1200", "2600", "Arcillas firmes, limos"),
             ("Corona de corte", "1200", "2900", "Roca UCS ≤ 40 MPa, bolos"),
             ("Cubeta con camisa", "1100", "2700", "Interior de entubación"),
             ("Camisa 3 m (tramo)", "1200/1130", "3050", "Estabilización en suelos granulares")]
    tabla(marco, 25, 278, filas, [45, 20, 20, 70], alto=4.8, titulo="JUEGO DE HERRAMIENTAS Ø1200")
    notas(marco, 195, 281, [
        "Todas las herramientas con caja Kelly cuadrada 200 mm y bulón Ø70.",
        "Dientes: portadientes soldados, dientes intercambiables tipo Betek BFZ.",
        "Cubeta: fondo con apertura por pestillo automático al chocar con tope de la guía.",
        "Perforación con lodos bentoníticos o polímero cuando no se entuba.",
        "Tolerancia de verticalidad del pilote: ≤ 1:100 (EN 1536).",
    ], titulo="NOTAS — HERRAMIENTAS")
    cajetin(marco, "HERRAMIENTAS DE PERFORACIÓN Ø1200", "PR280-06", "1:25", 6, TOTAL_HOJAS)
    guardar(pdf, fig, "PR280-06")


# ---------------------------------------------------------------------------
# HOJA 7 — Esquema hidráulico
# ---------------------------------------------------------------------------
def _bomba(ax, x, y, nombre, var=True, motor=False, r=7):
    circ(ax, x, y, r, lw=0.6, fill=True)
    if motor:
        poly(ax, [(x, y + r * 0.1), (x - r * 0.35, y + r * 0.7), (x + r * 0.35, y + r * 0.7)], fill=True, fc="black", lw=0.1)
    else:
        poly(ax, [(x, y + r), (x - r * 0.35, y + r * 0.4), (x + r * 0.35, y + r * 0.4)], fill=True, fc="black", lw=0.1)
    if var:
        linea(ax, [x - r * 1.1, x + r * 1.1], [y - r * 1.1, y + r * 1.1], lw=0.4)
        poly(ax, [(x + r * 1.1, y + r * 1.1), (x + r * 0.7, y + r * 1.0), (x + r * 1.0, y + r * 0.7)], fill=True, fc="black", lw=0.1)
    texto(ax, x, y - r - 3.5, nombre, size=5.3)


def _cilindro(ax, x, y, nombre, w=22, h=6):
    rect(ax, x - w / 2, y - h / 2, w, h, lw=0.6, fill=True)
    linea(ax, [x - 2, x - 2], [y - h / 2, y + h / 2], lw=0.8)
    linea(ax, [x - 2, x + w / 2 + 6], [y, y], lw=0.8)
    texto(ax, x, y - h / 2 - 3, nombre, size=5.3)


def _valvula(ax, x, y, n=3, nombre=""):
    w = 10
    for i in range(n):
        rect(ax, x + i * w - n * w / 2, y - 4, w, 8, lw=0.5, fill=True)
    xs = x - n * w / 2
    linea(ax, [xs + w + 3, xs + w + 7], [y - 3, y + 3], lw=0.4)
    linea(ax, [xs + w + 7, xs + w + 3], [y - 3, y + 3], lw=0.4)
    linea(ax, [xs + 2 * w + 3, xs + 2 * w + 7], [y - 3, y + 3], lw=0.4)
    linea(ax, [xs + 2 * w + 3, xs + 2 * w + 7], [y + 3, y - 3], lw=0.4)
    if nombre:
        texto(ax, x, y + 7, nombre, size=5)


def hoja_7(pdf, res):
    fig, marco = nueva_hoja()
    ax = fig.add_axes([22 / 420, 55 / 297, 380 / 420, 225 / 297])
    ax.set_xlim(0, 380)
    ax.set_ylim(0, 225)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.escala = 1
    texto(ax, 190, 220, "ESQUEMA HIDRÁULICO PRINCIPAL (ISO 1219-1) — SIN ESCALA", size=8, weight="bold")
    # motor diésel y caja de bombas
    rect(ax, 10, 95, 36, 30, lw=0.8, fill=True)
    texto(ax, 28, 113, "MOTOR\nDIÉSEL", size=6, weight="bold")
    texto(ax, 28, 101, "354 kW\n1800 rpm", size=5)
    rect(ax, 52, 90, 16, 40, lw=0.8, fill=True)
    texto(ax, 60, 110, "CAJA\nTOMA\nFUERZA", size=4.5)
    linea(ax, [46, 52], [110, 110], lw=1.5)
    bombas = [(90, 180, "P1 360 l/min\nLS 350 bar"), (90, 145, "P2 360 l/min\nLS 350 bar"),
              (90, 90, "P3 180 l/min\ntraslación/giro"), (90, 45, "P4 engranajes\npilotaje/refrig.")]
    for bx, by, nom in bombas:
        linea(ax, [68, bx - 7], [110, by], lw=0.5)
        _bomba(ax, bx, by, nom, var=("P4" not in nom))
    # depósito
    poly(ax, [(75, 12), (75, 4), (125, 4), (125, 12)], closed=False, lw=0.8)
    texto(ax, 100, 8, "DEPÓSITO 650 l", size=5.5)
    for bx, by, _ in bombas:
        linea(ax, [bx, bx], [by - 7, 12], lw=0.3, ls=(0, (3, 2)))
    # bloque de distribución principal
    rect(ax, 130, 110, 80, 90, lw=0.8, ls=(0, (6, 2)))
    texto(ax, 170, 204, "BLOQUE PRINCIPAL LUDV (P1+P2)", size=5.5, weight="bold")
    val = [(170, 188, "Rotaria"), (170, 170, "Cabrestante ppal."), (170, 152, "Empuje"),
           (170, 134, "Cabrestante aux."), (170, 118, "Mástil / paralelogramo")]
    for vx, vy, n in val:
        _valvula(ax, vx, vy, nombre=n)
        linea(ax, [97, vx - 15], [180 if vy > 150 else 145, vy], lw=0.4)
    rect(ax, 130, 30, 80, 70, lw=0.8, ls=(0, (6, 2)))
    texto(ax, 170, 94, "BLOQUE TRASLACIÓN / GIRO (P3)", size=5.5, weight="bold")
    for vx, vy, n in ((170, 78, "Traslación izq."), (170, 60, "Traslación der."), (170, 42, "Giro superestr.")):
        _valvula(ax, vx, vy, nombre=n)
        linea(ax, [97, vx - 15], [90, vy], lw=0.4)
    # actuadores
    for i, y in enumerate((196, 186, 176)):
        _bomba(ax, 250 + i * 22, 190, f"M{i+1} 160cc", var=True, motor=True, r=6)
    linea(ax, [185, 244], [188, 190], lw=0.5)
    linea(ax, [256, 266], [190, 190], lw=0.5)
    linea(ax, [278, 288], [190, 190], lw=0.5)
    texto(ax, 272, 205, "MESA ROTARIA 280 kNm", size=6, weight="bold")
    _bomba(ax, 255, 170, "Cabr. ppal. 300 kN", motor=True, r=6)
    rect(ax, 268, 164, 22, 12, lw=0.6)
    texto(ax, 279, 170, "freno", size=4.5)
    linea(ax, [185, 249], [170, 170], lw=0.5)
    _bomba(ax, 255, 150, "Cabr. empuje 250 kN", motor=True, r=6)
    linea(ax, [185, 249], [152, 150], lw=0.5)
    _bomba(ax, 255, 130, "Cabr. aux. 100 kN", motor=True, r=6)
    linea(ax, [185, 249], [134, 130], lw=0.5)
    _cilindro(ax, 320, 150, "2× Cil. inclinación Ø200/140")
    _cilindro(ax, 320, 130, "Cil. paralelogramo Ø180/125")
    _cilindro(ax, 320, 112, "Cil. inclinación lateral")
    linea(ax, [185, 309], [118, 150], lw=0.4)
    linea(ax, [185, 309], [118, 130], lw=0.4)
    linea(ax, [185, 309], [118, 112], lw=0.4)
    _bomba(ax, 255, 80, "Traslación izq.", motor=True, r=6)
    _bomba(ax, 255, 60, "Traslación der.", motor=True, r=6)
    _bomba(ax, 255, 40, "Giro", motor=True, r=6)
    for yy, yv in ((80, 78), (60, 60), (40, 42)):
        linea(ax, [185, 249], [yv, yy], lw=0.5)
    _cilindro(ax, 320, 70, "4× Cil. orugas telescópicas Ø125")
    linea(ax, [185, 309], [60, 70], lw=0.3, ls=(0, (3, 2)))
    # refrigeración y filtros
    rect(ax, 20, 30, 40, 30, lw=0.6)
    texto(ax, 40, 45, "Enfriador aceite\n+ filtro retorno\n10 µm", size=5)
    linea(ax, [60, 83], [45, 45], lw=0.4)
    texto(ax, 340, 20, "Presión de trabajo 350 bar · pilotaje 35 bar · retorno 5 bar\n"
                       "Aceite HVLP 46 (ISO 11158) · limpieza ISO 4406 18/16/13", size=5.5)
    # control
    rect(ax, 300, 170, 70, 40, lw=0.6, ls=(0, (2, 2)))
    texto(ax, 335, 190, "CONTROL ELECTRÓNICO\nCAN-bus · joysticks EHC\nregistro de perforación\n(MWD: prof., par, verticalidad)", size=5)
    cajetin(marco, "ESQUEMA HIDRÁULICO PRINCIPAL", "PR280-07", "S/E", 7, TOTAL_HOJAS)
    guardar(pdf, fig, "PR280-07")


# ---------------------------------------------------------------------------
# HOJA 8 — Cálculos y verificaciones
# ---------------------------------------------------------------------------
def hoja_8(pdf, res):
    fig, marco = nueva_hoja()
    # diagrama de estabilidad (planta) E 1:100
    E = 125
    ax = vista(fig, 40, 178, (-5000, 5200), (-5000, 5000), E, "ESTABILIDAD — LÍNEAS DE VUELCO Y CdG  E 1:125")
    for s in (-1, 1):
        rect(ax, -ORUGA_L / 2, s * TROCHA_T / 2 - ZAPATA / 2, ORUGA_L, ZAPATA, lw=LW_FINA, fill=True, fc="#eeeeee")
    L2 = C.LONGITUD_APOYO_ORUGA * 500
    poly(ax, [(-L2, -TROCHA_T / 2), (L2, -TROCHA_T / 2), (L2, TROCHA_T / 2), (-L2, TROCHA_T / 2)],
         lw=1.0, ls=(0, (6, 2)))
    circ(ax, res.x_cg * 1000, 0, 120, fill=True, fc="black")
    texto(ax, res.x_cg * 1000, 350, f"CdG x={res.x_cg*1000:.0f}", size=5.5)
    circ(ax, R_PERF, 0, 600, lw=0.6)
    circ(ax, 0, R_PERF, 600, lw=0.6, ls=(0, (4, 2)))
    texto(ax, R_PERF, -850, "Kelly 0°", size=5.5)
    texto(ax, 850, R_PERF, "Kelly 90°", size=5.5, ha="left")
    circ(ax, 0, 0, R_PERF, lw=LW_FINA, ls=(0, (8, 3, 2, 3)))
    texto(ax, L2 + 150, -2700, "Línea de vuelco\nfrontal", size=5, ha="left")
    texto(ax, -4800, TROCHA_T / 2 + 200, "Línea de vuelco lateral", size=5, ha="left")
    eje(ax, -5000, 0, 5200, 0)
    eje(ax, 0, -4900, 0, 4900)

    # curva par-velocidad
    rpm, M = C.curva_par_velocidad()
    ax2 = fig.add_axes([190 / 420, 185 / 297, 95 / 420, 80 / 297])
    ax2.plot(rpm, M, color="black", lw=1.0)
    ax2.axhline(float(res.tabla["Par requerido suelo"].split()[0]), color="black", lw=0.6, ls="--")
    ax2.axhline(float(res.tabla["Par requerido roca"].split()[0]), color="black", lw=0.6, ls=":")
    ax2.text(18, 222, "req. roca", fontsize=5)
    ax2.text(18, 200, "req. suelo", fontsize=5)
    ax2.set_xlabel("Velocidad [rpm]", fontsize=6)
    ax2.set_ylabel("Par [kNm]", fontsize=6)
    ax2.set_title("Curva par – velocidad (290 kW)", fontsize=6.5, weight="bold")
    ax2.tick_params(labelsize=5.5)
    ax2.grid(lw=0.3)
    ax2.set_xlim(0, 32)
    ax2.set_ylim(0, 320)

    # presión sobre el terreno
    ax3 = fig.add_axes([305 / 420, 185 / 297, 95 / 420, 80 / 297])
    L = C.LONGITUD_APOYO_ORUGA
    A = 2 * C.ANCHO_ZAPATA * L
    W = res.W * C.G
    xs = np.linspace(-L / 2, L / 2, 50)
    for e, ls, lab in ((0, ":", "e = 0"), (res.x_cg, "-", f"e = {res.x_cg:.2f} m (0°)")):
        p = W / A * (1 + 12 * e * xs / L**2) / 1e3
        ax3.plot(xs, p, color="black", lw=0.9, ls=ls, label=lab)
    ax3.axhline(250, color="black", lw=0.6, ls="--")
    ax3.text(-2.2, 255, "límite 250 kPa", fontsize=5)
    ax3.set_xlabel("Posición a lo largo de la oruga [m]", fontsize=6)
    ax3.set_ylabel("Presión [kPa]", fontsize=6)
    ax3.set_title("Presión bajo orugas (servicio)", fontsize=6.5, weight="bold")
    ax3.tick_params(labelsize=5.5)
    ax3.legend(fontsize=5)
    ax3.grid(lw=0.3)
    ax3.set_ylim(0, 300)

    filas = [("VERIFICACIÓN", "VALOR", "LÍMITE", "UD.", "")]
    for nombre, val, lim, u, ok in res.verificaciones:
        filas.append((nombre, f"{val:.2f}", f"{lim:.2f}", u, "CUMPLE" if ok else "NO CUMPLE"))
    y = tabla(marco, 28, 162, filas, [95, 22, 22, 14, 22], alto=4.7, titulo="VERIFICACIONES (calculos.py)", size=5.3)

    filas = [("CONJUNTO", "MASA [t]", "x [m]", "z [m]")]
    for nombre, m, x, z in res.masas:
        filas.append((nombre, f"{m/1000:.1f}", f"{x:.2f}", f"{z:.2f}"))
    filas.append(("TOTAL / CdG", f"{res.W/1000:.1f}", f"{res.x_cg:.2f}", f"{res.z_cg:.2f}"))
    y2 = tabla(marco, 220, 162, filas, [100, 20, 20, 20], alto=4.7, titulo="MASAS Y CENTRO DE GRAVEDAD", size=5.3)
    notas(marco, 220, y2 - 5, [
        "Par suelo: M = f·R²·1.3, f = 450 kN/m (grava densa/roca blanda).",
        "Par roca: 14 picas · 3.2·UCS·(10×25 mm²)·R·1.3, UCS = 25 MPa.",
        "Cabrestante: (Kelly + cubeta + suelo)·g·1.6 (succión y dinámica).",
        "Kelly: τ = M·r/J ≤ 0.58·fy/1.5; pandeo Euler K = 1 (guiada).",
        "Vuelco: ΣM_est/ΣM_vol ≥ 1.4 con viento 20 m/s sobre el mástil.",
        "Normas: EN 16228-1/-2, EN 13001, EN 1536, ISO 5817, ISO 4406.",
    ], titulo="HIPÓTESIS", size=5.3, paso=3.2)
    cajetin(marco, "MEMORIA DE CÁLCULO — RESUMEN", "PR280-08", "1:125 / S/E", 8, TOTAL_HOJAS)
    guardar(pdf, fig, "PR280-08")


def guardar(pdf, fig, nombre):
    pdf.savefig(fig)
    fig.savefig(os.path.join(SALIDA, f"{nombre}.png"), dpi=130)
    plt.close(fig)


def main():
    os.makedirs(SALIDA, exist_ok=True)
    res = C.calcular()
    ruta = os.path.join(SALIDA, "UT-PR280_planos.pdf")
    with PdfPages(ruta) as pdf:
        for h in (hoja_1, hoja_2, hoja_3, hoja_4, hoja_5, hoja_6, hoja_7, hoja_8):
            h(pdf, res)
        d = pdf.infodict()
        d["Title"] = "UT-PR280 — Planos de perforadora rotativa para pilotes Ø1200 × 40 m"
        d["Author"] = "Utech"
    print(f"Planos generados en {ruta}")


if __name__ == "__main__":
    main()
