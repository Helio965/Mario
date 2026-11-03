"""Montanhas Geladas: snowfields, frozen lakes, pine forests and blue peaks.

Identity: a pale winter sun low in the upper left with a halo ring and sun
dogs, lenticular clouds over layered blue mountain ranges, a frozen lake that
mirrors the pine forest, log huts, lanterns and rope bridges. Terrain is
blue-grey rock strata (snow resting on every ledge) under soft snow cornices
with icicles. Slippery floors (``surface == "ice"``) get a glossy translucent
cyan ice cap with reflection streaks instead of snow, so the physics reads at
a glance (rule R5: ice blue = slides). Light comes from the upper left.
"""

from __future__ import annotations

import math
from typing import Sequence

from ..svg import Rand, Svg, blob, mix, rounded_rect_path, shade, smooth_closed, smooth_open, star_points
from .base import Layer, PropSpec, Weather, WorldArt

Pt = tuple[float, float]

INK = "#2b1d2c"
SNOW_HI, SNOW, SNOW_SHADE, SNOW_DEEP, SNOW_LINE = "#ffffff", "#eef5fb", "#cddcee", "#a7bfdc", "#6a89b2"
ROCK_TOP, ROCK, ROCK_DEEP, ROCK_LINE = "#8d9fbb", "#67799a", "#3a4563", "#242d45"
ICE_HI, ICE_TOP, ICE, ICE_DEEP, ICE_LINE = "#f2feff", "#b6ecff", "#62c6ef", "#2a8bca", "#17548a"
PINE_LIGHT, PINE, PINE_DARK, PINE_LINE = "#4d917f", "#2c6a63", "#1b4849", "#123236"
WOOD_LIGHT, WOOD, WOOD_DARK = "#c99366", "#93613f", "#5a3824"
GLOW, GLOW_DEEP = "#ffd682", "#ff9f45"
VALLEY = "#b8cbe1"  # misty valley floor: bottom of the sky and of the nearest layer (seen through pits)


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


def _ridge(r: Rand, a: Pt, b: Pt, depth: int, rough: float) -> list[Pt]:
    """Jagged mountain ridge from ``a`` to ``b`` (midpoint displacement)."""
    pts = [a, b]
    for _ in range(depth):
        nxt = [pts[0]]
        for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
            seg = math.hypot(x2 - x1, y2 - y1)
            nxt.append(((x1 + x2) / 2 + r.uniform(-0.25, 0.25) * seg * rough, (y1 + y2) / 2 + r.uniform(-1, 1) * seg * rough))
            nxt.append((x2, y2))
        pts = nxt
    return pts


def _ridge_keys(r: Rand, keys: Sequence[Pt], depth: int, rough: float) -> list[Pt]:
    """Jagged ridge through several key points (summit, shoulders, foot)."""
    out = [keys[0]]
    for a, b in zip(keys, keys[1:]):
        out += _ridge(r, a, b, depth, rough)[1:]
    return out


def _down_to(path: Sequence[Pt], y_line: float) -> list[Pt]:
    """Points of ``path`` (starting at a summit) until it first reaches ``y_line``; ends on the crossing."""
    out = [path[0]]
    for (x1, y1), (x2, y2) in zip(path, path[1:]):
        if y2 >= y_line:
            t = (y_line - y1) / (y2 - y1) if y2 != y1 else 0.0
            out.append((x1 + (x2 - x1) * t, y_line))
            return out
        out.append((x2, y2))
    return out


def _icicle(s: Svg, x: float, y: float, length: float, width: float, opacity: float = 1.0) -> None:
    """Translucent icicle hanging from (x, y) with a white glint."""
    hw = width / 2
    d = (f"M{x - hw:.2f} {y:.2f} Q{x - hw * 0.35:.2f} {y + length * 0.55:.2f} {x + hw * 0.08:.2f} {y + length:.2f} "
         f"Q{x + hw * 0.45:.2f} {y + length * 0.5:.2f} {x + hw:.2f} {y:.2f} Z")
    s.path(d, fill=s.linear(x, y, x, y + length, [(0, "#f6fdff"), (0.45, "#c4ecff"), (1, "#86d2f4")]), stroke=ICE_LINE,
           width=0.55, opacity=opacity)
    s.path(f"M{x - hw * 0.45:.2f} {y + 0.8:.2f} Q{x - hw * 0.25:.2f} {y + length * 0.42:.2f} {x - hw * 0.02:.2f} {y + length * 0.78:.2f}",
           stroke="#ffffff", width=min(0.8, width * 0.22), opacity=0.9 * opacity)


def _sparkle(s: Svg, x: float, y: float, size: float, opacity: float = 0.95, color: str = "#ffffff") -> None:
    s.polygon(star_points(x, y, size, size * 0.24, 4), fill=color, opacity=opacity)


def _edge_snow(a: Pt, b: Pt, thick: float, side: int, seed: int) -> str:
    """Snow lying along a branch edge from ``a`` (summit) to ``b`` (tip): it
    rides slightly above the edge and has a lumpy underside, thickest near
    the tip. ``side`` is +1 for a left edge, -1 for a right edge."""
    ax, ay = a
    dx, dy = b[0] - ax, b[1] - ay
    ln = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / ln * side, dx / ln * side
    top = [(ax + nx * 0.6, ay + ny * 0.6)] + [(ax + dx * t + nx * 1.6, ay + dy * t + ny * 1.6) for t in (0.3, 0.6, 0.9)]
    top.append((ax + dx * 1.03 + nx * 0.8, ay + dy * 1.03 + ny * 0.8))
    low = []
    for k, t in enumerate((0.96, 0.82, 0.68, 0.54, 0.4, 0.26, 0.12)):
        lump = 1.0 if k % 2 else 0.45 + 0.2 * _hash(seed * 7 + k, 3)
        d = thick * lump * (0.35 + 0.65 * t)
        low.append((ax + dx * t - nx * d, ay + dy * t - ny * d))
    return smooth_closed(top + low, 0.5)


def _pine_points(x: float, base: float, h: float, tiers: int = 4, spread: float = 0.42) -> list[Pt]:
    """Silhouette of a snowy fir: stacked tiers with drooping tips."""
    w = h * spread
    left: list[Pt] = []
    step = h * 0.86 / tiers
    for i in range(tiers):
        k = i / tiers
        y_bottom = base - h * 0.1 - step * i
        half = w * 0.5 * (1 - k * 0.78)
        left.append((x - half, y_bottom))
        left.append((x - half * 0.42, y_bottom - step * 0.62))
    right = [(2 * x - px, py) for px, py in reversed(left)]
    return [(x - w * 0.05, base)] + left + [(x, base - h)] + right + [(x + w * 0.05, base)]


