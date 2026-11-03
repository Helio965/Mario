"""Reino Verde creatures: Bolota, Caramujo, Besouro(-Asa), Flor-Mordedora,
Ouriço-Espinho and the Javali Espinheiro boss."""

from __future__ import annotations

import math

from ..rig import DrawCommand, Xf
from ..svg import Svg, blob, rounded_rect_path, shade, smooth_closed, smooth_open, star_points
from .base import INK, CreatureRig, eye_svg, pupil_svg, register


def _foot(color: str) -> Svg:
    s = Svg(14, 9)
    s.path(blob(7, 5, 6, 3.8, 0.05, seed=2, squash_top=1.3), fill=s.linear(0, 1, 0, 9, [(0, shade(color, 0.25)), (1, shade(color, -0.25))]),
           stroke=INK, width=1.2)
    return s


@register("acorn")
class Acorn(CreatureRig):
    du = 0.5

    def parts(self):
        def body():
            s = Svg(56, 46)
            s.path(blob(28, 26, 24, 19, 0.03, seed=5, squash_top=0.9),
                   fill=s.radial(20, 18, 34, [(0, "#f2c98a"), (0.5, "#d49556"), (1, "#9a5c30")]), stroke=INK, width=1.8)
            s.path(smooth_open([(10, 34), (28, 42), (46, 34)]), stroke="#8a4e26", width=2.0, opacity=0.5)
            s.ellipse(17, 22, 5, 3, fill="#ffffff", opacity=0.35)
            return s

        def cap():
            s = Svg(62, 34)
            s.path(blob(31, 22, 29, 12, 0.04, seed=3, squash_top=1.25), fill=s.linear(0, 8, 0, 34, [(0, "#a8744a"), (1, "#6a4426")]),
                   stroke=INK, width=1.8)
            for i in range(-3, 4):
                s.path(smooth_open([(31 + i * 7.5 - 4, 14), (31 + i * 7.5 + 2, 24), (31 + i * 7.5 + 6, 31)]), stroke="#4e2e18", width=1.2, opacity=0.6)
            s.path(smooth_open([(8, 22), (31, 30), (54, 22)]), stroke="#d8a878", width=1.6, opacity=0.6)
            s.path("M31 10 Q30 2 35 0", stroke="#5a3a20", width=3.2)
            return s

        def brow():
            s = Svg(12, 5)
            s.path("M1 1.5 L11 4", stroke=INK, width=2.4)
            return s

        return {
            "body": (body, (28, 44)), "cap": (cap, (31, 30)), "eye": (lambda: eye_svg(12), (6, 6)),
            "pupil": (lambda: pupil_svg(6), (3, 3)), "brow": (brow, (6, 2.5)), "foot": (lambda: _foot("#5a3420"), (7, 8)),
        }

    def commands(self, e, t):
        root = Xf()
        if not e.alive:
            root = self.defeat_xf(e, root)
        walk = e.anim == "walk" and e.alive
        ph = t * 9.0
        bob = -abs(math.sin(ph)) * 2.4 if walk else 0.0
        alert = e.anim == "alert"
        hop = -6 * math.sin(min(1.0, e.state_time / 0.45) * math.pi) if alert else 0.0
        tilt = math.sin(ph) * 4 if walk else 0.0
        out = [
            self.cmd("foot", root.child(-9 + (math.sin(ph) * 4 if walk else 0), 0)),
            self.cmd("foot", root.child(10 - (math.sin(ph) * 4 if walk else 0), 0)),
        ]
        body = root.child(0, -4 + bob + hop, tilt)
        out.append(self.cmd("body", body))
        out.append(self.cmd("cap", body.child(0, -30, -tilt * 0.4)))
        if e.alive:
            look = 1.6 if e.facing > 0 or True else -1.6
            closed = self.blink(t, e.origin_x)
            for ex in (4.0, 15.0):
                eye = body.child(ex, -22)
                out.append(self.cmd("eye", eye, scale=1.0 if not closed else 0.0001))
                out.append(self.cmd("pupil", eye.child(look + (1.5 if alert else 0), 0.5 if not alert else -0.8), scale=1.35 if alert else 1.0))
            out.append(self.cmd("brow", body.child(4, -29, 8 if not alert else -12)))
            out.append(self.cmd("brow", body.child(15, -29.5, 168 if not alert else 192), scale=1.0))
        return out


