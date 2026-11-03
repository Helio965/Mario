"""Cidade Mecânica creatures.

* ``patrol_bot`` — Robô de Ronda: a chubby tin automaton on two stubby legs,
  a gyroscope spinning on its head and a caged lantern in its chest. On alert
  it stops, the lantern flares and its beam sweeps the street.
* ``cannon`` — Canhão Sentinela: a brass steam mortar on a cog carriage over a
  riveted plinth; while charging, the boiler hisses, the gauge climbs and the
  valve wheel glows; firing kicks the barrel back in a burst of steam.
* ``drone`` — Drone Vigia: a tin pod on twin rotors with a single camera eye;
  on alert the iris snaps shut to a red pinpoint before the dive.
* ``steam_press`` — Prensa a Vapor: a faceless press ram (flat brass top, a
  hazard band and a striking die) hanging from two hydraulic cylinders whose
  chrome rods extend as it falls; it vents steam and flashes its lamps as a
  telegraph.
* ``arc_turret`` — Torreta de Arco: a copper turret on four spider legs whose
  stubby mortar tilts up and glows red-hot before lobbing a hot nut.

Metals stay cool (tin, steel) or carry a dark ink outline so they read against
the warm dusk; every telegraph is a light (lantern, valve, iris, lamps,
barrel) plus steam. Light comes from the upper left, as in the world art.
"""

from __future__ import annotations

import math

from ..rig import DrawCommand, Xf
from ..svg import Svg, rounded_rect_path, smooth_closed, star_points
from .base import CreatureRig, register

INK = "#22161e"
FLASH = (255, 118, 112)
TIN_HI, TIN_LIGHT, TIN, TIN_DARK, TIN_DEEP = "#f6f9fc", "#d3dce8", "#9eabc0", "#62708a", "#373f55"
BRASS_HI, BRASS_LIGHT, BRASS, BRASS_DARK, BRASS_DEEP = "#fff1c2", "#f4cd72", "#d49a3e", "#956126", "#5a3816"
COPPER_HI, COPPER_LIGHT, COPPER, COPPER_DARK = "#ffd2a8", "#e8935c", "#bf6738", "#73351c"
STEEL_HI, STEEL_LIGHT, STEEL, STEEL_DARK, STEEL_DEEP = "#e9eef6", "#b0bace", "#7c87a2", "#4c536a", "#2b2f40"
IRON_HI, IRON, IRON_DARK, IRON_DEEP = "#8e8c9c", "#545264", "#34323f", "#1d1c25"
LAMP_HOT, LAMP, LAMP_DEEP = "#fff7df", "#ffd583", "#ff9c45"
HOT_WHITE, HOT_YELLOW, HOT_ORANGE, HOT_RED = "#fff4cc", "#ffcf4a", "#ff8a2c", "#d8401e"
HAZARD_Y, HAZARD_K = "#f5c43c", "#2b2329"
LENS_CALM, LENS_ALERT = "#6ff0e0", "#ff3b30"


# --------------------------------------------------------------------------- shared helpers
def _root(rig: CreatureRig, e) -> Xf:
    return Xf() if e.alive else rig.defeat_xf(e, Xf())


def _flash(e, t: float, out: list[DrawCommand]) -> list[DrawCommand]:
    """Hit flash while the damage timer runs (the two-hit turret and every hit)."""
    if e.hit_timer > 0 and int(t * 20) % 2 == 0:
        for c in out:
            c.tint = FLASH
    return out


def _at(base: Xf, lx: float, ly: float, angle: float = 0.0, sx: float = 1.0, sy: float = 1.0) -> Xf:
    """Child transform of ``base`` with an extra local scale."""
    c = base.child(lx, ly, angle)
    return Xf(c.x, c.y, c.angle, c.sx * sx, c.sy * sy)


def _clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


def _ease(t: float) -> float:
    t = _clamp(t)
    return t * t * (3 - 2 * t)


def _halo_svg(size: float, color: str, strength: float = 0.6) -> Svg:
    s = Svg(size, size)
    c = size / 2
    s.circle(c, c, c, fill=s.radial(c, c, c, [(0, color, strength), (0.35, color, strength * 0.5), (1, color, 0)]))
    return s


def _lobes(cx: float, cy: float, rx: float, ry: float, n: int, depth: float, seed: float = 0.0) -> str:
    """Closed puffy outline with ``n`` lobes (steam, smoke)."""
    pts = []
    for i in range(n * 2):
        a = math.pi * i / n
        k = 1 + (depth if i % 2 == 0 else -depth * 0.3) + 0.05 * math.sin(i * 2.7 + seed)
        pts.append((cx + math.cos(a) * rx * k, cy + math.sin(a) * ry * k))
    return smooth_closed(pts, 1.0)


def _puff_svg(size: float = 20.0, dark: bool = False) -> Svg:
    """Steam puff (white, lit from the upper left) or soot smoke (``dark``)."""
    s = Svg(size, size * 0.8)
    c = size / 2
    if dark:
        stops = [(0, "#9a8a94"), (0.6, "#6a5a66"), (1, "#4a3a48")]
        line = "#3a2a36"
    else:
        stops = [(0, "#ffffff"), (0.6, "#f2ece8"), (1, "#c8bcc4")]
        line = "#a8949e"
    s.path(_lobes(c, size * 0.42, size * 0.4, size * 0.3, 5, 0.18, seed=2), fill=s.radial(c - size * 0.12, size * 0.28, size * 0.55, stops),
           stroke=line, width=size * 0.04, opacity=0.95)
    return s


def _spark_svg(size: float = 12.0, color: str = HOT_YELLOW) -> Svg:
    s = Svg(size, size)
    c = size / 2
    s.circle(c, c, c, fill=s.radial(c, c, c, [(0, color, 0.7), (1, color, 0)]))
    s.polygon(star_points(c, c, c * 0.9, c * 0.22, 4), fill="#ffffff")
    return s


def _streak_svg(length: float = 40.0, color: str = "#ffffff") -> Svg:
    s = Svg(6, length)
    s.path(f"M2 {length:.1f} L3 0 L4 {length:.1f} Z", fill=s.linear(0, 0, 0, length, [(0, color, 0), (1, color, 0.85)]))
    return s


def _eye_x_svg(size: float = 9.0) -> Svg:
    s = Svg(size, size)
    m, n = size * 0.18, size * 0.82
    s.path(f"M{m:.2f} {m:.2f} L{n:.2f} {n:.2f} M{n:.2f} {m:.2f} L{m:.2f} {n:.2f}", stroke=INK, width=size * 0.2)
    return s


def _rivet(s: Svg, x: float, y: float, r: float, body: str = TIN_LIGHT, rim: str = TIN_DEEP, hi: str = "#ffffff") -> None:
    s.circle(x, y, r, fill=body, stroke=rim, width=r * 0.4)
    s.circle(x - r * 0.3, y - r * 0.3, r * 0.4, fill=hi, opacity=0.85)


def _gear_d(cx: float, cy: float, r: float, teeth: int, depth: float = 0.2, hole: float = 0.0, phase: float = 0.0) -> str:
    ri = r * (1 - depth)
    step = 2 * math.pi / teeth
    pts = []
    for i in range(teeth):
        a0 = phase + step * i
        for frac, rad in ((0.0, ri), (0.13, r), (0.41, r), (0.54, ri)):
            a = a0 + step * frac
            pts.append((cx + math.cos(a) * rad, cy + math.sin(a) * rad))
    d = "M" + "L".join(f"{x:.2f} {y:.2f}" for x, y in pts) + "Z"
    if hole > 0:
        d += (f"M{cx + hole:.2f} {cy:.2f}A{hole:.2f} {hole:.2f} 0 1 0 {cx - hole:.2f} {cy:.2f}"
              f"A{hole:.2f} {hole:.2f} 0 1 0 {cx + hole:.2f} {cy:.2f}Z")
    return d


