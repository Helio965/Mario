"""Percepção dos inimigos: o que cada um consegue observar do mundo.

Separa três áreas: a hitbox física (colisão), a área de ataque e a área de
percepção. A percepção usa apenas informações observáveis (distância, campo de
visão à frente, altura relativa, linha de visão bloqueada por plataformas) e
um tempo de reação, para que o comportamento permaneça justo e aprendível.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from game.core.types import Rect
from game.physics.collision import overlaps


@dataclass(slots=True, frozen=True)
class PerceptionProfile:
    sight_range: float = 320.0  # distância máxima de percepção (px)
    sight_height: float = 120.0  # diferença vertical tolerada (px)
    field_of_view_behind: float = 40.0  # quanto enxerga para trás (px)
    attack_range: float = 90.0
    reaction_time: float = 0.25  # segundos até reagir ao avistar
    forget_time: float = 1.2  # segundos até esquecer o jogador
    needs_line_of_sight: bool = True


@dataclass(slots=True)
class Perception:
    profile: PerceptionProfile
    noticed_for: float = 0.0
    lost_for: float = 0.0
    aware: bool = False

    def observe(
        self, dt: float, enemy: Any, player: Any, facing: int, platforms: list[Any]
    ) -> dict[str, Any]:
        """Atualiza a consciência e devolve os fatos para o ``Blackboard``."""
        ex = enemy.x + enemy.w / 2
        ey = enemy.y + enemy.h / 2
        px = player.x + player.w / 2
        py = player.y + player.h / 2
        dx = px - ex
        dy = py - ey
        distance = (dx * dx + dy * dy) ** 0.5
        ahead = dx * facing >= -self.profile.field_of_view_behind
        within = (
            distance <= self.profile.sight_range and abs(dy) <= self.profile.sight_height and ahead
        )
        visible = within and (
            not self.profile.needs_line_of_sight or line_of_sight(ex, ey, px, py, platforms)
        )
        if visible:
            self.noticed_for += dt
            self.lost_for = 0.0
            if self.noticed_for >= self.profile.reaction_time:
                self.aware = True
        else:
            self.noticed_for = 0.0
            if self.aware:
                self.lost_for += dt
                if self.lost_for >= self.profile.forget_time:
                    self.aware = False
                    self.lost_for = 0.0
        return {
            "player_dx": dx,
            "player_dy": dy,
            "player_distance": distance,
            "player_visible": self.aware,
            "player_in_attack_range": self.aware and distance <= self.profile.attack_range,
            "player_above": dy < -enemy.h / 2,
            "facing_player": dx * facing > 0,
        }


def line_of_sight(
    x0: float, y0: float, x1: float, y1: float, platforms: list[Any], samples: int = 12
) -> bool:
    """Amostra o segmento entre dois pontos; bloqueado se cruzar uma plataforma sólida visível."""
    probe = Rect(0.0, 0.0, 2.0, 2.0)
    for i in range(1, samples):
        t = i / samples
        probe.x = x0 + (x1 - x0) * t - 1
        probe.y = y0 + (y1 - y0) * t - 1
        for p in platforms:
            if not p.alive or (p.kind == "hidden" and not p.used):
                continue
            if overlaps(probe, p):
                return False
    return True


def edge_ahead(enemy: Any, facing: int, platforms: list[Any], probe_depth: float = 7.0) -> bool:
    """Não há chão logo à frente dos pés (mesma regra do motor de referência)."""
    probe = Rect(
        enemy.x + enemy.w + 5 if facing > 0 else enemy.x - 7, enemy.y + enemy.h, 2.0, probe_depth
    )
    return not any(
        p.alive and (p.kind != "hidden" or p.used) and overlaps(probe, p) for p in platforms
    )


def wall_ahead(enemy: Any, facing: int, platforms: list[Any], reach: float = 4.0) -> bool:
    probe = Rect(
        enemy.x + enemy.w if facing > 0 else enemy.x - reach,
        enemy.y + 2,
        reach,
        max(1.0, enemy.h - 4),
    )
    return any(p.alive and (p.kind != "hidden" or p.used) and overlaps(probe, p) for p in platforms)
