"""
fs_vs_nf.py — Curva Factor de Seguridad vs nivel freatico (Seccion A-A real).
Barre la posicion del NF (offset vertical respecto al NF critico del DXF) y
calcula el FS de Bishop minimo en cada caso. Util para disenar el drenaje.
"""
import sys, os, json
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import bishop_lem as B

def search(yt, yw, horizon, xmax):
    best = None
    for x1 in np.linspace(40, 105, 24):
        z1 = float(yt(x1))
        for x2 in np.linspace(x1 + 25, xmax - 5, 20):
            z2 = float(yt(x2)); L = np.hypot(x2 - x1, z2 - z1)
            for R in np.linspace(L / 2 * 1.05, L * 2.2, 14):
                c = B.circle_through(x1, z1, x2, z2, R)
                if not c: continue
                xc, yc = c
                fs = B.fs_circle(xc, yc, R, x1, x2, yt, yw, horizon)
                if fs is not None and (best is None or fs < best):
                    best = fs
    return best


def main():
    ter, yt, yw_crit, horizon = B.make_funcs()
    xmax = ter[:, 0].max()
    xs = np.linspace(ter[:, 0].min(), xmax, 200)
    # offsets verticales del NF respecto al critico: - (mas profundo) a + (mas alto)
    offsets = [-12, -9, -6, -4, -2, 0, 2, 4]
    rows = []
    open("/tmp/fsnf.log", "w").write("FS vs NF\n")
    for dz in offsets:
        yw = lambda x, dz=dz: np.minimum(yw_crit(x) + dz, yt(x) - 0.2)
        depth = float(np.mean(yt(xs) - yw(xs)))    # profundidad media del NF
        fs = search(yt, yw, horizon, xmax)
        rows.append(dict(offset=dz, mean_depth=depth, FS=fs))
        open("/tmp/fsnf.log", "a").write("offset=%+d m  prof_media=%.1f m  FS=%.3f\n" % (dz, depth, fs))
    json.dump(rows, open(os.path.join(B.ROOT, "reports", "fs_vs_nf.json"), "w"), indent=2)
    # plot
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    dep = [r["mean_depth"] for r in rows]; fss = [r["FS"] for r in rows]
    fig, ax = plt.subplots(figsize=(8, 5), dpi=120)
    ax.plot(dep, fss, "o-", color="#2a6f97", lw=2)
    ax.axhline(1.0, color="crimson", ls="--", lw=1, label="FS = 1 (falla)")
    ax.axhline(1.5, color="green", ls=":", lw=1, label="FS = 1.5 (objetivo tipico)")
    # marcar critico (offset 0)
    crit = next(r for r in rows if r["offset"] == 0)
    ax.plot([crit["mean_depth"]], [crit["FS"]], "rs", ms=10, label="NF critico (DXF)")
    ax.set_xlabel("Profundidad media del NF bajo el terreno [m]  (→ mas drenado)")
    ax.set_ylabel("Factor de Seguridad (Bishop)")
    ax.set_title("Seccion A-A — FS vs nivel freatico (diseno de drenaje)")
    ax.legend(); ax.grid(alpha=0.3); ax.invert_xaxis()  # izq=NF alto, der=drenado
    fig.tight_layout()
    fig.savefig(os.path.join(B.ROOT, "reports", "FS_vs_NF.png"))
    open("/tmp/fsnf.log", "a").write("PLOT OK\nDONE\n")


if __name__ == "__main__":
    main()
