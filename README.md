# Algoritmo de Análisis de Pilote con Carga Lateral

Este proyecto implementa un algoritmo para resolver el problema de pilotes embebidos en suelo estratificado (n capas) sometidos a carga lateral, utilizando el modelo de fundación de Winkler.

## Descripción del Problema

El problema consiste en analizar la respuesta de un pilote vertical embebido en un suelo estratificado cuando se somete a cargas laterales (horizontales) y momentos en la cabeza. El suelo se modela mediante el método de Winkler, donde la reacción del suelo es proporcional a la deflexión del pilote a través de resortes independientes.

## Fundamento Teórico

La ecuación diferencial que gobierna el comportamiento del pilote es:

```
EI * d⁴y/dx⁴ + kh(x) * b * y = 0
```

Donde:
- `y`: Deflexión lateral del pilote
- `x`: Profundidad desde la superficie
- `E`: Módulo de elasticidad del material del pilote
- `I`: Momento de inercia de la sección transversal
- `kh(x)`: Coeficiente de reacción del suelo (varía con la profundidad y estrato)
- `b`: Diámetro o ancho del pilote

## Método de Solución

El algoritmo utiliza el **método de diferencias finitas** para:
1. Discretizar el pilote en elementos
2. Convertir la ecuación diferencial en un sistema de ecuaciones lineales
3. Aplicar condiciones de frontera (cargas en cabeza, empotramiento al final)
4. Resolver el sistema para obtener: deflexiones, rotaciones, momentos y cortantes

## Características

- Soporte para múltiples estratos de suelo
- Propiedades variables del suelo por estrato (módulo de reacción)
- Condiciones de frontera configurables
- Cálculo de:
  - Deflexiones laterales
  - Rotaciones
  - Momentos flectores
  - Fuerzas cortantes
  - Presiones del suelo

## Instalación

```bash
pip install -r requirements.txt
```

## Uso Básico

```python
from src.pile_analysis.models import PileProperties, SoilLayer, LoadCase
from src.pile_analysis.lateral_load_algorithm import LateralLoadAnalysis

# Definir propiedades del pilote
pile = PileProperties(
    length=20.0,          # metros
    diameter=1.0,         # metros
    elastic_modulus=25e9, # Pa (25 GPa para concreto)
    moment_inertia=0.049  # m^4 (circular)
)

# Definir estratos de suelo
soil_layers = [
    SoilLayer(depth_top=0.0, depth_bottom=5.0, k_h=10e6),   # Arena
    SoilLayer(depth_top=5.0, depth_bottom=15.0, k_h=5e6),   # Arcilla
    SoilLayer(depth_top=15.0, depth_bottom=20.0, k_h=15e6)  # Roca
]

# Definir cargas
load = LoadCase(
    horizontal_load=100e3,  # N (100 kN)
    moment=50e3             # N·m (50 kN·m)
)

# Crear y ejecutar análisis
analysis = LateralLoadAnalysis(
    pile=pile,
    soil_layers=soil_layers,
    num_elements=100
)

results = analysis.solve(load)

# Acceder a resultados
print(f"Deflexión en cabeza: {results.deflections[0]:.6f} m")
print(f"Momento máximo: {max(abs(results.moments)):.2f} N·m")
```

## Estructura del Proyecto

```
Utech/
├── src/
│   └── pile_analysis/
│       ├── __init__.py
│       ├── models.py                    # Clases de datos
│       └── lateral_load_algorithm.py    # Algoritmo principal
├── examples/
│   └── example_basic.py                 # Ejemplo de uso
├── README.md
└── requirements.txt
```

## Referencias

- Reese, L. C., & Van Impe, W. F. (2001). Single Piles and Pile Groups Under Lateral Loading
- Broms, B. B. (1964). Lateral Resistance of Piles in Cohesive Soils
- Poulos, H. G., & Davis, E. H. (1980). Pile Foundation Analysis and Design

## Licencia

MIT License
