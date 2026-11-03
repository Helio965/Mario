"""Typed registry of enemy species (``lume/data/enemies.json``).

A *species* is data: habitat, size, tuning and which behaviour/animation rig it
uses. The behaviour code lives in :mod:`lume.core.behaviors`; the art rig lives in
:mod:`lume.render.enemies`. Validation guarantees that every species points to
real code and that levels only use species compatible with their biome.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

from ..levels.errors import DataError, Reader

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

BIOMES = {
    "grassland", "desert", "coast", "underwater", "snow", "forest", "city", "sky",
    "swamp", "volcano", "citadel", "underground", "fortress",
}
MOVEMENT_TYPES = {"ground", "air", "water", "burrow", "stationary", "ghost", "hopper", "ceiling"}
WEAKNESSES = {"stomp", "fire", "shell", "star", "bump", "explosion"}
ABILITIES = {
    "shell", "kickable", "projectile", "arc_projectile", "fly", "swim", "burrow", "emerge", "charge",
    "camouflage", "spiked_top", "fire_immune", "stomp_immune", "reassemble", "inflate", "crush",
    "light_reactive", "phase", "summon", "slide", "wind", "explode", "follow", "shield", "segments",
}


@dataclass(frozen=True, slots=True)
class EnemyProfile:
    id: str
    name: str
    role_reference: str
    description: str
    habitats: tuple[str, ...]
    movement_type: str
    difficulty_tier: int
    behavior: str
    abilities: tuple[str, ...]
    weaknesses: tuple[str, ...]
    size: tuple[float, float]
    hp: int
    speed: float
    score: int
    animation_set: str
    animation_states: tuple[str, ...]
    visual_theme: str
    defeat: str
    introduced_in: str = ""
    boss: bool = False
    params: dict[str, Any] = field(default_factory=dict)

    @property
    def w(self) -> float:
        return self.size[0]

    @property
    def h(self) -> float:
        return self.size[1]


def parse_profiles(data: Any, source: str = "enemies.json") -> dict[str, EnemyProfile]:
    r = Reader(source)
    root = r.obj(data, "$")
    if root.get("format") != "lume.enemies" or root.get("format_version") != 1:
        r.error("$", "esperado format='lume.enemies' e format_version=1")
    profiles: dict[str, EnemyProfile] = {}
    for i, raw in enumerate(r.arr(root.get("species"), "$.species")):
        path = f"species[{i}]"
        s = r.obj(raw, path)
        r.unknown_keys(
            s,
            {"id", "name", "role_reference", "description", "habitats", "movement_type", "difficulty_tier",
             "behavior", "abilities", "weaknesses", "size", "hp", "speed", "score", "animation_set",
             "animation_states", "visual_theme", "defeat", "introduced_in", "boss", "params"},
            path,
        )
        sid = r.string(s, "id", path)
        if sid in profiles:
            r.error(f"{path}.id", f"espécie '{sid}' duplicada")
        habitats = tuple(r.arr(s.get("habitats"), f"{path}.habitats"))
        for h in habitats:
            if h not in BIOMES:
                r.error(f"{path}.habitats", f"bioma desconhecido '{h}'")
        if not habitats:
            r.error(f"{path}.habitats", "informe ao menos um habitat")
        abilities = tuple(r.arr(s.get("abilities"), f"{path}.abilities"))
        for a in abilities:
            if a not in ABILITIES:
                r.error(f"{path}.abilities", f"habilidade desconhecida '{a}'")
        weaknesses = tuple(r.arr(s.get("weaknesses"), f"{path}.weaknesses"))
        for w in weaknesses:
            if w not in WEAKNESSES:
                r.error(f"{path}.weaknesses", f"fraqueza desconhecida '{w}'")
        size = r.arr(s.get("size"), f"{path}.size")
        if len(size) != 2 or not all(isinstance(v, (int, float)) and 4 <= v <= 400 for v in size):
            r.error(f"{path}.size", "deveria ser [largura, altura] entre 4 e 400")
            size = [28, 28]
        states = tuple(r.arr(s.get("animation_states"), f"{path}.animation_states"))
        if "defeat" not in states:
            r.error(f"{path}.animation_states", "toda espécie precisa do estado 'defeat'")
        params = s.get("params", {})
        if not isinstance(params, dict):
            r.error(f"{path}.params", "deveria ser um objeto")
            params = {}
        profiles[sid] = EnemyProfile(
            id=sid,
            name=r.string(s, "name", path),
            role_reference=r.string(s, "role_reference", path),
            description=r.string(s, "description", path),
            habitats=habitats,
            movement_type=r.choice(s, "movement_type", path, MOVEMENT_TYPES),
            difficulty_tier=r.integer(s, "difficulty_tier", path, minimum=1, maximum=6),
            behavior=r.string(s, "behavior", path),
            abilities=abilities,
            weaknesses=weaknesses,
            size=(float(size[0]), float(size[1])),
            hp=r.integer(s, "hp", path, 1, minimum=1, maximum=40),
            speed=r.number(s, "speed", path, 0.0, minimum=0, maximum=900),
            score=r.integer(s, "score", path, 200, minimum=0, maximum=100000),
            animation_set=r.string(s, "animation_set", path),
            animation_states=states,
            visual_theme=r.string(s, "visual_theme", path),
            defeat=r.string(s, "defeat", path),
            introduced_in=s.get("introduced_in", "") or "",
            boss=r.boolean(s, "boss", path, False),
            params=dict(params),
        )
    if any(p.severity == "error" for p in r.problems):
        raise DataError(r.problems)
    return profiles


@lru_cache(maxsize=1)
def load_profiles(path: str | None = None) -> dict[str, EnemyProfile]:
    file = Path(path) if path else DATA_DIR / "enemies.json"
    with file.open(encoding="utf-8") as handle:
        return parse_profiles(json.load(handle), str(file.name))
