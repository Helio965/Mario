"""Port de ``routes.test.ts``: percorre a primeira fase com corrida e saltos reais."""

from __future__ import annotations

from game.core.game import Game
from game.core.types import InputState
from game.levels.loader import load_levels


def test_first_level_with_real_running_and_jumping() -> None:
    g = Game([load_levels()[0]])
    hold = 0.0
    cooldown = 0.0
    for _tick in range(120 * 70):
        if g.status == "complete":
            break
        hold = max(0, hold - 1 / 120)
        cooldown = max(0, cooldown - 1 / 120)
        p = g.player
        if p.grounded and cooldown == 0:
            wall = any(
                s.alive
                and s.kind != "hidden"
                and s.x >= p.x + p.w - 2
                and s.x < p.x + p.w + 74
                and s.y < p.y + p.h - 3
                and s.y + s.h > p.y
                for s in g.platforms
            )
            ground_ahead = any(
                s.alive
                and s.kind != "hidden"
                and p.x + p.w + 12 >= s.x
                and p.x + p.w + 12 <= s.x + s.w
                and s.y >= p.y + p.h - 8
                and s.y <= p.y + p.h + 80
                for s in g.platforms
            )
            enemy = any(
                e.alive
                and e.x > p.x
                and e.x < p.x + p.w + 125
                and e.y < p.y + p.h + 16
                and e.y + e.h > p.y
                for e in g.enemies
            )
            if wall or not ground_ahead or enemy:
                hold = 0.4
                cooldown = 0.55
        g.update(1 / 120, InputState(right=True, run=True, jump=hold > 0))
    assert g.status == "complete", f"parou em x={g.player.x} vidas={g.lives}"
    assert g.lives == 5
    assert g.coins_total > 0
    assert g.checkpoint_reached
