"""Lee un archivo individual o recorre un directorio devolviendo rutas de código fuente."""

from pathlib import Path

# Extensiones reconocidas como código fuente
SOURCE_EXTENSIONS: frozenset[str] = frozenset(
    {
        ".py", ".js", ".ts", ".java", ".c", ".cpp", ".h", ".hpp",
        ".cs", ".go", ".rb", ".php", ".rs", ".kt", ".swift",
        ".sh", ".bash", ".sql", ".r", ".scala", ".lua",
    }
)


def collect_files(path: Path, extensions: frozenset[str] = SOURCE_EXTENSIONS) -> list[Path]:
    """Devuelve lista de archivos de código fuente bajo *path*.

    Si *path* es un archivo, se retorna tal cual (sin filtrar por extensión).
    Si es un directorio, se buscan recursivamente todos los archivos cuya
    extensión esté en *extensions*.
    """
    if path.is_file():
        return [path]

    if path.is_dir():
        found = sorted(
            p for p in path.rglob("*") if p.is_file() and p.suffix in extensions
        )
        return found

    raise FileNotFoundError(f"La ruta no existe: {path}")


def read_source(path: Path) -> str:
    """Lee el contenido de texto de *path* con detección básica de encoding."""
    for encoding in ("utf-8", "latin-1"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    # Último recurso: ignora errores
    return path.read_text(encoding="utf-8", errors="replace")
