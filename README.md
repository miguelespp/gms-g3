# Code Anomaly Detector — Índice de Mantenibilidad

Herramienta de análisis **estático léxico** de código fuente que calcula el Índice de
Mantenibilidad (MI) para detectar archivos de alto riesgo de mantenimiento.

> Proyecto final — Gestión de Mantenimiento de Software

---

## Requisitos

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (recomendado) o pip

## Instalación

```bash
# Con uv (recomendado)
uv sync --extra dev

# Con pip
pip install -e ".[dev]"
```

## Uso

```bash
# Analizar un directorio
python -m src.cli analyze samples/

# Analizar un archivo individual
python -m src.cli analyze samples/messy_example.py

# Agregar extensiones adicionales
python -m src.cli analyze src/ --ext .vue,.svelte
```

La tabla muestra los archivos **ordenados por MI ascendente** (el más riesgoso primero).

### Detección de *code smells*

```bash
# Buscar code smells en un directorio o archivo
python -m src.cli smells samples/

# Ajustar umbrales
python -m src.cli smells src/ --max-func-lines 60 --max-nesting 5

# Reporte integrado: MI + smells + recomendación
python -m src.cli report samples/
```

Muestra, por archivo, los smells detectados (ordenados por severidad) y un
resumen global. Reglas detectadas:

| Regla | Severidad | Qué marca |
|-------|-----------|-----------|
| `dangerous-function` | 🔴 crítico | Llamadas a `gets`, `strcpy`, `system`, `eval`, … |
| `unbalanced-delimiters` | 🔴 crítico | Paréntesis / llaves / corchetes sin pareja |
| `complex-function` | 🟡 advertencia | Función que supera **a la vez** LOC, complejidad ciclomática y anidamiento (regla compuesta) |
| `deep-nesting` | 🟡 advertencia | Anidamiento (por indentación) sobre el umbral |
| `long-function` | 🟡 advertencia | Funciones más largas que el umbral de líneas |
| `magic-number` | 🔵 info | Literales numéricos fuera de la whitelist |
| `commented-code` | 🔵 info | Comentarios que parecen código comentado |
| `todo-marker` | 🔵 info | Marcadores `TODO` / `FIXME` / `HACK` / `XXX` |

> **Regla compuesta (`complex-function`).** Siguiendo las *detection strategies* de
> Lanza & Marinescu, esta regla combina tres métricas con AND lógico
> (`LOC ∧ Complejidad Ciclomática ∧ Anidamiento`): una función solo se marca si
> supera los tres umbrales a la vez. Así, una función larga *pero* simple no se
> reporta, reduciendo falsos positivos. Cuando una función cae en `complex-function`,
> se omite el `long-function` redundante. Reutiliza `compute_complexity` del módulo
> de mantenibilidad.

## Ejecutar tests

```bash
pytest -v
# Con cobertura
pytest --cov=src --cov-report=term-missing
```

---

## Métricas calculadas

| Métrica | Descripción |
|---------|-------------|
| **SLOC** | Source Lines of Code (sin blancos ni comentarios) |
| **CC** | Complejidad Ciclomática aproximada — `1 + tokens de decisión` |
| **Vol. Halstead** | `V = N · log₂(n)` donde N = total tokens, n = vocabulario |
| **% Comentarios** | `comentarios / (comentarios + SLOC)` |
| **MI** | Índice de Mantenibilidad `max(0, (171 − 5.2·ln(V) − 0.23·CC − 16.2·ln(SLOC)) · 100/171)` |

### Umbrales de MI

| Color | Rango | Significado |
|-------|-------|-------------|
| 🟢 Verde | MI ≥ 20 | Mantenible |
| 🟡 Amarillo | 10 ≤ MI < 20 | Riesgo moderado |
| 🔴 Rojo | MI < 10 | Difícil de mantener |

---

## Arquitectura

```
src/
  core/
    file_reader.py   # lee archivo o recorre directorio
    lexer.py         # tokenización léxica con Pygments
  metrics/
    halstead.py      # métricas de Halstead (n1, n2, N1, N2, V, D, E)
    complexity.py    # complejidad ciclomática (conteo de tokens de decisión)
    loc.py           # LOC, SLOC, blancos, comentarios, ratio
    maintainability.py  # fórmula MI normalizada de Microsoft
    smells.py        # detector de code smells por patrones léxicos/textuales
  report/
    console.py       # tabla Rich con ranking de mantenibilidad
    smells.py        # tablas Rich de code smells por archivo + resumen
    summary.py       # reporte integrado MI + smells + recomendaciones
  cli.py             # punto de entrada CLI (Typer): analyze / smells / report
samples/             # archivos de ejemplo para prueba
tests/               # suite de pruebas (pytest)
```

El diseño es **modular**: los detectores de métricas son independientes entre sí y se
invocan desde `cli.py`. Para agregar un nuevo detector basta con crear un módulo en
`src/metrics/` que acepte la lista de `NormalizedToken` y devuelva un dataclass con el
resultado.

---

## Restricciones de diseño

- **Solo análisis léxico**: se usa Pygments únicamente para tokenizar. No se construye
  AST ni se realiza análisis sintáctico.
- **Solo análisis estático**: el código analizado jamás se ejecuta.
- La entrada puede ser un archivo o un directorio (se recorre recursivamente).
