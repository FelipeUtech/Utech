"""
slope_loop.py — LOOP PRINCIPAL autónomo para el talud CEMEX Seccion A.

MPM bifásico (MPMExplicitTwoPhase2D), solido Mohr-Coulomb saturado con
ablandamiento (strain-softening => banda de corte localizada), liquido
Newtonian, nivel freatico alto (NF alto). Gravedad + disparador por
reduccion de resistencia (ablandamiento).

Itera: CORRER -> VERIFICAR (gates) -> DIAGNOSTICAR -> AJUSTAR -> RELANZAR.
Topes: max 12 iters, reloj 06:00, sin-progreso 3 iters, checkpoint del mejor.

GEOMETRIA: parametrica (stand-in de la Seccion A; el DXF real no existe en el
entorno -- ver REPORTE.md). Sustituir meshgen.load_section_polygon() por los
vertices reales cuando se disponga del DXF.
"""
import os
import sys
import json
import time
import shutil
import subprocess
import copy
import datetime
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import make_case
import meshgen as mg
import gates as gatesmod

# --- Selección de motor ---------------------------------------------------
# El motor BIFÁSICO (mpm-dev, MPMExplicitTwoPhase2D) se compiló y se probó,
# pero explota hacia el paso ~20: la presión de poro hidrostática (~60 kPa en
# la base) se inicializa con tensión efectiva sólida = 0, dejando el sistema
# lejos del equilibrio => inestabilidad. Corregirlo exige un estado inicial
# geostático+hidrostático equilibrado (ver REPORTE.md, "Trabajo futuro").
# Para el loop autónomo de esta noche se modela "NF alto" con el enfoque
# ESTÁNDAR de TENSIÓN EFECTIVA en una sola fase: peso unitario sumergido
# (boyante) bajo el NF + resistencia efectiva reducida por la presión de poro.
TWOPHASE = False
MPM_BIN_2PH = "/home/user/mpm-dev/build/mpm"     # bifásico (no usado por defecto)
MPM_BIN_1PH = "/home/user/mpm-build/build/mpm"   # una fase (efectivo)
MPM_BIN = MPM_BIN_2PH if TWOPHASE else MPM_BIN_1PH
ROOT = os.path.abspath(os.path.join(HERE, ".."))
CASE_DIR = os.path.join(ROOT, "cases", "seccionA")
CKPT = os.path.join(ROOT, "checkpoints")
HIST = os.path.join(ROOT, "reports", "loop_history.json")

MAX_ITERS = 12
STOP_HOUR_UTC = 6          # detener nuevas corridas a las 06:00 UTC
NO_PROGRESS_LIMIT = 3

# ---- Geometria de la Seccion A ----
# Si DXF_PATH existe, se usa la geometria REAL (capa TERRENO) y el NF real
# (NAF_CRITICO); si no, se cae al stand-in parametrico GEOM.
DXF_PATH = "/home/user/Utech/#seccion_A-A.dxf"
PROFILE_LAYER = "TERRENO"
NF_LAYER = "NAF_CRITICO"
GEOM = dict(crest_h=6.0, slope_angle_deg=55.0, crest_len=4.0,
            toe_x=5.0, foundation_h=2.0)
# Escala real ~161 m ancho x 54 m relieve => malla gruesa para tractabilidad.
H_CELL = 2.0
RUNOUT_EXT = 35.0   # extension horizontal extra del dominio para runout
NF_Y = None         # cota del NF (marco trasladado), fijada por domain_from_geom


def domain_from_geom():
    global NF_Y
    if DXF_PATH and os.path.exists(DXF_PATH):
        import dxf_to_section as D
        poly, nf_y, meta = D.section_polygon_from_dxf(
            DXF_PATH, profile_layer=PROFILE_LAYER, nf_layer=NF_LAYER,
            base_margin=3.0, side_margin=2.0, runout_pad=RUNOUT_EXT)
        NF_Y = nf_y
    else:
        poly = mg.load_section_polygon(**GEOM)
        NF_Y = GEOM["foundation_h"] + 0.85 * GEOM["crest_h"]
    xs = [p[0] for p in poly]; ys = [p[1] for p in poly]
    Lx = max(xs) + RUNOUT_EXT
    Ly = max(ys) + 3.0
    return poly, Lx, Ly


def region_from_poly(poly):
    return lambda x, y: mg.point_in_poly(x, y, poly)


