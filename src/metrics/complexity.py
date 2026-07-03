"""Complejidad ciclomática aproximada via conteo de tokens de decisión léxicos."""

from __future__ import annotations

from pygments.token import Token, _TokenType

from src.core.lexer import NormalizedToken

# Tokens cuyo valor indica un punto de decisión.
# Configurable: se puede sobreescribir al llamar compute_complexity().
DEFAULT_DECISION_TOKENS: frozenset[tuple[_TokenType, str]] = frozenset(
    {
        # Python / Ruby / etc.
        (Token.Keyword, "if"),
        (Token.Keyword, "elif"),
        # else NO cuenta: es el camino implícito del if, no un punto de decisión nuevo
        (Token.Keyword, "for"),
        (Token.Keyword, "while"),
        (Token.Keyword, "except"),
        (Token.Keyword, "with"),
        (Token.Keyword, "case"),
        (Token.Keyword, "match"),
        # C / Java / JS / Go / etc.
        (Token.Keyword, "switch"),
        (Token.Keyword, "catch"),
        (Token.Keyword, "finally"),
        (Token.Keyword, "do"),
        (Token.Keyword, "goto"),
        # Operadores lógicos simbólicos (C/JS/Go/Java)
        (Token.Operator, "&&"),
        (Token.Operator, "||"),
        (Token.Operator, "?"),
        # Python: and/or son Token.Operator.Word en Pygments
        (Token.Operator.Word, "and"),
        (Token.Operator.Word, "or"),
    }
)


def compute_complexity(
    tokens: list[NormalizedToken],
    decision_tokens: frozenset[tuple[_TokenType, str]] = DEFAULT_DECISION_TOKENS,
) -> int:
    """Retorna la complejidad ciclomática aproximada.

    CC = 1 + número de tokens de decisión encontrados.
    """
    count = sum(
        1 for tok in tokens if (tok.ttype, tok.value) in decision_tokens
    )
    return 1 + count
