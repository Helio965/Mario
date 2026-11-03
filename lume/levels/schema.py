"""Typed, validated representation of a ``lume.level`` JSON file (format 1).

Coordinates are world units. ``spawn``/checkpoint/warp targets describe the
player's top-left corner; enemy ``y`` is the *feet* line (bottom of the
hitbox); ``exit.y`` is the base of the goal flag. See
``docs/technical/ARQUITETURA_FASES.md`` for the full reference.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import Any, Optional

from .errors import DataError, Reader

LEVEL_FORMAT = "lume.level"
LEVEL_FORMAT_VERSION = 1
ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]{1,63}$")
LOCAL_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_\-]{0,63}$")

ROLES = {"presentation", "exploration", "movement", "special", "advanced", "fortress", "secret", "bonus"}
PLATFORM_KINDS = {
    "ground", "ledge", "brick", "question", "hidden", "moving", "crumble",
    "pipe", "semisolid", "conveyor", "spring", "switch",
}
SURFACES = {"normal", "ice", "sticky"}
REWARDS = {"coin", "grow", "fire", "star", "heart"}
ITEM_KINDS = {"grow", "fire", "star", "heart"}
HAZARD_KINDS = {"lava", "water", "spikes", "moving", "thorns", "electric", "poison"}
ZONE_KINDS = {"swim", "current", "wind", "dark", "quicksand", "lowgrav"}
COLLECTIBLE_KINDS = {"relic"}
SECRET_KINDS = {"warp_room", "hidden_block", "high_route", "breakable_path", "hidden_area", "optional_challenge"}
EVENT_KINDS = {"boss_arena", "camera_lock", "rising_lava", "lights", "toggle_switch", "message"}
DECOR_LAYERS = {"back", "mid", "front"}
COIN_SHAPES = {"row", "arc", "column", "grid", "diagonal"}
EXIT_KINDS = {"flag", "gate"}


@dataclass(frozen=True, slots=True)
class Point:
    x: float
    y: float


@dataclass(frozen=True, slots=True)
class MotionSpec:
    axis: str  # x | y | circle
    range: float
    speed: float
    phase: float = 0.0


@dataclass(frozen=True, slots=True)
class PlatformSpec:
    id: str
    kind: str
    x: float
    y: float
    w: float
    h: float
    style: str = ""
    surface: str = "normal"
    reward: Optional[str] = None
    motion: Optional[MotionSpec] = None
    warp: Optional[Point] = None
    return_point: Optional[Point] = None
    secret: Optional[str] = None
    surface_speed: float = 0.0
    bounce: float = 0.0
    group: str = ""


@dataclass(frozen=True, slots=True)
class CoinSpec:
    id: str
    x: float
    y: float


@dataclass(frozen=True, slots=True)
class CollectibleSpec:
    id: str
    kind: str
    x: float
    y: float


@dataclass(frozen=True, slots=True)
class ItemSpec:
    id: str
    kind: str
    x: float
    y: float


@dataclass(frozen=True, slots=True)
class EnemySpec:
    id: str
    species: str
    x: float
    y: float  # feet line
    patrol: tuple[float, float]
    hp: Optional[int] = None
    params: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class HazardSpec:
    id: str
    kind: str
    x: float
    y: float
    w: float
    h: float
    range: float = 30.0
    speed: float = 1.0
    phase: float = 0.0


@dataclass(frozen=True, slots=True)
class ZoneSpec:
    id: str
    kind: str
    x: float
    y: float
    w: float
    h: float
    force_x: float = 0.0
    force_y: float = 0.0
    period: float = 0.0
    duty: float = 1.0
    radius: float = 0.0


@dataclass(frozen=True, slots=True)
class CheckpointSpec:
    id: str
    x: float
    y: float


@dataclass(frozen=True, slots=True)
class ExitSpec:
    id: str
    kind: str
    x: float
    y: float
    next: Optional[str] = None


@dataclass(frozen=True, slots=True)
class AreaSpec:
    id: str
    x: float
    y: float
    w: float
    h: float
    variant: str = ""
    music: str = ""


@dataclass(frozen=True, slots=True)
class SecretSpec:
    id: str
    kind: str
    clue: str
    rewards: tuple[str, ...] = ()
    entry: Optional[str] = None


@dataclass(frozen=True, slots=True)
class HintSpec:
    x: float
    text: str


@dataclass(frozen=True, slots=True)
class DecorSpec:
    prop: str
    x: float
    y: float
    layer: str = "mid"
    scale: float = 1.0
    flip: bool = False


@dataclass(frozen=True, slots=True)
class EventSpec:
    id: str
    kind: str
    x: float = 0.0
    params: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class LevelSpec:
    id: str
    name: str
    world: str
    role: str
    difficulty: int
    art_set: str
    art_variant: str
    weather: str
    music: str
    width: float
    height: float
    time_limit: float
    spawn: Point
    checkpoints: tuple[CheckpointSpec, ...]
    exit: ExitSpec
    platforms: tuple[PlatformSpec, ...]
    coins: tuple[CoinSpec, ...]
    collectibles: tuple[CollectibleSpec, ...]
    items: tuple[ItemSpec, ...]
    enemies: tuple[EnemySpec, ...]
    hazards: tuple[HazardSpec, ...]
    zones: tuple[ZoneSpec, ...]
    areas: tuple[AreaSpec, ...]
    secrets: tuple[SecretSpec, ...]
    hints: tuple[HintSpec, ...]
    decor: tuple[DecorSpec, ...]
    events: tuple[EventSpec, ...]
    legacy_ids: tuple[str, ...] = ()
    source: str = ""
    notes: str = ""

    def area_at(self, x: float, y: float) -> AreaSpec:
        for area in self.areas:
            if area.x <= x < area.x + area.w and area.y <= y < area.y + area.h:
                return area
        return self.areas[0]


def _point(r: Reader, value, path: str) -> Point:
    data = r.obj(value, path)
    return Point(r.number(data, "x", path), r.number(data, "y", path))


def _local_id(r: Reader, data: dict, path: str, seen: set[str]) -> str:
    value = r.string(data, "id", path)
    if value and not LOCAL_ID_PATTERN.match(value):
        r.error(f"{path}.id", "use letras minúsculas, dígitos, '_' ou '-' (até 64)")
    if value in seen:
        r.error(f"{path}.id", f"identificador '{value}' repetido na fase")
    seen.add(value)
    return value


def _expand_coins(r: Reader, groups: list, seen: set[str]) -> list[CoinSpec]:
    coins: list[CoinSpec] = []
    for gi, raw in enumerate(groups):
        path = f"coin_groups[{gi}]"
        g = r.obj(raw, path)
        r.unknown_keys(g, {"id", "shape", "x", "y", "count", "spacing", "rise", "rows"}, path)
        gid = _local_id(r, g, path, seen)
        shape = r.choice(g, "shape", path, COIN_SHAPES)
        x, y = r.number(g, "x", path), r.number(g, "y", path)
        count = r.integer(g, "count", path, minimum=1, maximum=40)
        spacing = r.number(g, "spacing", path, 34 if shape in ("row", "grid") else 30, required=False, minimum=8)
        rise = r.number(g, "rise", path, 32, required=False)
        rows = r.integer(g, "rows", path, 1, required=False, minimum=1, maximum=8)
        for i in range(count):
            for row in range(rows if shape == "grid" else 1):
                if shape == "row" or shape == "grid":
                    cx, cy = x + i * spacing, y + row * spacing
                elif shape == "arc":
                    cx = x + i * spacing
                    cy = y - math.sin(math.pi * i / max(1, count - 1)) * rise
                elif shape == "column":
                    cx, cy = x, y + i * spacing
                else:  # diagonal
                    cx, cy = x + i * spacing, y - i * rise
                suffix = f"{i + 1}" if rows == 1 or shape != "grid" else f"{row + 1}_{i + 1}"
                coins.append(CoinSpec(f"{gid}-{suffix}", cx, cy))
    return coins


def parse_level(data: Any, source: str = "<memória>") -> LevelSpec:
    """Parse decoded JSON into a :class:`LevelSpec` or raise :class:`DataError`."""

    r = Reader(source)
    root = r.obj(data, "$")
    allowed = {
        "format", "format_version", "id", "legacy_ids", "name", "world", "role", "difficulty", "art",
        "music", "bounds", "areas", "time_limit", "spawn", "checkpoints", "exit", "platforms", "coins",
        "coin_groups", "collectibles", "items", "enemies", "hazards", "zones", "secrets", "hints", "decor",
        "events", "notes",
    }
    r.unknown_keys(root, allowed, "$")
    if root.get("format") != LEVEL_FORMAT:
        r.error("$.format", f"deveria ser '{LEVEL_FORMAT}'")
    if root.get("format_version") != LEVEL_FORMAT_VERSION:
        r.error("$.format_version", f"versão suportada: {LEVEL_FORMAT_VERSION}")
    level_id = r.string(root, "id", "$")
    if level_id and not ID_PATTERN.match(level_id):
        r.error("$.id", "use snake_case ASCII começando com letra (2–64 caracteres)")
    name = r.string(root, "name", "$")
    world = r.string(root, "world", "$")
    role = r.choice(root, "role", "$", ROLES)
    difficulty = r.integer(root, "difficulty", "$", minimum=1, maximum=10)
    art = r.obj(root.get("art", {}), "$.art")
    r.unknown_keys(art, {"set", "variant", "weather"}, "$.art")
    art_set = r.string(art, "set", "$.art")
    art_variant = r.string(art, "variant", "$.art", "default", required=False)
    weather = r.string(art, "weather", "$.art", "none", required=False)
    music = r.string(root, "music", "$")
    bounds = r.obj(root.get("bounds"), "$.bounds")
    width = r.number(bounds, "width", "$.bounds", minimum=960, maximum=40000)
    height = r.number(bounds, "height", "$.bounds", minimum=540, maximum=8000)
    time_limit = r.number(root, "time_limit", "$", minimum=30, maximum=999)
    spawn = _point(r, root.get("spawn"), "$.spawn")
    seen: set[str] = set()

    checkpoints = []
    for i, raw in enumerate(r.arr(root.get("checkpoints"), "$.checkpoints")):
        path = f"checkpoints[{i}]"
        c = r.obj(raw, path)
        r.unknown_keys(c, {"id", "x", "y"}, path)
        checkpoints.append(CheckpointSpec(_local_id(r, c, path, seen), r.number(c, "x", path), r.number(c, "y", path)))

    exit_raw = r.obj(root.get("exit"), "$.exit")
    r.unknown_keys(exit_raw, {"id", "kind", "x", "y", "next"}, "$.exit")
    exit_spec = ExitSpec(
        _local_id(r, exit_raw, "$.exit", seen),
        r.choice(exit_raw, "kind", "$.exit", EXIT_KINDS, "flag"),
        r.number(exit_raw, "x", "$.exit"),
        r.number(exit_raw, "y", "$.exit"),
        exit_raw.get("next"),
    )

    platforms = []
    for i, raw in enumerate(r.arr(root.get("platforms"), "$.platforms")):
        path = f"platforms[{i}]"
        p = r.obj(raw, path)
        r.unknown_keys(
            p,
            {"id", "kind", "x", "y", "w", "h", "style", "surface", "reward", "motion", "warp", "return",
             "secret", "surface_speed", "bounce", "group"},
            path,
        )
        motion = None
        if "motion" in p:
            m = r.obj(p["motion"], f"{path}.motion")
            r.unknown_keys(m, {"axis", "range", "speed", "phase"}, f"{path}.motion")
            motion = MotionSpec(
                r.choice(m, "axis", f"{path}.motion", {"x", "y", "circle"}),
                r.number(m, "range", f"{path}.motion", minimum=0, maximum=600),
                r.number(m, "speed", f"{path}.motion", minimum=0, maximum=20),
                r.number(m, "phase", f"{path}.motion", 0.0, required=False),
            )
        reward = p.get("reward")
        if reward is not None and reward not in REWARDS:
            r.error(f"{path}.reward", f"recompensa inválida '{reward}'")
        platforms.append(
            PlatformSpec(
                id=_local_id(r, p, path, seen),
                kind=r.choice(p, "kind", path, PLATFORM_KINDS),
                x=r.number(p, "x", path),
                y=r.number(p, "y", path),
                w=r.number(p, "w", path, minimum=4),
                h=r.number(p, "h", path, minimum=4),
                style=p.get("style", "") if isinstance(p.get("style", ""), str) else "",
                surface=r.choice(p, "surface", path, SURFACES, "normal"),
                reward=reward,
                motion=motion,
                warp=_point(r, p["warp"], f"{path}.warp") if "warp" in p else None,
                return_point=_point(r, p["return"], f"{path}.return") if "return" in p else None,
                secret=p.get("secret"),
                surface_speed=r.number(p, "surface_speed", path, 0.0, required=False, minimum=-400, maximum=400),
                bounce=r.number(p, "bounce", path, 0.0, required=False, minimum=0, maximum=1400),
                group=p.get("group", "") if isinstance(p.get("group", ""), str) else "",
            )
        )

    coins = []
    for i, raw in enumerate(r.arr(root.get("coins"), "$.coins")):
        path = f"coins[{i}]"
        c = r.obj(raw, path)
        r.unknown_keys(c, {"id", "x", "y"}, path)
        coins.append(CoinSpec(_local_id(r, c, path, seen), r.number(c, "x", path), r.number(c, "y", path)))
    for coin in _expand_coins(r, r.arr(root.get("coin_groups"), "$.coin_groups"), seen):
        if coin.id in seen:
            r.error("$.coin_groups", f"moeda gerada '{coin.id}' colide com outro identificador")
        seen.add(coin.id)
        coins.append(coin)

    collectibles = []
    for i, raw in enumerate(r.arr(root.get("collectibles"), "$.collectibles")):
        path = f"collectibles[{i}]"
        c = r.obj(raw, path)
        r.unknown_keys(c, {"id", "kind", "x", "y"}, path)
        collectibles.append(
            CollectibleSpec(
                _local_id(r, c, path, seen),
                r.choice(c, "kind", path, COLLECTIBLE_KINDS, "relic"),
                r.number(c, "x", path),
                r.number(c, "y", path),
            )
        )

    items = []
    for i, raw in enumerate(r.arr(root.get("items"), "$.items")):
        path = f"items[{i}]"
        it = r.obj(raw, path)
        r.unknown_keys(it, {"id", "kind", "x", "y"}, path)
        items.append(ItemSpec(_local_id(r, it, path, seen), r.choice(it, "kind", path, ITEM_KINDS), r.number(it, "x", path), r.number(it, "y", path)))

    enemies = []
    for i, raw in enumerate(r.arr(root.get("enemies"), "$.enemies")):
        path = f"enemies[{i}]"
        e = r.obj(raw, path)
        r.unknown_keys(e, {"id", "species", "x", "y", "patrol", "hp", "params"}, path)
        patrol_raw = r.arr(e.get("patrol"), f"{path}.patrol")
        patrol = (0.0, 0.0)
        if len(patrol_raw) == 2 and all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in patrol_raw):
            patrol = (float(patrol_raw[0]), float(patrol_raw[1]))
            if patrol[0] >= patrol[1]:
                r.error(f"{path}.patrol", "limite esquerdo deve ser menor que o direito")
        else:
            r.error(f"{path}.patrol", "deveria ser [esquerda, direita]")
        params = e.get("params", {})
        if not isinstance(params, dict):
            r.error(f"{path}.params", "deveria ser um objeto")
            params = {}
        hp = e.get("hp")
        if hp is not None and (isinstance(hp, bool) or not isinstance(hp, int) or hp < 1 or hp > 40):
            r.error(f"{path}.hp", "deveria ser inteiro entre 1 e 40")
            hp = None
        enemies.append(
            EnemySpec(_local_id(r, e, path, seen), r.string(e, "species", path), r.number(e, "x", path), r.number(e, "y", path), patrol, hp, dict(params))
        )

    hazards = []
    for i, raw in enumerate(r.arr(root.get("hazards"), "$.hazards")):
        path = f"hazards[{i}]"
        h = r.obj(raw, path)
        r.unknown_keys(h, {"id", "kind", "x", "y", "w", "h", "range", "speed", "phase"}, path)
        hazards.append(
            HazardSpec(
                _local_id(r, h, path, seen), r.choice(h, "kind", path, HAZARD_KINDS),
                r.number(h, "x", path), r.number(h, "y", path), r.number(h, "w", path, minimum=1), r.number(h, "h", path, minimum=1),
                r.number(h, "range", path, 30.0, required=False), r.number(h, "speed", path, 1.0, required=False),
                r.number(h, "phase", path, 0.0, required=False),
            )
        )

    zones = []
    for i, raw in enumerate(r.arr(root.get("zones"), "$.zones")):
        path = f"zones[{i}]"
        z = r.obj(raw, path)
        r.unknown_keys(z, {"id", "kind", "x", "y", "w", "h", "force_x", "force_y", "period", "duty", "radius"}, path)
        zones.append(
            ZoneSpec(
                _local_id(r, z, path, seen), r.choice(z, "kind", path, ZONE_KINDS),
                r.number(z, "x", path), r.number(z, "y", path), r.number(z, "w", path, minimum=1), r.number(z, "h", path, minimum=1),
                r.number(z, "force_x", path, 0.0, required=False, minimum=-2000, maximum=2000),
                r.number(z, "force_y", path, 0.0, required=False, minimum=-2000, maximum=2000),
                r.number(z, "period", path, 0.0, required=False, minimum=0, maximum=60),
                r.number(z, "duty", path, 1.0, required=False, minimum=0, maximum=1),
                r.number(z, "radius", path, 0.0, required=False, minimum=0, maximum=1000),
            )
        )

    areas = []
    for i, raw in enumerate(r.arr(root.get("areas"), "$.areas")):
        path = f"areas[{i}]"
        a = r.obj(raw, path)
        r.unknown_keys(a, {"id", "x", "y", "w", "h", "variant", "music"}, path)
        areas.append(
            AreaSpec(
                _local_id(r, a, path, seen), r.number(a, "x", path), r.number(a, "y", path),
                r.number(a, "w", path, minimum=960), r.number(a, "h", path, minimum=540),
                a.get("variant", "") or "", a.get("music", "") or "",
            )
        )
    if not areas:
        areas.append(AreaSpec("main", 0.0, 0.0, width, height, art_variant, music))

    secrets = []
    for i, raw in enumerate(r.arr(root.get("secrets"), "$.secrets")):
        path = f"secrets[{i}]"
        s = r.obj(raw, path)
        r.unknown_keys(s, {"id", "kind", "clue", "rewards", "entry"}, path)
        rewards = tuple(v for v in r.arr(s.get("rewards"), f"{path}.rewards") if isinstance(v, str))
        secrets.append(
            SecretSpec(_local_id(r, s, path, seen), r.choice(s, "kind", path, SECRET_KINDS), r.string(s, "clue", path), rewards, s.get("entry"))
        )

    hints = []
    for i, raw in enumerate(r.arr(root.get("hints"), "$.hints")):
        path = f"hints[{i}]"
        h = r.obj(raw, path)
        r.unknown_keys(h, {"x", "text"}, path)
        hints.append(HintSpec(r.number(h, "x", path), r.string(h, "text", path)))

    decor = []
    for i, raw in enumerate(r.arr(root.get("decor"), "$.decor")):
        path = f"decor[{i}]"
        d = r.obj(raw, path)
        r.unknown_keys(d, {"prop", "x", "y", "layer", "scale", "flip"}, path)
        decor.append(
            DecorSpec(
                r.string(d, "prop", path), r.number(d, "x", path), r.number(d, "y", path),
                r.choice(d, "layer", path, DECOR_LAYERS, "mid"),
                r.number(d, "scale", path, 1.0, required=False, minimum=0.1, maximum=6),
                r.boolean(d, "flip", path, False),
            )
        )

    events = []
    for i, raw in enumerate(r.arr(root.get("events"), "$.events")):
        path = f"events[{i}]"
        ev = r.obj(raw, path)
        r.unknown_keys(ev, {"id", "kind", "x", "params"}, path)
        params = ev.get("params", {})
        if not isinstance(params, dict):
            r.error(f"{path}.params", "deveria ser um objeto")
            params = {}
        events.append(
            EventSpec(_local_id(r, ev, path, seen), r.choice(ev, "kind", path, EVENT_KINDS), r.number(ev, "x", path, 0.0, required=False), dict(params))
        )

    legacy_ids = tuple(v for v in r.arr(root.get("legacy_ids"), "$.legacy_ids") if isinstance(v, str))
    notes = root.get("notes", "") if isinstance(root.get("notes", ""), str) else ""
    errors = [p for p in r.problems if p.severity == "error"]
    if errors:
        raise DataError(r.problems)
    return LevelSpec(
        id=level_id, name=name, world=world, role=role, difficulty=difficulty, art_set=art_set,
        art_variant=art_variant, weather=weather, music=music, width=width, height=height,
        time_limit=time_limit, spawn=spawn, checkpoints=tuple(checkpoints), exit=exit_spec,
        platforms=tuple(platforms), coins=tuple(coins), collectibles=tuple(collectibles), items=tuple(items),
        enemies=tuple(enemies), hazards=tuple(hazards), zones=tuple(zones), areas=tuple(areas),
        secrets=tuple(secrets), hints=tuple(hints), decor=tuple(decor), events=tuple(events),
        legacy_ids=legacy_ids, source=source, notes=notes,
    )
