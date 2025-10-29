"""
Algoritmo de análisis de pilote con carga lateral usando el modelo de Winkler
Método de diferencias finitas para ecuación diferencial de cuarto orden
"""

import numpy as np
from scipy.linalg import solve
from typing import List
from .models import PileProperties, SoilLayer, LoadCase, AnalysisResults


class LateralLoadAnalysis:
    """
    Análisis de pilote sometido a carga lateral usando el modelo de Winkler

    El modelo resuelve la ecuación diferencial de cuarto orden:
    EI * d⁴y/dx⁴ + k(x) * b * y = 0

    Usando el método de diferencias finitas para discretizar el problema.
    """

    def __init__(self, pile: PileProperties, soil_layers: List[SoilLayer], num_elements: int = 100):
        """
        Inicializar el análisis

        Args:
            pile: Propiedades del pilote
            soil_layers: Lista de estratos de suelo
            num_elements: Número de elementos para discretización
        """
        self.pile = pile
        self.soil_layers = sorted(soil_layers, key=lambda x: x.depth_top)
        self.num_elements = num_elements

        # Validar estratos
        self._validate_soil_layers()

        # Discretizar el pilote
        self.depths = np.linspace(0, pile.length, num_elements + 1)
        self.delta_x = pile.length / num_elements

        # Obtener módulos de reacción para cada profundidad
        self.k_values = self._get_k_values()

    def _validate_soil_layers(self):
        """Validar que los estratos de suelo cubran toda la longitud del pilote"""
        if not self.soil_layers:
            raise ValueError("Debe proporcionar al menos un estrato de suelo")

        # Verificar que los estratos estén contiguos
        for i in range(len(self.soil_layers) - 1):
            if abs(self.soil_layers[i].depth_bottom - self.soil_layers[i + 1].depth_top) > 1e-6:
                raise ValueError(f"Los estratos {i} y {i+1} no son contiguos")

        # Verificar que cubran toda la longitud
        if self.soil_layers[0].depth_top > 1e-6:
            raise ValueError("El primer estrato debe comenzar en profundidad 0")

        if self.soil_layers[-1].depth_bottom < self.pile.length - 1e-6:
            raise ValueError("Los estratos deben cubrir toda la longitud del pilote")

    def _get_k_values(self) -> np.ndarray:
        """
        Obtener el coeficiente de reacción k_h para cada profundidad

        Returns:
            Array con valores de k_h para cada nodo
        """
        k_values = np.zeros(len(self.depths))

        for i, depth in enumerate(self.depths):
            # Encontrar el estrato correspondiente
            for layer in self.soil_layers:
                if layer.contains_depth(depth) or abs(depth - layer.depth_bottom) < 1e-6:
                    k_values[i] = layer.k_h
                    break

        return k_values

    def _build_stiffness_matrix(self) -> np.ndarray:
        """
        Construir la matriz de rigidez global usando diferencias finitas

        La ecuación diferencial: EI * d⁴y/dx⁴ + k*b*y = 0
        Se discretiza usando diferencias finitas centradas

        Returns:
            Matriz de rigidez global
        """
        n = len(self.depths)
        K = np.zeros((n, n))

        # Coeficientes de diferencias finitas para derivada de cuarto orden
        # d⁴y/dx⁴ ≈ (yi-2 - 4*yi-1 + 6*yi - 4*yi+1 + yi+2) / dx⁴
        dx4 = self.delta_x ** 4
        EI = self.pile.EI

        # Nodos internos (aplicar ecuación diferencial)
        for i in range(2, n - 2):
            # Término de rigidez del pilote (d⁴y/dx⁴)
            K[i, i - 2] += EI / dx4
            K[i, i - 1] += -4 * EI / dx4
            K[i, i] += 6 * EI / dx4
            K[i, i + 1] += -4 * EI / dx4
            K[i, i + 2] += EI / dx4

            # Término de reacción del suelo (k*b*y)
            K[i, i] += self.k_values[i] * self.pile.diameter

        # Condiciones de frontera en la cabeza (nodo 0)
        # Se aplican después según el caso de carga

        # Condiciones de frontera en la punta (empotramiento ficticio)
        # Nodo n-1: deflexión = 0
        K[n - 1, n - 1] = 1.0

        # Nodo n-2: rotación = 0 (dy/dx ≈ (yi+1 - yi-1) / 2dx = 0)
        K[n - 2, n - 3] = -1.0 / (2 * self.delta_x)
        K[n - 2, n - 1] = 1.0 / (2 * self.delta_x)

        return K

    def _apply_boundary_conditions(self, K: np.ndarray, F: np.ndarray, load: LoadCase):
        """
        Aplicar condiciones de frontera en la cabeza del pilote

        Args:
            K: Matriz de rigidez
            F: Vector de fuerzas
            load: Caso de carga
        """
        dx = self.delta_x
        dx2 = dx ** 2
        dx3 = dx ** 3

        # Nodo 0: Cortante en la cabeza = Carga aplicada
        # V = -EI * d³y/dx³ = P (carga horizontal aplicada)
        # d³y/dx³ ≈ (-yi+3 + 3*yi+2 - 3*yi+1 + yi) / dx³
        K[0, 0] = -self.pile.EI / dx3
        K[0, 1] = 3 * self.pile.EI / dx3
        K[0, 2] = -3 * self.pile.EI / dx3
        K[0, 3] = self.pile.EI / dx3
        F[0] = load.horizontal_load

        if load.free_head:
            # Cabeza libre: Momento en la cabeza = Momento aplicado
            # M = -EI * d²y/dx² = M_aplicado
            # d²y/dx² ≈ (yi+2 - 2*yi+1 + yi) / dx²
            K[1, 0] = self.pile.EI / dx2
            K[1, 1] = -2 * self.pile.EI / dx2
            K[1, 2] = self.pile.EI / dx2
            F[1] = load.moment
        else:
            # Cabeza fija: Rotación = 0
            # dy/dx ≈ (yi+1 - yi-1) / 2dx = 0
            # Usamos forward difference: (yi+1 - yi) / dx = 0
            K[1, 0] = -1.0 / dx
            K[1, 1] = 1.0 / dx
            F[1] = 0.0

    def solve(self, load: LoadCase) -> AnalysisResults:
        """
        Resolver el análisis de carga lateral

        Args:
            load: Caso de carga a aplicar

        Returns:
            Resultados del análisis
        """
        n = len(self.depths)

        # Construir matriz de rigidez
        K = self._build_stiffness_matrix()

        # Vector de fuerzas
        F = np.zeros(n)

        # Aplicar condiciones de frontera
        self._apply_boundary_conditions(K, F, load)

        # Resolver sistema de ecuaciones K*y = F
        try:
            deflections = solve(K, F)
        except np.linalg.LinAlgError:
            raise RuntimeError("Error al resolver el sistema de ecuaciones. "
                               "Verifique las propiedades del pilote y del suelo.")

        # Calcular derivadas usando diferencias finitas
        rotations = self._compute_rotations(deflections)
        moments = self._compute_moments(deflections)
        shears = self._compute_shears(deflections, load)
        soil_pressures = self._compute_soil_pressures(deflections)

        return AnalysisResults(
            depths=self.depths.copy(),
            deflections=deflections,
            rotations=rotations,
            moments=moments,
            shears=shears,
            soil_pressures=soil_pressures
        )

    def _compute_rotations(self, deflections: np.ndarray) -> np.ndarray:
        """
        Calcular rotaciones a partir de deflexiones
        Rotación = dy/dx

        Args:
            deflections: Array de deflexiones

        Returns:
            Array de rotaciones (rad)
        """
        rotations = np.zeros_like(deflections)
        dx = self.delta_x

        # Diferencia centrada para puntos internos
        for i in range(1, len(deflections) - 1):
            rotations[i] = (deflections[i + 1] - deflections[i - 1]) / (2 * dx)

        # Diferencia hacia adelante para el primer punto
        rotations[0] = (-deflections[2] + 4 * deflections[1] - 3 * deflections[0]) / (2 * dx)

        # Diferencia hacia atrás para el último punto
        n = len(deflections)
        rotations[n - 1] = (3 * deflections[n - 1] - 4 * deflections[n - 2] + deflections[n - 3]) / (2 * dx)

        return rotations

    def _compute_moments(self, deflections: np.ndarray) -> np.ndarray:
        """
        Calcular momentos flectores a partir de deflexiones
        Momento = -EI * d²y/dx²

        Args:
            deflections: Array de deflexiones

        Returns:
            Array de momentos (N·m)
        """
        moments = np.zeros_like(deflections)
        dx = self.delta_x
        dx2 = dx ** 2
        EI = self.pile.EI

        # Diferencia centrada para puntos internos
        for i in range(1, len(deflections) - 1):
            d2y_dx2 = (deflections[i + 1] - 2 * deflections[i] + deflections[i - 1]) / dx2
            moments[i] = -EI * d2y_dx2

        # Extremos usando diferencias de segundo orden
        moments[0] = -EI * (2 * deflections[0] - 5 * deflections[1] +
                            4 * deflections[2] - deflections[3]) / dx2

        n = len(deflections)
        moments[n - 1] = -EI * (2 * deflections[n - 1] - 5 * deflections[n - 2] +
                                4 * deflections[n - 3] - deflections[n - 4]) / dx2

        return moments

    def _compute_shears(self, deflections: np.ndarray, load: LoadCase) -> np.ndarray:
        """
        Calcular fuerzas cortantes usando la ecuación de equilibrio

        Usa la relación: dV/dz = -k(z) * b * y(z)
        Integrando desde la cabeza hacia la punta con condición inicial V(0) = P

        Este método asegura continuidad en el diagrama de cortante.

        Args:
            deflections: Array de deflexiones
            load: Caso de carga (para condición de frontera en cabeza)

        Returns:
            Array de cortantes (N)
        """
        n = len(deflections)
        shears = np.zeros(n)
        dx = self.delta_x
        b = self.pile.diameter

        # Condición de frontera en la cabeza
        shears[0] = load.horizontal_load

        # Integrar hacia abajo usando la ecuación de equilibrio: dV/dz = -k*b*y
        # Usando el método del trapecio para mayor precisión
        for i in range(n - 1):
            # Reacción del suelo en el segmento
            soil_reaction_i = self.k_values[i] * b * deflections[i]
            soil_reaction_ip1 = self.k_values[i + 1] * b * deflections[i + 1]

            # Método del trapecio: promedio de reacciones en ambos extremos
            avg_reaction = (soil_reaction_i + soil_reaction_ip1) / 2.0

            # Actualizar cortante: V[i+1] = V[i] - avg_reaction * dx
            shears[i + 1] = shears[i] - avg_reaction * dx

        return shears

    def _compute_soil_pressures(self, deflections: np.ndarray) -> np.ndarray:
        """
        Calcular presiones del suelo a partir de deflexiones
        Presión = k * b * y

        Args:
            deflections: Array de deflexiones

        Returns:
            Array de presiones del suelo (N/m)
        """
        return self.k_values * self.pile.diameter * deflections

    def get_pile_capacity(self, max_deflection_limit: float = 0.025) -> float:
        """
        Estimar la capacidad del pilote basada en un límite de deflexión

        Args:
            max_deflection_limit: Deflexión máxima permitida en la cabeza (m)

        Returns:
            Carga lateral máxima estimada (N)
        """
        # Análisis con carga unitaria
        unit_load = LoadCase(horizontal_load=1000.0, moment=0.0)
        results = self.solve(unit_load)

        # Factor de escala basado en deflexión límite
        head_deflection = abs(results.head_deflection())
        scale_factor = max_deflection_limit / head_deflection

        return unit_load.horizontal_load * scale_factor

    def parametric_study(self, load_range: np.ndarray) -> List[AnalysisResults]:
        """
        Realizar un estudio paramétrico variando la carga

        Args:
            load_range: Array de valores de carga horizontal a analizar (N)

        Returns:
            Lista de resultados para cada carga
        """
        results_list = []

        for load_value in load_range:
            load_case = LoadCase(horizontal_load=load_value, moment=0.0)
            result = self.solve(load_case)
            results_list.append(result)

        return results_list
