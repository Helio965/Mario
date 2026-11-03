"""Colisões AABB com resolução por eixo (port de ``src/core/physics.ts``)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from game.core.types import Platform


class _Box(Protocol):
    x: float
    y: float
    w: float
    h: float


class _Body(Protocol):
    x: float
    y: float
    w: float
    h: float
    vx: float
    vy: float


def overlaps(a: Any, b: Any) -> bool:
    return bool(a.x < b.x + b.w and a.x + a.w > b.x and a.y < b.y + b.h and a.y + a.h > b.y)


def approach(value: float, target: float, amount: float) -> float:
    if value < target:
        return min(value + amount, target)
    return max(value - amount, target)


@dataclass(slots=True)
class CollisionResult:
    grounded: bool
    standing_on: str | None
    heads: list[Platform]


def move_body(body: _Body, platforms: list[Platform], dt: float) -> CollisionResult:
    """Integra ``vx``/``vy`` e empurra o corpo para fora das plataformas vivas.

    Reproduz a ordem exata do motor original: eixo X e depois eixo Y, cada um
    contra todas as plataformas na ordem de declaração. Blocos ocultos só
    colidem vindos de baixo (``vy < 0``).
    """
    grounded = False
    standing_on: str | None = None
    heads: list[Platform] = []
    solids = [p for p in platforms if p.alive]
    body.x += body.vx * dt
    for p in solids:
        if p.kind == "hidden" and not p.used:
            continue
        if not overlaps(body, p):
            continue
        if body.vx > 0:
            body.x = p.x - body.w
        elif body.vx < 0:
            body.x = p.x + p.w
        body.vx = 0
    vy = body.vy
    body.y += vy * dt
    for p in solids:
        if p.kind == "hidden" and not p.used and vy >= 0:
            continue
        if not overlaps(body, p):
            continue
        if vy > 0:
            body.y = p.y - body.h
            grounded = True
            standing_on = p.id
        elif vy < 0:
            body.y = p.y + p.h
            heads.append(p)
        body.vy = 0
    return CollisionResult(grounded, standing_on, heads)
