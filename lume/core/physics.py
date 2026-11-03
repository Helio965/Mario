"""Axis-separated AABB movement with a broad-phase index.

The resolution rules are a faithful port of ``moveBody`` from the TypeScript
edition (horizontal pass, then vertical pass, in platform order) extended with
one-way platforms and switch blocks. The broad phase only changes *which*
platforms are tested, never the order in which overlaps are resolved.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Optional, Sequence

from .entities import Platform

BUCKET = 256.0


@dataclass(slots=True)
class CollisionResult:
    grounded: bool = False
    standing_on: Optional[Platform] = None
    heads: list[Platform] = field(default_factory=list)
    wall: int = 0  # -1 left, +1 right, 0 none


class CollisionIndex:
    """Buckets static platforms by x so each body tests only nearby solids."""

    def __init__(self, platforms: Sequence[Platform]) -> None:
        self.platforms = list(platforms)
        self.order = {id(p): i for i, p in enumerate(self.platforms)}
        self.dynamic: list[int] = []
        self.buckets: dict[int, list[int]] = {}
        for index, p in enumerate(self.platforms):
            if p.motion is not None:
                self.dynamic.append(index)
                continue
            for column in range(int(p.x // BUCKET), int((p.x + p.w) // BUCKET) + 1):
                self.buckets.setdefault(column, []).append(index)

    def query(self, x0: float, x1: float) -> list[Platform]:
        first, last = int(x0 // BUCKET), int(x1 // BUCKET)
        if first == last and not self.dynamic:
            return [self.platforms[i] for i in self.buckets.get(first, ())]
        found: set[int] = set(self.dynamic)
        for column in range(first, last + 1):
            found.update(self.buckets.get(column, ()))
        return [self.platforms[i] for i in sorted(found)]

    def all(self) -> list[Platform]:
        return self.platforms


def _is_solid(p: Platform) -> bool:
    return p.alive and (p.kind != "switch" or p.active)


def move_body(
    body,
    index: CollisionIndex,
    dt: float,
    *,
    reveal_hidden: bool = True,
    one_way: bool = True,
    margin: float = 48.0,
) -> CollisionResult:
    """Move ``body`` by its velocity, resolving collisions axis by axis.

    ``reveal_hidden``: unused hidden blocks are solid only from below (player,
    items and projectiles). Enemies pass ``False`` and ignore them entirely.
    """

    result = CollisionResult()
    reach = abs(body.vx * dt) + abs(body.vy * dt) + margin
    candidates = [p for p in index.query(body.x - reach, body.x + body.w + reach) if _is_solid(p)]

    body.x += body.vx * dt
    for p in candidates:
        if p.kind == "hidden" and not p.used:
            continue
        if p.kind == "semisolid":
            continue
        if not (body.x < p.x + p.w and body.x + body.w > p.x and body.y < p.y + p.h and body.y + body.h > p.y):
            continue
        if body.vx > 0:
            body.x = p.x - body.w
            result.wall = 1
        elif body.vx < 0:
            body.x = p.x + p.w
            result.wall = -1
        body.vx = 0.0

    vy = body.vy
    previous_bottom = body.y + body.h
    body.y += vy * dt
    for p in candidates:
        if p.kind == "hidden" and not p.used and (vy >= 0 or not reveal_hidden):
            continue
        if p.kind == "semisolid":
            if not one_way or vy <= 0 or previous_bottom > p.y + 0.5 + max(0.0, p.dy):
                continue
        if not (body.x < p.x + p.w and body.x + body.w > p.x and body.y < p.y + p.h and body.y + body.h > p.y):
            continue
        if vy > 0:
            body.y = p.y - body.h
            result.grounded = True
            result.standing_on = p
        elif vy < 0:
            body.y = p.y + p.h
            result.heads.append(p)
        body.vy = 0.0
    return result


def solid_at(index: CollisionIndex, x: float, y: float, w: float, h: float, *, enemies: bool = False) -> bool:
    """True when the probe rectangle overlaps any solid (used for ledge checks)."""
    for p in index.query(x - 1, x + w + 1):
        if not _is_solid(p):
            continue
        if p.kind == "hidden" and not p.used:
            continue
        if x < p.x + p.w and x + w > p.x and y < p.y + p.h and y + h > p.y:
            return True
    return False


def first_floor_below(index: CollisionIndex, x: float, y: float, depth: float = 2000.0) -> Optional[Platform]:
    best: Optional[Platform] = None
    for p in index.query(x - 1, x + 1):
        if not _is_solid(p) or (p.kind == "hidden" and not p.used):
            continue
        if p.x <= x < p.x + p.w and y <= p.y <= y + depth:
            if best is None or p.y < best.y:
                best = p
    return best


def iter_solids(platforms: Iterable[Platform]) -> Iterable[Platform]:
    return (p for p in platforms if _is_solid(p))
