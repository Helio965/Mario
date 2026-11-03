"""Cidade Mecânica: a clockwork steam city at golden dusk.

Identity: an amber-to-violet dusk with a low sun on the left, a giant clock
tower whose glass face glows over the skyline, aqueduct arches and smoking
chimneys on the horizon, drifting steam banks and slow airships. Parallax:
hazy rooftops and little clock towers; brick factories with saw-tooth roofs,
lit windows, copper pipes and gear silhouettes; a quay railing with gas lamps
and cargo. Terrain is a riveted steel deck with a bolted brass trim on top of
red-brick foundations (plate seams, bolts, brick bond, pipe couplings and soot
streaks are functions of the world x); slick floors (``surface == "ice"``) are
polished, oily steel behind yellow-black warning stripes.

Light: the low sun on the left gives a warm rim to left-facing edges; lamps
and furnaces are local warm accents. Steel stays cool and every walkable top
carries a pale highlight, so creatures and ledges read against the warm sky.
"""

from __future__ import annotations

import math
from typing import Sequence

from ..svg import Rand, Svg, blob, mix, rounded_rect_path, shade, smooth_open, star_points
from .base import Layer, PropSpec, Weather, WorldArt

Pt = tuple[float, float]

INK = "#22161e"
BRASS_HI, BRASS_LIGHT, BRASS, BRASS_DARK, BRASS_DEEP = "#fff1c2", "#f4cd72", "#d49a3e", "#956126", "#5a3816"
COPPER_HI, COPPER_LIGHT, COPPER, COPPER_DARK = "#ffd2a8", "#e8935c", "#bf6738", "#73351c"
STEEL_HI, STEEL_LIGHT, STEEL, STEEL_DARK, STEEL_DEEP = "#e9eef6", "#b0bace", "#7c87a2", "#4c536a", "#2b2f40"
BRICK_HI, BRICK, BRICK_DARK, BRICK_DEEP, MORTAR = "#df8160", "#ae4f3a", "#7f352b", "#4c1d1c", "#4a2a2c"
IRON_HI, IRON, IRON_DARK, IRON_DEEP = "#8e8c9c", "#545264", "#34323f", "#1d1c25"
SOOT = "#1a1016"
LAMP_HOT, LAMP, LAMP_DEEP = "#fff7df", "#ffd583", "#ff9c45"
MOLTEN_WHITE, MOLTEN_YELLOW, MOLTEN, MOLTEN_RED = "#fff3c8", "#ffcc4a", "#ff8a2a", "#d8461e"
HAZARD_Y, HAZARD_K = "#f5c43c", "#2b2329"
VERDIGRIS, VERDIGRIS_DARK = "#7cc9b0", "#3e8a78"
TEAL_GLOW = "#7ff3dc"
STEAM = "#f7efe8"

SUN = (196.0, 276.0)


