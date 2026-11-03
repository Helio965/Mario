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


def is_boss_kind(kind: str) -> bool:
    """Guardião: tipo legado ``boss`` ou arquétipo marcado ``is_boss`` (os cinco guardiões)."""
    return kind == "boss" or bool(getattr(ARCHETYPES.get(kind), "is_boss", False))


def floats(kind: str) -> bool:
    """Inimigo sem gravidade (voador legado, chefe flutuante, clone): dispensa chão abaixo."""
    if kind == "flyer":
        return True
    cls = ARCHETYPES.get(kind)
    definition = getattr(cls, "definition", None)
    if definition is not None:
        return bool(definition.floats)
    return cls is not None and not bool(getattr(cls, "uses_gravity", True))
