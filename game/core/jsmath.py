"""Equivalências numéricas JavaScript → Python usadas pelo port.

O motor original roda em V8 com ``number`` IEEE 754; Python usa o mesmo
formato, mas algumas funções têm semântica diferente.
"""

from __future__ import annotations

import math


def js_round(value: float) -> int:
    """``Math.round``: arredonda 0,5 para +∞ (Python ``round`` vai para o par)."""
    return math.floor(value + 0.5)


def js_mod(a: float, b: float) -> float:
    """``%`` do JavaScript: resto com o sinal do dividendo."""
    return math.fmod(a, b)


def js_min(a: float, b: float) -> float:
    """``Math.min`` propaga NaN; ``min`` do Python não."""
    if math.isnan(a) or math.isnan(b):
        return math.nan
    return a if a < b else b
