"""Floresta Encantada creatures: Cogumelo Saltitante, Caracol-Musgo,
Mariposa-Lume, Planta-de-Esporos, Besouro-Casca, Arbusto-Espreita and
Aranha-do-Cipó.

Night-world readability: every creature keeps the dark ink outline, a cool
moonlit rim on its top edge and a light source of its own (glowing spots,
wings, eyes or spores) so it separates from the blue-teal backdrop. The moss,
stone and glow colours are shared with the world art set, so the camouflaged
creatures (the snail as a mossy stone, the lurking bush) truly blend in until
they move.
"""

from __future__ import annotations

import math

from ..rig import DrawCommand, Xf, smoothstep
from ..svg import Svg, blob, shade, smooth_closed, smooth_open, star_points
from ..worlds.enchanted_forest import GLOW_CYAN, GLOW_GOLD, MOSS, STONE, STONE_DARK, STONE_LIGHT, _curve, _glow, _leaf, _taper
from .base import INK, CreatureRig, register

HIT_TINT = (255, 150, 160)
FAR_TINT = (150, 165, 185)  # far-side limbs sit in shadow
RIM = "#d8f4ff"  # moonlight rim


def _flash(out: list[DrawCommand], e, t: float) -> list[DrawCommand]:
    """Hit flash on alternate frames while the damage timer runs."""
    if e.alive and e.hit_timer > 0 and int(t * 20) % 2 == 0:
        for c in out:
            c.tint = HIT_TINT
    return out


def _scaled(xf: Xf, sx: float, sy: float) -> Xf:
    return Xf(xf.x, xf.y, xf.angle, xf.sx * sx, xf.sy * sy)


def _halo_part(w: float, h: float, color: str, alpha: float) -> Svg:
    s = Svg(w, h)
    _glow(s, w / 2, h / 2, min(w, h) / 2, color, alpha)
    return s


def _cross_part(size: float = 12.0) -> Svg:
    s = Svg(size, size + 2)
    a, b = size * 0.22, size * 0.78
    s.path(f"M{a:.2f} {a + 1:.2f} L{b:.2f} {b + 1:.2f} M{b:.2f} {a + 1:.2f} L{a:.2f} {b + 1:.2f}", stroke=INK, width=size * 0.14)
    return s


def _star_part() -> Svg:
    s = Svg(16, 16)
    _glow(s, 8, 8, 8, "#fff3b0", 0.5)
    s.polygon(star_points(8, 8, 6.5, 2.8, 5), fill="#ffe27a", stroke=INK, width=0.9)
    return s


def _moss_cap(s: Svg, left: float, right: float, top_pts: list[tuple[float, float]], lip: float, seed: int, strands: int = 7) -> None:
    """Terrain-style moss cushion with drooping strands over [left, right]."""
    top_c, body_c, dark_c, deep_c, rim_c = MOSS["normal"]
    fringe = [(right, lip)]
    for k in range(strands):
        x = right - (k + 0.5) * (right - left) / strands
        ln = 2.0 + 6.0 * ((math.sin(seed * 3.1 + k * 2.3) + 1) / 2) ** 2
        fringe += [(x + 1.6, lip + 0.5), (x, lip + ln), (x - 1.6, lip + 0.5)]
    fringe.append((left, lip))
    d = smooth_open(top_pts, 0.8) + f"L{fringe[0][0]:.2f} {fringe[0][1]:.2f}" + _curve(fringe, 0.7) + "Z"
    y_top = min(y for _, y in top_pts)
    s.path(d, fill=s.linear(0, y_top, 0, lip + 8, [(0, top_c), (0.3, body_c), (0.7, dark_c), (1, deep_c)]))
    s.path(smooth_open(fringe, 0.7), stroke=shade(deep_c, -0.5), width=1.0)
    s.path(smooth_open(top_pts, 0.8), stroke=rim_c, width=1.3, opacity=0.85)


# ============================================================================ Cogumelo Saltitante
def _bell_cap() -> Svg:
    """Tall indigo bell (inkcap-like) whose frayed brim is lit from below by luminous gills."""
    s = Svg(70, 62)
    cx = 35.0
    # the shadowed underside: dark bowl lined with glowing gill lines
    s.path(f"M8 43.5 Q{cx} 66 62 43.5 Z", fill=s.radial(cx, 46, 30, [(0, "#07061a"), (0.7, "#130e32"), (1, "#271c56")]), stroke=INK,
           width=1.3)
    for i in range(13):
        x = 10 + i * 50 / 12
        s.line(x, 44.6, x + (cx - x) * 0.55, 44.6 + 10.5 * 0.55, "#5ff0d6", 0.9, 0.9)
    s.path(f"M9 44.4 Q{cx} 49.5 61 44.4", stroke="#9ffbe9", width=1.2, opacity=0.8)
    # the bell, with a frayed (scalloped) brim
    def scallops(dy: float) -> str:
        return "".join(f"Q{65 - (i + 0.5) * 7.5:.2f} {47.6 + dy:.2f} {65 - (i + 1) * 7.5:.2f} {44 + dy:.2f}" for i in range(8))

    bell = f"M5 44 C6 36 10 27 15 19.5 C20 11 27 6 {cx} 6 C43 6 50 11 55 19.5 C60 27 64 36 65 44 {scallops(0)} Z"
    s.path(bell, fill=s.linear(0, 6, 0, 46, [(0, "#6c56c8"), (0.45, "#3a2a8c"), (1, "#1c1552")]))
    s.path(bell, fill=s.radial(24, 16, 28, [(0, "#b4a4ff", 0.5), (1, "#b4a4ff", 0)]))
    s.path(bell, fill=s.linear(0, 33, 0, 47, [(0, "#5ff0d6", 0), (1, "#5ff0d6", 0.38)]))  # gill light creeping up the rim
    for k in range(-3, 4):  # striate grooves running down from the apex
        top = (cx + k * 2.2, 10 + abs(k) * 1.2)
        mid = (cx + k * 6.6, 26)
        bot = (cx + k * 8.4, 43)
        s.path(f"M{top[0]:.2f} {top[1]:.2f} Q{mid[0]:.2f} {mid[1]:.2f} {bot[0]:.2f} {bot[1]:.2f}", stroke="#251a62", width=1.2, opacity=0.65)
        s.path(f"M{top[0] + 1.2:.2f} {top[1] + 1:.2f} Q{mid[0] + 1.4:.2f} {mid[1]:.2f} {bot[0] + 1.4:.2f} {bot[1] - 1:.2f}", stroke="#8a78e0",
               width=0.6, opacity=0.4)
    s.path(bell, stroke=INK, width=1.8)
    s.path(f"M65 43 {scallops(-1.0)}", stroke="#7af0d8", width=0.8, opacity=0.75)  # the brim catches the gill light
    s.path("M9.5 35 C12 24 22 10.5 35 8.5", stroke="#dccfff", width=1.7, opacity=0.55)  # moonlit edge
    return s


