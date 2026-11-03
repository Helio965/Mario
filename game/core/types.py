"""Tipos de dados da simulação (port fiel de ``src/core/types.ts``).

Nenhum módulo deste pacote importa pygame: a simulação é Python puro e
determinística, testável sem janela, áudio ou sistema de arquivos.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

PlatformKind = Literal["ground", "brick", "question", "hidden", "moving", "crumble", "pipe", "ice"]
Power = Literal["small", "grown", "fire"]
ItemKind = Literal["grow", "fire", "star", "heart"]
# Tipos legados (comportamento em game/enemies/legacy.py); arquétipos modernos são
# registrados em game/enemies/registry.py e validados por ``known_enemy_kinds()``.
EnemyKind = str
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
    "boss_intro",
    "boss_phase",
    "talk",
    "npc_say",
    "kick",
    "ricochet",
    "impact",
    "explode",
    "telegraph",
    "boss_telegraph",
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
    "boss_intro",
    "boss_phase",
    "talk",
    "npc_say",
    "kick",
    "ricochet",
    "impact",
    "explode",
    "telegraph",
    "boss_telegraph",
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
    behavior: Any = None  # arquétipo moderno (game/enemies/behaviors.py) ou None
    anim: str = "walk"  # estado de animação exposto à renderização
    telegraph: bool = False  # sinalização visível de ataque iminente
    stompable: bool = True


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
    gravity: float = 0.0  # projéteis em arco (martelo, gota de magma); 0 = comportamento legado
    owner: str | None = None  # id do inimigo/chefe que criou o projétil (orçamento de perigos)


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
class RoutineStep:
    """Passo de rotina de NPC: walk (x, speed), wait (seconds), look (facing), emote (expression, seconds), say (reaction)."""

    action: str
    x: float = 0.0
    speed: float = 60.0
    seconds: float = 1.0
    facing: int = 1
    expression: str = "neutral"
    reaction: str = ""


@dataclass(slots=True)
class NpcSpec:
    id: str
    kind: str
    x: float
    y: float
    w: float = 24.0
    h: float = 32.0
    facing: int = 1
    routine: list[RoutineStep] = field(default_factory=list)
    loop: bool = True
    dialogue: str | None = None
    talk_once: bool = False
    reactions: str = ""  # personagem do banco de reações (data/locales)
    observe_distance: float = 90.0


@dataclass(slots=True)
class Npc:
    id: str
    kind: str
    x: float
    y: float
    w: float
    h: float
    facing: int
    routine: list[RoutineStep]
    loop: bool
    dialogue: str | None
    talk_once: bool
    reactions: str
    observe_distance: float
    vx: float = 0.0
    vy: float = 0.0
    grounded: bool = False
    state: str = "routine"  # routine | observe | talk | done
    step_index: int = 0
    step_clock: float = 0.0
    expression: str = "neutral"
    talked: bool = False
    anim: str = "idle"
    bubble: str | None = None  # contexto da última fala curta (para a interface)
    bubble_time: float = 0.0

    @classmethod
    def from_spec(cls, spec: NpcSpec) -> Npc:
        return cls(
            id=spec.id,
            kind=spec.kind,
            x=spec.x,
            y=spec.y,
            w=spec.w,
            h=spec.h,
            facing=spec.facing,
            routine=list(spec.routine),
            loop=spec.loop,
            dialogue=spec.dialogue,
            talk_once=spec.talk_once,
            reactions=spec.reactions,
            observe_distance=spec.observe_distance,
        )


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
    npcs: list[NpcSpec] = field(default_factory=list)


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
    run_grace: float = 0.0
    skidding: bool = False
    hit_ceiling: bool = False
    crouching: bool = False
    charge: float = 0.0  # salto carregado (Fagulha): tempo agachada parada
    charged: bool = False
    float_time: float = 0.0  # flutuação (Aurora): tempo restante no ar
    float_used: bool = False
    floating: bool = False
    stun: float = 0.0  # Pirilampo: sem controle após o empurrão


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
