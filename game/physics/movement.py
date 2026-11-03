"""Perfil de movimentação do personagem.

Os valores padrão reproduzem exatamente o motor TypeScript de referência
(``src/core/game.ts``); perfis calibrados pela pesquisa são adicionados sem
alterar o comportamento base testado.
"""

from __future__ import annotations

from dataclasses import dataclass

FIXED_DT = 1 / 120
GRAVITY = 1550.0
JUMP_SPEED = 590.0


@dataclass(slots=True, frozen=True)
class MovementProfile:
    walk_speed: float = 220.0
    run_speed: float = 340.0
    ground_acceleration: float = 1400.0
    air_acceleration: float = 1000.0
    ground_friction: float = 1500.0
    ice_friction: float = 180.0
    air_friction: float = 500.0
    jump_speed: float = JUMP_SPEED
    jump_cut_speed: float = 190.0
    gravity: float = GRAVITY
    terminal_velocity: float = 850.0
    coyote_time: float = 0.1
    jump_buffer: float = 0.12
    camera_lookahead: float = 0.15


LEGACY_PROFILE = MovementProfile()
