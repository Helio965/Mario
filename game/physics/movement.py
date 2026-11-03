"""Perfis de movimentação do personagem.

Unidades: px/s, px/s² e segundos, para o passo fixo de 1/120 s.

* ``LEGACY_PROFILE`` reproduz byte a byte o motor TypeScript de referência
  (``src/core/game.ts``) e é o perfil usado pelos testes diferenciais.
* ``CALIBRATED_PROFILE`` aplica as conclusões da pesquisa
  (``docs/research/MOVIMENTACAO.md`` §13 e ``docs/research/FISICA.md`` §10):
  arco de salto assimétrico (preset B), derrapagem com atrito dobrado (SMB1),
  sem atrito aéreo sem entrada (SMB1), graça ao soltar a corrida (SMB1
  ``RunningTimer``), gelo afetando a aceleração (SMW), dano sem empurrão
  (SMB1). Altura (112 px) e tempo total do salto (0,76 s) são preservados
  para não invalidar o desenho das 15 fases.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

FIXED_DT = 1 / 120
GRAVITY = 1550.0  # gravidade do mundo (inimigos, itens, projéteis) — não muda com o perfil
JUMP_SPEED = 590.0

Model = Literal["legacy", "calibrated"]


@dataclass(slots=True, frozen=True)
class MovementProfile:
    model: Model = "legacy"
    walk_speed: float = 220.0
    run_speed: float = 340.0
    # legado: aceleração única no chão/ar e atrito ao soltar
    ground_acceleration: float = 1400.0
    air_acceleration: float = 1000.0
    ground_friction: float = 1500.0  # desaceleração ao soltar (chão)
    ice_friction: float = 180.0
    air_friction: float = 500.0  # desaceleração sem entrada no ar (SMB1: 0)
    jump_speed: float = JUMP_SPEED
    jump_cut_speed: float = 190.0
    gravity: float = GRAVITY  # legado: simétrica; calibrado: gravidade de subida (botão segurado)
    gravity_fall: float | None = None  # calibrado: gravidade de descida / botão solto
    terminal_velocity: float = 850.0
    coyote_time: float = 0.1
    jump_buffer: float = 0.12
    camera_lookahead: float = 0.15
    # calibrado
    walk_acceleration: float = 700.0
    run_acceleration: float = 800.0
    skid_deceleration: float = 1800.0  # SMB1: dobro do atrito ao soltar
    skid_turn_speed: float = 80.0  # abaixo disso a derrapagem termina (SMB1: 11/16 px/q × 1,875)
    run_release_grace: float = 0.17  # SMB1 RunningTimer (10 quadros)
    ice_acceleration_multiplier: float = 0.35  # SMW/SMB3: menos tração (ESTIMADO)
    ice_skid_deceleration: float = 500.0
    ceiling_bump_speed: float = 0.0  # empurrão ao bater a cabeça (SMB1 ≈ +112 escalado)
    hurt_knockback: float = 100.0  # SMB1: 0 (sem empurrão)
    hurt_invulnerability: float = 2.0
    run_jump_speed: float | None = None  # bônus de corrida (desligado por padrão)
    run_jump_threshold: float = 300.0

    @property
    def fall_gravity(self) -> float:
        return self.gravity_fall if self.gravity_fall is not None else self.gravity

    # ---------------------------------------------------------- previsões
    def jump_height(self) -> float:
        """Altura contínua do salto máximo: v0² / (2·g_sobe)."""
        return self.jump_speed * self.jump_speed / (2 * self.gravity)

    def rise_time(self) -> float:
        return self.jump_speed / self.gravity

    def fall_time(self) -> float:
        h = self.jump_height()
        g = self.fall_gravity
        vt = self.terminal_velocity
        if vt * vt < 2 * g * h:
            return vt / g + (h - vt * vt / (2 * g)) / vt
        return math.sqrt(2 * h / g)

    def air_time(self) -> float:
        return self.rise_time() + self.fall_time()

    def horizontal_range(self, vx: float | None = None) -> float:
        return (self.run_speed if vx is None else vx) * self.air_time()

    def min_jump_height(self) -> float:
        """Altura ao soltar imediatamente: corte para ``jump_cut_speed`` e descida com ``fall_gravity``."""
        v = min(self.jump_speed, self.jump_cut_speed)
        return v * v / (2 * self.fall_gravity)

    def run_up_distance(self) -> float:
        """Distância para ir do repouso à velocidade de corrida no chão."""
        a = self.run_acceleration if self.model == "calibrated" else self.ground_acceleration
        return self.run_speed * self.run_speed / (2 * a)

    def braking_distance(self, speed: float | None = None, skid: bool = False) -> float:
        v = self.run_speed if speed is None else speed
        if self.model == "calibrated":
            d = self.skid_deceleration if skid else self.ground_friction
        else:
            d = self.ground_acceleration if skid else self.ground_friction
        return v * v / (2 * d)


LEGACY_PROFILE = MovementProfile()

CALIBRATED_PROFILE = MovementProfile(
    model="calibrated",
    walk_speed=220.0,
    run_speed=340.0,
    ground_acceleration=800.0,
    air_acceleration=700.0,  # SMB1: igual ao chão
    ground_friction=900.0,  # "desacelera mais rápido do que acelera" (SMW)
    ice_friction=220.0,
    air_friction=0.0,  # SMB1: sem atrito aéreo sem entrada
    jump_speed=487.0,  # h = 487² / (2·1059) = 112 px (mantém o alcance das fases)
    jump_cut_speed=330.0,  # salto mínimo ≈ 23 % do máximo (SMB1: 33 %)
    gravity=1059.0,  # subida 0,46 s
    gravity_fall=2489.0,  # descida 0,30 s; razão 2,35 (SMB1 ≈ 3,2–3,6)
    terminal_velocity=760.0,
    coyote_time=5 / 60,
    jump_buffer=6 / 60,  # NSMBW: janela de 8 quadros para encadear saltos
    camera_lookahead=0.15,
    walk_acceleration=700.0,
    run_acceleration=800.0,  # 0,43 s / 72 px até 340 (SMB1: 0,75 s; SMW: 0,4–0,5 s)
    skid_deceleration=1800.0,
    skid_turn_speed=80.0,
    run_release_grace=0.17,
    ice_acceleration_multiplier=0.35,
    ice_skid_deceleration=500.0,
    ceiling_bump_speed=100.0,
    hurt_knockback=0.0,
    hurt_invulnerability=2.6,  # SMB1: 148–168 quadros
    run_jump_speed=None,
)

PROFILES: dict[str, MovementProfile] = {"legacy": LEGACY_PROFILE, "calibrated": CALIBRATED_PROFILE}
