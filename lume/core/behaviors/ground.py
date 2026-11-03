"""Ground families: walker, shell, armored, hopper, charger, slider, bones, burrower."""

from __future__ import annotations

import math

from ..constants import GRAVITY
from ..entities import Enemy
from ..physics import move_body, solid_at
from .base import Behavior, apply_gravity, ground_move, player_distance, register


@register("walker")
class Walker(Behavior):
    """Patrols, turns at walls and ledges. Optional burrow cycle (desert) and
    'notice' reaction that makes the creature look at the player first."""

    states = ("idle", "walk", "alert", "burrow", "emerge", "hurt", "defeat")

    def spawn(self, game, e):
        super().spawn(game, e)
        e.memory["noticed"] = False

    def update(self, game, e, dt, old_timer):
        interval = float(self.param(e, "burrow_interval", 0.0))
        if interval > 0:
            cycle = e.timer % interval
            hide = float(self.param(e, "burrow_time", 1.2))
            if cycle < hide:
                e.set_state("burrow")
                e.anim = "burrow" if cycle < hide - 0.35 else "emerge"
                e.vx = 0.0
                apply_gravity(e, dt)
                hit = move_body(e, game.index, dt, reveal_hidden=False)
                e.grounded = hit.grounded
                return
            if e.state == "burrow":
                e.set_state("walk")
        notice = float(self.param(e, "notice_range", 0.0))
        dx, dy = player_distance(game, e)
        if notice and not e.memory.get("noticed") and abs(dx) < notice and abs(dy) < 60:
            e.memory["noticed"] = True
            e.memory["alert"] = 0.45
            e.facing = 1 if dx > 0 else -1
        alert = e.memory.get("alert", 0.0)
        if alert > 0:
            e.memory["alert"] = alert - dt
            e.vx = 0.0
            e.anim = "alert"
            ground_move(game, e, dt, edge_turn=False)
            return
        e.vx = e.facing * self.speed(e)
        e.anim = "walk"
        ground_move(game, e, dt, edge_turn=bool(self.param(e, "edge_turn", True)))

    def tangible(self, game, e):
        return e.state != "burrow" or e.anim == "emerge"


@register("shell")
class Shell(Behavior):
    """Walk → (stomp) shell → (kick/stomp) slide → hits other enemies.
    A resting shell wakes up after ``recover_time`` seconds (0 disables)."""

    states = ("walk", "shell", "slide", "wake", "hurt", "defeat")

    def update(self, game, e, dt, old_timer):
        recover = float(self.param(e, "recover_time", 7.0))
        if e.state == "shell":
            e.vx = 0.0
            e.anim = "wake" if recover and e.state_time > recover - 1.0 else "shell"
            if recover and e.state_time >= recover:
                e.set_state("walk")
                e.facing = 1 if game.player.x > e.x else -1
        elif e.state == "slide":
            e.vx = e.facing * float(self.param(e, "slide_speed", 360.0))
            e.anim = "slide"
        else:
            e.vx = e.facing * self.speed(e)
            e.anim = "walk"
        ground_move(game, e, dt, edge_turn=e.state != "slide" and bool(self.param(e, "edge_turn", True)))
        if e.state == "slide":
            for other in game.enemies:
                if other is not e and other.alive and other.active and _overlap(e, other):
                    game.hit_enemy(other, 2, "shell")

    def spiked(self, game, e):
        return False

    def on_stomp(self, game, e):
        game.bounce_player(e)
        if e.state in ("walk", "slide"):
            e.set_state("shell")
            e.vx = 0.0
            game.score += 100
            game.emit("stomp", x=e.x, y=e.y)
        else:
            e.set_state("slide")
            p = game.player
            e.facing = 1 if p.x + p.w / 2 < e.x + e.w / 2 else -1
            e.vx = e.facing * 360.0
            game.emit("kick", x=e.x, y=e.y)

    def on_touch(self, game, e):
        if e.state == "shell":
            p = game.player
            e.set_state("slide")
            e.facing = 1 if p.x < e.x else -1
            e.x += e.facing * 14
            e.vx = e.facing * 360.0
            game.emit("kick", x=e.x, y=e.y)
        else:
            game.hurt()


