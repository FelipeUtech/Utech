"""
postprocess.py — HDF5 (cb-geo MPM) -> secuencia PNG -> MP4 estilo CEL/Abaqus.

Colorea las partículas por magnitud de velocidad o por desplazamiento total,
estilo "Coupled Eulerian-Lagrangian" de Abaqus (campo continuo sobre el
material desplazándose). Genera frames con matplotlib y los une con ffmpeg.

Uso:
  python postprocess.py <results_dir> <out.mp4> [--field velocity|displacement]
                        [--domain x0 y0 x1 y1] [--fps 20] [--dt DT --out_steps N]
"""
import sys
import os
import glob
import argparse
import subprocess
import numpy as np
import h5py
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def load_files(results_dir):
    files = sorted(glob.glob(os.path.join(results_dir, "**", "particles*.h5"),
                             recursive=True))
    def step(f):
        d = "".join(ch for ch in os.path.basename(f) if ch.isdigit())
        return int(d) if d else 0
    return sorted(files, key=step)


def field_value(d, field):
    if field == "velocity":
        v = np.sqrt(d["velocity_x"].astype(float) ** 2 +
                    d["velocity_y"].astype(float) ** 2)
        label = "Velocidad |v| [m/s]"
    elif field == "displacement":
        v = np.sqrt(d["displacement_x"].astype(float) ** 2 +
                    d["displacement_y"].astype(float) ** 2)
        label = "Desplazamiento |u| [m]"
    elif field == "pdstrain":
        v = d["svars_6"].astype(float)
        label = "Def. plastica desviadora"
    else:
        raise ValueError(field)
    return v, label


def render(results_dir, out_mp4, field="velocity", domain=None, fps=20,
           dt=None, out_steps=None, title="CEMEX Talud Seccion A"):
    files = load_files(results_dir)
    if not files:
        raise SystemExit(f"sin frames en {results_dir}")
    tmp = os.path.join(os.path.dirname(out_mp4) or ".", "_frames")
    os.makedirs(tmp, exist_ok=True)
    for old in glob.glob(os.path.join(tmp, "*.png")):
        os.remove(old)

    # rango de color global (percentil robusto)
    allv = []
    for f in files[:: max(1, len(files) // 30)]:
        with h5py.File(f, "r") as h:
            allv.append(field_value(np.array(h["table"][:]), field)[0])
    vmax = float(np.percentile(np.concatenate(allv), 98)) if allv else 1.0
    vmax = max(vmax, 1e-6)

    if domain is None:
        with h5py.File(files[0], "r") as h:
            d0 = np.array(h["table"][:])
        domain = [float(d0["coord_x"].min()) - 1, float(d0["coord_y"].min()) - 1,
                  float(d0["coord_x"].max()) + 1, float(d0["coord_y"].max()) + 1]

    for k, f in enumerate(files):
        with h5py.File(f, "r") as h:
            d = np.array(h["table"][:])
        x = d["coord_x"].astype(float)
        y = d["coord_y"].astype(float)
        v, label = field_value(d, field)
        fig, ax = plt.subplots(figsize=(8, 4.5), dpi=110)
        ax.set_facecolor("#0b0b16")
        sc = ax.scatter(x, y, c=v, s=7, cmap="turbo", vmin=0, vmax=vmax,
                        edgecolors="none")
        ax.set_xlim(domain[0], domain[2])
        ax.set_ylim(domain[1], domain[3])
        ax.set_aspect("equal")
        cb = fig.colorbar(sc, ax=ax, fraction=0.035, pad=0.02)
        cb.set_label(label)
        t_txt = ""
        if dt is not None and out_steps is not None:
            t_txt = f"  t = {k * out_steps * dt:.3f} s"
        ax.set_title(f"{title}{t_txt}", fontsize=10)
        ax.set_xlabel("x [m]"); ax.set_ylabel("y [m]")
        fig.tight_layout()
        fig.savefig(os.path.join(tmp, f"f{k:05d}.png"))
        plt.close(fig)

    # ffmpeg
    cmd = ["ffmpeg", "-y", "-framerate", str(fps),
           "-i", os.path.join(tmp, "f%05d.png"),
           "-c:v", "libx264", "-pix_fmt", "yuv420p",
           "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2", out_mp4]
    subprocess.run(cmd, check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"video -> {out_mp4} ({len(files)} frames)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("results_dir")
    ap.add_argument("out_mp4")
    ap.add_argument("--field", default="velocity")
    ap.add_argument("--domain", nargs=4, type=float, default=None)
    ap.add_argument("--fps", type=int, default=20)
    ap.add_argument("--dt", type=float, default=None)
    ap.add_argument("--out_steps", type=int, default=None)
    ap.add_argument("--title", default="CEMEX Talud Seccion A")
    a = ap.parse_args()
    render(a.results_dir, a.out_mp4, a.field, a.domain, a.fps,
           a.dt, a.out_steps, a.title)
