"""Regra de ouro do elenco: nenhuma fase obrigatória fica impossível para personagem algum."""

from __future__ import annotations

import pytest

from game.characters.roster import load_roster
from game.levels.loader import load_levels
from game.levels.validator import validate_level
from game.physics.movement import LEGACY_PROFILE

ROSTER = load_roster()
LEVELS = load_levels()


@pytest.mark.parametrize("character_id", sorted(ROSTER))
def test_every_main_path_gap_is_jumpable_by_each_character(character_id: str) -> None:
    profile = ROSTER[character_id].profile(LEGACY_PROFILE)
    for level in LEVELS:
        issues = [str(i) for i in validate_level(level, profile) if i.code == "gap.unreachable"]
        assert issues == [], f"{character_id} em {level.id}: {issues}"


def test_minimum_jump_character_still_clears_tallest_mandatory_step() -> None:
    fagulha = ROSTER["fagulha"].profile(LEGACY_PROFILE)
    # Maior desnível entre chãos consecutivos do caminho principal nas 15 fases: 48 px (docs/FASES.md).
    assert fagulha.jump_height() > 48 + 20
