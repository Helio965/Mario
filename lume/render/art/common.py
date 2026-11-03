"""Art shared by every world: coins, relics, items, projectiles, particles,
checkpoint lantern, goal banner, hint signs and generic hazards.

All sizes are in world units (1 u = 2 px at 1080p, 4 px at 4K before zoom).
"""

from __future__ import annotations

import math

from ..assets import ArtSpec
from ..svg import Svg, blob, rounded_rect_path, shade, smooth_closed, smooth_open, star_points

GOLD, GOLD_DARK, GOLD_LIGHT = "#ffc93c", "#b97a1c", "#fff3b0"
INK = "#2b1d2c"


def coin_frame(i: int, frames: int = 8) -> Svg:
    """Coin rotating around its vertical axis: frame i of ``frames`` (half turn)."""
    s = Svg(22, 26)
    k = abs(math.cos(math.pi * i / frames))
    cx, cy, ry = 11.0, 13.0, 11.0
    rx = max(1.6, 10.0 * k)
    edge = 2.2 * (1 - k) + 0.8
    # edge thickness (darker band) for a solid look while turning
    s.ellipse(cx + edge * 0.6, cy, rx + 0.2, ry, fill=s.linear(cx - rx, 0, cx + rx, 0, [(0, GOLD_DARK), (1, shade(GOLD_DARK, -0.25))]))
    s.ellipse(cx, cy, rx, ry, fill=s.linear(cx - rx, cy - ry, cx + rx, cy + ry, [(0, GOLD_LIGHT), (0.35, GOLD), (1, "#d48a1e")]),
              stroke=shade(GOLD_DARK, -0.35), width=1.0)
    if k > 0.35:
        s.ellipse(cx, cy, rx * 0.72, ry * 0.72, fill=None, stroke=shade(GOLD_DARK, 0.1), width=1.0, opacity=0.8)
        # embossed sun
        for j in range(8):
            a = j * math.pi / 4
            x1, y1 = cx + math.cos(a) * rx * 0.28, cy + math.sin(a) * ry * 0.28
            x2, y2 = cx + math.cos(a) * rx * 0.52, cy + math.sin(a) * ry * 0.52
            s.line(x1, y1, x2, y2, shade(GOLD_DARK, 0.15), 1.1 * k + 0.3, 0.9)
        s.ellipse(cx, cy, rx * 0.2, ry * 0.2, fill=shade(GOLD, 0.2), stroke=shade(GOLD_DARK, 0.1), width=0.8)
        s.path(f"M{cx - rx * 0.55:.2f} {cy - ry * 0.45:.2f} Q{cx - rx * 0.2:.2f} {cy - ry * 0.85:.2f} {cx + rx * 0.25:.2f} {cy - ry * 0.7:.2f}",
               stroke="#ffffff", width=1.3 * k + 0.2, opacity=0.75)
    return s


def relic() -> Svg:
    s = Svg(40, 44)
    s.circle(20, 20, 19, fill=s.radial(20, 20, 19, [(0, "#9ff7e6", 0.55), (1, "#5fe0d0", 0)]))
    pts = [(20, 3), (30, 13), (27, 30), (20, 36), (13, 30), (10, 13)]
    s.polygon(pts, fill=s.linear(10, 3, 30, 36, [(0, "#d9fff7"), (0.4, "#4fd6c8"), (1, "#137a7a")]), stroke="#0b4d55", width=1.2)
    s.polygon([(20, 3), (24, 15), (20, 36), (16, 15)], fill="#ffffff", opacity=0.25)
    s.path("M10 13 L20 18 L30 13 M20 18 L20 36", stroke="#bff7ee", width=0.9, opacity=0.7)
    s.path("M14 34 Q20 41 26 34 L24 38 Q20 42 16 38 Z", fill=s.linear(0, 34, 0, 41, [(0, GOLD_LIGHT), (1, GOLD_DARK)]), stroke=INK, width=0.9)
    s.polygon(star_points(28, 8, 3.4, 0.9, 4), fill="#ffffff", opacity=0.9)
    return s


