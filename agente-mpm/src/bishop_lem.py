"""
bishop_lem.py — Factor de Seguridad de la Seccion A-A real por EQUILIBRIO LIMITE
(Bishop simplificado, superficies circulares), con estratigrafia Dearman real
(4 horizontes del DXF) y nivel freatico NF critico.

Herramienta estandar de estabilidad de taludes (lo que MPM-SRM no da limpio).
Lee el DXF directo (perfil TERRENO, NF NAF_CRITICO, contactos CONTORNO).

Salida: FS minimo + circulo critico + figura.
"""
import sys, os, json
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import dxf_to_section as D

DXF = "/home/user/Utech/#seccion_A-A.dxf"
ROOT = os.path.abspath(os.path.join(HERE, ".."))
GW = 9.81  # kN/m3

# Parametros por horizonte (tabla Dearman; bedrock I = muy resistente, no falla)
HOR = {
    "VI": dict(c=10.0, phi=25.0, gd=18.0, gsat=20.0),
    "V":  dict(c=20.0, phi=30.0, gd=19.0, gsat=21.0),
    "IV": dict(c=50.0, phi=34.0, gd=21.0, gsat=21.5),
    "I":  dict(c=500.0, phi=45.0, gd=26.0, gsat=26.3),  # bedrock: resistente
}


def load_curves():
    polys = D.extract_polylines(DXF)
    def longest(layer):
        c = [p for p in polys if p["layer"] == layer]
        a = np.array(max(c, key=lambda d: d["length"])["pts"]); return a[np.argsort(a[:, 0])]
    ter = longest("TERRENO"); naf = longest("NAF_CRITICO")
    cons = sorted([p for p in polys if p["layer"] == "CONTORNO"],
                  key=lambda d: np.array(d["pts"])[:, 0].max())
    def pick(xt):
        a = np.array([p for p in cons if abs(np.array(p["pts"])[:, 0].max() - xt) < 8][0]["pts"])
        return a[np.argsort(a[:, 0])]
    c_viv, c_v4, c_4i = pick(89), pick(99), pick(113)  # VI/V, V/IV, IV/I
    return ter, naf, (c_viv, c_v4, c_4i)


def make_funcs():
    ter, naf, (c_viv, c_v4, c_4i) = load_curves()
    yt = lambda x: np.interp(x, ter[:, 0], ter[:, 1])
    yw = lambda x: np.interp(x, naf[:, 0], naf[:, 1])
    # contactos: por encima del contacto => estrato superior; +inf fuera de rango (aflorado)
    def cc(c, x): return np.interp(x, c[:, 0], c[:, 1], left=c[1, 1], right=np.inf)
    def horizon(x, z):
        if z >= cc(c_viv, x): return "VI"
        if z >= cc(c_v4, x):  return "V"
        if z >= cc(c_4i, x):  return "I" if False else "IV"
        return "I"
    return ter, yt, yw, horizon


def bishop_FS(xc, yc, R, yt, yw, horizon, nsl=40):
    """FS de un circulo por Bishop simplificado. None si invalido."""
    # interseccion arco inferior con terreno: x donde yc - sqrt(R^2-(x-xc)^2) = yt(x)
    xs = np.linspace(xc - R, xc + R, 400)
    valid = (R**2 - (xs - xc)**2) > 0
    xs = xs[valid]
    base = yc - np.sqrt(R**2 - (xs - xc)**2)
    diff = yt(xs) - base                      # >0 donde el arco esta bajo el terreno
    sign = np.sign(diff)
    cross = np.where(np.diff(sign) > 0)[0]     # entradas (de - a +)
    crossb = np.where(np.diff(sign) < 0)[0]    # salidas
    if len(cross) == 0 or len(crossb) == 0:
        return None
    x1 = xs[cross[0]]; x2 = xs[crossb[-1]]
    if x2 - x1 < 5:
        return None
    xm = np.linspace(x1, x2, nsl + 1)
    xc_m = 0.5 * (xm[:-1] + xm[1:]); b = np.diff(xm)
    num = 0.0; den = 0.0
    for x, bw in zip(xc_m, b):
        if R**2 - (x - xc)**2 <= 0: return None
        zb = yc - np.sqrt(R**2 - (x - xc)**2)   # cota base
        zt = yt(x)
        if zt - zb <= 0.05: continue
        alpha = np.arctan2(x - xc, (yc - zb))    # inclinacion base
        # peso de la columna: integrar gamma (gsat bajo NF, gd encima)
        zlev = np.linspace(zb, zt, 12); dz = (zt - zb) / 11
        W = 0.0
        for z in 0.5 * (zlev[:-1] + zlev[1:]):
            h = horizon(x, z); g = HOR[h]["gsat"] if z < yw(x) else HOR[h]["gd"]
            W += g * dz * bw
        hb = horizon(x, zb + 0.1); c = HOR[hb]["c"]; phi = np.radians(HOR[hb]["phi"])
        u = max(0.0, GW * (yw(x) - zb))          # presion de poro en la base
        l = bw / np.cos(alpha)
        num_i = c * bw + (W - u * bw) * np.tan(phi)   # numerador (sin /m_alpha aun)
        num += (num_i, alpha, W); den += W * np.sin(alpha)
        # (se reescribe abajo con iteracion)
    return (xm, x1, x2)  # placeholder


