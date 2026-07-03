"""Tests para complejidad ciclomática aproximada."""

from src.core.lexer import tokenize
from src.metrics.complexity import compute_complexity


def _tokens(source: str, filename: str = "test.py"):
    return tokenize(source, filename)


def test_no_branches_returns_one():
    """Código sin ramificaciones debe retornar CC = 1."""
    tokens = _tokens("x = 1\ny = 2\nz = x + y")
    assert compute_complexity(tokens) == 1


def test_single_if_adds_one():
    source = "if x > 0:\n    y = 1"
    tokens = _tokens(source)
    assert compute_complexity(tokens) == 2


def test_if_elif_else():
    source = (
        "if x > 0:\n"
        "    y = 1\n"
        "elif x < 0:\n"
        "    y = -1\n"
        "else:\n"
        "    y = 0\n"
    )
    tokens = _tokens(source)
    # if=1, elif=1 → CC = 3  (else no es punto de decisión en McCabe)
    assert compute_complexity(tokens) == 3


def test_for_while_increase_cc():
    source = "for i in range(10):\n    while True:\n        break"
    tokens = _tokens(source)
    cc = compute_complexity(tokens)
    assert cc >= 3


def test_logical_operators_count():
    source = "if a and b or c:\n    pass"
    tokens = _tokens(source)
    cc = compute_complexity(tokens)
    # if=1, and=1, or=1 → CC = 4
    assert cc == 4


def test_empty_tokens_returns_one():
    assert compute_complexity([]) == 1


def test_custom_decision_tokens():
    """Soporte para lista de decisión personalizada."""
    from pygments.token import Token
    custom = frozenset({(Token.Keyword, "if")})
    source = "if x:\n    pass\nfor i in range(5):\n    pass"
    tokens = _tokens(source)
    cc = compute_complexity(tokens, decision_tokens=custom)
    # Solo "if" cuenta
    assert cc == 2
