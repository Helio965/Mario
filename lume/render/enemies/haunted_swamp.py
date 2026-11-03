"""Pântano Assombrado creatures.

* ``shy_ghost`` — Sombra-Errante: a smoky dark wisp with two glowing amber
  eyes and a tattered tail. It streams toward Lume in the dark, and when the
  lantern halo catches it (``freeze``/``hide``) it curls up around its tail,
  dims and half-closes its eyes. Light-based, never facing-based.
* ``swamp_frog`` — Sapo-do-Lodo: a chubby olive mud frog with duckweed on its
  back; it squats and inflates a pale throat sac before every leap (telegraph).
* ``mud_hand`` — Mão-do-Lodo: a dripping hand of peat that rises from its own
  bubbling mud puddle (drawn by the rig), grabs the air and sinks again; the
  puddle boils and fingertips break the surface just before it rises.
* ``bone_walker`` — Ossada do Pântano: the mossy skeleton of a heron-like
  marsh bird stalking on long legs, lantern-glow in its eye socket. A stomp
  collapses it into a pile of bones that rattles and rebuilds itself.

Night readability: dark bodies carry a lilac moonlit rim (the ghost a soft
halo), bones are ivory with ink outlines, and eyes glow. Hits blink a warm
tint; stomps squash, fire/shell/star knock the creature upside down.
"""

from __future__ import annotations

import math

from ..rig import DrawCommand, Xf
from ..svg import Svg, blob, smooth_closed, smooth_open
from .base import CreatureRig, register

INK = "#1a1526"
FLASH = (255, 150, 140)
GHOST_FLASH = (255, 236, 200)  # a dark smoky body needs a bright blink
AMBER, AMBER_HOT, AMBER_DEEP = "#ffcf6e", "#fff6d4", "#e88a28"
FIRE, FIRE_HOT = "#d4f26c", "#f6ffd8"
BONE_HI, BONE, BONE_DARK = "#fbf4de", "#e2d6b4", "#a8987a"
MOSS_HI, MOSS, MOSS_DARK = "#c3d68e", "#809c54", "#3e5a2e"
MUD_HI, MUD, MUD_DARK, MUD_DEEP = "#806652", "#54423a", "#2e231d", "#140e0b"
SHEEN = "#d2c4ec"  # moonlit wet highlight


