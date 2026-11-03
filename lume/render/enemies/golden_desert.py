"""Deserto Dourado creatures: Escaravelho-de-Areia, Tatu-Bola, Abutrinho,
Cacto Sentinela, Escorpião-Couraça, Serpente-de-Duna and Escaravelho Lançador.

Each rig poses itself from what the behaviour publishes (``e.anim``,
``e.state``, ``e.state_time``, ``e.timer``, ``e.memory``), flashes while
``e.hit_timer`` runs and uses :meth:`CreatureRig.defeat_xf` for the defeat
look (squashed by a stomp, tumbling upside down when knocked out). Palette
rule for the biome: every creature carries a hue the golden sand does not
have (indigo, slate blue, crimson, teal, emerald, green) so it reads against
both the dunes and the red rock.
"""

from __future__ import annotations

import math
from typing import Sequence

from ..rig import DrawCommand, Xf, smoothstep
from ..svg import Rand, Svg, blob, rounded_rect_path, smooth_closed, smooth_open, star_points
from .base import INK, CreatureRig, eye_svg, pupil_svg, register

# sand tones shared with the Deserto Dourado terrain (mounds, puffs)
SAND_HI, SAND_TOP, SAND, SAND_MID, SAND_DEEP, SAND_EDGE = "#fff5d6", "#fbe3a6", "#f2c776", "#e2a95c", "#c88644", "#6b3820"
HIT_TINT = (255, 150, 150)
FAR = (150, 138, 165)  # limbs on the far side of the body


def _pl(pts: Sequence[tuple[float, float]]) -> str:
    return "M" + "L".join(f"{x:.2f} {y:.2f}" for x, y in pts)


def _ellipse_d(cx: float, cy: float, rx: float, ry: float) -> str:
    return f"M{cx - rx:.2f} {cy:.2f}a{rx:.2f} {ry:.2f} 0 1 0 {2 * rx:.2f} 0a{rx:.2f} {ry:.2f} 0 1 0 {-2 * rx:.2f} 0"


def _flash(e, t: float, out: list[DrawCommand]) -> list[DrawCommand]:
    """Hit flash while ``hit_timer`` runs (also on the first defeat frames)."""
    if e.hit_timer > 0 and (e.alive or e.defeated > 0.42) and int(t * 20) % 2 == 0:
        for c in out:
            c.tint = HIT_TINT
    return out


def _limb(s: Svg, d: str, width: float, fill: str, light: str | None = None) -> None:
    """Outlined tubular limb: ink stroke, colour stroke, optional rim light."""
    s.path(d, stroke=INK, width=width + 2.4)
    s.path(d, stroke=fill, width=width)
    if light:
        with s.group("translate(0.7 -0.7)"):
            s.path(d, stroke=light, width=width * 0.3, opacity=0.8)


def sand_mound(w: float = 80.0, h: float = 26.0, seed: int = 1) -> Svg:
    """Hump of loose sand (burrows, trails). Same tones as the terrain cap."""
    r = Rand(seed)
    s = Svg(w, h)
    top = 3.0
    d = (f"M1 {h - 1:.1f} C{w * 0.2:.1f} {h - 2:.1f} {w * 0.3:.1f} {top:.1f} {w * 0.5:.1f} {top:.1f} "
         f"C{w * 0.7:.1f} {top:.1f} {w * 0.8:.1f} {h - 2:.1f} {w - 1:.1f} {h - 1:.1f} Z")
    s.path(d, fill=s.linear(0, top, 0, h, [(0, SAND_HI), (0.22, SAND_TOP), (0.7, SAND), (1, SAND_MID)]), stroke=SAND_EDGE, width=1.3)
    for k in range(3):
        y = top + 6 + k * 5
        x1, x2 = w * (0.3 - k * 0.07), w * (0.6 + k * 0.07)
        s.path(f"M{x1:.1f} {y:.1f} Q{(x1 + x2) / 2:.1f} {y - 2.2:.1f} {x2:.1f} {y + 0.6:.1f}", stroke=SAND_DEEP, width=1.0, opacity=0.5)
    s.path(f"M{w * 0.4:.1f} {top + 1.4:.1f} Q{w * 0.55:.1f} {top - 0.4:.1f} {w * 0.68:.1f} {top + 2.2:.1f}", stroke="#ffffff", width=1.4, opacity=0.75)
    for _ in range(3):
        px, py = r.uniform(w * 0.22, w * 0.78), r.uniform(h * 0.6, h * 0.85)
        s.circle(px, py, r.uniform(1.0, 1.7), fill="#c08050", stroke=SAND_EDGE, width=0.5)
    return s


def sand_puff(seed: int = 1) -> Svg:
    """Burst of sand: soft cloud plus a few grains."""
    r = Rand(seed)
    s = Svg(24, 24)
    s.circle(12, 12, 11.5, fill=s.radial(13, 11, 11.5, [(0, "#fff8e6", 0.95), (0.45, SAND_TOP, 0.85), (1, SAND, 0)]))
    for _ in range(7):
        a, rr = r.uniform(0, 2 * math.pi), r.uniform(3, 9.5)
        s.circle(12 + math.cos(a) * rr, 12 + math.sin(a) * rr, r.uniform(0.7, 1.5), fill=SAND_DEEP)
    return s


def _lid(width: float = 11.0) -> Svg:
    """Closed eye (blink): a soft ink arc."""
    s = Svg(width, 6)
    s.path(f"M1.2 2 Q{width / 2:.1f} 5.6 {width - 1.2:.1f} 2", stroke=INK, width=1.6)
    return s


def _brow(width: float = 12.0, thick: float = 2.6) -> Svg:
    s = Svg(width, 6)
    s.path(f"M1 1.6 Q{width * 0.5:.1f} 1.8 {width - 1:.1f} 4.4", stroke=INK, width=thick)
    return s


def _eye(rig: CreatureRig, out: list[DrawCommand], xf: Xf, closed: bool, look: tuple[float, float] = (1.3, 0.5),
         eye: str = "eye") -> None:
    """Eye white + pupil, or the lid while blinking."""
    if closed:
        out.append(rig.cmd("lid", xf.child(0, 0.5)))
        return
    out.append(rig.cmd(eye, xf))
    out.append(rig.cmd("pupil", xf.child(*look)))


def _puffs(rig: CreatureRig, origin: Xf, t: float, speed: float, n: int, spread: float, rise: float, back: float,
           alpha: float = 0.85) -> list[DrawCommand]:
    """Cycling sand puffs drifting away from ``origin`` (dust trails, sprays)."""
    out = []
    for i in range(n):
        p = (t * speed + i / n) % 1.0
        x = back * (4 + p * spread) + math.sin(i * 2.3) * 3
        y = -p * rise
        out.append(rig.cmd("puff", origin.child(x, y), alpha=alpha * (1 - p) ** 1.3, scale=0.45 + 0.7 * p))
    return out


