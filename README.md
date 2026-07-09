# Code Anomaly Detector

Herramienta de deteccion de anomalias en codigo fuente orientada a la gestion
del mantenimiento de software. El proyecto aplica analisis estatico lexico para
calcular metricas de mantenibilidad, detectar code smells y generar reportes que
ayudan al programador a priorizar archivos con mayor riesgo de mantenimiento.

> Proyecto final - Gestion de Mantenimiento de Software

## Objetivo

Disenar e implementar una herramienta de soporte al programador para minimizar
posibles anomalias en el codigo fuente, sin ejecutar el programa analizado y sin
realizar analisis sintactico profundo.

La herramienta busca responder preguntas practicas de mantenimiento:

- Que archivos son mas dificiles de mantener?
- Donde existe mayor complejidad o deuda tecnica?
- Que anomalias deberian atenderse primero?
- Que accion de mejora se recomienda para cada archivo?

## Alcance Del Proyecto

Code Anomaly Detector permite:

- Analizar archivos individuales o directorios completos.
- Calcular el Indice de Mantenibilidad (MI).
- Calcular SLOC, complejidad ciclomatica aproximada, volumen Halstead y ratio de comentarios.
- Detectar code smells mediante reglas lexicas y textuales.
- Clasificar anomalias por severidad: critica, advertencia e informativa.
- Generar reportes en consola con tablas legibles.
- Emitir una recomendacion breve por archivo en el reporte integrado.

El proyecto no realiza:

- Ejecucion del programa analizado.
- Compilacion del codigo fuente analizado.
- Debugging.
- Correccion automatica del codigo.
- Analisis semantico profundo.
- Construccion de AST como estrategia principal de analisis.

## Cumplimiento Del Enunciado

| Requisito | Como lo cumple el proyecto |
|---|---|
| Herramienta de soporte al programador | Entrega reportes, metricas y recomendaciones. |
| Deteccion de anomalias | Identifica code smells y condiciones de baja mantenibilidad. |
| Codigo fuente como entrada | Recibe archivos o directorios de codigo fuente. |
| No considerar el programa en ejecucion | Aplica analisis estatico; nunca ejecuta el codigo analizado. |
| No considerar analisis sintactico | Usa tokenizacion, conteos y reglas heuristicas, sin depender de AST. |

## Enfoque De Analisis

El flujo general de procesamiento es:

```text
Codigo fuente
  -> Lectura de archivo o directorio
  -> Tokenizacion lexica con Pygments
  -> Calculo de metricas
  -> Deteccion de anomalias
  -> Reporte en consola
  -> Recomendacion de mantenimiento
```

Este enfoque permite inspeccionar el codigo como texto/tokenes, manteniendo la
herramienta simple, segura y alineada con el analisis estatico solicitado.

## Requisitos

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) recomendado, o `pip`

## Instalacion

Con `uv`:

```bash
uv sync --extra dev
```

Con `pip`:

```bash
pip install -e ".[dev]"
```

## Uso

El proyecto expone una interfaz de linea de comandos con Typer. Puede ejecutarse
como modulo de Python:

```bash
python -m src.cli --help
```

Tambien puede instalarse como comando:

```bash
code-anomaly --help
```

### Analisis De Mantenibilidad

Calcula metricas por archivo y muestra un ranking ordenado por MI ascendente, es
decir, del archivo mas riesgoso al mas mantenible.

```bash
python -m src.cli analyze samples/
```

Analizar un archivo individual:

```bash
python -m src.cli analyze samples/messy_example.py
```

Agregar extensiones adicionales:

```bash
python -m src.cli analyze src/ --ext .vue,.svelte
```

El reporte `analyze` muestra:

- Archivo.
- SLOC.
- Complejidad ciclomatica aproximada.
- Volumen Halstead.
- Porcentaje de comentarios.
- Indice de Mantenibilidad.
- Estado del archivo.

### Deteccion De Code Smells

Detecta anomalias por archivo y las agrupa por severidad.

```bash
python -m src.cli smells samples/
```

Ajustar umbrales de deteccion:

