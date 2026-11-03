"""NPCs: rotinas, observação do jogador, interação e congelamento durante o diálogo."""

from __future__ import annotations

from game.core.game import Game
from game.core.types import InputState
from game.levels.loader import level_from_dict, level_to_dict
from tests.unit.helpers import STEP, level, ticks

FLOOR = {"id": "floor", "kind": "ground", "x": 0, "y": 448, "w": 2400, "h": 152}
GUIDE = {
    "id": "guia",
    "kind": "guide",
    "x": 600,
    "y": 416,
    "facing": -1,
    "routine": [
        {"action": "walk", "x": 700, "speed": 80},
        {"action": "wait", "seconds": 0.5},
        {"action": "look", "facing": -1},
        {"action": "emote", "expression": "happy", "seconds": 0.3},
        {"action": "say", "reaction": "greeting"},
        {"action": "walk", "x": 600, "speed": 80},
    ],
    "dialogue": "intro_1-1",
    "talk_once": True,
    "reactions": "lume",
}


def guide_level(player_x: float = 64):
    return level(spawn={"x": player_x, "y": 418}, platforms=[FLOOR], npcs=[GUIDE])


def test_round_trip_and_loading() -> None:
    lvl = guide_level()
    assert len(lvl.npcs) == 1 and lvl.npcs[0].dialogue == "intro_1-1"
    again = level_from_dict(level_to_dict(lvl))
    assert level_to_dict(again) == level_to_dict(lvl)
    assert "npcs" not in level_to_dict(level()), "fases sem NPC não ganham a chave"


def test_routine_walks_waits_looks_emotes_says_and_loops() -> None:
    g = Game([guide_level(player_x=64)])
    npc = g.npcs[0]
    ticks(g, 5)
    assert npc.grounded
    xs: set[int] = set()
    anims: set[str] = set()
    for _ in range(120 * 6):
        g.update(STEP, InputState())
        xs.add(round(npc.x))
        anims.add(npc.anim)
    assert max(xs) >= 699 and min(xs) <= 601, "anda entre 600 e 700"
    assert {"walk", "idle", "emote"} <= anims
    assert any(e.type == "npc_say" and e.text == "lume:greeting" for e in g.events)
    assert npc.state in ("routine", "observe")


def test_observes_player_when_near_and_resumes_when_far() -> None:
    g = Game([guide_level(player_x=64)])
    npc = g.npcs[0]
    ticks(g, 30)
    g.player.x = npc.x + 50
    ticks(g, 2)
    assert npc.state == "observe"
    assert npc.vx == 0
    assert npc.facing == 1
    assert npc.expression == "attentive"
    g.player.x = 64
    ticks(g, 2)
    assert npc.state == "routine"


def test_interaction_freezes_world_until_end_talk_and_only_once() -> None:
    g = Game([guide_level(player_x=64)])
    npc = g.npcs[0]
    ticks(g, 30)
    g.player.x = npc.x
    ticks(g, 1)
    ticks(g, 1, down=True)
    assert g.talking
    assert npc.state == "talk"
    assert [e.text for e in g.events if e.type == "talk"] == ["intro_1-1"]
    time_before = g.time
    x_before = g.player.x
    ticks(g, 60, right=True, run=True, jump=True)
    assert g.time == time_before and g.player.x == x_before, "mundo congelado durante o diálogo"
    g.end_talk()
    assert not g.talking and npc.state == "routine"
    ticks(g, 10, right=True)
    assert g.player.x > x_before
    g.player.x = npc.x
    ticks(g, 1)
    ticks(g, 1, down=True)
    assert not g.talking, "talk_once impede repetir"


def test_pipe_has_priority_over_npc_and_down_is_edge_triggered() -> None:
    pipe = {
        "id": "p",
        "kind": "pipe",
        "x": 580,
        "y": 400,
        "w": 56,
        "h": 48,
        "destination": {"x": 100, "y": 414},
    }
    lvl = level(
        spawn={"x": 590, "y": 370},
        platforms=[FLOOR, pipe],
        npcs=[{**GUIDE, "x": 590, "routine": []}],
    )
    g = Game([lvl])
    ticks(g, 30)
    ticks(g, 1, down=True)
    assert not g.talking
    assert any(e.type == "secret" for e in g.events)
    h = Game([guide_level(player_x=64)])
    ticks(h, 30)
    h.player.x = h.npcs[0].x
    ticks(h, 60, down=True)  # segurar ↓ não repete a interação
    assert h.talking
    h.end_talk()
    ticks(h, 5, down=True)
    assert not h.talking, "precisa soltar e pressionar de novo"
