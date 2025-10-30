"""
Comparación de modelos hiperbólicos no lineales para rigidez del suelo
"""

import numpy as np
import matplotlib.pyplot as plt

# Parámetros de ejemplo
k_h_inicial = 10e6  # N/m³
b = 1.0  # Diámetro del pilote (m)
p_ult = 500e3  # Presión última (N/m)
y_max = 0.1  # Deflexión máxima (m)

# Rango de deflexiones
y = np.linspace(0, y_max, 200)

# Modelo 1: Hiperbólico clásico (Duncan-Chang)
p_1 = (k_h_inicial * b * y) / (1 + k_h_inicial * b * y / p_ult)
k_s_1 = k_h_inicial / (1 + k_h_inicial * b * y / p_ult)

# Modelo 2: Factor de degradación hiperbólico
alpha = 20  # Parámetro de degradación
k_h_2 = k_h_inicial / (1 + alpha * np.abs(y))
p_2 = k_h_2 * b * y

# Modelo 3: Hiperbólico con exponente
y_ref = 0.02  # Deflexión de referencia (m)
n = 1.0
k_h_3 = k_h_inicial / (1 + (y / y_ref)**n)
p_3 = k_h_3 * b * y

# Modelo 4: Tangente hiperbólica (p-y API)
A = 0.9
p_4 = A * p_ult * np.tanh(k_h_inicial * b * y / (A * p_ult))
k_s_4 = k_h_inicial * (1 - np.tanh(k_h_inicial * b * y / (A * p_ult))**2)

# Modelo lineal (referencia)
p_linear = k_h_inicial * b * y
k_linear = np.ones_like(y) * k_h_inicial

# Crear gráficos
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Gráfico 1: Presión vs Deflexión
ax1 = axes[0]
ax1.plot(y*1000, p_1/1000, 'b-', linewidth=2.5, label='Modelo 1: Duncan-Chang')
ax1.plot(y*1000, p_2/1000, 'g-', linewidth=2.5, label='Modelo 2: Degradación α')
ax1.plot(y*1000, p_3/1000, 'r-', linewidth=2.5, label='Modelo 3: Exponencial')
ax1.plot(y*1000, p_4/1000, 'm-', linewidth=2.5, label='Modelo 4: tanh (p-y API)')
ax1.plot(y*1000, p_linear/1000, 'k--', linewidth=2, label='Lineal (Winkler)', alpha=0.5)

ax1.set_xlabel('Deflexión, y (mm)', fontsize=12, fontweight='bold')
ax1.set_ylabel('Presión del suelo, p (kN/m)', fontsize=12, fontweight='bold')
ax1.set_title('(a) Relación Presión-Deflexión', fontsize=13, fontweight='bold')
ax1.grid(True, alpha=0.3, linestyle='--')
ax1.legend(loc='lower right', fontsize=10)
ax1.set_xlim(0, y_max*1000)
ax1.set_ylim(0, None)

# Gráfico 2: Rigidez vs Deflexión
ax2 = axes[1]
ax2.plot(y*1000, k_s_1/1e6, 'b-', linewidth=2.5, label='Modelo 1: Duncan-Chang')
ax2.plot(y*1000, k_h_2/1e6, 'g-', linewidth=2.5, label='Modelo 2: Degradación α')
ax2.plot(y*1000, k_h_3/1e6, 'r-', linewidth=2.5, label='Modelo 3: Exponencial')
ax2.plot(y*1000, k_s_4/1e6, 'm-', linewidth=2.5, label='Modelo 4: tanh (p-y API)')
ax2.plot(y*1000, k_linear/1e6, 'k--', linewidth=2, label='Lineal (Winkler)', alpha=0.5)

ax2.set_xlabel('Deflexión, y (mm)', fontsize=12, fontweight='bold')
ax2.set_ylabel('Rigidez, k_h (MN/m³)', fontsize=12, fontweight='bold')
ax2.set_title('(b) Degradación de Rigidez', fontsize=13, fontweight='bold')
ax2.grid(True, alpha=0.3, linestyle='--')
ax2.legend(loc='upper right', fontsize=10)
ax2.set_xlim(0, y_max*1000)
ax2.set_ylim(0, None)

