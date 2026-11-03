"""Port de ``interactions.test.ts``: moedas, blocos, canos e plataformas."""

from __future__ import annotations

from game.core.game import Game
from game.core.types import InputState
from tests.unit.helpers import STEP, level

FLOOR = {"id": "g", "kind": "ground", "x": 0, "y": 448, "w": 1800, "h": 100}
BASE = {
    "width": 1800,
    "spawn": {"x": 70, "y": 414},
    "checkpoint": {"x": 900, "y": 414},
    "exit": {"x": 1700, "y": 448},
    "platforms": [FLOOR],
}


def run(g: Game, n: int, state: InputState | None = None) -> None:
    state = state or InputState()
    for _ in range(n):
        g.update(STEP, state)


def test_coin_collected_once_and_relic_has_own_reward() -> None:
    g = Game(
        [
            level(
                **BASE,
                coins=[
                    {"id": "c", "x": 70, "y": 418, "w": 16, "h": 20},
                    {"id": "r", "x": 90, "y": 418, "w": 16, "h": 20, "special": True},
                ],
            )
        ]
    )
    run(g, 2)
    assert g.coins_total == 1
    assert g.score == 1100
    assert g.found_relic
    run(g, 30)
    assert g.score == 1100


def test_question_block_hit_from_below_releases_coin_and_depletes() -> None:
    g = Game(
        [
            level(
                **{
                    **BASE,
                    "platforms": [
                        FLOOR,
                        {
                            "id": "q",
                            "kind": "question",
                            "reward": "coin",
                            "x": 64,
                            "y": 336,
                            "w": 32,
                            "h": 32,
                        },
                    ],
                }
            )
        ]
    )
    run(g, 20)
    run(g, 60, InputState(jump=True))
    assert g.platforms[1].used
    assert g.coins_total == 1
    run(g, 50)
    run(g, 70, InputState(jump=True))
    assert g.coins_total == 1


def test_pipe_only_transports_when_pressing_down() -> None:
    pipe = {
        "id": "p",
        "kind": "pipe",
        "x": 64,
        "y": 432,
        "w": 48,
        "h": 16,
        "destination": {"x": 600, "y": 414},
    }
    g = Game([level(**{**BASE, "spawn": {"x": 70, "y": 400}, "platforms": [FLOOR, pipe]})])
    run(g, 20)
    assert g.player.x == 70
    run(g, 1, InputState(down=True))
    assert g.player.x == 600
    assert any(e.type == "secret" for e in g.events)


def test_moving_platform_carries_player_and_crumble_respawns() -> None:
    moving = {
        "id": "m",
        "kind": "moving",
        "x": 80,
        "y": 400,
        "w": 100,
        "h": 16,
        "motion": {"axis": "x", "range": 40, "speed": 1},
    }
    g = Game([level(**{**BASE, "spawn": {"x": 100, "y": 370}, "platforms": [FLOOR, moving]})])
    run(g, 10)
    x = g.player.x
    run(g, 30)
    assert g.player.x > x + 4
    c = Game(
        [
            level(
                **{
                    **BASE,
                    "spawn": {"x": 90, "y": 370},
                    "platforms": [
                        FLOOR,
                        {"id": "c", "kind": "crumble", "x": 80, "y": 400, "w": 100, "h": 16},
                    ],
                }
            )
        ]
    )
    run(c, 100)
    assert not c.platforms[1].alive
    run(c, 400)
    assert c.platforms[1].alive
