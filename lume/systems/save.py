"""Versioned save data (format 2) with lossless migration from the web save.

* Format 1 is the browser ``localStorage`` value ``lume-save-v1`` of the
  TypeScript edition: linear ``unlocked`` index (0–14), level ids "1-1"…"5-3",
  one relic mark per level. It is imported through :func:`migrate_v1`.
* Format 2 identifies levels by stable ids, keeps the set of unlocked levels,
  the collectible/secret ids found per level and everything from format 1
  that cannot be mapped exactly (``legacy_*`` fields), so no progress is lost.

Unreadable or unknown files are copied to ``save.corrupt-*.json`` before a
fresh save is used, and writes are atomic (temporary file + replace).
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable, Optional

SAVE_VERSION = 2
SAVE_FILE = "save.json"
LEGACY_KEY = "lume-save-v1"
LEGACY_ORDER = ["1-1", "1-2", "1-3", "2-1", "2-2", "2-3", "3-1", "3-2", "3-3", "4-1", "4-2", "4-3", "5-1", "5-2", "5-3"]
QUALITY = ("auto", "high", "medium", "low")
RESOLUTIONS = ("auto", "1280x720", "1600x900", "1920x1080", "2560x1440", "3840x2160")
_ID = re.compile(r"^[^\x00-\x1f\x7f]{1,128}$")
_FORBIDDEN = {"__proto__", "constructor", "prototype"}


@dataclass
class Settings:
    music: float = 0.45
    sfx: float = 0.75
    effects: bool = True
    touch: bool = False
    quality: str = "auto"
    resolution: str = "auto"
    fullscreen: bool = False
    vsync: bool = True
    show_fps: bool = False


@dataclass
class SaveData:
    version: int = SAVE_VERSION
    unlocked: list[str] = field(default_factory=list)
    completed: list[str] = field(default_factory=list)
    records: dict[str, int] = field(default_factory=dict)
    relics: dict[str, list[str]] = field(default_factory=dict)
    secrets: dict[str, list[str]] = field(default_factory=dict)
    achievements: list[str] = field(default_factory=list)
    legacy_relic_marks: list[str] = field(default_factory=list)
    legacy_achievements: list[str] = field(default_factory=list)
    migrated_from: str = ""
    settings: Settings = field(default_factory=Settings)

    def to_json(self) -> dict[str, Any]:
        return asdict(self)


# --------------------------------------------------------------------------- helpers
def _valid_id(value: Any) -> bool:
    return isinstance(value, str) and bool(_ID.match(value)) and value.strip() == value and value not in _FORBIDDEN


def _ids(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    out: list[str] = []
    for v in value:
        if _valid_id(v) and v not in out:
            out.append(v)
    return out


def _number(value: Any, fallback: float, maximum: float, integer: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value != value or value in (float("inf"), float("-inf")):
        return fallback
    result = min(maximum, max(0.0, float(value)))
    return float(int(result)) if integer else result


def _settings(raw: Any) -> Settings:
    s = raw if isinstance(raw, dict) else {}
    d = Settings()
    return Settings(
        music=_number(s.get("music"), d.music, 1),
        sfx=_number(s.get("sfx"), d.sfx, 1),
        effects=s["effects"] if isinstance(s.get("effects"), bool) else d.effects,
        touch=s["touch"] if isinstance(s.get("touch"), bool) else d.touch,
        quality=s["quality"] if s.get("quality") in QUALITY else d.quality,
        resolution=s["resolution"] if s.get("resolution") in RESOLUTIONS else d.resolution,
        fullscreen=s["fullscreen"] if isinstance(s.get("fullscreen"), bool) else d.fullscreen,
        vsync=s["vsync"] if isinstance(s.get("vsync"), bool) else d.vsync,
        show_fps=s["show_fps"] if isinstance(s.get("show_fps"), bool) else d.show_fps,
    )


def _records(raw: Any) -> dict[str, int]:
    out: dict[str, int] = {}
    if isinstance(raw, dict):
        for key, score in raw.items():
            if _valid_id(key) and isinstance(score, (int, float)) and not isinstance(score, bool) and score == score:
                out[key] = int(_number(score, 0, 2**53 - 1, True))
    return out


def _id_map(raw: Any) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    if isinstance(raw, dict):
        for key, values in raw.items():
            if _valid_id(key):
                ids = _ids(values)
                if ids:
                    out[key] = ids
    return out


# --------------------------------------------------------------------------- campaign glue
class CampaignView:
    """Minimal campaign information needed by the save system."""

    def __init__(self, order: list[str], legacy: dict[str, str], playable: Optional[set[str]] = None):
        self.order = order  # every level id, campaign order
        self.legacy = legacy  # "1-1" -> "first_steps"
        self.playable = playable if playable is not None else set(order)

    @classmethod
    def from_campaign(cls, campaign) -> "CampaignView":
        legacy: dict[str, str] = {}
        for level in campaign.levels:
            for old in level.legacy_ids:
                legacy[old] = level.id
        return cls([e.id for e in campaign.entries], legacy, {lvl.id for lvl in campaign.levels})

    def first(self) -> str:
        for level_id in self.order:
            if level_id in self.playable:
                return level_id
        return self.order[0]

    def next_after(self, level_id: str) -> Optional[str]:
        if level_id not in self.order:
            return None
        i = self.order.index(level_id)
        return self.order[i + 1] if i + 1 < len(self.order) else None


def fresh_save(view: CampaignView) -> SaveData:
    return SaveData(unlocked=[view.first()])


def recompute_unlocks(data: SaveData, view: CampaignView) -> None:
    unlocked = list(data.unlocked)
    for level_id in [view.first(), *data.completed]:
        if level_id not in unlocked:
            unlocked.append(level_id)
        nxt = view.next_after(level_id) if level_id in data.completed else None
        if nxt and nxt not in unlocked:
            unlocked.append(nxt)
    data.unlocked = unlocked


def sanitize(raw: Any, view: CampaignView) -> SaveData:
    if not isinstance(raw, dict) or raw.get("version") != SAVE_VERSION:
        return fresh_save(view)
    data = SaveData(
        unlocked=_ids(raw.get("unlocked")),
        completed=_ids(raw.get("completed")),
        records=_records(raw.get("records")),
        relics=_id_map(raw.get("relics")),
        secrets=_id_map(raw.get("secrets")),
        achievements=_ids(raw.get("achievements")),
        legacy_relic_marks=_ids(raw.get("legacy_relic_marks")),
        legacy_achievements=_ids(raw.get("legacy_achievements")),
        migrated_from=raw.get("migrated_from") if isinstance(raw.get("migrated_from"), str) else "",
        settings=_settings(raw.get("settings")),
    )
    recompute_unlocks(data, view)
    return data


def migrate_v1(raw: Any, view: CampaignView) -> SaveData:
    """Convert the browser save (format 1) without discarding information."""
    if not isinstance(raw, dict) or raw.get("version") != 1:
        return fresh_save(view)
    mapping = view.legacy
    completed_old = _ids(raw.get("completed"))
    data = SaveData(migrated_from=LEGACY_KEY, settings=_settings(raw.get("settings")))
    data.completed = [mapping[o] for o in completed_old if o in mapping]
    for old, score in _records(raw.get("records")).items():
        new = mapping.get(old)
        if new:
            data.records[new] = max(data.records.get(new, 0), score)
    data.legacy_relic_marks = [mapping[o] for o in _ids(raw.get("relics")) if o in mapping]
    data.legacy_achievements = _ids(raw.get("achievements"))
    unlocked_index = int(_number(raw.get("unlocked"), 0, len(LEGACY_ORDER) - 1, True))
    data.unlocked = [mapping[o] for o in LEGACY_ORDER[: unlocked_index + 1] if o in mapping]
    recompute_unlocks(data, view)
    return data


def load_data(raw: Any, view: CampaignView) -> SaveData:
    if isinstance(raw, dict) and raw.get("version") == 1:
        return migrate_v1(raw, view)
    return sanitize(raw, view)


# --------------------------------------------------------------------------- files
def save_dir() -> Path:
    override = os.environ.get("LUME_SAVE_DIR")
    if override:
        return Path(override)
    if sys.platform.startswith("win"):
        return Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming")) / "Lume"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "Lume"
    return Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")) / "lume"


def load_save(view: CampaignView, directory: Optional[Path] = None) -> tuple[SaveData, list[str]]:
    """Return the save and human-readable notices (backup made, migration)."""
    notices: list[str] = []
    folder = directory or save_dir()
    path = folder / SAVE_FILE
    if not path.exists():
        legacy = folder / f"{LEGACY_KEY}.json"
        if legacy.exists():
            data, more = import_legacy_file(legacy, view)
            return data, more
        return fresh_save(view), notices
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        backup = _backup(path)
        notices.append(f"Salvamento ilegível preservado em {backup.name}; um novo progresso foi iniciado.")
        return fresh_save(view), notices
    if not isinstance(raw, dict) or raw.get("version") not in (1, SAVE_VERSION):
        backup = _backup(path)
        notices.append(f"Versão de salvamento desconhecida preservada em {backup.name}.")
        return fresh_save(view), notices
    data = load_data(raw, view)
    if raw.get("version") == 1:
        notices.append("Progresso da edição web importado.")
    return data, notices


def import_legacy_file(path: Path, view: CampaignView) -> tuple[SaveData, list[str]]:
    """Import a JSON file exported from the browser (value of lume-save-v1)."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return fresh_save(view), [f"Não foi possível ler {path.name}."]
    if isinstance(raw, dict) and LEGACY_KEY in raw and isinstance(raw[LEGACY_KEY], str):
        try:
            raw = json.loads(raw[LEGACY_KEY])
        except ValueError:
            return fresh_save(view), [f"{path.name} não contém um salvamento válido."]
    data = migrate_v1(raw, view)
    if data.migrated_from:
        return data, ["Progresso da edição web importado."]
    return data, [f"{path.name} não é um salvamento lume-save-v1 válido."]


