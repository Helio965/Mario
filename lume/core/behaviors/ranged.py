"""Ranged families: shooter (legacy sentinel), thrower (arcing projectiles) and
cannon (straight, stompable shots)."""

from __future__ import annotations

from ..entities import Projectile
from .base import Behavior, ground_move, player_distance, register


def fire(game, e, *, vx: float, vy: float = 0.0, size: float = 12.0, life: float = 3.5, kind: str = "orb",
         gravity: float = 0.0, stompable: bool = False, x: float | None = None, y: float | None = None) -> Projectile:
    shot = Projectile(
        x=e.x + e.w / 2 if x is None else x,
        y=e.y + 8 if y is None else y,
        w=size,
        h=size,
        vx=vx,
        vy=vy,
        hostile=True,
        life=life,
        kind=kind,
        gravity=gravity,
        owner=e.id,
        stompable=stompable,
    )
    game.projectiles.append(shot)
    game.emit("shot", x=shot.x, y=shot.y, ref=kind)
    return shot


@register("shooter")
class Shooter(Behavior):
    """Stationary sentinel: faces the player and fires every ``interval`` seconds
    when the player is within ``range``. Shows a charge pose before firing."""

    states = ("idle", "charge", "fire", "hurt", "defeat")

    def spawn(self, game, e):
        e.vx = 0.0
        e.anim = "idle"

    def update(self, game, e, dt, old_timer):
        p = game.player
        e.vx = 0.0
        e.facing = -1 if p.x < e.x else 1
        interval = float(self.param(e, "interval", 2.2))
        reach = float(self.param(e, "range", 650.0))
        phase = e.timer % interval
        if int(e.timer // interval) > int(old_timer // interval) and abs(p.x - e.x) < reach:
            fire(
                game, e,
                vx=e.facing * float(self.param(e, "shot_speed", 180.0)),
                vy=float(self.param(e, "shot_vy", 0.0)),
                size=float(self.param(e, "shot_size", 12.0)),
                life=float(self.param(e, "shot_life", 3.5)),
                kind=str(self.param(e, "shot_kind", "orb")),
                gravity=float(self.param(e, "shot_gravity", 0.0)),
            )
            e.memory["fired"] = 0.25
        e.memory["fired"] = max(0.0, e.memory.get("fired", 0.0) - dt)
        if e.memory["fired"] > 0:
            e.anim = "fire"
        elif interval - phase < 0.45 and abs(p.x - e.x) < reach:
            e.anim = "charge"
        else:
            e.anim = "idle"
        ground_move(game, e, dt, edge_turn=False)


@register("thrower")
class Thrower(Behavior):
    """Keeps its ground, sidesteps, hops, and throws arcing projectiles at the
    player with a visible wind-up (role analogous to the classic 'brother')."""

    states = ("idle", "step", "windup", "throw", "jump", "hurt", "defeat")

    def spawn(self, game, e):
        e.vx = 0.0
        e.set_state("step")

    def update(self, game, e, dt, old_timer):
        dx, _ = player_distance(game, e)
        e.facing = 1 if dx > 0 else -1
        interval = float(self.param(e, "interval", 1.8))
        if e.state == "step":
            e.vx = (1 if int(e.timer * 0.8) % 2 == 0 else -1) * self.speed(e)
            if e.state_time > interval and abs(dx) < float(self.param(e, "range", 520.0)):
                e.set_state("windup")
            elif e.state_time > interval * 1.5 and e.grounded and self.param(e, "hop", True):
                e.vy = -430.0
                e.set_state("jump")
        elif e.state == "jump":
            e.vx = 0.0
            if e.grounded and e.state_time > 0.1:
                e.set_state("step")
        elif e.state == "windup":
            e.vx = 0.0
            if e.state_time > float(self.param(e, "telegraph", 0.35)):
                flight = max(0.6, min(1.3, abs(dx) / 260.0))
                fire(
                    game, e,
                    vx=dx / flight,
                    vy=-float(self.param(e, "arc", 330.0)),
                    size=14,
                    life=4.0,
                    kind=str(self.param(e, "shot_kind", "sand")),
                    gravity=float(self.param(e, "shot_gravity", 600.0)),
                    y=e.y - 6,
                )
                e.set_state("throw")
        elif e.state == "throw":
            e.vx = 0.0
            if e.state_time > 0.3:
                e.set_state("step")
        e.anim = e.state
        ground_move(game, e, dt, edge_turn=True)


@register("cannon")
class Cannon(Behavior):
    """Launcher that fires straight shots toward the player's side. Shots can be
    stomped. The launcher itself is indestructible (pure obstacle)."""

    states = ("idle", "charge", "fire", "defeat")

    def spawn(self, game, e):
        e.vx = 0.0
        e.anim = "idle"

    def update(self, game, e, dt, old_timer):
        p = game.player
        interval = float(self.param(e, "interval", 3.0))
        phase = e.timer % interval
        dx = p.x - e.x
        if int(e.timer // interval) > int(old_timer // interval) and 60 < abs(dx) < float(self.param(e, "range", 700.0)):
            e.facing = 1 if dx > 0 else -1
            fire(
                game, e,
                vx=e.facing * float(self.param(e, "shot_speed", 170.0)),
                size=float(self.param(e, "shot_size", 22.0)),
                life=6.0,
                kind=str(self.param(e, "shot_kind", "bolt")),
                stompable=True,
                x=e.x + (e.w if e.facing > 0 else -22),
                y=e.y + 4,
            )
            e.memory["fired"] = 0.3
        e.memory["fired"] = max(0.0, e.memory.get("fired", 0.0) - dt)
        e.anim = "fire" if e.memory["fired"] > 0 else ("charge" if interval - phase < 0.5 else "idle")

    def tangible(self, game, e):
        # The launcher is an emitter mounted on solid terrain declared by the level.
        return False

    def vulnerable_to(self, game, e, source):
        return False


__all__ = ["Shooter", "Thrower", "Cannon", "fire"]
