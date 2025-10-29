"""
Generar reporte completo con parámetros personalizados del usuario:
- Carga: 1000 kN sin momento
- E1 = 10 MPa, H = 5m
- E2 = 20 MPa, H = 5m
- E3 = 80 MPa, H = 10m
"""

import sys
sys.path.append('..')

from src.pile_analysis.models import PileProperties, SoilLayer, LoadCase
from src.pile_analysis.lateral_load_algorithm import LateralLoadAnalysis


def main():
    print("=" * 80)
    print("GENERANDO REPORTE CON PARÁMETROS PERSONALIZADOS")
    print("=" * 80)
    print()

    # Propiedades del pilote
    pile = PileProperties.circular_pile(
        length=20.0,
        diameter=1.0,
        elastic_modulus=25e9
    )

    # Estratos de suelo - PARÁMETROS DEL USUARIO
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

    # Caso de carga - PARÁMETROS DEL USUARIO
    load = LoadCase(
        horizontal_load=1000e3,  # 1000 kN
        moment=0.0,              # Sin momento
        free_head=True           # Cabeza libre
    )

    # Ejecutar análisis
    print("Ejecutando análisis con parámetros personalizados...")
    analysis = LateralLoadAnalysis(
        pile=pile,
        soil_layers=soil_layers,
        num_elements=100
    )
    results = analysis.solve(load)
    print("¡Análisis completado!")
    print()

    # Generar reporte completo
    print("=" * 80)
    print("GENERANDO REPORTE COMPLETO")
    print("=" * 80)
    print()

    report_text = results.generate_report(
        pile=pile,
        soil_layers=soil_layers,
        load_case=load,
        save_report_path='reporte_parametros_usuario.txt',
        save_plot_path='graficos_parametros_usuario.png',
        show_plot=False
    )

    # Mostrar reporte
    print(report_text)
    print()
    print("=" * 80)
    print("ARCHIVOS GENERADOS:")
    print("=" * 80)
    print("  ✓ reporte_parametros_usuario.txt   (Reporte completo de texto)")
    print("  ✓ graficos_parametros_usuario.png  (Gráficos de resultados)")
    print()


if __name__ == "__main__":
    main()
