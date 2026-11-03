"""Cenários dos cinco mundos (port de ``src/render/background.ts``).

``Background(painter)`` com ``sky()``, ``landscape()``, ``shrub(x, y, seed)``,
``weather(foreground)``, ``vignette()``, ``pine``, ``mushroom``, ``cloud``.

Camadas estáticas por mundo (gradiente do céu em faixas, vinheta) são
pré-renderizadas em Surfaces e reutilizadas; as camadas com parallax
(sol/lua, estrelas, nuvens, montanhas, ruínas, clima) são desenhadas por
quadro com os mesmos números do original, para que a variação determinística
(``hash01``) produza a mesma cena.
"""

from __future__ import annotations

import math

import pygame

from game.core.types import Theme
from game.levels.loader import THEMES
from game.rendering.cache import SurfaceCache, make_surface
from game.rendering.painter import HEIGHT, WIDTH, Painter, hash01, parse_color, tint

VIGNETTE_RGB = (12, 28, 40)
_fmod = math.fmod


def vignette_alpha(position: float) -> float:
    """Gradiente linear do original: 0 → 0,11; 0,22 → 0; 0,85 → 0; 1 → 0,10."""
    if position <= 0.22:
        return 0.11 * (1 - position / 0.22)
    if position >= 0.85:
        return 0.10 * (position - 0.85) / 0.15
    return 0.0


