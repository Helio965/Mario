"""Caches de superfícies para a renderização.

Superfícies estáticas (gradiente do céu, vinheta, camadas de rascunho com
alpha) são criadas uma única vez e reutilizadas por quadro. ``convert`` /
``convert_alpha`` aceleram blits quando há uma janela; em modo headless
(``SDL_VIDEODRIVER=dummy`` sem ``set_mode``) o pygame lança ``pygame.error``
e a superfície crua é usada sem conversão.
"""

from __future__ import annotations

from collections.abc import Callable, Hashable

import pygame


def make_surface(size: tuple[int, int], alpha: bool = False) -> pygame.Surface:
    """Cria uma ``Surface`` (opcionalmente SRCALPHA) convertida ao formato da tela quando possível."""
    width = max(1, int(size[0]))
    height = max(1, int(size[1]))
    surface = pygame.Surface((width, height), pygame.SRCALPHA if alpha else 0)
    try:
        converted = surface.convert_alpha() if alpha else surface.convert()
    except pygame.error:
        # Sem janela (testes, capturas) não existe formato de tela: usa a superfície crua.
        return surface
    return converted


class SurfaceCache[K: Hashable]:
    """Dicionário limitado de superfícies, chaveado por qualquer valor hashable.

    Ao exceder ``limit`` entradas o cache é esvaziado por completo: a política
    é simples e suficiente para conjuntos pequenos (tamanhos de partículas,
    temas, blocos), evitando crescimento sem fim durante partidas longas.
    """

    def __init__(self, limit: int = 256) -> None:
        self._limit = max(1, limit)
        self._entries: dict[K, pygame.Surface] = {}

    def __len__(self) -> int:
        return len(self._entries)

    def get(self, key: K, build: Callable[[], pygame.Surface]) -> pygame.Surface:
        """Devolve a superfície de ``key``, construindo-a com ``build`` na primeira vez."""
        surface = self._entries.get(key)
        if surface is None:
            if len(self._entries) >= self._limit:
                self._entries.clear()
            surface = build()
            self._entries[key] = surface
        return surface

    def clear(self) -> None:
        self._entries.clear()
