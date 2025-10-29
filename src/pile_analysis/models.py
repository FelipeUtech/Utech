"""
Modelos de datos para el análisis de pilotes con carga lateral
"""

from dataclasses import dataclass
from typing import List
import numpy as np


@dataclass
class PileProperties:
    """
    Propiedades geométricas y materiales del pilote

    Attributes:
        length: Longitud total del pilote (m)
        diameter: Diámetro del pilote (m)
        elastic_modulus: Módulo de elasticidad del material (Pa)
        moment_inertia: Momento de inercia de la sección (m^4)
    """
    length: float
    diameter: float
    elastic_modulus: float
    moment_inertia: float

    def __post_init__(self):
        """Validar propiedades"""
        if self.length <= 0:
            raise ValueError("La longitud del pilote debe ser positiva")
        if self.diameter <= 0:
            raise ValueError("El diámetro del pilote debe ser positivo")
        if self.elastic_modulus <= 0:
            raise ValueError("El módulo de elasticidad debe ser positivo")
        if self.moment_inertia <= 0:
            raise ValueError("El momento de inercia debe ser positivo")

    @property
    def EI(self) -> float:
        """Rigidez flexural del pilote (N·m^2)"""
        return self.elastic_modulus * self.moment_inertia

    @classmethod
    def circular_pile(cls, length: float, diameter: float, elastic_modulus: float):
        """
        Crear un pilote circular con momento de inercia calculado

        Args:
            length: Longitud del pilote (m)
            diameter: Diámetro del pilote (m)
            elastic_modulus: Módulo de elasticidad (Pa)

        Returns:
            PileProperties con momento de inercia calculado para sección circular
        """
        moment_inertia = np.pi * diameter**4 / 64
        return cls(length, diameter, elastic_modulus, moment_inertia)

    @classmethod
    def square_pile(cls, length: float, side: float, elastic_modulus: float):
        """
        Crear un pilote cuadrado con momento de inercia calculado

        Args:
            length: Longitud del pilote (m)
            side: Lado del pilote cuadrado (m)
            elastic_modulus: Módulo de elasticidad (Pa)

        Returns:
            PileProperties con momento de inercia calculado para sección cuadrada
        """
        moment_inertia = side**4 / 12
        return cls(length, side, elastic_modulus, moment_inertia)


@dataclass
class SoilLayer:
    """
    Propiedades de un estrato de suelo

    Attributes:
        depth_top: Profundidad superior del estrato (m)
        depth_bottom: Profundidad inferior del estrato (m)
        k_h: Coeficiente de reacción horizontal del suelo (N/m^3)
    """
    depth_top: float
    depth_bottom: float
    k_h: float

    def __post_init__(self):
        """Validar propiedades"""
        if self.depth_bottom <= self.depth_top:
            raise ValueError("La profundidad inferior debe ser mayor que la superior")
        if self.k_h <= 0:
            raise ValueError("El coeficiente de reacción debe ser positivo")

    @property
    def thickness(self) -> float:
        """Espesor del estrato (m)"""
        return self.depth_bottom - self.depth_top

    def contains_depth(self, depth: float) -> bool:
        """Verificar si una profundidad está dentro de este estrato"""
        return self.depth_top <= depth < self.depth_bottom


@dataclass
class LoadCase:
    """
    Caso de carga aplicado en la cabeza del pilote

    Attributes:
        horizontal_load: Carga horizontal en la cabeza (N)
        moment: Momento aplicado en la cabeza (N·m)
        free_head: Si es True, cabeza libre de rotar; si es False, cabeza fija
    """
    horizontal_load: float = 0.0
    moment: float = 0.0
    free_head: bool = True


@dataclass
class AnalysisResults:
    """
    Resultados del análisis de pilote con carga lateral

    Attributes:
        depths: Array de profundidades (m)
        deflections: Array de deflexiones laterales (m)
        rotations: Array de rotaciones (rad)
        moments: Array de momentos flectores (N·m)
        shears: Array de fuerzas cortantes (N)
        soil_pressures: Array de presiones del suelo (N/m)
    """
    depths: np.ndarray
    deflections: np.ndarray
    rotations: np.ndarray
    moments: np.ndarray
    shears: np.ndarray
    soil_pressures: np.ndarray

    def max_deflection(self) -> tuple[float, float]:
        """
        Obtener la deflexión máxima y su profundidad

        Returns:
            Tupla (deflexión_máxima, profundidad)
        """
        idx = np.argmax(np.abs(self.deflections))
        return self.deflections[idx], self.depths[idx]

    def max_moment(self) -> tuple[float, float]:
        """
        Obtener el momento máximo y su profundidad

        Returns:
            Tupla (momento_máximo, profundidad)
        """
        idx = np.argmax(np.abs(self.moments))
        return self.moments[idx], self.depths[idx]

    def head_deflection(self) -> float:
        """Deflexión en la cabeza del pilote (m)"""
        return self.deflections[0]

    def head_rotation(self) -> float:
        """Rotación en la cabeza del pilote (rad)"""
        return self.rotations[0]

    def plot_results(self, save_path: str = None):
        """
        Graficar los resultados del análisis

        Args:
            save_path: Ruta para guardar la figura (opcional)
        """
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            print("Matplotlib no está instalado. No se pueden generar gráficos.")
            return

        fig, axes = plt.subplots(1, 4, figsize=(16, 8))

        # Deflexión
        axes[0].plot(self.deflections * 1000, self.depths, 'b-', linewidth=2)
        axes[0].set_xlabel('Deflexión (mm)', fontsize=12)
        axes[0].set_ylabel('Profundidad (m)', fontsize=12)
        axes[0].grid(True, alpha=0.3)
        axes[0].invert_yaxis()
        axes[0].set_title('Deflexión Lateral', fontsize=14, fontweight='bold')

        # Rotación
        axes[1].plot(self.rotations * 1000, self.depths, 'g-', linewidth=2)
        axes[1].set_xlabel('Rotación (mrad)', fontsize=12)
        axes[1].set_ylabel('Profundidad (m)', fontsize=12)
        axes[1].grid(True, alpha=0.3)
        axes[1].invert_yaxis()
        axes[1].set_title('Rotación', fontsize=14, fontweight='bold')

        # Momento
        axes[2].plot(self.moments / 1000, self.depths, 'r-', linewidth=2)
        axes[2].set_xlabel('Momento (kN·m)', fontsize=12)
        axes[2].set_ylabel('Profundidad (m)', fontsize=12)
        axes[2].grid(True, alpha=0.3)
        axes[2].invert_yaxis()
        axes[2].set_title('Momento Flector', fontsize=14, fontweight='bold')

        # Cortante
        axes[3].plot(self.shears / 1000, self.depths, 'm-', linewidth=2)
        axes[3].set_xlabel('Cortante (kN)', fontsize=12)
        axes[3].set_ylabel('Profundidad (m)', fontsize=12)
        axes[3].grid(True, alpha=0.3)
        axes[3].invert_yaxis()
        axes[3].set_title('Fuerza Cortante', fontsize=14, fontweight='bold')

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Gráfico guardado en: {save_path}")
        else:
            plt.show()
