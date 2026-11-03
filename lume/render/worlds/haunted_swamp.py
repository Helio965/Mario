"""Pântano Assombrado: a misty bayou at night under a big moon.

Identity: a deep indigo-to-teal night with a large pale moon (corona ring,
thin silver-lined clouds crossing it) whose glitter path lies fixed on the
still water of the sky; a leaning manor and the far lantern keep on misty
hills with dead trees and drifting will-o'-wisps; bald cypresses with
flared trunks, knees and curtains of Spanish moss standing in the water
(mirrored in it); reeds, cattails and crooked lantern posts in front.

The ground is a dark peat-mud bank: wavy mud strata with stones, twisted
roots and specks of foxfire under an olive moss carpet whose hanging lip is
wet mud with root loops; sedge tufts and bell-capped glowing mushrooms grow
on top. Slippery floors (``surface == "ice"``) are slick wet moss (glossy
teal, specular rim, water beads); "sticky" floors are thick muck. The
fortress style is the mossy old stone of the lantern keep.

Light and readability: the moon is the cool key light (rims are slate and
lilac), foxfire and fireflies are yellow-green, and lantern amber is the only
warm light — it always marks something safe or rewarding (reward lantern
boxes, lantern posts, the keep crest). The parallax layers stay in a dark,
narrow value band with a lilac mist behind the play band so dark-outlined
characters stand out. Patterns that cross terrain chunk borders (moss lip,
mud lip, root loops, strata, roots, coping stones) are functions of the world
x, and only hanging edges are outlined, so chunks join seamlessly.

All motifs are original (crescent-and-flame lantern rune, abstract
portraits, damask of moths and leaves); no crosses on the stones.
"""

from __future__ import annotations

import math
from functools import partial
from typing import Optional, Sequence

from ..svg import Rand, Svg, blob, mix, rounded_rect_path, shade, smooth_closed, smooth_open, star_points
from .base import Layer, PropSpec, Weather, WorldArt

Pt = tuple[float, float]

INK = "#1a1526"
# peat-mud body: highlight → deep
PEAT_HI, PEAT_TOP, PEAT, PEAT_DARK, PEAT_DEEP = "#6e5a48", "#4a3c30", "#32281f", "#1c1611", "#0b0806"
MUD_WET, MUD_SHINE = "#231b15", "#9c8c7a"
STONE_HI, STONE, STONE_DARK = "#a6ae9e", "#67715f", "#2f3630"
ROOT_HI, ROOT, ROOT_DARK = "#9c7e60", "#5e4733", "#251b14"
WOOD_HI, WOOD, WOOD_DARK = "#a3866a", "#6a5140", "#382a22"
PLANK_HI, PLANK, PLANK_DARK = "#b4a284", "#7c6a54", "#463b30"  # weathered grey-brown boards
IRON_HI, IRON, IRON_DARK, IRON_DEEP = "#9399a8", "#5a5f6e", "#33363f", "#1a1c22"
RUST, RUST_HI, RUST_DARK = "#8a4c30", "#c27646", "#4a2618"
KEEP_HI, KEEP, KEEP_DARK, KEEP_DEEP = "#909a8c", "#5e695c", "#363f37", "#1b201c"  # lantern-keep stone (old, mossy)
# moss carpets: top, body, dark, deep, moonlit rim
MOSS = {
    "normal": ("#a9bd84", "#6e8a4e", "#45603a", "#24341e", "#d6e4b6"),
    "ice": ("#e2fff4", "#78c4ac", "#357a6c", "#173f3a", "#ffffff"),  # slick wet moss
    "sticky": ("#a3986a", "#6e6440", "#4a4028", "#2a2418", "#cfc59c"),  # thick muck
}
FOLIAGE = ("#4a6e60", "#2a463f", "#17282a")  # cypress needles: lit, body, shadow
SPANISH_MOSS = ("#8d9b8c", "#c3ccb8")
# light
GLOW, GLOW_HOT, GLOW_DEEP = "#ffcf6e", "#fff4d2", "#e8902e"  # lantern amber: the only warm light (safe)
FIRE, FIRE_HOT, FIRE_DEEP = "#d4f26c", "#f6ffd8", "#7aa82e"  # fireflies and foxfire
WISP, WISP_HOT = "#86f0de", "#eafffb"  # will-o'-wisps
GREEN_FLAME = [(0, "#f2ffe6"), (0.35, "#b4ffb0"), (0.7, "#3fd47c"), (1, "#137a4c")]
MIST = "#b7a9d6"  # lilac mist
SLATE = "#7d8fb0"  # moonlit rim light
MOON, MOON_SHADE = "#f8f4e0", "#d0cec4"
MOON_X, MOON_Y, MOON_R = 668.0, 150.0, 64.0
HORIZON = 332.0  # sky y of the far shore; below it the sky is still water


# --------------------------------------------------------------------------- helpers
def _fract(v: float) -> float:
    return v - math.floor(v)


def _hash(i: int, k: float = 0.0) -> float:
    """Stable value in [0, 1) for an integer world-grid cell (seam-safe variation)."""
    return _fract(math.sin(i * 127.1 + k * 311.7) * 43758.5453)


def _pl(pts: Sequence[Pt]) -> str:
    return "M" + "L".join(f"{x:.2f} {y:.2f}" for x, y in pts)


def _poly(pts: Sequence[Pt]) -> str:
    return _pl(pts) + "Z"


def _curve(pts: Sequence[Pt], tension: float = 1.0) -> str:
    """Catmull-Rom segments through ``pts`` without the leading moveto."""
    d = smooth_open(pts, tension)
    return d[d.index("C"):] if "C" in d else ""


def _taper(centre: Sequence[tuple[float, float, float]], tension: float = 0.9) -> str:
    """Closed tapered ribbon along (x, y, thickness) samples (roots, reeds, moss)."""
    upper = [(x, y - t / 2) for x, y, t in centre]
    lower = [(x, y + t / 2) for x, y, t in reversed(centre)]
    return smooth_open(upper, tension) + f"L{lower[0][0]:.2f} {lower[0][1]:.2f}" + _curve(lower, tension) + "Z"


def _vtaper(centre: Sequence[tuple[float, float, float]], tension: float = 0.9) -> str:
    """Closed tapered ribbon for mostly vertical strands (offset sideways)."""
    left = [(x - t / 2, y) for x, y, t in centre]
    right = [(x + t / 2, y) for x, y, t in reversed(centre)]
    return smooth_open(left, tension) + f"L{right[0][0]:.2f} {right[0][1]:.2f}" + _curve(right, tension) + "Z"


def _grid(x0: float, w: float, step: float, margin: int = 2) -> list[float]:
    """World x positions of a fixed grid covering the chunk plus ``margin`` cells."""
    first = math.floor(x0 / step) - margin
    last = math.ceil((x0 + w) / step) + margin
    return [i * step for i in range(first, last + 1)]


def _wave(x: float, w: float, k: int, phase: float = 0.0) -> float:
    """Periodic over the strip width so parallax strips tile seamlessly."""
    return math.sin(2 * math.pi * k * x / w + phase)


def _dot(x: float, y: float, r: float) -> str:
    """Circle as a path subpath, so many dots can be batched into one shape (cheaper to rasterize)."""
    return f"M{x - r:.2f} {y:.2f}a{r:.2f} {r:.2f} 0 1 0 {2 * r:.2f} 0a{r:.2f} {r:.2f} 0 1 0 {-2 * r:.2f} 0Z"


def _glow(s: Svg, cx: float, cy: float, r: float, color: str, alpha: float = 0.5) -> None:
    """Soft emitted-light halo, clamped to the canvas so it never shows a cut edge."""
    r = min(r, cx, cy, s.w - cx, s.h - cy)
    if r < 0.6:
        return
    s.circle(cx, cy, r, fill=s.radial(cx, cy, r, [(0, color, alpha), (0.3, color, alpha * 0.5), (0.65, color, alpha * 0.14), (1, color, 0)]))


def _haze(s: Svg, cx: float, cy: float, rx: float, ry: float, color: str, alpha: float) -> None:
    """Soft elliptical mist (radial gradient squashed by a group transform), clamped to the canvas."""
    rx, ry = min(rx, cx, s.w - cx), min(ry, cy, s.h - cy)
    if rx < 0.6 or ry < 0.3:
        return
    with s.group(f"translate({cx:.2f} {cy:.2f}) scale(1 {max(0.01, ry / rx):.4f})"):
        s.circle(0, 0, rx, fill=s.radial(0, 0, rx, [(0, color, alpha), (0.5, color, alpha * 0.45), (1, color, 0)]))


def _band(s: Svg, w: float, y1: float, y2: float, color: str, alpha: float) -> None:
    """Full-width soft horizontal band (tiles across strip borders)."""
    s.rect(0, y1, w, y2 - y1, fill=s.linear(0, y1, 0, y2, [(0, color, 0), (0.5, color, alpha), (1, color, 0)]))


def _firefly(s: Svg, x: float, y: float, size: float = 1.0, alpha: float = 1.0) -> None:
    _glow(s, x, y, 6 * size, FIRE, 0.45 * alpha)
    s.circle(x, y, 0.9 * size, fill=FIRE_HOT, opacity=min(1.0, 0.95 * alpha))


def _wisp(s: Svg, x: float, y: float, size: float, water: Optional[float] = None, alpha: float = 1.0) -> None:
    """Will-o'-wisp: a teal flame-light with a soft halo (and its reflection on still water)."""
    _glow(s, x, y, size * 4.5, WISP, 0.32 * alpha)
    s.path(f"M{x:.2f} {y - size * 1.7:.2f} Q{x + size * 1.1:.2f} {y - size * 0.2:.2f} {x:.2f} {y + size:.2f} "
           f"Q{x - size * 1.1:.2f} {y - size * 0.2:.2f} {x:.2f} {y - size * 1.7:.2f} Z",
           fill=s.radial(x, y, size * 1.6, [(0, WISP_HOT), (0.55, WISP), (1, WISP, 0.2)]), opacity=alpha)
    if water is not None and 2 * water - y < s.h:
        _haze(s, x, 2 * water - y, size * 1.6, size * 3.4, WISP, 0.22 * alpha)


def _moss_hang(s: Svg, x: float, y: float, width: float, length: float, seed: float, pal: tuple[str, str] = SPANISH_MOSS,
               alpha: float = 0.85) -> None:
    """Festoon of Spanish moss: a few long stringy beards of uneven length with
    wisps branching off, hanging from (x, y)."""
    r = Rand(seed)
    n = max(2, int(width / 6))
    top, tip = pal
    fill = s.linear(0, y, 0, y + length, [(0, top, alpha), (1, tip, alpha * 0.45)])
    for k in range(n):
        sx = x - width / 2 + width * (k + 0.5) / n + r.uniform(-1.5, 1.5)
        ln = length * r.uniform(0.3, 1.0) * (1 - abs(k - (n - 1) / 2) / n * 0.5)
        sway = r.uniform(-5, 5)
        thick = r.uniform(1.2, 2.4) * min(1.0, 0.45 + length / 70)
        centre = [(sx + sway * (j / 7) ** 2 + 1.4 * math.sin(j * 2.3 + k + seed), y + ln * j / 7, thick * (1 - j / 7) ** 0.6 + 0.25) for j in range(8)]
        s.path(_vtaper(centre), fill=fill)
        for j in (2, 4, 5):  # wisps peeling off the strand
            if ln < 10 or r.next() < 0.35:
                continue
            hx, hy, _t = centre[j]
            side = -1 if (j + k) % 2 else 1
            s.path(f"M{hx:.2f} {hy:.2f} q{side * 2.5:.2f} {ln * 0.08:.2f} {side * 1.5:.2f} {ln * 0.2:.2f}", stroke=top, width=0.7, opacity=alpha * 0.7)


def _reeds(s: Svg, x: float, base: float, height: float, n: int, seed: float, fill: str, rim: Optional[str] = None,
           spread: float = 9.0, width: float = 2.4) -> None:
    """Clump of tapered reed blades rising from (x, base)."""
    r = Rand(seed)
    for k in range(n):
        bx = x + r.uniform(-spread, spread)
        hh = height * r.uniform(0.5, 1.0)
        lean = r.uniform(-0.32, 0.32) * hh
        wd = width * r.uniform(0.7, 1.2)
        tx, ty = bx + lean, base - hh
        s.path(f"M{bx - wd:.2f} {base + 1:.2f} Q{bx + lean * 0.25 - wd * 0.3:.2f} {base - hh * 0.55:.2f} {tx:.2f} {ty:.2f} "
               f"Q{bx + lean * 0.25 + wd * 0.6:.2f} {base - hh * 0.5:.2f} {bx + wd:.2f} {base + 1:.2f} Z", fill=fill)
        if rim:
            s.path(f"M{bx + wd * 0.35:.2f} {base:.2f} Q{bx + lean * 0.25 + wd * 0.35:.2f} {base - hh * 0.52:.2f} {tx:.2f} {ty:.2f}",
                   stroke=rim, width=max(0.4, wd * 0.28), opacity=0.55)


def _cattail(s: Svg, x: float, base: float, height: float, lean: float, stem: str, head: tuple[str, str],
             rim: Optional[str] = None, size: float = 1.0) -> None:
    """Cattail: a slender stem with a velvety brown head and a thin spike."""
    tx, ty = x + lean, base - height
    s.path(f"M{x:.2f} {base + 1:.2f} Q{x + lean * 0.15:.2f} {base - height * 0.5:.2f} {tx:.2f} {ty:.2f}", stroke=stem, width=1.3 * size)
    ang = math.degrees(math.atan2(lean, height)) * 0.8
    hx, hy = x + lean * 0.88, ty + 11 * size
    hw, hh = 4.6 * size, 15 * size
    with s.group(f"rotate({ang:.2f} {hx:.2f} {hy:.2f})"):
        s.path(rounded_rect_path(hx - hw / 2, hy - hh / 2, hw, hh, hw / 2), fill=s.linear(hx - hw / 2, 0, hx + hw / 2, 0, [(0, head[0]), (1, head[1])]))
        if rim:
            s.path(f"M{hx - hw * 0.18:.2f} {hy - hh * 0.4:.2f} L{hx - hw * 0.18:.2f} {hy + hh * 0.36:.2f}", stroke=rim, width=0.7 * size, opacity=0.55)
        s.line(hx, hy - hh / 2, hx, hy - hh / 2 - 6 * size, stem, 0.9 * size)


def _bell_mushroom(s: Svg, x: float, base: float, height: float, cap: float, lean: float = 0.0, halo: float = 0.45,
                   outline: Optional[str] = INK, pal: tuple[str, str, str] = (FIRE_HOT, FIRE, FIRE_DEEP)) -> None:
    """Foxfire mushroom: a slender stem under a glowing bell-shaped cap."""
    light, mid, dark = pal
    tx, ty = x + lean, base - height
    lw = max(0.3, min(1.2, cap * 0.09))
    if halo > 0:
        _glow(s, tx, ty - cap * 0.2, cap * 2.8, mid, halo)
    sw = max(0.45, cap * 0.16)
    s.path(f"M{x - sw:.2f} {base + 0.3:.2f} Q{x + lean * 0.3 - sw * 0.4:.2f} {base - height * 0.55:.2f} {tx - sw * 0.6:.2f} {ty:.2f} "
           f"L{tx + sw * 0.6:.2f} {ty:.2f} Q{x + lean * 0.3 + sw * 0.4:.2f} {base - height * 0.55:.2f} {x + sw:.2f} {base + 0.3:.2f} Z",
           fill=s.linear(x - sw, 0, x + sw, 0, [(0, "#e6efd2"), (1, "#7d8a6a")]), stroke=outline, width=lw * 0.7)
    bell = (f"M{tx - cap:.2f} {ty + cap * 0.32:.2f} C{tx - cap * 0.95:.2f} {ty - cap * 0.25:.2f} {tx - cap * 0.45:.2f} {ty - cap * 0.95:.2f} "
            f"{tx + lean * 0.05:.2f} {ty - cap * 1.0:.2f} C{tx + cap * 0.45:.2f} {ty - cap * 0.95:.2f} {tx + cap * 0.95:.2f} {ty - cap * 0.25:.2f} "
            f"{tx + cap:.2f} {ty + cap * 0.32:.2f} Q{tx:.2f} {ty + cap * 0.08:.2f} {tx - cap:.2f} {ty + cap * 0.32:.2f} Z")
    s.path(bell, fill=s.radial(tx - cap * 0.25, ty - cap * 0.55, cap * 1.5, [(0, light), (0.5, mid), (1, dark)]), stroke=outline, width=lw)
    s.path(f"M{tx - cap * 0.78:.2f} {ty + cap * 0.22:.2f} Q{tx:.2f} {ty + cap * 0.02:.2f} {tx + cap * 0.78:.2f} {ty + cap * 0.22:.2f}",
           stroke=light, width=max(0.3, cap * 0.12), opacity=0.85)
    s.circle(tx - cap * 0.3, ty - cap * 0.5, cap * 0.16, fill="#ffffff", opacity=0.75)


def _hang_lantern(s: Svg, x: float, y: float, size: float, lit: bool = True, halo: float = 0.55) -> None:
    """Small iron lantern hanging from a hook at (x, y): hood, glass cage and base."""
    k = size
    cy = y + k * 0.82
    if lit:
        _glow(s, x, cy, k * 3.4, GLOW, halo)
    s.line(x, y, x, y + k * 0.22, IRON_DARK, max(0.5, k * 0.08))
    s.circle(x, y + k * 0.12, k * 0.1, stroke=IRON_DARK, width=max(0.4, k * 0.05))
    glass = [(0, "#ffe9a8"), (0.4, GLOW), (0.8, "#f0a242"), (1, GLOW_DEEP)] if lit else [(0, "#5a6680"), (1, "#202634")]
    s.path(smooth_closed([(x - k * 0.28, y + k * 0.42), (x + k * 0.28, y + k * 0.42), (x + k * 0.36, y + k * 0.82), (x + k * 0.28, y + k * 1.2),
                          (x - k * 0.28, y + k * 1.2), (x - k * 0.36, y + k * 0.82)], 0.35),
           fill=s.radial(x, cy + k * 0.08, k * 0.42, glass), stroke=INK, width=max(0.4, k * 0.07))
    for dx in (-0.14, 0.14):
        s.line(x + dx * k, y + k * 0.44, x + dx * k, y + k * 1.18, IRON_DARK, max(0.35, k * 0.05), 0.8)
    s.path(f"M{x - k * 0.4:.2f} {y + k * 0.44:.2f} L{x:.2f} {y + k * 0.2:.2f} L{x + k * 0.4:.2f} {y + k * 0.44:.2f} Z", fill=IRON_DARK,
           stroke=INK, width=max(0.35, k * 0.05))
    s.rect(x - k * 0.32, y + k * 1.18, k * 0.64, k * 0.14, fill=IRON_DARK, stroke=INK, width=max(0.3, k * 0.04), rx=k * 0.04)
    if lit:  # the flame: a small white-hot teardrop with an amber edge
        fy = cy + k * 0.16
        s.path(f"M{x:.2f} {fy - k * 0.3:.2f} Q{x + k * 0.13:.2f} {fy - k * 0.05:.2f} {x:.2f} {fy + k * 0.08:.2f} Q{x - k * 0.13:.2f} {fy - k * 0.05:.2f} "
               f"{x:.2f} {fy - k * 0.3:.2f} Z", fill="#fffbea", stroke="#f0a242", width=max(0.25, k * 0.03))


def _dead_tree(s: Svg, x: float, base: float, height: float, seed: float, fill: str, rim: Optional[str] = None, lean: float = 0.0,
               outline: Optional[str] = None, trunk: Optional[str] = None) -> None:
    """Bare twisted tree: forking limbs with thin twigs. Silhouette by default;
    with ``outline`` the limbs get an ink edge (outlines first, so joints stay clean)."""
    r = Rand(seed)
    thick = max(1.2, height * 0.075)
    limbs: list[tuple[str, float]] = []

    def limb(px: float, py: float, ang: float, ln: float, th: float, depth: int) -> None:
        a = math.radians(ang)
        bend = r.uniform(-0.35, 0.35)
        ex, ey = px + math.cos(a) * ln, py + math.sin(a) * ln
        mx, my = px + math.cos(a + bend) * ln * 0.55, py + math.sin(a + bend) * ln * 0.55
        limbs.append((f"M{px:.2f} {py:.2f} Q{mx:.2f} {my:.2f} {ex:.2f} {ey:.2f}", th))
        if depth <= 0 or ln < 3:
            return
        for k in range(2 if depth > 1 else 3):
            spread = r.uniform(18, 42) * (1 if k % 2 else -1)
            limb(ex, ey, ang + spread + r.uniform(-8, 8), ln * r.uniform(0.55, 0.75), th * 0.62, depth - 1)

    top = (x + lean, base - height * 0.5)
    limb(top[0], top[1], -90 + r.uniform(-14, 14), height * 0.32, thick * 0.9, 3)
    limb(top[0], top[1] + height * 0.08, -90 - r.uniform(30, 55), height * 0.3, thick * 0.7, 2)
    limb(top[0], top[1] + height * 0.14, -90 + r.uniform(30, 60), height * 0.26, thick * 0.6, 2)
    trunk_d = (f"M{x - thick * 1.6:.2f} {base + 1:.2f} Q{x - thick * 0.6:.2f} {base - height * 0.25:.2f} {top[0] - thick * 0.4:.2f} {top[1]:.2f} "
               f"L{top[0] + thick * 0.4:.2f} {top[1]:.2f} Q{x + thick * 0.7:.2f} {base - height * 0.25:.2f} {x + thick * 1.8:.2f} {base + 1:.2f} Z")
    if outline:
        for d, th in limbs:
            s.path(d, stroke=outline, width=th + 1.6)
        s.path(trunk_d, fill=trunk or fill, stroke=outline, width=1.3)
    else:
        s.path(trunk_d, fill=trunk or fill)
    for d, th in limbs:
        s.path(d, stroke=fill, width=th)
    if rim:
        for d, th in limbs:
            if th > 1.6:
                s.path(d, stroke=rim, width=th * 0.25, opacity=0.45)


class _Cypress:
    """Geometry of a bald cypress: ``at(t, f)`` maps height fraction t
    (0 = water line, 1 = crown) and width fraction f (-1..1) to a point.
    The base flares into the typical buttress."""

    def __init__(self, cx: float, base: float, height: float, width: float, lean: float, seed: float, flare: float = 2.4) -> None:
        self.cx, self.base, self.height, self.width, self.lean, self.seed, self.flare = cx, base, height, width, lean, seed, flare

    def half(self, t: float) -> float:
        return self.width / 2 * (1 + self.flare * (1 - t) ** 7) * (1 - 0.5 * t)

    def at(self, t: float, f: float) -> Pt:
        off = self.lean * t * t + math.sin(t * 5.0 + self.seed) * self.width * 0.05
        return self.cx + off + f * self.half(t), self.base - self.height * t

    def outline(self, n: int = 16) -> str:
        left = [self.at(1 - i / n, -1) for i in range(n + 1)]
        right = [self.at(i / n, 1) for i in range(n + 1)]
        left[-1] = (left[-1][0] - self.width * 0.25, left[-1][1] + 1.5)
        right[0] = (right[0][0] + self.width * 0.25, right[0][1] + 1.5)
        return smooth_open(left, 0.8) + f"L{right[0][0]:.2f} {right[0][1]:.2f}" + _curve(right, 0.8) + "Z"


