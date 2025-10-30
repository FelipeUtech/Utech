"""
Análisis de curva carga-deflexión hasta la falla
Compara modelo lineal vs no lineal (Duncan-Chang) para múltiples cargas
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
    print("CURVA CARGA-DEFLEXIÓN HASTA LA FALLA")
    print("Comparación: Modelo Lineal vs No Lineal (Duncan-Chang)")
    print("=" * 80)
    print()

    # Propiedades del pilote
    pile = PileProperties.circular_pile(
        length=20.0,
        diameter=1.0,
        elastic_modulus=25e9
    )

    # Estratigrafía - Modelo Lineal
    soil_layers_linear = [
        SoilLayer.from_elastic_modulus(0.0, 5.0, 10e6, pile.diameter),
        SoilLayer.from_elastic_modulus(5.0, 10.0, 20e6, pile.diameter),
        SoilLayer.from_elastic_modulus(10.0, 20.0, 80e6, pile.diameter)
    ]

    # Estratigrafía - Modelo No Lineal
    soil_layers_nonlinear = [
        SoilLayerNonlinear.from_elastic_modulus(0.0, 5.0, 10e6, pile.diameter, ultimate_strain=0.02),
        SoilLayerNonlinear.from_elastic_modulus(5.0, 10.0, 20e6, pile.diameter, ultimate_strain=0.02),
        SoilLayerNonlinear.from_elastic_modulus(10.0, 20.0, 80e6, pile.diameter, ultimate_strain=0.02)
    ]

    print("CONFIGURACIÓN:")
    print("-" * 80)
    print(f"  Pilote: L={pile.length}m, D={pile.diameter}m, E={pile.elastic_modulus/1e9}GPa")
    print(f"  Estratos (lineal): k_h = {soil_layers_linear[0].k_h/1e6:.2f}, "
          f"{soil_layers_linear[1].k_h/1e6:.2f}, {soil_layers_linear[2].k_h/1e6:.2f} MN/m³")
    print(f"  Estratos (no lineal): p_ult = {soil_layers_nonlinear[0].p_ult/1e3:.0f}, "
          f"{soil_layers_nonlinear[1].p_ult/1e3:.0f}, {soil_layers_nonlinear[2].p_ult/1e3:.0f} kN/m")
    print()

    # Crear objetos de análisis
    analysis_linear = LateralLoadAnalysis(
        pile=pile,
        soil_layers=soil_layers_linear,
        num_elements=100
    )

    analysis_nonlinear = NonlinearLateralLoadAnalysis(
        pile=pile,
        soil_layers=soil_layers_nonlinear,
        num_elements=100
    )

    # ========== ANÁLISIS INCREMENTAL DE CARGA ==========
    print("ANÁLISIS INCREMENTAL DE CARGA:")
    print("-" * 80)

    # Definir rango de cargas
    # Comenzar con paso grande, luego refinamos si es necesario
    load_step = 50e3  # 50 kN por paso
    max_load = 3000e3  # 3000 kN máximo
    max_deflection = 0.5  # 500 mm - límite práctico de deflexión

    loads = []
    deflections_linear = []
    deflections_nonlinear = []

    load = 0
    failure_reached = False

    print(f"  Paso de carga: {load_step/1e3:.0f} kN")
    print(f"  Carga máxima: {max_load/1e3:.0f} kN")
    print(f"  Deflexión límite: {max_deflection*1000:.0f} mm")
    print()
    print("  Progreso:")

    while load <= max_load and not failure_reached:
        # Crear caso de carga
        load_case = LoadCase(
            horizontal_load=load,
            moment=0.0,
            free_head=True
        )

        # ========== ANÁLISIS LINEAL ==========
        try:
            results_linear = analysis_linear.solve(load_case)
            y_head_linear = results_linear.head_deflection()

            # Verificar si excede límite práctico
            if y_head_linear > max_deflection:
                print(f"    {load/1e3:6.0f} kN: Lineal excede deflexión límite ({y_head_linear*1000:.1f} mm)")
                failure_reached = True
                break

        except Exception as e:
            print(f"    {load/1e3:6.0f} kN: Lineal FALLÓ - {str(e)}")
            failure_reached = True
            break

        # ========== ANÁLISIS NO LINEAL ==========
        try:
            results_nonlinear = analysis_nonlinear.solve(
                load_case,
                max_iterations=30,
                tolerance=1e-4,
                relaxation=0.5
            )
            y_head_nonlinear = results_nonlinear.head_deflection()

            # Verificar convergencia y límite
            if y_head_nonlinear > max_deflection:
                print(f"    {load/1e3:6.0f} kN: No lineal excede deflexión límite ({y_head_nonlinear*1000:.1f} mm)")
                failure_reached = True
                break

        except Exception as e:
            print(f"    {load/1e3:6.0f} kN: No lineal NO CONVERGIÓ - Falla alcanzada")
            failure_reached = True
            break

        # Guardar resultados
        loads.append(load / 1e3)  # Convertir a kN
        deflections_linear.append(y_head_linear * 1000)  # Convertir a mm
        deflections_nonlinear.append(y_head_nonlinear * 1000)  # Convertir a mm

        # Imprimir progreso cada 200 kN
        if load % 200e3 == 0 or load == 0:
            print(f"    {load/1e3:6.0f} kN: y_lin = {y_head_linear*1000:6.1f} mm, "
                  f"y_nl = {y_head_nonlinear*1000:6.1f} mm")

        # Incrementar carga
        load += load_step

    print()
    print(f"  Total de puntos calculados: {len(loads)}")
    print(f"  Carga máxima alcanzada: {loads[-1]:.0f} kN")
    print(f"  Deflexión máxima (lineal): {deflections_linear[-1]:.1f} mm")
    print(f"  Deflexión máxima (no lineal): {deflections_nonlinear[-1]:.1f} mm")
    print()

    # Convertir a arrays numpy
    loads = np.array(loads)
    deflections_linear = np.array(deflections_linear)
    deflections_nonlinear = np.array(deflections_nonlinear)

    # ========== ANÁLISIS DE RESULTADOS ==========
    print("=" * 80)
    print("ANÁLISIS DE RESULTADOS")
    print("=" * 80)
    print()

    # Calcular rigidez inicial (pendiente al inicio)
    if len(loads) > 5:
        k_initial_linear = loads[5] / deflections_linear[5]
        k_initial_nonlinear = loads[5] / deflections_nonlinear[5]
        print(f"Rigidez inicial (P/y a baja carga):")
        print(f"  Modelo lineal:     {k_initial_linear:.2f} kN/mm (constante)")
        print(f"  Modelo no lineal:  {k_initial_nonlinear:.2f} kN/mm (degrada con carga)")
        print()

    # Encontrar carga para deflexión de 25mm (criterio común de servicio)
    idx_25mm_linear = np.where(deflections_linear >= 25)[0]
    idx_25mm_nonlinear = np.where(deflections_nonlinear >= 25)[0]

    if len(idx_25mm_linear) > 0:
        print(f"Carga para deflexión de 25 mm (criterio de servicio típico):")
        print(f"  Modelo lineal:     {loads[idx_25mm_linear[0]]:.0f} kN")
    if len(idx_25mm_nonlinear) > 0:
        print(f"  Modelo no lineal:  {loads[idx_25mm_nonlinear[0]]:.0f} kN")
        if len(idx_25mm_linear) > 0:
            ratio = loads[idx_25mm_linear[0]] / loads[idx_25mm_nonlinear[0]]
            print(f"  Ratio (lin/nl):    {ratio:.2f} (modelo lineal sobrestima {(ratio-1)*100:.1f}%)")
        print()

    # Diferencia al final del análisis
    final_diff = ((deflections_nonlinear[-1] - deflections_linear[-1]) / deflections_linear[-1]) * 100
    print(f"A carga máxima ({loads[-1]:.0f} kN):")
    print(f"  Diferencia en deflexión: {final_diff:+.1f}%")
    print(f"  El modelo no lineal predice {abs(final_diff):.1f}% {'MÁS' if final_diff > 0 else 'MENOS'} deflexión")
    print()

    # ========== GENERAR GRÁFICO ==========
    print("Generando gráfico de curva carga-deflexión...")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # Gráfico 1: Curva P-y completa
    ax1.plot(deflections_linear, loads, 'b-', linewidth=2.5, label='Modelo Lineal (Winkler)')
    ax1.plot(deflections_nonlinear, loads, 'r--', linewidth=2.5, label='Modelo No Lineal (Duncan-Chang)')
    ax1.set_xlabel('Deflexión en cabeza (mm)', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Carga horizontal (kN)', fontsize=12, fontweight='bold')
    ax1.set_title('Curva Carga-Deflexión hasta la Falla', fontsize=13, fontweight='bold')
    ax1.grid(True, alpha=0.3, linestyle='--')
    ax1.legend(fontsize=11, loc='lower right')

    # Línea de referencia para 25mm
    ax1.axvline(25, color='green', linestyle=':', linewidth=1.5, alpha=0.7, label='Límite servicio (25mm)')
    ax1.legend(fontsize=11, loc='lower right')

    # Gráfico 2: Ratio de deflexiones
    ratio_deflections = deflections_nonlinear / deflections_linear
    ax2.plot(loads, ratio_deflections, 'purple', linewidth=2.5)
    ax2.set_xlabel('Carga horizontal (kN)', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Ratio: y_no_lineal / y_lineal', fontsize=12, fontweight='bold')
    ax2.set_title('Ratio de Deflexiones (No Lineal / Lineal)', fontsize=13, fontweight='bold')
    ax2.grid(True, alpha=0.3, linestyle='--')
    ax2.axhline(1.0, color='k', linestyle='--', linewidth=1, alpha=0.5)
    ax2.fill_between(loads, 1, ratio_deflections, alpha=0.2, color='purple')

    # Anotar ratio al final
    ax2.text(loads[-1]*0.6, ratio_deflections[-1]*0.95,
             f'Ratio final = {ratio_deflections[-1]:.2f}x',
             fontsize=11, bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

    plt.tight_layout()
    plt.savefig('load_deflection_curve.png', dpi=300, bbox_inches='tight')
    print("  ✓ Gráfico guardado: load_deflection_curve.png")
    print()

    # ========== GUARDAR DATOS EN ARCHIVO TXT ==========
    print("Guardando datos en archivo de texto...")
    with open('load_deflection_data.txt', 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("CURVA CARGA-DEFLEXION - DATOS TABULADOS\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Pilote: L={pile.length}m, D={pile.diameter}m, E={pile.elastic_modulus/1e9}GPa\n")
        f.write(f"Modelo: Lineal (Winkler) vs No Lineal (Duncan-Chang)\n\n")
        f.write("-" * 80 + "\n")
        f.write(f"{'Carga (kN)':>12} {'y_lineal (mm)':>15} {'y_no_lineal (mm)':>18} {'Diferencia (%)':>16} {'Ratio':>10}\n")
        f.write("-" * 80 + "\n")

        for i in range(len(loads)):
            diff_pct = ((deflections_nonlinear[i] - deflections_linear[i]) / deflections_linear[i]) * 100
            ratio = deflections_nonlinear[i] / deflections_linear[i]
            f.write(f"{loads[i]:>12.1f} {deflections_linear[i]:>15.2f} {deflections_nonlinear[i]:>18.2f} "
                   f"{diff_pct:>+15.1f}% {ratio:>9.3f}\n")

        f.write("-" * 80 + "\n")

    print("  ✓ Datos guardados: load_deflection_data.txt")
    print()

    print("=" * 80)
    print("ANÁLISIS COMPLETADO")
    print("=" * 80)


if __name__ == "__main__":
    main()
