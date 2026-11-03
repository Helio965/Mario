"""Elenco: envelopes de equilíbrio e perfis derivados sem alterar o base."""

from __future__ import annotations

from game.characters.roster import CharacterDelta, get_character, load_roster, minimum_profiles
from game.physics.movement import CALIBRATED_PROFILE, LEGACY_PROFILE


def test_roster_loads_five_characters_within_envelopes() -> None:
    roster = load_roster()
    assert set(roster) == {"lume", "vento", "fagulha", "aurora", "pirilampo"}
    for character in roster.values():
        assert character.delta.within_envelope() == [], character.id
        assert character.name("pt-BR")
    assert get_character("inexistente").id == "lume"
    assert get_character("pirilampo").delta.damage_model == "invincible"
    assert get_character("pirilampo").delta.time_bonus == 100.0


def test_profiles_scale_but_base_stays_untouched() -> None:
    base = CALIBRATED_PROFILE
    vento = get_character("vento").profile(base)
    assert vento.jump_speed == base.jump_speed * 1.10
    assert 1.2 < vento.jump_height() / base.jump_height() < 1.22
    assert vento.ground_friction == base.ground_friction * 0.6
    assert CALIBRATED_PROFILE.jump_speed == 487.0, "o perfil base não é alterado"
    fagulha = get_character("fagulha").profile(LEGACY_PROFILE)
    assert fagulha.run_speed > LEGACY_PROFILE.run_speed
    assert fagulha.jump_height() < LEGACY_PROFILE.jump_height()
    assert LEGACY_PROFILE.run_speed == 340.0


def test_envelope_violations_are_reported() -> None:
    bad = CharacterDelta(
        jump_speed_mul=1.3,
        run_speed_mul=1.5,
        ground_friction_mul=0.2,
        abilities=("teleport",),
        damage_model="god",
    )
    problems = bad.within_envelope()
    assert len(problems) == 5


def test_minimum_profiles_pick_lowest_jump_and_slowest_run() -> None:
    minimum = minimum_profiles(LEGACY_PROFILE)
    assert minimum["menor_salto"].jump_speed < LEGACY_PROFILE.jump_speed
    assert minimum["menor_corrida"].run_speed < LEGACY_PROFILE.run_speed
