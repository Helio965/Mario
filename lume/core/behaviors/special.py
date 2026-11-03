"""Special families: emerger (hostile plants / burrow ambushers), shy ghost,
crusher, swimmer/leaper, lava jumper and puffer."""

from __future__ import annotations

import math

from .base import Behavior, apply_gravity, player_distance, register
from .ranged import fire


@register("emerger")
class Emerger(Behavior):
    """Hidden → rising (telegraph) → out (snaps; may spit) → retreating.
    Stays hidden while the player stands right next to its spot (``shy``)."""

    states = ("hidden", "rise", "out", "bite", "retreat", "hurt", "defeat")

    def spawn(self, game, e):
        e.set_state("hidden")
        e.vx = 0.0
        e.memory["base_y"] = e.y

    def update(self, game, e, dt, old_timer):
        dx, dy = player_distance(game, e)
        hidden_time = float(self.param(e, "hidden_time", 1.8))
        out_time = float(self.param(e, "out_time", 2.0))
        travel = float(self.param(e, "travel", e.h))
        base = e.memory["base_y"]
        if e.state == "hidden":
            e.y = base + travel
            shy = float(self.param(e, "shy_radius", 42.0))
            if e.state_time >= hidden_time and not (abs(dx) < shy + e.w / 2 and abs(dy) < 120):
                e.set_state("rise")
        elif e.state == "rise":
            t = min(1.0, e.state_time / 0.45)
            e.y = base + travel * (1 - t)
            if t >= 1:
                e.set_state("out")
                e.memory["spat"] = False
        elif e.state == "out":
            e.y = base
            e.facing = 1 if dx > 0 else -1
            shots = int(self.param(e, "shots", 0))
            if shots and not e.memory.get("spat") and e.state_time > out_time * 0.45:
                e.memory["spat"] = True
                for i in range(shots):
                    fire(game, e, vx=e.facing * (140 + 40 * i), vy=-160 - 40 * i, size=12, life=3.0,
                         kind=str(self.param(e, "shot_kind", "seed")), gravity=520.0, y=e.y + 4)
            if e.state_time >= out_time:
                e.set_state("retreat")
        elif e.state == "retreat":
            t = min(1.0, e.state_time / 0.45)
            e.y = base + travel * t
            if t >= 1:
                e.set_state("hidden")
        e.anim = "bite" if e.state == "out" and (e.state_time % 0.6) < 0.25 else e.state

    def tangible(self, game, e):
        return e.state in ("out", "rise", "retreat") and e.y < e.memory.get("base_y", e.y) + float(self.param(e, "travel", e.h)) * 0.7


@register("shy_ghost")
class ShyGhost(Behavior):
    """Approaches only while the player looks away; when faced it stops and
    hides its face. Passes through walls. Light (dark zones) can repel it."""

    states = ("chase", "hide", "hurt", "defeat")

    def spawn(self, game, e):
        e.vx = 0.0
        e.set_state("hide")

    def update(self, game, e, dt, old_timer):
        p = game.player
        dx, dy = player_distance(game, e)
        facing_ghost = (p.facing > 0) == (dx < 0) if abs(dx) > 4 else True
        speed = float(self.param(e, "speed", self.profile.speed))
        if facing_ghost and abs(dx) < 700:
            e.set_state("hide")
            e.vx *= max(0.0, 1 - dt * 6)
            e.vy *= max(0.0, 1 - dt * 6)
        elif abs(dx) < float(self.param(e, "sight", 520.0)):
            e.set_state("chase")
            dist = max(1.0, math.hypot(dx, dy))
            e.vx += (dx / dist * speed - e.vx) * min(1.0, dt * 2.5)
            e.vy += (dy / dist * speed - e.vy) * min(1.0, dt * 2.5)
            e.facing = 1 if dx > 0 else -1
        e.x += e.vx * dt
        e.y += e.vy * dt + math.sin(e.timer * 3) * 6 * dt
        e.anim = e.state

    def stompable(self, game, e):
        return False


@register("crusher")
class Crusher(Behavior):
    """Waits above a lane; shakes (telegraph) when the player passes below,
    slams down, rests, then rises slowly. Indestructible obstacle."""

    states = ("wait", "shake", "fall", "rest", "rise", "defeat")

    def spawn(self, game, e):
        e.vx = 0.0
        e.set_state("wait")

    def update(self, game, e, dt, old_timer):
        p = game.player
        if e.state == "wait":
            e.y = e.origin_y
            if p.x + p.w > e.x - 24 and p.x < e.x + e.w + 24 and p.y > e.y:
                e.set_state("shake")
        elif e.state == "shake":
            if e.state_time > float(self.param(e, "telegraph", 0.35)):
                e.set_state("fall")
                e.vy = 0.0
        elif e.state == "fall":
            apply_gravity(e, dt, gravity=2600.0, max_fall=900.0)
            from ..physics import move_body

            hit = move_body(e, game.index, dt, reveal_hidden=False)
            if hit.grounded:
                e.set_state("rest")
                game.shake = max(game.shake, 0.18)
                game.emit("crash", x=e.x + e.w / 2, y=e.y + e.h)
        elif e.state == "rest":
            if e.state_time > float(self.param(e, "rest", 1.0)):
                e.set_state("rise")
        elif e.state == "rise":
            e.y = max(e.origin_y, e.y - 70 * dt)
            if e.y <= e.origin_y:
                e.set_state("wait")
        e.anim = e.state

    def stompable(self, game, e):
        return False

    def safe_top(self, game, e):
        return True

    def vulnerable_to(self, game, e, source):
        return False

    def on_stomp(self, game, e):
        # Its top is safe: treat it like standing on a block.
        p = game.player
        p.y = e.y - p.h
        p.vy = 0.0
        p.grounded = True


