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
        elif e.state in ("recover", "hurt"):
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
