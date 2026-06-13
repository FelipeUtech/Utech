"""
gates.py — Verificación física CUANTITATIVA desde el HDF5 de cb-geo MPM.

"Rompimiento perfecto" = TODOS los gates pasan:
  a. Corre completo, sin NaN.
  b. Masa conservada (±tol).
  c. Energía cinética: sube y decae a ~0; NO diverge.
  d. Superficie de falla localizada (banda de corte): la deformación plástica
     desviadora (pdstrain = svars_6) se concentra en una banda, no difusa ni
     cuerpo rígido.
  e. Material permanece en el dominio; sin popcorn/cell-crossing (oscilación
     espuria de velocidad).
  f. Runout converge: la distancia se estabiliza en los últimos frames.

Uso:
  python gates.py <results_dir> [--domain x0 y0 x1 y1] [--toe X] [--json out.json]
"""
import sys
import os
import glob
import json
import argparse
import numpy as np
import h5py

PDSTRAIN = "svars_6"  # plastic deviatoric strain en MohrCoulomb (orden de state_variables)
G = 9.81


def load_frames(results_dir):
    files = sorted(glob.glob(os.path.join(results_dir, "**", "particles*.h5"),
                              recursive=True))
    # ordenar por número de paso embebido
    def step(f):
        b = os.path.basename(f)
        d = "".join(ch for ch in b if ch.isdigit())
        return int(d) if d else 0
    files = sorted(files, key=step)
    frames = []
    for f in files:
        with h5py.File(f, "r") as h:
            frames.append(np.array(h["table"][:]))
    return files, frames


def frame_metrics(d):
    m = d["mass"].astype(float)
    vx = d["velocity_x"].astype(float)
    vy = d["velocity_y"].astype(float)
    x = d["coord_x"].astype(float)
    y = d["coord_y"].astype(float)
    speed2 = vx * vx + vy * vy
    ke = 0.5 * np.sum(m * speed2)
    pd = d[PDSTRAIN].astype(float) if PDSTRAIN in d.dtype.names else np.zeros_like(m)
    return {
        "mass": float(np.sum(m)),
        "ke": float(ke),
        "xmax": float(np.max(x)),
        "xmin": float(np.min(x)),
        "ymax": float(np.max(y)),
        "ymin": float(np.min(y)),
        "vmax": float(np.sqrt(np.max(speed2))) if len(speed2) else 0.0,
        "vmed": float(np.median(np.sqrt(speed2))) if len(speed2) else 0.0,
        "pd": pd,
        "x": x, "y": y,
        "nan": bool(np.any(~np.isfinite(x)) or np.any(~np.isfinite(y))
                    or np.any(~np.isfinite(vx)) or np.any(~np.isfinite(vy))),
    }


