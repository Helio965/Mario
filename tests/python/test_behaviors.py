"""Behaviour families added in the Python edition."""

from lume.core.behaviors import BEHAVIORS
from lume.core.species import load_profiles

from .conftest import game, ticks


def one(species, **extra):
    enemy = {"id": "e", "species": species, "x": 400, "y": 448, "patrol": [200, 900]}
    enemy.update(extra.pop("enemy", {}))
    return game(enemies=[enemy], **extra)


def test_every_species_has_registered_behavior_and_defeat_state():
    for profile in load_profiles().values():
        assert profile.behavior in BEHAVIORS, profile.id
        assert "defeat" in profile.animation_states


def test_walker_notices_player_once_then_patrols():
    g = one("bolota", spawn={"x": 250, "y": 418})
    states = []
    for _ in range(120):
        ticks(g, 1)
        states.append(g.enemies[0].anim)
    assert "alert" in states and states[-1] == "walk"


def test_emerger_hides_rises_and_is_intangible_while_hidden():
    g = one("flor_mordedora", spawn={"x": 64, "y": 418})
    e = g.enemies[0]
    beh = g.behaviors[e.species]
    assert e.state == "hidden" and not beh.tangible(g, e)
    seen = set()
    for _ in range(int(5 * 120)):
        ticks(g, 1)
        seen.add(e.state)
    assert {"hidden", "rise", "out", "retreat"} <= seen
    assert not beh.stompable(g, e)


def test_emerger_stays_hidden_when_player_is_next_to_it():
    g = one("flor_mordedora", spawn={"x": 400, "y": 418})
    e = g.enemies[0]
    ticks(g, int(4 * 120))
    assert e.state == "hidden"


def test_hopper_anticipates_before_jumping():
    g = one("cogumelo_saltitante", world="enchanted_forest", spawn={"x": 64, "y": 418})
    e = g.enemies[0]
    order = []
    for _ in range(int(4 * 120)):
        ticks(g, 1)
        if not order or order[-1] != e.state:
            order.append(e.state)
    assert "crouch" in order and "jump" in order
    assert order.index("crouch") < order.index("jump")


def test_charger_telegraphs_charges_and_is_stunned_by_wall():
    wall = {"id": "wall", "kind": "ground", "x": 150, "y": 300, "w": 40, "h": 148}
    g = one("carneiro_glacial", world="frozen_peaks", spawn={"x": 260, "y": 418}, extra_platforms=[wall],
            enemy={"x": 600, "patrol": [190, 900]})
    e = g.enemies[0]
    g.player.invulnerable = 99
    seen = []
    for _ in range(int(6 * 120)):
        ticks(g, 1)
        if not seen or seen[-1] != e.state:
            seen.append(e.state)
        if e.state == "stunned":
            break
    assert "alert" in seen and "charge" in seen and seen[-1] == "stunned"
    assert seen.index("alert") < seen.index("charge")


def test_slider_belly_slides_on_ice():
    g = one("pinguim_patrulha", world="frozen_peaks", spawn={"x": 150, "y": 418},
            platforms=[{"id": "ice", "kind": "ground", "x": 0, "y": 448, "w": 2400, "h": 92, "surface": "ice"}])
    e = g.enemies[0]
    ticks(g, 60)
    assert e.state == "slide" and abs(e.vx) > 200


def test_desert_scarab_burrows_and_is_intangible():
    g = one("escaravelho_areia", world="golden_desert", spawn={"x": 64, "y": 418})
    e = g.enemies[0]
    beh = g.behaviors[e.species]
    found = False
    for _ in range(int(6 * 120)):
        ticks(g, 1)
        if e.state == "burrow" and e.anim == "burrow":
            assert not beh.tangible(g, e)
            found = True
    assert found


def test_scorpion_tail_makes_it_spiked_periodically():
    g = one("escorpiao_couraca", world="golden_desert", spawn={"x": 64, "y": 418})
    e = g.enemies[0]
    beh = g.behaviors[e.species]
    spiked = set()
    for _ in range(int(4 * 120)):
        ticks(g, 1)
        spiked.add(beh.spiked(g, e))
    assert spiked == {True, False}


def test_bones_collapse_and_reassemble():
    from lume.core.species import EnemyProfile, parse_profiles
    import json
    from pathlib import Path

    data = json.loads((Path(__file__).resolve().parents[2] / "lume" / "data" / "enemies.json").read_text())
    data["species"].append({**data["species"][0], "id": "ossada_teste", "behavior": "bones", "habitats": ["grassland"],
                            "weaknesses": ["shell", "star"], "animation_states": ["walk", "pile", "defeat"]})
    profiles = parse_profiles(data)
    from lume.core.game import Game
    from .conftest import level

    g = Game([level(enemies=[{"id": "e", "species": "ossada_teste", "x": 400, "y": 448, "patrol": [200, 900]}])], profiles=profiles)
    e = g.enemies[0]
    g.player.x, g.player.y, g.player.vy, g.player.grounded = e.x - 3, e.y - g.player.h - 2, 400, False
    ticks(g, 2)
    assert e.alive and e.state == "pile"
    g.player.x = 64
    ticks(g, int(4.2 * 120))
    assert e.state == "walk"


def test_activation_keeps_far_enemies_frozen_until_near():
    g = one("bolota", enemy={"x": 1800, "patrol": [1700, 2000]})
    e = g.enemies[0]
    x = e.x
    ticks(g, 120)
    assert not e.active and e.x == x
