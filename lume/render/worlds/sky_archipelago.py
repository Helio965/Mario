"""Arquipélago Celeste: floating islands high above a sea of clouds.

Identity: a bright, windy afternoon. The sun stands in the upper left (all
light comes from there), a deep cerulean sky fades into a warm haze over a
sea of clouds far below, and towering cumulus rise on the horizon. Islands
are pale sandstone and white rock under a lush grassy cap with wildflowers;
their undersides cool into lavender shade, faintly lit from below by the
clouds, with dangling roots and small sky crystals. Kites, rope bridges,
wind chimes, sail-cloth banners and hot-air balloons carry the wind theme;
the wind always blows from the left.

Readability rules of this set: walkable cloud (style ``cloud``) is dense,
bright cumulus with a defined lavender top line, while the cloud sea seen
through pits is hazier, softer and lower, so a pit always reads as a drop.
Slippery floors (``surface == "ice"``) are slick wet rock with a cold blue
gloss (rule R5: blue gloss = slides). Every pattern that crosses chunk
borders is a function of the world x and only hanging edges are outlined.
"""

from __future__ import annotations

import math
from typing import Callable, Sequence

from ..svg import Rand, Svg, blob, mix, rounded_rect_path, shade, smooth_closed, smooth_open, star_points
from .base import Layer, PropSpec, Weather, WorldArt

Pt = tuple[float, float]
Puff = tuple[float, float, float]  # centre x, centre y, radius

INK = "#2b1d2c"
SUN = (190.0, 112.0)
# sky and clouds (lavender shadows, warm lit tops)
CLOUD_HI, CLOUD, CLOUD_SHADE, CLOUD_DEEP, CLOUD_LINE = "#ffffff", "#f3f5fc", "#d6dcf1", "#b6bde2", "#8c90c4"
CLOUD_WARM = "#fffaf0"
SEA_TOP, SEA, SEA_LOW = "#f7f3fb", "#e2def1", "#cdc8e6"  # body of the cloud sea (sky bottom and pit layers)
# island rock: pale sandstone that cools to lavender in its own shade
ROCK_HI, ROCK_TOP, ROCK, ROCK_MID, ROCK_LOW, ROCK_UNDER, ROCK_LINE = (
    "#fffbf2", "#f5ead8", "#e8d6bc", "#d4bfa3", "#b6a7c0", "#8e87b4", "#5e4c64")
GRASS_TOP, GRASS, GRASS_DARK, GRASS_LINE, GRASS_LIGHT = "#c2f272", "#7acd58", "#3f9a4e", "#265c38", "#e9fcb4"
CRYSTAL_HI, CRYSTAL, CRYSTAL_LILAC, CRYSTAL_LINE = "#f0fdff", "#7fdcff", "#c6a8ff", "#1f5a8c"
ROOT, ROOT_DARK = "#9c7552", "#5a3f2e"
WOOD_LIGHT, WOOD, WOOD_DARK = "#e2b67f", "#ad7a46", "#6c4527"
BRONZE_HI, BRONZE, BRONZE_DEEP, BRONZE_LINE = "#ffe7ad", "#dca14b", "#94592a", "#5a3218"
SAIL, SAIL_SHADE, SAIL_BLUE, SAIL_BLUE_DEEP, CORAL = "#fffaf0", "#dcd5e6", "#4b93dc", "#2b62a8", "#ff8a6a"
WICKER_HI, WICKER, WICKER_DEEP = "#ffe6a6", "#e3aa5a", "#9a6430"
WET_HI, WET_TOP, WET, WET_DEEP, WET_LINE = "#f2fdff", "#a6e0f5", "#58a9d4", "#2f6f9e", "#1b4a72"
STONE_HI, STONE, STONE_DARK, MORTAR = "#fffdf8", "#ece4d8", "#c4b7aa", "#a79cb4"
TILE, TILE_DEEP = "#4f9be0", "#2a63a8"
FLOWERS = ("#ffffff", "#a8d8ff", "#ffe57a", "#ffd2e6", "#ffffff")
HANG = 34.0  # island art below the collision box: underside lobes, roots and crystals