# --------------------------------------------------------------------------- world
class FrozenPeaks(WorldArt):
    id = "frozen_peaks"
    name = "Montanhas Geladas"
    accent = "#4cb3e6"
    terrain_headroom = 12.0
    provisional = False
    SUN = (214.0, 128.0)

    # ------------------------------------------------------------------ sky
    def sky(self) -> Svg:
        s = Svg(960, 540)
        s.rect(0, 0, 960, 540, fill=s.linear(0, 0, 0, 540, [(0, "#3576c2"), (0.3, "#6ea9df"), (0.58, "#b6d7f0"),
                                                            (0.78, "#e1eef8"), (1, VALLEY)]))
        sx, sy = self.SUN
        s.circle(sx, sy, 360, fill=s.radial(sx, sy, 360, [(0, "#ffffff", 0.5), (0.28, "#eef6ff", 0.2), (1, "#e6f2ff", 0)]))
        # 22° halo ring and two sun dogs: ice crystals glittering in the cold air
        s.circle(sx, sy, 98, stroke="#fff0da", width=8, opacity=0.12)
        s.circle(sx, sy, 103, stroke="#d6ebff", width=5, opacity=0.18)
        for dx in (-101.0, 101.0):
            s.ellipse(sx + dx, sy + 3, 10, 18, fill=s.radial(sx + dx, sy + 3, 18, [(0, "#ffffff", 0.8), (0.45, "#fff1df", 0.32), (1, "#ffffff", 0)]))
        s.circle(sx, sy, 64, fill=s.radial(sx, sy, 64, [(0, "#ffffff", 0.95), (0.4, "#ffffff", 0.35), (1, "#ffffff", 0)]))
        s.circle(sx, sy, 25, fill=s.radial(sx - 6, sy - 6, 30, [(0, "#ffffff"), (0.7, "#fffbf2"), (1, "#fbe9cf")]))
        # feathery cirrus: tapered strands that fade out at both ends
        r = Rand(5)
        for i in range(6):
            x, y = r.uniform(-40, 800), r.uniform(44, 215)
            length, thick, rise = r.uniform(170, 330), r.uniform(4, 8), r.uniform(-8, 16)
            veil = s.linear(x, 0, x + length, 0, [(0, "#ffffff", 0), (0.3, "#ffffff", 0.34), (0.75, "#ffffff", 0.22), (1, "#ffffff", 0)])
            for strand in range(3):
                oy = strand * thick * 0.8
                top = [(x + length * k / 6 + strand * 9, y + oy - rise * k / 6 + 2.4 * math.sin(k * 1.2 + i + strand)) for k in range(7)]
                bottom = [(px, py + thick * (0.3 + 0.7 * math.sin(math.pi * k / 6)) * (1 - strand * 0.28)) for k, (px, py) in enumerate(top)]
                d = smooth_open(top) + "L" + smooth_open(list(reversed(bottom)))[1:] + "Z"
                s.path(d, fill=veil, opacity=0.95 - strand * 0.3)
        s.rect(0, 280, 960, 260, fill=s.linear(0, 280, 0, 540, [(0, "#eef6fc", 0), (0.55, "#eef6fc", 0.4), (1, VALLEY, 0.9)]))
        return s

    def _lenticular(self, seed: int, w: float, h: float) -> Svg:
        """Stack of lens clouds, the classic mountain-wave cloud."""
        r = Rand(seed)
        s = Svg(w, h)
        cx = w / 2
        for k in range(3):
            lw = w * (0.94 - 0.24 * k) * r.uniform(0.9, 1.0)
            ly = h * (0.74 - 0.21 * k)
            th = h * (0.2 - 0.035 * k)
            x0 = cx - lw / 2 + r.uniform(-10, 10) * k
            x1 = x0 + lw
            d = (f"M{x0:.1f} {ly:.1f} C{x0 + lw * 0.22:.1f} {ly - th * 1.5:.1f} {x1 - lw * 0.22:.1f} {ly - th * 1.5:.1f} {x1:.1f} {ly:.1f} "
                 f"C{x1 - lw * 0.3:.1f} {ly + th * 0.75:.1f} {x0 + lw * 0.3:.1f} {ly + th * 0.75:.1f} {x0:.1f} {ly:.1f} Z")
            s.path(d, fill="#9fb6d6", opacity=0.35)
            s.path(d, fill=s.linear(0, ly - th * 1.2, 0, ly + th * 0.6, [(0, "#ffffff"), (0.55, "#eef4fb"), (1, "#b3c8e3")]))
            s.path(f"M{x0 + lw * 0.12:.1f} {ly - th * 0.55:.1f} Q{cx:.1f} {ly - th * 1.25:.1f} {x1 - lw * 0.18:.1f} {ly - th * 0.6:.1f}",
                   stroke="#ffffff", width=2.2, opacity=0.8)
        return s

    def _cumulus(self, seed: int, w: float, h: float) -> Svg:
        """Flat-bottomed winter cloud with cool blue shading."""
        r = Rand(seed)
        s = Svg(w, h)
        base = h * 0.8
        puffs = []
        n = 7
        for i in range(n):
            cx = w * (0.1 + 0.8 * i / (n - 1)) + r.uniform(-6, 6)
            rad = h * (0.2 + 0.2 * math.sin(math.pi * i / (n - 1))) + r.uniform(-3, 3)
            puffs.append((cx, base - rad * 0.55, rad))
        for cx, cy, rad in puffs:
            s.circle(cx + 3, cy + 5, rad, fill="#a8bfdc", opacity=0.4)
        body = s.linear(0, h * 0.15, 0, base + 4, [(0, "#ffffff"), (0.6, "#edf3fa"), (1, "#bccfe6")])
        for cx, cy, rad in puffs:
            s.circle(cx, cy, rad, fill=body)
        s.path(f"M{w * 0.08:.1f} {base:.1f} Q{w * 0.5:.1f} {base + 7:.1f} {w * 0.92:.1f} {base:.1f} L{w * 0.92:.1f} {base - 9:.1f} "
               f"L{w * 0.08:.1f} {base - 9:.1f} Z", fill="#d4e1ef")
        for cx, cy, rad in puffs[1:-1]:
            s.circle(cx - rad * 0.3, cy - rad * 0.35, rad * 0.42, fill="#ffffff", opacity=0.8)
        return s

    def sky_extras(self) -> dict[str, PropSpec]:
        return {
            "fp.cloud.0": PropSpec(lambda: self._lenticular(3, 280, 84), (0, 0)),
            "fp.cloud.1": PropSpec(lambda: self._cumulus(8, 230, 82), (0, 0)),
            "fp.cloud.2": PropSpec(lambda: self._lenticular(14, 210, 66), (0, 0)),
        }

    # ------------------------------------------------------------------ mountains (shared by the far layers)
    def _mountain(self, s: Svg, seed: int, px: float, py: float, wl: float, wr: float, base: float, cap: float,
                  pal: dict[str, str]) -> None:
        """Asymmetric peak (optional shoulders), lit from the left, with a
        snowfield whose lower edge sends tongues down the gullies."""
        r = Rand(seed)
        kind = r.next()
        height = base - py
        lkeys: list[Pt] = [(px - wl, base)]
        if kind < 0.45:
            lkeys.append((px - wl * r.uniform(0.38, 0.55), py + height * r.uniform(0.2, 0.32)))
        lkeys.append((px, py))
        rkeys: list[Pt] = [(px, py)]
        if kind > 0.55:
            rkeys.append((px + wr * r.uniform(0.3, 0.5), py + height * r.uniform(0.16, 0.3)))
        rkeys.append((px + wr, base))
        left = _ridge_keys(r, lkeys, 3, 0.12)
        right = _ridge_keys(r, rkeys, 3, 0.12)
        s.path(_poly(left + right[1:]), fill=s.linear(0, py, 0, base, [(0, pal["rock"]), (1, pal["rock_low"])]))
        spine = _ridge(r, (px, py), (px + wr * r.uniform(0.08, 0.3), base), 3, 0.07)
        s.path(_poly(spine + list(reversed(right))), fill=s.linear(0, py, 0, base, [(0, pal["shadow"]), (1, pal["shadow_low"])]))
        for _ in range(3):  # couloirs on the lit face
            gx, gy = left[int((len(left) - 1) * r.uniform(0.45, 0.8))]
            end = (gx + r.uniform(10, 30), gy + r.uniform(30, 70))
            s.path(smooth_open([(gx + 2, gy + 2), ((gx + end[0]) / 2 + r.uniform(-4, 4), (gy + end[1]) / 2), end]),
                   stroke=pal["line"], width=r.uniform(1.0, 2.0), opacity=0.45)
        ys = py + cap
        cap_l = _down_to(list(reversed(left)), ys)
        cap_r = _down_to(right, ys)
        xl, xr = cap_l[-1][0], cap_r[-1][0]
        span = max(1.0, xr - xl)
        tongues = [(r.uniform(xl + 5, xr - 5), r.uniform(7, 28) * (0.6 + cap / 120), r.uniform(3, 7)) for _ in range(max(1, int(span / 24)))]
        cols = {xl + span * i / max(2, int(span / 6)) for i in range(1, max(2, int(span / 6)))}
        for tx, _tl, tw in tongues:
            cols |= {tx - tw, tx, tx + tw}
        zig = []
        for x in sorted((c for c in cols if xl < c < xr), reverse=True):
            y = ys + 2.5 * math.sin(x * 0.13 + seed) + r.uniform(-1.2, 1.2)
            for tx, tl, tw in tongues:
                y += tl * max(0.0, 1 - abs(x - tx) / tw)
            zig.append((x, y))
        snow = list(reversed(cap_l)) + cap_r[1:] + zig
        s.path(_poly(snow), fill=s.linear(0, py, 0, ys + 20, [(0, pal["snow"]), (1, mix(pal["snow"], pal["snow_shadow"], 0.3))]))
        spine_cap = _down_to(spine, ys)
        xs = spine_cap[-1][0]
        s.path(_poly(spine_cap + sorted(p for p in zig if p[0] > xs) + list(reversed(cap_r))), fill=pal["snow_shadow"])
        for tx, tl, _tw in tongues:  # the gully keeps a thin snow streak below each tongue
            if r.next() < 0.8:
                y0 = ys + tl - 2
                ln = r.uniform(10, 40)
                s.path(smooth_open([(tx, y0), (tx + r.uniform(-2, 4), y0 + ln * 0.5), (tx + r.uniform(0, 7), y0 + ln)]),
                       stroke=pal["snow"] if tx < xs else pal["snow_shadow"], width=r.uniform(1.0, 2.0), opacity=0.8)

    def _range(self, s: Svg, w: float, specs: list[tuple[float, float, float, float, float, float]], pal: dict[str, str],
               seed: int) -> None:
        """Draw mountains, wrapping copies across the strip edges so a strip tiles with itself."""
        for i, (px, py, wl, wr, base, cap) in enumerate(specs):
            for shift in (-w, 0.0, w):
                if px + shift + wr < 0 or px + shift - wl > w:
                    continue
                self._mountain(s, seed * 31 + i, px + shift, py, wl, wr, base, cap, pal)

    def _fir(self, s: Svg, x: float, base: float, h: float, fill: str, lit: str, snow: str) -> None:
        """Small background fir: silhouette, lit left half and snow on the tiers."""
        pts = _pine_points(x, base, h)
        s.path(_poly(pts), fill=fill)
        half = pts[: len(pts) // 2 + 1]
        s.path(_poly(half + [(x, base)]), fill=lit, opacity=0.6)
        for k in range(1, len(half) - 1, 2 if h >= 18 else 4):
            ax, ay = half[k]
            s.path(f"M{ax:.1f} {ay:.1f} Q{(ax + x) / 2:.1f} {ay - h * 0.09:.1f} {x + h * 0.06:.1f} {ay - h * 0.1:.1f}", stroke=snow,
                   width=max(1.0, h * 0.055), opacity=0.95)
        s.circle(x, base - h + 1, max(0.8, h * 0.03), fill=snow)

    # ------------------------------------------------------------------ parallax layers
    def _far(self, seed: int) -> Svg:
        # Only the upper part of this range is ever visible (the lake layer
        # covers the rest), so the strip is cropped at ``h`` with the slopes of
        # mountains whose feet would sit at ``foot``.
        w, h, foot = 1200.0, 232.0, 330.0
        s = Svg(w, h)
        r = Rand(seed)
        pal = {"rock": "#b1c3df", "rock_low": "#c4d3ea", "shadow": "#9db1d5", "shadow_low": "#b6c6e2", "snow": "#f8fbff",
               "snow_shadow": "#d0dcf0", "line": "#96a9cb"}
        specs = []
        x = 60.0
        while x < w - 40:
            py = r.uniform(18, 100)
            k = (h + 8 - py) / (foot - py)
            specs.append((x, py, r.uniform(170, 300) * k, r.uniform(170, 300) * k, h + 8, (foot - py) * r.uniform(0.42, 0.6)))
            x += r.uniform(170, 260)
        specs.sort(key=lambda m: m[1])
        self._range(s, w, specs, pal, seed)
        s.rect(0, h * 0.35, w, h * 0.65, fill=s.linear(0, h * 0.35, 0, h, [(0, "#dfeaf6", 0), (0.6, "#dfeaf6", 0.55), (1, "#dfeaf6", 0.85)]))
        return s

    def _lake(self, seed: int) -> Svg:
        """Second range; fir groves on snowy foothills; a frozen lake mirroring them."""
        w, h = 1200.0, 300.0
        s = Svg(w, h)
        r = Rand(seed)
        shore = 176.0
        pal = {"rock": "#768db4", "rock_low": "#8da3c6", "shadow": "#586e98", "shadow_low": "#7287ae", "snow": "#ffffff",
               "snow_shadow": "#b4c8e7", "line": "#50658e"}
        specs = []
        x = 30.0
        while x < w - 30:
            py = r.uniform(34, 108)
            specs.append((x, py, r.uniform(110, 210), r.uniform(110, 210), shore - 4, (shore - py) * r.uniform(0.36, 0.52)))
            x += r.uniform(140, 230)
        specs.sort(key=lambda m: m[1])
        self._range(s, w, specs, pal, seed)
        s.rect(0, 60, w, shore - 50, fill=s.linear(0, 60, 0, shore, [(0, "#e4eef9", 0), (1, "#e4eef9", 0.6)]))

        def hill(x: float) -> float:
            t = x / w * 2 * math.pi
            return shore - 22 + 7 * math.sin(t * 3 + 0.4) + 5 * math.sin(t * 7 + 1.3) + 2.5 * math.sin(t * 13 + 2.0)

        foot = [(x, hill(x)) for x in _samples(w, 8)]
        s.path(_line([(0, shore + 4)] + foot + [(w, shore + 4)]) + "Z", fill=s.linear(0, shore - 32, 0, shore, [(0, "#eef4fa"), (1, "#cbdaec")]))
        trees = []
        for _c in range(12):
            cx, spread = r.uniform(0, w), r.uniform(18, 72)
            for _t in range(int(spread / 5.0)):
                tx = (cx + r.uniform(-spread, spread)) % w
                d = abs(tx - cx) / spread if abs(tx - cx) <= spread else 1.0
                top = hill(tx)
                by = top + r.uniform(2, shore - top + 1)
                depth = (by - top) / (shore - top + 1)
                trees.append((tx, by, r.uniform(11, 20) * (1.25 - 0.5 * d) * (0.7 + 0.5 * depth)))
        trees.sort(key=lambda t: t[1])
        for tx, by, th in trees:
            for shift in (-w, 0.0, w):
                if -th < tx + shift < w + th:
                    self._fir(s, tx + shift, by, th, "#3a6474", "#5a8696", "#f2f8fd")
        # the frozen lake
        edge = [(x, shore + 1.4 * math.sin(x / w * 2 * math.pi * 9 + 0.5) + 0.9 * math.sin(x / w * 2 * math.pi * 23)) for x in _samples(w, 6)]
        s.path(_line(edge + [(w, h), (0, h)]) + "Z", fill=s.linear(0, shore, 0, h, [(0, "#d3eef9"), (0.25, "#b2dbef"), (1, "#8cc4e3")]))
        for tx, by, th in trees:
            if shore - by < 7:
                for shift in (-w, 0.0, w):
                    if -th < tx + shift < w + th:
                        pts = [(px, 2 * shore - py + 2) for px, py in _pine_points(tx + shift, by, th * 0.9)]
                        s.path(_poly(pts), fill="#5f93ae", opacity=0.3)
        s.path(_line(edge), stroke="#f6fafd", width=2.6)
        for _ in range(24):
            gx, gy = r.uniform(0, w), r.uniform(shore + 5, h - 50)
            s.line(gx, gy, min(w, gx + r.uniform(20, 110)), gy, "#ffffff", r.uniform(0.8, 1.8), r.uniform(0.4, 0.85))
        for _ in range(8):
            gx, gy = r.uniform(30, w - 30), r.uniform(shore + 14, h - 60)
            s.path(blob(gx, gy, r.uniform(16, 44), r.uniform(2.4, 4.5), 0.2, seed=gx), fill="#f7fbfe", opacity=0.85)
        for _ in range(5):
            cx, cy = r.uniform(40, w - 40), r.uniform(shore + 10, h - 50)
            pts = [(cx, cy)]
            for _k in range(5):
                pts.append((pts[-1][0] + r.uniform(8, 18), pts[-1][1] + r.uniform(-4, 4)))
            s.path(_line(pts), stroke="#ffffff", width=0.9, opacity=0.6)
        return s

    def _hill_line(self, x: float, w: float, base: float, k: int, seed: int) -> float:
        """Rolling crest whose value and slope match at both strip edges for every
        seed (the per-strip variation is windowed), so strips tile in any order."""
        t = x / w * 2 * math.pi
        common = 9 * math.sin(t * 2 + 0.7) + 5 * math.sin(t * 5 + 1.9)
        window = math.sin(math.pi * x / w) ** 2
        var = 16 * math.sin(t * 3 + seed * 1.7 + k) + 7 * math.sin(t * 7 + seed * 0.9)
        return base + common + window * var

    def _cabin_far(self, s: Svg, x: float, base: float, size: float) -> None:
        w, hgt = size, size * 0.62
        for k in range(4):
            s.circle(x + w * 0.3 + k * w * 0.16, base - hgt - w * (0.55 + 0.22 * k), w * (0.09 + 0.04 * k), fill="#f4f8fc", opacity=0.55 - k * 0.1)
        s.rect(x + w * 0.22, base - hgt - w * 0.42, w * 0.13, w * 0.3, fill="#7a6a6a")
        s.rect(x - w / 2, base - hgt, w, hgt, fill="#8a6650")
        for k in range(1, 4):
            s.line(x - w / 2, base - hgt + hgt * k / 4, x + w / 2, base - hgt + hgt * k / 4, "#6a4a38", 0.8)
        s.circle(x + w * 0.18, base - hgt * 0.5, w * 0.5, fill=s.radial(x + w * 0.18, base - hgt * 0.5, w * 0.5, [(0, GLOW, 0.5), (1, GLOW, 0)]))
        s.rect(x + w * 0.06, base - hgt * 0.66, w * 0.24, hgt * 0.32, fill="#ffd27a")
        s.polygon([(x - w * 0.68, base - hgt + 1), (x, base - hgt - w * 0.5), (x + w * 0.68, base - hgt + 1)], fill="#f7fbfe")
        s.polygon([(x, base - hgt - w * 0.5), (x + w * 0.68, base - hgt + 1), (x + w * 0.1, base - hgt + 1)], fill="#c8d9ee")

    def _mid(self, seed: int) -> Svg:
        """Snowy rolling hills with fir-covered knolls; a rope bridge spans the
        valley in one strip, a smoking cabin sits on the other."""
        w, h = 1100.0, 270.0
        s = Svg(w, h)
        r = Rand(seed)
        bridge = seed % 2 == 0
        back = [(x, self._hill_line(x, w, 168, 0, seed) - 10) for x in _samples(w, 10)]
        s.path(_line([(0, h)] + back + [(w, h)]) + "Z", fill=s.linear(0, 130, 0, h, [(0, "#cbdaeb"), (1, "#b1c5de")]))
        knolls = [(380.0, 100.0), (720.0, 108.0)] if bridge else [(250.0, 116.0), (850.0, 98.0)]

        def knoll_y(x: float, kx: float, ktop: float) -> float:
            u = max(-1.0, min(1.0, (x - kx) / 200))
            return 214 - (214 - ktop) * math.cos(math.pi / 2 * u) ** 1.5

        for kx, ktop in knolls:
            pts = [(kx - 200 + x, knoll_y(kx - 200 + x, kx, ktop)) for x in _samples(400, 8)]
            s.path(_line(pts + [(kx + 200, h), (kx - 200, h)]) + "Z", fill=s.linear(0, ktop, 0, 214, [(0, "#eaf1f9"), (1, "#c0d2e8")]))
            s.path(_line([p for p in pts if p[0] < kx - 4]), stroke="#ffffff", width=1.6, opacity=0.8)
            grove = []
            for _ in range(16):
                tx = kx + r.uniform(-150, 150)
                grove.append((tx, knoll_y(tx, kx, ktop) + r.uniform(3, 16), r.uniform(26, 50)))
            for tx, ty, th in sorted(grove, key=lambda g: g[1]):
                self._fir(s, tx, ty, th, "#2f5f68", "#4a8088", "#f1f7fc")
        bx = (knolls[0][0] + knolls[1][0]) / 2

        def front_y(x: float) -> float:
            y = self._hill_line(x, w, 198, 1, seed)
            return y + (26 * math.exp(-((x - bx) / 80) ** 2) if bridge else 0.0)

        if bridge:
            x0b, x1b = knolls[0][0] + 118, knolls[1][0] - 118
            y0b, y1b = knoll_y(x0b, *knolls[0]) - 2, knoll_y(x1b, *knolls[1]) - 2
            sag = 16.0

            def deck(t: float) -> float:
                return y0b + (y1b - y0b) * t + sag * math.sin(math.pi * t)

            for k in range(17):
                t = (k + 0.5) / 17
                px = x0b + (x1b - x0b) * t
                s.line(px, deck(t), px, deck(t) + 3.4, "#6a4a34", 3.6)
            rail = 11.0
            for t in [i / 16 for i in range(1, 16)]:
                px = x0b + (x1b - x0b) * t
                s.line(px, deck(t) - rail + sag * 0.35 * math.sin(math.pi * t), px, deck(t), "#5a3d2a", 0.7)
            s.path(_line([(x0b + (x1b - x0b) * t, deck(t)) for t in [i / 20 for i in range(21)]]), stroke="#5a3d2a", width=1.2)
            s.path(_line([(x0b + (x1b - x0b) * t, deck(t) - rail + sag * 0.35 * math.sin(math.pi * t)) for t in [i / 20 for i in range(21)]]),
                   stroke="#5a3d2a", width=1.1)
            for px, py in ((x0b, y0b), (x1b, y1b)):
                s.rect(px - 2.2, py - rail - 3, 4.4, rail + 6, fill="#6a4a34", rx=1)
                s.circle(px, py - rail - 3.2, 2.4, fill="#ffffff")
        front = [(x, front_y(x)) for x in _samples(w, 10)]
        s.path(_line([(0, h)] + front + [(w, h)]) + "Z", fill=s.linear(0, 170, 0, h, [(0, "#e2ecf6"), (0.5, "#cbdaec"), (1, "#b6c9e1")]))
        s.path(_line(front), stroke="#ffffff", width=2.0, opacity=0.9)
        s.path(_line([(x, y + 5) for x, y in front]), stroke="#b9cde4", width=3.0, opacity=0.5)
        if not bridge:
            cx = w * 0.5 + r.uniform(-40, 40)
            self._cabin_far(s, cx, front_y(cx) + 5, 36)
        for _ in range(30):
            px = r.uniform(20, w - 20)
            _sparkle(s, px, front_y(px) + r.uniform(4, 40), r.uniform(1.2, 2.2), 0.8)
        return s

    def _near(self, seed: int) -> Svg:
        """Shaded snow drifts with saplings, frosted shrubs and rocks; solid valley mist below."""
        w, h = 900.0, 210.0
        s = Svg(w, h)
        r = Rand(seed)

        def crest_y(x: float) -> float:
            return self._hill_line(x, w, 92, 2, seed) * 0.7 + 22

        for _ in range(7):
            tx = r.uniform(40, w - 40)
            ty = crest_y(tx) + 4
            if r.next() < 0.65:
                self._fir(s, tx, ty, r.uniform(36, 72), "#285a5e", "#3f7a7a", "#eef5fb")
            else:
                rw = r.uniform(14, 24)
                rock = [(tx - rw, ty), (tx - rw * 0.8, ty - rw * 0.5), (tx - rw * 0.2, ty - rw * 0.85), (tx + rw * 0.5, ty - rw * 0.7),
                        (tx + rw, ty - rw * 0.2), (tx + rw, ty)]
                s.path(_poly(rock), fill=s.linear(tx - rw, 0, tx + rw, 0, [(0, "#8b9dba"), (1, "#53668a")]))
                s.path(blob(tx - rw * 0.2, ty - rw * 0.8, rw * 0.7, rw * 0.2, 0.2, seed=tx + 1), fill="#f2f7fc")
        crest = [(x, crest_y(x)) for x in _samples(w, 8)]
        s.path(_line([(0, h)] + crest + [(w, h)]) + "Z",
               fill=s.linear(0, 60, 0, h, [(0, "#d3e0ef"), (0.3, "#c0d1e6"), (0.6, VALLEY), (1, VALLEY)]))
        s.path(_line(crest), stroke="#eef4fa", width=2.0, opacity=0.9)
        for _ in range(9):
            dx = r.uniform(30, w - 30)
            dy = crest_y(dx) + r.uniform(10, 30)
            s.path(smooth_open([(dx - 50, dy + 6), (dx, dy), (dx + 60, dy + 5)]), stroke="#a6bcd8", width=3.0, opacity=0.6)
        for _ in range(5):
            bx = r.uniform(40, w - 40)
            by = crest_y(bx) + 2
            for c in range(3):
                s.path(blob(bx + (c - 1) * 9, by - 6 - (c % 2) * 3, 8, 6, 0.15, seed=bx + c), fill="#3a6f6c")
            s.path(blob(bx, by - 11, 16, 4, 0.2, seed=bx + 9), fill="#f5f9fd")
            for b in range(4):
                s.circle(bx - 10 + b * 6.5, by - 5 + (b % 2) * 2, 1.6, fill="#d8434f")
        for _ in range(40):
            px = r.uniform(10, w - 10)
            _sparkle(s, px, crest_y(px) + 2 + r.uniform(0, 50), r.uniform(1.2, 2.4), 0.85)
        return s

    def layer_art(self) -> dict[str, PropSpec]:
        art = {
            "fp.far.0": PropSpec(lambda: self._far(11), (0, 0)),
            "fp.lake.0": PropSpec(lambda: self._lake(17), (0, 0)),
        }
        for i in range(2):
            art[f"fp.mid.{i}"] = PropSpec((lambda i=i: self._mid(20 + i)), (0, 0))
            art[f"fp.near.{i}"] = PropSpec((lambda i=i: self._near(40 + i * 3)), (0, 0))
        return art

    def layers(self) -> list[Layer]:
        return [
            Layer("far", 0.05, ["fp.far.0"], 1200, -36, vertical=0.03),
            Layer("lake", 0.12, ["fp.lake.0"], 1200, 52, vertical=0.08),
            Layer("mid", 0.27, ["fp.mid.0", "fp.mid.1"], 1100, 58, vertical=0.18),
            Layer("near", 0.5, ["fp.near.0", "fp.near.1"], 900, 98, vertical=0.32),
        ]

    # ------------------------------------------------------------------ terrain
    def terrain(self, style: str, w: float, h: float, seed: int, left: bool, right: bool, top: bool = True, x0: float = 0.0,
                surface: str = "normal") -> Svg:
        """Terrain chunk art. Everything that crosses chunk borders (cap edges,
        strata, ledge snow, icicles, reflections) is a function of the world x
        (``x0`` + local x), so adjacent chunks join seamlessly; only the hanging
        edges are outlined, never the chunk's vertical borders."""
        if style == "cave":
            return self._cave(w, h, seed, left, right, x0)
        hr = self.terrain_headroom
        s = Svg(w, h + hr)
        r = Rand(seed)
        ice = surface == "ice"
        self._rock(s, r, w, h, hr, left, right, x0, ice and top)
        if top:
            if ice:
                self._ice_cap(s, r, w, hr, left, right, x0)
            else:
                self._snow_cap(s, r, w, hr, left, right, x0)
        return s

    def _rock(self, s: Svg, r: Rand, w: float, h: float, y0: float, left: bool, right: bool, x0: float, glazed: bool) -> None:
        bottom = h + y0
        il, ir = (3.5 if left else 0.0), (3.5 if right else 0.0)
        ys = [y0 + 4 + (bottom - y0 - 4) * i / 10 for i in range(11)]
        lface = [(il + 1.2 * math.sin(y * 0.21 + x0 * 0.01), y) for y in ys] if left else [(0.0, y) for y in ys]
        rface = [(w - ir - 1.2 * math.sin(y * 0.19 + x0 * 0.013), y) for y in ys] if right else [(w, y) for y in ys]
        body = list(reversed(lface)) + rface
        s.path(_poly(body), fill=s.linear(0, y0, 0, bottom, [(0, ROCK_TOP), (0.28, ROCK), (1, ROCK_DEEP)]))
        if glazed:
            s.rect(il, y0 + 4, w - il - ir, 46, fill=s.linear(0, y0 + 6, 0, y0 + 50, [(0, "#8fe2ff", 0.5), (1, "#8fe2ff", 0)]))
        xs = _samples(w, 3.0)
        # folded strata: protruding lighter bands with snow resting on their ledges
        for k in range(6):
            def yy(lx: float, k: int = k) -> float:
                gx = x0 + lx
                return y0 + 30 + k * 25 + 3.2 * _wobble(gx, k * 1.3) + 5 * math.sin(gx * 0.006 + k * 0.6)
            if y0 + 30 + k * 25 > bottom - 10:
                break
            top_edge = [(lx, yy(lx)) for lx in xs]
            low_edge = [(lx, yy(lx) + 9) for lx in reversed(xs)]
            s.path(_poly(top_edge + low_edge), fill="#a9bad2", opacity=0.2)
            s.path(_line([(lx, yy(lx) + 9) for lx in xs]), stroke=ROCK_LINE, width=1.4, opacity=0.38)
            s.path(_line([(lx, yy(lx) + 0.6) for lx in xs]), stroke="#c3d1e3", width=0.8, opacity=0.35)
            # snow lies on the ledge only here and there (world-aligned, so it crosses chunks)
            for run in _runs(xs, lambda lx, k=k: math.sin((x0 + lx) * 0.029 + k * 2.1) + 0.6 * math.sin((x0 + lx) * 0.083 + k) > 0.9):
                pts = [(lx, yy(lx) - 0.3) for lx in run]
                s.path(_line(pts), stroke="#f4f8fc", width=1.6, opacity=0.8)
        # angular stones and frost-filled cracks
        for _ in range(max(2, int(w * h / 3400))):
            px, py = r.uniform(8, w - 8), r.uniform(y0 + 22, bottom - 6)
            rad = r.uniform(3, 7.5)
            pts = [(px + math.cos(a) * rad * r.uniform(0.7, 1.15), py + math.sin(a) * rad * 0.75 * r.uniform(0.7, 1.15))
                   for a in [i * 2 * math.pi / 6 + 0.3 for i in range(6)]]
            tone = r.choice(["#7f91ae", "#5d6f8f", "#94a6c0", "#6c7d9c"])
            s.path(_poly(pts), fill=tone, stroke=ROCK_LINE, width=0.7, opacity=0.85)
            s.path(_line(pts[3:6]), stroke="#c9d6e6", width=0.8, opacity=0.6)
        for _ in range(max(1, int(w / 75))):
            cx = r.uniform(12, w - 12)
            pts = [(cx, y0 + r.uniform(18, 40))]
            for _k in range(4):
                pts.append((pts[-1][0] + r.uniform(-6, 6), pts[-1][1] + r.uniform(7, 13)))
            s.path(_line(pts), stroke=ROCK_LINE, width=1.2, opacity=0.5)
            s.path(_line([(px + 1.1, py) for px, py in pts]), stroke="#d6e6f4", width=0.7, opacity=0.35)
        for _ in range(int(w / 140)):
            cx, cy = r.uniform(14, w - 14), r.uniform(y0 + 40, bottom - 14)
            s.circle(cx, cy, 6, fill=s.radial(cx, cy, 6, [(0, "#9feaff", 0.55), (1, "#9feaff", 0)]))
            s.polygon([(cx, cy - 4.5), (cx + 2.4, cy), (cx, cy + 3.2), (cx - 2.4, cy)], fill=s.linear(cx, cy - 4.5, cx, cy + 3, [(0, "#f2feff"), (1, "#4fb8e6")]),
                      stroke=ICE_LINE, width=0.5)
        if left:
            s.path(_poly([(px, py) for px, py in lface] + [(px + 6, py) for px, py in reversed(lface)]), fill="#b5c6dc", opacity=0.3)
            s.path(_line(lface), stroke=ROCK_LINE, width=1.2, opacity=0.7)
        if right:
            s.path(_poly([(px, py) for px, py in rface] + [(px - 8, py) for px, py in reversed(rface)]), fill="#1c2438", opacity=0.35)
            s.path(_line(rface), stroke=ROCK_LINE, width=1.2, opacity=0.7)

    def _snow_cap(self, s: Svg, r: Rand, w: float, y0: float, left: bool, right: bool, x0: float) -> None:
        step = 17.0
        xs = _samples(w, 2.0)

        def top_y(lx: float) -> float:
            gx = x0 + lx
            y = y0 - 1.5 + 0.9 * _wobble(gx, 0.4) + 0.35 * math.sin(gx * 0.17)
            if left and lx < 7:
                y += 5.5 * (1 - lx / 7) ** 2
            if right and w - lx < 7:
                y += 5.5 * (1 - (w - lx) / 7) ** 2
            return y

        def bottom_y(lx: float) -> float:
            gx = x0 + lx
            n = math.floor(gx / step)
            t = gx / step - n
            depth = 2.6 + 4.2 * _hash(n, 3)
            y = y0 + 8.5 + 1.3 * _wobble(gx, 1.7) + depth * math.sin(math.pi * t) ** 0.55
            if left and lx < 12:
                y += 6.5 * (1 - lx / 12) ** 1.6
            if right and w - lx < 12:
                y += 6.5 * (1 - (w - lx) / 12) ** 1.6
            return y

        tops = [(lx, top_y(lx)) for lx in xs]
        bottoms = [(lx, bottom_y(lx)) for lx in xs]
        # cast shadow of the cornice on the rock
        s.path(_line([(x, y + 2.6) for x, y in bottoms]), stroke="#18213a", width=5.0, opacity=0.22)
        s.path(_poly(tops + list(reversed(bottoms))),
               fill=s.linear(0, y0 - 3, 0, y0 + 17, [(0, SNOW_HI), (0.32, "#f4f9fd"), (0.68, "#d8e6f3"), (1, "#b2c9e3")]))
        # lobe volume: bluish inner rim and a lighter fold above it
        s.path(_line([(x, y - 2.0) for x, y in bottoms]), stroke="#a9c1de", width=3.0, opacity=0.65)
        s.path(_line([(x, y - 5.2) for x, y in bottoms]), stroke="#ffffff", width=1.6, opacity=0.5)
        s.path(_line(bottoms), stroke=SNOW_LINE, width=1.2)
        if left:
            s.path(f"M0 {tops[0][1]:.2f} L0 {bottoms[0][1]:.2f}", stroke=SNOW_LINE, width=1.4)
        if right:
            s.path(f"M{w:.2f} {tops[-1][1]:.2f} L{w:.2f} {bottoms[-1][1]:.2f}", stroke=SNOW_LINE, width=1.4)
        s.path(_line([(x, y + 0.9) for x, y in tops]), stroke="#ffffff", width=1.4, opacity=0.9)
        s.path(_line(tops), stroke="#b8cde6", width=0.8, opacity=0.8)
        # icicles hang from the lowest point of some lobes (world-aligned)
        n0, n1 = math.floor(x0 / step), math.floor((x0 + w) / step)
        for n in range(n0, n1 + 1):
            if _hash(n, 7) < 0.5:
                continue
            lx = (n + 0.5) * step - x0
            length = 4 + 11 * _hash(n, 8)
            width = 2.6 + 1.6 * _hash(n, 9)
            if width < lx < w - width - 1.5:
                _icicle(s, lx, bottom_y(lx) - 1.2, length, width)
        # glitter on the snow surface
        g0, g1 = math.floor(x0 / 11), math.floor((x0 + w) / 11)
        for n in range(g0, g1 + 1):
            v = _hash(n, 21)
            lx = n * 11 + 11 * _hash(n, 22) - x0
            if v < 0.62 or not 3 < lx < w - 3:
                continue
            ly = top_y(lx) + 2 + 6 * _hash(n, 23)
            if v > 0.88:
                _sparkle(s, lx, ly, 1.8 + 1.2 * _hash(n, 24))
            else:
                s.circle(lx, ly, 0.75, fill="#8fd8ff" if v > 0.75 else "#ffffff", opacity=0.9)

    def _ice_cap(self, s: Svg, r: Rand, w: float, y0: float, left: bool, right: bool, x0: float) -> None:
        slot = 9.0
        xs = _samples(w, 2.0)

        def top_y(lx: float) -> float:
            y = y0 - 0.4
            if left and lx < 4:
                y += 3.0 * (1 - lx / 4) ** 2
            if right and w - lx < 4:
                y += 3.0 * (1 - (w - lx) / 4) ** 2
            return y

        def bottom_y(lx: float) -> float:
            gx = x0 + lx
            y = y0 + 11 + 1.1 * _wobble(gx, 2.3)
            n = math.floor(gx / slot)
            for m in (n - 1, n, n + 1):
                if _hash(m, 11) > 0.58:
                    c = (m + 0.5) * slot
                    y += (3 + 7 * _hash(m, 12)) * math.exp(-((gx - c) / 2.6) ** 2)
            if left and lx < 6:
                y -= 3.5 * (1 - lx / 6)
            if right and w - lx < 6:
                y -= 3.5 * (1 - (w - lx) / 6)
            return y

        tops = [(lx, top_y(lx)) for lx in xs]
        bottoms = [(lx, bottom_y(lx)) for lx in xs]
        s.path(_line([(x, y + 2.4) for x, y in bottoms]), stroke="#0d2a4a", width=4.5, opacity=0.25)
        s.path(_poly(tops + list(reversed(bottoms))),
               fill=s.linear(0, y0 - 1, 0, y0 + 20, [(0, ICE_HI), (0.14, ICE_TOP), (0.5, ICE), (1, ICE_DEEP)]))
        # depth band and glossy reflections
        s.path(_line([(x, y - 2.2) for x, y in bottoms]), stroke="#2f7fc0", width=3.2, opacity=0.35)
        streak = 46.0
        m0, m1 = math.floor(x0 / streak), math.floor((x0 + w) / streak)
        for m in range(m0, m1 + 1):
            if _hash(m, 31) < 0.35:
                continue
            gx = m * streak + 30 * _hash(m, 32) - x0
            wide = 4 + 6 * _hash(m, 33)
            if not 2 < gx - 7 and gx + wide + 2 < w:
                continue
            s.polygon([(gx, y0 + 1.6), (gx + wide, y0 + 1.6), (gx + wide - 6, y0 + 10), (gx - 6, y0 + 10)], fill="#ffffff", opacity=0.42)
            if _hash(m, 34) > 0.4 and gx + wide + 6.5 < w - 2:
                s.polygon([(gx + wide + 3, y0 + 1.6), (gx + wide + 5, y0 + 1.6), (gx + wide - 1, y0 + 10), (gx + wide - 3, y0 + 10)],
                          fill="#ffffff", opacity=0.32)
        # internal cracks and trapped bubbles (per chunk)
        for _ in range(max(1, int(w / 90))):
            cx = r.uniform(10, w - 30)
            pts = [(cx, y0 + r.uniform(3, 6))]
            for _k in range(3):
                pts.append((pts[-1][0] + r.uniform(4, 9), pts[-1][1] + r.uniform(-1.5, 2.5)))
            s.path(_line(pts), stroke="#ffffff", width=0.7, opacity=0.65)
            s.path(_line([(px + 0.6, py + 0.8) for px, py in pts]), stroke="#2a7fbd", width=0.5, opacity=0.4)
        for _ in range(int(w / 26)):
            bx, by = r.uniform(4, w - 4), r.uniform(y0 + 4, y0 + 9)
            s.circle(bx, by, r.uniform(0.5, 1.2), stroke="#ffffff", width=0.45, opacity=0.6)
        s.path(_line(bottoms), stroke=ICE_LINE, width=1.2)
        if left:
            s.path(f"M0 {tops[0][1]:.2f} L0 {bottoms[0][1]:.2f}", stroke=ICE_LINE, width=1.4)
        if right:
            s.path(f"M{w:.2f} {tops[-1][1]:.2f} L{w:.2f} {bottoms[-1][1]:.2f}", stroke=ICE_LINE, width=1.4)
        # specular rim: the mirror-like top edge is what says "slippery"
        s.path(_line(tops), stroke="#5fb6e6", width=0.9, opacity=0.9)
        s.path(_line([(x, y + 1.3) for x, y in tops]), stroke="#ffffff", width=1.5, opacity=0.95)
        for run in _runs(xs, lambda lx: math.sin((x0 + lx) * 0.045) + 0.4 * math.sin((x0 + lx) * 0.13) > 0.35):
            s.path(_line([(lx, y0 + 4.2) for lx in run]), stroke="#ffffff", width=0.9, opacity=0.55)
        # icicles hang from the drips; frozen runs streak down the rock face
        n0, n1 = math.floor(x0 / slot), math.floor((x0 + w) / slot)
        for n in range(n0, n1 + 1):
            lx = (n + 0.5) * slot - x0
            width = 2.4 + 1.8 * _hash(n, 14)
            if not width < lx < w - width - 1.5:
                continue
            if _hash(n, 11) > 0.58:
                _icicle(s, lx, bottom_y(lx) - 1.5, 6 + 12 * _hash(n, 13), width)
            elif _hash(n, 15) > 0.8:
                ln = 14 + 24 * _hash(n, 16)
                y1 = bottom_y(lx)
                s.path(f"M{lx - 1.6:.2f} {y1:.2f} Q{lx - 1.2:.2f} {y1 + ln * 0.6:.2f} {lx:.2f} {y1 + ln:.2f} Q{lx + 1.4:.2f} {y1 + ln * 0.6:.2f} "
                       f"{lx + 1.8:.2f} {y1:.2f} Z", fill="#c8f0ff", opacity=0.45)
        # a little snow is piled only at the exposed ends ("the snow edge marks the ice")
        if left:
            s.path(blob(5.5, y0 - 0.6, 7.5, 3.6, 0.15, seed=x0, squash_top=1.15), fill=s.linear(0, y0 - 4, 0, y0 + 3, [(0, "#ffffff"), (1, SNOW_SHADE)]),
                   stroke=SNOW_LINE, width=0.8)
        if right:
            s.path(blob(w - 5.5, y0 - 0.6, 7.5, 3.6, 0.15, seed=x0 + w, squash_top=1.15),
                   fill=s.linear(0, y0 - 4, 0, y0 + 3, [(0, "#ffffff"), (1, SNOW_SHADE)]), stroke=SNOW_LINE, width=0.8)

    def _cave(self, w: float, h: float, seed: int, left: bool, right: bool, x0: float) -> Svg:
        """Blue ice-cave rock: frozen layers and glowing crystal veins near the
        surface, darkening with depth. The frost rim on top is always drawn
        (cave floors are often 'covered' by the room walls standing on them)."""
        r = Rand(seed)
        hr = self.terrain_headroom
        s = Svg(w, h + hr)
        y0 = hr
        bottom = h + hr
        s.rect(0, y0, w, h, fill=s.linear(0, y0, 0, y0 + min(h, 230), [(0, "#6a88bd"), (0.16, "#4a6196"), (0.55, "#28365f"), (1, "#151d38")]))
        xs = _samples(w, 4.0)
        for k in range(3):
            def yy(lx: float, k: int = k) -> float:
                gx = x0 + lx
                return y0 + 16 + k * 19 + 3.5 * _wobble(gx * 0.7, k * 1.9)
            if y0 + 16 + k * 19 > bottom - 6:
                break
            s.path(_line([(lx, yy(lx)) for lx in xs]), stroke="#9cbbe8", width=1.8, opacity=0.3 - k * 0.07)
            s.path(_line([(lx, yy(lx) + 2.2) for lx in xs]), stroke="#0f1630", width=1.2, opacity=0.35 - k * 0.07)
        for _ in range(max(1, int(w * min(h, 160) / 4200))):
            px, py = r.uniform(6, w - 6), r.uniform(y0 + 10, min(bottom - 6, y0 + 150))
            rad = r.uniform(4, 9)
            pts = [(px + math.cos(a) * rad * r.uniform(0.7, 1.15), py + math.sin(a) * rad * 0.7 * r.uniform(0.7, 1.15))
                   for a in [i * 2 * math.pi / 6 + 0.4 for i in range(6)]]
            s.path(_poly(pts), fill=r.choice(["#3f5588", "#2e3f6a", "#5a76aa"]), opacity=0.7)
            s.path(_line(pts[3:6]), stroke="#a9c6ee", width=0.7, opacity=0.4)
        # glowing crystal seams (per chunk, kept inside the chunk)
        for _ in range(max(1, int(w / 160))):
            vx = r.uniform(20, w - 70)
            vy = r.uniform(y0 + 24, min(bottom - 14, y0 + 110))
            pts = [(vx, vy)]
            for _k in range(5):
                pts.append((pts[-1][0] + r.uniform(7, 12), pts[-1][1] + r.uniform(-6, 6)))
            s.path(_line(pts), stroke="#7fe6ff", width=5.0, opacity=0.18)
            s.path(_line(pts), stroke="#bff4ff", width=1.5, opacity=0.85)
            s.path(_line([(px, py + 1.2) for px, py in pts]), stroke="#10204a", width=0.8, opacity=0.5)
            for px, py in pts[1:-1:2]:
                s.polygon([(px, py - 4), (px + 2, py), (px, py + 2.5), (px - 2, py)], fill=s.linear(px, py - 4, px, py + 2.5, [(0, "#f2feff"), (1, "#4fb8e6")]),
                          stroke="#1a2e5a", width=0.5)
        for _ in range(int(w / 150) + 1):
            cx, cy = r.uniform(14, w - 14), r.uniform(y0 + 16, min(bottom - 10, y0 + 80))
            color = r.choice(["#7ff0ff", "#b9a4ff", "#7ff0ff"])
            s.circle(cx, cy - 4, 14, fill=s.radial(cx, cy - 4, 14, [(0, color, 0.45), (1, color, 0)]))
            for k in range(3):
                a = math.radians(-90 + (k - 1) * 28 + r.uniform(-8, 8))
                ln = r.uniform(7, 12) * (1.2 if k == 1 else 0.85)
                tip = (cx + math.cos(a) * ln, cy + math.sin(a) * ln)
                nx, ny = -math.sin(a) * 2.4, math.cos(a) * 2.4
                s.polygon([(cx + nx, cy + ny), (tip[0] + nx * 0.6, tip[1] + ny * 0.6), (tip[0] + math.cos(a) * 2.6, tip[1] + math.sin(a) * 2.6),
                           (tip[0] - nx * 0.6, tip[1] - ny * 0.6), (cx - nx, cy - ny)],
                          fill=s.linear(cx, cy, tip[0], tip[1], [(0, shade(color, -0.35)), (1, "#f4feff")]), stroke="#1a2e5a", width=0.6)
        if left:
            s.rect(0, y0, 5, h, fill=s.linear(0, y0, 0, bottom, [(0, "#b4cdf0", 0.4), (1, "#b4cdf0", 0.05)]))
        if right:
            s.rect(w - 6, y0, 6, h, fill="#0a1024", opacity=0.45)
        # frost rim along the top
        tops = [(lx, y0 - 0.8 + 0.8 * _wobble(x0 + lx, 0.9)) for lx in _samples(w, 2.0)]
        lows = [(lx, y0 + 5.5 + 1.6 * _wobble(x0 + lx, 2.2) + 1.6 * abs(math.sin((x0 + lx) * 0.19))) for lx in _samples(w, 2.0)]
        s.path(_line([(x, y + 2) for x, y in lows]), stroke="#0b1430", width=3.0, opacity=0.35)
        s.path(_poly(tops + list(reversed(lows))), fill=s.linear(0, y0 - 2, 0, y0 + 8, [(0, "#f2fbff"), (1, "#8fc8ee")]))
        s.path(_line(lows), stroke="#2c4f86", width=1.0, opacity=0.9)
        s.path(_line([(x, y + 0.8) for x, y in tops]), stroke="#ffffff", width=1.2, opacity=0.9)
        g0, g1 = math.floor(x0 / 13), math.floor((x0 + w) / 13)
        for n in range(g0, g1 + 1):
            lx = n * 13 + 13 * _hash(n, 51) - x0
            if _hash(n, 52) > 0.7 and 3 < lx < w - 3:
                _sparkle(s, lx, y0 + 1.5, 1.6, 0.9, "#e8fbff")
        if h <= 100:
            # thin slabs are ceilings: icicles hang from their underside
            slot = 13.0
            s.path(_line([(lx, bottom - 1.5 - 1.2 * abs(math.sin((x0 + lx) * 0.2))) for lx in _samples(w, 3.0)]), stroke="#bfe6ff", width=1.6, opacity=0.6)
            for n in range(math.floor(x0 / slot), math.floor((x0 + w) / slot) + 1):
                lx = (n + 0.5) * slot - x0
                if _hash(n, 41) < 0.4 or not 4 < lx < w - 5.5:
                    continue
                ln = 7 + 12 * _hash(n, 42)
                _icicle(s, lx, bottom - ln - 0.5, ln, 3 + 2 * _hash(n, 43))
        return s

    def cave_sky(self) -> Svg:
        """Blue ice cave: translucent curtains, glowing crystals, stalactites."""
        s = Svg(960, 540)
        r = Rand(77)
        s.rect(0, 0, 960, 540, fill=s.linear(0, 0, 0, 540, [(0, "#121c36"), (0.45, "#1c2f57"), (1, "#0b1226")]))
        for cx, cy, rad, color in ((220, 300, 210, "#3fb8e8"), (700, 260, 190, "#7a6ae0"), (480, 470, 170, "#2fa0d0")):
            s.circle(cx, cy, rad, fill=s.radial(cx, cy, rad, [(0, color, 0.32), (1, color, 0)]))
        # ice curtains on the back wall
        for i in range(10):
            x = i * 100 + r.uniform(-30, 30)
            wcur = r.uniform(30, 64)
            top = r.uniform(30, 120)
            bottom = r.uniform(330, 470)
            pts = [(x, top)]
            for k in range(1, 7):
                pts.append((x + math.sin(k * 1.3 + i) * 6, top + (bottom - top) * k / 6))
            right = [(px + wcur * (0.7 + 0.3 * math.sin(j + i)), py) for j, (px, py) in enumerate(reversed(pts))]
            s.path(smooth_open(pts) + "L" + smooth_open(right)[1:] + "Z",
                   fill=s.linear(0, top, 0, bottom, [(0, "#7fb6e8", 0.05), (0.5, "#9fd2f6", 0.16), (1, "#9fd2f6", 0.02)]))
            s.path(smooth_open(pts), stroke="#bfe6ff", width=1.2, opacity=0.18)
        # distant crystal clusters
        for i in range(9):
            cx = 50 + i * 110 + r.uniform(-30, 30)
            cy = r.uniform(400, 470)
            color = r.choice(["#6fe6ff", "#a99aff", "#6fe6ff"])
            s.circle(cx, cy - 20, 44, fill=s.radial(cx, cy - 20, 44, [(0, color, 0.32), (1, color, 0)]))
            for k in range(r.choice([3, 4, 5])):
                a = math.radians(-90 + (k - 2) * 20 + r.uniform(-8, 8))
                ln = r.uniform(26, 70)
                tip = (cx + math.cos(a) * ln, cy + math.sin(a) * ln)
                nx, ny = -math.sin(a) * 7, math.cos(a) * 7
                s.polygon([(cx + nx, cy + ny), (tip[0] + nx * 0.7, tip[1] + ny * 0.7), (tip[0] + math.cos(a) * 9, tip[1] + math.sin(a) * 9),
                           (tip[0] - nx * 0.7, tip[1] - ny * 0.7), (cx - nx, cy - ny)],
                          fill=s.linear(cx, cy, tip[0], tip[1], [(0, shade(color, -0.55)), (0.7, shade(color, -0.1)), (1, "#e8fdff")]),
                          opacity=0.75)
        # stalactites and stalagmites
        for i in range(22):
            x = i * 46 + r.uniform(-12, 12)
            ln = r.uniform(30, 120)
            wd = r.uniform(14, 34)
            s.path(f"M{x - wd / 2:.1f} 0 Q{x - wd * 0.2:.1f} {ln * 0.6:.1f} {x:.1f} {ln:.1f} Q{x + wd * 0.25:.1f} {ln * 0.55:.1f} {x + wd / 2:.1f} 0 Z",
                   fill=s.linear(x - wd / 2, 0, x + wd / 2, 0, [(0, "#3a5a90"), (0.4, "#5a86c0"), (1, "#1a2a50")]))
            s.path(f"M{x - wd * 0.3:.1f} 2 Q{x - wd * 0.15:.1f} {ln * 0.5:.1f} {x - 1:.1f} {ln * 0.9:.1f}", stroke="#bfe6ff", width=1.4, opacity=0.4)
        for i in range(14):
            x = i * 72 + r.uniform(-20, 20)
            ln = r.uniform(30, 80)
            wd = r.uniform(30, 60)
            s.path(f"M{x - wd / 2:.1f} 540 Q{x - wd * 0.15:.1f} {540 - ln * 0.7:.1f} {x:.1f} {540 - ln:.1f} Q{x + wd * 0.2:.1f} {540 - ln * 0.6:.1f} "
                   f"{x + wd / 2:.1f} 540 Z", fill=s.linear(0, 540 - ln, 0, 540, [(0, "#2a4478"), (1, "#0c1430")]))
        for _ in range(40):
            px, py = r.uniform(0, 960), r.uniform(60, 500)
            if r.next() < 0.25:
                _sparkle(s, px, py, r.uniform(2, 4), 0.6, "#dff8ff")
            else:
                s.circle(px, py, r.uniform(0.8, 1.8), fill="#bfeaff", opacity=r.uniform(0.3, 0.7))
        return s

    # ------------------------------------------------------------------ blocks and platforms
    def _frost_strip(self, s: Svg, x0: float, x1: float, y: float, seed: int, thick: float = 3.2) -> None:
        """Thin lumpy snow strip with tiny drips, kept inside the art bounds."""
        r = Rand(seed)
        xs = _samples(x1 - x0, 2.5)
        tops = [(x0 + lx, y + 0.3 * math.sin(lx * 0.5)) for lx in xs]
        lows = [(x0 + lx, y + thick + 1.1 * math.sin(lx * 0.42 + seed) + 0.7 * math.sin(lx * 1.3)) for lx in reversed(xs)]
        s.path(_poly(tops + lows), fill=s.linear(0, y, 0, y + thick + 2, [(0, "#ffffff"), (1, "#d2e2f1")]))
        s.path(_line(list(reversed(lows))), stroke=SNOW_LINE, width=0.6, opacity=0.8)
        for _ in range(max(1, int((x1 - x0) / 14))):
            dx = r.uniform(x0 + 3, x1 - 3)
            s.path(blob(dx, y + thick + 0.6, 1.2, 1.8, 0.05, seed=dx), fill="#eef6fc")

    def block(self, kind: str, w: float, h: float) -> Svg:
        s = Svg(w, h)
        if kind in ("question", "used"):
            used = kind == "used"
            if used:
                face = s.linear(0, 0, 0, h, [(0, "#d6dfe9"), (0.5, "#aebcd0"), (1, "#7f8fa8")])
            else:
                face = s.linear(0, 0, w * 0.6, h, [(0, "#f2fdff"), (0.4, "#a9e4fa"), (0.75, "#5cc0ee"), (1, "#3194d2")])
            s.path(rounded_rect_path(0.6, 0.6, w - 1.2, h - 1.2, 4.5), fill=face, stroke=INK, width=1.3)
            ix, iy = w * 0.2, h * 0.22
            inner = [(ix, iy), (w - ix, iy), (w - ix, h - iy), (ix, h - iy)]
            outer = [(2.4, 2.4), (w - 2.4, 2.4), (w - 2.4, h - 2.4), (2.4, h - 2.4)]
            # cut facets: lit top-left bevels, shaded bottom-right bevels
            s.polygon([outer[0], outer[1], inner[1], inner[0]], fill="#ffffff", opacity=0.32 if not used else 0.22)
            s.polygon([outer[0], inner[0], inner[3], outer[3]], fill="#ffffff", opacity=0.18 if not used else 0.12)
            s.polygon([outer[3], inner[3], inner[2], outer[2]], fill="#0e3a6a" if not used else "#3a4660", opacity=0.22)
            s.polygon([outer[1], outer[2], inner[2], inner[1]], fill="#0e3a6a" if not used else "#3a4660", opacity=0.14)
            for a, b in zip(outer, inner):
                s.line(a[0], a[1], b[0], b[1], "#ffffff", 0.7, 0.55)
            if not used:
                cx, cy = w / 2, h / 2 + 0.5
                rad = min(w, h) * 0.36
                s.circle(cx, cy, rad * 1.25, fill=s.radial(cx, cy, rad * 1.25, [(0, "#fff3c0", 0.95), (0.5, GLOW, 0.5), (1, GLOW, 0)]))
                s.polygon(star_points(cx, cy, rad, rad * 0.3, 4), fill=s.linear(cx - rad, cy - rad, cx + rad, cy + rad,
                                                                                [(0, "#fffbe6"), (0.5, "#ffd76a"), (1, "#e8952a")]),
                          stroke="#9a5a12", width=0.8)
                for k in range(4):
                    a = math.radians(45 + k * 90)
                    s.circle(cx + math.cos(a) * rad * 0.62, cy + math.sin(a) * rad * 0.62, 0.9, fill="#fff3c0")
                _sparkle(s, w * 0.26, h * 0.3, 2.4, 0.95)
            else:
                cx, cy = w / 2, h / 2 + 0.5
                for k in range(3):
                    a = math.radians(k * 60)
                    d = min(w, h) * 0.2
                    s.line(cx - math.cos(a) * d, cy - math.sin(a) * d, cx + math.cos(a) * d, cy + math.sin(a) * d, "#5f6f88", 1.2, 0.7)
                s.circle(cx, cy, 1.6, fill="#5f6f88", opacity=0.8)
            self._frost_strip(s, 2.0, w - 2.0, 1.4, int(w * 3 + h), 2.6)
        elif kind == "brick":
            s.path(rounded_rect_path(0.6, 0.6, w - 1.2, h - 1.2, 3), fill="#e4eff8", stroke=INK, width=1.2)
            rows = 2
            rh = (h - 2) / rows
            for row in range(rows):
                y = 1 + row * rh
                x = -(0 if row % 2 == 0 else 10)
                while x < w:
                    bx0, bx1 = max(1.4, x + 1.1), min(w - 1.4, x + 20 - 1.1)
                    if bx1 > bx0 + 2:
                        s.path(rounded_rect_path(bx0, y + 1.0, bx1 - bx0, rh - 2.0, 1.8),
                               fill=s.linear(0, y, 0, y + rh, [(0, "#dcf5ff"), (0.45, "#9ad9f6"), (1, "#57ade0")]), stroke="#2c74aa", width=0.7)
                        s.line(bx0 + 1.2, y + 2.1, bx1 - 1.2, y + 2.1, "#ffffff", 0.9, 0.8)
                        k = int(x + row * 7) % 3
                        if k == 0 and bx1 - bx0 > 8:
                            s.polygon([(bx0 + 3, y + rh - 2.4), (bx0 + 5.5, y + 2.6), (bx0 + 7, y + 2.6), (bx0 + 4.5, y + rh - 2.4)], fill="#ffffff", opacity=0.45)
                        elif k == 1 and bx1 - bx0 > 10:
                            mx = (bx0 + bx1) / 2
                            s.path(f"M{mx:.1f} {y + 2.6:.1f} L{mx + 1.6:.1f} {y + rh * 0.5:.1f} L{mx - 0.6:.1f} {y + rh - 2.2:.1f}", stroke="#ffffff",
                                   width=0.6, opacity=0.8)
                    x += 20
            self._frost_strip(s, 1.6, w - 1.6, 1.0, int(w * 5 + h), 2.4)
        return s

    def platform(self, kind: str, w: float, h: float, style: str = "") -> Svg:
        if kind == "ledge":
            if "ice" in style:
                return self._ice_ledge(w, h)
            return self.terrain("terrain", w, h, int(w * 7 + h), True, True)
        s = Svg(w, h + 10)
        if kind == "moving":
            # wooden sled: frosted plank deck on curled steel runners
            deck = h - 4.5
            for sx in (14.0, w / 2, w - 14.0):
                s.rect(sx - 2, deck - 1, 4, 7, fill="#6f7f94", stroke=INK, width=0.8)
            runner = (f"M5 {deck - 2:.1f} Q1 {h + 6:.1f} 12 {h + 6:.1f} L{w - 12:.1f} {h + 6:.1f} Q{w - 1:.1f} {h + 6:.1f} {w - 5:.1f} {deck - 2:.1f}")
            s.path(runner, stroke=INK, width=3.6)
            s.path(runner, stroke="#c9d8e8", width=2.0)
            s.path(f"M12 {h + 5.3:.1f} L{w - 12:.1f} {h + 5.3:.1f}", stroke="#ffffff", width=0.7, opacity=0.8)
            s.path(rounded_rect_path(0.8, 1.2, w - 1.6, deck, 3.5), fill=s.linear(0, 1, 0, deck, [(0, WOOD_LIGHT), (0.55, WOOD), (1, WOOD_DARK)]),
                   stroke=INK, width=1.2)
            for x in range(16, int(w) - 6, 16):
                s.line(x, 3.5, x, deck - 0.5, "#5a3824", 1.0, 0.7)
                s.circle(x - 3, deck - 3, 0.9, fill="#3a2a22")
            s.line(3, deck - 1.6, w - 3, deck - 1.6, "#4a2e1c", 1.0, 0.5)
            self._frost_strip(s, 2.0, w - 2.0, 0.6, int(w * 11), 3.0)
        elif kind == "crumble":
            s = Svg(w, h + 6)
            r = Rand(int(w * 3 + h))
            s.path(rounded_rect_path(0.6, 0.6, w - 1.2, h - 1.2, 3.5),
                   fill=s.linear(0, 0, 0, h, [(0, "#f6fafd"), (0.45, "#d7e6f3"), (0.8, "#a9c6e2"), (1, "#86b6dc")]), stroke=INK, width=1.2)
            for _ in range(int(w / 3)):
                s.circle(r.uniform(3, w - 3), r.uniform(3, h - 4), r.uniform(0.4, 1.0), fill=r.choice(["#ffffff", "#b6cce4"]), opacity=0.8)
            s.path(f"M2 {h * 0.72:.1f} Q{w / 2:.1f} {h * 0.62:.1f} {w - 2:.1f} {h * 0.72:.1f} L{w - 2:.1f} {h - 2:.1f} L2 {h - 2:.1f} Z",
                   fill="#7cc8f0", opacity=0.45)
            for _ in range(3):
                x = r.uniform(8, w - 8)
                pts = [(x, 1.5), (x + r.uniform(-4, 4), h * 0.4), (x + r.uniform(-6, 6), h * 0.7), (x + r.uniform(-4, 4), h - 1.5)]
                s.path(_line(pts), stroke="#2a4a78", width=1.3)
                s.path(_line([(px + 0.9, py) for px, py in pts]), stroke="#ffffff", width=0.6, opacity=0.8)
                bx, by = pts[1]
                s.path(_line([(bx, by), (bx + r.uniform(4, 8), by + r.uniform(-3, 3))]), stroke="#2a4a78", width=0.9)
            for x in range(7, int(w) - 4, 11):
                _icicle(s, x, h - 1.5, 3 + (x * 7 % 5), 2.4)
        elif kind == "semisolid":
            # rope-bridge planks with frost
            s.path(rounded_rect_path(0.6, 1.0, w - 1.2, min(h, 8), 2.5), fill=s.linear(0, 0, 0, 9, [(0, WOOD_LIGHT), (1, WOOD_DARK)]), stroke=INK, width=1.1)
            for x in range(10, int(w) - 4, 10):
                s.line(x, 1.5, x, min(h, 8) + 0.5, "#4a2e1c", 0.9, 0.7)
            s.path(f"M2 {min(h, 8) + 2:.1f} Q{w / 2:.1f} {min(h, 8) + 7:.1f} {w - 2:.1f} {min(h, 8) + 2:.1f}", stroke="#c8a676", width=1.6)
            for x in range(14, int(w), 28):
                s.line(x, 8, x - 4, h + 8, "#5a3824", 2.2)
            self._frost_strip(s, 1.5, w - 1.5, 0.4, int(w * 13), 2.4)
        elif kind == "spring":
            s.path(rounded_rect_path(w * 0.15, h - 4, w * 0.7, 4, 1.5), fill=s.linear(0, h - 4, 0, h, [(0, WOOD), (1, WOOD_DARK)]),
                   stroke=INK, width=1.0)
            coil = [(w / 2 + (w * 0.22 if k % 2 else -w * 0.22), h * 0.42 + (h * 0.54) * k / 6) for k in range(7)]
            s.path(_line(coil), stroke=INK, width=2.6)
            s.path(_line(coil), stroke="#c9d8e8", width=1.4)
            s.path(blob(w / 2, h * 0.3, w / 2, h * 0.28, 0.04, seed=3, squash_top=1.2),
                   fill=s.radial(w * 0.38, h * 0.2, w * 0.7, [(0, "#ffffff"), (0.55, "#bfe6fa"), (1, "#4aa6dc")]), stroke=INK, width=1.2)
            for k in range(4):
                _sparkle(s, w * (0.25 + k * 0.17), h * (0.2 + 0.08 * (k % 2)), 1.8)
        else:  # conveyor / switch fallbacks: frosted steel capsule
            s.path(rounded_rect_path(0.6, 0.6, w - 1.2, h - 1.2, h / 2), fill=s.linear(0, 0, 0, h, [(0, "#c9d8e8"), (1, "#6f829c")]),
                   stroke=INK, width=1.2)
            self._frost_strip(s, h / 2, w - h / 2, 0.8, int(w * 17), 2.0)
        return s

    def _ice_ledge(self, w: float, h: float) -> Svg:
        """Floating slab of clear ice (always a slippery surface): glossy top,
        faceted translucent body, icicles below."""
        hr = self.terrain_headroom
        s = Svg(w, h + hr + 13)
        y0, y1 = hr, hr + h
        r = Rand(int(w * 13 + h))
        bottom = [(w - 2, y1 - 1)]
        x = w - 6.0
        while x > 6:
            bottom.append((x, y1 + r.uniform(-1.5, 2.5)))
            x -= r.uniform(7, 12)
        bottom.append((2, y1 - 1))
        outline = [(1.2, y0 + 3.5), (3.5, y0 - 0.3), (w - 3.5, y0 - 0.3), (w - 1.2, y0 + 3.5)] + bottom
        s.path(_line([(px, py + 2.5) for px, py in bottom]), stroke="#0d2a4a", width=3.5, opacity=0.2)
        s.path(_poly(outline), fill=s.linear(0, y0, 0, y1 + 2, [(0, ICE_HI), (0.18, ICE_TOP), (0.55, ICE), (1, ICE_DEEP)]))
        # facets
        for _ in range(int(w / 22) + 1):
            fx = r.uniform(8, w - 14)
            fw = r.uniform(6, 12)
            s.polygon([(fx, y0 + 6), (fx + fw, y0 + 6), (fx + fw - 4, y1 - 1), (fx - 6, y1 - 1)], fill=r.choice(["#ffffff", "#1f6fae"]), opacity=0.16)
        for _ in range(2):
            fx = r.uniform(10, w - 22)
            s.polygon([(fx, y0 + 1.5), (fx + 5, y0 + 1.5), (fx - 1, y1 - 3), (fx - 6, y1 - 3)], fill="#ffffff", opacity=0.4)
        s.path(_poly(outline), stroke=ICE_LINE, width=1.2)
        s.path(f"M3.5 {y0 + 1.1:.1f} L{w - 3.5:.1f} {y0 + 1.1:.1f}", stroke="#ffffff", width=1.5, opacity=0.95)
        s.path(f"M6 {y0 + 4:.1f} L{w * 0.45:.1f} {y0 + 4:.1f}", stroke="#ffffff", width=0.8, opacity=0.55)
        for (px, py) in bottom[1:-1]:
            if r.next() < 0.75:
                ln = r.uniform(4, 12)
                _icicle(s, px, py - 1.2, ln, r.uniform(2.4, 4))
        for ex in (6.0, w - 6.0):
            s.path(blob(ex, y0 - 0.6, 6.5, 3.2, 0.15, seed=ex, squash_top=1.2), fill=s.linear(0, y0 - 4, 0, y0 + 3, [(0, "#ffffff"), (1, SNOW_SHADE)]),
                   stroke=SNOW_LINE, width=0.7)
        return s

    def pipe(self, w: float, h: float, warp: bool) -> Svg:
        """Frosted steel conduit with a snowy rim and icicles."""
        s = Svg(w, h)
        metal = s.linear(4, 0, w - 4, 0, [(0, "#3d5673"), (0.16, "#8ea8c4"), (0.3, "#dbe7f2"), (0.5, "#7b95b2"), (1, "#28394f")])
        s.path(rounded_rect_path(4, 10, w - 8, h - 10, 2), fill=metal, stroke=INK, width=1.3)
        r = Rand(int(w * 7 + h))
        for _ in range(3):
            fx, fy = r.uniform(10, w - 12), r.uniform(20, max(21, h - 8))
            s.path(blob(fx, fy, r.uniform(3, 6), r.uniform(2, 3.5), 0.3, seed=fx), fill="#f2f8fd", opacity=0.55)
        if h > 30:
            s.rect(4.5, h - 9, w - 9, 4, fill="#5a7393", stroke=INK, width=0.8)
            for bx in range(9, int(w) - 6, 9):
                s.circle(bx, h - 7, 0.9, fill="#c9d8e8")
        rim = s.linear(0.8, 0, w - 0.8, 0, [(0, "#46617f"), (0.22, "#b4c9de"), (0.36, "#f0f7fc"), (0.6, "#88a2be"), (1, "#2c405a")])
        s.path(rounded_rect_path(0.8, 0.8, w - 1.6, 14, 4), fill=rim, stroke=INK, width=1.3)
        for bx in (5.5, w - 5.5):
            s.circle(bx, 8, 1.2, fill="#2c405a", stroke="#c9d8e8", width=0.5)
        self._frost_strip(s, 2.5, w - 2.5, 1.0, int(w * 3 + h), 3.0)
        for k, ix in enumerate((9.0, w * 0.4, w * 0.62, w - 10)):
            _icicle(s, ix, 14.2, 4 + (k * 3 % 5) + (2 if k == 1 else 0), 2.6)
        if warp:
            cy = 27 if h > 36 else h * 0.68
            s.circle(w / 2, cy, 9, fill=s.radial(w / 2, cy, 9, [(0, "#e8fbff", 0.95), (1, "#73e6ff", 0)]))
            s.polygon([(w / 2 - 5, cy - 3.2), (w / 2 + 5, cy - 3.2), (w / 2, cy + 4)], fill="#ffffff", stroke="#1f6fae", width=0.6)
        return s

    # ------------------------------------------------------------------ props
    def _pine(self, seed: int, height: float, tiers: int) -> Svg:
        """Snow-laden fir: drooping needle tiers, clumps of snow resting on the
        branches (heavier on the lit left side), a capped tip."""
        r = Rand(seed)
        wdt = height * 0.62
        s = Svg(wdt, height)
        cx = wdt / 2
        base = height
        s.path(rounded_rect_path(cx - 5, base - 34, 10, 34, 2), fill=s.linear(cx - 5, 0, cx + 5, 0, [(0, WOOD_LIGHT), (1, WOOD_DARK)]),
               stroke=INK, width=1.2)
        span = base - 24 - 3
        for i in range(tiers):
            k = i / tiers
            by = base - 22 - span * k * 0.93
            th = span / tiers * 1.85
            ty = by - th
            half = wdt * 0.48 * (1 - k * 0.72)
            droop = th * 0.12
            ltip, rtip = (cx - half, by - droop), (cx + half, by - droop * 0.6)
            teeth = []
            n = max(4, int(half / 5))
            for j in range(n + 1):
                t = j / n
                tx = rtip[0] + (ltip[0] - rtip[0]) * t
                sag = math.sin(math.pi * t) * th * 0.1
                teeth.append((tx + r.uniform(-1, 1), by + sag + (0 if j % 2 else -th * 0.12)))
            outline = ([(cx, ty)] + [(cx + half * 0.42, ty + th * 0.45), rtip] + teeth[1:-1] + [ltip, (cx - half * 0.42, ty + th * 0.45)])
            fill = s.radial(cx - half * 0.5, ty + th * 0.3, half * 2.0, [(0, PINE_LIGHT), (0.55, PINE), (1, PINE_DARK)])
            s.path(smooth_closed(outline, 0.35), fill=fill, stroke=PINE_LINE, width=1.1)
            for tip in (ltip, rtip, teeth[n // 3], teeth[2 * n // 3]):
                s.path(smooth_open([(cx, ty + th * 0.35), ((cx + tip[0]) / 2, (ty + th * 0.35 + tip[1]) / 2 + th * 0.06), tip]),
                       stroke=PINE_DARK, width=1.0, opacity=0.45)
            # snow mantles lying on the upper edges of the tier (thicker toward the tips)
            lit = s.linear(0, ty - 2, 0, by, [(0, "#ffffff"), (0.7, "#eef5fb"), (1, "#d3e2f1")])
            dim = s.linear(0, ty - 2, 0, by, [(0, "#e4edf8"), (1, SNOW_SHADE)])
            s.path(_edge_snow((cx, ty), ltip, th * 0.2, 1, seed + i), fill=lit, stroke=SNOW_LINE, width=0.8)
            s.path(_edge_snow((cx, ty), rtip, th * 0.13, -1, seed + i + 5), fill=dim, stroke=SNOW_LINE, width=0.8)
            s.path(smooth_open([(cx - half * 0.08, ty + th * 0.12), (cx - half * 0.45, ty + th * 0.42), (cx - half * 0.8, by - th * 0.2)]),
                   stroke="#ffffff", width=1.3, opacity=0.9)
        s.path(blob(cx, 7, 4.5, 6, 0.1, seed=seed), fill="#ffffff", stroke=SNOW_LINE, width=0.8)
        for _ in range(5):
            _sparkle(s, r.uniform(cx - wdt * 0.3, cx + wdt * 0.2), r.uniform(height * 0.15, height * 0.8), r.uniform(1.6, 2.6))
        return s

    def _snow_mound(self, seed: int) -> Svg:
        r = Rand(seed)
        s = Svg(92, 40)
        s.ellipse(47, 38, 42, 3, fill="#6f8db4", opacity=0.3)
        if seed % 2:
            s.path("M62 24 L70 5 M67 12 L75 8 M65 17 L58 11", stroke="#4a2e1c", width=2.4)
            s.path("M62 24 L70 5 M67 12 L75 8 M65 17 L58 11", stroke="#7a5236", width=1.2)
        d = "M5 39 C8 26 22 15 40 13 C52 11.5 60 15 66 19 C74 18 84 24 88 39 Z"
        s.path(d, fill=s.radial(34, 15, 58, [(0, "#ffffff"), (0.45, "#f1f7fc"), (0.8, "#cddcee"), (1, "#a9c0dc")]), stroke=SNOW_LINE, width=1.1)
        s.path("M58 36 C66 33 74 30 80 34 C82 36 84 38 85 39 L58 39 Z", fill="#9fb8d8", opacity=0.45)
        s.path("M14 30 C20 22 30 17 40 16", stroke="#ffffff", width=2.2, opacity=0.9)
        if not seed % 2:
            s.path(blob(72, 32, 9, 6.5, 0.12, seed=seed + 5), fill=s.linear(0, 25, 0, 39, [(0, "#9aaccb"), (1, "#53658a")]), stroke=ROCK_LINE, width=1.0)
            s.path(blob(71, 26.5, 7, 2.6, 0.2, seed=seed + 6, squash_top=1.3), fill="#ffffff", stroke=SNOW_LINE, width=0.6)
        for _ in range(5):
            _sparkle(s, r.uniform(16, 70), r.uniform(18, 32), r.uniform(1.4, 2.4))
        return s

    def _crystals(self, seed: int) -> Svg:
        r = Rand(seed)
        s = Svg(56, 58)
        s.circle(28, 34, 26, fill=s.radial(28, 34, 26, [(0, "#9feaff", 0.55), (1, "#9feaff", 0)]))
        shards = [(-24, 30, 7), (-6, 46, 8.5), (14, 36, 7), (32, 22, 5.5), (-40, 20, 5)]
        for ang, ln, wd in shards[: 3 + seed % 3]:
            a = math.radians(-90 + ang + r.uniform(-5, 5))
            bx, by = 28 + math.cos(a + math.pi / 2) * 2, 52
            tip = (bx + math.cos(a) * ln, by + math.sin(a) * ln)
            nx, ny = -math.sin(a) * wd / 2, math.cos(a) * wd / 2
            body = [(bx + nx, by + ny), (tip[0] + nx, tip[1] + ny), (tip[0] + math.cos(a) * wd * 0.8, tip[1] + math.sin(a) * wd * 0.8),
                    (tip[0] - nx, tip[1] - ny), (bx - nx, by - ny)]
            s.polygon(body, fill=s.linear(bx - nx, by - ny, bx + nx, by + ny, [(0, "#2f8fd0"), (0.45, "#9fe6ff"), (1, "#e8fbff")]),
                      stroke=ICE_LINE, width=0.9)
            s.polygon([(bx + nx * 0.2, by + ny * 0.2), (tip[0] + nx * 0.2, tip[1] + ny * 0.2), (tip[0] + math.cos(a) * wd * 0.8, tip[1] + math.sin(a) * wd * 0.8),
                       (tip[0] + nx * 0.7, tip[1] + ny * 0.7), (bx + nx * 0.7, by + ny * 0.7)], fill="#ffffff", opacity=0.45)
        s.path(blob(28, 53, 22, 5, 0.12, seed=seed, squash_top=1.3), fill=s.linear(0, 48, 0, 58, [(0, "#ffffff"), (1, SNOW_SHADE)]),
               stroke=SNOW_LINE, width=0.8)
        _sparkle(s, 20, 18, 3.2)
        _sparkle(s, 37, 30, 2.2)
        return s

    def _rock_prop(self, seed: int) -> Svg:
        s = Svg(62, 40)
        s.path(blob(31, 26, 27, 14, 0.12, seed=seed, squash_top=1.15),
               fill=s.radial(22, 16, 34, [(0, "#b9c7da"), (0.5, "#8293ae"), (1, "#4f5f7f")]), stroke=ROCK_LINE, width=1.2)
        s.path(smooth_open([(14, 30), (25, 24), (33, 30)]), stroke="#3e4b66", width=1.1, opacity=0.7)
        s.path(blob(27, 14, 20, 5.5, 0.18, seed=seed + 1, squash_top=1.3), fill=s.linear(0, 8, 0, 19, [(0, "#ffffff"), (1, SNOW_SHADE)]),
               stroke=SNOW_LINE, width=0.8)
        s.path(blob(45, 18, 6, 2.4, 0.2, seed=seed + 2), fill="#ffffff")
        _icicle(s, 12, 26, 5, 2.4)
        _sparkle(s, 20, 11, 2.0)
        return s

    def _bush_frost(self, seed: int) -> Svg:
        r = Rand(seed)
        s = Svg(84, 48)
        for cx, cy, rad in ((24, 32, 18), (44, 27, 22), (63, 33, 17)):
            s.path(blob(cx, cy, rad, rad * 0.8, 0.1, seed=cx + seed),
                   fill=s.radial(cx - rad * 0.3, cy - rad * 0.5, rad * 1.5, [(0, "#5e9c88"), (0.6, "#2f6a63"), (1, "#1c4a4c")]), stroke=PINE_LINE, width=1.0)
        for cx, cy, rad in ((22, 20, 13), (44, 13, 17), (64, 21, 12)):
            s.path(blob(cx, cy, rad, rad * 0.42, 0.18, seed=cx * 3 + seed, squash_top=1.3),
                   fill=s.linear(0, cy - rad * 0.4, 0, cy + rad * 0.4, [(0, "#ffffff"), (1, SNOW_SHADE)]), stroke=SNOW_LINE, width=0.7)
        if seed % 2:
            for _ in range(7):
                bx, by = r.uniform(14, 72), r.uniform(26, 40)
                s.circle(bx, by, 2.3, fill=s.radial(bx - 0.7, by - 0.7, 2.6, [(0, "#ff9aa0"), (1, "#c0283a")]), stroke="#5a1020", width=0.5)
        for _ in range(3):
            _sparkle(s, r.uniform(16, 70), r.uniform(8, 20), 2.0)
        return s

    def _lantern(self) -> Svg:
        s = Svg(40, 96)
        s.circle(29, 46, 22, fill=s.radial(29, 46, 22, [(0, "#fff0b8", 0.75), (0.5, GLOW, 0.3), (1, GLOW, 0)]))
        s.path(rounded_rect_path(9, 18, 7, 78, 2), fill=s.linear(9, 0, 16, 0, [(0, WOOD_LIGHT), (1, WOOD_DARK)]), stroke=INK, width=1.1)
        s.path("M12.5 24 L30 24 L30 30", stroke=INK, width=2.4)
        s.path("M12.5 24 L30 24 L30 30", stroke="#4a3a34", width=1.2)
        s.path(smooth_closed([(24, 33), (34, 33), (35.5, 46), (33.5, 56), (24.5, 56), (22.5, 46)], 0.4),
               fill=s.radial(29, 45, 11, [(0, "#ffffff"), (0.35, "#ffe27a"), (1, GLOW_DEEP)]), stroke=INK, width=1.0)
        s.path("M23 33 L35 33 L33 29 L25 29 Z", fill="#3a3a48", stroke=INK, width=0.9)
        s.rect(23.5, 55.5, 11, 2.8, fill="#3a3a48", stroke=INK, width=0.8, rx=1)
        s.path(blob(29, 28.8, 6, 2.2, 0.15, seed=2), fill="#ffffff", stroke=SNOW_LINE, width=0.6)
        s.path(blob(12.5, 17.5, 5.5, 2.6, 0.15, seed=4, squash_top=1.2), fill="#ffffff", stroke=SNOW_LINE, width=0.7)
        s.path(blob(29, 44, 2.2, 3.6, 0.1, seed=1), fill="#ffffff", opacity=0.9)
        _icicle(s, 18, 24.8, 4, 1.8)
        return s

    def _hut(self) -> Svg:
        """Log cabin with a heavy snow roof, warm window and chimney smoke."""
        s = Svg(176, 160)
        # chimney smoke
        for k in range(5):
            px, py, pr = 128 + k * 7.5, 26 - k * 6.5, 5 + k * 2.4
            s.circle(px, py, pr, fill=s.radial(px - pr * 0.3, py - pr * 0.3, pr * 1.2, [(0, "#ffffff", 0.75 - k * 0.12), (1, "#e6eef8", 0)]))
        s.path(rounded_rect_path(116, 30, 16, 40, 2), fill=s.linear(116, 0, 132, 0, [(0, "#9aa4b8"), (1, "#5a6480")]), stroke=INK, width=1.2)
        for y in (38, 47, 56):
            s.line(117, y, 131, y, "#4a5068", 0.8, 0.7)
        s.path(blob(124, 30, 10, 3.6, 0.15, seed=3, squash_top=1.3), fill="#ffffff", stroke=SNOW_LINE, width=0.7)
        # walls of stacked logs
        for i in range(7):
            y = 86 + i * 10.5
            s.path(rounded_rect_path(26, y, 124, 10.5, 5), fill=s.linear(0, y, 0, y + 10.5, [(0, WOOD_LIGHT), (0.6, WOOD), (1, WOOD_DARK)]),
                   stroke=INK, width=0.9)
            for ex in (26, 150):
                s.circle(ex, y + 5.25, 5.2, fill=s.radial(ex - 1, y + 4, 6, [(0, "#e2b88a"), (1, "#a8744a")]), stroke=INK, width=0.8)
                s.circle(ex, y + 5.25, 2.4, stroke="#8a5a36", width=0.6)
        s.polygon([(30, 88), (88, 46), (146, 88)], fill=s.linear(0, 46, 0, 88, [(0, "#8a5a3a"), (1, "#6a4228")]), stroke=INK, width=1.0)
        for x in range(42, 140, 9):
            s.line(x, 88, x, 88 - max(0.0, 42 - abs(x - 88) * 0.72), "#4a2e1c", 0.8, 0.6)
        # door and window
        s.path(rounded_rect_path(48, 110, 26, 48, 3), fill=s.linear(48, 0, 74, 0, [(0, "#7a4a2c"), (1, "#4a2a18")]), stroke=INK, width=1.1)
        for x in (56, 64):
            s.line(x, 112, x, 156, "#3a2214", 0.8)
        s.circle(69, 135, 1.6, fill="#ffd27a", stroke=INK, width=0.5)
        s.circle(112, 124, 30, fill=s.radial(112, 124, 30, [(0, "#fff0b8", 0.55), (1, GLOW, 0)]))
        s.path(rounded_rect_path(100, 110, 24, 22, 2), fill=s.radial(112, 121, 16, [(0, "#fff6d0"), (0.5, "#ffd27a"), (1, GLOW_DEEP)]),
               stroke=INK, width=1.1)
        s.line(112, 110, 112, 132, "#5a3824", 1.6)
        s.line(100, 121, 124, 121, "#5a3824", 1.6)
        s.path(blob(112, 132.5, 15, 2.6, 0.15, seed=7), fill="#ffffff", stroke=SNOW_LINE, width=0.6)
        # heavy snow roof with overhanging lip and icicles
        roof = [(4, 92), (88, 34), (172, 92), (166, 99), (88, 46), (10, 99)]
        s.path(_poly(roof), fill="#5a3824", stroke=INK, width=1.2)
        snow = [(1, 92), (20, 76), (88, 26), (156, 76), (175, 92), (170, 97), (156, 92), (140, 95), (124, 88), (108, 92), (88, 86),
                (70, 92), (52, 88), (36, 95), (18, 92), (6, 97)]
        s.path(smooth_closed(snow, 0.4), fill=s.linear(0, 26, 0, 98, [(0, "#ffffff"), (0.6, "#eef5fb"), (1, "#bfd2e8")]), stroke=SNOW_LINE, width=1.1)
        s.path(smooth_closed([(88, 30), (150, 74), (166, 88), (148, 86), (88, 44)], 0.4), fill=SNOW_SHADE, opacity=0.55)
        s.path(smooth_open([(14, 86), (50, 60), (84, 36)]), stroke="#ffffff", width=2.2, opacity=0.9)
        for k, ix in enumerate((14, 30, 47, 63, 80, 98, 117, 133, 150, 164)):
            _icicle(s, ix, 92 + (k % 3), 5 + (k * 5 % 9), 2.8)
        s.path(blob(88, 157, 74, 4.5, 0.1, seed=11, squash_top=1.4), fill=s.linear(0, 152, 0, 160, [(0, "#ffffff"), (1, SNOW_SHADE)]),
               stroke=SNOW_LINE, width=0.8)
        return s

    def _fence(self) -> Svg:
        s = Svg(124, 42)
        posts = (8, 44, 80, 116)
        for i, x in enumerate(posts[:-1]):
            nx = posts[i + 1]
            for yy, sag in ((15, 5), (26, 4)):
                s.path(f"M{x:.1f} {yy:.1f} Q{(x + nx) / 2:.1f} {yy + sag:.1f} {nx:.1f} {yy:.1f}", stroke="#4a3424", width=2.2)
                s.path(f"M{x:.1f} {yy - 0.5:.1f} Q{(x + nx) / 2:.1f} {yy + sag - 0.5:.1f} {nx:.1f} {yy - 0.5:.1f}", stroke="#c8a676", width=0.9)
        for x in posts:
            s.path(rounded_rect_path(x - 3.5, 7, 7, 35, 2), fill=s.linear(x - 3.5, 0, x + 3.5, 0, [(0, WOOD_LIGHT), (1, WOOD_DARK)]), stroke=INK, width=1.0)
            s.path(blob(x, 6.5, 5.2, 3, 0.15, seed=x, squash_top=1.3), fill="#ffffff", stroke=SNOW_LINE, width=0.7)
        return s

    def props(self) -> dict[str, PropSpec]:
        return {
            "tree_pine": PropSpec(lambda: self._pine(3, 196, 5), (196 * 0.31, 196)),
            "tree_pine_b": PropSpec(lambda: self._pine(9, 156, 4), (156 * 0.31, 156)),
            "tree_pine_small": PropSpec(lambda: self._pine(15, 104, 3), (104 * 0.31, 104)),
            "snow_mound": PropSpec(lambda: self._snow_mound(2), (46, 39)),
            "snow_mound_b": PropSpec(lambda: self._snow_mound(5), (46, 39)),
            "crystal": PropSpec(lambda: self._crystals(4), (28, 56)),
            "crystal_b": PropSpec(lambda: self._crystals(7), (28, 56)),
            "rock": PropSpec(lambda: self._rock_prop(2), (31, 38)),
            "rock_b": PropSpec(lambda: self._rock_prop(8), (31, 38)),
            "bush_frost": PropSpec(lambda: self._bush_frost(5), (44, 46)),
            "bush_frost_b": PropSpec(lambda: self._bush_frost(12), (44, 46)),
            "lantern": PropSpec(self._lantern, (12.5, 96)),
            "hut": PropSpec(self._hut, (88, 158)),
            "fence": PropSpec(self._fence, (62, 42)),
        }

    def auto_decor(self, rng, surface_w: float) -> list[tuple[str, float, float, str]]:
        out = []
        x = rng.uniform(40, 120)
        hut = False
        while x < surface_w - 40:
            roll = rng.next()
            if roll < 0.27 and surface_w > 240:
                out.append((rng.choice(["tree_pine", "tree_pine_b", "tree_pine_small"]), x, rng.uniform(0.82, 1.05), "back"))
            elif roll < 0.43:
                out.append((rng.choice(["snow_mound", "snow_mound_b"]), x, rng.uniform(0.7, 1.0), "mid"))
            elif roll < 0.55:
                out.append((rng.choice(["bush_frost", "bush_frost_b"]), x, rng.uniform(0.75, 1.0), "back"))
            elif roll < 0.65:
                out.append((rng.choice(["crystal", "crystal_b"]), x, rng.uniform(0.6, 0.85), "mid"))
            elif roll < 0.73:
                out.append((rng.choice(["rock", "rock_b"]), x, rng.uniform(0.6, 0.9), "mid"))
            elif roll < 0.81:
                out.append(("lantern", x, rng.uniform(0.9, 1.0), "back"))
            elif roll < 0.88 and surface_w > 520 and not hut:
                out.append(("hut", x, rng.uniform(0.85, 1.0), "back"))
                hut = True
            elif roll < 0.94:
                out.append(("fence", x, 1.0, "back"))
            x += rng.uniform(110, 220)
        return out

    def weather(self) -> Weather:
        return Weather("snow", 0.75, ("soft", "soft", "soft", "sparkle"), wind=28.0)


ART_CLASS = FrozenPeaks