def item(kind: str) -> Svg:
    s = Svg(28, 28)
    if kind == "grow":  # Fruta-Lume: glowing golden peach
        s.circle(14, 15, 12.5, fill=s.radial(14, 15, 13, [(0, "#fff2c0", 0.6), (1, "#ffd27a", 0)]))
        s.path(blob(14, 16, 9.5, 9, 0.04, seed=3), fill=s.radial(10.5, 12.5, 12, [(0, "#fff0d0"), (0.35, "#ffb35c"), (1, "#e2643f")]),
               stroke="#7a2e22", width=1.2)
        s.path(smooth_open([(14, 8.5), (13.6, 12), (14.2, 16)]), stroke="#c75a3a", width=1.0, opacity=0.6)
        s.path(smooth_closed([(14.6, 7.6), (19, 3.6), (23.5, 4.6), (19.6, 8.6)]), fill=s.linear(15, 4, 23, 8, [(0, "#9be36a"), (1, "#3c9a46")]),
               stroke="#24622d", width=0.9)
        s.line(14, 8.6, 13.4, 4.4, "#6b3f22", 1.4)
        s.ellipse(10.5, 12, 2.6, 1.8, fill="#ffffff", opacity=0.6)
    elif kind == "fire":  # Flor de Brasa
        s.circle(14, 11, 11, fill=s.radial(14, 11, 11, [(0, "#ffe08a", 0.6), (1, "#ff8a3c", 0)]))
        s.path("M14 26 Q13 20 14 15", stroke="#3c8a3c", width=2.0)
        s.path(smooth_closed([(14, 21), (8.4, 18.6), (6.4, 21.6), (10, 23.4)]), fill="#58b04c", stroke="#24622d", width=0.8)
        for k in range(6):
            a = k * math.pi / 3 + 0.3
            px, py = 14 + math.cos(a) * 6.4, 11 + math.sin(a) * 6.4
            s.path(blob(px, py, 4.6, 3.4, 0.0, seed=k), fill=s.radial(14, 11, 10, [(0, "#fff0a0"), (0.45, "#ff9a3c"), (1, "#d63a2a")]),
                   stroke="#7a1e18", width=0.8)
        s.circle(14, 11, 3.6, fill=s.radial(13, 10, 4, [(0, "#ffffff"), (1, "#ffd24a")]), stroke="#a55a16", width=0.7)
    elif kind == "star":  # Estrela-guia (eight-pointed compass star)
        s.circle(14, 14, 13.5, fill=s.radial(14, 14, 14, [(0, "#fffbe0", 0.8), (1, "#ffe48a", 0)]))
        s.polygon(star_points(14, 14, 12.5, 4.2, 8, -90), fill=s.radial(12, 11, 13, [(0, "#ffffff"), (0.4, "#ffe27a"), (1, "#e8a22a")]),
                  stroke="#9a5a10", width=1.0)
        s.polygon(star_points(14, 14, 6.6, 2.6, 4, -45), fill="#ffffff", opacity=0.75)
    else:  # heart crystal
        s.circle(14, 14, 12, fill=s.radial(14, 14, 12, [(0, "#ffd0d6", 0.5), (1, "#ff8a9a", 0)]))
        s.path("M14 24 C 4 17, 3.6 9, 8.8 7.2 C 11.6 6.4, 13.4 8, 14 10 C 14.6 8, 16.4 6.4, 19.2 7.2 C 24.4 9, 24 17, 14 24 Z",
               fill=s.linear(6, 6, 22, 24, [(0, "#ff9aa8"), (0.5, "#ee4a63"), (1, "#a8203c")]), stroke="#5a1024", width=1.1)
        s.path("M9 10 Q10.5 8.6 12.4 9.8", stroke="#ffffff", width=1.4, opacity=0.8)
    return s


