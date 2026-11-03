"""Blocos, moedas, checkpoint, canos e plataformas (port de ``interactions.ts``)."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from game.core.types import GameEvent, InputState, Item, Particle, Platform
from game.physics.collision import overlaps

if TYPE_CHECKING:
    from game.core.game import Game


def burst(game: Game, x: float, y: float, color: str = "#ffe5a0", count: int = 10) -> None:
    for i in range(count):
        game.particles.append(
            Particle(
                x=x,
                y=y,
                vx=math.cos(i * 2.4) * 85,
                vy=-50 - math.sin(i * 1.7) * 90,
                life=0.5 + (i % 3) * 0.1,
                color=color,
                size=2 + (i % 2) * 2,
            )
        )


def update_platforms(game: Game, dt: float) -> None:
    p = game.player
    for s in game.platforms:
        s.bump = max(0, s.bump - dt)
        old_x, old_y = s.x, s.y
        if s.motion is not None:
            wave = math.sin(game.elapsed * s.motion.speed + s.motion.phase) * s.motion.range
            s.x = s.start_x + (wave if s.motion.axis == "x" else 0)
            s.y = s.start_y + (wave if s.motion.axis == "y" else 0)
        s.dx = s.x - old_x
        s.dy = s.y - old_y
        if p.standing_on == s.id and s.alive:
            p.x += s.dx
            p.y += s.dy
        if s.kind == "crumble":
            if s.alive and p.standing_on == s.id:
                s.crumble += dt
            if s.alive and s.crumble > 0.65:
                s.alive = False
                s.respawn = 3
                burst(game, s.x + s.w / 2, s.y, "#cdaa7c")
            if not s.alive:
                s.respawn -= dt
                if s.respawn <= 0 and not overlaps(p, s):
                    s.alive = True
                    s.crumble = 0


def interact_world(game: Game, input_state: InputState, heads: list[Platform]) -> None:
    p = game.player
    for block in heads:
        if block.bump > 0:
            continue
        block.bump = 0.18
        if block.kind in ("question", "hidden") and not block.used:
            block.used = True
            game.events.append(GameEvent("block", x=block.x, y=block.y))
            if not block.reward or block.reward == "coin":
                collect_coin(game, block.x + block.w / 2, block.y, False)
            else:
                game.items.append(
                    Item(
                        id=f"item-{block.id}",
                        kind=block.reward,  # type: ignore[arg-type]
                        x=block.x + (block.w - 24) / 2,
                        y=block.y - 26,
                        w=24,
                        h=24,
                        vx=55,
                        vy=-100,
                        alive=True,
                    )
                )
        elif block.kind == "brick" and p.power != "small":
            block.alive = False
            game.score += 50
            burst(game, block.x + block.w / 2, block.y, "#cf8f60", 14)
            game.events.append(GameEvent("block"))
    for coin in game.coins:
        if not coin.collected and overlaps(p, coin):
            coin.collected = True
            collect_coin(game, coin.x, coin.y, coin.special)
    if (
        not game.checkpoint_reached
        and p.x >= game.level.checkpoint.x
        and abs(p.y - game.level.checkpoint.y) < 100
    ):
        game.checkpoint_reached = True
        game.events.append(GameEvent("checkpoint", text="Checkpoint ativado"))
        burst(game, p.x, p.y, "#73ffe1")
    if input_state.down and game.pipe_cooldown <= 0:
        pipe = next(
            (
                s
                for s in game.platforms
                if s.kind == "pipe"
                and s.destination is not None
                and p.x + p.w > s.x
                and p.x < s.x + s.w
                and abs(p.y + p.h - s.y) < 10
            ),
            None,
        )
        if pipe is not None and pipe.destination is not None:
            p.x = pipe.destination.x
            p.y = pipe.destination.y
            p.vx = 0
            p.vy = 0
            p.standing_on = None
            game.pipe_cooldown = 0.8
            game.camera.x = max(0, min(game.level.width - 960, p.x - 300))
            game.camera.y = max(0, min(game.level.height - 540, p.y - 250))
            game.events.append(GameEvent("secret", text="Uma passagem secreta!"))
            burst(game, p.x, p.y, "#73ffe1")


def collect_coin(game: Game, x: float, y: float, special: bool) -> None:
    if special:
        game.found_relic = True
        game.score += 1000
        game.events.append(GameEvent("relic", text="Relíquia encontrada!"))
    else:
        game.coins_total += 1
        game.score += 100
        game.events.append(GameEvent("coin"))
        if game.coins_total % 100 == 0:
            game.lives += 1
            game.events.append(GameEvent("life", text="100 moedas: vida extra!"))
    burst(game, x, y, "#73ffe1" if special else "#ffd36e", 16 if special else 8)