# --------------------------------------------------------------------------- Escaravelho-de-Areia
@register("scarab")
class SandScarab(CreatureRig):
    """Indigo scarab with a copper rim and a toothed digging shovel. Burrows:
    noses into the sand under a growing mound, leaves only its antenna fans
    showing, then bursts back out."""

    du = 0.5
    burrow_time = 1.1  # species default (enemies.json params)

    def parts(self):
        def shell():
            s = Svg(60, 48)
            pts = [(3, 39), (4, 24), (12, 10), (27, 3), (42, 4), (52, 13), (57, 28), (54, 41), (30, 45), (8, 43)]
            s.path(smooth_closed(pts, 0.85), fill=s.radial(40, 11, 52, [(0, "#e2d8ff"), (0.16, "#a08af2"), (0.48, "#5038b4"),
                                                                       (0.82, "#261a60"), (1, "#160e38")]), stroke=INK, width=1.8)
            s.path("M39 5 Q46 23 41 42", stroke="#120a2e", width=1.6, opacity=0.85)
            s.path("M40.6 6 Q47.6 23 42.6 41", stroke="#c2b4ff", width=0.8, opacity=0.5)
            for off in (6.0, 12.0):
                s.path(smooth_open([(7 + off * 0.5, 40 - off * 0.2), (11 + off * 0.3, 20 + off * 0.5), (26, 6 + off), (36, 7 + off * 0.8)]),
                       stroke="#130b38", width=1.0, opacity=0.5)
            s.path(smooth_open([(12, 33), (14, 21), (22, 11)]), stroke="#5fe6d2", width=1.8, opacity=0.35)
            s.path(smooth_open([(5, 40), (18, 44), (36, 44.5), (54, 40)]), stroke="#e8a04a", width=2.6)
            s.path(smooth_open([(7, 38.6), (18, 42.4), (36, 43), (52, 38.8)]), stroke="#ffe0a0", width=0.8, opacity=0.85)
            s.path(smooth_open([(22, 6.5), (36, 4), (48, 9.5), (54, 21)]), stroke="#ffffff", width=2.4, opacity=0.45)
            s.ellipse(45, 12, 3.6, 2.2, fill="#ffffff", opacity=0.8)
            return s

        def head():
            s = Svg(32, 28)
            s.path(_pl([(13, 21), (21, 15), (26, 15.2), (28.5, 17), (26.8, 18.8), (29, 20.6), (26.8, 22.4), (28.6, 24.6), (17, 25.6)]) + "Z",
                   fill=s.linear(14, 15, 29, 26, [(0, "#ffd884"), (0.5, "#e09838"), (1, "#8a4c14")]), stroke=INK, width=1.2)
            s.path(blob(13, 14, 10.5, 10, 0.03, seed=2), fill=s.radial(18, 8, 14, [(0, "#a898f0"), (0.5, "#4a3a96"), (1, "#1c1442")]),
                   stroke=INK, width=1.5)
            s.ellipse(18, 7.5, 3.2, 1.6, fill="#ffffff", opacity=0.5)
            s.path("M20 20.6 Q23 22 25 21", stroke=INK, width=1.0)
            return s

        def antenna():
            s = Svg(16, 18)
            s.path("M2 16 Q2.5 9 8 6", stroke=INK, width=1.7)
            for k in range(3):
                a = math.radians(-70 + k * 32)
                cx, cy = 8 + math.cos(a) * 3.4, 6 + math.sin(a) * 3.4
                with s.group(f"translate({cx:.2f} {cy:.2f}) rotate({math.degrees(a):.1f})"):
                    s.ellipse(0, 0, 3.6, 1.6, fill="#f2b04a", stroke=INK, width=0.8)
            return s

        def leg():
            s = Svg(14, 16)
            _limb(s, "M4 2 L9 7.5 L6.6 13.2 L9.6 14", 2.0, "#3a2a6a", "#9a88e8")
            s.path("M7.8 9.6 L10.2 9.2", stroke=INK, width=0.9)
            return s

        return {
            "shell": (shell, (30, 44)), "head": (head, (6, 15)), "antenna": (antenna, (2, 16)), "leg": (leg, (4, 2)),
            "eye": (lambda: eye_svg(12), (6, 6)), "pupil": (lambda: pupil_svg(6), (3, 3)), "lid": (lambda: _lid(12), (6, 2)),
            "brow": (lambda: _brow(11, 2.4), (5.5, 3)),
            "mound": (lambda: sand_mound(78, 26, 3), (39, 24)), "puff": (lambda: sand_puff(4), (12, 12)),
        }

    def _body(self, e, t: float, root: Xf, walking: bool, dig: float = 0.0, squash: float = 1.0) -> list[DrawCommand]:
        ph = t * 12.0
        bob = -abs(math.sin(ph)) * 1.4 if walking else 0.0
        body = root.child(-4 * (1 - dig), -12 + bob + 9 * max(0.0, 1 - squash) + 4 * dig, dig * 10)
        shrink = 1 - 0.45 * dig
        body = Xf(body.x, body.y, body.angle, body.sx * shrink * (1 + 0.12 * max(0.0, 1 - squash)), body.sy * shrink * squash)
        legs = squash > 0.55
        out = []
        if legs:
            for i, lx in enumerate((-12.0, 0.0, 12.0)):
                swing = math.sin(ph + i * math.pi + 0.7) * 24 if walking else 8
                if dig > 0:
                    swing = math.sin(t * 40 + i) * 35
                out.append(self.cmd("leg", body.child(lx + 3, -4, swing - 8), tint=FAR))
        head = body.child(24, -16, (math.sin(ph * 0.5) * 3 if walking else 0) + dig * 14)
        out.append(self.cmd("antenna", head.child(9, -7, -18 + math.sin(t * 5) * 8), tint=FAR))
        out.append(self.cmd("shell", body))
        out.append(self.cmd("head", head))
        out.append(self.cmd("antenna", head.child(12, -6, 8 + math.sin(t * 5 + 1) * 10)))
        if e.alive:
            _eye(self, out, head.child(12, -3.5), self.blink(t, e.origin_x), (1.6, 0.4))
            out.append(self.cmd("brow", head.child(11.5, -10, 14)))
        if legs:
            for i, lx in enumerate((-14.0, -2.0, 10.0)):
                swing = math.sin(ph + i * math.pi) * 26 if walking else 0.0
                if dig > 0:
                    swing = math.sin(t * 40 + i * 2) * 40
                out.append(self.cmd("leg", body.child(lx, -3, swing)))
        return out

    def commands(self, e, t):
        root = Xf()
        if not e.alive:
            root = self.defeat_xf(e, root)
            return _flash(e, t, self._body(e, t, root, False))
        if e.anim not in ("burrow", "emerge"):
            return _flash(e, t, self._body(e, t, root, e.anim == "walk"))
        hide = float(e.params.get("burrow_time", self.burrow_time))
        st = e.state_time
        sink = smoothstep(st / 0.3)
        q = max(0.0, min(1.0, (st - (hide - 0.35)) / 0.35))
        out: list[DrawCommand] = []
        if q <= 0.0:
            if sink < 1.0:  # nosing into the sand, legs digging, sand thrown back
                out += self._body(e, t, root, False, dig=sink, squash=1.0 - 0.6 * sink)
                out += _puffs(self, root.child(-8, -8), t, 3.0, 3, 26, 24, -1, 0.95 * min(1.0, sink * 2))
            else:  # only the antenna fans give it away
                for k, ox in enumerate((-5.0, 5.0)):
                    out.append(self.cmd("antenna", root.child(ox, -18, -14 + k * 24 + math.sin(t * 6 + k) * 10), scale=0.8))
            mound = 0.45 + 0.55 * sink
            out.append(self.cmd("mound", Xf(root.x, root.y, 0, mound * (1 + 0.04 * math.sin(t * 9)), mound)))
            return _flash(e, t, out)
        if q < 0.3:  # tremble before bursting out
            jitter = math.sin(t * 70) * 1.6
            for k, ox in enumerate((-5.0, 5.0)):
                out.append(self.cmd("antenna", root.child(ox + jitter, -19, -14 + k * 24), scale=0.8))
            out.append(self.cmd("mound", Xf(root.x + jitter, root.y, 0, 1.05, 1.1)))
            out += _puffs(self, root.child(0, -14), t, 4.0, 2, 8, 10, 1, 0.5)
            return _flash(e, t, out)
        p = (q - 0.3) / 0.7
        pop = 0.25 + 0.95 * smoothstep(p / 0.6) - 0.2 * smoothstep((p - 0.6) / 0.4)
        out += self._body(e, t, root, False, squash=max(0.15, min(1.15, pop)))
        out += _puffs(self, root.child(0, -12), t, 2.6, 4, 18, 30, 1, 0.95 * (1 - p))
        out += _puffs(self, root.child(0, -12), t + 0.2, 2.6, 3, 18, 30, -1, 0.95 * (1 - p))
        k = max(0.0, 1.0 - p * 1.3)
        if k > 0:
            out.append(self.cmd("mound", Xf(root.x, root.y, 0, k, k)))
        return _flash(e, t, out)


# --------------------------------------------------------------------------- Tatu-Bola
SLATE = [(0, "#e6eef4"), (0.22, "#a8bccc"), (0.6, "#62788e"), (1, "#2e3c50")]
SKIN = "#e7aa92"


