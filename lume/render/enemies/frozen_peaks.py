"""Montanhas Geladas creatures: Pinguim Patrulheiro, Caracol-de-Cristal,
Coruja Nevada, Boneco de Neve, Carneiro Glacial, Yeti-Mirim and the falling
Pingente de Gelo.

White creatures in a white world: every rig keeps the ink outline, a cool
blue shading and one saturated accent (beanie, scarf, eyes, ice horns, blue
face) so they read against the snow. Light comes from the upper left, as in
the world art.
"""

from __future__ import annotations

import math

from ..rig import DrawCommand, Xf
from ..svg import Svg, blob, mix, rounded_rect_path, smooth_closed, smooth_open, star_points
from .base import INK, CreatureRig, eye_svg, pupil_svg, register

FLASH = (255, 140, 140)
ICE_LINE = "#17548a"
SNOW_LINE = "#6a89b2"


# --------------------------------------------------------------------------- shared helpers
def _spin(root: Xf, cx: float, cy: float, ox: float, oy: float, angle: float) -> Xf:
    """Transform that turns a part around its visual centre placed at (cx, cy);
    (ox, oy) is that centre's offset from the part's pivot, in du."""
    a = math.radians(angle)
    return root.child(cx - (ox * math.cos(a) - oy * math.sin(a)), cy - (ox * math.sin(a) + oy * math.cos(a)), angle)


def _flash(e, t: float, out: list[DrawCommand]) -> list[DrawCommand]:
    """Hit flash while the damage timer runs (two-hit creatures and the hit itself)."""
    if e.hit_timer > 0 and int(t * 20) % 2 == 0:
        for c in out:
            c.tint = FLASH
    return out


def _root(rig: CreatureRig, e) -> Xf:
    return Xf() if e.alive else rig.defeat_xf(e, Xf())


def _shaggy(cx: float, cy: float, rx: float, ry: float, n: int, depth: float, seed: float = 0.0, tension: float = 0.7) -> str:
    """Closed outline with ``n`` tufts (fur, wool, snow lumps)."""
    pts = []
    for i in range(n * 2):
        a = math.pi * i / n
        k = 1 + (depth if i % 2 == 0 else -depth * 0.35) + 0.04 * math.sin(i * 2.3 + seed)
        pts.append((cx + math.cos(a) * rx * k, cy + math.sin(a) * ry * k))
    return smooth_closed(pts, tension)


def _eye_closed(size: float = 12.0) -> Svg:
    s = Svg(size, size * 0.6)
    s.path(f"M{size * 0.1:.2f} {size * 0.2:.2f} Q{size * 0.5:.2f} {size * 0.55:.2f} {size * 0.9:.2f} {size * 0.2:.2f}", stroke=INK, width=size * 0.14)
    return s


def _eye_x(size: float = 11.0) -> Svg:
    s = Svg(size, size)
    m, n = size * 0.18, size * 0.82
    s.path(f"M{m:.2f} {m:.2f} L{n:.2f} {n:.2f} M{n:.2f} {m:.2f} L{m:.2f} {n:.2f}", stroke=INK, width=size * 0.16)
    return s


def _brow(w: float = 12.0) -> Svg:
    s = Svg(w, 5)
    s.path(f"M1 1.4 L{w - 1:.1f} 3.8", stroke=INK, width=2.4)
    return s


def _star() -> Svg:
    s = Svg(14, 14)
    s.polygon(star_points(7, 7, 6.5, 2.8, 5), fill="#ffe27a", stroke=INK, width=0.9)
    return s


def _puff(size: float = 18.0) -> Svg:
    """Soft snow/steam puff (slide spray, snort, dust of a charge)."""
    s = Svg(size, size * 0.75)
    c = size / 2
    s.path(_shaggy(c, size * 0.42, size * 0.4, size * 0.28, 5, 0.18, seed=2, tension=1.0),
           fill=s.radial(c - size * 0.12, size * 0.3, size * 0.5, [(0, "#ffffff"), (0.7, "#eef5fb"), (1, "#c9daee")]), stroke=SNOW_LINE,
           width=size * 0.05)
    return s


def _snowball(size: float = 16.0) -> Svg:
    s = Svg(size, size)
    c = size / 2
    s.circle(c, c, c * 0.9, fill=s.radial(c * 0.7, c * 0.65, c * 1.2, [(0, "#ffffff"), (0.7, "#e2edf7"), (1, "#a9c0dc")]), stroke=INK,
             width=size * 0.07)
    s.ellipse(c * 0.75, c * 0.65, c * 0.28, c * 0.16, fill="#ffffff", opacity=0.9)
    return s


def _shared_parts() -> dict:
    return {
        "eye": (lambda: eye_svg(12), (6, 6)), "pupil": (lambda: pupil_svg(6), (3, 3)), "brow": (_brow, (6, 2.5)),
        "eye_closed": (_eye_closed, (6, 3.6)), "eye_x": (_eye_x, (5.5, 5.5)), "star": (_star, (7, 7)),
    }


def _face(rig: CreatureRig, e, t: float, at: Xf, eyes: tuple[tuple[float, float], ...], *, look: tuple[float, float] = (1.4, 0.4),
          brow: float = 8.0, brow_dy: float = -7.0, scale: float = 1.0, angry: bool = False) -> list[DrawCommand]:
    """Eyes with blinking, pupils and brows; X eyes once defeated."""
    out = []
    if not e.alive:
        for ex, ey in eyes:
            out.append(rig.cmd("eye_x", at.child(ex, ey), scale=scale))
        return out
    closed = rig.blink(t, e.origin_x * 0.37)
    for i, (ex, ey) in enumerate(eyes):
        eye = at.child(ex, ey)
        if closed:
            out.append(rig.cmd("eye_closed", eye, scale=scale))
        else:
            out.append(rig.cmd("eye", eye, scale=scale))
            out.append(rig.cmd("pupil", eye.child(look[0] * scale, look[1] * scale), scale=scale))
        tilt = (brow + (10 if angry else 0)) * (1 if i else -1)
        out.append(rig.cmd("brow", eye.child(0, brow_dy * scale, tilt + (180 if i == 0 else 0)), scale=scale))
    return out