def _gill_eye(kind: str) -> Svg:
    """Glowing eyes peering out of the shadow under the brim (no pupils)."""
    s = Svg(14, 12)
    glow = s.radial(7, 6, 3.8, [(0, "#ffffff"), (0.55, "#e2fff8"), (1, "#7aeedd")])
    if kind == "x":
        s.path("M4.6 3.6 L9.4 8.4 M9.4 3.6 L4.6 8.4", stroke="#8aa4ac", width=1.3)
        return s
    _glow(s, 7, 6, 6, "#9ffbe9", 0.75)
    if kind == "wide":
        s.ellipse(7, 6, 3.1, 3.7, fill=glow)
    elif kind == "narrow":  # determined squint: lid cut at a slant
        s.path("M4.2 5.2 L9.8 4.0 Q9.9 8.4 7 8.5 Q4.2 8.4 4.2 5.2 Z", fill=glow)
    elif kind == "shut":
        s.path("M4.2 6.2 Q7 8.2 9.8 6.2", stroke="#c8fff4", width=1.4)
    else:
        s.ellipse(7, 6.2, 2.5, 3.0, fill=glow)
    return s


def _coil_stalk() -> Svg:
    """Thin springy stalk wound like a coil, with a small bulb at the base."""
    s = Svg(16, 26)
    pts = [(8 + 3.0 * math.sin(i * 22 / 16 * 0.62 + 0.4), 24 - i * 22 / 16) for i in range(17)]
    s.path(smooth_open(pts), stroke=INK, width=5.4)
    s.path(smooth_open(pts), stroke="#bfc7e8", width=3.6)
    s.path(smooth_open([(x - 0.8, y) for x, y in pts]), stroke="#f4f7ff", width=1.1, opacity=0.7)
    s.ellipse(8, 23.6, 4.6, 2.2, fill=s.linear(0, 21.5, 0, 26, [(0, "#d6dcf2"), (1, "#7c78a8")]), stroke=INK, width=1.0)
    return s


def _root_foot() -> Svg:
    """Rootlet toes spreading over the ground, one tip glowing."""
    s = Svg(22, 10)
    for dx, dy, wd in ((-9, 3.6, 2.6), (0.5, 6.0, 2.8), (9, 3.2, 2.4)):
        s.path(_taper([(11, 2.2, wd + 0.8), (11 + dx * 0.55, 2.2 + dy * 0.6, wd), (11 + dx, 2.2 + dy, 0.6)]), fill="#5e4c72", stroke=INK,
               width=0.6)
    _glow(s, 20, 5.4, 2.6, GLOW_CYAN, 0.7)
    s.ellipse(11, 2.6, 3.2, 1.8, fill="#7a6a92", stroke=INK, width=0.6)
    return s


@register("mushroom")
class HopMushroom(CreatureRig):
    """Bell-capped inkcap on a coiled, springy stalk. Its eyes glow from the
    shadow under the brim; the coil compresses (anticipation) before every
    hop, stretches on the way up and the bell flares like a parachute on the
    way down."""

    du = 0.5
    STALK = 20.0  # where the bell sits on the coil (its top hides inside the dark gill bowl)

    def parts(self):
        eyes = {f"eye{suffix}": ((lambda k=kind: _gill_eye(k)), (7, 6))
                for suffix, kind in (("", "open"), ("_wide", "wide"), ("_narrow", "narrow"), ("_shut", "shut"), ("_x", "x"))}
        return {"halo": (lambda: _halo_part(110, 84, "#7af0d8", 0.45), (55, 42)), "cap": (_bell_cap, (35, 52)),
                "stalk": (_coil_stalk, (8, 24)), "foot": (_root_foot, (11, 2.2)), **eyes}

    def commands(self, e, t):
        root = Xf()
        if not e.alive:
            root = self.defeat_xf(e, root)
        st = e.anim if e.alive else "defeat"
        coil, coil_w = 1.0, 1.0
        cap_sx = cap_sy = 1.0
        tilt = shake = 0.0
        feet_dx, feet_dy = 6.0, 0.0
        eye = "eye"
        glow = 0.8 + 0.2 * math.sin(t * 2.4 + e.origin_x)
        if st == "crouch":  # anticipation: the coil winds down, the bell leans in, the gills brighten
            k = smoothstep(e.state_time / 0.28)
            coil, coil_w = 1 - 0.55 * k, 1 + 0.25 * k
            cap_sx, cap_sy, tilt = 1 + 0.1 * k, 1 - 0.1 * k, 7.0 * k
            feet_dx = 6 + 4 * k
            shake = math.sin(t * 70) * 0.8 * k
            eye, glow = "eye_narrow", min(1.0, 0.8 + 0.3 * k)
        elif st == "jump":
            coil, coil_w = 1.5, 0.85
            cap_sx, cap_sy, tilt = 0.94, 1.06, -6.0
            feet_dx, feet_dy = 4.0, -2.0
            eye = "eye_wide"
        elif st == "fall":  # the bell flares like a parachute
            coil, coil_w = 1.15, 0.95
            cap_sx, cap_sy = 1.14, 0.88
            feet_dy = 2.0
            eye = "eye_wide"
        elif st == "land":
            k = 1 - min(1.0, e.state_time / 0.18)
            coil, coil_w = 1 - 0.5 * k, 1 + 0.25 * k
            cap_sx, cap_sy = 1 + 0.14 * k, 1 - 0.12 * k
            feet_dx = 6 + 4 * k
            eye = "eye_shut" if k > 0.45 else "eye"
        elif st == "defeat":
            eye, glow = "eye_x", 0.35
        else:  # idle: the coil breathes and the bell sways
            coil = 1 + 0.05 * math.sin(t * 3.2 + e.origin_x)
            tilt = 2.0 * math.sin(t * 1.7 + e.origin_x)
        if eye == "eye" and self.blink(t, e.origin_x):
            eye = "eye_shut"
        stalk = Xf(root.x + shake, root.y, root.angle, root.sx * coil_w, root.sy * coil)
        top = root.child(shake, -self.STALK * coil)
        cap = Xf(top.x, top.y, root.angle + tilt, root.sx * cap_sx, root.sy * cap_sy)
        out = [self.cmd("halo", cap.child(0, -6), alpha=glow)]
        out += [self.cmd("foot", root.child(-feet_dx, feet_dy)), self.cmd("foot", root.child(feet_dx, feet_dy))]
        out.append(self.cmd("stalk", stalk))
        out.append(self.cmd("cap", cap))
        for ex, ey in ((7.0, -4.0), (18.0, -5.0)):
            out.append(self.cmd(eye, cap.child(ex, ey)))
        return _flash(out, e, t)