class Background:
    """Céu, montanhas, ruínas, flora e clima das cinco fronteiras."""

    def __init__(self, painter: Painter) -> None:
        self._painter = painter
        # Fração das partículas de clima desenhadas (qualidade "medium"/"low").
        self.density = 1.0
        self._skies: SurfaceCache[str] = SurfaceCache(limit=16)
        self._vignette: tuple[pygame.Surface, pygame.Surface] | None = None

    @property
    def theme(self) -> Theme:
        theme = self._painter.scene.theme
        return theme if theme is not None else THEMES[0]

    # céu ------------------------------------------------------------------
    def sky(self) -> None:
        painter = self._painter
        scene = painter.scene
        theme = self.theme
        world = scene.world
        frame = scene.frame
        camera_x = scene.camera_x
        camera_y = scene.camera_y
        painter.surface.blit(self._skies.get(theme.sky, lambda: self._build_sky(theme.sky)), (0, 0))
        rect = painter.rect
        x = 770 - camera_x * 0.035
        y = 116 - camera_y * 0.025
        night = world >= 4
        rect(x - 38, y - 18, 76, 36, tint(theme.sky, 0.09 if night else 0.19))
        rect(x - 28, y - 28, 56, 56, tint(theme.sky, 0.13 if night else 0.25))
        painter.polygon(
            [
                x - 18,
                y - 28,
                x + 18,
                y - 28,
                x + 28,
                y - 18,
                x + 28,
                y + 18,
                x + 18,
                y + 28,
                x - 18,
                y + 28,
                x - 28,
                y + 18,
                x - 28,
                y - 18,
            ],
            "#d7e7d4" if night else "#ffe5a0",
        )
        if night:
            rect(x + 5, y - 10, 9, 6, "#adcac2")
            rect(x - 15, y + 10, 6, 6, "#adcac2")
            for i in range(54):
                star_x = hash01(i + 77) * WIDTH
                star_y = hash01(i + 180) * 290
                painter.set_alpha(0.4 + math.sin(frame * 0.8 + i) * 0.22)
                rect(star_x, star_y, 3 if i % 7 == 0 else 2, 2, "#dce6db")
                if i % 11 == 0:
                    rect(star_x + 1, star_y - 2, 1, 6, "#dce6db")
            painter.set_alpha(1)
        if world == 5:
            cloud_color = "#6c5560"
        elif world == 4:
            cloud_color = "#5a7b8b"
        else:
            cloud_color = tint(theme.sky, 0.5)
        offset = (_fmod(camera_x * 0.12 + frame * 3, 270) + 270) % 270
        for i in range(-1, 7):
            cx = i * 270 - offset
            cy = 73 + hash01(i + 120) * 98 - camera_y * 0.045
            self.cloud(cx, cy, 0.7 + hash01(i + 50) * 0.55, cloud_color)
        rect(0, 386 - camera_y * 0.08, WIDTH, 85, tint(theme.sky, 0.21))

    def _build_sky(self, sky: str) -> pygame.Surface:
        """Faixas horizontais de 18 px clareando para baixo (estático por tema)."""
        surface = make_surface((WIDTH, HEIGHT))
        for y in range(0, HEIGHT, 18):
            surface.fill(parse_color(tint(sky, (y / HEIGHT) * 0.16)), (0, y, WIDTH, 18))
        return surface

    def cloud(self, x: float, y: float, scale: float, color: str) -> None:
        rect = self._painter.rect
        rect(x + 20 * scale, y, 34 * scale, 12 * scale, color)
        rect(x + 10 * scale, y + 8 * scale, 65 * scale, 20 * scale, color)
        rect(x, y + 18 * scale, 96 * scale, 18 * scale, color)
        rect(x + 10 * scale, y + 36 * scale, 78 * scale, 6 * scale, tint(color, -0.04))

    # paisagem -------------------------------------------------------------
    def landscape(self) -> None:
        painter = self._painter
        scene = painter.scene
        theme = self.theme
        world = scene.world
        camera_x = scene.camera_x
        base = 450 - scene.camera_y * 0.11
        far = theme.far
        near = theme.near
        rect = painter.rect
        polygon = painter.polygon
        # Duas camadas largas de montanhas em velocidades distintas mantêm a rota legível.
        for layer in range(2):
            step = 340 if layer else 450
            parallax = 0.2 if layer else 0.085
            offset = camera_x * parallax
            first = math.floor(offset / step) - 1
            for i in range(first, first + 5):
                x = i * step - offset
                peak = base - (130 if layer else 235) - hash01(i + layer * 50) * 70
                color = near if layer else far
                if world == 1:
                    polygon(
                        [
                            x - 30,
                            base,
                            x + 16,
                            peak + 108,
                            x + 46,
                            peak + 62,
                            x + 90,
                            peak + 38,
                            x + 122,
                            peak + 30,
                            x + 156,
                            peak + 40,
                            x + 198,
                            peak + 84,
                            x + 232,
                            peak + 124,
                            x + step,
                            base,
                        ],
                        color,
                    )
                    if not layer:
                        polygon(
                            [
                                x + 50,
                                peak + 83,
                                x + 91,
                                peak + 41,
                                x + 121,
                                peak + 32,
                                x + 156,
                                peak + 45,
                                x + 186,
                                peak + 70,
                                x + 141,
                                peak + 60,
                                x + 108,
                                peak + 64,
                            ],
                            tint(color, 0.1),
                        )
                elif world == 2:
                    polygon(
                        [
                            x - 20,
                            base,
                            x + 30,
                            peak + 70,
                            x + 60,
                            peak + 70,
                            x + 60,
                            peak + 20,
                            x + 170,
                            peak + 20,
                            x + 170,
                            peak + 46,
                            x + 213,
                            peak + 46,
                            x + 267,
                            base,
                        ],
                        color,
                    )
                    rect(x + 62, peak + 30, 107, 7, tint(color, 0.1))
                    rect(x + 29, peak + 99, 170, 5, tint(color, -0.08))
                    rect(x + 88, peak + 50, 6, 62, tint(color, -0.09))
                elif world == 3:
                    polygon(
                        [
                            x - 25,
                            base,
                            x + 116,
                            peak,
                            x + 150,
                            peak + 52,
                            x + 183,
                            peak + 19,
                            x + step,
                            base,
                        ],
                        color,
                    )
                    polygon(
                        [
                            x + 81,
                            peak + 62,
                            x + 116,
                            peak,
                            x + 150,
                            peak + 52,
                            x + 130,
                            peak + 45,
                            x + 119,
                            peak + 61,
                            x + 109,
                            peak + 37,
                            x + 100,
                            peak + 70,
                        ],
                        "#c8e9ee" if layer else "#b2d6df",
                    )
                    polygon(
                        [
                            x + 160,
                            peak + 58,
                            x + 183,
                            peak + 19,
                            x + 218,
                            peak + 62,
                            x + 184,
                            peak + 48,
                        ],
                        "#bbdce7",
                    )
                elif world == 4:
                    rect(x + 89, peak + 80, 30, base - peak, color)
                    polygon(
                        [
                            x + 18,
                            peak + 140,
                            x + 56,
                            peak + 78,
                            x + 56,
                            peak + 49,
                            x + 93,
                            peak + 10,
                            x + 130,
                            peak + 24,
                            x + 154,
                            peak + 65,
                            x + 151,
                            peak + 90,
                            x + 182,
                            peak + 140,
                        ],
                        color,
                    )
                    rect(x + 106, peak + 180, 5, 76, tint(color, 0.09))
                    polygon(
                        [
                            x + 111,
                            peak + 196,
                            x + 143,
                            peak + 176,
                            x + 140,
                            peak + 188,
                            x + 114,
                            peak + 211,
                        ],
                        color,
                    )
                else:
                    polygon(
                        [
                            x - 30,
                            base,
                            x + 75,
                            peak + 20,
                            x + 123,
                            peak + 20,
                            x + 146,
                            peak + 32,
                            x + 185,
                            peak + 19,
                            x + step,
                            base,
                        ],
                        color,
                    )
                    polygon(
                        [
                            x + 83,
                            peak + 31,
                            x + 116,
                            peak + 31,
                            x + 145,
                            peak + 45,
                            x + 159,
                            peak + 30,
                            x + 177,
                            peak + 29,
                            x + 157,
                            peak + 70,
                            x + 152,
                            peak + 139,
                            x + 128,
                            peak + 84,
                        ],
                        "#b65450" if layer else "#8d4c53",
                    )
                    rect(x + 133, peak + 51, 8, 33, "#e88963")
        # Pequenas silhuetas antigas ligam as cinco fronteiras.
        offset = camera_x * 0.32
        start = math.floor(offset / 620)
        for i in range(start - 1, start + 3):
            x = i * 620 + 205 - offset
            y = base - 49
            color = tint(near, -0.09)
            rect(x, y - 18, 48, 95, color)
            rect(x - 5, y - 25, 60, 11, color)
            rect(x + 7, y - 35, 8, 12, color)
            rect(x + 32, y - 35, 8, 12, color)
            rect(x + 18, y + 11, 12, 26, tint(color, -0.14))
            rect(x + 20, y + 14, 3, 15, tint(color, 0.1))
            if world == 4:
                self.mushroom(x + 71, base + 18, 0.8, "#75868b", "#4b737a")
            if world == 1 or world == 3:
                self.pine(x + 91, base + 24, 0.75, color)

    def pine(self, x: float, y: float, scale: float, color: str) -> None:
        painter = self._painter
        painter.rect(x - 4 * scale, y - 53 * scale, 8 * scale, 53 * scale, "#6b6557")
        snowy = painter.scene.world == 3
        for i in range(3):
            top = y - (100 - i * 26) * scale
            width = (20 + i * 12) * scale
            painter.polygon(
                [x, top, x + width, top + 44 * scale, x - width, top + 44 * scale], color
            )
            if snowy:
                painter.polygon(
                    [
                        x,
                        top,
                        x + width * 0.5,
                        top + 23 * scale,
                        x + 4 * scale,
                        top + 19 * scale,
                        x - width * 0.54,
                        top + 23 * scale,
                    ],
                    "#b2dbe2",
                )

    def mushroom(self, x: float, y: float, scale: float, cap: str, stem: str) -> None:
        painter = self._painter
        painter.rect(x - 4 * scale, y - 24 * scale, 8 * scale, 24 * scale, stem)
        painter.polygon(
            [
                x - 30 * scale,
                y - 22 * scale,
                x - 25 * scale,
                y - 40 * scale,
                x - 9 * scale,
                y - 50 * scale,
                x + 13 * scale,
                y - 50 * scale,
                x + 29 * scale,
                y - 34 * scale,
                x + 31 * scale,
                y - 22 * scale,
            ],
            cap,
        )
        painter.rect(x - 17 * scale, y - 36 * scale, 6 * scale, 4 * scale, tint(cap, 0.2))
        painter.rect(x + 7 * scale, y - 43 * scale, 5 * scale, 5 * scale, tint(cap, 0.2))

    def shrub(self, x: float, y: float, seed: int) -> None:
        painter = self._painter
        rect = painter.rect
        world = painter.scene.world
        if world == 1:
            color = "#407f69" if seed % 2 else "#4e9570"
            rect(x, y - 10, 27, 10, color)
            rect(x + 5, y - 17, 14, 7, color)
            rect(x - 6, y - 5, 40, 5, tint(color, -0.13))
            for i in range(4):
                rect(x + i * 7, y - 9 - (i % 2) * 4, 3, 3, "#f4a793" if i % 2 else "#eadba0")
            if seed % 5 == 0:
                self.pine(x - 40, y, 0.75, "#326e60")
        elif world == 2:
            rect(x + 7, y - 39, 12, 39, "#537d67")
            rect(x + 3, y - 34, 20, 24, "#537d67")
            rect(x - 6, y - 26, 9, 16, "#537d67")
            rect(x - 6, y - 28, 9, 5, "#a4b283")
            rect(x + 22, y - 35, 8, 18, "#537d67")
            rect(x + 9, y - 35, 3, 30, "#80a783")
            rect(x + 19, y - 6, 16, 6, "#7c7761")
        elif world == 3:
            if seed % 3 == 0:
                self.pine(x + 10, y, 0.85, "#458894")
            else:
                painter.polygon([x, y, x + 7, y - 15, x + 25, y - 14, x + 33, y], "#a3cbd7")
                rect(x + 7, y - 15, 18, 4, "#e3f5ee")
                rect(x + 16, y - 8, 8, 4, "#86afc1")
        elif world == 4:
            self.mushroom(x + 10, y, 0.4 + hash01(seed) * 0.3, "#75b5ad", "#578291")
            self.mushroom(x + 31, y, 0.3, "#ac80a8", "#67828b")
            rect(x - 4, y - 5, 48, 5, "#356967")
        else:
            painter.polygon(
                [x, y, x + 4, y - 11, x + 13, y - 19, x + 23, y - 15, x + 34, y], "#5e5260"
            )
            rect(x + 11, y - 14, 5, 9, "#d37664")
            rect(x + 21, y - 8, 8, 4, "#8c5d63")

    # clima e vinheta --------------------------------------------------------
    def weather(self, foreground: bool) -> None:
        kind = self.theme.weather
        if kind == "none":
            return
        count = int((26 if foreground else 18) * self.density)
        if count <= 0:
            return
        painter = self._painter
        scene = painter.scene
        frame = scene.frame
        camera_x = scene.camera_x
        camera_y = scene.camera_y
        rect = painter.rect
        painter.set_alpha(0.6 if foreground else 0.35)
        speed = 14 if kind == "snow" else 9 if kind == "sand" else -10
        drift = -45 if kind == "sand" else -8
        parallax = 0.7 if foreground else 0.15
        if kind == "snow":
            color = "#e4f4f0"
        elif kind == "sand":
            color = "#d9bf89"
        elif kind == "embers":
            color = "#f4a476"
        else:
            color = "#b6dac0"
        flake_height = 1 if kind == "sand" else 2
        base_seed = 0 if foreground else 500
        for i in range(count):
            seed = i + base_seed
            x = (
                _fmod(
                    hash01(seed) * WIDTH
                    + math.sin(frame * 0.7 + seed) * 20
                    + frame * drift
                    - camera_x * parallax,
                    WIDTH,
                )
                + WIDTH
            ) % WIDTH
            y = (
                _fmod(hash01(seed + 51) * HEIGHT + frame * speed - camera_y * 0.1, HEIGHT) + HEIGHT
            ) % HEIGHT
            rect(x, y, 3 if i % 3 == 0 else 2, flake_height, color)
            if kind == "spores" and i % 4 == 0:
                rect(x - 1, y + 1, 4, 1, "#74b49b")
        painter.set_alpha(1)

    def vignette(self) -> None:
        if self._vignette is None:
            self._vignette = self._build_vignette()
        top, bottom = self._vignette
        surface = self._painter.surface
        surface.blit(top, (0, 0))
        surface.blit(bottom, (0, HEIGHT - bottom.get_height()))

    @staticmethod
    def _build_vignette() -> tuple[pygame.Surface, pygame.Surface]:
        """Duas faixas SRCALPHA (topo e base); o meio do gradiente é transparente."""
        rows = [vignette_alpha((row + 0.5) / HEIGHT) for row in range(HEIGHT)]
        top_rows = next(row for row in range(HEIGHT) if rows[row] <= 0)
        bottom_start = next(row for row in range(HEIGHT) if row > top_rows and rows[row] > 0)
        top = make_surface((WIDTH, top_rows), alpha=True)
        for row in range(top_rows):
            top.fill((*VIGNETTE_RGB, round(rows[row] * 255)), (0, row, WIDTH, 1))
        bottom = make_surface((WIDTH, HEIGHT - bottom_start), alpha=True)
        for row in range(bottom_start, HEIGHT):
            bottom.fill((*VIGNETTE_RGB, round(rows[row] * 255)), (0, row - bottom_start, WIDTH, 1))
        return top, bottom
