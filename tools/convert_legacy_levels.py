"""Convert the fifteen TypeScript levels into ``lume.level`` JSON files.

Run once (idempotent) after exporting the TS data:

    node --experimental-strip-types tools/export_legacy_levels.mjs > /tmp/legacy.json
    python tools/convert_legacy_levels.py /tmp/legacy.json

Conversions (documented in docs/technical/ARQUITETURA_FASES.md):
* stable ids replace "1-1"…"5-3" (kept in ``legacy_ids`` for save migration);
* generic enemy kinds become species native to each biome, with the legacy
  hitbox and tuning;
* the floating sky chambers reached by pipes become underground cave areas
  (+720 u) with walls, floor and ceiling, keeping their inner layout;
* coin rows/arcs become ``coin_groups``.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "lume" / "data" / "levels"
ROOM_SHIFT = 720.0

LEVEL_IDS = {
    "1-1": ("first_steps", "green_kingdom", "presentation", 1, "meadow"),
    "1-2": ("valley_canals", "green_kingdom", "exploration", 1, "canals"),
    "1-3": ("orchard_guardian", "green_kingdom", "movement", 2, "orchard"),
    "2-1": ("windswept_dunes", "golden_desert", "presentation", 2, "dunes"),
    "2-2": ("canyon_bridges", "golden_desert", "exploration", 3, "canyon"),
    "2-3": ("sand_temple", "golden_desert", "movement", 3, "temple"),
    "3-1": ("crystal_lake", "frozen_peaks", "presentation", 4, "lake"),
    "3-2": ("blue_ascent", "frozen_peaks", "exploration", 4, "summit"),
    "3-3": ("blizzard_heart", "frozen_peaks", "movement", 5, "blizzard"),
    "4-1": ("glowing_canopy", "enchanted_forest", "presentation", 5, "canopy"),
    "4-2": ("firefly_ruins", "enchanted_forest", "exploration", 5, "ruins"),
    "4-3": ("ancestral_tree", "enchanted_forest", "movement", 6, "ancestral"),
    "5-1": ("basalt_bridges", "volcanic_fortress", "presentation", 7, "basalt"),
    "5-2": ("echo_furnace", "volcanic_fortress", "exploration", 7, "furnace"),
    "5-3": ("last_flame", "volcanic_fortress", "movement", 8, "citadel"),
}
SPECIES = {
    1: {"walker": "bolota", "shell": "caramujo", "flyer": "besouro_alado", "boss": "guardiao_pomar"},
    2: {"walker": "escaravelho_areia", "shell": "tatu_bola", "flyer": "abutre_filhote", "shooter": "cacto_sentinela",
        "armored": "escorpiao_couraca", "boss": "guardiao_templo"},
    3: {"walker": "pinguim_patrulha", "shell": "caracol_cristal", "flyer": "coruja_nevada", "shooter": "boneco_neve",
        "armored": "carneiro_glacial", "boss": "guardiao_nevasca"},
    4: {"walker": "cogumelo_saltitante", "shell": "caracol_musgo", "flyer": "mariposa_lume", "shooter": "planta_esporos",
        "armored": "besouro_casca", "boss": "guardiao_arvore"},
    5: {"walker": "brasa_andante", "shell": "tartaruga_basalto", "flyer": "morcego_brasa", "shooter": "boca_fornalha",
        "armored": "golem_basalto", "boss": "guardiao_chama"},
}


def group_coins(coins: list[dict]) -> tuple[list[dict], list[dict]]:
    """Recover row/arc groups from consecutive legacy coins."""
    groups, loose = [], []
    i = 0
    n = 0
    while i < len(coins):
        best = None
        for count in range(min(12, len(coins) - i), 1, -1):
            chunk = coins[i : i + count]
            dx = chunk[1]["x"] - chunk[0]["x"]
            if dx <= 0 or any(abs((chunk[k + 1]["x"] - chunk[k]["x"]) - dx) > 1e-6 for k in range(count - 1)):
                continue
            if all(abs(c["y"] - chunk[0]["y"]) < 1e-6 for c in chunk):
                best = {"shape": "row", "x": chunk[0]["x"], "y": chunk[0]["y"], "count": count, "spacing": dx}
                break
            base = chunk[0]["y"]
            if abs(chunk[-1]["y"] - base) < 1e-6 and count >= 3:
                ok = all(
                    abs(c["y"] - (base - math.sin(math.pi * k / (count - 1)) * 32)) < 1e-6 for k, c in enumerate(chunk)
                )
                if ok:
                    best = {"shape": "arc", "x": chunk[0]["x"], "y": base, "count": count, "spacing": dx}
                    break
        if best:
            n += 1
            groups.append({"id": f"coins{n:02d}", **best})
            i += best["count"]
        else:
            loose.append(coins[i])
            i += 1
    return groups, loose


def r(v: float) -> float | int:
    return int(v) if float(v).is_integer() else round(v, 3)


def convert(level: dict) -> dict:
    new_id, world_id, role, difficulty, variant = LEVEL_IDS[level["id"]]
    legacy_world = level["world"]
    room_pipe = next(p for p in level["platforms"] if p["kind"] == "pipe" and p.get("destination", {}).get("y") == 126)
    room_x = room_pipe["destination"]["x"] - 24
    in_room = lambda x, y: room_x - 2 <= x <= room_x + 300 and y < 200  # noqa: E731
    platforms, counter = [], {}

    def pid(kind: str) -> str:
        counter[kind] = counter.get(kind, 0) + 1
        return f"{kind}{counter[kind]:02d}"

    for p in level["platforms"]:
        kind, x, y, w, h = p["kind"], p["x"], p["y"], p["w"], p["h"]
        if kind == "brick" and y == 176 and w == 298:
            continue  # replaced by the cave floor below
        terrain = abs((y + h) - 600) < 1e-6
        spec: dict = {}
        if kind == "ground" or (kind == "ice" and terrain):
            spec = {"id": pid("ground"), "kind": "ground", "style": "terrain"}
            if kind == "ice":
                spec["surface"] = "ice"
        elif kind == "ice":
            spec = {"id": pid("ledge"), "kind": "ledge", "style": "ice_ledge", "surface": "ice"}
        elif kind == "pipe" and p.get("destination") and in_room(p["x"], p["y"]):
            spec = {"id": "pipe_room_exit", "kind": "pipe", "style": "pipe",
                    "warp": {"x": r(p["destination"]["x"]), "y": r(p["destination"]["y"])},
                    "return": {"x": r(p["returnPoint"]["x"]), "y": r(p["returnPoint"]["y"] + ROOM_SHIFT)}}
            y += ROOM_SHIFT
        elif kind == "pipe" and p.get("destination"):
            spec = {"id": "pipe_room_entry", "kind": "pipe", "style": "pipe", "secret": "pipe_room",
                    "warp": {"x": r(p["destination"]["x"]), "y": r(p["destination"]["y"] + ROOM_SHIFT)},
                    "return": {"x": r(p["returnPoint"]["x"]), "y": r(p["returnPoint"]["y"])}}
        else:
            spec = {"id": pid(kind), "kind": kind}
            if kind == "pipe":
                spec["style"] = "pipe"
        spec.update({"x": r(x), "y": r(y), "w": r(w), "h": r(h)})
        if p.get("reward"):
            spec["reward"] = p["reward"]
        if p.get("motion"):
            m = p["motion"]
            spec["motion"] = {"axis": m["axis"], "range": r(m["range"]), "speed": r(m["speed"]), "phase": r(m.get("phase", 0))}
        if kind == "hidden":
            spec["secret"] = f"hidden_{spec['id']}"
        platforms.append(spec)

    # Cave chamber around the relocated room (legacy floor y176 → y896).
    area_x = max(0.0, min(level["width"] - 960.0, room_x + 149 - 480))
    floor_y, top = 176 + ROOM_SHIFT, 700.0
    platforms += [
        {"id": "cave_floor", "kind": "ground", "style": "cave", "x": r(area_x), "y": r(floor_y), "w": 960, "h": r(1240 - floor_y)},
        {"id": "cave_ceiling", "kind": "ground", "style": "cave", "x": r(area_x), "y": r(top), "w": 960, "h": 60},
        {"id": "cave_wall_left", "kind": "ground", "style": "cave", "x": r(area_x), "y": 760, "w": r(room_x - 40 - area_x), "h": r(floor_y - 760)},
        {"id": "cave_wall_right", "kind": "ground", "style": "cave", "x": r(room_x + 338), "y": 760,
         "w": r(area_x + 960 - (room_x + 338)), "h": r(floor_y - 760)},
    ]

    coins = [c for c in level["coins"] if not c.get("special")]
    main_coins = [c for c in coins if not in_room(c["x"], c["y"])]
    room_coins = [dict(c, y=c["y"] + ROOM_SHIFT) for c in coins if in_room(c["x"], c["y"])]
    groups, loose = group_coins(main_coins)
    room_groups, room_loose = group_coins(room_coins)
    for g in room_groups:
        g["id"] = "room_" + g["id"]
    collectibles = []
    for c in level["coins"]:
        if not c.get("special"):
            continue
        if in_room(c["x"], c["y"]):
            collectibles.append({"id": "relic_room", "kind": "relic", "x": r(c["x"]), "y": r(c["y"] + ROOM_SHIFT)})
        else:
            collectibles.append({"id": "relic_high", "kind": "relic", "x": r(c["x"]), "y": r(c["y"])})
    items = []
    for n, it in enumerate(level["items"], 1):
        y = it["y"] + (ROOM_SHIFT if in_room(it["x"], it["y"]) else 0)
        items.append({"id": f"item{n:02d}_{it['kind']}", "kind": it["kind"], "x": r(it["x"]), "y": r(y)})
    enemies = []
    for n, e in enumerate(level["enemies"], 1):
        species = SPECIES[legacy_world][e["kind"]]
        spec = {"id": f"enemy{n:02d}", "species": species, "x": r(e["x"]), "y": r(e["y"] + e["h"]),
                "patrol": [r(e["patrol"][0]), r(e["patrol"][1])]}
        if e.get("hp"):
            spec["hp"] = e["hp"]
        enemies.append(spec)
    hazards = []
    for n, h in enumerate(level["hazards"], 1):
        spec = {"id": f"hz_{h['kind']}{n:02d}", "kind": h["kind"], "x": r(h["x"]), "y": r(h["y"]), "w": r(h["w"]), "h": r(h["h"])}
        if h["kind"] == "moving":
            spec.update({"range": r(h.get("range", 30)), "speed": r(h.get("speed", 1))})
        hazards.append(spec)
    secrets = [{"id": "pipe_room", "kind": "warp_room", "entry": "pipe_room_entry",
                "clue": "Cano com seta luminosa e dica próxima", "rewards": ["relic_room"]}]
    for p in platforms:
        if p["kind"] == "hidden":
            secrets.append({"id": p["secret"], "kind": "hidden_block", "entry": p["id"],
                            "clue": "Moedas e luzes convergem para um ponto vazio no ar", "rewards": []})
    if any(c["id"] == "relic_high" for c in collectibles):
        secrets.append({"id": "high_route", "kind": "high_route", "clue": "Trilha de moedas sobe pelos blocos",
                        "rewards": ["relic_high"]})
    music = f"{world_id}_main"
    data = {
        "format": "lume.level",
        "format_version": 1,
        "id": new_id,
        "legacy_ids": [level["id"]],
        "name": level["name"],
        "world": world_id,
        "role": role,
        "difficulty": difficulty,
        "art": {"set": world_id, "variant": variant, "weather": "auto"},
        "music": music,
        "bounds": {"width": r(level["width"]), "height": 1240},
        "areas": [
            {"id": "main", "x": 0, "y": 0, "w": r(level["width"]), "h": 540, "variant": variant},
            {"id": "pipe_room_area", "x": r(area_x), "y": 700, "w": 960, "h": 540, "variant": "cave"},
        ],
        "time_limit": r(level["time"]),
        "spawn": {"x": r(level["spawn"]["x"]), "y": r(level["spawn"]["y"])},
        "checkpoints": [{"id": "cp_mid", "x": r(level["checkpoint"]["x"]), "y": r(level["checkpoint"]["y"])}],
        "exit": {"id": "goal", "kind": "flag", "x": r(level["exit"]["x"]), "y": r(level["exit"]["y"])},
        "platforms": platforms,
        "coin_groups": groups + room_groups,
        "coins": [{"id": f"coin_loose{n:02d}", "x": r(c["x"]), "y": r(c["y"])} for n, c in enumerate(loose + room_loose, 1)],
        "collectibles": collectibles,
        "items": items,
        "enemies": enemies,
        "hazards": hazards,
        "secrets": secrets,
        "hints": [{"x": r(h["x"]), "text": h["text"]} for h in level["hints"]],
        "notes": f"Convertida da edição TypeScript (fase {level['id']}). Sala secreta movida para câmara subterrânea (+{int(ROOM_SHIFT)} u).",
    }
    return data


def main(path: str) -> None:
    exported = json.loads(Path(path).read_text(encoding="utf-8"))
    for level in exported["levels"]:
        data = convert(level)
        target = OUT / data["world"] / f"{data['id']}.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"{level['id']} → {target.relative_to(ROOT)}")


if __name__ == "__main__":
    main(sys.argv[1])