@register("armored")
class Armored(Walker):
    """Slow, heavy walker that needs several hits; optional spiked crest that
    is raised periodically (stomp only when the crest is down)."""

    states = ("walk", "guard", "hurt", "defeat")

    def update(self, game, e, dt, old_timer):
        period = float(self.param(e, "crest_period", 0.0))
        if period:
            raised = (e.timer % period) < period * float(self.param(e, "crest_duty", 0.5))
            e.memory["crest"] = raised
        e.vx = e.facing * self.speed(e)
        e.anim = "guard" if e.memory.get("crest") else "walk"
        ground_move(game, e, dt, edge_turn=bool(self.param(e, "edge_turn", True)))

    def spiked(self, game, e):
        return bool(e.memory.get("crest")) or super().spiked(game, e)

    def on_damaged(self, game, e, source):
        e.facing = 1 if game.player.x > e.x else -1


@register("hopper")
class Hopper(Behavior):
    """Rests, crouches (anticipation), leaps toward the player, lands with squash."""

    states = ("idle", "crouch", "jump", "fall", "land", "hurt", "defeat")

    def spawn(self, game, e):
        e.vx = 0.0
        e.facing = -1
        e.set_state("idle")
        e.memory["wait"] = float(self.param(e, "interval", 1.6)) * 0.5

    def update(self, game, e, dt, old_timer):
        interval = float(self.param(e, "interval", 1.6))
        if e.state == "idle":
            e.vx = 0.0
            e.memory["wait"] = e.memory.get("wait", interval) - dt
            dx, _ = player_distance(game, e)
            if self.param(e, "track_player", True):
                e.facing = 1 if dx > 0 else -1
            if e.memory["wait"] <= 0:
                e.set_state("crouch")
        elif e.state == "crouch":
            e.vx = 0.0
            if e.state_time >= float(self.param(e, "anticipation", 0.28)):
                e.set_state("jump")
                e.vy = -float(self.param(e, "jump_speed", 520.0))
                e.vx = e.facing * float(self.param(e, "hop_speed", self.profile.speed))
                e.grounded = False
                game.emit("enemy_jump", x=e.x, y=e.y)
        elif e.state == "jump":
            e.vx = e.facing * float(self.param(e, "hop_speed", self.profile.speed))
            if e.grounded and e.state_time > 0.05:
                e.set_state("land")
                game.emit("land_dust", x=e.x + e.w / 2, y=e.y + e.h)
        elif e.state == "land":
            e.vx = 0.0
            if e.state_time > 0.18:
                e.set_state("idle")
                e.memory["wait"] = interval
        e.anim = e.state if e.state != "jump" else ("jump" if e.vy < 0 else "fall")
        ground_move(game, e, dt, edge_turn=False)


@register("charger")
class Charger(Behavior):
    """Patrols; on seeing the player at the same height it telegraphs (paws the
    ground), charges, and is stunned after hitting a wall."""

    states = ("walk", "alert", "charge", "stunned", "recover", "hurt", "defeat")

    def update(self, game, e, dt, old_timer):
        dx, dy = player_distance(game, e)
        sight = float(self.param(e, "sight", 300.0))
        if e.state == "walk":
            e.vx = e.facing * self.speed(e)
            if abs(dy) < 50 and abs(dx) < sight and (dx > 0) == (e.facing > 0):
                e.set_state("alert")
        elif e.state == "alert":
            e.vx = 0.0
            if e.state_time > float(self.param(e, "telegraph", 0.55)):
                e.set_state("charge")
                game.emit("charge", x=e.x, y=e.y)
        elif e.state == "charge":
            e.vx = e.facing * float(self.param(e, "charge_speed", 300.0))
            if e.state_time > float(self.param(e, "charge_time", 2.2)):
                e.set_state("recover")
        elif e.state == "stunned":
            e.vx = 0.0
            if e.state_time > float(self.param(e, "stun_time", 1.3)):
                e.set_state("recover")
        elif e.state == "recover":
            e.vx = 0.0
            if e.state_time > 0.5:
                e.set_state("walk")
        e.anim = e.state
        before = e.vx
        turned = ground_move(game, e, dt, edge_turn=e.state != "charge")
        if e.state == "charge" and before != 0 and e.vx == 0:
            e.set_state("stunned")
            game.shake = max(game.shake, 0.12)
            game.emit("crash", x=e.x, y=e.y)
        elif e.state == "charge" and e.grounded:
            probe_x = e.x + e.w + 5 if e.facing > 0 else e.x - 7
            if not solid_at(game.index, probe_x, e.y + e.h, 2, 7):
                e.facing *= -1
                e.set_state("recover")
        del turned

    def stompable(self, game, e):
        return super().stompable(game, e) and e.state != "charge"