# --------------------------------------------------------------------------- penguin
@register("penguin")
class Penguin(CreatureRig):
    """Pinguim Patrulheiro: waddles on patrol in a red beanie; belly-slides on ice."""

    du = 0.42

    def parts(self):
        def body():
            s = Svg(54, 52)
            s.path(blob(27, 28, 24, 23.5, 0.025, seed=4), fill=s.radial(18, 16, 44, [(0, "#5f7db2"), (0.5, "#2f4674"), (1, "#172342")]),
                   stroke=INK, width=1.8)
            s.path(blob(33, 31, 15.5, 18.5, 0.03, seed=2), fill=s.radial(30, 24, 26, [(0, "#ffffff"), (0.6, "#f6eedf"), (1, "#d6c6aa")]))
            s.path("M9 18 Q12 10 19 7", stroke="#9fb6e0", width=2.2, opacity=0.55)
            return s

        def head():
            s = Svg(44, 38)
            s.path(blob(21, 20, 19, 17, 0.03, seed=6), fill=s.radial(14, 11, 32, [(0, "#5f7db2"), (0.55, "#2f4674"), (1, "#172342")]),
                   stroke=INK, width=1.7)
            s.path(blob(28, 20, 12.5, 10.5, 0.05, seed=7), fill=s.radial(26, 16, 15, [(0, "#ffffff"), (1, "#e6ddcf")]))
            s.ellipse(35, 27, 3.4, 2.0, fill="#f2948a", opacity=0.6)
            return s

        def beak():
            s = Svg(18, 12)
            s.path("M1 2.5 Q9 2 17 6 Q9 6.6 1 6.2 Z", fill=s.linear(0, 2, 0, 7, [(0, "#ffd27a"), (1, "#f08a2a")]), stroke=INK, width=1.1)
            s.path("M1 6.4 Q8 7 14 7.4 Q8 10.5 1.5 9.6 Z", fill="#d9701e", stroke=INK, width=1.0)
            return s

        def hat():
            s = Svg(38, 26)
            s.path("M5 19 Q6 4 19 3 Q33 4 34 19 Z", fill=s.radial(14, 8, 26, [(0, "#ff8a7a"), (0.55, "#d6453f"), (1, "#8f2228")]), stroke=INK, width=1.4)
            for x in (12, 19, 26):
                s.path(f"M{x} 6 Q{x - 1} 12 {x} 18", stroke="#a82f30", width=1.0, opacity=0.7)
            s.path(rounded_rect_path(3, 16, 32, 7, 3.5), fill=s.linear(0, 16, 0, 23, [(0, "#ffffff"), (1, "#cbd9ea")]), stroke=INK, width=1.2)
            s.path(_shaggy(20, 4.5, 4.6, 4.2, 5, 0.15, seed=3, tension=1.0), fill="#ffffff", stroke=INK, width=1.0)
            return s

        def flipper():
            s = Svg(16, 32)
            s.path("M4 2 Q14 4 12 18 Q10 28 5 30 Q2 22 2 12 Q2 5 4 2 Z", fill=s.linear(0, 0, 14, 0, [(0, "#3d5788"), (1, "#18233f")]),
                   stroke=INK, width=1.4)
            s.path("M5 6 Q4 16 6 26", stroke="#7f9ccc", width=1.0, opacity=0.6)
            return s

        def foot():
            s = Svg(18, 10)
            s.path("M2 8.5 Q2 3 8 2.6 Q14 3 17 7 Q15 9.5 12 8.4 Q10 10 7.5 8.6 Q5 10 2 8.5 Z",
                   fill=s.linear(0, 2, 0, 10, [(0, "#ffb85a"), (1, "#e0761e")]), stroke=INK, width=1.1)
            return s

        return {**_shared_parts(), "body": (body, (27, 51)), "head": (head, (20, 35)), "beak": (beak, (2, 5.5)), "hat": (hat, (19, 22)),
                "flipper": (flipper, (6, 3)), "foot": (foot, (7, 9)), "spray": (lambda: _puff(18), (9, 12))}

    def commands(self, e, t):
        root = _root(self, e)
        out: list[DrawCommand] = []
        if e.alive and e.anim == "slide":
            return _flash(e, t, self._slide(e, t, root))
        walk = e.alive and e.anim == "walk"
        ph = t * 7.5
        waddle = math.sin(ph) * 7 if walk else 0.0
        bob = -abs(math.sin(ph)) * 2.0 if walk else 0.0
        hop = -8 * math.sin(min(1.0, e.state_time / 0.4) * math.pi) if e.alive and e.anim == "alert" else 0.0
        body = root.child(0, -3 + bob + hop, waddle)
        flap = math.sin(ph) * 14 if walk else (25 if e.anim == "alert" else 0.0)
        out.append(self.cmd("flipper", body.child(12, -34, -28 - flap * 0.6)))
        out.append(self.cmd("foot", root.child(-7, -(max(0.0, math.sin(ph)) * 3 if walk else 0))))
        out.append(self.cmd("foot", root.child(8, -(max(0.0, -math.sin(ph)) * 3 if walk else 0))))
        out.append(self.cmd("body", body))
        head = body.child(3, -40, -waddle * 0.4)
        out.append(self.cmd("head", head))
        out += _face(self, e, t, head, ((5, -20), (14, -20)), brow=10, angry=True)
        out.append(self.cmd("beak", head.child(18, -14)))
        out.append(self.cmd("hat", head.child(0, -28, -6 + waddle * 0.3)))
        out.append(self.cmd("flipper", body.child(-15, -32, 14 + flap)))
        return _flash(e, t, out)

    def _slide(self, e, t: float, root: Xf) -> list[DrawCommand]:
        """Belly slide: lying flat, head up, flippers swept back, snow spraying."""
        out = []
        wob = math.sin(t * 18) * 2.5
        k = min(1.0, e.state_time / 0.15)
        angle = 86 * k
        body = _spin(root, 2, -24 * k - 27 * (1 - k), 0, -23, angle + wob)
        out.append(self.cmd("spray", root.child(-24 + math.sin(t * 25) * 2, -1), scale=0.8 + 0.25 * abs(math.sin(t * 13))))
        out.append(self.cmd("foot", root.child(-27, -10, -96)))
        out.append(self.cmd("foot", root.child(-25, -5, -84)))
        out.append(self.cmd("flipper", body.child(10, -26, 30)))
        out.append(self.cmd("body", body))
        head = body.child(2, -44, -angle * 0.72)
        out.append(self.cmd("head", head))
        out += _face(self, e, t, head, ((5, -20), (14, -20)), look=(2.0, 0.0), brow=14, angry=True)
        out.append(self.cmd("beak", head.child(18, -14)))
        out.append(self.cmd("hat", head.child(-2, -28, -24 + wob)))
        out.append(self.cmd("flipper", body.child(-14, -22, 30 + wob * 2)))
        out.append(self.cmd("spray", root.child(30, -1), scale=0.6 + 0.3 * abs(math.sin(t * 17 + 1))))
        return out


