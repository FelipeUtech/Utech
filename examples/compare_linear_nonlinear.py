"""
Comparación de análisis lineal vs no lineal (Modelo Duncan-Chang)

Compara el comportamiento del pilote usando:
1. Modelo lineal (Winkler): k_h constante
2. Modelo no lineal (Duncan-Chang): k_h degrada con deflexión
"""

import sys
sys.path.append('..')

import numpy as np
import matplotlib.pyplot as plt
import base64
from io import BytesIO
from src.pile_analysis.models import PileProperties, SoilLayer, SoilLayerNonlinear, LoadCase
from src.pile_analysis.lateral_load_algorithm import LateralLoadAnalysis
from src.pile_analysis.nonlinear_analysis import NonlinearLateralLoadAnalysis


def main():
    print("=" * 80)
    print("COMPARACIÓN: ANÁLISIS LINEAL vs NO LINEAL (DUNCAN-CHANG)")
    print("=" * 80)
    print()

    # Propiedades del pilote
    pile = PileProperties.circular_pile(
        length=20.0,
        diameter=1.0,
        elastic_modulus=25e9
    )

    # Caso de carga
    load = LoadCase(
        horizontal_load=1000e3,  # 1000 kN
        moment=0.0,
        free_head=True
    )

    print("CONFIGURACIÓN DEL ANÁLISIS:")
    print("-" * 80)
    print(f"  Pilote: L={pile.length}m, D={pile.diameter}m, E={pile.elastic_modulus/1e9}GPa")
    print(f"  Carga: P={load.horizontal_load/1e3}kN, M={load.moment/1e3}kN·m")
    print()

    # ========== MODELO LINEAL ==========
    print("1. ANÁLISIS LINEAL (Winkler - k_h constante)")
    print("-" * 80)

    soil_layers_linear = [
        SoilLayer.from_elastic_modulus(0.0, 5.0, 10e6, pile.diameter),
        SoilLayer.from_elastic_modulus(5.0, 10.0, 20e6, pile.diameter),
        SoilLayer.from_elastic_modulus(10.0, 20.0, 80e6, pile.diameter)
    ]

    for i, layer in enumerate(soil_layers_linear, 1):
        print(f"  Estrato {i}: k_h = {layer.k_h/1e6:.2f} MN/m³ (constante)")

    analysis_linear = LateralLoadAnalysis(
        pile=pile,
        soil_layers=soil_layers_linear,
        num_elements=100
    )

    print("  Ejecutando análisis lineal...")
    results_linear = analysis_linear.solve(load)
    print("  ✓ Análisis lineal completado")
    print()

    # ========== MODELO NO LINEAL ==========
    print("2. ANÁLISIS NO LINEAL (Duncan-Chang - k_h variable)")
    print("-" * 80)

    soil_layers_nonlinear = [
        SoilLayerNonlinear.from_elastic_modulus(0.0, 5.0, 10e6, pile.diameter, ultimate_strain=0.02),
        SoilLayerNonlinear.from_elastic_modulus(5.0, 10.0, 20e6, pile.diameter, ultimate_strain=0.02),
        SoilLayerNonlinear.from_elastic_modulus(10.0, 20.0, 80e6, pile.diameter, ultimate_strain=0.02)
    ]

    for i, layer in enumerate(soil_layers_nonlinear, 1):
        print(f"  Estrato {i}: k_h_inicial = {layer.k_h_inicial/1e6:.2f} MN/m³")
        print(f"            p_ult = {layer.p_ult/1e3:.0f} kN/m")

    analysis_nonlinear = NonlinearLateralLoadAnalysis(
        pile=pile,
        soil_layers=soil_layers_nonlinear,
        num_elements=100
    )

    print()
    results_nonlinear = analysis_nonlinear.solve(load, max_iterations=20, tolerance=1e-4)
    print()

    # ========== COMPARACIÓN DE RESULTADOS ==========
    print("=" * 80)
    print("COMPARACIÓN DE RESULTADOS")
    print("=" * 80)
    print()

    print(f"{'Parámetro':<35} {'Lineal':<15} {'No Lineal':<15} {'Diferencia'}")
    print("-" * 80)

    # Deflexión en cabeza
    y0_lin = results_linear.head_deflection() * 1000
    y0_nl = results_nonlinear.head_deflection() * 1000
    diff_y0 = ((y0_nl - y0_lin) / y0_lin) * 100
    print(f"{'Deflexión en cabeza (mm)':<35} {y0_lin:>14.3f} {y0_nl:>14.3f} {diff_y0:>+10.1f}%")

    # Rotación en cabeza
    theta0_lin = results_linear.head_rotation() * 1000
    theta0_nl = results_nonlinear.head_rotation() * 1000
    diff_theta = ((theta0_nl - theta0_lin) / abs(theta0_lin)) * 100
    print(f"{'Rotación en cabeza (mrad)':<35} {theta0_lin:>14.3f} {theta0_nl:>14.3f} {diff_theta:>+10.1f}%")

    # Momento máximo
    M_max_lin, z_M_lin = results_linear.max_moment()
    M_max_nl, z_M_nl = results_nonlinear.max_moment()
    diff_M = ((M_max_nl - M_max_lin) / abs(M_max_lin)) * 100
    print(f"{'Momento máximo (kN·m)':<35} {M_max_lin/1e3:>14.2f} {M_max_nl/1e3:>14.2f} {diff_M:>+10.1f}%")
    print(f"{'  Profundidad (m)':<35} {z_M_lin:>14.2f} {z_M_nl:>14.2f}")

    # Cortante máximo
    V_max_lin = np.max(results_linear.shears)
    V_max_nl = np.max(results_nonlinear.shears)
    print(f"{'Cortante máximo (kN)':<35} {V_max_lin/1e3:>14.2f} {V_max_nl/1e3:>14.2f}")

    # Presión del suelo máxima
    p_max_lin = np.max(np.abs(results_linear.soil_pressures))
    p_max_nl = np.max(np.abs(results_nonlinear.soil_pressures))
    diff_p = ((p_max_nl - p_max_lin) / p_max_lin) * 100
    print(f"{'Presión del suelo máxima (kN/m)':<35} {p_max_lin/1e3:>14.2f} {p_max_nl/1e3:>14.2f} {diff_p:>+10.1f}%")

    print()
    print("Observación:")
    if diff_y0 > 0:
        print(f"  • El modelo no lineal predice deflexiones {abs(diff_y0):.1f}% MAYORES")
        print(f"    (La rigidez efectiva del suelo disminuye con la deflexión)")
    else:
        print(f"  • El modelo no lineal predice deflexiones {abs(diff_y0):.1f}% MENORES")

    print()

    # ========== GRÁFICOS COMPARATIVOS ==========
    print("Generando gráficos comparativos...")

    fig, axes = plt.subplots(2, 3, figsize=(18, 12))

    # Deflexión
    axes[0,0].plot(results_linear.deflections * 1000, results_linear.depths,
                   'b-', linewidth=2.5, label='Lineal')
    axes[0,0].plot(results_nonlinear.deflections * 1000, results_nonlinear.depths,
                   'r--', linewidth=2.5, label='No Lineal (Duncan-Chang)')
    axes[0,0].set_xlabel('Deflexión, y (mm)', fontsize=11)
    axes[0,0].set_ylabel('Profundidad, z (m)', fontsize=11)
    axes[0,0].grid(True, alpha=0.3, linestyle='--')
    axes[0,0].invert_yaxis()
    axes[0,0].set_title('(a) Deflexión Lateral', fontsize=12, fontweight='bold')
    axes[0,0].legend(fontsize=10)
    axes[0,0].axvline(0, color='k', linewidth=0.5, alpha=0.3)

    # Rotación
    axes[0,1].plot(results_linear.rotations * 1000, results_linear.depths,
                   'b-', linewidth=2.5, label='Lineal')
    axes[0,1].plot(results_nonlinear.rotations * 1000, results_nonlinear.depths,
                   'r--', linewidth=2.5, label='No Lineal')
    axes[0,1].set_xlabel('Rotación, θ (mrad)', fontsize=11)
    axes[0,1].set_ylabel('Profundidad, z (m)', fontsize=11)
    axes[0,1].grid(True, alpha=0.3, linestyle='--')
    axes[0,1].invert_yaxis()
    axes[0,1].set_title('(b) Rotación', fontsize=12, fontweight='bold')
    axes[0,1].legend(fontsize=10)
    axes[0,1].axvline(0, color='k', linewidth=0.5, alpha=0.3)

    # Momento
    axes[0,2].plot(results_linear.moments / 1000, results_linear.depths,
                   'b-', linewidth=2.5, label='Lineal')
    axes[0,2].plot(results_nonlinear.moments / 1000, results_nonlinear.depths,
                   'r--', linewidth=2.5, label='No Lineal')
    axes[0,2].set_xlabel('Momento, M (kN·m)', fontsize=11)
    axes[0,2].set_ylabel('Profundidad, z (m)', fontsize=11)
    axes[0,2].grid(True, alpha=0.3, linestyle='--')
    axes[0,2].invert_yaxis()
    axes[0,2].set_title('(c) Momento Flector', fontsize=12, fontweight='bold')
    axes[0,2].legend(fontsize=10)
    axes[0,2].axvline(0, color='k', linewidth=0.5, alpha=0.3)

    # Cortante
    axes[1,0].plot(results_linear.shears / 1000, results_linear.depths,
                   'b-', linewidth=2.5, label='Lineal')
    axes[1,0].plot(results_nonlinear.shears / 1000, results_nonlinear.depths,
                   'r--', linewidth=2.5, label='No Lineal')
    axes[1,0].set_xlabel('Cortante, V (kN)', fontsize=11)
    axes[1,0].set_ylabel('Profundidad, z (m)', fontsize=11)
    axes[1,0].grid(True, alpha=0.3, linestyle='--')
    axes[1,0].invert_yaxis()
    axes[1,0].set_title('(d) Fuerza Cortante', fontsize=12, fontweight='bold')
    axes[1,0].legend(fontsize=10)
    axes[1,0].axvline(0, color='k', linewidth=0.5, alpha=0.3)

    # Presión del suelo
    axes[1,1].plot(results_linear.soil_pressures / 1000, results_linear.depths,
                   'b-', linewidth=2.5, label='Lineal')
    axes[1,1].plot(results_nonlinear.soil_pressures / 1000, results_nonlinear.depths,
                   'r--', linewidth=2.5, label='No Lineal')
    axes[1,1].set_xlabel('Presión del suelo, p (kN/m)', fontsize=11)
    axes[1,1].set_ylabel('Profundidad, z (m)', fontsize=11)
    axes[1,1].grid(True, alpha=0.3, linestyle='--')
    axes[1,1].invert_yaxis()
    axes[1,1].set_title('(e) Presión del Suelo', fontsize=12, fontweight='bold')
    axes[1,1].legend(fontsize=10)
    axes[1,1].axvline(0, color='k', linewidth=0.5, alpha=0.3)

    # Curva k_h vs profundidad
    k_h_linear = np.array([soil_layers_linear[0].k_h] * len(results_linear.depths))
    k_h_nonlinear = np.zeros_like(results_nonlinear.deflections)
    for i, (depth, y) in enumerate(zip(results_nonlinear.depths, results_nonlinear.deflections)):
        for layer in soil_layers_nonlinear:
            if layer.contains_depth(depth) or abs(depth - layer.depth_bottom) < 1e-6:
                k_h_nonlinear[i] = layer.get_k_h(y, pile.diameter)
                break

    # Ajustar k_h_linear para mostrar los diferentes estratos
    for i, depth in enumerate(results_linear.depths):
        for layer in soil_layers_linear:
            if layer.contains_depth(depth) or abs(depth - layer.depth_bottom) < 1e-6:
                k_h_linear[i] = layer.k_h
                break

    axes[1,2].plot(k_h_linear / 1e6, results_linear.depths,
                   'b-', linewidth=2.5, label='Lineal (constante)')
    axes[1,2].plot(k_h_nonlinear / 1e6, results_nonlinear.depths,
                   'r--', linewidth=2.5, label='No Lineal (degradado)')
    axes[1,2].set_xlabel('Rigidez, k_h (MN/m³)', fontsize=11)
    axes[1,2].set_ylabel('Profundidad, z (m)', fontsize=11)
    axes[1,2].grid(True, alpha=0.3, linestyle='--')
    axes[1,2].invert_yaxis()
    axes[1,2].set_title('(f) Rigidez del Suelo', fontsize=12, fontweight='bold')
    axes[1,2].legend(fontsize=10)

    plt.tight_layout()
    plt.savefig('comparison_linear_nonlinear.png', dpi=300, bbox_inches='tight')
    print("  ✓ Gráfico guardado: comparison_linear_nonlinear.png")
    print()

    # ========== GENERAR REPORTE HTML ==========
    print("Generando reporte HTML...")
    generate_html_report(pile, load, soil_layers_linear, soil_layers_nonlinear,
                        results_linear, results_nonlinear, 'comparison_report.html')
    print()


