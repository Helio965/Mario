"""Lume, the protagonist: vector parts for the cut-out skeletal rig.

Design units (du): the small form is ~100 du tall; ``DU`` converts du to world
units. Each part is an :class:`Part` with its own SVG and the pivot (joint)
in du. Palettes change with the power-up; the silhouette (wide amber hat,
teal scarf, belt lantern) stays recognisable.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..svg import Svg, blob, mix, shade, smooth_closed, smooth_open

DU = 0.36  # world units per design unit (small form ≈ 34 u tall; hitbox 30 u)
DU_FORM = {"small": 0.36, "big": 0.40}  # big form ≈ 47 u tall (hitbox 46 u)
OUTLINE = "#2b1d2c"


@dataclass(frozen=True)
class Part:
    id: str
    svg: Svg
    pivot: tuple[float, float]  # du, inside the svg


PALETTES = {
    "normal": {
        "tunic": "#2f5d9a", "tunic_dark": "#1f3d6c", "trim": "#f1dfb8", "scarf": "#35c9b4", "scarf_dark": "#1d8f86",
        "glove": "#f3e6cc", "trousers": "#3a3552", "boot": "#6c3f24", "gem": "#ffe07a", "gem_glow": "#fff3b0",
    },
    "fire": {
        "tunic": "#c2412f", "tunic_dark": "#8a2620", "trim": "#f7c64c", "scarf": "#ffb347", "scarf_dark": "#d9772a",
        "glove": "#fff1d6", "trousers": "#4a2b36", "boot": "#5c2b1c", "gem": "#ff9a3c", "gem_glow": "#ffd27a",
    },
}
SKIN, SKIN_SHADE, BLUSH = "#f7cda7", "#e3a27d", "#f2948a"
HAIR, HAIR_LIGHT = "#6d3b2b", "#a35f40"
HAT, HAT_DARK, HAT_LIGHT, BAND = "#e3a33e", "#b5711f", "#f6cc78", "#2aa598"
IRIS, IRIS_DARK, PUPIL = "#2aa5a0", "#0f5c66", "#1a2232"

FORMS = {
    # thigh, shin, torso, head radius
    "small": {"thigh": 13.0, "shin": 15.0, "torso": 23.0, "head": 19.0, "width": 27.0},
    "big": {"thigh": 17.0, "shin": 19.5, "torso": 29.0, "head": 20.0, "width": 30.0},
}


def head() -> Part:
    s = Svg(52, 50)
    cx, cy, r = 25.0, 23.0, 19.0
    # ear (far side shows only a hint), hair back volume
    s.path(blob(cx - 13, cy - 2, 13, 15, 0.05, seed=2), fill=HAIR, stroke=shade(HAIR, -0.35), width=1.6)
    s.ellipse(cx - 15.5, cy + 3, 4.2, 5.2, fill=s.radial(cx - 16, cy + 2, 6, [(0, SKIN), (1, SKIN_SHADE)]),
              stroke=shade(SKIN_SHADE, -0.4), width=1.3)
    face = s.radial(cx + 4, cy - 6, r * 1.35, [(0, "#fff0dc"), (0.45, SKIN), (1, SKIN_SHADE)])
    s.path(smooth_closed([(cx - 17, cy - 4), (cx - 8, cy - 18), (cx + 8, cy - 18.5), (cx + 18.5, cy - 6),
                          (cx + 18, cy + 8), (cx + 9, cy + 17), (cx - 6, cy + 17.5), (cx - 16.5, cy + 9)]),
           fill=face, stroke=shade(SKIN_SHADE, -0.42), width=1.8)
    # soft jaw shadow
    s.path(smooth_open([(cx - 12, cy + 12), (cx, cy + 16.8), (cx + 12, cy + 12.5)]), stroke=SKIN_SHADE, width=2.4, opacity=0.55)
    # blush
    s.ellipse(cx - 6, cy + 8, 4.3, 2.6, fill=s.radial(cx - 6, cy + 8, 4.6, [(0, BLUSH, 0.75), (1, BLUSH, 0)]))
    s.ellipse(cx + 13.5, cy + 7.5, 3.6, 2.3, fill=s.radial(cx + 13.5, cy + 7.5, 4, [(0, BLUSH, 0.7), (1, BLUSH, 0)]))
    # nose (3/4 view, facing right)
    s.path(smooth_open([(cx + 9.6, cy + 1.5), (cx + 12.3, cy + 4.6), (cx + 9.4, cy + 5.6)]), stroke=shade(SKIN_SHADE, -0.25), width=1.5)
    # bangs sweeping toward the face
    bangs = s.linear(cx - 10, cy - 20, cx + 12, cy - 6, [(0, HAIR_LIGHT), (1, HAIR)])
    s.path(smooth_closed([(cx - 16, cy - 8), (cx - 12, cy - 19), (cx + 4, cy - 22), (cx + 17, cy - 13), (cx + 15, cy - 7),
                          (cx + 8, cy - 11), (cx + 3, cy - 6.5), (cx - 2, cy - 11), (cx - 9, cy - 6)]),
           fill=bangs, stroke=shade(HAIR, -0.35), width=1.5)
    s.path(smooth_open([(cx - 6, cy - 15), (cx + 2, cy - 18), (cx + 10, cy - 14)]), stroke=HAIR_LIGHT, width=1.4, opacity=0.8)
    return Part("lume.head", s, (cx - 1, cy + 18))


def hat(palette: str = "normal") -> Part:
    p = PALETTES[palette]
    s = Svg(64, 34)
    # brim (wide ellipse with underside shadow)
    s.ellipse(32, 25, 30, 7.2, fill=s.linear(0, 18, 0, 32, [(0, HAT), (1, HAT_DARK)]), stroke=shade(HAT_DARK, -0.45), width=1.8)
    s.path(smooth_open([(6, 26), (32, 30.5), (58, 26)]), stroke=shade(HAT_DARK, -0.15), width=1.6, opacity=0.7)
    # crown
    crown = s.linear(14, 4, 46, 24, [(0, HAT_LIGHT), (0.55, HAT), (1, HAT_DARK)])
    s.path(smooth_closed([(15, 24), (16, 13), (22, 5), (33, 2.5), (43, 6), (48, 14), (48, 24)]), fill=crown,
           stroke=shade(HAT_DARK, -0.45), width=1.8)
    # dent and band
    s.path(smooth_open([(24, 6), (31, 9), (38, 6)]), stroke=HAT_DARK, width=1.4, opacity=0.6)
    s.path(f"M15.6 19.5 Q32 23.5 48 19.5 L48 24.5 Q32 28 15.6 24.5 Z", fill=s.linear(0, 19, 0, 26, [(0, shade(BAND, 0.2)), (1, shade(BAND, -0.2))]),
           stroke=shade(BAND, -0.5), width=1.2)
    # glowing gem (the "lume")
    s.circle(44, 21.5, 6.5, fill=s.radial(44, 21.5, 6.5, [(0, p["gem_glow"], 0.9), (1, p["gem_glow"], 0)]))
    s.path(smooth_closed([(44, 17), (47.4, 21.5), (44, 26), (40.6, 21.5)]), fill=s.radial(43, 20.5, 4.5, [(0, "#ffffff"), (0.4, p["gem"]), (1, shade(p["gem"], -0.3))]),
           stroke=shade(p["gem"], -0.55), width=1)
    s.path("M41 8 Q35 6 30 9", stroke="#ffffff", width=1.6, opacity=0.45)
    return Part(f"lume.hat.{palette}", s, (31, 24))


def eye(kind: str) -> Part:
    """Sclera/closed shapes; the iris is a separate moving part."""
    s = Svg(12, 14)
    if kind == "open":
        s.ellipse(6, 7, 4.6, 5.8, fill=s.linear(0, 1, 0, 13, [(0, "#ffffff"), (1, "#e7eef5")]), stroke=OUTLINE, width=1.0)
        s.path("M1.4 4.6 Q6 0.2 10.6 4.4", stroke=OUTLINE, width=1.6)  # upper lash line
    elif kind == "blink":
        s.path("M1.2 7.6 Q6 10.4 10.8 7.6", stroke=OUTLINE, width=1.6)
    elif kind == "happy":
        s.path("M1.4 9 Q6 3.2 10.6 9", stroke=OUTLINE, width=1.8)
    elif kind == "wince":
        s.path("M1.6 4.4 L9.6 7.2 L1.6 10", stroke=OUTLINE, width=1.7)
    elif kind == "daze":
        s.path("M6 7 m-3.6 0 a3.6 3.6 0 1 0 7.2 0 a2.6 2.6 0 1 0 -5.2 0 a1.4 1.4 0 1 0 2.8 0", stroke=OUTLINE, width=1.2)
    return Part(f"lume.eye.{kind}", s, (6, 7))


def iris() -> Part:
    s = Svg(8, 9)
    s.ellipse(4, 4.5, 3.0, 3.7, fill=s.radial(4, 3.4, 3.8, [(0, IRIS), (1, IRIS_DARK)]))
    s.ellipse(4, 4.8, 1.6, 2.1, fill=PUPIL)
    s.ellipse(5.1, 3.0, 1.0, 1.15, fill="#ffffff")
    s.circle(3.0, 6.2, 0.45, fill="#ffffff", opacity=0.8)
    return Part("lume.iris", s, (4, 4.5))


def brow() -> Part:
    s = Svg(10, 4)
    s.path("M1.2 2.6 Q5 0.6 8.8 2", stroke=shade(HAIR, -0.2), width=1.9)
    return Part("lume.brow", s, (5, 2))


def mouth(kind: str) -> Part:
    s = Svg(14, 10)
    dark, tongue = "#5a1f2b", "#e8707a"
    if kind == "smile":
        s.path("M2.2 3.6 Q7 8.4 11.6 3.2", stroke=OUTLINE, width=1.5)
    elif kind == "grin":
        s.path("M1.6 2.6 Q7 3.4 12.4 2.2 Q11 9.4 6.6 9.2 Q2.4 9 1.6 2.6 Z", fill=dark, stroke=OUTLINE, width=1.2)
        s.path("M3.6 7 Q6.6 5.4 9.8 7.4 Q8.4 9 6.6 9 Q4.6 9 3.6 7 Z", fill=tongue)
        s.path("M2.4 3 L11.6 2.6 L11.2 4.2 L2.8 4.4 Z", fill="#ffffff")
    elif kind == "open":
        s.ellipse(7, 5.4, 3.2, 3.8, fill=dark, stroke=OUTLINE, width=1.2)
        s.ellipse(7, 7.2, 2.0, 1.4, fill=tongue)
    elif kind == "small_o":
        s.ellipse(7, 5.2, 1.8, 2.2, fill=dark, stroke=OUTLINE, width=1.0)
    elif kind == "determined":
        s.path("M3 5 Q7 6.4 11 4.4", stroke=OUTLINE, width=1.6)
    elif kind == "wince":
        s.path("M2 4.4 L4.6 6.4 L7 4.2 L9.4 6.4 L12 4.4", stroke=OUTLINE, width=1.4)
    elif kind == "sad":
        s.path("M3 7.4 Q7 3.6 11 7.2", stroke=OUTLINE, width=1.5)
    return Part(f"lume.mouth.{kind}", s, (7, 5))


def torso(form: str, palette: str) -> Part:
    f, p = FORMS[form], PALETTES[palette]
    h, w = f["torso"], f["width"]
    s = Svg(w + 8, h + 10)
    cx = (w + 8) / 2
    top, bottom = 3.0, h + 4
    body = s.linear(cx - w / 2, top, cx + w / 2, bottom, [(0, shade(p["tunic"], 0.18)), (0.6, p["tunic"]), (1, p["tunic_dark"])])
    pts = [(cx - w * 0.36, top + 2), (cx + w * 0.34, top + 1.5), (cx + w * 0.5, bottom - 6), (cx + w * 0.46, bottom),
           (cx - w * 0.47, bottom), (cx - w * 0.5, bottom - 6)]
    s.path(smooth_closed(pts, 0.55), fill=body, stroke=shade(p["tunic_dark"], -0.45), width=1.8)
    # hem trim and side shading
    s.path(smooth_open([(cx - w * 0.47, bottom - 2.6), (cx, bottom - 1.2), (cx + w * 0.46, bottom - 2.6)]), stroke=p["trim"], width=2.2)
    s.path(smooth_open([(cx + w * 0.22, top + 4), (cx + w * 0.4, bottom - 8)]), stroke=shade(p["tunic"], 0.35), width=1.6, opacity=0.6)
    # belt and buckle
    by = bottom - h * 0.36
    s.path(f"M{cx - w * 0.5:.2f} {by:.2f} Q{cx:.2f} {by + 2.2:.2f} {cx + w * 0.5:.2f} {by:.2f} L{cx + w * 0.5:.2f} {by + 4.4:.2f} "
           f"Q{cx:.2f} {by + 6.6:.2f} {cx - w * 0.5:.2f} {by + 4.4:.2f} Z", fill="#5b3524", stroke="#2c1913", width=1.1)
    s.rect(cx + 2, by + 0.6, 5.2, 4.6, fill=s.linear(0, by, 0, by + 5, [(0, "#ffe7a1"), (1, "#c9902e")]), stroke="#5c3a12", width=0.9, rx=1)
    # collar
    s.path(smooth_open([(cx - 8, top + 2.4), (cx - 1, top + 6.4), (cx + 7, top + 2.2)]), stroke=p["trim"], width=2.4)
    return Part(f"lume.torso.{form}.{palette}", s, (cx, bottom - 1))


def scarf_wrap(palette: str) -> Part:
    p = PALETTES[palette]
    s = Svg(26, 12)
    s.path(smooth_closed([(2, 5), (8, 2), (18, 1.6), (24.5, 4.4), (23.5, 8.6), (13, 10.6), (3.2, 9)]),
           fill=s.linear(0, 1, 0, 11, [(0, shade(p["scarf"], 0.25)), (1, p["scarf_dark"])]), stroke=shade(p["scarf_dark"], -0.45), width=1.4)
    s.path(smooth_open([(5, 5.6), (13, 6.8), (21, 5.2)]), stroke=shade(p["scarf"], 0.45), width=1.1, opacity=0.7)
    return Part(f"lume.scarf_wrap.{palette}", s, (13, 6))


def scarf_tail(palette: str, index: int) -> Part:
    p = PALETTES[palette]
    length = 15 - index * 2.5
    s = Svg(length + 3, 9)
    tip = length + 1 if index else length - 1
    s.path(smooth_closed([(1, 2.2), (length * 0.6, 1.4), (tip, 3.2 + index), (length * 0.55, 7.2), (1.2, 6.6)], 0.8),
           fill=s.linear(0, 1, 0, 8, [(0, shade(p["scarf"], 0.15)), (1, p["scarf_dark"])]), stroke=shade(p["scarf_dark"], -0.45), width=1.2)
    if index == 1:
        for k in range(3):
            x = length - 1.5 + k * 0.2
            s.line(x, 3.2 + k * 1.4, x + 2.2, 3.6 + k * 1.6, shade(p["scarf"], 0.3), 0.9)
    return Part(f"lume.scarf_tail.{palette}.{index}", s, (1.4, 4.4))


def upper_arm(form: str, palette: str) -> Part:
    p = PALETTES[palette]
    length = 11.0 if form == "small" else 14.0
    s = Svg(10, length + 4)
    s.path(smooth_closed([(2, 2.6), (5, 1), (8.2, 2.6), (7.6, length + 1.4), (5, length + 2.6), (2.4, length + 1.2)], 0.7),
           fill=s.linear(1, 0, 9, 0, [(0, shade(p["tunic"], 0.12)), (1, p["tunic_dark"])]), stroke=shade(p["tunic_dark"], -0.45), width=1.3)
    return Part(f"lume.upper_arm.{form}.{palette}", s, (5, 3))


def forearm(form: str, palette: str) -> Part:
    p = PALETTES[palette]
    length = 10.0 if form == "small" else 13.0
    s = Svg(11, length + 9)
    s.path(smooth_closed([(2.6, 1.6), (5.4, 0.8), (8.2, 1.8), (7.4, length), (3.4, length)], 0.7),
           fill=s.linear(1, 0, 9, 0, [(0, shade(p["tunic"], 0.12)), (1, p["tunic_dark"])]), stroke=shade(p["tunic_dark"], -0.45), width=1.2)
    s.rect(2.4, length - 2.4, 6.4, 2.8, fill=p["trim"], rx=1.2, stroke=shade(p["trim"], -0.5), width=0.8)
    # mitten hand
    s.path(blob(5.6, length + 3.6, 3.7, 3.9, 0.05, seed=1), fill=s.radial(4.8, length + 2.4, 5, [(0, "#ffffff"), (1, p["glove"])]),
           stroke=shade(p["glove"], -0.55), width=1.2)
    s.ellipse(8.2, length + 2.6, 1.4, 1.9, fill=p["glove"], stroke=shade(p["glove"], -0.55), width=0.9)
    return Part(f"lume.forearm.{form}.{palette}", s, (5.4, 2))


def thigh(form: str, palette: str) -> Part:
    p = PALETTES[palette]
    length = FORMS[form]["thigh"]
    s = Svg(12, length + 4)
    s.path(smooth_closed([(1.4, 2), (6, 0.6), (10.6, 2), (9.6, length + 1.6), (6, length + 3), (2.4, length + 1.6)], 0.7),
           fill=s.linear(1, 0, 11, 0, [(0, shade(p["trousers"], 0.18)), (1, shade(p["trousers"], -0.15))]),
           stroke=shade(p["trousers"], -0.5), width=1.3)
    return Part(f"lume.thigh.{form}.{palette}", s, (6, 2.4))


def shin(form: str, palette: str) -> Part:
    p = PALETTES[palette]
    length = FORMS[form]["shin"]
    s = Svg(17, length + 4)
    leg_end = length - 5.5
    s.path(smooth_closed([(3, 1.4), (6.2, 0.6), (9.2, 1.6), (8.6, leg_end), (3.6, leg_end)], 0.7),
           fill=s.linear(2, 0, 10, 0, [(0, shade(p["trousers"], 0.15)), (1, shade(p["trousers"], -0.15))]),
           stroke=shade(p["trousers"], -0.5), width=1.2)
    # boot with rolled cuff, toe pointing forward (+x)
    boot = s.linear(0, leg_end - 3, 0, length + 2, [(0, shade(p["boot"], 0.25)), (1, shade(p["boot"], -0.2))])
    s.path(smooth_closed([(2.2, leg_end - 3), (9.8, leg_end - 3.4), (10.6, length - 3.2), (15.6, length - 1.4), (15.4, length + 1.6),
                          (2.6, length + 1.8), (1.8, length - 3)], 0.55), fill=boot, stroke=shade(p["boot"], -0.55), width=1.3)
    s.path(f"M2.2 {leg_end - 3:.2f} L9.8 {leg_end - 3.4:.2f} L9.9 {leg_end - 0.8:.2f} L2.3 {leg_end - 0.4:.2f} Z", fill=shade(p["boot"], 0.35))
    s.path(smooth_open([(3.4, length + 0.4), (14.6, length + 0.2)]), stroke=shade(p["boot"], -0.5), width=1.0, opacity=0.8)
    return Part(f"lume.shin.{form}.{palette}", s, (6.2, 2))


def lantern(palette: str) -> Part:
    p = PALETTES[palette]
    s = Svg(14, 18)
    s.path("M7 1.2 a2.6 2.6 0 1 1 0.01 0", stroke="#5c3a12", width=1.2)
    s.circle(7, 11, 7, fill=s.radial(7, 11, 7, [(0, p["gem_glow"], 0.8), (1, p["gem_glow"], 0)]))
    s.rect(3.2, 5.4, 7.6, 2.2, fill="#8a5a22", rx=0.8, stroke="#3d2610", width=0.8)
    s.path(smooth_closed([(3.4, 7.6), (10.6, 7.6), (11.2, 12), (10, 15.2), (4, 15.2), (2.8, 12)], 0.6),
           fill=s.radial(7, 11, 5, [(0, "#ffffff"), (0.35, p["gem"]), (1, shade(p["gem"], -0.25))]), stroke="#5c3a12", width=1.0)
    s.rect(4, 15, 6, 1.8, fill="#8a5a22", rx=0.7, stroke="#3d2610", width=0.7)
    return Part(f"lume.lantern.{palette}", s, (7, 1.2))


def all_parts() -> list[Part]:
    parts = [head(), iris(), brow()]
    parts += [eye(k) for k in ("open", "blink", "happy", "wince", "daze")]
    parts += [mouth(k) for k in ("smile", "grin", "open", "small_o", "determined", "wince", "sad")]
    for palette in PALETTES:
        parts += [hat(palette), scarf_wrap(palette), scarf_tail(palette, 0), scarf_tail(palette, 1), lantern(palette)]
        for form in FORMS:
            parts += [torso(form, palette), upper_arm(form, palette), forearm(form, palette), thigh(form, palette), shin(form, palette)]
    return parts
