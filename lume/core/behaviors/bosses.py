"""Boss families.

``guardian`` is the exact port of the five legacy guardians (open-shell
vulnerability window, charge, jump and shots; faster in the second half).
``thorn_boar`` is the Reino Verde fortress boss: telegraphed charges that end
in a wall crash, which opens the only vulnerability window.
"""

from __future__ import annotations

from .base import Behavior, ground_move, player_distance, register
from .ranged import fire


@register("guardian")
class Guardian(Behavior):
    states = ("walk", "shell", "jump", "hurt", "defeat")

    def spawn(self, game, e):
        e.vx = -60.0
        e.facing = -1
        e.anim = "walk"

    def update(self, game, e, dt, old_timer):
        hp = e.hp or 4
        tier = int(self.param(e, "tier", 1))
        aggressive = e.health <= hp / 2
        period = 3.8 if aggressive else 4.8
        phase, previous = e.timer % period, old_timer % period
        vulnerable = phase < (1.1 if aggressive else 1.65)
        e.state = "shell" if vulnerable else "walk"
        e.vx = 0.0 if vulnerable else e.facing * (135.0 if aggressive else 85.0)
        if phase >= 2 and previous < 2 and e.grounded:
            e.vy = -400.0
        shots = (2.5, 3.0, 3.4) if tier >= 5 else (2.7,)
        for shot in shots:
            if phase >= shot and previous < shot:
                direction = -1 if game.player.x < e.x else 1
                fire(game, e, vx=direction * (160.0 + tier * 15), vy=-40.0 if aggressive else 0.0, size=14, life=4.0,
                     kind="guardian_orb", x=e.x + e.w / 2, y=e.y + 24)
        ground_move(game, e, dt, edge_turn=False)
        e.anim = "shell" if vulnerable else ("jump" if not e.grounded else "walk")

    def can_take_damage(self, game, e, source):
        return e.state == "shell"

    def stompable(self, game, e):
        return True

    def on_stomp(self, game, e):
        game.bounce_player(e)
        game.hit_enemy(e, 1, "stomp")


@register("thorn_boar")
class ThornBoar(Behavior):
    """intro → stalk → telegraph → charge → crash/stunned (vulnerable) → recover.
    Second phase: shorter telegraph, faster charge and falling thorn-acorns."""

    states = ("intro", "stalk", "telegraph", "charge", "stunned", "recover", "hurt", "defeat")

    def spawn(self, game, e):
        e.vx = 0.0
        e.facing = -1
        e.set_state("dormant")

    def update(self, game, e, dt, old_timer):
        dx, _ = player_distance(game, e)
        hp = e.hp or 3
        angry = e.health <= hp / 2
        if e.state == "dormant":
            e.vx = 0.0
            if abs(dx) < float(self.param(e, "wake_range", 430.0)):
                e.set_state("intro")
                game.emit("boss_intro", x=e.x, y=e.y, ref=e.species)
        elif e.state == "intro":
            e.vx = 0.0
            if e.state_time > 1.3:
                e.set_state("stalk")
        elif e.state == "stalk":
            e.facing = 1 if dx > 0 else -1
            e.vx = e.facing * (95.0 if angry else 70.0)
            if e.state_time > (0.8 if angry else 1.2):
                e.set_state("telegraph")
        elif e.state == "telegraph":
            e.vx = 0.0
            e.facing = 1 if dx > 0 else -1
            if e.state_time > (0.45 if angry else 0.7):
                e.set_state("charge")
                game.emit("charge", x=e.x, y=e.y)
        elif e.state == "charge":
            e.vx = e.facing * (400.0 if angry else 330.0)
        elif e.state == "stunned":
            e.vx = 0.0
            if e.state_time > (1.35 if angry else 1.8):
                e.set_state("recover")
        elif e.state == "hurt":
            # knocked back toward the arena centre; harmless while recoiling
            centre = (e.patrol[0] + e.patrol[1]) / 2
            e.facing = 1 if centre > e.x + e.w / 2 else -1
            e.vx = e.facing * (160.0 if e.state_time < 0.5 else 0.0)
            if e.state_time > 1.1:
                e.set_state("recover")
        elif e.state == "recover":
            e.vx = 0.0
            if e.state_time > 0.55:
                e.set_state("stalk")
        before = e.vx
        ground_move(game, e, dt, edge_turn=False)
        if e.state == "charge" and before != 0 and e.vx == 0:
            e.facing *= -1  # ground_move flipped it; keep the head pointing at the wall
            e.set_state("stunned")
            game.shake = max(game.shake, 0.35)
            game.emit("crash", x=e.x + (e.w if e.facing > 0 else 0), y=e.y + e.h / 2)
            if angry:
                self._drop_thorns(game, e)
        e.anim = e.state if e.state != "dormant" else "intro"

    def _drop_thorns(self, game, e):
        p = game.player
        left, right = e.patrol
        for offset in (-90.0, 0.0, 90.0):
            x = max(left + 20, min(right - 40, p.x + offset))
            fire(game, e, vx=0.0, vy=40.0, size=18, life=3.2, kind="thorn_acorn", gravity=700.0,
                 x=x, y=game.camera.y + 10)

    def spiked(self, game, e):
        return e.state != "stunned"

    def tangible(self, game, e):
        return e.state not in ("hurt", "dormant")

    def stompable(self, game, e):
        return e.state == "stunned"

    def can_take_damage(self, game, e, source):
        return e.state == "stunned" or (source == "fire" and e.state == "telegraph")

    def on_stomp(self, game, e):
        game.bounce_player(e)
        if game.hit_enemy(e, 1, "stomp") and e.alive:
            e.set_state("hurt")

    def on_damaged(self, game, e, source):
        e.set_state("hurt")


