"""Telas da interface: bases ``Screen``/``PanelScreen`` e telas simples.

* ``Screen``: conjunto de widgets + camada estática; recebe ações de navegação
  (``nav``), mouse e teclas; ``enter``/``rebuild`` reconstroem o conteúdo.
* ``PanelScreen``: painel centralizado sobre um fundo escurecido, com rótulo
  (eyebrow), título, botão "Voltar" (ou ícone de estado) e conteúdo rolável.
* Telas de estado (pausa, fase concluída, fim de jogo), controles e créditos.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Literal

import pygame

from game.settings import VIEW_HEIGHT, VIEW_WIDTH
from game.systems.save import ACTIONS
from game.ui.theme import Style
from game.ui.widgets import Button, ButtonKind, Direction, Layer, WidgetGroup

if TYPE_CHECKING:
    from game.ui.interface import Interface

NavAction = Literal["up", "down", "left", "right", "confirm", "back", "next", "prev", "start"]
MARGIN = 20
APPEAR_SECONDS = 0.15
DIRECTIONS: dict[str, Direction] = {"up": "up", "down": "down", "left": "left", "right": "right"}
STATE_BUTTON_WIDTH = 285
ButtonSpec = tuple[str, str, ButtonKind, str | None, str | None, Callable[[], None]]


class Screen:
    """Base de todas as telas: widgets, camada estática, navegação e mouse."""

    name: str = ""

    def __init__(self, ui: Interface) -> None:
        self.ui = ui
        self.group = WidgetGroup()
        self.layer: pygame.Surface | None = None
        self.age = 0.0

    @property
    def style(self) -> Style:
        return self.ui.style

    # ---------------------------------------------------------------- ciclo
    def enter(self) -> None:
        self.age = 0.0
        self.group.scroll = 0
        self.build()
        self.group.focus_first()

    def rebuild(self) -> None:
        """Reconstrói mantendo foco (por id) e rolagem."""
        focused = self.group.focused_id
        scroll = self.group.scroll
        self.build()
        self.group.scroll_to(scroll)
        if not (focused and self.group.focus_id(focused)):
            self.group.focus_first()
            self.group.scroll_to(scroll)

    def build(self) -> None:
        raise NotImplementedError

    def update(self, dt: float) -> None:
        self.age += dt

    def appear(self) -> float:
        """Progresso 0–1 da animação de entrada (sempre 1 com redução de movimento)."""
        if not self.style.motion:
            return 1.0
        return max(0.0, min(1.0, self.age / APPEAR_SECONDS))

    def draw(self, surface: pygame.Surface) -> None:
        raise NotImplementedError

    # -------------------------------------------------------------- entrada
    def nav(self, action: NavAction) -> bool:
        direction = DIRECTIONS.get(action)
        if direction is not None:
            return self.group.nav(direction)
        if action == "confirm":
            return self.group.activate()
        if action == "next":
            return self.group.tab(1)
        if action == "prev":
            return self.group.tab(-1)
        if action == "back":
            self.back()
            return True
        if action == "start":
            return self.start()
        return False

    def back(self) -> None:
        """Esc / botão B. Por padrão não faz nada."""

    def start(self) -> bool:
        """Botão Start do gamepad. Por padrão ativa o widget focado."""
        return self.group.activate()

    def key_down(self, event: pygame.event.Event) -> bool:
        """Primeira chance a teclas brutas (captura de atalhos); ``True`` consome."""
        return False

    def mouse_move(self, pos: tuple[int, int], pressed: bool) -> None:
        self.group.mouse_move(pos, pressed)

    def mouse_down(self, pos: tuple[int, int]) -> bool:
        return self.group.mouse_down(pos)

    def mouse_up(self, pos: tuple[int, int]) -> None:
        self.group.mouse_up(pos)

    def wheel(self, steps: int) -> None:
        self.group.wheel(steps)


class PanelScreen(Screen):
    """Painel centralizado com cabeçalho e conteúdo rolável."""

    label_key = ""
    title_key = ""
    max_width = 930
    pad_x = 30
    pad_y = 26
    state_icon: str | None = None

    def __init__(self, ui: Interface) -> None:
        super().__init__(ui)
        self.panel = pygame.Rect(0, 0, 0, 0)

    def label(self) -> str:
        return self.ui.t(self.label_key)

    def title(self) -> str:
        return self.ui.t(self.title_key)

    def back_label(self) -> str:
        return self.ui.t("common.back")

    def build(self) -> None:
        style = self.style
        width = min(self.max_width, VIEW_WIDTH - 2 * MARGIN)
        inner = width - 2 * self.pad_x
        layer = Layer(inner, style)
        self.group.clear()
        y = self.heading(layer, inner)
        y = self.content(layer, inner, y)
        height = max(y, layer.bottom)
        self.layer = layer.render(height)
        self.group.content_height = height
        panel_h = min(VIEW_HEIGHT - 2 * MARGIN, height + 2 * self.pad_y)
        self.panel = pygame.Rect(
            (VIEW_WIDTH - width) // 2, (VIEW_HEIGHT - panel_h) // 2, width, panel_h
        )
        self.group.viewport = pygame.Rect(
            self.panel.x + self.pad_x, self.panel.y + self.pad_y, inner, panel_h - 2 * self.pad_y
        )
        self.group.scroll_to(self.group.scroll)

    def heading(self, layer: Layer, width: int) -> int:
        p = self.style.palette
        if self.state_icon is not None:
            cx = width // 2
            layer.circle((cx, 29), 29, p.state_icon_bg)
            layer.icon(cx, 29, self.state_icon, 27, p.state_icon, anchor="center")
            layer.text(cx, 70, self.label(), 9, p.eyebrow, bold=True, spacing=2, anchor="midtop")
            y = layer.paragraph(
                cx - 200,
                90,
                self.title(),
                24,
                p.ink,
                400,
                line_height=28,
                bold=True,
                align="center",
            )
            return y + 4
        layer.text(0, 0, self.label(), 9, p.eyebrow, bold=True, spacing=2)
        rect = layer.text(0, 16, self.title(), 26, p.ink, bold=True)
        self.group.add(
            Button(
                pygame.Rect(width - 104, 6, 104, 32),
                self.back_label(),
                self.back,
                kind="close",
                icon="back",
                size=10,
                widget_id="back",
            )
        )
        return rect.bottom + 18

    def content(self, layer: Layer, width: int, y: int) -> int:
        raise NotImplementedError

    def back(self) -> None:
        self.ui.show("menu")

    # ------------------------------------------------------------ auxiliares
    def section_title(self, layer: Layer, x: int, y: int, icon: str, text: str) -> int:
        p = self.style.palette
        layer.icon(x, y, icon, 18, p.section_icon)
        layer.text(x + 27, y + 1, text, 13, p.ink, bold=True)
        return y + 34

    def stats(self, layer: Layer, width: int, y: int, items: list[tuple[str, str, bool]]) -> int:
        """Linha de resultados ``(rótulo, valor, pequeno)`` entre duas regras."""
        p = self.style.palette
        layer.line((0, y), (width, y), p.line)
        y += 16
        count = max(1, len(items))
        col_w = min(150, (width - 20) // count)
        total = col_w * count + 28 * (count - 1)
        x0 = (width - total) // 2
        for i, (label, value, small) in enumerate(items):
            cx = x0 + i * (col_w + 28) + col_w // 2
            layer.text(cx, y, label, 8, p.stat_label, bold=True, spacing=1, anchor="midtop")
            size = 12 if small else 20
            layer.text(
                cx,
                y + 18 + (6 if small else 0),
                value,
                size,
                p.stat_value,
                bold=True,
                anchor="midtop",
            )
        y += 62
        layer.line((0, y), (width, y), p.line)
        return y + 8

    def buttons(self, width: int, y: int, specs: list[ButtonSpec]) -> int:
        """Coluna de botões centralizada; ``specs``: (id, rótulo, tipo, ícone, ícone final, ação)."""
        x = (width - STATE_BUTTON_WIDTH) // 2
        for widget_id, label, kind, icon, trailing, action in specs:
            height = 31 if kind == "text" else 45
            self.group.add(
                Button(
                    pygame.Rect(x, y, STATE_BUTTON_WIDTH, height),
                    label,
                    action,
                    kind=kind,
                    icon=icon,
                    trailing=trailing,
                    size=12 if kind != "text" else 11,
                    bold=kind != "text",
                    widget_id=widget_id,
                )
            )
            y += height + 10
        return y

    def draw(self, surface: pygame.Surface) -> None:
        style = self.style
        p = style.palette
        t = self.appear()
        surface.blit(self.ui.backdrop(round(p.backdrop_alpha * t)), (0, 0))
        offset = round((1 - t) * 12)
        panel = self.panel.move(0, offset)
        style.shadow(surface, panel, 10)
        style.round_rect(
            surface, panel, p.panel, 10, border=p.line if style.high_contrast else None, width=2
        )
        viewport = self.group.viewport
        self.group.viewport = viewport.move(0, offset)
        self.group.draw(surface, style, self.layer)
        self.group.viewport = viewport


class StatePanel(PanelScreen):
    """Painel estreito e centralizado das telas de estado do jogo."""

    max_width = 530
    pad_x = 36
    pad_y = 28

    def description(self, layer: Layer, width: int, y: int, text: str) -> int:
        p = self.style.palette
        return (
            layer.paragraph(0, y + 6, text, 11, p.note, width, line_height=19, align="center") + 8
        )

    def go_menu(self) -> None:
        self.ui.handlers.menu()
        self.ui.show("menu")


class PauseScreen(StatePanel):
    name = "pause"
    label_key = "screens.pause.label"
    title_key = "screens.pause.title"
    state_icon = "pause"

    def content(self, layer: Layer, width: int, y: int) -> int:
        ui = self.ui
        game = ui.game
        if game is not None:
            text = ui.t(
                "pause.description",
                level=ui.level_name(game.level),
                world=game.level.world,
                stage=game.level.stage,
            )
        else:
            text = ui.t("pause.journey")
        y = self.description(layer, width, y, text)
        y = self.buttons(
            width,
            y + 8,
            [
                ("resume", ui.t("pause.resume"), "primary", "play", "arrow", ui.handlers.resume),
                ("restart", ui.t("pause.restart"), "secondary", None, None, ui.handlers.restart),
                ("settings", ui.t("pause.settings"), "secondary", None, None, self.open_settings),
                ("menu", ui.t("pause.menu"), "text", None, None, self.go_menu),
            ],
        )
        footnote = ui.t("pause.footnote", button=ui.key_label(ui.primary_key("pause")))
        return layer.paragraph(
            0, y + 6, footnote, 9, self.style.palette.note, width, align="center"
        )

    def open_settings(self) -> None:
        self.ui.show("settings", self.ui.game)

    def back(self) -> None:
        self.ui.handlers.resume()

    def start(self) -> bool:
        self.ui.handlers.resume()
        return True


class CompleteScreen(StatePanel):
    name = "complete"
    label_key = "screens.complete.label"
    state_icon = "trophy"

    def is_final(self) -> bool:
        game = self.ui.game
        return game is not None and game.level_index >= len(self.ui.levels) - 1

    def title(self) -> str:
        return self.ui.t(
            "screens.complete.title_final" if self.is_final() else "screens.complete.title"
        )

    def content(self, layer: Layer, width: int, y: int) -> int:
        ui = self.ui
        game = ui.game
        final = self.is_final()
        name = ui.level_name(game.level) if game is not None else ""
        text = f"{name}\n{ui.t('complete.final' if final else 'complete.unlocked')}"
        y = self.description(layer, width, y, text)
        relic = game is not None and game.found_relic
        y = self.stats(
            layer,
            width,
            y + 6,
            [
                (ui.t("stats.score"), ui.format_score(game.score if game else 0), False),
                (ui.t("stats.coins"), str(game.coins_total if game else 0), False),
                (
                    ui.t("stats.relic"),
                    ui.t("complete.relic_found" if relic else "complete.relic_missing"),
                    True,
                ),
            ],
        )
        return self.buttons(
            width,
            y + 8,
            [
                (
                    "next",
                    ui.t("complete.map" if final else "complete.next"),
                    "primary",
                    "map" if final else "play",
                    "arrow",
                    self.next,
                ),
                ("map", ui.t("complete.world_map"), "secondary", None, None, self.go_map),
                ("menu", ui.t("complete.menu"), "text", None, None, self.go_menu),
            ],
        )

    def next(self) -> None:
        game = self.ui.game
        if game is not None and game.level_index < len(self.ui.levels) - 1:
            self.ui.handlers.play(game.level_index + 1)
        else:
            self.go_map()

    def go_map(self) -> None:
        self.ui.handlers.menu()
        self.ui.show("map")


class GameOverScreen(StatePanel):
    name = "gameover"
    label_key = "screens.gameover.label"
    title_key = "screens.gameover.title"
    state_icon = "heart"

    def content(self, layer: Layer, width: int, y: int) -> int:
        ui = self.ui
        game = ui.game
        y = self.description(layer, width, y, ui.t("gameover.description"))
        y = self.stats(
            layer,
            width,
            y + 6,
            [
                (ui.t("stats.score"), ui.format_score(game.score if game else 0), False),
                (ui.t("stats.coins"), str(game.coins_total if game else 0), False),
            ],
        )
        return self.buttons(
            width,
            y + 8,
            [
                ("retry", ui.t("gameover.retry"), "primary", "play", "arrow", ui.handlers.restart),
                ("menu", ui.t("gameover.menu"), "text", None, None, self.go_menu),
            ],
        )


GAMEPAD_ROWS: tuple[tuple[str, str], ...] = (
    ("controls.actions.move", "controls.gamepad_move"),
    ("controls.actions.jump", "controls.gamepad_jump"),
    ("controls.actions.run", "controls.gamepad_run"),
    ("controls.actions.ability", "controls.gamepad_ability"),
    ("controls.actions.pause", "controls.gamepad_pause"),
    ("controls.actions.menus", "controls.gamepad_menus"),
)


class ControlsScreen(PanelScreen):
    name = "controls"
    label_key = "screens.controls.label"
    title_key = "screens.controls.title"

    def content(self, layer: Layer, width: int, y: int) -> int:
        ui = self.ui
        p = self.style.palette
        col = (width - 61) // 2
        right = col + 61
        top = y
        # Teclado: uma linha por ação, com as teclas configuradas.
        yl = self.section_title(layer, 0, y, "keys", ui.t("controls.keyboard"))
        for action in ACTIONS:
            label = layer.text(0, yl + 10, ui.t(f"controls.actions.{action}"), 10, p.kbd_text)
            x = col
            for key in reversed(ui.binding_labels(action)):
                w = self.style.measure(key, 9, True, 1)[0] + 12
                x -= w
                layer.kbd(x, yl + 8, key)
                x -= 4
            row_bottom = yl + max(36, label.height + 20)
            layer.line((0, row_bottom), (col, row_bottom), p.line)
            yl = row_bottom
        self.group.add(
            Button(
                pygame.Rect(0, yl + 12, col, 24),
                ui.t("controls.remap"),
                self.open_settings,
                kind="link",
                icon="settings",
                size=10,
                align="left",
                widget_id="remap",
            )
        )
        yl += 44
        # Gamepad (e navegação dos menus).
        yr = self.section_title(layer, right, y, "gamepad", ui.t("controls.gamepad"))
        for label_key, value_key in GAMEPAD_ROWS:
            label = layer.text(right, yr + 10, ui.t(label_key), 10, p.kbd_text)
            layer.text(right + col, yr + 11, ui.t(value_key), 9, p.note, anchor="topright")
            row_bottom = yr + max(36, label.height + 20)
            layer.line((right, row_bottom), (right + col, row_bottom), p.line)
            yr = row_bottom
        yr = layer.paragraph(
            right, yr + 13, ui.t("controls.ui_hint"), 10, p.note, col, line_height=17
        )
        bottom = max(yl, yr)
        layer.line((col + 30, top), (col + 30, bottom), p.line)
        y = bottom + 21
        # Dica destacada.
        title = ui.t("controls.tip_title")
        body = ui.t("controls.tip")
        lines = self.style.wrap(body, 10, width - 70)
        box_h = 14 + 16 + len(lines) * 17 + 12
        layer.box(pygame.Rect(0, y, width, box_h), p.tip_bg, radius=6)
        layer.icon(18, y + box_h // 2, "star", 22, p.section_icon, anchor="midleft")
        layer.text(56, y + 14, title, 10, p.tip_title, bold=True)
        layer.paragraph(56, y + 30, body, 10, p.tip_text, width - 70, line_height=17)
        return y + box_h

    def open_settings(self) -> None:
        self.ui.show("settings")


class CreditsScreen(PanelScreen):
    name = "credits"
    label_key = "screens.credits.label"
    title_key = "screens.credits.title"

    def content(self, layer: Layer, width: int, y: int) -> int:
        ui = self.ui
        p = self.style.palette
        cx = width // 2
        layer.icon(cx, y + 24, "sparkle", 46, p.section_icon, anchor="center")
        y += 56
        y = (
            layer.text(cx, y, ui.t("credits.title"), 22, p.ink, bold=True, anchor="midtop").bottom
            + 10
        )
        y = layer.paragraph(
            cx - 285, y, ui.t("credits.intro"), 11, p.note, 570, line_height=19, align="center"
        )
        y += 16
        layer.line((0, y), (width, y), p.line)
        y += 18
        col = (width - 30) // 2
        bottoms = []
        for i, (label_key, text_key) in enumerate(
            (("credits.art_label", "credits.art"), ("credits.music_label", "credits.music"))
        ):
            x = i * (col + 30)
            layer.text(x, y, ui.t(label_key), 8, p.accent_dark, bold=True, spacing=1)
            bottoms.append(
                layer.paragraph(x, y + 18, ui.t(text_key), 10, p.note, col, line_height=17)
            )
        y = max(bottoms) + 12
        layer.line((0, y), (width, y), p.line)
        y += 16
        return layer.paragraph(
            cx - 300, y, ui.t("credits.license"), 9, p.note, 600, line_height=16, align="center"
        )