@register("armadillo")
class Armadillo(CreatureRig):
    """Slate-blue banded armadillo with pink ears and snout. Curls into a
    ball when stomped, rolls fast when kicked, peeks out before waking."""

    du = 0.5

    def parts(self):
        def shell():
            s = Svg(58, 38)
            outline = smooth_closed([(2, 34), (4, 20), (14, 7), (30, 2), (45, 5), (54, 15), (57, 30), (50, 36), (29, 37.5), (8, 36.5)], 0.85)
            s.path(outline, fill=s.radial(40, 8, 52, SLATE), stroke=INK, width=1.8)
            for bx in (21.0, 27.5, 34.0):  # the movable bands
                s.path(f"M{bx:.1f} 3.5 Q{bx + 3.5:.1f} 20 {bx + 1.5:.1f} 36.6", stroke="#25303f", width=1.5, opacity=0.85)
                s.path(f"M{bx + 1.4:.1f} 4 Q{bx + 4.9:.1f} 20 {bx + 2.9:.1f} 36.4", stroke="#e2ecf2", width=0.8, opacity=0.6)
            for row, y in enumerate((11.0, 19.0, 27.0)):  # scute texture
                for k in range(9):
                    x = 6 + k * 5.6 + (2.8 if row % 2 else 0)
                    if 4 < x < 54 and not (y < 9 and (x < 14 or x > 46)):
                        s.path(f"M{x - 1.6:.1f} {y:.1f} Q{x:.1f} {y - 1.6:.1f} {x + 1.6:.1f} {y:.1f}", stroke="#2c3a4c", width=0.7, opacity=0.5)
            s.path(smooth_open([(4, 33.5), (20, 36.5), (40, 36.5), (55, 32)]), stroke="#1e2836", width=1.6, opacity=0.6)
            s.path(smooth_open([(20, 5), (34, 2.6), (46, 6), (53, 14)]), stroke="#ffffff", width=2.2, opacity=0.55)
            return s

        def head():
            s = Svg(30, 22)
            s.path("M2 7 Q10 2 18 7 L27 12.5 Q29.4 14 27 15.6 L18 17.5 Q8 20 3 16 Z",
                   fill=s.linear(0, 4, 0, 19, [(0, "#f6c4ae"), (1, "#c07a64")]), stroke=INK, width=1.4)
            s.path("M3 7.5 Q10 1.6 17 6.6 L13 9.5 Q8 6.6 4 10 Z", fill=s.linear(0, 2, 0, 10, [(0, "#c8d6e2"), (1, "#5a6e84")]), stroke=INK, width=1.0)
            s.circle(27.2, 14, 1.9, fill="#8a3a3a", stroke=INK, width=0.6)
            s.circle(14, 11.4, 2.2, fill="#1e1626")
            s.circle(14.7, 10.7, 0.75, fill="#ffffff")
            s.path("M19 16.2 Q22 17.2 24.6 16", stroke="#7a3a30", width=0.8)
            return s

        def ear():
            s = Svg(10, 16)
            s.path("M5 15 Q0.5 8 3 2 Q5 0.5 7 2 Q9.5 8 5 15 Z", fill=SKIN, stroke=INK, width=1.1)
            s.path("M5 12 Q3.2 7 4.4 3.6", stroke="#c86a6a", width=1.4, opacity=0.8)
            return s

        def leg():
            s = Svg(10, 12)
            s.path(rounded_rect_path(2, 0, 6, 9, 2.5), fill="#c88a74", stroke=INK, width=1.1)
            s.path("M2.5 9.5 L1.5 11.5 M5 10 L5 11.8 M7.5 9.5 L8.5 11.5", stroke=INK, width=1.0)
            return s

        def tail():
            s = Svg(20, 10)
            s.path("M19 3 Q10 2 1.5 7.5 Q11 7 19 8 Z", fill=s.linear(0, 2, 0, 8, [(0, "#a8bccc"), (1, "#4a5e74")]), stroke=INK, width=1.0)
            for x in (8.0, 12.0, 16.0):
                s.line(x, 3.4, x - 0.6, 7.6, "#25303f", 0.7, 0.7)
            return s

        def ball():
            s = Svg(58, 58)
            c = 29.0
            s.circle(c, c, 27, fill=s.radial(38, 18, 44, SLATE), stroke=INK, width=1.8)
            for k in range(-2, 3):  # bands seen wrapping around the ball
                x = c + k * 9.5
                bend = k * 4.5
                s.path(f"M{x:.1f} {c - 26 + abs(k) * 2.4:.1f} Q{x + bend:.1f} {c:.1f} {x:.1f} {c + 26 - abs(k) * 2.4:.1f}",
                       stroke="#25303f", width=1.4, opacity=0.8)
                s.path(f"M{x + 1.4:.1f} {c - 25 + abs(k) * 2.4:.1f} Q{x + bend + 1.4:.1f} {c:.1f} {x + 1.4:.1f} {c + 25 - abs(k) * 2.4:.1f}",
                       stroke="#e2ecf2", width=0.7, opacity=0.5)
            # head shield and tail tip interlock at the lower front, where it opens
            s.path(f"M{c + 10:.1f} {c + 23:.1f} Q{c + 13:.1f} {c + 13:.1f} {c + 23:.1f} {c + 11:.1f} "
                   f"Q{c + 24:.1f} {c + 18:.1f} {c + 17:.1f} {c + 23.5:.1f} Z", fill="#93a8bc", stroke=INK, width=1.1)
            s.path(f"M{c + 8:.1f} {c + 21:.1f} Q{c + 4:.1f} {c + 24.5:.1f} {c - 2:.1f} {c + 25:.1f}", stroke=INK, width=2.0)
            s.path(smooth_open([(c - 6, c - 22), (c + 8, c - 24), (c + 20, c - 14)]), stroke="#ffffff", width=2.6, opacity=0.6)
            s.ellipse(c + 11, c - 16, 3.4, 2, fill="#ffffff", opacity=0.75)
            return s

        def peek():
            s = Svg(26, 20)
            s.path("M6.5 9 Q4 1.6 7.6 0.8 Q10 3.6 9.6 9", fill=SKIN, stroke=INK, width=0.9)
            s.path("M2 15 Q8 7 15 9 L23 12 Q25.4 13.6 23 15 L13 17 Q6 18.6 2 15 Z",
                   fill=s.linear(0, 7, 0, 18, [(0, "#f6c4ae"), (1, "#c07a64")]), stroke=INK, width=1.2)
            s.circle(23.4, 13.4, 1.7, fill="#8a3a3a")
            s.circle(11.5, 12, 1.9, fill="#1e1626")
            s.circle(12.1, 11.4, 0.65, fill="#ffffff")
            return s

        def speed():
            s = Svg(44, 34)
            for k, y in enumerate((6.0, 16.0, 26.0)):
                ln = 40 - k * 9 if k != 1 else 44
                s.path(f"M{44 - ln:.1f} {y:.1f} Q{44 - ln * 0.5:.1f} {y - 1.2:.1f} 44 {y:.1f} L44 {y + 1.6:.1f} "
                       f"Q{44 - ln * 0.5:.1f} {y + 1:.1f} {44 - ln:.1f} {y:.1f} Z", fill="#ffffff", opacity=0.75)
            return s

        return {
            "shell": (shell, (29, 36)), "head": (head, (4, 11)), "ear": (ear, (5, 14)), "leg": (leg, (5, 1)), "tail": (tail, (19, 5)),
            "ball": (ball, (29, 29)), "peek": (peek, (3, 14)), "speed": (speed, (44, 17)), "puff": (lambda: sand_puff(7), (12, 12)),
        }

    def _walker(self, e, t: float, root: Xf, walking: bool) -> list[DrawCommand]:
        ph = t * 10.0
        bob = -abs(math.sin(ph)) * 1.6 if walking else 0.0
        body = root.child(-3, -7 + bob)
        out = []
        for i, lx in enumerate((-15.0, 13.0)):
            sw = math.sin(ph + i * math.pi + 1.2) * 26 if walking else 0.0
            out.append(self.cmd("leg", body.child(lx + 4, -4, sw), tint=FAR))
        out.append(self.cmd("tail", body.child(-26, -8, -10 + math.sin(ph) * 6)))
        head = body.child(24, -13, (math.sin(ph) * 4 if walking else 0) + 4)
        out.append(self.cmd("ear", head.child(6, -5, -28 + math.sin(ph + 1.5) * 9), tint=FAR))
        out.append(self.cmd("shell", body))
        out.append(self.cmd("head", head))
        out.append(self.cmd("ear", head.child(8, -5, -6 + math.sin(ph + 1.0) * 10)))
        for i, lx in enumerate((-16.0, 12.0)):
            sw = math.sin(ph + i * math.pi) * 26 if walking else 0.0
            out.append(self.cmd("leg", body.child(lx, -3, sw)))
        return out

    def commands(self, e, t):
        root = Xf()
        if not e.alive:
            root = self.defeat_xf(e, root)
        curled = e.state in ("shell", "slide") or e.anim in ("shell", "slide", "wake")
        if not curled:
            return _flash(e, t, self._walker(e, t, root, e.alive and e.anim == "walk"))
        out: list[DrawCommand] = []
        centre = root.child(0, -28.5)
        if e.alive and e.anim == "slide":
            spin = (t * 1500.0) % 360.0
            out.append(self.cmd("speed", centre.child(-18, 0), alpha=0.7))
            out += _puffs(self, root.child(-14, -3), t, 3.2, 3, 22, 10, -1, 0.75)
            out.append(self.cmd("ball", Xf(centre.x, centre.y, spin, centre.sx, centre.sy)))
        elif e.alive and e.anim == "wake":
            rock = math.sin(t * 16) * 8
            peek = 0.5 + 0.5 * math.sin(t * 5)
            ball = Xf(centre.x, centre.y, rock, centre.sx, centre.sy)
            out.append(self.cmd("ball", ball))
            out.append(self.cmd("peek", ball.child(14 + 4 * peek, 17 - 2 * peek, -22 + 12 * peek), scale=0.55 + 0.45 * peek))
        else:
            breathe = 1 + 0.015 * math.sin(t * 3) if e.alive else 1.0
            out.append(self.cmd("ball", Xf(centre.x, centre.y, centre.angle, centre.sx * breathe, centre.sy / breathe)))
        return _flash(e, t, out)


