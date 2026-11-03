"""Floresta Encantada: night under giant trees, firefly ruins and root caves.

Identity: a blue-teal twilight with a large pale moon (cool rim light from the
upper right) and warm/cyan bioluminescence from below — glowing mushrooms,
bell flowers, lantern fruits and mycelium threads. Giant trunks rise above
the screen in parallax, ancient overgrown ruins carry glowing leaf runes, the
ground is a cushion of moss with drooping strands over dark rooted soil, and
spores and fireflies drift through the air.

Readability rules: the parallax layers stay in a narrow dark/mid value band
with a pale mist behind the play band, so dark-outlined characters read; the
moss lip is the brightest band of the terrain; reward blocks are the only
warm, saturated surfaces. Patterns that cross terrain chunk borders (moss
strands, roots, rim) are functions of the world x so chunks join seamlessly,
and only the hanging edge of the moss is outlined.
"""

from __future__ import annotations

import math
from typing import Optional, Sequence

from ..svg import Rand, Svg, blob, rounded_rect_path, shade, smooth_open, star_points
from .base import Layer, PropSpec, Weather, WorldArt

INK = "#1b1a2b"
SOIL_TOP, SOIL, SOIL_DEEP = "#54403f", "#3a2c33", "#1c151d"
ROOT, ROOT_LIGHT, ROOT_DARK = "#6a4c3c", "#a07a5e", "#2e211f"
STONE, STONE_LIGHT, STONE_DARK = "#6c7f8c", "#a6bcc4", "#36434f"
BARK, BARK_LIGHT, BARK_DARK = "#6a4a3a", "#9a7458", "#2e1f1c"
GLOW_CYAN, GLOW_TEAL, GLOW_GOLD, GLOW_LEAF = "#a6fbef", "#52e4c8", "#ffe58f", "#d8ff8a"
MIST = "#5fb4a8"
MOON_X, MOON_Y, MOON_R = 712.0, 132.0, 44.0

# moss cap: top, body, dark, deep, moonlit rim
MOSS = {
    "normal": ("#a9f2b4", "#5dc28c", "#2f8266", "#1a5046", "#e6ffea"),
    "sticky": ("#cfe08e", "#8ea65c", "#58722f", "#33461e", "#f4ffc4"),
    "ice": ("#f4feff", "#c2eaf4", "#84b8ce", "#4f7f9c", "#ffffff"),
}
# mushroom caps: light, mid, dark
CAP_CYAN = ("#dcfff8", "#58ddd2", "#15707f")
CAP_VIOLET = ("#f6dcff", "#b67fe8", "#57308c")
CAP_PINK = ("#ffe4f4", "#f08ac8", "#8a2e6e")
# dimmer caps for scenery standing in the play band (never brighter than the creatures)
CAP_VIOLET_DIM = ("#dcc0f0", "#9264c2", "#42266a")
CAP_PINK_DIM = ("#f0c8e0", "#bc66a0", "#5a1e4c")

Pt = tuple[float, float]


# ----------------------------------------------------------------------------- helpers
def _fract(v: float) -> float:
    return v - math.floor(v)


def _hash(i: int, k: float = 0.0) -> float:
    """Stable value in [0, 1) for an integer world-grid cell (seam-safe variation)."""
    return _fract(math.sin(i * 127.1 + k * 311.7) * 43758.5453)


def _curve(pts: Sequence[Pt], tension: float = 1.0) -> str:
    """Catmull-Rom segments through ``pts`` without the leading moveto."""
    d = smooth_open(pts, tension)
    return d[d.index("C"):] if "C" in d else ""


def _glow(s: Svg, cx: float, cy: float, r: float, color: str, alpha: float = 0.5) -> None:
    """Soft halo with a gaussian-like falloff (reads as emitted light on dark art).

    The radius is clamped to the canvas so a halo never shows a clipped edge."""
    r = min(r, cx, cy, s.w - cx, s.h - cy)
    if r < 0.6:
        return
    s.circle(cx, cy, r, fill=s.radial(cx, cy, r, [(0, color, alpha), (0.28, color, alpha * 0.55), (0.62, color, alpha * 0.16),
                                                   (1, color, 0)]))


def _haze(s: Svg, cx: float, cy: float, rx: float, ry: float, color: str, alpha: float) -> None:
    """Soft elliptical mist (a radial gradient squashed by a group transform), clamped to the canvas."""
    rx, ry = min(rx, cx, s.w - cx), min(ry, cy, s.h - cy)
    if rx < 0.6 or ry < 0.3:
        return
    with s.group(f"translate({cx:.2f} {cy:.2f}) scale(1 {max(0.01, ry / rx):.4f})"):
        s.circle(0, 0, rx, fill=s.radial(0, 0, rx, [(0, color, alpha), (0.5, color, alpha * 0.45), (1, color, 0)]))


def _brackets(s: Svg, x: float, y: float, size: float, side: int, pal: tuple[str, str, str] = ("#e6fffa", "#62d6cc", "#1d6f78"),
              halo: float = 0.4, outline: str = "#0c2a2e") -> None:
    """Shelf (bracket) fungi stacked on a trunk or cliff face, growing toward ``side``."""
    light, mid, dark = pal
    if halo:
        _glow(s, x + side * size * 0.55, y + size * 0.25, size * 1.7, light, halo)
    # tiers of different sizes sit slightly inside each other (never evenly stacked like stripes)
    for dy, k, shift in ((-size * 0.5, 0.58, 0.12), (0.0, 1.0, 0.0), (size * 0.46, 0.72, 0.06)):
        ww, bx = size * k, x - side * size * shift
        hh = ww * 0.46
        yy = y + dy
        tip = bx + side * ww
        s.path(f"M{bx:.2f} {yy - hh * 0.55:.2f} C{bx + side * ww * 0.55:.2f} {yy - hh * 0.8:.2f} {tip:.2f} {yy - hh * 0.4:.2f} "
               f"{tip:.2f} {yy + hh * 0.02:.2f} C{tip - side * ww * 0.08:.2f} {yy + hh * 0.42:.2f} {bx + side * ww * 0.45:.2f} "
               f"{yy + hh * 0.52:.2f} {bx:.2f} {yy + hh * 0.46:.2f} Z",
               fill=s.linear(0, yy - hh * 0.7, 0, yy + hh * 0.5, [(0, light), (0.5, mid), (1, dark)]), stroke=outline,
               width=max(0.35, size * 0.05))
        s.path(f"M{bx + side * ww * 0.12:.2f} {yy - hh * 0.36:.2f} Q{bx + side * ww * 0.6:.2f} {yy - hh * 0.5:.2f} "
               f"{bx + side * ww * 0.86:.2f} {yy - hh * 0.08:.2f}", stroke="#ffffff", width=max(0.3, size * 0.045), opacity=0.55)
        s.path(f"M{tip - side * ww * 0.06:.2f} {yy + hh * 0.16:.2f} Q{bx + side * ww * 0.5:.2f} {yy + hh * 0.52:.2f} "
               f"{bx:.2f} {yy + hh * 0.42:.2f}", stroke=light, width=max(0.35, size * 0.05), opacity=0.6)


def _moss_curtain(s: Svg, x: float, y: float, width: float, length: float, seed: float, color: str = "#2a5c50",
                  tip: str = "#4f9a80", glow: bool = True) -> None:
    """Clump of tapered hanging moss strands (Spanish-moss look)."""
    r = Rand(seed)
    n = max(3, int(width / 5))
    for k in range(n):
        sx = x - width / 2 + width * (k + 0.5) / n + r.uniform(-1.5, 1.5)
        ln = length * r.uniform(0.45, 1.0) * (1 - abs(k - (n - 1) / 2) / n * 0.6)
        sway = r.uniform(-5, 5)
        thick = r.uniform(2.2, 3.6)
        centre = [(sx + sway * (j / 5) ** 2 + 1.4 * math.sin(j * 1.7 + k), y + ln * j / 5, thick * (1 - j / 5) ** 0.8 + 0.4)
                  for j in range(6)]
        s.path(_taper(centre), fill=s.linear(0, y, 0, y + ln, [(0, color), (1, tip)]))
        if glow and k % 3 == 1:
            ex, ey = centre[-1][0], centre[-1][1]
            _glow(s, ex, ey, 5, GLOW_CYAN, 0.5)
            s.circle(ex, ey, 1.0, fill="#e6fff8")


def _band(s: Svg, w: float, y1: float, y2: float, color: str, alpha: float) -> None:
    """Full-width soft horizontal band (tiles across strip borders)."""
    s.rect(0, y1, w, y2 - y1, fill=s.linear(0, y1, 0, y2, [(0, color, 0), (0.5, color, alpha), (1, color, 0)]))


def _leaf(cx: float, cy: float, length: float, width: float, angle: float) -> str:
    """Pointed leaf centred at (cx, cy); ``angle`` in degrees along its long axis."""
    a = math.radians(angle)
    ca, sa = math.cos(a), math.sin(a)

    def p(u: float, v: float) -> str:
        return f"{cx + u * ca - v * sa:.2f} {cy + u * sa + v * ca:.2f}"

    return f"M{p(-length / 2, 0)} Q{p(0, -width)} {p(length / 2, 0)} Q{p(0, width)} {p(-length / 2, 0)}Z"


def _taper(centre: Sequence[tuple[float, float, float]]) -> str:
    """Closed tapered ribbon along (x, y, thickness) samples (roots, vines, stems)."""
    upper = [(x, y - t / 2) for x, y, t in centre]
    lower = [(x, y + t / 2) for x, y, t in reversed(centre)]
    return smooth_open(upper, 0.9) + f"L{lower[0][0]:.2f} {lower[0][1]:.2f}" + _curve(lower, 0.9) + "Z"


def _wave(x: float, w: float, k: int, phase: float = 0.0) -> float:
    """Periodic over the strip width so parallax strips tile seamlessly."""
    return math.sin(2 * math.pi * k * x / w + phase)


def _mushroom(s: Svg, x: float, base: float, height: float, cap: float, pal: tuple[str, str, str] = CAP_CYAN,
              lean: float = 0.0, halo: float = 0.4, outline: Optional[str] = INK, stem: str = "#e2f1ea", spots: int = 3) -> None:
    """Bioluminescent mushroom standing on (x, base): stem, domed cap, glowing gills and spots."""
    light, mid, dark = pal
    tx, ty = x + lean, base - height
    lw = max(0.35, min(1.5, cap * 0.075))
    if halo > 0:
        _glow(s, tx, ty - cap * 0.3, cap * 2.6, light, halo)
    sw = max(0.6, cap * 0.2)
    s.path(f"M{x - sw:.2f} {base + 0.4:.2f} Q{x + lean * 0.25 - sw * 0.5:.2f} {base - height * 0.55:.2f} {tx - sw * 0.7:.2f} {ty:.2f} "
           f"L{tx + sw * 0.7:.2f} {ty:.2f} Q{x + lean * 0.25 + sw * 0.5:.2f} {base - height * 0.55:.2f} {x + sw:.2f} {base + 0.4:.2f} Z",
           fill=s.linear(x - sw, 0, x + sw, 0, [(0, stem), (1, shade(stem, -0.38))]), stroke=outline, width=lw * 0.8)
    dome = (f"M{tx - cap:.2f} {ty + cap * 0.1:.2f} C{tx - cap * 1.04:.2f} {ty - cap * 0.6:.2f} {tx - cap * 0.52:.2f} {ty - cap * 0.96:.2f} "
            f"{tx:.2f} {ty - cap * 0.96:.2f} C{tx + cap * 0.52:.2f} {ty - cap * 0.96:.2f} {tx + cap * 1.04:.2f} {ty - cap * 0.6:.2f} "
            f"{tx + cap:.2f} {ty + cap * 0.1:.2f} Q{tx:.2f} {ty - cap * 0.2:.2f} {tx - cap:.2f} {ty + cap * 0.1:.2f}Z")
    s.path(dome, fill=s.radial(tx - cap * 0.3, ty - cap * 0.75, cap * 1.6, [(0, light), (0.45, mid), (1, dark)]), stroke=outline, width=lw)
    s.path(f"M{tx - cap * 0.86:.2f} {ty + cap * 0.06:.2f} Q{tx:.2f} {ty - cap * 0.13:.2f} {tx + cap * 0.86:.2f} {ty + cap * 0.06:.2f}",
           stroke=light, width=max(0.35, cap * 0.13), opacity=0.8)
    for u, v, k in ((-0.45, 0.5, 0.15), (0.12, 0.76, 0.12), (0.55, 0.42, 0.13), (-0.12, 0.3, 0.09), (0.36, 0.66, 0.08))[:spots]:
        s.circle(tx + cap * u, ty - cap * v, cap * k, fill="#ffffff", opacity=0.85)


def _crystal_cluster(s: Svg, x: float, y: float, size: float, pal: tuple[str, str, str], seed: float, up: bool = True,
                     halo: float = 0.45) -> None:
    """Fan of glowing prisms growing from (x, y); ``up`` False hangs them from a ceiling."""
    light, mid, dark = pal
    if halo:
        _glow(s, x, y - (size * 0.5 if up else -size * 0.5), size * 2.0, light, halo)
    r = Rand(seed)
    for k in range(4):
        a = math.radians((-90 if up else 90) + (-38 + k * 25) + r.uniform(-8, 8))
        ln = size * (1.0 - abs(k - 1.5) * 0.22) * r.uniform(0.8, 1.1)
        wd = ln * 0.24
        ca, sa = math.cos(a), math.sin(a)
        nx, ny = -sa, ca

        def p(u: float, v: float) -> Pt:
            return x + ca * u + nx * v, y + sa * u + ny * v

        pts = [p(0, -wd * 0.5), p(ln * 0.78, -wd * 0.5), p(ln, 0), p(ln * 0.78, wd * 0.5), p(0, wd * 0.5)]
        tip, root = p(ln, 0), p(0, 0)
        s.polygon(pts, fill=s.linear(root[0], root[1], tip[0], tip[1], [(0, dark), (0.55, mid), (1, light)]), stroke=shade(dark, -0.45),
                  width=max(0.4, size * 0.04))
        s.path(f"M{p(ln * 0.1, 0)[0]:.2f} {p(ln * 0.1, 0)[1]:.2f} L{p(ln * 0.86, 0)[0]:.2f} {p(ln * 0.86, 0)[1]:.2f}", stroke="#ffffff",
               width=max(0.3, size * 0.035), opacity=0.55)


