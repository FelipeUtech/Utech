"""
make_case.py — Construye un caso cb-geo MPM completo (malla, partículas,
entity_sets, mpm.json) a partir de un diccionario de configuración.

Soporta:
  - 1 fase: MohrCoulomb2D seco (calibración columna granular).
  - 2 fases: MPMExplicitTwoPhase2D, sólido MohrCoulomb2D + líquido (bulk),
    nivel freático (water_table) para "NF alto".
"""
import os
import json
import numpy as np
import meshgen as mg


def build(case_dir, cfg):
    os.makedirs(case_dir, exist_ok=True)
    g = cfg["grid"]
    nodes, cells, grid = mg.build_grid(g["Lx"], g["Ly"], g["h"])
    region = cfg["region_fn"]
    pts = mg.seed_particles(cells, nodes, grid, region, ppc=cfg.get("ppc", 2))
    if len(pts) == 0:
        raise SystemExit("0 particulas: revisar region/geometria")
    mg.write_mesh(os.path.join(case_dir, "mesh.txt"), nodes, cells)
    mg.write_particles(os.path.join(case_dir, "particles.txt"), pts)
    nsets = mg.boundary_node_sets(nodes, grid)
    mg.write_entity_sets(os.path.join(case_dir, "entity_sets.json"), nsets)

    # --- Estado geostatico K0 (estado in-situ) -------------------------------
    # Inicializa la tension efectiva en compresion para arrancar en equilibrio
    # y evitar el shock gravitacional en t=0. Convencion cb-geo: traccion (+).
    #   sigma_v = -gamma*g*profundidad ;  sigma_h = K0*sigma_v ;  K0 = 1 - sin(phi)
    if cfg.get("initial_stress_K0", False):
        import math
        rho = cfg["materials"][0]["density"]
        phi = math.radians(cfg["materials"][0].get("friction", 25.0))
        K0 = max(0.3, 1.0 - math.sin(phi))
        g = abs(cfg.get("gravity", [0, -9.81])[1])
        # superficie por sub-columna (mismo x): tope de particulas + 1/4 celda
        from collections import defaultdict
        col = defaultdict(float)
        for x, y in pts:
            if y > col[round(x, 6)]:
                col[round(x, 6)] = y
        half = 0.25 * cfg["grid"]["h"]
        stress_path = os.path.join(case_dir, "particle_stresses.txt")
        with open(stress_path, "w") as f:
            f.write(f"{len(pts)}\n")
            for x, y in pts:
                surf = col[round(x, 6)] + half
                depth = max(0.0, surf - y)
                sv = -rho * g * depth            # vertical efectiva (compresion -)
                sh = K0 * sv
                f.write(f"{sh:.3f} {sv:.3f} {sh:.3f} 0 0 0\n")

    twophase = cfg.get("twophase", False)
    ptype = "P2D2PHASE" if twophase else "P2D"
    atype = "MPMExplicitTwoPhase2D" if twophase else "MPMExplicit2D"
    material_id = cfg["material_id"]  # int o [solid, liquid]

    mesh_block = {
        "mesh": "mesh.txt",
        "entity_sets": "entity_sets.json",
        "cell_type": cfg.get("cell_type", "ED2Q4"),
        "isoparametric": False,
        "io_type": "Ascii2D",
        "node_type": "N2D",
        "boundary_conditions": {
            "velocity_constraints": cfg["velocity_constraints"],
        },
    }
    if cfg.get("initial_stress_K0", False):
        mesh_block["particles_stresses"] = "particle_stresses.txt"
    if twophase and "water_table" in cfg:
        wt = cfg["water_table"]
        mesh_block["particles_pore_pressures"] = {
            "type": "water_table",
            "dir_v": 1,
            "dir_h": 0,
            "water_tables": [{"position": wt["position"], "h0": wt.get("h0", 0.0)}],
        }

    j = {
        "title": cfg.get("title", "case"),
        "mesh": mesh_block,
        "particles": [{
            "generator": {
                "check_duplicates": True,
                "location": "particles.txt",
                "io_type": "Ascii2D",
                "pset_id": 0,
                "particle_type": ptype,
                "material_id": material_id,
                "type": "file",
            }
        }],
        "materials": cfg["materials"],
        "external_loading_conditions": {"gravity": cfg.get("gravity", [0.0, -9.81])},
        "analysis": {
            "type": atype,
            "stress_update": cfg.get("stress_update", "usf"),
            "dt": cfg["dt"],
            "uuid": cfg["uuid"],
            "nsteps": cfg["nsteps"],
            "velocity_update": cfg.get("velocity_update", True),
            "damping": {"type": "Cundall", "damping_factor": cfg.get("damping", 0.05)},
            "resume": {"resume": False, "uuid": cfg["uuid"], "step": 0},
        },
        "post_processing": {
            "path": "results/",
            "output_steps": cfg["output_steps"],
        },
    }
    if twophase:
        j["analysis"]["pore_pressure_smoothing"] = cfg.get("pore_pressure_smoothing", True)
    with open(os.path.join(case_dir, "mpm.json"), "w") as f:
        json.dump(j, f, indent=2)
    return len(nodes), len(cells), len(pts)
