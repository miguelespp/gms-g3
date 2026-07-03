"""Tests para métricas LOC."""

from src.core.lexer import tokenize
from src.metrics.loc import compute_loc


def _measure(source: str, filename: str = "test.py"):
    tokens = tokenize(source, filename)
    return compute_loc(source, tokens)


def test_empty_file():
    result = _measure("")
    assert result.total == 0
    assert result.blank == 0
    assert result.comment == 0
    assert result.sloc == 0
    assert result.comment_ratio == 0.0


def test_blank_lines_counted():
    source = "x = 1\n\n\ny = 2\n"
    result = _measure(source)
    assert result.blank == 2
    assert result.total == 4


def test_comment_lines_counted():
    source = "# This is a comment\nx = 1  # inline\ny = 2\n"
    result = _measure(source)
    assert result.comment >= 1


def test_sloc_excludes_blanks_and_comments():
    source = "# comment\n\nx = 1\ny = 2\n"
    result = _measure(source)
    # 2 SLOC: x=1 and y=2
    assert result.sloc == 2


def test_comment_ratio_is_between_0_and_1():
    source = "# a\n# b\nx = 1\ny = 2\n"
    result = _measure(source)
    assert 0.0 <= result.comment_ratio <= 1.0


def test_total_equals_sum_of_parts():
    source = "# c\n\nx = 1\n"
    result = _measure(source)
    assert result.total == result.blank + result.comment + result.sloc


def test_only_comments():
    source = "# line1\n# line2\n# line3\n"
    result = _measure(source)
    assert result.comment == 3
    assert result.sloc == 0
    assert result.comment_ratio == 1.0
