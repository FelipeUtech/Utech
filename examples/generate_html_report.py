"""
Generar reporte HTML completo con gráficos integrados y esquema del pilote
"""

import sys
sys.path.append('..')

from src.pile_analysis.models import PileProperties, SoilLayer, LoadCase
from src.pile_analysis.lateral_load_algorithm import LateralLoadAnalysis


def main():
    print("=" * 80)
    print("GENERANDO REPORTE HTML COMPLETO CON GRÁFICOS INTEGRADOS")
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
    print()
    analysis = LateralLoadAnalysis(
        pile=pile,
        soil_layers=soil_layers,
        num_elements=100
    )
    results = analysis.solve(load)
    print("✓ Análisis completado!")
    print()

    # Generar reporte completo en HTML
    print("Generando reporte HTML completo...")
    print("  - Esquema del pilote con estratos y carga")
    print("  - Gráficos de deflexión, rotación, momento, cortante y presión")
    print("  - Resultados detallados")
    print()

    html_path = results.generate_complete_report(
        pile=pile,
        soil_layers=soil_layers,
        load_case=load,
        save_path='reporte_completo_html.html'
    )

    print()
    print("=" * 80)
    print("REPORTE GENERADO EXITOSAMENTE")
    print("=" * 80)
    print()
    print(f"✓ Archivo HTML: {html_path}")
    print()
    print("El reporte incluye:")
    print("  • Propiedades del pilote y estratos de suelo")
    print("  • Caso de carga aplicado")
    print("  • Esquema visual del pilote con estratos y carga")
    print("  • Gráficos de resultados:")
    print("    - Deflexión lateral")
    print("    - Rotación")
    print("    - Momento flector")
    print("    - Fuerza cortante")
    print("    - Presión del suelo")
    print("  • Tabla de resultados principales")
    print()
    print("Abre el archivo HTML en tu navegador para visualizarlo.")
    print()


if __name__ == "__main__":
    main()
