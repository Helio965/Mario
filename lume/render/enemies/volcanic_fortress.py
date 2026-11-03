"""Fortaleza Vulcânica creatures.

* ``ember`` — Brasa Andante: a living lump of coal on stubby legs, cracked
  with magma, a flame tuft on top (fire-immune walker).
* ``basalt_turtle`` — Ermitão-de-Basalto: a magma hermit crab living inside a
  chunk of porous basalt; it hides in the rock, and a kicked rock rolls.
* ``bat`` — Morcego-Brasa: a charcoal bat whose wing membranes glow like
  embers along their trailing edge.
* ``furnace_mouth`` — Boca-de-Fornalha: a stone gargoyle furnace; its maw
  brightens while it draws breath and blazes when it spits.
* ``golem`` — Golem de Basalto: hexagonal basalt columns bound by iron bands
  around a furnace core; raises obsidian spikes on guard, cracks after the
  first hit.
* ``magma_bubble`` — Salta-Brasa: a small ember spirit (a flame tongue with
  eyes) that leaps out of lava; while submerged only bubbles show.

Fire creatures carry a soft halo part so they read against dark basalt and red
skies. A hit blinks a cool tint (a red flash would vanish on warm bodies) and
defeated creatures cool down to ash grey while their glow dies out.
"""

from __future__ import annotations

import math

from ..rig import DrawCommand, Xf
from ..svg import Svg, blob, rounded_rect_path, smooth_closed, smooth_open, star_points
from .base import CreatureRig, register

INK = "#1b0f15"
MAGMA_WHITE, MAGMA_YELLOW, MAGMA_ORANGE, MAGMA_RED, MAGMA_DARK = "#fff4c4", "#ffc548", "#ff7d2c", "#d8391f", "#7a1810"
COAL_HI, COAL, COAL_DARK, COAL_DEEP = "#5e4c55", "#382a32", "#221820", "#120b10"
IRON_HI, IRON, IRON_DARK = "#a9a7b4", "#6c6977", "#3e3b47"
STONE_HI, STONE, STONE_DARK = "#b0a0a4", "#7c6a70", "#46363e"
FLASH = (150, 205, 255)  # cool blink on warm bodies
ASH = (112, 102, 108)  # fully cooled tint


def _glow_line(s: Svg, d: str, width: float = 1.0, hot: bool = True, opacity: float = 1.0) -> None:
    s.path(d, stroke=MAGMA_RED, width=width * 4.2, opacity=0.25 * opacity)
    s.path(d, stroke=MAGMA_ORANGE, width=width * 1.8, opacity=0.95 * opacity)
    if hot:
        s.path(d, stroke=MAGMA_YELLOW, width=width * 0.75, opacity=opacity)


def _halo(w: float, h: float, color: str = MAGMA_ORANGE, strength: float = 0.6) -> Svg:
    s = Svg(w, h)
    r = min(w, h) / 2
    with s.group(transform=f"translate({w / 2:.2f} {h / 2:.2f}) scale({w / 2 / r:.4f} {h / 2 / r:.4f})"):
        s.circle(0, 0, r, fill=s.radial(0, 0, r, [(0, color, strength), (0.4, color, strength * 0.45), (1, color, 0)]))
    return s


def _flame_path(cx: float, base: float, w: float, h: float, lean: float = 0.0) -> str:
    """Three-tongued flame silhouette standing on ``base``."""
    pts = [
        (cx - w * 0.5, base - h * 0.18),
        (cx - w * 0.42, base - h * 0.5), (cx - w * 0.3 + lean * 0.4, base - h * 0.72),
        (cx - w * 0.16, base - h * 0.5),
        (cx - w * 0.02 + lean, base - h),
        (cx + w * 0.14, base - h * 0.55),
        (cx + w * 0.3 + lean * 0.5, base - h * 0.8),
        (cx + w * 0.42, base - h * 0.45),
        (cx + w * 0.5, base - h * 0.16),
        (cx + w * 0.3, base + h * 0.02),
        (cx - w * 0.3, base + h * 0.02),
    ]
    return smooth_closed(pts, 0.6)


def _flame(s: Svg, cx: float, base: float, w: float, h: float, lean: float = 0.0) -> None:
    s.path(_flame_path(cx, base, w, h, lean), fill=s.linear(0, base - h, 0, base, [(0, MAGMA_RED, 0.85), (0.45, MAGMA_ORANGE), (1, MAGMA_YELLOW)]))
    s.path(_flame_path(cx + w * 0.02, base, w * 0.66, h * 0.7, lean * 0.6),
           fill=s.linear(0, base - h * 0.7, 0, base, [(0, MAGMA_ORANGE, 0.9), (0.5, MAGMA_YELLOW), (1, MAGMA_WHITE)]))
    s.path(_flame_path(cx + w * 0.03, base, w * 0.34, h * 0.4, lean * 0.3), fill=MAGMA_WHITE, opacity=0.9)


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