# --------------------------------------------------------------------------- Abutrinho
@register("vulture")
class VultureChick(CreatureRig):
    """Fluffy vulture chick on oversized dark wings: flaps hard while
    climbing, glides with the wings in a V while sinking."""

    du = 0.5

    def parts(self):
        def body():
            s = Svg(50, 46)
            pts = []
            for i in range(22):
                a = 2 * math.pi * i / 22
                k = 1.0 + (0.07 if i % 2 else -0.02)
                pts.append((25 + math.cos(a) * 21 * k, 24 + math.sin(a) * 19 * k))
            s.path(smooth_closed(pts, 0.9), fill=s.radial(31, 15, 30, [(0, "#ffffff"), (0.5, "#f4e8d2"), (1, "#c4a884")]), stroke=INK, width=1.6)
            s.path("M6 18 Q14 6 30 7 Q18 12 12 24 Z", fill="#6a4a38", opacity=0.85)
            for k in range(4):
                y = 28 + k * 3.5
                s.path(f"M{20 + k * 2:.1f} {y:.1f} q2 2 4 0 q2 2 4 0", stroke="#c4a884", width=0.9, opacity=0.8)
            s.ellipse(32, 14, 5, 3, fill="#ffffff", opacity=0.6)
            return s

        def head():
            s = Svg(34, 30)
            ruff = []
            for i in range(14):
                a = math.radians(90 + i * 180 / 13)
                k = 1.0 + (0.18 if i % 2 else 0.0)
                ruff.append((9 + math.cos(a) * 8 * k, 22 + math.sin(a) * 6 * k))
            s.path(smooth_closed(ruff + [(15, 26), (14, 18)], 0.8), fill="#fffaf0", stroke=INK, width=1.1)
            s.path(blob(16, 14, 9.5, 9, 0.04, seed=4), fill=s.radial(19, 10, 13, [(0, "#ffc8b8"), (0.6, "#ee8f84"), (1, "#b85a50")]),
                   stroke=INK, width=1.4)
            s.path("M23 11 Q31 10.5 33 15 Q33.6 19 30 21 Q31 17 27.5 16.5 L23 17 Z",
                   fill=s.linear(23, 10, 33, 21, [(0, "#fff2cc"), (0.6, "#e8c890"), (1, "#5a4a44")]), stroke=INK, width=1.1)
            s.path("M24 14.6 L28 14.4", stroke="#8a6a50", width=0.7)
            for k in range(3):
                s.path(f"M{13 + k * 3:.1f} 6 Q{11 + k * 3:.1f} 0.5 {15 + k * 3.4:.1f} 2", stroke="#fff8ea", width=2.0)
                s.path(f"M{13 + k * 3:.1f} 6 Q{11 + k * 3:.1f} 0.5 {15 + k * 3.4:.1f} 2", stroke=INK, width=0.5, opacity=0.6)
            s.path("M10 17 Q12 19 15 18.4", stroke="#b85a50", width=0.8, opacity=0.7)
            return s

        def wing():
            s = Svg(60, 30)
            d = ("M3 8 Q18 1 38 4 L47 3 Q50 4 47 7 L55 7 Q58 9 54 11 L57 13 Q59 15.5 54 16 L52 18.5 Q49 20 46 18 "
                 "Q30 22 14 18 Q5 16 3 8 Z")
            s.path(d, fill=s.linear(0, 2, 0, 20, [(0, "#7a5a46"), (0.45, "#3e2c26"), (1, "#22181a")]), stroke=INK, width=1.3)
            s.path("M5 8 Q20 3 38 5.5 Q30 10 16 11 Q8 11.5 5 8 Z", fill="#a8846a", opacity=0.9)
            for k, x in enumerate((24.0, 32.0, 40.0)):
                s.path(f"M{x:.1f} 9 Q{x + 6:.1f} 13 {x + 9:.1f} {15 + k * 0.6:.1f}", stroke="#1a1012", width=0.8, opacity=0.7)
            s.path("M6 7 Q20 2.4 36 4.6", stroke="#f0dcc0", width=1.0, opacity=0.8)
            return s

        def tail():
            s = Svg(22, 16)
            s.path("M21 4 L5 1.5 Q1 3 2.5 6 Q0.5 8.5 3 11 Q2 14 6 14.5 L21 11 Z", fill=s.linear(0, 1, 0, 15, [(0, "#5a4234"), (1, "#22181a")]),
                   stroke=INK, width=1.1)
            return s

        def foot():
            s = Svg(12, 12)
            s.path("M6 1 L6 7 M6 7 L2.5 10.5 M6 7 L6.2 11 M6 7 L9.5 10.4", stroke=INK, width=2.6)
            s.path("M6 1 L6 7 M6 7 L2.5 10.5 M6 7 L6.2 11 M6 7 L9.5 10.4", stroke="#f0a894", width=1.2)
            return s

        def eye():
            s = Svg(12, 12)
            s.ellipse(6, 6, 5.2, 5.6, fill="#ffffff", stroke=INK, width=1.0)
            return s

        return {
            "body": (body, (25, 24)), "head": (head, (8, 20)), "wing": (wing, (5, 9)), "tail": (tail, (20, 7)), "foot": (foot, (6, 1)),
            "eye": (eye, (6, 6)), "pupil": (lambda: pupil_svg(5.6), (2.8, 2.8)), "lid": (lambda: _lid(11), (5.5, 2)),
        }

    def commands(self, e, t):
        root = Xf()
        if not e.alive:
            root = self.defeat_xf(e, root)
        freq = float(e.params.get("frequency", 1.9))
        climb = -math.cos(e.timer * freq) if e.alive else -0.6  # >0 while rising
        effort = 0.25 + 0.75 * max(0.0, climb)
        beat = t * (12 + 7 * effort)
        flap = math.sin(beat)
        bob = flap * 2.2 * effort
        tilt = -9 * climb if e.alive else 0.0
        body = root.child(-2, -24 + bob, tilt)
        if e.alive:  # upstroke stops short of the head, downstroke sweeps below the body
            near = -147 + flap * 67 * effort + (1 - effort) * 14
            far = -158 + math.sin(beat - 0.6) * 60 * effort + (1 - effort) * 6
        else:  # wings spread back: flat when squashed, limp when knocked out
            near, far = -176.0, -186.0
        out = [self.cmd("wing", body.child(-4, -13, far), tint=FAR)]
        out.append(self.cmd("tail", body.child(-19, 3, -6 + math.sin(t * 3) * 6)))
        for k, fx in enumerate((-1.0, 6.0)):
            out.append(self.cmd("foot", body.child(fx, 17, 10 + math.sin(t * 4 + k) * 10), tint=FAR if k == 0 else None))
        out.append(self.cmd("body", body))
        head = body.child(13, -11, -tilt * 0.6 + math.sin(t * 2.2) * 5)
        out.append(self.cmd("head", head))
        if e.alive:
            _eye(self, out, head.child(11, -9), self.blink(t, e.origin_x), (1.2, 0.6))
        out.append(self.cmd("wing", body.child(-1, -12, near)))
        return _flash(e, t, out)


