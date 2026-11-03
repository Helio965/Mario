"""Reino Verde: sunny meadows, canals, windmill hills and orchards.

Identity: warm sunlight from the upper right, layered blue-green hills with
windmills, round orchard trees, scalloped grass lips over striped soil with
pebbles and roots, wildflowers, drifting leaves and petals.
"""

from __future__ import annotations

import math

from ..svg import Rand, Svg, blob, mix, rounded_rect_path, shade, smooth_closed, smooth_open, star_points
from .base import Layer, PropSpec, Weather, WorldArt

INK = "#2b1d2c"
GRASS_TOP, GRASS, GRASS_DARK, GRASS_LIGHT = "#9fe064", "#5fbf47", "#3a8a36", "#d2f59a"
SOIL_TOP, SOIL, SOIL_DEEP = "#c48a50", "#99613a", "#5e3b24"


PALETTE = {
    "grass_top": GRASS_TOP, "grass": GRASS, "grass_dark": GRASS_DARK, "grass_light": GRASS_LIGHT,
    "soil_top": SOIL_TOP, "soil": SOIL, "soil_deep": SOIL_DEEP,
    "sky": ("#4aa6e8", "#8fd2f4", "#dff4f4", "#f2f8e2"), "sun": "#fff6c8",
    "mountain": ("#a9c9e0", "#c9e2ea"), "far_hill": ("#9ccbb4", "#b4dcc4"),
    "mid_hill": ("#8ed07a", "#6cbb66", "#5aa964"), "foliage": ("#9ad97a", "#5aa95a", "#3f8a4e"),
    "near": ("#6fbf62", "#3e8f4b", "#2f7442"), "flowers": ("#fff3c4", "#ffd1e3", "#ffe27a"),
}