class _Trunk:
    """Geometry of a giant trunk with a flared base: ``at(t, f)`` maps height
    fraction t (0 = ground, 1 = top) and width fraction f (-1..1) to a point."""

    def __init__(self, cx: float, ground: float, top: float, width: float, lean: float, seed: float, flare: float = 1.5) -> None:
        self.cx, self.ground, self.top, self.width, self.lean, self.seed, self.flare = cx, ground, top, width, lean, seed, flare

    def half(self, t: float) -> float:
        return self.width / 2 * (1 + self.flare * (1 - t) ** 6)

    def at(self, t: float, f: float) -> Pt:
        y = self.ground + (self.top - self.ground) * t
        off = self.lean * t * t + math.sin(t * 4.2 + self.seed) * self.width * 0.05
        return self.cx + off + f * self.half(t), y

    def outline(self, n: int = 18) -> str:
        left = [self.at(1 - i / n, -1) for i in range(n + 1)]
        right = [self.at(i / n, 1) for i in range(n + 1)]
        return smooth_open(left, 0.8) + f"L{right[0][0]:.2f} {right[0][1]:.2f}" + _curve(right, 0.8) + "Z"


# ----------------------------------------------------------------------------- world
class EnchantedForest(WorldArt):
    id = "enchanted_forest"
    name = "Floresta Encantada"
    accent = "#5fe0b0"
    terrain_headroom = 14.0
    ambient = (226, 236, 255)  # cool moonlight (the art is authored dark already; keep close to white)
    vignette = 0.4
    provisional = False

    # ------------------------------------------------------------------ sky
    def sky(self) -> Svg:
        s = Svg(960, 540)
        s.rect(0, 0, 960, 540, fill=s.linear(0, 0, 0, 540, [(0, "#050c1e"), (0.3, "#0b1d3a"), (0.6, "#123a55"), (0.84, "#1a5662"),
                                                              (1, "#1f6464")]))
        # an enchanted veil (very soft aurora ribbons)
        for k, (y, amp) in enumerate(((150.0, 26.0), (212.0, 18.0))):
            pts = [(x, y + amp * math.sin(x / 960 * 2 * math.pi * 1.2 + k * 1.7) + 9 * math.sin(x * 0.019 + k)) for x in range(-40, 1001, 50)]
            for width, alpha in ((70, 0.035), (44, 0.04), (22, 0.045), (8, 0.05)):
                s.path(smooth_open(pts), stroke="#72f2c8" if k == 0 else "#8ab8ff", width=width, opacity=alpha)
        # stars, denser near the zenith, none inside the moon halo
        r = Rand(5)
        for _ in range(150):
            x, y = r.uniform(0, 960), 400 * r.next() ** 1.8
            rad, a = r.uniform(0.45, 1.3), r.uniform(0.3, 0.95)
            if (x - MOON_X) ** 2 + (y - MOON_Y) ** 2 < 100 ** 2:
                continue
            s.circle(x, y, rad, fill=r.choice(["#eafcff", "#fff6d8", "#d6e8ff"]), opacity=a * max(0.15, 1 - y / 460))
        for _ in range(10):
            x, y = r.uniform(30, 930), r.uniform(18, 250)
            if (x - MOON_X) ** 2 + (y - MOON_Y) ** 2 < 120 ** 2:
                continue
            _glow(s, x, y, 8, "#cdf3ff", 0.32)
            s.polygon(star_points(x, y, 4.4, 0.7, 4), fill="#f4feff", opacity=0.9)
        # the moon: wide halo, glow, disc with soft maria
        mx, my, mr = MOON_X, MOON_Y, MOON_R
        s.circle(mx, my, 320, fill=s.radial(mx, my, 320, [(0, "#c4f7ea", 0.3), (0.16, "#94e2d6", 0.16), (0.45, "#5cb4c0", 0.06),
                                                          (1, "#4aa0b0", 0)]))
        _glow(s, mx, my, mr * 2.1, "#eafff6", 0.5)
        s.circle(mx, my, mr, fill=s.radial(mx - 14, my - 16, mr * 1.5, [(0, "#ffffff"), (0.45, "#f0fdf4"), (1, "#c2e4da")]))
        for dx, dy, rx, ry, a in ((-13, -6, 14, 9, 0.2), (11, 13, 12, 7, 0.17), (15, -15, 6, 5, 0.15), (-6, 19, 6, 4, 0.14), (-22, 12, 4, 3, 0.12)):
            s.ellipse(mx + dx, my + dy, rx, ry, fill="#98c6be", opacity=a)
        s.circle(mx, my, mr - 0.6, fill=None, stroke="#ffffff", width=1.2, opacity=0.5)
        # low mist over the horizon
        _band(s, 960, 380, 560, "#4c9c94", 0.18)
        return s

    def _wisp(self, seed: int, w: float, h: float) -> Svg:
        """Thin moonlit night cloud (translucent; drifts across the moon)."""
        r = Rand(seed)
        s = Svg(w, h)
        n = 5
        puffs = []
        for i in range(n):
            cx = w * (0.2 + 0.6 * i / (n - 1)) + r.uniform(-10, 10)
            cy = h * 0.56 + r.uniform(-h * 0.12, h * 0.08)
            rx, ry = w * r.uniform(0.16, 0.24), h * r.uniform(0.2, 0.3)
            puffs.append((cx, cy, rx, ry))
        for cx, cy, rx, ry in puffs:
            _haze(s, cx, cy + ry * 0.2, rx, ry, "#2c4a6a", 0.75)
        for cx, cy, rx, ry in puffs[1:-1]:
            _haze(s, cx, cy - ry * 0.35, rx * 0.8, ry * 0.42, "#a8dce8", 0.4)
        return s

    def _particle(self, kind: str) -> Svg:
        """World weather sprites (tinted and drawn additively by the scene)."""
        s = Svg(16, 16)
        if kind == "firefly":
            _glow(s, 8, 8, 7.9, "#fff6b8", 0.9)
            s.circle(8, 8, 3.4, fill=s.radial(8, 8, 3.4, [(0, "#ffffff"), (0.6, "#fffbe0"), (1, "#fff4b0", 0.3)]))
        else:  # spore: fluffy seed with a bright heart
            _glow(s, 8, 8, 7.9, "#e8fff8", 0.7)
            for k in range(7):
                a = k * 2 * math.pi / 7 + 0.3
                s.line(8, 8, 8 + math.cos(a) * 5.6, 8 + math.sin(a) * 5.6, "#ffffff", 0.6, 0.6)
            s.circle(8, 8, 2.4, fill="#ffffff")
        return s

    def sky_extras(self) -> dict[str, PropSpec]:
        extras = {
            f"ef.cloud.{i}": PropSpec((lambda i=i, w=w, h=h: self._wisp(61 + i * 13, w, h)), (0, 0))
            for i, (w, h) in enumerate([(280, 58), (210, 44), (340, 70)])
        }
        # Weather sprites resolve as ``particle.<name>`` (see ``weather``).
        extras["particle.ef_spore"] = PropSpec(lambda: self._particle("spore"), (8, 8))
        extras["particle.ef_firefly"] = PropSpec(lambda: self._particle("firefly"), (8, 8))
        return extras

    # ------------------------------------------------------------------ parallax layers
    def _far(self, seed: int, variant: int) -> Svg:
        """Distant trunks dissolving into the night, far ruins, forest line and mist."""
        w, h = 1200.0, 480.0
        r = Rand(seed)
        s = Svg(w, h)
        ground = 392.0
        # trunks are fully transparent where the moon sits (strip y < 150), so
        # they dissolve into the night instead of slicing the moon disc
        trunk_fill = s.linear(0, 150, 0, ground, [(0, "#18344e", 0), (0.4, "#1a3a54", 0.88), (1, "#244e62")])
        rim_fill = s.linear(0, 150, 0, ground, [(0, "#4a7c8c", 0), (0.5, "#4a7c8c", 0.45), (1, "#4a7c8c", 0.3)])
        n = 8
        for i in range(n):
            width = r.uniform(16, 32)
            cx = w * (i + 0.5) / n + r.uniform(-40, 40)
            cx = min(max(cx, width * 1.6), w - width * 1.6)
            trunk = _Trunk(cx, ground + 6, 120, width, r.uniform(-14, 14), seed + i, flare=1.0)
            s.path(trunk.outline(10), fill=trunk_fill)
            s.path(smooth_open([trunk.at(t, 0.8) for t in (0.05, 0.35, 0.7, 1.0)]), stroke=rim_fill, width=1.6)
            s.path(smooth_open([trunk.at(t, -0.2) for t in (0.05, 0.35, 0.7, 1.0)]), stroke="#10263a", width=1.4, opacity=0.4)
        # ruins on the horizon
        stone = s.linear(0, 140, 0, ground, [(0, "#244a60"), (1, "#2a5668")])
        if variant == 0:  # broken tower with a lit window
            tx = w * 0.62
            s.path(f"M{tx - 26} {ground} L{tx - 24} 176 L{tx - 16} 168 L{tx - 10} 176 L{tx - 2} 150 L{tx + 6} 162 L{tx + 14} 154 L{tx + 24} 170 "
                   f"L{tx + 26} {ground} Z", fill=stone)
            s.path(f"M{tx - 34} 230 L{tx + 34} 230 L{tx + 30} 240 L{tx - 30} 240 Z", fill="#2c5a70")
            s.path(f"M{tx - 7} 214 L{tx - 7} 200 Q{tx} 190 {tx + 7} 200 L{tx + 7} 214 Z", fill="#0f2232")
            _glow(s, tx, 206, 16, GLOW_TEAL, 0.45)
            s.path(f"M{tx - 4} 212 L{tx - 4} 202 Q{tx} 196 {tx + 4} 202 L{tx + 4} 212 Z", fill="#9ff6e6", opacity=0.75)
        else:  # arches of an old aqueduct
            ax = w * 0.3
            span = 70.0
            s.rect(ax - 10, 250, span * 3 + 20, 16, fill="#2c5a70")
            for k in range(3):
                x1 = ax + k * span
                s.path(f"M{x1 - 4} {ground} L{x1 - 4} 266 L{x1 + span + 4} 266 L{x1 + span + 4} {ground} L{x1 + span - 8} {ground} "
                       f"L{x1 + span - 8} 300 Q{x1 + span / 2} 270 {x1 + 8} 300 L{x1 + 8} {ground} Z", fill=stone)
            s.path(f"M{ax + span * 3 + 10} 250 L{ax + span * 3 + 26} 262 L{ax + span * 3 + 10} 266 Z", fill="#2c5a70")
            for k in range(4):
                _glow(s, ax + 10 + k * span * 0.98, 258, 7, GLOW_TEAL, 0.35)
        # distant forest line (rounded crowns) and floor
        crowns = s.linear(0, ground - 80, 0, ground + 30, [(0, "#24546a"), (1, "#1c4256")])
        x = 40.0
        while x < w - 40:
            rad = r.uniform(26, 40)
            cx = min(max(x, rad * 1.3), w - rad * 1.3)
            s.path(blob(cx, ground - rad * 0.35, rad * 1.3, rad * 0.75, 0.1, seed=x + seed), fill=crowns)
            x += r.uniform(46, 80)
        floor = [(x, ground - 8 + 4 * _wave(x, w, 3, seed)) for x in [i * w / 24 for i in range(25)]]
        s.path(smooth_open(floor) + f"L{w} {h} L0 {h} Z", fill=s.linear(0, ground - 12, 0, h, [(0, "#1d4658"), (1, "#163646")]))
        # fireflies and mist
        for _ in range(16):
            fx, fy = r.uniform(10, w - 10), r.uniform(120, ground - 10)
            _glow(s, fx, fy, 5, "#e8ff9a", 0.35)
            s.circle(fx, fy, r.uniform(0.7, 1.2), fill="#f4ffc8", opacity=0.9)
        _band(s, w, 250, 480, MIST, 0.2)
        return s

    def _vine(self, s: Svg, x: float, y1: float, y2: float, seed: float, lantern: bool) -> None:
        r = Rand(seed)
        pts = [(x + 6 * math.sin(i * 0.9 + seed) * (i / 6), y1 + (y2 - y1) * i / 6) for i in range(7)]
        s.path(smooth_open(pts), stroke="#183630", width=2.0)
        for i in range(1, 7):
            px, py = pts[i]
            side = 1 if i % 2 else -1
            s.path(_leaf(px + side * 4, py - 2, 9, 2.6, 90 + side * 55 + r.uniform(-10, 10)), fill="#1c4238")
            s.path(_leaf(px + side * 4, py - 2, 9, 2.6, 90 + side * 55), fill=None, stroke="#3f7f6c", width=0.6, opacity=0.6)
        if lantern:
            lx, ly = pts[-1]
            _glow(s, lx, ly + 6, 18, GLOW_GOLD, 0.45)
            s.path(blob(lx, ly + 6, 3.6, 5, 0.05, seed=seed), fill=s.radial(lx - 1, ly + 4, 6, [(0, "#ffffff"), (0.4, "#ffe9a0"), (1, "#e0a040")]))

    def _ruin_mid(self, s: Svg, x: float, ground: float, variant: int) -> None:
        stone = s.linear(x - 90, 0, x + 90, 0, [(0, "#22384a"), (0.6, "#30505e"), (1, "#3f6472")])
        edge = "#5a8494"
        if variant == 0:  # broken arch with a rune keystone
            for px, top in ((x - 64, ground - 170), (x + 64, ground - 118)):
                s.path(rounded_rect_path(px - 16, top, 32, ground - top + 4, 3), fill=stone)
                s.rect(px - 20, top - 8, 40, 10, fill="#2c4858", rx=2)
                s.line(px - 19, top - 7.5, px + 19, top - 7.5, edge, 1.4, 0.7)
                for yy in range(int(top + 26), int(ground), 30):
                    s.line(px - 15, yy, px + 15, yy, "#1a2c38", 1.2, 0.7)
                s.path(blob(px - 6, top - 9, 16, 5, 0.25, seed=px), fill="#2a5a4a")
            s.path(f"M{x - 80} {ground - 176} Q{x - 40} {ground - 236} {x + 6} {ground - 222} L{x + 10} {ground - 204} "
                   f"Q{x - 36} {ground - 214} {x - 48} {ground - 170} Z", fill=stone)
            s.path(f"M{x - 80} {ground - 176} Q{x - 40} {ground - 236} {x + 6} {ground - 222}", stroke=edge, width=1.6, opacity=0.6)
            kx, ky = x - 30, ground - 214
            _glow(s, kx, ky, 26, GLOW_TEAL, 0.5)
            s.path(_leaf(kx, ky, 12, 3.4, -60), fill="#b4fff0", opacity=0.9)
            for i, (hx, hl) in enumerate(((x - 64, 120), (x - 40, 80), (x - 12, 60))):
                self._vine(s, hx, ground - 220 + i * 10, ground - 220 + hl, x + i, i == 1)
            s.path(blob(x + 30, ground - 4, 14, 8, 0.2, seed=x), fill="#22384a")
            s.path(blob(x + 52, ground - 2, 9, 6, 0.2, seed=x + 1), fill="#2a4454")
        else:  # standing pillar with a crystal lantern and a fallen column
            s.path(rounded_rect_path(x - 18, ground - 150, 36, 154, 4), fill=stone)
            for fx in (-9, 0, 9):
                s.line(x + fx, ground - 140, x + fx, ground - 4, "#1c3040", 1.4, 0.6)
            s.path(f"M{x - 24} {ground - 150} L{x + 24} {ground - 150} L{x + 20} {ground - 162} L{x - 20} {ground - 162} Z", fill="#2c4858")
            _crystal_cluster(s, x, ground - 162, 22, CAP_CYAN, x, halo=0.55)
            for k in range(3):
                _glow(s, x, ground - 110 + k * 26, 9, GLOW_TEAL, 0.4)
                s.path(_leaf(x, ground - 110 + k * 26, 9, 2.4, -90), fill="#b4fff0", opacity=0.8)
            s.path(rounded_rect_path(x + 40, ground - 28, 110, 30, 14), fill=s.linear(0, ground - 28, 0, ground, [(0, "#34566a"), (1, "#1e3442")]))
            s.ellipse(x + 146, ground - 13, 9, 14, fill="#2a4454", stroke=edge, width=1.2)
            s.path(blob(x + 80, ground - 28, 26, 6, 0.3, seed=x), fill="#2a5a4a")
            self._vine(s, x - 14, ground - 152, ground - 70, x, False)

    def _mid(self, seed: int, variant: int) -> Svg:
        """Giant trunks rising into the canopy, ruins, lantern vines, glowing mushrooms and lit fog."""
        w, h = 1100.0, 640.0
        r = Rand(seed)
        s = Svg(w, h)
        ground = 545.0
        # lit fog between the trunks (the backdrop of the play band)
        _band(s, w, 300, 620, "#58aca0", 0.34)
        # a farther, hazier trunk
        far_x = w * (0.52 if variant == 0 else 0.18)
        thin = _Trunk(far_x, ground, -40, 46, r.uniform(-20, 20), seed + 7, flare=1.2)
        s.path(thin.outline(), fill=s.linear(far_x - 60, 0, far_x + 60, 0, [(0, "#183444"), (0.7, "#244a58"), (1, "#1c3c4c")]))
        for f in (-0.5, 0.0, 0.45):
            s.path(smooth_open([thin.at(t, f + 0.05 * math.sin(t * 7 + f)) for t in [0.03 + i * 0.12 for i in range(9)]]), stroke="#132a38",
                   width=1.6, opacity=0.5)
        s.path(smooth_open([thin.at(t, 0.92) for t in [0.1 + i * 0.11 for i in range(9)]]), stroke="#4f8890", width=1.4, opacity=0.3)
        # ruins
        self._ruin_mid(s, w * (0.5 if variant == 0 else 0.45), ground, variant)
        # giant trunks
        specs = ((w * 0.2, 104.0), (w * 0.8, 82.0)) if variant == 0 else ((w * 0.74, 112.0), (w * 0.12, 70.0))
        for k, (cx, width) in enumerate(specs):
            cx += r.uniform(-30, 30)
            cx = min(max(cx, width * 1.9), w - width * 1.9)
            self._giant_trunk(s, _Trunk(cx, ground, -110, width, r.uniform(-26, 26), seed + k * 3), r, hole=(k == variant % 2))
        # canopy band at the top (mostly behind the HUD) with moonlit leaf edges
        s.rect(0, 0, w, 34, fill="#08141e")
        x = 30.0
        while x < w - 30:
            rad = r.uniform(34, 56)
            cx = min(max(x, rad * 1.35), w - rad * 1.35)
            cy = r.uniform(26, 58)
            s.path(blob(cx, cy, rad * 1.35, rad * 0.8, 0.14, seed=cx + seed),
                   fill=s.radial(cx + rad * 0.3, cy + rad * 0.5, rad * 1.6, [(0, "#1c3c4a"), (0.6, "#0f2430"), (1, "#08141e")]))
            for j in range(5):
                lx = cx - rad + j * rad * 0.5 + r.uniform(-4, 4)
                ly = cy + rad * 0.62 + r.uniform(-4, 4)
                s.path(_leaf(lx, ly, 15, 4, 90 + r.uniform(-30, 30)), fill="#13303c", stroke="#3a6c76", width=0.8)
            x += r.uniform(50, 86)
        # lantern vines and moss curtains hanging from the canopy
        for k in range(7):
            vx = w * (k + 0.5) / 7 + r.uniform(-30, 30)
            self._vine(s, min(max(vx, 14), w - 14), 40, r.uniform(130, 300), seed + k, k % 3 == 1)
        # glowing mushrooms at the trunk bases and between them
        for k in range(9):
            mx = r.uniform(30, w - 30)
            pal = r.choice([CAP_CYAN, CAP_CYAN, CAP_VIOLET])
            hgt = r.uniform(14, 34)
            _mushroom(s, mx, ground + 2, hgt, hgt * r.uniform(0.38, 0.5), pal, r.uniform(-4, 4), halo=0.4, outline="#0c1a22", stem="#6f8c8c")
        # forest floor: undulating, sinking into darkness (pits look deep)
        floor = [(x, ground - 2 + 3 * _wave(x, w, 4, seed)) for x in [i * w / 30 for i in range(31)]]
        s.path(smooth_open(floor) + f"L{w} {h} L0 {h} Z", fill=s.linear(0, ground - 6, 0, h, [(0, "#122a30"), (0.4, "#0b1a20"), (1, "#060d12")]))
        _band(s, w, ground - 40, ground + 50, "#6cc4b4", 0.24)
        for _ in range(14):
            fx, fy = r.uniform(10, w - 10), r.uniform(200, ground - 20)
            _glow(s, fx, fy, 7, "#e8ff9a", 0.4)
            s.circle(fx, fy, r.uniform(0.9, 1.4), fill="#fbffd8")
        return s

    def _giant_trunk(self, s: Svg, tr: _Trunk, r: Rand, hole: bool) -> None:
        w = tr.width
        body = s.linear(tr.cx - w * 1.3, 0, tr.cx + w * 1.3, 0, [(0, "#0d1d28"), (0.32, "#152c3a"), (0.62, "#1e3c4a"), (0.8, "#2f5a66"),
                                                                 (1, "#152a36")])
        # flaring roots
        for side in (-1, 1):
            for k in range(2):
                sx, sy = tr.at(0.06 + k * 0.05, side * 0.8)
                reach = w * (0.55 + 0.4 * k) * side
                pts = [(sx, sy, w * 0.26), (sx + reach * 0.45, tr.ground - w * 0.1 + k * 4, w * 0.16), (sx + reach, tr.ground + 3, 1.5)]
                s.path(_taper(pts), fill=body)
                s.path(smooth_open([(p[0], p[1] - p[2] / 2) for p in pts]), stroke="#3f6a70", width=1.2, opacity=0.4)
        s.path(tr.outline(), fill=body)
        # bark grooves and lit ridges
        for k, f in enumerate((-0.68, -0.36, -0.05, 0.27, 0.56)):
            pts = [tr.at(t, f + 0.06 * math.sin(t * 9 + k)) for t in [0.02 + i * 0.098 for i in range(11)]]
            s.path(smooth_open(pts), stroke="#08141c", width=r.uniform(1.6, 2.8), opacity=0.6)
            if f > 0:
                s.path(smooth_open([(x + 3, y) for x, y in pts]), stroke="#5a8e96", width=0.9, opacity=0.3)
        s.path(smooth_open([tr.at(t, 0.97) for t in [0.12 + i * 0.088 for i in range(11)]]), stroke="#8fd2d0", width=2.2, opacity=0.35)
        # moss streaks climbing the shadow side (vertical, so they never read as ledges)
        for k, (f, t1, thick) in enumerate(((-0.8, 0.42, w * 0.22), (-0.45, 0.26, w * 0.13))):
            centre = []
            for j in range(9):
                t = 0.02 + (t1 - 0.02) * j / 8
                x, y = tr.at(t, f + 0.05 * math.sin(j * 1.9 + k))
                centre.append((x, y, thick * math.sin(math.pi * (0.08 + 0.84 * j / 8)) ** 0.7))
            pts_l = [(x - th / 2, y) for x, y, th in centre]
            pts_r = [(x + th / 2, y) for x, y, th in reversed(centre)]
            d = smooth_open(pts_l) + f"L{pts_r[0][0]:.2f} {pts_r[0][1]:.2f}" + _curve(pts_r) + "Z"
            s.path(d, fill=s.linear(centre[0][0] - thick, 0, centre[0][0] + thick, 0, [(0, "#122a28"), (0.6, "#1b3f38"), (1, "#24503f")]),
                   opacity=0.75)
        # glowing bracket fungi on the lit side
        fx, fy = tr.at(0.36, 0.97)
        _brackets(s, fx - 1, fy, r.uniform(13, 17), 1, halo=0.4)
        # a branch stub hung with moss
        bx, by = tr.at(0.5, -0.95)
        s.path(_taper([(bx + 6, by, 12), (bx - 22, by - 8, 7), (bx - 40, by - 20, 1.5)]), fill=body)
        s.path(smooth_open([(bx + 4, by - 5), (bx - 22, by - 11.5), (bx - 39, by - 21)]), stroke="#3f6a70", width=1.0, opacity=0.5)
        _moss_curtain(s, bx - 18, by - 10, 30, r.uniform(46, 70), bx + by)
        if hole:  # a hollow with something watching
            hx, hy = tr.at(0.22, -0.15)
            s.ellipse(hx, hy, w * 0.11, w * 0.17, fill="#050d12", stroke="#2c4c56", width=2.4)
            for ex in (-3.2, 3.2):
                _glow(s, hx + ex, hy, 5, GLOW_GOLD, 0.6)
                s.ellipse(hx + ex, hy, 1.5, 1.1, fill="#fff2a8")

    def _near(self, seed: int) -> Svg:
        """Undergrowth peeking above the ground line: bushes, ferns, flowers; a dark drop below."""
        w, h = 900.0, 260.0
        r = Rand(seed)
        s = Svg(w, h)
        ground = 165.0
        x = 30.0
        while x < w - 30:
            rad = r.uniform(24, 40)
            cx = min(max(x, rad * 1.3), w - rad * 1.3)
            cy = ground - rad * 0.32
            s.path(blob(cx, cy, rad * 1.25, rad * 0.78, 0.14, seed=cx + seed),
                   fill=s.radial(cx + rad * 0.35, cy - rad * 0.7, rad * 1.7, [(0, "#24564c"), (0.55, "#143a34"), (1, "#0c2624")]))
            for j in range(5):  # moonlit leaf tips along the crown (filled, never outlined like eyes)
                a = math.radians(-160 + j * 35)
                lx, ly = cx + math.cos(a) * rad * 1.05, cy + math.sin(a) * rad * 0.66
                s.path(_leaf(lx, ly, 11, 2.8, math.degrees(a)), fill="#2f6e5c", opacity=0.9)
            s.path(f"M{cx - rad * 0.7:.2f} {cy - rad * 0.62:.2f} Q{cx:.2f} {cy - rad * 0.95:.2f} {cx + rad * 0.7:.2f} {cy - rad * 0.62:.2f}",
                   stroke="#4f9a84", width=1.2, opacity=0.5)
            x += r.uniform(56, 100)
        for _ in range(7):  # ferns
            fx = r.uniform(40, w - 40)
            for k in range(5):
                a = math.radians(-90 + (k - 2) * 26 + r.uniform(-6, 6))
                ln = r.uniform(26, 40) * (1 - abs(k - 2) * 0.12)
                ex, ey = fx + math.cos(a) * ln, ground + math.sin(a) * ln * 0.85
                cx_, cy_ = fx + math.cos(a) * ln * 0.55 + math.cos(a + 1.2) * 6, ground + math.sin(a) * ln * 0.55 - 4
                s.path(f"M{fx:.2f} {ground:.2f} Q{cx_:.2f} {cy_:.2f} {ex:.2f} {ey:.2f}", stroke="#1d4a3e", width=1.4)
                for j in range(1, 6):
                    t = j / 6
                    px = (1 - t) ** 2 * fx + 2 * (1 - t) * t * cx_ + t * t * ex
                    py = (1 - t) ** 2 * ground + 2 * (1 - t) * t * cy_ + t * t * ey
                    for side in (-1, 1):
                        s.path(_leaf(px + side * 2.5, py, 7 * (1 - t * 0.5), 1.8, math.degrees(a) + side * 60), fill="#1f5444")
        for _ in range(5):  # glowing bell flowers
            fx = r.uniform(30, w - 30)
            top = ground - r.uniform(22, 44)
            s.path(f"M{fx:.2f} {ground:.2f} Q{fx - 3:.2f} {top + 10:.2f} {fx + 5:.2f} {top:.2f}", stroke="#1d4a3e", width=1.2)
            color = r.choice([GLOW_GOLD, "#ffc4ec", "#c8f4ff"])
            _glow(s, fx + 6, top + 5, 14, color, 0.5)
            s.path(f"M{fx + 2.5:.2f} {top + 1.5:.2f} Q{fx + 6:.2f} {top - 1:.2f} {fx + 9.5:.2f} {top + 1.5:.2f} L{fx + 10.5:.2f} {top + 8:.2f} "
                   f"Q{fx + 6:.2f} {top + 6:.2f} {fx + 1.5:.2f} {top + 8:.2f} Z", fill=s.linear(0, top, 0, top + 8, [(0, "#ffffff"), (1, color)]))
        for _ in range(6):  # small glowing mushroom clusters
            mx = r.uniform(20, w - 40)
            for j in range(r.choice([1, 2, 3])):
                hgt = r.uniform(7, 15)
                _mushroom(s, mx + j * 7, ground + 1, hgt, hgt * 0.45, r.choice([CAP_CYAN, CAP_VIOLET]), r.uniform(-2, 2), halo=0.5,
                          outline="#0a1a1c", spots=2, stem="#86a2a0")
        floor = [(x, ground - 3 + 2.5 * _wave(x, w, 5, seed)) for x in [i * w / 30 for i in range(31)]]
        s.path(smooth_open(floor) + f"L{w} {h} L0 {h} Z", fill=s.linear(0, ground - 5, 0, h, [(0, "#0f2626"), (0.5, "#081618"), (1, "#03080a")]))
        _band(s, w, ground - 46, ground + 44, "#74c8b8", 0.2)
        return s

    def layer_art(self) -> dict[str, PropSpec]:
        art = {}
        for i in range(2):
            art[f"ef.far.{i}"] = PropSpec((lambda i=i: self._far(13 + i * 7, i)), (0, 0))
            art[f"ef.mid.{i}"] = PropSpec((lambda i=i: self._mid(23 + i * 11, i)), (0, 0))
            art[f"ef.near.{i}"] = PropSpec((lambda i=i: self._near(43 + i * 5)), (0, 0))
        return art

    def layers(self) -> list[Layer]:
        # Tall strips: the giant trunks run above the top of the screen and the
        # dark floor reaches below its bottom (pits read as a misty drop).
        return [
            Layer("far", 0.08, ["ef.far.0", "ef.far.1"], 1200, 70, vertical=0.05),
            Layer("mid", 0.24, ["ef.mid.0", "ef.mid.1"], 1100, 92, vertical=0.15),
            Layer("near", 0.48, ["ef.near.0", "ef.near.1"], 900, 100, vertical=0.32),
        ]

    # ------------------------------------------------------------------ terrain
    def terrain(self, style: str, w: float, h: float, seed: int, left: bool, right: bool, top: bool = True, x0: float = 0.0,
                surface: str = "normal") -> Svg:
        """Mossy soil chunk. World-x functions drive everything that crosses a
        chunk border (strands, roots, rim), so adjacent chunks join seamlessly."""
        if style == "cave":
            return self._cave(w, h, seed, left, right, x0)
        hr = self.terrain_headroom
        s = Svg(w, h + hr)
        r = Rand(seed)
        y0 = hr
        bottom = h + hr
        rl, rr = (12.0 if left else 0.0), (12.0 if right else 0.0)
        yb = y0 + (5.0 if top else 0.0)
        body = (f"M{rl:.1f} {yb:.1f} L{w - rr:.1f} {yb:.1f} Q{w:.1f} {yb:.1f} {w:.1f} {yb + rr:.1f} L{w:.1f} {bottom:.1f} "
                f"L0 {bottom:.1f} L0 {yb + rl:.1f} Q0 {yb:.1f} {rl:.1f} {yb:.1f} Z")
        s.path(body, fill=s.linear(0, y0, 0, y0 + h, [(0, SOIL_TOP), (0.3, SOIL), (1, SOIL_DEEP)]))
        # strata (world-aligned samples)
        xs = [gx - x0 for gx in self._grid(x0, w, 16.0)]
        for k in range(1, 4):
            yy = y0 + 34 + k * 28
            if yy > bottom - 8:
                break
            pts = [(lx, yy + 3.5 * math.sin((x0 + lx) * 0.041 + k * 1.9) + 2 * math.sin((x0 + lx) * 0.013 + k)) for lx in xs]
            s.path(smooth_open(pts), stroke=shade(SOIL, -0.3), width=2.2, opacity=0.4)
        # glowing mycelium threads (chunk-local, kept inside the chunk)
        for _ in range(max(1, int(w / 130))):
            if bottom - y0 < 60 or w < 70:
                break
            mx, my = r.uniform(32, w - 32), r.uniform(y0 + 42, min(bottom - 16, y0 + 116))
            _glow(s, mx, my, 16, GLOW_TEAL, 0.18)
            for _b in range(5):
                a = r.uniform(0, 2 * math.pi)
                ln = r.uniform(10, 26)
                pts = [(mx, my), (mx + math.cos(a) * ln * 0.5 + r.uniform(-3, 3), my + math.sin(a) * ln * 0.3 + r.uniform(-2, 2)),
                       (mx + math.cos(a) * ln, my + math.sin(a) * ln * 0.55)]
                s.path(smooth_open(pts), stroke=GLOW_CYAN, width=0.55, opacity=0.4)
                s.circle(pts[-1][0], pts[-1][1], 0.8, fill=GLOW_CYAN, opacity=0.8)
        # embedded stones, some wearing moss
        for _ in range(max(2, int(w / 38))):
            pr = r.uniform(2.4, 6.8)
            px, py = r.uniform(pr * 1.5, w - pr * 1.5), r.uniform(y0 + 26, bottom - 8)
            s.path(blob(px, py, pr * 1.35, pr, 0.12, seed=px), fill=s.radial(px - pr * 0.4, py - pr * 0.5, pr * 1.7,
                   [(0, STONE_LIGHT), (0.55, STONE), (1, STONE_DARK)]), stroke=shade(SOIL_DEEP, -0.3), width=0.8, opacity=0.9)
            if pr > 4.5:
                s.path(blob(px - pr * 0.3, py - pr * 0.7, pr * 0.8, pr * 0.35, 0.2, seed=py), fill="#3f8a64", opacity=0.9)
        # roots diving from the moss into the soil (world-aligned segments)
        if h > 40:
            self._roots(s, w, x0, y0, bottom)
        # exposed cliff sides: shadowed face, dangling rootlets, a glowing shelf fungus
        for side, exposed in ((-1, left), (1, right)):
            if not exposed:
                continue
            ex = 0.0 if side < 0 else w
            s.path(f"M{ex:.1f} {y0 + 10:.1f} L{ex - side * 8:.1f} {y0 + 14:.1f} L{ex - side * 6:.1f} {bottom:.1f} L{ex:.1f} {bottom:.1f} Z",
                   fill="#0e0a10", opacity=0.45)
            for k in range(3):
                ry = y0 + 16 + k * 13 + r.uniform(-3, 3)
                pts = [(ex - side * 3, ry), (ex - side * (1.5 + r.uniform(0, 2)), ry + 7), (ex - side * r.uniform(0.5, 3), ry + 14 + r.uniform(0, 6))]
                s.path(smooth_open(pts), stroke=ROOT_LIGHT, width=1.1, opacity=0.75)
            if h > 50:
                # the face is inside the chunk, so the fungi grow inward from it
                _brackets(s, ex, y0 + 36 + r.uniform(0, 14), 7.5, -side, halo=0.45)
        if top:
            self._moss_cap(s, w, x0, y0, left, right, r, MOSS.get(surface, MOSS["normal"]))
        return s

    @staticmethod
    def _grid(x0: float, w: float, step: float, margin: int = 2) -> list[float]:
        """World x positions of a fixed grid covering the chunk plus ``margin`` cells."""
        first = math.floor(x0 / step) - margin
        last = math.ceil((x0 + w) / step) + margin
        return [i * step for i in range(first, last + 1)]

    def _roots(self, s: Svg, w: float, x0: float, y0: float, bottom: float) -> None:
        period = 150.0
        fill = s.linear(0, y0, 0, y0 + 60, [(0, ROOT_LIGHT), (0.4, ROOT), (1, shade(ROOT, -0.3))])
        for k in range(math.floor((x0 - 260) / period), math.ceil((x0 + w + 40) / period) + 1):
            if _hash(k, 1.3) < 0.22:
                continue
            start = k * period + _hash(k, 2.1) * 70
            length = 80 + 120 * _hash(k, 3.7)
            depth = min(bottom - y0 - 18, 16 + 34 * _hash(k, 4.4))
            direction = 1 if _hash(k, 5.9) > 0.45 else -1
            thick = 3.2 + 3.6 * _hash(k, 6.2)
            centre = []
            for j in range(9):
                t = j / 8
                gx = start + direction * length * t
                gy = y0 + 9 + depth * math.sin(min(1.0, t * 1.15) * math.pi * 0.62) + 2.2 * math.sin(gx * 0.08 + k)
                centre.append((gx - x0, gy, thick * (1 - t) ** 0.75 + 0.5))
            if max(p[0] for p in centre) < -10 or min(p[0] for p in centre) > w + 10:
                continue
            s.path(_taper(centre), fill=fill, stroke=ROOT_DARK, width=0.8)
            s.path(smooth_open([(x, y - t * 0.3) for x, y, t in centre[:6]]), stroke="#c49a78", width=max(0.5, thick * 0.18), opacity=0.5)
            for j in (3, 5):  # rootlets branching off the lower side
                px, py, pt = centre[j]
                bend = (_hash(k, 7.0 + j) - 0.5) * 16
                rootlet = [(px, py + pt * 0.3), (px + bend * 0.5 + direction * 4, py + 8), (px + bend, py + 15 + 10 * _hash(k, 8.0 + j))]
                s.path(smooth_open(rootlet), stroke=ROOT, width=max(0.6, pt * 0.35), opacity=0.9)

    def _moss_cap(self, s: Svg, w: float, x0: float, y0: float, left: bool, right: bool, r: Rand,
                  moss: tuple[str, str, str, str, str]) -> None:
        top_c, body_c, dark_c, deep_c, rim_c = moss
        step = 6.0

        def top_y(gx: float) -> float:
            return y0 - 0.7 - 1.5 * (0.5 + 0.5 * math.sin(gx * 0.21 + 1.6 * math.sin(gx * 0.047)))

        def lip_y(gx: float) -> float:
            return y0 + 7.6 + 1.2 * math.sin(gx * 0.11 + 0.6) + 0.8 * math.sin(gx * 0.037)

        cells = range(math.floor(x0 / step) - 3, math.ceil((x0 + w) / step) + 4)
        lo, hi = (4.5 if left else -1e9), (w - 4.5 if right else 1e9)
        top_pts = [(i * step - x0, top_y(i * step)) for i in cells if lo <= i * step - x0 <= hi]
        if left:
            top_pts = [(0.3, y0 + 6.0), (1.4, y0 + 1.6)] + top_pts
        if right:
            top_pts = top_pts + [(w - 1.4, y0 + 1.6), (w - 0.3, y0 + 6.0)]
        fringe: list[Pt] = []
        tips: list[tuple[float, float, int]] = []
        if left:
            fringe += [(0.3, y0 + 9), (1.6, y0 + 19), (3.2, y0 + 10.5), (4.6, y0 + 15)]
        for i in cells:
            gx = i * step
            lx = gx - x0
            if not lo <= lx <= hi:
                continue
            ln = 1.0 + 13.0 * _hash(i, 0.7) ** 2.6
            wd = 2.4 + 1.4 * _hash(i, 1.9)
            jit = (_hash(i, 2.3) - 0.5) * 1.6
            lip = lip_y(gx)
            fringe.append((lx - step / 2, lip_y(gx - step / 2)))
            if ln < 3:
                fringe.append((lx + jit * 0.3, lip + ln))
            else:
                fringe += [(lx - wd * 0.5, lip + 0.8), (lx - wd * 0.28 + jit * 0.3, lip + ln * 0.62), (lx + jit, lip + ln),
                           (lx + wd * 0.28 + jit * 0.3, lip + ln * 0.62), (lx + wd * 0.5, lip + 0.8)]
                if ln > 8 and _hash(i, 4.1) > 0.4:
                    tips.append((lx + jit, lip + ln, i))
        if right:
            fringe += [(w - 4.6, y0 + 15), (w - 3.2, y0 + 10.5), (w - 1.6, y0 + 19), (w - 0.3, y0 + 9)]
        back = list(reversed(fringe))
        d = smooth_open(top_pts, 0.8) + f"L{back[0][0]:.2f} {back[0][1]:.2f}" + _curve(back, 0.75) + "Z"
        # soft shadow cast by the cap on the soil
        s.path(smooth_open([(p[0], p[1] + 3) for p in fringe], 0.75), stroke="#0c080c", width=4, opacity=0.25)
        s.path(d, fill=s.linear(0, y0 - 3, 0, y0 + 22, [(0, top_c), (0.16, body_c), (0.48, dark_c), (1, deep_c)]))
        edge = shade(deep_c, -0.5)
        s.path(smooth_open(fringe, 0.75), stroke=edge, width=1.1)
        if left:
            s.path(f"M{top_pts[0][0]:.2f} {top_pts[0][1]:.2f} L{fringe[0][0]:.2f} {fringe[0][1]:.2f}", stroke=edge, width=1.2)
        if right:
            s.path(f"M{top_pts[-1][0]:.2f} {top_pts[-1][1]:.2f} L{fringe[-1][0]:.2f} {fringe[-1][1]:.2f}", stroke=edge, width=1.2)
        # cushion texture: curls and speckles inside the cap
        for _ in range(max(2, int(w / 14))):
            cx = r.uniform(3, w - 3)
            cy = y0 + r.uniform(1.5, 5.5)
            s.path(f"M{cx - 2.2:.2f} {cy + 0.8:.2f} Q{cx:.2f} {cy - 1.2:.2f} {cx + 2.2:.2f} {cy + 0.8:.2f}", stroke=dark_c, width=0.7, opacity=0.55)
            s.circle(cx + r.uniform(-4, 4), cy - 1.5, 0.55, fill=rim_c, opacity=0.7)
        # moonlit rim on the cushion top
        s.path(smooth_open(top_pts, 0.8), stroke=rim_c, width=1.5, opacity=0.9)
        # bioluminescent droplets at the tips of long strands
        for tx, ty, i in tips:
            _glow(s, tx, ty, 4.2, GLOW_CYAN, 0.55)
            s.circle(tx, ty - 0.2, 0.8, fill="#effffb")
        # life above the surface: moss sporophytes, sprouts and glowing mushrooms
        for _ in range(max(2, int(w / 11))):
            bx = r.uniform(3, w - 3)
            sh = r.uniform(3.5, 8.0)
            lean = r.uniform(-1.6, 1.6)
            s.path(f"M{bx:.2f} {y0:.2f} Q{bx + lean * 0.2:.2f} {y0 - sh * 0.6:.2f} {bx + lean:.2f} {y0 - sh:.2f}", stroke="#8a7a52", width=0.4)
            s.ellipse(bx + lean, y0 - sh - 0.6, 0.55, 1.0, fill=r.choice(["#e8c878", "#d2b060", "#bff8e0"]))
        for _ in range(max(1, int(w / 26))):
            bx = r.uniform(4, w - 4)
            for side in (-1, 1):
                s.path(_leaf(bx + side * 1.6, y0 - 1.8, 4.2, 1.3, -90 + side * 50), fill=r.choice([top_c, body_c]))
        for _ in range(max(1, int(w / 105))):
            mx = r.uniform(10, max(11, w - 24))
            pal = CAP_CYAN if r.next() < 0.7 else CAP_VIOLET
            for j in range(r.choice([1, 2, 2, 3])):
                hgt = r.uniform(4.5, 10.0) * (1 - j * 0.22)
                _mushroom(s, mx + j * r.uniform(3.6, 5.2), y0 + 0.5, hgt, hgt * 0.42, pal, r.uniform(-1.4, 1.4), halo=0.55,
                          outline=INK, spots=2)

    def _cave(self, w: float, h: float, seed: int, left: bool, right: bool, x0: float) -> Svg:
        """Root-cave rock: dark stone, roots threading through, glowing crystals."""
        r = Rand(seed)
        hr = self.terrain_headroom
        s = Svg(w, h + hr)
        y0 = hr
        bottom = h + hr
        rl, rr = (6.0 if left else 0.0), (6.0 if right else 0.0)
        body = (f"M{rl:.1f} {y0:.1f} L{w - rr:.1f} {y0:.1f} Q{w:.1f} {y0:.1f} {w:.1f} {y0 + rr:.1f} L{w:.1f} {bottom - rr:.1f} "
                f"Q{w:.1f} {bottom:.1f} {w - rr:.1f} {bottom:.1f} L{rl:.1f} {bottom:.1f} Q0 {bottom:.1f} 0 {bottom - rl:.1f} "
                f"L0 {y0 + rl:.1f} Q0 {y0:.1f} {rl:.1f} {y0:.1f} Z")
        depth = min(h, 140.0)
        s.path(body, fill=s.linear(0, y0, 0, y0 + depth, [(0, "#3a4154"), (0.35, "#272d3e"), (1, "#171b27")]))
        # strata (world-aligned) and rock facets that fade with depth
        for k in range(1, 6):
            yy = y0 + 14 + k * 22
            if yy > bottom - 6:
                break
            pts = [(gx - x0, yy + 3 * math.sin(gx * 0.03 + k * 2.1)) for gx in self._grid(x0, w, 20.0)]
            s.path(smooth_open(pts), stroke="#0e1118", width=1.6, opacity=0.5 - k * 0.06)
        reach = min(h, 150.0)
        for _ in range(max(2, int(w * reach / 1700))):
            pr = r.uniform(4, 12)
            px = r.uniform(pr * 1.6, w - pr * 1.6)
            py = y0 + 6 + (reach - 12) * r.next() ** 1.5
            fade = max(0.3, 1 - (py - y0) / 160)
            s.path(blob(px, py, pr * 1.5, pr, 0.18, seed=px + py), fill=r.choice(["#363d50", "#2a3042", "#40485e"]), opacity=0.8 * fade)
            s.path(f"M{px - pr * 1.1:.2f} {py - pr * 0.45:.2f} Q{px - pr * 0.2:.2f} {py - pr * 1.05:.2f} {px + pr * 0.9:.2f} {py - pr * 0.55:.2f}",
                   stroke="#5c6680", width=0.9, opacity=0.45 * fade)
        for _ in range(max(1, int(w / 90))):  # cracks
            cx = r.uniform(10, w - 10)
            pts = [(cx, y0 + r.uniform(4, 20))]
            for _k in range(4):
                pts.append((pts[-1][0] + r.uniform(-8, 8), pts[-1][1] + r.uniform(6, 14)))
            s.path(smooth_open(pts), stroke="#10131c", width=1.2, opacity=0.7)
        if h > 30:
            self._roots(s, w, x0 + 37.0, y0 - 4, bottom)
        if h > 170:  # a faint luminous mineral vein deep in the rock (world-aligned)
            vein = [(gx - x0, y0 + 150 + 14 * math.sin(gx * 0.011) + 5 * math.sin(gx * 0.047)) for gx in self._grid(x0, w, 16.0)]
            s.path(smooth_open(vein), stroke=GLOW_TEAL, width=2.4, opacity=0.12)
            s.path(smooth_open(vein), stroke=GLOW_CYAN, width=0.7, opacity=0.4)
            for gx in self._grid(x0, w, 16.0, 0):
                i = int(round(gx / 16.0))
                if _hash(i, 3.3) > 0.7:
                    lx = gx - x0
                    ly = y0 + 150 + 14 * math.sin(gx * 0.011) + 5 * math.sin(gx * 0.047)
                    _glow(s, lx, ly, 6, GLOW_CYAN, 0.35)
        for _ in range(max(1, int(w * min(h, 200) / 16000))):
            cx, cy = r.uniform(18, w - 18), r.uniform(y0 + 16, max(y0 + 17, min(bottom - 10, y0 + 190)))
            _crystal_cluster(s, cx, cy, r.uniform(7, 12) * (1.0 if cy < y0 + 90 else 0.75), r.choice([CAP_CYAN, CAP_VIOLET]), cx + cy,
                             halo=0.4 if cy < y0 + 90 else 0.28)
        # stone rim with glowing lichen (world-aligned)
        rim = [(gx - x0, y0 + 1.4 + 0.9 * math.sin(gx * 0.08)) for gx in self._grid(x0, w, 8.0)]
        s.path(smooth_open(rim), stroke="#6c778e", width=2.4, opacity=0.85)
        for gx in self._grid(x0, w, 8.0, 0):
            i = int(round(gx / 8.0))
            if _hash(i, 9.1) > 0.78:
                lx = gx - x0
                _glow(s, lx, y0 + 3, 4, GLOW_CYAN, 0.5)
                s.circle(lx, y0 + 3, 0.8, fill="#e6fffa")
        return s

    def cave_sky(self) -> Svg:
        """Root cave: hanging roots, glow-worm threads and crystal light."""
        s = Svg(960, 540)
        s.rect(0, 0, 960, 540, fill=s.linear(0, 0, 0, 540, [(0, "#070c12"), (0.45, "#0e1a22"), (1, "#081016")]))
        r = Rand(29)
        # back wall: rock ledges
        for k, (y, color) in enumerate(((150, "#101c26"), (330, "#13222c"), (460, "#0c161e"))):
            pts = [(x, y + 26 * _wave(x, 960, 2 + k, k) + 12 * _wave(x, 960, 5, k * 2)) for x in [i * 40.0 for i in range(25)]]
            s.path(smooth_open(pts) + "L960 540 L0 540 Z", fill=color, opacity=0.85)
        # stalactites
        for _ in range(16):
            x, ln = r.uniform(0, 960), r.uniform(30, 110)
            wd = r.uniform(10, 26)
            s.path(f"M{x - wd:.1f} 0 Q{x - wd * 0.3:.1f} {ln * 0.6:.1f} {x:.1f} {ln:.1f} Q{x + wd * 0.3:.1f} {ln * 0.6:.1f} {x + wd:.1f} 0 Z",
                   fill="#141f2a")
        # great roots coming through the ceiling
        for k, (x, reach, thick) in enumerate(((120, 300, 30), (390, 200, 22), (610, 360, 34), (840, 240, 26))):
            pts = []
            for j in range(9):
                t = j / 8
                pts.append((x + 40 * math.sin(t * 3.2 + k) + 18 * t * (1 if k % 2 else -1), -10 + reach * t, thick * (1 - t) ** 0.7 + 1.5))
            s.path(_taper(pts), fill=s.linear(x - thick, 0, x + thick, 0, [(0, "#1c1416"), (0.6, "#3a2c28"), (1, "#24181a")]))
            s.path(smooth_open([(px + pt * 0.32, py) for px, py, pt in pts[:7]]), stroke="#6a5444", width=1.4, opacity=0.5)
            for j in (3, 5):
                px, py, pt = pts[j]
                side = 1 if (j + k) % 2 else -1
                s.path(smooth_open([(px, py), (px + side * 22, py + 30), (px + side * 30, py + 70)]), stroke="#2e2220", width=max(1.5, pt * 0.3))
        # glow-worm threads
        for _ in range(26):
            x, ln = r.uniform(10, 950), r.uniform(30, 160)
            s.line(x, 0, x, ln, "#8ff0e0", 0.6, 0.28)
            for j in range(3):
                yy = ln * (0.4 + 0.3 * j)
                s.circle(x, yy, 0.9, fill="#c8fff4", opacity=0.75)
            _glow(s, x, ln, 9, GLOW_CYAN, 0.45)
            s.circle(x, ln, 1.6, fill="#e8fffb")
        # crystal clusters lighting the walls
        for x, y, size, pal, up in ((70, 520, 46, CAP_CYAN, True), (300, 430, 26, CAP_VIOLET, True), (560, 500, 34, CAP_CYAN, True),
                                     (800, 410, 30, CAP_VIOLET, True), (930, 515, 40, CAP_CYAN, True), (470, 70, 24, CAP_CYAN, False),
                                     (700, 40, 20, CAP_VIOLET, False)):
            _crystal_cluster(s, x, y, size, pal, x + y, up=up, halo=0.5)
        for _ in range(30):
            x, y = r.uniform(0, 960), r.uniform(100, 520)
            s.circle(x, y, r.uniform(0.6, 1.3), fill="#bff8ff", opacity=r.uniform(0.3, 0.8))
        _band(s, 960, 430, 560, "#3c8c8c", 0.2)
        return s

    # ------------------------------------------------------------------ blocks and platforms
    def block(self, kind: str, w: float, h: float) -> Svg:
        s = Svg(w, h)
        if kind in ("question", "used"):
            self._rune_block(s, w, h, kind == "used")
        elif kind == "brick":
            self._stone_bricks(s, w, h)
        return s

    def _rune_block(self, s: Svg, w: float, h: float, used: bool) -> None:
        """Carved honey-wood box with a stone inlay holding a glowing leaf rune."""
        wood = ("#eab06a", "#b06e30", "#6c3c1a") if not used else ("#8c7e72", "#5f5248", "#3a302c")
        s.path(rounded_rect_path(0.6, 0.6, w - 1.2, h - 1.2, 5), fill=s.linear(0, 0, 0, h, [(0, wood[0]), (0.55, wood[1]), (1, wood[2])]),
               stroke=INK, width=1.3)
        for k, gy in enumerate((h * 0.16, h * 0.84)):
            sign = 1 if k else -1
            s.path(smooth_open([(3, gy), (w * 0.3, gy + 0.9 * sign), (w * 0.7, gy - 0.7 * sign), (w - 3, gy)]), stroke=shade(wood[2], -0.1),
                   width=0.7, opacity=0.55)
        s.path(f"M4.5 2.3 L{w - 4.5:.2f} 2.3", stroke=shade(wood[0], 0.5), width=1.1, opacity=0.85)
        px, py = 5.6, 4.6
        pw, ph = w - 2 * px, h - 2 * py
        inlay = [(0, "#1a2c34"), (1, "#0d151b")] if not used else [(0, "#2e2a28"), (1, "#1e1a19")]
        s.path(rounded_rect_path(px, py, pw, ph, 3.4), fill=s.linear(0, py, 0, py + ph, inlay), stroke=shade(wood[2], -0.45), width=0.9)
        s.path(f"M{px + 2:.2f} {py + ph + 0.4:.2f} L{px + pw - 2:.2f} {py + ph + 0.4:.2f}", stroke=shade(wood[0], 0.3), width=0.8, opacity=0.7)
        cx, cy = w / 2, h / 2
        size = min(pw * 0.9, ph * 1.25)
        if not used:
            _glow(s, cx, cy, min(pw, ph) * 0.95, GLOW_LEAF, 0.7)
            s.path(_leaf(cx, cy, size * 0.92, size * 0.3, -32), fill=s.radial(cx - 1, cy - 1, size * 0.6, [(0, "#ffffff"), (0.4, "#f4ffb6"),
                   (1, "#86e070")]), stroke="#3a8a3a", width=0.7)
            a = math.radians(-32)
            ux, uy = math.cos(a), math.sin(a)
            s.line(cx - ux * size * 0.42, cy - uy * size * 0.42, cx + ux * size * 0.4, cy + uy * size * 0.4, "#5aa84a", 0.6)
            for t in (-0.2, 0.05, 0.25):
                bx, by = cx + ux * size * t, cy + uy * size * t
                for side in (-1, 1):
                    s.line(bx, by, bx + (ux * 0.6 - uy * side) * size * 0.13, by + (uy * 0.6 + ux * side) * size * 0.13, "#5aa84a", 0.5)
            sx, sy = cx - ux * size * 0.46, cy - uy * size * 0.46
            s.path(f"M{sx:.2f} {sy:.2f} q-2.2 1.6 -1 3.2 q1.4 1.2 2.4 -0.4", stroke="#c8ff8a", width=0.8)
            s.polygon(star_points(cx + size * 0.34, cy - ph * 0.22, 2.4, 0.5, 4), fill="#ffffff", opacity=0.9)
        else:
            s.path(_leaf(cx, cy, size * 0.92, size * 0.3, -32), fill="#141b20", stroke=shade(wood[1], -0.15), width=0.8)
            s.path(blob(5, 2.6, 7, 2.6, 0.3, seed=w), fill="#3f8a64")
            s.path(f"M3 3.5 q0.6 3 -0.2 5", stroke="#2f7a5a", width=1.0)
        for qx, qy in ((3.1, 3.1), (w - 3.1, 3.1), (3.1, h - 3.1), (w - 3.1, h - 3.1)):
            s.circle(qx, qy, 1.05, fill=shade(wood[2], -0.35))
        # a tuft of moss on the top edge (forest identity)
        mx = w * 0.72
        s.path(blob(mx, 1.6, 6, 1.9, 0.25, seed=w + h), fill="#5dc28c" if not used else "#4a8a64")
        s.path(f"M{mx - 3:.2f} 2.6 q0.4 2.4 -0.4 4.4 M{mx + 1.5:.2f} 2.8 q0.3 1.8 -0.2 3", stroke="#2f8266", width=0.9)

    def _stone_bricks(self, s: Svg, w: float, h: float) -> None:
        """Mossy blue-grey stone bricks (breakable)."""
        r = Rand(int(w * 13 + h))
        s.path(rounded_rect_path(0.6, 0.6, w - 1.2, h - 1.2, 3), fill="#1e2832", stroke=INK, width=1.2)
        rows = 2
        rh = (h - 2) / rows
        tones = [("#93a6b0", "#5c6c78"), ("#8aa2a6", "#56706e"), ("#9ca8b6", "#606a7c")]
        for row in range(rows):
            y = 1 + row * rh
            x = -(0 if row % 2 == 0 else 10.0)
            i = 0
            while x < w:
                bx0, bx1 = max(1.4, x + 1.1), min(w - 1.4, x + 20 - 1.1)
                if bx1 > bx0 + 2:
                    t0, t1 = tones[(row * 2 + i) % 3]
                    s.path(rounded_rect_path(bx0, y + 1.0, bx1 - bx0, rh - 2.0, 1.8), fill=s.linear(0, y, 0, y + rh, [(0, t0), (1, t1)]),
                           stroke="#28323e", width=0.7)
                    s.line(bx0 + 1, y + 2.1, bx1 - 1, y + 2.1, "#d4e4ea", 0.8, 0.6)
                    if r.next() < 0.45:  # hairline crack rising from the bottom edge
                        cx = r.uniform(bx0 + 3, bx1 - 3)
                        s.path(f"M{cx:.2f} {y + rh - 1.3:.2f} l0.7 -2.1 l-0.8 -1.5 l0.6 -1.4", stroke="#34404c", width=0.55, opacity=0.75)
                    if r.next() < 0.25:  # chipped corner
                        cx = bx0 if r.next() < 0.5 else bx1
                        sgn = 1 if cx == bx0 else -1
                        s.polygon([(cx, y + 1.2), (cx + sgn * 3.2, y + 1.2), (cx, y + 3.4)], fill="#28323e")
                    if r.next() < 0.18:
                        gx, gy = r.uniform(bx0 + 2, bx1 - 2), r.uniform(y + 3, y + rh - 3)
                        _glow(s, gx, gy, 3.2, GLOW_CYAN, 0.55)
                        s.circle(gx, gy, 0.7, fill="#e6fffa")
                x += 20
                i += 1
        # moss creeping over the top edge with a few short strands
        pts = [(x, 1.3 + 0.9 * math.sin(x * 0.35 + w)) for x in [i * w / 14 for i in range(15)]]
        lip = [(x, 3.6 + 1.2 * math.sin(x * 0.5 + h)) for x in reversed([i * w / 14 for i in range(15)])]
        s.path(smooth_open(pts) + f"L{lip[0][0]:.2f} {lip[0][1]:.2f}" + _curve(lip) + "Z", fill=s.linear(0, 0, 0, 5, [(0, "#9fe8ac"), (1, "#2f8266")]),
               opacity=0.95)
        for _ in range(max(2, int(w / 22))):
            mx = r.uniform(4, w - 4)
            ln = r.uniform(2.5, 6.5)
            s.path(f"M{mx - 1.2:.2f} 3.6 Q{mx:.2f} {3.6 + ln * 1.2:.2f} {mx + 1.2:.2f} 3.6 Z", fill="#2f8266")

    def platform(self, kind: str, w: float, h: float, style: str = "") -> Svg:
        if kind == "ledge":
            if "fungus" in style and h <= 40:
                return self._shelf_fungus(w, h)
            return self._root_shelf(w, h)
        s = Svg(w, h + 16)
        r = Rand(int(w * 3 + h * 7))
        if kind == "moving":
            self._leafy_branch(s, w, h, r)
        elif kind == "crumble":
            self._rotten_bark(s, w, h, r)
        elif kind == "semisolid":
            band = min(h, 8.0)
            for k, vx in enumerate((w * 0.18, w * 0.45, w * 0.7, w * 0.9)):
                ln = 8 + 6 * (k % 2)
                s.path(f"M{vx:.2f} {band - 1:.2f} q{1.5 - k:.2f} {ln * 0.5:.2f} {0.5 - k * 0.4:.2f} {ln:.2f}", stroke="#2a5a40", width=1.2)
            s.path(rounded_rect_path(0.6, 0.8, w - 1.2, band, band / 2), fill=s.linear(0, 0.8, 0, band, [(0, BARK_LIGHT), (1, BARK_DARK)]),
                   stroke=INK, width=1.1)
            for x in range(6, int(w) - 4, 14):
                s.path(_leaf(x, 1.6, 8, 2.2, -160 + (x % 3) * 14), fill="#4fae7c", stroke="#1f5a44", width=0.5)
        elif kind == "spring":
            s.rect(w / 2 - 3.5, h * 0.45, 7, h * 0.55, fill=s.linear(w / 2 - 3.5, 0, w / 2 + 3.5, 0, [(0, "#eef6f0"), (1, "#9ab8b0")]),
                   stroke=INK, width=1.0, rx=2.5)
            _glow(s, w / 2, h * 0.3, w * 0.7, "#ffb8ec", 0.4)
            s.path(blob(w / 2, h * 0.45, w / 2 - 0.5, h * 0.42, 0.04, seed=3, squash_top=1.25),
                   fill=s.radial(w * 0.4, h * 0.2, w * 0.75, [(0, CAP_PINK[0]), (0.55, CAP_PINK[1]), (1, CAP_PINK[2])]), stroke=INK, width=1.2)
            for k in range(4):
                s.circle(w * (0.25 + k * 0.17), h * (0.28 + 0.12 * (k % 2)), 2.2, fill="#ffffff", opacity=0.9)
        else:  # conveyor / switch fallbacks: a mossy log
            s.path(rounded_rect_path(0.6, 0.6, w - 1.2, h - 1.2, h / 2), fill=s.linear(0, 0, 0, h, [(0, BARK_LIGHT), (1, BARK_DARK)]),
                   stroke=INK, width=1.2)
            s.path(f"M{h / 2:.2f} 1.6 L{w - h / 2:.2f} 1.6", stroke="#5dc28c", width=2.2)
        return s

    def _leafy_branch(self, s: Svg, w: float, h: float, r: Rand) -> None:
        """Floating enchanted branch: bark log, moss and leaves, glowing seed pods below."""
        _haze(s, w / 2, h + 3, w * 0.42, 5, "#7af0d8", 0.3)
        for k, vx in enumerate((w * 0.24, w * 0.52, w * 0.8)):
            ln = 7 + 5 * ((k + 1) % 2)
            s.path(f"M{vx:.2f} {h - 3:.2f} q2 {ln * 0.5:.2f} {k - 1:.2f} {ln:.2f}", stroke="#24543e", width=1.1)
            _glow(s, vx + k - 1, h - 2 + ln, 4.6, GLOW_GOLD, 0.65)
            s.circle(vx + k - 1, h - 2 + ln, 1.4, fill="#fff6cc")
        top = 3.5
        s.path(rounded_rect_path(0.8, top, w - 1.6, h - top - 0.8, (h - top) / 2),
               fill=s.linear(0, top, 0, h, [(0, "#94705a"), (0.45, "#5e4436"), (1, "#352420")]), stroke=INK, width=1.2)
        for k in range(3):
            yy = top + 4 + k * (h - top - 7) / 2.5
            pts = [(x, yy + 0.8 * math.sin(x * 0.2 + k * 2)) for x in [6 + i * (w - 12) / 8 for i in range(9)]]
            s.path(smooth_open(pts), stroke="#2a1c18", width=0.8, opacity=0.6)
        for ex in (3.6, w - 3.6):
            s.ellipse(ex, (top + h) / 2, 2.6, (h - top) / 2 - 1.2, fill=s.radial(ex, (top + h) / 2, 4, [(0, "#f2dcb0"), (1, "#b08860")]),
                      stroke=INK, width=0.8)
            s.ellipse(ex, (top + h) / 2, 1.2, (h - top) / 4, fill=None, stroke="#9a7450", width=0.5)
        pts = [(x, top + 0.2 - 1.4 * abs(math.sin(x * 0.3))) for x in [3 + i * (w - 6) / 16 for i in range(17)]]
        lip = [(x, top + 2.6 + 1.2 * abs(math.sin(x * 0.45))) for x in reversed([3 + i * (w - 6) / 16 for i in range(17)])]
        s.path(smooth_open(pts) + f"L{lip[0][0]:.2f} {lip[0][1]:.2f}" + _curve(lip) + "Z", fill=s.linear(0, 1, 0, top + 4, [(0, "#a9f2b4"),
               (1, "#2f8266")]))
        s.path(smooth_open(pts), stroke="#e6ffea", width=0.9, opacity=0.8)
        for lx, ang in ((7, -150), (11, -125), (w * 0.5 - 4, -105), (w * 0.5 + 4, -75), (w - 11, -55), (w - 7, -30)):
            s.path(_leaf(lx + math.cos(math.radians(ang)) * 4, top + math.sin(math.radians(ang)) * 4, 10, 2.8, ang),
                   fill=s.linear(0, top - 8, 0, top + 2, [(0, "#8fe0a0"), (1, "#2f8266")]), stroke="#1a5046", width=0.6)

    def _rotten_bark(self, s: Svg, w: float, h: float, r: Rand) -> None:
        """Decaying bark slab: cracked, punky holes, fungus; crumbs falling below."""
        top = [(x, 0.8 + 0.6 * abs(math.sin(x * 0.27))) for x in [1 + i * (w - 2) / 14 for i in range(15)]]
        bottom = []
        for i in range(15):
            x = w - 1 - i * (w - 2) / 14
            bottom.append((x, h - 1.2 + (r.uniform(0.5, 3.2) if 0 < i < 14 else 0)))
        d = smooth_open(top, 0.6) + f"L{bottom[0][0]:.2f} {bottom[0][1]:.2f}" + "".join(f"L{x:.2f} {y:.2f}" for x, y in bottom[1:]) + "Z"
        s.path(d, fill=s.linear(0, 0, 0, h, [(0, "#a38a78"), (0.45, "#77604f"), (1, "#4a3832")]), stroke=INK, width=1.2)
        s.path(smooth_open(top, 0.6), stroke="#d2bca8", width=0.9, opacity=0.7)
        for k in range(int(w / 16)):
            x = 8 + k * 16 + r.uniform(-3, 3)
            s.line(x, 3, x + r.uniform(-1, 1), h - 3, "#5a463c", 0.8, 0.6)
        for _ in range(3):
            x = r.uniform(10, w - 10)
            s.path(f"M{x:.2f} 1 l{r.uniform(-2, 2):.2f} {h * 0.3:.2f} l{r.uniform(1, 3):.2f} {h * 0.2:.2f} l{r.uniform(-3, -1):.2f} {h * 0.3:.2f}",
                   stroke="#24161a", width=1.2)
        for _ in range(max(2, int(w / 30))):
            x, y = r.uniform(8, w - 8), r.uniform(5, h - 5)
            s.ellipse(x, y, r.uniform(1.6, 3.0), r.uniform(1.0, 1.8), fill="#2a1c1c", stroke="#b89a80", width=0.5)
        for _ in range(3):
            x, y = r.uniform(6, w - 6), r.uniform(3, h - 3)
            s.circle(x, y, r.uniform(1.2, 2.2), fill="#c8d0a8", opacity=0.55)
        for fx in (r.uniform(6, w * 0.4), r.uniform(w * 0.6, w - 6)):
            fy = h - 3
            s.path(f"M{fx - 4:.2f} {fy:.2f} Q{fx:.2f} {fy - 3.2:.2f} {fx + 4:.2f} {fy:.2f} Q{fx:.2f} {fy + 1.5:.2f} {fx - 4:.2f} {fy:.2f} Z",
                   fill=s.linear(0, fy - 3, 0, fy + 1, [(0, "#ffb870"), (1, "#c06a30")]), stroke=INK, width=0.5)
        for _ in range(5):
            x, y = r.uniform(6, w - 6), h + r.uniform(1.5, 9)
            sz = r.uniform(0.8, 1.8)
            s.polygon([(x - sz, y), (x, y - sz), (x + sz, y + sz * 0.3)], fill="#6a5244", opacity=0.85)

    def _root_shelf(self, w: float, h: float) -> Svg:
        """Ledge: a floating slab of mossy earth bound by roots, rootlets dangling below."""
        hr = self.terrain_headroom
        r = Rand(int(w * 7 + h * 3))
        drop = 16.0
        s = Svg(w, h + hr + drop)
        y0, bottom = hr, hr + h
        # rootlets dangling under the slab, glowing at the tips
        n = max(2, int(w / 24))
        for k in range(n):
            rx = (k + 0.5) * w / n + r.uniform(-4, 4)
            ln = r.uniform(5, drop - 2)
            pts = [(rx, bottom - 3), (rx + r.uniform(-2, 2), bottom + ln * 0.5), (rx + r.uniform(-3, 3), bottom + ln)]
            s.path(smooth_open(pts), stroke=ROOT, width=r.uniform(1.0, 1.8))
            if k % 2 == 0:
                _glow(s, pts[-1][0], pts[-1][1], 4, GLOW_CYAN, 0.55)
                s.circle(pts[-1][0], pts[-1][1], 0.9, fill="#e6fff8")
        d = (f"M6 {y0 + 4:.2f} L{w - 6:.2f} {y0 + 4:.2f} Q{w:.2f} {y0 + 4:.2f} {w - 0.6:.2f} {y0 + 11:.2f} "
             f"L{w - 2.5:.2f} {bottom - 5:.2f} Q{w - 5:.2f} {bottom:.2f} {w - 13:.2f} {bottom:.2f} L13 {bottom:.2f} "
             f"Q5 {bottom:.2f} 2.5 {bottom - 5:.2f} L0.6 {y0 + 11:.2f} Q0 {y0 + 4:.2f} 6 {y0 + 4:.2f} Z")
        s.path(d, fill=s.linear(0, y0, 0, bottom, [(0, SOIL_TOP), (0.45, SOIL), (1, SOIL_DEEP)]), stroke=INK, width=1.2)
        # roots wrapping around the slab
        fill = s.linear(0, y0, 0, bottom, [(0, ROOT_LIGHT), (1, ROOT)])
        for k in range(3):
            x1 = w * (0.2 + 0.3 * k) + r.uniform(-6, 6)
            x2 = min(max(x1 + r.uniform(-18, 18), 8), w - 8)
            s.path(_taper([(x1, y0 + 7, 3.4), ((x1 + x2) / 2, (y0 + bottom) / 2 + 2, 2.6), (x2, bottom + 0.5, 1.4)]), fill=fill,
                   stroke=ROOT_DARK, width=0.6)
        for _ in range(max(1, int(w / 40))):
            pr = r.uniform(2.2, 4.0)
            px, py = r.uniform(pr * 1.5 + 4, w - pr * 1.5 - 4), r.uniform(y0 + 12, max(y0 + 13, bottom - 5))
            s.path(blob(px, py, pr * 1.35, pr, 0.12, seed=px), fill=s.radial(px - pr * 0.4, py - pr * 0.5, pr * 1.7,
                   [(0, STONE_LIGHT), (0.55, STONE), (1, STONE_DARK)]), opacity=0.9)
        if h > 30:
            _brackets(s, w - 1, y0 + h * 0.55, 6.5, -1, halo=0.45)
        self._moss_cap(s, w, 0.0, y0, True, True, r, MOSS["normal"])
        return s

    def _shelf_fungus(self, w: float, h: float) -> Svg:
        """Ledge (style 'fungus'): a stack of flat bracket fungi with a glowing underside."""
        hr = self.terrain_headroom
        s = Svg(w, h + hr + 8)
        y0 = hr
        _haze(s, w / 2, y0 + h + 2, w * 0.36, 4, GLOW_GOLD, 0.5)
        for inset, top, depth in ((w * 0.22, y0 + h * 0.62, h * 0.55), (w * 0.08, y0 + h * 0.3, h * 0.5), (0.0, y0, h * 0.62)):
            x1, x2 = 1 + inset, w - 1 - inset
            yb = top + depth
            s.path(f"M{x1:.2f} {top + 1.5:.2f} Q{(x1 + x2) / 2:.2f} {top - 2.2:.2f} {x2:.2f} {top + 1.5:.2f} "
                   f"Q{x2 + 0.5:.2f} {yb - depth * 0.15:.2f} {x2 - depth * 0.8:.2f} {yb:.2f} L{x1 + depth * 0.8:.2f} {yb:.2f} "
                   f"Q{x1 - 0.5:.2f} {yb - depth * 0.15:.2f} {x1:.2f} {top + 1.5:.2f} Z",
                   fill=s.linear(0, top - 2, 0, yb, [(0, "#d8a868"), (0.45, "#9a6438"), (1, "#5a3420")]), stroke=INK, width=1.1)
            for j in range(1, 3):
                yy = top + depth * j / 3
                s.path(f"M{x1 + 2 + j:.2f} {yy:.2f} Q{(x1 + x2) / 2:.2f} {yy + 1.6:.2f} {x2 - 2 - j:.2f} {yy:.2f}",
                       stroke="#f2d2a0" if j == 1 else "#6a3a20", width=1.0, opacity=0.7)
            s.path(f"M{x1 + depth * 0.8:.2f} {yb - 0.6:.2f} L{x2 - depth * 0.8:.2f} {yb - 0.6:.2f}", stroke="#fff0c0", width=1.2, opacity=0.85)
            s.path(f"M{x1 + 2:.2f} {top + 0.8:.2f} Q{(x1 + x2) / 2:.2f} {top - 2.6:.2f} {x2 - 2:.2f} {top + 0.8:.2f}", stroke="#fffaf0",
                   width=1.0, opacity=0.85)
        s.path(blob(w * 0.3, y0 - 0.5, min(10, w * 0.12), 1.8, 0.3, seed=w), fill="#5dc28c")
        return s

    def pipe(self, w: float, h: float, warp: bool) -> Svg:
        """Hollow log standing upright (a mossy trunk section with a dark hollow)."""
        s = Svg(w, h)
        body = s.linear(4, 0, w - 4, 0, [(0, "#24181a"), (0.2, "#5e4232"), (0.45, "#7e5a42"), (0.62, "#5a3e2e"), (0.86, "#3a2820"),
                                         (1, "#1c1214")])
        s.path(rounded_rect_path(4, 10, w - 8, h - 10, 2), fill=body, stroke=INK, width=1.3)
        for k in range(5):
            gx = 9 + k * (w - 18) / 4
            pts = [(gx + 1.2 * math.sin(y * 0.3 + k), y) for y in [14 + i * (h - 16) / 4 for i in range(5)]]
            s.path(smooth_open(pts), stroke="#1e1214", width=1.0, opacity=0.6)
        s.path(f"M{w - 6.5:.2f} 14 L{w - 6.5:.2f} {h - 2:.2f}", stroke="#c89a78", width=1.0, opacity=0.4)
        s.path(blob(9, h * 0.62, 5, min(10.0, h * 0.24), 0.3, seed=w + h), fill="#2f8266", opacity=0.95)
        s.path(blob(8, h * 0.62 - min(8.0, h * 0.2), 4, 2, 0.3, seed=h), fill="#5dc28c")
        # collar with the cut face and the hollow
        collar = s.linear(0, 0, w, 0, [(0, "#2c1e1c"), (0.25, "#6e4e3a"), (0.5, "#8a6a50"), (0.8, "#4a3426"), (1, "#24181a")])
        s.path(rounded_rect_path(0.8, 3.4, w - 1.6, 11, 4), fill=collar, stroke=INK, width=1.3)
        s.ellipse(w / 2, 4.4, w / 2 - 1.2, 3.8, fill=s.linear(0, 0.6, 0, 8, [(0, "#f4e0b8"), (1, "#b48e62")]), stroke=INK, width=1.1)
        s.ellipse(w / 2, 4.5, w / 2 - 4.2, 2.8, fill=None, stroke="#a07a50", width=0.6)
        if warp:
            _haze(s, w / 2, 4.5, w / 2 - 6, 2.6, GLOW_CYAN, 0.95)
        s.ellipse(w / 2, 4.6, w / 2 - 8, 2.1, fill="#0c0809" if not warp else "#163a3a")
        # moss draping over the collar
        s.path(blob(w * 0.3, 3.6, w * 0.16, 1.8, 0.3, seed=w), fill="#5dc28c")
        s.path(f"M{w * 0.22:.2f} 4.5 q0.6 4 -0.4 7 M{w * 0.32:.2f} 4.6 q0.5 3 -0.2 5", stroke="#2f8266", width=1.1)
        _mushroom(s, w - 9, h - 1, min(7.0, h * 0.2), 2.6, CAP_CYAN, 0.6, halo=0.5, outline=INK, spots=2)
        if warp:  # carved arrow rune: the secret is down this log
            cy = 26 if h > 34 else h * 0.66
            _glow(s, w / 2, cy, 11, GLOW_CYAN, 0.75)
            s.circle(w / 2, cy, 6.4, fill=None, stroke="#bffbf2", width=0.9, opacity=0.85)
            s.polygon([(w / 2 - 4.2, cy - 2.6), (w / 2 + 4.2, cy - 2.6), (w / 2, cy + 3.4)], fill="#effffb")
        return s

    def hazard(self, kind: str, w: float, h: float):
        if kind != "thorns":
            return None
        hh = max(h, 16.0)
        s = Svg(w, hh + 4)
        for k in range(3):
            pts = [(lx, hh * (0.45 + 0.18 * k) + 3 * math.sin(lx * 0.12 + k * 2)) for lx in [i * w / 12 for i in range(13)]]
            s.path(smooth_open(pts), stroke=["#1c2a2c", "#2a3e3a", "#3c5a4c"][k], width=3.4 - k * 0.6)
            for i, (lx, ly) in enumerate(pts[:-1]):
                if (i + k) % 2 == 0:
                    s.polygon([(lx - 1.8, ly), (lx + 0.4, ly - 6), (lx + 1.8, ly)], fill="#d8c8f0", stroke=INK, width=0.5)
        return s

    # ------------------------------------------------------------------ props
    def _giant_mushroom(self, seed: int) -> Svg:
        """Towering mushroom kept in a dark, low-contrast key (scenery, never a platform):
        the light comes from its gills and spots rather than from the cap surface."""
        r = Rand(seed)
        s = Svg(150, 150)
        cx, base = 75.0, 148.0
        _glow(s, cx, 70, 70, GLOW_CYAN, 0.28)
        stem = s.linear(cx - 12, 0, cx + 12, 0, [(0, "#8eaaa8"), (0.55, "#5e7a7a"), (1, "#334a4e")])
        s.path(f"M{cx - 11} {base} Q{cx - 8} 110 {cx - 6} 72 L{cx + 8} 72 Q{cx + 10} 112 {cx + 13} {base} Z", fill=stem, stroke="#0e2228",
               width=1.2)
        s.path(f"M{cx - 11} 104 Q{cx} 111 {cx + 11} 104 L{cx + 14} 111 Q{cx} 120 {cx - 14} 111 Z", fill="#7c9896", stroke="#0e2228", width=0.9)
        s.path(f"M{cx - 46} 74 C{cx - 51} 37 {cx - 22} 17 {cx} 17 C{cx + 22} 17 {cx + 51} 37 {cx + 46} 74 Q{cx} 64 {cx - 46} 74 Z",
               fill=s.radial(cx + 8, 68, 60, [(0, "#2f9a9e"), (0.55, "#16525e"), (1, "#0c2c38")]), stroke="#0a1e26", width=1.3)
        s.path(f"M{cx - 42} 72 Q{cx} 62 {cx + 42} 72 Q{cx} 78 {cx - 42} 72 Z", fill="#b4fff2", opacity=0.9)
        for k in range(9):
            gx = cx - 36 + k * 9
            s.line(gx, 70.5 - abs(k - 4) * 0.5, cx + (gx - cx) * 0.25, 76, "#5fd6cc", 0.7, 0.8)
        for u, v, rad in ((-26, 46, 4.4), (-7, 32, 3.8), (14, 37, 4.6), (29, 55, 3.2), (-34, 62, 2.6), (2, 54, 2.6), (20, 64, 2.2)):
            _glow(s, cx + u, v, rad * 2.8, GLOW_CYAN, 0.45)
            s.circle(cx + u, v, rad, fill="#dffff8", opacity=0.92)
        s.path(f"M{cx + 8} 22 Q{cx + 30} 28 {cx + 41} 48", stroke="#8fd2d0", width=1.5, opacity=0.5)
        for dx, hgt, pal in ((-26, 22, CAP_CYAN), (-36, 13, CAP_VIOLET), (24, 16, CAP_CYAN)):
            _mushroom(s, cx + dx, base, hgt, hgt * 0.45, pal, r.uniform(-2, 2), halo=0.4, stem="#a9c2bd")
        s.path(blob(cx, base - 1, 34, 4, 0.25, seed=seed), fill="#2f7a5e")
        return s

    def _mushroom_trio(self, seed: int) -> Svg:
        r = Rand(seed)
        s = Svg(140, 120)
        for dx, hgt, cap, pal in ((-22, 58, 22, CAP_VIOLET_DIM), (14, 40, 17, CAP_PINK_DIM), (34, 24, 11, CAP_VIOLET_DIM), (-42, 18, 8, CAP_CYAN)):
            _mushroom(s, 70 + dx, 118, hgt, cap, pal, r.uniform(-5, 5), halo=0.3, spots=4, stem="#8ea4a2", outline="#1a1830")
        s.path(blob(70, 117, 46, 4, 0.25, seed=seed), fill="#2f7a5e")
        return s

    def _glow_flowers(self, seed: int) -> Svg:
        r = Rand(seed)
        s = Svg(72, 54)
        for k in range(5):
            lx = 14 + k * 11 + r.uniform(-3, 3)
            s.path(_leaf(lx, 47, 16, 3.4, -90 + (k - 2) * 24), fill="#2f7a5a", stroke="#1a4a3c", width=0.6)
        for k in range(5):
            x = r.uniform(10, 62)
            top = r.uniform(10, 28)
            bend = r.uniform(4, 9) * (1 if x < 36 else -1)
            s.path(f"M{x:.1f} 54 Q{x - bend * 0.3:.1f} {top + 6:.1f} {x + bend:.1f} {top:.1f}", stroke="#3a8a5e", width=1.2)
            bx, by = x + bend, top + 1
            color = r.choice([GLOW_GOLD, "#ffc4ec", "#c8f4ff", GLOW_GOLD])
            _glow(s, bx, by + 5, 13, color, 0.55)
            s.path(f"M{bx - 4:.2f} {by:.2f} Q{bx:.2f} {by - 3.4:.2f} {bx + 4:.2f} {by:.2f} L{bx + 5:.2f} {by + 7:.2f} "
                   f"Q{bx + 2.5:.2f} {by + 5.6:.2f} {bx:.2f} {by + 7.6:.2f} Q{bx - 2.5:.2f} {by + 5.6:.2f} {bx - 5:.2f} {by + 7:.2f} Z",
                   fill=s.linear(0, by - 3, 0, by + 8, [(0, "#ffffff"), (0.6, color), (1, shade(color, -0.25))]), stroke=shade(color, -0.55),
                   width=0.6)
            s.circle(bx, by + 8.6, 1.0, fill="#ffffff")
        return s

    def _fern(self, seed: int) -> Svg:
        r = Rand(seed)
        s = Svg(104, 66)
        bx, by = 52.0, 65.0
        leaflet = s.linear(0, 6, 0, 66, [(0, "#86e0aa"), (0.5, "#3f9a72"), (1, "#1f5a46")])
        for k in sorted(range(9), key=lambda k: -abs(k - 4)):  # outer fronds first, the upright ones on top
            a = math.radians(-90 + (k - 4) * 19 + r.uniform(-4, 4))
            ln = r.uniform(42, 54) * (1 - abs(k - 4) * 0.08)
            ex, ey = bx + math.cos(a) * ln, by + math.sin(a) * ln * 0.95 + abs(k - 4) * 4.5
            c = (bx + math.cos(a) * ln * 0.5 + math.cos(a - 1.4 * (1 if k > 4 else -1)) * 7, by + math.sin(a) * ln * 0.6 - 6)
            s.path(f"M{bx:.2f} {by:.2f} Q{c[0]:.2f} {c[1]:.2f} {ex:.2f} {ey:.2f}", stroke="#1f4e3c", width=1.6)
            for j in range(1, 10):
                t = j / 10
                px = (1 - t) ** 2 * bx + 2 * (1 - t) * t * c[0] + t * t * ex
                py = (1 - t) ** 2 * by + 2 * (1 - t) * t * c[1] + t * t * ey
                dx, dy = 2 * (1 - t) * (c[0] - bx) + 2 * t * (ex - c[0]), 2 * (1 - t) * (c[1] - by) + 2 * t * (ey - c[1])
                ang = math.degrees(math.atan2(dy, dx))
                size = 11.5 * (1 - t * 0.62)
                for side in (-1, 1):
                    s.path(_leaf(px + math.cos(math.radians(ang + side * 64)) * size * 0.45,
                                 py + math.sin(math.radians(ang + side * 64)) * size * 0.45, size, size * 0.3, ang + side * 64),
                           fill=leaflet, stroke="#173f32", width=0.4)
        s.path(f"M{bx + 3} {by} Q{bx + 8} {by - 22} {bx + 14} {by - 26} q4 -2 3 2 q-1 3 -4 1", stroke="#4fae7c", width=1.6)
        return s

    def _root_tangle(self, seed: int) -> Svg:
        """Thin gnarled roots looping out of the ground (too thin to read as a ledge)."""
        r = Rand(seed)
        s = Svg(150, 50)
        fill = s.linear(0, 10, 0, 50, [(0, "#7a5a46"), (0.5, "#4e382e"), (1, "#2a1e1c")])
        for k in range(4):
            x1 = 14 + k * 22 + r.uniform(-6, 6)
            span = r.uniform(34, 62)
            peak = r.uniform(14, 34)
            thick = r.uniform(3.0, 5.2)
            pts = [(x1 + span * t, 49 - peak * math.sin(math.pi * t) + 3 * math.sin(t * 9 + k), thick * (0.55 + 0.45 * math.sin(math.pi * t)) + 0.6)
                   for t in [j / 8 for j in range(9)]]
            s.path(_taper(pts), fill=fill, stroke="#16100f", width=0.8)
            s.path(smooth_open([(x, y - t * 0.35) for x, y, t in pts[2:7]]), stroke="#b08a6a", width=0.8, opacity=0.5)
            mx, my, _t = pts[4]
            s.path(blob(mx, my - 2.2, 6, 1.8, 0.3, seed=mx), fill="#3f9a72")
        _mushroom(s, 104, 49, 8, 3.6, CAP_CYAN, -1, halo=0.5, spots=2)
        _mushroom(s, 110, 49, 5, 2.6, CAP_CYAN, 1, halo=0.5, spots=2)
        return s

    def _runestone(self, seed: int) -> Svg:
        r = Rand(seed)
        s = Svg(60, 86)
        cx = 30.0
        s.path(f"M{cx - 18} 84 L{cx - 20} 30 Q{cx - 18} 6 {cx + 2} 4 Q{cx + 20} 6 {cx + 19} 34 L{cx + 17} 84 Z",
               fill=s.linear(cx - 20, 0, cx + 20, 0, [(0, "#3e4e5a"), (0.6, "#6a8090"), (1, "#8aa2ae")]), stroke=INK, width=1.4)
        for _ in range(4):
            px, py = r.uniform(cx - 14, cx + 14), r.uniform(20, 76)
            s.circle(px, py, r.uniform(1.5, 3), fill="#a8b8a0", opacity=0.45)
        _glow(s, cx, 46, 26, GLOW_TEAL, 0.5)
        s.path(_leaf(cx, 46, 22, 6.2, -90), fill=None, stroke="#c8fff4", width=1.8)
        s.path(f"M{cx} 58 L{cx} 35 M{cx} 50 l-5 -5 M{cx} 50 l5 -5 M{cx} 43 l-4 -4 M{cx} 43 l4 -4", stroke="#c8fff4", width=1.1)
        s.circle(cx, 64, 2.2, fill="#c8fff4")
        s.path(f"M{cx - 19} 18 Q{cx - 6} 2 {cx + 12} 6 Q{cx + 4} 12 {cx - 6} 12 Q{cx - 14} 16 {cx - 19} 24 Z",
               fill=s.linear(0, 2, 0, 24, [(0, "#a9f2b4"), (1, "#2f8266")]))
        for x in (cx - 15, cx - 9, cx - 2):
            s.path(f"M{x - 1} 14 Q{x} {14 + r.uniform(4, 9):.1f} {x + 1} 13 Z", fill="#2f8266")
        _mushroom(s, cx + 15, 84, 8, 3.6, CAP_CYAN, 1, halo=0.5, spots=2)
        return s

    def _lantern_plant(self, seed: int) -> Svg:
        r = Rand(seed)
        s = Svg(76, 100)
        for k in range(4):
            s.path(_leaf(26 + k * 8, 92, 22, 4.5, -90 + (k - 1.5) * 30), fill="#2f7a5a", stroke="#1a4a3c", width=0.6)
        s.path("M34 98 Q30 40 46 16 Q58 4 66 18", stroke="#2a5a44", width=2.6)
        s.path("M34 98 Q30 40 46 16 Q58 4 66 18", stroke="#4fae7c", width=1.0, opacity=0.7)
        for k, (x, y) in enumerate(((66, 18), (40, 30), (35, 52))):
            ln = 8 + k * 2 + r.uniform(0, 3)
            s.line(x, y, x + 1, y + ln, "#2a5a44", 1.0)
            by = y + ln + 6
            _glow(s, x + 1, by, 16, GLOW_GOLD, 0.6)
            s.path(blob(x + 1, by, 5, 6.5, 0.06, seed=k), fill=s.radial(x - 0.5, by - 2, 8, [(0, "#ffffff"), (0.35, "#ffe9a0"), (1, "#e09036")]),
                   stroke="#6a3a10", width=0.7)
            s.path(f"M{x - 3:.1f} {by - 4.6:.1f} Q{x + 1:.1f} {by - 8:.1f} {x + 5:.1f} {by - 4.6:.1f}", stroke="#2a5a44", width=1.6)
        return s

    def _ruin_pillar(self, seed: int) -> Svg:
        s = Svg(70, 144)
        cx = 35.0
        stone = s.linear(cx - 16, 0, cx + 16, 0, [(0, "#2c3a46"), (0.55, "#5c7280"), (1, "#3e505c")])
        s.path(f"M{cx - 15} 132 L{cx - 15} 34 L{cx - 9} 26 L{cx - 2} 32 L{cx + 5} 20 L{cx + 15} 28 L{cx + 15} 132 Z", fill=stone, stroke=INK,
               width=1.4)
        for fx in (-8, 0, 8):
            s.line(cx + fx, 36, cx + fx, 128, "#2e3a46", 1.2, 0.6)
        s.path(rounded_rect_path(cx - 21, 126, 42, 14, 2), fill=s.linear(0, 126, 0, 140, [(0, "#6a808a"), (1, "#36444f")]), stroke=INK, width=1.2)
        _glow(s, cx, 78, 20, GLOW_TEAL, 0.45)
        s.rect(cx - 15, 74, 30, 7, fill="#1c3038")
        for k in range(4):
            s.path(_leaf(cx - 9 + k * 6, 77.5, 5, 1.4, -60), fill="#b4fff0")
        vine = [(cx - 15, 120), (cx + 10, 108), (cx + 15, 96), (cx - 10, 84), (cx - 15, 70), (cx + 8, 56), (cx + 12, 44)]
        s.path(smooth_open(vine), stroke="#245a44", width=1.6)
        for i, (vx, vy) in enumerate(vine[1:]):
            s.path(_leaf(vx, vy - 2, 8, 2.4, -30 + (i % 2) * -120), fill="#3f9a72", stroke="#1a4a3c", width=0.5)
        s.path(blob(cx - 2, 27, 15, 4, 0.3, seed=seed), fill=s.linear(0, 22, 0, 32, [(0, "#a9f2b4"), (1, "#2f8266")]))
        s.path(blob(cx + 22, 138, 9, 5, 0.2, seed=seed + 1), fill="#56697a", stroke=INK, width=1.0)
        return s

    def _stump(self, seed: int) -> Svg:
        """Low, broken mossy stump (jagged top, so it never reads as a flat ledge)."""
        s = Svg(100, 56)
        cx = 50.0
        s.path(f"M{cx - 40} 54 Q{cx - 28} 50 {cx - 26} 40 L{cx - 24} 22 L{cx - 14} 28 L{cx - 6} 14 L{cx + 4} 24 L{cx + 12} 18 L{cx + 24} 26 "
               f"L{cx + 26} 40 Q{cx + 30} 50 {cx + 42} 54 Z",
               fill=s.linear(cx - 30, 0, cx + 30, 0, [(0, "#1e1616"), (0.45, "#4a3830"), (0.78, "#5e4a3c"), (1, "#2a1e1c")]), stroke="#120c0e",
               width=1.2)
        for fx in (-16, -6, 6, 16):
            s.path(smooth_open([(cx + fx, 28), (cx + fx + 1.5, 40), (cx + fx * 1.2, 52)]), stroke="#140e0e", width=1.0, opacity=0.6)
        s.path(blob(cx - 14, 30, 13, 4, 0.3, seed=seed), fill=s.linear(0, 26, 0, 34, [(0, "#6fc48e"), (1, "#245e4a")]))
        _brackets(s, cx + 24, 38, 9, 1, halo=0.4)
        _mushroom(s, cx - 34, 54, 9, 4, CAP_VIOLET, -1, halo=0.5, spots=2, stem="#a9c2bd")
        return s

    def _lantern_tree(self, seed: int) -> Svg:
        r = Rand(seed)
        s = Svg(190, 236)
        cx, base = 95.0, 232.0
        bark = s.linear(cx - 30, 0, cx + 30, 0, [(0, "#14242e"), (0.45, "#2c4652"), (0.78, "#4a6e76"), (1, "#1c2e38")])
        s.path(f"M{cx - 34} {base} Q{cx - 16} {base - 10} {cx - 14} {base - 40} Q{cx - 20} {base - 90} {cx - 6} 110 Q{cx - 30} 92 {cx - 52} 86 "
               f"Q{cx - 26} 80 {cx - 2} 98 Q{cx + 4} 80 {cx + 30} 70 Q{cx + 12} 92 {cx + 10} 116 Q{cx + 22} {base - 80} {cx + 14} {base - 40} "
               f"Q{cx + 16} {base - 10} {cx + 36} {base} Z", fill=bark, stroke=INK, width=1.5)
        for fx in (-6, 2, 9):
            s.path(smooth_open([(cx + fx - 4, base - 6), (cx + fx * 0.6 - 2, base - 60), (cx + fx, 116)]), stroke="#0c161c", width=1.2, opacity=0.6)
        clumps = [(cx, 64, 48), (cx - 48, 86, 32), (cx + 50, 82, 34), (cx - 22, 36, 32), (cx + 28, 40, 30)]
        for x, y, rad in clumps:
            s.path(blob(x, y + 6, rad, rad * 0.8, 0.16, seed=x + seed), fill="#0a1a20")
        for x, y, rad in clumps:
            for j in range(8):  # leaf fringe along the lower edge
                a = math.radians(14 + j * 21)
                s.path(_leaf(x + math.cos(a) * rad * 0.95, y + math.sin(a) * rad * 0.78 + 2, 12, 3.2, math.degrees(a)), fill="#12302f")
            s.path(blob(x, y, rad, rad * 0.8, 0.16, seed=x + seed), fill=s.radial(x + rad * 0.35, y - rad * 0.5, rad * 1.6,
                   [(0, "#3a786e"), (0.5, "#1c4846"), (1, "#0e282c")]))
            for j in range(5):  # moonlit leaves on the upper right of each clump
                a = math.radians(-112 + j * 26)
                s.path(_leaf(x + math.cos(a) * rad * 0.82, y + math.sin(a) * rad * 0.64, 11, 3, math.degrees(a)), fill="#2f6a62",
                       stroke="#7cc4b0", width=0.7)
            for _ in range(3):
                lx, ly = x + r.uniform(-rad * 0.5, rad * 0.5), y + r.uniform(-rad * 0.3, rad * 0.4)
                s.path(_leaf(lx, ly, 9, 2.6, r.uniform(-160, -20)), fill="#245650", opacity=0.9)
        for _ in range(7):
            x, y = r.uniform(cx - 70, cx + 70), r.uniform(70, 116)
            ln = r.uniform(6, 16)
            s.line(x, y, x, y + ln, "#16302c", 0.9)
            _glow(s, x, y + ln + 4, 12, GLOW_GOLD, 0.55)
            s.path(blob(x, y + ln + 4, 3.4, 4.4, 0.05, seed=x), fill=s.radial(x - 1, y + ln + 2.5, 5.5, [(0, "#ffffff"), (0.4, "#ffe9a0"),
                   (1, "#e09036")]), stroke="#6a3a10", width=0.6)
        s.path(blob(cx, base - 2, 40, 5, 0.25, seed=seed), fill="#3f9a72")
        _mushroom(s, cx - 30, base, 10, 4.4, CAP_CYAN, -1, halo=0.5, spots=2)
        return s

    def _bush(self, seed: int) -> Svg:
        """Leafy forest bush (the Arbusto-Espreita hides among these)."""
        r = Rand(seed)
        s = Svg(100, 60)
        for cx, cy, rad in ((30, 38, 22), (52, 30, 26), (72, 38, 20)):
            s.path(blob(cx, cy, rad, rad * 0.82, 0.1, seed=cx + seed), fill=s.radial(cx + rad * 0.3, cy - rad * 0.6, rad * 1.6,
                   [(0, "#4fae7c"), (0.55, "#2a7458"), (1, "#16443a")]), stroke="#0c2a26", width=1.1)
        for _ in range(16):
            x, y = r.uniform(14, 86), r.uniform(12, 46)
            s.path(_leaf(x, y, 8, 2.4, r.uniform(-160, -20)), fill=r.choice(["#5cc08a", "#3f9a72", "#2f8266"]), stroke="#164a3a", width=0.4)
        s.path("M34 14 Q52 4 70 14", stroke="#a9f2b4", width=1.2, opacity=0.45)
        for _ in range(3):
            x, y = r.uniform(20, 80), r.uniform(18, 40)
            _glow(s, x, y, 5, GLOW_GOLD, 0.5)
            s.circle(x, y, 1.3, fill="#fff2b0")
        return s

    def props(self) -> dict[str, PropSpec]:
        return {
            "tree_mushroom": PropSpec(lambda: self._giant_mushroom(3), (75, 148)),
            "mushroom_trio": PropSpec(lambda: self._mushroom_trio(5), (70, 118)),
            "glow_flowers": PropSpec(lambda: self._glow_flowers(4), (36, 54)),
            "glow_flowers_b": PropSpec(lambda: self._glow_flowers(19), (36, 54)),
            "fern": PropSpec(lambda: self._fern(7), (52, 65)),
            "fern_b": PropSpec(lambda: self._fern(23), (52, 65)),
            "roots": PropSpec(lambda: self._root_tangle(2), (75, 49)),
            "runestone": PropSpec(lambda: self._runestone(6), (30, 84)),
            "lantern_plant": PropSpec(lambda: self._lantern_plant(8), (34, 98)),
            "ruin_pillar": PropSpec(lambda: self._ruin_pillar(9), (35, 140)),
            "stump": PropSpec(lambda: self._stump(10), (50, 54)),
            "tree_lantern": PropSpec(lambda: self._lantern_tree(12), (95, 232)),
            "bush": PropSpec(lambda: self._bush(5), (50, 58)),
            "bush_b": PropSpec(lambda: self._bush(14), (50, 58)),
        }

    def auto_decor(self, rng, surface_w: float):
        out = []
        x = rng.uniform(30, 110)
        while x < surface_w - 30:
            roll = rng.next()
            if roll < 0.2:
                out.append((rng.choice(["glow_flowers", "glow_flowers_b"]), x, rng.uniform(0.8, 1.05), "mid"))
            elif roll < 0.33:
                out.append((rng.choice(["fern", "fern_b"]), x, rng.uniform(0.6, 0.9), "mid"))
            elif roll < 0.43:
                out.append((rng.choice(["bush", "bush_b"]), x, rng.uniform(0.7, 0.95), "back"))
            elif roll < 0.53:
                out.append(("mushroom_trio", x, rng.uniform(0.75, 1.0), "back"))
            elif roll < 0.61 and surface_w > 240:
                out.append(("tree_mushroom", x, rng.uniform(0.6, 0.8), "back"))
            elif roll < 0.67:
                out.append(("runestone", x, rng.uniform(0.75, 0.95), "back"))
            elif roll < 0.73:
                out.append(("lantern_plant", x, rng.uniform(0.75, 1.0), "back"))
            elif roll < 0.79:
                out.append(("roots", x, rng.uniform(0.7, 0.95), "back"))
            elif roll < 0.83:
                out.append(("stump", x, rng.uniform(0.6, 0.8), "back"))
            elif roll < 0.89:
                out.append(("ruin_pillar", x, rng.uniform(0.6, 0.8), "back"))
            elif roll < 0.95 and surface_w > 300:
                out.append(("tree_lantern", x, rng.uniform(0.8, 1.0), "back"))
            x += rng.uniform(100, 210)
        return out

    def weather(self) -> Weather:
        # ``colors`` name particle sprites: two thirds drifting spores, one third fireflies.
        return Weather("spores", 0.55, ("ef_spore", "ef_firefly", "ef_spore"), wind=6.0)


ART_CLASS = EnchantedForest