def _cypress(s: Svg, tr: _Cypress, r: Rand, bark: tuple[str, str, str], rim: str, foliage: tuple[str, str, str], leaf_rim: str,
             moss: tuple[str, str] = SPANISH_MOSS, moss_alpha: float = 0.8, detail: float = 1.0, bare: bool = False,
             outline: Optional[str] = None) -> list[Pt]:
    """Bald cypress: buttressed trunk, a few long limbs ending in flat needle
    pads, Spanish moss hanging from the limbs (``bare``: a dead snag with twiggy
    forks instead of needles). Returns the pad centres."""
    lit, body, dark = bark
    w = tr.width
    limbs = []
    n = 5
    for i in range(n):
        t = 0.5 + 0.46 * i / (n - 1) + r.uniform(-0.04, 0.04)
        side = -1 if i % 2 == 0 else 1
        if i == n - 1:
            side = 1 if r.next() < 0.5 else -1
        sx, sy = tr.at(t, side * 0.3)
        ln = w * r.uniform(1.8, 3.0) * (1.25 - 0.55 * t)
        rise = r.uniform(4, 16)
        ex, ey = sx + side * ln, sy - rise
        limbs.append((sx, sy, ex, ey, side, ln, max(1.4, tr.half(t) * 0.7)))
    for sx, sy, ex, ey, side, ln, th in limbs:
        mx, my = (sx + ex) / 2, min(sy, ey) - ln * 0.08
        s.path(f"M{sx:.2f} {sy:.2f} Q{mx:.2f} {my:.2f} {ex:.2f} {ey:.2f}", stroke=body, width=th)
        s.path(f"M{sx:.2f} {sy - th * 0.3:.2f} Q{mx:.2f} {my - th * 0.3:.2f} {ex:.2f} {ey - th * 0.25:.2f}", stroke=rim, width=max(0.4, th * 0.22),
               opacity=0.45)
    s.path(tr.outline(), fill=s.linear(tr.cx - w * 1.4, 0, tr.cx + w * 1.4, 0, [(0, dark), (0.35, body), (0.7, lit), (0.86, body), (1, dark)]))
    if outline:
        s.path(tr.outline(), stroke=outline, width=1.3)
    for k, f in enumerate((-0.6, -0.25, 0.1, 0.45)):
        pts = [tr.at(t, f + 0.07 * math.sin(t * 9 + k)) for t in [0.02 + i * 0.1 for i in range(9)]]
        s.path(smooth_open(pts), stroke=dark, width=max(0.8, w * 0.05), opacity=0.55)
    s.path(smooth_open([tr.at(t, 0.92) for t in [0.04 + i * 0.1 for i in range(9)]]), stroke=rim, width=max(0.8, w * 0.07), opacity=0.5)
    pads = [(ex, ey, ln) for sx, sy, ex, ey, side, ln, th in limbs]
    top = tr.at(1.0, 0)
    pads.append((top[0], top[1] - 4, w * 2.2))
    if bare:  # a dead snag: forked twigs at the limb ends and a broken top
        for sx, sy, ex, ey, side, ln, th in limbs:
            for k in (-1, 1):
                fx, fy = ex + side * ln * 0.18, ey - ln * (0.12 + 0.08 * k)
                s.path(f"M{ex:.2f} {ey:.2f} Q{(ex + fx) / 2:.2f} {fy + ln * 0.06:.2f} {fx:.2f} {fy:.2f}", stroke=body, width=max(0.8, th * 0.5))
        tx, ty = top
        s.polygon([(tx - w * 0.3, ty + 6), (tx - w * 0.1, ty - 6), (tx + w * 0.05, ty + 2), (tx + w * 0.25, ty - 4), (tx + w * 0.32, ty + 6)], fill=body)
        pads = []
    for px, py, ln in pads:
        rx, ry = ln * 0.62, max(5.0, ln * 0.2)
        for j in range(3):
            cx = px + (j - 1) * rx * 0.55 + r.uniform(-3, 3)
            cy = py - (2.5 if j == 1 else 0) + r.uniform(-1.5, 1.5)
            cr = rx * (0.55 if j == 1 else 0.42)
            s.path(blob(cx, cy, cr, ry * (1.0 if j == 1 else 0.8), 0.16, seed=cx + tr.seed, squash_top=0.75),
                   fill=s.radial(cx - cr * 0.2, cy - ry * 0.9, cr * 1.4, [(0, foliage[0]), (0.55, foliage[1]), (1, foliage[2])]))
        s.path(f"M{px - rx * 0.8:.2f} {py - ry * 0.55:.2f} Q{px:.2f} {py - ry * 1.5:.2f} {px + rx * 0.8:.2f} {py - ry * 0.55:.2f}", stroke=leaf_rim,
               width=max(0.6, ry * 0.18), opacity=0.5)
    if detail > 0:
        for sx, sy, ex, ey, side, ln, th in limbs:
            for u in (0.45, 0.85):
                mx, my = sx + (ex - sx) * u, sy + (ey - sy) * u + ln * 0.03
                _moss_hang(s, mx, my + 1, ln * 0.35, ln * r.uniform(0.6, 1.1) * detail, mx + my, moss, moss_alpha)
    return [(px, py) for px, py, _ln in pads]


def _knee(s: Svg, x: float, base: float, height: float, width: float, fill: tuple[str, str], rim: Optional[str] = None) -> None:
    """Cypress knee: a knobbly rounded woody stump rising from water or mud (blunt, never spiky)."""
    lit, dark = fill
    pts = [(x - width, base + 0.6), (x - width * 0.78, base - height * 0.42), (x - width * 0.74, base - height * 0.8), (x - width * 0.38, base - height),
           (x + width * 0.18, base - height * 1.02), (x + width * 0.62, base - height * 0.82), (x + width * 0.72, base - height * 0.42),
           (x + width, base + 0.6)]
    s.path(smooth_open(pts, 0.8) + "Z", fill=s.linear(x - width, 0, x + width, 0, [(0, dark), (0.42, lit), (1, dark)]))
    if rim:
        s.path(smooth_open([pts[1], pts[2], pts[3], pts[4]], 0.8), stroke=rim, width=max(0.4, width * 0.14), opacity=0.55)
        s.path(f"M{x - width * 0.4:.2f} {base - height * 0.55:.2f} q{width * 0.3:.2f} {-height * 0.06:.2f} {width * 0.5:.2f} {height * 0.04:.2f}",
               stroke=dark, width=max(0.35, width * 0.08), opacity=0.6)


