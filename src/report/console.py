"""Genera la tabla Rich con ranking de archivos por Índice de Mantenibilidad."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich import box

from src.metrics.maintainability import MI_GREEN, MI_YELLOW


@dataclass
class FileReport:
    path: Path
    sloc: int
    cyclomatic: int
    volume: float
    comment_ratio: float
    mi: float
    grade: str  # "green" | "yellow" | "red"


_GRADE_COLOR = {
    "green": "green",
    "yellow": "yellow",
    "red": "red",
}

_GRADE_ICON = {
    "green": "OK",
    "yellow": "WARN",
    "red": "RISK",
}


def render_table(reports: list[FileReport], console: Console | None = None) -> None:
    """Imprime la tabla de resultados ordenada por MI ascendente (más riesgoso primero)."""
    if console is None:
        console = Console()

    sorted_reports = sorted(reports, key=lambda r: r.mi)

    table = Table(
        title="[bold]Indice de Mantenibilidad -- Ranking de archivos[/bold]",
        box=box.ROUNDED,
        show_lines=True,
        highlight=True,
    )

    table.add_column("Archivo", style="cyan", no_wrap=True, min_width=20)
    table.add_column("SLOC", justify="right")
    table.add_column("CC", justify="right")
    table.add_column("Vol. Halstead", justify="right")
    table.add_column("% Comentarios", justify="right")
    table.add_column("MI", justify="right")
    table.add_column("Estado", justify="center")

    for r in sorted_reports:
        color = _GRADE_COLOR[r.grade]
        icon = _GRADE_ICON[r.grade]
        mi_str = f"[{color} bold]{r.mi:.1f}[/{color} bold]"
        status = f"[{color}]{icon}[/{color}]"

        table.add_row(
            r.path.name,
            str(r.sloc),
            str(r.cyclomatic),
            f"{r.volume:.0f}",
            f"{r.comment_ratio * 100:.1f}%",
            mi_str,
            status,
        )

    console.print()
    console.print(table)
    console.print(
        f"  [green]OK[/green]   Mantenible (MI >= {MI_GREEN})  "
        f"[yellow]WARN[/yellow] Moderado ({MI_YELLOW}-{MI_GREEN - 1})  "
        f"[red]RISK[/red] Riesgoso (MI < {MI_YELLOW})"
    )
    console.print()
