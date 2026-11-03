"""Port of tests/unit/bosses.test.ts for the five legacy guardians (now
mid-bosses of slot 3) plus the Reino Verde fortress boss."""

from dataclasses import replace

import pytest

from lume.core.constants import FIXED_DT
from lume.core.game import Game
from lume.core.input import InputState
from lume.levels.campaign import load_campaign
from lume.levels.schema import CheckpointSpec, EnemySpec, ExitSpec, ItemSpec, PlatformSpec, Point

from .conftest import game, ticks

CAMPAIGN = load_campaign()
GUARDIAN_LEVELS = [lvl for lvl in CAMPAIGN.levels if any(e.species.startswith("guardiao_") for e in lvl.enemies)]


def arena(source, with_powers=False) -> Game:
    boss = next(e for e in source.enemies if e.species.startswith("guardiao_"))
    offset = boss.patrol[0] - 300
    right = boss.patrol[1] - offset
    level = replace(
        source,
        width=right + 200, height=540, time_limit=300,
        spawn=Point(240, 418), checkpoints=(CheckpointSpec("cp", 240, 418),),
        exit=ExitSpec("goal", "flag", right + 100, 448),
        platforms=(PlatformSpec("arena_floor", "ground", 0, 448, right + 200, 92),),
        enemies=(replace(boss, x=boss.x - offset, patrol=(300, right)),),
        coins=(), hazards=(), hints=(), zones=(), areas=(replace(source.areas[0], w=right + 200, h=540),),
        items=(ItemSpec("fire", "fire", 240, 418), ItemSpec("star", "star", 240, 418)) if with_powers else (),
    )
    g = Game([level])
    ticks(g, 2)
    return g


def test_one_guardian_per_legacy_world_in_slot_three():
    assert [lvl.id for lvl in GUARDIAN_LEVELS] == ["orchard_guardian", "sand_temple", "blizzard_heart", "ancestral_tree", "last_flame"]
    assert [next(e.hp for e in lvl.enemies if e.species.startswith("guardiao_")) for lvl in GUARDIAN_LEVELS] == [3, 4, 5, 6, 7]
    for lvl in GUARDIAN_LEVELS:
        assert CAMPAIGN.entry(lvl.id).slot == 3


@pytest.mark.parametrize("source", GUARDIAN_LEVELS, ids=lambda lvl: lvl.id)
class TestGuardian:
    def test_damage_only_in_window_and_once_per_recovery(self, source):
        g = arena(source)
        boss = g.enemies[0]
        health = boss.health
        boss.timer = 1.8
        ticks(g, 1)
        assert boss.state == "walk"
        assert not g.hit_enemy(boss)
        boss.timer = 0.2
        ticks(g, 1)
        assert boss.state == "shell"
        assert g.hit_enemy(boss)
        assert boss.health == health - 1
        assert not g.hit_enemy(boss)

    def test_second_phase_is_faster_and_shots_arc(self, source):
        calm, angry = arena(source), arena(source)
        angry.enemies[0].health = angry.enemies[0].health // 2
        for g in (calm, angry):
            g.enemies[0].timer = 1.3
            ticks(g, 1)
        assert calm.enemies[0].state == "shell" and angry.enemies[0].state == "walk"
        for g in (calm, angry):
            g.enemies[0].timer = 1.8
            ticks(g, 1)
        assert abs(angry.enemies[0].vx) > abs(calm.enemies[0].vx)
        tier = calm.enemies[0].params.get("tier") or calm.profiles[calm.enemies[0].species].params["tier"]
        attack = 2.5 if tier >= 5 else 2.7
        for g in (calm, angry):
            g.enemies[0].timer = attack - FIXED_DT / 2
            ticks(g, 1)
        assert len([s for s in calm.projectiles if s.hostile]) == 1
        assert len([s for s in angry.projectiles if s.hostile]) == 1
        assert calm.projectiles[0].vy == 0 and angry.projectiles[0].vy < 0

    def test_exit_locked_while_alive(self, source):
        g = arena(source)
        g.player.x = g.level.exit.x
        ticks(g, 1)
        assert g.status == "playing"
        assert not any(e.type == "complete" for e in g.events)

    def test_defeated_with_collected_powers(self, source):
        g = arena(source, with_powers=True)
        boss = g.enemies[0]
        assert g.player.power == "fire" and g.player.star > 0
        jump = 0
        for _ in range(3000):
            if not boss.alive or g.status != "playing":
                break
            incoming = any(
                s.hostile and s.vx < 0 and s.x > g.player.x and s.x - g.player.x < 145
                and s.y + s.h > g.player.y - 10 and s.y < g.player.y + g.player.h
                for s in g.projectiles
            )
            if incoming and g.player.grounded and jump == 0:
                jump = 28
            g.update(FIXED_DT, InputState(ability=True, jump=jump > 0))
            jump = max(0, jump - 1)
        assert g.status == "playing" and not boss.alive
        assert any(e.type == "boss" for e in g.events)
        for _ in range(2400):
            if g.status != "playing":
                break
            g.update(FIXED_DT, InputState(right=True))
        assert g.status == "complete"


