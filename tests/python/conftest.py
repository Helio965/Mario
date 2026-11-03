"""Shared fixtures for the Python test-suite."""

from __future__ import annotations

import copy
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

from lume.core.constants import FIXED_DT  # noqa: E402
from lume.core.game import Game  # noqa: E402
from lume.core.input import InputState  # noqa: E402
from lume.levels.schema import parse_level  # noqa: E402

BASE_LEVEL = {
    "format": "lume.level",
    "format_version": 1,
    "id": "test_arena",
    "name": "Arena de teste",
    "world": "green_kingdom",
    "role": "presentation",
    "difficulty": 1,
    "art": {"set": "green_kingdom", "variant": "meadow"},
    "music": "green_kingdom_main",
    "bounds": {"width": 2400, "height": 540},
    "time_limit": 300,
    "spawn": {"x": 64, "y": 418},
    "checkpoints": [{"id": "cp", "x": 1100, "y": 414}],
    "exit": {"id": "goal", "kind": "flag", "x": 2280, "y": 448},
    "platforms": [{"id": "floor", "kind": "ground", "x": 0, "y": 448, "w": 2400, "h": 92}],
    "collectibles": [{"id": "relic", "kind": "relic", "x": 2000, "y": 300}],
}


def level(**changes):
    data = copy.deepcopy(BASE_LEVEL)
    extra_platforms = changes.pop("extra_platforms", None)
    data.update(changes)
    if extra_platforms:
        data["platforms"] = data["platforms"] + extra_platforms
    return parse_level(data)


def game(**changes) -> Game:
    return Game([level(**changes)])


def ticks(g: Game, count: int, **inputs) -> None:
    inp = InputState(**inputs)
    for _ in range(count):
        g.update(FIXED_DT, inp)


def run(g: Game, seconds: float, **inputs) -> None:
    ticks(g, int(round(seconds * 120)), **inputs)


@pytest.fixture
def make_game():
    return game
