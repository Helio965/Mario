"""Carrega as fases e os temas de ``data/levels`` (JSON exportado do TS)."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from game.core.types import (
    CoinSpec,
    EnemySpec,
    Hazard,
    Hint,
    ItemSpec,
    Level,
    Motion,
    NpcSpec,
    PlatformSpec,
    RoutineStep,
    Theme,
    Vec,
)
from game.paths import data_path

LEVEL_FORMAT = "lume-level/1"


def _vec(value: Any) -> Vec:
    return Vec(float(value["x"]), float(value["y"]))


def platform_from_dict(d: dict[str, Any]) -> PlatformSpec:
    motion = d.get("motion")
    return PlatformSpec(
        id=str(d["id"]),
        kind=d["kind"],
        x=float(d["x"]),
        y=float(d["y"]),
        w=float(d["w"]),
        h=float(d["h"]),
        reward=d.get("reward"),
        motion=Motion(
            motion["axis"],
            float(motion["range"]),
            float(motion["speed"]),
            float(motion.get("phase", 0) or 0),
        )
        if motion
        else None,
        destination=_vec(d["destination"]) if d.get("destination") else None,
        return_point=_vec(d["returnPoint"]) if d.get("returnPoint") else None,
    )


def level_from_dict(d: dict[str, Any]) -> Level:
    """Constrói uma ``Level`` a partir do dicionário JSON (chaves do formato TS)."""
    return Level(
        id=str(d["id"]),
        name=str(d["name"]),
        world=int(d["world"]),
        stage=int(d["stage"]),
        width=float(d["width"]),
        height=float(d["height"]),
        time=float(d["time"]),
        spawn=_vec(d["spawn"]),
        checkpoint=_vec(d["checkpoint"]),
        exit=_vec(d["exit"]),
        platforms=[platform_from_dict(p) for p in d.get("platforms", [])],
        coins=[
            CoinSpec(
                str(c["id"]),
                float(c["x"]),
                float(c["y"]),
                float(c["w"]),
                float(c["h"]),
                bool(c.get("special", False)),
            )
            for c in d.get("coins", [])
        ],
        enemies=[
            EnemySpec(
                str(e["id"]),
                e["kind"],
                float(e["x"]),
                float(e["y"]),
                float(e["w"]),
                float(e["h"]),
                [float(e["patrol"][0]), float(e["patrol"][1])],
                e.get("hp"),
            )
            for e in d.get("enemies", [])
        ],
        items=[
            ItemSpec(
                str(i["id"]), i["kind"], float(i["x"]), float(i["y"]), float(i["w"]), float(i["h"])
            )
            for i in d.get("items", [])
        ],
        hazards=[
            Hazard(
                h["kind"],
                float(h["x"]),
                float(h["y"]),
                float(h["w"]),
                float(h["h"]),
                h.get("range"),
                h.get("speed"),
            )
            for h in d.get("hazards", [])
        ],
        hints=[Hint(float(h["x"]), str(h["text"])) for h in d.get("hints", [])],
        npcs=[npc_from_dict(n) for n in d.get("npcs", [])],
    )


def npc_from_dict(d: dict[str, Any]) -> NpcSpec:
    return NpcSpec(
        id=str(d["id"]),
        kind=str(d.get("kind", "guide")),
        x=float(d["x"]),
        y=float(d["y"]),
        w=float(d.get("w", 24)),
        h=float(d.get("h", 32)),
        facing=int(d.get("facing", 1)),
        routine=[
            RoutineStep(
                action=str(s["action"]),
                x=float(s.get("x", 0)),
                speed=float(s.get("speed", 60)),
                seconds=float(s.get("seconds", 1)),
                facing=int(s.get("facing", 1)),
                expression=str(s.get("expression", "neutral")),
                reaction=str(s.get("reaction", "")),
            )
            for s in d.get("routine", [])
        ],
        loop=bool(d.get("loop", True)),
        dialogue=d.get("dialogue"),
        talk_once=bool(d.get("talk_once", False)),
        reactions=str(d.get("reactions", "")),
        observe_distance=float(d.get("observe_distance", 90)),
    )


def npc_to_dict(n: NpcSpec) -> dict[str, Any]:
    steps = []
    for s in n.routine:
        step: dict[str, Any] = {"action": s.action}
        if s.action == "walk":
            step.update({"x": s.x, "speed": s.speed})
        elif s.action in ("wait", "emote"):
            step["seconds"] = s.seconds
        if s.action == "look":
            step["facing"] = s.facing
        if s.action == "emote":
            step["expression"] = s.expression
        if s.action == "say":
            step["reaction"] = s.reaction
        steps.append(step)
    entry: dict[str, Any] = {
        "id": n.id,
        "kind": n.kind,
        "x": n.x,
        "y": n.y,
        "w": n.w,
        "h": n.h,
        "facing": n.facing,
        "routine": steps,
        "loop": n.loop,
    }
    if n.dialogue is not None:
        entry["dialogue"] = n.dialogue
    if n.talk_once:
        entry["talk_once"] = True
    if n.reactions:
        entry["reactions"] = n.reactions
    if n.observe_distance != 90:
        entry["observe_distance"] = n.observe_distance
    return entry


def level_to_dict(level: Level) -> dict[str, Any]:
    """Inverso de ``level_from_dict`` (usado pelo editor e pelos testes comparativos)."""
    platforms = []
    for p in level.platforms:
        entry: dict[str, Any] = {"id": p.id, "kind": p.kind, "x": p.x, "y": p.y, "w": p.w, "h": p.h}
        if p.reward is not None:
            entry["reward"] = p.reward
        if p.motion is not None:
            entry["motion"] = {
                "axis": p.motion.axis,
                "range": p.motion.range,
                "speed": p.motion.speed,
                "phase": p.motion.phase,
            }
        if p.destination is not None:
            entry["destination"] = {"x": p.destination.x, "y": p.destination.y}
        if p.return_point is not None:
            entry["returnPoint"] = {"x": p.return_point.x, "y": p.return_point.y}
        platforms.append(entry)
    return {
        "format": LEVEL_FORMAT,
        "id": level.id,
        "world": level.world,
        "stage": level.stage,
        "name": level.name,
        "width": level.width,
        "height": level.height,
        "time": level.time,
        "spawn": {"x": level.spawn.x, "y": level.spawn.y},
        "checkpoint": {"x": level.checkpoint.x, "y": level.checkpoint.y},
        "exit": {"x": level.exit.x, "y": level.exit.y},
        "platforms": platforms,
        "coins": [
            {
                "id": c.id,
                "x": c.x,
                "y": c.y,
                "w": c.w,
                "h": c.h,
                **({"special": True} if c.special else {}),
            }
            for c in level.coins
        ],
        "enemies": [
            {
                "id": e.id,
                "kind": e.kind,
                "x": e.x,
                "y": e.y,
                "w": e.w,
                "h": e.h,
                "patrol": list(e.patrol),
                **({"hp": e.hp} if e.hp else {}),
            }
            for e in level.enemies
        ],
        "items": [
            {"id": i.id, "kind": i.kind, "x": i.x, "y": i.y, "w": i.w, "h": i.h}
            for i in level.items
        ],
        "hazards": [
            {
                "kind": h.kind,
                "x": h.x,
                "y": h.y,
                "w": h.w,
                "h": h.h,
                **({"range": h.range} if h.range is not None else {}),
                **({"speed": h.speed} if h.speed is not None else {}),
            }
            for h in level.hazards
        ],
        "hints": [{"x": h.x, "text": h.text} for h in level.hints],
        **({"npcs": [npc_to_dict(n) for n in level.npcs]} if level.npcs else {}),
    }


def levels_dir() -> Path:
    return data_path("levels")


@lru_cache(maxsize=1)
def load_index() -> dict[str, Any]:
    with open(levels_dir() / "index.json", encoding="utf-8") as handle:
        index: dict[str, Any] = json.load(handle)
    return index


def load_themes() -> list[Theme]:
    return [Theme(**t) for t in load_index()["themes"]]


def load_level_file(path: Path) -> Level:
    with open(path, encoding="utf-8") as handle:
        data = json.load(handle)
    if data.get("format") != LEVEL_FORMAT:
        raise ValueError(f"{path}: formato de fase desconhecido {data.get('format')!r}")
    return level_from_dict(data)


def load_levels() -> list[Level]:
    """Lê todas as fases na ordem do índice. Cada chamada devolve objetos novos."""
    index = load_index()
    return [load_level_file(levels_dir() / entry["file"]) for entry in index["levels"]]


THEMES: list[Theme] = load_themes()