# --------------------------------------------------------------------------- Cacto Sentinela
@register("cactus")
class CactusSentinel(CreatureRig):
    """Ribbed green sentinel with a magenta flower crown. Turns to Lume,
    swells and bristles its spines (charge), then recoils as it spits a
    spine from its mouth (fire)."""

    du = 0.5

    def parts(self):
        def body():
            s = Svg(44, 62)
            pts = [(22, 2), (34, 6), (41, 20), (41.5, 44), (37, 58), (22, 61), (7, 58), (2.5, 44), (3, 20), (10, 6)]
            s.path(smooth_closed(pts, 0.9), fill=s.radial(30, 16, 48, [(0, "#d6f29a"), (0.35, "#82c460"), (0.75, "#3f8a48"), (1, "#22573a")]),
                   stroke=INK, width=1.8)
            for k, x in enumerate((9.0, 15.5, 22.0, 28.5, 35.0)):
                bend = (x - 22) * 0.28
                d = f"M{22 + (x - 22) * 0.45:.1f} 4.5 Q{x + bend:.1f} 30 {22 + (x - 22) * 0.78:.1f} 59"
                s.path(d, stroke="#1f5232", width=1.1, opacity=0.55)
                with s.group("translate(1.3 0)"):
                    s.path(d, stroke="#e2f8b0", width=0.8, opacity=0.45)
                for j in range(5):
                    yy = 12 + j * 10 + (k % 2) * 5
                    xx = 22 + (x - 22) * (0.5 + 0.3 * math.sin(math.pi * yy / 62)) + bend * 0.6
                    if 5 < yy < 57:
                        s.path(f"M{xx - 1.8:.1f} {yy - 1.2:.1f} L{xx + 1.8:.1f} {yy + 1.2:.1f} M{xx - 1.8:.1f} {yy + 1.2:.1f} "
                               f"L{xx + 1.8:.1f} {yy - 1.2:.1f}", stroke="#fffbe6", width=0.6)
            s.path(smooth_open([(24, 5), (33, 8), (38, 18)]), stroke="#f4ffd8", width=2.2, opacity=0.6)
            return s

        def arm(side: int):
            s = Svg(18, 24)
            x0 = 2 if side > 0 else 16
            ex = x0 + side * 11
            d = f"M{x0} 20 Q{ex} 20 {ex} 12 L{ex} 5"
            _limb(s, d, 6.4, "#62a650", "#d8f2a0")
            s.path(f"M{ex - 1.6 * side:.1f} 5 Q{ex:.1f} 2.4 {ex + 1.6 * side:.1f} 5", stroke=INK, width=1.0)
            for y in (9.0, 14.0):
                s.circle(ex + 1.6, y, 0.6, fill="#fffbe6")
            return s

        def flower(open_: float):
            s = Svg(26, 16)
            n = 7
            for k in range(n):
                a = math.radians(-180 + k * 180 / (n - 1))
                ln = 6 + 5 * open_
                px, py = 13 + math.cos(a) * ln * 0.9, 13 + math.sin(a) * ln * 0.75
                s.path(f"M13 13 Q{13 + math.cos(a - 0.35) * ln:.1f} {13 + math.sin(a - 0.35) * ln * 0.8:.1f} {px:.1f} {py:.1f} "
                       f"Q{13 + math.cos(a + 0.35) * ln:.1f} {13 + math.sin(a + 0.35) * ln * 0.8:.1f} 13 13 Z",
                       fill=s.linear(13, 13, px, py, [(0, "#ff4f8e"), (1, "#ffb8d4")]), stroke="#7a1240", width=0.8)
            s.circle(13, 12.5, 2.6, fill="#ffd84a", stroke="#a86a10", width=0.7)
            return s

        def spines():
            s = Svg(64, 76)
            pts = [(32, 10), (44, 14), (51, 28), (51.5, 52), (47, 66), (17, 66), (12.5, 52), (13, 28), (20, 14)]
            for i in range(len(pts)):
                ax, ay = pts[i]
                bx, by = pts[(i + 1) % len(pts)]
                if i == 5:
                    continue
                for k in range(3):
                    f = (k + 0.5) / 3
                    x, y = ax + (bx - ax) * f, ay + (by - ay) * f
                    nx, ny = x - 32, y - 40
                    nl = math.hypot(nx, ny) or 1
                    nx, ny = nx / nl, ny / nl
                    s.polygon([(x - ny * 1.1, y + nx * 1.1), (x + nx * 7, y + ny * 7), (x + ny * 1.1, y - nx * 1.1)], fill="#fffbe6",
                              stroke="#8a7a50", width=0.5)
            return s

        def mouth(kind: str):
            s = Svg(14, 12)
            if kind == "idle":
                s.path("M2.5 7 Q7 4.6 11.5 7", stroke=INK, width=1.6)
            elif kind == "charge":
                s.ellipse(7, 6.5, 2.6, 2.2, fill="#5a1420", stroke=INK, width=1.3)
                s.path("M1.5 4.5 Q3 6.5 1.8 8.5 M12.5 4.5 Q11 6.5 12.2 8.5", stroke=INK, width=0.9)
            else:
                s.ellipse(7, 6.5, 5.2, 4.8, fill="#5a1420", stroke=INK, width=1.4)
                s.ellipse(7.6, 7.4, 2.6, 2.2, fill="#e8506a")
            return s

        def base():
            s = Svg(58, 14)
            s.path("M1 13 Q8 5 22 4 Q29 2.6 38 4 Q52 5 57 13 Z", fill=s.linear(0, 3, 0, 13, [(0, SAND_TOP), (1, SAND_MID)]), stroke=SAND_EDGE, width=1.1)
            for (x, y, rad) in ((12, 10, 1.8), (44, 9.6, 2.2), (49, 11.4, 1.3)):
                s.circle(x, y, rad, fill="#c08050", stroke=SAND_EDGE, width=0.5)
            return s

        def burst():
            s = Svg(24, 20)
            s.polygon(star_points(12, 10, 9.5, 4.0, 7), fill="#fff8e0", stroke="#c8a060", width=0.7, opacity=0.95)
            s.circle(12, 10, 4, fill="#ffffff")
            return s

        return {
            "body": (body, (22, 60)), "arm_front": (lambda: arm(1), (2, 20)), "arm_back": (lambda: arm(-1), (16, 20)),
            "flower": (lambda: flower(1.0), (13, 13)), "bud": (lambda: flower(0.0), (13, 13)), "spines": (spines, (32, 68)),
            "mouth_idle": (lambda: mouth("idle"), (7, 6)), "mouth_charge": (lambda: mouth("charge"), (7, 6)),
            "mouth_fire": (lambda: mouth("fire"), (7, 6)), "base": (base, (29, 12)), "burst": (burst, (4, 10)),
            "eye": (lambda: eye_svg(11), (5.5, 5.5)), "eye_angry": (lambda: eye_svg(11, angry=True), (5.5, 5.5)),
            "pupil": (lambda: pupil_svg(5.2), (2.6, 2.6)), "lid": (lambda: _lid(11), (5.5, 2)), "brow": (lambda: _brow(11, 2.6), (5.5, 3)),
        }

    def commands(self, e, t):
        root = Xf()
        if not e.alive:
            root = self.defeat_xf(e, root)
        interval = float(e.params.get("interval", 2.2))
        charge = 0.0
        fired = 0.0
        if e.alive and e.anim == "charge":
            charge = max(0.0, min(1.0, 1 - (interval - e.timer % interval) / 0.45))
        if e.alive and e.anim == "fire":
            fired = max(0.0, min(1.0, e.memory.get("fired", 0.0) / 0.25))
        breathe = math.sin(t * 2.4) * 0.018 if e.alive else 0.0
        shake = math.sin(t * 55) * 0.9 * charge
        sx = 1 + breathe + 0.15 * charge - 0.08 * fired
        sy = 1 - breathe + 0.07 * charge + 0.06 * fired
        out = [self.cmd("base", root)]
        body = root.child(shake, -3, -7 * fired + math.sin(t * 1.3) * 1.5 * (1 - charge))
        body = Xf(body.x, body.y, body.angle, body.sx * sx, body.sy * sy)
        raise_ = -45 * charge - 20 * fired
        out.append(self.cmd("arm_back", body.child(-16, -27, -raise_ * 0.6 + math.sin(t * 2) * 6), tint=FAR))
        if charge > 0.05:
            out.append(self.cmd("spines", body, alpha=min(1.0, charge * 1.6), scale=0.92 + 0.12 * charge))
        out.append(self.cmd("body", body))
        out.append(self.cmd("arm_front", body.child(17, -24, raise_ + math.sin(t * 2 + 1) * 6)))
        out.append(self.cmd("bud" if charge > 0.4 else "flower", body.child(0, -58, math.sin(t * 1.8) * 6), scale=1.0 + 0.25 * fired))
        if e.alive:
            angry = charge > 0.15 or fired > 0
            closed = self.blink(t, e.origin_x) and not angry
            for ex in (6.0, 16.0):
                _eye(self, out, body.child(ex, -38), closed, (1.6, 0.6 if not angry else 1.0), "eye_angry" if angry else "eye")
            out.append(self.cmd("brow", body.child(6, -44.5, 12 if angry else 4)))
            out.append(self.cmd("brow", body.child(16.5, -44.8, 168 if angry else 176)))
            mouth = "mouth_fire" if fired > 0 else ("mouth_charge" if charge > 0.1 else "mouth_idle")
            out.append(self.cmd(mouth, body.child(12, -28)))
            if fired > 0:
                out.append(self.cmd("burst", body.child(17, -28), alpha=fired, scale=0.7 + 0.6 * (1 - fired)))
        return _flash(e, t, out)


# --------------------------------------------------------------------------- Escorpião-Couraça
ARMOR = [(0, "#ffb08a"), (0.25, "#d8503c"), (0.7, "#8a2020"), (1, "#4a0e12")]


