"""Motor de chefes: justiça (telegraph/recuperação), fases, vulnerabilidade e derrota."""

from __future__ import annotations

from game.bosses.boss import (
    DEFAULT_GUARDIAN,
    Attack,
    BossDefinition,
    Phase,
    charge_attack,
    shoot_attack,
)
from game.core.game import Game
from game.core.types import InputState
from game.enemies.legacy import hit_enemy
from game.enemies.state_machine import EnemyStateName as S
from tests.unit.helpers import STEP, level


def arena(player_x: float = 200, boss_x: float = 900):
    return level(
        width=1600,
        spawn={"x": player_x, "y": 418},
        checkpoint={"x": 100, "y": 418},
        exit={"x": 1450, "y": 448},
        platforms=[{"id": "floor", "kind": "ground", "x": 0, "y": 448, "w": 1600, "h": 152}],
        enemies=[
            {
                "id": "g",
                "kind": "guardian",
                "x": boss_x,
                "y": 384,
                "w": 62,
                "h": 64,
                "patrol": [400, 1300],
                "hp": 6,
            }
        ],
    )


def run(g: Game, seconds: float, **fields: bool) -> None:
    state = InputState(**fields)
    for _ in range(round(seconds * 120)):
        g.update(STEP, state)


def test_definition_fairness_invariants() -> None:
    assert DEFAULT_GUARDIAN.validate() == []
    assert len(DEFAULT_GUARDIAN.phases) == 3
    sets = [tuple(a.name for a in p.attacks) for p in DEFAULT_GUARDIAN.phases]
    assert len(set(sets)) == 3, "cada fase muda o conjunto de ataques"
    unfair = BossDefinition(
        "x",
        3,
        [
            Phase("a", 1.0, [Attack("quick", 0.1, 0.2, 0.0)]),
            Phase("b", 0.5, [Attack("quick", 0.1, 0.2, 0.0)]),
        ],
    )
    problems = unfair.validate()
    assert any("telegraph" in p for p in problems)
    assert any("recuperação" in p for p in problems)
    assert any("mesmos ataques" in p for p in problems)


def test_waits_hidden_until_player_approaches_then_cycles_attacks_with_telegraph() -> None:
    g = Game([arena(player_x=100, boss_x=1100)])
    boss = g.enemies[0]
    behavior = boss.behavior
    run(g, 1.0)
    assert behavior.state == S.HIDDEN
    assert boss.vx == 0
    g.player.x = 700  # entra na arena
    seen: list[S] = [behavior.state]
    telegraph_before_attack = True
    for _ in range(120 * 6):
        g.update(STEP, InputState())
        st = behavior.state
        if not seen or seen[-1] != st:
            if st == S.ATTACK and (not seen or seen[-1] != S.PREPARE_ATTACK):
                telegraph_before_attack = False
            seen.append(st)
    assert seen[:4] == [S.HIDDEN, S.EMERGE, S.IDLE, S.PREPARE_ATTACK]
    assert S.ATTACK in seen and S.RECOVER in seen
    assert telegraph_before_attack
    assert any(e.type == "boss_intro" for e in g.events)
    assert any(e.type == "shot" for e in g.events), "o disparo da fase 1 ocorreu"


def test_vulnerable_only_in_windows_and_phases_change_with_health() -> None:
    g = Game([arena(player_x=600, boss_x=900)])
    boss = g.enemies[0]
    behavior = boss.behavior
    g.player.invulnerable = 0
    g.player.star = 0
    run(g, 0.1)
    # Avança até a preparação de um ataque: não vulnerável.
    for _ in range(120 * 3):
        g.update(STEP, InputState())
        if behavior.state == S.PREPARE_ATTACK:
            break
    assert behavior.state == S.PREPARE_ATTACK
    assert not boss.stompable
    assert hit_enemy(g, boss) is False
    # Espera a recuperação: vulnerável e o golpe conta.
    for _ in range(120 * 3):
        g.update(STEP, InputState())
        if behavior.state == S.RECOVER:
            break
    assert behavior.state == S.RECOVER
    assert boss.stompable
    assert hit_enemy(g, boss) is True
    assert boss.health == 5
    assert hit_enemy(g, boss) is False, "um golpe por janela"
    # Leva à segunda fase: vida ≤ 66 % (4/6) → STUNNED (troca anunciada) e depois fase 2.
    boss.hit_timer = 0
    for _ in range(120 * 3):
        g.update(STEP, InputState())
        if behavior.vulnerable and boss.hit_timer == 0:
            hit_enemy(g, boss)
            break
    assert boss.health == 4
    assert behavior.state == S.STUNNED
    assert any(e.type == "boss_phase" and e.value == 2 for e in g.events)
    run(g, 1.0)
    assert behavior.phase_index == 1
    assert behavior.phase.name == "combinação"


def test_defeat_keeps_exit_blocked_until_animation_ends_then_opens() -> None:
    g = Game([arena(player_x=600, boss_x=900)])
    boss = g.enemies[0]
    behavior = boss.behavior
    run(g, 0.1)
    # Golpes sucessivos apenas nas janelas vulneráveis.
    for _ in range(120 * 40):
        g.update(STEP, InputState())
        if behavior.vulnerable and boss.hit_timer == 0 and boss.alive:
            hit_enemy(g, boss)
        if behavior.state == S.DEFEATED:
            break
    assert behavior.state == S.DEFEATED
    assert boss.alive, "a animação de derrota mantém o chefe presente"
    assert any(e.type == "boss" for e in g.events)
    g.player.x = g.level.exit.x
    run(g, 0.5)
    assert g.status == "playing", "saída bloqueada durante a derrota"
    run(g, 2.0)
    assert not boss.alive
    g.player.x = g.level.exit.x
    run(g, 0.2)
    assert g.status == "complete"


def test_attacks_use_observable_player_position() -> None:
    g = Game([arena(player_x=400, boss_x=900)])
    boss = g.enemies[0]
    shoot = shoot_attack(count=1)
    charge = charge_attack()
    assert shoot.start is not None and charge.start is not None
    boss.behavior.target_x = g.player.x  # alvo congelado no 1.º quadro do aviso
    shoot.start(g, boss, boss.behavior)
    assert g.projectiles[-1].vx < 0, "atira na direção observada do jogador (à esquerda)"
    g.player.x = 1400
    charge.start(g, boss, boss.behavior)
    assert boss.facing == -1, "o ataque usa a posição observada no aviso, não a atual"
    boss.behavior.target_x = g.player.x
    charge.start(g, boss, boss.behavior)
    assert boss.facing == 1
