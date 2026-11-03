"""Port de ``combat.test.ts``: dano, pisão, casco, armadura, fogo, estrela, perigos."""

from __future__ import annotations

from game.characters.abilities import grant_power
from game.core.game import Game
from game.core.types import InputState
from tests.unit.helpers import STEP, level


def arena(kind: str = "walker", hp: int = 1):
    return level(
        width=1800,
        spawn={"x": 64, "y": 414},
        checkpoint={"x": 900, "y": 414},
        exit={"x": 1700, "y": 448},
        platforms=[{"id": "g", "kind": "ground", "x": 0, "y": 448, "w": 1800, "h": 100}],
        enemies=[
            {
                "id": "e",
                "kind": kind,
                "x": 180,
                "y": 420,
                "w": 28,
                "h": 28,
                "patrol": [160, 600],
                "hp": hp,
            }
        ],
    )


def run(g: Game, n: int, ability: bool = False) -> None:
    for _ in range(n):
        g.update(STEP, InputState(ability=ability))


def stomp(g: Game) -> None:
    e = g.enemies[0]
    g.player.x = e.x - 3
    g.player.y = e.y - g.player.h - 2
    g.player.vy = 400
    g.player.grounded = False
    run(g, 2)


def test_side_contact_defeats_player_and_stomp_defeats_enemy() -> None:
    g = Game([arena()])
    g.player.invulnerable = 0
    g.player.x = 176
    run(g, 1)
    assert g.status == "dead"
    assert g.lives == 4
    h = Game([arena()])
    stomp(h)
    assert not h.enemies[0].alive
    assert h.player.vy < 0


def test_power_absorbs_damage_and_invulnerability_prevents_repeat() -> None:
    g = Game([arena()])
    grant_power(g, "grow")
    assert g.player.h == 46
    g.player.invulnerable = 0
    g.hurt()
    assert g.player.power == "small"
    assert g.lives == 5
    g.hurt()
    assert g.lives == 5


def test_growth_delays_expansion_under_low_ceiling() -> None:
    lvl = arena()
    lvl.platforms.append(
        __import__("game.levels.loader", fromlist=["platform_from_dict"]).platform_from_dict(
            {"id": "roof", "kind": "brick", "x": 50, "y": 375, "w": 90, "h": 32}
        )
    )
    g = Game([lvl])
    run(g, 20)
    grant_power(g, "grow")
    assert g.player.power == "grown"
    assert g.player.h == 30
    g.player.x = 250
    run(g, 2)
    assert g.player.h == 46
    assert g.player.y + g.player.h == 448


def test_shell_retracts_slides_and_hits_other_enemy() -> None:
    lvl = arena("shell")
    from game.core.types import EnemySpec

    lvl.enemies.append(EnemySpec("other", "walker", 280, 420, 28, 28, [270, 600]))
    g = Game([lvl])
    stomp(g)
    assert g.enemies[0].state == "shell"
    g.player.x = 70
    run(g, 100)
    stomp(g)
    assert g.enemies[0].state == "slide"
    g.player.x = 70
    run(g, 80)
    assert not g.enemies[1].alive


def test_armor_resists_first_stomp() -> None:
    g = Game([arena("armored", 2)])
    stomp(g)
    assert g.enemies[0].health == 1
    assert g.enemies[0].alive
    g.player.x = 70
    run(g, 100)
    stomp(g)
    assert not g.enemies[0].alive


def test_fire_flower_projectiles_defeat_enemies_and_expire() -> None:
    g = Game([arena()])
    grant_power(g, "fire")
    run(g, 55, ability=True)
    assert not g.enemies[0].alive
    run(g, 400)
    assert g.projectiles == []


def test_star_grants_immunity_and_pause_preserves_duration() -> None:
    g = Game([arena()])
    grant_power(g, "star")
    g.player.invulnerable = 0
    g.hurt()
    assert g.lives == 5
    g.player.x = 180
    run(g, 1)
    assert not g.enemies[0].alive
    star = g.player.star
    g.pause()
    run(g, 100)
    assert g.player.star == star
    g.resume()
    run(g, 1500)
    assert g.player.star == 0


def test_shooter_fires_when_player_in_range() -> None:
    g = Game([arena("shooter")])
    run(g, 270)
    assert any(s.hostile for s in g.projectiles)
    assert any(e.type == "shot" for e in g.events)


def test_water_and_lava_cost_a_life_even_when_invincible() -> None:
    for kind in ("water", "lava"):
        lvl = arena()
        lvl.enemies = []
        from game.core.types import Hazard

        lvl.hazards = [Hazard(kind, 50, 410, 100, 40)]
        g = Game([lvl])
        grant_power(g, "star")
        run(g, 1)
        assert g.status == "dead"
        assert g.lives == 4
