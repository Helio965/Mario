"""Máquina de estados finitos genérica para inimigos, NPCs e chefes.

Cada estado é declarado com duração mínima/máxima opcional, animação
associada e uma lista de transições avaliadas em ordem. As condições recebem
um ``Blackboard`` (percepção + temporizadores) e nunca o jogo inteiro, o que
mantém as decisões observáveis, testáveis e previsíveis para o jogador.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class EnemyStateName(StrEnum):
    IDLE = "IDLE"
    PATROL = "PATROL"
    ALERT = "ALERT"
    CHASE = "CHASE"
    PREPARE_ATTACK = "PREPARE_ATTACK"
    ATTACK = "ATTACK"
    RECOVER = "RECOVER"
    HURT = "HURT"
    STUNNED = "STUNNED"
    RETREAT = "RETREAT"
    DEFEATED = "DEFEATED"
    # Estados específicos de arquétipos (casco, explosivo, aquático…).
    SHELL = "SHELL"
    SLIDE = "SLIDE"
    FUSE = "FUSE"
    EXPLODE = "EXPLODE"
    HIDDEN = "HIDDEN"
    EMERGE = "EMERGE"
    DIVE = "DIVE"
    LEAP = "LEAP"
    DROP = "DROP"
    RISE = "RISE"
    SWIM = "SWIM"


@dataclass(slots=True)
class Blackboard:
    """Fatos observáveis compartilhados entre percepção e decisões."""

    time_in_state: float = 0.0
    total_time: float = 0.0
    player_dx: float = 0.0  # jogador.x − inimigo.x (centros)
    player_dy: float = 0.0
    player_distance: float = float("inf")
    player_visible: bool = False
    player_in_attack_range: bool = False
    player_above: bool = False
    facing_player: bool = False
    grounded: bool = False
    edge_ahead: bool = False
    wall_ahead: bool = False
    hurt: bool = False
    health: int = 1
    max_health: int = 1
    in_water: bool = False
    player_looking_at_me: bool = False
    player_speed: float = 0.0
    player_below: bool = False
    player_grounded: bool = True
    player_star: bool = False
    on_screen: bool = True
    just_landed: bool = False
    hit_enemy: bool = False
    hit_wall: bool = False
    flags: dict[str, Any] = field(default_factory=dict)
    timers: dict[str, float] = field(default_factory=dict)

    def in_zone(self, low: float, high: float) -> bool:
        """Janela assimétrica em ``player_dx`` (Thwomp/Piranha usam deslocamentos distintos)."""
        return low <= self.player_dx < high

    def timer(self, name: str) -> float:
        return self.timers.get(name, 0.0)

    def set_timer(self, name: str, seconds: float) -> None:
        self.timers[name] = seconds

    def tick(self, dt: float) -> None:
        self.time_in_state += dt
        self.total_time += dt
        for key in list(self.timers):
            self.timers[key] = max(0.0, self.timers[key] - dt)


Condition = Callable[[Blackboard], bool]
Action = Callable[[Blackboard], None]


@dataclass(slots=True)
class Transition:
    to: EnemyStateName
    when: Condition
    label: str = ""


@dataclass(slots=True)
class State:
    name: EnemyStateName
    transitions: list[Transition] = field(default_factory=list)
    min_time: float = 0.0  # transições (exceto forçadas) só após este tempo
    max_time: float | None = None  # ao expirar, vai para ``timeout_to``
    timeout_to: EnemyStateName | None = None
    on_enter: Action | None = None
    on_exit: Action | None = None
    animation: str = "idle"
    telegraph: bool = False  # estado de sinalização visível antes de um ataque


class StateMachine:
    """Executa a FSM. ``force`` ignora ``min_time`` (dano, derrota)."""

    def __init__(self, states: dict[EnemyStateName, State], initial: EnemyStateName) -> None:
        if initial not in states:
            raise ValueError(f"estado inicial desconhecido: {initial}")
        self.states = states
        self.current: State = states[initial]
        self.history: list[tuple[float, EnemyStateName]] = [(0.0, initial)]

    @property
    def name(self) -> EnemyStateName:
        return self.current.name

    def force(self, to: EnemyStateName, bb: Blackboard) -> None:
        self._enter(to, bb)

    def update(self, dt: float, bb: Blackboard) -> EnemyStateName:
        bb.tick(dt)
        state = self.current
        if (
            state.max_time is not None
            and state.timeout_to is not None
            and bb.time_in_state >= state.max_time
        ):
            self._enter(state.timeout_to, bb)
            return self.current.name
        if bb.time_in_state < state.min_time:
            return state.name
        for transition in state.transitions:
            if transition.when(bb):
                self._enter(transition.to, bb)
                break
        return self.current.name

    def _enter(self, to: EnemyStateName, bb: Blackboard) -> None:
        if to not in self.states:
            raise ValueError(f"transição para estado desconhecido: {to}")
        if self.current.on_exit is not None:
            self.current.on_exit(bb)
        self.current = self.states[to]
        bb.time_in_state = 0.0
        self.history.append((bb.total_time, to))
        if len(self.history) > 64:
            del self.history[0]
        if self.current.on_enter is not None:
            self.current.on_enter(bb)
