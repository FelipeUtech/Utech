"""
finalize.py — Genera el VIDEO final + REPORTE.md a partir del mejor intento
del loop autónomo (reports/best.json + checkpoints/ + reports/loop_history.json).

VIDEO_rompimiento.mp4  si TODOS los gates pasaron (rompimiento perfecto)
VIDEO_intento.mp4      si se llegó al tope sin perfecto
"""
import os
import sys
import json
import glob
import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import postprocess

ROOT = os.path.abspath(os.path.join(HERE, ".."))
REPORTS = os.path.join(ROOT, "reports")


def best_checkpoint():
    best = json.load(open(os.path.join(REPORTS, "best.json")))
    ck = best.get("ckpt")
    if not ck or not os.path.isdir(ck):
        # fallback: el checkpoint de mayor score
        cks = sorted(glob.glob(os.path.join(ROOT, "checkpoints", "iter*")))
        ck = cks[-1] if cks else None
    return best, ck


def make_video(best, ck):
    passed = best.get("rep", {}).get("passed", False)
    name = "VIDEO_rompimiento.mp4" if passed else "VIDEO_intento.mp4"
    out = os.path.join(REPORTS, name)
    p = best.get("params", {})
    Lx = best.get("Lx"); Ly = best.get("Ly")
    postprocess.render(ck, out, field="velocity",
                       domain=[0, 0, Lx, Ly] if Lx else None, fps=18,
                       dt=p.get("dt"), out_steps=p.get("output_steps"),
                       title="CEMEX Talud Seccion A — campo de velocidad")
    # segundo video: desplazamiento
    out2 = os.path.join(REPORTS, "VIDEO_desplazamiento.mp4")
    postprocess.render(ck, out2, field="displacement",
                       domain=[0, 0, Lx, Ly] if Lx else None, fps=18,
                       dt=p.get("dt"), out_steps=p.get("output_steps"),
                       title="CEMEX Talud Seccion A — desplazamiento")
    return name, passed


if __name__ == "__main__":
    best, ck = best_checkpoint()
    print("best score", best.get("score"), "ckpt", ck)
    if ck:
        name, passed = make_video(best, ck)
        print("video:", name, "passed:", passed)
    else:
        print("sin checkpoint para video")
