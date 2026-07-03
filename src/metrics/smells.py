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


def _detect_long_functions(
    source_lines: list[str],
    tokens: list[NormalizedToken],
    code_lines: set[int],
    keywords: frozenset[str],
    threshold: int,
) -> list[Smell]:
    """Detecta funciones más largas que *threshold* midiendo el bloque por indentación."""
    out: list[Smell] = []
    total = len(source_lines)

    for tok in tokens:
        if tok.ttype not in Token.Keyword or tok.value not in keywords:
            continue
        start = tok.line
        if start < 1 or start > total:
            continue
        start_indent = _indent_of(source_lines[start - 1])

        # El bloque termina en la primera línea de código con indentación <= la firma.
        end = total
        for j in range(start + 1, total + 1):
            if j not in code_lines:
                continue
            if _indent_of(source_lines[j - 1]) <= start_indent:
                end = j - 1
                break

        length = end - start + 1
        if length > threshold:
            out.append(
                Smell(
                    rule="long-function",
                    severity="warning",
                    line=start,
                    message=f"Función de ~{length} líneas (umbral {threshold}).",
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

    smells: list[Smell] = []
    smells += _detect_magic_numbers(tokens, config.allowed_numbers)
    smells += _detect_dangerous_functions(tokens, config.dangerous_functions)
    smells += _detect_comment_smells(tokens)
    smells += _detect_unbalanced_delimiters(tokens)
    smells += _detect_deep_nesting(source_lines, code_lines, config.max_nesting_depth)
    smells += _detect_long_functions(
        source_lines, tokens, code_lines, config.function_keywords,
        config.long_function_lines,
    )

    smells.sort(key=lambda s: (s.line, SEVERITY_ORDER.get(s.severity, 9)))
    return smells


def summarize_by_rule(smells: Iterable[Smell]) -> dict[str, int]:
    """Cuenta hallazgos agrupados por regla."""
    counts: dict[str, int] = {}
    for s in smells:
        counts[s.rule] = counts.get(s.rule, 0) + 1
    return counts
