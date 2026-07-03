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
from src.metrics.smells import SmellConfig, detect_smells
from src.report.console import FileReport, render_table
from src.report.smells import SmellReport, render_smells

app = typer.Typer(
    name="code-anomaly",
    help="Herramienta de detección de anomalías: calcula el Índice de Mantenibilidad.",
    add_completion=False,
)

console = Console(legacy_windows=False)


@app.callback()
def _callback() -> None:
    """Detección de anomalías en código fuente — Índice de Mantenibilidad."""


def _resolve_files(path: Path, extensions: str) -> list[Path]:
    """Valida la ruta, resuelve extensiones y recolecta archivos (sale si no hay)."""
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
    return files


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
    files = _resolve_files(path, extensions)

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


@app.command()
def smells(
    path: Path = typer.Argument(..., help="Archivo o directorio a analizar."),
    extensions: str = typer.Option(
        "",
        "--ext",
        help="Extensiones adicionales separadas por coma (ej. .vue,.svelte).",
    ),
    max_function_lines: int = typer.Option(
        40, "--max-func-lines", help="Umbral de líneas para 'función larga'."
    ),
    max_nesting: int = typer.Option(
        4, "--max-nesting", help="Profundidad de anidamiento permitida."
    ),
) -> None:
    """Detecta code smells por patrones léxicos (números mágicos, anidamiento, etc.)."""
    files = _resolve_files(path, extensions)
    config = SmellConfig(
        long_function_lines=max_function_lines,
        max_nesting_depth=max_nesting,
    )

    console.print(
        f"\n[bold]Buscando code smells en {len(files)} archivo(s)[/bold] "
        f"[cyan]{path}[/cyan]...\n"
    )

    reports: list[SmellReport] = []
    for fpath in files:
        source = read_source(fpath)
        if not source.strip():
            reports.append(SmellReport(path=fpath, smells=[]))
            continue
        tokens = tokenize(source, filename=fpath.name)
        reports.append(
            SmellReport(path=fpath, smells=detect_smells(source, tokens, config))
        )

    render_smells(reports, console)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
