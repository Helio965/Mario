"""Behaviour base class, registry and shared movement helpers.

Each family is a small state machine. Species tune a family through
``EnemyProfile.params`` and per-instance ``EnemySpec.params``; the family also
publishes ``enemy.anim`` (animation state) so the renderer can pose the rig.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Type

from ..constants import GRAVITY, MAX_FALL_SPEED, STOMP_BOUNCE
from ..entities import Enemy
from ..physics import move_body, solid_at

if TYPE_CHECKING:  # pragma: no cover
    from ..game import Game
    from ..species import EnemyProfile

BEHAVIORS: dict[str, Type["Behavior"]] = {}


def register(name: str) -> Callable[[Type["Behavior"]], Type["Behavior"]]:
    def decorate(cls: Type["Behavior"]) -> Type["Behavior"]:
        cls.family = name
        BEHAVIORS[name] = cls
        return cls

    return decorate


class Behavior:
    family = "base"
    #: animation states this family can publish (subset must exist in the species)
    states: tuple[str, ...] = ("idle", "walk", "hurt", "defeat")

    def __init__(self, profile: "EnemyProfile") -> None:
        self.profile = profile

    # -- tuning -----------------------------------------------------------------
    def param(self, e: Enemy, key: str, default):
        if key in e.params:
            return e.params[key]
        return self.profile.params.get(key, default)

    def speed(self, e: Enemy) -> float:
        return float(self.param(e, "speed", self.profile.speed))

    # -- lifecycle --------------------------------------------------------------
    def spawn(self, game: "Game", e: Enemy) -> None:
        e.vx = -self.speed(e)
        e.facing = -1
        e.anim = "walk"

    def update(self, game: "Game", e: Enemy, dt: float, old_timer: float) -> None:
        raise NotImplementedError

    # -- contact rules ------------------------------------------------------------
    def tangible(self, game: "Game", e: Enemy) -> bool:
        """False while hidden/burrowed: no contact with the player at all."""
        return True

    def spiked(self, game: "Game", e: Enemy) -> bool:
        return "spiked_top" in self.profile.abilities

    def stompable(self, game: "Game", e: Enemy) -> bool:
        return "stomp" in self.profile.weaknesses and not self.spiked(game, e)

    def safe_top(self, game: "Game", e: Enemy) -> bool:
        """True for solid-topped obstacles (crushers) that can be stood on."""
        return False

    def vulnerable_to(self, game: "Game", e: Enemy, source: str) -> bool:
        if source == "star":
            return "star" in self.profile.weaknesses or not self.profile.boss
        if source == "shell":
            return "shell" in self.profile.weaknesses
        if source == "fire":
            return "fire" in self.profile.weaknesses
        if source == "explosion":
            return "explosion" in self.profile.weaknesses or "fire" in self.profile.weaknesses
        return True

    def can_take_damage(self, game: "Game", e: Enemy, source: str) -> bool:
        """Bosses override this to expose vulnerability windows."""
        return True

    def on_stomp(self, game: "Game", e: Enemy) -> None:
        game.bounce_player(e)
        game.hit_enemy(e, 1, "stomp")

    def on_touch(self, game: "Game", e: Enemy) -> None:
        game.hurt()

    def on_damaged(self, game: "Game", e: Enemy, source: str) -> None:
        """Called after health was reduced but the enemy survived."""

    def on_blocked(self, game: "Game", e: Enemy, source: str) -> None:
        """Called when a hit from ``source`` was refused (armour, helmets):
        bosses use it to react to shells or fire without taking damage."""

    def on_defeated(self, game: "Game", e: Enemy, source: str) -> None:
        """Called once when health reaches zero."""


def behavior_for(profile: "EnemyProfile") -> Behavior:
    cls = BEHAVIORS.get(profile.behavior)
    if cls is None:
        raise KeyError(f"comportamento '{profile.behavior}' não registrado (espécie {profile.id})")
    return cls(profile)


def apply_gravity(e: Enemy, dt: float, gravity: float = GRAVITY, max_fall: float = MAX_FALL_SPEED) -> None:
    e.vy = min(max_fall, e.vy + gravity * dt)


def ground_move(game: "Game", e: Enemy, dt: float, *, edge_turn: bool = True, gravity: bool = True) -> bool:
    """Legacy walker motion: gravity, move, turn at walls and (optionally) ledges.

    Returns True when the enemy turned this step.
    """

    turned = False
    if gravity:
        apply_gravity(e, dt)
    before = e.vx
    hit = move_body(e, game.index, dt, reveal_hidden=False)
    e.grounded = hit.grounded
    if before != 0 and e.vx == 0:
        e.facing *= -1
        turned = True
    if edge_turn and e.grounded:
        probe_x = e.x + e.w + 5 if e.facing > 0 else e.x - 7
        if not solid_at(game.index, probe_x, e.y + e.h, 2, 7):
            e.facing *= -1
            turned = True
    return turned


def player_distance(game: "Game", e: Enemy) -> tuple[float, float]:
    p = game.player
    return (p.x + p.w / 2) - (e.x + e.w / 2), (p.y + p.h / 2) - (e.y + e.h / 2)


def stomp_bounce() -> float:
    return STOMP_BOUNCE