# --------------------------------------------------------------------------- crystal snail
@register("crystal_snail")
class CrystalSnail(CreatureRig):
    """Caracol-de-Cristal: soft periwinkle body under a faceted ice shell that
    spins like a gem when kicked."""

    du = 0.5

    def parts(self):
        def soft():
            s = Svg(68, 28)
            s.path(smooth_closed([(2, 25), (12, 14), (38, 11), (58, 13), (66, 22), (62, 26.5), (34, 27)], 0.7),
                   fill=s.linear(0, 9, 0, 28, [(0, "#eef1ff"), (0.55, "#c4ccf4"), (1, "#8f9ad8")]), stroke=INK, width=1.6)
            for x in (16, 28, 40, 52):
                s.circle(x, 20 + (x % 3), 1.0, fill="#ffffff", opacity=0.8)
            return s

        def head():
            s = Svg(26, 26)
            s.path(blob(13, 15.5, 11, 9.5, 0.04, seed=1), fill=s.radial(10, 11, 14, [(0, "#f6f7ff"), (1, "#a9b3e6")]), stroke=INK, width=1.5)
            s.path("M10 20.5 Q14 23.5 18 20", stroke=INK, width=1.3)
            s.ellipse(19, 18, 2.4, 1.4, fill="#f2948a", opacity=0.6)
            return s

        def stalk():
            s = Svg(12, 22)
            s.path("M6 21 Q4.6 12 6 6", stroke="#8f9ad8", width=3.4)
            s.path("M6 21 Q4.6 12 6 6", stroke="#e4e8ff", width=1.8)
            s.circle(6, 5.2, 4.4, fill="#ffffff", stroke=INK, width=1.1)
            s.circle(7.2, 5.4, 2.2, fill="#2a2238")
            s.circle(7.8, 4.6, 0.7, fill="#ffffff")
            return s

        def shell():
            s = Svg(54, 54)
            cx, cy, rad = 27.0, 28.0, 24.0
            s.circle(cx, cy, rad + 5, fill=s.radial(cx, cy, rad + 5, [(0, "#a8ecff", 0.45), (1, "#a8ecff", 0)]))
            n = 7
            outer = [(cx + math.cos(2 * math.pi * i / n - 0.4) * rad, cy + math.sin(2 * math.pi * i / n - 0.4) * rad * 0.94) for i in range(n)]
            inner = [(cx + 3 + math.cos(2 * math.pi * i / n + 0.05) * rad * 0.5, cy - 2 + math.sin(2 * math.pi * i / n + 0.05) * rad * 0.48)
                     for i in range(n)]
            for i in range(n):
                a, b = outer[i], outer[(i + 1) % n]
                c, d = inner[(i + 1) % n], inner[i]
                mid = math.atan2((a[1] + b[1]) / 2 - cy, (a[0] + b[0]) / 2 - cx)
                light = (1 + math.cos(mid - math.radians(-135))) / 2
                col = mix("#2f86c8", "#f0fcff", light)
                s.polygon([a, b, c, d], fill=col, stroke="#5fb0e0", width=0.6)
            for i in range(n):
                a, b = inner[i], inner[(i + 1) % n]
                mid = math.atan2((a[1] + b[1]) / 2 - cy, (a[0] + b[0]) / 2 - cx)
                light = (1 + math.cos(mid - math.radians(-135))) / 2
                s.polygon([a, b, (cx + 4, cy - 3)], fill=mix("#4aa6dc", "#ffffff", light * 0.9), stroke="#7fc8ee", width=0.5)
            pts = []
            for i in range(44):
                a = i * 0.33 + 0.6
                rr = 2 + i * 0.42
                pts.append((cx + 4 + math.cos(a) * rr * 0.9, cy - 3 + math.sin(a) * rr * 0.86))
            s.path(smooth_open(pts), stroke="#ffffff", width=1.4, opacity=0.75)
            s.polygon(outer, fill=None, stroke=INK, width=1.8)
            s.polygon(star_points(15, 15, 4.2, 1.0, 4), fill="#ffffff")
            return s

        def glint():
            s = Svg(12, 12)
            s.polygon(star_points(6, 6, 5.8, 1.3, 4), fill="#ffffff")
            return s

        return {**_shared_parts(), "soft": (soft, (34, 26)), "head": (head, (13, 24)), "stalk": (stalk, (6, 21)), "shell": (shell, (27, 52)),
                "glint": (glint, (6, 6)), "spray": (lambda: _puff(16), (8, 11))}

    def commands(self, e, t):
        root = _root(self, e)
        state = e.anim if e.alive else e.state
        out: list[DrawCommand] = []
        if state in ("shell", "slide", "wake"):
            if state == "slide" and e.alive:
                spin = (t * 900) % 360
                out.append(self.cmd("spray", root.child(-20, -1), scale=0.7 + 0.3 * abs(math.sin(t * 20))))
                out.append(self.cmd("shell", _spin(root, 0, -24, 0, -24, spin)))
                a = t * 7
                out.append(self.cmd("glint", root.child(math.cos(a) * 14, -24 + math.sin(a) * 14), scale=0.9))
                return _flash(e, t, out)
            shake = math.sin(t * 40) * 4 if state == "wake" and e.alive else 0.0
            if state == "wake" and e.alive:
                out.append(self.cmd("stalk", root.child(13, -9, 30 + shake * 2), scale=0.75))
                out.append(self.cmd("stalk", root.child(17, -8, 50 + shake * 2), scale=0.7))
            out.append(self.cmd("shell", _spin(root, 0, -24, 0, -24, shake)))
            return _flash(e, t, out)
        ph = t * 5
        stretch = 1 + 0.08 * math.sin(ph) if e.alive else 1.0
        out.append(self.cmd("soft", Xf(root.x, root.y, root.angle, root.sx * stretch, root.sy)))
        head = root.child(26 * stretch, -5)
        if e.alive:
            out.append(self.cmd("stalk", head.child(-3, -15, -14 + math.sin(t * 3) * 8)))
            out.append(self.cmd("stalk", head.child(4, -16, 8 + math.sin(t * 3 + 1) * 8)))
        out.append(self.cmd("head", head))
        if not e.alive:
            out.append(self.cmd("eye_x", head.child(3, -14), scale=0.8))
        out.append(self.cmd("shell", root.child(-7, -5, math.sin(ph) * 3)))
        return _flash(e, t, out)


