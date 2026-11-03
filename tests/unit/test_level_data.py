"""Os dados das 15 fases em JSON preservam exatamente o conteúdo do TypeScript."""

from __future__ import annotations

import json

from game.levels.loader import THEMES, level_to_dict, levels_dir, load_index, load_levels


def test_index_matches_reference_commit() -> None:
    index = load_index()
    assert index["format"] == "lume-level/1"
    assert index["reference_commit"] == "b40c39ca77026de4101817b8a8f7198f6e870ab9"
    assert [entry["id"] for entry in index["levels"]] == [
        f"{world}-{stage}" for world in range(1, 6) for stage in range(1, 4)
    ]


def test_totals_match_original_export() -> None:
    levels = load_levels()
    assert len(levels) == 15
    assert len(THEMES) == 5
    assert sum(len(level.platforms) for level in levels) == 238
    assert sum(len(level.coins) for level in levels) == 572
    assert sum(1 for level in levels for coin in level.coins if coin.special) == 29
    assert sum(len(level.enemies) for level in levels) == 49
    assert sum(1 for level in levels for enemy in level.enemies if enemy.kind == "boss") == 5
    assert sum(len(level.items) for level in levels) == 21
    assert sum(len(level.hazards) for level in levels) == 40
    assert sum(len(level.hints) for level in levels) == 46


def test_ids_unique_and_round_trip() -> None:
    for entry in load_index()["levels"]:
        with open(levels_dir() / entry["file"], encoding="utf-8") as handle:
            raw = json.load(handle)
        from game.levels.loader import level_from_dict

        level = level_from_dict(raw)
        ids = (
            [p.id for p in level.platforms]
            + [c.id for c in level.coins]
            + [e.id for e in level.enemies]
            + [i.id for i in level.items]
        )
        assert len(ids) == len(set(ids)), f"{level.id}: ids duplicados"
        again = level_to_dict(level)
        for key in (
            "id",
            "world",
            "stage",
            "name",
            "width",
            "height",
            "time",
            "spawn",
            "checkpoint",
            "exit",
        ):
            assert again[key] == raw[key], f"{level.id}: campo {key} diverge"
        for key in ("platforms", "coins", "enemies", "items", "hazards", "hints"):
            assert again[key] == raw[key], f"{level.id}: lista {key} diverge após ida e volta"