def base_params():
    """Parametros ajustables por el diagnostico.

    Modelo de TENSION EFECTIVA (NF alto, una fase):
      - density = peso unitario EFECTIVO (sumergido/boyante) ~ gamma_sat - gamma_w.
        gamma_sat ~ 20 kN/m3 (rho 2040), gamma_w ~ 10 kN/m3 => rho_eff ~ 1100.
        Con NF alto casi todo el talud queda bajo el NF => se usa rho efectivo.
      - cohesion/friction = parametros EFECTIVOS, ya reducidos por la presion de
        poro alta. El disparador es la reduccion de resistencia (ablandamiento
        peak->residual) una vez iniciada la fluencia.
    """
    return dict(
        # escala real (~54 m): E mayor; ppc=3 + dt menor controlan el
        # cell-crossing (popcorn) que ejecta particulas en la banda de corte.
        dt=1.0e-3, nsteps=12000, output_steps=120,
        damping=0.12, ppc=3,
        # solido Mohr-Coulomb (tension efectiva) con ablandamiento MODERADO:
        # pico => falla bajo NF alto; residual moderado => el slump se ARRESTA.
        density=1200.0, E=5.0e7, nu=0.30,
        friction_peak=24.0, friction_res=18.0,
        cohesion_peak=12000.0, cohesion_res=4000.0,
        tension_cutoff=5000.0,
        dilation=0.0,
        peak_pdstrain=0.01, residual_pdstrain=0.10,
        # (parametros bifasicos retenidos para reactivar TWOPHASE)
        porosity=0.40, k=1.0e-4,
        liq_density=1000.0, liq_bulk=2.0e6, liq_visc=1.0e-3,
        # NF alto: fraccion de la altura de cresta donde esta el nivel freatico
        wt_frac=0.85,
        runout_ext=RUNOUT_EXT,
    )


def make_cfg(p, poly, Lx, Ly):
    # NF: cota real del DXF (NAF_CRITICO) si esta disponible, si no parametrico
    wt_y = NF_Y if NF_Y is not None else (
        GEOM["foundation_h"] + p["wt_frac"] * GEOM["crest_h"])
    solid = {
        "id": 0, "type": "MohrCoulomb2D",
        "density": p["density"], "youngs_modulus": p["E"], "poisson_ratio": p["nu"],
        "friction": p["friction_peak"], "dilation": p["dilation"],
        "cohesion": p["cohesion_peak"],
        "residual_friction": p["friction_res"], "residual_dilation": p["dilation"],
        "residual_cohesion": p["cohesion_res"],
        "peak_pdstrain": p["peak_pdstrain"], "residual_pdstrain": p["residual_pdstrain"],
        "tension_cutoff": p["tension_cutoff"], "softening": True,
        "porosity": p["porosity"], "k_x": p["k"], "k_y": p["k"],
    }
    liquid = {
        "id": 1, "type": "Newtonian2D",
        "density": p["liq_density"], "bulk_modulus": p["liq_bulk"],
        "dynamic_viscosity": p["liq_visc"], "incompressible": False,
    }
    cfg = {
        "title": ("CEMEX Talud Seccion A - " +
                  ("bifasico saturado NF alto" if TWOPHASE
                   else "tension efectiva (NF alto: peso sumergido + resistencia reducida)")),
        "grid": {"Lx": Lx, "Ly": Ly, "h": H_CELL},
        "region_fn": region_from_poly(poly),
        "ppc": p["ppc"],
        "gravity": [0.0, -9.81],
        "velocity_constraints": [
            {"nset_id": 0, "dir": 0, "velocity": 0.0},
            {"nset_id": 0, "dir": 1, "velocity": 0.0},
            {"nset_id": 1, "dir": 0, "velocity": 0.0},
            {"nset_id": 2, "dir": 0, "velocity": 0.0},
        ],
        "dt": p["dt"], "nsteps": p["nsteps"], "output_steps": p["output_steps"],
        "damping": p["damping"], "uuid": "seccionA",
        "stress_update": "usf",
        "initial_stress_K0": True,
    }
    if TWOPHASE:
        cfg.update({"twophase": True, "material_id": [0, 1],
                    "materials": [solid, liquid],
                    "water_table": {"position": wt_y, "h0": 0.0},
                    "pore_pressure_smoothing": True})
    else:
        cfg.update({"twophase": False, "material_id": 0, "materials": [solid]})
    return cfg


