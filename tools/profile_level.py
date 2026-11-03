"""Measure simulation and rendering cost while the route bot plays a level.

    python tools/profile_level.py first_steps --res 1920x1080 --seconds 20 [--json out.json]

Reports per-frame update time, render time, draw calls, live entities and
texture memory. Under the SDL dummy driver the *software* renderer is used,
so render times are an upper bound, not GPU numbers (see PERFORMANCE.md).
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import time
import tracemalloc

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lume.core.constants import FIXED_DT  # noqa: E402
from lume.core.game import Game  # noqa: E402
from lume.levels.campaign import load_campaign  # noqa: E402
from lume.qa import route_bot  # noqa: E402
from lume.render.display import Display  # noqa: E402
from lume.render.scene import Scene  # noqa: E402


def pct(values, q):
    if not values:
        return 0.0
    s = sorted(values)
    return s[min(len(s) - 1, int(q * (len(s) - 1)))]


def profile(level_id: str, res: tuple[int, int], seconds: float, quality: str = "high") -> dict:
    level = load_campaign().level(level_id)
    display = Display(res, hidden=True)
    scene = Scene(display, quality=quality)
    game = Game([level])
    t_pre = time.perf_counter()
    scene.prepare(game)
    scene.preload(game)
    preload_ms = (time.perf_counter() - t_pre) * 1000
    update_ms, render_ms, draws, entities, submit_ms = [], [], [], [], []
    tracemalloc.start()
    original_update = game.update
    frame_state = {"n": 0, "cursor": 0}

    def instrumented(dt, inp):
        t0 = time.perf_counter()
        original_update(dt, inp)
        t1 = time.perf_counter()
        frame_state["n"] += 1
        if frame_state["n"] % 2 == 0:  # render at 60 Hz of simulated time
            update_ms.append((t1 - t0) * 1000 * 2)
            scene.handle_events(game, game.events[frame_state["cursor"]:])
            frame_state["cursor"] = len(game.events)
            r0 = time.perf_counter()
            scene.render(game, 1 / 60)
            submit_ms.append((time.perf_counter() - r0) * 1000)
            display.present()  # SDL batches draw calls; present() executes them
            render_ms.append((time.perf_counter() - r0) * 1000)
            draws.append(scene.stats["draws"])
            entities.append(sum(1 for e in game.enemies if e.alive and e.active) + len(game.projectiles) + len(game.particles)
                            + len(scene.fx.items))

    game.update = instrumented  # type: ignore[assignment]
    route = route_bot.play_route(level, seconds, run=level_id != "blue_ascent", game=game)
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    result = {
        "level": level_id, "resolution": f"{res[0]}x{res[1]}", "renderer": "software" if display.software else "gpu",
        "frames": len(render_ms), "status": route.game.status,
        "update_ms": {"avg": round(statistics.fmean(update_ms), 3), "p95": round(pct(update_ms, 0.95), 3), "max": round(max(update_ms), 3)},
        "submit_ms": {"avg": round(statistics.fmean(submit_ms), 2), "p95": round(pct(submit_ms, 0.95), 2)},
        "frame_ms": {"avg": round(statistics.fmean(render_ms), 2), "p95": round(pct(render_ms, 0.95), 2), "max": round(max(render_ms), 2)},
        "draw_calls": {"avg": round(statistics.fmean(draws), 1), "max": max(draws)},
        "entities": {"avg": round(statistics.fmean(entities), 1), "max": max(entities)},
        "texture_mb": round(scene.store.used / 1024 / 1024, 1),
        "textures": len(scene.store.cache),
        "raster_ms_total": round(scene.store.stats["load_ms"], 1),
        "preload_ms": round(preload_ms, 1),
        "python_heap_peak_mb": round(peak / 1024 / 1024, 1),
        # 1-minute load average of the machine at the end of the run: values well above
        # the CPU count mean the frame times were inflated by other processes
        "load_avg_1m": round(os.getloadavg()[0], 2) if hasattr(os, "getloadavg") else None,
        "cpus": os.cpu_count(),
    }
    display.close()
    return result


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("level")
    ap.add_argument("--res", default="1920x1080")
    ap.add_argument("--seconds", type=float, default=20)
    ap.add_argument("--quality", default="high")
    ap.add_argument("--json")
    a = ap.parse_args()
    w, h = map(int, a.res.split("x"))
    out = profile(a.level, (w, h), a.seconds, a.quality)
    print(json.dumps(out, indent=1, ensure_ascii=False))
    if a.json:
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump(out, fh, indent=1, ensure_ascii=False)
