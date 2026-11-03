"""Costa dos Corais: a bright tropical coast, tide pools, coral reefs and a sunken galleon.

Identity: late-morning light. A warm sun stands high in the upper left of a
turquoise-to-azure sky and lays a glittering path on the sea; distant green
islands, sea stacks and small sailboats sit on the horizon; warm sandstone
headlands carry a red-and-white lighthouse, a keeper's cottage and a wooden
pier; beach dunes with sea oats, sea-grape bushes and spray-washed rocks frame
the foreground. Terrain is layered sandstone (salmon, ochre and rose bands
with cross-bedding, tafoni pockets and fossil shells) under a wet golden-sand
cap with a lacy foam line and shells lying on it; style ``reef`` is living
coral rock (brain corals, anemones, coralline crusts) for underwater areas;
slippery floors (``surface == "ice"``) get a glossy green algae mat. Indoors:
deep water with god-rays and kelp, the hull of a listing galleon, and a sea
cave lit by teal water reflections. Light always comes from the upper left.

Level art variants: ``interior()`` answers "underwater"/"reef"/"depths" (deep
water with kelp) and "ship"/"galleon"/"wreck"/"fortress" (the sunken hull);
when the level's ``art.variant`` is one of ``SEA_VARIANTS`` the automatic decor
grows kelp, sea fans and rocks instead of palms, dune plants and driftwood.
"""

from __future__ import annotations

import math
from typing import Callable, Sequence

from ..svg import Rand, Svg, blob, mix, rounded_rect_path, shade, smooth_closed, smooth_open, star_points
from .base import Layer, PropSpec, Weather, WorldArt

Pt = tuple[float, float]

INK = "#2b1d2c"
SUN = (214.0, 104.0)
HORIZON = 300.0
# golden sand cap: highlight → wet underside
SAND_HI, SAND_TOP, SAND, SAND_WET, SAND_LOW, SAND_LINE = "#fff4cf", "#f6d995", "#e9bd72", "#cf9a58", "#b67f47", "#7e5130"
# layered sandstone body
STONE_TOP, STONE, STONE_LOW, STONE_DEEP, STONE_LINE = "#ebb88f", "#d99673", "#b8735f", "#7c4848", "#5a3236"
STRATA = ("#f6cfa2", "#e98f7c", "#dcb276", "#c98078", "#f4dcb0", "#c4866a")
# living reef rock
REEF_TOP, REEF, REEF_LOW, REEF_DEEP, REEF_LINE = "#e39aae", "#b66d90", "#7b4b7a", "#3a2a58", "#2c1c3c"
CORAL, CORAL_ORANGE, VIOLET, ALGAE, TURQUOISE, DEEP = "#ff7f6b", "#ffa94d", "#9a6ad6", "#4f9a6a", "#3fb7c4", "#1d4e7a"
WOOD_LIGHT, WOOD, WOOD_DARK = "#b88a5c", "#7a5a3a", "#4a3222"
DRIFT_HI, DRIFT, DRIFT_DARK = "#eee6d6", "#bdb09c", "#7f7262"
BRASS_HI, BRASS, BRASS_DARK = "#f6dc94", "#c9a35b", "#7f5f2a"
COPPER_HI, COPPER, COPPER_DARK = "#ffcfa4", "#c8774a", "#73391f"
PATINA_HI, PATINA, PATINA_DARK, PATINA_DEEP = "#a6ecd4", "#52b49b", "#2f7a6c", "#173f3c"
LEAF_HI, LEAF, LEAF_DARK, LEAF_LINE = "#b6ea78", "#5cae52", "#2f7a46", "#1c4a30"
ROCK_HI, ROCK, ROCK_DARK = "#d9cab6", "#a8937f", "#62544c"
GLOW = "#ffd682"
# level art variants whose main area is mostly sea floor: auto decor avoids palms,
# dune plants, driftwood and buoys there and grows kelp and corals instead
SEA_VARIANTS = frozenset({"underwater", "depths", "deep", "reef", "maze", "sea"})


