"""Arquétipos modernos convivem com os inimigos legados e usam percepção + FSM."""

from __future__ import annotations

from game.core.game import Game
from game.core.types import InputState
from game.enemies.registry import is_modern, known_enemy_kinds
from game.enemies.state_machine import EnemyStateName as S
from tests.unit.helpers import STEP, level, ticks


def stalker_level(
    player_x: float = 64, enemy_x: float = 700, patrol: tuple[int, int] = (100, 1100)
):
    return level(
        spawn={"x": player_x, "y": 418},
        platforms=[{"id": "floor", "kind": "ground", "x": 0, "y": 448, "w": 1200, "h": 152}],
        enemies=[
            {
                "id": "s",
                "kind": "stalker",
                "x": enemy_x,
                "y": 420,
                "w": 28,
                "h": 28,
                "patrol": list(patrol),
            }
        ],
    )


def test_registry_and_behavior_creation() -> None:
    assert is_modern("stalker") and not is_modern("walker")
    assert "stalker" in known_enemy_kinds() and "boss" in known_enemy_kinds()
    g = Game([stalker_level()])
    e = g.enemies[0]
    assert e.behavior is not None and e.behavior.state == S.PATROL
    assert e.anim == "walk"


def test_patrols_turning_at_edges_while_player_is_far() -> None:
    # Patrulha longe do jogador (fora do alcance de visão de 300 px).
    g = Game([stalker_level(player_x=64, enemy_x=650, patrol=(600, 1100))])
    e = g.enemies[0]
    facings = set()
    for _ in range(120 * 6):
        g.update(STEP, InputState())
        facings.add(e.facing)
        assert 600 <= e.x <= 1100 - e.w + 1
        assert e.behavior.state == S.PATROL
    assert facings == {-1, 1}
    assert abs(e.vx) == 55


def test_alerts_with_telegraph_then_chases_and_recovers() -> None:
    g = Game([stalker_level(player_x=500, enemy_x=700)])
    e = g.enemies[0]
    g.player.invulnerable = 0
    seen: list[S] = []
    telegraph_seen = False
    for _ in range(120 * 4):
        g.update(STEP, InputState(left=True))  # jogador se afasta devagar
        state = e.behavior.state
        telegraph_seen = telegraph_seen or e.telegraph
        if not seen or seen[-1] != state:
            seen.append(state)
        if S.RECOVER in seen:
            break
    assert seen[:4] == [S.PATROL, S.ALERT, S.CHASE, S.RECOVER], seen
    assert telegraph_seen
    assert g.status == "playing"


def test_chase_is_faster_than_patrol_and_faces_player() -> None:
    g = Game([stalker_level(player_x=400, enemy_x=760)])
    e = g.enemies[0]
    g.player.invulnerable = 0
    speeds = []
    for _ in range(120 * 2):
        g.update(STEP, InputState())
        if e.behavior.state == S.CHASE:
            speeds.append(abs(e.vx))
            assert e.facing == -1
    assert speeds and max(speeds) == 140


def test_stomp_defeats_and_side_contact_hurts() -> None:
    g = Game([stalker_level(player_x=64, enemy_x=300)])
    e = g.enemies[0]
    g.player.x = e.x - 3
    g.player.y = e.y - g.player.h - 2
    g.player.vy = 400
    g.player.grounded = False
    ticks(g, 2)
    assert not e.alive
    assert e.behavior.state == S.DEFEATED
    assert any(ev.type == "stomp" for ev in g.events)
    h = Game([stalker_level(player_x=64, enemy_x=300)])
    h.player.invulnerable = 0
    h.player.x = 290
    ticks(h, 1)
    assert h.status == "dead"


def test_legacy_kinds_unchanged_by_registry() -> None:
    g = Game(
        [
            level(
                enemies=[
                    {
                        "id": "w",
                        "kind": "walker",
                        "x": 300,
                        "y": 420,
                        "w": 28,
                        "h": 28,
                        "patrol": [200, 600],
                    }
                ]
            )
        ]
    )
    assert g.enemies[0].behavior is None
    ticks(g, 60)
    assert g.enemies[0].alive
