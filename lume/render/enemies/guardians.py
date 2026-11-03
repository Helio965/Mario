"""The five legacy guardians (now mid-bosses), one material set per biome."""

from __future__ import annotations

import math

from ..rig import Xf
from ..svg import Svg, blob, rounded_rect_path, shade, smooth_closed, star_points
from .base import INK, CreatureRig, register

MATERIALS = {
    "guardiao_pomar": ("#6f9a72", "#9dc191", "#c7bc8b", "#f1cc6f"),
    "guardiao_templo": ("#c49a64", "#e2c08a", "#f4d49a", "#72dac5"),
    "guardiao_nevasca": ("#7aa8c0", "#b8dcea", "#e6f6fb", "#d9a4d7"),
    "guardiao_arvore": ("#7a6aa0", "#a38aaa", "#c5aec9", "#9de0b8"),
    "guardiao_chama": ("#8b5a5a", "#aa7e7a", "#e09a6a", "#ffd27a"),
}


@register("guardian")
class Guardian(CreatureRig):
    du = 0.5

    def __init__(self, species: str = "") -> None:
        super().__init__(species)
        self.armor, self.panel, self.trim, self.gem = MATERIALS.get(species, MATERIALS["guardiao_pomar"])

    def part_id(self, name: str) -> str:
        return f"guardian.{self.species}.{name}"

    def parts(self):
        armor, panel, trim, gem = self.armor, self.panel, self.trim, self.gem

        def torso(open_: bool):
            s = Svg(130, 110)
            s.path(blob(65, 60, 58, 46, 0.04, seed=4), fill=s.radial(50, 40, 80, [(0, shade(armor, 0.3)), (0.6, armor), (1, shade(armor, -0.45))]),
                   stroke=INK, width=2.2)
            for x in (35, 65, 95):
                s.path(rounded_rect_path(x - 9, 26, 18, 48, 5), fill=s.linear(0, 26, 0, 74, [(0, shade(panel, 0.2)), (1, shade(panel, -0.2))]),
                       stroke=shade(armor, -0.5), width=1.2, opacity=0.95)
            s.path(f"M14 52 Q65 64 116 52", stroke=trim, width=4)
            if open_:
                s.circle(65, 60, 20, fill=s.radial(65, 60, 20, [(0, "#ffffff"), (0.35, gem), (1, shade(gem, -0.5))]), stroke=INK, width=1.6)
                s.circle(65, 60, 34, fill=s.radial(65, 60, 34, [(0, gem, 0.6), (1, gem, 0)]))
            else:
                s.path(rounded_rect_path(46, 44, 38, 34, 8), fill=s.linear(0, 44, 0, 78, [(0, shade(panel, 0.1)), (1, shade(armor, -0.3))]),
                       stroke=INK, width=1.6)
            return s

        def head():
            s = Svg(70, 64)
            s.path(blob(35, 36, 28, 24, 0.03, seed=2), fill=s.radial(28, 26, 36, [(0, shade(panel, 0.35)), (1, shade(armor, -0.3))]),
                   stroke=INK, width=2.0)
            s.path("M14 34 L56 34 L54 42 L16 42 Z", fill="#2a2238")
            s.ellipse(25, 38, 6, 3, fill=gem)
            s.ellipse(45, 38, 6, 3, fill=gem)
            if self.species == "guardiao_pomar":
                s.path(smooth_closed([(12, 20), (2, 4), (16, 10)]), fill="#9dc191", stroke=INK, width=1.2)
                s.path(smooth_closed([(58, 20), (68, 4), (54, 10)]), fill="#9dc191", stroke=INK, width=1.2)
            elif self.species == "guardiao_chama":
                for x in (18, 52):
                    s.path(blob(x, 10, 6, 10, 0.2, seed=x), fill=s.radial(x, 10, 10, [(0, "#fff0a0"), (1, "#ff6a2a")]))
            elif self.species == "guardiao_nevasca":
                s.polygon([(12, 22), (6, 2), (20, 14)], fill="#e6f6fb", stroke=INK, width=1.1)
                s.polygon([(58, 22), (64, 2), (50, 14)], fill="#e6f6fb", stroke=INK, width=1.1)
            elif self.species == "guardiao_templo":
                s.rect(14, 6, 42, 8, fill=trim, stroke=INK, width=1.1, rx=2)
            else:
                s.polygon(star_points(35, 8, 8, 3, 4), fill=gem, stroke=INK, width=1.0)
            return s

        def arm():
            s = Svg(30, 56)
            s.path(rounded_rect_path(3, 2, 24, 50, 10), fill=s.linear(3, 0, 27, 0, [(0, shade(armor, 0.2)), (1, shade(armor, -0.35))]),
                   stroke=INK, width=1.8)
            s.rect(6, 34, 18, 6, fill=trim, rx=2)
            return s

        def leg():
            s = Svg(34, 30)
            s.path(rounded_rect_path(4, 2, 26, 24, 7), fill=s.linear(0, 2, 0, 26, [(0, shade(armor, 0.1)), (1, shade(armor, -0.5))]),
                   stroke=INK, width=1.8)
            return s

        return {"torso": (lambda: torso(False), (65, 104)), "torso_open": (lambda: torso(True), (65, 104)), "head": (head, (35, 60)),
                "arm": (arm, (15, 6)), "leg": (leg, (17, 4))}

    def commands(self, e, t):
        root = Xf()
        if not e.alive:
            k = min(1.0, (1.2 - e.defeated) / 1.2)
            root = Xf(0, 0, 0, 1 + 0.3 * k, 1 - 0.7 * k)
        open_ = e.anim == "shell"
        ph = t * 7 if e.anim == "walk" else 0
        out = [self.cmd("leg", root.child(-26 + math.sin(ph) * 6, -24)), self.cmd("leg", root.child(26 - math.sin(ph) * 6, -24))]
        body = root.child(0, -18 - abs(math.sin(ph)) * 3)
        out.append(self.cmd("arm", body.child(-56, -78, 20 + math.sin(ph) * 10)))
        out.append(self.cmd("torso_open" if open_ else "torso", body))
        out.append(self.cmd("head", body.child(0, -92, math.sin(t * 2) * 3)))
        out.append(self.cmd("arm", body.child(56, -78, -20 - math.sin(ph) * 10)))
        if e.hit_timer > 0 and int(t * 20) % 2 == 0:
            for c in out:
                c.tint = (255, 170, 170)
        return out