```bash
python -m src.cli smells src/ --max-func-lines 60 --max-nesting 5
```

Opciones principales:

- `--max-func-lines`: umbral para detectar funciones largas.
- `--max-nesting`: profundidad maxima de anidamiento permitida.
- `--ext`: extensiones adicionales separadas por coma.

Reglas detectadas:

| Regla | Severidad | Que detecta |
|---|---|---|
| `dangerous-function` | Critica | Llamadas riesgosas como `gets`, `strcpy`, `system` o `eval`. |
| `unbalanced-delimiters` | Critica | Parentesis, llaves o corchetes sin pareja. |
| `complex-function` | Advertencia | Funcion que supera simultaneamente LOC, complejidad ciclomatica y anidamiento. |
| `deep-nesting` | Advertencia | Anidamiento por encima del umbral configurado. |
| `long-function` | Advertencia | Funcion con mas lineas que el limite permitido. |
| `magic-number` | Informativa | Literales numericos fuera de la lista permitida. |
| `commented-code` | Informativa | Comentarios que parecen codigo comentado. |
| `todo-marker` | Informativa | Marcadores como `TODO`, `FIXME`, `HACK` o `XXX`. |

### Reporte Integrado

Combina mantenibilidad, smells y recomendaciones en una sola tabla.

```bash
python -m src.cli report samples/
```

El reporte integrado muestra:

- Archivo analizado.
- MI.
- Nivel de riesgo.
- Complejidad ciclomatica.
- Ratio de comentarios.
- Cantidad de anomalias criticas.
- Cantidad de advertencias.
- Cantidad de hallazgos informativos.
- Accion recomendada.

Ejemplos de acciones recomendadas:

- `Corregir criticos.`
- `Reducir tamano.`
- `Dividir funciones.`
- `Reducir anidamiento.`
- `Nombrar constantes.`
- `Sin urgencias.`

## Metricas Calculadas

| Metrica | Descripcion | Uso en mantenimiento |
|---|---|---|
| SLOC | Lineas efectivas de codigo, sin blancos ni comentarios. | Estima tamano real del archivo. |
| Complejidad ciclomatica | Aproximacion basada en tokens de decision. | Indica cantidad de caminos logicos. |
| Halstead Volume | Medida basada en operadores, operandos y vocabulario. | Estima complejidad lexica del codigo. |
| Ratio de comentarios | `comentarios / (comentarios + SLOC)`. | Complementa la evaluacion de comprensibilidad. |
| MI | Indice de Mantenibilidad normalizado. | Resume el riesgo de mantenimiento. |

### Indice De Mantenibilidad

El Indice de Mantenibilidad es la metrica central del proyecto porque se
relaciona directamente con el curso. La formula usada es:

```text
MI = max(0, (171 - 5.2*ln(V) - 0.23*CC - 16.2*ln(SLOC)) * 100 / 171)
```

Donde:

- `V` es el volumen Halstead.
- `CC` es la complejidad ciclomatica aproximada.
- `SLOC` son las lineas efectivas de codigo.

El ratio de comentarios se calcula y se muestra como metrica complementaria. No
altera la formula actual del MI, pero ayuda a interpretar la documentacion del
archivo.

### Umbrales De MI

| Estado | Rango | Interpretacion |
|---|---|---|
| Verde | MI >= 20 | Mantenible. |
| Amarillo | 10 <= MI < 20 | Riesgo moderado. |
| Rojo | MI < 10 | Dificil de mantener. |

## Code Smells Detectados

Las reglas detectadas se resumen en la seccion de uso del comando `smells`. Esta
parte explica con mayor detalle la regla compuesta principal del detector.

### Regla Compuesta `complex-function`

La regla `complex-function` sigue una estrategia compuesta: una funcion se marca
solo cuando supera al mismo tiempo tres condiciones:

```text
LOC alto AND complejidad ciclomatica alta AND anidamiento alto
```

Esto reduce falsos positivos. Por ejemplo, una funcion larga pero lineal no se
marca automaticamente como compleja si no tiene decisiones ni anidamiento
relevante.

## Recomendaciones Del Reporte Integrado