# ============================================================================ Caracol-Musgo
def _moss_shell() -> Svg:
    """Snail shell that is a mossy stone: retracted, it is just another rock."""
    s = Svg(64, 56)
    pts = [(5, 51), (3, 33), (11, 13), (30, 4), (49, 8), (60, 26), (60, 51), (32, 54)]
    s.path(smooth_closed(pts, 0.7), fill=s.radial(24, 18, 46, [(0, STONE_LIGHT), (0.45, STONE), (1, STONE_DARK)]), stroke=INK, width=1.8)
    spiral = []
    for i in range(46):
        a = i * 0.28
        rad = 1.6 + i * 0.36
        spiral.append((35 + math.cos(a) * rad, 33 + math.sin(a) * rad * 0.86))
    s.path(smooth_open(spiral), stroke="#33404c", width=1.6, opacity=0.55)
    for x, y, rad in ((14, 40, 2.4), (22, 46, 1.6), (50, 42, 2.0), (44, 48, 1.4)):
        s.circle(x, y, rad, fill="#b8c8a8", opacity=0.6)
    s.path("M42 52.5 Q50 49.5 58 51.5", stroke="#1c242c", width=1.8, opacity=0.45)  # the opening, tucked under the front
    _moss_cap(s, 5, 59, [(5, 30), (11, 15), (22, 7), (32, 4.5), (43, 6.5), (53, 13), (59, 24)], 26, 5, strands=8)
    _glow(s, 46, 8, 7, GLOW_CYAN, 0.5)
    s.path("M45 9 Q44.5 5 46 2.5", stroke="#cfe8e0", width=1.0)
    s.path("M43.4 3.2 Q46 0.6 48.6 3.2 Q46 2.4 43.4 3.2 Z", fill="#58ddd2", stroke=INK, width=0.5)
    s.path(_leaf(20, 6.5, 7, 1.8, -130), fill="#7ad89a")
    s.path(_leaf(23, 5.5, 6, 1.6, -60), fill="#5dc28c")
    return s


@register("moss_snail")
class MossSnail(CreatureRig):
    du = 0.5

    def parts(self):
        def body():
            s = Svg(72, 30)
            s.path(smooth_closed([(2, 26), (10, 17), (34, 12), (58, 14), (69, 22), (67, 28), (34, 29)], 0.7),
                   fill=s.linear(0, 11, 0, 29, [(0, "#c6d8e4"), (0.55, "#8aa2b8"), (1, "#5a7088")]), stroke=INK, width=1.6)
            s.path("M8 25 Q34 28 64 25", stroke="#e4f0f8", width=1.2, opacity=0.7)
            for x in (16, 28, 40, 52):
                _glow(s, x, 21, 3.6, GLOW_CYAN, 0.6)
                s.circle(x, 21, 1.1, fill="#e6fffa")
            return s

        def head():
            s = Svg(26, 26)
            s.path(blob(13, 15, 10, 9, 0.04, seed=1), fill=s.radial(10, 11, 13, [(0, "#e2eef6"), (1, "#8aa2b8")]), stroke=INK, width=1.5)
            s.path("M10 19.5 Q14 22.5 18 19.5", stroke=INK, width=1.3)
            s.ellipse(19, 16, 2.4, 1.5, fill="#f2a8c8", opacity=0.6)
            s.path("M7 9 Q12 5.5 17 8", stroke=RIM, width=1.2, opacity=0.6)
            return s

        def stalk():
            s = Svg(12, 22)
            s.path("M6 21 Q5 12 6 6", stroke="#6f88a0", width=3.2)
            s.path("M6 21 Q5 12 6 6", stroke="#c6d8e4", width=1.6)
            s.circle(6, 5.5, 4.2, fill="#ffffff", stroke=INK, width=1.1)
            s.circle(7, 5.8, 2.1, fill="#2a2238")
            s.circle(7.7, 5.0, 0.7, fill="#ffffff")
            return s

        def peek():
            s = Svg(20, 10)
            s.ellipse(10, 5.5, 9, 4.2, fill="#141a22")
            for x in (6, 13.5):
                s.circle(x, 5.2, 2.6, fill="#ffffff", stroke=INK, width=0.6)
                s.circle(x + 0.7, 5.6, 1.3, fill="#2a2238")
            return s

        def streak():
            s = Svg(40, 26)
            for k, y in enumerate((5, 13, 21)):
                s.path(f"M2 {y} L{36 - k * 6} {y - 1.2} L{36 - k * 6} {y + 1.2} Z", fill="#e6fff6", opacity=0.45)
            return s

        return {"body": (body, (34, 28)), "head": (head, (8, 22)), "stalk": (stalk, (6, 21)), "peek": (peek, (10, 5)),
                "shell": (_moss_shell, (32, 53)), "shell_spin": (_moss_shell, (32, 30)), "streak": (streak, (40, 13))}

    def commands(self, e, t):
        root = Xf()
        if not e.alive:
            root = self.defeat_xf(e, root)
        state = e.anim
        retracted = state in ("shell", "slide", "wake") or (not e.alive and e.state in ("shell", "slide"))
        if retracted:
            if state == "slide" and e.alive:
                spin = (t * 900) % 360
                return _flash([self.cmd("streak", root.child(-22, -27), alpha=0.8),
                               self.cmd("shell_spin", Xf(root.x, root.y - 23 * root.sy, spin, root.sx, root.sy))], e, t)
            if state == "wake" and e.alive:
                shake = math.sin(t * 38) * 4
                out = [self.cmd("shell", root.child(0, 0, shake))]
                if int(t * 3) % 3 != 0:
                    out.append(self.cmd("peek", root.child(15, -7, shake * 0.5)))
                return _flash(out, e, t)
            breathe = 1 + 0.015 * math.sin(t * 1.6)
            return _flash([self.cmd("shell", _scaled(root, 1.0, breathe))], e, t)
        ph = t * 4.0
        stretch = 1 + 0.07 * math.sin(ph)
        body = _scaled(root, stretch, 1.0)
        head = root.child(26 * stretch, -5)
        out = [self.cmd("body", body)]
        if e.alive:
            out.append(self.cmd("stalk", head.child(1, -15, -16 + math.sin(t * 3) * 8), tint=FAR_TINT))
            out.append(self.cmd("stalk", head.child(6, -16, 6 + math.sin(t * 3 + 1) * 8)))
        out.append(self.cmd("head", head.child(0, 0, math.sin(ph) * 3)))
        out.append(self.cmd("shell", root.child(-8, -6, math.sin(ph) * 2.5)))
        return _flash(out, e, t)


