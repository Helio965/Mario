"""Escaravelho-Rei, boss of the Deserto Dourado."""

from __future__ import annotations

import math

from ..rig import Xf
from ..svg import Svg, blob, rounded_rect_path, shade, smooth_closed, smooth_open, star_points
from .base import INK, CreatureRig, register

GOLD, GOLD_D, TEAL = "#f2c14e", "#9a6a1c", "#2fb3a0"


@register("scarab_king")
class ScarabKing(CreatureRig):
    du = 0.55

    def parts(self):
        def shell():
            s = Svg(170, 110)
            s.path(blob(85, 62, 80, 46, 0.03, seed=5, squash_top=0.95),
                   fill=s.radial(62, 34, 110, [(0, "#fff0b0"), (0.35, GOLD), (0.8, GOLD_D), (1, "#5a3a10")]), stroke=INK, width=2.4)
            s.path("M85 18 L85 106", stroke="#5a3a10", width=2.4, opacity=0.8)
            for side in (-1, 1):
                pts = [(85 + side * 8, 30), (85 + side * 44, 26), (85 + side * 70, 48), (85 + side * 58, 82), (85 + side * 14, 92)]
                s.path(smooth_closed(pts, 0.6), fill=s.linear(85, 20, 85 + side * 70, 90, [(0, TEAL), (1, "#145a5a")]), opacity=0.55)
                for k in range(3):
                    s.path(smooth_open([(85 + side * 16, 40 + k * 16), (85 + side * 46, 36 + k * 18), (85 + side * 64, 50 + k * 14)]),
                           stroke="#fff3c0", width=1.6, opacity=0.6)
            s.polygon(star_points(85, 58, 14, 5, 8), fill="#fff3c0", stroke=INK, width=1.0, opacity=0.9)
            s.ellipse(56, 36, 18, 7, fill="#ffffff", opacity=0.35)
            return s

        def head():
            s = Svg(80, 70)
            s.path(blob(34, 44, 30, 22, 0.03, seed=2), fill=s.radial(28, 34, 36, [(0, "#4a5a7a"), (1, "#1a2032")]), stroke=INK, width=2.0)
            s.path(smooth_closed([(26, 26), (44, 0), (52, 4), (44, 28)], 0.6), fill=s.linear(30, 0, 50, 28, [(0, GOLD), (1, GOLD_D)]),
                   stroke=INK, width=1.6)
            for y, flip in ((58, 1), (60, -1)):
                s.path(f"M58 {y} q14 {-6 * flip} 20 {4 * flip}", stroke=INK, width=3.6)
            s.ellipse(48, 40, 7, 6, fill="#ffb84a", stroke=INK, width=1.2)
            s.circle(50, 40, 3, fill="#5a1a0a")
            return s

        def leg():
            s = Svg(14, 40)
            s.path("M7 2 L9 18 L4 36", stroke=INK, width=5.0)
            s.path("M7 2 L9 18 L4 36", stroke="#3a3048", width=3.0)
            return s

        def belly():
            s = Svg(160, 90)
            s.path(blob(80, 46, 74, 40, 0.03, seed=8), fill=s.radial(70, 36, 90, [(0, "#fff0d6"), (1, "#c9a87a")]), stroke=INK, width=2.2)
            for k in range(4):
                s.path(smooth_open([(30, 30 + k * 12), (80, 34 + k * 12), (130, 30 + k * 12)]), stroke="#8a6a44", width=1.6, opacity=0.7)
            return s

        def mound():
            s = Svg(140, 40)
            s.path(blob(70, 34, 66, 16, 0.08, seed=4, squash_top=1.2), fill=s.linear(0, 14, 0, 40, [(0, "#f6d58a"), (1, "#c08a4a")]),
                   stroke="#8a5a2a", width=1.6)
            for k in range(5):
                s.path(f"M{20 + k * 25} 28 q8 -8 16 0", stroke="#fff0c0", width=1.4, opacity=0.8)
            return s

        def ball():
            s = Svg(100, 100)
            s.circle(50, 50, 46, fill=s.radial(36, 34, 70, [(0, "#fff0b0"), (0.4, GOLD), (1, "#6a4410")]), stroke=INK, width=2.4)
            for a in range(0, 360, 45):
                r = math.radians(a)
                s.line(50 + math.cos(r) * 14, 50 + math.sin(r) * 14, 50 + math.cos(r) * 42, 50 + math.sin(r) * 42, "#5a3a10", 2.2, 0.7)
            s.polygon(star_points(50, 50, 12, 5, 8), fill="#fff3c0", stroke=INK, width=1.0)
            return s

        def spray():
            s = Svg(60, 80)
            for k in range(7):
                x = 30 + (k - 3) * 6
                s.path(blob(x, 70 - k * 9 % 50, 6, 9, 0.2, seed=k), fill="#f6d58a", opacity=0.75)
            return s

        def star():
            s = Svg(14, 14)
            s.polygon(star_points(7, 7, 6.5, 2.8, 5), fill="#ffe27a", stroke=INK, width=0.9)
            return s

        return {"shell": (shell, (85, 104)), "head": (head, (8, 46)), "leg": (leg, (7, 2)), "belly": (belly, (80, 86)),
                "mound": (mound, (70, 38)), "ball": (ball, (50, 50)), "spray": (spray, (30, 78)), "star": (star, (7, 7))}

    def commands(self, e, t):
        state = e.anim
        root = Xf()
        out = []
        if not e.alive:
            k = min(1.0, (1.2 - e.defeated) / 0.6)
            return [self.cmd("belly", Xf(0, -4, 0, 1 + 0.2 * k, 1 - 0.5 * k)), self.cmd("star", Xf(0, -70 + 10 * k))]
        if state in ("burrow", "telegraph", "intro") and state != "intro" or (state == "intro" and e.state_time < 0.6):
            shake = math.sin(t * 50) * (3 if state == "telegraph" else 1)
            out.append(self.cmd("mound", root.child(shake, 0)))
            if state == "telegraph":
                for k in range(3):
                    out.append(self.cmd("spray", root.child((k - 1) * 30, -10 - 20 * abs(math.sin(t * 9 + k)))))
            return out
        if state == "roll":
            return [self.cmd("ball", root.child(0, -50, (t * 720 * e.facing) % 360))]
        if state in ("dazed", "hurt"):
            for i, lx in enumerate((-50, -20, 20, 50)):
                out.append(self.cmd("leg", root.child(lx, -70, 180 + math.sin(t * 16 + i) * 30)))
            out.append(self.cmd("belly", root.child(0, -6)))
            for k in range(3):
                a = t * 5 + k * 2.1
                out.append(self.cmd("star", root.child(math.cos(a) * 40, -96 + math.sin(a) * 8)))
            return out
        rise = min(1.0, e.state_time / 0.6) if state == "intro" else 1.0
        walk = math.sin(t * 10)
        for i, lx in enumerate((-56, -30, -4, 22, 48)):
            out.append(self.cmd("leg", root.child(lx, -26 * rise, walk * 18 * (1 if i % 2 else -1))))
        body = root.child(0, -18 * rise - (6 if state == "erupt" else 0))
        out.append(self.cmd("shell", body))
        out.append(self.cmd("head", body.child(64, -40, -8 if state == "erupt" else 0)))
        if e.hit_timer > 0 and int(t * 20) % 2 == 0:
            for c in out:
                c.tint = (255, 160, 160)
        return out