def _boar_level():
    from .conftest import level

    return level(
        bounds={"width": 1400, "height": 540},
        exit={"id": "goal", "kind": "flag", "x": 1300, "y": 448},
        checkpoints=[],
        platforms=[
            {"id": "floor", "kind": "ground", "x": 0, "y": 448, "w": 1400, "h": 92},
            {"id": "wall_l", "kind": "ground", "x": 100, "y": 200, "w": 40, "h": 248},
            {"id": "wall_r", "kind": "ground", "x": 1000, "y": 200, "w": 40, "h": 248},
        ],
        spawn={"x": 300, "y": 418},
        enemies=[{"id": "boss", "species": "javali_espinheiro", "x": 800, "y": 448, "patrol": [140, 1000]}],
        role="fortress",
    )


def test_thorn_boar_cycle_and_wall_crash_opens_window():
    g = Game([_boar_level()])
    boss = g.enemies[0]
    g.player.x = 500
    g.player.invulnerable = 999
    seen = set()
    for _ in range(int(12 * 120)):
        g.update(FIXED_DT, InputState())
        seen.add(boss.state)
        if boss.state == "stunned":
            break
    assert {"intro", "stalk", "telegraph", "charge", "stunned"} <= seen
    assert any(e.type == "crash" for e in g.events)
    beh = g.behaviors[boss.species]
    assert beh.stompable(g, boss) and not beh.spiked(g, boss)


def test_thorn_boar_spiked_outside_window_and_three_stomps_defeat():
    g = Game([_boar_level()])
    boss = g.enemies[0]
    beh = g.behaviors[boss.species]
    boss.set_state("stalk")
    assert beh.spiked(g, boss) and not beh.stompable(g, boss)
    for hit in range(3):
        boss.set_state("stunned")
        boss.hit_timer = 0
        g.player.x, g.player.y = boss.x + 20, boss.y - g.player.h - 2
        g.player.vy, g.player.grounded = 400, False
        ticks(g, 2)
        if hit < 2:
            assert boss.alive and boss.state == "hurt"
    assert not boss.alive
    assert any(e.type == "boss" for e in g.events)


def test_thorn_boar_second_phase_drops_thorns():
    g = Game([_boar_level()])
    boss = g.enemies[0]
    boss.health = 1
    boss.set_state("charge")
    boss.facing = 1
    for _ in range(600):
        g.update(FIXED_DT, InputState())
        if boss.state == "stunned":
            break
    assert boss.state == "stunned"
    assert len([s for s in g.projectiles if s.kind == "thorn_acorn"]) == 3


def _scarab_level():
    from .conftest import level

    return level(
        world="golden_desert",
        bounds={"width": 1400, "height": 540},
        exit={"id": "goal", "kind": "flag", "x": 1300, "y": 448},
        checkpoints=[],
        platforms=[
            {"id": "floor", "kind": "ground", "x": 0, "y": 448, "w": 1400, "h": 92},
            {"id": "wall_l", "kind": "ground", "x": 100, "y": 200, "w": 40, "h": 248},
            {"id": "wall_r", "kind": "ground", "x": 1000, "y": 200, "w": 40, "h": 248},
        ],
        spawn={"x": 500, "y": 418},
        enemies=[{"id": "boss", "species": "escaravelho_rei", "x": 760, "y": 448, "patrol": [140, 1000]}],
        role="fortress",
    )


def test_scarab_king_cycle_has_telegraph_and_single_stomp_window():
    g = Game([_scarab_level()])
    boss = g.enemies[0]
    beh = g.behaviors[boss.species]
    g.player.invulnerable = 999
    seen = []
    for _ in range(int(14 * 120)):
        g.update(FIXED_DT, InputState())
        if not seen or seen[-1] != boss.state:
            seen.append(boss.state)
            if boss.state in ("burrow", "telegraph"):
                assert not beh.tangible(g, boss)
            if boss.state in ("erupt", "roll"):
                assert beh.spiked(g, boss) and not beh.stompable(g, boss)
            if boss.state == "dazed":
                assert beh.stompable(g, boss)
    order = [s for s in seen if s in ("burrow", "telegraph", "erupt", "dazed", "roll")]
    assert order[:5] == ["burrow", "telegraph", "erupt", "dazed", "roll"]


def test_scarab_king_three_stomps_and_angry_sand_balls():
    g = Game([_scarab_level()])
    boss = g.enemies[0]
    for hit in range(3):
        boss.set_state("dazed")
        boss.hit_timer = 0
        g.player.x, g.player.y = boss.x + 20, boss.y - g.player.h - 2
        g.player.vy, g.player.grounded = 400, False
        ticks(g, 2)
        if hit < 2:
            assert boss.alive and boss.state == "hurt"
    assert not boss.alive
    g2 = Game([_scarab_level()])
    b2 = g2.enemies[0]
    b2.health = 1
    b2.set_state("telegraph")
    for _ in range(120):
        g2.update(FIXED_DT, InputState())
        if b2.state == "erupt":
            break
    assert len([s for s in g2.projectiles if s.kind == "sand"]) == 3
