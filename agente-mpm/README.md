# agente-mpm — Talud CEMEX Sección A (MPM, 2D)

Pipeline autónomo de simulación de **rompimiento de talud** por el Método del
Punto Material (MPM, cb-geo) con verificación física cuantitativa desde HDF5 y
generación de video estilo CEL/Abaqus.

## Estructura
```
src/
  meshgen.py        Malla estructurada de cuadriláteros + partículas (Ascii2D), sin DXF
  make_case.py      Construye un caso cb-geo (malla, partículas, K0, mpm.json)
  gates.py          Gates físicos cuantitativos desde el HDF5 (6 criterios)
  postprocess.py    HDF5 -> PNG -> MP4 (campo de velocidad/desplazamiento)
  run_calibration.py  Caso canónico: colapso de columna granular seco
  slope_loop.py     LOOP autónomo: correr->verificar->diagnosticar->ajustar->relanzar
calibration/        Caso canónico + VIDEO_calibracion.mp4 (validación de la cadena)
cases/seccionA/     Caso del talud
checkpoints/        Mejor intento por iteración (results HDF5; ignorado por git)
reports/            loop_history.json, best.json, REPORTE.md, VIDEO final
```

## Motor
cb-geo/MPM compilado desde fuente (Docker Hub estaba rate-limited):
- `MPMExplicit2D` (una fase) — `/home/user/mpm-build`
- `MPMExplicitTwoPhase2D` (dos fases) — `/home/user/mpm-dev`, rama
  `solver/two-phase-explicit`

## Gates ("rompimiento perfecto" = los 6 pasan)
a. corre completo, sin NaN · b. masa conservada · c. KE sube y decae a ~0 ·
d. banda de corte localizada (no difusa ni cuerpo rígido) · e. material en el
dominio, sin popcorn/cell-crossing · f. runout converge.

## Notas importantes (ver REPORTE.md)
- **DXF / Sección A:** el repo `agente-topografia` y el DXF de la Sección A NO
  existen en este entorno. La geometría es un **stand-in paramétrico**
  (`meshgen.load_section_polygon`), trivial de sustituir por los vértices reales.
- **NF alto / bifásico:** el solver bifásico se compiló y probó, pero explota
  hacia el paso ~20 por falta de estado inicial geostático+hidrostático
  equilibrado. El "NF alto" se modela con **tensión efectiva en una fase**
  (peso sumergido + resistencia efectiva reducida), numéricamente estable.