@register("scorpion")
class ArmoredScorpion(CreatureRig):
    """Crimson plated scorpion with amber rivets. The tail droops behind with
    the sting pointing at the ground while it is safe to stomp; on guard it
    arches over the back, spiked, with a glowing sting, and the pincers go
    up."""

    du = 0.5
    crest_period, crest_duty = 3.0, 0.35  # species defaults (enemies.json params)

    def parts(self):
        def body():
            s = Svg(60, 34)
            base = "M2 23 Q1.6 15 8 13.4 L44 10 Q56 9.4 59 18 Q59.6 26.4 52 28.6 L9 30 Q2.2 29.4 2 23 Z"
            s.path(base, fill=s.linear(0, 9, 0, 30, [(0, "#b8342c"), (0.6, "#7a1c1c"), (1, "#4a0e12")]), stroke=INK, width=1.8)
            s.path("M7 27.6 Q28 31.6 53 27.4", stroke="#f2b48a", width=2.0, opacity=0.75)
            for k in range(5):  # overlapping tergites, tail end to head
                x = 4.5 + k * 7.6
                top = 12.4 - k * 0.6
                d = f"M{x:.1f} 25 L{x:.1f} {top + 3:.1f} Q{x + 4.8:.1f} {top - 3.4:.1f} {x + 10:.1f} {top + 1.4:.1f} L{x + 10:.1f} 25.4 Z"
                s.path(d, fill=s.linear(0, top - 3, 0, 25, [(0, "#ff8a6a"), (0.35, "#d0443a"), (1, "#7a1c1c")]), stroke=INK, width=1.0)
                s.path(f"M{x + 0.8:.1f} {top + 2:.1f} Q{x + 4.8:.1f} {top - 2.4:.1f} {x + 9.2:.1f} {top + 1.4:.1f}", stroke="#ffd0a0",
                       width=0.9, opacity=0.9)
                s.circle(x + 5, 19.4, 1.0, fill="#ffb84a", stroke="#5a1a10", width=0.4)
            s.path("M42 26 L42 13 Q46 6.4 53 7.6 Q59.6 9.6 60 18 Q60 24.4 54 26.4 Z",
                   fill=s.radial(53, 7, 16, [(0, "#ffb08a"), (0.4, "#d8503c"), (1, "#7a1c1c")]), stroke=INK, width=1.3)
            s.path("M45 11.4 Q51 6.8 57 9.8", stroke="#ffd8b8", width=1.2, opacity=0.9)
            s.circle(51, 17, 1.1, fill="#ffb84a", stroke="#5a1a10", width=0.4)
            return s

        def leg(front: bool):
            s = Svg(18, 20)
            d = "M3 6 L9 1.6 L14.6 17.6" if front else "M15 6 L9 1.6 L3.4 17.6"
            _limb(s, d, 2.0, "#9a2a24", "#ff9a7a")
            return s

        def arm():
            s = Svg(20, 12)
            s.path(rounded_rect_path(2, 2.5, 16, 7, 3.4), fill=s.linear(0, 2, 0, 10, [(0, "#e8604a"), (1, "#6a1418")]), stroke=INK, width=1.2)
            s.circle(16.4, 6, 2.3, fill="#ffb84a", stroke=INK, width=0.8)
            return s

        def claw():
            s = Svg(30, 24)
            s.path("M2 13 Q2 5 11 4.4 Q19 4 21.6 10 Q23 14.6 19 17.6 Q11 21 5 18.6 Q2 17 2 13 Z",
                   fill=s.radial(15, 5, 20, ARMOR), stroke=INK, width=1.4)
            s.path("M18.6 16 Q25 15.4 29.4 19.6 Q26 21.8 19.6 20.2 Z", fill="#9a2a24", stroke=INK, width=1.1)
            s.path("M7 7.4 Q13 5 19 7.4", stroke="#ffd0b0", width=1.2, opacity=0.85)
            s.circle(9, 12, 1.1, fill="#ffb84a")
            return s

        def finger():
            s = Svg(16, 10)
            s.path("M1 7 Q6 2 12 2.6 Q15.6 3.4 15 7.2 Q10 5.8 4 8.6 Z", fill="#d04a3a", stroke=INK, width=1.1)
            return s

        def seg(spiky: bool):
            s = Svg(16, 16)
            if spiky:
                for x in (5.0, 10.4):
                    s.polygon([(x - 1.8, 4.6), (x + 0.2, 0.4), (x + 1.8, 4.6)], fill="#ffe7b0", stroke=INK, width=0.7)
            s.path(_ellipse_d(8.5, 8, 6.8, 5.8), fill=s.radial(10, 4, 9, ARMOR), stroke=INK, width=1.3)
            s.path("M4.4 5.2 Q8.5 2.8 12.6 5.2", stroke="#ffc890", width=0.9, opacity=0.9)
            s.circle(8.5, 9, 0.9, fill="#ffb84a")
            return s

        def stinger(hot: bool):
            s = Svg(26, 26)
            if hot:
                s.circle(14, 13, 12, fill=s.radial(14, 13, 12, [(0, "#ffe08a", 0.85), (0.5, "#ff7a3a", 0.4), (1, "#ff5a2a", 0)]))
                for a in (-60.0, 0.0, 60.0, 120.0, 180.0):
                    ra = math.radians(a)
                    s.polygon([(10 + math.cos(ra - 0.4) * 6, 12.6 + math.sin(ra - 0.4) * 5), (10 + math.cos(ra) * 10.5, 12.6 + math.sin(ra) * 9.5),
                               (10 + math.cos(ra + 0.4) * 6, 12.6 + math.sin(ra + 0.4) * 5)], fill="#ffe7b0", stroke=INK, width=0.6)
            bulb = [(0, "#fff0b0"), (0.55, "#f2b040"), (1, "#a86a10")] if not hot else [(0, "#fff6d0"), (0.5, "#ff9a3a"), (1, "#c8301c")]
            s.path("M2 13 Q4 6.5 11 6.6 Q17 7 18.6 12 Q19.4 16 15 18.6 Q8 20 4 17.4 Q2 15.6 2 13 Z",
                   fill=s.radial(13, 9, 11, bulb), stroke=INK, width=1.3)
            s.path("M17.6 14.6 Q23 15.8 24.6 21.6 Q20.6 18.6 15.6 18.4 Z", fill="#3a0e10" if not hot else "#8a0e0e", stroke=INK, width=1.0)
            s.ellipse(11, 10, 2.6, 1.4, fill="#ffffff", opacity=0.7)
            return s

        return {
            "body": (body, (30, 30)), "leg_front": (lambda: leg(True), (3, 6)), "leg_back": (lambda: leg(False), (15, 6)),
            "arm": (arm, (3, 6)), "claw": (claw, (3, 12)), "finger": (finger, (2, 6)),
            "seg": (lambda: seg(False), (2, 8)), "seg_spiky": (lambda: seg(True), (2, 8)),
            "stinger": (lambda: stinger(False), (3, 13)), "stinger_hot": (lambda: stinger(True), (3, 13)),
            "eye": (lambda: eye_svg(10), (5, 5)), "eye_angry": (lambda: eye_svg(10, angry=True), (5, 5)),
            "pupil": (lambda: pupil_svg(5), (2.5, 2.5)), "lid": (lambda: _lid(10), (5, 2)),
        }

    def _raise(self, e) -> float:
        """0 = tail drooping (stompable), 1 = tail arched (spiked); eased from
        the same crest cycle the behaviour uses."""
        guard = 1.0 if e.anim == "guard" else 0.0
        period = float(e.params.get("crest_period", self.crest_period))
        duty = float(e.params.get("crest_duty", self.crest_duty))
        if period <= 0:
            return guard
        phase = e.timer % period
        up = period * duty
        k = min(1.0, phase / 0.16) if phase < up else max(0.0, 1.0 - (phase - up) / 0.16)
        return smoothstep(k) if (k > 0.5) == (guard > 0.5) else guard

    def commands(self, e, t):
        root = Xf()
        if not e.alive:
            root = self.defeat_xf(e, root)
        k = self._raise(e) if e.alive else 0.0
        walking = e.alive
        ph = t * 9.0
        bob = -abs(math.sin(ph)) * 1.0 if walking else 0.0
        body = root.child(0, -12 + bob - 2 * k)
        out: list[DrawCommand] = []
        legs = [(-17.0, False), (-10.0, False), (3.0, True), (10.0, True)]
        for i, (lx, front) in enumerate(legs):
            sw = math.sin(ph + i * 1.7 + 0.8) * 14 if walking else 0.0
            out.append(self.cmd("leg_front" if front else "leg_back", body.child(lx + 4, -6, sw), tint=FAR))
        # tail: drooping with the sting down (k=0) -> arched over the back (k=1)
        low = (186.0, -10.0, -16.0, -20.0, -22.0)
        high = (250.0, 36.0, 34.0, 30.0, 26.0)
        sway = math.sin(t * 2.6) * 3 * (1 - k) + math.sin(t * 7) * 2 * k
        xf = body.child(-25, -14, low[0] + (high[0] - low[0]) * k + sway)
        segs = []
        for i in range(5):
            scale = 1.0 - i * 0.07
            segs.append((xf, scale))
            j = min(i + 1, 4)
            xf = xf.child(9.0 * scale, 0, low[j] + (high[j] - low[j]) * k + sway * 0.5)
        name = "seg_spiky" if k > 0.5 else "seg"
        for sxf, scale in segs:
            out.append(self.cmd(name, sxf, scale=scale))
        out.append(self.cmd("stinger_hot" if k > 0.5 else "stinger", xf.child(-1, 0, 6 * k), scale=0.85))
        # pincers: low and snapping while walking, raised and wide open on guard
        arm_a = 34 - 72 * k + math.sin(ph * 0.5) * 6 * (1 - k)
        far_arm = body.child(21, -11, arm_a + 10)
        out.append(self.cmd("arm", far_arm, tint=FAR))
        out.append(self.cmd("claw", far_arm.child(16, 0, -50 + 20 * k), tint=FAR, scale=0.9))
        out.append(self.cmd("body", body))
        snap = (0.5 + 0.5 * math.sin(t * 6)) * (1 - k) + k
        arm = body.child(23, -9, arm_a)
        out.append(self.cmd("arm", arm))
        claw = arm.child(16, 0, -52 + 22 * k)
        out.append(self.cmd("finger", claw.child(15, -4, -8 - 30 * snap)))
        out.append(self.cmd("claw", claw))
        if e.alive:
            closed = self.blink(t, e.origin_x) and k < 0.5
            for ex in (17.0, 23.5):
                _eye(self, out, body.child(ex, -25 - 1.5 * k), closed, (1.2, 0.4), "eye_angry" if k > 0.5 else "eye")
        for i, (lx, front) in enumerate(legs):
            sw = math.sin(ph + i * 1.7) * 14 if walking else 0.0
            out.append(self.cmd("leg_front" if front else "leg_back", body.child(lx, -5, sw)))
        return _flash(e, t, out)


