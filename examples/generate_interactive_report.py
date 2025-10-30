"""
Genera reporte HTML interactivo con gráficos Plotly
Para la carga que produce deflexión de 25mm en cabeza
"""

import sys
sys.path.append('..')

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import base64
from src.pile_analysis.models import PileProperties, SoilLayer, SoilLayerNonlinear, LoadCase
from src.pile_analysis.lateral_load_algorithm import LateralLoadAnalysis
from src.pile_analysis.nonlinear_analysis import NonlinearLateralLoadAnalysis


def find_load_for_deflection(analysis, soil_layers, pile, target_deflection, is_nonlinear=False):
    """
    Encuentra la carga que produce una deflexión objetivo usando bisección
    """
    load_min = 0
    load_max = 2000e3  # 2000 kN
    tolerance = 0.1e-3  # 0.1 mm
    max_iterations = 30

    for iteration in range(max_iterations):
        load_mid = (load_min + load_max) / 2
        load_case = LoadCase(horizontal_load=load_mid, moment=0.0, free_head=True)

        if is_nonlinear:
            results = analysis.solve(load_case, max_iterations=30, tolerance=1e-4, relaxation=0.5)
        else:
            results = analysis.solve(load_case)

        deflection = results.head_deflection()

        if abs(deflection - target_deflection) < tolerance:
            return load_mid, results

        if deflection < target_deflection:
            load_min = load_mid
        else:
            load_max = load_mid

    # Si no converge, retornar el último resultado
    return load_mid, results


def read_load_deflection_data():
    """Lee los datos de la curva carga-deflexión del archivo"""
    try:
        with open('load_deflection_data.txt', 'r') as f:
            lines = f.readlines()

        loads = []
        deflections_linear = []
        deflections_nonlinear = []

        # Saltar el encabezado
        for line in lines:
            if line.strip().startswith('-') or not line.strip() or 'Carga' in line or '=' in line:
                continue
            if 'Pilote' in line or 'Modelo' in line:
                continue

            parts = line.split()
            if len(parts) >= 3:
                try:
                    loads.append(float(parts[0]))
                    deflections_linear.append(float(parts[1]))
                    deflections_nonlinear.append(float(parts[2]))
                except:
                    continue

        return np.array(loads), np.array(deflections_linear), np.array(deflections_nonlinear)
    except:
        return None, None, None