# --------------------------------------------------------------------------- world
class HauntedSwamp(WorldArt):
    id = "haunted_swamp"
    name = "Pântano Assombrado"
    accent = "#b8e05c"  # firefly green
    terrain_headroom = 14.0
    ambient = (212, 220, 242)  # slightly dimmed, cool moonlight (the art itself is authored dark)
    vignette = 0.46
    provisional = False

    # ------------------------------------------------------------------ sky
    def sky(self) -> Svg:
        s = Svg(960, 540)
        hz = HORIZON / 540
        s.rect(0, 0, 960, 540, fill=s.linear(0, 0, 0, 540, [
            (0, "#07091f"), (0.2, "#10153d"), (0.4, "#1b2a5c"), (0.52, "#23426c"), (hz - 0.035, "#2b6476"), (hz, "#3f8382"),
            (hz + 0.008, "#1d3b50"), (0.78, "#142a42"), (1, "#0a1424")]))
        r = Rand(8)
        # stars, denser near the zenith, none inside the moon halo
        for _ in range(120):
            x, y = r.uniform(0, 960), (HORIZON - 50) * r.next() ** 1.7
            rad, a = r.uniform(0.45, 1.25), r.uniform(0.3, 0.9)
            if (x - MOON_X) ** 2 + (y - MOON_Y) ** 2 < 150 ** 2:
                continue
            s.circle(x, y, rad, fill=r.choice(["#eef2ff", "#fff4dc", "#d8e4ff"]), opacity=a * max(0.2, 1 - y / 300))
        for _ in range(9):
            x, y = r.uniform(30, 930), r.uniform(16, 210)
            if (x - MOON_X) ** 2 + (y - MOON_Y) ** 2 < 175 ** 2:
                continue
            _glow(s, x, y, 7, "#d6e2ff", 0.3)
            s.polygon(star_points(x, y, 4.0, 0.7, 4), fill="#f4f6ff", opacity=0.85)
        # the moon: wide cool halo, faint corona ring, glow and a pale disc with soft maria
        mx, my, mr = MOON_X, MOON_Y, MOON_R
        s.circle(mx, my, 330, fill=s.radial(mx, my, 330, [(0, "#dfe6ff", 0.32), (0.16, "#b4c2ee", 0.17), (0.42, "#7f95d0", 0.06),
                                                          (1, "#6a88c0", 0)]))
        s.circle(mx, my, 106, stroke="#e6ebff", width=7, opacity=0.07)
        s.circle(mx, my, 112, stroke="#cdd6ff", width=3, opacity=0.08)
        _glow(s, mx, my, mr * 2.1, "#fffbe8", 0.42)
        s.circle(mx, my, mr, fill=s.radial(mx - mr * 0.35, my - mr * 0.4, mr * 1.7, [(0, "#fffff8"), (0.5, MOON), (1, MOON_SHADE)]))
        for dx, dy, rx, ry, a in ((-20, -12, 19, 12, 0.24), (14, 16, 17, 10, 0.2), (22, -22, 9, 7, 0.18), (-8, 28, 9, 6, 0.16),
                                  (-34, 14, 6, 5, 0.14), (30, 4, 6, 9, 0.12)):
            s.ellipse(mx + dx, my + dy, rx, ry, fill="#b9b8b4", opacity=a)
        for dx, dy, rr in ((-30, -30, 4.5), (8, -36, 3), (36, 26, 3.5), (-14, 40, 2.6), (26, -6, 2.2)):
            s.circle(mx + dx, my + dy, rr, stroke="#c4c2bc", width=1.0, opacity=0.4)
            s.path(f"M{mx + dx - rr * 0.7:.2f} {my + dy - rr * 0.5:.2f} Q{mx + dx:.2f} {my + dy - rr * 1.1:.2f} {mx + dx + rr * 0.7:.2f} "
                   f"{my + dy - rr * 0.5:.2f}", stroke="#ffffff", width=0.8, opacity=0.5)
        s.circle(mx, my, mr, fill=s.radial(mx + mr * 0.75, my + mr * 0.7, mr * 1.3, [(0, "#8a92b8", 0.42), (0.6, "#8a92b8", 0.12), (1, "#8a92b8", 0)]))
        s.circle(mx, my, mr - 0.6, stroke="#ffffff", width=1.3, opacity=0.5)
        # thin clouds crossing the moon: soft dark-indigo streaks, silver-lined where they pass the disc
        for x0, y0, length, thick, rise, seed in ((430, 126, 420, 9.0, 10.0, 1), (520, 178, 380, 7.0, -6.0, 2), (60, 96, 300, 7.0, 6.0, 3)):
            self._cloud_streak(s, x0, y0, length, thick, rise, seed)
        # lilac mist hugging the horizon
        _band(s, 960, 244, 372, "#a497cf", 0.3)
        # still water below the horizon: sky reflections and the moon's glitter path (fixed under the moon)
        for i in range(16):
            y = HORIZON + 6 + i * 13 + r.uniform(-3, 3)
            x = r.uniform(-40, 960)
            s.line(x, y, x + r.uniform(60, 220), y, "#4d7c92", r.uniform(0.8, 1.6), r.uniform(0.15, 0.32))
        _haze(s, mx, 455, 64, 130, "#e8e4d0", 0.12)
        for i in range(30):
            y = HORIZON + 8 + i * 7 + r.uniform(-2, 2)
            t = (y - HORIZON) / (540 - HORIZON)
            half = (8 + 30 * t) * r.uniform(0.5, 1.2)
            x = mx + r.uniform(-7, 7) * (1 + t)
            s.line(x - half, y, x + half, y, MOON, 1.0 + 2.0 * t, 0.2 + 0.45 * r.next() * (1 - abs(x - mx) / 60))
        return s

    @staticmethod
    def _cloud_streak(s: Svg, x0: float, y0: float, length: float, thick: float, rise: float, seed: int) -> None:
        """A thin, frayed cloud streak made of soft puffs; puffs crossing the moon get a silver lining."""
        r = Rand(seed)
        n = max(4, int(length / (thick * 2.2)))
        puffs = []
        for i in range(n):
            u = i / (n - 1)
            taper = math.sin(math.pi * u) ** 0.7
            rx = thick * r.uniform(2.0, 3.2) * (0.6 + 0.4 * taper)
            ry = thick * (0.35 + 0.65 * taper) * r.uniform(0.75, 1.15)
            puffs.append((x0 + length * u + r.uniform(-4, 4), y0 - rise * u + r.uniform(-thick * 0.35, thick * 0.35), rx, ry, taper))
        for cx, cy, rx, ry, taper in puffs:
            _haze(s, cx, cy, rx, ry, "#1a1d46", 0.18 + 0.5 * taper)
        for cx, cy, rx, ry, taper in puffs:
            d = math.hypot(cx - MOON_X, cy - MOON_Y)
            if d < MOON_R + 18:
                k = 1 - d / (MOON_R + 18)
                _haze(s, cx, cy - ry * 0.45, rx * 0.85, ry * 0.42, "#e4e0fa", 0.25 + 0.4 * k)

    def _night_cloud(self, seed: int, w: float, h: float) -> Svg:
        """Thin translucent night cloud with a moonlit upper edge (drifts across the moon)."""
        r = Rand(seed)
        s = Svg(w, h)
        n = 6
        puffs = []
        for i in range(n):
            cx = w * (0.14 + 0.72 * i / (n - 1)) + r.uniform(-8, 8)
            cy = h * 0.58 + r.uniform(-h * 0.1, h * 0.08)
            rx, ry = w * r.uniform(0.12, 0.19), h * r.uniform(0.17, 0.27)
            puffs.append((cx, cy, rx, ry))
        for cx, cy, rx, ry in puffs:
            _haze(s, cx, cy + ry * 0.15, rx, ry, "#232756", 0.72)
        for cx, cy, rx, ry in puffs[1:-1]:
            _haze(s, cx, cy - ry * 0.42, rx * 0.85, ry * 0.36, "#a9a5d8", 0.32)
        return s

    def _particle(self, kind: str) -> Svg:
        """Weather sprites (the scene tints spores mint and draws them additively)."""
        s = Svg(16, 16)
        if kind == "firefly":
            _glow(s, 8, 8, 7.9, "#f4ff60", 0.85)
            s.circle(8, 8, 2.6, fill=s.radial(8, 8, 2.6, [(0, "#ffffd0"), (0.6, "#fbff9a"), (1, "#f4ff60", 0.4)]))
        else:  # a dimmer, smaller firefly further away
            _glow(s, 8, 8, 6.5, "#e8ff50", 0.6)
            s.circle(8, 8, 1.6, fill="#fcffb0")
        return s

    def sky_extras(self) -> dict[str, PropSpec]:
        extras = {f"hs.cloud.{i}": PropSpec(partial(self._night_cloud, 83 + i * 19, w, h), (0, 0))
                  for i, (w, h) in enumerate([(320.0, 58.0), (240.0, 44.0), (400.0, 70.0)])}
        # weather sprites resolve as ``particle.<name>`` (see ``weather``)
        extras["particle.hs_firefly"] = PropSpec(lambda: self._particle("firefly"), (8, 8))
        extras["particle.hs_firefly_far"] = PropSpec(lambda: self._particle("far"), (8, 8))
        return extras

    # ------------------------------------------------------------------ parallax layers
    def _manor(self, s: Svg, x: float, base: float, fill: str, rim: str) -> None:
        """Distant leaning manor: mansard block, witch-hat tower, crooked chimneys, a few lit windows."""
        with s.group(f"rotate(-4 {x:.1f} {base:.1f})"):
            s.rect(x - 52, base - 56, 88, 60, fill=fill)
            s.polygon([(x - 60, base - 54), (x - 46, base - 80), (x + 24, base - 80), (x + 40, base - 54)], fill=fill)
            for dx in (-34, -12):
                s.polygon([(x + dx - 8, base - 70), (x + dx, base - 88), (x + dx + 8, base - 70)], fill=fill)
                s.rect(x + dx - 5.5, base - 74, 11, 9, fill=fill)
            s.rect(x - 41, base - 98, 7, 24, fill=fill)
            s.rect(x - 43, base - 100, 11, 3, fill=fill)
            s.polygon([(x + 6, base - 78), (x + 10, base - 100), (x + 17, base - 99), (x + 13, base - 78)], fill=fill)
            tx = x + 44
            s.rect(tx - 13, base - 108, 26, 112, fill=fill)
            s.polygon([(tx - 18, base - 106), (tx + 3, base - 150), (tx + 18, base - 106)], fill=fill)
            s.line(tx + 3, base - 150, tx + 4.5, base - 160, fill, 1.4)
            s.polygon([(x - 68, base - 26), (x - 52, base - 34), (x - 52, base - 26)], fill=fill)
            for px in (x - 66, x - 59):
                s.rect(px, base - 26, 1.8, 28, fill=fill)
            # moonlit roof edges
            s.path(f"M{x - 60:.1f} {base - 54:.1f} L{x - 46:.1f} {base - 80:.1f} L{x + 24:.1f} {base - 80:.1f}", stroke=rim, width=1.1, opacity=0.6)
            s.path(f"M{tx - 18:.1f} {base - 106:.1f} L{tx + 3:.1f} {base - 150:.1f} L{tx + 18:.1f} {base - 106:.1f}", stroke=rim, width=1.1, opacity=0.6)
            # windows: mostly dark, a few lit (amber = someone keeps a lantern burning)
            lit = {(0, 1), (1, 3), (2, 0)}
            for row in range(2):
                for col in range(4):
                    wx, wy = x - 42 + col * 19, base - 46 + row * 22
                    on = (row, col) in lit
                    if on:
                        _glow(s, wx + 3.5, wy + 5, 12, GLOW, 0.35)
                    s.path(f"M{wx:.1f} {wy + 11:.1f} L{wx:.1f} {wy + 3:.1f} Q{wx + 3.5:.1f} {wy - 1:.1f} {wx + 7:.1f} {wy + 3:.1f} L{wx + 7:.1f} {wy + 11:.1f} Z",
                           fill=GLOW if on else "#2a3154", opacity=0.9 if on else 1.0)
            for wy in (base - 92, base - 70):
                on = wy == base - 92
                if on:
                    _glow(s, tx, wy + 5, 12, GLOW, 0.35)
                s.path(f"M{tx - 3.5:.1f} {wy + 10:.1f} L{tx - 3.5:.1f} {wy + 3:.1f} Q{tx:.1f} {wy - 1:.1f} {tx + 3.5:.1f} {wy + 3:.1f} L{tx + 3.5:.1f} {wy + 10:.1f} Z",
                       fill=GLOW if on else "#2a3154", opacity=0.9 if on else 1.0)
            for dx in (-34, -12):
                s.circle(x + dx, base - 70, 2.4, fill="#2a3154")

    def _keep_far(self, s: Svg, x: float, base: float, fill: str, rim: str) -> None:
        """The lantern keep far away: a tall tower on a crag with the great lantern room on top."""
        s.rect(x - 15, base - 128, 30, 132, fill=fill)
        s.rect(x - 19, base - 134, 38, 8, fill=fill)
        for k in range(5):
            s.rect(x - 19 + k * 8.4, base - 140, 4.6, 7, fill=fill)
        s.rect(x - 11, base - 166, 22, 33, fill=fill)
        s.polygon([(x - 15, base - 165), (x, base - 186), (x + 15, base - 165)], fill=fill)
        s.line(x, base - 186, x, base - 194, fill, 1.2)
        _glow(s, x, base - 150, 22, "#7dffa0", 0.28)
        for dx in (-5.5, 0.0, 5.5):
            s.rect(x + dx - 1.6, base - 160, 3.2, 16, fill="#9dffb4", opacity=0.55)
        for j in range(4):
            s.rect(x - 1.4 + (j % 2) * 5, base - 112 + j * 24, 2.8, 6, fill="#2a3154")
        s.path(f"M{x - 19:.1f} {base - 134:.1f} L{x + 19:.1f} {base - 134:.1f} M{x - 15:.1f} {base - 165:.1f} L{x:.1f} {base - 186:.1f}", stroke=rim,
               width=1.0, opacity=0.6)

    def _far(self, variant: int) -> Svg:
        """Misty hills with the leaning manor (or the lantern keep), dead trees and wisps over the marsh."""
        w, h = 1200.0, 300.0
        shore = 250.0
        s = Svg(w, h)
        r = Rand(31 + variant * 17)

        def win(x: float) -> float:
            return math.sin(math.pi * x / w) ** 2

        def back_y(x: float) -> float:
            return 132 + 13 * _wave(x, w, 2, 0.4) + 7 * _wave(x, w, 5, 1.1) + win(x) * 16 * _wave(x, w, 3, 2.0 + 1.7 * variant)

        if variant == 0:
            bumps = ((760.0, 95.0, 56.0), (300.0, 80.0, 20.0))
        else:
            bumps = ((170.0, 55.0, 64.0), (720.0, 120.0, 18.0))

        def front_y(x: float) -> float:
            y = 202 + 8 * _wave(x, w, 3, 0.7) + 4 * _wave(x, w, 8, 2.3) + win(x) * 7 * _wave(x, w, 4, 1.0 + variant)
            for bx, bw, bh in bumps:
                y -= bh * math.exp(-((x - bx) / bw) ** 2)
            return y

        xs = [w * i / 60 for i in range(61)]
        back = [(x, back_y(x)) for x in xs]
        s.path(_pl([(0, shore + 2)] + back + [(w, shore + 2)]) + "Z", fill=s.linear(0, 100, 0, shore, [(0, "#34416e"), (1, "#3e4f7c")]))
        s.path(smooth_open(back, 0.6), stroke="#6a7cb0", width=1.0, opacity=0.35)
        for _ in range(9):
            tx = r.uniform(20, w - 20)
            _dead_tree(s, tx, back_y(tx) + 3, r.uniform(16, 30), tx, "#34416e")
        _band(s, w, 150, 236, MIST, 0.26)
        front_fill = "#1c2249"
        rim = "#5f70a8"
        front = [(x, front_y(x)) for x in xs]
        if variant == 0:
            self._manor(s, 760, front_y(760) + 4, front_fill, rim)
            _dead_tree(s, 690, front_y(690) + 2, 46, 5.0, front_fill, rim, lean=-4)
            for k in range(6):  # crooked fence down the hill
                fx = 840 + k * 13
                fy = front_y(fx) + 1
                s.line(fx, fy, fx + (k % 2) * 1.5 - 0.5, fy - 8 - (k % 3), front_fill, 1.6)
            s.path(_pl([(840 + k * 13, front_y(840 + k * 13) - 5) for k in range(6)]), stroke=front_fill, width=1.0)
        else:
            self._keep_far(s, 170, front_y(170) + 6, front_fill, rim)
            # a stilt hut on the marsh with a lit window
            hx = 640.0
            hy = front_y(hx) + 10
            for px in (hx - 14, hx - 4, hx + 8, hx + 16):
                s.line(px, hy - 18, px, shore + 2, front_fill, 1.6)
            s.rect(hx - 18, hy - 34, 38, 18, fill=front_fill)
            s.polygon([(hx - 23, hy - 33), (hx + 1, hy - 50), (hx + 25, hy - 33)], fill=front_fill)
            _glow(s, hx + 8, hy - 26, 12, GLOW, 0.4)
            s.rect(hx + 5, hy - 29, 6, 6, fill=GLOW, opacity=0.9)
        s.path(_pl([(0, shore + 2)] + front + [(w, shore + 2)]) + "Z", fill=s.linear(0, 140, 0, shore, [(0, "#1f264e"), (1, "#232c56")]))
        s.path(smooth_open(front, 0.6), stroke=rim, width=1.3, opacity=0.45)
        for _ in range(7):
            tx = r.uniform(30, w - 30)
            if any(abs(tx - bx) < bw * 0.8 for bx, bw, _bh in bumps[:1]):
                continue
            _dead_tree(s, tx, front_y(tx) + 3, r.uniform(26, 44), tx * 1.3, front_fill, rim, lean=r.uniform(-5, 5))
        # reeds along the shore
        for k in range(70):
            rx = (k + 0.5) * w / 70 + r.uniform(-6, 6)
            s.line(rx, shore + 1, rx + r.uniform(-1.5, 1.5), shore - r.uniform(3, 9), front_fill, 1.0)
        # water: fades into the sky's own water, mirrors the hills near the shore
        s.rect(0, shore, w, h - shore, fill=s.linear(0, shore, 0, h, [(0, "#1d3b50"), (0.45, "#1a344a", 0.85), (1, "#16304a", 0)]))
        refl = [(x, shore + (shore - front_y(x)) * 0.85) for x in xs]
        s.path(_pl([(0, shore)] + refl + [(w, shore)]) + "Z", fill=s.linear(0, shore, 0, h, [(0, "#121836", 0.7), (1, "#121836", 0)]))
        for _ in range(26):
            gx, gy = r.uniform(0, w), r.uniform(shore + 3, h - 6)
            s.line(gx, gy, min(w, gx + r.uniform(18, 70)), gy, "#6f8cb0", r.uniform(0.7, 1.4), r.uniform(0.2, 0.4))
        s.line(0, shore + 0.5, w, shore + 0.5, "#4e6890", 1.0, 0.5)
        # will-o'-wisps drifting over the marsh
        for _ in range(5):
            wx = r.uniform(40, w - 40)
            _wisp(s, wx, shore - r.uniform(8, 22), r.uniform(1.6, 2.4), shore, 0.9)
        _band(s, w, 196, 262, MIST, 0.18)
        return s

    def _mid(self, variant: int) -> Svg:
        """Bald cypresses standing in still water (mirrored), knees, lily pads, a dock or a stilt cabin, lit mist."""
        w, h = 1100.0, 420.0
        water = 300.0
        s = Svg(w, h)
        r = Rand(57 + variant * 23)
        # misty cypress line far behind (wraps across the strip edges)
        far_fill = "#2c3a62"
        for k in range(16):
            cx = (k + 0.5) * w / 16 + r.uniform(-20, 20)
            hh = r.uniform(40, 86)
            for shift in (-w, 0.0, w):
                x = cx + shift
                if -40 < x < w + 40:
                    s.path(f"M{x - 5:.1f} {water + 1:.1f} Q{x - 2:.1f} {water - hh * 0.5:.1f} {x:.1f} {water - hh:.1f} Q{x + 2:.1f} {water - hh * 0.5:.1f} "
                           f"{x + 5:.1f} {water + 1:.1f} Z", fill=far_fill, opacity=0.85)
                    s.path(blob(x, water - hh, hh * 0.32, hh * 0.1, 0.2, seed=k * 7.1), fill=far_fill, opacity=0.85)
                    s.path(blob(x + hh * 0.12, water - hh * 0.7, hh * 0.24, hh * 0.08, 0.2, seed=k * 3.3), fill=far_fill, opacity=0.85)
        _band(s, w, water - 70, water + 10, MIST, 0.22)
        # translucent water: the sky's moon path shows through
        s.rect(0, water, w, h - water, fill=s.linear(0, water, 0, h, [(0, "#1a3a4e", 0.4), (1, "#0c1a2a", 0.7)]))
        trees = ([(170.0, 262.0, 30.0, False), (560.0, 176.0, 20.0, True), (890.0, 236.0, 26.0, False)] if variant == 0
                 else [(90.0, 230.0, 24.0, False), (430.0, 280.0, 32.0, False), (980.0, 186.0, 20.0, True)])
        bark = ("#4a4a68", "#2e2e48", "#1a1a2c")
        for cx, height, width, bare in trees:
            tr = _Cypress(cx + r.uniform(-20, 20), water, height, width, r.uniform(-18, 18), cx * 0.01)
            # reflection first (under the trunk), broken by ripples
            refl = [(px, 2 * water - py) for px, py in (tr.at(t, -1) for t in [i / 10 for i in range(11)])]
            refl += [(px, 2 * water - py) for px, py in (tr.at(1 - i / 10, 1) for i in range(11))]
            s.path(smooth_closed(refl, 0.6), fill=s.linear(0, water, 0, water + height * 0.8, [(0, "#0a1020", 0.55), (1, "#0a1020", 0)]))
            for j in range(6):
                yy = water + 6 + j * 13
                s.line(tr.cx - width * 2.2, yy, tr.cx + width * 2.2, yy, "#2e5a70", 1.2, 0.35)
            _cypress(s, tr, r, bark, "#8090c0", FOLIAGE, "#7aa094", moss_alpha=0.7, bare=bare)
            for k in range(r.choice([3, 4, 5])):
                kx = tr.cx + r.uniform(-width * 2.6, width * 2.6)
                if abs(kx - tr.cx) < width * 1.2:
                    continue
                kh = r.uniform(6, 15)
                _knee(s, kx, water + 1, kh, kh * 0.45, ("#4e4a66", "#26243a"), "#8a96c4")
                s.ellipse(kx, water + 1.5, kh * 0.8, 1.6, stroke="#6f8cb0", width=0.7, opacity=0.5)
            s.ellipse(tr.cx, water + 1.5, width * 2.0, 3.2, stroke="#7a96ba", width=0.9, opacity=0.4)
        # set dressing: a sunken dock with a moored boat (0) or a stilt cabin (1)
        if variant == 0:
            dx = 360.0
            for px in (dx, dx + 34, dx + 68, dx + 102):
                s.rect(px - 2.2, water - 26 + (px - dx) * 0.06, 4.4, 34, fill="#2e2a40")
            s.path(_poly([(dx - 8, water - 26), (dx + 110, water - 18), (dx + 110, water - 13), (dx - 8, water - 21)]), fill="#3a3550")
            s.path(f"M{dx - 8:.1f} {water - 26:.1f} L{dx + 110:.1f} {water - 18:.1f}", stroke="#8a90b8", width=1.0, opacity=0.55)
            bx = dx + 150
            s.path(f"M{bx - 30:.1f} {water - 6:.1f} Q{bx:.1f} {water + 6:.1f} {bx + 30:.1f} {water - 6:.1f} L{bx + 24:.1f} {water - 1:.1f} "
                   f"Q{bx:.1f} {water + 4:.1f} {bx - 24:.1f} {water - 1:.1f} Z", fill="#2c2a3e")
            s.path(f"M{bx - 30:.1f} {water - 6:.1f} Q{bx:.1f} {water - 1:.1f} {bx + 30:.1f} {water - 6:.1f}", stroke="#8a90b8", width=1.0, opacity=0.6)
            s.line(bx + 18, water - 6, bx + 20, water - 34, "#2c2a3e", 1.6)
            _hang_lantern(s, bx + 20, water - 34, 7, True, 0.5)
            _haze(s, bx + 20, water + 22, 6, 14, GLOW, 0.25)
        else:
            cx0 = 700.0
            for px in (cx0 - 40, cx0 - 12, cx0 + 16, cx0 + 44):
                s.rect(px - 2.4, water - 40, 4.8, 48, fill="#2a2840")
                s.line(px - 2, water + 4, px + 2, water + 30, "#0a1020", 4, 0.25)
            s.rect(cx0 - 50, water - 92, 104, 54, fill=s.linear(0, water - 92, 0, water - 38, [(0, "#3a3652"), (1, "#26243a")]))
            for k in range(5):
                s.line(cx0 - 50, water - 82 + k * 10, cx0 + 54, water - 82 + k * 10, "#1c1a2c", 1.0, 0.7)
            s.polygon([(cx0 - 62, water - 90), (cx0 + 2, water - 132), (cx0 + 66, water - 90)], fill="#24223a")
            s.path(f"M{cx0 - 62:.1f} {water - 90:.1f} L{cx0 + 2:.1f} {water - 132:.1f} L{cx0 + 66:.1f} {water - 90:.1f}", stroke="#8a90b8", width=1.2,
                   opacity=0.55)
            s.rect(cx0 + 24, water - 120, 9, 22, fill="#24223a")
            for k in range(4):
                _haze(s, cx0 + 30 + k * 6, water - 130 - k * 10, 6 + k * 3, 5 + k * 2, "#9a9cc4", 0.25 - k * 0.05)
            _glow(s, cx0 - 20, water - 66, 30, GLOW, 0.4)
            s.rect(cx0 - 30, water - 76, 18, 16, fill=s.radial(cx0 - 21, water - 68, 12, [(0, GLOW_HOT), (0.6, GLOW), (1, GLOW_DEEP)]))
            s.line(cx0 - 21, water - 76, cx0 - 21, water - 60, "#3a2a20", 1.2)
            s.line(cx0 - 30, water - 68, cx0 - 12, water - 68, "#3a2a20", 1.2)
            s.rect(cx0 + 8, water - 78, 14, 40, fill="#141322")
            s.rect(cx0 - 58, water - 40, 120, 4, fill="#2e2a44")
            _hang_lantern(s, cx0 + 50, water - 88, 7, True, 0.5)
            _haze(s, cx0 - 20, water + 26, 14, 22, GLOW, 0.2)
            s.path(f"M{cx0 - 150:.1f} {water + 2:.1f} L{cx0 - 70:.1f} {water - 10:.1f} L{cx0 - 66:.1f} {water - 3:.1f} L{cx0 - 148:.1f} {water + 6:.1f} Z",
                   fill="#2c2840")
        # lily pads and a few water lilies
        for _ in range(14):
            lx, ly = r.uniform(20, w - 20), water + r.uniform(4, 60)
            rx = r.uniform(5, 11) * (1 + (ly - water) / 90)
            s.path(f"M{lx:.2f} {ly:.2f} L{lx + rx:.2f} {ly - rx * 0.08:.2f} A{rx:.2f} {rx * 0.28:.2f} 0 1 1 {lx + rx * 0.9:.2f} {ly + rx * 0.14:.2f} Z",
                   fill="#2f4c40", opacity=0.9)
            s.path(f"M{lx - rx * 0.8:.2f} {ly - rx * 0.12:.2f} Q{lx:.2f} {ly - rx * 0.32:.2f} {lx + rx * 0.6:.2f} {ly - rx * 0.2:.2f}", stroke="#6f9a80",
                   width=0.8, opacity=0.6)
            if r.next() < 0.22:
                fx = lx - rx * 0.2
                for k in range(5):
                    a = math.radians(-160 + k * 35)
                    s.path(f"M{fx:.2f} {ly - 1:.2f} L{fx + math.cos(a) * 3.2:.2f} {ly - 1 + math.sin(a) * 2.6:.2f}", stroke="#f2eef8", width=1.6)
                s.circle(fx, ly - 1.4, 0.9, fill=FIRE)
        # glints on the water
        for _ in range(40):
            gx, gy = r.uniform(0, w), r.uniform(water + 3, h - 10)
            s.line(gx, gy, gx + r.uniform(6, 28), gy, "#9fb6d8", r.uniform(0.6, 1.2), r.uniform(0.18, 0.4))
        for _ in range(3):
            _wisp(s, r.uniform(60, w - 60), water - r.uniform(14, 40), r.uniform(1.8, 2.6), water, 0.85)
        for _ in range(16):
            _firefly(s, r.uniform(10, w - 10), r.uniform(120, water - 6), r.uniform(0.7, 1.1), 0.9)
        # lilac mist lit by the moon: the backdrop of the play band
        _band(s, w, water - 10, water + 120, MIST, 0.3)
        return s

    def _near(self, variant: int) -> Svg:
        """Dark bank in front: reeds, cattails, a crooked lantern post, knees; deep water below (pits)."""
        w, h = 900.0, 300.0
        bank = 160.0
        s = Svg(w, h)
        r = Rand(71 + variant * 13)

        def bank_y(x: float) -> float:
            return bank + 4 * _wave(x, w, 3, 0.4 + variant) + 2.5 * _wave(x, w, 7, 1.3)

        sil, rim = "#121a24", "#4a6478"
        # crooked lantern post(s)
        for lx in ([300.0] if variant == 0 else [140.0, 690.0]):
            lx += r.uniform(-30, 30)
            by = bank_y(lx)
            top = by - r.uniform(118, 132)
            lean = r.uniform(-8, 8)
            s.path(f"M{lx - 3.5:.1f} {by + 4:.1f} Q{lx - 2:.1f} {(by + top) / 2:.1f} {lx + lean - 2:.1f} {top:.1f} L{lx + lean + 2.4:.1f} {top:.1f} "
                   f"Q{lx + 2.6:.1f} {(by + top) / 2:.1f} {lx + 3.8:.1f} {by + 4:.1f} Z", fill="#1a1820")
            s.path(f"M{lx + 2.4:.1f} {by:.1f} Q{lx + 2.4:.1f} {(by + top) / 2:.1f} {lx + lean + 2:.1f} {top + 2:.1f}", stroke="#5a5470", width=0.9, opacity=0.6)
            arm_x = lx + lean + 20
            s.path(f"M{lx + lean:.1f} {top + 6:.1f} Q{lx + lean + 10:.1f} {top - 2:.1f} {arm_x:.1f} {top + 2:.1f}", stroke="#1a1820", width=2.6)
            _hang_lantern(s, arm_x, top + 2, 13, True, 0.6)
        # reeds and cattails (kept off the strip edges so no blade is cut where strips meet)
        x = r.uniform(30, 50)
        while x < w - 40:
            by = bank_y(x)
            roll = r.next()
            if roll < 0.55:
                _reeds(s, x, by + 2, r.uniform(40, 92), int(r.uniform(6, 12)), x + variant, sil, rim, spread=r.uniform(8, 16), width=2.6)
            elif roll < 0.85:
                for k in range(int(r.uniform(3, 6))):
                    cx = x + r.uniform(-12, 12)
                    _cattail(s, cx, by + 2, r.uniform(56, 104), r.uniform(-10, 10), "#1a2420", ("#4a3628", "#22160e"), "#8a7058", 1.1)
                _reeds(s, x, by + 2, 40, 5, x * 1.7, sil, rim, spread=10)
            else:
                for k in range(3):
                    kx = x + k * 9 + r.uniform(-3, 3)
                    _knee(s, kx, by + 2, r.uniform(10, 22), r.uniform(5, 8), ("#2a2634", "#141218"), "#6a6688")
            x += r.uniform(36, 80)
        crest = [(x, bank_y(x)) for x in [w * i / 45 for i in range(46)]]
        s.path(smooth_open(crest, 0.7) + f"L{w} {h} L0 {h} Z", fill=s.linear(0, bank - 8, 0, h, [(0, "#121820"), (0.35, "#0a0f16"), (1, "#05070b")]))
        s.path(smooth_open(crest, 0.7), stroke="#3e5466", width=1.4, opacity=0.6)
        # the deep water seen through pits
        for _ in range(18):
            gx, gy = r.uniform(0, w), r.uniform(bank + 30, h - 10)
            s.line(gx, gy, gx + r.uniform(10, 40), gy, "#3a5a74", r.uniform(0.6, 1.2), r.uniform(0.15, 0.3))
        for _ in range(10):
            _firefly(s, r.uniform(10, w - 10), r.uniform(40, bank - 10), r.uniform(0.8, 1.2))
        return s

    def layer_art(self) -> dict[str, PropSpec]:
        art: dict[str, PropSpec] = {}
        for i in range(2):
            art[f"hs.far.{i}"] = PropSpec(partial(self._far, i), (0, 0))
            art[f"hs.mid.{i}"] = PropSpec(partial(self._mid, i), (0, 0))
            art[f"hs.near.{i}"] = PropSpec(partial(self._near, i), (0, 0))
        return art

    def layers(self) -> list[Layer]:
        # far shore sits on the sky's horizon (y 332); the mid water line at ~350 and
        # the near bank just under the ground line, so only reed tops show above it.
        return [
            Layer("far", 0.07, ["hs.far.0", "hs.far.1"], 1200, -68, vertical=0.05),
            Layer("mid", 0.25, ["hs.mid.0", "hs.mid.1"], 1100, 15, vertical=0.15),
            Layer("near", 0.5, ["hs.near.0", "hs.near.1"], 900, 135, vertical=0.32),
        ]

    # ------------------------------------------------------------------ terrain
    def terrain(self, style: str, w: float, h: float, seed: int, left: bool, right: bool, top: bool = True, x0: float = 0.0,
                surface: str = "normal") -> Svg:
        """Peat-mud bank chunk. World-x functions drive everything that crosses
        a chunk border (strata, roots, mud lip, root loops, moss fringe), so
        adjacent chunks join seamlessly; only the hanging edges are outlined."""
        if style == "cave":
            return self._cave(w, h, seed, left, right, x0)
        if style == "fortress":
            return self._keep_wall(w, h, seed, left, right, top, x0)
        hr = self.terrain_headroom
        s = Svg(w, h + hr)
        r = Rand(seed)
        y0 = hr
        bottom = h + hr
        rl, rr = (11.0 if left else 0.0), (11.0 if right else 0.0)
        yb = y0 + (4.0 if top else 0.0)
        body = (f"M{rl:.1f} {yb:.1f} L{w - rr:.1f} {yb:.1f} Q{w:.1f} {yb:.1f} {w:.1f} {yb + rr:.1f} L{w:.1f} {bottom:.1f} "
                f"L0 {bottom:.1f} L0 {yb + rl:.1f} Q0 {yb:.1f} {rl:.1f} {yb:.1f} Z")
        s.path(body, fill=s.linear(0, y0, 0, y0 + min(h, 230), [(0, PEAT_TOP), (0.22, PEAT), (0.6, PEAT_DARK), (1, PEAT_DEEP)]))
        self._strata(s, w, x0, y0, bottom)
        # peat fibres and embedded stones (chunk-local, kept inside the chunk)
        fibres: dict[str, list[str]] = {"#120d0a": [], "#5a4838": []}
        for _ in range(max(2, int(w / 16))):
            fx, fy = r.uniform(4, w - 12), r.uniform(y0 + 16, min(bottom - 4, y0 + 150))
            ln = r.uniform(3, 8)
            fibres[r.choice(["#120d0a", "#5a4838"])].append(f"M{fx:.2f} {fy:.2f}L{fx + ln:.2f} {fy + r.uniform(-1.2, 1.2):.2f}")
        for color, segs in fibres.items():
            if segs:
                s.path("".join(segs), stroke=color, width=0.7, opacity=0.45)
        for _ in range(max(2, int(w / 40))):
            pr = r.uniform(2.4, 6.4)
            px, py = r.uniform(pr * 1.6, w - pr * 1.6), r.uniform(y0 + 22, max(y0 + 23, bottom - 8))
            s.path(blob(px, py, pr * 1.35, pr, 0.12, seed=px), fill=s.radial(px - pr * 0.4, py - pr * 0.5, pr * 1.7, [(0, STONE_HI), (0.55, STONE),
                                                                                                                (1, STONE_DARK)]),
                   stroke="#0e0b09", width=0.7, opacity=0.9)
            if pr > 4.6:
                s.path(blob(px - pr * 0.3, py - pr * 0.72, pr * 0.8, pr * 0.32, 0.2, seed=py), fill="#4d6a39", opacity=0.9)
        # foxfire specks: tiny glowing fungus in the peat
        for _ in range(max(1, int(w / 120))):
            if h < 50:
                break
            gx, gy = r.uniform(12, w - 12), r.uniform(y0 + 40, min(bottom - 10, y0 + 120))
            for k in range(3):
                px, py = gx + r.uniform(-6, 6), gy + r.uniform(-3, 3)
                _glow(s, px, py, 4, FIRE, 0.35)
                s.circle(px, py, 0.7, fill=FIRE_HOT)
        if h > 40:
            self._roots(s, w, x0, y0, bottom)
        # exposed banks: shadowed face, dangling rootlets, a dark outline
        for side, exposed in ((-1, left), (1, right)):
            if not exposed:
                continue
            ex = 0.0 if side < 0 else w
            s.path(f"M{ex:.1f} {y0 + 8:.1f} L{ex - side * 9:.1f} {y0 + 13:.1f} L{ex - side * 7:.1f} {bottom:.1f} L{ex:.1f} {bottom:.1f} Z",
                   fill="#060404", opacity=0.45)
            for k in range(3):
                ry = y0 + 14 + k * 12 + r.uniform(-3, 3)
                pts = [(ex - side * 3, ry), (ex - side * (1.5 + r.uniform(0, 2)), ry + 7), (ex - side * r.uniform(0.5, 3), ry + 13 + r.uniform(0, 6))]
                s.path(smooth_open(pts), stroke=ROOT_HI, width=1.0, opacity=0.7)
            s.path(f"M{ex - side * 0.6:.1f} {yb + 10:.1f} L{ex - side * 0.6:.1f} {bottom:.1f}", stroke=INK, width=1.3, opacity=0.8)
        if top:
            self._bank_cap(s, w, x0, y0, left, right, r, surface)
        return s

    def _strata(self, s: Svg, w: float, x0: float, y0: float, bottom: float) -> None:
        """Wavy mud layers (world-aligned): a lighter band over a dark seam (batched into three shapes)."""
        xs = [gx - x0 for gx in _grid(x0, w, 12.0)]
        bands, seams = [], []
        for k in range(5):
            base = y0 + 30 + k * 27
            if base > bottom - 8:
                break

            def yy(lx: float, k: int = k, base: float = base) -> float:
                gx = x0 + lx
                return base + 3.4 * math.sin(gx * 0.037 + k * 1.9) + 1.8 * math.sin(gx * 0.011 + k)

            top_edge = [(lx, yy(lx)) for lx in xs]
            low_edge = [(lx, yy(lx) + 8) for lx in reversed(xs)]
            bands.append(smooth_open(top_edge) + f"L{low_edge[0][0]:.2f} {low_edge[0][1]:.2f}" + _curve(low_edge) + "Z")
            seams.append(smooth_open([(lx, yy(lx) + 8) for lx in xs]))
        if bands:
            s.path("".join(bands), fill="#6a5644", opacity=0.1)
            s.path("".join(seams), stroke="#0e0a08", width=1.6, opacity=0.36)

    def _roots(self, s: Svg, w: float, x0: float, y0: float, bottom: float, salt: float = 0.0) -> None:
        """Twisted roots diving from the bank into the mud (world-aligned, two strands wound together)."""
        period = 130.0
        fill = s.linear(0, y0, 0, y0 + 70, [(0, ROOT_HI), (0.35, ROOT), (1, ROOT_DARK)])
        for k in range(math.floor((x0 - 260) / period), math.ceil((x0 + w + 40) / period) + 1):
            if _hash(k, 1.3 + salt) < 0.25:
                continue
            start = k * period + _hash(k, 2.1 + salt) * 60
            length = 70 + 120 * _hash(k, 3.7 + salt)
            depth = min(bottom - y0 - 16, 18 + 40 * _hash(k, 4.4 + salt))
            if depth < 10:
                continue
            direction = 1 if _hash(k, 5.9 + salt) > 0.5 else -1
            thick = 2.6 + 3.0 * _hash(k, 6.2 + salt)
            centre = []
            for j in range(11):
                t = j / 10
                gx = start + direction * length * t
                gy = y0 + 8 + depth * math.sin(min(1.0, t * 1.15) * math.pi * 0.6) + 2.4 * math.sin(gx * 0.1 + k)
                centre.append((gx - x0, gy, thick * (1 - t) ** 0.8 + 0.5))
            if max(p[0] for p in centre) < -12 or min(p[0] for p in centre) > w + 12:
                continue
            s.path(_taper(centre), fill=fill, stroke=ROOT_DARK, width=0.7)
            # a thinner strand winding around the main root
            wind = [(x, y + math.sin(j * 1.6 + k) * t * 0.55, max(0.4, t * 0.42)) for j, (x, y, t) in enumerate(centre[:9])]
            s.path(_taper(wind), fill=ROOT, stroke=ROOT_DARK, width=0.5)
            s.path(smooth_open([(x, y - t * 0.3) for x, y, t in centre[:7]]), stroke="#c8a888", width=max(0.5, thick * 0.16), opacity=0.4)
            for j in (4, 7):
                px, py, pt = centre[j]
                bend = (_hash(k, 7.0 + j) - 0.5) * 16
                rootlet = [(px, py + pt * 0.3), (px + bend * 0.5 + direction * 4, py + 8), (px + bend, py + 15 + 10 * _hash(k, 8.0 + j))]
                s.path(smooth_open(rootlet), stroke=ROOT, width=max(0.6, pt * 0.35), opacity=0.9)

    def _bank_cap(self, s: Svg, w: float, x0: float, y0: float, left: bool, right: bool, r: Rand, surface: str) -> None:
        """Wet mud lip with root loops under a moss carpet; sedges and foxfire mushrooms on top."""
        top_c, body_c, dark_c, deep_c, rim_c = MOSS.get(surface, MOSS["normal"])
        slick = surface == "ice"
        muck = surface == "sticky"
        step = 5.0

        def top_y(gx: float) -> float:
            return y0 - 0.6 - 1.5 * (0.5 + 0.5 * math.sin(gx * 0.17 + 1.4 * math.sin(gx * 0.043)))

        def lip_y(gx: float) -> float:
            return y0 + 6.0 + 1.2 * math.sin(gx * 0.083 + 0.6) + 0.8 * math.sin(gx * 0.29)

        def mud_y(gx: float) -> float:
            return y0 + 11.5 + 1.6 * math.sin(gx * 0.061 + 2.0) + 1.0 * math.sin(gx * 0.19 + 0.3)

        cells = range(math.floor(x0 / step) - 3, math.ceil((x0 + w) / step) + 4)
        lo, hi = (4.0 if left else -1e9), (w - 4.0 if right else 1e9)
        # wet mud lip: the bank's edge just under the moss, with a moonlit shine
        mxs = [gx - x0 for gx in _grid(x0, w, 4.0)]
        mxs = [x for x in mxs if (-6 if not left else 2.5) <= x <= (w + 6 if not right else w - 2.5)]
        mud_top = [(lx, lip_y(x0 + lx) - 2) for lx in mxs]
        mud_low = [(lx, mud_y(x0 + lx)) for lx in reversed(mxs)]
        s.path(smooth_open([(x, y + 3) for x, y in reversed(mud_low)], 0.8), stroke="#050303", width=4.0, opacity=0.3)
        s.path(smooth_open(mud_top, 0.8) + f"L{mud_low[0][0]:.2f} {mud_low[0][1]:.2f}" + _curve(mud_low, 0.8) + "Z",
               fill=s.linear(0, y0 + 4, 0, y0 + 14, [(0, "#3a2e24"), (0.6, MUD_WET), (1, "#140f0b")]))
        s.path(smooth_open([(x, y - 2.2) for x, y in reversed(mud_low)], 0.8), stroke=MUD_SHINE, width=0.9, opacity=0.35)
        s.path(smooth_open(list(reversed(mud_low)), 0.8), stroke="#0a0705", width=1.0, opacity=0.8)
        # root loops breaking out of the bank (world-aligned)
        loop_fill = s.linear(0, y0 + 4, 0, y0 + 18, [(0, ROOT_HI), (1, ROOT)])
        for k in range(math.floor((x0 - 40) / 70.0), math.ceil((x0 + w + 10) / 70.0) + 1):
            if _hash(k, 9.3) < 0.45:
                continue
            gx = k * 70.0 + _hash(k, 9.7) * 40
            lx = gx - x0
            span = 14 + 14 * _hash(k, 10.1)
            if (left and lx < 6) or (right and lx + span > w - 6):
                continue
            sag = 5 + 6 * _hash(k, 10.7)
            th = 1.8 + 1.6 * _hash(k, 11.3)
            centre = [(lx + span * t, lip_y(gx + span * t) + 1.5 + sag * math.sin(math.pi * t), th * (0.7 + 0.3 * math.sin(math.pi * t)))
                      for t in [i / 8 for i in range(9)]]
            s.path(_taper(centre), fill=loop_fill, stroke=ROOT_DARK, width=0.6)
            if _hash(k, 12.1) > 0.5:
                px, py, _t = centre[5]
                s.path(f"M{px:.2f} {py:.2f} q{1.5:.2f} 5 {-0.5:.2f} {9 + 6 * _hash(k, 12.7):.2f}", stroke=ROOT, width=0.9)
        # the moss carpet (world-aligned fringe)
        top_pts = [(i * step - x0, top_y(i * step)) for i in cells if lo <= i * step - x0 <= hi]
        if left:
            top_pts = [(0.3, y0 + 5.0), (1.3, y0 + 1.2)] + top_pts
        if right:
            top_pts = top_pts + [(w - 1.3, y0 + 1.2), (w - 0.3, y0 + 5.0)]
        fringe: list[Pt] = []
        drips: list[Pt] = []
        if left:
            fringe += [(0.3, y0 + 8.0), (1.8, y0 + 13), (3.4, y0 + 9.5)]
        for i in cells:
            gx = i * step
            lx = gx - x0
            if not lo <= lx <= hi:
                continue
            lip = lip_y(gx)
            ln = 0.6 + (5.0 if muck else 9.0) * _hash(i, 0.7) ** 3.0
            wd = 2.0 + 1.6 * _hash(i, 1.9)
            jit = (_hash(i, 2.3) - 0.5) * 1.4
            fringe.append((lx - step / 2, lip_y(gx - step / 2)))
            if ln < 2.5:
                fringe.append((lx + jit * 0.3, lip + ln))
            else:
                fringe += [(lx - wd * 0.5, lip + 0.6), (lx - wd * 0.22 + jit * 0.3, lip + ln * 0.62), (lx + jit, lip + ln),
                           (lx + wd * 0.22 + jit * 0.3, lip + ln * 0.62), (lx + wd * 0.5, lip + 0.6)]
                if ln > 5.5 and _hash(i, 4.1) > 0.45:
                    drips.append((lx + jit, lip + ln))
        if right:
            fringe += [(w - 3.4, y0 + 9.5), (w - 1.8, y0 + 13), (w - 0.3, y0 + 8.0)]
        back = list(reversed(fringe))
        d = smooth_open(top_pts, 0.8) + f"L{back[0][0]:.2f} {back[0][1]:.2f}" + _curve(back, 0.75) + "Z"
        s.path(smooth_open([(p[0], p[1] + 2.5) for p in fringe], 0.75), stroke="#060404", width=3.2, opacity=0.3)
        s.path(d, fill=s.linear(0, y0 - 3, 0, y0 + 16, [(0, top_c), (0.18, body_c), (0.5, dark_c), (1, deep_c)]))
        edge = shade(deep_c, -0.55)
        s.path(smooth_open(fringe, 0.75), stroke=edge, width=1.1)
        if left:
            s.path(f"M{top_pts[0][0]:.2f} {top_pts[0][1]:.2f} L{fringe[0][0]:.2f} {fringe[0][1]:.2f}", stroke=edge, width=1.2)
        if right:
            s.path(f"M{top_pts[-1][0]:.2f} {top_pts[-1][1]:.2f} L{fringe[-1][0]:.2f} {fringe[-1][1]:.2f}", stroke=edge, width=1.2)
        if slick:
            # glossy wet moss: specular streaks, a water film and beads hanging from the lip
            for k in range(math.floor(x0 / 23.0) - 1, math.ceil((x0 + w) / 23.0) + 1):
                if _hash(k, 13.3) < 0.4:
                    continue
                gx = k * 23.0 + 10 * _hash(k, 13.9) - x0
                wide = 3 + 5 * _hash(k, 14.4)
                if not 3 < gx - 4 and gx + wide + 3 < w:
                    continue
                s.polygon([(gx, y0 + 0.6), (gx + wide, y0 + 0.6), (gx + wide - 4, y0 + 6.5), (gx - 4, y0 + 6.5)], fill="#ffffff", opacity=0.4)
            for tx, ty in drips:
                s.path(f"M{tx - 1.1:.2f} {ty - 1:.2f} Q{tx:.2f} {ty + 2.6:.2f} {tx + 1.1:.2f} {ty - 1:.2f} Z", fill="#d8fff4", stroke="#2a6a60", width=0.4)
            s.path(smooth_open([(x, y + 1.6) for x, y in top_pts], 0.8), stroke="#ffffff", width=1.0, opacity=0.6)
        elif muck:
            for _ in range(max(2, int(w / 18))):
                bx, by = r.uniform(4, w - 4), y0 + r.uniform(1.5, 5.5)
                br = r.uniform(0.8, 2.2)
                s.circle(bx, by, br, fill=dark_c, stroke=rim_c, width=0.5, opacity=0.8)
                s.circle(bx - br * 0.35, by - br * 0.35, br * 0.3, fill="#ffffff", opacity=0.6)
        else:
            # sphagnum cushion texture: little curls and speckles
            curls, specks = [], []
            for _ in range(max(2, int(w / 12))):
                cx = r.uniform(3, w - 3)
                cy = y0 + r.uniform(1.5, 5.0)
                curls.append(f"M{cx - 2:.2f} {cy + 0.7:.2f} Q{cx:.2f} {cy - 1.1:.2f} {cx + 2:.2f} {cy + 0.7:.2f}")
                specks.append(_dot(cx + r.uniform(-4, 4), cy - 1.4, 0.5))
            s.path("".join(curls), stroke=dark_c, width=0.7, opacity=0.6)
            s.path("".join(specks), fill=rim_c, opacity=0.7)
            if drips:
                s.path("".join(_dot(tx, ty + 0.4, 0.75) for tx, ty in drips), fill="#cfe0d8", opacity=0.75)
        # moonlit rim on top
        s.path(smooth_open(top_pts, 0.8), stroke=rim_c, width=1.4, opacity=0.9)
        if muck:
            return
        # life above the surface: sedge tufts, clover leaves, foxfire mushrooms
        blades: dict[str, list[str]] = {c: [] for c in (top_c, body_c, "#a8b870", "#d0c890")}
        for _ in range(max(2, int(w / (24 if slick else 13)))):
            bx = r.uniform(3, w - 3)
            n = r.choice([2, 3, 3, 4])
            for k in range(n):
                sh = r.uniform(3.5, 9.0)
                lean = r.uniform(-2.8, 2.8)
                sx = bx + (k - n / 2) * 0.9
                blades[r.choice(list(blades))].append(
                    f"M{sx - 0.7:.2f} {y0 + 0.5:.2f} Q{sx + lean * 0.3:.2f} {y0 - sh * 0.55:.2f} {sx + lean:.2f} {y0 - sh:.2f} "
                    f"Q{sx + 0.3:.2f} {y0 - sh * 0.45:.2f} {sx + 0.7:.2f} {y0 + 0.5:.2f} Z")
        for color, ds in blades.items():
            if ds:
                s.path("".join(ds), fill=color)
        if slick:
            return
        leaves: dict[str, list[str]] = {top_c: [], body_c: []}
        for _ in range(max(1, int(w / 34))):
            bx = r.uniform(4, w - 4)
            for side in (-1, 1):
                lx, ly = bx + side * 1.6, y0 - 1.2
                leaves[r.choice([top_c, body_c])].append(f"M{lx - 1.6:.2f} {ly:.2f}a1.6 1.1 0 1 0 3.2 0a1.6 1.1 0 1 0 -3.2 0Z")
        for color, ds in leaves.items():
            if ds:
                s.path("".join(ds), fill=color)
        for _ in range(max(1, int(w / 110))):
            mx = r.uniform(10, max(11, w - 24))
            for j in range(r.choice([1, 2, 2, 3])):
                hgt = r.uniform(5.0, 10.5) * (1 - j * 0.22)
                _bell_mushroom(s, mx + j * r.uniform(3.4, 5.0), y0 + 0.5, hgt, hgt * 0.4, r.uniform(-1.4, 1.4), halo=0.5)

    def _keep_wall(self, w: float, h: float, seed: int, left: bool, right: bool, top: bool, x0: float) -> Svg:
        """Mossy old stone of the lantern keep: big ashlar blocks, coping stones, moss drips (world-aligned)."""
        hr = self.terrain_headroom
        s = Svg(w, h + hr)
        y0 = hr
        bottom = y0 + h
        s.rect(0, y0, w, h, fill="#191d19")
        row_h, brick = 26.0, 52.0
        tones = ("#6c7668", "#5e695c", "#4e584c")
        for row in range(int(h / row_h) + 1):
            yy = y0 + 8 + row * row_h
            offset = (row % 2) * brick / 2
            first = math.floor((x0 - offset) / brick)
            idx = first
            gx = first * brick + offset - x0
            # blocks of a row share three tone gradients; highlights, shadows and details are batched per row
            blocks: dict[int, list[str]] = {0: [], 1: [], 2: []}
            lit, low, algae, cracks, tufts = [], [], [], [], []
            while gx < w:
                bx0, bx1 = gx + 1.4, gx + brick - 1.4
                blocks[min(2, int(_hash(idx * 31 + row, 2.2) * 3))].append(rounded_rect_path(bx0, yy + 1.4, bx1 - bx0, row_h - 2.8, 3.0))
                lit.append(f"M{bx0 + 2:.2f} {yy + 3:.2f}L{bx1 - 2:.2f} {yy + 3:.2f}")
                low.append(f"M{bx0 + 2:.2f} {yy + row_h - 2.6:.2f}L{bx1 - 2:.2f} {yy + row_h - 2.6:.2f}")
                v = _hash(idx * 17 + row, 5.9)
                if v < 0.18:  # algae streak running down from the joint above
                    sx = gx + brick * (0.3 + 0.4 * _hash(idx, 6.6))
                    algae.append(f"M{sx - 2:.2f} {yy + 1.6:.2f} Q{sx - 1:.2f} {yy + row_h * 0.6:.2f} {sx:.2f} {yy + row_h - 2:.2f} "
                                 f"Q{sx + 1.4:.2f} {yy + row_h * 0.5:.2f} {sx + 2.4:.2f} {yy + 1.6:.2f} Z")
                elif v < 0.3:  # a crack
                    cx = gx + brick * 0.5
                    cracks.append(f"M{cx - 5:.2f} {yy + 3:.2f} l3 5 l-1 4 l4 5")
                elif v > 0.9:  # a moss tuft in the joint
                    tufts.append(blob(gx + 2, yy + row_h - 1.5, 6, 2.2, 0.3, seed=idx + row))
                gx += brick
                idx += 1
            depth = min(0.5, max(0.0, (yy - y0 - 30) / 360))  # rows darken with depth (no full-size overlay needed)
            for k, ds in blocks.items():
                if ds:
                    c = shade(tones[k], -depth)
                    s.path("".join(ds), fill=s.linear(0, yy, 0, yy + row_h, [(0, c), (1, shade(c, -0.35))]))
            s.path("".join(lit), stroke=KEEP_HI, width=1.0, opacity=0.45)
            s.path("".join(low), stroke="#0e1014", width=1.0, opacity=0.6)
            if algae:
                s.path("".join(algae), fill="#2f4a32", opacity=0.55)
            if cracks:
                s.path("".join(cracks), stroke="#14171c", width=0.9, opacity=0.8)
            if tufts:
                s.path("".join(tufts), fill="#4d6a39", opacity=0.9)
        if left:
            s.rect(0, y0, 5, h, fill=s.linear(0, 0, 5, 0, [(0, "#0a0c10"), (1, "#0a0c10", 0)]))
            s.line(0.7, y0 + 6, 0.7, bottom, INK, 1.4)
        if right:
            s.rect(w - 5, y0, 5, h, fill=s.linear(w - 5, 0, w, 0, [(0, "#0a0c10", 0), (1, "#0a0c10")]))
            s.line(w - 0.7, y0 + 6, w - 0.7, bottom, INK, 1.4)
        if top:
            # coping stones (world-aligned), mossy on top with moss drips down the face
            cope = 36.0
            first = math.floor(x0 / cope) - 1
            stones, glints = [], []
            for i in range(first, math.ceil((x0 + w) / cope) + 1):
                ax, bxx = i * cope - x0 + 0.8, (i + 1) * cope - x0 - 0.8
                if left and bxx < 2:
                    continue
                ax, bxx = (max(ax, 0.6) if left else ax), (min(bxx, w - 0.6) if right else bxx)
                if bxx - ax < 3:
                    continue
                dy = (_hash(i, 3.1) - 0.5) * 0.5
                stones.append(rounded_rect_path(ax, y0 - 0.8 + dy, bxx - ax, 9.5, 2.2))
                glints.append(f"M{ax + 2:.2f} {y0 + 0.4 + dy:.2f}L{bxx - 2:.2f} {y0 + 0.4 + dy:.2f}")
            s.path("".join(stones), fill=s.linear(0, y0 - 1, 0, y0 + 9, [(0, KEEP_HI), (0.35, KEEP), (1, KEEP_DARK)]), stroke=INK, width=1.0)
            s.path("".join(glints), stroke="#c6cfd8", width=1.0, opacity=0.7)
            pads, drips = [], []
            for i in range(math.floor(x0 / 9.0) - 1, math.ceil((x0 + w) / 9.0) + 1):
                if _hash(i, 4.7) < 0.35:
                    continue
                lx = i * 9.0 + 4 * _hash(i, 5.1) - x0
                if not 3 < lx < w - 3:
                    continue
                ln = 3 + 12 * _hash(i, 5.5) ** 2
                pads.append(blob(lx, y0 - 0.4, 5.5, 2.0, 0.3, seed=i))
                if ln > 5:
                    drips.append(f"M{lx - 1.6:.2f} {y0 + 1:.2f} Q{lx:.2f} {y0 + ln:.2f} {lx + 1.6:.2f} {y0 + 1:.2f} Z")
            if drips:
                s.path("".join(drips), fill=MOSS["normal"][2], opacity=0.9)
            if pads:
                s.path("".join(pads), fill=s.linear(0, y0 - 3, 0, y0 + 2, [(0, MOSS["normal"][0]), (1, MOSS["normal"][2])]))
            s.path(f"M0 {y0 - 1:.2f} L{w:.2f} {y0 - 1:.2f}", stroke=MOSS["normal"][4], width=0.8, opacity=0.35)
        return s

    def _cave(self, w: float, h: float, seed: int, left: bool, right: bool, x0: float) -> Svg:
        """Root-cavern earth: dark peat with stones, twisted roots and glowing fungi.
        The rooty rim on top is always drawn (cave floors are often 'covered' by
        the room walls standing on them); thin slabs (ceilings) grow hanging roots."""
        r = Rand(seed)
        hr = self.terrain_headroom
        s = Svg(w, h + hr)
        y0 = hr
        bottom = h + hr
        s.rect(0, y0, w, h, fill=s.linear(0, y0, 0, y0 + min(h, 180), [(0, "#3e3238"), (0.35, "#2a2026"), (1, "#141014")]))
        for k in range(1, 6):
            yy = y0 + 12 + k * 22
            if yy > bottom - 6:
                break
            pts = [(gx - x0, yy + 3 * math.sin(gx * 0.031 + k * 2.1)) for gx in _grid(x0, w, 20.0)]
            s.path(smooth_open(pts), stroke="#0c080a", width=1.6, opacity=0.5 - k * 0.06)
        reach = min(h, 150.0)
        for _ in range(max(2, int(w * reach / 1800))):
            pr = r.uniform(4, 11)
            px = r.uniform(pr * 1.6, w - pr * 1.6)
            py = y0 + 6 + (reach - 12) * r.next() ** 1.5
            fade = max(0.3, 1 - (py - y0) / 160)
            s.path(blob(px, py, pr * 1.5, pr, 0.18, seed=px + py), fill=r.choice(["#3a3036", "#2c2328", "#463a40"]), opacity=0.85 * fade)
            s.path(f"M{px - pr * 1.1:.2f} {py - pr * 0.45:.2f} Q{px - pr * 0.2:.2f} {py - pr * 1.05:.2f} {px + pr * 0.9:.2f} {py - pr * 0.55:.2f}",
                   stroke="#6a5a62", width=0.9, opacity=0.4 * fade)
        if h > 30:
            self._roots(s, w, x0 + 41.0, y0 - 3, bottom, salt=0.5)
        # glowing shelf fungi growing out of the walls (chunk-local, kept inside the chunk)
        for _ in range(max(1, int(w * min(h, 200) / 14000))):
            cx, cy = r.uniform(18, w - 26), r.uniform(y0 + 22, max(y0 + 23, min(bottom - 12, y0 + 170)))
            side = 1 if r.next() < 0.5 else -1
            for j in range(r.choice([2, 3])):
                size = (6.5 - j * 1.6) * (1.0 if cy < y0 + 90 else 0.8)
                bx, by = cx, cy + j * 5.5
                _glow(s, bx + side * size * 0.6, by, size * 1.8, FIRE, 0.4 if cy < y0 + 90 else 0.28)
                s.path(f"M{bx:.2f} {by - size * 0.3:.2f} Q{bx + side * size:.2f} {by - size * 0.55:.2f} {bx + side * size * 1.2:.2f} {by + size * 0.05:.2f} "
                       f"Q{bx + side * size * 0.6:.2f} {by + size * 0.35:.2f} {bx:.2f} {by + size * 0.25:.2f} Z",
                       fill=s.linear(0, by - size * 0.5, 0, by + size * 0.3, [(0, FIRE_HOT), (0.5, FIRE), (1, FIRE_DEEP)]), stroke=INK, width=0.5)
        for side, exposed in ((-1, left), (1, right)):
            if exposed:
                ex = 0.0 if side < 0 else w
                s.rect(min(ex, ex - side * 6), y0, 6, h, fill="#070506", opacity=0.45)
                s.line(ex - side * 0.7, y0 + 4, ex - side * 0.7, bottom, INK, 1.3, 0.8)
        # rooty earth rim with tufts and tiny foxfire caps (world-aligned)
        tops = [(gx - x0, y0 - 0.5 + 0.9 * math.sin(gx * 0.07) + 0.5 * math.sin(gx * 0.21)) for gx in _grid(x0, w, 4.0)]
        lows = [(gx - x0, y0 + 5.0 + 1.4 * math.sin(gx * 0.05 + 1.0) + 1.2 * abs(math.sin(gx * 0.17))) for gx in _grid(x0, w, 4.0)]
        s.path(smooth_open([(x, y + 2.5) for x, y in lows]), stroke="#050304", width=3.0, opacity=0.35)
        s.path(smooth_open(tops) + f"L{lows[-1][0]:.2f} {lows[-1][1]:.2f}" + _curve(list(reversed(lows))) + "Z",
               fill=s.linear(0, y0 - 2, 0, y0 + 8, [(0, "#7a6a5a"), (0.4, "#54463c"), (1, "#2e2420")]))
        s.path(smooth_open(lows), stroke="#0c0809", width=1.0, opacity=0.9)
        s.path(smooth_open([(x, y + 0.7) for x, y in tops]), stroke="#a8967e", width=1.0, opacity=0.6)
        for gx in _grid(x0, w, 11.0, 0):
            i = int(round(gx / 11.0))
            lx = gx - x0
            if not 4 < lx < w - 4:
                continue
            v = _hash(i, 9.1)
            if v > 0.86:
                _bell_mushroom(s, lx, y0 + 0.6, 4.5 + 3 * _hash(i, 9.4), 2.0 + _hash(i, 9.6), 0.4, halo=0.45)
            elif v > 0.55:
                s.path(blob(lx, y0 - 0.2, 4.5, 1.6, 0.3, seed=i), fill=MOSS["normal"][2], opacity=0.9)
        if h <= 100:
            # ceilings: hanging roots with glowing droplets
            for gx in _grid(x0, w, 14.0, 0):
                i = int(round(gx / 14.0))
                lx = gx - x0
                if _hash(i, 21.3) < 0.45 or not 4 < lx < w - 4:
                    continue
                ln = 8 + 18 * _hash(i, 21.7)
                ln = min(ln, h * 0.45)
                pts = [(lx, bottom - ln - 2), (lx + (_hash(i, 22.1) - 0.5) * 6, bottom - ln * 0.5 - 1.5), (lx + (_hash(i, 22.5) - 0.5) * 8, bottom - 1.6)]
                s.path(smooth_open(pts), stroke=ROOT_DARK, width=2.4)
                s.path(smooth_open(pts), stroke=ROOT, width=1.3)
                if _hash(i, 23.3) > 0.5:
                    _glow(s, pts[-1][0], pts[-1][1], 4, FIRE, 0.5)
                    s.circle(pts[-1][0], pts[-1][1], 0.8, fill=FIRE_HOT)
        return s

    def cave_sky(self) -> Svg:
        """Root cavern: huge cypress roots through the vault, foxfire fungi lighting the
        earthen ledges and the roots, glowing root tips and a still pool."""
        s = Svg(960, 540)
        r = Rand(41)
        s.rect(0, 0, 960, 210, fill=s.linear(0, 0, 0, 210, [(0, "#0c0a10"), (1, "#1a151c")]))
        # earthen back wall: layered ledges whose lips catch the fungus light (each band ends under the next ledge)
        for k, (y, color, foot) in enumerate(((165, "#251c22", 345.0), (300, "#2b2125", 470.0), (425, "#1f181b", 540.0))):
            pts = [(x, y + 24 * _wave(x, 960, 2 + k, k) + 10 * _wave(x, 960, 5, k * 2)) for x in [i * 40.0 for i in range(25)]]
            s.path(smooth_open(pts) + f"L960 {foot:.0f} L0 {foot:.0f} Z", fill=color)
            s.path(smooth_open(pts), stroke="#7a8a50", width=1.6, opacity=0.35)
            s.path(smooth_open([(x, yy + 3) for x, yy in pts]), stroke="#3a3034", width=5.0, opacity=0.5)
            for _ in range(10):  # pebbles and strata on the ledge faces
                px = r.uniform(10, 950)
                py = y + 30 + r.uniform(0, 60)
                s.path(blob(px, py, r.uniform(5, 12), r.uniform(3, 6), 0.2, seed=px), fill=shade(color, 0.08), opacity=0.8)
        for cx, cy, rx, ry, a in ((200, 330, 200, 120, 0.14), (520, 420, 230, 100, 0.12), (820, 300, 170, 110, 0.12)):
            _haze(s, cx, cy, rx, ry, "#8ab04a", a)
        # great roots through the vault
        for k, (x, reach, thick) in enumerate(((90, 330, 34), (330, 220, 24), (560, 380, 40), (800, 260, 28), (940, 320, 30))):
            root: list[tuple[float, float, float]] = []
            for j in range(9):
                t = j / 8
                root.append((x + 46 * math.sin(t * 3.0 + k) + 22 * t * (1 if k % 2 else -1), -10 + reach * t, thick * (1 - t) ** 0.7 + 1.5))
            s.path(_vtaper(root), fill=s.linear(x - thick, 0, x + thick, 0, [(0, "#1e1416"), (0.6, "#4a382c"), (1, "#24181a")]))
            wound = [(px + math.sin(j * 1.4 + k) * pt * 0.5, py, max(1.0, pt * 0.35)) for j, (px, py, pt) in enumerate(root[:7])]
            s.path(_vtaper(wound), fill="#33251f")
            s.path(smooth_open([(px + pt * 0.3, py) for px, py, pt in root[:7]]), stroke="#9a7c60", width=1.4, opacity=0.45)
            for j in (3, 5, 6):
                px, py, pt = root[j]
                side = 1 if (j + k) % 2 else -1
                tip = (px + side * 30, py + 70 + 20 * math.sin(j + k))
                s.path(smooth_open([(px, py), (px + side * 20, py + 34), tip]), stroke="#2a1e1c", width=max(1.4, pt * 0.25))
                _glow(s, tip[0], tip[1], 10, FIRE, 0.55)
                s.circle(tip[0], tip[1], 1.5, fill=FIRE_HOT)
            _moss_hang(s, root[2][0], root[2][1], 26, 50, x + k, ("#5a6a50", "#8a9a78"), 0.6)
            # shelf fungi stacked on the side of the root, glowing
            fx, fy, ft = root[4]
            side = 1 if k % 2 else -1
            for j in range(3):
                size = 13 - j * 3.2
                bx, by = fx + side * ft * 0.45, fy - 8 + j * 9
                _glow(s, bx + side * size * 0.6, by, size * 2.0, FIRE, 0.3)
                s.path(f"M{bx:.1f} {by - size * 0.32:.1f} C{bx + side * size * 0.6:.1f} {by - size * 0.6:.1f} {bx + side * size * 1.25:.1f} {by - size * 0.2:.1f} "
                       f"{bx + side * size * 1.25:.1f} {by + size * 0.05:.1f} C{bx + side * size * 1.1:.1f} {by + size * 0.3:.1f} {bx + side * size * 0.5:.1f} "
                       f"{by + size * 0.32:.1f} {bx:.1f} {by + size * 0.26:.1f} Z",
                       fill=s.linear(0, by - size * 0.6, 0, by + size * 0.35, [(0, FIRE_HOT), (0.45, FIRE), (1, FIRE_DEEP)]), stroke="#1a140e", width=0.8)
                s.path(f"M{bx + side * size * 0.2:.1f} {by + size * 0.2:.1f} Q{bx + side * size * 0.7:.1f} {by + size * 0.28:.1f} {bx + side * size * 1.1:.1f} "
                       f"{by + size * 0.08:.1f}", stroke="#4a6a1a", width=0.8, opacity=0.8)
        # glowing mushroom clusters on the ledges
        for x, y, n, scale in ((120, 296, 4, 1.4), (300, 314, 3, 1.1), (470, 430, 5, 1.6), (650, 300, 3, 1.2), (850, 420, 4, 1.5),
                               (210, 440, 3, 1.0), (760, 186, 2, 1.0), (40, 190, 3, 1.0)):
            _glow(s, x + n * 3, y - 8 * scale, 46 * scale, FIRE, 0.26)
            for j in range(n):
                hgt = r.uniform(7, 14) * scale
                _bell_mushroom(s, x + j * 6 * scale, y + 1, hgt, hgt * 0.42, r.uniform(-2, 2), halo=0.35, outline="#0c0a0c")
        # still pool at the bottom reflecting the fungus light
        s.rect(0, 470, 960, 70, fill=s.linear(0, 470, 0, 540, [(0, "#18282a"), (1, "#0a1014")]))
        s.line(0, 470.5, 960, 470.5, "#5a7a6a", 1.2, 0.55)
        for x in (124, 482, 868, 218):
            _haze(s, x, 492, 30, 12, FIRE, 0.3)
        for _ in range(20):
            gx, gy = r.uniform(0, 960), r.uniform(476, 536)
            s.line(gx, gy, gx + r.uniform(10, 50), gy, "#6a9a80", r.uniform(0.6, 1.2), r.uniform(0.2, 0.4))
        # drips and fireflies
        for _ in range(14):
            dx, dy = r.uniform(20, 940), r.uniform(60, 260)
            s.path(f"M{dx:.1f} {dy - 3:.1f} Q{dx + 1.6:.1f} {dy + 1:.1f} {dx:.1f} {dy + 2:.1f} Q{dx - 1.6:.1f} {dy + 1:.1f} {dx:.1f} {dy - 3:.1f} Z",
                   fill="#9ac8c8", opacity=0.5)
        for _ in range(26):
            _firefly(s, r.uniform(10, 950), r.uniform(80, 460), r.uniform(0.8, 1.4))
        return s

    # ------------------------------------------------------------------ interiors
    def interior(self, variant: str):
        """Indoor areas: the sunken manor ("mansion", also "manor") and the lantern
        keep hall ("fortress", also "keep"/"tower"); "cave" uses ``cave_sky``."""
        if variant in ("mansion", "manor"):
            return self._mansion_backdrop, self._mansion_shelves
        if variant in ("fortress", "keep", "tower"):
            return self._keep_hall, self._keep_pillars
        return None

    def _mansion_backdrop(self) -> Svg:
        """Inside the sunken manor: listing walls with peeling damask, crooked abstract
        portraits, candle sconces, a broken stair, a tall moonlit window and a flooded floor."""
        s = Svg(960, 540)
        r = Rand(63)
        with s.group("rotate(-3 480 270)"):
            s.rect(-60, -60, 1080, 560, fill="#231c2e")
            # damask wallpaper: stripes with moth-and-leaf motifs (original)
            stripes, seams, motifs, dots = [], [], [], []
            for i in range(-2, 26):
                x = i * 44.0
                stripes.append(f"M{x:.1f} -60h22v460h-22Z")
                seams.append(f"M{x + 22:.1f} -60V400")
                for j in range(9):
                    cy = -30 + j * 58 + (i % 2) * 29
                    cx = x + 33
                    motifs.append(f"M{cx:.1f} {cy - 9:.1f} Q{cx + 7:.1f} {cy - 4:.1f} {cx + 6:.1f} {cy:.1f} Q{cx + 9:.1f} {cy + 6:.1f} {cx:.1f} {cy + 10:.1f} "
                                  f"Q{cx - 9:.1f} {cy + 6:.1f} {cx - 6:.1f} {cy:.1f} Q{cx - 7:.1f} {cy - 4:.1f} {cx:.1f} {cy - 9:.1f} Z")
                    dots.append(_dot(cx, cy, 1.6))
            s.path("".join(stripes), fill="#2f263c", opacity=0.6)
            s.path("".join(seams), stroke="#3e3250", width=1.0, opacity=0.5)
            s.path("".join(motifs), fill="#3a2f4c", opacity=0.75)
            s.path("".join(dots), fill="#4e4064", opacity=0.8)
            # torn wallpaper: plaster and brick showing through, a curled flap of paper
            for px, py, pw, ph in ((120, 70, 70, 50), (610, 40, 60, 44), (860, 200, 50, 70), (340, 250, 46, 30)):
                pts = [(px + pw * (0.5 + 0.5 * math.cos(a)) * r.uniform(0.85, 1.1), py + ph * (0.5 + 0.5 * math.sin(a)) * r.uniform(0.85, 1.1))
                       for a in [k * math.pi / 5 for k in range(10)]]
                s.path(smooth_closed(pts, 0.6), fill="#4e434a", stroke="#1a1218", width=1.2)
                for row in range(int(ph / 9)):
                    off = (row % 2) * 7
                    for col in range(int(pw / 14) + 1):
                        bx, by = px + 4 + col * 14 - off, py + 5 + row * 9
                        if px + 3 < bx and bx + 11 < px + pw - 3 and r.next() < 0.7:
                            s.rect(bx, by, 11, 6.5, fill="#5e3a36", rx=1.2, opacity=0.8)
                fx, fy = pts[0]
                s.path(f"M{fx:.1f} {fy:.1f} q10 -2 13 8 q-7 -1 -13 -8 Z", fill="#6a5a78", stroke="#1a1218", width=0.8)
            # water stains and the flood line
            s.rect(-60, 360, 1080, 120, fill=s.linear(0, 360, 0, 480, [(0, "#1a2a2a", 0), (0.5, "#1a2a2a", 0.4), (1, "#0e1818", 0.7)]))
            s.line(-60, 392, 1020, 392, "#3a5050", 2.0, 0.4)
            # wainscot
            s.rect(-60, 398, 1080, 90, fill=s.linear(0, 398, 0, 488, [(0, "#2e2026"), (1, "#1a1216")]))
            s.rect(-60, 394, 1080, 8, fill="#3e2c30")
            s.line(-60, 394.5, 1020, 394.5, "#6a5258", 1.2, 0.6)
            for i in range(-1, 14):
                s.path(rounded_rect_path(i * 80 + 10, 412, 62, 60, 4), stroke="#120c10", width=2.0, opacity=0.7)
            # the tall moonlit window
            wx, wy, ww, wh = 600.0, 60.0, 170.0, 300.0
            s.path(f"M{wx} {wy + wh} L{wx} {wy + 80} Q{wx + ww / 2} {wy - 30} {wx + ww} {wy + 80} L{wx + ww} {wy + wh} Z",
                   fill=s.linear(0, wy, 0, wy + wh, [(0, "#1c2a5a"), (0.6, "#2c5a78"), (1, "#3e7a80")]))
            _glow(s, wx + 110, wy + 110, 70, "#e8ecff", 0.35)
            s.circle(wx + 110, wy + 110, 32, fill=s.radial(wx + 98, wy + 98, 44, [(0, "#ffffff"), (0.6, MOON), (1, MOON_SHADE)]))
            s.path(f"M{wx} {wy + wh - 30} Q{wx + 50} {wy + wh - 70} {wx + 90} {wy + wh - 44} Q{wx + 130} {wy + wh - 80} {wx + ww} {wy + wh - 40} "
                   f"L{wx + ww} {wy + wh} L{wx} {wy + wh} Z", fill="#141a34")
            _dead_tree(s, wx + 40, wy + wh - 36, 70, 3.0, "#141a34")
            for k in range(3):
                mullion = wx + ww * (k + 1) / 4
                s.line(mullion, wy + (40 if k == 1 else 52), mullion, wy + wh, "#100c14", 4.0)
            for yy in (wy + 140, wy + 220):
                s.line(wx, yy, wx + ww, yy, "#100c14", 4.0)
            s.path(f"M{wx} {wy + wh} L{wx} {wy + 80} Q{wx + ww / 2} {wy - 30} {wx + ww} {wy + 80} L{wx + ww} {wy + wh} Z", stroke="#2a1c22", width=12)
            s.path(f"M{wx + 106} {wy + 150} L{wx + 128} {wy + 172} L{wx + 112} {wy + 196} L{wx + 136} {wy + 214}", stroke="#d8e0ff", width=1.0, opacity=0.6)
            s.rect(wx - 16, wy + wh, ww + 32, 12, fill="#3e2c30", rx=2)
            s.polygon([(wx + 10, wy + wh + 10), (wx + ww - 10, wy + wh + 10), (wx + ww + 90, 540), (wx - 40, 540)], fill="#c8d4ff", opacity=0.06)
            # crooked portraits with abstract scenes (no faces)
            for k, (px, py, pw, ph, tilt) in enumerate(((150, 150, 70, 90, -7), (300, 110, 56, 70, 5), (420, 200, 80, 60, -4), (860, 120, 60, 80, 9))):
                with s.group(f"rotate({tilt} {px + pw / 2:.1f} {py:.1f})"):
                    s.line(px + pw / 2, py - 26, px + 8, py, "#6a5a40", 1.2)
                    s.line(px + pw / 2, py - 26, px + pw - 8, py, "#6a5a40", 1.2)
                    s.rect(px - 6, py - 6, pw + 12, ph + 12, fill=s.linear(px, py, px + pw, py + ph, [(0, "#c8a056"), (0.5, "#7a5a2a"), (1, "#4a3418")]),
                           stroke="#1a1208", width=1.2, rx=2)
                    pal = [("#2a3a4a", "#4a6a6a"), ("#3a2a3a", "#7a5a6a"), ("#2a3a2a", "#5a7a4a"), ("#2a2a44", "#6a6a9a")][k]
                    s.rect(px, py, pw, ph, fill=s.linear(0, py, 0, py + ph, [(0, pal[0]), (1, pal[1])]))
                    if k == 0:  # a moonlit hill
                        s.circle(px + pw * 0.7, py + ph * 0.3, 8, fill="#e8e0c0", opacity=0.8)
                        s.path(f"M{px} {py + ph} Q{px + pw * 0.4} {py + ph * 0.5} {px + pw} {py + ph * 0.8} L{px + pw} {py + ph} Z", fill="#1a2420")
                    elif k == 1:  # a vase of reeds
                        s.path(f"M{px + pw * 0.38} {py + ph - 6} Q{px + pw * 0.3} {py + ph * 0.6} {px + pw / 2} {py + ph * 0.55} "
                               f"Q{px + pw * 0.7} {py + ph * 0.6} {px + pw * 0.62} {py + ph - 6} Z", fill="#c8b07a", opacity=0.85)
                        for j in range(4):
                            s.line(px + pw / 2, py + ph * 0.55, px + pw * (0.3 + j * 0.13), py + 8 + (j % 2) * 6, "#2a3a26", 1.4)
                    elif k == 2:  # geometric rings
                        for j in range(3):
                            s.circle(px + pw / 2, py + ph / 2, 8 + j * 7, stroke="#c8b07a", width=1.4, opacity=0.6)
                    else:  # a sailboat on calm water
                        s.path(f"M{px + 14} {py + ph * 0.66} L{px + pw - 14} {py + ph * 0.66} L{px + pw - 20} {py + ph * 0.76} L{px + 20} {py + ph * 0.76} Z",
                               fill="#3a2a20")
                        s.polygon([(px + pw / 2, py + 12), (px + pw / 2, py + ph * 0.64), (px + pw * 0.75, py + ph * 0.64)], fill="#e0d8c0", opacity=0.85)
                    s.rect(px, py, pw, ph, fill="#000000", opacity=0.18)
            # candle sconces (warm: the safe light inside the manor)
            for cx, cy in ((90, 260), (520, 250), (900, 300)):
                _glow(s, cx, cy - 18, 60, GLOW, 0.4)
                s.path(f"M{cx - 20} {cy} Q{cx} {cy + 14} {cx + 20} {cy}", stroke="#8a7044", width=2.4)
                s.line(cx, cy + 6, cx, cy + 22, "#8a7044", 3.0)
                for dx in (-18, 0, 18):
                    s.rect(cx + dx - 2.5, cy - 12 - (4 if dx == 0 else 0), 5, 12 + (4 if dx == 0 else 0), fill="#efe6d0", stroke="#5a4a30", width=0.6)
                    fy = cy - 14 - (4 if dx == 0 else 0)
                    s.path(f"M{cx + dx:.1f} {fy - 7:.1f} Q{cx + dx + 2.6:.1f} {fy - 2:.1f} {cx + dx:.1f} {fy:.1f} Q{cx + dx - 2.6:.1f} {fy - 2:.1f} "
                           f"{cx + dx:.1f} {fy - 7:.1f} Z", fill=s.linear(0, fy - 7, 0, fy, [(0, GLOW_HOT), (1, GLOW_DEEP)]))
            # a broken staircase climbing to a gallery
            for k in range(9):
                sx, sy = 160 + k * 26, 470 - k * 20
                if k in (4, 6):
                    continue
                s.rect(sx, sy, 34, 8, fill="#3a2a2c", stroke="#140c0e", width=1.0)
                s.line(sx + 2, sy + 1.5, sx + 32, sy + 1.5, "#6a5054", 1.0, 0.6)
            s.path("M160 470 L404 290 L410 300 L170 480 Z", fill="#24181c")
            for k in range(0, 9, 2):
                bx, by = 168 + k * 26, 462 - k * 20
                s.line(bx, by, bx, by - 34, "#4a3438", 2.0)
            s.path("M168 428 L282 342 M330 306 L376 272", stroke="#4a3438", width=3.0)
            s.rect(400, 286, 200, 10, fill="#3a2a2c", stroke="#140c0e", width=1.0)
            # unlit tilted chandelier
            with s.group("rotate(8 300 0)"):
                s.line(300, -20, 300, 60, "#3a3030", 2.0)
                s.path("M250 62 Q300 90 350 62", stroke="#5a4a3a", width=3.0)
                for dx in (-50, -25, 0, 25, 50):
                    s.rect(300 + dx - 2, 52 + abs(dx) * 0.2, 4, 10, fill="#cfc6b0")
                _moss_hang(s, 300, 64, 40, 30, 7.0, ("#5a6058", "#8a9080"), 0.5)
            # cobwebs in the corners
            for cx, cy, sx in ((40, 20, 1), (1000, 20, -1)):
                for k in range(5):
                    a = math.radians(5 + k * 20)
                    s.line(cx, cy, cx + sx * math.cos(a) * 90, cy + math.sin(a) * 90, "#9a98a8", 0.7, 0.4)
                for rr in (24, 44, 66):
                    pts = [(cx + sx * math.cos(math.radians(5 + k * 20)) * rr, cy + math.sin(math.radians(5 + k * 20)) * rr) for k in range(5)]
                    s.path(smooth_open(pts, 0.4), stroke="#9a98a8", width=0.6, opacity=0.4)
        # flooded floor in front of the wainscot
        s.rect(0, 486, 960, 54, fill=s.linear(0, 486, 0, 540, [(0, "#16262a"), (1, "#0a1012")]))
        s.line(0, 486.5, 960, 486.5, "#5a7a7a", 1.2, 0.5)
        for x in (90, 520, 900):
            _haze(s, x, 504, 30, 10, GLOW, 0.3)
        _haze(s, 690, 508, 60, 12, "#c8d4ff", 0.2)
        for _ in range(16):
            gx, gy = r.uniform(0, 960), r.uniform(492, 536)
            s.line(gx, gy, gx + r.uniform(12, 50), gy, "#6a8a8a", 1.0, 0.3)
        return s

    def _mansion_shelves(self) -> Svg:
        """Scrolling layer of the manor: leaning bookshelves between fluted columns (tiles at 900)."""
        s = Svg(900, 420)
        r = Rand(67)
        for k, x in enumerate((40.0, 490.0)):
            # bookshelf
            with s.group(f"rotate({-2.5 if k == 0 else 2.0} {x + 100:.1f} 420)"):
                s.rect(x, 90, 200, 330, fill=s.linear(x, 0, x + 200, 0, [(0, "#1e1416"), (0.5, "#2e2022"), (1, "#181012")]), stroke="#0e0806", width=2)
                s.rect(x - 8, 82, 216, 12, fill="#4a3226", stroke="#0e0806", width=1.2)
                for row in range(5):
                    yy = 110 + row * 60
                    s.rect(x + 8, yy + 46, 184, 6, fill="#4a3226")
                    bx = x + 10
                    while bx < x + 186:
                        bw = r.uniform(7, 13)
                        bh = r.uniform(30, 44)
                        lean = 0.0 if r.next() < 0.8 else r.uniform(-12, 12)
                        color = r.choice(["#46262c", "#26323e", "#323a26", "#463c28", "#30263e", "#4e4438"])
                        with s.group(f"rotate({lean:.1f} {bx + bw / 2:.1f} {yy + 46:.1f})"):
                            s.rect(bx, yy + 46 - bh, bw, bh, fill=color, stroke="#120a08", width=0.6)
                            s.line(bx + 1.2, yy + 46 - bh + 4, bx + bw - 1.2, yy + 46 - bh + 4, "#c8a868", 0.8, 0.6)
                        bx += bw + 0.8
                        if r.next() < 0.08:
                            bx += 18
                    if row == 2:
                        _bell_mushroom(s, x + 150, yy + 46, 9, 4, 0.5, halo=0.4)
                _moss_hang(s, x + 40, 94, 40, 40, x, ("#4a5248", "#7a8270"), 0.5)
            s.rect(x - 10, 300, 230, 120, fill=s.linear(0, 300, 0, 420, [(0, "#0a0610", 0), (1, "#0a0610", 0.55)]))
            # column
            cx = x + 300
            s.rect(cx - 22, 40, 44, 380, fill=s.linear(cx - 22, 0, cx + 22, 0, [(0, "#2e2832"), (0.4, "#4a4250"), (1, "#1c1820")]))
            for fx in (-12, -4, 4, 12):
                s.line(cx + fx, 70, cx + fx, 400, "#1a161e", 1.6, 0.7)
            s.rect(cx - 30, 30, 60, 16, fill="#3e3846", stroke="#120e14", width=1.2)
            s.rect(cx - 30, 404, 60, 16, fill="#3e3846", stroke="#120e14", width=1.2)
            s.path(blob(cx - 10, 47, 18, 4, 0.3, seed=cx), fill="#3a4a34", opacity=0.8)
        return s

    def _keep_hall(self) -> Svg:
        """Lantern keep hall: dark mossy masonry, moonlit arched windows, hanging chains,
        green-flame braziers and the counterweight wheel of the great lantern."""
        s = Svg(960, 540)
        s.rect(0, 0, 960, 540, fill=s.linear(0, 0, 0, 540, [(0, "#0e1016"), (0.6, "#1a1e26"), (1, "#101218")]))
        for row in range(13):
            y = row * 44
            off = (row % 2) * 60
            for col in range(-1, 9):
                x = col * 120 + off
                tone = _hash(row * 13 + col, 1.3)
                s.rect(x + 2, y + 2, 116, 40, fill=mix("#262b34", "#323844", tone), rx=3)
                s.line(x + 4, y + 4, x + 114, y + 4, "#434a58", 1.2, 0.5)
                if _hash(row * 7 + col, 2.9) < 0.15:
                    s.path(blob(x + 30, y + 40, 22, 4, 0.3, seed=x + y), fill="#2c4030", opacity=0.8)
        for ax in (150.0, 480.0, 810.0):
            s.path(f"M{ax - 56} 360 L{ax - 56} 170 Q{ax} 86 {ax + 56} 170 L{ax + 56} 360 Z",
                   fill=s.linear(0, 100, 0, 360, [(0, "#1a2250"), (0.7, "#2a4a6a"), (1, "#3a6070")]), stroke="#0a0c10", width=7)
            if ax == 480.0:
                s.circle(ax + 14, 186, 26, fill=s.radial(ax + 6, 178, 34, [(0, "#ffffff"), (0.6, MOON), (1, MOON_SHADE)]))
                _glow(s, ax + 14, 186, 60, "#e8ecff", 0.3)
            s.path(f"M{ax - 56} 330 Q{ax - 20} 300 {ax + 10} 318 Q{ax + 36} 334 {ax + 56} 312 L{ax + 56} 360 L{ax - 56} 360 Z", fill="#121830")
            s.line(ax, 104, ax, 360, "#0a0c10", 4.0)
            s.line(ax - 56, 250, ax + 56, 250, "#0a0c10", 4.0)
            s.rect(ax - 74, 360, 148, 14, fill="#2a2e38", rx=3)
            s.polygon([(ax - 40, 372), (ax + 40, 372), (ax + 130, 540), (ax - 130, 540)], fill="#c8d4ff", opacity=0.05)
        # counterweight wheel of the great lantern
        cx, cy = 315.0, 120.0
        s.circle(cx, cy, 64, stroke="#2c2a30", width=10)
        for k in range(8):
            a = k * math.pi / 4
            s.line(cx, cy, cx + math.cos(a) * 60, cy + math.sin(a) * 60, "#2c2a30", 5)
        s.circle(cx, cy, 12, fill="#3a3640", stroke="#0e0c10", width=2)
        for k in range(12):
            a = k * math.pi / 6
            s.rect(cx + math.cos(a) * 68 - 4, cy + math.sin(a) * 68 - 4, 8, 8, fill="#2c2a30")
        # chains
        for x, length in ((60, 300), (250, 220), (380, 180), (640, 260), (900, 320)):
            for k in range(int(length / 14)):
                y = k * 14
                if k % 2 == 0:
                    s.ellipse(x, y + 7, 4, 7, stroke="#3e3c46", width=2.2)
                else:
                    s.line(x, y + 1, x, y + 13, "#3e3c46", 3.0)
            s.path(f"M{x - 8} {length} L{x + 8} {length} L{x} {length + 14} Z", fill="#3e3c46")
        # green-flame braziers along the hall
        for bx in (315.0, 645.0):
            by = 400.0
            _glow(s, bx, by - 40, 90, "#5aff8c", 0.25)
            s.polygon([(bx - 8, 540), (bx - 4, by + 6), (bx + 4, by + 6), (bx + 8, 540)], fill=s.linear(bx - 8, 0, bx + 8, 0, [(0, IRON_HI), (1, IRON_DEEP)]))
            s.path(f"M{bx - 22} {by - 10} L{bx + 22} {by - 10} L{bx + 16} {by + 6} Q{bx} {by + 10} {bx - 16} {by + 6} Z",
                   fill=s.linear(bx - 22, 0, bx + 22, 0, [(0, IRON_HI), (0.5, IRON), (1, IRON_DEEP)]), stroke="#0a0a0e", width=1.4)
            self._green_flame(s, bx, by - 10, 30, 44, bx)
        s.rect(0, 500, 960, 40, fill=s.linear(0, 500, 0, 540, [(0, "#000000", 0), (1, "#000000", 0.4)]))
        return s

    def _green_flame(self, s: Svg, cx: float, base: float, w: float, h: float, seed: float) -> None:
        """Eerie green brazier flame: layered tongues with a pale core."""
        for k, scale in enumerate((1.0, 0.7, 0.42)):
            fw, fh = w * scale, h * scale
            pts = [(cx - fw * 0.5, base)]
            for i in range(3):
                tx = cx - fw * 0.5 + fw * (i + 0.5) / 3 + math.sin(seed + i * 2.1 + k) * fw * 0.06
                peak = fh * (0.6 + 0.4 * (1 - abs(i - 1)))
                pts += [(tx - fw * 0.12, base - peak * 0.55), (tx + math.sin(seed * 1.7 + i) * fw * 0.08, base - peak), (tx + fw * 0.12, base - peak * 0.55)]
            pts += [(cx + fw * 0.5, base), (cx, base + fh * 0.06)]
            s.path(smooth_closed(pts, 0.55), fill=s.linear(0, base - fh, 0, base, [(0, GREEN_FLAME[3 - k][1], 0.35), (0.5, GREEN_FLAME[2 - k][1]),
                                                                                   (1, GREEN_FLAME[max(0, 1 - k)][1])]))

    def _keep_pillars(self) -> Svg:
        """Scrolling keep layer: stone piers with green-flame sconces and hanging chains (tiles at 900)."""
        s = Svg(900, 420)
        for x in (90.0, 540.0):
            s.rect(x, 20, 76, 400, fill=s.linear(x, 0, x + 76, 0, [(0, "#2a2e38"), (0.4, "#424856"), (1, "#181b22")]), rx=4)
            for y in range(46, 420, 44):
                s.line(x, y, x + 76, y, "#101216", 2.0, 0.8)
            s.path(blob(x + 30, 22, 40, 6, 0.3, seed=x), fill="#34482e", opacity=0.9)
            for k in range(5):
                s.path(f"M{x + 8 + k * 15:.1f} 24 q1.5 {6 + k * 3:.1f} 0 {12 + k * 4:.1f}", stroke="#34482e", width=2.0)
            _glow(s, x + 38, 170, 50, "#5aff8c", 0.4)
            s.path(f"M{x + 22} 180 L{x + 54} 180 L{x + 47} 196 L{x + 29} 196 Z", fill=IRON_DARK, stroke=INK, width=1.4)
            self._green_flame(s, x + 38, 180, 24, 34, x)
            for cx in (x - 30, x + 110):
                for k in range(12):
                    y = 20 + k * 12
                    if k % 2 == 0:
                        s.ellipse(cx, y + 6, 3.4, 6, stroke="#3e3c46", width=2.0)
                    else:
                        s.line(cx, y + 1, cx, y + 11, "#3e3c46", 2.6)
        return s

    def gate(self, w: float, h: float) -> Svg:
        """Arena gate: wrought iron with scrollwork, spear tips and a lantern crest."""
        s = Svg(w, h)
        s.rect(0, 0, w, h, fill=s.linear(0, 0, 0, h, [(0, "#14161c", 0.85), (1, "#0a0b0e", 0.85)]), rx=2)
        n = max(2, int(w // 9) + 1)
        for i in range(n):
            x = 2.4 + i * (w - 4.8) / max(1, n - 1)
            s.rect(x - 1.5, 2, 3.0, h - 8, fill=s.linear(x - 1.5, 0, x + 1.5, 0, [(0, IRON_HI), (1, IRON_DEEP)]), rx=1)
            s.polygon([(x - 2.6, h - 7), (x, h), (x + 2.6, h - 7)], fill=s.linear(0, h - 7, 0, h, [(0, IRON_HI), (1, IRON_DARK)]), stroke=INK, width=0.6)
        for y in (6.0, h * 0.52, h - 12):
            s.rect(0, y, w, 4, fill=s.linear(0, y, 0, y + 4, [(0, IRON_HI), (1, IRON_DARK)]), stroke=INK, width=0.7, rx=1.5)
        # scrollwork between the rails
        for i in range(n - 1):
            x0 = 2.4 + i * (w - 4.8) / max(1, n - 1)
            x1 = 2.4 + (i + 1) * (w - 4.8) / max(1, n - 1)
            mx = (x0 + x1) / 2
            for yy in (h * 0.52 + 12, h - 30):
                s.path(f"M{x0:.2f} {yy:.2f} Q{mx:.2f} {yy - 10:.2f} {mx:.2f} {yy - 3:.2f} Q{mx - 2.5:.2f} {yy + 1:.2f} {mx - 3:.2f} {yy - 3:.2f}",
                       stroke=IRON, width=1.2)
                s.path(f"M{x1:.2f} {yy:.2f} Q{mx:.2f} {yy + 10:.2f} {mx:.2f} {yy + 3:.2f} Q{mx + 2.5:.2f} {yy - 1:.2f} {mx + 3:.2f} {yy + 3:.2f}",
                       stroke=IRON, width=1.2)
        # lantern crest
        cx, cy = w / 2, min(h * 0.3, 44.0)
        rad = min(w * 0.42, 15.0)
        _glow(s, cx, cy, rad * 1.8, GLOW, 0.5)
        s.circle(cx, cy, rad, fill=s.radial(cx, cy, rad, [(0, "#2a2018"), (1, "#141016")]), stroke=IRON_HI, width=2.0)
        s.circle(cx, cy, rad - 2.6, stroke=IRON_DARK, width=1.0)
        _hang_lantern(s, cx, cy - rad * 0.72, rad * 1.1, True, 0.0)
        for k in range(8):
            a = k * math.pi / 4
            s.line(cx + math.cos(a) * (rad + 1), cy + math.sin(a) * (rad + 1), cx + math.cos(a) * (rad + 4), cy + math.sin(a) * (rad + 4), IRON_HI, 1.2)
        for k in range(4):  # rust running down from the rails
            rx, ry = 3 + (k * 13) % max(4.0, w - 6), h * 0.52 + 4 if k % 2 else 10.0
            s.path(f"M{rx - 0.8:.2f} {ry:.2f} Q{rx:.2f} {ry + 9:.2f} {rx + 0.3:.2f} {ry + 14:.2f} Q{rx + 0.9:.2f} {ry + 7:.2f} {rx + 1.1:.2f} {ry:.2f} Z",
                   fill=RUST, opacity=0.55)
        s.path(blob(w * 0.3, 2.5, w * 0.25, 2.4, 0.3, seed=w), fill=MOSS["normal"][1], opacity=0.9)
        return s

    # ------------------------------------------------------------------ blocks and platforms
    def block(self, kind: str, w: float, h: float) -> Svg:
        s = Svg(w, h)
        if kind in ("question", "used"):
            self._lantern_box(s, w, h, kind == "used")
        elif kind == "brick":
            self._mossy_bricks(s, w, h)
        return s

    def _rune(self, s: Svg, cx: float, cy: float, size: float, lit: bool) -> None:
        """Lantern rune (original glyph): a crescent cradling a flame drop, with two sparks."""
        k = size
        crescent = (f"M{cx + k * 0.15:.2f} {cy - k * 0.95:.2f} A{k:.2f} {k:.2f} 0 1 0 {cx + k * 0.15:.2f} {cy + k * 0.95:.2f} "
                    f"A{k * 0.78:.2f} {k * 0.78:.2f} 0 1 1 {cx + k * 0.15:.2f} {cy - k * 0.95:.2f} Z")
        fx, fy = cx + k * 0.12, cy + k * 0.1
        flame = (f"M{fx:.2f} {fy - k * 0.72:.2f} Q{fx + k * 0.42:.2f} {fy - k * 0.08:.2f} {fx + k * 0.24:.2f} {fy + k * 0.3:.2f} "
                 f"Q{fx:.2f} {fy + k * 0.5:.2f} {fx - k * 0.24:.2f} {fy + k * 0.3:.2f} Q{fx - k * 0.42:.2f} {fy - k * 0.08:.2f} {fx:.2f} {fy - k * 0.72:.2f} Z")
        if lit:
            s.path(crescent, fill="#fff8e0", stroke="#a85a14", width=k * 0.12)
            s.path(flame, fill=s.radial(fx, fy, k * 0.6, [(0, "#ffffff"), (0.6, "#fff2b0"), (1, "#ffd05a")]), stroke="#a85a14", width=k * 0.1)
            for dx, dy in ((0.72, -0.62), (0.9, -0.2)):
                s.polygon(star_points(cx + k * dx, cy + k * dy, k * 0.2, k * 0.06, 4), fill="#ffffff")
        else:
            s.path(crescent, fill="#2e3646", stroke="#56627a", width=k * 0.1)
            s.path(flame, fill="#232a38", stroke="#56627a", width=k * 0.08)

    def _lantern_box(self, s: Svg, w: float, h: float, used: bool) -> None:
        """Reward block: an old lantern-box — dark wood frame, iron corners, a glowing
        glass panel with the lantern rune (used: cold glass, dark rune, a cobweb)."""
        wood = [(0, "#8a6a4e"), (0.5, "#5a4232"), (1, "#30231a")] if not used else [(0, "#625a56"), (0.5, "#433d3a"), (1, "#26221f")]
        s.path(rounded_rect_path(0.6, 0.6, w - 1.2, h - 1.2, 3.6), fill=s.linear(0, 0, 0, h, wood), stroke=INK, width=1.3)
        s.path(f"M3.5 2.2 L{w - 3.5:.2f} 2.2", stroke="#c8a888" if not used else "#8a827c", width=0.9, opacity=0.7)
        for gy in (h * 0.3, h * 0.72):
            s.path(f"M2.4 {gy:.2f} Q{w * 0.3:.2f} {gy + 0.8:.2f} {w * 0.5:.2f} {gy - 0.3:.2f}", stroke="#2a1c14", width=0.6, opacity=0.5)
        px, py = 6.4, 4.6
        pw, ph = w - 2 * px, h - 2 * py
        glass = [(0, GLOW_HOT), (0.4, GLOW), (1, GLOW_DEEP)] if not used else [(0, "#4a5872"), (0.6, "#2a3348"), (1, "#181e2c")]
        s.path(rounded_rect_path(px, py, pw, ph, 2.6), fill=s.radial(w / 2, h / 2, max(pw, ph) * 0.75, glass), stroke="#1a120c", width=1.0)
        if not used:
            s.path(rounded_rect_path(px + 1.2, py + 1.2, pw - 2.4, ph - 2.4, 2.0), stroke="#fff8e0", width=0.7, opacity=0.6)
        else:
            s.path(f"M{px + 2:.2f} {py + ph - 2:.2f} L{px + pw * 0.45:.2f} {py + 2:.2f}", stroke="#8a98b8", width=0.7, opacity=0.4)
        for bx in (px + pw * 0.2, px + pw * 0.8):
            s.line(bx, py + 0.6, bx, py + ph - 0.6, "#2a1c14" if not used else "#141820", 1.1, 0.75)
        self._rune(s, w / 2 - 0.5, h / 2, min(pw * 0.28, ph * 0.42), not used)
        # iron corner plates with rivets
        for qx, qy, sx, sy in ((0.6, 0.6, 1, 1), (w - 0.6, 0.6, -1, 1), (0.6, h - 0.6, 1, -1), (w - 0.6, h - 0.6, -1, -1)):
            pts = [(qx, qy), (qx + sx * 7.5, qy), (qx + sx * 7.5, qy + sy * 2.6), (qx + sx * 2.6, qy + sy * 2.6), (qx + sx * 2.6, qy + sy * 6.5),
                   (qx, qy + sy * 6.5)]
            s.polygon(pts, fill=s.linear(qx, qy, qx + sx * 7, qy + sy * 7, [(0, IRON_HI), (1, IRON_DARK)]), stroke=INK, width=0.6)
            s.circle(qx + sx * 1.6, qy + sy * 1.6, 0.8, fill="#d8dce6" if not used else "#8a8e98")
        if used:
            cx, cy = 1.6, 1.6
            for k in range(4):
                a = math.radians(8 + k * 25)
                s.line(cx, cy, cx + math.cos(a) * 9, cy + math.sin(a) * 9, "#c8ccd8", 0.35, 0.6)
            for rr in (3.5, 6.5):
                pts = [(cx + math.cos(math.radians(8 + k * 25)) * rr, cy + math.sin(math.radians(8 + k * 25)) * rr) for k in range(4)]
                s.path(smooth_open(pts, 0.4), stroke="#c8ccd8", width=0.35, opacity=0.6)
        else:
            s.path(blob(w * 0.74, 1.4, 5.5, 1.6, 0.3, seed=w + h), fill=MOSS["normal"][1])
            s.path(f"M{w * 0.72:.2f} 2.2 q0.4 2.4 -0.3 4.2", stroke=MOSS["normal"][2], width=0.9)

    def _mossy_bricks(self, s: Svg, w: float, h: float) -> None:
        """Mossy old manor stone (breakable): algae streaks, chipped corners, moss on top."""
        r = Rand(int(w * 11 + h))
        s.path(rounded_rect_path(0.6, 0.6, w - 1.2, h - 1.2, 3), fill="#1a1e1c", stroke=INK, width=1.2)
        rows = 2
        rh = (h - 2) / rows
        tones = [("#7c877a", "#454e43"), ("#717d72", "#3e4a40"), ("#868c7e", "#4c5246")]
        for row in range(rows):
            y = 1 + row * rh
            x = -(0 if row % 2 == 0 else 10.0)
            i = 0
            while x < w:
                bx0, bx1 = max(1.4, x + 1.1), min(w - 1.4, x + 20 - 1.1)
                if bx1 > bx0 + 2:
                    t0, t1 = tones[(row * 2 + i) % 3]
                    s.path(rounded_rect_path(bx0, y + 1.0, bx1 - bx0, rh - 2.0, 1.8), fill=s.linear(0, y, 0, y + rh, [(0, t0), (1, t1)]),
                           stroke="#20261f", width=0.7)
                    s.line(bx0 + 1, y + 2.1, bx1 - 1, y + 2.1, "#c8d4c0", 0.8, 0.55)
                    if r.next() < 0.4:  # algae streak
                        sx = r.uniform(bx0 + 2, bx1 - 2)
                        s.path(f"M{sx - 1.2:.2f} {y + 1.4:.2f} Q{sx:.2f} {y + rh * 0.7:.2f} {sx + 0.4:.2f} {y + rh - 1.5:.2f} Q{sx + 1:.2f} {y + rh * 0.5:.2f} "
                               f"{sx + 1.4:.2f} {y + 1.4:.2f} Z", fill="#2f4a2c", opacity=0.55)
                    if r.next() < 0.25:
                        cx = bx0 if r.next() < 0.5 else bx1
                        sgn = 1 if cx == bx0 else -1
                        s.polygon([(cx, y + 1.2), (cx + sgn * 3.0, y + 1.2), (cx, y + 3.2)], fill="#20261f")
                x += 20
                i += 1
        pts = [(x, 1.3 + 0.9 * math.sin(x * 0.4 + w)) for x in [i * w / 14 for i in range(15)]]
        lip = [(x, 3.8 + 1.3 * math.sin(x * 0.55 + h)) for x in reversed([i * w / 14 for i in range(15)])]
        s.path(smooth_open(pts) + f"L{lip[0][0]:.2f} {lip[0][1]:.2f}" + _curve(lip) + "Z",
               fill=s.linear(0, 0, 0, 5, [(0, MOSS["normal"][0]), (1, MOSS["normal"][2])]), opacity=0.95)
        for _ in range(max(2, int(w / 20))):
            mx = r.uniform(4, w - 4)
            ln = r.uniform(2.5, 7.0)
            s.path(f"M{mx - 1.2:.2f} 3.8 Q{mx:.2f} {3.8 + ln * 1.2:.2f} {mx + 1.2:.2f} 3.8 Z", fill=MOSS["normal"][2])

    def platform(self, kind: str, w: float, h: float, style: str = "") -> Svg:
        if kind == "ledge":
            if "floating" in style:
                return self._mossy_stump(w, h)
            return self._root_shelf(w, h, slick="ice" in style)
        s = Svg(w, h + 16)
        r = Rand(int(w * 3 + h * 7))
        if kind == "moving":
            if "raft" in style:
                self._raft(s, w, h, r)
            else:
                self._lily_pad(s, w, h, r)
        elif kind == "crumble":
            self._rotten_planks(s, w, h, r)
        elif kind == "semisolid":
            self._boardwalk(s, w, h, r)
        elif kind == "spring":
            self._spring_mushroom(s, w, h)
        else:  # conveyor / switch fallbacks: a slatted belt on rusty rollers
            s.path(rounded_rect_path(0.6, 0.6, w - 1.2, h - 1.2, h / 2), fill=s.linear(0, 0, 0, h, [(0, PLANK_HI), (0.5, PLANK), (1, PLANK_DARK)]),
                   stroke=INK, width=1.2)
            for x in range(int(h / 2), int(w - h / 2), 9):
                s.line(x, 1.5, x, h - 1.5, "#2e261e", 1.0, 0.7)
            for rx in (h / 2, w - h / 2):
                s.circle(rx, h / 2, h * 0.34, fill=s.radial(rx - 1, h / 2 - 1, h * 0.36, [(0, RUST_HI), (1, RUST_DARK)]), stroke=INK, width=0.8)
            s.line(h / 2, 1.4, w - h / 2, 1.4, "#e0d0b0", 0.9, 0.7)
        return s

    def _lily_pad(self, s: Svg, w: float, h: float, r: Rand) -> None:
        """Giant floating lily pad: a broad veined disc with a thin upturned plum rim,
        its stem and rootlets dangling under it (a faint wisp light keeps it afloat)."""
        cx = w / 2
        rx, ry, cy = w / 2 - 1.2, 4.8, 5.4
        _haze(s, cx, h + 2, w * 0.42, 6, WISP, 0.3)
        s.path(f"M{cx - 3:.2f} {cy + 6:.2f} Q{cx + 7:.2f} {h + 4:.2f} {cx + 1:.2f} {h + 15:.2f}", stroke="#2c4a32", width=2.6)
        s.path(f"M{cx - 3:.2f} {cy + 6:.2f} Q{cx + 7:.2f} {h + 4:.2f} {cx + 1:.2f} {h + 15:.2f}", stroke="#6a9a64", width=0.8, opacity=0.6)
        for k, vx in enumerate((w * 0.22, w * 0.38, w * 0.64, w * 0.8)):
            ln = 4 + 4 * ((k + 1) % 2)
            s.path(f"M{vx:.2f} {cy + 7:.2f} q{1.5 - k:.2f} {ln * 0.5:.2f} {0.5 - k * 0.3:.2f} {ln:.2f}", stroke="#3a2a30", width=0.9)
            s.circle(vx + 0.5 - k * 0.3, cy + 7 + ln + 0.8, 0.9, fill="#9ad0e0", opacity=0.7)
        # outer face of the upturned rim along the near edge: plum with fine ribs
        rim = 4.4
        outer = [(cx + math.cos(a) * rx, cy + math.sin(a) * ry) for a in [math.pi * i / 24 for i in range(25)]]
        lower = [(x, y + rim * (0.35 + 0.65 * math.sin(math.pi * i / 24))) for i, (x, y) in enumerate(outer)]
        s.path(_pl(outer) + "L" + _pl(list(reversed(lower)))[1:] + "Z", fill=s.linear(0, cy, 0, cy + ry + rim, [(0, "#c87888"), (0.5, "#8a3c58"), (1, "#4a1c32")]),
               stroke=INK, width=1.0)
        for i in range(2, 24, 2):
            (x1, y1), (x2, y2) = outer[i], lower[i]
            s.line(x1, y1 + 0.6, x2, y2 - 0.4, "#3a1426", 0.7, 0.6)
        # the disc
        s.ellipse(cx, cy, rx, ry, fill=s.radial(cx - rx * 0.3, cy - ry * 0.8, rx * 1.1, [(0, "#cfeea0"), (0.45, "#7fb85e"), (1, "#3c7a42")]), stroke=INK,
                  width=1.0)
        s.ellipse(cx, cy + 0.4, rx - 2.2, ry - 1.4, stroke="#2e5e34", width=0.8, opacity=0.6)
        hub = (cx - rx * 0.1, cy + 0.3)
        for k in range(14):
            a = 2 * math.pi * k / 14 + 0.2
            s.line(hub[0], hub[1], cx + math.cos(a) * (rx - 2.6), cy + math.sin(a) * (ry - 1.6), "#4e9048", 0.6, 0.65)
        s.polygon([(hub[0], hub[1]), (cx + rx - 0.6, cy - 1.0), (cx + rx - 0.6, cy + 1.6)], fill="#4a2036", stroke=INK, width=0.5)
        s.path(f"M{cx - rx * 0.85:.2f} {cy - 1.4:.2f} Q{cx - rx * 0.4:.2f} {cy - ry - 0.2:.2f} {cx + rx * 0.2:.2f} {cy - ry + 0.4:.2f}", stroke="#efffd8",
               width=1.0, opacity=0.8)
        for bx, by, br in ((w * 0.3, cy - 1.0, 1.0), (w * 0.34, cy + 0.6, 0.65), (w * 0.62, cy - 1.8, 0.8)):
            s.circle(bx, by, br, fill="#e6faff", opacity=0.8)

    def _raft(self, s: Svg, w: float, h: float, r: Rand) -> None:
        """Floating raft (style 'raft'): two mossy logs lashed with rope, seen lengthwise."""
        back_h, top_h = h * 0.5, h * 0.62
        s.path(rounded_rect_path(5, h - back_h - 0.5, w - 10, back_h, back_h / 2), fill=s.linear(0, h - back_h, 0, h, [(0, WOOD), (1, WOOD_DARK)]),
               stroke=INK, width=1.0)
        s.path(rounded_rect_path(0.8, 1.0, w - 1.6, top_h, top_h / 2), fill=s.linear(0, 1, 0, 1 + top_h, [(0, WOOD_HI), (0.5, WOOD), (1, WOOD_DARK)]),
               stroke=INK, width=1.1)
        for k in range(3):
            gy = 3.2 + k * (top_h - 4) / 3
            s.path(f"M{top_h * 0.6:.2f} {gy:.2f} Q{w * 0.5:.2f} {gy + 0.8 * (1 if k % 2 else -1):.2f} {w - top_h * 0.6:.2f} {gy:.2f}", stroke="#3a2a1e",
                   width=0.6, opacity=0.6)
        for ex in (top_h / 2 + 0.4, w - top_h / 2 - 0.4):
            s.ellipse(ex, 1 + top_h / 2, top_h * 0.3, top_h / 2 - 0.8, fill=s.radial(ex, 1 + top_h / 2, top_h / 2, [(0, "#e2c89a"), (1, "#a8845a")]),
                      stroke=INK, width=0.7)
            s.ellipse(ex, 1 + top_h / 2, top_h * 0.14, top_h * 0.24, stroke="#8a6a44", width=0.5)
        for bx in (w * 0.24, w * 0.5, w * 0.76):  # rope lashings around both logs
            s.path(rounded_rect_path(bx - 2.4, 0.4, 4.8, h - 0.8, 1.4), fill=s.linear(bx - 2.4, 0, bx + 2.4, 0, [(0, "#d8c08a"), (1, "#8a7044")]), stroke=INK,
                   width=0.6)
            for y in (3.0, 6.0, 9.0, 12.0):
                if y < h - 1:
                    s.line(bx - 2.2, y, bx + 2.2, y + 1.6, "#6a5430", 0.6, 0.8)
        s.path(blob(w * 0.66, 1.3, 7, 1.7, 0.3, seed=w), fill=MOSS["normal"][1])
        s.path(f"M6 {h + 3:.2f} Q{w / 2:.2f} {h + 8:.2f} {w - 6:.2f} {h + 3:.2f}", stroke="#5a8aa0", width=1.0, opacity=0.5)

    def _rotten_planks(self, s: Svg, w: float, h: float, r: Rand) -> None:
        """Crumbling walkway: two rotten planks with cracks, holes, a bent nail and fungus; crumbs falling."""
        for k in range(2):
            y = 0.8 + k * (h - 1.6) / 2
            ph = (h - 1.6) / 2 - 0.6
            sag = 1.2 if k == 0 else 0.6
            top = [(x, y + sag * math.sin(math.pi * x / w) + 0.4 * math.sin(x * 0.7 + k)) for x in [1 + i * (w - 2) / 12 for i in range(13)]]
            low = []
            for i in range(13):
                x = w - 1 - i * (w - 2) / 12
                low.append((x, y + ph + sag * math.sin(math.pi * x / w) + (r.uniform(0.2, 1.8) if 0 < i < 12 and k == 1 else 0)))
            d = smooth_open(top, 0.6) + "".join(f"L{x:.2f} {y_:.2f}" for x, y_ in low) + "Z"
            s.path(d, fill=s.linear(0, y, 0, y + ph, [(0, PLANK_HI if k == 0 else "#9c8a70"), (0.5, PLANK), (1, PLANK_DARK)]), stroke=INK, width=1.0)
            s.path(smooth_open(top, 0.6), stroke="#e0d2b8", width=0.8, opacity=0.6)
            for j in range(3):  # grain
                gy = y + ph * (0.3 + j * 0.22)
                s.path(f"M{3 + j * 5:.1f} {gy:.2f} Q{w * 0.5:.2f} {gy + 0.9 - j * 0.5:.2f} {w - 4 - j * 3:.1f} {gy:.2f}", stroke="#4a3e30", width=0.5, opacity=0.6)
        for _ in range(3):
            x = r.uniform(10, w - 10)
            s.path(f"M{x:.2f} 1 l{r.uniform(-2, 2):.2f} {h * 0.3:.2f} l{r.uniform(1, 3):.2f} {h * 0.2:.2f} l{r.uniform(-3, -1):.2f} {h * 0.35:.2f}",
                   stroke="#1a1410", width=1.2)
        for _ in range(max(2, int(w / 28))):
            x, y = r.uniform(8, w - 8), r.uniform(4, h - 4)
            s.ellipse(x, y, r.uniform(1.4, 2.6), r.uniform(0.9, 1.6), fill="#1a1410", stroke="#b0a084", width=0.4)
        nx = r.uniform(w * 0.3, w * 0.7)
        s.path(f"M{nx:.2f} 2.4 l2.4 -1.4 l1.2 1", stroke=RUST, width=1.0)
        s.circle(nx, 2.6, 0.9, fill=RUST_HI)
        for fx in (r.uniform(6, w * 0.35), r.uniform(w * 0.65, w - 6)):
            fy = h - 2
            s.path(f"M{fx - 3.5:.2f} {fy:.2f} Q{fx:.2f} {fy - 2.6:.2f} {fx + 3.5:.2f} {fy:.2f} Q{fx:.2f} {fy + 1.2:.2f} {fx - 3.5:.2f} {fy:.2f} Z",
                   fill=s.linear(0, fy - 3, 0, fy + 1, [(0, "#e8e0c8"), (1, "#a89878")]), stroke=INK, width=0.4)
        s.path(blob(w * 0.18, 1.4, 6, 1.6, 0.3, seed=w), fill=MOSS["normal"][1], opacity=0.9)
        for _ in range(5):
            x, y = r.uniform(6, w - 6), h + r.uniform(1.5, 10)
            sz = r.uniform(0.8, 1.8)
            s.polygon([(x - sz, y), (x, y - sz), (x + sz, y + sz * 0.3)], fill="#6a5a46", opacity=0.85)

    def _boardwalk(self, s: Svg, w: float, h: float, r: Rand) -> None:
        """Semisolid: a rickety boardwalk — uneven cross planks on spindly posts with a sagging rope."""
        band = min(h, 8.0)
        for k, px in enumerate((w * 0.16, w * 0.5, w * 0.84)):
            lean = (k - 1) * 2.0
            s.path(f"M{px - 1.8:.2f} {band - 1:.2f} L{px - 1.8 + lean:.2f} {h + 16:.2f} L{px + 1.8 + lean:.2f} {h + 16:.2f} L{px + 1.8:.2f} {band - 1:.2f} Z",
                   fill=s.linear(px - 2, 0, px + 2, 0, [(0, WOOD), (1, WOOD_DARK)]))
        s.path(f"M{w * 0.16 + 1:.2f} {band + 2:.2f} L{w * 0.5 + 1:.2f} {h + 12:.2f} M{w * 0.84 - 1:.2f} {band + 2:.2f} L{w * 0.5 - 1:.2f} {h + 12:.2f}",
               stroke=WOOD_DARK, width=1.4)
        s.path(f"M1 {band + 1.5:.2f} Q{w / 2:.2f} {band + 7:.2f} {w - 1:.2f} {band + 1.5:.2f}", stroke="#c2a878", width=1.2)
        s.path(rounded_rect_path(0.6, band - 2.4, w - 1.2, 2.6, 1.2), fill=WOOD_DARK)
        x = 0.8
        i = 0
        while x < w - 2:
            pw = min(w - 0.8 - x, 8.5 + 4 * _hash(i, 4.4))
            dy = (_hash(i, 5.1) - 0.5) * 1.4
            s.path(rounded_rect_path(x + 0.35, 0.6 + max(0.0, dy), pw - 0.7, band - 1.0, 1.2),
                   fill=s.linear(0, 0, 0, band, [(0, PLANK_HI if i % 3 else "#9c8a70"), (1, PLANK_DARK)]), stroke=INK, width=0.8)
            s.line(x + 1.2, 1.4 + max(0.0, dy), x + pw - 1.2, 1.4 + max(0.0, dy), "#e8dcc0", 0.7, 0.6)
            if _hash(i, 6.3) > 0.6:
                s.circle(x + pw / 2, band - 2.5, 0.7, fill="#2a221a")
            x += pw
            i += 1
        s.path(blob(w * 0.66, 1.2, 5, 1.5, 0.3, seed=w), fill=MOSS["normal"][1], opacity=0.9)
        _moss_hang(s, w * 0.3, band + 1, 10, 12, w, ("#6a7a62", "#9aa88c"), 0.7)

    def _spring_mushroom(self, s: Svg, w: float, h: float) -> None:
        """Spring: a squat bouncy toadstool — plum cap with pale spots and a glowing gill ring."""
        cx = w / 2
        stem_top = h * 0.5
        s.path(f"M{cx - w * 0.17:.2f} {h + 1:.2f} Q{cx - w * 0.2:.2f} {stem_top + 3:.2f} {cx - w * 0.12:.2f} {stem_top:.2f} L{cx + w * 0.12:.2f} {stem_top:.2f} "
               f"Q{cx + w * 0.2:.2f} {stem_top + 3:.2f} {cx + w * 0.17:.2f} {h + 1:.2f} Z",
               fill=s.linear(cx - w * 0.2, 0, cx + w * 0.2, 0, [(0, "#f0ead8"), (1, "#a49a86")]), stroke=INK, width=1.0)
        _haze(s, cx, stem_top + 1, w * 0.4, 3.0, FIRE, 0.75)
        s.path(f"M{cx - w * 0.44:.2f} {stem_top - 0.5:.2f} Q{cx:.2f} {stem_top + 3.4:.2f} {cx + w * 0.44:.2f} {stem_top - 0.5:.2f}", stroke=FIRE, width=1.6)
        cap = (f"M{cx - w / 2 + 0.6:.2f} {stem_top:.2f} C{cx - w / 2:.2f} {stem_top - h * 0.36:.2f} {cx - w * 0.3:.2f} 0.8 {cx:.2f} 0.8 "
               f"C{cx + w * 0.3:.2f} 0.8 {cx + w / 2:.2f} {stem_top - h * 0.36:.2f} {cx + w / 2 - 0.6:.2f} {stem_top:.2f} "
               f"Q{cx:.2f} {stem_top - 2.4:.2f} {cx - w / 2 + 0.6:.2f} {stem_top:.2f} Z")
        s.path(cap, fill=s.radial(cx - w * 0.15, h * 0.12, w * 0.7, [(0, "#f2a8d8"), (0.45, "#b0508a"), (1, "#5e1e4a")]), stroke=INK, width=1.2)
        for fx, fy, fr in ((-0.26, 0.42, 0.07), (0.0, 0.2, 0.08), (0.24, 0.38, 0.065), (-0.1, 0.62, 0.05), (0.34, 0.66, 0.045)):
            s.ellipse(cx + w * fx, h * fy, w * fr, w * fr * 0.75, fill="#fff2e8", opacity=0.9)
        s.path(f"M{cx - w * 0.32:.2f} {h * 0.22:.2f} Q{cx - w * 0.12:.2f} {h * 0.04:.2f} {cx + w * 0.08:.2f} {h * 0.06:.2f}", stroke="#ffe0f2", width=1.0,
               opacity=0.8)

    def _root_shelf(self, w: float, h: float, slick: bool = False) -> Svg:
        """Ledge: a shelf of twisted roots packed with peat, moss on top, rootlets dangling (foxfire tips)."""
        hr = self.terrain_headroom
        r = Rand(int(w * 7 + h * 3))
        drop = 16.0
        s = Svg(w, h + hr + drop)
        y0, bottom = hr, hr + h
        n = max(2, int(w / 22))
        for k in range(n):
            rx = (k + 0.5) * w / n + r.uniform(-4, 4)
            ln = r.uniform(5, drop - 2)
            pts = [(rx, bottom - 3), (rx + r.uniform(-2, 2), bottom + ln * 0.5), (rx + r.uniform(-3, 3), bottom + ln)]
            s.path(smooth_open(pts), stroke=ROOT, width=r.uniform(1.0, 1.8))
            if k % 2 == 0:
                _glow(s, pts[-1][0], pts[-1][1], 4, FIRE, 0.55)
                s.circle(pts[-1][0], pts[-1][1], 0.9, fill=FIRE_HOT)
        d = (f"M6 {y0 + 4:.2f} L{w - 6:.2f} {y0 + 4:.2f} Q{w:.2f} {y0 + 4:.2f} {w - 0.6:.2f} {y0 + 11:.2f} "
             f"L{w - 3:.2f} {bottom - 5:.2f} Q{w - 6:.2f} {bottom + 1:.2f} {w - 14:.2f} {bottom:.2f} L14 {bottom:.2f} "
             f"Q6 {bottom + 1:.2f} 3 {bottom - 5:.2f} L0.6 {y0 + 11:.2f} Q0 {y0 + 4:.2f} 6 {y0 + 4:.2f} Z")
        s.path(d, fill=s.linear(0, y0, 0, bottom, [(0, PEAT_TOP), (0.45, PEAT), (1, PEAT_DARK)]), stroke=INK, width=1.2)
        # thick roots twisting along the shelf, wrapping over the ends
        fill = s.linear(0, y0, 0, bottom, [(0, ROOT_HI), (0.5, ROOT), (1, ROOT_DARK)])
        for k in range(3):
            yb = y0 + 8 + k * (h - 8) / 3
            amp = 2.5 + k
            centre = [(x, yb + amp * math.sin(x * 0.09 + k * 2.1), (3.2 - k * 0.5) * (0.75 + 0.25 * math.sin(x * 0.2 + k)))
                      for x in [-2 + i * (w + 4) / 16 for i in range(17)]]
            s.path(_taper(centre), fill=fill, stroke=ROOT_DARK, width=0.6)
            s.path(smooth_open([(x, y - t * 0.3) for x, y, t in centre]), stroke="#c8a888", width=0.6, opacity=0.4)
        for _ in range(max(1, int(w / 50))):
            pr = r.uniform(2.2, 3.8)
            px, py = r.uniform(pr * 1.5 + 4, w - pr * 1.5 - 4), r.uniform(y0 + 12, max(y0 + 13, bottom - 5))
            s.path(blob(px, py, pr * 1.35, pr, 0.12, seed=px), fill=s.radial(px - pr * 0.4, py - pr * 0.5, pr * 1.7, [(0, STONE_HI), (0.55, STONE),
                                                                                                               (1, STONE_DARK)]), opacity=0.9)
        self._bank_cap(s, w, 0.0, y0, True, True, r, "ice" if slick else "normal")
        return s

    def _mossy_stump(self, w: float, h: float) -> Svg:
        """Floating ledge (style 'floating'): a slice of a giant cypress stump — furrowed
        bark, a pale ringed cut face (the walkable top) half covered by moss, bracket
        fungi and roots trailing below."""
        hr = self.terrain_headroom
        r = Rand(int(w * 5 + h * 11))
        drop = 18.0
        s = Svg(w, h + hr + drop)
        y0, bottom = hr, hr + h
        cx, rx, ry = w / 2, w / 2 - 0.8, 3.6
        for k in range(max(3, int(w / 18))):
            rx_ = (k + 0.5) * w / max(3, int(w / 18)) + r.uniform(-3, 3)
            ln = r.uniform(6, drop - 1)
            side = 1 if rx_ > w / 2 else -1
            pts = [(rx_, bottom - 4), (rx_ + side * r.uniform(1, 4), bottom + ln * 0.5), (rx_ + side * r.uniform(2, 7), bottom + ln)]
            s.path(smooth_open(pts), stroke=ROOT_DARK, width=r.uniform(1.6, 2.6))
            s.path(smooth_open(pts), stroke=ROOT, width=0.8)
        # bark body flaring into roots at the bottom
        body = (f"M0.8 {y0 + ry:.2f} L{w - 0.8:.2f} {y0 + ry:.2f} Q{w:.2f} {(y0 + bottom) / 2:.2f} {w - 0.6:.2f} {bottom - 3:.2f} "
                f"Q{w - 5:.2f} {bottom + 2:.2f} {w - 14:.2f} {bottom:.2f} L14 {bottom:.2f} Q5 {bottom + 2:.2f} 0.6 {bottom - 3:.2f} "
                f"Q0 {(y0 + bottom) / 2:.2f} 0.8 {y0 + ry:.2f} Z")
        s.path(body, fill=s.linear(0, 0, w, 0, [(0, "#2a201c"), (0.2, "#5e4a3a"), (0.42, "#7a6250"), (0.75, "#4a3a2e"), (1, "#201818")]), stroke=INK,
               width=1.2)
        for k in range(int(w / 6)):  # furrows (dark) and plates (light)
            gx = 3 + k * 6 + r.uniform(-1.2, 1.2)
            if gx > w - 3:
                break
            bend = r.uniform(-1.5, 1.5)
            s.path(f"M{gx:.2f} {y0 + ry + 2:.2f} Q{gx + bend:.2f} {(y0 + bottom) / 2:.2f} {gx + bend * 0.5:.2f} {bottom - 1.5:.2f}", stroke="#1a1210",
                   width=r.uniform(0.9, 1.6), opacity=0.75)
            if k % 2:
                s.path(f"M{gx + 2.4:.2f} {y0 + ry + 3:.2f} L{gx + 2.4 + bend * 0.5:.2f} {bottom - 3:.2f}", stroke="#a08468", width=0.6, opacity=0.35)
        # the cut face: rings, a radial crack, a moonlit rim
        s.ellipse(cx, y0 + ry, rx, ry, fill=s.radial(cx - rx * 0.25, y0 + ry * 0.6, rx * 0.9, [(0, "#efd9b0"), (0.6, "#cbab80"), (1, "#9a7852")]),
                  stroke=INK, width=1.0)
        for k in range(1, 6):
            s.ellipse(cx + rx * 0.08, y0 + ry + 0.15, rx * k / 6, ry * k / 6, stroke="#8a6a46", width=0.5, opacity=0.65)
        s.path(f"M{cx + rx * 0.08:.2f} {y0 + ry:.2f} L{cx + rx * 0.55:.2f} {y0 + ry + 1.4:.2f}", stroke="#5a4028", width=0.8, opacity=0.8)
        s.path(f"M{cx - rx * 0.92:.2f} {y0 + ry - 0.6:.2f} Q{cx - rx * 0.4:.2f} {y0 - 0.3:.2f} {cx + rx * 0.4:.2f} {y0 + 0.1:.2f}", stroke="#fff4dc", width=0.9,
               opacity=0.8)
        # moss patch over the left of the face, dripping over the rim
        mx1 = w * r.uniform(0.45, 0.6)
        top = [(x, y0 + ry - ry * math.sqrt(max(0.0, 1 - ((x - cx) / rx) ** 2)) - 0.6) for x in [1.2 + i * (mx1 - 1.2) / 12 for i in range(13)]]
        low = [(x, y0 + ry + ry * math.sqrt(max(0.0, 1 - ((x - cx) / rx) ** 2)) + 1.5 + (2.5 + 3 * _hash(i, 3.3) if i % 2 else 0.4))
               for i, x in enumerate([mx1 - i * (mx1 - 1.2) / 12 for i in range(13)])]
        s.path(smooth_open(top, 0.8) + f"Q{mx1 + 5:.2f} {top[-1][1] + 1.2:.2f} {mx1 + 3:.2f} {y0 + ry + 1:.2f}"
               + "".join(f"L{x:.2f} {y:.2f}" for x, y in low) + "Z",
               fill=s.linear(0, y0 - 2, 0, y0 + ry * 2 + 4, [(0, MOSS["normal"][0]), (0.4, MOSS["normal"][1]), (1, MOSS["normal"][3])]), stroke=INK, width=0.8)
        s.path(smooth_open(top, 0.8), stroke=MOSS["normal"][4], width=1.1, opacity=0.85)
        for _ in range(max(2, int(mx1 / 10))):
            bx = r.uniform(3, mx1 - 3)
            for k in range(3):
                sh = r.uniform(3, 7)
                lean = r.uniform(-2.4, 2.4)
                s.path(f"M{bx + k - 1.4:.2f} {y0 + 0.8:.2f} Q{bx + k + lean * 0.3:.2f} {y0 - sh * 0.5:.2f} {bx + k + lean:.2f} {y0 - sh:.2f}",
                       stroke=r.choice([MOSS["normal"][0], "#c8c890"]), width=0.8)
        for j in range(2):
            hgt = r.uniform(6, 9) * (1 - j * 0.25)
            _bell_mushroom(s, mx1 * 0.35 + j * 4.5, y0 + 1.0, hgt, hgt * 0.4, r.uniform(-1, 1), halo=0.5)
        for fx, fy, size in ((w * 0.84, y0 + ry + h * 0.4, 6.0), (w * 0.88, y0 + ry + h * 0.65, 4.2)):
            if fy < bottom - 3:
                _glow(s, fx, fy, size * 1.8, FIRE, 0.35)
                s.path(f"M{fx - size:.2f} {fy:.2f} Q{fx:.2f} {fy - size * 0.7:.2f} {fx + size:.2f} {fy:.2f} Q{fx:.2f} {fy + size * 0.35:.2f} {fx - size:.2f} {fy:.2f} Z",
                       fill=s.linear(0, fy - size * 0.6, 0, fy + size * 0.3, [(0, FIRE_HOT), (0.5, FIRE), (1, FIRE_DEEP)]), stroke=INK, width=0.6)
        _moss_hang(s, w * 0.24, bottom - 2, 16, 14, w, ("#6a7a62", "#9aa88c"), 0.75)
        return s

    def pipe(self, w: float, h: float, warp: bool) -> Svg:
        """Rusted iron culvert: corrugated grey iron blooming with rust, a riveted collar,
        roots and moss gripping it (warp: fireflies circling the dark mouth)."""
        s = Svg(w, h)
        r = Rand(int(w * 7 + h))
        body = s.linear(4, 0, w - 4, 0, [(0, IRON_DEEP), (0.14, "#474c5a"), (0.3, "#a4acbc"), (0.42, "#6a7080"), (0.75, "#3a3e4a"), (1, IRON_DEEP)])
        s.path(rounded_rect_path(4, 10, w - 8, h - 10, 2), fill=body, stroke=INK, width=1.3)
        for y in range(17, int(h) - 2, 6):  # corrugations: a shadow groove under a lit crest
            s.line(5, y, w - 5, y, "#14161c", 1.4, 0.5)
            s.line(5, y - 1.8, w - 5, y - 1.8, "#d8deea", 0.7, 0.3)
        # rust bloom: patches around the seams and runs dripping down
        for _ in range(4):
            rx, ry = r.uniform(8, w - 8), r.uniform(16, max(17.0, h - 6))
            s.path(blob(rx, ry, r.uniform(3, 6), r.uniform(2, 4), 0.35, seed=rx + ry), fill=s.radial(rx, ry, 6, [(0, RUST_HI), (1, RUST, 0.6)]), opacity=0.75)
        for k in range(3):
            rx = 9 + k * (w - 18) / 2 + r.uniform(-3, 3)
            s.path(f"M{rx - 1.2:.2f} 14 Q{rx - 0.4:.2f} {h * 0.55:.2f} {rx + 0.3:.2f} {h - 3:.2f} Q{rx + 1.2:.2f} {h * 0.5:.2f} {rx + 1.6:.2f} 14 Z",
                   fill=RUST, opacity=0.5)
        s.line(w * 0.66, 14, w * 0.66, h - 2, "#22242c", 1.2, 0.7)  # riveted seam
        for y in range(18, int(h) - 2, 9):
            s.circle(w * 0.66, y, 0.9, fill="#c8ccd6", stroke=INK, width=0.3)
        # a root crawling down from the rim and splitting into rootlets
        pts = [(9.0, 12.0, 4.0), (7.0, h * 0.35, 3.4), (10.5, h * 0.62, 2.8), (8.0, h - 2, 2.2)]
        s.path(_vtaper(pts), fill=s.linear(0, 0, 0, h, [(0, ROOT_HI), (1, ROOT)]), stroke=ROOT_DARK, width=0.6)
        s.path(f"M10 {h * 0.45:.2f} Q16 {h * 0.55:.2f} 15 {h * 0.75:.2f}", stroke=ROOT, width=1.4)
        s.path(f"M{w - 9:.2f} 13 Q{w - 6:.2f} 18 {w - 8.5:.2f} 25", stroke=ROOT, width=1.8)
        s.path(f"M{w - 9:.2f} 13 Q{w - 6:.2f} 18 {w - 8.5:.2f} 25", stroke=ROOT_HI, width=0.6, opacity=0.6)
        # collar with the dark mouth
        rim = s.linear(0.8, 0, w - 0.8, 0, [(0, IRON_DEEP), (0.2, "#5a606e"), (0.34, "#c4ccda"), (0.5, "#767c8c"), (0.85, "#30343e"), (1, IRON_DEEP)])
        s.path(rounded_rect_path(0.8, 2.6, w - 1.6, 11, 3.5), fill=rim, stroke=INK, width=1.3)
        s.path(f"M3 12 L{w - 3:.2f} 12", stroke=RUST, width=1.6, opacity=0.6)
        for rx in [5 + i * (w - 10) / 5 for i in range(6)]:
            s.circle(rx, 10.0, 1.1, fill="#d8dce6", stroke=INK, width=0.4)
        s.ellipse(w / 2, 4.0, w / 2 - 1.4, 3.4, fill=s.linear(0, 0.6, 0, 7.4, [(0, "#9aa2b2"), (1, "#3a3e4a")]), stroke=INK, width=1.0)
        s.ellipse(w / 2, 4.3, w / 2 - 5, 2.3, fill="#060608" if not warp else "#1a2410")
        s.path(blob(w * 0.28, 2.4, w * 0.18, 2.0, 0.3, seed=w), fill=MOSS["normal"][1])
        s.path(f"M{w * 0.2:.2f} 3.6 q0.6 4 -0.4 7 M{w * 0.3:.2f} 3.8 q0.5 3 -0.2 5", stroke=MOSS["normal"][2], width=1.1)
        if h > 30:
            _bell_mushroom(s, w - 10, h - 1, min(7.0, h * 0.18), 2.6, 0.5, halo=0.5)
        if warp:  # fireflies circling the mouth: the secret is down this culvert
            _haze(s, w / 2, 4.3, w / 2 - 6, 2.2, FIRE, 0.9)
            for k in range(6):
                a = k * 2 * math.pi / 6 + 0.4
                fx, fy = w / 2 + math.cos(a) * (w / 2 - 4), 12 + math.sin(a) * 7
                _glow(s, fx, fy, 5, FIRE, 0.7)
                s.circle(fx, fy, 1.1, fill=FIRE_HOT)
            cy = 27 if h > 36 else h * 0.68
            _glow(s, w / 2, cy, 10, FIRE, 0.6)
            s.polygon([(w / 2 - 4.5, cy - 2.8), (w / 2 + 4.5, cy - 2.8), (w / 2, cy + 3.6)], fill=FIRE_HOT, stroke="#3a5a12", width=0.7)
        return s

    def hazard(self, kind: str, w: float, h: float):
        if kind != "thorns":
            return None
        hh = max(h, 16.0)
        s = Svg(w, hh + 4)
        for k in range(3):
            pts = [(lx, hh * (0.45 + 0.18 * k) + 3 * math.sin(lx * 0.12 + k * 2)) for lx in [i * w / 12 for i in range(13)]]
            s.path(smooth_open(pts), stroke=["#2a1e2a", "#3a2c38", "#4e3c48"][k], width=3.4 - k * 0.6)
            for i, (lx, ly) in enumerate(pts[:-1]):
                if (i + k) % 2 == 0:
                    s.polygon([(lx - 1.8, ly), (lx + 0.4, ly - 6), (lx + 1.8, ly)], fill="#e6dcc8", stroke=INK, width=0.5)
        return s

    # ------------------------------------------------------------------ props
    def _tree_cypress(self, seed: int) -> Svg:
        r = Rand(seed)
        s = Svg(200, 240)
        tr = _Cypress(100 + r.uniform(-6, 6), 236, 196, 24, r.uniform(-10, 10), seed * 0.37, flare=2.0)
        _cypress(s, tr, r, ("#7a6a62", "#4a3e3c", "#241e20"), "#a8b0d0", ("#5e8a6c", "#33573f", "#1c3024"), "#9ac0a0",
                 ("#9aa898", "#cdd6c4"), 0.85, outline=INK)
        for k in range(5):
            kx = tr.cx + r.uniform(-62, 62)
            if abs(kx - tr.cx) < 30:
                continue
            _knee(s, kx, 238, r.uniform(8, 16), r.uniform(4, 6), ("#7a6a62", "#2e2626"), "#c0c4d8")
        return s

    def _knees(self, seed: int) -> Svg:
        """A cluster of cypress knees: knobbly rounded wooden bumps with moss caps."""
        r = Rand(seed)
        s = Svg(72, 34)
        for k in range(4):
            kx = 12 + k * 15 + r.uniform(-3, 3)
            kh = r.uniform(11, 22) * (1.0 if k % 2 else 0.72)
            kw = kh * r.uniform(0.5, 0.62)
            pts = [(kx - kw, 33.5), (kx - kw * 0.85, 33 - kh * 0.45), (kx - kw * 0.75, 33 - kh * 0.85), (kx - kw * 0.2, 33 - kh * 1.02),
                   (kx + kw * 0.45, 33 - kh * 0.95), (kx + kw * 0.8, 33 - kh * 0.6), (kx + kw, 33.5)]
            d = smooth_open(pts, 0.8) + "Z"
            s.path(d, fill=s.linear(kx - kw, 0, kx + kw, 0, [(0, "#5a4a40"), (0.4, "#8a7462"), (1, "#3a2e28")]), stroke=INK, width=1.1)
            for j in range(2):
                y = 33 - kh * (0.3 + j * 0.28)
                s.path(f"M{kx - kw * 0.7:.2f} {y:.2f} Q{kx:.2f} {y + 1.4:.2f} {kx + kw * 0.7:.2f} {y - 0.4:.2f}", stroke="#2e241e", width=0.7, opacity=0.7)
            s.path(f"M{kx - kw * 0.55:.2f} {33 - kh * 0.6:.2f} Q{kx - kw * 0.45:.2f} {33 - kh * 0.92:.2f} {kx - kw * 0.05:.2f} {33 - kh * 0.98:.2f}",
                   stroke="#d0c4b4", width=0.9, opacity=0.6)
            s.path(blob(kx - kw * 0.05, 33 - kh * 0.92, kw * 0.7, kh * 0.16, 0.3, seed=kx), fill=s.linear(0, 33 - kh * 1.1, 0, 33 - kh * 0.7,
                   [(0, MOSS["normal"][0]), (1, MOSS["normal"][2])]))
        s.path(blob(36, 33.5, 32, 2.0, 0.3, seed=seed), fill=MOSS["normal"][2])
        return s

    def _reed_clump(self, seed: int, cattails: bool) -> Svg:
        r = Rand(seed)
        s = Svg(60, 90)
        _reeds(s, 30, 88, 70, 9, seed, "#4a6a48", "#c0d8a0", spread=14, width=2.0)
        if cattails:
            for k in range(3):
                _cattail(s, 22 + k * 8 + r.uniform(-2, 2), 88, r.uniform(58, 80), r.uniform(-6, 6), "#3a5a34", ("#8a5a3a", "#3e2416"), "#e0b890", 1.0)
        _reeds(s, 30, 88, 46, 6, seed * 1.7, "#6a8a5a", "#d8eab0", spread=12, width=1.8)
        return s

    def _lantern_post(self, seed: int) -> Svg:
        """Crooked wooden lantern post with a warm lantern (amber = safe ground)."""
        s = Svg(56, 120)
        lean = 3.0 if seed % 2 else -2.0
        s.path(f"M14 120 Q13 70 {16 + lean:.1f} 14 L{22 + lean:.1f} 14 Q20 70 22 120 Z", fill=s.linear(13, 0, 22, 0, [(0, WOOD_HI), (1, WOOD_DARK)]), stroke=INK,
               width=1.2)
        for y in (40, 72, 98):
            s.path(f"M15 {y} q3 2 6 0", stroke="#2a1e16", width=0.8)
        s.path(f"M{18 + lean:.1f} 20 Q{30 + lean:.1f} 12 {40 + lean:.1f} 18", stroke=INK, width=3.0)
        s.path(f"M{18 + lean:.1f} 20 Q{30 + lean:.1f} 12 {40 + lean:.1f} 18", stroke=WOOD, width=1.6)
        _hang_lantern(s, 40 + lean, 18, 13, True, 0.6)
        s.path(blob(17, 14, 6, 2.4, 0.3, seed=seed), fill=MOSS["normal"][1])
        _moss_hang(s, 26 + lean, 16, 8, 16, seed, SPANISH_MOSS, 0.8)
        s.path(blob(18, 119, 10, 2.6, 0.3, seed=seed + 3), fill=MOSS["normal"][2])
        return s

    def _gravestone(self, seed: int) -> Svg:
        """Gravestone-like mossy standing stone (rounded top, a carved spiral; never a cross)."""
        s = Svg(44, 56)
        tilt = -6 if seed % 2 else 5
        with s.group(f"rotate({tilt} 22 54)"):
            s.path("M8 56 L8 18 Q8 4 22 4 Q36 4 36 18 L36 56 Z", fill=s.linear(8, 0, 36, 0, [(0, "#a2aa9c"), (0.5, "#76806f"), (1, "#454d42")]), stroke=INK,
                   width=1.3)
            s.path("M10 18 Q10 7 22 7", stroke="#d8e0d0", width=1.2, opacity=0.6)
            cx, cy = 22.0, 26.0
            pts = []
            for i in range(26):
                a = i * 0.42
                rr = 1 + i * 0.3
                pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
            s.path(smooth_open(pts), stroke="#3a4236", width=1.2)
            s.path(smooth_open([(x + 0.5, y + 0.5) for x, y in pts]), stroke="#c0c8b8", width=0.5, opacity=0.5)
            s.line(13, 42, 31, 42, "#3a4236", 1.2)
            s.line(15, 47, 29, 47, "#3a4236", 1.0)
            s.path(blob(14, 9, 9, 3.6, 0.3, seed=seed), fill=s.linear(0, 5, 0, 13, [(0, MOSS["normal"][0]), (1, MOSS["normal"][2])]))
            s.path(blob(33, 50, 6, 4, 0.3, seed=seed + 1), fill=MOSS["normal"][1])
            s.path("M10 12 q0.4 6 -0.3 10 M14 12 q0.4 4 0 7", stroke=MOSS["normal"][2], width=1.2)
        return s

    def _lily_puddle(self, seed: int) -> Svg:
        """A shallow mossy pool on the bank with lily pads and a white lily."""
        r = Rand(seed)
        s = Svg(56, 12)
        s.ellipse(28, 6, 27, 5, fill=MOSS["normal"][2], stroke=INK, width=1.0)
        s.ellipse(28, 6.2, 24, 3.9, fill=s.linear(0, 2, 0, 10, [(0, "#3a5a6a"), (1, "#16262e")]))
        s.path("M8 5 Q28 2.6 48 5", stroke="#b8d0e0", width=0.8, opacity=0.6)
        for lx, rx in ((16, 6), (34, 7), (44, 4.5)):
            s.path(f"M{lx:.1f} 6 L{lx + rx:.1f} 5.6 A{rx:.1f} {rx * 0.34:.1f} 0 1 1 {lx + rx * 0.9:.1f} 6.7 Z", fill="#5a8a50", stroke="#1e3a20",
                   width=0.5)
        fx = 33.0
        for k in range(6):
            a = math.radians(-170 + k * 32)
            s.path(f"M{fx:.1f} 5 L{fx + math.cos(a) * 3.4:.1f} {5 + math.sin(a) * 2.8:.1f}", stroke="#f6f2ff", width=1.8)
        s.circle(fx, 4.6, 1.0, fill=FIRE)
        del r
        return s

    def _firefly_jar(self, seed: int) -> Svg:
        r = Rand(seed)
        s = Svg(26, 32)
        _glow(s, 13, 18, 13, FIRE, 0.45)
        s.path("M6 12 Q4 20 6 29 Q13 31.5 20 29 Q22 20 20 12 Z", fill=s.linear(4, 0, 22, 0, [(0, "#c8e0d8", 0.35), (0.5, "#e8fff4", 0.15),
                                                                                            (1, "#a0c0b8", 0.35)]), stroke="#5a7a74", width=0.9)
        for _ in range(5):
            fx, fy = r.uniform(8, 18), r.uniform(15, 27)
            _glow(s, fx, fy, 3.4, FIRE, 0.7)
            s.circle(fx, fy, 0.9, fill=FIRE_HOT)
        s.path("M7.5 14 Q7 21 8 27", stroke="#ffffff", width=0.9, opacity=0.6)
        s.rect(6.5, 8, 13, 4.5, fill=s.linear(0, 8, 0, 12.5, [(0, "#a88a6a"), (1, "#5a4434")]), stroke=INK, width=0.8, rx=1.2)
        s.path("M8 8 Q13 4 18 8", stroke="#8a7a5a", width=0.9)
        s.path(blob(13, 30.5, 11, 1.8, 0.2, seed=seed), fill=MOSS["normal"][2])
        return s

    def _signpost(self, seed: int) -> Svg:
        """Crooked signpost with blank arrow boards (no text)."""
        s = Svg(60, 76)
        s.path("M27 76 L28 10 L32 10 L33 76 Z", fill=s.linear(27, 0, 33, 0, [(0, WOOD_HI), (1, WOOD_DARK)]), stroke=INK, width=1.1)
        for y, d, tilt in ((18, 1, -8), (34, -1, 10), (48, 1, 4)):
            with s.group(f"rotate({tilt} 30 {y + 4})"):
                if d > 0:
                    pts = [(24, y), (50, y), (56, y + 4.5), (50, y + 9), (24, y + 9)]
                else:
                    pts = [(36, y), (10, y), (4, y + 4.5), (10, y + 9), (36, y + 9)]
                s.polygon(pts, fill=s.linear(0, y, 0, y + 9, [(0, PLANK_HI), (1, PLANK_DARK)]), stroke=INK, width=1.0)
                s.line(pts[0][0] + 2 * d, y + 2.4, pts[1][0] - 3 * d, y + 2.4, "#e8dcc0", 0.7, 0.6)
                s.circle(30, y + 4.5, 0.9, fill="#2a221a")
        s.path(blob(30, 9.5, 5, 2.2, 0.3, seed=seed), fill=MOSS["normal"][1])
        _moss_hang(s, 44, 22, 8, 12, seed, SPANISH_MOSS, 0.8)
        return s

    def _mushrooms(self, seed: int) -> Svg:
        r = Rand(seed)
        s = Svg(44, 30)
        for k in range(r.choice([3, 4, 5])):
            hgt = r.uniform(9, 20) * (1 - k * 0.12)
            _bell_mushroom(s, 10 + k * 6.5 + r.uniform(-2, 2), 29, hgt, hgt * 0.36, r.uniform(-2.5, 2.5), halo=0.5)
        s.path(blob(22, 29.5, 17, 2.2, 0.3, seed=seed), fill=MOSS["normal"][2])
        return s

    def _dead_tree_prop(self, seed: int) -> Svg:
        s = Svg(190, 190)
        _dead_tree(s, 95, 188, 150, seed * 1.3, "#4e4248", "#a8a0c0", lean=6, outline=INK,
                   trunk=s.linear(80, 0, 112, 0, [(0, "#2e262c"), (0.4, "#5e5058"), (1, "#2a2228")]))
        _moss_hang(s, 78, 92, 18, 34, seed, SPANISH_MOSS, 0.8)
        _moss_hang(s, 112, 86, 14, 28, seed + 1, SPANISH_MOSS, 0.8)
        return s

    def props(self) -> dict[str, PropSpec]:
        return {
            "tree_cypress": PropSpec(lambda: self._tree_cypress(3), (100, 238)),
            "tree_cypress_b": PropSpec(lambda: self._tree_cypress(8), (100, 238)),
            "tree_dead": PropSpec(lambda: self._dead_tree_prop(5), (95, 188)),
            "cypress_knees": PropSpec(lambda: self._knees(2), (36, 33)),
            "cypress_knees_b": PropSpec(lambda: self._knees(9), (36, 33)),
            "reed_bush": PropSpec(lambda: self._reed_clump(4, False), (30, 88)),
            "cattail_bush": PropSpec(lambda: self._reed_clump(7, True), (30, 88)),
            "lantern_post": PropSpec(lambda: self._lantern_post(1), (18, 119)),
            "lantern_post_b": PropSpec(lambda: self._lantern_post(2), (18, 119)),
            "grave_stone": PropSpec(lambda: self._gravestone(1), (22, 54)),
            "grave_stone_b": PropSpec(lambda: self._gravestone(2), (22, 54)),
            "lily_puddle": PropSpec(lambda: self._lily_puddle(3), (28, 6)),
            "firefly_jar": PropSpec(lambda: self._firefly_jar(5), (13, 31)),
            "signpost": PropSpec(lambda: self._signpost(6), (30, 75)),
            "mushrooms": PropSpec(lambda: self._mushrooms(4), (22, 29)),
            "mushrooms_b": PropSpec(lambda: self._mushrooms(11), (22, 29)),
        }

    def auto_decor(self, rng, surface_w: float):
        out = []
        x = rng.uniform(30, 110)
        lantern_gap = 0.0
        while x < surface_w - 30:
            roll = rng.next()
            if roll < 0.16:
                out.append((rng.choice(["reed_bush", "cattail_bush"]), x, rng.uniform(0.75, 1.0), "back"))
            elif roll < 0.28:
                out.append((rng.choice(["mushrooms", "mushrooms_b"]), x, rng.uniform(0.7, 1.0), "mid"))
            elif roll < 0.38:
                out.append((rng.choice(["cypress_knees", "cypress_knees_b"]), x, rng.uniform(0.7, 1.0), "back"))
            elif roll < 0.47:
                out.append((rng.choice(["grave_stone", "grave_stone_b"]), x, rng.uniform(0.8, 1.0), "back"))
            elif roll < 0.56 and x - lantern_gap > 260:
                out.append((rng.choice(["lantern_post", "lantern_post_b"]), x, rng.uniform(0.9, 1.05), "back"))
                lantern_gap = x
            elif roll < 0.63 and surface_w > 280:
                out.append((rng.choice(["tree_cypress", "tree_cypress_b"]), x, rng.uniform(0.8, 1.0), "back"))
            elif roll < 0.69:
                out.append(("tree_dead", x, rng.uniform(0.75, 0.95), "back"))
            elif roll < 0.76:
                out.append(("lily_puddle", x, rng.uniform(0.8, 1.0), "mid"))
            elif roll < 0.82:
                out.append(("firefly_jar", x, rng.uniform(0.85, 1.0), "mid"))
            elif roll < 0.88:
                out.append(("signpost", x, rng.uniform(0.85, 1.0), "back"))
            x += rng.uniform(100, 210)
        return out

    def weather(self) -> Weather:
        # ``colors`` name particle sprites (registered in ``sky_extras``): fireflies drifting in the mist
        return Weather("spores", 0.5, ("hs_firefly", "hs_firefly", "hs_firefly_far"), wind=5.0)


ART_CLASS = HauntedSwamp
