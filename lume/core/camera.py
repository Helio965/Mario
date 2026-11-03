"""Camera that follows the player inside the current area.

Horizontal framing is the legacy one (player at ~1/3 of the view, small
look-ahead). Vertically the camera anchors to the last ground height so short
jumps do not shake the view, and follows long falls or climbs.
"""

from __future__ import annotations

import math

from .constants import VIEW_HEIGHT, VIEW_WIDTH


class Camera:
    __slots__ = ("x", "y", "anchor_y", "lock")

    def __init__(self) -> None:
        self.x = 0.0
        self.y = 0.0
        self.anchor_y = 0.0
        self.lock: tuple[float, float, float, float] | None = None  # x, y, w, h

    def bounds(self, game) -> tuple[float, float, float, float]:
        if self.lock is not None:
            return self.lock
        p = game.player
        area = game.level.area_at(p.x + p.w / 2, p.y + p.h / 2)
        return area.x, area.y, area.w, area.h

    def target(self, game) -> tuple[float, float]:
        p = game.player
        ax, ay, aw, ah = self.bounds(game)
        tx = p.x - 310 + p.vx * 0.15
        if p.grounded or p.swimming:
            self.anchor_y = p.y
        elif p.y > self.anchor_y + 40:
            self.anchor_y = p.y - 40
        elif p.y < self.anchor_y - 170:
            self.anchor_y = p.y + 170
        ty = self.anchor_y - 290
        tx = max(ax, min(ax + aw - VIEW_WIDTH, tx))
        ty = max(ay, min(ay + ah - VIEW_HEIGHT, ty))
        return tx, ty

    def follow(self, game, dt: float) -> None:
        tx, ty = self.target(game)
        k = 1 - math.exp(-6 * dt)
        self.x += (tx - self.x) * k
        self.y += (ty - self.y) * k

    def snap(self, game) -> None:
        self.anchor_y = game.player.y
        self.x, self.y = self.target(game)
