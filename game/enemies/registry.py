"""Registro de tipos de inimigo: legados (passo monolítico) e arquétipos modernos."""

from __future__ import annotations

import game.bosses.boss  # registra o arquétipo 'guardian'
import game.bosses.guardians  # registra os cinco guardiões
import game.enemies.archetypes  # noqa: F401 - registra as famílias de arquétipos
from game.core.types import ENEMY_KINDS
from game.enemies.behaviors import ARCHETYPES

LEGACY_KINDS: tuple[str, ...] = ENEMY_KINDS


def known_enemy_kinds() -> tuple[str, ...]:
    return (*LEGACY_KINDS, *ARCHETYPES)


def is_modern(kind: str) -> bool:
    return kind in ARCHETYPES
