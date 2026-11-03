"""Visual-only particles (dust, sparkles, leaves, weather). They never affect
the simulation; counts are capped by the quality preset."""

from __future__ import annotations

import math
from dataclasses import dataclass

from ..render.svg import Rand


@dataclass(slots=True)
class Fx:
    art: str
    x: float
    y: float
    vx: float
    vy: float
    life: float
    max_life: float
    size: float
    rot: float = 0.0
    vrot: float = 0.0
    gravity: float = 0.0
    tint: tuple[int, int, int] = (255, 255, 255)
    alpha: float = 1.0
    grow: float = 0.0
    additive: bool = False
    screen: bool = False  # canvas-space (weather)


class FxSystem:
    def __init__(self, cap: int = 600) -> None:
        self.items: list[Fx] = []
        self.cap = cap
        self.rand = Rand(17)

    def add(self, fx: Fx) -> None:
        if len(self.items) < self.cap:
            self.items.append(fx)

    def update(self, dt: float) -> None:
        alive = []
        for p in self.items:
            p.life -= dt
            if p.life <= 0:
                continue
            p.vy += p.gravity * dt
            p.x += p.vx * dt
            p.y += p.vy * dt
            p.rot += p.vrot * dt
            p.size += p.grow * dt
            alive.append(p)
        self.items = alive

    def dust(self, x: float, y: float, n: int = 5, spread: float = 40.0, color=(236, 226, 206), up: float = 30.0) -> None:
        r = self.rand
        for _ in range(n):
            self.add(Fx("particle.soft", x + r.uniform(-6, 6), y - r.uniform(0, 4), r.uniform(-spread, spread), -r.uniform(5, up),
                        r.uniform(0.35, 0.6), 0.6, r.uniform(5, 9), grow=r.uniform(8, 16), tint=color, alpha=0.7))

    def sparkle(self, x: float, y: float, n: int = 6, color=(255, 236, 170)) -> None:
        r = self.rand
        for k in range(n):
            a = k * 2 * math.pi / n + r.uniform(-0.3, 0.3)
            sp = r.uniform(40, 110)
            self.add(Fx("particle.sparkle", x, y, math.cos(a) * sp, math.sin(a) * sp - 20, r.uniform(0.35, 0.6), 0.6,
                        r.uniform(4, 7), vrot=r.uniform(-300, 300), tint=color, additive=True))

    def stars(self, x: float, y: float) -> None:
        self.sparkle(x, y, 8, (255, 230, 140))
