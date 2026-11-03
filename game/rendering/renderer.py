"""Compositor da cena (port de ``src/render/renderer.ts``).

* ``Renderer(surface)`` desenha o mundo inteiro em uma ``Surface`` 960 × 540.
* ``render(game, now)``: céu → paisagem → clima (fundo) → [translação de
  câmera + tremor] marcos (arbustos, placas, checkpoint, saída) → plataformas
  → perigos → moedas → itens → inimigos → projéteis → jogador → partículas →
  clima (frente) → vinheta. Mesma ordem e aparência do original. ``now`` é o
  relógio em **segundos** (``time.perf_counter()``, como ``Application.frame``
  o passa; o original usava ``performance.now()`` em ms) e só serve de
  reserva quando ``game.elapsed`` não é finito.
* ``backdrop(world)``: cena estática do menu.
* ``effects`` e ``quality`` ("high" | "medium" | "low") reduzem partículas,
  clima e tremor.
* ``stats`` expõe o custo do último quadro (ms) para o medidor de desempenho.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from time import perf_counter

import pygame

from game.core.game import Game
from game.core.jsmath import js_round
from game.core.types import Platform
from game.levels.loader import THEMES
from game.rendering.backgrounds import Background
from game.rendering.painter import GOLD, INK, WIDTH, Painter, Scene, hash01, tint
from game.rendering.particles import draw_particles
from game.rendering.sprites import Sprites

QUESTION_MARK = (".###.", "#...#", "....#", "..##.", "..#..", ".....", "..#..")
QUESTION_PALETTE = {"#": "#fff0bd"}


@dataclass(frozen=True, slots=True)
class QualityPreset:
    """Ajustes por nível de qualidade: fração do clima, limite de partículas, fator do tremor."""

    weather: float
    particles: int  # 0 = todas
    shake: float


QUALITY_PRESETS: dict[str, QualityPreset] = {
    "high": QualityPreset(weather=1.0, particles=0, shake=1.0),
    "medium": QualityPreset(weather=0.5, particles=60, shake=0.5),
    "low": QualityPreset(weather=0.0, particles=24, shake=0.0),
}


class Renderer:
    """Compõe o mundo rolável em um viewport fixo de 960 × 540 pixels."""

    effects: bool = True
    quality: str = "high"

    def __init__(self, surface: pygame.Surface) -> None:
        self._scene = Scene(theme=THEMES[0])
        self._painter = Painter(surface, self._scene)
        self._background = Background(self._painter)
        self._sprites = Sprites(self._painter)
        self._stats: dict[str, float] = {
            "sky": 0.0,
            "scenery": 0.0,
            "entities": 0.0,
            "overlay": 0.0,
            "total": 0.0,
        }

    # acesso --------------------------------------------------------------------
    @property
    def surface(self) -> pygame.Surface:
        return self._painter.surface

    @surface.setter
    def surface(self, value: pygame.Surface) -> None:
        self._painter.surface = value

    @property
    def painter(self) -> Painter:
        return self._painter

    @property
    def scene(self) -> Scene:
        return self._scene

    @property
    def stats(self) -> dict[str, float]:
        """Tempos (ms) do último quadro: ``sky``, ``scenery``, ``entities``, ``overlay``, ``total``."""
        return dict(self._stats)

    @property
    def preset(self) -> QualityPreset:
        return QUALITY_PRESETS.get(self.quality, QUALITY_PRESETS["high"])

    # quadro --------------------------------------------------------------------
    def render(self, game: Game, now: float) -> None:
        """Desenha o estado atual de ``game``.

        ``now`` (segundos, ``time.perf_counter()``) só é usado como relógio de
        animação se ``game.elapsed`` não for finito; se nenhum dos dois for
        finito o quadro usa ``0.0`` em vez de propagar NaN/inf (``math.floor``
        e ``math.sin`` lançariam ``ValueError``).
        """
        preset = self.preset
        scene = self._scene
        painter = self._painter
        background = self._background
        sprites = self._sprites
        effects = self.effects
        scene.effects = effects
        frame = game.elapsed if math.isfinite(game.elapsed) else now
        if not math.isfinite(frame):
            frame = 0.0
        scene.frame = frame
        scene.world = game.level.world
        scene.theme = THEMES[scene.world - 1] if 1 <= scene.world <= len(THEMES) else THEMES[0]
        scene.camera_x = game.camera.x
        scene.camera_y = game.camera.y
        background.density = preset.weather
        painter.reset()
        started = perf_counter()
        background.sky()
        sky_done = perf_counter()
        background.landscape()
        if effects:
            background.weather(False)
        scenery_done = perf_counter()
        painter.save()
        shake = min(5, game.shake * 22) * preset.shake if effects and game.shake > 0 else 0
        painter.translate(
            -js_round(scene.camera_x) + js_round(math.sin(frame * 83) * shake),
            -js_round(scene.camera_y) + js_round(math.cos(frame * 97) * shake),
        )
        self.landmarks(game)
        visible = painter.visible
        for platform in game.platforms:
            if platform.alive and visible(platform.x, platform.y, platform.w, platform.h):
                self.platform(platform)
        self.hazards(game)
        for coin in game.coins:
            if not coin.collected and visible(coin.x, coin.y, coin.w, coin.h):
                sprites.coin(coin)
        for item in game.items:
            if item.alive and visible(item.x, item.y, item.w, item.h):
                sprites.item(item)
        for enemy in game.enemies:
            if enemy.alive and visible(enemy.x, enemy.y, enemy.w, enemy.h):
                sprites.enemy(enemy)
        rect = painter.rect
        for projectile in game.projectiles:
            if not projectile.alive:
                continue
            radius = max(4, projectile.w / 2)
            x = projectile.x + projectile.w / 2
            y = projectile.y + projectile.h / 2
            rect(
                x - radius - 4,
                y - radius + 2,
                radius * 2 + 8,
                radius * 2 - 4,
                "#732e69" if projectile.hostile else "#9d493d",
            )
            rect(
                x - radius,
                y - radius,
                radius * 2,
                radius * 2,
                "#d869af" if projectile.hostile else "#ff9e55",
            )
            rect(x - radius + 2, y - radius + 2, radius * 2 - 4, radius * 2 - 4, "#fff2b6")
            rect(
                x - projectile.vx / 100 - 9, y - 2, 5, 4, "#d98dbc" if projectile.hostile else GOLD
            )
        sprites.player(game.player)
        if effects:
            draw_particles(painter, game.particles, preset.particles)
        painter.set_alpha(1)
        painter.restore()
        entities_done = perf_counter()
        if effects:
            background.weather(True)
        background.vignette()
        finished = perf_counter()
        stats = self._stats
        stats["sky"] = (sky_done - started) * 1000
        stats["scenery"] = (scenery_done - sky_done) * 1000
        stats["entities"] = (entities_done - scenery_done) * 1000
        stats["overlay"] = (finished - entities_done) * 1000
        stats["total"] = (finished - started) * 1000

    def backdrop(self, world: int = 1) -> None:
        """Cena estática do menu: céu, paisagem, chão de demonstração e dois arbustos."""
        scene = self._scene
        painter = self._painter
        background = self._background
        scene.effects = self.effects
        scene.world = max(1, min(len(THEMES), int(world)))
        scene.theme = THEMES[scene.world - 1]
        scene.frame = 2.4
        scene.camera_x = 0
        scene.camera_y = 0
        background.density = self.preset.weather
        painter.reset()
        started = perf_counter()
        background.sky()
        background.landscape()
        demo = Platform(
            id="preview",
            kind="ground",
            x=0,
            y=460,
            w=WIDTH,
            h=80,
            reward=None,
            motion=None,
            destination=None,
            return_point=None,
            start_x=0,
            start_y=460,
        )
        self.platform(demo)
        background.shrub(70, 460, 1)
        background.shrub(816, 460, 2)
        if self.effects:
            background.weather(True)
        background.vignette()
        self._stats["total"] = (perf_counter() - started) * 1000

    # marcos ----------------------------------------------------------------------
    def landmarks(self, game: Game) -> None:
        painter = self._painter
        scene = self._scene
        level = game.level
        platforms = game.platforms
        rect = painter.rect
        camera_x = scene.camera_x
        start = math.floor((camera_x - 100) / 190)
        for i in range(start, start + 7):
            x = i * 190 + 22 + hash01(i + 33) * 55
            ground = next(
                (
                    platform
                    for platform in platforms
                    if platform.kind == "ground"
                    and x >= platform.x + 14
                    and x < platform.x + platform.w - 26
                ),
                None,
            )
            if ground is not None and ground.alive:
                self._background.shrub(x, ground.y, i)
        if painter.visible(level.checkpoint.x, level.checkpoint.y - 110, 50, 110):
            x = level.checkpoint.x
            ground = next(
                (p for p in platforms if p.kind == "ground" and x >= p.x and x < p.x + p.w), None
            )
            y = ground.y if ground is not None else level.checkpoint.y + 30
            reached = game.checkpoint_reached
            rect(x - 8, y - 4, 34, 5, "#384558")
            rect(x + 4, y - 101, 5, 97, "#d3d7c2")
            rect(x + 9, y - 96, 28, 24, "#6ee2bf" if reached else "#8fa19d")
            rect(x + 9, y - 96, 28, 3, "#c2f9d8" if reached else "#b4c1b3")
            rect(x + 22, y - 90, 3, 12, "#264f57")
            rect(x + 17, y - 85, 13, 3, "#264f57")
            if reached:
                painter.sparkle(x + 6, y - 103, 5, "#eeffc9")
        if painter.visible(level.exit.x - 40, level.exit.y - 230, 250, 320):
            self.exit(level.exit.x, level.exit.y, level.world)
        for hint in level.hints:
            if hint.x < camera_x - 30 or hint.x > camera_x + WIDTH + 30:
                continue
            platform = next(
                (
                    p
                    for p in platforms
                    if p.kind == "ground" and hint.x >= p.x and hint.x < p.x + p.w
                ),
                None,
            )
            if platform is None:
                continue
            rect(hint.x + 9, platform.y - 29, 4, 29, "#77634f")
            rect(hint.x - 4, platform.y - 44, 30, 21, "#3a505d")
            rect(hint.x - 2, platform.y - 42, 26, 17, "#e4c894")
            rect(hint.x + 9, platform.y - 39, 3, 7, "#43555b")
            rect(hint.x + 9, platform.y - 29, 3, 3, "#43555b")

    def exit(self, x: float, y: float, world: int) -> None:
        """Portal de saída: arco de pedra, porta, mastro com bandeira ondulante."""
        painter = self._painter
        rect = painter.rect
        color = "#8e6170" if world == 5 else "#bac3b8"
        rect(x + 81, y - 116, 69, 116, "#354753")
        rect(x + 75, y - 125, 82, 10, color)
        rect(x + 75, y - 116, 13, 116, color)
        rect(x + 144, y - 116, 13, 116, color)
        for i in range(4):
            rect(x + 75 + i * 23, y - 136, 13, 12, color)
        rect(x + 99, y - 61, 33, 61, "#263540")
        rect(x + 105, y - 71, 21, 12, "#263540")
        rect(x + 108, y - 56, 4, 50, "#435d60")
        rect(x + 100, y - 108, 12, 15, "#5c8180")
        rect(x + 127, y - 108, 12, 15, "#5c8180")
        rect(x - 8, y - 4, 42, 4, "#344f58")
        rect(x + 9, y - 177, 6, 173, "#d4d7b9")
        rect(x + 15, y - 177, 3, 172, "#809aa0")
        painter.sparkle(x + 12, y - 184, 5, "#f7dda2")
        wave = js_round(math.sin(self._scene.frame * 5) * 3)
        painter.polygon(
            [
                x + 18,
                y - 169,
                x + 61,
                y - 167 + wave,
                x + 70,
                y - 154 + wave,
                x + 59,
                y - 138 + wave,
                x + 18,
                y - 141,
            ],
            "#e7ad65",
        )
        rect(x + 20, y - 166, 4, 22, "#ffe3a3")
        painter.sparkle(x + 41, y - 153, 7, "#fef7cb")
        for i in range(3):
            rect(x + 82, y - 70 + i * 22, 7, 3, "#8eaba6")

    # plataformas -------------------------------------------------------------------
    def platform(self, p: Platform) -> None:
        if p.kind == "hidden" and not p.used:
            return
        painter = self._painter
        scene = self._scene
        rect = painter.rect
        polygon = painter.polygon
        theme = scene.theme if scene.theme is not None else THEMES[0]
        world = scene.world
        camera_x = scene.camera_x
        frame = scene.frame
        x = p.x
        y = p.y - math.sin(max(0, p.bump) * math.pi) * 8
        if p.kind == "ground" or p.kind == "ice":
            ice = p.kind == "ice"
            rect(x, y, p.w, p.h, "#84bacd" if ice else theme.ground)
            rect(x, y, p.w, 9, "#d3f6f1" if ice else theme.top)
            rect(x, y + 9, p.w, 5, "#a8dce4" if ice else tint(theme.ground, -0.15))
            if ice:
                i = max(0, math.floor((camera_x - x) / 44))
                while i * 44 < p.w and x + i * 44 < camera_x + WIDTH + 44:
                    ix = x + i * 44
                    polygon([ix + 4, y + 19, ix + 19, y + 19, ix + 7, y + 30], "#b5e5e9")
                    rect(ix + 30, y + 38, 4, 6, "#669fb9")
                    i += 1
            else:
                first = max(0, math.floor((camera_x - x - 32) / 32))
                last = min(math.ceil(p.w / 32), math.ceil((camera_x + WIDTH - x + 32) / 32))
                highlight = tint(theme.top, 0.14)
                dark_rock = tint(theme.ground, -0.16)
                light_rock = tint(theme.ground, 0.09)
                for i in range(first, last):
                    tx = x + i * 32
                    right = min(32, x + p.w - tx)
                    rect(tx + 2, y + 2, max(0, right - 4), 3, highlight)
                    rect(tx + 5, y + 9, 7, 6, theme.top)
                    if world == 3:
                        polygon([tx + 18, y + 9, tx + 22, y + 21, tx + 26, y + 9], "#b7e2e6")
                    row = 0
                    while row * 28 + 23 < p.h:
                        px = tx + 4 + hash01(i * 33 + row) * 17
                        py = y + 22 + row * 28
                        rock = hash01(i + row * 54)
                        if rock > 0.32:
                            rect(px, py, 6 + rock * 7, 3, dark_rock)
                        if rock > 0.65:
                            rect(px + 3, py + 5, 5, 2, light_rock)
                        row += 1
            rect(x, y + p.h - 4, p.w, 4, "#6195ab" if ice else tint(theme.ground, -0.2))
            return
        if p.kind == "pipe":
            base = "#638b83" if world == 2 else "#855e75" if world == 5 else "#4c9290"
            rect(x + 5, y + 10, p.w - 10, p.h - 10, "#283f50")
            rect(x + 9, y + 10, p.w - 19, p.h - 10, base)
            rect(x + 12, y + 15, 5, p.h - 15, tint(base, 0.25))
            rect(x + p.w - 18, y + 15, 6, p.h - 15, tint(base, -0.16))
            rect(x, y, p.w, 18, "#283f50")
            rect(x + 2, y + 2, p.w - 4, 13, base)
            rect(x + 4, y + 3, p.w - 8, 3, tint(base, 0.36))
            rect(x + p.w - 12, y + 5, 5, 8, tint(base, -0.18))
            rect(x + 4, y + 10, 3, 3, "#d2d4ab")
            rect(x + p.w - 7, y + 10, 3, 3, "#d2d4ab")
            if p.destination is not None:
                rect(x + p.w / 2 - 6, y + 22, 12, 3, "#9de3c4")
                polygon(
                    [x + p.w / 2 - 5, y + 28, x + p.w / 2 + 5, y + 28, x + p.w / 2, y + 34],
                    "#9de3c4",
                )
            return
        if p.kind == "moving" or p.kind == "crumble":
            crumble = p.kind == "crumble"
            offset = math.sin(frame * 50) * 2 if crumble and p.crumble > 0 else 0
            color = "#a58c8a" if crumble else "#5e91a7"
            rect(x + offset, y, p.w, p.h, INK)
            rect(x + 2 + offset, y + 2, p.w - 4, p.h - 5, color)
            rect(x + 3 + offset, y + 2, p.w - 6, 4, tint(color, 0.25))
            i = 9
            while i < p.w - 4:
                rect(x + i + offset, y + 8, 3, 3, "#6c606d" if crumble else "#c2e4cf")
                if crumble:
                    polygon(
                        [
                            x + i,
                            y + 5,
                            x + i + 3,
                            y + 5,
                            x + i,
                            y + 10,
                            x + i + 4,
                            y + 14,
                            x + i + 1,
                            y + 13,
                            x + i - 3,
                            y + 9,
                        ],
                        "#695a65",
                    )
                i += 18
            if not crumble:
                rect(x + 5, y + p.h - 4, p.w - 10, 2, "#34667d")
            return
        used = p.used
        question = p.kind == "question" or p.kind == "hidden"
        if question:
            fill = "#7c888b" if used else "#dea856"
        else:
            fill = "#8fbdcc" if world == 3 else "#ba7968"
        local_x = 0.0
        while local_x < p.w:
            width = min(40, p.w - local_x)
            bx = x + local_x
            rect(bx, y, width, p.h, "#38414b")
            rect(bx + 2, y + 2, width - 4, p.h - 4, fill)
            rect(bx + 3, y + 3, width - 6, 3, tint(fill, 0.25))
            rect(bx + width - 5, y + 5, 2, p.h - 7, tint(fill, -0.2))
            rect(bx + 3, y + p.h - 5, width - 6, 2, tint(fill, -0.18))
            if question:
                rect(bx + 4, y + 9, 2, 2, tint(fill, -0.35))
                rect(bx + width - 6, y + p.h - 11, 2, 2, tint(fill, -0.35))
                if not used:
                    bob = js_round(math.sin(frame * 4) * 1)
                    painter.sprite(
                        QUESTION_MARK,
                        QUESTION_PALETTE,
                        bx + width / 2 - 5,
                        y + p.h / 2 - 7 + bob,
                        2,
                    )
                else:
                    rect(bx + width / 2 - 2, y + p.h / 2 - 2, 4, 4, "#aab7ad")
            else:
                rect(bx + 2, y + math.floor(p.h / 2), width - 4, 2, "#815b5b")
                rect(bx + 15, y + 6, 2, p.h / 2 - 6, "#815b5b")
                rect(bx + 8, y + p.h / 2 + 2, 2, p.h / 2 - 6, "#815b5b")
            local_x += 40

    # perigos -----------------------------------------------------------------------
    def hazards(self, game: Game) -> None:
        painter = self._painter
        rect = painter.rect
        polygon = painter.polygon
        frame = self._scene.frame
        for hazard in game.level.hazards:
            x = hazard.x
            y = hazard.y
            if hazard.kind == "moving":
                # ``frame`` == ``game.elapsed`` quando finito (ver ``render``).
                x += math.sin(frame * (hazard.speed or 1)) * (hazard.range or 30)
            if not painter.visible(x, y, hazard.w, hazard.h):
                continue
            if hazard.kind == "lava" or hazard.kind == "water":
                water = hazard.kind == "water"
                rect(x, y + 6, hazard.w, hazard.h - 6, "#347b94" if water else "#bd4e4b")
                i = 0
                while i < hazard.w:
                    offset = js_round(math.sin(frame * 3 + i / 21) * 3)
                    rect(
                        x + i,
                        y + offset,
                        min(16, hazard.w - i),
                        8,
                        "#b4edf3" if water else "#ffc176",
                    )
                    rect(
                        x + i + 2,
                        y + 9 + offset,
                        min(12, hazard.w - i - 2),
                        6,
                        "#62b7cd" if water else "#ec7957",
                    )
                    if i % 48 == 0:
                        rect(
                            x + i + 5,
                            y + 27 + math.sin(frame + i) * 4,
                            7,
                            4,
                            "#8dcbd5" if water else "#ec8e5f",
                        )
                    i += 16
            elif hazard.kind == "spikes":
                rect(x, y + hazard.h - 5, hazard.w, 5, "#53616c")
                i = 0
                while i < hazard.w:
                    polygon(
                        [x + i, y + hazard.h - 4, x + i + 8, y + 1, x + i + 16, y + hazard.h - 4],
                        "#d0d5d0",
                    )
                    polygon(
                        [
                            x + i + 8,
                            y + 3,
                            x + i + 8,
                            y + hazard.h - 4,
                            x + i + 15,
                            y + hazard.h - 4,
                        ],
                        "#8899a7",
                    )
                    i += 16
            else:
                # Chama orbital: oito línguas girando em torno de um núcleo.
                painter.save()
                painter.translate(x + hazard.w / 2, y + hazard.h / 2)
                painter.rotate(frame * 3)
                for i in range(8):
                    painter.save()
                    painter.rotate(i * math.pi / 4)
                    polygon(
                        [-5, -hazard.h * 0.28, 0, -hazard.h * 0.52, 7, -hazard.h * 0.34], "#ccd5cf"
                    )
                    painter.restore()
                rect(
                    -hazard.w * 0.26,
                    -hazard.h * 0.26,
                    hazard.w * 0.52,
                    hazard.h * 0.52,
                    "#78899a",
                )
                rect(-5, -5, 10, 10, "#ecc174")
                painter.restore()
