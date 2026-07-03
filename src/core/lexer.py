"""Envuelve Pygments para exponer tokens normalizados con su categoría semántica."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pygments.lexers import get_lexer_for_filename, guess_lexer, TextLexer
from pygments.token import Token, _TokenType
from pygments.util import ClassNotFound


@dataclass(slots=True)
class NormalizedToken:
    ttype: _TokenType  # tipo Pygments (p. ej. Token.Keyword)
    value: str         # valor literal del token
    line: int          # línea de origen (1-based)


def tokenize(source: str, filename: str = "unknown") -> list[NormalizedToken]:
    """Tokeniza *source* usando Pygments y devuelve tokens sin espacios en blanco."""
    try:
        lexer = get_lexer_for_filename(filename, stripall=False)
    except ClassNotFound:
        try:
            lexer = guess_lexer(source)
        except ClassNotFound:
            lexer = TextLexer()

    tokens: list[NormalizedToken] = []
    line = 1
    for ttype, value in lexer.get_tokens(source):
        # Contar saltos de línea para llevar registro de línea actual
        newlines = value.count("\n")
        if ttype not in Token.Text.Whitespace and ttype not in Token.Text:
            if value.strip():  # omite tokens que son solo blancos
                tokens.append(NormalizedToken(ttype=ttype, value=value, line=line))
        line += newlines

    return tokens


def tokenize_file(path: Path) -> list[NormalizedToken]:
    """Conveniencia: lee *path* y tokeniza."""
    from src.core.file_reader import read_source
    source = read_source(path)
    return tokenize(source, filename=path.name)