# ============================================================================ Mariposa-Lume
@register("moth")
class GlowMoth(CreatureRig):
    """Fuzzy moth whose wings glow; the light pulses with each wingbeat."""

    du = 0.5

    def parts(self):
        def wing_fore():
            s = Svg(64, 46)
            d = "M6 42 C10 26 22 6 40 3 C52 1 62 6 61 13 C60 22 50 30 38 34 C26 38 14 40 6 42 Z"
            s.path(d, fill=s.radial(32, 18, 40, [(0, "#fbfff2"), (0.35, "#c2fae0"), (0.72, "#52c6b4"), (1, "#1d6476")]), stroke="#163040",
                   width=1.4)
            for ex, ey in ((40, 6), (56, 9), (52, 24), (30, 33)):
                s.line(7, 41, ex, ey, "#ffffff", 0.8, 0.5)
            s.ellipse(41, 17, 7.4, 6.2, fill="#1f5a66")
            s.ellipse(41, 17, 5.8, 4.8, fill=s.radial(41, 17, 6, [(0, "#fffbe0"), (0.55, "#ffd45a"), (1, "#e0902a")]))
            s.ellipse(41, 17, 2.6, 2.0, fill="#7ae8d8")
            for k in range(6):
                a = math.radians(-60 + k * 22)
                s.circle(40 + math.cos(a) * 19, 18 + math.sin(a) * 15, 1.2, fill="#ffffff", opacity=0.8)
            return s

        def wing_hind():
            s = Svg(48, 38)
            d = "M6 6 C14 2 30 4 40 12 C47 18 44 30 34 34 C22 37 12 26 6 6 Z"
            s.path(d, fill=s.radial(26, 18, 30, [(0, "#eafff4"), (0.45, "#8eeacc"), (1, "#24707a")]), stroke="#163040", width=1.3)
            s.ellipse(31, 23, 4.4, 3.6, fill="#1f5a66")
            s.ellipse(31, 23, 3.2, 2.6, fill="#ffd45a")
            s.ellipse(31, 23, 1.3, 1.0, fill="#7ae8d8")
            s.line(7, 7, 38, 30, "#ffffff", 0.8, 0.45)
            return s

        def body():
            s = Svg(46, 26)
            s.path(smooth_closed([(3, 13), (10, 7), (24, 5), (34, 7), (40, 12), (34, 19), (22, 20), (9, 18)], 0.8),
                   fill=s.radial(30, 9, 26, [(0, "#fff8ea"), (0.5, "#dccaf0"), (1, "#8a6aac")]), stroke=INK, width=1.4)
            for x in (10, 16, 22):
                s.path(f"M{x} 7.5 Q{x - 2.5} 13 {x} 18.5", stroke="#7a5a9a", width=1.1, opacity=0.6)
            for k in range(8):
                a = math.radians(200 + k * 20)
                s.line(30 + math.cos(a) * 9, 12 + math.sin(a) * 6, 30 + math.cos(a) * 11.5, 12 + math.sin(a) * 7.8, "#fff8ea", 1.0, 0.8)
            for lx in (26, 32):
                s.path(f"M{lx} 18 L{lx - 2} 24", stroke=INK, width=1.0)
            return s

        def head():
            s = Svg(28, 28)
            s.path("M12 10 Q14 2 22 1.5 M12 10 Q12 3.5 17 1.6", stroke="#4a3a5a", width=0.9)
            for k in range(5):
                x = 14 + k * 1.6
                y = 6.5 - k * 1.1
                s.line(x, y, x + 1.6, y - 1.6, "#4a3a5a", 0.6)
            s.circle(12, 15, 8, fill=s.radial(10, 12, 10, [(0, "#fff8ea"), (1, "#c2a8dc")]), stroke=INK, width=1.3)
            s.circle(16.5, 15, 5, fill=s.radial(15.5, 13.5, 5.5, [(0, "#5a4a7a"), (1, "#1a1428")]), stroke=INK, width=0.8)
            s.circle(17.6, 13.4, 1.4, fill="#ffffff")
            s.circle(15.2, 16.8, 0.6, fill="#ffffff", opacity=0.7)
            return s

        return {"halo": (lambda: _halo_part(150, 130, "#c8ffe0", 0.55), (75, 65)), "wing_fore": (wing_fore, (6, 42)),
                "wing_hind": (wing_hind, (6, 6)), "body": (body, (24, 13)), "head": (head, (8, 15)),
                "eye_x": (lambda: _cross_part(10), (5, 6))}

    def commands(self, e, t):
        root = Xf()
        if not e.alive:
            root = self.defeat_xf(e, root)
        flap = math.sin(t * 13.0) if e.alive else -0.6
        open_ = 0.5 + 0.5 * flap
        body = root.child(0, -24, math.sin(t * 3.0) * 5 if e.alive else 0)
        out = [self.cmd("halo", root.child(0, -27), alpha=(0.7 + 0.3 * open_) if e.alive else 0.35)]
        shoulder = body.child(6, -4)

        def fore(phase: float) -> Xf:
            k = 0.5 + 0.5 * math.sin(t * 13.0 + phase) if e.alive else 0.2
            return Xf(shoulder.x, shoulder.y, shoulder.angle - 18 + 26 * k, shoulder.sx, shoulder.sy * (0.3 + 0.7 * k))

        def hind(phase: float) -> Xf:
            k = 0.5 + 0.5 * math.sin(t * 13.0 + phase) if e.alive else 0.2
            hip = body.child(0, 1)
            return Xf(hip.x, hip.y, hip.angle + 12 - 18 * k, hip.sx, hip.sy * (0.45 + 0.55 * k))

        out.append(self.cmd("wing_fore", fore(0.5), tint=FAR_TINT, alpha=0.9))
        out.append(self.cmd("wing_hind", hind(0.5), tint=FAR_TINT, alpha=0.9))
        out.append(self.cmd("body", body))
        head = body.child(14, -1)
        out.append(self.cmd("head", head))
        if not e.alive:
            out.append(self.cmd("eye_x", head.child(8, -1)))
        out.append(self.cmd("wing_hind", hind(0.0)))
        out.append(self.cmd("wing_fore", fore(0.0)))
        return _flash(out, e, t)