class _VolcanicRig(CreatureRig):
    """Shared finishing: hit blink, cooling on defeat, glow parts dying out."""

    du = 0.5
    glow_parts: tuple[str, ...] = ("halo",)

    def finish(self, e, t: float, out: list[DrawCommand]) -> list[DrawCommand]:
        if e.alive:
            if e.hit_timer > 0 and int(t * 20) % 2 == 0:
                for c in out:
                    c.tint = FLASH
            return out
        k = max(0.0, min(1.0, e.defeated / 0.6))
        cool = tuple(int(_lerp(a, 255, k * k)) for a in ASH)
        glow = {self.part_id(n) for n in self.glow_parts}
        for c in out:
            base = c.tint or (255, 255, 255)  # keep depth tints (far limbs) while cooling
            c.tint = (base[0] * cool[0] // 255, base[1] * cool[1] // 255, base[2] * cool[2] // 255)
            if c.part in glow:
                c.alpha *= k * k
        return out

    @staticmethod
    def pulse(t: float, speed: float, lo: float, hi: float, seed: float = 0.0) -> float:
        return lo + (hi - lo) * (0.5 + 0.5 * math.sin(t * speed + seed))


# =========================================================================== Brasa Andante
@register("ember")
class EmberWalker(_VolcanicRig):
    """Living coal: faceted lump with magma cracks, hot belly and a flame tuft."""

    def parts(self):
        def body():
            s = Svg(56, 48)
            outline = [(5, 31), (8, 16), (18, 7), (31, 3.5), (44, 7), (51.5, 18), (52.5, 32), (46.5, 42.5), (30, 46.5), (12, 44)]
            s.polygon(outline, fill=s.radial(20, 14, 42, [(0, "#66545c"), (0.45, COAL), (1, COAL_DEEP)]), stroke=INK, width=1.9)
            # facets of the coal
            s.polygon([(8.5, 16.5), (18, 7.5), (31, 4.5), (26, 16), (14, 20)], fill="#56444c", opacity=0.9)
            s.polygon([(31, 4.5), (43.5, 7.8), (50.5, 18), (38, 18.5), (26, 16)], fill="#44363e", opacity=0.9)
            s.polygon([(5.8, 30.5), (14, 20), (26, 16), (21, 31), (12.5, 43)], fill="#2a1e25", opacity=0.85)
            s.path("M10 16 L18 9 L29 6", stroke="#9a8890", width=1.3, opacity=0.8)
            # hot belly and magma cracks (kept off the face on the right)
            s.ellipse(28, 39, 21, 9, fill=s.radial(28, 41, 22, [(0, "#ffa03c", 0.85), (0.55, "#e0401e", 0.4), (1, "#e0401e", 0)]))
            _glow_line(s, "M14 20 L19.5 25.5 L17.5 32 L23 39", 0.95)
            _glow_line(s, "M26 16 L28.5 23 L24 28", 0.85)
            _glow_line(s, "M8 33 L13 35 L11.5 40", 0.7, False)
            # jagged glowing grin
            s.path("M35 34.5 L38 37 L41 34.8 L44 37.2 L47.5 34", stroke=INK, width=3.4)
            s.path("M35 34.5 L38 37 L41 34.8 L44 37.2 L47.5 34", stroke=MAGMA_YELLOW, width=1.5)
            return s

        def eye():
            s = Svg(12, 12)
            s.ellipse(6, 6, 4.7, 5.3, fill=s.radial(5, 4.6, 6, [(0, "#ffffff"), (0.55, "#fff1bc"), (1, "#ffc24a")]), stroke=INK, width=1.1)
            return s

        def pupil():
            s = Svg(6, 7)
            s.ellipse(3, 3.5, 2.2, 3.0, fill="#2a0c08")
            s.circle(3.8, 2.4, 0.8, fill="#ffffff")
            return s

        def brow():
            s = Svg(13, 6)
            s.path("M1 1.8 L12 4.6 L11 5.8 L1.4 3.8 Z", fill=COAL_DEEP, stroke=INK, width=0.8)
            return s

        def flame():
            s = Svg(30, 32)
            _flame(s, 15, 30, 26, 29, 1.5)
            return s

        def leg():
            s = Svg(13, 15)
            s.path(rounded_rect_path(2, 0.5, 9, 11.5, 3.5), fill=s.linear(2, 0, 11, 0, [(0, COAL_HI), (1, COAL_DEEP)]), stroke=INK, width=1.3)
            s.path(blob(6.5, 11.8, 5.6, 3, 0.04, seed=2, squash_top=1.3), fill=COAL_DARK, stroke=INK, width=1.2)
            s.path("M5 12.4 L7 11 L8.6 12.6", stroke=MAGMA_ORANGE, width=0.9)
            return s

        return {
            "halo": (lambda: _halo(96, 84, MAGMA_ORANGE, 0.55), (48, 42)),
            "body": (body, (28, 46)),
            "eye": (eye, (6, 6)),
            "pupil": (pupil, (3, 3.5)),
            "brow": (brow, (6.5, 3)),
            "flame": (flame, (15, 30)),
            "leg": (leg, (6.5, 1.5)),
        }

    def commands(self, e, t):
        root = Xf()
        if not e.alive:
            root = self.defeat_xf(e, root)
        walking = e.anim == "walk" and e.alive
        alert = e.anim == "alert" and e.alive
        ph = t * 10.0
        swing = math.sin(ph) * 26 if walking else 0.0
        bob = -abs(math.sin(ph)) * 2.2 if walking else math.sin(t * 2.4) * 0.6
        hop = 0.0
        if alert:
            prog = 1.0 - max(0.0, min(1.0, e.memory.get("alert", 0.0) / 0.45))
            hop = -9 * math.sin(prog * math.pi)
        tilt = math.sin(ph) * 3 if walking else 0.0
        out = [self.cmd("halo", root.child(0, -30), alpha=self.pulse(t, 6, 0.55, 0.85) if not alert else 1.0, scale=1.25 if alert else 1.0)]
        out.append(self.cmd("leg", root.child(-9, -11 + (hop * 0.4 if alert else 0), swing)))
        out.append(self.cmd("leg", root.child(10, -11 + (hop * 0.4 if alert else 0), -swing)))
        body = root.child(0, -8 + bob + hop, tilt)
        flick = math.sin(t * 17) * 0.08 + math.sin(t * 29) * 0.05
        lean = -12 if walking else (6 * math.sin(t * 3))
        if e.alive:
            flame_scale = 1.45 if alert else 1.0
            out.append(self.cmd("flame", body.child(-3, -40, lean + math.sin(t * 9) * 5),
                                scale=flame_scale * (1 + flick)))
        else:
            out.append(self.cmd("flame", body.child(-3, -40, 0), scale=0.45, alpha=0.6))
        out.append(self.cmd("body", body))
        if e.alive:
            closed = self.blink(t, e.origin_x) and not alert
            wide = 1.25 if alert else 1.0
            look = 1.0 if not alert else 1.6
            for ex, ey in ((9.0, -24.0), (19.0, -23.5)):
                eye = body.child(ex, ey)
                out.append(self.cmd("eye", eye, scale=wide if not closed else 0.0001))
                out.append(self.cmd("pupil", eye.child(look, 0.6 if not alert else -0.4), scale=wide))
            out.append(self.cmd("brow", body.child(8.5, -31.5 - (2.5 if alert else 0), 10 if not alert else -14)))
            out.append(self.cmd("brow", body.child(19.5, -31 - (2.5 if alert else 0), 18 if not alert else -6)))
        return self.finish(e, t, out)


# =========================================================================== Ermitão-de-Basalto
@register("basalt_turtle")
class BasaltHermit(_VolcanicRig):
    """Ermitão-de-Basalto: a magma hermit crab inside a chunk of porous basalt.

    The rig id stays ``basalt_turtle`` (species tartaruga_basalto) until the
    data ids are renamed; the creature drawn is an original hermit crab."""

    glow_parts = ("halo", "rock_glow", "streak", "spark")
    CRAB, CRAB_DARK, CRAB_HI = "#d8603a", "#8a2c1c", "#ffa070"

    def _rock(self) -> Svg:
        s = Svg(66, 52)
        outline = [(4, 39), (5, 24), (12, 12), (25, 5), (41, 5), (54, 12), (62, 25), (62, 38), (55, 46), (38, 49.5), (18, 48.5), (8, 46)]
        s.path(smooth_closed(outline, 0.85), fill=s.radial(22, 15, 52, [(0, "#74606a"), (0.42, "#43333b"), (1, "#1a1015")]), stroke=INK, width=2.0)
        # crust cap and facets
        s.path(smooth_open([(10, 17), (22, 8.5), (38, 7.5), (52, 13)]), stroke="#a4909a", width=1.6, opacity=0.75)
        s.path("M14 20 Q26 15 34 19 L30 27 Q20 25 14 20 Z", fill="#5a4852", opacity=0.6)
        # vesicles (gas pores) with lit lower lips
        for px, py, pr in ((19, 21, 2.6), (28, 14, 1.8), (39, 18, 2.2), (47, 27, 1.7), (14, 33, 2.0), (25, 37, 1.5), (35, 30, 2.8),
                           (52, 20, 1.4), (9, 28, 1.3), (42, 39, 1.6)):
            s.ellipse(px, py, pr, pr * 0.78, fill="#0e080b")
            s.path(f"M{px - pr * 0.9:.2f} {py + pr * 0.3:.2f} Q{px:.2f} {py + pr * 1.3:.2f} {px + pr * 0.9:.2f} {py + pr * 0.3:.2f}",
                   stroke="#8a7680", width=0.7, opacity=0.8)
        # glowing cracks
        _glow_line(s, "M22 6.5 L25 14 L21 21 L26 28", 0.85)
        _glow_line(s, "M41 6 L39 12 L44 17", 0.7)
        _glow_line(s, "M6 36 L13 38 L16 45", 0.7, False)
        # the dwelling's opening faces forward (right)
        s.ellipse(52, 40, 9, 6.5, fill=s.radial(50, 41, 9, [(0, "#5a1a10"), (0.6, "#1a0a0c"), (1, "#0a0507")]), stroke=INK, width=1.4)
        s.path("M44 37 Q52 33 60 37", stroke="#9a8690", width=1.0, opacity=0.6)
        return s

    def parts(self):
        crab, crab_dark, crab_hi = self.CRAB, self.CRAB_DARK, self.CRAB_HI

        def leg():
            s = Svg(18, 24)
            d = "M5 2 L12 9 L7 21.5"
            s.path(d, stroke=INK, width=5.4)
            s.path(d, stroke=crab_dark, width=3.8)
            s.path("M5 2 L12 9", stroke=crab, width=3.0)
            s.path("M5.6 2.6 L11 7.6", stroke=crab_hi, width=0.9, opacity=0.8)
            s.circle(12, 9, 2.1, fill=MAGMA_ORANGE, stroke=INK, width=0.8)
            s.polygon([(5.8, 20), (6.6, 23.6), (8.6, 20.6)], fill="#3a1410", stroke=INK, width=0.6)
            return s

        def claw():
            s = Svg(24, 18)
            s.path("M2 9 L9 9", stroke=INK, width=5.2)
            s.path("M2 9 L9 9", stroke=crab_dark, width=3.6)
            s.path("M8 4 Q16 0 22 5 Q20 9 13 9 L8 10 Z", fill=s.linear(0, 1, 0, 10, [(0, crab_hi), (0.5, crab), (1, crab_dark)]), stroke=INK, width=1.2)
            s.path("M8 10.5 Q15 11 20 13.5 Q15 16 9 14 Z", fill=s.linear(0, 10, 0, 15, [(0, crab), (1, crab_dark)]), stroke=INK, width=1.1)
            s.path("M11 4.4 Q15 2.4 19 4.6", stroke="#ffffff", width=0.9, opacity=0.55)
            s.circle(8, 9.6, 1.6, fill=MAGMA_ORANGE)
            return s

        def stalk():
            s = Svg(12, 26)
            s.path("M5 25 Q4 16 6 8", stroke=INK, width=3.6)
            s.path("M5 25 Q4 16 6 8", stroke=crab, width=2.0)
            s.circle(6, 6, 4.8, fill=s.radial(5, 4.8, 5.6, [(0, "#ffffff"), (1, "#e8e0d6")]), stroke=INK, width=1.1)
            s.circle(7.6, 6.2, 2.3, fill="#1e0c10")
            s.circle(8.3, 5.3, 0.7, fill="#ffffff")
            return s

        def face():
            s = Svg(22, 16)
            s.path(blob(10, 9, 9, 6.2, 0.04, seed=4), fill=s.radial(8, 6, 11, [(0, crab_hi), (0.5, crab), (1, crab_dark)]), stroke=INK, width=1.3)
            s.path("M12 11 Q15 12.6 17.6 10.6", stroke=INK, width=1.0)
            s.path("M15.5 11.4 L16.2 13.6 L17 11.2", fill="#ffffff", stroke=INK, width=0.4)
            return s

        def streak():
            s = Svg(60, 22)
            s.path("M60 6 Q30 2 0 11 Q30 20 60 16 Z", fill=s.linear(0, 0, 60, 0, [(0, MAGMA_ORANGE, 0), (1, MAGMA_ORANGE, 0.75)]))
            s.path("M60 9 Q34 8 8 11 Q34 14 60 13 Z", fill=s.linear(0, 0, 60, 0, [(0, MAGMA_YELLOW, 0), (1, MAGMA_WHITE, 0.9)]))
            return s

        def spark():
            s = Svg(8, 8)
            s.circle(4, 4, 3.8, fill=s.radial(4, 4, 4, [(0, MAGMA_WHITE), (0.4, MAGMA_YELLOW, 0.9), (1, MAGMA_ORANGE, 0)]))
            return s

        return {
            "halo": (lambda: _halo(90, 70, MAGMA_ORANGE, 0.4), (45, 35)),
            "rock_glow": (lambda: _halo(80, 64, MAGMA_ORANGE, 0.5), (40, 32)),
            "rock": (self._rock, (33, 49)),
            "rock_c": (self._rock, (33, 27)),  # same art pivoting on its centre, for rolling
            "leg": (leg, (5, 2)),
            "claw": (claw, (2, 9)),
            "stalk": (stalk, (5, 25)),
            "face": (face, (4, 9)),
            "streak": (streak, (58, 11)),
            "spark": (spark, (4, 4)),
        }

    def commands(self, e, t):
        root = Xf()
        if not e.alive:
            root = self.defeat_xf(e, root)
        state = e.anim
        hiding = state in ("shell", "slide", "wake") if e.alive else e.state in ("shell", "slide")
        out: list[DrawCommand] = []
        if hiding and state == "slide" and e.alive:
            spin = (t * 820) % 360
            hop = -abs(math.sin(t * 22)) * 1.5
            out.append(self.cmd("streak", root.child(-14, -24), alpha=0.85))
            for k in range(3):
                life = (t * 3.0 + k / 3) % 1.0
                out.append(self.cmd("spark", root.child(-14 - life * 40, -6 - life * 14 - k * 5), alpha=1 - life, scale=1.3 - life))
            out.append(self.cmd("rock_c", Xf(root.x, root.y - 26 + hop, spin)))
            return self.finish(e, t, out)
        if hiding:
            shake = math.sin(t * 42) * 4.0 if state == "wake" else 0.0
            out.append(self.cmd("rock_glow", root.child(0, -24), alpha=self.pulse(t, 2.2, 0.25, 0.5)))
            if state == "wake":
                peek = 0.75 + 0.15 * math.sin(t * 9)
                rock = root.child(0, -1, shake)
                out.append(self.cmd("rock", rock))
                for sx, sa in ((17.0, -16.0), (22.0, 8.0)):
                    out.append(self.cmd("stalk", rock.child(sx, -6, sa + shake * 2), scale=peek))
                out.append(self.cmd("claw", rock.child(24, -3, 20 + math.sin(t * 14) * 12), scale=0.7))
            else:
                out.append(self.cmd("rock", root.child(0, -1)))
            return self.finish(e, t, out)
        # walking crab carrying its rock: legs fan out from under the rock,
        # face, eye stalks and claws come out of the opening in front
        walking = e.alive and state == "walk"
        ph = t * 11.0
        bob = -abs(math.sin(ph)) * 1.6 if walking else 0.0
        tilt = math.sin(ph) * 2.5 if walking else 0.0
        far_tint = (150, 110, 110)
        rock = root.child(-3, -15 + bob, tilt)
        for i, (lx, fan) in enumerate(((-10.0, 30.0), (-1.0, 12.0), (8.0, -8.0))):
            sw = math.sin(ph + i * 2.1 + 1.0) * 14 if walking else 0.0
            out.append(self.cmd("leg", root.child(lx + 3, -20 + bob, fan + sw), tint=far_tint))
        out.append(self.cmd("claw", rock.child(22, -12, 10 + (math.sin(t * 6) * 10 if walking else 0)), tint=far_tint, scale=0.85))
        out.append(self.cmd("rock", rock))
        for sx, sa in ((17.0, -18.0), (22.0, 6.0)):
            out.append(self.cmd("stalk", rock.child(sx, -10, sa + math.sin(t * 3 + sx) * 6)))
        out.append(self.cmd("face", rock.child(18, -6)))
        for i, (lx, fan) in enumerate(((-13.0, 34.0), (-4.0, 14.0), (5.0, -6.0), (13.0, -24.0))):
            sw = math.sin(ph + i * 2.1) * 16 if walking else 0.0
            out.append(self.cmd("leg", root.child(lx, -19 + bob, fan - sw)))
        out.append(self.cmd("claw", rock.child(25, -5, 4 + (math.sin(t * 6 + 1.4) * 12 if walking else 0))))
        return self.finish(e, t, out)


# =========================================================================== Morcego-Brasa
@register("bat")
class EmberBat(_VolcanicRig):
    """Charcoal bat with ember-lit wing membranes (3/4 front view)."""

    def _wing(self, right: bool) -> Svg:
        s = Svg(46, 34)

        def X(x: float) -> float:
            return x if right else 46 - x

        sh = (X(3), 9)
        tips = [(X(44), 3), (X(39), 19), (X(27), 29), (X(12), 27)]
        edge = [sh, tips[0]]
        for a, b in zip(tips, tips[1:]):
            mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
            edge.append((mx + (X(3) - mx) * 0.22, my + (9 - my) * 0.22))
            edge.append(b)
        edge.append((X(4), 18))
        d = "M" + " L".join(f"{px:.2f} {py:.2f}" for px, py in edge[:2])
        for i in range(2, len(edge) - 1, 2):
            (cx_, cy_), (bx, by) = edge[i], edge[i + 1]
            d += f" Q{cx_:.2f} {cy_:.2f} {bx:.2f} {by:.2f}"
        d += f" L{edge[-1][0]:.2f} {edge[-1][1]:.2f} Z"
        s.path(d, fill=s.radial(sh[0], sh[1], 46, [(0, "#2a121d"), (0.45, "#6a2626"), (0.78, MAGMA_ORANGE), (1, MAGMA_YELLOW)]),
               stroke=INK, width=1.3)
        for tx, ty in tips:
            s.path(f"M{sh[0]:.2f} {sh[1]:.2f} L{tx:.2f} {ty:.2f}", stroke="#1e0c14", width=1.6)
        s.path(f"M{sh[0]:.2f} {sh[1] - 0.5:.2f} L{tips[0][0]:.2f} {tips[0][1]:.2f}", stroke="#4a2a34", width=2.6)
        s.polygon([(tips[0][0], tips[0][1]), (X(46), 0.5), (X(41.5), 3.5)], fill=COAL_DEEP, stroke=INK, width=0.6)
        return s

    def parts(self):
        def body():
            s = Svg(38, 38)
            # ears with ember-lit insides
            for ex in (11, 25):
                s.polygon([(ex - 5, 12), (ex - 1, 1), (ex + 5, 11)], fill=COAL, stroke=INK, width=1.2)
                s.polygon([(ex - 2.6, 10.5), (ex - 1, 4), (ex + 2.4, 10)], fill=MAGMA_ORANGE, opacity=0.9)
            s.path(blob(18, 21, 13.5, 13, 0.06, seed=5), fill=s.radial(14, 15, 20, [(0, "#5a4650"), (0.5, "#33222b"), (1, "#170c12")]),
                   stroke=INK, width=1.6)
            s.path(smooth_open([(7, 26), (12, 32.5), (19, 34.6), (27, 32), (31, 25)]), stroke="#e0643c", width=1.8, opacity=0.85)
            s.path(blob(19, 26, 8, 7.5, 0.05, seed=2), fill=s.radial(19, 27, 9, [(0, "#a8483a"), (1, "#4a2028")]))
            s.circle(19, 27, 2.2, fill=MAGMA_YELLOW, opacity=0.9)
            # fur tufts
            for fx, fy in ((8, 18), (10, 27), (28, 16)):
                s.path(f"M{fx} {fy} l-2 2 l2.6 0.4", stroke="#140a10", width=0.9)
            # face looks toward the facing side (right)
            for ex in (20.5, 27.5):
                s.ellipse(ex, 17.5, 3.0, 3.4, fill=s.radial(ex - 0.6, 16.6, 3.6, [(0, "#ffffff"), (0.5, MAGMA_YELLOW), (1, MAGMA_ORANGE)]),
                          stroke=INK, width=0.9)
                s.ellipse(ex + 0.6, 17.8, 0.9, 2.2, fill="#2a0806")
            s.path("M21 23.5 Q24.5 25.5 28.5 23", stroke=INK, width=1.1)
            s.polygon([(22.5, 24.2), (23.4, 27), (24.4, 24.6)], fill="#ffffff", stroke=INK, width=0.4)
            s.polygon([(26.2, 24.4), (27, 26.8), (27.9, 24)], fill="#ffffff", stroke=INK, width=0.4)
            return s

        def feet():
            s = Svg(16, 8)
            for fx in (4, 12):
                s.path(f"M{fx} 0 L{fx} 4 M{fx} 4 l-2 3 M{fx} 4 l2 3", stroke=INK, width=1.4)
            return s

        return {
            "halo": (lambda: _halo(110, 76, MAGMA_ORANGE, 0.62), (55, 38)),
            "body": (body, (19, 22)),
            "wing_r": (lambda: self._wing(True), (3, 9)),
            "wing_l": (lambda: self._wing(False), (43, 9)),
            "feet": (feet, (8, 0)),
        }

    def commands(self, e, t):
        root = Xf()
        if not e.alive:
            root = self.defeat_xf(e, root)
        flying = e.alive
        flap = math.sin(t * 15.0) if flying else -0.6
        down = (flap + 1) / 2  # 0 = wings up, 1 = wings down
        bob = (0.5 - down) * 4.0 if flying else 0.0
        body = root.child(0, -24 + bob, math.sin(t * 2.2) * 4 if flying else 0.0)
        ang = _lerp(-52, 32, down)
        squash = 0.55 + 0.45 * (1 - abs(flap)) if flying else 0.7
        out = [self.cmd("halo", root.child(0, -24 + bob), alpha=self.pulse(t, 5, 0.5, 0.8))]
        # far (left) wing first, then body, then near (right) wing
        out.append(self.cmd("wing_l", Xf(*_xy(body.child(-7, -2)), -ang, 1, squash)))
        out.append(self.cmd("feet", body.child(0, 11, math.sin(t * 4) * 8)))
        out.append(self.cmd("body", body))
        out.append(self.cmd("wing_r", Xf(*_xy(body.child(7, -2)), ang, 1, squash)))
        return self.finish(e, t, out)


def _xy(xf: Xf) -> tuple[float, float]:
    return xf.x, xf.y


# =========================================================================== Boca-de-Fornalha
@register("furnace_mouth")
class FurnaceMouth(_VolcanicRig):
    """Stone gargoyle furnace: the maw brightens while it draws breath, blazes on fire."""

    glow_parts = ("halo", "maw", "eye", "smoke")

    def parts(self):
        def base():
            s = Svg(66, 32)
            s.polygon([(6, 31.5), (10, 9), (56, 9), (60, 31.5)], fill=s.linear(0, 9, 0, 32, [(0, STONE), (1, STONE_DARK)]), stroke=INK, width=1.6)
            for y in (16, 24):
                s.line(8.5, y, 57.5, y, "#241a20", 1.1, 0.8)
            for x, y in ((20, 9), (40, 9), (30, 16), (14, 24), (48, 16), (36, 24)):
                s.line(x, y + 0.6, x, y + 7.4, "#241a20", 1.1, 0.8)
            # ash grate glowing at the foot
            s.path("M24 31.5 L24 25 Q33 19 42 25 L42 31.5 Z", fill=s.radial(33, 30, 10, [(0, MAGMA_YELLOW), (0.5, MAGMA_ORANGE), (1, "#3a1010")]),
                   stroke=INK, width=1.2)
            for x in (28, 33, 38):
                s.line(x, 24, x, 31.5, IRON_DARK, 1.4)
            s.path(rounded_rect_path(3, 3, 60, 7, 2), fill=s.linear(0, 3, 0, 10, [(0, IRON_HI), (0.5, IRON), (1, IRON_DARK)]), stroke=INK, width=1.3)
            for x in (8, 20, 33, 46, 58):
                s.circle(x, 6.5, 1.2, fill="#ece8f2")
            return s

        def head():
            s = Svg(66, 60)
            # horns sweeping back
            s.path("M16 22 Q8 12 2 4 Q10 7 18 14 Q21 17 22 21 Z", fill=s.linear(0, 4, 0, 22, [(0, "#d8c8b8"), (1, STONE)]), stroke=INK, width=1.3)
            s.path("M30 18 Q28 8 22 1 Q32 4 35 14 Z", fill=s.linear(0, 1, 0, 18, [(0, "#d8c8b8"), (1, STONE)]), stroke=INK, width=1.3)
            skull = [(8, 58), (5, 40), (7, 28), (15, 19), (28, 16), (42, 18), (52, 23), (60, 32), (63, 40), (62, 45), (34, 45), (28, 50), (26, 58)]
            s.path(smooth_closed(skull, 0.55), fill=s.radial(24, 26, 46, [(0, STONE_HI), (0.5, STONE), (1, STONE_DARK)]), stroke=INK, width=1.9)
            # chimney vent on the back of the head
            s.path(rounded_rect_path(9, 20, 8, 12, 1.5), fill=s.linear(9, 0, 17, 0, [(0, IRON_HI), (1, IRON_DARK)]), stroke=INK, width=1.0)
            s.rect(8, 19, 10, 3, fill=IRON_DARK, stroke=INK, width=0.8, rx=1)
            # riveted iron brow band
            s.path("M14 30 Q34 24 58 31 L59 36 Q34 29 13 35 Z", fill=s.linear(0, 24, 0, 36, [(0, IRON_HI), (0.5, IRON), (1, IRON_DARK)]),
                   stroke=INK, width=1.2)
            for x, y in ((20, 31.4), (30, 29.2), (40, 29.4), (50, 31.2)):
                s.circle(x, y, 1.1, fill="#ece8f2")
            # deep eye socket under the brow (the glowing eye is its own part)
            s.path("M38 36 Q45 34 51 37 Q46 41 39 40 Z", fill="#120a0e")
            # snout ridge, nostril, cracks and soot
            s.path("M52 38 Q58 37 61 41", stroke=STONE_DARK, width=1.4)
            s.ellipse(58.5, 40.6, 1.4, 1.0, fill="#0e080b")
            s.path("M20 42 L24 47 L22 52", stroke="#241a20", width=1.0)
            s.path("M10 36 Q16 33 22 35", stroke=STONE_HI, width=1.2, opacity=0.7)
            # upper jaw fangs hanging over the maw
            for x in (38, 45, 52, 58):
                s.polygon([(x - 2.2, 44.6), (x, 50), (x + 2.2, 44.6)], fill="#efe2cc", stroke=INK, width=0.8)
            return s

        def jaw():
            s = Svg(34, 16)
            s.path("M1 3 Q2 12 10 14 L30 12 Q33 9 32 5 L26 6 L4 4 Z", fill=s.linear(0, 3, 0, 14, [(0, STONE), (1, STONE_DARK)]), stroke=INK, width=1.5)
            for x in (12, 19, 26):
                s.polygon([(x - 2, 5.6), (x, 0.6), (x + 2, 5.6)], fill="#efe2cc", stroke=INK, width=0.7)
            s.path("M6 10 Q15 12.5 28 10.5", stroke=STONE_HI, width=1.0, opacity=0.5)
            return s

        def maw():
            s = Svg(40, 28)
            with s.group(transform="translate(20 14) scale(1 0.7)"):
                s.circle(0, 0, 20, fill=s.radial(0, 0, 20, [(0, MAGMA_WHITE), (0.3, MAGMA_YELLOW), (0.62, MAGMA_ORANGE), (0.85, MAGMA_RED, 0.8),
                                                            (1, MAGMA_RED, 0)]))
            return s

        def eye():
            s = Svg(14, 8)
            s.path("M1 4.6 Q7 0.8 13 3.6 Q8 7.2 1 4.6 Z", fill=s.radial(7, 4, 6.5, [(0, MAGMA_WHITE), (0.5, MAGMA_YELLOW), (1, MAGMA_ORANGE)]))
            return s

        def smoke():
            s = Svg(22, 22)
            s.circle(11, 11, 10.5, fill=s.radial(9, 9, 11, [(0, "#9a8a96", 0.7), (0.6, "#6a5864", 0.45), (1, "#6a5864", 0)]))
            return s

        return {
            "halo": (lambda: _halo(96, 84, MAGMA_ORANGE, 0.75), (48, 42)),
            "base": (base, (33, 31.5)),
            "head": (head, (30, 58)),
            "jaw": (jaw, (2, 4)),
            "maw": (maw, (20, 14)),
            "eye": (eye, (7, 4)),
            "smoke": (smoke, (11, 11)),
        }

    def _intensity(self, e, t: float) -> tuple[float, float]:
        """(glow 0..1, phase progress) for the current state."""
        if e.anim == "charge":
            interval = float(e.params.get("interval", 2.2))
            remaining = interval - (e.timer % interval)
            prog = 1.0 - max(0.0, min(1.0, remaining / 0.45))
            return 0.5 + 0.5 * prog, prog
        if e.anim == "fire":
            prog = 1.0 - max(0.0, min(1.0, e.memory.get("fired", 0.0) / 0.25))
            return 1.0, prog
        return 0.42 + 0.12 * math.sin(t * 3.0), 0.0

    def commands(self, e, t):
        root = Xf()
        if not e.alive:
            root = self.defeat_xf(e, root)
        glow, prog = self._intensity(e, t) if e.alive else (0.0, 0.0)
        state = e.anim if e.alive else "defeat"
        lean, jaw_open, shake = 0.0, 5.0, 0.0
        if state == "charge":
            lean = -7 * prog
            jaw_open = 5 + 9 * prog
            shake = math.sin(t * 70) * 1.2 * prog
        elif state == "fire":
            lean = 9 * (1 - prog)
            jaw_open = 34 * (1 - prog) + 8 * prog
        out = []
        for k in range(3):  # chimney smoke
            life = (t * 0.6 + k / 3) % 1.0
            out.append(self.cmd("smoke", root.child(-17 - life * 10, -66 - life * 30), alpha=(1 - life) * 0.8 * (1.0 if e.alive else 0.0),
                                scale=0.5 + life * 1.1))
        out.append(self.cmd("base", root))
        head = root.child(shake, -26, lean)
        head = Xf(head.x, head.y, head.angle, head.sx * 0.84, head.sy * 0.84)
        if glow > 0:
            out.append(self.cmd("halo", head.child(18, -14), alpha=min(1.0, glow * 0.9), scale=0.7 + 0.6 * glow))
            out.append(self.cmd("maw", head.child(17, -10), alpha=min(1.0, 0.35 + glow * 0.75), scale=0.75 + 0.45 * glow))
        out.append(self.cmd("jaw", head.child(3, -13, jaw_open)))
        out.append(self.cmd("head", head))
        if e.alive:
            out.append(self.cmd("eye", head.child(15, -20), alpha=min(1.0, 0.45 + glow * 0.7), scale=0.9 + 0.3 * glow))
        return self.finish(e, t, out)


# =========================================================================== Golem de Basalto
@register("golem")
class BasaltGolem(_VolcanicRig):
    """Basalt columns bound by iron around a furnace core; cracks after one hit."""

    glow_parts = ("halo", "core_glow")

    def _torso(self, cracked: bool) -> Svg:
        s = Svg(70, 54)
        outline = [(6, 52), (3, 30), (8, 12), (20, 5), (35, 3), (50, 5), (62, 12), (67, 30), (64, 52)]
        s.path(smooth_closed(outline, 0.5), fill=s.linear(0, 3, 0, 54, [(0, "#4e3c46"), (0.5, COAL), (1, COAL_DEEP)]), stroke=INK, width=2.1)
        # vertical hexagonal column plates
        for i, (x0, x1) in enumerate(((7, 18), (18, 29), (41, 52), (52, 63))):
            s.polygon([(x0 + 0.8, 8 + abs(i - 1.5) * 2), (x1 - 0.8, 7 + abs(i - 1.5) * 2), (x1 - 0.5, 49), (x0 + 0.5, 49)],
                      fill=s.linear(x0, 0, x1, 0, [(0, "#5a4852"), (0.35, "#3e3038"), (1, "#1c1218")]), stroke="#120a0e", width=1.0)
            s.line(x0 + 3, 12 + abs(i - 1.5) * 2, x0 + 3, 46, "#7a6872", 0.8, 0.6)
        # crust caps on the shoulders
        for cx in (13, 57):
            s.path(f"M{cx - 11} 13 Q{cx} 4 {cx + 11} 13 L{cx + 10} 17 Q{cx} 11 {cx - 10} 17 Z",
                   fill=s.linear(0, 5, 0, 17, [(0, "#c9a491"), (0.5, "#94776c"), (1, "#6b5452")]), stroke=INK, width=1.1)
        # iron bands binding the columns
        s.path(rounded_rect_path(4, 38, 62, 6, 2), fill=s.linear(0, 38, 0, 44, [(0, IRON_HI), (0.5, IRON), (1, IRON_DARK)]), stroke=INK, width=1.1)
        for x in (10, 22, 48, 60):
            s.circle(x, 41, 1.1, fill="#ece8f2")
        # furnace core behind an iron grille
        s.circle(35, 25, 12.5, fill=s.radial(35, 25, 12.5, [(0, MAGMA_WHITE), (0.35, MAGMA_YELLOW), (0.75, MAGMA_ORANGE), (1, MAGMA_RED)]),
                 stroke=INK, width=1.6)
        for x in (30, 35, 40):
            s.line(x, 13.5, x, 36.5, IRON_DARK, 1.6)
        s.circle(35, 25, 12.5, fill=None, stroke=IRON, width=2.2)
        _glow_line(s, "M23 26 L18 30 L19 37", 0.7)
        _glow_line(s, "M47 22 L53 19 L55 26", 0.7)
        if cracked:
            _glow_line(s, "M35 4 L31 9 L34 12", 0.9)
            _glow_line(s, "M9 22 L15 26 L12 33 L17 38", 0.9)
            _glow_line(s, "M60 30 L54 33 L57 38", 0.9)
            s.polygon([(52, 7), (62, 12), (63, 22), (56, 20)], fill=MAGMA_ORANGE, stroke=INK, width=1.0)
            s.polygon([(54, 10), (61, 13.5), (61.5, 19.5), (57, 18)], fill=MAGMA_YELLOW, opacity=0.9)
        return s

    def parts(self):
        def head():
            s = Svg(28, 24)
            s.polygon([(3, 22), (2, 9), (7, 3), (21, 3), (26, 9), (25, 22)], fill=s.linear(0, 3, 0, 22, [(0, "#5a4852"), (1, COAL_DARK)]),
                      stroke=INK, width=1.6)
            s.polygon([(7, 3.5), (21, 3.5), (19, 7), (9, 7)], fill="#94776c", stroke=INK, width=0.8)
            s.path(rounded_rect_path(8, 11, 17, 5, 2.4), fill="#120a0e")
            s.path("M10 13.5 L23 13.5", stroke=MAGMA_ORANGE, width=2.6)
            s.path("M10.5 13.5 L22.5 13.5", stroke=MAGMA_WHITE, width=1.0)
            s.path("M5 19 L23 19", stroke="#120a0e", width=1.0, opacity=0.7)
            return s

        def arm():
            s = Svg(26, 48)
            s.path(rounded_rect_path(6, 2, 14, 26, 5), fill=s.linear(6, 0, 20, 0, [(0, "#5a4852"), (1, COAL_DEEP)]), stroke=INK, width=1.5)
            s.path(rounded_rect_path(5, 16, 16, 4, 1.5), fill=IRON, stroke=INK, width=0.9)
            s.path(rounded_rect_path(2, 27, 22, 19, 5), fill=s.radial(9, 31, 20, [(0, "#66545e"), (0.5, COAL), (1, COAL_DEEP)]), stroke=INK, width=1.7)
            s.path("M6 34 L20 34 M7 40 L19 40", stroke="#120a0e", width=1.0, opacity=0.8)
            _glow_line(s, "M13 28 L12 33 L15 37", 0.6)
            return s

        def leg():
            s = Svg(24, 24)
            s.path(rounded_rect_path(4, 1, 16, 17, 3), fill=s.linear(4, 0, 20, 0, [(0, "#4e3c46"), (1, COAL_DEEP)]), stroke=INK, width=1.5)
            s.path(rounded_rect_path(1.5, 15, 21, 8, 3), fill=s.linear(0, 15, 0, 23, [(0, "#5a4852"), (1, COAL_DEEP)]), stroke=INK, width=1.5)
            s.path(rounded_rect_path(3.5, 6, 17, 3.5, 1.2), fill=IRON, stroke=INK, width=0.8)
            return s

        def spikes():
            s = Svg(76, 38)
            for x, hgt, lean in ((9, 22, -16), (22, 30, -8), (38, 36, 0), (54, 30, 8), (67, 22, 16)):
                tip = (x + lean * 0.5, 37 - hgt)
                s.polygon([(x - 7, 37), tip, (x + 7, 37)], fill=s.linear(x - 7, 37 - hgt, x + 7, 37, [(0, "#7a62a0"), (0.4, "#2e2240"), (1, "#0e0914")]),
                          stroke=INK, width=1.4)
                s.polygon([(tip[0] - 2.4, tip[1] + 6.5), tip, (tip[0] + 2.4, tip[1] + 6.5)], fill=s.linear(0, tip[1], 0, tip[1] + 7,
                                                                                                         [(0, MAGMA_WHITE), (1, MAGMA_ORANGE)]))
                s.line(tip[0] - 0.6, tip[1] + 4, x - 3.5, 35, "#c0a8e8", 1.0, 0.6)
            return s

        return {
            "halo": (lambda: _halo(110, 90, MAGMA_ORANGE, 0.35), (55, 45)),
            "core_glow": (lambda: _halo(54, 54, MAGMA_YELLOW, 0.75), (27, 27)),
            "torso": (lambda: self._torso(False), (35, 52)),
            "torso_cracked": (lambda: self._torso(True), (35, 52)),
            "head": (head, (14, 22)),
            "arm": (arm, (13, 6)),
            "leg": (leg, (12, 2)),
            "spikes": (spikes, (38, 36)),
        }

    def commands(self, e, t):
        root = Xf()
        if not e.alive:
            root = self.defeat_xf(e, root)
        state = e.anim
        hurt = e.alive and e.hit_timer > 0
        guard = e.alive and state == "guard"
        walking = e.alive and state in ("walk", "guard") and not hurt
        ph = t * 5.5
        stomp = abs(math.sin(ph))
        bob = -stomp * 2.6 if walking else 0.0
        lean = -11.0 if hurt else (3.0 if walking else 0.0)
        if hurt:
            lean += math.sin(t * 30) * 2
        out = [self.cmd("halo", root.child(0, -36), alpha=0.8)]
        sw = math.sin(ph) * 15 if walking else 0.0
        out.append(self.cmd("leg", root.child(-11, -21, sw), tint=(190, 170, 175)))
        torso = root.child(0, -18 + bob + (2.5 if guard else 0.0), lean)
        far_arm = 24.0 + sw * 0.8
        near_arm = -12.0 - sw * 0.8
        if guard:
            far_arm, near_arm = -18.0, -32.0
        if hurt:
            far_arm, near_arm = 70.0 + math.sin(t * 25) * 8, -50.0
        out.append(self.cmd("arm", torso.child(-27, -40, far_arm), tint=(185, 165, 170)))
        out.append(self.cmd("leg", root.child(11, -21, -sw)))
        cracked = e.health < e.hp or not e.alive
        out.append(self.cmd("torso_cracked" if cracked else "torso", torso))
        core = self.pulse(t, 4.0, 0.55, 0.9) * (0.45 if guard else 1.0) * (1.35 if cracked else 1.0)
        out.append(self.cmd("core_glow", torso.child(0, -27), alpha=min(1.0, core), scale=1.15 if cracked else 1.0))
        if guard:
            out.append(self.cmd("spikes", torso.child(0, -33)))
        out.append(self.cmd("head", torso.child(3, -41 + (3 if guard else 0), -lean * 0.5 + (math.sin(t * 20) * 6 if hurt else 0.0))))
        out.append(self.cmd("arm", torso.child(29, -40, near_arm)))
        return self.finish(e, t, out)


# =========================================================================== Salta-Brasa
@register("magma_bubble")
class EmberSpirit(_VolcanicRig):
    """Salta-Brasa: a little flame-tongue spirit that leaps out of lava."""

    glow_parts = ("halo", "spark")

    def parts(self):
        def body():
            s = Svg(48, 64)
            outline = [(24, 62), (12, 58), (5, 48), (5, 36), (9, 26), (8, 16), (14, 21), (17, 11), (21, 1), (27, 12), (31, 18), (36, 8),
                       (39, 21), (43, 32), (43, 46), (37, 57)]
            s.path(smooth_closed(outline, 0.75), fill=s.radial(24, 48, 40, [(0, MAGMA_YELLOW), (0.45, MAGMA_ORANGE), (0.85, MAGMA_RED), (1, "#9a2214")]),
                   stroke="#6a1610", width=1.6)
            inner = [(24, 58), (15, 54), (11, 45), (12, 35), (16, 28), (19, 31), (22, 18), (26, 27), (30, 24), (33, 33), (37, 42), (35, 53)]
            s.path(smooth_closed(inner, 0.75), fill=s.radial(24, 48, 24, [(0, MAGMA_WHITE), (0.55, MAGMA_YELLOW), (1, MAGMA_ORANGE)]))
            s.path(smooth_open([(11, 44), (12, 34), (16, 27)]), stroke="#ffffff", width=1.4, opacity=0.55)
            # rosy cheeks
            s.ellipse(17, 47, 3, 1.8, fill="#ff6a4a", opacity=0.55)
            s.ellipse(36, 47, 2.6, 1.6, fill="#ff6a4a", opacity=0.55)
            return s

        def eye():
            s = Svg(9, 12)
            s.ellipse(4.5, 6, 3.6, 5.0, fill="#2a0a10", stroke="#6a1610", width=0.8)
            s.circle(5.6, 3.9, 1.3, fill="#ffffff")
            s.circle(3.4, 8.2, 0.6, fill="#ffffff", opacity=0.8)
            return s

        def brow():
            s = Svg(10, 5)
            s.path("M1 1.2 Q5 2.2 9 4", stroke="#6a1610", width=1.8)
            return s

        def mouth():
            s = Svg(10, 8)
            s.path("M1 1.5 Q5 3 9 1.5 Q8 7.4 5 7.4 Q2 7.4 1 1.5 Z", fill="#5a0e10", stroke="#3a0608", width=0.8)
            s.ellipse(5, 5.8, 2.2, 1.3, fill=MAGMA_ORANGE)
            return s

        def drip():
            s = Svg(10, 14)
            s.path("M5 1 Q9 7 8.5 9.5 Q8 13 5 13 Q2 13 1.5 9.5 Q1 7 5 1 Z",
                   fill=s.radial(5, 9, 6, [(0, MAGMA_WHITE), (0.5, MAGMA_YELLOW), (1, MAGMA_ORANGE)]), stroke="#6a1610", width=0.8)
            return s

        def bubble():
            s = Svg(18, 11)
            s.path("M1 10.5 Q1 1 9 1 Q17 1 17 10.5 Z", fill=s.radial(7, 5, 10, [(0, MAGMA_WHITE), (0.4, MAGMA_YELLOW), (1, MAGMA_ORANGE)]),
                   stroke=MAGMA_RED, width=1.0)
            s.path("M4.5 6 Q6 3.2 9 2.8", stroke="#ffffff", width=1.1, opacity=0.8)
            return s

        def spark():
            s = Svg(8, 8)
            s.polygon(star_points(4, 4, 3.8, 1.2, 4), fill=MAGMA_WHITE)
            s.circle(4, 4, 1.4, fill=MAGMA_YELLOW)
            return s

        return {
            "halo": (lambda: _halo(100, 100, MAGMA_ORANGE, 0.7), (50, 50)),
            "body": (body, (24, 62)),
            "eye": (eye, (4.5, 6)),
            "mouth": (mouth, (5, 3)),
            "brow": (brow, (5, 2.5)),
            "drip": (drip, (5, 2)),
            "bubble": (bubble, (9, 10.5)),
            "spark": (spark, (4, 4)),
        }

    def _bubbles(self, t: float, n: int, spread: float, size: float, out: list[DrawCommand], root: Xf) -> None:
        for k in range(n):
            period = 0.55 + 0.17 * k
            life = ((t + k * 0.37) % period) / period
            x = (math.sin(k * 2.7 + math.floor((t + k * 0.37) / period) * 1.3)) * spread
            scale = size * (0.35 + life * 0.85) if life < 0.88 else 0.0001
            out.append(self.cmd("bubble", root.child(x, 1.5), scale=scale))
            if life > 0.88:
                out.append(self.cmd("spark", root.child(x, -6 - (life - 0.88) * 60), scale=0.8, alpha=0.9))

    def commands(self, e, t):
        root = Xf()
        out: list[DrawCommand] = []
        state = e.anim if e.alive else "defeat"
        if state == "submerged":
            out.append(self.cmd("halo", root.child(0, 2), alpha=0.25, scale=0.6))
            self._bubbles(t, 2, 9, 0.75, out, root)
            return self.finish(e, t, out)
        if state == "bubble":
            prog = max(0.0, min(1.0, e.state_time / 0.5))
            out.append(self.cmd("halo", root.child(0, -4), alpha=0.4 + 0.5 * prog, scale=0.7 + 0.4 * prog))
            body = root.child(math.sin(t * 50) * 1.2 * prog, 52 - 20 * prog)
            out.append(self.cmd("body", body, scale=0.9))
            self._bubbles(t, 4, 13, 1.0 + 0.3 * prog, out, root)
            return self.finish(e, t, out)
        if not e.alive:
            root = self.defeat_xf(e, root)
        vy = e.vy if e.alive else 0.0
        rising = state == "jump" or vy < 0
        stretch = 1.0 + min(0.32, abs(vy) / 1800.0)
        sx, sy = 1.0 / math.sqrt(stretch), stretch
        out.append(self.cmd("halo", root.child(0, -28), alpha=self.pulse(t, 9, 0.7, 0.95)))
        for k in range(3):  # molten drips trail behind the motion
            life = (t * 2.6 + k / 3) % 1.0
            if rising:
                out.append(self.cmd("drip", root.child(math.sin(k * 2.1) * 7, 2 + life * 24 + k * 4), scale=(1 - life) * 0.9, alpha=1 - life))
            else:
                out.append(self.cmd("spark", root.child(math.sin(k * 2.1 + 1) * 9, -62 - life * 26 - k * 3), scale=1 - life, alpha=1 - life))
        body = Xf(root.x, root.y, root.angle, sx, sy)
        wobble = math.sin(t * 14) * 4
        body = body.child(0, 0, wobble)
        out.append(self.cmd("body", body))
        if e.alive:
            look = -2.0 if rising else 2.0
            for ex in (-6.0, 6.0):
                out.append(self.cmd("eye", body.child(ex + 3, -24 + look)))
            out.append(self.cmd("brow", body.child(-3, -31 + look, 0)))
            out.append(self.cmd("brow", body.child(9, -31.5 + look, -14)))
            out.append(self.cmd("mouth", body.child(3, -15 + look * 0.5), scale=1.15 if rising else 0.8))
        return self.finish(e, t, out)
