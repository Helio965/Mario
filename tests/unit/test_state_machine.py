"""FSM genérica e percepção: transições, tempos mínimos, timeouts e visão."""

from __future__ import annotations

from game.core.types import Platform, PlatformSpec, Rect
from game.enemies.perception import (
    Perception,
    PerceptionProfile,
    edge_ahead,
    line_of_sight,
    wall_ahead,
)
from game.enemies.state_machine import (
    Blackboard,
    State,
    StateMachine,
    Transition,
)
from game.enemies.state_machine import (
    EnemyStateName as S,
)


def build() -> StateMachine:
    states = {
        S.PATROL: State(S.PATROL, [Transition(S.ALERT, lambda bb: bb.player_visible, "viu")]),
        S.ALERT: State(
            S.ALERT,
            [Transition(S.PREPARE_ATTACK, lambda bb: bb.player_in_attack_range)],
            min_time=0.3,
            max_time=2.0,
            timeout_to=S.PATROL,
            animation="alert",
        ),
        S.PREPARE_ATTACK: State(
            S.PREPARE_ATTACK, [], max_time=0.4, timeout_to=S.ATTACK, telegraph=True
        ),
        S.ATTACK: State(S.ATTACK, [], max_time=0.2, timeout_to=S.RECOVER),
        S.RECOVER: State(
            S.RECOVER,
            [
                Transition(S.ALERT, lambda bb: bb.player_visible),
                Transition(S.PATROL, lambda bb: True),
            ],
            min_time=0.6,
        ),
        S.HURT: State(S.HURT, [], max_time=0.5, timeout_to=S.PATROL),
        S.DEFEATED: State(S.DEFEATED),
    }
    return StateMachine(states, S.PATROL)


def test_transitions_follow_observations_and_minimum_times() -> None:
    fsm = build()
    bb = Blackboard()
    assert fsm.update(1 / 60, bb) == S.PATROL
    bb.player_visible = True
    assert fsm.update(1 / 60, bb) == S.ALERT
    bb.player_in_attack_range = True
    for _ in range(10):  # 0,17 s < min_time 0,3 s: ainda em alerta (tempo de reação)
        assert fsm.update(1 / 60, bb) == S.ALERT
    for _ in range(10):
        name = fsm.update(1 / 60, bb)
    assert name == S.PREPARE_ATTACK
    assert fsm.current.telegraph


def test_timeouts_chain_prepare_attack_recover() -> None:
    fsm = build()
    bb = Blackboard(player_visible=True, player_in_attack_range=True)
    names = []
    for _ in range(int(2.5 * 60)):
        names.append(fsm.update(1 / 60, bb))
    order = [n for i, n in enumerate(names) if i == 0 or names[i - 1] != n]
    assert order[:5] == [S.ALERT, S.PREPARE_ATTACK, S.ATTACK, S.RECOVER, S.ALERT]


def test_alert_times_out_back_to_patrol_and_force_hurt() -> None:
    fsm = build()
    bb = Blackboard(player_visible=True)
    fsm.update(1 / 60, bb)
    bb.player_visible = False
    for _ in range(int(2.1 * 60)):
        fsm.update(1 / 60, bb)
    assert fsm.name == S.PATROL
    fsm.force(S.HURT, bb)
    assert fsm.name == S.HURT
    for _ in range(40):
        fsm.update(1 / 60, bb)
    assert fsm.name == S.PATROL
    fsm.force(S.DEFEATED, bb)
    assert fsm.update(1, bb) == S.DEFEATED


def test_perception_requires_reaction_time_and_forgets() -> None:
    enemy = Rect(100, 400, 28, 28)
    player = Rect(300, 400, 22, 30)
    p = Perception(PerceptionProfile(sight_range=400, reaction_time=0.25, forget_time=0.5))
    facts = p.observe(0.1, enemy, player, 1, [])
    assert not facts["player_visible"]
    for _ in range(3):
        facts = p.observe(0.1, enemy, player, 1, [])
    assert facts["player_visible"]
    assert facts["facing_player"]
    # Jogador atrás e fora do campo de visão traseiro: esquece depois do tempo.
    player.x = -200
    facts = p.observe(0.1, enemy, player, 1, [])
    assert facts["player_visible"], "ainda lembra por um instante"
    for _ in range(6):
        facts = p.observe(0.1, enemy, player, 1, [])
    assert not facts["player_visible"]


def test_line_of_sight_blocked_by_platform_and_edge_wall_probes() -> None:
    wall = Platform.from_spec(PlatformSpec("w", "brick", 200, 300, 40, 200))
    assert line_of_sight(100, 400, 300, 400, [])
    assert not line_of_sight(100, 400, 300, 400, [wall])
    hidden = Platform.from_spec(PlatformSpec("h", "hidden", 200, 300, 40, 200))
    assert line_of_sight(100, 400, 300, 400, [hidden]), "bloco oculto não revelado não bloqueia"
    floor = Platform.from_spec(PlatformSpec("f", "ground", 0, 448, 300, 100))
    enemy = Rect(270, 420, 28, 28)
    assert edge_ahead(enemy, 1, [floor]), "sonda em x=303 cai fora do chão (0..300)"
    assert not edge_ahead(enemy, -1, [floor])
    assert not edge_ahead(Rect(250, 420, 28, 28), 1, [floor])
    assert wall_ahead(Rect(170, 420, 28, 28), 1, [wall])
    assert not wall_ahead(Rect(100, 420, 28, 28), 1, [wall])
