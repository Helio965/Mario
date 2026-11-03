"""Generate an art-QA showcase level for a world (not part of the campaign).

    python tools/art_showcase.py coral_coast /tmp/showcase_coral_coast.json
    python tools/capture_level.py /tmp/showcase_coral_coast.json out --at 300,1300,2300,3300

The level exercises every visual element a world art set must cover —
terrain (normal and ice), ledges, reward/used/brick blocks, pipe, moving,
crumbling, semisolid, spring and conveyor platforms, spikes, a swim pond,
a cave room behind a pipe, decor, checkpoint and goal — and places every
species whose ``visual_theme`` matches the world's biome, so world art and
creature rigs can be reviewed in context before real levels exist.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools" / "levelgen"))

from kit import L  # noqa: E402

AIR = {"flyer", "swooper", "floater", "cloud_rider"}
WATER = {"swimmer", "puffer"}
HANGING = {"crusher"}


def build(world_id: str) -> dict:
    campaign = json.loads((ROOT / "lume" / "data" / "campaign.json").read_text(encoding="utf-8"))
    world = next(w for w in campaign["worlds"] if w["id"] == world_id)
    species = json.loads((ROOT / "lume" / "data" / "enemies.json").read_text(encoding="utf-8"))
    species = species["species"] if isinstance(species, dict) else species
    theme = {"grassland": "grassland", "desert": "desert", "snow": "snow", "forest": "forest", "volcano": "volcano"}
    biome = world["biome"]
    mine = [s for s in species if s.get("visual_theme") == theme.get(biome, biome) and not s.get("boss")]

    l = L(id=f"showcase_{world_id}", name=f"Vitrine — {world['name']}", world=world_id, role="presentation", difficulty=1,
          art={"set": world_id, "variant": "showcase", "weather": "auto"}, music=f"{world_id}_main",
          bounds={"width": 4400, "height": 1240}, time_limit=999, spawn={"x": 72, "y": 418},
          exit={"id": "goal", "kind": "flag", "x": 4250, "y": 448})
    l.d["areas"] = [{"id": "main", "x": 0, "y": 0, "w": 4400, "h": 540, "variant": "showcase"}]
    # 0..900: ground, blocks, a floating ledge
    l.ground(0, 900)
    l.plat("question", 300, 340, 40, 28, reward="grow")
    l.plat("brick", 340, 340, 120, 22)
    l.plat("question", 460, 340, 40, 28, reward="fire")
    l.plat("ledge", 620, 250, 150, 24, style="floating")
    l.coins("arc", 640, 210, 5, 30, 30)
    l.plat("hidden", 820, 340, 40, 24, reward="star")
    # 900..1000 gap with a moving platform
    l.plat("moving", 905, 380, 90, 18, motion={"axis": "y", "range": 60, "speed": 1.0, "phase": 0})
    # 1000..1900: pipe to the cave room, semisolid, crumble, spring
    l.ground(1000, 900)
    l.cave_room(1080, 1500, 4400)
    l.plat("semisolid", 1300, 360, 140, 14)
    l.plat("crumble", 1500, 300, 100, 20)
    l.plat("spring", 1700, 432, 40, 16, bounce=900)
    l.plat("ledge", 1740, 230, 150, 24, style="floating")
    # 1900..2600: ice ground, conveyor, spikes
    l.ground(1900, 300, surface="ice")
    l.ground(2200, 400)
    l.plat("conveyor", 2240, 360, 160, 20, surface_speed=80)
    l.hazard("spikes", 2460, 432, 64, 16)
    # 2600..3000: swim pond
    l.d["zones"].append({"id": "pond", "kind": "swim", "x": 2600, "y": 470, "w": 400, "h": 150})
    l.ground(2600, 400, 620, 60, id="pond_bed")
    # 3000..4400: long ground for creatures
    l.ground(3000, 1400)
    l.d["checkpoints"].append({"id": "cp", "x": 3060, "y": 418})
    # creatures: ground walkers spread along the ground, flyers above, swimmers in the pond
    gx = [180, 560, 1120, 1380, 2280, 3200, 3420, 3640, 3860, 4060]
    ax = [700, 1600, 3300, 3700, 4000]
    wx = [2700, 2880]
    for s in mine:
        kind = s["behavior"]
        if kind in WATER and wx:
            x = wx.pop(0)
            l.enemy(s["id"], x, 560, 2620, 2980)
        elif kind in AIR and ax:
            x = ax.pop(0)
            l.enemy(s["id"], x, 300, x - 120, x + 120)
        elif kind in HANGING and ax:
            x = ax.pop(0)
            l.enemy(s["id"], x, 260, x - 40, x + 40)
        elif gx:
            x = gx.pop(0)
            l.enemy(s["id"], x, 448, x - 100, x + 100)
    return l.d


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    data = build(sys.argv[1])
    Path(sys.argv[2]).write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(sys.argv[2], len(data["enemies"]), "creatures")