# ============================================================================ Planta-de-Esporos
@register("spore_plant")
class SporePlant(CreatureRig):
    """Giant bud on a rosette of leaves: swells and trembles while charging,
    contracts and puffs a violet spore cloud when it fires."""

    du = 0.5

    def parts(self):
        def leaves():
            s = Svg(84, 28)
            for ang, ln in ((-172, 36), (-140, 30), (-40, 30), (-8, 36)):
                a = math.radians(ang)
                cx, cy = 42 + math.cos(a) * ln * 0.5, 24 + math.sin(a) * ln * 0.5
                s.path(_leaf(cx, cy, ln, 6.5, ang), fill=s.linear(0, 6, 0, 26, [(0, "#7ac88e"), (1, "#245a3e")]), stroke=INK, width=1.2)
                s.line(42 + math.cos(a) * 4, 24 + math.sin(a) * 4, 42 + math.cos(a) * ln * 0.9, 24 + math.sin(a) * ln * 0.9, "#b4f0c0", 0.8, 0.7)
            return s

        def stem():
            s = Svg(18, 18)
            s.path("M4 17 Q5 8 6 2 L12 2 Q13 8 14 17 Z", fill=s.linear(4, 0, 14, 0, [(0, "#3a8a5a"), (1, "#1e4e36")]), stroke=INK, width=1.3)
            return s

        def bud():
            s = Svg(58, 56)
            d = "M29 54 C11 54 4 40 8 29 C12 18 21 11 29 3 C37 11 46 18 50 29 C54 40 47 54 29 54 Z"
            s.path(d, fill=s.linear(0, 3, 0, 54, [(0, "#e4b0ff"), (0.45, "#9452c8"), (0.8, "#4a5a6a"), (1, "#2a5038")]), stroke=INK, width=1.8)
            for x in (15, 23, 35, 43):  # ribs converging on the tip
                s.path(f"M{x} 50 Q{x + (29 - x) * 0.3:.1f} 28 29 6", stroke="#5a2a7a", width=1.2, opacity=0.55)
            s.path("M17 22 Q22 12 29 7", stroke="#ffffff", width=2.0, opacity=0.45)
            for x, y, rad in ((18, 34, 1.6), (24, 24, 1.3), (33, 40, 1.5), (40, 30, 1.2), (14, 42, 1.1), (27, 46, 1.2)):
                _glow(s, x, y, rad * 3.2, "#f0c8ff", 0.55)
                s.circle(x, y, rad, fill="#fbeaff")
            # puckered vent facing forward
            s.ellipse(47, 23, 4.2, 5.4, fill="#2a1030", stroke="#ffb8ec", width=1.6)
            for a in (-60, -20, 20, 60):
                r_ = math.radians(a)
                s.line(47 + math.cos(r_) * 4.2, 23 + math.sin(r_) * 5.4, 47 + math.cos(r_) * 6.4, 23 + math.sin(r_) * 7.4, "#5a2a6a", 1.0)
            # narrow glowing eyes under a frowning ridge
            for ex in (30, 39.5):
                _glow(s, ex, 34, 4.6, GLOW_GOLD, 0.6)
                s.path(f"M{ex - 3.6} 34 Q{ex} 31 {ex + 3.6} 34 Q{ex} 36.6 {ex - 3.6} 34 Z", fill="#ffe27a", stroke=INK, width=0.8)
                s.line(ex, 32.2, ex, 35.8, "#2a1a10", 1.1)
            s.path("M26 30.5 L34 31.5 M36 31.5 L43.5 30", stroke=INK, width=1.4)
            return s

        def puff():
            s = Svg(46, 36)
            for cx, cy, rad, a in ((10, 18, 7, 0.75), (20, 13, 9, 0.7), (21, 23, 8, 0.65), (32, 17, 10, 0.55), (38, 26, 6, 0.45)):
                s.circle(cx, cy, rad, fill=s.radial(cx - 2, cy - 2, rad * 1.2, [(0, "#fbe8ff", a), (0.6, "#d08ae8", a * 0.8), (1, "#9a4ac0", 0)]))
            for x, y in ((14, 8), (28, 6), (40, 12), (34, 30), (24, 31)):
                s.circle(x, y, 1.1, fill="#ffffff", opacity=0.9)
            return s

        return {"glow": (lambda: _halo_part(110, 110, "#e0a8ff", 0.5), (55, 55)), "leaves": (leaves, (42, 24)), "stem": (stem, (9, 17)),
                "bud": (bud, (29, 54)), "puff": (puff, (4, 18))}

    @staticmethod
    def _charge_progress(e) -> float:
        interval = float(e.params.get("interval", 2.2))
        phase = e.timer % interval
        return max(0.0, min(1.0, 1 - (interval - phase) / 0.45))

    def commands(self, e, t):
        root = Xf()
        if not e.alive:
            root = self.defeat_xf(e, root)
        state = e.anim if e.alive else "defeat"
        sway = math.sin(t * 1.8 + e.origin_x) * 3
        sx = sy = 1.0
        glow = 0.45 + 0.1 * math.sin(t * 2.2)
        fired = 0.0
        if state == "charge":
            k = smoothstep(self._charge_progress(e))
            tremble = math.sin(t * 46) * 0.035 * (0.4 + k)
            sx, sy = 1 + 0.2 * k + tremble, 1 + 0.16 * k - tremble
            glow = 0.55 + 0.45 * k
            sway *= 0.3
        elif state == "fire":
            fired = 1 - max(0.0, min(1.0, e.memory.get("fired", 0.0) / 0.25))
            k = smoothstep(fired)
            sx, sy = 1.14 - 0.14 * k, 0.8 + 0.2 * k
            glow = 1.0 - 0.5 * k
        elif state == "defeat":
            sx, sy, glow = 1.0, 0.92, 0.2
        stem = root.child(0, -4, sway * 0.4)
        bud = _scaled(stem.child(0, -12, sway), sx, sy)
        out = [self.cmd("glow", bud.child(0, -26), alpha=glow), self.cmd("leaves", root), self.cmd("stem", stem), self.cmd("bud", bud)]
        if state == "fire":
            out.append(self.cmd("puff", bud.child(20, -31), scale=0.7 + 0.7 * fired, alpha=max(0.0, 1 - fired * 0.9)))
        return _flash(out, e, t)


