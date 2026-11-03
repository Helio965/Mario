"""Deserto Dourado: golden dunes, sandstone canyons, wind and buried temples.

Identity: a high white sun in the upper right with heat shimmer over the
horizon; hazy mesas, a stepped pyramid and obelisks far away; sweeping dunes
whose sharp crests split a sunlit windward slope from a shaded slip face;
a ruined colonnade, a canyon butte and a palm oasis in the middle distance.
The terrain is a drifted golden sand cap (wind ripples, spill tongues, a
wind-carved undercut) over red sandstone strata with carved glyph friezes.
Indoors: torch-lit tomb rooms (caves) and the pyramid interior (fortress
style): sandstone ashlar with sun-and-wind friezes, a corbelled hall with a
great sun relief, torch-lit columns and slab gates. Props: saguaro, prickly
pear and barrel cacti, date palms, bleached bones, clay pots, broken
columns, an obelisk and a hoodoo. Weather: sand blown by the east wind
(right to left, the same wind that shaped the dunes).

All carved motifs are original abstract glyphs (sun, wind waves, spiral,
rings, stepped terrace, nested diamonds, crescent, frond, beetle).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

from ..svg import Rand, Svg, mix, rounded_rect_path, shade, smooth_closed, smooth_open
from .base import Layer, PropSpec, Weather, WorldArt

INK = "#2b1d2c"
# walkable sand (caps, drifts) and dunes
SAND_HI, SAND_TOP, SAND, SAND_MID, SAND_DEEP = "#fff5d6", "#fbe3a6", "#f2c776", "#e2a95c", "#c88644"
SAND_EDGE = "#6b3820"  # outline of the hanging sand edge
# red sandstone (terrain body, rock props)
ROCK_TOP, ROCK, ROCK_DEEP, ROCK_DARK = "#e2a06a", "#c4704a", "#8f4630", "#55261a"
STRATA = ("#e8b07a", "#c76a40", "#e6ab74", "#a9502f", "#d38452", "#8c4128", "#c56c43", "#7a3622")
CARVE_DARK, CARVE_LIGHT = "#4e1e12", "#ffe3b8"
# pale temple sandstone (blocks, columns, conduits, pyramid)
STONE_HI, STONE, STONE_MID, STONE_DEEP = "#fff0cf", "#f1d3a0", "#d9ac72", "#a8743f"
TURQ, TURQ_DARK, TURQ_LIGHT = "#35ccb8", "#13766d", "#c9fff4"
BRONZE, BRONZE_DARK, BRONZE_LIGHT = "#c7853a", "#653a14", "#ffd892"
LEAF = ("#b3dc6c", "#64a043", "#2e6532")
CACTUS = ("#b4d684", "#5e9c58", "#2c6040")
BONE = ("#fbf1dc", "#e2cca6", "#a89070")
CLAY = ("#f0a072", "#c8643a", "#7e3720")
FLAME = [(0, "#fff8d0"), (0.35, "#ffd060"), (0.75, "#ff8a2a"), (1, "#d8441c")]

SUN = (812.0, 76.0)
SUN_WIND = (0, 2, 1, 4, 8, 3)  # sun, wind waves, spiral, rings, diamonds, terrace


# --------------------------------------------------------------------------- helpers
def _hash(i: int, k: int = 0) -> float:
    """Deterministic value in [0, 1) for an integer grid cell. Patterns that
    must continue across terrain chunks are keyed by world-aligned cells."""
    x = (i * 0x9E3779B1 + k * 0x85EBCA6B + 0x632BE5AB) & 0xFFFFFFFF
    x ^= x >> 15
    x = (x * 0x2C1B3C6D) & 0xFFFFFFFF
    x ^= x >> 12
    x = (x * 0x297A2D39) & 0xFFFFFFFF
    x ^= x >> 15
    return x / 4294967296.0


def _pl(pts: Sequence[tuple[float, float]]) -> str:
    """Polyline path data (no smoothing: exact at world-aligned samples)."""
    return "M" + "L".join(f"{x:.2f} {y:.2f}" for x, y in pts)


def _grid(x0: float, w: float, step: float) -> list[float]:
    """Local x positions on a world-aligned grid, always including both ends,
    so adjacent terrain chunks evaluate the same curve at the same world x."""
    xs = [0.0]
    k = math.floor(x0 / step) + 1
    while True:
        lx = k * step - x0
        if lx >= w - 0.05:
            break
        if lx > 0.05:
            xs.append(lx)
        k += 1
    xs.append(w)
    return xs


def _circle_d(cx: float, cy: float, r: float) -> str:
    return f"M{cx - r:.2f} {cy:.2f}a{r:.2f} {r:.2f} 0 1 0 {2 * r:.2f} 0a{r:.2f} {r:.2f} 0 1 0 {-2 * r:.2f} 0"


def _ellipse_d(cx: float, cy: float, rx: float, ry: float) -> str:
    return f"M{cx - rx:.2f} {cy:.2f}a{rx:.2f} {ry:.2f} 0 1 0 {2 * rx:.2f} 0a{rx:.2f} {ry:.2f} 0 1 0 {-2 * rx:.2f} 0"


def _soft(s: Svg, cx: float, cy: float, rx: float, ry: float, stops) -> None:
    """Soft elliptical glow/shadow (radial gradient squashed by a transform)."""
    with s.group(f"translate({cx:.2f} {cy:.2f}) scale(1 {ry / rx:.4f})"):
        s.circle(0, 0, rx, fill=s.radial(0, 0, rx, stops))


def glyph_d(kind: int, cx: float, cy: float, sz: float) -> str:
    """Original carved motifs used on rock friezes, blocks and walls
    (sun, spiral, wind waves, stepped terrace, rings, beetle, crescent,
    palm frond, nested diamonds). ``sz`` is the half size."""
    k = kind % 9
    if k == 0:  # sun disc with rays
        d = _circle_d(cx, cy, sz * 0.36)
        for j in range(8):
            a = j * math.pi / 4
            d += (f"M{cx + math.cos(a) * sz * 0.58:.2f} {cy + math.sin(a) * sz * 0.58:.2f}"
                  f"L{cx + math.cos(a) * sz * 0.92:.2f} {cy + math.sin(a) * sz * 0.92:.2f}")
        return d
    if k == 1:  # spiral
        pts = [(cx + math.cos(i * 0.55) * sz * 0.92 * i / 20, cy + math.sin(i * 0.55) * sz * 0.92 * i / 20) for i in range(21)]
        return smooth_open(pts)
    if k == 2:  # wind waves
        d = ""
        for dy in (-0.45, 0.0, 0.45):
            d += _pl([(cx - sz * 0.9 + i * sz * 0.3, cy + dy * sz + (0.17 * sz if i % 2 else -0.17 * sz)) for i in range(7)])
        return d
    if k == 3:  # stepped terrace under a sun dot
        u = [(-1, 0.85), (-1, 0.35), (-0.72, 0.35), (-0.72, -0.15), (-0.45, -0.15), (-0.45, -0.6), (0.45, -0.6), (0.45, -0.15),
             (0.72, -0.15), (0.72, 0.35), (1, 0.35), (1, 0.85)]
        return _pl([(cx + a * sz, cy + b * sz) for a, b in u]) + "Z" + _circle_d(cx, cy - 0.86 * sz, sz * 0.1)
    if k == 4:  # rings
        return _circle_d(cx, cy, sz * 0.85) + _circle_d(cx, cy, sz * 0.48) + _circle_d(cx, cy, sz * 0.1)
    if k == 5:  # beetle
        d = _ellipse_d(cx, cy + sz * 0.12, sz * 0.42, sz * 0.56) + _circle_d(cx, cy - sz * 0.62, sz * 0.2)
        d += f"M{cx:.2f} {cy - sz * 0.42:.2f}L{cx:.2f} {cy + sz * 0.66:.2f}"
        for j, yy in enumerate((-0.2, 0.15, 0.5)):
            dx = 0.82 + 0.08 * j
            d += (f"M{cx - sz * 0.4:.2f} {cy + yy * sz:.2f}L{cx - sz * dx:.2f} {cy + (yy - 0.18 + 0.2 * j) * sz:.2f}"
                  f"M{cx + sz * 0.4:.2f} {cy + yy * sz:.2f}L{cx + sz * dx:.2f} {cy + (yy - 0.18 + 0.2 * j) * sz:.2f}")
        return d
    if k == 6:  # crescent over a star point
        return (f"M{cx - sz * 0.2:.2f} {cy - sz * 0.85:.2f}A{sz * 0.75:.2f} {sz * 0.75:.2f} 0 1 0 {cx + sz * 0.62:.2f} {cy + sz * 0.3:.2f}"
                f"A{sz * 0.55:.2f} {sz * 0.55:.2f} 0 1 1 {cx - sz * 0.2:.2f} {cy - sz * 0.85:.2f}Z" + _circle_d(cx + sz * 0.5, cy - sz * 0.5, sz * 0.1))
    if k == 7:  # palm frond
        d = f"M{cx:.2f} {cy + sz * 0.95:.2f}L{cx:.2f} {cy - sz * 0.95:.2f}"
        for j in range(4):
            yy = cy - sz * 0.75 + j * sz * 0.42
            d += _pl([(cx - sz * 0.62, yy + sz * 0.3), (cx, yy), (cx + sz * 0.62, yy + sz * 0.3)])
        return d
    # nested diamonds
    return (_pl([(cx, cy - sz), (cx + sz * 0.8, cy), (cx, cy + sz), (cx - sz * 0.8, cy)]) + "Z"
            + _pl([(cx, cy - sz * 0.45), (cx + sz * 0.36, cy), (cx, cy + sz * 0.45), (cx - sz * 0.36, cy)]) + "Z")


def carve(s: Svg, d: str, width: float, opacity: float = 0.8, dark: str = CARVE_DARK, light: str = CARVE_LIGHT) -> None:
    """Incised line: dark groove plus the groove wall lit by the upper-right
    sun (a light copy offset to the lower left)."""
    with s.group("translate(-0.55 0.55)"):
        s.path(d, stroke=light, width=width, opacity=opacity * 0.6)
    s.path(d, stroke=dark, width=width, opacity=opacity)


def flame(s: Svg, x: float, y: float, size: float, glow: float = 0.0) -> None:
    """Torch flame with an optional warm light pool (radius ``glow``)."""
    if glow:
        s.circle(x, y, glow, fill=s.radial(x, y, glow, [(0, "#ffc070", 0.5), (0.35, "#ff9a40", 0.18), (1, "#ff8a30", 0)]))
    h = size
    s.path(smooth_closed([(x, y - h), (x + h * 0.32, y - h * 0.25), (x + h * 0.22, y + h * 0.22), (x - h * 0.22, y + h * 0.22),
                          (x - h * 0.32, y - h * 0.25)], 0.8), fill=s.radial(x, y, h, FLAME))
    s.path(smooth_closed([(x, y - h * 0.55), (x + h * 0.14, y - h * 0.05), (x, y + h * 0.14), (x - h * 0.14, y - h * 0.05)], 0.8),
           fill="#ffffff", opacity=0.85)


@dataclass(frozen=True)
class Dune:
    """Side-view dune: steep shaded slip face on the left (downwind), gentle
    sunlit windward slope on the right, sharp crest in between."""

    xc: float
    yc: float
    wl: float
    wr: float

    def y(self, x: float, yb: float) -> float:
        hgt = yb - self.yc
        if x <= self.xc:
            u = max(0.0, (x - (self.xc - self.wl)) / self.wl)
            return yb - hgt * u ** 1.8
        v = min(1.0, (x - self.xc) / self.wr)
        return yb - hgt * (1 - v * v * (3 - 2 * v))


def draw_dune(s: Svg, d: Dune, yb: float, lit: tuple[str, str], shadow: tuple[str, str], rim: str, ripple: str,
              ripples: int = 3) -> None:
    xs = [d.xc - d.wl + i * (d.wl / 14) for i in range(15)] + [d.xc + i * (d.wr / 18) for i in range(1, 19)]
    pts = [(x, d.y(x, yb)) for x in xs]
    s.path(_pl(pts) + f"L{d.xc + d.wr:.2f} {yb + 1:.2f}L{d.xc - d.wl:.2f} {yb + 1:.2f}Z",
           fill=s.linear(0, d.yc, 0, yb, [(0, lit[0]), (1, lit[1])]))
    hgt = yb - d.yc
    slip = [p for p in pts if p[0] <= d.xc + 0.01]
    crescent = (_pl(list(reversed(slip))) + f"L{d.xc - d.wl * 0.4:.2f} {yb + 1:.2f}"
                f"Q{d.xc - d.wl * 0.06:.2f} {d.yc + hgt * 0.7:.2f} {d.xc:.2f} {d.yc:.2f}Z")
    s.path(crescent, fill=s.linear(d.xc, d.yc, d.xc - d.wl * 0.6, yb, [(0, shadow[0]), (1, shadow[1])]))
    s.path(_pl([(x, d.y(x, yb) + 0.7) for x in [d.xc + d.wr * 0.04 * i for i in range(10)]]), stroke=rim, width=1.8, opacity=0.9)
    for k in range(ripples):  # wind ripples parallel to the windward slope
        off = 6.0 + k * 7.5
        seg = []
        for i in range(16):
            x = d.xc + d.wr * (0.12 + k * 0.08 + i * 0.045)
            y = d.y(x, yb) + off + 1.1 * math.sin(x * 0.21 + k * 1.7)
            if y < yb - 2:
                seg.append((x, y))
        if len(seg) > 2:
            s.path(_pl(seg), stroke=ripple, width=1.1, opacity=0.38)


class GoldenDesert(WorldArt):
    id = "golden_desert"
    name = "Deserto Dourado"
    accent = "#2f6fd6"  # lapis banner: the complementary note against gold
    terrain_headroom = 14.0
    vignette = 0.22
    provisional = False

    # ------------------------------------------------------------------ sky
    def sky(self) -> Svg:
        s = Svg(960, 540)
        s.rect(0, 0, 960, 540, fill=s.linear(0, 0, 0, 540, [(0, "#3d8dd8"), (0.33, "#7cbfe8"), (0.55, "#c6e2e0"), (0.69, "#f6e6c0"),
                                                             (0.84, "#f7d6a0"), (1, "#efc188")]))
        sx, sy = SUN
        _soft(s, sx - 60, sy + 40, 760, 470, [(0, "#fff8e8", 0.55), (0.45, "#fff0d4", 0.2), (1, "#ffe6c0", 0)])
        s.circle(sx, sy, 230, fill=s.radial(sx, sy, 230, [(0, "#fffef8", 0.95), (0.15, "#fffaea", 0.7), (0.38, "#fff4dc", 0.26),
                                                          (1, "#fff0d0", 0)]))
        for k in range(12):
            a = math.radians(98 + k * 7.4)
            spread = 0.016 + 0.01 * (k % 3)
            s.polygon([(sx, sy), (sx + math.cos(a - spread) * 620, sy + math.sin(a - spread) * 620),
                       (sx + math.cos(a + spread) * 620, sy + math.sin(a + spread) * 620)], fill="#fffcf0", opacity=0.035 + 0.015 * (k % 2))
        s.circle(sx, sy, 46, fill=s.radial(sx, sy, 46, [(0, "#ffffff"), (0.66, "#fffefa"), (0.82, "#fff6d8", 0.9), (1, "#ffefc0", 0)]))
        # heat shimmer over the horizon
        for i, (y, a) in enumerate(((300, 0.2), (330, 0.26), (358, 0.3), (386, 0.24))):
            _soft(s, 480, y, 620, 12, [(0, "#fffaf0", a), (0.7, "#fff6e6", a * 0.5), (1, "#fff6e6", 0)])
            pts = [(float(x), y + 1.5 * math.sin(x * 0.043 + i * 1.7) + 0.8 * math.sin(x * 0.131 + i)) for x in range(-20, 1000, 16)]
            s.path(smooth_open(pts), stroke="#fffbf2", width=0.9, opacity=0.14)
        return s

    def _wisp(self, seed: int, w: float, h: float) -> Svg:
        """High cirrus combed by the wind: a soft veil and tapered streaks."""
        r = Rand(seed)
        s = Svg(w, h)
        cy = h * 0.55
        for _ in range(3):
            cx = w * r.uniform(0.35, 0.65)
            rx = min(cx, w - cx) * r.uniform(0.75, 0.95)
            _soft(s, cx, cy + r.uniform(-h * 0.1, h * 0.1), rx, h * r.uniform(0.16, 0.26),
                  [(0, "#ffffff", 0.5), (0.55, "#fffaf2", 0.22), (1, "#ffffff", 0)])
        for _ in range(7):
            y = cy + r.uniform(-h * 0.26, h * 0.22)
            x1, x2 = w * r.uniform(0.04, 0.3), w * r.uniform(0.6, 0.96)
            thick, hook = r.uniform(1.8, 4.2), r.uniform(2, 6)
            mx = x1 + (x2 - x1) * 0.45
            d = (f"M{x1:.1f} {y + hook:.1f} Q{mx:.1f} {y - thick:.1f} {x2:.1f} {y - hook * 0.3:.1f} "
                 f"Q{mx:.1f} {y + thick * 0.5:.1f} {x1:.1f} {y + hook:.1f} Z")
            s.path(d, fill="#ffffff", opacity=r.uniform(0.32, 0.58))
        _soft(s, w * 0.7, cy - h * 0.08, w * 0.22, h * 0.14, [(0, "#fff3d0", 0.4), (1, "#fff3d0", 0)])
        return s

    def _grit(self) -> Svg:
        """Weather particle: tumbling sand grains (the scene tints them)."""
        s = Svg(16, 16)
        for (x, y, rad) in ((5.0, 7.0, 2.0), (10.0, 4.6, 1.5), (11.6, 10.0, 1.8), (6.6, 11.6, 1.3), (2.8, 10.4, 1.0)):
            s.circle(x, y, rad, fill="#fffaf0", stroke="#b89060", width=0.45)
        s.path("M0.6 8.6 Q8 6.6 15.4 3.8", stroke="#ffffff", width=1.0, opacity=0.55)
        return s

    def sky_extras(self) -> dict[str, PropSpec]:
        extras = {
            f"gd.cloud.{i}": PropSpec((lambda i=i, w=w, h=h: self._wisp(61 + i * 13, w, h)), (0, 0))
            for i, (w, h) in enumerate([(300, 54), (220, 44), (360, 62)])
        }
        # sand grains for the weather system (looked up as particle.<name>)
        extras["particle.gd_grit"] = PropSpec(self._grit, (8, 8))
        return extras

    # ------------------------------------------------------------------ parallax layers
    def _mesa(self, s: Svg, xl: float, xr: float, top: float, base: float, lit: str, dark: str, cap: str, haze: str) -> None:
        tall = base - top
        cliff = tall * 0.6
        talus = tall * 0.5
        pts = [(xl - talus, base), (xl - talus * 0.45, base - (tall - cliff) * 0.45), (xl - 3, top + cliff), (xl - 1, top + 5),
               (xl + 3, top)]
        span = xr - xl
        n = max(2, int(span / 18))
        for i in range(1, n):
            pts.append((xl + span * i / n, top + (0.0 if (i * 7) % 3 else 1.2)))
        pts += [(xr - 3, top), (xr + 1, top + 5), (xr + 3, top + cliff), (xr + talus * 0.45, base - (tall - cliff) * 0.45),
                (xr + talus, base)]
        s.path(_pl(pts) + "Z", fill=s.linear(0, top, 0, base, [(0, lit), (0.62, mix(lit, haze, 0.25)), (1, haze)]))
        s.line(xl + 2, top + 0.8, xr - 2, top + 0.8, cap, 1.6, 0.9)
        for k, f in enumerate((0.22, 0.42, 0.62)):
            y = top + cliff * f
            s.line(xl - 1 - f * 2, y, xr + 1 + f * 2, y, dark, 1.1, 0.3 - 0.06 * k)
        for i in range(int(span / 26)):  # erosion gullies
            gx = xl + 10 + i * 26 + (7 if i % 2 else 0)
            if gx < xr - 8:
                s.path(f"M{gx:.1f} {top + 4:.1f} L{gx - 1.5:.1f} {top + cliff * 0.7:.1f} L{gx + 3:.1f} {top + cliff:.1f}",
                       stroke=dark, width=2.2, opacity=0.18)
        # the west flank turns away from the sun
        s.path(_pl([(xl - talus, base), (xl - talus * 0.45, base - (tall - cliff) * 0.45), (xl - 3, top + cliff), (xl - 1, top + 5),
                    (xl + 3, top), (xl + 9, top + 3), (xl + 6, top + cliff), (xl + 2, base)]) + "Z", fill=dark, opacity=0.28)

    def _far(self, idx: int) -> Svg:
        w, h = 1200.0, 300.0
        s = Svg(w, h)
        hz = 172.0  # foot of the mesas (canvas ~397 with the camera on the main ground)
        lit, dark, cap, haze = "#e7b6a0", "#b98a90", "#f8d8c2", "#f4dcc2"
        mesas = [(70, 250, 94), (332, 372, 68), (700, 960, 110), (930, 1110, 128)] if idx == 0 else \
            [(40, 190, 112), (850, 906, 84), (980, 1140, 118)]
        for xl, xr, top in mesas:
            self._mesa(s, xl, xr, top, hz + 4, lit, dark, cap, haze)
        if idx == 0:
            s.path(_pl([(392, hz + 4), (396, 120), (398, 104), (402, 103), (405, 118), (410, hz + 4)]) + "Z",
                   fill=s.linear(0, 100, 0, hz, [(0, lit), (1, haze)]))
            s.rect(540, hz - 12, 86, 14, fill=s.linear(0, hz - 12, 0, hz + 2, [(0, "#e9c0a8"), (1, haze)]))
            for ox, oh in ((562, 70), (598, 52)):
                s.polygon([(ox - 5, hz - 12), (ox - 3.4, hz - 12 - oh), (ox, hz - 18 - oh), (ox + 3.4, hz - 12 - oh), (ox + 5, hz - 12)],
                          fill=s.linear(0, hz - oh, 0, hz, [(0, "#efc6ae"), (1, haze)]))
                s.polygon([(ox - 5, hz - 12), (ox - 3.4, hz - 12 - oh), (ox, hz - 18 - oh), (ox - 0.6, hz - 12)], fill=dark, opacity=0.3)
        else:
            # stepped pyramid (foreshadows the last level) with its shaded west face
            cx, base, half, steps, hgt = 520.0, hz + 4, 158.0, 7, 104.0
            pts = [(cx - half, base)]
            for i in range(steps):
                y = base - hgt * (i + 1) / steps
                x = cx - half + (half - 16) * (i + 1) / steps
                pts += [(x - 4, pts[-1][1]), (x - 4, y)]
            pts += [(cx - 12, base - hgt), (cx + 12, base - hgt)]
            right = [(2 * cx - x, y) for (x, y) in reversed(pts[1:-2])]
            s.path(_pl(pts + right + [(cx + half, base)]) + "Z", fill=s.linear(0, base - hgt, 0, base, [(0, "#f1c9ad"), (1, haze)]))
            s.path(_pl(pts + [(cx, base - hgt), (cx, base)]) + "Z", fill=dark, opacity=0.32)
            for i in range(1, steps):
                y = base - hgt * i / steps
                xx = cx - half + (half - 16) * i / steps - 4
                s.line(xx, y, 2 * cx - xx, y, "#a07070", 1.0, 0.3)
            s.polygon([(cx + 52, base - hgt * 3 / 7), (cx + 70, base - hgt * 3 / 7), (cx + 62, base - hgt * 2 / 7)], fill=haze, opacity=0.9)
            s.rect(cx - 9, base - hgt - 12, 18, 12, fill="#ecc2a8")
            s.rect(cx - 9, base - hgt - 12, 6, 12, fill=dark, opacity=0.3)
        # far dunes seated on the mesa feet (periodic: seamless between strips)
        pts = [(x, hz + 2 - 5 * math.sin(2 * math.pi * x / w * 5) - 3 * math.sin(2 * math.pi * x / w * 11 + 1.0))
               for x in [i * w / 120 for i in range(121)]]
        s.path(_pl(pts) + f"L{w} {h}L0 {h}Z", fill=s.linear(0, hz - 8, 0, h, [(0, "#f6dcb4"), (0.35, "#efcb98"), (1, "#e4b67e")]))
        # mirage: a bright shimmering band at the foot of the mesas
        s.rect(0, hz - 18, w, 30, fill=s.linear(0, hz - 18, 0, hz + 12, [(0, "#fff8ea", 0), (0.5, "#fff8ea", 0.55), (1, "#fff8ea", 0)]))
        for k in range(3):
            y = hz - 9 + k * 6
            pts = [(x, y + 1.2 * math.sin(2 * math.pi * x / w * (13 + 4 * k) + k)) for x in [i * w / 150 for i in range(151)]]
            s.path(_pl(pts), stroke="#fffdf6", width=1.0, opacity=0.36 - 0.08 * k)
        return s

    def _ruined_temple(self, s: Svg, x: float, base: float) -> None:
        lit, dark, haze = "#f2d8b2", "#cba48a", "#f4dcbc"
        s.rect(x - 6, base - 12, 168, 14, fill=s.linear(0, base - 12, 0, base, [(0, lit), (1, haze)]))
        for cx, hgt in ((x + 10, 74), (x + 52, 78), (x + 94, 52), (x + 136, 30)):
            top = base - 12 - hgt
            s.rect(cx, top, 16, hgt, fill=s.linear(cx, 0, cx + 16, 0, [(0, dark), (0.65, lit), (1, mix(lit, dark, 0.4))]))
            for fx in (cx + 4, cx + 8, cx + 12):
                s.line(fx, top + 3, fx, base - 13, dark, 0.8, 0.3)
            if hgt > 60:
                s.rect(cx - 4, top - 7, 24, 7, fill=lit)
                s.rect(cx - 4, top - 7, 24, 2, fill="#fff4e0", opacity=0.8)
            else:
                s.polygon([(cx, top), (cx + 5, top - 4), (cx + 9, top + 1), (cx + 16, top - 3), (cx + 16, top + 4), (cx, top + 4)], fill=lit)
        s.path(_pl([(x + 2, base - 99), (x + 76, base - 99), (x + 80, base - 95), (x + 74, base - 90), (x + 2, base - 90)]) + "Z",
               fill=s.linear(0, base - 99, 0, base - 90, [(0, "#fff2da"), (1, lit)]))
        s.circle(x + 36, base - 94.5, 3, fill=None, stroke=dark, width=1.0, opacity=0.6)
        s.rect(x + 112, base - 22, 30, 12, fill=s.linear(0, base - 22, 0, base - 10, [(0, lit), (1, dark)]), rx=5)

    def _palm_far(self, s: Svg, x: float, base: float, hgt: float, lean: float, leaf: tuple[str, str], trunk: str) -> None:
        tx, ty = x + lean, base - hgt
        s.path(f"M{x - 2.6:.1f} {base:.1f} Q{x + lean * 0.2:.1f} {base - hgt * 0.5:.1f} {tx - 1.4:.1f} {ty:.1f} "
               f"L{tx + 1.4:.1f} {ty:.1f} Q{x + lean * 0.2 + 3:.1f} {base - hgt * 0.5:.1f} {x + 2.6:.1f} {base:.1f} Z", fill=trunk)
        for i in range(1, int(hgt / 9)):
            t = i * 9 / hgt
            px, py = x + lean * t * t, base - hgt * t
            s.line(px - 2.4, py, px + 2.4, py - 0.8, "#6a5040", 0.8, 0.5)
        for k in range(9):
            a = math.radians(-178 + k * 22)
            ln = 24 + 6 * math.sin(k * 1.7)
            droop = 10 + 8 * abs(math.cos(a))
            ex, ey = tx + math.cos(a) * ln, ty + math.sin(a) * ln * 0.45 + droop
            mx, my = tx + math.cos(a) * ln * 0.55, ty + math.sin(a) * ln * 0.5 - 4
            s.path(f"M{tx:.1f} {ty:.1f} Q{mx:.1f} {my - 3.4:.1f} {ex:.1f} {ey:.1f} Q{mx:.1f} {my + 2.6:.1f} {tx:.1f} {ty + 2:.1f} Z",
                   fill=leaf[k % 2])

    def _mid(self, idx: int) -> Svg:
        w, h = 1100.0, 280.0
        s = Svg(w, h)
        back_lit, back_shadow = ("#f8e0b6", "#f2cea0"), ("#e0b596", "#ecc7a2")
        front_lit, front_shadow = ("#f6d096", "#ecbd7e"), ("#d49e74", "#e2b082")
        yb_back, yb_front = 196.0, 262.0
        s.rect(0, yb_back - 2, w, h - yb_back + 2, fill=s.linear(0, yb_back, 0, h, [(0, back_lit[1]), (1, front_lit[1])]))
        if idx == 1:  # a canyon butte closer than the far mesas, behind the back dunes
            self._mesa(s, 742, 990, 58, 200, "#eab28c", "#b88272", "#f8d4b8", "#f2d6b6")
        junction_back = (122.0, 150.0, 230.0)
        backs = [(420.0, 112.0, 170.0, 260.0), (790.0, 124.0, 150.0, 220.0)] if idx == 0 else \
            [(330.0, 122.0, 170.0, 230.0), (640.0, 132.0, 140.0, 200.0)]
        dunes = [Dune(0.0, *junction_back)] + [Dune(*d) for d in backs] + [Dune(w, *junction_back)]
        for d in dunes:
            draw_dune(s, d, yb_back, back_lit, back_shadow, "#fff6e2", "#dcb088", 2)
        if idx == 0:
            self._ruined_temple(s, 560, 166)
            s.path("M520 172 Q600 152 690 160 Q730 164 760 176 L760 200 L520 200 Z", fill=back_lit[0])
        else:
            for ox, oh in ((560, 86), (598, 64)):
                s.polygon([(ox - 7, 150), (ox - 4.6, 150 - oh), (ox, 142 - oh), (ox + 4.6, 150 - oh), (ox + 7, 150)],
                          fill=s.linear(ox - 7, 0, ox + 7, 0, [(0, "#caa086"), (0.6, "#f4d8b0"), (1, "#e4bc94")]))
                s.polygon([(ox - 4.6, 150 - oh), (ox, 142 - oh), (ox + 4.6, 150 - oh)], fill="#ecc070")
                for gy in range(int(150 - oh + 12), 146, 12):
                    s.circle(ox, gy, 1.4, fill="#bc9078", opacity=0.6)
            s.path("M528 158 Q575 140 625 150 Q650 156 668 166 L668 190 L528 190 Z", fill=back_lit[0])
        junction_front = (150.0, 130.0, 210.0)
        fronts = [(330.0, 146.0, 150.0, 240.0), (720.0, 160.0, 140.0, 220.0)] if idx == 0 else \
            [(470.0, 142.0, 160.0, 250.0), (850.0, 156.0, 130.0, 160.0)]
        if idx == 1:  # oasis pocket: palms around a small pool in the trough
            for px, ph, lean in ((222, 78, -9), (252, 96, 6), (292, 66, 11), (318, 52, -4)):
                self._palm_far(s, px, 216, ph, lean, ("#7ea65e", "#5e8a4e"), "#8e7058")
        dunes = [Dune(0.0, *junction_front)] + [Dune(*d) for d in fronts] + [Dune(w, *junction_front)]
        for d in dunes:
            draw_dune(s, d, yb_front, front_lit, front_shadow, "#fff2d6", "#d6a068", 3)
        if idx == 1:
            s.path(_ellipse_d(268, 238, 62, 7), fill=s.linear(0, 231, 0, 245, [(0, "#c6f2ea"), (1, "#62bcb4")]))
            s.path(_ellipse_d(268, 238, 62, 7), stroke="#ecca96", width=1.6)
            s.line(236, 237, 262, 237, "#ffffff", 1.2, 0.8)
            s.line(276, 240, 296, 240, "#ffffff", 1.0, 0.6)
            for rx_ in (212, 220, 316, 324, 330):
                s.path(f"M{rx_} 238 Q{rx_ - 1} 226 {rx_ + 2} 218", stroke="#6f9a52", width=1.6)
        return s

    def _butte(self, s: Svg, x: float, base: float, wd: float, top: float) -> None:
        """Flat-topped sandstone butte half buried in the near dunes."""
        hgt = base - top
        west = [(x - 8, base), (x + 2, top + hgt * 0.66), (x - 1, top + hgt * 0.56), (x + 4, top + hgt * 0.24), (x + 9, top + 6),
                (x + 16, top + 1)]
        crown = [(x + wd * 0.32, top - 1.5), (x + wd * 0.5, top + 1), (x + wd * 0.64, top - 2.5)]
        east = [(x + wd - 14, top + 1), (x + wd - 7, top + 5), (x + wd - 5, top + hgt * 0.3), (x + wd, top + hgt * 0.4),
                (x + wd - 3, top + hgt * 0.72), (x + wd + 10, base)]
        s.path(smooth_closed(west + crown + east + [(x + wd * 0.5, base + 6)], 0.35),
               fill=s.linear(0, top, 0, base, [(0, "#eaae80"), (0.55, "#d48a5e"), (1, "#bf774c")]))
        for k in range(1, 4):
            y = top + hgt * (0.18 + 0.24 * k)
            pts = [(x + 4 + i * (wd - 8) / 6, y + 1.6 * math.sin(i * 1.3 + k)) for i in range(7)]
            s.path(smooth_open(pts), stroke="#9c553a", width=1.4, opacity=0.36)
            s.path(smooth_open([(px, py + 1.6) for px, py in pts]), stroke="#f8c8a0", width=0.9, opacity=0.3)
        for gx, ln in ((x + wd * 0.38, 0.55), (x + wd * 0.7, 0.4)):
            s.path(f"M{gx:.1f} {top + 4:.1f} Q{gx - 3:.1f} {top + hgt * ln * 0.5:.1f} {gx + 1:.1f} {top + hgt * ln:.1f}", stroke="#9c553a",
                   width=2.4, opacity=0.22)
        s.path(smooth_open([(x + 16, top + 2), (x + wd * 0.32, top - 0.5), (x + wd * 0.5, top + 2), (x + wd * 0.64, top - 1.5),
                            (x + wd - 14, top + 2)]), stroke="#ffdcb4", width=1.8, opacity=0.8)
        s.path(_pl(west + [(x + 20, top + 5), (x + 16, base)]) + "Z", fill="#7a3a26", opacity=0.28)
        s.path(_pl(east), stroke="#ffd4a6", width=1.8, opacity=0.5)

    def _saguaro_silhouette(self, s: Svg, x: float, base: float, hgt: float, color: str) -> None:
        s.path(f"M{x} {base} L{x} {base - hgt}", stroke=color, width=7)
        s.path(f"M{x - 1} {base - hgt * 0.45} Q{x - 11} {base - hgt * 0.45} {x - 11} {base - hgt * 0.72}", stroke=color, width=5)
        s.path(f"M{x + 1} {base - hgt * 0.6} Q{x + 10} {base - hgt * 0.6} {x + 10} {base - hgt * 0.82}", stroke=color, width=5)

    def _near(self, idx: int) -> Svg:
        w, h = 900.0, 240.0
        s = Svg(w, h)
        lit, shadow = ("#f0bf78", "#e4a966"), ("#bf7c4c", "#d79a62")
        yb = 150.0
        s.rect(0, yb - 2, w, h - yb + 2, fill=s.linear(0, yb, 0, h, [(0, lit[1]), (0.45, "#cf9058"), (1, "#a96a3e")]))
        junction = (84.0, 110.0, 190.0)
        inner = {
            0: [(300.0, 70.0, 130.0, 210.0), (640.0, 92.0, 120.0, 180.0)],
            1: [(380.0, 76.0, 150.0, 220.0), (720.0, 66.0, 120.0, 150.0)],
            2: [(250.0, 88.0, 120.0, 200.0), (560.0, 72.0, 140.0, 230.0)],
        }[idx]
        if idx == 0:
            self._butte(s, 452, 118, 104, 26)
            # the butte's foot is buried in drifted sand
            s.path("M432 126 Q470 98 506 102 Q540 96 576 126 Z", fill=s.linear(0, 96, 0, 126, [(0, lit[0]), (1, lit[1])]))
            s.path("M446 112 Q472 99 506 103 Q536 98 560 112", stroke="#fff0cc", width=1.6, opacity=0.8)
            self._saguaro_silhouette(s, 222, 92, 54, "#8e9a62")
        elif idx == 1:  # hoodoo: eroded pillar under a wide cap rock
            s.path("M548 112 Q552 70 556 52 Q560 42 566 40 L578 40 Q584 44 586 56 Q590 76 594 112 Z",
                   fill=s.linear(548, 0, 594, 0, [(0, "#b8704e"), (0.6, "#dc9a6c"), (1, "#c27c56")]))
            s.path(smooth_closed([(536, 40), (552, 22), (590, 20), (606, 32), (598, 44), (548, 46)], 0.7),
                   fill=s.linear(0, 18, 0, 46, [(0, "#eab088"), (1, "#a8644a")]))
            s.path("M550 25 Q575 18 600 27", stroke="#ffd6aa", width=1.6, opacity=0.6)
            for y in (60, 76, 92):
                s.line(556 - (y - 60) * 0.12, y, 588 + (y - 60) * 0.1, y, "#8a4a34", 1.2, 0.35)
        else:
            self._saguaro_silhouette(s, 690, 96, 46, "#8e9a62")
        dunes = [Dune(0.0, *junction)] + [Dune(*d) for d in inner] + [Dune(w, *junction)]
        for d in dunes:
            draw_dune(s, d, yb, lit, shadow, "#fff0cc", "#cf9152", 3)
        if idx == 2:  # half-buried rib arcs of some great old beast
            ribs = ""
            for k in range(5):
                bx = 398 + k * 13
                ribs += f"M{bx} {108 - k:.1f} Q{bx + 9} {84 - k * 2:.1f} {bx + 21} {103 - k * 0.5:.1f}"
            spine = "M392 106 Q440 88 478 98"
            for d_, wd_ in ((ribs, 2.2), (spine, 3.0)):
                s.path(d_, stroke="#b49a7a", width=wd_ + 1.6)
                s.path(d_, stroke="#f6ead2", width=wd_)
            s.path("M380 116 Q430 104 486 114 L486 120 L380 120 Z", fill=lit[0])
        r = Rand(71 + idx)
        for _ in range(6):  # sparse dry shrubs on the slopes
            sx = r.uniform(40, w - 40)
            over = [d.y(sx, yb) for d in dunes if d.xc - d.wl <= sx <= d.xc + d.wr]
            sy = min(over) if over else yb
            for k in range(5):
                a = math.radians(-150 + k * 30)
                s.line(sx, sy + 1, sx + math.cos(a) * 6, sy + math.sin(a) * 6, "#9a7a48", 1.0, 0.8)
        # second, darker dune row: only seen down in the pits
        for d in (Dune(0.0, 196.0, 120.0, 200.0), Dune(450.0, 186.0, 160.0, 240.0), Dune(w, 196.0, 120.0, 200.0)):
            draw_dune(s, d, 236.0, ("#d69a5e", "#b8783f"), ("#a8643c", "#b8783f"), "#f2c88e", "#a8683a", 2)
        s.rect(0, 234, w, 6, fill="#b8783f")
        return s

    def layer_art(self) -> dict[str, PropSpec]:
        art: dict[str, PropSpec] = {}
        for i in range(2):
            art[f"gd.far.{i}"] = PropSpec((lambda i=i: self._far(i)), (0, 0))
            art[f"gd.mid.{i}"] = PropSpec((lambda i=i: self._mid(i)), (0, 0))
        for i in range(3):
            art[f"gd.near.{i}"] = PropSpec((lambda i=i: self._near(i)), (0, 0))
        return art

    def layers(self) -> list[Layer]:
        return [
            Layer("far", 0.08, ["gd.far.0", "gd.far.1"], 1200, 70, vertical=0.05),
            Layer("mid", 0.26, ["gd.mid.0", "gd.mid.1"], 1100, 60, vertical=0.15),
            # the near strip reaches below the screen so pits show a dune valley, not sky
            Layer("near", 0.5, ["gd.near.0", "gd.near.1", "gd.near.2"], 900, 110, vertical=0.35),
        ]

    # ------------------------------------------------------------------ terrain
    def terrain(self, style: str, w: float, h: float, seed: int, left: bool, right: bool, top: bool = True, x0: float = 0.0,
                surface: str = "normal") -> Svg:
        """Terrain chunk art. Every pattern that crosses chunk borders (sand
        cap, spill tongues, ripples, strata, glyph friezes, masonry courses)
        is a function of the world x (``x0`` + local x) sampled on a
        world-aligned grid, and only the hanging sand edge is outlined, so
        chunks join seamlessly."""
        if style == "cave":
            return self._tomb_wall(w, h, seed, left, right, x0)
        if style in ("fortress", "temple", "pyramid", "ruins"):
            return self._pyramid_masonry(w, h, seed, left, right, top, x0)
        hr = self.terrain_headroom
        s = Svg(w, h + hr)
        r = Rand(seed)
        y0 = hr
        bottom = h + hr

        def wav(gx: float, k: float) -> float:
            return 0.6 * math.sin(gx * 0.037 + k * 1.9) + 0.4 * math.sin(gx * 0.0113 + k * 3.7)

        def spill(gx: float) -> float:
            """Sand tongues spilling over the rock (world-aligned sites)."""
            j = math.floor(gx / 56.0)
            best = 0.0
            for jj in (j - 1, j, j + 1):
                if _hash(jj, 11) < 0.45:
                    c = jj * 56.0 + 28.0 + (_hash(jj, 12) - 0.5) * 24.0
                    hw = 7.0 + 10.0 * _hash(jj, 13)
                    u = (gx - c) / hw
                    if abs(u) < 1:
                        best = max(best, (5.0 + 11.0 * _hash(jj, 14)) * (1 - u * u) ** 1.6)
            return best

        def drift(gx: float) -> float:
            j = math.floor(gx / 92.0)
            best = 0.0
            for jj in (j - 1, j, j + 1):
                if _hash(jj, 21) < 0.4:
                    c = jj * 92.0 + 46.0 + (_hash(jj, 22) - 0.5) * 40.0
                    u = (gx - c) / (18.0 + 16.0 * _hash(jj, 23))
                    if abs(u) < 1:
                        best = max(best, (1.2 + 1.8 * _hash(jj, 24)) * (1 - u * u) ** 2)
            return best

        def top_y(gx: float) -> float:
            return y0 - 0.9 + 0.55 * math.sin(gx * 0.031 + 0.4) + 0.35 * math.sin(gx * 0.097 + 1.3) - drift(gx)

        def cap_y(gx: float) -> float:
            return y0 + 12.5 + 2.2 * math.sin(gx * 0.047 + 0.8) + 1.3 * math.sin(gx * 0.13 + 2.1) + spill(gx)

        depths = (13.0, 30.0, 46.0, 80.0, 96.0, 118.0, 141.0, 168.0, 198.0, 232.0)

        def strata_y(k: int, gx: float) -> float:
            return y0 + depths[k] + (1.6 + 0.5 * k) * wav(gx, k + 1)

        xs = _grid(x0, w, 4.0)
        xs_rock = _grid(x0, w, 6.0)
        s.rect(0, y0 + 2, w, bottom - y0 - 2, fill=s.linear(0, y0, 0, bottom, [(0, ROCK_TOP), (0.3, ROCK), (0.75, ROCK_DEEP), (1, ROCK_DARK)]))
        for k in range(len(depths) - 1):  # strata bands, each lit along its upper lip
            upper = [(lx, strata_y(k, x0 + lx)) for lx in xs_rock]
            if upper[0][1] > bottom:
                break
            lower = [(lx, min(bottom, strata_y(k + 1, x0 + lx))) for lx in reversed(xs_rock)]
            band = STRATA[k % len(STRATA)]
            ytop, ybot = y0 + depths[k], min(bottom, y0 + depths[k + 1])
            s.path(_pl(upper + lower) + "Z", fill=s.linear(0, ytop, 0, ybot + 2, [(0, shade(band, 0.1)), (0.6, band), (1, shade(band, -0.1))]))
            if k > 0:
                s.path(_pl(upper), stroke=shade(band, -0.42), width=1.2, opacity=0.45)
                s.path(_pl([(x, y + 1.3) for x, y in upper]), stroke=shade(band, 0.42), width=0.9, opacity=0.35)
        for k in (3, 5):  # cross-bedding in the deep red bands
            if y0 + depths[k] > bottom:
                continue
            ya, yb_ = y0 + depths[k] + 3, y0 + depths[k + 1] - 3
            d = ""
            first = math.floor(x0 / 9.0)
            for j in range(first - 2, first + int(w / 9.0) + 3):
                if _hash(j, 31 + k) < 0.55:
                    gx = j * 9.0 - x0
                    d += f"M{gx:.2f} {ya:.2f}L{gx + 7:.2f} {yb_:.2f}"
            if d:
                s.path(d, stroke=shade(STRATA[k], -0.35), width=0.8, opacity=0.2)
        self._glyph_frieze(s, x0, w, y0 + depths[2] + 6, y0 + depths[3] - 6, bottom)
        # fossils, a few pebbles and cracks (chunk-local, never crossing borders)
        for _ in range(max(1, int(w / 120))):
            fx, fy = r.uniform(14, w - 14), r.uniform(y0 + 98, min(bottom - 8, y0 + 160))
            if fy < bottom - 8:
                carve(s, glyph_d(1, fx, fy, r.uniform(3.2, 4.6)), 0.8, 0.45)
        for _ in range(max(1, int(w / 95))):
            px, py = r.uniform(6, w - 6), r.uniform(y0 + 84, bottom - 6)
            pr = r.uniform(1.6, 3.2)
            s.ellipse(px, py, pr * 1.3, pr, fill=s.radial(px + pr * 0.4, py - pr * 0.4, pr * 1.6, [(0, "#f6d2a8"), (1, "#a0603e")]),
                      stroke=ROCK_DARK, width=0.6, opacity=0.8)
        for _ in range(max(1, int(w / 85))):
            cx0 = r.uniform(10, w - 10)
            pts = [(cx0, y0 + r.choice([depths[1], depths[3], depths[4]]))]
            for _k in range(4):
                pts.append((pts[-1][0] + r.uniform(-3, 3), pts[-1][1] + r.uniform(4, 7)))
            s.path(_pl(pts), stroke=ROCK_DARK, width=1.1, opacity=0.4)
        # exposed cliff sides: shaded west face, sunlit east face
        if left:
            s.rect(0, y0, 9, bottom - y0, fill=s.linear(0, 0, 9, 0, [(0, "#3a160c", 0.5), (1, "#3a160c", 0)]))
            s.line(0.7, y0 + 6, 0.7, bottom, ROCK_DARK, 1.4, 0.85)
        if right:
            s.rect(w - 7, y0, 7, bottom - y0, fill=s.linear(w - 7, 0, w, 0, [(0, "#ffd2a0", 0), (1, "#ffd2a0", 0.4)]))
            s.line(w - 0.7, y0 + 6, w - 0.7, bottom, ROCK_DARK, 1.4, 0.85)
        if not top:
            s.path(_pl([(lx, y0 + 0.8) for lx in xs_rock]), stroke=shade(STRATA[0], 0.4), width=1.2, opacity=0.6)
            return s

        # ---- sand cap
        def corner(lx: float) -> float:
            drop = 0.0
            if left and lx < 7:
                drop = 3.2 * (1 - lx / 7) ** 2
            if right and lx > w - 7:
                drop = max(drop, 3.2 * (1 - (w - lx) / 7) ** 2)
            return drop

        top_pts = [(lx, top_y(x0 + lx) + corner(lx)) for lx in xs]
        cap_pts = [(lx, cap_y(x0 + lx)) for lx in xs]
        # wind-carved undercut: the cap overhangs the softer rock below
        under = [(x, y + 6.5) for x, y in reversed(cap_pts)]
        s.path(_pl(cap_pts + under) + "Z", fill=s.linear(0, y0 + 10, 0, y0 + 24, [(0, "#3a160c", 0.5), (1, "#3a160c", 0)]))
        self._tafoni(s, r, w, cap_pts)
        s.path(_pl(top_pts + list(reversed(cap_pts))) + "Z",
               fill=s.linear(0, y0 - 4, 0, y0 + 26, [(0, SAND_HI), (0.14, SAND_TOP), (0.45, SAND), (0.8, SAND_MID), (1, SAND_DEEP)]))
        for row, (depth, cell, phase) in enumerate(((3.6, 11.0, 0.0), (7.6, 13.0, 6.0))):  # wind ripples
            first = math.floor((x0 - phase) / cell)
            dark_d = light_d = ""
            for j in range(first - 1, first + int(w / cell) + 3):
                if _hash(j, 41 + row) > 0.72:
                    continue
                cx = j * cell + phase + (_hash(j, 43 + row) - 0.5) * 4 - x0
                if not (-6 < cx < w + 6):
                    continue
                gy = top_y(cx + x0) + depth + corner(min(max(cx, 0), w))
                if gy > cap_y(cx + x0) - 2.5:
                    continue
                half = 3.2 + 1.6 * _hash(j, 45 + row)
                dark_d += f"M{cx - half:.2f} {gy + 0.4:.2f}Q{cx - half * 0.2:.2f} {gy - 1.4:.2f} {cx + half:.2f} {gy:.2f}"
                light_d += f"M{cx - half:.2f} {gy - 0.5:.2f}Q{cx - half * 0.2:.2f} {gy - 2.3:.2f} {cx + half * 0.7:.2f} {gy - 1.0:.2f}"
            if dark_d:
                s.path(light_d, stroke=SAND_HI, width=0.7, opacity=0.75)
                s.path(dark_d, stroke=SAND_DEEP, width=0.85, opacity=0.5)
        # outline only the hanging edge (never the chunk's vertical borders)
        s.path(_pl(cap_pts), stroke=SAND_EDGE, width=1.2)
        if left:
            s.path(f"M0.6 {top_pts[0][1]:.2f} L0.6 {cap_pts[0][1]:.2f}", stroke=SAND_EDGE, width=1.5)
        if right:
            s.path(f"M{w - 0.6:.2f} {top_pts[-1][1]:.2f} L{w - 0.6:.2f} {cap_pts[-1][1]:.2f}", stroke=SAND_EDGE, width=1.5)
        s.path(_pl(top_pts), stroke=SAND_HI, width=1.5, opacity=0.95)
        for _ in range(int(w / 70)):  # sparse golden grass tufts
            gx = r.uniform(8, w - 8)
            gy = top_y(x0 + gx) + corner(gx) + 0.8
            for k in range(5):
                lean = (k - 2) * 1.4 + r.uniform(-0.6, 0.6)
                bh = r.uniform(3.5, 7.0)
                s.path(f"M{gx + (k - 2) * 0.8:.2f} {gy:.2f} Q{gx + lean * 0.5:.2f} {gy - bh * 0.6:.2f} {gx + lean:.2f} {gy - bh:.2f}",
                       stroke=r.choice(["#c99a48", "#e2b860", "#b08038"]), width=0.9)
        for _ in range(int(w / 60)):  # pebbles resting on the sand
            px = r.uniform(6, w - 6)
            py = top_y(x0 + px) + corner(px) + 0.6
            pr = r.uniform(1.0, 2.0)
            s.ellipse(px, py - pr * 0.5, pr * 1.4, pr, fill=s.radial(px + 0.4, py - pr, pr * 1.6, [(0, "#f2d0a8"), (1, "#a8704a")]),
                      stroke="#7a4a30", width=0.4)
        return s

    def _glyph_frieze(self, s: Svg, x0: float, w: float, ya: float, yb: float, bottom: float) -> None:
        """Weathered inscription bands in the pale stratum: runs of four glyphs
        on a world-aligned 26 u grid (about half of the 5-cell slots carry
        one), in a softly recessed field between two grooves. Some glyphs
        have nearly weathered away."""
        if yb > bottom - 4:
            return
        cell = 26.0
        cy = (ya + yb) / 2
        first = math.floor((x0 - 30) / cell)
        recess = grooves = ""
        glyphs: list[tuple[str, float]] = []
        for j in range(first, first + int((w + 60) / cell) + 2):
            panel, slot = j // 5, j % 5
            if _hash(panel, 7) > 0.5 or slot == 4:
                continue
            gx = j * cell - x0
            x1, x2 = gx - (4.0 if slot == 0 else 0.0), gx + cell + (4.0 if slot == 3 else 0.0)
            recess += f"M{x1:.2f} {ya + 1:.2f}L{x2:.2f} {ya + 1:.2f}L{x2:.2f} {yb - 1:.2f}L{x1:.2f} {yb - 1:.2f}Z"
            grooves += f"M{x1:.2f} {ya:.2f}L{x2:.2f} {ya:.2f}M{x1:.2f} {yb:.2f}L{x2:.2f} {yb:.2f}"
            wear = _hash(j, 9)
            glyphs.append((glyph_d(int(_hash(j, 3) * 9), gx + cell / 2, cy, min(7.5, (yb - ya) / 2 - 3)), 0.18 + 0.42 * wear))
        if not grooves:
            return
        s.path(recess, fill="#5a2414", opacity=0.09)
        carve(s, grooves, 1.0, 0.4)
        for d, op in glyphs:
            carve(s, d, 1.0, op)

    def _tafoni(self, s: Svg, r: Rand, w: float, cap_pts: list[tuple[float, float]]) -> None:
        """Honeycomb weathering pits just under the sand cap."""
        for _ in range(max(1, int(w / 120))):
            cx = r.uniform(14, w - 14)
            near = [y for x, y in cap_pts if abs(x - cx) < 14]
            cap = min(near) if near else cap_pts[0][1]
            for _k in range(r.choice([2, 3, 4])):
                px, py = cx + r.uniform(-9, 9), cap + 9 + r.uniform(0, 7)
                rx, ry = r.uniform(1.6, 3.2), r.uniform(1.2, 2.2)
                s.ellipse(px, py, rx, ry, fill="#5a2416", opacity=0.5)
                s.path(f"M{px - rx:.2f} {py:.2f}Q{px - rx * 0.6:.2f} {py + ry * 1.2:.2f} {px + rx * 0.4:.2f} {py + ry:.2f}",
                       stroke="#f2b88a", width=0.6, opacity=0.6)

    def _courses(self, s: Svg, x0: float, w: float, top_y: float, bottom: float, row_h: float, bw: float, salt: int,
                 hi: str, lo: str, joint: str, skip: Sequence[int] = (), marks: float = 0.0,
                 mark_kinds: Sequence[int] = SUN_WIND) -> None:
        """Ashlar courses keyed to world x, batched for cheap rasterizing: block
        tones as two translucent overlays, one lit and one shaded line per
        course, every joint in a single path. Blocks are never clamped to the
        chunk (the viewport clips them), so a chunk border is not a joint."""
        light = dark = joints = chips = cracks = ""
        lines: list[tuple[float, float]] = []
        marks_d = ""
        row = 0
        while top_y + row * row_h < bottom:
            yy = top_y + row * row_h
            if row in skip:
                row += 1
                continue
            lines.append((yy, min(1.0, row * row_h / 130)))
            joints += f"M0 {yy:.2f}L{w:.2f} {yy:.2f}"
            offset = (row % 2) * bw / 2
            j = math.floor((x0 - offset) / bw)
            gx = j * bw + offset - x0
            while gx < w:
                joints += f"M{gx:.2f} {yy:.2f}L{gx:.2f} {yy + row_h:.2f}"
                k = _hash(j, row * 13 + salt)
                block = f"M{gx:.2f} {yy:.2f}h{bw:.2f}v{row_h:.2f}h{-bw:.2f}Z"
                if k > 0.66:
                    light += block
                elif k < 0.34:
                    dark += block
                if k > 0.93:  # chipped corner
                    chips += f"M{gx + bw:.2f} {yy + 0.8:.2f}l-5 0l5 5Z"
                elif k < 0.07:
                    cracks += _pl([(gx + 9, yy + 2), (gx + 13, yy + row_h * 0.45), (gx + 11, yy + row_h - 3)])
                elif marks and 0.45 < k < 0.45 + marks:  # an isolated carved mark
                    marks_d += glyph_d(mark_kinds[int(k * 1000) % len(mark_kinds)], gx + bw / 2, yy + row_h / 2, min(6.0, row_h * 0.27))
                gx += bw
                j += 1
            row += 1
        if light:
            s.path(light, fill="#fff0d0", opacity=0.1)
        if dark:
            s.path(dark, fill="#2a1408", opacity=0.12)
        for yy, depth_k in lines:
            s.line(0, yy + 2.6, w, yy + 2.6, hi, 1.0, 0.5 * (1 - depth_k * 0.7))
            s.line(0, yy + row_h - 2.2, w, yy + row_h - 2.2, lo, 1.0, 0.3)
        s.path(joints, stroke=joint, width=1.6)
        if chips:
            s.path(chips, fill=joint, opacity=0.7)
        if cracks:
            s.path(cracks, stroke=joint, width=0.9, opacity=0.6)
        if marks_d:
            carve(s, marks_d, 0.85, 0.45)

    def _tomb_wall(self, w: float, h: float, seed: int, left: bool, right: bool, x0: float) -> Svg:
        """Torch-lit tomb masonry for underground rooms (cave style)."""
        hr = self.terrain_headroom
        s = Svg(w, h + hr)
        r = Rand(seed)
        y0 = hr
        bottom = h + hr
        s.rect(0, y0, w, h, fill=s.linear(0, y0, 0, bottom, [(0, "#9a6a46"), (0.18, "#8a5c3c"), (0.5, "#5e3c28"), (1, "#341e14")]))
        row_h = 24.0
        band_rows = (3, 9)  # carved bands break up deep walls
        self._courses(s, x0, w, y0, bottom, row_h, 62.0, 17, "#d8a06e", "#1e0e08", "#2a160c", skip=band_rows, marks=0.06,
                      mark_kinds=(0, 1, 2, 4, 5, 6, 8))
        for row in band_rows:
            yy = y0 + row * row_h
            if yy < bottom:
                k = min(1.0, row * row_h / 130)
                s.rect(0, yy + 0.8, w, row_h - 1.6, fill=s.linear(0, yy, 0, yy + row_h, [(0, mix("#a8764c", "#4a2c1c", k)),
                                                                                      (1, mix("#7a5034", "#2e1a10", k))]))
                carve(s, f"M0 {yy + 3.4:.2f}L{w:.2f} {yy + 3.4:.2f}M0 {yy + row_h - 3.4:.2f}L{w:.2f} {yy + row_h - 3.4:.2f}", 1.0, 0.6,
                      dark="#1e0e08", light="#d8a070")
                cells = ""
                for j in range(math.floor(x0 / 30.0) - 1, math.floor((x0 + w) / 30.0) + 2):
                    cells += glyph_d((0, 2, 5, 4, 1, 8, 6)[int(_hash(j, 61 + row) * 7)], j * 30.0 - x0 + 15, yy + row_h / 2, 6.0)
                carve(s, cells, 1.0, 0.5, dark="#1e0e08", light="#d8a070")
        if left:
            s.rect(0, y0, 6, h, fill=s.linear(0, 0, 6, 0, [(0, "#1e0e08", 0.5), (1, "#1e0e08", 0)]))
            s.line(0.7, y0, 0.7, bottom, INK, 1.4, 0.8)
        if right:
            s.rect(w - 6, y0, 6, h, fill=s.linear(w - 6, 0, w, 0, [(0, "#ffd8a8", 0), (1, "#ffd8a8", 0.3)]))
            s.line(w - 0.7, y0, w - 0.7, bottom, INK, 1.4, 0.8)
        # floor course: the walkable top (always shown: covered flags are per platform, not per chunk)
        s.rect(0, y0 - 1, w, 6, fill=s.linear(0, y0 - 1, 0, y0 + 5, [(0, "#e8c08a"), (1, "#8a5c3c")]))
        s.line(0, y0 - 0.4, w, y0 - 0.4, "#ffe2b0", 1.2, 0.9)
        for _ in range(max(1, int(w / 50))):
            sx = r.uniform(8, w - 8)
            s.path(_ellipse_d(sx, y0 - 0.2, r.uniform(6, 14), r.uniform(1.4, 2.6)), fill=SAND, opacity=0.8)
        s.rect(0, bottom - 5, w, 5, fill=s.linear(0, bottom - 5, 0, bottom, [(0, "#1a0c06", 0), (1, "#1a0c06", 0.55)]))
        return s

    def _pyramid_masonry(self, w: float, h: float, seed: int, left: bool, right: bool, top: bool, x0: float) -> Svg:
        """Pyramid interior (fortress style): big sandstone ashlar courses
        with carved sun-and-wind friezes, torch light from above, sand blown
        in along the floor. Courses, joints and frieze cells are keyed to
        world x, so chunks (and overlapping pieces) line up exactly."""
        hr = self.terrain_headroom
        s = Svg(w, h + hr)
        r = Rand(seed)
        y0 = hr
        bottom = h + hr
        s.rect(0, y0, w, h, fill=s.linear(0, y0, 0, bottom, [(0, "#dcae72"), (0.3, "#c4945e"), (0.65, "#946440"), (1, "#5a3822")]))
        row_h = 22.0
        frieze_rows = (1, 6)
        self._courses(s, x0, w, y0, bottom, row_h, 56.0, 3, "#ffe0b0", "#2e180c", "#3e2414", skip=frieze_rows, marks=0.05)
        for row in frieze_rows:
            yy = y0 + row * row_h
            if yy < bottom:
                self._sun_wind_frieze(s, x0, w, yy, row_h, min(1.0, row * row_h / 130))
        if left:
            s.rect(0, y0, 7, h, fill=s.linear(0, 0, 7, 0, [(0, "#1e0e08", 0.55), (1, "#1e0e08", 0)]))
            s.line(0.7, y0, 0.7, bottom, INK, 1.5, 0.85)
        if right:
            s.rect(w - 6, y0, 6, h, fill=s.linear(w - 6, 0, w, 0, [(0, "#ffe0b0", 0), (1, "#ffe0b0", 0.32)]))
            s.line(w - 0.7, y0, w - 0.7, bottom, INK, 1.5, 0.85)
        if top:  # polished capstones, with sand blown in along the floor
            s.rect(0, y0 - 1, w, 7, fill=s.linear(0, y0 - 1, 0, y0 + 6, [(0, "#fbe2b4"), (1, "#c8965e")]))
            s.line(0, y0 - 0.4, w, y0 - 0.4, "#fff2d6", 1.3, 0.95)
            s.line(0, y0 + 6, w, y0 + 6, "#3e2414", 1.0, 0.6)
            for _ in range(max(1, int(w / 75))):
                sx, sw = r.uniform(14, w - 14), r.uniform(9, 16)
                s.path(f"M{sx - sw:.2f} {y0 + 0.6:.2f} Q{sx - sw * 0.2:.2f} {y0 - 3.2:.2f} {sx + sw:.2f} {y0 + 0.6:.2f} Z",
                       fill=s.linear(0, y0 - 3, 0, y0 + 1, [(0, SAND_TOP), (1, SAND)]), stroke=SAND_MID, width=0.6)
        s.rect(0, bottom - 6, w, 6, fill=s.linear(0, bottom - 6, 0, bottom, [(0, "#1a0c06", 0), (1, "#1a0c06", 0.6)]))
        return s

    def _sun_wind_frieze(self, s: Svg, x0: float, w: float, y: float, hgt: float, depth_k: float) -> None:
        band = mix("#ecc286", "#8a5c36", depth_k * 0.6)
        s.rect(0, y + 0.8, w, hgt - 1.6, fill=s.linear(0, y, 0, y + hgt, [(0, shade(band, 0.12)), (1, shade(band, -0.14))]))
        carve(s, f"M0 {y + 3.4:.2f}L{w:.2f} {y + 3.4:.2f}M0 {y + hgt - 3.4:.2f}L{w:.2f} {y + hgt - 3.4:.2f}", 1.0, 0.7)
        cell = 26.0
        glyphs = dots = ""
        for j in range(math.floor(x0 / cell) - 1, math.floor((x0 + w) / cell) + 2):
            gx = j * cell - x0
            glyphs += glyph_d(SUN_WIND[int(_hash(j, 51) * len(SUN_WIND))], gx + cell / 2, y + hgt / 2, 5.4)
            dots += _circle_d(gx, y + hgt / 2, 0.9)
        carve(s, glyphs, 1.0, 0.75)
        s.path(dots, fill="#4e2a16", opacity=0.6)

    # ------------------------------------------------------------------ blocks and platforms
    def block(self, kind: str, w: float, h: float) -> Svg:
        s = Svg(w, h)
        if kind in ("question", "used"):
            self._sun_block(s, w, h, kind == "used")
        elif kind == "brick":
            self._ashlar(s, w, h)
        else:
            s.path(rounded_rect_path(0.6, 0.6, w - 1.2, h - 1.2, 3), fill=s.linear(0, 0, 0, h, [(0, STONE), (1, STONE_DEEP)]), stroke=INK, width=1.2)
        return s

    def _sun_block(self, s: Svg, w: float, h: float, used: bool) -> None:
        """Sandstone reward block with a carved sun glyph; the gold inlay is
        gone once used."""
        if used:
            stops = [(0, "#d9b68c"), (0.5, "#b88e66"), (1, "#8a6444")]
            edge_light, edge_dark = "#f0d2aa", "#6a4a32"
        else:
            stops = [(0, "#ffe7a2"), (0.4, "#f8c45c"), (1, "#d5862a")]
            edge_light, edge_dark = "#fff6d0", "#9a5418"
        s.path(rounded_rect_path(0.6, 0.6, w - 1.2, h - 1.2, 3.6), fill=s.linear(0, 0, 0, h, stops), stroke=INK, width=1.3)
        s.path(f"M3 {h - 3:.2f} L3 3 L{w - 3:.2f} 3", stroke=edge_light, width=1.1, opacity=0.85)
        s.path(f"M{w - 2.6:.2f} 3 L{w - 2.6:.2f} {h - 2.6:.2f}", stroke=edge_light, width=1.0, opacity=0.55)
        s.path(f"M3 {h - 2.8:.2f} L{w - 3:.2f} {h - 2.8:.2f}", stroke=edge_dark, width=1.3, opacity=0.6)
        carve(s, rounded_rect_path(4.2, 4.2, w - 8.4, h - 8.4, 2.2), 0.8, 0.45 if not used else 0.35, dark=edge_dark, light=edge_light)
        for cx, cy in ((6.2, 6.2), (w - 6.2, 6.2), (6.2, h - 6.2), (w - 6.2, h - 6.2)):
            s.polygon([(cx - 1.3, cy), (cx, cy - 1.3), (cx + 1.3, cy), (cx, cy + 1.3)], fill=edge_dark, opacity=0.55)
        cx, cy, rad = w / 2, h / 2, min(w, h) * 0.32
        rays = ""
        for j in range(12):
            a = j * math.pi / 6
            ln = 1.0 if j % 2 == 0 else 0.78
            rays += (f"M{cx + math.cos(a) * rad * 0.62:.2f} {cy + math.sin(a) * rad * 0.62:.2f}"
                     f"L{cx + math.cos(a) * rad * ln:.2f} {cy + math.sin(a) * rad * ln:.2f}")
        if used:
            carve(s, rays, 1.0, 0.35, dark=edge_dark, light=edge_light)
            s.circle(cx, cy, rad * 0.46, fill=s.radial(cx + 1, cy - 1, rad * 0.5, [(0, "#6a4a32"), (1, "#8a6444")]), stroke=edge_dark, width=0.9)
            s.path(f"M{cx - rad * 0.3:.2f} {cy + rad * 0.32:.2f} Q{cx:.2f} {cy + rad * 0.5:.2f} {cx + rad * 0.34:.2f} {cy + rad * 0.2:.2f}",
                   stroke=edge_light, width=0.7, opacity=0.6)
        else:
            carve(s, rays, 1.3, 0.85, dark="#9a4e12", light="#fff2c8")
            s.circle(cx, cy, rad * 0.5, fill=s.radial(cx - rad * 0.12, cy - rad * 0.14, rad * 0.55,
                                                       [(0, "#ffffff"), (0.45, "#fff3c0"), (1, "#f0a830")]), stroke="#8a4a10", width=0.9)
            s.circle(cx + rad * 0.14, cy - rad * 0.16, rad * 0.14, fill="#ffffff", opacity=0.9)
            s.circle(cx, cy, rad * 0.24, fill=None, stroke="#e08a20", width=0.7, opacity=0.7)

    def _ashlar(self, s: Svg, w: float, h: float) -> None:
        """Breakable sandstone brickwork (pitted cream ashlar, dark mortar)."""
        s.path(rounded_rect_path(0.6, 0.6, w - 1.2, h - 1.2, 2.6), fill="#7a4a2a", stroke=INK, width=1.2)
        rows = 2 if h >= 16 else 1
        rh = (h - 2) / rows
        n = max(2, round(w / 24.0))
        bw = (w - 2) / n
        idx = 0
        for row in range(rows):
            y = 1 + row * rh
            x = 1 - (0.0 if row % 2 == 0 else bw / 2)
            while x < w - 1:
                bx0, bx1 = max(1.6, x + 0.9), min(w - 1.6, x + bw - 0.9)
                if bx1 > bx0 + 2:
                    idx += 1
                    k = _hash(idx, 91)
                    s.path(rounded_rect_path(bx0, y + 0.9, bx1 - bx0, rh - 1.8, 1.8),
                           fill=s.linear(0, y, 0, y + rh, [(0, mix("#fbe4b8", "#f2d09a", k)), (1, "#cf9a60")]), stroke="#8a5632", width=0.6)
                    s.line(bx0 + 1, y + 2.0, bx1 - 1.2, y + 2.0, "#fff4da", 0.9, 0.75)
                    s.line(bx1 - 0.9, y + 2.4, bx1 - 0.9, y + rh - 2.4, "#ffe8c0", 0.7, 0.4)
                    for p in range(2):
                        px = bx0 + 3 + (bx1 - bx0 - 6) * _hash(idx, 92 + p)
                        py = y + 3.5 + (rh - 7) * _hash(idx, 94 + p)
                        s.circle(px, py, 0.7 + 0.5 * _hash(idx, 96 + p), fill="#9a6440", opacity=0.6)
                    if k > 0.7:
                        s.polygon([(bx1, y + rh - 0.9), (bx1 - 3.2, y + rh - 0.9), (bx1, y + rh - 4.0)], fill="#7a4a2a")
                x += bw

    def platform(self, kind: str, w: float, h: float, style: str = "") -> Svg:
        if kind == "ledge":
            return self._ruin_ledge(w, h) if style == "ruin" else self._shelf(w, h)
        s = Svg(w, h + 10)
        if kind == "moving":
            self._floating_slab(s, w, h)
        elif kind == "crumble":
            self._cracked_slab(s, w, h)
        elif kind == "semisolid":
            if style == "palm":
                self._palm_canopy(s, w, h)
            else:
                self._plank_walk(s, w, h)
        elif kind == "spring":
            self._drum(s, w, h)
        else:  # conveyor and any other mechanism: sandstone rollers in a bronze frame
            s.path(rounded_rect_path(0.6, 0.6, w - 1.2, h - 1.2, h / 2), fill=s.linear(0, 0, 0, h, [(0, BRONZE_LIGHT), (1, BRONZE_DARK)]),
                   stroke=INK, width=1.2)
            for x in range(int(h / 2) + 2, int(w - h / 2), 14):
                s.circle(x, h / 2, h * 0.32, fill=s.radial(x + 1, h / 2 - 1, h * 0.35, [(0, STONE_HI), (1, STONE_MID)]), stroke=INK, width=0.8)
        return s

    def _floating_slab(self, s: Svg, w: float, h: float) -> None:
        """Levitating carved slab held up by a turquoise glyph crystal."""
        _soft(s, w / 2, h + 4, w * 0.46, 6, [(0, TURQ_LIGHT, 0.7), (0.5, TURQ, 0.3), (1, TURQ, 0)])
        s.polygon([(w / 2 - 5.5, h - 1.5), (w / 2 + 5.5, h - 1.5), (w / 2, h + 8.5)],
                  fill=s.linear(w / 2 - 5, 0, w / 2 + 5, 0, [(0, TURQ_DARK), (0.55, TURQ_LIGHT), (1, TURQ)]), stroke="#0c4a44", width=0.8)
        s.path(rounded_rect_path(0.8, 1.0, w - 1.6, h - 1.8, 3.2),
               fill=s.linear(0, 0, 0, h, [(0, "#fbe6bc"), (0.3, "#ecc58c"), (1, "#b07a48")]), stroke=INK, width=1.2)
        s.path(f"M3 3.4 L{w - 3:.2f} 3.4", stroke="#fff6dc", width=1.4, opacity=0.9)
        s.path(f"M2.5 {h - 2.6:.2f} L{w - 2.5:.2f} {h - 2.6:.2f}", stroke="#7a4a28", width=1.0, opacity=0.5)
        carve(s, _pl([(10 + i * 5.0, h * 0.62 + (-2.2 if i % 2 else 2.2)) for i in range(int((w - 20) / 5) + 1)]), 0.9, 0.6)
        s.path(_ellipse_d(w / 2, h * 0.6, 5.5, 3.2), fill=s.linear(0, h * 0.6 - 3, 0, h * 0.6 + 3, [(0, TURQ_LIGHT), (1, TURQ_DARK)]),
               stroke="#0c4a44", width=0.8)
        for x in (2.4, w - 9.4):
            s.path(rounded_rect_path(x, 1.8, 7, h - 3.4, 2), fill=s.linear(x, 0, x + 7, 0, [(0, BRONZE_DARK), (0.6, BRONZE_LIGHT), (1, BRONZE)]),
                   stroke=INK, width=0.9)
            s.circle(x + 3.5, h * 0.55, 1.1, fill=BRONZE_DARK)

    def _cracked_slab(self, s: Svg, w: float, h: float) -> None:
        """Dry, sun-bleached sandstone that gives way (cracks, chips, trickles)."""
        r = Rand(int(w * 13 + h))
        for _ in range(3):
            x = r.uniform(10, w - 10)
            ln = r.uniform(4, 9)
            s.path(f"M{x:.2f} {h - 1:.2f} Q{x + 0.6:.2f} {h + ln * 0.5:.2f} {x - 0.4:.2f} {h + ln:.2f}", stroke=SAND_MID, width=1.0, opacity=0.75)
            s.circle(x - 0.4, h + ln + 1.2, 0.8, fill=SAND_MID, opacity=0.7)
        notch = []
        x = 1.0
        while x < w - 1:
            notch.append((x, 1.0 + (1.6 if r.next() < 0.25 else 0.0)))
            x += r.uniform(5, 9)
        notch.append((w - 1.0, 1.0))
        outline = _pl([(1.0, h - 2.0)] + notch + [(w - 1.0, h - 2.0), (w - 4.0, h - 0.8), (4.0, h - 0.8)]) + "Z"
        s.path(outline, fill=s.linear(0, 0, 0, h, [(0, "#f7e6c4"), (0.4, "#e2c294"), (1, "#b68a5e")]), stroke=INK, width=1.2)
        s.path(_pl([(3, 3.2), (w - 3, 3.2)]), stroke="#fff8e6", width=1.1, opacity=0.8)
        for _ in range(max(3, int(w / 26))):
            x = r.uniform(8, w - 8)
            pts = [(x, 1.5)]
            y = 1.5
            while y < h - 2:
                y = min(h - 1.5, y + r.uniform(3, 6))
                pts.append((pts[-1][0] + r.uniform(-3.5, 3.5), y))
            s.path(_pl(pts), stroke="#5a3a22", width=1.0, opacity=0.85)
            bx, by = pts[len(pts) // 2]
            s.path(_pl([(bx, by), (bx + r.uniform(-6, 6), by + r.uniform(1, 4))]), stroke="#5a3a22", width=0.7, opacity=0.7)
        for _ in range(int(w / 30)):
            x = r.uniform(6, w - 10)
            s.polygon([(x, h - 1), (x + 3, h - 4), (x + 6, h - 1)], fill="#8a6440", opacity=0.6)

    def _plank_walk(self, s: Svg, w: float, h: float) -> None:
        top = min(h, 8.0)
        for x in range(12, int(w) - 6, 30):
            s.path(rounded_rect_path(x - 2.2, top - 1, 4.4, h + 9, 1.5), fill=s.linear(x - 2, 0, x + 2, 0, [(0, "#8a5a32"), (1, "#5a3a20")]),
                   stroke=INK, width=0.8)
        s.path(rounded_rect_path(0.6, 0.6, w - 1.2, top, 2.4), fill=s.linear(0, 0, 0, top, [(0, "#e2b07a"), (1, "#9a6a3e")]), stroke=INK, width=1.1)
        for x in range(8, int(w), 16):
            s.line(x, 1.4, x, top - 0.8, "#7a4a28", 0.8, 0.6)
        for x in range(12, int(w) - 6, 30):
            s.path(f"M{x - 3:.1f} {top - 2:.1f} L{x + 3:.1f} {top + 2:.1f} M{x + 3:.1f} {top - 2:.1f} L{x - 3:.1f} {top + 2:.1f}",
                   stroke="#e8d2a0", width=1.1)

    def _palm_canopy(self, s: Svg, w: float, h: float) -> None:
        """One-way palm-crown platform (oasis): a flat mat of fronds to stand
        on, drooping frond tips, date clusters and the top of the trunk."""
        cx = w / 2
        s.path(f"M{cx - 5:.2f} {h + 10:.2f} L{cx - 3.4:.2f} {h - 2:.2f} L{cx + 3.4:.2f} {h - 2:.2f} L{cx + 5:.2f} {h + 10:.2f} Z",
               fill=s.linear(0, h - 2, 0, h + 10, [(0, "#a87448"), (0.45, "#8a5a36", 0.85), (1, "#7a5030", 0)]))
        for side in (-1, 1):  # the trunk fades out: the palm stands far below
            s.path(f"M{cx + side * 3.4:.2f} {h - 2:.2f} L{cx + side * 5:.2f} {h + 10:.2f}",
                   stroke=s.linear(0, h - 2, 0, h + 10, [(0, INK), (1, INK, 0)]), width=1.0)
        for side in (-1, 1):
            for k in range(3):  # drooping lower fronds
                ex = cx + side * (w / 2 - 3 - k * 9)
                ey = h * 0.55 + 6 + k * 1.5
                d = (f"M{cx:.2f} {h * 0.35:.2f} Q{cx + side * w * 0.3:.2f} {h * 0.1 - 2:.2f} {ex:.2f} {ey:.2f} "
                     f"Q{cx + side * w * 0.28:.2f} {h * 0.55:.2f} {cx:.2f} {h * 0.6:.2f} Z")
                s.path(d, fill=LEAF[2] if k == 0 else LEAF[1], stroke="#1e4422", width=0.8)
        for dx in (-7.0, 6.0):  # dates
            for j in range(6):
                ex = cx + dx + (j % 3 - 1) * 2.4
                ey = h * 0.62 + 1.6 + (j // 3) * 2.6
                s.path(_ellipse_d(ex, ey, 1.3, 1.8), fill=s.radial(ex + 0.4, ey - 0.6, 2.2, [(0, "#ffb050"), (1, "#a8501c")]), stroke=INK,
                       width=0.4)
        mat = [(1.5, 3.6)]
        n = max(6, int(w / 7))
        for i in range(1, n):
            x = w * i / n
            mat.append((x, 1.0 + 1.4 * abs(2 * i / n - 1)))
        mat.append((w - 1.5, 3.6))
        lower = []
        for i in range(n, -1, -1):
            x = 1.5 + (w - 3) * i / n
            lower.append((x, h * 0.48 + (2.2 if i % 2 else 0.0)))
        s.path(_pl(mat + lower) + "Z", fill=s.linear(0, 0, 0, h * 0.5, [(0, LEAF[0]), (0.6, LEAF[1]), (1, LEAF[2])]), stroke="#1e4422", width=1.0)
        s.path(_pl(mat), stroke="#e8f6b0", width=1.2, opacity=0.8)
        for i in range(1, n, 2):
            x = w * i / n
            s.line(x, 2.4, x + (1.6 if x > cx else -1.6), h * 0.44, "#2e6532", 0.7, 0.6)

    def _drum(self, s: Svg, w: float, h: float) -> None:
        """Bounce pad: a hide drum laced with rope, a sun painted on the skin."""
        top = h * 0.3
        s.path(f"M3 {top:.2f} L{w - 3:.2f} {top:.2f} L{w - 6:.2f} {h:.2f} L6 {h:.2f} Z",
               fill=s.linear(0, 0, w, 0, [(0, "#7a4222"), (0.62, "#d88a4e"), (1, "#9a5430")]), stroke=INK, width=1.1)
        lace = []
        n = max(3, int(w / 9))
        for i in range(n + 1):
            lace.append((5 + (w - 10) * i / n, top + 2 if i % 2 == 0 else h - 3))
        s.path(_pl(lace), stroke="#f2deb0", width=1.2)
        s.path(f"M5 {h - 2.5:.2f} L{w - 5:.2f} {h - 2.5:.2f}", stroke="#5a2e16", width=2.2)
        s.path(_ellipse_d(w / 2, top, w / 2 - 2, h * 0.17), fill=s.radial(w * 0.6, top - 2, w * 0.5, [(0, "#fff2d8"), (1, "#d8b48a")]),
               stroke=INK, width=1.1)
        s.path(glyph_d(0, w / 2, top, min(w * 0.2, h * 0.15)), stroke="#c8642c", width=1.0, opacity=0.8)

    def _shelf(self, w: float, h: float) -> Svg:
        """Rock shelf (ledge): sand-dusted top, strata, tapered underside."""
        hr = self.terrain_headroom
        s = Svg(w, h + hr)
        y0 = hr
        body = (f"M0 {y0 + 1:.2f} L{w:.2f} {y0 + 1:.2f} L{w:.2f} {y0 + h * 0.45:.2f} "
                f"Q{w - 4:.2f} {y0 + h:.2f} {w * 0.6:.2f} {y0 + h:.2f} L{w * 0.35:.2f} {y0 + h * 0.92:.2f} "
                f"Q4 {y0 + h * 0.85:.2f} 0 {y0 + h * 0.4:.2f} Z")
        s.path(body, fill=s.linear(0, y0, 0, y0 + h, [(0, ROCK_TOP), (0.5, ROCK), (1, ROCK_DEEP)]), stroke=INK, width=1.2)
        for k in range(1, 3):
            y = y0 + h * (0.22 + 0.16 * k)
            s.line(4 + k * 3, y, w - 4 - k * 3, y, shade(ROCK, -0.4), 1.0, 0.45)
        s.path(f"M0 {y0 - 0.6:.2f} Q{w / 2:.2f} {y0 - 2.2:.2f} {w:.2f} {y0 - 0.6:.2f} L{w:.2f} {y0 + 6:.2f} "
               f"Q{w * 0.6:.2f} {y0 + 9:.2f} {w * 0.3:.2f} {y0 + 6:.2f} Q8 {y0 + 4:.2f} 0 {y0 + 7:.2f} Z",
               fill=s.linear(0, y0 - 2, 0, y0 + 8, [(0, SAND_HI), (0.4, SAND), (1, SAND_MID)]), stroke=SAND_EDGE, width=1.0)
        return s

    def _ruin_ledge(self, w: float, h: float) -> Svg:
        """Ruined masonry ledge: two courses of temple blocks, snapped off at
        the east end, a wind frieze and sand trickling from the break."""
        hr = self.terrain_headroom
        s = Svg(w, h + hr)
        y0 = hr
        mid = y0 + h * 0.5
        outline = [(0, y0), (w - 7, y0), (w - 3, y0 + 3), (w - 6, mid - 1), (w - 1.5, mid + 2), (w - 4, y0 + h - 4), (w - 10, y0 + h),
                   (0, y0 + h)]
        s.path(_pl(outline) + "Z", fill=s.linear(0, y0, 0, y0 + h, [(0, STONE), (0.5, STONE_MID), (1, STONE_DEEP)]), stroke=INK, width=1.2)
        s.line(1, mid, w - 6, mid, "#7a4e2a", 1.0, 0.7)
        for x in (w * 0.34, w * 0.72):
            s.line(x, y0 + 1.5, x, mid - 0.5, "#7a4e2a", 1.0, 0.7)
        for x in (w * 0.16, w * 0.55):
            s.line(x, mid + 0.5, x, y0 + h - 1.5, "#7a4e2a", 1.0, 0.7)
        carve(s, _pl([(4 + i * 4.0, mid + (h * 0.25) + (-1.6 if i % 2 else 1.6)) for i in range(int((w - 16) / 4))]), 0.8, 0.55)
        s.line(2, y0 + 1.6, w - 8, y0 + 1.6, STONE_HI, 1.2, 0.85)
        s.path(f"M2 {y0 + 0.6:.2f} Q{w * 0.3:.2f} {y0 - 2.6:.2f} {w * 0.55:.2f} {y0 + 0.6:.2f} Z", fill=SAND, stroke=SAND_MID, width=0.6)
        for k in range(2):
            x = w - 6 - k * 3
            s.path(f"M{x:.2f} {y0 + h - 2:.2f} Q{x + 0.6:.2f} {y0 + h + 3:.2f} {x - 0.4:.2f} {y0 + h + 7 - k * 2:.2f}", stroke=SAND_MID,
                   width=1.0, opacity=0.75)
        return s

    def pipe(self, w: float, h: float, warp: bool) -> Svg:
        """Carved sandstone conduit with bronze collars (warp: a glowing glyph)."""
        s = Svg(w, h)
        body = s.linear(0, 0, w, 0, [(0, "#a06a3e"), (0.2, "#d8aa72"), (0.62, "#fbe2b2"), (0.8, "#e8bf86"), (1, "#a8703f")])
        s.path(rounded_rect_path(4, 10, w - 8, h - 10, 2), fill=body, stroke=INK, width=1.3)
        for fx in (0.3, 0.5, 0.7):
            x = 4 + (w - 8) * fx
            s.line(x, 16, x, h - 3, "#a8763f", 1.0, 0.5)
            s.line(x + 1.0, 16, x + 1.0, h - 3, "#fff0cc", 0.7, 0.45)
        collar = s.linear(0, 0, w, 0, [(0, BRONZE_DARK), (0.6, BRONZE_LIGHT), (1, BRONZE)])
        if h > 30:
            s.path(rounded_rect_path(3, h - 8, w - 6, 5, 1.5), fill=collar, stroke=INK, width=0.9)
            for k in range(3):
                s.circle(w * (0.3 + 0.2 * k), h - 5.5, 0.9, fill="#4fb8a8", opacity=0.8)
        s.path(rounded_rect_path(0.8, 0.8, w - 1.6, 14, 3.5),
               fill=s.linear(0, 0, w, 0, [(0, "#b07a48"), (0.6, "#ffeccc"), (1, "#c8925a")]), stroke=INK, width=1.3)
        s.path(f"M3.5 3.0 L{w - 3.5:.2f} 3.0", stroke="#5a3418", width=1.6, opacity=0.6)
        carve(s, _pl([(5 + i * 4.0, 9.2 + (-1.8 if i % 2 else 1.8)) for i in range(int((w - 10) / 4) + 1)]), 0.8, 0.55)
        s.path(rounded_rect_path(2.4, 13.2, w - 4.8, 4.2, 1.4), fill=collar, stroke=INK, width=0.9)
        if warp:
            cy = 27.0 if h > 36 else h * 0.66
            s.circle(w / 2, cy, 9, fill=s.radial(w / 2, cy, 9, [(0, TURQ_LIGHT, 0.95), (0.5, TURQ, 0.45), (1, TURQ, 0)]))
            s.path(glyph_d(0, w / 2, cy, 5.2), stroke="#ffffff", width=1.1, opacity=0.95)
            s.circle(w / 2, cy, 2.0, fill="#ffffff")
        return s

    def gate(self, w: float, h: float) -> Svg:
        """Arena gate: a heavy sandstone slab door bound with bronze bands,
        a bronze sun boss and a carved wind panel."""
        s = Svg(w, h)
        s.path(rounded_rect_path(0.6, 0, w - 1.2, h, 2.5),
               fill=s.linear(0, 0, w, 0, [(0, "#8a5a34"), (0.22, "#c99a62"), (0.68, "#f0d0a0"), (1, "#b8875a")]), stroke=INK, width=1.4)
        carve(s, rounded_rect_path(4.5, 6, w - 9, h - 12, 2), 1.0, 0.55)
        bronze = s.linear(0, 0, w, 0, [(0, BRONZE_DARK), (0.6, BRONZE_LIGHT), (1, BRONZE)])
        for y in (10.0, h * 0.5 - 3, h - 18):
            s.path(rounded_rect_path(1.2, y, w - 2.4, 6, 1.6), fill=bronze, stroke=INK, width=0.8)
            for rx_ in (5.0, w - 5.0):
                s.circle(rx_, y + 3, 1.2, fill=BRONZE_LIGHT, stroke=INK, width=0.4)
        cy, rad = h * 0.3, min(w * 0.3, 10.0)
        s.circle(w / 2, cy, rad, fill=s.radial(w / 2 + 2, cy - 2, rad * 1.2, [(0, BRONZE_LIGHT), (0.6, BRONZE), (1, BRONZE_DARK)]),
                 stroke=INK, width=1.0)
        s.path(glyph_d(0, w / 2, cy, rad * 0.8), stroke=BRONZE_DARK, width=1.0)
        carve(s, glyph_d(2, w / 2, h * 0.72, min(w * 0.3, 9.0)), 1.0, 0.6)
        s.rect(0.6, h - 5, w - 1.2, 5, fill="#5a3a22")
        return s

    # ------------------------------------------------------------------ interiors
    def _tomb_backdrop(self) -> Svg:
        """Torch-lit tomb chamber behind underground rooms (cave_sky)."""
        s = Svg(960, 540)
        s.rect(0, 0, 960, 540, fill=s.linear(0, 0, 0, 540, [(0, "#2a170e"), (0.45, "#3e2516"), (1, "#1c0f09")]))
        for row in range(12):
            y = row * 48
            off = (row % 2) * 62
            for col in range(-1, 9):
                x = col * 124 + off
                s.rect(x + 2, y + 2, 120, 44, fill=mix("#4a2c1a", "#583420", _hash(row * 31 + col, 77)), rx=3, opacity=0.95)
        s.rect(0, 96, 960, 44, fill=s.linear(0, 96, 0, 140, [(0, "#6a4228"), (1, "#4e301e")]))
        s.line(0, 96, 960, 96, "#a8744a", 2.0, 0.6)
        s.line(0, 140, 960, 140, "#1a0c06", 2.0, 0.7)
        carve(s, "".join(glyph_d(i * 5 + 2, 20 + i * 40, 118, 13) for i in range(24)), 1.6, 0.55, dark="#24120a", light="#c8885a")
        cx, cy = 480.0, 262.0
        s.circle(cx, cy, 70, fill=s.radial(cx, cy, 70, [(0, "#6e4630"), (1, "#4a2c1a")]))
        carve(s, glyph_d(0, cx, cy, 64), 3.0, 0.6, dark="#1e0e08", light="#b07a4e")
        carve(s, glyph_d(4, cx, cy, 22), 2.2, 0.55, dark="#1e0e08", light="#b07a4e")
        for tx in (250.0, 710.0):
            ty = 250.0
            s.circle(tx, ty, 190, fill=s.radial(tx, ty, 190, [(0, "#ffb860", 0.42), (0.35, "#ff9a40", 0.16), (1, "#ff8a30", 0)]))
            s.path(f"M{tx - 9} {ty + 6} L{tx + 9} {ty + 6} L{tx + 4} {ty + 26} L{tx - 4} {ty + 26} Z",
                   fill=s.linear(tx - 9, 0, tx + 9, 0, [(0, BRONZE_DARK), (0.6, BRONZE_LIGHT), (1, BRONZE)]), stroke="#140a06", width=1.5)
            flame(s, tx, ty - 6, 26)
        for px in (60.0, 900.0):
            s.rect(px - 46, 0, 92, 540, fill=s.linear(px - 46, 0, px + 46, 0, [(0, "#2a160c"), (0.55, "#6e4a30"), (1, "#3a2214")]))
            for fx in (-26, -10, 6, 22):
                s.line(px + fx, 60, px + fx, 520, "#20100a", 2.0, 0.5)
            s.rect(px - 56, 40, 112, 22, fill="#5a3a24", rx=3)
            s.rect(px - 56, 40, 112, 4, fill="#a8744a", opacity=0.6)
        # dusty light from a crack in the ceiling (soft across its width)
        with s.group("translate(640 0) skewX(-18)"):
            s.rect(0, 0, 70, 540, fill=s.linear(0, 0, 70, 0, [(0, "#ffd9a0", 0), (0.5, "#ffd9a0", 0.08), (1, "#ffd9a0", 0)]))
        s.rect(0, 470, 960, 70, fill=s.linear(0, 470, 0, 540, [(0, "#1a0c06", 0), (1, "#1a0c06", 0.6)]))
        return s

    def _hall_backdrop(self) -> Svg:
        """Pyramid interior: a dim corbelled hall with a great sun relief lit
        by braziers, doorways to deeper galleries and air-shaft light."""
        s = Svg(960, 540)
        s.rect(0, 0, 960, 540, fill=s.linear(0, 0, 0, 540, [(0, "#140a06"), (0.3, "#2a180e"), (0.62, "#3a2414"), (1, "#1c0f08")]))
        for row in range(9):
            y = 96 + row * 50
            off = (row % 2) * 70
            for col in range(-1, 8):
                x = col * 140 + off
                s.rect(x + 2, y + 2, 136, 46, fill=mix("#3a2416", "#4a2e1c", _hash(row * 17 + col, 61)), rx=3)
                s.line(x + 5, y + 4, x + 133, y + 4, "#6a4428", 1.2, 0.45)
        for i in range(5):  # corbelled ceiling: each course steps further in
            y = i * 19
            s.rect(0, y, 960, 19, fill=mix("#1a0f08", "#2e1c10", i / 5))
            s.line(0, y + 18, 960, y + 18, "#0c0604", 2.0, 0.8)
            s.line(0, y + 1.2, 960, y + 1.2, "#6a4428", 1.2, 0.3 + 0.08 * i)
        cx, cy = 480.0, 250.0
        s.circle(cx, cy + 30, 210, fill=s.radial(cx, cy + 60, 230, [(0, "#ffb060", 0.3), (0.5, "#ff9040", 0.1), (1, "#ff8030", 0)]))
        s.circle(cx, cy, 80, fill=s.radial(cx + 10, cy - 14, 92, [(0, "#7a5232"), (1, "#4a2e1a")]))
        carve(s, glyph_d(0, cx, cy, 72), 3.2, 0.7, dark="#1a0c06", light="#c08a58")
        carve(s, glyph_d(4, cx, cy, 30), 2.4, 0.6, dark="#1a0c06", light="#c08a58")
        for side in (-1, 1):  # wind bands sweeping out of the sun
            for k in range(3):
                y = cy - 32 + k * 32
                pts = [(cx + side * (98 + i * 30), y + 6 * math.sin(i * 1.4 + k)) for i in range(8)]
                carve(s, smooth_open(pts), 2.0, 0.45, dark="#1a0c06", light="#a87048")
        for dx in (110.0, 850.0):  # doorways into deeper galleries
            s.path(f"M{dx - 46} 470 L{dx - 46} 312 L{dx + 46} 312 L{dx + 46} 470 Z", fill=s.linear(0, 312, 0, 470, [(0, "#070302"), (1, "#160b06")]))
            s.rect(dx - 60, 294, 120, 20, fill="#5a3a22", rx=2)
            s.line(dx - 58, 296, dx + 58, 296, "#9a6a40", 1.4, 0.7)
            carve(s, "".join(glyph_d(SUN_WIND[k], dx - 40 + k * 16, 304, 5.5) for k in range(6)), 1.2, 0.5, dark="#1a0c06", light="#a87048")
        for bx in (330.0, 630.0):  # braziers below the relief
            s.path(f"M{bx - 18} 392 Q{bx} 410 {bx + 18} 392 Z", fill=s.linear(bx - 18, 0, bx + 18, 0, [(0, BRONZE_DARK), (0.6, BRONZE_LIGHT), (1, BRONZE)]),
                   stroke="#140a06", width=1.4)
            s.rect(bx - 3, 404, 6, 60, fill="#4a2e18")
            flame(s, bx, 380, 22, glow=110)
        for k, x0 in enumerate((180.0, 560.0)):  # air-shaft light
            with s.group(f"translate({x0:.1f} 0) skewX(-24)"):
                s.rect(0, 0, 46 + 10 * k, 540, fill=s.linear(0, 0, 46 + 10 * k, 0, [(0, "#ffdca8", 0), (0.5, "#ffdca8", 0.07), (1, "#ffdca8", 0)]))
        s.rect(0, 462, 960, 78, fill=s.linear(0, 462, 0, 540, [(0, "#120804", 0), (1, "#120804", 0.7)]))
        return s

    def _hall_columns(self) -> Svg:
        """Parallax layer for the pyramid hall: massive carved columns, each
        with a torch whose light pools on the stone."""
        s = Svg(900, 420)
        for x in (130.0, 580.0):
            cw = 78.0
            s.rect(x, 24, cw, 396, fill=s.linear(x, 0, x + cw, 0, [(0, "#24130a"), (0.35, "#4e3220"), (0.72, "#7a5234"), (1, "#3a2414")]))
            for fx in (0.22, 0.42, 0.62, 0.82):
                s.line(x + cw * fx, 40, x + cw * fx, 404, "#1a0c06", 1.6, 0.45)
            s.rect(x - 12, 0, cw + 24, 14, fill="#5e3e24", rx=2)
            s.rect(x - 6, 14, cw + 12, 10, fill="#4a301c")
            s.line(x - 10, 1.5, x + cw + 10, 1.5, "#a87a4c", 1.4, 0.6)
            s.rect(x - 10, 400, cw + 20, 20, fill="#3e2616", rx=2)
            for by in (96.0, 318.0):
                s.rect(x + 2, by, cw - 4, 24, fill="#5a3a24")
                carve(s, "".join(glyph_d(SUN_WIND[(k + int(by)) % len(SUN_WIND)], x + 14 + k * 25, by + 12, 6.5) for k in range(3)),
                      1.3, 0.6, dark="#140a06", light="#b07a4c")
            tx, ty = x + cw / 2, 196.0
            s.circle(tx, ty, 130, fill=s.radial(tx, ty, 130, [(0, "#ffb860", 0.4), (0.4, "#ff9a40", 0.14), (1, "#ff8a30", 0)]))
            s.path(f"M{tx - 9} {ty + 8} L{tx + 9} {ty + 8} L{tx + 4} {ty + 30} L{tx - 4} {ty + 30} Z",
                   fill=s.linear(tx - 9, 0, tx + 9, 0, [(0, BRONZE_DARK), (0.6, BRONZE_LIGHT), (1, BRONZE)]), stroke="#140a06", width=1.4)
            flame(s, tx, ty - 4, 24)
        return s

    def interior(self, variant: str):
        """Indoor backdrops: the pyramid hall for fortress (pyramid) areas.
        Outdoor variants such as "temple", "dunes", "oasis" keep the sky."""
        if variant not in ("fortress", "pyramid", "tomb"):
            return None
        return self._hall_backdrop, self._hall_columns

    def cave_sky(self) -> Svg:
        return self._tomb_backdrop()

    # ------------------------------------------------------------------ props
    def _saguaro(self, seed: int) -> Svg:
        r = Rand(seed)
        s = Svg(70, 132)
        x, base, top = 35.0, 130.0, 14.0
        arms = [(-1, r.uniform(62, 76), r.uniform(12, 15), r.uniform(26, 34)), (1, r.uniform(48, 60), r.uniform(11, 14), r.uniform(30, 40))]
        if r.next() < 0.4:
            arms = arms[1:]

        def limb(d: str, wd: float) -> None:
            s.path(d, stroke=INK, width=wd + 2.6)
            s.path(d, stroke=CACTUS[1], width=wd)
            with s.group("translate(1.6 -0.4)"):
                s.path(d, stroke=CACTUS[0], width=wd * 0.32, opacity=0.85)
            with s.group(f"translate({-wd * 0.28:.2f} 0)"):
                s.path(d, stroke=CACTUS[2], width=wd * 0.22, opacity=0.5)

        for side, ay, reach, rise in arms:
            ax = x + side * reach
            limb(f"M{x:.1f} {base - ay:.1f} Q{ax:.1f} {base - ay + 2:.1f} {ax:.1f} {base - ay - rise * 0.4:.1f} L{ax:.1f} {base - ay - rise:.1f}", 9.0)
        limb(f"M{x:.1f} {base:.1f} L{x:.1f} {top:.1f}", 14.0)
        for k in (-3.5, 0, 3.5):
            s.line(x + k, top + 6, x + k, base - 4, CACTUS[2], 0.7, 0.45)
        for i in range(14):
            yy = top + 8 + i * 8
            for k in (-4.5, 4.5):
                s.circle(x + k, yy + (2 if k > 0 else 0), 0.7, fill="#fffbe8")
        for fx in (-3, 2, 5):
            s.circle(x + fx, top - 4.5 + abs(fx) * 0.3, 2.2, fill="#fff4d0", stroke="#d8a040", width=0.6)
        s.circle(x + 2, top - 5, 1.0, fill="#f0b020")
        return s

    def _prickly_pear(self, seed: int) -> Svg:
        r = Rand(seed)
        s = Svg(74, 60)
        for (cx, cy, rx, ry, rot) in ((37, 44, 13, 15, 0), (22, 36, 11, 13, -28), (52, 34, 11, 13, 24), (30, 18, 9, 11, -12), (49, 15, 9, 11, 18)):
            with s.group(f"translate({cx} {cy}) rotate({rot})"):
                s.ellipse(0, 0, rx, ry, fill=s.radial(rx * 0.35, -ry * 0.4, ry * 1.5, [(0, CACTUS[0]), (0.6, CACTUS[1]), (1, CACTUS[2])]),
                          stroke=INK, width=1.1)
                for _k in range(6):
                    s.circle(r.uniform(-rx * 0.6, rx * 0.6), r.uniform(-ry * 0.6, ry * 0.6), 0.8, fill="#fffbe8")
        for (fx, fy) in ((25, 7.5), (31, 7), (44, 5), (52, 6), (60, 25)):
            s.path(_ellipse_d(fx, fy, 2.6, 3.4), fill=s.radial(fx + 0.8, fy - 1, 3.6, [(0, "#ff8aa8"), (1, "#b8204a")]), stroke=INK, width=0.7)
        return s

    def _barrel(self, seed: int) -> Svg:
        s = Svg(40, 38)
        s.path(smooth_closed([(20, 6), (33, 12), (35, 26), (30, 36), (10, 36), (5, 26), (7, 12)], 0.8),
               fill=s.radial(25, 14, 26, [(0, CACTUS[0]), (0.6, CACTUS[1]), (1, CACTUS[2])]), stroke=INK, width=1.2)
        for fx in (-10, -4.5, 1, 6.5, 12):
            s.path(f"M{20 + fx * 0.4:.1f} 8 Q{20 + fx * 1.35:.1f} 20 {20 + fx * 1.1:.1f} 35", stroke=CACTUS[2], width=0.8, opacity=0.6)
        for k in range(5):
            a = math.radians(-150 + k * 30)
            s.path(_ellipse_d(20 + math.cos(a) * 5, 7 + math.sin(a) * 3, 2.4, 1.8), fill="#ffd84a", stroke="#a87010", width=0.5)
        s.circle(20, 6.5, 1.6, fill="#f08a20")
        return s

    def _palm(self, seed: int, hgt: float = 150.0, lean: float = 14.0) -> Svg:
        r = Rand(seed)
        w, h = 150.0, hgt + 46
        s = Svg(w, h)
        bx, by = 75.0, h - 2
        tx, ty = bx + lean, by - hgt
        trunk = (f"M{bx - 6:.1f} {by:.1f} Q{bx - 2 + lean * 0.15:.1f} {by - hgt * 0.55:.1f} {tx - 3.4:.1f} {ty + 4:.1f} "
                 f"L{tx + 3.4:.1f} {ty + 4:.1f} Q{bx + 7 + lean * 0.2:.1f} {by - hgt * 0.5:.1f} {bx + 6:.1f} {by:.1f} Z")
        s.path(trunk, fill=s.linear(bx - 6, 0, bx + 8, 0, [(0, "#6a4426"), (0.6, "#b88456"), (1, "#7a5030")]), stroke=INK, width=1.2)
        for i in range(1, int(hgt / 7)):
            t = i * 7 / hgt
            px = bx + (tx - bx) * t * t * 0.8 + lean * 0.12 * t
            py = by - hgt * t
            wd = 6.0 - 2.4 * t
            s.path(f"M{px - wd:.2f} {py + 1.2:.2f} Q{px:.2f} {py - 1.6:.2f} {px + wd:.2f} {py + 1.2:.2f}", stroke="#5a3820", width=0.9, opacity=0.7)
        s.path(_ellipse_d(tx, ty + 3, 5, 3.6), fill="#7a5030", stroke=INK, width=0.8)
        for dx in (-7.0, 6.0):  # hanging date clusters
            cx, cy = tx + dx, ty + 9
            s.path(f"M{tx + dx * 0.3:.1f} {ty + 3:.1f} Q{cx:.1f} {cy - 3:.1f} {cx:.1f} {cy:.1f}", stroke="#d8a040", width=1.0)
            for j in range(8):
                ex = cx + (j % 3 - 1) * 2.5 + r.uniform(-0.5, 0.5)
                ey = cy + 1 + (j // 3) * 2.7
                s.path(_ellipse_d(ex, ey, 1.4, 2.0), fill=s.radial(ex + 0.4, ey - 0.6, 2.4, [(0, "#ffb050"), (1, "#a8501c")]), stroke=INK, width=0.4)
        for k, ang in enumerate([-168, -140, -112, -80, -52, -22, 4, 26, 150]):
            a = math.radians(ang + r.uniform(-6, 6))
            ln = r.uniform(46, 60) * (0.8 if -100 < ang < -60 else 1.0)
            droop = 16 + 10 * abs(math.cos(a))
            ex, ey = tx + math.cos(a) * ln, ty + math.sin(a) * ln * 0.55 + droop
            mx, my = tx + math.cos(a) * ln * 0.55, ty + math.sin(a) * ln * 0.55 - 6
            spine = [(tx, ty)]
            for i in range(1, 9):
                t = i / 8
                spine.append(((1 - t) ** 2 * tx + 2 * (1 - t) * t * mx + t * t * ex, (1 - t) ** 2 * ty + 2 * (1 - t) * t * my + t * t * ey))
            upper, lower = [], []
            for i in range(1, len(spine)):
                (qx, qy), (px, py) = spine[i - 1], spine[i]
                nx, ny = -(py - qy), px - qx
                nl = math.hypot(nx, ny) or 1
                nx, ny = nx / nl, ny / nl
                wd = 7.5 * math.sin(math.pi * min(1.0, i / 8 + 0.08)) * (1.3 if i % 2 else 0.85)
                upper.append((px + nx * wd, py + ny * wd))
                lower.append((px - nx * wd * 0.7, py - ny * wd * 0.7))
            fill = s.linear(tx, ty - 10, ex, ey, [(0, LEAF[0]), (0.6, LEAF[1]), (1, LEAF[2])]) if k % 3 else \
                s.linear(tx, ty - 10, ex, ey, [(0, "#a6d062"), (1, "#3e7a36")])
            s.path(_pl([(tx, ty)] + upper + list(reversed(lower))) + "Z", fill=fill, stroke="#1e4422", width=0.9)
            s.path(smooth_open(spine), stroke="#e8f0a0", width=0.8, opacity=0.6)
        return s

    def _reeds(self, seed: int) -> Svg:
        r = Rand(seed)
        s = Svg(46, 40)
        for _ in range(9):
            x, top, bend = r.uniform(8, 38), r.uniform(4, 16), r.uniform(-5, 5)
            s.path(f"M{x:.1f} 39 Q{x + bend * 0.3:.1f} {top + 12:.1f} {x + bend:.1f} {top:.1f}", stroke=r.choice(["#5f9a46", "#7ab454", "#4a8038"]),
                   width=1.6)
            if r.next() < 0.5:
                s.path(_ellipse_d(x + bend, top - 2.5, 1.5, 3.8), fill="#8a5a30", stroke=INK, width=0.5)
        return s

    def _ribcage(self, seed: int) -> Svg:
        s = Svg(120, 60)
        bone = s.linear(0, 0, 0, 60, [(0, BONE[0]), (0.6, BONE[1]), (1, BONE[2])])
        spine = [(14, 44), (34, 26), (60, 18), (86, 22), (104, 34)]
        for k in range(6):
            t = 0.12 + k * 0.15
            sx = 14 + (104 - 14) * t
            sy = 44 - 26 * math.sin(math.pi * t)
            d = f"M{sx:.1f} {sy:.1f} Q{sx + 18:.1f} {sy + 2:.1f} {sx + 10 - k * 1.5:.1f} 56"
            s.path(d, stroke=INK, width=5.6)
            s.path(d, stroke=BONE[1], width=3.6)
            with s.group("translate(0.8 -0.6)"):
                s.path(d, stroke=BONE[0], width=1.4, opacity=0.9)
        s.path(smooth_open(spine), stroke=INK, width=7.4)
        s.path(smooth_open(spine), stroke=bone, width=5.2)
        for (vx, vy) in spine[1:-1] + [(47, 21), (73, 19), (96, 27)]:
            s.circle(vx, vy - 1, 2.4, fill=BONE[0], stroke=INK, width=0.8)
        s.path("M0 60 Q20 50 44 54 Q70 46 96 54 Q110 52 120 60 Z", fill=s.linear(0, 46, 0, 60, [(0, SAND_TOP), (1, SAND)]), stroke=SAND_MID, width=0.8)
        return s

    def _skull(self, seed: int) -> Svg:
        s = Svg(48, 28)
        for side in (-1, 1):
            d = f"M{24 + side * 7} 11 Q{24 + side * 18} 4 {24 + side * 22} 10 Q{24 + side * 23} 14 {24 + side * 20} 13"
            s.path(d, stroke=INK, width=4.4)
            s.path(d, stroke=BONE[1], width=2.6)
        s.path(smooth_closed([(24, 4), (33, 9), (31, 18), (27, 25), (21, 25), (17, 18), (15, 9)], 0.8),
               fill=s.radial(28, 9, 18, [(0, BONE[0]), (0.6, BONE[1]), (1, BONE[2])]), stroke=INK, width=1.1)
        for ex in (20.0, 28.0):
            s.path(_ellipse_d(ex, 13, 2.6, 3.0), fill="#4a3428")
        s.path("M22.5 21 L24 18.5 L25.5 21", stroke="#4a3428", width=1.0)
        s.path("M6 28 Q24 22 42 28 Z", fill=SAND_TOP, stroke=SAND_MID, width=0.6)
        return s

    def _pots(self, seed: int) -> Svg:
        s = Svg(64, 46)
        s.path("M18 6 L26 6 L25 10 Q36 18 33 32 Q30 42 22 43 Q14 42 11 32 Q8 18 19 10 Z",
               fill=s.linear(8, 0, 36, 0, [(0, CLAY[2]), (0.62, CLAY[0]), (1, CLAY[1])]), stroke=INK, width=1.1)
        s.path("M19 12 Q12 14 13 22", stroke=INK, width=1.6)
        s.path("M25 12 Q33 14 32 22", stroke=INK, width=1.6)
        s.path("M12 24 Q22 27 33 24", stroke="#f6dcb0", width=1.6)
        s.path(_pl([(12.5, 29), (15, 26.5), (17.5, 29), (20, 26.5), (22.5, 29), (25, 26.5), (27.5, 29), (30, 26.5), (32.5, 29)]),
               stroke="#3a1c10", width=0.9)
        s.path("M14 33 Q22 36 31 33", stroke=TURQ, width=1.8, opacity=0.9)
        s.path("M36 42 Q34 30 44 28 L54 28 Q62 30 61 38 Q60 44 50 44 L40 44 Z",
               fill=s.linear(36, 0, 62, 0, [(0, CLAY[2]), (0.6, "#e08a5a"), (1, CLAY[1])]), stroke=INK, width=1.1)
        s.path("M54 28 Q58 34 56 44", stroke="#3a1c10", width=1.0, opacity=0.7)
        s.path("M40 33 Q48 31 56 33", stroke="#f6dcb0", width=1.3, opacity=0.9)
        s.polygon([(4, 44), (8, 40), (11, 44)], fill=CLAY[1], stroke=INK, width=0.7)
        s.path("M0 46 Q32 40 64 46 Z", fill=SAND_TOP, stroke=SAND_MID, width=0.6)
        return s

    def _column(self, seed: int, hgt: float) -> Svg:
        r = Rand(seed)
        s = Svg(56, hgt + 18)
        base = hgt + 14
        x0, x1 = 16.0, 40.0
        top = base - hgt
        s.path(rounded_rect_path(9, base - 9, 38, 9, 2), fill=s.linear(0, base - 9, 0, base, [(0, STONE_HI), (1, STONE_MID)]), stroke=INK, width=1.1)
        jag = [(x0, top + 6)] + [(x0 + (x1 - x0) * i / 5, top + r.uniform(0, 9)) for i in range(1, 5)] + [(x1, top + r.uniform(2, 7))]
        s.path(_pl([(x0, base - 9)] + jag + [(x1, base - 9)]) + "Z",
               fill=s.linear(x0, 0, x1, 0, [(0, STONE_DEEP), (0.3, STONE_MID), (0.68, STONE_HI), (1, STONE_MID)]), stroke=INK, width=1.2)
        for fx in (21.0, 26.0, 31.0, 36.0):
            s.line(fx, top + 10, fx, base - 11, "#a8743f", 0.9, 0.55)
            s.line(fx + 0.9, top + 10, fx + 0.9, base - 11, "#fff2d0", 0.6, 0.5)
        ring = top + hgt * 0.45
        s.rect(x0 - 0.5, ring, x1 - x0 + 1, 6, fill="#e8c08a", stroke=INK, width=0.8)
        carve(s, glyph_d(int(seed) % 9, (x0 + x1) / 2, ring + 3, 2.6), 0.6, 0.6)
        for _ in range(2):
            cy = r.uniform(top + 14, base - 16)
            s.path(_pl([(x1 - 1, cy), (x1 - 5, cy + 3), (x1 - 3, cy + 7)]), stroke="#6a4224", width=0.8, opacity=0.7)
        s.path(f"M2 {base + 2:.1f} Q14 {base - 8:.1f} 28 {base - 4:.1f} Q44 {base - 9:.1f} 54 {base + 2:.1f} Z",
               fill=s.linear(0, base - 9, 0, base + 2, [(0, SAND_TOP), (1, SAND)]), stroke=SAND_MID, width=0.7)
        return s

    def _fallen_column(self) -> Svg:
        s = Svg(96, 46)
        s.path(rounded_rect_path(6, 30, 30, 8, 2), fill=s.linear(0, 30, 0, 38, [(0, STONE_HI), (1, STONE_MID)]), stroke=INK, width=1.0)
        s.path(_pl([(10, 30), (10, 14), (16, 10), (22, 15), (28, 11), (32, 16), (32, 30)]) + "Z",
               fill=s.linear(10, 0, 32, 0, [(0, STONE_DEEP), (0.65, STONE_HI), (1, STONE_MID)]), stroke=INK, width=1.1)
        s.path(rounded_rect_path(40, 22, 40, 18, 3), fill=s.linear(0, 22, 0, 40, [(0, STONE_HI), (0.5, STONE), (1, STONE_DEEP)]), stroke=INK, width=1.1)
        for y in (26.0, 30.5, 35.0):
            s.line(42, y, 78, y, "#a8743f", 0.8, 0.5)
        s.path(_ellipse_d(80, 31, 6, 9), fill=s.radial(81, 28, 9, [(0, STONE_HI), (1, STONE_MID)]), stroke=INK, width=1.0)
        s.circle(80, 31, 2, fill=None, stroke="#a8743f", width=0.8)
        s.path("M0 46 Q24 36 48 40 Q72 36 96 46 Z", fill=s.linear(0, 36, 0, 46, [(0, SAND_TOP), (1, SAND)]), stroke=SAND_MID, width=0.7)
        return s

    def _obelisk(self) -> Svg:
        s = Svg(40, 138)
        base = 132.0
        s.path(rounded_rect_path(6, base - 8, 28, 8, 1.5), fill=s.linear(0, base - 8, 0, base, [(0, STONE_HI), (1, STONE_MID)]), stroke=INK, width=1.0)
        s.path(_pl([(10, base - 8), (13, 20), (20, 8), (27, 20), (30, base - 8)]) + "Z",
               fill=s.linear(10, 0, 30, 0, [(0, STONE_DEEP), (0.35, STONE_MID), (0.7, STONE_HI), (1, STONE)]), stroke=INK, width=1.2)
        s.path(_pl([(13, 20), (20, 8), (27, 20)]) + "Z", fill=s.linear(13, 8, 27, 20, [(0, "#fff0b0"), (0.5, "#f2b840"), (1, "#a86a18")]),
               stroke=INK, width=1.0)
        carve(s, "".join(glyph_d(k * 2 + 1, 20, 34 + k * 15, 4.2) for k in range(6)), 0.8, 0.6)
        s.path(f"M0 {base + 6:.1f} Q12 {base - 4:.1f} 20 {base - 2:.1f} Q30 {base - 5:.1f} 40 {base + 6:.1f} Z",
               fill=s.linear(0, base - 5, 0, base + 6, [(0, SAND_TOP), (1, SAND)]), stroke=SAND_MID, width=0.7)
        return s

    def _hoodoo(self) -> Svg:
        s = Svg(78, 104)
        s.path("M24 100 Q27 70 30 52 Q32 40 36 36 L46 36 Q50 42 51 52 Q54 72 56 100 Z",
               fill=s.linear(24, 0, 56, 0, [(0, "#9a5232"), (0.6, "#d88a5a"), (1, "#b46a44")]), stroke=INK, width=1.2)
        for y, c in ((52, "#e8a874"), (66, "#c46a40"), (80, "#e2a070")):
            s.path(f"M{28 + (y - 52) * -0.08:.1f} {y} L{52 + (y - 52) * 0.08:.1f} {y}", stroke=shade(c, -0.35), width=1.2, opacity=0.6)
        s.path(smooth_closed([(8, 34), (22, 16), (52, 12), (72, 22), (70, 34), (40, 40)], 0.7),
               fill=s.linear(0, 12, 0, 40, [(0, "#f2b88a"), (0.6, "#c8784c"), (1, "#8a4630")]), stroke=INK, width=1.2)
        s.path("M24 18 Q48 11 66 20", stroke="#ffe0b8", width=1.8, opacity=0.8)
        s.path("M14 33 Q40 39 66 32", stroke="#5a2a18", width=1.4, opacity=0.5)
        s.path("M10 104 Q40 90 70 104 Z", fill=s.linear(0, 92, 0, 104, [(0, SAND_TOP), (1, SAND)]), stroke=SAND_MID, width=0.7)
        return s

    def _boulders(self, seed: int) -> Svg:
        s = Svg(64, 36)
        for (cx, cy, rx, ry, sd) in ((22, 22, 16, 12, 1), (42, 26, 13, 9, 2), (52, 30, 7, 5, 3)):
            pts = [(cx + math.cos(a) * rx * (1 + 0.08 * math.sin(a * 3 + sd)), cy + math.sin(a) * ry * (0.85 if math.sin(a) < 0 else 1))
                   for a in [i * math.pi / 5 for i in range(10)]]
            s.path(smooth_closed(pts, 0.8), fill=s.radial(cx + rx * 0.35, cy - ry * 0.5, rx * 1.6, [(0, "#f2b88a"), (0.55, "#cd7f52"), (1, "#8a4630")]),
                   stroke=INK, width=1.1)
            s.path(f"M{cx - rx * 0.7:.1f} {cy + 1:.1f} Q{cx:.1f} {cy + 3:.1f} {cx + rx * 0.7:.1f} {cy:.1f}", stroke="#8a4630", width=0.9, opacity=0.5)
        s.path("M0 36 Q32 28 64 36 Z", fill=SAND_TOP, stroke=SAND_MID, width=0.6)
        return s

    def _shrub(self, seed: int) -> Svg:
        r = Rand(seed)
        s = Svg(52, 28)
        for _ in range(14):
            a = math.radians(r.uniform(-165, -15))
            ln = r.uniform(9, 18)
            ex, ey = 26 + math.cos(a) * ln * 1.3, 27 + math.sin(a) * ln
            s.path(f"M26 27 Q{26 + math.cos(a) * ln * 0.5:.1f} {27 + math.sin(a) * ln * 0.7 - 2:.1f} {ex:.1f} {ey:.1f}",
                   stroke=r.choice(["#b08a50", "#d8b060", "#9a7040"]), width=1.0)
            if r.next() < 0.6:
                s.circle(ex, ey, r.uniform(1.2, 2.0), fill=r.choice(["#9aaa52", "#7a9a48", "#c8c070"]))
        return s

    def _tumbleweed(self, seed: int) -> Svg:
        r = Rand(seed)
        s = Svg(32, 30)
        s.circle(16, 15, 13, fill="#c8a060", opacity=0.25)
        for _ in range(16):
            a1, a2, rr = r.uniform(0, 6.28), r.uniform(0, 6.28), r.uniform(6, 13)
            p1 = (16 + math.cos(a1) * rr, 15 + math.sin(a1) * rr * 0.9)
            p2 = (16 + math.cos(a2) * rr, 15 + math.sin(a2) * rr * 0.9)
            s.path(f"M{p1[0]:.1f} {p1[1]:.1f} Q{16 + r.uniform(-4, 4):.1f} {15 + r.uniform(-4, 4):.1f} {p2[0]:.1f} {p2[1]:.1f}",
                   stroke=r.choice(["#8a6a3a", "#b08850", "#d8b46a"]), width=0.9)
        return s

    def props(self) -> dict[str, PropSpec]:
        return {
            "cactus_saguaro": PropSpec(lambda: self._saguaro(3), (35, 130)),
            "cactus_saguaro_b": PropSpec(lambda: self._saguaro(8), (35, 130)),
            "cactus_pear": PropSpec(lambda: self._prickly_pear(5), (37, 58)),
            "cactus_barrel": PropSpec(lambda: self._barrel(2), (20, 37)),
            "tree_palm": PropSpec(lambda: self._palm(4, 150, 16), (75, 194)),
            "tree_palm_b": PropSpec(lambda: self._palm(11, 118, -12), (75, 162)),
            "reeds": PropSpec(lambda: self._reeds(6), (23, 39)),
            "bones_ribs": PropSpec(lambda: self._ribcage(1), (60, 57)),
            "bones_skull": PropSpec(lambda: self._skull(1), (24, 26)),
            "pots": PropSpec(lambda: self._pots(1), (32, 44)),
            "column_ruin": PropSpec(lambda: self._column(7, 96), (28, 110)),
            "column_ruin_b": PropSpec(lambda: self._column(12, 58), (28, 72)),
            "column_fallen": PropSpec(self._fallen_column, (48, 44)),
            "obelisk": PropSpec(self._obelisk, (20, 134)),
            "rock_hoodoo": PropSpec(self._hoodoo, (40, 101)),
            "rock": PropSpec(lambda: self._boulders(2), (32, 34)),
            "shrub": PropSpec(lambda: self._shrub(5), (26, 27)),
            "shrub_b": PropSpec(lambda: self._shrub(19), (26, 27)),
            "tumbleweed": PropSpec(lambda: self._tumbleweed(3), (16, 29)),
        }

    def auto_decor(self, rng, surface_w: float):
        """Sparse, readable desert dressing: tall silhouettes behind the sand
        lip, small low props in front of it, an occasional palm oasis."""
        out: list[tuple[str, float, float, str]] = []
        x = rng.uniform(40, 130)
        while x < surface_w - 30:
            roll = rng.next()
            if roll < 0.18:
                out.append((rng.choice(["shrub", "shrub_b"]), x, rng.uniform(0.8, 1.05), "mid"))
            elif roll < 0.27:
                out.append((rng.choice(["bones_skull", "tumbleweed"]), x, rng.uniform(0.8, 1.0), "back"))
            elif roll < 0.36:
                out.append(("pots", x, rng.uniform(0.75, 0.9), "back"))
            elif roll < 0.45:
                out.append(("rock", x, rng.uniform(0.7, 1.0), "back"))
            elif roll < 0.58 and surface_w > 240:
                out.append((rng.choice(["cactus_saguaro", "cactus_saguaro_b"]), x, rng.uniform(0.8, 1.0), "back"))
            elif roll < 0.67:  # (the round barrel cactus is kept out: too close to the Cacto Sentinela)
                out.append(("cactus_pear", x, rng.uniform(0.7, 0.88), "back"))
            elif roll < 0.77 and surface_w > 300:
                out.append((rng.choice(["tree_palm", "tree_palm_b"]), x, rng.uniform(0.85, 1.05), "back"))
                out.append(("reeds", x + rng.uniform(18, 30), rng.uniform(0.8, 1.0), "back"))
            elif roll < 0.87:
                out.append((rng.choice(["column_ruin", "column_ruin_b", "column_fallen"]), x, rng.uniform(0.85, 1.0), "back"))
            elif roll < 0.93:
                out.append(("bones_ribs", x, rng.uniform(0.7, 0.85), "back"))
            elif roll < 0.97:
                out.append(("obelisk", x, rng.uniform(0.8, 1.0), "back"))
            else:
                out.append(("rock_hoodoo", x, rng.uniform(0.75, 0.9), "back"))
            x += rng.uniform(120, 240)
        return out

    def weather(self) -> Weather:
        return Weather("sand", 0.6, ("gd_grit", "gd_grit", "soft"), wind=-120.0)


ART_CLASS = GoldenDesert