def write_save(data: SaveData, view: CampaignView, directory: Optional[Path] = None) -> bool:
    folder = directory or save_dir()
    try:
        folder.mkdir(parents=True, exist_ok=True)
        clean = sanitize(data.to_json(), view)
        clean.migrated_from = data.migrated_from
        tmp = folder / (SAVE_FILE + ".tmp")
        tmp.write_text(json.dumps(clean.to_json(), ensure_ascii=False, indent=1), encoding="utf-8")
        os.replace(tmp, folder / SAVE_FILE)
        return True
    except OSError:
        return False


def reset_save(view: CampaignView, directory: Optional[Path] = None) -> SaveData:
    folder = directory or save_dir()
    path = folder / SAVE_FILE
    if path.exists():
        _backup(path, "reset")
    return fresh_save(view)


def _backup(path: Path, reason: str = "corrupt") -> Path:
    target = path.with_name(f"save.{reason}-{time.strftime('%Y%m%d-%H%M%S')}.json")
    n = 1
    while target.exists():
        n += 1
        target = path.with_name(f"save.{reason}-{time.strftime('%Y%m%d-%H%M%S')}-{n}.json")
    try:
        target.write_bytes(path.read_bytes())
    except OSError:
        pass
    return target


# --------------------------------------------------------------------------- progress
def complete_level(
    data: SaveData,
    view: CampaignView,
    level_id: str,
    score: float,
    relics: Iterable[str] = (),
    secrets: Iterable[str] = (),
) -> SaveData:
    if not _valid_id(level_id) or level_id not in view.order:
        return data
    if level_id not in data.completed:
        data.completed.append(level_id)
    data.records[level_id] = max(data.records.get(level_id, 0), int(_number(score, 0, 2**53 - 1, True)))
    found = data.relics.setdefault(level_id, [])
    for r in relics:
        if _valid_id(r) and r not in found:
            found.append(r)
    if not found:
        data.relics.pop(level_id, None)
    s_found = data.secrets.setdefault(level_id, [])
    for s in secrets:
        if _valid_id(s) and s not in s_found:
            s_found.append(s)
    if not s_found:
        data.secrets.pop(level_id, None)
    recompute_unlocks(data, view)
    return data


def has_relic_mark(data: SaveData, level_id: str) -> bool:
    return bool(data.relics.get(level_id)) or level_id in data.legacy_relic_marks
