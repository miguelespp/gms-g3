"""CLI principal — comando: python -m src.cli analyze <ruta>"""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from src.core.file_reader import collect_files, read_source
from src.core.lexer import tokenize
from src.metrics.halstead import compute_halstead
from src.metrics.complexity import compute_complexity
from src.metrics.loc import compute_loc
from src.metrics.maintainability import compute_mi
from src.report.console import FileReport, render_table

app = typer.Typer(
    name="code-anomaly",
    help="Herramienta de detección de anomalías: calcula el Índice de Mantenibilidad.",
    add_completion=False,
)

console = Console(legacy_windows=False)


@app.callback()
def _callback() -> None:
    """Detección de anomalías en código fuente — Índice de Mantenibilidad."""


@app.command()
def analyze(
    path: Path = typer.Argument(..., help="Archivo o directorio a analizar."),
    extensions: str = typer.Option(
        "",
        "--ext",
        help="Extensiones adicionales separadas por coma (ej. .vue,.svelte).",
    ),
) -> None:
    """Analiza código fuente y muestra el ranking de Índice de Mantenibilidad."""
    if not path.exists():
        console.print(f"[red]Error:[/red] La ruta no existe: {path}")
        raise typer.Exit(code=1)

    from src.core.file_reader import SOURCE_EXTENSIONS
    exts = SOURCE_EXTENSIONS
    if extensions:
        extra = frozenset(e.strip() for e in extensions.split(",") if e.strip())
        exts = exts | extra

    files = collect_files(path, exts)
    if not files:
        console.print("[yellow]No se encontraron archivos de código fuente.[/yellow]")
        raise typer.Exit()

    console.print(f"\n[bold]Analizando {len(files)} archivo(s) en[/bold] [cyan]{path}[/cyan]...\n")

    reports: list[FileReport] = []
    for fpath in files:
        source = read_source(fpath)
        if not source.strip():
            # Archivo vacío — MI máximo, CC mínimo
            reports.append(
                FileReport(
                    path=fpath, sloc=0, cyclomatic=1,
                    volume=0.0, comment_ratio=0.0, mi=100.0, grade="green",
                )
            )
            continue

        tokens = tokenize(source, filename=fpath.name)
        halstead = compute_halstead(tokens)
        cc = compute_complexity(tokens)
        loc = compute_loc(source, tokens)
        mi_result = compute_mi(halstead.volume, cc, loc.sloc)

        reports.append(
            FileReport(
                path=fpath,
                sloc=loc.sloc,
                cyclomatic=cc,
                volume=halstead.volume,
                comment_ratio=loc.comment_ratio,
                mi=mi_result.mi,
                grade=mi_result.grade,
            )
        )

    render_table(reports, console)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
