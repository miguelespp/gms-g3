"""Índice de Mantenibilidad (MI) — fórmula normalizada de Microsoft (0–100)."""

from __future__ import annotations

import math
from dataclasses import dataclass

# Umbrales de mantenibilidad (Microsoft Visual Studio)
MI_GREEN = 20   # MI >= 20 → mantenible (verde)
MI_YELLOW = 10  # 10 <= MI < 20 → moderado (amarillo)
# MI < 10 → difícil de mantener (rojo)


@dataclass(frozen=True)
class MaintainabilityResult:
    mi: float          # Índice de Mantenibilidad (0–100)
    grade: str         # "green" | "yellow" | "red"


def compute_mi(volume: float, cyclomatic: int, sloc: int) -> MaintainabilityResult:
    """Calcula MI usando la fórmula normalizada de Microsoft.

    MI = max(0, (171 − 5.2·ln(V) − 0.23·CC − 16.2·ln(SLOC)) · 100 / 171)

    Maneja casos degenerados (volumen o SLOC en 0) para evitar log(0).
    """
    # Valores mínimos para evitar log(0)
    safe_volume = max(volume, 1.0)
    safe_sloc = max(sloc, 1)

    raw = 171.0 - 5.2 * math.log(safe_volume) - 0.23 * cyclomatic - 16.2 * math.log(safe_sloc)
    mi = max(0.0, raw * 100.0 / 171.0)
    mi = min(mi, 100.0)  # acota superiormente también

    if mi >= MI_GREEN:
        grade = "green"
    elif mi >= MI_YELLOW:
        grade = "yellow"
    else:
        grade = "red"

    return MaintainabilityResult(mi=round(mi, 2), grade=grade)
