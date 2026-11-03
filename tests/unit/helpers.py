"""Utilidades compartilhadas pelos testes de lógica."""

from __future__ import annotations

from typing import Any

from game.core.game import Game
from game.core.types import InputState, Level
from game.levels.loader import level_from_dict

STEP = 1 / 120


def level(**overrides: Any) -> Level:
    base: dict[str, Any] = {
        "id": "test",
        "name": "arena",
        "world": 1,
        "stage": 1,
        "width": 2400,
        "height": 540,
        "time": 300,
        "spawn": {"x": 64, "y": 414},
        "checkpoint": {"x": 1100, "y": 414},
        "exit": {"x": 2280, "y": 448},
        "platforms": [{"id": "floor", "kind": "ground", "x": 0, "y": 448, "w": 2400, "h": 92}],
        "coins": [],
        "enemies": [],
        "items": [],
        "hazards": [],
        "hints": [],
    }
    base.update(overrides)
    return level_from_dict(base)


def ticks(game: Game, count: int, **input_fields: bool) -> None:
    state = InputState(**input_fields)
    for _ in range(count):
        game.update(STEP, state)


def run_seconds(game: Game, seconds: float, **input_fields: bool) -> None:
    ticks(game, round(seconds * 120), **input_fields)


def events_of(game: Game, kind: str) -> list[Any]:
    return [event for event in game.events if event.type == kind]
