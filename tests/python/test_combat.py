"""Port of tests/unit/combat.test.ts using the biome species that replaced the
legacy generic kinds (same hitboxes and tuning)."""

import pytest

from lume.core.constants import PLAYER_BIG_HEIGHT

from .conftest import game, ticks


def arena(species="bolota", hp=None, **extra):
    enemy = {"id": "e", "species": species, "x": 180, "y": 448, "patrol": [160, 600]}
    if hp:
        enemy["hp"] = hp
    enemies = [enemy] + extra.pop("more_enemies", [])
    return game(enemies=enemies, spawn={"x": 64, "y": 414}, **extra)


def stomp(g, index=0):
    e = g.enemies[index]
    g.player.x = e.x - 3
    g.player.y = e.y - g.player.h - 2
    g.player.vy = 400
    g.player.grounded = False
    ticks(g, 2)


def test_side_contact_kills_small_player_and_stomp_defeats():
    g = arena()
    g.player.invulnerable = 0
    g.player.x = 176
    ticks(g, 1)
    assert g.status == "dead" and g.lives == 4
    h = arena()
    stomp(h)
    assert not h.enemies[0].alive and h.player.vy < 0


def test_power_absorbs_hit_and_invulnerability():
    g = arena()
    g.grant_power("grow")
    assert g.player.h == PLAYER_BIG_HEIGHT
    g.player.invulnerable = 0
    g.hurt()
    assert g.player.power == "small" and g.lives == 5
    g.hurt()
    assert g.lives == 5


def test_growth_waits_for_headroom():
    g = arena(platforms=[{"id": "g", "kind": "ground", "x": 0, "y": 448, "w": 2400, "h": 92},
                         {"id": "roof", "kind": "brick", "x": 50, "y": 375, "w": 90, "h": 32}])
    ticks(g, 20)
    g.grant_power("grow")
    assert g.player.power == "grown" and g.player.h == 30
    g.player.x = 250
    ticks(g, 2)
    assert g.player.h == PLAYER_BIG_HEIGHT and g.player.y + g.player.h == 448


def test_shell_slides_and_hits_other_enemy():
    g = arena("caramujo", more_enemies=[{"id": "other", "species": "bolota", "x": 280, "y": 448, "patrol": [270, 600]}])
    stomp(g)
    assert g.enemies[0].state == "shell"
    g.player.x = 70
    ticks(g, 100)
    stomp(g)
    assert g.enemies[0].state == "slide"
    g.player.x = 70
    ticks(g, 80)
    assert not g.enemies[1].alive


def test_shell_wakes_up_after_recover_time():
    g = arena("caramujo")
    stomp(g)
    g.player.x = 1000
    ticks(g, int(7.2 * 120))
    assert g.enemies[0].state == "walk"


def test_armor_resists_first_stomp():
    g = arena("besouro_casca", hp=2, world="enchanted_forest")
    stomp(g)
    assert g.enemies[0].health == 1 and g.enemies[0].alive
    g.player.x = 70
    ticks(g, 100)
    stomp(g)
    assert not g.enemies[0].alive


def test_fire_projectiles_defeat_and_expire():
    g = arena()
    g.grant_power("fire")
    ticks(g, 55, ability=True)
    assert not g.enemies[0].alive
    ticks(g, 400)
    assert g.projectiles == []


def test_fire_immune_species_deflects_fire():
    g = arena("brasa_andante", world="volcanic_fortress")
    g.grant_power("fire")
    ticks(g, 55, ability=True)
    assert g.enemies[0].alive
    assert any(e.type == "deflect" for e in g.events)


def test_star_immunity_and_pause_preserves_duration():
    g = arena()
    g.grant_power("star")
    g.player.invulnerable = 0
    g.hurt()
    assert g.lives == 5
    g.player.x = 180
    ticks(g, 1)
    assert not g.enemies[0].alive
    star = g.player.star
    g.pause()
    ticks(g, 100)
    assert g.player.star == star
    g.resume()
    ticks(g, 1500)
    assert g.player.star == 0


def test_shooter_fires_when_player_in_range():
    g = arena("cacto_sentinela", world="golden_desert")
    ticks(g, 270)
    assert any(s.hostile for s in g.projectiles)
    assert any(e.type == "shot" for e in g.events)


@pytest.mark.parametrize("kind", ["water", "lava"])
def test_water_and_lava_cost_a_life_even_with_star(kind):
    g = game(hazards=[{"id": "h", "kind": kind, "x": 50, "y": 410, "w": 100, "h": 40}], spawn={"x": 64, "y": 414},
             checkpoints=[])
    g.grant_power("star")
    ticks(g, 1)
    assert g.status == "dead" and g.lives == 4


def test_winged_beetle_loses_wings_on_stomp():
    g = arena("besouro_alado", more_enemies=[])
    e = g.enemies[0]
    e.y = 380
    e.origin_y = 380
    stomp(g)
    assert e.alive and e.species == "besouro"
    assert any(ev.type == "wings_lost" for ev in g.events)


def test_spiked_species_hurts_on_stomp():
    g = arena("ourico_espinho")
    g.grant_power("grow")
    g.player.invulnerable = 0
    stomp(g)
    assert g.enemies[0].alive
    assert g.player.power == "small"
