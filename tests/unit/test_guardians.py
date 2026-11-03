"""Os Cinco Guardiões: invariantes de justiça, fases e robô de justiça (docs/research/CHEFES.md §6–§7)."""

from __future__ import annotations

import pytest

from game.bosses.boss import MIN_TELEGRAPH_BY_WORLD, BossDefinition
from game.bosses.guardians import BRUMO, FORNALHO, GUARDIANS, LUMIA, OCULUS, ROLAO
from game.characters.abilities import grant_power
from game.core.game import Game
from game.enemies.state_machine import EnemyStateName as S
from tests.support.fairness_bot import FairnessBot
from tests.unit.helpers import STEP, level

FLOOR = 448.0
ARENA_LEFT, ARENA_RIGHT = 400.0, 1300.0


def arena_for(definition: BossDefinition, player_x: float = 200.0) -> Game:
    w, h = definition.size
    y = FLOOR - h - (4 if definition.floats else 0)
    if definition.kind == "lumia":
        y = FLOOR - 96 - h  # poleiro: copa a 96 px
    lvl = level(
        width=1700,
        spawn={"x": player_x, "y": FLOOR - 30},
        checkpoint={"x": 100, "y": FLOOR - 30},
        exit={"x": 1600, "y": FLOOR},
        platforms=[{"id": "floor", "kind": "ground", "x": 0, "y": FLOOR, "w": 1700, "h": 152}],
        enemies=[
            {
                "id": definition.kind,
                "kind": definition.kind,
                "x": 900,
                "y": y,
                "w": w,
                "h": h,
                "patrol": [ARENA_LEFT, ARENA_RIGHT],
            }
        ],
    )
    g = Game([lvl])
    g.player.invulnerable = 0
    return g


def fight(
    definition: BossDefinition, reaction: float = 0.25, seed: int = 0, max_seconds: float = 150.0
) -> tuple[Game, FairnessBot]:
    g = arena_for(definition)
    grant_power(g, "fire")
    bot = FairnessBot(
        g,
        definition,
        reaction,
        seed,
        floor=FLOOR,
        arena=(ARENA_LEFT, ARENA_RIGHT),
        walk=(ARENA_LEFT - 100, ARENA_RIGHT + 100),
    )
    boss = bot.boss
    for _ in range(int(max_seconds * 120)):
        g.update(STEP, bot.update())
        behavior = boss.behavior
        if behavior.state not in (S.HIDDEN, S.DEFEATED):
            assert behavior.active_hazards(g) <= behavior.phase.max_hazards, (
                "orçamento de perigos excedido"
            )
        if not boss.alive or g.status != "playing":
            break
    return g, bot


@pytest.mark.parametrize("definition", GUARDIANS, ids=[g.kind for g in GUARDIANS])
def test_definition_respects_fairness_invariants_and_world_floors(
    definition: BossDefinition,
) -> None:
    assert definition.validate() == []
    assert len(definition.phases) == 3
    floor = MIN_TELEGRAPH_BY_WORLD[definition.world]
    for index, phase in enumerate(definition.phases):
        expected = floor if index < 2 else max(0.4, floor * 0.85)
        for attack in phase.attacks:
            assert attack.telegraph >= expected - 1e-9, (definition.kind, phase.name, attack.name)
    verbs = [tuple(a.name for a in p.attacks) for p in definition.phases]
    assert len(set(verbs)) == 3


def test_hit_counts_follow_research() -> None:
    assert [g.hp for g in GUARDIANS] == [3, 3, 3, 4, 5]
    assert [g.world for g in GUARDIANS] == [1, 2, 3, 4, 5]
    assert LUMIA.floats and OCULUS.floats and not ROLAO.floats
    assert BRUMO.phases[2].vulnerable_sources == frozenset({"shell"})
    assert FORNALHO.phases[0].max_hazards == 1


@pytest.mark.parametrize("definition", GUARDIANS, ids=[g.kind for g in GUARDIANS])
@pytest.mark.parametrize("seed", [0, 1, 2])
def test_fairness_bot_wins_without_losing_health(definition: BossDefinition, seed: int) -> None:
    g, bot = fight(definition, reaction=0.25, seed=seed)
    boss = bot.boss
    assert bot.violations == [], bot.violations[:3]
    assert not boss.alive or boss.behavior.state == S.DEFEATED, (
        f"{definition.kind}: não derrotado em 150 s (fase {boss.behavior.phase_index + 1}, vida {boss.health})"
    )
    assert g.lives == 5
    assert g.player.power == "fire", f"{definition.kind}: o robô levou dano"
    assert bot.telegraphs >= bot.attack_starts > 0


@pytest.mark.parametrize("definition", GUARDIANS, ids=[g.kind for g in GUARDIANS])
def test_slow_bot_still_wins_with_at_most_two_hits(definition: BossDefinition) -> None:
    g, bot = fight(definition, reaction=0.4, seed=7)
    boss = bot.boss
    assert not boss.alive or boss.behavior.state == S.DEFEATED
    assert g.lives == 5, "duas falhas custam poder, nunca a vida"