# --------------------------------------------------------------------------- helpers
def _hash(n: int, salt: int = 0) -> float:
    """Stable pseudo-random value in [0, 1] for an integer lattice cell."""
    x = (n * 374761393 + salt * 668265263 + 1013904223) & 0xFFFFFFFF
    x = ((x ^ (x >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((x ^ (x >> 16)) & 0xFFFFFF) / float(0xFFFFFF)


def _wobble(gx: float, k: float) -> float:
    return math.sin(gx * 0.071 + k) * 0.6 + math.sin(gx * 0.023 + 2 * k) * 0.4


def _line(pts: Sequence[Pt]) -> str:
    return "M" + "L".join(f"{x:.2f} {y:.2f}" for x, y in pts)


def _poly(pts: Sequence[Pt]) -> str:
    return _line(pts) + "Z"


def _samples(w: float, step: float = 2.0) -> list[float]:
    n = max(2, int(math.ceil(w / step)))
    return [w * i / n for i in range(n + 1)]


def _grid(x0: float, w: float, cell: float) -> list[float]:
    """Local x of the edges and centres of world-aligned cells inside [0, w] (plus both ends)."""
    out = {0.0, w}
    n = math.floor(x0 / cell)
    while n * cell - x0 < w:
        for f in (0.0, 0.5):
            lx = (n + f) * cell - x0
            if 0.0 < lx < w:
                out.add(lx)
        n += 1
    return sorted(out)


def _runs(xs: Sequence[float], keep: Callable[[float], bool]) -> list[list[float]]:
    """Consecutive runs of sample positions where ``keep(x)`` holds."""
    runs: list[list[float]] = []
    cur: list[float] = []
    for x in xs:
        if keep(x):
            cur.append(x)
        elif cur:
            runs.append(cur)
            cur = []
    if cur:
        runs.append(cur)
    return [run for run in runs if len(run) > 1]


def _glow(s: Svg, x: float, y: float, r: float, color: str, alpha: float) -> None:
    s.circle(x, y, r, fill=s.radial(x, y, r, [(0, color, alpha), (0.45, color, alpha * 0.45), (1, color, 0)]))


def _sparkle(s: Svg, x: float, y: float, size: float, opacity: float = 0.95, color: str = "#ffffff") -> None:
    s.polygon(star_points(x, y, size, size * 0.24, 4), fill=color, opacity=opacity)


def _crystal(s: Svg, x: float, y: float, angle: float, length: float, width: float, tone: str = CRYSTAL,
             opacity: float = 1.0) -> None:
    """Prism growing from (x, y) toward ``angle`` (degrees, -90 = up): the
    face toward the upper-left light is pale, the other deep, plus a glint."""
    a = math.radians(angle)
    ux, uy = math.cos(a), math.sin(a)
    nx, ny = -uy * width / 2, ux * width / 2
    if nx < 0 or (nx == 0 and ny < 0):  # make (x - nx, y - ny) the lit (left/up) side
        nx, ny = -nx, -ny
    shoulder = max(0.0, length - width * 0.8)
    sx, sy = x + ux * shoulder, y + uy * shoulder
    tx, ty = x + ux * length, y + uy * length
    body = [(x + nx, y + ny), (sx + nx, sy + ny), (tx, ty), (sx - nx, sy - ny), (x - nx, y - ny)]
    s.polygon(body, fill=s.linear(x - nx, y - ny, x + nx, y + ny, [(0, CRYSTAL_HI), (0.45, tone), (1, shade(tone, -0.42))]),
              stroke=CRYSTAL_LINE, width=0.6, opacity=opacity)
    s.polygon([(x - nx * 0.1, y - ny * 0.1), (sx - nx * 0.1, sy - ny * 0.1), (tx, ty), (sx - nx * 0.7, sy - ny * 0.7),
               (x - nx * 0.7, y - ny * 0.7)], fill="#ffffff", opacity=0.42 * opacity)


def _cluster(s: Svg, x: float, y: float, size: float, seed: int, tone: str = CRYSTAL, hanging: bool = False,
             glow: float = 0.4) -> None:
    """Small crystal cluster rooted at (x, y), growing up (or hanging down)."""
    r = Rand(seed)
    sign = 1 if hanging else -1
    if glow > 0:
        _glow(s, x, y + sign * size * 0.45, size * 1.25, tone, glow)
    if seed % 3:
        shapes = ((-30, 0.62, 0.42), (26, 0.7, 0.42), (0, 1.0, 0.52))[: 2 + seed % 2]
    else:
        shapes = ((-34, 0.55, 0.4), (22, 0.74, 0.44), (-8, 0.95, 0.5))
    for da, lk, wk in shapes:
        _crystal(s, x + da * size * 0.012, y, sign * 90 + da + r.uniform(-6, 6), size * lk, size * wk, tone)


def _dangle(s: Svg, x: float, y: float, length: float, seed: int, width: float = 1.4, color: str = ROOT,
            dark: str = ROOT_DARK) -> None:
    """Root hanging from (x, y): swaying, thicker near the top, one rootlet."""
    r = Rand(seed)
    n = max(3, int(length / 5))
    pts = [(x, y)]
    for k in range(1, n + 1):
        t = k / n
        pts.append((x + math.sin(t * 2.4 + seed * 0.7) * 2.4 * t + r.uniform(-0.6, 0.6), y + length * t))
    s.path(smooth_open(pts), stroke=dark, width=width + 0.8, opacity=0.85)
    s.path(smooth_open(pts), stroke=color, width=width)
    s.path(smooth_open(pts[: n // 2 + 1]), stroke=color, width=width + 0.9)
    bx, by = pts[n // 2]
    side = 1 if seed % 2 else -1
    s.path(f"M{bx:.2f} {by:.2f} Q{bx + side * 3:.2f} {by + 2:.2f} {bx + side * 4.5:.2f} {by + length * 0.28:.2f}", stroke=color,
           width=max(0.6, width * 0.55))


def _puffs(s: Svg, puffs: Sequence[Puff], *, lit: str = CLOUD_WARM, mid: str = CLOUD, low: str = CLOUD_SHADE, deep: str = CLOUD_DEEP,
           shadow: str = "#a3b0d6", shadow_alpha: float = 0.3, glow: float = 0.75, creases: float = 0.3) -> None:
    """Soft cumulus from overlapping puffs: one shared light-to-shade fill so
    the puffs merge into a single body, a soft shadow to the lower right, a
    glow on the lit side of each upper puff and faint creases where puffs
    overlap. Puffs are opaque (overlaps of translucent circles would show)."""
    if not puffs:
        return
    top = min(cy - rad for _cx, cy, rad in puffs)
    bottom = max(cy + rad for _cx, cy, rad in puffs)
    if shadow_alpha > 0:
        for cx, cy, rad in puffs:
            s.circle(cx + rad * 0.07, cy + rad * 0.09, rad, fill=shadow, opacity=shadow_alpha)
    body = s.linear(0, top, 0, bottom, [(0, lit), (0.4, mid), (0.78, low), (1, deep)])
    for cx, cy, rad in puffs:
        s.circle(cx, cy, rad, fill=body)
    if creases > 0:
        for cx, cy, rad in puffs:
            if cy + rad * 0.6 < bottom - 1:
                rr = rad * 0.93
                a0, a1 = math.radians(30), math.radians(150)
                s.path(f"M{cx + math.cos(a0) * rr:.1f} {cy + math.sin(a0) * rr:.1f} A{rr:.1f} {rr:.1f} 0 0 1 "
                       f"{cx + math.cos(a1) * rr:.1f} {cy + math.sin(a1) * rr:.1f}", stroke=low, width=max(0.6, rad * 0.09), opacity=creases)
    if glow > 0:
        limit = top + (bottom - top) * 0.62
        for cx, cy, rad in puffs:
            if cy - rad < limit:
                gx, gy = cx - rad * 0.3, cy - rad * 0.34
                s.circle(gx, gy, rad * 0.72, fill=s.radial(gx, gy, rad * 0.72, [(0, CLOUD_HI, glow), (0.6, CLOUD_HI, glow * 0.35), (1, CLOUD_HI, 0)]))


def _cloud_outline(puffs: Sequence[Puff], x0: float, x1: float, base: float, step: float = 3.0) -> list[Pt]:
    """Upper envelope of a row of puffs between x0 and x1 (single path, for
    semi-transparent cloud bodies where overlapping circles would show)."""
    pts = []
    n = max(2, int((x1 - x0) / step))
    for i in range(n + 1):
        x = x0 + (x1 - x0) * i / n
        y = base
        for cx, cy, rad in puffs:
            dx = x - cx
            if abs(dx) < rad:
                y = min(y, cy - math.sqrt(rad * rad - dx * dx))
        pts.append((x, y))
    return pts


# --------------------------------------------------------------------------- background set pieces
def _float_island(s: Svg, cx: float, top: float, wd: float, depth: float, pal: dict[str, str], seed: int, *,
                  roots: int = 5, fall: float = 0.0, crystals: int = 0) -> None:
    """Floating island for the parallax layers: domed grassy cap, pale rock
    lit from the left and a jagged underside tapering to a point (no ink)."""
    r = Rand(seed)
    xl, xr = cx - wd / 2, cx + wd / 2
    cap = max(2.5, wd * 0.045)
    n = max(6, int(wd / 9))
    rim = [(xl + wd * i / n, top - math.sin(math.pi * i / n) * wd * 0.035 + r.uniform(-0.5, 0.5)) for i in range(n + 1)]
    tip = cx + r.uniform(-0.12, 0.12) * wd
    under = []
    m = max(8, int(wd / 6))
    for i in range(1, m):
        x = xr - wd * i / m
        reach = wd * 0.5 + abs(tip - cx)
        k = max(0.0, 1 - abs(x - tip) / reach)
        y = top + cap + (depth - cap) * k ** 1.5 + r.uniform(-1, 1) * depth * 0.035
        if i % 3 == 1:
            y += r.uniform(0.0, depth * 0.1) * k
        under.append((x, y))
    body = rim + [(xr - 1, top + cap * 1.8)] + under + [(xl + 1, top + cap * 1.8)]
    s.path(_poly(body), fill=s.linear(0, top, 0, top + depth, [(0, pal["rock_top"]), (0.3, pal["rock"]), (1, pal["under"])]))
    # light from the left, shade on the right, bounce light from the clouds below
    s.path(_poly(body), fill=s.linear(xl, 0, xr, 0, [(0, pal["light"], 0.35), (0.45, pal["light"], 0), (0.62, pal["dark"], 0),
                                                     (1, pal["dark"], 0.38)]))
    s.path(_line(under), stroke=pal["bounce"], width=max(1.0, wd * 0.012), opacity=0.55)
    for k in range(2):
        yy = top + cap + (depth - cap) * (0.2 + 0.18 * k)
        pts = [(x, yy + 1.5 * math.sin(x * 0.09 + k)) for x in _samples(wd * 0.7, 6.0)]
        s.path(_line([(cx - wd * 0.35 + x, y) for x, y in pts]), stroke=pal["dark"], width=1.0, opacity=0.18)
    for _ in range(crystals):
        px = r.uniform(xl + wd * 0.25, xr - wd * 0.25)
        k = max(0.0, 1 - abs(px - tip) / (wd * 0.5))
        _crystal(s, px, top + cap + (depth - cap) * k ** 1.5 * 0.85, 90 + r.uniform(-12, 12), depth * 0.12 + 3, max(1.6, wd * 0.022),
                 pal.get("crystal", CRYSTAL), 0.85)
    for _ in range(roots):
        i = int(r.uniform(1, len(under) - 1))
        ux, uy = under[i]
        _dangle(s, ux, uy - 1, r.uniform(depth * 0.15, depth * 0.45), seed * 7 + i, max(0.7, wd * 0.007), pal["root"], pal["root"])
    # grassy cap with a scalloped lip and a light rim
    lip = [(x, y + cap + 1.6 * abs(math.sin(x * 0.35 + seed))) for x, y in reversed(rim)]
    s.path(_poly(rim + lip), fill=s.linear(0, top - wd * 0.035, 0, top + cap + 2, [(0, pal["grass_hi"]), (1, pal["grass"])]))
    s.path(_line([(x, y + 0.6) for x, y in rim]), stroke=pal["grass_hi"], width=max(0.8, wd * 0.01), opacity=0.9)
    if fall > 0:
        _waterfall(s, xr - wd * 0.08, top + cap * 0.6, fall, max(2.0, wd * 0.03))


def _waterfall(s: Svg, x: float, y: float, length: float, wd: float) -> None:
    """Thin stream spilling off an island edge and dissolving into mist."""
    d = (f"M{x - wd / 2:.1f} {y:.1f} Q{x + wd * 1.4:.1f} {y + length * 0.15:.1f} {x + wd * 1.2:.1f} {y + length:.1f} "
         f"L{x + wd * 2.4:.1f} {y + length:.1f} Q{x + wd * 2.4:.1f} {y + length * 0.15:.1f} {x + wd / 2:.1f} {y:.1f} Z")
    s.path(d, fill=s.linear(0, y, 0, y + length, [(0, "#ffffff", 0.95), (0.55, "#e6f6ff", 0.6), (1, "#e6f6ff", 0)]))
    s.path(f"M{x:.1f} {y + 1:.1f} Q{x + wd * 1.6:.1f} {y + length * 0.15:.1f} {x + wd * 1.7:.1f} {y + length * 0.7:.1f}", stroke="#ffffff",
           width=max(0.6, wd * 0.3), opacity=0.8)
    _glow(s, x + wd * 1.8, y + length * 0.8, wd * 4, "#ffffff", 0.25)


def _balloon(s: Svg, x: float, y: float, size: float, colors: tuple[str, str], seed: int) -> None:
    """Hot-air balloon (no lettering): striped envelope lit from the left,
    a stitched crown band, ropes and a wicker basket."""
    r = Rand(seed)
    top, mouth = y - size * 0.55, y + size * 0.62
    rad = size * 0.5
    env = (f"M{x - size * 0.13:.1f} {mouth:.1f} C{x - size * 0.42:.1f} {y + size * 0.3:.1f} {x - rad * 1.05:.1f} {y:.1f} "
           f"{x - rad:.1f} {y - size * 0.06:.1f} C{x - rad * 0.95:.1f} {top - size * 0.02:.1f} {x + rad * 0.95:.1f} {top - size * 0.02:.1f} "
           f"{x + rad:.1f} {y - size * 0.06:.1f} C{x + rad * 1.05:.1f} {y:.1f} {x + size * 0.42:.1f} {y + size * 0.3:.1f} "
           f"{x + size * 0.13:.1f} {mouth:.1f} Z")
    a, b = colors
    s.path(env, fill=a)
    for k in (-2, 0, 2):  # coloured gores
        f0, f1 = (k - 0.5) / 5, (k + 0.5) / 5
        d = (f"M{x + size * 0.13 * f0 * 2:.1f} {mouth:.1f} C{x + rad * f0 * 2.2:.1f} {y + size * 0.3:.1f} {x + rad * f0 * 2.1:.1f} {y:.1f} "
             f"{x + rad * f0 * 1.6:.1f} {top + size * 0.04:.1f} L{x + rad * f1 * 1.6:.1f} {top + size * 0.04:.1f} "
             f"C{x + rad * f1 * 2.1:.1f} {y:.1f} {x + rad * f1 * 2.2:.1f} {y + size * 0.3:.1f} {x + size * 0.13 * f1 * 2:.1f} {mouth:.1f} Z")
        s.path(d, fill=b)
    s.path(env, fill=s.linear(x - rad, 0, x + rad, 0, [(0, "#ffffff", 0.32), (0.4, "#ffffff", 0.05), (0.7, "#3a2a5a", 0.12),
                                                       (1, "#3a2a5a", 0.4)]))
    s.ellipse(x - rad * 0.38, y - size * 0.22, rad * 0.22, rad * 0.32, fill="#ffffff", opacity=0.35)
    s.path(f"M{x - rad * 0.98:.1f} {y + size * 0.02:.1f} Q{x:.1f} {y + size * 0.12:.1f} {x + rad * 0.98:.1f} {y + size * 0.02:.1f}",
           stroke=shade(a, -0.35), width=max(0.8, size * 0.04), opacity=0.7)
    s.path(env, stroke=shade(b, -0.5), width=max(0.6, size * 0.018), opacity=0.6)
    basket_y = mouth + size * 0.28
    for dx in (-0.12, -0.04, 0.04, 0.12):
        s.line(x + size * dx, mouth, x + size * dx * 0.8, basket_y, "#6a5040", max(0.5, size * 0.012), 0.9)
    bw, bh = size * 0.26, size * 0.17
    s.rect(x - bw / 2, basket_y, bw, bh, fill=s.linear(0, basket_y, 0, basket_y + bh, [(0, WICKER_HI), (1, WICKER_DEEP)]), rx=size * 0.03)
    s.line(x - bw / 2, basket_y + bh * 0.4, x + bw / 2, basket_y + bh * 0.4, WICKER_DEEP, max(0.5, size * 0.012), 0.8)
    _glow(s, x, mouth + size * 0.04, size * 0.12, "#ffd27a", 0.7)  # burner flame in the mouth
    del r


def _banner(s: Svg, x: float, base: float, height: float, length: float, color: str, stripe: str, seed: int, ink: str = "#5a4a5a",
            width: float = 1.4) -> None:
    """Sail-cloth pennant on a pole, streaming to the right in the wind."""
    s.line(x, base, x, base - height, ink, width * 1.5)
    s.line(x - width * 0.3, base, x - width * 0.3, base - height, shade(ink, 0.5), width * 0.6, 0.6)
    s.circle(x, base - height, width * 1.4, fill=BRONZE, stroke=ink, width=width * 0.4)
    top = base - height + width * 1.6
    deep = length * 0.24
    n = 10
    upper, lower = [], []
    for i in range(n + 1):
        t = i / n
        wave = math.sin(t * 5.2 + seed) * length * 0.05 * t
        upper.append((x + length * t, top + wave + t * length * 0.04))
        lower.append((x + length * t * 0.98, top + deep * (1 - t * 0.85) + wave + t * length * 0.04))
    s.path(smooth_open(upper) + "L" + smooth_open(list(reversed(lower)))[1:] + "Z", fill=color, stroke=shade(color, -0.45), width=width * 0.45)
    mid = [((ux + lx) / 2, (uy + ly) / 2) for (ux, uy), (lx, ly) in zip(upper, lower)]
    s.path(smooth_open(mid[:-1]), stroke=stripe, width=deep * 0.22)
    s.path(smooth_open(upper[:7]), stroke="#ffffff", width=width * 0.5, opacity=0.6)


def _kite(s: Svg, x: float, y: float, size: float, colors: tuple[str, str], angle: float, tail: float, ink: str = INK,
          line_w: float = 1.0) -> None:
    """Diamond kite centred at (x, y), nose tilted by ``angle`` degrees, with a bowed tail."""
    a = math.radians(angle)
    ca, sa = math.cos(a), math.sin(a)

    def p(dx: float, dy: float) -> Pt:
        return x + dx * ca - dy * sa, y + dx * sa + dy * ca

    nose, left, right, foot, centre = p(0, -size * 0.62), p(-size * 0.42, -size * 0.12), p(size * 0.42, -size * 0.12), p(0, size * 0.62), p(0, -size * 0.12)
    c1, c2 = colors
    s.polygon([nose, right, centre], fill=c1)
    s.polygon([right, foot, centre], fill=c2)
    s.polygon([foot, left, centre], fill=c1)
    s.polygon([left, nose, centre], fill=c2)
    s.polygon([nose, right, foot, left], stroke=ink, width=line_w)
    s.line(nose[0], nose[1], foot[0], foot[1], ink, line_w * 0.7, 0.8)
    s.line(left[0], left[1], right[0], right[1], ink, line_w * 0.7, 0.8)
    s.polygon([nose, left, centre], fill="#ffffff", opacity=0.25)
    pts = [foot]
    for k in range(1, 7):
        t = k / 6
        pts.append((foot[0] - tail * 0.55 * t, foot[1] + tail * t + math.sin(t * 6.0) * size * 0.18))
    s.path(smooth_open(pts), stroke=ink, width=line_w * 0.6)
    for k in (2, 4, 6):
        bx, by = pts[k]
        bs = size * 0.13
        s.polygon([(bx - bs, by - bs * 0.6), (bx + bs, by + bs * 0.6), (bx + bs, by - bs * 0.6), (bx - bs, by + bs * 0.6)],
                  fill=c1 if k % 4 else c2, stroke=ink, width=line_w * 0.4)


def _chime(s: Svg, x: float, y: float, size: float, ink: str = INK, w_line: float = 1.0) -> None:
    """Wind chime hanging from (x, y): bronze ring, five tubes and a sail-shaped wind catcher."""
    ring_y = y + size * 0.22
    s.line(x, y, x, ring_y, ink, w_line * 0.7)
    s.ellipse(x, ring_y, size * 0.32, size * 0.07, fill=s.linear(0, ring_y - size * 0.07, 0, ring_y + size * 0.07, [(0, BRONZE_HI), (1, BRONZE_DEEP)]),
              stroke=ink, width=w_line * 0.6)
    for k, (dx, ln) in enumerate(((-0.26, 0.5), (-0.13, 0.66), (0.0, 0.76), (0.13, 0.62), (0.26, 0.46))):
        tx = x + size * dx
        ty = ring_y + size * 0.1
        s.line(tx, ring_y + size * 0.04, tx, ty, ink, w_line * 0.4, 0.8)
        tw = size * 0.065
        s.rect(tx - tw / 2, ty, tw, size * ln, fill=s.linear(tx - tw / 2, 0, tx + tw / 2, 0, [(0, "#fff4d0"), (0.4, BRONZE), (1, BRONZE_DEEP)]),
               stroke=ink, width=w_line * 0.45, rx=tw * 0.3)
    s.line(x, ring_y, x, ring_y + size * 0.95, ink, w_line * 0.45, 0.8)
    cy = ring_y + size * 0.95
    s.path(f"M{x:.1f} {cy:.1f} L{x + size * 0.2:.1f} {cy + size * 0.16:.1f} L{x:.1f} {cy + size * 0.34:.1f} Z", fill=SAIL,
           stroke=ink, width=w_line * 0.5)
    s.line(x + size * 0.02, cy + size * 0.1, x + size * 0.13, cy + size * 0.17, SAIL_BLUE, w_line * 0.9)


# --------------------------------------------------------------------------- world
class SkyArchipelago(WorldArt):
    id = "sky_archipelago"
    name = "Arquipélago Celeste"
    accent = "#3aa6f0"
    terrain_headroom = 12.0
    vignette = 0.2
    wind_tint = (244, 250, 255)  # white gust streaks
    provisional = False

    # ------------------------------------------------------------------ sky
    def sky(self) -> Svg:
        s = Svg(960, 540)
        s.rect(0, 0, 960, 540, fill=s.linear(0, 0, 0, 540, [(0, "#1a63be"), (0.22, "#2c84d6"), (0.44, "#66b0e7"), (0.6, "#a7d6f2"),
                                                             (0.68, "#dbecf2"), (0.73, "#fbe9d2"), (1, "#f2dfd8")]))
        sx, sy = SUN
        s.circle(sx, sy, 420, fill=s.radial(sx, sy, 420, [(0, "#fff8e2", 0.62), (0.22, "#fff3d8", 0.28), (0.55, "#ffefd0", 0.08),
                                                          (1, "#ffefd0", 0)]))
        # soft rays fanning down to the right
        for k in range(10):
            a = math.radians(6 + k * 8.2)
            spread = 0.016 + 0.009 * (k % 3)
            s.polygon([(sx, sy), (sx + math.cos(a - spread) * 1000, sy + math.sin(a - spread) * 1000),
                       (sx + math.cos(a + spread) * 1000, sy + math.sin(a + spread) * 1000)], fill="#fffaf0", opacity=0.035 + 0.02 * (k % 2))
        # high cirrus combed by the wind (blowing from the left)
        r = Rand(5)
        for i in range(6):
            x, y = r.uniform(300, 900), r.uniform(30, 190)
            length, thick = r.uniform(140, 300), r.uniform(3.0, 6.5)
            veil = s.linear(x, 0, x + length, 0, [(0, "#ffffff", 0), (0.25, "#ffffff", 0.36), (0.8, "#ffffff", 0.2), (1, "#ffffff", 0)])
            for strand in range(2):
                oy = strand * thick * 1.1
                top = [(x + length * k / 6 + strand * 14, y + oy - k * 1.4 + 2.0 * math.sin(k * 1.3 + i)) for k in range(7)]
                bottom = [(px, py + thick * (0.3 + 0.7 * math.sin(math.pi * k / 6)) * (1 - strand * 0.3)) for k, (px, py) in enumerate(top)]
                s.path(smooth_open(top) + "L" + smooth_open(list(reversed(bottom)))[1:] + "Z", fill=veil, opacity=0.9 - strand * 0.35)
        # towering cumulus far away on the horizon (hazy: they sit behind the sea of clouds)
        self._tower(s, 700, 402, 210, 214, 3)
        self._tower(s, 905, 402, 130, 128, 7)
        self._tower(s, 76, 402, 170, 64, 11)
        s.rect(0, 300, 960, 110, fill=s.linear(0, 300, 0, 410, [(0, "#fbe9d6", 0), (1, "#fbe9d6", 0.75)]))
        # the sun
        s.circle(sx, sy, 78, fill=s.radial(sx, sy, 78, [(0, "#ffffff", 0.95), (0.35, "#fffbea", 0.45), (1, "#fff6dc", 0)]))
        s.circle(sx, sy, 27, fill=s.radial(sx - 6, sy - 6, 31, [(0, "#ffffff"), (0.7, "#fffcf3"), (1, "#ffeec6")]))
        self._sky_sea(s)
        return s

    def _tower(self, s: Svg, cx: float, base: float, width: float, height: float, seed: int) -> None:
        """Towering cumulus: a broad base, a column sheared to the right by the
        wind at altitude and a cauliflower crown; hazy blue shade (far away)."""
        r = Rand(seed)
        puffs: list[Puff] = []
        nb = 9
        for i in range(nb):
            t = i / (nb - 1)
            rad = width * (0.07 + 0.05 * math.sin(math.pi * t)) * r.uniform(0.85, 1.15)
            puffs.append((cx - width / 2 + width * t, base - rad * 0.4, rad))
        levels = max(3, int(height / 24))
        for j in range(1, levels + 1):
            k = j / levels
            col = width * (0.42 - 0.2 * k)
            lean = height * 0.12 * k * k
            m = 4 if k < 0.6 else 3
            for i in range(m):
                rad = col * r.uniform(0.19, 0.28)
                puffs.append((cx + lean + (i - (m - 1) / 2) * col * 0.34 + r.uniform(-4, 4), base - height * k + rad * 0.7, rad))
        for _ in range(3):
            rad = width * r.uniform(0.07, 0.1)
            puffs.append((cx + height * 0.12 + r.uniform(-width * 0.12, width * 0.12), base - height + r.uniform(-2, 8), rad))
        _puffs(s, puffs, lit="#fffaf2", mid="#f1f3f9", low="#d3dbee", deep="#bccae6", shadow="#b4c4e4", shadow_alpha=0.25, glow=0.5,
               creases=0.22)

    def _sky_sea(self, s: Svg) -> None:
        """The sea of clouds far below: soft rolling bands growing toward the
        viewer, warm on top (afternoon light), cool lavender-blue between."""
        bands = ((394.0, 9.0, 15.0, 0.7), (412.0, 14.0, 24.0, 0.5), (440.0, 22.0, 36.0, 0.3), (482.0, 32.0, 50.0, 0.12),
                 (530.0, 44.0, 66.0, 0.0))
        for i, (y, rmin, rmax, haze) in enumerate(bands):
            r = Rand(31 + i * 7)
            lit = mix("#fffaf2", "#f8e8dc", haze)
            mid = mix("#f2f3fa", "#f2e6e0", haze)
            low = mix("#d6dbef", "#e8dce0", haze)
            deep = mix("#bfc6e4", "#dccfd8", haze)
            s.rect(0, y + rmax * 0.15, 960, 540 - y, fill=s.linear(0, y, 0, 540, [(0, low), (1, mix(SEA, SEA_LOW, 0.5))]))
            puffs = []
            x = -rmax * r.uniform(0.2, 1.0)
            while x < 960 + rmax:
                rad = r.uniform(rmin, rmax)
                puffs.append((x, y + rad * 0.25, rad))
                x += rad * r.uniform(1.2, 1.7)
            _puffs(s, puffs, lit=lit, mid=mid, low=low, deep=deep, shadow="#b8bedf", shadow_alpha=0.18 * (1 - haze), glow=0.45 * (1 - haze * 0.6),
                   creases=0.0)

    def _cumulus(self, seed: int, w: float, h: float) -> Svg:
        """Fair-weather cumulus drifting across the upper sky: a flat base and
        a lumpy crown of smaller puffs."""
        r = Rand(seed)
        s = Svg(w, h)
        base = h * 0.84
        puffs: list[Puff] = []
        n = 9
        for i in range(n):
            t = i / (n - 1)
            rad = h * (0.16 + 0.22 * math.sin(math.pi * t) ** 1.2) * r.uniform(0.85, 1.12)
            puffs.append((w * (0.1 + 0.8 * t) + r.uniform(-4, 4), base - rad * 0.62, rad))
        for _ in range(3):
            rad = h * r.uniform(0.18, 0.26)
            puffs.append((w * r.uniform(0.3, 0.68), base - h * r.uniform(0.42, 0.56), rad))
        puffs = [(cx, min(cy, base - rad * 0.3), rad) for cx, cy, rad in puffs]
        s.path(f"M{w * 0.1:.1f} {base:.1f} Q{w * 0.5:.1f} {base + 5:.1f} {w * 0.9:.1f} {base:.1f} L{w * 0.88:.1f} {base - 8:.1f} "
               f"L{w * 0.12:.1f} {base - 8:.1f} Z", fill=CLOUD_DEEP, opacity=0.7)
        _puffs(s, puffs, shadow_alpha=0.28, glow=0.6, creases=0.26)
        return s

    def _feather_particle(self) -> Svg:
        """Weather particle: a small downy feather (the scene does not tint petals)."""
        s = Svg(16, 16)
        vane = smooth_closed([(2.6, 13.6), (5.0, 9.2), (9.6, 4.6), (13.8, 2.0), (12.6, 5.8), (9.0, 10.2), (4.2, 13.8)], 0.7)
        s.path(vane, fill=s.linear(3, 14, 13, 2, [(0, "#dde9fa"), (0.6, "#ffffff"), (1, "#f4f8ff")]), stroke="#8fa8cf", width=0.45)
        s.path("M1.6 14.6 Q7.6 9.6 13.6 2.2", stroke="#7f98c2", width=0.6)
        for k in range(4):
            t = 0.25 + k * 0.16
            px, py = 1.6 + 12 * t, 14.6 - 12.4 * t
            s.line(px, py, px + 1.6, py + 1.8, "#b9cbe6", 0.4, 0.8)
        return s

    def _petal_particle(self, color: str, edge: str) -> Svg:
        s = Svg(16, 16)
        s.path(smooth_closed([(2.6, 8.6), (7.6, 4.2), (13.4, 6.8), (9.0, 11.8)]), fill=s.linear(3, 4, 13, 12, [(0, "#ffffff"), (1, color)]),
               stroke=edge, width=0.45)
        s.path("M4.2 8.4 Q8 7 11.6 7.4", stroke="#ffffff", width=0.6, opacity=0.8)
        return s

    def sky_extras(self) -> dict[str, PropSpec]:
        extras = {
            f"sa.cloud.{i}": PropSpec((lambda i=i, w=w, h=h: self._cumulus(41 + i * 9, w, h)), (0, 0))
            for i, (w, h) in enumerate([(230, 78), (160, 58), (290, 90)])
        }
        # drifting feathers and petals for the weather system (looked up as particle.<name>)
        extras["particle.sa_feather"] = PropSpec(self._feather_particle, (8, 8))
        extras["particle.sa_petal"] = PropSpec(lambda: self._petal_particle("#eef2ff", "#b8c4e4"), (8, 8))
        extras["particle.sa_petal_blue"] = PropSpec(lambda: self._petal_particle("#b9dcff", "#6f9fd6"), (8, 8))
        return extras

    # ------------------------------------------------------------------ parallax layers
    FAR_PAL = {"rock_top": "#eee6ec", "rock": "#dcd3e4", "under": "#b3afd6", "light": "#fff8ee", "dark": "#8f8bbe", "bounce": "#f1eeff",
               "root": "#a497b8", "grass": "#93c3b0", "grass_hi": "#c4e4cc", "crystal": "#b7ecff"}
    MID_PAL = {"rock_top": "#f6ecdc", "rock": "#e5d5c6", "under": "#a59fcb", "light": "#fffaf0", "dark": "#77709f", "bounce": "#ece8ff",
               "root": "#8f7466", "grass": "#76c070", "grass_hi": "#bfe88c", "crystal": "#8fe2ff"}

    def _far(self, seed: int) -> Svg:
        """Distant islands with tiny waterfalls and kites over a far cloud bank (tiles with itself)."""
        w, h = 1200.0, 290.0
        s = Svg(w, h)
        r = Rand(seed)
        pal = self.FAR_PAL
        bank: list[Puff] = []
        x = 0.0
        while x < w:
            rad = r.uniform(16, 30)
            bank.append((x, 236 + r.uniform(-4, 6), rad))
            x += rad * r.uniform(1.1, 1.5)
        s.rect(0, 238, w, h - 238, fill=s.linear(0, 238, 0, h, [(0, "#efebf6"), (1, "#e4dff0")]))
        bank = [(px + shift, py, rad) for px, py, rad in bank for shift in (-w, 0.0, w) if -40 < px + shift < w + 40]
        _puffs(s, bank, lit="#fdf7f2", mid="#f2eef8", low="#dcd8ee", deep="#c6c3e2", shadow="#b8b6dc", shadow_alpha=0.2)
        islands = [(90.0, 128.0, 120.0, 70.0, 1), (330.0, 70.0, 190.0, 96.0, 2), (560.0, 150.0, 80.0, 48.0, 0), (760.0, 96.0, 150.0, 84.0, 1),
                   (980.0, 140.0, 110.0, 60.0, 0), (1120.0, 52.0, 70.0, 40.0, 0)]
        for i, (cx, top, wd, depth, falls) in enumerate(islands):
            cx += r.uniform(-20, 20)
            for shift in (-w, 0.0, w):
                if cx + shift + wd < 0 or cx + shift - wd > w:
                    continue
                _float_island(s, cx + shift, top, wd, depth, pal, seed * 13 + i, roots=3 + falls, fall=depth * 1.1 if falls else 0.0,
                              crystals=1)
                if i in (1, 3):
                    kx, ky = cx + shift + wd * 0.22, top - 60 - i * 6
                    s.path(f"M{cx + shift - wd * 0.1:.1f} {top - 1:.1f} Q{kx - 20:.1f} {top - 20:.1f} {kx:.1f} {ky + 8:.1f}", stroke="#8f86a8",
                           width=0.6, opacity=0.8)
                    _kite(s, kx, ky, 11, ("#ff9c7f", "#fff0c8") if i == 1 else ("#7fbfff", "#fff6e0"), 18, 26, "#7a6f96", 0.7)
        return s

    def _mid(self, seed: int) -> Svg:
        """Nearer islands: a rope bridge with a wind chime, sail-cloth banners,
        hot-air balloons and undersides with dangling roots. Nothing crosses
        the strip edges, so both strips tile in any order."""
        w, h = 1100.0, 330.0
        s = Svg(w, h)
        r = Rand(seed)
        pal = self.MID_PAL
        if seed % 2:
            _balloon(s, 860, 70, 46, ("#ff9d7e", "#fff1d6"), seed)
            _balloon(s, 300, 118, 26, ("#7fc0ff", "#fff6e6"), seed + 1)
            a = (250.0, 170.0, 300.0, 120.0)
            b = (700.0, 196.0, 230.0, 96.0)
            _float_island(s, *a, pal, seed * 5, roots=7, fall=150, crystals=2)
            _float_island(s, *b, pal, seed * 5 + 1, roots=6, crystals=1)
            _float_island(s, 1000.0, 120.0, 70.0, 42.0, pal, seed * 5 + 2, roots=3)
            _banner(s, 190, 168, 54, 46, SAIL, CORAL, seed)
            _banner(s, 330, 166, 40, 34, SAIL, SAIL_BLUE, seed + 3)
            _banner(s, 760, 193, 46, 40, "#fff2d0", SAIL_BLUE, seed + 5)
            self._bg_tree(s, 255, 170, 46, seed)
            self._bg_tree(s, 640, 196, 34, seed + 2)
        else:
            _balloon(s, 520, 64, 38, ("#8fd0ff", "#fffaf0"), seed)
            a = (230.0, 186.0, 240.0, 104.0)
            b = (800.0, 168.0, 260.0, 112.0)
            _float_island(s, *a, pal, seed * 5, roots=6, crystals=1)
            _float_island(s, *b, pal, seed * 5 + 1, roots=7, fall=140, crystals=2)
            # rope bridge between the two islands, with a wind chime under it
            x0b, x1b = a[0] + a[2] / 2 - 18, b[0] - b[2] / 2 + 18
            y0b, y1b = a[1] - 2, b[1] - 2
            sag = 26.0

            def deck(t: float) -> float:
                return y0b + (y1b - y0b) * t + sag * math.sin(math.pi * t)

            for k in range(30):
                t = (k + 0.5) / 30
                px = x0b + (x1b - x0b) * t
                s.line(px, deck(t), px, deck(t) + 3.0, "#8a6248", 3.4)
            rail = 12.0
            for t in [i / 14 for i in range(1, 14)]:
                px = x0b + (x1b - x0b) * t
                s.line(px, deck(t) - rail + sag * 0.3 * math.sin(math.pi * t), px, deck(t), "#7a5a48", 0.7, 0.8)
            ts = [i / 24 for i in range(25)]
            s.path(_line([(x0b + (x1b - x0b) * t, deck(t)) for t in ts]), stroke="#6a4a3a", width=1.2)
            s.path(_line([(x0b + (x1b - x0b) * t, deck(t) - rail + sag * 0.3 * math.sin(math.pi * t)) for t in ts]), stroke="#6a4a3a", width=1.0)
            for px, py in ((x0b, y0b), (x1b, y1b)):
                s.rect(px - 2.2, py - rail - 4, 4.4, rail + 6, fill="#7a5238", rx=1)
            _chime(s, (x0b + x1b) / 2, deck(0.5) + 2.5, 24, "#5a4a5a", 0.8)
            _banner(s, 150, 184, 50, 44, SAIL, SAIL_BLUE, seed)
            _banner(s, 880, 166, 56, 50, SAIL, CORAL, seed + 2)
            self._bg_tree(s, 290, 186, 40, seed + 4)
            self._bg_tree(s, 760, 168, 48, seed + 6)
        return s

    def _bg_tree(self, s: Svg, x: float, base: float, size: float, seed: int) -> None:
        """Wind-combed tree silhouette for the mid layer (canopy streams right)."""
        r = Rand(seed)
        s.path(f"M{x - size * 0.06:.1f} {base:.1f} Q{x - size * 0.02:.1f} {base - size * 0.5:.1f} {x + size * 0.14:.1f} {base - size * 0.8:.1f} "
               f"L{x + size * 0.2:.1f} {base - size * 0.78:.1f} Q{x + size * 0.06:.1f} {base - size * 0.45:.1f} {x + size * 0.06:.1f} {base:.1f} Z",
               fill="#8a6a5a")
        puffs = [(x + size * (0.1 + 0.18 * k) + r.uniform(-2, 2), base - size * (0.82 + 0.06 * math.sin(k * 1.7)), size * (0.26 - 0.03 * k))
                 for k in range(5)]
        for cx, cy, rad in puffs:
            s.circle(cx, cy + rad * 0.15, rad, fill="#4f9a62")
        for cx, cy, rad in puffs:
            s.circle(cx - rad * 0.12, cy - rad * 0.1, rad * 0.86, fill=s.radial(cx - rad * 0.4, cy - rad * 0.5, rad * 1.3,
                                                                                 [(0, "#c6ef96"), (0.6, "#7cc66a"), (1, "#57a463")]))

    def _sea(self, seed: int) -> Svg:
        """The sea of clouds far below, seen through every pit: big soft rolls
        with no outline (walkable cloud always has one). Both strips share the
        puffs at their edges, so they tile in any order."""
        w, h = 900.0, 240.0
        s = Svg(w, h)
        r = Rand(seed)
        s.rect(0, 46, w, h - 46, fill=s.linear(0, 46, 0, h, [(0, "#eeeaf7"), (0.5, SEA), (1, SEA_LOW)]))
        puffs: list[Puff] = [(0.0, 52.0, 34.0), (w, 52.0, 34.0)]
        x = 40.0
        while x < w - 40:
            rad = r.uniform(26, 46)
            puffs.append((x, 50 + r.uniform(-6, 10) + rad * 0.15, rad))
            x += rad * r.uniform(1.0, 1.4)
        _puffs(s, sorted(puffs, key=lambda p: p[1]), lit="#fffaf3", mid="#f3f0f9", low="#d8d4ec", deep="#c3bfe0", shadow="#aaa7d4",
               shadow_alpha=0.24)
        lower: list[Puff] = [(0.0, 104.0, 40.0), (w, 104.0, 40.0)]
        x = 70.0
        while x < w - 60:
            rad = r.uniform(34, 54)
            lower.append((x, 102 + r.uniform(-6, 8), rad))
            x += rad * r.uniform(1.3, 1.8)
        _puffs(s, lower, lit="#f9f5fb", mid="#ebe7f5", low="#d3cfe8", deep="#c0bbdd", shadow="#a8a5d2", shadow_alpha=0.2, opacity=0.9)
        return s

    def _near(self, seed: int) -> Svg:
        """Wisps of cloud drifting low in front of the far layers (soft, no outline)."""
        w, h = 900.0, 260.0
        s = Svg(w, h)
        r = Rand(seed)
        for _ in range(7):
            x, y = r.uniform(60, w - 260), r.uniform(40, h - 40)
            length, thick = r.uniform(140, 240), r.uniform(10, 22)
            veil = s.linear(x, 0, x + length, 0, [(0, "#ffffff", 0), (0.2, "#ffffff", 0.5), (0.7, "#f6f4ff", 0.4), (1, "#f6f4ff", 0)])
            top = [(x + length * k / 8, y - thick * 0.5 * math.sin(math.pi * k / 8) + 2.0 * math.sin(k * 1.4 + seed)) for k in range(9)]
            bottom = [(px, y + thick * 0.35 * math.sin(math.pi * k / 8)) for k, (px, _py) in enumerate(top)]
            s.path(smooth_open(top) + "L" + smooth_open(list(reversed(bottom)))[1:] + "Z", fill=veil)
            s.path(smooth_open(top[1:-1]), stroke="#ffffff", width=1.2, opacity=0.3)
        return s

    def layer_art(self) -> dict[str, PropSpec]:
        art = {"sa.far.0": PropSpec(lambda: self._far(11), (0, 0))}
        for i in range(2):
            art[f"sa.mid.{i}"] = PropSpec((lambda i=i: self._mid(21 + i)), (0, 0))
            art[f"sa.sea.{i}"] = PropSpec((lambda i=i: self._sea(31 + i)), (0, 0))
            art[f"sa.near.{i}"] = PropSpec((lambda i=i: self._near(41 + i)), (0, 0))
        return art

    def layers(self) -> list[Layer]:
        return [
            Layer("far", 0.06, ["sa.far.0"], 1200, 40, vertical=0.04),
            Layer("mid", 0.2, ["sa.mid.0", "sa.mid.1"], 1100, 52, vertical=0.11),
            Layer("sea", 0.34, ["sa.sea.0", "sa.sea.1"], 900, 205, vertical=0.18),
            Layer("near", 0.55, ["sa.near.0", "sa.near.1"], 900, 150, vertical=0.3),
        ]

    # ------------------------------------------------------------------ terrain
    def terrain(self, style: str, w: float, h: float, seed: int, left: bool, right: bool, top: bool = True, x0: float = 0.0,
                surface: str = "normal") -> Svg:
        """Terrain chunk art. Everything that crosses chunk borders (grass
        tufts, strata, cloud lobes, underside lobes, roots, drips) is keyed on
        the world x (``x0`` + local x), so adjacent chunks join seamlessly;
        only hanging edges are outlined, never a chunk's vertical borders."""
        if style == "cave":
            return self._cave(w, h, seed, left, right, top, x0)
        if style == "fortress":
            return self._fortress(w, h, seed, left, right, top, x0, surface)
        if style == "cloud":
            return self._cloud_mass(w, h, left, right, top, x0)
        return self._island(w, h, seed, left, right, top, x0, surface)

    def _island(self, w: float, h: float, seed: int, left: bool, right: bool, top: bool, x0: float, surface: str) -> Svg:
        """Pale sandstone island: strata, crystals and roots in the rock, an
        underside that tapers at exposed ends and hangs in lobes with roots."""
        hr = self.terrain_headroom
        s = Svg(w, h + hr + HANG)
        r = Rand(seed)
        y0, bottom = hr, h + hr
        span = bottom - y0
        d0 = max(30.0, span * 0.5)
        taper = min(w * 0.28, span * 0.42, 44.0) if span > 40 else 0.0

        def inset(y: float) -> float:
            if taper <= 0 or y <= y0 + d0:
                return 0.0
            k = min(1.0, (y - y0 - d0) / max(1.0, bottom - y0 - d0))
            return taper * k ** 1.8

        def face(y: float, k: float) -> float:
            ramp = min(1.0, (y - y0) / 14.0)
            return inset(y) + ramp * (1.2 * math.sin(y * 0.23 + k) + 0.6 * math.sin(y * 0.61 + 2 * k))

        ys = [y0 + 1.0 + (bottom - y0 - 1.0) * i / 18 for i in range(19)]
        lface = [(face(y, x0 * 0.011), y) for y in ys] if left else [(0.0, y) for y in ys]
        rface = [(w - face(y, x0 * 0.017 + 1.0), y) for y in ys] if right else [(w, y) for y in ys]
        xl, xr = lface[-1][0], rface[-1][0]

        def under_y(lx: float) -> float:
            gx = x0 + lx
            n = math.floor(gx / 26.0)
            t = gx / 26.0 - n
            depth = 2.0 + 9.0 * _hash(n, 3)
            fade = 1.0
            if left:
                fade = min(fade, max(0.0, (lx - xl) / 26.0))
            if right:
                fade = min(fade, max(0.0, (xr - lx) / 26.0))
            return bottom + depth * math.sin(math.pi * t) ** 0.8 * fade

        under = [(lx, under_y(lx)) for lx in _samples(w, 3.0) if xl < lx < xr]
        under = [(xl, bottom)] + under + [(xr, bottom)]
        outline = lface + under[1:-1] + list(reversed(rface))
        s.path(_poly(outline), fill=s.linear(0, y0, 0, y0 + max(span, 96.0) + 8, [(0, ROCK_TOP), (0.14, ROCK), (0.46, ROCK_MID), (0.76, ROCK_LOW),
                                                                                  (1, ROCK_UNDER)]))

        def inside(lx: float, y: float, margin: float) -> bool:
            if y > bottom - margin:
                return False
            if left and lx < inset(y) + margin:
                return False
            return not (right and lx > w - inset(y) - margin)

        # wind-carved sandstone strata (world-aligned)
        xs = _samples(w, 3.0)
        for k in range(7):
            by = y0 + 21 + k * 20

            if by > bottom - 10:
                break

            def yy(lx: float, k: int = k, by: float = by) -> float:
                gx = x0 + lx
                return by + 2.6 * _wobble(gx, k * 1.31) + 4.0 * math.sin(gx * 0.0052 + k * 0.9)

            for run in _runs(xs, lambda lx, yy=yy: inside(lx, yy(lx) + 8, 3.0)):
                band = [(lx, yy(lx)) for lx in run]
                if k % 2 == 0:
                    s.path(_poly(band + [(lx, y + 7.0) for lx, y in reversed(band)]), fill="#fff6e6", opacity=0.24)
                s.path(_line([(lx, y + 7.5) for lx, y in band]), stroke=ROCK_LINE, width=1.1, opacity=0.2)
                s.path(_line([(lx, y + 0.6) for lx, y in band]), stroke="#fffaf2", width=0.9, opacity=0.5)
        # wind-carved hollows and embedded pebbles
        deep = min(bottom - 6, y0 + 150)
        for _ in range(max(1, int(w / 110))):
            hx, hy = r.uniform(14, w - 14), r.uniform(y0 + 26, max(y0 + 27, deep - 10))
            hw = r.uniform(6, 13)
            if not inside(hx - hw, hy, 5) or not inside(hx + hw, hy, 5):
                continue
            s.path(blob(hx, hy, hw, hw * 0.42, 0.18, seed=hx), fill="#a8919a", opacity=0.32)
            s.path(f"M{hx - hw * 0.9:.1f} {hy + hw * 0.3:.1f} Q{hx:.1f} {hy + hw * 0.62:.1f} {hx + hw * 0.9:.1f} {hy + hw * 0.3:.1f}",
                   stroke="#fff8ec", width=1.0, opacity=0.6)
        for _ in range(max(2, int(w / 46))):
            px, py = r.uniform(8, w - 8), r.uniform(y0 + 16, max(y0 + 17, deep))
            rad = r.uniform(2.0, 4.6)
            if not inside(px, py, rad + 3):
                continue
            tone = r.choice(["#fff6ea", "#ece2f2", "#f2dcc4", "#ded6ea"])
            s.path(blob(px, py, rad * 1.25, rad, 0.12, seed=px), fill=s.radial(px - rad * 0.4, py - rad * 0.5, rad * 1.8, [(0, "#ffffff"), (1, tone)]),
                   stroke=ROCK_LINE, width=0.55, opacity=0.75)
        # sky crystals growing in the rock (kept inside the chunk)
        for _ in range(int(w / 150) + (1 if r.next() < 0.5 else 0)):
            cx, cy = r.uniform(16, w - 16), r.uniform(y0 + 30, max(y0 + 31, deep - 4))
            if not inside(cx, cy, 12):
                continue
            s.ellipse(cx, cy + 1.5, 7, 2.6, fill="#6c5a78", opacity=0.45)
            _cluster(s, cx, cy + 1.5, r.uniform(8, 12), int(cx * 7) + seed % 97, r.choice([CRYSTAL, CRYSTAL, CRYSTAL_LILAC]), glow=0.35)
        # roots reaching down from the turf
        for _ in range(max(1, int(w / 80))):
            rx = r.uniform(10, w - 10)
            if not inside(rx, y0 + 30, 6):
                continue
            pts = [(rx, y0 + 6)]
            for _k in range(4):
                pts.append((pts[-1][0] + r.uniform(-5, 5), pts[-1][1] + r.uniform(5, 9)))
            s.path(smooth_open(pts), stroke="#8a6a50", width=1.3, opacity=0.5)
            s.path(smooth_open(pts[1:3] + [(pts[2][0] + r.uniform(-7, 7), pts[2][1] + 6)]), stroke="#8a6a50", width=0.8, opacity=0.4)
        # exposed faces: lit on the left, in shade on the right
        if left:
            s.path(_poly(lface + [(x + 5.5, y) for x, y in reversed(lface)]), fill=ROCK_HI, opacity=0.5)
        if right:
            s.path(_poly(rface + [(x - 8.0, y) for x, y in reversed(rface)]), fill="#5f5482", opacity=0.26)
        # underside: shade, bounce light from the clouds below, the hanging outline
        inner = under[1:-1]
        if len(inner) > 1:
            s.path(_line([(x, y - 4.0) for x, y in inner]), stroke="#6d6494", width=7.0, opacity=0.28)
            s.path(_line([(x, y - 1.3) for x, y in inner]), stroke="#efeaff", width=1.5, opacity=0.6)
        edge = (lface if left else []) + inner + (list(reversed(rface)) if right else [])
        if len(edge) > 1:
            s.path(_line(edge), stroke=ROCK_LINE, width=1.3)
        # roots and crystals hanging below (world slots, never cut by a chunk border)
        slot = 21.0
        for n in range(math.floor(x0 / slot), math.floor((x0 + w) / slot) + 1):
            if _hash(n, 5) < 0.5:
                continue
            lx = (n + 0.3 + 0.4 * _hash(n, 6)) * slot - x0
            if xl + 7 < lx < xr - 7 and 4 < lx < w - 4:
                uy = under_y(lx)
                _dangle(s, lx, uy - 1.5, min(HANG - (uy - bottom) - 2, 7 + 17 * _hash(n, 7)), n, 1.0 + 0.7 * _hash(n, 8))
        slot = 57.0
        for n in range(math.floor(x0 / slot), math.floor((x0 + w) / slot) + 1):
            if _hash(n, 9) < 0.62:
                continue
            lx = (n + 0.5) * slot - x0
            if xl + 10 < lx < xr - 10 and 7 < lx < w - 7:
                tone = CRYSTAL_LILAC if _hash(n, 10) > 0.7 else CRYSTAL
                uy = under_y(lx)
                _crystal(s, lx, uy - 2.5, 90 + (_hash(n, 11) - 0.5) * 30, 7 + 6 * _hash(n, 12), 3.4, tone)
                _crystal(s, lx + 3.2, uy - 2.0, 104, 5 + 3 * _hash(n, 13), 2.6, tone)
        if top:
            if surface == "ice":
                self._wet_cap(s, r, w, y0, left, right, x0)
            else:
                self._grass_cap(s, r, w, y0, left, right, x0)
        return s

    def _grass_cap(self, s: Svg, r: Rand, w: float, y0: float, left: bool, right: bool, x0: float) -> None:
        """Lush turf whose tufts hang over the lip (world-aligned), blades
        combed by the wind and wildflowers."""
        cell = 7.0

        def top_y(lx: float) -> float:
            gx = x0 + lx
            y = y0 - 1.0 + 0.8 * _wobble(gx, 0.5) + 0.3 * math.sin(gx * 0.31)
            if left and lx < 6:
                y += 4.0 * (1 - lx / 6) ** 2
            if right and w - lx < 6:
                y += 4.0 * (1 - (w - lx) / 6) ** 2
            return y

        def lip_y(lx: float) -> float:
            gx = x0 + lx
            n = math.floor(gx / cell + 1e-9)
            t = gx / cell - n
            tuft = (1 - abs(2 * t - 1)) ** 1.3 * (1.2 + 4.4 * _hash(n, 13))
            y = y0 + 7.6 + 1.3 * _wobble(gx, 1.7) + tuft
            if left and lx < 10:
                y += 5.5 * (1 - lx / 10) ** 1.6
            if right and w - lx < 10:
                y += 5.5 * (1 - (w - lx) / 10) ** 1.6
            return y

        tops = [(lx, top_y(lx)) for lx in _samples(w, 2.0)]
        lips = [(lx, lip_y(lx)) for lx in _grid(x0, w, cell)]
        s.path(_line([(x, y + 2.6) for x, y in lips]), stroke="#2a1e30", width=4.5, opacity=0.2)
        s.path(_poly(tops + list(reversed(lips))), fill=s.linear(0, y0 - 2, 0, y0 + 13, [(0, GRASS_TOP), (0.42, GRASS), (1, GRASS_DARK)]))
        # darker clumps and a lit band give the turf some volume
        for n in range(math.floor(x0 / 31.0), math.floor((x0 + w) / 31.0) + 1):
            cx = (n + _hash(n, 21)) * 31.0 - x0
            if 6 < cx < w - 6:
                s.path(blob(cx, y0 + 6.2, 5 + 4 * _hash(n, 22), 1.8, 0.3, seed=n), fill=GRASS_DARK, opacity=0.35)
        s.path(_line([(x, y + 2.4) for x, y in tops]), stroke="#d2f68a", width=2.2, opacity=0.4)
        s.path(_line(lips), stroke=GRASS_LINE, width=1.1)
        if left:
            s.path(f"M0 {tops[0][1]:.2f} L0 {lips[0][1]:.2f}", stroke=GRASS_LINE, width=1.4)
        if right:
            s.path(f"M{w:.2f} {tops[-1][1]:.2f} L{w:.2f} {lips[-1][1]:.2f}", stroke=GRASS_LINE, width=1.4)
        s.path(_line([(x, y + 0.7) for x, y in tops]), stroke=GRASS_LIGHT, width=1.3, opacity=0.9)
        # blades leaning with the wind
        for _ in range(max(3, int(w / 8))):
            bx = r.uniform(3, w - 6)
            bh = r.uniform(3, 8)
            lean = r.uniform(0.6, 3.6)
            by = top_y(bx) + 1.2
            s.path(f"M{bx - 1.3:.2f} {by:.2f} Q{bx + lean * 0.3:.2f} {by - bh * 0.55:.2f} {bx + lean:.2f} {by - bh:.2f} "
                   f"Q{bx + 0.9:.2f} {by - bh * 0.4:.2f} {bx + 1.3:.2f} {by:.2f} Z", fill=r.choice([GRASS_TOP, GRASS, "#a6e66a", "#d8f890"]))
        # wildflowers: daisies, forget-me-nots, buttercups
        for _ in range(int(w / 46)):
            fx = r.uniform(7, w - 7)
            fy = top_y(fx) - r.uniform(2.5, 5.0)
            color = r.choice(FLOWERS)
            s.line(fx, fy, fx - 0.6, top_y(fx) + 1, "#4f9a3e", 0.8)
            for k in range(5):
                a = k * 2 * math.pi / 5 + fx
                s.circle(fx + math.cos(a) * 1.6, fy + math.sin(a) * 1.6, 1.25, fill=color, stroke=shade(color, -0.35), width=0.25)
            s.circle(fx, fy, 0.9, fill="#ffb732" if color != "#ffe57a" else "#e88a1a")

    def _wet_cap(self, s: Svg, r: Rand, w: float, y0: float, left: bool, right: bool, x0: float) -> None:
        """Slick wet rock: a glossy blue-slate band with reflections, beads
        of water and drips; the rock below is darkened by the run-off."""
        xs = _samples(w, 2.0)

        def top_y(lx: float) -> float:
            y = y0 - 0.6
            if left and lx < 4:
                y += 2.6 * (1 - lx / 4) ** 2
            if right and w - lx < 4:
                y += 2.6 * (1 - (w - lx) / 4) ** 2
            return y

        def low_y(lx: float) -> float:
            gx = x0 + lx
            y = y0 + 7.2 + 0.9 * _wobble(gx, 2.1)
            n = math.floor(gx / 11.0)
            for m in (n - 1, n, n + 1):
                if _hash(m, 41) > 0.55:
                    c = (m + 0.5) * 11.0
                    y += (1.5 + 3.0 * _hash(m, 42)) * math.exp(-((gx - c) / 2.4) ** 2)
            if left and lx < 6:
                y -= 2.4 * (1 - lx / 6)
            if right and w - lx < 6:
                y -= 2.4 * (1 - (w - lx) / 6)
            return y

        tops = [(lx, top_y(lx)) for lx in xs]
        lows = [(lx, low_y(lx)) for lx in xs]
        s.rect(0, y0 + 4, w, 46, fill=s.linear(0, y0 + 4, 0, y0 + 50, [(0, "#3d6f96", 0.42), (1, "#3d6f96", 0)]))
        for n in range(math.floor(x0 / 17.0), math.floor((x0 + w) / 17.0) + 1):  # run-off streaks
            lx = (n + 0.5) * 17.0 - x0
            if _hash(n, 43) > 0.45 and 2 < lx < w - 2:
                ln = 10 + 26 * _hash(n, 44)
                s.line(lx, y0 + 8, lx + 0.8, y0 + 8 + ln, "#e8f6ff", 1.0 + _hash(n, 45), 0.35)
        s.path(_line([(x, y + 2.4) for x, y in lows]), stroke="#0d2a4a", width=4.0, opacity=0.25)
        s.path(_poly(tops + list(reversed(lows))), fill=s.linear(0, y0 - 1, 0, y0 + 9, [(0, WET_HI), (0.16, WET_TOP), (0.55, WET), (1, WET_DEEP)]))
        streak = 40.0
        for m in range(math.floor(x0 / streak), math.floor((x0 + w) / streak) + 1):
            if _hash(m, 31) < 0.3:
                continue
            gx = m * streak + 26 * _hash(m, 32) - x0
            wide = 3 + 6 * _hash(m, 33)
            if 6 < gx and gx + wide + 2 < w:
                s.polygon([(gx, y0 + 1.4), (gx + wide, y0 + 1.4), (gx + wide - 5, y0 + 6.5), (gx - 5, y0 + 6.5)], fill="#ffffff", opacity=0.42)
        for _ in range(int(w / 22)):
            s.circle(r.uniform(4, w - 4), r.uniform(y0 + 2.5, y0 + 5.5), r.uniform(0.5, 1.1), fill="#ffffff", opacity=0.75)
        s.path(_line(lows), stroke=WET_LINE, width=1.1)
        if left:
            s.path(f"M0 {tops[0][1]:.2f} L0 {lows[0][1]:.2f}", stroke=WET_LINE, width=1.4)
        if right:
            s.path(f"M{w:.2f} {tops[-1][1]:.2f} L{w:.2f} {lows[-1][1]:.2f}", stroke=WET_LINE, width=1.4)
        s.path(_line(tops), stroke="#6fbde6", width=0.9, opacity=0.9)
        s.path(_line([(x, y + 1.2) for x, y in tops]), stroke="#ffffff", width=1.5, opacity=0.95)
        for n in range(math.floor(x0 / 11.0), math.floor((x0 + w) / 11.0) + 1):  # drips falling from the lowest points
            if _hash(n, 41) <= 0.55 or _hash(n, 46) < 0.5:
                continue
            lx = (n + 0.5) * 11.0 - x0
            if 3 < lx < w - 3:
                dy = low_y(lx) + 1.5 + 4 * _hash(n, 47)
                s.path(f"M{lx:.2f} {dy - 2.2:.2f} Q{lx + 1.4:.2f} {dy + 0.6:.2f} {lx:.2f} {dy + 1.3:.2f} Q{lx - 1.4:.2f} {dy + 0.6:.2f} "
                       f"{lx:.2f} {dy - 2.2:.2f} Z", fill="#d8f2ff", stroke=WET_LINE, width=0.4)

    def _cloud_mass(self, w: float, h: float, left: bool, right: bool, top: bool, x0: float) -> Svg:
        """Walkable cumulus: puffy top keyed on the world x, a defined
        lavender top line, puff volumes, and a body that thins out below."""
        hr = self.terrain_headroom
        s = Svg(w, h + hr + 12)
        y0, bottom = hr, h + hr
        span = bottom - y0
        cell = 23.0
        rr = min(15.0, span * 0.45)

        def top_y(lx: float) -> float:
            y = y0
            if top:
                gx = x0 + lx
                n = math.floor(gx / cell)
                t = gx / cell - n
                y = y0 + 1.2 - (2.2 + 3.8 * _hash(n, 17)) * math.sin(math.pi * t) ** 0.55
            if left and lx < rr:
                y = max(y, y0 + rr - math.sqrt(max(0.0, rr * rr - (rr - lx) ** 2)))
            if right and w - lx < rr:
                y = max(y, y0 + rr - math.sqrt(max(0.0, rr * rr - (rr - (w - lx)) ** 2)))
            return y

        def low_y(lx: float) -> float:
            gx = x0 + lx
            n = math.floor(gx / 31.0)
            t = gx / 31.0 - n
            return bottom - 3 + (3 + 6 * _hash(n, 19)) * math.sin(math.pi * t) ** 0.6

        xs = _samples(w, 2.0)
        tops = [(lx, top_y(lx)) for lx in xs]
        ys = [y0 + rr + (bottom - 3 - y0 - rr) * i / 12 for i in range(13)]
        lside = [(3.4 - 3.0 * abs(math.sin((y - y0) * math.pi / 15)), y) for y in ys] if left else [(0.0, y) for y in ys]
        rside = [(w - 3.4 + 3.0 * abs(math.sin((y - y0) * math.pi / 15 + 0.7)), y) for y in ys] if right else [(w, y) for y in ys]
        lows = [(lx, low_y(lx)) for lx in reversed(xs)]
        body = tops + rside + lows + list(reversed(lside))
        s.path(_poly(body), fill=s.linear(0, y0 - 6, 0, y0 + max(span, 50.0) + 8, [(0, "#ffffff"), (0.16, "#f8f7fd"), (0.45, "#e6e3f5"),
                                                                                   (0.8, "#d1cdea", 0.92), (1, "#c2bee3", 0.7)]))
        # puff volumes: a crease under every top lobe, a second row of soft puffs
        for n in range(math.floor(x0 / cell) - 1, math.floor((x0 + w) / cell) + 2):
            cx = (n + 0.5) * cell - x0
            if top:
                a = 2.2 + 3.8 * _hash(n, 17)
                s.path(f"M{cx - cell * 0.42:.1f} {y0 + 2.5:.1f} Q{cx:.1f} {y0 + 6 + a * 0.4:.1f} {cx + cell * 0.46:.1f} {y0 + 1.5:.1f}",
                       stroke=CLOUD_SHADE, width=1.6, opacity=0.55)
                s.circle(cx - cell * 0.12, y0 - a * 0.3, cell * 0.2, fill="#ffffff", opacity=0.7)
            px = cx + cell * 0.5
            py = y0 + 15 + 3 * _hash(n, 18)
            if py + 14 < bottom:
                s.path(f"M{px - cell * 0.55:.1f} {py:.1f} Q{px:.1f} {py + 9:.1f} {px + cell * 0.55:.1f} {py:.1f}", stroke="#cfcbe8", width=2.2,
                       opacity=0.45)
                s.circle(px - cell * 0.18, py - 6, cell * 0.22, fill="#ffffff", opacity=0.35)
        s.path(_line(tops), stroke=CLOUD_LINE, width=1.1)
        s.path(_line([(x, y + 1.3) for x, y in tops]), stroke="#ffffff", width=1.6, opacity=0.95)
        if left:
            s.path(_line(lside[:8]), stroke=CLOUD_LINE, width=1.0, opacity=0.6)
        if right:
            s.path(_line(rside[:8]), stroke=CLOUD_LINE, width=1.0, opacity=0.6)
        return s

    def _fortress(self, w: float, h: float, seed: int, left: bool, right: bool, top: bool, x0: float, surface: str) -> Svg:
        """Sky-citadel masonry: white sandstone ashlar with sky-blue glazed
        tiles and bronze studs under a polished coping with a tile band. The
        running bond, inlays and coping joints are keyed on the world x."""
        hr = self.terrain_headroom
        s = Svg(w, h + hr)
        r = Rand(seed)
        y0, bottom = hr, h + hr
        wet = surface == "ice"
        coping = (4.0 if wet else 10.0) if top else 0.0
        s.rect(-1, y0, w + 2, h, fill=s.linear(0, y0, 0, bottom, [(0, MORTAR), (1, "#5c5578")]))
        row_h, bw = 22.0, 46.0
        yy, row = y0 + coping, 0
        while yy < bottom - 1:
            rh = min(row_h, bottom - yy)
            offset = (row % 2) * bw / 2
            k = math.floor((x0 - offset) / bw)
            while k * bw + offset - x0 < w + 1:
                self._ashlar(s, k, row, k * bw + offset - x0, yy, bw, rh, w)
                k += 1
            yy += row_h
            row += 1
        s.rect(-1, y0 + 30, w + 2, max(0.0, h - 30), fill=s.linear(0, y0 + 30, 0, min(bottom, y0 + 200), [(0, "#3a3466", 0), (1, "#3a3466", 0.5)]))
        if left:
            s.rect(0, y0, 5, h, fill=s.linear(0, y0, 0, bottom, [(0, "#ffffff", 0.55), (1, "#ffffff", 0.08)]))
            s.line(0.7, y0, 0.7, bottom, ROCK_LINE, 1.4, 0.8)
        if right:
            s.rect(w - 6, y0, 6, h, fill="#2e2850", opacity=0.4)
            s.line(w - 0.7, y0, w - 0.7, bottom, ROCK_LINE, 1.4, 0.8)
        if top and wet:
            self._wet_cap(s, r, w, y0, left, right, x0)
        elif top:
            s.rect(-1, y0 - 1.2, w + 2, 7.2, fill=s.linear(0, y0 - 1.2, 0, y0 + 6, [(0, "#ffffff"), (0.4, STONE_HI), (1, STONE_DARK)]))
            s.rect(-1, y0 + 6, w + 2, 4, fill=s.linear(0, y0 + 6, 0, y0 + 10, [(0, TILE), (1, TILE_DEEP)]))
            for n in range(math.floor(x0 / 12.0), math.floor((x0 + w) / 12.0) + 1):
                lx = n * 12.0 - x0
                if -1 < lx < w + 1:
                    s.line(lx, y0 + 6.2, lx, y0 + 9.8, "#1d4a86", 0.7, 0.7)
                    s.line(lx + 2, y0 + 7, lx + 5, y0 + 7, "#bfe2ff", 0.8, 0.7)
            for n in range(math.floor(x0 / 64.0), math.floor((x0 + w) / 64.0) + 1):
                lx = n * 64.0 + 10 - x0
                if -1 < lx < w + 1:
                    s.line(lx, y0 + 0.5, lx, y0 + 5.8, "#b8aca0", 0.9, 0.8)
            s.line(-1, y0 + 10.8, w + 1, y0 + 10.8, "#1c1838", 2.2, 0.35)
            s.line(-1, y0 - 0.4, w + 1, y0 - 0.4, "#ffffff", 1.2, 0.9)
            if left:
                s.line(0.7, y0 - 1.2, 0.7, y0 + 10, ROCK_LINE, 1.4)
            if right:
                s.line(w - 0.7, y0 - 1.2, w - 0.7, y0 + 10, ROCK_LINE, 1.4)
        return s

    def _ashlar(self, s: Svg, k: int, row: int, gx0: float, y: float, bw: float, rh: float, w: float) -> None:
        """One block of a course; ``k``/``row`` give it a world-stable identity."""
        bx0, bx1 = max(-1.0, gx0 + 1.0), min(w + 1.0, gx0 + bw - 1.0)
        y1 = y + rh - 1.1
        if bx1 <= bx0 or y1 <= y + 2:
            return
        ident = k * 7 + row * 131
        if _hash(ident, 5) < 0.08 and rh > 14:
            s.rect(bx0, y + 1.0, bx1 - bx0, y1 - y - 1.0, fill=s.linear(0, y, 0, y1, [(0, "#8fd0ff"), (0.4, TILE), (1, TILE_DEEP)]))
            s.line(bx0, y + 1.8, bx1, y + 1.8, "#e6f6ff", 1.0, 0.9)
            cx = gx0 + bw / 2
            if -6 < cx < w + 6:
                s.polygon([(cx, y + 4), (cx + 5, y + rh / 2), (cx, y + rh - 5), (cx - 5, y + rh / 2)], fill="#ffffff", opacity=0.85)
                s.polygon([(cx, y + 6.5), (cx + 2.5, y + rh / 2), (cx, y + rh - 7.5), (cx - 2.5, y + rh / 2)], fill=BRONZE)
            return
        tone = mix(STONE_DARK, STONE_HI, 0.45 + 0.45 * _hash(ident, 6))
        s.rect(bx0, y + 1.0, bx1 - bx0, y1 - y - 1.0, fill=s.linear(0, y, 0, y1, [(0, shade(tone, 0.4)), (0.25, tone), (1, shade(tone, -0.12))]))
        s.line(bx0 + 0.5, y + 1.7, bx1 - 0.5, y + 1.7, "#ffffff", 1.0, 0.7)
        s.line(bx0, y1 - 0.4, bx1, y1 - 0.4, "#6e6488", 1.0, 0.4)
        if -1 < gx0 + 1.7 < w + 1:
            s.line(gx0 + 1.7, y + 2.2, gx0 + 1.7, y1 - 1.0, "#ffffff", 0.9, 0.55)
        if -1 < gx0 + bw - 1.7 < w + 1:
            s.line(gx0 + bw - 1.7, y + 2.2, gx0 + bw - 1.7, y1 - 1.0, "#7a6e90", 0.9, 0.4)
        if _hash(ident, 7) > 0.9:
            cx = gx0 + bw / 2
            if -4 < cx < w + 4:
                s.circle(cx, y + rh / 2, 2.4, fill=s.radial(cx - 0.8, y + rh / 2 - 0.8, 2.8, [(0, BRONZE_HI), (1, BRONZE_DEEP)]), stroke=BRONZE_LINE,
                         width=0.6)

    def _cave(self, w: float, h: float, seed: int, left: bool, right: bool, top: bool, x0: float) -> Svg:
        """Inside an island: warm violet sandstone darkening with depth, lit by
        glowing crystal veins; a pale rim on top, roots and crystals hanging
        under thin slabs (ceilings)."""
        r = Rand(seed)
        hr = self.terrain_headroom
        ceiling = h <= 100
        s = Svg(w, h + hr + (16 if ceiling else 0))
        y0, bottom = hr, h + hr
        s.rect(0, y0, w, h, fill=s.linear(0, y0, 0, y0 + min(h, 230), [(0, "#9a8296"), (0.1, "#76607a"), (0.5, "#4a3a56"), (1, "#2a2036")]))
        xs = _samples(w, 4.0)
        for k in range(4):
            def yy(lx: float, k: int = k) -> float:
                gx = x0 + lx
                return y0 + 18 + k * 21 + 3.0 * _wobble(gx * 0.8, k * 1.7)

            if y0 + 18 + k * 21 > bottom - 6:
                break
            s.path(_line([(lx, yy(lx)) for lx in xs]), stroke="#c8b0c4", width=1.4, opacity=0.24 - k * 0.04)
            s.path(_line([(lx, yy(lx) + 2.2) for lx in xs]), stroke="#1c1428", width=1.1, opacity=0.3 - k * 0.05)
        for _ in range(max(1, int(w * min(h, 160) / 4000))):
            px, py = r.uniform(6, w - 6), r.uniform(y0 + 10, min(bottom - 6, y0 + 150))
            rad = r.uniform(3, 7)
            s.path(blob(px, py, rad * 1.3, rad * 0.8, 0.15, seed=px), fill=r.choice(["#5e4a66", "#6e5a74", "#463852"]), opacity=0.75)
        for _ in range(max(1, int(w / 150))):  # glowing crystal veins
            vx = r.uniform(16, w - 70)
            vy = r.uniform(y0 + 22, min(bottom - 12, y0 + 110))
            pts = [(vx, vy)]
            for _k in range(5):
                pts.append((pts[-1][0] + r.uniform(7, 11), pts[-1][1] + r.uniform(-5, 5)))
            s.path(_line(pts), stroke="#7fe8ff", width=5.0, opacity=0.18)
            s.path(_line(pts), stroke="#c8f6ff", width=1.4, opacity=0.85)
            for px, py in pts[1:-1:2]:
                _crystal(s, px, py + 1, -90 + r.uniform(-25, 25), r.uniform(4, 7), 2.6)
        for _ in range(int(w / 140) + 1):
            cx, cy = r.uniform(14, w - 14), r.uniform(y0 + 18, min(bottom - 10, y0 + 70))
            _cluster(s, cx, cy, r.uniform(8, 12), int(cx) + seed % 89, r.choice([CRYSTAL, CRYSTAL_LILAC]), glow=0.45)
        if left:
            s.rect(0, y0, 5, h, fill=s.linear(0, y0, 0, bottom, [(0, "#f2e2f0", 0.4), (1, "#f2e2f0", 0.05)]))
        if right:
            s.rect(w - 6, y0, 6, h, fill="#140e1e", opacity=0.45)
        # pale rim along the top (cave floors are often covered by the room walls)
        tops = [(lx, y0 - 0.8 + 0.8 * _wobble(x0 + lx, 0.9)) for lx in _samples(w, 2.0)]
        lows = [(lx, y0 + 5.0 + 1.4 * _wobble(x0 + lx, 2.2) + 1.4 * abs(math.sin((x0 + lx) * 0.17))) for lx in _samples(w, 2.0)]
        s.path(_line([(x, y + 2) for x, y in lows]), stroke="#140e1e", width=3.0, opacity=0.35)
        s.path(_poly(tops + list(reversed(lows))), fill=s.linear(0, y0 - 2, 0, y0 + 8, [(0, "#f4e6d6"), (1, "#b89cae")]))
        s.path(_line(lows), stroke="#4a3450", width=1.0, opacity=0.9)
        s.path(_line([(x, y + 0.8) for x, y in tops]), stroke="#fff6ea", width=1.1, opacity=0.8)
        for n in range(math.floor(x0 / 19.0), math.floor((x0 + w) / 19.0) + 1):
            lx = (n + _hash(n, 51)) * 19.0 - x0
            if _hash(n, 52) > 0.6 and 4 < lx < w - 4:
                s.path(blob(lx, y0 + 0.5, 4 + 3 * _hash(n, 53), 1.6, 0.3, seed=n), fill="#7fae7a", opacity=0.85)
        if ceiling:
            slot = 15.0
            for n in range(math.floor(x0 / slot), math.floor((x0 + w) / slot) + 1):
                lx = (n + 0.5) * slot - x0
                if not 5 < lx < w - 5:
                    continue
                v = _hash(n, 61)
                if v > 0.72:
                    _crystal(s, lx, bottom - 1.5, 90 + (_hash(n, 62) - 0.5) * 24, 6 + 7 * _hash(n, 63), 3.2,
                             CRYSTAL_LILAC if _hash(n, 64) > 0.6 else CRYSTAL)
                elif v > 0.35:
                    _dangle(s, lx, bottom - 1.0, 5 + 10 * _hash(n, 65), n, 0.9 + 0.5 * _hash(n, 66))
        return s

    # ------------------------------------------------------------------ hazards and gates
    def hazard(self, kind: str, w: float, h: float):
        """Thistle brambles: wiry stems with spiny leaves and violet thistle heads."""
        if kind != "thorns":
            return None
        hh = max(h, 16.0)
        s = Svg(w, hh + 4)
        for k in range(3):
            pts = [(lx, hh * (0.48 + 0.17 * k) + 2.6 * math.sin(lx * 0.13 + k * 2)) for lx in [i * w / 12 for i in range(13)]]
            s.path(smooth_open(pts), stroke=["#2c5a34", "#386c3e", "#4a8248"][k], width=3.0 - k * 0.5)
            for i, (lx, ly) in enumerate(pts[:-1]):
                if (i + k) % 2 == 0:
                    s.polygon([(lx - 2.2, ly), (lx - 0.4, ly - 6.5), (lx + 1.0, ly - 2.0), (lx + 2.6, ly - 5.4), (lx + 2.4, ly)], fill="#6fa858",
                              stroke="#1f3a24", width=0.5)
                    s.polygon([(lx - 1.0, ly - 5.5), (lx - 0.2, ly - 8.5), (lx + 0.6, ly - 5.5)], fill="#f2ecd2", stroke=INK, width=0.4)
        for i in range(max(1, int(w / 22))):
            fx = (i + 0.5) * w / max(1, int(w / 22))
            fy = hh * 0.36 + 2 * math.sin(i * 1.7)
            s.path(blob(fx, fy + 2.4, 3.2, 2.6, 0.08, seed=i), fill="#5e9a4e", stroke="#1f3a24", width=0.6)
            for k in range(7):
                a = math.radians(-160 + k * 23)
                s.line(fx, fy, fx + math.cos(a) * 5.0, fy + math.sin(a) * 5.0, "#b05fd8", 1.4)
            s.circle(fx, fy, 2.0, fill="#d690f2")
        return s

    def gate(self, w: float, h: float) -> Svg:
        """Arena gate: bronze bars forged like long feathers between white
        stone posts, cross rails with rivets and a fan of bronze feathers on top."""
        s = Svg(w, h)
        post = min(5.0, w * 0.13)
        crest = min(26.0, h * 0.18)
        s.rect(post, crest, w - 2 * post, h - crest - 6, fill="#1a1d3a", opacity=0.5)
        n = max(3, int((w - 2 * post) // 8))
        bar = 4.4
        for i in range(n):
            x = post + 1.4 + i * (w - 2 * post - 2.8 - bar) / max(1, n - 1)
            cx = x + bar / 2
            s.rect(x, crest - 2, bar, h - crest - 6, fill=s.linear(x, 0, x + bar, 0, [(0, BRONZE_HI), (0.45, BRONZE), (1, BRONZE_DEEP)]),
                   stroke=BRONZE_LINE, width=0.7)
            for y in range(int(crest + 6), int(h - 14), 7):  # feather barbs
                s.line(cx - bar * 0.5, y + 2.2, cx, y, BRONZE_LINE, 0.6, 0.55)
                s.line(cx, y, cx + bar * 0.5, y + 2.2, BRONZE_LINE, 0.6, 0.55)
            s.line(cx, crest, cx, h - 10, "#fff2c8", 0.7, 0.8)
            s.polygon([(x - 0.4, h - 9), (cx, h), (x + bar + 0.4, h - 9)], fill=s.linear(0, h - 9, 0, h, [(0, BRONZE), (1, BRONZE_DEEP)]),
                      stroke=BRONZE_LINE, width=0.7)
        for fx in (0.0, w - post):
            s.rect(fx, crest * 0.6, post, h - crest * 0.6 - 4, fill=s.linear(0, 0, 0, h, [(0, STONE_HI), (0.5, STONE), (1, STONE_DARK)]), stroke=INK,
                   width=0.9)
            for y in range(int(crest) + 10, int(h) - 8, 20):
                s.line(fx + 0.6, y, fx + post - 0.6, y, TILE, 1.4, 0.9)
        for y in (h * 0.44, h * 0.72):
            s.rect(0, y, w, 6, fill=s.linear(0, y, 0, y + 6, [(0, BRONZE_HI), (1, BRONZE_DEEP)]), stroke=INK, width=0.9, rx=1.5)
            for bx in (post / 2, w / 2, w - post / 2):
                s.circle(bx, y + 3, 1.0, fill=BRONZE_LINE)
        # crest: a fan of bronze feathers around a sun boss
        cx, cy = w / 2, crest * 0.95
        for k in range(5):
            a = math.radians(-90 + (k - 2) * 26)
            ln = crest * (0.95 - abs(k - 2) * 0.08)
            tip = (cx + math.cos(a) * ln, cy + math.sin(a) * ln)
            nx, ny = -math.sin(a) * w * 0.07, math.cos(a) * w * 0.07
            s.path(smooth_closed([(cx + nx * 0.4, cy + ny * 0.4), (cx + math.cos(a) * ln * 0.5 + nx, cy + math.sin(a) * ln * 0.5 + ny), tip,
                                  (cx + math.cos(a) * ln * 0.5 - nx, cy + math.sin(a) * ln * 0.5 - ny), (cx - nx * 0.4, cy - ny * 0.4)], 0.5),
                   fill=s.linear(cx, cy, tip[0], tip[1], [(0, BRONZE_DEEP), (0.5, BRONZE), (1, BRONZE_HI)]), stroke=BRONZE_LINE, width=0.7)
            s.line(cx, cy, tip[0], tip[1], BRONZE_LINE, 0.6, 0.7)
        s.rect(0, crest * 0.9, w, 5, fill=s.linear(0, crest * 0.9, 0, crest * 0.9 + 5, [(0, BRONZE_HI), (1, BRONZE_DEEP)]), stroke=INK, width=0.9, rx=1.5)
        s.circle(cx, cy, w * 0.12, fill=s.radial(cx - 1, cy - 1, w * 0.14, [(0, "#fff6d0"), (0.6, "#ffc94a"), (1, BRONZE_DEEP)]), stroke=INK,
                 width=0.8)
        return s

    # ------------------------------------------------------------------ interiors (storm spire, sky citadel)
    def interior(self, variant: str):
        """Indoor halls: the storm spire (lightning outside) and the sky
        citadel / fortress (same family, bright sky outside). Every outdoor
        variant of this world keeps returning None."""
        if variant == "spire":
            return (lambda: self._hall(True)), (lambda: self._colonnade(True))
        if variant in ("fortress", "citadel"):
            return (lambda: self._hall(False)), (lambda: self._colonnade(False))
        return None

    def _hall(self, storm: bool) -> Svg:
        """960×540 backdrop: inside a round stone tower. A spiral stair winds
        around a central column, tall windows show the storm (or the bright
        sky), wind banners stream and the bronze gears of the weather vane
        turn under the roof."""
        s = Svg(960, 540)
        r = Rand(71 if storm else 73)
        wall = ("#1c2140", "#2a3156", "#151a30") if storm else ("#4a4f78", "#5c628c", "#333658")
        s.rect(0, 0, 960, 540, fill=s.linear(0, 0, 0, 540, [(0, wall[0]), (0.55, wall[1]), (1, wall[2])]))
        # curved masonry of a round tower: joints crowd toward the edges
        joint, hi = ("#0c0f22", "#5d6694") if storm else ("#262848", "#9aa0c8")
        for row in range(14):
            y = row * 40 - 8
            s.path(f"M0 {y + 14:.1f} Q480 {y - 6:.1f} 960 {y + 14:.1f}", stroke=joint, width=2.2, opacity=0.6)
            s.path(f"M0 {y + 16.5:.1f} Q480 {y - 3.5:.1f} 960 {y + 16.5:.1f}", stroke=hi, width=1.0, opacity=0.22)
            for col in range(-7, 8):
                theta = (col + (row % 2) * 0.5) * 0.21
                if abs(theta) > 1.5:
                    continue
                x = 480 + 500 * math.sin(theta)
                t = x / 960
                yj = y + 14 - 40 * t * (1 - t)  # on this course's arc; the next one is 40 lower
                s.line(x, yj, x, yj + 40, joint, 2.0, 0.5)
            if r.next() < 0.5:
                bx = r.uniform(60, 900)
                s.rect(bx, y + 14, r.uniform(40, 90), 24, fill="#ffffff" if not storm else "#7a84b8", opacity=0.05)
        windows = ((150.0, 70.0, 360.0, 92.0), (810.0, 70.0, 360.0, 92.0))
        for i, (cx, top, bottom, wd) in enumerate(windows):  # light falling from the windows
            c = "#d8d0ff" if storm else "#fff2d6"
            s.polygon([(cx - wd / 2, bottom - 40), (cx + wd / 2, bottom - 40), (cx + wd / 2 + 150, 540), (cx - wd / 2 + 110, 540)], fill=c,
                      opacity=0.07)
        for i, (cx, top, bottom, wd) in enumerate(windows):
            self._tower_window(s, cx, top, bottom, wd, storm, 5 + i * 3)
        for bx in (300.0, 660.0):
            self._wind_banner(s, bx, 46, 250, 52, int(bx), storm)
        self._gears(s, 480, 64, storm)
        self._spiral_stair(s, 480, 540, 120, storm)
        for lx, ly in ((80.0, 230.0), (880.0, 230.0)):
            _glow(s, lx, ly, 46, "#ffd88a", 0.45 if storm else 0.35)
            s.path(f"M{lx - 7:.1f} {ly - 10:.1f} L{lx + 7:.1f} {ly - 10:.1f} L{lx + 5:.1f} {ly + 9:.1f} L{lx - 5:.1f} {ly + 9:.1f} Z",
                   fill=s.radial(lx, ly, 10, [(0, "#fff6d6"), (0.5, "#ffd27a"), (1, "#e08a2a")]), stroke="#2a1a1a", width=1.4)
            s.path(f"M{lx - 9:.1f} {ly - 10:.1f} L{lx:.1f} {ly - 18:.1f} L{lx + 9:.1f} {ly - 10:.1f} Z", fill=BRONZE_DEEP, stroke="#2a1a1a", width=1.2)
            s.line(lx, ly - 18, lx, ly - 30, "#2a1a1a", 1.6)
        s.rect(0, 400, 960, 140, fill=s.linear(0, 400, 0, 540, [(0, "#b8b4ff" if storm else "#fff0e0", 0), (1, "#b8b4ff" if storm else "#fff0e0", 0.18)]))
        return s

    def _tower_window(self, s: Svg, cx: float, top: float, bottom: float, wd: float, storm: bool, seed: int) -> None:
        """Tall arched window; outside, a storm with lightning, or the open sky."""
        r = Rand(seed)
        x0, x1 = cx - wd / 2, cx + wd / 2
        spring = top + wd * 0.5
        outline = (f"M{x0:.1f} {bottom:.1f} L{x0:.1f} {spring:.1f} Q{x0:.1f} {top:.1f} {cx:.1f} {top:.1f} Q{x1:.1f} {top:.1f} {x1:.1f} {spring:.1f} "
                   f"L{x1:.1f} {bottom:.1f} Z")
        if storm:
            s.path(outline, fill=s.linear(0, top, 0, bottom, [(0, "#0e1230"), (0.6, "#2a2f62"), (1, "#3c3f7a")]))
            for k in range(3):  # lead-grey storm clouds lit from inside
                cy = top + 40 + k * 70
                s.path(blob(cx + r.uniform(-20, 20), cy, wd * 0.6, 22, 0.2, seed=seed + k), fill="#4a4f8a", opacity=0.55)
            bolt = [(cx + 10, top + 10), (cx - 6, top + 70), (cx + 8, top + 76), (cx - 12, top + 150), (cx + 2, top + 154), (cx - 18, top + 240)]
            s.path(_line(bolt), stroke="#c9b8ff", width=9, opacity=0.25)
            s.path(_line(bolt), stroke="#f4f0ff", width=2.6)
            s.path(_line(bolt[:3] + [(cx + 22, top + 110)]), stroke="#f4f0ff", width=1.2, opacity=0.8)
            for _ in range(22):
                x, y = r.uniform(x0 + 4, x1 - 4), r.uniform(top + 20, bottom - 20)
                s.line(x, y, x - 5, y + 14, "#a8b4ff", 0.8, 0.45)
        else:
            s.path(outline, fill=s.linear(0, top, 0, bottom, [(0, "#3d8edc"), (0.6, "#8cc8f0"), (1, "#f6e2cc")]))
            puffs = [(x0 + wd * 0.2, bottom - 40, 22.0), (cx, bottom - 30, 28.0), (x1 - wd * 0.15, bottom - 44, 20.0), (cx - 10, bottom - 60, 18.0)]
            _puffs(s, puffs, shadow_alpha=0.2)
            s.rect(x0, bottom - 22, wd, 22, fill="#f2eef8")
            _float_island(s, cx + 14, top + 120, 40, 26, self.FAR_PAL, seed)
        for k in (1, 2):
            mx = x0 + wd * k / 3
            s.line(mx, spring - 10, mx, bottom, "#0a0c1c", 3.0)
        for y in range(int(spring + 30), int(bottom), 56):
            s.line(x0, y, x1, y, "#0a0c1c", 3.0)
        s.path(outline, stroke="#090b1a", width=14)
        s.path(outline, stroke="#8a90b8" if storm else "#e8e2ea", width=9)
        s.path(outline, stroke="#ffffff", width=1.4, opacity=0.5)
        s.rect(x0 - 16, bottom - 2, wd + 32, 14, fill=s.linear(0, bottom, 0, bottom + 14, [(0, "#e4dce8"), (1, "#7a7498")]), stroke="#090b1a",
               width=1.6, rx=2)
        s.rect(x0 - 16, bottom + 8, wd + 32, 4, fill=TILE, opacity=0.9)

    def _wind_banner(self, s: Svg, x: float, top: float, length: float, wd: float, seed: int, storm: bool) -> None:
        """Long sail-cloth banner hanging from a bronze rod, its tail blown sideways."""
        s.line(x - wd * 0.75, top, x + wd * 0.75, top, "#1a1424", 5)
        s.line(x - wd * 0.75, top - 1, x + wd * 0.75, top - 1, BRONZE, 1.6)
        for ex in (x - wd * 0.75, x + wd * 0.75):
            s.circle(ex, top, 3.6, fill=BRONZE, stroke="#1a1424", width=1.2)
        n = 12
        left, right = [], []
        for i in range(n + 1):
            t = i / n
            sway = math.sin(t * 4.2 + seed) * 6 * t + t * t * 26
            left.append((x - wd / 2 + sway, top + length * t))
            right.append((x + wd / 2 + sway - t * t * 6, top + length * t))
        tail = (left[-1][0] + wd * 0.5 + 8, top + length - wd * 0.35)
        d = smooth_open(left) + f"L{tail[0]:.1f} {tail[1]:.1f}" + "L" + smooth_open(list(reversed(right)))[1:] + "Z"
        cloth = s.linear(x - wd / 2, 0, x + wd / 2 + 30, 0, [(0, "#fffaf0"), (0.55, "#e8e0ec"), (1, "#b8b0cc")])
        s.path(d, fill=cloth, stroke="#1a1424", width=2.0, opacity=0.95 if not storm else 0.85)
        s.path(smooth_open([(px + 4, py) for px, py in left[:-1]]), stroke=TILE, width=3.2)
        s.path(smooth_open([(px - 4, py) for px, py in right[:-1]]), stroke=TILE, width=3.2)
        ex, ey = left[5][0] + wd / 2, left[5][1]
        self._feather_emblem(s, ex, ey, wd * 0.3)

    def _feather_emblem(self, s: Svg, x: float, y: float, size: float) -> None:
        """Sun disc crossed by a feather (the world's emblem, also on reward crates)."""
        s.circle(x, y, size * 0.62, fill=s.radial(x - size * 0.2, y - size * 0.2, size * 0.8, [(0, "#fff6c8"), (0.6, "#ffc94a"), (1, "#e88a2a")]),
                 stroke=INK, width=max(0.6, size * 0.06))
        for k in range(8):
            a = k * math.pi / 4 + math.pi / 8
            s.polygon([(x + math.cos(a - 0.16) * size * 0.66, y + math.sin(a - 0.16) * size * 0.66), (x + math.cos(a) * size * 0.95, y + math.sin(a) * size * 0.95),
                       (x + math.cos(a + 0.16) * size * 0.66, y + math.sin(a + 0.16) * size * 0.66)], fill="#ffc94a", stroke=INK, width=max(0.4, size * 0.04))
        fx0, fy0, fx1, fy1 = x - size * 0.75, y + size * 0.85, x + size * 0.8, y - size * 0.95
        mx, my = (fx0 + fx1) / 2, (fy0 + fy1) / 2
        nx, ny = (fy1 - fy0) * 0.17, -(fx1 - fx0) * 0.17
        vane = smooth_closed([(fx0 + (fx1 - fx0) * 0.2, fy0 + (fy1 - fy0) * 0.2), (mx + nx, my + ny), (fx1, fy1), (mx - nx * 0.8, my - ny * 0.8)], 0.8)
        s.path(vane, fill=s.linear(fx0, fy0, fx1, fy1, [(0, "#d6e8ff"), (0.5, "#ffffff"), (1, "#8fc4ff")]), stroke=INK, width=max(0.5, size * 0.05))
        s.line(fx0, fy0, fx1, fy1, "#5a6a9a", max(0.5, size * 0.05))

    def _gears(self, s: Svg, x: float, y: float, storm: bool) -> None:
        """Bronze gear train of the weather vane, under the roof."""
        s.rect(x - 4, 0, 8, y, fill="#2a1e1e")
        for gx, gy, rad, teeth, ph in ((x, y, 46.0, 14, 0.0), (x - 74, y + 22, 30.0, 10, 0.18), (x + 70, y + 30, 24.0, 8, 0.1)):
            pts = []
            for k in range(teeth * 2):
                a0 = 2 * math.pi * k / (teeth * 2) + ph
                for j, a in enumerate((a0 - 0.08, a0 + 0.08)):
                    rr = rad if k % 2 == 0 else rad * 0.84
                    pts.append((gx + math.cos(a) * rr, gy + math.sin(a) * rr))
            s.polygon(pts, fill=s.radial(gx - rad * 0.3, gy - rad * 0.3, rad * 1.4, [(0, BRONZE_HI), (0.5, BRONZE), (1, BRONZE_DEEP)]),
                      stroke="#1a1010", width=1.6, opacity=0.9 if storm else 1.0)
            s.circle(gx, gy, rad * 0.62, fill="#3a2418", opacity=0.5)
            for k in range(5):
                a = 2 * math.pi * k / 5 + ph
                s.line(gx, gy, gx + math.cos(a) * rad * 0.62, gy + math.sin(a) * rad * 0.62, BRONZE, rad * 0.12)
            s.circle(gx, gy, rad * 0.18, fill=BRONZE_HI, stroke="#1a1010", width=1.2)

    def _spiral_stair(self, s: Svg, cx: float, base: float, rad: float, storm: bool) -> None:
        """Stone steps spiralling around a central column (back half first)."""
        col = s.linear(cx - 26, 0, cx + 26, 0, [(0, "#8a86aa" if not storm else "#4a4e78"), (0.4, "#c8c2d8" if not storm else "#6c7098"),
                                                  (1, "#4a4668" if not storm else "#262a48")])
        steps = []
        for i in range(56):
            phi = i * 0.36
            y = base - 18 - i * 9.0
            if y < 40:
                break
            steps.append((phi, y))
        tread_lit, tread, riser = ("#e8e2ee", "#b8b0cc", "#6e6890") if not storm else ("#8a90b8", "#646a96", "#343a62")

        def draw(phi: float, y: float) -> None:
            a0, a1 = phi - 0.2, phi + 0.2
            p = [(cx + 22 * math.sin(a0), y + 6 * math.cos(a0)), (cx + rad * math.sin(a0), y + 16 * math.cos(a0)),
                 (cx + rad * math.sin(a1), y + 16 * math.cos(a1)), (cx + 22 * math.sin(a1), y + 6 * math.cos(a1))]
            front = math.cos(phi) > 0
            s.polygon(p, fill=tread_lit if front and math.sin(phi) < 0.2 else tread, stroke="#0c0e20", width=1.0)
            if front:
                s.polygon([p[1], p[2], (p[2][0], p[2][1] + 8), (p[1][0], p[1][1] + 8)], fill=riser, stroke="#0c0e20", width=1.0)

        for phi, y in steps:
            if math.cos(phi) <= 0:
                draw(phi, y)
        s.rect(cx - 24, 0, 48, base, fill=col)
        for y in range(20, int(base), 34):
            s.line(cx - 24, y, cx + 24, y, "#1a1830", 1.4, 0.6)
        for phi, y in steps:
            if math.cos(phi) > 0:
                draw(phi, y)
        rail = [(cx + (rad + 2) * math.sin(phi), y - 22 + 16 * math.cos(phi)) for phi, y in steps if math.cos(phi) > 0.05]
        for k in range(1, len(rail)):
            (ax, ay), (bx, by) = rail[k - 1], rail[k]
            if abs(bx - ax) < 60:
                s.line(ax, ay, bx, by, BRONZE if not storm else "#8a6a3a", 1.6, 0.9)

    def _colonnade(self, storm: bool) -> Svg:
        """900×420 layer (scrolls at 0.45×): white stone columns with blue
        tile bands and bronze capitals carrying arches, chimes under the
        arches; tiles horizontally (the arch across the edge is drawn twice)."""
        w, h = 900.0, 420.0
        s = Svg(w, h)
        cols = (150.0, 600.0)
        cw = 64.0
        cap = 70.0
        for a, b in ((-300.0, 150.0), (150.0, 600.0), (600.0, 1050.0)):
            self._arch(s, a + cw / 2 + 8, b - cw / 2 - 8, cap, storm)
        for x in cols:
            self._column(s, x, cap, h, cw, storm)
        return s

    def _arch(self, s: Svg, xa: float, xb: float, spring: float, storm: bool) -> None:
        span = xb - xa
        rise = spring - 4
        thick = 22.0
        ts = [i / 24 for i in range(25)]
        outer = [(xa - 8 + (span + 16) * t, spring - (rise + 4) * math.sin(math.pi * t)) for t in ts]
        inner = [(xa + span * t, spring + thick - (rise - thick + 8) * math.sin(math.pi * t)) for t in ts]
        stone = s.linear(0, 0, 0, spring + thick, [(0, "#d8d0e2" if not storm else "#8a8eb4"), (1, "#8a82a8" if not storm else "#4a4e74")])
        s.path(_poly(outer + list(reversed(inner))), fill=stone, stroke="#0c0e20", width=1.8)
        for t in [i / 12 for i in range(1, 12)]:
            ox, oy = xa - 8 + (span + 16) * t, spring - (rise + 4) * math.sin(math.pi * t)
            ix, iy = xa + span * t, spring + thick - (rise - thick + 8) * math.sin(math.pi * t)
            s.line(ox, oy, ix, iy, "#2a2848", 1.1, 0.7)
        s.path(_line(inner[2:-2]), stroke=TILE, width=2.4, opacity=0.9)
        s.path(_line(outer[1:-1]), stroke="#ffffff", width=1.8, opacity=0.5)
        _chime(s, (xa + xb) / 2, spring + thick - rise + 8 + 12, 30, "#0c0e20", 1.0)

    def _column(self, s: Svg, x: float, cap: float, h: float, cw: float, storm: bool) -> None:
        shaft = s.linear(x - cw / 2, 0, x + cw / 2, 0, [(0, "#a8a2c4" if not storm else "#6a6e98"), (0.3, "#f2ecf4" if not storm else "#9ca0c8"),
                                                        (1, "#5a5478" if not storm else "#2c2f50")])
        s.rect(x - cw / 2, cap + 18, cw, h - cap - 18, fill=shaft, stroke="#0c0e20", width=1.8)
        for fx in (-0.25, 0.0, 0.25):
            s.line(x + fx * cw, cap + 22, x + fx * cw, h - 34, "#3a3658", 1.3, 0.45)
        for y in (cap + 60, h - 90):
            s.rect(x - cw / 2, y, cw, 7, fill=s.linear(0, y, 0, y + 7, [(0, "#8fd0ff"), (1, TILE_DEEP)]), stroke="#0c0e20", width=1.0)
        s.rect(x - cw / 2 - 10, cap, cw + 20, 18, fill=s.linear(0, cap, 0, cap + 18, [(0, BRONZE_HI), (1, BRONZE_DEEP)]), stroke="#0c0e20",
               width=1.8, rx=2)
        for k in range(5):
            s.circle(x - cw / 2 - 4 + (cw + 8) * k / 4, cap + 9, 2.2, fill=BRONZE_HI, stroke="#3a2010", width=0.6)
        s.rect(x - cw / 2 - 8, h - 34, cw + 16, 34, fill=s.linear(0, h - 34, 0, h, [(0, "#d8d0e2" if not storm else "#7a7ea6"), (1, "#5a5478")]),
               stroke="#0c0e20", width=1.8, rx=2)
        sy = cap + 120
        _glow(s, x, sy - 10, 36, "#ffd88a", 0.5)
        s.path(f"M{x - 9:.1f} {sy - 16:.1f} L{x + 9:.1f} {sy - 16:.1f} L{x + 7:.1f} {sy + 6:.1f} L{x - 7:.1f} {sy + 6:.1f} Z",
               fill=s.radial(x, sy - 5, 12, [(0, "#fff6d6"), (0.5, "#ffd27a"), (1, "#e08a2a")]), stroke="#1a1010", width=1.4)
        s.path(f"M{x - 11:.1f} {sy - 16:.1f} L{x:.1f} {sy - 26:.1f} L{x + 11:.1f} {sy - 16:.1f} Z", fill=BRONZE_DEEP, stroke="#1a1010", width=1.2)
        s.rect(x - 9, sy + 6, 18, 3, fill=BRONZE_DEEP, stroke="#1a1010", width=0.8)

    def cave_sky(self) -> Svg:
        """Hollow inside an island: warm violet sandstone vaults lit by
        glowing crystal clusters and a shaft of daylight from a crack above."""
        s = Svg(960, 540)
        r = Rand(77)
        s.rect(0, 0, 960, 540, fill=s.linear(0, 0, 0, 540, [(0, "#1e1628"), (0.45, "#33263f"), (1, "#18121f")]))
        for cx, cy, rad, color in ((230, 330, 230, "#4fd0f0"), (720, 300, 200, "#a98aff"), (500, 470, 180, "#4fc8e8")):
            s.circle(cx, cy, rad, fill=s.radial(cx, cy, rad, [(0, color, 0.26), (1, color, 0)]))
        # opening in the vault with a glimpse of the sky
        hole = [(380, 0), (580, 0), (566, 22), (540, 36), (498, 44), (452, 40), (414, 26)]
        s.path(smooth_closed(hole, 0.5), fill=s.linear(0, 0, 0, 44, [(0, "#4a9be0"), (1, "#bfe2f4")]))
        _puffs(s, [(470.0, 34.0, 14.0), (492.0, 30.0, 12.0), (512.0, 36.0, 10.0)], shadow_alpha=0.0)
        for k in range(3):  # shafts of daylight
            x = 430 + k * 40
            s.polygon([(x, 20), (x + 34, 20), (x + 150 + k * 20, 540), (x + 40 + k * 10, 540)], fill="#fff4dc", opacity=0.06 + 0.02 * (k == 1))
        # vault ribs and back wall formations
        for layer, (color, base, amp) in enumerate((("#2c2136", 330.0, 120.0), ("#3a2c46", 400.0, 90.0), ("#46354f", 470.0, 60.0))):
            pts = [(-20.0, 540.0)] + [(x, base - r.uniform(0.3, 1.0) * amp) for x in range(-20, 1000, 60)] + [(980.0, 540.0)]
            s.path(smooth_closed(pts, 0.55), fill=color)
            s.path(smooth_open(pts[1:-1], 0.55), stroke="#8a6f8e", width=1.6, opacity=0.25 + layer * 0.08)
        ceiling = [(-20.0, 0.0)] + [(x, 40 + r.uniform(0, 50) + 30 * math.sin(x * 0.01)) for x in range(-20, 1000, 50)] + [(980.0, 0.0)]
        s.path(smooth_closed(ceiling, 0.5), fill="#241a2e")
        s.path(_poly(hole + [(380, 0)]), fill=s.linear(0, 0, 0, 44, [(0, "#4a9be0"), (1, "#bfe2f4")]))
        for _ in range(16):  # roots dangling through the vault
            x = r.uniform(20, 940)
            if 360 < x < 600:
                continue
            _dangle(s, x, r.uniform(40, 90), r.uniform(40, 130), int(x), r.uniform(1.6, 3.0), "#7a5a48", "#3a2a28")
        for i in range(10):  # crystal clusters on the floor and ledges
            cx = 50 + i * 96 + r.uniform(-24, 24)
            cy = r.uniform(430, 500)
            tone = r.choice([CRYSTAL, CRYSTAL_LILAC, CRYSTAL])
            _glow(s, cx, cy - 22, 50, tone, 0.3)
            for k in range(r.choice([3, 4, 5])):
                _crystal(s, cx + (k - 2) * 7, cy, -90 + (k - 2) * 18 + r.uniform(-8, 8), r.uniform(22, 54), r.uniform(9, 14), tone, 0.85)
        for _ in range(40):
            px, py = r.uniform(0, 960), r.uniform(60, 500)
            if r.next() < 0.3:
                _sparkle(s, px, py, r.uniform(2, 3.5), 0.6, "#dff8ff")
            else:
                s.circle(px, py, r.uniform(0.8, 1.6), fill="#fff0d8", opacity=r.uniform(0.25, 0.6))
        return s

    # ------------------------------------------------------------------ blocks and platforms
    def block(self, kind: str, w: float, h: float) -> Svg:
        s = Svg(w, h)
        if kind in ("question", "used"):
            used = kind == "used"
            hi, mid, deep = (WICKER_HI, WICKER, WICKER_DEEP) if not used else ("#d6c6aa", "#a8967c", "#6e5e4c")
            s.path(rounded_rect_path(0.6, 0.6, w - 1.2, h - 1.2, 4.5), fill=s.linear(0, 0, 0, h, [(0, hi), (0.5, mid), (1, deep)]), stroke=INK, width=1.3)
            # basket weave: woven bands with stakes showing in alternate cells
            rows = max(3, int((h - 5) / 6))
            rh = (h - 5) / rows
            cols = max(4, int((w - 5) / 6.5))
            cwid = (w - 5) / cols
            for row in range(rows):
                y = 2.5 + row * rh
                s.path(rounded_rect_path(2.4, y + 0.4, w - 4.8, rh - 0.8, rh * 0.45),
                       fill=s.linear(0, y, 0, y + rh, [(0, shade(hi, 0.25)), (0.5, mid), (1, shade(deep, 0.1))]), stroke=shade(deep, -0.2), width=0.45)
                for col in range(cols):
                    if (col + row) % 2:
                        x = 2.5 + col * cwid
                        s.rect(x + cwid * 0.28, y + 0.2, cwid * 0.44, rh - 0.4, fill=s.linear(x, 0, x + cwid, 0, [(0, shade(deep, 0.15)), (1, deep)]),
                               rx=0.8)
                s.line(3.2, y + rh * 0.3, w - 3.2, y + rh * 0.3, "#ffffff", 0.5, 0.35)
            s.path(rounded_rect_path(1.8, 1.8, w - 3.6, h - 3.6, 3.6), stroke=shade(deep, -0.15), width=2.0)
            s.path(rounded_rect_path(1.8, 1.8, w - 3.6, h - 3.6, 3.6), stroke=shade(hi, 0.3), width=0.6, opacity=0.8)
            for x in range(4, int(w) - 2, 4):  # braided rim
                s.line(x, 0.9, x + 2, 2.8, shade(deep, -0.2), 0.6, 0.7)
                s.line(x, h - 2.8, x + 2, h - 0.9, shade(deep, -0.2), 0.6, 0.7)
            if not used:
                cx, cy = w / 2, h / 2
                size = min(w, h) * 0.36
                s.circle(cx, cy, size * 1.4, fill=s.radial(cx, cy, size * 1.4, [(0, "#fff3c0", 0.9), (0.6, "#ffd27a", 0.35), (1, "#ffd27a", 0)]))
                self._feather_emblem(s, cx, cy, size)
            else:
                cx, cy = w / 2, h / 2
                s.circle(cx, cy, min(w, h) * 0.24, fill="#8a7a64", opacity=0.6)
                s.circle(cx, cy, min(w, h) * 0.24, stroke="#5a4a3a", width=0.8, opacity=0.8)
                for k in range(4):
                    a = math.radians(45 + k * 90)
                    s.circle(cx + math.cos(a) * min(w, h) * 0.32, cy + math.sin(a) * min(w, h) * 0.32, 0.9, fill="#4a3a2a")
        elif kind == "brick":
            s.path(rounded_rect_path(0.6, 0.6, w - 1.2, h - 1.2, 3), fill=MORTAR, stroke=INK, width=1.2)
            trim = 3.2
            rows = 2
            rh = (h - 2 * trim - 1.2) / rows
            for row in range(rows):
                y = trim + 0.6 + row * rh
                x = -(0 if row % 2 == 0 else 10)
                while x < w:
                    bx0, bx1 = max(1.4, x + 1.0), min(w - 1.4, x + 20 - 1.0)
                    if bx1 > bx0 + 2:
                        tone = mix(STONE_DARK, STONE_HI, 0.55 + 0.35 * _hash(int(x * 3 + row * 17), 3))
                        s.path(rounded_rect_path(bx0, y + 0.8, bx1 - bx0, rh - 1.6, 1.6),
                               fill=s.linear(0, y, 0, y + rh, [(0, shade(tone, 0.5)), (0.3, tone), (1, shade(tone, -0.12))]), stroke="#8a7e98", width=0.6)
                        s.line(bx0 + 1, y + 1.8, bx1 - 1, y + 1.8, "#ffffff", 0.8, 0.8)
                    x += 20
            for y in (0.6, h - trim - 0.6):  # blue glazed trim with white dots
                s.path(rounded_rect_path(0.6, y, w - 1.2, trim, 1.4), fill=s.linear(0, y, 0, y + trim, [(0, "#8fd0ff"), (0.5, TILE), (1, TILE_DEEP)]))
                for x in range(5, int(w) - 3, 10):
                    s.circle(x, y + trim / 2, 0.7, fill="#ffffff", opacity=0.9)
            s.path(rounded_rect_path(0.6, 0.6, w - 1.2, h - 1.2, 3), stroke=INK, width=1.2)
        return s

    def platform(self, kind: str, w: float, h: float, style: str = "") -> Svg:
        if kind == "ledge":
            if "fortress" in style:
                return self._fortress(w, h, int(w * 7 + h), True, True, True, 0.0, "ice" if "ice" in style else "normal")
            if "cloud" in style:
                return self._cloud_mass(w, h, True, True, True, 0.0)
            return self._islet(w, h, wet="ice" in style, floating=style != "")
        if kind == "moving":
            return self._skiff(w, h)
        if kind == "crumble":
            return self._crumble_cloud(w, h)
        if kind == "semisolid":
            if "cloud" in style:
                return self._cloud_semisolid(w, h)
            if style in ("root", "branch"):
                return self._root_semisolid(w, h, style == "branch")
            return self._bridge_planks(w, h)
        if kind == "spring":
            return self._cushion(w, h)
        return self._sail_belt(w, h)  # conveyor (and any other fallback)

    def _islet(self, w: float, h: float, wet: bool, floating: bool) -> Svg:
        """Rock outcrop / tiny floating islet: the turf (or wet rock) cap and a
        body that tapers inside the collision box, with a short point, roots
        and a crystal hanging below."""
        hr = self.terrain_headroom
        s = Svg(w, h + hr + 22)
        r = Rand(int(w * 13 + h))
        y0, y1 = hr, hr + h
        cut = min(h * 0.55, 12.0) if floating else min(h * 0.35, 7.0)
        tip_depth = 8.0 if floating else 3.0
        tipx = w * r.uniform(0.42, 0.58)
        pts = [(0.0, y0 + 1), (0.4, y0 + h * 0.4)]
        n = max(6, int(w / 8))
        for i in range(n + 1):
            t = i / n
            x = cut * 1.6 + (w - cut * 3.2) * t
            k = max(0.0, 1 - abs(x - tipx) / (w * 0.5))
            pts.append((x, y1 - cut + cut * math.sin(math.pi * t) ** 0.6 + tip_depth * k ** 3 + r.uniform(-0.8, 0.8)))
        pts += [(w - 0.4, y0 + h * 0.4), (w, y0 + 1)]
        s.path(_poly(pts), fill=s.linear(0, y0, 0, y1 + tip_depth, [(0, ROCK_TOP), (0.35, ROCK), (0.75, ROCK_LOW), (1, ROCK_UNDER)]))
        s.path(_poly(pts), fill=s.linear(0, 0, w, 0, [(0, "#ffffff", 0.3), (0.4, "#ffffff", 0), (0.7, "#5f5482", 0), (1, "#5f5482", 0.3)]))
        under = pts[1:-1]
        s.path(_line([(x, y - 2.2) for x, y in under[1:-1]]), stroke="#efeaff", width=1.3, opacity=0.6)
        s.path(_line(under), stroke=ROCK_LINE, width=1.3)
        for k in range(2):
            y = y0 + 9 + k * 6
            if y < y1 - cut:
                s.path(_line([(x, y + 1.2 * math.sin(x * 0.2 + k)) for x in _samples(w - 8, 4.0)]), stroke=ROCK_LINE, width=0.9, opacity=0.2)
        for k, fx in enumerate((0.3, 0.62, 0.8)):
            x = w * fx + r.uniform(-4, 4)
            depth = max(0.0, 1 - abs(x - tipx) / (w * 0.5))
            t = min(1.0, max(0.0, (x - cut * 1.6) / max(1.0, w - cut * 3.2)))
            yb = y1 - cut + cut * math.sin(math.pi * t) ** 0.6 + tip_depth * depth ** 3
            _dangle(s, x, yb - 1.5, r.uniform(6, 14) if floating else r.uniform(4, 8), int(x * 3) + k, 0.9)
        if floating:
            _cluster(s, tipx, y1 + tip_depth - 2.5, 7, int(w) + 5, CRYSTAL, hanging=True, glow=0.3)
        if wet:
            self._wet_cap(s, r, w, y0, True, True, 0.0)
        else:
            self._grass_cap(s, r, w, y0, True, True, w * 3.0)
        return s

    def _skiff(self, w: float, h: float) -> Svg:
        """Moving platform: a little sky-skiff. Plank deck on a white hull with
        a blue stripe and portholes; the keel-sail hangs below and fills with
        the wind (sky sailors rig it under the hull to keep the deck clear)."""
        s = Svg(w, h + 30)
        deck = 6.0
        hull_bottom = h + 2.0
        mast_x = w * 0.5
        # keel sail and its rigging (behind the hull)
        sail = (f"M{mast_x + 1:.1f} {hull_bottom - 1:.1f} Q{mast_x + w * 0.22:.1f} {hull_bottom + 6:.1f} {mast_x + w * 0.3:.1f} {h + 25:.1f} "
                f"L{mast_x + 1:.1f} {h + 26:.1f} Z")
        s.line(mast_x, hull_bottom - 2, mast_x, h + 28, "#5a3a24", 2.2)
        s.path(sail, fill=s.linear(mast_x, 0, mast_x + w * 0.3, 0, [(0, SAIL_SHADE), (0.6, SAIL), (1, "#ffffff")]), stroke=INK, width=1.0)
        s.path(f"M{mast_x + 3:.1f} {h + 10:.1f} Q{mast_x + w * 0.14:.1f} {h + 13:.1f} {mast_x + w * 0.2:.1f} {h + 19:.1f}", stroke=SAIL_BLUE, width=3.0)
        s.line(mast_x - 2, h + 26, mast_x + w * 0.3 + 1, h + 25, "#5a3a24", 1.6)
        for ex in (6.0, w - 6.0):
            s.line(ex, hull_bottom - 3, mast_x, h + 27, "#6a5a4a", 0.6, 0.8)
        # hull
        hull = (f"M1.5 {deck - 0.5:.1f} L{w - 1.5:.1f} {deck - 0.5:.1f} Q{w + 1:.1f} {deck + 3:.1f} {w - 6:.1f} {hull_bottom:.1f} "
                f"L8 {hull_bottom:.1f} Q-1 {deck + 3:.1f} 1.5 {deck - 0.5:.1f} Z")
        s.path(hull, fill=s.linear(0, deck, 0, hull_bottom, [(0, "#ffffff"), (0.55, "#ece6f0"), (1, "#b9b0cc")]), stroke=INK, width=1.2)
        s.path(f"M3 {deck + 4:.1f} L{w - 3:.1f} {deck + 4:.1f}", stroke=SAIL_BLUE, width=2.6)
        s.path(f"M5 {deck + 6.2:.1f} L{w - 5:.1f} {deck + 6.2:.1f}", stroke=SAIL_BLUE_DEEP, width=0.7, opacity=0.8)
        for px in [w * k / 5 for k in range(1, 5)]:
            s.circle(px, deck + 9.5, 1.7, fill=s.radial(px - 0.5, deck + 9, 2, [(0, "#e8fbff"), (1, "#4a90c8")]), stroke=BRONZE_LINE, width=0.7)
        # plank deck
        s.path(rounded_rect_path(0.8, 0.8, w - 1.6, deck, 2.4), fill=s.linear(0, 0.8, 0, deck + 0.8, [(0, WOOD_LIGHT), (0.6, WOOD), (1, WOOD_DARK)]),
               stroke=INK, width=1.1)
        for x in range(12, int(w) - 4, 12):
            s.line(x, 1.4, x, deck + 0.4, "#5a3a24", 0.8, 0.7)
        s.line(2.5, 1.7, w - 2.5, 1.7, "#ffe2b8", 0.8, 0.8)
        for ex in (3.0, w - 3.0):  # bronze cleats
            s.circle(ex, deck + 1.0, 1.5, fill=BRONZE, stroke=BRONZE_LINE, width=0.6)
        return s

    def _crumble_cloud(self, w: float, h: float) -> Svg:
        """Dissolving cloud puff: grey-lavender, frayed, with sky showing
        through its tears and wisps falling away below."""
        s = Svg(w, h + 14)
        r = Rand(int(w * 5 + h))
        cell = 16.0
        n = max(3, int(w / cell))
        puffs: list[Puff] = []
        for i in range(n):
            cx = 6 + (w - 12) * (i + 0.5) / n
            rad = r.uniform(6.5, 9.5)
            puffs.append((cx, 2.2 + rad * 0.9, rad))
        tops = _cloud_outline(puffs, 0.5, w - 0.5, h * 0.4)
        lows = []
        for i in range(n * 2 + 1):
            x = w - 0.5 - (w - 1) * i / (n * 2)
            lows.append((x, h - 2.5 + (2.5 if i % 2 else -0.5) + r.uniform(-1, 1)))
        body = tops + lows
        s.path(_poly(body), fill=s.linear(0, 0, 0, h + 2, [(0, "#f2f0f8"), (0.4, "#d6d2e8"), (1, "#a9a4c6")]))
        for cx, cy, rad in puffs:
            s.path(f"M{cx - rad * 0.8:.1f} {cy + rad * 0.2:.1f} Q{cx:.1f} {cy + rad * 0.75:.1f} {cx + rad * 0.85:.1f} {cy + rad * 0.15:.1f}",
                   stroke="#a6a0c4", width=1.2, opacity=0.6)
            s.circle(cx - rad * 0.3, cy - rad * 0.35, rad * 0.35, fill="#ffffff", opacity=0.55)
        for k in range(max(2, int(w / 45))):  # tears with the sky showing through
            x = w * (k + 0.5) / max(2, int(w / 45)) + r.uniform(-6, 6)
            s.path(f"M{x - 2.5:.1f} {h + 0.5:.1f} L{x + 0.5:.1f} {h * 0.45:.1f} L{x + 3.2:.1f} {h + 0.5:.1f} Z", fill="#9fd0f2", opacity=0.9)
            s.path(f"M{x - 2.5:.1f} {h + 0.5:.1f} L{x + 0.5:.1f} {h * 0.45:.1f} L{x + 3.2:.1f} {h + 0.5:.1f}", stroke="#6f6a98", width=0.8)
        s.path(_line(tops), stroke="#6f6a98", width=1.2)
        s.path(_line([(x, y + 1.2) for x, y in tops]), stroke="#ffffff", width=1.2, opacity=0.8)
        for _ in range(int(w / 9)):  # wisps and droplets falling away
            x = r.uniform(4, w - 4)
            y = r.uniform(h + 1, h + 12)
            s.circle(x, y, r.uniform(0.8, 2.2), fill="#c9c5e0", opacity=max(0.15, 0.8 - (y - h) / 14))
        return s

    def _bridge_planks(self, w: float, h: float) -> Svg:
        """Rope-bridge planks lashed between two ropes; rope loops hang below."""
        s = Svg(w, h + 12)
        r = Rand(int(w * 11 + h))
        deck = min(h, 8.0)
        x = 1.0
        while x < w - 2:
            pw = r.uniform(8.5, 11.0)
            x1 = min(w - 1.0, x + pw)
            tone = r.choice([WOOD_LIGHT, "#d6a873", "#c99a64"])
            s.path(rounded_rect_path(x, 1.0 + r.uniform(-0.3, 0.4), x1 - x - 0.9, deck, 1.6),
                   fill=s.linear(0, 1, 0, deck + 1, [(0, shade(tone, 0.2)), (0.5, tone), (1, WOOD_DARK)]), stroke=INK, width=0.8)
            s.line(x + 1.2, 2.4, x1 - 2, 2.4, "#ffe8c4", 0.7, 0.7)
            x = x1 + 0.2
        for y in (1.2, deck + 0.6):
            s.path(f"M0 {y:.1f} L{w:.1f} {y:.1f}", stroke="#4a3424", width=2.0)
            s.path(f"M0 {y - 0.4:.1f} L{w:.1f} {y - 0.4:.1f}", stroke="#d8b888", width=0.8)
        for lx in range(8, int(w) - 4, 22):  # lashings and hanging loops
            s.line(lx, 0.6, lx, deck + 1.4, "#4a3424", 1.8)
            s.line(lx - 0.5, 0.6, lx - 0.5, deck + 1.4, "#d8b888", 0.6)
            nx = min(w - 2.0, lx + 22.0)
            s.path(f"M{lx:.1f} {deck + 1:.1f} Q{(lx + nx) / 2:.1f} {deck + 10:.1f} {nx:.1f} {deck + 1:.1f}", stroke="#6a4a30", width=1.2, opacity=0.9)
        return s

    def _cloud_semisolid(self, w: float, h: float) -> Svg:
        """Thin walkable cloud you can jump through from below."""
        s = Svg(w, h + 10)
        r = Rand(int(w * 3 + h))
        n = max(3, int(w / 18))
        puffs = [(5 + (w - 10) * (i + 0.5) / n, 2.0 + 6.0, r.uniform(6.0, 8.0)) for i in range(n)]
        tops = _cloud_outline(puffs, 0.5, w - 0.5, h * 0.55)
        lows = [(w - 0.5 - (w - 1) * i / (n * 2), h + 2.5 + (2.0 if i % 2 else -1.0)) for i in range(n * 2 + 1)]
        s.path(_poly(tops + lows), fill=s.linear(0, 0, 0, h + 4, [(0, "#ffffff"), (0.5, "#f0eefa"), (1, "#d2cdea", 0.85)]))
        for cx, cy, rad in puffs:
            s.path(f"M{cx - rad * 0.8:.1f} {cy + rad * 0.3:.1f} Q{cx:.1f} {cy + rad * 0.8:.1f} {cx + rad * 0.85:.1f} {cy + rad * 0.2:.1f}",
                   stroke=CLOUD_SHADE, width=1.2, opacity=0.6)
        s.path(_line(tops), stroke=CLOUD_LINE, width=1.1)
        s.path(_line([(x, y + 1.2) for x, y in tops]), stroke="#ffffff", width=1.4, opacity=0.9)
        return s

    def _root_semisolid(self, w: float, h: float, branch: bool) -> Svg:
        """A thick root (or a bundle of nest branches) to stand on, with rootlets hanging."""
        s = Svg(w, h + 14)
        r = Rand(int(w * 7 + h))
        tone = ("#b08a5c", "#7a5634", "#4a321e") if branch else ("#a8805a", "#7a5838", "#4c3624")
        for k in range(3 if branch else 2):
            pts = [(x, 4 + k * 2.4 + 1.6 * math.sin(x * 0.07 + k * 2.2)) for x in _samples(w, 8.0)]
            s.path(smooth_open(pts), stroke=INK, width=7.6 - k * 1.6)
            s.path(smooth_open(pts), stroke=s.linear(0, 0, 0, 10, [(0, tone[0]), (1, tone[1])]), width=6.0 - k * 1.6)
            s.path(smooth_open([(x, y - 1.6) for x, y in pts]), stroke="#e8c898", width=0.8, opacity=0.6)
        for _ in range(int(w / 16)):
            x = r.uniform(6, w - 6)
            if branch:
                s.path(f"M{x:.1f} 5 L{x + r.uniform(4, 9):.1f} {r.uniform(-1, 2):.1f}", stroke=tone[1], width=1.4)
                s.path(blob(x + 9, 0.5, 2.6, 1.3, 0.1, seed=x), fill="#8fcf6a", stroke="#2f6a2e", width=0.4)
            else:
                _dangle(s, x, 8.5, r.uniform(4, 11), int(x), 0.9, tone[0], tone[2])
        return s

    def _cushion(self, w: float, h: float) -> Svg:
        """Spring: a plump cloud cushion with a stitched sky-blue sash on a bronze cradle."""
        s = Svg(w, h + 10)
        s.path(rounded_rect_path(w * 0.14, h - 4, w * 0.72, 4.5, 1.6), fill=s.linear(0, h - 4, 0, h + 0.5, [(0, BRONZE_HI), (1, BRONZE_DEEP)]),
               stroke=INK, width=1.0)
        coil = [(w / 2 + (w * 0.2 if k % 2 else -w * 0.2), h * 0.5 + (h * 0.44) * k / 5) for k in range(6)]
        s.path(_line(coil), stroke=INK, width=2.6)
        s.path(_line(coil), stroke=BRONZE, width=1.3)
        puffs = [(w * 0.25, h * 0.42, w * 0.2), (w * 0.5, h * 0.33, w * 0.26), (w * 0.75, h * 0.42, w * 0.2)]
        for cx, cy, rad in puffs:
            s.circle(cx, cy, rad + 1.1, fill=INK)
        body = s.linear(0, 0, 0, h * 0.7, [(0, "#ffffff"), (0.6, "#eef2ff"), (1, "#bcd2f2")])
        for cx, cy, rad in puffs:
            s.circle(cx, cy, rad, fill=body)
        s.path(f"M{w * 0.08:.1f} {h * 0.5:.1f} Q{w * 0.5:.1f} {h * 0.66:.1f} {w * 0.92:.1f} {h * 0.5:.1f}", stroke=TILE, width=2.6)
        for k in range(5):
            x = w * (0.18 + 0.16 * k)
            s.line(x, h * 0.52 + 2.2 * math.sin(math.pi * (k + 0.5) / 5), x + 1.2, h * 0.52 + 2.2 * math.sin(math.pi * (k + 0.5) / 5),
                   "#ffffff", 0.8)
        for cx, cy, rad in puffs:
            s.circle(cx - rad * 0.35, cy - rad * 0.4, rad * 0.3, fill="#ffffff", opacity=0.9)
        _sparkle(s, w * 0.72, h * 0.12, 2.2)
        return s

    def _sail_belt(self, w: float, h: float) -> Svg:
        """Conveyor: a belt of striped sail cloth driven by the wind between
        two bronze rollers with pinwheel vanes, on a wooden frame."""
        s = Svg(w, h + 8)
        rad = h / 2
        s.path(rounded_rect_path(rad * 0.6, h * 0.55, w - rad * 1.2, h * 0.45 + 6, 2), fill=s.linear(0, h * 0.5, 0, h + 6, [(0, WOOD), (1, WOOD_DARK)]),
               stroke=INK, width=1.0)
        s.path(rounded_rect_path(0.6, 0.6, w - 1.2, h - 1.2, rad - 0.6), fill=SAIL, stroke=INK, width=1.2)
        x = rad
        k = 0
        while x < w - rad:
            x1 = min(w - rad, x + 9)
            s.polygon([(x, 1.6), (x1, 1.6), (x1 - 4, h - 1.6), (x - 4, h - 1.6)], fill=SAIL_BLUE if k % 2 else "#ffffff")
            x += 9
            k += 1
        s.path(rounded_rect_path(0.6, 0.6, w - 1.2, h - 1.2, rad - 0.6), fill=s.linear(0, 0, 0, h, [(0, "#ffffff", 0.45), (0.5, "#ffffff", 0),
                                                                                                    (1, "#2a2050", 0.3)]))
        s.path(rounded_rect_path(0.6, 0.6, w - 1.2, h - 1.2, rad - 0.6), stroke=INK, width=1.2)
        for cx in (rad, w - rad):
            s.circle(cx, rad, rad * 0.78, fill=s.radial(cx - rad * 0.3, rad * 0.7, rad, [(0, BRONZE_HI), (0.6, BRONZE), (1, BRONZE_DEEP)]),
                     stroke=INK, width=1.0)
            for j in range(4):
                a = j * math.pi / 2 + 0.4
                s.polygon([(cx, rad), (cx + math.cos(a) * rad * 0.7, rad + math.sin(a) * rad * 0.7),
                           (cx + math.cos(a + 0.7) * rad * 0.45, rad + math.sin(a + 0.7) * rad * 0.45)], fill="#ffffff" if j % 2 else CORAL,
                          stroke=INK, width=0.5)
            s.circle(cx, rad, 1.4, fill=BRONZE_DEEP)
        return s

    def pipe(self, w: float, h: float, warp: bool) -> Svg:
        """Carved white-stone wind horn: fluted shaft with bronze rings and a
        flared, bronze-banded mouth; the warp horn glows with a wind spiral."""
        s = Svg(w, h)
        stone = s.linear(4, 0, w - 4, 0, [(0, "#a79fc0"), (0.16, "#efe8ee"), (0.34, "#ffffff"), (0.62, "#e4dce4"), (1, "#8a82a6")])
        s.path(rounded_rect_path(4, 10, w - 8, h - 10, 2), fill=stone, stroke=INK, width=1.3)
        for fx in (0.26, 0.5, 0.74):
            x = 4 + (w - 8) * fx
            s.line(x, 17, x, h - 3, "#9a90b4", 1.2, 0.45)
            s.line(x + 1.3, 17, x + 1.3, h - 3, "#ffffff", 0.8, 0.6)
        if h > 30:
            for ry in (h - 9.0,) if h < 60 else (h - 9.0, 24 + (h - 40) * 0.45):
                s.rect(4.5, ry, w - 9, 4.4, fill=s.linear(4, 0, w - 4, 0, [(0, BRONZE_DEEP), (0.3, BRONZE_HI), (0.6, BRONZE), (1, BRONZE_DEEP)]),
                       stroke=INK, width=0.8)
                for bx in range(9, int(w) - 6, 9):
                    s.circle(bx, ry + 2.2, 0.8, fill=BRONZE_LINE)
        cy = 14 + (h - 14) * 0.5 if h < 44 else 28.0
        if warp:
            _glow(s, w / 2, cy, 14, "#8ff0ff", 0.7)
        spiral = []
        for i in range(30):
            a = i * 0.36
            rr = 1.0 + i * 0.22
            spiral.append((w / 2 + math.cos(a) * rr, cy + math.sin(a) * rr * 0.85))
        s.path(smooth_open(spiral), stroke="#8fe8ff" if warp else "#a49ac0", width=1.6 if warp else 1.2, opacity=1.0 if warp else 0.7)
        if warp:
            s.path(smooth_open(spiral), stroke="#ffffff", width=0.6)
            s.polygon([(w / 2 - 5, cy + 6.5), (w / 2 + 5, cy + 6.5), (w / 2, cy + 11.5)], fill="#ffffff", stroke="#1f6fae", width=0.6)
        rim = s.linear(0.8, 0, w - 0.8, 0, [(0, "#a79fc0"), (0.22, "#f6f0f4"), (0.38, "#ffffff"), (0.64, "#ded6e2"), (1, "#80789e")])
        s.path(f"M0.8 1.5 Q0.8 0.6 2 0.6 L{w - 2:.1f} 0.6 Q{w - 0.8:.1f} 0.6 {w - 0.8:.1f} 1.5 L{w - 3.2:.1f} 14 L3.2 14 Z", fill=rim, stroke=INK,
               width=1.3)
        s.rect(2.4, 8.6, w - 4.8, 4.0, fill=s.linear(2, 0, w - 2, 0, [(0, BRONZE_DEEP), (0.3, BRONZE_HI), (0.6, BRONZE), (1, BRONZE_DEEP)]),
               stroke=INK, width=0.7)
        s.path(f"M3 2.6 Q{w / 2:.1f} 5.2 {w - 3:.1f} 2.6", stroke="#3a3050" if not warp else "#3fd8f0", width=2.2, opacity=0.6)
        s.line(2.5, 1.5, w - 2.5, 1.5, "#ffffff", 0.9, 0.9)
        if warp:
            _glow(s, w / 2, 3, 12, "#bff8ff", 0.6)
        return s

    # ------------------------------------------------------------------ props
    def _flowers(self, seed: int) -> Svg:
        r = Rand(seed)
        s = Svg(60, 30)
        for _ in range(4):
            x = r.uniform(8, 52)
            s.path(f"M{x:.1f} 30 Q{x - 3:.1f} 24 {x - 5:.1f} {r.uniform(20, 24):.1f}", stroke="#4f9a3e", width=1.6)
        for _ in range(8):
            x = r.uniform(5, 55)
            top = r.uniform(5, 17)
            s.path(f"M{x:.1f} 30 Q{x + r.uniform(-2, 3):.1f} {top + 8:.1f} {x + 1:.1f} {top:.1f}", stroke="#4a9a3e", width=1.2)
            color = r.choice(FLOWERS)
            size = 2.3 if color in ("#ffffff", "#ffe57a") else 1.8
            for k in range(5):
                a = k * 2 * math.pi / 5 + x
                s.circle(x + 1 + math.cos(a) * size, top + math.sin(a) * size, size * 0.8, fill=color, stroke=shade(color, -0.4), width=0.4)
            s.circle(x + 1, top, 1.2, fill="#ffb732" if color != "#ffe57a" else "#e8851a")
        return s

    def _chime_post(self) -> Svg:
        s = Svg(48, 112)
        s.path(rounded_rect_path(9, 14, 6, 98, 2), fill=s.linear(9, 0, 15, 0, [(0, WOOD_LIGHT), (1, WOOD_DARK)]), stroke=INK, width=1.1)
        s.path("M12 18 Q22 10 34 14", stroke=INK, width=3.4)
        s.path("M12 18 Q22 10 34 14", stroke=WOOD, width=1.8)
        s.circle(12, 13, 3.2, fill=BRONZE, stroke=INK, width=0.9)
        _chime(s, 33, 14, 30, INK, 1.1)
        for x in (6, 18):
            s.path(f"M{x} 112 Q{x + 2} 104 {x + 5} 101", stroke="#4f9a3e", width=1.6)
        return s

    def _kite_stake(self, seed: int) -> Svg:
        s = Svg(110, 170)
        colors = (CORAL, "#fff1c8") if seed % 2 else (SAIL_BLUE, "#fffaf0")
        kx, ky = 82.0, 34.0
        s.path(f"M12 154 Q40 120 {kx - 2:.1f} {ky + 18:.1f}", stroke="#7a6a5a", width=0.8)
        _kite(s, kx, ky, 26, colors, 22, 62, INK, 1.1)
        s.path(rounded_rect_path(9.5, 148, 5, 22, 1.5), fill=s.linear(9, 0, 15, 0, [(0, WOOD_LIGHT), (1, WOOD_DARK)]), stroke=INK, width=1.0)
        s.path("M9.5 152 L14.5 154 M9.5 156 L14.5 158", stroke="#d8c8a0", width=1.1)
        return s

    def _windsock(self) -> Svg:
        s = Svg(72, 80)
        s.path(rounded_rect_path(8, 8, 4.5, 72, 1.6), fill=s.linear(8, 0, 12.5, 0, [(0, "#f2f2f6"), (1, "#9a98ae")]), stroke=INK, width=1.0)
        s.circle(10.2, 7, 2.6, fill=BRONZE, stroke=INK, width=0.8)
        s.ellipse(14.5, 17, 2.4, 7.2, fill=SAIL_SHADE, stroke=INK, width=0.9)
        sock = [(14.5, 10), (62, 14.5), (63, 21), (14.5, 24)]
        segs = 5
        for k in range(segs):
            t0, t1 = k / segs, (k + 1) / segs
            ax0, ay0 = 14.5 + (62 - 14.5) * t0, 10 + 4.5 * t0
            ax1, ay1 = 14.5 + (62 - 14.5) * t1, 10 + 4.5 * t1
            bx0, by0 = 14.5 + (63 - 14.5) * t0, 24 - 3 * t0
            bx1, by1 = 14.5 + (63 - 14.5) * t1, 24 - 3 * t1
            droop = 2.2 * t0 * t0
            s.polygon([(ax0, ay0 + droop), (ax1, ay1 + droop * 1.4), (bx1, by1 + droop * 1.4), (bx0, by0 + droop)],
                      fill=CORAL if k % 2 == 0 else "#ffffff")
        s.path(_poly([(14.5, 10), (62, 17.7), (63, 26.4), (14.5, 24)]), fill=s.linear(0, 10, 0, 26, [(0, "#ffffff", 0.3), (1, "#3a2050", 0.25)]))
        s.path(_poly([(14.5, 10), (62, 14.5 + 3.1), (63, 21 + 3.1 * 1.4 - 0.4), (14.5, 24)]), stroke=INK, width=0.9)
        return s

    def _feathers(self, seed: int) -> Svg:
        s = Svg(46, 16)
        for k, (x, y, ln, ang, tone) in enumerate(((6, 13, 26, -14, "#ffffff"), (18, 14, 22, -4, "#cfe6ff"))[: 1 + seed % 2 + 1]):
            a = math.radians(ang)
            tx, ty = x + math.cos(a) * ln, y + math.sin(a) * ln
            nx, ny = -math.sin(a) * 3.2, math.cos(a) * 3.2
            vane = smooth_closed([(x + (tx - x) * 0.12, y + (ty - y) * 0.12), (x + (tx - x) * 0.5 + nx, y + (ty - y) * 0.5 + ny), (tx, ty),
                                  (x + (tx - x) * 0.55 - nx, y + (ty - y) * 0.55 - ny)], 0.8)
            s.path(vane, fill=s.linear(x, y, tx, ty, [(0, tone), (0.75, "#ffffff"), (1, SAIL_BLUE if k == 0 else "#ffffff")]), stroke=INK, width=0.7)
            s.line(x, y, tx, ty, "#6a7aa0", 0.8)
        return s

    def _rock(self, seed: int) -> Svg:
        s = Svg(58, 40)
        s.path(blob(29, 27, 26, 13, 0.1, seed=seed, squash_top=1.2), fill=s.radial(20, 17, 34, [(0, ROCK_HI), (0.5, ROCK), (1, ROCK_LOW)]),
               stroke=ROCK_LINE, width=1.2)
        s.path(smooth_open([(12, 29), (26, 25), (36, 31)]), stroke=ROCK_LINE, width=1.0, opacity=0.45)
        s.path(smooth_open([(16, 21), (30, 19), (44, 23)]), stroke="#ffffff", width=1.4, opacity=0.6)
        s.path(blob(22, 15, 11, 3.4, 0.25, seed=seed + 1), fill=s.linear(0, 11, 0, 18, [(0, GRASS_TOP), (1, GRASS_DARK)]), stroke=GRASS_LINE,
               width=0.6)
        if seed % 2:
            _cluster(s, 43, 22, 9, seed + 3, CRYSTAL, glow=0.3)
        return s

    def _crystals(self, seed: int) -> Svg:
        r = Rand(seed)
        s = Svg(56, 58)
        tone = CRYSTAL if seed % 3 else CRYSTAL_LILAC
        _glow(s, 28, 36, 28, tone, 0.5)
        for ang, ln, wd in ((-26, 30, 8), (-4, 46, 10), (18, 36, 8.5), (38, 22, 6.5), (-46, 18, 6))[: 3 + seed % 3]:
            _crystal(s, 28 + ang * 0.12, 52, -90 + ang + r.uniform(-5, 5), ln, wd, tone)
        s.path(blob(28, 53, 20, 4.5, 0.15, seed=seed, squash_top=1.3), fill=s.linear(0, 49, 0, 58, [(0, ROCK), (1, ROCK_LOW)]), stroke=ROCK_LINE,
               width=0.8)
        s.path(blob(20, 50.5, 7, 2.2, 0.2, seed=seed + 2), fill=GRASS, opacity=0.9)
        _sparkle(s, 21, 17, 3.0)
        return s

    def _signpost(self) -> Svg:
        """Blank arrow boards (no lettering) with painted feather pictograms."""
        s = Svg(56, 66)
        s.path(rounded_rect_path(25, 10, 6, 56, 2), fill=s.linear(25, 0, 31, 0, [(0, WOOD_LIGHT), (1, WOOD_DARK)]), stroke=INK, width=1.0)
        for y, d, length in ((14, 1, 24), (30, -1, 20)):
            x0 = 28
            x1 = x0 + d * length
            pts = [(x0 - d * 3, y), (x1, y), (x1 + d * 6, y + 5), (x1, y + 10), (x0 - d * 3, y + 10)]
            s.polygon(pts, fill=s.linear(0, y, 0, y + 10, [(0, "#f2d8a8"), (1, "#c49660")]), stroke=INK, width=1.0)
            fx = (x0 + x1) / 2 + d * 2
            s.path(f"M{fx - 5 * d:.1f} {y + 7.5:.1f} Q{fx:.1f} {y + 1.5:.1f} {fx + 6 * d:.1f} {y + 2.2:.1f} Q{fx + 1 * d:.1f} {y + 6:.1f} "
                   f"{fx - 5 * d:.1f} {y + 7.5:.1f} Z", fill=SAIL_BLUE, opacity=0.9)
            s.circle(x0, y + 5, 1.1, fill=BRONZE_DEEP)
        s.path("M22 66 Q24 60 28 58 Q32 60 34 66", fill=GRASS, stroke=GRASS_LINE, width=0.6)
        return s

    def _bush(self, seed: int) -> Svg:
        """Blossom shrub: round green clumps carrying pale-blue and white flower heads."""
        r = Rand(seed)
        s = Svg(86, 52)
        for cx, cy, rad in ((24, 34, 19), (45, 27, 23), (65, 35, 17)):
            s.path(blob(cx, cy, rad, rad * 0.8, 0.1, seed=cx + seed),
                   fill=s.radial(cx - rad * 0.3, cy - rad * 0.5, rad * 1.5, [(0, "#b6ea86"), (0.6, "#5fb556"), (1, "#3a8a4c")]), stroke=GRASS_LINE,
                   width=1.0)
        for _ in range(6):
            fx, fy = r.uniform(14, 72), r.uniform(14, 36)
            color = r.choice(["#b8dcff", "#ffffff", "#d8c8ff"])
            for k in range(6):
                a = k * math.pi / 3
                s.circle(fx + math.cos(a) * 2.6, fy + math.sin(a) * 2.2, 1.8, fill=color, stroke=shade(color, -0.35), width=0.35)
            s.circle(fx, fy, 1.4, fill=shade(color, -0.2))
        return s

    def _tree(self, seed: int) -> Svg:
        """Wind-swept island tree: the trunk leans and the canopy streams to the right."""
        r = Rand(seed)
        s = Svg(160, 176)
        s.path("M54 176 Q50 140 60 112 Q66 94 82 80 L90 86 Q76 98 72 116 Q66 142 70 176 Z",
               fill=s.linear(50, 0, 90, 0, [(0, "#b08460"), (1, "#5e3e28")]), stroke=INK, width=1.3)
        s.path("M66 116 Q50 104 40 102", stroke=INK, width=3.4)
        s.path("M66 116 Q50 104 40 102", stroke="#8a6040", width=2.0)
        clusters = [(84, 66, 34), (56, 78, 24), (114, 70, 28), (100, 44, 28), (136, 60, 20), (70, 50, 24), (42, 98, 14)]
        for cx, cy, rad in clusters:
            s.path(blob(cx + 2, cy + 6, rad, rad * 0.8, 0.08, seed=cx + seed), fill="#2f7a46")
        for cx, cy, rad in clusters:
            s.path(blob(cx, cy, rad, rad * 0.8, 0.08, seed=cx + seed),
                   fill=s.radial(cx - rad * 0.35, cy - rad * 0.45, rad * 1.5, [(0, "#c8f08e"), (0.55, "#66b858"), (1, "#3a8a4c")]),
                   stroke=GRASS_LINE, width=1.1)
        for _ in range(9):
            fx, fy = r.uniform(40, 145), r.uniform(30, 92)
            s.circle(fx, fy, r.uniform(1.6, 2.4), fill=r.choice(["#ffffff", "#ffe2f0", "#d8ecff"]), stroke="#8a7a9a", width=0.4)
        for k in range(3):  # leaves torn off by the wind
            lx, ly = 140 + k * 7, 40 + k * 14
            s.path(smooth_closed([(lx - 3, ly), (lx, ly - 2), (lx + 3.5, ly), (lx, ly + 1.8)]), fill="#8fd06a", stroke=GRASS_LINE, width=0.5)
        return s

    def props(self) -> dict[str, PropSpec]:
        return {
            "flowers": PropSpec(lambda: self._flowers(4), (30, 30)),
            "flowers_b": PropSpec(lambda: self._flowers(17), (30, 30)),
            "chime": PropSpec(self._chime_post, (12, 111)),
            "kite": PropSpec(lambda: self._kite_stake(1), (12, 169)),
            "kite_b": PropSpec(lambda: self._kite_stake(2), (12, 169)),
            "windsock": PropSpec(self._windsock, (10, 79)),
            "feathers": PropSpec(lambda: self._feathers(1), (22, 14)),
            "rock": PropSpec(lambda: self._rock(2), (29, 38)),
            "rock_b": PropSpec(lambda: self._rock(5), (29, 38)),
            "crystal": PropSpec(lambda: self._crystals(4), (28, 56)),
            "crystal_b": PropSpec(lambda: self._crystals(9), (28, 56)),
            "signpost": PropSpec(self._signpost, (28, 65)),
            "bush_bloom": PropSpec(lambda: self._bush(5), (43, 50)),
            "bush_bloom_b": PropSpec(lambda: self._bush(12), (43, 50)),
            "tree_wind": PropSpec(lambda: self._tree(3), (62, 176)),
        }

    def auto_decor(self, rng, surface_w: float) -> list[tuple[str, float, float, str]]:
        out = []
        x = rng.uniform(40, 120)
        tree = False
        while x < surface_w - 40:
            roll = rng.next()
            if roll < 0.26:
                out.append((rng.choice(["flowers", "flowers_b"]), x, rng.uniform(0.8, 1.1), "mid"))
            elif roll < 0.4:
                out.append((rng.choice(["bush_bloom", "bush_bloom_b"]), x, rng.uniform(0.75, 1.0), "back"))
            elif roll < 0.48:
                out.append((rng.choice(["rock", "rock_b"]), x, rng.uniform(0.6, 0.9), "mid"))
            elif roll < 0.56:
                out.append((rng.choice(["crystal", "crystal_b"]), x, rng.uniform(0.55, 0.8), "mid"))
            elif roll < 0.63:
                out.append(("feathers", x, rng.uniform(0.8, 1.0), "mid"))
            elif roll < 0.7:
                out.append(("chime", x, rng.uniform(0.9, 1.0), "back"))
            elif roll < 0.77:
                out.append((rng.choice(["kite", "kite_b"]), x, rng.uniform(0.85, 1.0), "back"))
            elif roll < 0.83:
                out.append(("windsock", x, rng.uniform(0.85, 1.0), "back"))
            elif roll < 0.88:
                out.append(("signpost", x, 1.0, "back"))
            elif roll < 0.95 and surface_w > 300 and not tree:
                out.append(("tree_wind", x, rng.uniform(0.85, 1.05), "back"))
                tree = True
            x += rng.uniform(110, 220)
        return out

    def weather(self) -> Weather:
        return Weather("petals", 0.42, ("sa_feather", "sa_petal", "sa_feather", "sa_petal_blue"), wind=52.0)


ART_CLASS = SkyArchipelago
