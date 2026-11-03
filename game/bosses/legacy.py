"""Guardião da versão de referência (port de ``bosses.ts``).

Os guardiões descansam com a guarda aberta, depois carregam, saltam e disparam.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from game.core.types import Enemy, GameEvent, Projectile

if TYPE_CHECKING:
    from game.core.game import Game


def update_boss(game: Game, e: Enemy, previous_timer: float) -> None:
    max_hp = e.hp if e.hp is not None else 4
    aggressive = e.health <= max_hp / 2
    period = 3.8 if aggressive else 4.8
    phase = math.fmod(e.timer, period)
    previous_phase = math.fmod(previous_timer, period)
    vulnerable = phase < (1.1 if aggressive else 1.65)
    e.state = "shell" if vulnerable else "walk"
    e.vx = 0 if vulnerable else e.facing * (135 if aggressive else 85)
    if phase >= 2 and previous_phase < 2 and e.grounded:
        e.vy = -400
    shots = [2.5, 3, 3.4] if game.level.world == 5 else [2.7]
    for shot_time in shots:
        if phase >= shot_time and previous_phase < shot_time:
            direction = -1 if game.player.x < e.x else 1
            game.projectiles.append(
                Projectile(
                    x=e.x + e.w / 2,
                    y=e.y + 24,
                    w=14,
                    h=14,
                    vx=direction * (160 + game.level.world * 15),
                    vy=-40 if aggressive else 0,
                    hostile=True,
                    life=4,
                    alive=True,
                )
            )
            game.events.append(GameEvent("shot"))