# --------------------------------------------------------------------------- owl
@register("owl")
class Owl(CreatureRig):
    """Coruja Nevada: snowy owl with barred wings and amber eyes; the head
    stays steady while the body bobs with every wingbeat."""

    du = 0.42

    def parts(self):
        def body():
            s = Svg(46, 44)
            s.path(blob(23, 23, 19.5, 20, 0.03, seed=3), fill=s.radial(16, 13, 36, [(0, "#ffffff"), (0.6, "#e8eff8"), (1, "#a9bcd6")]),
                   stroke=INK, width=1.8)
            for row in range(3):
                for col in range(3):
                    x = 13 + col * 8.5 + (row % 2) * 4
                    y = 17 + row * 8
                    s.path(f"M{x - 2.4:.1f} {y:.1f} Q{x:.1f} {y + 2.2:.1f} {x + 2.4:.1f} {y:.1f}", stroke="#5a6f8f", width=1.3, opacity=0.75)
            return s

        def head():
            s = Svg(44, 38)
            s.path(smooth_closed([(4, 13), (8, 5), (14, 9), (22, 6), (30, 9), (36, 5), (40, 13), (41, 25), (33, 35), (22, 37), (11, 35), (3, 25)], 0.6),
                   fill=s.radial(16, 12, 34, [(0, "#ffffff"), (0.6, "#edf2f9"), (1, "#b4c5dc")]), stroke=INK, width=1.7)
            s.path(blob(23, 21, 14, 11.5, 0.05, seed=4), fill=s.radial(22, 18, 15, [(0, "#ffffff"), (1, "#dfe7f2")]))
            for x, y in ((10, 14), (34, 13), (8, 27), (37, 27)):
                s.path(f"M{x - 2:.1f} {y:.1f} Q{x:.1f} {y + 2:.1f} {x + 2:.1f} {y:.1f}", stroke="#5a6f8f", width=1.1, opacity=0.7)
            return s

        def eye():
            s = Svg(14, 14)
            s.circle(7, 7, 6.2, fill=s.radial(6, 6, 7, [(0, "#fff3a0"), (0.6, "#ffc83a"), (1, "#e08a1a")]), stroke=INK, width=1.2)
            return s

        def lid():
            s = Svg(14, 8)
            s.path("M1 6.5 Q7 1 13 6.5 Z", fill="#e8eff8", stroke=INK, width=1.0)
            return s

        def beak():
            s = Svg(9, 10)
            s.path("M1 1 Q8 1 7 6 Q6 9 3.5 9.5 Q4 5 1 1 Z", fill=s.linear(0, 1, 0, 9, [(0, "#6f7a8a"), (1, "#2a2f3a")]), stroke=INK, width=0.9)
            return s

        def wing(far: bool):
            s = Svg(58, 34)
            d = ("M52 6 C40 0 20 0 4 10 L8 15 L11 13 L13 20 L18 17 L21 24 L27 20 L30 27 L36 22 L40 26 L44 19 Q50 16 54 13 Q56 9 52 6 Z")
            top, low = ("#dfe8f3", "#9fb3cf") if far else ("#ffffff", "#c9d6e7")
            s.path(d, fill=s.linear(0, 2, 0, 26, [(0, top), (1, low)]), stroke=INK, width=1.5)
            s.path("M50 8 C40 5 24 5 12 12", stroke="#ffffff" if not far else "#eef3f9", width=2.0, opacity=0.8)
            for x, y in ((16, 14), (24, 16), (32, 18), (40, 17), (22, 21), (30, 22)):
                s.path(f"M{x - 2.6:.1f} {y:.1f} L{x + 2.6:.1f} {y - 1.2:.1f}", stroke="#4a5f80", width=1.4, opacity=0.8)
            return s

        def tail():
            s = Svg(20, 14)
            s.path("M18 2 Q8 3 2 11 Q7 10 9 13 Q12 9 18 8 Z", fill=s.linear(0, 2, 0, 12, [(0, "#ffffff"), (1, "#b4c5dc")]), stroke=INK, width=1.2)
            return s

        def talon():
            s = Svg(12, 10)
            s.path("M2 1 Q6 3 10 1 L10 4 Q11 8 8 9 M6 4 Q6 8 4.5 9 M3 4 Q2 7 1 8", fill="#cfd8e4", stroke=INK, width=1.1)
            return s

        return {**_shared_parts(), "body": (body, (23, 42)), "head": (head, (22, 35)), "owl_eye": (eye, (7, 7)), "lid": (lid, (7, 6)),
                "beak": (beak, (3, 1)), "wing": (lambda: wing(False), (51, 9)), "wing_far": (lambda: wing(True), (51, 9)),
                "tail": (tail, (17, 4)), "talon": (talon, (6, 1))}

    def commands(self, e, t):
        root = _root(self, e)
        out: list[DrawCommand] = []
        ph = t * 11.0
        beat = math.sin(ph)
        bob = -beat * 2.4 if e.alive else 0.0
        body = root.child(0, -6 + bob, 6)
        flap = 38 * beat + 4 if e.alive else -12.0
        fold = 0.72 + 0.28 * abs(beat) if e.alive else 0.9
        out.append(self.cmd("wing_far", Xf(*_xy(body.child(4, -30)), body.angle + flap + 8, body.sx, body.sy * fold)))
        out.append(self.cmd("tail", body.child(-14, -9, -10 + beat * 5)))
        out.append(self.cmd("talon", body.child(-4, -2)))
        out.append(self.cmd("talon", body.child(5, -1)))
        out.append(self.cmd("body", body))
        head = body.child(2, -32, -6 - bob * 0.7)
        out.append(self.cmd("head", head))
        if e.alive:
            closed = self.blink(t, e.origin_x * 0.29)
            for ex in (-7.0, 7.0):
                eye = head.child(ex, -15)
                out.append(self.cmd("owl_eye", eye))
                if closed:
                    out.append(self.cmd("eye_closed", eye.child(0, 1), scale=0.95))
                else:
                    out.append(self.cmd("pupil", eye.child(1.6, 0.6), scale=0.95))
                    out.append(self.cmd("lid", eye.child(0, -3.8, 12 if ex > 0 else -12), scale=0.9))
        else:
            for ex in (-7.0, 7.0):
                out.append(self.cmd("eye_x", head.child(ex, -15)))
        out.append(self.cmd("beak", head.child(1, -11)))
        out.append(self.cmd("wing", Xf(*_xy(body.child(-1, -27)), body.angle + flap, body.sx, body.sy * fold)))
        return _flash(e, t, out)


def _xy(xf: Xf) -> tuple[float, float]:
    return xf.x, xf.y