def diagnose(rep, p, prev_runout):
    """Devuelve (nuevos_params, descripcion_ajuste). Cambio DIRIGIDO."""
    p = copy.deepcopy(p)
    g = rep.get("gates", {})
    notes = []

    def failed(name):
        return name in g and not g[name]["pass"]

    # 1. NaN / energia diverge -> bajar dt, subir damping
    if failed("a_no_nan") or (failed("c_kinetic_energy") and
                              "not_diverge=False" in g.get("c_kinetic_energy", {}).get("detail", "")):
        p["dt"] *= 0.5
        p["nsteps"] = int(p["nsteps"] * 1.5)
        p["output_steps"] = max(1, int(p["nsteps"] / 100))
        p["damping"] = min(0.25, p["damping"] + 0.05)
        notes.append(f"NaN/divergencia -> dt={p['dt']:.1e}, damping={p['damping']:.2f}")
        return p, "; ".join(notes)

    # 2. popcorn / cell-crossing -> mas ppc, mas damping, menor dt
    if failed("e_domain_no_popcorn") and g["e_domain_no_popcorn"].get("popcorn"):
        p["ppc"] = min(3, p["ppc"] + 1)
        p["damping"] = min(0.25, p["damping"] + 0.04)
        p["dt"] *= 0.7
        notes.append(f"popcorn -> ppc={p['ppc']}, damping={p['damping']:.2f}, dt={p['dt']:.1e}")
        return p, "; ".join(notes)

    # 4. material cruza frontera -> extender dominio
    if failed("e_domain_no_popcorn") and not g["e_domain_no_popcorn"].get("in_domain", True):
        p["runout_ext"] += 6.0
        notes.append(f"material fuera dominio -> runout_ext={p['runout_ext']:.0f}")
        return p, "; ".join(notes)

    # 3. talud no se mueve -> reforzar disparador (bajar resistencia, subir NF)
    moved = g.get("c_kinetic_energy", {}).get("ke_peak", 0) > 1e-2 and \
        g.get("f_runout_converge", {}).get("runout", 0) > 0.05
    if not moved:
        p["friction_res"] = max(8.0, p["friction_res"] - 4.0)
        p["cohesion_res"] = max(0.0, p["cohesion_res"] - 250.0)
        p["wt_frac"] = min(1.0, p["wt_frac"] + 0.05)
        notes.append(f"talud estatico -> fric_res={p['friction_res']:.0f}, "
                     f"coh_res={p['cohesion_res']:.0f}, NF={p['wt_frac']:.2f}")
        return p, "; ".join(notes)

    # 5. falla difusa -> localizar (ablandamiento mas abrupto)
    if failed("d_shear_band"):
        det = g["d_shear_band"]
        if det.get("frac_band", 0) >= 0.5:        # demasiado difusa
            p["residual_pdstrain"] = max(0.02, p["residual_pdstrain"] * 0.6)
            p["cohesion_res"] = max(0.0, p["cohesion_res"] - 200.0)
            notes.append(f"falla difusa -> res_pdstrain={p['residual_pdstrain']:.3f} "
                         "(ablandamiento mas abrupto)")
        else:                                      # casi nada de plastico
            p["friction_res"] = max(8.0, p["friction_res"] - 3.0)
            notes.append(f"poca plastificacion -> fric_res={p['friction_res']:.0f}")
        return p, "; ".join(notes)

    # 6. KE no decae -> mas damping / mas tiempo
    if failed("c_kinetic_energy"):
        p["damping"] = min(0.3, p["damping"] + 0.05)
        p["nsteps"] = int(p["nsteps"] * 1.4)
        p["output_steps"] = max(1, int(p["nsteps"] / 100))
        notes.append(f"KE no decae -> damping={p['damping']:.2f}, nsteps={p['nsteps']}")
        return p, "; ".join(notes)

    # 7. runout no converge -> mas tiempo
    if failed("f_runout_converge"):
        p["nsteps"] = int(p["nsteps"] * 1.4)
        p["output_steps"] = max(1, int(p["nsteps"] / 100))
        notes.append(f"runout no converge -> nsteps={p['nsteps']}")
        return p, "; ".join(notes)

    return p, "sin ajuste (todos los gates pasan)"


def run_once(p, it):
    poly, Lx, Ly = domain_from_geom()
    global RUNOUT_EXT
    cfg = make_cfg(p, poly, Lx, Ly)
    if os.path.exists(os.path.join(CASE_DIR, "results")):
        shutil.rmtree(os.path.join(CASE_DIR, "results"))
    nn, nc, npart = make_case.build(CASE_DIR, cfg)
    t0 = time.time()
    r = subprocess.run([MPM_BIN, "-f", CASE_DIR + "/", "-i", "mpm.json", "-p", "4"],
                       capture_output=True, text=True)
    dt_run = time.time() - t0
    ok = (r.returncode == 0)
    res = os.path.join(CASE_DIR, "results")
    if not ok or not os.path.isdir(res):
        return None, dict(mesh=(nn, nc, npart), rc=r.returncode,
                          stderr=r.stderr[-800:], run_s=dt_run, Lx=Lx, Ly=Ly)
    rep = gatesmod.evaluate(res, domain=[0, 0, Lx, Ly],
                            mass_tol=0.02, ke_decay_ratio=0.15, runout_tol=0.05)
    rep["_run_s"] = dt_run
    rep["_mesh"] = (nn, nc, npart)
    rep["_Lx"], rep["_Ly"] = Lx, Ly
    return rep, dict(mesh=(nn, nc, npart), rc=0, run_s=dt_run, Lx=Lx, Ly=Ly)


