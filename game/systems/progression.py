"""Conquistas derivadas do progresso (port de ``src/core/progression.ts``)."""

from __future__ import annotations

from collections.abc import Sequence

from game.core.types import Level

ACHIEVEMENT_IDS: tuple[str, ...] = (
    "first-clear",
    "world-1",
    "world-2",
    "world-3",
    "world-4",
    "world-5",
    "all-clear",
    "relic-hunter",
    "secret-path",
)


def achievements_for(
    completed: Sequence[str], relics: Sequence[str], levels: Sequence[Level] | None = None
) -> list[str]:
    if levels is None:
        from game.levels.loader import load_levels

        levels = load_levels()
    result: list[str] = []
    if len(completed) > 0:
        result.append("first-clear")
    worlds = sorted({level.world for level in levels})
    for world in worlds:
        if all(level.id in completed for level in levels if level.world == world):
            result.append(f"world-{world}")
    if all(level.id in completed for level in levels):
        result.append("all-clear")
    if all(level.id in relics for level in levels):
        result.append("relic-hunter")
    return result