# --------------------------------------------------------------------------- snowman
@register("snowman")
class Snowman(CreatureRig):
    """Boneco de Neve: two-ball sentinel with a tin-bucket hat, red scarf and
    a pine-cone nose; twists back with a snowball before each throw."""

    du = 0.4

    def parts(self):
        def base():
            s = Svg(62, 50)
            s.path(blob(31, 26, 28.5, 22.5, 0.03, seed=5), fill=s.radial(20, 14, 46, [(0, "#ffffff"), (0.55, "#eef4fb"), (1, "#a8bfdc")]),
                   stroke=INK, width=1.9)
            s.path("M9 34 Q31 48 53 34", stroke="#9fb6d6", width=3.2, opacity=0.6)
            for y in (14, 25, 36):
                s.circle(37 - (y - 14) * 0.1, y, 2.5, fill=s.radial(36, y - 1, 3.2, [(0, "#5a5f6e"), (1, "#14161e")]))
            return s

        def head():
            s = Svg(40, 36)
            s.path(blob(20, 19, 17.5, 16, 0.03, seed=8), fill=s.radial(13, 11, 30, [(0, "#ffffff"), (0.6, "#eef4fb"), (1, "#aec4e0")]),
                   stroke=INK, width=1.7)
            s.ellipse(30, 24, 3.2, 1.9, fill="#f2948a", opacity=0.5)
            return s

        def bucket():
            s = Svg(32, 24)
            s.path("M6 21 L9 4 Q16 2 23 4 L26 21 Z", fill=s.linear(6, 0, 26, 0, [(0, "#8fb4c8"), (0.4, "#5f8aa0"), (1, "#2f5266")]), stroke=INK, width=1.4)
            s.path(rounded_rect_path(3, 18, 26, 5, 2.5), fill=s.linear(0, 18, 0, 23, [(0, "#a9c8d8"), (1, "#4a6f84")]), stroke=INK, width=1.2)
            s.path("M10 8 L21 8 M9.5 13 L22.5 13", stroke="#2f4a5a", width=0.9, opacity=0.7)
            s.path(blob(16, 3.6, 8, 2.6, 0.15, seed=2), fill="#ffffff", stroke=SNOW_LINE, width=0.7)
            return s

        def scarf():
            s = Svg(42, 14)
            s.path(rounded_rect_path(2, 3, 38, 9, 4.5), fill=s.linear(0, 3, 0, 12, [(0, "#ff6a5a"), (1, "#b42a2e")]), stroke=INK, width=1.3)
            for x in (10, 18, 26, 34):
                s.line(x, 3.6, x - 2, 11.4, "#ffffff", 1.6, 0.85)
            return s

        def scarf_tail():
            s = Svg(12, 24)
            s.path(rounded_rect_path(2, 1, 8, 19, 3), fill=s.linear(0, 1, 0, 20, [(0, "#e8463f"), (1, "#a82a2e")]), stroke=INK, width=1.2)
            s.line(2.5, 8, 9.5, 8, "#ffffff", 1.5, 0.85)
            for x in (3.5, 6, 8.5):
                s.line(x, 20, x, 23, "#c8333a", 1.4)
            return s

        def arm():
            s = Svg(38, 18)
            s.path("M2 10 Q16 8 35 6", stroke=INK, width=4.0)
            s.path("M2 10 Q16 8 35 6", stroke="#8a5a36", width=2.4)
            for x0, y0, x1, y1 in ((22, 7.5, 30, 1), (14, 8.6, 18, 15)):
                s.path(f"M{x0} {y0} L{x1} {y1}", stroke=INK, width=3.0)
                s.path(f"M{x0} {y0} L{x1} {y1}", stroke="#8a5a36", width=1.6)
            return s

        def coal():
            s = Svg(7, 8)
            s.ellipse(3.5, 4, 3, 3.5, fill=s.radial(2.6, 2.8, 4, [(0, "#6a6f80"), (1, "#101218")]))
            s.circle(2.4, 2.6, 0.9, fill="#ffffff", opacity=0.85)
            return s

        def grin():
            s = Svg(20, 10)
            for i in range(5):
                x = 3 + i * 3.5
                y = 3 + math.sin(math.pi * i / 4) * 3.4
                s.circle(x, y, 1.4, fill="#1a1c24")
            return s

        def nose():
            s = Svg(16, 10)
            s.path("M1 2 Q9 1 15 5 Q9 9 1 8 Q-0.5 5 1 2 Z", fill=s.linear(0, 1, 0, 9, [(0, "#b0784a"), (1, "#5a3420")]), stroke=INK, width=1.1)
            for x in (4.5, 8.5):
                s.path(f"M{x} 2.4 Q{x + 1.6} 5 {x} 7.4", stroke="#3a2214", width=0.9)
            return s

        return {**_shared_parts(), "base": (base, (31, 49)), "head": (head, (20, 34)), "bucket": (bucket, (16, 21)), "scarf": (scarf, (21, 7)),
                "scarf_tail": (scarf_tail, (6, 2)), "arm": (arm, (2, 10)), "coal": (coal, (3.5, 4)), "grin": (grin, (10, 3)),
                "nose": (nose, (1.5, 5)), "ball": (lambda: _snowball(15), (7.5, 7.5))}

    def commands(self, e, t):
        root = _root(self, e)
        out: list[DrawCommand] = []
        anim = e.anim if e.alive else "idle"
        sway = math.sin(t * 2.2) * 2.5
        wind = 0.0
        if anim == "charge":
            wind = min(1.0, e.state_time / 0.4)
            wind = wind * wind * (3 - 2 * wind)
        throw = min(1.0, e.state_time / 0.12) if anim == "fire" else 0.0
        lean = sway * (1 - wind) - 9 * wind + 12 * throw
        squash = 1 - 0.05 * wind + 0.04 * throw
        base = Xf(root.x, root.y, root.angle + lean * 0.4, root.sx * (2 - squash), root.sy * squash)
        # back arm, base, scarf, head and its face, hat, front (throwing) arm
        out.append(self.cmd("arm", base.child(-18, -32, 200 - 10 * wind + sway)))
        out.append(self.cmd("base", base))
        head = base.child(2, -41, lean * 0.6 + sway * 0.4)
        out.append(self.cmd("scarf_tail", head.child(-9, 1, 12 - lean * 0.8 + math.sin(t * 3) * 6)))
        out.append(self.cmd("head", head))
        if e.alive:
            closed = self.blink(t, e.origin_x * 0.41) and wind == 0
            for i, ex in enumerate((2.0, 12.0)):
                eye = head.child(ex, -19)
                if closed:
                    out.append(self.cmd("eye_closed", eye, scale=0.6))
                else:
                    out.append(self.cmd("coal", eye, scale=1.0 if wind < 0.5 else 0.85))
                out.append(self.cmd("brow", eye.child(0, -5.5, (14 + 10 * wind) * (1 if i else -1) + (180 if i == 0 else 0)), scale=0.8))
            out.append(self.cmd("grin", head.child(7, -9, -4 * wind), scale=1.0 + 0.15 * throw))
        else:
            for ex in (2.0, 12.0):
                out.append(self.cmd("eye_x", head.child(ex, -19), scale=0.75))
        out.append(self.cmd("nose", head.child(12, -14, -6 * wind + 4 * throw)))
        out.append(self.cmd("scarf", head.child(0, 2)))
        out.append(self.cmd("bucket", head.child(-2, -29, -14 - 8 * wind + 10 * throw + sway)))
        arm_angle = -18 + sway - 150 * wind + 120 * throw
        arm = base.child(17, -32, arm_angle)
        out.append(self.cmd("arm", arm))
        if anim == "charge":
            out.append(self.cmd("ball", arm.child(33, -2)))
        return _flash(e, t, out)


