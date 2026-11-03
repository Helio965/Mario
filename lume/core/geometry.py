"""Small, allocation-free helpers for axis-aligned rectangles."""

from __future__ import annotations

from typing import Protocol


class RectLike(Protocol):
    x: float
    y: float
    w: float
    h: float


def overlaps(a: RectLike, b: RectLike) -> bool:
    """Strict AABB overlap; touching edges do not overlap (as in the TS edition)."""
    return a.x < b.x + b.w and a.x + a.w > b.x and a.y < b.y + b.h and a.y + a.h > b.y


def overlaps_xywh(a: RectLike, x: float, y: float, w: float, h: float) -> bool:
    return a.x < x + w and a.x + a.w > x and a.y < y + h and a.y + a.h > y


def approach(value: float, target: float, amount: float) -> float:
    """Move ``value`` toward ``target`` by at most ``amount``."""
    if value < target:
        return min(value + amount, target)
    return max(value - amount, target)


def clamp(value: float, low: float, high: float) -> float:
    return low if value < low else high if value > high else value


class Box:
    """Mutable rectangle used for temporary probes."""

    __slots__ = ("x", "y", "w", "h")

    def __init__(self, x: float, y: float, w: float, h: float) -> None:
        self.x, self.y, self.w, self.h = x, y, w, h

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"Box({self.x:.1f}, {self.y:.1f}, {self.w:.1f}, {self.h:.1f})"