def generate_interactive_html_report(pile, soil_layers_linear, soil_layers_nonlinear,
                                    load_linear, results_linear,
                                    load_nonlinear, results_nonlinear,
                                    filename='interactive_report.html'):
    """Genera reporte HTML con gráficos interactivos usando Plotly"""

    # Leer datos de curva carga-deflexión
    loads_curve, def_lin_curve, def_nl_curve = read_load_deflection_data()

    # ========== CREAR GRÁFICOS INTERACTIVOS ==========

    # Gráfico 1: Curva carga-deflexión (del análisis previo)
    fig1 = go.Figure()

    if loads_curve is not None:
        fig1.add_trace(go.Scatter(
            x=def_lin_curve, y=loads_curve,
            mode='lines',
            name='Modelo Lineal',
            line=dict(color='blue', width=3),
            hovertemplate='Deflexión: %{x:.1f} mm<br>Carga: %{y:.0f} kN<extra></extra>'
        ))

        fig1.add_trace(go.Scatter(
            x=def_nl_curve, y=loads_curve,
            mode='lines',
            name='Modelo No Lineal',
            line=dict(color='red', width=3, dash='dash'),
            hovertemplate='Deflexión: %{x:.1f} mm<br>Carga: %{y:.0f} kN<extra></extra>'
        ))

        # Línea de 25mm
        fig1.add_vline(x=25, line_dash="dot", line_color="green",
                      annotation_text="Límite servicio (25mm)")

        # Marcar puntos de análisis actual
        fig1.add_trace(go.Scatter(
            x=[25], y=[load_linear/1e3],
            mode='markers',
            name=f'Análisis Lineal ({load_linear/1e3:.0f} kN)',
            marker=dict(color='blue', size=12, symbol='star')
        ))

        fig1.add_trace(go.Scatter(
            x=[25], y=[load_nonlinear/1e3],
            mode='markers',
            name=f'Análisis No Lineal ({load_nonlinear/1e3:.0f} kN)',
            marker=dict(color='red', size=12, symbol='star')
        ))

    fig1.update_layout(
        title='Curva Carga-Deflexión hasta la Falla',
        xaxis_title='Deflexión en cabeza (mm)',
        yaxis_title='Carga horizontal (kN)',
        hovermode='closest',
        template='plotly_white',
        height=500,
        font=dict(family='Arial', size=12)
    )

    # Gráfico 2: Deflexión lateral
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=results_linear.deflections * 1000, y=results_linear.depths,
        mode='lines',
        name='Lineal',
        line=dict(color='blue', width=3),
        hovertemplate='y: %{x:.2f} mm<br>z: %{y:.2f} m<extra></extra>'
    ))
    fig2.add_trace(go.Scatter(
        x=results_nonlinear.deflections * 1000, y=results_nonlinear.depths,
        mode='lines',
        name='No Lineal',
        line=dict(color='red', width=3, dash='dash'),
        hovertemplate='y: %{x:.2f} mm<br>z: %{y:.2f} m<extra></extra>'
    ))
    fig2.update_layout(
        title='Deflexión Lateral',
        xaxis_title='Deflexión (mm)',
        yaxis_title='Profundidad (m)',
        yaxis_autorange='reversed',
        hovermode='closest',
        template='plotly_white',
        height=600,
        font=dict(family='Arial', size=11)
    )

    # Gráfico 3: Rotación
    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(
        x=results_linear.rotations * 1000, y=results_linear.depths,
        mode='lines',
        name='Lineal',
        line=dict(color='blue', width=3),
        hovertemplate='θ: %{x:.3f} mrad<br>z: %{y:.2f} m<extra></extra>'
    ))
    fig3.add_trace(go.Scatter(
        x=results_nonlinear.rotations * 1000, y=results_nonlinear.depths,
        mode='lines',
        name='No Lineal',
        line=dict(color='red', width=3, dash='dash'),
        hovertemplate='θ: %{x:.3f} mrad<br>z: %{y:.2f} m<extra></extra>'
    ))
    fig3.update_layout(
        title='Rotación',
        xaxis_title='Rotación (mrad)',
        yaxis_title='Profundidad (m)',
        yaxis_autorange='reversed',
        hovermode='closest',
        template='plotly_white',
        height=600,
        font=dict(family='Arial', size=11)
    )

    # Gráfico 4: Momento flector
    fig4 = go.Figure()
    fig4.add_trace(go.Scatter(
        x=results_linear.moments / 1000, y=results_linear.depths,
        mode='lines',
        name='Lineal',
        line=dict(color='blue', width=3),
        hovertemplate='M: %{x:.1f} kN·m<br>z: %{y:.2f} m<extra></extra>'
    ))
    fig4.add_trace(go.Scatter(
        x=results_nonlinear.moments / 1000, y=results_nonlinear.depths,
        mode='lines',
        name='No Lineal',
        line=dict(color='red', width=3, dash='dash'),
        hovertemplate='M: %{x:.1f} kN·m<br>z: %{y:.2f} m<extra></extra>'
    ))
    M_max_lin, z_M_lin = results_linear.max_moment()
    M_max_nl, z_M_nl = results_nonlinear.max_moment()
    fig4.add_trace(go.Scatter(
        x=[M_max_lin/1000], y=[z_M_lin],
        mode='markers',
        name=f'M_max Lineal',
        marker=dict(color='blue', size=10, symbol='diamond')
    ))
    fig4.add_trace(go.Scatter(
        x=[M_max_nl/1000], y=[z_M_nl],
        mode='markers',
        name=f'M_max No Lineal',
        marker=dict(color='red', size=10, symbol='diamond')
    ))
    fig4.update_layout(
        title='Momento Flector',
        xaxis_title='Momento (kN·m)',
        yaxis_title='Profundidad (m)',
        yaxis_autorange='reversed',
        hovermode='closest',
        template='plotly_white',
        height=600,
        font=dict(family='Arial', size=11)
    )

    # Gráfico 5: Fuerza cortante
    fig5 = go.Figure()
    fig5.add_trace(go.Scatter(
        x=results_linear.shears / 1000, y=results_linear.depths,
        mode='lines',
        name='Lineal',
        line=dict(color='blue', width=3),
        hovertemplate='V: %{x:.1f} kN<br>z: %{y:.2f} m<extra></extra>'
    ))
    fig5.add_trace(go.Scatter(
        x=results_nonlinear.shears / 1000, y=results_nonlinear.depths,
        mode='lines',
        name='No Lineal',
        line=dict(color='red', width=3, dash='dash'),
        hovertemplate='V: %{x:.1f} kN<br>z: %{y:.2f} m<extra></extra>'
    ))
    fig5.update_layout(
        title='Fuerza Cortante',
        xaxis_title='Cortante (kN)',
        yaxis_title='Profundidad (m)',
        yaxis_autorange='reversed',
        hovermode='closest',
        template='plotly_white',
        height=600,
        font=dict(family='Arial', size=11)
    )

    # Gráfico 6: Presión del suelo
    fig6 = go.Figure()
    fig6.add_trace(go.Scatter(
        x=results_linear.soil_pressures / 1000, y=results_linear.depths,
        mode='lines',
        name='Lineal',
        line=dict(color='blue', width=3),
        hovertemplate='p: %{x:.1f} kN/m<br>z: %{y:.2f} m<extra></extra>'
    ))
    fig6.add_trace(go.Scatter(
        x=results_nonlinear.soil_pressures / 1000, y=results_nonlinear.depths,
        mode='lines',
        name='No Lineal',
        line=dict(color='red', width=3, dash='dash'),
        hovertemplate='p: %{x:.1f} kN/m<br>z: %{y:.2f} m<extra></extra>'
    ))
    fig6.update_layout(
        title='Presión del Suelo',
        xaxis_title='Presión (kN/m)',
        yaxis_title='Profundidad (m)',
        yaxis_autorange='reversed',
        hovermode='closest',
        template='plotly_white',
        height=600,
        font=dict(family='Arial', size=11)
    )

    # Gráfico 7: Rigidez k_h
    fig7 = go.Figure()
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

    fig7.add_trace(go.Scatter(
        x=k_h_linear / 1e6, y=results_linear.depths,
        mode='lines',
        name='Lineal (constante)',
        line=dict(color='blue', width=3),
        hovertemplate='k_h: %{x:.2f} MN/m³<br>z: %{y:.2f} m<extra></extra>'
    ))
    fig7.add_trace(go.Scatter(
        x=k_h_nonlinear / 1e6, y=results_nonlinear.depths,
        mode='lines',
        name='No Lineal (degradado)',
        line=dict(color='red', width=3, dash='dash'),
        hovertemplate='k_h: %{x:.2f} MN/m³<br>z: %{y:.2f} m<extra></extra>'
    ))
    fig7.update_layout(
        title='Rigidez del Suelo (k_h)',
        xaxis_title='k_h (MN/m³)',
        yaxis_title='Profundidad (m)',
        yaxis_autorange='reversed',
        hovermode='closest',
        template='plotly_white',
        height=600,
        font=dict(family='Arial', size=11)
    )

    # Calcular estadísticas
    y0_lin = results_linear.head_deflection() * 1000
    y0_nl = results_nonlinear.head_deflection() * 1000
    theta0_lin = results_linear.head_rotation() * 1000
    theta0_nl = results_nonlinear.head_rotation() * 1000
    p_max_lin = np.max(np.abs(results_linear.soil_pressures))
    p_max_nl = np.max(np.abs(results_nonlinear.soil_pressures))
    V_max_lin = np.max(results_linear.shears)
    V_max_nl = np.max(results_nonlinear.shears)

    # ========== GENERAR HTML ==========
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Reporte Interactivo - Análisis para Deflexión de 25mm</title>
    <script src="https://cdn.plot.ly/plotly-2.26.0.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            line-height: 1.6;
        }}

        .container {{
            max-width: 1600px;
            margin: 0 auto;
            background-color: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }}

        h1 {{
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 10px;
            color: #2d3748;
            border-bottom: 4px solid #667eea;
            padding-bottom: 15px;
        }}

        h2 {{
            font-size: 20px;
            font-weight: 600;
            margin-top: 40px;
            margin-bottom: 20px;
            color: #4a5568;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 12px 20px;
            border-radius: 5px;
        }}

        .subtitle {{
            font-size: 16px;
            color: #718096;
            margin-bottom: 30px;
            font-style: italic;
        }}

        .info-box {{
            background-color: #f7fafc;
            border-left: 4px solid #667eea;
            padding: 20px;
            margin: 20px 0;
            border-radius: 5px;
        }}

        .info-box pre {{
            font-family: 'Courier New', monospace;
            font-size: 13px;
            line-height: 1.8;
            color: #2d3748;
        }}

        .results-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}

        .results-table th {{
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 600;
        }}

        .results-table td {{
            padding: 12px 15px;
            border-bottom: 1px solid #e2e8f0;
        }}

        .results-table tr:hover {{
            background-color: #f7fafc;
        }}

        .graph-container {{
            margin: 30px 0;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}

        .graphs-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 30px;
            margin-top: 30px;
        }}

        .graph-full {{
            grid-column: 1 / -1;
        }}

        .highlight {{
            color: #667eea;
            font-weight: 600;
        }}

        .warning {{
            background-color: #fff5f5;
            border-left: 4px solid #f56565;
            padding: 15px;
            margin: 20px 0;
            border-radius: 5px;
        }}

        .note {{
            background-color: #fffff0;
            border-left: 4px solid #ecc94b;
            padding: 15px;
            margin: 20px 0;
            border-radius: 5px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Reporte Interactivo: Análisis Comparativo Lineal vs No Lineal</h1>
        <div class="subtitle">Análisis para deflexión de servicio de 25 mm en cabeza del pilote</div>

        <h2>1. Configuración del Análisis</h2>
        <div class="info-box">
            <pre><strong>PILOTE:</strong>
  Longitud                : {pile.length:.2f} m
  Diámetro                : {pile.diameter:.3f} m
  Módulo de Young         : {pile.elastic_modulus/1e9:.1f} GPa
  Momento de inercia      : {pile.moment_inertia:.6e} m⁴

<strong>ESTRATIGRAFÍA - MODELO LINEAL:</strong>
  Estrato 1               : z = {soil_layers_linear[0].depth_top:.1f} - {soil_layers_linear[0].depth_bottom:.1f} m
    k_h                   : {soil_layers_linear[0].k_h/1e6:.2f} MN/m³ (constante)
  Estrato 2               : z = {soil_layers_linear[1].depth_top:.1f} - {soil_layers_linear[1].depth_bottom:.1f} m
    k_h                   : {soil_layers_linear[1].k_h/1e6:.2f} MN/m³ (constante)
  Estrato 3               : z = {soil_layers_linear[2].depth_top:.1f} - {soil_layers_linear[2].depth_bottom:.1f} m
    k_h                   : {soil_layers_linear[2].k_h/1e6:.2f} MN/m³ (constante)

<strong>ESTRATIGRAFÍA - MODELO NO LINEAL (Duncan-Chang):</strong>
  Estrato 1               : z = {soil_layers_nonlinear[0].depth_top:.1f} - {soil_layers_nonlinear[0].depth_bottom:.1f} m
    k_h inicial           : {soil_layers_nonlinear[0].k_h_inicial/1e6:.2f} MN/m³
    p_ult                 : {soil_layers_nonlinear[0].p_ult/1e3:.1f} kN/m
  Estrato 2               : z = {soil_layers_nonlinear[1].depth_top:.1f} - {soil_layers_nonlinear[1].depth_bottom:.1f} m
    k_h inicial           : {soil_layers_nonlinear[1].k_h_inicial/1e6:.2f} MN/m³
    p_ult                 : {soil_layers_nonlinear[1].p_ult/1e3:.1f} kN/m
  Estrato 3               : z = {soil_layers_nonlinear[2].depth_top:.1f} - {soil_layers_nonlinear[2].depth_bottom:.1f} m
    k_h inicial           : {soil_layers_nonlinear[2].k_h_inicial/1e6:.2f} MN/m³
    p_ult                 : {soil_layers_nonlinear[2].p_ult/1e3:.1f} kN/m

<strong>MODELO CONSTITUTIVO NO LINEAL:</strong>
  Ecuación Duncan-Chang:
    k_h(y) = k_h_inicial / (1 + k_h_inicial × b × |y| / p_ult)

<strong>CRITERIO DE DISEÑO:</strong>
  Deflexión objetivo      : 25 mm (límite típico de servicio)</pre>
        </div>

        <h2>2. Cargas Aplicadas para Deflexión de 25 mm</h2>
        <table class="results-table">
            <thead>
                <tr>
                    <th>Modelo</th>
                    <th>Carga Horizontal (kN)</th>
                    <th>Deflexión en Cabeza (mm)</th>
                    <th>Observación</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td><strong>Modelo Lineal (Winkler)</strong></td>
                    <td>{load_linear/1e3:.1f}</td>
                    <td>{y0_lin:.2f}</td>
                    <td>k_h constante</td>
                </tr>
                <tr>
                    <td><strong>Modelo No Lineal (Duncan-Chang)</strong></td>
                    <td>{load_nonlinear/1e3:.1f}</td>
                    <td>{y0_nl:.2f}</td>
                    <td>k_h degrada con deflexión</td>
                </tr>
            </tbody>
        </table>

        <div class="warning">
            <strong>⚠ Diferencia de Carga:</strong> El modelo lineal requiere <strong>{((load_linear-load_nonlinear)/load_nonlinear*100):.1f}% MÁS</strong> carga
            que el modelo no lineal para alcanzar la misma deflexión de 25 mm. Esto significa que el modelo lineal <strong>SOBRESTIMA</strong>
            la capacidad del pilote.
        </div>

        <h2>3. Curva Carga-Deflexión Completa</h2>
        <div class="note">
            <strong>📊 Gráfico Interactivo:</strong> Pase el cursor sobre las curvas para ver valores exactos.
            Las estrellas marcan los puntos de análisis actual (25 mm de deflexión).
        </div>
        <div class="graph-container graph-full">
            <div id="graph1"></div>
        </div>

        <h2>4. Resultados Comparativos</h2>
        <table class="results-table">
            <thead>
                <tr>
                    <th>Parámetro</th>
                    <th>Modelo Lineal</th>
                    <th>Modelo No Lineal</th>
                    <th>Diferencia</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>Carga aplicada</td>
                    <td>{load_linear/1e3:.1f} kN</td>
                    <td>{load_nonlinear/1e3:.1f} kN</td>
                    <td class="highlight">{((load_linear-load_nonlinear)/load_nonlinear*100):+.1f}%</td>
                </tr>
                <tr>
                    <td>Deflexión en cabeza</td>
                    <td>{y0_lin:.2f} mm</td>
                    <td>{y0_nl:.2f} mm</td>
                    <td>{((y0_nl-y0_lin)/y0_lin*100):+.1f}%</td>
                </tr>
                <tr>
                    <td>Rotación en cabeza</td>
                    <td>{theta0_lin:.3f} mrad</td>
                    <td>{theta0_nl:.3f} mrad</td>
                    <td>{((theta0_nl-theta0_lin)/abs(theta0_lin)*100):+.1f}%</td>
                </tr>
                <tr>
                    <td>Momento máximo</td>
                    <td>{M_max_lin/1e3:.1f} kN·m</td>
                    <td>{M_max_nl/1e3:.1f} kN·m</td>
                    <td>{((M_max_nl-M_max_lin)/abs(M_max_lin)*100):+.1f}%</td>
                </tr>
                <tr>
                    <td>Profundidad momento máximo</td>
                    <td>{z_M_lin:.2f} m</td>
                    <td>{z_M_nl:.2f} m</td>
                    <td>-</td>
                </tr>
                <tr>
                    <td>Cortante máximo</td>
                    <td>{V_max_lin/1e3:.1f} kN</td>
                    <td>{V_max_nl/1e3:.1f} kN</td>
                    <td>-</td>
                </tr>
                <tr>
                    <td>Presión del suelo máxima</td>
                    <td>{p_max_lin/1e3:.1f} kN/m</td>
                    <td>{p_max_nl/1e3:.1f} kN/m</td>
                    <td>{((p_max_nl-p_max_lin)/p_max_lin*100):+.1f}%</td>
                </tr>
            </tbody>
        </table>

        <h2>5. Diagramas Comparativos Interactivos</h2>
        <div class="note">
            <strong>🖱 Interactividad:</strong> Haga clic en las leyendas para mostrar/ocultar curvas.
            Use zoom, pan y hover para explorar los datos en detalle.
        </div>

        <div class="graphs-grid">
            <div class="graph-container">
                <div id="graph2"></div>
            </div>
            <div class="graph-container">
                <div id="graph3"></div>
            </div>
            <div class="graph-container">
                <div id="graph4"></div>
            </div>
            <div class="graph-container">
                <div id="graph5"></div>
            </div>
            <div class="graph-container">
                <div id="graph6"></div>
            </div>
            <div class="graph-container">
                <div id="graph7"></div>
            </div>
        </div>

        <h2>6. Conclusiones</h2>
        <div class="info-box">
            <pre><strong>1. DIFERENCIA EN CARGA REQUERIDA:</strong>
   Para alcanzar la misma deflexión de 25 mm, el modelo lineal requiere
   {((load_linear-load_nonlinear)/load_nonlinear*100):.1f}% más carga que el modelo no lineal.

<strong>2. IMPLICACIONES PARA DISEÑO:</strong>
   • El modelo lineal (Winkler) SOBRESTIMA la capacidad del pilote
   • Usar modelo lineal puede llevar a diseños NO CONSERVADORES
   • Modelo no lineal (Duncan-Chang) más realista para cargas de servicio

<strong>3. DEGRADACIÓN DE RIGIDEZ:</strong>
   • En modelo no lineal: k_h disminuye con la deflexión
   • En modelo lineal: k_h permanece constante (irreal)
   • Ver gráfico de rigidez k_h para visualizar degradación

<strong>4. RECOMENDACIÓN:</strong>
   Utilizar modelo NO LINEAL para análisis de servicio cuando:
   - Deflexiones esperadas > 10-20 mm
   - Cargas laterales significativas
   - Diseño crítico donde precisión es importante</pre>
        </div>

    </div>

    <script>
        // Cargar gráficos interactivos
        var fig1_data = {fig1.to_json()};
        Plotly.newPlot('graph1', fig1_data.data, fig1_data.layout, {{responsive: true}});

        var fig2_data = {fig2.to_json()};
        Plotly.newPlot('graph2', fig2_data.data, fig2_data.layout, {{responsive: true}});

        var fig3_data = {fig3.to_json()};
        Plotly.newPlot('graph3', fig3_data.data, fig3_data.layout, {{responsive: true}});

        var fig4_data = {fig4.to_json()};
        Plotly.newPlot('graph4', fig4_data.data, fig4_data.layout, {{responsive: true}});

        var fig5_data = {fig5.to_json()};
        Plotly.newPlot('graph5', fig5_data.data, fig5_data.layout, {{responsive: true}});

        var fig6_data = {fig6.to_json()};
        Plotly.newPlot('graph6', fig6_data.data, fig6_data.layout, {{responsive: true}});

        var fig7_data = {fig7.to_json()};
        Plotly.newPlot('graph7', fig7_data.data, fig7_data.layout, {{responsive: true}});
    </script>
</body>
</html>"""

    # Guardar archivo HTML
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"  ✓ Reporte HTML interactivo generado: {filename}")


def main():
    print("=" * 80)
    print("REPORTE INTERACTIVO PARA DEFLEXIÓN DE 25 mm")
    print("=" * 80)
    print()

    # Propiedades del pilote
    pile = PileProperties.circular_pile(
        length=20.0,
        diameter=1.0,
        elastic_modulus=25e9
    )

    # Estratigrafía - Modelo Lineal
    soil_layers_linear = [
        SoilLayer.from_elastic_modulus(0.0, 5.0, 10e6, pile.diameter),
        SoilLayer.from_elastic_modulus(5.0, 10.0, 20e6, pile.diameter),
        SoilLayer.from_elastic_modulus(10.0, 20.0, 80e6, pile.diameter)
    ]

    # Estratigrafía - Modelo No Lineal
    soil_layers_nonlinear = [
        SoilLayerNonlinear.from_elastic_modulus(0.0, 5.0, 10e6, pile.diameter, ultimate_strain=0.02),
        SoilLayerNonlinear.from_elastic_modulus(5.0, 10.0, 20e6, pile.diameter, ultimate_strain=0.02),
        SoilLayerNonlinear.from_elastic_modulus(10.0, 20.0, 80e6, pile.diameter, ultimate_strain=0.02)
    ]

    # Crear objetos de análisis
    analysis_linear = LateralLoadAnalysis(
        pile=pile,
        soil_layers=soil_layers_linear,
        num_elements=100
    )

    analysis_nonlinear = NonlinearLateralLoadAnalysis(
        pile=pile,
        soil_layers=soil_layers_nonlinear,
        num_elements=100
    )

    print("BUSCANDO CARGAS PARA DEFLEXIÓN DE 25 mm:")
    print("-" * 80)

    # Encontrar carga para deflexión de 25mm - Modelo Lineal
    print("  Buscando carga para modelo lineal...")
    target_deflection = 0.025  # 25 mm
    load_linear, results_linear = find_load_for_deflection(
        analysis_linear, soil_layers_linear, pile, target_deflection, is_nonlinear=False
    )
    y_head_linear = results_linear.head_deflection() * 1000
    print(f"    ✓ Modelo lineal: {load_linear/1e3:.1f} kN → y = {y_head_linear:.2f} mm")

    # Encontrar carga para deflexión de 25mm - Modelo No Lineal
    print("  Buscando carga para modelo no lineal...")
    load_nonlinear, results_nonlinear = find_load_for_deflection(
        analysis_nonlinear, soil_layers_nonlinear, pile, target_deflection, is_nonlinear=True
    )
    y_head_nonlinear = results_nonlinear.head_deflection() * 1000
    print(f"    ✓ Modelo no lineal: {load_nonlinear/1e3:.1f} kN → y = {y_head_nonlinear:.2f} mm")

    print()
    print(f"  Diferencia en carga requerida: {((load_linear-load_nonlinear)/load_nonlinear*100):+.1f}%")
    print()

    # Generar reporte HTML interactivo
    print("GENERANDO REPORTE HTML INTERACTIVO:")
    print("-" * 80)
    generate_interactive_html_report(
        pile, soil_layers_linear, soil_layers_nonlinear,
        load_linear, results_linear,
        load_nonlinear, results_nonlinear,
        'interactive_report_25mm.html'
    )

    print()
    print("=" * 80)
    print("ANÁLISIS COMPLETADO")
    print("=" * 80)
    print()
    print("Archivos generados:")
    print("  • interactive_report_25mm.html - Reporte con gráficos interactivos")
    print()
    print("Para visualizar:")
    print("  Abra 'interactive_report_25mm.html' en su navegador web")


if __name__ == "__main__":
    main()
