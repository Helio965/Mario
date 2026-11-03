"""Poderes, itens, projéteis e perigos (port de ``src/core/powers.ts``)."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from game.core.interactions import burst
from game.core.types import GameEvent, ItemKind, Projectile, Rect
from game.enemies.legacy import hit_enemy
from game.physics.collision import move_body, overlaps
from game.physics.movement import GRAVITY

if TYPE_CHECKING:
    from game.core.game import Game

POWER_TEXT: dict[str, str | None] = {
    "grow": "Mais forte!",
    "fire": "Chama ativa — pressione J",
    "star": "12 segundos de invencibilidade",
    "heart": None,
}


def grant_power(game: Game, kind: ItemKind) -> None:
    p = game.player
    if game.invincible_model and kind in ("grow", "fire"):
        # Pirilampo não usa poderes: o item vira pontos e uma moeda (Wonder/NSMBU Deluxe).
        from game.core.interactions import collect_coin

        collect_coin(game, p.x, p.y, False)
        game.score += 250
        game.events.append(GameEvent("power", text=None))
        return
    if kind == "grow" and p.power == "small":
        p.power = "grown"
    elif kind == "fire":
        p.power = "fire"
    elif kind == "star":
        p.star = 12
    elif kind == "heart":
        game.lives = min(99, game.lives + 1)
        game.events.append(GameEvent("life", text="Uma vida extra!"))
    game.score += 250
    game.events.append(GameEvent("power", text=POWER_TEXT.get(kind)))
    burst(game, p.x, p.y, "#73ffe1")
    grow_safely(game)


def grow_safely(game: Game) -> None:
    p = game.player
    if p.power == "small" or p.h == 46:
        return
    big = Rect(x=p.x, y=p.y - (46 - p.h), w=p.w, h=46)
    if not any(
        s.alive and (s.kind != "hidden" or s.used) and overlaps(big, s) for s in game.platforms
    ):
        p.y = big.y
        p.h = 46


def update_powers(game: Game, dt: float, input_state: object) -> None:
    p = game.player
    grow_safely(game)
    for i in game.items:
        if not i.alive:
            continue
        i.vy = min(700, i.vy + GRAVITY * dt)
        before = i.vx
        move_body(i, game.platforms, dt)
        if before and i.vx == 0:
            i.vx = -before
        if i.y > game.level.height + 80:
            i.alive = False
        if overlaps(p, i):
            i.alive = False
            grant_power(game, i.kind)
    if (
        getattr(input_state, "ability", False)
        and p.power == "fire"
        and p.shoot_cooldown <= 0
        and "none" not in game.abilities
    ):
        game.projectiles.append(
            Projectile(
                x=p.x + (p.w if p.facing > 0 else -10),
                y=p.y + p.h * 0.4,
                w=10,
                h=10,
                vx=p.facing * 450,
                vy=-90,
                hostile=False,
                life=2.4,
                alive=True,
            )
        )
        p.shoot_cooldown = 0.3
        game.events.append(GameEvent("shot"))
    for s in game.projectiles:
        if not s.alive:
            continue
        s.life -= dt
        if s.life <= 0:
            s.alive = False
            continue
        if not s.hostile:
            s.vy += 600 * dt
        before = s.vx
        collision = move_body(s, game.platforms, dt)
        if before != 0 and s.vx == 0:
            s.alive = False
        if collision.grounded:
            if s.hostile:
                s.alive = False
            else:
                s.vy = -200
        if s.hostile:
            if overlaps(s, p):
                game.hurt()
                s.alive = False
        else:
            for e in game.enemies:
                if e.alive and overlaps(s, e):
                    hit_enemy(game, e)
                    s.alive = False
                    burst(game, s.x, s.y, "#ffb35c", 5)
                    break
    game.items = [i for i in game.items if i.alive]
    game.projectiles = [s for s in game.projectiles if s.alive]
    for h in game.level.hazards:
        if h.kind == "moving":
            hazard = Rect(
                x=h.x
                + math.sin(game.elapsed * (h.speed if h.speed is not None else 1))
                * (h.range if h.range is not None else 30),
                y=h.y,
                w=h.w,
                h=h.h,
            )
        else:
            hazard = Rect(h.x, h.y, h.w, h.h)
        if overlaps(p, hazard):
            if h.kind in ("lava", "water"):
                game.die()
            else:
                game.hurt()