# --------------------------------------------------------------------------- ram
@register("ram")
class Ram(CreatureRig):
    """Carneiro Glacial: woolly ram with curled ice horns. Paws the snow and
    snorts steam before charging; sees stars after hitting a wall."""

    du = 0.46

    def parts(self):
        def body():
            s = Svg(64, 52)
            s.path(_shaggy(32, 27, 28.5, 21, 8, 0.12, seed=4, tension=1.0),
                   fill=s.radial(22, 15, 46, [(0, "#ffffff"), (0.55, "#eef2f8"), (1, "#a6b7d1")]), stroke=INK, width=1.9)
            for cx, cy, rr in ((19, 20, 5.5), (32, 16, 6), (45, 21, 5.5), (25, 32, 5.5), (40, 33, 5.5)):
                s.path(f"M{cx - rr:.1f} {cy:.1f} Q{cx:.1f} {cy - rr:.1f} {cx + rr:.1f} {cy:.1f}", stroke="#b4c3da", width=1.6, opacity=0.85)
            s.path("M9 34 Q32 50 55 34", stroke="#8fa4c4", width=3.0, opacity=0.55)
            return s

        def head():
            s = Svg(48, 42)
            s.path("M4 18 Q2 26 6 30 Q10 26 12 21 Z", fill="#4a5470", stroke=INK, width=1.2)
            s.path("M8 14 Q14 4 26 6 Q36 8 42 20 Q46 27 43 32 Q37 36 30 33 Q22 33 15 29 Q8 25 8 14 Z",
                   fill=s.radial(20, 12, 34, [(0, "#9aa6be"), (0.55, "#66728f"), (1, "#353e58")]), stroke=INK, width=1.7)
            s.path("M33 25 Q40 23 43.5 27 Q42.5 32 37 32.5 Q33 31 33 25 Z", fill="#2c3348", opacity=0.45)
            s.ellipse(40.5, 27.4, 1.4, 1.0, fill="#101320")
            s.path("M30 32.6 Q34 34.5 38.5 33", stroke=INK, width=1.1)
            s.path(_shaggy(20, 8, 8.5, 5.5, 5, 0.2, seed=2, tension=1.0), fill="#f4f7fb", stroke=INK, width=1.2)
            return s

        def horn():
            s = Svg(32, 32)
            pts = []
            for i in range(36):
                a = -1.2 - i * 0.2
                rr = 12.5 - i * 0.27
                pts.append((16 + math.cos(a) * rr, 16 + math.sin(a) * rr))
            s.path(smooth_open(pts), stroke=INK, width=8.0)
            s.path(smooth_open(pts), stroke="#86d6f4", width=6.0)
            s.path(smooth_open(pts[:26]), stroke="#e9fbff", width=1.8, opacity=0.9)
            for i in range(3, 28, 4):
                x, y = pts[i]
                s.circle(x, y, 0.9, fill="#2f7fb8", opacity=0.75)
            return s

        def leg():
            s = Svg(12, 30)
            s.path(rounded_rect_path(3, 0, 7, 25, 3), fill=s.linear(3, 0, 10, 0, [(0, "#6a7690"), (1, "#323b54")]), stroke=INK, width=1.4)
            s.path(rounded_rect_path(1.5, 23, 10, 6.5, 2.5), fill="#1e2232", stroke=INK, width=1.2)
            return s

        def tail():
            s = Svg(16, 14)
            s.path(_shaggy(9, 7, 6, 5, 4, 0.2, seed=1, tension=1.0), fill="#f4f7fb", stroke=INK, width=1.3)
            return s

        def eye_open():
            s = Svg(12, 10)
            s.ellipse(6, 5.5, 4.6, 3.8, fill="#fff4cc", stroke=INK, width=1.1)
            s.circle(7, 5.8, 2.3, fill="#2a5ab0")
            s.circle(7.5, 5.8, 1.1, fill="#0a0a14")
            s.circle(6.4, 4.8, 0.6, fill="#ffffff")
            s.path("M0.5 1.2 L11.5 3.8", stroke=INK, width=2.4)
            return s

        def eye_daze():
            s = Svg(12, 10)
            s.ellipse(6, 5.5, 4.6, 3.8, fill="#fff4cc", stroke=INK, width=1.1)
            s.path("M6 5.5 m-3 0 a3 3 0 1 0 6 0 a2.2 2.2 0 1 0 -4.4 0 a1.2 1.2 0 1 0 2.4 0", stroke=INK, width=1.0)
            return s

        return {**_shared_parts(), "body": (body, (32, 46)), "head": (head, (11, 22)), "horn": (horn, (21, 5)), "leg": (leg, (6, 2)),
                "tail": (tail, (14, 7)), "eye_open": (eye_open, (6, 5)), "eye_daze": (eye_daze, (6, 5)), "puff": (lambda: _puff(16), (8, 12))}

    def commands(self, e, t):
        root = _root(self, e)
        state = e.anim if e.alive else "defeat"
        out: list[DrawCommand] = []
        speed = {"charge": 24.0, "walk": 8.0}.get(state, 0.0)
        ph = t * speed
        lean = {"charge": 7.0, "alert": -4.0, "stunned": -5.0}.get(state, 0.0)
        if state == "recover":
            lean = math.sin(e.state_time * 26) * 5 * max(0.0, 1 - e.state_time / 0.5)
        legs = []
        for i, lx in enumerate((-21, -11, 9, 19)):
            swing = math.sin(ph + (math.pi if i in (1, 2) else 0)) * (34 if state == "charge" else 18 if state == "walk" else 0)
            if state == "alert" and i == 3:
                swing = -42 + 48 * abs(math.sin(e.state_time * 13))
            legs.append(self.cmd("leg", root.child(lx, -27 - (abs(math.sin(ph)) * 1.5 if speed else 0), swing)))
        out += [legs[0], legs[2]]
        body = root.child(-3, -21 - abs(math.sin(ph)) * (3 if speed else 0), lean)
        out.append(self.cmd("tail", body.child(-29, -30, math.sin(t * 6) * 10)))
        out.append(self.cmd("body", body))
        out += [legs[1], legs[3]]
        head_angle = {"charge": 26.0, "alert": 14.0 + math.sin(t * 20) * 2, "stunned": math.sin(t * 6) * 10}.get(state, math.sin(t * 2) * 3)
        if state == "recover":
            head_angle = math.sin(e.state_time * 30) * 14 * max(0.0, 1 - e.state_time / 0.5)
        head = body.child(24, -29, head_angle - lean * 0.5)
        out.append(self.cmd("head", head))
        eye = "eye_daze" if state in ("stunned", "defeat") else "eye_open"
        out.append(self.cmd(eye, head.child(17, -7)))
        out.append(self.cmd("horn", head.child(5, -14, 6)))
        if state == "alert":
            k = (e.state_time * 3) % 1
            out.append(self.cmd("puff", head.child(36 + k * 10, 8 + k * 4), scale=0.4 + 0.5 * k, alpha=1 - k))
            out.append(self.cmd("puff", root.child(26 + k * 8, -2), scale=0.5 + 0.4 * k, alpha=0.9 - 0.8 * k))
        elif state == "charge":
            for j in range(2):
                k = (t * 4 + j * 0.5) % 1
                out.append(self.cmd("puff", root.child(-28 - k * 26, -2 - k * 6), scale=0.5 + 0.6 * k, alpha=1 - k))
        elif state == "stunned":
            for j in range(3):
                a = t * 5 + j * 2.1
                out.append(self.cmd("star", head.child(12 + math.cos(a) * 18, -30 + math.sin(a) * 6), scale=0.9))
        return _flash(e, t, out)


