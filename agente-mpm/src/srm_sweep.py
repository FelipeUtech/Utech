"""
srm_sweep.py — Strength Reduction Method (SRM) para la Seccion A-A real.
Reduce c' y tan(phi') por un factor SRF creciente; mide la movilidad del talud
(desplazamiento maximo y velocidad final). El FS es el SRF donde el
desplazamiento se dispara (transicion estable->falla).

Malla gruesa (rapidez): la deteccion estable/falla es un comportamiento global.
"""
import sys, os, glob, json, subprocess, time
import numpy as np, h5py
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import run_strata as R

R.H = 4.0; R.PPC = 2; R.APRON = 6.0; R.UPSTREAM = 0.0
R.DT = 6.0e-4; R.NSTEPS = 7000; R.FLOW = False; R.DAMP = 0.05
CASE = R.CASE

def mobility(srf):
    poly, Lx, Ly, nf, cl = R.geometry()
    R.build(CASE, poly, Lx, Ly, nf, cl, srf)
    r = subprocess.run([R.MPM, "-f", CASE + "/", "-i", "mpm.json", "-p", "4"],
                       capture_output=True, text=True)
    fs = sorted(glob.glob(CASE + "/results/**/*.h5", recursive=True),
                key=lambda f: int("".join(c for c in os.path.basename(f) if c.isdigit())))
    if r.returncode != 0 and len(fs) < 5:
        return dict(srf=srf, crash=True, dmax=float("nan"), vfin=float("nan"))
    # solo manto (no bedrock) y excluir franja de borde
    def load(f):
        d = h5py.File(f, "r")["table"][:]
        m = (d["material_id"] < 3) & (d["coord_x"] > 6)
        dxy = np.sqrt(d["displacement_x"]**2 + d["displacement_y"]**2)
        sp = np.sqrt(d["velocity_x"]**2 + d["velocity_y"]**2)
        return float(dxy[m].max()), float(np.percentile(sp[m], 99))
    dmax, _ = load(fs[-1])
    # velocidad final media de los ultimos frames (sostenida=falla, ~0=estable)
    vfin = np.mean([load(f)[1] for f in fs[-3:]])
    # crecimiento: despl ultimo vs mitad (si crece mucho => fluyendo)
    dmid, _ = load(fs[len(fs)//2])
    growth = dmax - dmid
    return dict(srf=srf, crash=bool(r.returncode != 0), dmax=dmax,
                vfin=float(vfin), growth=float(growth))


def main():
    srfs = [2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 6.0]
    out = []
    open("/tmp/srm.log", "w").write("SRM sweep\n")
    for s in srfs:
        t = time.time(); m = mobility(s); m["t"] = round(time.time() - t)
        out.append(m)
        open("/tmp/srm.log", "a").write(
            f"SRF={s}: dmax={m['dmax']:.2f}m vfin={m['vfin']:.3f} growth={m.get('growth',0):.2f} "
            f"crash={m['crash']} ({m['t']}s)\n")
        json.dump(out, open(os.path.join(R.ROOT, "reports", "srm_sweep.json"), "w"), indent=2)
    # FS: SRF donde dmax cruza un umbral de movilizacion (p.ej. 1.0 m) interpolado
    THR = 1.0
    fs_val = None
    for i in range(1, len(out)):
        a, b = out[i-1], out[i]
        if not (np.isnan(a["dmax"]) or np.isnan(b["dmax"])):
            if a["dmax"] < THR <= b["dmax"]:
                fs_val = a["srf"] + (THR - a["dmax"]) / (b["dmax"] - a["dmax"]) * (b["srf"] - a["srf"])
                break
    open("/tmp/srm.log", "a").write(f"FS estimado ~ {fs_val}\n" if fs_val else "FS fuera de rango\n")
    # plot
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    ss = [o["srf"] for o in out]; dd = [o["dmax"] for o in out]
    fig, ax = plt.subplots(figsize=(7, 4.5), dpi=120)
    ax.plot(ss, dd, "o-", color="#d4843a", lw=2)
    if fs_val: ax.axvline(fs_val, color="crimson", ls="--", label=f"FS ≈ {fs_val:.2f}")
    ax.axhline(THR, color="grey", ls=":", lw=0.8)
    ax.set_xlabel("Factor de reduccion de resistencia (SRF)")
    ax.set_ylabel("Desplazamiento maximo del manto [m]")
    ax.set_title("SRM — Seccion A-A real (NF critico): desplazamiento vs SRF")
    ax.legend(); ax.grid(alpha=0.3); fig.tight_layout()
    fig.savefig(os.path.join(R.ROOT, "reports", "SRM_factor_seguridad.png"))
    open("/tmp/srm.log", "a").write("PLOT OK\nDONE\n")


if __name__ == "__main__":
    main()
