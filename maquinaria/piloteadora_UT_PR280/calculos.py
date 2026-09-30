"""
Memoria de cálculo de la perforadora rotativa para pilotes UT-PR280

Dimensionamiento preliminar de los sistemas principales para perforar
pilotes de Ø1.2 m hasta 40 m de profundidad (con reserva hasta ~43 m):
par de la mesa rotaria, potencia, cabrestante principal, empuje,
barra Kelly (torsión y pandeo), estabilidad al vuelco y presión sobre el suelo.

Todas las magnitudes internas en SI (m, kg, N, s) salvo que se indique.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple
import numpy as np

G = 9.81

# ---------------------------------------------------------------------------
# Requisitos de proyecto
# ---------------------------------------------------------------------------
DIAMETRO_PILOTE = 1.20        # m
PROFUNDIDAD_REQUERIDA = 40.0  # m


@dataclass
class TuboKelly:
    """Sección tubular de la barra Kelly telescópica"""
    nombre: str
    D: float      # diámetro exterior (m)
    t: float      # espesor de pared (m)
    L: float      # longitud (m)

    @property
    def d(self) -> float:
        return self.D - 2 * self.t

    @property
    def area(self) -> float:
        return np.pi / 4 * (self.D**2 - self.d**2)

    @property
    def J(self) -> float:
        """Momento polar de inercia (m^4)"""
        return np.pi / 32 * (self.D**4 - self.d**4)

    @property
    def I(self) -> float:
        return self.J / 2

    @property
    def masa(self) -> float:
        # tubo + chavetas de arrastre y collarines (~18 % adicional)
        return self.area * self.L * 7850 * 1.18


# Barra Kelly de 4 secciones con bloqueo (interlocking), acero 42CrMo4 / S690
# Holgura radial entre tubos = chaveta 18 mm + juego 3 mm → D(i+1) = d(i) − 42
KELLY = [
    TuboKelly("Sección 1 (exterior)", 0.508, 0.022, 12.5),
    TuboKelly("Sección 2", 0.422, 0.020, 12.5),
    TuboKelly("Sección 3", 0.340, 0.020, 12.5),
    TuboKelly("Sección 4 (interior)", 0.258, 0.030, 12.5),
]
ALTURA_CHAVETA = 0.018  # m
SOLAPE_KELLY = 1.60       # m, solape mínimo entre secciones extendidas
SOBRESALIENTE_KELLY = 3.5  # m, parte de la Kelly sobre el terreno a máx. prof.
ALTURA_UTIL_HERRAMIENTA = 1.5  # m, cubeta Ø1200

# Masas de los conjuntos principales (kg) y posición del CdG
# x: distancia horizontal al eje de giro, positivo hacia el mástil (m)
# z: altura sobre el terreno (m)
MASAS: List[Tuple[str, float, float, float]] = [
    # nombre, masa, x, z
    ("Tren de rodaje (orugas 800 mm)", 26_000, 0.00, 0.60),
    ("Superestructura + motor + cabina", 16_000, -1.10, 2.10),
    ("Contrapeso", 18_000, -3.85, 2.10),
    ("Mástil + cinemática + cabrestantes", 8_500, 2.85, 10.50),
    ("Mesa rotaria (en posición alta)", 6_200, 4.00, 6.00),
    ("Barra Kelly 4 secciones", 0, 4.30, 8.20),  # se calcula de KELLY
    ("Herramienta (cubeta Ø1200 llena)", 5_600, 4.30, 0.75),
]

# Tren de rodaje
LONGITUD_APOYO_ORUGA = 4.70   # m, entre centros de rueda guía y motriz
ANCHO_ZAPATA = 0.80           # m
TROCHA_TRABAJO = 4.40         # m, entre ejes de orugas (extendido)
TROCHA_TRANSPORTE = 2.20      # m (retraído, ancho total 3.0 m)
RADIO_PERFORACION = 4.30      # m, eje de giro a eje Kelly (nominal)


@dataclass
class Resultados:
    tabla: Dict[str, str] = field(default_factory=dict)
    verificaciones: List[Tuple[str, float, float, str, bool]] = field(default_factory=list)

    def ok(self, nombre, valor, limite, unidad, cumple):
        self.verificaciones.append((nombre, valor, limite, unidad, cumple))


def par_requerido(D=DIAMETRO_PILOTE, f_corte=450e3, factor_friccion=1.30):
    """
    Par de corte de una cubeta de doble corte radial.

    Cada filo radial de longitud R = D/2 soporta una fuerza de corte por
    unidad de longitud f (N/m). Par de dos filos: M = 2∫f·r dr = f·R².
    f ≈ 450 kN/m corresponde a grava densa / roca blanda (UCS ≤ 10 MPa).
    Se mayora un 30 % por rozamiento lateral de la herramienta y la Kelly.
    """
    R = D / 2
    return f_corte * R**2 * factor_friccion


def par_empotramiento_roca(D=DIAMETRO_PILOTE, ucs=25e6, n_picas=14,
                           prof_corte=0.010, ancho_pica=0.025, k_corte=3.2,
                           factor_friccion=1.30):
    """
    Par para corona de corte con picas (core barrel) en roca de UCS dado.
    Fuerza de corte por pica: F_c = k·UCS·(profundidad de corte × ancho),
    con k ≈ 3–4 (ensayos de corte lineal). Picas en el radio exterior.
    """
    F_c = k_corte * ucs * prof_corte * ancho_pica
    return n_picas * F_c * (D / 2) * factor_friccion


def calcular() -> Resultados:
    r = Resultados()

    # --- Profundidad con Kelly -------------------------------------------
    n = len(KELLY)
    L_ext = sum(k.L for k in KELLY) - (n - 1) * SOLAPE_KELLY
    L_ret = max(k.L for k in KELLY) + 0.9  # + collarines y amortiguador
    prof_max = L_ext - SOBRESALIENTE_KELLY + ALTURA_UTIL_HERRAMIENTA
    r.tabla["Kelly extendida"] = f"{L_ext:.1f} m"
    r.tabla["Kelly retraída"] = f"{L_ret:.1f} m"
    r.tabla["Profundidad máxima"] = f"{prof_max:.1f} m"
    r.ok("Profundidad máxima alcanzable", prof_max, PROFUNDIDAD_REQUERIDA, "m",
         prof_max >= PROFUNDIDAD_REQUERIDA)

    masa_kelly = sum(k.masa for k in KELLY)
    r.tabla["Masa Kelly"] = f"{masa_kelly/1000:.1f} t"

    # --- Par ---------------------------------------------------------------
    M_suelo = par_requerido()
    M_roca = par_empotramiento_roca()
    M_nom = 280e3
    r.tabla["Par requerido suelo"] = f"{M_suelo/1e3:.0f} kNm"
    r.tabla["Par requerido roca"] = f"{M_roca/1e3:.0f} kNm"
    M_dem = max(M_suelo, M_roca)
    r.ok("Par nominal mesa rotaria ≥ 1.15·par requerido", M_nom / 1e3,
         1.15 * M_dem / 1e3, "kNm", M_nom >= 1.15 * M_dem)

    # --- Potencia ----------------------------------------------------------
    rpm_trabajo = 8.0
    P_hid = M_nom * rpm_trabajo * 2 * np.pi / 60
    eta = 0.80  # bombas + motores + reductores
    P_motor = 354e3
    r.tabla["Potencia rotaria (280 kNm @ 8 rpm)"] = f"{P_hid/1e3:.0f} kW"
    r.ok("Potencia útil del motor (η=0.80)", P_motor * eta / 1e3, P_hid / 1e3, "kW",
         P_motor * eta >= P_hid)

    # --- Cabrestante principal --------------------------------------------
    vol_cubeta = np.pi / 4 * 1.18**2 * 1.20
    m_suelo = vol_cubeta * 2000
    m_cubeta = 3000
    carga_est = (masa_kelly + m_cubeta + m_suelo) * G
    factor_din = 1.60  # succión + arranque + dinámica
    carga_din = carga_est * factor_din
    F_winch = 300e3
    r.tabla["Volumen cubeta"] = f"{vol_cubeta:.2f} m³"
    r.tabla["Carga estática gancho"] = f"{carga_est/1e3:.0f} kN"
    r.ok("Tiro cabrestante principal ≥ carga·1.6", F_winch / 1e3, carga_din / 1e3, "kN",
         F_winch >= carga_din)

    # Cable Ø32 mm, 35xK7, 1960 N/mm² — carga de rotura mínima
    MBL = 1_000e3
    r.ok("Coef. seguridad cable Ø32 (≥ 3.0)", MBL / F_winch, 3.0, "-", MBL / F_winch >= 3.0)

    # --- Kelly: torsión ----------------------------------------------------
    fy = 690e6
    tau_adm = 0.58 * fy / 1.5
    for k in KELLY:
        tau = M_nom * (k.D / 2) / k.J
        r.ok(f"Torsión {k.nombre}", tau / 1e6, tau_adm / 1e6, "MPa", tau <= tau_adm)

    # --- Kelly: pandeo de la sección interior bajo empuje -----------------
    F_empuje = 250e3
    k_in = KELLY[-1]
    E = 210e9
    # K = 1: extremo superior guiado por el solape en la sección 3 y
    # extremo inferior guiado por la herramienta dentro de la perforación
    Pcr = np.pi**2 * E * k_in.I / (1.0 * k_in.L) ** 2
    r.ok("Pandeo sección interior (FS ≥ 2.5)", Pcr / F_empuje, 2.5, "-",
         Pcr / F_empuje >= 2.5)

    # --- Estabilidad y presión sobre el terreno ---------------------------
    masas = []
    for nombre, m, x, z in MASAS:
        if m == 0 and "Kelly" in nombre:
            m = masa_kelly
        masas.append((nombre, m, x, z))
    W = sum(m for _, m, _, _ in masas)
    x_cg = sum(m * x for _, m, x, _ in masas) / W
    z_cg = sum(m * z for _, m, _, z in masas) / W
    r.tabla["Masa en servicio (con herramienta)"] = f"{W/1000:.1f} t"
    r.tabla["CdG (x, z)"] = f"({x_cg:.2f} m, {z_cg:.2f} m)"

    # Viento en servicio 20 m/s sobre mástil+Kelly (≈ 0.9 m × 22 m, Cf = 1.6)
    q = 0.5 * 1.25 * 20**2
    F_viento = q * 1.6 * 0.9 * 22
    M_viento = F_viento * 11.0

    def coef_vuelco(a):
        """Momentos respecto a la línea de vuelco a distancia 'a' del eje"""
        M_est = sum(m * G * (a - x) for _, m, x, _ in masas if x < a)
        M_vol = sum(m * G * (x - a) for _, m, x, _ in masas if x >= a) + M_viento
        return M_est / M_vol

    # frontal: línea en la rueda guía delantera
    s_front = coef_vuelco(LONGITUD_APOYO_ORUGA / 2)
    # lateral (giro 90°): línea en el eje de la oruga
    s_lat = coef_vuelco(TROCHA_TRABAJO / 2)
    r.ok("Estabilidad frontal (≥ 1.4)", s_front, 1.4, "-", s_front >= 1.4)
    r.ok("Estabilidad lateral a 90° (≥ 1.4)", s_lat, 1.4, "-", s_lat >= 1.4)

    # Vuelco hacia atrás sin herramienta ni Kelly, mástil vertical
    masas_tras = [(n_, m, -x, z) for n_, m, x, z in masas
                  if "Herramienta" not in n_ and "Kelly" not in n_]
    M_est = sum(m * G * (LONGITUD_APOYO_ORUGA / 2 - x) for _, m, x, _ in masas_tras
                if x < LONGITUD_APOYO_ORUGA / 2)
    M_vol = sum(m * G * (x - LONGITUD_APOYO_ORUGA / 2) for _, m, x, _ in masas_tras
                if x >= LONGITUD_APOYO_ORUGA / 2)
    s_tras = M_est / max(M_vol, 1.0)
    r.ok("Estabilidad trasera sin Kelly (≥ 1.4)", s_tras, 1.4, "-", s_tras >= 1.4)

    A = 2 * ANCHO_ZAPATA * LONGITUD_APOYO_ORUGA
    p_med = W * G / A
    e = abs(x_cg)
    p_max = p_med * (1 + 6 * e / LONGITUD_APOYO_ORUGA)
    r.tabla["Presión media sobre terreno"] = f"{p_med/1e3:.0f} kPa"
    r.ok("Presión máxima bajo orugas (≤ 250 kPa)", p_max / 1e3, 250, "kPa", p_max <= 250e3)

    r.masas = masas
    r.W, r.x_cg, r.z_cg = W, x_cg, z_cg
    r.L_ext, r.L_ret, r.prof_max, r.masa_kelly = L_ext, L_ret, prof_max, masa_kelly
    return r


def curva_par_velocidad():
    """Curva característica de la mesa rotaria (potencia hidráulica limitada)"""
    P = 290e3  # W disponibles en la rotaria
    rpm = np.linspace(1, 32, 200)
    M = np.minimum(280e3, P / (rpm * 2 * np.pi / 60))
    return rpm, M / 1e3


if __name__ == "__main__":
    res = calcular()
    print("=== UT-PR280 — resultados principales ===")
    for k, v in res.tabla.items():
        print(f"  {k:40s} {v}")
    print("\n=== Verificaciones ===")
    for nombre, val, lim, u, cumple in res.verificaciones:
        print(f"  [{'OK' if cumple else 'NO'}] {nombre:45s} {val:8.2f} vs {lim:8.2f} {u}")
