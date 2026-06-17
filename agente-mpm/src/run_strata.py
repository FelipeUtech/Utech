"""
run_strata.py — Modelo MPM ESTRATIFICADO de la Seccion A-A real (CEMEX La Susana).
4 horizontes Dearman (VI/V/IV/I) con Mohr-Coulomb por estrato, K0 por estrato,
NF critico (NAF_CRITICO), berma aguas abajo para runout, y reduccion de
resistencia (SRF) que dispara la falla. Ablandamiento pico->residual => la cuña
se desprende y fluye.

Uso: python run_strata.py [SRF] [nsteps]
"""
import sys, os, math, shutil, subprocess, json, time
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import dxf_to_section as D, meshgen as mg, postprocess as PP, gates as G

DXF = "/home/user/Utech/#seccion_A-A.dxf"
MPM = "/home/user/mpm-build/build/mpm"
ROOT = os.path.abspath(os.path.join(HERE, ".."))
CASE = os.path.join(ROOT, "cases", "seccionA_strata")
H = 2.5; PPC = 2; APRON = 180.0; SIDE = 2.0; BASEM = 3.0  # runout: berma MUY amplia aguas abajo
UPSTREAM = 0.0
GW = 9.81  # kN/m3 agua

# --- Parametros por horizonte (tabla Dearman del usuario) ---
# densidad EFECTIVA (boyante) = (gamma_sat - gamma_w)/g * 1000  [kg/m3]
def rho_eff(gsat): return (gsat - GW) / GW * 1000.0
HOR = {  # id: nombre, gamma_sat, c'kPa, phi', psi, E_MPa, nu, ratio_res
    0: dict(name="VI", gsat=20.0, c=10e3, phi=25, psi=0, E=20e6,  nu=0.30, r=0.4),
    1: dict(name="V",  gsat=21.0, c=20e3, phi=30, psi=0, E=50e6,  nu=0.30, r=0.4),
    2: dict(name="IV", gsat=21.5, c=50e3, phi=34, psi=5, E=400e6, nu=0.28, r=0.7),
    3: dict(name="I",  gsat=26.3, c=10e3, phi=0,  psi=0, E=500e6, nu=0.25, r=1.0),  # bedrock rigido
}


def geometry():
    poly, nf_y, meta = D.section_polygon_from_dxf(
        DXF, profile_layer="TERRENO", nf_layer="NAF_CRITICO",
        base_margin=BASEM, side_margin=SIDE, runout_pad=0.0,
        downstream_apron=APRON, upstream_apron=UPSTREAM)
    Lx = max(p[0] for p in poly) + 5.0
    Ly = max(p[1] for p in poly) + 4.0
    # transform para clasificar contactos (mismo shift que el poligono, +UPSTREAM)
    polys = D.extract_polylines(DXF)
    ter = max([p for p in polys if p["layer"] == "TERRENO"], key=lambda d: d["length"])
    T = np.array(ter["pts"]); T = T[np.argsort(T[:, 0])]
    xoff = SIDE + UPSTREAM - T[:, 0].min(); yshift = T[:, 1].min() - BASEM
    def tx(pp):
        a = np.array(pp, float); a[:, 0] += xoff; a[:, 1] -= yshift
        return a[np.argsort(a[:, 0])]
    cons = sorted([p for p in polys if p["layer"] == "CONTORNO"],
                  key=lambda d: np.array(d["pts"])[:, 0].max())
    def pick(xt): return tx([p for p in cons
                             if abs(np.array(p["pts"])[:, 0].max() - xt) < 8][0]["pts"])
    c_viv, c_v4, c_4i = pick(89), pick(99), pick(113)
    def at(c, x): return np.interp(x, c[:, 0], c[:, 1], left=c[1, 1], right=np.inf)
    def classify(x, y):
        if y >= at(c_viv, x): return 0   # VI
        if y >= at(c_v4, x):  return 1   # V
        if y >= at(c_4i, x):  return 2   # IV
        return 3                          # I bedrock
    return poly, Lx, Ly, nf_y, classify


