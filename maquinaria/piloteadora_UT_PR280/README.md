# UT-PR280 — Perforadora rotativa para pilotes Ø1200 × 40 m

Anteproyecto de una piloteadora hidráulica de gama alta sobre orugas, con Kelly
telescópica de bloqueo (interlocking), para ejecutar pilotes perforados de
**Ø1.2 m hasta 40 m** de profundidad (reserva hasta 43.2 m) en suelos y roca blanda.

Los planos están en [`planos/UT-PR280_planos.pdf`](planos/UT-PR280_planos.pdf)
(8 hojas A3, a escala real impresos al 100 %) y se regeneran con:

```bash
pip install -r ../../requirements.txt
python planos.py      # genera planos/*.pdf y un PNG por hoja
python calculos.py    # imprime la memoria de cálculo resumida
```

## Índice de planos

| N.º | Título | Escala |
|-----|--------|--------|
| PR280-01 | Disposición general: alzado lateral, frontal, planta y características | 1:100 |
| PR280-02 | Configuración de transporte, rango del paralelogramo, inclinación del mástil | 1:75 / 1:100 |
| PR280-03 | Mástil: sección A-A, cabeza con poleas, unión del tramo superior | 1:15 / 1:25 / 1:40 / 1:150 |
| PR280-04 | Mesa rotaria 280 kNm: sección D-D, planta de motores, despiece | 1:15 / 1:20 |
| PR280-05 | Barra Kelly 4 secciones: retraída/extendida, sección, punto de bloqueo | 1:200 / 1:5 |
| PR280-06 | Herramientas Ø1200: cubeta, hélice, corona de roca, camisa | 1:25 |
| PR280-07 | Esquema hidráulico principal (ISO 1219-1) | S/E |
| PR280-08 | Memoria de cálculo: estabilidad, curva par-velocidad, presiones, verificaciones | 1:125 / S/E |

## Características principales

| Característica | Valor |
|---|---|
| Diámetro de perforación nominal / máximo | 1200 / 1500 mm |
| Profundidad máxima (Kelly 4 × 12.5 m) | 43.2 m |
| Par nominal de la mesa rotaria (350 bar) | 280 kNm |
| Velocidad de rotación / centrifugado | 5–30 / 90 rpm |
| Empuje / extracción (cabrestante de empuje) | 250 / 300 kN, carrera 12 m |
| Cabrestante principal | 300 kN, 70 m/min, cable Ø32 |
| Cabrestante auxiliar | 100 kN, cable Ø20 |
| Motor diésel | 354 kW @ 1800 rpm (Stage V / Tier 4f) |
| Altura de trabajo | 23.4 m |
| Radio de perforación | 3800 – 4700 mm |
| Orugas | zapata 800 mm, trocha 4400 (trabajo) / 2200 (transporte) |
| Masa en servicio (con herramienta) | ≈ 92 t |
| Transporte (lote 1) | 15.7 × 3.0 × 3.45 m, ≈ 71 t |

## Resumen de cálculo (`calculos.py`)

| Verificación | Resultado | Límite |
|---|---|---|
| Profundidad alcanzable | 43.2 m | ≥ 40 m |
| Par disponible vs. 1.15 × par requerido (roca UCS 25 MPa) | 280 kNm | ≥ 251 kNm |
| Potencia útil del motor (η = 0.80) | 283 kW | ≥ 235 kW |
| Cabrestante principal vs. carga × 1.6 | 300 kN | ≥ 271 kN |
| Torsión en la sección interior de la Kelly | 127 MPa | ≤ 267 MPa |
| Pandeo de la sección interior (FS) | 7.5 | ≥ 2.5 |
| Estabilidad frontal / lateral / trasera | 4.0 / 3.6 / 6.1 | ≥ 1.4 |
| Presión máxima bajo orugas | 180 kPa | ≤ 250 kPa |

Hipótesis: par de corte de cubeta `M = f·R²·1.3` con f = 450 kN/m; corona de 14
picas con `F = 3.2·UCS·A` y UCS = 25 MPa; factor dinámico 1.6 en el cabrestante
(succión y arranque); viento en servicio 20 m/s sobre el mástil; aceros S690QL
(mástil) y 42CrMo4 QT (Kelly). Normas de referencia: EN 16228-1/-2, EN 13001,
EN 1536, ISO 5817, ISO 1219-1.

## Alcance y limitaciones

Esto es un **anteproyecto / diseño conceptual**: fija la geometría, las
prestaciones y el dimensionamiento preliminar de los sistemas principales. Antes
de fabricar hace falta la ingeniería de detalle: modelo 3D y cálculo por
elementos finitos del mástil y del bastidor, fatiga de las uniones soldadas,
selección de componentes comerciales (motor, bombas, reductores, rodamientos)
con los datos del fabricante, análisis de riesgos según EN 16228 y marcado CE.
