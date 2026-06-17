"""
run_calibration.py — Caso canónico: colapso de columna granular SECO.
NO es entregable. Confirma que el motor MPM y la cadena run->HDF5->gates->video
están sanos antes de creerle a la verificación del talud.

Columna: a=0.2 m ancho x H=0.4 m alto (aspect ratio 2) sobre base plana
friccional; dominio extendido a la derecha para runout. Mohr-Coulomb seco.
"""
import os
import sys
import shutil
import subprocess
import json

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import make_case
import meshgen as mg
import gates as gatesmod
import postprocess

MPM_BIN = "/home/user/mpm-build/build/mpm"  # binario 1-fase
ROOT = os.path.abspath(os.path.join(HERE, "..", "calibration"))


def main():
    case_dir = os.path.join(ROOT, "column_collapse")
    if os.path.exists(os.path.join(case_dir, "results")):
        shutil.rmtree(os.path.join(case_dir, "results"))

    Lx, Ly, h = 2.0, 0.5, 0.02
    a, H = 0.20, 0.40
    cfg = {
        "title": "Columna granular seca (calibracion)",
        "grid": {"Lx": Lx, "Ly": Ly, "h": h},
        "region_fn": mg.region_column(a, H),
        "ppc": 2,
        "twophase": False,
        "material_id": 0,
        "materials": [{
            "id": 0, "type": "MohrCoulomb2D",
            "density": 1800.0,
            "youngs_modulus": 1.0e6, "poisson_ratio": 0.3,
            "friction": 30.0, "dilation": 0.0, "cohesion": 100.0,
            "residual_friction": 30.0, "residual_dilation": 0.0,
            "residual_cohesion": 100.0,
            "peak_pdstrain": 0.0, "residual_pdstrain": 0.0,
            "tension_cutoff": 50.0, "softening": False,
        }],
        "gravity": [0.0, -9.81],
        "velocity_constraints": [
            {"nset_id": 0, "dir": 0, "velocity": 0.0},  # base fija x
            {"nset_id": 0, "dir": 1, "velocity": 0.0},  # base fija y
            {"nset_id": 1, "dir": 0, "velocity": 0.0},  # izq roller x
            {"nset_id": 2, "dir": 0, "velocity": 0.0},  # der roller x
        ],
        "dt": 1.0e-4, "nsteps": 18000, "output_steps": 180,
        "damping": 0.10, "uuid": "column_collapse",
        "stress_update": "usf",
    }
    nn, nc, npart = make_case.build(case_dir, cfg)
    print(f"[calib] malla {nn} nodos {nc} celdas, {npart} particulas")

    print("[calib] corriendo MPM...")
    r = subprocess.run([MPM_BIN, "-f", case_dir + "/", "-i", "mpm.json", "-p", "4"],
                       capture_output=True, text=True)
    tail = "\n".join(r.stdout.splitlines()[-3:])
    print("[calib] mpm rc=", r.returncode, tail)
    if r.returncode != 0:
        print(r.stderr[-1500:])
        return 2

    res = os.path.join(case_dir, "results")
    rep = gatesmod.evaluate(res, domain=[0, 0, Lx, Ly],
                            mass_tol=0.01, ke_decay_ratio=0.15, runout_tol=0.05)
    print(f"\n=== GATES CALIBRACION  frames={rep['n_frames']} ===")
    for k, gg in rep.get("gates", {}).items():
        print(f"  [{'PASS' if gg['pass'] else 'FAIL'}] {k}: {gg['detail']}")
    print(f"  SCORE {rep.get('score')}/{rep.get('score_max')}")
    with open(os.path.join(case_dir, "gates.json"), "w") as f:
        json.dump({k: v for k, v in rep.items() if k != "series"}, f,
                  indent=2, default=str)

    try:
        out = os.path.join(ROOT, "VIDEO_calibracion.mp4")
        postprocess.render(res, out, field="velocity",
                           domain=[0, 0, Lx, Ly], fps=15,
                           dt=cfg["dt"], out_steps=cfg["output_steps"],
                           title="Calibracion: colapso columna granular")
    except Exception as e:
        print("[calib] video fallo:", e)
    return 0


if __name__ == "__main__":
    sys.exit(main())