# --------------------------------------------------------------------------- helpers
def _hash(n: int, salt: int = 0) -> float:
    """Stable pseudo-random value in [0, 1] for an integer lattice cell."""
    x = (n * 374761393 + salt * 668265263 + 1013904223) & 0xFFFFFFFF
    x = ((x ^ (x >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((x ^ (x >> 16)) & 0xFFFFFF) / float(0xFFFFFF)


def _wobble(gx: float, k: float) -> float:
    return math.sin(gx * 0.071 + k) * 0.6 + math.sin(gx * 0.023 + 2 * k) * 0.4


def _pick(options: Sequence[str], n: int) -> str:
    """Deterministic pick from ``options`` for a world-aligned cell ``n``."""
    return options[int(_hash(n, 97) * len(options)) % len(options)]


def _line(pts: Sequence[Pt]) -> str:
    return "M" + "L".join(f"{x:.2f} {y:.2f}" for x, y in pts)


def _poly(pts: Sequence[Pt]) -> str:
    return _line(pts) + "Z"


def _samples(w: float, step: float = 2.0) -> list[float]:
    n = max(2, int(math.ceil(w / step)))
    return [w * i / n for i in range(n + 1)]


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


def _slots(x0: float, w: float, step: float, margin: float = 0.0) -> range:
    """World-aligned cell indices of size ``step`` touching [x0 - margin, x0 + w + margin]."""
    return range(math.floor((x0 - margin) / step), math.floor((x0 + w + margin) / step) + 1)


def _sparkle(s: Svg, x: float, y: float, size: float, opacity: float = 0.95, color: str = "#ffffff") -> None:
    s.polygon(star_points(x, y, size, size * 0.24, 4), fill=color, opacity=opacity)


def _soft(s: Svg, cx: float, cy: float, rx: float, ry: float, color: str, alpha: float = 1.0, core: float = 0.0) -> None:
    """Soft-edged ellipse: a radial falloff stretched by a scaled group."""
    with s.group(transform=f"translate({cx:.2f} {cy:.2f}) scale(1 {ry / rx:.4f})"):
        s.circle(0, 0, rx, fill=s.radial(0, 0, rx, [(0, color, alpha), (core, color, alpha), (1, color, 0)]))


def _ease_profile(keys: Sequence[Pt], xs: Sequence[float]) -> list[float]:
    """Height profile through key points with eased (cosine) segments."""
    out = []
    for x in xs:
        if x <= keys[0][0]:
            out.append(keys[0][1])
            continue
        if x >= keys[-1][0]:
            out.append(keys[-1][1])
            continue
        for (ax, ay), (bx, by) in zip(keys, keys[1:]):
            if ax <= x <= bx:
                t = (x - ax) / (bx - ax) if bx > ax else 0.0
                out.append(ay + (by - ay) * (1 - math.cos(math.pi * t)) / 2)
                break
    return out


# --------------------------------------------------------------------------- small shore things
def _scallop(s: Svg, cx: float, base: float, size: float, tone: str, tilt: float = 0.0, line: str = INK, width: float = 0.5) -> None:
    """Fan shell resting on its hinge at (cx, base); ribs radiate from the hinge."""
    rim = []
    for i in range(11):
        a = math.radians(-168 + 156 * i / 10 + tilt)
        rad = size * (1.0 if i % 2 == 0 else 0.9)
        rim.append((cx + math.cos(a) * rad, base + math.sin(a) * rad * 0.92))
    ear = [(cx + size * 0.3, base + size * 0.04), (cx + size * 0.18, base + size * 0.18), (cx - size * 0.18, base + size * 0.18),
           (cx - size * 0.3, base + size * 0.04)]
    s.path(smooth_closed(rim + ear, 0.35), fill=s.linear(cx - size, base - size, cx + size, base,
                                                         [(0, shade(tone, 0.55)), (0.5, tone), (1, shade(tone, -0.22))]),
           stroke=line, width=width)
    for px, py in rim[2:-2:2]:
        s.line(cx, base + size * 0.06, cx + (px - cx) * 0.86, base + (py - base) * 0.86, shade(tone, -0.35), max(0.3, width * 0.9), 0.75)


def _conch(s: Svg, cx: float, base: float, size: float, tone: str, flip: bool = False, line: str = INK, width: float = 0.5) -> None:
    """Spiral shell lying on its side: a cone with spiral bands and a pink lip."""
    d = -1.0 if flip else 1.0
    pts = [(cx - size * 1.05 * d, base - size * 0.2), (cx - size * 0.75 * d, base - size * 0.62), (cx - size * 0.1 * d, base - size * 0.78),
           (cx + size * 0.55 * d, base - size * 0.5), (cx + size * 1.25 * d, base - size * 0.12), (cx + size * 0.5 * d, base + size * 0.02),
           (cx - size * 0.6 * d, base + size * 0.05)]
    s.path(smooth_closed(pts, 0.6), fill=s.linear(cx, base - size * 0.8, cx, base, [(0, shade(tone, 0.5)), (0.55, tone), (1, shade(tone, -0.25))]),
           stroke=line, width=width)
    for k in (0.15, 0.45, 0.75):
        x = cx + size * (1.15 - 1.4 * k) * d
        s.path(f"M{x:.2f} {base - size * (0.15 + 0.45 * (1 - k)):.2f} Q{x - size * 0.25 * d:.2f} {base - size * 0.35:.2f} {x - size * 0.08 * d:.2f} "
               f"{base - size * 0.02:.2f}", stroke=shade(tone, -0.4), width=max(0.3, width * 0.8), opacity=0.7)
    s.path(blob(cx - size * 0.62 * d, base - size * 0.3, size * 0.32, size * 0.22, 0.1, seed=cx), fill="#ffc2b4", opacity=0.9)


def _starfish(s: Svg, cx: float, cy: float, size: float, tone: str, angle: float = 0.0, line: str = INK, width: float = 0.5) -> None:
    pts = star_points(cx, cy, size, size * 0.42, 5, -90 + angle)
    s.path(smooth_closed(pts, 0.5), fill=s.radial(cx - size * 0.3, cy - size * 0.35, size * 1.4,
                                                  [(0, shade(tone, 0.4)), (0.55, tone), (1, shade(tone, -0.3))]), stroke=line, width=width)
    for k in range(5):
        a = math.radians(-90 + angle + k * 72)
        for j in (0.32, 0.6):
            s.circle(cx + math.cos(a) * size * j, cy + math.sin(a) * size * j, max(0.25, size * 0.075), fill=shade(tone, 0.55), opacity=0.95)


def _barnacle(s: Svg, x: float, y: float, size: float) -> None:
    """Tiny barnacle cone sitting on a surface at (x, y)."""
    s.path(f"M{x - size:.2f} {y:.2f} L{x - size * 0.45:.2f} {y - size * 0.9:.2f} L{x + size * 0.45:.2f} {y - size * 0.9:.2f} L{x + size:.2f} {y:.2f} Z",
           fill=s.linear(x - size, 0, x + size, 0, [(0, "#f4efe4"), (1, "#a59a8e")]), stroke="#4a4048", width=max(0.3, size * 0.18))
    s.ellipse(x, y - size * 0.9, size * 0.42, size * 0.16, fill="#3a3038")


def _frond(s: Svg, cx: float, cy: float, ang: float, length: float, droop: float, width: float, colors: tuple[str, str, str],
           leaflets: int = 16, rib: str = "#e2eea0") -> None:
    """Arching coconut-palm frond: tapered leaflets hanging from a drooping midrib."""
    a = math.radians(ang)
    dx, dy = math.cos(a), math.sin(a)
    mid = [(cx + dx * length * t + 0.0, cy + dy * length * t + droop * length * t * t) for t in [i / leaflets for i in range(leaflets + 1)]]
    dark, light, edge = colors
    for side, tone in ((1, dark), (-1, light)):
        for i in range(1, leaflets + 1):
            px, py = mid[i]
            qx, qy = mid[min(i + 1, leaflets)][0] - mid[i - 1][0], mid[min(i + 1, leaflets)][1] - mid[i - 1][1]
            ln = math.hypot(qx, qy) or 1.0
            tx, ty = qx / ln, qy / ln
            nx, ny = -ty, tx
            if ny > 0:
                nx, ny = -nx, -ny
            t = i / leaflets
            ll = width * (0.35 + 0.95 * math.sin(math.pi * min(1.0, t * 0.92 + 0.08))) * (1.0 if side > 0 else 1.2)
            # leaflets point outward, sweep back toward the trunk and hang down
            ox = nx * side * 0.55 - tx * 0.45
            oy = ny * side * 0.55 - ty * 0.45 + 0.75
            on = math.hypot(ox, oy) or 1.0
            ex, ey = px + ox / on * ll, py + oy / on * ll
            bw = max(0.8, width * 0.12)
            s.path(f"M{px - tx * bw:.2f} {py - ty * bw:.2f} Q{(px + ex) / 2 + nx * bw:.2f} {(py + ey) / 2 + ny * bw:.2f} {ex:.2f} {ey:.2f} "
                   f"Q{(px + ex) / 2 - nx * bw * 0.4:.2f} {(py + ey) / 2 - ny * bw * 0.4:.2f} {px + tx * bw:.2f} {py + ty * bw:.2f} Z",
                   fill=tone, stroke=edge, width=0.45)
    s.path(smooth_open(mid), stroke=edge, width=2.2)
    s.path(smooth_open(mid), stroke=rib, width=1.0, opacity=0.9)


def _palm_silhouette(s: Svg, x: float, base: float, hgt: float, lean: float, trunk: str, leaf: str, leaf_dark: str) -> None:
    """Simplified coconut palm for the parallax layers (no outline)."""
    tx, ty = x + lean, base - hgt
    s.path(f"M{x - hgt * 0.035:.2f} {base:.2f} Q{x + lean * 0.15:.2f} {base - hgt * 0.5:.2f} {tx - hgt * 0.02:.2f} {ty:.2f} "
           f"L{tx + hgt * 0.02:.2f} {ty:.2f} Q{x + lean * 0.15 + hgt * 0.045:.2f} {base - hgt * 0.5:.2f} {x + hgt * 0.035:.2f} {base:.2f} Z", fill=trunk)
    for k, ang in enumerate((-160, -128, -96, -60, -22, 12, 168, 196)):
        a = math.radians(ang)
        ln = hgt * (0.42 if k not in (0, 7) else 0.34)
        droop = 0.55 if abs(math.cos(a)) > 0.5 else 0.25
        pts_u, pts_l = [], []
        for i in range(9):
            t = i / 8
            px = tx + math.cos(a) * ln * t
            py = ty + math.sin(a) * ln * t + droop * ln * t * t
            wd = hgt * 0.07 * math.sin(math.pi * min(1.0, t * 1.05)) ** 0.7
            pts_u.append((px, py - wd * (1.0 if i % 2 else 0.5)))
            pts_l.append((px, py + wd * (1.3 if i % 2 == 0 else 0.6)))
        s.path(_poly(pts_u + list(reversed(pts_l))), fill=leaf if k % 2 else leaf_dark)


def _seagrape_clump(s: Svg, bx: float, by: float, size: float, r: Rand, hazy: bool = False, line: str | None = None) -> None:
    """Sea-grape bush: a dark mass under round leathery leaves with red veins."""
    greens = ("#6fae78", "#7cb882", "#5f9e6e", "#8cc48a") if hazy else ("#5fae5a", "#4a9a50", "#78be5e", "#3f8a4a", "#6aaa52")
    s.path(blob(bx, by - size * 0.42, size * 0.95, size * 0.5, 0.12, seed=bx), fill="#4a7e5a" if hazy else "#2f6a3a")
    leaves = []
    for _ in range(int(9 + size * 0.35)):
        a = r.uniform(math.pi * 1.0, math.pi * 2.0)
        d = r.uniform(0.2, 1.0)
        leaves.append((bx + math.cos(a) * size * 0.85 * d, by - size * 0.2 + math.sin(a) * size * 0.75 * d, size * r.uniform(0.17, 0.26),
                       r.uniform(-0.9, 0.9)))
    leaves.sort(key=lambda q: -q[1])
    for i, (lx, ly, rr, tilt) in enumerate(leaves):
        tone = r.choice(greens) if i % 9 else ("#c9a070" if hazy else "#c8603a")
        ct, st = math.cos(tilt), math.sin(tilt)
        pts = []
        for k in range(12):
            a = 2 * math.pi * k / 12 + math.pi / 2
            rad = rr * (0.72 if k == 0 else 1.0)  # notch where the stalk joins
            ex, ey = math.cos(a) * rad, math.sin(a) * rad * 0.86
            pts.append((lx + ex * ct - ey * st, ly + ex * st + ey * ct))
        s.path(smooth_closed(pts, 0.9), fill=s.radial(lx - rr * 0.35, ly - rr * 0.4, rr * 1.6, [(0, shade(tone, 0.4)), (0.6, tone), (1, shade(tone, -0.22))]),
               stroke=line, width=0.8)
        vein = "#c8583a" if not hazy else "#b88070"
        sx, sy = lx - st * rr * 0.62, ly + ct * rr * 0.62  # stalk end of the leaf
        for va in (-0.75, 0.0, 0.75):
            ex, ey = lx + math.sin(tilt + va) * rr * 0.7, ly - math.cos(tilt + va) * rr * 0.7
            s.line(sx, sy, ex, ey, vein, max(0.45, rr * 0.07), 0.7)


def _splash(s: Svg, x: float, y: float, size: float, r: Rand) -> None:
    """Wave breaking on a rock: a crown of white tongues and flying droplets."""
    s.path(blob(x, y - size * 0.12, size * 0.75, size * 0.22, 0.25, seed=x), fill="#ffffff", opacity=0.85)
    for k in range(6):
        a = math.radians(-160 + k * 28 + r.uniform(-6, 6))
        ln = size * r.uniform(0.55, 1.0)
        ex, ey = x + math.cos(a) * ln, y - size * 0.15 + math.sin(a) * ln
        nx, ny = -math.sin(a) * size * 0.11, math.cos(a) * size * 0.11
        s.path(f"M{x + nx:.1f} {y - size * 0.15 + ny:.1f} Q{(x + ex) / 2 + nx * 1.6:.1f} {(y + ey) / 2 + ny * 1.6:.1f} {ex:.1f} {ey:.1f} "
               f"Q{(x + ex) / 2 - nx * 1.6:.1f} {(y + ey) / 2 - ny * 1.6:.1f} {x - nx:.1f} {y - size * 0.15 - ny:.1f} Z", fill="#ffffff",
               opacity=r.uniform(0.6, 0.9))
        s.circle(ex + math.cos(a) * size * 0.18, ey + math.sin(a) * size * 0.18, size * r.uniform(0.04, 0.08), fill="#ffffff", opacity=0.85)


# --------------------------------------------------------------------------- world
class CoralCoast(WorldArt):
    id = "coral_coast"
    name = "Costa dos Corais"
    accent = "#ff7f6b"
    terrain_headroom = 12.0
    vignette = 0.24
    provisional = False

    # ------------------------------------------------------------------ sky
    def sky(self) -> Svg:
        s = Svg(960, 540)
        H = HORIZON
        r = Rand(5)
        s.rect(0, 0, 960, H + 1, fill=s.linear(0, 0, 0, H, [(0, "#2a7ed2"), (0.3, "#3d9fe0"), (0.66, "#74c9ea"), (0.9, "#b9e9f0"),
                                                          (1, "#e2f6f1")]))
        sx, sy = SUN
        s.circle(sx, sy, 330, fill=s.radial(sx, sy, 330, [(0, "#fffbea", 0.55), (0.3, "#fff8de", 0.18), (1, "#fff8de", 0)]))
        for k in range(8):
            a = math.radians(-4 + k * 12)
            s.polygon([(sx, sy), (sx + math.cos(a - 0.025) * 620, sy + math.sin(a - 0.025) * 620),
                       (sx + math.cos(a + 0.025) * 620, sy + math.sin(a + 0.025) * 620)], fill="#fffbe6", opacity=0.05)
        s.circle(sx, sy, 76, fill=s.radial(sx, sy, 76, [(0, "#ffffff", 0.95), (0.4, "#fffbe8", 0.4), (1, "#fff3c8", 0)]))
        s.circle(sx, sy, 29, fill=s.radial(sx - 7, sy - 7, 36, [(0, "#ffffff"), (0.65, "#fffdf3"), (1, "#ffeebd")]))
        # a low bank of distant cumulus resting on the horizon (its foot is hidden by the sea)
        x = -30.0
        bank = s.linear(0, H - 46, 0, H, [(0, "#ffffff", 0.95), (0.6, "#eaf7fa", 0.85), (1, "#cfe9ef", 0.8)])
        while x < 990:
            rad = r.uniform(12, 30) * (1.25 if 560 < x < 900 else 1.0)
            s.path(blob(x, H - rad * 0.32, rad * 1.25, rad, 0.08, seed=x), fill=bank)
            x += r.uniform(26, 54)
        # the sea
        s.rect(0, H, 960, 540 - H, fill=s.linear(0, H, 0, 540, [(0, "#2a7cbc"), (0.1, "#2c8cc4"), (0.42, "#2aa6c4"), (1, "#38c1bd")]))
        _soft(s, sx, H + 64, 190, 70, "#c9f6f2", 0.32, 0.0)
        s.rect(0, H - 2.5, 960, 6, fill=s.linear(0, H - 2.5, 0, H + 3.5, [(0, "#f4fcf8", 0), (0.5, "#f4fcf8", 0.85), (1, "#f4fcf8", 0)]))
        # swell lines, spaced by perspective
        rows = 24
        for i in range(rows):
            t = (i + 0.5) / rows
            y = H + 4 + (540 - H - 6) * t ** 1.6
            for _ in range(5 + int(4 * t)):
                x0 = r.uniform(-60, 960)
                ln = 16 + 150 * t ** 1.4 * r.uniform(0.5, 1.2)
                s.line(x0, y, x0 + ln, y + r.uniform(-0.6, 0.6), "#a6e6ee", 0.5 + 1.5 * t, r.uniform(0.18, 0.36))
                s.line(x0 + ln * 0.2, y + 1.2 + 2 * t, x0 + ln * 0.85, y + 1.2 + 2 * t, "#1f6f9e", 0.4 + 1.0 * t, 0.16)
        # the glittering path under the sun: a widening wedge of broken highlights
        for i in range(64):
            t = ((i + 0.5) / 64) ** 1.4
            y = H + 2 + (540 - H - 4) * t + r.uniform(-1.5, 1.5)
            spread = 20 + 200 * t
            for _ in range(2 + int(7 * t)):
                off = (r.next() + r.next() + r.next() - 1.5) / 1.5
                x = sx + off * spread
                ln = 3 + 22 * t * r.uniform(0.4, 1.2)
                s.path(f"M{x - ln / 2:.1f} {y:.1f} Q{x:.1f} {y - 0.8 - t:.1f} {x + ln / 2:.1f} {y:.1f}", stroke="#fffbe6", width=0.6 + 1.3 * t,
                       opacity=max(0.12, 0.92 * (1 - abs(off)) ** 1.3))
        for _ in range(16):
            t = r.uniform(0.05, 0.9)
            y = H + 4 + (540 - H) * t ** 1.4
            _sparkle(s, sx + (r.next() - 0.5) * (30 + 160 * t), y, 2.0 + 3.5 * t, 0.9)
        return s

    def _cumulus(self, seed: int, w: float, h: float) -> Svg:
        """Light trade-wind cumulus: a flat base, a bulging tower and sunlit lobes."""
        r = Rand(seed)
        s = Svg(w, h)
        base = h * 0.84
        lobes = []
        n = 7
        for i in range(n):
            t = i / (n - 1)
            tower = math.sin(math.pi * (0.15 + 0.7 * t)) ** 1.6
            rad = h * (0.15 + 0.22 * tower) + r.uniform(-2.5, 2.5)
            lobes.append((w * (0.12 + 0.76 * t) + r.uniform(-5, 5), base - rad * (0.5 + 0.45 * tower), rad))
        for _ in range(3):
            rad = h * r.uniform(0.15, 0.2)
            lobes.append((w * r.uniform(0.32, 0.6), base - h * r.uniform(0.5, 0.62), rad))
        for cx, cy, rad in lobes:
            s.path(blob(cx + 4, cy + 5, rad, rad * 0.92, 0.05, seed=cx), fill="#93c4dc", opacity=0.3)
        body = s.linear(0, base - h * 0.85, 0, base + 3, [(0, "#ffffff"), (0.55, "#f4fbfd"), (0.82, "#d9edf4"), (1, "#b5d8e6")])
        for cx, cy, rad in lobes:
            s.path(blob(cx, cy, rad, rad * 0.92, 0.05, seed=cx), fill=body)
        s.path(f"M{w * 0.08:.1f} {base:.1f} Q{w * 0.5:.1f} {base + 6:.1f} {w * 0.92:.1f} {base:.1f} L{w * 0.9:.1f} {base - 8:.1f} "
               f"L{w * 0.1:.1f} {base - 8:.1f} Z", fill="#cfe6ef")
        for cx, cy, rad in lobes:
            s.circle(cx - rad * 0.3, cy - rad * 0.32, rad * 0.45, fill="#ffffff", opacity=0.7)
            s.path(f"M{cx - rad * 0.85:.1f} {cy - rad * 0.1:.1f} Q{cx - rad * 0.7:.1f} {cy - rad * 0.75:.1f} {cx:.1f} {cy - rad * 0.88:.1f}",
                   stroke="#fffbe8", width=1.6, opacity=0.8)
        return s

    def sky_extras(self) -> dict[str, PropSpec]:
        return {
            f"cc.cloud.{i}": PropSpec((lambda i=i, w=w, h=h: self._cumulus(19 + i * 13, w, h)), (0, 0))
            for i, (w, h) in enumerate([(230, 88), (170, 66), (290, 104)])
        }

    # ------------------------------------------------------------------ parallax layers
    def _island(self, s: Svg, x: float, wl: float, wid: float, hgt: float, seed: int, palms: int) -> None:
        """Distant green island: a hazy hump with a pale beach and a reflection."""
        r = Rand(seed)
        n = 24
        pts = []
        for i in range(n + 1):
            t = i / n
            bump = 0.78 + 0.22 * math.sin(t * 9.0 + seed) + 0.1 * math.sin(t * 23 + seed * 2)
            pts.append((x - wid / 2 + wid * t, wl - hgt * math.sin(math.pi * t) ** 0.85 * bump))
        s.path(_poly(pts + [(x + wid / 2, wl + 1), (x - wid / 2, wl + 1)]),
               fill=s.linear(0, wl - hgt, 0, wl, [(0, "#6aa898"), (0.6, "#86baae"), (1, "#a6cfc6")]))
        s.path(_line(pts[2:n // 2]), stroke="#b6dcc6", width=1.2, opacity=0.6)
        for _ in range(palms):
            px = x + r.uniform(-wid * 0.3, wid * 0.3)
            t = (px - (x - wid / 2)) / wid
            top = wl - hgt * math.sin(math.pi * t) ** 0.85 * 0.9
            _palm_silhouette(s, px, top + 1, r.uniform(12, 18), r.uniform(-4, 4), "#6a948e", "#76aa98", "#62948a")
        s.path(f"M{x - wid / 2 + 4:.1f} {wl:.1f} Q{x:.1f} {wl - 2.2:.1f} {x + wid / 2 - 4:.1f} {wl:.1f}", stroke="#efe8c8", width=1.6, opacity=0.8)
        s.path(f"M{x - wid / 2 + 8:.1f} {wl + 2.4:.1f} L{x + wid / 2 - 8:.1f} {wl + 2.4:.1f}", stroke="#2f7aa8", width=2.2, opacity=0.25)
        s.path(f"M{x - wid / 2 + 2:.1f} {wl + 0.6:.1f} L{x + wid / 2 - 2:.1f} {wl + 0.6:.1f}", stroke="#ffffff", width=0.8, opacity=0.7)

    def _stack(self, s: Svg, x: float, wl: float, wid: float, hgt: float, seed: int, arch: bool = False) -> None:
        """Hazy sandstone sea stack (or a natural arch) standing in the sea."""
        r = Rand(seed)
        top = wl - hgt
        lw, rw = wid * 0.5, wid * 0.42
        left = [(x - lw, wl), (x - lw * 0.85, wl - hgt * 0.4), (x - lw * 0.95, wl - hgt * 0.75), (x - lw * 0.7, top + 2)]
        right = [(x + rw * 0.8, top + 1), (x + rw, wl - hgt * 0.6), (x + rw * 0.9, wl - hgt * 0.3), (x + rw * 1.05, wl)]
        s.path(_poly(left + right), fill=s.linear(0, top, 0, wl, [(0, "#c9b0a6"), (1, "#a4b4bc")]))
        s.path(_poly([(x + 1, top + 1)] + right + [(x + 2, wl)]), fill="#7a8a9e", opacity=0.35)
        for k in range(1, 5):
            y = top + hgt * k / 5 + r.uniform(-2, 2)
            s.line(x - lw * 0.85, y, x + rw * 0.85, y + r.uniform(-1, 1), "#8a8a98", 0.8, 0.4)
        s.path(blob(x - 1, top + 1, wid * 0.42, 3.2, 0.2, seed=seed), fill="#6aa28c")
        if arch:
            ax = x + wid * 1.6
            s.path(f"M{x + rw * 0.6:.1f} {top + hgt * 0.3:.1f} Q{(x + ax) / 2:.1f} {top - 2:.1f} {ax + 4:.1f} {top + hgt * 0.38:.1f} L{ax + 6:.1f} {wl:.1f} "
                   f"L{ax - 4:.1f} {wl:.1f} L{ax - 3:.1f} {top + hgt * 0.5:.1f} Q{(x + ax) / 2:.1f} {top + hgt * 0.2:.1f} {x + rw * 0.7:.1f} "
                   f"{top + hgt * 0.55:.1f} Z", fill=s.linear(0, top, 0, wl, [(0, "#c4ada4"), (1, "#a0b2ba")]))
        s.path(f"M{x - lw - 3:.1f} {wl + 0.5:.1f} L{x + rw + 3:.1f} {wl + 0.5:.1f}", stroke="#ffffff", width=1.0, opacity=0.75)

    def _sailboat(self, s: Svg, x: float, wl: float, size: float, stripe: str) -> None:
        s.path(f"M{x - size * 0.6:.2f} {wl - size * 0.16:.2f} L{x + size * 0.6:.2f} {wl - size * 0.16:.2f} L{x + size * 0.42:.2f} {wl:.2f} "
               f"L{x - size * 0.45:.2f} {wl:.2f} Z", fill="#4a5a6e")
        s.line(x, wl - size * 0.16, x, wl - size * 1.3, "#5a6070", 0.6)
        s.polygon([(x + 0.4, wl - size * 1.28), (x + 0.4, wl - size * 0.24), (x + size * 0.66, wl - size * 0.24)], fill="#fdfbf2")
        s.polygon([(x - 0.4, wl - size * 1.05), (x - 0.4, wl - size * 0.26), (x - size * 0.48, wl - size * 0.26)], fill="#eef2f2")
        s.line(x + 0.6, wl - size * 0.62, x + size * 0.36, wl - size * 0.62, stripe, size * 0.1)
        s.path(f"M{x - size * 0.5:.2f} {wl + 1.2:.2f} L{x + size * 0.5:.2f} {wl + 1.2:.2f}", stroke="#ffffff", width=0.7, opacity=0.6)

    def _far(self) -> Svg:
        """Islands, sea stacks and sailboats on the horizon (tiles with itself)."""
        w, h = 1200.0, 160.0
        s = Svg(w, h)
        wl = 132.0
        items: list[tuple[str, float, tuple]] = [
            ("island", 150.0, (260.0, 30.0, 3, 3)), ("stack", 360.0, (16.0, 44.0, 0)), ("boat", 470.0, (9.0, CORAL)),
            ("island", 640.0, (170.0, 20.0, 7, 2)), ("stack", 790.0, (22.0, 58.0, 1)), ("island", 990.0, (300.0, 38.0, 11, 4)),
            ("boat", 1130.0, (7.0, TURQUOISE)), ("boat", 560.0, (6.0, "#ffd36a")),
        ]
        for shift in (-w, 0.0, w):
            for kind, x, args in items:
                xx = x + shift
                if xx + 200 < 0 or xx - 200 > w:
                    continue
                if kind == "island":
                    self._island(s, xx, wl, args[0], args[1], args[2], args[3])
                elif kind == "stack":
                    self._stack(s, xx, wl + 0.5, args[0], args[1], int(x), arch=bool(args[2]))
                else:
                    self._sailboat(s, xx, wl + 2.0, args[0], args[1])
        return s

    def _headland(self, s: Svg, keys: Sequence[Pt], wl: float, seed: int, scrub: bool = True) -> list[Pt]:
        """Hazy sandstone headland through ``keys`` standing in the sea at ``wl``:
        tilted bedding planes, sunlit and shaded faces, scrub on the plateaus and
        surf at the foot. Colours are pushed toward the sky (aerial perspective)
        so gameplay in front always reads first. Returns the top profile."""
        r = Rand(seed)
        x0, x1 = keys[0][0], keys[-1][0]
        n = max(4, int((x1 - x0) / 3))
        xs = [x0 + (x1 - x0) * i / n for i in range(n + 1)]
        base = _ease_profile(keys, xs)
        tops = [y + 0.9 * math.sin(x * 0.37 + seed) + 0.6 * math.sin(x * 0.91 + 1) for x, y in zip(xs, base)]
        tops[0] = tops[-1] = wl + 2
        pts = list(zip(xs, tops))
        top_min = min(tops)
        s.path(_poly(pts + [(x1, wl + 3), (x0, wl + 3)]), fill=s.linear(0, top_min, 0, wl, [(0, "#f4d6c0"), (0.5, "#e2b6a6"), (1, "#c6a0a2")]))
        idx = list(range(n + 1))
        slope = [(base[min(i + 2, n)] - base[max(i - 2, 0)]) / (xs[min(i + 2, n)] - xs[max(i - 2, 0)]) for i in idx]
        for run in _runs(idx, lambda i: slope[i] > 0.5):
            if len(run) > 3:
                face = [pts[i] for i in run]
                s.path(_poly(face + [(face[-1][0] + 4, wl + 2), (face[0][0], wl + 2)]), fill="#6a5a86", opacity=0.24)
        for run in _runs(idx, lambda i: slope[i] < -0.5):
            if len(run) > 3:
                face = [pts[i] for i in run]
                s.path(_poly(face + [(face[-1][0], wl + 2), (face[0][0] - 4, wl + 2)]), fill="#fff8ec", opacity=0.22)
        # tilted bedding planes, broken into ledges, only where the rock is
        k = 0
        y = top_min + 10.0
        tilt = r.uniform(-0.05, 0.05)
        while y < wl - 5:
            def plane(x: float, y: float = y, k: int = k) -> float:
                return y + (x - x0) * tilt + 1.3 * math.sin(x * 0.045 + k * 1.7)
            for run in _runs(xs, lambda x: _ease_profile(keys, [x])[0] + 3 < plane(x)):
                for seg in _runs(run, lambda x, k=k: _hash(int(x / 23) + k * 131, seed) > 0.3):
                    line = [(x, plane(x)) for x in seg]
                    s.path(_line(line), stroke="#a8828a", width=1.0, opacity=0.4)
                    s.path(_line([(x, yy + 1.3) for x, yy in line]), stroke="#fff4ea", width=0.7, opacity=0.35)
            y += r.uniform(8, 17)
            k += 1
        for _ in range(int((x1 - x0) / 55)):
            gx = r.uniform(x0 + 20, x1 - 20)
            gy = _ease_profile(keys, [gx])[0] + 6
            if gy > wl - 16:
                continue
            ln = r.uniform(10, min(46, wl - gy - 4))
            s.path(smooth_open([(gx, gy), (gx + r.uniform(-3, 3), gy + ln * 0.5), (gx + r.uniform(-2, 4), gy + ln)]), stroke="#9a7a86",
                   width=r.uniform(1.0, 2.0), opacity=0.32)
        if scrub:
            for run in _runs(idx, lambda i: abs(slope[i]) < 0.55 and tops[i] < wl - 22):
                cap = [(pts[i][0], pts[i][1] - 2.0 - 1.4 * abs(math.sin(pts[i][0] * 0.21))) for i in run]
                s.path(_poly(cap + [(pts[i][0], pts[i][1] + 4.0) for i in reversed(run)]), fill="#78ae80")
                s.path(_line(cap), stroke="#b6dc9a", width=1.1, opacity=0.8)
                bx = pts[run[0]][0] + r.uniform(2, 10)
                while bx < pts[run[-1]][0] - 6:
                    by = _ease_profile(keys, [bx])[0] - 1
                    rad = r.uniform(3.0, 6.5)
                    s.path(blob(bx, by - rad * 0.55, rad * 1.2, rad * 0.8, 0.12, seed=bx), fill=r.choice(["#5f9a72", "#6aa476", "#558e6a"]))
                    s.path(f"M{bx - rad * 0.9:.1f} {by - rad * 0.7:.1f} Q{bx - rad * 0.4:.1f} {by - rad * 1.35:.1f} {bx + rad * 0.3:.1f} "
                           f"{by - rad * 1.25:.1f}", stroke="#b0dc96", width=1.2, opacity=0.75)
                    bx += r.uniform(12, 26)
        # sea caves where the waves have hollowed the foot
        for _ in range(int((x1 - x0) / 260)):
            cx = r.uniform(x0 + 70, x1 - 70)
            room = wl - _ease_profile(keys, [cx])[0]
            if room < 50:
                continue
            cw, ch = r.uniform(14, 24), min(room * 0.45, r.uniform(18, 30))
            s.path(f"M{cx - cw:.1f} {wl + 1:.1f} Q{cx - cw:.1f} {wl - ch:.1f} {cx:.1f} {wl - ch:.1f} Q{cx + cw:.1f} {wl - ch:.1f} {cx + cw:.1f} {wl + 1:.1f} Z",
                   fill=s.linear(0, wl - ch, 0, wl, [(0, "#5a4a6a"), (1, "#3a4a6a")]), opacity=0.75)
            s.path(f"M{cx - cw:.1f} {wl + 1:.1f} Q{cx - cw:.1f} {wl - ch:.1f} {cx:.1f} {wl - ch:.1f}", stroke="#fff2e6", width=1.0, opacity=0.4)
        # surf at the foot
        s.path(f"M{x0 - 8:.1f} {wl + 4:.1f} L{x1 + 8:.1f} {wl + 4:.1f}", stroke="#1f5f84", width=6, opacity=0.16)
        foam = [(x, wl + 0.6 + 1.2 * math.sin(x * 0.17 + seed)) for x in _samples(x1 - x0 + 16, 4.0)]
        s.path(_line([(x + x0 - 8, y) for x, y in foam]), stroke="#ffffff", width=2.0, opacity=0.9)
        for _ in range(int((x1 - x0) / 22)):
            fx = r.uniform(x0 - 4, x1 + 4)
            s.path(blob(fx, wl - 0.5, r.uniform(2.5, 6), r.uniform(1.2, 2.2), 0.2, seed=fx), fill="#ffffff", opacity=0.85)
        return pts

    def _lighthouse(self, s: Svg, x: float, base: float, hgt: float = 96.0) -> None:
        """Red-and-white striped lighthouse with a gallery and a brass lantern room."""
        bw, tw = 25.0, 16.0
        top = base - hgt

        def half(y: float) -> float:
            return bw / 2 + (tw / 2 - bw / 2) * (base - y) / hgt

        bands = 6
        for i in range(bands):
            ya, yb = base - hgt * i / bands, base - hgt * (i + 1) / bands
            s.polygon([(x - half(ya), ya), (x + half(ya), ya), (x + half(yb), yb), (x - half(yb), yb)], fill="#f8f2ea" if i % 2 == 0 else "#e2605a")
        s.polygon([(x + 2, base), (x + half(base), base), (x + half(top), top), (x + 1.5, top)], fill="#4a1e30", opacity=0.24)
        s.line(x - half(base) + 1.6, base, x - half(top) + 1.4, top, "#ffffff", 1.6, 0.45)
        s.path(rounded_rect_path(x - 3.6, base - 13, 7.2, 13, 3.2), fill="#5a3a2e")
        for k in (0.36, 0.7):
            wy = base - hgt * k
            s.rect(x - 1.6, wy, 3.2, 5, fill="#3a3448", rx=1.4)
        # gallery, lantern room and dome
        s.rect(x - tw / 2 - 5, top - 2, tw + 10, 3.2, fill="#2e2a36")
        for k in range(7):
            px = x - tw / 2 - 4 + k * (tw + 8) / 6
            s.line(px, top - 2, px, top - 7, "#2e2a36", 0.8)
        s.line(x - tw / 2 - 4.5, top - 7, x + tw / 2 + 4.5, top - 7, "#2e2a36", 0.9)
        s.circle(x, top - 11, 15, fill=s.radial(x, top - 11, 15, [(0, "#fffbe0", 0.9), (0.4, GLOW, 0.4), (1, GLOW, 0)]))
        s.rect(x - 5.5, top - 16, 11, 13, fill=s.linear(x - 5.5, 0, x + 5.5, 0, [(0, "#fff8d8"), (0.5, "#ffe7a0"), (1, "#f2c66a")]))
        for px in (x - 2, x + 2):
            s.line(px, top - 16, px, top - 3, "#4a3a2a", 0.7)
        s.path(f"M{x - 7:.1f} {top - 16:.1f} Q{x:.1f} {top - 27:.1f} {x + 7:.1f} {top - 16:.1f} Z",
               fill=s.linear(x - 7, 0, x + 7, 0, [(0, "#c45a40"), (1, "#7a2a24")]))
        s.line(x, top - 25, x, top - 30, "#3a2a2a", 0.9)
        s.circle(x, top - 30.5, 1.3, fill=BRASS)

    def _cottage(self, s: Svg, x: float, base: float, size: float = 30.0) -> None:
        w, hh = size, size * 0.55
        s.rect(x - w / 2, base - hh, w, hh, fill="#f4efe6")
        s.rect(x + w * 0.1, base - hh, w * 0.4, hh, fill="#c8b8b0", opacity=0.45)
        s.polygon([(x - w * 0.62, base - hh + 1), (x - w * 0.1, base - hh - w * 0.38), (x + w * 0.62, base - hh + 1)], fill="#cf6a4a")
        s.polygon([(x - w * 0.1, base - hh - w * 0.38), (x + w * 0.62, base - hh + 1), (x + w * 0.05, base - hh + 1)], fill="#9a4434")
        s.rect(x + w * 0.22, base - hh - w * 0.3, w * 0.12, w * 0.22, fill="#a0705a")
        s.rect(x - w * 0.3, base - hh * 0.62, w * 0.18, hh * 0.32, fill="#4a6a8a")
        s.rect(x + w * 0.05, base - hh * 0.75, w * 0.16, hh * 0.75, fill="#5a3a2e")

    def _pier(self, s: Svg, x0: float, x1: float, deck: float, wl: float) -> None:
        """Wooden pier on piles, a T-head with a lamp post."""
        px = x0 + 8
        while px < x1 - 2:
            s.rect(px - 1.6, deck, 3.2, wl - deck + 3, fill="#6a4a36")
            s.line(px - 1.0, deck + 2, px - 1.0, wl, "#a07a58", 0.7, 0.8)
            s.path(blob(px, wl + 0.8, 4.0, 1.2, 0.15, seed=px), fill="#ffffff", opacity=0.8)
            px += 26
        px = x0 + 8
        while px + 26 < x1:
            s.line(px, deck + 3, px + 26, wl - 4, "#5a3e2c", 1.0, 0.7)
            s.line(px + 26, deck + 3, px, wl - 4, "#5a3e2c", 1.0, 0.7)
            px += 26
        s.rect(x0, deck - 3.5, x1 - x0, 4.5, fill=s.linear(0, deck - 3.5, 0, deck + 1, [(0, "#d4a878"), (1, "#8a603e")]))
        s.line(x0, deck - 3.2, x1, deck - 3.2, "#f2d6a8", 0.9, 0.9)
        s.rect(x1 - 30, deck - 4, 36, 5, fill=s.linear(0, deck - 4, 0, deck + 1, [(0, "#d4a878"), (1, "#8a603e")]))
        post = x0 + 4
        prev = None
        while post < x1:
            s.line(post, deck - 3.5, post, deck - 12, "#6a4a36", 1.4)
            if prev is not None:
                s.path(f"M{prev:.1f} {deck - 11:.1f} Q{(prev + post) / 2:.1f} {deck - 7.5:.1f} {post:.1f} {deck - 11:.1f}", stroke="#e8d8b0", width=0.8)
            prev = post
            post += 48
        s.line(x1 + 2, deck - 4, x1 + 2, deck - 26, "#3a3440", 1.4)
        s.circle(x1 + 2, deck - 28, 6, fill=s.radial(x1 + 2, deck - 28, 6, [(0, "#fff6d0", 0.8), (1, GLOW, 0)]))
        s.rect(x1 - 0.5, deck - 30.5, 5, 5, fill="#ffe7a0", rx=1)

    def _moored_boat(self, s: Svg, x: float, wl: float) -> None:
        s.line(x, wl - 4, x, wl - 78, "#5a4a42", 1.4)
        s.path(f"M{x - 2:.1f} {wl - 70:.1f} Q{x + 18:.1f} {wl - 44:.1f} {x + 2:.1f} {wl - 14:.1f} Z", fill="#f4f0e4")
        s.line(x - 4, wl - 14, x + 26, wl - 14, "#5a4a42", 1.2)
        s.polygon([(x, wl - 78), (x + 9, wl - 75), (x, wl - 72)], fill=CORAL)
        s.path(f"M{x - 26:.1f} {wl - 10:.1f} L{x + 30:.1f} {wl - 10:.1f} Q{x + 26:.1f} {wl + 1:.1f} {x + 18:.1f} {wl + 1:.1f} L{x - 18:.1f} {wl + 1:.1f} "
               f"Q{x - 24:.1f} {wl - 2:.1f} {x - 26:.1f} {wl - 10:.1f} Z", fill=s.linear(0, wl - 10, 0, wl + 1, [(0, "#ffffff"), (1, "#c8d4dc")]))
        s.line(x - 24, wl - 6, x + 28, wl - 6, "#2f8fb0", 2.0)
        s.path(f"M{x - 22:.1f} {wl + 2:.1f} L{x + 24:.1f} {wl + 2:.1f}", stroke="#ffffff", width=1.0, opacity=0.7)

    def _hut(self, s: Svg, x: float, base: float) -> None:
        """Fisherman's hut on short stilts with a palm-thatch roof."""
        for px in (x - 12, x + 12):
            s.line(px, base, px, base - 8, "#5a3e2c", 2.0)
        s.rect(x - 15, base - 26, 30, 18, fill=s.linear(x - 15, 0, x + 15, 0, [(0, "#c49a6a"), (1, "#8a643e")]))
        for k in range(1, 5):
            s.line(x - 15 + k * 6, base - 26, x - 15 + k * 6, base - 8, "#6a4a30", 0.7, 0.7)
        s.rect(x - 4, base - 21, 8, 13, fill="#4a3226")
        s.polygon([(x - 22, base - 24), (x, base - 40), (x + 22, base - 24)], fill="#c8a85a")
        for k in range(9):
            px = x - 20 + k * 5
            s.line(px, base - 24, px + 1, base - 21, "#a8883a", 1.2)
        s.polygon([(x, base - 40), (x + 22, base - 24), (x + 4, base - 24)], fill="#8a6a2a", opacity=0.5)

    def _mid(self, idx: int) -> Svg:
        """Sandstone headlands on the sea: the lighthouse strip and the pier strip."""
        w, h = 1100.0, 300.0
        s = Svg(w, h)
        r = Rand(23 + idx * 9)
        wl = 252.0
        if idx == 0:
            keys = [(110, 254), (140, 240), (164, 196), (196, 182), (262, 174), (330, 178), (380, 166), (470, 156), (560, 150), (640, 156),
                    (690, 184), (714, 192), (736, 228), (770, 254)]
            pts = self._headland(s, keys, wl, 31)
            self._stack(s, 840, wl, 26, 74, 5, arch=False)
            for px, hgt, lean in ((230, 30, -5), (262, 36, 4), (650, 28, 6)):
                top = _ease_profile(keys, [px])[0]
                _palm_silhouette(s, px, top + 2, hgt, lean, "#8a6e5c", "#6aa676", "#558e66")
            self._cottage(s, 500, _ease_profile(keys, [500])[0] + 2, 26)
            self._lighthouse(s, 572, _ease_profile(keys, [572])[0] + 3, 80)
            for rx, rr in ((960, 9), (982, 6), (1002, 4)):
                s.path(blob(rx, wl - rr * 0.4, rr * 1.5, rr, 0.15, seed=rx), fill=s.linear(0, wl - rr * 1.4, 0, wl, [(0, "#b49a90"), (1, "#7a6a74")]))
                s.path(blob(rx, wl, rr * 1.8, 1.6, 0.2, seed=rx + 1), fill="#ffffff", opacity=0.85)
            del pts
        else:
            keys = [(70, 254), (96, 238), (116, 212), (150, 202), (230, 198), (300, 204), (346, 214), (370, 236), (394, 254)]
            self._headland(s, keys, wl, 37)
            for px, hgt, lean in ((150, 46, -8), (182, 54, 6), (262, 42, -4), (300, 36, 7)):
                top = _ease_profile(keys, [px])[0]
                _palm_silhouette(s, px, top + 2, hgt, lean, "#8a6e5c", "#6aa676", "#558e66")
            self._hut(s, 222, _ease_profile(keys, [222])[0] + 2)
            self._pier(s, 340, 860, 234, wl)
            self._moored_boat(s, 930, wl)
            keys2 = [(1000, 254), (1016, 232), (1034, 220), (1050, 230), (1066, 254)]
            self._headland(s, keys2, wl, 41, scrub=False)
            _palm_silhouette(s, 1032, 222, 28, 5, "#8a6e5c", "#6aa676", "#558e66")
        # gulls
        for _ in range(4):
            gx, gy = r.uniform(80, w - 80), r.uniform(30, 120)
            sz = r.uniform(3, 5)
            s.path(f"M{gx - sz:.1f} {gy:.1f} Q{gx - sz * 0.5:.1f} {gy - sz * 0.6:.1f} {gx:.1f} {gy:.1f} Q{gx + sz * 0.5:.1f} {gy - sz * 0.6:.1f} "
                   f"{gx + sz:.1f} {gy:.1f}", stroke="#4a5a6a", width=0.9, opacity=0.8)
        return s

    def _near(self, idx: int) -> Svg:
        """Beach dunes: sea oats, sea-grape bushes, a sand fence and spray-washed rocks."""
        w, h = 900.0, 200.0
        s = Svg(w, h)
        r = Rand(41 + idx * 7)

        def crest(x: float) -> float:
            t = x / w * 2 * math.pi
            common = 6 * math.sin(2 * t + 0.6) + 4 * math.sin(5 * t + 1.7)
            window = math.sin(math.pi * x / w) ** 2
            return 54 + common + window * (10 * math.sin(3 * t + idx * 2.3) + 4 * math.sin(7 * t + idx))

        # rocks with spray just behind the dunes
        for rx in ((240.0, 700.0) if idx == 0 else (120.0, 520.0, 820.0)):
            cy = crest(rx)
            for k, (dx, rr) in enumerate(((-14, 13), (6, 18), (24, 10))):
                bx = rx + dx
                s.path(blob(bx, cy - rr * 0.55, rr * 1.15, rr, 0.14, seed=bx), fill=s.linear(bx - rr, 0, bx + rr, 0, [(0, "#8d8a96"), (0.5, "#6a6674"),
                                                                                                                  (1, "#4a4656")]))
                s.path(f"M{bx - rr * 0.9:.1f} {cy - rr * 0.8:.1f} Q{bx - rr * 0.4:.1f} {cy - rr * 1.5:.1f} {bx + rr * 0.3:.1f} {cy - rr * 1.45:.1f}",
                       stroke="#c9c6d4", width=1.4, opacity=0.7)
            _splash(s, rx + 4, cy - 24, 30, r)
            _splash(s, rx - 16, cy - 15, 18, r)
            for j in range(5):
                _sparkle(s, rx + r.uniform(-34, 38), cy - r.uniform(24, 54), r.uniform(1.0, 2.0), 0.8)
        # dune body
        xs = _samples(w, 6.0)
        top = [(x, crest(x)) for x in xs]
        s.path(_line([(0, h)] + top + [(w, h)]) + "Z", fill=s.linear(0, 30, 0, h, [(0, "#f6e6bf"), (0.3, "#ead09a"), (0.7, "#dcb67c"), (1, "#c99e68")]))
        s.path(_line(top), stroke="#fff6dc", width=2.2, opacity=0.9)
        for _ in range(7):
            dx = r.uniform(30, w - 30)
            dy = crest(dx) + r.uniform(16, 70)
            s.path(smooth_open([(dx - 46, dy + 5), (dx, dy), (dx + 52, dy + 4)]), stroke="#c49a66", width=2.2, opacity=0.35)
            s.path(smooth_open([(dx - 40, dy + 7.5), (dx, dy + 2.5), (dx + 46, dy + 6.5)]), stroke="#fff2d4", width=1.2, opacity=0.4)
        # sand fence along the dune
        fx = 380.0 if idx == 0 else 610.0
        prev = None
        for k in range(7):
            px = fx + k * 16
            py = crest(px) + 3
            s.line(px, py + 6, px + 1.2, py - 16 + (k % 2) * 2, "#8a6a4a", 1.8)
            if prev is not None:
                for yy in (11.0, 5.0):
                    s.line(prev[0] + 1, prev[1] - yy, px + 1, py - yy, "#a88a6a", 0.8, 0.9)
            prev = (px, py)
        # sea-grape bushes
        for bx in ((90.0, 520.0, 800.0) if idx == 0 else (300.0, 470.0, 720.0)):
            _seagrape_clump(s, bx, crest(bx) + 8, r.uniform(30, 40), r, hazy=True)
        # sea oats along the crest
        for gx in _samples(w, 9.0)[1:-1]:
            if r.next() < 0.35:
                continue
            gy = crest(gx) + 2
            for b in range(int(r.uniform(3, 6))):
                lean = r.uniform(-7, 9)
                bh = r.uniform(10, 24)
                bx = gx + r.uniform(-4, 4)
                s.path(f"M{bx - 1.2:.1f} {gy:.1f} Q{bx + lean * 0.3:.1f} {gy - bh * 0.6:.1f} {bx + lean:.1f} {gy - bh:.1f} Q{bx + lean * 0.3 + 0.8:.1f} "
                       f"{gy - bh * 0.5:.1f} {bx + 1.2:.1f} {gy:.1f} Z", fill=r.choice(["#9cc46a", "#b8cf78", "#7aa858", "#d6d08a"]))
            if r.next() < 0.45:
                hx, hy = gx + r.uniform(2, 8), gy - r.uniform(22, 32)
                s.path(f"M{gx:.1f} {gy:.1f} Q{gx + 2:.1f} {(gy + hy) / 2:.1f} {hx:.1f} {hy:.1f}", stroke="#c8b878", width=0.8)
                for k in range(4):
                    s.ellipse(hx + 1.6 + k * 1.2, hy + 1.5 + k * 2.4, 1.1, 1.9, fill="#e8d49a")
        return s

    def layer_art(self) -> dict[str, PropSpec]:
        art = {"cc.far.0": PropSpec(self._far, (0, 0))}
        for i in range(2):
            art[f"cc.mid.{i}"] = PropSpec((lambda i=i: self._mid(i)), (0, 0))
            art[f"cc.near.{i}"] = PropSpec((lambda i=i: self._near(i)), (0, 0))
        return art

    def layers(self) -> list[Layer]:
        return [
            Layer("far", 0.06, ["cc.far.0"], 1200, -123, vertical=0.03),
            Layer("mid", 0.22, ["cc.mid.0", "cc.mid.1"], 1100, -35, vertical=0.12),
            Layer("near", 0.48, ["cc.near.0", "cc.near.1"], 900, 100, vertical=0.3),
        ]

    # ------------------------------------------------------------------ terrain
    def terrain(self, style: str, w: float, h: float, seed: int, left: bool, right: bool, top: bool = True, x0: float = 0.0,
                surface: str = "normal") -> Svg:
        """Terrain chunk art. Everything that crosses chunk borders (strata,
        cross-bedding, cap edges, drips, foam lace, shells, corals) is a
        function of the world x (``x0`` + local x), so adjacent chunks join
        seamlessly; only the hanging edges are outlined, never the chunk's
        vertical borders."""
        if style == "cave":
            return self._cave(w, h, seed, left, right, x0)
        if style in ("fortress", "ship", "hull", "galleon"):
            return self._hull(w, h, seed, left, right, top, x0)
        hr = self.terrain_headroom
        s = Svg(w, h + hr)
        r = Rand(seed)
        slick = surface == "ice"
        if style == "reef":
            self._reef_rock(s, r, w, h, hr, left, right, x0)
            if top:
                if slick:
                    self._algae_cap(s, w, hr, left, right, x0)
                else:
                    self._reef_cap(s, w, hr, left, right, x0)
            return s
        self._sandstone(s, r, w, h, hr, left, right, x0, slick and top)
        if top:
            if slick:
                self._algae_cap(s, w, hr, left, right, x0)
            else:
                self._sand_cap(s, w, hr, left, right, x0, surface == "sticky")
        return s

    def _sandstone(self, s: Svg, r: Rand, w: float, h: float, y0: float, left: bool, right: bool, x0: float, wet: bool) -> None:
        bottom = h + y0
        il, ir = (2.5 if left else 0.0), (2.5 if right else 0.0)
        ys = [y0 + 4 + (bottom - y0 - 4) * i / 12 for i in range(13)]
        lface = [(il + 1.3 * math.sin(y * 0.19 + x0 * 0.01), y) for y in ys] if left else [(0.0, y) for y in ys]
        rface = [(w - ir - 1.3 * math.sin(y * 0.17 + x0 * 0.013), y) for y in ys] if right else [(w, y) for y in ys]
        s.path(_poly(list(reversed(lface)) + rface),
               fill=s.linear(0, y0, 0, y0 + 300, [(0, STONE_TOP), (0.13, STONE), (0.37, STONE_LOW), (0.6, STONE_DEEP), (1, "#5a2c36")]))
        if wet:
            s.rect(il, y0 + 4, w - il - ir, 34, fill=s.linear(0, y0 + 4, 0, y0 + 38, [(0, "#2f5a3a", 0.35), (1, "#2f5a3a", 0)]))
        xs = _samples(w, 5.0)

        def plane(lx: float, k: int) -> float:
            gx = x0 + lx
            return y0 + 24 + k * 23 + 3.0 * _wobble(gx, k * 1.7) + 4.5 * math.sin(gx * 0.0055 + k * 0.8)

        for k in range(7):
            if y0 + 24 + k * 23 > bottom - 8:
                break
            edge = [(lx, plane(lx, k)) for lx in xs]
            if k % 2 == 0:  # alternate bands are tinted (salmon, ochre, rose…)
                low = [(lx, plane(lx, k + 1) - 1) for lx in reversed(xs)]
                s.path(_poly(edge + low), fill=STRATA[(k // 2) % len(STRATA)], opacity=0.34)
            s.path(_line(edge), stroke=STONE_LINE, width=1.3, opacity=0.42)
            s.path(_line([(x, y + 1.3) for x, y in edge]), stroke="#ffe4c4", width=0.8, opacity=0.35)
            if k % 2 == 0:  # cross-bedding: thin slanted laminae inside the band
                for n in _slots(x0, w, 11.0):
                    if _hash(n, 40 + k) < 0.45:
                        continue
                    lx = n * 11.0 + 4 * _hash(n, 50 + k) - x0
                    if not 2 < lx < w - 14:
                        continue
                    ya, yb = plane(lx, k) + 3, plane(lx, k + 1) - 4
                    if yb - ya > 6:
                        s.line(lx, ya, lx + (yb - ya) * 0.75, yb, STONE_LINE, 0.7, 0.26)
        # tafoni: wind-eroded pockets lit on their lower rim
        deep = min(bottom - 10, y0 + 130)
        for _ in range(max(1, int(w * min(h, 140) / 5600))):
            pr = r.uniform(2.8, 6.5)
            if deep - pr < y0 + 28 or w < pr * 4 + 12:
                continue
            px, py = r.uniform(pr * 1.6 + 5, w - pr * 1.6 - 5), r.uniform(y0 + 28, deep - pr)
            s.ellipse(px, py, pr * 1.5, pr, fill=s.radial(px, py - pr * 0.3, pr * 1.6, [(0, "#4e2630", 0.9), (1, "#7a4448", 0.55)]))
            s.path(f"M{px - pr * 1.35:.2f} {py + pr * 0.3:.2f} Q{px:.2f} {py + pr * 1.3:.2f} {px + pr * 1.35:.2f} {py + pr * 0.3:.2f}",
                   stroke="#ffd8b4", width=1.0, opacity=0.6)
        # fossil shells and coral sprigs
        for _ in range(int(w / 110) + 1):
            if deep < y0 + 34:
                break
            fx, fy = r.uniform(14, w - 14), r.uniform(y0 + 32, deep)
            if r.next() < 0.55:
                pts = [(fx + math.cos(i * 0.45) * (0.4 + i * 0.16), fy + math.sin(i * 0.45) * (0.4 + i * 0.16)) for i in range(26)]
                s.path(smooth_open(pts), stroke="#7a4444", width=1.0, opacity=0.35)
                s.path(smooth_open([(x - 0.5, y - 0.5) for x, y in pts]), stroke="#ffe2c4", width=0.8, opacity=0.6)
            else:
                for k in range(4):
                    a = math.radians(-150 + k * 40)
                    s.line(fx, fy, fx + math.cos(a) * 5, fy + math.sin(a) * 5, "#ffe8d0", 0.9, 0.55)
                    s.circle(fx + math.cos(a) * 5.4, fy + math.sin(a) * 5.4, 0.8, fill="#ffe8d0", opacity=0.6)
        for _ in range(max(1, int(w / 55))):
            px, py = r.uniform(6, w - 6), r.uniform(y0 + 16, min(bottom - 5, y0 + 70))
            pr = r.uniform(1.6, 3.4)
            s.ellipse(px, py, pr * 1.3, pr, fill=r.choice(["#c9b8a4", "#efe0c8", "#9a8478", "#d8a490", "#b4a2b8"]), stroke=STONE_LINE, width=0.6,
                      opacity=0.9)
            s.ellipse(px - pr * 0.4, py - pr * 0.35, pr * 0.45, pr * 0.25, fill="#ffffff", opacity=0.5)
        if left:
            s.path(_poly(lface + [(px + 7, py) for px, py in reversed(lface)]), fill="#ffe8cc", opacity=0.28)
            s.path(_line(lface), stroke=STONE_LINE, width=1.3, opacity=0.75)
        if right:
            s.path(_poly(rface + [(px - 9, py) for px, py in reversed(rface)]), fill="#4a2230", opacity=0.3)
            s.path(_line(rface), stroke=STONE_LINE, width=1.3, opacity=0.75)

    def _sand_cap(self, s: Svg, w: float, y0: float, left: bool, right: bool, x0: float, sticky: bool = False) -> None:
        xs = _samples(w, 2.5)
        drip = 21.0

        def top_y(lx: float) -> float:
            gx = x0 + lx
            y = y0 - 1.3 + 0.7 * _wobble(gx, 0.4) + 0.25 * math.sin(gx * 0.23)
            if left and lx < 6:
                y += 4.5 * (1 - lx / 6) ** 2
            if right and w - lx < 6:
                y += 4.5 * (1 - (w - lx) / 6) ** 2
            return y

        def bottom_y(lx: float) -> float:
            gx = x0 + lx
            y = y0 + 10.5 + 1.4 * _wobble(gx, 1.9)
            n = math.floor(gx / drip)
            for m in (n - 1, n, n + 1):
                if _hash(m, 5) > 0.45:
                    c = (m + 0.3 + 0.4 * _hash(m, 6)) * drip
                    y += (2.0 + 4.5 * _hash(m, 7)) * math.exp(-((gx - c) / (2.4 + 2.0 * _hash(m, 8))) ** 2)
            if left and lx < 10:
                y -= 4.0 * (1 - lx / 10) ** 1.5
            if right and w - lx < 10:
                y -= 4.0 * (1 - (w - lx) / 10) ** 1.5
            return y

        def foam_y(lx: float) -> float:
            gx = x0 + lx
            return y0 + 3.9 + 1.1 * math.sin(gx * 0.083 + 0.7) + 0.6 * math.sin(gx * 0.21)

        tops = [(lx, top_y(lx)) for lx in xs]
        bottoms = [(lx, bottom_y(lx)) for lx in xs]
        foam = [(lx, foam_y(lx)) for lx in xs]
        s.path(_line([(x, y + 2.6) for x, y in bottoms]), stroke="#4a2028", width=5.0, opacity=0.24)
        stops = [(0, SAND_HI), (0.14, SAND_TOP), (0.42, SAND), (0.7, SAND_WET), (1, SAND_LOW)]
        if sticky:
            stops = [(0, "#d8b888"), (0.2, "#a8804e"), (0.6, "#7e5a36"), (1, "#5a3e26")]
        s.path(_poly(tops + list(reversed(bottoms))), fill=s.linear(0, y0 - 2, 0, y0 + 15, stops))
        s.path(_poly(foam + list(reversed(bottoms))), fill="#b07440", opacity=0.2)
        s.path(_line([(x, y - 1.8) for x, y in bottoms]), stroke="#a46a3a", width=2.4, opacity=0.4)
        for n in _slots(x0, w, 17.0):
            if _hash(n, 61) < 0.5:
                continue
            ln = 4 + 7 * _hash(n, 63)
            lx = n * 17.0 + 9 * _hash(n, 62) - x0
            if 3 < lx and lx + ln < w - 3:
                yy = foam_y(lx) + 2.8 + 2.4 * _hash(n, 64)
                s.line(lx, yy, lx + ln, yy, "#fff6dc", 0.9, 0.55)
        if sticky:
            for n in _slots(x0, w, 23.0):
                lx = n * 23.0 + 12 * _hash(n, 66) - x0
                if _hash(n, 65) > 0.5 and 6 < lx < w - 6:
                    s.ellipse(lx, top_y(lx) + 1.4, 4 + 3 * _hash(n, 67), 0.9, fill="#5a3e26", opacity=0.6)
                    s.line(lx - 2, top_y(lx) + 1, lx + 1.5, top_y(lx) + 1, "#f4e6c8", 0.6, 0.7)
        # the lace of foam left by the last wave
        s.path(_line([(x, y + 0.7) for x, y in foam]), stroke="#b8844e", width=1.0, opacity=0.35)
        s.path(_line(foam), stroke="#ffffff", width=1.5, opacity=0.82)
        for n in _slots(x0, w, 4.0):
            if _hash(n, 71) < 0.55:
                continue
            lx = n * 4.0 + 3 * _hash(n, 72) - x0
            if 1.5 < lx < w - 1.5:
                s.circle(lx, foam_y(lx) + (_hash(n, 74) - 0.4) * 2.4, 0.45 + 0.75 * _hash(n, 73), stroke="#ffffff", width=0.45, opacity=0.75)
        s.path(_line(bottoms), stroke=SAND_LINE, width=1.2)
        if left:
            s.path(f"M0 {tops[0][1]:.2f} L0 {bottoms[0][1]:.2f}", stroke=SAND_LINE, width=1.4)
        if right:
            s.path(f"M{w:.2f} {tops[-1][1]:.2f} L{w:.2f} {bottoms[-1][1]:.2f}", stroke=SAND_LINE, width=1.4)
        s.path(_line([(x, y + 0.8) for x, y in tops]), stroke="#fffbe9", width=1.3, opacity=0.9)
        s.path(_line(tops), stroke="#c99858", width=0.7, opacity=0.55)
        for n in _slots(x0, w, 3.0):
            if _hash(n, 91) < 0.6:
                continue
            lx = n * 3.0 + 3 * _hash(n, 92) - x0
            if 1 < lx < w - 1:
                s.circle(lx, top_y(lx) + 2.2 + 6.5 * _hash(n, 93), 0.35, fill=_pick(("#fff8e0", "#b8864e", "#d6a466"), n), opacity=0.8)
        self._beach_bits(s, w, x0, top_y, left, right)

    def _beach_bits(self, s: Svg, w: float, x0: float, top_y: Callable[[float], float], left: bool, right: bool) -> None:
        """Shells, pebbles and the odd tiny starfish lying on the sand (world-aligned)."""
        step = 31.0
        for n in _slots(x0, w, step, 8.0):
            if _hash(n, 81) < 0.48:
                continue
            lx = n * step + step * 0.8 * _hash(n, 82) - x0
            size = 1.9 + 1.5 * _hash(n, 83)
            if (left and lx < size + 5) or (right and lx > w - size - 5) or lx < -size - 3 or lx > w + size + 3:
                continue
            ty = top_y(min(max(lx, 0.0), w)) + 0.7
            kind = int(_hash(n, 84) * 6)
            if kind == 0:
                _scallop(s, lx, ty, size * 1.1, _pick(("#f6b8a0", "#fbe2c8", "#f2a6b4"), n), tilt=(_hash(n, 85) - 0.5) * 30, width=0.45)
            elif kind == 1:
                _conch(s, lx, ty, size * 0.9, _pick(("#f4d0b0", "#e8b48e"), n), flip=_hash(n, 86) > 0.5, width=0.45)
            elif kind == 2:
                _starfish(s, lx, ty - size * 0.25, size * 0.95, _pick((CORAL_ORANGE, CORAL, "#f2785a"), n), angle=_hash(n, 87) * 70, width=0.45)
            else:
                for j in range(1 + kind % 2):
                    px = lx + j * size * 1.6
                    pr = size * (0.55 + 0.25 * _hash(n, 88 + j))
                    s.ellipse(px, ty - pr * 0.55, pr * 1.3, pr * 0.75, fill=_pick(("#9a8a86", "#c8b4a4", "#7a7a86", "#d8c4b0"), n + j),
                              stroke="#4a3a3a", width=0.45)
                    s.ellipse(px - pr * 0.4, ty - pr * 0.85, pr * 0.45, pr * 0.22, fill="#ffffff", opacity=0.55)

    def _algae_cap(self, s: Svg, w: float, y0: float, left: bool, right: bool, x0: float) -> None:
        """Slippery cap: a glossy mat of green algae with slime drips."""
        xs = _samples(w, 2.0)
        slot = 11.0

        def top_y(lx: float) -> float:
            y = y0 - 0.6
            if left and lx < 4:
                y += 3.0 * (1 - lx / 4) ** 2
            if right and w - lx < 4:
                y += 3.0 * (1 - (w - lx) / 4) ** 2
            return y

        def bottom_y(lx: float) -> float:
            gx = x0 + lx
            y = y0 + 9.5 + 1.0 * _wobble(gx, 2.3)
            n = math.floor(gx / slot)
            for m in (n - 1, n, n + 1):
                if _hash(m, 11) > 0.55:
                    c = (m + 0.5) * slot
                    y += (3 + 7 * _hash(m, 12)) * math.exp(-((gx - c) / 2.4) ** 2)
            if left and lx < 6:
                y -= 3.5 * (1 - lx / 6)
            if right and w - lx < 6:
                y -= 3.5 * (1 - (w - lx) / 6)
            return y

        tops = [(lx, top_y(lx)) for lx in xs]
        bottoms = [(lx, bottom_y(lx)) for lx in xs]
        s.path(_line([(x, y + 2.4) for x, y in bottoms]), stroke="#0f2a24", width=4.5, opacity=0.25)
        s.path(_poly(tops + list(reversed(bottoms))),
               fill=s.linear(0, y0 - 1, 0, y0 + 19, [(0, "#efffd8"), (0.12, "#a6e68e"), (0.45, "#52b270"), (0.8, "#2c7f5c"), (1, "#1d5848")]))
        s.path(_line([(x, y - 2.2) for x, y in bottoms]), stroke="#1f6a4a", width=3.0, opacity=0.35)
        streak = 44.0
        for m in _slots(x0, w, streak):
            if _hash(m, 31) < 0.35:
                continue
            gx = m * streak + 30 * _hash(m, 32) - x0
            wide = 4 + 6 * _hash(m, 33)
            if not (gx - 6 > 2 and gx + wide + 2 < w):
                continue
            s.polygon([(gx, y0 + 1.6), (gx + wide, y0 + 1.6), (gx + wide - 6, y0 + 9), (gx - 6, y0 + 9)], fill="#ffffff", opacity=0.4)
            if _hash(m, 34) > 0.4 and gx + wide + 6 < w - 2:
                s.polygon([(gx + wide + 3, y0 + 1.6), (gx + wide + 5, y0 + 1.6), (gx + wide - 1, y0 + 9), (gx + wide - 3, y0 + 9)], fill="#ffffff",
                          opacity=0.3)
        for n in _slots(x0, w, 6.0):
            lx = n * 6.0 + 5 * _hash(n, 35) - x0
            if _hash(n, 36) > 0.6 and 2 < lx < w - 2:
                s.circle(lx, y0 + 3 + 5 * _hash(n, 37), 0.5 + 0.7 * _hash(n, 38), stroke="#e8ffe0", width=0.45, opacity=0.7)
        s.path(_line(bottoms), stroke="#174a3a", width=1.2)
        if left:
            s.path(f"M0 {tops[0][1]:.2f} L0 {bottoms[0][1]:.2f}", stroke="#174a3a", width=1.4)
        if right:
            s.path(f"M{w:.2f} {tops[-1][1]:.2f} L{w:.2f} {bottoms[-1][1]:.2f}", stroke="#174a3a", width=1.4)
        s.path(_line(tops), stroke="#3f9a62", width=0.9, opacity=0.9)
        s.path(_line([(x, y + 1.2) for x, y in tops]), stroke="#ffffff", width=1.5, opacity=0.95)
        for run in _runs(xs, lambda lx: math.sin((x0 + lx) * 0.045) + 0.4 * math.sin((x0 + lx) * 0.13) > 0.35):
            s.path(_line([(lx, y0 + 4.0) for lx in run]), stroke="#ffffff", width=0.9, opacity=0.5)
        # slime drips under the heavier lobes
        for n in _slots(x0, w, slot):
            lx = (n + 0.5) * slot - x0
            if _hash(n, 11) > 0.55 and _hash(n, 13) > 0.4 and 3 < lx < w - 3:
                y1 = bottom_y(lx) - 1
                ln = 3 + 7 * _hash(n, 14)
                s.path(f"M{lx - 1.4:.2f} {y1:.2f} Q{lx - 1.6:.2f} {y1 + ln * 0.7:.2f} {lx:.2f} {y1 + ln:.2f} Q{lx + 1.6:.2f} {y1 + ln * 0.7:.2f} "
                       f"{lx + 1.4:.2f} {y1:.2f} Z", fill="#7fd08a", stroke="#1f5a44", width=0.5, opacity=0.8)
                s.circle(lx - 0.4, y1 + ln * 0.62, 0.45, fill="#ffffff", opacity=0.8)
        # wet sand piled at the exposed ends marks where the slick mat begins
        for exposed, ex in ((left, 5.5), (right, w - 5.5)):
            if exposed:
                s.path(blob(ex, y0 - 0.4, 7.0, 3.2, 0.15, seed=x0 + ex, squash_top=1.15),
                       fill=s.linear(0, y0 - 4, 0, y0 + 3, [(0, SAND_HI), (1, SAND)]), stroke=SAND_LINE, width=0.8)

    # --- reef ------------------------------------------------------------------------
    def _reef_rock(self, s: Svg, r: Rand, w: float, h: float, y0: float, left: bool, right: bool, x0: float) -> None:
        """Living coral rock: lumpy coralline boulders, pores, brain corals, crusts."""
        bottom = h + y0
        s.rect(0, y0 + 2, w, h - 2, fill=s.linear(0, y0, 0, y0 + 300, [(0, REEF_TOP), (0.16, REEF), (0.42, REEF_LOW), (0.65, REEF_DEEP), (1, "#1c1430")]))
        deep = min(bottom - 6, y0 + 150)
        # lumps (chunk-local, kept off the borders so nothing is cut)
        for _ in range(max(3, int(w * min(h, 150) / 2000))):
            pr = r.uniform(7, 15)
            if w < pr * 3 + 10 or deep - pr < y0 + 14:
                continue
            px, py = r.uniform(pr * 1.3 + 4, w - pr * 1.3 - 4), r.uniform(y0 + 14, deep - pr * 0.5)
            tone = r.choice(["#c27a9a", "#a9658a", "#d08aa2", "#96587e", "#b8749a"])
            s.path(blob(px, py, pr * 1.25, pr, 0.12, seed=px), fill=tone, opacity=0.75)
            s.path(f"M{px - pr * 1.1:.2f} {py - pr * 0.1:.2f} Q{px - pr * 0.8:.2f} {py - pr * 0.95:.2f} {px + pr * 0.2:.2f} {py - pr * 0.95:.2f}",
                   stroke="#ffd2de", width=1.2, opacity=0.5)
            s.path(f"M{px + pr * 1.15:.2f} {py + pr * 0.05:.2f} Q{px + pr * 0.9:.2f} {py + pr * 0.85:.2f} {px - pr * 0.2:.2f} {py + pr * 0.95:.2f}",
                   stroke=REEF_LINE, width=1.2, opacity=0.45)
        # star-coral colonies grown into the rock: knobby lumps covered in polyp cups
        for _ in range(int(w / 95) + 1):
            pr = r.uniform(5, 9)
            if deep - pr < y0 + 16:
                break
            px, py = r.uniform(pr * 1.3 + 4, w - pr * 1.3 - 4), r.uniform(y0 + 16, deep - pr)
            tone = r.choice(["#f0b066", "#c9a0e0", "#f2a080", "#a8d08a"])
            s.path(blob(px, py, pr * 1.3, pr, 0.15, seed=px), fill=s.radial(px - pr * 0.4, py - pr * 0.5, pr * 1.8,
                                                                         [(0, shade(tone, 0.35)), (0.6, tone), (1, shade(tone, -0.3))]),
                   stroke=REEF_LINE, width=0.7)
            for _j in range(int(pr * 1.4)):
                a = r.uniform(0, 2 * math.pi)
                d = r.uniform(0.0, 0.75)
                s.circle(px + math.cos(a) * pr * 1.15 * d, py + math.sin(a) * pr * 0.85 * d, 0.85, fill=shade(tone, -0.35), stroke=shade(tone, 0.5),
                         width=0.4)
        # pores and encrusting patches
        for _ in range(int(w * min(h, 150) / 520)):
            px, py = r.uniform(3, w - 3), r.uniform(y0 + 8, deep)
            s.circle(px, py, r.uniform(0.6, 1.6), fill="#5a3260")
        for _ in range(int(w / 60) + 1):
            px, py = r.uniform(8, w - 8), r.uniform(y0 + 14, deep)
            rr = r.uniform(3, 7)
            s.path(blob(px, py, rr * 1.4, rr, 0.3, seed=px), fill=r.choice(["#ff9aa8", "#7fc28a", "#f6b0c8", "#ffb87a"]), opacity=0.45)
        if left:
            s.rect(0, y0 + 4, 6, h - 4, fill=s.linear(0, 0, 6, 0, [(0, "#ffd6e2", 0.35), (1, "#ffd6e2", 0)]))
            s.line(0.7, y0 + 4, 0.7, bottom, REEF_LINE, 1.4, 0.8)
        if right:
            s.rect(w - 8, y0 + 4, 8, h - 4, fill=s.linear(w - 8, 0, w, 0, [(0, "#1a0c28", 0), (1, "#1a0c28", 0.45)]))
            s.line(w - 0.7, y0 + 4, w - 0.7, bottom, REEF_LINE, 1.4, 0.8)

    def _reef_cap(self, s: Svg, w: float, y0: float, left: bool, right: bool, x0: float) -> None:
        """Coralline crust with lobed edge; small corals and anemones live on top."""
        xs = _samples(w, 2.0)
        lobe = 9.0

        def top_y(lx: float) -> float:
            gx = x0 + lx
            y = y0 - 0.9 + 0.5 * _wobble(gx, 0.8)
            if left and lx < 5:
                y += 3.5 * (1 - lx / 5) ** 2
            if right and w - lx < 5:
                y += 3.5 * (1 - (w - lx) / 5) ** 2
            return y

        def bottom_y(lx: float) -> float:
            gx = x0 + lx
            t = gx / lobe
            y = y0 + 7.5 + 3.4 * abs(math.sin(math.pi * t)) ** 0.6 * (0.6 + 0.4 * _hash(math.floor(t), 21)) + 0.8 * _wobble(gx, 2.9)
            if left and lx < 8:
                y -= 3.0 * (1 - lx / 8)
            if right and w - lx < 8:
                y -= 3.0 * (1 - (w - lx) / 8)
            return y

        tops = [(lx, top_y(lx)) for lx in xs]
        bottoms = [(lx, bottom_y(lx)) for lx in xs]
        s.path(_line([(x, y + 2.4) for x, y in bottoms]), stroke="#1a0c26", width=4.5, opacity=0.3)
        s.path(_poly(tops + list(reversed(bottoms))),
               fill=s.linear(0, y0 - 2, 0, y0 + 12, [(0, "#ffe0e6"), (0.2, "#f7a8bc"), (0.6, "#de7898"), (1, "#a8507c")]))
        for n in _slots(x0, w, 3.4):
            lx = n * 3.4 + 2 * _hash(n, 22) - x0
            if _hash(n, 23) > 0.5 and 1 < lx < w - 1:
                s.circle(lx, y0 + 2 + 7 * _hash(n, 24), 0.4 + 0.4 * _hash(n, 25), fill="#ffe8ee" if _hash(n, 26) > 0.5 else "#8a3a62", opacity=0.75)
        s.path(_line(bottoms), stroke=REEF_LINE, width=1.2)
        if left:
            s.path(f"M0 {tops[0][1]:.2f} L0 {bottoms[0][1]:.2f}", stroke=REEF_LINE, width=1.4)
        if right:
            s.path(f"M{w:.2f} {tops[-1][1]:.2f} L{w:.2f} {bottoms[-1][1]:.2f}", stroke=REEF_LINE, width=1.4)
        s.path(_line([(x, y + 0.8) for x, y in tops]), stroke="#fff0f4", width=1.3, opacity=0.9)
        # reef life on the surface
        step = 17.0
        for n in _slots(x0, w, step, 10.0):
            v = _hash(n, 27)
            if v < 0.3:
                continue
            lx = n * step + step * 0.7 * _hash(n, 28) - x0
            size = 3.0 + 2.6 * _hash(n, 29)
            if (left and lx < size + 4) or (right and lx > w - size - 4) or lx < -size * 2 or lx > w + size * 2:
                continue
            ty = top_y(min(max(lx, 0.0), w)) + 1.0
            kind = int(_hash(n, 30) * 5)
            if kind == 0:  # brain coral dome
                tone = _pick(("#f2b46a", "#c8a2e6", "#a8d48a"), n)
                s.path(f"M{lx - size:.2f} {ty:.2f} Q{lx - size:.2f} {ty - size * 1.2:.2f} {lx:.2f} {ty - size * 1.2:.2f} Q{lx + size:.2f} "
                       f"{ty - size * 1.2:.2f} {lx + size:.2f} {ty:.2f} Z", fill=s.radial(lx - size * 0.3, ty - size, size * 1.6,
                                                                             [(0, shade(tone, 0.4)), (1, shade(tone, -0.25))]),
                       stroke=REEF_LINE, width=0.6)
                s.path(f"M{lx - size * 0.7:.2f} {ty - size * 0.5:.2f} Q{lx - size * 0.3:.2f} {ty - size * 0.9:.2f} {lx:.2f} {ty - size * 0.55:.2f} "
                       f"Q{lx + size * 0.35:.2f} {ty - size * 0.2:.2f} {lx + size * 0.7:.2f} {ty - size * 0.6:.2f}", stroke=shade(tone, -0.4), width=0.6)
            elif kind == 1:  # anemone tuft
                tone = _pick(("#5fd8c8", "#ff8fb8", "#ffd27a"), n)
                for k in range(7):
                    a = math.radians(-150 + k * 20)
                    ex, ey = lx + math.cos(a) * size * 1.15, ty - size * 0.5 + math.sin(a) * size * 1.1
                    s.path(f"M{lx:.2f} {ty - size * 0.45:.2f} Q{(lx + ex) / 2 + math.cos(a + 1.2) * 1.2:.2f} {(ty + ey) / 2:.2f} {ex:.2f} {ey:.2f}",
                           stroke=tone, width=1.1)
                    s.circle(ex, ey, 0.75, fill=shade(tone, 0.5))
                s.path(f"M{lx - size * 0.5:.2f} {ty:.2f} L{lx - size * 0.35:.2f} {ty - size * 0.5:.2f} L{lx + size * 0.35:.2f} {ty - size * 0.5:.2f} "
                       f"L{lx + size * 0.5:.2f} {ty:.2f} Z", fill=shade(tone, -0.3), stroke=REEF_LINE, width=0.5)
            elif kind == 2:  # staghorn sprig
                tone = _pick((CORAL_ORANGE, CORAL), n)
                for k, (dx, hh) in enumerate(((-0.6, 1.3), (0.0, 1.8), (0.65, 1.2))):
                    s.path(f"M{lx + dx * size * 0.4:.2f} {ty:.2f} L{lx + dx * size:.2f} {ty - hh * size:.2f}", stroke=REEF_LINE, width=2.4)
                    s.path(f"M{lx + dx * size * 0.4:.2f} {ty:.2f} L{lx + dx * size:.2f} {ty - hh * size:.2f}", stroke=tone, width=1.4)
                    s.circle(lx + dx * size, ty - hh * size, 0.9, fill=shade(tone, 0.5))
            elif kind == 3:  # tube sponges
                tone = _pick((VIOLET, "#d86ab0"), n)
                for k, (dx, hh) in enumerate(((-0.45, 1.1), (0.25, 1.6))):
                    bx = lx + dx * size
                    s.path(rounded_rect_path(bx - size * 0.3, ty - hh * size, size * 0.6, hh * size + 0.5, size * 0.25),
                           fill=s.linear(bx - size * 0.3, 0, bx + size * 0.3, 0, [(0, shade(tone, 0.3)), (1, shade(tone, -0.3))]), stroke=REEF_LINE, width=0.5)
                    s.ellipse(bx, ty - hh * size + 0.4, size * 0.2, 0.5, fill="#2a1030")
            else:  # tiny sea fan
                tone = _pick(("#b05ac8", CORAL_ORANGE), n)
                for k in range(5):
                    a = math.radians(-130 + k * 20)
                    s.path(f"M{lx:.2f} {ty:.2f} Q{lx + math.cos(a) * size * 0.6:.2f} {ty + math.sin(a) * size:.2f} {lx + math.cos(a) * size * 1.2:.2f} "
                           f"{ty + math.sin(a) * size * 1.6:.2f}", stroke=tone, width=0.8)

    # --- sea cave ----------------------------------------------------------------------
    def _cave(self, w: float, h: float, seed: int, left: bool, right: bool, x0: float) -> Svg:
        """Wet sea-cave rock: teal reflections, barnacles and mussels, damp rim.
        The rim is always drawn (cave floors are often covered by room walls);
        thin slabs are ceilings and get seaweed and drips underneath."""
        r = Rand(seed)
        hr = self.terrain_headroom
        s = Svg(w, h + hr)
        y0 = hr
        bottom = h + hr
        s.rect(0, y0, w, h, fill=s.linear(0, y0, 0, y0 + 260, [(0, "#4f6f7c"), (0.14, "#34525f"), (0.46, "#1f3542"), (0.85, "#0c161e"), (1, "#080f16")]))
        for _ in range(max(2, int(w * min(h, 160) / 2200))):
            pr = r.uniform(5, 12)
            if w < pr * 3.2 + 8 or h < pr * 2 + 8:
                continue
            px, py = r.uniform(pr * 1.5 + 4, w - pr * 1.5 - 4), r.uniform(y0 + pr + 6, min(bottom - pr - 4, y0 + 160))
            s.path(blob(px, py, pr * 1.3, pr * 0.8, 0.15, seed=px), fill=r.choice(["#2c4652", "#3a5866", "#24404c"]), opacity=0.8)
            s.path(f"M{px - pr * 1.1:.2f} {py - pr * 0.1:.2f} Q{px - pr * 0.7:.2f} {py - pr * 0.75:.2f} {px + pr * 0.2:.2f} {py - pr * 0.78:.2f}",
                   stroke="#8fc8cc", width=0.9, opacity=0.35)
        xs = _samples(w, 4.0)
        for k, (base, amp, freq) in enumerate(((16.0, 3.0, 0.052), (27.0, 2.4, 0.071), (38.0, 2.0, 0.039))):
            if y0 + base > bottom - 6:
                break
            pts = [(lx, y0 + base + amp * math.sin((x0 + lx) * freq + k * 1.7) + 1.5 * math.sin((x0 + lx) * 0.19 + k)) for lx in xs]
            s.path(_line(pts), stroke="#7ff0e6", width=2.6, opacity=0.12 - k * 0.02)
            s.path(_line(pts), stroke="#bffaf2", width=0.8, opacity=0.4 - k * 0.1)
        if left:
            s.rect(0, y0, 5, h, fill=s.linear(0, y0, 0, bottom, [(0, "#9fe0e0", 0.35), (1, "#9fe0e0", 0.05)]))
            s.line(0.8, y0, 0.8, bottom, "#0a141c", 1.6)
        if right:
            s.rect(w - 6, y0, 6, h, fill="#050c14", opacity=0.45)
            s.line(w - 0.8, y0, w - 0.8, bottom, "#0a141c", 1.6)
        # damp rim along the top
        tops = [(lx, y0 - 0.8 + 0.7 * _wobble(x0 + lx, 0.9)) for lx in _samples(w, 2.0)]
        lows = [(lx, y0 + 5.0 + 1.4 * _wobble(x0 + lx, 2.2) + 1.4 * abs(math.sin((x0 + lx) * 0.17))) for lx in _samples(w, 2.0)]
        s.path(_line([(x, y + 2) for x, y in lows]), stroke="#050c14", width=3.0, opacity=0.4)
        s.path(_poly(tops + list(reversed(lows))), fill=s.linear(0, y0 - 2, 0, y0 + 8, [(0, "#a8c8c4"), (0.4, "#6a8e92"), (1, "#3a5a66")]))
        s.path(_line(lows), stroke="#0e1a24", width=1.0, opacity=0.9)
        s.path(_line([(x, y + 0.7) for x, y in tops]), stroke="#e0fbf6", width=1.1, opacity=0.85)
        for n in _slots(x0, w, 19.0, 6.0):
            lx = n * 19.0 + 12 * _hash(n, 51) - x0
            v = _hash(n, 52)
            if not 4 < lx < w - 4:
                continue
            if v > 0.78:  # a tiny glowing puddle
                s.ellipse(lx, y0 + 0.4, 3.5 + 2 * _hash(n, 53), 0.9, fill="#7ff4ea", opacity=0.75)
                s.line(lx - 2, y0 + 0.1, lx + 1, y0 + 0.1, "#ffffff", 0.6, 0.9)
            elif v > 0.5:  # barnacle cluster
                for j in range(3):
                    _barnacle(s, lx + (j - 1) * 2.4, y0 + 0.6 + (j % 2) * 0.6, 1.0 + 0.5 * _hash(n * 3 + j, 54))
            elif v > 0.3:  # mussels
                for j in range(2):
                    mx = lx + j * 3.2
                    s.ellipse(mx, y0 + 2.2, 2.0, 1.2, fill=s.linear(mx - 2, 0, mx + 2, 0, [(0, "#4a5a86"), (1, "#1a2038")]), stroke="#0a0e1a", width=0.4)
        if h <= 100:
            # thin slabs are ceilings: kelp strands and drips hang from their underside
            for n in _slots(x0, w, 15.0):
                lx = (n + 0.5) * 15.0 - x0
                if _hash(n, 41) < 0.45 or not 4 < lx < w - 5:
                    continue
                ln = 6 + 16 * _hash(n, 42)
                if _hash(n, 43) > 0.5:
                    pts = [(lx + 2.2 * math.sin(k * 1.3 + n), bottom - 1 + ln * k / 4) for k in range(5)]
                    s.path(smooth_open(pts), stroke="#2f6a4a", width=2.6)
                    s.path(smooth_open(pts), stroke="#5fa86a", width=1.2)
                else:
                    s.path(f"M{lx - 3:.2f} {bottom - 1:.2f} Q{lx - 0.6:.2f} {bottom + ln * 0.5:.2f} {lx:.2f} {bottom - 1 + ln * 0.7:.2f} "
                           f"Q{lx + 0.8:.2f} {bottom + ln * 0.4:.2f} {lx + 3:.2f} {bottom - 1:.2f} Z", fill="#2c4652", stroke="#0e1a24", width=0.6)
                    s.circle(lx, bottom + ln * 0.78, 0.9, fill="#9ff4ec", opacity=0.85)
        return s

    # --- galleon hull --------------------------------------------------------------------
    def _hull(self, w: float, h: float, seed: int, left: bool, right: bool, top: bool, x0: float) -> Svg:
        """Sunken-galleon planking (fortress style): world-aligned planks with
        treenails, algae streaks and barnacles, a deck rail on top."""
        r = Rand(seed)
        hr = self.terrain_headroom
        s = Svg(w, h + hr)
        y0 = hr
        s.rect(0, y0, w, h, fill=s.linear(0, y0, 0, y0 + min(h, 200), [(0, "#7a5a3e"), (0.5, "#4e3828"), (1, "#2a1e16")]))
        row_h = 12.0
        for row in range(int(h / row_h) + 1):
            yy = y0 + 7 + row * row_h
            offset = (row * 37) % 64
            first = math.floor((x0 - offset) / 64.0)
            gx = first * 64.0 + offset - x0
            idx = first
            while gx < w:
                bx0, bx1 = gx + 0.6, gx + 64 - 0.6
                tone = _hash(idx * 17 + row, 5)
                s.rect(max(0.0, bx0), yy + 0.6, min(w, bx1) - max(0.0, bx0), row_h - 1.2, fill=mix("#7a583c", "#5a4030", tone), opacity=0.9)
                s.line(max(0.0, bx0) + 1, yy + 1.8, min(w, bx1) - 1, yy + 1.8, "#a07a54", 0.8, 0.6)
                for ex in (bx0 + 3, bx1 - 3):
                    if 1 < ex < w - 1:
                        s.circle(ex, yy + row_h * 0.5, 0.9, fill="#3a281c")
                        s.circle(ex - 0.3, yy + row_h * 0.5 - 0.3, 0.35, fill="#c9a070", opacity=0.6)
                gx += 64.0
                idx += 1
            s.line(0, yy, w, yy, "#21160f", 1.1, 0.85)
        for _ in range(int(w / 60) + 1):
            ax = r.uniform(6, w - 6)
            ln = r.uniform(14, 40)
            s.path(smooth_open([(ax, y0 + 9), (ax + r.uniform(-2, 2), y0 + 9 + ln * 0.5), (ax + r.uniform(-1, 3), y0 + 9 + ln)]), stroke="#4f8a5a",
                   width=r.uniform(1.4, 3.0), opacity=0.45)
        for _ in range(int(w / 90) + 1):
            bx, by = r.uniform(10, w - 10), r.uniform(y0 + 30, min(y0 + h - 4, y0 + 120))
            for j in range(4):
                _barnacle(s, bx + (j - 1.5) * 2.6, by + (j % 2) * 1.6, 1.2)
        if left:
            s.rect(0, y0, 5, h, fill="#2a1e16")
            s.line(0.8, y0, 0.8, y0 + h, INK, 1.5)
        if right:
            s.rect(w - 5, y0, 5, h, fill="#1a120c")
            s.line(w - 0.8, y0, w - 0.8, y0 + h, INK, 1.5)
        # deck rail along the top (always: hull floors are often covered by the room walls)
        s.rect(0, y0 - 1, w, 7, fill=s.linear(0, y0 - 1, 0, y0 + 6, [(0, "#c49a6a"), (0.5, "#8a6440"), (1, "#5a3e26")]))
        s.line(0, y0 - 0.4, w, y0 - 0.4, "#f0d4a4", 1.2, 0.9)
        s.line(0, y0 + 6, w, y0 + 6, INK, 1.2)
        for n in _slots(x0, w, 24.0):
            nx = n * 24.0 + 12 - x0
            if 2 < nx < w - 2:
                s.circle(nx, y0 + 2.6, 1.1, fill=s.radial(nx - 0.4, y0 + 2.2, 1.4, [(0, BRASS_HI), (1, BRASS_DARK)]))
        return s

    # ------------------------------------------------------------------ indoor areas
    def interior(self, variant: str):
        if variant in ("underwater", "reef", "depths"):
            return self._underwater_backdrop, self._underwater_layer
        if variant in ("ship", "galleon", "wreck", "fortress"):
            return self._ship_backdrop, self._ship_layer
        return None

    def _kelp(self, s: Svg, x: float, base: float, hgt: float, seed: int, stem: str, blade: str, bladder: str, sway: float = 1.0,
              size: float = 1.0) -> None:
        """Giant kelp: a wavy stipe with long blades and air bladders."""
        n = int(hgt / (14 * size)) + 2
        pts = [(x + sway * (6 * math.sin(k * 0.7 + seed) + 3 * math.sin(k * 1.9 + seed * 2)), base - hgt * k / (n - 1)) for k in range(n)]
        s.path(smooth_open(pts), stroke=stem, width=2.4 * size)
        for k in range(1, n - 1):
            px, py = pts[k]
            side = 1 if (k + seed) % 2 else -1
            ln = (14 + 6 * math.sin(k * 1.3 + seed)) * size
            tip = (px + side * ln, py - ln * 0.55)
            s.path(f"M{px:.1f} {py:.1f} Q{px + side * ln * 0.45:.1f} {py - ln * 0.65:.1f} {tip[0]:.1f} {tip[1]:.1f} "
                   f"Q{px + side * ln * 0.6:.1f} {py - ln * 0.05:.1f} {px:.1f} {py:.1f} Z", fill=blade)
            if size > 1:
                s.path(f"M{px:.1f} {py:.1f} Q{px + side * ln * 0.5:.1f} {py - ln * 0.4:.1f} {tip[0]:.1f} {tip[1]:.1f}", stroke=shade(blade, 0.3),
                       width=0.8, opacity=0.6)
            s.circle(px + side * 2.2 * size, py - 1.5 * size, 2.0 * size, fill=bladder)

    def _underwater_backdrop(self) -> Svg:
        """Deep blue water: a bright rippled surface, god-rays, far reefs and kelp."""
        s = Svg(960, 540)
        r = Rand(23)
        s.rect(0, 0, 960, 540, fill=s.linear(0, 0, 0, 540, [(0, "#46b4d8"), (0.1, "#2a8fc2"), (0.38, "#18669e"), (0.7, "#0f4174"),
                                                            (1, "#0a2a55")]))
        surf = [(x, 16 + 4 * math.sin(x * 0.031) + 2 * math.sin(x * 0.113 + 1)) for x in range(0, 961, 10)]
        s.path(_line([(0, 0)] + surf + [(960, 0)]) + "Z", fill=s.linear(0, 0, 0, 22, [(0, "#e6fdff", 0.95), (1, "#a6ecf8", 0.6)]))
        s.path(_line(surf), stroke="#ffffff", width=1.4, opacity=0.8)
        for _ in range(26):
            x, y = r.uniform(0, 940), r.uniform(26, 90)
            ln = r.uniform(16, 60)
            s.path(f"M{x:.1f} {y:.1f} Q{x + ln / 2:.1f} {y - r.uniform(2, 6):.1f} {x + ln:.1f} {y:.1f}", stroke="#d8fbff", width=r.uniform(0.8, 1.8),
                   opacity=r.uniform(0.15, 0.35))
        for x, wd, lean, a in ((90, 60, 80, 0.15), (250, 34, 60, 0.11), (420, 90, 110, 0.14), (610, 50, 76, 0.12), (760, 80, 100, 0.15),
                               (900, 30, 50, 0.1)):
            s.polygon([(x - wd * 0.35, 0), (x + wd * 0.35, 0), (x + lean + wd, 540), (x + lean - wd, 540)],
                      fill=s.linear(0, 0, 0, 540, [(0, "#e0f8ff", a), (0.55, "#c4ecff", a * 0.45), (1, "#c4ecff", 0)]))
        # far reef ridges and kelp silhouettes in the blue haze
        for depth, (base, color, kelp) in enumerate(((420.0, "#1c5684", "#215f86"), (466.0, "#164873", "#1a527c"))):
            pts = [(0.0, 540.0)]
            x = 0.0
            while x <= 960:
                pts.append((x, base - r.uniform(10, 60) - 20 * math.sin(x * 0.012 + depth * 2)))
                x += r.uniform(30, 60)
            pts += [(960.0, base - 20), (960.0, 540.0)]
            for _ in range(7 - depth * 2):
                kx = r.uniform(20, 940)
                self._kelp(s, kx, base + 10, r.uniform(140, 260) - depth * 30, int(kx), kelp, kelp, kelp, 1.4)
            s.path(smooth_closed(pts, 0.5), fill=color)
            s.path(smooth_open(pts[1:-2], 0.5), stroke="#3a86b0", width=1.2, opacity=0.4)
        for _ in range(3):  # schools of small fish in the distance
            cx, cy = r.uniform(80, 880), r.uniform(120, 330)
            for k in range(12):
                fx, fy = cx + r.uniform(-50, 50), cy + r.uniform(-16, 16) + math.sin(k) * 6
                s.path(f"M{fx - 4:.1f} {fy:.1f} Q{fx:.1f} {fy - 2.2:.1f} {fx + 4:.1f} {fy:.1f} Q{fx:.1f} {fy + 2.2:.1f} {fx - 4:.1f} {fy:.1f} Z "
                       f"M{fx - 4:.1f} {fy:.1f} L{fx - 7:.1f} {fy - 2:.1f} L{fx - 7:.1f} {fy + 2:.1f} Z", fill="#5aa0c8", opacity=0.55)
        for _ in range(90):
            x, y = r.uniform(0, 960), r.uniform(30, 520)
            s.circle(x, y, r.uniform(0.6, 1.6), fill="#d8f4ff", opacity=r.uniform(0.2, 0.55))
        for k in range(4):  # rising bubble trails
            bx = r.uniform(60, 900)
            by = r.uniform(380, 520)
            for j in range(9):
                s.circle(bx + math.sin(j * 1.3 + k) * 3, by - j * r.uniform(14, 22), 1.0 + j * 0.25, stroke="#e8fbff", width=0.6, opacity=0.5)
        return s

    def _underwater_layer(self) -> Svg:
        """Kelp stalks and coral fans on reef rocks (900 × 420, tiles horizontally)."""
        w, h = 900.0, 420.0
        s = Svg(w, h)
        r = Rand(29)
        kelps = [(40.0, 250.0, 1.0), (110.0, 330.0, 1.35), (270.0, 380.0, 1.45), (350.0, 220.0, 1.0), (450.0, 290.0, 1.3), (640.0, 360.0, 1.45),
                 (720.0, 240.0, 1.0), (830.0, 320.0, 1.3)]
        fans = [(185.0, 62.0, "#b45ac8"), (540.0, 70.0, "#f08a4a"), (760.0, 56.0, "#d65a8a")]
        for shift in (-w, 0.0, w):
            for kx, hgt, size in kelps:
                x = kx + shift
                if -80 < x < w + 80:
                    tone = ("#4f6e3a", "#6a8a40", "#98a844") if size < 1.2 else ("#5a7a3a", "#7c9c44", "#b0c04c")
                    self._kelp(s, x, h - 8, hgt, int(kx), tone[0], tone[1], tone[2], size=size)
        rocks = []
        x = -20.0
        while x < w + 20:
            rad = r.uniform(18, 34)
            rocks.append((x, rad))
            x += r.uniform(36, 64)
        for shift in (-w, 0.0, w):
            for fx, size, tone in fans:
                x = fx + shift
                if -size < x < w + size:
                    self._fan(s, x, h - 18, size, tone, int(fx))
        for rx, rad in rocks:
            s.path(blob(rx, h - rad * 0.35, rad * 1.3, rad * 0.7, 0.12, seed=rx), fill=s.linear(0, h - rad, 0, h, [(0, "#5a4a7a"), (1, "#2a2448")]))
            s.path(f"M{rx - rad:.1f} {h - rad * 0.55:.1f} Q{rx - rad * 0.5:.1f} {h - rad * 1.0:.1f} {rx + rad * 0.3:.1f} {h - rad * 0.98:.1f}",
                   stroke="#9a8ac8", width=1.4, opacity=0.6)
        for shift in (-w, 0.0, w):
            for bx, tone in ((120.0, "#e8b06a"), (360.0, "#c9a0e0"), (600.0, "#f09a7a"), (860.0, "#9ad08a")):
                x = bx + shift
                if -20 < x < w + 20:
                    s.path(f"M{x - 14:.1f} {h - 22:.1f} Q{x - 14:.1f} {h - 40:.1f} {x:.1f} {h - 40:.1f} Q{x + 14:.1f} {h - 40:.1f} {x + 14:.1f} {h - 22:.1f} Z",
                           fill=s.radial(x - 4, h - 38, 22, [(0, shade(tone, 0.3)), (1, shade(tone, -0.35))]))
                    for k in range(3):
                        y = h - 36 + k * 5
                        s.path(f"M{x - 10 + k:.1f} {y:.1f} Q{x - 4:.1f} {y - 3:.1f} {x:.1f} {y:.1f} Q{x + 5:.1f} {y + 3:.1f} {x + 10 - k:.1f} {y:.1f}",
                               stroke=shade(tone, -0.45), width=0.9, opacity=0.8)
        return s

    def _fan(self, s: Svg, x: float, base: float, size: float, tone: str, seed: int, line: str | None = None) -> None:
        """Sea fan (gorgonian): a branching lattice laced with a fine mesh."""
        r = Rand(seed)
        branches = [((x, base), -90.0, size * 0.4, 3.0, 0)]
        segs = []
        tips = []
        while branches:
            (px, py), ang, ln, wd, depth = branches.pop()
            ex = px + math.cos(math.radians(ang)) * ln
            ey = py + math.sin(math.radians(ang)) * ln
            segs.append((px, py, ex, ey, wd))
            if depth < 4:
                spread = 34.0 if depth == 0 else 22.0
                for da in (-spread, spread * 0.85):
                    branches.append(((ex, ey), ang + da + r.uniform(-7, 7), ln * 0.8, wd * 0.72, depth + 1))
            else:
                tips.append((ex, ey))
        tips.sort(key=lambda q: math.atan2(q[1] - base, q[0] - x))
        s.path(smooth_closed([(x - 2, base)] + tips + [(x + 2, base)], 0.4), fill=tone, opacity=0.22)
        for a, b in zip(tips, tips[1:]):  # the mesh between neighbouring twigs
            s.line(a[0], a[1], b[0], b[1], tone, 0.7, 0.7)
        if line:
            for px, py, ex, ey, wd in segs:
                s.line(px, py, ex, ey, line, wd + 1.1)
        for px, py, ex, ey, wd in segs:
            s.line(px, py, ex, ey, tone, wd)
        for px, py, ex, ey, wd in segs[::2]:
            s.line(px, py, ex, ey, shade(tone, 0.45), wd * 0.35, 0.8)
        for tx, ty in tips[::2]:
            s.circle(tx, ty, 0.9, fill=shade(tone, 0.5))

    def _ship_backdrop(self) -> Svg:
        """Inside the listing hull of a sunken galleon: ribs, planking, lit portholes,
        barnacles, hanging lanterns and a flooded bilge in greenish half-light."""
        s = Svg(960, 540)
        r = Rand(31)
        s.rect(0, 0, 960, 540, fill=s.linear(0, 0, 0, 540, [(0, "#162420"), (0.45, "#22362e"), (1, "#121c18")]))
        with s.group(transform="rotate(-5 480 270)"):
            for row in range(-2, 24):
                y = -60 + row * 28
                s.rect(-80, y + 1, 1120, 26, fill=mix("#3e3a2a", "#4a4230", _hash(row, 3)))
                s.line(-80, y + 2.5, 1040, y + 2.5, "#6a5e44", 1.4, 0.5)
                s.line(-80, y + 26, 1040, y + 26, "#14100c", 2.0, 0.8)
                off = (row * 57) % 150
                for bx in range(-80 + off, 1040, 150):
                    s.line(bx, y + 2, bx, y + 26, "#14100c", 1.6, 0.7)
            for k, px in enumerate((150, 480, 810)):  # portholes with light pouring in
                py = 210 + k * 6
                s.polygon([(px - 18, py), (px + 18, py), (px + 150, 640), (px - 60, 640)], fill="#9fe8c8", opacity=0.06)
                s.circle(px, py, 34, fill=s.radial(px, py, 34, [(0, "#c8fff0", 0.7), (1, "#7ad0b0", 0)]))
                s.circle(px, py, 20, fill=s.radial(px - 5, py - 5, 22, [(0, "#e6fff6"), (0.6, "#8adcc0"), (1, "#3a8a7a")]), stroke=BRASS_DARK, width=6)
                s.circle(px, py, 20, stroke=BRASS, width=2.2)
                for a in range(0, 360, 45):
                    s.circle(px + math.cos(math.radians(a)) * 20, py + math.sin(math.radians(a)) * 20, 1.4, fill=BRASS_HI)
            for k in range(9):  # ribs
                rx = -40 + k * 128
                s.path(f"M{rx:.1f} -80 Q{rx + 26:.1f} 270 {rx + 4:.1f} 640 L{rx + 34:.1f} 640 Q{rx + 56:.1f} 270 {rx + 30:.1f} -80 Z",
                       fill=s.linear(rx, 0, rx + 40, 0, [(0, "#6a4a30"), (0.4, "#4a3420"), (1, "#22160e")]))
                s.path(f"M{rx + 3:.1f} -80 Q{rx + 29:.1f} 270 {rx + 7:.1f} 640", stroke="#a07a50", width=1.4, opacity=0.5)
                for j in range(5):
                    by = r.uniform(60, 480)
                    _barnacle(s, rx + 16 + 8 * math.sin(by * 0.006), by, 2.2)
            s.rect(-80, -60, 1120, 40, fill="#2a1e14")
            s.line(-80, -20, 1040, -20, "#5a4430", 2.0, 0.8)
            for k in range(10):  # seaweed hanging from the beams
                hx = r.uniform(0, 960)
                pts = [(hx + 5 * math.sin(j * 1.1 + k), -20 + j * r.uniform(12, 18)) for j in range(6)]
                s.path(smooth_open(pts), stroke="#3f7a4a", width=r.uniform(2, 4), opacity=0.75)
        for lx in (300.0, 660.0):  # lanterns hang plumb, not with the listing hull
            s.line(lx, 0, lx, 120, "#2a2018", 1.6)
            s.circle(lx, 140, 60, fill=s.radial(lx, 140, 60, [(0, "#ffe6a0", 0.5), (0.4, GLOW, 0.18), (1, GLOW, 0)]))
            s.path(rounded_rect_path(lx - 9, 124, 18, 30, 4), fill=s.radial(lx, 138, 14, [(0, "#ffffff"), (0.4, "#ffe08a"), (1, "#e09a3a")]),
                   stroke=BRASS_DARK, width=2)
            s.path(f"M{lx - 11:.1f} 124 L{lx:.1f} 114 L{lx + 11:.1f} 124 Z", fill=BRASS, stroke=BRASS_DARK, width=1.2)
            s.rect(lx - 10, 153, 20, 4, fill=BRASS, rx=1.5)
        # the flooded bilge: water stays level while the hull lists
        s.rect(0, 452, 960, 88, fill=s.linear(0, 452, 0, 540, [(0, "#3a8a6a", 0.55), (1, "#0e2a22", 0.9)]))
        s.path(_line([(x, 452 + 1.6 * math.sin(x * 0.05)) for x in range(0, 961, 8)]), stroke="#bff4d8", width=1.6, opacity=0.7)
        for _ in range(50):
            s.circle(r.uniform(0, 960), r.uniform(20, 520), r.uniform(0.6, 1.5), fill="#d8f4c8", opacity=r.uniform(0.15, 0.45))
        return s

    def _ship_layer(self) -> Svg:
        """Heavy knees, a mast stump with rope coils and a hanging lantern (tiles)."""
        w, h = 900.0, 420.0
        s = Svg(w, h)
        for shift in (-w, 0.0, w):
            for kx in (120.0, 560.0):
                x = kx + shift
                if x < -80 or x > w + 80:
                    continue
                s.path(f"M{x - 18:.1f} {h:.1f} L{x - 18:.1f} 0 L{x + 18:.1f} 0 L{x + 18:.1f} {h:.1f} Z",
                       fill=s.linear(x - 18, 0, x + 18, 0, [(0, "#6a4a30"), (0.35, "#8a6440"), (1, "#3a2818")]))
                for y in (60.0, 230.0):
                    s.rect(x - 21, y, 42, 9, fill=s.linear(0, y, 0, y + 9, [(0, BRASS_HI), (1, BRASS_DARK)]), rx=2)
                for k in range(3):
                    cy = h - 20 - k * 9
                    s.ellipse(x + 30, cy, 22 - k * 3, 5, fill="#c8a870", stroke="#6a5030", width=1.4)
                s.path(f"M{x + 18:.1f} 40 Q{x + 60:.1f} 90 {x + 120:.1f} 30", stroke="#c8a870", width=2.4)
            lx = 340.0 + shift
            if -40 < lx < w + 40:
                s.line(lx, 0, lx, 120, "#2a2018", 1.6)
                s.circle(lx, 142, 40, fill=s.radial(lx, 142, 40, [(0, "#ffe6a0", 0.55), (1, GLOW, 0)]))
                s.path(rounded_rect_path(lx - 8, 128, 16, 26, 4), fill=s.radial(lx, 140, 12, [(0, "#ffffff"), (0.45, "#ffe08a"), (1, "#e09a3a")]),
                       stroke=BRASS_DARK, width=1.8)
                s.path(f"M{lx - 10:.1f} 128 L{lx:.1f} 119 L{lx + 10:.1f} 128 Z", fill=BRASS, stroke=BRASS_DARK, width=1)
        return s

    def cave_sky(self) -> Svg:
        """Sea cave: a vault lit by teal reflections dancing up from a glowing pool,
        and a bright arch opening onto the sea."""
        s = Svg(960, 540)
        r = Rand(77)
        s.rect(0, 0, 960, 540, fill=s.linear(0, 0, 0, 540, [(0, "#06121a"), (0.45, "#0e2632"), (0.8, "#123a44"), (1, "#0a2630")]))
        # the sea arch at the far end
        s.path("M600 430 Q606 250 700 230 Q800 226 812 430 Z", fill=s.linear(0, 230, 0, 430, [(0, "#bff0f4"), (0.55, "#58c4dc"), (1, "#1f86aa")]))
        s.path("M600 430 L812 430 L812 410 Q706 396 600 412 Z", fill="#2a9cc0")
        _soft(s, 706, 330, 160, 120, "#9fe8ee", 0.25, 0.1)
        # back wall masses
        for k, (color, base) in enumerate((("#0f2630", 470.0), ("#14303a", 500.0))):
            pts = [(0.0, 540.0)] + [(x, base - r.uniform(30, 150) * (1 - k * 0.35)) for x in range(0, 1001, 80)] + [(960.0, 540.0)]
            if k == 0:
                pts = [(x, y if not 560 < x < 850 else max(y, 430.0)) for x, y in pts]
            s.path(smooth_closed(pts, 0.45), fill=color)
        # glowing tide pool on the floor
        _soft(s, 300, 506, 300, 50, "#3fe8dc", 0.55, 0.2)
        s.path("M40 520 Q300 492 600 518 L600 540 L40 540 Z", fill=s.linear(0, 492, 0, 540, [(0, "#6ff4e6"), (1, "#1a8a8a")]), opacity=0.85)
        s.path("M60 516 Q300 494 580 514", stroke="#e6fffb", width=1.4, opacity=0.8)
        # caustics: the pool throws a net of light onto the vault
        for _ in range(70):
            cx, cy = r.uniform(0, 960), r.uniform(20, 300)
            ln = r.uniform(18, 46)
            a = r.uniform(-0.5, 0.5)
            pts = [(cx + math.cos(a) * ln * t + math.sin(t * 6 + cx) * 4, cy + math.sin(a) * ln * t + math.cos(t * 5 + cy) * 3) for t in (0, 0.33, 0.66, 1)]
            s.path(smooth_open(pts), stroke="#7ff4ea", width=r.uniform(0.8, 2.0), opacity=r.uniform(0.12, 0.35) * (1.0 if cy < 220 else 0.6))
        for cx, cy, rr in ((240, 120, 120), (420, 70, 90), (130, 260, 80)):
            _soft(s, cx, cy, rr, rr * 0.5, "#5fe0d8", 0.14, 0.2)
        # stalactites, seaweed and drips along the vault
        ceiling = [(0.0, 40.0)]
        x = 0.0
        while x < 960:
            x += r.uniform(36, 70)
            ceiling.append((min(960.0, x), r.uniform(24, 60)))
        s.path("M0 0 L960 0 " + " ".join(f"L{px:.1f} {py:.1f}" for px, py in reversed(ceiling)) + " Z", fill="#050e14")
        for _ in range(18):
            sx = r.uniform(10, 950)
            ln = r.uniform(26, 90)
            sw = r.uniform(6, 16)
            s.polygon([(sx - sw, 30), (sx + sw, 30), (sx + sw * 0.15, 30 + ln), (sx - sw * 0.1, 30 + ln * 0.9)],
                      fill=s.linear(0, 30, 0, 30 + ln, [(0, "#050e14"), (1, "#1c3c48")]))
            s.path(f"M{sx - sw * 0.6:.1f} 36 L{sx - sw * 0.05:.1f} {30 + ln * 0.85:.1f}", stroke="#5fd8d0", width=1.0, opacity=0.4)
            if r.next() < 0.5:
                s.circle(sx + sw * 0.05, 30 + ln + 4, 1.4, fill="#9ff8f0", opacity=0.85)
        for _ in range(12):
            hx = r.uniform(0, 960)
            pts = [(hx + 4 * math.sin(j * 1.2 + hx), 30 + j * r.uniform(10, 16)) for j in range(6)]
            s.path(smooth_open(pts), stroke="#1f4a3a", width=r.uniform(2.0, 3.6), opacity=0.9)
        for _ in range(30):
            px, py = r.uniform(0, 960), r.uniform(80, 500)
            if r.next() < 0.3:
                _sparkle(s, px, py, r.uniform(1.6, 3.0), 0.6, "#c8fff8")
            else:
                s.circle(px, py, r.uniform(0.7, 1.6), fill="#9ff4ec", opacity=r.uniform(0.3, 0.7))
        return s

    # ------------------------------------------------------------------ blocks and platforms
    def block(self, kind: str, w: float, h: float) -> Svg:
        s = Svg(w, h)
        if kind in ("question", "used"):
            self._nacre_block(s, w, h, kind == "used")
        elif kind == "brick":
            self._coral_bricks(s, w, h)
        return s

    def _nacre_block(self, s: Svg, w: float, h: float, used: bool) -> None:
        """Polished mother-of-pearl block with a golden sea-star emblem; once
        used it turns dull and the emblem is gone (an empty socket remains)."""
        if used:
            face = s.linear(0, 0, w * 0.4, h, [(0, "#e2dccf"), (0.55, "#bcb2a0"), (1, "#8c8170")])
        else:
            face = s.linear(0, 0, w, h, [(0, "#fffaf2"), (0.25, "#f6d8ea"), (0.5, "#d2eef8"), (0.75, "#f6e8c6"), (1, "#d6c2ee")])
        s.path(rounded_rect_path(0.6, 0.6, w - 1.2, h - 1.2, 5), fill=face, stroke=INK, width=1.3)
        if not used:
            for k, (col, op) in enumerate((("#ffffff", 0.5), ("#ffc4e2", 0.35), ("#b8eeff", 0.4), ("#fff0b8", 0.3))):
                y = h * (0.2 + 0.2 * k)
                s.path(smooth_open([(2.5, y + 1.6), (w * 0.3, y - 1.6), (w * 0.64, y + 1.8), (w - 2.5, y - 0.8)]), stroke=col, width=2.0, opacity=op)
        s.path(rounded_rect_path(2.6, 2.6, w - 5.2, h - 5.2, 3.6), stroke="#ffffff" if not used else "#f0e8da", width=1.1, opacity=0.8 if not used else 0.4)
        s.path(f"M4 {h - 2.8:.1f} L{w - 4:.1f} {h - 2.8:.1f}", stroke="#7a6a8e" if not used else "#5e5446", width=1.3, opacity=0.5)
        for cx, cy in ((4.4, 4.4), (w - 4.4, 4.4), (4.4, h - 4.4), (w - 4.4, h - 4.4)):
            if used:
                s.circle(cx, cy, 1.3, fill="#8a8070", stroke="#5e5446", width=0.4)
            else:
                s.circle(cx, cy, 1.6, fill=s.radial(cx - 0.5, cy - 0.5, 1.8, [(0, "#ffffff"), (0.6, "#f2e6f6"), (1, "#b4a4c8")]), stroke="#6a5a7a", width=0.4)
        cx, cy = w / 2, h / 2 + 0.3
        rad = min(w, h) * 0.37
        if not used:
            s.circle(cx, cy, rad * 1.4, fill=s.radial(cx, cy, rad * 1.4, [(0, "#fff3c0", 0.9), (0.5, GLOW, 0.4), (1, GLOW, 0)]))
            star = star_points(cx, cy, rad, rad * 0.44, 5)
            s.path(smooth_closed(star, 0.32), fill=s.linear(cx - rad, cy - rad, cx + rad, cy + rad, [(0, "#fffbe0"), (0.45, "#ffd060"), (1, "#d8861c")]),
                   stroke="#8a4e10", width=0.9)
            for k in range(5):
                a = math.radians(-90 + k * 72)
                for j in (0.42, 0.7):
                    s.circle(cx + math.cos(a) * rad * j, cy + math.sin(a) * rad * j, max(0.4, rad * 0.07), fill="#fff6c8")
            s.circle(cx, cy, rad * 0.17, fill="#fff3c0", stroke="#b8701a", width=0.5)
            _sparkle(s, w * 0.24, h * 0.3, 2.2, 0.95)
        else:
            star = star_points(cx, cy, rad * 0.9, rad * 0.4, 5)
            s.path(smooth_closed(star, 0.32), fill="#9a8e7c", stroke="#6e6252", width=0.7, opacity=0.5)
            s.path(smooth_closed([(x, y + 0.7) for x, y in star], 0.32), stroke="#f0e6d6", width=0.5, opacity=0.4)
            s.path(f"M{w * 0.66:.1f} 2.5 l-1.6 4 l2 2.6 l-1.2 3", stroke="#6e6252", width=0.7, opacity=0.7)

    def _coral_bricks(self, s: Svg, w: float, h: float) -> None:
        """Blocks of cut coral stone: porous salmon-cream limestone with polyp marks."""
        s.path(rounded_rect_path(0.6, 0.6, w - 1.2, h - 1.2, 3), fill="#8e4a42", stroke=INK, width=1.2)
        rows = max(2, int(round(h / 11)))
        rh = (h - 2) / rows
        bw = 20.0
        for row in range(rows):
            y = 1 + row * rh
            x = -(bw / 2 if row % 2 else 0.0)
            i = 0
            while x < w:
                bx0, bx1 = max(1.4, x + 1.1), min(w - 1.4, x + bw - 1.1)
                if bx1 > bx0 + 2:
                    tone = _hash(row * 31 + i, 3)
                    top_c = mix("#ffe6c8", "#ffc8a2", tone)
                    s.path(rounded_rect_path(bx0, y + 1.0, bx1 - bx0, rh - 2.0, 1.8),
                           fill=s.linear(0, y, 0, y + rh, [(0, top_c), (0.55, mix("#f0a682", "#e8987a", tone)), (1, mix("#c8705a", "#b8644e", tone))]),
                           stroke="#6e3430", width=0.7)
                    s.line(bx0 + 1, y + 2.1, bx1 - 1, y + 2.1, "#fff6ea", 0.9, 0.8)
                    for j in range(3):
                        px = bx0 + 2 + (bx1 - bx0 - 4) * _hash(row * 97 + i * 7 + j, 4)
                        py = y + 3.5 + (rh - 6) * _hash(row * 89 + i * 5 + j, 6)
                        s.circle(px, py, 0.5 + 0.5 * _hash(i + j, 8), fill="#8a4a44", opacity=0.6)
                    if _hash(row * 13 + i, 9) > 0.55 and bx1 - bx0 > 9:
                        px, py = (bx0 + bx1) / 2 + 2, y + rh * 0.55
                        for k in range(6):
                            a = k * math.pi / 3
                            s.line(px, py, px + math.cos(a) * 1.8, py + math.sin(a) * 1.8, "#b46a5a", 0.5, 0.75)
                x += bw
                i += 1

    def platform(self, kind: str, w: float, h: float, style: str = "") -> Svg:
        if kind == "ledge":
            if any(k in style for k in ("float", "islet", "reef", "coral")):
                return self._islet(w, h, "ice" in style)
            return self.terrain("terrain", w, h, int(w * 7 + h), True, True, True, 0.0, "ice" if "ice" in style else "normal")
        if kind == "crumble":
            return self._sand_crumble(w, h)
        s = Svg(w, h + 12)
        if kind == "moving":
            self._raft(s, w, h)
        elif kind == "semisolid":
            self._jetty(s, w, h)
        elif kind == "spring":
            self._clam_spring(s, w, h)
        else:  # conveyor and other belts
            self._rope_belt(s, w, h)
        return s

    def _islet(self, w: float, h: float, slick: bool) -> Svg:
        """Floating coral-rock islet: coralline top, rounded underside with growths."""
        hr = self.terrain_headroom
        extra = 16.0
        s = Svg(w, h + hr + extra)
        y0, y1 = hr, hr + h
        r = Rand(int(w * 13 + h))
        bottom = []
        n = max(6, int(w / 8))
        for i in range(n + 1):
            t = i / n
            x = w - 2 - (w - 4) * t
            bottom.append((x, y1 - 4 + extra * 0.85 * math.sin(math.pi * t) ** 0.9 + r.uniform(-1.5, 1.5) * math.sin(math.pi * t)))
        outline = [(1.5, y0 + 2), (w - 1.5, y0 + 2)] + bottom
        s.path(_line([(x, y + 2.5) for x, y in bottom]), stroke="#140a24", width=4.0, opacity=0.25)
        s.path(_poly(outline), fill=s.linear(0, y0, 0, y1 + extra, [(0, REEF_TOP), (0.35, REEF), (0.75, REEF_LOW), (1, REEF_DEEP)]))
        for _ in range(int(w / 26) + 1):
            pr = r.uniform(4, 8)
            px = r.uniform(pr + 6, w - pr - 6)
            py = r.uniform(y0 + 10, y1 + 2)
            s.path(blob(px, py, pr * 1.3, pr, 0.12, seed=px), fill=r.choice(["#c27a9a", "#a9658a", "#d08aa2"]), opacity=0.7)
            s.path(f"M{px - pr:.2f} {py - pr * 0.2:.2f} Q{px - pr * 0.6:.2f} {py - pr:.2f} {px + pr * 0.3:.2f} {py - pr * 0.95:.2f}", stroke="#ffd2de",
                   width=1.0, opacity=0.5)
        for _ in range(int(w / 12)):
            s.circle(r.uniform(6, w - 6), r.uniform(y0 + 8, y1 + 4), r.uniform(0.6, 1.4), fill="#3a2040", opacity=0.5)
        for i in range(1, len(bottom) - 1, 2):
            px, py = bottom[i]
            if r.next() < 0.6:
                ln = r.uniform(5, 14)
                pts = [(px + 1.8 * math.sin(k * 1.4 + px), py - 1 + ln * k / 3) for k in range(4)]
                s.path(smooth_open(pts), stroke="#2f6a4a", width=2.2)
                s.path(smooth_open(pts), stroke="#6ab86a", width=1.0)
        s.path(_poly(outline), stroke=REEF_LINE, width=1.2)
        if slick:
            self._algae_cap(s, w, y0, True, True, 0.0)
        else:
            self._reef_cap(s, w, y0, True, True, 0.0)
        return s

    def _raft(self, s: Svg, w: float, h: float) -> None:
        """Driftwood raft: a bleached plank deck lashed onto a long float log, a
        buoy hanging off one end."""
        deck = max(6.0, h * 0.48)
        lr = min(h * 0.36, 6.5)
        ly = deck + lr * 0.8
        log = (f"M{6:.1f} {ly - lr:.1f} L{w - 6:.1f} {ly - lr:.1f} Q{w - 1.5:.1f} {ly:.1f} {w - 6:.1f} {ly + lr:.1f} L{6:.1f} {ly + lr:.1f} "
               f"Q{1.5:.1f} {ly:.1f} {6:.1f} {ly - lr:.1f} Z")
        s.path(log, fill=s.linear(0, ly - lr, 0, ly + lr, [(0, "#d8c4a0"), (0.4, "#a8875e"), (1, "#5e4630")]), stroke=INK, width=1.1)
        for k in range(int(w / 16)):
            gx = 10 + k * 16 + 6 * _hash(k, 75)
            if gx < w - 10:
                s.path(f"M{gx:.1f} {ly - lr * 0.4:.1f} Q{gx + 5:.1f} {ly - lr * 0.6:.1f} {gx + 9:.1f} {ly - lr * 0.3:.1f}", stroke="#5e4630", width=0.7,
                       opacity=0.6)
        s.ellipse(w - 6.5, ly, lr * 0.45, lr * 0.85, fill=s.radial(w - 6.5, ly, lr, [(0, "#f2e2c4"), (1, "#b49468")]), stroke="#5e4630", width=0.6)
        s.ellipse(w - 6.5, ly, lr * 0.2, lr * 0.4, stroke="#8a6a46", width=0.5)
        for k in range(4):
            ax = 8 + (w - 16) * (k + 0.5) / 4
            s.path(f"M{ax:.1f} {ly + lr - 0.5:.1f} Q{ax + 1.4:.1f} {ly + lr + 3:.1f} {ax - 0.8:.1f} {ly + lr + 4.5:.1f}", stroke="#4f8a5a", width=1.3,
                   opacity=0.75)
        s.path(rounded_rect_path(0.8, 0.8, w - 1.6, deck, 3), fill=s.linear(0, 0.8, 0, deck, [(0, DRIFT_HI), (0.5, DRIFT), (1, DRIFT_DARK)]), stroke=INK,
               width=1.2)
        x = 0.8
        k = 0
        while x < w - 6:
            pw = 22 + 14 * _hash(k, 71)
            if x + pw < w - 4:
                s.line(x + pw, 2.2, x + pw, deck - 0.6, "#6a5e50", 0.9, 0.8)
            for j in range(2):
                gy = 2.6 + (deck - 4) * (0.3 + 0.4 * j)
                s.path(f"M{x + 3:.1f} {gy:.1f} Q{x + pw * 0.5:.1f} {gy + (1.2 if j else -1.0):.1f} {min(w - 3, x + pw - 3):.1f} {gy:.1f}",
                       stroke="#8a7c6a", width=0.6, opacity=0.6)
            x += pw
            k += 1
        s.line(3, 1.8, w - 3, 1.8, "#ffffff", 1.0, 0.7)
        for lx in (w * 0.2, w * 0.5, w * 0.8):
            for j in range(3):
                yy = 0.8 + j * (ly + lr - 0.8) / 3
                d = f"M{lx - 2.4:.1f} {yy:.1f} L{lx + 2.4:.1f} {yy + (ly + lr) / 3:.1f}"
                s.path(d, stroke=INK, width=2.3)
                s.path(d, stroke="#e8d4a4", width=1.2)
        bx, by = w - 9.0, h + 7.0
        s.path(f"M{w - 6:.1f} {ly:.1f} Q{w - 4:.1f} {(ly + by) / 2:.1f} {bx:.1f} {by - 4.2:.1f}", stroke="#d8c49a", width=1.0)
        s.circle(bx, by, 4.4, fill=s.radial(bx - 1.4, by - 1.4, 5, [(0, "#ff9a8a"), (0.6, "#e0483e"), (1, "#9a2a26")]), stroke=INK, width=0.9)
        s.path(f"M{bx - 4.3:.1f} {by - 0.6:.1f} Q{bx:.1f} {by + 1.2:.1f} {bx + 4.3:.1f} {by - 0.6:.1f} L{bx + 4.1:.1f} {by + 1.4:.1f} "
               f"Q{bx:.1f} {by + 3.2:.1f} {bx - 4.1:.1f} {by + 1.4:.1f} Z", fill="#ffffff", stroke=INK, width=0.5)

    def _sand_crumble(self, w: float, h: float) -> Svg:
        """Packed sand moulded like a sandcastle: bucket towers, pressed shells,
        drips along the bottom and cracks that say it will give way."""
        s = Svg(w, h + 6)
        r = Rand(int(w * 3 + h))
        lip = [(w - 2, h - 2)]
        x = w - 2
        while x > 4:
            x -= r.uniform(4, 8)
            lip.append((max(2.0, x), h - 1 + r.uniform(0, 4) * (1 if r.next() > 0.4 else 0.2)))
        body = [(1.2, 3), (3.5, 0.8), (w - 3.5, 0.8), (w - 1.2, 3)] + lip + [(1.2, h - 2)]
        s.path(_line([(px, py + 2.2) for px, py in lip]), stroke="#4a2a20", width=3.5, opacity=0.25)
        s.polygon(body, fill=s.linear(0, 0, 0, h + 3, [(0, "#fbe2a8"), (0.35, "#e8c47c"), (1, "#c2925a")]), stroke=INK, width=1.2)
        tw = 14.0
        n = max(1, int((w - 6) / (tw + 6)))
        gap = (w - n * tw) / (n + 1)
        for i in range(n):
            tx = gap + i * (tw + gap)
            s.path(rounded_rect_path(tx, 3.5, tw, h - 6, 3), fill="#f8dca0", opacity=0.55)
            for j in range(1, 3):
                yy = 3.5 + (h - 6) * j / 3
                s.line(tx + 1, yy, tx + tw - 1, yy, "#b88a50", 0.7, 0.6)
            s.path(f"M{tx + tw / 2 - 2:.1f} {h - 3:.1f} L{tx + tw / 2 - 2:.1f} {h * 0.5:.1f} Q{tx + tw / 2:.1f} {h * 0.5 - 3:.1f} {tx + tw / 2 + 2:.1f} "
                   f"{h * 0.5:.1f} L{tx + tw / 2 + 2:.1f} {h - 3:.1f} Z", fill="#7a5032", opacity=0.75)
        for i in range(n + 1):
            sx = gap / 2 + i * (tw + gap) - (tw + gap) * 0 + (0 if i == 0 else 0)
            if 6 < sx < w - 6 and h > 14:
                _scallop(s, sx, h * 0.62, 2.6, "#fbe0d0", width=0.4)
        s.line(4, 1.6, w - 4, 1.6, "#fff6d8", 1.3, 0.95)
        for _ in range(int(w / 3)):
            s.circle(r.uniform(3, w - 3), r.uniform(3, h - 3), r.uniform(0.25, 0.6), fill=r.choice(["#fff4d8", "#b48450"]), opacity=0.7)
        for _ in range(3):
            cx = r.uniform(8, w - 8)
            pts = [(cx, 1.4), (cx + r.uniform(-4, 4), h * 0.4), (cx + r.uniform(-5, 5), h * 0.72), (cx + r.uniform(-3, 3), h - 1)]
            s.path(_line(pts), stroke="#5a3418", width=1.2)
            s.path(_line([(px + 0.8, py) for px, py in pts]), stroke="#fff0c8", width=0.6, opacity=0.8)
            bx, by = pts[1]
            s.path(_line([(bx, by), (bx + r.uniform(3, 7), by + r.uniform(-2, 2))]), stroke="#5a3418", width=0.9)
        for px, py in lip[1:-1:2]:
            if r.next() < 0.5:
                s.circle(px, py + r.uniform(2.5, 4.5), r.uniform(0.6, 1.1), fill="#d8b070", opacity=0.85)
        return s

    def _jetty(self, s: Svg, w: float, h: float) -> None:
        """Wooden jetty planks on piles (one-way platform)."""
        top_h = min(h, 8.0)
        for px in [x for x in range(12, int(w) - 4, 34)]:
            s.path(rounded_rect_path(px - 2.4, top_h - 1, 4.8, h + 11 - top_h, 1.5), fill=s.linear(px - 2.4, 0, px + 2.4, 0, [(0, WOOD_LIGHT), (1, WOOD_DARK)]),
                   stroke=INK, width=0.9)
            for j in range(2):
                _barnacle(s, px - 1 + j * 2.2, h + 8 - j * 2.4, 0.9)
            s.path(blob(px, h + 4, 3.2, 1.6, 0.2, seed=px), fill="#4f8a5a", opacity=0.8)
        s.path(rounded_rect_path(0.6, 0.8, w - 1.2, top_h, 2.4), fill=s.linear(0, 0.8, 0, top_h + 0.8, [(0, "#e2b888"), (0.5, "#b4865a"), (1, "#7a5434")]),
               stroke=INK, width=1.1)
        x = 9.0
        while x < w - 3:
            s.line(x, 1.6, x, top_h, "#5a3a22", 0.8, 0.75)
            s.circle(x - 3.2, top_h * 0.5 + 0.8, 0.55, fill="#3a2a22")
            x += 9.0
        s.line(2.5, 1.7, w - 2.5, 1.7, "#fff0d0", 1.0, 0.85)
        s.path(f"M2 {top_h + 1.6:.1f} Q{w / 2:.1f} {top_h + 5:.1f} {w - 2:.1f} {top_h + 1.6:.1f}", stroke="#d8c49a", width=1.2)

    def _clam_spring(self, s: Svg, w: float, h: float) -> None:
        """A puffy yellow sea sponge cushioned in an open scallop shell (spring)."""
        cx = w / 2
        sy = h * 0.62  # where the sponge sits in the shell
        rim = [(cx + math.cos(math.radians(a)) * w * 0.49, sy + math.sin(math.radians(a)) * (h + 9 - sy)) for a in range(0, 181, 12)]
        s.path(_poly([(cx + w * 0.49, sy)] + rim[1:-1] + [(cx - w * 0.49, sy)]),
               fill=s.linear(0, sy, 0, h + 9, [(0, "#fff4f2"), (0.5, "#f6c0c8"), (1, "#c87a92")]), stroke=INK, width=1.1)
        for k in range(1, 9):
            a = math.radians(180 * k / 9)
            s.line(cx, h + 7, cx + math.cos(a) * w * 0.46, sy + math.sin(a) * (h + 6 - sy) * 0.2, "#b8708a", 0.8, 0.7)
        lobes = [(0.24, 0.42, 0.2), (0.42, 0.26, 0.24), (0.6, 0.27, 0.23), (0.77, 0.43, 0.19)]
        sponge = s.radial(cx - w * 0.12, h * 0.08, w * 0.62, [(0, "#fff8b8"), (0.45, "#ffd84a"), (1, "#d88a14")])
        s.path(blob(cx, sy - h * 0.12, w * 0.44, h * 0.42, 0.05, seed=3), fill=sponge, stroke=INK, width=1.1)
        for px, py, pr in lobes:
            s.path(blob(w * px, h * py + 1.2, w * pr, h * 0.34, 0.06, seed=px * 10), fill=sponge, stroke=INK, width=1.0)
        s.path(blob(cx, sy - h * 0.1, w * 0.4, h * 0.36, 0.05, seed=3), fill=sponge)
        for px, py, pr in ((0.3, 0.42, 1.5), (0.47, 0.3, 1.8), (0.64, 0.36, 1.6), (0.38, 0.6, 1.2), (0.56, 0.58, 1.3), (0.74, 0.55, 1.1),
                           (0.22, 0.6, 1.0), (0.5, 0.45, 1.0)):
            s.ellipse(w * px, h * py, pr * 1.15, pr, fill="#b86a0a", opacity=0.7)
            s.path(f"M{w * px - pr:.2f} {h * py + pr * 0.4:.2f} Q{w * px:.2f} {h * py + pr * 1.3:.2f} {w * px + pr:.2f} {h * py + pr * 0.4:.2f}",
                   stroke="#fff4b0", width=0.5, opacity=0.8)
        s.path(f"M{w * 0.2:.1f} {h * 0.36:.1f} Q{w * 0.3:.1f} {h * 0.06:.1f} {w * 0.5:.1f} {h * 0.04:.1f}", stroke="#ffffff", width=1.4, opacity=0.85)
        s.path(f"M{cx - w * 0.47:.1f} {sy + 0.5:.1f} Q{cx:.1f} {sy + 4:.1f} {cx + w * 0.47:.1f} {sy + 0.5:.1f}", stroke="#fffaf6", width=1.2, opacity=0.9)

    def _rope_belt(self, s: Svg, w: float, h: float) -> None:
        """Wet rope belt over wooden rollers (conveyor)."""
        s.path(rounded_rect_path(0.6, 0.6, w - 1.2, h - 1.2, h / 2), fill=s.linear(0, 0, 0, h, [(0, "#e2c890"), (0.5, "#b4904e"), (1, "#7a5a30")]),
               stroke=INK, width=1.2)
        k = 0
        x = h * 0.4
        while x < w - h * 0.3:
            s.path(f"M{x:.1f} 1.2 Q{x + 2.4:.1f} {h * 0.5:.1f} {x - 1:.1f} {h - 1.2:.1f}", stroke="#6a4a24", width=1.3, opacity=0.8)
            s.path(f"M{x + 1.2:.1f} 1.6 Q{x + 3.4:.1f} {h * 0.5:.1f} {x + 0.2:.1f} {h - 1.6:.1f}", stroke="#fff0c8", width=0.6, opacity=0.6)
            x += 3.6
            k += 1
        for cx in (h / 2, w - h / 2):
            s.circle(cx, h / 2, h * 0.3, fill=s.radial(cx - 1, h / 2 - 1, h * 0.32, [(0, "#c49a6a"), (1, "#5a3e26")]), stroke=INK, width=0.8)
            s.circle(cx, h / 2, h * 0.1, fill=BRASS)
        s.line(h / 2, 2.0, w - h / 2, 2.0, "#ffffff", 1.1, 0.75)
        for x in range(int(h), int(w - h), 22):
            s.ellipse(x + 6, h - 2.2, 3, 0.9, fill="#ffffff", opacity=0.4)

    def pipe(self, w: float, h: float, warp: bool) -> Svg:
        """Verdigris copper sea pipe with a porthole; a warp pipe's porthole glows."""
        s = Svg(w, h)
        r = Rand(int(w * 7 + h))
        body = s.linear(4, 0, w - 4, 0, [(0, PATINA_DEEP), (0.14, PATINA_DARK), (0.3, PATINA_HI), (0.42, PATINA), (0.75, PATINA_DARK), (1, PATINA_DEEP)])
        s.path(rounded_rect_path(4, 10, w - 8, h - 10, 2), fill=body, stroke=INK, width=1.3)
        for _ in range(int(h / 18) + 1):  # copper rubbed bright through the patina
            fx, fy = r.uniform(8, w - 22), r.uniform(18, max(19.0, h - 10))
            ln = r.uniform(6, 14)
            s.path(f"M{fx:.1f} {fy:.1f} Q{fx + ln / 2:.1f} {fy - 1.2:.1f} {fx + ln:.1f} {fy + 0.4:.1f}", stroke=COPPER, width=1.6, opacity=0.5)
            s.path(f"M{fx + 1:.1f} {fy - 0.5:.1f} Q{fx + ln / 2:.1f} {fy - 1.6:.1f} {fx + ln - 2:.1f} {fy:.1f}", stroke=COPPER_HI, width=0.6, opacity=0.6)
        for _ in range(4):
            sx = r.uniform(7, w - 7)
            s.line(sx, 15, sx + r.uniform(-1, 1), min(h - 3, 15 + r.uniform(8, 22)), PATINA_HI, r.uniform(0.8, 1.6), 0.35)
        if h > 30:
            s.rect(4.5, h - 8.5, w - 9, 4, fill=s.linear(0, h - 8.5, 0, h - 4.5, [(0, COPPER_HI), (1, COPPER_DARK)]), stroke=INK, width=0.8)
            for bx in range(9, int(w) - 6, 9):
                s.circle(bx, h - 6.5, 0.9, fill="#ffe0c0")
        if h > 26:
            cy = (14 + h - (9 if h > 30 else 0)) / 2 + 1
            pr = max(3.0, min(7.0, (h - (9 if h > 30 else 0) - 14) / 2 - 2.5))
            if warp:
                s.circle(w / 2, cy, pr + 7, fill=s.radial(w / 2, cy, pr + 7, [(0, "#d8fff6", 0.9), (0.55, "#73ffe1", 0.55), (1, "#73ffe1", 0)]))
            s.circle(w / 2, cy, pr + 1.8, fill=s.linear(0, cy - pr, 0, cy + pr, [(0, BRASS_HI), (1, BRASS_DARK)]), stroke=INK, width=0.9)
            glass = [(0, "#e8fffb"), (0.5, "#8af0dc"), (1, "#2fb8a6")] if warp else [(0, "#bfe8f0"), (0.55, "#3a8aa8"), (1, "#1a3a5a")]
            s.circle(w / 2, cy, pr, fill=s.radial(w / 2 - pr * 0.3, cy - pr * 0.3, pr * 1.3, glass), stroke="#3a2a12", width=0.6)
            s.path(f"M{w / 2 - pr * 0.6:.2f} {cy - pr * 0.1:.2f} Q{w / 2 - pr * 0.5:.2f} {cy - pr * 0.6:.2f} {w / 2:.2f} {cy - pr * 0.65:.2f}",
                   stroke="#ffffff", width=0.9, opacity=0.85)
            for a in range(0, 360, 60):
                s.circle(w / 2 + math.cos(math.radians(a)) * (pr + 0.9), cy + math.sin(math.radians(a)) * (pr + 0.9), 0.5, fill="#5a3e12")
            if warp:
                s.circle(w / 2, cy, pr + 3.4, stroke="#b8fff0", width=1.6, opacity=0.95)
                s.polygon([(w / 2 - pr * 0.55, cy - pr * 0.25), (w / 2 + pr * 0.55, cy - pr * 0.25), (w / 2, cy + pr * 0.5)], fill="#ffffff", opacity=0.9)
        rim = s.linear(0.8, 0, w - 0.8, 0, [(0, COPPER_DARK), (0.18, "#d8895a"), (0.32, COPPER_HI), (0.5, COPPER), (0.8, "#8a4a2a"), (1, "#4a2414")])
        s.path(rounded_rect_path(0.8, 0.8, w - 1.6, 14, 4), fill=rim, stroke=INK, width=1.3)
        s.line(3, 2.6, w - 3, 2.6, "#ffe4c8", 1.0, 0.7)
        for bx in [5.5 + i * (w - 11) / 4 for i in range(5)]:
            s.circle(bx, 8.2, 1.25, fill=s.radial(bx - 0.4, 7.8, 1.6, [(0, "#fff0dc"), (1, COPPER_DARK)]), stroke=INK, width=0.4)
        for k in range(int(w / 9)):
            dx = 4 + k * 9 + 3 * _hash(k, 7)
            ln = 1.6 + 3.4 * _hash(k, 8)
            s.path(f"M{dx - 1.6:.1f} 13.6 Q{dx:.1f} {13.6 + ln * 1.4:.1f} {dx + 1.6:.1f} 13.6 Z", fill=PATINA, stroke=PATINA_DEEP, width=0.4, opacity=0.9)
        if warp:
            s.rect(1.5, 0.6, w - 3, 3, fill="#b8fff0", opacity=0.55, rx=1.5)
        return s

    def gate(self, w: float, h: float) -> Svg:
        """Arena gate: barnacled copper bars in a brass-banded frame."""
        s = Svg(w, h)
        s.rect(0, 0, w, h, fill=s.linear(0, 0, 0, h, [(0, "#14262a"), (1, "#0a1416")]), rx=2)
        n = max(2, int(w // 9) + 1)
        for i in range(n):
            x = 2 + i * (w - 4) / max(1, n - 1) - 1.7
            s.rect(x, 0, 3.4, h - 4, fill=s.linear(x, 0, x + 3.4, 0, [(0, PATINA_HI), (0.5, PATINA), (1, PATINA_DEEP)]), rx=1)
            s.polygon([(x - 0.8, h - 6), (x + 1.7, h), (x + 4.2, h - 6)], fill=COPPER, stroke=INK, width=0.5)
            for j in range(2):
                yy = h * (0.35 + 0.4 * _hash(i * 3 + j, 2))
                _barnacle(s, x + 1.7, yy, 1.1)
        for y in (h * 0.2, h * 0.62):
            s.rect(0, y, w, 4.5, fill=s.linear(0, y, 0, y + 4.5, [(0, BRASS_HI), (1, BRASS_DARK)]), stroke=INK, width=0.8, rx=1.5)
        for k in range(3):
            sx = w * (0.2 + 0.3 * k)
            pts = [(sx + 2.4 * math.sin(j * 1.3 + k), h * 0.2 + 4.5 + j * 5) for j in range(4)]
            s.path(smooth_open(pts), stroke="#3f8a5a", width=1.8, opacity=0.85)
        return s

    def hazard(self, kind: str, w: float, h: float):
        if kind != "thorns":
            return None
        # a row of sea urchins on a rock strip
        hh = max(h, 16.0)
        s = Svg(w, hh + 4)
        s.path(rounded_rect_path(0.5, hh - 5, w - 1, 7, 3), fill=s.linear(0, hh - 5, 0, hh + 2, [(0, "#8a7a86"), (1, "#4a3e4a")]), stroke=INK, width=0.8)
        n = max(1, round(w / 13))
        for i in range(n):
            cx = (i + 0.5) * w / n
            cy = hh - 6.5
            for k in range(13):
                a = math.radians(-180 + k * 15)
                ln = 8.5 if k % 2 == 0 else 6.0
                s.line(cx + math.cos(a) * 3, cy + math.sin(a) * 3, cx + math.cos(a) * ln, cy + math.sin(a) * ln, "#2a1a36", 1.3)
                s.line(cx + math.cos(a) * 3, cy + math.sin(a) * 3, cx + math.cos(a) * (ln - 1), cy + math.sin(a) * (ln - 1), "#9a6ad6", 0.5, 0.9)
            s.circle(cx, cy, 4.2, fill=s.radial(cx - 1.4, cy - 1.6, 5, [(0, "#b48ae8"), (0.6, "#5a2e78"), (1, "#2a1238")]), stroke=INK, width=0.7)
        return s

    # ------------------------------------------------------------------ props
    def _palm(self, seed: int, hgt: float, lean: float, fronds: int = 10) -> Svg:
        """Coconut palm: a slim ringed trunk curving toward the sea, a lush crown of
        long drooping fronds and a cluster of coconuts."""
        r = Rand(seed)
        W, H, bx, by = self._palm_frame(hgt, lean)
        s = Svg(W, H)
        tx, ty = bx + lean, by - hgt * 0.74
        ctrl = (bx + lean * 0.05, by - hgt * 0.42)

        def trunk(t: float) -> Pt:
            return ((1 - t) ** 2 * bx + 2 * (1 - t) * t * ctrl[0] + t * t * tx, (1 - t) ** 2 * by + 2 * (1 - t) * t * ctrl[1] + t * t * ty)

        n = 18
        left, right = [], []
        for i in range(n + 1):
            t = i / n
            px, py = trunk(t)
            qx, qy = trunk(min(1.0, t + 0.02))
            ox, oy = trunk(max(0.0, t - 0.02))
            dx, dy = qx - ox, qy - oy
            ln = math.hypot(dx, dy) or 1.0
            wd = hgt * (0.042 - 0.016 * t) * (1.25 if t < 0.06 else 1.0)
            left.append((px + dy / ln * wd, py - dx / ln * wd))
            right.append((px - dy / ln * wd, py + dx / ln * wd))
        back = (LEAF_DARK, "#3f8a4a", LEAF_LINE)
        front = ("#4f9e4c", LEAF_HI, LEAF_LINE)
        angles = sorted([-168 + 152 * k / (fronds - 1) + r.uniform(-6, 6) for k in range(fronds)])
        for k, ang in enumerate(angles[::2]):
            _frond(s, tx, ty, ang - 8, hgt * r.uniform(0.44, 0.52), 0.62 if abs(math.cos(math.radians(ang))) > 0.4 else 0.3, hgt * 0.13, back, 14)
        s.path(_poly(left + list(reversed(right))), fill=s.linear(bx - hgt * 0.05, 0, bx + hgt * 0.05, 0, [(0, "#e2c696"), (0.45, "#b08a5c"), (1, "#6e4e34")]),
               stroke=INK, width=1.2)
        for i in range(1, n):
            (lx, ly), (rx, ry) = left[i], right[i]
            s.path(f"M{lx:.2f} {ly:.2f} Q{(lx + rx) / 2:.2f} {(ly + ry) / 2 + 2.2:.2f} {rx:.2f} {ry:.2f}", stroke="#5a3e28", width=0.9, opacity=0.7)
            s.path(f"M{lx:.2f} {ly - 1.2:.2f} Q{(lx + rx) / 2:.2f} {(ly + ry) / 2 + 1.0:.2f} {rx:.2f} {ry - 1.2:.2f}", stroke="#f2dcae", width=0.6, opacity=0.5)
        s.path(blob(bx, by - 1, hgt * 0.07, hgt * 0.02, 0.2, seed=seed), fill="#6e4e34", stroke=INK, width=0.9)
        for k, (cx, cy) in enumerate(((tx - 5, ty + 5), (tx + 4, ty + 6), (tx - 0.5, ty + 10), (tx + 8, ty + 1))):
            rr = 4.4 - (k == 3) * 0.6
            tone = "#8aa04a" if k % 2 else "#7a5a32"
            s.circle(cx, cy, rr, fill=s.radial(cx - 1.4, cy - 1.4, rr * 1.4, [(0, shade(tone, 0.4)), (1, shade(tone, -0.3))]), stroke=INK, width=0.8)
        for k, ang in enumerate(angles[1::2]):
            _frond(s, tx, ty, ang, hgt * r.uniform(0.42, 0.5), 0.58 if abs(math.cos(math.radians(ang))) > 0.4 else 0.28, hgt * 0.13, front, 15)
        s.path(blob(tx, ty - 1, hgt * 0.04, hgt * 0.03, 0.1, seed=seed + 2), fill="#6a8a3a", stroke=LEAF_LINE, width=0.8)
        return s

    @staticmethod
    def _palm_frame(hgt: float, lean: float) -> tuple[float, float, float, float]:
        """Canvas (w, h) and trunk base (x, y) of a palm prop: room for the whole crown."""
        W = hgt * 1.3 + abs(lean) * 1.4
        H = hgt * 1.3
        return W, H, W / 2 - lean, H - 2

    def _palm_pivot(self, hgt: float, lean: float) -> tuple[float, float]:
        _w, _h, bx, by = self._palm_frame(hgt, lean)
        return bx, by + 1

    def _seagrape(self, seed: int) -> Svg:
        """Sea-grape bush: round leathery leaves with red veins and grape clusters."""
        r = Rand(seed)
        s = Svg(100, 64)
        for _ in range(4):
            ex, ey = r.uniform(26, 74), r.uniform(26, 44)
            s.path(f"M50 63 Q{(50 + ex) / 2:.1f} {ey + 16:.1f} {ex:.1f} {ey:.1f}", stroke="#7a4a32", width=2.2)
        _seagrape_clump(s, 50, 60, 46, r, line=LEAF_LINE)
        for _ in range(3):
            gx, gy = r.uniform(28, 72), r.uniform(34, 50)
            for k in range(5):
                s.circle(gx + (k % 2) * 2.4 - 1.2, gy + k * 2.0, 1.5, fill="#8a4a9a" if k % 3 else "#6aa04a", stroke="#3a1a3a", width=0.4)
        return s

    def _dune_grass(self, seed: int) -> Svg:
        r = Rand(seed)
        s = Svg(60, 46)
        s.path(blob(30, 45, 22, 3.5, 0.15, seed=seed, squash_top=1.3), fill=s.linear(0, 41, 0, 47, [(0, SAND_TOP), (1, SAND)]))
        for _ in range(14):
            bx = r.uniform(16, 44)
            lean = r.uniform(-12, 12)
            bh = r.uniform(18, 36)
            tone = r.choice(["#8fbc62", "#a8c86a", "#6a9a4e", "#c8c878"])
            s.path(f"M{bx - 1.4:.1f} 45 Q{bx + lean * 0.3:.1f} {45 - bh * 0.6:.1f} {bx + lean:.1f} {45 - bh:.1f} Q{bx + lean * 0.3 + 0.9:.1f} "
                   f"{45 - bh * 0.5:.1f} {bx + 1.4:.1f} 45 Z", fill=tone, stroke="#3a5a2a", width=0.5)
        for _ in range(2):
            hx = r.uniform(24, 38)
            tip = (hx + r.uniform(-6, 8), r.uniform(2, 8))
            s.path(f"M{hx:.1f} 45 Q{hx + 1:.1f} 24 {tip[0]:.1f} {tip[1]:.1f}", stroke="#b4a466", width=0.9)
            for k in range(5):
                s.ellipse(tip[0] + 1.6 + (k % 2) * 0.8, tip[1] + 1.8 + k * 2.6, 1.2, 2.1, fill="#e6d29a", stroke="#9a8448", width=0.4)
        return s

    def _shells(self, seed: int) -> Svg:
        s = Svg(58, 26)
        s.path(blob(29, 25, 26, 4, 0.15, seed=seed, squash_top=1.3), fill=s.linear(0, 21, 0, 27, [(0, SAND_TOP), (1, SAND)]))
        if seed % 2:
            _scallop(s, 19, 23, 9, "#f7b49a", tilt=-8, width=0.8)
            _conch(s, 40, 24, 6.5, "#f4d6b8", width=0.8)
            s.ellipse(52, 22.5, 3.2, 2.2, fill=s.radial(51, 21.5, 3.5, [(0, "#fff4e8"), (1, "#c8a088")]), stroke=INK, width=0.6)
        else:
            _conch(s, 22, 24, 8, "#f2c8a8", flip=True, width=0.8)
            _scallop(s, 42, 23.5, 7, "#fbe0d0", tilt=10, width=0.8)
            s.ellipse(8, 22.6, 3.6, 2.4, fill="#8a8a96", stroke=INK, width=0.6)
        return s

    def _starfish_prop(self, seed: int) -> Svg:
        s = Svg(52, 22)
        s.path(blob(26, 21, 24, 3.6, 0.15, seed=seed, squash_top=1.3), fill=s.linear(0, 17, 0, 23, [(0, SAND_TOP), (1, SAND)]))
        _starfish(s, 18, 14.5, 8.5, CORAL_ORANGE, angle=12, width=0.8)
        _starfish(s, 37, 17, 5.5, "#e2584a", angle=-20, width=0.7)
        return s

    def _rock(self, seed: int) -> Svg:
        """Coastal boulder: wet dark foot, barnacles and a fringe of algae."""
        r = Rand(seed)
        s = Svg(66, 42)
        d = blob(33, 28, 30, 14.5, 0.12, seed=seed, squash_top=1.2)
        s.path(d, fill=s.radial(22, 16, 42, [(0, ROCK_HI), (0.5, ROCK), (1, ROCK_DARK)]), stroke=INK, width=1.3)
        s.path(f"M6 33 Q33 44 60 33 L60 38 Q33 46 6 38 Z", fill="#3a3038", opacity=0.3)
        s.path(smooth_open([(14, 30), (26, 25), (34, 31)]), stroke="#5a4c46", width=1.1, opacity=0.7)
        for _ in range(5):
            _barnacle(s, r.uniform(14, 52), r.uniform(26, 36), r.uniform(1.0, 1.8))
        for k in range(6):
            ax = 10 + k * 9 + r.uniform(-2, 2)
            s.path(f"M{ax:.1f} 37 Q{ax + 1.5:.1f} {41 + r.uniform(0, 2):.1f} {ax - 1:.1f} 42", stroke="#4f9a5a", width=2.0, opacity=0.85)
        s.ellipse(24, 18, 6, 2.2, fill="#ffffff", opacity=0.35)
        return s

    def _tide_pool(self, seed: int) -> Svg:
        """Rock basin holding a little pool with an anemone and a starfish."""
        r = Rand(seed)
        s = Svg(124, 46)
        for cx, cy, rx, ry in ((22, 28, 20, 12), (100, 27, 22, 13)):
            s.path(blob(cx, cy, rx, ry, 0.12, seed=cx + seed), fill=s.radial(cx - rx * 0.3, cy - ry * 0.5, rx * 1.4, [(0, "#b8a8a0"), (1, "#6a5a5e")]),
                   stroke=INK, width=1.1)
        s.ellipse(62, 26, 44, 8, fill=s.linear(0, 18, 0, 34, [(0, "#bff6f2"), (0.5, "#4fc8cc"), (1, "#2a8aa8")]), stroke="#2a5a6a", width=1.0)
        for k in range(8):
            a = math.radians(-160 + k * 20)
            ex, ey = 70 + math.cos(a) * 9, 22 + math.sin(a) * 7
            s.path(f"M70 26 Q{70 + math.cos(a) * 5 + 1:.1f} {22 + math.sin(a) * 3:.1f} {ex:.1f} {ey:.1f}", stroke="#ff8ab0", width=1.6)
            s.circle(ex, ey, 1.0, fill="#ffd0e0")
        s.path("M44 26 Q46 16 43 9 M48 26 Q51 18 50 12", stroke="#4f9a5a", width=1.8)
        s.path(_line([(24, 24.5), (52, 22.5), (60, 23)]), stroke="#ffffff", width=1.2, opacity=0.85)
        front = [(8, 44), (14, 32), (34, 33), (50, 35), (74, 35), (92, 33), (112, 32), (118, 44)]
        s.path(smooth_closed(front, 0.5), fill=s.linear(0, 30, 0, 46, [(0, "#a89488"), (1, "#5e4e52")]), stroke=INK, width=1.2)
        s.path(smooth_open(front[1:-1], 0.5), stroke="#d8c8bc", width=1.0, opacity=0.6)
        _starfish(s, 86, 33, 5.5, CORAL_ORANGE, angle=r.uniform(0, 60), width=0.7)
        for _ in range(4):
            _barnacle(s, r.uniform(16, 60), r.uniform(37, 42), 1.2)
        return s

    def _driftwood(self, seed: int) -> Svg:
        """Bleached driftwood log with a broken branch, half buried in sand."""
        r = Rand(seed)
        s = Svg(116, 40)
        s.path("M66 24 Q70 12 80 4 L83 6 Q76 14 73 25 Z", fill=s.linear(66, 0, 83, 0, [(0, DRIFT_HI), (1, DRIFT_DARK)]), stroke=INK, width=1.0)
        log = "M6 30 Q4 20 14 18 Q50 14 96 16 Q110 17 110 26 Q110 34 96 34 Q50 36 14 35 Q6 35 6 30 Z"
        s.path(log, fill=s.linear(0, 16, 0, 36, [(0, DRIFT_HI), (0.55, DRIFT), (1, DRIFT_DARK)]), stroke=INK, width=1.2)
        for k in range(5):
            y = 20 + k * 3
            s.path(f"M{16 + k * 4:.1f} {y:.1f} Q{55:.1f} {y - 2 + k * 0.4:.1f} {98 - k * 3:.1f} {y + 1:.1f}", stroke="#8a7c6a", width=0.7, opacity=0.6)
        s.ellipse(104, 25, 4.5, 7, fill=s.radial(104, 25, 6, [(0, "#f4ead6"), (1, "#a89a84")]), stroke=INK, width=0.9)
        s.ellipse(104, 25, 2, 3.4, stroke="#8a7c6a", width=0.6)
        s.ellipse(40, 24, 3, 1.6, fill="#5a4c40")
        s.path(blob(58, 37, 54, 4, 0.12, seed=seed, squash_top=1.3), fill=s.linear(0, 33, 0, 40, [(0, SAND_TOP), (1, SAND)]))
        for _ in range(2):
            px = r.uniform(20, 90)
            _scallop(s, px, 37, 2.4, "#fbe0d0", width=0.4)
        return s

    def _buoy(self, seed: int) -> Svg:
        """Old fishing float with a coil of rope, washed up by the tide."""
        s = Svg(56, 44)
        s.path(blob(28, 42, 26, 3.6, 0.15, seed=seed, squash_top=1.3), fill=s.linear(0, 38, 0, 45, [(0, SAND_TOP), (1, SAND)]))
        for k in range(3):
            s.ellipse(40, 39 - k * 3, 12 - k * 2, 3.2, stroke=INK, width=2.4)
            s.ellipse(40, 39 - k * 3, 12 - k * 2, 3.2, stroke="#e8d0a0", width=1.3)
        s.circle(20, 26, 13, fill=s.radial(15, 20, 16, [(0, "#ffb0a0"), (0.55, "#e8483c"), (1, "#8a2420")]), stroke=INK, width=1.3)
        s.path("M7.4 25 Q20 30 32.6 25 L32.6 29 Q20 34 7.6 29 Z", fill="#ffffff", stroke=INK, width=0.7)
        s.rect(17.5, 10, 5, 4, fill="#6a6a72", stroke=INK, width=0.8, rx=1)
        s.path("M20 10 Q30 2 36 14 Q40 24 40 33", stroke="#e8d0a0", width=1.2)
        s.ellipse(14, 19, 3.4, 2.2, fill="#ffffff", opacity=0.55)
        return s

    def _buoy_marker(self) -> Svg:
        """Striped channel buoy tilted on the sand, its little flag still up."""
        s = Svg(46, 64)
        s.path(blob(23, 62, 21, 3.4, 0.15, seed=3, squash_top=1.3), fill=s.linear(0, 58, 0, 64, [(0, SAND_TOP), (1, SAND)]))
        with s.group(transform="rotate(-12 23 60)"):
            s.path("M12 60 L14 30 L32 30 L34 60 Z", fill=s.linear(12, 0, 34, 0, [(0, "#ff9a8a"), (0.5, "#e0483c"), (1, "#8a2420")]), stroke=INK, width=1.2)
            s.path("M13.2 46 L32.8 46 L33.4 53 L12.6 53 Z", fill="#f6f2ea", stroke=INK, width=0.6)
            s.path("M14 30 L23 16 L32 30 Z", fill=s.linear(14, 0, 32, 0, [(0, "#f6f2ea"), (1, "#a8a29a")]), stroke=INK, width=1.1)
            s.line(23, 16, 23, 4, "#3a3440", 1.3)
            s.polygon([(23, 4), (33, 7), (23, 10)], fill=TURQUOISE, stroke=INK, width=0.6)
            s.rect(10, 58, 26, 4, fill="#5a5a66", stroke=INK, width=0.8, rx=1)
        s.path("M10 61 Q4 56 6 50", stroke="#4f9a5a", width=1.8)
        return s

    def _kelp_prop(self, seed: int) -> Svg:
        """A clump of giant kelp anchored on a rock (sways like the bushes)."""
        r = Rand(seed)
        s = Svg(90, 170)
        for k, (dx, hgt, size) in enumerate(((-14.0, 120.0, 1.05), (10.0, 150.0, 1.25), (24.0, 96.0, 0.95))):
            tone = ("#5a7a3a", "#7c9c44", "#b0c04c") if k != 1 else ("#4f6e34", "#6e9040", "#a4b848")
            self._kelp(s, 45 + dx, 162, hgt + r.uniform(-8, 8), seed * 7 + k, tone[0], tone[1], tone[2], sway=0.8, size=size)
        s.path(blob(45, 163, 30, 8, 0.15, seed=seed, squash_top=1.1), fill=s.radial(38, 157, 32, [(0, "#b8a8b0"), (1, "#5e4e5a")]), stroke=INK,
               width=1.1)
        for j in range(3):
            _barnacle(s, 30 + j * 12 + r.uniform(-2, 2), 158 + (j % 2), 1.3)
        return s

    def _coral_fan_prop(self, seed: int, tone: str) -> Svg:
        """Sea fan washed up against a rock."""
        s = Svg(72, 74)
        s.path(blob(36, 70, 20, 7, 0.15, seed=seed, squash_top=1.1), fill=s.radial(30, 64, 22, [(0, "#b8a8a0"), (1, "#6a5a5e")]), stroke=INK, width=1.1)
        self._fan(s, 36, 66, 34, tone, seed, line=INK)
        return s

    def props(self) -> dict[str, PropSpec]:
        return {
            "tree_palm": PropSpec(lambda: self._palm(4, 200, 24), self._palm_pivot(200, 24)),
            "tree_palm_b": PropSpec(lambda: self._palm(11, 168, -20, 9), self._palm_pivot(168, -20)),
            "tree_palm_small": PropSpec(lambda: self._palm(17, 118, 12, 8), self._palm_pivot(118, 12)),
            "bush_seagrape": PropSpec(lambda: self._seagrape(5), (50, 60)),
            "bush_seagrape_b": PropSpec(lambda: self._seagrape(14), (50, 60)),
            "dune_grass": PropSpec(lambda: self._dune_grass(3), (30, 45)),
            "dune_grass_b": PropSpec(lambda: self._dune_grass(8), (30, 45)),
            "shells": PropSpec(lambda: self._shells(1), (29, 25)),
            "shells_b": PropSpec(lambda: self._shells(2), (29, 25)),
            "starfish": PropSpec(lambda: self._starfish_prop(3), (26, 21)),
            "rock": PropSpec(lambda: self._rock(2), (33, 40)),
            "rock_b": PropSpec(lambda: self._rock(9), (33, 40)),
            "tide_pool": PropSpec(lambda: self._tide_pool(4), (62, 44)),
            "driftwood": PropSpec(lambda: self._driftwood(6), (58, 38)),
            "buoy": PropSpec(lambda: self._buoy(2), (28, 42)),
            "buoy_marker": PropSpec(self._buoy_marker, (23, 62)),
            "coral_fan": PropSpec(lambda: self._coral_fan_prop(5, "#b45ac8"), (36, 72)),
            "coral_fan_b": PropSpec(lambda: self._coral_fan_prop(12, "#f08a4a"), (36, 72)),
            "bush_kelp": PropSpec(lambda: self._kelp_prop(3), (45, 168)),
            "bush_kelp_b": PropSpec(lambda: self._kelp_prop(8), (45, 168)),
        }

    def auto_decor(self, rng, surface_w: float) -> list[tuple[str, float, float, str]]:
        """Natural shore decor only (no umbrellas or other beach furniture); levels
        whose art variant is a sea floor (``SEA_VARIANTS``) get kelp and corals."""
        out = []
        x = rng.uniform(40, 120)
        if self.variant in SEA_VARIANTS:
            while x < surface_w - 40:
                roll = rng.next()
                if roll < 0.3:
                    out.append((rng.choice(["bush_kelp", "bush_kelp_b"]), x, rng.uniform(0.8, 1.05), "back"))
                elif roll < 0.52:
                    out.append((rng.choice(["coral_fan", "coral_fan_b"]), x, rng.uniform(0.75, 1.0), "back"))
                elif roll < 0.68:
                    out.append((rng.choice(["rock", "rock_b"]), x, rng.uniform(0.65, 0.9), "mid"))
                elif roll < 0.84:
                    out.append((rng.choice(["shells", "shells_b", "starfish"]), x, rng.uniform(0.75, 1.0), "mid"))
                x += rng.uniform(90, 190)
            return out
        while x < surface_w - 40:
            roll = rng.next()
            if roll < 0.18 and surface_w > 260:
                out.append((rng.choice(["tree_palm", "tree_palm_b", "tree_palm_small"]), x, rng.uniform(0.86, 1.05), "back"))
            elif roll < 0.32:
                out.append((rng.choice(["bush_seagrape", "bush_seagrape_b"]), x, rng.uniform(0.75, 1.0), "back"))
            elif roll < 0.45:
                out.append((rng.choice(["dune_grass", "dune_grass_b"]), x, rng.uniform(0.75, 1.0), "mid"))
            elif roll < 0.58:
                out.append((rng.choice(["shells", "shells_b", "starfish"]), x, rng.uniform(0.75, 1.0), "mid"))
            elif roll < 0.67:
                out.append((rng.choice(["rock", "rock_b"]), x, rng.uniform(0.65, 0.9), "mid"))
            elif roll < 0.74 and surface_w > 200:
                out.append(("tide_pool", x, rng.uniform(0.8, 1.0), "mid"))
            elif roll < 0.81:
                out.append(("driftwood", x, rng.uniform(0.75, 0.95), "back"))
            elif roll < 0.87:
                out.append((rng.choice(["buoy", "buoy_marker"]), x, rng.uniform(0.8, 1.0), "back"))
            elif roll < 0.94:
                out.append((rng.choice(["coral_fan", "coral_fan_b"]), x, rng.uniform(0.7, 0.9), "back"))
            x += rng.uniform(100, 210)
        return out

    def weather(self) -> Weather:
        return Weather("bubbles", 0.28, ("soft", "soft", "sparkle"), wind=24.0)


ART_CLASS = CoralCoast