@register("snail")
class Snail(CreatureRig):
    du = 0.5

    def parts(self):
        def soft():
            s = Svg(66, 28)
            s.path(smooth_closed([(2, 24), (14, 12), (40, 10), (60, 14), (64, 24), (36, 27)], 0.7),
                   fill=s.linear(0, 8, 0, 28, [(0, "#f6e7b0"), (1, "#c9b070")]), stroke=INK, width=1.6)
            return s

        def head():
            s = Svg(24, 26)
            s.path(blob(12, 16, 10, 9, 0.04, seed=1), fill=s.radial(9, 12, 13, [(0, "#fff4c8"), (1, "#d6be7a")]), stroke=INK, width=1.5)
            s.path("M8 21 Q12 24 16 21", stroke=INK, width=1.3)
            return s

        def stalk():
            s = Svg(10, 20)
            s.path("M5 19 Q4 10 5 5", stroke="#c9b070", width=3.2)
            s.path("M5 19 Q4 10 5 5", stroke="#f6e7b0", width=1.6)
            s.circle(5, 5, 4.2, fill="#ffffff", stroke=INK, width=1.1)
            s.circle(6, 5, 2.1, fill="#2a2238")
            return s

        def shell():
            s = Svg(50, 50)
            s.circle(25, 25, 23, fill=s.radial(18, 15, 32, [(0, "#ffe2b0"), (0.5, "#f09a52"), (1, "#a8502a")]), stroke=INK, width=1.8)
            pts = []
            for i in range(60):
                a = i * 0.3
                r = 2 + i * 0.32
                pts.append((25 + math.cos(a) * r, 25 + math.sin(a) * r))
            s.path(smooth_open(pts), stroke="#8a3e20", width=2.0, opacity=0.8)
            s.ellipse(17, 14, 6, 3.5, fill="#ffffff", opacity=0.45)
            return s

        return {"soft": (soft, (33, 26)), "head": (head, (12, 24)), "stalk": (stalk, (5, 19)), "shell": (shell, (25, 48))}

    def commands(self, e, t):
        root = Xf()
        if not e.alive:
            root = self.defeat_xf(e, root)
        state = e.anim
        out = []
        if state in ("shell", "slide", "wake") and e.alive or (not e.alive and e.state in ("shell", "slide")):
            spin = (t * 900 * e.facing) % 360 if state == "slide" else 0.0
            shake = math.sin(t * 40) * 3 if state == "wake" else 0.0
            shell = root.child(0, -2, spin + shake)
            if state == "slide":
                shell = root.child(0, -26).child(0, 24, spin)  # rotate around centre
                shell = Xf(shell.x, shell.y, spin, shell.sx, shell.sy)
                out.append(self.cmd("shell", Xf(root.x, root.y - 2, 0, root.sx, root.sy), alpha=0.0))
            out.append(self.cmd("shell", shell))
            if state == "wake":
                out.append(self.cmd("stalk", root.child(14, -10, 20 + shake * 3), scale=0.7))
            return out[-2:] if state == "wake" else [out[-1]]
        ph = t * 5
        stretch = 1 + 0.08 * math.sin(ph)
        out.append(self.cmd("soft", Xf(root.x, root.y, root.angle, root.sx * stretch, root.sy)))
        head = root.child(26 * stretch, -4)
        out.append(self.cmd("stalk", head.child(-3, -14, -12 + math.sin(t * 3) * 8)))
        out.append(self.cmd("stalk", head.child(3, -15, 8 + math.sin(t * 3 + 1) * 8)))
        out.append(self.cmd("head", head))
        out.append(self.cmd("shell", root.child(-6, -6, math.sin(ph) * 3)))
        return out