# --------------------------------------------------------------------------- yeti
@register("yeti")
class Yeti(CreatureRig):
    """Yeti-Mirim: shaggy cub with a blue face and little horns; hoists a big
    snowball over its head before each lobbed throw."""

    du = 0.42

    def parts(self):
        def body():
            s = Svg(66, 60)
            s.path(_shaggy(33, 31, 28, 26, 11, 0.12, seed=6, tension=0.75),
                   fill=s.radial(23, 18, 50, [(0, "#ffffff"), (0.55, "#e6eef8"), (1, "#9fb3d2")]), stroke=INK, width=1.9)
            s.path(blob(36, 36, 15, 15, 0.05, seed=3), fill=s.radial(34, 32, 17, [(0, "#f6f9fd"), (1, "#c9d6e8")]))
            for x, y in ((18, 22), (46, 18), (24, 44), (48, 42)):
                s.path(f"M{x - 3:.1f} {y:.1f} Q{x:.1f} {y + 4:.1f} {x + 3:.1f} {y:.1f}", stroke="#9fb3d2", width=1.4, opacity=0.8)
            return s

        def head():
            s = Svg(56, 50)
            for x, tilt in ((14, -1), (42, 1)):
                s.path(f"M{x - 4:.1f} 14 Q{x + tilt * 2:.1f} 0 {x + tilt * 9:.1f} 2 Q{x + tilt * 4:.1f} 8 {x + 4:.1f} 16 Z",
                       fill=s.linear(0, 0, 0, 16, [(0, "#fff8e6"), (1, "#d6c4a0")]), stroke=INK, width=1.3)
            s.path(_shaggy(28, 27, 24, 21, 10, 0.12, seed=9, tension=0.75),
                   fill=s.radial(20, 16, 40, [(0, "#ffffff"), (0.6, "#e6eef8"), (1, "#a6b9d6")]), stroke=INK, width=1.8)
            s.path("M12 26 Q12 15 28 14 Q44 15 44 26 Q44 40 28 41 Q12 40 12 26 Z",
                   fill=s.radial(24, 22, 22, [(0, "#a9c4ee"), (0.6, "#7f9fd4"), (1, "#5a78b0")]), stroke=INK, width=1.4)
            s.ellipse(36, 33, 3.4, 2, fill="#f2948a", opacity=0.55)
            s.path(_shaggy(28, 14, 12, 4.5, 5, 0.2, seed=1, tension=0.8), fill="#f4f8fc")
            return s

        def mouth(open_: bool):
            s = Svg(16, 10)
            if open_:
                s.path("M2 2 Q8 1 14 2 Q13 9 8 9.5 Q3 9 2 2 Z", fill="#3a1e3a", stroke=INK, width=1.1)
                s.polygon([(4, 2), (5.5, 4.6), (7, 2)], fill="#ffffff")
                s.polygon([(9, 2), (10.5, 4.6), (12, 2)], fill="#ffffff")
                s.ellipse(8, 7.6, 3, 1.4, fill="#e86a7a")
            else:
                s.path("M2 3 Q8 7 14 2.5", stroke=INK, width=1.4)
                s.polygon([(10, 4.6), (11.4, 7), (12.6, 4)], fill="#ffffff", stroke=INK, width=0.6)
            return s

        def arm():
            s = Svg(22, 40)
            s.path(_shaggy(11, 16, 8, 15, 6, 0.14, seed=4, tension=0.8), fill=s.linear(3, 0, 19, 0, [(0, "#f4f8fc"), (1, "#a9bcd8")]),
                   stroke=INK, width=1.5)
            s.path(blob(11, 33, 6.4, 5.4, 0.05, seed=2), fill=s.radial(9, 31, 7, [(0, "#a9c4ee"), (1, "#5a78b0")]), stroke=INK, width=1.3)
            return s

        def foot():
            s = Svg(26, 13)
            s.path(_shaggy(13, 6, 11, 5.4, 5, 0.12, seed=5, tension=0.9), fill=s.linear(0, 0, 0, 12, [(0, "#f4f8fc"), (1, "#a9bcd8")]),
                   stroke=INK, width=1.4)
            s.path("M4 10.5 Q13 13 22 10.5", stroke="#5a78b0", width=2.0)
            return s

        return {**_shared_parts(), "body": (body, (33, 57)), "head": (head, (28, 46)), "mouth": (lambda: mouth(False), (8, 4)),
                "mouth_open": (lambda: mouth(True), (8, 4)), "arm": (arm, (11, 4)), "foot": (foot, (13, 11)),
                "ball": (lambda: _snowball(28), (14, 14))}

    def commands(self, e, t):
        root = _root(self, e)
        state = e.anim if e.alive else "defeat"
        out: list[DrawCommand] = []
        ph = t * 9.0
        stepping = state == "step"
        windup = state == "windup"
        throw = state == "throw"
        jump = state == "jump"
        k_w = min(1.0, e.state_time / 0.25) if windup else 0.0
        k_t = min(1.0, e.state_time / 0.1) if throw else 0.0
        bob = -abs(math.sin(ph)) * 2.5 if stepping else 0.0
        stretch = 1 + 0.06 * k_w - 0.04 * k_t + (0.06 if jump else 0.0)
        lean = math.sin(ph) * 4 if stepping else (-6 * k_w + 12 * k_t)
        lift_a = max(0.0, math.sin(ph)) * 4 if stepping else (7 if jump else 0)
        lift_b = max(0.0, -math.sin(ph)) * 4 if stepping else (7 if jump else 0)
        out.append(self.cmd("foot", root.child(-11, -lift_a, -12 if jump else 0)))
        out.append(self.cmd("foot", root.child(11, -lift_b, 12 if jump else 0)))
        body = Xf(*_xy(root.child(0, -6 + bob)), root.angle + lean, root.sx, root.sy * stretch)
        if windup:
            back_a, front_a = -160 * k_w - 15 * (1 - k_w), 160 * k_w + 15 * (1 - k_w)
        elif throw:
            back_a, front_a = -95 + 20 * (1 - k_t), -85 + 30 * (1 - k_t)
        elif jump:
            back_a, front_a = -150.0, 150.0
        else:
            swing = math.sin(ph) * 22 if stepping else math.sin(t * 2) * 5
            back_a, front_a = 18 + swing, -18 + swing
        back_arm = body.child(-23, -40, back_a)
        front_arm = body.child(23, -40, front_a)
        out.append(self.cmd("arm", back_arm))
        out.append(self.cmd("body", body))
        head = body.child(1, -44, -lean * 0.5)
        out.append(self.cmd("head", head))
        out += _face(self, e, t, head, ((-6, -19), (6, -19)), look=(1.6, 0.6 if not windup else -1.0), brow=8, brow_dy=-6.5,
                     scale=0.9, angry=windup or throw)
        out.append(self.cmd("mouth_open" if (windup or throw or jump) and e.alive else "mouth", head.child(0, -8)))
        if windup and e.alive:
            ha, hb = back_arm.child(0, 29), front_arm.child(0, 29)
            out.append(self.cmd("ball", Xf((ha.x + hb.x) / 2, (ha.y + hb.y) / 2 - 9, 0, root.sx, root.sy)))
        out.append(self.cmd("arm", front_arm))
        return _flash(e, t, out)


