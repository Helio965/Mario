"""Tipos de dados da simulação (port fiel de ``src/core/types.ts``).

Nenhum módulo deste pacote importa pygame: a simulação é Python puro e
determinística, testável sem janela, áudio ou sistema de arquivos.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

PlatformKind = Literal["ground", "brick", "question", "hidden", "moving", "crumble", "pipe", "ice"]
Power = Literal["small", "grown", "fire"]
ItemKind = Literal["grow", "fire", "star", "heart"]
EnemyKind = Literal["walker", "shell", "flyer", "shooter", "armored", "boss"]
EnemyState = Literal["walk", "shell", "slide"]
HazardKind = Literal["lava", "water", "spikes", "moving"]
Weather = Literal["none", "sand", "snow", "spores", "embers"]
GameStatus = Literal["playing", "paused", "dead", "gameover", "complete"]
PlayerAnimation = Literal["idle", "walk", "run", "jump", "fall", "hurt", "dead", "win"]
EventType = Literal[
    "jump",
    "coin",
    "relic",
    "block",
    "power",
    "hurt",
    "death",
    "stomp",
    "shot",
    "checkpoint",
    "secret",
    "complete",
    "boss",
    "life",
]

PLATFORM_KINDS: tuple[str, ...] = (
    "ground",
    "brick",
    "question",
    "hidden",
    "moving",
    "crumble",
    "pipe",
    "ice",
)
ITEM_KINDS: tuple[str, ...] = ("grow", "fire", "star", "heart")
ENEMY_KINDS: tuple[str, ...] = ("walker", "shell", "flyer", "shooter", "armored", "boss")
HAZARD_KINDS: tuple[str, ...] = ("lava", "water", "spikes", "moving")
EVENT_TYPES: tuple[str, ...] = (
    "jump",
    "coin",
    "relic",
    "block",
    "power",
    "hurt",
    "death",
    "stomp",
    "shot",
    "checkpoint",
    "secret",
    "complete",
    "boss",
    "life",
)


@dataclass(slots=True)
class Vec:
    x: float = 0.0
    y: float = 0.0


@dataclass(slots=True)
class Rect:
    """Retângulo mutável usado por colisões transitórias (saída, perigos móveis)."""

    x: float
    y: float
    w: float
    h: float


@dataclass(slots=True)
class Motion:
    axis: Literal["x", "y"]
    range: float
    speed: float
    phase: float = 0.0


@dataclass(slots=True)
class PlatformSpec:
    id: str
    kind: PlatformKind
    x: float
    y: float
    w: float
    h: float
    reward: str | None = None  # ItemKind | "coin"
    motion: Motion | None = None
    destination: Vec | None = None
    return_point: Vec | None = None


@dataclass(slots=True)
class Platform:
    """Plataforma em execução: especificação + estado mutável."""

    id: str
    kind: PlatformKind
    x: float
    y: float
    w: float
    h: float
    reward: str | None
    motion: Motion | None
    destination: Vec | None
    return_point: Vec | None
    start_x: float
    start_y: float
    dx: float = 0.0
    dy: float = 0.0
    used: bool = False
    alive: bool = True
    bump: float = 0.0
    crumble: float = 0.0
    respawn: float = 0.0

    @classmethod
    def from_spec(cls, spec: PlatformSpec) -> Platform:
        return cls(
            id=spec.id,
            kind=spec.kind,
            x=spec.x,
            y=spec.y,
            w=spec.w,
            h=spec.h,
            reward=spec.reward,
            motion=spec.motion,
            destination=spec.destination,
            return_point=spec.return_point,
            start_x=spec.x,
            start_y=spec.y,
        )


@dataclass(slots=True)
class CoinSpec:
    id: str
    x: float
    y: float
    w: float
    h: float
    special: bool = False


@dataclass(slots=True)
class Coin:
    id: str
    x: float
    y: float
    w: float
    h: float
    special: bool = False
    collected: bool = False


@dataclass(slots=True)
class EnemySpec:
    id: str
    kind: EnemyKind
    x: float
    y: float
    w: float
    h: float
    patrol: list[float]
    hp: int | None = None


@dataclass(slots=True)
class Enemy:
    id: str
    kind: EnemyKind
    x: float
    y: float
    w: float
    h: float
    patrol: list[float]
    hp: int | None
    vx: float
    vy: float
    alive: bool
    health: int
    facing: int
    timer: float
    hit_timer: float
    state: EnemyState
    origin_y: float
    grounded: bool


@dataclass(slots=True)
class ItemSpec:
    id: str
    kind: ItemKind
    x: float
    y: float
    w: float
    h: float


@dataclass(slots=True)
class Item:
    id: str
    kind: ItemKind
    x: float
    y: float
    w: float
    h: float
    vx: float = 0.0
    vy: float = 0.0
    alive: bool = True


@dataclass(slots=True)
class Projectile:
    x: float
    y: float
    w: float
    h: float
    vx: float
    vy: float
    hostile: bool
    life: float
    alive: bool = True


@dataclass(slots=True)
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    life: float
    color: str
    size: float


@dataclass(slots=True)
class Hazard:
    kind: HazardKind
    x: float
    y: float
    w: float
    h: float
    range: float | None = None
    speed: float | None = None


@dataclass(slots=True)
class Hint:
    x: float
    text: str


@dataclass(slots=True)
class Level:
    id: str
    name: str
    world: int
    stage: int
    width: float
    height: float
    time: float
    spawn: Vec
    checkpoint: Vec
    exit: Vec
    platforms: list[PlatformSpec] = field(default_factory=list)
    coins: list[CoinSpec] = field(default_factory=list)
    enemies: list[EnemySpec] = field(default_factory=list)
    items: list[ItemSpec] = field(default_factory=list)
    hazards: list[Hazard] = field(default_factory=list)
    hints: list[Hint] = field(default_factory=list)


@dataclass(slots=True)
class Theme:
    name: str
    subtitle: str
    sky: str
    far: str
    near: str
    ground: str
    top: str
    accent: str
    weather: Weather


@dataclass(slots=True)
class Player:
    x: float
    y: float
    w: float = 22
    h: float = 30
    vx: float = 0.0
    vy: float = 0.0
    facing: int = 1
    grounded: bool = False
    power: Power = "small"
    invulnerable: float = 1.5
    star: float = 0.0
    coyote: float = 0.0
    buffer: float = 0.0
    shoot_cooldown: float = 0.0
    standing_on: str | None = None
    animation: PlayerAnimation = "idle"


@dataclass(slots=True)
class InputState:
    left: bool = False
    right: bool = False
    jump: bool = False
    run: bool = False
    ability: bool = False
    down: bool = False
    pause: bool = False
    pause_pressed: bool = False

    def copy(self, **changes: bool) -> InputState:
        return InputState(
            left=changes.get("left", self.left),
            right=changes.get("right", self.right),
            jump=changes.get("jump", self.jump),
            run=changes.get("run", self.run),
            ability=changes.get("ability", self.ability),
            down=changes.get("down", self.down),
            pause=changes.get("pause", self.pause),
            pause_pressed=changes.get("pause_pressed", self.pause_pressed),
        )


EMPTY_INPUT = InputState()


@dataclass(slots=True)
class GameEvent:
    type: EventType
    x: float | None = None
    y: float | None = None
    text: str | None = None
    value: float | None = None
