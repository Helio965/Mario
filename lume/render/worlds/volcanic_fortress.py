"""Fortaleza Vulcânica: basalt bridges over lava, furnace halls and a burning citadel.

Identity: a smoky crimson-to-purple sky lit from below by an erupting volcano
and its ash plume; distant fortress silhouettes with chains, banners and lit
slit windows; hexagonal basalt column cliffs split by lava falls; dark basalt
terrain whose columns are capped by cooled crust plates with glowing magma
seams; iron-banded obsidian blocks with an ember rune, heat-cracked bricks,
furnace conduits, braziers, warning totems, steam vents and rising embers.

Light: the key light is the lava glow from below and the volcano (warm
orange); the fill is the cool purple of the smoky sky. Hazards are the only
white-hot elements, so lava always reads as danger while every walkable top
carries a pale crust highlight that reads as safe.
"""

from __future__ import annotations

import math
from typing import Optional, Sequence

from ..svg import Rand, Svg, blob, mix, rounded_rect_path, shade, smooth_closed, smooth_open, star_points
from .base import Layer, PropSpec, Weather, WorldArt

INK = "#1b0f15"
# basalt body: light facet → deep
BASALT_LIT, BASALT, BASALT_DARK, BASALT_DEEP = "#4d3a44", "#33252d", "#211820", "#120c11"
# cooled crust cap: highlight → underside
CRUST_HI, CRUST_TOP, CRUST, CRUST_LOW = "#c9a491", "#94776c", "#6b5452", "#463539"
# magma ramp: white-hot → dark red
MAGMA_WHITE, MAGMA_YELLOW, MAGMA_ORANGE, MAGMA_RED, MAGMA_DARK = "#fff4c4", "#ffc548", "#ff7d2c", "#d8391f", "#7a1810"
IRON_HI, IRON, IRON_DARK, IRON_DEEP = "#a9a7b4", "#6c6977", "#3e3b47", "#22202a"
OBSIDIAN_HI, OBSIDIAN, OBSIDIAN_DARK = "#5a4778", "#261b35", "#0e0914"
BANNER, BANNER_DARK = "#8e2230", "#4e1019"

COL = 26.0  # mean width of a basalt column (world units), world-aligned grid


def _hash01(i: int, salt: float = 0.0) -> float:
    """Stable pseudo-random value in [0, 1) for a world-aligned index."""
    v = math.sin(i * 127.1 + salt * 311.7) * 43758.5453
    return v - math.floor(v)


def _col_edge(k: int) -> float:
    return k * COL + (_hash01(k, 3.1) - 0.5) * 11.0


def _columns(start: float, end: float) -> list[tuple[int, float, float]]:
    """World-aligned basalt columns (index, left, right) covering [start, end]."""
    k = math.floor(start / COL) - 1
    out = []
    while _col_edge(k) < end + 1:
        out.append((k, _col_edge(k), _col_edge(k + 1)))
        k += 1
    return out


def _glow_line(s: Svg, d: str, width: float = 1.0, hot: bool = True, opacity: float = 1.0) -> None:
    """A glowing magma crack: wide soft glow, orange body and a white-hot core."""
    s.path(d, stroke=MAGMA_RED, width=width * 5.0, opacity=0.22 * opacity)
    s.path(d, stroke=MAGMA_ORANGE, width=width * 2.0, opacity=0.9 * opacity)
    if hot:
        s.path(d, stroke=MAGMA_YELLOW, width=width * 0.8, opacity=opacity)


def _halo(s: Svg, cx: float, cy: float, r: float, color: str = MAGMA_ORANGE, strength: float = 0.55) -> None:
    s.circle(cx, cy, r, fill=s.radial(cx, cy, r, [(0, color, strength), (0.45, color, strength * 0.35), (1, color, 0)]))


def _soft(s: Svg, cx: float, cy: float, rx: float, ry: float, color: str, alpha: float = 1.0, core: float = 0.0) -> None:
    """Soft-edged ellipse: radial falloff made elliptical by a scaled group."""
    with s.group(transform=f"translate({cx:.2f} {cy:.2f}) scale(1 {ry / rx:.4f})"):
        s.circle(0, 0, rx, fill=s.radial(0, 0, rx, [(0, color, alpha), (core, color, alpha), (1, color, 0)]))


def _flame(s: Svg, cx: float, base: float, w: float, h: float, seed: float = 0.0, tongues: int = 3) -> None:
    """Layered flame standing on ``base``: red tongues, orange body, white-hot root."""
    layers = (
        (1.0, [(0, MAGMA_RED, 0.25), (0.35, MAGMA_RED, 0.95), (1, MAGMA_ORANGE)]),
        (0.72, [(0, MAGMA_ORANGE, 0.5), (0.5, MAGMA_ORANGE), (1, MAGMA_YELLOW)]),
        (0.42, [(0, MAGMA_YELLOW, 0.6), (0.5, MAGMA_YELLOW), (1, MAGMA_WHITE)]),
    )
    for k, (scale, stops) in enumerate(layers):
        fw, fh = w * scale, h * scale
        pts = [(cx - fw * 0.5, base - fh * 0.12)]
        for i in range(tongues):
            tx = cx - fw * 0.5 + fw * (i + 0.5) / tongues + math.sin(seed + i * 2.1 + k) * fw * 0.06
            peak = fh * (0.62 + 0.38 * (1 - abs(i - (tongues - 1) / 2) / max(1, tongues / 2)))
            pts.append((tx - fw * 0.12, base - peak * 0.55))
            pts.append((tx + math.sin(seed * 1.7 + i) * fw * 0.08, base - peak))
            pts.append((tx + fw * 0.12, base - peak * 0.55))
        pts += [(cx + fw * 0.5, base - fh * 0.12), (cx + fw * 0.32, base + fh * 0.04), (cx - fw * 0.32, base + fh * 0.04)]
        s.path(smooth_closed(pts, 0.55), fill=s.linear(0, base - fh, 0, base, stops))


def _chain(s: Svg, pts: Sequence[tuple[float, float]], link: float = 4.0, color: str = IRON_DARK, width: float = 1.2,
           hi: Optional[str] = IRON) -> None:
    """Chain links along a polyline (alternating face-on ovals and edge-on bars)."""
    segs = [((ax, ay), (bx, by), math.hypot(bx - ax, by - ay)) for (ax, ay), (bx, by) in zip(pts, pts[1:])]
    if not segs:
        return
    total = sum(seg[2] for seg in segs)
    n = max(1, int(total / link))
    for i in range(n):
        d = (i + 0.5) * total / n
        for (ax, ay), (bx, by), ln in segs:  # the last segment absorbs rounding overflow
            if d <= ln:
                break
            d -= ln
        t = min(1.0, d / ln) if ln else 0.0
        x, y = ax + (bx - ax) * t, ay + (by - ay) * t
        ang = math.atan2(by - ay, bx - ax)
        ca, sa = math.cos(ang), math.sin(ang)
        if i % 2 == 0:
            rx, ry = link * 0.62, link * 0.36
            s.raw(f'<ellipse cx="{x:.2f}" cy="{y:.2f}" rx="{rx:.2f}" ry="{ry:.2f}" '
                  f'transform="rotate({math.degrees(ang):.1f} {x:.2f} {y:.2f})" fill="none" stroke="{color}" stroke-width="{width:.2f}"/>')
            if hi:  # glint on the upper rim of the link
                nx, ny = sa * ry * 0.55, -ca * ry * 0.55
                s.line(x - ca * rx * 0.45 + nx, y - sa * rx * 0.45 + ny, x + ca * rx * 0.2 + nx, y + sa * rx * 0.2 + ny, hi, width * 0.5, 0.7)
        else:
            s.line(x - ca * link * 0.55, y - sa * link * 0.55, x + ca * link * 0.55, y + sa * link * 0.55, color, width * 1.3)


def _sag(x1: float, y1: float, x2: float, y2: float, sag: float, n: int = 10) -> list[tuple[float, float]]:
    """Points of a hanging chain/rope between two anchors."""
    return [(x1 + (x2 - x1) * i / n, y1 + (y2 - y1) * i / n + sag * 4 * (i / n) * (1 - i / n)) for i in range(n + 1)]