El reporte integrado asigna una recomendacion por archivo usando prioridades. El
orden general es:

1. Si hay smells criticos, recomienda corregirlos primero.
2. Si el MI es rojo, recomienda reducir tamano o complejidad.
3. Si hay funcion compleja, recomienda dividir funciones.
4. Si hay anidamiento profundo, recomienda reducir anidamiento.
5. Si hay funcion larga, recomienda separar responsabilidades.
6. Si hay numeros magicos, recomienda nombrar constantes.
7. Si no hay problemas relevantes, indica que no hay urgencias.

Este mecanismo convierte metricas tecnicas en una accion concreta de
mantenimiento.

## Arquitectura

```text
src/
  core/
    file_reader.py      # lectura de archivos y recorrido de directorios
    lexer.py            # tokenizacion lexica con Pygments
  metrics/
    halstead.py         # metricas de Halstead
    complexity.py       # complejidad ciclomatica aproximada
    loc.py              # LOC, SLOC, blancos, comentarios y ratio
    maintainability.py  # calculo del Indice de Mantenibilidad
    smells.py           # deteccion de code smells
  report/
    console.py          # ranking de mantenibilidad
    smells.py           # reporte de code smells
    summary.py          # reporte integrado y recomendaciones
  cli.py                # comandos analyze, smells y report
samples/                # archivos de ejemplo
tests/                  # pruebas automatizadas con pytest
```

El diseno es modular. Cada modulo tiene una responsabilidad clara:

- `core`: obtiene y tokeniza el codigo fuente.
- `metrics`: calcula indicadores y detecta anomalias.
- `report`: transforma resultados en tablas legibles.
- `cli.py`: coordina el flujo desde la linea de comandos.
- `tests`: valida el comportamiento de la herramienta.

## Pruebas

Ejecutar la suite completa:

```bash
pytest
```

Ejecutar con salida detallada:

```bash
pytest -v
```

Ejecutar con cobertura:

```bash
pytest --cov=src --cov-report=term-missing
```

Las pruebas cubren, entre otros aspectos:

- Calculo de LOC y ratio de comentarios.
- Calculo de metricas de mantenibilidad.
- Deteccion de smells.
- Reglas de recomendacion del reporte integrado.
- Renderizado del resumen global.

## Ejemplo De Demo Para Exposicion

1. Mostrar los archivos de ejemplo en `samples/`.
2. Ejecutar el ranking de mantenibilidad:

```bash
python -m src.cli analyze samples/
```

3. Ejecutar la deteccion de smells:

```bash
python -m src.cli smells samples/
```

4. Ejecutar el reporte integrado:

```bash
python -m src.cli report samples/
```

5. Explicar como la herramienta ayuda a decidir que archivo revisar primero.

## Relacion Con Gestion De Mantenimiento De Software

Code Anomaly Detector se relaciona con el mantenimiento de software porque apoya:

- Mantenimiento preventivo: detecta riesgos antes de que generen fallos.
- Analizabilidad: facilita comprender el estado interno del codigo.
- Modificabilidad: identifica archivos dificiles de cambiar.
- Testeabilidad: senala funciones complejas que pueden requerir mas pruebas.
- Gestion de deuda tecnica: ayuda a priorizar refactorizaciones.

El aporte principal del proyecto es transformar codigo fuente en informacion
accionable para mantenimiento.

## Limitaciones

- La complejidad ciclomatica es aproximada porque se basa en conteo lexico.
- La deteccion de funciones depende de patrones textuales y tokens, no de AST.
- Algunas reglas pueden generar falsos positivos o falsos negativos.
- El ratio de comentarios no garantiza calidad documental; solo mide proporcion.
- El analisis esta orientado a soporte y priorizacion, no a verificacion formal.

## Trabajo Futuro

- Exportar reportes a JSON, HTML o PDF.
- Integrar la herramienta en pipelines CI/CD.
- Permitir configuracion externa de reglas y umbrales.
- Agregar historial de metricas por version.
- Ampliar soporte y calibracion por lenguaje.
- Incorporar mas metricas complementarias de mantenibilidad.