# --------------------------------------------------------------------------- shared helpers
def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def _ease(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def _xy(xf: Xf) -> tuple[float, float]:
    return xf.x, xf.y


def _root(rig: CreatureRig, e) -> Xf:
    return Xf() if e.alive else rig.defeat_xf(e, Xf())


def _flash(e, t: float, out: list[DrawCommand], tint: tuple[int, int, int] = FLASH) -> list[DrawCommand]:
    """Blink while the damage timer runs (the hit itself and the defeat)."""
    if e.hit_timer > 0 and int(t * 20) % 2 == 0:
        for c in out:
            c.tint = tint
    return out


def _soft(w: float, h: float, color: str, strength: float, core: float = 0.0) -> Svg:
    """Soft elliptical glow sprite."""
    s = Svg(w, h)
    r = min(w, h) / 2
    with s.group(f"translate({w / 2:.2f} {h / 2:.2f}) scale({w / 2 / r:.4f} {h / 2 / r:.4f})"):
        s.circle(0, 0, r, fill=s.radial(0, 0, r, [(0, color, strength), (max(core, 0.01), color, strength), (0.55, color, strength * 0.35), (1, color, 0)]))
    return s


def _eye_x(size: float = 10.0, color: str = INK) -> Svg:
    s = Svg(size, size)
    m, n = size * 0.18, size * 0.82
    s.path(f"M{m:.2f} {m:.2f} L{n:.2f} {n:.2f} M{n:.2f} {m:.2f} L{m:.2f} {n:.2f}", stroke=color, width=size * 0.17)
    return s


def _taper(centre, tension: float = 0.9) -> str:
    left = [(x - t / 2, y) for x, y, t in centre]
    right = [(x + t / 2, y) for x, y, t in reversed(centre)]
    d = smooth_open(right, tension)
    return smooth_open(left, tension) + f"L{right[0][0]:.2f} {right[0][1]:.2f}" + (d[d.index("C"):] if "C" in d else "") + "Z"


# =========================================================================== Sombra-Errante
@register("shy_ghost")
class ShyGhost(CreatureRig):
    """Hooded wisp of night smoke trailing a two-part tattered tail, with slanted
    amber eyes. ``chase``: leans in, tail streaming, eyes wide and hungry, smoke
    puffs shed from the tail. ``freeze``/``hide`` (caught by the lantern halo):
    curled into a ball around its own tail, dimmed, eyes half closed, shivering.
    Deliberately not a round white sheet ghost: no mouth, no hands, no face hiding."""

    du = 0.42
    SMOKE = [(0, "#5c4e92"), (0.35, "#2e2656"), (0.75, "#18122e"), (1, "#100c20")]

    def parts(self):
        smoke = self.SMOKE

        def head():
            s = Svg(72, 66)
            outline = [(40, 6), (54, 10), (64, 22), (66, 36), (60, 50), (54, 58), (46, 52), (38, 60), (30, 52), (20, 56), (12, 46), (8, 34),
                       (12, 20), (22, 11), (30, 4), (26, 12)]
            d = smooth_closed(outline, 0.8)
            s.path(d, fill=s.radial(30, 18, 60, smoke))
            for pts, a in (([(16, 40), (24, 34), (34, 40), (38, 50)], 0.35), ([(50, 18), (58, 28), (56, 40)], 0.25)):
                s.path(smooth_open(pts), stroke="#8a7ac8", width=1.8, opacity=a)
            s.ellipse(46, 32, 16, 11, fill=s.radial(46, 32, 16, [(0, "#06040c", 0.8), (1, "#06040c", 0)]))  # the dark hood the eyes glow in
            s.path(d, stroke="#07050e", width=1.3, opacity=0.55)
            s.path(smooth_open([(12, 30), (16, 18), (28, 9), (40, 6), (54, 10)]), stroke="#d6ccff", width=1.6, opacity=0.7)
            return s

        def aura():
            s = Svg(84, 78)
            d = smooth_closed([(46, 3), (62, 8), (74, 22), (78, 38), (70, 56), (56, 70), (38, 72), (20, 66), (8, 50), (5, 32), (12, 16), (26, 6)], 0.85)
            s.path(d, fill=s.radial(40, 34, 44, [(0, "#8070c8", 0.55), (0.7, "#6a5ab8", 0.35), (1, "#5a4aa8", 0.08)]))
            return s

        def tail(seg: int, aura: bool = False):
            s = Svg(36, 44)
            if seg == 0:
                centre = [(18, 2, 30), (19, 12, 25), (16, 23, 19), (18, 33, 15), (17, 42, 12)]
            else:
                centre = [(18, 2, 13), (19, 12, 10), (16, 22, 7.5), (19, 31, 4.5), (17, 41, 1.0)]
            if aura:
                centre = [(x, y, t * 1.3 + 3) for x, y, t in centre]
            d = _taper(centre, 0.85)
            if aura:
                s.path(d, fill=s.linear(0, 0, 0, 44, [(0, "#7a6ac8", 0.5), (1, "#6a5ab8", 0.05)]))
                return s
            s.path(d, fill=s.linear(0, 0, 0, 44, [(0, "#251e48"), (0.7, "#1a1434"), (1, "#16102c", 0.7)]))
            s.path(smooth_open([(x - t / 2 + 1.0, y) for x, y, t in centre[:-1]]), stroke="#07050e", width=1.0, opacity=0.4)
            s.path(smooth_open([(x + t / 2 - 1.2, y) for x, y, t in centre[:-1]]), stroke="#b4a6ec", width=1.0, opacity=0.5)
            if seg == 1:  # tattered split tip
                s.path("M17 33 Q11 37 8 43 M18 33 Q23 38 26 43", stroke="#1a1434", width=1.8)
            else:  # wisps curling off the smoke
                s.path("M6 22 Q2 26 5 30", stroke="#3a3070", width=1.6, opacity=0.8)
                s.path("M29 30 Q34 33 31 38", stroke="#3a3070", width=1.4, opacity=0.8)
            return s

        def curl():
            s = Svg(74, 66)
            ball = smooth_closed([(38, 6), (55, 11), (65, 26), (64, 44), (52, 57), (34, 60), (17, 53), (9, 38), (12, 22), (24, 10)], 0.8)
            s.path(ball, fill=s.radial(28, 20, 56, smoke))
            s.path(ball, stroke="#07050e", width=1.2, opacity=0.5)
            # the tail wrapped round the front like a scarf, its tattered tip tucked in
            wrap = [(8, 40, 5), (16, 52, 10), (34, 58, 13), (52, 52, 11), (63, 40, 8), (62, 29, 5), (55, 24, 2)]
            upper = [(x, y - th / 2) for x, y, th in wrap]
            lower = [(x, y + th / 2) for x, y, th in reversed(wrap)]
            du_, dl = smooth_open(upper, 0.8), smooth_open(lower, 0.8)
            s.path(du_ + f"L{lower[0][0]:.2f} {lower[0][1]:.2f}" + dl[dl.index("C"):] + "Z", fill=s.linear(0, 40, 0, 64, [(0, "#3e3474"), (1, "#16102c")]))
            s.path(smooth_open(upper, 0.8), stroke="#b4a6ec", width=1.1, opacity=0.6)
            s.ellipse(44, 30, 15, 9, fill=s.radial(44, 30, 15, [(0, "#06040c", 0.7), (1, "#06040c", 0)]))
            s.path(smooth_open([(14, 26), (24, 12), (40, 7)]), stroke="#d6ccff", width=1.4, opacity=0.55)
            return s

        def wisp():
            s = Svg(16, 26)
            s.path("M8 25 Q2 18 7 12 Q12 7 8 1 Q15 7 12 13 Q8 19 11 25 Z", fill=s.linear(0, 0, 0, 26, [(0, "#5c4e92", 0.2), (1, "#2e2656", 0.9)]))
            return s

        def eye():
            s = Svg(18, 14)
            d = "M1 8.5 Q6 1 13 2.4 Q17 3.4 17 6.2 Q12 13 1 8.5 Z"
            s.path(d, fill=s.radial(9, 6.5, 9, [(0, AMBER_HOT), (0.38, "#ffe08a"), (0.78, AMBER), (1, AMBER_DEEP)]))
            s.ellipse(8.4, 6.0, 1.6, 2.6, fill="#5a2a08", opacity=0.55)
            s.circle(6.5, 4.8, 1.3, fill="#ffffff", opacity=0.9)
            return s

        def lid():
            s = Svg(20, 10)
            s.path("M0 9.5 Q4 0 12 0.6 Q19 1 20 6 Q12 5.2 0 9.5 Z", fill="#120d24")
            s.path("M0.5 9.2 Q11 5 19.6 6", stroke="#ffd98a", width=0.9, opacity=0.75)
            return s

        def puff():
            s = Svg(20, 16)
            s.path(blob(10, 8, 8, 6, 0.18, seed=3), fill=s.radial(8, 6, 10, [(0, "#4a3e7a", 0.8), (1, "#2a2250", 0.45)]))
            return s

        return {"halo": (lambda: _soft(116, 116, "#7a6ad0", 0.4), (58, 58)), "aura": (aura, (42, 40)), "head": (head, (38, 34)),
                "tail0": (lambda: tail(0), (18, 3)), "tail1": (lambda: tail(1), (18, 3)), "tail0_aura": (lambda: tail(0, True), (18, 3)),
                "tail1_aura": (lambda: tail(1, True), (18, 3)), "curl": (curl, (37, 36)), "wisp": (wisp, (8, 25)),
                "flash": (lambda: _soft(80, 80, "#fff6e8", 0.85, 0.2), (40, 40)),
                "eye": (eye, (9, 7)), "eye_glow": (lambda: _soft(40, 34, AMBER, 0.55, 0.05), (20, 17)), "lid": (lid, (10, 8)), "puff": (puff, (10, 8)),
                "eye_x": (lambda: _eye_x(10, "#e8e0ff"), (5, 5))}

    def commands(self, e, t):
        root = _root(self, e)
        anim = e.anim if e.alive else "defeat"
        st = e.state_time
        if anim in ("freeze", "hide"):  # the behaviour publishes 'freeze'; the species sheet calls it 'hide'
            k_hide = _ease(st / 0.18)  # curling up
        elif anim == "chase" and st < 0.18:
            k_hide = 1.0 - _ease(st / 0.18)  # uncurling
        else:
            k_hide = 0.0
        out: list[DrawCommand] = []
        bob = math.sin(t * 2.6) * 2.5
        if k_hide < 1.0:
            out += self._chase(e, t, root, bob, 1.0 - k_hide)
        if k_hide > 0.0:
            out += self._hide(e, t, root, bob, k_hide)
        if e.hit_timer > 0 and int(t * 20) % 2 == 0:
            out.append(self.cmd("flash", root.child(2, -46 + bob), alpha=0.85))
        return _flash(e, t, out, GHOST_FLASH)

    def _chase(self, e, t: float, root: Xf, bob: float, a: float) -> list[DrawCommand]:
        out: list[DrawCommand] = []
        alive = e.alive
        lean = 12.0 + math.sin(t * 3.1) * 3 if alive else 0.0
        centre = root.child(4, -52 + bob)
        head = Xf(centre.x, centre.y, root.angle + lean, root.sx * 1.03, root.sy * 0.98)
        out.append(self.cmd("halo", root.child(0, -42 + bob), alpha=0.85 * a))
        wave = t * 7.5
        tail0 = head.child(-12, 14, 44 + math.sin(wave) * 9)
        tail1 = tail0.child(-1, 38, 24 + math.sin(wave - 1.2) * 20)
        if alive:  # puffs shed from the tail tip
            tip = tail1.child(0, 38)
            for j in range(3):
                k = (t * 1.5 + j / 3) % 1
                out.append(self.cmd("puff", Xf(tip.x - k * 24, tip.y - k * 10 + math.sin(t * 5 + j) * 3, 0, root.sx, root.sy), scale=0.95 - 0.55 * k,
                                    alpha=(1 - k) * 0.7 * a))
        out.append(self.cmd("aura", head, alpha=0.75 * a))
        out.append(self.cmd("tail1_aura", tail1, alpha=0.8 * a))
        out.append(self.cmd("tail0_aura", tail0, alpha=0.8 * a))
        out.append(self.cmd("tail1", tail1, alpha=a))
        out.append(self.cmd("tail0", tail0, alpha=a))
        out.append(self.cmd("head", head, alpha=a))
        out.append(self.cmd("wisp", head.child(-10, -24, -30 + math.sin(t * 4) * 12), alpha=0.85 * a, scale=0.9))
        face = head.child(8, -2)
        if alive:
            closed = self.blink(t, e.origin_x * 0.3)
            for ex, tilt in ((-6.0, 14.0), (8.0, -10.0)):
                eye = face.child(ex, 0, tilt)
                out.append(self.cmd("eye_glow", eye, alpha=0.85 * a))
                if closed:
                    out.append(self.cmd("lid", eye.child(0, 1.5), alpha=a, scale=0.9))
                else:
                    out.append(self.cmd("eye", eye, alpha=a))
        else:
            for ex in (-6.0, 8.0):
                out.append(self.cmd("eye_x", face.child(ex, 0), alpha=a))
        return out

    def _hide(self, e, t: float, root: Xf, bob: float, a: float) -> list[DrawCommand]:
        out: list[DrawCommand] = []
        shiver = math.sin(t * 34) * 0.7
        pulse = 0.5 + 0.5 * math.sin(t * 2.2)
        centre = root.child(shiver, -38 + bob * 0.4)
        ball = Xf(centre.x, centre.y, root.angle - 6, root.sx * 0.9, root.sy * 0.88)
        out.append(self.cmd("halo", centre, alpha=(0.34 + 0.08 * pulse) * a, scale=0.8))
        out.append(self.cmd("curl", ball, alpha=(0.76 + 0.08 * pulse) * a))
        face = ball.child(7, -6)
        for ex, tilt in ((-6.0, 10.0), (7.0, -8.0)):
            eye = face.child(ex, 0, tilt)
            out.append(self.cmd("eye_glow", eye, alpha=0.4 * a, scale=0.8))
            out.append(self.cmd("eye", eye, alpha=0.85 * a, scale=0.85))
            out.append(self.cmd("lid", eye.child(0, -0.4), alpha=a, scale=0.92))
        return out


# =========================================================================== Sapo-do-Lodo
@register("swamp_frog")
class SwampFrog(CreatureRig):
    """Chubby olive mud frog. idle: breathing throat; crouch (telegraph): squats,
    eyes narrow and the throat sac balloons; jump: stretched, legs trailing;
    fall: legs reaching down; land: squash with a mud splash."""

    du = 0.5

    def parts(self):
        skin = [(0, "#a8b870"), (0.45, "#6a7e3e"), (1, "#334222")]

        def body():
            s = Svg(80, 56)
            outline = [(8, 44), (6, 30), (14, 16), (28, 10), (44, 12), (56, 10), (66, 14), (75, 24), (77, 32), (70, 40), (58, 46), (40, 50),
                       (22, 50)]
            d = smooth_closed(outline, 0.75)
            s.path(d, fill=s.radial(34, 16, 58, skin))
            # pale belly and chin
            s.path(smooth_closed([(18, 46), (34, 38), (54, 37), (70, 38), (62, 46), (42, 50), (24, 50)], 0.7),
                   fill=s.linear(0, 36, 0, 50, [(0, "#efe6b8"), (1, "#bcae78")]))
            # mottled blotches and warts
            for cx, cy, rx, ry in ((24, 20, 6, 4), (38, 17, 5, 3.4), (16, 32, 4.5, 3.5), (50, 24, 4, 3), (30, 30, 3.5, 2.6)):
                s.path(blob(cx, cy, rx, ry, 0.25, seed=cx), fill="#3e3a1e", opacity=0.55)
            for cx, cy in ((20, 16), (31, 24), (44, 21), (12, 26), (26, 36)):
                s.circle(cx, cy, 1.4, fill="#d8e0a0", opacity=0.75)
            # duckweed on the back
            for cx, cy in ((26, 11.5), (31, 10.4), (35, 11.8), (29, 13.4)):
                s.ellipse(cx, cy, 2.2, 1.4, fill="#b8f070", stroke="#3a6a24", width=0.5)
            # pale ridge along the flank, a wide content mouth and a nostril
            s.path("M56 15 Q40 13 26 19 Q15 24 11 32", stroke="#e6d88e", width=1.8, opacity=0.75)
            s.path("M56 15 Q40 13 26 19 Q15 24 11 32", stroke="#5a5a24", width=0.6, opacity=0.5)
            s.path("M76.5 30.5 Q66 36 52 33 Q49.5 32.4 48.6 34", stroke=INK, width=1.6)
            s.circle(72, 22, 0.9, fill=INK)
            s.path(d, stroke=INK, width=1.8)
            s.path(smooth_open([(12, 24), (20, 14), (32, 10)]), stroke="#e6f0b8", width=1.6, opacity=0.6)
            return s

        def thigh():
            s = Svg(36, 30)
            d = smooth_closed([(6, 6), (20, 2), (32, 10), (33, 20), (24, 28), (10, 27), (3, 18)], 0.8)
            s.path(d, fill=s.radial(14, 8, 30, skin), stroke=INK, width=1.6)
            s.path(blob(18, 12, 5, 3.4, 0.25, seed=2), fill="#3e3a1e", opacity=0.5)
            return s

        def foot():
            s = Svg(38, 14)
            s.path("M3 6 Q14 3 26 5 L35 2 L33 6 L37 7 L33 9 L35 12 L26 9 Q14 10 3 9 Z", fill=s.linear(0, 2, 0, 12, [(0, "#8a9a58"), (1, "#3e4e26")]),
                   stroke=INK, width=1.2)
            return s

        def arm():
            s = Svg(16, 26)
            s.path("M5 2 Q11 3 10 12 L10 20 L14 23 L10 23.5 L11 25.5 L7 23.6 L3 25 L5 22 Q4 12 5 2 Z",
                   fill=s.linear(0, 0, 14, 0, [(0, "#8a9a58"), (1, "#4a5a2c")]), stroke=INK, width=1.1)
            return s

        def eye():
            s = Svg(22, 20)
            s.path(smooth_closed([(2, 18), (2, 8), (11, 1.5), (20, 8), (20, 18)], 0.85), fill=s.radial(9, 7, 14, skin), stroke=INK, width=1.4)
            s.circle(11, 10.5, 6.4, fill=s.radial(10, 9, 7, [(0, "#fff4a8"), (0.6, "#f0b83a"), (1, "#a8601a")]), stroke=INK, width=0.9)
            s.ellipse(11.6, 10.8, 4.2, 1.7, fill="#140c08")
            s.circle(9, 8.4, 1.6, fill="#ffffff", opacity=0.9)
            return s

        def lid():
            s = Svg(22, 12)
            s.path("M3.5 10.5 Q3.5 2.5 11 2 Q18.5 2.5 18.5 10.5 Q11 8 3.5 10.5 Z", fill=s.linear(0, 2, 0, 11, [(0, "#9ab066"), (1, "#5a6e34")]),
                   stroke=INK, width=1.1)
            return s

        def sac():
            s = Svg(34, 30)
            d = smooth_closed([(17, 2), (29, 7), (33, 17), (27, 27), (17, 29), (7, 27), (1, 17), (5, 7)], 0.85)
            s.path(d, fill=s.radial(13, 11, 22, [(0, "#fff8e8"), (0.45, "#f6d8c0"), (0.85, "#d8a0a0"), (1, "#a86a78")]), stroke=INK, width=1.3)
            for pts in (((8, 12), (13, 18), (12, 25)), ((22, 9), (24, 17), (21, 25))):
                s.path(smooth_open(pts), stroke="#c87a8a", width=0.8, opacity=0.6)
            s.ellipse(11, 9, 4.5, 3, fill="#ffffff", opacity=0.9)
            return s

        def splash():
            s = Svg(60, 22)
            s.path("M4 21 Q30 15 56 21 Z", fill=MUD, stroke=INK, width=0.8)
            for k, (x, y, r) in enumerate(((8, 15, 2.2), (16, 9, 2.8), (26, 5, 2.4), (36, 6, 2.6), (45, 10, 2.8), (53, 16, 2.0), (21, 14, 1.6), (40, 14, 1.8))):
                s.circle(x, y, r, fill=MUD_HI if k % 2 else MUD, stroke=INK, width=0.7)
                s.circle(x - r * 0.3, y - r * 0.3, r * 0.3, fill=SHEEN, opacity=0.7)
            return s

        return {"body": (body, (40, 54)), "thigh": (thigh, (20, 6)), "foot": (foot, (5, 7)), "arm": (arm, (6, 3)), "eye": (eye, (11, 18)),
                "lid": (lid, (11, 10)), "sac": (sac, (17, 15)), "splash": (splash, (30, 21)), "eye_x": (lambda: _eye_x(11), (5.5, 5.5))}

    def commands(self, e, t):
        root = _root(self, e)
        anim = e.anim if e.alive else "defeat"
        st = e.state_time
        out: list[DrawCommand] = []
        sx = sy = 1.0
        tilt = lift = 0.0
        sac = 0.32 + 0.08 * math.sin(t * 5.0)
        thigh_a, foot_a, arm_a = 0.0, 4.0, 4.0  # foot angle is relative to the thigh
        lids = self.blink(t, e.origin_x * 0.53) and anim == "idle"
        if anim == "crouch":  # telegraph: squat, narrowed eyes, the sac balloons
            k = _ease(st / 0.2)
            sx, sy = 1 + 0.12 * k, 1 - 0.18 * k
            tilt = -5 * k
            sac = 0.32 + 0.78 * k + 0.04 * math.sin(t * 40) * k
            thigh_a, foot_a, arm_a = -6 * k, 10 * k, 4 - 12 * k
            lids = True
        elif anim == "jump":
            sx, sy = 0.9, 1.12
            tilt = -20
            sac = max(0.22, 1.1 - st * 7)
            thigh_a, foot_a, arm_a = 52.0, 96.0, -46.0
            lift = 3.0
        elif anim == "fall":
            sx, sy = 0.97, 1.04
            tilt = 12
            sac = 0.24
            thigh_a, foot_a, arm_a = 18.0, 40.0, -24.0
            lift = 2.0
        elif anim == "land":
            k = 1 - _ease(st / 0.18)
            sx, sy = 1 + 0.18 * k, 1 - 0.22 * k
        elif anim == "defeat":
            sac = 0.15
        body = Xf(root.x, root.y - lift, root.angle + tilt, root.sx * sx, root.sy * sy)
        far = (150, 160, 140)
        thigh_far = body.child(-12, -27, thigh_a)
        thigh = body.child(-18, -26, thigh_a)
        # far legs first (darker), body, near legs, eye, sac
        out.append(self.cmd("foot", thigh_far.child(-12, 18, foot_a), tint=far))
        out.append(self.cmd("arm", body.child(28, -22, arm_a - 12), tint=far))
        out.append(self.cmd("body", body))
        out.append(self.cmd("thigh", thigh))
        out.append(self.cmd("foot", thigh.child(-12, 18, foot_a)))
        out.append(self.cmd("arm", body.child(22, -22, arm_a)))
        head = body.child(20, -40)
        out.append(self.cmd("eye", head))
        if not e.alive:
            out.append(self.cmd("eye_x", head.child(0, -8), scale=0.9))
        elif lids:
            out.append(self.cmd("lid", head.child(0, -8)))
        out.append(self.cmd("sac", body.child(28, -17), scale=sac))
        if anim == "land":
            k = min(1.0, st / 0.18)
            out.append(self.cmd("splash", root.child(0, 1), scale=0.7 + 0.5 * k, alpha=1 - k))
        return _flash(e, t, out)


# =========================================================================== Mão-do-Lodo
@register("mud_hand")
class MudHand(CreatureRig):
    """A hand of dripping peat in a bubbling puddle. The puddle stays on the ground
    while the hitbox rises and sinks (the arm is stretched to the visible height)."""

    du = 0.45

    def parts(self):
        def puddle_back():
            s = Svg(110, 28)
            s.ellipse(55, 14, 53, 11.5, fill=s.radial(55, 12, 54, [(0, "#2a1e2e"), (0.6, "#1c141c"), (1, "#3a2c34")]), stroke=INK, width=1.3)
            s.ellipse(55, 13, 44, 7.5, fill=s.radial(48, 11, 44, [(0, "#5a3a6a", 0.6), (0.6, "#3a2448", 0.35), (1, "#3a2448", 0)]))
            s.path("M18 11 Q50 4 92 10", stroke=SHEEN, width=1.0, opacity=0.5)
            return s

        def puddle_front():
            s = Svg(110, 28)
            s.path("M2 14 Q4 25 30 26.5 Q55 28 80 26.5 Q106 25 108 14 Q100 22 55 22 Q10 22 2 14 Z", fill=s.linear(0, 14, 0, 28, [(0, MUD), (1, MUD_DEEP)]),
                   stroke=INK, width=1.1)
            for cx, rx in ((22, 7), (46, 9), (74, 8), (94, 6)):
                s.path(blob(cx, 22.5, rx, 3.2, 0.2, seed=cx), fill=MUD_HI, opacity=0.9)
                s.path(f"M{cx - rx * 0.6:.1f} 21.2 Q{cx:.1f} 19.6 {cx + rx * 0.6:.1f} 21.2", stroke=SHEEN, width=0.8, opacity=0.55)
            return s

        def arm():
            s = Svg(44, 100)
            d = ("M6 100 Q2 84 7 70 Q4 56 9 42 Q11 24 12 2 L32 2 Q33 22 35 40 Q39 54 36 66 Q41 82 38 100 Z")
            s.path(d, fill=s.linear(4, 0, 40, 0, [(0, MUD_DARK), (0.3, MUD_HI), (0.6, MUD), (1, MUD_DEEP)]), stroke=INK, width=1.4)
            for x, y, ln in ((15, 18, 14), (27, 44, 18), (18, 64, 16), (30, 78, 12)):
                s.path(f"M{x - 1.8:.1f} {y:.1f} Q{x:.1f} {y + ln:.1f} {x + 1.8:.1f} {y:.1f} Z", fill=MUD_DARK, opacity=0.7)
            s.path("M8 96 Q6 70 10 50 Q12 26 14 4", stroke=SHEEN, width=1.4, opacity=0.5)
            return s

        def hand(mode: str):
            """Goopy hand of peat seen from the palm side; the wrist (pivot) is at (36, 62)."""
            s = Svg(72, 66)
            fill = s.radial(26, 22, 50, [(0, "#9a7e64"), (0.4, MUD_HI), (0.75, MUD), (1, MUD_DARK)])

            def finger(bx: float, by: float, ang: float, ln: float, wd: float, bend: float) -> None:
                a = math.radians(ang)
                dx, dy = math.sin(a), -math.cos(a)
                px, py = math.cos(a), math.sin(a)
                pts = [(bx + dx * ln * u + px * bend * u * u, by + dy * ln * u + py * bend * u * u, wd * (1 - 0.25 * u)) for u in [j / 5 for j in range(6)]]
                s.path(_taper(pts), fill=fill, stroke=INK, width=1.2)
                tx, ty, tw = pts[-1]
                s.circle(tx, ty, tw * 0.5, fill=fill, stroke=INK, width=1.2)
                s.path(smooth_open([(x - w * 0.28, y) for x, y, w in pts[1:]]), stroke=SHEEN, width=1.0, opacity=0.5)
                s.circle(tx - tw * 0.15, ty - tw * 0.15, tw * 0.16, fill="#e8dcf8", opacity=0.6)

            if mode == "open":
                for bx, ang, ln, wd in ((19, -24, 24, 11.5), (30, -8, 28, 12.5), (42, 6, 27, 12), (53, 20, 22, 11)):
                    finger(bx, 32, ang, ln, wd, 5)
            elif mode == "claw":
                for bx, ang, ln, wd in ((20, -12, 15, 12), (30, -3, 18, 13), (41, 6, 17, 12.5), (51, 15, 14, 11.5)):
                    finger(bx, 32, ang, ln, wd, 9)
            if mode == "fist":
                s.path(smooth_closed([(22, 62), (16, 46), (16, 28), (24, 16), (38, 13), (52, 17), (58, 30), (56, 46), (50, 62)], 0.8), fill=fill, stroke=INK,
                       width=1.4)
                for x in (24, 34, 44):  # knuckles
                    s.path(f"M{x:.1f} 17 Q{x + 5:.1f} 14 {x + 9:.1f} 18", stroke=MUD_DARK, width=1.3)
                    s.circle(x + 4.5, 17.5, 2.2, fill="#a88c72", opacity=0.7)
                for y in (26, 34):
                    s.path(f"M20 {y} Q34 {y + 3} 50 {y}", stroke=MUD_DARK, width=1.2, opacity=0.8)
                s.path("M18 30 Q17 44 24 58", stroke=SHEEN, width=1.4, opacity=0.5)
            else:
                s.path(smooth_closed([(22, 62), (17, 50), (14, 36), (20, 27), (36, 24), (52, 27), (58, 38), (54, 50), (50, 62)], 0.8), fill=fill, stroke=INK,
                       width=1.4)
                s.path("M20 52 Q16 40 22 30", stroke=SHEEN, width=1.4, opacity=0.5)
            # thumb on the front (+x) side
            if mode == "open":
                thumb = [(52, 50, 11), (59, 44, 10), (64, 37, 9), (67, 30, 8)]
            elif mode == "claw":
                thumb = [(52, 50, 11), (58, 45, 10), (61, 39, 9), (59, 33, 8)]
            else:
                thumb = [(50, 48, 11), (56, 42, 10), (54, 36, 9), (47, 33, 8)]
            s.path(_taper(thumb), fill=fill, stroke=INK, width=1.2)
            s.circle(thumb[-1][0], thumb[-1][1], 4, fill=fill, stroke=INK, width=1.2)
            for x, y, ln in ((26, 58, 9), (46, 60, 7), (17, 44, 7)):
                s.path(f"M{x - 1.8:.1f} {y:.1f} Q{x:.1f} {y + ln:.1f} {x + 1.8:.1f} {y:.1f} Z", fill=MUD, stroke=INK, width=0.6)
            if mode != "fist":  # two little foxfire eyes peering from the palm
                for ex, ey, rr in ((31, 39, 2.6), (42, 38, 2.9)):
                    s.circle(ex, ey, rr * 2.2, fill=s.radial(ex, ey, rr * 2.2, [(0, FIRE, 0.55), (1, FIRE, 0)]))
                    s.ellipse(ex, ey, rr * 0.8, rr, fill=s.radial(ex - 0.4, ey - 0.4, rr, [(0, FIRE_HOT), (0.7, FIRE), (1, "#6a8a20")]), stroke=INK, width=0.6)
            else:
                s.ellipse(36, 30, 2.2, 1.0, fill=FIRE, opacity=0.8)
                s.ellipse(44, 30, 2.4, 1.0, fill=FIRE, opacity=0.8)
            return s

        def fingertips():
            s = Svg(50, 16)
            for k, (x, h) in enumerate(((10, 8), (21, 12), (31, 11), (41, 7))):
                s.path(f"M{x - 3.6:.1f} 16 Q{x - 3.6:.1f} {16 - h:.1f} {x:.1f} {16 - h - 1:.1f} Q{x + 3.6:.1f} {16 - h:.1f} {x + 3.6:.1f} 16 Z",
                       fill=s.linear(0, 16 - h, 0, 16, [(0, MUD_HI), (1, MUD)]), stroke=INK, width=1.0)
            return s

        def bubble():
            s = Svg(14, 14)
            s.circle(7, 7, 5.6, fill=s.radial(5.5, 5.5, 7, [(0, "#8a6aa8", 0.5), (0.7, "#4a3458", 0.75), (1, "#2a1c30", 0.9)]), stroke="#b8a0d8", width=0.9)
            s.ellipse(5, 4.6, 1.8, 1.2, fill="#ffffff", opacity=0.85)
            return s

        def drip():
            s = Svg(8, 12)
            s.path("M4 1 Q7.2 7 6 9.5 Q4 11.6 2 9.5 Q0.8 7 4 1 Z", fill=s.linear(0, 1, 0, 11, [(0, MUD_HI), (1, MUD_DARK)]), stroke=INK, width=0.6)
            return s

        def splash():
            s = Svg(70, 24)
            for k, (x, h, lean) in enumerate(((8, 10, -6), (19, 16, -3), (31, 20, -1), (41, 21, 1), (52, 15, 3), (62, 10, 6))):
                s.path(f"M{x - 2.6:.1f} 23 Q{x + lean * 0.5:.1f} {23 - h * 0.5:.1f} {x + lean:.1f} {23 - h:.1f} Q{x + lean * 0.5 + 2.2:.1f} {23 - h * 0.45:.1f} "
                       f"{x + 2.6:.1f} 23 Z", fill=MUD_HI if k % 2 else MUD, stroke=INK, width=0.8)
                s.circle(x + lean * 1.5, 23 - h - 3.5, 1.8, fill=MUD, stroke=INK, width=0.6)
            return s

        return {"puddle_back": (puddle_back, (55, 14)), "puddle_front": (puddle_front, (55, 14)), "arm": (arm, (22, 100)),
                "hand_open": (lambda: hand("open"), (36, 62)), "hand_claw": (lambda: hand("claw"), (36, 62)), "hand_fist": (lambda: hand("fist"), (36, 62)),
                "fingertips": (fingertips, (25, 16)), "bubble": (bubble, (7, 7)), "drip": (drip, (4, 1)), "splash": (splash, (35, 23)),
                "glow": (lambda: _soft(90, 30, "#8a5ac8", 0.35), (45, 15))}

    def commands(self, e, t):
        out: list[DrawCommand] = []
        base_y = e.memory.get("base_y", e.y)
        # the puddle is fixed on the ground (base_y + h) whatever the hitbox does
        ground = -(e.y - base_y) / self.du
        travel = max(1.0, e.h)
        rise = 1.0 - max(0.0, min(1.0, (e.y - base_y) / travel)) if e.alive else 0.0
        anim = e.anim if e.alive else "defeat"
        st = e.state_time
        hidden_time = float(e.params.get("hidden_time", 2.0))
        puddle = Xf(0.0, ground)
        agitation = 0.0
        if anim == "hidden":
            agitation = _ease((st - (hidden_time - 0.75)) / 0.6)
        elif anim in ("rise", "retreat"):
            agitation = 1.0
        out.append(self.cmd("glow", puddle.child(0, -2), alpha=0.35 + 0.5 * agitation))
        out.append(self.cmd("puddle_back", puddle))
        # bubbles: slow when calm, boiling before the hand rises (telegraph)
        n = 2 + int(4 * agitation)
        speed = 0.6 + 2.6 * agitation
        for j in range(n):
            k = (t * speed + j * 0.37 + e.origin_x * 0.013) % 1
            bx = math.sin(j * 2.3 + e.origin_x) * 34
            out.append(self.cmd("bubble", puddle.child(bx, -2 - k * 3), scale=(0.4 + 0.9 * k) * (0.7 + 0.5 * agitation), alpha=1 - k * k))
        if anim == "hidden" and agitation > 0:
            wig = math.sin(t * 24) * 1.2
            out.append(self.cmd("fingertips", puddle.child(wig, 4 - 7 * agitation)))
        if not e.alive:
            # knocked: a limp claw tumbling out of the mud (defeat_xf flips it); squashed: flattened on the puddle
            knock = e.memory.get("defeat_kind") == "knock"
            root = self.defeat_xf(e, Xf(0.0, -40.0 if knock else ground))
            out.append(self.cmd("hand_claw", root))
        elif rise > 0.02:
            root = Xf(0.0, ground)
            sway = math.sin(t * 2.8) * 6 if anim in ("out", "bite") else 0.0
            length = max(0.05, rise * 0.4)  # hand (62 du) + arm (40 du) ≈ 1.15 × the hitbox height
            arm = Xf(root.x, root.y + 4, root.angle + sway * 0.4, root.sx, root.sy * length)
            out.append(self.cmd("arm", arm))
            wrist = Xf(*_xy(arm.child(0, -100)), arm.angle + sway * 0.6, root.sx, root.sy)
            if anim == "bite":
                k = (st % 0.6) / 0.25
                part = "hand_claw" if k < 0.35 else "hand_fist"
                squeeze = 1 - 0.08 * math.sin(min(1.0, k) * math.pi)
                out.append(self.cmd(part, Xf(wrist.x, wrist.y, wrist.angle, wrist.sx * squeeze, wrist.sy * (2 - squeeze))))
            elif anim in ("rise", "retreat"):
                k = min(1.0, st / 0.45)
                opening = k if anim == "rise" else 1 - k
                out.append(self.cmd("hand_claw" if opening < 0.6 else "hand_open", wrist))
            else:
                wig = math.sin(t * 7) * 4
                out.append(self.cmd("hand_open", Xf(wrist.x, wrist.y, wrist.angle + wig * 0.4, wrist.sx, wrist.sy)))
            for j in range(2):
                k = (t * 1.4 + j * 0.5) % 1
                out.append(self.cmd("drip", wrist.child(-12 + j * 22, -26 + k * (40 + 60 * rise)), alpha=1 - k, scale=0.9))
        if anim in ("rise", "retreat") and st < 0.4:
            k = st / 0.4
            out.append(self.cmd("splash", puddle.child(0, 2), scale=0.6 + 0.6 * k, alpha=1 - k))
        out.append(self.cmd("puddle_front", puddle))
        return _flash(e, t, out)


# =========================================================================== Ossada do Pântano
@register("bone_walker")
class BoneWalker(CreatureRig):
    """Heron skeleton: S-necked, dagger beak, ivory bones with moss and a lantern
    glow in the eye socket. Stalks on long legs; collapses into a heap when
    stomped (``pile``), rattles and rebuilds itself (``reassemble``)."""

    du = 0.37
    NECK = 6
    PIECES = ("shin1", "shank1", "foot1", "ribs", "vert0", "vert1", "vert2", "vert3", "vert4", "vert5", "skull", "wing", "shin0", "shank0", "foot0")
    FAR = ("shin1", "shank1", "foot1")
    PILE = {
        "shin0": Xf(-8, -3, 74), "shank0": Xf(12, -2, -96), "foot0": Xf(-28, -1, 12),
        "shin1": Xf(4, -6, 104), "shank1": Xf(-18, -4, -66), "foot1": Xf(26, -1, -8),
        "ribs": Xf(-2, -9, -168), "wing": Xf(4, -16, 26),
        "vert0": Xf(-24, -4, 30), "vert1": Xf(18, -6, -40), "vert2": Xf(-12, -13, 70), "vert3": Xf(28, -3, 10), "vert4": Xf(-30, -2, -20),
        "vert5": Xf(10, -15, 50),
        "skull": Xf(6, -23, -18),
    }

    def parts(self):
        bone = [(0, BONE_HI), (0.5, BONE), (1, BONE_DARK)]

        def skull():
            s = Svg(50, 24)
            d = ("M2 12 Q2 3 10 2.5 Q17 2 21 7 L48 11.5 L48.8 12.6 L21 15.5 Q18 20 12 21 Q3 21 2 12 Z")
            s.path(d, fill=s.linear(0, 2, 0, 21, bone), stroke=INK, width=1.3)
            s.path("M21 12.6 L46 12.2", stroke="#7a6a52", width=0.7, opacity=0.8)
            s.circle(11, 10.5, 5.2, fill="#140c10", stroke=INK, width=0.8)
            s.circle(11, 10.5, 2.6, fill=s.radial(11, 10.5, 2.8, [(0, AMBER_HOT), (0.6, AMBER), (1, AMBER_DEEP)]))
            s.path("M5 6 Q9 3.2 15 4.2", stroke="#ffffff", width=1.0, opacity=0.7)
            s.path(blob(8, 3.4, 6, 2.4, 0.3, seed=4), fill=MOSS)
            s.path("M5 5 q-1 4 0.4 7 M8 5.4 q-0.4 3 0.4 5", stroke=MOSS_DARK, width=1.1)
            return s

        def vert():
            s = Svg(12, 10)
            s.path("M1.5 3.4 Q6 0.8 10.5 3.4 L10.5 6.8 Q6 9.4 1.5 6.8 Z", fill=s.linear(0, 1, 0, 9, bone), stroke=INK, width=1.0)
            s.path("M3.5 3 L3.5 7.2 M8.5 3 L8.5 7.2", stroke="#9a8a6c", width=0.7, opacity=0.8)
            s.path("M4 2.6 Q6 1.6 8 2.6", stroke="#ffffff", width=0.7, opacity=0.7)
            return s

        def ribs():
            s = Svg(52, 40)
            # spine and pelvis/tail
            s.path("M4 9 Q16 4 30 7 Q40 9 47 6", stroke=INK, width=4.2)
            s.path("M4 9 Q16 4 30 7 Q40 9 47 6", stroke=BONE, width=2.6)
            s.path("M1 7 L6 4 L10 9 L4 14 Z", fill=BONE, stroke=INK, width=1.0)
            s.path(smooth_closed([(4, 10), (14, 8), (18, 15), (12, 20), (5, 17)], 0.7), fill=s.linear(0, 8, 0, 20, bone), stroke=INK, width=1.1)
            s.circle(12, 14, 2.2, fill="#2a1e1a")
            # ribs sweeping down to the keel
            for k in range(6):
                x0 = 20 + k * 4.6
                s.path(f"M{x0:.1f} 7.5 Q{x0 - 6:.1f} 18 {x0 - 2 + k * 0.6:.1f} {28 + k * 0.6:.1f}", stroke=INK, width=3.0)
                s.path(f"M{x0:.1f} 7.5 Q{x0 - 6:.1f} 18 {x0 - 2 + k * 0.6:.1f} {28 + k * 0.6:.1f}", stroke=BONE, width=1.7)
            # keel (sternum)
            s.path("M18 28 Q32 40 48 26 Q40 32 30 31 Q24 30 18 28 Z", fill=s.linear(0, 26, 0, 38, bone), stroke=INK, width=1.1)
            # moss patches and a hanging beard of moss
            s.path(blob(28, 6, 9, 3.2, 0.3, seed=7), fill=MOSS)
            s.path(blob(40, 7, 5, 2.2, 0.3, seed=9), fill=MOSS_HI)
            for k, (x, ln) in enumerate(((24, 12), (28, 18), (32, 10), (36, 15))):
                s.path(f"M{x - 1.4:.1f} 7 Q{x + (k % 2) * 2:.1f} {7 + ln * 0.6:.1f} {x + 0.5:.1f} {7 + ln:.1f} Q{x + 1.6:.1f} {7 + ln * 0.5:.1f} {x + 1.4:.1f} 7 Z",
                       fill="#8d9b8c", opacity=0.85)
            return s

        def wing():
            s = Svg(42, 16)
            for d, wd in (("M40 4 Q30 6 22 5", 3.4), ("M22 5 Q12 9 4 13", 2.6), ("M22 7 Q14 11 7 14", 1.8)):
                s.path(d, stroke=INK, width=wd + 1.6)
                s.path(d, stroke=BONE, width=wd)
            for x in (40, 22):
                s.circle(x, 4.6, 2.6, fill=BONE, stroke=INK, width=0.9)
            for x, y in ((10, 11.5), (15, 9.5)):
                s.line(x, y, x - 4, y + 4, MOSS_DARK, 1.0, 0.8)
            return s

        def long_bone(ln: float):
            s = Svg(8, ln + 4)
            s.path(f"M4 2 L4 {ln + 1:.1f}", stroke=INK, width=4.0)
            s.path(f"M4 2 L4 {ln + 1:.1f}", stroke=BONE, width=2.4)
            s.path(f"M4.5 3 L4.5 {ln:.1f}", stroke=BONE_HI, width=0.7, opacity=0.8)
            for y in (2.0, ln + 1):
                s.circle(4, y, 2.5, fill=BONE, stroke=INK, width=0.9)
            return s

        def foot():
            s = Svg(26, 10)
            for d in ("M8 2 L24 4.6", "M8 2 L19 8", "M8 2 L13 9", "M8 2 L1 6"):
                s.path(d, stroke=INK, width=3.0)
                s.path(d, stroke=BONE, width=1.6)
            s.circle(8, 2.2, 2.4, fill=BONE, stroke=INK, width=0.8)
            return s

        return {"skull": (skull, (4, 12)), "eye_glow": (lambda: _soft(26, 26, AMBER, 0.6, 0.06), (13, 13)), "vert": (vert, (6, 5)),
                "ribs": (ribs, (10, 12)), "wing": (wing, (40, 4.6)), "shin": (lambda: long_bone(32), (4, 2)), "shank": (lambda: long_bone(30), (4, 2)),
                "foot": (foot, (8, 2.2)), "bone": (lambda: long_bone(12), (4, 8))}

    def _stand(self, e, t: float, walking: bool) -> dict[str, Xf]:
        """Bone transforms of the standing skeleton (stalking gait while walking)."""
        ph = t * 5.2
        poses: dict[str, Xf] = {}
        bob = -abs(math.sin(ph)) * 2.0 if walking else math.sin(t * 2.0) * 0.8
        hip = Xf(-14, -68 + bob, 0)
        for i, off in ((0, 0.0), (1, math.pi)):
            p = ph + off
            swing = math.cos(p) if walking else 0.0
            lift = max(0.0, math.sin(p)) if walking else 0.0
            shin = hip.child(2 if i == 0 else -2, 0, -14 * swing - 6)
            shank = shin.child(0, 32, 36 * lift + 10)
            foot = shank.child(0, 30, -36 * lift - 4 + 10 * swing)
            poses[f"shin{i}"], poses[f"shank{i}"], poses[f"foot{i}"] = shin, shank, foot
        body = Xf(hip.x, hip.y, -6 + (math.sin(ph * 2) * 2 if walking else 0))
        poses["ribs"] = body
        poses["wing"] = body.child(36, -4, -4 + math.sin(t * 3) * 3)
        pump = math.sin(ph * 2) * 4 if walking else math.sin(t * 1.6) * 1.5
        # S-curved neck: overlapping vertebrae along a cubic curve from the shoulders to the skull
        p0, p1, p2, p3 = (37.0, -6.0), (58.0, -12.0), (20.0, -30.0), (40.0 + pump, -38.0)
        for j in range(self.NECK):
            u = (j + 0.5) / self.NECK
            bx = (1 - u) ** 3 * p0[0] + 3 * (1 - u) ** 2 * u * p1[0] + 3 * (1 - u) * u * u * p2[0] + u ** 3 * p3[0]
            by = (1 - u) ** 3 * p0[1] + 3 * (1 - u) ** 2 * u * p1[1] + 3 * (1 - u) * u * u * p2[1] + u ** 3 * p3[1]
            tx = 3 * (1 - u) ** 2 * (p1[0] - p0[0]) + 6 * (1 - u) * u * (p2[0] - p1[0]) + 3 * u * u * (p3[0] - p2[0])
            ty = 3 * (1 - u) ** 2 * (p1[1] - p0[1]) + 6 * (1 - u) * u * (p2[1] - p1[1]) + 3 * u * u * (p3[1] - p2[1])
            poses[f"vert{j}"] = body.child(bx, by, math.degrees(math.atan2(ty, tx)))
        poses["skull"] = body.child(41 + pump, -40, 8 + math.sin(t * 1.3) * 3)
        return poses

    def commands(self, e, t):
        out: list[DrawCommand] = []
        anim = e.anim if e.alive else ("pile" if e.state == "pile" else "walk")
        st = e.state_time
        stand = self._stand(e, t, anim == "walk" and e.alive)
        collapse = 0.0  # 0 = standing, 1 = heap
        shake = 0.0
        if anim in ("pile", "collapse"):
            collapse = _ease(st / 0.4) if (anim == "collapse" or st < 0.4) else 1.0
        elif anim == "reassemble":
            k = max(0.0, st - 3.2)  # the behaviour switches to 'reassemble' at 3.2 s of the pile
            if k < 0.35:
                collapse, shake = 1.0, 1.0
            else:
                u = min(1.0, (k - 0.35) / 0.4)
                collapse = 1.0 - u + math.sin(u * math.pi) * 0.12
        root = _root(self, e)
        glow_a = 1.0
        for name in self.PIECES:
            a = stand[name]
            b = self.PILE[name]
            if collapse <= 0:
                xf = a
            else:
                c = collapse
                drop = math.sin(min(1.0, c) * math.pi) * (10 if name in ("skull", "vert5", "wing") else 4)
                jx = math.sin(t * 60 + len(name) * 1.7) * 1.6 * shake
                jy = math.cos(t * 54 + len(name)) * 1.0 * shake
                xf = Xf(_lerp(a.x, b.x, c) + jx, _lerp(a.y, b.y, c) - drop + jy, _lerp(a.angle, b.angle, c) + jx * 3, 1, 1)
            world = root.child(xf.x, xf.y, xf.angle)
            part = name.rstrip("0123456789")
            out.append(self.cmd(part, world, tint=(196, 186, 176) if name in self.FAR else None))
            if name == "skull":
                if anim == "pile" and st >= 0.4:
                    glow_a = 0.25 + 0.2 * (math.sin(t * 9) > 0.6)
                elif anim == "reassemble":
                    glow_a = 0.4 + 0.6 * _ease((st - 3.2) / 0.75)
                if e.alive:
                    out.append(self.cmd("eye_glow", world.child(7, -1.5), alpha=glow_a))
        if not e.alive:
            out = [c for c in out if c.part != self.part_id("eye_glow")]
        return _flash(e, t, out)
