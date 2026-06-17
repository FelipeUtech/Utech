# CONTINUAR EN LOCAL — meter la Sección A real (DXF) y re-correr

> Handoff para la **sesión local de Claude Code (Mac)** con acceso a OneDrive y Docker.
> El trabajo de la corrida nocturna (cloud) quedó en este branch:
> `claude/cemex-talud-mpm-loop-teo9nh`. Lee primero `REPORTE.md`.

## Objetivo
Sustituir la geometría **paramétrica** (stand-in) por la **Sección A-A real** del DXF
y volver a correr el loop MPM, regenerando video + REPORTE con la geometría verdadera.

DXF (en OneDrive local del usuario):
```
/Users/felipeuribe/Library/CloudStorage/OneDrive-UTechEngineerings.a.s/UTECH - PROYECTOS/U_260001-GEO-CEMX-MACEO-SUSANA/002-Memorias/#seccion_A-A.dxf
```

## Pasos para el agente local

### 1. Motor MPM (con Docker, sin rate-limit)
```bash
docker pull cbgeo/mpm
# correr un caso:
docker run --rm -v "<CASE_DIR>":/sim cbgeo/mpm mpm -f /sim/ -i mpm.json -p 4
```
En `src/slope_loop.py` y `src/run_calibration.py`, `MPM_BIN` apunta a los binarios
compilados en la nube (`/home/user/mpm-build/...`, `/home/user/mpm-dev/...`) que **no
existen en el Mac**. Opciones:
- (fácil) crear un wrapper `src/mpm` que invoque `docker run ... cbgeo/mpm mpm "$@"`
  con mapeo de volumen, y apuntar `MPM_BIN` a ese wrapper; **o**
- recompilar de fuente (Homebrew: `cmake eigen hdf5 boost`), igual que en la nube.
- Nota: el binario **bifásico** está en la rama `solver/two-phase-explicit` de cb-geo.

### 2. Parsear el DXF y extraer la Sección A-A
```bash
pip install ezdxf
```
```python
import ezdxf
doc = ezdxf.readfile("<ruta del dxf>")
msp = doc.modelspace()
print("Capas:", [l.dxf.name for l in doc.layers])
# Extraer polilíneas por capa (perfil de terreno, talud, NF/nivel freático, estratos):
for e in msp.query("LWPOLYLINE POLYLINE LINE"):
    print(e.dxftype(), getattr(e.dxf,'layer',''), len(list(e.vertices())) if hasattr(e,'vertices') else '')
```
- Identificar la **capa del perfil del talud** → lista de vértices `(x,y)`.
- Si hay una **capa de nivel freático (NF)** → usarla como `water_table.position`.
- Si hay **capas de estratos** → propiedades por material por estrato.

### 3. Enchufar la geometría real
Reemplazar el cuerpo de `meshgen.load_section_polygon()` (en `src/meshgen.py`) para
devolver los vértices reales de la Sección A-A (la función está **aislada justo para
esto**). Normalizar el origen (toe en x grande para dejar runout a la derecha) y
escalar a metros si el DXF está en otras unidades.

### 4. Re-correr
```bash
cd agente-mpm/src
python3 run_calibration.py      # opcional, revalida la cadena
python3 slope_loop.py           # loop autónomo con la geometría real
python3 make_deliverable.py <results> <case> <score> <0|1> <Lx> <Ly> <dt> <out_steps>
```

## Config que ya funcionó (punto de partida, ver REPORTE.md §4)
- Malla ED2Q4, `h≈0.25 m`, **estado inicial K0 geostático** (evita shock en t=0).
- **Tensión efectiva 1-fase** para NF alto (peso sumergido + resistencia reducida).
- **`ppc=3`** (clave: eliminó el ruido de cell-crossing; |v|max 0.63 m/s).
- Cundall damping ≈ 0.18, dt=3.5e-4, ablandamiento `pdstrain` 0.01→0.10.
- Resultado: **5/6 gates** (banda de corte localizada, runout convergente).
  Gate c (quiescencia total KE) asíntota en ~0.18 vs umbral 0.15.

## Para cerrar el gate c (6/6)
- **GIMP/CPDI**: en el build de la nube `ED2Q16G` hace segfault en t=0 por falta de
  soporte de nodos vecinos en la frontera; corregir el manejo de celdas de borde
  (o compilar CPDI) sostiene la gran deformación sin ruido → KE→0.
- **Bifásico real**: inicializar estado **geostático + hidrostático equilibrado**
  (tensión efectiva K0 + presión de poro consistentes) antes de t=0; con eso el
  solver bifásico ya compilado debería estabilizarse (hoy explota al paso ~20).
