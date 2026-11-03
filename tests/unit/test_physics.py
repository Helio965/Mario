"""Port de ``physics.test.ts``: movimentação em passo fixo."""

from __future__ import annotations

from game.core.game import Game
from game.core.types import InputState
from tests.unit.helpers import STEP, level, run_seconds

ARENA_PLATFORMS = [
    {"id": "floor", "kind": "ground", "x": 0, "y": 448, "w": 2400, "h": 92},
    {"id": "wall", "kind": "brick", "x": 480, "y": 368, "w": 128, "h": 80},
]
ARENA = level(platforms=ARENA_PLATFORMS)


def arena() -> Game:
    return Game([ARENA])


def test_lands_without_sinking_and_collides_with_wall() -> None:
    g = arena()
    run_seconds(g, 1)
    assert g.player.y + g.player.h == 448
    run_seconds(g, 3, right=True, run=True)
    assert g.player.x + g.player.w <= 480
    assert g.player.grounded


def test_held_jump_reaches_higher_than_tap() -> None:
    heights = []
    for hold in (0.025, 0.5):
        g = arena()
        run_seconds(g, 0.1)
        lowest = g.player.y
        for i in range(90):
            g.update(STEP, InputState(jump=i / 120 < hold))
            lowest = min(lowest, g.player.y)
        heights.append(lowest)
    assert heights[1] < heights[0] - 40


def test_same_result_at_30_60_and_144_hz() -> None:
    positions = []
    for hz in (30, 60, 144):
        g = arena()
        for _ in range(hz):
            g.update(1 / hz, InputState(right=True))
        positions.append(g.player.x)
    assert max(positions) - min(positions) < 2


def test_pause_freezes_position_and_timer() -> None:
    g = arena()
    run_seconds(g, 0.5)
    t = g.time
    x = g.player.x
    g.pause()
    run_seconds(g, 2, right=True)
    assert g.player.x == x
    assert g.time == t


def test_jump_buffer_before_touching_ground() -> None:
    g = Game([level(spawn={"x": 64, "y": 400}, platforms=ARENA_PLATFORMS)])
    g.player.vy = 240
    g.update(STEP, InputState(jump=True))
    run_seconds(g, 0.15, jump=True)
    assert g.player.vy < 0
