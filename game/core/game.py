"""Laço de simulação em passo fixo (port fiel de ``src/core/game.ts``)."""

from __future__ import annotations

import math

from game.characters.abilities import update_powers
from game.core.interactions import burst, interact_world, update_platforms
from game.core.types import (
    Coin,
    Enemy,
    GameEvent,
    GameStatus,
    InputState,
    Item,
    Level,
    Particle,
    Platform,
    Player,
    Projectile,
    Rect,
    Vec,
)
from game.enemies.legacy import update_enemies
from game.physics.collision import approach, move_body, overlaps
from game.physics.movement import FIXED_DT, LEGACY_PROFILE, MovementProfile

VIEW_WIDTH = 960
VIEW_HEIGHT = 540


class Game:
    """Estado completo de uma partida: fase carregada, jogador, entidades, eventos."""

    def __init__(
        self, levels: list[Level] | None = None, profile: MovementProfile = LEGACY_PROFILE
    ) -> None:
        if levels is None:
            from game.levels.loader import load_levels

            levels = load_levels()
        self.levels: list[Level] = levels
        self.profile = profile
        self.level: Level = levels[0]
        self.level_index = 0
        self.player: Player = Player(x=0, y=0)
        self.platforms: list[Platform] = []
        self.coins: list[Coin] = []
        self.enemies: list[Enemy] = []
        self.items: list[Item] = []
        self.projectiles: list[Projectile] = []
        self.particles: list[Particle] = []
        self.events: list[GameEvent] = []
        self.camera = Vec(0, 0)
        self.status: GameStatus = "playing"
        self.time = 300.0
        self.lives = 5
        self.score = 0
        self.level_start_score = 0
        self.coins_total = 0
        self.checkpoint_reached = False
        self.found_relic = False
        self.elapsed = 0.0
        self.shake = 0.0
        self._accumulator = 0.0
        self._previous_jump = False
        self._transition = 0.0
        self.pipe_cooldown = 0.0
        self.load(0)

    # ----------------------------------------------------------------- ciclo
    def start(self, index: int = 0) -> None:
        self.lives = 5
        self.score = 0
        self.coins_total = 0
        self.load(index)

    def load(self, index: int) -> None:
        self.level_start_score = self.score
        self.level_index = max(0, min(index, len(self.levels) - 1))
        self.level = self.levels[self.level_index]
        self.platforms = [Platform.from_spec(p) for p in self.level.platforms]
        self.coins = [Coin(c.id, c.x, c.y, c.w, c.h, c.special, False) for c in self.level.coins]
        self.items = [Item(i.id, i.kind, i.x, i.y, i.w, i.h, 0, 0, True) for i in self.level.items]
        self.enemies = [
            Enemy(
                id=e.id,
                kind=e.kind,
                x=e.x,
                y=e.y,
                w=e.w,
                h=e.h,
                patrol=list(e.patrol),
                hp=e.hp,
                vx=-60,
                vy=0,
                alive=True,
                health=e.hp
                if e.hp is not None
                else (2 if e.kind == "armored" else 4 if e.kind == "boss" else 1),
                facing=-1,
                timer=0,
                hit_timer=0,
                state="walk",
                origin_y=e.y,
                grounded=False,
            )
            for e in self.level.enemies
        ]
        self.projectiles = []
        self.particles = []
        self.events = []
        self.checkpoint_reached = False
        self.found_relic = False
        self.elapsed = 0.0
        self.time = self.level.time
        self.status = "playing"
        self._accumulator = 0.0
        self._previous_jump = False
        self._transition = 0.0
        self.spawn(self.level.spawn.x, self.level.spawn.y)

    def spawn(self, x: float, y: float) -> None:
        self.player = Player(x=x, y=y)
        self.camera = Vec(max(0, x - 240), 0)

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

    def update(self, dt: float, input_state: InputState) -> None:
        if self.status == "paused" or self.status == "gameover":
            return
        if self.status == "complete":
            self.elapsed += min(dt, 0.25)
            for v in self.particles:
                v.life -= dt
                v.x += v.vx * dt
                v.y += v.vy * dt
            self.particles = [v for v in self.particles if v.life > 0]
            return
        self._accumulator += min(dt, 0.25)
        while self._accumulator >= FIXED_DT:
            self.step(FIXED_DT, input_state)
            self._accumulator -= FIXED_DT

    # ------------------------------------------------------------------ passo
    def step(self, dt: float, input_state: InputState) -> None:
        self.elapsed += dt
        if self.status == "dead":
            self._transition -= dt
            if self._transition <= 0:
                self.respawn()
            return
        if self.status != "playing":
            return
        self.time = max(0, self.time - dt)
        self.pipe_cooldown = max(0, self.pipe_cooldown - dt)
        update_platforms(self, dt)
        p = self.player
        prof = self.profile
        p.invulnerable = max(0, p.invulnerable - dt)
        p.star = max(0, p.star - dt)
        p.shoot_cooldown = max(0, p.shoot_cooldown - dt)
        self.shake = max(0, self.shake - dt)
        direction = int(input_state.right) - int(input_state.left)
        floor = next((s for s in self.platforms if s.id == p.standing_on), None)
        friction = (
            prof.ice_friction if floor is not None and floor.kind == "ice" else prof.ground_friction
        )
        if direction:
            rate = prof.ground_acceleration if p.grounded else prof.air_acceleration
        else:
            rate = friction if p.grounded else prof.air_friction
        p.vx = approach(
            p.vx, direction * (prof.run_speed if input_state.run else prof.walk_speed), rate * dt
        )
        if direction:
            p.facing = direction
        if input_state.jump and not self._previous_jump:
            p.buffer = prof.jump_buffer
        self._previous_jump = input_state.jump
        p.buffer = max(0, p.buffer - dt)
        p.coyote = prof.coyote_time if p.grounded else max(0, p.coyote - dt)
        if p.buffer > 0 and p.coyote > 0:
            p.vy = -prof.jump_speed
            p.grounded = False
            p.standing_on = None
            p.coyote = 0
            p.buffer = 0
            self.events.append(GameEvent("jump"))
        if not input_state.jump and p.vy < -prof.jump_cut_speed:
            p.vy = -prof.jump_cut_speed
        p.vy = min(prof.terminal_velocity, p.vy + prof.gravity * dt)
        collision = move_body(p, self.platforms, dt)
        p.grounded = collision.grounded
        p.standing_on = collision.standing_on
        p.x = max(0, min(p.x, self.level.width - p.w))
        self.interactions(dt, input_state, collision.heads)
        if p.y > self.level.height + 100 or self.time <= 0:
            self.die()
        if self.status == "playing":
            if p.invulnerable > 0 and p.invulnerable < 1.2:
                p.animation = "hurt"
            elif not p.grounded:
                p.animation = "jump" if p.vy < 0 else "fall"
            elif abs(p.vx) > 260:
                p.animation = "run"
            elif abs(p.vx) > 15:
                p.animation = "walk"
            else:
                p.animation = "idle"
        target_x = max(
            0, min(self.level.width - VIEW_WIDTH, p.x - 310 + p.vx * prof.camera_lookahead)
        )
        target_y = max(0, min(self.level.height - VIEW_HEIGHT, p.y - 250))
        self.camera.x += (target_x - self.camera.x) * (1 - math.exp(-6 * dt))
        self.camera.y += (target_y - self.camera.y) * (1 - math.exp(-6 * dt))

    def interactions(self, dt: float, input_state: InputState, heads: list[Platform]) -> None:
        interact_world(self, input_state, heads)
        update_enemies(self, dt)
        update_powers(self, dt, input_state)
        exit_box = Rect(x=self.level.exit.x - 12, y=self.level.exit.y - 110, w=44, h=110)
        if overlaps(self.player, exit_box) and not any(
            e.kind == "boss" and e.alive for e in self.enemies
        ):
            self.finish()
        for particle in self.particles:
            particle.life -= dt
            particle.x += particle.vx * dt
            particle.y += particle.vy * dt
            particle.vy += 300 * dt
        self.particles = [v for v in self.particles if v.life > 0]

    # ---------------------------------------------------------------- estado
    def hurt(self) -> None:
        p = self.player
        if self.status != "playing" or p.invulnerable > 0 or p.star > 0:
            return
        self.events.append(GameEvent("hurt"))
        self.shake = 0.12
        burst(self, p.x, p.y, "#ef9473")
        if p.power == "small":
            self.die()
            return
        if p.power == "fire":
            p.power = "grown"
        else:
            p.power = "small"
            p.y += p.h - 30
            p.h = 30
        p.invulnerable = 2
        p.vx = -p.facing * 100

    def finish(self) -> None:
        if self.status != "playing":
            return
        self.status = "complete"
        self.player.animation = "win"
        self.score += math.floor(self.time) * 10
        self.events.append(
            GameEvent("complete", text="Fase concluída!", value=self.score - self.level_start_score)
        )

    def die(self) -> None:
        if self.status != "playing":
            return
        self.lives -= 1
        self.status = "dead"
        self.player.animation = "dead"
        self._transition = 1.1
        self.events.append(GameEvent("death"))

    def respawn(self) -> None:
        if self.lives <= 0:
            self.status = "gameover"
            return
        point = self.level.checkpoint if self.checkpoint_reached else self.level.spawn
        self.spawn(point.x, point.y)
        self.status = "playing"
        self.time = max(self.time, 90)
        self.projectiles = []
        self.pipe_cooldown = 0

    # -------------------------------------------------------------- consultas
    def boss(self) -> Enemy | None:
        return next((e for e in self.enemies if e.kind == "boss" and e.alive), None)
