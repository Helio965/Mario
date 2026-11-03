"""Save format 2 and lossless migration from the browser save (format 1)."""

import json

from lume.core.progression import achievements_for
from lume.levels.campaign import load_campaign
from lume.systems.save import (
    CampaignView, SaveData, complete_level, fresh_save, import_legacy_file, load_save, migrate_v1,
    reset_save, sanitize, write_save,
)

CAMPAIGN = load_campaign()
VIEW = CampaignView.from_campaign(CAMPAIGN)


def legacy(**changes):
    data = {"version": 1, "unlocked": 0, "completed": [], "records": {}, "relics": [], "achievements": [],
            "settings": {"music": 0.2, "sfx": 0.9, "effects": False, "touch": True}}
    data.update(changes)
    return data


def test_fresh_save_unlocks_first_level_only():
    s = fresh_save(VIEW)
    assert s.unlocked == ["first_steps"] and s.completed == []


def test_v1_migration_keeps_progress_records_relics_and_settings():
    old = legacy(unlocked=4, completed=["1-1", "1-2", "1-3", "2-1"], records={"1-1": 4200, "2-1": 900},
                 relics=["1-1", "2-1"], achievements=["first-clear", "world-1", "secret-path"])
    new = migrate_v1(old, VIEW)
    assert new.completed == ["first_steps", "valley_canals", "orchard_guardian", "windswept_dunes"]
    assert new.records == {"first_steps": 4200, "windswept_dunes": 900}
    assert new.legacy_relic_marks == ["first_steps", "windswept_dunes"]
    assert new.legacy_achievements == ["first-clear", "world-1", "secret-path"]
    # Everything playable before remains playable, plus the levels that follow
    # completed ones in the new order.
    for level_id in ["first_steps", "valley_canals", "orchard_guardian", "windswept_dunes", "canyon_bridges"]:
        assert level_id in new.unlocked
    assert "windmill_heights" in new.unlocked  # new level after orchard_guardian
    assert new.settings.music == 0.2 and new.settings.effects is False and new.settings.touch is True
    assert new.migrated_from == "lume-save-v1"


def test_v1_unlocked_index_without_completion_is_respected():
    new = migrate_v1(legacy(unlocked=7), VIEW)
    assert "blue_ascent" in new.unlocked  # legacy index 7 = "3-2"


def test_corrupt_and_unknown_files_are_backed_up(tmp_path):
    (tmp_path / "save.json").write_text("{not json", encoding="utf-8")
    data, notices = load_save(VIEW, tmp_path)
    assert data.unlocked == ["first_steps"] and notices
    assert list(tmp_path.glob("save.corrupt-*.json"))
    (tmp_path / "save.json").write_text(json.dumps({"version": 99}), encoding="utf-8")
    data, notices = load_save(VIEW, tmp_path)
    assert notices and len(list(tmp_path.glob("save.corrupt-*.json"))) == 2


def test_round_trip_and_atomic_write(tmp_path):
    s = fresh_save(VIEW)
    complete_level(s, VIEW, "first_steps", 1234, relics=["relic_room"], secrets=["pipe_room"])
    assert write_save(s, VIEW, tmp_path)
    loaded, _ = load_save(VIEW, tmp_path)
    assert loaded.completed == ["first_steps"]
    assert loaded.records["first_steps"] == 1234
    assert loaded.relics == {"first_steps": ["relic_room"]}
    assert loaded.secrets == {"first_steps": ["pipe_room"]}
    assert "valley_canals" in loaded.unlocked
    assert not list(tmp_path.glob("*.tmp"))


def test_import_browser_export_file(tmp_path):
    exported = tmp_path / "lume-save-v1.json"
    exported.write_text(json.dumps({"lume-save-v1": json.dumps(legacy(completed=["1-1"], unlocked=1))}), encoding="utf-8")
    data, notices = import_legacy_file(exported, VIEW)
    assert data.completed == ["first_steps"] and data.migrated_from
    data2, _ = load_save(VIEW, tmp_path)  # auto-import when no save.json exists
    assert data2.completed == ["first_steps"]


def test_sanitize_rejects_malicious_or_invalid_values():
    raw = {"version": 2, "unlocked": ["__proto__", "first_steps", 3], "completed": ["x" * 500], "records": {"a": float("nan"), "b": -5},
           "relics": {"first_steps": ["r", None]}, "settings": {"music": 7, "quality": "ultra"}}
    s = sanitize(raw, VIEW)
    assert "__proto__" not in s.unlocked and s.completed == []
    assert s.records == {"b": 0}
    assert s.relics == {"first_steps": ["r"]}
    assert s.settings.music == 1 and s.settings.quality == "auto"


def test_reset_keeps_backup(tmp_path):
    s = fresh_save(VIEW)
    write_save(s, VIEW, tmp_path)
    reset_save(VIEW, tmp_path)
    assert list(tmp_path.glob("save.reset-*.json"))


def test_achievements_are_derived():
    s = SaveData()
    assert achievements_for(s, CAMPAIGN) == []
    complete_level(s, VIEW, "first_steps", 1, secrets=["pipe_room"])
    assert achievements_for(s, CAMPAIGN) == ["first-clear", "secret-path"]
    m = migrate_v1(legacy(completed=["1-1"], unlocked=1), VIEW)
    assert "legacy-traveler" in achievements_for(m, CAMPAIGN)
