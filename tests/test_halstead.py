"""Tests para métricas de Halstead."""

import pytest
from src.core.lexer import tokenize
from src.metrics.halstead import compute_halstead


def _tokens(source: str, filename: str = "test.py"):
    return tokenize(source, filename)


def test_empty_source_no_crash():
    """Archivo vacío no debe lanzar excepciones."""
    result = compute_halstead([])
    assert result.volume == 0.0
    assert result.difficulty == 0.0
    assert result.effort == 0.0


def test_simple_expression():
    """Una expresión simple debe producir métricas positivas."""
    tokens = _tokens("x = 1 + 2")
    result = compute_halstead(tokens)
    assert result.N1 > 0, "Debe haber operadores"
    assert result.N2 > 0, "Debe haber operandos"
    assert result.volume > 0.0


def test_vocabulary_equals_n1_plus_n2():
    tokens = _tokens("a = b + c * d")
    result = compute_halstead(tokens)
    assert result.vocabulary == result.n1 + result.n2


def test_length_equals_N1_plus_N2():
    tokens = _tokens("a = b + c * d")
    result = compute_halstead(tokens)
    assert result.length == result.N1 + result.N2


def test_repeated_operators_increase_N1_not_n1():
    """Repetir el mismo operador aumenta N1 pero no n1."""
    tokens_one = _tokens("a + b")
    tokens_two = _tokens("a + b + c + d")
    r1 = compute_halstead(tokens_one)
    r2 = compute_halstead(tokens_two)
    assert r2.N1 > r1.N1
    # n1 (distintos) no debe crecer mucho (solo "+")
    assert r2.n1 <= r1.n1 + 1


def test_volume_grows_with_more_code():
    small = compute_halstead(_tokens("x = 1"))
    large = compute_halstead(_tokens("x = 1 + 2 * 3 - 4 / 5 + (a + b) * c"))
    assert large.volume > small.volume


def test_effort_is_difficulty_times_volume():
    tokens = _tokens("result = (a + b) * (c - d) / e")
    r = compute_halstead(tokens)
    assert abs(r.effort - r.difficulty * r.volume) < 1e-9