@register("beetle")
class Beetle(CreatureRig):
    du = 0.5
    winged = False

    def parts(self):
        def body():
            s = Svg(60, 44)
            s.path(blob(30, 26, 26, 17, 0.03, seed=7, squash_top=1.05),
                   fill=s.radial(22, 16, 36, [(0, "#9ff0e0"), (0.4, "#2f9ab0"), (1, "#163a6a")]), stroke=INK, width=1.8)
            s.path("M30 10 L30 42", stroke="#0e2a4a", width=1.6, opacity=0.7)
            s.ellipse(20, 18, 7, 3.6, fill="#ffffff", opacity=0.5)
            return s

        def head():
            s = Svg(26, 24)
            s.path(blob(13, 14, 11, 9.5, 0.03, seed=2), fill=s.radial(10, 10, 14, [(0, "#4a5a7a"), (1, "#1e2440")]), stroke=INK, width=1.5)
            s.path("M8 6 Q4 0 0 1 M16 6 Q19 0 24 1", stroke=INK, width=1.4)
            s.circle(9, 12, 3.6, fill="#ffffff")
            s.circle(17, 12, 3.6, fill="#ffffff")
            s.circle(10, 12.5, 1.8, fill="#2a2238")
            s.circle(18, 12.5, 1.8, fill="#2a2238")
            return s

        def wing():
            s = Svg(40, 22)
            s.path(smooth_closed([(2, 18), (14, 4), (36, 2), (34, 12), (12, 20)], 0.7),
                   fill=s.linear(0, 2, 0, 20, [(0, "#ffffff", 0.75), (1, "#bfe8ff", 0.45)]), stroke="#6a8aa8", width=1.0)
            s.path("M4 17 L30 5 M10 18 L34 10", stroke="#8ab0d0", width=0.8, opacity=0.7)
            return s

        def leg():
            s = Svg(8, 14)
            s.path("M4 1 Q6 7 3 13", stroke=INK, width=2.4)
            return s

        return {"body": (body, (30, 42)), "head": (head, (4, 18)), "wing": (wing, (4, 18)), "leg": (leg, (4, 1))}

    def commands(self, e, t):
        root = Xf()
        if not e.alive:
            root = self.defeat_xf(e, root)
        flying = e.anim == "fly" or self.species == "besouro_alado"
        ph = t * (14 if not flying else 3)
        out = []
        if flying:
            flap = abs(math.sin(t * 26))
            out.append(self.cmd("wing", Xf(*_p(root.child(-6, -30)), -20 - 30 * flap, 1, 0.4 + 0.6 * flap), alpha=0.85))
        for i, lx in enumerate((-12, -2, 8)):
            swing = math.sin(ph + i * 2.1) * (25 if not flying else 8)
            out.append(self.cmd("leg", root.child(lx, -8, swing)))
        bob = -abs(math.sin(ph)) * 1.6 if not flying else 0.0
        body = root.child(0, -4 + bob)
        out.append(self.cmd("body", body))
        out.append(self.cmd("head", body.child(20, -22, math.sin(t * 6) * 4)))
        if flying:
            flap = abs(math.sin(t * 26 + 1.2))
            out.append(self.cmd("wing", Xf(*_p(root.child(-2, -32)), -10 - 34 * flap, 1, 0.4 + 0.6 * flap), alpha=0.9))
        return out


def _p(xf: Xf) -> tuple[float, float]:
    return xf.x, xf.y


@register("beetle_winged")
class WingedBeetle(Beetle):
    pass