def _hazard(s: Svg, x: float, y: float, w: float, h: float, step: float = 6.0) -> None:
    """Yellow-black diagonal stripes inside a rectangle (stripes clipped by hand)."""
    s.rect(x, y, w, h, fill=HAZARD_Y)
    d = ""
    a = x - h
    while a < x + w:
        pts = []
        for px, py in ((a, y + h), (a + step, y + h), (a + step + h, y), (a + h, y)):
            pts.append((min(max(px, x), x + w), py))
        if pts[1][0] - pts[0][0] > 0.01 or pts[2][0] - pts[3][0] > 0.01:
            d += "M" + "L".join(f"{px:.2f} {py:.2f}" for px, py in pts) + "Z"
        a += step * 2
    s.path(d, fill=HAZARD_K)


# =========================================================================== Robô de Ronda
@register("patrol_bot")
class PatrolBot(CreatureRig):
    """Tin automaton with a spinning gyroscope on its head and a caged chest
    lantern; no wind-up key anywhere — it runs on its gyroscope."""

    du = 0.36
    ALERT = 0.45  # walker alert duration (lume/core/behaviors/ground.py)

    def parts(self):
        def body():
            s = Svg(84, 62)
            pts = [(12, 3), (42, 1), (72, 3), (82, 18), (83, 34), (80, 51), (66, 59), (42, 60), (18, 59), (4, 51), (1, 34), (2, 18)]
            s.path(smooth_closed(pts, 0.85), fill=s.radial(26, 14, 66, [(0, TIN_HI), (0.35, TIN_LIGHT), (0.75, TIN), (1, TIN_DARK)]), stroke=INK,
                   width=2.0)
            # brass waist band
            s.path("M2.2 42 Q42 47 81.8 42 L81 50 Q42 55 3 50 Z", fill=s.linear(0, 42, 0, 52, [(0, BRASS_LIGHT), (0.5, BRASS), (1, BRASS_DARK)]),
                   stroke=INK, width=1.0)
            for k in range(7):
                x = 10 + k * 10.6
                _rivet(s, x, 46.5 + 1.4 * math.sin(math.pi * x / 84), 1.2, body=BRASS_LIGHT, rim=BRASS_DEEP, hi=BRASS_HI)
            # panel seam and back vent grille (no key)
            s.path("M30 5 Q28 24 30 42", stroke=TIN_DARK, width=1.2, opacity=0.8)
            for y in (12, 24, 36):
                s.circle(30.5, y, 1.0, fill=TIN_DEEP)
            for y in (15, 21, 27, 33):
                s.path(rounded_rect_path(8, y, 13, 2.8, 1.4), fill=TIN_DEEP)
            # lantern porthole bezel (the glass is a separate part)
            s.circle(54, 25, 15, fill=s.linear(40, 12, 68, 40, [(0, BRASS_HI), (0.45, BRASS), (1, BRASS_DEEP)]), stroke=INK, width=1.4)
            s.circle(54, 25, 11, fill="#1a1216")
            for a in range(6):
                ang = a * math.pi / 3 + 0.5
                s.circle(54 + math.cos(ang) * 13, 25 + math.sin(ang) * 13, 0.9, fill=BRASS_DEEP)
            s.path("M8 16 Q12 7 22 5", stroke="#ffffff", width=2.2, opacity=0.65)
            s.path("M66 56 Q76 52 80 42", stroke=TIN_DEEP, width=1.6, opacity=0.5)
            return s

        def head():
            s = Svg(56, 30)
            s.path("M4 27 L4 17 Q4 2 28 2 Q52 2 52 17 L52 27 Z", fill=s.radial(18, 8, 44, [(0, TIN_HI), (0.4, TIN_LIGHT), (1, TIN_DARK)]), stroke=INK,
                   width=1.8)
            s.path(rounded_rect_path(22, 9, 32, 13, 6), fill=s.linear(0, 9, 0, 22, [(0, "#3a4a5e"), (1, "#141a26")]), stroke=INK, width=1.2)
            s.path("M25 11.5 L50 11.5", stroke="#9ad8e8", width=0.9, opacity=0.5)
            s.path(rounded_rect_path(2, 24, 52, 5.5, 2.5), fill=s.linear(0, 24, 0, 30, [(0, BRASS_LIGHT), (1, BRASS_DARK)]), stroke=INK, width=1.0)
            _rivet(s, 11, 16, 1.6, body=TIN_LIGHT)
            s.path(rounded_rect_path(24, 0, 8, 4, 1.5), fill=BRASS, stroke=INK, width=0.8)
            s.path("M9 12 Q12 6 19 4.5", stroke="#ffffff", width=1.6, opacity=0.7)
            return s

        def eye(alert: bool):
            s = Svg(10, 10)
            if alert:
                s.circle(5, 5, 4.6, fill=s.radial(5, 5, 4.6, [(0, "#ffffff"), (0.55, "#fff2c0"), (1, LAMP_DEEP)]))
                s.circle(5, 5, 4.6, fill=None, stroke="#ff6a3a", width=0.8)
            else:
                s.circle(5, 5, 3.7, fill=s.radial(4.2, 4.2, 4.4, [(0, "#ffffff"), (0.35, "#ffe9a6"), (1, "#f0952e")]))
                s.circle(3.8, 3.6, 1.0, fill="#ffffff")
            return s

        def leg():
            s = Svg(14, 22)
            s.path(rounded_rect_path(3.5, 2, 7, 19, 3), fill=s.linear(3.5, 0, 10.5, 0, [(0, STEEL_LIGHT), (1, STEEL_DARK)]), stroke=INK, width=1.2)
            for y in (10.0, 14.0):
                s.line(3.8, y, 10.2, y, STEEL_DEEP, 0.9, 0.8)
            s.circle(7, 3.4, 4.2, fill=s.radial(6, 2.4, 5, [(0, BRASS_HI), (1, BRASS_DARK)]), stroke=INK, width=1.0)
            s.line(5, 8, 5, 19, "#ffffff", 0.8, 0.5)
            return s

        def foot():
            s = Svg(24, 11)
            s.path("M2 10 L2 6 Q2 2 8 2 L15 2 Q22 2 23 8 L23 10 Z", fill=s.linear(0, 2, 0, 10, [(0, STEEL), (1, STEEL_DEEP)]), stroke=INK, width=1.2)
            s.line(4, 4.2, 14, 4.2, STEEL_HI, 0.9, 0.7)
            return s

        def arm():
            s = Svg(16, 28)
            s.path(rounded_rect_path(5, 3, 6, 16, 3), fill=s.linear(5, 0, 11, 0, [(0, TIN_LIGHT), (1, TIN_DARK)]), stroke=INK, width=1.1)
            s.circle(8, 4.5, 3.8, fill=s.radial(7, 3.5, 4.4, [(0, BRASS_HI), (1, BRASS_DARK)]), stroke=INK, width=0.9)
            s.path("M8 18 Q2 21 3.5 26.5 M8 18 Q14 21 12.5 26.5", stroke=INK, width=3.0)
            s.path("M8 18 Q2 21 3.5 26.5 M8 18 Q14 21 12.5 26.5", stroke=STEEL_LIGHT, width=1.5)
            s.circle(8, 18.5, 2.4, fill=STEEL, stroke=INK, width=0.8)
            return s

        def gyro_post():
            s = Svg(8, 14)
            s.path(rounded_rect_path(2.6, 3, 2.8, 11, 1.2), fill=s.linear(2.6, 0, 5.4, 0, [(0, STEEL_HI), (1, STEEL_DARK)]), stroke=INK, width=0.8)
            return s

        def ring(color: str, dark: str):
            s = Svg(26, 26)
            s.circle(13, 13, 10.8, fill=None, stroke=INK, width=3.6)
            s.circle(13, 13, 10.8, fill=None, stroke=color, width=2.2)
            s.path("M5.4 7.6 A10.8 10.8 0 0 1 13 2.2", stroke="#ffffff", width=0.9, opacity=0.8)
            for a in (0, math.pi):
                s.circle(13 + math.cos(a) * 10.8, 13 + math.sin(a) * 10.8, 1.7, fill=dark, stroke=INK, width=0.6)
            return s

        def core():
            s = Svg(10, 10)
            s.circle(5, 5, 3.8, fill=s.radial(4, 4, 4.4, [(0, "#ffffff"), (0.5, STEEL_LIGHT), (1, STEEL_DARK)]), stroke=INK, width=0.9)
            return s

        def lamp(on: bool):
            s = Svg(24, 24)
            if on:
                s.circle(12, 12, 11, fill=s.radial(10.5, 10.5, 11.5, [(0, "#ffffff"), (0.35, LAMP_HOT), (0.7, LAMP), (1, LAMP_DEEP)]))
            else:
                s.circle(12, 12, 11, fill=s.radial(9, 9, 12, [(0, "#5a5662"), (1, "#1e1a24")]))
                s.path("M7 8 L13 13 L10 17", stroke="#a8a4b4", width=0.7, opacity=0.7)
            return s

        def cage():
            s = Svg(24, 24)
            s.path("M8 2.5 L8 21.5 M16 2.5 L16 21.5 M1.5 12 L22.5 12", stroke=INK, width=2.2)
            s.path("M8 2.5 L8 21.5 M16 2.5 L16 21.5 M1.5 12 L22.5 12", stroke=BRASS_DARK, width=1.1)
            s.path("M6 7 Q9 4 12 3.6", stroke="#ffffff", width=1.0, opacity=0.7)
            return s

        def beam():
            s = Svg(150, 76)
            s.path("M2 38 L150 0 L150 76 Z", fill=s.linear(0, 0, 150, 0, [(0, "#fff6d8", 0.75), (0.25, LAMP, 0.42), (1, LAMP, 0)]))
            s.path("M2 38 L150 22 L150 54 Z", fill=s.linear(0, 0, 150, 0, [(0, "#ffffff", 0.7), (0.4, "#fff2c8", 0.3), (1, "#fff2c8", 0)]))
            return s

        return {
            "body": (body, (42, 60)), "head": (head, (28, 27)), "eye": (lambda: eye(False), (5, 5)), "eye_alert": (lambda: eye(True), (5, 5)),
            "eye_x": (lambda: _eye_x_svg(8), (4, 4)), "leg": (leg, (7, 3)), "foot": (foot, (11, 9.5)), "arm": (arm, (8, 4.5)),
            "gyro_post": (gyro_post, (4, 14)), "ring": (lambda: ring(BRASS_LIGHT, BRASS_DEEP), (13, 13)),
            "ring_b": (lambda: ring(COPPER_LIGHT, COPPER_DARK), (13, 13)), "core": (core, (5, 5)),
            "lamp_on": (lambda: lamp(True), (12, 12)), "lamp_off": (lambda: lamp(False), (12, 12)), "cage": (cage, (12, 12)),
            "halo": (lambda: _halo_svg(70, LAMP, 0.65), (35, 35)), "beam": (beam, (2, 38)),
        }

    def commands(self, e, t):
        root = _root(self, e)
        out: list[DrawCommand] = []
        alive = e.alive
        walk = alive and e.anim == "walk"
        alert = alive and e.anim == "alert"
        ph = t * 9.0
        swing = math.sin(ph) if walk else 0.0
        bob = -abs(math.sin(ph)) * 1.8 if walk else 0.0
        k = 0.0
        if alert:
            left = e.memory.get("alert")
            k = _clamp(1 - left / self.ALERT) if isinstance(left, (int, float)) else (e.state_time % self.ALERT) / self.ALERT
        tilt = swing * 2.5 - (5 * math.sin(math.pi * k) if alert else 0.0)
        # legs and feet
        for side, sgn in ((-1, 1), (1, -1)):
            lift = max(0.0, sgn * math.sin(ph)) * 4 if walk else 0.0
            fx = side * 12 + (sgn * math.sin(ph) * 4 if walk else 0.0)
            out.append(self.cmd("leg", root.child(fx * 0.85, -19 - lift, -sgn * swing * 10)))
            out.append(self.cmd("foot", root.child(fx, -lift)))
        body = root.child(0, -15 + bob, tilt)
        # far arm behind the body
        arm_a = swing * 22 if walk else (-35 * math.sin(math.pi * k) if alert else math.sin(t * 2) * 4)
        out.append(self.cmd("arm", body.child(14, -40, 8 - arm_a), tint=(196, 196, 210)))
        out.append(self.cmd("body", body))
        # chest lantern (the alert telegraph): halo, glass, cage, sweeping beam
        lamp = body.child(12, -35)
        if alive:
            glow = 0.55 + 0.1 * math.sin(t * 3) if not alert else 0.8 + 0.2 * math.sin(math.pi * k)
            out.append(self.cmd("halo", lamp, alpha=glow * (0.6 if not alert else 1.0), scale=1.0 if not alert else 1.35))
            out.append(self.cmd("lamp_on", lamp))
        else:
            out.append(self.cmd("lamp_off", lamp))
        out.append(self.cmd("cage", lamp))
        # head with visor eyes, gyroscope on top
        nod = (-8 * math.sin(2 * math.pi * k) if alert else -swing * 1.5)
        head = body.child(0, -57, nod)
        out.append(self.cmd("head", head))
        if alive:
            eye = "eye_alert" if alert else "eye"
            closed = self.blink(t, e.origin_x * 0.31) and not alert
            for ex in (7.0, 17.5):
                out.append(self.cmd(eye, head.child(ex, -11.5), scale=0.25 if closed else 1.0))
        else:
            for ex in (7.0, 17.5):
                out.append(self.cmd("eye_x", head.child(ex, -11.5)))
        post = head.child(0, -25)
        out.append(self.cmd("gyro_post", post))
        spin = t * (26.0 if alert else 9.0) if alive else 0.7
        hub = post.child(0, -22)
        sa, sb = abs(math.cos(spin)), abs(math.sin(spin))
        out.append(self.cmd("ring_b", _at(hub, 0, 0, 0, max(0.1, sb), 1.0)))
        out.append(self.cmd("ring", _at(hub, 0, 0, 0, max(0.1, sa), 1.0)))
        out.append(self.cmd("core", hub))
        # near arm in front
        out.append(self.cmd("arm", body.child(-16, -40, -8 + arm_a)))
        if alert:
            sweep = 12 * math.cos(2 * math.pi * k) - 4
            out.append(self.cmd("beam", lamp.child(0, 0, sweep), alpha=_clamp(k * 6) * (1 - _clamp((k - 0.85) / 0.15))))
        return _flash(e, t, out)


