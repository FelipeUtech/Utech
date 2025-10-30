"""
Análisis no lineal de pilotes con carga lateral usando modelo hiperbólico Duncan-Chang
"""

import numpy as np
from scipy.linalg import solve
from typing import List, Union
from .models import PileProperties, SoilLayerNonlinear, LoadCase, AnalysisResults


class NonlinearLateralLoadAnalysis:
    """
    Análisis no lineal de pilote con carga lateral usando modelo hiperbólico Duncan-Chang

    El modelo resuelve iterativamente la ecuación diferencial de cuarto orden:
    EI * d⁴y/dx⁴ + k_h(y) * b * y = 0

    donde k_h(y) varía con la deflexión según el modelo hiperbólico
    """

    def __init__(self, pile: PileProperties, soil_layers: List[SoilLayerNonlinear],
                 num_elements: int = 100):
        """
        Inicializar el análisis no lineal

        Args:
            pile: Propiedades del pilote
            soil_layers: Lista de estratos de suelo no lineales
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

    def _get_k_values(self, deflections: np.ndarray) -> np.ndarray:
        """
        Obtener el coeficiente de reacción k_h no lineal para cada profundidad

        Args:
            deflections: Array de deflexiones actuales

        Returns:
            Array con valores de k_h para cada nodo
        """
        k_values = np.zeros(len(self.depths))

        for i, depth in enumerate(self.depths):
            # Encontrar el estrato correspondiente
            for layer in self.soil_layers:
                if layer.contains_depth(depth) or abs(depth - layer.depth_bottom) < 1e-6:
                    k_values[i] = layer.get_k_h(deflections[i], self.pile.diameter)
                    break

        return k_values

    def _build_stiffness_matrix(self, k_values: np.ndarray) -> np.ndarray:
        """
        Construir la matriz de rigidez global usando diferencias finitas

        Args:
            k_values: Valores de k_h para cada nodo

        Returns:
            Matriz de rigidez global
        """
        n = len(self.depths)
        K = np.zeros((n, n))

        # Coeficientes de diferencias finitas para derivada de cuarto orden
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
            K[i, i] += k_values[i] * self.pile.diameter

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
        K[0, 0] = -self.pile.EI / dx3
        K[0, 1] = 3 * self.pile.EI / dx3
        K[0, 2] = -3 * self.pile.EI / dx3
        K[0, 3] = self.pile.EI / dx3
        F[0] = load.horizontal_load

        if load.free_head:
            # Cabeza libre: Momento en la cabeza = Momento aplicado
            K[1, 0] = self.pile.EI / dx2
            K[1, 1] = -2 * self.pile.EI / dx2
            K[1, 2] = self.pile.EI / dx2
            F[1] = load.moment
        else:
            # Cabeza fija: Rotación = 0
            K[1, 0] = -1.0 / dx
            K[1, 1] = 1.0 / dx
            F[1] = 0.0

    def solve(self, load: LoadCase, max_iterations: int = 20, tolerance: float = 1e-4,
              relaxation: float = 0.5) -> AnalysisResults:
        """
        Resolver el análisis no lineal iterativamente

        Args:
            load: Caso de carga a aplicar
            max_iterations: Número máximo de iteraciones
            tolerance: Tolerancia para convergencia (metros)
            relaxation: Factor de relajación (0 < relaxation <= 1)

        Returns:
            Resultados del análisis
        """
        n = len(self.depths)

        # Inicializar con deflexiones pequeñas (estimación lineal)
        deflections = np.zeros(n)

        print(f"Iniciando análisis no lineal (max iter: {max_iterations}, tol: {tolerance*1000:.3f} mm)")

        for iteration in range(max_iterations):
            # Obtener k_values actualizados basados en deflexiones actuales
            k_values = self._get_k_values(deflections)

            # Construir matriz de rigidez con k_values actuales
            K = self._build_stiffness_matrix(k_values)

            # Vector de fuerzas
            F = np.zeros(n)

            # Aplicar condiciones de frontera
            self._apply_boundary_conditions(K, F, load)

            # Resolver sistema de ecuaciones K*y = F
            try:
                deflections_new = solve(K, F)
            except np.linalg.LinAlgError:
                raise RuntimeError("Error al resolver el sistema de ecuaciones no lineal.")

            # Calcular cambio en deflexiones
            delta = np.max(np.abs(deflections_new - deflections))

            # Aplicar relajación para mejorar convergencia
            deflections = deflections + relaxation * (deflections_new - deflections)

            # Criterio de convergencia
            if delta < tolerance:
                print(f"  ✓ Convergencia alcanzada en iteración {iteration + 1}")
                print(f"    Cambio máximo: {delta*1000:.4f} mm")
                break

            if iteration % 5 == 0 or iteration == max_iterations - 1:
                print(f"  Iteración {iteration + 1}: cambio = {delta*1000:.4f} mm")
        else:
            print(f"  ⚠ Máximo de iteraciones alcanzado. Cambio final: {delta*1000:.4f} mm")

        # Calcular derivadas usando diferencias finitas
        rotations = self._compute_rotations(deflections)
        moments = self._compute_moments(deflections)
        shears = self._compute_shears(deflections, load)

        # Calcular presiones del suelo con el modelo no lineal
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
        """Calcular rotaciones a partir de deflexiones"""
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
        """Calcular momentos flectores a partir de deflexiones"""
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
        """Calcular fuerzas cortantes usando ecuación de equilibrio"""
        n = len(deflections)
        shears = np.zeros(n)
        dx = self.delta_x
        b = self.pile.diameter

        # Condición de frontera en la cabeza
        shears[0] = load.horizontal_load

        # Integrar hacia abajo: dV/dz = -k(z)*b*y(z)
        for i in range(n - 1):
            # Obtener k_h para cada nodo
            k_i = self._get_soil_layer_k(self.depths[i], deflections[i])
            k_ip1 = self._get_soil_layer_k(self.depths[i + 1], deflections[i + 1])

            # Reacción del suelo promedio
            soil_reaction_i = k_i * b * deflections[i]
            soil_reaction_ip1 = k_ip1 * b * deflections[i + 1]
            avg_reaction = (soil_reaction_i + soil_reaction_ip1) / 2.0

            # Actualizar cortante
            shears[i + 1] = shears[i] - avg_reaction * dx

        return shears

    def _get_soil_layer_k(self, depth: float, deflection: float) -> float:
        """Obtener k_h del estrato correspondiente"""
        for layer in self.soil_layers:
            if layer.contains_depth(depth) or abs(depth - layer.depth_bottom) < 1e-6:
                return layer.get_k_h(deflection, self.pile.diameter)
        return 0.0

    def _compute_soil_pressures(self, deflections: np.ndarray) -> np.ndarray:
        """Calcular presiones del suelo con modelo no lineal"""
        pressures = np.zeros_like(deflections)

        for i, (depth, y) in enumerate(zip(self.depths, deflections)):
            for layer in self.soil_layers:
                if layer.contains_depth(depth) or abs(depth - layer.depth_bottom) < 1e-6:
                    pressures[i] = layer.get_pressure(y, self.pile.diameter)
                    break

        return pressures
