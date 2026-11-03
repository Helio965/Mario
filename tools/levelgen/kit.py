"""Level authoring kit: small builders that emit ``lume.level`` v1 JSON.

The JSON files under ``lume/data/levels/<world>/`` are the source of truth
(the game, the validator and the tests read only them).  The world scripts in
this folder document how the *new* levels were authored and regenerate them
byte for byte::

    python tools/levelgen/world02_golden_desert.py
    LUME_LEVELGEN_OUT=/tmp/out python tools/levelgen/world02_golden_desert.py   # dry run

Reino Verde (1-4..1-6) was authored with this same kit and then hand-tuned
directly in its JSON files, so it has no regeneration script here; edit its
JSON directly.

After regenerating, always run ``python -m lume --validate`` and the pytest
suite (which plays every level with the route bot): geometry changes must
keep every level completable.
"""

from __future__ import annotations

import json
import os
import pathlib

REPO = pathlib.Path(__file__).resolve().parents[2]
OUT_ROOT = pathlib.Path(os.environ.get("LUME_LEVELGEN_OUT") or REPO / "lume" / "data" / "levels")


def save(data: dict) -> pathlib.Path:
    """Write a level to ``<OUT_ROOT>/<world>/<id>.json`` (stable formatting)."""
    folder = OUT_ROOT / data["world"]
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{data['id']}.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return path


class L:
    """Builder for one level; ``L.d`` is the JSON document being written."""

    def __init__(self, **kw):
        self.d = {"format": "lume.level", "format_version": 1, **kw, "platforms": [], "coin_groups": [], "coins": [],
                  "collectibles": [], "items": [], "enemies": [], "hazards": [], "zones": [], "secrets": [], "hints": [],
                  "events": [], "checkpoints": []}
        self.n: dict[str, int] = {}

    def nid(self, k):
        self.n[k] = self.n.get(k, 0) + 1
        return f"{k}{self.n[k]:02d}"

    def ground(self, x, w, y=448, h=None, style="terrain", **kw):
        p = {"id": kw.pop("id", None) or self.nid("ground"), "kind": "ground", "style": style, "x": x, "y": y, "w": w, "h": h if h is not None else 600 - y}
        p.update(kw)
        self.d["platforms"].append(p)
        return p

    def plat(self, kind, x, y, w, h, **kw):
        p = {"id": kw.pop("id", None) or self.nid(kind), "kind": kind, "x": x, "y": y, "w": w, "h": h}
        p.update(kw)
        self.d["platforms"].append(p)
        return p

    def coins(self, shape, x, y, count, spacing=None, rise=None):
        g = {"id": self.nid("coins"), "shape": shape, "x": x, "y": y, "count": count}
        if spacing:
            g["spacing"] = spacing
        if rise is not None:
            g["rise"] = rise
        self.d["coin_groups"].append(g)

    def relic(self, id, x, y):
        self.d["collectibles"].append({"id": id, "kind": "relic", "x": x, "y": y})

    def enemy(self, species, x, y, left, right, **kw):
        e = {"id": self.nid("enemy"), "species": species, "x": x, "y": y, "patrol": [left, right]}
        e.update(kw)
        self.d["enemies"].append(e)

    def hazard(self, kind, x, y, w, h, **kw):
        hz = {"id": self.nid("hz_" + kind), "kind": kind, "x": x, "y": y, "w": w, "h": h}
        hz.update(kw)
        self.d["hazards"].append(hz)

    def water(self, x, w, y=468):
        self.hazard("water", x, y, w, 540 - y + 60)

    def item(self, kind, x, y):
        self.d["items"].append({"id": self.nid("item_" + kind), "kind": kind, "x": x, "y": y})

    def hint(self, x, text):
        self.d["hints"].append({"x": x, "text": text})

    def secret(self, id, kind, clue, rewards=(), entry=None):
        s = {"id": id, "kind": kind, "clue": clue, "rewards": list(rewards)}
        if entry:
            s["entry"] = entry
        self.d["secrets"].append(s)

    def cave_room(self, entry_x, room_x, width, reward_item="heart", relic_id="relic_room", variant="cave"):
        """Pipe on the main ground → underground chamber (+720 u) → pipe back."""
        back = {"x": entry_x + 72, "y": 402}
        self.plat("pipe", entry_x, 400, 56, 48, id="pipe_room_entry", style="pipe", secret="pipe_room",
                  warp={"x": room_x + 24, "y": 846}, **{"return": back})
        area_x = max(0, min(width - 960, room_x + 149 - 480))
        self.d.setdefault("areas", [])
        self.d["areas"].append({"id": "pipe_room_area", "x": area_x, "y": 700, "w": 960, "h": 540, "variant": variant})
        self.ground(area_x, 960, 896, 344, style="cave", id="cave_floor")
        self.ground(area_x, 960, 700, 60, style="cave", id="cave_ceiling")
        self.ground(area_x, room_x - 40 - area_x, 760, 136, style="cave", id="cave_wall_left")
        self.ground(room_x + 338, area_x + 960 - (room_x + 338), 760, 136, style="cave", id="cave_wall_right")
        self.plat("pipe", room_x + 226, 864, 56, 32, id="pipe_room_exit", style="pipe", warp=back, **{"return": {"x": room_x + 24, "y": 846}})
        self.coins("row", room_x + 64, 852, 4, 34)
        self.relic(relic_id, room_x + 178, 850)
        self.item(reward_item, room_x + 128, 866)
        self.secret("pipe_room", "warp_room", "Cano com seta luminosa", [relic_id], "pipe_room_entry")


# ----------------------------------------------------------------------------- zone helpers
def wind(l: L, x, w, force, period=0.0, duty=1.0, y=0, h=540):
    """Horizontal wind (force_x is a drift velocity in u/s); optional gusts."""
    z = {"id": l.nid("wind"), "kind": "wind", "x": x, "y": y, "w": w, "h": h, "force_x": force}
    if period:
        z.update(period=period, duty=duty)
    l.d["zones"].append(z)


def quicksand(l: L, x, w, top=448, floor=520):
    """Quicksand pit: sinking zone over a solid sand bed (escape by hopping)."""
    l.d["zones"].append({"id": l.nid("quicksand"), "kind": "quicksand", "x": x, "y": top, "w": w, "h": floor - top})
    l.ground(x, w, floor, 80, style="terrain", id=l.nid("sandbed"))