# =========================================================================== Canhão Sentinela
def _cannon_interval(e) -> float:
    """Firing interval of this launcher (per-instance param, else the species')."""
    if "interval" in e.params:
        return float(e.params["interval"])
    try:
        from ...core.species import load_profiles

        return float(load_profiles()[e.species].params.get("interval", 3.0))
    except Exception:  # pragma: no cover - art must never crash the game
        return 3.0


@register("cannon")
class SteamCannon(CreatureRig):
    """Brass steam mortar on a cog carriage. The barrel axis sits exactly at
    the height where the behaviour spawns its shot; the muzzle reaches the
    hitbox edge on the facing side."""

    du = 0.4
    CHARGE = 0.5  # last part of the interval spent charging (behaviour)
    FIRE = 0.3

    def parts(self):
        def plinth():
            s = Svg(96, 22)
            s.path("M4 21 L10 6 Q11 3 14 3 L82 3 Q85 3 86 6 L92 21 Z", fill=s.linear(0, 3, 0, 21, [(0, IRON_HI), (0.3, IRON), (1, IRON_DEEP)]), stroke=INK,
                   width=1.6)
            s.line(12, 5, 84, 5, "#c8c6d4", 1.0, 0.7)
            for x in (18, 34, 50, 66, 80):
                _rivet(s, x, 12, 1.4, body=IRON_HI, rim=IRON_DEEP)
            s.path("M8 17 L88 17", stroke=IRON_DEEP, width=1.2, opacity=0.8)
            return s

        def cog():
            s = Svg(62, 62)
            body = _gear_d(31, 31, 29, 12, 0.2, hole=6)
            win = ""
            for i in range(5):
                a0, a1 = 2 * math.pi * i / 5 + 0.28, 2 * math.pi * (i + 1) / 5 - 0.28
                pts = [(31 + math.cos(a0) * 9, 31 + math.sin(a0) * 9)]
                for j in range(5):
                    a = a0 + (a1 - a0) * j / 4
                    pts.append((31 + math.cos(a) * 18.5, 31 + math.sin(a) * 18.5))
                pts.append((31 + math.cos(a1) * 9, 31 + math.sin(a1) * 9))
                win += "M" + "L".join(f"{x:.2f} {y:.2f}" for x, y in reversed(pts)) + "Z"
            s.path(body + win, fill=s.linear(4, 4, 58, 58, [(0, BRASS_HI), (0.35, BRASS_LIGHT), (0.7, BRASS), (1, BRASS_DARK)]), stroke=INK, width=1.6)
            s.circle(31, 31, 21.5, fill=None, stroke=BRASS_DEEP, width=1.0, opacity=0.6)
            s.path("M10 20 A23 23 0 0 1 22 8", stroke="#ffffff", width=1.6, opacity=0.7)
            return s

        def barrel():
            s = Svg(76, 46)
            # breech knob, chamber, bands, flared muzzle and dark bore
            s.circle(7, 23, 6, fill=s.radial(5, 21, 7, [(0, BRASS_HI), (1, BRASS_DARK)]), stroke=INK, width=1.3)
            body = "M10 10 Q12 8 16 8 L48 10 Q56 10 62 4 L70 2 Q74 2 74 6 L74 40 Q74 44 70 44 L62 42 Q56 36 48 36 L16 38 Q12 38 10 36 Z"
            s.path(body, fill=s.linear(0, 2, 0, 44, [(0, BRASS_HI), (0.22, BRASS_LIGHT), (0.55, BRASS), (0.85, BRASS_DARK), (1, BRASS_DEEP)]),
                   stroke=INK, width=1.7)
            for x0 in (20.0, 38.0):
                s.path(f"M{x0} 8.4 L{x0 + 6} 8.6 L{x0 + 6} 37.4 L{x0} 37.6 Z", fill=s.linear(0, 8, 0, 38, [(0, COPPER_HI), (0.4, COPPER), (1, COPPER_DARK)]),
                       stroke=INK, width=1.0)
                for y in (14, 23, 32):
                    s.circle(x0 + 3, y, 0.95, fill=COPPER_HI)
            s.ellipse(72, 23, 3.4, 19, fill=s.linear(0, 4, 0, 42, [(0, "#3a2a24"), (1, "#0e0a0c")]), stroke=INK, width=1.0)
            s.path("M14 13 L46 14 Q55 13 62 8", stroke="#ffffff", width=1.8, opacity=0.6)
            s.path("M64 5 L71 4", stroke="#ffffff", width=1.2, opacity=0.7)
            return s

        def boiler():
            s = Svg(32, 52)
            s.path(rounded_rect_path(4, 8, 24, 43, 10), fill=s.linear(4, 0, 28, 0, [(0, COPPER_DARK), (0.3, COPPER_LIGHT), (0.6, COPPER), (1, COPPER_DARK)]),
                   stroke=INK, width=1.5)
            for y in (18, 40):
                s.line(4.5, y, 27.5, y, COPPER_DARK, 1.3, 0.9)
                for x in (8, 14, 20, 26):
                    s.circle(x - 1, y + 2, 0.8, fill=COPPER_HI)
            s.rect(13, 2, 6, 8, fill=s.linear(13, 0, 19, 0, [(0, STEEL_HI), (1, STEEL_DARK)]), stroke=INK, width=0.9)
            # gauge face (the needle is a separate part)
            s.circle(16, 29, 7, fill=s.linear(9, 22, 23, 36, [(0, BRASS_HI), (1, BRASS_DEEP)]), stroke=INK, width=1.0)
            s.circle(16, 29, 5.2, fill="#fbf3dc")
            s.path("M19.6 25.8 A5 5 0 0 1 21 30", stroke="#d8402e", width=1.4)
            for a in range(5):
                ang = math.radians(-120 + a * 60)
                s.line(16 + math.sin(ang) * 3.6, 29 - math.cos(ang) * 3.6, 16 + math.sin(ang) * 4.8, 29 - math.cos(ang) * 4.8, "#3a2a2a", 0.6)
            s.path("M7 14 Q8 10 12 9", stroke="#ffffff", width=1.4, opacity=0.6)
            return s

        def needle():
            s = Svg(4, 10)
            s.path("M2 1 L3 8.5 L1 8.5 Z", fill="#b8241c")
            s.circle(2, 8.5, 1.2, fill=INK)
            return s

        def valve(hot: bool):
            s = Svg(18, 18)
            rim = s.radial(9, 9, 8, [(0, HOT_WHITE), (0.5, HOT_YELLOW), (1, HOT_ORANGE)]) if hot else "#c8382c"
            spoke = HOT_RED if hot else "#6a1a16"
            s.circle(9, 9, 7, fill=None, stroke=INK, width=3.2)
            s.circle(9, 9, 7, fill=None, stroke=rim, width=2.0)
            d = "".join(f"M9 9L{9 + math.cos(a) * 7:.2f} {9 + math.sin(a) * 7:.2f}" for a in (0.3, 1.55, 2.8, 4.05, 5.3))
            s.path(d, stroke=INK, width=1.8)
            s.path(d, stroke=spoke, width=0.9)
            s.circle(9, 9, 2.2, fill=rim, stroke=INK, width=0.7)
            return s

        def flash_svg():
            s = Svg(48, 48)
            s.circle(24, 24, 24, fill=s.radial(24, 24, 24, [(0, "#ffffff", 0.95), (0.3, HOT_YELLOW, 0.7), (1, HOT_ORANGE, 0)]))
            s.polygon(star_points(24, 24, 22, 6, 6, 0), fill="#fff6d0", opacity=0.9)
            return s

        def bore_svg():
            s = Svg(7, 38)
            s.ellipse(3.5, 19, 3.4, 18.4, fill=s.radial(3.5, 19, 18, [(0, HOT_WHITE), (0.35, HOT_YELLOW), (0.75, HOT_ORANGE), (1, HOT_RED)]))
            return s

        return {
            "plinth": (plinth, (48, 21)), "cog": (cog, (31, 31)), "barrel": (barrel, (24, 23)), "boiler": (boiler, (16, 51)),
            "needle": (needle, (2, 8.5)), "valve": (lambda: valve(False), (9, 9)), "valve_hot": (lambda: valve(True), (9, 9)),
            "glow": (lambda: _halo_svg(56, HOT_ORANGE, 0.7), (28, 28)), "puff": (lambda: _puff_svg(20), (10, 9)),
            "smoke": (lambda: _puff_svg(24, dark=True), (12, 10)), "muzzle": (flash_svg, (24, 24)), "bore": (bore_svg, (3.5, 19)),
        }

    def commands(self, e, t):
        root = _root(self, e)
        out: list[DrawCommand] = []
        anim = e.anim if e.alive else "idle"
        charge = fire = 0.0
        if anim == "charge":
            interval = _cannon_interval(e)
            charge = _clamp(1 - (interval - e.timer % interval) / self.CHARGE)
        elif anim == "fire":
            left = e.memory.get("fired", 0.0)
            fire = _clamp(1 - float(left) / self.FIRE) if isinstance(left, (int, float)) else 0.5
        shudder = math.sin(t * 70) * 1.2 * charge if anim == "charge" else 0.0
        recoil = (1 - _ease(fire / 0.6)) if anim == "fire" else 0.0
        # boiler behind the carriage: gauge climbs while charging, valve glows
        boiler = root.child(-30, -16)
        out.append(self.cmd("boiler", boiler))
        needle = -100 + 200 * (charge if anim == "charge" else (1 - fire if anim == "fire" else 0.08 + 0.04 * math.sin(t * 2)))
        out.append(self.cmd("needle", boiler.child(0, -22, needle), scale=0.9))
        valve = boiler.child(0, -50)
        if anim == "charge":
            out.append(self.cmd("glow", valve, alpha=0.3 + 0.7 * charge, scale=0.6 + 0.8 * charge))
            out.append(self.cmd("valve_hot", valve, alpha=1.0))
        elif anim == "fire":
            out.append(self.cmd("glow", valve, alpha=0.8 * (1 - fire), scale=1.2))
            out.append(self.cmd("valve_hot", valve, alpha=1 - fire))
        else:
            out.append(self.cmd("valve", valve))
        # cog carriage turns a little as the barrel is laid
        cog_angle = (charge * 40 if anim == "charge" else 40 * (1 - fire) if anim == "fire" else 0.0) + shudder * 2
        trunnion = root.child(-4 + shudder * 0.4, -42)
        out.append(self.cmd("cog", trunnion.child(0, 0, cog_angle)))
        out.append(self.cmd("plinth", root))
        barrel_angle = -2 * charge + shudder - 7 * recoil
        barrel = trunnion.child(-7 * recoil, 0, barrel_angle)
        out.append(self.cmd("barrel", barrel))
        if anim == "charge":
            bore = barrel.child(48, 0)
            out.append(self.cmd("glow", bore, alpha=0.2 + 0.8 * charge, scale=0.4 + 0.7 * charge))
            out.append(self.cmd("bore", bore, alpha=_ease(charge * 1.4)))
        # steam: wisps at idle, hissing jets while charging, a blast when firing
        if e.alive and anim == "idle":
            kk = (t * 0.45 + e.origin_x * 0.013) % 1.0
            if kk < 0.4:
                q = kk / 0.4
                out.append(self.cmd("puff", valve.child(2 + q * 6, -6 - q * 16), scale=0.35 + 0.4 * q, alpha=0.8 * (1 - q)))
        elif anim == "charge":
            for j in range(3):
                q = (t * 3.2 + j / 3) % 1.0
                out.append(self.cmd("puff", valve.child(-4 + j * 5 + q * 4, -5 - q * 22), scale=(0.35 + 0.5 * q) * (0.6 + 0.6 * charge),
                                    alpha=(1 - q) * (0.4 + 0.6 * charge)))
            q = (t * 5) % 1.0
            out.append(self.cmd("puff", trunnion.child(-24 - q * 10, -10 - q * 6), scale=0.3 + 0.4 * q, alpha=(1 - q) * charge))
        elif anim == "fire":
            muzzle = trunnion.child(46 - 7 * recoil, 0)
            if fire < 0.4:
                out.append(self.cmd("muzzle", muzzle.child(4, 0), scale=0.7 + 0.6 * fire, alpha=1 - fire / 0.4))
            for j in range(3):
                q = _clamp(fire * 1.2 + j * 0.12)
                out.append(self.cmd("smoke" if j == 1 else "puff", muzzle.child(4 + q * 14 + j * 3, -4 - q * (8 + j * 6) + j * 4),
                                    scale=0.6 + 0.9 * q, alpha=(1 - q) * 0.95))
            out.append(self.cmd("puff", valve.child(4 + fire * 6, -8 - fire * 20), scale=0.5 + 0.6 * fire, alpha=1 - fire))
        return _flash(e, t, out)


