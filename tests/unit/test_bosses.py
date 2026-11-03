"""Port de ``bosses.test.ts``: os cinco guardiões reais da campanha."""

from __future__ import annotations

from dataclasses import replace

import pytest

from game.core.game import Game
from game.core.types import InputState, ItemSpec, Level, Projectile, Vec
from game.enemies.legacy import hit_enemy
from game.levels.loader import load_levels
from game.physics.movement import FIXED_DT

LEVELS = load_levels()
BOSS_LEVELS = [lvl for lvl in LEVELS if any(e.kind == "boss" for e in lvl.enemies)]


def ticks(game: Game, count: int, **fields: bool) -> None:
    state = InputState(**fields)
    for _ in range(count):
        game.update(FIXED_DT, state)


def arena(source: Level, with_powers: bool = False) -> Game:
    boss = next(e for e in source.enemies if e.kind == "boss")
    offset = boss.patrol[0] - 300
    right = boss.patrol[1] - offset
    floor = next(
        p
        for p in source.platforms
        if p.y == boss.y + boss.h and p.x <= boss.x and p.x + p.w >= boss.x + boss.w
    )
    level = replace(
        source,
        width=right + 200,
        height=540,
        time=300,
        spawn=Vec(240, 418),
        checkpoint=Vec(240, 418),
        exit=Vec(right + 100, 448),
        platforms=[replace(floor, id="arena-floor", x=0, y=448, w=right + 200)],
        enemies=[replace(boss, x=boss.x - offset, patrol=[300, right])],
        coins=[],
        hazards=[],
        hints=[],
        items=[
            ItemSpec("arena-fire", "fire", 240, 418, 24, 24),
            ItemSpec("arena-star", "star", 240, 418, 24, 24),
        ]
        if with_powers
        else [],
    )
    game = Game([level])
    ticks(game, 2)
    return game


def test_exactly_one_guardian_per_world() -> None:
    assert [lvl.world for lvl in BOSS_LEVELS] == [1, 2, 3, 4, 5]
    assert [next(e for e in lvl.enemies if e.kind == "boss").hp for lvl in BOSS_LEVELS] == [
        3,
        4,
        5,
        6,
        7,
    ]


@pytest.mark.parametrize("level", BOSS_LEVELS, ids=[f"mundo-{lvl.world}" for lvl in BOSS_LEVELS])
class TestGuardian:
    def test_blocks_damage_outside_opening_and_one_hit_per_recovery(self, level: Level) -> None:
        game = arena(level)
        boss = game.enemies[0]
        health = boss.health
        boss.timer = 1.8
        ticks(game, 1)
        assert boss.state == "walk"
        assert hit_enemy(game, boss) is False
        assert boss.health == health
        boss.timer = 0.2
        ticks(game, 1)
        assert boss.state == "shell"
        assert hit_enemy(game, boss) is True
        assert boss.health == health - 1
        assert hit_enemy(game, boss) is False
        assert boss.health == health - 1

    def test_second_phase_closes_opening_earlier_runs_faster_and_tilts_projectile(
        self, level: Level
    ) -> None:
        calm = arena(level)
        angry = arena(level)
        angry.enemies[0].health = angry.enemies[0].health // 2
        for game in (calm, angry):
            game.enemies[0].timer = 1.3
        ticks(calm, 1)
        ticks(angry, 1)
        assert calm.enemies[0].state == "shell"
        assert angry.enemies[0].state == "walk"
        for game in (calm, angry):
            game.enemies[0].timer = 1.8
        ticks(calm, 1)
        ticks(angry, 1)
        assert abs(angry.enemies[0].vx) > abs(calm.enemies[0].vx)
        attack_time = 2.5 if level.world == 5 else 2.7
        for game in (calm, angry):
            game.enemies[0].timer = attack_time - FIXED_DT / 2
        ticks(calm, 1)
        ticks(angry, 1)
        assert len([s for s in calm.projectiles if s.hostile]) == 1
        assert len([s for s in angry.projectiles if s.hostile]) == 1
        assert calm.projectiles[0].vy == 0
        assert angry.projectiles[0].vy < 0

    def test_protects_exit_while_alive(self, level: Level) -> None:
        game = arena(level)
        game.player.x = game.level.exit.x
        ticks(game, 1)
        assert game.status == "playing"
        assert not any(e.type == "complete" for e in game.events)

    def test_defeated_with_collected_power_and_ability_then_normal_completion(
        self, level: Level
    ) -> None:
        game = arena(level, True)
        boss = game.enemies[0]
        assert game.player.power == "fire"
        assert game.player.star > 0
        jump_remaining = 0
        for _ in range(3000):
            if not boss.alive or game.status != "playing":
                break
            incoming = any(
                s.hostile
                and s.vx < 0
                and s.x > game.player.x
                and s.x - game.player.x < 145
                and s.y + s.h > game.player.y - 10
                and s.y < game.player.y + game.player.h
                for s in game.projectiles
            )
            if incoming and game.player.grounded and jump_remaining == 0:
                jump_remaining = 28
            ticks(game, 1, ability=True, jump=jump_remaining > 0)
            jump_remaining = max(0, jump_remaining - 1)
        assert game.status == "playing"
        assert not boss.alive
        assert len([e for e in game.events if e.type == "boss"]) == 1
        for _ in range(600):
            if game.status != "playing":
                break
            ticks(game, 1, right=True, run=True)
        assert game.status == "complete"
        assert game.player.animation == "win"
        assert len([e for e in game.events if e.type == "complete"]) == 1


def test_final_guardian_shoots_three_times_per_cycle_others_once() -> None:
    shots = []
    for level in BOSS_LEVELS:
        # Keep the observation alive through the complete cycle without attacking.
        game = arena(level, True)
        ticks(game, 430)
        shots.append(len([e for e in game.events if e.type == "shot"]))
    assert shots == [1, 1, 1, 1, 3]


def test_flyer_patrols_horizontally_and_oscillates_around_origin() -> None:
    source = next(lvl for lvl in LEVELS if any(e.kind == "flyer" for e in lvl.enemies))
    flyer = next(e for e in source.enemies if e.kind == "flyer")
    from game.core.types import PlatformSpec

    level = replace(
        source,
        spawn=Vec(72, 418),
        platforms=[PlatformSpec("floor", "ground", 0, 448, source.width, 92)],
        enemies=[replace(flyer, patrol=list(flyer.patrol))],
        items=[],
        coins=[],
        hazards=[],
        hints=[],
    )
    game = Game([level])
    enemy = game.enemies[0]
    initial_x = enemy.x
    min_y = max_y = enemy.y
    for _ in range(480):
        ticks(game, 1)
        min_y = min(min_y, enemy.y)
        max_y = max(max_y, enemy.y)
        assert enemy.x >= flyer.patrol[0]
        assert enemy.x + enemy.w <= flyer.patrol[1]
    assert enemy.x != initial_x
    assert max_y - min_y > 70
    assert min_y >= flyer.y - 38
    assert max_y <= flyer.y + 38


def test_hostile_projectile_deals_real_damage_and_disappears() -> None:
    game = arena(BOSS_LEVELS[0], True)
    game.enemies = []
    game.player.star = 0
    game.player.invulnerable = 0
    game.projectiles.append(
        Projectile(game.player.x + 40, game.player.y + 10, 12, 12, -180, 0, True, 3, True)
    )
    ticks(game, 20)
    assert game.player.power == "grown"
    assert game.lives == 5
    assert game.projectiles == []
    assert len([e for e in game.events if e.type == "hurt"]) == 1