# --------------------------------------------------------------------------- helpers
def _hash(n: int, salt: int = 0) -> float:
    """Stable pseudo-random value in [0, 1] for an integer lattice cell."""
    x = (n * 374761393 + salt * 668265263 + 1013904223) & 0xFFFFFFFF
    x = ((x ^ (x >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((x ^ (x >> 16)) & 0xFFFFFF) / float(0xFFFFFF)


def _line(pts: Sequence[Pt]) -> str:
    return "M" + "L".join(f"{x:.2f} {y:.2f}" for x, y in pts)


def _poly(pts: Sequence[Pt]) -> str:
    return _line(pts) + "Z"


def _grid(x0: float, w: float, step: float, offset: float = 0.0) -> list[tuple[int, float]]:
    """World-aligned grid positions (index, local x) covering [-step, w + step]."""
    k = math.floor((x0 - offset) / step) - 1
    out = []
    while True:
        lx = k * step + offset - x0
        if lx > w + step:
            return out
        out.append((k, lx))
        k += 1


def _keep(lx: float, w: float, left: bool, right: bool, margin: float = 2.0, reach: float = 2.0) -> bool:
    """Whether a world-aligned feature at local x ``lx`` (half-width ``reach``)
    is drawn in a chunk: exposed ends keep ``margin`` clear, interior borders
    let it spill over (the neighbour chunk draws the other half)."""
    lo = margin if left else -reach
    hi = w - margin if right else w + reach
    return lo < lx < hi


def _circle_d(cx: float, cy: float, r: float, ccw: bool = False) -> str:
    sweep = 0 if ccw else 1
    return (f"M{cx + r:.2f} {cy:.2f}A{r:.2f} {r:.2f} 0 1 {sweep} {cx - r:.2f} {cy:.2f}"
            f"A{r:.2f} {r:.2f} 0 1 {sweep} {cx + r:.2f} {cy:.2f}Z")


def _gear_d(cx: float, cy: float, r: float, teeth: int, depth: float = 0.2, hole: float = 0.0, phase: float = 0.0) -> str:
    """Cog outline with trapezoid teeth; ``hole`` > 0 punches an axle hole."""
    ri = r * (1 - depth)
    step = 2 * math.pi / teeth
    pts = []
    for i in range(teeth):
        a0 = phase + step * i
        for frac, rad in ((0.0, ri), (0.13, r), (0.41, r), (0.54, ri)):
            a = a0 + step * frac
            pts.append((cx + math.cos(a) * rad, cy + math.sin(a) * rad))
    d = _poly(pts)
    if hole > 0:
        d += _circle_d(cx, cy, hole, ccw=True)
    return d


def _spokes_d(cx: float, cy: float, r_in: float, r_out: float, n: int, width: float, phase: float = 0.0) -> str:
    """Windows between ``n`` spokes of a wheel (reversed winding: cut out of a gear body)."""
    d = ""
    half = math.asin(min(0.95, width / 2 / max(r_in, 1e-3)))
    for i in range(n):
        a0 = phase + 2 * math.pi * i / n + half + width / max(r_out, 1e-3)
        a1 = phase + 2 * math.pi * (i + 1) / n - half - width / max(r_out, 1e-3)
        if a1 <= a0:
            continue
        pts = [(cx + math.cos(a0) * r_in, cy + math.sin(a0) * r_in)]
        steps = 5
        for k in range(steps + 1):
            a = a0 + (a1 - a0) * k / steps
            pts.append((cx + math.cos(a) * r_out, cy + math.sin(a) * r_out))
        pts.append((cx + math.cos(a1) * r_in, cy + math.sin(a1) * r_in))
        d += _poly(list(reversed(pts)))
    return d


def _soft(s: Svg, cx: float, cy: float, rx: float, ry: float, color: str, alpha: float = 1.0, core: float = 0.0) -> None:
    """Soft-edged glow ellipse (radial falloff made elliptical by a scaled group)."""
    if rx <= 0 or ry <= 0:
        return
    with s.group(transform=f"translate({cx:.2f} {cy:.2f}) scale(1 {ry / rx:.4f})"):
        s.circle(0, 0, rx, fill=s.radial(0, 0, rx, [(0, color, alpha), (core, color, alpha), (1, color, 0)]))


def _halo(s: Svg, cx: float, cy: float, r: float, color: str = LAMP, strength: float = 0.55) -> None:
    s.circle(cx, cy, r, fill=s.radial(cx, cy, r, [(0, color, strength), (0.4, color, strength * 0.4), (1, color, 0)]))


def _rivet(s: Svg, x: float, y: float, r: float = 1.3, body: str = STEEL, rim: str = STEEL_DEEP, hi: str = STEEL_HI) -> None:
    s.circle(x, y, r, fill=body, stroke=rim, width=r * 0.38)
    s.circle(x - r * 0.3, y - r * 0.32, r * 0.42, fill=hi, opacity=0.85)


def _rivets(s: Svg, pts: Sequence[Pt], r: float = 1.3, body: str = STEEL, rim: str = STEEL_DEEP, hi: str = STEEL_HI) -> None:
    """Many rivets as two paths (bodies, glints): nanosvg cost grows with the
    number of shapes, so terrain chunks batch their rivets and bolts."""
    if not pts:
        return
    s.path("".join(_circle_d(x, y, r) for x, y in pts), fill=body, stroke=rim, width=r * 0.38)
    s.path("".join(_circle_d(x - r * 0.3, y - r * 0.32, r * 0.42) for x, y in pts), fill=hi, opacity=0.85)


def _dots(s: Svg, pts: Sequence[Pt], r: float, fill: str, opacity: float = 1.0) -> None:
    if pts:
        s.path("".join(_circle_d(x, y, r) for x, y in pts), fill=fill, opacity=opacity)


def _clip(poly: Sequence[Pt], x0: float, y0: float, x1: float, y1: float) -> list[Pt]:
    """Clip a convex polygon to an axis-aligned rectangle (Sutherland-Hodgman)."""
    def cut(pts: list[Pt], inside, cross) -> list[Pt]:
        out: list[Pt] = []
        for i, cur in enumerate(pts):
            prev = pts[i - 1]
            if inside(cur):
                if not inside(prev):
                    out.append(cross(prev, cur))
                out.append(cur)
            elif inside(prev):
                out.append(cross(prev, cur))
        return out

    def at_x(x: float):
        return lambda p, q: (x, p[1] + (q[1] - p[1]) * (x - p[0]) / ((q[0] - p[0]) or 1e-9))

    def at_y(y: float):
        return lambda p, q: (p[0] + (q[0] - p[0]) * (y - p[1]) / ((q[1] - p[1]) or 1e-9), y)

    pts = list(poly)
    for inside, cross in ((lambda p: p[0] >= x0, at_x(x0)), (lambda p: p[0] <= x1, at_x(x1)),
                          (lambda p: p[1] >= y0, at_y(y0)), (lambda p: p[1] <= y1, at_y(y1))):
        if not pts:
            break
        pts = cut(pts, inside, cross)
    return pts


def _hazard(s: Svg, x: float, y: float, w: float, h: float, gx: float = 0.0, step: float = 6.0,
            yellow: str = HAZARD_Y, black: str = HAZARD_K, opacity: float = 1.0) -> None:
    """Yellow-black diagonal warning stripes filling a rectangle; the stripes
    are aligned to ``gx`` (world x of the rectangle's left edge)."""
    s.rect(x, y, w, h, fill=yellow, opacity=opacity)
    slant = h * 0.9
    d = ""
    k = math.floor((gx - slant) / (2 * step)) - 1
    while True:
        a = k * 2 * step - gx + x
        if a > x + w:
            break
        pts = _clip([(a, y + h), (a + step, y + h), (a + step + slant, y), (a + slant, y)], x, y, x + w, y + h)
        if len(pts) >= 3:
            d += _poly(pts)
        k += 1
    if d:
        s.path(d, fill=black, opacity=opacity)


def _plume(s: Svg, x: float, y: float, length: float, width: float, seed: int, color: str = "#e8c8c0", alpha: float = 0.5,
           drift: float = 0.6, lit: str = "#ffcf9a") -> None:
    """Smoke or steam rising from (x, y) and bending downwind (to the right)."""
    r = Rand(seed)
    n = max(4, int(length / (width * 0.55)))
    for i in range(n):
        t = i / (n - 1)
        px = x + length * drift * t * t + r.uniform(-2, 2) * width * 0.1
        py = y - length * t * (1 - 0.35 * t)
        rad = width * (0.35 + 0.9 * t)
        a = alpha * (1 - t) ** 1.2
        _soft(s, px, py, rad, rad * 0.8, color, a, 0.25)
        if i % 2 == 0:
            _soft(s, px - rad * 0.25, py + rad * 0.3, rad * 0.6, rad * 0.4, lit, a * 0.45, 0.2)


def _chain(s: Svg, x1: float, y1: float, x2: float, y2: float, link: float = 3.6, color: str = IRON_DARK, width: float = 1.0,
           hi: str = IRON_HI) -> None:
    """Straight chain from (x1, y1) to (x2, y2): alternating face-on and edge-on links."""
    ln = math.hypot(x2 - x1, y2 - y1)
    n = max(1, int(ln / link))
    ang = math.atan2(y2 - y1, x2 - x1)
    ca, sa = math.cos(ang), math.sin(ang)
    for i in range(n):
        t = (i + 0.5) / n
        x, y = x1 + (x2 - x1) * t, y1 + (y2 - y1) * t
        if i % 2 == 0:
            rx, ry = link * 0.62, link * 0.36
            s.raw(f'<ellipse cx="{x:.2f}" cy="{y:.2f}" rx="{rx:.2f}" ry="{ry:.2f}" transform="rotate({math.degrees(ang):.1f} {x:.2f} {y:.2f})" '
                  f'fill="none" stroke="{color}" stroke-width="{width:.2f}"/>')
            s.line(x - ca * rx * 0.4 + sa * ry * 0.5, y - sa * rx * 0.4 - ca * ry * 0.5, x + ca * rx * 0.2 + sa * ry * 0.5,
                   y + sa * rx * 0.2 - ca * ry * 0.5, hi, width * 0.5, 0.7)
        else:
            s.line(x - ca * link * 0.55, y - sa * link * 0.55, x + ca * link * 0.55, y + sa * link * 0.55, color, width * 1.3)


def _gauge(s: Svg, cx: float, cy: float, r: float, needle: float = -40.0, face: str = "#fbf3dc", glow: bool = False,
           rim: str = BRASS) -> None:
    """Round pressure gauge: brass bezel, ticks, red zone and needle (degrees from straight up)."""
    if glow:
        _halo(s, cx, cy, r * 2.6, TEAL_GLOW, 0.7)
    s.circle(cx, cy, r, fill=s.linear(cx - r, cy - r, cx + r, cy + r, [(0, BRASS_HI), (0.5, rim), (1, BRASS_DEEP)]), stroke=INK,
             width=r * 0.14)
    inner = r * 0.74
    fill = s.radial(cx - inner * 0.3, cy - inner * 0.3, inner * 1.4, [(0, "#ffffff"), (0.5, TEAL_GLOW), (1, "#2fb8a0")]) if glow else face
    s.circle(cx, cy, inner, fill=fill)
    ticks = ""
    for k in range(7):
        a = math.radians(-120 + k * 40)
        ticks += (f"M{cx + math.sin(a) * inner * 0.72:.2f} {cy - math.cos(a) * inner * 0.72:.2f}"
                  f"L{cx + math.sin(a) * inner * 0.92:.2f} {cy - math.cos(a) * inner * 0.92:.2f}")
    s.path(ticks, stroke="#3a2a2a" if not glow else "#0e4a40", width=max(0.25, r * 0.07))
    a0, a1 = math.radians(60), math.radians(115)
    s.path(f"M{cx + math.sin(a0) * inner * 0.82:.2f} {cy - math.cos(a0) * inner * 0.82:.2f}"
           f"A{inner * 0.82:.2f} {inner * 0.82:.2f} 0 0 1 {cx + math.sin(a1) * inner * 0.82:.2f} {cy - math.cos(a1) * inner * 0.82:.2f}",
           stroke="#d8402e", width=max(0.3, r * 0.12))
    a = math.radians(needle)
    s.line(cx - math.sin(a) * inner * 0.15, cy + math.cos(a) * inner * 0.15, cx + math.sin(a) * inner * 0.8, cy - math.cos(a) * inner * 0.8,
           "#b8241c" if not glow else "#0b3a33", max(0.35, r * 0.13))
    s.circle(cx, cy, r * 0.13, fill=INK)
    s.path(f"M{cx - inner * 0.6:.2f} {cy - inner * 0.35:.2f} Q{cx - inner * 0.2:.2f} {cy - inner * 0.85:.2f} {cx + inner * 0.35:.2f} {cy - inner * 0.65:.2f}",
           stroke="#ffffff", width=max(0.3, r * 0.1), opacity=0.7)


def _handwheel(s: Svg, cx: float, cy: float, r: float, color: str = "#c8382c", dark: str = "#6a1a16", spokes: int = 5,
               phase: float = 0.3) -> None:
    """Valve handwheel seen face-on: rim, spokes and hub."""
    s.circle(cx, cy, r, fill=None, stroke=INK, width=r * 0.42)
    s.circle(cx, cy, r, fill=None, stroke=color, width=r * 0.26)
    d = ""
    for k in range(spokes):
        a = phase + 2 * math.pi * k / spokes
        d += f"M{cx:.2f} {cy:.2f}L{cx + math.cos(a) * r:.2f} {cy + math.sin(a) * r:.2f}"
    s.path(d, stroke=INK, width=r * 0.24)
    s.path(d, stroke=dark, width=r * 0.12)
    s.circle(cx, cy, r * 0.28, fill=color, stroke=INK, width=r * 0.1)
    s.path(f"M{cx - r * 0.8:.2f} {cy - r * 0.45:.2f} A{r:.2f} {r:.2f} 0 0 1 {cx - r * 0.1:.2f} {cy - r * 0.98:.2f}", stroke="#ff9a8a",
           width=r * 0.08, opacity=0.8)


# --------------------------------------------------------------------------- world
class ClockworkCity(WorldArt):
    id = "clockwork_city"
    name = "Cidade Mecânica"
    accent = "#d9a441"
    terrain_headroom = 24.0
    ambient = (255, 244, 230)
    vignette = 0.3
    wind_tint = (250, 244, 240)  # lateral steam jets read as white steam, not sand
    provisional = False

    # ------------------------------------------------------------------ sky
    def sky(self) -> Svg:
        s = Svg(960, 540)
        s.rect(0, 0, 960, 540, fill=s.linear(0, 0, 0, 540, [(0, "#2a2150"), (0.18, "#43306c"), (0.36, "#7a4679"), (0.52, "#bb5e6c"),
                                                            (0.66, "#e6865a"), (0.8, "#f9b45f"), (1, "#ffd99a")]))
        r = Rand(3)
        for _ in range(30):  # early stars in the violet zenith
            x, y = r.uniform(0, 960), r.uniform(4, 150)
            s.circle(x, y, r.uniform(0.5, 1.3), fill="#fff1e6", opacity=r.uniform(0.25, 0.75) * (1 - y / 180))
        sx, sy = SUN
        s.circle(sx, sy, 470, fill=s.radial(sx, sy, 470, [(0, "#ffe3a2", 0.62), (0.28, "#ffb46a", 0.26), (1, "#ff9a5a", 0)]))
        # long cirrus streaks: gold underside, mauve top
        for y, xa, xb, th in ((96, 420, 1010, 4.0), (132, -60, 470, 5.5), (176, 300, 900, 4.5), (214, -40, 560, 6.5),
                              (250, 620, 1010, 4.0)):
            top = [(xa + (xb - xa) * k / 8, y + 2.4 * math.sin(k * 1.3 + y)) for k in range(9)]
            low = [(px, py + th * (0.3 + 0.7 * math.sin(math.pi * k / 8))) for k, (px, py) in enumerate(top)]
            veil = s.linear(xa, 0, xb, 0, [(0, "#ffb38a", 0), (0.3, "#ffc79a", 0.5), (0.7, "#f2a6a0", 0.4), (1, "#f2a6a0", 0)])
            s.path(smooth_open(top) + "L" + smooth_open(list(reversed(low)))[1:] + "Z", fill=veil)
        s.circle(sx, sy, 92, fill=s.radial(sx, sy, 92, [(0, "#fff8e4", 0.95), (0.4, "#ffe8b0", 0.45), (1, "#ffd08a", 0)]))
        s.circle(sx, sy, 40, fill=s.radial(sx - 9, sy - 11, 46, [(0, "#fffcf2"), (0.55, "#ffeab4"), (1, "#ffc676")]))
        for y, th, a in ((sy - 8, 2.6, 0.55), (sy + 7, 3.4, 0.5), (sy + 21, 2.2, 0.4)):
            s.rect(sx - 80, y, 160, th, fill=s.linear(sx - 80, 0, sx + 80, 0, [(0, "#f08a64", 0), (0.5, "#e2785e", a), (1, "#f08a64", 0)]))
        self._horizon(s)
        self._clock_tower(s, 612.0, 214.0, 40.0)
        s.rect(0, 360, 960, 180, fill=s.linear(0, 360, 0, 540, [(0, "#ffcf8e", 0), (0.55, "#ffcb88", 0.42), (1, "#f6b072", 0.85)]))
        return s

    def _horizon(self, s: Svg) -> None:
        """Far horizon: an aqueduct striding across the setting sun on a hazy
        ridge, and factory chimneys trailing long smoke on the right."""
        haze, haze_dark, lit = "#c9767e", "#b8687a", "#ffcfa0"
        ridge = [(-20, 300), (80, 268), (200, 258), (330, 262), (430, 276), (520, 300)]
        s.path(smooth_open(ridge) + "L520 340L-20 340Z", fill=haze, opacity=0.8)
        deck = 236.0
        x_end = 470.0
        d = f"M-10 {deck:.1f}L{x_end:.1f} {deck:.1f}L{x_end:.1f} 330"
        x = x_end
        while x > -10:
            d += f"L{x - 8:.1f} 330L{x - 8:.1f} {deck + 24:.1f}A15 15 0 0 0 {x - 38:.1f} {deck + 24:.1f}L{x - 38:.1f} 330"
            x -= 38.0
        d += "L-10 330Z"
        s.path(d, fill=haze_dark, opacity=0.92)
        s.rect(-10, deck - 5, x_end + 14, 5, fill=haze_dark, opacity=0.92)
        s.line(-10, deck - 4.6, x_end + 4, deck - 4.6, lit, 1.0, 0.7)
        for cx, top, wd, smoke in ((700, 252, 11, 200), (748, 272, 9, 150), (880, 244, 12, 140), (930, 280, 9, 90)):
            _plume(s, cx, top - 4, smoke, wd * 1.4, int(cx), color="#c99aa6", alpha=0.42, drift=0.7, lit="#ffd0a0")
            s.polygon([(cx - wd * 0.62, 340), (cx - wd * 0.5, top), (cx + wd * 0.5, top), (cx + wd * 0.62, 340)], fill=haze_dark, opacity=0.9)
            s.rect(cx - wd * 0.62, top - 4, wd * 1.24, 5, fill=haze_dark, opacity=0.9)
            s.line(cx - wd * 0.5 + 0.8, top + 2, cx - wd * 0.6 + 0.8, 340, "#f6b090", 1.2, 0.5)

    def _clock_tower(self, s: Svg, cx: float, cy: float, rad: float) -> None:
        """The city's great clock: a slender tower with a backlit glass face,
        cog-toothed rim, belfry and a gear finial (original design). Hazy
        violet like the far rooftops, so it stays a distant landmark."""
        k = rad / 60.0
        body, body_lit, band = "#87507a", "#b8687a", "#76436c"
        base_w = rad * 1.5
        # shaft with pilasters and lit slit windows
        s.polygon([(cx - base_w * 0.62, 560), (cx - base_w * 0.5, cy + rad + 20 * k), (cx + base_w * 0.5, cy + rad + 20 * k), (cx + base_w * 0.62, 560)],
                  fill=body)
        s.polygon([(cx - base_w * 0.62, 560), (cx - base_w * 0.5, cy + rad + 20 * k), (cx - base_w * 0.36, cy + rad + 20 * k), (cx - base_w * 0.44, 560)],
                  fill=body_lit, opacity=0.5)
        for f in (-0.2, 0.06, 0.32):
            s.line(cx + base_w * f, cy + rad + 30 * k, cx + base_w * f * 1.18, 520, band, 2.0 * k, 0.7)
        for y in (cy + rad + 70 * k, cy + rad + 130 * k):
            s.rect(cx - base_w * 0.56, y, base_w * 1.12, 5 * k, fill=band, opacity=0.8)
            for f in (-0.3, -0.1, 0.1, 0.3):
                x = cx + base_w * f
                s.path(f"M{x - 4 * k:.1f} {y + 34 * k:.1f} L{x - 4 * k:.1f} {y + 18 * k:.1f} Q{x:.1f} {y + 12 * k:.1f} {x + 4 * k:.1f} {y + 18 * k:.1f} "
                       f"L{x + 4 * k:.1f} {y + 34 * k:.1f} Z", fill="#ffcf8a", opacity=0.5)
        # face housing, belfry and roof
        hw = rad + 16 * k
        s.rect(cx - hw, cy - rad - 16 * k, hw * 2, rad * 2 + 38 * k, fill=body)
        s.rect(cx - hw, cy - rad - 16 * k, 7 * k, rad * 2 + 38 * k, fill=body_lit, opacity=0.55)
        s.rect(cx - hw - 5 * k, cy + rad + 16 * k, hw * 2 + 10 * k, 7 * k, fill=band)
        s.rect(cx - hw - 5 * k, cy - rad - 22 * k, hw * 2 + 10 * k, 7 * k, fill=band)
        bw = rad * 0.92
        s.rect(cx - bw, cy - rad - 70 * k, bw * 2, 50 * k, fill=body)
        for f in (-1, 0, 1):
            ax = cx + f * bw * 0.62
            s.path(f"M{ax - 9 * k:.1f} {cy - rad - 26 * k:.1f} L{ax - 9 * k:.1f} {cy - rad - 50 * k:.1f} Q{ax:.1f} {cy - rad - 62 * k:.1f} "
                   f"{ax + 9 * k:.1f} {cy - rad - 50 * k:.1f} L{ax + 9 * k:.1f} {cy - rad - 26 * k:.1f} Z", fill="#ffd9a0", opacity=0.6)
            s.path(f"M{ax - 6 * k:.1f} {cy - rad - 40 * k:.1f} Q{ax:.1f} {cy - rad - 50 * k:.1f} {ax + 6 * k:.1f} {cy - rad - 40 * k:.1f} "
                   f"L{ax + 5 * k:.1f} {cy - rad - 32 * k:.1f} L{ax - 5 * k:.1f} {cy - rad - 32 * k:.1f} Z", fill=body)
        s.rect(cx - bw - 6 * k, cy - rad - 76 * k, bw * 2 + 12 * k, 8 * k, fill=band)
        roof_top = cy - rad - 116 * k
        s.polygon([(cx - bw - 4 * k, cy - rad - 74 * k), (cx, roof_top), (cx + bw + 4 * k, cy - rad - 74 * k)], fill=body)
        s.polygon([(cx - bw - 4 * k, cy - rad - 74 * k), (cx, roof_top), (cx - bw * 0.35, cy - rad - 74 * k)], fill=body_lit, opacity=0.5)
        s.line(cx, roof_top, cx, roof_top - 18 * k, body, 2.4 * k)
        s.path(_gear_d(cx, roof_top - 22 * k, 8 * k, 8, 0.3, hole=2.6 * k), fill=body)
        # the glass face: backlit amber, rose-window mullions, cog rim, hands
        _halo(s, cx, cy, rad * 1.7, "#ffcf8a", 0.26)
        s.path(_gear_d(cx, cy, rad + 11 * k, 40, 0.11), fill=band)
        s.circle(cx, cy, rad + 3 * k, fill="#8f5578")
        s.circle(cx, cy, rad, fill=s.radial(cx - rad * 0.25, cy - rad * 0.3, rad * 1.25, [(0, "#ffe9c4"), (0.55, "#f8c48e"), (1, "#e2926e")]))
        mull = ""
        for i in range(12):
            a = 2 * math.pi * i / 12
            mull += f"M{cx + math.cos(a) * rad * 0.3:.1f} {cy + math.sin(a) * rad * 0.3:.1f}L{cx + math.cos(a) * rad:.1f} {cy + math.sin(a) * rad:.1f}"
        s.path(mull, stroke="#a2597a", width=1.6 * k, opacity=0.5)
        s.circle(cx, cy, rad * 0.3, fill=None, stroke="#a2597a", width=1.6 * k, opacity=0.5)
        s.circle(cx, cy, rad * 0.82, fill=None, stroke="#8a4a6e", width=2.2 * k, opacity=0.75)
        ticks = ""
        for i in range(12):
            a = 2 * math.pi * i / 12
            r0 = rad * (0.82 if i % 3 == 0 else 0.87)
            ticks += f"M{cx + math.cos(a) * r0:.1f} {cy + math.sin(a) * r0:.1f}L{cx + math.cos(a) * rad * 0.96:.1f} {cy + math.sin(a) * rad * 0.96:.1f}"
        s.path(ticks, stroke=band, width=3.2 * k)
        for ang, ln, wd in ((215.0, 0.52, 5.0 * k), (300.0, 0.78, 3.4 * k)):  # hour ~ 6:50, minute hand
            a = math.radians(ang - 90)
            tip = (cx + math.cos(a) * rad * ln, cy + math.sin(a) * rad * ln)
            nx, ny = -math.sin(a) * wd / 2, math.cos(a) * wd / 2
            s.polygon([(cx - math.cos(a) * 8 * k + nx, cy - math.sin(a) * 8 * k + ny), (tip[0] + nx * 0.3, tip[1] + ny * 0.3),
                       (tip[0] + math.cos(a) * 5 * k, tip[1] + math.sin(a) * 5 * k), (tip[0] - nx * 0.3, tip[1] - ny * 0.3),
                       (cx - math.cos(a) * 8 * k - nx, cy - math.sin(a) * 8 * k - ny)], fill="#64365c")
        s.circle(cx, cy, 5 * k, fill="#64365c")
        s.path(f"M{cx - rad * 0.7:.1f} {cy - rad * 0.45:.1f} A{rad * 0.84:.1f} {rad * 0.84:.1f} 0 0 1 {cx - rad * 0.1:.1f} {cy - rad * 0.82:.1f}",
               stroke="#ffffff", width=2.0 * k, opacity=0.3)

    def _steam_bank(self, seed: int, w: float, h: float) -> Svg:
        """Drifting steam/smoke bank: violet body, warm sunset underside."""
        r = Rand(seed)
        s = Svg(w, h)
        n = 7
        lobes = []
        for i in range(n):
            t = i / (n - 1)
            ry = h * (0.17 + 0.17 * math.sin(math.pi * t)) + r.uniform(-2, 2)
            rx = ry * r.uniform(1.5, 2.1)
            cx = w * (0.12 + 0.76 * t) + r.uniform(-6, 6)
            cy = h * 0.55 - ry * 0.3 + r.uniform(-3, 3)
            lobes.append((cx, cy, min(rx, cx, w - cx), ry))
        for cx, cy, rx, ry in lobes:
            _soft(s, cx, cy + ry * 0.45, rx, ry * 0.7, "#ffb27a", 0.55, 0.3)
        for cx, cy, rx, ry in lobes:
            _soft(s, cx, cy, rx, ry, "#b9849e", 0.8, 0.5)
        for cx, cy, rx, ry in lobes[1:-1:2]:
            _soft(s, cx - rx * 0.15, cy - ry * 0.3, rx * 0.55, ry * 0.45, "#e8c0c4", 0.5, 0.2)
        return s

    def _airship(self) -> Svg:
        """Small, hazy airship far away, heading right; its belly catches the sunset."""
        s = Svg(104, 44)
        body, lit = "#74496e", "#e09a78"
        env = "M9 15 C16 4 44 3 70 4 C88 5 99 9 100 15 C99 21 88 25 70 26 C44 27 16 26 9 15 Z"
        s.path(env, fill=s.linear(0, 3, 0, 27, [(0, "#83567c"), (0.6, body), (1, "#9a5a6c")]))
        s.path("M15 20 C32 26 62 27 86 24 C93 23 98 19 99.5 16", stroke=lit, width=1.4, opacity=0.8)
        for x in (26, 40, 54, 68, 82):
            s.path(f"M{x} 4.6 Q{x + 2.6} 15 {x} 25.4", stroke="#8e6288", width=0.7, opacity=0.8)
        s.polygon([(10, 15), (1, 5), (6, 5), (17, 11)], fill=body)
        s.polygon([(10, 15), (1, 25), (6, 25), (17, 19)], fill=body)
        for x in (44, 64):
            s.line(x, 25.5, x + 2.4, 31, body, 0.8)
        s.path(rounded_rect_path(41, 30, 28, 6, 2.6), fill=body)
        for i in range(4):
            s.rect(44.5 + i * 5.6, 32, 2.6, 2, fill=LAMP, opacity=0.85)
        _halo(s, 55, 33, 10, LAMP, 0.2)
        return s

    def sky_extras(self) -> dict[str, PropSpec]:
        return {
            "cc.cloud.0": PropSpec(lambda: self._steam_bank(13, 300, 86), (0, 0)),
            "cc.cloud.1": PropSpec(self._airship, (0, 0)),
            "cc.cloud.2": PropSpec(lambda: self._steam_bank(29, 230, 70), (0, 0)),
        }

    # ------------------------------------------------------------------ parallax layers
    def _far(self, seed: int) -> Svg:
        """Hazy rooftops: two rows of houses, domes, spires and little clock
        towers with lit windows (wrap-around copies make the strip tile)."""
        w, h = 1200.0, 300.0
        s = Svg(w, h)
        r = Rand(seed)
        rows = (("#bd7888", "#e8a690", 0.4, (72.0, 128.0), 0.0), ("#8e526e", "#d07e78", 0.85, (98.0, 156.0), 1.0))
        for back, rim, win_alpha, (top_a, top_b), depth in rows:
            x = r.uniform(0, 20)
            items = []
            while x < w - 10:
                bw = r.uniform(34, 78) if depth else r.uniform(46, 110)
                items.append((x, bw, r.uniform(top_a, top_b), r.next(), r.next()))
                x += bw + r.uniform(-6, 10)
            for bx, bw, top, kind, seed2 in items:
                for shift in (-w, 0.0, w):
                    if bx + shift > w or bx + bw + shift < 0:
                        continue
                    self._far_building(s, bx + shift, bw, top, kind, seed2, back, rim, win_alpha, depth, h)
            if not depth:
                s.rect(0, 150, w, 150, fill=back)
        s.rect(0, 130, w, 170, fill=s.linear(0, 130, 0, 300, [(0, "#f6b88a", 0), (0.55, "#f2a884", 0.32), (1, "#e89482", 0.6)]))
        return s

    def _far_building(self, s: Svg, x: float, bw: float, top: float, kind: float, seed: float, fill: str, rim: str,
                      win_alpha: float, depth: float, bottom: float) -> None:
        r = Rand(seed * 1000 + 7)
        s.rect(x, top, bw, bottom - top, fill=fill)
        s.line(x + 0.6, top, x + 0.6, bottom, rim, 1.2, 0.55)
        cx = x + bw / 2
        if kind < 0.28:  # pitched roof with dormer
            s.polygon([(x - 3, top + 1), (cx, top - bw * 0.42), (x + bw + 3, top + 1)], fill=fill)
            s.line(x - 3, top + 1, cx, top - bw * 0.42, rim, 1.2, 0.5)
        elif kind < 0.42:  # dome with a lantern
            s.path(f"M{x + 2:.1f} {top + 1:.1f} Q{x + 2:.1f} {top - bw * 0.55:.1f} {cx:.1f} {top - bw * 0.55:.1f} "
                   f"Q{x + bw - 2:.1f} {top - bw * 0.55:.1f} {x + bw - 2:.1f} {top + 1:.1f} Z", fill=fill)
            s.rect(cx - 3, top - bw * 0.55 - 12, 6, 12, fill=fill)
            s.polygon([(cx - 4, top - bw * 0.55 - 12), (cx, top - bw * 0.55 - 20), (cx + 4, top - bw * 0.55 - 12)], fill=fill)
        elif kind < 0.56 and depth:  # little clock tower
            tw = min(bw * 0.5, 24)
            s.rect(cx - tw / 2, top - 46, tw, 47, fill=fill)
            s.polygon([(cx - tw / 2 - 3, top - 46), (cx, top - 64), (cx + tw / 2 + 3, top - 46)], fill=fill)
            s.circle(cx, top - 32, tw * 0.34, fill="#ffd89a", opacity=0.85)
            s.line(cx, top - 32, cx, top - 32 - tw * 0.24, fill, 1.2)
            s.line(cx, top - 32, cx + tw * 0.18, top - 32, fill, 1.2)
        elif kind < 0.72:  # chimneys
            for k in range(1 + int(r.next() * 2)):
                ch_x = x + bw * (0.2 + 0.45 * k)
                s.rect(ch_x, top - 16 - k * 4, 6, 17 + k * 4, fill=fill)
                if depth and r.next() < 0.5:
                    _plume(s, ch_x + 3, top - 20 - k * 4, 60, 7, int(seed * 77 + k), color="#d8a8b0", alpha=0.35, drift=1.0)
        elif kind < 0.84:  # water tank on stilts
            s.line(cx - bw * 0.25, top, cx - bw * 0.2, top - 12, fill, 2)
            s.line(cx + bw * 0.25, top, cx + bw * 0.2, top - 12, fill, 2)
            s.rect(cx - bw * 0.28, top - 30, bw * 0.56, 19, fill=fill)
            s.polygon([(cx - bw * 0.3, top - 30), (cx, top - 40), (cx + bw * 0.3, top - 30)], fill=fill)
        else:  # spire
            s.polygon([(cx - 6, top + 1), (cx, top - 54), (cx + 6, top + 1)], fill=fill)
        rows = int((bottom - top - 12) / 13)
        cols = max(1, int((bw - 8) / 9))
        for row in range(min(rows, 9)):
            for col in range(cols):
                if r.next() < 0.26:
                    s.rect(x + 5 + col * 9, top + 9 + row * 13, 3.6, 5.5, fill="#ffd28a", opacity=win_alpha * r.uniform(0.5, 0.95))

    def _mid(self, idx: int) -> Svg:
        """Brick factories: saw-tooth roofs, arched lit windows, chimneys with
        smoke, copper pipes and big gear silhouettes. Nothing crosses the strip
        edges, so the two variants tile in any order."""
        w, h = 1100.0, 300.0
        s = Svg(w, h)
        r = Rand(21 + idx * 17)
        wall, wall_lit, roof, win = "#5e2f3c", "#9a4b4c", "#4a2434", "#ffcd78"
        layout = [(30, 250, 150, "saw"), (300, 130, 120, "chimney"), (460, 280, 165, "hall"), (770, 150, 130, "tank"), (950, 130, 140, "gear")]
        if idx % 2:
            layout = [(40, 210, 120, "gear"), (270, 260, 160, "saw"), (550, 150, 128, "chimney"), (740, 320, 150, "hall")]
        for bx, bw, top, kind in layout:
            bx += r.uniform(-12, 12)
            self._factory(s, r, bx, bw, top, kind, h, wall, wall_lit, roof, win)
        # copper pipes linking neighbours (horizontal runs with elbows down to the ground)
        for k in range(len(layout) - 1):
            ax = layout[k][0] + layout[k][1] - 10
            bxp = layout[k + 1][0] + 14
            if bxp - ax < 30:
                continue
            py = r.uniform(190, 232)
            self._pipe_run(s, ax, bxp, py, h - 30)
        s.rect(0, h - 34, w, 34, fill="#3a1e2c")
        s.line(0, h - 34, w, h - 34, "#8a4448", 1.4, 0.7)
        s.rect(0, 120, w, 180, fill=s.linear(0, 120, 0, 300, [(0, "#f0a07a", 0), (0.6, "#d0786a", 0.18), (1, "#a85a5e", 0.3)]))
        return s

    def _factory(self, s: Svg, r: Rand, bx: float, bw: float, top: float, kind: str, h: float, wall: str, wall_lit: str, roof: str,
                 win: str) -> None:
        base = h - 30
        if kind == "chimney":
            cx = bx + bw * 0.5
            _plume(s, cx + 4, top - 70, 130, 15, int(bx), color="#c8a0aa", alpha=0.45, drift=0.8)
            s.polygon([(cx - 13, base), (cx - 9, top - 64), (cx + 9, top - 64), (cx + 13, base)], fill="#6a3440")
            s.line(cx - 9, top - 62, cx - 13, base, wall_lit, 1.6, 0.6)
            for y in (top - 64, top - 50):
                s.rect(cx - 12, y - 3, 24, 5, fill="#4a2232")
        s.rect(bx, top, bw, base - top, fill=wall)
        s.rect(bx, top, 5, base - top, fill=wall_lit, opacity=0.65)
        for y in range(int(top) + 8, int(base), 7):
            s.line(bx + 2, y, bx + bw - 2, y, "#4a2230", 0.7, 0.35)
        if kind in ("saw", "hall"):
            n = max(2, int(bw / 48))
            tw = bw / n
            for k in range(n):
                x0 = bx + k * tw
                s.polygon([(x0, top + 1), (x0, top - 26), (x0 + tw, top + 1)], fill=roof)
                s.polygon([(x0 + 1.5, top - 1), (x0 + 1.5, top - 22), (x0 + 6, top - 18), (x0 + 6, top - 1)], fill=win, opacity=0.8)
                s.line(x0, top - 26, x0 + tw, top + 1, wall_lit, 1.2, 0.5)
        elif kind == "tank":
            cx = bx + bw * 0.5
            for lx in (-0.3, -0.1, 0.1, 0.3):
                s.line(cx + bw * lx, top, cx + bw * lx * 0.8, top - 26, "#3e1e2c", 2.4)
            s.path(rounded_rect_path(cx - bw * 0.32, top - 58, bw * 0.64, 34, 4), fill="#6a3a3e")
            s.polygon([(cx - bw * 0.34, top - 58), (cx, top - 72), (cx + bw * 0.34, top - 58)], fill=roof)
            for y in (top - 50, top - 40, top - 30):
                s.line(cx - bw * 0.32, y, cx + bw * 0.32, y, "#4a2632", 1.0, 0.8)
        else:
            s.rect(bx - 3, top - 6, bw + 6, 7, fill=roof)
        # arched windows, some lit
        cols = max(1, int((bw - 16) / 26))
        gap = (bw - cols * 14) / (cols + 1)
        rows = 2 if base - top > 120 else 1
        for row in range(rows):
            wy = top + 22 + row * 52
            for c in range(cols):
                wx = bx + gap + c * (14 + gap)
                lit = r.next() < 0.7
                d = f"M{wx:.1f} {wy + 34:.1f} L{wx:.1f} {wy + 7:.1f} Q{wx + 7:.1f} {wy - 2:.1f} {wx + 14:.1f} {wy + 7:.1f} L{wx + 14:.1f} {wy + 34:.1f} Z"
                if lit:
                    _halo(s, wx + 7, wy + 18, 20, "#ffb060", 0.22)
                s.path(d, fill=win if lit else "#3a1a2a", opacity=0.92 if lit else 0.9)
                s.path(f"M{wx + 7:.1f} {wy:.1f}L{wx + 7:.1f} {wy + 34:.1f}M{wx:.1f} {wy + 18:.1f}L{wx + 14:.1f} {wy + 18:.1f}", stroke=wall, width=1.4)
        if kind == "gear":
            gx, gy, gr = bx + bw * 0.55, top + 4, min(42.0, bw * 0.24)
            body = _gear_d(gx, gy, gr, 14, 0.16, hole=gr * 0.16) + _spokes_d(gx, gy, gr * 0.24, gr * 0.68, 5, gr * 0.12)
            s.path(body, fill="#6e3a48")
            s.path(f"M{gx - gr * 0.95:.1f} {gy - gr * 0.3:.1f} A{gr:.1f} {gr:.1f} 0 0 1 {gx - gr * 0.3:.1f} {gy - gr * 0.95:.1f}", stroke="#e0906a",
                   width=1.4, opacity=0.6)
            sg = gr * 0.5
            s.path(_gear_d(gx - gr - sg * 0.6, gy + gr * 0.5, sg, 9, 0.2, hole=sg * 0.25, phase=0.2), fill="#74404c")

    def _pipe_run(self, s: Svg, x0: float, x1: float, y: float, ground: float) -> None:
        """Copper pipe crossing between two buildings, dropping to the ground at both ends."""
        d = f"M{x0:.1f} {ground:.1f} L{x0:.1f} {y + 8:.1f} Q{x0:.1f} {y:.1f} {x0 + 8:.1f} {y:.1f} L{x1 - 8:.1f} {y:.1f} Q{x1:.1f} {y:.1f} {x1:.1f} {y + 8:.1f} L{x1:.1f} {ground:.1f}"
        s.path(d, stroke="#4a2228", width=7.5)
        s.path(d, stroke="#b8643c", width=5.5)
        s.path(f"M{x0 + 8:.1f} {y - 1.4:.1f} L{x1 - 8:.1f} {y - 1.4:.1f}", stroke="#f0a46c", width=1.4, opacity=0.8)
        k = x0 + 40
        while k < x1 - 30:
            s.rect(k, y - 4.5, 4, 9, fill="#7a3a26")
            k += 60
        if x1 - x0 > 90:
            _gauge(s, (x0 + x1) / 2, y - 9, 4.5, -20, face="#e8d0b0")

    def _near(self, idx: int) -> Svg:
        """Quay wall with an iron railing, gas lamps and cargo (dark, low detail)."""
        w, h = 900.0, 230.0
        s = Svg(w, h)
        r = Rand(41 + idx * 13)
        sil, rim = "#2e1a26", "#a85a4c"
        top = 128.0
        # cargo silhouettes in front of the railing
        x = r.uniform(70, 160)
        while x < w - 80:
            kind = r.next()
            if kind < 0.45:
                for k in range(int(r.uniform(1, 3))):
                    cw = r.uniform(22, 30)
                    s.rect(x + k * (cw - 2), top - cw * 0.9 - (cw * 0.85 if k == 1 and r.next() < 0.5 else 0), cw, cw * 0.9, fill=sil)
                    s.line(x + k * (cw - 2) + 0.8, top - cw * 0.9, x + k * (cw - 2) + 0.8, top, rim, 1.0, 0.5)
            elif kind < 0.75:
                for k in range(2):
                    s.path(rounded_rect_path(x + k * 17, top - 24, 15, 24, 3), fill=sil)
                    s.line(x + k * 17 + 1, top - 20, x + k * 17 + 1, top - 2, rim, 1.0, 0.45)
            x += r.uniform(140, 260)
        # railing
        posts = 60.0
        bal = ""
        for k in range(int(w / 10)):
            bx = 5 + k * 10
            bal += f"M{bx:.1f} {top - 30:.1f}L{bx:.1f} {top:.1f}"
        s.path(bal, stroke=sil, width=1.6)
        s.rect(0, top - 34, w, 4.5, fill=sil)
        s.line(0, top - 34, w, top - 34, rim, 1.0, 0.45)
        s.rect(0, top - 14, w, 3, fill=sil)
        for k in range(int(w / posts)):
            px = 30 + k * posts
            s.rect(px - 3, top - 40, 6, 40, fill=sil)
            s.circle(px, top - 42, 3.4, fill=sil)
        # gas lamps
        for lx in ((180.0, 620.0) if idx % 2 == 0 else (90.0, 470.0, 800.0)):
            _halo(s, lx, top - 84, 38, LAMP, 0.42)
            s.rect(lx - 2.2, top - 76, 4.4, 76, fill=sil)
            s.path(f"M{lx - 6:.1f} {top:.1f} L{lx - 4:.1f} {top - 10:.1f} L{lx + 4:.1f} {top - 10:.1f} L{lx + 6:.1f} {top:.1f} Z", fill=sil)
            s.path(f"M{lx - 7:.1f} {top - 76:.1f} L{lx + 7:.1f} {top - 76:.1f} L{lx + 5:.1f} {top - 92:.1f} L{lx - 5:.1f} {top - 92:.1f} Z",
                   fill="#ffd690")
            s.polygon([(lx - 8, top - 92), (lx, top - 99), (lx + 8, top - 92)], fill=sil)
            s.line(lx - 2.2 + 0.8, top - 74, lx - 2.2 + 0.8, top - 12, rim, 1.0, 0.5)
        # quay wall
        s.rect(0, top, w, h - top, fill=s.linear(0, top, 0, h, [(0, "#3c2230"), (0.5, "#2a1822"), (1, "#24141c")]))
        s.rect(0, top - 2, w, 7, fill="#4a2a36")
        s.line(0, top - 1.6, w, top - 1.6, rim, 1.2, 0.55)
        for y in range(int(top) + 16, int(h), 14):
            s.line(0, y, w, y, "#1c0f16", 1.0, 0.5)
        return s

    def layer_art(self) -> dict[str, PropSpec]:
        art = {"cc.far.0": PropSpec(lambda: self._far(7), (0, 0))}
        for i in range(2):
            art[f"cc.mid.{i}"] = PropSpec((lambda i=i: self._mid(i)), (0, 0))
            art[f"cc.near.{i}"] = PropSpec((lambda i=i: self._near(i)), (0, 0))
        return art

    def layers(self) -> list[Layer]:
        return [
            Layer("far", 0.06, ["cc.far.0"], 1200, 62, vertical=0.05),
            Layer("mid", 0.22, ["cc.mid.0", "cc.mid.1"], 1100, 60, vertical=0.15),
            Layer("near", 0.5, ["cc.near.0", "cc.near.1"], 900, 108, vertical=0.32),
        ]

    # ------------------------------------------------------------------ terrain
    def terrain(self, style: str, w: float, h: float, seed: int, left: bool, right: bool, top: bool = True, x0: float = 0.0,
                surface: str = "normal") -> Svg:
        """Terrain chunk art. Everything that crosses chunk borders (plate
        seams, bolts, brick bond, pipe couplings, stripes, soot streaks) is a
        function of the world x (``x0`` + local x), so adjacent chunks join
        seamlessly; only the hanging edges are outlined, never the chunk's
        vertical borders."""
        if style == "cave":
            return self._tunnel(w, h, seed, left, right, x0)
        if style == "fortress":
            return self._foundry(w, h, left, right, top, x0)
        hr = self.terrain_headroom
        s = Svg(w, h + hr)
        y0 = hr
        self._brickwork(s, w, h, y0, x0, left, right, deep=True)
        if top:
            self._deck(s, w, y0, left, right, x0, surface)
        return s

    def _brickwork(self, s: Svg, w: float, h: float, y0: float, x0: float, left: bool, right: bool, deep: bool,
                   tones: tuple[str, str, str] = (BRICK, BRICK_DARK, BRICK_DEEP), mortar: str = MORTAR, pipe: bool = True) -> None:
        """Red factory brick (running bond, world-aligned) with soot and rust streaks."""
        bottom = y0 + h
        b0, b1, b2 = tones
        # one gradient carries the soot under the deck and the darkness with depth
        # (separate full-chunk overlays are the costliest thing nanosvg can draw)
        depth = [(0, mix(b0, SOOT, 0.62)), (0.16, mix(b0, SOOT, 0.12)), (0.3, b0), (0.62, b1)]
        depth += [(0.85, mix(b2, SOOT, 0.35)), (1, mix(b2, SOOT, 0.62))] if deep else [(1, b2)]
        s.rect(0, y0, w, h, fill=s.linear(0, y0, 0, y0 + 170, depth))
        course, brick = 9.0, 22.0
        top_row = y0 + 13.0
        detail = min(bottom, y0 + 158.0)  # below this the bond is lost in the dark
        rows = int((detail - top_row) / course) + 1
        mortar_d, hi_d, tone_d, dark_d = "", "", "", ""
        for row in range(rows):
            y = top_row + row * course
            if y > detail:
                break
            mortar_d += f"M0 {y:.2f}L{w:.2f} {y:.2f}"
            off = (row % 2) * brick / 2
            for k, lx in _grid(x0, w, brick, off):
                if -1 < lx < w + 1:
                    mortar_d += f"M{lx:.2f} {y:.2f}L{lx:.2f} {min(bottom, y + course):.2f}"
                a, b = max(0.0, lx + 1.0), min(w, lx + brick - 1.0)
                if b - a < 2 or y < y0 + 20 or y > y0 + 112:
                    continue
                hi_d += f"M{a:.2f} {y + 1.4:.2f}L{b:.2f} {y + 1.4:.2f}"
                v = _hash(k * 31 + row * 7, 5)
                if v < 0.16:
                    tone_d += f"M{a:.2f} {y + 0.6:.2f}L{b:.2f} {y + 0.6:.2f}L{b:.2f} {y + course - 0.6:.2f}L{a:.2f} {y + course - 0.6:.2f}Z"
                elif v > 0.86:
                    dark_d += f"M{a:.2f} {y + 0.6:.2f}L{b:.2f} {y + 0.6:.2f}L{b:.2f} {y + course - 0.6:.2f}L{a:.2f} {y + course - 0.6:.2f}Z"
        if tone_d:
            s.path(tone_d, fill=BRICK_HI if b0 == BRICK else shade(b0, 0.18), opacity=0.32)
        if dark_d:
            s.path(dark_d, fill=SOOT, opacity=0.3)
        s.path(hi_d, stroke=shade(b0, 0.32), width=0.9, opacity=0.45)
        s.path(mortar_d, stroke=mortar, width=1.2, opacity=0.9)
        # rust and soot streaks below the deck seams (world-aligned)
        streak = ""
        for k, lx in _grid(x0, w, 48.0):
            if _hash(k, 41) < 0.45 or not 3 < lx < w - 3:
                continue
            ln = 14 + 26 * _hash(k, 42)
            streak += f"M{lx - 1:.2f} {y0 + 13:.2f}Q{lx - 1.6:.2f} {y0 + 13 + ln * 0.6:.2f} {lx - 0.6:.2f} {y0 + 13 + ln:.2f}"
        if streak:
            s.path(streak, stroke="#8a4a2a", width=1.6, opacity=0.45)
        # a copper service pipe runs along the foundation (couplings every 120 u)
        if pipe and h > 72:
            py = y0 + 40
            s.rect(0, py - 4.6, w, 9.2, fill=s.linear(0, py - 4.6, 0, py + 4.6, [(0, COPPER_LIGHT), (0.35, COPPER), (1, COPPER_DARK)]))
            s.line(0, py - 2.6, w, py - 2.6, COPPER_HI, 1.0, 0.7)
            s.line(0, py + 4.6, w, py + 4.6, INK, 0.9, 0.6)
            s.rect(0, py + 4.8, w, 3, fill=SOOT, opacity=0.3)
            bolts = []
            for k, lx in _grid(x0, w, 120.0, 30.0):
                if not -8 < lx < w + 8:
                    continue
                s.rect(lx - 3.5, py - 6.4, 7, 12.8, fill=s.linear(lx - 3.5, 0, lx + 3.5, 0, [(0, COPPER_HI), (0.5, COPPER), (1, COPPER_DARK)]),
                       stroke=INK, width=0.8, rx=1.2)
                bolts += [(lx, py - 4), (lx, py + 4)]
                if _hash(k, 43) < 0.35 and 12 < lx + 40 < w - 12:
                    vx = lx + 40
                    s.rect(vx - 2, py - 11, 4, 7, fill=STEEL_DARK, stroke=INK, width=0.6)
                    _handwheel(s, vx, py - 13, 4.2, spokes=4)
                if _hash(k, 44) < 0.3 and 8 < lx + 75 < w - 8:  # verdigris stain
                    s.path(blob(lx + 75, py + 0.6, 7, 2.6, 0.25, seed=k), fill=VERDIGRIS_DARK, opacity=0.7)
                    s.path(blob(lx + 74, py - 0.2, 4.2, 1.4, 0.25, seed=k + 1), fill=VERDIGRIS, opacity=0.8)
            _dots(s, bolts, 0.9, BRASS_HI)
        # exposed foundation ends: an angle-iron corner post with rivets
        for exposed, edge, inner in ((left, 0.0, 6.0), (right, w, w - 6.0)):
            if not exposed:
                continue
            a = min(edge, inner)
            s.rect(a, y0 + 10, 6, h - 10, fill=s.linear(a, 0, a + 6, 0, [(0, STEEL_DARK), (0.4, STEEL_LIGHT), (1, STEEL_DARK)]))
            s.line(edge + (0.6 if edge == 0 else -0.6), y0 + 10, edge + (0.6 if edge == 0 else -0.6), bottom, INK, 1.4)
            _rivets(s, [(a + 3, y0 + 22 + 16 * i) for i in range(int((bottom - 4 - y0 - 22) / 16) + 1)], 1.1)
            s.rect(a + (6 if edge == 0 else -6), y0 + 10, 6, h - 10, fill=s.linear(a, 0, a + 12, 0, [(0, SOOT, 0.35), (1, SOOT, 0)]) if edge == 0
                   else s.linear(w - 12, 0, w - 6, 0, [(0, SOOT, 0), (1, SOOT, 0.4)]))

    def _deck(self, s: Svg, w: float, y0: float, left: bool, right: bool, x0: float, surface: str) -> None:
        """Riveted steel deck plates with a bolted brass trim (the walkable top)."""
        slick = surface == "ice"
        sticky = surface == "sticky"
        il = 1.2 if left else 0.0
        ir = w - 1.2 if right else w
        top, band, trim = y0 - 0.8, 10.0, 4.0
        if slick:
            plate = s.linear(0, top, 0, top + band, [(0, "#ffffff"), (0.16, "#e2ecf6"), (0.42, "#b2c2d6"), (0.58, "#5e6e8a"), (0.78, "#8ea0ba"),
                                                     (1, "#56647e")])
        elif sticky:
            plate = s.linear(0, top, 0, top + band, [(0, "#8a6a4a"), (0.3, "#4a3424"), (1, "#2a1c16")])
        else:
            plate = s.linear(0, top, 0, top + band, [(0, STEEL_HI), (0.22, STEEL_LIGHT), (0.6, STEEL), (1, STEEL_DARK)])
        corner = 2.2
        body = [(il, top + corner if left else top), (il + (corner if left else 0), top), (ir - (corner if right else 0), top),
                (ir, top + corner if right else top), (ir, top + band + trim), (il, top + band + trim)]
        # cast shadow of the deck on the brick
        s.rect(il, top + band + trim, ir - il, 5, fill=s.linear(0, top + band + trim, 0, top + band + trim + 5, [(0, SOOT, 0.55), (1, SOOT, 0)]))
        s.path(_poly(body), fill=plate)
        seams = _grid(x0, w, 48.0)
        if not slick and not sticky:
            # patched brass plates and darker worn plates
            for k, lx in seams:
                a, b = max(il, lx + 0.8), min(ir, lx + 48 - 0.8)
                if b - a < 3:
                    continue
                v = _hash(k, 11)
                if v < 0.22:
                    s.rect(a, top + 0.4, b - a, band - 0.6, fill=s.linear(0, top, 0, top + band, [(0, BRASS_HI), (0.3, BRASS_LIGHT), (0.7, BRASS),
                                                                                                    (1, BRASS_DARK)]))
                elif v > 0.8:
                    s.rect(a, top + 2.5, b - a, band - 2.6, fill=STEEL_DARK, opacity=0.25)
            # scuffs where feet wear the plates (world-aligned)
            scuff = ""
            for k, lx in _grid(x0, w, 13.0):
                if _hash(k, 13) < 0.55 or not il + 3 < lx < ir - 9:
                    continue
                ln = 3 + 6 * _hash(k, 14)
                yy = top + 1.6 + 2.2 * _hash(k, 15)
                scuff += f"M{lx:.2f} {yy:.2f}L{min(ir - 2, lx + ln):.2f} {yy + 0.2:.2f}"
            if scuff:
                s.path(scuff, stroke="#ffffff", width=0.6, opacity=0.45)
        elif slick:
            # oily sheen bands and long specular streaks
            for k, lx in _grid(x0, w, 37.0):
                v = _hash(k, 17)
                if v < 0.35:
                    continue
                gx = lx + 20 * _hash(k, 18)
                wd = 5 + 8 * _hash(k, 19)
                pts = _clip([(gx, top + band - 1), (gx + wd, top + band - 1), (gx + wd + 6, top + 0.8), (gx + 6, top + 0.8)], il, top, ir, top + band)
                if len(pts) >= 3:
                    s.path(_poly(pts), fill="#ffffff", opacity=0.7)
                if v > 0.62 and _keep(gx + 22, w, left, right, 12.0, 12.0):
                    cx = gx + 22
                    for j, col in enumerate(("#d070e0", "#50e0d0", "#f8c848")):
                        s.path(f"M{cx - 10 + j:.2f} {top + 5.2 + j * 1.2:.2f}Q{cx + 1:.2f} {top + 3.2 + j * 1.2:.2f} {cx + 12 - j:.2f} {top + 5.1 + j * 1.2:.2f}",
                               stroke=col, width=1.2, opacity=0.55)
        else:
            for k, lx in _grid(x0, w, 21.0):
                if _hash(k, 23) < 0.5 or not il + 4 < lx < ir - 12:
                    continue
                s.path(blob(lx + 4, top + 1.5, 4 + 3 * _hash(k, 24), 1.8, 0.2, seed=k), fill="#a8845a", opacity=0.7)
        # plate seams with bolts on both sides
        seam_d, seam_hi = "", ""
        for k, lx in seams:
            if not _keep(lx, w, left, right, 1.5, 1.0):
                continue
            seam_d += f"M{lx:.2f} {top + 0.6:.2f}L{lx:.2f} {top + band:.2f}"
            seam_hi += f"M{lx + 0.9:.2f} {top + 0.8:.2f}L{lx + 0.9:.2f} {top + band - 0.3:.2f}"
        s.path(seam_d, stroke=INK, width=0.9, opacity=0.8)
        s.path(seam_hi, stroke="#ffffff", width=0.6, opacity=0.5)
        if not sticky:
            _rivets(s, [(bx, top + band * 0.55) for k, lx in seams for bx in (lx - 3.4, lx + 3.4) if _keep(bx, w, left, right, 2.0, 1.5)], 1.15,
                    body=STEEL_LIGHT if not slick else "#d8e4f0")
        # brass trim strip (hazard stripes on slick floors), bolt heads world-aligned
        ty = top + band
        if slick:
            _hazard(s, il, ty, ir - il, trim + 0.4, gx=x0 + il, step=5.0)
        else:
            s.rect(il, ty, ir - il, trim, fill=s.linear(0, ty, 0, ty + trim, [(0, BRASS_LIGHT), (0.45, BRASS), (1, BRASS_DARK)]))
            bolts = [(k, lx) for k, lx in _grid(x0, w, 16.0, 8.0) if _keep(lx, w, left, right, 2.0, 1.0)]
            _dots(s, [(lx, ty + trim / 2) for k, lx in bolts if k % 3], 0.95, BRASS_HI)
            _dots(s, [(lx, ty + trim / 2) for k, lx in bolts if not k % 3], 0.95, BRASS_DEEP)
        s.line(il, ty, ir, ty, INK, 0.8, 0.7)
        # oil drips on slick floors (world-aligned)
        if slick:
            drips = ""
            for k, lx in _grid(x0, w, 29.0):
                if _hash(k, 27) < 0.55 or not il + 3 < lx < ir - 3:
                    continue
                ln = 6 + 16 * _hash(k, 28)
                y1 = ty + trim
                drips += f"M{lx - 1.3:.2f} {y1:.2f}Q{lx - 1:.2f} {y1 + ln * 0.7:.2f} {lx:.2f} {y1 + ln:.2f}Q{lx + 1:.2f} {y1 + ln * 0.7:.2f} {lx + 1.3:.2f} {y1:.2f}Z"
            if drips:
                s.path(drips, fill="#2a2a3a", opacity=0.6)
        # hanging edge outline, exposed ends, top highlight
        s.line(il, ty + trim, ir, ty + trim, INK, 1.3)
        if left:
            s.path(_line([(il, ty + trim), (il, top + corner), (il + corner, top)]), stroke=INK, width=1.3)
        if right:
            s.path(_line([(ir, ty + trim), (ir, top + corner), (ir - corner, top)]), stroke=INK, width=1.3)
        s.line(il + (corner if left else 0), top + 0.5, ir - (corner if right else 0), top + 0.5, "#ffffff" if not sticky else "#c8a070", 1.1,
               0.95 if slick else 0.8)
        s.line(il + (corner if left else 0), top + 1.6, ir - (corner if right else 0), top + 1.6, STEEL_HI if not sticky else "#6a4a30", 0.6, 0.6)

    def _foundry(self, w: float, h: float, left: bool, right: bool, top: bool, x0: float) -> Svg:
        """Iron foundry walls: dark riveted iron panels warmed by the furnaces."""
        hr = self.terrain_headroom
        s = Svg(w, h + hr)
        y0 = hr
        bottom = y0 + h
        s.rect(0, y0, w, h, fill=s.linear(0, y0, 0, y0 + 200, [(0, "#4a4656"), (0.3, "#34323f"), (0.65, "#22212a"), (1, "#121118")]))
        pw, ph = 60.0, 40.0
        seam, hi, rivets = "", "", []
        rows = int((min(h, 172.0) - 12) / ph) + 1  # deeper panels are lost in the dark
        for row in range(rows):
            y = y0 + 12 + row * ph
            if y > bottom - 2:
                break
            off = (row % 2) * pw / 2
            seam += f"M0 {y:.2f}L{w:.2f} {y:.2f}"
            hi += f"M0 {y + 1.4:.2f}L{w:.2f} {y + 1.4:.2f}"
            for k, lx in _grid(x0, w, pw, off):
                if -1 < lx < w + 1:
                    seam += f"M{lx:.2f} {y:.2f}L{lx:.2f} {min(bottom, y + ph):.2f}"
                    hi += f"M{lx + 1.2:.2f} {y + 1.4:.2f}L{lx + 1.2:.2f} {min(bottom, y + ph):.2f}"
                for fx in (0.12, 0.5, 0.88):
                    rx = lx + pw * fx
                    if _keep(rx, w, left, right, 3.0, 2.0) and y + 5 < bottom - 2:
                        rivets.append((rx, y + 5))
                v = _hash(k * 13 + row, 61)
                if v < 0.2 and lx + 6 > 0 and lx + pw - 6 < w + pw:
                    a, b = max(0.0, lx + 3), min(w, lx + pw - 3)
                    if b - a > 6:
                        s.rect(a, y + 3, b - a, min(ph - 6, bottom - y - 4), fill="#6a5a7a" if v < 0.1 else "#5a4048", opacity=0.22)
        s.path(hi, stroke="#7a7688", width=1.0, opacity=0.5)
        s.path(seam, stroke="#0e0d13", width=1.6, opacity=0.9)
        _rivets(s, rivets, 1.5, body=IRON, rim=IRON_DEEP, hi=IRON_HI)
        for exposed, edge in ((left, 0.0), (right, w)):
            if exposed:
                a = 0.0 if edge == 0 else w - 7
                s.rect(a, y0, 7, h, fill=s.linear(a, 0, a + 7, 0, [(0, IRON_DARK), (0.5, IRON), (1, IRON_DEEP)]))
                s.line(edge + (0.8 if edge == 0 else -0.8), y0, edge + (0.8 if edge == 0 else -0.8), bottom, INK, 1.6)
        if top:
            s.rect(0, y0 - 1, w, 10, fill=s.linear(0, y0 - 1, 0, y0 + 9, [(0, "#b8b4c4"), (0.35, IRON_HI), (0.7, IRON), (1, IRON_DARK)]))
            _hazard(s, 0, y0 + 9, w, 3.4, gx=x0, step=5.0, opacity=0.9)
            s.line(0, y0 + 12.4, w, y0 + 12.4, INK, 1.3)
            s.line(0, y0 - 0.4, w, y0 - 0.4, "#f2eee8", 1.2, 0.9)
            _rivets(s, [(lx, y0 + 4) for k, lx in _grid(x0, w, 24.0, 12.0) if _keep(lx, w, left, right, 2.0, 2.0)], 1.5, body=IRON_HI, rim=IRON_DEEP,
                    hi="#ffffff")
            s.rect(0, y0 + 13, w, 6, fill=s.linear(0, y0 + 13, 0, y0 + 19, [(0, SOOT, 0.5), (1, SOOT, 0)]))
        return s

    def _tunnel(self, w: float, h: float, seed: int, left: bool, right: bool, x0: float) -> Svg:
        """Maintenance tunnel masonry: sooty brick, a cable conduit and pipes;
        the walkway rim on top is always drawn (cave floors are often covered
        by the room walls standing on them); thin slabs are ceilings."""
        hr = self.terrain_headroom
        s = Svg(w, h + hr)
        y0 = hr
        bottom = y0 + h
        r = Rand(seed)
        self._brickwork(s, w, h, y0, x0, left, right, deep=True, tones=("#6a3c3c", "#4a2a30", "#2a181e"), mortar="#24141a", pipe=False)
        if h > 50:
            for py, wd, col in ((y0 + 26, 4.0, STEEL), (y0 + 33, 3.0, "#3e6a5a")):
                if py + 4 > bottom - 4:
                    continue
                s.rect(0, py - wd / 2, w, wd, fill=s.linear(0, py - wd / 2, 0, py + wd / 2, [(0, shade(col, 0.4)), (1, shade(col, -0.35))]))
                s.line(0, py + wd / 2, w, py + wd / 2, INK, 0.7, 0.6)
            for k, lx in _grid(x0, w, 80.0, 20.0):
                if 4 < lx < w - 4 and y0 + 38 < bottom - 2:
                    s.rect(lx - 2, y0 + 22, 4, 16, fill=STEEL_DARK, stroke=INK, width=0.6)
            # caged work lamps (chunk-local, kept off the chunk borders)
            for _ in range(int(w / 200)):
                lx = r.uniform(30, w - 30)
                ly = y0 + 48
                if ly + 10 > bottom - 6:
                    break
                _halo(s, lx, ly, 26, LAMP, 0.5)
                s.rect(lx - 3, ly - 8, 6, 3, fill=STEEL_DARK, stroke=INK, width=0.6)
                s.path(rounded_rect_path(lx - 4, ly - 5, 8, 10, 3), fill=s.radial(lx, ly, 6, [(0, LAMP_HOT), (0.6, LAMP), (1, LAMP_DEEP)]),
                       stroke=INK, width=0.7)
                s.path(f"M{lx - 4:.1f} {ly - 1:.1f}L{lx + 4:.1f} {ly - 1:.1f}M{lx - 4:.1f} {ly + 2.5:.1f}L{lx + 4:.1f} {ly + 2.5:.1f}M{lx:.1f} {ly - 5:.1f}L{lx:.1f} {ly + 5:.1f}",
                       stroke=INK, width=0.7)
        # damp streaks
        for _ in range(max(1, int(w / 90))):
            dx = r.uniform(8, w - 8)
            s.path(f"M{dx:.1f} {y0 + 12:.1f}Q{dx - 1:.1f} {y0 + 40:.1f} {dx + 0.5:.1f} {min(bottom - 2, y0 + 70):.1f}", stroke="#1a1218", width=2.4,
                   opacity=0.35)
        # steel walkway rim
        s.rect(0, y0 - 1, w, 7, fill=s.linear(0, y0 - 1, 0, y0 + 6, [(0, STEEL_LIGHT), (0.5, STEEL), (1, STEEL_DEEP)]))
        grate = ""
        for k, lx in _grid(x0, w, 6.0):
            if 0 < lx < w:
                grate += f"M{lx:.2f} {y0 + 1.5:.2f}L{lx - 2:.2f} {y0 + 5:.2f}"
        s.path(grate, stroke=STEEL_DEEP, width=0.9, opacity=0.8)
        s.line(0, y0 - 0.4, w, y0 - 0.4, STEEL_HI, 1.1, 0.9)
        s.line(0, y0 + 6, w, y0 + 6, INK, 1.1)
        if h <= 100:
            # ceilings: a pipe and drips along the underside
            py = bottom - 5
            s.rect(0, py - 2.5, w, 5, fill=s.linear(0, py - 2.5, 0, py + 2.5, [(0, "#8a9ab0"), (1, "#3a4258")]))
            for k, lx in _grid(x0, w, 34.0):
                if _hash(k, 71) > 0.5 and 3 < lx < w - 3:
                    ln = 3 + 5 * _hash(k, 72)
                    s.path(f"M{lx - 1:.2f} {py + 2.4:.2f}Q{lx:.2f} {py + 2.4 + ln:.2f} {lx + 1:.2f} {py + 2.4:.2f}Z", fill="#9ad0e8", opacity=0.7)
        if left:
            s.line(0.8, y0, 0.8, bottom, INK, 1.6)
        if right:
            s.line(w - 0.8, y0, w - 0.8, bottom, INK, 1.6)
        return s

    def cave_sky(self) -> Svg:
        """Maintenance tunnel: a brick vault receding into the dark, pipe
        bundles along the walls, caged lamps and drifting steam."""
        s = Svg(960, 540)
        s.rect(0, 0, 960, 540, fill="#1a1016")
        vx, vy = 480.0, 250.0
        # receding vault ribs: every rib is one annulus of a single merged path, shaded
        # by a radial gradient (near ribs catch the lamp light, far ones sink into the dark)
        ribs, rims = "", ""
        for k in range(7):
            t = k / 6
            rw, rh, th = 520 - 380 * t, 330 - 230 * t, 13 - 9 * t
            ribs += (f"M{vx - rw - th:.1f} 560 L{vx - rw - th:.1f} {vy:.1f} A{rw + th:.1f} {rh + th:.1f} 0 0 1 {vx + rw + th:.1f} {vy:.1f} "
                     f"L{vx + rw + th:.1f} 560 L{vx + rw - th:.1f} 560 L{vx + rw - th:.1f} {vy:.1f} "
                     f"A{rw - th:.1f} {rh - th:.1f} 0 0 0 {vx - rw + th:.1f} {vy:.1f} L{vx - rw + th:.1f} 560 Z")
            rims += (f"M{vx - rw - th:.1f} {vy:.1f} A{rw + th:.1f} {rh + th:.1f} 0 0 1 {vx + rw + th:.1f} {vy:.1f} "
                     f"L{vx + rw + th - 1.8:.1f} {vy:.1f} A{rw + th - 1.8:.1f} {rh + th - 1.8:.1f} 0 0 0 {vx - rw - th + 1.8:.1f} {vy:.1f} Z")
        s.path(ribs, fill=s.radial(vx, vy + 40, 560, [(0, "#1c1216"), (0.45, "#33202a"), (1, "#4e2e32")]))
        s.path(rims, fill="#8a4c40", opacity=0.6)
        _soft(s, vx, vy + 40, 90, 70, "#ffb46a", 0.28, 0.1)
        s.path(f"M{vx - 40:.1f} 560 L{vx - 40:.1f} {vy + 30:.1f} A40 34 0 0 1 {vx + 40:.1f} {vy + 30:.1f} L{vx + 40:.1f} 560 Z", fill="#ffcf8a", opacity=0.2)
        # pipe bundles converging toward the vanishing point
        for side in (-1, 1):
            for j, (col, wd, y_near) in enumerate((("#7a4a34", 14, 300), ("#5a6478", 10, 330), ("#3e6a5a", 8, 352))):
                x_near, x_far = vx + side * 540, vx + side * 150
                y_far = vy + 48 + j * 9
                far_w = wd * 0.3
                d = _poly([(x_near, y_near - wd / 2), (x_far, y_far - far_w / 2), (x_far, y_far + far_w / 2), (x_near, y_near + wd / 2)])
                s.path(d, fill=col, stroke="#140c10", width=1.5)
                s.path(_line([(x_near, y_near - wd * 0.25), (x_far, y_far - far_w * 0.25)]), stroke="#ffffff", width=1.2, opacity=0.18)
            for k in range(4):
                t = k / 4
                px = vx + side * (540 - 390 * t)
                s.rect(px - 3 * (1 - t * 0.7), 286 + 26 * t, 6 * (1 - t * 0.7), 74 - 46 * t, fill="#1c1216", opacity=0.9)
        # caged lamps on the vault
        for lx, ly, rr in ((190, 150, 1.0), (770, 150, 1.0), (330, 205, 0.7), (630, 205, 0.7)):
            _halo(s, lx, ly, 70 * rr, LAMP, 0.45)
            s.path(rounded_rect_path(lx - 7 * rr, ly - 9 * rr, 14 * rr, 18 * rr, 5 * rr),
                   fill=s.radial(lx, ly, 10 * rr, [(0, LAMP_HOT), (0.6, LAMP), (1, LAMP_DEEP)]), stroke="#140c10", width=1.4)
            s.path(f"M{lx - 7 * rr:.1f} {ly:.1f}L{lx + 7 * rr:.1f} {ly:.1f}M{lx:.1f} {ly - 9 * rr:.1f}L{lx:.1f} {ly + 9 * rr:.1f}", stroke="#140c10",
                   width=1.4)
            s.polygon([(lx - 10 * rr, ly + 10 * rr), (lx + 10 * rr, ly + 10 * rr), (lx + 70 * rr, 540), (lx - 70 * rr, 540)], fill="#ffd28a",
                      opacity=0.05)
        # steam drifting across the tunnel
        for cx, cy, sz in ((200, 420, 60), (760, 430, 64)):
            _soft(s, cx, cy, sz * 1.5, sz * 0.45, "#c8b0b4", 0.18, 0.3)
        # puddles reflecting the lamps
        for px, pw in ((200, 120), (700, 160)):
            s.ellipse(px, 520, pw, 8, fill="#ffcf8a", opacity=0.08)
        return s

    # ------------------------------------------------------------------ indoor halls
    def interior(self, variant: str):
        if variant == "factory":
            return self._factory_hall, self._factory_layer
        if variant == "fortress":
            return self._foundry_hall, self._foundry_layer
        if variant in ("underground", "sewer", "tunnel"):
            return self.cave_sky, None
        return None

    def _factory_hall(self) -> Svg:
        """Factory hall: roof trusses, a wall of giant gears, furnace glow,
        steam and conveyor silhouettes."""
        s = Svg(960, 540)
        s.rect(0, 0, 960, 540, fill=s.linear(0, 0, 0, 540, [(0, "#1e1420"), (0.45, "#3a2228"), (0.8, "#5a2e2a"), (1, "#3a1e1e")]))
        # back brick wall courses
        d = ""
        for y in range(160, 540, 16):
            d += f"M0 {y}L960 {y}"
        s.path(d, stroke="#2a161c", width=1.2, opacity=0.6)
        # tall windows with dusk light
        for wx in (120, 400, 680):
            s.path(f"M{wx} 330 L{wx} 150 Q{wx + 50} 100 {wx + 100} 150 L{wx + 100} 330 Z",
                   fill=s.linear(0, 110, 0, 330, [(0, "#6a4a7a"), (0.6, "#d07a62"), (1, "#f2a85e")]), opacity=0.85)
            grid = f"M{wx + 50} 116L{wx + 50} 330"
            for gy in (170, 210, 250, 290):
                grid += f"M{wx} {gy}L{wx + 100} {gy}"
            grid += f"M{wx + 25} 128L{wx + 25} 330M{wx + 75} 128L{wx + 75} 330"
            s.path(grid, stroke="#2a161c", width=3)
            s.polygon([(wx, 330), (wx + 100, 330), (wx + 180, 540), (wx - 40, 540)], fill="#ffc888", opacity=0.06)
        # giant gears on the wall
        for gx, gy, gr, teeth, col in ((830, 250, 150, 22, "#3a2228"), (250, 470, 120, 18, "#40262a"), (560, 120, 90, 14, "#36202a")):
            body = _gear_d(gx, gy, gr, teeth, 0.12, hole=gr * 0.12) + _spokes_d(gx, gy, gr * 0.2, gr * 0.72, 6, gr * 0.1)
            s.path(body, fill=col)
            s.path(_gear_d(gx, gy, gr, teeth, 0.12), fill=None, stroke="#8a4a3a", width=2.0, opacity=0.5)
            s.circle(gx, gy, gr * 0.12, fill="#8a5a3a")
        # roof trusses
        for k in range(5):
            x = k * 240 - 20
            s.path(f"M{x} 0 L{x + 120} 70 L{x + 240} 0 M{x + 60} 35 L{x + 60} 0 M{x + 180} 35 L{x + 180} 0 M{x} 70 L{x + 240} 70", stroke="#140c12",
                   width=7)
            s.path(f"M{x} 70 L{x + 240} 70", stroke="#5a3a3a", width=1.4, opacity=0.6)
        # hanging lamps
        for lx in (180, 480, 780):
            s.line(lx, 70, lx, 128, "#140c12", 2)
            _halo(s, lx, 140, 60, LAMP, 0.4)
            s.path(f"M{lx - 16} 140 Q{lx} 120 {lx + 16} 140 Z", fill="#2a1a20")
            s.ellipse(lx, 141, 7, 3, fill=LAMP_HOT)
            s.polygon([(lx - 16, 141), (lx + 16, 141), (lx + 80, 540), (lx - 80, 540)], fill="#ffd28a", opacity=0.05)
        # furnace mouths glowing low on the wall
        for fx in (60, 520, 900):
            _soft(s, fx, 470, 120, 70, MOLTEN, 0.45, 0.1)
            s.path(f"M{fx - 34} 520 L{fx - 34} 470 Q{fx} 440 {fx + 34} 470 L{fx + 34} 520 Z",
                   fill=s.linear(0, 450, 0, 520, [(0, MOLTEN_YELLOW), (0.5, MOLTEN), (1, MOLTEN_RED)]))
            s.path(f"M{fx - 40} 520 L{fx - 40} 468 Q{fx} 432 {fx + 40} 468 L{fx + 40} 520", stroke="#1a1014", width=6)
        # conveyor silhouettes with crates
        for cy, x0, x1 in ((400, 0, 420), (430, 560, 960)):
            s.path(rounded_rect_path(x0, cy, x1 - x0, 12, 6), fill="#1a1016")
            for rx in range(int(x0) + 10, int(x1) - 4, 26):
                s.circle(rx, cy + 6, 4, fill="#3a2a2e")
            for bx in range(int(x0) + 30, int(x1) - 40, 110):
                s.rect(bx, cy - 22, 26, 22, fill="#24161a")
            s.rect(x0 + 10, cy + 12, 6, 60, fill="#1a1016")
            s.rect(x1 - 16, cy + 12, 6, 60, fill="#1a1016")
        for cx, cy, sz in ((300, 300, 60), (640, 260, 50), (900, 380, 70)):
            _soft(s, cx, cy, sz * 2, sz * 0.8, "#e8d0d0", 0.12, 0.3)
        return s

    def _factory_layer(self) -> Svg:
        """Scrolling pipe-and-gear wall (900×420) behind the factory floor."""
        s = Svg(900, 420)
        # vertical and horizontal pipe runs
        for x, col in ((90, "#9a5432"), (110, "#5e6880"), (520, "#9a5432"), (760, "#34584c")):
            s.rect(x - 7, 0, 14, 420, fill=s.linear(x - 7, 0, x + 7, 0, [(0, shade(col, -0.45)), (0.35, shade(col, 0.25)), (1, shade(col, -0.55))]))
            for y in range(30, 420, 90):
                s.rect(x - 9, y, 18, 6, fill=shade(col, -0.3), stroke=INK, width=1.0)
        for y, x0, x1, col in ((120, 0, 520, "#5e6880"), (210, 110, 900, "#9a5432"), (300, 520, 900, "#34584c")):
            s.rect(x0, y - 6, x1 - x0, 12, fill=s.linear(0, y - 6, 0, y + 6, [(0, shade(col, 0.3)), (0.5, col), (1, shade(col, -0.5))]))
            s.line(x0, y + 6, x1, y + 6, INK, 1.0, 0.6)
        _gauge(s, 300, 108, 13, 30)
        _gauge(s, 640, 198, 11, -50)
        _handwheel(s, 180, 210, 12)
        _handwheel(s, 520, 330, 10, color=BRASS, dark=BRASS_DEEP)
        # gear cluster
        for gx, gy, gr, teeth, ph in ((360, 300, 70, 14, 0.0), (448, 236, 40, 9, 0.2), (250, 360, 44, 10, 0.1)):
            s.path(_gear_d(gx, gy, gr, teeth, 0.18, hole=gr * 0.18) + _spokes_d(gx, gy, gr * 0.28, gr * 0.66, 5, gr * 0.12, ph),
                   fill=s.linear(gx - gr, gy - gr, gx + gr, gy + gr, [(0, "#8a6040"), (0.5, "#56402c"), (1, "#30201c")]))
            s.path(_gear_d(gx, gy, gr, teeth, 0.18), fill=None, stroke=INK, width=1.6)
        return s

    def _foundry_hall(self) -> Svg:
        """Iron foundry: dark iron walls, molten-metal channels pouring down
        the back wall, hanging ladles on rails and sparks."""
        s = Svg(960, 540)
        s.rect(0, 0, 960, 540, fill=s.linear(0, 0, 0, 540, [(0, "#0e0c12"), (0.5, "#221a20"), (0.85, "#3a1c18"), (1, "#5a2414")]))
        d = ""
        for y in range(40, 540, 56):
            d += f"M0 {y}L960 {y}"
        for x in range(0, 960, 80):
            d += f"M{x} 0L{x} 540"
        s.path(d, stroke="#08070b", width=2.2, opacity=0.7)
        r = Rand(9)
        for _ in range(60):
            x, y = r.choice(range(0, 960, 80)) + r.choice((10, 70)), r.choice(range(40, 540, 56)) + r.choice((8, 48))
            s.circle(x, y, 2.0, fill="#3a3644")
        # molten channels pouring from spouts and running along the floor
        for fx in (220, 610):
            _soft(s, fx, 300, 60, 260, MOLTEN, 0.3, 0.2)
            s.path(f"M{fx - 26} 96 L{fx + 26} 96 L{fx + 18} 116 L{fx - 18} 116 Z", fill="#2a2630", stroke="#08070b", width=2)
            s.path(f"M{fx - 6} 116 Q{fx - 8} 300 {fx - 10} 470 L{fx + 10} 470 Q{fx + 8} 300 {fx + 6} 116 Z",
                   fill=s.linear(0, 116, 0, 470, [(0, MOLTEN_WHITE), (0.2, MOLTEN_YELLOW), (0.6, MOLTEN), (1, MOLTEN_RED)]))
        s.rect(0, 470, 960, 22, fill=s.linear(0, 470, 0, 492, [(0, MOLTEN_YELLOW), (0.5, MOLTEN), (1, MOLTEN_RED)]))
        _soft(s, 480, 480, 600, 70, MOLTEN, 0.45, 0.2)
        s.rect(0, 492, 960, 48, fill="#120c10")
        # overhead rail with hanging ladles
        s.rect(0, 40, 960, 12, fill="#2a2830")
        s.line(0, 40, 960, 40, "#5a5664", 1.4, 0.8)
        for lx in (110, 420, 820):
            _chain(s, lx - 18, 52, lx - 26, 150, 6, "#1a1820", 2.0, "#5a5664")
            _chain(s, lx + 18, 52, lx + 26, 150, 6, "#1a1820", 2.0, "#5a5664")
            s.path(f"M{lx - 40} 150 L{lx + 40} 150 L{lx + 30} 210 Q{lx} 222 {lx - 30} 210 Z",
                   fill=s.linear(lx - 40, 0, lx + 40, 0, [(0, "#4a4654"), (0.4, "#2a2630"), (1, "#14121a")]), stroke="#08070b", width=2)
            s.ellipse(lx, 150, 40, 7, fill=s.radial(lx, 150, 40, [(0, MOLTEN_WHITE), (0.5, MOLTEN_YELLOW), (1, MOLTEN)]))
            _halo(s, lx, 150, 60, MOLTEN, 0.3)
        for _ in range(50):
            x, y = r.uniform(0, 960), r.uniform(120, 470)
            s.circle(x, y, r.uniform(0.6, 1.6), fill=r.choice([MOLTEN_YELLOW, MOLTEN, MOLTEN_WHITE]), opacity=r.uniform(0.4, 0.9))
        return s

    def _foundry_layer(self) -> Svg:
        """Scrolling iron pillars with crucible braziers (900×420)."""
        s = Svg(900, 420)
        for x in (110, 560):
            s.rect(x, 0, 64, 420, fill=s.linear(x, 0, x + 64, 0, [(0, "#3a3644"), (0.4, "#56526a"), (1, "#18161e")]))
            for y in range(20, 420, 40):
                s.line(x, y, x + 64, y, "#0c0b10", 2.0, 0.8)
                for rx in (x + 8, x + 32, x + 56):
                    s.circle(rx, y + 6, 2.0, fill="#7a7688")
            _hazard(s, x - 4, 250, 72, 10, gx=x, step=7)
            _halo(s, x + 32, 170, 52, MOLTEN, 0.5)
            s.path(f"M{x + 10} 170 L{x + 54} 170 L{x + 46} 196 L{x + 18} 196 Z", fill="#2a2630", stroke=INK, width=1.6)
            s.ellipse(x + 32, 170, 22, 5, fill=s.radial(x + 32, 170, 22, [(0, MOLTEN_WHITE), (0.5, MOLTEN_YELLOW), (1, MOLTEN)]))
        return s

    def gate(self, w: float, h: float) -> Svg:
        """Arena gate: a rolled iron shutter with hazard-striped edges."""
        s = Svg(w, h)
        s.rect(0, 0, w, h, fill=s.linear(0, 0, w, 0, [(0, "#6a6a7a"), (0.4, "#9a9aaa"), (1, "#4a4a58")]), rx=1.5)
        slat = 5.0
        d, hi = "", ""
        y = 3.0
        while y < h - 9:
            d += f"M1.5 {y:.2f}L{w - 1.5:.2f} {y:.2f}"
            hi += f"M1.5 {y + 1.2:.2f}L{w - 1.5:.2f} {y + 1.2:.2f}"
            y += slat
        s.path(hi, stroke="#d8d8e4", width=0.8, opacity=0.6)
        s.path(d, stroke="#26262e", width=1.2)
        side = min(4.0, w * 0.18)
        for x in (0.0, w - side):
            s.rect(x, 0, side, h, fill=s.linear(x, 0, x + side, 0, [(0, IRON_HI), (1, IRON_DARK)]))
            for ry in range(6, int(h) - 6, 14):
                s.circle(x + side / 2, ry, min(1.1, side * 0.3), fill="#e8e6f0")
        _hazard(s, 0, h - 8, w, 8, step=4.0)
        _hazard(s, 0, 0, w, 3.5, step=4.0)
        s.rect(0, 0, w, h, fill=None, stroke=INK, width=1.3, rx=1.5)
        return s

    # ------------------------------------------------------------------ blocks, platforms, pipes
    def block(self, kind: str, w: float, h: float) -> Svg:
        s = Svg(w, h)
        if kind in ("question", "used"):
            self._dial_box(s, w, h, kind == "used")
        elif kind == "brick":
            self._factory_brick(s, w, h)
        else:
            s.path(rounded_rect_path(0.6, 0.6, w - 1.2, h - 1.2, 3), fill=s.linear(0, 0, 0, h, [(0, STEEL_LIGHT), (1, STEEL_DARK)]), stroke=INK,
                   width=1.2)
        return s

    def _dial_box(self, s: Svg, w: float, h: float, used: bool) -> None:
        """Reward block: a riveted brass box with a glowing cog behind a glass
        dial; once used the brass tarnishes and the dial goes dark."""
        if used:
            stops = [(0, "#c0905a"), (0.5, "#8a6238"), (1, "#5a3e22")]
            hi, lo = "#e2b47e", "#3a2414"
        else:
            stops = [(0, BRASS_HI), (0.25, BRASS_LIGHT), (0.7, BRASS), (1, BRASS_DARK)]
            hi, lo = "#fff8e0", BRASS_DEEP
        s.path(rounded_rect_path(0.6, 0.6, w - 1.2, h - 1.2, 3.8), fill=s.linear(0, 0, w * 0.35, h, stops), stroke=INK, width=1.3)
        s.path(f"M3 {h - 3:.2f} L3 3 L{w - 3:.2f} 3", stroke=hi, width=1.1, opacity=0.85)
        s.path(f"M3.4 {h - 2.8:.2f} L{w - 2.8:.2f} {h - 2.8:.2f} L{w - 2.8:.2f} 3.4", stroke=lo, width=1.2, opacity=0.6)
        for cx, cy in ((4.6, 4.6), (w - 4.6, 4.6), (4.6, h - 4.6), (w - 4.6, h - 4.6)):
            _rivet(s, cx, cy, 1.25, body=BRASS if not used else "#8a6238", rim=lo, hi=hi)
        cx, cy = w / 2, h / 2
        rad = min(w, h) * 0.37
        # bezel with ticks
        s.circle(cx, cy, rad + 1.6, fill=s.linear(cx - rad, cy - rad, cx + rad, cy + rad, [(0, lo), (0.5, BRASS_DARK if not used else "#6a4a2a"), (1, hi)]),
                 stroke=INK, width=0.9)
        if used:
            s.circle(cx, cy, rad, fill=s.radial(cx - rad * 0.3, cy - rad * 0.3, rad * 1.4, [(0, "#4a4250"), (0.6, "#2a2430"), (1, "#16121a")]))
            s.path(_gear_d(cx, cy, rad * 0.62, 8, 0.24, hole=rad * 0.2), fill="#3e3640")
            s.path(f"M{cx - rad * 0.6:.2f} {cy - rad * 0.35:.2f} Q{cx - rad * 0.2:.2f} {cy - rad * 0.8:.2f} {cx + rad * 0.3:.2f} {cy - rad * 0.7:.2f}",
                   stroke="#a8a0b8", width=0.8, opacity=0.5)
        else:
            _halo(s, cx, cy, rad * 1.45, "#fff0b0", 0.8)
            s.circle(cx, cy, rad, fill=s.radial(cx - rad * 0.2, cy - rad * 0.25, rad * 1.2, [(0, "#ffffff"), (0.45, "#fff2c0"), (1, "#ffc45c")]))
            s.path(_gear_d(cx, cy, rad * 0.66, 8, 0.24, hole=rad * 0.2, phase=0.2),
                   fill=s.linear(cx - rad, cy - rad, cx + rad, cy + rad, [(0, "#ffd36a"), (0.5, "#e8962a"), (1, "#a8561a")]), stroke="#7a3a10", width=0.7)
            s.circle(cx, cy, rad * 0.2, fill=None, stroke="#7a3a10", width=0.6)
            s.path(f"M{cx - rad * 0.62:.2f} {cy - rad * 0.3:.2f} Q{cx - rad * 0.3:.2f} {cy - rad * 0.82:.2f} {cx + rad * 0.25:.2f} {cy - rad * 0.74:.2f}",
                   stroke="#ffffff", width=1.1, opacity=0.9)
            s.polygon(star_points(cx + rad * 0.55, cy - rad * 0.55, 2.6, 0.6, 4), fill="#ffffff")
        ticks = ""
        for k in range(8):
            a = math.pi * k / 4
            ticks += f"M{cx + math.cos(a) * (rad + 0.2):.2f} {cy + math.sin(a) * (rad + 0.2):.2f}L{cx + math.cos(a) * (rad + 1.5):.2f} {cy + math.sin(a) * (rad + 1.5):.2f}"
        s.path(ticks, stroke=INK, width=0.7, opacity=0.8)
        s.circle(cx, cy, rad, fill=None, stroke=INK, width=0.8)

    def _factory_brick(self, s: Svg, w: float, h: float) -> None:
        """Breakable block: red factory bricks with soot."""
        s.path(rounded_rect_path(0.6, 0.6, w - 1.2, h - 1.2, 2.5), fill="#3a2024", stroke=INK, width=1.2)
        rows = 2
        rh = (h - 2) / rows
        bw = 20.0
        for row in range(rows):
            y = 1 + row * rh
            x = -(bw / 2 if row % 2 else 0.0)
            i = 0
            while x < w:
                bx0, bx1 = max(1.5, x + 1.0), min(w - 1.5, x + bw - 1.0)
                if bx1 > bx0 + 2:
                    tone = _hash(row * 7 + i, 4)
                    s.path(rounded_rect_path(bx0, y + 1.0, bx1 - bx0, rh - 2.0, 1.3),
                           fill=s.linear(0, y, 0, y + rh, [(0, mix(BRICK_HI, "#c8603e", tone)), (0.6, BRICK), (1, BRICK_DARK)]), stroke="#3a1a18", width=0.6)
                    s.line(bx0 + 1, y + 2.1, bx1 - 1, y + 2.1, "#f2a280", 0.9, 0.7)
                    if _hash(row * 11 + i, 6) < 0.5:
                        s.rect(bx0 + 0.6, y + rh * 0.55, bx1 - bx0 - 1.2, rh * 0.38, fill=SOOT, opacity=0.28)
                x += bw
                i += 1
        s.rect(1, 1, w - 2, 5, fill=s.linear(0, 1, 0, 6, [(0, SOOT, 0.35), (1, SOOT, 0)]))

    def platform(self, kind: str, w: float, h: float, style: str = "") -> Svg:
        if kind == "ledge":
            return self._girder(w, h, "float" in style or "suspend" in style)
        if kind == "moving":
            return self._lift(w, h)
        if kind == "crumble":
            return self._rust_grate(w, h)
        if kind == "semisolid":
            return self._catwalk(w, h)
        if kind == "spring":
            return self._piston_spring(w, h)
        return self._conveyor(w, h, style)

    def _girder(self, w: float, h: float, suspended: bool) -> Svg:
        """Ledge: a riveted iron I-beam with a steel walking plate; 'floating'
        ledges hang from cables that run up out of view."""
        hr = self.terrain_headroom
        s = Svg(w, h + hr + 4)
        y0, y1 = hr, hr + h
        if suspended:
            for cx in (min(18.0, w * 0.2), max(w - 18.0, w * 0.8)):
                cable = s.linear(0, 0, 0, y0, [(0, "#2a2630", 0), (0.55, "#2a2630", 0.9), (1, "#2a2630")])
                s.line(cx, 0, cx, y0 + 1, cable, 1.6)
                s.line(cx - 0.5, 0, cx - 0.5, y0 + 1, s.linear(0, 0, 0, y0, [(0, STEEL_HI, 0), (1, STEEL_HI, 0.6)]), 0.5)
                s.path(f"M{cx - 3:.1f} {y0 + 1:.1f} Q{cx - 3.4:.1f} {y0 - 5:.1f} {cx:.1f} {y0 - 5.4:.1f} Q{cx + 3.4:.1f} {y0 - 5:.1f} {cx + 3:.1f} {y0 + 1:.1f}",
                       stroke=INK, width=2.0)
                s.path(f"M{cx - 3:.1f} {y0 + 1:.1f} Q{cx - 3.4:.1f} {y0 - 5:.1f} {cx:.1f} {y0 - 5.4:.1f} Q{cx + 3.4:.1f} {y0 - 5:.1f} {cx + 3:.1f} {y0 + 1:.1f}",
                       stroke=STEEL_LIGHT, width=1.0)
        flange = min(6.0, h * 0.26)
        web_top, web_bot = y0 + flange, y1 - flange
        # web with lightening holes
        web = rounded_rect_path(3, web_top - 0.5, w - 6, web_bot - web_top + 1, 0.5)
        holes = ""
        n = max(1, int((w - 16) / 22))
        hole_r = max(1.5, min((web_bot - web_top) * 0.32, 5.0))
        for k in range(n):
            hx = 8 + (w - 16) * (k + 0.5) / n
            holes += _circle_d(hx, (web_top + web_bot) / 2, hole_r, ccw=True)
        s.path(web + holes, fill=s.linear(0, web_top, 0, web_bot, [(0, IRON_DARK), (0.5, IRON), (1, IRON_DARK)]), stroke=INK, width=0.9)
        for k in range(n):
            hx = 8 + (w - 16) * (k + 0.5) / n
            s.path(f"M{hx - hole_r:.2f} {(web_top + web_bot) / 2:.2f} A{hole_r:.2f} {hole_r:.2f} 0 0 1 {hx + hole_r:.2f} {(web_top + web_bot) / 2:.2f}",
                   stroke=IRON_DEEP, width=1.0, opacity=0.8)
        for k in range(n + 1):  # stiffener plates between the holes
            sx = 8 + (w - 16) * k / n
            s.rect(sx - 1.2, web_top, 2.4, web_bot - web_top, fill=IRON_HI, opacity=0.35)
        # bottom flange
        s.path(rounded_rect_path(0.8, y1 - flange, w - 1.6, flange, 1.2), fill=s.linear(0, y1 - flange, 0, y1, [(0, IRON_HI), (0.4, IRON), (1, IRON_DEEP)]),
               stroke=INK, width=1.1)
        # top flange with the steel walking plate
        s.path(rounded_rect_path(0.8, y0 - 0.8, w - 1.6, flange + 0.8, 1.6),
               fill=s.linear(0, y0 - 0.8, 0, y0 + flange, [(0, STEEL_HI), (0.25, STEEL_LIGHT), (0.7, STEEL), (1, STEEL_DARK)]), stroke=INK, width=1.2)
        s.line(2.5, y0 - 0.1, w - 2.5, y0 - 0.1, "#ffffff", 1.1, 0.85)
        xs = [6.0 + 11.0 * i for i in range(int((w - 10) / 11.0) + 1)]
        _rivets(s, [(x, y0 + flange * 0.55) for x in xs], 1.05, body=STEEL_LIGHT)
        _rivets(s, [(x, y1 - flange * 0.5) for x in xs], 1.0, body=IRON, rim=IRON_DEEP, hi=IRON_HI)
        s.rect(1, y1, w - 2, 3.5, fill=s.linear(0, y1, 0, y1 + 3.5, [(0, SOOT, 0.4), (1, SOOT, 0)]))
        return s

    def _lift(self, w: float, h: float) -> Svg:
        """Moving platform: a gear-driven elevator deck; drive chains loop
        around a cog under the middle."""
        s = Svg(w, h + 16)
        cx, gy = w / 2, h + 3.0
        gr = min(10.0, h * 0.6)
        for side in (-1, 1):
            _chain(s, cx + side * gr * 1.0, h - 1, cx + side * gr * 1.0, h + 15, 4.0, INK, 1.5, IRON_HI)
        s.path(_gear_d(cx, gy, gr, 10, 0.22, hole=gr * 0.22) + _spokes_d(cx, gy, gr * 0.32, gr * 0.62, 4, gr * 0.16),
               fill=s.linear(cx - gr, gy - gr, cx + gr, gy + gr, [(0, BRASS_LIGHT), (0.5, BRASS), (1, BRASS_DEEP)]), stroke=INK, width=0.9)
        s.circle(cx, gy, gr * 0.22, fill=STEEL_DARK, stroke=INK, width=0.6)
        for bx in (w * 0.16, w * 0.84):
            s.path(f"M{bx - 4:.1f} {h - 1:.1f} L{bx + 4:.1f} {h - 1:.1f} L{bx + 1.5:.1f} {h + 5:.1f} L{bx - 1.5:.1f} {h + 5:.1f} Z", fill=IRON_DARK, stroke=INK,
                   width=0.8)
        deck = h - 1.0
        s.path(rounded_rect_path(0.8, 1.0, w - 1.6, deck, 2.6),
               fill=s.linear(0, 1, 0, deck, [(0, STEEL_HI), (0.25, STEEL_LIGHT), (0.65, STEEL), (1, STEEL_DARK)]), stroke=INK, width=1.2)
        band = max(3.0, deck * 0.32)
        s.rect(1.6, deck - band + 0.6, w - 3.2, band - 0.4, fill=s.linear(0, deck - band, 0, deck, [(0, BRASS_LIGHT), (1, BRASS_DARK)]))
        _hazard(s, 1.6, deck - band + 0.6, 9, band - 0.4, step=3.0)
        _hazard(s, w - 10.6, deck - band + 0.6, 9, band - 0.4, gx=w, step=3.0)
        s.line(1.6, deck - band + 0.6, w - 1.6, deck - band + 0.6, INK, 0.7, 0.8)
        s.line(3, 1.9, w - 3, 1.9, "#ffffff", 1.1, 0.85)
        x = 14.0
        while x < w - 12:
            _rivet(s, x, 1 + (deck - band) * 0.55, 1.05, body=STEEL_LIGHT)
            x += 15.0
        return s

    def _rust_grate(self, w: float, h: float) -> Svg:
        """Crumbling platform: a rusted, sagging grate with flaking rust."""
        s = Svg(w, h + 10)
        r = Rand(int(w * 3 + h))
        sag = 2.6

        def low(x: float) -> float:
            return h - 1 + sag * math.sin(math.pi * x / w)

        outline = [(1.0, 1.4), (3.0, 0.4), (w - 3.0, 0.4), (w - 1.0, 1.4)] + [(w - 1.0 - (w - 2) * k / 12, low(w - 1.0 - (w - 2) * k / 12)) for k in range(13)]
        s.path(_poly(outline), fill=s.linear(0, 0, 0, h + sag, [(0, "#c8784a"), (0.35, "#9a5232"), (1, "#5a2c1e")]), stroke=INK, width=1.2)
        # grate openings
        n = max(2, int((w - 10) / 9))
        holes = ""
        for k in range(n):
            x0 = 6 + (w - 12) * k / n
            x1 = x0 + (w - 12) / n - 3.2
            yb = min(low(x0), low(x1)) - 3.2
            if yb - 4.5 > 2:
                holes += _poly([(x0, 4.5), (x1, 4.5), (x1, yb), (x0, yb)])
        if holes:
            s.path(holes, fill="#2a1410", opacity=0.9)
        s.line(3, 1.4, w - 3, 1.4, "#f0b080", 1.0, 0.85)
        # rust bloom and a bent bar
        for _ in range(int(w / 16)):
            px, py = r.uniform(4, w - 4), r.uniform(1.5, h - 2)
            s.path(blob(px, py, r.uniform(2, 4.5), r.uniform(1.2, 2.4), 0.3, seed=px), fill=r.choice(["#e0904e", "#6a2a18", "#b05a2a"]), opacity=0.7)
        bx = r.uniform(w * 0.3, w * 0.7)
        s.path(f"M{bx - 6:.1f} {h * 0.5:.1f} Q{bx:.1f} {h * 0.5 + 3:.1f} {bx + 7:.1f} {h * 0.5 + 1:.1f}", stroke="#4a1e12", width=1.4)
        for x in (5.0, w - 5.0):
            _rivet(s, x, 3.6, 1.1, body="#a8603a", rim="#3a1a10", hi="#f0b080")
        # flakes falling
        for _ in range(4):
            fx = r.uniform(8, w - 8)
            fy = low(fx) + r.uniform(2, 8)
            s.polygon([(fx, fy), (fx + 2.2, fy + 0.6), (fx + 0.8, fy + 2.2)], fill="#a8582e", opacity=0.75)
        return s

    def _catwalk(self, w: float, h: float) -> Svg:
        """Semisolid: a grating catwalk whose railing truss hangs below it."""
        s = Svg(w, h + 12)
        deck = min(h, 6.0)
        bot = h + 8.0
        # truss railing under the deck
        truss = ""
        n = max(2, int(w / 20))
        for k in range(n + 1):
            x = 3 + (w - 6) * k / n
            truss += f"M{x:.2f} {deck:.2f}L{x:.2f} {bot:.2f}"
            if k < n:
                x2 = 3 + (w - 6) * (k + 1) / n
                truss += f"M{x:.2f} {deck:.2f}L{x2:.2f} {bot:.2f}" if k % 2 == 0 else f"M{x:.2f} {bot:.2f}L{x2:.2f} {deck:.2f}"
        s.path(truss, stroke=INK, width=2.2)
        s.path(truss, stroke=IRON, width=1.1)
        s.path(rounded_rect_path(1.5, bot - 1.6, w - 3, 3.2, 1.4), fill=s.linear(0, bot - 1.6, 0, bot + 1.6, [(0, IRON_HI), (1, IRON_DARK)]), stroke=INK,
               width=0.8)
        # grating deck with a kick plate
        s.path(rounded_rect_path(0.6, 0.6, w - 1.2, deck, 1.8), fill=s.linear(0, 0, 0, deck, [(0, STEEL_HI), (0.4, STEEL_LIGHT), (1, STEEL_DARK)]),
               stroke=INK, width=1.1)
        grate = ""
        x = 4.0
        while x < w - 3:
            grate += f"M{x:.2f} {deck - 1.2:.2f}L{x + 1.8:.2f} 2.2"
            x += 4.0
        s.path(grate, stroke=STEEL_DARK, width=0.8, opacity=0.8)
        s.line(2.5, 1.3, w - 2.5, 1.3, "#ffffff", 1.0, 0.8)
        for x in (4.0, w - 4.0):
            _rivet(s, x, deck * 0.6, 0.9, body=STEEL_LIGHT)
        return s

    def _piston_spring(self, w: float, h: float) -> Svg:
        """Spring: a piston pad on a coil over a bolted base plate."""
        s = Svg(w, h + 10)
        base_h = min(4.0, h * 0.28)
        s.path(rounded_rect_path(w * 0.1, h - base_h, w * 0.8, base_h, 1.2), fill=s.linear(0, h - base_h, 0, h, [(0, IRON_HI), (1, IRON_DARK)]),
               stroke=INK, width=1.0)
        for bx in (w * 0.16, w * 0.84):
            s.circle(bx, h - base_h / 2, 0.9, fill=STEEL_HI)
        pad_h = max(4.0, h * 0.34)
        coil_top, coil_bot = pad_h - 0.5, h - base_h
        s.rect(w / 2 - 2.2, coil_top, 4.4, coil_bot - coil_top, fill=s.linear(w / 2 - 2.2, 0, w / 2 + 2.2, 0, [(0, STEEL_DARK), (0.4, STEEL_HI), (1, STEEL)]))
        coil = []
        turns = 4
        for k in range(turns * 2 + 1):
            coil.append((w / 2 + (w * 0.26 if k % 2 else -w * 0.26), coil_top + (coil_bot - coil_top) * k / (turns * 2)))
        s.path(_line(coil), stroke=INK, width=2.6)
        s.path(_line(coil), stroke=STEEL_LIGHT, width=1.4)
        s.path(rounded_rect_path(w * 0.06, 0.6, w * 0.88, pad_h, pad_h * 0.45),
               fill=s.linear(0, 0.6, 0, pad_h, [(0, BRASS_HI), (0.4, BRASS_LIGHT), (1, BRASS_DARK)]), stroke=INK, width=1.1)
        s.rect(w * 0.12, pad_h * 0.55, w * 0.76, pad_h * 0.25, fill="#d8462e", opacity=0.85)
        s.line(w * 0.14, 1.8, w * 0.86, 1.8, "#ffffff", 0.9, 0.8)
        s.polygon([(w / 2 - 3, pad_h * 0.5), (w / 2, pad_h * 0.2), (w / 2 + 3, pad_h * 0.5)], fill="#ffffff", opacity=0.85)
        return s

    def _conveyor(self, w: float, h: float, style: str) -> Svg:
        """Conveyor belt: a rubber belt over steel rollers in a riveted frame;
        chevrons show the travel direction (style 'left'/'reverse' flips it)."""
        s = Svg(w, h + 6)
        left = any(k in style for k in ("left", "reverse", "<"))
        rad = h / 2
        s.path(rounded_rect_path(0.6, 0.6, w - 1.2, h - 1.2, rad), fill="#24202a", stroke=INK, width=1.2)
        frame_top, frame_bot = 5.4, h - 3.6
        s.path(rounded_rect_path(rad * 0.55, frame_top, w - rad * 1.1, frame_bot - frame_top, 2),
               fill=s.linear(0, frame_top, 0, frame_bot, [(0, STEEL_LIGHT), (0.5, STEEL), (1, STEEL_DARK)]), stroke=INK, width=0.8)
        n = max(2, int((w - h) / 14))
        rr = (frame_bot - frame_top) * 0.36
        for k in range(n + 1):
            x = rad + (w - 2 * rad) * k / n
            s.circle(x, h / 2, rr, fill=s.radial(x - rr * 0.3, h / 2 - rr * 0.3, rr * 1.2, [(0, STEEL_HI), (0.6, STEEL_LIGHT), (1, STEEL_DARK)]),
                     stroke=INK, width=0.6)
            s.line(x - rr * 0.6, h / 2, x + rr * 0.6, h / 2, STEEL_DARK, 0.6, 0.8)
            s.circle(x, h / 2, rr * 0.25, fill=INK)
        for x in (rad, w - rad):  # end drums
            s.circle(x, h / 2, rad * 0.78, fill=s.radial(x - 1, h / 2 - 1, rad, [(0, BRASS_LIGHT), (0.6, BRASS), (1, BRASS_DEEP)]), stroke=INK, width=0.9)
            s.circle(x, h / 2, rad * 0.25, fill=INK)
        # belt top run with bold chevrons
        belt = 5.2
        s.path(rounded_rect_path(rad * 0.3, 0.6, w - rad * 0.6, belt, 2.2), fill=s.linear(0, 0.6, 0, belt, [(0, "#4a4452"), (1, "#24202a")]),
               stroke=INK, width=0.7)
        chev = ""
        step = 11.0
        x = rad * 0.6 + 2
        while x < w - rad * 0.6 - 5:
            if left:
                chev += f"M{x + 4.2:.2f} 1.6L{x:.2f} {belt / 2 + 0.6:.2f}L{x + 4.2:.2f} {belt - 0.4:.2f}"
            else:
                chev += f"M{x:.2f} 1.6L{x + 4.2:.2f} {belt / 2 + 0.6:.2f}L{x:.2f} {belt - 0.4:.2f}"
            x += step
        s.path(chev, stroke=HAZARD_Y, width=1.5, join="miter", cap="butt")
        s.line(rad * 0.5, 1.1, w - rad * 0.5, 1.1, "#9a94a4", 0.6, 0.8)
        # bottom run
        s.path(rounded_rect_path(rad * 0.4, h - 4, w - rad * 0.8, 3.4, 1.6), fill="#1a161e")
        for x in (w * 0.2, w * 0.8):
            s.rect(x - 2, h - 0.5, 4, 6, fill=IRON_DARK, stroke=INK, width=0.6)
        return s

    def pipe(self, w: float, h: float, warp: bool) -> Svg:
        """Brass steam pipe: flanged rim, riveted collar, valve handwheel and a
        pressure gauge (the warp variant's gauge glows and points down)."""
        s = Svg(w, h)
        body = s.linear(4, 0, w - 4, 0, [(0, BRASS_DEEP), (0.18, BRASS), (0.3, BRASS_HI), (0.48, BRASS_LIGHT), (0.78, BRASS_DARK), (1, BRASS_DEEP)])
        s.path(rounded_rect_path(4, 10, w - 8, h - 10, 2), fill=body, stroke=INK, width=1.3)
        if h > 36:
            cy = h - 9
            s.rect(4.5, cy - 3, w - 9, 6, fill=s.linear(4.5, 0, w - 4.5, 0, [(0, COPPER_DARK), (0.3, COPPER_LIGHT), (1, COPPER_DARK)]), stroke=INK,
                   width=0.8)
            for bx in range(9, int(w) - 6, 8):
                s.circle(bx, cy, 0.85, fill=COPPER_HI)
        s.path(f"M{w * 0.2:.2f} 16 L{w * 0.2:.2f} {h - 2:.2f}", stroke="#ffffff", width=1.6, opacity=0.35)
        # rim flange with bolts
        rim = s.linear(0.8, 0, w - 0.8, 0, [(0, BRASS_DEEP), (0.2, BRASS_LIGHT), (0.34, BRASS_HI), (0.6, BRASS), (1, BRASS_DEEP)])
        s.path(rounded_rect_path(0.8, 0.8, w - 1.6, 13, 3.5), fill=rim, stroke=INK, width=1.3)
        s.path(f"M3 3.2 L{w - 3:.2f} 3.2", stroke=BRASS_DEEP, width=1.4, opacity=0.7)
        for k in range(5):
            bx = 5 + (w - 10) * k / 4
            _rivet(s, bx, 8.6, 1.3, body=BRASS_LIGHT, rim=BRASS_DEEP, hi="#ffffff")
        s.line(4.5, 13.8, w - 4.5, 13.8, INK, 1.0, 0.6)
        gy = 26.0 if h > 36 else max(18.0, h * 0.62)
        gr = 6.5 if h > 36 else 4.6
        if warp:
            _gauge(s, w * 0.62, gy, gr, 180.0, glow=True)
            s.polygon([(w * 0.62 - 2.6, gy + gr + 1.6), (w * 0.62 + 2.6, gy + gr + 1.6), (w * 0.62, gy + gr + 4.6)], fill=TEAL_GLOW, stroke="#0b3a33",
                      width=0.5)
        else:
            _gauge(s, w * 0.62, gy, gr, -50.0)
        if h > 36 and w > 40:
            s.rect(w * 0.26 - 1.8, gy - 0.6, 3.6, 4, fill=STEEL_DARK, stroke=INK, width=0.6)
            _handwheel(s, w * 0.26, gy - 2, 5.2, spokes=5)
        return s

    # ------------------------------------------------------------------ props
    def _lamp_post(self) -> Svg:
        """Gas lamp: fluted cast-iron post, ladder bar and a brass lantern."""
        s = Svg(40, 122)
        cx = 20.0
        _halo(s, cx, 22, 20, LAMP, 0.6)
        post = s.linear(cx - 3, 0, cx + 3, 0, [(0, "#4a4458"), (0.4, "#7a7488"), (1, "#24202c")])
        s.path(f"M{cx - 9:.1f} 122 L{cx - 8:.1f} 112 Q{cx - 4:.1f} 108 {cx - 4:.1f} 100 L{cx - 2.6:.1f} 40 L{cx + 2.6:.1f} 40 L{cx + 4:.1f} 100 "
               f"Q{cx + 4:.1f} 108 {cx + 8:.1f} 112 L{cx + 9:.1f} 122 Z", fill=post, stroke=INK, width=1.1)
        s.rect(cx - 6, 106, 12, 3, fill="#5a5466", stroke=INK, width=0.7)
        s.line(cx - 10, 46, cx + 10, 46, INK, 2.4)
        s.line(cx - 10, 46, cx + 10, 46, "#6a6478", 1.2)
        for x in (cx - 10, cx + 10):
            s.circle(x, 46, 1.4, fill="#6a6478", stroke=INK, width=0.6)
        s.path(f"M{cx - 3:.1f} 40 L{cx + 3:.1f} 40 L{cx + 5:.1f} 35 L{cx - 5:.1f} 35 Z", fill="#5a5466", stroke=INK, width=0.8)
        s.path(f"M{cx - 7:.1f} 35 L{cx + 7:.1f} 35 L{cx + 9:.1f} 15 L{cx - 9:.1f} 15 Z",
               fill=s.radial(cx, 25, 12, [(0, LAMP_HOT), (0.45, LAMP), (1, LAMP_DEEP)]), stroke=INK, width=1.0)
        s.path(f"M{cx:.1f} 15 L{cx:.1f} 35 M{cx - 8:.1f} 25 L{cx + 8:.1f} 25", stroke="#8a5a2a", width=0.9, opacity=0.7)
        s.path(f"M{cx - 11:.1f} 15 L{cx + 11:.1f} 15 L{cx + 6:.1f} 9 L{cx - 6:.1f} 9 Z", fill=s.linear(cx - 11, 0, cx + 11, 0, [(0, BRASS_HI), (0.5, BRASS), (1, BRASS_DEEP)]),
               stroke=INK, width=1.0)
        s.path(f"M{cx - 3:.1f} 9 Q{cx:.1f} 2 {cx + 3:.1f} 9 Z", fill=BRASS, stroke=INK, width=0.8)
        s.circle(cx, 2.6, 1.6, fill=BRASS_LIGHT, stroke=INK, width=0.6)
        s.path(f"M{cx - 5:.1f} 32 L{cx - 6.5:.1f} 18", stroke="#ffffff", width=1.2, opacity=0.7)
        return s

    def _street_clock(self) -> Svg:
        """Street clock on a post: brass bezel, ticks, hands and a cog crest."""
        s = Svg(46, 128)
        cx, cy, rr = 23.0, 30.0, 15.0
        s.path(f"M{cx - 9:.1f} 128 L{cx - 7:.1f} 118 L{cx - 3:.1f} 114 L{cx - 2.6:.1f} 46 L{cx + 2.6:.1f} 46 L{cx + 3:.1f} 114 L{cx + 7:.1f} 118 L{cx + 9:.1f} 128 Z",
               fill=s.linear(cx - 3, 0, cx + 3, 0, [(0, "#3e5a50"), (0.4, "#6a8a7a"), (1, "#24342e")]), stroke=INK, width=1.1)
        s.rect(cx - 5, 64, 10, 3, fill="#4a6a5e", stroke=INK, width=0.6)
        s.path(_gear_d(cx, cy - rr - 4, 6, 8, 0.28, hole=1.8), fill=BRASS, stroke=INK, width=0.8)
        s.circle(cx, cy, rr + 3.4, fill=s.linear(cx - rr, cy - rr, cx + rr, cy + rr, [(0, BRASS_HI), (0.5, BRASS), (1, BRASS_DEEP)]), stroke=INK,
                 width=1.2)
        s.circle(cx, cy, rr, fill=s.radial(cx - 4, cy - 4, rr * 1.3, [(0, "#fffbf0"), (1, "#efd9b0")]), stroke=INK, width=0.8)
        ticks = ""
        for k in range(12):
            a = 2 * math.pi * k / 12
            r0 = rr * (0.7 if k % 3 == 0 else 0.8)
            ticks += f"M{cx + math.cos(a) * r0:.2f} {cy + math.sin(a) * r0:.2f}L{cx + math.cos(a) * rr * 0.92:.2f} {cy + math.sin(a) * rr * 0.92:.2f}"
        s.path(ticks, stroke="#3a2a2a", width=1.0)
        s.line(cx, cy, cx + 5.5, cy + 4.5, INK, 1.6)
        s.line(cx, cy, cx - 2.5, cy - 11, INK, 1.0)
        s.circle(cx, cy, 1.4, fill="#b8241c")
        s.path(f"M{cx - rr * 0.7:.2f} {cy - rr * 0.4:.2f} Q{cx - rr * 0.3:.2f} {cy - rr * 0.85:.2f} {cx + rr * 0.2:.2f} {cy - rr * 0.8:.2f}",
               stroke="#ffffff", width=1.2, opacity=0.8)
        s.path(f"M{cx - 4:.1f} {cy + rr + 3:.1f} L{cx + 4:.1f} {cy + rr + 3:.1f} L{cx + 2.6:.1f} 46 L{cx - 2.6:.1f} 46 Z", fill="#4a6a5e", stroke=INK,
               width=0.8)
        return s

    def _crates(self, seed: int) -> Svg:
        r = Rand(seed)
        s = Svg(70, 52)

        def crate(x: float, y: float, sz: float, dark: float) -> None:
            fill = s.linear(x, y, x + sz, y + sz, [(0, shade("#c89058", dark)), (1, shade("#8a5a32", dark))])
            s.path(rounded_rect_path(x, y, sz, sz, 1.5), fill=fill, stroke=INK, width=1.1)
            for k in range(1, 4):
                s.line(x + 1, y + sz * k / 4, x + sz - 1, y + sz * k / 4, "#6a4226", 0.8, 0.6)
            s.path(f"M{x + 3:.1f} {y + 3:.1f} L{x + sz - 3:.1f} {y + sz - 3:.1f}", stroke="#6a4226", width=2.0, opacity=0.8)
            for cx, cy, dx, dy in ((x, y, 1, 1), (x + sz, y, -1, 1), (x, y + sz, 1, -1), (x + sz, y + sz, -1, -1)):
                s.path(f"M{cx + dx * 6:.1f} {cy + dy * 1.2:.1f} L{cx + dx * 1.2:.1f} {cy + dy * 1.2:.1f} L{cx + dx * 1.2:.1f} {cy + dy * 6:.1f}",
                       stroke=STEEL_DARK, width=2.2, join="miter", cap="butt")
                s.circle(cx + dx * 3, cy + dy * 3, 0.8, fill=STEEL_HI)
            s.path(_gear_d(x + sz * 0.68, y + sz * 0.35, sz * 0.14, 7, 0.3, hole=sz * 0.05), fill="#3a2414", opacity=0.55)
        crate(4, 20, 32, 0.0)
        crate(36, 24, 28, -0.08)
        if r.next() < 0.6 or seed % 2:
            crate(14, 0, 22, 0.06)
        return s

    def _barrels(self, seed: int) -> Svg:
        s = Svg(56, 40)
        for k, (x, col) in enumerate(((4, "#4a6a8a"), (28, "#a84a3a"))):
            body = s.linear(x, 0, x + 22, 0, [(0, shade(col, -0.45)), (0.35, shade(col, 0.25)), (1, shade(col, -0.5))])
            s.path(rounded_rect_path(x, 6, 22, 33, 3), fill=body, stroke=INK, width=1.1)
            for y in (12, 32):
                s.rect(x, y, 22, 2.2, fill=shade(col, -0.35))
            s.ellipse(x + 11, 6.5, 11, 2.6, fill=shade(col, 0.1), stroke=INK, width=0.9)
            s.circle(x + 15, 6.4, 1.3, fill=INK)
            if k == (seed % 2):
                _hazard(s, x + 0.6, 18, 20.8, 7, step=3.0)
        return s

    def _gear_pile(self, seed: int) -> Svg:
        r = Rand(seed)
        s = Svg(64, 34)
        s.ellipse(32, 32, 28, 2.4, fill=SOOT, opacity=0.35)
        gears = [(20, 22, 11, 10, BRASS), (40, 24, 9, 9, STEEL), (31, 14, 8, 8, COPPER), (50, 28, 6, 7, BRASS)]
        for gx, gy, gr, teeth, col in gears:
            ph = r.uniform(0, 1)
            s.path(_gear_d(gx, gy, gr, teeth, 0.24, hole=gr * 0.28, phase=ph),
                   fill=s.linear(gx - gr, gy - gr, gx + gr, gy + gr, [(0, shade(col, 0.45)), (0.5, col), (1, shade(col, -0.5))]), stroke=INK, width=1.0)
        for nx, ny in ((10, 30), (58, 31), (25, 31)):
            pts = [(nx + math.cos(a) * 3, ny + math.sin(a) * 2.2) for a in [i * math.pi / 3 for i in range(6)]]
            s.polygon(pts, fill=STEEL_LIGHT, stroke=INK, width=0.7)
            s.circle(nx, ny, 1.0, fill=INK)
        s.path("M44 12 Q48 6 52 12 Q56 18 60 12", stroke=STEEL_DARK, width=1.4)
        return s

    def _valve(self) -> Svg:
        """Standpipe with a big red handwheel and a gauge."""
        s = Svg(38, 58)
        body = s.linear(13, 0, 25, 0, [(0, COPPER_DARK), (0.35, COPPER_LIGHT), (1, COPPER_DARK)])
        s.path(rounded_rect_path(13, 14, 12, 44, 2), fill=body, stroke=INK, width=1.1)
        for y in (24, 50):
            s.rect(11, y, 16, 4, fill=s.linear(11, 0, 27, 0, [(0, BRASS_DEEP), (0.4, BRASS_LIGHT), (1, BRASS_DEEP)]), stroke=INK, width=0.8)
        s.path(rounded_rect_path(6, 30, 26, 8, 3), fill=body, stroke=INK, width=1.0)
        s.rect(17.5, 6, 3, 9, fill=STEEL_DARK, stroke=INK, width=0.7)
        _handwheel(s, 19, 8, 7.2, spokes=5)
        _gauge(s, 30, 22, 4.6, 20)
        return s

    def _steam_vent(self) -> Svg:
        s = Svg(64, 100)
        for cx, cy, rx, ry, op in ((32, 78, 9, 9, 0.6), (30, 62, 13, 11, 0.5), (35, 44, 17, 13, 0.38), (29, 26, 20, 14, 0.26), (34, 10, 18, 9, 0.14)):
            _soft(s, cx, cy, rx, ry, STEAM, op, 0.3)
        s.path("M8 100 L12 88 L52 88 L56 100 Z", fill=s.linear(0, 88, 0, 100, [(0, IRON_HI), (1, IRON_DARK)]), stroke=INK, width=1.1)
        s.rect(14, 86, 36, 3.6, fill="#14121a")
        d = ""
        for x in range(16, 50, 5):
            d += f"M{x} 86.4L{x} 89.4"
        s.path(d, stroke=IRON_HI, width=1.2)
        _hazard(s, 13, 92, 38, 3, step=3.0)
        return s

    def _signpost(self, seed: int) -> Svg:
        """Cast-iron signpost with blank arrow plates and pictograms (no text)."""
        s = Svg(58, 86)
        s.path(rounded_rect_path(27, 10, 4, 76, 1.5), fill=s.linear(27, 0, 31, 0, [(0, "#6a6478"), (1, "#24202c")]), stroke=INK, width=1.0)
        s.circle(29, 8.5, 2.6, fill=BRASS, stroke=INK, width=0.8)
        s.path("M23 86 L25 80 L33 80 L35 86 Z", fill="#4a4458", stroke=INK, width=0.9)
        plates = ((16, 1), (34, -1)) if seed % 2 else ((16, -1), (34, 1))
        for y, direction in plates:
            if direction > 0:
                pts = [(29, y), (48, y), (54, y + 6), (48, y + 12), (29, y + 12)]
            else:
                pts = [(29, y), (10, y), (4, y + 6), (10, y + 12), (29, y + 12)]
            s.polygon(pts, fill=s.linear(0, y, 0, y + 12, [(0, "#3e6a5e"), (1, "#24443c")]), stroke=INK, width=1.0)
            s.polygon([(px, py) for px, py in pts], fill=None, stroke=BRASS, width=0.7, opacity=0.8)
            icon_x = 29 + direction * 13
            if y == plates[0][0]:
                s.path(_gear_d(icon_x, y + 6, 3.6, 7, 0.3, hole=1.2), fill=BRASS_LIGHT)
            else:
                s.path(f"M{icon_x - 3.5:.1f} {y + 9:.1f} L{icon_x - 3.5:.1f} {y + 4.5:.1f} L{icon_x:.1f} {y + 2.6:.1f} L{icon_x + 3.5:.1f} {y + 4.5:.1f} "
                       f"L{icon_x + 3.5:.1f} {y + 9:.1f} Z", fill=BRASS_LIGHT)
        return s

    def _boiler(self) -> Svg:
        """Big riveted boiler on cradles with a stack, gauges and a valve."""
        s = Svg(124, 100)
        _halo(s, 30, 86, 26, MOLTEN, 0.45)
        for x in (24, 92):
            s.path(f"M{x - 12} 100 L{x - 8} 80 L{x + 8} 80 L{x + 12} 100 Z", fill=s.linear(0, 80, 0, 100, [(0, IRON_HI), (1, IRON_DARK)]), stroke=INK, width=1.1)
        s.path(rounded_rect_path(86, 8, 12, 40, 2), fill=s.linear(86, 0, 98, 0, [(0, IRON_DARK), (0.4, IRON_HI), (1, IRON_DEEP)]), stroke=INK, width=1.1)
        s.rect(84, 6, 16, 5, fill=IRON, stroke=INK, width=0.9)
        tank = s.linear(0, 40, 0, 86, [(0, COPPER_HI), (0.25, COPPER_LIGHT), (0.6, COPPER), (1, COPPER_DARK)])
        s.path(rounded_rect_path(6, 40, 112, 46, 22), fill=tank, stroke=INK, width=1.4)
        for x in (30, 58, 86):
            s.line(x, 41, x, 85, COPPER_DARK, 1.6, 0.8)
            for y in range(46, 84, 7):
                s.circle(x + 2.4, y, 0.9, fill=COPPER_HI)
        s.path("M18 48 Q60 42 106 48", stroke="#ffffff", width=1.6, opacity=0.5)
        s.path(rounded_rect_path(14, 60, 22, 18, 3), fill="#2a1a1a", stroke=INK, width=1.0)
        s.path("M16 76 L34 76 L34 66 Q25 60 16 66 Z", fill=s.linear(0, 62, 0, 76, [(0, MOLTEN_YELLOW), (1, MOLTEN_RED)]))
        _gauge(s, 52, 34, 7, 35)
        _gauge(s, 68, 36, 5, -30)
        s.rect(50.5, 40, 3, 3, fill=STEEL_DARK)
        _handwheel(s, 106, 34, 6, spokes=5)
        s.rect(104.5, 38, 3, 4, fill=STEEL_DARK)
        _soft(s, 92, 0, 14, 8, STEAM, 0.35, 0.3)
        return s

    def props(self) -> dict[str, PropSpec]:
        return {
            "lamp_post": PropSpec(self._lamp_post, (20, 121)),
            "street_clock": PropSpec(self._street_clock, (23, 127)),
            "crates": PropSpec(lambda: self._crates(3), (34, 51)),
            "crates_b": PropSpec(lambda: self._crates(8), (34, 51)),
            "barrels": PropSpec(lambda: self._barrels(2), (28, 39)),
            "barrels_b": PropSpec(lambda: self._barrels(5), (28, 39)),
            "gear_pile": PropSpec(lambda: self._gear_pile(4), (32, 33)),
            "valve": PropSpec(self._valve, (19, 57)),
            "steam_vent": PropSpec(self._steam_vent, (32, 99)),
            "signpost": PropSpec(lambda: self._signpost(1), (29, 85)),
            "signpost_b": PropSpec(lambda: self._signpost(2), (29, 85)),
            "boiler": PropSpec(self._boiler, (62, 99)),
        }

    def auto_decor(self, rng, surface_w: float) -> list[tuple[str, float, float, str]]:
        out = []
        x = rng.uniform(40, 120)
        boiler = False
        while x < surface_w - 40:
            roll = rng.next()
            if roll < 0.2:
                out.append(("lamp_post", x, rng.uniform(0.74, 0.86), "back"))
            elif roll < 0.36:
                out.append((rng.choice(["crates", "crates_b"]), x, rng.uniform(0.75, 1.0), "back"))
            elif roll < 0.48:
                out.append((rng.choice(["barrels", "barrels_b"]), x, rng.uniform(0.8, 1.0), "mid"))
            elif roll < 0.58:
                out.append(("gear_pile", x, rng.uniform(0.7, 0.95), "mid"))
            elif roll < 0.66:
                out.append(("valve", x, rng.uniform(0.85, 1.0), "back"))
            elif roll < 0.74:
                out.append(("steam_vent", x, rng.uniform(0.8, 1.0), "back"))
            elif roll < 0.81:
                out.append(("street_clock", x, rng.uniform(0.72, 0.82), "back"))
            elif roll < 0.88:
                out.append((rng.choice(["signpost", "signpost_b"]), x, rng.uniform(0.9, 1.0), "back"))
            elif roll < 0.94 and surface_w > 480 and not boiler:
                out.append(("boiler", x, rng.uniform(0.85, 1.0), "back"))
                boiler = True
            x += rng.uniform(110, 220)
        return out

    def weather(self) -> Weather:
        return Weather("ash", 0.3, ("soft",), wind=14.0)


ART_CLASS = ClockworkCity
