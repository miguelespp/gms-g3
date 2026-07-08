"""Reporte integrado de mantenibilidad y code smells."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from rich import box
from rich.console import Console
from rich.table import Table

from src.metrics.smells import Smell


@dataclass
class IntegratedReport:
    path: Path
    sloc: int
    cyclomatic: int
    volume: float
    mi: float
    grade: str
    smells: list[Smell] = field(default_factory=list)

    @property
    def critical(self) -> int:
        return sum(1 for s in self.smells if s.severity == "critical")

    @property
    def warnings(self) -> int:
        return sum(1 for s in self.smells if s.severity == "warning")

    @property
    def info(self) -> int:
        return sum(1 for s in self.smells if s.severity == "info")


_GRADE_COLOR = {"green": "green", "yellow": "yellow", "red": "red"}
_GRADE_LABEL = {"green": "Bajo", "yellow": "Moderado", "red": "Alto"}


def recommend(report: IntegratedReport) -> str:
    """Devuelve una recomendación breve priorizando los riesgos más accionables."""
    rules = {s.rule for s in report.smells}

    if report.critical:
        return "Corregir criticos."
    if report.grade == "red":
        return "Reducir tamano."
    if "complex-function" in rules:
        return "Dividir funciones."
    if "deep-nesting" in rules:
        return "Reducir anidamiento."
    if "long-function" in rules:
        return "Separar funciones."
    if report.cyclomatic >= 15:
        return "Simplificar ramas."
    if report.volume >= 3000:
        return "Revisar tokens."
    if "magic-number" in rules:
        return "Nombrar constantes."
    if report.grade == "yellow" or report.warnings:
        return "Revisar warnings."
    if report.info:
        return "Limpieza menor."
    return "Sin urgencias."


def render_integrated_report(
    reports: list[IntegratedReport], console: Console | None = None
) -> None:
    """Imprime un resumen integrado ordenado por mayor riesgo."""
    if console is None:
        console = Console()

    ordered = sorted(
        reports,
        key=lambda r: (r.critical, r.warnings, -r.mi),
        reverse=True,
    )

    table = Table(
        title="[bold]Reporte integrado de anomalias[/bold]",
        box=box.ROUNDED,
        show_lines=True,
        highlight=True,
    )
    table.add_column("Archivo", style="cyan", no_wrap=True, min_width=17)
    table.add_column("MI", justify="right")
    table.add_column("R", justify="center")
    table.add_column("CC", justify="right")
    table.add_column("C", justify="right")
    table.add_column("WARN", justify="right")
    table.add_column("INFO", justify="right")
    table.add_column("Accion", no_wrap=True)

    for report in ordered:
        color = _GRADE_COLOR[report.grade]
        risk = _GRADE_LABEL[report.grade]
        table.add_row(
            report.path.name,
            f"[{color} bold]{report.mi:.1f}[/{color} bold]",
            f"[{color}]{risk}[/{color}]",
            str(report.cyclomatic),
            str(report.critical),
            str(report.warnings),
            str(report.info),
            recommend(report),
        )

    console.print()
    console.print(table)
    _render_global_summary(ordered, console)


def _render_global_summary(reports: list[IntegratedReport], console: Console) -> None:
    total_files = len(reports)
    total_smells = sum(len(r.smells) for r in reports)
    critical = sum(r.critical for r in reports)
    warnings = sum(r.warnings for r in reports)
    avg_mi = sum(r.mi for r in reports) / total_files if total_files else 0.0
    riskiest = min(reports, key=lambda r: r.mi, default=None)

    if riskiest is None:
        console.print("[yellow]No hay archivos para resumir.[/yellow]\n")
        return

    console.print(
        f"  Archivos: {total_files}   MI promedio: {avg_mi:.1f}   "
        f"Smells: {total_smells} ([red]{critical} criticos[/red], "
        f"[yellow]{warnings} advertencias[/yellow])"
    )
    console.print(
        f"  Archivo con menor MI: [cyan]{riskiest.path.name}[/cyan] "
        f"({riskiest.mi:.1f})"
    )
    console.print()
