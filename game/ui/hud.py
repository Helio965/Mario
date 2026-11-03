"""HUD em jogo e sobreposições: barra superior (vidas, pontos, moedas,
mundo/fase, tempo, poder ativo), barra do guardião, FPS opcional, avisos
(toast) e legendas.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import pygame

from game.core.game import Game
from game.core.types import Enemy
from game.rendering.sprites import PLAYER_PALETTE, PLAYER_UPPER
from game.settings import VIEW_HEIGHT, VIEW_WIDTH
from game.ui.theme import rgb

if TYPE_CHECKING:
    from game.ui.interface import Interface

BOSS_RANGE = 850.0
TIME_LOW = 30.0
TOAST_SLIDE = 0.2
TOAST_FADE = 0.3
MARK_UNIT = 1.5


class Hud:
    def __init__(self, ui: Interface) -> None:
        self.ui = ui
        self._mark: pygame.Surface | None = None
        self._boss_id: str | None = None
        self._boss_fill = 0.0
        self._toast_key: tuple[str, int] | None = None
        self._toast_surface: pygame.Surface | None = None

    # ------------------------------------------------------------ consultas
    @staticmethod
    def nearby_boss(game: Game) -> Enemy | None:
        """Guardião vivo a menos de 850 px do jogador (como no original)."""
        px = game.player.x
        return next(
            (
                enemy
                for enemy in game.enemies
                if enemy.kind == "boss" and enemy.alive and abs(enemy.x - px) < BOSS_RANGE
            ),
            None,
        )

    def power_label(self, game: Game) -> str:
        player = game.player
        if player.star > 0:
            return self.ui.t("hud.power_star", seconds=math.ceil(player.star))
        return self.ui.t(f"hud.power_{player.power}")

    def mark(self) -> pygame.Surface:
        """Figura em pixel art do protagonista (tronco e cabeça), desenhada uma vez."""
        if self._mark is None:
            rows = PLAYER_UPPER
            width = math.ceil(len(rows[0]) * MARK_UNIT)
            height = math.ceil(len(rows) * MARK_UNIT)
            surface = pygame.Surface((width, height), pygame.SRCALPHA)
            cell = math.ceil(MARK_UNIT)
            for y, row in enumerate(rows):
                for x, char in enumerate(row):
                    color = PLAYER_PALETTE.get(char)
                    if color is not None:
                        surface.fill(
                            rgb(color), (round(x * MARK_UNIT), round(y * MARK_UNIT), cell, cell)
                        )
            self._mark = surface
        return self._mark

    # ------------------------------------------------------------- atualizar
    def update(self, game: Game | None, dt: float) -> None:
        boss = self.nearby_boss(game) if game is not None else None
        if boss is None:
            self._boss_id = None
            self._boss_fill = 0.0
            return
        target = max(0.0, min(1.0, boss.health / (boss.hp or 4)))
        if boss.id != self._boss_id or not self.ui.style.motion:
            self._boss_id = boss.id
            self._boss_fill = target
        else:
            self._boss_fill += (target - self._boss_fill) * min(1.0, dt * 12)

    # --------------------------------------------------------------- desenho
    def draw(self, surface: pygame.Surface, game: Game) -> None:
        ui = self.ui
        style = ui.style
        p = style.palette
        t = ui.t
        bar = pygame.Rect(25, 12, VIEW_WIDTH - 50, 46)
        style.round_rect(surface, bar.move(0, 3), p.hud, 7, 60)
        style.round_rect(surface, bar, p.hud, 7, p.hud_alpha, border=p.hud_border)
        mark = self.mark()
        surface.blit(mark, (bar.x + 14, bar.centery - mark.get_height() // 2))
        name_x = bar.x + 14 + mark.get_width() + 10
        name = style.text(t("game.title"), 14, p.hud_text, True, 1)
        surface.blit(name, (name_x, bar.y + 8))
        power = style.text(self.power_label(game), 8, p.hud_sub)
        surface.blit(power, (name_x, bar.y + 27))
        stats: list[tuple[str | None, str, str, bool]] = [
            ("heart", t("hud.lives"), str(game.lives), False),
            (None, t("hud.score"), ui.format_score(game.score), False),
            ("coin", t("hud.coins"), str(game.coins_total), False),
            (
                None,
                t("hud.stage"),
                t("hud.stage_value", world=game.level.world, stage=game.level.stage),
                False,
            ),
            (None, t("hud.time"), str(max(0, math.ceil(game.time))), game.time <= TIME_LOW),
        ]
        x0 = bar.x + 218
        x1 = bar.right - 170
        step = (x1 - x0) / len(stats)
        for i, (icon, label, value, low) in enumerate(stats):
            x = round(x0 + i * step)
            if icon:
                surface.blit(style.icon(icon, 15, p.hud_icon), (x, bar.centery - 7))
                x += 21
            surface.blit(style.text(label, 7, p.hud_label, True, 1), (x, bar.y + 9))
            surface.blit(
                style.text(value, 14, p.time_low if low else p.hud_text, True, 1), (x, bar.y + 21)
            )
        # Dica de pausa (a tecla configurada) no canto direito da barra.
        badge = pygame.Rect(bar.right - 46, bar.centery - 15, 31, 31)
        style.round_rect(surface, badge, p.hud_badge, 4)
        pause_icon = style.icon("pause", 17, p.hud_sub)
        surface.blit(pause_icon, pause_icon.get_rect(center=badge.center))
        hint = style.text(ui.key_label(ui.primary_key("pause")), 7, p.hud_label, True, 1)
        surface.blit(hint, (badge.x - 8 - hint.get_width(), badge.centery - hint.get_height() // 2))
        boss = self.nearby_boss(game)
        if boss is not None:
            self.boss_bar(surface, boss, bar.bottom + 9)

    def boss_bar(self, surface: pygame.Surface, boss: Enemy, y: int) -> None:
        style = self.ui.style
        p = style.palette
        t = self.ui.t
        box = pygame.Rect((VIEW_WIDTH - 380) // 2, y, 380, 30)
        style.round_rect(surface, box, p.hud, 5, p.hud_alpha)
        label = style.text(t("hud.guardian"), 7, p.boss_text, True, 1)
        surface.blit(label, (box.x + 14, box.centery - label.get_height() // 2))
        maximum = boss.hp or 4
        value = style.text(t("hud.boss_health", health=boss.health, max=maximum), 8, p.boss_text)
        surface.blit(
            value, (box.right - 14 - value.get_width(), box.centery - value.get_height() // 2)
        )
        track_x = box.x + 14 + label.get_width() + 10
        track = pygame.Rect(
            track_x, box.centery - 2, box.right - 14 - value.get_width() - 10 - track_x, 5
        )
        style.round_rect(surface, track, p.boss_track, 3)
        fill = round(track.w * self._boss_fill)
        if fill > 0:
            style.round_rect(surface, pygame.Rect(track.x, track.y, fill, track.h), p.boss_fill, 3)

    def draw_overlays(self, surface: pygame.Surface, fps: float | None) -> None:
        """Legenda, toast e FPS, sobre qualquer tela."""
        ui = self.ui
        style = ui.style
        p = style.palette
        subtitle = ui.subtitle_text
        if subtitle is not None:
            lines = style.wrap(subtitle, 14, 760)
            width = max(style.measure(line, 14)[0] for line in lines) + 40
            height = 12 + len(lines) * 20
            box = pygame.Rect((VIEW_WIDTH - width) // 2, VIEW_HEIGHT - 80 - height, width, height)
            style.round_rect(surface, box, p.subtitle_bg, 5, 200)
            y = box.y + 6
            for line in lines:
                text = style.text(line, 14, p.subtitle_text)
                surface.blit(text, (box.centerx - text.get_width() // 2, y))
                y += 20
        toast = ui.toast_text
        if toast is not None:
            self.toast(surface, toast, ui.toast_age, ui.toast_remaining)
        if fps is not None:
            text = style.text(ui.t("hud.fps", fps=round(fps)), 9, p.hud_text, True)
            box = pygame.Rect(10, VIEW_HEIGHT - 26, text.get_width() + 14, 18)
            style.round_rect(surface, box, p.hud, 4, 200)
            surface.blit(text, (box.x + 7, box.y + 2))

    def _compose_toast(self, text: str) -> pygame.Surface:
        """Caixa + texto do aviso numa única superfície (cacheada por texto e paleta)."""
        style = self.ui.style
        p = style.palette
        key = (text, id(p))
        if self._toast_key == key and self._toast_surface is not None:
            return self._toast_surface
        lines = style.wrap(text, 12, 700)
        width = max(style.measure(line, 12)[0] for line in lines) + 46
        height = 26 + len(lines) * 18
        composed = pygame.Surface((width, height + 8), pygame.SRCALPHA)
        box = pygame.Rect(0, 0, width, height)
        style.round_rect(composed, box.move(0, 6), p.shadow, 7, 40)
        style.round_rect(composed, box, p.toast, 7, border=p.toast_border)
        y = 13
        for line in lines:
            line_surface = style.text(line, 12, p.toast_text)
            composed.blit(line_surface, (width // 2 - line_surface.get_width() // 2, y))
            y += 18
        self._toast_key = key
        self._toast_surface = composed
        return composed

    def toast(self, surface: pygame.Surface, text: str, age: float, remaining: float) -> None:
        style = self.ui.style
        composed = self._compose_toast(text)
        slide = 0
        alpha = 255
        if style.motion:
            slide = round((1 - min(1.0, age / TOAST_SLIDE)) * 10)
            alpha = round(255 * min(1.0, remaining / TOAST_FADE))
        composed.set_alpha(alpha)
        height = composed.get_height() - 8
        surface.blit(
            composed, ((VIEW_WIDTH - composed.get_width()) // 2, VIEW_HEIGHT - 25 - height + slide)
        )