def fs_circle(xc, yc, R, x1, x2, yt, yw, horizon, nsl=40):
    """Bishop simplificado para un circulo dado que aflora en x1 (cabecera) y x2 (pie)."""
    xm = np.linspace(x1, x2, nsl + 1); xcm = 0.5 * (xm[:-1] + xm[1:]); b = np.diff(xm)
    slices = []
    for x, bw in zip(xcm, b):
        disc = R**2 - (x - xc)**2
        if disc <= 0: return None
        zb = yc - np.sqrt(disc); zt = yt(x)
        if zt - zb <= 0.05: continue
        # alpha positivo cuando la base buza hacia el pie (sentido del deslizamiento, +x)
        alpha = np.arctan2(xc - x, yc - zb)
        zlev = np.linspace(zb, zt, 10); dz = (zt - zb) / 9; W = 0.0
        for z in 0.5 * (zlev[:-1] + zlev[1:]):
            h = horizon(x, z); g = HOR[h]["gsat"] if z < yw(x) else HOR[h]["gd"]
            W += g * dz * bw
        hb = horizon(x, zb + 0.1)
        slices.append((bw, alpha, W, HOR[hb]["c"], np.radians(HOR[hb]["phi"]),
                       max(0.0, GW * (yw(x) - zb))))
    if len(slices) < 5: return None
    den = sum(W * np.sin(al) for (_, al, W, _, _, _) in slices)
    if den <= 0: return None
    FS = 1.5
    for _ in range(80):
        num = 0.0
        for (bw, al, W, c, phi, u) in slices:
            ma = np.cos(al) + np.sin(al) * np.tan(phi) / FS
            if ma < 0.1: ma = 0.1
            num += (c * bw + (W - u * bw) * np.tan(phi)) / ma
        FSn = num / den
        if abs(FSn - FS) < 1e-4: FS = FSn; break
        FS = FSn
    if FS <= 0 or FS > 50: return None
    return FS


def circle_through(x1, z1, x2, z2, R):
    """Centro de un circulo de radio R que pasa por (x1,z1),(x2,z2), arriba de la cuerda."""
    mx, mz = 0.5 * (x1 + x2), 0.5 * (z1 + z2)
    L = np.hypot(x2 - x1, z2 - z1)
    if R < L / 2 * 1.001: return None
    h = np.sqrt(R**2 - (L / 2)**2)
    # perpendicular a la cuerda, apuntando hacia arriba (centro sobre el talud)
    dx, dz = (x2 - x1) / L, (z2 - z1) / L
    px, pz = -dz, dx
    if pz < 0: px, pz = -px, -pz   # que apunte hacia +z (arriba)
    return mx + h * px, mz + h * pz


def main():
    ter, yt, yw, horizon = make_funcs()
    xmin, xmax = ter[:, 0].min(), ter[:, 0].max()
    best = None; ntried = 0
    X1 = np.linspace(xmin + 5, xmax * 0.6, 30)      # cabecera (parte alta)
    for x1 in X1:
        z1 = float(yt(x1))
        X2 = np.linspace(x1 + 25, xmax - 2, 26)     # pie (mas abajo/derecha)
        for x2 in X2:
            z2 = float(yt(x2))
            L = np.hypot(x2 - x1, z2 - z1)
            for R in np.linspace(L / 2 * 1.05, L * 2.5, 22):
                c = circle_through(x1, z1, x2, z2, R)
                if c is None: continue
                xc, yc = c
                fs = fs_circle(xc, yc, R, x1, x2, yt, yw, horizon)
                ntried += 1
                if fs is not None and (best is None or fs < best[0]):
                    best = (fs, xc, yc, R, x1, x2)
    if best is None:
        print("sin circulo valido (probados %d)" % ntried); return
    FS, xc, yc, R, x1, x2 = best
    print("Circulos validos probados: %d" % ntried)
    print("FS MINIMO = %.3f  centro=(%.1f,%.1f) R=%.1f  afloramiento x=[%.1f,%.1f]" % (FS, xc, yc, R, x1, x2))
    json.dump(dict(FS=FS, xc=xc, yc=yc, R=R, x_in=x1, x_out=x2),
              open(os.path.join(ROOT, "reports", "bishop_FS.json"), "w"), indent=2)
    plot(ter, yt, yw, horizon, best)


