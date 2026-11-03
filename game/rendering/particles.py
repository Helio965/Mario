"""Desenho das partículas da simulação (explosões de moedas, poeira, dano).

As partículas vivem em ``game.particles`` (simulação pura); aqui elas só são
desenhadas, com alpha proporcional à vida restante como no original
(``globalAlpha = min(1, life·3)``). ``limit`` restringe quantas são
desenhadas nas qualidades reduzidas: as mais recentes têm prioridade.
"""

from __future__ import annotations

from collections.abc import Sequence

from game.core.types import Particle
from game.rendering.painter import Painter


def draw_particles(painter: Painter, particles: Sequence[Particle], limit: int = 0) -> None:
    """Desenha ``particles`` (as últimas ``limit`` quando ``limit > 0``) e restaura alpha 1."""
    if not particles:
        return
    chosen = particles[-limit:] if 0 < limit < len(particles) else particles
    rect = painter.rect
    set_alpha = painter.set_alpha
    for particle in chosen:
        set_alpha(min(1.0, particle.life * 3))
        rect(particle.x, particle.y, particle.size, particle.size, particle.color)
    set_alpha(1.0)
