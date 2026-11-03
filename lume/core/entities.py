"""Runtime entities of the simulation.

Level files describe *specs*; :mod:`lume.core.game` instantiates these mutable
runtime objects from them. Every class uses ``slots`` because the simulation
runs at 120 Hz and the campaign tests simulate thousands of seconds.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Optional

from .constants import PLAYER_SMALL_HEIGHT, PLAYER_WIDTH

PlatformKind = Literal[
    "ground",  # terrain body (any art style)
    "ledge",  # floating solid platform
    "brick",  # breakable when strong
    "question",  # reward block
    "hidden",  # invisible reward block, solid only from below until revealed
    "moving",  # solid platform that oscillates or orbits
    "crumble",  # gives way after standing on it, then respawns
    "pipe",  # solid; may warp
    "semisolid",  # one-way platform: solid only from above
    "conveyor",  # solid; carries bodies standing on it
    "spring",  # solid; launches bodies landing on it
    "switch",  # on/off block toggled by switch hits
]
SOLID_KINDS = frozenset(
    {"ground", "ledge", "brick", "question", "hidden", "moving", "crumble", "pipe", "conveyor", "spring", "switch"}
)
Power = Literal["small", "grown", "fire"]
ItemKind = Literal["grow", "fire", "star", "heart"]


@dataclass(slots=True)
class Motion:
    """Oscillation (``axis`` x/y, sine) or orbit (``axis`` = "circle")."""

    axis: str
    range: float
    speed: float
    phase: float = 0.0


@dataclass(slots=True)
class Platform:
    id: str
    kind: str
    x: float
    y: float
    w: float
    h: float
    style: str = ""
    surface: str = "normal"  # normal | ice | sticky
    reward: Optional[str] = None
    motion: Optional[Motion] = None
    destination: Optional[tuple[float, float]] = None
    return_point: Optional[tuple[float, float]] = None
    secret: Optional[str] = None
    surface_speed: float = 0.0  # conveyor belts
    bounce: float = 0.0  # springs
    group: str = ""  # switch blocks
    # runtime
    start_x: float = 0.0
    start_y: float = 0.0
    dx: float = 0.0
    dy: float = 0.0
    used: bool = False
    alive: bool = True
    bump: float = 0.0
    crumble: float = 0.0
    respawn: float = 0.0
    active: bool = True  # switch blocks: solid when active

    def __post_init__(self) -> None:
        self.start_x = self.x
        self.start_y = self.y

    @property
    def one_way(self) -> bool:
        return self.kind == "semisolid"

    @property
    def is_ice(self) -> bool:
        return self.surface == "ice"


@dataclass(slots=True)
class Coin:
    id: str
    x: float
    y: float
    w: float
    h: float
    special: bool = False  # relic / special collectible
    kind: str = "coin"
    collected: bool = False


@dataclass(slots=True)
class Item:
    id: str
    kind: str
    x: float
    y: float
    w: float = 24.0
    h: float = 24.0
    vx: float = 0.0
    vy: float = 0.0
    alive: bool = True
    age: float = 0.0


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
    kind: str = "orb"  # orb | fireball | sand | snowball | bolt | seed | bubble ...
    gravity: float = 0.0
    bounces: int = 0
    owner: str = ""
    age: float = 0.0
    stompable: bool = False


@dataclass(slots=True)
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    life: float
    color: str
    size: float
    kind: str = "spark"
    max_life: float = 0.0
    gravity: float = 300.0

    def __post_init__(self) -> None:
        if self.max_life <= 0:
            self.max_life = self.life


@dataclass(slots=True)
class Hazard:
    id: str
    kind: str  # lava | water | spikes | moving (orbiting flame) | firebar | thorns | electric
    x: float
    y: float
    w: float
    h: float
    range: float = 30.0
    speed: float = 1.0
    phase: float = 0.0
    lethal: bool = False  # lava/water pits kill directly
    style: str = ""  # art variant (e.g. "snowball")

    def position(self, elapsed: float) -> tuple[float, float]:
        if self.kind == "moving":
            import math

            return self.x + math.sin(elapsed * self.speed + self.phase) * self.range, self.y
        return self.x, self.y


@dataclass(slots=True)
class Zone:
    """Non-solid volume that changes physics or visibility."""

    id: str
    kind: str  # swim | current | wind | dark | quicksand | lowgrav
    x: float
    y: float
    w: float
    h: float
    force_x: float = 0.0
    force_y: float = 0.0
    period: float = 0.0  # >0: force pulses (wind gusts)
    duty: float = 1.0
    radius: float = 0.0  # visibility radius for dark zones
    phase: float = 0.0  # clock offset for periodic zones


@dataclass(slots=True)
class Checkpoint:
    id: str
    x: float
    y: float
    reached: bool = False


@dataclass(slots=True)
class Player:
    x: float
    y: float
    w: float = PLAYER_WIDTH
    h: float = PLAYER_SMALL_HEIGHT
    vx: float = 0.0
    vy: float = 0.0
    facing: int = 1
    grounded: bool = False
    power: str = "small"
    invulnerable: float = 1.5
    star: float = 0.0
    coyote: float = 0.0
    buffer: float = 0.0
    shoot_cooldown: float = 0.0
    standing_on: Optional[str] = None
    animation: str = "idle"
    anim_time: float = 0.0
    swimming: bool = False
    skid: float = 0.0
    land_impact: float = 0.0  # >0 right after landing; drives squash and dust
    air_time: float = 0.0
    transform: float = 0.0  # >0 while the growth/power-up animation plays
    shot_flash: float = 0.0
    hurt_flash: float = 0.0
    damage_blink: float = 0.0
    launched: bool = False  # spring launch: the jump-cut rule does not apply until the apex


@dataclass(slots=True)
class Enemy:
    id: str
    species: str
    x: float
    y: float
    w: float
    h: float
    patrol: tuple[float, float]
    hp: int = 1
    params: dict[str, Any] = field(default_factory=dict)
    # runtime
    vx: float = 0.0
    vy: float = 0.0
    alive: bool = True
    health: int = 1
    facing: int = -1
    timer: float = 0.0
    hit_timer: float = 0.0
    state: str = "walk"
    state_time: float = 0.0
    origin_x: float = 0.0
    origin_y: float = 0.0
    grounded: bool = False
    active: bool = False
    anim: str = "walk"
    defeated: float = 0.0  # >0 while the defeat animation plays
    memory: dict[str, Any] = field(default_factory=dict)

    @property
    def kind(self) -> str:
        """Behaviour family (kept for compatibility with legacy tests)."""
        return self.memory.get("family", self.species)

    def set_state(self, state: str) -> None:
        if state != self.state:
            self.state = state
            self.state_time = 0.0


@dataclass(slots=True)
class GameEvent:
    type: str
    x: Optional[float] = None
    y: Optional[float] = None
    text: Optional[str] = None
    value: Optional[float] = None
    ref: Optional[str] = None
