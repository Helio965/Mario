"""Campaign registry: worlds, stable level ids, order and playable levels.

The order of worlds/levels comes from ``lume/data/campaign.json``; identity
comes from ids, never from positions or file names. A level listed in the
campaign but without a data file is *planned* (not playable).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Optional

from .errors import DataError, Problem, Reader
from .schema import LevelSpec, parse_level

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
LEVELS_DIR = DATA_DIR / "levels"


@dataclass(frozen=True, slots=True)
class LevelEntry:
    id: str
    name: str
    world: str
    slot: int  # 1-based position inside the world (presentation only)
    order: int  # 0-based position in the whole campaign (presentation only)
    path: Path

    @property
    def implemented(self) -> bool:
        return self.path.exists()


@dataclass(frozen=True, slots=True)
class World:
    id: str
    name: str
    subtitle: str
    biome: str
    legacy_world: Optional[int]
    color: str
    entries: tuple[LevelEntry, ...]
    number: int


@dataclass
class Campaign:
    title: str
    worlds: list[World]
    levels: list[LevelSpec] = field(default_factory=list)  # playable, campaign order
    entries: list[LevelEntry] = field(default_factory=list)  # all 60, campaign order

    def world(self, world_id: str) -> World:
        for w in self.worlds:
            if w.id == world_id:
                return w
        raise KeyError(world_id)

    def entry(self, level_id: str) -> LevelEntry:
        for e in self.entries:
            if e.id == level_id:
                return e
        raise KeyError(level_id)

    def level(self, level_id: str) -> LevelSpec:
        for level in self.levels:
            if level.id == level_id:
                return level
        raise KeyError(level_id)

    def world_number(self, world_id: str) -> int:
        return self.world(world_id).number

    @property
    def planned(self) -> list[LevelEntry]:
        return [e for e in self.entries if not e.implemented]


def level_path(world_id: str, level_id: str) -> Path:
    return LEVELS_DIR / world_id / f"{level_id}.json"


def parse_campaign(data, source: str = "campaign.json") -> Campaign:
    r = Reader(source)
    root = r.obj(data, "$")
    if root.get("format") != "lume.campaign" or root.get("format_version") != 1:
        r.error("$", "esperado format='lume.campaign' e format_version=1")
    worlds: list[World] = []
    entries: list[LevelEntry] = []
    seen_worlds: set[str] = set()
    seen_levels: set[str] = set()
    for wi, raw in enumerate(r.arr(root.get("worlds"), "$.worlds")):
        path = f"worlds[{wi}]"
        w = r.obj(raw, path)
        wid = r.string(w, "id", path)
        if wid in seen_worlds:
            r.error(f"{path}.id", f"mundo '{wid}' repetido")
        seen_worlds.add(wid)
        world_entries = []
        for li, lraw in enumerate(r.arr(w.get("levels"), f"{path}.levels")):
            lpath = f"{path}.levels[{li}]"
            entry = r.obj(lraw, lpath)
            lid = r.string(entry, "id", lpath)
            if lid in seen_levels:
                r.error(f"{lpath}.id", f"fase '{lid}' repetida na campanha")
            seen_levels.add(lid)
            le = LevelEntry(lid, r.string(entry, "name", lpath), wid, li + 1, len(entries), level_path(wid, lid))
            world_entries.append(le)
            entries.append(le)
        worlds.append(
            World(wid, r.string(w, "name", path), r.string(w, "subtitle", path), r.string(w, "biome", path),
                  w.get("legacy_world"), r.string(w, "color", path, "#ffffff", required=False), tuple(world_entries), wi + 1)
        )
    if any(p.severity == "error" for p in r.problems):
        raise DataError(r.problems)
    return Campaign(r.string(root, "title", "$", "Lume"), worlds, [], entries)


def load_level_file(path: Path) -> LevelSpec:
    try:
        with path.open(encoding="utf-8") as handle:
            data = json.load(handle)
    except json.JSONDecodeError as exc:
        raise DataError([Problem(str(path.name), f"linha {exc.lineno}", f"JSON inválido: {exc.msg}")]) from exc
    return parse_level(data, source=str(path.relative_to(DATA_DIR)) if DATA_DIR in path.parents else str(path))


@lru_cache(maxsize=1)
def load_campaign() -> Campaign:
    with (DATA_DIR / "campaign.json").open(encoding="utf-8") as handle:
        campaign = parse_campaign(json.load(handle))
    problems: list[Problem] = []
    for entry in campaign.entries:
        if not entry.implemented:
            continue
        try:
            level = load_level_file(entry.path)
        except DataError as exc:
            problems.extend(exc.problems)
            continue
        if level.id != entry.id:
            problems.append(Problem(entry.path.name, "$.id", f"id '{level.id}' difere do registro '{entry.id}'"))
        if level.world != entry.world:
            problems.append(Problem(entry.path.name, "$.world", f"mundo '{level.world}' difere do registro '{entry.world}'"))
        campaign.levels.append(level)
    if problems:
        raise DataError(problems)
    return campaign