@register("slider")
class Slider(Walker):
    """Walks; on ice it belly-slides toward the player at high speed."""

    states = ("walk", "alert", "slide", "hurt", "defeat")

    def update(self, game, e, dt, old_timer):
        floor = e.memory.get("floor_ice", False)
        dx, dy = player_distance(game, e)
        if e.state == "slide":
            e.vx = e.facing * float(self.param(e, "slide_speed", 230.0))
            if not floor or e.state_time > 3.0:
                e.set_state("walk")
        elif floor and abs(dx) < float(self.param(e, "sight", 280.0)) and abs(dy) < 50:
            e.facing = 1 if dx > 0 else -1
            e.set_state("slide")
            game.emit("slide", x=e.x, y=e.y)
        else:
            e.vx = e.facing * self.speed(e)
        e.anim = e.state
        apply_gravity(e, dt)
        before = e.vx
        hit = move_body(e, game.index, dt, reveal_hidden=False)
        e.grounded = hit.grounded
        e.memory["floor_ice"] = bool(hit.standing_on and hit.standing_on.surface == "ice")
        if before != 0 and e.vx == 0:
            e.facing *= -1
            if e.state == "slide":
                e.set_state("walk")
        if e.grounded and e.state != "slide":
            probe_x = e.x + e.w + 5 if e.facing > 0 else e.x - 7
            if not solid_at(game.index, probe_x, e.y + e.h, 2, 7):
                e.facing *= -1


@register("bones")
class Bones(Walker):
    """Collapses into a harmless pile when stomped and reassembles later.
    Only star, shell or explosions defeat it for good."""

    states = ("walk", "collapse", "pile", "reassemble", "defeat")

    def update(self, game, e, dt, old_timer):
        if e.state == "pile":
            e.vx = 0.0
            e.anim = "pile" if e.state_time < 3.2 else "reassemble"
            if e.state_time > float(self.param(e, "rest", 4.0)):
                e.set_state("walk")
                e.facing = 1 if game.player.x > e.x else -1
            ground_move(game, e, dt, edge_turn=False)
            return
        super().update(game, e, dt, old_timer)

    def tangible(self, game, e):
        return True

    def stompable(self, game, e):
        return True  # stomping only collapses it; it is not a lasting weakness

    def on_stomp(self, game, e):
        game.bounce_player(e)
        if e.state != "pile":
            e.set_state("pile")
            game.score += 100
            game.emit("collapse", x=e.x, y=e.y)

    def on_touch(self, game, e):
        if e.state != "pile":
            game.hurt()


@register("burrower")
class Burrower(Behavior):
    """Travels underground (only a dust trail is visible), surfaces next to the
    player with a telegraphed burst, walks for a while, then digs again."""

    states = ("underground", "surface", "walk", "dig", "hurt", "defeat")

    def spawn(self, game, e):
        e.set_state("underground")
        e.vx = 0.0
        e.facing = -1

    def update(self, game, e, dt, old_timer):
        dx, dy = player_distance(game, e)
        if e.state == "underground":
            e.vx = (1 if dx > 0 else -1) * float(self.param(e, "dig_speed", 120.0)) if abs(dx) > 20 else 0.0
            if abs(dx) < float(self.param(e, "surface_range", 70.0)) and abs(dy) < 80:
                e.set_state("surface")
                game.emit("dust", x=e.x + e.w / 2, y=e.y + e.h)
        elif e.state == "surface":
            e.vx = 0.0
            if e.state_time > float(self.param(e, "telegraph", 0.45)):
                e.set_state("walk")
                e.vy = -380.0
                e.facing = 1 if dx > 0 else -1
        elif e.state == "walk":
            e.vx = e.facing * self.speed(e)
            if e.state_time > float(self.param(e, "walk_time", 3.5)) and e.grounded:
                e.set_state("dig")
        elif e.state == "dig":
            e.vx = 0.0
            if e.state_time > 0.5:
                e.set_state("underground")
        e.anim = e.state
        ground_move(game, e, dt, edge_turn=e.state == "walk")

    def tangible(self, game, e):
        return e.state in ("walk", "dig") or (e.state == "surface" and e.state_time > 0.3)


def _overlap(a: Enemy, b: Enemy) -> bool:
    return a.x < b.x + b.w and a.x + a.w > b.x and a.y < b.y + b.h and a.y + a.h > b.y


__all__ = ["Walker", "Shell", "Armored", "Hopper", "Charger", "Slider", "Bones", "Burrower", "GRAVITY", "math"]