# ============================================================================ Besouro-Casca
def _bark_shell(kind: str) -> Svg:
    """Beetle elytra made of tree bark (normal, cracked after a hit, or bristling with thorns)."""
    s = Svg(90, 76)
    with s.group("translate(2 14)"):  # headroom for the thorns
        if kind == "guard":  # bark thorns bristle out: not safe to stomp
            for k in range(7):
                a = math.radians(-160 + k * 23.3)
                bx, by = 43 + math.cos(a) * 30, 56 + math.sin(a) * 44
                tx, ty = 43 + math.cos(a) * 44, 56 + math.sin(a) * 62
                nx, ny = -math.sin(a) * 5.4, math.cos(a) * 5.4
                s.polygon([(bx - nx, by - ny), (tx, ty), (bx + nx, by + ny)], fill=s.linear(bx, by, tx, ty, [(0, "#6a5444"), (1, "#f0e2c4")]),
                          stroke=INK, width=1.0)
        d = "M4 58 C2 32 18 8 43 6 C68 8 84 32 82 58 Q43 62 4 58 Z"
        s.path(d, fill=s.linear(4, 0, 82, 0, [(0, "#3e2e26"), (0.32, "#76604e"), (0.62, "#8a735c"), (1, "#3a2a22")]), stroke=INK, width=2.0)
        for k in range(-3, 4):
            x = 43 + k * 10.5
            top = 10 + abs(k) * 4.5
            s.path(f"M{43 + k * 4:.1f} {top:.1f} Q{x + k * 1.5:.1f} {top + 22:.1f} {x + k * 2:.1f} 57", stroke="#2a1c16", width=1.7, opacity=0.75)
            s.path(f"M{43 + k * 4 + 2.2:.1f} {top + 2:.1f} Q{x + k * 1.5 + 2.2:.1f} {top + 22:.1f} {x + k * 2 + 2:.1f} 55", stroke="#b49a7c",
                   width=0.8, opacity=0.45)
        for y in (26, 40):
            s.path(f"M{12 + (y - 26) * 0.2:.1f} {y} l6 1.5 M{56} {y + 3} l7 -1", stroke="#2a1c16", width=1.2, opacity=0.6)
        for x, y, rad in ((22, 34, 4.6), (60, 26, 3.6), (50, 46, 3.0), (30, 50, 2.4)):
            s.path(blob(x, y, rad, rad * 0.7, 0.3, seed=x), fill="#a9bf9a", opacity=0.75)
            s.circle(x + rad * 0.3, y - rad * 0.2, rad * 0.25, fill="#d8e8c8", opacity=0.8)
        s.path(blob(36, 9.5, 11, 3.4, 0.3, seed=4), fill="#5dc28c", stroke="#1a5046", width=0.6)
        s.path("M30 11 q0.4 3.2 -0.4 5.6 M37 12 q0.3 2.4 -0.2 4.2", stroke="#2f8266", width=1.0)
        s.path("M14 24 Q27 9 43 8 Q59 9 72 24", stroke=RIM, width=2.0, opacity=0.6)
        s.line(43, 9, 43, 58, "#1c120e", 1.4, 0.8)
        if kind == "cracked":
            s.path("M50 12 L46 24 L53 30 L47 42 L52 55", stroke=INK, width=1.8)
            s.path("M58 28 L66 26 L70 34 L62 38 Z", fill="#e8d2a8", stroke=INK, width=1.1)
            s.path("M60 31 L67 31", stroke="#b49470", width=0.8)
    return s


@register("bark_beetle")
class BarkBeetle(CreatureRig):
    """Heavy beetle whose shell is tree bark; two hits: the first one cracks it."""

    du = 0.5

    def parts(self):
        def head(hurt: bool):
            s = Svg(36, 30)
            for sgn in (-1, 1):
                s.path(f"M24 {15 + sgn * 3} Q33 {15 + sgn * 4} 34 {15 + sgn * 9} Q30 {15 + sgn * 6} 25 {15 + sgn * 6.5} Z", fill="#e2cba4",
                       stroke=INK, width=1.0)
            s.path("M12 6 Q15 0 21 1 M14 6 Q19 2 24 4", stroke=INK, width=1.0)
            s.path(blob(16, 16, 11, 10, 0.04, seed=3), fill=s.radial(13, 11, 14, [(0, "#5a4a42"), (1, "#1c1414")]), stroke=INK, width=1.5)
            s.path("M8 10 Q14 5.5 21 8", stroke=RIM, width=1.0, opacity=0.5)
            if hurt:
                s.path("M17 11 L21 14 L17 17 M23 11 L20 14", stroke="#ffe27a", width=1.3)
            else:
                for ex, ey in ((20, 12.5), (24.5, 14.5)):
                    _glow(s, ex, ey, 4.2, GLOW_GOLD, 0.6)
                    s.circle(ex, ey, 1.8, fill="#ffe27a", stroke=INK, width=0.5)
            return s

        def leg():
            s = Svg(16, 26)
            s.path("M7 1.5 L4 12 L11 23.5", stroke=INK, width=3.8)
            s.path("M7 1.5 L4 12 L11 23.5", stroke="#5a463a", width=2.0)
            s.path("M11 23.5 L14 23.5", stroke=INK, width=2.2)
            s.circle(4, 12, 1.4, fill="#a08a74")
            return s

        return {"shell": (lambda: _bark_shell("normal"), (45, 72)), "shell_cracked": (lambda: _bark_shell("cracked"), (45, 72)),
                "shell_guard": (lambda: _bark_shell("guard"), (45, 72)), "head": (lambda: head(False), (6, 18)),
                "head_hurt": (lambda: head(True), (6, 18)), "leg": (leg, (7, 1.5))}

    def commands(self, e, t):
        root = Xf()
        if not e.alive:
            root = self.defeat_xf(e, root)
        guard = e.anim == "guard" and e.alive
        hurt = e.alive and (e.hit_timer > 0 or e.anim == "hurt")
        walking = e.anim == "walk" and e.alive and not hurt
        ph = t * 7.0
        bob = -abs(math.sin(ph)) * 1.4 if walking else 0.0
        sx = sy = 1.0
        if hurt:
            k = max(0.0, min(1.0, e.hit_timer / 0.65))
            sx, sy = 1 + 0.12 * k, 1 - 0.14 * k
        if guard:
            sy *= 0.92
        out = []
        for i, lx in enumerate((-22, -4, 14)):
            swing = math.sin(ph + i * 2.1 + 1.0) * (26 if walking else 0) + (-34 if guard else 0)
            out.append(self.cmd("leg", root.child(lx + 5, -22 + (4 if guard else 0), swing), tint=FAR_TINT))
        shell_xf = _scaled(root.child(0, -8 + bob + (3 if guard else 0)), sx, sy)
        cracked = e.health < e.hp or not e.alive
        name = "shell_guard" if guard else ("shell_cracked" if cracked else "shell")
        head_xf = shell_xf.child(31 if guard else 37, -13 if guard else -16, math.sin(t * 5) * 3 if walking else (-8 if hurt else 0))
        out.append(self.cmd("head_hurt" if hurt or not e.alive else "head", head_xf, scale=1.15))
        out.append(self.cmd(name, shell_xf))
        for i, lx in enumerate((-20, -2, 16)):
            swing = math.sin(ph + i * 2.1) * (26 if walking else 0) + (-34 if guard else 0)
            out.append(self.cmd("leg", root.child(lx, -21 + (4 if guard else 0), swing)))
        return _flash(out, e, t)


