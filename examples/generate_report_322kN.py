"""
Genera reporte HTML interactivo con gráficos Plotly
Para una carga fija de 322 kN aplicada a ambos modelos
"""

import sys
sys.path.append('..')

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
from src.pile_analysis.models import PileProperties, SoilLayer, SoilLayerNonlinear, LoadCase
from src.pile_analysis.lateral_load_algorithm import LateralLoadAnalysis
from src.pile_analysis.nonlinear_analysis import NonlinearLateralLoadAnalysis


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
                                    load_applied, results_linear, results_nonlinear,
                                    filename='interactive_report.html'):
    """Genera reporte HTML con gráficos interactivos usando Plotly"""

    # Leer datos de curva carga-deflexión
    loads_curve, def_lin_curve, def_nl_curve = read_load_deflection_data()

    # ========== CREAR GRÁFICOS INTERACTIVOS ==========
    # Proporciones: ancho x alto (píxeles)
    graph_width = 500
    graph_height = 800

    # Obtener deflexiones para marcar en curva P-y
    y_lin_load = results_linear.head_deflection() * 1000
    y_nl_load = results_nonlinear.head_deflection() * 1000

    # Gráfico 1: Curva carga-deflexión (más ancho, horizontal)
    fig1_data = []
    fig1_layout = {}

    if loads_curve is not None:
        fig1_data = [
            {
                'x': def_lin_curve.tolist(),
                'y': loads_curve.tolist(),
                'mode': 'lines',
                'name': 'Modelo Lineal',
                'line': {'color': 'blue', 'width': 3},
                'hovertemplate': 'Deflexión: %{x:.1f} mm<br>Carga: %{y:.0f} kN<extra></extra>'
            },
            {
                'x': def_nl_curve.tolist(),
                'y': loads_curve.tolist(),
                'mode': 'lines',
                'name': 'Modelo No Lineal',
                'line': {'color': 'red', 'width': 3, 'dash': 'dash'},
                'hovertemplate': 'Deflexión: %{x:.1f} mm<br>Carga: %{y:.0f} kN<extra></extra>'
            },
            {
                'x': [y_lin_load],
                'y': [load_applied/1e3],
                'mode': 'markers',
                'name': f'Lineal ({y_lin_load:.1f} mm)',
                'marker': {'color': 'blue', 'size': 12, 'symbol': 'star'}
            },
            {
                'x': [y_nl_load],
                'y': [load_applied/1e3],
                'mode': 'markers',
                'name': f'No Lineal ({y_nl_load:.1f} mm)',
                'marker': {'color': 'red', 'size': 12, 'symbol': 'star'}
            }
        ]

        fig1_layout = {
            'title': 'Curva Carga-Deflexión hasta la Falla',
            'xaxis': {'title': 'Deflexión en cabeza (mm)'},
            'yaxis': {'title': 'Carga horizontal (kN)'},
            'hovermode': 'closest',
            'template': 'plotly_white',
            'width': 1000,
            'height': 600,
            'font': {'family': 'Arial', 'size': 12},
            'shapes': [{
                'type': 'line',
                'x0': 0, 'x1': max(def_nl_curve),
                'y0': load_applied/1e3, 'y1': load_applied/1e3,
                'line': {'color': 'green', 'width': 2, 'dash': 'dot'}
            }],
            'annotations': [{
                'x': max(def_nl_curve) * 0.7, 'y': load_applied/1e3 + 50,
                'text': f'Carga aplicada: {load_applied/1e3:.0f} kN',
                'showarrow': False,
                'font': {'color': 'green', 'size': 11}
            }]
        }

    # Gráfico 2: Deflexión lateral
    fig2_data = [
        {
            'x': (results_linear.deflections * 1000).tolist(),
            'y': results_linear.depths.tolist(),
            'mode': 'lines',
            'name': 'Lineal',
            'line': {'color': 'blue', 'width': 3},
            'hovertemplate': 'y: %{x:.2f} mm<br>z: %{y:.2f} m<extra></extra>'
        },
        {
            'x': (results_nonlinear.deflections * 1000).tolist(),
            'y': results_nonlinear.depths.tolist(),
            'mode': 'lines',
            'name': 'No Lineal',
            'line': {'color': 'red', 'width': 3, 'dash': 'dash'},
            'hovertemplate': 'y: %{x:.2f} mm<br>z: %{y:.2f} m<extra></extra>'
        }
    ]
    fig2_layout = {
        'title': 'Deflexión Lateral',
        'xaxis': {'title': 'Deflexión (mm)'},
        'yaxis': {'title': 'Profundidad (m)', 'autorange': 'reversed'},
        'hovermode': 'closest',
        'template': 'plotly_white',
        'width': graph_width,
        'height': graph_height,
        'font': {'family': 'Arial', 'size': 11}
    }

    # Gráfico 3: Rotación
    fig3_data = [
        {
            'x': (results_linear.rotations * 1000).tolist(),
            'y': results_linear.depths.tolist(),
            'mode': 'lines',
            'name': 'Lineal',
            'line': {'color': 'blue', 'width': 3},
            'hovertemplate': 'θ: %{x:.3f} mrad<br>z: %{y:.2f} m<extra></extra>'
        },
        {
            'x': (results_nonlinear.rotations * 1000).tolist(),
            'y': results_nonlinear.depths.tolist(),
            'mode': 'lines',
            'name': 'No Lineal',
            'line': {'color': 'red', 'width': 3, 'dash': 'dash'},
            'hovertemplate': 'θ: %{x:.3f} mrad<br>z: %{y:.2f} m<extra></extra>'
        }
    ]
    fig3_layout = {
        'title': 'Rotación',
        'xaxis': {'title': 'Rotación (mrad)'},
        'yaxis': {'title': 'Profundidad (m)', 'autorange': 'reversed'},
        'hovermode': 'closest',
        'template': 'plotly_white',
        'width': graph_width,
        'height': graph_height,
        'font': {'family': 'Arial', 'size': 11}
    }

    # Gráfico 4: Momento flector
    M_max_lin, z_M_lin = results_linear.max_moment()
    M_max_nl, z_M_nl = results_nonlinear.max_moment()

    fig4_data = [
        {
            'x': (results_linear.moments / 1000).tolist(),
            'y': results_linear.depths.tolist(),
            'mode': 'lines',
            'name': 'Lineal',
            'line': {'color': 'blue', 'width': 3},
            'hovertemplate': 'M: %{x:.1f} kN·m<br>z: %{y:.2f} m<extra></extra>'
        },
        {
            'x': (results_nonlinear.moments / 1000).tolist(),
            'y': results_nonlinear.depths.tolist(),
            'mode': 'lines',
            'name': 'No Lineal',
            'line': {'color': 'red', 'width': 3, 'dash': 'dash'},
            'hovertemplate': 'M: %{x:.1f} kN·m<br>z: %{y:.2f} m<extra></extra>'
        },
        {
            'x': [M_max_lin/1000],
            'y': [z_M_lin],
            'mode': 'markers',
            'name': 'M_max Lineal',
            'marker': {'color': 'blue', 'size': 10, 'symbol': 'diamond'}
        },
        {
            'x': [M_max_nl/1000],
            'y': [z_M_nl],
            'mode': 'markers',
            'name': 'M_max No Lineal',
            'marker': {'color': 'red', 'size': 10, 'symbol': 'diamond'}
        }
    ]
    fig4_layout = {
        'title': 'Momento Flector',
        'xaxis': {'title': 'Momento (kN·m)'},
        'yaxis': {'title': 'Profundidad (m)', 'autorange': 'reversed'},
        'hovermode': 'closest',
        'template': 'plotly_white',
        'width': graph_width,
        'height': graph_height,
        'font': {'family': 'Arial', 'size': 11}
    }

    # Gráfico 5: Fuerza cortante
    fig5_data = [
        {
            'x': (results_linear.shears / 1000).tolist(),
            'y': results_linear.depths.tolist(),
            'mode': 'lines',
            'name': 'Lineal',
            'line': {'color': 'blue', 'width': 3},
            'hovertemplate': 'V: %{x:.1f} kN<br>z: %{y:.2f} m<extra></extra>'
        },
        {
            'x': (results_nonlinear.shears / 1000).tolist(),
            'y': results_nonlinear.depths.tolist(),
            'mode': 'lines',
            'name': 'No Lineal',
            'line': {'color': 'red', 'width': 3, 'dash': 'dash'},
            'hovertemplate': 'V: %{x:.1f} kN<br>z: %{y:.2f} m<extra></extra>'
        }
    ]
    fig5_layout = {
        'title': 'Fuerza Cortante',
        'xaxis': {'title': 'Cortante (kN)'},
        'yaxis': {'title': 'Profundidad (m)', 'autorange': 'reversed'},
        'hovermode': 'closest',
        'template': 'plotly_white',
        'width': graph_width,
        'height': graph_height,
        'font': {'family': 'Arial', 'size': 11}
    }

    # Gráfico 6: Presión del suelo
    fig6_data = [
        {
            'x': (results_linear.soil_pressures / 1000).tolist(),
            'y': results_linear.depths.tolist(),
            'mode': 'lines',
            'name': 'Lineal',
            'line': {'color': 'blue', 'width': 3},
            'hovertemplate': 'p: %{x:.1f} kN/m<br>z: %{y:.2f} m<extra></extra>'
        },
        {
            'x': (results_nonlinear.soil_pressures / 1000).tolist(),
            'y': results_nonlinear.depths.tolist(),
            'mode': 'lines',
            'name': 'No Lineal',
            'line': {'color': 'red', 'width': 3, 'dash': 'dash'},
            'hovertemplate': 'p: %{x:.1f} kN/m<br>z: %{y:.2f} m<extra></extra>'
        }
    ]
    fig6_layout = {
        'title': 'Presión del Suelo',
        'xaxis': {'title': 'Presión (kN/m)'},
        'yaxis': {'title': 'Profundidad (m)', 'autorange': 'reversed'},
        'hovermode': 'closest',
        'template': 'plotly_white',
        'width': graph_width,
        'height': graph_height,
        'font': {'family': 'Arial', 'size': 11}
    }

    # Gráfico 7: Rigidez k_h
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

    fig7_data = [
        {
            'x': (k_h_linear / 1e6).tolist(),
            'y': results_linear.depths.tolist(),
            'mode': 'lines',
            'name': 'Lineal (constante)',
            'line': {'color': 'blue', 'width': 3},
            'hovertemplate': 'k_h: %{x:.2f} MN/m³<br>z: %{y:.2f} m<extra></extra>'
        },
        {
            'x': (k_h_nonlinear / 1e6).tolist(),
            'y': results_nonlinear.depths.tolist(),
            'mode': 'lines',
            'name': 'No Lineal (degradado)',
            'line': {'color': 'red', 'width': 3, 'dash': 'dash'},
            'hovertemplate': 'k_h: %{x:.2f} MN/m³<br>z: %{y:.2f} m<extra></extra>'
        }
    ]
    fig7_layout = {
        'title': 'Rigidez del Suelo (k_h)',
        'xaxis': {'title': 'k_h (MN/m³)'},
        'yaxis': {'title': 'Profundidad (m)', 'autorange': 'reversed'},
        'hovermode': 'closest',
        'template': 'plotly_white',
        'width': graph_width,
        'height': graph_height,
        'font': {'family': 'Arial', 'size': 11}
    }

    # Calcular estadísticas
    y0_lin = results_linear.head_deflection() * 1000
    y0_nl = results_nonlinear.head_deflection() * 1000
    theta0_lin = results_linear.head_rotation() * 1000
    theta0_nl = results_nonlinear.head_rotation() * 1000
    p_max_lin = np.max(np.abs(results_linear.soil_pressures))
    p_max_nl = np.max(np.abs(results_nonlinear.soil_pressures))
    V_max_lin = np.max(results_linear.shears)
    V_max_nl = np.max(results_nonlinear.shears)

    # Convertir datos a JSON
    fig1_data_json = json.dumps(fig1_data)
    fig1_layout_json = json.dumps(fig1_layout)
    fig2_data_json = json.dumps(fig2_data)
    fig2_layout_json = json.dumps(fig2_layout)
    fig3_data_json = json.dumps(fig3_data)
    fig3_layout_json = json.dumps(fig3_layout)
    fig4_data_json = json.dumps(fig4_data)
    fig4_layout_json = json.dumps(fig4_layout)
    fig5_data_json = json.dumps(fig5_data)
    fig5_layout_json = json.dumps(fig5_layout)
    fig6_data_json = json.dumps(fig6_data)
    fig6_layout_json = json.dumps(fig6_layout)
    fig7_data_json = json.dumps(fig7_data)
    fig7_layout_json = json.dumps(fig7_layout)

    # ========== GENERAR HTML ==========
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Reporte Interactivo - Análisis para Carga de {load_applied/1e3:.0f} kN</title>
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
            display: inline-block;
        }}

        .graphs-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            margin-top: 30px;
        }}

        .graph-full {{
            grid-column: 1 / -1;
            text-align: center;
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
        <div class="subtitle">Análisis para carga horizontal de {load_applied/1e3:.0f} kN aplicada a ambos modelos</div>

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

<strong>CARGA APLICADA:</strong>
  Fuerza horizontal       : {load_applied/1e3:.0f} kN
  Momento en cabeza       : 0.0 kN·m</pre>
        </div>

        <h2>2. Deflexiones Resultantes para Carga de {load_applied/1e3:.0f} kN</h2>
        <table class="results-table">
            <thead>
                <tr>
                    <th>Modelo</th>
                    <th>Carga Aplicada (kN)</th>
                    <th>Deflexión en Cabeza (mm)</th>
                    <th>Observación</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td><strong>Modelo Lineal (Winkler)</strong></td>
                    <td>{load_applied/1e3:.1f}</td>
                    <td>{y0_lin:.2f}</td>
                    <td>k_h constante</td>
                </tr>
                <tr>
                    <td><strong>Modelo No Lineal (Duncan-Chang)</strong></td>
                    <td>{load_applied/1e3:.1f}</td>
                    <td>{y0_nl:.2f}</td>
                    <td>k_h degrada con deflexión</td>
                </tr>
            </tbody>
        </table>

        <div class="warning">
            <strong>⚠ Diferencia en Deflexión:</strong> Para la misma carga de {load_applied/1e3:.0f} kN, el modelo no lineal predice una deflexión
            <strong>{((y0_nl-y0_lin)/y0_lin*100):.1f}% MAYOR</strong> que el modelo lineal ({y0_nl:.1f} mm vs {y0_lin:.1f} mm).
            Esto demuestra que el modelo lineal <strong>SUBESTIMA</strong> las deflexiones reales.
        </div>

        <h2>3. Curva Carga-Deflexión Completa</h2>
        <div class="note">
            <strong>📊 Gráfico Interactivo:</strong> Pase el cursor sobre las curvas para ver valores exactos.
            Las estrellas marcan los puntos de análisis actual para la carga de {load_applied/1e3:.0f} kN.
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
                    <td>{load_applied/1e3:.1f} kN</td>
                    <td>{load_applied/1e3:.1f} kN</td>
                    <td class="highlight">Misma carga</td>
                </tr>
                <tr>
                    <td>Deflexión en cabeza</td>
                    <td>{y0_lin:.2f} mm</td>
                    <td>{y0_nl:.2f} mm</td>
                    <td class="highlight">{((y0_nl-y0_lin)/y0_lin*100):+.1f}%</td>
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
            Use zoom, pan y hover para explorar los datos en detalle. Los gráficos tienen proporción vertical (altura > ancho).
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
            <pre><strong>1. DIFERENCIA EN DEFLEXIÓN:</strong>
   Para la misma carga de {load_applied/1e3:.0f} kN, el modelo no lineal predice
   deflexiones {((y0_nl-y0_lin)/y0_lin*100):.1f}% MAYORES que el modelo lineal.

<strong>2. IMPLICACIONES PARA DISEÑO:</strong>
   • El modelo lineal (Winkler) SUBESTIMA las deflexiones reales
   • Usar modelo lineal puede llevar a FALLA POR SERVICIABILIDAD
   • Modelo no lineal (Duncan-Chang) más realista para cargas de trabajo

<strong>3. DEGRADACIÓN DE RIGIDEZ:</strong>
   • En modelo no lineal: k_h disminuye progresivamente con deflexión
   • En modelo lineal: k_h permanece constante (asunción irreal)
   • Mayor deflexión → mayor degradación → diferencia amplificada

<strong>4. RECOMENDACIÓN:</strong>
   El modelo NO LINEAL es esencial para:
   - Predecir deflexiones reales bajo cargas de trabajo
   - Verificar criterios de serviciabilidad
   - Diseño de pilotes sometidos a cargas laterales significativas
   - Estructuras donde las deflexiones son críticas</pre>
        </div>

    </div>

    <script>
        // Cargar gráficos interactivos con configuración responsive
        var config = {{responsive: true, displayModeBar: true}};

        Plotly.newPlot('graph1', {fig1_data_json}, {fig1_layout_json}, config);
        Plotly.newPlot('graph2', {fig2_data_json}, {fig2_layout_json}, config);
        Plotly.newPlot('graph3', {fig3_data_json}, {fig3_layout_json}, config);
        Plotly.newPlot('graph4', {fig4_data_json}, {fig4_layout_json}, config);
        Plotly.newPlot('graph5', {fig5_data_json}, {fig5_layout_json}, config);
        Plotly.newPlot('graph6', {fig6_data_json}, {fig6_layout_json}, config);
        Plotly.newPlot('graph7', {fig7_data_json}, {fig7_layout_json}, config);
    </script>
</body>
</html>"""

    # Guardar archivo HTML
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"  ✓ Reporte HTML interactivo generado: {filename}")


def main():
    print("=" * 80)
    print("REPORTE INTERACTIVO PARA CARGA FIJA DE 322 kN")
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

    # Carga fija a aplicar
    load_applied = 322e3  # 322 kN

    print("APLICANDO CARGA FIJA:")
    print("-" * 80)
    print(f"  Carga aplicada: {load_applied/1e3:.0f} kN")
    print()

    # Crear caso de carga
    load_case = LoadCase(horizontal_load=load_applied, moment=0.0, free_head=True)

    # Análisis lineal
    print("  Ejecutando análisis lineal...")
    results_linear = analysis_linear.solve(load_case)
    y_head_linear = results_linear.head_deflection() * 1000
    print(f"    ✓ Modelo lineal: y = {y_head_linear:.2f} mm")

    # Análisis no lineal
    print("  Ejecutando análisis no lineal...")
    results_nonlinear = analysis_nonlinear.solve(load_case, max_iterations=30, tolerance=1e-4, relaxation=0.5)
    y_head_nonlinear = results_nonlinear.head_deflection() * 1000
    print(f"    ✓ Modelo no lineal: y = {y_head_nonlinear:.2f} mm")

    print()
    print(f"  Diferencia en deflexión: {((y_head_nonlinear-y_head_linear)/y_head_linear*100):+.1f}%")
    print(f"  El modelo no lineal predice {((y_head_nonlinear-y_head_linear)/y_head_linear*100):.1f}% MÁS deflexión")
    print()

    # Generar reporte HTML interactivo
    print("GENERANDO REPORTE HTML INTERACTIVO:")
    print("-" * 80)
    generate_interactive_html_report(
        pile, soil_layers_linear, soil_layers_nonlinear,
        load_applied, results_linear, results_nonlinear,
        'interactive_report_322kN.html'
    )

    print()
    print("=" * 80)
    print("ANÁLISIS COMPLETADO")
    print("=" * 80)
    print()
    print("Archivos generados:")
    print("  • interactive_report_322kN.html - Reporte con gráficos interactivos Plotly")
    print()
    print("Características de los gráficos:")
    print("  • Proporciones: altura > ancho (500x800 px para gráficos verticales)")
    print("  • Curva P-y: 1000x600 px (horizontal)")
    print("  • Totalmente interactivos: zoom, pan, hover, download")
    print()
    print("Para visualizar:")
    print("  Abra 'interactive_report_322kN.html' en su navegador web")


if __name__ == "__main__":
    main()
