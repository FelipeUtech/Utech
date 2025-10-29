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

    @classmethod
    def from_elastic_modulus(cls, depth_top: float, depth_bottom: float,
                            elastic_modulus: float, pile_diameter: float,
                            poisson_ratio: float = 0.3):
        """
        Crear un estrato de suelo a partir del módulo de Young (E)

        Convierte el módulo elástico del suelo a coeficiente de reacción horizontal
        usando la correlación: k_h = E_s / (1.5 * D * (1 - ν²))

        Args:
            depth_top: Profundidad superior del estrato (m)
            depth_bottom: Profundidad inferior del estrato (m)
            elastic_modulus: Módulo de Young del suelo (Pa)
            pile_diameter: Diámetro del pilote (m)
            poisson_ratio: Coeficiente de Poisson del suelo (adimensional, default=0.3)

        Returns:
            SoilLayer con k_h calculado desde E
        """
        # Correlación basada en teoría elástica
        k_h = elastic_modulus / (1.5 * pile_diameter * (1 - poisson_ratio**2))
        return cls(depth_top, depth_bottom, k_h)


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

    def generate_report(self, pile: 'PileProperties' = None, soil_layers: list = None,
                       load_case: 'LoadCase' = None, save_report_path: str = None,
                       save_plot_path: str = None, show_plot: bool = True):
        """
        Generar reporte completo del análisis con gráficos

        Args:
            pile: Propiedades del pilote (opcional, para incluir en reporte)
            soil_layers: Lista de estratos de suelo (opcional)
            load_case: Caso de carga aplicado (opcional)
            save_report_path: Ruta para guardar el reporte de texto (opcional)
            save_plot_path: Ruta para guardar los gráficos (opcional)
            show_plot: Si True, muestra los gráficos en pantalla (default: True)

        Returns:
            String con el reporte completo
        """
        # Construir reporte
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("REPORTE DE ANÁLISIS DE PILOTE CON CARGA LATERAL")
        report_lines.append("=" * 80)
        report_lines.append("")

        # Información del pilote
        if pile:
            report_lines.append("PROPIEDADES DEL PILOTE:")
            report_lines.append("-" * 80)
            report_lines.append(f"  Longitud (L):                {pile.length:.2f} m")
            report_lines.append(f"  Diámetro (D):                {pile.diameter:.2f} m")
            report_lines.append(f"  Módulo de elasticidad (E):   {pile.elastic_modulus/1e9:.2f} GPa")
            report_lines.append(f"  Momento de inercia (I):      {pile.moment_inertia:.6f} m⁴")
            report_lines.append(f"  Rigidez flexural (EI):       {pile.EI/1e6:.2f} MN·m²")
            report_lines.append("")

        # Información de estratos de suelo
        if soil_layers:
            report_lines.append("ESTRATOS DE SUELO:")
            report_lines.append("-" * 80)
            for i, layer in enumerate(soil_layers, 1):
                report_lines.append(f"  Estrato {i}:")
                report_lines.append(f"    Profundidad:  {layer.depth_top:.2f} - {layer.depth_bottom:.2f} m")
                report_lines.append(f"    Espesor:      {layer.thickness:.2f} m")
                report_lines.append(f"    k_h:          {layer.k_h/1e6:.2f} MN/m³")
            report_lines.append("")

        # Información de carga
        if load_case:
            report_lines.append("CASO DE CARGA:")
            report_lines.append("-" * 80)
            report_lines.append(f"  Carga horizontal (P):  {load_case.horizontal_load/1e3:.2f} kN")
            report_lines.append(f"  Momento (M):           {load_case.moment/1e3:.2f} kN·m")
            report_lines.append(f"  Condición de cabeza:   {'Libre' if load_case.free_head else 'Fija'}")
            report_lines.append("")

        # Resultados principales
        report_lines.append("RESULTADOS PRINCIPALES:")
        report_lines.append("=" * 80)
        report_lines.append("")

        # Deflexión en cabeza
        head_defl = self.head_deflection() * 1000  # mm
        report_lines.append(f"  Deflexión en cabeza del pilote:")
        report_lines.append(f"    y(0) = {head_defl:.3f} mm")
        report_lines.append("")

        # Rotación en cabeza
        head_rot = self.head_rotation() * 1000  # mrad
        report_lines.append(f"  Rotación en cabeza del pilote:")
        report_lines.append(f"    θ(0) = {head_rot:.3f} mrad")
        report_lines.append(f"    θ(0) = {np.degrees(self.head_rotation()):.4f}°")
        report_lines.append("")

        # Deflexión máxima
        max_defl, depth_max_defl = self.max_deflection()
        report_lines.append(f"  Deflexión máxima:")
        report_lines.append(f"    y_max = {max_defl * 1000:.3f} mm")
        report_lines.append(f"    Profundidad: {depth_max_defl:.2f} m")
        report_lines.append("")

        # Momento máximo
        max_mom, depth_max_mom = self.max_moment()
        report_lines.append(f"  Momento flector máximo:")
        report_lines.append(f"    M_max = {max_mom / 1e3:.2f} kN·m")
        report_lines.append(f"    Profundidad: {depth_max_mom:.2f} m")
        report_lines.append("")

        # Cortante máximo y mínimo
        max_shear = np.max(self.shears)
        min_shear = np.min(self.shears)
        idx_max_shear = np.argmax(self.shears)
        idx_min_shear = np.argmin(self.shears)
        report_lines.append(f"  Fuerza cortante:")
        report_lines.append(f"    V_max = {max_shear / 1e3:.2f} kN (a {self.depths[idx_max_shear]:.2f} m)")
        report_lines.append(f"    V_min = {min_shear / 1e3:.2f} kN (a {self.depths[idx_min_shear]:.2f} m)")
        report_lines.append("")

        # Presión del suelo máxima
        max_soil_press = np.max(np.abs(self.soil_pressures))
        idx_max_press = np.argmax(np.abs(self.soil_pressures))
        report_lines.append(f"  Presión del suelo máxima:")
        report_lines.append(f"    p_max = {max_soil_press / 1e3:.2f} kN/m")
        report_lines.append(f"    Profundidad: {self.depths[idx_max_press]:.2f} m")
        report_lines.append("")

        # Estadísticas adicionales
        report_lines.append("ESTADÍSTICAS ADICIONALES:")
        report_lines.append("-" * 80)

        # Punto de inflexión (donde momento cambia de signo)
        moment_signs = np.sign(self.moments)
        sign_changes = np.where(np.diff(moment_signs) != 0)[0]
        if len(sign_changes) > 0:
            report_lines.append(f"  Punto(s) de inflexión del momento:")
            for idx in sign_changes[:3]:  # Mostrar máximo 3
                report_lines.append(f"    z = {self.depths[idx]:.2f} m")
        else:
            report_lines.append(f"  Sin puntos de inflexión del momento")
        report_lines.append("")

        # Profundidad de penetración efectiva (donde deflexión < 1% de máxima)
        threshold = 0.01 * np.max(np.abs(self.deflections))
        effective_depths = self.depths[np.abs(self.deflections) > threshold]
        if len(effective_depths) > 0:
            penetration_depth = effective_depths[-1]
            report_lines.append(f"  Profundidad de penetración efectiva (y > 1% y_max):")
            report_lines.append(f"    L_eff = {penetration_depth:.2f} m")
            report_lines.append("")

        report_lines.append("=" * 80)
        report_lines.append("FIN DEL REPORTE")
        report_lines.append("=" * 80)

        # Unir líneas en string
        report_text = "\n".join(report_lines)

        # Guardar reporte si se especifica
        if save_report_path:
            with open(save_report_path, 'w', encoding='utf-8') as f:
                f.write(report_text)
            print(f"Reporte guardado en: {save_report_path}")

        # Generar y guardar/mostrar gráficos
        if save_plot_path or show_plot:
            try:
                import matplotlib.pyplot as plt

                fig, axes = plt.subplots(1, 4, figsize=(16, 8))

                # Deflexión
                axes[0].plot(self.deflections * 1000, self.depths, 'b-', linewidth=2)
                axes[0].set_xlabel('Deflexión (mm)', fontsize=12)
                axes[0].set_ylabel('Profundidad (m)', fontsize=12)
                axes[0].grid(True, alpha=0.3)
                axes[0].invert_yaxis()
                axes[0].set_title('Deflexión Lateral', fontsize=14, fontweight='bold')
                axes[0].axvline(0, color='k', linewidth=0.5)

                # Rotación
                axes[1].plot(self.rotations * 1000, self.depths, 'g-', linewidth=2)
                axes[1].set_xlabel('Rotación (mrad)', fontsize=12)
                axes[1].set_ylabel('Profundidad (m)', fontsize=12)
                axes[1].grid(True, alpha=0.3)
                axes[1].invert_yaxis()
                axes[1].set_title('Rotación', fontsize=14, fontweight='bold')
                axes[1].axvline(0, color='k', linewidth=0.5)

                # Momento
                axes[2].plot(self.moments / 1000, self.depths, 'r-', linewidth=2)
                axes[2].set_xlabel('Momento (kN·m)', fontsize=12)
                axes[2].set_ylabel('Profundidad (m)', fontsize=12)
                axes[2].grid(True, alpha=0.3)
                axes[2].invert_yaxis()
                axes[2].set_title('Momento Flector', fontsize=14, fontweight='bold')
                axes[2].axvline(0, color='k', linewidth=0.5)

                # Cortante
                axes[3].plot(self.shears / 1000, self.depths, 'm-', linewidth=2)
                axes[3].set_xlabel('Cortante (kN)', fontsize=12)
                axes[3].set_ylabel('Profundidad (m)', fontsize=12)
                axes[3].grid(True, alpha=0.3)
                axes[3].invert_yaxis()
                axes[3].set_title('Fuerza Cortante', fontsize=14, fontweight='bold')
                axes[3].axvline(0, color='k', linewidth=0.5)

                plt.tight_layout()

                if save_plot_path:
                    plt.savefig(save_plot_path, dpi=300, bbox_inches='tight')
                    print(f"Gráficos guardados en: {save_plot_path}")

                if show_plot:
                    plt.show()
                else:
                    plt.close()

            except ImportError:
                print("Matplotlib no está instalado. No se pueden generar gráficos.")

        return report_text