def material(hid, srf):
    h = HOR[hid]; rho = rho_eff(h["gsat"])
    phi_p = h["phi"]; c_p = h["c"]
    if MONO:
        # cuerpo movilizado homogeneo: se desprende, desliza y CAE ladera abajo.
        # pico moderado (falla bajo gravedad), residual casi nulo (fluye y cae).
        return dict(id=hid, type="MohrCoulomb2D", density=2000.0, youngs_modulus=3.0e7,
                    poisson_ratio=0.30, friction=18.0, dilation=0.0, cohesion=8000.0,
                    residual_friction=4.0, residual_dilation=0.0, residual_cohesion=0.0,
                    peak_pdstrain=0.003, residual_pdstrain=0.03, tension_cutoff=2000.0,
                    softening=True)
    if hid == 3:  # bedrock: rigido, no falla, sin SRF
        return dict(id=3, type="MohrCoulomb2D", density=rho, youngs_modulus=h["E"],
                    poisson_ratio=h["nu"], friction=45.0, dilation=0.0, cohesion=1.0e6,
                    residual_friction=45.0, residual_dilation=0.0, residual_cohesion=1.0e6,
                    peak_pdstrain=0.0, residual_pdstrain=0.0, tension_cutoff=1.0e6,
                    softening=False)
    # reduccion de resistencia (SRM): c y tan(phi) divididos por srf
    def red(c, phi): return c / srf, math.degrees(math.atan(math.tan(math.radians(phi)) / srf))
    c_pk, phi_pk = red(c_p, phi_p)
    if FLOW:
        # escenario DESLIZAMIENTO-FLUJO (NF critico): residual casi nulo => corre
        c_rs, phi_rs = 0.0, FLOW_PHI_RES
        pk_pd, rs_pd = 0.002, 0.02   # ablandamiento abrupto => moviliza rapido
    else:
        c_rs, phi_rs = red(c_p * h["r"], math.degrees(math.atan(math.tan(math.radians(phi_p)) * h["r"])))
        pk_pd, rs_pd = 0.01, 0.08
    return dict(id=hid, type="MohrCoulomb2D", density=rho, youngs_modulus=h["E"],
                poisson_ratio=h["nu"], friction=phi_pk, dilation=h["psi"], cohesion=c_pk,
                residual_friction=phi_rs, residual_dilation=h["psi"] * h["r"],
                residual_cohesion=c_rs, peak_pdstrain=pk_pd, residual_pdstrain=rs_pd,
                tension_cutoff=max(1e3, c_pk * 0.5), softening=True)


