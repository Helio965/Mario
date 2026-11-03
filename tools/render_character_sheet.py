"""Render Lume in every animation state to a PNG for visual review.

    SDL_VIDEODRIVER=dummy python tools/render_character_sheet.py out.png [scale]
"""

from __future__ import annotations

import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402

from lume.core.entities import Player  # noqa: E402
from lume.render.art.lume_parts import DU_FORM, all_parts  # noqa: E402
from lume.render.assets import ArtSpec, ArtStore  # noqa: E402
from lume.render.characters.lume import LumeAnimator  # noqa: E402
from lume.render.display import Display  # noqa: E402
from lume.render.rig import RigDrawer  # noqa: E402


def main(out: str, px: float = 1080) -> None:
    states = ["idle", "walk", "run", "skid", "jump", "fall", "land", "crouch", "swim", "hurt", "dead", "win"]
    cols = 6
    display = Display((int(px * 16 / 9), int(px)), hidden=True)
    zoom = 3.0  # world units -> canvas units for the sheet
    store = ArtStore(display, display.scale * zoom)
    for part in all_parts():
        store.register(ArtSpec(part.id, (lambda p=part: p.svg), 0.40, part.pivot, "lume"))
    display.clear((52, 70, 92))
    for row, power in enumerate(("small", "fire")):
        for i, state in enumerate(states):
            anim = LumeAnimator()
            p = Player(0, 0)
            p.power = power
            p.grounded = state not in ("jump", "fall", "swim")
            p.vx = {"walk": 200, "run": 340, "skid": -150}.get(state, 0)
            p.vy = {"jump": -400, "fall": 300}.get(state, 0)
            p.land_impact = 0.16 if state == "land" else 0
            cmds, du = [], 0.36
            for _ in range(20):
                cmds, du = anim.commands(p, state, 1 / 60)
            cx = 80 + (i % cols) * 150
            cy = 150 + (i // cols) * 170
            drawer = RigDrawer(store.rig_entry, lambda x, y, cx=cx, cy=cy: (cx + x * zoom, cy + y * zoom), zoom)
            if row == 0:
                drawer.draw(display, cmds, 0, 0, du, 1)
            else:
                pass
    # second sheet half: fire palette, facing left
    for i, state in enumerate(states):
        anim = LumeAnimator()
        p = Player(0, 0)
        p.power = "fire"
        p.facing = -1
        p.grounded = state not in ("jump", "fall", "swim")
        p.vx = {"walk": -200, "run": -340, "skid": 150}.get(state, 0)
        p.vy = {"jump": -400, "fall": 300}.get(state, 0)
        p.land_impact = 0.16 if state == "land" else 0
        cmds, du = [], 0.4
        for _ in range(20):
            cmds, du = anim.commands(p, state, 1 / 60)
        cx = 80 + (i % cols) * 150
        cy = 505
        if i >= cols:
            continue
        drawer = RigDrawer(store.rig_entry, lambda x, y, cx=cx, cy=cy: (cx + x * zoom, cy + y * zoom), zoom)
        drawer.draw(display, cmds, 0, 0, du, -1)
    pygame.image.save(display.screenshot(), out)
    print("saved", out, display.pixel_size, store.stats)


if __name__ == "__main__":
    main(sys.argv[1], float(sys.argv[2]) if len(sys.argv) > 2 else 1080)
