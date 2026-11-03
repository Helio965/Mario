"""Port of tests/unit/physics*.test.ts: fixed-step movement and tolerances."""

from lume.core.constants import FIXED_DT
from lume.core.input import InputState

from .conftest import game, level, run, ticks

WALL = {"id": "wall", "kind": "brick", "x": 480, "y": 368, "w": 128, "h": 80}


def test_lands_without_crossing_floor_and_stops_at_wall():
    g = game(extra_platforms=[WALL])
    run(g, 1)
    assert g.player.y + g.player.h == 448
    run(g, 3, right=True, run=True)
    assert g.player.x + g.player.w <= 480
    assert g.player.grounded


def test_held_jump_goes_higher_than_tap():
    heights = []
    for hold in (0.025, 0.5):
        g = game(extra_platforms=[WALL])
        run(g, 0.1)
        top = g.player.y
        for i in range(90):
            g.update(FIXED_DT, InputState(jump=i / 120 < hold))
            top = min(top, g.player.y)
        heights.append(top)
    assert heights[1] < heights[0] - 40


def test_same_result_at_30_60_144_hz():
    positions = []
    for hz in (30, 60, 144):
        g = game()
        for _ in range(hz):
            g.update(1 / hz, InputState(right=True))
        positions.append(g.player.x)
    assert max(positions) - min(positions) < 2


def test_pause_freezes_position_and_timer():
    g = game()
    run(g, 0.5)
    t, x = g.time, g.player.x
    g.pause()
    run(g, 2, right=True)
    assert g.player.x == x and g.time == t


def test_jump_buffer_before_touching_ground():
    g = game(spawn={"x": 64, "y": 400})
    g.player.vy = 240
    g.update(FIXED_DT, InputState(jump=True))
    run(g, 0.15, jump=True)
    assert g.player.vy < 0


def _walk_off_ledge():
    g = game(spawn={"x": 200, "y": 418}, platforms=[{"id": "floor", "kind": "ground", "x": 0, "y": 448, "w": 240, "h": 92}])
    ticks(g, 2)
    assert g.player.grounded
    for _ in range(120):
        if not g.player.grounded:
            break
        ticks(g, 1, right=True, run=True)
    assert not g.player.grounded and g.player.x >= 240 - g.player.w
    return g


def test_coyote_time_accepts_late_jump():
    g = _walk_off_ledge()
    ticks(g, 5, right=True, run=True)
    assert g.player.vy > 0
    ticks(g, 1, right=True, run=True, jump=True)
    assert g.player.vy < -500
    assert len([e for e in g.events if e.type == "jump"]) == 1


def test_coyote_window_expires():
    g = _walk_off_ledge()
    ticks(g, 15, right=True, run=True)
    ticks(g, 1, right=True, run=True, jump=True)
    assert g.player.vy > 0
    assert not [e for e in g.events if e.type == "jump"]


def test_air_control_can_reverse():
    g = game()
    ticks(g, 2)
    ticks(g, 1, jump=True)
    ticks(g, 10, jump=True, right=True)
    before = g.player.x
    assert not g.player.grounded and g.player.vx > 60
    furthest = before
    for _ in range(24):
        ticks(g, 1, jump=True, left=True)
        furthest = max(furthest, g.player.x)
    assert not g.player.grounded and g.player.vx < -60 and g.player.x < furthest - 5


def test_ceiling_stops_rise_and_player_lands_again():
    ceiling = {"id": "ceiling", "kind": "brick", "x": 40, "y": 330, "w": 140, "h": 16}
    g = game(extra_platforms=[ceiling])
    ticks(g, 2)
    ticks(g, 1, jump=True)
    assert g.player.vy < 0
    hit = False
    for _ in range(100):
        ticks(g, 1, jump=True)
        assert g.player.y >= 346
        hit = hit or (g.player.y == 346 and g.player.vy == 0)
    assert hit and g.player.grounded and g.player.y + g.player.h == 448
    assert len([e for e in g.events if e.type == "jump"]) == 1


def test_thin_wall_is_not_tunnelled_at_run_speed():
    wall = {"id": "wall", "kind": "brick", "x": 480, "y": 350, "w": 16, "h": 98}
    g = game(extra_platforms=[wall])
    ticks(g, 2)
    fastest = 0.0
    for _ in range(240):
        ticks(g, 1, right=True, run=True)
        fastest = max(fastest, g.player.vx)
        assert g.player.x + g.player.w <= 480
    assert fastest == 340 and g.player.x + g.player.w == 480 and g.player.grounded