def projectile(kind: str) -> Svg:
    s = Svg(24, 24)
    c = 12
    if kind == "fireball":
        s.circle(c, c, 11, fill=s.radial(c, c, 11, [(0, "#fff6c0", 0.9), (0.5, "#ffb03c", 0.6), (1, "#ff6a2a", 0)]))
        s.path(blob(c, c, 6.2, 6.2, 0.12, seed=2), fill=s.radial(c - 1, c - 1, 7, [(0, "#ffffff"), (0.4, "#ffd76a"), (1, "#ff7a2a")]))
    elif kind in ("spine", "seed", "thorn_acorn"):
        color = {"spine": "#8fbf5a", "seed": "#7a5a2a", "thorn_acorn": "#8a5a33"}[kind]
        s.path(blob(c, c, 7, 6, 0.08, seed=4), fill=s.radial(c - 2, c - 2, 9, [(0, shade(color, 0.4)), (1, shade(color, -0.25))]),
               stroke=INK, width=1.1)
        for k in range(6):
            a = k * math.pi / 3
            s.polygon([(c + math.cos(a) * 6, c + math.sin(a) * 5.5), (c + math.cos(a + 0.25) * 10, c + math.sin(a + 0.25) * 9.5),
                       (c + math.cos(a + 0.5) * 6, c + math.sin(a + 0.5) * 5.5)], fill="#f2e6c0", stroke=INK, width=0.7)
    elif kind == "snowball":
        s.circle(c, c, 8, fill=s.radial(c - 3, c - 3, 11, [(0, "#ffffff"), (1, "#bcd8ec")]), stroke="#5a7a9a", width=1.0)
    elif kind == "bolt":
        s.path(rounded_rect_path(2, 6, 20, 12, 6), fill=s.linear(0, 6, 0, 18, [(0, "#9aa8b8"), (1, "#4a5568")]), stroke=INK, width=1.1)
        s.circle(18, 12, 3, fill="#ffd24a")
    else:  # orb, spore, sand, guardian_orb
        color = {"spore": "#c88ad8", "sand": "#e8c07a", "guardian_orb": "#73ffe1"}.get(kind, "#d869af")
        s.circle(c, c, 11, fill=s.radial(c, c, 11, [(0, color, 0.8), (1, color, 0)]))
        s.circle(c, c, 6, fill=s.radial(c - 2, c - 2, 7, [(0, "#ffffff"), (0.5, color), (1, shade(color, -0.4))]))
    return s


def particle(kind: str) -> Svg:
    s = Svg(16, 16)
    if kind == "sparkle":
        s.polygon(star_points(8, 8, 7.5, 1.6, 4), fill="#ffffff")
    elif kind == "leaf":
        s.path(smooth_closed([(2, 8), (8, 3), (14, 6), (9, 12)]), fill=s.linear(2, 3, 14, 12, [(0, "#a6e36a"), (1, "#3f9a46")]),
               stroke="#2a6a2a", width=0.7)
    elif kind == "petal":
        s.path(smooth_closed([(3, 8), (8, 4.5), (13, 8), (8, 11.5)]), fill=s.linear(3, 4, 13, 12, [(0, "#ffe6f0"), (1, "#f59ab8")]))
    elif kind == "debris":
        s.polygon([(3, 5), (10, 2.5), (13.5, 9), (7, 13.5), (2.5, 10)], fill="#9a6a44", stroke="#4a3020", width=0.9)
    else:  # soft (dust, glow, smoke)
        s.circle(8, 8, 7.8, fill=s.radial(8, 8, 8, [(0, "#ffffff", 0.95), (0.5, "#ffffff", 0.5), (1, "#ffffff", 0)]))
    return s


def checkpoint(lit: bool) -> Svg:
    s = Svg(40, 112)
    s.path(rounded_rect_path(16, 18, 7, 92, 2.5), fill=s.linear(16, 0, 23, 0, [(0, "#a8744a"), (1, "#6a4426")]), stroke=INK, width=1.1)
    s.path(rounded_rect_path(9, 104, 21, 7, 2.5), fill="#7a5a3a", stroke=INK, width=1.0)
    s.path("M19.5 18 Q30 14 32 24", stroke="#4a3020", width=2.2)
    glass = [(0, "#ffffff"), (0.4, "#ffe27a"), (1, "#ff9a3c")] if lit else [(0, "#e6eef0"), (1, "#8a9aa2")]
    if lit:
        s.circle(32, 36, 18, fill=s.radial(32, 36, 18, [(0, "#fff3b0", 0.85), (1, "#ffd27a", 0)]))
    s.rect(26, 24, 12, 3, fill="#6a4426", rx=1, stroke=INK, width=0.8)
    s.path(smooth_closed([(26.5, 27), (37.5, 27), (38.5, 38), (36.5, 45), (27.5, 45), (25.5, 38)], 0.5),
           fill=s.radial(32, 35, 9, glass), stroke=INK, width=1.0)
    s.rect(27, 44.5, 10, 2.6, fill="#6a4426", rx=1, stroke=INK, width=0.8)
    if lit:
        s.path(blob(32, 37, 2.6, 4.2, 0.1, seed=1), fill="#ffffff", opacity=0.9)
    return s


