"""Port de ``save.test.ts`` + comportamento novo do arquivo versionado (v2 com migração v1)."""

from __future__ import annotations

import json
from pathlib import Path

from game.systems.save import (
    SAVE_KEY,
    FileStorage,
    MemoryStorage,
    Settings,
    complete_level,
    import_browser_export,
    load_save,
    reset_save,
    write_save,
)


class Denied(MemoryStorage):
    def read(self) -> str | None:
        raise OSError("Denied")

    def write(self, text: str) -> None:
        raise OSError("Quota")

    def remove(self) -> None:
        raise OSError("Denied")


def reading(value: object) -> MemoryStorage:
    return MemoryStorage(json.dumps(value))


def test_fresh_independent_defaults_for_unavailable_malformed_or_incompatible_saves() -> None:
    initial = load_save(Denied())
    assert initial.unlocked == 0
    assert initial.version == 2
    assert load_save(MemoryStorage("{broken")) == initial
    assert load_save(reading({"version": 3, "unlocked": 14})) == initial
    migrated = load_save(reading({"version": 1, "unlocked": 14}))
    assert migrated.unlocked == 14
    assert migrated.version == 2
    initial.completed.append("mutated")
    initial.settings.music = 0
    another = load_save(MemoryStorage(None))
    assert another.completed == []
    assert another.settings.music > 0


def test_sanitizes_every_persisted_field_without_unsafe_property_names() -> None:
    data = load_save(
        reading(
            {
                "version": 1,
                "unlocked": 99.5,
                "completed": ["1-1", None, "1-1", "", " line ", "__proto__"],
                "records": {"1-1": 9.8, "1-2": -2, "bad": "999", "__proto__": 8},
                "relics": ["1-1", 33, "1-1"],
                "achievements": ["first-clear", "first-clear", False],
                "settings": {
                    "music": 5,
                    "sfx": -2,
                    "effects": "false",
                    "touch": True,
                    "fps_limit": 999,
                    "language": "xx",
                    "bindings": {"jump": ["k", "", "k"], "nope": ["x"]},
                },
            }
        )
    )
    assert data.unlocked == 14
    assert data.completed == ["1-1"]
    assert data.records == {"1-1": 9, "1-2": 0}
    assert data.relics == ["1-1"]
    assert data.achievements == ["first-clear"]
    expected = Settings(music=1, sfx=0, effects=True, touch=True)
    expected.bindings["jump"] = ["k"]
    assert data.settings == expected
    assert data.settings.fps_limit == 60
    assert data.settings.language == "pt-BR"


def test_unlocks_at_most_last_stage_retains_best_score_and_leaves_input_unchanged() -> None:
    original = load_save(MemoryStorage(None))
    first = complete_level(original, 0, 950, True, "1-1")
    assert first.unlocked == 1
    assert first.completed == ["1-1"]
    assert first.relics == ["1-1"]
    assert original.completed == []
    assert original.records == {}
    assert first.settings is not original.settings
    replay = complete_level(first, 0, 10, True, "1-1")
    assert replay.records["1-1"] == 950
    assert len(replay.completed) == 1
    assert len(replay.relics) == 1
    assert complete_level(replay, 14, 100, False, "5-3").unlocked == 14
    assert complete_level(replay, -1, 100, False, "bad") == replay
    assert complete_level(replay, 2.5, 100, False, "2-1") == replay


def test_handles_storage_denial_and_clears_only_game_data_on_reset() -> None:
    data = load_save(MemoryStorage(None))
    assert write_save(data, Denied()) is False
    memory = MemoryStorage(None)
    assert write_save(data, memory) is True
    assert json.loads(memory.text or "") == data.to_dict()
    assert reset_save(memory) == data
    assert memory.text is None
    assert reset_save(Denied()) == data


def test_file_storage_is_atomic_and_recovers_from_corruption(tmp_path: Path) -> None:
    storage = FileStorage(tmp_path / "nested" / "save.json")
    data = complete_level(load_save(storage), 0, 1200, True, "1-1")
    assert write_save(data, storage)
    assert load_save(storage) == data
    assert not (tmp_path / "nested" / "save.json.tmp").exists()
    (tmp_path / "nested" / "save.json").write_text('{"version": 2, "unlocked": ', encoding="utf-8")
    assert load_save(storage).unlocked == 0
    (tmp_path / "nested" / "save.json.tmp").write_text("garbage", encoding="utf-8")
    assert write_save(data, storage)
    assert load_save(storage) == data
    reset_save(storage)
    assert not (tmp_path / "nested" / "save.json").exists()


def test_import_browser_export_accepts_v1_payloads() -> None:
    payload = {
        "version": 1,
        "unlocked": 3,
        "completed": ["1-1", "1-2", "1-3"],
        "records": {"1-1": 500},
        "relics": ["1-1"],
        "achievements": ["first-clear"],
        "settings": {"music": 0.2, "sfx": 0.9, "effects": False, "touch": True},
    }
    imported = import_browser_export(json.dumps(payload))
    assert imported is not None
    assert imported.unlocked == 3
    assert imported.records == {"1-1": 500}
    assert imported.settings.music == 0.2
    assert imported.settings.effects is False
    wrapped = import_browser_export(json.dumps({SAVE_KEY: json.dumps(payload)}))
    assert wrapped == imported
    assert import_browser_export("not json") is None
    assert import_browser_export(json.dumps({"version": 7})) is None