def test_lands_on_thin_platform_at_terminal_speed():
    g = game(spawn={"x": 64, "y": 20}, platforms=[{"id": "floor", "kind": "ground", "x": 0, "y": 448, "w": 2400, "h": 8}])
    g.player.vy, g.player.vx = 850, 340
    for _ in range(120):
        if g.player.grounded:
            break
        ticks(g, 1, right=True, run=True)
        assert g.player.y + g.player.h <= 448
    assert g.player.grounded and g.player.y + g.player.h == 448 and g.player.vy == 0


def test_ice_keeps_more_speed():
    results = []
    for surface in ("normal", "ice"):
        g = game(platforms=[{"id": "floor", "kind": "ground", "x": 0, "y": 448, "w": 2400, "h": 92, "surface": surface}])
        ticks(g, 2)
        ticks(g, 60, right=True, run=True)
        assert g.player.vx == 340
        start = g.player.x
        ticks(g, 12)
        results.append((g.player.vx, g.player.x - start))
    assert results[1][0] > results[0][0] + 100
    assert results[1][1] > results[0][1] + 5


def test_checkpoint_activation_and_respawn():
    g = game(checkpoints=[{"id": "cp", "x": 400, "y": 418}],
             platforms=[{"id": "floor", "kind": "ground", "x": 0, "y": 448, "w": 700, "h": 92}],
             exit={"id": "goal", "kind": "flag", "x": 600, "y": 448})
    g.level = g.level  # spawn already applied
    ticks(g, 2)
    for _ in range(180):
        if g.checkpoint_reached:
            break
        ticks(g, 1, right=True, run=True)
    assert g.checkpoint_reached
    assert len([e for e in g.events if e.type == "checkpoint"]) == 1


def test_respawn_at_checkpoint_after_pit():
    g = game(checkpoints=[{"id": "cp", "x": 400, "y": 418}],
             platforms=[{"id": "floor", "kind": "ground", "x": 0, "y": 448, "w": 700, "h": 92},
                        {"id": "far", "kind": "ground", "x": 2200, "y": 448, "w": 200, "h": 92}])
    ticks(g, 2)
    for _ in range(360):
        if g.status != "playing":
            break
        ticks(g, 1, right=True, run=True)
    assert g.status == "dead" and g.lives == 4
    for _ in range(180):
        if g.status != "dead":
            break
        ticks(g, 1)
    assert g.status == "playing"
    assert (g.player.x, g.player.y, g.player.vx, g.player.vy) == (400, 418, 0, 0)
    assert len([e for e in g.events if e.type == "death"]) == 1


def test_one_way_platform_supports_from_above_only():
    shelf = {"id": "shelf", "kind": "semisolid", "x": 0, "y": 380, "w": 300, "h": 12}
    g = game(extra_platforms=[shelf])
    ticks(g, 20)
    assert g.player.y + g.player.h == 448  # spawned below the shelf
    ticks(g, 1, jump=True)
    for _ in range(80):
        ticks(g, 1, jump=True)
    assert g.player.grounded and g.player.y + g.player.h == 380


def test_spring_launches_higher_than_jump():
    spring = {"id": "spring", "kind": "spring", "x": 200, "y": 432, "w": 40, "h": 16, "bounce": 900}
    g = game(spawn={"x": 209, "y": 300}, extra_platforms=[spring])
    best = 999
    for _ in range(200):
        ticks(g, 1, jump=True)
        best = min(best, g.player.y)
    assert any(e.type == "spring" for e in g.events)
    assert best < 432 - 200


def test_conveyor_carries_player():
    belt = {"id": "belt", "kind": "conveyor", "x": 0, "y": 448, "w": 2400, "h": 92, "surface_speed": 120}
    g = game(platforms=[belt])
    ticks(g, 4)
    x = g.player.x
    run(g, 1)
    assert g.player.x > x + 100


def test_swim_zone_changes_physics():
    water = [{"id": "lake", "kind": "swim", "x": 0, "y": 200, "w": 2400, "h": 248}]
    g = game(zones=water, spawn={"x": 64, "y": 300})
    run(g, 1)
    assert g.player.swimming
    y = g.player.y
    ticks(g, 1, jump=True)
    run(g, 0.2)
    assert g.player.y < y
    assert g.player.animation == "swim"


def test_wind_zone_pushes_player():
    wind = [{"id": "gust", "kind": "wind", "x": 0, "y": 0, "w": 2400, "h": 540, "force_x": -500}]
    calm, windy = game(), game(zones=wind)
    for g in (calm, windy):
        ticks(g, 2)
        ticks(g, 1, jump=True)
        run(g, 0.5, jump=True, right=True)
    assert windy.player.x < calm.player.x - 50