class VolcanicFortress(WorldArt):
    id = "volcanic_fortress"
    name = "Fortaleza Vulcânica"
    accent = "#ff8a3d"
    terrain_headroom = 12.0
    ambient = (255, 232, 222)
    vignette = 0.36
    provisional = False

    # ------------------------------------------------------------------ sky
    def sky(self) -> Svg:
        s = Svg(960, 540)
        s.rect(0, 0, 960, 540, fill=s.linear(0, 0, 0, 540, [(0, "#0f0817"), (0.24, "#20102a"), (0.48, "#3d1531"),
                                                          (0.68, "#6a1f31"), (0.85, "#a3352d"), (1, "#cf5a2c")]))
        r = Rand(7)
        # soft smoke strata
        for cx, cy, rx, ry, color, a in ((300, 92, 480, 36, "#2b1230", 0.55), (420, 236, 520, 30, "#5a1d33", 0.4),
                                         (640, 318, 480, 24, "#8a2a30", 0.3)):
            _soft(s, cx, cy, rx, ry, color, a, 0.35)
        # horizon: the glow of the lava sea
        _soft(s, 480, 590, 620, 250, "#ff8a3a", 0.5, 0.0)
        # faint sparks in the upper sky
        for _ in range(40):
            x, y = r.uniform(0, 960), r.uniform(10, 300)
            s.circle(x, y, r.uniform(0.5, 1.3), fill=r.choice([MAGMA_YELLOW, "#ffb070", "#ffd8c0"]), opacity=r.uniform(0.25, 0.7))
        # secondary distant volcano (hazy, left)
        s.path("M-60 540 C40 470 130 380 186 330 Q198 320 212 324 Q236 336 276 396 C330 460 400 510 500 540 Z",
               fill=s.linear(0, 320, 0, 540, [(0, "#561d35"), (1, "#7a2834")]), opacity=0.8)
        _halo(s, 199, 326, 50, "#ff7a3a", 0.35)
        # main volcano: concave flanks, a jagged truncated rim and a crater lit from inside
        cx, cy = 690.0, 164.0
        _halo(s, cx, cy, 220, "#ff7a36", 0.45)
        s.path("M648 168 L654 154 L664 158 L673 149 L686 155 L697 147 L709 154 L720 149 L732 168 Z",
               fill=s.linear(0, 146, 0, 168, [(0, MAGMA_RED), (0.55, MAGMA_ORANGE), (1, MAGMA_YELLOW)]))
        s.path("M654 154 L664 158 L673 149 L686 155 L697 147 L709 154 L720 149", stroke=MAGMA_YELLOW, width=1.0, opacity=0.75)
        rim = "L640 172 L647 165 L652 168 L660 163 Q690 172 720 163 L728 168 L734 164 L741 171 L746 175"
        cone = f"M230 540 C420 528 560 380 630 176 L634 175 {rim} C800 380 960 528 1150 540 Z"
        s.path(cone, fill=s.radial(cx, cy + 12, 400, [(0, "#9a3a30"), (0.18, "#5e2030"), (0.42, "#36132a"), (1, "#45182c")]))
        s.path("M652 168.5 L660 163.5 Q690 172.5 720 163.5 L728 168.5", stroke=MAGMA_ORANGE, width=1.8, opacity=0.95)
        # gullies (shadowed) and sunlit ribs fading down the flanks
        for x0, sway, length, k in ((644, -0.42, 230, 0), (668, -0.16, 170, 1), (712, 0.2, 200, 2), (736, 0.46, 250, 3)):
            pts = [(x0 + sway * length * t * (0.6 + 0.4 * t) + math.sin(t * 5 + k) * 4, cy + 12 + length * t) for t in (0, 0.33, 0.66, 1)]
            fade = s.linear(0, cy + 12, 0, cy + 12 + length, [(0, "#14060f", 0.55), (1, "#14060f", 0)])
            s.path(smooth_open(pts), stroke=fade, width=5 - k * 0.6)
            lit = s.linear(0, cy + 12, 0, cy + 12 + length, [(0, "#d0603a", 0.45), (1, "#d0603a", 0)])
            s.path(smooth_open([(px - 4, py + 2) for px, py in pts]), stroke=lit, width=1.3)
        # lava rivulets: hot near the rim, thinning and cooling as they run down
        for x0, sway, length, seed in ((656, -0.58, 270, 1.0), (681, -0.1, 150, 2.0), (707, 0.3, 320, 3.0), (726, 0.72, 220, 4.0)):
            pts = []
            for i in range(9):
                t = i / 8
                pts.append((x0 + sway * length * t * (0.55 + 0.45 * t) + math.sin(t * 9 + seed) * 6 * t, cy + 5 + length * t))
            d = smooth_open(pts)
            s.path(d, stroke=s.linear(0, cy, 0, cy + length, [(0, MAGMA_RED, 0.35), (1, MAGMA_RED, 0)]), width=9)
            s.path(d, stroke=s.linear(0, cy, 0, cy + length, [(0, MAGMA_ORANGE), (0.7, "#e2482a"), (1, "#a8302a", 0.4)]), width=2.8)
            s.path(smooth_open(pts[:5]), stroke=s.linear(0, cy, 0, cy + length * 0.5, [(0, MAGMA_WHITE), (1, MAGMA_YELLOW, 0)]), width=1.2)
            if seed in (1.0, 3.0):  # a branch
                bx, by = pts[4]
                s.path(smooth_open([(bx, by), (bx + 10 * (1 if sway > 0 else -1), by + 30), (bx + 14 * (1 if sway > 0 else -1), by + 70)]),
                       stroke=s.linear(0, by, 0, by + 70, [(0, MAGMA_ORANGE), (1, MAGMA_RED, 0)]), width=1.8)
        # eruption plume: one lumpy silhouette bending with the wind, lit from below
        spine = [(cx, cy - 16), (683, 124), (664, 92), (636, 64), (598, 42), (552, 28), (500, 24), (446, 30), (396, 40), (356, 50)]
        widths = [10, 20, 30, 40, 48, 54, 56, 50, 40, 26]
        left_side, right_side = [], []
        for i, ((px, py), wd) in enumerate(zip(spine, widths)):
            qx, qy = spine[min(i + 1, len(spine) - 1)] if i < len(spine) - 1 else (2 * px - spine[i - 1][0], 2 * py - spine[i - 1][1])
            if i == len(spine) - 1:
                qx, qy = px - (spine[i - 1][0] - px), py - (spine[i - 1][1] - py)
            dx, dy = qx - px, qy - py
            ln = math.hypot(dx, dy) or 1.0
            nx, ny = -dy / ln, dx / ln
            bump = 1 + 0.16 * math.sin(i * 2.3)
            left_side.append((px + nx * wd * bump, py + ny * wd * bump))
            right_side.append((px - nx * wd * (2 - bump), py - ny * wd * (2 - bump)))
        outline = left_side + [(spine[-1][0] - 24, spine[-1][1] + 4)] + list(reversed(right_side))
        s.path(smooth_closed(outline, 0.8), fill=s.linear(0, 10, 0, cy, [(0, "#22102a"), (0.6, "#341630"), (1, "#5a2234")]))
        for i, ((px, py), wd) in enumerate(zip(spine, widths)):
            if i == 0:
                continue
            _soft(s, px + wd * 0.25, py + wd * 0.45, wd * 0.9, wd * 0.55, "#c8583e", 0.6 - 0.045 * i, 0.25)
            _soft(s, px - wd * 0.3, py - wd * 0.35, wd * 0.7, wd * 0.45, "#12061a", 0.35, 0.2)
        for i, ((px, py), wd) in enumerate(zip(spine[1:], widths[1:])):
            _soft(s, px + math.sin(i * 1.7) * wd * 0.5, py - wd * 0.6, wd * 0.6, wd * 0.5, "#2a1230", 0.7, 0.4)
        _soft(s, cx, cy - 22, 40, 34, "#ff8a3a", 0.6, 0.15)
        _soft(s, cx - 4, cy - 46, 30, 24, "#d86a40", 0.35, 0.1)
        _halo(s, cx, cy - 10, 60, MAGMA_YELLOW, 0.4)
        for _ in range(16):
            a = r.uniform(-2.5, -0.6)
            dist = r.uniform(8, 46)
            x, y = cx + math.cos(a) * dist * 0.8, cy - 6 + math.sin(a) * dist
            s.circle(x, y, r.uniform(0.7, 1.7), fill=r.choice([MAGMA_WHITE, MAGMA_YELLOW, MAGMA_ORANGE]), opacity=r.uniform(0.6, 1.0))
        return s

    def _ash_cloud(self, seed: int, w: float, h: float) -> Svg:
        """Drifting ash: soft translucent smoke banks with a lava-lit underside."""
        r = Rand(seed)
        s = Svg(w, h)
        n = 8
        banks = []
        for i in range(n):
            t = i / (n - 1)
            ry = h * (0.16 + 0.17 * math.sin(math.pi * t)) + r.uniform(-2, 3)
            rx = ry * r.uniform(1.7, 2.5)
            cx = w * (0.1 + 0.8 * t) + r.uniform(-8, 8)
            cy = h * 0.56 - ry * 0.25 + r.uniform(-3, 3)
            banks.append((cx, cy, min(rx, cx, w - cx), ry))
        for cx, cy, rx, ry in banks:
            _soft(s, cx, cy + ry * 0.5, rx * 0.95, ry * 0.7, "#c2563c", 0.5, 0.25)
        for cx, cy, rx, ry in banks:
            _soft(s, cx, cy, rx, ry, "#4a2538", 0.78, 0.5)
        for cx, cy, rx, ry in banks[2:-2:2]:
            _soft(s, cx - rx * 0.2, cy - ry * 0.35, rx * 0.5, ry * 0.45, "#1e0c22", 0.4, 0.2)
        return s

    def sky_extras(self) -> dict[str, PropSpec]:
        return {
            f"vf.cloud.{i}": PropSpec((lambda i=i, w=w, h=h: self._ash_cloud(53 + i * 11, w, h)), (0, 0))
            for i, (w, h) in enumerate([(300, 84), (220, 64), (360, 96)])
        }

    # ------------------------------------------------------------------ parallax layers
    def _fortress_silhouette(self, s: Svg, r: Rand, kx: float, top: float, fill: str, window: str, scale: float = 1.0) -> None:
        """Distant castle chained to its crag: towers, keep, banners, lit slits."""
        k = scale
        # crag spire
        s.polygon([(kx - 74 * k, top + 90 * k), (kx - 42 * k, top + 6 * k), (kx + 44 * k, top + 4 * k), (kx + 80 * k, top + 96 * k)], fill=fill)
        keep_w, keep_h = 64 * k, 64 * k
        s.rect(kx - keep_w / 2, top - keep_h, keep_w, keep_h + 8 * k, fill=fill)
        merlon = 7 * k
        x = kx - keep_w / 2
        while x < kx + keep_w / 2 - 1:
            s.rect(x, top - keep_h - 6 * k, merlon * 0.62, 6.5 * k, fill=fill)
            x += merlon
        for tx, tw, th, roof in ((kx - 46 * k, 20 * k, 112 * k, "spire"), (kx + 34 * k, 18 * k, 92 * k, "flat"),
                                 (kx - 6 * k, 14 * k, 96 * k, "spire")):
            s.rect(tx - tw / 2, top - th, tw, th, fill=fill)
            if roof == "spire":
                s.polygon([(tx - tw * 0.72, top - th), (tx, top - th - 30 * k), (tx + tw * 0.72, top - th)], fill=fill)
                s.line(tx, top - th - 30 * k, tx, top - th - 44 * k, fill, 1.2)
                s.polygon([(tx, top - th - 44 * k), (tx + 12 * k, top - th - 40 * k), (tx, top - th - 36 * k)], fill=BANNER, opacity=0.85)
            else:
                for j in range(3):
                    s.rect(tx - tw / 2 + j * tw / 3, top - th - 5 * k, tw / 3 * 0.6, 5 * k, fill=fill)
            for j in range(int(th / (26 * k))):
                wy = top - th + 14 * k + j * 24 * k
                if r.next() < 0.7:
                    s.rect(tx - 1.2 * k, wy, 2.4 * k, 6 * k, fill=window, opacity=0.9)
        # anchor chains binding the castle to the rock
        for ax, ay, ex, ey in ((kx - 54 * k, top - 70 * k, kx - 92 * k, top + 40 * k), (kx + 42 * k, top - 60 * k, kx + 86 * k, top + 52 * k)):
            _chain(s, _sag(ax, ay, ex, ey, 10 * k, 8), 3.4 * k, "#1e0b18", 1.1 * k, None)
        # banners on the keep
        for bx in (kx - 18 * k, kx + 12 * k):
            s.path(f"M{bx:.1f} {top - keep_h + 6 * k:.1f} h{8 * k:.1f} v{26 * k:.1f} l{-4 * k:.1f} {-5 * k:.1f} l{-4 * k:.1f} {5 * k:.1f} Z",
                   fill=BANNER, opacity=0.9)
            s.polygon(star_points(bx + 4 * k, top - keep_h + 16 * k, 2.6 * k, 1.0 * k, 4), fill="#ffb070", opacity=0.8)
        for j in range(3):
            s.rect(kx - 20 * k + j * 16 * k, top - keep_h * 0.45, 3 * k, 7 * k, fill=window, opacity=0.95)
        _halo(s, kx, top - keep_h * 0.4, 30 * k, "#ff8a3a", 0.25)

    def _far(self, seed: int) -> Svg:
        w, h = 1200.0, 300.0
        r = Rand(seed)
        s = Svg(w, h)
        fill = "#3b162d"
        window = "#ffad5a"
        # jagged crag ridge (both ends at the same height so strips tile)
        pts = [(0.0, 190.0)]
        x = 0.0
        while x < w - 90:
            x += r.uniform(50, 95)
            pts.append((x, r.uniform(150, 214)))
        pts.append((w, 190.0))
        s.path("M0 300 " + " ".join(f"L{px:.1f} {py:.1f}" for px, py in pts) + f" L{w} 300 Z", fill=fill)
        for kx, top, scale in ((w * r.uniform(0.18, 0.3), r.uniform(128, 148), r.uniform(0.85, 1.0)),
                               (w * r.uniform(0.62, 0.74), r.uniform(120, 140), r.uniform(0.9, 1.05))):
            self._fortress_silhouette(s, r, kx, top, fill, window, scale)
        # lava falls pouring down the crag faces

        def ridge_y(px: float) -> float:
            for (ax, ay), (bx, by) in zip(pts, pts[1:]):
                if ax <= px <= bx:
                    return ay + (by - ay) * (px - ax) / max(1e-6, bx - ax)
            return 190.0

        for fx in (r.uniform(60, 120), r.uniform(480, 560), r.uniform(1080, 1140)):
            fy = ridge_y(fx) + 4
            s.rect(fx - 20, fy, 40, 300 - fy, fill=s.linear(fx - 20, 0, fx + 20, 0, [(0, "#ff6a2a", 0), (0.5, "#ff6a2a", 0.32), (1, "#ff6a2a", 0)]))
            s.path(f"M{fx - 2.5:.1f} {fy:.1f} Q{fx - 4.5:.1f} {(fy + 300) / 2:.1f} {fx - 4:.1f} 300 L{fx + 4:.1f} 300 "
                   f"Q{fx + 4.5:.1f} {(fy + 300) / 2:.1f} {fx + 2.5:.1f} {fy:.1f} Z",
                   fill=s.linear(0, fy, 0, 300, [(0, MAGMA_YELLOW), (0.5, MAGMA_ORANGE), (1, MAGMA_RED)]))
        # atmospheric lava haze toward the bottom
        s.rect(0, 90, w, 210, fill=s.linear(0, 90, 0, 300, [(0, "#9a3430", 0), (0.55, "#9a3430", 0.38), (1, "#c2482e", 0.68)]))
        return s

    def _cliff(self, s: Svg, r: Rand, x0: float, x1: float, peak: float, base: float, bottom: float) -> list[tuple[float, float, float]]:
        """A cliff of touching hexagonal basalt columns; returns (left, right, top) per column."""
        lit, body, dark, cap, cap_hi = "#4a2238", "#32172b", "#1f0c1b", "#5c2b40", "#8a4450"
        cols = []
        x = x0
        while x < x1 - 8:
            cw = min(r.uniform(14, 24), x1 - x)
            t = (x + cw / 2 - x0) / (x1 - x0)
            prof = math.sin(math.pi * min(1.0, max(0.0, t))) ** 0.6
            cols.append((x, x + cw, base - (base - peak) * prof + r.uniform(-8, 8)))
            x += cw
        for a, b, top in cols:
            cw = b - a
            s.rect(a, top, cw, bottom - top, fill=body)
            s.rect(a, top, cw * 0.3, bottom - top, fill=lit)
            s.rect(a + cw * 0.7, top, cw * 0.3, bottom - top, fill=dark)
            s.line(a, top, a, bottom, "#14070f", 1.0)
            hx = cw * 0.25
            s.polygon([(a, top), (a + hx, top - 4.5), (b - hx, top - 4.5), (b, top), (b - hx, top + 4), (a + hx, top + 4)], fill=cap)
            s.line(a + hx, top - 4.5, b - hx, top - 4.5, cap_hi, 1.0, 0.7)
            yy = top + r.uniform(16, 36)
            while yy < bottom - 16:
                s.line(a + 1, yy, b - 1, yy + r.uniform(-3, 3), "#14070f", 1.5, 0.85)
                yy += r.uniform(24, 56)
        # warm rim on the outer faces of the cliff
        for a, b, top in (cols[0], cols[-1]):
            edge = a if (a, b, top) == cols[0] else b
            s.line(edge, top + 2, edge, bottom, "#d0583a", 1.6, 0.55)
        return cols

    def _lava_fall(self, s: Svg, x: float, top: float, bottom: float, width: float, r: Rand) -> None:
        """Lava spilling over a column top and splashing into the river below."""
        _soft(s, x, (top + bottom) / 2, width * 2.6, (bottom - top) * 0.62, "#ff6a2a", 0.42, 0.35)
        left = [(x - width / 2 + math.sin(i * 1.3 + x) * 1.2 - i * 0.3, top + (bottom - top) * i / 8) for i in range(9)]
        right = [(x + width / 2 + math.sin(i * 1.1 + x * 0.7) * 1.2 + i * 0.4, top + (bottom - top) * i / 8) for i in range(9)]
        left[0] = (x - width * 0.62, top - 2.5)
        right[0] = (x + width * 0.62, top - 2.5)
        d = smooth_open(left) + "".join(f"L{px:.2f} {py:.2f}" for px, py in reversed(right)) + "Z"
        s.path(d, fill=s.linear(0, top, 0, bottom, [(0, MAGMA_YELLOW), (0.12, MAGMA_ORANGE), (0.6, "#f05a26"), (1, MAGMA_RED)]))
        for k in range(3):
            sx = x - width * 0.25 + k * width * 0.25 + r.uniform(-1, 1)
            s.path(smooth_open([(sx, top + 2), (sx + 1.2, top + (bottom - top) * 0.45), (sx - 0.8, bottom - 6)]), stroke=MAGMA_YELLOW,
                   width=1.0, opacity=0.55)
        s.path(f"M{x - width * 0.62:.1f} {top - 2.5:.1f} Q{x:.1f} {top - 4.5:.1f} {x + width * 0.62:.1f} {top - 2.5:.1f}", stroke=MAGMA_YELLOW,
               width=1.2, opacity=0.9)
        _halo(s, x, bottom - 4, width * 2.4, MAGMA_ORANGE, 0.55)
        for k in range(4):
            px = x + r.uniform(-width, width)
            _soft(s, px, bottom - 14 - k * 10, width * r.uniform(0.7, 1.1), width * 0.6, "#e0a8a0", 0.16, 0.2)

    def _mid(self, seed: int) -> Svg:
        w, h = 1100.0, 280.0
        r = Rand(seed)
        s = Svg(w, h)
        x = r.uniform(10, 50)
        while x < w - 160:
            width = r.uniform(170, 300)
            x1 = min(w - 10, x + width)
            cols = self._cliff(s, r, x, x1, r.uniform(70, 105), r.uniform(140, 165), h)
            if len(cols) > 4 and r.next() < 0.8:
                a, b, top = cols[int(r.uniform(1.5, len(cols) - 1.5))]
                self._lava_fall(s, (a + b) / 2, top, h - 22, min(b - a - 2, r.uniform(13, 19)), r)
            x = x1 + r.uniform(40, 120)
        # lava river along the bottom and warm haze
        s.rect(0, 252, w, 28, fill=s.linear(0, 252, 0, 280, [(0, MAGMA_ORANGE), (1, MAGMA_RED)]))
        s.line(0, 252.5, w, 252.5, MAGMA_YELLOW, 1.4, 0.8)
        s.rect(0, 110, w, 170, fill=s.linear(0, 110, 0, 280, [(0, "#8a2c30", 0), (0.55, "#8a2c30", 0.4), (1, "#d0502c", 0.72)]))
        return s

    def _near(self, seed: int) -> Svg:
        w, h = 900.0, 150.0
        r = Rand(seed)
        s = Svg(w, h)
        silhouette, rim = "#1d0c16", "#c2522e"

        def ground_y(x: float) -> float:  # periodic in w: every strip variant shares its edge height
            return 104 + 8 * math.sin(2 * math.pi * 2 * x / w) + 5 * math.sin(2 * math.pi * 5 * x / w)

        # broken column stumps and spikes
        x = r.uniform(20, 70)
        while x < w - 50:
            gy = ground_y(x)
            roll = r.next()
            if roll < 0.45:
                for j in range(int(r.uniform(2, 4))):
                    cw = r.uniform(12, 20)
                    top = gy - r.uniform(18, 62)
                    s.rect(x, top, cw, gy - top + 10, fill=silhouette)
                    s.polygon([(x, top), (x + cw * 0.3, top - 3.5), (x + cw * 0.7, top - 3.5), (x + cw, top), (x + cw * 0.5, top + 2)],
                              fill="#2c1520")
                    s.line(x + 0.6, top, x + 0.6, gy, rim, 1.1, 0.55)
                    s.line(x + cw * 0.3, top - 3.5, x + cw * 0.7, top - 3.5, rim, 1.0, 0.6)
                    x += cw + 0.8
            elif roll < 0.7:
                rw = r.uniform(30, 54)
                rh = r.uniform(10, 20)
                pts = [(x, gy + 2), (x + rw * 0.15, gy - rh * 0.7), (x + rw * 0.42, gy - rh), (x + rw * 0.7, gy - rh * 0.8), (x + rw, gy + 2)]
                s.polygon(pts, fill=silhouette)
                s.path("M" + " L".join(f"{px:.1f} {py:.1f}" for px, py in pts[1:4]), stroke=rim, width=1.2, opacity=0.5)
                x += rw
            else:
                for j in range(3):
                    px = x + j * 9
                    s.polygon([(px - 3, gy), (px, gy - r.uniform(16, 30)), (px + 3, gy)], fill=silhouette)
                s.path(smooth_open(_sag(x, gy - 14, x + 18, gy - 13, 5, 6)), stroke="#3a2230", width=1.4)
                x += 30
            x += r.uniform(30, 90)
        pts = [(0.0, ground_y(0))] + [(w * i / 30, ground_y(w * i / 30)) for i in range(1, 30)] + [(w, ground_y(w))]
        s.path(smooth_open(pts) + f"L{w} {h} L0 {h} Z", fill=s.linear(0, 90, 0, h, [(0, silhouette), (0.5, "#2a0f18"), (1, "#5e1c1c")]))
        s.path(smooth_open(pts), stroke=rim, width=1.4, opacity=0.45)
        for _ in range(10):
            px = r.uniform(10, w - 10)
            py = ground_y(px) + r.uniform(8, 30)
            s.ellipse(px, py, r.uniform(8, 20), r.uniform(2, 4), fill=s.radial(px, py, 20, [(0, MAGMA_YELLOW, 0.9), (0.5, MAGMA_ORANGE, 0.6),
                                                                                          (1, MAGMA_RED, 0)]))
        return s

    def layer_art(self) -> dict[str, PropSpec]:
        art = {}
        for i in range(2):
            art[f"vf.far.{i}"] = PropSpec((lambda i=i: self._far(13 + i * 7)), (0, 0))
            art[f"vf.mid.{i}"] = PropSpec((lambda i=i: self._mid(29 + i * 5)), (0, 0))
            art[f"vf.near.{i}"] = PropSpec((lambda i=i: self._near(47 + i * 3)), (0, 0))
        return art

    def layers(self) -> list[Layer]:
        return [
            Layer("far", 0.08, ["vf.far.0", "vf.far.1"], 1200, 70, vertical=0.05),
            Layer("mid", 0.24, ["vf.mid.0", "vf.mid.1"], 1100, 62, vertical=0.15),
            Layer("near", 0.5, ["vf.near.0", "vf.near.1"], 900, 40, vertical=0.35),
        ]

    # ------------------------------------------------------------------ terrain
    def terrain(self, style: str, w: float, h: float, seed: int, left: bool, right: bool, top: bool = True, x0: float = 0.0,
                surface: str = "normal") -> Svg:
        """Terrain chunk art. Every pattern that crosses chunk borders (basalt
        columns, crust plates, seams, joints, magma cracks) is a function of the
        world x (``x0`` + local x), so adjacent chunks join seamlessly; only the
        hanging edge of the crust is outlined."""
        if style == "cave":
            return self._cave(w, h, seed, left, right, x0)
        if style == "fortress":
            return self._fortress(w, h, seed, left, right, top, x0)
        return self._basalt(w, h, seed, left, right, top, x0, surface)

    def _plates(self, w: float, left: bool, right: bool, x0: float) -> list[tuple[int, float, float]]:
        """Crust plates (= column tops) in local x; exposed ends get a full plate."""
        out = []
        for k, a, b in _columns(x0, x0 + w):
            a, b = a - x0, b - x0
            if left and b < 7:
                continue
            if right and a > w - 7:
                break
            if left and a < 0.6:
                a = 0.6
            if right and b > w - 0.6:
                b = w - 0.6
            out.append((k, a, b))
        if left and out:
            out[0] = (out[0][0], 0.6, out[0][2])
        if right and out:
            out[-1] = (out[-1][0], out[-1][1], w - 0.6)
        return out

    def _basalt(self, w: float, h: float, seed: int, left: bool, right: bool, top: bool, x0: float, surface: str) -> Svg:
        hr = self.terrain_headroom
        s = Svg(w, h + hr)
        r = Rand(seed)
        y0 = hr
        bottom = h + hr
        s.rect(0, y0 + 2, w, h - 2, fill=s.linear(0, y0, 0, y0 + 150, [(0, BASALT), (0.25, "#2c2027"), (0.6, "#160f14"), (1, "#0a0609")]))
        cols = _columns(x0, x0 + w)
        # column faces: lit facet, ridge, shadow facet, seams and joints
        for k, a, b in cols:
            a, b = a - x0, b - x0
            cw = b - a
            s.rect(a, y0, cw * 0.3, h, fill="#ffffff", opacity=0.045)
            s.rect(a + cw * 0.68, y0, cw * 0.32, h, fill="#000000", opacity=0.22)
            s.line(a + cw * 0.3, y0 + 10, a + cw * 0.3, bottom, BASALT_LIT, 0.9, 0.55)
            s.line(a, y0, a, bottom, BASALT_DEEP, 1.4)
            jy = y0 + 20 + _hash01(k, 1.7) * 18
            j = 0
            while jy < bottom - 4 and j < 5:
                slant = (_hash01(k * 7 + j, 2.3) - 0.5) * 5
                s.line(a + 0.7, jy, b - 0.7, jy + slant, BASALT_DEEP, 1.3)
                s.line(a + 1.2, jy + 1.5, b - 1.2, jy + 1.5 + slant, BASALT_LIT, 0.8, 0.5)
                jy += 24 + _hash01(k * 13 + j, 4.1) * 22
                j += 1
        # glowing magma cracks following some column seams (world-aligned)
        for k, a, b in cols:
            if _hash01(k, 7.7) > 0.2:
                continue
            a -= x0
            length = 26 + _hash01(k, 8.1) * 46
            pts = [(a, y0 + 8)]
            yy = y0 + 8
            i = 0
            while yy < y0 + 8 + length:
                yy += 7 + _hash01(k * 5 + i, 9.3) * 6
                pts.append((a + (_hash01(k * 3 + i, 5.5) - 0.5) * 5, yy))
                i += 1
            d = "M" + " L".join(f"{px:.2f} {py:.2f}" for px, py in pts)
            _glow_line(s, d, 1.0, True, 0.95)
            bx, by = pts[len(pts) // 2]
            s.path(f"M{bx:.2f} {by:.2f} l{4 + _hash01(k, 6.6) * 5:.2f} {5 + _hash01(k, 6.9) * 6:.2f}", stroke=MAGMA_ORANGE, width=1.2, opacity=0.8)
            _halo(s, a, y0 + 14, 12, MAGMA_ORANGE, 0.35)
        # embedded embers and obsidian glints (chunk-local, kept off the borders)
        for _ in range(max(1, int(w / 70))):
            px, py = r.uniform(10, w - 10), r.uniform(y0 + 30, min(bottom - 8, y0 + 110))
            if r.next() < 0.5:
                _halo(s, px, py, 6, MAGMA_ORANGE, 0.45)
                s.circle(px, py, 1.2, fill=MAGMA_YELLOW)
            else:
                pr = r.uniform(2.5, 4.5)
                s.polygon([(px - pr, py), (px - pr * 0.2, py - pr * 1.3), (px + pr, py - pr * 0.1), (px + pr * 0.1, py + pr * 0.9)],
                          fill=s.linear(px - pr, py - pr, px + pr, py + pr, [(0, OBSIDIAN_HI), (1, OBSIDIAN_DARK)]), stroke=INK, width=0.6)
        # exposed cliff sides: shadowed face plus a warm rim lit by the lava below
        for exposed, edge, inner in ((left, 0.0, 9.0), (right, w, w - 9.0)):
            if not exposed:
                continue
            s.rect(min(edge, inner), y0, 9, h, fill=s.linear(edge, 0, inner, 0, [(0, "#000000", 0.5), (1, "#000000", 0)]))
            s.rect(min(edge, inner), y0 + 12, 9, 90, fill=s.linear(0, y0 + 12, 0, y0 + 102, [(0, MAGMA_ORANGE, 0), (0.35, MAGMA_ORANGE, 0.42),
                                                                                           (1, MAGMA_ORANGE, 0)]))
            s.line(edge, y0 + 4, edge, bottom, INK, 2.0)
        if top:
            self._crust(s, w, y0, left, right, x0, surface)
        return s

    def _crust(self, s: Svg, w: float, y0: float, left: bool, right: bool, x0: float, surface: str) -> None:
        """Cooled crust cap: one plate per column top, magma glowing in the seams."""
        if surface == "ice":  # glassy obsidian crust
            hi, top_c, mid_c, low_c, seam = "#b9b0d8", "#4a3c66", "#2a2040", "#160f24", "#7a5ab8"
        elif surface == "sticky":  # thick ash drifts
            hi, top_c, mid_c, low_c, seam = "#b2a6a2", "#857a78", "#635958", "#433a3c", "#5a3a34"
        else:
            hi, top_c, mid_c, low_c, seam = CRUST_HI, CRUST_TOP, CRUST, CRUST_LOW, MAGMA_ORANGE
        plates = self._plates(w, left, right, x0)
        # magma behind the plates shows through the seams
        s.rect(0, y0 - 0.5, w, 11, fill=s.linear(0, y0, 0, y0 + 11, [(0, seam), (0.5, MAGMA_RED if surface == "normal" else seam), (1, BASALT_DEEP)]))
        cap_fills = [s.linear(0, y0 - 1, 0, y0 + 13, [(0, shade(top_c, d)), (0.45, shade(mid_c, d)), (1, low_c)]) for d in (0.07, 0.0, -0.1)]
        lips = []
        for k, a, b in plates:
            dy = (_hash01(k, 11.3) - 0.5) * 1.0
            ty = y0 - 0.6 + dy * 0.5
            c = 2.2
            gap = 0.55
            la, lb = a + (gap if not (left and a < 1) else 0.0), b - (gap if not (right and b > w - 1) else 0.0)
            depth_l = y0 + 9 + _hash01(k, 12.1) * 4
            depth_r = y0 + 9 + _hash01(k + 1, 12.1) * 4 if not (right and b > w - 1) else y0 + 10
            mid_y = max(depth_l, depth_r) + 1.5 + _hash01(k, 13.7) * 2.5
            lip = [(lb - 0.4, depth_r), (lb - (lb - la) * 0.3, mid_y - 0.8), (la + (lb - la) * 0.55, mid_y),
                   (la + 0.4, depth_l)]
            outline = [(la, ty + c), (la + c, ty), (lb - c, ty), (lb, ty + c)] + lip
            s.polygon(outline, fill=cap_fills[int(_hash01(k, 16.1) * 3) % 3])
            # bevelled top face and a hot glint where the plate meets the seam
            s.path(f"M{la + c:.2f} {ty + 0.5:.2f} L{lb - c:.2f} {ty + 0.5:.2f}", stroke=hi, width=1.3, opacity=0.95)
            s.path(f"M{la + 0.6:.2f} {ty + c + 0.6:.2f} L{la + 0.6:.2f} {depth_l - 2:.2f}", stroke=hi, width=0.8, opacity=0.35)
            # cracks in the crust
            if _hash01(k, 14.9) < 0.45:
                cx = la + (lb - la) * (0.3 + 0.4 * _hash01(k, 15.3))
                s.path(f"M{cx:.2f} {ty + 1:.2f} l{1.5:.2f} 3 l-1 3 l1.6 2.5", stroke=low_c if surface != "normal" else "#3a2a2e", width=0.8)
            if surface == "sticky":
                s.path(blob((la + lb) / 2, ty + 0.5, (lb - la) * 0.42, 2.2, 0.2, seed=k), fill="#9c908e", opacity=0.9)
            elif surface == "ice":
                s.path(f"M{la + 3:.2f} {ty + 3:.2f} l3 4 M{la + 6:.2f} {ty + 2.5:.2f} l2 2.5", stroke="#ffffff", width=0.8, opacity=0.6)
            lips.append(lip)
        # shadow under the cap, then outline only the hanging edge of each plate
        for lip in lips:
            s.path(smooth_open([(px, py + 2.5) for px, py in lip], 0.5), stroke="#000000", width=4.5, opacity=0.28)
        for lip in lips:
            s.path(smooth_open(lip, 0.5), stroke=INK, width=1.2)
        # exposed ends of the cap get an outline (never the chunk's inner borders)
        if left and plates:
            k, a, b = plates[0]
            s.path(f"M0.6 {y0 + 1.4:.2f} L0.6 {lips[0][-1][1]:.2f}", stroke=INK, width=1.4)
        if right and plates:
            s.path(f"M{w - 0.6:.2f} {y0 + 1.4:.2f} L{w - 0.6:.2f} {lips[-1][0][1]:.2f}", stroke=INK, width=1.4)

    def _fortress(self, w: float, h: float, seed: int, left: bool, right: bool, top: bool, x0: float) -> Svg:
        """Fortress masonry: dark bricked stone with iron trims (world-aligned)."""
        hr = self.terrain_headroom
        s = Svg(w, h + hr)
        y0 = hr
        s.rect(0, y0, w, h, fill=s.linear(0, y0, 0, y0 + h, [(0, "#4a3a46"), (0.5, "#30242e"), (1, "#18121a")]))
        row_h = 20.0
        brick = 44.0
        for row in range(int(h / row_h) + 1):
            yy = y0 + 8 + row * row_h
            offset = (row % 2) * brick / 2
            first = math.floor((x0 - offset) / brick)
            gx = first * brick + offset - x0
            idx = first
            while gx < w:
                bx0, bx1 = gx + 1.2, gx + brick - 1.2
                tone = _hash01(idx * 31 + row, 2.2)
                s.rect(bx0, yy + 1.2, bx1 - bx0, row_h - 2.4, fill=mix("#4e3c4a", "#3a2c38", tone), rx=2)
                s.line(bx0 + 1.5, yy + 2.6, bx1 - 1.5, yy + 2.6, "#6e5a68", 1.0, 0.6)
                s.line(bx0 + 1.5, yy + row_h - 2.4, bx1 - 1.5, yy + row_h - 2.4, "#140c12", 1.0, 0.6)
                if _hash01(idx * 17 + row, 5.9) < 0.12:
                    cx = gx + brick * 0.5
                    _glow_line(s, f"M{cx - 6:.2f} {yy + 3:.2f} L{cx - 1:.2f} {yy + 9:.2f} L{cx + 3:.2f} {yy + 7:.2f} L{cx + 7:.2f} {yy + 15:.2f}",
                               0.7, True, 0.85)
                gx += brick
                idx += 1
        s.rect(0, y0 + 30, w, h - 30, fill=s.linear(0, y0 + 30, 0, y0 + 160, [(0, "#000000", 0), (1, "#000000", 0.5)]))
        if left:
            s.rect(0, y0, 6, h, fill=s.linear(0, 0, 6, 0, [(0, IRON_DARK), (1, IRON_DEEP)]))
            s.line(0.8, y0, 0.8, y0 + h, INK, 1.6)
        if right:
            s.rect(w - 6, y0, 6, h, fill=s.linear(w - 6, 0, w, 0, [(0, IRON_DEEP), (1, IRON_DARK)]))
            s.line(w - 0.8, y0, w - 0.8, y0 + h, INK, 1.6)
        if top:
            s.rect(0, y0 - 1, w, 9, fill=s.linear(0, y0 - 1, 0, y0 + 8, [(0, IRON_HI), (0.4, IRON), (1, IRON_DARK)]))
            s.line(0, y0 - 0.4, w, y0 - 0.4, "#d8d6e2", 1.2, 0.9)
            s.line(0, y0 + 8, w, y0 + 8, INK, 1.3)
            first = math.ceil((x0 - 12) / 24)
            rx = first * 24 + 12 - x0
            while rx < w + 3:
                s.circle(rx, y0 + 3.6, 1.6, fill=s.radial(rx - 0.5, y0 + 3.1, 2, [(0, "#e8e6f0"), (1, IRON_DARK)]))
                rx += 24
        return s

    def _cave(self, w: float, h: float, seed: int, left: bool, right: bool, x0: float) -> Svg:
        """Magma chamber rock: dark basalt mass threaded with glowing veins."""
        r = Rand(seed)
        hr = self.terrain_headroom
        s = Svg(w, h + hr)
        y0 = hr
        s.rect(0, y0, w, h, fill=s.linear(0, y0, 0, y0 + min(h, 200), [(0, "#46303a"), (0.4, "#2e1f27"), (1, "#1a1016")]))
        # fractured rock facets (kept clear of the chunk borders so none is cut)
        for _ in range(max(2, int(w * h / 2200))):
            pr = r.uniform(5, 13)
            if w < pr * 3.2 + 8 or h < pr * 2 + 8:
                continue
            px, py = r.uniform(pr * 1.6 + 4, w - pr * 1.6 - 4), r.uniform(y0 + pr + 6, y0 + h - pr - 4)
            n = int(r.uniform(5, 7))
            angles = [2 * math.pi * i / n + 0.3 for i in range(n)]
            pts = [(px + math.cos(a) * pr * r.uniform(1.0, 1.5), py + math.sin(a) * pr * r.uniform(0.6, 0.9)) for a in angles]
            s.polygon(pts, fill=r.choice(["#3c2832", "#4a343e", "#2a1a22"]), opacity=0.85)
            top_edge = sorted(pts, key=lambda q: q[1])[:3]
            top_edge.sort()
            s.path("M" + " L".join(f"{qx:.2f} {qy:.2f}" for qx, qy in top_edge), stroke="#6a4c56", width=0.9, opacity=0.6)
        # magma veins as functions of world x (continuous across chunks)
        for k, (base, amp, freq) in enumerate(((0.45, 10, 0.021), (0.78, 7, 0.033))):
            yb = y0 + min(h - 8, max(14, h * base))
            pts = [(lx, yb + amp * math.sin((x0 + lx) * freq + k * 2.1) + 4 * math.sin((x0 + lx) * 0.071 + k))
                   for lx in [i * w / 16 for i in range(17)]]
            if h > 30:
                _glow_line(s, smooth_open(pts), 0.9 if k == 0 else 0.7, k == 0, 0.85)
        # ember crystals
        for _ in range(int(w / 110) + 1):
            cx, cy = r.uniform(12, w - 12), r.uniform(y0 + 10, y0 + max(12, h - 10))
            _halo(s, cx, cy, 10, MAGMA_ORANGE, 0.4)
            s.polygon([(cx, cy - 7), (cx + 3.2, cy), (cx, cy + 3.5), (cx - 3.2, cy)],
                      fill=s.linear(cx, cy - 7, cx, cy + 4, [(0, MAGMA_WHITE), (0.5, MAGMA_ORANGE), (1, MAGMA_RED)]), stroke=INK, width=0.6)
        s.rect(0, y0 + 24, w, h - 24, fill=s.linear(0, y0 + 24, 0, y0 + 220, [(0, "#000000", 0), (1, "#000000", 0.45)]))
        # walkable top edge (cave floors are often flagged covered by their walls)
        s.rect(0, y0 - 0.6, w, 5, fill=s.linear(0, y0 - 0.6, 0, y0 + 4.4, [(0, CRUST_TOP), (1, CRUST_LOW)]))
        s.line(0, y0 - 0.2, w, y0 - 0.2, CRUST_HI, 1.3, 0.85)
        s.path(smooth_open([(lx, y0 + 4.6 + 0.8 * math.sin((x0 + lx) * 0.19)) for lx in [i * w / 12 for i in range(13)]]), stroke=INK, width=1.0)
        # glowing underside for ceilings and ledges
        s.rect(0, y0 + h - 6, w, 6, fill=s.linear(0, y0 + h - 6, 0, y0 + h, [(0, MAGMA_RED, 0), (1, MAGMA_ORANGE, 0.45)]))
        if left:
            s.line(0.8, y0, 0.8, y0 + h, INK, 1.6)
        if right:
            s.line(w - 0.8, y0, w - 0.8, y0 + h, INK, 1.6)
        return s

    def cave_sky(self) -> Svg:
        """Magma chamber: a vault of basalt columns lit from a magma lake below."""
        s = Svg(960, 540)
        s.rect(0, 0, 960, 540, fill=s.linear(0, 0, 0, 540, [(0, "#0b050a"), (0.45, "#1c0a12"), (0.8, "#3a1014"), (1, "#5a1a14")]))
        r = Rand(19)
        _soft(s, 480, 130, 380, 90, "#07030a", 0.55, 0.3)
        _soft(s, 480, 570, 600, 240, "#ff7a32", 0.7, 0.1)
        _soft(s, 480, 250, 520, 90, "#a8382a", 0.35, 0.2)
        # distant falls pouring from cracks in the vault
        for fx, top in ((250, 70), (640, 60), (820, 90)):
            _soft(s, fx, 300, 40, 260, "#ff6a2a", 0.35, 0.2)
            s.path(f"M{fx - 3} {top} Q{fx - 5} {top + 200} {fx - 6} 540 L{fx + 6} 540 Q{fx + 5} {top + 200} {fx + 3} {top} Z",
                   fill=s.linear(0, top, 0, 540, [(0, MAGMA_YELLOW, 0.9), (0.5, MAGMA_ORANGE, 0.85), (1, MAGMA_RED, 0.7)]))
        # far basalt column clusters, rim-lit by the lake
        for k, (gx, n, peak) in enumerate(((20, 6, 150), (300, 5, 130), (520, 6, 110), (790, 7, 140))):
            x = gx + r.uniform(-20, 20)
            for i in range(n):
                cw = r.uniform(16, 26)
                t = i / max(1, n - 1)
                top = peak + 90 * abs(t - 0.5) * 2 + r.uniform(-14, 14)
                s.rect(x, top, cw, 540 - top, fill=s.linear(0, top, 0, 540, [(0, "#24101c"), (1, "#3a1520")]))
                s.rect(x + cw * 0.68, top, cw * 0.32, 540 - top, fill="#000000", opacity=0.3)
                hx = cw * 0.25
                s.polygon([(x, top), (x + hx, top - 4), (x + cw - hx, top - 4), (x + cw, top), (x + cw - hx, top + 3), (x + hx, top + 3)],
                          fill="#3e1c2a")
                s.line(x + 0.8, top + 2, x + 0.8, 540, s.linear(0, top, 0, 540, [(0, "#e0643c", 0.1), (1, "#ff8a3a", 0.75)]), 1.6)
                yy = top + r.uniform(20, 50)
                while yy < 520:
                    s.line(x + 1, yy, x + cw - 1, yy + r.uniform(-3, 3), "#12060c", 1.4, 0.8)
                    yy += r.uniform(30, 70)
                x += cw + 0.8
        # vault with hanging stalactites, their lower edges catching the glow
        ceiling = [(0.0, 64.0)]
        x = 0.0
        while x < 960:
            x += r.uniform(30, 70)
            ceiling.append((min(960.0, x), r.uniform(44, 84)))
        s.path("M0 0 L960 0 " + " ".join(f"L{px:.1f} {py:.1f}" for px, py in reversed(ceiling)) + " Z", fill="#0d050a")
        s.path(smooth_open(ceiling, 0.4), stroke="#7a2a22", width=1.4, opacity=0.6)
        for _ in range(16):
            sx = r.uniform(10, 950)
            ln = r.uniform(30, 110)
            sw = r.uniform(7, 18)
            s.polygon([(sx - sw, 50), (sx + sw, 50), (sx + sw * 0.15, 50 + ln), (sx - sw * 0.1, 50 + ln * 0.92)],
                      fill=s.linear(0, 50, 0, 50 + ln, [(0, "#0d050a"), (1, "#3a1620")]))
            s.path(f"M{sx + sw:.1f} 56 L{sx + sw * 0.15:.1f} {50 + ln:.1f}", stroke="#c2502e", width=1.1, opacity=0.55)
            s.circle(sx + sw * 0.05, 50 + ln + 3, 1.6, fill=MAGMA_ORANGE, opacity=0.8)
        for _ in range(40):
            s.circle(r.uniform(0, 960), r.uniform(100, 520), r.uniform(0.6, 1.6), fill=r.choice([MAGMA_YELLOW, MAGMA_ORANGE]),
                     opacity=r.uniform(0.3, 0.8))
        return s

    # ------------------------------------------------------------------ indoor fortress halls
    def interior(self, variant: str):
        if variant != "fortress":
            return None

        def backdrop() -> Svg:
            s = Svg(960, 540)
            s.rect(0, 0, 960, 540, fill=s.linear(0, 0, 0, 540, [(0, "#140a12"), (0.6, "#2a1620"), (1, "#3a1a1c")]))
            for row in range(13):
                y = row * 44
                off = (row % 2) * 60
                for col in range(-1, 9):
                    x = col * 120 + off
                    tone = _hash01(row * 13 + col, 1.3)
                    s.rect(x + 2, y + 2, 116, 40, fill=mix("#2e1c28", "#3a2430", tone), rx=3)
                    s.line(x + 4, y + 4, x + 114, y + 4, "#4e3440", 1.2, 0.6)
            for ax in (140, 480, 820):
                # arched windows open on the lava sea outside
                s.path(f"M{ax - 60} 380 L{ax - 60} 180 Q{ax} 90 {ax + 60} 180 L{ax + 60} 380 Z",
                       fill=s.linear(0, 100, 0, 380, [(0, "#3a1230"), (0.55, "#a8382c"), (1, "#ffa04a")]), stroke="#120a10", width=7)
                s.path(f"M{ax - 60} 330 Q{ax - 20} 300 {ax + 10} 320 Q{ax + 40} 336 {ax + 60} 310 L{ax + 60} 380 L{ax - 60} 380 Z", fill="#2a0e18")
                for bx in (ax - 30, ax, ax + 30):
                    s.line(bx, 120 if bx == ax else 140, bx, 380, "#140a10", 4.0)
                s.line(ax - 60, 250, ax + 60, 250, "#140a10", 4.0)
                s.rect(ax - 80, 380, 160, 14, fill="#3a2a32", rx=3)
                s.polygon([(ax - 50, 380), (ax + 50, 380), (ax + 140, 540), (ax - 140, 540)], fill="#ff8a3a", opacity=0.07)
            for bx in (300, 650):
                s.path(f"M{bx} 60 L{bx + 46} 60 L{bx + 46} 220 L{bx + 23} 200 L{bx} 220 Z",
                       fill=s.linear(bx, 0, bx + 46, 0, [(0, BANNER), (1, BANNER_DARK)]), stroke="#120a10", width=2)
                s.polygon(star_points(bx + 23, 120, 13, 5, 4), fill="#ffb060", stroke="#5a1a10", width=1.2)
                s.line(bx - 6, 60, bx + 52, 60, IRON_DARK, 4)
            for cx in (30, 930):
                _chain(s, [(cx, 0), (cx + 4, 160), (cx, 300)], 9, IRON_DARK, 2.4, IRON)
            return s

        def pillars() -> Svg:
            s = Svg(900, 420)
            for x in (90, 540):
                s.rect(x, 20, 70, 400, fill=s.linear(x, 0, x + 70, 0, [(0, "#3e2a36"), (0.4, "#5a3e4a"), (1, "#22161e")]), rx=4)
                for y in range(40, 420, 46):
                    s.line(x, y, x + 70, y, "#1a1016", 2.0, 0.8)
                for y in (60, 300):
                    s.rect(x - 4, y, 78, 12, fill=s.linear(0, y, 0, y + 12, [(0, IRON_HI), (1, IRON_DARK)]), rx=2, stroke=INK, width=1.2)
                _halo(s, x + 35, 150, 44, MAGMA_ORANGE, 0.55)
                s.path(f"M{x + 20} 160 L{x + 50} 160 L{x + 44} 176 L{x + 26} 176 Z", fill=IRON_DARK, stroke=INK, width=1.4)
                _flame(s, x + 35, 160, 26, 34, seed=x)
            return s

        return backdrop, pillars

    def gate(self, w: float, h: float) -> Svg:
        """Arena portcullis: heated iron bars with glowing tips."""
        s = Svg(w, h)
        s.rect(0, 0, w, h, fill=s.linear(0, 0, 0, h, [(0, "#24161e"), (1, "#100a0e")]), rx=2)
        n = max(2, int(w // 9) + 1)
        for i in range(n):
            x = 2 + i * (w - 4) / max(1, n - 1) - 1.6
            s.rect(x, 0, 3.4, h - 5, fill=s.linear(x, 0, x + 3.4, 0, [(0, IRON_HI), (1, IRON_DARK)]), rx=1)
            s.polygon([(x - 0.8, h - 7), (x + 1.7, h), (x + 4.2, h - 7)], fill=s.linear(0, h - 7, 0, h, [(0, IRON), (1, MAGMA_ORANGE)]))
        for y in (h * 0.22, h * 0.6):
            s.rect(0, y, w, 4.5, fill=s.linear(0, y, 0, y + 4.5, [(0, IRON_HI), (1, IRON_DARK)]), stroke=INK, width=0.8, rx=1.5)
        s.rect(0, h - 10, w, 10, fill=s.linear(0, h - 10, 0, h, [(0, MAGMA_ORANGE, 0), (1, MAGMA_ORANGE, 0.35)]))
        return s

    # ------------------------------------------------------------------ blocks and platforms
    def _rune(self, s: Svg, cx: float, cy: float, size: float, lit: bool) -> None:
        """Ember rune: a diamond eye around a rising flame tongue (original glyph)."""
        k = size
        diamond = [(cx, cy - k), (cx + k * 0.78, cy), (cx, cy + k), (cx - k * 0.78, cy)]
        flame = (f"M{cx:.2f} {cy - k * 0.55:.2f} Q{cx + k * 0.34:.2f} {cy - k * 0.05:.2f} {cx + k * 0.2:.2f} {cy + k * 0.32:.2f} "
                 f"Q{cx:.2f} {cy + k * 0.5:.2f} {cx - k * 0.2:.2f} {cy + k * 0.32:.2f} Q{cx - k * 0.3:.2f} {cy:.2f} {cx:.2f} {cy - k * 0.55:.2f} Z")
        ticks = (f"M{cx - k * 1.15:.2f} {cy:.2f} L{cx - k * 0.95:.2f} {cy:.2f} M{cx + k * 0.95:.2f} {cy:.2f} L{cx + k * 1.15:.2f} {cy:.2f} "
                 f"M{cx:.2f} {cy - k * 1.3:.2f} L{cx:.2f} {cy - k * 1.12:.2f}")
        if lit:
            _halo(s, cx, cy, k * 2.0, MAGMA_ORANGE, 0.75)
            s.polygon(diamond, fill=None, stroke=MAGMA_RED, width=k * 0.42)
            s.polygon(diamond, fill=None, stroke=MAGMA_YELLOW, width=k * 0.2)
            s.path(flame, fill=s.radial(cx, cy + k * 0.2, k * 0.7, [(0, MAGMA_WHITE), (0.6, MAGMA_YELLOW), (1, MAGMA_ORANGE)]),
                   stroke=MAGMA_RED, width=k * 0.08)
            s.path(ticks, stroke=MAGMA_YELLOW, width=k * 0.16)
        else:
            s.polygon(diamond, fill=None, stroke="#120c16", width=k * 0.3)
            s.polygon([(x, y + 0.6) for x, y in diamond], fill=None, stroke="#4a3e52", width=k * 0.1, opacity=0.6)
            s.path(flame, fill="#1a1220", stroke="#3e3448", width=k * 0.08)

    def block(self, kind: str, w: float, h: float) -> Svg:
        s = Svg(w, h)
        if kind in ("question", "used"):
            used = kind == "used"
            stops = [(0, "#3a2e46"), (0.5, "#221a2c"), (1, "#110c16")] if used else [(0, "#4e3a6c"), (0.45, OBSIDIAN), (1, OBSIDIAN_DARK)]
            s.path(rounded_rect_path(0.6, 0.6, w - 1.2, h - 1.2, 3.5), fill=s.linear(0, 0, w * 0.4, h, stops), stroke=INK, width=1.3)
            # glassy facets of the obsidian
            if not used:
                s.polygon([(8, 1.5), (16, 1.5), (9, h - 1.5), (4, h - 1.5)], fill="#ffffff", opacity=0.08)
                s.polygon([(w - 14, 1.5), (w - 11, 1.5), (w - 17, h - 1.5), (w - 19, h - 1.5)], fill="#ffffff", opacity=0.06)
            s.path(f"M2.5 2.4 L{w - 2.5} 2.4", stroke="#8a78b0" if not used else "#5a5066", width=1.0, opacity=0.6)
            # iron bands with rivets wrapping both sides
            for bx in (2.2, w - 8.2):
                s.path(rounded_rect_path(bx, 0.8, 6, h - 1.6, 1.2), fill=s.linear(bx, 0, bx + 6, 0, [(0, IRON_HI), (0.5, IRON), (1, IRON_DARK)]),
                       stroke=INK, width=0.8)
                for ry in (4.2, h - 4.2):
                    s.circle(bx + 3, ry, 1.25, fill=s.radial(bx + 2.6, ry - 0.5, 1.6, [(0, "#f0eef8"), (1, IRON_DARK)]))
            self._rune(s, w / 2, h / 2, min(w - 18, h) * 0.3, not used)
            if used:
                s.path(f"M{w * 0.62:.1f} 2 l-2 5 l2.5 3 l-1.5 4", stroke="#0c0810", width=0.9, opacity=0.8)
        elif kind == "brick":
            s.path(rounded_rect_path(0.6, 0.6, w - 1.2, h - 1.2, 2.5), fill="#1e1014", stroke=INK, width=1.2)
            rows = 2
            rh = (h - 2) / rows
            bw = 22.0
            for row in range(rows):
                y = 1 + row * rh
                x = -(bw / 2 if row % 2 else 0.0)
                i = 0
                while x < w:
                    bx0, bx1 = max(1.5, x + 1.1), min(w - 1.5, x + bw - 1.1)
                    if bx1 > bx0 + 2:
                        tone = _hash01(row * 7 + i, 4.4)
                        top_c = mix("#a8523a", "#8a3e2e", tone)
                        s.path(rounded_rect_path(bx0, y + 1.1, bx1 - bx0, rh - 2.2, 1.4),
                               fill=s.linear(0, y, 0, y + rh, [(0, top_c), (1, "#4e1e18")]), stroke="#2a0e0e", width=0.7)
                        s.line(bx0 + 1, y + 2.2, bx1 - 1, y + 2.2, "#e08a62", 0.9, 0.7)
                        # soot on the lower half
                        s.rect(bx0 + 0.5, y + rh * 0.55, bx1 - bx0 - 1, rh * 0.35, fill="#1a0a0c", opacity=0.25)
                        if bx1 - bx0 > bw - 4 and _hash01(row * 11 + i, 6.1) < 0.4:  # heat crack across a whole brick
                            cx = (bx0 + bx1) / 2 + (_hash01(i, 2.9) - 0.5) * 8
                            d = (f"M{cx - 5:.2f} {y + 2.2:.2f} L{cx - 2:.2f} {y + rh * 0.38:.2f} L{cx + 1.2:.2f} {y + rh * 0.42:.2f} "
                                 f"L{cx + 2.6:.2f} {y + rh * 0.7:.2f} L{cx + 5.5:.2f} {y + rh - 2.2:.2f}")
                            _glow_line(s, d, 0.42, True, 0.85)
                    x += bw
                    i += 1
        return s

    def platform(self, kind: str, w: float, h: float, style: str = "") -> Svg:
        if kind == "ledge":
            return self.terrain("terrain", w, h, int(w * 7 + h), True, True)
        s = Svg(w, h + 14)
        if kind == "moving":
            # floating basalt slab clamped by iron bands, chains dangling below
            under = (f"M3 {h - 2} Q{w * 0.25:.1f} {h + 6} {w * 0.42:.1f} {h + 10} Q{w * 0.5:.1f} {h + 13} {w * 0.58:.1f} {h + 10} "
                     f"Q{w * 0.75:.1f} {h + 6} {w - 3} {h - 2} Z")
            s.path(under, fill=s.linear(0, h - 2, 0, h + 13, [(0, BASALT), (1, BASALT_DEEP)]), stroke=INK, width=1.1)
            _glow_line(s, f"M{w * 0.36:.1f} {h + 1} L{w * 0.44:.1f} {h + 7} L{w * 0.52:.1f} {h + 4} L{w * 0.6:.1f} {h + 8}", 0.6, True, 0.9)
            s.path(rounded_rect_path(0.8, 1.5, w - 1.6, h - 1.5, 3), fill=s.linear(0, 1.5, 0, h, [(0, BASALT_LIT), (0.5, BASALT), (1, BASALT_DARK)]),
                   stroke=INK, width=1.2)
            x = 0.8
            k = 0
            while x < w - 2:
                cw = 14 + _hash01(k, 21.0) * 8
                s.line(x + cw, 5, x + cw, h - 1, BASALT_DEEP, 1.1)
                x += cw
                k += 1
            s.path(rounded_rect_path(0.8, 0.6, w - 1.6, 5.5, 2.5), fill=s.linear(0, 0.6, 0, 6, [(0, CRUST_TOP), (1, CRUST_LOW)]))
            s.line(3, 1.2, w - 3, 1.2, CRUST_HI, 1.3, 0.95)
            for bx in (w * 0.18, w * 0.82):
                s.path(rounded_rect_path(bx - 4, 0.2, 8, h + 0.4, 1.5), fill=s.linear(bx - 4, 0, bx + 4, 0, [(0, IRON_HI), (0.5, IRON), (1, IRON_DARK)]),
                       stroke=INK, width=0.9)
                for ry in (3.4, h - 3.4):
                    s.circle(bx, ry, 1.2, fill="#e8e6f0")
                _chain(s, [(bx, h + 0.5), (bx + 0.6, h + 13.5)], 3.6, IRON_DARK, 1.1, IRON_HI)
        elif kind == "crumble":
            # brittle cooling crust: pale, flaky and glowing through its cracks
            r = Rand(int(w * 3 + h))
            lip = [(w - 2, h - 2)]
            x = w - 2
            while x > 4:
                x -= r.uniform(5, 10)
                lip.append((max(2.0, x), h - 1 + r.uniform(0, 4.5)))
            body = [(1.2, 3), (3.5, 0.8), (w - 3.5, 0.8), (w - 1.2, 3)] + lip + [(1.2, h - 2)]
            s.polygon(body, fill=s.linear(0, 0, 0, h + 3, [(0, "#b19a8e"), (0.4, "#86706a"), (1, "#5a4648")]), stroke=INK, width=1.2)
            s.line(4, 1.6, w - 4, 1.6, "#ead8c8", 1.2, 0.9)
            for _ in range(3):
                cx = r.uniform(10, w - 10)
                pts = [(cx, 2.0), (cx + r.uniform(-4, 4), h * 0.4), (cx + r.uniform(-5, 5), h * 0.75), (cx + r.uniform(-4, 4), h)]
                _glow_line(s, "M" + " L".join(f"{px:.2f} {py:.2f}" for px, py in pts), 0.55, True, 0.9)
            for _ in range(int(w / 14)):
                fx = r.uniform(4, w - 4)
                s.polygon([(fx, 3 + r.uniform(0, 4)), (fx + 2.5, 4 + r.uniform(0, 4)), (fx + 1, 7 + r.uniform(0, 4))], fill="#5a4648", opacity=0.6)
            for _ in range(4):
                fx = r.uniform(8, w - 8)
                fy = h + r.uniform(4, 11)
                s.polygon([(fx, fy), (fx + 2.2, fy + 0.6), (fx + 1, fy + 2.4)], fill="#86706a", opacity=0.75)
        elif kind == "semisolid":
            # iron grate walkway on struts
            s.path(rounded_rect_path(0.6, 0.6, w - 1.2, min(h, 8), 2), fill=s.linear(0, 0, 0, 8, [(0, IRON_HI), (0.4, IRON), (1, IRON_DARK)]),
                   stroke=INK, width=1.1)
            for x in range(6, int(w) - 3, 6):
                s.line(x, 2.5, x - 2, 7, IRON_DEEP, 1.0, 0.8)
            for x in range(14, int(w), 28):
                s.line(x, 8, x - 6, h + 12, IRON_DARK, 2.2)
                s.line(x, 8, x + 6, h + 12, IRON_DEEP, 1.6)
        elif kind == "spring":
            s.rect(w / 2 - 4, h * 0.42, 8, h * 0.58, fill=s.linear(w / 2 - 4, 0, w / 2 + 4, 0, [(0, IRON_HI), (1, IRON_DARK)]),
                   stroke=INK, width=1.0, rx=2)
            for k in range(4):
                y = h * 0.5 + k * h * 0.12
                s.path(f"M{w / 2 - 7} {y:.1f} Q{w / 2} {y - 4:.1f} {w / 2 + 7} {y:.1f}", stroke=MAGMA_ORANGE, width=1.6)
            s.path(blob(w / 2, h * 0.42, w / 2, h * 0.36, 0.04, seed=3, squash_top=1.2),
                   fill=s.radial(w * 0.4, h * 0.2, w * 0.7, [(0, IRON_HI), (0.55, IRON), (1, IRON_DARK)]), stroke=INK, width=1.2)
            s.ellipse(w / 2, h * 0.3, w * 0.22, h * 0.09,
                      fill=s.radial(w / 2, h * 0.3, w * 0.22, [(0, MAGMA_WHITE), (0.5, MAGMA_ORANGE), (1, MAGMA_RED)]))
            for k in (-1, 1):
                s.circle(w / 2 + k * w * 0.32, h * 0.42, 1.2, fill="#e8e6f0")
        else:  # conveyor: iron rollers under a riveted belt
            s.path(rounded_rect_path(0.6, 0.6, w - 1.2, h - 1.2, h / 2), fill=s.linear(0, 0, 0, h, [(0, IRON), (1, IRON_DEEP)]), stroke=INK, width=1.2)
            for x in range(int(h / 2), int(w - h / 2) + 1, max(8, int(h))):
                s.circle(x, h / 2, h * 0.32, fill=s.radial(x - 1, h / 2 - 1, h * 0.35, [(0, IRON_HI), (1, IRON_DARK)]), stroke=INK, width=0.7)
            s.line(h / 2, 1.4, w - h / 2, 1.4, IRON_HI, 1.0, 0.8)
        return s

    def pipe(self, w: float, h: float, warp: bool) -> Svg:
        """Iron furnace conduit with glowing seams and a riveted collar."""
        s = Svg(w, h)
        body = s.linear(4, 0, w - 4, 0, [(0, IRON_DEEP), (0.22, IRON_HI), (0.45, IRON), (0.8, IRON_DARK), (1, IRON_DEEP)])
        s.path(rounded_rect_path(4, 10, w - 8, h - 10, 2), fill=body, stroke=INK, width=1.3)
        # glowing welded seams
        for sx in (w * 0.34, w * 0.68):
            if h > 24:
                _glow_line(s, f"M{sx:.2f} 16 L{sx:.2f} {h - 2:.2f}", 0.5, False, 0.75)
        s.rect(4.5, h - 7, w - 9, 6, fill=s.linear(0, h - 7, 0, h - 1, [(0, MAGMA_ORANGE, 0), (1, MAGMA_ORANGE, 0.3)]))
        # collar
        s.path(rounded_rect_path(0.8, 0.8, w - 1.6, 14, 3),
               fill=s.linear(0, 0, w, 0, [(0, IRON_DEEP), (0.25, IRON_HI), (0.5, IRON), (1, IRON_DEEP)]), stroke=INK, width=1.3)
        s.path(f"M3 2.4 L{w - 3} 2.4", stroke=MAGMA_YELLOW, width=1.2, opacity=0.85)
        s.path(f"M3 3.6 L{w - 3} 3.6", stroke=MAGMA_RED, width=1.0, opacity=0.6)
        s.path(f"M4 14.6 L{w - 4} 14.6", stroke=MAGMA_RED, width=2.4, opacity=0.5)
        s.path(f"M4 14.6 L{w - 4} 14.6", stroke=MAGMA_ORANGE, width=1.0)
        for rx in [6 + i * (w - 12) / 4 for i in range(5)]:
            s.circle(rx, 8.4, 1.5, fill=s.radial(rx - 0.5, 7.8, 2, [(0, "#f0eef8"), (1, IRON_DARK)]), stroke=INK, width=0.4)
        if warp:
            cy = 27 if h > 34 else h * 0.66
            _halo(s, w / 2, cy, 9, MAGMA_YELLOW, 0.8)
            s.polygon([(w / 2 - 5, cy - 3.5), (w / 2 + 5, cy - 3.5), (w / 2, cy + 3.5)], fill=MAGMA_WHITE, stroke=MAGMA_RED, width=0.8)
        return s

    # ------------------------------------------------------------------ props
    def _pillar(self, seed: int, broken: bool = False) -> Svg:
        """Cluster of weathered basalt columns (dark caps: decor, not a ledge)."""
        r = Rand(seed)
        s = Svg(80, 100)
        x = 10.0
        heights = [r.uniform(46, 70), r.uniform(70, 94), r.uniform(36, 58)] if broken else \
            [r.uniform(50, 76), r.uniform(74, 96), r.uniform(56, 84), r.uniform(30, 50)]
        for i, top_h in enumerate(heights):
            cw = r.uniform(13, 17)
            top = 100 - top_h
            s.rect(x, top, cw, top_h, fill=s.linear(x, 0, x + cw, 0, [(0, "#634c5a"), (0.32, "#4e3a48"), (0.36, "#3e2c3a"), (1, "#2c1e2a")]),
                   stroke="#26141f", width=1.1)
            hx = cw * 0.25
            if broken and i != 1:
                s.polygon([(x, top + 3), (x + cw * 0.4, top - 2), (x + cw * 0.7, top + 4), (x + cw, top)], fill="#4e3a48", stroke="#26141f", width=0.9)
            else:
                s.polygon([(x, top), (x + hx, top - 3), (x + cw - hx, top - 3), (x + cw, top), (x + cw - hx, top + 2.5), (x + hx, top + 2.5)],
                          fill="#5e4854", stroke="#26141f", width=0.9)
            yy = top + r.uniform(14, 26)
            while yy < 94:
                s.line(x + 0.8, yy, x + cw - 0.8, yy + r.uniform(-2, 2), BASALT_DEEP, 1.2)
                yy += r.uniform(16, 30)
            s.line(x + 0.6, top + 3, x + 0.6, 99, "#b0503a", 0.9, 0.45)
            if r.next() < 0.35:
                _glow_line(s, f"M{x + cw * 0.5:.1f} {top + 16:.1f} l2 7 l-2 6 l1.5 6", 0.55, False, 0.7)
            x += cw + 0.6
        if broken:
            _chain(s, _sag(12, 46, x - 3, 54, 10, 8), 4.0, IRON_DARK, 1.3, IRON_HI)
        return s

    def _rubble(self, seed: int) -> Svg:
        """Broken crust slabs leaning on each other (no glow: never mistaken for a creature)."""
        r = Rand(seed)
        s = Svg(50, 26)
        slabs = [((4, 26), (10, 12), (24, 9), (26, 26)), ((20, 26), (24, 6), (38, 4), (44, 26)), ((34, 26), (38, 15), (47, 17), (48, 26))]
        for i, pts in enumerate(slabs):
            top = min(py for _, py in pts)
            s.polygon(pts, fill=s.linear(0, top, 0, 26, [(0, CRUST_TOP if i != 1 else "#a68a7c"), (0.5, CRUST), (1, CRUST_LOW)]), stroke=INK, width=1.1)
            (ax, ay), (bx, by) = pts[1], pts[2]
            s.line(ax + 0.8, ay + 1, bx - 0.8, by + 1, CRUST_HI, 1.0, 0.7)
        for _ in range(3):
            px = r.uniform(4, 46)
            s.ellipse(px, 24.5, r.uniform(1.5, 2.6), 1.4, fill=CRUST_LOW, stroke=INK, width=0.6)
        return s

    def _brazier(self) -> Svg:
        s = Svg(40, 66)
        _halo(s, 20, 20, 22, MAGMA_ORANGE, 0.55)
        s.polygon([(13, 66), (17, 38), (23, 38), (27, 66)], fill=s.linear(13, 0, 27, 0, [(0, IRON_HI), (1, IRON_DEEP)]), stroke=INK, width=1.0)
        s.path(rounded_rect_path(9, 62, 22, 4, 1.5), fill=IRON_DARK, stroke=INK, width=0.9)
        s.path(rounded_rect_path(15, 44, 10, 4, 1), fill=IRON, stroke=INK, width=0.7)
        _flame(s, 20, 28, 20, 28, seed=1.3)
        s.path("M5 26 L35 26 L30 38 Q20 42 10 38 Z", fill=s.linear(5, 0, 35, 0, [(0, IRON_HI), (0.4, IRON), (1, IRON_DEEP)]), stroke=INK, width=1.2)
        s.path("M6 26.5 L34 26.5", stroke=MAGMA_YELLOW, width=1.4)
        for x in (11, 20, 29):
            s.circle(x, 32, 1.2, fill="#e8e6f0")
        for x in (8, 32):
            s.polygon([(x - 2, 26), (x, 21), (x + 2, 26)], fill=IRON, stroke=INK, width=0.6)
        return s

    def _chain_posts(self) -> Svg:
        s = Svg(120, 48)
        for x in (10, 110):
            s.path(rounded_rect_path(x - 4, 12, 8, 36, 1.5), fill=s.linear(x - 4, 0, x + 4, 0, [(0, IRON_HI), (1, IRON_DEEP)]), stroke=INK, width=1.0)
            s.polygon([(x - 5, 13), (x, 3), (x + 5, 13)], fill=s.linear(0, 3, 0, 13, [(0, MAGMA_YELLOW), (0.4, MAGMA_ORANGE), (1, IRON_DARK)]),
                      stroke=INK, width=0.9)
            s.rect(x - 5, 18, 10, 3, fill=IRON_DARK, stroke=INK, width=0.6)
        _chain(s, _sag(14, 20, 106, 20, 14, 12), 5, IRON_DARK, 1.6, IRON_HI)
        _chain(s, _sag(14, 32, 106, 32, 8, 12), 5, IRON_DARK, 1.6, IRON_HI)
        return s

    def _totem(self, seed: int) -> Svg:
        """Warning stele: a carved basalt slab with a glowing chevron-and-flame glyph."""
        s = Svg(36, 80)
        s.path("M6 80 L8 18 Q18 4 28 18 L30 80 Z", fill=s.linear(6, 0, 30, 0, [(0, "#6e5864"), (0.4, "#4c3a46"), (1, "#2c1e28")]), stroke="#26141f",
               width=1.3)
        s.path("M8 18 Q18 4 28 18", stroke=CRUST_HI, width=1.2, opacity=0.7)
        _halo(s, 18, 40, 16, MAGMA_ORANGE, 0.5)
        for k, y in enumerate((26, 34)):
            _glow_line(s, f"M11 {y + 6} L18 {y} L25 {y + 6}", 0.75, True, 1.0 - k * 0.25)
        s.path("M18 44 Q22 50 19.5 56 Q18 58 16.5 56 Q14 50 18 44 Z", fill=MAGMA_YELLOW, stroke=MAGMA_RED, width=0.8)
        s.rect(4, 74, 28, 6, fill=IRON_DARK, stroke=INK, width=1.0, rx=1.5)
        for x in (9, 18, 27):
            s.circle(x, 77, 1.1, fill="#e8e6f0")
        if seed % 2:
            _chain(s, _sag(8, 62, 30, 64, 6, 6), 3.6, IRON_DARK, 1.0, IRON_HI)
        return s

    def _obsidian(self) -> Svg:
        """Low cluster of glassy obsidian chunks (blocky, never spiky: not a hazard)."""
        s = Svg(58, 30)
        _halo(s, 29, 26, 22, MAGMA_ORANGE, 0.25)
        chunks = [(12, 10, 9), (28, 16, 13), (44, 11, 10), (36, 7, 7)]
        for cx, half, tall in chunks:
            base = 29.0
            top = base - tall
            pts = [(cx - half, base), (cx - half * 0.9, top + tall * 0.35), (cx - half * 0.35, top), (cx + half * 0.5, top + 1.5),
                   (cx + half, top + tall * 0.45), (cx + half * 0.95, base)]
            s.polygon(pts, fill=s.linear(cx - half, top, cx + half, base, [(0, OBSIDIAN_HI), (0.45, OBSIDIAN), (1, OBSIDIAN_DARK)]),
                      stroke=INK, width=1.0)
            s.polygon([(cx - half * 0.9, top + tall * 0.35), (cx - half * 0.35, top), (cx + half * 0.5, top + 1.5), (cx, top + tall * 0.45)],
                      fill="#ffffff", opacity=0.1)
            s.line(cx - half * 0.3, top + 1.2, cx + half * 0.45, top + 2.4, "#c8b0f0", 0.9, 0.7)
            s.line(cx + half * 0.6, top + tall * 0.5, cx + half * 0.5, base - 2, "#ff9a5a", 0.9, 0.6)
        return s

    def _steam_vent(self) -> Svg:
        s = Svg(64, 96)
        for cx, cy, rx, ry, op in ((32, 62, 8, 10, 0.5), (30, 48, 12, 11, 0.42), (35, 33, 15, 12, 0.32), (29, 18, 18, 13, 0.22), (34, 8, 16, 8, 0.12)):
            _soft(s, cx, cy, rx, ry, "#efe2e8", op, 0.25)
        _halo(s, 32, 76, 18, MAGMA_ORANGE, 0.5)
        s.path("M6 96 Q12 80 22 74 L42 74 Q52 80 58 96 Z", fill=s.linear(0, 74, 0, 96, [(0, CRUST_TOP), (0.5, CRUST), (1, BASALT_DARK)]),
               stroke=INK, width=1.2)
        s.ellipse(32, 75, 10, 3, fill=s.radial(32, 75, 10, [(0, MAGMA_WHITE), (0.5, MAGMA_ORANGE), (1, MAGMA_RED)]), stroke=INK, width=0.9)
        _glow_line(s, "M18 84 L22 90 L20 95", 0.5, True, 0.8)
        _glow_line(s, "M45 82 L42 88 L45 94", 0.5, True, 0.8)
        s.path("M12 86 Q22 78 32 80", stroke=CRUST_HI, width=1.0, opacity=0.6)
        return s

    def _banner(self, seed: int) -> Svg:
        s = Svg(44, 124)
        s.path(rounded_rect_path(19, 4, 5, 120, 2), fill=s.linear(19, 0, 24, 0, [(0, IRON_HI), (1, IRON_DEEP)]), stroke=INK, width=1.0)
        s.polygon([(16.5, 6), (21.5, -1), (26.5, 6)], fill=MAGMA_ORANGE, stroke=INK, width=0.8)
        s.path(rounded_rect_path(5, 12, 34, 4, 1.5), fill=IRON, stroke=INK, width=0.8)
        sway = 2.5 if seed % 2 else -2.0
        s.path(f"M7 16 L37 16 L{37 + sway} 70 L22 62 L{7 + sway} 70 Z", fill=s.linear(0, 16, 0, 70, [(0, BANNER), (1, BANNER_DARK)]),
               stroke=INK, width=1.1)
        s.path(f"M10 19 L34 19", stroke="#d06a5a", width=1.0, opacity=0.6)
        s.polygon(star_points(22 + sway * 0.4, 38, 8, 3, 4), fill="#ffb060", stroke="#6a1a10", width=0.9)
        s.circle(22 + sway * 0.4, 38, 2.2, fill=MAGMA_WHITE)
        s.rect(15, 118, 14, 6, fill=IRON_DARK, stroke=INK, width=0.9, rx=1.5)
        return s

    def props(self) -> dict[str, PropSpec]:
        return {
            "basalt_pillar": PropSpec(lambda: self._pillar(5), (40, 99)),
            "basalt_pillar_b": PropSpec(lambda: self._pillar(12, broken=True), (40, 99)),
            "brazier": PropSpec(self._brazier, (20, 65)),
            "chain_posts": PropSpec(self._chain_posts, (60, 47)),
            "totem": PropSpec(lambda: self._totem(2), (18, 79)),
            "totem_b": PropSpec(lambda: self._totem(3), (18, 79)),
            "obsidian": PropSpec(self._obsidian, (29, 29)),
            "steam_vent": PropSpec(self._steam_vent, (32, 95)),
            "banner": PropSpec(lambda: self._banner(1), (22, 123)),
            "rubble": PropSpec(lambda: self._rubble(6), (25, 25)),
        }

    def auto_decor(self, rng, surface_w: float):
        out = []
        x = rng.uniform(40, 120)
        while x < surface_w - 30:
            roll = rng.next()
            if roll < 0.2:
                out.append((rng.choice(["obsidian", "rubble"]), x, rng.uniform(0.7, 1.0), "back"))
            elif roll < 0.36:
                out.append(("brazier", x, rng.uniform(0.9, 1.05), "back"))
            elif roll < 0.52:
                out.append((rng.choice(["basalt_pillar", "basalt_pillar_b"]), x, rng.uniform(0.8, 1.05), "back"))
            elif roll < 0.62:
                out.append(("steam_vent", x, rng.uniform(0.8, 1.0), "back"))
            elif roll < 0.72:
                out.append((rng.choice(["totem", "totem_b"]), x, rng.uniform(0.85, 1.0), "back"))
            elif roll < 0.8:
                out.append(("chain_posts", x, rng.uniform(0.85, 1.0), "back"))
            elif roll < 0.87 and surface_w > 300:
                out.append(("banner", x, rng.uniform(0.9, 1.0), "back"))
            x += rng.uniform(110, 230)
        return out

    def weather(self) -> Weather:
        return Weather("embers", 0.7, ("soft", "soft", "sparkle"), wind=-12.0)


ART_CLASS = VolcanicFortress
