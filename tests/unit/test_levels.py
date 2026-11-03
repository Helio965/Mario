"""Port de ``levels.test.ts``: estrutura dos mundos e segurança de cada fase."""

from __future__ import annotations

import json
from dataclasses import replace

import pytest

from game.core.game import Game
from game.core.types import InputState
from game.levels.loader import THEMES, load_levels

LEVELS = load_levels()


def test_five_worlds_with_three_distinct_maps_and_one_boss_each() -> None:
    assert len(LEVELS) == 15
    assert len(THEMES) == 5
    assert len({lvl.id for lvl in LEVELS}) == 15
    for world in range(1, 6):
        levels = [lvl for lvl in LEVELS if lvl.world == world]
        assert len(levels) == 3
        assert len([e for e in levels[2].enemies if e.kind == "boss"]) == 1
        assert len({json.dumps([[p.x, p.y, p.w] for p in lvl.platforms]) for lvl in levels}) == 3


@pytest.mark.parametrize("level", LEVELS, ids=[lvl.id for lvl in LEVELS])
def test_safe_spawn_checkpoint_returnable_secrets_and_exit_on_ground(level) -> None:
    for point in (level.spawn, level.checkpoint):
        g = Game([replace(level, spawn=point)])
        for _ in range(90):
            g.update(1 / 120, InputState())
        assert g.lives == 5
        assert g.player.grounded
    assert any(p.x <= level.exit.x <= p.x + p.w and p.y == level.exit.y for p in level.platforms)
    assert any(c.special for c in level.coins)
    pipes = [p for p in level.platforms if p.destination is not None]
    assert len(pipes) >= 2
    for pipe in pipes:
        assert pipe.destination is not None
        assert 0 <= pipe.destination.x < level.width
        assert any(
            pipe.destination.x + 22 > s.x
            and pipe.destination.x < s.x + s.w
            and pipe.destination.y + 30 <= s.y <= pipe.destination.y + 100
            for s in level.platforms
        )
