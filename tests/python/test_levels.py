"""Structural tests: every implemented level parses, validates and keeps the
invariants of the legacy suite (safe spawn/checkpoints, returnable secrets,
exit on ground, relics)."""

import json

import pytest

from lume.core.species import load_profiles
from lume.levels.campaign import load_campaign
from lume.levels.errors import DataError
from lume.levels.schema import parse_level
from lume.levels.validate import errors, main_path_gaps, simulate_gap, validate_campaign, validate_level

CAMPAIGN = load_campaign()
PROFILES = load_profiles()
BIOMES = {w.id: w.biome for w in CAMPAIGN.worlds}


def test_campaign_has_ten_worlds_and_sixty_unique_level_ids():
    assert len(CAMPAIGN.worlds) == 10
    assert len(CAMPAIGN.entries) == 60
    assert len({e.id for e in CAMPAIGN.entries}) == 60
    for world in CAMPAIGN.worlds:
        assert len(world.entries) == 6


def test_legacy_levels_are_preserved_with_their_ids():
    legacy = {old: lvl.id for lvl in CAMPAIGN.levels for old in lvl.legacy_ids}
    assert sorted(legacy) == sorted(f"{w}-{s}" for w in range(1, 6) for s in range(1, 4))


def test_campaign_validation_has_no_errors():
    problems = errors(validate_campaign(CAMPAIGN, PROFILES))
    assert not problems, "\n".join(map(str, problems))


@pytest.mark.parametrize("lvl", CAMPAIGN.levels, ids=lambda lvl: lvl.id)
def test_level_structure(lvl):
    problems = errors(validate_level(lvl, PROFILES, world_biome=BIOMES[lvl.world]))
    assert not problems, "\n".join(map(str, problems))
    assert lvl.collectibles, "relíquias"
    warps = [p for p in lvl.platforms if p.warp]
    assert len(warps) >= 2, "segredo com ida e volta"
    assert any(p.x <= lvl.exit.x <= p.x + p.w and p.y == lvl.exit.y for p in lvl.platforms)


def test_gap_simulation_detects_impossible_jump():
    from tests.python.conftest import level

    lvl = level(platforms=[{"id": "a", "kind": "ground", "x": 0, "y": 448, "w": 800, "h": 92},
                           {"id": "b", "kind": "ground", "x": 1300, "y": 448, "w": 800, "h": 92}],
                exit={"id": "goal", "kind": "flag", "x": 2000, "y": 448})
    gaps = main_path_gaps(lvl)
    assert len(gaps) == 1 and gaps[0].width == 500
    assert simulate_gap(lvl, gaps[0]) == {"pequeno": False, "grande": False}
    assert any("não pode ser atravessado" in p.message for p in validate_level(lvl, PROFILES))


def test_parser_reports_paths_for_bad_data():
    bad = {"format": "lume.level", "format_version": 1, "id": "Bad Id", "platforms": [{"id": "x", "kind": "lava"}]}
    with pytest.raises(DataError) as exc:
        parse_level(bad)
    text = str(exc.value)
    assert "$.id" in text and "platforms[0].kind" in text and "$.bounds" in text


def test_species_outside_biome_is_rejected():
    from tests.python.conftest import level

    lvl = level(enemies=[{"id": "e", "species": "pinguim_patrulha", "x": 600, "y": 448, "patrol": [500, 900]}])
    problems = validate_level(lvl, PROFILES, world_biome="grassland", simulate=False)
    assert any("não habita" in p.message for p in problems)


def test_level_files_are_canonical_json():
    for entry in CAMPAIGN.entries:
        if entry.implemented:
            text = entry.path.read_text(encoding="utf-8")
            assert json.loads(text)["id"] == entry.id
            assert text.endswith("\n")


def test_overlapping_blocks_are_rejected():
    """A brick resting inside a reward block made a planned secret unreachable."""
    from tests.python.conftest import level

    lvl = level(platforms=[
        {"id": "floor", "kind": "ground", "x": 0, "y": 448, "w": 1600, "h": 92},
        {"id": "q", "kind": "question", "x": 400, "y": 350, "w": 40, "h": 28, "reward": "grow"},
        {"id": "b", "kind": "brick", "x": 420, "y": 330, "w": 40, "h": 22},
    ])
    problems = errors(validate_level(lvl, PROFILES, simulate=False))
    assert any("sobrepõe" in p.message for p in problems)


def test_terraces_count_as_ground_when_measuring_gaps():
    """Narrow steps that touch each other form one run (no false 'pit')."""
    from tests.python.conftest import level

    steps = [{"id": f"s{k}", "kind": "ground", "x": 400 + k * 64, "y": 384 + k * 16, "w": 64, "h": 200} for k in range(5)]
    lvl = level(platforms=[{"id": "a", "kind": "ground", "x": 0, "y": 368, "w": 400, "h": 232}, *steps,
                           {"id": "b", "kind": "ground", "x": 720, "y": 448, "w": 900, "h": 152}])
    assert main_path_gaps(lvl) == []


def test_unreachable_relic_is_reported():
    from tests.python.conftest import level

    lvl = level(collectibles=[{"id": "relic_sky", "kind": "relic", "x": 700, "y": 100}])
    problems = validate_level(lvl, PROFILES, simulate=False)
    assert any("inalcançável" in p.message for p in problems)
    near = level(collectibles=[{"id": "relic_low", "kind": "relic", "x": 700, "y": 330}])
    assert not any("inalcançável" in p.message for p in validate_level(near, PROFILES, simulate=False))