def goal(world_color: str = "#35c9b4") -> Svg:
    s = Svg(120, 220)
    # stone arch gateway
    stone = s.linear(0, 80, 0, 220, [(0, "#e2dccb"), (1, "#a59a86")])
    s.path("M50 220 L50 120 Q85 70 120 120 L120 220 L106 220 L106 124 Q85 92 64 124 L64 220 Z", fill=stone, stroke=INK, width=1.6)
    for y in range(130, 220, 18):
        s.line(50, y, 64, y, "#8a806e", 1.0, 0.8)
        s.line(106, y, 120, y, "#8a806e", 1.0, 0.8)
    s.path("M64 220 L64 124 Q85 92 106 124 L106 220 Z", fill=s.linear(0, 100, 0, 220, [(0, "#3a5a6a"), (1, "#22323c")]))
    s.circle(85, 150, 22, fill=s.radial(85, 150, 22, [(0, "#fff3b0", 0.55), (1, "#fff3b0", 0)]))
    # pole and banner
    s.path(rounded_rect_path(18, 12, 6, 208, 3), fill=s.linear(18, 0, 24, 0, [(0, "#ffffff"), (1, "#b9c2c6")]), stroke=INK, width=1.1)
    s.circle(21, 10, 6, fill=s.radial(19.5, 8.5, 6, [(0, GOLD_LIGHT), (1, GOLD_DARK)]), stroke=INK, width=1.0)
    s.path("M24 18 Q46 14 62 20 Q54 30 62 42 Q44 38 24 44 Z", fill=s.linear(24, 14, 62, 44, [(0, shade(world_color, 0.25)), (1, shade(world_color, -0.25))]),
           stroke=INK, width=1.2)
    s.circle(40, 30, 6.5, fill=s.radial(39, 29, 7, [(0, GOLD_LIGHT), (1, GOLD)]), stroke=shade(GOLD_DARK, -0.2), width=0.9)
    for j in range(8):
        a = j * math.pi / 4
        s.line(40 + math.cos(a) * 7.5, 30 + math.sin(a) * 7.5, 40 + math.cos(a) * 10, 30 + math.sin(a) * 10, GOLD_LIGHT, 1.3)
    s.path(rounded_rect_path(8, 212, 28, 8, 3), fill="#7a6a5a", stroke=INK, width=1.0)
    return s


def sign() -> Svg:
    s = Svg(40, 48)
    s.path(rounded_rect_path(17, 18, 6, 30, 2), fill=s.linear(17, 0, 23, 0, [(0, "#a8744a"), (1, "#6a4426")]), stroke=INK, width=1.0)
    s.path(rounded_rect_path(3, 3, 34, 22, 4), fill=s.linear(0, 3, 0, 25, [(0, "#f1d49a"), (1, "#c79a5c")]), stroke=INK, width=1.2)
    s.path(rounded_rect_path(6, 6, 28, 16, 3), fill=None, stroke="#a0763e", width=0.9)
    s.path("M20 8 L20 16", stroke="#3a5a8a", width=3.0)
    s.circle(20, 19.6, 1.6, fill="#3a5a8a")
    return s


def spikes(width: float) -> Svg:
    n = max(1, round(width / 12))
    s = Svg(width, 16)
    s.rect(0, 11, width, 5, fill=s.linear(0, 11, 0, 16, [(0, "#8a96a2"), (1, "#4a5562")]), stroke=INK, width=0.9, rx=1.5)
    step = width / n
    for i in range(n):
        x = i * step
        s.polygon([(x + 0.6, 12), (x + step / 2, 0.8), (x + step - 0.6, 12)],
                  fill=s.linear(x, 0, x + step, 0, [(0, "#f2f5f7"), (0.5, "#b8c2cc"), (1, "#6a7682")]), stroke=INK, width=0.9)
    return s