def generate_html_report(pile, load, soil_layers_linear, soil_layers_nonlinear,
                        results_linear, results_nonlinear, filename='comparison_report.html'):
    """Genera reporte HTML comparativo con formato sobrio tipo programación"""

    def fig_to_base64(fig):
        """Convierte figura de matplotlib a string base64"""
        buf = BytesIO()
        fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        img_str = base64.b64encode(buf.read()).decode()
        plt.close(fig)
        return img_str

    # Calcular estadísticas
    y0_lin = results_linear.head_deflection() * 1000
    y0_nl = results_nonlinear.head_deflection() * 1000
    theta0_lin = results_linear.head_rotation() * 1000
    theta0_nl = results_nonlinear.head_rotation() * 1000
    M_max_lin, z_M_lin = results_linear.max_moment()
    M_max_nl, z_M_nl = results_nonlinear.max_moment()
    V_max_lin = np.max(results_linear.shears)
    V_max_nl = np.max(results_nonlinear.shears)
    p_max_lin = np.max(np.abs(results_linear.soil_pressures))
    p_max_nl = np.max(np.abs(results_nonlinear.soil_pressures))

    # ========== GENERAR GRÁFICOS INDIVIDUALES ==========

    # Gráfico 1: Deflexión
    fig1, ax1 = plt.subplots(figsize=(4, 8))
    ax1.plot(results_linear.deflections * 1000, results_linear.depths,
             'b-', linewidth=2, label='Lineal')
    ax1.plot(results_nonlinear.deflections * 1000, results_nonlinear.depths,
             'r--', linewidth=2, label='No Lineal')
    ax1.set_xlabel('Deflexión (mm)', fontsize=10)
    ax1.set_ylabel('Profundidad (m)', fontsize=10)
    ax1.grid(True, alpha=0.3)
    ax1.invert_yaxis()
    ax1.legend(fontsize=9)
    ax1.axvline(0, color='k', linewidth=0.5, alpha=0.3)
    img1 = fig_to_base64(fig1)

    # Gráfico 2: Rotación
    fig2, ax2 = plt.subplots(figsize=(4, 8))
    ax2.plot(results_linear.rotations * 1000, results_linear.depths,
             'b-', linewidth=2, label='Lineal')
    ax2.plot(results_nonlinear.rotations * 1000, results_nonlinear.depths,
             'r--', linewidth=2, label='No Lineal')
    ax2.set_xlabel('Rotación (mrad)', fontsize=10)
    ax2.set_ylabel('Profundidad (m)', fontsize=10)
    ax2.grid(True, alpha=0.3)
    ax2.invert_yaxis()
    ax2.legend(fontsize=9)
    ax2.axvline(0, color='k', linewidth=0.5, alpha=0.3)
    img2 = fig_to_base64(fig2)

    # Gráfico 3: Momento
    fig3, ax3 = plt.subplots(figsize=(4, 8))
    ax3.plot(results_linear.moments / 1000, results_linear.depths,
             'b-', linewidth=2, label='Lineal')
    ax3.plot(results_nonlinear.moments / 1000, results_nonlinear.depths,
             'r--', linewidth=2, label='No Lineal')
    ax3.set_xlabel('Momento (kN·m)', fontsize=10)
    ax3.set_ylabel('Profundidad (m)', fontsize=10)
    ax3.grid(True, alpha=0.3)
    ax3.invert_yaxis()
    ax3.legend(fontsize=9)
    ax3.axvline(0, color='k', linewidth=0.5, alpha=0.3)
    img3 = fig_to_base64(fig3)

    # Gráfico 4: Cortante
    fig4, ax4 = plt.subplots(figsize=(4, 8))
    ax4.plot(results_linear.shears / 1000, results_linear.depths,
             'b-', linewidth=2, label='Lineal')
    ax4.plot(results_nonlinear.shears / 1000, results_nonlinear.depths,
             'r--', linewidth=2, label='No Lineal')
    ax4.set_xlabel('Cortante (kN)', fontsize=10)
    ax4.set_ylabel('Profundidad (m)', fontsize=10)
    ax4.grid(True, alpha=0.3)
    ax4.invert_yaxis()
    ax4.legend(fontsize=9)
    ax4.axvline(0, color='k', linewidth=0.5, alpha=0.3)
    img4 = fig_to_base64(fig4)

    # Gráfico 5: Presión del suelo
    fig5, ax5 = plt.subplots(figsize=(4, 8))
    ax5.plot(results_linear.soil_pressures / 1000, results_linear.depths,
             'b-', linewidth=2, label='Lineal')
    ax5.plot(results_nonlinear.soil_pressures / 1000, results_nonlinear.depths,
             'r--', linewidth=2, label='No Lineal')
    ax5.set_xlabel('Presión (kN/m)', fontsize=10)
    ax5.set_ylabel('Profundidad (m)', fontsize=10)
    ax5.grid(True, alpha=0.3)
    ax5.invert_yaxis()
    ax5.legend(fontsize=9)
    ax5.axvline(0, color='k', linewidth=0.5, alpha=0.3)
    img5 = fig_to_base64(fig5)

    # Gráfico 6: Rigidez k_h
    fig6, ax6 = plt.subplots(figsize=(4, 8))
    k_h_linear = np.zeros_like(results_linear.depths)
    k_h_nonlinear = np.zeros_like(results_nonlinear.depths)

    for i, depth in enumerate(results_linear.depths):
        for layer in soil_layers_linear:
            if layer.contains_depth(depth) or abs(depth - layer.depth_bottom) < 1e-6:
                k_h_linear[i] = layer.k_h
                break

    for i, (depth, y) in enumerate(zip(results_nonlinear.depths, results_nonlinear.deflections)):
        for layer in soil_layers_nonlinear:
            if layer.contains_depth(depth) or abs(depth - layer.depth_bottom) < 1e-6:
                k_h_nonlinear[i] = layer.get_k_h(y, pile.diameter)
                break

    ax6.plot(k_h_linear / 1e6, results_linear.depths,
             'b-', linewidth=2, label='Lineal')
    ax6.plot(k_h_nonlinear / 1e6, results_nonlinear.depths,
             'r--', linewidth=2, label='No Lineal')
    ax6.set_xlabel('k_h (MN/m³)', fontsize=10)
    ax6.set_ylabel('Profundidad (m)', fontsize=10)
    ax6.grid(True, alpha=0.3)
    ax6.invert_yaxis()
    ax6.legend(fontsize=9)
    img6 = fig_to_base64(fig6)

    # ========== GENERAR HTML ==========
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Reporte Comparativo - Análisis Lineal vs No Lineal</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Courier New', Consolas, monospace;
            background-color: #0d1117;
            color: #c9d1d9;
            padding: 20px;
            line-height: 1.5;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background-color: #161b22;
            padding: 30px;
            border: 1px solid #30363d;
        }}

        h1 {{
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 20px;
            color: #58a6ff;
            border-bottom: 2px solid #30363d;
            padding-bottom: 10px;
        }}

        h2 {{
            font-size: 14px;
            font-weight: bold;
            margin-top: 30px;
            margin-bottom: 15px;
            color: #79c0ff;
        }}

        pre {{
            background-color: #0d1117;
            padding: 15px;
            border: 1px solid #30363d;
            overflow-x: auto;
            font-size: 12px;
            margin-bottom: 20px;
        }}

        .section {{
            margin-bottom: 30px;
        }}

        .graphs {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            margin-top: 20px;
        }}

        .graph-item {{
            text-align: center;
        }}

        .graph-item img {{
            width: 100%;
            height: auto;
            border: 1px solid #30363d;
        }}

        .graph-caption {{
            font-size: 11px;
            color: #8b949e;
            margin-top: 8px;
        }}

        .highlight {{
            color: #ffa657;
        }}

        .success {{
            color: #56d364;
        }}

        .error {{
            color: #f85149;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>REPORTE COMPARATIVO: ANALISIS LINEAL vs NO LINEAL (DUNCAN-CHANG)</h1>

        <div class="section">
            <h2>[1] DATOS DE ENTRADA</h2>
            <pre>PILOTE:
  Longitud                : {pile.length:.2f} m
  Diametro                : {pile.diameter:.3f} m
  Modulo de Young         : {pile.elastic_modulus/1e9:.1f} GPa
  Momento de inercia      : {pile.moment_inertia:.6e} m^4

CARGA:
  Fuerza horizontal       : {load.horizontal_load/1e3:.1f} kN
  Momento en cabeza       : {load.moment/1e3:.1f} kN·m
  Condicion de borde      : {'Cabeza libre' if load.free_head else 'Cabeza fija'}

ESTRATIGRAFIA - MODELO LINEAL (k_h constante):
  Estrato 1               : z = {soil_layers_linear[0].depth_top:.1f} - {soil_layers_linear[0].depth_bottom:.1f} m
    k_h                   : {soil_layers_linear[0].k_h/1e6:.2f} MN/m^3
  Estrato 2               : z = {soil_layers_linear[1].depth_top:.1f} - {soil_layers_linear[1].depth_bottom:.1f} m
    k_h                   : {soil_layers_linear[1].k_h/1e6:.2f} MN/m^3
  Estrato 3               : z = {soil_layers_linear[2].depth_top:.1f} - {soil_layers_linear[2].depth_bottom:.1f} m
    k_h                   : {soil_layers_linear[2].k_h/1e6:.2f} MN/m^3

ESTRATIGRAFIA - MODELO NO LINEAL (Duncan-Chang, k_h degradado):
  Estrato 1               : z = {soil_layers_nonlinear[0].depth_top:.1f} - {soil_layers_nonlinear[0].depth_bottom:.1f} m
    k_h_inicial           : {soil_layers_nonlinear[0].k_h_inicial/1e6:.2f} MN/m^3
    p_ult                 : {soil_layers_nonlinear[0].p_ult/1e3:.1f} kN/m
  Estrato 2               : z = {soil_layers_nonlinear[1].depth_top:.1f} - {soil_layers_nonlinear[1].depth_bottom:.1f} m
    k_h_inicial           : {soil_layers_nonlinear[1].k_h_inicial/1e6:.2f} MN/m^3
    p_ult                 : {soil_layers_nonlinear[1].p_ult/1e3:.1f} kN/m
  Estrato 3               : z = {soil_layers_nonlinear[2].depth_top:.1f} - {soil_layers_nonlinear[2].depth_bottom:.1f} m
    k_h_inicial           : {soil_layers_nonlinear[2].k_h_inicial/1e6:.2f} MN/m^3
    p_ult                 : {soil_layers_nonlinear[2].p_ult/1e3:.1f} kN/m

MODELO CONSTITUTIVO NO LINEAL:
  Ecuacion Duncan-Chang:
    k_h(y) = k_h_inicial / (1 + k_h_inicial * b * |y| / p_ult)

  Donde:
    y      = deflexion lateral
    b      = diametro del pilote
    p_ult  = presion ultima del suelo</pre>
        </div>

        <div class="section">
            <h2>[2] RESULTADOS DE ANALISIS</h2>
            <pre>PARAMETRO                          LINEAL         NO LINEAL      DIFERENCIA
================================================================================
Deflexion en cabeza (mm)           {y0_lin:>10.3f}     {y0_nl:>10.3f}     {((y0_nl-y0_lin)/y0_lin*100):>+9.1f}%
Rotacion en cabeza (mrad)          {theta0_lin:>10.3f}     {theta0_nl:>10.3f}     {((theta0_nl-theta0_lin)/abs(theta0_lin)*100):>+9.1f}%
Momento maximo (kN·m)              {M_max_lin/1e3:>10.2f}     {M_max_nl/1e3:>10.2f}     {((M_max_nl-M_max_lin)/abs(M_max_lin)*100):>+9.1f}%
  Profundidad (m)                  {z_M_lin:>10.2f}     {z_M_nl:>10.2f}
Cortante maximo (kN)               {V_max_lin/1e3:>10.2f}     {V_max_nl/1e3:>10.2f}
Presion suelo maxima (kN/m)        {p_max_lin/1e3:>10.2f}     {p_max_nl/1e3:>10.2f}     {((p_max_nl-p_max_lin)/p_max_lin*100):>+9.1f}%</pre>
        </div>

        <div class="section">
            <h2>[3] OBSERVACIONES</h2>
            <pre>• El modelo NO LINEAL predice deflexiones {((y0_nl-y0_lin)/y0_lin*100):.1f}% MAYORES que el modelo lineal.

• Causa: La rigidez k_h del suelo DISMINUYE con la deflexion en el modelo Duncan-Chang,
  mientras que permanece CONSTANTE en el modelo de Winkler.

• Implicaciones:
  - Modelo lineal (Winkler): SUBESTIMA deflexiones para cargas grandes
  - Modelo no lineal (Duncan-Chang): Mas REALISTA para comportamiento del suelo

• Degradacion de rigidez:
  - k_h_efectiva < k_h_inicial cuando y > 0
  - La rigidez efectiva depende del nivel de deformacion</pre>
        </div>

        <div class="section">
            <h2>[4] GRAFICOS COMPARATIVOS</h2>
            <div class="graphs">
                <div class="graph-item">
                    <img src="data:image/png;base64,{img1}" alt="Deflexión">
                    <div class="graph-caption">Fig. 1 - Deflexion lateral</div>
                </div>
                <div class="graph-item">
                    <img src="data:image/png;base64,{img2}" alt="Rotación">
                    <div class="graph-caption">Fig. 2 - Rotacion</div>
                </div>
                <div class="graph-item">
                    <img src="data:image/png;base64,{img3}" alt="Momento">
                    <div class="graph-caption">Fig. 3 - Momento flector</div>
                </div>
                <div class="graph-item">
                    <img src="data:image/png;base64,{img4}" alt="Cortante">
                    <div class="graph-caption">Fig. 4 - Fuerza cortante</div>
                </div>
                <div class="graph-item">
                    <img src="data:image/png;base64,{img5}" alt="Presión">
                    <div class="graph-caption">Fig. 5 - Presion del suelo</div>
                </div>
                <div class="graph-item">
                    <img src="data:image/png;base64,{img6}" alt="Rigidez">
                    <div class="graph-caption">Fig. 6 - Rigidez del suelo (k_h)</div>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>[5] CONCLUSIONES</h2>
            <pre>1. DIFERENCIAS SIGNIFICATIVAS:
   El modelo no lineal predice respuestas sustancialmente diferentes al modelo lineal,
   especialmente en terminos de deflexiones ({((y0_nl-y0_lin)/y0_lin*100):+.1f}%).

2. APLICABILIDAD:
   - Modelo LINEAL: Valido para cargas pequeñas (comportamiento elastico)
   - Modelo NO LINEAL: Necesario para cargas grandes (degradacion de rigidez)

3. RECOMENDACION:
   Para diseño conservador, utilizar modelo no lineal cuando las deflexiones
   esperadas sean significativas (> 10-20 mm tipicamente).

4. VERIFICACION:
   Ambos modelos convergen para deflexiones muy pequeñas donde k_h ≈ k_h_inicial.</pre>
        </div>

    </div>
</body>
</html>"""

    # Guardar archivo HTML
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"  ✓ Reporte HTML generado: {filename}")


if __name__ == "__main__":
    main()