# --------------------------------------------------------------------------- Serpente-de-Duna
@register("dune_serpent")
class DuneSerpent(CreatureRig):
    """Teal sand viper with gold diamonds and little horns. Underground only
    a travelling sand mound and its dust trail show; it erupts with a burst,
    slithers in humps and dives back head first."""

    du = 0.5

    def parts(self):
        def seg(fill_only: bool):
            s = Svg(26, 26)
            if not fill_only:
                s.circle(13, 13, 12.2, fill=INK)
                return s
            s.circle(13, 13, 11, fill=s.radial(16, 7, 16, [(0, "#9af0dc"), (0.4, "#33b0a0"), (1, "#145a5a")]))
            s.path("M3.6 17 Q13 25.6 22.4 17 Q13 21.6 3.6 17 Z", fill="#f6e6b8")
            s.polygon([(13, 2.4), (18.2, 7.6), (13, 12.6), (7.8, 7.6)], fill=s.linear(8, 2, 18, 12, [(0, "#fff0a0"), (1, "#d8962a")]),
                      stroke="#7a4a10", width=0.7)
            return s

        def head():
            s = Svg(38, 30)
            s.path("M3 18 Q2 8 13 5.6 Q24 3.6 31 9.6 Q36.6 14 35.6 18.6 Q34 22.6 27 23 L12 24.4 Q4 24.6 3 18 Z",
                   fill=s.radial(22, 8, 22, [(0, "#a8f6e2"), (0.4, "#36b2a2"), (1, "#145a5a")]), stroke=INK, width=1.6)
            s.path("M8 21.6 Q20 25.6 34.4 19.6 Q30 23.6 20 24.2 Q11 24.6 8 21.6 Z", fill="#f6e6b8")
            s.polygon([(13, 7), (17.6, 10.6), (13, 14.4), (8.4, 10.6)], fill="#f2c050", stroke="#7a4a10", width=0.7)
            s.path("M18 6 Q20 0.4 24.6 1.2 Q22 3 22.6 6.4 Z", fill="#f2c860", stroke=INK, width=1.0)
            s.circle(32, 14.6, 0.9, fill=INK)
            s.path("M22 19.4 Q27 21.6 33 18.2", stroke=INK, width=1.1)
            return s

        def eye():
            s = Svg(12, 12)
            s.ellipse(6, 6, 5, 5.4, fill="#fff8d8", stroke=INK, width=1.0)
            return s

        def pupil():
            s = Svg(6, 8)
            s.ellipse(3, 4, 1.8, 3.4, fill="#1e1626")
            s.circle(3.8, 2.4, 0.8, fill="#ffffff")
            return s

        def tongue():
            s = Svg(14, 8)
            s.path("M1 4 L8 4 L12.6 1.4 M8 4 L12.6 6.6", stroke="#c81e3a", width=1.3)
            return s

        def tail():
            s = Svg(24, 16)
            s.path("M23 2.4 Q12 4 1.5 9.6 Q12 13.6 23 13.6 Z", fill=s.linear(0, 2, 0, 14, [(0, "#5ad0be"), (1, "#145a5a")]), stroke=INK, width=1.3)
            s.path("M23 12 Q14 12.6 6 10.4", stroke="#f6e6b8", width=1.4)
            return s

        return {
            "seg_ink": (lambda: seg(False), (13, 13)), "seg": (lambda: seg(True), (13, 13)), "head": (head, (8, 18)),
            "eye": (eye, (6, 6)), "pupil": (pupil, (3, 4)), "lid": (lambda: _lid(11), (5.5, 2)), "tongue": (tongue, (1, 4)),
            "tail": (tail, (22, 8)), "mound": (lambda: sand_mound(76, 24, 9), (38, 22)), "puff": (lambda: sand_puff(11), (12, 12)),
        }

    def _snake(self, e, t: float, root: Xf, sink: float = 0.0, lift: float = 1.0) -> list[DrawCommand]:
        """Slithering body: segments ride a travelling hump wave (two passes:
        ink discs first, fills on top, so the tube has one clean outline)."""
        ph = t * 7.0
        n = 7
        pts = []
        for i in range(n):
            x = 12 - i * 7.6 + sink * i * 2.2
            hump = max(0.0, math.sin(ph - i * 0.95)) * 7 * lift
            pts.append((x, -11 - hump + sink * 6))
        scale = [(1.0 - i * 0.06) * (1 - sink * 0.5) for i in range(n)]
        out: list[DrawCommand] = []
        tail_x, tail_y = pts[-1]
        out.append(self.cmd("tail", root.child(tail_x - 4, tail_y + 1, math.sin(ph - n) * 10), scale=1 - sink * 0.5))
        for (x, y), sc in zip(reversed(pts), reversed(scale)):
            out.append(self.cmd("seg_ink", root.child(x, y), scale=sc))
        for (x, y), sc in zip(reversed(pts), reversed(scale)):
            out.append(self.cmd("seg", root.child(x, y), scale=sc))
        head = root.child(18 - 4 * sink, -21 + 18 * sink + math.sin(ph * 0.5) * 1.5 * lift, -6 + 75 * sink + math.sin(ph * 0.5) * 4)
        hs = 1 - sink * 0.65
        if (t * 1.3 + e.origin_x * 0.01) % 1.0 < 0.22 and e.alive and sink < 0.3:
            out.append(self.cmd("tongue", head.child(26, 1.4, math.sin(t * 40) * 8)))
        out.append(self.cmd("head", head, scale=hs))
        if e.alive and sink < 0.5:
            _eye(self, out, head.child(22 * hs, -3 * hs), self.blink(t, e.origin_x), (1.0, 0.2))
        return out

    def commands(self, e, t):
        root = Xf()
        if not e.alive:
            root = self.defeat_xf(e, root)
            return _flash(e, t, self._snake(e, t, root, lift=0.0))
        state = e.anim
        out: list[DrawCommand] = []
        if state == "underground":  # only the travelling hump and its dust trail
            moving = abs(e.vx) > 1
            back = (-1.0 if e.vx * e.facing > 0 else 1.0) if moving else 1.0
            wob = math.sin(t * (16 if moving else 8))
            if moving:
                out += _puffs(self, root.child(back * 14, -4), t, 2.4, 4, 34, 16, back, 0.9)
            out.append(self.cmd("mound", Xf(root.x, root.y, 0, 1.0 + 0.06 * wob, 0.86 + 0.1 * wob)))
            if moving:  # a smaller wake of loose sand behind the hump
                out.append(self.cmd("mound", root.child(back * 30, 0), scale=0.42 + 0.04 * math.sin(t * 16 + 1)))
            return _flash(e, t, out)
        if state == "surface":
            k = min(1.0, e.state_time / 0.45)
            jitter = math.sin(t * 70) * 1.8 * (1 - k * 0.5)
            out += _puffs(self, root.child(0, -10), t, 3.0, 4, 14, 34, 1, 0.9 * k)
            out += _puffs(self, root.child(0, -10), t + 0.13, 3.0, 3, 14, 34, -1, 0.9 * k)
            if k > 0.55:
                rise = (k - 0.55) / 0.45
                head = root.child(4 + jitter, -10 - 16 * rise, -70 + 40 * rise)
                out.append(self.cmd("head", head))
                _eye(self, out, head.child(22, -3), False, (1.0, 0.2))
            out.append(self.cmd("mound", Xf(root.x + jitter, root.y, 0, 0.9 + 0.35 * k, 0.8 + 0.5 * k)))
            return _flash(e, t, out)
        if state == "dig":
            k = min(1.0, e.state_time / 0.5)
            out += self._snake(e, t, root, sink=k, lift=1 - k)
            out += _puffs(self, root.child(14, -8), t, 3.0, 3, 12, 22, 1, 0.8 * (1 - k * 0.5))
            out.append(self.cmd("mound", root.child(12, 0), scale=0.45 + 0.55 * k))
            return _flash(e, t, out)
        out += self._snake(e, t, root)
        return _flash(e, t, out)


# --------------------------------------------------------------------------- Escaravelho Lançador
EMERALD = [(0, "#d6fff0"), (0.2, "#6ee0b0"), (0.55, "#1f8a5e"), (0.85, "#0c4630"), (1, "#062a1c")]


