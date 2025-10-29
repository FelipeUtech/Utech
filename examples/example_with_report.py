"""
Ejemplo que demuestra el uso de la función de reporte completo
"""

import sys
sys.path.append('..')

from src.pile_analysis.models import PileProperties, SoilLayer, LoadCase
from src.pile_analysis.lateral_load_algorithm import LateralLoadAnalysis


def main():
    print("=" * 80)
    print("EJEMPLO DE ANÁLISIS CON REPORTE COMPLETO")
    print("=" * 80)
    print()

    # 1. Definir propiedades del pilote
    pile = PileProperties.circular_pile(
        length=20.0,
        diameter=1.0,
        elastic_modulus=25e9
    )

    # 2. Definir estratos de suelo usando módulo de Young
    soil_layers = [
        SoilLayer.from_elastic_modulus(
            depth_top=0.0,
            depth_bottom=5.0,
            elastic_modulus=10e6,  # 10 MPa
            pile_diameter=pile.diameter
        ),
        SoilLayer.from_elastic_modulus(
            depth_top=5.0,
            depth_bottom=10.0,
            elastic_modulus=20e6,  # 20 MPa
            pile_diameter=pile.diameter
        ),
        SoilLayer.from_elastic_modulus(
            depth_top=10.0,
            depth_bottom=20.0,
            elastic_modulus=80e6,  # 80 MPa
            pile_diameter=pile.diameter
        )
    ]

    # 3. Definir caso de carga
    load = LoadCase(
        horizontal_load=1000e3,  # 1000 kN
        moment=0.0,              # Sin momento
        free_head=True
    )

    # 4. Ejecutar análisis
    print("Ejecutando análisis...")
    analysis = LateralLoadAnalysis(
        pile=pile,
        soil_layers=soil_layers,
        num_elements=100
    )
    results = analysis.solve(load)
    print("¡Análisis completado!")
    print()

    # 5. Generar reporte completo
    print("=" * 80)
    print("GENERANDO REPORTE COMPLETO")
    print("=" * 80)
    print()

    # Opción 1: Mostrar reporte en consola
    report_text = results.generate_report(
        pile=pile,
        soil_layers=soil_layers,
        load_case=load,
        save_report_path='reporte_analisis.txt',
        save_plot_path='reporte_graficos.png',
        show_plot=False  # No mostrar gráfico (solo guardarlo)
    )

    # Imprimir el reporte
    print(report_text)
    print()
    print("=" * 80)
    print("ARCHIVOS GENERADOS:")
    print("=" * 80)
    print("  - reporte_analisis.txt   (Reporte de texto)")
    print("  - reporte_graficos.png   (Gráficos)")
    print()


if __name__ == "__main__":
    main()
