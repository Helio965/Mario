"""Costa dos Corais creatures.

* ``crab`` — Caranguejo-Pinça: a teal-blue fiddler crab with one huge golden
  claw. Walking, both claws are held low in front of the shell (its top is
  clear: stompable); on guard it hoists them over its shell, the golden pincer
  open and snapping. Before every guard the claws twitch upward (telegraph).
* ``leaping_fish`` — Peixe-Saltador: a slender striped flying fish; its
  wing-like pectoral fins lie folded while it swims and spread wide during
  the leap, the body pitching with its arc.
* ``puffer`` — Baiacu-Espinho: a cute spotted puffer that balloons into a
  round ball bristling with pale spines (they only show when it is spiky).
* ``jellyfish`` — Água-Viva Elétrica: a translucent bell whose top crackles
  with electricity (never stompable), frilly arms and tentacles trailing.
* ``moray`` — Moreia-da-Toca: a spotted green moray living in a coral-rock
  den that is part of the rig. Hidden, only its eyes glint in the crevice;
  before rising the den shakes and bubbles stream out (telegraph).
* ``octopus`` — Polvo-Tinteiro: a round coral-orange octopus with a spotted
  mantle that swims in pulsing jets and puffs ink while it chases.

Light comes from the upper left, as in the world art. Blue and green bodies
blink warm on a hit, warm bodies blink cool.
"""

from __future__ import annotations

import math

from ..rig import DrawCommand, Xf
from ..svg import Svg, blob, rounded_rect_path, smooth_closed, smooth_open, star_points
from .base import INK, CreatureRig, register

WARM_FLASH = (255, 150, 140)
COOL_FLASH = (150, 205, 255)


# --------------------------------------------------------------------------- shared helpers
def _root(rig: CreatureRig, e) -> Xf:
    return Xf() if e.alive else rig.defeat_xf(e, Xf())


def _spin(root: Xf, cx: float, cy: float, ox: float, oy: float, angle: float) -> Xf:
    """Transform that turns a part around its visual centre placed at (cx, cy);
    (ox, oy) is that centre's offset from the part's pivot, in du."""
    a = math.radians(angle)
    return root.child(cx - (ox * math.cos(a) - oy * math.sin(a)), cy - (ox * math.sin(a) + oy * math.cos(a)), angle)


def _flash(e, t: float, out: list[DrawCommand], tint: tuple[int, int, int]) -> list[DrawCommand]:
    if e.hit_timer > 0 and int(t * 20) % 2 == 0:
        for c in out:
            c.tint = tint
    return out


def _xy(xf: Xf) -> tuple[float, float]:
    return xf.x, xf.y