@register("biter_flower")
class BiterFlower(CreatureRig):
    du = 0.5

    def parts(self):
        def mound():
            s = Svg(76, 26)
            s.path(blob(38, 20, 34, 11, 0.06, seed=4, squash_top=0.8), fill=s.linear(0, 6, 0, 26, [(0, "#a87a4a"), (1, "#5e3c24")]),
                   stroke=INK, width=1.6)
            s.ellipse(38, 17, 18, 5, fill="#2a1a12")
            for x in (12, 64):
                s.path(blob(x, 14, 7, 4, 0.1, seed=x), fill="#6abf52", stroke="#2f7a36", width=0.8)
            return s

        def stem():
            s = Svg(16, 60)
            s.path("M8 60 Q4 40 8 22 Q11 10 8 2", stroke="#2f7a36", width=6.2)
            s.path("M8 60 Q4 40 8 22 Q11 10 8 2", stroke="#6fca5a", width=3.4)
            return s

        def leaf():
            s = Svg(28, 14)
            s.path(smooth_closed([(1, 8), (12, 1.5), (27, 5), (14, 12.5)]), fill=s.linear(0, 1, 0, 13, [(0, "#9be36a"), (1, "#3c9a46")]),
                   stroke="#24622d", width=1.0)
            return s

        def jaw(top: bool):
            s = Svg(46, 26)
            if top:
                s.path(smooth_closed([(2, 24), (6, 8), (20, 1), (36, 4), (44, 16), (40, 24)], 0.7),
                       fill=s.radial(18, 8, 30, [(0, "#ffb3c8"), (0.5, "#e8476a"), (1, "#9a1e3e")]), stroke=INK, width=1.6)
                for x in range(9, 40, 7):
                    s.polygon([(x, 23.5), (x + 3, 30), (x + 6, 23.5)], fill="#fff7e6", stroke=INK, width=0.7)
                for (cx, cy) in ((14, 10), (26, 7), (34, 12)):
                    s.circle(cx, cy, 2.4, fill="#ffe2ec", opacity=0.9)
                s.circle(30, 15, 5, fill="#ffffff", stroke=INK, width=1.0)
                s.circle(31.5, 15.5, 2.4, fill="#2a2238")
            else:
                s.path(smooth_closed([(2, 2), (40, 2), (44, 10), (30, 22), (10, 22), (2, 12)], 0.7),
                       fill=s.radial(18, 10, 28, [(0, "#e8476a"), (1, "#7a1a34")]), stroke=INK, width=1.6)
                for x in range(10, 38, 7):
                    s.polygon([(x, 2.5), (x + 3, -3), (x + 6, 2.5)], fill="#fff7e6", stroke=INK, width=0.7)
            return s

        return {
            "mound": (mound, (38, 25)), "stem": (stem, (8, 60)), "leaf": (leaf, (2, 8)),
            "jaw_top": (lambda: jaw(True), (6, 24)), "jaw_bottom": (lambda: jaw(False), (6, 2)),
        }

    def commands(self, e, t):
        base = Xf()
        base_y = e.memory.get("base_y", e.y)
        rise = 1.0 - max(0.0, min(1.0, (e.y - base_y) / max(1.0, e.h)))
        out = []
        if e.alive or e.defeated > 0:
            k = rise if e.alive else max(0.0, e.defeated / 0.6)
            stem_len = 0.25 + 0.75 * k
            sway = math.sin(t * 2.4) * 6 * k
            stem = Xf(base.x, base.y - 8, sway, 1, stem_len)
            if k > 0.05:
                out.append(self.cmd("leaf", stem.child(0, -14 * stem_len, -160)))
                out.append(self.cmd("leaf", stem.child(0, -20 * stem_len, -20)))
                out.append(self.cmd("stem", stem))
                head = Xf(base.x + math.sin(math.radians(sway)) * 55 * stem_len, base.y - 8 - 58 * stem_len, sway * 0.5)
                opening = 18 + 22 * abs(math.sin(t * 7)) if e.anim == "bite" else (10 if e.anim == "out" else 4)
                if not e.alive:
                    opening = 30
                out.append(self.cmd("jaw_bottom", head.child(-14, 2, opening * 0.5)))
                out.append(self.cmd("jaw_top", head.child(-14, 2, -opening)))
        shake = math.sin(t * 50) * 1.5 if e.alive and e.anim == "hidden" and e.state_time > 1.2 else 0.0
        out.append(self.cmd("mound", base.child(shake, 0)))
        return out


