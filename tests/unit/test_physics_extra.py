"""Port de ``physics-extra.test.ts``: tolerâncias, limites e recuperação."""

from __future__ import annotations

from game.core.game import Game
from tests.unit.helpers import events_of, level, ticks

FLOOR = {"id": "floor", "kind": "ground", "x": 0, "y": 448, "w": 2400, "h": 92}
ARENA = level(
    id="physics-extra",
    name="Arena de física",
    spawn={"x": 64, "y": 418},
    checkpoint={"x": 1100, "y": 418},
    exit={"x": 2300, "y": 448},
)


def walk_off_ledge() -> Game:
    game = Game([level(spawn={"x": 200, "y": 418}, platforms=[{**FLOOR, "w": 240}])])
    ticks(game, 2)
    assert game.player.grounded
    for _ in range(120):
        if not game.player.grounded:
            break
        ticks(game, 1, right=True, run=True)
    assert not game.player.grounded
    assert game.player.x >= 240
    return game


def test_accepts_jump_within_coyote_time() -> None:
    game = walk_off_ledge()
    ticks(game, 5, right=True, run=True)
    assert game.player.vy > 0
    ticks(game, 1, right=True, run=True, jump=True)
    assert game.player.vy < -500
    assert len(events_of(game, "jump")) == 1


def test_refuses_jump_after_coyote_window() -> None:
    game = walk_off_ledge()
    ticks(game, 15, right=True, run=True)
    ticks(game, 1, right=True, run=True, jump=True)
    assert game.player.vy > 0
    assert len(events_of(game, "jump")) == 0


def test_air_control_accelerates_and_reverses() -> None:
    game = Game([ARENA])
    ticks(game, 2)
    ticks(game, 1, jump=True)
    ticks(game, 10, jump=True, right=True)
    before_reverse = game.player.x
    assert not game.player.grounded
    assert game.player.vx > 60
    furthest_right = before_reverse
    for _ in range(24):
        ticks(game, 1, jump=True, left=True)
        furthest_right = max(furthest_right, game.player.x)
    assert not game.player.grounded
    assert game.player.vx < -60
    assert game.player.x < furthest_right - 5


def test_ceiling_interrupts_ascent_and_lands_again() -> None:
    ceiling = {"id": "ceiling", "kind": "brick", "x": 40, "y": 330, "w": 140, "h": 16}
    game = Game([level(spawn={"x": 64, "y": 418}, platforms=[FLOOR, ceiling])])
    ticks(game, 2)
    ticks(game, 1, jump=True)
    assert game.player.vy < 0
    hit_ceiling = False
    for _ in range(100):
        ticks(game, 1, jump=True)
        assert game.player.y >= ceiling["y"] + ceiling["h"]
        hit_ceiling = hit_ceiling or (
            game.player.y == ceiling["y"] + ceiling["h"] and game.player.vy == 0
        )
    assert hit_ceiling
    assert game.player.grounded
    assert game.player.y + game.player.h == 448
    assert len(events_of(game, "jump")) == 1


def test_does_not_pass_through_thin_wall_at_run_speed() -> None:
    wall = {"id": "wall", "kind": "brick", "x": 480, "y": 350, "w": 16, "h": 98}
    game = Game([level(spawn={"x": 64, "y": 418}, platforms=[FLOOR, wall])])
    ticks(game, 2)
    fastest = 0.0
    for _ in range(240):
        ticks(game, 1, right=True, run=True)
        fastest = max(fastest, game.player.vx)
        assert game.player.x + game.player.w <= wall["x"]
    assert fastest == 340
    assert game.player.x + game.player.w == wall["x"]
    assert game.player.grounded


def test_lands_on_thin_platform_at_terminal_velocity() -> None:
    game = Game([level(spawn={"x": 64, "y": 20}, platforms=[{**FLOOR, "h": 8}])])
    game.player.vy = 850
    game.player.vx = 340
    for _ in range(120):
        if game.player.grounded:
            break
        ticks(game, 1, right=True, run=True)
        assert game.player.y + game.player.h <= 448
    assert game.player.grounded
    assert game.player.y + game.player.h == 448
    assert game.player.vy == 0


def test_ice_keeps_more_speed_and_slides_further() -> None:
    results = []
    for kind in ("ground", "ice"):
        game = Game([level(spawn={"x": 64, "y": 418}, platforms=[{**FLOOR, "kind": kind}])])
        ticks(game, 2)
        ticks(game, 60, right=True, run=True)
        assert game.player.vx == 340
        start_x = game.player.x
        ticks(game, 12)
        results.append((game.player.vx, game.player.x - start_x))
    assert results[1][0] > results[0][0] + 100
    assert results[1][1] > results[0][1] + 5


def test_checkpoint_by_movement_and_respawn_after_pit() -> None:
    checkpoint = {"x": 400, "y": 418}
    game = Game(
        [level(spawn={"x": 64, "y": 418}, checkpoint=checkpoint, platforms=[{**FLOOR, "w": 700}])]
    )
    ticks(game, 2)
    for _ in range(180):
        if game.checkpoint_reached:
            break
        ticks(game, 1, right=True, run=True)
    assert game.checkpoint_reached
    assert len(events_of(game, "checkpoint")) == 1
    for _ in range(360):
        if game.status != "playing":
            break
        ticks(game, 1, right=True, run=True)
    assert game.status == "dead"
    assert game.lives == 4
    for _ in range(180):
        if game.status != "dead":
            break
        ticks(game, 1)
    assert game.status == "playing"
    assert game.player.x == checkpoint["x"]
    assert game.player.y == checkpoint["y"]
    assert game.player.vx == 0
    assert game.player.vy == 0
    assert game.checkpoint_reached
    assert len(events_of(game, "death")) == 1
    assert len(events_of(game, "checkpoint")) == 1
