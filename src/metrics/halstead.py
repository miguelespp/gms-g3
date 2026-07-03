"""Métricas de Halstead calculadas únicamente a partir de tokens léxicos de Pygments."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable

from pygments.token import Token, _TokenType

from src.core.lexer import NormalizedToken


# ---------------------------------------------------------------------------
# Clasificadores de tokens (configurables por lenguaje)
# ---------------------------------------------------------------------------

def _is_operator_default(ttype: _TokenType) -> bool:
    """Clasifica un tipo de token como operador."""
    return ttype in Token.Operator or ttype in Token.Keyword or ttype in Token.Punctuation


def _is_operand_default(ttype: _TokenType) -> bool:
    """Clasifica un tipo de token como operando."""
    return (
        ttype in Token.Name
        or ttype in Token.Literal
        or ttype in Token.Number
        or ttype in Token.String
        or ttype in Token.Literal.Number
        or ttype in Token.Literal.String
    )


TokenClassifier = Callable[[_TokenType], bool]


# ---------------------------------------------------------------------------
# Resultado
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class HalsteadMetrics:
    n1: int    # número de operadores distintos
    n2: int    # número de operandos distintos
    N1: int    # total de usos de operadores
    N2: int    # total de usos de operandos
    vocabulary: int    # n = n1 + n2
    length: int        # N = N1 + N2
    volume: float      # V = N · log2(n)
    difficulty: float  # D = (n1/2) · (N2/n2)
    effort: float      # E = D · V


# ---------------------------------------------------------------------------
# Cálculo
# ---------------------------------------------------------------------------

def compute_halstead(
    tokens: list[NormalizedToken],
    is_operator: TokenClassifier = _is_operator_default,
    is_operand: TokenClassifier = _is_operand_default,
) -> HalsteadMetrics:
    """Calcula métricas de Halstead a partir de una lista de tokens normalizados."""
    operators: dict[str, int] = {}
    operands: dict[str, int] = {}

    for tok in tokens:
        if is_operator(tok.ttype):
            operators[tok.value] = operators.get(tok.value, 0) + 1
        elif is_operand(tok.ttype):
            operands[tok.value] = operands.get(tok.value, 0) + 1

    n1 = len(operators)
    n2 = len(operands)
    N1 = sum(operators.values())
    N2 = sum(operands.values())

    vocabulary = n1 + n2
    length = N1 + N2

    # Evita log(0)
    volume = length * math.log2(vocabulary) if vocabulary > 1 else 0.0
    difficulty = (n1 / 2) * (N2 / n2) if n2 > 0 else 0.0
    effort = difficulty * volume

    return HalsteadMetrics(
        n1=n1, n2=n2, N1=N1, N2=N2,
        vocabulary=vocabulary, length=length,
        volume=volume, difficulty=difficulty, effort=effort,
    )