plt.tight_layout()
plt.savefig('modelos_hiperbolicos_no_lineales.png', dpi=300, bbox_inches='tight')
print("Gráfico guardado: modelos_hiperbolicos_no_lineales.png")

# Mostrar ecuaciones
print("\n" + "="*80)
print("MODELOS HIPERBÓLICOS NO LINEALES")
print("="*80)
print()

print("MODELO 1: Hiperbólico Clásico (Duncan-Chang)")
print("-" * 80)
print("  p(y) = k_h·b·y / (1 + k_h·b·y/p_ult)")
print("  k_s(y) = k_h / (1 + k_h·b·y/p_ult)")
print()
print(f"  Parámetros:")
print(f"    k_h inicial = {k_h_inicial/1e6:.1f} MN/m³")
print(f"    p_ult = {p_ult/1e3:.1f} kN/m")
print()

print("MODELO 2: Factor de Degradación Hiperbólico")
print("-" * 80)
print("  k_h(y) = k_h_inicial / (1 + α·|y|)")
print("  p(y) = k_h(y)·b·y")
print()
print(f"  Parámetros:")
print(f"    k_h inicial = {k_h_inicial/1e6:.1f} MN/m³")
print(f"    α = {alpha} m⁻¹")
print()

print("MODELO 3: Hiperbólico con Exponente")
print("-" * 80)
print("  k_h(y) = k_h_inicial / (1 + (y/y_ref)^n)")
print("  p(y) = k_h(y)·b·y")
print()
print(f"  Parámetros:")
print(f"    k_h inicial = {k_h_inicial/1e6:.1f} MN/m³")
print(f"    y_ref = {y_ref*1000:.1f} mm")
print(f"    n = {n}")
print()

print("MODELO 4: Tangente Hiperbólica (API p-y)")
print("-" * 80)
print("  p(y) = A·p_ult·tanh(k_h·b·y/(A·p_ult))")
print("  k_t(y) = k_h·sech²(k_h·b·y/(A·p_ult))")
print()
print(f"  Parámetros:")
print(f"    k_h inicial = {k_h_inicial/1e6:.1f} MN/m³")
print(f"    A = {A}")
print(f"    p_ult = {p_ult/1e3:.1f} kN/m")
print()

# Comparación de rigidez a diferentes deflexiones
print("\n" + "="*80)
print("COMPARACIÓN DE RIGIDEZ A DIFERENTES DEFLEXIONES")
print("="*80)
print()
print(f"{'Deflexión (mm)':<20} {'Lineal':<12} {'Modelo 1':<12} {'Modelo 2':<12} {'Modelo 3':<12} {'Modelo 4':<12}")
print(f"{'':20} {'k_h (MN/m³)':<12} {'k_s (MN/m³)':<12} {'k_h (MN/m³)':<12} {'k_h (MN/m³)':<12} {'k_t (MN/m³)':<12}")
print("-" * 100)

deflexiones_test = [0, 10, 25, 50, 75, 100]
for y_test_mm in deflexiones_test:
    y_test = y_test_mm / 1000

    # Lineal
    k_lin = k_h_inicial

    # Modelo 1
    k_1 = k_h_inicial / (1 + k_h_inicial * b * y_test / p_ult)

    # Modelo 2
    k_2 = k_h_inicial / (1 + alpha * abs(y_test))

    # Modelo 3
    k_3 = k_h_inicial / (1 + (y_test / y_ref)**n) if y_test > 0 else k_h_inicial

    # Modelo 4
    k_4 = k_h_inicial * (1 - np.tanh(k_h_inicial * b * y_test / (A * p_ult))**2)

    print(f"{y_test_mm:<20.1f} {k_lin/1e6:<12.2f} {k_1/1e6:<12.2f} {k_2/1e6:<12.2f} {k_3/1e6:<12.2f} {k_4/1e6:<12.2f}")

print()
print("Observación: Todos los modelos muestran degradación de rigidez con el aumento")
print("de la deflexión, siendo el modelo lineal (Winkler) el único que mantiene k_h constante.")
print()
