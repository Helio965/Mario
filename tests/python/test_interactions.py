"""Port of tests/unit/interactions.test.ts plus secrets and collectibles."""

from .conftest import game, run, ticks


def test_coin_once_and_relic_reward():
    g = game(spawn={"x": 70, "y": 414}, coins=[{"id": "c", "x": 70, "y": 418}],
             collectibles=[{"id": "r", "kind": "relic", "x": 90, "y": 418}])
    ticks(g, 2)
    assert g.coins_total == 1 and g.score == 1100 and g.found_relic
    assert g.found == {"r"}
    ticks(g, 30)
    assert g.score == 1100


def test_question_block_from_below_once():
    q = {"id": "q", "kind": "question", "reward": "coin", "x": 64, "y": 336, "w": 32, "h": 32}
    g = game(spawn={"x": 70, "y": 414}, extra_platforms=[q])
    ticks(g, 20)
    ticks(g, 60, jump=True)
    assert g.platform_by_id["q"].used and g.coins_total == 1
    ticks(g, 50)
    ticks(g, 70, jump=True)
    assert g.coins_total == 1


def test_pipe_requires_down_and_reports_secret():
    pipe = {"id": "p", "kind": "pipe", "x": 64, "y": 432, "w": 48, "h": 16, "warp": {"x": 600, "y": 414}, "secret": "room"}
    g = game(spawn={"x": 70, "y": 400}, extra_platforms=[pipe],
             secrets=[{"id": "room", "kind": "warp_room", "clue": "seta", "rewards": []}])
    ticks(g, 20)
    assert g.player.x == 70
    ticks(g, 1, down=True)
    assert g.player.x == 600
    assert any(e.type == "secret" for e in g.events)
    assert g.secrets_found == {"room"}


def test_moving_platform_carries_and_crumble_respawns():
    moving = {"id": "m", "kind": "moving", "x": 80, "y": 400, "w": 100, "h": 16, "motion": {"axis": "x", "range": 40, "speed": 1}}
    g = game(spawn={"x": 100, "y": 370}, extra_platforms=[moving])
    ticks(g, 10)
    x = g.player.x
    ticks(g, 30)
    assert g.player.x > x + 4
    c = game(spawn={"x": 90, "y": 370}, extra_platforms=[{"id": "c", "kind": "crumble", "x": 80, "y": 400, "w": 100, "h": 16}])
    ticks(c, 100)
    assert not c.platform_by_id["c"].alive
    ticks(c, 400)
    assert c.platform_by_id["c"].alive


def test_hidden_block_revealed_from_below_registers_secret():
    hidden = {"id": "h", "kind": "hidden", "reward": "star", "x": 64, "y": 336, "w": 40, "h": 24, "secret": "hidden_h"}
    g = game(extra_platforms=[hidden], secrets=[{"id": "hidden_h", "kind": "hidden_block", "clue": "luzes", "rewards": []}])
    ticks(g, 20)
    assert not g.platform_by_id["h"].used
    ticks(g, 60, jump=True)
    assert g.platform_by_id["h"].used
    assert "hidden_h" in g.secrets_found
    assert any(i.kind == "star" for i in g.items) or g.player.star > 0


def test_coin_groups_expand_with_stable_ids():
    g = game(coin_groups=[{"id": "row", "shape": "row", "x": 300, "y": 400, "count": 4},
                          {"id": "arc", "shape": "arc", "x": 600, "y": 400, "count": 5}])
    ids = [c.id for c in g.coins if not c.special]
    assert ids == ["row-1", "row-2", "row-3", "row-4", "arc-1", "arc-2", "arc-3", "arc-4", "arc-5"]
    arc = [c for c in g.coins if c.id.startswith("arc")]
    assert arc[2].y < arc[0].y  # middle of the arc is higher


def test_multiple_checkpoints_respawn_at_furthest():
    g = game(checkpoints=[{"id": "a", "x": 300, "y": 414}, {"id": "b", "x": 600, "y": 414}])
    ticks(g, 2)
    run(g, 3, right=True)
    assert g.last_checkpoint is not None and g.last_checkpoint.id == "b"
