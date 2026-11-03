"""Habilidades por personagem sobre a física compartilhada (docs/research/PERSONAGENS.md §10)."""

from __future__ import annotations

from game.characters.abilities import grant_power
from game.characters.roster import FLOAT_MAX_DURATION
from game.core.game import Game
from game.core.types import InputState
from game.physics.movement import LEGACY_PROFILE
from tests.unit.helpers import STEP, level, ticks

FLOOR = {"id": "floor", "kind": "ground", "x": 0, "y": 448, "w": 6000, "h": 152}


def flight(character: str, hold_after_apex: bool) -> tuple[float, float]:
    """(tempo no ar, alcance) segurando ou não o salto após o ápice."""
    g = Game([level(width=6000, platforms=[FLOOR])], LEGACY_PROFILE, character)
    ticks(g, 120, right=True, run=True)
    x0 = g.player.x
    g.update(STEP, InputState(jump=True, right=True, run=True))
    t = STEP
    for _ in range(600):
        holding = g.player.vy < 0 or hold_after_apex
        g.update(STEP, InputState(jump=holding, right=True, run=True))
        t += STEP
        if g.player.grounded:
            break
    return t, g.player.x - x0


def test_lume_is_identical_to_base_profile() -> None:
    g = Game([level()], LEGACY_PROFILE, "lume")
    assert g.profile == LEGACY_PROFILE
    assert g.abilities == {"fire"}
    assert not g.invincible_model


def test_vento_scuttle_slows_the_fall_while_holding_jump() -> None:
    normal, _ = flight("vento", hold_after_apex=False)
    slow, _ = flight("vento", hold_after_apex=True)
    assert slow > normal + 0.06, (normal, slow)
    lume_hold, _ = flight("lume", hold_after_apex=True)
    lume_release, _ = flight("lume", hold_after_apex=False)
    assert abs(lume_hold - lume_release) < 2 * STEP, "Lume não tem scuttle"


def test_fagulha_charged_jump_after_crouching_still_and_moving_cancels() -> None:
    def jump_height(crouch_seconds: float, move_before: bool) -> float:
        g = Game([level(platforms=[FLOOR])], LEGACY_PROFILE, "fagulha")
        ticks(g, 30)
        ticks(g, round(crouch_seconds * 120), down=True)
        if move_before:
            ticks(g, 6, right=True)
        start = g.player.y
        peak = start
        g.update(STEP, InputState(jump=True, down=not move_before))
        for _ in range(200):
            g.update(STEP, InputState(jump=True))
            peak = min(peak, g.player.y)
            if g.player.grounded:
                break
        return start - peak

    base = jump_height(0.0, False)
    charged = jump_height(0.6, False)
    cancelled = jump_height(0.6, True)
    assert charged > base * 1.3, (base, charged)
    assert abs(cancelled - base) < 3
    g = Game([level(platforms=[FLOOR])], LEGACY_PROFILE, "fagulha")
    ticks(g, 30)
    ticks(g, 30, down=True)
    assert g.player.crouching and not g.player.charged
    ticks(g, 40, down=True)
    assert g.player.charged


def test_aurora_float_extends_air_time_once_with_bounded_reach() -> None:
    plain_t, plain_reach = flight("aurora", hold_after_apex=False)
    float_t, float_reach = flight("aurora", hold_after_apex=True)
    assert float_t > plain_t + 0.5
    assert float_t <= plain_t + FLOAT_MAX_DURATION + 0.1
    assert 0 < float_reach - plain_reach <= 180, "alcance extra limitado"
    g = Game([level(width=6000, platforms=[FLOOR])], LEGACY_PROFILE, "aurora")
    ticks(g, 30)
    g.update(STEP, InputState(jump=True))
    floated = False
    for _ in range(400):
        g.update(STEP, InputState(jump=True))
        floated = floated or g.player.floating
        if g.player.grounded:
            break
    assert floated
    assert g.player.float_used


def test_pirilampo_takes_knockback_instead_of_damage_but_dies_in_lava() -> None:
    enemy = {
        "id": "w",
        "kind": "walker",
        "x": 300,
        "y": 420,
        "w": 28,
        "h": 28,
        "patrol": [200, 600],
    }
    g = Game([level(platforms=[FLOOR], enemies=[enemy])], LEGACY_PROFILE, "pirilampo")
    assert g.time == 300 + 100
    ticks(g, 5)
    g.player.invulnerable = 0
    g.player.x = 290
    g.player.facing = 1
    ticks(g, 1)
    assert g.status == "playing"
    assert g.lives == 5
    assert g.player.power == "small"
    assert g.player.stun > 0
    assert g.player.vx < 0, "empurrado para trás"
    assert g.player.invulnerable == 0, "sem piscar"
    grant_power(g, "grow")
    assert g.player.power == "small"
    assert g.coins_total == 1
    grant_power(g, "fire")
    assert g.player.power == "small"
    ticks(g, 20, ability=True)
    assert g.projectiles == []
    lava = level(
        platforms=[FLOOR], hazards=[{"kind": "lava", "x": 50, "y": 410, "w": 100, "h": 40}]
    )
    h = Game([lava], LEGACY_PROFILE, "pirilampo")
    ticks(h, 2)
    assert h.status == "dead"
    assert h.lives == 4