def build(case, poly, Lx, Ly, nf_y, classify, srf):
    shutil.rmtree(case, ignore_errors=True); os.makedirs(case)
    nodes, cells, grid = mg.build_grid(Lx, Ly, H)
    pts = mg.seed_particles(cells, nodes, grid,
                            lambda x, y: mg.point_in_poly(x, y, poly), ppc=PPC)
    mat = np.array([classify(x, y) for x, y in pts])
    mg.write_mesh(os.path.join(case, "mesh.txt"), nodes, cells)
    nsets = mg.boundary_node_sets(nodes, grid)
    mg.write_entity_sets(os.path.join(case, "entity_sets.json"), nsets)
    # superficie por columna (para profundidad K0)
    from collections import defaultdict
    col = defaultdict(float)
    for x, y in pts:
        col[round(x, 4)] = max(col[round(x, 4)], y)
    # agrupar por material en orden 0..3; archivos de particulas + stresses global
    order = []; gens = []
    stress_lines = []
    for hid in range(4):
        idx = np.where(mat == hid)[0]
        if len(idx) == 0: continue
        gp = pts[idx]
        with open(os.path.join(case, f"part_{hid}.txt"), "w") as f:
            f.write(f"{len(gp)}\n")
            for x, y in gp: f.write(f"{x:.4f}\t{y:.4f}\n")
        gens.append({"generator": {"check_duplicates": True, "location": f"part_{hid}.txt",
                     "io_type": "Ascii2D", "pset_id": hid, "particle_type": "P2D",
                     "material_id": hid, "type": "file"}})
        rho = HOR[hid]["gsat"]; rho_e = rho_eff(rho)
        K0 = 1.0 - math.sin(math.radians(HOR[hid]["phi"] if hid != 3 else 30))
        for x, y in gp:
            depth = max(0.0, col[round(x, 4)] + 0.25 * H - y)
            sv = -rho_e * 9.81 * depth; sh = K0 * sv
            stress_lines.append(f"{sh:.2f} {sv:.2f} {sh:.2f} 0 0 0")
        order.append(hid)
    with open(os.path.join(case, "particle_stresses.txt"), "w") as f:
        f.write(f"{len(stress_lines)}\n" + "\n".join(stress_lines) + "\n")
    mats = [material(h, srf) for h in range(4)]
    j = {"title": "Seccion A-A estratificada (SRF=%.2f)" % srf,
         "mesh": {"mesh": "mesh.txt", "entity_sets": "entity_sets.json", "cell_type": "ED2Q4",
                  "isoparametric": False, "io_type": "Ascii2D", "node_type": "N2D",
                  "particles_stresses": "particle_stresses.txt",
                  "boundary_conditions": {"velocity_constraints": [
                      {"nset_id": 0, "dir": 0, "velocity": 0.0}, {"nset_id": 0, "dir": 1, "velocity": 0.0},
                      {"nset_id": 1, "dir": 0, "velocity": 0.0}, {"nset_id": 2, "dir": 0, "velocity": 0.0}]}},
         "particles": gens, "materials": mats,
         "external_loading_conditions": {"gravity": [0.0, -9.81]},
         "analysis": {"type": "MPMExplicit2D", "stress_update": "usf", "dt": DT,
                      "uuid": "strata", "nsteps": NSTEPS, "velocity_update": True,
                      "damping": {"type": "Cundall", "damping_factor": DAMP},
                      "resume": {"resume": False, "uuid": "strata", "step": 0}},
         "post_processing": {"path": "results/", "output_steps": max(1, NSTEPS // 100)}}
    json.dump(j, open(os.path.join(case, "mpm.json"), "w"), indent=2)
    return len(nodes), len(cells), len(pts), mat


DT = 8.0e-4; NSTEPS = 10000
FLOW = False; FLOW_PHI_RES = 2.0; DAMP = 0.05; MONO = False
if __name__ == "__main__":
    srf = float(sys.argv[1]) if len(sys.argv) > 1 else 1.6
    if len(sys.argv) > 2: NSTEPS = int(sys.argv[2])
    if len(sys.argv) > 3 and sys.argv[3] == "flow":
        FLOW = True; DAMP = 0.02
    if len(sys.argv) > 3 and sys.argv[3] == "mono":
        MONO = True; DAMP = 0.02
    poly, Lx, Ly, nf_y, classify = geometry()
    nn, nc, npart, mat = build(CASE, poly, Lx, Ly, nf_y, classify, srf)
    names = ["VI", "V", "IV", "I"]
    dist = " ".join(f"{names[i]}={int((mat==i).sum())}" for i in range(4))
    open("/tmp/strata.log", "w").write(
        f"START srf={srf} dom {Lx:.0f}x{Ly:.0f} part {npart} [{dist}] nsteps {NSTEPS}\n")
    t = time.time()
    r = subprocess.run([MPM, "-f", CASE + "/", "-i", "mpm.json", "-p", "4"],
                       capture_output=True, text=True)
    with open("/tmp/strata.log", "a") as f:
        f.write(f"DONE rc={r.returncode} t={time.time()-t:.0f}s\n")
        if r.returncode:
            f.write("ERR " + (r.stderr.strip().splitlines()[-1] if r.stderr.strip() else "?") + "\n")
