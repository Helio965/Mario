"""Fixed-step platformer simulation.

Ported from ``src/core/game.ts`` (and interactions/enemies/powers) of the
TypeScript edition. The order of operations inside :meth:`Game._step` is the
legacy one, so the fifteen legacy levels keep their tuned feel; new systems
(zones, swimming, springs, conveyors, enemy activation, species behaviours,
multiple checkpoints, collectibles and secrets) hook into that order.
"""

from __future__ import annotations

import math
from typing import Iterable, Optional, Sequence

from . import constants as C
from .behaviors import Behavior, behavior_for
from .camera import Camera
from .entities import (
    Checkpoint,
    Coin,
    Enemy,
    GameEvent,
    Hazard,
    Item,
    Motion,
    Particle,
    Platform,
    Player,
    Projectile,
    Zone,
)
from .geometry import approach, overlaps
from .input import InputState
from .physics import CollisionIndex, move_body
from .species import EnemyProfile, load_profiles
from ..levels.schema import LevelSpec

ACTIVATION_MARGIN = 160.0
POWER_TEXT = {
    "grow": "Mais forte!",
    "fire": "Chama ativa — pressione J",
    "star": "12 segundos de invencibilidade",
}


class Game:
    def __init__(
        self,
        levels: Optional[Sequence[LevelSpec]] = None,
        *,
        profiles: Optional[dict[str, EnemyProfile]] = None,
        activation: bool = True,
    ) -> None:
        if levels is None:
            from ..levels.campaign import load_campaign

            levels = load_campaign().levels
        self.levels: list[LevelSpec] = list(levels)
        if not self.levels:
            raise ValueError("a campanha precisa de ao menos uma fase")
        self.profiles = profiles if profiles is not None else load_profiles()
        self.behaviors: dict[str, Behavior] = {}
        self.activation = activation
        self.camera = Camera()
        self.lives = C.LIVES_START
        self.score = 0
        self.coins_total = 0
        self.events: list[GameEvent] = []
        self.load(0)

    # ------------------------------------------------------------------ lifecycle
    def start(self, index: int = 0) -> None:
        self.lives = C.LIVES_START
        self.score = 0
        self.coins_total = 0
        self.load(index)

    def load(self, index: int) -> None:
        self.level_start_score = self.score
        self.level_index = max(0, min(index, len(self.levels) - 1))
        level = self.levels[self.level_index]
        self.level = level
        self.platforms = [
            Platform(
                id=s.id, kind=s.kind, x=s.x, y=s.y, w=s.w, h=s.h, style=s.style, surface=s.surface,
                reward=s.reward,
                motion=Motion(s.motion.axis, s.motion.range, s.motion.speed, s.motion.phase) if s.motion else None,
                destination=(s.warp.x, s.warp.y) if s.warp else None,
                return_point=(s.return_point.x, s.return_point.y) if s.return_point else None,
                secret=s.secret, surface_speed=s.surface_speed, bounce=s.bounce, group=s.group,
            )
            for s in level.platforms
        ]
        self.index = CollisionIndex(self.platforms)
        self.platform_by_id = {p.id: p for p in self.platforms}
        self.coins = [Coin(c.id, c.x, c.y, *C.COIN_SIZE) for c in level.coins]
        self.coins += [Coin(c.id, c.x, c.y, *C.RELIC_SIZE, special=True, kind=c.kind) for c in level.collectibles]
        self.items = [Item(i.id, i.kind, i.x, i.y, C.ITEM_SIZE, C.ITEM_SIZE) for i in level.items]
        self.hazards = [
            Hazard(h.id, h.kind, h.x, h.y, h.w, h.h, h.range, h.speed, h.phase, lethal=h.kind in ("lava", "water"))
            for h in level.hazards
        ]
        self.zones = [
            Zone(z.id, z.kind, z.x, z.y, z.w, z.h, z.force_x, z.force_y, z.period, z.duty, z.radius)
            for z in level.zones
        ]
        self.checkpoints = [Checkpoint(c.id, c.x, c.y) for c in level.checkpoints]
        self.enemies = []
        for spec in level.enemies:
            enemy = self._make_enemy(spec.species, spec.x, spec.y, spec.id, spec.patrol, spec.hp, spec.params)
            self.enemies.append(enemy)
        self.projectiles: list[Projectile] = []
        self.particles: list[Particle] = []
        self.events = []
        self.found: set[str] = set()  # collectible ids
        self.secrets_found: set[str] = set()
        self.last_checkpoint: Optional[Checkpoint] = None
        self.elapsed = 0.0
        self.shake = 0.0
        self.time = level.time_limit
        self.status = "playing"
        self.accumulator = 0.0
        self.previous_jump = False
        self.transition = 0.0
        self.pipe_cooldown = 0.0
        self.deaths = 0
        self.camera.lock = None
        self._spawn(level.spawn.x, level.spawn.y)
        self._activate_enemies()

    def _make_enemy(self, species: str, x: float, feet_y: float, eid: str, patrol, hp, params) -> Enemy:
        profile = self.profiles.get(species)
        if profile is None:
            raise KeyError(f"espécie desconhecida '{species}' na fase {self.level.id}")
        behavior = self.behaviors.get(species)
        if behavior is None:
            behavior = self.behaviors[species] = behavior_for(profile)
        w, h = profile.size
        hp_value = hp if hp else profile.hp
        enemy = Enemy(
            id=eid, species=species, x=x, y=feet_y - h, w=w, h=h, patrol=(float(patrol[0]), float(patrol[1])),
            hp=hp_value, params=dict(params or {}),
        )
        enemy.health = hp_value
        enemy.origin_x, enemy.origin_y = enemy.x, enemy.y
        enemy.memory["family"] = profile.behavior
        behavior.spawn(self, enemy)
        return enemy

    def behavior(self, e: Enemy) -> Behavior:
        return self.behaviors[e.species]

    def profile(self, e: Enemy) -> EnemyProfile:
        return self.profiles[e.species]

    def spawn_enemy(self, species: str, x: float, y: float) -> Optional[Enemy]:
        if species not in self.profiles:
            return None
        n = sum(1 for e in self.enemies if e.id.startswith("spawn-"))
        e = self._make_enemy(species, x, y + self.profiles[species].h, f"spawn-{n + 1}", (x - 400, x + 400), None, {})
        e.active = True
        self.enemies.append(e)
        return e

    def transform_enemy(self, e: Enemy, species: str) -> None:
        profile = self.profiles[species]
        bottom = e.y + e.h
        e.species = species
        e.w, e.h = profile.size
        e.y = bottom - e.h
        e.vy = 0.0
        e.memory = {"family": profile.behavior}
        e.state, e.state_time = "walk", 0.0
        if species not in self.behaviors:
            self.behaviors[species] = behavior_for(profile)
        facing = e.facing
        self.behaviors[species].spawn(self, e)
        e.facing = facing
        e.vx = facing * abs(e.vx)

    def _spawn(self, x: float, y: float) -> None:
        self.player = Player(x=x, y=y)
        self.camera.snap(self)

    def pause(self) -> None:
        if self.status == "playing":
            self.status = "paused"

    def resume(self) -> None:
        if self.status == "paused":
            self.status = "playing"

    def next(self) -> bool:
        if self.status != "complete" or self.level_index >= len(self.levels) - 1:
            return False
        self.load(self.level_index + 1)
        return True

    # ------------------------------------------------------------------ queries
    @property
    def checkpoint_reached(self) -> bool:
        return self.last_checkpoint is not None

    @property
    def found_relic(self) -> bool:
        return bool(self.found)

    def bosses_alive(self) -> bool:
        return any(e.alive and self.profiles[e.species].boss for e in self.enemies)

    def emit(self, type: str, *, x: float | None = None, y: float | None = None, text: str | None = None,
             value: float | None = None, ref: str | None = None) -> None:
        self.events.append(GameEvent(type, x, y, text, value, ref))

    # ------------------------------------------------------------------ main loop
    def update(self, dt: float, inp: InputState) -> None:
        if self.status in ("paused", "gameover"):
            return
        if self.status == "complete":
            self.elapsed += min(dt, C.MAX_FRAME_DT)
            for v in self.particles:
                v.life -= dt
                v.x += v.vx * dt
                v.y += v.vy * dt
            self.particles = [v for v in self.particles if v.life > 0]
            return
        self.accumulator += min(dt, C.MAX_FRAME_DT)
        while self.accumulator >= C.FIXED_DT:
            self._step(C.FIXED_DT, inp)
            self.accumulator -= C.FIXED_DT

    def _step(self, dt: float, inp: InputState) -> None:
        self.elapsed += dt
        if self.status == "dead":
            self.transition -= dt
            self._particles(dt)
            if self.transition <= 0:
                self.respawn()
            return
        if self.status != "playing":
            return
        self.time = max(0.0, self.time - dt)
        self.pipe_cooldown = max(0.0, self.pipe_cooldown - dt)
        self._update_platforms(dt)
        p = self.player
        p.invulnerable = max(0.0, p.invulnerable - dt)
        p.star = max(0.0, p.star - dt)
        p.shoot_cooldown = max(0.0, p.shoot_cooldown - dt)
        p.skid = max(0.0, p.skid - dt)
        p.land_impact = max(0.0, p.land_impact - dt)
        p.transform = max(0.0, p.transform - dt)
        p.shot_flash = max(0.0, p.shot_flash - dt)
        p.hurt_flash = max(0.0, p.hurt_flash - dt)
        p.damage_blink = max(0.0, p.damage_blink - dt)
        p.anim_time += dt
        self.shake = max(0.0, self.shake - dt)

        direction = int(inp.right) - int(inp.left)
        swim_zone, force_x, force_y, gravity_scale = self._zones_at(p)
        was_swimming = p.swimming
        p.swimming = swim_zone is not None
        jump_pressed = inp.jump and not self.previous_jump
        if p.swimming:
            self._swim(p, inp, direction, jump_pressed, dt)
        else:
            floor = self.platform_by_id.get(p.standing_on) if p.standing_on else None
            friction = C.ICE_FRICTION if floor is not None and floor.surface == "ice" else C.GROUND_FRICTION
            target = direction * (C.RUN_SPEED if inp.run else C.WALK_SPEED)
            if direction:
                rate = C.GROUND_ACCEL if p.grounded else C.AIR_ACCEL
            else:
                rate = friction if p.grounded else C.AIR_DRAG
            if p.grounded and direction and p.vx * direction < -120:
                p.skid = 0.16
            p.vx = approach(p.vx, target, rate * dt)
            if direction:
                p.facing = direction
            if jump_pressed:
                p.buffer = C.JUMP_BUFFER
            p.buffer = max(0.0, p.buffer - dt)
            p.coyote = C.COYOTE_TIME if p.grounded else max(0.0, p.coyote - dt)
            if p.buffer > 0 and p.coyote > 0:
                p.vy = -C.JUMP_SPEED
                if was_swimming:
                    p.vy *= 0.85
                p.grounded = False
                p.standing_on = None
                p.coyote = 0.0
                p.buffer = 0.0
                self.emit("jump", x=p.x + p.w / 2, y=p.y + p.h)
            if not inp.jump and p.vy < C.JUMP_CUT_SPEED:
                p.vy = C.JUMP_CUT_SPEED
            p.vy = min(C.MAX_FALL_SPEED, p.vy + C.GRAVITY * gravity_scale * dt)
        self.previous_jump = inp.jump
        if force_y:
            p.vy += force_y * dt  # vertical: acceleration (negative = updraft)
        was_grounded = p.grounded
        fall_speed = p.vy
        collision = move_body(p, self.index, dt)
        p.grounded = collision.grounded
        p.standing_on = collision.standing_on.id if collision.standing_on else None
        floor = collision.standing_on
        if floor is not None and floor.kind == "spring" and fall_speed > 60:
            p.vy = -(floor.bounce or 900.0) * (1.0 if inp.jump else 0.82)
            p.grounded = False
            p.standing_on = None
            floor.bump = 0.25
            self.emit("spring", x=floor.x + floor.w / 2, y=floor.y)
        drift = force_x * (0.6 if p.grounded else 1.0)
        if floor is not None and floor.kind == "conveyor" and floor.surface_speed:
            drift += floor.surface_speed
        if drift:
            # External drift (conveyors, wind, currents) moves the body without
            # changing the speed the player controls.
            saved_vx, saved_vy = p.vx, p.vy
            p.vx, p.vy = drift, 0.0
            move_body(p, self.index, dt)
            p.vx, p.vy = saved_vx, saved_vy
        if p.grounded and not was_grounded:
            p.land_impact = 0.16 if fall_speed > 260 else 0.08
            p.air_time = 0.0
            if fall_speed > 300:
                self.emit("land", x=p.x + p.w / 2, y=p.y + p.h, value=fall_speed)
        elif not p.grounded:
            p.air_time += dt
        p.x = max(0.0, min(p.x, self.level.width - p.w))
        self._interactions(dt, inp, collision.heads)
        area = self.level.area_at(p.x + p.w / 2, min(p.y, self.level.height - 1))
        if p.y > area.y + area.h + 100 or self.time <= 0:
            self.die()
        if self.status == "playing":
            p.animation = self._player_animation(p, inp)
        self.camera.follow(self, dt)
        self._activate_enemies()

    def _player_animation(self, p: Player, inp: InputState) -> str:
        if p.hurt_flash > 0:
            return "hurt"
        if p.transform > 0:
            return "transform"
        if p.swimming:
            return "swim"
        if not p.grounded:
            return "jump" if p.vy < 0 else "fall"
        if p.skid > 0:
            return "skid"
        if p.land_impact > 0.1:
            return "land"
        if inp.down and abs(p.vx) < 40:
            return "crouch"
        if abs(p.vx) > 260:
            return "run"
        if abs(p.vx) > 15:
            return "walk"
        return "idle"

    def _swim(self, p: Player, inp: InputState, direction: int, jump_pressed: bool, dt: float) -> None:
        target = direction * C.WATER_MAX_SPEED
        p.vx = approach(p.vx, target, (C.WATER_ACCEL if direction else C.WATER_DRAG) * dt)
        if direction:
            p.facing = direction
        if jump_pressed:
            p.vy = -C.WATER_SWIM_IMPULSE
            p.grounded = False
            p.standing_on = None
            self.emit("swim", x=p.x + p.w / 2, y=p.y)
        p.vy = max(-C.WATER_SWIM_IMPULSE * 1.2, min(C.WATER_MAX_FALL, p.vy + C.WATER_GRAVITY * dt))
        p.coyote = 0.0
        p.buffer = 0.0

    def _zones_at(self, p: Player):
        swim = None
        fx = fy = 0.0
        gravity = 1.0
        cx, cy = p.x + p.w / 2, p.y + p.h / 2
        for z in self.zones:
            if not (z.x <= cx < z.x + z.w and z.y <= cy < z.y + z.h):
                continue
            if z.kind == "swim":
                swim = z
            elif z.kind in ("wind", "current"):
                if z.period > 0 and (self.elapsed % z.period) >= z.period * z.duty:
                    continue
                fx += z.force_x
                fy += z.force_y
            elif z.kind == "lowgrav":
                gravity = min(gravity, 0.55)
        return swim, fx, fy, gravity

    def zone_active(self, z: Zone) -> bool:
        return z.period <= 0 or (self.elapsed % z.period) < z.period * z.duty

    # ------------------------------------------------------------------ platforms
    def _update_platforms(self, dt: float) -> None:
        p = self.player
        for s in self.platforms:
            s.bump = max(0.0, s.bump - dt)
            old_x, old_y = s.x, s.y
            if s.motion is not None:
                m = s.motion
                angle = self.elapsed * m.speed + m.phase
                if m.axis == "circle":
                    s.x = s.start_x + math.cos(angle) * m.range
                    s.y = s.start_y + math.sin(angle) * m.range
                else:
                    wave = math.sin(angle) * m.range
                    s.x = s.start_x + (wave if m.axis == "x" else 0.0)
                    s.y = s.start_y + (wave if m.axis == "y" else 0.0)
            s.dx = s.x - old_x
            s.dy = s.y - old_y
            if p.standing_on == s.id and s.alive:
                p.x += s.dx
                p.y += s.dy
            if s.kind == "crumble":
                if s.alive and p.standing_on == s.id:
                    s.crumble += dt
                if s.alive and s.crumble > 0.65:
                    s.alive = False
                    s.respawn = 3.0
                    self.burst(s.x + s.w / 2, s.y, "#cdaa7c", kind="debris")
                    self.emit("crumble", x=s.x + s.w / 2, y=s.y)
                if not s.alive:
                    s.respawn -= dt
                    if s.respawn <= 0 and not overlaps(p, s):
                        s.alive = True
                        s.crumble = 0.0

    # ------------------------------------------------------------------ interactions
    def _interactions(self, dt: float, inp: InputState, heads: list[Platform]) -> None:
        self._interact_world(inp, heads)
        self._update_enemies(dt)
        self._update_powers(dt, inp)
        ex = self.level.exit
        exit_rect = (ex.x - 12, ex.y - 110, 44, 110)
        p = self.player
        if (
            p.x < exit_rect[0] + exit_rect[2] and p.x + p.w > exit_rect[0]
            and p.y < exit_rect[1] + exit_rect[3] and p.y + p.h > exit_rect[1]
            and not self.bosses_alive()
        ):
            self.finish()
        self._particles(dt)

    def _particles(self, dt: float) -> None:
        for v in self.particles:
            v.life -= dt
            v.x += v.vx * dt
            v.y += v.vy * dt
            v.vy += v.gravity * dt
        if self.particles:
            self.particles = [v for v in self.particles if v.life > 0]
        for e in self.enemies:
            if not e.alive and e.defeated > 0:
                e.defeated = max(0.0, e.defeated - dt)
                e.vy += C.GRAVITY * 0.6 * dt
                e.y += e.vy * dt if e.memory.get("defeat_kind") == "knock" else 0.0

    def burst(self, x: float, y: float, color: str = "#ffe5a0", count: int = 10, kind: str = "spark") -> None:
        for i in range(count):
            self.particles.append(
                Particle(
                    x=x, y=y, vx=math.cos(i * 2.4) * 85, vy=-50 - math.sin(i * 1.7) * 90,
                    life=0.5 + (i % 3) * 0.1, color=color, size=2 + (i % 2) * 2, kind=kind,
                )
            )

    def _interact_world(self, inp: InputState, heads: list[Platform]) -> None:
        p = self.player
        for block in heads:
            if block.bump > 0:
                continue
            block.bump = 0.18
            if block.kind in ("question", "hidden") and not block.used:
                block.used = True
                self.emit("block", x=block.x, y=block.y, ref=block.id)
                if block.kind == "hidden" and block.secret:
                    self._secret(block.secret)
                if not block.reward or block.reward == "coin":
                    self._collect_coin(block.x + block.w / 2, block.y, False, None)
                else:
                    self.items.append(
                        Item(
                            id=f"item-{block.id}", kind=block.reward, x=block.x + (block.w - 24) / 2,
                            y=block.y - 26, w=24, h=24, vx=55, vy=-100,
                        )
                    )
                    self.emit("sprout", x=block.x + block.w / 2, y=block.y, ref=block.reward)
            elif block.kind == "brick" and p.power != "small":
                block.alive = False
                self.score += 50
                self.burst(block.x + block.w / 2, block.y, "#cf8f60", 14, kind="debris")
                self.emit("brick", x=block.x + block.w / 2, y=block.y, ref=block.id)
            else:
                self.emit("bump", x=block.x + block.w / 2, y=block.y + block.h)
        for coin in self.coins:
            if not coin.collected and p.x < coin.x + coin.w and p.x + p.w > coin.x and p.y < coin.y + coin.h and p.y + p.h > coin.y:
                coin.collected = True
                self._collect_coin(coin.x, coin.y, coin.special, coin.id)
        for checkpoint in self.checkpoints:
            if not checkpoint.reached and p.x >= checkpoint.x and abs(p.y - checkpoint.y) < 100:
                checkpoint.reached = True
                if self.last_checkpoint is None or checkpoint.x >= self.last_checkpoint.x:
                    self.last_checkpoint = checkpoint
                self.emit("checkpoint", text="Checkpoint ativado", x=checkpoint.x, y=checkpoint.y, ref=checkpoint.id)
                self.burst(p.x, p.y, "#73ffe1")
        if inp.down and self.pipe_cooldown <= 0:
            for s in self.platforms:
                if (
                    s.kind == "pipe" and s.destination is not None
                    and p.x + p.w > s.x and p.x < s.x + s.w and abs(p.y + p.h - s.y) < 10
                ):
                    self._warp(s)
                    break

    def _warp(self, pipe: Platform) -> None:
        p = self.player
        assert pipe.destination is not None
        p.x, p.y = pipe.destination
        p.vx = p.vy = 0.0
        p.standing_on = None
        self.pipe_cooldown = 0.8
        self.camera.snap(self)
        first = pipe.secret is not None and pipe.secret not in self.secrets_found
        if pipe.secret:
            self._secret(pipe.secret)
        self.emit("secret" if first or pipe.secret is None else "warp",
                  text="Uma passagem secreta!" if first or pipe.secret is None else None, ref=pipe.id)
        self.burst(p.x, p.y, "#73ffe1")

    def _secret(self, secret_id: str) -> None:
        if secret_id not in self.secrets_found:
            self.secrets_found.add(secret_id)
            self.emit("secret_found", ref=secret_id)

    def _collect_coin(self, x: float, y: float, special: bool, coin_id: Optional[str]) -> None:
        if special:
            if coin_id:
                self.found.add(coin_id)
            self.score += 1000
            self.emit("relic", text="Relíquia encontrada!", x=x, y=y, ref=coin_id)
        else:
            self.coins_total += 1
            self.score += 100
            self.emit("coin", x=x, y=y)
            if self.coins_total % C.COINS_PER_LIFE == 0:
                self.lives += 1
                self.emit("life", text="100 moedas: vida extra!")
        self.burst(x, y, "#73ffe1" if special else "#ffd36e", 16 if special else 8, kind="glint")

    # ------------------------------------------------------------------ enemies
    def _activate_enemies(self) -> None:
        if not self.activation:
            for e in self.enemies:
                e.active = True
            return
        left = self.camera.x - ACTIVATION_MARGIN
        right = self.camera.x + C.VIEW_WIDTH + ACTIVATION_MARGIN
        top = self.camera.y - 400
        bottom = self.camera.y + C.VIEW_HEIGHT + 400
        for e in self.enemies:
            if not e.active and e.alive and e.x + e.w > left and e.x < right and e.y + e.h > top and e.y < bottom:
                e.active = True

    def bounce_player(self, e: Enemy) -> None:
        p = self.player
        p.vy = -C.STOMP_BOUNCE
        p.y = e.y - p.h - 1
        p.grounded = False
        p.standing_on = None

    def hit_enemy(self, e: Enemy, damage: int = 1, source: str = "stomp") -> bool:
        behavior = self.behaviors[e.species]
        if not e.alive or e.hit_timer > 0:
            return False
        if not behavior.can_take_damage(self, e, source) or not behavior.vulnerable_to(self, e, source):
            if source in ("fire", "shell"):
                self.emit("deflect", x=e.x + e.w / 2, y=e.y)
            return False
        profile = self.profiles[e.species]
        e.health -= damage
        e.hit_timer = 0.65
        self.burst(e.x + e.w / 2, e.y, "#ffdc87")
        if e.health <= 0:
            e.alive = False
            e.defeated = 1.2 if profile.boss else 0.6
            e.memory["defeat_kind"] = "squash" if source == "stomp" else "knock"
            e.vy = -260.0 if source != "stomp" else 0.0
            e.anim = "defeat"
            self.score += 5000 if profile.boss else profile.score
            behavior.on_defeated(self, e, source)
            if profile.boss:
                self.emit("boss", text="Guardião derrotado!", x=e.x, y=e.y, ref=e.species)
                self.shake = 0.3
                self.burst(e.x, e.y, "#73ffe1", 30)
            else:
                self.emit("stomp", x=e.x, y=e.y, ref=source)
        else:
            self.emit("stomp", x=e.x, y=e.y, ref=source)
            behavior.on_damaged(self, e, source)
        return True

    def _update_enemies(self, dt: float) -> None:
        player = self.player
        for e in self.enemies:
            if not e.alive or not e.active:
                continue
            behavior = self.behaviors[e.species]
            old_timer = e.timer
            e.timer += dt
            e.state_time += dt
            e.hit_timer = max(0.0, e.hit_timer - dt)
            behavior.update(self, e, dt, old_timer)
            if e.x < e.patrol[0]:
                e.x = e.patrol[0]
                e.facing = 1
            if e.x + e.w > e.patrol[1]:
                e.x = e.patrol[1] - e.w
                e.facing = -1
            area = self.level.area_at(e.x + e.w / 2, min(e.y, self.level.height - 1))
            if e.y > area.y + area.h + 80:
                e.alive = False
                continue
            if not behavior.tangible(self, e):
                continue
            if not (player.x < e.x + e.w and player.x + player.w > e.x and player.y < e.y + e.h and player.y + player.h > e.y):
                continue
            if self.status != "playing":
                continue
            if player.star > 0:
                self.hit_enemy(e, 2, "star")
                continue
            stomp = player.vy > 0 and player.y + player.h <= e.y + min(24.0, player.vy * dt + 15)
            if stomp and (behavior.stompable(self, e) or behavior.safe_top(self, e)):
                behavior.on_stomp(self, e)
            else:
                behavior.on_touch(self, e)

    # ------------------------------------------------------------------ powers, items and shots
    def grant_power(self, kind: str) -> None:
        p = self.player
        if kind == "grow" and p.power == "small":
            p.power = "grown"
            p.transform = 0.6
        elif kind == "fire":
            p.power = "fire"
            p.transform = 0.6
        elif kind == "star":
            p.star = C.STAR_DURATION
        elif kind == "heart":
            self.lives = min(C.LIVES_MAX, self.lives + 1)
            self.emit("life", text="Uma vida extra!")
        self.score += 250
        self.emit("power", text=POWER_TEXT.get(kind), ref=kind)
        self.burst(p.x, p.y, "#73ffe1")
        self._grow_safely()

    def _grow_safely(self) -> None:
        p = self.player
        if p.power == "small" or p.h == C.PLAYER_BIG_HEIGHT:
            return
        top = p.y - (C.PLAYER_BIG_HEIGHT - p.h)
        for s in self.index.query(p.x - 1, p.x + p.w + 1):
            if not s.alive or (s.kind == "hidden" and not s.used) or s.kind == "semisolid":
                continue
            if s.kind == "switch" and not s.active:
                continue
            if p.x < s.x + s.w and p.x + p.w > s.x and top < s.y + s.h and top + C.PLAYER_BIG_HEIGHT > s.y:
                return
        p.y = top
        p.h = C.PLAYER_BIG_HEIGHT

    def _update_powers(self, dt: float, inp: InputState) -> None:
        p = self.player
        self._grow_safely()
        for item in self.items:
            if not item.alive:
                continue
            item.age += dt
            item.vy = min(700.0, item.vy + C.GRAVITY * dt)
            before = item.vx
            move_body(item, self.index, dt)
            if before and item.vx == 0:
                item.vx = -before
            if item.y > self.level.height + 80:
                item.alive = False
            if overlaps(p, item):
                item.alive = False
                self.grant_power(item.kind)
        if inp.ability and p.power == "fire" and p.shoot_cooldown <= 0:
            self.projectiles.append(
                Projectile(
                    x=p.x + (p.w if p.facing > 0 else -10), y=p.y + p.h * 0.4, w=10, h=10,
                    vx=p.facing * 450.0, vy=-90.0, hostile=False, life=2.4, kind="fireball", gravity=600.0,
                )
            )
            p.shoot_cooldown = 0.3
            p.shot_flash = 0.18
            self.emit("shot", ref="player")
        for s in self.projectiles:
            if not s.alive:
                continue
            s.life -= dt
            s.age += dt
            if s.life <= 0:
                s.alive = False
                continue
            if s.gravity:
                s.vy += s.gravity * dt
            before = s.vx
            collision = move_body(s, self.index, dt)
            if before != 0 and s.vx == 0:
                s.alive = False
            if collision.grounded:
                if s.hostile:
                    s.alive = False
                    if s.kind == "thorn_acorn":
                        self.burst(s.x + s.w / 2, s.y + s.h, "#8a5a33", 8, kind="debris")
                else:
                    s.vy = -200.0
            if not s.alive:
                continue
            if s.hostile:
                if overlaps(s, p):
                    if s.stompable and p.vy > 0 and p.y + p.h <= s.y + 12:
                        s.alive = False
                        p.vy = -C.STOMP_BOUNCE
                        self.score += 100
                        self.emit("stomp", x=s.x, y=s.y, ref="shot")
                    elif p.star > 0:
                        s.alive = False
                    else:
                        self.hurt()
                        s.alive = False
            else:
                for e in self.enemies:
                    if e.alive and e.active and self.behaviors[e.species].tangible(self, e) and overlaps(s, e):
                        self.hit_enemy(e, 1, "fire")
                        s.alive = False
                        self.burst(s.x, s.y, "#ffb35c", 5)
                        break
        self.items = [i for i in self.items if i.alive]
        self.projectiles = [s for s in self.projectiles if s.alive]
        for h in self.hazards:
            hx, hy = h.position(self.elapsed)
            if p.x < hx + h.w and p.x + p.w > hx and p.y < hy + h.h and p.y + p.h > hy:
                if h.lethal:
                    self.die()
                else:
                    self.hurt()

    # ------------------------------------------------------------------ player state changes
    def hurt(self) -> None:
        p = self.player
        if self.status != "playing" or p.invulnerable > 0 or p.star > 0:
            return
        self.emit("hurt", x=p.x, y=p.y)
        self.shake = 0.12
        self.burst(p.x, p.y, "#ef9473")
        if p.power == "small":
            self.die()
            return
        if p.power == "fire":
            p.power = "grown"
        else:
            p.power = "small"
            p.y += p.h - C.PLAYER_SMALL_HEIGHT
            p.h = C.PLAYER_SMALL_HEIGHT
        p.invulnerable = 2.0
        p.damage_blink = 2.0
        p.hurt_flash = 0.45
        p.vx = -p.facing * 100.0

    def finish(self) -> None:
        if self.status != "playing":
            return
        self.status = "complete"
        self.player.animation = "win"
        self.score += int(self.time) * 10
        self.emit("complete", text="Fase concluída!", value=self.score - self.level_start_score)

    def die(self) -> None:
        if self.status != "playing":
            return
        self.lives -= 1
        self.deaths += 1
        self.status = "dead"
        self.player.animation = "dead"
        self.transition = 1.1
        self.emit("death", x=self.player.x, y=self.player.y)

    def respawn(self) -> None:
        if self.lives <= 0:
            self.status = "gameover"
            return
        point = self.last_checkpoint or self.level.spawn
        self._spawn(point.x, point.y)
        self.status = "playing"
        self.time = max(self.time, 90.0)
        self.projectiles = []
        self.pipe_cooldown = 0.0

    # ------------------------------------------------------------------ helpers for tools/tests
    def run(self, seconds: float, inp: InputState) -> None:
        for _ in range(int(round(seconds / C.FIXED_DT))):
            self.update(C.FIXED_DT, inp)

    def alive_enemies(self) -> Iterable[Enemy]:
        return (e for e in self.enemies if e.alive)