# --------------------------------------------------------------------------- falling icicle
@register("icicle")
class Icicle(CreatureRig):
    """Pingente de Gelo: a giant icicle under a frozen rock cap (the cap is a
    safe, flat top). It sleeps, wakes and shakes, plunges, cracks on impact and
    slowly rises again. Its feet origin is the tip; the snow on the cap is
    flush with the hitbox top so standing on it looks right."""

    du = 0.43

    def parts(self):
        def body():
            s = Svg(82, 96)
            # spike
            spike = "M9 24 Q13 46 26 64 Q35 80 41 95 Q47 80 56 64 Q69 46 73 24 Z"
            s.path(spike, fill=s.linear(9, 0, 73, 0, [(0, "#eafcff"), (0.35, "#a6e6fb"), (0.7, "#4fb4e6"), (1, "#2a7fc0")]), stroke=INK, width=1.8)
            s.path("M41 95 Q47 80 56 64 Q69 46 73 24 L52 24 Q50 56 41 95 Z", fill="#1f6aa8", opacity=0.28)
            s.path("M20 27 Q24 48 34 66 Q38 76 41 88", stroke="#ffffff", width=2.6, opacity=0.85)
            s.path("M30 27 Q32 44 38 58", stroke="#ffffff", width=1.4, opacity=0.6)
            for x, y, rr in ((50, 40, 1.6), (44, 56, 1.1), (56, 32, 1.2), (36, 44, 0.9)):
                s.circle(x, y, rr, stroke="#ffffff", width=0.6, opacity=0.7)
            # frozen rock cap (safe top)
            s.path(rounded_rect_path(3, 6, 76, 22, 8), fill=s.linear(0, 6, 0, 28, [(0, "#9aaccb"), (0.5, "#6a7c9c"), (1, "#3c4866")]), stroke=INK, width=1.8)
            s.path("M10 20 L22 16 L30 22 M50 15 L58 20 L70 16", stroke="#2a3450", width=1.2, opacity=0.7)
            s.path(_shaggy(41, 6.5, 37, 5.5, 9, 0.12, seed=3, tension=0.9), fill=s.linear(0, 0, 0, 12, [(0, "#ffffff"), (1, "#cddcee")]),
                   stroke=SNOW_LINE, width=1.0)
            s.rect(6, 1.5, 70, 4, fill="#ffffff")
            for x, ln in ((6, 7), (14, 10), (68, 9), (76, 6)):
                s.path(f"M{x - 2:.1f} 26 Q{x - 0.6:.1f} {26 + ln * 0.6:.1f} {x:.1f} {26 + ln:.1f} Q{x + 0.8:.1f} {26 + ln * 0.5:.1f} {x + 2:.1f} 26 Z",
                       fill="#c8f0ff", stroke=ICE_LINE, width=0.6)
            return s

        def eyes(mode: str):
            s = Svg(40, 16)
            if mode == "sleep":
                for x in (11, 29):
                    s.path(f"M{x - 5} 8 Q{x} 11.5 {x + 5} 8", stroke="#123a66", width=2.0)
            elif mode == "daze":
                for x in (11, 29):
                    s.path(f"M{x} 8.5 m-3.6 0 a3.6 3.6 0 1 0 7.2 0 a2.6 2.6 0 1 0 -5.2 0 a1.4 1.4 0 1 0 2.8 0", stroke="#123a66", width=1.2)
            else:
                for x, sign in ((11, 1), (29, -1)):
                    s.ellipse(x, 9, 4.6, 4.2, fill="#ffffff", stroke="#123a66", width=1.2)
                    s.circle(x - sign * 0.6, 9.6, 2.2, fill="#0e2240")
                    s.path(f"M{x - 6 * sign:.1f} {2 if sign > 0 else 5.5} L{x + 5 * sign:.1f} {5.5 if sign > 0 else 2}", stroke="#0e2240", width=2.2)
            return s

        def crack():
            s = Svg(40, 50)
            s.path("M20 0 L17 10 L23 18 L16 29 L21 38 L18 50", stroke="#ffffff", width=1.6, opacity=0.95)
            s.path("M17 10 L9 15 M23 18 L31 21 M16 29 L8 33", stroke="#ffffff", width=1.1, opacity=0.9)
            s.path("M20.8 0 L17.8 10 L23.8 18 L16.8 29 L21.8 38", stroke="#1f5a8f", width=0.7, opacity=0.6)
            return s

        def chip():
            s = Svg(8, 8)
            s.polygon([(1, 3), (4, 0.6), (7.4, 3.4), (5, 7.4), (1.6, 6.2)], fill="#d8f6ff", stroke=ICE_LINE, width=0.7)
            return s

        def streak():
            s = Svg(10, 40)
            s.path("M3.6 40 L5 0 L6.4 40 Z", fill=s.linear(0, 0, 0, 40, [(0, "#ffffff", 0), (1, "#ffffff", 0.9)]))
            return s

        def glint():
            s = Svg(12, 12)
            s.polygon(star_points(6, 6, 5.8, 1.2, 4), fill="#ffffff")
            return s

        return {"body": (body, (41, 95)), "eyes_sleep": (lambda: eyes("sleep"), (20, 8)), "eyes_open": (lambda: eyes("open"), (20, 8)),
                "eyes_daze": (lambda: eyes("daze"), (20, 8)), "crack": (crack, (20, 0)), "chip": (chip, (4, 4)), "streak": (streak, (5, 40)),
                "glint": (glint, (6, 6))}

    def commands(self, e, t):
        root = _root(self, e)
        state = e.anim if e.alive else "rest"
        out: list[DrawCommand] = []
        jitter = math.sin(t * 70) * 1.8 if state == "shake" else 0.0
        sy = 1.0
        if state == "fall":
            sy = 1.05
        elif state == "rest":
            sy = 1 - 0.08 * max(0.0, 1 - e.state_time / 0.12)
        body = Xf(root.x + jitter, root.y, root.angle, root.sx * (2 - sy), root.sy * sy)
        if state == "fall":
            for j, sx in enumerate((-30, -10, 12, 30)):
                out.append(self.cmd("streak", body.child(sx, -96 + (j % 2) * 6), alpha=0.75))
        out.append(self.cmd("body", body))
        eyes = {"wait": "eyes_sleep", "rise": "eyes_sleep", "rest": "eyes_daze"}.get(state, "eyes_open")
        out.append(self.cmd(eyes, body.child(0, -60)))
        if state in ("rest", "rise"):
            fade = 1.0 if state == "rest" else max(0.0, 1 - e.state_time / 0.8)
            out.append(self.cmd("crack", body.child(-6, -56), alpha=fade))
        if state == "wait":
            k = (t * 0.35 + e.origin_x * 0.01) % 1
            if k < 0.25:
                out.append(self.cmd("glint", body.child(-14 + k * 40, -64 + k * 150), scale=0.6 + 1.2 * math.sin(k / 0.25 * math.pi)))
        elif state == "shake":
            for j in range(3):
                k = (e.state_time * 2.2 + j * 0.33) % 1
                out.append(self.cmd("chip", root.child(-30 + j * 30 + math.sin(j * 4) * 6, -92 + k * 50, k * 300), alpha=1 - k))
        elif state == "rest" and e.state_time < 0.6:
            k = e.state_time / 0.6
            for j, dx in enumerate((-1, 1, -0.6, 0.6)):
                out.append(self.cmd("chip", root.child(dx * (8 + 40 * k), -4 - 30 * k + 60 * k * k * (0.6 + j * 0.2), k * 500 * dx),
                                    alpha=1 - k))
        return _flash(e, t, out)