def checkpoint_best(it, score):
    dst = os.path.join(CKPT, f"iter{it:02d}_score{score}")
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(os.path.join(CASE_DIR, "results"), dst)
    return dst


def main():
    os.makedirs(CKPT, exist_ok=True)
    os.makedirs(os.path.dirname(HIST), exist_ok=True)
    global RUNOUT_EXT
    p = base_params()
    history = []
    best = {"score": -1, "iter": -1, "ckpt": None, "rep": None, "params": None}
    no_progress = 0

    for it in range(1, MAX_ITERS + 1):
        now = datetime.datetime.utcnow()
        if now.hour >= STOP_HOUR_UTC:
            print(f"[loop] reloj {now.time()} >= 06:00 UTC -> detener nuevas corridas")
            break
        RUNOUT_EXT = p["runout_ext"]
        print(f"\n===== ITER {it} =====")
        print("  params:", {k: p[k] for k in ("dt", "nsteps", "damping", "ppc",
              "friction_res", "cohesion_res", "wt_frac", "residual_pdstrain", "runout_ext")})
        rep, meta = run_once(p, it)
        if rep is None:
            print(f"  MPM FALLO rc={meta['rc']} run={meta['run_s']:.0f}s")
            print("  stderr:", meta.get("stderr", "")[-400:])
            # tratar como NaN/divergencia -> bajar dt
            p["dt"] *= 0.5
            p["damping"] = min(0.25, p["damping"] + 0.05)
            history.append({"iter": it, "crash": True, "meta": meta,
                            "params": {k: p[k] for k in p}})
            no_progress += 1
            if no_progress >= NO_PROGRESS_LIMIT:
                print("[loop] sin progreso -> parar"); break
            continue

        score = rep["score"]
        print(f"  run={meta['run_s']:.0f}s  malla={meta['mesh']}  SCORE {score}/{rep['score_max']}")
        for k, gg in rep["gates"].items():
            print(f"    [{'PASS' if gg['pass'] else 'FAIL'}] {k}: {gg['detail']}")

        # checkpoint si mejora
        improved = score > best["score"]
        if improved:
            ck = checkpoint_best(it, score)
            best = {"score": score, "iter": it, "ckpt": ck,
                    "rep": {k: v for k, v in rep.items() if k != "series"},
                    "params": copy.deepcopy(p), "Lx": rep["_Lx"], "Ly": rep["_Ly"]}
            no_progress = 0
            print(f"  >> nuevo MEJOR (score {score}) checkpoint {ck}")
        else:
            no_progress += 1

        history.append({
            "iter": it, "score": score, "passed": rep["passed"],
            "run_s": meta["run_s"], "mesh": meta["mesh"],
            "gates": {k: {"pass": v["pass"], "detail": v["detail"]}
                      for k, v in rep["gates"].items()},
            "series": rep.get("series"),
            "params": {k: p[k] for k in p},
        })
        with open(HIST, "w") as f:
            json.dump(history, f, indent=2, default=str)

        if rep["passed"]:
            print("\n[loop] *** ROMPIMIENTO PERFECTO: TODOS LOS GATES PASAN ***")
            break
        if no_progress >= NO_PROGRESS_LIMIT:
            print(f"[loop] sin progreso en {NO_PROGRESS_LIMIT} iters -> parar")
            break

        # diagnosticar + ajustar
        prev_runout = rep["gates"].get("f_runout_converge", {}).get("runout", 0)
        p, adj = diagnose(rep, p, prev_runout)
        print("  DIAGNOSTICO/AJUSTE:", adj)
        history[-1]["ajuste"] = adj
        with open(HIST, "w") as f:
            json.dump(history, f, indent=2, default=str)

    # guardar resumen best
    with open(os.path.join(ROOT, "reports", "best.json"), "w") as f:
        json.dump(best, f, indent=2, default=str)
    print(f"\n[loop] FIN. Mejor score {best['score']} en iter {best['iter']} "
          f"ckpt={best['ckpt']}")
    return best


if __name__ == "__main__":
    main()
