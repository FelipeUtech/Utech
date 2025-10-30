"""
Comparación de análisis lineal vs no lineal (Modelo Duncan-Chang)

Compara el comportamiento del pilote usando:
1. Modelo lineal (Winkler): k_h constante
2. Modelo no lineal (Duncan-Chang): k_h degrada con deflexión
"""

import sys
sys.path.append('..')

import numpy as np
import matplotlib.pyplot as plt
from src.pile_analysis.models import PileProperties, SoilLayer, SoilLayerNonlinear, LoadCase
from src.pile_analysis.lateral_load_algorithm import LateralLoadAnalysis
from src.pile_analysis.nonlinear_analysis import NonlinearLateralLoadAnalysis


def main():
    print("=" * 80)
    print("COMPARACIÓN: ANÁLISIS LINEAL vs NO LINEAL (DUNCAN-CHANG)")
    print("=" * 80)
    print()

    # Propiedades del pilote
    pile = PileProperties.circular_pile(
        length=20.0,
        diameter=1.0,
        elastic_modulus=25e9
    )

    # Caso de carga
    load = LoadCase(
        horizontal_load=1000e3,  # 1000 kN
        moment=0.0,
        free_head=True
    )

    print("CONFIGURACIÓN DEL ANÁLISIS:")
    print("-" * 80)
    print(f"  Pilote: L={pile.length}m, D={pile.diameter}m, E={pile.elastic_modulus/1e9}GPa")
    print(f"  Carga: P={load.horizontal_load/1e3}kN, M={load.moment/1e3}kN·m")
    print()

    # ========== MODELO LINEAL ==========
    print("1. ANÁLISIS LINEAL (Winkler - k_h constante)")
    print("-" * 80)

    soil_layers_linear = [
        SoilLayer.from_elastic_modulus(0.0, 5.0, 10e6, pile.diameter),
        SoilLayer.from_elastic_modulus(5.0, 10.0, 20e6, pile.diameter),
        SoilLayer.from_elastic_modulus(10.0, 20.0, 80e6, pile.diameter)
    ]

    for i, layer in enumerate(soil_layers_linear, 1):
        print(f"  Estrato {i}: k_h = {layer.k_h/1e6:.2f} MN/m³ (constante)")

    analysis_linear = LateralLoadAnalysis(
        pile=pile,
        soil_layers=soil_layers_linear,
        num_elements=100
    )

    print("  Ejecutando análisis lineal...")
    results_linear = analysis_linear.solve(load)
    print("  ✓ Análisis lineal completado")
    print()

    # ========== MODELO NO LINEAL ==========
    print("2. ANÁLISIS NO LINEAL (Duncan-Chang - k_h variable)")
    print("-" * 80)

    soil_layers_nonlinear = [
        SoilLayerNonlinear.from_elastic_modulus(0.0, 5.0, 10e6, pile.diameter, ultimate_strain=0.02),
        SoilLayerNonlinear.from_elastic_modulus(5.0, 10.0, 20e6, pile.diameter, ultimate_strain=0.02),
        SoilLayerNonlinear.from_elastic_modulus(10.0, 20.0, 80e6, pile.diameter, ultimate_strain=0.02)
    ]

    for i, layer in enumerate(soil_layers_nonlinear, 1):
        print(f"  Estrato {i}: k_h_inicial = {layer.k_h_inicial/1e6:.2f} MN/m³")
        print(f"            p_ult = {layer.p_ult/1e3:.0f} kN/m")

    analysis_nonlinear = NonlinearLateralLoadAnalysis(
        pile=pile,
        soil_layers=soil_layers_nonlinear,
        num_elements=100
    )

    print()
    results_nonlinear = analysis_nonlinear.solve(load, max_iterations=20, tolerance=1e-4)
    print()

    # ========== COMPARACIÓN DE RESULTADOS ==========
    print("=" * 80)
    print("COMPARACIÓN DE RESULTADOS")
    print("=" * 80)
    print()

    print(f"{'Parámetro':<35} {'Lineal':<15} {'No Lineal':<15} {'Diferencia'}")
    print("-" * 80)

    # Deflexión en cabeza
    y0_lin = results_linear.head_deflection() * 1000
    y0_nl = results_nonlinear.head_deflection() * 1000
    diff_y0 = ((y0_nl - y0_lin) / y0_lin) * 100
    print(f"{'Deflexión en cabeza (mm)':<35} {y0_lin:>14.3f} {y0_nl:>14.3f} {diff_y0:>+10.1f}%")

    # Rotación en cabeza
    theta0_lin = results_linear.head_rotation() * 1000
    theta0_nl = results_nonlinear.head_rotation() * 1000
    diff_theta = ((theta0_nl - theta0_lin) / abs(theta0_lin)) * 100
    print(f"{'Rotación en cabeza (mrad)':<35} {theta0_lin:>14.3f} {theta0_nl:>14.3f} {diff_theta:>+10.1f}%")

    # Momento máximo
    M_max_lin, z_M_lin = results_linear.max_moment()
    M_max_nl, z_M_nl = results_nonlinear.max_moment()
    diff_M = ((M_max_nl - M_max_lin) / abs(M_max_lin)) * 100
    print(f"{'Momento máximo (kN·m)':<35} {M_max_lin/1e3:>14.2f} {M_max_nl/1e3:>14.2f} {diff_M:>+10.1f}%")
    print(f"{'  Profundidad (m)':<35} {z_M_lin:>14.2f} {z_M_nl:>14.2f}")

    # Cortante máximo
    V_max_lin = np.max(results_linear.shears)
    V_max_nl = np.max(results_nonlinear.shears)
    print(f"{'Cortante máximo (kN)':<35} {V_max_lin/1e3:>14.2f} {V_max_nl/1e3:>14.2f}")

    # Presión del suelo máxima
    p_max_lin = np.max(np.abs(results_linear.soil_pressures))
    p_max_nl = np.max(np.abs(results_nonlinear.soil_pressures))
    diff_p = ((p_max_nl - p_max_lin) / p_max_lin) * 100
    print(f"{'Presión del suelo máxima (kN/m)':<35} {p_max_lin/1e3:>14.2f} {p_max_nl/1e3:>14.2f} {diff_p:>+10.1f}%")

    print()
    print("Observación:")
    if diff_y0 > 0:
        print(f"  • El modelo no lineal predice deflexiones {abs(diff_y0):.1f}% MAYORES")
        print(f"    (La rigidez efectiva del suelo disminuye con la deflexión)")
    else:
        print(f"  • El modelo no lineal predice deflexiones {abs(diff_y0):.1f}% MENORES")

    print()

    # ========== GRÁFICOS COMPARATIVOS ==========
    print("Generando gráficos comparativos...")

    fig, axes = plt.subplots(2, 3, figsize=(18, 12))

    # Deflexión
    axes[0,0].plot(results_linear.deflections * 1000, results_linear.depths,
                   'b-', linewidth=2.5, label='Lineal')
    axes[0,0].plot(results_nonlinear.deflections * 1000, results_nonlinear.depths,
                   'r--', linewidth=2.5, label='No Lineal (Duncan-Chang)')
    axes[0,0].set_xlabel('Deflexión, y (mm)', fontsize=11)
    axes[0,0].set_ylabel('Profundidad, z (m)', fontsize=11)
    axes[0,0].grid(True, alpha=0.3, linestyle='--')
    axes[0,0].invert_yaxis()
    axes[0,0].set_title('(a) Deflexión Lateral', fontsize=12, fontweight='bold')
    axes[0,0].legend(fontsize=10)
    axes[0,0].axvline(0, color='k', linewidth=0.5, alpha=0.3)

    # Rotación
    axes[0,1].plot(results_linear.rotations * 1000, results_linear.depths,
                   'b-', linewidth=2.5, label='Lineal')
    axes[0,1].plot(results_nonlinear.rotations * 1000, results_nonlinear.depths,
                   'r--', linewidth=2.5, label='No Lineal')
    axes[0,1].set_xlabel('Rotación, θ (mrad)', fontsize=11)
    axes[0,1].set_ylabel('Profundidad, z (m)', fontsize=11)
    axes[0,1].grid(True, alpha=0.3, linestyle='--')
    axes[0,1].invert_yaxis()
    axes[0,1].set_title('(b) Rotación', fontsize=12, fontweight='bold')
    axes[0,1].legend(fontsize=10)
    axes[0,1].axvline(0, color='k', linewidth=0.5, alpha=0.3)

    # Momento
    axes[0,2].plot(results_linear.moments / 1000, results_linear.depths,
                   'b-', linewidth=2.5, label='Lineal')
    axes[0,2].plot(results_nonlinear.moments / 1000, results_nonlinear.depths,
                   'r--', linewidth=2.5, label='No Lineal')
    axes[0,2].set_xlabel('Momento, M (kN·m)', fontsize=11)
    axes[0,2].set_ylabel('Profundidad, z (m)', fontsize=11)
    axes[0,2].grid(True, alpha=0.3, linestyle='--')
    axes[0,2].invert_yaxis()
    axes[0,2].set_title('(c) Momento Flector', fontsize=12, fontweight='bold')
    axes[0,2].legend(fontsize=10)
    axes[0,2].axvline(0, color='k', linewidth=0.5, alpha=0.3)

    # Cortante
    axes[1,0].plot(results_linear.shears / 1000, results_linear.depths,
                   'b-', linewidth=2.5, label='Lineal')
    axes[1,0].plot(results_nonlinear.shears / 1000, results_nonlinear.depths,
                   'r--', linewidth=2.5, label='No Lineal')
    axes[1,0].set_xlabel('Cortante, V (kN)', fontsize=11)
    axes[1,0].set_ylabel('Profundidad, z (m)', fontsize=11)
    axes[1,0].grid(True, alpha=0.3, linestyle='--')
    axes[1,0].invert_yaxis()
    axes[1,0].set_title('(d) Fuerza Cortante', fontsize=12, fontweight='bold')
    axes[1,0].legend(fontsize=10)
    axes[1,0].axvline(0, color='k', linewidth=0.5, alpha=0.3)

    # Presión del suelo
    axes[1,1].plot(results_linear.soil_pressures / 1000, results_linear.depths,
                   'b-', linewidth=2.5, label='Lineal')
    axes[1,1].plot(results_nonlinear.soil_pressures / 1000, results_nonlinear.depths,
                   'r--', linewidth=2.5, label='No Lineal')
    axes[1,1].set_xlabel('Presión del suelo, p (kN/m)', fontsize=11)
    axes[1,1].set_ylabel('Profundidad, z (m)', fontsize=11)
    axes[1,1].grid(True, alpha=0.3, linestyle='--')
    axes[1,1].invert_yaxis()
    axes[1,1].set_title('(e) Presión del Suelo', fontsize=12, fontweight='bold')
    axes[1,1].legend(fontsize=10)
    axes[1,1].axvline(0, color='k', linewidth=0.5, alpha=0.3)

    # Curva k_h vs profundidad
    k_h_linear = np.array([soil_layers_linear[0].k_h] * len(results_linear.depths))
    k_h_nonlinear = np.zeros_like(results_nonlinear.deflections)
    for i, (depth, y) in enumerate(zip(results_nonlinear.depths, results_nonlinear.deflections)):
        for layer in soil_layers_nonlinear:
            if layer.contains_depth(depth) or abs(depth - layer.depth_bottom) < 1e-6:
                k_h_nonlinear[i] = layer.get_k_h(y, pile.diameter)
                break

    # Ajustar k_h_linear para mostrar los diferentes estratos
    for i, depth in enumerate(results_linear.depths):
        for layer in soil_layers_linear:
            if layer.contains_depth(depth) or abs(depth - layer.depth_bottom) < 1e-6:
                k_h_linear[i] = layer.k_h
                break

    axes[1,2].plot(k_h_linear / 1e6, results_linear.depths,
                   'b-', linewidth=2.5, label='Lineal (constante)')
    axes[1,2].plot(k_h_nonlinear / 1e6, results_nonlinear.depths,
                   'r--', linewidth=2.5, label='No Lineal (degradado)')
    axes[1,2].set_xlabel('Rigidez, k_h (MN/m³)', fontsize=11)
    axes[1,2].set_ylabel('Profundidad, z (m)', fontsize=11)
    axes[1,2].grid(True, alpha=0.3, linestyle='--')
    axes[1,2].invert_yaxis()
    axes[1,2].set_title('(f) Rigidez del Suelo', fontsize=12, fontweight='bold')
    axes[1,2].legend(fontsize=10)

    plt.tight_layout()
    plt.savefig('comparison_linear_nonlinear.png', dpi=300, bbox_inches='tight')
    print("  ✓ Gráfico guardado: comparison_linear_nonlinear.png")
    print()


if __name__ == "__main__":
    main()
