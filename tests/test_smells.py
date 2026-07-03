"""Tests para el detector de code smells."""

from src.core.lexer import tokenize
from src.metrics.smells import SmellConfig, detect_smells, summarize_by_rule


def _detect(source: str, filename: str = "test.py", **kwargs):
    tokens = tokenize(source, filename)
    config = SmellConfig(**kwargs) if kwargs else SmellConfig()
    return detect_smells(source, tokens, config)


def _rules(smells) -> set[str]:
    return {s.rule for s in smells}


# --- magic numbers ---------------------------------------------------------

def test_magic_number_detected():
    smells = _detect("x = 42\n")
    assert "magic-number" in _rules(smells)


def test_allowed_numbers_not_flagged():
    smells = _detect("x = 0\ny = 1\nz = 2\n")
    assert "magic-number" not in _rules(smells)


def test_custom_allowed_numbers():
    smells = _detect("x = 42\n", allowed_numbers=frozenset({"0", "1", "2", "42"}))
    assert "magic-number" not in _rules(smells)


# --- dangerous functions ---------------------------------------------------

def test_dangerous_function_detected():
    smells = _detect("result = eval(user_input)\n")
    dangerous = [s for s in smells if s.rule == "dangerous-function"]
    assert len(dangerous) == 1
    assert dangerous[0].severity == "critical"


def test_dangerous_name_without_call_not_flagged():
    # 'eval' usado como identificador, no como llamada
    smells = _detect("eval = 5\n")
    assert "dangerous-function" not in _rules(smells)


# --- todo / commented code -------------------------------------------------

def test_todo_marker_detected():
    smells = _detect("# TODO: arreglar esto\nx = 1\n")
    todos = [s for s in smells if s.rule == "todo-marker"]
    assert len(todos) == 1


def test_fixme_and_hack_markers():
    smells = _detect("# FIXME urgente\n# HACK temporal\nx = 1\n")
    assert sum(1 for s in smells if s.rule == "todo-marker") == 2


def test_commented_code_detected():
    smells = _detect("# x = compute(a, b);\nx = 1\n")
    assert "commented-code" in _rules(smells)


def test_prose_comment_not_flagged_as_code():
    smells = _detect("# esta es una explicación normal\nx = 1\n")
    assert "commented-code" not in _rules(smells)


# --- nesting & long functions ---------------------------------------------

def test_deep_nesting_detected():
    source = (
        "def f():\n"
        "    if a:\n"
        "        if b:\n"
        "            if c:\n"
        "                if d:\n"
        "                    return 1\n"
    )
    smells = _detect(source, max_nesting_depth=3)
    assert "deep-nesting" in _rules(smells)


def test_shallow_nesting_not_flagged():
    source = "def f():\n    if a:\n        return 1\n"
    smells = _detect(source, max_nesting_depth=4)
    assert "deep-nesting" not in _rules(smells)


def test_long_function_detected():
    body = "\n".join(f"    x{i} = {i}" for i in range(50))
    source = f"def big():\n{body}\n"
    smells = _detect(source, long_function_lines=40)
    long_funcs = [s for s in smells if s.rule == "long-function"]
    assert len(long_funcs) == 1
    assert long_funcs[0].line == 1


def test_short_function_not_flagged():
    source = "def small():\n    return 1\n"
    smells = _detect(source, long_function_lines=40)
    assert "long-function" not in _rules(smells)


# --- delimiter balance -----------------------------------------------------

def test_unbalanced_open_delimiter():
    smells = _detect("x = (1 + 2\n", filename="t.c")
    assert "unbalanced-delimiters" in _rules(smells)


def test_unbalanced_close_delimiter():
    smells = _detect("x = 1 + 2)\n", filename="t.c")
    assert "unbalanced-delimiters" in _rules(smells)


def test_balanced_delimiters_ok():
    smells = _detect("x = (1 + [2, 3]) * {4}\n", filename="t.c")
    assert "unbalanced-delimiters" not in _rules(smells)


def test_delimiters_inside_string_ignored():
    smells = _detect('x = "((("\n', filename="t.py")
    assert "unbalanced-delimiters" not in _rules(smells)


# --- integración -----------------------------------------------------------

def test_clean_source_has_no_smells():
    source = "def add(a, b):\n    return a + b\n"
    assert _detect(source) == []


def test_summarize_by_rule():
    source = "x = 42\ny = 137\n"
    smells = _detect(source)
    counts = summarize_by_rule(smells)
    assert counts.get("magic-number") == 2
