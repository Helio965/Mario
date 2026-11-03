"""Custo da simulação pura (sem renderização) em cenários carregados.

Os números são impressos com ``-s`` e registrados em docs/DESEMPENHO.md; as
asserções só garantem que o passo fixo cabe folgadamente em 1/120 s nesta
máquina de CI (limite generoso para não gerar falsos negativos).
"""

from __future__ import annotations

import time

import pytest

from game.core.game import Game
from game.core.types import InputState
from game.levels.loader import level_from_dict, load_levels
from game.physics.movement import FIXED_DT


def crowded_level(enemies: int, platforms: int) -> object:
    width = 400 + enemies * 60
    data = {
        "id": "perf",
        "name": "perf",
        "world": 5,
        "stage": 1,
        "width": width,
        "height": 540,
        "time": 900,
        "spawn": {"x": 72, "y": 414},
        "checkpoint": {"x": width // 2, "y": 414},
        "exit": {"x": width - 150, "y": 448},
        "platforms": [{"id": "floor", "kind": "ground", "x": 0, "y": 448, "w": width, "h": 152}]
        + [
            {
                "id": f"b{i}",
                "kind": "brick" if i % 3 else "question",
                "x": 200 + i * 90,
                "y": 300 - (i % 4) * 40,
                "w": 40,
                "h": 24,
                "reward": "coin",
            }
            for i in range(platforms)
        ]
        + [
            {
                "id": f"m{i}",
                "kind": "moving",
                "x": 300 + i * 500,
                "y": 360,
                "w": 90,
                "h": 18,
                "motion": {"axis": "y", "range": 30, "speed": 1.5},
            }
            for i in range(max(1, platforms // 10))
        ],
        "coins": [
            {"id": f"c{i}", "x": 150 + i * 45, "y": 400, "w": 16, "h": 20} for i in range(enemies)
        ],
        "enemies": [
            {
                "id": f"e{i}",
                "kind": ("walker", "shell", "flyer", "shooter", "armored")[i % 5],
                "x": 300 + i * 60,
                "y": 420 - (24 if i % 5 == 2 else 0),
                "w": 28,
                "h": 28,
                "patrol": [250 + i * 60, 420 + i * 60],
            }
            for i in range(enemies)
        ],
        "items": [],
        "hazards": [
            {
                "kind": "moving",
                "x": 500 + i * 700,
                "y": 320,
                "w": 26,
                "h": 26,
                "range": 40,
                "speed": 1.5,
            }
            for i in range(max(1, enemies // 20))
        ],
        "hints": [],
    }
    return level_from_dict(data)


def measure(game: Game, steps: int, state: InputState) -> float:
    start = time.perf_counter()
    for _ in range(steps):
        game.update(FIXED_DT, state)
    return (time.perf_counter() - start) / steps


@pytest.mark.performance
@pytest.mark.parametrize(("enemies", "platforms"), [(10, 20), (50, 60), (200, 120)])
def test_fixed_step_cost_with_many_entities(enemies: int, platforms: int) -> None:
    game = Game([crowded_level(enemies, platforms)])  # type: ignore[list-item]
    state = InputState(right=True, run=True, jump=True, ability=True)
    measure(game, 60, state)  # aquecimento
    per_step = measure(game, 600, state)
    budget = FIXED_DT
    print(
        f"\n[perf] inimigos={enemies} plataformas={platforms}: {per_step * 1e6:.0f} µs/passo ({per_step / budget * 100:.1f}% do passo de 1/120 s), vivos={sum(e.alive for e in game.enemies)}"
    )
    assert per_step < budget * 0.9, "um passo de física não cabe no passo fixo"


@pytest.mark.performance
def test_campaign_level_steps_per_second() -> None:
    game = Game([load_levels()[14]])
    state = InputState(right=True, run=True)
    per_step = measure(game, 1200, state)
    print(
        f"\n[perf] fase 5-3: {per_step * 1e6:.0f} µs/passo → {1 / per_step:,.0f} passos/s ({1 / per_step / 120:.0f}× tempo real)"
    )
    assert 1 / per_step > 2000
