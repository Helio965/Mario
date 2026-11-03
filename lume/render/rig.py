"""Cut-out skeletal rigs: forward kinematics and part drawing.

A rig is a tree of bones in *design units* (du). Each frame an animator
produces a :class:`Pose` (bone angles in degrees, root offset, squash and
stretch); :func:`solve` turns it into transforms and :class:`RigDrawer` draws
every part texture rotated around its joint (one GPU quad per part).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable, Optional


@dataclass(slots=True)
class Xf:
    x: float = 0.0
    y: float = 0.0
    angle: float = 0.0  # degrees, clockwise (screen space, y down)
    sx: float = 1.0
    sy: float = 1.0

    def child(self, lx: float, ly: float, angle: float = 0.0) -> "Xf":
        a = math.radians(self.angle)
        px, py = lx * self.sx, ly * self.sy
        return Xf(
            self.x + px * math.cos(a) - py * math.sin(a),
            self.y + px * math.sin(a) + py * math.cos(a),
            self.angle + angle,
            self.sx,
            self.sy,
        )


@dataclass
class Pose:
    angles: dict[str, float] = field(default_factory=dict)
    root_x: float = 0.0
    root_y: float = 0.0
    sx: float = 1.0
    sy: float = 1.0
    extra: dict = field(default_factory=dict)

    def get(self, bone: str, default: float = 0.0) -> float:
        return self.angles.get(bone, default)


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def smoothstep(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def blend(a: Pose, b: Pose, t: float) -> Pose:
    keys = set(a.angles) | set(b.angles)
    return Pose(
        {k: lerp(a.angles.get(k, 0.0), b.angles.get(k, 0.0), t) for k in keys},
        lerp(a.root_x, b.root_x, t), lerp(a.root_y, b.root_y, t), lerp(a.sx, b.sx, t), lerp(a.sy, b.sy, t),
        dict(b.extra if t >= 0.5 else a.extra),
    )


class Spring:
    """Critically damped scalar spring for secondary motion (scarf, lantern, hat)."""

    __slots__ = ("value", "velocity", "stiffness", "damping")

    def __init__(self, value: float = 0.0, stiffness: float = 120.0, damping: float = 14.0) -> None:
        self.value, self.velocity, self.stiffness, self.damping = value, 0.0, stiffness, damping

    def update(self, target: float, dt: float) -> float:
        dt = min(dt, 1 / 30)
        accel = (target - self.value) * self.stiffness - self.velocity * self.damping
        self.velocity += accel * dt
        self.value += self.velocity * dt
        return self.value


@dataclass(slots=True)
class DrawCommand:
    part: str
    xf: Xf
    alpha: float = 1.0
    tint: Optional[tuple[int, int, int]] = None
    scale: float = 1.0


class RigDrawer:
    """Draws :class:`DrawCommand` lists produced in rig space (du, facing right).

    ``place`` maps rig space to world units: world = origin + (x * flip, y) * du.
    """

    def __init__(self, textures: Callable[[str], tuple], world_to_canvas: Callable[[float, float], tuple[float, float]],
                 canvas_per_world: float) -> None:
        self.textures = textures  # part id -> (texture, w_du, h_du, pivot_du)
        self.world_to_canvas = world_to_canvas
        self.k = canvas_per_world

    def draw(self, display, commands: list[DrawCommand], origin_x: float, origin_y: float, du: float, facing: int,
             alpha: float = 1.0, tint: Optional[tuple[int, int, int]] = None) -> None:
        flip = facing < 0
        for cmd in commands:
            entry = self.textures(cmd.part)
            if entry is None:
                continue
            tex, w_du, h_du, (pvx, pvy) = entry
            xf = cmd.xf
            wx = origin_x + (-xf.x if flip else xf.x) * du
            wy = origin_y + xf.y * du
            cx, cy = self.world_to_canvas(wx, wy)
            scale = du * self.k * cmd.scale
            w, h = w_du * scale * xf.sx, h_du * scale * xf.sy
            px, py = pvx * scale * xf.sx, pvy * scale * xf.sy
            if flip:
                px = w - px
            display.draw(
                tex, cx - px, cy - py, w, h,
                angle=-xf.angle if flip else xf.angle,
                origin=(px, py),
                flip_x=flip, alpha=alpha * cmd.alpha, tint=cmd.tint or tint,
            )