# ============================================================================ Arbusto-Espreita
@register("lurk_bush")
class LurkBush(CreatureRig):
    """An ordinary-looking bush (same leaves as the scenery bushes) until it
    spots Lume: yellow eyes snap open, leaves shake loose, it charges."""

    du = 0.5

    def parts(self):
        def bush():
            s = Svg(88, 70)
            for cx, cy, rad in ((24, 46, 21), (64, 46, 20), (44, 34, 26), (44, 52, 24)):
                s.path(blob(cx, cy, rad, rad * 0.84, 0.1, seed=cx + cy), fill=s.radial(cx + rad * 0.3, cy - rad * 0.6, rad * 1.6,
                       [(0, "#56b884"), (0.55, "#2a7458"), (1, "#16443a")]), stroke=INK, width=1.6)
            leaf_spots = ((20, 36, -140), (30, 28, -110), (40, 20, -95), (52, 21, -75), (62, 30, -55), (70, 40, -35), (16, 48, -160),
                          (36, 42, -120), (56, 44, -60), (46, 30, -90), (26, 54, -150), (64, 54, -30), (44, 58, -100))
            for x, y, a in leaf_spots:
                s.path(_leaf(x, y, 9, 2.6, a), fill="#5dc28c" if (x + y) % 3 else "#3f9a72", stroke="#164a3a", width=0.45)
            s.path("M26 22 Q44 10 62 22", stroke="#a9f2b4", width=1.4, opacity=0.5)
            for x, y in ((30, 40), (58, 36)):
                _glow(s, x, y, 4, GLOW_GOLD, 0.45)
                s.circle(x, y, 1.1, fill="#fff2b0")
            return s

        def eyes(kind: str):
            s = Svg(38, 20)
            for ex in (10, 27):
                if kind == "open":
                    _glow(s, ex, 11, 8, "#ffe27a", 0.6)
                    s.path(f"M{ex - 6} 11 Q{ex} 4.5 {ex + 6} 11 Q{ex} 16.5 {ex - 6} 11 Z",
                           fill=s.radial(ex, 10, 7, [(0, "#fffbe0"), (0.55, "#ffd84a"), (1, "#e0961e")]), stroke=INK, width=1.1)
                    s.path(f"M{ex} 7.6 Q{ex + 1.4} 11 {ex} 14.4 Q{ex - 1.4} 11 {ex} 7.6 Z", fill="#2a1a10")
                elif kind == "daze":
                    s.circle(ex, 11, 5.4, fill="#fff2b8", stroke=INK, width=1.0)
                    s.path(f"M{ex} 11 m-3 0 a3 3 0 1 0 6 0 a2.2 2.2 0 1 0 -4.4 0 a1.2 1.2 0 1 0 2.4 0", stroke=INK, width=1.0)
                else:  # closed: two dark creases in the foliage, barely visible
                    s.path(f"M{ex - 5} 10 Q{ex} 13 {ex + 5} 10", stroke="#123a30", width=1.4, opacity=0.8)
            if kind == "open":
                s.path("M3 4 L15 7 M35 4 L22 7", stroke=INK, width=2.2)
            return s

        def foot():
            s = Svg(18, 12)
            for dx, ln in ((-4, 9), (0, 10), (4, 8.5)):
                s.path(_taper([(9, 1.5, 3.4), (9 + dx * 0.6, 5.5, 2.4), (9 + dx, 1.5 + ln, 0.6)]), fill="#6a4c3c", stroke=INK, width=0.6)
            return s

        def leaf():
            s = Svg(14, 8)
            s.path(_leaf(7, 4, 11, 2.8, 0), fill="#5dc28c", stroke="#164a3a", width=0.6)
            return s

        return {"bush": (bush, (44, 67)), "eyes_open": (lambda: eyes("open"), (19, 11)), "eyes_closed": (lambda: eyes("closed"), (19, 11)),
                "eyes_daze": (lambda: eyes("daze"), (19, 11)), "foot": (foot, (9, 2)), "leaf": (leaf, (7, 4)), "star": (_star_part, (8, 8))}

    def commands(self, e, t):
        root = Xf()
        if not e.alive:
            root = self.defeat_xf(e, root)
        state = e.anim if e.alive else "defeat"
        st = e.state_time
        angle = sx_k = sy_k = 0.0
        lift, feet_speed, feet_amp = -3.0, 6.0, 2.0
        eyes = "eyes_closed"
        out: list[DrawCommand] = []
        if state == "alert":  # eyes snap open, leaves shake loose, paws the ground
            eyes = "eyes_open"
            angle = math.sin(t * 45) * 6 * min(1.0, st / 0.1)
            sx_k = sy_k = 0.06 * abs(math.sin(t * 30))
            lift, feet_speed, feet_amp = -6.0, 18.0, 3.0
            for i in range(3):
                lt = (st + i * 0.13) % 0.55
                lx = -14 + i * 14 + lt * (30 if i == 2 else -24 if i == 0 else 6)
                ly = -54 - lt * 50 + lt * lt * 160
                out.append(self.cmd("leaf", root.child(lx, ly, lt * 600 + i * 90), alpha=max(0.0, 1 - lt / 0.55)))
        elif state == "charge":
            eyes = "eyes_open"
            angle, sx_k, sy_k = 12.0, 0.08, -0.06
            lift, feet_speed, feet_amp = -7.0, 24.0, 7.0
            for i in range(3):
                lt = (t * 1.8 + i * 0.33) % 1.0
                out.append(self.cmd("leaf", root.child(-34 - lt * 40, -50 + i * 12 + math.sin(t * 9 + i) * 4, t * 400 + i * 120),
                                    alpha=max(0.0, 0.9 - lt)))
        elif state == "stunned":
            eyes = "eyes_daze"
            angle, sx_k, sy_k = -6.0 + math.sin(t * 4) * 2, 0.04, -0.08
            feet_amp = 0.0
        elif state == "recover":
            eyes = "eyes_open" if int(st * 10) % 3 else "eyes_closed"
            angle = math.sin(t * 30) * 3
            feet_amp = 1.0
        elif state == "defeat":
            eyes = "eyes_daze"
            feet_amp = 0.0
        else:  # walk: camouflaged shuffle, eyes shut
            angle = math.sin(t * 2.2 + e.origin_x) * 2
            feet_amp = 1.6
        swing = math.sin(t * feet_speed) * feet_amp
        out.insert(0, self.cmd("foot", root.child(-12 + swing, 0), tint=FAR_TINT))
        out.insert(1, self.cmd("foot", root.child(12 - swing, 0)))
        body = _scaled(root.child(0, lift, angle), 1 + sx_k, 1 + sy_k)
        out.insert(2, self.cmd("bush", body))
        out.append(self.cmd(eyes, body.child(18, -40)))
        if state == "stunned":
            for k in range(3):
                a = t * 5 + k * 2.1
                out.append(self.cmd("star", body.child(math.cos(a) * 24, -70 + math.sin(a) * 7)))
        return _flash(out, e, t)