@register("hedgehog")
class Hedgehog(CreatureRig):
    du = 0.5

    def parts(self):
        def body():
            s = Svg(70, 52)
            for i in range(11):
                a = math.radians(-170 + i * 15)
                x0, y0 = 30 + math.cos(a) * 20, 32 + math.sin(a) * 18
                s.polygon([(x0 - 4, y0), (30 + math.cos(a) * 36, 32 + math.sin(a) * 32), (x0 + 4, y0 + 2)],
                          fill=s.linear(x0, y0, 30 + math.cos(a) * 36, 32 + math.sin(a) * 32, [(0, "#a8702a"), (1, "#ffe08a")]),
                          stroke=INK, width=1.0)
            s.path(blob(32, 34, 24, 16, 0.04, seed=8), fill=s.radial(26, 26, 30, [(0, "#d8a070"), (1, "#8a5030")]), stroke=INK, width=1.6)
            s.path(blob(50, 38, 13, 11, 0.03, seed=2), fill=s.radial(48, 34, 14, [(0, "#fff0d6"), (1, "#e8c49a")]), stroke=INK, width=1.4)
            s.circle(61, 38, 2.6, fill="#2a2238")
            s.circle(51, 33, 3.2, fill="#2a2238")
            s.circle(52, 32, 1.1, fill="#ffffff")
            s.path("M50 44 Q55 46 58 43", stroke=INK, width=1.2)
            return s

        return {"body": (body, (35, 50)), "foot": (lambda: _foot("#6a3a22"), (7, 8))}

    def commands(self, e, t):
        root = Xf()
        if not e.alive:
            root = self.defeat_xf(e, root)
        ph = t * 8
        walking = e.anim == "walk" and e.alive
        out = [self.cmd("foot", root.child(-12 + (math.sin(ph) * 3 if walking else 0), 0), scale=0.8),
               self.cmd("foot", root.child(12 - (math.sin(ph) * 3 if walking else 0), 0), scale=0.8)]
        bristle = 1.0 + (0.12 * abs(math.sin(e.state_time * 12)) if e.anim == "alert" else 0.0)
        out.append(self.cmd("body", Xf(root.x, root.y - 3 - abs(math.sin(ph)) * 1.4 * walking, root.angle, root.sx * bristle, root.sy * bristle)))
        return out


