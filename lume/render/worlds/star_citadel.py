"""Cidadela das Estrelas: a celestial citadel floating in space, where
constellations are architecture (world 10, the grand finale).

Identity: deep indigo-to-violet space with layered star fields, soft teal and
magenta nebulae, a large ringed planet, a moon and distant galaxies; floating
citadel spires with lit windows far away, orbiting stone rings and
observatory domes linked by constellation lines in the middle distance,
drifting star dust and crystal shards close by. The ground is midnight-blue
star-stone (lapis-like, flecked with gold) inlaid with gold constellations
(dots joined by thin lines) under a faintly glowing white-crystal rim; temple
levels use star-stone masonry with gold trim. Slippery floors
(``surface == "ice"``) are thick polished mirror-crystal slabs set in gold,
reflecting the stars, so the physics reads at a glance.

Light: a cool starlight key from the upper left (the planet and the moon are
lit from that side); gold inlays and crystal edges glow faintly. Walkable tops
always carry the bright crystal (or gold) edge; hazards are never gold.
"""

from __future__ import annotations

import math
from typing import Sequence

from ..svg import Rand, Svg, blob, mix, rounded_rect_path, shade, smooth_closed, smooth_open, star_points
from .base import Layer, PropSpec, Weather, WorldArt

Pt = tuple[float, float]

INK = "#140f30"  # deep indigo outline
# star-stone (lapis): highlight → deep
STONE_HI, STONE_TOP, STONE, STONE_DARK, STONE_DEEP = "#5a66c2", "#38418c", "#262d6e", "#181c4c", "#0c0e2c"
STONE_LINE = "#0a0b26"
# gold inlays and trims
GOLD_HI, GOLD_LIGHT, GOLD, GOLD_DARK, GOLD_DEEP = "#fff4c8", "#ffd978", "#e8b04a", "#a8701e", "#5e3a10"
# white crystal
CRYSTAL_HI, CRYSTAL, CRYSTAL_MID, CRYSTAL_LOW, CRYSTAL_LINE = "#ffffff", "#e3ecff", "#b6c4f4", "#8592dc", "#3a3f8e"
GLOW_CYAN, GLOW_TEAL, GLOW_VIOLET, GLOW_MAGENTA = "#a8e6ff", "#5fe6d8", "#b294ff", "#e070d8"
# mirror crystal (slippery floors)
MIRROR_HI, MIRROR_TOP, MIRROR, MIRROR_DEEP, MIRROR_LINE = "#ffffff", "#dfeaff", "#9fb4f2", "#5d6fd0", "#262a78"
# space
SPACE = ("#05061a", "#0d0f3a", "#1d1856", "#33216d", "#4d2c84")
NEBULA_TEAL, NEBULA_MAGENTA = "#36cfc6", "#d24fcf"


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


def _glow(s: Svg, cx: float, cy: float, r: float, color: str, strength: float = 0.5) -> None:
    s.circle(cx, cy, r, fill=s.radial(cx, cy, r, [(0, color, strength), (0.4, color, strength * 0.4), (1, color, 0)]))


def _soft(s: Svg, cx: float, cy: float, rx: float, ry: float, color: str, alpha: float = 1.0, core: float = 0.0,
          angle: float = 0.0) -> None:
    """Soft-edged (optionally rotated) ellipse: a radial falloff in a scaled group."""
    rot = f" rotate({angle:.1f})" if angle else ""
    with s.group(transform=f"translate({cx:.2f} {cy:.2f}){rot} scale(1 {ry / rx:.4f})"):
        s.circle(0, 0, rx, fill=s.radial(0, 0, rx, [(0, color, alpha), (core, color, alpha), (1, color, 0)]))


def _sparkle(s: Svg, x: float, y: float, size: float, opacity: float = 0.95, color: str = "#ffffff") -> None:
    s.polygon(star_points(x, y, size, size * 0.24, 4), fill=color, opacity=opacity)


def _star_node(s: Svg, x: float, y: float, size: float, color: str = GOLD_LIGHT, core: str = GOLD_HI, glow: float = 0.5) -> None:
    """A star of a constellation: soft halo, small twinkle and a bright core."""
    _glow(s, x, y, size * 3.2, color, glow)
    _sparkle(s, x, y, size * 2.0, 0.85, core)
    s.circle(x, y, size * 0.55, fill=core)


def _crystal(s: Svg, bx: float, by: float, angle: float, length: float, width: float, light: str, dark: str,
             line: str = CRYSTAL_LINE, line_w: float = 0.8, opacity: float = 1.0) -> None:
    """Hexagonal crystal prism from base (bx, by) pointing at ``angle`` degrees
    (0 = up): a lit left facet, a shaded right facet and a chisel tip."""
    a = math.radians(angle)
    ux, uy = math.sin(a), -math.cos(a)  # along the crystal
    nx, ny = -uy, ux  # across (to the right of the axis)
    hw = width / 2
    shoulder = length - width * 0.75
    pts = [(bx - nx * hw, by - ny * hw), (bx - nx * hw + ux * shoulder, by - ny * hw + uy * shoulder),
           (bx + ux * length, by + uy * length), (bx + nx * hw + ux * shoulder, by + ny * hw + uy * shoulder),
           (bx + nx * hw, by + ny * hw)]
    s.polygon(pts, fill=s.linear(pts[0][0], pts[0][1], pts[4][0], pts[4][1], [(0, light), (0.48, mix(light, dark, 0.35)), (0.52, dark),
                                                                              (1, shade(dark, -0.25))]),
              stroke=line, width=line_w, opacity=opacity)
    # the bright ridge along the axis and the lit facet edge
    s.line(bx + ux * 1.0, by + uy * 1.0, bx + ux * length * 0.98, by + uy * length * 0.98, "#ffffff", max(0.5, width * 0.09), 0.55 * opacity)
    s.line(bx - nx * hw * 0.55 + ux * 1.5, by - ny * hw * 0.55 + uy * 1.5, bx - nx * hw * 0.55 + ux * shoulder,
           by - ny * hw * 0.55 + uy * shoulder, "#ffffff", max(0.4, width * 0.06), 0.4 * opacity)


def _constellation_shape(n: int, salt: int, x0: float, x1: float, y0: float, y1: float) -> tuple[list[Pt], list[tuple[int, int]]]:
    """Deterministic constellation inside a box: a chain of stars with one branch."""
    k = 4 + int(_hash(n, salt) * 3)
    pts: list[Pt] = []
    for i in range(k):
        t = (i + 0.2 + 0.6 * _hash(n * 7 + i, salt + 1)) / k
        pts.append((x0 + (x1 - x0) * t, y0 + (y1 - y0) * _hash(n * 13 + i, salt + 2)))
    edges = [(i, i + 1) for i in range(k - 1)]
    if k >= 5:
        a = 1 + int(_hash(n, salt + 3) * (k - 3))
        b = min(k - 1, a + 2)
        edges.append((a, b))
    return pts, edges


def _inlay(s: Svg, pts: Sequence[Pt], edges: Sequence[tuple[int, int]], node: float = 1.0, glow: float = 0.4,
           groove: bool = True) -> None:
    """Gold constellation inlaid in stone: engraved groove, gold line, glowing nodes."""
    for a, b in edges:
        (ax, ay), (bx, by) = pts[a], pts[b]
        s.line(ax, ay, bx, by, GOLD_LIGHT, 3.2 * node, 0.12 * glow / 0.4)
        if groove:
            s.line(ax, ay + 0.6 * node, bx, by + 0.6 * node, STONE_LINE, 1.3 * node, 0.6)
        s.line(ax, ay, bx, by, GOLD, 0.9 * node, 0.95)
        s.line(ax, ay - 0.25 * node, bx, by - 0.25 * node, GOLD_HI, 0.35 * node, 0.7)
    for i, (x, y) in enumerate(pts):
        big = i % 3 == 1
        _glow(s, x, y, 4.2 * node * (1.3 if big else 1.0), GOLD_LIGHT, glow)
        s.circle(x, y, 1.45 * node, fill=s.radial(x - 0.4 * node, y - 0.4 * node, 1.6 * node, [(0, GOLD_HI), (0.6, GOLD_LIGHT), (1, GOLD_DARK)]),
                 stroke=GOLD_DEEP, width=0.35 * node)
        if big:
            _sparkle(s, x, y, 3.0 * node, 0.8, GOLD_HI)