def bishop_iter(xc, yc, R, yt, yw, horizon, nsl=40):
    """Bishop simplificado con iteracion de FS. Devuelve (FS, x1, x2) o None."""
    xs = np.linspace(xc - R, xc + R, 500)
    valid = (R**2 - (xs - xc)**2) > 1e-6
    xs = xs[valid]
    if len(xs) < 10: return None
    base = yc - np.sqrt(R**2 - (xs - xc)**2)
    diff = yt(xs) - base
    s = np.sign(diff)
    ent = np.where(np.diff(s) > 0)[0]; sal = np.where(np.diff(s) < 0)[0]
    if len(ent) == 0 or len(sal) == 0: return None
    x1 = xs[ent[0]]; x2 = xs[sal[-1]]
    if x2 - x1 < 8: return None
    xm = np.linspace(x1, x2, nsl + 1); xcm = 0.5 * (xm[:-1] + xm[1:]); b = np.diff(xm)
    slices = []
    for x, bw in zip(xcm, b):
        if R**2 - (x - xc)**2 <= 0: return None
        zb = yc - np.sqrt(R**2 - (x - xc)**2); zt = yt(x)
        if zt - zb <= 0.05: continue
        alpha = np.arctan2(x - xc, yc - zb)
        zlev = np.linspace(zb, zt, 10); dz = (zt - zb) / 9; W = 0.0
        for z in 0.5 * (zlev[:-1] + zlev[1:]):
            h = horizon(x, z); g = HOR[h]["gsat"] if z < yw(x) else HOR[h]["gd"]
            W += g * dz * bw
        hb = horizon(x, zb + 0.1)
        slices.append((bw, alpha, W, HOR[hb]["c"], np.radians(HOR[hb]["phi"]),
                       max(0.0, GW * (yw(x) - zb))))
    if not slices: return None
    den = sum(W * np.sin(al) for (_, al, W, _, _, _) in slices)
    if den <= 0: return None
    FS = 1.5
    for _ in range(60):
        num = 0.0
        for (bw, al, W, c, phi, u) in slices:
            ma = np.cos(al) + np.sin(al) * np.tan(phi) / FS
            if ma <= 0.1: ma = 0.1
            num += (c * bw + (W - u * bw) * np.tan(phi)) / ma
        FSn = num / den
        if abs(FSn - FS) < 1e-4: FS = FSn; break
        FS = FSn
    if FS <= 0 or FS > 20: return None
    return (FS, x1, x2)


def plot(ter, yt, yw, horizon, best):
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    FS, xc, yc, R, x1, x2 = best
    fig, ax = plt.subplots(figsize=(11, 5), dpi=120)
    xx = np.linspace(ter[:, 0].min(), ter[:, 0].max(), 400)
    ax.plot(xx, yt(xx), "k-", lw=1.5, label="Terreno")
    ax.plot(xx, yw(xx), "b--", lw=1.0, label="NF critico")
    # superficie de falla critica
    xa = np.linspace(x1, x2, 200); za = yc - np.sqrt(np.maximum(R**2 - (xa - xc)**2, 0))
    ax.plot(xa, za, "r-", lw=2.5, label=f"Superficie critica  FS={FS:.2f}")
    ax.plot([xc], [yc], "r+", ms=12)
    ax.fill_between(xa, za, yt(xa), color="orange", alpha=0.25)
    ax.set_aspect("equal"); ax.legend(loc="lower left")
    ax.set_xlabel("distancia s [m]"); ax.set_ylabel("cota z [m s.n.m.]")
    ax.set_title("Seccion A-A — Bishop simplificado (NF critico): FS = %.2f" % FS)
    ax.grid(alpha=0.3); fig.tight_layout()
    fig.savefig(os.path.join(ROOT, "reports", "BISHOP_superficie_critica.png"))
    print("figura OK")


if __name__ == "__main__":
    main()
