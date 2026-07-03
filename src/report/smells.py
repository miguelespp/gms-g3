"""Renderiza los *code smells* detectados en tablas Rich por archivo."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich import box

from src.metrics.smells import Smell, SEVERITY_ORDER, summarize_by_rule


@dataclass
class SmellReport:
    path: Path
    smells: list[Smell] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.smells)

    @property
    def critical(self) -> int:
        return sum(1 for s in self.smells if s.severity == "critical")


_SEVERITY_COLOR = {"critical": "red", "warning": "yellow", "info": "cyan"}
_SEVERITY_LABEL = {"critical": "CRIT", "warning": "WARN", "info": "INFO"}


def _severity_tag(severity: str) -> str:
    color = _SEVERITY_COLOR.get(severity, "white")
    label = _SEVERITY_LABEL.get(severity, severity.upper())
    return f"[{color}]{label}[/{color}]"


def render_smells(reports: list[SmellReport], console: Console | None = None) -> None:
    """Imprime, por archivo, una tabla con los smells; resumen global al final.

    Los archivos se ordenan por nº de smells críticos y luego total (desc).
    """
    if console is None:
        console = Console()

    ordered = sorted(reports, key=lambda r: (r.critical, r.count), reverse=True)

    total_smells = 0
    global_counts: dict[str, int] = {}

    for report in ordered:
        if not report.smells:
            continue
        total_smells += report.count
        for rule, n in summarize_by_rule(report.smells).items():
            global_counts[rule] = global_counts.get(rule, 0) + n

        table = Table(
            title=f"[bold cyan]{report.path.name}[/bold cyan] — {report.count} smell(s)",
            box=box.ROUNDED,
            show_lines=False,
            title_justify="left",
        )
        table.add_column("Línea", justify="right", style="dim", no_wrap=True)
        table.add_column("Sev.", justify="center", no_wrap=True)
        table.add_column("Regla", style="magenta", no_wrap=True)
        table.add_column("Detalle")

        for s in sorted(report.smells, key=lambda x: (SEVERITY_ORDER.get(x.severity, 9), x.line)):
            loc = str(s.line) if s.line > 0 else "—"
            table.add_row(loc, _severity_tag(s.severity), s.rule, s.message)

        console.print()
        console.print(table)

    _render_summary(console, ordered, total_smells, global_counts)


def _render_summary(
    console: Console,
    reports: list[SmellReport],
    total_smells: int,
    global_counts: dict[str, int],
) -> None:
    clean = [r for r in reports if r.count == 0]

    console.print()
    if total_smells == 0:
        console.print("[green]Sin code smells detectados.[/green]\n")
        return

    summary = Table(
        title="[bold]Resumen de code smells[/bold]",
        box=box.SIMPLE_HEAVY,
        title_justify="left",
    )
    summary.add_column("Regla", style="magenta")
    summary.add_column("Ocurrencias", justify="right")
    for rule, n in sorted(global_counts.items(), key=lambda kv: kv[1], reverse=True):
        summary.add_row(rule, str(n))
    summary.add_row("[bold]TOTAL[/bold]", f"[bold]{total_smells}[/bold]")

    console.print(summary)
    files_with = len(reports) - len(clean)
    console.print(
        f"  {total_smells} smell(s) en {files_with} archivo(s); "
        f"{len(clean)} archivo(s) limpio(s)."
    )
    console.print(
        "  [red]CRIT[/red] crítico   [yellow]WARN[/yellow] advertencia   "
        "[cyan]INFO[/cyan] informativo"
    )
    console.print()
