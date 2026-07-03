# Guion de demostración — Detector de Anomalías en Código

> Duración objetivo: **6–8 minutos**. Ten dos comandos clave copiados y una
> terminal con fuente grande. Verifica **antes** que corres con Python **3.11+**.

---

## 0. Preparación (antes de exponer)

```bash
# Verifica versión (debe ser 3.11+)
python --version

# Instala dependencias
uv sync --extra dev        # o:  pip install -e ".[dev]"

# Prueba rápida de humo (que todo corra)
pytest -q
python -m src.cli analyze samples/
python -m src.cli smells  samples/
```

Deja la terminal **limpia** y con el prompt en la raíz del proyecto.

---

## 1. Contexto y objetivo (30–45 s)

> "El objetivo del trabajo es una **herramienta de soporte al programador** para
> minimizar anomalías en el código fuente. A medida que un programa crece, revisarlo
> se vuelve caro. Nuestra herramienta analiza el código **de forma estática y léxica**
> —sin ejecutarlo y sin análisis sintáctico, tal como pide el enunciado— y detecta
> dos cosas: **qué tan mantenible es cada archivo** y **qué malos patrones (code smells)
> contiene**."

Menciona la restricción como decisión de diseño, no como limitación.

---

## 2. Índice de Mantenibilidad (1 min) — el ancla del curso

```bash
python -m src.cli analyze samples/
```

**Qué señalar:**
- La tabla ordena los archivos **del menos al más mantenible** (MI ascendente).
- Columnas: **SLOC, Complejidad Ciclomática, Volumen de Halstead, % comentarios, MI**.
- El **MI** usa la fórmula normalizada de Microsoft (0–100). Todo sale de **contar tokens** (Halstead) y **palabras clave de decisión** (complejidad) — 100% léxico.

> "Esto le dice al programador *dónde* está el riesgo de mantenimiento."

---

## 3. Detección de code smells (2–3 min) — el núcleo de la demo

### 3a. Un archivo relativamente limpio

```bash
python -m src.cli smells samples/clean_example.py
```

> "En código bien escrito casi no aparecen smells. El único hallazgo es el `0.5` de
> `int(n**0.5)` marcado como número mágico: es un **falso positivo esperado** —un
> análisis puramente léxico no sabe que es la raíz cuadrada. Es el *trade-off*
> conocido precisión/exhaustividad de este enfoque."

*(Reconocer el falso positivo tú mismo suma nota.)*

### 3b. Un archivo intencionalmente sucio

```bash
python -m src.cli smells samples/messy_example.py
```

**Qué señalar** (de arriba hacia abajo, por severidad):
- 🔴 **críticos** primero (si el archivo los tuviera): funciones peligrosas, delimitadores desbalanceados.
- 🟡 **`complex-function`** en la función `proc` → *"48 líneas, CC=21, anidamiento 13"*.
- 🔵 **`magic-number`**, **anidamiento**, etc.
- Al final, el **resumen global** con el conteo por regla.

### 3c. El ejemplo que dispara TODAS las reglas

```bash
python -m src.cli smells samples/smelly_example.c
```

> "Este archivo en C tiene a propósito de todo: `strcpy` y `system` (funciones
> peligrosas → **crítico**), un paréntesis sin cerrar (**delimitadores
> desbalanceados**), anidamiento profundo, números mágicos, código comentado y
> marcadores `TODO`/`FIXME`."

---

## 4. La pieza técnica fuerte (1–1.5 min) — regla compuesta

> "La regla estrella es **`complex-function`**. En vez de mirar una sola métrica,
> combina **tres** con AND lógico: **líneas de código Y complejidad ciclomática Y
> anidamiento**. Es una *detection strategy* de **Lanza & Marinescu**, el estado del
> arte en detección basada en métricas."

**Puntos a recalcar:**
- Una función **larga pero simple NO se marca** → reduce falsos positivos.
- Cuando una función es `complex-function`, se **omite** el `long-function` redundante.
- **Reutiliza** el `compute_complexity` del módulo de mantenibilidad → los dos
  módulos del proyecto quedan **integrados**.

*(Opcional: abre [src/metrics/smells.py](src/metrics/smells.py) y muestra
`_detect_complex_functions` — las tres condiciones con `and`.)*

---

## 5. Calidad del trabajo (30 s)

```bash
pytest -q
```

> "Toda la lógica está cubierta con **pruebas unitarias**: 22 tests solo para el
> detector de smells, con casos positivos y negativos por cada regla. El diseño es
> **modular**: cada regla es independiente y consume la misma lista de tokens."

---

## 6. Cierre honesto (30 s)

> "Las herramientas industriales como PMD o SonarQube usan **AST** para más
> precisión. Nosotros usamos **tokens e indentación** por la restricción del
> enunciado, lo que nos sitúa en la misma familia que los detectores de clones
> basados en tokens. Es un enfoque válido, documentado en la literatura, y con un
> trade-off precisión/exhaustividad que asumimos conscientemente."

---

## Comandos de respaldo (por si preguntan)

```bash
# Ajustar umbrales en vivo
python -m src.cli smells samples/ --max-func-lines 60 --max-nesting 5

# Analizar el propio código de la herramienta
python -m src.cli analyze src/
python -m src.cli smells  src/

# Otras extensiones
python -m src.cli smells proyecto/ --ext .vue,.svelte
```

## Preguntas probables y respuestas cortas

| Pregunta | Respuesta |
|----------|-----------|
| ¿Por qué no usan AST? | El enunciado prohíbe el análisis sintáctico; usamos análisis léxico (tokens + indentación). |
| ¿Cómo miden complejidad sin ejecutar? | Contando **palabras clave de decisión** (`if`, `for`, `&&`, `?`…) — es la aproximación de McCabe. |
| ¿Y los falsos positivos? | Existen (ej. el `0.5`). La regla compuesta `complex-function` los reduce al exigir 3 métricas a la vez. |
| ¿Funciona en varios lenguajes? | Sí: usa Pygments para tokenizar; probado en Python, JS y C. |
| ¿Se puede extender? | Sí: agregar una regla es una función que recibe la lista de tokens y devuelve `Smell`. |
