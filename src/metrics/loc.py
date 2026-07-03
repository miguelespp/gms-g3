"""Métricas de líneas de código (LOC) a partir del texto fuente y tokens."""

from __future__ import annotations

import math
from dataclasses import dataclass

from pygments.token import Token

from src.core.lexer import NormalizedToken


@dataclass(frozen=True)
class LOCMetrics:
    total: int           # líneas totales (incluyendo blancas)
    blank: int           # líneas en blanco
    comment: int         # líneas de comentario
    sloc: int            # Source Lines of Code (no blancas, no comentario)
    comment_ratio: float # comment / (comment + sloc), o 0 si no hay líneas


def compute_loc(source: str, tokens: list[NormalizedToken]) -> LOCMetrics:
    """Calcula métricas LOC combinando el texto fuente con los tokens de Pygments."""
    lines = source.splitlines()
    total = len(lines)

    # Líneas que contienen al menos un token de comentario
    comment_lines: set[int] = set()
    for tok in tokens:
        if tok.ttype in Token.Comment:
            comment_lines.add(tok.line)

    blank = sum(1 for ln in lines if not ln.strip())
    comment = len(comment_lines)
    sloc = max(0, total - blank - comment)

    denominator = comment + sloc
    comment_ratio = comment / denominator if denominator > 0 else 0.0

    return LOCMetrics(
        total=total,
        blank=blank,
        comment=comment,
        sloc=sloc,
        comment_ratio=comment_ratio,
    )