# =========================================================================== Drone Vigia
@register("drone")
class Drone(CreatureRig):
    """Tin pod on twin rotors with one camera eye: a calm cyan iris on patrol,
    a red pinpoint once it has locked on."""

    du = 0.4

    def parts(self):
        def body():
            s = Svg(84, 50)
            # tail fin with a navigation light
            s.path("M14 18 L2 6 L8 5 L22 15 Z", fill=s.linear(0, 5, 0, 18, [(0, COPPER_LIGHT), (1, COPPER_DARK)]), stroke=INK, width=1.2)
            s.path("M14 32 L4 42 L10 43 L22 34 Z", fill=s.linear(0, 32, 0, 43, [(0, COPPER), (1, COPPER_DARK)]), stroke=INK, width=1.2)
            s.circle(4.5, 6.5, 2.2, fill="#ff5a4a", stroke=INK, width=0.6)
            pod = "M12 25 C12 10 30 4 48 4 C66 4 80 12 80 25 C80 38 66 46 48 46 C30 46 12 40 12 25 Z"
            s.path(pod, fill=s.radial(34, 14, 56, [(0, TIN_HI), (0.35, TIN_LIGHT), (0.75, TIN), (1, TIN_DARK)]), stroke=INK, width=1.9)
            s.path("M12.6 27 C30 33 62 33 79.4 27 L79 31 C62 37 30 37 13 31 Z", fill=s.linear(0, 27, 0, 37, [(0, BRASS_LIGHT), (1, BRASS_DARK)]),
                   stroke=INK, width=0.9)
            for x in (22, 34, 46, 58, 70):
                s.circle(x, 30.4 + 1.6 * math.sin(math.pi * (x - 12) / 68), 0.95, fill=BRASS_HI)
            # rotor arm across the top
            s.path(rounded_rect_path(18, 2, 50, 6, 3), fill=s.linear(0, 2, 0, 8, [(0, STEEL_LIGHT), (1, STEEL_DARK)]), stroke=INK, width=1.1)
            s.path("M22 14 Q30 8 42 7.5", stroke="#ffffff", width=1.8, opacity=0.7)
            s.path("M24 20 L36 20 M24 23.5 L34 23.5", stroke=TIN_DARK, width=1.2, opacity=0.8)
            return s

        def mast():
            s = Svg(8, 16)
            s.path(rounded_rect_path(2.6, 2, 2.8, 14, 1.2), fill=s.linear(2.6, 0, 5.4, 0, [(0, STEEL_HI), (1, STEEL_DARK)]), stroke=INK, width=0.8)
            s.circle(4, 3, 2.6, fill=BRASS, stroke=INK, width=0.8)
            return s

        def disc():
            s = Svg(40, 10)
            s.ellipse(20, 5, 19, 3.6, fill=s.radial(20, 5, 19, [(0, "#ffffff", 0.0), (0.6, "#e8eef6", 0.35), (1, "#c8d2e0", 0.55)]))
            s.ellipse(20, 5, 19, 3.6, fill=None, stroke="#ffffff", width=0.8, opacity=0.6)
            return s

        def blade():
            s = Svg(40, 6)
            s.path("M2 3 Q10 0.6 20 2.4 Q30 0.6 38 3 Q30 5.4 20 3.6 Q10 5.4 2 3 Z", fill=s.linear(0, 0, 0, 6, [(0, STEEL_LIGHT), (1, STEEL_DEEP)]),
                   stroke=INK, width=0.8)
            return s

        def lens(mode: str):
            s = Svg(28, 28)
            s.circle(14, 14, 12.5, fill=s.linear(2, 2, 26, 26, [(0, BRASS_HI), (0.5, BRASS), (1, BRASS_DEEP)]), stroke=INK, width=1.5)
            s.circle(14, 14, 9.6, fill=s.radial(12, 11, 11, [(0, "#3a4a5a"), (1, "#0c1016")]))
            if mode == "calm":
                s.circle(14, 14, 6.2, fill=s.radial(14, 14, 6.2, [(0, "#ffffff"), (0.3, LENS_CALM), (1, "#1a8a80")]))
                blades = "".join(f"M{14 + math.cos(a) * 2.8:.2f} {14 + math.sin(a) * 2.8:.2f}L{14 + math.cos(a + 0.9) * 6.2:.2f} {14 + math.sin(a + 0.9) * 6.2:.2f}"
                                 for a in [i * math.pi / 3 for i in range(6)])
                s.path(blades, stroke="#0e4a46", width=0.7, opacity=0.8)
                s.circle(14, 14, 2.4, fill="#0a1a1a")
            elif mode == "alert":
                s.circle(14, 14, 8, fill=s.radial(14, 14, 8, [(0, LENS_ALERT, 0.85), (1, LENS_ALERT, 0)]))
                s.circle(14, 14, 3.2, fill=s.radial(14, 14, 3.2, [(0, "#ffffff"), (0.45, "#ffb0a0"), (1, LENS_ALERT)]))
                blades = "".join(f"M{14 + math.cos(a) * 3.4:.2f} {14 + math.sin(a) * 3.4:.2f}L{14 + math.cos(a + 1.2) * 9:.2f} {14 + math.sin(a + 1.2) * 9:.2f}"
                                 for a in [i * math.pi / 3 for i in range(6)])
                s.path(blades, stroke="#3a0a0a", width=1.1)
            else:
                s.path("M9 9 L14 15 L11 20 M14 15 L20 12", stroke="#8a96a8", width=0.9)
            s.path("M6.5 9 A9 9 0 0 1 13 5", stroke="#ffffff", width=1.4, opacity=0.85)
            return s

        def claw():
            s = Svg(14, 16)
            s.path(rounded_rect_path(5, 0, 4, 6, 1.5), fill=STEEL_DARK, stroke=INK, width=0.8)
            s.path("M7 5 Q1 8 3 14 M7 5 Q13 8 11 14", stroke=INK, width=2.6)
            s.path("M7 5 Q1 8 3 14 M7 5 Q13 8 11 14", stroke=STEEL_LIGHT, width=1.2)
            return s

        return {
            "body": (body, (46, 25)), "mast": (mast, (4, 16)), "disc": (disc, (20, 5)), "blade": (blade, (20, 3)),
            "lens": (lambda: lens("calm"), (14, 14)), "lens_alert": (lambda: lens("alert"), (14, 14)), "lens_dead": (lambda: lens("dead"), (14, 14)),
            "glow_calm": (lambda: _halo_svg(56, LENS_CALM, 0.45), (28, 28)), "glow_alert": (lambda: _halo_svg(64, LENS_ALERT, 0.7), (32, 32)),
            "claw": (claw, (7, 1)), "streak": (lambda: _streak_svg(40), (3, 40)), "puff": (lambda: _puff_svg(18), (9, 8)),
        }

    def commands(self, e, t):
        root = _root(self, e)
        out: list[DrawCommand] = []
        alive = e.alive
        state = e.anim if alive else "defeat"
        st = e.state_time
        hover = math.sin(t * 3.1 + e.origin_x * 0.01) * 1.6 if state in ("perch", "alert") else 0.0
        tilt = {"perch": math.sin(t * 1.7) * 3, "alert": 10 * _ease(st / 0.25) + math.sin(t * 40) * 1.2, "dive": 26.0, "climb": -16.0}.get(state, 0.0)
        body = root.child(0, -27 + hover, tilt)
        spin_rate = {"climb": 70.0, "dive": 34.0, "alert": 60.0}.get(state, 46.0)
        # rotors behind the body
        for mx in (-17.0, 15.0):
            mast = body.child(mx, -17)
            out.append(self.cmd("mast", mast))
            hub = mast.child(0, -15)
            if alive:
                out.append(self.cmd("disc", hub, alpha=0.85 if state != "climb" else 1.0))
                ph = t * spin_rate + mx
                out.append(self.cmd("blade", _at(hub, 0, -0.5, 0, max(0.08, abs(math.cos(ph))), 1.0)))
            else:
                out.append(self.cmd("blade", hub.child(0, -0.5, 8)))
        # claws: folded on patrol, open in the dive
        claw_a = {"dive": -55.0, "alert": -20.0}.get(state, 0.0)
        for cx, sgn in ((-6.0, 1), (10.0, -1)):
            out.append(self.cmd("claw", body.child(cx, 18, claw_a + sgn * (6 if state == "dive" else 0)), tint=(205, 205, 215) if sgn > 0 else None))
        out.append(self.cmd("body", body))
        lens = body.child(22, 6)
        if not alive:
            out.append(self.cmd("lens_dead", lens))
        elif state in ("alert", "dive"):
            focus = _ease(st / 0.3) if state == "alert" else 1.0
            out.append(self.cmd("glow_alert", lens, alpha=0.4 + 0.6 * focus, scale=1.3 - 0.4 * focus))
            out.append(self.cmd("lens_alert", lens, scale=1.0 + 0.12 * (1 - focus)))
        else:
            warm = _clamp(st / 0.6) if state == "climb" else 1.0
            out.append(self.cmd("glow_calm", lens, alpha=0.35 * warm + 0.1 * math.sin(t * 4)))
            out.append(self.cmd("lens", lens))
        if state == "dive":
            for j, sx in enumerate((-30.0, -12.0, 6.0)):
                out.append(self.cmd("streak", body.child(sx, -18 - j * 4, -tilt - 35), alpha=0.6, scale=0.8 + 0.2 * j))
        elif state == "climb":
            for j in range(2):
                q = (t * 3.5 + j * 0.5) % 1.0
                out.append(self.cmd("puff", body.child(-8 + j * 12 - q * 6, 22 + q * 16), scale=0.4 + 0.5 * q, alpha=0.8 * (1 - q)))
        return _flash(e, t, out)


