"""Comportamento dos inimigos da versão de referência (port de ``enemies.ts``)."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from game.bosses.legacy import update_boss
from game.core.interactions import burst
from game.core.types import Enemy, GameEvent, Projectile, Rect
from game.physics.collision import move_body, overlaps
from game.physics.movement import GRAVITY

if TYPE_CHECKING:
    from game.core.game import Game


def hit_enemy(game: Game, e: Enemy, damage: int = 1) -> bool:
    if e.behavior is not None:
        return bool(e.alive and e.behavior.on_hit(game, damage))
    if not e.alive or e.hit_timer > 0 or (e.kind == "boss" and e.state != "shell"):
        return False
    e.health -= damage
    e.hit_timer = 0.65
    burst(game, e.x + e.w / 2, e.y, "#ffdc87")
    if e.health <= 0:
        e.alive = False
        game.score += 5000 if e.kind == "boss" else 200
        game.events.append(
            GameEvent(
                "boss" if e.kind == "boss" else "stomp",
                text="Guardião derrotado!" if e.kind == "boss" else None,
            )
        )
        if e.kind == "boss":
            game.shake = 0.3
            burst(game, e.x, e.y, "#73ffe1", 30)
    else:
        game.events.append(GameEvent("stomp"))
    return True


def update_enemies(game: Game, dt: float) -> None:
    player = game.player
    for e in game.enemies:
        if not e.alive or e.behavior is not None:
            continue
        old_timer = e.timer
        e.timer += dt
        e.hit_timer = max(0, e.hit_timer - dt)
        if e.kind == "flyer":
            e.vx = e.facing * (72 + game.level.world * 6)
            e.x += e.vx * dt
            e.y = e.origin_y + math.sin(e.timer * 2.2) * 38
        else:
            if e.kind == "boss":
                update_boss(game, e, old_timer)
            elif e.kind == "shooter":
                e.vx = 0
                e.facing = -1 if player.x < e.x else 1
                if (
                    math.floor(e.timer / 2.2) > math.floor(old_timer / 2.2)
                    and abs(player.x - e.x) < 650
                ):
                    game.projectiles.append(
                        Projectile(
                            x=e.x + e.w / 2,
                            y=e.y + 8,
                            w=12,
                            h=12,
                            vx=e.facing * 180,
                            vy=0,
                            hostile=True,
                            life=3.5,
                            alive=True,
                        )
                    )
                    game.events.append(GameEvent("shot"))
            elif e.state == "shell":
                e.vx = 0
            else:
                if e.state == "slide":
                    speed = 360
                elif e.kind == "armored":
                    speed = 44
                else:
                    speed = 55 + game.level.world * 7
                e.vx = e.facing * speed
            e.vy = min(850, e.vy + GRAVITY * dt)
            before = e.vx
            hit = move_body(e, [s for s in game.platforms if s.kind != "hidden" or s.used], dt)
            e.grounded = hit.grounded
            if before != 0 and e.vx == 0:
                e.facing *= -1
            if e.grounded and e.state != "slide" and e.kind != "boss" and e.kind != "shooter":
                ahead = Rect(
                    x=e.x + e.w + 5 if e.facing > 0 else e.x - 7,
                    y=e.y + e.h,
                    w=2,
                    h=7,
                )
                if not any(
                    s.alive and (s.kind != "hidden" or s.used) and overlaps(ahead, s)
                    for s in game.platforms
                ):
                    e.facing *= -1
        if e.x < e.patrol[0]:
            e.x = e.patrol[0]
            e.facing = 1
        if e.x + e.w > e.patrol[1]:
            e.x = e.patrol[1] - e.w
            e.facing = -1
        if e.y > game.level.height + 80:
            e.alive = False
            continue
        if e.state == "slide":
            for other in game.enemies:
                if other is not e and other.alive and overlaps(e, other):
                    hit_enemy(game, other, 2)
        if not overlaps(player, e):
            continue
        if player.star > 0:
            hit_enemy(game, e, 2)
            continue
        stomp = player.vy > 0 and player.y + player.h <= e.y + min(24, player.vy * dt + 15)
        if stomp:
            player.vy = -390
            player.y = e.y - player.h - 1
            player.grounded = False
            player.standing_on = None
            if e.kind == "shell":
                if e.state == "walk" or e.state == "slide":
                    e.state = "shell"
                    e.vx = 0
                    game.score += 100
                    game.events.append(GameEvent("stomp"))
                else:
                    e.state = "slide"
                    e.facing = 1 if player.x + player.w / 2 < e.x + e.w / 2 else -1
                    e.vx = e.facing * 360
                    game.events.append(GameEvent("stomp"))
            else:
                hit_enemy(game, e)
        elif e.kind == "shell" and e.state == "shell":
            e.state = "slide"
            e.facing = 1 if player.x < e.x else -1
            e.x += e.facing * 14
            e.vx = e.facing * 360
        else:
            game.hurt()