def flame_orb() -> Svg:
    s = Svg(40, 40)
    s.circle(20, 20, 19, fill=s.radial(20, 20, 19, [(0, "#ffe38a", 0.8), (0.5, "#ff8a3c", 0.45), (1, "#ff5a2a", 0)]))
    for k in range(7):
        a = k * 2 * math.pi / 7
        s.path(blob(20 + math.cos(a) * 7, 20 + math.sin(a) * 7, 6, 4, 0.1, seed=k),
               fill=s.radial(20, 20, 14, [(0, "#fff0a0"), (0.6, "#ff9a3c"), (1, "#d63a2a")]), opacity=0.9)
    s.circle(20, 20, 7, fill=s.radial(18, 18, 8, [(0, "#ffffff"), (1, "#ffd24a")]))
    return s


def liquid_surface(kind: str, width: float = 64) -> Svg:
    """Tileable animated surface strip (scrolls horizontally)."""
    s = Svg(width, 14)
    if kind == "lava":
        top, mid, glow = "#ffe08a", "#ff8a3c", "#ff5a2a"
    elif kind == "poison":
        top, mid, glow = "#d8f7a0", "#7ac85a", "#3f8a3a"
    else:
        top, mid, glow = "#e6fbff", "#7fd4ea", "#3aa8c8"
    pts = []
    for i in range(9):
        x = width * i / 8
        pts.append((x, 4 + 2.4 * math.sin(i / 8 * 2 * math.pi * 2)))
    d = smooth_open(pts) + f"L{width} 14 L0 14 Z"
    s.path(d, fill=s.linear(0, 1, 0, 14, [(0, top), (0.35, mid), (1, glow)]))
    s.path(smooth_open(pts), stroke="#ffffff", width=1.2, opacity=0.8 if kind != "lava" else 0.5)
    return s


def liquid_body(kind: str) -> Svg:
    s = Svg(32, 64)
    stops = {
        "lava": [(0, "#ff7a2a"), (0.5, "#d43a22"), (1, "#7a1a12")],
        "poison": [(0, "#5aa84a"), (1, "#1e4a2a")],
    }.get(kind, [(0, "#3aa8c8"), (0.6, "#1f7aa0"), (1, "#0f4060")])
    s.rect(0, 0, 32, 64, fill=s.linear(0, 0, 0, 64, stops))
    return s


def specs() -> list[ArtSpec]:
    out = [ArtSpec(f"coin.{i}", (lambda i=i: coin_frame(i)), 1.0, (11, 13), "common") for i in range(8)]
    out.append(ArtSpec("relic", relic, 1.0, (20, 22), "common"))
    for kind in ("grow", "fire", "star", "heart"):
        out.append(ArtSpec(f"item.{kind}", (lambda k=kind: item(k)), 1.0, (14, 14), "common"))
    for kind in ("fireball", "spine", "seed", "thorn_acorn", "snowball", "bolt", "orb", "spore", "sand", "guardian_orb"):
        out.append(ArtSpec(f"shot.{kind}", (lambda k=kind: projectile(k)), 1.0, (12, 12), "common"))
    for kind in ("sparkle", "leaf", "petal", "debris", "soft"):
        out.append(ArtSpec(f"particle.{kind}", (lambda k=kind: particle(k)), 1.0, (8, 8), "common"))
    out.append(ArtSpec("checkpoint.off", lambda: checkpoint(False), 1.0, (20, 111), "common"))
    out.append(ArtSpec("checkpoint.on", lambda: checkpoint(True), 1.0, (20, 111), "common"))
    out.append(ArtSpec("sign", sign, 1.0, (20, 48), "common"))
    out.append(ArtSpec("flame_orb", flame_orb, 1.0, (20, 20), "common"))
    for kind in ("water", "lava", "poison"):
        out.append(ArtSpec(f"liquid.{kind}.surface", (lambda k=kind: liquid_surface(k)), 1.0, (0, 4), "common"))
        out.append(ArtSpec(f"liquid.{kind}.body", (lambda k=kind: liquid_body(k)), 1.0, (0, 0), "common"))
    return out
