"""Tests para el lector de archivos."""

import pytest
from pathlib import Path
from src.core.file_reader import collect_files, read_source


def test_collect_single_file(tmp_path):
    f = tmp_path / "test.py"
    f.write_text("x = 1")
    result = collect_files(f)
    assert result == [f]


def test_collect_directory(tmp_path):
    (tmp_path / "a.py").write_text("pass")
    (tmp_path / "b.py").write_text("pass")
    (tmp_path / "ignore.txt").write_text("text")
    result = collect_files(tmp_path)
    names = {p.name for p in result}
    assert "a.py" in names
    assert "b.py" in names
    assert "ignore.txt" not in names


def test_collect_nonexistent_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        collect_files(tmp_path / "no_existe.py")


def test_read_source_utf8(tmp_path):
    f = tmp_path / "test.py"
    f.write_text("x = 'héllo'", encoding="utf-8")
    content = read_source(f)
    assert "héllo" in content


def test_empty_file(tmp_path):
    f = tmp_path / "empty.py"
    f.write_text("")
    content = read_source(f)
    assert content == ""
