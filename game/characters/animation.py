"""Máquina de estados de animação do personagem.

Observa a física a cada passo e os eventos do jogo para produzir um estado
corporal legível (preparação do salto, ápice, aterrissagem forte, derrapagem,
agachamento, dano, vitória…), camadas sobrepostas (piscar, invencibilidade,
estrela) e deformação squash & stretch. É Python puro: a renderização só lê
``state``, ``frame``, ``squash`` e ``overlays``.

Os estados cobrem o catálogo pedido: idle, respiração (quadros do idle),
piscar (camada), olhar ao redor, caminhada, corrida, aceleração,
desaceleração, mudança de direção, derrapagem, agachamento, preparação do
salto, impulso, subida, ápice, queda, aterrissagem, aterrissagem forte, dano,
atordoamento, invencibilidade (camada), ataque, transformação, vitória,
derrota, interação com NPC, entrada/saída de passagem e natação.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Protocol


class AnimState(StrEnum):
    IDLE = "idle"
    LOOK_AROUND = "look_around"
    WALK = "walk"
    RUN = "run"
    ACCELERATE = "accelerate"
    DECELERATE = "decelerate"
    TURN = "turn"
    SKID = "skid"
    CROUCH = "crouch"
    JUMP_PREP = "jump_prep"
    JUMP_LAUNCH = "jump_launch"
    RISE = "rise"
    APEX = "apex"
    FALL = "fall"
    LAND = "land"
    LAND_HARD = "land_hard"
    HURT = "hurt"
    STUNNED = "stunned"
    ATTACK = "attack"
    TRANSFORM = "transform"
    WIN = "win"
    DEAD = "dead"
    TALK = "talk"
    PIPE_ENTER = "pipe_enter"
    PIPE_EXIT = "pipe_exit"
    SWIM = "swim"


@dataclass(slots=True, frozen=True)
class ClipSpec:
    """Quadros e cadência de um estado (``fps`` 0 = quadro fixo, ``loop`` False = congela no fim)."""

    frames: int
    fps: float
    loop: bool = True


# Cadências sugeridas pela pesquisa de animação (ajustáveis por personagem).
DEFAULT_CLIPS: dict[AnimState, ClipSpec] = {
    AnimState.IDLE: ClipSpec(4, 3),  # respiração em 4 quadros
    AnimState.LOOK_AROUND: ClipSpec(6, 5, loop=False),
    AnimState.WALK: ClipSpec(6, 10),
    AnimState.RUN: ClipSpec(6, 16),
    AnimState.ACCELERATE: ClipSpec(3, 12, loop=False),
    AnimState.DECELERATE: ClipSpec(2, 8, loop=False),
    AnimState.TURN: ClipSpec(2, 16, loop=False),
    AnimState.SKID: ClipSpec(2, 12),
    AnimState.CROUCH: ClipSpec(2, 8, loop=False),
    AnimState.JUMP_PREP: ClipSpec(1, 0),
    AnimState.JUMP_LAUNCH: ClipSpec(1, 0),
    AnimState.RISE: ClipSpec(2, 8, loop=False),
    AnimState.APEX: ClipSpec(1, 0),
    AnimState.FALL: ClipSpec(2, 8, loop=False),
    AnimState.LAND: ClipSpec(2, 16, loop=False),
    AnimState.LAND_HARD: ClipSpec(3, 12, loop=False),
    AnimState.HURT: ClipSpec(2, 10),
    AnimState.STUNNED: ClipSpec(4, 8),
    AnimState.ATTACK: ClipSpec(3, 18, loop=False),
    AnimState.TRANSFORM: ClipSpec(4, 14),
    AnimState.WIN: ClipSpec(4, 6, loop=False),
    AnimState.DEAD: ClipSpec(1, 0),
    AnimState.TALK: ClipSpec(4, 6),
    AnimState.PIPE_ENTER: ClipSpec(3, 10, loop=False),
    AnimState.PIPE_EXIT: ClipSpec(3, 10, loop=False),
    AnimState.SWIM: ClipSpec(4, 8),
}

# Durações fixas dos estados transitórios (segundos).
JUMP_PREP_TIME = 0.05
JUMP_LAUNCH_TIME = 0.06
LAND_TIME = 0.09
LAND_HARD_TIME = 0.2
HARD_LANDING_SPEED = 620.0
HURT_TIME = 0.45
ATTACK_TIME = 0.2
TRANSFORM_TIME = 0.5
TURN_TIME = 0.1
PIPE_TIME = 0.35
LOOK_AROUND_AFTER = 3.5
BLINK_INTERVAL = 3.1
BLINK_DURATION = 0.12
APEX_SPEED = 60.0
SKID_MIN_SPEED = 120.0
IDLE_SPEED = 15.0
RUN_SPEED = 260.0
ACCELERATE_TIME = 0.15


class PhysicsView(Protocol):
    """Fatia do estado do jogador que a animação observa."""

    vx: float
    vy: float
    grounded: bool
    facing: int
    invulnerable: float
    star: float


@dataclass(slots=True)
class Overlays:
    blink: bool = False
    invincible_flicker: bool = False
    star_aura: bool = False


@dataclass(slots=True)
class AnimationController:
    clips: dict[AnimState, ClipSpec] = field(default_factory=lambda: dict(DEFAULT_CLIPS))
    state: AnimState = AnimState.IDLE
    time_in_state: float = 0.0
    clock: float = 0.0
    frame: int = 0
    facing: int = 1
    squash_x: float = 1.0
    squash_y: float = 1.0
    overlays: Overlays = field(default_factory=Overlays)
    idle_time: float = 0.0
    blink_clock: float = 0.0
    _was_grounded: bool = True
    _last_vy: float = 0.0
    _last_facing: int = 1
    _pending: AnimState | None = None
    _pending_until: float = 0.0
    _hold_until: float = 0.0
    _underwater: bool = False
    _crouching: bool = False

    # ------------------------------------------------------------- entrada
    def notify(self, event_type: str, power_changed: bool = False) -> None:
        """Eventos do jogo relevantes para a animação (``GameEvent.type``)."""
        if event_type == "jump":
            self._hold(
                AnimState.JUMP_PREP,
                JUMP_PREP_TIME,
                then=AnimState.JUMP_LAUNCH,
                then_time=JUMP_LAUNCH_TIME,
            )
        elif event_type == "hurt":
            self._hold(AnimState.HURT, HURT_TIME)
        elif event_type == "death":
            self._set(AnimState.DEAD)
            self._hold_until = float("inf")
        elif event_type == "complete":
            self._set(AnimState.WIN)
            self._hold_until = float("inf")
        elif event_type == "shot":
            if self.state not in (AnimState.DEAD, AnimState.WIN, AnimState.HURT):
                self._hold(AnimState.ATTACK, ATTACK_TIME)
        elif event_type == "power" and power_changed:
            self._hold(AnimState.TRANSFORM, TRANSFORM_TIME)
        elif event_type == "secret":
            self._hold(
                AnimState.PIPE_ENTER, PIPE_TIME, then=AnimState.PIPE_EXIT, then_time=PIPE_TIME
            )
        elif event_type == "talk":
            self._set(AnimState.TALK)
            self._hold_until = float("inf")
        elif event_type == "talk_end" and self.state == AnimState.TALK:
            self._hold_until = 0.0
            self._set(AnimState.IDLE)

    def set_underwater(self, underwater: bool) -> None:
        self._underwater = underwater

    def set_crouching(self, crouching: bool) -> None:
        self._crouching = crouching

    # ---------------------------------------------------------------- passo
    def update(self, dt: float, body: PhysicsView, direction: int = 0) -> AnimState:
        self.clock += dt
        self.time_in_state += dt
        self.blink_clock += dt
        self.facing = body.facing
        self._update_overlays(body)
        landed = body.grounded and not self._was_grounded
        fall_speed = self._last_vy
        self._was_grounded = body.grounded
        self._last_vy = body.vy

        # Estados retidos (eventos) têm prioridade até expirar.
        if self.clock < self._hold_until:
            self._tick_frame(dt)
            self._update_squash(dt, body)
            return self.state
        if self._pending is not None:
            self._set(self._pending)
            self._hold_until = self.clock + self._pending_until
            self._pending = None
            self._tick_frame(dt)
            return self.state
        if self.state in (AnimState.DEAD, AnimState.WIN, AnimState.TALK):
            self._tick_frame(dt)
            return self.state

        if landed and not self._underwater:
            hard = fall_speed >= HARD_LANDING_SPEED
            self._hold(
                AnimState.LAND_HARD if hard else AnimState.LAND,
                LAND_HARD_TIME if hard else LAND_TIME,
            )
            self.squash_x, self.squash_y = (1.3, 0.7) if hard else (1.15, 0.85)
            self._tick_frame(dt)
            return self.state

        target = self._choose_state(body, direction)
        if target != self.state:
            if target == AnimState.TURN:
                self._hold(AnimState.TURN, TURN_TIME)
            else:
                self._set(target)
        self._tick_frame(dt)
        self._update_squash(dt, body)
        return self.state

    # ------------------------------------------------------------- decisões
    def _choose_state(self, body: PhysicsView, direction: int) -> AnimState:
        speed = abs(body.vx)
        if self._underwater:
            return AnimState.SWIM
        if not body.grounded:
            if body.vy < -APEX_SPEED:
                return AnimState.RISE
            if body.vy > APEX_SPEED:
                return AnimState.FALL
            return AnimState.APEX
        if self._crouching and direction == 0:
            return AnimState.CROUCH
        if body.facing != self._last_facing:
            self._last_facing = body.facing
            if speed < SKID_MIN_SPEED and direction != 0:
                return AnimState.TURN
        if direction != 0 and speed >= SKID_MIN_SPEED and (body.vx > 0) != (direction > 0):
            return AnimState.SKID
        if direction == 0 and speed > IDLE_SPEED:
            return AnimState.DECELERATE
        if speed <= IDLE_SPEED:
            self.idle_time += 0.0  # mantido pelo relógio de estado
            if (
                self.state in (AnimState.IDLE, AnimState.LOOK_AROUND)
                and self.time_in_state >= LOOK_AROUND_AFTER
            ):
                return AnimState.LOOK_AROUND
            if self.state == AnimState.LOOK_AROUND and self.time_in_state < LOOK_AROUND_AFTER:
                return AnimState.LOOK_AROUND
            return AnimState.IDLE
        if speed > RUN_SPEED:
            return AnimState.RUN
        if (
            self.state in (AnimState.IDLE, AnimState.LOOK_AROUND, AnimState.ACCELERATE)
            and self.time_in_state < ACCELERATE_TIME
            and speed < RUN_SPEED * 0.5
        ):
            return AnimState.ACCELERATE
        return AnimState.WALK

    # ------------------------------------------------------------ auxiliares
    def _set(self, state: AnimState) -> None:
        if state != self.state:
            self.state = state
            self.time_in_state = 0.0
            self.frame = 0

    def _hold(
        self,
        state: AnimState,
        seconds: float,
        then: AnimState | None = None,
        then_time: float = 0.0,
    ) -> None:
        self._set(state)
        self._hold_until = self.clock + seconds
        self._pending = then
        self._pending_until = then_time

    def _tick_frame(self, dt: float) -> None:
        clip = self.clips.get(self.state, ClipSpec(1, 0))
        if clip.fps <= 0 or clip.frames <= 1:
            self.frame = 0
            return
        raw = int(self.time_in_state * clip.fps)
        self.frame = raw % clip.frames if clip.loop else min(raw, clip.frames - 1)

    def _update_overlays(self, body: PhysicsView) -> None:
        self.overlays.star_aura = body.star > 0
        self.overlays.invincible_flicker = (
            body.invulnerable > 0 and body.star <= 0 and int(self.clock * 15) % 2 == 0
        )
        if self.blink_clock >= BLINK_INTERVAL + BLINK_DURATION:
            self.blink_clock = 0.0
        self.overlays.blink = (
            BLINK_INTERVAL <= self.blink_clock < BLINK_INTERVAL + BLINK_DURATION
            and self.state
            in (
                AnimState.IDLE,
                AnimState.LOOK_AROUND,
                AnimState.WALK,
                AnimState.TALK,
            )
        )

    def _update_squash(self, dt: float, body: PhysicsView) -> None:
        if self.state in (AnimState.JUMP_PREP,):
            self.squash_x, self.squash_y = 1.2, 0.8
        elif self.state in (AnimState.JUMP_LAUNCH, AnimState.RISE) and body.vy < -400:
            self.squash_x, self.squash_y = 0.85, 1.15
        # Relaxa para 1 com constante de tempo curta.
        k = min(1.0, dt * 14)
        self.squash_x += (1.0 - self.squash_x) * k
        self.squash_y += (1.0 - self.squash_y) * k
