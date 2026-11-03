"""Creature rig framework shared by all enemy species."""

from __future__ import annotations

import math
from typing import Callable, Type

from ..rig import DrawCommand, Xf
from ..svg import Svg

RIGS: dict[str, Type["CreatureRig"]] = {}
INK = "#2b1d2c"


def register(name: str):
    def deco(cls):
        cls.rig_id = name
        RIGS[name] = cls
        return cls

    return deco


class CreatureRig:
    """Parts are SVGs in design units (du); ``du`` converts to world units.

    ``commands(enemy, t)`` returns draw commands in rig space (origin at the
    feet centre, facing right). ``provisional`` rigs are flagged in reports.
    """

    rig_id = "base"
    du = 0.5
    provisional = False

    def __init__(self, species: str = "") -> None:
        self.species = species

    def parts(self) -> dict[str, tuple[Callable[[], Svg], tuple[float, float]]]:
        return {}

    def part_id(self, name: str) -> str:
        return f"{self.rig_id}.{name}"

    def commands(self, e, t: float) -> list[DrawCommand]:
        raise NotImplementedError

    # helpers --------------------------------------------------------------------------
    def cmd(self, name: str, xf: Xf, **kw) -> DrawCommand:
        return DrawCommand(self.part_id(name), xf, **kw)

    @staticmethod
    def blink(t: float, seed: float) -> bool:
        period = 2.6 + (math.sin(seed * 7.13) + 1) * 1.1
        return ((t + seed) % period) < 0.12

    @staticmethod
    def defeat_xf(e, root: Xf) -> Xf:
        """Squash for stomps; tumble for fire/shell/star knock-outs."""
        if e.memory.get("defeat_kind") == "knock":
            return Xf(root.x, root.y, 180.0, root.sx, root.sy)
        k = max(0.0, min(1.0, e.defeated / 0.6))
        return Xf(root.x, root.y, 0.0, 1.0 + 0.45 * (1 - k * 0.3), 0.28)


def rig_for(animation_set: str, species: str) -> CreatureRig:
    cls = RIGS.get(animation_set)
    if cls is None:
        from .provisional import ProvisionalCreature

        return ProvisionalCreature(species)
    return cls(species)


def eye_svg(size: float = 12.0, iris: str = "#2a2238", angry: bool = False) -> Svg:
    s = Svg(size, size)
    c = size / 2
    s.ellipse(c, c, c * 0.82, c * 0.9, fill=s.linear(0, 0, 0, size, [(0, "#ffffff"), (1, "#e2e8f0")]), stroke=INK, width=size * 0.08)
    if angry:
        s.path(f"M{size * 0.05:.2f} {size * 0.12:.2f} L{size * 0.95:.2f} {size * 0.38:.2f} L{size * 0.95:.2f} 0 L{size * 0.05:.2f} 0 Z", fill=INK)
    return s


def pupil_svg(size: float = 6.0, color: str = "#2a2238") -> Svg:
    s = Svg(size, size)
    c = size / 2
    s.circle(c, c, c * 0.92, fill=color)
    s.circle(c * 1.3, c * 0.7, c * 0.32, fill="#ffffff")
    return s
