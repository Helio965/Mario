"""Procedural + keyed animation of Lume on the cut-out rig.

Each animation state is a pose function of time (and of the real physics
state: speed drives the stride, vertical speed drives the jump arc, landing
impact drives squash). Secondary motion (scarf, lantern, hat) uses springs,
so it follows movement instead of looping blindly. Faces combine eyes, iris
direction, brows and mouth per state; blinking is irregular but
deterministic. See docs/technical/ANIMACOES.md for timings.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from ..art.lume_parts import DU_FORM, FORMS
from ..rig import DrawCommand, Pose, Spring, Xf, lerp

BACK_TINT = (196, 200, 214)


@dataclass
class Face:
    eyes: str = "open"
    mouth: str = "smile"
    look_x: float = 0.0  # -1..1
    look_y: float = 0.0
    brow: float = 0.0  # +: raised, -: furrowed


class LumeAnimator:
    def __init__(self) -> None:
        self.state = "idle"
        self.state_time = 0.0
        self.phase = 0.0
        self.time = 0.0
        self.lean = Spring(0.0, 90.0, 13.0)
        self.scarf = [Spring(0.0, 70.0, 7.0), Spring(0.0, 55.0, 6.0)]
        self.lantern = Spring(0.0, 60.0, 4.5)
        self.hat = Spring(0.0, 140.0, 10.0)
        self.prev_vx = 0.0
        self.look = Spring(0.0, 50.0, 10.0)

    # ------------------------------------------------------------------ face
    def _blink(self) -> bool:
        period = 3.1 + 1.4 * math.sin(math.floor(self.time / 3.1) * 12.9898) ** 2
        return (self.time % period) < 0.11

    def face(self, anim: str, p) -> Face:
        f = Face()
        if anim in ("walk",):
            f.mouth, f.look_x = "smile", 0.6
        elif anim == "run":
            f.mouth, f.look_x, f.brow = "determined", 0.9, -0.5
        elif anim == "jump":
            f.mouth, f.look_x, f.look_y, f.brow = "open", 0.5, -0.6, 0.7
        elif anim == "fall":
            f.mouth, f.look_y, f.brow = "small_o", 0.7, 0.5
        elif anim == "skid":
            f.mouth, f.brow, f.look_x = "wince", -0.8, 1.0
        elif anim == "land":
            f.eyes, f.mouth = "blink", "determined"
        elif anim == "crouch":
            f.mouth, f.look_y = "smile", 0.9
        elif anim == "swim":
            f.mouth, f.look_x = "small_o", 0.7
        elif anim == "hurt":
            f.eyes, f.mouth, f.brow = "wince", "wince", -0.6
        elif anim == "dead":
            f.eyes, f.mouth, f.brow = "daze", "sad", 0.6
        elif anim == "win":
            f.eyes, f.mouth, f.brow = "happy", "grin", 0.8
        elif anim == "transform":
            f.eyes, f.mouth, f.brow = "open", "open", 1.0
        elif anim == "shoot":
            f.mouth, f.look_x, f.brow = "determined", 1.0, -0.4
        else:  # idle: look around occasionally
            cycle = self.time % 7.0
            f.look_x = -0.8 if 3.0 < cycle < 4.2 else (0.7 if 4.2 <= cycle < 5.0 else 0.2)
        if f.eyes == "open" and self._blink():
            f.eyes = "blink"
        return f

    # ------------------------------------------------------------------ pose
    def pose(self, anim: str, p, dt: float) -> Pose:
        form = "big" if p.power != "small" else "small"
        F = FORMS[form]
        t = self.state_time
        speed = abs(p.vx)
        a: dict[str, float] = {}
        pose = Pose(a)
        # defaults (standing)
        a.update(thigh_f=4, shin_f=4, thigh_b=-4, shin_b=6, upper_f=-6, fore_f=-14, upper_b=8, fore_b=-12,
                 head=0.0, torso=0.0)
        breathe = math.sin(self.time * 2.6)
        if anim == "idle":
            a.update(upper_f=-4 + breathe * 2, upper_b=6 - breathe * 2, head=breathe * 1.5)
            pose.sy = 1 + 0.012 * breathe
            pose.sx = 1 - 0.006 * breathe
        elif anim in ("walk", "run"):
            run = anim == "run"
            freq = 0.9 + speed / (95 if run else 100)
            self.phase += dt * freq * 2 * math.pi
            ph = self.phase
            amp = 36 if run else 26
            a["thigh_f"] = amp * math.sin(ph)
            a["thigh_b"] = -amp * math.sin(ph)
            a["shin_f"] = (62 if run else 34) * max(0.0, math.sin(ph - 1.6)) + 6
            a["shin_b"] = (62 if run else 34) * max(0.0, math.sin(ph - 1.6 + math.pi)) + 6
            arm = 46 if run else 24
            a["upper_f"] = -arm * math.sin(ph) + (10 if run else 0)
            a["upper_b"] = arm * math.sin(ph) + (10 if run else 0)
            a["fore_f"] = -(70 if run else 26) + (12 * math.sin(ph))
            a["fore_b"] = -(70 if run else 26) - (12 * math.sin(ph))
            pose.root_y = -(3.2 if run else 2.0) * abs(math.cos(ph))
            a["head"] = (-3 if run else -1) + math.sin(ph * 2) * 1.5
        elif anim == "skid":
            a.update(thigh_f=38, shin_f=2, thigh_b=-24, shin_b=58, upper_f=-40, fore_f=-30, upper_b=-55, fore_b=-20, head=-6)
            pose.root_y = 2.5
        elif anim == "jump":
            rise = min(1.0, t / 0.12)
            a.update(thigh_f=lerp(10, 48, rise), shin_f=lerp(10, 72, rise), thigh_b=lerp(-10, -18, rise), shin_b=lerp(10, 38, rise),
                     upper_f=lerp(20, 116, rise), fore_f=lerp(-10, -26, rise), upper_b=lerp(-10, -48, rise), fore_b=-30, head=-6)
            stretch = max(0.0, 1 - t / 0.25)
            pose.sy, pose.sx = 1 + 0.12 * stretch, 1 - 0.07 * stretch
        elif anim == "fall":
            flail = math.sin(self.time * 13)
            a.update(thigh_f=18 + flail * 4, shin_f=26, thigh_b=-8 - flail * 4, shin_b=34,
                     upper_f=92 + flail * 8, fore_f=-30, upper_b=-70 - flail * 8, fore_b=-22, head=4)
        elif anim == "land":
            a.update(thigh_f=34, shin_f=58, thigh_b=-6, shin_b=64, upper_f=24, fore_f=-30, upper_b=-26, fore_b=-24, head=6)
            k = min(1.0, p.land_impact / 0.16)
            pose.sx, pose.sy = 1 + 0.16 * k, 1 - 0.16 * k
            pose.root_y = 4 * k
        elif anim == "crouch":
            a.update(thigh_f=78, shin_f=128, thigh_b=62, shin_b=120, upper_f=34, fore_f=-70, upper_b=14, fore_b=-60, head=8, torso=14)
        elif anim == "swim":
            ph = self.time * 5.0
            stroke = math.sin(ph)
            a.update(thigh_f=20 + 30 * stroke, shin_f=40 + 30 * max(0, stroke), thigh_b=-10 - 30 * stroke, shin_b=50,
                     upper_f=78 + 36 * stroke, fore_f=-24 - 26 * stroke, upper_b=40 - 60 * stroke, fore_b=-20, torso=18, head=-10)
        elif anim == "hurt":
            shake = math.sin(self.time * 40) * 3
            a.update(thigh_f=-14, shin_f=30, thigh_b=-30, shin_b=40, upper_f=-58 + shake * 3, fore_f=-50, upper_b=-80, fore_b=-30,
                     torso=-16, head=-12 + shake)
        elif anim == "dead":
            a.update(thigh_f=20, shin_f=50, thigh_b=-20, shin_b=50, upper_f=112, fore_f=-12, upper_b=-120, fore_b=-10, head=-10)
        elif anim == "win":
            hop = abs(math.sin(t * 5.5)) if t < 1.6 else 0.0
            a.update(thigh_f=10 + 20 * hop, shin_f=10 + 40 * hop, thigh_b=-6, shin_b=10 + 30 * hop, upper_f=128, fore_f=8,
                     upper_b=-30, fore_b=-95, head=-6)
            pose.root_y = -9 * hop
        elif anim == "transform":
            a.update(upper_f=104, fore_f=-30, upper_b=-100, fore_b=-30, thigh_f=10, thigh_b=-10)
        if p.shot_flash > 0 and anim not in ("dead", "hurt", "win"):
            a.update(upper_f=88, fore_f=-4)
        # torso lean follows acceleration and speed (secondary)
        target_lean = 0.0
        if anim in ("walk", "run"):
            target_lean = (5 if anim == "walk" else 13) + (p.vx * p.facing - self.prev_vx * p.facing) * 0.02
        elif anim == "skid":
            target_lean = -12
        elif anim in ("jump", "fall"):
            target_lean = max(-8.0, min(10.0, abs(p.vx) * 0.025))
        a["torso"] = a.get("torso", 0.0) + self.lean.update(target_lean, dt)
        # hip height keeps the lowest foot on the ground
        L1, L2 = F["thigh"], F["shin"]
        def foot(th: float, sh: float) -> float:
            t1 = math.radians(th)
            t2 = math.radians(th - sh)
            return L1 * math.cos(t1) + L2 * math.cos(t2)
        hip = max(foot(a["thigh_f"], a["shin_f"]), foot(a["thigh_b"], a["shin_b"]))
        if anim in ("jump", "fall", "swim", "hurt", "dead", "transform") or not p.grounded and anim != "win":
            hip = L1 + L2 - 2
        pose.extra["hip"] = hip + 2.0
        pose.extra["form"] = form
        return pose

    # ------------------------------------------------------------------ assembly
    def commands(self, p, anim: str, dt: float, *, form_override: str | None = None, palette: str | None = None) -> tuple[list[DrawCommand], float]:
        if anim != self.state:
            self.state, self.state_time = anim, 0.0
        else:
            self.state_time += dt
        self.time += dt
        pose = self.pose(anim, p, dt)
        face = self.face(anim, p)
        form = form_override or pose.extra["form"]
        F = FORMS[form]
        pal = palette or ("fire" if p.power == "fire" else "normal")
        a = pose.angles
        # root at feet center; y up is negative
        root = Xf(pose.root_x, pose.root_y, 0.0, pose.sx, pose.sy)
        pelvis = root.child(0, -pose.extra["hip"], a["torso"] * 0.35)
        torso = pelvis.child(0, 0, a["torso"] * 0.65)
        T = F["torso"]
        neck = torso.child(0.5, -T - 0.5)
        head = neck.child(0, 0, a["head"] * 0.8)
        hc = head.child(1, -18)  # head center
        upper_len = 11.0 if form == "small" else 14.0
        sh_f = torso.child(3.0, -T + 5)
        sh_b = torso.child(-3.5, -T + 5)
        hip_f, hip_b = pelvis.child(2.5, -2), pelvis.child(-2.5, -2)
        cmds: list[DrawCommand] = []

        def limb(base: Xf, upper_ang: float, lower_ang: float, upper: str, lower: str, length: float, tint=None, elbow=False):
            u = base.child(0, 0, -upper_ang)
            lo = u.child(0, length - 1, lower_ang if not elbow else lower_ang)
            cmds.append(DrawCommand(upper, u, tint=tint))
            cmds.append(DrawCommand(lower, lo, tint=tint))

        # secondary motion targets
        speed = p.vx * (1 if p.facing >= 0 else -1)
        accel = (p.vx - self.prev_vx) / max(dt, 1e-4)
        self.prev_vx = p.vx
        flutter = math.sin(self.time * 11) * (4 + min(abs(speed), 340) / 40)
        lift = min(70.0, abs(speed) * 0.16 + max(0.0, -p.vy) * 0.04 + (25 if not p.grounded else 0))
        s0 = self.scarf[0].update(-lift + flutter, dt)
        s1 = self.scarf[1].update(-lift * 0.6 + flutter * 1.4 - 8, dt)
        sw = self.lantern.update(max(-60.0, min(60.0, -accel * 0.02 * (1 if p.facing >= 0 else -1) + speed * -0.04)), dt)
        hat_tilt = self.hat.update(max(-12.0, min(12.0, -p.vy * 0.012)), dt)
        # scarf tails behind the neck, pointing backwards (180°) with lift
        tail_base = neck.child(-5, 2.2, 0)
        t0 = tail_base.child(0, 0, 180 - 18 - s0 - neck.angle)
        t1 = t0.child(13.5, 0, s1 * 0.5 - 10)
        cmds.append(DrawCommand(f"lume.scarf_tail.{pal}.1", t1))
        cmds.append(DrawCommand(f"lume.scarf_tail.{pal}.0", t0))
        # back limbs
        limb(sh_b, a["upper_b"], a["fore_b"], f"lume.upper_arm.{form}.{pal}", f"lume.forearm.{form}.{pal}", upper_len, BACK_TINT, True)
        limb(hip_b, a["thigh_b"], a["shin_b"], f"lume.thigh.{form}.{pal}", f"lume.shin.{form}.{pal}", F["thigh"], BACK_TINT)
        limb(hip_f, a["thigh_f"], a["shin_f"], f"lume.thigh.{form}.{pal}", f"lume.shin.{form}.{pal}", F["thigh"])
        cmds.append(DrawCommand(f"lume.torso.{form}.{pal}", torso))
        belt_y = -T * 0.36 + 2.5
        cmds.append(DrawCommand(f"lume.lantern.{pal}", torso.child(8.5, belt_y, sw - torso.angle * 0.5)))
        cmds.append(DrawCommand(f"lume.scarf_wrap.{pal}", neck.child(0.5, 0.6)))
        cmds.append(DrawCommand("lume.head", head))
        # face
        look = self.look.update(face.look_x, dt)
        ix, iy = look * 1.3, face.look_y * 1.2
        for ex, ey, sc in ((-1.6, 0.4, 0.86), (9.4, 0.8, 1.0)):
            eye_xf = hc.child(ex, ey)
            cmds.append(DrawCommand(f"lume.eye.{face.eyes}", eye_xf, scale=sc))
            if face.eyes == "open":
                cmds.append(DrawCommand("lume.iris", eye_xf.child(ix + 0.4, iy + 0.6), scale=sc))
        brow_y = -8.4 - face.brow * 1.6
        cmds.append(DrawCommand("lume.brow", hc.child(-1.8, brow_y, -face.brow * 8 + 6), scale=0.82))
        cmds.append(DrawCommand("lume.brow", hc.child(9.4, brow_y - 0.4, face.brow * 8 - 6 + 4)))
        cmds.append(DrawCommand(f"lume.mouth.{face.mouth}", hc.child(8.2, 10.6)))
        cmds.append(DrawCommand(f"lume.hat.{pal}", hc.child(0.5, -14.5, -7 + hat_tilt)))
        # front arm last
        limb(sh_f, a["upper_f"], a["fore_f"], f"lume.upper_arm.{form}.{pal}", f"lume.forearm.{form}.{pal}", upper_len, None, True)
        return cmds, DU_FORM[form]