@register("scarab_thrower")
class ScarabThrower(CreatureRig):
    """Upright emerald scarab in a sand-coloured head wrap and teal scarf.
    Side-steps, hops, and lifts a packed sand ball overhead with both arms
    before hurling it in an arc."""

    du = 0.5

    def parts(self):
        def torso():
            s = Svg(46, 50)
            s.path(smooth_closed([(22, 2), (36, 7), (43, 22), (40, 40), (30, 48), (16, 48), (6, 40), (3, 22), (9, 7)], 0.9),
                   fill=s.radial(31, 12, 44, EMERALD), stroke=INK, width=1.8)
            s.path("M30 10 Q42 22 38 40 Q34 46 28 47 Q34 30 30 10 Z", fill=s.linear(30, 10, 40, 46, [(0, "#fff0c0"), (1, "#d0a050")]),
                   stroke=INK, width=1.0)
            for y in (20.0, 27.0, 34.0, 41.0):
                s.path(f"M{31 + (y - 20) * 0.08:.1f} {y:.1f} Q35 {y + 1:.1f} {39.5 - (y - 20) * 0.1:.1f} {y - 0.6:.1f}", stroke="#a87830", width=0.8)
            s.path("M19 4 Q16 26 20 46", stroke="#06261a", width=1.4, opacity=0.8)
            s.path("M20.4 5 Q17.4 26 21.4 45", stroke="#a8ffd8", width=0.7, opacity=0.5)
            s.path("M6 28 Q22 20 40 15 L42 20.5 Q24 25 8 34 Z", fill=s.linear(6, 20, 42, 30, [(0, "#a8302a"), (0.5, "#e05040"), (1, "#a8302a")]),
                   stroke=INK, width=1.0)
            for k in range(5):
                s.circle(10 + k * 6.6, 28.6 - k * 2.6, 1.0, fill="#ffd27a")
            s.path(smooth_open([(14, 6), (26, 3), (36, 9)]), stroke="#ffffff", width=2.2, opacity=0.5)
            return s

        def head():
            s = Svg(38, 34)
            s.path("M17 12 Q14 2 23 0.6 Q20.6 4 22.6 11 Z", fill=s.linear(14, 0, 23, 12, [(0, "#ffe9a0"), (1, "#b07a20")]), stroke=INK, width=1.1)
            s.path(blob(18, 19, 12, 11, 0.03, seed=6), fill=s.radial(23, 13, 16, EMERALD), stroke=INK, width=1.5)
            s.path("M6.5 14 Q18 7 30 12.6 L30.6 17.6 Q18 12.6 6.2 19 Z", fill=s.linear(0, 8, 0, 19, [(0, "#fff4dc"), (1, "#d8bc8a")]),
                   stroke=INK, width=1.1)
            s.path("M7 16.8 Q18 11.6 30.4 15.4", stroke="#2aa89a", width=1.6)
            s.path("M27 25 Q33 25.4 34.4 28.4 Q31 27.6 28 28.4 Z", fill="#3a2a1a", stroke=INK, width=0.9)
            return s

        def scarf():
            s = Svg(32, 18)
            s.path("M1 3 Q10 0.6 18 4 Q25 7 31 4.6 Q29 9.6 21 9.4 Q12 9 2 7.6 Z",
                   fill=s.linear(0, 1, 0, 10, [(0, "#6ee8d8"), (1, "#178a7e")]), stroke=INK, width=1.0)
            s.path("M2 7 Q11 9.6 17 12.4 Q22 14.6 27 13 Q24 17.6 17 16.6 Q9 14.6 1.6 9.6 Z",
                   fill=s.linear(0, 7, 0, 17, [(0, "#3ac8b8"), (1, "#0f6a62")]), stroke=INK, width=1.0)
            s.path("M8 3.4 L9 7.6 M14 3.8 L15 8.4", stroke="#ffffff", width=0.9, opacity=0.7)
            return s

        def upper():
            s = Svg(18, 10)
            s.path(rounded_rect_path(1.5, 2, 15, 6, 3), fill=s.linear(0, 2, 0, 8, [(0, "#3aa878"), (1, "#0c3a26")]), stroke=INK, width=1.1)
            s.circle(15, 5, 2.0, fill="#e8b04a", stroke=INK, width=0.6)
            return s

        def fore():
            s = Svg(22, 14)
            s.path(rounded_rect_path(1.5, 4, 13, 6, 3), fill=s.linear(0, 4, 0, 10, [(0, "#3aa878"), (1, "#0c3a26")]), stroke=INK, width=1.1)
            s.path("M14 7 L19 3.4 M14 7 L20.6 7 M14 7 L19 10.6", stroke=INK, width=2.4)
            s.path("M14 7 L19 3.4 M14 7 L20.6 7 M14 7 L19 10.6", stroke="#2a6a4a", width=1.0)
            return s

        def leg():
            s = Svg(16, 24)
            _limb(s, "M8 2 L11 11 L6 20 L12 21.6", 3.0, "#1f6a48", "#7ae0b0")
            return s

        def ball():
            s = Svg(26, 26)
            s.circle(13, 13, 12.5, fill=s.radial(13, 13, 12.5, [(0, "#ffe8a8", 0.8), (1, "#e8c07a", 0)]))
            s.circle(13, 13, 8, fill=s.radial(15, 10, 9, [(0, "#fff6d8"), (0.5, "#e8c07a"), (1, "#a8783a")]), stroke="#6b3820", width=1.0)
            r = Rand(5)
            for _ in range(7):
                a, rr = r.uniform(0, 6.28), r.uniform(2, 6.5)
                s.circle(13 + math.cos(a) * rr, 13 + math.sin(a) * rr, 0.7, fill="#8a5a2a")
            return s

        def whoosh():
            s = Svg(30, 30)
            s.path("M4 26 Q4 6 26 4 Q12 10 10 26 Z", fill="#ffffff", opacity=0.6)
            return s

        return {
            "torso": (torso, (23, 46)), "head": (head, (14, 28)), "scarf": (scarf, (2, 4)), "upper": (upper, (3, 5)), "fore": (fore, (3, 7)),
            "leg": (leg, (8, 2)), "ball": (ball, (13, 13)), "whoosh": (whoosh, (6, 24)),
            "eye": (lambda: eye_svg(11), (5.5, 5.5)), "pupil": (lambda: pupil_svg(5.4), (2.7, 2.7)), "lid": (lambda: _lid(11), (5.5, 2)),
            "brow": (lambda: _brow(11, 2.6), (5.5, 3)),
        }

    def commands(self, e, t):
        root = Xf()
        if not e.alive:
            root = self.defeat_xf(e, root)
        state = e.anim if e.alive else "defeat"
        st = e.state_time
        ph = t * 10.0
        lean = 0.0
        legs = (math.sin(ph) * 20, -math.sin(ph) * 20)
        bob = -abs(math.sin(ph)) * 1.6
        shoulder_a, elbow_a = 70.0 + math.sin(ph) * 14, -40.0
        shoulder_b, elbow_b = 80.0 - math.sin(ph) * 14, -50.0
        ball_k = 0.0
        if state == "windup":
            k = smoothstep(st / 0.22)
            lean = -8 * k
            shoulder_a = 70 + (-125 - 70) * k
            shoulder_b = 80 + (-100 - 80) * k
            elbow_a, elbow_b = -40 + 55 * k, -50 + 30 * k
            ball_k = k
            legs = (-14.0, 18.0)
            bob = 0.0
        elif state == "throw":
            k = smoothstep(st / 0.14)
            lean = 12 * k - 8 * (1 - k)
            shoulder_a = -100 + 125 * k
            shoulder_b = -86 + 116 * k
            elbow_a = elbow_b = -10.0
            legs = (-20.0, 22.0)
            bob = 0.0
        elif state == "jump":
            rising = e.vy < 0
            legs = (-55.0, 40.0) if rising else (-25.0, 20.0)
            shoulder_a, shoulder_b = (-120.0, -100.0) if rising else (-60.0, -40.0)
            elbow_a = elbow_b = -30.0
            bob = 0.0
        elif state == "defeat":
            bob = 0.0
            legs = (-70.0, 70.0)
            shoulder_a, shoulder_b, elbow_a, elbow_b = 10.0, 160.0, 0.0, 0.0
        hips = root.child(0, -20 + bob)
        torso = hips.child(-2, 4, lean)
        out: list[DrawCommand] = []
        out.append(self.cmd("leg", hips.child(-5, -2, legs[1]), tint=FAR))
        out.append(self.cmd("scarf", torso.child(-6, -40, 155 + math.sin(t * 9) * 10)))
        shoulder = torso.child(9, -34)
        upper_b = shoulder.child(-6, 0, shoulder_b)
        out.append(self.cmd("upper", upper_b, tint=FAR))
        out.append(self.cmd("fore", upper_b.child(14, 0, elbow_b), tint=FAR))
        out.append(self.cmd("torso", torso))
        upper_a = shoulder.child(0, 0, shoulder_a)
        fore_a = upper_a.child(14, 0, elbow_a)
        near_arm = [self.cmd("upper", upper_a), self.cmd("fore", fore_a)]
        if ball_k > 0:  # the ball sits in the raised hands, up behind the head
            near_arm.insert(0, self.cmd("ball", fore_a.child(20, -2), scale=0.4 + 0.8 * ball_k))
        head = torso.child(2, -42, lean * 0.3 + math.sin(t * 2.5) * 3)
        out.append(self.cmd("head", head))
        if e.alive:
            _eye(self, out, head.child(9, -6), self.blink(t, e.origin_x), (1.5, 0.5))
            out.append(self.cmd("brow", head.child(9.5, -12.5, 14 if state in ("windup", "throw") else 6)))
        out.append(self.cmd("leg", hips.child(4, -2, legs[0])))
        out += near_arm
        if state == "throw" and st < 0.2:
            out.append(self.cmd("whoosh", torso.child(16, -40, 20), alpha=1 - st / 0.2))
        return _flash(e, t, out)
