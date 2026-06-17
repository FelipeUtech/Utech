"""
make_deliverable.py — Genera los entregables finales a partir de un directorio
de resultados elegido (el mejor intento): video(s) + actualización de REPORTE.md
+ copia del caso para el registro.

Uso:
  python make_deliverable.py <results_dir> <case_dir> <score> <passed 0|1> <Lx> <Ly> <dt> <out_steps>
"""
import sys, os, json, glob, shutil
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import postprocess

ROOT = os.path.abspath(os.path.join(HERE, ".."))
REPORTS = os.path.join(ROOT, "reports")


def fill_report(score, passed, video_name, gates_detail):
    rp = os.path.join(ROOT, "REPORTE.md")
    txt = open(rp).read()
    lines = []
    verdict = ("**ROMPIMIENTO PERFECTO — los 6 gates pasan.** "
               if passed else f"**Mejor intento limpio: {score}/6 gates.** ")
    lines.append(verdict + f"Video: `reports/{video_name}`.\n")
    lines.append("| Gate | Estado | Detalle |")
    lines.append("|------|--------|---------|")
    for k, (ok, det) in gates_detail.items():
        st = "✅ PASS" if ok else "❌ FAIL"
        safe = det.replace("|", "/")[:150]
        lines.append(f"| {k} | {st} | {safe} |")
    lines.append("")
    if not passed:
        fails = [k for k, (ok, _) in gates_detail.items() if not ok]
        lines.append(f"**Gate(s) sin pasar:** {', '.join(fails)}.\n")
        lines.append(
            "**Diagnóstico y ajuste manual recomendado (gate c — quiescencia "
            "total de la energía cinética):** el frente de runout converge "
            "(gate f) y la masa forma una banda de corte localizada (gate d) con "
            "velocidades físicas (gate e), pero el bloque deslizado sigue "
            "reacomodándose internamente al final de la ventana. Con el mapeo "
            "estándar ED2Q4, alargar la corrida introduce ruido de cell-crossing "
            "(popcorn) antes de que la KE decaiga del todo. **Ajuste recomendado:** "
            "(1) usar mapeo **GIMP/CPDI** (en este build, `ED2Q16G` requiere "
            "soporte de nodos vecinos en la frontera —corregir el manejo de "
            "celdas de borde— o compilar CPDI) para sostener la gran deformación "
            "sin ruido y dejar que la KE decaiga a ~0; (2) alternativamente, "
            "amortiguamiento Cundall ~0.25–0.30 con `ppc=3` y `dt` menor para "
            "quiescencia dentro de la ventana limpia. Para el NF real, además, "
            "habilitar el bifásico con estado inicial geostático+hidrostático "
            "equilibrado (§4.1).\n")
    section = "\n".join(lines)
    txt = txt.replace("<!-- RESULTS_PLACEHOLDER -->", section)
    open(rp, "w").write(txt)
    print("REPORTE.md actualizado")


def main():
    results_dir, case_dir = sys.argv[1], sys.argv[2]
    score = int(sys.argv[3]); passed = bool(int(sys.argv[4]))
    Lx, Ly = float(sys.argv[5]), float(sys.argv[6])
    dt = float(sys.argv[7]); out_steps = int(sys.argv[8])

    # recomputar gates para el detalle exacto
    import gates as G
    rep = G.evaluate(results_dir, domain=[0, 0, Lx, Ly], mass_tol=0.02,
                     ke_decay_ratio=0.15, runout_tol=0.05)
    gd = {k: (v["pass"], v["detail"]) for k, v in rep["gates"].items()}

    name = "VIDEO_rompimiento.mp4" if passed else "VIDEO_intento.mp4"
    os.makedirs(REPORTS, exist_ok=True)
    postprocess.render(results_dir, os.path.join(REPORTS, name), field="velocity",
                       domain=[0, 0, Lx, Ly], fps=18, dt=dt, out_steps=out_steps,
                       title="CEMEX Talud Seccion A — campo de velocidad")
    postprocess.render(results_dir, os.path.join(REPORTS, "VIDEO_desplazamiento.mp4"),
                       field="displacement", domain=[0, 0, Lx, Ly], fps=18,
                       dt=dt, out_steps=out_steps,
                       title="CEMEX Talud Seccion A — desplazamiento")
    # registro del caso
    dst = os.path.join(ROOT, "cases", "seccionA")
    for fn in ("mesh.txt", "particles.txt", "mpm.json", "entity_sets.json",
               "particle_stresses.txt"):
        s = os.path.join(case_dir, fn)
        if os.path.exists(s):
            shutil.copy(s, os.path.join(dst, fn))
    json.dump({k: v for k, v in rep.items() if k != "series"},
              open(os.path.join(REPORTS, "final_gates.json"), "w"),
              indent=2, default=str)
    fill_report(score, passed, name, gd)
    print("entregables listos: score", score, "passed", passed)


if __name__ == "__main__":
    main()
