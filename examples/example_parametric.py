"""
Ejemplo avanzado: Estudio paramétrico de pilote con carga lateral
"""

import sys
sys.path.append('..')

import numpy as np
from src.pile_analysis.models import PileProperties, SoilLayer, LoadCase
from src.pile_analysis.lateral_load_algorithm import LateralLoadAnalysis


def main():
    print("=" * 80)
    print("ESTUDIO PARAMÉTRICO - PILOTE CON CARGA LATERAL")
    print("=" * 80)
    print()

    # Definir pilote
    pile = PileProperties.circular_pile(
        length=15.0,
        diameter=0.8,
        elastic_modulus=30e9  # Concreto de alta resistencia
    )

    # Definir estratos de suelo (4 capas)
    soil_layers = [
        SoilLayer(depth_top=0.0, depth_bottom=3.0, k_h=8e6),    # Relleno
        SoilLayer(depth_top=3.0, depth_bottom=7.0, k_h=12e6),   # Arena media
        SoilLayer(depth_top=7.0, depth_bottom=12.0, k_h=6e6),   # Arcilla
        SoilLayer(depth_top=12.0, depth_bottom=15.0, k_h=20e6)  # Arena densa
    ]

    # Crear análisis
    analysis = LateralLoadAnalysis(
        pile=pile,
        soil_layers=soil_layers,
        num_elements=150
    )

    print("Configuración del análisis:")
    print(f"  - Pilote: L={pile.length}m, D={pile.diameter}m")
    print(f"  - Estratos de suelo: {len(soil_layers)} capas")
    print(f"  - Elementos: {analysis.num_elements}")
    print()

    # Estudio 1: Variación de carga horizontal
    print("ESTUDIO 1: Variación de carga horizontal")
    print("-" * 80)

    load_range = np.array([50, 100, 150, 200, 250, 300]) * 1e3  # kN

    print(f"{'Carga (kN)':>12} | {'Defl. cabeza (mm)':>18} | "
          f"{'Rot. cabeza (mrad)':>20} | {'Momento máx (kN·m)':>20}")
    print("-" * 80)

    results_list = []
    for load_value in load_range:
        load_case = LoadCase(horizontal_load=load_value, moment=0.0, free_head=True)
        result = analysis.solve(load_case)
        results_list.append(result)

        max_moment, _ = result.max_moment()
        print(f"{load_value/1e3:>12.1f} | {result.head_deflection()*1000:>18.3f} | "
              f"{result.head_rotation()*1000:>20.3f} | {max_moment/1e3:>20.2f}")

    print()

    # Estudio 2: Comparación cabeza libre vs fija
    print("ESTUDIO 2: Comparación de condiciones de frontera")
    print("-" * 80)

    test_load = 150e3  # 150 kN

    # Cabeza libre
    load_free = LoadCase(horizontal_load=test_load, moment=0.0, free_head=True)
    result_free = analysis.solve(load_free)

    # Cabeza fija
    load_fixed = LoadCase(horizontal_load=test_load, moment=0.0, free_head=False)
    result_fixed = analysis.solve(load_fixed)

    print(f"Carga aplicada: {test_load/1e3:.1f} kN")
    print()
    print(f"{'Condición':>15} | {'Defl. (mm)':>12} | {'Rot. (mrad)':>14} | "
          f"{'M_max (kN·m)':>15} | {'Prof. M_max (m)':>17}")
    print("-" * 80)

    max_m_free, depth_m_free = result_free.max_moment()
    print(f"{'Cabeza libre':>15} | {result_free.head_deflection()*1000:>12.3f} | "
          f"{result_free.head_rotation()*1000:>14.3f} | {max_m_free/1e3:>15.2f} | "
          f"{depth_m_free:>17.2f}")

    max_m_fixed, depth_m_fixed = result_fixed.max_moment()
    print(f"{'Cabeza fija':>15} | {result_fixed.head_deflection()*1000:>12.3f} | "
          f"{result_fixed.head_rotation()*1000:>14.3f} | {max_m_fixed/1e3:>15.2f} | "
          f"{depth_m_fixed:>17.2f}")

    print()

    # Diferencias porcentuales
    diff_defl = (result_fixed.head_deflection() - result_free.head_deflection()) / result_free.head_deflection() * 100
    diff_moment = (max_m_fixed - max_m_free) / max_m_free * 100

    print(f"Diferencias (fija vs libre):")
    print(f"  - Deflexión en cabeza: {diff_defl:+.1f}%")
    print(f"  - Momento máximo: {diff_moment:+.1f}%")
    print()

    # Estudio 3: Efecto del módulo de reacción del suelo
    print("ESTUDIO 3: Sensibilidad al módulo de reacción del suelo")
    print("-" * 80)

    k_factors = [0.5, 0.75, 1.0, 1.25, 1.5]  # Factores multiplicadores
    base_k = 10e6  # Módulo base

    print(f"{'Factor k':>10} | {'k_h (MN/m³)':>15} | {'Defl. (mm)':>12} | "
          f"{'M_max (kN·m)':>15}")
    print("-" * 80)

    for k_factor in k_factors:
        # Crear suelo homogéneo con k modificado
        soil_uniform = [SoilLayer(depth_top=0.0, depth_bottom=pile.length,
                                  k_h=base_k * k_factor)]

        # Nuevo análisis
        analysis_k = LateralLoadAnalysis(pile=pile, soil_layers=soil_uniform, num_elements=100)

        # Resolver
        load_test = LoadCase(horizontal_load=150e3, moment=0.0)
        result_k = analysis_k.solve(load_test)

        max_m, _ = result_k.max_moment()
        print(f"{k_factor:>10.2f} | {base_k*k_factor/1e6:>15.1f} | "
              f"{result_k.head_deflection()*1000:>12.3f} | {max_m/1e3:>15.2f}")

    print()

    # Capacidad del pilote
    print("ESTUDIO 4: Capacidad del pilote")
    print("-" * 80)

    deflection_limits = [0.010, 0.015, 0.020, 0.025, 0.030]  # metros

    print(f"{'Límite defl. (mm)':>20} | {'Capacidad (kN)':>18}")
    print("-" * 80)

    for limit in deflection_limits:
        capacity = analysis.get_pile_capacity(max_deflection_limit=limit)
        print(f"{limit*1000:>20.1f} | {capacity/1e3:>18.1f}")

    print()
    print("=" * 80)
    print("ESTUDIO PARAMÉTRICO COMPLETADO")
    print("=" * 80)


if __name__ == "__main__":
    main()