class GreenKingdom(WorldArt):
    id = "green_kingdom"
    name = "Reino Verde"
    accent = "#35c9b4"
    terrain_headroom = 12.0
    provisional = False

    def __init__(self) -> None:
        self.c = dict(PALETTE)

    # ------------------------------------------------------------------ sky
    def sky(self) -> Svg:
        s = Svg(960, 540)
        c0, c1, c2, c3 = self.c["sky"]
        s.rect(0, 0, 960, 540, fill=s.linear(0, 0, 0, 540, [(0, c0), (0.45, c1), (0.78, c2), (1, c3)]))
        sun = self.c["sun"]
        s.circle(790, 96, 260, fill=s.radial(790, 96, 260, [(0, sun, 0.75), (0.35, sun, 0.3), (1, sun, 0)]))
        for k in range(9):
            a = math.radians(100 + k * 9)
            s.polygon([(790, 96), (790 + math.cos(a - 0.03) * 700, 96 + math.sin(a - 0.03) * 700),
                       (790 + math.cos(a + 0.03) * 700, 96 + math.sin(a + 0.03) * 700)], fill="#fffbe0", opacity=0.07)
        s.circle(790, 96, 38, fill=s.radial(780, 86, 40, [(0, "#ffffff"), (0.5, "#fff6c8"), (1, "#ffe08a")]))
        return s

    def _cloud(self, seed: int, w: float, h: float) -> Svg:
        r = Rand(seed)
        s = Svg(w, h)
        base = h * 0.78
        puffs = []
        n = 6
        for i in range(n):
            cx = w * (0.14 + 0.72 * i / (n - 1)) + r.uniform(-8, 8)
            rad = h * (0.24 + 0.22 * math.sin(math.pi * i / (n - 1))) + r.uniform(-3, 4)
            puffs.append((cx, base - rad * 0.6, rad))
        shadow = s.linear(0, h * 0.2, 0, base + 6, [(0, "#ffffff"), (0.65, "#eef5fb"), (1, "#c5d7e8")])
        for cx, cy, rad in puffs:
            s.circle(cx, cy + 4, rad, fill="#b8cde0", opacity=0.45)
        for cx, cy, rad in puffs:
            s.circle(cx, cy, rad, fill=shadow)
        s.path(f"M{w * 0.1:.1f} {base:.1f} Q{w * 0.5:.1f} {base + 9:.1f} {w * 0.9:.1f} {base:.1f} L{w * 0.9:.1f} {base - 8:.1f} L{w * 0.1:.1f} {base - 8:.1f} Z",
               fill="#dbe7f2")
        for cx, cy, rad in puffs[1:-1]:
            s.circle(cx - rad * 0.25, cy - rad * 0.35, rad * 0.45, fill="#ffffff", opacity=0.75)
        return s

    def sky_extras(self) -> dict[str, PropSpec]:
        return {
            f"gk.cloud.{i}": PropSpec((lambda i=i, w=w, h=h: self._cloud(31 + i * 7, w, h)), (0, 0))
            for i, (w, h) in enumerate([(240, 96), (180, 76), (300, 110)])
        }

    # ------------------------------------------------------------------ parallax layers
    def _far(self, seed: int) -> Svg:
        w, h = 1200.0, 300.0
        r = Rand(seed)
        s = Svg(w, h)
        # distant mountains (atmospheric blue) with soft snow caps
        pts = [(0, h)]
        x = 0.0
        while x <= w:
            pts.append((x, h * 0.18 + r.uniform(0, 60) + 40 * math.sin(x / w * 2 * math.pi)))
            x += r.uniform(110, 190)
        pts += [(w, h * 0.3), (w, h)]
        pts[1] = (0, h * 0.3)
        mountain = s.linear(0, 30, 0, h, [(0, self.c["mountain"][0]), (1, self.c["mountain"][1])])
        s.path(smooth_closed(pts, 0.5), fill=mountain)
        # hazy hills
        hill = [(0, h)]
        for i in range(13):
            hill.append((w * i / 12, h * 0.55 + 22 * math.sin(i * 1.3 + seed) + r.uniform(-8, 8)))
        hill[1] = (0, h * 0.6)
        hill += [(w, h * 0.6), (w, h)]
        s.path(smooth_closed(hill, 0.6), fill=s.linear(0, h * 0.45, 0, h, [(0, self.c["far_hill"][0]), (1, self.c["far_hill"][1])]))
        # windmills
        for k in range(2):
            mx = w * (0.25 + 0.5 * k) + r.uniform(-60, 60)
            my = h * 0.56 + 22 * math.sin((mx / w) * 12 * 1.3 / (2 * math.pi) + seed) - 6
            s.polygon([(mx - 7, my + 14), (mx - 4, my - 30), (mx + 4, my - 30), (mx + 7, my + 14)], fill="#8db0a8")
            for b in range(4):
                a = math.radians(20 + b * 90)
                s.polygon([(mx, my - 30), (mx + math.cos(a) * 30 - math.sin(a) * 3, my - 30 + math.sin(a) * 30 + math.cos(a) * 3),
                           (mx + math.cos(a) * 30 + math.sin(a) * 3, my - 30 + math.sin(a) * 30 - math.cos(a) * 3)], fill="#8db0a8")
        return s

    def _mid(self, seed: int) -> Svg:
        w, h = 1100.0, 280.0
        r = Rand(seed)
        s = Svg(w, h)
        hill = [(0, h)]
        for i in range(9):
            hill.append((w * i / 8, h * 0.42 + 34 * math.sin(i * 0.9 + seed * 0.7) + r.uniform(-10, 10)))
        hill[1] = (0, h * 0.45)
        hill += [(w, h * 0.45), (w, h)]
        m0, m1, m2 = self.c["mid_hill"]
        s.path(smooth_closed(hill, 0.65), fill=s.linear(0, h * 0.25, 0, h, [(0, m0), (0.5, m1), (1, m2)]))
        # path / hedge lines
        s.path(smooth_open([(0, h * 0.78), (w * 0.3, h * 0.72), (w * 0.6, h * 0.8), (w, h * 0.74)]), stroke="#e8e0b0", width=6, opacity=0.55)
        # orchard trees along the ridge
        for i in range(10):
            tx = r.uniform(20, w - 20)
            ty = h * 0.42 + 34 * math.sin((tx / w * 8) * 0.9 + seed * 0.7) + 16
            size = r.uniform(18, 30)
            s.rect(tx - 2.5, ty - 4, 5, 18, fill="#6a5a44")
            f0, f1, f2 = self.c["foliage"]
            s.path(blob(tx, ty - size * 0.8, size, size * 0.85, 0.08, seed=i + seed), fill=s.radial(tx - size * 0.3, ty - size * 1.2, size * 1.6,
                   [(0, f0), (0.6, f1), (1, f2)]))
        return s

    def _near(self, seed: int) -> Svg:
        w, h = 900.0, 150.0
        r = Rand(seed)
        s = Svg(w, h)
        x = -20.0
        while x < w + 20:
            rad = r.uniform(28, 52)
            cy = h - rad * 0.55
            n0, n1, n2 = self.c["near"]
            s.path(blob(x, cy, rad * 1.25, rad, 0.1, seed=x), fill=s.radial(x - rad * 0.4, cy - rad * 0.6, rad * 1.8,
                   [(0, n0), (0.7, n1), (1, n2)]))
            x += r.uniform(50, 95)
        s.rect(0, h - 18, w, 18, fill=self.c["near"][2])
        for i in range(26):
            fx, fy = r.uniform(0, w), h - r.uniform(14, 44)
            color = r.choice(list(self.c["flowers"]))
            s.circle(fx, fy, r.uniform(2.2, 3.6), fill=color, opacity=0.9)
        return s

    def layer_art(self) -> dict[str, PropSpec]:
        art = {}
        for i in range(2):
            art[f"gk.far.{i}"] = PropSpec((lambda i=i: self._far(11 + i * 5)), (0, 0))
            art[f"gk.mid.{i}"] = PropSpec((lambda i=i: self._mid(21 + i * 9)), (0, 0))
            art[f"gk.near.{i}"] = PropSpec((lambda i=i: self._near(41 + i * 3)), (0, 0))
        return art

    def layers(self) -> list[Layer]:
        return [
            Layer("far", 0.08, ["gk.far.0", "gk.far.1"], 1200, 70, vertical=0.05),
            Layer("mid", 0.26, ["gk.mid.0", "gk.mid.1"], 1100, 60, vertical=0.15),
            Layer("near", 0.5, ["gk.near.0", "gk.near.1"], 900, 40, vertical=0.35),
        ]

    # ------------------------------------------------------------------ terrain
    def terrain(self, style: str, w: float, h: float, seed: int, left: bool, right: bool, top: bool = True, x0: float = 0.0) -> Svg:
        """Terrain chunk art. Patterns that cross chunk borders (grass lip,
        strata) are functions of the world x (``x0`` + local x) so adjacent
        chunks join seamlessly."""
        if style == "cave":
            return self._cave(w, h, seed, left, right)
        hr = self.terrain_headroom
        s = Svg(w, h + hr)
        r = Rand(seed)

        def wobble(gx: float, k: float) -> float:
            return math.sin(gx * 0.071 + k) * 0.6 + math.sin(gx * 0.023 + 2 * k) * 0.4
        y0 = hr  # surface line
        round_l, round_r = (10.0 if left else 0.0), (10.0 if right else 0.0)
        body = (f"M{round_l:.1f} {y0 + 6:.1f} L{w - round_r:.1f} {y0 + 6:.1f} "
                f"Q{w:.1f} {y0 + 6:.1f} {w:.1f} {y0 + 6 + round_r:.1f} L{w:.1f} {h + hr:.1f} L0 {h + hr:.1f} L0 {y0 + 6 + round_l:.1f} "
                f"Q0 {y0 + 6:.1f} {round_l:.1f} {y0 + 6:.1f} Z")
        SOIL_TOP, SOIL, SOIL_DEEP = self.c["soil_top"], self.c["soil"], self.c["soil_deep"]
        GRASS_TOP, GRASS, GRASS_DARK, GRASS_LIGHT = self.c["grass_top"], self.c["grass"], self.c["grass_dark"], self.c["grass_light"]
        s.path(body, fill=s.linear(0, y0, 0, y0 + h, [(0, SOIL_TOP), (0.35, SOIL), (1, SOIL_DEEP)]))
        # strata
        for k in range(1, 4):
            yy = y0 + 26 + k * 30
            if yy > h + hr - 6:
                break
            pts = [(lx, yy + 4 * wobble(x0 + lx, k)) for lx in [i * w / 8 for i in range(9)]]
            s.path(smooth_open(pts), stroke=shade(SOIL, -0.25), width=2.4, opacity=0.35)
        # pebbles and roots
        for _ in range(max(2, int(w / 26))):
            px, py = r.uniform(6, w - 6), r.uniform(y0 + 22, h + hr - 8)
            pr = r.uniform(2.5, 6.5)
            s.ellipse(px, py, pr * 1.3, pr, fill=s.radial(px - pr * 0.4, py - pr * 0.4, pr * 1.6, [(0, "#d8c0a0"), (1, "#8a6e56")]),
                      stroke=shade(SOIL_DEEP, -0.2), width=0.8, opacity=0.9)
        for _ in range(max(1, int(w / 90))):
            rx0 = r.uniform(10, w - 10)
            pts = [(rx0, y0 + 10)]
            for k in range(4):
                pts.append((pts[-1][0] + r.uniform(-7, 7), pts[-1][1] + r.uniform(6, 11)))
            s.path(smooth_open(pts), stroke="#6a3f22", width=1.6, opacity=0.7)
        # side cliffs (exposed edges get a darker face)
        if left:
            s.path(f"M0 {y0 + 12} L7 {y0 + 14} L6 {h + hr} L0 {h + hr} Z", fill=shade(SOIL_DEEP, -0.1), opacity=0.45)
        if right:
            s.path(f"M{w} {y0 + 12} L{w - 7} {y0 + 14} L{w - 6} {h + hr} L{w} {h + hr} Z", fill=shade(SOIL_DEEP, -0.1), opacity=0.45)
        if top:
            # shadow under the lip
            s.path(smooth_open([(round_l, y0 + 15), (w / 2, y0 + 17), (w - round_r, y0 + 15)]), stroke="#3a2416", width=5, opacity=0.25)
            # scalloped grass cap
            # top edge and scalloped lip sampled on a world-aligned grid
            step = 12.0
            first = math.floor(x0 / step) * step - x0
            xs = [0.0] + [first + i * step for i in range(1, int((w - first) / step) + 1) if 0 < first + i * step < w] + [w]
            pts_top = [(lx, y0 - 1.2 + 0.8 * wobble(x0 + lx, 0.5)) for lx in xs]
            bottom = []
            for lx in reversed(xs):
                gx = x0 + lx
                scallop = 3.0 if int(math.floor(gx / step)) % 2 else 0.0
                bottom.append((lx, y0 + 11 + 1.8 * wobble(gx, 1.7) + scallop))
            d = smooth_open(pts_top) + "".join(f"L{px:.2f} {py:.2f}" for px, py in bottom) + "Z"
            s.path(d, fill=s.linear(0, y0 - 2, 0, y0 + 14, [(0, GRASS_TOP), (0.5, GRASS), (1, GRASS_DARK)]))
            # outline only the hanging edge (never the chunk's vertical borders)
            s.path(smooth_open(list(reversed(bottom)), 0.6), stroke=shade(GRASS_DARK, -0.35), width=1.2)
            if left:
                s.path(f"M0 {y0 - 1.2:.2f} L0 {bottom[-1][1]:.2f}", stroke=shade(GRASS_DARK, -0.35), width=1.6)
            if right:
                s.path(f"M{w:.2f} {y0 - 1.2:.2f} L{w:.2f} {bottom[0][1]:.2f}", stroke=shade(GRASS_DARK, -0.35), width=1.6)
            s.path(smooth_open(pts_top), stroke=GRASS_LIGHT, width=1.6, opacity=0.9)
            # blades poking above the surface
            for _ in range(max(3, int(w / 9))):
                bx = r.uniform(2, w - 2)
                bh = r.uniform(3, 8)
                lean = r.uniform(-2.5, 2.5)
                s.path(f"M{bx - 1.4:.2f} {y0 + 1:.2f} Q{bx + lean * 0.4:.2f} {y0 - bh * 0.5:.2f} {bx + lean:.2f} {y0 - bh:.2f} "
                       f"Q{bx + 0.6:.2f} {y0 - bh * 0.4:.2f} {bx + 1.4:.2f} {y0 + 1:.2f} Z",
                       fill=r.choice([GRASS_TOP, GRASS, "#b8ea7a"]))
            for _ in range(int(w / 70)):
                fx = r.uniform(6, w - 6)
                color = r.choice(["#ffffff", "#ffe27a", "#ffb3d1", "#b9d8ff"])
                for k in range(5):
                    a = k * 2 * math.pi / 5
                    s.circle(fx + math.cos(a) * 1.8, y0 - 4 + math.sin(a) * 1.8, 1.5, fill=color)
                s.circle(fx, y0 - 4, 1.1, fill="#f5b52a")
        return s

    def _cave(self, w: float, h: float, seed: int, left: bool, right: bool) -> Svg:
        r = Rand(seed)
        hr = self.terrain_headroom
        s = Svg(w, h + hr)
        s.rect(0, hr, w, h, fill=s.linear(0, hr, 0, h + hr, [(0, "#6a5a66"), (0.5, "#4a3e4a"), (1, "#2e2632")]), rx=4)
        for _ in range(max(2, int(w * h / 1400))):
            px, py = r.uniform(4, w - 4), r.uniform(hr + 4, h + hr - 4)
            pr = r.uniform(3, 9)
            s.path(blob(px, py, pr * 1.4, pr, 0.15, seed=px), fill=r.choice(["#5a4c58", "#7a6a74", "#463a44"]), opacity=0.85)
        for _ in range(int(w / 80) + 1):
            cx, cy = r.uniform(10, w - 10), r.uniform(hr + 6, h + hr - 10)
            s.polygon([(cx, cy - 7), (cx + 3.4, cy), (cx, cy + 4), (cx - 3.4, cy)], fill=s.linear(cx, cy - 7, cx, cy + 4, [(0, "#d8fff7"), (1, "#3bc0b0")]),
                      stroke="#1f6a6a", width=0.6)
        s.path(smooth_open([(0, hr + 1.5), (w, hr + 1.5)]), stroke="#8a7a86", width=2.5, opacity=0.7)
        return s

    # ------------------------------------------------------------------ blocks and platforms
    def block(self, kind: str, w: float, h: float) -> Svg:
        s = Svg(w, h)
        if kind in ("question", "used"):
            used = kind == "used"
            top, bottom = ("#c9a77a", "#7a5a3a") if used else ("#ffdf7a", "#e0951f")
            s.path(rounded_rect_path(0.6, 0.6, w - 1.2, h - 1.2, 4.5), fill=s.linear(0, 0, 0, h, [(0, top), (1, bottom)]), stroke=INK, width=1.3)
            s.path(rounded_rect_path(3, 3, w - 6, h - 6, 3), fill=None, stroke=shade(top, 0.45), width=1.1, opacity=0.8)
            s.path(f"M3 {h - 3.5} L{w - 3} {h - 3.5}", stroke=shade(bottom, -0.3), width=1.4, opacity=0.6)
            for cx, cy in ((4.6, 4.6), (w - 4.6, 4.6), (4.6, h - 4.6), (w - 4.6, h - 4.6)):
                s.circle(cx, cy, 1.3, fill=shade(bottom, -0.2) if not used else "#5a4a3a")
            if not used:
                s.polygon(star_points(w / 2, h / 2, min(w, h) * 0.32, min(w, h) * 0.1, 4), fill="#fff7d0", stroke="#c9781a", width=0.8)
            else:
                s.circle(w / 2, h / 2, 2.4, fill="#5a4a3a")
        elif kind == "brick":
            s.path(rounded_rect_path(0.6, 0.6, w - 1.2, h - 1.2, 3), fill="#f0d2a8", stroke=INK, width=1.2)
            rows = 2
            rh = (h - 2) / rows
            for row in range(rows):
                y = 1 + row * rh
                offset = 0 if row % 2 == 0 else 10
                x = -offset
                while x < w:
                    bx0, bx1 = max(1.4, x + 1.2), min(w - 1.4, x + 20 - 1.2)
                    if bx1 > bx0 + 2:
                        s.path(rounded_rect_path(bx0, y + 1.1, bx1 - bx0, rh - 2.2, 1.6),
                               fill=s.linear(0, y, 0, y + rh, [(0, "#e08a5c"), (1, "#a8513a")]), stroke="#7a3424", width=0.7)
                        s.line(bx0 + 1, y + 2.2, bx1 - 1, y + 2.2, "#f4b08a", 0.9, 0.7)
                    x += 20
        return s

    def platform(self, kind: str, w: float, h: float, style: str = "") -> Svg:
        s = Svg(w, h + 10)
        if kind == "moving":
            s.path(rounded_rect_path(0.8, 2, w - 1.6, h - 2, 4), fill=s.linear(0, 2, 0, h, [(0, "#d9a066"), (1, "#8a5a33")]), stroke=INK, width=1.2)
            for x in range(10, int(w) - 4, 16):
                s.line(x, 4, x, h - 2, "#7a4a28", 1.0, 0.6)
            s.path(f"M2 3 Q{w / 2} 0 {w - 2} 3", stroke="#7ac85a", width=3.0)
            for x in range(6, int(w), 22):
                s.path(blob(x, 3, 5, 3, 0.1, seed=x), fill="#6abf52", stroke="#2f7a36", width=0.6)
            s.path(f"M8 {h} Q{w / 2} {h + 9} {w - 8} {h}", stroke="#5a3a22", width=1.6, opacity=0.8)
        elif kind == "crumble":
            s.path(rounded_rect_path(0.6, 0.6, w - 1.2, h - 1.2, 3.5), fill=s.linear(0, 0, 0, h, [(0, "#d6b088"), (1, "#9a7050")]), stroke=INK, width=1.2)
            r = Rand(int(w))
            for _ in range(3):
                x = r.uniform(8, w - 8)
                s.path(smooth_open([(x, 1.5), (x + r.uniform(-4, 4), h * 0.5), (x + r.uniform(-5, 5), h - 1.5)]), stroke="#5a3e2a", width=1.1)
            for x in range(6, int(w), 14):
                s.path(f"M{x} {h - 1} q2 6 0 9", stroke="#6a4a2a", width=1.0, opacity=0.7)
        elif kind == "ledge":
            return self.terrain("terrain", w, h, int(w * 7 + h), True, True)
        elif kind == "semisolid":
            s.path(rounded_rect_path(0.6, 0.6, w - 1.2, min(h, 8), 3), fill=s.linear(0, 0, 0, 8, [(0, "#c98d55"), (1, "#7a4a28")]), stroke=INK, width=1.1)
            for x in range(14, int(w), 28):
                s.line(x, 8, x - 6, h + 8, "#6a4426", 2.0)
        elif kind == "spring":
            s.rect(w / 2 - 3, h * 0.45, 6, h * 0.55, fill="#e9e2c8", stroke=INK, width=1.0, rx=2)
            s.path(blob(w / 2, h * 0.45, w / 2, h * 0.42, 0.04, seed=3, squash_top=1.2),
                   fill=s.radial(w * 0.4, h * 0.2, w * 0.7, [(0, "#ffb0c8"), (0.6, "#e84a6a"), (1, "#a82a4a")]), stroke=INK, width=1.2)
            for k in range(4):
                s.circle(w * (0.25 + k * 0.17), h * (0.3 + 0.12 * (k % 2)), 2.2, fill="#ffffff", opacity=0.85)
        else:  # conveyor / switch fallbacks for this world
            s.path(rounded_rect_path(0.6, 0.6, w - 1.2, h - 1.2, h / 2), fill="#8a9aa8", stroke=INK, width=1.2)
        return s

    def pipe(self, w: float, h: float, warp: bool) -> Svg:
        s = Svg(w, h)
        body = s.linear(0, 0, w, 0, [(0, "#2f8f8a"), (0.25, "#6fd8c8"), (0.5, "#3aa89c"), (1, "#1e5f62")])
        s.path(rounded_rect_path(4, 10, w - 8, h - 10, 2), fill=body, stroke=INK, width=1.3)
        s.path(rounded_rect_path(0.8, 0.8, w - 1.6, 14, 4), fill=s.linear(0, 0, w, 0, [(0, "#2f8f8a"), (0.3, "#8ae8d8"), (0.6, "#3aa89c"), (1, "#1e5f62")]),
               stroke=INK, width=1.3)
        s.path(f"M3 13 L{w - 3} 13", stroke="#f2c14e", width=2.0)
        if h > 24:
            s.path(f"M5 {h - 6} L{w - 5} {h - 6}", stroke="#f2c14e", width=1.6, opacity=0.8)
        if warp:
            s.circle(w / 2, 26 if h > 34 else h * 0.66, 6, fill=s.radial(w / 2, 26, 7, [(0, "#d8fff7", 0.95), (1, "#73ffe1", 0)]))
            cy = 26 if h > 34 else h * 0.66
            s.polygon([(w / 2 - 4.5, cy - 3), (w / 2 + 4.5, cy - 3), (w / 2, cy + 3.5)], fill="#ffffff")
        return s

    # ------------------------------------------------------------------ props
    def _tree(self, seed: int) -> Svg:
        r = Rand(seed)
        s = Svg(150, 190)
        s.path("M68 190 Q66 150 70 120 Q60 104 48 98 Q62 100 72 110 Q78 96 92 88 Q84 104 82 120 Q86 150 84 190 Z",
               fill=s.linear(60, 0, 90, 0, [(0, "#a07048"), (1, "#5e3c24")]), stroke=INK, width=1.4)
        clusters = [(75, 70, 52), (42, 92, 34), (110, 90, 36), (60, 40, 34), (98, 46, 32)]
        for cx, cy, rad in clusters:
            s.path(blob(cx, cy + 6, rad, rad * 0.86, 0.07, seed=cx + seed), fill="#2f7a3e")
        for cx, cy, rad in clusters:
            s.path(blob(cx, cy, rad, rad * 0.86, 0.07, seed=cx + seed),
                   fill=s.radial(cx - rad * 0.35, cy - rad * 0.45, rad * 1.5, [(0, "#b6ea86"), (0.55, "#5fb553"), (1, "#3a8a44")]),
                   stroke=shade("#2f7a3e", -0.3), width=1.1)
        for _ in range(7):
            fx, fy = r.uniform(30, 120), r.uniform(30, 110)
            s.circle(fx, fy, r.uniform(3, 4.5), fill=s.radial(fx - 1, fy - 1, 5, [(0, "#ffd0a0"), (1, "#e8603a")]), stroke=INK, width=0.6)
        return s

    def _bush(self, seed: int) -> Svg:
        s = Svg(90, 52)
        for cx, cy, rad in ((26, 32, 22), (48, 26, 26), (68, 33, 20)):
            s.path(blob(cx, cy, rad, rad * 0.8, 0.08, seed=cx + seed),
                   fill=s.radial(cx - rad * 0.3, cy - rad * 0.5, rad * 1.5, [(0, "#a6e27a"), (0.6, "#56ad4e"), (1, "#3a8a44")]),
                   stroke=shade("#2f7a3e", -0.3), width=1.0)
        r = Rand(seed)
        for _ in range(4):
            x, y = r.uniform(16, 74), r.uniform(14, 38)
            s.circle(x, y, 2.2, fill=r.choice(["#ffffff", "#ffe27a", "#ffb3d1"]))
        return s

    def _flowers(self, seed: int) -> Svg:
        r = Rand(seed)
        s = Svg(60, 30)
        for _ in range(7):
            x = r.uniform(5, 55)
            top = r.uniform(4, 16)
            s.path(f"M{x:.1f} 30 Q{x + r.uniform(-3, 3):.1f} {top + 8:.1f} {x:.1f} {top:.1f}", stroke="#4f9a3e", width=1.3)
            color = r.choice(["#ffffff", "#ffe27a", "#ff9ab8", "#9ac8ff"])
            for k in range(5):
                a = k * 2 * math.pi / 5
                s.circle(x + math.cos(a) * 2.6, top + math.sin(a) * 2.6, 2.1, fill=color, stroke=shade(color, -0.4), width=0.4)
            s.circle(x, top, 1.4, fill="#f5a52a")
        return s

    def _fence(self) -> Svg:
        s = Svg(120, 36)
        for x in (8, 40, 72, 104):
            s.path(rounded_rect_path(x, 4, 8, 32, 2), fill=s.linear(x, 0, x + 8, 0, [(0, "#f2e2c0"), (1, "#c9a87a")]), stroke=INK, width=1.0)
            s.polygon([(x, 6), (x + 4, 0), (x + 8, 6)], fill="#f2e2c0", stroke=INK, width=1.0)
        for y in (12, 24):
            s.path(rounded_rect_path(2, y, 116, 5, 2), fill="#e8d4ac", stroke=INK, width=0.9)
        return s

    def _rock(self, seed: int) -> Svg:
        s = Svg(56, 36)
        s.path(blob(28, 23, 25, 14, 0.1, seed=seed, squash_top=1.15),
               fill=s.radial(20, 13, 30, [(0, "#efe6d2"), (0.55, "#b8ad98"), (1, "#7a7062")]), stroke=INK, width=1.3)
        s.path(smooth_open([(12, 26), (24, 22), (31, 27)]), stroke="#6a6052", width=1.1, opacity=0.7)
        s.path(blob(17, 12, 9, 3.4, 0.25, seed=seed + 1), fill=s.linear(0, 8, 0, 16, [(0, "#a6e36a"), (1, "#4f9a3e")]), opacity=0.95)
        s.path(blob(37, 13, 5, 2.4, 0.25, seed=seed + 2), fill="#7ac85a", opacity=0.9)
        s.ellipse(22, 15, 5, 2, fill="#ffffff", opacity=0.35)
        return s

    def _windmill(self) -> Svg:
        s = Svg(120, 200)
        s.polygon([(40, 200), (48, 70), (72, 70), (80, 200)], fill=s.linear(40, 0, 80, 0, [(0, "#f2e6cc"), (1, "#c9b088")]), stroke=INK, width=1.4)
        s.path("M44 74 L60 46 L76 74 Z", fill="#c0573a", stroke=INK, width=1.3)
        s.rect(54, 150, 12, 50, fill="#7a4a28", stroke=INK, width=1.0, rx=5)
        s.circle(60, 104, 6, fill="#4aa6e8", stroke=INK, width=1.0)
        return s

    def _windmill_blades(self) -> Svg:
        s = Svg(140, 140)
        for b in range(4):
            a = b * math.pi / 2
            ca, sa = math.cos(a), math.sin(a)
            pts = [(70 + ca * 6 - sa * 2, 70 + sa * 6 + ca * 2), (70 + ca * 66 - sa * 2, 70 + sa * 66 + ca * 2),
                   (70 + ca * 66 - sa * 14, 70 + sa * 66 + ca * 14), (70 + ca * 14 - sa * 12, 70 + sa * 14 + ca * 12)]
            s.polygon(pts, fill="#f7efd8", stroke=INK, width=1.1, opacity=0.95)
        s.circle(70, 70, 7, fill="#7a4a28", stroke=INK, width=1.0)
        return s

    def props(self) -> dict[str, PropSpec]:
        return {
            "tree_oak": PropSpec(lambda: self._tree(3), (76, 190)),
            "tree_oak_b": PropSpec(lambda: self._tree(9), (76, 190)),
            "bush": PropSpec(lambda: self._bush(5), (48, 50)),
            "bush_b": PropSpec(lambda: self._bush(13), (48, 50)),
            "flowers": PropSpec(lambda: self._flowers(4), (30, 30)),
            "flowers_b": PropSpec(lambda: self._flowers(17), (30, 30)),
            "fence": PropSpec(self._fence, (60, 36)),
            "rock": PropSpec(lambda: self._rock(2), (28, 34)),
            "windmill": PropSpec(self._windmill, (60, 200)),
            "windmill_blades": PropSpec(self._windmill_blades, (70, 70)),
        }

    def auto_decor(self, rng, surface_w: float):
        out = []
        x = rng.uniform(30, 120)
        while x < surface_w - 30:
            roll = rng.next()
            if roll < 0.32:
                out.append((rng.choice(["flowers", "flowers_b"]), x, rng.uniform(0.8, 1.1), "mid"))
            elif roll < 0.55:
                out.append((rng.choice(["bush", "bush_b"]), x, rng.uniform(0.7, 1.0), "back"))
            elif roll < 0.63:
                out.append(("rock", x, rng.uniform(0.6, 0.9), "mid"))
            elif roll < 0.72 and surface_w > 300:
                out.append((rng.choice(["tree_oak", "tree_oak_b"]), x, rng.uniform(0.85, 1.1), "back"))
            x += rng.uniform(110, 230)
        return out

    def weather(self) -> Weather:
        return Weather("leaves", 0.35, ("leaf", "petal"), wind=40.0)
