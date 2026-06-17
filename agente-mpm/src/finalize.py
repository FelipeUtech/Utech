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


def write_results_section(best, video_name):
    hist_path = os.path.join(REPORTS, "loop_history.json")
    hist = json.load(open(hist_path)) if os.path.exists(hist_path) else []
    rep = best.get("rep", {})
    gates = rep.get("gates", {})
    passed = rep.get("passed", False)
    lines = []
    verdict = ("**ROMPIMIENTO PERFECTO — los 6 gates pasan.**" if passed
               else f"**Mejor intento: {best.get('score')}/6 gates** "
                    f"(iteración {best.get('iter')}).")
    lines.append(verdict + "\n")
    lines.append(f"- Iteraciones ejecutadas: **{len(hist)}**")
    lines.append(f"- Video: `reports/{video_name}`\n")
    if gates:
        lines.append("| Gate | Estado | Detalle |")
        lines.append("|------|--------|---------|")
        for k, g in gates.items():
            st = "✅ PASS" if g.get("pass") else "❌ FAIL"
            det = str(g.get("detail", "")).replace("|", "\\|")[:140]
            lines.append(f"| {k} | {st} | {det} |")
        lines.append("")
    if not passed:
        fails = [k for k, g in gates.items() if not g.get("pass")]
        lines.append(f"**Gate(s) sin pasar:** {', '.join(fails)}.")
        lines.append("**Ajuste manual recomendado:** aumentar amortiguamiento "
                     "Cundall y/o pasos de tiempo para que la masa depositada "
                     "alcance el reposo (KE→0, runout estable); de persistir, "
                     "afinar el ablandamiento (`residual_pdstrain`) para nitidez "
                     "de la banda. Para NF real, ver §4.1 (estado bifásico "
                     "equilibrado).\n")
    # trayectoria de scores
    if hist:
        traj = " → ".join(str(h.get("score", "x")) for h in hist)
        lines.append(f"**Trayectoria de score por iteración:** {traj}\n")
        lines.append("**Bitácora de ajustes:**")
        for h in hist:
            if h.get("ajuste"):
                lines.append(f"- iter {h['iter']} (score {h.get('score')}): {h['ajuste']}")
    section = "\n".join(lines)
    rp = os.path.join(ROOT, "REPORTE.md")
    txt = open(rp).read()
    txt = txt.replace("<!-- RESULTS_PLACEHOLDER -->", section)
    open(rp, "w").write(txt)
    print("REPORTE.md actualizado")


if __name__ == "__main__":
    best, ck = best_checkpoint()
    print("best score", best.get("score"), "ckpt", ck)
    if ck:
        name, passed = make_video(best, ck)
        write_results_section(best, name)
        print("video:", name, "passed:", passed)
    else:
        print("sin checkpoint para video")