def _ease(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def _eye(size: float = 12.0, rim: str = INK) -> Svg:
    s = Svg(size, size)
    c = size / 2
    s.circle(c, c, c * 0.88, fill=s.radial(c * 0.8, c * 0.7, c * 1.1, [(0, "#ffffff"), (1, "#dce6ef")]), stroke=rim, width=size * 0.09)
    return s


def _pupil(size: float = 6.0, color: str = "#1a1630") -> Svg:
    s = Svg(size, size)
    c = size / 2
    s.circle(c, c, c * 0.92, fill=color)
    s.circle(c * 1.3, c * 0.68, c * 0.34, fill="#ffffff")
    return s


def _eye_x(size: float = 11.0) -> Svg:
    s = Svg(size, size)
    m, n = size * 0.18, size * 0.82
    s.path(f"M{m:.2f} {m:.2f} L{n:.2f} {n:.2f} M{n:.2f} {m:.2f} L{m:.2f} {n:.2f}", stroke=INK, width=size * 0.17)
    return s


def _eye_closed(size: float = 12.0) -> Svg:
    s = Svg(size, size * 0.6)
    s.path(f"M{size * 0.1:.2f} {size * 0.2:.2f} Q{size * 0.5:.2f} {size * 0.55:.2f} {size * 0.9:.2f} {size * 0.2:.2f}", stroke=INK, width=size * 0.14)
    return s


def _bubble(size: float = 8.0) -> Svg:
    s = Svg(size, size)
    c = size / 2
    s.circle(c, c, c * 0.86, fill="#dff8ff", stroke="#5ab8d8", width=size * 0.08, opacity=0.55)
    s.circle(c * 0.7, c * 0.65, c * 0.26, fill="#ffffff")
    return s


def _shared_parts() -> dict:
    return {"eye_x": (_eye_x, (5.5, 5.5)), "eye_closed": (_eye_closed, (6, 3.6)), "bubble": (_bubble, (4, 4))}


# =========================================================================== Caranguejo-Pinça
@register("crab")
class FiddlerCrab(CreatureRig):
    """Teal fiddler crab seen from the front, scuttling sideways; the huge golden
    claw leads. Claws low = safe top; claws hoisted over the shell = guard."""

    du = 0.45
    LEG = (37.0, 27.0)  # leg part: hip → tip vector (du)
    HIPS = ((12.0, -19.0, 0.62), (15.5, -20.0, 0.68), (19.0, -20.0, 0.73), (22.5, -19.0, 0.78))

    def parts(self):
        def carapace():
            s = Svg(66, 40)
            outline = [(5, 14), (11, 6), (22, 2.5), (33, 2), (44, 2.5), (55, 6), (61, 14), (59, 24), (52, 33), (40, 38), (26, 38), (14, 33), (7, 24)]
            s.path(smooth_closed(outline, 0.55), fill=s.radial(24, 12, 48, [(0, "#bff8f2"), (0.35, "#52c4d6"), (0.75, "#2a7fb2"), (1, "#1a4a7e")]),
                   stroke=INK, width=1.8)
            s.path(smooth_open([(10, 9), (22, 5), (33, 4.6), (44, 5), (56, 9)]), stroke="#e6fffb", width=1.6, opacity=0.85)
            for x, y, rr in ((16, 12, 1.6), (24, 9, 1.1), (42, 9, 1.3), (50, 13, 1.6), (12, 20, 1.0), (54, 21, 1.1), (30, 13, 0.9), (37, 15, 1.0)):
                s.circle(x, y, rr, fill="#dcfff8", opacity=0.6)
            s.path("M23 15 Q33 19 43 15 M33 19 L33 25", stroke="#1d5a86", width=1.1, opacity=0.5)
            s.path(smooth_open([(12, 29), (33, 36), (54, 29)]), stroke="#123a62", width=2.4, opacity=0.45)
            for x in (26.5, 33.5):
                s.path(rounded_rect_path(x, 26, 6, 8, 2.2), fill=s.linear(x, 0, x + 6, 0, [(0, "#5ab6cc"), (1, "#256e94")]), stroke=INK, width=0.8)
            s.path("M29 31 Q33 33 37 31", stroke=INK, width=1.0)
            return s

        def stalk(shut: bool):
            s = Svg(14, 30)
            s.path("M7 29 Q6 20 7 11", stroke=INK, width=4.4)
            s.path("M7 29 Q6 20 7 11", stroke="#45b4cc", width=2.5)
            if shut:
                s.circle(7, 7, 5.2, fill=s.linear(0, 2, 0, 12, [(0, "#52c4d6"), (1, "#2a7fb2")]), stroke=INK, width=1.1)
                s.path("M2.5 7.5 Q7 10 11.5 7.5", stroke=INK, width=1.2)
            else:
                s.circle(7, 7, 5.6, fill=s.radial(5.6, 5.4, 6.4, [(0, "#ffffff"), (1, "#d6e2ec")]), stroke=INK, width=1.1)
                s.circle(8.4, 7.4, 2.9, fill="#1a1630")
                s.circle(9.3, 6.2, 0.95, fill="#ffffff")
            return s

        def leg(mirror: bool):
            s = Svg(44, 36)

            def x(v: float) -> float:
                return 44 - v if mirror else v
            d = f"M{x(3):.1f} 6 Q{x(14):.1f} 0.6 {x(24):.1f} 5 Q{x(34):.1f} 14 {x(40):.1f} 33"
            s.path(d, stroke=INK, width=5.6)
            s.path(d, stroke="#3aa6c4", width=3.6)
            s.path(f"M{x(4):.1f} 5 Q{x(14):.1f} 1.2 {x(23):.1f} 4.6", stroke="#c4f6f6", width=1.0, opacity=0.8)
            s.circle(x(24), 5, 2.3, fill="#2a8ab0", stroke=INK, width=0.8)
            s.path(f"M{x(38.4):.1f} 29 L{x(41.4):.1f} 35 L{x(40.8):.1f} 28.4 Z", fill="#e8f6f6", stroke=INK, width=0.7)
            return s

        def claw_big():
            # wrist on the right, pincer pointing left: a big mitten-like palm and a
            # long fixed finger; the moving finger (dactyl) is its own part
            s = Svg(58, 38)
            fill = s.radial(38, 12, 40, [(0, "#fff8c4"), (0.4, "#ffd24c"), (0.8, "#e89a24"), (1, "#a8601a")])
            finger = [(30, 21), (18, 21.6), (8, 22.6), (2.5, 24.5), (6, 27.4), (16, 30), (26, 32), (32, 31)]
            s.path(smooth_closed(finger, 0.5), fill=fill, stroke=INK, width=1.5)
            for k in range(5):
                tx = 8 + k * 4.4
                s.polygon([(tx - 1.4, 22.4 - k * 0.1), (tx, 19.4 - k * 0.1), (tx + 1.4, 22.2 - k * 0.1)], fill="#fff2c0", stroke=INK, width=0.5)
            palm = [(56, 14), (52, 6), (42, 3), (32, 4.5), (27, 10), (26, 20), (29, 29), (40, 33), (52, 30), (57, 22)]
            s.path(smooth_closed(palm, 0.55), fill=fill, stroke=INK, width=1.7)
            s.path(smooth_open([(53, 9), (44, 5.4), (34, 6.4), (29.5, 11)]), stroke="#fffbe0", width=1.8, opacity=0.85)
            for x, y in ((40, 12), (47, 15), (36, 21), (44, 24)):
                s.circle(x, y, 0.7, fill="#c8781e", opacity=0.45)
            s.path("M30 24 Q40 28.5 54 25", stroke="#b86a1a", width=1.4, opacity=0.5)
            s.path("M52 16 Q55 20 52 25", stroke="#a8601a", width=1.2, opacity=0.7)
            s.path("M10 25.8 Q18 26.6 27 27.4", stroke="#fff2c0", width=0.9, opacity=0.7)
            return s

        def dactyl():
            # moving finger, hinge on the right, tip on the left
            s = Svg(30, 13)
            fill = s.linear(0, 1, 0, 12, [(0, "#fff2b0"), (0.5, "#ffc43a"), (1, "#c8781e")])
            s.path(smooth_closed([(28.5, 2.2), (18, 1.5), (8, 3.5), (2, 8.5), (6.5, 10), (16, 9.2), (28.5, 9.8)], 0.5), fill=fill, stroke=INK, width=1.4)
            for k in range(4):
                tx = 9 + k * 4.4
                s.polygon([(tx - 1.2, 9.4 - k * 0.1), (tx, 12.2), (tx + 1.2, 9.6 - k * 0.1)], fill="#fff2c0", stroke=INK, width=0.5)
            s.path("M26 3.4 Q16 2.4 8 4.6", stroke="#fffbe0", width=1.0, opacity=0.8)
            return s

        def arm_big():
            s = Svg(26, 14)
            s.path(rounded_rect_path(1.5, 2, 23, 10, 4.5), fill=s.linear(0, 2, 0, 12, [(0, "#ffe07a"), (0.6, "#e8a030"), (1, "#a8601a")]), stroke=INK,
                   width=1.3)
            s.path("M5 4.5 L21 4.5", stroke="#fff6cc", width=1.0, opacity=0.7)
            return s

        def claw_small():
            s = Svg(24, 16)
            fill = s.linear(0, 2, 0, 15, [(0, "#9ff0f0"), (0.6, "#3aa6c4"), (1, "#1f5a86")])
            s.path(smooth_closed([(2, 6), (8, 2.5), (16, 3), (22.5, 5.5), (17, 7.6), (10, 8.4)], 0.5), fill=fill, stroke=INK, width=1.2)
            s.path(smooth_closed([(3, 9), (10, 8.2), (17, 9.8), (22, 13.6), (14, 13.6), (6, 13)], 0.5), fill=fill, stroke=INK, width=1.2)
            s.path("M6 4 Q12 3 17 4.4", stroke="#e6fffb", width=0.8, opacity=0.8)
            return s

        def arm_small():
            s = Svg(18, 9)
            s.path(rounded_rect_path(1, 1.5, 16, 6, 3), fill=s.linear(0, 1, 0, 8, [(0, "#7fe0e8"), (1, "#256e94")]), stroke=INK, width=1.1)
            return s

        return {**_shared_parts(), "carapace": (carapace, (33, 37)), "stalk": (lambda: stalk(False), (7, 29)), "stalk_shut": (lambda: stalk(True), (7, 29)),
                "leg": (lambda: leg(False), (3, 6)), "leg_l": (lambda: leg(True), (41, 6)), "claw": (claw_big, (54, 19)), "dactyl": (dactyl, (28, 5.5)),
                "arm": (arm_big, (3, 7)), "pinch": (claw_small, (3, 8)), "forearm": (arm_small, (2, 4.5))}

    def _guard(self, e, t: float) -> float:
        """0 = claws low (stompable) … 1 = claws hoisted (guard)."""
        if not e.alive:
            return 0.0
        period = float(e.params.get("crest_period", 2.6))
        duty = float(e.params.get("crest_duty", 0.45))
        phase = e.timer % period if period > 0 else 0.0
        if e.anim == "guard":
            return _ease(phase / 0.12) if phase < 0.12 else 1.0
        since = phase - period * duty
        if 0 <= since < 0.12:  # snapping back down
            return 1.0 - _ease(since / 0.12)
        left = period - phase
        if period > 0 and left < 0.45:  # telegraph: the claws twitch upward
            k = 1 - left / 0.45
            return 0.3 * _ease(k) + 0.05 * math.sin(t * 46) * k
        return 0.0

    def _leg_angle(self, hx: float, hy: float, scale: float, lift: float, mirror: bool) -> float:
        lx, ly = self.LEG
        reach = math.hypot(lx, ly) * scale
        need = max(-0.98, min(0.98, (-hy - lift) / reach))
        base = math.degrees(math.atan2(ly, lx))
        ang = math.degrees(math.asin(need)) - base
        return -ang if mirror else ang

    def commands(self, e, t):
        root = _root(self, e)
        out: list[DrawCommand] = []
        g = self._guard(e, t)
        moving = e.alive and abs(e.vx) > 1
        ph = t * 14.0
        bob = -abs(math.sin(ph)) * 1.4 if moving else math.sin(t * 2.0) * 0.4
        body = root.child(0, -14 + bob, math.sin(ph * 0.5) * 1.5 if moving else 0.0)
        # legs behind the shell: four per side, scuttling in alternation
        for side, part in ((1, "leg"), (-1, "leg_l")):
            for i, (hx, hy, sc) in enumerate(self.HIPS):
                lift = max(0.0, math.sin(ph + i * math.pi / 2 + (math.pi / 2 if side < 0 else 0))) * 5.0 if moving else 0.0
                ang = self._leg_angle(hx, hy, sc, lift, side < 0)
                out.append(self.cmd(part, root.child(side * hx, hy + bob * 0.5, ang), scale=sc / 0.78 * 0.78))
        # eyestalks: upright and alert, folded aside on guard
        for side in (-1, 1):
            sway = math.sin(t * 3 + side) * 4 if e.alive else 0.0
            ang = side * (6 + 52 * g) + sway
            stalk = Xf(*_xy(body.child(side * 7.5, -33)), body.angle + ang, body.sx, body.sy * (1 - 0.18 * g))
            if not e.alive:
                out.append(self.cmd("stalk_shut", stalk))
                out.append(self.cmd("eye_x", stalk.child(0, -22), scale=0.9))
            else:
                shut = self.blink(t, e.origin_x * 0.31 + side) and g < 0.5
                out.append(self.cmd("stalk_shut" if shut else "stalk", stalk))
        out.append(self.cmd("carapace", body))
        # small claw (left): tucked under the mouth → raised over the shell
        sx0, sy0 = _lerp(-25, -26, g), _lerp(-21, -28, g)
        wx, wy = _lerp(-13, -27, g), _lerp(-10, -46, g)
        out.append(self._segment("forearm", body, (sx0, sy0), (wx, wy), 16.0))
        out.append(self.cmd("pinch", body.child(wx, wy, _lerp(-8, -66, g))))
        # big golden claw (right): resting low in front → hoisted over the shell, pincer snapping
        bx0, by0 = _lerp(25, 26, g), _lerp(-21, -28, g)
        cx, cy = _lerp(29, 25, g), _lerp(-1, -40, g)
        out.append(self._segment("arm", body, (bx0, by0), (cx, cy), 23.0))
        twitch = math.sin(t * 40) * 3 if 0 < g < 0.5 else 0.0
        claw = body.child(cx, cy, _lerp(-2, 34, g) + twitch)
        claw = Xf(claw.x, claw.y, claw.angle, claw.sx * _lerp(0.86, 1.0, g), claw.sy * _lerp(0.86, 1.0, g))
        if g > 0.5:
            gape = 10 + 18 * (0.5 + 0.5 * math.sin(t * 16))  # snapping open and shut
        else:
            gape = -15 + (12 * max(0.0, math.sin(t * 1.7)) if e.alive else 0.0) + 30 * g
        out.append(self.cmd("dactyl", claw.child(-25, -7, gape)))
        out.append(self.cmd("claw", claw))
        return _flash(e, t, out, WARM_FLASH)

    def _segment(self, part: str, body: Xf, a: tuple[float, float], b: tuple[float, float], length: float) -> DrawCommand:
        """Arm segment stretched between two points (never upscaled past 1.15)."""
        dx, dy = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(dx, dy) or 1.0
        start = body.child(*a)
        xf = Xf(start.x, start.y, body.angle + math.degrees(math.atan2(dy, dx)), body.sx * min(1.15, ln / length), body.sy)
        return self.cmd(part, xf)


# =========================================================================== Peixe-Saltador
@register("leaping_fish")
class FlyingFish(CreatureRig):
    """Slender banded flying fish: folded pectorals while swimming, wings spread
    and the body pitched along its arc while leaping."""

    du = 0.34

    def parts(self):
        def body():
            s = Svg(96, 40)
            top = [(94, 21), (86, 12.5), (70, 7), (48, 6.5), (28, 10), (12, 15.5), (5, 18.5)]
            low = [(5, 22), (12, 24.5), (28, 30), (48, 33.5), (70, 32.5), (86, 28), (94, 23)]
            s.path(smooth_closed(top + low, 0.45), fill=s.linear(0, 6, 0, 34, [(0, "#1d3a8a"), (0.32, "#2f72c4"), (0.52, "#7fd2f2"), (0.66, "#eef8ff"),
                                                                                (1, "#c4d4e2")]), stroke=INK, width=1.6)
            for x in (30, 42, 54, 66):  # dark bands across the back
                s.path(f"M{x:.1f} {9 if x < 60 else 7.5:.1f} Q{x - 3:.1f} 15 {x - 4.5:.1f} 20", stroke="#16306e", width=4.2, opacity=0.5)
            s.path(smooth_open([(12, 20.5), (40, 20), (70, 19.5), (88, 21)]), stroke="#e6fbff", width=1.2, opacity=0.85)
            s.path(smooth_open([(20, 13), (46, 9), (74, 9.5)]), stroke="#8fc8ff", width=1.6, opacity=0.7)
            s.path("M78 14 Q74 21 78 28", stroke="#1a2c6a", width=1.2, opacity=0.8)
            s.path("M93 22.5 L88.5 23.6", stroke=INK, width=1.1)
            return s

        def tail():
            s = Svg(36, 42)
            s.path("M34 18 L20 12 L6 2 Q10 14 17 21 Q8 30 1 40 L20 30 L34 24 Z", fill=s.linear(0, 0, 36, 0, [(0, "#8fd8ff"), (0.6, "#3a7ad0"), (1, "#1d3a8a")]),
                   stroke=INK, width=1.3)
            for d in ("M32 20 L9 5", "M32 21 L16 19", "M32 22 L5 37"):
                s.path(d, stroke="#dff4ff", width=0.8, opacity=0.7)
            return s

        def wing(far: bool):
            s = Svg(64, 30)
            fill = s.linear(0, 2, 0, 26, [(0, "#d8f6ff", 0.92), (1, "#6ec8ec", 0.8)]) if not far else s.linear(0, 2, 0, 26, [(0, "#6aa8d0"), (1, "#2a5a9a")])
            s.path("M60 22 Q46 3 22 2 Q8 2 2 8 Q12 10 22 12 Q10 14 4 20 Q20 19 34 22 Q46 26 60 25 Z", fill=fill, stroke=INK, width=1.2)
            for d in ("M59 23 Q36 8 6 6", "M59 23.5 Q36 12 10 13", "M59 24 Q38 17 8 19", "M59 24 Q44 21 26 21"):
                s.path(d, stroke="#ffffff" if not far else "#9ccbe8", width=0.7, opacity=0.8)
            return s

        def fin():
            s = Svg(20, 12)
            s.path("M18 2 Q8 3 2 10 Q10 8 18 7 Z", fill="#5aa0e0", stroke=INK, width=0.9)
            return s

        def eye():
            s = Svg(13, 13)
            s.circle(6.5, 6.5, 5.6, fill=s.radial(5.5, 5, 6.5, [(0, "#ffffff"), (1, "#d8e4ee")]), stroke="#10204a", width=1.0)
            s.circle(7.4, 6.8, 3.2, fill="#10142a")
            s.circle(8.4, 5.6, 1.1, fill="#ffffff")
            return s

        def drop():
            s = Svg(6, 8)
            s.path("M3 0.5 Q5.6 4.6 3 7.5 Q0.4 4.6 3 0.5 Z", fill="#e8fbff", stroke="#5ab8d8", width=0.5)
            return s

        return {**_shared_parts(), "body": (body, (48, 20)), "tail": (tail, (33, 21)), "wing": (lambda: wing(False), (59, 23)),
                "wing_far": (lambda: wing(True), (59, 23)), "fin": (fin, (17, 4)), "eye": (eye, (6.5, 6.5)), "drop": (drop, (3, 4))}

    def commands(self, e, t):
        root = _root(self, e)
        out: list[DrawCommand] = []
        leap = e.alive and e.anim == "leap"
        cy = -e.h / 2 / self.du if e.h else -29.0
        if leap:
            pitch = max(-50.0, min(50.0, math.degrees(math.atan2(e.vy, max(40.0, abs(e.vx))))))
        else:
            pitch = math.sin(t * 5.5) * 3 if e.alive else 0.0
        body = _spin(root, 0, cy, 0, 0, root.angle + pitch)
        beat = math.sin(t * (16 if leap and e.vy < 0 else 11)) * (22 if not leap or e.vy < 0 else 6)
        spread = 1.0 if leap else 0.0
        flutter = math.sin(t * 32) * 4 * spread
        far = Xf(*_xy(body.child(26, -1)), body.angle + _lerp(4, 30, spread) + flutter, body.sx * _lerp(0.6, 0.95, spread),
                 body.sy * _lerp(0.45, 0.9, spread))
        out.append(self.cmd("wing_far", far))
        out.append(self.cmd("tail", body.child(-43, 1, beat)))
        out.append(self.cmd("fin", body.child(-12, -12, -4 + beat * 0.2)))
        out.append(self.cmd("fin", body.child(4, 12, 160 - beat * 0.2), scale=0.8))
        out.append(self.cmd("body", body))
        if e.alive:
            out.append(self.cmd("eye", body.child(36, -4)))
        else:
            out.append(self.cmd("eye_x", body.child(36, -4), scale=1.1))
        near = Xf(*_xy(body.child(28, 2)), body.angle + _lerp(-6, 38, spread) + flutter + (math.sin(t * 6) * 3 if not leap else 0.0),
                  body.sx * _lerp(0.62, 1.0, spread), body.sy * _lerp(0.5, 1.0, spread))
        out.append(self.cmd("wing", near))
        if leap and e.state_time < 0.35:  # bursting out of the water
            k = e.state_time / 0.35
            for j, (dx, up) in enumerate(((-30, 1.0), (-10, 1.3), (12, 1.1), (-44, 0.7))):
                out.append(self.cmd("drop", root.child(dx - k * 10 * (1 + j % 2), -6 - up * 40 * k + 50 * k * k, j * 40), alpha=1 - k))
        return _flash(e, t, out, WARM_FLASH)


# =========================================================================== Baiacu-Espinho
@register("puffer")
class Puffer(CreatureRig):
    """Spotted puffer: an oval little fish at rest that balloons into a ball
    bristling with pale spines (clearly visible only while dangerous)."""

    du = 0.42
    REST = (0.95, 0.8)  # body scale when deflated

    def parts(self):
        def body():
            s = Svg(84, 84)
            s.circle(42, 42, 38, fill=s.radial(30, 28, 54, [(0, "#fff8d4"), (0.45, "#f4d67e"), (0.85, "#d6a452"), (1, "#a8763a")]), stroke=INK, width=1.9)
            s.path("M8 50 Q42 86 76 50 Q66 76 42 79 Q18 76 8 50 Z", fill=s.linear(0, 50, 0, 80, [(0, "#fffdf4"), (1, "#e8e2d2")]))
            for x, y, rr in ((24, 22, 3.2), (36, 14, 2.4), (50, 16, 3.0), (62, 26, 2.6), (18, 36, 2.6), (30, 32, 2.0), (46, 30, 2.2), (60, 40, 2.2),
                             (70, 36, 1.8), (12, 46, 1.8), (40, 22, 1.4), (54, 6 + 20, 1.5), (26, 44, 1.6)):
                s.circle(x, y, rr, fill="#8a5426", opacity=0.85)
                s.circle(x - rr * 0.3, y - rr * 0.35, rr * 0.35, fill="#c8925a", opacity=0.8)
            for x, y in ((22, 60), (32, 66), (44, 68), (56, 64), (64, 56), (38, 58), (50, 58)):
                s.circle(x, y, 0.8, fill="#b8a888")
            s.path("M16 24 Q24 12 38 9", stroke="#ffffff", width=2.4, opacity=0.8)
            return s

        def spikes():
            s = Svg(104, 104)
            for k in range(26):
                a = math.radians(k * 360 / 26 + 4)
                ca, sa = math.cos(a), math.sin(a)
                nx, ny = -sa, ca
                base, tip = 34.0, 50.0 if k % 2 == 0 else 46.0
                pts = [(52 + ca * base + nx * 3.4, 52 + sa * base + ny * 3.4), (52 + ca * tip, 52 + sa * tip),
                       (52 + ca * base - nx * 3.4, 52 + sa * base - ny * 3.4)]
                s.polygon(pts, fill=s.linear(52 + ca * base, 52 + sa * base, 52 + ca * tip, 52 + sa * tip, [(0, "#b88a4a"), (0.5, "#fff2d0"), (1, "#ffffff")]),
                          stroke=INK, width=0.9)
            return s

        def fin():
            s = Svg(18, 16)
            s.path("M2 8 Q8 0 17 2 Q14 8 17 14 Q8 16 2 8 Z", fill=s.linear(0, 0, 18, 0, [(0, "#e8b45a", 0.95), (1, "#fff0c0", 0.8)]), stroke=INK, width=1.0)
            s.path("M3 8 L16 4 M3 8 L15 8 M3 8 L16 12", stroke="#b8803a", width=0.6, opacity=0.8)
            return s

        def tail():
            s = Svg(22, 26)
            s.path("M20 10 Q8 0 2 4 Q6 13 2 22 Q8 26 20 16 Z", fill=s.linear(0, 0, 22, 0, [(0, "#fff0c0"), (1, "#d6a452")]), stroke=INK, width=1.1)
            s.path("M18 12 L4 5 M18 13 L3 13 M18 14 L4 21", stroke="#b8803a", width=0.6, opacity=0.8)
            return s

        def eye():
            s = Svg(16, 16)
            s.circle(8, 8, 7, fill=s.radial(7, 6.5, 8, [(0, "#ffffff"), (1, "#dde6ee")]), stroke=INK, width=1.2)
            s.circle(9, 8.6, 4.2, fill="#1a1630")
            s.circle(10.4, 6.8, 1.4, fill="#ffffff")
            s.circle(7.6, 10.4, 0.7, fill="#ffffff")
            return s

        def lid():
            s = Svg(16, 9)
            s.path("M1 8 Q8 -1 15 8 Q8 5 1 8 Z", fill="#e2b45e", stroke=INK, width=1.0)
            return s

        def mouth(round_: bool):
            s = Svg(12, 10)
            if round_:
                s.ellipse(6, 5, 3.6, 3.8, fill="#c4485a", stroke=INK, width=1.1)
                s.ellipse(5.4, 4.2, 1.2, 1.0, fill="#ffffff", opacity=0.6)
            else:
                s.path("M2.5 3.5 Q6 7.5 9.5 3.5", stroke=INK, width=1.3)
                s.ellipse(9.8, 3.4, 1.4, 1.2, fill="#e08a6a", opacity=0.8)
            return s

        def blush():
            s = Svg(12, 7)
            s.ellipse(6, 3.5, 5, 2.6, fill="#ff9a8a", opacity=0.55)
            return s

        return {**_shared_parts(), "body": (body, (42, 42)), "spikes": (spikes, (52, 52)), "fin": (fin, (3, 8)), "tail": (tail, (19, 13)),
                "eye": (eye, (8, 8)), "lid": (lid, (8, 7)), "mouth": (lambda: mouth(False), (6, 4)), "mouth_o": (lambda: mouth(True), (6, 5)),
                "blush": (blush, (6, 3.5))}

    def _puff(self, e) -> float:
        if not e.alive:
            return 1.0 if e.state in ("inflate", "spiky") else 0.0
        if e.anim == "inflate":
            return _ease(e.state_time / 0.3)
        if e.anim == "spiky":
            return 1.0
        if e.anim == "deflate":
            return 1.0 - _ease(e.state_time / 0.4)
        return 0.0

    def commands(self, e, t):
        root = _root(self, e)
        out: list[DrawCommand] = []
        k = self._puff(e)
        cy = -e.h / 2 / self.du if e.h else -36.0
        bx, by = _lerp(self.REST[0], 1.0, k), _lerp(self.REST[1], 1.0, k)
        if e.alive and e.anim == "spiky":
            wob = 1 + 0.025 * math.sin(t * 9)
            bx, by = bx * wob, by * (2 - wob)
        tilt = math.sin(t * 2.2) * 5 * (1 - k) if e.alive else 0.0
        center = root.child(0, cy, tilt)
        body = Xf(center.x, center.y, center.angle, center.sx * bx, center.sy * by)
        if k > 0.02:
            bristle = 1 + (0.04 * math.sin(t * 22) if e.alive and e.anim == "spiky" else 0.0)
            out.append(self.cmd("spikes", body, scale=(0.72 + 0.28 * k) * bristle, alpha=min(1.0, k * 1.6)))
        flap = math.sin(t * 24) if e.alive else 0.0
        out.append(self.cmd("tail", body.child(-36, 2, math.sin(t * 7) * 14 * (1 - 0.6 * k))))
        out.append(self.cmd("body", body))
        out.append(self.cmd("fin", Xf(*_xy(body.child(2, 8)), body.angle - 20 + flap * 18, body.sx * (1 - 0.35 * k) / bx * 0.9,
                                      body.sy * (0.75 + 0.25 * flap) / by * 0.9)))
        face = Xf(body.x, body.y, body.angle, center.sx, center.sy)
        ex = _lerp(15, 17, k)
        if e.alive:
            closed = self.blink(t, e.origin_x * 0.23) and k < 0.5
            for i, (dx, dy, sc) in enumerate(((ex, -12.0 * by, 1.0), (ex + 15 * bx, -10.5 * by, 0.82))):
                eye = face.child(dx * bx, dy)
                if closed:
                    out.append(self.cmd("eye_closed", eye, scale=sc * 1.15))
                else:
                    out.append(self.cmd("eye", eye, scale=sc * (1 + 0.1 * k)))
                    if k > 0.6:
                        out.append(self.cmd("lid", eye.child(0, -3.5, 8 if i else -6), scale=sc))
            out.append(self.cmd("blush", face.child(ex * bx - 2, 1 * by), scale=0.9))
            out.append(self.cmd("mouth_o" if k > 0.4 else "mouth", face.child(36 * bx, 5 * by), scale=1.0 + 0.3 * k))
        else:
            for dx, dy, sc in ((ex, -12.0 * by, 1.0), (ex + 15 * bx, -10.5 * by, 0.8)):
                out.append(self.cmd("eye_x", face.child(dx * bx, dy), scale=sc * 1.2))
        return _flash(e, t, out, COOL_FLASH)


# =========================================================================== Água-Viva Elétrica
@register("jellyfish")
class ElectricJellyfish(CreatureRig):
    """Translucent lilac bell pulsing with the drift; its crown crackles with
    electricity (dangerous top) while frilly arms and tentacles trail."""

    du = 0.42
    TENTACLES = (-29.0, -18.0, -7.0, 7.0, 18.0, 29.0)
    ARMS = (-11.0, -3.5, 4.0, 11.5)

    def parts(self):
        def bell():
            s = Svg(84, 54)
            pts = [(4, 46), (5, 30), (14, 13), (28, 5), (42, 3), (56, 5), (70, 13), (79, 30), (80, 46)]
            scallops = []
            for k in range(8):
                x1 = 80 - 76 * (k + 0.5) / 8
                scallops.append((x1, 51.5))
                scallops.append((80 - 76 * (k + 1) / 8, 46.5))
            outline = pts + scallops[:-1]
            s.path(smooth_closed(outline, 0.45), fill=s.radial(34, 18, 54, [(0, "#fff2ff", 0.92), (0.45, "#f0b0ea", 0.78), (1, "#a95ad0", 0.8)]),
                   stroke="#5a2a7a", width=1.5)
            s.path(smooth_open([(12, 42), (30, 36), (54, 36), (72, 42)]), stroke="#ffffff", width=1.0, opacity=0.5)
            for x in (16, 29, 42, 55, 68):  # radial canals
                s.path(f"M42 20 Q{(42 + x) / 2:.1f} {30:.1f} {x:.1f} 46", stroke="#ffffff", width=0.8, opacity=0.45)
            s.circle(42, 22, 13, fill=s.radial(42, 22, 13, [(0, "#fffbd0", 0.95), (0.45, "#c8fff6", 0.55), (1, "#c8fff6", 0)]))
            s.path(smooth_open([(14, 22), (22, 12), (36, 7)]), stroke="#ffffff", width=2.6, opacity=0.85)
            return s

        def crown():
            # the electrified upper rim: glow, bright core and spark points
            s = Svg(84, 34)
            arc = smooth_open([(6, 30), (14, 13), (28, 5), (42, 3), (56, 5), (70, 13), (78, 30)])
            s.path(arc, stroke="#6ff6ff", width=9.0, opacity=0.35)
            s.path(arc, stroke="#aefcff", width=4.2, opacity=0.95)
            s.path(arc, stroke="#ffffff", width=1.6)
            jag = "M10 20 L13 15 L16 17 L20 10.5 L24 12 L28 6 L33 7.5 L37 3.5 L42 5 L47 3.5 L51 7.5 L56 6 L60 12 L64 10.5 L68 17 L71 15 L74 20"
            s.path(jag, stroke="#fffbd0", width=1.3, opacity=0.95)
            for x, y in ((14, 13), (28, 5), (42, 3), (56, 5), (70, 13)):
                s.polygon(star_points(x, y, 4.6, 1.0, 4), fill="#fffbd0")
            return s

        def zap():
            s = Svg(18, 26)
            d = "M10.5 1 L5 11 L10.5 12 L3.5 25 L14.5 9.5 L9 8.6 L13.5 1 Z"
            s.path(d, stroke="#6ff6ff", width=4.0, opacity=0.45)
            s.path(d, fill="#fffbd0", stroke="#22b8e0", width=1.2)
            return s

        def halo():
            s = Svg(120, 96)
            with s.group(transform="translate(60 48) scale(1 0.8)"):
                s.circle(0, 0, 60, fill=s.radial(0, 0, 60, [(0, "#d8a8ff", 0.45), (0.5, "#9fe8ff", 0.18), (1, "#9fe8ff", 0)]))
            return s

        def tentacle():
            s = Svg(6, 18)
            s.path("M3 0.5 Q4.6 6 3 9 Q1.4 12 3 17.5", stroke="#b070d8", width=1.8, opacity=0.9)
            s.path("M3 0.5 Q4.6 6 3 9 Q1.4 12 3 17.5", stroke="#f8d8ff", width=0.7, opacity=0.9)
            return s

        def arm():
            # a ruffled ribbon segment (overlaps the next one)
            s = Svg(16, 28)
            left = [(5, 0.5), (2.5, 5), (4.6, 9), (1.6, 13.5), (4.2, 18), (2.2, 22.5), (5.6, 27.5)]
            right = [(10.4, 27.5), (13.6, 22.5), (11.4, 18), (14.2, 13.5), (11.2, 9), (13.4, 5), (11, 0.5)]
            s.path(smooth_closed(left + right, 0.6), fill=s.linear(0, 0, 16, 0, [(0, "#ffd8fa", 0.85), (0.5, "#e8a6f0", 0.8), (1, "#b870d8", 0.8)]),
                   stroke="#7a3a9a", width=0.8)
            s.path("M8 1 Q6 9 8.6 14 Q10.6 20 8 27", stroke="#ffffff", width=0.8, opacity=0.6)
            return s

        def eye():
            s = Svg(8, 9)
            s.ellipse(4, 4.5, 3, 3.6, fill="#2a1438")
            s.circle(5, 3.2, 1.0, fill="#ffffff")
            return s

        return {**_shared_parts(), "bell": (bell, (42, 50)), "crown": (crown, (42, 30)), "zap": (zap, (9, 25)), "halo": (halo, (60, 48)),
                "tentacle": (tentacle, (3, 0.5)), "arm": (arm, (8, 0.5)), "eye": (eye, (4, 4.5))}

    def commands(self, e, t):
        root = _root(self, e)
        out: list[DrawCommand] = []
        alive = e.alive
        freq = float(e.params.get("frequency", 0.9))
        phase = e.timer * freq + e.origin_x * 0.01
        rising = max(0.0, -math.cos(phase)) if alive else 0.0
        squeeze = (0.55 * rising + 0.45 * max(0.0, math.sin(t * 5.0))) if alive else 0.0
        bell = root.child(0, -38)
        bell = Xf(bell.x, bell.y, bell.angle, bell.sx * (1 - 0.08 * squeeze), bell.sy * (1 + 0.07 * squeeze))
        if alive:
            out.append(self.cmd("halo", bell.child(0, -22), alpha=0.55 + 0.25 * math.sin(t * 6)))
        trail = 1.0 + 0.6 * rising
        for i, x in enumerate(self.TENTACLES):  # thin tentacles behind the arms
            xf = bell.child(x * (1 - 0.08 * squeeze), -1)
            for j in range(4):
                wave = math.sin(t * 2.6 + j * 0.9 + i * 1.3) * 16 / trail + (x * 0.25 if j == 0 else 0.0)
                xf = Xf(xf.x, xf.y, xf.angle + wave * (0.6 if j == 0 else 1.0), xf.sx, xf.sy)
                out.append(self.cmd("tentacle", xf))
                xf = xf.child(0, 17)
        for i, x in enumerate(self.ARMS):
            xf = bell.child(x, -4)
            for j in range(3):
                wave = math.sin(t * 2.0 + j * 1.1 + i * 2.1) * 12 / trail
                xf = Xf(xf.x, xf.y, xf.angle + wave, xf.sx, xf.sy)
                out.append(self.cmd("arm", xf, scale=1.0 - j * 0.14))
                xf = xf.child(0, 20 * (1.0 - j * 0.14))
        out.append(self.cmd("bell", bell))
        if alive:
            for ex in (-9.0, 9.0):
                out.append(self.cmd("eye", bell.child(ex, -14)))
            out.append(self.cmd("crown", bell.child(0, -20), alpha=0.75 + 0.25 * math.sin(t * 13)))
            for i, (zx, zy, za) in enumerate(((-26.0, -44.0, -35.0), (-9.0, -52.0, -10.0), (10.0, -52.0, 12.0), (27.0, -44.0, 38.0))):
                if (t * 6.5 + i * 0.29) % 1.0 < 0.5:
                    out.append(self.cmd("zap", bell.child(zx, zy, za + math.sin(t * 50 + i) * 8), scale=0.85 + 0.15 * math.sin(t * 31 + i)))
        else:
            for ex in (-9.0, 9.0):
                out.append(self.cmd("eye_x", bell.child(ex, -14), scale=0.75))
        return _flash(e, t, out, WARM_FLASH)


# =========================================================================== Moreia-da-Toca
@register("moray")
class MorayEel(CreatureRig):
    """Spotted green moray in a coral-rock den (the den is part of the rig and
    stays at ground level while the hitbox sinks into it)."""

    du = 0.45
    LIP = -15.0  # top of the den's front lip around the crevice (du above the ground)
    SEG = 9.5  # spacing of the body segments along the spine

    def parts(self):
        def den_back():
            s = Svg(110, 46)
            s.path("M8 45 Q10 22 30 14 Q55 6 80 14 Q100 22 102 45 Z", fill=s.linear(0, 8, 0, 46, [(0, "#b9768f"), (1, "#6a3e5e")]), stroke=INK, width=1.4)
            s.ellipse(55, 30, 22, 12, fill=s.radial(55, 34, 24, [(0, "#05030a"), (0.7, "#1a0c1e"), (1, "#3a2032")]))
            return s

        def den_front():
            s = Svg(112, 34)
            top = [(4, 33), (6, 16), (16, 9), (28, 10), (40, 18.5), (50, 18.8), (62, 18.8), (72, 18.5), (84, 10), (96, 9), (106, 16), (108, 33)]
            s.path(smooth_closed(top, 0.4), fill=s.linear(0, 8, 0, 34, [(0, "#f2a6bc"), (0.35, "#d27c9c"), (1, "#7a4670")]), stroke=INK, width=1.6)
            s.path(smooth_open([(8, 15), (16, 10), (28, 11), (40, 19)], 0.4), stroke="#ffe0ea", width=1.6, opacity=0.8)
            s.path(smooth_open([(72, 19), (84, 11), (96, 10), (104, 15)], 0.4), stroke="#ffe0ea", width=1.6, opacity=0.8)
            for x, y, rr in ((14, 25, 1.4), (24, 28, 1.0), (88, 26, 1.3), (98, 23, 1.0), (60, 27, 1.1), (46, 26, 0.9), (34, 24, 0.8)):
                s.circle(x, y, rr, fill="#5a2a48", opacity=0.6)
            # a brain coral, an anemone and a tube sponge living on the den
            s.path("M86 12 Q86 2 96 2 Q106 2 106 12 Z", fill=s.radial(92, 4, 12, [(0, "#ffe2a8"), (1, "#d8963a")]), stroke=INK, width=1.0)
            s.path("M89 8 Q93 4 96 7 Q99 10 103 6", stroke="#a8641a", width=0.8)
            for k in range(7):
                a = math.radians(-150 + k * 20)
                ex, ey = 18 + math.cos(a) * 7.5, 8 + math.sin(a) * 7
                s.path(f"M18 9 Q{18 + math.cos(a) * 4 + 1:.1f} {8 + math.sin(a) * 3:.1f} {ex:.1f} {ey:.1f}", stroke="#5fe0cc", width=1.4)
                s.circle(ex, ey, 0.9, fill="#d8fff8")
            s.path("M14.5 11 L15.5 7 L20.5 7 L21.5 11 Z", fill="#2f9a8a", stroke=INK, width=0.6)
            for x, hh in ((6.5, 9.0), (10.5, 12.0)):
                s.path(rounded_rect_path(x - 1.8, 16 - hh, 3.6, hh, 1.4), fill="#9a6ad6", stroke=INK, width=0.6)
            return s

        def seg(variant: int):
            s = Svg(30, 26)
            s.ellipse(15, 13, 12.2, 10.6, fill=s.linear(3, 0, 27, 0, [(0, "#2f6a4a"), (0.4, "#4f9e62"), (0.78, "#8cc85e"), (1, "#c8e07a")]))
            spots = ((9, 8, 1.6), (16, 15, 1.4), (8, 17, 1.1), (19, 6, 1.0)) if variant == 0 else ((12, 5, 1.2), (7, 12, 1.5), (17, 11, 1.2), (12, 19, 1.3))
            for x, y, rr in spots:
                s.circle(x, y, rr, fill="#f2e05a", opacity=0.9)
            s.circle(13 if variant else 11, 12 if variant else 13, 1.1, fill="#1f4a36", opacity=0.6)
            return s

        def seg_ink():
            s = Svg(30, 26)
            s.ellipse(15, 13, 13.4, 11.8, fill=INK)
            return s

        def fin():
            s = Svg(14, 18)
            s.path("M12 1 Q2 4 1.5 9 Q2 14 12 17 Z", fill=s.linear(0, 0, 14, 0, [(0, "#ffd24a"), (1, "#c8902a")]), stroke=INK, width=1.0)
            return s

        def head():
            s = Svg(58, 38)
            outline = [(4, 30), (3, 16), (10, 8), (24, 4.5), (38, 6), (50, 10.5), (56.5, 15), (55, 19), (46, 20.5), (30, 22.5), (20, 26), (12, 33)]
            s.path(smooth_closed(outline, 0.45), fill=s.linear(0, 4, 0, 33, [(0, "#3f8a58"), (0.5, "#5aa86a"), (1, "#a8d070")]), stroke=INK, width=1.6)
            for x, y, rr in ((14, 14, 1.6), (22, 10, 1.3), (30, 12, 1.2), (12, 23, 1.2), (40, 10, 1.0), (19, 18, 1.0)):
                s.circle(x, y, rr, fill="#f2e05a", opacity=0.9)
            for k in range(6):  # upper fangs
                tx = 30 + k * 4
                s.polygon([(tx - 1.1, 20.2 - k * 0.3), (tx, 24 - k * 0.3), (tx + 1.1, 20 - k * 0.3)], fill="#fffbf0", stroke=INK, width=0.5)
            s.path("M54 12 L58 9.5", stroke=INK, width=2.4)  # tubular nostril
            s.path("M54 12 L58 9.5", stroke="#7ab86a", width=1.2)
            s.circle(16, 26, 1.8, fill="#1f3a2a")
            s.path("M12 10 Q22 5 34 6.5", stroke="#b8e89a", width=1.4, opacity=0.8)
            return s

        def jaw():
            s = Svg(34, 14)
            s.path("M2 3 L30 2 Q34 3 32 6 Q22 12 6 12 Q1 9 2 3 Z", fill=s.linear(0, 2, 0, 12, [(0, "#9ccc6a"), (1, "#4a8a56")]), stroke=INK, width=1.3)
            s.path("M6 3.2 L29 2.6", stroke="#c2385a", width=1.6)
            for k in range(5):
                tx = 10 + k * 4.2
                s.polygon([(tx - 1.0, 3), (tx, -0.4), (tx + 1.0, 3)], fill="#fffbf0", stroke=INK, width=0.45)
            return s

        def maw():
            s = Svg(30, 16)
            s.path("M1 2 L28 3 Q24 13 6 14 Q0 9 1 2 Z", fill=s.radial(10, 8, 18, [(0, "#5a0a1a"), (1, "#c2385a")]))
            return s

        def eye():
            s = Svg(10, 10)
            s.circle(5, 5, 4.2, fill=s.radial(4.4, 4.2, 5, [(0, "#fff6a0"), (1, "#f0b81a")]), stroke=INK, width=1.0)
            s.ellipse(5.4, 5, 1.2, 2.8, fill="#10140a")
            s.circle(4.0, 3.4, 0.8, fill="#ffffff")
            return s

        def lurk():
            s = Svg(26, 10)
            for x in (8, 18):
                s.ellipse(x, 5, 3.2, 2.4, fill=s.radial(x, 5, 3.4, [(0, "#fffbb0"), (0.6, "#f2c41a"), (1, "#f2c41a", 0)]))
                s.ellipse(x + 0.3, 5, 0.8, 1.8, fill="#10140a")
            return s

        def grit():
            s = Svg(10, 8)
            s.path(blob(5, 4, 4, 3, 0.25, seed=2), fill="#e8c8d8", opacity=0.8)
            return s

        return {**_shared_parts(), "den_back": (den_back, (55, 44)), "den_front": (den_front, (56, 33)), "seg": (lambda: seg(0), (15, 13)),
                "seg_b": (lambda: seg(1), (15, 13)),
                "seg_ink": (seg_ink, (15, 13)), "fin": (fin, (12, 9)), "head": (head, (8, 24)),
                "jaw": (jaw, (4, 3)), "maw": (maw, (3, 3)), "eye": (eye, (5, 5)), "lurk": (lurk, (13, 5)), "grit": (grit, (5, 4))}

    def commands(self, e, t):
        base_y = e.memory.get("base_y", e.y)
        travel = max(1.0, e.h)
        sink = max(0.0, e.y - base_y)
        k = 1.0 - max(0.0, min(1.0, sink / travel))  # how far out of the den
        base = Xf(0.0, -sink / self.du)
        state = e.anim if e.alive else "defeat"
        hidden_time = float(e.params.get("hidden_time", 2.2))
        telegraph = e.alive and state == "hidden" and e.state_time > hidden_time - 0.6
        shake = math.sin(t * 55) * 1.6 if telegraph else 0.0
        out: list[DrawCommand] = [self.cmd("den_back", base.child(shake, 0))]
        if state == "hidden" or k < 0.08:
            glint = 1.0 if telegraph else (0.55 if not self.blink(t * 0.7, e.origin_x * 0.13) else 0.0)
            if e.alive:
                out.append(self.cmd("lurk", base.child(shake + (2 if e.facing > 0 else -2), -20), alpha=glint))
        squashed = not e.alive and e.memory.get("defeat_kind") == "squash"
        if not e.alive:
            k = k * max(0.0, min(1.0, e.defeated / 0.6)) * (0.35 if squashed else 1.0)
        length = k * 84.0
        lip = self.LIP
        # body: segments from the lip up to the neck, swaying in an S-curve
        sway_t = t * 2.3
        pts = []
        s_ = 0.0
        while s_ <= length:
            amp = 7.0 * min(1.0, s_ / 36.0)
            pts.append((amp * math.sin(s_ * 0.06 - sway_t), lip - s_))
            s_ += self.SEG
        if length > 1:
            pts.append((7.0 * min(1.0, length / 36.0) * math.sin(length * 0.06 - sway_t), lip - length))
        body = pts[:-1] + ([pts[-1]] if length > 1 else [])
        for x, y in body:  # dorsal fin along the back (left side), then a continuous ink outline, then the body
            out.append(self.cmd("fin", base.child(x + shake - 10, y)))
        for x, y in body:
            out.append(self.cmd("seg_ink", base.child(x + shake, y)))
        for i, (x, y) in enumerate(body):
            out.append(self.cmd("seg" if i % 2 == 0 else "seg_b", base.child(x + shake, y)))
        if length > 1:
            nx, ny = pts[-1]
            px, py = pts[-2] if len(pts) > 1 else (nx, ny + 1)
            spine = math.degrees(math.atan2(ny - py, nx - px)) + 90  # 0 = straight up
            bite = state == "bite"
            if state in ("out", "bite"):
                head_ang = -58 + spine * 0.4 + (34 if bite else math.sin(t * 2.5) * 6)
                gape = 46 if bite else 10 + 8 * max(0.0, math.sin(t * 3.1))
            elif state == "rise":
                head_ang, gape = -70 + spine * 0.4, 18.0
            elif state == "defeat":
                head_ang, gape = 40.0, 26.0
            else:
                head_ang, gape = -72 + spine * 0.4, 6.0
            neck = base.child(nx + shake, ny + 4)
            head = neck.child(0, 0, head_ang)
            if squashed:  # flattened into the mouth of the den
                head = Xf(head.x, head.y, 80.0, head.sx * 1.2, head.sy * 0.45)
            out.append(self.cmd("maw", head.child(26, -3, gape * 0.35), alpha=min(1.0, gape / 20)))
            out.append(self.cmd("jaw", head.child(24, -1, gape)))
            out.append(self.cmd("head", head))
            if e.alive:
                out.append(self.cmd("eye", head.child(28, -14)))
            else:
                out.append(self.cmd("eye_x", head.child(28, -14), scale=0.8))
        out.append(self.cmd("den_front", base.child(shake, 0)))
        if telegraph or (e.alive and state == "rise"):
            for j in range(4):  # bubbles stream out of the crevice
                life = (t * 1.6 + j * 0.27) % 1.0
                out.append(self.cmd("bubble", base.child(math.sin(life * 9 + j * 2) * 5 + (j - 1.5) * 4, -18 - life * 46),
                                    scale=0.8 + 0.7 * life, alpha=1 - life))
        if e.alive and state == "rise":
            for j in range(4):  # coral grit kicked up by the lunge
                life = min(1.0, e.state_time / 0.45)
                out.append(self.cmd("grit", base.child((j - 1.5) * 14 * (0.6 + life), -16 - 18 * life + 22 * life * life, j * 50), alpha=1 - life))
        return _flash(e, t, out, WARM_FLASH)


# =========================================================================== Polvo-Tinteiro
@register("octopus")
class InkOctopus(CreatureRig):
    """Round coral-orange octopus with a spotted mantle: squeezes and spreads
    its arms in jets; while chasing it leans in, pulses faster and puffs ink."""

    du = 0.42
    ROOTS = (-19.0, -12.5, -6.0, 0.5, 7.0, 13.5, 20.0)

    def parts(self):
        def mantle():
            s = Svg(66, 64)
            s.path(blob(33, 30, 29, 28, 0.03, seed=4), fill=s.radial(24, 18, 46, [(0, "#ffd2b0"), (0.35, "#ff9a62"), (0.75, "#e8603e"), (1, "#a83a2a")]),
                   stroke=INK, width=1.9)
            for x, y, rr in ((20, 18, 3.4), (34, 12, 2.6), (46, 20, 3.0), (26, 32, 2.4), (42, 34, 2.2), (14, 30, 2.0), (52, 32, 1.8), (32, 24, 1.6)):
                s.circle(x, y, rr, fill="#c8402a", opacity=0.75)
                s.circle(x - rr * 0.3, y - rr * 0.3, rr * 0.4, fill="#ffb48a", opacity=0.8)
            for x, y in ((28, 8), (40, 9), (16, 24), (50, 26), (38, 28)):
                s.circle(x, y, 1.0, fill="#fff0e0", opacity=0.85)
            s.path("M12 20 Q16 8 30 5", stroke="#ffffff", width=2.6, opacity=0.75)
            s.path(smooth_open([(8, 44), (33, 54), (58, 44)]), stroke="#8a2a1e", width=2.0, opacity=0.4)
            return s

        def eye():
            s = Svg(18, 18)
            s.ellipse(9, 10, 7.4, 7.0, fill=s.radial(7.6, 8.4, 8.6, [(0, "#ffffff"), (1, "#e2dcd2")]), stroke=INK, width=1.3)
            s.circle(9.6, 10.4, 4.6, fill=s.radial(9, 9.6, 5, [(0, "#ffe88a"), (0.7, "#f2a628"), (1, "#b8661a")]))
            s.path(rounded_rect_path(6.2, 9.1, 6.8, 2.6, 1.3), fill="#1a1020")
            s.circle(11.8, 8.0, 1.3, fill="#ffffff")
            return s

        def brow():
            s = Svg(18, 8)
            s.path("M1 6.5 Q9 -0.5 17 6.5 Q9 3.6 1 6.5 Z", fill="#c84a30", stroke=INK, width=1.0)
            return s

        def arm(lower: bool):
            s = Svg(16, 34)
            if lower:
                d = "M4 1 Q2 12 4 22 Q6 30 12 31 Q15 28 11 26 Q8 24 9 18 Q10 9 12 1 Z"
            else:
                d = "M2 1 Q1 14 4 30 L12 30 Q15 14 14 1 Z"
            s.path(d, fill=s.linear(0, 0, 16, 0, [(0, "#ff9a62"), (0.6, "#e8603e"), (1, "#b84430")]), stroke=INK, width=1.3)
            for k in range(4 if not lower else 3):
                y = 6 + k * 7
                s.circle(11.2 if not lower else 9.6, y, 1.4 - k * 0.15, fill="#ffe2d0", stroke="#c8604a", width=0.4)
            return s

        def siphon():
            s = Svg(14, 10)
            s.path("M1 3 Q8 1 13 4 L12 8 Q6 9 1 7 Z", fill=s.linear(0, 1, 0, 9, [(0, "#ffb084"), (1, "#c8503a")]), stroke=INK, width=1.0)
            s.ellipse(12.4, 6, 1.0, 1.8, fill="#5a1a14")
            return s

        def ink():
            s = Svg(24, 20)
            s.path(blob(12, 10, 10, 8, 0.2, seed=3), fill=s.radial(11, 9, 11, [(0, "#2a1838", 0.8), (0.7, "#3a2848", 0.5), (1, "#3a2848", 0)]))
            return s

        return {**_shared_parts(), "mantle": (mantle, (33, 54)), "eye": (eye, (9, 10)), "brow": (brow, (9, 6)), "arm": (lambda: arm(False), (8, 2)),
                "arm_tip": (lambda: arm(True), (8, 2)), "siphon": (siphon, (2, 5)), "ink": (ink, (12, 10))}

    def commands(self, e, t):
        root = _root(self, e)
        out: list[DrawCommand] = []
        chase = e.alive and e.anim == "chase"
        rate = 1.7 if chase else 0.85
        p = (t * rate + e.origin_x * 0.003) % 1.0
        jet = _ease(p / 0.3) if p < 0.3 else 1.0 - _ease((p - 0.3) / 0.7)  # 1 = squeezed (jet), 0 = spread
        if not e.alive:
            jet = 0.2
        lean = (12.0 if chase else 4.0 * math.sin(t * 1.3)) if e.alive else 0.0
        center = root.child(0, -40 - 4 * jet)
        body = Xf(center.x, center.y, center.angle + lean, center.sx * (1 - 0.1 * jet), center.sy * (1 + 0.1 * jet))
        if chase:
            for j in range(2):
                life = (t * 1.2 + j * 0.5) % 1.0
                out.append(self.cmd("ink", root.child(-34 - life * 26, -30 + life * 10), scale=0.6 + 1.0 * life, alpha=(1 - life) * 0.9))
        n = len(self.ROOTS)
        for idx in list(range(0, n, 2)) + list(range(1, n, 2)):  # back arms first
            x = self.ROOTS[idx]
            spread = x / 20.0
            ang = -spread * _lerp(58, 10, jet) + math.sin(t * 3 + idx) * 6 - lean * 0.6
            upper = body.child(x * (1 - 0.15 * jet), 2, ang)
            out.append(self.cmd("arm", upper, scale=0.9 if idx % 2 else 1.0))
            curl = -spread * _lerp(64, 6, jet) - (10 if spread >= 0 else -10) * (1 - jet) + math.sin(t * 4 + idx * 1.7) * 14
            out.append(self.cmd("arm_tip", upper.child(0, 27, curl), scale=0.9 if idx % 2 else 1.0))
        out.append(self.cmd("siphon", body.child(22, -14, -10 - 20 * jet)))
        out.append(self.cmd("mantle", body))
        if e.alive:
            closed = self.blink(t, e.origin_x * 0.17)
            for i, (ex, sc) in enumerate(((-10.0, 0.95), (11.0, 1.0))):
                eye = body.child(ex, -16)
                out.append(self.cmd("eye_closed" if closed else "eye", eye, scale=sc * (1.15 if closed else 1.0)))
                if chase and not closed:  # a determined frown while hunting
                    out.append(self.cmd("brow", eye.child(0, -6.5, 12 if i else -12), scale=sc))
        else:
            for ex in (-10.0, 11.0):
                out.append(self.cmd("eye_x", body.child(ex, -16), scale=1.1))
        return _flash(e, t, out, COOL_FLASH)
