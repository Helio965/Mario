"""Morsa Gelomar, boss of the Montanhas Geladas (original design).

A heavy blue-grey walrus with ivory tusks and a crown-like helmet of
spiked ice.  The helmet is the readable state: intact (spikes = do not
stomp), askew with stars (dazed after a wall crash) or cracked into shards
(stunned after a kicked crystal shell or three fireballs).
"""

from __future__ import annotations

import math

from ..rig import Xf
from ..svg import Svg, blob, smooth_closed, smooth_open, star_points
from .base import INK, CreatureRig, register

HIDE, HIDE_D, HIDE_L = "#7d8fae", "#3e4c6a", "#b7c6dc"
ICE, ICE_D, ICE_L = "#9fe2ff", "#3a8fc4", "#eafaff"
IVORY = "#fff6e2"


@register("ice_walrus")
class IceWalrus(CreatureRig):
    du = 0.6

    def parts(self):
        def body():
            s = Svg(200, 130)
            s.path(blob(100, 72, 94, 56, 0.035, seed=11, squash_top=1.05),
                   fill=s.radial(74, 42, 130, [(0, HIDE_L), (0.45, HIDE), (1, HIDE_D)]), stroke=INK, width=2.6)
            # wrinkles and belly sheen
            for k in range(4):
                y = 60 + k * 13
                s.path(smooth_open([(36 + k * 6, y), (70, y - 6), (104, y - 2)]), stroke=HIDE_D, width=1.6, opacity=0.55)
            s.path(blob(118, 98, 54, 22, 0.05, seed=4), fill=HIDE_L, opacity=0.45)
            s.ellipse(70, 38, 26, 9, fill="#ffffff", opacity=0.25)
            for x, y in ((48, 84), (62, 96), (150, 70), (138, 54)):
                s.circle(x, y, 2.2, fill=HIDE_D, opacity=0.5)
            return s

        def head(open_mouth: bool):
            def build():
                s = Svg(120, 110)
                s.path(blob(56, 52, 46, 40, 0.03, seed=7), fill=s.radial(46, 36, 60, [(0, HIDE_L), (0.6, HIDE), (1, HIDE_D)]),
                       stroke=INK, width=2.4)
                # muzzle pads
                for dx in (-14, 14):
                    s.ellipse(70 + dx, 70, 18, 14, fill=s.radial(66 + dx, 64, 20, [(0, "#d6dfec"), (1, "#8e9ebb")]),
                              stroke=INK, width=1.6)
                    for k in range(3):
                        s.circle(70 + dx + (k - 1) * 6, 70 + (k % 2) * 4, 1.4, fill=HIDE_D)
                # whiskers
                for k in range(3):
                    s.path(smooth_open([(88, 66 + k * 5), (104, 62 + k * 7), (116, 64 + k * 9)]), stroke="#e8eef6", width=1.2)
                if open_mouth:
                    s.path(blob(70, 88, 14, 9, 0.05, seed=2), fill="#5a2034", stroke=INK, width=1.6)
                # tusks
                for dx in (-9, 9):
                    s.path(smooth_closed([(70 + dx - 4, 80), (70 + dx + 4, 80), (70 + dx + 2, 104), (70 + dx - 1, 108)], 0.4),
                           fill=s.linear(0, 80, 0, 108, [(0, IVORY), (1, "#d9c9a4")]), stroke=INK, width=1.4)
                # eye and brow
                s.ellipse(60, 40, 7, 8, fill="#1c2236")
                s.circle(62, 37, 2.4, fill="#ffffff")
                s.path("M48 28 Q60 22 72 30", stroke=INK, width=3.0)
                return s
            return build

        def helmet(cracked: bool):
            def build():
                s = Svg(110, 80)
                band = [(10, 66), (100, 66), (96, 46), (14, 46)]
                s.path(smooth_closed(band, 0.2), fill=s.linear(0, 46, 0, 70, [(0, ICE_L), (0.5, ICE), (1, ICE_D)]),
                       stroke="#1f4e6e", width=2.0)
                spikes = [(18, 46, 28, 8), (40, 46, 50, 2), (62, 46, 72, 6), (84, 46, 92, 14)] if not cracked else \
                         [(22, 46, 30, 30), (58, 46, 66, 24)]
                for x0, y0, tip_x, tip_y in spikes:
                    s.polygon([(x0, y0), (x0 + 20, y0), (tip_x, tip_y)],
                              fill=s.linear(x0, y0, x0 + 20, tip_y, [(0, ICE_L), (0.5, ICE), (1, ICE_D)]),
                              stroke="#1f4e6e", width=1.6)
                    s.line(x0 + 7, y0 - 4, tip_x - 1, tip_y + 8, "#ffffff", 1.4, 0.8)
                if cracked:
                    for path in ("M20 50 L34 60 L30 66", "M54 48 L62 58 L76 56 L84 66", "M90 50 L82 58"):
                        s.path(path, stroke="#163a52", width=2.0)
                s.ellipse(40, 54, 18, 4, fill="#ffffff", opacity=0.5)
                return s
            return build

        def flipper():
            s = Svg(70, 40)
            s.path(smooth_closed([(4, 10), (40, 4), (66, 18), (58, 34), (30, 30), (6, 22)], 0.5),
                   fill=s.linear(0, 4, 0, 34, [(0, HIDE), (1, HIDE_D)]), stroke=INK, width=2.0)
            for k in range(3):
                s.line(44 + k * 6, 16, 54 + k * 5, 30, HIDE_D, 1.4, 0.7)
            return s

        def tail():
            s = Svg(60, 50)
            s.path(smooth_closed([(50, 30), (22, 8), (6, 14), (16, 30), (4, 44), (24, 44)], 0.45),
                   fill=s.linear(0, 8, 0, 44, [(0, HIDE), (1, HIDE_D)]), stroke=INK, width=2.0)
            return s

        def shard():
            s = Svg(24, 30)
            s.polygon([(4, 28), (20, 26), (12, 2)], fill=s.linear(4, 2, 20, 28, [(0, ICE_L), (1, ICE)]), stroke="#1f4e6e", width=1.2)
            return s

        def spray():
            s = Svg(60, 40)
            for k in range(6):
                s.path(blob(10 + k * 8, 30 - (k % 3) * 8, 7, 6, 0.25, seed=k + 20), fill="#f4fbff", opacity=0.85)
            return s

        def star():
            s = Svg(16, 16)
            s.polygon(star_points(8, 8, 7.5, 3.2, 5), fill="#ffe27a", stroke=INK, width=1.0)
            return s

        def wave():
            s = Svg(160, 30)
            s.path("M4 26 Q40 0 80 18 Q120 0 156 26", fill="none", stroke="#e6f6ff", width=4.0, opacity=0.8)
            return s

        return {
            "body": (body, (100, 126)),
            "head": (head(False), (30, 96)),
            "head_roar": (head(True), (30, 96)),
            "helmet": (helmet(False), (55, 64)),
            "helmet_cracked": (helmet(True), (55, 64)),
            "flipper": (flipper, (8, 14)),
            "tail": (tail, (50, 30)),
            "shard": (shard, (12, 16)),
            "spray": (spray, (30, 38)),
            "star": (star, (8, 8)),
            "wave": (wave, (80, 26)),
        }

    def commands(self, e, t):
        state = e.anim
        root = Xf()
        if not e.alive:
            return [self.cmd(name, self.defeat_xf(e, root).child(*xy))
                    for name, xy in (("tail", (-52, -26)), ("body", (0, 0)), ("head", (52, -44)))]
        out = []
        breathe = math.sin(t * 2.6)
        rise = 0.0
        sy = 1.0 + 0.02 * breathe
        lean = 0.0
        head_angle = 0.0
        flip_angle = 10 + 6 * breathe
        roar = False
        helmet = "helmet"
        helmet_dx, helmet_angle = 0.0, 0.0
        if state == "intro":
            k = min(1.0, e.state_time / 0.6)
            rise, head_angle, roar = 10 * k, -18 * k, e.state_time > 0.4
            flip_angle = -30 * k
        elif state == "flap":
            flip_angle = -40 + 50 * abs(math.sin(t * 22))
            rise = 4 * abs(math.sin(t * 22))
        elif state == "slide":
            sy, lean, head_angle, flip_angle = 0.78, 6, 10, 160
        elif state == "dazed":
            sy, head_angle = 0.94, 12 + 6 * math.sin(t * 6)
            helmet_dx, helmet_angle = -10, -24
        elif state == "rear":
            k = min(1.0, e.state_time / 0.35)
            rise, sy, lean, head_angle, roar = 22 * k, 1.0 + 0.12 * k, -14 * k, -22 * k, True
            flip_angle = -50 * k
        elif state == "slam":
            k = max(0.0, 1.0 - e.state_time / 0.3)
            sy, lean, head_angle = 0.86 + 0.14 * (1 - k), 10 * k, 18 * k
        elif state == "stunned":
            sy, head_angle = 0.92, 16
            helmet = "helmet_cracked"
            helmet_dx, helmet_angle = -4, -8
        elif state == "hurt":
            sy, head_angle, roar = 0.9, -10, True
        body = Xf(0.0, -rise, lean, 1.0, sy)
        out.append(self.cmd("tail", body.child(-86, -30, 6 * math.sin(t * 3))))
        out.append(self.cmd("flipper", body.child(-30, -22, 180 - flip_angle)))
        out.append(self.cmd("body", body))
        head = body.child(64, -54, head_angle)
        out.append(self.cmd("head_roar" if roar else "head", head))
        out.append(self.cmd(helmet, head.child(28 + helmet_dx, -78, helmet_angle)))
        out.append(self.cmd("flipper", body.child(44, -22, flip_angle)))
        if state == "slide":
            out.append(self.cmd("spray", root.child(100, -4)))
            out.append(self.cmd("wave", Xf(-40.0, -6.0, 0.0, 0.8, 0.6)))
        if state == "slam" and e.state_time < 0.5:
            spread = 1.0 + e.state_time * 3
            out.append(self.cmd("wave", Xf(0.0, -4.0, 0.0, spread, 1.0)))
        if state == "stunned":
            for k in range(3):
                a = t * 3 + k * 2.1
                out.append(self.cmd("shard", head.child(28 + math.cos(a) * 46, -96 + math.sin(a) * 10, (t * 200 + k * 90) % 360)))
        if state == "dazed" or state == "stunned":
            for k in range(3):
                a = t * 5 + k * 2.1
                out.append(self.cmd("star", head.child(30 + math.cos(a) * 38, -110 + math.sin(a) * 8)))
        if e.hit_timer > 0 and int(t * 20) % 2 == 0:
            for c in out:
                c.tint = (255, 170, 170)
        return out
