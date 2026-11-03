"""Travessia das quinze fases por entradas normais (port de ``campaign-routes.test.ts``).

Além das garantias originais, confere que o condutor Python gera exatamente a
mesma sequência de entradas gravada com o condutor TypeScript.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

import pytest

from game.levels.loader import level_to_dict, load_levels
from tests.gameplay.route_player import play_campaign_route
from tests.unit.golden import expand_inputs

GOLDEN = Path(__file__).resolve().parent.parent / "fixtures" / "golden"
LEVELS = load_levels()

DEATH_BUDGET = {"4-2": 2, "5-3": 1}


@pytest.mark.gameplay
@pytest.mark.parametrize("level", LEVELS, ids=[level.id for level in LEVELS])
def test_route_reaches_exit_with_enemies_and_hazards_active(level) -> None:
    original_map = json.dumps(level_to_dict(level), sort_keys=True)
    # Walking on the mountain's slippery terraces leaves braking distance.
    route = play_campaign_route(level, 100, run=level.id != "3-2", record_inputs=True)
    details = json.dumps(
        {
            "status": route.game.status,
            "lives": route.game.lives,
            "deaths": route.deaths,
            "powers": route.powers,
            "bossHits": route.boss_hits,
            "incidents": route.incidents,
            "tail": [asdict(s) for s in route.samples[-16:]],
        },
        ensure_ascii=False,
        indent=2,
    )
    assert route.game.status == "complete", details
    assert route.game.checkpoint_reached, details
    assert [e for e in route.game.enemies if e.kind == "boss" and e.alive] == [], details
    assert route.game.lives > 0, details
    assert route.game.coins_total > 0, details
    assert route.powers > 0, details
    # These two harder routes exercise ordinary checkpoint respawns. Every
    # other route currently finishes without spending a life.
    assert route.deaths <= DEATH_BUDGET.get(level.id, 0), details
    assert json.dumps(level_to_dict(level), sort_keys=True) == original_map, (
        "o condutor preserva todos os dados do mapa"
    )
    with open(GOLDEN / f"route-{level.id}.json", encoding="utf-8") as handle:
        fixture = json.load(handle)
    expected = expand_inputs(fixture["inputs"])
    assert route.ticks == fixture["ticks"], details
    first = next(
        (i for i, (a, b) in enumerate(zip(route.inputs, expected, strict=True)) if a != b), None
    )
    assert first is None, f"entrada diverge do condutor TypeScript no tick {first}"
