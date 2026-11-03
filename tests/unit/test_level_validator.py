"""Validador de fases: esquema, suporte, canos, patrulhas e saltos do caminho principal."""

from __future__ import annotations

import json
from dataclasses import replace

import pytest

from game.core.types import Vec
from game.levels.loader import level_from_dict, levels_dir, load_index, load_levels
from game.levels.validator import (
    Issue,
    errors,
    jump_gap_feasible,
    main_grounds,
    validate_level,
    validate_level_dict,
)
from game.physics.movement import CALIBRATED_PROFILE, LEGACY_PROFILE
from tests.unit.helpers import level

LEVELS = load_levels()


def test_schema_accepts_all_shipped_levels_and_rejects_broken_data() -> None:
    for entry in load_index()["levels"]:
        with open(levels_dir() / entry["file"], encoding="utf-8") as handle:
            assert validate_level_dict(json.load(handle)) == []
    broken = {
        "id": "",
        "name": "x",
        "world": 1,
        "stage": 1,
        "width": -5,
        "height": 540,
        "time": 300,
        "spawn": {"x": 1},
        "checkpoint": {"x": 1, "y": 2},
        "exit": {"x": 1, "y": 2},
        "platforms": [
            {"id": "a", "kind": "lava", "x": 0, "y": 0, "w": 0, "h": 10},
            {
                "id": "a",
                "kind": "ground",
                "x": 0,
                "y": 0,
                "w": 10,
                "h": 10,
                "motion": {"axis": "z"},
            },
        ],
        "enemies": [{"id": "e", "kind": "ghost", "x": 0, "y": 0, "w": 1, "h": 1, "patrol": [5, 1]}],
        "hazards": [{"kind": "acid", "x": 0, "y": 0, "w": 1, "h": 1}],
    }
    codes = {issue.code for issue in validate_level_dict(broken)}
    assert {
        "schema",
        "platform.kind",
        "platform.rect",
        "id.duplicate",
        "platform.motion",
        "enemy.kind",
        "enemy.patrol",
        "hazard.kind",
    } <= codes
    assert validate_level_dict([]) and validate_level_dict([])[0].code == "schema"


@pytest.mark.parametrize("lvl", LEVELS, ids=[lvl.id for lvl in LEVELS])
def test_shipped_levels_have_no_semantic_errors(lvl) -> None:
    issues = validate_level(lvl, check_jumps=False)
    assert errors(issues) == [], [str(i) for i in issues]


@pytest.mark.parametrize("lvl", LEVELS, ids=[lvl.id for lvl in LEVELS])
def test_main_path_gaps_are_jumpable_with_both_profiles(lvl) -> None:
    grounds = main_grounds(lvl)
    assert len(grounds) >= 3
    for profile in (LEGACY_PROFILE, CALIBRATED_PROFILE):
        issues = [i for i in validate_level(lvl, profile) if i.code == "gap.unreachable"]
        assert issues == [], [str(i) for i in issues]


def test_detects_unreachable_gap_missing_support_and_bad_pipe() -> None:
    wide = level(
        platforms=[
            {"id": "a", "kind": "ground", "x": 0, "y": 448, "w": 600, "h": 152},
            {"id": "b", "kind": "ground", "x": 1000, "y": 448, "w": 600, "h": 152},
        ],
        exit={"x": 1500, "y": 448},
        checkpoint={"x": 1200, "y": 414},
    )
    issues = validate_level(wide)
    assert any(i.code == "gap.unreachable" for i in issues)
    assert jump_gap_feasible(wide, wide.platforms[0], wide.platforms[1]) is None
    ok = level(
        platforms=[
            {"id": "a", "kind": "ground", "x": 0, "y": 448, "w": 600, "h": 152},
            {"id": "b", "kind": "ground", "x": 720, "y": 448, "w": 600, "h": 152},
        ],
        exit={"x": 1200, "y": 448},
        checkpoint={"x": 900, "y": 414},
    )
    assert jump_gap_feasible(ok, ok.platforms[0], ok.platforms[1]) is not None
    assert [i for i in validate_level(ok) if i.severity == "error"] == []
    floating = replace(ok, spawn=Vec(64, 100))
    assert any(i.code == "spawn.support" for i in validate_level(floating, check_jumps=False))
    bad_pipe = level(
        platforms=[
            {"id": "a", "kind": "ground", "x": 0, "y": 448, "w": 2400, "h": 152},
            {
                "id": "p",
                "kind": "pipe",
                "x": 300,
                "y": 400,
                "w": 56,
                "h": 48,
                "destination": {"x": 9000, "y": 100},
            },
        ]
    )
    codes = {i.code for i in validate_level(bad_pipe, check_jumps=False)}
    assert "pipe.destination" in codes
    assert str(Issue("error", "x", "msg", "ref")) == "error:x [ref] msg"
    assert (
        level_from_dict(
            {
                "id": "t",
                "name": "t",
                "world": 1,
                "stage": 1,
                "width": 100,
                "height": 540,
                "time": 10,
                "spawn": {"x": 0, "y": 0},
                "checkpoint": {"x": 0, "y": 0},
                "exit": {"x": 0, "y": 0},
            }
        ).platforms
        == []
    )
