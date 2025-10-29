"""
Ejemplo básico de uso del algoritmo de análisis de pilote con carga lateral
"""

import sys
sys.path.append('..')

from src.pile_analysis.models import PileProperties, SoilLayer, LoadCase
from src.pile_analysis.lateral_load_algorithm import LateralLoadAnalysis


def main():
    print("=" * 80)
    print("ANÁLISIS DE PILOTE CON CARGA LATERAL - EJEMPLO BÁSICO")
    print("=" * 80)
    print()

    # 1. Definir propiedades del pilote (circular de concreto)
    print("1. Propiedades del Pilote:")
    print("-" * 40)
    pile = PileProperties.circular_pile(
        length=20.0,           # 20 metros de longitud
        diameter=1.0,          # 1 metro de diámetro
        elastic_modulus=25e9   # 25 GPa (concreto)
    )
    print(f"   Longitud: {pile.length} m")
    print(f"   Diámetro: {pile.diameter} m")
    print(f"   Módulo E: {pile.elastic_modulus/1e9:.1f} GPa")
    print(f"   Momento de inercia: {pile.moment_inertia:.6f} m^4")
    print(f"   Rigidez EI: {pile.EI/1e6:.2f} MN·m^2")
    print()

    # 2. Definir estratos de suelo
    print("2. Estratos de Suelo:")
    print("-" * 40)
    soil_layers = [
        SoilLayer(depth_top=0.0, depth_bottom=5.0, k_h=10e6),   # Arena suelta
        SoilLayer(depth_top=5.0, depth_bottom=15.0, k_h=5e6),   # Arcilla blanda
        SoilLayer(depth_top=15.0, depth_bottom=20.0, k_h=15e6)  # Arena densa
    ]

    for i, layer in enumerate(soil_layers, 1):
        print(f"   Estrato {i}:")
        print(f"      Profundidad: {layer.depth_top} - {layer.depth_bottom} m")
        print(f"      k_h: {layer.k_h/1e6:.1f} MN/m³")

    print()

    # 3. Definir caso de carga
    print("3. Caso de Carga:")
    print("-" * 40)
    load = LoadCase(
        horizontal_load=100e3,  # 100 kN horizontal
        moment=50e3,            # 50 kN·m
        free_head=True          # Cabeza libre de rotar
    )
    print(f"   Carga horizontal: {load.horizontal_load/1e3:.1f} kN")
    print(f"   Momento: {load.moment/1e3:.1f} kN·m")
    print(f"   Condición de cabeza: {'Libre' if load.free_head else 'Fija'}")
    print()

    # 4. Crear y ejecutar análisis
    print("4. Ejecutando Análisis...")
    print("-" * 40)
    analysis = LateralLoadAnalysis(
        pile=pile,
        soil_layers=soil_layers,
        num_elements=100  # Discretización en 100 elementos
    )

    results = analysis.solve(load)
    print("   ¡Análisis completado!")
    print()

    # 5. Mostrar resultados
    print("5. Resultados del Análisis:")
    print("=" * 80)
    print()

    # Deflexión en cabeza
    print(f"   Deflexión en cabeza del pilote:")
    print(f"      y(0) = {results.head_deflection() * 1000:.3f} mm")
    print()

    # Rotación en cabeza
    print(f"   Rotación en cabeza del pilote:")
    print(f"      θ(0) = {results.head_rotation() * 1000:.3f} mrad")
    print()

    # Deflexión máxima
    max_defl, depth_max_defl = results.max_deflection()
    print(f"   Deflexión máxima:")
    print(f"      y_max = {max_defl * 1000:.3f} mm")
    print(f"      Profundidad: {depth_max_defl:.2f} m")
    print()

    # Momento máximo
    max_moment, depth_max_moment = results.max_moment()
    print(f"   Momento máximo:")
    print(f"      M_max = {max_moment / 1e3:.2f} kN·m")
    print(f"      Profundidad: {depth_max_moment:.2f} m")
    print()

    # Cortante máximo
    max_shear = max(abs(results.shears))
    print(f"   Cortante máximo:")
    print(f"      V_max = {max_shear / 1e3:.2f} kN")
    print()

    # 6. Capacidad del pilote
    print("6. Estimación de Capacidad:")
    print("-" * 40)
    capacity = analysis.get_pile_capacity(max_deflection_limit=0.025)  # 25 mm
    print(f"   Capacidad para deflexión límite de 25 mm:")
    print(f"      P_max ≈ {capacity / 1e3:.1f} kN")
    print()

    # 7. Generar gráficos
    print("7. Generando Gráficos...")
    print("-" * 40)
    try:
        results.plot_results(save_path='pile_analysis_results.png')
        print("   Gráficos guardados en: pile_analysis_results.png")
    except Exception as e:
        print(f"   No se pudieron generar gráficos: {e}")

    print()
    print("=" * 80)
    print("ANÁLISIS COMPLETADO")
    print("=" * 80)


if __name__ == "__main__":
    main()
