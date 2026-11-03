"""Air families: flyer (sine patrol, optional wings that fall off), swooper,
floater and cloud rider."""

from __future__ import annotations

import math

from .base import Behavior, ground_move, player_distance, register


@register("flyer")
class Flyer(Behavior):
    """Legacy sine flight that ignores terrain. With ``grounded_form`` the first
    stomp only tears the wings off and the creature continues as that species."""

    states = ("fly", "hurt", "defeat")

    def spawn(self, game, e):
        e.facing = -1
        e.vx = -self.speed(e)
        e.anim = "fly"

    def update(self, game, e, dt, old_timer):
        e.vx = e.facing * self.speed(e)
        e.x += e.vx * dt
        amplitude = float(self.param(e, "amplitude", 38.0))
        frequency = float(self.param(e, "frequency", 2.2))
        e.y = e.origin_y + math.sin(e.timer * frequency) * amplitude
        e.anim = "fly"

    def on_stomp(self, game, e):
        form = self.param(e, "grounded_form", "")
        if form:
            game.bounce_player(e)
            game.transform_enemy(e, form)
            game.score += 100
            game.emit("wings_lost", x=e.x, y=e.y)
            return
        super().on_stomp(game, e)


@register("swooper")
class Swooper(Behavior):
    """Hangs/perches, notices the player below, swoops down in an arc, climbs back."""

    states = ("perch", "alert", "dive", "climb", "hurt", "defeat")

    def spawn(self, game, e):
        e.set_state("perch")
        e.vx = 0.0

    def update(self, game, e, dt, old_timer):
        dx, dy = player_distance(game, e)
        if e.state == "perch":
            e.vx, e.vy = 0.0, 0.0
            if abs(dx) < float(self.param(e, "sight", 180.0)) and 0 < dy < 360:
                e.set_state("alert")
                e.facing = 1 if dx > 0 else -1
        elif e.state == "alert":
            if e.state_time > float(self.param(e, "telegraph", 0.4)):
                e.set_state("dive")
                e.memory["dive_dir"] = e.facing
        elif e.state == "dive":
            e.vx = e.memory.get("dive_dir", e.facing) * float(self.param(e, "dive_speed", 190.0))
            e.vy = 260.0 * max(0.0, 1.0 - e.state_time / 0.9)
            if e.state_time > 1.2:
                e.set_state("climb")
        elif e.state == "climb":
            e.vx = e.memory.get("dive_dir", e.facing) * 120.0
            e.vy = -150.0
            if e.y <= e.origin_y or e.state_time > 2.4:
                e.y = max(e.y, e.origin_y)
                e.set_state("perch")
        e.x += e.vx * dt
        e.y += e.vy * dt
        e.anim = e.state


@register("floater")
class Floater(Behavior):
    """Drifts slowly up and down (balloons, jellyfish, spores). Usually spiked."""

    states = ("drift", "hurt", "defeat")

    def spawn(self, game, e):
        e.vx = 0.0
        e.anim = "drift"

    def update(self, game, e, dt, old_timer):
        amplitude = float(self.param(e, "amplitude", 48.0))
        frequency = float(self.param(e, "frequency", 1.1))
        drift = float(self.param(e, "drift", 0.0))
        e.y = e.origin_y + math.sin(e.timer * frequency + e.origin_x * 0.01) * amplitude
        if drift:
            e.x += e.facing * drift * dt
        e.anim = "drift"


@register("cloud_rider")
class CloudRider(Behavior):
    """Follows the player from above and drops seeds that become walkers."""

    states = ("float", "throw", "hurt", "defeat")

    def spawn(self, game, e):
        e.vx = 0.0
        e.anim = "float"

    def update(self, game, e, dt, old_timer):
        dx, _ = player_distance(game, e)
        target = max(-1.0, min(1.0, dx / 120.0)) * float(self.param(e, "speed", 130.0))
        e.vx += (target - e.vx) * min(1.0, dt * 2.0)
        e.x += e.vx * dt
        e.y = e.origin_y + math.sin(e.timer * 1.7) * 10
        e.facing = 1 if e.vx >= 0 else -1
        period = float(self.param(e, "interval", 3.0))
        phase, previous = e.timer % period, old_timer % period
        e.anim = "throw" if phase > period - 0.5 else "float"
        if phase < previous and abs(dx) < 420 and len([x for x in game.enemies if x.alive and x.memory.get("spawned_by") == e.id]) < 3:
            spawn = self.param(e, "seed_species", "")
            if spawn:
                child = game.spawn_enemy(spawn, e.x + e.w / 2 - 12, e.y + e.h + 4)
                if child is not None:
                    child.memory["spawned_by"] = e.id
                    child.vy = -200.0
                    child.facing = 1 if dx > 0 else -1


__all__ = ["Flyer", "Swooper", "Floater", "CloudRider", "ground_move"]