@register("scarab_king")
class ScarabKing(Behavior):
    """Deserto Dourado boss.

    dormant → intro → burrow (tracks Lume under the sand) → telegraph (sand
    spray under Lume) → erupt (leaps out, harmful) → dazed (lands on its back:
    the only stomp window) → roll (curled, bounces off a wall once) → recover.
    Second phase: shorter telegraph, faster roll, three sand balls on erupting.
    """

    states = ("intro", "burrow", "telegraph", "erupt", "dazed", "roll", "recover", "hurt", "defeat")

    def spawn(self, game, e):
        e.vx = 0.0
        e.facing = -1
        e.set_state("dormant")

    def update(self, game, e, dt, old_timer):
        p = game.player
        dx, _ = player_distance(game, e)
        hp = e.hp or 3
        angry = e.health <= hp / 2
        left, right = e.patrol
        if e.state == "dormant":
            e.vx = 0.0
            if abs(dx) < float(self.param(e, "wake_range", 420.0)):
                e.set_state("intro")
                game.emit("boss_intro", x=e.x, y=e.y, ref=e.species)
        elif e.state == "intro":
            e.vx = 0.0
            if e.state_time > 1.2:
                e.set_state("burrow")
        elif e.state == "burrow":
            target = p.x + p.w / 2 - e.w / 2
            e.vx = max(-180.0, min(180.0, (target - e.x) * 3.0))
            e.facing = 1 if dx > 0 else -1
            if e.state_time > (0.9 if angry else 1.3):
                e.set_state("telegraph")
                e.memory["strike_x"] = max(left, min(right - e.w, target))
                game.emit("dust", x=e.x + e.w / 2, y=e.y + e.h)
        elif e.state == "telegraph":
            e.vx = 0.0
            e.x += (e.memory.get("strike_x", e.x) - e.x) * min(1.0, dt * 10)
            if e.state_time > (0.45 if angry else 0.65):
                e.set_state("erupt")
                e.vy = -640.0
                game.shake = max(game.shake, 0.2)
                game.emit("crash", x=e.x + e.w / 2, y=e.y + e.h)
                if angry:
                    for k, vx in enumerate((-200.0, 0.0, 200.0)):
                        fire(game, e, vx=vx, vy=-420.0 - 40 * k, size=16, life=3.0, kind="sand", gravity=900.0,
                             x=e.x + e.w / 2, y=e.y)
        elif e.state == "erupt":
            e.vx = 0.0
            if e.grounded and e.state_time > 0.15:
                e.set_state("dazed")
                game.emit("land_dust", x=e.x + e.w / 2, y=e.y + e.h)
        elif e.state == "dazed":
            e.vx = 0.0
            if e.state_time > (1.1 if angry else 1.6):
                e.set_state("roll")
                e.facing = 1 if dx > 0 else -1
                e.memory["bounces"] = 0
        elif e.state == "roll":
            e.vx = e.facing * (380.0 if angry else 300.0)
        elif e.state == "hurt":
            centre = (left + right) / 2
            e.facing = 1 if centre > e.x + e.w / 2 else -1
            e.vx = e.facing * (150.0 if e.state_time < 0.4 else 0.0)
            if e.state_time > 0.9:
                e.set_state("burrow")
        elif e.state == "recover":
            e.vx = 0.0
            if e.state_time > 0.6:
                e.set_state("burrow")
        before = e.vx
        gravity = e.state not in ("burrow", "telegraph", "dormant")
        ground_move(game, e, dt, edge_turn=False, gravity=gravity)
        if e.state == "roll" and before != 0 and e.vx == 0:
            e.memory["bounces"] = e.memory.get("bounces", 0) + 1
            game.shake = max(game.shake, 0.15)
            game.emit("crash", x=e.x + e.w / 2, y=e.y + e.h / 2)
            if e.memory["bounces"] >= 2:
                e.set_state("recover")
        e.anim = e.state if e.state != "dormant" else "burrow"

    def tangible(self, game, e):
        return e.state not in ("dormant", "burrow", "telegraph", "hurt")

    def spiked(self, game, e):
        return e.state in ("erupt", "roll")

    def stompable(self, game, e):
        return e.state == "dazed"

    def can_take_damage(self, game, e, source):
        return e.state == "dazed"

    def on_stomp(self, game, e):
        game.bounce_player(e)
        if game.hit_enemy(e, 1, "stomp") and e.alive:
            e.set_state("hurt")

    def on_damaged(self, game, e, source):
        e.set_state("hurt")