# =========================================================================== Prensa a Vapor
@register("steam_press")
class SteamPress(CreatureRig):
    """Faceless press ram: brass top plate flush with the hitbox top (a safe
    platform), riveted ribs, a hazard band and a hardened die. Two hydraulic
    cylinders stay at the resting height while their chrome rods extend."""

    du = 0.5

    def parts(self):
        def head():
            s = Svg(96, 84)
            # body block with stiffener ribs
            s.path("M6 12 L90 12 L90 58 L6 58 Z", fill=s.linear(0, 12, 0, 58, [(0, STEEL), (0.5, STEEL_DARK), (1, STEEL_DEEP)]), stroke=INK, width=1.6)
            for x in (22.0, 48.0, 74.0):
                s.path(f"M{x - 4:.1f} 12 L{x + 4:.1f} 12 L{x + 4:.1f} 58 L{x - 4:.1f} 58 Z",
                       fill=s.linear(x - 4, 0, x + 4, 0, [(0, STEEL_HI), (0.4, STEEL_LIGHT), (1, STEEL_DARK)]), stroke=INK, width=1.1)
                for y in (20.0, 34.0, 48.0):
                    _rivet(s, x, y, 1.2, body=STEEL_LIGHT, rim=STEEL_DEEP)
            # side steam ports
            for x in (6.0, 90.0):
                s.path(rounded_rect_path(x - 4, 26, 8, 12, 2.5), fill=s.linear(x - 4, 0, x + 4, 0, [(0, BRASS_LIGHT), (1, BRASS_DARK)]), stroke=INK,
                       width=1.0)
                s.circle(x, 32, 1.6, fill="#1a1216")
            # hazard band
            _hazard(s, 4, 58, 88, 9, step=6.0)
            s.path("M4 58 L92 58 L92 67 L4 67 Z", fill=None, stroke=INK, width=1.3)
            # striking die
            s.path("M8 67 L88 67 L86 80 Q86 82 84 82 L12 82 Q10 82 10 80 Z", fill=s.linear(0, 67, 0, 82, [(0, STEEL_DARK), (0.5, STEEL_DEEP), (1, "#14161e")]),
                   stroke=INK, width=1.5)
            s.line(12, 80.6, 84, 80.6, STEEL_LIGHT, 1.1, 0.8)
            s.line(10, 70, 86, 70, "#6a7088", 0.9, 0.7)
            # brass top plate: the safe, walkable top (flush with the hitbox top at y=2)
            s.path(rounded_rect_path(1.5, 2, 93, 11, 2.5), fill=s.linear(0, 2, 0, 13, [(0, BRASS_HI), (0.3, BRASS_LIGHT), (0.75, BRASS), (1, BRASS_DARK)]),
                   stroke=INK, width=1.5)
            s.line(4, 3.2, 92, 3.2, "#ffffff", 1.3, 0.9)
            for x in (8.0, 26.0, 48.0, 70.0, 88.0):
                _rivet(s, x, 8.5, 1.3, body=BRASS_LIGHT, rim=BRASS_DEEP, hi=BRASS_HI)
            return s

        def lamp(on: bool):
            s = Svg(12, 9)
            if on:
                s.path("M1 8.5 Q1 1 6 1 Q11 1 11 8.5 Z", fill=s.radial(6, 6, 6, [(0, "#ffffff"), (0.45, "#ffe08a"), (1, "#ff8a2a")]), stroke=INK, width=0.9)
            else:
                s.path("M1 8.5 Q1 1 6 1 Q11 1 11 8.5 Z", fill=s.radial(5, 4, 6, [(0, "#c8803a"), (1, "#5a2e18")]), stroke=INK, width=0.9)
            return s

        def rod():
            s = Svg(10, 40)
            s.rect(1.5, 0, 7, 40, fill=s.linear(1.5, 0, 8.5, 0, [(0, "#8a92a6"), (0.3, "#ffffff"), (0.55, "#c8d0dc"), (1, "#5a6278")]))
            s.line(1.5, 0, 1.5, 40, INK, 1.0)
            s.line(8.5, 0, 8.5, 40, INK, 1.0)
            return s

        def cylinder():
            s = Svg(24, 58)
            s.path(rounded_rect_path(3, 6, 18, 48, 3), fill=s.linear(3, 0, 21, 0, [(0, BRASS_DEEP), (0.25, BRASS_LIGHT), (0.5, BRASS), (1, BRASS_DEEP)]),
                   stroke=INK, width=1.4)
            for y in (14.0, 44.0):
                s.rect(2, y, 20, 4, fill=s.linear(2, 0, 22, 0, [(0, STEEL_DARK), (0.4, STEEL_HI), (1, STEEL_DARK)]), stroke=INK, width=0.9)
            s.path(rounded_rect_path(5, 52, 14, 6, 2), fill=s.linear(5, 0, 19, 0, [(0, STEEL_DARK), (0.4, STEEL_LIGHT), (1, STEEL_DEEP)]), stroke=INK,
                   width=1.0)
            s.path(rounded_rect_path(0.5, 1, 23, 6, 2), fill=s.linear(0, 1, 0, 7, [(0, IRON_HI), (1, IRON_DARK)]), stroke=INK, width=1.1)
            for x in (4.0, 20.0):
                s.circle(x, 4, 1.1, fill="#e8e6f0")
            s.line(8, 9, 8, 50, "#ffffff", 1.2, 0.45)
            return s

        def jet():
            s = Svg(46, 26)
            s.path(_lobes(26, 13, 19, 10, 6, 0.2, seed=4), fill=s.radial(16, 10, 30, [(0, "#ffffff"), (0.6, "#f0ece8"), (1, "#c8bcc4")]),
                   stroke="#a8949e", width=0.9, opacity=0.95)
            s.path("M1 13 L12 9 L12 17 Z", fill="#ffffff", opacity=0.9)
            return s

        return {
            "head": (head, (48, 82)), "lamp_on": (lambda: lamp(True), (6, 8.5)), "lamp_off": (lambda: lamp(False), (6, 8.5)),
            "glow": (lambda: _halo_svg(40, "#ffb040", 0.7), (20, 20)), "rod": (rod, (5, 0)), "cylinder": (cylinder, (12, 58)),
            "jet": (jet, (1, 13)), "puff": (lambda: _puff_svg(24), (12, 10)), "streak": (lambda: _streak_svg(46), (3, 46)),
            "spark": (lambda: _spark_svg(14), (7, 7)),
        }

    def commands(self, e, t):
        root = _root(self, e)
        out: list[DrawCommand] = []
        state = e.anim if e.alive else "rest"
        st = e.state_time
        ext = max(0.0, (e.y - e.origin_y) / self.du) if e.alive else 0.0
        jitter = math.sin(t * 85) * 1.3 if state == "shake" else 0.0
        sy = 1.0
        if state == "fall":
            sy = 1.03
        elif state == "rest":
            sy = 1 - 0.07 * max(0.0, 1 - st / 0.14)
        head = Xf(root.x + jitter, root.y, root.angle, root.sx * (2 - sy), root.sy * sy)
        top = -80.0 * sy  # head top in rig space (flush with the hitbox top)
        # cylinders stay at the resting height; rods span the drop
        for side in (-1, 1):
            cx = side * 39.0
            gland = top - ext
            if ext > 0.5:
                out.append(self.cmd("rod", _at(root, cx + jitter * 0.3, gland - 2, 0, 1.0, (ext + 4) / 40.0)))
            out.append(self.cmd("cylinder", root.child(cx, gland + 2)))
            # warning beacon on each cylinder's mounting flange (blinks while venting)
            lamp = root.child(cx, gland - 54)
            if (state == "shake" and int(t * 14 + (side > 0)) % 2 == 0) or state == "fall":
                out.append(self.cmd("glow", lamp.child(0, -3), alpha=0.95))
                out.append(self.cmd("lamp_on", lamp))
            else:
                out.append(self.cmd("lamp_off", lamp))
        out.append(self.cmd("head", head))
        if state == "shake":
            k = _clamp(st / 0.35)
            for side in (-1, 1):
                port = head.child(side * 42, -50)
                for j in range(2):
                    q = (t * 6 + j * 0.5) % 1.0
                    out.append(self.cmd("jet", port.child(side * q * 6, -q * 4, 0 if side > 0 else 180), scale=(0.5 + 0.6 * q) * (0.6 + 0.6 * k),
                                        alpha=(1 - q * 0.8) * (0.5 + 0.5 * k)))
        elif state == "fall":
            for sx in (-24.0, -8.0, 8.0, 24.0):
                out.append(self.cmd("streak", head.child(sx, top - 6), alpha=0.7))
        elif state == "rest" and e.alive:
            if st < 0.5:
                q = st / 0.5
                for side in (-1, 1):
                    out.append(self.cmd("puff", root.child(side * (46 + 26 * q), -6 - 10 * q), scale=0.8 + 0.9 * q, alpha=1 - q))
                    out.append(self.cmd("puff", root.child(side * (30 + 14 * q), -2 - 4 * q), scale=0.6 + 0.6 * q, alpha=0.9 * (1 - q)))
            if st < 0.25:
                q = st / 0.25
                for side in (-1, 1):
                    out.append(self.cmd("spark", root.child(side * (30 + 30 * q), -4 - 18 * q + 30 * q * q), scale=1 - q * 0.6, alpha=1 - q))
        elif state in ("rise", "wait") and e.alive:
            q = (t * (1.6 if state == "rise" else 0.5) + e.origin_x * 0.01) % 1.0
            if state == "rise" or q < 0.3:
                k = q if state == "rise" else q / 0.3
                for side in (-1, 1):
                    out.append(self.cmd("puff", root.child(side * (39 + 6 * k), top - ext - 4 - 12 * k), scale=0.3 + 0.35 * k, alpha=0.7 * (1 - k)))
        return _flash(e, t, out)


