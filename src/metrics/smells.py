"""Detector de *code smells* por patrones léxicos y textuales.

No construye AST ni ejecuta el código: combina la lista de ``NormalizedToken``
(igual que el resto de métricas) con el texto fuente para medir indentación,
tal como hace :mod:`src.metrics.loc`.

Reglas implementadas
--------------------
- ``magic-number``        : literales numéricos "mágicos" (fuera de la whitelist).
- ``long-function``       : funciones con más líneas que el umbral.
- ``deep-nesting``        : anidamiento (por indentación) que excede el umbral.
- ``commented-code``      : comentarios que parecen código comentado.
- ``todo-marker``         : marcadores TODO / FIXME / HACK / XXX.
- ``dangerous-function``  : llamadas a funciones inseguras (gets, strcpy, eval…).
- ``unbalanced-delimiters``: paréntesis / llaves / corchetes desbalanceados.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

from pygments.token import Token

from src.core.lexer import NormalizedToken
from src.metrics.complexity import compute_complexity


# Severidades ordenadas de mayor a menor gravedad (para priorizar/ordenar).
SEVERITY_ORDER: dict[str, int] = {"critical": 0, "warning": 1, "info": 2}


@dataclass(frozen=True)
class Smell:
    rule: str       # identificador de la regla, p. ej. "magic-number"
    severity: str   # "critical" | "warning" | "info"
    line: int       # línea 1-based; 0 indica un hallazgo a nivel de archivo
    message: str


DEFAULT_ALLOWED_NUMBERS: frozenset[str] = frozenset({"0", "1", "2", "-1", "1.0", "0.0"})

DEFAULT_DANGEROUS_FUNCTIONS: frozenset[str] = frozenset(
    {
        "gets", "strcpy", "strcat", "sprintf", "scanf", "gets_s",
        "memcpy", "alloca", "system", "popen",
        "eval", "exec", "execfile", "compile",
        "pickle", "marshal", "os.system", "subprocess",
        "shell_exec", "passthru", "assert",
    }
)

DEFAULT_FUNCTION_KEYWORDS: frozenset[str] = frozenset(
    {"def", "function", "func", "fn", "sub"}
)

_MARKER_RE = re.compile(r"\b(TODO|FIXME|HACK|XXX)\b", re.IGNORECASE)

_CODE_LIKE_RE = re.compile(
    r"""
    [;{}]\s*$                                   # termina en ; { o }
    | ^\s*(if|for|while|return|else|def|function|var|let|const|int|
           public|private|class|import|print)\b # arranca con keyword de código
    | =[^=]                                       # asignación (evita ==)
    | \)\s*[{;:]?\s*$                             # cierre de llamada/bloque
    """,
    re.VERBOSE,
)

_DELIMS: dict[str, str] = {")": "(", "]": "[", "}": "{"}
_OPENERS: frozenset[str] = frozenset({"(", "[", "{"})


@dataclass(frozen=True)
class SmellConfig:
    long_function_lines: int = 40
    max_nesting_depth: int = 4
    allowed_numbers: frozenset[str] = DEFAULT_ALLOWED_NUMBERS
    dangerous_functions: frozenset[str] = DEFAULT_DANGEROUS_FUNCTIONS
    function_keywords: frozenset[str] = DEFAULT_FUNCTION_KEYWORDS
    # Regla compuesta "complex-function" (detection strategy Lanza & Marinescu):
    # se dispara solo cuando las TRES métricas superan su umbral a la vez.
    complex_min_loc: int = 30
    complex_min_cyclomatic: int = 8
    complex_min_nesting: int = 3


def _indent_of(line: str) -> int:
    """Ancho de la indentación (tabs expandidos a 4)."""
    expanded = line.expandtabs(4)
    return len(expanded) - len(expanded.lstrip())


def _code_line_numbers(tokens: list[NormalizedToken]) -> set[int]:
    """Líneas que contienen al menos un token que NO es comentario."""
    lines: set[int] = set()
    for tok in tokens:
        if tok.ttype not in Token.Comment:
            lines.add(tok.line)
    return lines


def _detect_magic_numbers(
    tokens: list[NormalizedToken], allowed: frozenset[str]
) -> list[Smell]:
    out: list[Smell] = []
    for tok in tokens:
        if tok.ttype in Token.Number and tok.value not in allowed:
            out.append(
                Smell(
                    rule="magic-number",
                    severity="info",
                    line=tok.line,
                    message=f"Número mágico '{tok.value}' — considere una constante con nombre.",
                )
            )
    return out


def _detect_dangerous_functions(
    tokens: list[NormalizedToken], dangerous: frozenset[str]
) -> list[Smell]:
    out: list[Smell] = []
    for i, tok in enumerate(tokens):
        if tok.ttype in Token.Name and tok.value in dangerous:
            nxt = tokens[i + 1] if i + 1 < len(tokens) else None
            if nxt is not None and nxt.value == "(":
                out.append(
                    Smell(
                        rule="dangerous-function",
                        severity="critical",
                        line=tok.line,
                        message=f"Llamada a función peligrosa '{tok.value}(...)'.",
                    )
                )
    return out


def _detect_comment_smells(tokens: list[NormalizedToken]) -> list[Smell]:
    out: list[Smell] = []
    for tok in tokens:
        if tok.ttype not in Token.Comment:
            continue
        text = tok.value.strip()
        stripped = text.lstrip("#/*! ").rstrip("*/ ").strip()

        marker = _MARKER_RE.search(text)
        if marker:
            out.append(
                Smell(
                    rule="todo-marker",
                    severity="info",
                    line=tok.line,
                    message=f"Marcador '{marker.group(1).upper()}' pendiente de resolver.",
                )
            )
            continue  # no reportar el mismo comentario dos veces

        if len(stripped) >= 4 and _CODE_LIKE_RE.search(stripped):
            out.append(
                Smell(
                    rule="commented-code",
                    severity="info",
                    line=tok.line,
                    message="Posible código comentado — elimínelo o restáurelo.",
                )
            )
    return out


def _detect_unbalanced_delimiters(tokens: list[NormalizedToken]) -> list[Smell]:
    """Verifica el balance de () [] {} usando una pila (ignora strings/comentarios)."""
    stack: list[tuple[str, int]] = []
    out: list[Smell] = []
    for tok in tokens:
        if tok.ttype in Token.String or tok.ttype in Token.Comment:
            continue
        val = tok.value
        if val in _OPENERS:
            stack.append((val, tok.line))
        elif val in _DELIMS:
            expected = _DELIMS[val]
            if not stack or stack[-1][0] != expected:
                out.append(
                    Smell(
                        rule="unbalanced-delimiters",
                        severity="critical",
                        line=tok.line,
                        message=f"Delimitador de cierre '{val}' sin apertura correspondiente.",
                    )
                )
            else:
                stack.pop()

    for opener, line in stack:
        out.append(
            Smell(
                rule="unbalanced-delimiters",
                severity="critical",
                line=line,
                message=f"Delimitador de apertura '{opener}' sin cierre correspondiente.",
            )
        )
    return out


def _detect_deep_nesting(
    source_lines: list[str], code_lines: set[int], max_depth: int
) -> list[Smell]:
    """Anidamiento por indentación (pila de niveles al estilo INDENT/DEDENT)."""
    out: list[Smell] = []
    indent_stack: list[int] = [0]
    reported_from: int | None = None  # evita spamear líneas consecutivas profundas

    for idx, line in enumerate(source_lines, start=1):
        if idx not in code_lines or not line.strip():
            continue
        indent = _indent_of(line)

        if indent > indent_stack[-1]:
            indent_stack.append(indent)
        elif indent < indent_stack[-1]:
            while len(indent_stack) > 1 and indent_stack[-1] > indent:
                indent_stack.pop()

        depth = len(indent_stack)
        if depth > max_depth:
            if reported_from is None:
                out.append(
                    Smell(
                        rule="deep-nesting",
                        severity="warning",
                        line=idx,
                        message=f"Anidamiento profundo (nivel {depth} > {max_depth}).",
                    )
                )
                reported_from = idx
        else:
            reported_from = None
    return out


@dataclass(frozen=True)
class _FunctionSpan:
    name: str
    start: int  # línea de la firma (1-based)
    end: int    # última línea del cuerpo (1-based)


def _function_spans(
    source_lines: list[str],
    tokens: list[NormalizedToken],
    code_lines: set[int],
    keywords: frozenset[str],
) -> list[_FunctionSpan]:
    """Delimita cada función por su firma y su indentación (una sola vez)."""
    total = len(source_lines)
    spans: list[_FunctionSpan] = []

    for i, tok in enumerate(tokens):
        if tok.ttype not in Token.Keyword or tok.value not in keywords:
            continue
        start = tok.line
        if start < 1 or start > total:
            continue

        # El nombre es el primer token Name que sigue a la palabra clave.
        name = "<anónima>"
        for j in range(i + 1, min(i + 4, len(tokens))):
            if tokens[j].ttype in Token.Name:
                name = tokens[j].value
                break

        start_indent = _indent_of(source_lines[start - 1])
        # El bloque termina en la primera línea de código con indentación <= la firma.
        end = total
        for k in range(start + 1, total + 1):
            if k not in code_lines:
                continue
            if _indent_of(source_lines[k - 1]) <= start_indent:
                end = k - 1
                break

        spans.append(_FunctionSpan(name=name, start=start, end=end))
    return spans


def _max_nesting_in_span(
    source_lines: list[str], code_lines: set[int], span: _FunctionSpan
) -> int:
    """Niveles de anidamiento por indentación DENTRO de la función (cuerpo = nivel 1)."""
    base = _indent_of(source_lines[span.start - 1])
    stack: list[int] = [base]
    max_depth = 0

    for idx in range(span.start + 1, span.end + 1):
        if idx not in code_lines:
            continue
        line = source_lines[idx - 1]
        if not line.strip():
            continue
        indent = _indent_of(line)
        if indent > stack[-1]:
            stack.append(indent)
        elif indent < stack[-1]:
            while len(stack) > 1 and stack[-1] > indent:
                stack.pop()
        max_depth = max(max_depth, len(stack) - 1)
    return max_depth


def _cyclomatic_in_span(
    tokens: list[NormalizedToken], span: _FunctionSpan
) -> int:
    """Complejidad ciclomática de una función (reusa compute_complexity)."""
    body = [t for t in tokens if span.start <= t.line <= span.end]
    return compute_complexity(body)


def _detect_long_functions(
    spans: list[_FunctionSpan], threshold: int, skip_starts: set[int]
) -> list[Smell]:
    """Detecta funciones más largas que *threshold* (omite las ya marcadas como complejas)."""
    out: list[Smell] = []
    for span in spans:
        if span.start in skip_starts:
            continue
        length = span.end - span.start + 1
        if length > threshold:
            out.append(
                Smell(
                    rule="long-function",
                    severity="warning",
                    line=span.start,
                    message=f"Función '{span.name}' de ~{length} líneas (umbral {threshold}).",
                )
            )
    return out


def _detect_complex_functions(
    source_lines: list[str],
    tokens: list[NormalizedToken],
    code_lines: set[int],
    spans: list[_FunctionSpan],
    config: SmellConfig,
) -> list[Smell]:
    """Detection strategy compuesta: LOC ∧ Complejidad ∧ Anidamiento sobre umbral.

    Combina las tres métricas con AND lógico (estilo Lanza & Marinescu), de modo
    que una función larga PERO simple no se marca — reduce falsos positivos.
    """
    out: list[Smell] = []
    for span in spans:
        loc = span.end - span.start + 1
        cc = _cyclomatic_in_span(tokens, span)
        nesting = _max_nesting_in_span(source_lines, code_lines, span)

        if (
            loc > config.complex_min_loc
            and cc > config.complex_min_cyclomatic
            and nesting > config.complex_min_nesting
        ):
            out.append(
                Smell(
                    rule="complex-function",
                    severity="warning",
                    line=span.start,
                    message=(
                        f"Función '{span.name}' compleja: {loc} líneas, "
                        f"CC={cc}, anidamiento {nesting} "
                        f"(combina 3 métricas sobre umbral)."
                    ),
                )
            )
    return out


def detect_smells(
    source: str,
    tokens: list[NormalizedToken],
    config: SmellConfig = SmellConfig(),
) -> list[Smell]:
    """Ejecuta todas las reglas y devuelve los hallazgos ordenados por línea."""
    source_lines = source.splitlines()
    code_lines = _code_line_numbers(tokens)

    spans = _function_spans(source_lines, tokens, code_lines, config.function_keywords)

    smells: list[Smell] = []
    smells += _detect_magic_numbers(tokens, config.allowed_numbers)
    smells += _detect_dangerous_functions(tokens, config.dangerous_functions)
    smells += _detect_comment_smells(tokens)
    smells += _detect_unbalanced_delimiters(tokens)
    smells += _detect_deep_nesting(source_lines, code_lines, config.max_nesting_depth)

    complex_smells = _detect_complex_functions(
        source_lines, tokens, code_lines, spans, config
    )
    smells += complex_smells
    # No reportar long-function si la función ya se marcó como complex-function.
    complex_starts = {s.line for s in complex_smells}
    smells += _detect_long_functions(spans, config.long_function_lines, complex_starts)

    smells.sort(key=lambda s: (s.line, SEVERITY_ORDER.get(s.severity, 9)))
    return smells


def summarize_by_rule(smells: Iterable[Smell]) -> dict[str, int]:
    """Cuenta hallazgos agrupados por regla."""
    counts: dict[str, int] = {}
    for s in smells:
        counts[s.rule] = counts.get(s.rule, 0) + 1
    return counts
