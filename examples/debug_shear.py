"""
Script para diagnosticar el problema de discontinuidad en el cortante
"""

import sys
sys.path.append('..')

from src.pile_analysis.models import PileProperties, SoilLayer, LoadCase
from src.pile_analysis.lateral_load_algorithm import LateralLoadAnalysis

# Configurar análisis simple
pile = PileProperties.circular_pile(
    length=20.0,
    diameter=1.0,
    elastic_modulus=25e9
)

soil_layers = [
    SoilLayer.from_elastic_modulus(
        depth_top=0.0,
        depth_bottom=20.0,
        elastic_modulus=20e6,
        pile_diameter=pile.diameter
    )
]

load = LoadCase(horizontal_load=1000e3, moment=0.0, free_head=True)

analysis = LateralLoadAnalysis(pile=pile, soil_layers=soil_layers, num_elements=100)
results = analysis.solve(load)

# Mostrar primeros y últimos 5 valores de cortante
print("Primeros 10 nodos:")
print("Nodo | Profundidad (m) | Cortante (kN)")
print("-" * 50)
for i in range(10):
    print(f"{i:4d} | {results.depths[i]:15.3f} | {results.shears[i]/1e3:12.2f}")

print("\nÚltimos 10 nodos:")
print("Nodo | Profundidad (m) | Cortante (kN)")
print("-" * 50)
for i in range(len(results.depths)-10, len(results.depths)):
    print(f"{i:4d} | {results.depths[i]:15.3f} | {results.shears[i]/1e3:12.2f}")

# Calcular diferencias entre nodos consecutivos
print("\nDiferencias entre nodos consecutivos (primeros 10):")
print("Nodo | Delta V (kN)")
print("-" * 30)
for i in range(9):
    delta = (results.shears[i+1] - results.shears[i]) / 1e3
    print(f"{i:4d} | {delta:12.2f}")

print("\nDiferencias entre nodos consecutivos (últimos 10):")
print("Nodo | Delta V (kN)")
print("-" * 30)
for i in range(len(results.depths)-10, len(results.depths)-1):
    delta = (results.shears[i+1] - results.shears[i]) / 1e3
    print(f"{i:4d} | {delta:12.2f}")