@register("boar")
class Boar(CreatureRig):
    du = 0.55

    def parts(self):
        def body():
            s = Svg(170, 120)
            # bramble mane with thorns
            for i in range(9):
                cx = 40 + i * 11
                cy = 30 + abs(i - 4) * 4
                s.path(blob(cx, cy, 14, 11, 0.15, seed=i), fill=s.radial(cx - 4, cy - 4, 16, [(0, "#6a9a4a"), (1, "#2f5a2a")]), stroke=INK, width=1.2)
                s.polygon([(cx - 3, cy - 8), (cx + 1, cy - 20), (cx + 4, cy - 8)], fill="#e8d8a8", stroke=INK, width=0.9)
            s.path(blob(80, 66, 66, 40, 0.04, seed=3, squash_top=0.9), fill=s.radial(64, 46, 90, [(0, "#a8704a"), (0.6, "#6a4026"), (1, "#3e2416")]),
                   stroke=INK, width=2.2)
            s.path(smooth_open([(30, 84), (80, 100), (130, 86)]), stroke="#2e1a10", width=3, opacity=0.4)
            return s

        def head():
            s = Svg(80, 70)
            s.path(blob(36, 36, 32, 27, 0.04, seed=6), fill=s.radial(28, 26, 44, [(0, "#b8805a"), (1, "#5a341e")]), stroke=INK, width=2.0)
            s.path(blob(60, 44, 15, 12, 0.03, seed=2), fill=s.radial(58, 40, 16, [(0, "#f2b0a0"), (1, "#c06a5a")]), stroke=INK, width=1.6)
            s.ellipse(56, 44, 2.6, 3.4, fill="#3a1a1a")
            s.ellipse(65, 44, 2.6, 3.4, fill="#3a1a1a")
            s.path("M48 54 Q42 66 50 70", stroke="#fff6e0", width=4.6)
            s.path("M48 54 Q42 66 50 70", stroke=INK, width=0.8, opacity=0.6)
            s.path(smooth_closed([(16, 6), (24, -2), (30, 12)]), fill="#5a341e", stroke=INK, width=1.4)
            return s

        def eye_open():
            s = Svg(18, 14)
            s.ellipse(9, 8, 7.5, 5.6, fill="#fff4cc", stroke=INK, width=1.3)
            s.circle(11, 8.4, 3.2, fill="#c8281e")
            s.circle(11.5, 8.4, 1.4, fill="#1a0a0a")
            s.path("M1 3 L17 6", stroke=INK, width=3.0)
            return s

        def eye_daze():
            s = Svg(18, 14)
            s.ellipse(9, 8, 7.5, 5.6, fill="#fff4cc", stroke=INK, width=1.3)
            s.path("M9 8 m-4 0 a4 4 0 1 0 8 0 a3 3 0 1 0 -6 0 a1.6 1.6 0 1 0 3.2 0", stroke=INK, width=1.2)
            return s

        def leg():
            s = Svg(22, 40)
            s.path(rounded_rect_path(4, 0, 14, 32, 6), fill=s.linear(4, 0, 18, 0, [(0, "#8a5a3a"), (1, "#4a2e1c")]), stroke=INK, width=1.6)
            s.path(blob(11, 34, 9, 6, 0.02, seed=1), fill="#2e1a12", stroke=INK, width=1.4)
            return s

        def star():
            s = Svg(14, 14)
            s.polygon(star_points(7, 7, 6.5, 2.8, 5), fill="#ffe27a", stroke=INK, width=0.9)
            return s

        return {"body": (body, (80, 110)), "head": (head, (10, 50)), "eye_open": (eye_open, (9, 8)), "eye_daze": (eye_daze, (9, 8)),
                "leg": (leg, (11, 2)), "star": (star, (7, 7))}

    def commands(self, e, t):
        root = Xf()
        if not e.alive:
            root = Xf(0, 0, 180.0 * min(1.0, (1.2 - e.defeated) / 0.5), 1, 1)
        state = e.anim
        speed = {"charge": 22.0, "stalk": 9.0}.get(state, 0.0)
        ph = t * speed
        out = []
        lean = {"charge": 10.0, "telegraph": -6.0 + math.sin(t * 18) * 3, "stunned": -4.0, "hurt": -14.0}.get(state, 0.0)
        for i, lx in enumerate((-46, -24, 22, 44)):
            swing = math.sin(ph + i * math.pi / 2) * (30 if state == "charge" else 14 if state == "stalk" else 0)
            if state == "telegraph" and i == 3:
                swing = -30 + 40 * abs(math.sin(t * 14))
            out.append(self.cmd("leg", root.child(lx, -34, swing)))
        body = root.child(0, -8 - abs(math.sin(ph)) * (3 if speed else 0), lean)
        out.append(self.cmd("body", body))
        head = body.child(52, -66, lean * 0.5 + (16 if state == "charge" else 0))
        out.append(self.cmd("head", head))
        eye = "eye_daze" if state in ("stunned",) or not e.alive else "eye_open"
        out.append(self.cmd(eye, head.child(26, -26)))
        if state == "stunned":
            for k in range(3):
                a = t * 5 + k * 2.1
                out.append(self.cmd("star", head.child(22 + math.cos(a) * 26, -44 + math.sin(a) * 8)))
        if e.hit_timer > 0 and int(t * 20) % 2 == 0:
            for c in out:
                c.tint = (255, 150, 150)
        return out