@register("swimmer")
class Swimmer(Behavior):
    """Swims a sine path inside its patrol; ``leap`` makes it jump out of the
    water in an arc periodically; ``chase`` steers toward a swimming player."""

    states = ("swim", "leap", "chase", "hurt", "defeat")

    def spawn(self, game, e):
        e.facing = -1
        e.vx = -self.speed(e)
        e.set_state("swim")

    def update(self, game, e, dt, old_timer):
        dx, dy = player_distance(game, e)
        leap = float(self.param(e, "leap_interval", 0.0))
        if e.state == "leap":
            e.vy += 900.0 * dt
            e.x += e.vx * dt
            e.y += e.vy * dt
            if e.y >= e.origin_y and e.vy > 0:
                e.y = e.origin_y
                e.set_state("swim")
        else:
            if leap and int(e.timer // leap) > int(old_timer // leap):
                e.set_state("leap")
                e.vy = -float(self.param(e, "leap_speed", 560.0))
                e.vx = e.facing * self.speed(e) * 1.4
                game.emit("splash", x=e.x, y=e.y)
            elif self.param(e, "chase", False) and game.player.swimming and abs(dx) < 260:
                e.set_state("chase")
                e.vx += ((1 if dx > 0 else -1) * self.speed(e) * 1.3 - e.vx) * min(1.0, dt * 2)
                e.y += max(-60.0, min(60.0, dy)) * dt
                e.facing = 1 if e.vx > 0 else -1
                e.x += e.vx * dt
            else:
                e.set_state("swim")
                e.vx = e.facing * self.speed(e)
                e.x += e.vx * dt
                e.y = e.origin_y + math.sin(e.timer * float(self.param(e, "frequency", 1.8))) * float(self.param(e, "amplitude", 18.0))
        e.anim = e.state


@register("lava_jumper")
class LavaJumper(Behavior):
    """Leaps vertically out of lava on a fixed rhythm (telegraphed by bubbles)."""

    states = ("submerged", "bubble", "jump", "fall", "defeat")

    def spawn(self, game, e):
        e.vx = 0.0
        e.set_state("submerged")

    def update(self, game, e, dt, old_timer):
        interval = float(self.param(e, "interval", 2.6))
        if e.state == "submerged":
            e.y = e.origin_y
            if e.state_time > interval - 0.5:
                e.set_state("bubble")
        elif e.state == "bubble":
            if e.state_time > 0.5:
                e.set_state("jump")
                e.vy = -float(self.param(e, "jump_speed", 640.0))
        else:
            e.vy += 1300.0 * dt
            e.y += e.vy * dt
            if e.vy > 0:
                e.state = "fall"
            if e.y >= e.origin_y and e.vy > 0:
                e.y = e.origin_y
                e.set_state("submerged")
        e.anim = e.state

    def tangible(self, game, e):
        return e.state in ("jump", "fall")

    def stompable(self, game, e):
        return False

    def vulnerable_to(self, game, e, source):
        return source == "star"


@register("puffer")
class Puffer(Behavior):
    """Bobs in place; inflates with spikes when the player gets close."""

    states = ("idle", "inflate", "spiky", "deflate", "hurt", "defeat")

    def spawn(self, game, e):
        e.vx = 0.0
        e.set_state("idle")

    def update(self, game, e, dt, old_timer):
        dx, dy = player_distance(game, e)
        near = math.hypot(dx, dy) < float(self.param(e, "trigger", 120.0))
        if e.state == "idle" and near:
            e.set_state("inflate")
        elif e.state == "inflate" and e.state_time > 0.3:
            e.set_state("spiky")
        elif e.state == "spiky" and not near and e.state_time > 1.2:
            e.set_state("deflate")
        elif e.state == "deflate" and e.state_time > 0.4:
            e.set_state("idle")
        e.y = e.origin_y + math.sin(e.timer * 1.6) * 12
        e.anim = e.state

    def spiked(self, game, e):
        return e.state in ("inflate", "spiky")


__all__ = ["Emerger", "ShyGhost", "Crusher", "Swimmer", "LavaJumper", "Puffer"]
