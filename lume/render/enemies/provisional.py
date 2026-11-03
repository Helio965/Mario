"""PROVISIONAL creature used for species whose dedicated rig is not drawn yet.

A round body with eyes and feet tinted per species. It is reported as
provisional in the quality matrix and must be replaced before a world's art
is considered final.
"""

from __future__ import annotations

import hashlib
import math

from ..rig import Xf
from ..svg import Svg, blob, hue_shift, shade
from .base import INK, CreatureRig, eye_svg, pupil_svg, register


@register("provisional")
class ProvisionalCreature(CreatureRig):
    du = 0.5
    provisional = True

    def __init__(self, species: str = "") -> None:
        super().__init__(species)
        h = int(hashlib.sha1(species.encode()).hexdigest()[:6], 16)
        self.color = hue_shift("#c8784a", h % 360, 1.0, 1.0)

    def part_id(self, name: str) -> str:
        return f"provisional.{self.species}.{name}"

    def parts(self):
        c = self.color

        def body():
            s = Svg(60, 52)
            s.path(blob(30, 30, 26, 21, 0.05, seed=3), fill=s.radial(22, 20, 38, [(0, shade(c, 0.4)), (0.6, c), (1, shade(c, -0.45))]),
                   stroke=INK, width=1.8)
            return s

        def foot():
            s = Svg(14, 9)
            s.path(blob(7, 5, 6, 3.8, 0.05, seed=2), fill=shade(c, -0.5), stroke=INK, width=1.2)
            return s

        return {"body": (body, (30, 50)), "eye": (lambda: eye_svg(12), (6, 6)), "pupil": (lambda: pupil_svg(6), (3, 3)),
                "foot": (foot, (7, 8))}

    def commands(self, e, t):
        root = Xf()
        if not e.alive:
            root = self.defeat_xf(e, root)
        ph = t * 9
        out = [self.cmd("foot", root.child(-9 + math.sin(ph) * 3, 0)), self.cmd("foot", root.child(10 - math.sin(ph) * 3, 0))]
        body = root.child(0, -3 - abs(math.sin(ph)) * 1.6)
        out.append(self.cmd("body", body))
        if e.alive:
            for ex in (4.0, 15.0):
                eye = body.child(ex, -30)
                out.append(self.cmd("eye", eye))
                out.append(self.cmd("pupil", eye.child(1.6, 0.4)))
        return out
