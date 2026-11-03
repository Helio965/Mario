"""Tela inicial: título LUME, subtítulo, JOGAR com o próximo destino, atalhos
(mapa, controles, configurações, créditos, sair), rótulo do tema do mundo
atual e o indicador ``0N / 05`` sobre o cenário desenhado pelo renderizador.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from game.settings import VIEW_HEIGHT, VIEW_WIDTH
from game.ui.screens import Screen
from game.ui.widgets import Button, Layer

if TYPE_CHECKING:
    from game.ui.interface import Interface

PLAY_WIDTH = 214
PLAY_HEIGHT = 52
LINKS: tuple[tuple[str, str, str], ...] = (
    ("map", "menu.map", "map"),
    ("controls", "menu.controls", "keys"),
    ("settings", "menu.settings", "settings"),
    ("credits", "menu.credits", "info"),
    ("quit", "menu.quit", "back"),
)


class MenuScreen(Screen):
    name = "menu"

    def __init__(self, ui: Interface) -> None:
        super().__init__(ui)
        self.star = (0, 0)

    def build(self) -> None:
        ui = self.ui
        style = ui.style
        p = style.palette
        t = ui.t
        save = ui.save
        level = ui.levels[max(0, min(save.unlocked, len(ui.levels) - 1))]
        layer = Layer(VIEW_WIDTH, style)
        layer.blit(ui.menu_fade(), (0, 0))
        self.group.clear()
        x = 52
        layer.icon(x, 40, "dot", 10, p.accent_dark)
        layer.text(x + 16, 38, t("game.eyebrow"), 9, p.eyebrow, bold=True, spacing=2)
        title = layer.text(x - 6, 52, t("game.title"), 104, p.ink, bold=True, spacing=-5)
        self.star = (title.right + 6, title.top + 22)
        sub = layer.text(x, title.bottom + 2, t("game.subtitle"), 12, p.ink, bold=True, spacing=4)
        y = layer.paragraph(x, sub.bottom + 12, t("game.tagline"), 11, p.muted, 420, line_height=19)
        y += 14
        progress = (
            t("menu.continue", world=level.world, stage=level.stage)
            if save.completed
            else t("menu.start_here")
        )
        self.group.add(
            Button(
                pygame.Rect(x, y, PLAY_WIDTH, PLAY_HEIGHT),
                t("menu.play"),
                self.play,
                kind="primary",
                icon="play",
                trailing="arrow",
                sublabel=progress,
                size=12,
                spacing=2,
                align="left",
                widget_id="play",
            )
        )
        y += PLAY_HEIGHT + 22
        actions = {
            "map": self.go_map,
            "controls": self.go_controls,
            "settings": self.go_settings,
            "credits": self.go_credits,
            "quit": ui.handlers.quit,
        }
        for i, (widget_id, key, icon) in enumerate(LINKS):
            column, row = i % 2, i // 2
            self.group.add(
                Button(
                    pygame.Rect(x + column * 150, y + row * 26, 140, 22),
                    t(key),
                    actions[widget_id],
                    kind="link",
                    icon=icon,
                    size=10,
                    bold=False,
                    align="left",
                    widget_id=widget_id,
                )
            )
        y += 3 * 26 + 8
        layer.icon(x, y + 5, "bullet", 8, p.section_icon)
        layer.text(x + 13, y, t("menu.saved_locally"), 8, p.note)
        # Rótulo do próximo destino com a cor do tema.
        label_w, label_h = 196, 74
        lx = VIEW_WIDTH - 58 - label_w
        ly = VIEW_HEIGHT - 66 - label_h
        layer.box(pygame.Rect(lx + 2, ly + 4, label_w, label_h), p.shadow, alpha=28)
        layer.box(pygame.Rect(lx, ly, label_w, label_h), p.scene_label, alpha=p.scene_label_alpha)
        layer.box(pygame.Rect(lx, ly, 3, label_h), p.accent)
        heading = "menu.next_frontier" if save.unlocked else "menu.first_destination"
        layer.text(lx + 19, ly + 13, t(heading), 8, p.scene_text, bold=True, spacing=1)
        layer.text(lx + 19, ly + 27, ui.theme_name(level.world), 15, p.ink, bold=True)
        subtitle = t("menu.scene_subtitle", subtitle=ui.theme_subtitle(level.world))
        layer.text(lx + 19, ly + 50, subtitle, 9, p.scene_text)
        # Indicador de mundos (pontos + 0N / 05).
        count = len(ui.themes)
        counter = t("menu.world_counter", current=f"{level.world:02d}", total=f"{count:02d}")
        dy = VIEW_HEIGHT - 29
        rect = layer.text(
            VIEW_WIDTH - 58, dy, counter, 8, p.scene_dot, bold=True, spacing=1, anchor="midright"
        )
        px = rect.left - 12
        for i in range(count - 1, -1, -1):
            active = i == level.world - 1
            w = 17 if active else 5
            px -= w
            layer.box(
                pygame.Rect(px, dy - 2, w, 5), p.scene_dot, radius=3, alpha=255 if active else 156
            )
            px -= 8
        self.layer = layer.render(VIEW_HEIGHT)
        self.group.viewport = pygame.Rect(0, 0, VIEW_WIDTH, VIEW_HEIGHT)
        self.group.content_height = VIEW_HEIGHT

    def draw(self, surface: pygame.Surface) -> None:
        style = self.style
        if self.layer is not None:
            surface.blit(self.layer, (0, 0))
        size = round(28 + 6 * style.pulse(2.4, 0.0, 1.0))
        star = style.icon("sparkle", size, style.palette.accent_dark)
        surface.blit(star, star.get_rect(center=self.star))
        self.group.draw(surface, style, None)

    # ----------------------------------------------------------------- ações
    def play(self) -> None:
        self.ui.handlers.play(self.ui.save.unlocked)

    def go_map(self) -> None:
        self.ui.handlers.menu()
        self.ui.show("map")

    def go_controls(self) -> None:
        self.ui.show("controls")

    def go_settings(self) -> None:
        self.ui.show("settings")

    def go_credits(self) -> None:
        self.ui.show("credits")

    def start(self) -> bool:
        self.play()
        return True
