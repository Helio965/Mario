"""Render gameplay frames of a level to PNG files (graphics QA).

    python tools/capture_level.py first_steps out_dir --res 1920x1080 --at 0,900,2200 [--play 6]

Frames are produced by the real renderer (SDL software renderer under the
dummy video driver when no display is available).
"""

from __future__ import annotations

import argparse
import os
import sys
import time

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402

from lume.core.constants import FIXED_DT  # noqa: E402
from lume.core.game import Game  # noqa: E402
from lume.core.input import InputState  # noqa: E402
from lume.levels.campaign import load_campaign  # noqa: E402
from lume.render.display import Display  # noqa: E402
from lume.render.scene import Scene  # noqa: E402


def capture(level_id: str, out_dir: str, res: tuple[int, int], xs: list[float], play: float = 0.0, quality: str = "high") -> list[str]:
    campaign = load_campaign()
    level = campaign.level(level_id)
    os.makedirs(out_dir, exist_ok=True)
    display = Display(res, hidden=True)
    scene = Scene(display, quality=quality)
    files = []
    for x in xs:
        game = Game([level])
        # place the player on the ground near x by walking the camera there
        p = game.player
        p.x = x
        floor = None
        for s in game.index.query(x - 1, x + 1):
            if s.kind in ("ground", "ledge") and s.x <= x + 11 < s.x + s.w and s.y < 540:
                floor = s.y if floor is None else min(floor, s.y)
        if floor is not None:
            p.y = floor - p.h
        game.camera.snap(game)
        for e in game.enemies:
            e.active = True
        steps = int(max(play, 0.6) * 120)
        start = time.perf_counter()
        for i in range(steps):
            game.update(FIXED_DT, InputState(right=play > 0 and i > 30, run=True))
            if i % 2 == 0:
                scene.handle_events(game, game.events[-6:] if i % 30 == 0 else [])
        scene.render(game, 1 / 60)
        name = os.path.join(out_dir, f"{level_id}_{int(x)}_{res[0]}x{res[1]}.png")
        pygame.image.save(display.screenshot(), name)
        files.append(name)
        print(f"{name} draws={scene.stats['draws']} store={scene.store.stats} {time.perf_counter() - start:.2f}s")
    return files


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("level")
    ap.add_argument("out")
    ap.add_argument("--res", default="1920x1080")
    ap.add_argument("--at", default="72")
    ap.add_argument("--play", type=float, default=0.0)
    ap.add_argument("--quality", default="high")
    a = ap.parse_args()
    w, h = map(int, a.res.split("x"))
    capture(a.level, a.out, (w, h), [float(v) for v in a.at.split(",")], a.play, a.quality)