# =========================================================================== Torreta de Arco
@register("arc_turret")
class ArcTurret(CreatureRig):
    """Copper turret on four spider legs (two-bone IK); its stubby mortar
    tilts up and glows red-hot with a nut loaded before every lob."""

    du = 0.46
    THIGH, SHIN = 20.0, 40.0

    def parts(self):
        def dome():
            s = Svg(66, 46)
            s.path("M6 34 Q6 4 33 4 Q60 4 60 34 Z", fill=s.radial(22, 12, 50, [(0, COPPER_HI), (0.35, COPPER_LIGHT), (0.75, COPPER), (1, COPPER_DARK)]),
                   stroke=INK, width=1.8)
            for k in range(7):
                a = math.pi + math.pi * (k + 0.5) / 7
                s.circle(33 + math.cos(a) * 21, 34 + math.sin(a) * 21, 1.1, fill=COPPER_HI, stroke=COPPER_DARK, width=0.4)
            s.path("M12 30 Q12 12 28 8", stroke="#ffffff", width=2.0, opacity=0.6)
            s.path(rounded_rect_path(16, 8, 14, 5, 2), fill=COPPER_DARK, stroke=INK, width=0.9)
            # base ring
            s.path(rounded_rect_path(2, 32, 62, 10, 4), fill=s.linear(0, 32, 0, 42, [(0, IRON_HI), (0.4, IRON), (1, IRON_DEEP)]), stroke=INK, width=1.5)
            for x in (10, 22, 34, 46, 58):
                s.circle(x, 37, 1.2, fill="#d8d6e2")
            # trunnion boss for the barrel
            s.circle(46, 20, 7, fill=s.radial(44, 18, 8, [(0, BRASS_HI), (1, BRASS_DARK)]), stroke=INK, width=1.2)
            s.circle(46, 20, 2.2, fill=INK)
            return s

        def barrel(hot: bool):
            s = Svg(46, 22)
            if hot:
                fill = s.linear(0, 0, 46, 0, [(0, "#a83a1e"), (0.5, HOT_ORANGE), (0.85, HOT_YELLOW), (1, HOT_WHITE)])
                band = HOT_RED
            else:
                fill = s.linear(0, 2, 0, 20, [(0, STEEL_HI), (0.3, STEEL_LIGHT), (0.7, STEEL), (1, STEEL_DEEP)])
                band = BRASS
            s.path("M4 6 Q4 4 7 4 L34 5 L38 1.5 Q44 1.5 44 4 L44 18 Q44 20.5 38 20.5 L34 17 L7 18 Q4 18 4 16 Z", fill=fill, stroke=INK, width=1.4)
            s.rect(18, 4.6, 5, 12.8, fill=band, stroke=INK, width=0.8)
            s.ellipse(43, 11, 1.8, 8, fill="#1a1012" if not hot else "#ffefc0", stroke=INK, width=0.8)
            s.path("M8 6.5 L33 7", stroke="#ffffff", width=1.2, opacity=0.6 if not hot else 0.9)
            return s

        def nut():
            s = Svg(18, 18)
            s.circle(9, 9, 9, fill=s.radial(9, 9, 9, [(0, HOT_YELLOW, 0.8), (1, HOT_ORANGE, 0)]))
            hexagon = [(9 + math.cos(a) * 5.4, 9 + math.sin(a) * 5.4) for a in [i * math.pi / 3 + math.pi / 6 for i in range(6)]]
            s.polygon(hexagon, fill=s.radial(8, 8, 6, [(0, HOT_WHITE), (0.5, HOT_YELLOW), (1, HOT_ORANGE)]), stroke="#8a2a10", width=0.8)
            s.circle(9, 9, 2, fill=HOT_RED)
            return s

        def thigh():
            s = Svg(26, 10)
            s.path(rounded_rect_path(2, 2, 21, 6, 3), fill=s.linear(0, 2, 0, 8, [(0, IRON_HI), (1, IRON_DARK)]), stroke=INK, width=1.2)
            s.circle(4, 5, 3.2, fill=BRASS, stroke=INK, width=0.9)
            s.circle(22, 5, 3, fill=s.radial(21, 4, 3.4, [(0, BRASS_HI), (1, BRASS_DARK)]), stroke=INK, width=0.9)
            return s

        def shin():
            s = Svg(10, 44)
            s.path("M1.8 3 L8.2 3 L6.4 36 L5 43.5 L3.6 36 Z", fill=s.linear(2, 0, 8, 0, [(0, IRON_HI), (0.5, IRON), (1, IRON_DEEP)]), stroke=INK, width=1.2)
            s.line(4.2, 6, 4.4, 30, "#c8c6d4", 0.8, 0.6)
            return s

        def dent():
            s = Svg(24, 18)
            s.path("M2 8 L8 6 L11 10 L16 4 L22 9", stroke=INK, width=1.4)
            s.path("M8 6 L9 13 M16 4 L18 1", stroke=INK, width=1.0)
            s.path("M2.6 9 L8 7.2 L11 11 L16 5.4 L21.6 10", stroke=COPPER_HI, width=0.8, opacity=0.8)
            return s

        return {
            "dome": (dome, (33, 42)), "barrel": (lambda: barrel(False), (6, 11)), "barrel_hot": (lambda: barrel(True), (6, 11)),
            "nut": (nut, (9, 9)), "thigh": (thigh, (4, 5)), "shin": (shin, (5, 3)), "dent": (dent, (12, 9)),
            "glow": (lambda: _halo_svg(60, HOT_ORANGE, 0.6), (30, 30)), "smoke": (lambda: _puff_svg(20, dark=True), (10, 8)),
            "puff": (lambda: _puff_svg(18), (9, 7)),
        }

    def _knee(self, hip: tuple[float, float], foot: tuple[float, float], out_dir: int) -> tuple[float, float]:
        """Two-bone IK in rig space: the knee bends upward and outward like a spider's."""
        hx, hy = hip
        fx, fy = foot
        d = max(1e-3, min(self.THIGH + self.SHIN - 0.01, math.hypot(fx - hx, fy - hy)))
        base = math.atan2(fy - hy, fx - hx)
        off = math.acos(_clamp((self.THIGH ** 2 + d * d - self.SHIN ** 2) / (2 * self.THIGH * d), -1.0, 1.0))
        knee_a = min((base - off, base + off), key=lambda a: math.sin(a) - 0.3 * out_dir * math.cos(a))
        return hx + math.cos(knee_a) * self.THIGH, hy + math.sin(knee_a) * self.THIGH

    def commands(self, e, t):
        root = _root(self, e)
        out: list[DrawCommand] = []
        alive = e.alive
        state = e.anim if alive else "defeat"
        st = e.state_time
        ph = t * 9.0
        stepping = state == "step"
        k_w = _ease(st / 0.3) if state == "windup" else 0.0
        k_t = _clamp(st / 0.12) if state == "throw" else 0.0
        crouch = 4.0 * k_w - 2.0 * k_t
        bob = -abs(math.sin(ph)) * 1.6 if stepping else 0.0
        body_y = -30 + crouch + bob - (8.0 if state == "jump" else 0.0)
        lean = (math.sin(ph) * 2 if stepping else 0.0) - 7 * k_w + 9 * k_t * (1 - _clamp((st - 0.12) / 0.18))
        body = root.child(0, body_y, lean)
        la = math.radians(lean)
        legs = []
        for i, (hx, fx) in enumerate(((-22.0, -36.0), (-9.0, -17.0), (9.0, 17.0), (22.0, 36.0))):
            phase = ph + (0 if i in (0, 2) else math.pi)
            step_x = math.sin(phase) * 5 if stepping else 0.0
            step_up = max(0.0, math.cos(phase)) * 5 if stepping else 0.0
            foot = (fx + step_x, -step_up + (5.0 if state == "jump" else 0.0))
            hip = (hx * math.cos(la) + 2 * math.sin(la), body_y + hx * math.sin(la) - 2 * math.cos(la))
            knee = self._knee(hip, foot, 1 if hx > 0 else -1)
            legs.append((i, hip, knee, foot))
        far = (196, 192, 208)
        for i, hip, knee, foot in legs:  # the far pair is drawn behind the dome
            if i in (1, 2):
                self._draw_leg(out, root, hip, knee, foot, far)
        out.append(self.cmd("dome", body))
        if state == "throw":
            barrel_angle = -72 + 34 * k_t
            recoil = -5 * k_t * (1 - _clamp((st - 0.1) / 0.2))
        else:
            barrel_angle = -(42 + 30 * k_w) + (math.sin(ph) * 2 if stepping else 0.0)
            recoil = 0.0
        barrel = body.child(13, -22, barrel_angle).child(recoil, 0)
        out.append(self.cmd("barrel", barrel))
        if state == "windup":
            out.append(self.cmd("barrel_hot", barrel, alpha=k_w))
            out.append(self.cmd("glow", barrel.child(30, 0), alpha=0.3 + 0.7 * k_w, scale=0.5 + 0.6 * k_w))
            out.append(self.cmd("nut", barrel.child(38, 0, t * 200), scale=0.4 + 0.6 * k_w))
        elif state == "throw":
            q = _clamp(st / 0.3)
            out.append(self.cmd("barrel_hot", barrel, alpha=1 - q))
            out.append(self.cmd("smoke", barrel.child(42 + q * 10, -q * 6), scale=0.6 + 0.8 * q, alpha=1 - q))
            out.append(self.cmd("puff", barrel.child(40 + q * 6, 4 + q * 4), scale=0.5 + 0.6 * q, alpha=0.9 * (1 - q)))
        if alive and e.health < e.hp:  # dented after the first stomp, smoking
            out.append(self.cmd("dent", body.child(-6, -18)))
            q = (t * 1.4) % 1.0
            out.append(self.cmd("smoke", body.child(-12 - q * 4, -34 - q * 18), scale=0.4 + 0.5 * q, alpha=0.75 * (1 - q)))
        for i, hip, knee, foot in legs:  # near pair in front
            if i in (0, 3):
                self._draw_leg(out, root, hip, knee, foot, None)
        return _flash(e, t, out)

    def _draw_leg(self, out: list[DrawCommand], root: Xf, hip: tuple[float, float], knee: tuple[float, float], foot: tuple[float, float],
                  tint) -> None:
        (hx, hy), (kx, ky), (fx, fy) = hip, knee, foot
        thigh_a = math.degrees(math.atan2(ky - hy, kx - hx))
        shin_a = math.degrees(math.atan2(fy - ky, fx - kx)) - 90
        out.append(self.cmd("thigh", root.child(hx, hy, thigh_a), tint=tint))
        out.append(self.cmd("shin", root.child(kx, ky, shin_a), tint=tint))