# --------------------------------------------------------------------------- world
class StarCitadel(WorldArt):
    id = "star_citadel"
    name = "Cidadela das Estrelas"
    accent = "#ffd36b"  # starlight gold
    terrain_headroom = 12.0
    ambient = (236, 236, 255)  # faint cool starlight (the art itself is authored dark)
    vignette = 0.34
    wind_tint = (226, 222, 255)  # pale stardust streaks
    provisional = False
    PLANET = (744.0, 190.0, 64.0)
    MOON = (212.0, 134.0, 24.0)

    # ------------------------------------------------------------------ sky
    def _eclipse_sky(self) -> bool:
        return "eclipse" in self.variant

    def sky(self) -> Svg:
        s = Svg(960, 540)
        eclipse = self._eclipse_sky()
        stops = SPACE if not eclipse else ("#07041a", "#140a36", "#2a1050", "#4a1658", "#6a2058")
        s.rect(0, 0, 960, 540, fill=s.linear(0, 0, 0, 540, [(0, stops[0]), (0.28, stops[1]), (0.55, stops[2]), (0.8, stops[3]), (1, stops[4])]))
        r = Rand(23)
        # the band of the galaxy (from lower left to upper right) and its nebulae
        bx0, by0, bx1, by1 = -40.0, 372.0, 1000.0, 64.0
        ang = math.degrees(math.atan2(by1 - by0, bx1 - bx0))
        for t, rx, ry, color, a in ((0.2, 230, 62, NEBULA_TEAL, 0.2), (0.33, 170, 44, "#5fe8dc", 0.16), (0.5, 210, 54, "#7a5ad8", 0.18),
                                    (0.66, 190, 58, NEBULA_MAGENTA, 0.2), (0.8, 160, 46, "#f07ad8", 0.15)):
            cx, cy = bx0 + (bx1 - bx0) * t, by0 + (by1 - by0) * t
            _soft(s, cx, cy, rx, ry, color, a, 0.15, ang + (t - 0.5) * 14)
        # bright cores and dark dust lanes give the nebulae structure
        for t, off, rx, ry, color, a in ((0.24, -10, 70, 20, "#a8fff2", 0.18), (0.62, 8, 80, 18, "#ffb4ee", 0.16),
                                         (0.42, 4, 150, 10, "#05041a", 0.4), (0.72, -6, 120, 9, "#05041a", 0.35)):
            cx, cy = bx0 + (bx1 - bx0) * t, by0 + (by1 - by0) * t + off
            _soft(s, cx, cy, rx, ry, color, a, 0.2, ang)
        # wispy filaments along the band
        dx, dy = (bx1 - bx0), (by1 - by0)
        ln = math.hypot(dx, dy)
        ux, uy, nx, ny = dx / ln, dy / ln, -dy / ln, dx / ln
        for k, (color, width, op, off) in enumerate((("#5fe8dc", 14, 0.06, -26), ("#c08aff", 10, 0.07, 18), ("#ff9ae0", 6, 0.08, 34),
                                                     ("#9ff8f0", 4, 0.1, -14))):
            pts = []
            for i in range(9):
                t = 0.05 + 0.9 * i / 8
                wob = math.sin(i * 1.7 + k * 2.3) * 16
                pts.append((bx0 + dx * t + nx * (off + wob), by0 + dy * t + ny * (off + wob)))
            s.path(smooth_open(pts), stroke=color, width=width, opacity=op)
        # star fields: faint dust everywhere, a denser band, medium stars, bright twinkles
        for _ in range(170):
            x, y = r.uniform(0, 960), r.uniform(0, 520)
            s.circle(x, y, r.uniform(0.45, 0.85), fill=r.choice(["#ffffff", "#cfd8ff", "#ffe9c4", "#d8c8ff"]), opacity=r.uniform(0.3, 0.75))
        for _ in range(150):
            t = r.next()
            off = (r.next() + r.next() + r.next() - 1.5) * 70
            x, y = bx0 + dx * t + nx * off, by0 + dy * t + ny * off
            s.circle(x, y, r.uniform(0.4, 0.8), fill=r.choice(["#ffffff", "#e6f4ff", "#ffe6f6"]), opacity=r.uniform(0.35, 0.9))
        for _ in range(42):
            x, y = r.uniform(10, 950), r.uniform(10, 500)
            rad = r.uniform(0.9, 1.6)
            color = r.choice(["#ffffff", "#bfd4ff", "#ffe2a8", "#ffd0f0"])
            if r.next() < 0.35:
                _glow(s, x, y, rad * 4.5, color, 0.35)
            s.circle(x, y, rad, fill=color, opacity=0.95)
        for _ in range(13):
            x, y = r.uniform(20, 940), r.uniform(70, 470)
            size = r.uniform(3.0, 6.0)
            color = r.choice(["#ffffff", "#dff0ff", "#fff0c8"])
            _glow(s, x, y, size * 3.2, color, 0.32)
            _sparkle(s, x, y, size, 0.95, color)
            s.circle(x, y, size * 0.22, fill="#ffffff")
        # distant galaxies
        self._galaxy(s, 452, 104, 30, 24, "#d6c8ff")
        self._galaxy(s, 92, 262, 22, -38, "#a8e8ff")
        self._galaxy(s, 610, 318, 14, 60, "#ffc8ec")
        # a faint constellation drawn on the sky itself
        pts = [(492.0, 182.0), (520.0, 160.0), (551.0, 168.0), (566.0, 142.0), (598.0, 150.0), (553.0, 196.0)]
        for a, b in ((0, 1), (1, 2), (2, 3), (3, 4), (2, 5)):
            s.line(pts[a][0], pts[a][1], pts[b][0], pts[b][1], GOLD_LIGHT, 0.9, 0.28)
        for x, y in pts:
            _glow(s, x, y, 7, GOLD_LIGHT, 0.3)
            s.circle(x, y, 1.3, fill=GOLD_HI)
        if eclipse:
            self._eclipse(s, *self.MOON[:2], 34)
        else:
            self._moon(s, *self.MOON)
        self._planet(s, *self.PLANET)
        return s

    def _galaxy(self, s: Svg, cx: float, cy: float, size: float, tilt: float, color: str) -> None:
        """Small spiral galaxy seen at an angle: glowing core and two arms."""
        with s.group(transform=f"translate({cx:.1f} {cy:.1f}) rotate({tilt:.1f}) scale(1 0.42)"):
            s.circle(0, 0, size * 1.25, fill=s.radial(0, 0, size * 1.25, [(0, "#fff4dc", 0.55), (0.22, color, 0.32), (1, color, 0)]))
            for arm in range(2):
                pts = []
                for i in range(12):
                    a = arm * math.pi + i * 0.42
                    rr = size * (0.12 + 0.075 * i)
                    pts.append((math.cos(a) * rr, math.sin(a) * rr))
                s.path(smooth_open(pts), stroke=color, width=size * 0.2, opacity=0.18)
                s.path(smooth_open(pts[:9]), stroke="#ffffff", width=size * 0.06, opacity=0.22)
            s.circle(0, 0, size * 0.16, fill="#fffaf0", opacity=0.95)

    def _moon(self, s: Svg, cx: float, cy: float, r: float) -> None:
        """Pale cratered moon, lit from the upper left like everything else."""
        _glow(s, cx, cy, r * 3.0, "#d6dcff", 0.28)
        s.circle(cx, cy, r, fill=s.radial(cx - r * 0.35, cy - r * 0.4, r * 1.5, [(0, "#ffffff"), (0.45, "#e6e6fa"), (1, "#a9a8d6")]))
        for dx, dy, cr in ((-0.35, -0.2, 0.22), (0.25, -0.42, 0.13), (0.3, 0.25, 0.2), (-0.15, 0.45, 0.12), (0.55, -0.05, 0.1)):
            x, y, rr = cx + dx * r, cy + dy * r, cr * r
            s.circle(x, y, rr, fill="#b8b6dc", opacity=0.55)
            s.path(f"M{x - rr * 0.8:.2f} {y + rr * 0.3:.2f} A{rr:.2f} {rr:.2f} 0 0 0 {x + rr * 0.8:.2f} {y + rr * 0.3:.2f}", stroke="#ffffff",
                   width=rr * 0.28, opacity=0.5)
        s.circle(cx, cy, r, fill=s.radial(cx - r * 0.55, cy - r * 0.6, r * 2.1, [(0, "#0a0828", 0), (0.55, "#0a0828", 0), (0.78, "#140f3a", 0.55),
                                                                                (1, "#140f3a", 0.85)]))
        s.path(f"M{cx - r * 0.94:.2f} {cy + r * 0.3:.2f} A{r:.2f} {r:.2f} 0 0 1 {cx + r * 0.3:.2f} {cy - r * 0.95:.2f}", stroke="#ffffff",
               width=1.2, opacity=0.65)

    def _eclipse(self, s: Svg, cx: float, cy: float, r: float) -> None:
        """Black sun: a dark disc with a ragged gold-and-magenta corona."""
        _glow(s, cx, cy, r * 4.0, "#ff8ad0", 0.3)
        _glow(s, cx, cy, r * 2.0, "#ffe2a0", 0.6)
        for k in range(24):
            a = k * math.pi / 12 + 0.13
            ln = r * (0.45 + 0.55 * _hash(k, 5))
            w = 0.09 + 0.06 * _hash(k, 6)
            s.polygon([(cx + math.cos(a - w) * r * 0.96, cy + math.sin(a - w) * r * 0.96), (cx + math.cos(a) * (r + ln), cy + math.sin(a) * (r + ln)),
                       (cx + math.cos(a + w) * r * 0.96, cy + math.sin(a + w) * r * 0.96)], fill="#fff0c8", opacity=0.35)
        s.circle(cx, cy, r * 1.04, fill="#fff6d8", opacity=0.9)
        s.circle(cx, cy, r, fill=s.radial(cx, cy, r, [(0, "#05030c"), (0.85, "#0c0718"), (1, "#2a1230")]))

    def _planet(self, s: Svg, cx: float, cy: float, R: float) -> None:
        """Large ringed planet lit from the upper left; the ring passes behind
        and in front of the disc (no clipping: the halves are drawn apart)."""
        tilt = -14.0
        ring = [(2.2, 1.98, "#a993dc", 0.38), (1.93, 1.62, "#e2d4fb", 0.72), (1.56, 1.38, "#bba4ea", 0.5)]
        ratio = 0.21
        s.circle(cx, cy, R * 1.9, fill=s.radial(cx, cy, R * 1.9, [(0, "#c8a8ff", 0.3), (0.52, "#c8a8ff", 0.26), (0.62, "#c8a8ff", 0.08),
                                                                    (1, "#c8a8ff", 0)]))

        def band(o: float, i: float, front: bool) -> str:
            ro, ri = R * o, R * i
            if front:
                return (f"M{cx + ro:.2f} {cy:.2f} A{ro:.2f} {ro * ratio:.2f} 0 0 1 {cx - ro:.2f} {cy:.2f} L{cx - ri:.2f} {cy:.2f} "
                        f"A{ri:.2f} {ri * ratio:.2f} 0 0 0 {cx + ri:.2f} {cy:.2f} Z")
            return (f"M{cx - ro:.2f} {cy:.2f} A{ro:.2f} {ro * ratio:.2f} 0 0 1 {cx + ro:.2f} {cy:.2f} L{cx + ri:.2f} {cy:.2f} "
                    f"A{ri:.2f} {ri * ratio:.2f} 0 0 0 {cx - ri:.2f} {cy:.2f} Z")

        with s.group(transform=f"rotate({tilt:.1f} {cx:.1f} {cy:.1f})"):
            for o, i, color, op in ring:
                s.path(band(o, i, False), fill=s.linear(cx - R * o, 0, cx + R * o, 0, [(0, shade(color, 0.2)), (1, shade(color, -0.35))]),
                       opacity=op * 0.8)
            # the disc with latitude bands (clipped to the disc by construction)
            s.circle(cx, cy, R, fill=s.radial(cx - R * 0.38, cy - R * 0.42, R * 1.5, [(0, "#ffe6c8"), (0.3, "#f0b49e"), (0.58, "#b86ca6"),
                                                                                      (0.84, "#5c3a88"), (1, "#2c1c56")]))
            for y_c, half, color, op in ((-0.62, 0.07, "#fff4e0", 0.18), (-0.36, 0.1, "#6a2c78", 0.2), (-0.1, 0.06, "#fff0e6", 0.16),
                                         (0.16, 0.12, "#5a2a6e", 0.2), (0.44, 0.07, "#ffe8d8", 0.14), (0.66, 0.08, "#4a2462", 0.2)):
                y1, y2 = cy + (y_c - half) * R, cy + (y_c + half) * R
                ys = [y1 + (y2 - y1) * k / 6 for k in range(7)]
                left = [(cx - math.sqrt(max(0.0, R * R - (y - cy) ** 2)), y) for y in ys]
                right = [(cx + math.sqrt(max(0.0, R * R - (y - cy) ** 2)), y) for y in reversed(ys)]
                s.path(_poly(left + right), fill=color, opacity=op)
            # shadow of the ring on the disc
            pts = []
            for k in range(41):
                a = math.pi * k / 40
                x, y = cx + math.cos(a) * R * 1.75, cy - R * 0.1 + math.sin(a) * R * 1.75 * ratio
                if (x - cx) ** 2 + (y - cy) ** 2 < (R - 1.5) ** 2:
                    pts.append((x, y))
            if len(pts) > 1:
                s.path(_line(pts), stroke="#1c1038", width=R * 0.1, opacity=0.4)
            # terminator (dark side toward the lower right) and the lit rim
            s.circle(cx, cy, R, fill=s.radial(cx - R * 0.55, cy - R * 0.6, R * 2.15, [(0, "#0a0626", 0), (0.5, "#0a0626", 0), (0.74, "#120a34", 0.5),
                                                                                      (1, "#120a34", 0.9)]))
            s.path(f"M{cx - R * 0.98:.2f} {cy + R * 0.2:.2f} A{R:.2f} {R:.2f} 0 0 1 {cx + R * 0.1:.2f} {cy - R * 0.99:.2f}", stroke="#ffe8d6",
                   width=1.6, opacity=0.75)
            for o, i, color, op in ring:
                s.path(band(o, i, True), fill=s.linear(cx - R * o, 0, cx + R * o, 0, [(0, shade(color, 0.25)), (0.6, color), (1, shade(color, -0.4))]),
                       opacity=op)
            s.path(f"M{cx + R * 1.93:.2f} {cy:.2f} A{R * 1.93:.2f} {R * 1.93 * ratio:.2f} 0 0 1 {cx - R * 1.93:.2f} {cy:.2f}", stroke="#ffffff",
                   width=0.8, opacity=0.45)

    # ------------------------------------------------------------------ sky extras
    def _nebula_wisp(self, seed: int, w: float, h: float, colors: tuple[str, str]) -> Svg:
        """Drifting nebula veil: soft lobes with a brighter core and a few stars."""
        r = Rand(seed)
        s = Svg(w, h)
        base, core = colors
        n = 6
        for i in range(n):
            t = i / (n - 1)
            ry = h * (0.16 + 0.16 * math.sin(math.pi * t)) + r.uniform(-2, 2)
            cx = w * (0.14 + 0.72 * t) + r.uniform(-8, 8)
            cy = h * 0.5 + r.uniform(-h * 0.1, h * 0.1)
            rx = min(ry * r.uniform(1.8, 2.6), cx - 2, w - cx - 2)
            _soft(s, cx, cy, rx, min(ry, cy - 2, h - cy - 2), base, r.uniform(0.18, 0.26), 0.2, r.uniform(-12, 12))
        for i in range(3):
            cx = w * (0.3 + 0.2 * i) + r.uniform(-10, 10)
            _soft(s, cx, h * 0.5 + r.uniform(-5, 5), w * 0.12, h * 0.1, core, 0.18, 0.2, r.uniform(-10, 10))
        for _ in range(9):
            x, y = r.uniform(w * 0.15, w * 0.85), r.uniform(h * 0.3, h * 0.7)
            s.circle(x, y, r.uniform(0.5, 1.1), fill="#ffffff", opacity=r.uniform(0.5, 0.9))
        return s

    def _shooting_star(self, seed: int, w: float, h: float) -> Svg:
        """Meteor streak falling to the lower right: a tapered glowing trail and a bright head."""
        r = Rand(seed)
        s = Svg(w, h)
        hx, hy = w - 16, h - 14
        tx, ty = 6.0, 8.0
        dx, dy = hx - tx, hy - ty
        ln = math.hypot(dx, dy)
        nx, ny = -dy / ln, dx / ln
        for width, color, op in ((7.0, "#9fc8ff", 0.22), (3.2, "#dff0ff", 0.55), (1.3, "#ffffff", 1.0)):
            pts = [(tx, ty), (hx + nx * width / 2, hy + ny * width / 2), (hx + dx / ln * width * 0.4, hy + dy / ln * width * 0.4),
                   (hx - nx * width / 2, hy - ny * width / 2)]
            s.polygon(pts, fill=s.linear(tx, ty, hx, hy, [(0, color, 0), (0.6, color, op * 0.45), (1, color, op)]))
        _glow(s, hx, hy, 12, "#cfe6ff", 0.55)
        _sparkle(s, hx, hy, 7.5, 0.95)
        s.circle(hx, hy, 1.8, fill="#ffffff")
        for _ in range(5):  # sparks shed along the trail
            t = r.uniform(0.45, 0.9)
            x, y = tx + dx * t + nx * r.uniform(-5, 5), ty + dy * t + ny * r.uniform(-5, 5)
            s.circle(x, y, r.uniform(0.5, 1.0), fill=r.choice(["#ffffff", "#ffe6a8"]), opacity=r.uniform(0.5, 0.9))
        return s

    def _dust_particle(self, kind: str) -> Svg:
        """Weather sprites: falling star dust (drawn as ``particle.<name>``)."""
        s = Svg(16, 16)
        if kind == "gold":
            _glow(s, 8, 8, 7.8, GOLD_LIGHT, 0.55)
            s.polygon(star_points(8, 8, 5.4, 1.3, 4), fill=GOLD_HI)
            s.circle(8, 8, 1.2, fill="#ffffff")
        elif kind == "spark":
            _glow(s, 8, 8, 6.5, "#d8e4ff", 0.4)
            s.polygon(star_points(8, 8, 4.2, 1.6, 6), fill="#ffffff", opacity=0.95)
        else:
            _glow(s, 8, 8, 6.0, "#cfe0ff", 0.55)
            s.circle(8, 8, 1.7, fill="#ffffff")
        return s

    def sky_extras(self) -> dict[str, PropSpec]:
        extras = {
            "sc.cloud.0": PropSpec(lambda: self._nebula_wisp(5, 300, 84, ("#4fd8cc", "#c8fff6")), (0, 0)),
            "sc.cloud.1": PropSpec(lambda: self._shooting_star(9, 230, 66), (0, 0)),
            "sc.cloud.2": PropSpec(lambda: self._nebula_wisp(17, 340, 96, ("#c060d8", "#ffc8f0")), (0, 0)),
        }
        # weather sprites resolve as ``particle.<name>`` (see ``weather``)
        for kind in ("gold", "white", "spark"):
            extras[f"particle.sc_dust_{kind}"] = PropSpec((lambda k=kind: self._dust_particle(k)), (8, 8))
        return extras

    def weather(self) -> Weather:
        # ``colors`` name particle sprites (registered in ``sky_extras``): gold and white star dust drifting down
        return Weather("stars", 0.55, ("sc_dust_gold", "sc_dust_white", "sc_dust_white", "sc_dust_spark"), wind=7.0)

    # ------------------------------------------------------------------ parallax layers
    def _spire(self, s: Svg, r: Rand, x: float, base: float, wd: float, ht: float, fill: str, rim: str, window: str,
               roof: str = "cone", glow_tip: bool = False) -> None:
        """Slender citadel tower: slightly tapered body, roof, rows of lit
        windows, string courses and a rim light on the lit (left) edge."""
        top = base - ht
        tw = wd * 0.82  # width under the roof
        s.polygon([(x - wd / 2, base + 2), (x - tw / 2, top), (x + tw / 2, top), (x + wd / 2, base + 2)], fill=fill)
        s.line(x - wd / 2 + 0.6, base, x - tw / 2 + 0.6, top + 2, rim, 1.0, 0.75)
        for k in range(1, int(ht / 30) + 1):  # string courses
            yy = top + k * 30 - 6
            half = (tw + (wd - tw) * (yy - top) / ht) / 2 + 1.2
            s.rect(x - half, yy, half * 2, 2.2, fill=fill)
            s.line(x - half, yy, x + half, yy, rim, 0.6, 0.5)
        if roof == "cone":
            tip = top - tw * 2.6
            s.polygon([(x - tw * 0.66, top + 1), (x, tip), (x + tw * 0.66, top + 1)], fill=fill)
            s.line(x - tw * 0.66, top + 1, x, tip, rim, 0.8, 0.75)
        elif roof == "dome":
            tip = top - tw * 0.95
            s.path(f"M{x - tw * 0.62:.1f} {top + 1:.1f} Q{x - tw * 0.66:.1f} {tip:.1f} {x:.1f} {tip:.1f} Q{x + tw * 0.66:.1f} {tip:.1f} "
                   f"{x + tw * 0.62:.1f} {top + 1:.1f} Z", fill=fill)
            s.path(f"M{x - tw * 0.62:.1f} {top + 1:.1f} Q{x - tw * 0.66:.1f} {tip:.1f} {x:.1f} {tip:.1f}", stroke=rim, width=0.8, opacity=0.75)
            tip -= 7
            s.line(x, tip + 7, x, tip, fill, 1.2)
        elif roof == "crystal":  # a glowing crystal set on a short cone
            s.polygon([(x - tw * 0.6, top + 1), (x, top - tw * 1.1), (x + tw * 0.6, top + 1)], fill=fill)
            tip = top - tw * 1.1 - 12
            _glow(s, x, tip + 5, 12, GLOW_TEAL, 0.5)
            s.polygon([(x, tip), (x + 2.6, tip + 6), (x, tip + 12), (x - 2.6, tip + 6)], fill=s.linear(x, tip, x, tip + 12, [(0, "#f0fffc"),
                                                                                                         (1, GLOW_TEAL)]))
        else:  # crown of points
            tip = top - 7
            for k in range(3):
                px = x - tw * 0.35 + k * tw * 0.35
                s.polygon([(px - tw * 0.16, top + 1), (px, top - 7 - (3 if k == 1 else 0)), (px + tw * 0.16, top + 1)], fill=fill)
        if glow_tip and roof != "crystal":
            _glow(s, x, tip, 7, GLOW_TEAL, 0.6)
            s.circle(x, tip, 1.3, fill="#e8fffb")
        rows = int((ht - 16) / 12)
        cols = 1 if wd < 14 else 2
        for j in range(rows):
            for c in range(cols):
                if r.next() < 0.42:
                    wx = x + (c - (cols - 1) / 2) * wd * 0.4
                    wy = top + 9 + j * 12
                    s.path(f"M{wx - 0.9:.2f} {wy + 3.8:.2f} L{wx - 0.9:.2f} {wy + 0.9:.2f} Q{wx:.2f} {wy - 0.2:.2f} {wx + 0.9:.2f} {wy + 0.9:.2f} "
                           f"L{wx + 0.9:.2f} {wy + 3.8:.2f} Z", fill=window, opacity=0.95)

    def _island(self, s: Svg, r: Rand, cx: float, top: float, wd: float, depth: float, pal: dict[str, str]) -> None:
        """Floating rock: inverted craggy cone, lit left facets, glowing crystals at the tip."""
        left = cx - wd / 2
        tip_x = cx + r.uniform(-wd * 0.08, wd * 0.08)
        pts: list[Pt] = [(left, top)]
        n = 7
        for i in range(1, n):
            t = i / n
            pts.append((left + wd * t * 0.5 + r.uniform(-4, 4), top + depth * (t ** 1.4) * 0.92 + r.uniform(-3, 3)))
        pts.append((tip_x, top + depth))
        for i in range(n - 1, 0, -1):
            t = i / n
            pts.append((left + wd - wd * t * 0.5 + r.uniform(-4, 4), top + depth * (t ** 1.4) * 0.92 + r.uniform(-3, 3)))
        pts.append((left + wd, top))
        s.path(_poly(pts), fill=s.linear(0, top, 0, top + depth, [(0, pal["rock"]), (1, pal["rock_low"])]))
        mid = len(pts) // 2
        s.path(_poly(pts[: mid + 1] + [(cx - wd * 0.12, top + 4)]), fill=pal["lit"], opacity=0.35)
        for i in range(1, mid - 1, 2):  # crags
            x, y = pts[i]
            s.line(x + 3, y + 1, x + wd * 0.12, y + depth * 0.1, pal["line"], 1.0, 0.5)
        s.rect(left - 2, top - 3, wd + 4, 5, fill=pal["rock"], rx=2)
        s.line(left - 1, top - 2.6, left + wd + 1, top - 2.6, pal["lit"], 1.0, 0.8)
        _glow(s, tip_x, top + depth + 4, wd * 0.22, pal["glow"], 0.45)
        for k in range(3):
            _crystal(s, tip_x + (k - 1) * 4.5, top + depth - 6, 180 + (k - 1) * 22, 9 + 4 * (k == 1), 3.4, "#e6fffb", pal["glow"],
                     pal["line"], 0.5, 0.9)

    def _far(self, seed: int) -> Svg:
        """Distant floating citadels: spire clusters on rock islands, windows lit."""
        w, h = 1200.0, 300.0
        s = Svg(w, h)
        r = Rand(seed)
        pal = {"rock": "#211c4c", "rock_low": "#171338", "lit": "#3c3482", "line": "#120e30", "glow": "#7fe8e0"}
        fill, rim, window = "#1d1946", "#40388a", "#ffcf72"
        # tiny drifting rocks far away
        for _ in range(10):
            x, y = r.uniform(30, w - 30), r.uniform(60, 230)
            rr = r.uniform(2, 5)
            s.path(blob(x, y, rr * 1.4, rr, 0.2, seed=x), fill="#1c1844")
            s.line(x - rr * 1.1, y - rr * 0.5, x + rr * 0.2, y - rr * 0.95, rim, 0.6, 0.6)
        specs = [(w * 0.2 + r.uniform(-50, 50), r.uniform(196, 212), r.uniform(230, 280)),
                 (w * 0.66 + r.uniform(-40, 40), r.uniform(188, 206), r.uniform(260, 320))]
        for i, (cx, top, wd) in enumerate(specs):
            _glow(s, cx, top - 60, wd * 0.62, "#8a6ad8", 0.14)
            # towers: a dominant central spire, flanking towers stepping down
            towers = []
            n = 5 + int(r.next() * 3)
            main = n // 2
            for k in range(n):
                t = (k + 0.5) / n
                tx = cx - wd * 0.38 + wd * 0.76 * t + r.uniform(-5, 5)
                prof = math.sin(math.pi * t) ** 0.9
                ht = 30 + 105 * prof * r.uniform(0.7, 1.0) + (48 if k == main else 0)
                tw = r.uniform(18, 22) if k == main else r.uniform(9, 16)
                roof = "crystal" if k == main else r.choice(["cone", "cone", "dome", "crown"])
                if roof == "dome" and tw < 12:
                    roof = "cone"
                towers.append((ht, tx, tw, roof))
            ordered = sorted(towers, key=lambda tw: tw[1])
            for (ha, xa, _wa, _ra), (hb, xb, _wb, _rb) in zip(ordered, ordered[1:]):  # sky bridges
                by = top - min(ha, hb) * 0.55
                s.path(f"M{xa:.1f} {by:.1f} Q{(xa + xb) / 2:.1f} {by + 8:.1f} {xb:.1f} {by:.1f} L{xb:.1f} {by + 3:.1f} "
                       f"Q{(xa + xb) / 2:.1f} {by + 11:.1f} {xa:.1f} {by + 3:.1f} Z", fill=fill)
            for ht, tx, tw, roof in sorted(towers, reverse=True):  # tallest behind
                self._spire(s, r, tx, top, tw, ht, fill, rim, window if r.next() < 0.75 else "#9ff0ff", roof, glow_tip=ht > 110)
            # curtain wall along the island lip, with lit arches and merlons
            wl, wr = cx - wd * 0.44, cx + wd * 0.44
            wall_top = top - 16
            s.rect(wl, wall_top, wr - wl, 17, fill=fill)
            x = wl
            while x < wr - 3:
                s.rect(x, wall_top - 3.5, 3.6, 3.6, fill=fill)
                x += 6.5
            s.line(wl, wall_top, wr, wall_top, rim, 0.7, 0.6)
            for k in range(int((wr - wl) / 22)):
                ax = wl + 11 + k * 22
                if r.next() < 0.6:
                    s.path(f"M{ax - 2.4:.1f} {top - 1:.1f} L{ax - 2.4:.1f} {top - 8:.1f} Q{ax:.1f} {top - 11:.1f} {ax + 2.4:.1f} {top - 8:.1f} "
                           f"L{ax + 2.4:.1f} {top - 1:.1f} Z", fill=window, opacity=0.85)
            self._island(s, r, cx, top, wd, r.uniform(70, 90), pal)
        return s

    def _stone_ring(self, s: Svg, cx: float, cy: float, rx: float, ry: float, tilt: float, front: bool, pal: dict[str, str],
                    thick: float = 0.16) -> None:
        """Half of an orbiting ring of carved stone blocks (back or front half)."""
        n = 18
        with s.group(transform=f"rotate({tilt:.1f} {cx:.1f} {cy:.1f})"):
            for k in range(n):
                a0 = math.pi * k / n + (0.0 if front else math.pi) + 0.02
                a1 = math.pi * (k + 1) / n + (0.0 if front else math.pi) - 0.02
                outer = [(cx + math.cos(a) * rx, cy + math.sin(a) * ry) for a in (a0, (a0 + a1) / 2, a1)]
                inner = [(cx + math.cos(a) * rx * (1 - thick), cy + math.sin(a) * ry * (1 - thick)) for a in (a1, (a0 + a1) / 2, a0)]
                lit = 0.5 + 0.5 * math.cos((a0 + a1) / 2 - math.radians(200))
                color = mix(pal["ring_dark"], pal["ring"], lit if front else lit * 0.5)
                s.polygon(outer + inner, fill=color, stroke=pal["line"], width=0.8)
                if front and k % 3 == 1:
                    mx, my = cx + math.cos((a0 + a1) / 2) * rx * (1 - thick / 2), cy + math.sin((a0 + a1) / 2) * ry * (1 - thick / 2)
                    s.circle(mx, my, 1.4, fill=GOLD_LIGHT, opacity=0.85)
            if front:
                pts = [(cx + math.cos(math.pi * k / 24) * rx, cy + math.sin(math.pi * k / 24) * ry) for k in range(1, 24)]
                s.path(_line(pts), stroke=pal["rim"], width=0.9, opacity=0.6)

    def _dome(self, s: Svg, x: float, base: float, wd: float, pal: dict[str, str]) -> None:
        """Observatory: drum, ribbed dome with an open slit and a brass telescope."""
        drum_h = wd * 0.32
        s.rect(x - wd / 2, base - drum_h, wd, drum_h + 1, fill=pal["rock"])
        s.line(x - wd / 2, base - drum_h, x + wd / 2, base - drum_h, pal["rim"], 1.0, 0.8)
        for k in range(3):
            wx = x - wd * 0.3 + k * wd * 0.3
            s.path(f"M{wx - 2:.1f} {base - 3:.1f} L{wx - 2:.1f} {base - drum_h + 7:.1f} Q{wx:.1f} {base - drum_h + 4:.1f} {wx + 2:.1f} "
                   f"{base - drum_h + 7:.1f} L{wx + 2:.1f} {base - 3:.1f} Z", fill="#ffcf72", opacity=0.9)
        cy = base - drum_h
        rad = wd * 0.5
        s.path(f"M{x - rad:.1f} {cy:.1f} A{rad:.1f} {rad * 0.92:.1f} 0 0 1 {x + rad:.1f} {cy:.1f} Z",
               fill=s.linear(x - rad, cy - rad, x + rad, cy, [(0, pal["dome_hi"]), (0.5, pal["dome"]), (1, pal["dome_dark"])]))
        for k in range(1, 6):
            a = math.pi * k / 6
            s.path(f"M{x:.1f} {cy - rad * 0.92:.1f} Q{x + math.cos(math.pi - a) * rad * 0.7:.1f} {cy - rad * 0.8:.1f} "
                   f"{x + math.cos(math.pi - a) * rad:.1f} {cy:.1f}", stroke=GOLD_DARK, width=0.8, opacity=0.7)
        # slit with telescope
        s.polygon([(x - 3, cy - rad * 0.9), (x + 3, cy - rad * 0.9), (x + 4, cy), (x - 4, cy)], fill="#0a0826")
        s.line(x - 1, cy - rad * 0.4, x + rad * 0.9, cy - rad * 1.3, "#7a5a26", 4.2)
        s.line(x - 1, cy - rad * 0.4, x + rad * 0.9, cy - rad * 1.3, GOLD, 2.2)
        s.circle(x + rad * 0.9, cy - rad * 1.3, 2.4, fill=GOLD_LIGHT)
        _glow(s, x + rad * 0.9, cy - rad * 1.3, 6, "#fff2c0", 0.5)
        s.path(f"M{x - rad:.1f} {cy:.1f} A{rad:.1f} {rad * 0.92:.1f} 0 0 1 {x - rad * 0.2:.1f} {cy - rad * 0.9:.1f}", stroke=pal["rim"], width=1.2,
               opacity=0.8)

    def _mid(self, seed: int) -> Svg:
        """Orbiting stone rings and observatory domes on floating rocks, with
        constellations drawn between them."""
        w, h = 1100.0, 280.0
        s = Svg(w, h)
        r = Rand(seed)
        pal = {"rock": "#2a2862", "rock_low": "#1a1844", "lit": "#5048a0", "line": "#120f34", "glow": "#b294ff", "rim": "#7a70d0",
               "ring": "#6a64b8", "ring_dark": "#26245a", "dome": "#3a4a9a", "dome_hi": "#6a7ad0", "dome_dark": "#1e2458"}
        observatory = seed % 2 == 0
        # constellations in the open sky of the strip (kept inside the strip so it tiles)
        for k in range(3):
            x0 = 60 + k * 350 + r.uniform(-20, 20)
            pts, edges = _constellation_shape(seed * 5 + k, 31, x0, x0 + r.uniform(150, 220), 26, 110)
            for a, b in edges:
                s.line(pts[a][0], pts[a][1], pts[b][0], pts[b][1], GOLD_LIGHT, 1.0, 0.42)
                s.line(pts[a][0], pts[a][1], pts[b][0], pts[b][1], GOLD_LIGHT, 3.4, 0.08)
            for i, (x, y) in enumerate(pts):
                _glow(s, x, y, 7 if i % 2 else 10, GOLD_LIGHT, 0.4)
                s.circle(x, y, 1.6 if i % 2 else 2.1, fill=GOLD_HI)
        # floating rocks: one carries a dome or an orbiting ring, the others are small
        rocks = [(w * 0.3 + r.uniform(-40, 40), r.uniform(176, 190), r.uniform(150, 190)), (w * 0.76 + r.uniform(-30, 30), r.uniform(196, 210),
                                                                                             r.uniform(90, 120))]
        for i, (cx, top, wd) in enumerate(rocks):
            ring = (i == 0) != observatory
            if ring:
                self._stone_ring(s, cx, top - 18, wd * 0.85, wd * 0.2, -9, False, pal)
            if i == 0 and observatory:
                self._dome(s, cx - wd * 0.12, top - 1, wd * 0.36, pal)
                s.rect(cx + wd * 0.12, top - 34, 16, 34, fill=pal["rock"])
                s.line(cx + wd * 0.12, top - 34, cx + wd * 0.12, top, pal["rim"], 1.0, 0.7)
                s.polygon([(cx + wd * 0.12 - 3, top - 34), (cx + wd * 0.12 + 8, top - 50), (cx + wd * 0.12 + 19, top - 34)], fill=pal["rock"])
                s.rect(cx + wd * 0.12 + 6, top - 26, 3.4, 6, fill="#ffcf72")
            elif ring:
                _crystal(s, cx, top + 1, 0, 40, 15, "#e8f0ff", "#7a70d8", INK, 0.9)
                _crystal(s, cx - 11, top + 1, -18, 24, 10, "#e8f0ff", "#6a62c8", INK, 0.8)
                _crystal(s, cx + 11, top + 1, 20, 20, 9, "#e8f0ff", "#6a62c8", INK, 0.8)
                _glow(s, cx, top - 18, 34, "#b8a8ff", 0.3)
            else:
                for k in range(2):
                    px = cx - wd * 0.2 + k * wd * 0.4
                    s.rect(px - 3, top - 22 - k * 6, 6, 22 + k * 6, fill=pal["rock"])
                    s.line(px - 3, top - 22 - k * 6, px - 3, top, pal["rim"], 0.8, 0.7)
                    s.rect(px - 5, top - 25 - k * 6, 10, 3.4, fill=pal["rock"])
                    _glow(s, px, top - 31 - k * 6, 6, "#ffd88a", 0.5)
                    s.circle(px, top - 30 - k * 6, 1.6, fill="#fff2c4")
            self._island(s, r, cx, top, wd, r.uniform(48, 64), pal)
            if ring:
                self._stone_ring(s, cx, top - 18, wd * 0.85, wd * 0.2, -9, True, pal)
        return s

    def _shard(self, s: Svg, x: float, y: float, size: float, angle: float, light: str, dark: str, glow: str) -> None:
        """A drifting crystal shard (double-pointed) with a soft glow."""
        _glow(s, x, y, size * 1.6, glow, 0.25)
        _crystal(s, x, y, angle, size * 0.62, size * 0.36, light, dark, INK, 0.6, 0.92)
        _crystal(s, x, y, angle + 180, size * 0.42, size * 0.36, light, dark, INK, 0.6, 0.92)

    def _near(self, seed: int) -> Svg:
        """Drifting star dust and crystal shards; a luminous mist (the abyss)
        lies below, visible through pits. Kept dim so creatures read on top."""
        w, h = 900.0, 210.0
        s = Svg(w, h)
        r = Rand(seed)
        s.rect(0, 120, w, 90, fill=s.linear(0, 120, 0, h, [(0, "#4a2c8a", 0), (0.55, "#4a2c8a", 0.35), (1, "#5a3496", 0)]))
        for k in range(4):
            cx = (k + 0.5) * w / 4 + r.uniform(-40, 40)
            _soft(s, cx, 172 + r.uniform(-8, 8), r.uniform(90, 130), 22, r.choice([NEBULA_TEAL, "#8a5ae0", NEBULA_MAGENTA]), 0.12, 0.2)
        # star dust drifts: wavy bands of motes
        for band in range(2):
            y0 = 70 + band * 50 + r.uniform(-10, 10)
            for i in range(46):
                x = r.uniform(0, w)
                y = y0 + 12 * math.sin(x / w * 2 * math.pi * (2 + band) + seed) + r.uniform(-9, 9)
                if r.next() < 0.12:
                    _sparkle(s, x, y, r.uniform(1.6, 2.6), 0.7, r.choice(["#ffffff", GOLD_HI]))
                else:
                    s.circle(x, y, r.uniform(0.5, 1.1), fill=r.choice(["#ffffff", "#cfe0ff", GOLD_LIGHT]), opacity=r.uniform(0.35, 0.8))
        # crystal shards (kept inside the strip)
        for _ in range(6):
            size = r.uniform(12, 30)
            x, y = r.uniform(size + 10, w - size - 10), r.uniform(40, 150)
            light, dark, glow = r.choice([("#e6f0ff", "#6a62c8", GLOW_VIOLET), ("#e0fffb", "#3a9aa8", GLOW_TEAL), ("#ffe8fb", "#a24aa8", GLOW_MAGENTA)])
            self._shard(s, x, y, size, r.uniform(-50, 50), light, dark, glow)
        return s

    def layer_art(self) -> dict[str, PropSpec]:
        art = {}
        for i in range(2):
            art[f"sc.far.{i}"] = PropSpec((lambda i=i: self._far(11 + i * 7)), (0, 0))
            art[f"sc.mid.{i}"] = PropSpec((lambda i=i: self._mid(20 + i)), (0, 0))
            art[f"sc.near.{i}"] = PropSpec((lambda i=i: self._near(41 + i * 3)), (0, 0))
        return art

    def layers(self) -> list[Layer]:
        return [
            Layer("far", 0.06, ["sc.far.0", "sc.far.1"], 1200, 62, vertical=0.04),
            Layer("mid", 0.22, ["sc.mid.0", "sc.mid.1"], 1100, 52, vertical=0.14),
            Layer("near", 0.46, ["sc.near.0", "sc.near.1"], 900, 44, vertical=0.32),
        ]

    # ------------------------------------------------------------------ terrain
    def terrain(self, style: str, w: float, h: float, seed: int, left: bool, right: bool, top: bool = True, x0: float = 0.0,
                surface: str = "normal") -> Svg:
        """Terrain chunk art. Everything that crosses chunk borders (veins,
        gold flecks, constellation inlays, crystal trim, mirror reflections,
        masonry courses) is a function of the world x (``x0`` + local x), so
        adjacent chunks join seamlessly; only hanging edges are outlined,
        never the chunk's vertical borders."""
        if style == "cave":
            return self._cave(w, h, seed, left, right, top, x0)
        if style == "fortress":
            return self._fortress(w, h, seed, left, right, top, x0, surface)
        hr = self.terrain_headroom
        s = Svg(w, h + hr)
        ice = surface == "ice"
        self._starstone(s, w, h, hr, left, right, x0, top, ice and top)
        if top:
            if ice:
                self._mirror_cap(s, w, hr, left, right, x0)
            else:
                self._crystal_cap(s, w, hr, left, right, x0)
        return s

    @staticmethod
    def _halo_band(s: Svg, w: float, y0: float, height: float, color: str, alpha: float, right: bool) -> None:
        """Faint light rising above a walkable edge. Scene chunks overlap by
        1.5 u (scene.CHUNK pieces), so a translucent band stops short of the
        overlap on inner chunks instead of doubling up into a seam line."""
        s.rect(0, y0 - height, w if right else max(0.0, w - 1.5), height, fill=s.linear(0, y0 - height, 0, y0, [(0, color, 0), (1, color, alpha)]))

    def _starstone(self, s: Svg, w: float, h: float, y0: float, left: bool, right: bool, x0: float, top: bool, glazed: bool,
                   under: float = 0.0) -> None:
        """Lapis-like star-stone: veins, gold flecks and gold constellation
        inlays. Thin slabs (h <= 100) get a craggy underside with crystals
        hanging from it; ``under`` is extra art room below the slab."""
        bottom = h + y0
        thin = h <= 100
        il, ir = (2.5 if left else 0.0), (2.5 if right else 0.0)
        rock_bottom = bottom - (8.0 if thin and under <= 0 else 0.0)
        ys = [y0 + 3 + (rock_bottom - y0 - 3) * i / 10 for i in range(11)]
        lface = [(il + 0.9 * math.sin(y * 0.23 + x0 * 0.01), y) for y in ys] if left else [(-0.5, y) for y in ys]
        rface = [(w - ir - 0.9 * math.sin(y * 0.19 + x0 * 0.013), y) for y in ys] if right else [(w + 0.5, y) for y in ys]
        if thin:
            under_edge = [(lx, rock_bottom - 1.5 - 2.5 * abs(_wobble((x0 + lx) * 1.7, 4.2))) for lx in _samples(w, 5.0)]
            under_edge = [(max(lface[-1][0], min(rface[-1][0], x)), y) for x, y in under_edge]
        else:
            under_edge = []
        body = [(lface[0][0], y0)] + lface + under_edge + list(reversed(rface)) + [(rface[0][0], y0)]
        s.path(_poly(body), fill=s.linear(0, y0, 0, y0 + min(h, 210), [(0, STONE_TOP), (0.2, STONE), (0.6, STONE_DARK), (1, STONE_DEEP)]))
        if glazed:  # the mirror floor throws a cool reflection down the stone
            s.rect(il, y0 + 10, w - il - ir, 40, fill=s.linear(0, y0 + 10, 0, y0 + 50, [(0, "#a9bcff", 0.32), (1, "#a9bcff", 0)]))
        xs = _samples(w, 4.0)
        # lapis veins: lighter bands with calcite threads and dark seams (world-aligned)
        for k in range(4):
            def yy(lx: float, k: int = k) -> float:
                gx = x0 + lx
                return y0 + 30 + k * 27 + 3.5 * _wobble(gx * 0.8, k * 1.7) + 5 * math.sin(gx * 0.005 + k)
            if y0 + 30 + k * 27 > bottom - 10:
                break
            band = [(lx, yy(lx)) for lx in xs] + [(lx, yy(lx) + 6 + 2 * math.sin((x0 + lx) * 0.03 + k)) for lx in reversed(xs)]
            s.path(_poly(band), fill="#4a58b0", opacity=0.2)
            s.path(_line([(lx, yy(lx) + 7.5 + 2 * math.sin((x0 + lx) * 0.03 + k)) for lx in xs]), stroke=STONE_LINE, width=1.2, opacity=0.35)
            for run in self._runs(xs, lambda lx, k=k: math.sin((x0 + lx) * 0.021 + k * 2.3) + 0.5 * math.sin((x0 + lx) * 0.07 + k) > 0.55):
                s.path(_line([(lx, yy(lx) + 0.4) for lx in run]), stroke="#d6dcff", width=0.7, opacity=0.3)
        # gold (pyrite) flecks and white specks on a world lattice
        cell = 7.0
        depth = min(bottom - 6, y0 + 132)
        for i in range(math.floor(x0 / cell), math.floor((x0 + w) / cell) + 1):
            for j in range(int((depth - y0 - 14) / cell)):
                n = i * 92821 + j * 68917
                v = _hash(n, 5)
                if v < 0.8:
                    continue
                lx = i * cell + cell * _hash(n, 6) - x0
                if not 1.5 < lx < w - 1.5:
                    continue
                ly = y0 + 14 + j * cell + cell * _hash(n, 7)
                fade = 1 - (ly - y0) / 150
                if v > 0.985:
                    _sparkle(s, lx, ly, 1.8 + 0.8 * _hash(n, 8), 0.9 * fade, GOLD_HI)
                elif v > 0.87:
                    s.circle(lx, ly, 0.45 + 0.6 * _hash(n, 8), fill=GOLD_LIGHT, opacity=(0.55 + 0.4 * _hash(n, 9)) * fade)
                else:
                    s.circle(lx, ly, 0.4 + 0.35 * _hash(n, 8), fill="#e6ecff", opacity=0.45 * fade)
        # gold constellation inlays: one figure per world cell (some cells left
        # plain), kept in the band of stone that is on screen under the floor
        span = 112.0
        y_lo, y_hi = y0 + 19, min(rock_bottom - 10, y0 + 66)
        if y_hi - y_lo >= 14:
            for n in range(math.floor(x0 / span) - 1, math.floor((x0 + w) / span) + 1):
                if _hash(n, 41) < 0.25:
                    continue
                pts, edges = _constellation_shape(n, 50, n * span + 12 - x0, n * span + span - 12 - x0, y_lo, y_hi)
                _inlay(s, pts, edges, 1.0, 0.4)
        # exposed faces: lit left face, shadowed right face (outlined)
        if left:
            s.path(_poly(lface + [(x + 7, y) for x, y in reversed(lface)]), fill=s.linear(il, 0, il + 7, 0, [(0, "#8a96ea", 0.45), (1, "#8a96ea", 0)]))
            s.path(_line(lface), stroke=STONE_LINE, width=1.4)
        if right:
            s.path(_poly(rface + [(x - 9, y) for x, y in reversed(rface)]), fill=s.linear(w - ir, 0, w - ir - 9, 0, [(0, "#04051a", 0.6),
                                                                                                                (1, "#04051a", 0)]))
            s.path(_line(rface), stroke=STONE_LINE, width=1.4)
        if thin:
            self._hanging_crystals(s, under_edge, x0, il, w - ir, bottom + under - 0.5)

    @staticmethod
    def _runs(xs: Sequence[float], keep) -> list[list[float]]:
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

    def _hanging_crystals(self, s: Svg, edge: Sequence[Pt], x0: float, xmin: float, xmax: float, limit: float,
                          light: str = "#eef2ff", dark: str = "#6a70d0") -> None:
        """Craggy underside of a thin slab (``edge``, left to right): a dark
        rim and crystals hanging from it (world-aligned), never below ``limit``."""
        if len(edge) < 2:
            return
        s.path(_line(edge), stroke=STONE_LINE, width=1.3)
        s.path(_line([(x, y - 1.6) for x, y in edge]), stroke="#6f78d0", width=1.2, opacity=0.45)

        def edge_y(lx: float) -> float:
            for (ax, ay), (bx, by) in zip(edge, edge[1:]):
                if ax <= lx <= bx:
                    return ay + (by - ay) * (lx - ax) / max(1e-6, bx - ax)
            return edge[-1][1]

        slot = 17.0
        for n in range(math.floor(x0 / slot), math.floor((x0 + xmax) / slot) + 1):
            if _hash(n, 61) < 0.38:
                continue
            lx = (n + 0.5) * slot - x0 + (_hash(n, 62) - 0.5) * 6
            wd = 3.2 + 2.2 * _hash(n, 63)
            if not xmin + wd < lx < xmax - wd:
                continue
            ey = edge_y(lx) - 1.2
            ln = min(4 + 11 * _hash(n, 64), limit - ey)
            if ln < 3:
                continue
            _crystal(s, lx, ey, 180 + (_hash(n, 65) - 0.5) * 20, ln, wd, light, dark, CRYSTAL_LINE, 0.6)
            if _hash(n, 66) > 0.5 and lx + wd * 1.6 < xmax:
                _crystal(s, lx + wd * 0.9, edge_y(lx + wd * 0.9) - 1.0, 198, ln * 0.55, wd * 0.7, light, dark, CRYSTAL_LINE, 0.5)

    def _crystal_cap(self, s: Svg, w: float, y0: float, left: bool, right: bool, x0: float, hang: bool = True) -> None:
        """White-crystal rim: a cut-crystal trim with a faint glow and crystal
        points hanging from its front (all world-aligned)."""
        xs = _samples(w, 2.0)

        def top_y(lx: float) -> float:
            y = y0 - 1.3 + 0.3 * math.sin((x0 + lx) * 0.21)
            if left and lx < 5:
                y += 3.0 * (1 - lx / 5) ** 2
            if right and w - lx < 5:
                y += 3.0 * (1 - (w - lx) / 5) ** 2
            return y

        low = y0 + 7.0
        # faint glow rising from the crystal and the shadow it casts on the stone
        self._halo_band(s, w, y0, 9.0, GLOW_CYAN, 0.2, right)
        s.line(0, low + 2.6, w, low + 2.6, "#04051a", 3.4, 0.35)
        tops = [(lx, top_y(lx)) for lx in xs]
        s.path(_poly(tops + [(w, low), (0, low)]), fill=s.linear(0, y0 - 2, 0, low, [(0, CRYSTAL_HI), (0.3, "#ece9ff"), (0.7, "#c9c2f6"),
                                                                                       (1, "#a59ce8")]))
        # cut facets: a row of crystal prisms of varying width, lit on the left
        cell = 11.0
        for n in range(math.floor(x0 / cell) - 1, math.floor((x0 + w) / cell) + 1):
            a = n * cell + 3.0 * (_hash(n, 81) - 0.5) - x0
            b = (n + 1) * cell + 3.0 * (_hash(n + 1, 81) - 0.5) - x0
            if b < -1 or a > w + 1:
                continue
            m = a + (b - a) * (0.35 + 0.3 * _hash(n, 82))
            s.polygon([(m, y0 + 0.4), (b, y0 + 0.4), (b, low), (m + (b - m) * 0.4, low)], fill="#6f66c8", opacity=0.22 + 0.12 * _hash(n, 83))
            s.polygon([(a, low), (m + (b - m) * 0.4, low), (m, y0 + 0.4)], fill="#ffffff", opacity=0.35)
            s.line(b, y0 + 0.6, b, low - 0.4, "#7f78d4", 0.7, 0.75)
        s.line(0, low - 0.3, w, low - 0.3, GOLD, 1.3)
        s.line(0, low + 0.8, w, low + 0.8, CRYSTAL_LINE, 1.0)
        if left:
            s.path(f"M0.4 {top_y(0):.2f} L0.4 {low + 1:.2f}", stroke=CRYSTAL_LINE, width=1.2)
        if right:
            s.path(f"M{w - 0.4:.2f} {top_y(w):.2f} L{w - 0.4:.2f} {low + 1:.2f}", stroke=CRYSTAL_LINE, width=1.2)
        s.path(_line(tops), stroke=GLOW_CYAN, width=2.4, opacity=0.4)
        s.path(_line([(x, y + 0.5) for x, y in tops]), stroke="#ffffff", width=1.3)
        # crystal points hanging from the trim, in little clusters
        slot = 26.0
        for n in range(math.floor(x0 / slot), math.floor((x0 + w) / slot) + 1):
            if _hash(n, 71) < 0.4 or not hang:
                continue
            cx = n * slot + slot * (0.25 + 0.5 * _hash(n, 72)) - x0
            for j in range(1 + int(_hash(n, 73) * 2.6)):
                px = cx + (j - 0.5) * 4.6 * (1 if _hash(n, 74 + j) > 0.5 else -1)
                wd = 3.0 + 1.6 * _hash(n, 76 + j)
                if not 2 + wd < px < w - 2 - wd:
                    continue
                _crystal(s, px, low, 180 + (_hash(n, 78 + j) - 0.5) * 30, 5 + 8 * _hash(n, 80 + j) * (1.0 if j == 0 else 0.7), wd,
                         "#f6f4ff", "#8a80dc", CRYSTAL_LINE, 0.55)
        # glints on the rim
        g = 13.0
        for n in range(math.floor(x0 / g), math.floor((x0 + w) / g) + 1):
            if _hash(n, 91) < 0.78:
                continue
            lx = n * g + g * _hash(n, 92) - x0
            if 3 < lx < w - 3:
                _sparkle(s, lx, y0 + 1.6, 1.8 + 1.4 * _hash(n, 93), 0.9)

    def _mirror_cap(self, s: Svg, w: float, y0: float, left: bool, right: bool, x0: float) -> None:
        """Polished mirror-crystal floor (slippery): a thick glossy slab set in
        gold, reflecting the stars; streaks and the specular rim say 'slides'."""
        low = y0 + 12.0
        top = y0 - 1.4
        il = 4.5 if left else 0.0
        ir = 4.5 if right else 0.0
        self._halo_band(s, w, y0, 10.0, "#bfe8ff", 0.28, right)
        s.line(0, low + 2.2, w, low + 2.2, "#04051a", 4.0, 0.3)
        s.rect(il, top, w - il - ir, low - top, fill=s.linear(0, top, 0, low, [(0, MIRROR_HI), (0.1, MIRROR_TOP), (0.45, MIRROR), (1, MIRROR_DEEP)]))
        # the reflected night sky and its stars
        s.rect(il, y0 + 4.5, w - il - ir, 6.5, fill=s.linear(0, y0 + 4.5, 0, y0 + 11, [(0, "#1c1a5a", 0.12), (1, "#1c1a5a", 0.4)]))
        c = 8.0
        for n in range(math.floor(x0 / c), math.floor((x0 + w) / c) + 1):
            v = _hash(n, 101)
            lx = n * c + c * _hash(n, 102) - x0
            if v < 0.55 or not il + 1 < lx < w - ir - 1:
                continue
            ly = y0 + 5.5 + 4.5 * _hash(n, 103)
            if v > 0.93:
                _sparkle(s, lx, ly, 1.5, 0.85)
            else:
                s.circle(lx, ly, 0.35 + 0.35 * _hash(n, 104), fill="#ffffff", opacity=0.75)
        # specular streaks (world-aligned, slanted like the frozen floors)
        streak = 44.0
        for m in range(math.floor(x0 / streak) - 1, math.floor((x0 + w) / streak) + 1):
            if _hash(m, 111) < 0.3:
                continue
            gx = m * streak + 30 * _hash(m, 112) - x0
            wide = 3 + 6 * _hash(m, 113)
            if gx - 8 < il + 1 or gx + wide + 1 > w - ir:
                continue
            s.polygon([(gx, top + 1.6), (gx + wide, top + 1.6), (gx + wide - 7, low - 1.6), (gx - 7, low - 1.6)], fill="#ffffff", opacity=0.42)
            if _hash(m, 114) > 0.45 and gx + wide + 5 < w - ir:
                s.polygon([(gx + wide + 2.5, top + 1.6), (gx + wide + 4, top + 1.6), (gx + wide - 3, low - 1.6), (gx + wide - 4.5, low - 1.6)],
                          fill="#ffffff", opacity=0.3)
        s.line(il, low - 1.4, w - ir, low - 1.4, "#d6e0ff", 1.0, 0.7)
        s.line(il, low, w - ir, low, MIRROR_LINE, 1.2)
        s.line(il, top + 0.2, w - ir, top + 0.2, GLOW_CYAN, 2.6, 0.55)
        s.line(il, top + 1.1, w - ir, top + 1.1, "#ffffff", 1.5)
        # gold bezels hold the slab at its exposed ends
        for ex, exposed in ((0.0, left), (w - 5.0, right)):
            if exposed:
                s.path(rounded_rect_path(ex, top - 0.8, 5.0, low - top + 1.6, 1.6),
                       fill=s.linear(ex, 0, ex + 5, 0, [(0, GOLD_LIGHT), (0.5, GOLD), (1, GOLD_DARK)]), stroke=GOLD_DEEP, width=0.8)
                s.circle(ex + 2.5, y0 + 5, 1.0, fill=GOLD_HI)

    # ------------------------------------------------------------------ star-temple masonry (fortress levels)
    def _fortress(self, w: float, h: float, seed: int, left: bool, right: bool, top: bool, x0: float, surface: str) -> Svg:
        """Star-temple masonry with gold trim: running-bond courses of
        star-stone (rosettes, crystal bricks and small constellations inlaid),
        a gilded coping and gilded exposed edges; keyed on the world x."""
        hr = self.terrain_headroom
        s = Svg(w, h + hr)
        y0, bottom = hr, h + hr
        ice = surface == "ice"
        coping = 10.0
        s.rect(-1, y0, w + 2, h, fill=s.linear(0, y0, 0, bottom, [(0, "#0e1136"), (1, "#070820")]))
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
        s.rect(-1, y0 + 30, w + 2, max(0.0, h - 30), fill=s.linear(0, y0 + 30, 0, min(bottom, y0 + 200), [(0, "#05061a", 0), (1, "#05061a", 0.55)]))
        if not top:  # a plain course where the coping would be
            s.rect(-1, y0, w + 2, coping - 1.2, fill=s.linear(0, y0, 0, y0 + coping, [(0, "#2c3478"), (1, "#20275e")]))
        for exposed, ex, inner in ((left, 0.0, 6.0), (right, w, w - 6.0)):
            if exposed:
                s.rect(min(ex, inner), y0, 6, h, fill=s.linear(ex, 0, inner, 0, [(0, "#8a96ea" if ex == 0 else "#04051a", 0.4),
                                                                                    (1, "#8a96ea" if ex == 0 else "#04051a", 0)]))
                gx = 0.0 if ex == 0 else w - 3.0
                s.rect(gx, y0, 3.0, h, fill=s.linear(gx, 0, gx + 3, 0, [(0, GOLD_LIGHT), (1, GOLD_DARK)]))
                s.line(ex + (0.4 if ex == 0 else -0.4), y0, ex + (0.4 if ex == 0 else -0.4), bottom, GOLD_DEEP, 0.9)
        if top and ice:
            self._mirror_cap(s, w, y0, left, right, x0)
        elif top:
            self._halo_band(s, w, y0, 10.0, GOLD_LIGHT, 0.14, right)
            s.rect(-1, y0 - 1.3, w + 2, 3.0, fill=s.linear(0, y0 - 1.3, 0, y0 + 1.7, [(0, GOLD_HI), (0.5, GOLD), (1, GOLD_DARK)]))
            s.rect(-1, y0 + 1.7, w + 2, 6.6, fill=s.linear(0, y0 + 1.7, 0, y0 + 8.3, [(0, "#8e9ae6"), (0.45, "#5c68bc"), (1, "#39438e")]))
            s.line(-1, y0 + 2.2, w + 1, y0 + 2.2, "#c9d2ff", 0.8, 0.8)
            for n in range(math.floor(x0 / 64), math.floor((x0 + w) / 64) + 1):
                lx = n * 64 + 9 - x0
                if -1 < lx < w + 1:
                    s.line(lx, y0 + 2.4, lx, y0 + 8.0, "#232a68", 0.9, 0.9)
            for n in range(math.floor(x0 / 16), math.floor((x0 + w) / 16) + 1):
                lx = n * 16 + 8 - x0
                if 1.5 < lx < w - 1.5 and n % 4 != 0:
                    s.circle(lx, y0 + 5.1, 0.9, fill=GOLD_LIGHT, opacity=0.9)
                elif 3 < lx < w - 3:
                    _sparkle(s, lx, y0 + 5.1, 2.2, 0.95, GOLD_HI)
            s.rect(-1, y0 + 8.3, w + 2, 1.7, fill=s.linear(0, y0 + 8.3, 0, y0 + 10, [(0, GOLD), (1, GOLD_DEEP)]))
            s.line(-1, y0 + 11, w + 1, y0 + 11, "#04051a", 2.0, 0.45)
            s.line(-1, y0 - 1.0, w + 1, y0 - 1.0, "#ffffff", 0.9, 0.9)
            if left:
                s.line(0.5, y0 - 1.3, 0.5, y0 + 10, GOLD_DEEP, 1.2)
            if right:
                s.line(w - 0.5, y0 - 1.3, w - 0.5, y0 + 10, GOLD_DEEP, 1.2)
        if h <= 100:
            # a thin slab is a hanging edge: gold trim with little finials
            s.rect(-1, bottom - 3.2, w + 2, 3.2, fill=s.linear(0, bottom - 3.2, 0, bottom, [(0, GOLD), (1, GOLD_DARK)]))
            for n in range(math.floor(x0 / 24), math.floor((x0 + w) / 24) + 1):
                lx = n * 24 + 12 - x0
                if 4 < lx < w - 4:
                    s.path(f"M{lx - 2.4:.2f} {bottom - 0.5:.2f} Q{lx:.2f} {bottom + 1:.2f} {lx + 2.4:.2f} {bottom - 0.5:.2f} L{lx:.2f} {bottom + 0.0:.2f} Z",
                           fill=GOLD_DARK)
        return s

    def _ashlar(self, s: Svg, k: int, row: int, gx0: float, y: float, bw: float, rh: float, w: float) -> None:
        """One block of a course; ``k``/``row`` give it a world-stable identity."""
        bx0, bx1 = max(-1.0, gx0 + 1.0), min(w + 1.0, gx0 + bw - 1.0)
        y1 = y + rh - 1.1
        if bx1 <= bx0 or y1 <= y + 2:
            return
        ident = k * 7 + row * 131
        v = _hash(ident, 5)
        if v < 0.045 and rh > 14:  # glowing crystal brick
            s.rect(bx0, y + 1.0, bx1 - bx0, y1 - y - 1.0, fill=s.linear(0, y, 0, y1, [(0, "#f4f6ff"), (0.4, "#b8c2f6"), (1, "#6a72d6")]))
            for fx, fw, op in ((gx0 + 7, 5.0, 0.5), (gx0 + 15, 2.2, 0.35), (gx0 + bw * 0.6, 3.0, 0.3)):
                s.polygon([(fx, y + 2.2), (fx + fw, y + 2.2), (fx + fw - 5, y1 - 1.5), (fx - 5, y1 - 1.5)], fill="#ffffff", opacity=op)
            s.line(bx0, y + 1.6, bx1, y + 1.6, "#ffffff", 1.0, 0.9)
            s.line(bx0, y1 - 0.5, bx1, y1 - 0.5, CRYSTAL_LINE, 1.0, 0.8)
            cx = gx0 + bw * 0.32
            if -2 < cx < w + 2:
                _sparkle(s, cx, y + rh * 0.42, 2.2, 0.95)
            return
        tone = mix("#1e2462", "#3a4698", 0.25 + 0.5 * _hash(ident, 6))
        s.rect(bx0, y + 1.0, bx1 - bx0, y1 - y - 1.0, fill=s.linear(0, y, 0, y1, [(0, shade(tone, 0.16)), (0.25, tone), (1, shade(tone, -0.22))]))
        s.line(bx0 + 0.5, y + 1.7, bx1 - 0.5, y + 1.7, "#9aa6f0", 0.9, 0.5)
        s.line(bx0, y1 - 0.4, bx1, y1 - 0.4, "#0a0b26", 1.0, 0.55)
        if -1 < gx0 + 1.6 < w + 1:
            s.line(gx0 + 1.7, y + 2.2, gx0 + 1.7, y1 - 1.0, "#aab4f6", 0.8, 0.4)
        if -1 < gx0 + bw - 1.7 < w + 1:
            s.line(gx0 + bw - 1.7, y + 2.2, gx0 + bw - 1.7, y1 - 1.0, "#0a0b26", 0.9, 0.45)
        for j in range(4):
            px = gx0 + 4 + (bw - 8) * _hash(ident, 20 + j)
            if -1 < px < w + 1:
                py = y + 3.5 + (rh - 7) * _hash(ident, 30 + j)
                s.circle(px, py, 0.45 + 0.4 * _hash(ident, 40 + j), fill=GOLD_LIGHT if j % 2 else "#e6ecff", opacity=0.7)
        cx, cy = gx0 + bw / 2, y + rh / 2
        if v < 0.095 and rh > 14 and -8 < cx < w + 8:  # gold star rosette
            _glow(s, cx, cy, 9, GOLD_LIGHT, 0.35)
            s.circle(cx, cy, 6.2, stroke=GOLD, width=1.3)
            s.polygon(star_points(cx, cy, 5.2, 2.0, 8), fill=s.linear(cx - 5, cy - 5, cx + 5, cy + 5, [(0, GOLD_HI), (0.5, GOLD_LIGHT), (1, GOLD_DARK)]),
                      stroke=GOLD_DEEP, width=0.5)
        elif v < 0.15 and rh > 14 and -20 < cx < w + 20:  # a small constellation
            pts = [(gx0 + 8 + (bw - 16) * t, y + 5 + (rh - 10) * _hash(ident, 50 + i)) for i, t in enumerate((0.0, 0.4, 0.75, 1.0))]
            _inlay(s, pts, [(0, 1), (1, 2), (2, 3)], 0.7, 0.3, groove=False)

    # ------------------------------------------------------------------ asteroid rock (cave rooms)
    def _cave(self, w: float, h: float, seed: int, left: bool, right: bool, top: bool, x0: float) -> Svg:
        """Hollow-asteroid rock: grey-violet stone with craters, geodes and
        glowing crystal veins; the walkable rim on top is always drawn (cave
        floors are often 'covered' by the room walls standing on them)."""
        r = Rand(seed)
        hr = self.terrain_headroom
        s = Svg(w, h + hr)
        y0, bottom = hr, h + hr
        s.rect(0, y0, w, h, fill=s.linear(0, y0, 0, y0 + min(h, 230), [(0, "#565074"), (0.18, "#3a3554"), (0.6, "#24203a"), (1, "#14121f")]))
        xs = _samples(w, 4.0)
        for k in range(3):  # layered rock (world-aligned)
            def yy(lx: float, k: int = k) -> float:
                gx = x0 + lx
                return y0 + 18 + k * 21 + 3.5 * _wobble(gx * 0.7, k * 1.9)
            if y0 + 18 + k * 21 > bottom - 6:
                break
            s.path(_line([(lx, yy(lx)) for lx in xs]), stroke="#8a84b0", width=1.6, opacity=0.22 - k * 0.05)
            s.path(_line([(lx, yy(lx) + 2.2) for lx in xs]), stroke="#0c0a16", width=1.2, opacity=0.35 - k * 0.07)
        # craters (per chunk, kept inside)
        for _ in range(max(1, int(w * min(h, 150) / 5200))):
            cr = r.uniform(4, 10)
            if w < cr * 3 + 8 or h < cr * 2.5 + 16:
                continue
            cx, cy = r.uniform(cr + 4, w - cr - 4), r.uniform(y0 + cr + 12, min(bottom - cr - 4, y0 + 150))
            s.ellipse(cx, cy, cr * 1.25, cr * 0.8, fill="#1c1a2c", opacity=0.75)
            s.path(f"M{cx - cr * 1.1:.2f} {cy + cr * 0.15:.2f} A{cr * 1.25:.2f} {cr * 0.8:.2f} 0 0 0 {cx + cr * 1.15:.2f} {cy + cr * 0.1:.2f}",
                   stroke="#8a84ac", width=1.2, opacity=0.55)
            s.path(f"M{cx - cr * 1.2:.2f} {cy - cr * 0.1:.2f} A{cr * 1.3:.2f} {cr * 0.85:.2f} 0 0 1 {cx + cr * 0.6:.2f} {cy - cr * 0.72:.2f}",
                   stroke="#0e0c18", width=1.0, opacity=0.6)
        # geodes: a dark hollow lined with glowing crystal points
        if h > 50:
            for _ in range(max(0, int(w / 260) + (1 if r.next() < 0.5 else 0))):
                gr = r.uniform(7, 12)
                if w < gr * 3 + 10:
                    break
                gx, gy = r.uniform(gr * 1.5 + 4, w - gr * 1.5 - 4), r.uniform(y0 + gr + 14, min(bottom - gr - 6, y0 + 110))
                color = r.choice([GLOW_TEAL, GLOW_VIOLET, "#ff9ae6"])
                _glow(s, gx, gy, gr * 2.4, color, 0.3)
                s.ellipse(gx, gy, gr * 1.42, gr * 1.1, fill="#9a94c4", stroke="#1a1630", width=1.0)
                s.ellipse(gx, gy, gr * 1.22, gr * 0.92, fill=s.radial(gx, gy, gr * 1.3, [(0, shade(color, 0.45)), (0.45, color),
                                                                                       (1, shade(color, -0.55))]))
                for k in range(10):
                    a = k * 2 * math.pi / 10 + r.uniform(-0.15, 0.15)
                    bx, by = gx + math.cos(a) * gr * 1.15, gy + math.sin(a) * gr * 0.86
                    _crystal(s, bx, by, math.degrees(math.atan2(gx - bx, -(gy - by))), gr * r.uniform(0.35, 0.55), gr * 0.3, "#ffffff",
                             shade(color, -0.15), shade(color, -0.6), 0.4)
                _sparkle(s, gx - gr * 0.2, gy - gr * 0.15, gr * 0.35, 0.95)
        # glowing crystal veins (continuous across chunks)
        for k, (base, amp, freq) in enumerate(((0.42, 9, 0.019), (0.75, 6, 0.031))):
            yb = y0 + min(h - 8, max(16, h * base))
            if h <= 34:
                break
            pts = [(lx, yb + amp * math.sin((x0 + lx) * freq + k * 2.1) + 3.5 * math.sin((x0 + lx) * 0.067 + k)) for lx in _samples(w, 12.0)]
            s.path(smooth_open(pts), stroke=GLOW_TEAL, width=4.5, opacity=0.14)
            s.path(smooth_open(pts), stroke="#c8fff6", width=1.1, opacity=0.6)
        s.rect(0, y0 + 26, w, max(0.0, h - 26), fill=s.linear(0, y0 + 26, 0, y0 + 220, [(0, "#05040c", 0), (1, "#05040c", 0.5)]))
        if left:
            s.rect(0, y0, 5, h, fill=s.linear(0, 0, 5, 0, [(0, "#b4acd8", 0.35), (1, "#b4acd8", 0)]))
            s.line(0.7, y0, 0.7, bottom, "#0c0a16", 1.4)
        if right:
            s.rect(w - 6, y0, 6, h, fill="#05040c", opacity=0.45)
            s.line(w - 0.7, y0, w - 0.7, bottom, "#0c0a16", 1.4)
        # walkable rim
        tops = [(lx, y0 - 0.8 + 0.7 * _wobble(x0 + lx, 0.9)) for lx in _samples(w, 3.0)]
        lows = [(lx, y0 + 5.0 + 1.4 * _wobble(x0 + lx, 2.2) + 1.2 * abs(math.sin((x0 + lx) * 0.17))) for lx in _samples(w, 3.0)]
        s.path(_line([(x, y + 2) for x, y in lows]), stroke="#05040c", width=3.0, opacity=0.4)
        s.path(_poly(tops + list(reversed(lows))), fill=s.linear(0, y0 - 2, 0, y0 + 7, [(0, "#c9c2e8"), (0.4, "#8e87b4"), (1, "#5a547e")]))
        s.path(_line(lows), stroke="#1a1628", width=1.0)
        s.path(_line([(x, y + 0.7) for x, y in tops]), stroke="#efeaff", width=1.1, opacity=0.85)
        g = 15.0
        for n in range(math.floor(x0 / g), math.floor((x0 + w) / g) + 1):
            lx = n * g + g * _hash(n, 121) - x0
            if _hash(n, 122) > 0.72 and 3 < lx < w - 3:
                _sparkle(s, lx, y0 + 1.6, 1.6, 0.85, "#d8fff8")
        if h <= 100:
            # ceilings and thin slabs: glowing crystal stalactites along the underside
            # (drawn inside the slab's last units, like icicles under a ledge)
            s.line(-1, bottom - 1.2, w + 1, bottom - 1.2, "#8a84b0", 1.4, 0.5)
            slot = 15.0
            for n in range(math.floor(x0 / slot), math.floor((x0 + w) / slot) + 1):
                lx = (n + 0.5) * slot - x0
                if _hash(n, 131) < 0.4 or not 5 < lx < w - 5:
                    continue
                ln = 6 + 9 * _hash(n, 132)
                color = GLOW_TEAL if _hash(n, 133) > 0.4 else GLOW_VIOLET
                _glow(s, lx, bottom - ln * 0.4, ln * 0.9, color, 0.3)
                _crystal(s, lx, bottom - ln - 0.8, 180, ln, 3.4 + 2 * _hash(n, 134), "#f0fffc", shade(color, -0.35), "#1a1630", 0.5)
        return s

    # ------------------------------------------------------------------ blocks
    def block(self, kind: str, w: float, h: float) -> Svg:
        s = Svg(w, h)
        if kind in ("question", "used"):
            self._reliquary(s, w, h, kind == "used")
        elif kind == "brick":
            s.path(rounded_rect_path(0.6, 0.6, w - 1.2, h - 1.2, 3), fill="#0c0e30", stroke=INK, width=1.2)
            rows = 2
            rh = (h - 2) / rows
            for row in range(rows):
                y = 1 + row * rh
                x = -(0.0 if row % 2 == 0 else 10.0)
                i = 0
                while x < w:
                    bx0, bx1 = max(1.4, x + 1.1), min(w - 1.4, x + 20 - 1.1)
                    if bx1 > bx0 + 2:
                        ident = row * 31 + i
                        tone = mix("#3c48a0", "#5260c0", _hash(ident, 3))
                        s.path(rounded_rect_path(bx0, y + 1.0, bx1 - bx0, rh - 2.0, 1.8),
                               fill=s.linear(0, y, 0, y + rh, [(0, shade(tone, 0.12)), (0.35, tone), (1, "#1e2462")]), stroke=STONE_LINE, width=0.7)
                        s.line(bx0 + 1.2, y + 2.1, bx1 - 1.2, y + 2.1, "#aab6ff", 0.9, 0.75)
                        s.line(bx0 + 1.0, y + rh - 1.8, bx1 - 1.0, y + rh - 1.8, "#141a4c", 0.8, 0.6)
                        for j in range(2):
                            fx = bx0 + 2 + (bx1 - bx0 - 4) * _hash(ident, 10 + j)
                            fy = y + 3.4 + (rh - 6.4) * _hash(ident, 20 + j)
                            s.circle(fx, fy, 0.5 + 0.35 * _hash(ident, 30 + j), fill=GOLD_LIGHT if j == 0 else "#e6ecff", opacity=0.85)
                        if _hash(ident, 40) > 0.8 and bx1 - bx0 > 10:
                            _sparkle(s, (bx0 + bx1) / 2, y + rh * 0.5, 1.8, 0.8, GOLD_HI)
                    x += 20
                    i += 1
        return s

    def _reliquary(self, s: Svg, w: float, h: float, used: bool) -> None:
        """Reward block: a gold reliquary framing a crystal pane with a glowing
        eight-point star; once used, the gold tarnishes and the star goes dark."""
        if used:
            frame = [(0, "#b4aac6"), (0.45, "#7a7290"), (1, "#4a445e")]
        else:
            frame = [(0, GOLD_HI), (0.22, GOLD_LIGHT), (0.6, GOLD), (1, GOLD_DARK)]
        s.path(rounded_rect_path(0.6, 0.6, w - 1.2, h - 1.2, 4.2), fill=s.linear(0, 0, 0, h, frame), stroke=INK, width=1.3)
        s.path(rounded_rect_path(1.8, 1.8, w - 3.6, h - 3.6, 3.4), stroke="#ffffff" if not used else "#d8d2e6", width=0.8, opacity=0.55)
        ix, iy = 4.4, 4.2
        pane = rounded_rect_path(ix, iy, w - 2 * ix, h - 2 * iy, 2.6)
        if used:
            s.path(pane, fill=s.linear(ix, iy, w - ix, h - iy, [(0, "#3a3a66"), (1, "#1c1a3a")]), stroke="#2a2440", width=0.9)
        else:
            s.path(pane, fill=s.linear(ix, iy, w - ix, h - iy, [(0, "#6a7af0"), (0.5, "#3a3aa8"), (1, "#20186a")]), stroke=GOLD_DEEP, width=0.9)
        # glass facets
        s.polygon([(ix + 1.5, iy + 0.8), (ix + 6.5, iy + 0.8), (ix + 2.5, h - iy - 0.8), (ix + 0.8, h - iy - 0.8)], fill="#ffffff",
                  opacity=0.22 if not used else 0.08)
        s.polygon([(w - ix - 7, iy + 0.8), (w - ix - 5.2, iy + 0.8), (w - ix - 9, h - iy - 0.8), (w - ix - 10.8, h - iy - 0.8)], fill="#ffffff",
                  opacity=0.15 if not used else 0.05)
        cx, cy = w / 2, h / 2
        rad = min(w - 2 * ix, h - 2 * iy) * 0.46
        if not used:
            _glow(s, cx, cy, rad * 1.7, "#fff0b0", 0.85)
            s.polygon(star_points(cx, cy, rad * 0.78, rad * 0.22, 4, -45), fill=GOLD_LIGHT, opacity=0.9)
            s.polygon(star_points(cx, cy, rad * 1.05, rad * 0.26, 4), fill=s.linear(cx - rad, cy - rad, cx + rad, cy + rad,
                                                                                    [(0, "#ffffff"), (0.45, GOLD_HI), (1, GOLD_LIGHT)]),
                      stroke=GOLD_DARK, width=0.6)
            s.circle(cx, cy, rad * 0.16, fill="#ffffff")
            _sparkle(s, ix + 4.2, iy + 3.2, 2.0, 0.9)
        else:
            s.polygon(star_points(cx, cy, rad * 0.95, rad * 0.26, 4), fill="#2a2846", stroke="#55507a", width=0.8)
            s.polygon(star_points(cx, cy, rad * 0.62, rad * 0.2, 4, -45), fill=None, stroke="#55507a", width=0.6)
        # corner studs and filigree notches on the frame
        stud = "#fff6d8" if not used else "#9a92b0"
        for px, py in ((2.6, 2.6), (w - 2.6, 2.6), (2.6, h - 2.6), (w - 2.6, h - 2.6)):
            s.circle(px, py, 1.15, fill=stud, stroke=GOLD_DEEP if not used else "#3a344c", width=0.4)
        for py in (2.3, h - 2.3):
            s.polygon([(cx - 2.4, py), (cx, py - 1.6), (cx + 2.4, py), (cx, py + 1.6)], fill=stud, stroke=GOLD_DEEP if not used else "#3a344c",
                      width=0.4)

    # ------------------------------------------------------------------ pipes
    def pipe(self, w: float, h: float, warp: bool) -> Svg:
        """Crystal portal tube with brass telescope rings; the warp variant
        holds a swirling star glow and a luminous arrow."""
        s = Svg(w, h)
        body = s.linear(4, 0, w - 4, 0, [(0, "#16134e"), (0.14, "#3e44a8"), (0.28, "#aeb8ff"), (0.4, "#6a74de"), (0.72, "#2a2a80"), (1, "#110f3e")])
        s.path(rounded_rect_path(4, 10, w - 8, h - 10, 2), fill=body, stroke=INK, width=1.3)
        r = Rand(int(w * 7 + h * 3))
        for _ in range(int((w - 12) * (h - 16) / 90)):  # starlight inside the crystal
            px, py = r.uniform(9, w - 9), r.uniform(17, h - 4)
            s.circle(px, py, r.uniform(0.35, 0.8), fill="#ffffff", opacity=r.uniform(0.4, 0.85))
        s.line(w * 0.3, 16, w * 0.3, h - 2, "#ffffff", 1.4, 0.45)
        s.line(w * 0.36, 16, w * 0.36, h - 2, "#ffffff", 0.6, 0.3)
        band = s.linear(4, 0, w - 4, 0, [(0, GOLD_DEEP), (0.25, GOLD), (0.38, GOLD_HI), (0.62, GOLD), (1, GOLD_DARK)])
        if h > 30:
            s.path(rounded_rect_path(3.2, h - 9, w - 6.4, 4.6, 1.5), fill=band, stroke=INK, width=0.9)
        if h > 52:
            s.path(rounded_rect_path(3.2, h * 0.58, w - 6.4, 3.8, 1.4), fill=band, stroke=INK, width=0.8)
        # brass collar of the telescope, engraved with a small constellation
        rim = s.linear(0.8, 0, w - 0.8, 0, [(0, GOLD_DEEP), (0.18, GOLD), (0.34, GOLD_HI), (0.58, GOLD_LIGHT), (0.8, GOLD), (1, GOLD_DARK)])
        s.path(rounded_rect_path(0.8, 0.8, w - 1.6, 14, 3.5), fill=rim, stroke=INK, width=1.3)
        s.line(3, 3.2, w - 3, 3.2, GOLD_HI, 1.0, 0.85)
        s.line(3, 11.6, w - 3, 11.6, GOLD_DEEP, 0.9, 0.7)
        pts = [(w * 0.3, 8.4), (w * 0.42, 6.2), (w * 0.56, 8.8), (w * 0.7, 6.6)]
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            s.line(ax, ay, bx, by, GOLD_DEEP, 0.7, 0.8)
        for px, py in pts:
            s.circle(px, py, 0.9, fill=GOLD_DEEP)
        for bx in (5.0, w - 5.0):
            s.circle(bx, 7.6, 1.3, fill=GOLD_HI, stroke=GOLD_DEEP, width=0.5)
        if warp:
            cy = 30 if h > 40 else h * 0.66
            _glow(s, w / 2, cy, 14, "#d8f0ff", 0.85)
            for k in range(2):
                pts = [(w / 2 + math.cos(k * math.pi + i * 0.55) * (1.5 + i * 1.15), cy + math.sin(k * math.pi + i * 0.55) * (1.5 + i * 1.15) * 0.8)
                       for i in range(9)]
                s.path(smooth_open(pts), stroke="#ffffff", width=1.1, opacity=0.8)
            for k in range(5):
                a = k * 1.3 + 0.4
                _sparkle(s, w / 2 + math.cos(a) * 9.5, cy + math.sin(a) * 7, 1.4, 0.9, GOLD_HI if k % 2 else "#ffffff")
            s.polygon([(w / 2 - 4.6, cy - 3.0), (w / 2 + 4.6, cy - 3.0), (w / 2, cy + 3.8)], fill="#ffffff", stroke="#4a5ad8", width=0.7)
        return s

    # ------------------------------------------------------------------ platforms
    def platform(self, kind: str, w: float, h: float, style: str = "") -> Svg:
        if kind == "ledge":
            return self._ledge(w, h, style)
        s = Svg(w, h + 10)
        if kind == "moving":
            self._orbit_disc(s, w, h)
        elif kind == "crumble":
            self._fading_glass(s, w, h)
        elif kind == "semisolid":
            self._light_bridge(s, w, h)
        elif kind == "spring":
            self._tuning_fork(s, w, h)
        else:  # conveyor (and switch fallback): a rotating orrery band
            self._orrery_band(s, w, h)
        return s

    def _orbit_disc(self, s: Svg, w: float, h: float) -> None:
        """Small orbiting stone disc: rune ring on its rim, a levitation crystal
        and two pebbles circling underneath."""
        cx = w / 2
        rx = w / 2 - 1.0
        _glow(s, cx, h + 2, w * 0.28, GLOW_VIOLET, 0.35)
        # levitation crystal and its orbiting pebbles
        _crystal(s, cx, h - 4, 180, 12, 6, "#f4f2ff", "#7a6ae0", INK, 0.7)
        for px, py, pr in ((cx - w * 0.3, h + 3.5, 2.6), (cx + w * 0.34, h + 1.5, 2.0)):
            s.path(blob(px, py, pr * 1.3, pr, 0.15, seed=px), fill=s.linear(0, py - pr, 0, py + pr, [(0, "#7a84d0"), (1, "#262a68")]), stroke=INK, width=0.6)
            s.path(f"M{px - pr * 1.6:.2f} {py + 0.5:.2f} Q{px:.2f} {py + pr * 1.8:.2f} {px + pr * 1.6:.2f} {py + 0.5:.2f}", stroke="#bfc8ff", width=0.5,
                   opacity=0.6)
        side = (f"M1 3.2 L1 {h - 6:.2f} A{rx:.2f} 5.5 0 0 0 {w - 1:.2f} {h - 6:.2f} L{w - 1:.2f} 3.2 Z")
        s.path(side, fill=s.linear(0, 2, 0, h, [(0, "#58649e"), (0.3, "#3a4596"), (1, "#151946")]), stroke=INK, width=1.2)
        # rune band following the curve of the rim
        ya, yb = h * 0.42, h * 0.42 + 4.2
        s.path(f"M1.2 {ya:.2f} A{rx:.2f} 4 0 0 0 {w - 1.2:.2f} {ya:.2f} L{w - 1.2:.2f} {yb:.2f} A{rx:.2f} 4 0 0 1 1.2 {yb:.2f} Z",
               fill=s.linear(0, 0, w, 0, [(0, GOLD_DARK), (0.3, GOLD_LIGHT), (0.55, GOLD), (1, GOLD_DEEP)]), stroke=GOLD_DEEP, width=0.5)
        for k in range(1, 9):
            t = k / 9
            x = 1.2 + (w - 2.4) * t
            dy = 4 * math.sqrt(max(0.0, 1 - ((x - cx) / rx) ** 2))
            yy = (ya + yb) / 2 + dy
            if k % 2:
                s.line(x, yy - 1.2, x, yy + 1.2, "#2a1a08", 0.9)
            else:
                s.circle(x, yy, 0.9, fill="#d8fff8")
                _glow(s, x, yy, 2.6, GLOW_TEAL, 0.5)
        # top face: lighter stone with an inscribed ring and the bright crystal edge
        s.ellipse(cx, 3.2, rx, 2.8, fill=s.linear(0, 0.4, 0, 6, [(0, "#a6b0ee"), (1, "#5c68b8")]), stroke=INK, width=0.9)
        s.ellipse(cx, 3.3, rx * 0.66, 1.6, stroke=GOLD, width=0.6, opacity=0.9)
        s.path(f"M2 3.4 A{rx - 1:.2f} 2.6 0 0 0 {w - 2:.2f} 3.4", stroke="#ffffff", width=1.0, opacity=0.8)
        s.path(f"M3 2.2 A{rx - 2:.2f} 2.0 0 0 1 {w - 3:.2f} 2.2", stroke="#ffffff", width=0.8, opacity=0.5)

    def _fading_glass(self, s: Svg, w: float, h: float) -> None:
        """Crumbling platform: translucent constellation glass, cracked and
        shedding shards (it fades away when stepped on)."""
        r = Rand(int(w * 3 + h))
        _glow(s, w / 2, h / 2, w * 0.5, GLOW_VIOLET, 0.12)
        body = rounded_rect_path(0.6, 0.6, w - 1.2, h - 1.2, 3.2)
        s.path(body, fill=s.linear(0, 0, 0, h, [(0, "#d8dcff", 0.85), (0.35, "#8c92e8", 0.62), (1, "#3c3aa0", 0.5)]))
        s.path(body, fill=s.linear(0, 0, w, 0, [(0, "#ffffff", 0.0), (0.6, "#ffffff", 0.0), (1, "#c8b8ff", 0.25)]))
        pts, edges = _constellation_shape(int(w), 7, 8, w - 8, 6, h - 5)
        _inlay(s, pts, edges, 0.6, 0.3, groove=False)
        for _ in range(3):
            x = r.uniform(10, w - 10)
            crack = [(x, 1.5), (x + r.uniform(-4, 4), h * 0.4), (x + r.uniform(-5, 5), h * 0.72), (x + r.uniform(-3, 3), h - 1.2)]
            s.path(_line(crack), stroke="#2a2a7a", width=1.1, opacity=0.85)
            s.path(_line([(px + 0.8, py) for px, py in crack]), stroke="#ffffff", width=0.6, opacity=0.85)
            bx, by = crack[1]
            s.path(_line([(bx, by), (bx + r.uniform(4, 8), by + r.uniform(-3, 3))]), stroke="#2a2a7a", width=0.8, opacity=0.8)
        s.path(body, stroke=INK, width=1.1, opacity=0.85)
        s.line(3, 1.6, w - 3, 1.6, "#ffffff", 1.3, 0.95)
        for _ in range(5):  # shards drifting off the underside
            fx, fy = r.uniform(6, w - 6), h + r.uniform(1.5, 8)
            sz = r.uniform(1.4, 2.6)
            s.polygon([(fx, fy - sz), (fx + sz * 0.8, fy), (fx, fy + sz * 0.6), (fx - sz * 0.6, fy)], fill="#dcd8ff", stroke="#4a46a8", width=0.4,
                      opacity=r.uniform(0.5, 0.9))

    def _light_bridge(self, s: Svg, w: float, h: float) -> None:
        """Semisolid: a bridge of light joining a row of stars (pass-through from below)."""
        deck = min(h, 7.0)
        n = max(2, int(round((w - 12) / 24)))
        xs = [6 + (w - 12) * i / n for i in range(n + 1)]
        for x in xs:  # light falling from each star
            s.rect(x - 1.2, deck, 2.4, h + 7 - deck, fill=s.linear(0, deck, 0, h + 8, [(0, GOLD_LIGHT, 0.45), (1, GOLD_LIGHT, 0)]))
        s.line(4, deck * 0.5 + 0.5, w - 4, deck * 0.5 + 0.5, GOLD_LIGHT, 9, 0.14)
        s.path(rounded_rect_path(2, 0.8, w - 4, deck - 1.2, (deck - 1.2) / 2), fill=s.linear(0, 0.8, 0, deck, [(0, "#ffffff", 0.95),
                                                                                                                (0.45, "#fff2c4", 0.8),
                                                                                                                (1, GOLD, 0.5)]))
        s.line(4, 1.3, w - 4, 1.3, "#ffffff", 1.2)
        s.line(4, deck - 0.6, w - 4, deck - 0.6, GOLD_DARK, 0.7, 0.6)
        for i, x in enumerate(xs):
            end = i in (0, n)
            _glow(s, x, deck / 2, 7 if end else 5, "#fff0b8", 0.7)
            _sparkle(s, x, deck / 2, 5.2 if end else 3.6, 1.0, "#ffffff")
            s.circle(x, deck / 2, 1.4 if end else 1.0, fill="#ffffff")

    def _tuning_fork(self, s: Svg, w: float, h: float) -> None:
        """Spring: a crystal tuning fork on a brass foot, a crystal pad across
        its prongs and faint resonance rings."""
        cx = w / 2
        for side in (-1, 1):  # resonance rings
            for k in range(2):
                ox = cx + side * (w * 0.36 + k * 3.2)
                s.path(f"M{ox:.2f} {h * 0.22:.2f} Q{ox + side * 2.6:.2f} {h * 0.48:.2f} {ox:.2f} {h * 0.74:.2f}", stroke=GLOW_CYAN, width=0.9,
                       opacity=0.6 - k * 0.25)
        s.path(rounded_rect_path(w * 0.2, h - 3.6, w * 0.6, 3.6, 1.4), fill=s.linear(0, h - 3.6, 0, h, [(0, GOLD_LIGHT), (1, GOLD_DARK)]),
               stroke=INK, width=0.9)
        s.rect(cx - 1.8, h * 0.68, 3.6, h * 0.32 - 3, fill=s.linear(cx - 1.8, 0, cx + 1.8, 0, [(0, GOLD_LIGHT), (1, GOLD_DARK)]), stroke=INK,
               width=0.7)
        px0, px1 = w * 0.29, w * 0.71
        fork = f"M{px0:.2f} 4 L{px0:.2f} {h * 0.5:.2f} Q{px0:.2f} {h * 0.72:.2f} {cx:.2f} {h * 0.72:.2f} Q{px1:.2f} {h * 0.72:.2f} {px1:.2f} {h * 0.5:.2f} L{px1:.2f} 4"
        s.path(fork, stroke=INK, width=5.6)
        s.path(fork, stroke=s.linear(0, 0, w, 0, [(0, "#f4f2ff"), (0.5, "#b6acf2"), (1, "#7a6ad8")]), width=3.8)
        s.path(f"M{px0 - 0.8:.2f} 5 L{px0 - 0.8:.2f} {h * 0.5:.2f}", stroke="#ffffff", width=0.9, opacity=0.8)
        s.path(rounded_rect_path(1.8, 0.4, w - 3.6, 5.2, 2.6), fill=s.linear(0, 0.4, 0, 5.6, [(0, "#ffffff"), (0.5, "#d6d0ff"), (1, "#8a7ee0")]),
               stroke=INK, width=1.0)
        for ex in (1.8, w - 5.0):
            s.path(rounded_rect_path(ex, 0.4, 3.2, 5.2, 1.2), fill=s.linear(ex, 0, ex + 3.2, 0, [(0, GOLD_LIGHT), (1, GOLD_DARK)]))
        _sparkle(s, w * 0.3, 2.6, 2.2, 0.95)

    def _orrery_band(self, s: Svg, w: float, h: float) -> None:
        """Conveyor: a brass orrery band whose little planets roll on a track."""
        s.path(rounded_rect_path(0.6, 0.6, w - 1.2, h - 1.2, h / 2), fill=s.linear(0, 0, 0, h, [(0, GOLD_HI), (0.3, GOLD_LIGHT), (0.7, GOLD),
                                                                                                (1, GOLD_DARK)]), stroke=INK, width=1.2)
        s.path(rounded_rect_path(3.2, 3.6, w - 6.4, h - 7.2, (h - 7.2) / 2), fill=s.linear(0, 3.6, 0, h - 3.6, [(0, "#20206a"), (1, "#0c0a30")]),
               stroke=GOLD_DEEP, width=0.7)
        r = Rand(int(w))
        for _ in range(int(w / 9)):
            s.circle(r.uniform(h * 0.6, w - h * 0.6), r.uniform(5, h - 5), r.uniform(0.3, 0.6), fill="#ffffff", opacity=0.7)
        s.line(h / 2, h / 2, w - h / 2, h / 2, GOLD, 0.7, 0.8)
        colors = (("#fff2c0", GOLD), ("#c8fff6", "#2aa8a0"), ("#ffd6ea", "#c0508a"), ("#e8e2ff", "#7a6ad8"))
        rad = h * 0.2
        k = 0
        x = h * 1.15
        while x < w - h * 1.1:
            hi, lo = colors[k % len(colors)]
            s.circle(x, h / 2, rad, fill=s.radial(x - rad * 0.35, h / 2 - rad * 0.35, rad * 1.3, [(0, "#ffffff"), (0.35, hi), (1, lo)]), stroke=INK,
                     width=0.5)
            if k % 3 == 1:
                s.ellipse(x, h / 2, rad * 1.7, rad * 0.45, stroke="#ffe8b0", width=0.6, opacity=0.85)
            x += h * 1.15
            k += 1
        for hx in (h / 2, w - h / 2):  # orrery hubs
            s.circle(hx, h / 2, h * 0.36, fill=s.radial(hx - 1, h / 2 - 1, h * 0.4, [(0, GOLD_HI), (0.6, GOLD), (1, GOLD_DARK)]), stroke=INK, width=0.8)
            for j in range(6):
                a = j * math.pi / 3
                s.line(hx + math.cos(a) * h * 0.12, h / 2 + math.sin(a) * h * 0.12, hx + math.cos(a) * h * 0.3, h / 2 + math.sin(a) * h * 0.3,
                       GOLD_DEEP, 0.8)
            _glow(s, hx, h / 2, h * 0.22, "#fff6d0", 0.8)
        s.line(h / 2, 1.6, w - h / 2, 1.6, "#ffffff", 1.0, 0.8)
        for tx in range(int(h), int(w - h), 8):
            s.line(tx, 0.8, tx, 2.8, GOLD_DEEP, 0.6, 0.7)

    # ------------------------------------------------------------------ ledges
    def _ledge(self, w: float, h: float, style: str) -> Svg:
        """Ledges: star-stone slabs; "floating" = a small floating crystal;
        "fortress" = temple masonry; "ice" = a mirror-crystal slab."""
        hr = self.terrain_headroom
        seed = int(w * 7 + h)
        if "fortress" in style:
            return self._fortress(w, h, seed, True, True, True, 0.0, "ice" if "ice" in style else "normal")
        if style == "floating":
            return self._floating_crystal(w, h)
        under = 14.0
        s = Svg(w, h + hr + under)
        ice = "ice" in style
        self._starstone(s, w, h, hr, True, True, 0.0, True, ice, under)
        if ice:
            self._mirror_cap(s, w, hr, True, True, 0.0)
        else:
            self._crystal_cap(s, w, hr, True, True, 0.0)
        return s

    def _floating_crystal(self, w: float, h: float) -> Svg:
        """A small floating crystal: a flat polished top over a faceted lavender
        mass ending in crystal points, lit from inside."""
        hr = self.terrain_headroom
        under = 20.0
        s = Svg(w, h + hr + under)
        y0 = hr
        n = max(3, int(w / 34))
        tips = []
        for i in range(n):
            t = (i + 0.5) / n
            depth = h + under * (0.35 + 0.6 * math.sin(math.pi * t)) * (0.75 + 0.25 * _hash(i, 3))
            tips.append((w * t + (_hash(i, 4) - 0.5) * w / n * 0.3, y0 + depth))
        valleys = [(w * i / n, y0 + h * 0.55 + 3 * _hash(i, 5)) for i in range(1, n)]
        bottom: list[Pt] = []
        for i in range(n):
            bottom.append(tips[i])
            if i < n - 1:
                bottom.append(valleys[i])
        outline = [(1.0, y0 + 2.0)] + [(2.5, y0 + h * 0.45)] + bottom + [(w - 2.5, y0 + h * 0.45), (w - 1.0, y0 + 2.0)]
        _glow(s, w / 2, y0 + h + under * 0.5, w * 0.36, GLOW_VIOLET, 0.3)
        s.path(_poly(outline), fill=s.linear(0, y0, 0, y0 + h + under, [(0, "#e8e4ff"), (0.3, "#a69cf0"), (0.7, "#6a58c8"), (1, "#3a2c8a")]))
        # facets toward each point: lit left face, shaded right face
        for i, (tx, ty) in enumerate(tips):
            la = valleys[i - 1][0] if i > 0 else 2.5
            rb = valleys[i][0] if i < n - 1 else w - 2.5
            s.polygon([(tx, ty), ((la + tx) / 2, y0 + 3), (tx, y0 + 3)], fill="#ffffff", opacity=0.22)
            s.polygon([(tx, ty), (tx, y0 + 3), ((rb + tx) / 2, y0 + 3), (rb, y0 + h * 0.5)], fill="#2a1e70", opacity=0.28)
            s.line(tx, ty - 1.5, tx, y0 + 4, "#ffffff", 0.7, 0.5)
        _glow(s, w / 2, y0 + h * 0.6, min(w * 0.3, h * 1.2), "#c8f6ff", 0.45)
        s.path(_line(outline[1:-1]), stroke=INK, width=1.2)
        for k in range(3):
            a = k * 2.1 + 0.6
            _sparkle(s, w / 2 + math.cos(a) * w * 0.32, y0 + h * 0.75 + math.sin(a) * under * 0.4, 1.8, 0.8)
        self._crystal_cap(s, w, y0, True, True, 0.0, hang=False)
        return s

    # ------------------------------------------------------------------ props
    def _crystal_cluster(self, seed: int) -> Svg:
        """Cluster of chunky crystal prisms growing from a star-stone rock."""
        r = Rand(seed)
        s = Svg(64, 62)
        teal = seed % 2 == 1
        light, dark, glow = ("#e8fffb", "#3a9aa8", GLOW_TEAL) if teal else ("#f2f0ff", "#6a5ad0", GLOW_VIOLET)
        _glow(s, 32, 40, 30, glow, 0.35)
        shards = [(-26, 24, 9), (-4, 40, 12), (18, 30, 10), (34, 18, 7), (-44, 15, 6)]
        for ang, ln, wd in sorted(shards[: 3 + seed % 3], key=lambda c: -c[1]):
            a = ang + r.uniform(-5, 5)
            _crystal(s, 32 + math.sin(math.radians(a)) * 3, 54, a, ln, wd, light, dark, INK, 1.0)
        s.path(blob(32, 56, 24, 6.5, 0.15, seed=seed, squash_top=1.2), fill=s.linear(0, 49, 0, 62, [(0, "#5a66c2"), (0.5, "#2e3680"), (1, "#151946")]),
               stroke=INK, width=1.0)
        for k in range(3):
            s.circle(20 + k * 11 + r.uniform(-2, 2), 56.5 + r.uniform(-1, 1), 0.8, fill=GOLD_LIGHT)
        _sparkle(s, 26, 20, 3.2)
        _sparkle(s, 40, 32, 2.2)
        return s

    def _star_lantern(self) -> Svg:
        """Lamp post crowned by a star-shaped crystal lantern in a gold cradle."""
        s = Svg(40, 106)
        cx = 20.0
        _glow(s, cx, 20, 21, "#fff0b8", 0.6)
        s.path(rounded_rect_path(cx - 9, 98, 18, 8, 2), fill=s.linear(0, 98, 0, 106, [(0, "#5a66c2"), (1, "#1a1e52")]), stroke=INK, width=1.0)
        s.rect(cx - 6.5, 95, 13, 3.4, fill=s.linear(0, 95, 0, 98.4, [(0, GOLD_LIGHT), (1, GOLD_DARK)]), stroke=INK, width=0.7)
        s.path(rounded_rect_path(cx - 2.6, 36, 5.2, 60, 1.6), fill=s.linear(cx - 2.6, 0, cx + 2.6, 0, [(0, "#6a76d0"), (0.4, "#3a4496"), (1, "#151946")]),
               stroke=INK, width=1.0)
        for y in (48.0, 70.0):
            s.rect(cx - 3.6, y, 7.2, 2.6, fill=s.linear(0, y, 0, y + 2.6, [(0, GOLD_HI), (1, GOLD_DARK)]), stroke=INK, width=0.6, rx=1)
        # gold cradle with curled arms
        s.path(f"M{cx - 9:.1f} 30 Q{cx - 9:.1f} 37 {cx:.1f} 37 Q{cx + 9:.1f} 37 {cx + 9:.1f} 30", stroke=INK, width=3.0)
        s.path(f"M{cx - 9:.1f} 30 Q{cx - 9:.1f} 37 {cx:.1f} 37 Q{cx + 9:.1f} 37 {cx + 9:.1f} 30", stroke=GOLD, width=1.7)
        for side in (-1, 1):
            s.circle(cx + side * 9, 29.5, 1.4, fill=GOLD_LIGHT, stroke=INK, width=0.5)
        # the star lantern
        s.polygon(star_points(cx, 20, 11.5, 4.6, 4), fill=s.radial(cx, 20, 11.5, [(0, "#ffffff"), (0.35, "#fff2c4"), (1, GOLD)]), stroke=GOLD_DEEP,
                  width=0.9)
        s.polygon(star_points(cx, 20, 6.5, 2.6, 4, -45), fill="#ffffff", opacity=0.75)
        s.circle(cx, 20, 2.0, fill="#ffffff")
        s.line(cx, 31.5, cx, 37, GOLD_DARK, 1.0)
        return s

    def _orrery(self) -> Svg:
        """Small brass orrery on a star-stone pedestal: a glowing sun, two tilted
        orbits with planets and a meridian ring."""
        s = Svg(68, 76)
        cx, cy = 34.0, 28.0
        s.path(rounded_rect_path(22, 66, 24, 10, 2), fill=s.linear(0, 66, 0, 76, [(0, "#5a66c2"), (1, "#1a1e52")]), stroke=INK, width=1.0)
        s.path(f"M27 66 L29 50 L39 50 L41 66 Z", fill=s.linear(27, 0, 41, 0, [(0, "#6a76d0"), (0.4, "#3a4496"), (1, "#151946")]), stroke=INK, width=1.0)
        s.rect(26, 47, 16, 3.6, fill=s.linear(0, 47, 0, 50.6, [(0, GOLD_HI), (1, GOLD_DARK)]), stroke=INK, width=0.7, rx=1)
        s.line(cx, 47, cx, cy + 6, GOLD_DARK, 2.2)
        # orbits: back halves first, then the sun, then the front halves and planets
        orbits = ((26.0, 7.0, -12.0, "#ffd6ea", "#c0508a", 0.3), (17.0, 5.2, 18.0, "#c8fff6", "#2aa8a0", 2.4))
        for rx, ry, tilt, *_ in orbits:
            with s.group(transform=f"rotate({tilt:.1f} {cx:.1f} {cy:.1f})"):
                s.path(f"M{cx - rx:.1f} {cy:.1f} A{rx:.1f} {ry:.1f} 0 0 1 {cx + rx:.1f} {cy:.1f}", stroke=GOLD_DARK, width=1.4)
        s.circle(cx, cy, 14, stroke=GOLD_DARK, width=1.2, opacity=0.8)  # meridian ring
        _glow(s, cx, cy, 13, "#fff0b0", 0.8)
        s.circle(cx, cy, 5.6, fill=s.radial(cx - 1.6, cy - 1.6, 6.5, [(0, "#ffffff"), (0.4, GOLD_HI), (1, GOLD)]), stroke=GOLD_DEEP, width=0.8)
        for rx, ry, tilt, hi, lo, a in orbits:
            with s.group(transform=f"rotate({tilt:.1f} {cx:.1f} {cy:.1f})"):
                s.path(f"M{cx + rx:.1f} {cy:.1f} A{rx:.1f} {ry:.1f} 0 0 1 {cx - rx:.1f} {cy:.1f}", stroke=GOLD, width=1.4)
                px, py = cx + math.cos(a) * rx, cy + math.sin(a) * ry
                s.circle(px, py, 3.1, fill=s.radial(px - 1, py - 1, 3.6, [(0, "#ffffff"), (0.35, hi), (1, lo)]), stroke=INK, width=0.6)
        s.path(f"M{cx - 14:.1f} {cy:.1f} A14 14 0 0 1 {cx + 2:.1f} {cy - 13.9:.1f}", stroke=GOLD_LIGHT, width=1.0)
        return s

    def _broken_column(self, seed: int) -> Svg:
        """Fluted star-stone column with gold inlay rings, snapped off; a chunk
        of its drum lies at the foot."""
        r = Rand(seed)
        s = Svg(56, 100)
        short = seed % 2 == 0
        cx, cw = 24.0, 18.0
        top = 40.0 if short else 14.0
        shaft = s.linear(cx - cw / 2, 0, cx + cw / 2, 0, [(0, "#9aa6ec"), (0.35, "#6a76cc"), (1, "#262c6e")])
        broken = [(cx - cw / 2, top + 6), (cx - cw * 0.2, top - 2), (cx + cw * 0.05, top + 4), (cx + cw * 0.3, top - 4), (cx + cw / 2, top + 3)]
        s.path(_poly([(cx - cw / 2, 92)] + broken + [(cx + cw / 2, 92)]), fill=shaft, stroke=INK, width=1.1)
        for fx in (-0.25, 0.0, 0.25):
            s.line(cx + fx * cw, top + 6, cx + fx * cw, 90, "#2a3070", 1.0, 0.5)
        for y in (top + 14, 74.0):
            s.rect(cx - cw / 2 - 0.5, y, cw + 1, 3.0, fill=s.linear(0, y, 0, y + 3, [(0, GOLD_HI), (1, GOLD_DARK)]), stroke=INK, width=0.6)
        pts = [(cx - 4, top + 26), (cx + 3, top + 31), (cx - 1, top + 40), (cx + 5, top + 46)]
        if pts[-1][1] < 70:
            _inlay(s, pts, [(0, 1), (1, 2), (2, 3)], 0.55, 0.3, groove=False)
        s.path(rounded_rect_path(cx - cw / 2 - 4, 90, cw + 8, 8, 1.5), fill=s.linear(0, 90, 0, 98, [(0, "#7a86d8"), (1, "#262c6e")]), stroke=INK,
               width=1.0)
        s.line(cx - cw / 2 - 3, 91, cx + cw / 2 + 3, 91, GOLD, 1.0, 0.9)
        # fallen drum piece
        bx = 46.0
        s.path(_poly([(bx - 9, 98), (bx - 8, 89), (bx - 2, 86), (bx + 6, 88), (bx + 9, 98)]), fill=s.linear(0, 86, 0, 98, [(0, "#8a96e0"), (1, "#2e3680")]),
               stroke=INK, width=1.0)
        s.line(bx - 7, 90, bx + 5, 89, GOLD, 0.9, 0.9)
        s.circle(bx - 2 + r.uniform(-1, 1), 94, 0.8, fill=GOLD_LIGHT)
        return s

    def _constellation_stone(self, seed: int) -> Svg:
        """Chipped standing stone (a menhir with a slanted top) of star-stone,
        carrying a glowing gold constellation inlay."""
        s = Svg(48, 72)
        alt = seed % 2 == 1
        outline = [(6, 70), (4, 40), (7, 18), (12, 9), (21, 4), (27, 7), (33, 6), (40, 16), (43, 38), (42, 70)] if not alt else \
            [(6, 70), (5, 34), (9, 14), (16, 10), (24, 3), (31, 9), (38, 12), (42, 30), (43, 70)]
        s.path(_poly(outline), fill=s.linear(4, 0, 43, 0, [(0, "#5a68c0"), (0.4, "#303a8a"), (1, "#141846")]), stroke=INK, width=1.3)
        s.path(_poly([outline[0], outline[1], outline[2], outline[3], (16, 30), (13, 70)]), fill="#9aa8ff", opacity=0.16)
        s.path(_line(outline[1:5]), stroke="#a6b2ff", width=1.1, opacity=0.6)
        s.path(_poly([(outline[-3][0] - 4, outline[-3][1] + 4), outline[-2], outline[-1], (outline[-1][0] - 8, 70)]), fill="#05061a", opacity=0.3)
        r = Rand(seed)
        for _ in range(9):
            s.circle(r.uniform(11, 37), r.uniform(18, 66), r.uniform(0.4, 0.8), fill=GOLD_LIGHT if r.next() < 0.5 else "#e6ecff", opacity=0.75)
        if alt:
            pts = [(13.0, 50.0), (18.0, 38.0), (25.0, 31.0), (33.0, 22.0), (31.0, 44.0), (22.0, 56.0)]
            edges = [(0, 1), (1, 2), (2, 3), (2, 4), (4, 5)]
        else:
            pts = [(14.0, 22.0), (22.0, 18.0), (31.0, 27.0), (27.0, 39.0), (16.0, 45.0), (25.0, 57.0)]
            edges = [(0, 1), (1, 2), (2, 3), (3, 4), (3, 5)]
        _inlay(s, pts, edges, 0.9, 0.55)
        s.path(blob(24, 70, 22, 3.6, 0.2, seed=seed, squash_top=1.3), fill="#1a1e52", opacity=0.9)
        return s

    def _telescope(self) -> Svg:
        """Brass telescope with blue enamel bands on a tripod, aimed at the stars."""
        s = Svg(80, 90)
        hx, hy = 34.0, 46.0  # mount head
        for fx in (14.0, 34.0, 56.0):
            s.line(hx, hy, fx, 89, INK, 3.6)
            s.line(hx, hy, fx, 89, "#8a6a3a" if fx != 34.0 else "#6a4e2a", 2.0)
        s.circle(hx, hy, 3.6, fill=s.radial(hx - 1, hy - 1, 4, [(0, GOLD_HI), (1, GOLD_DARK)]), stroke=INK, width=0.8)
        with s.group(transform=f"rotate(-32 {hx:.1f} {hy:.1f})"):
            x0, x1 = hx - 22, hx + 34
            s.path(f"M{x0:.1f} {hy - 3.4:.1f} L{x1:.1f} {hy - 5.2:.1f} L{x1:.1f} {hy + 5.2:.1f} L{x0:.1f} {hy + 3.4:.1f} Z",
                   fill=s.linear(0, hy - 5, 0, hy + 5, [(0, GOLD_HI), (0.35, GOLD_LIGHT), (0.7, GOLD), (1, GOLD_DARK)]), stroke=INK, width=1.0)
            for bx in (hx - 10, hx + 8, hx + 22):
                s.rect(bx, hy - 5.4, 4, 10.8, fill=s.linear(0, hy - 5, 0, hy + 5, [(0, "#6a7ae0"), (1, "#1e246a")]), stroke=INK, width=0.6)
            s.rect(x1, hy - 6.4, 4, 12.8, fill=s.linear(0, hy - 6, 0, hy + 6, [(0, GOLD_HI), (1, GOLD_DARK)]), stroke=INK, width=0.8, rx=1)
            s.ellipse(x1 + 4, hy, 1.4, 5.4, fill=s.linear(0, hy - 5, 0, hy + 5, [(0, "#e8f6ff"), (1, "#5a7ad8")]), stroke=INK, width=0.6)
            s.rect(x0 - 6, hy - 2.2, 6, 4.4, fill=GOLD_DARK, stroke=INK, width=0.7)
            s.line(x0 + 2, hy - 2.4, x1 - 2, hy - 3.8, "#ffffff", 0.9, 0.7)
        lx, ly = hx + 34 * math.cos(math.radians(-32)) + 4, hy + 34 * math.sin(math.radians(-32)) - 2
        _glow(s, lx, ly, 8, "#dff2ff", 0.6)
        _sparkle(s, lx, ly, 4, 0.95)
        return s

    def props(self) -> dict[str, PropSpec]:
        return {
            "crystal_cluster": PropSpec(lambda: self._crystal_cluster(4), (32, 60)),
            "crystal_cluster_b": PropSpec(lambda: self._crystal_cluster(7), (32, 60)),
            "star_lantern": PropSpec(self._star_lantern, (20, 105)),
            "orrery": PropSpec(self._orrery, (34, 75)),
            "broken_column": PropSpec(lambda: self._broken_column(3), (24, 97)),
            "broken_column_b": PropSpec(lambda: self._broken_column(6), (24, 97)),
            "constellation_stone": PropSpec(lambda: self._constellation_stone(5), (24, 70)),
            "constellation_stone_b": PropSpec(lambda: self._constellation_stone(11), (24, 70)),
            "telescope": PropSpec(self._telescope, (34, 89)),
        }

    def auto_decor(self, rng, surface_w: float) -> list[tuple[str, float, float, str]]:
        out = []
        x = rng.uniform(40, 120)
        observatory = False
        while x < surface_w - 40:
            roll = rng.next()
            if roll < 0.24:
                out.append((rng.choice(["crystal_cluster", "crystal_cluster_b"]), x, rng.uniform(0.65, 0.95), "back"))
            elif roll < 0.38:
                out.append(("star_lantern", x, rng.uniform(0.9, 1.0), "back"))
            elif roll < 0.53:
                out.append((rng.choice(["broken_column", "broken_column_b"]), x, rng.uniform(0.85, 1.05), "back"))
            elif roll < 0.65:
                out.append((rng.choice(["constellation_stone", "constellation_stone_b"]), x, rng.uniform(0.8, 1.0), "back"))
            elif roll < 0.74:
                out.append(("orrery", x, rng.uniform(0.8, 0.95), "back"))
            elif roll < 0.82 and surface_w > 300 and not observatory:
                out.append(("telescope", x, rng.uniform(0.85, 1.0), "back"))
                observatory = True
            elif roll < 0.9:
                out.append((rng.choice(["crystal_cluster", "crystal_cluster_b"]), x, rng.uniform(0.45, 0.6), "mid"))
            x += rng.uniform(110, 220)
        return out

    # ------------------------------------------------------------------ indoor halls
    def interior(self, variant: str):
        """Indoor halls of the citadel. Only these variants are indoor; every
        outdoor variant of this world must keep returning None."""
        if variant in ("sanctum", "fortress"):
            return (lambda: self._hall(False)), (lambda: self._colonnade(False))
        if variant == "throne":
            return (lambda: self._hall(True)), (lambda: self._colonnade(True))
        return None

    def _hall(self, throne: bool) -> Svg:
        """960×540 backdrop. Grand hall: star-stone walls, tall windows on
        space, star charts, a giant astrolabe and a mirror floor reflecting it.
        Throne room: an eclipse — a black sun and its corona — behind the
        throne on a stepped dais, the same mirror floor."""
        s = Svg(960, 540)
        r = Rand(57 if throne else 59)
        top_c, mid_c, low_c = ("#06041a", "#120a30", "#0a0620") if throne else ("#0a0b2e", "#18184e", "#0c0c2c")
        s.rect(0, 0, 960, 540, fill=s.linear(0, 0, 0, 540, [(0, top_c), (0.6, mid_c), (1, low_c)]))
        # back wall: big star-stone blocks, a few tonal ones, gold-flecked joints
        for row in range(12):
            y = row * 46 - 6
            off = (row % 2) * 64
            for col in range(-1, 9):
                x = col * 128 + off
                v = _hash(row * 17 + col, 81 if not throne else 83)
                if v > 0.6:
                    s.rect(x + 2, y + 2, 124, 42, fill="#2a3070" if v > 0.82 else "#1a1c50", opacity=0.55 if not throne else 0.4)
                s.line(x + 1, y + 1, x + 1, y + 45, "#05061a", 2.2, 0.6)
            s.line(0, y + 1, 960, y + 1, "#05061a", 2.2, 0.6)
            s.line(0, y + 3.5, 960, y + 3.5, "#7f8ad8", 1.0, 0.16)
        for _ in range(60):
            s.circle(r.uniform(0, 960), r.uniform(0, 420), r.uniform(0.5, 1.0), fill=GOLD_LIGHT, opacity=r.uniform(0.25, 0.6))
        if throne:
            self._eclipse_throne(s, r)
        else:
            for wx in (135.0, 825.0):
                self._space_window(s, wx, 58, 360, 128, int(wx))
            for cx in (262.0, 698.0):
                self._star_chart(s, cx, 96, 92, 196, int(cx))
            self._astrolabe(s, 480, 214, 150)
        # mirror floor: a dark polished band with reflections of what stands above
        s.rect(0, 430, 960, 110, fill=s.linear(0, 430, 0, 540, [(0, "#2a2a6a"), (0.25, "#14143e"), (1, "#0a0a24")]))
        s.line(0, 431, 960, 431, "#c8d0ff", 1.6, 0.7)
        if throne:
            _soft(s, 480, 470, 200, 26, "#ffd890", 0.3, 0.1)
            _soft(s, 480, 470, 90, 14, "#ffffff", 0.25, 0.1)
        else:
            _soft(s, 480, 468, 170, 22, GOLD_LIGHT, 0.22, 0.1)
            for wx in (135.0, 825.0):
                s.rect(wx - 40, 436, 80, 70, fill=s.linear(0, 436, 0, 506, [(0, "#9fb4ff", 0.22), (1, "#9fb4ff", 0)]))
        for k in range(14):
            y = 440 + k * 7
            s.line(0, y, 960, y, "#ffffff", 0.8, 0.05 + 0.02 * (k % 3))
        return s

    def _space_window(self, s: Svg, cx: float, top: float, bottom: float, wd: float, seed: int) -> None:
        """Tall lancet window open on space (stars, nebula, a slice of the
        ringed planet), gold mullions, a shaft of starlight."""
        r = Rand(seed)
        x0, x1 = cx - wd / 2, cx + wd / 2
        spring = top + wd * 0.55
        outline = (f"M{x0:.1f} {bottom:.1f} L{x0:.1f} {spring:.1f} Q{x0:.1f} {top + wd * 0.08:.1f} {cx:.1f} {top:.1f} "
                   f"Q{x1:.1f} {top + wd * 0.08:.1f} {x1:.1f} {spring:.1f} L{x1:.1f} {bottom:.1f} Z")
        s.polygon([(x0 + 10, bottom), (x1 - 10, bottom), (x1 + 120, 540), (x0 + 60, 540)], fill="#bcc8ff", opacity=0.06)
        s.path(outline, fill=s.linear(0, top, 0, bottom, [(0, "#05061c"), (0.6, "#1c1650"), (1, "#3a2470")]))
        _soft(s, cx + r.uniform(-20, 20), (spring + bottom) / 2, wd * 0.45, 40, NEBULA_TEAL if seed % 2 else NEBULA_MAGENTA, 0.3, 0.2, -30)
        for _ in range(28):
            s.circle(r.uniform(x0 + 6, x1 - 6), r.uniform(spring - 30, bottom - 8), r.uniform(0.5, 1.3), fill="#ffffff", opacity=r.uniform(0.4, 0.95))
        for _ in range(3):
            _sparkle(s, r.uniform(x0 + 14, x1 - 14), r.uniform(spring, bottom - 40), r.uniform(2.5, 4), 0.9)
        if seed % 2:  # a slice of the ringed planet
            px, py, pr = x1 - 22, bottom - 70, 34
            s.circle(px, py, pr, fill=s.radial(px - pr * 0.4, py - pr * 0.4, pr * 1.5, [(0, "#ffe6c8"), (0.4, "#d88aa6"), (1, "#3a2468")]))
            s.ellipse(px, py + 4, pr * 1.9, pr * 0.32, stroke="#e2d4fb", width=3, opacity=0.6)
        # mullions and tracery in gold over star-stone
        for lx in (cx - wd / 6, cx + wd / 6):
            s.line(lx, spring - 12, lx, bottom, "#05061a", 5)
            s.line(lx, spring - 12, lx, bottom, GOLD_DARK, 2.0)
        for y in (spring + (bottom - spring) * 0.4, spring + (bottom - spring) * 0.75):
            s.line(x0, y, x1, y, "#05061a", 4)
            s.line(x0, y, x1, y, GOLD_DARK, 1.6)
        s.circle(cx, top + wd * 0.34, wd * 0.18, stroke=GOLD, width=2.4)
        s.polygon(star_points(cx, top + wd * 0.34, wd * 0.15, wd * 0.05, 8), fill=None, stroke=GOLD, width=1.2)
        s.path(outline, stroke="#05061a", width=13)
        s.path(outline, stroke="#3a4496", width=9)
        s.path(outline, stroke=GOLD, width=1.8)
        s.rect(x0 - 16, bottom - 1, wd + 32, 13, fill=s.linear(0, bottom, 0, bottom + 13, [(0, "#6a76cc"), (1, "#1e2462")]), stroke="#05061a",
               width=1.6, rx=2)
        s.line(x0 - 15, bottom + 0.5, x1 + 15, bottom + 0.5, GOLD, 1.4)

    def _star_chart(self, s: Svg, cx: float, top: float, wd: float, ht: float, seed: int) -> None:
        """Framed star chart on deep-blue vellum: a constellation, a few
        orbits and graduation marks."""
        x0 = cx - wd / 2
        s.rect(x0 + 4, top + 6, wd, ht, fill="#05061a", opacity=0.45)
        s.rect(x0, top, wd, ht, fill=s.linear(0, top, 0, top + ht, [(0, "#1e2a6e"), (1, "#121848")]), stroke=GOLD, width=3)
        s.rect(x0 + 5, top + 5, wd - 10, ht - 10, stroke=GOLD_DARK, width=0.8, opacity=0.8)
        c = (cx, top + ht * 0.4)
        for k, rr in enumerate((wd * 0.38, wd * 0.26)):
            s.circle(c[0], c[1], rr, stroke="#8a96e0", width=0.7, opacity=0.6)
        for k in range(12):
            a = k * math.pi / 6
            s.line(c[0] + math.cos(a) * wd * 0.38, c[1] + math.sin(a) * wd * 0.38, c[0] + math.cos(a) * wd * 0.42, c[1] + math.sin(a) * wd * 0.42,
                   GOLD_LIGHT, 0.8, 0.8)
        pts, edges = _constellation_shape(seed, 17, x0 + 12, x0 + wd - 12, top + ht * 0.6, top + ht - 14)
        _inlay(s, pts, edges, 0.9, 0.45, groove=False)
        r = Rand(seed)
        for _ in range(14):
            s.circle(r.uniform(x0 + 8, x0 + wd - 8), r.uniform(top + 8, top + ht - 8), r.uniform(0.5, 1.0), fill="#ffffff", opacity=0.7)
        _sparkle(s, c[0], c[1], 6, 0.9, GOLD_HI)
        for ex in (x0, x0 + wd):
            s.circle(ex, top, 3.2, fill=GOLD_LIGHT, stroke="#05061a", width=1)
            s.circle(ex, top + ht, 3.2, fill=GOLD_LIGHT, stroke="#05061a", width=1)

    def _astrolabe(self, s: Svg, cx: float, cy: float, rad: float) -> None:
        """Giant gold astrolabe: graduated mater, engraved plate, an openwork
        rete with star pointers, the rule across it and a central boss."""
        _glow(s, cx, cy, rad * 1.5, "#ffd88a", 0.25)
        s.circle(cx, cy, rad, fill=s.radial(cx - rad * 0.3, cy - rad * 0.3, rad * 1.4, [(0, "#2a3480"), (1, "#0e1240")]))
        for k, rr in enumerate((0.82, 0.62, 0.42)):  # engraved plate circles and arcs
            s.circle(cx, cy, rad * rr, stroke=GOLD_LIGHT, width=0.8, opacity=0.35)
        for k in range(5):
            s.path(f"M{cx - rad * 0.86:.1f} {cy + rad * (0.1 + 0.12 * k):.1f} Q{cx:.1f} {cy - rad * (0.5 - 0.15 * k):.1f} "
                   f"{cx + rad * 0.86:.1f} {cy + rad * (0.1 + 0.12 * k):.1f}", stroke=GOLD_LIGHT, width=0.7, opacity=0.25)
        # mater: graduated gold ring
        s.circle(cx, cy, rad, stroke=GOLD_DEEP, width=16)
        s.circle(cx, cy, rad, stroke=s.linear(cx - rad, cy - rad, cx + rad, cy + rad, [(0, GOLD_HI), (0.5, GOLD), (1, GOLD_DARK)]), width=13)
        for k in range(72):
            a = k * math.pi / 36
            ln = 6.0 if k % 6 == 0 else 3.0
            s.line(cx + math.cos(a) * (rad - 6), cy + math.sin(a) * (rad - 6), cx + math.cos(a) * (rad - 6 + ln), cy + math.sin(a) * (rad - 6 + ln),
                   GOLD_DEEP, 0.9 if k % 6 else 1.4)
        for k in range(12):
            a = k * math.pi / 6 + math.pi / 12
            s.polygon(star_points(cx + math.cos(a) * (rad + 1.5), cy + math.sin(a) * (rad + 1.5), 2.6, 1.0, 4), fill=GOLD_DEEP)
        # rete: an eccentric ecliptic ring and curved pointers ending in stars
        ex, ey, er = cx + rad * 0.12, cy - rad * 0.1, rad * 0.62
        s.circle(ex, ey, er, stroke=GOLD, width=5)
        s.circle(ex, ey, er, stroke=GOLD_HI, width=1.2, opacity=0.8)
        for k in range(7):
            a = k * 2 * math.pi / 7 + 0.4
            sx, sy = cx + math.cos(a) * rad * 0.2, cy + math.sin(a) * rad * 0.2
            tx, ty = cx + math.cos(a + 0.5) * rad * 0.74, cy + math.sin(a + 0.5) * rad * 0.74
            mx, my = cx + math.cos(a + 0.15) * rad * 0.55, cy + math.sin(a + 0.15) * rad * 0.55
            s.path(f"M{sx:.1f} {sy:.1f} Q{mx:.1f} {my:.1f} {tx:.1f} {ty:.1f}", stroke=GOLD, width=3)
            _glow(s, tx, ty, 9, "#fff0b8", 0.6)
            _sparkle(s, tx, ty, 6, 1.0, "#fffaf0")
        # the rule (alidade)
        a = math.radians(-28)
        dx, dy = math.cos(a) * rad * 0.98, math.sin(a) * rad * 0.98
        nx, ny = -math.sin(a) * 5, math.cos(a) * 5
        s.polygon([(cx - dx, cy - dy), (cx - nx, cy - ny), (cx + dx, cy + dy), (cx + nx, cy + ny)],
                  fill=s.linear(cx - dx, cy - dy, cx + dx, cy + dy, [(0, GOLD_LIGHT), (1, GOLD_DARK)]), stroke=GOLD_DEEP, width=1.0)
        s.circle(cx, cy, 13, fill=s.radial(cx - 3, cy - 3, 14, [(0, GOLD_HI), (0.6, GOLD), (1, GOLD_DARK)]), stroke=GOLD_DEEP, width=1.2)
        s.polygon(star_points(cx, cy, 8, 3, 8), fill="#fffaf0")
        # suspension ring and chain to the vault
        s.circle(cx, cy - rad - 14, 9, stroke=GOLD, width=3.2)
        s.line(cx, cy - rad - 23, cx, 0, GOLD_DARK, 3)

    def _eclipse_throne(self, s: Svg, r: Rand) -> None:
        """The eclipse behind the throne: a black sun with a ragged corona,
        light raking across the hall, and the throne on its stepped dais."""
        cx, cy, rad = 480.0, 196.0, 104.0
        for k in range(10):  # rays of the corona raking across the hall
            a = math.radians(-160 + k * 15 + r.uniform(-4, 4))
            ln = r.uniform(420, 620)
            wd = math.radians(r.uniform(2.0, 4.0))
            s.polygon([(cx, cy), (cx + math.cos(a - wd) * ln, cy + math.sin(a - wd) * ln), (cx + math.cos(a + wd) * ln, cy + math.sin(a + wd) * ln)],
                      fill="#ffe2a0", opacity=0.05)
        _glow(s, cx, cy, rad * 3.2, "#ff7ad0", 0.22)
        _glow(s, cx, cy, rad * 2.0, "#ffd890", 0.45)
        for k in range(36):  # ragged streamers
            a = k * math.pi / 18 + 0.07
            ln = rad * (0.25 + 0.75 * _hash(k, 151) ** 2)
            w0 = 0.05 + 0.05 * _hash(k, 152)
            s.polygon([(cx + math.cos(a - w0) * rad * 0.98, cy + math.sin(a - w0) * rad * 0.98), (cx + math.cos(a) * (rad + ln), cy + math.sin(a) * (rad + ln)),
                       (cx + math.cos(a + w0) * rad * 0.98, cy + math.sin(a + w0) * rad * 0.98)], fill="#fff2cc", opacity=0.3)
        s.circle(cx, cy, rad * 1.05, fill="#fff8e6", opacity=0.9)
        s.circle(cx, cy, rad, fill=s.radial(cx, cy, rad, [(0, "#020108"), (0.86, "#08041a"), (1, "#2a1036")]))
        _glow(s, cx - rad * 0.72, cy + rad * 0.7, 26, "#ffffff", 0.9)  # the diamond-ring flash
        _sparkle(s, cx - rad * 0.72, cy + rad * 0.7, 16, 1.0)
        # crystal braziers flanking the dais
        for bx in (250.0, 710.0):
            _glow(s, bx, 300, 70, GLOW_MAGENTA, 0.35)
            s.path(f"M{bx - 16:.1f} 316 L{bx + 16:.1f} 316 L{bx + 9:.1f} 334 L{bx - 9:.1f} 334 Z", fill=s.linear(0, 316, 0, 334, [(0, GOLD_LIGHT), (1, GOLD_DARK)]),
                   stroke="#05061a", width=1.4)
            s.rect(bx - 4, 334, 8, 96, fill=s.linear(bx - 4, 0, bx + 4, 0, [(0, "#4a56a8"), (1, "#121646")]), stroke="#05061a", width=1.2)
            for k in range(3):
                _crystal(s, bx + (k - 1) * 7, 318, (k - 1) * 20, 26 - abs(k - 1) * 8, 8, "#fff0fb", "#b04ab8", "#3a0a3a", 0.8)
        # stepped dais with gold nosings
        for k in range(4):
            wd = 420 - k * 80
            y = 430 - 16 * (k + 1)
            s.rect(480 - wd / 2, y, wd, 16, fill=mix("#141646", "#232a68", k / 4), stroke="#05061a", width=1.2)
            s.line(480 - wd / 2, y + 0.8, 480 + wd / 2, y + 0.8, GOLD, 1.6)
        # the throne: a tall dark back with a gold rim and a crystal eclipse emblem
        seat = 366.0
        back = (f"M{480 - 58:.1f} {seat:.1f} L{480 - 54:.1f} 170 Q480 104 {480 + 54:.1f} 170 L{480 + 58:.1f} {seat:.1f} Z")
        s.path(back, fill=s.linear(0, 120, 0, seat, [(0, "#1a1a50"), (1, "#0a0a28")]), stroke=GOLD, width=2.4)
        s.path(f"M{480 - 40:.1f} {seat - 20:.1f} L{480 - 38:.1f} 182 Q480 132 {480 + 38:.1f} 182 L{480 + 40:.1f} {seat - 20:.1f} Z", fill="#06061c",
               opacity=0.7)
        for k in range(5):  # crown of spikes on the backrest
            a = math.radians(-90 + (k - 2) * 24)
            bx, by = 480 + math.cos(a) * 40, 150 + math.sin(a) * 8
            tip = (bx + math.cos(a) * (46 - abs(k - 2) * 10), by + math.sin(a) * (46 - abs(k - 2) * 10))
            nx, ny = -math.sin(a) * 7, math.cos(a) * 7
            s.polygon([(bx + nx, by + ny), tip, (bx - nx, by - ny)], fill="#121244", stroke=GOLD, width=1.2)
        s.circle(480, 200, 16, fill=s.radial(480, 200, 16, [(0, "#05030c"), (0.8, "#120a26"), (1, "#3a1a3a")]), stroke=GOLD_LIGHT, width=2)
        s.circle(480, 200, 19, stroke="#fff2c8", width=1.2, opacity=0.8)
        s.rect(480 - 82, seat - 8, 164, 24, fill=s.linear(0, seat - 8, 0, seat + 16, [(0, "#2a3070"), (1, "#10123a")]), stroke=GOLD, width=1.6, rx=4)
        for side in (-1, 1):
            ax = 480 + side * 72
            s.rect(ax - 12, seat - 44, 24, 58, fill="#16184a", stroke=GOLD, width=1.4, rx=5)
            s.circle(ax, seat - 44, 7, fill=s.radial(ax - 2, seat - 46, 8, [(0, "#ffffff"), (0.5, GLOW_VIOLET), (1, "#4a2a9a")]), stroke=GOLD_DEEP, width=1)

    def _colonnade(self, throne: bool) -> Svg:
        """900×420 layer (scrolls at 0.45×): crystal columns with gold capitals
        carrying star-stone arches, constellation banners hanging between them
        (torn in the throne room). Tiles horizontally."""
        w, h = 900.0, 420.0
        s = Svg(w, h)
        cols = (150.0, 600.0)
        cw = 58.0
        cap = 64.0
        for a, b in ((-300.0, 150.0), (150.0, 600.0), (600.0, 1050.0)):
            self._arch(s, a + cw / 2 + 8, b - cw / 2 - 8, cap)
        for x in cols:
            self._crystal_column(s, x, cap, h, cw)
        for bx in (375.0, 825.0, -75.0):
            self._banner(s, bx, cap + 34, 190, 54, torn=throne)
        return s

    def _arch(self, s: Svg, xa: float, xb: float, spring: float) -> None:
        span = xb - xa
        rise = spring - 6
        thick = 18.0
        outer = [(xa - 8 + (span + 16) * t, spring - (rise + 4) * math.sin(math.pi * t)) for t in [i / 24 for i in range(25)]]
        inner = [(xa + span * t, spring + thick - (rise - thick + 8) * math.sin(math.pi * t)) for t in [i / 24 for i in range(25)]]
        s.path(_poly(outer + list(reversed(inner))), fill=s.linear(0, 0, 0, spring + thick, [(0, "#3a4496"), (1, "#1a1e56")]), stroke="#05061a",
               width=1.6)
        for t in [i / 10 for i in range(1, 10)]:
            ox, oy = xa - 8 + (span + 16) * t, spring - (rise + 4) * math.sin(math.pi * t)
            ix, iy = xa + span * t, spring + thick - (rise - thick + 8) * math.sin(math.pi * t)
            s.line(ox, oy, ix, iy, "#0a0b2c", 1.2, 0.8)
        s.path(_line(inner[1:-1]), stroke=GOLD, width=1.6, opacity=0.85)
        s.path(_line(outer[1:-1]), stroke="#8a96e0", width=1.4, opacity=0.5)
        mid = inner[12]
        s.polygon(star_points(mid[0], mid[1] + 6, 6, 2.2, 4), fill=GOLD_LIGHT)

    def _crystal_column(self, s: Svg, x: float, cap: float, h: float, cw: float) -> None:
        """Faceted crystal shaft between a gold capital and a star-stone base."""
        y0, y1 = cap + 16, h - 30
        s.rect(x - cw / 2, y0, cw, y1 - y0, fill=s.linear(x - cw / 2, 0, x + cw / 2, 0, [(0, "#8a80d8"), (0.3, "#4c40a0"), (0.55, "#2c2470"),
                                                                                    (1, "#140f40")]), stroke="#05061a", width=1.6)
        for fx, op in ((-0.3, 0.35), (-0.05, 0.18), (0.22, 0.12)):
            s.line(x + fx * cw, y0 + 2, x + fx * cw, y1 - 2, "#ffffff", 1.2, op)
        for k in range(4):  # inner light motes rising in the crystal
            yy = y0 + 30 + k * (y1 - y0 - 40) / 4
            _glow(s, x - cw * 0.1, yy, 9, "#c8f0ff", 0.35)
        s.rect(x - cw / 2 - 9, cap, cw + 18, 16, fill=s.linear(0, cap, 0, cap + 16, [(0, GOLD_HI), (0.5, GOLD), (1, GOLD_DARK)]), stroke="#05061a",
               width=1.6, rx=2)
        for k in range(5):
            s.circle(x - cw / 2 - 2 + (cw + 4) * (k + 0.5) / 5, cap + 8, 1.4, fill=GOLD_DEEP)
        s.rect(x - cw / 2 - 7, y1, cw + 14, 30, fill=s.linear(0, y1, 0, h, [(0, "#4a56a8"), (1, "#141846")]), stroke="#05061a", width=1.6, rx=2)
        s.line(x - cw / 2 - 6, y1 + 2, x + cw / 2 + 6, y1 + 2, GOLD, 1.6)
        # star lamp on the shaft
        _glow(s, x, cap + 70, 26, "#fff0b8", 0.55)
        s.polygon(star_points(x, cap + 70, 9, 3.4, 4), fill="#fffaf0", stroke=GOLD, width=1.0)

    def _banner(self, s: Svg, x: float, top: float, length: float, wd: float, torn: bool) -> None:
        """Deep-blue banner with a gold constellation and a forked tail."""
        s.line(x - wd * 0.7, top, x + wd * 0.7, top, "#05061a", 5)
        s.line(x - wd * 0.7, top - 1, x + wd * 0.7, top - 1, GOLD, 1.6)
        for ex in (x - wd * 0.7, x + wd * 0.7):
            s.circle(ex, top, 3.6, fill=GOLD_LIGHT, stroke="#05061a", width=1.2)
        tail = top + length
        if torn:
            d = (f"M{x - wd / 2:.1f} {top:.1f} L{x + wd / 2:.1f} {top:.1f} L{x + wd / 2:.1f} {tail - 40:.1f} L{x + wd * 0.18:.1f} {tail - 16:.1f} "
                 f"L{x + wd * 0.02:.1f} {tail - 48:.1f} L{x - wd * 0.2:.1f} {tail - 6:.1f} L{x - wd / 2:.1f} {tail - 30:.1f} Z")
        else:
            d = (f"M{x - wd / 2:.1f} {top:.1f} L{x + wd / 2:.1f} {top:.1f} L{x + wd / 2:.1f} {tail:.1f} L{x:.1f} {tail - wd * 0.45:.1f} "
                 f"L{x - wd / 2:.1f} {tail:.1f} Z")
        s.path(d, fill=s.linear(x - wd / 2, 0, x + wd / 2, 0, [(0, "#2a3488"), (0.45, "#1e2670"), (1, "#0e1240")]), stroke="#05061a", width=2.0)
        s.line(x - wd / 2 + 3, top + 8, x + wd / 2 - 3, top + 8, GOLD, 1.4, 0.9)
        pts = [(x - wd * 0.28, top + 40), (x - wd * 0.05, top + 30), (x + wd * 0.22, top + 46), (x + wd * 0.08, top + 72), (x - wd * 0.2, top + 88)]
        _inlay(s, pts, [(0, 1), (1, 2), (2, 3), (3, 4)], 1.1, 0.45, groove=False)
        s.path(_line([(x - wd / 2 + 2, top + 4), (x - wd / 2 + 2, tail - 36)]), stroke="#ffffff", width=2.0, opacity=0.18)

    # ------------------------------------------------------------------ cave rooms: inside a hollow asteroid
    def cave_sky(self) -> Svg:
        """Inside a hollow asteroid: craggy shell walls, glowing geodes, a rift
        open on the stars, floating rocks and crystal clusters."""
        s = Svg(960, 540)
        r = Rand(71)
        s.rect(0, 0, 960, 540, fill=s.linear(0, 0, 0, 540, [(0, "#0a0816"), (0.5, "#16122a"), (1, "#0a0812")]))
        # the rift: a jagged opening in the shell showing space
        rift = [(300, 0), (330, 40), (372, 62), (420, 58), (470, 86), (530, 72), (590, 90), (640, 60), (690, 44), (720, 0)]
        s.path(_poly(rift), fill=s.linear(0, 0, 0, 90, [(0, "#05061c"), (1, "#24185a")]))
        _soft(s, 520, 50, 170, 28, NEBULA_MAGENTA, 0.35, 0.2, 8)
        _soft(s, 420, 40, 120, 22, NEBULA_TEAL, 0.3, 0.2, -6)
        for _ in range(40):
            x, y = r.uniform(320, 700), r.uniform(4, 70)
            s.circle(x, y, r.uniform(0.5, 1.2), fill="#ffffff", opacity=r.uniform(0.5, 1.0))
        s.path(_line(rift[1:-1]), stroke="#b8b0e6", width=2.0, opacity=0.6)
        # shell walls: layered craggy silhouettes, rim-lit by the geodes
        for layer, (color, rim, base, amp) in enumerate((("#1c1830", "#4a4270", 300.0, 120.0), ("#241f3c", "#5a5288", 380.0, 90.0))):
            pts = [(0.0, 540.0)]
            for k in range(25):
                x = k * 40.0
                pts.append((x, base - amp * (0.5 + 0.5 * math.cos(x / 960 * 2 * math.pi)) + r.uniform(-18, 18)))
            pts.append((960.0, 540.0))
            s.path(_poly(pts), fill=color)
            s.path(_line(pts[1:-1]), stroke=rim, width=2.0, opacity=0.5)
        for side in (-1, 1):  # the curve of the shell closing overhead
            x = 0.0 if side < 0 else 960.0
            s.path(f"M{x:.1f} 0 L{x + side * -300:.1f} 0 Q{x + side * -150:.1f} 60 {x + side * -40:.1f} 300 L{x:.1f} 360 Z", fill="#120f22")
        # glowing geodes in the walls
        for gx, gy, gr, color in ((150.0, 250.0, 46.0, GLOW_TEAL), (812.0, 210.0, 54.0, GLOW_VIOLET), (560.0, 330.0, 34.0, "#ff8ae0"),
                                  (330.0, 360.0, 28.0, GLOW_TEAL)):
            _glow(s, gx, gy, gr * 2.6, color, 0.35)
            s.ellipse(gx, gy, gr * 1.3, gr, fill="#8a84b4", stroke="#0c0a18", width=2)
            s.ellipse(gx, gy, gr * 1.12, gr * 0.84, fill=s.radial(gx, gy, gr * 1.2, [(0, shade(color, 0.55)), (0.5, color), (1, shade(color, -0.6))]))
            for k in range(14):
                a = k * 2 * math.pi / 14 + r.uniform(-0.12, 0.12)
                bx, by = gx + math.cos(a) * gr * 1.08, gy + math.sin(a) * gr * 0.8
                _crystal(s, bx, by, math.degrees(math.atan2(gx - bx, -(gy - by))), gr * r.uniform(0.3, 0.5), gr * 0.2, "#ffffff", color,
                         shade(color, -0.6), 0.6)
            _sparkle(s, gx - gr * 0.25, gy - gr * 0.2, gr * 0.25, 0.95)
        # floating rocks in the low gravity of the hollow
        for _ in range(7):
            x, y = r.uniform(60, 900), r.uniform(120, 330)
            rr = r.uniform(6, 16)
            s.path(blob(x, y, rr * 1.4, rr, 0.22, seed=x), fill=s.linear(0, y - rr, 0, y + rr, [(0, "#4a4470"), (1, "#16122a")]), stroke="#0c0a18", width=1.2)
            s.path(f"M{x - rr * 1.2:.1f} {y - rr * 0.3:.1f} Q{x - rr * 0.6:.1f} {y - rr * 1.0:.1f} {x + rr * 0.4:.1f} {y - rr * 0.95:.1f}",
                   stroke="#a8a0d8", width=1.2, opacity=0.6)
        # crystal clusters on the far floor
        for k in range(6):
            cx = 80 + k * 160 + r.uniform(-30, 30)
            color = r.choice([GLOW_TEAL, GLOW_VIOLET])
            _glow(s, cx, 470, 46, color, 0.3)
            for j in range(3):
                _crystal(s, cx + (j - 1) * 10, 482, (j - 1) * 18 + r.uniform(-6, 6), r.uniform(26, 44) * (1.2 if j == 1 else 0.8), 12,
                         "#f2fffd", shade(color, -0.4), "#0c0a18", 1.0, 0.85)
        for _ in range(40):
            x, y = r.uniform(0, 960), r.uniform(90, 500)
            s.circle(x, y, r.uniform(0.6, 1.4), fill=r.choice(["#c8fff6", "#e6dcff"]), opacity=r.uniform(0.3, 0.7))
        return s

    # ------------------------------------------------------------------ arena gate
    def gate(self, w: float, h: float) -> Svg:
        """Arena portcullis: translucent crystal bars between gilded posts,
        gold rails with star studs and a star crest on the lintel."""
        s = Svg(w, h)
        frame = min(5.0, w * 0.13)
        crest = min(15.0, w * 0.4)
        top = crest * 1.25
        s.rect(frame, top, w - 2 * frame, h - top - 8, fill="#0c0a2e", opacity=0.55)
        n = max(3, int((w - 2 * frame) // 8))
        bar = 4.4
        for i in range(n):
            x = frame + 1.2 + i * (w - 2 * frame - 2.4 - bar) / max(1, n - 1)
            s.rect(x, top, bar, h - top - 10, fill=s.linear(x, 0, x + bar, 0, [(0, "#faf8ff"), (0.45, "#bdb4f6"), (1, "#5a4ec4")]), stroke=CRYSTAL_LINE,
                   width=0.8)
            s.line(x + 1.1, top + 2, x + 1.1, h - 12, "#ffffff", 0.9, 0.85)
            s.polygon([(x - 0.4, h - 10.5), (x + bar / 2, h), (x + bar + 0.4, h - 10.5)],
                      fill=s.linear(0, h - 11, 0, h, [(0, "#d8d2ff"), (1, "#6a5ad8")]), stroke=CRYSTAL_LINE, width=0.8)
        for fx in (0.0, w - frame):
            s.rect(fx, top - 2, frame, h - top - 4, fill=s.linear(fx, 0, fx + frame, 0, [(0, GOLD_LIGHT), (0.5, GOLD), (1, GOLD_DARK)]), stroke=INK,
                   width=0.9)
            for y in range(int(top) + 14, int(h) - 8, 20):
                s.line(fx + 0.6, y, fx + frame - 0.6, y, GOLD_DEEP, 0.8, 0.8)
        for y in (top + (h - top) * 0.3, top + (h - top) * 0.66):
            s.rect(0, y, w, 6, fill=s.linear(0, y, 0, y + 6, [(0, GOLD_HI), (0.5, GOLD), (1, GOLD_DARK)]), stroke=INK, width=0.9, rx=1.5)
            _sparkle(s, w / 2, y + 3, 3.0, 0.95, "#ffffff")
            for bx in (frame / 2, w - frame / 2):
                s.circle(bx, y + 3, 1.0, fill=GOLD_DEEP)
        # lintel with the star crest
        s.rect(0, top - 5, w, 6, fill=s.linear(0, top - 5, 0, top + 1, [(0, GOLD_HI), (1, GOLD_DARK)]), stroke=INK, width=0.9, rx=1.5)
        cx, cy = w / 2, crest * 0.95
        _glow(s, cx, cy, crest * 1.25, "#fff0b0", 0.55)
        s.circle(cx, cy, crest * 0.82, fill=s.radial(cx - 2, cy - 2, crest, [(0, "#4a4ab8"), (1, "#18145a")]), stroke=GOLD, width=1.8)
        s.circle(cx, cy, crest * 0.82, stroke=INK, width=0.6)
        s.polygon(star_points(cx, cy, crest * 0.72, crest * 0.28, 8), fill=s.linear(cx - crest, cy - crest, cx + crest, cy + crest,
                                                                                    [(0, "#ffffff"), (0.5, GOLD_LIGHT), (1, GOLD)]),
                  stroke=GOLD_DEEP, width=0.6)
        s.circle(cx, cy, crest * 0.16, fill="#ffffff")
        return s


ART_CLASS = StarCitadel