# ============================================================================ Aranha-do-Cipó
@register("vine_spider")
class VineSpider(CreatureRig):
    """Leaf-patterned spider hanging from a silk thread that runs up out of view;
    the thread trails behind its dive and is gone once it is defeated."""

    du = 0.5

    def parts(self):
        def thread():
            s = Svg(4, 1200)
            s.line(2, 0, 2, 1200, "#e6fff8", 0.9, 0.7)
            s.line(2, 1110, 2, 1196, "#ffffff", 1.4, 0.8)
            return s

        def body():
            s = Svg(54, 52)
            s.path(blob(24, 20, 17, 16, 0.04, seed=2), fill=s.radial(18, 13, 24, [(0, "#9ad890"), (0.5, "#3f8a5a"), (1, "#1c4434")]), stroke=INK,
                   width=1.8)
            s.line(24, 6, 24, 34, "#1c4434", 1.3)
            for k in range(3):
                y = 12 + k * 7
                s.path(f"M24 {y} Q{18 - k} {y + 2} {13 + k} {y + 6}", stroke="#c8f4b8", width=0.9, opacity=0.7)
                s.path(f"M24 {y} Q{30 + k} {y + 2} {35 - k} {y + 6}", stroke="#c8f4b8", width=0.9, opacity=0.7)
            s.path("M12 13 Q18 5 26 4.5", stroke=RIM, width=1.4, opacity=0.6)
            s.path(_leaf(24, 3.5, 9, 2.4, -30), fill="#7ad89a", stroke="#1a5046", width=0.5)
            s.path(blob(37, 36, 11, 10, 0.04, seed=5), fill=s.radial(34, 32, 13, [(0, "#4a5a4a"), (1, "#141c18")]), stroke=INK, width=1.5)
            for sgn in (-1, 1):
                s.path(f"M{44} {40 + sgn * 1.5} q4 {sgn * 1.5 + 2} 2 {6 + sgn}", stroke="#e8e0c8", width=1.6)
            return s

        def eyes():
            s = Svg(22, 16)
            for x, y, rad in ((7, 8, 3.6), (14.5, 8.5, 3.0), (4, 3.5, 1.7), (18, 4, 1.5)):
                _glow(s, x, y, rad * 2.2, "#ff9a5a", 0.5)
                s.circle(x, y, rad, fill=s.radial(x - rad * 0.3, y - rad * 0.3, rad * 1.2, [(0, "#fff0b0"), (0.6, "#ffb43c"), (1, "#c8501e")]),
                         stroke=INK, width=0.7)
                s.circle(x + rad * 0.25, y - rad * 0.3, rad * 0.3, fill="#ffffff")
            return s

        def leg():
            s = Svg(32, 14)
            s.path("M2 7 L15 2.5 L29 10", stroke=INK, width=3.2)
            s.path("M2 7 L15 2.5 L29 10", stroke="#2c4a3a", width=1.6)
            s.circle(15, 2.8, 1.3, fill="#7ab88a")
            return s

        return {"thread": (thread, (2, 1200)), "body": (body, (24, 22)), "eyes": (eyes, (11, 8)), "leg": (leg, (2, 7)),
                "eye_x": (lambda: _cross_part(12), (6, 7)), "glow": (lambda: _halo_part(70, 70, "#ffb070", 0.5), (35, 35))}

    def commands(self, e, t):
        root = Xf()
        if not e.alive:
            root = self.defeat_xf(e, root)
        state = e.anim if e.alive else "defeat"
        st = e.state_time
        tilt = math.sin(t * 1.6 + e.origin_x) * 3
        bounce = 0.0
        thread_angle = -tilt * 0.6
        if state == "perch":
            legs = (55, 75, 105, 125)
        elif state == "alert":
            legs = (-30 + math.sin(t * 30) * 8, 10, 170, 210 - math.sin(t * 30) * 8)
            bounce = math.sin(st * 26) * 2.5
        elif state == "dive":
            forward = e.vx * e.facing
            tilt = 18.0
            thread_angle = -max(-24.0, min(24.0, forward / 190.0 * 22.0))
            legs = (-38, -8, 168, 200)
        elif state == "climb":
            tilt = -24.0
            thread_angle = -10.0
            c = math.sin(t * 16)
            legs = (-70 + c * 12, -40 - c * 12, -120 + c * 12, -150 - c * 12)
        else:  # defeat
            legs = (40, 80, 100, 140)
        body = root.child(0, -24 + bounce, tilt)
        out: list[DrawCommand] = []
        if e.alive:
            attach = body.child(0, -18)
            out.append(self.cmd("thread", Xf(attach.x, attach.y, thread_angle, root.sx, root.sy)))
            out.append(self.cmd("glow", body.child(12, 10), alpha=1.0 if state in ("alert", "dive") else 0.55))
        hip = body.child(12, 13)
        for a in legs:
            out.append(self.cmd("leg", hip.child(-2, -1, a + 8), tint=FAR_TINT))
        out.append(self.cmd("body", body))
        for a in legs:
            out.append(self.cmd("leg", hip.child(0, 1, a)))
        if e.alive:
            out.append(self.cmd("eyes", body.child(15, 10), scale=1.15 if state in ("alert", "dive") else 1.0))
        else:
            out.append(self.cmd("eye_x", body.child(15, 10)))
        return _flash(out, e, t)