def evaluate(results_dir, domain=None, toe=None, mass_tol=0.01,
             ke_decay_ratio=0.10, runout_tol=0.02):
    files, frames = load_frames(results_dir)
    report = {"results_dir": results_dir, "n_frames": len(frames), "gates": {}, "series": {}}
    if len(frames) < 3:
        report["fatal"] = f"insuficientes frames ({len(frames)})"
        report["passed"] = False
        return report

    M = [frame_metrics(d) for d in frames]
    mass = np.array([f["mass"] for f in M])
    ke = np.array([f["ke"] for f in M])
    xmax = np.array([f["xmax"] for f in M])
    vmax = np.array([f["vmax"] for f in M])
    vmed = np.array([f["vmed"] for f in M])
    report["series"] = {
        "mass": mass.tolist(), "ke": ke.tolist(),
        "xmax": xmax.tolist(), "vmax": vmax.tolist(),
    }

    # --- Gate a: completa, sin NaN ---
    any_nan = any(f["nan"] for f in M) or bool(np.any(~np.isfinite(ke)))
    report["gates"]["a_no_nan"] = {
        "pass": (not any_nan),
        "detail": f"NaN detectado={any_nan}",
    }

    # --- Gate b: masa conservada ---
    m0 = mass[0]
    rel_mass = float(np.max(np.abs(mass - m0)) / (m0 + 1e-30))
    report["gates"]["b_mass"] = {
        "pass": rel_mass <= mass_tol,
        "detail": f"desviacion relativa masa={rel_mass:.2e} (tol {mass_tol})",
        "value": rel_mass,
    }

    # --- Gate c: KE sube y decae, no diverge ---
    ke_peak = float(np.max(ke))
    ipeak = int(np.argmax(ke))
    ke_final = float(np.mean(ke[-3:]))
    ke_init = float(ke[0])
    rose = ke_peak > max(ke_init, 1e-12) * 1.5  # se movilizó
    decayed = (ke_final <= ke_decay_ratio * ke_peak) if ke_peak > 0 else False
    not_diverge = np.all(np.isfinite(ke)) and (ke[-1] <= ke_peak * 1.05)
    report["gates"]["c_kinetic_energy"] = {
        "pass": bool(rose and decayed and not_diverge),
        "detail": (f"KE0={ke_init:.3e} peak={ke_peak:.3e}@{ipeak} "
                   f"final={ke_final:.3e} (final/peak={ke_final/(ke_peak+1e-30):.3f}); "
                   f"rose={rose} decayed={decayed} not_diverge={not_diverge}"),
        "ke_peak": ke_peak, "ke_final": ke_final, "ipeak": ipeak,
    }

    # --- Gate d: banda de corte localizada ---
    pd_final = M[-1]["pd"]
    pd_max = float(np.max(pd_final)) if len(pd_final) else 0.0
    if pd_max > 1e-8:
        thr = 0.2 * pd_max
        frac_band = float(np.mean(pd_final > thr))   # fraccion en la banda
        # indice de localizacion: Gini de pdstrain (1=muy localizado, 0=uniforme)
        s = np.sort(pd_final)
        n = len(s)
        cum = np.cumsum(s)
        gini = float((n + 1 - 2 * np.sum(cum) / cum[-1]) / n) if cum[-1] > 0 else 0.0
        localized = (pd_max > 1e-4) and (0.005 < frac_band < 0.5) and (gini > 0.45)
    else:
        frac_band, gini, localized = 0.0, 0.0, False
    report["gates"]["d_shear_band"] = {
        "pass": bool(localized),
        "detail": (f"pdstrain_max={pd_max:.3e} frac_en_banda={frac_band:.3f} "
                   f"gini={gini:.3f}; localizada={localized} "
                   f"(no difusa ni cuerpo rigido)"),
        "pd_max": pd_max, "frac_band": frac_band, "gini": gini,
    }

    # --- Gate e: material en dominio + sin popcorn ---
    in_domain = True
    dom_detail = "sin dominio especificado"
    if domain is not None:
        x0, y0, x1, y1 = domain
        out = 0
        for f in M:
            out += int(np.sum((f["x"] < x0 - 1e-6) | (f["x"] > x1 + 1e-6) |
                              (f["y"] < y0 - 1e-6) | (f["y"] > y1 + 1e-6)))
        in_domain = (out == 0)
        dom_detail = f"particulas fuera de dominio={out}"
    # popcorn: pico de velocidad muy por encima de la mediana en cualquier frame
    ratio = vmax / (vmed + 1e-12)
    # umbral fisico de velocidad ~ sqrt(2 g H)
    H = (domain[3] - domain[1]) if domain is not None else (np.max(xmax) - np.min(xmax))
    v_phys = np.sqrt(2 * G * max(H, 1.0))
    popcorn = bool(np.any(vmax > 5.0 * v_phys))
    report["gates"]["e_domain_no_popcorn"] = {
        "pass": bool(in_domain and not popcorn),
        "detail": (f"{dom_detail}; vmax_global={float(np.max(vmax)):.3f} "
                   f"v_fisica~{v_phys:.2f} popcorn={popcorn}"),
        "popcorn": popcorn, "in_domain": in_domain,
    }

    # --- Gate f: runout converge ---
    # runout = avance del frente respecto a la posicion inicial
    runout = xmax - xmax[0]
    tail = runout[-5:] if len(runout) >= 5 else runout
    span = float(np.max(tail) - np.min(tail))
    final_runout = float(runout[-1])
    rel_change = span / (abs(final_runout) + 1e-6)
    converged = (rel_change <= runout_tol) or (span < 0.01)
    report["gates"]["f_runout_converge"] = {
        "pass": bool(converged),
        "detail": (f"runout_final={final_runout:.3f} m, "
                   f"variacion_ultimos_frames={span:.4f} m "
                   f"(rel={rel_change:.3f}, tol {runout_tol}); converge={converged}"),
        "runout": final_runout, "span": span,
    }

    passed = all(g["pass"] for g in report["gates"].values())
    report["passed"] = bool(passed)
    score = sum(1 for g in report["gates"].values() if g["pass"])
    report["score"] = score
    report["score_max"] = len(report["gates"])
    return report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("results_dir")
    ap.add_argument("--domain", nargs=4, type=float, default=None)
    ap.add_argument("--toe", type=float, default=None)
    ap.add_argument("--json", default=None)
    a = ap.parse_args()
    rep = evaluate(a.results_dir, domain=a.domain, toe=a.toe)
    print(f"\n=== GATES [{a.results_dir}] frames={rep['n_frames']} ===")
    if "fatal" in rep:
        print("FATAL:", rep["fatal"])
    for k, g in rep.get("gates", {}).items():
        print(f"  [{'PASS' if g['pass'] else 'FAIL'}] {k}: {g['detail']}")
    print(f"  SCORE {rep.get('score','?')}/{rep.get('score_max','?')}  "
          f"=> {'ROMPIMIENTO PERFECTO' if rep.get('passed') else 'incompleto'}")
    if a.json:
        # quitar arrays grandes
        with open(a.json, "w") as f:
            json.dump({k: v for k, v in rep.items() if k != "series" or True},
                      f, indent=2, default=str)
    return 0 if rep.get("passed") else 1


if __name__ == "__main__":
    sys.exit(main())
