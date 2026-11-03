"""Perfil calibrado pela pesquisa (docs/research/FISICA.md §10, MOVIMENTACAO.md §13).

Confere as previsões matemáticas do modelo contra a simulação discreta de
1/120 s e garante que o perfil legado continua intocado.
"""

from __future__ import annotations

import math

import pytest

from game.core.game import Game
from game.core.types import InputState
from game.physics.movement import CALIBRATED_PROFILE, LEGACY_PROFILE, PROFILES, MovementProfile
from tests.unit.helpers import STEP, level, ticks


def simulate_jump(
    profile: MovementProfile, hold: float, vx_input: bool = False
) -> tuple[float, float, float]:
    """Devolve (altura alcançada, tempo até o ápice, tempo total no ar) com a física real."""
    g = Game(
        [
            level(
                width=6000,
                platforms=[{"id": "floor", "kind": "ground", "x": 0, "y": 448, "w": 6000, "h": 92}],
            )
        ],
        profile,
    )
    ticks(g, 120, right=vx_input, run=vx_input)
    assert g.player.grounded
    start_y = g.player.y
    peak = start_y
    t_peak = t_air = 0.0
    t = 0.0
    g.update(STEP, InputState(jump=True, right=vx_input, run=vx_input))
    for _ in range(600):
        t += STEP
        g.update(STEP, InputState(jump=t < hold, right=vx_input, run=vx_input))
        if g.player.y < peak:
            peak = g.player.y
            t_peak = t
        if g.player.grounded:
            t_air = t
            break
    return start_y - peak, t_peak, t_air


@pytest.mark.parametrize("name", list(PROFILES))
def test_full_jump_matches_analytic_predictions(name: str) -> None:
    profile = PROFILES[name]
    height, t_peak, t_air = simulate_jump(profile, hold=2.0)
    # Euler semi-implícito perde ≈ v0·dt/2 em relação à fórmula contínua.
    expected = profile.jump_height() - profile.jump_speed * STEP / 2
    assert abs(height - expected) < 1.5, (height, expected)
    assert abs(t_peak - profile.rise_time()) <= 2 * STEP
    assert abs(t_air - profile.air_time()) <= 3 * STEP


def test_calibrated_preserves_height_and_air_time_of_legacy() -> None:
    assert abs(CALIBRATED_PROFILE.jump_height() - LEGACY_PROFILE.jump_height()) < 1.0
    assert abs(CALIBRATED_PROFILE.air_time() - LEGACY_PROFILE.air_time()) < 0.01
    assert abs(CALIBRATED_PROFILE.horizontal_range() - LEGACY_PROFILE.horizontal_range()) < 3.0
    assert CALIBRATED_PROFILE.rise_time() > CALIBRATED_PROFILE.fall_time(), (
        "subida lenta, descida firme"
    )
    assert 2.2 < CALIBRATED_PROFILE.fall_gravity / CALIBRATED_PROFILE.gravity < 2.5


def test_minimum_jump_is_a_larger_fraction_than_legacy() -> None:
    legacy_min, _, _ = simulate_jump(LEGACY_PROFILE, hold=STEP)
    calibrated_min, _, _ = simulate_jump(CALIBRATED_PROFILE, hold=STEP)
    legacy_full, _, _ = simulate_jump(LEGACY_PROFILE, hold=2.0)
    calibrated_full, _, _ = simulate_jump(CALIBRATED_PROFILE, hold=2.0)
    assert 0.12 < legacy_min / legacy_full < 0.2
    assert 0.2 < calibrated_min / calibrated_full < 0.3
    assert abs(calibrated_min - CALIBRATED_PROFILE.min_jump_height()) < 8


def test_run_up_and_braking_distances() -> None:
    g = Game(
        [
            level(
                width=6000,
                platforms=[{"id": "floor", "kind": "ground", "x": 0, "y": 448, "w": 6000, "h": 92}],
            )
        ],
        CALIBRATED_PROFILE,
    )
    ticks(g, 60)
    start = g.player.x
    n = 0
    while g.player.vx < 340 and n < 400:
        ticks(g, 1, right=True, run=True)
        n += 1
    run_up = g.player.x - start
    expected = CALIBRATED_PROFILE.run_up_distance()
    assert abs(run_up - expected) < 6, (run_up, expected)
    assert 0.40 < n * STEP < 0.46
    # Frenagem ao soltar: 340² / (2·900) ≈ 64 px.
    start = g.player.x
    while g.player.vx > 0:
        ticks(g, 1)
    assert abs((g.player.x - start) - CALIBRATED_PROFILE.braking_distance()) < 4
    # Derrapagem (direção contrária): atrito dobrado → ≈ 32 px, e o estado é sinalizado.
    ticks(g, 120, right=True, run=True)
    start = g.player.x
    skid_seen = False
    while g.player.vx > 0:
        ticks(g, 1, left=True)
        skid_seen = skid_seen or g.player.skidding
    assert skid_seen
    assert abs((g.player.x - start) - CALIBRATED_PROFILE.braking_distance(skid=True)) < 4


def test_no_air_drag_run_release_grace_and_ceiling_bump() -> None:
    g = Game(
        [
            level(
                width=6000,
                platforms=[
                    {"id": "floor", "kind": "ground", "x": 0, "y": 448, "w": 6000, "h": 92},
                    {"id": "ceiling", "kind": "brick", "x": 1000, "y": 330, "w": 400, "h": 16},
                ],
            )
        ],
        CALIBRATED_PROFILE,
    )
    ticks(g, 120, right=True, run=True)
    assert g.player.vx == 340
    ticks(g, 1, jump=True, right=True, run=True)
    for _ in range(30):  # no ar, sem entrada, a velocidade é preservada (SMB1)
        ticks(g, 1, jump=True)
    assert g.player.vx == 340
    ticks(g, 200, right=True, run=True)
    assert g.player.grounded
    ticks(g, 10, right=True)  # soltou correr: graça de 0,17 s mantém 340
    assert g.player.vx == 340
    ticks(g, 60, right=True)
    assert g.player.vx < 340
    assert g.player.vx >= 220
    # Teto: ao bater a cabeça, recebe empurrão para baixo em vez de "grudar".
    g.player.x = 1100
    ticks(g, 2, right=False)
    bumped = False
    ticks(g, 1, jump=True)
    for _ in range(60):
        ticks(g, 1, jump=True)
        if g.player.hit_ceiling:
            bumped = True
            assert g.player.vy == CALIBRATED_PROFILE.ceiling_bump_speed
            break
    assert bumped


def test_hurt_without_knockback_and_longer_invulnerability() -> None:
    from game.characters.abilities import grant_power

    g = Game([level()], CALIBRATED_PROFILE)
    ticks(g, 5)
    grant_power(g, "grow")
    g.player.invulnerable = 0
    g.player.vx = 0
    g.hurt()
    assert g.player.vx == 0
    assert g.player.invulnerable == pytest.approx(2.6)


def test_profiles_registry_and_legacy_untouched() -> None:
    assert set(PROFILES) == {"legacy", "calibrated"}
    assert MovementProfile() == LEGACY_PROFILE
    assert math.isclose(LEGACY_PROFILE.jump_height(), 112.29, abs_tol=0.01)
