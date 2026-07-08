"""Tests para recomendaciones del reporte integrado."""

from pathlib import Path

from rich.console import Console

from src.metrics.smells import Smell
from src.report.summary import IntegratedReport, recommend, render_integrated_report


def _report(**kwargs) -> IntegratedReport:
    base = {
        "path": Path("sample.py"),
        "sloc": 10,
        "cyclomatic": 2,
        "volume": 100.0,
        "mi": 80.0,
        "grade": "green",
        "smells": [],
    }
    base.update(kwargs)
    return IntegratedReport(**base)


# Verifica que los hallazgos críticos tengan prioridad sobre cualquier otra recomendación.
def test_recommend_prioritizes_critical_smells():
    report = _report(
        smells=[
            Smell(
                rule="dangerous-function",
                severity="critical",
                line=1,
                message="Llamada peligrosa.",
            )
        ]
    )

    assert recommend(report) == "Corregir criticos."


# Verifica que una función compleja genere una recomendación de división/refactorización.
def test_recommend_complex_function():
    report = _report(
        smells=[
            Smell(
                rule="complex-function",
                severity="warning",
                line=1,
                message="Función compleja.",
            )
        ]
    )

    assert recommend(report) == "Dividir funciones."


# Verifica que un archivo sin anomalías relevantes no proponga acciones urgentes.
def test_recommend_clean_report():
    assert recommend(_report()) == "Sin urgencias."


# Verifica que el reporte integrado incluya el resumen global al final de la tabla.
def test_render_integrated_report_includes_global_summary():
    console = Console(record=True, width=120)

    render_integrated_report([_report()], console)

    output = console.export_text()
    assert "Archivos: 1" in output
    assert "MI promedio: 80.0" in output
    assert "Archivo con menor MI: sample.py" in output
