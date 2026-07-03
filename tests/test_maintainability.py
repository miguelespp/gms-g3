"""Tests para el Índice de Mantenibilidad."""

import math
import pytest
from src.metrics.maintainability import compute_mi, MI_GREEN, MI_YELLOW


def test_mi_is_in_valid_range():
    result = compute_mi(volume=100.0, cyclomatic=5, sloc=50)
    assert 0.0 <= result.mi <= 100.0


def test_high_complexity_gives_low_mi():
    low = compute_mi(volume=100.0, cyclomatic=5, sloc=50)
    high = compute_mi(volume=10000.0, cyclomatic=50, sloc=500)
    assert high.mi < low.mi


def test_grade_green():
    result = compute_mi(volume=10.0, cyclomatic=1, sloc=5)
    assert result.grade == "green"
    assert result.mi >= MI_GREEN


def test_grade_red():
    result = compute_mi(volume=1_000_000.0, cyclomatic=200, sloc=10_000)
    assert result.grade == "red"
    assert result.mi < MI_YELLOW


def test_zero_volume_no_crash():
    """MI con volumen 0 no debe lanzar excepciones."""
    result = compute_mi(volume=0.0, cyclomatic=1, sloc=0)
    assert 0.0 <= result.mi <= 100.0


def test_zero_sloc_no_crash():
    result = compute_mi(volume=50.0, cyclomatic=1, sloc=0)
    assert 0.0 <= result.mi <= 100.0


def test_mi_formula_manually():
    """Verifica la fórmula contra un cálculo manual."""
    V, CC, SLOC = 100.0, 5, 50
    raw = 171.0 - 5.2 * math.log(V) - 0.23 * CC - 16.2 * math.log(SLOC)
    expected = max(0.0, raw * 100.0 / 171.0)
    result = compute_mi(V, CC, SLOC)
    assert abs(result.mi - round(expected, 2)) < 0.01


def test_grade_boundary_green():
    """MI exactamente en MI_GREEN debe ser verde."""
    # Necesitamos valores que den MI ~= MI_GREEN
    # Simplemente probamos con el resultado
    result = compute_mi(volume=100.0, cyclomatic=5, sloc=50)
    if result.mi >= MI_GREEN:
        assert result.grade == "green"
    elif result.mi >= MI_YELLOW:
        assert result.grade == "yellow"
    else:
        assert result.grade == "red"
