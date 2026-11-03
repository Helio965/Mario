"""Tela de configurações: volumes, experiência (efeitos, tela cheia, FPS,
redução de movimento, alto contraste, legendas), tela (escala, limite de FPS,
qualidade, idioma), remapeamento de teclas com captura e reinício do progresso
com confirmação. Cada mudança chama ``handlers.update_settings``.
"""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

import pygame

from game.settings import FPS_OPTIONS, QUALITY_LEVELS, SCALE_OPTIONS
from game.systems.save import ACTIONS, DEFAULT_BINDINGS, LANGUAGES, Settings
from game.ui.screens import PanelScreen
from game.ui.widgets import BindingRow, Button, Layer, Selector, Slider, Toggle

if TYPE_CHECKING:
    from game.ui.interface import Interface

VOLUMES: tuple[str, ...] = ("music", "sfx", "voice", "ambient")
TOGGLES: tuple[str, ...] = (
    "effects",
    "fullscreen",
    "show_fps",
    "subtitles",
    "reduced_motion",
    "high_contrast",
)


class SettingsScreen(PanelScreen):
    name = "settings"
    label_key = "screens.settings.label"
    title_key = "screens.settings.title"

    def __init__(self, ui: Interface) -> None:
        super().__init__(ui)
        self.capturing: str | None = None
        self.confirming = False

    def enter(self) -> None:
        self.capturing = None
        self.confirming = False
        super().enter()

    def back_label(self) -> str:
        if self.ui.settings_return == "pause":
            return self.ui.t("common.back_to_pause")
        return self.ui.t("common.back")

    # ------------------------------------------------------------- conteúdo
    def content(self, layer: Layer, width: int, y: int) -> int:
        ui = self.ui
        style = self.style
        p = style.palette
        t = ui.t
        s = ui.save.settings
        col = (width - 61) // 2
        right = col + 61
        top = y
        # Som: um controle por barramento.
        yl = self.section_title(layer, 0, y, "sound", t("settings.sound"))
        for name in VOLUMES:
            value = float(getattr(s, name))
            self.group.add(
                Slider(
                    pygame.Rect(0, yl, col, 36),
                    t(f"settings.{name}"),
                    value,
                    partial(self.change_volume, name),
                    self.percent,
                    widget_id=f"slider-{name}",
                )
            )
            yl += 54
        yl = layer.paragraph(0, yl, t("settings.sound_note"), 9, p.note, col, line_height=15) + 4
        # Experiência: interruptores.
        yr = self.section_title(layer, right, y, "settings", t("settings.experience"))
        for name in TOGGLES:
            lines = style.wrap(t(f"settings.{name}_desc"), 9, col - 60)
            height = 18 + 4 + len(lines) * 13 + 8
            self.group.add(
                Toggle(
                    pygame.Rect(right, yr, col, height),
                    t(f"settings.{name}"),
                    "\n".join(lines),
                    bool(getattr(s, name)),
                    partial(self.change_toggle, name),
                    widget_id=f"toggle-{name}",
                )
            )
            layer.line((right, yr + height + 5), (right + col, yr + height + 5), p.line)
            yr += height + 14
        layer.line((col + 30, top), (col + 30, max(yl, yr) - 8), p.line)
        y = max(yl, yr) + 14
        # Tela: seletores em duas colunas.
        layer.line((0, y), (width, y), p.line)
        y += 18
        y = self.section_title(layer, 0, y, "full", t("settings.display"))
        scale_options = [
            t("settings.scale_fit") if scale == 0 else t("settings.scale_value", scale=scale)
            for scale in SCALE_OPTIONS
        ]
        fps_options = [
            t("settings.fps_unlimited") if fps == 0 else t("settings.fps_value", fps=fps)
            for fps in FPS_OPTIONS
        ]
        quality_options = [t(f"settings.quality_{quality}") for quality in QUALITY_LEVELS]
        language_options = [t(f"settings.languages.{code}") for code in LANGUAGES]
        selectors: list[tuple[str, list[str], int, partial[None]]] = [
            ("scale", scale_options, _index(SCALE_OPTIONS, s.scale, 0), partial(self.change_scale)),
            (
                "fps_limit",
                fps_options,
                _index(FPS_OPTIONS, s.fps_limit, 1),
                partial(self.change_fps),
            ),
            (
                "quality",
                quality_options,
                _index(QUALITY_LEVELS, s.quality, 0),
                partial(self.change_quality),
            ),
            (
                "language",
                language_options,
                _index(LANGUAGES, s.language, 0),
                partial(self.change_language),
            ),
        ]
        row_y = y
        for i, (name, options, index, action) in enumerate(selectors):
            column, row = i % 2, i // 2
            lines = style.wrap(t(f"settings.{name}_desc"), 9, col - Selector.BOX_W - 12)
            height = 18 + 4 + len(lines) * 13 + 6
            self.group.add(
                Selector(
                    pygame.Rect(column * right, row_y + row * 62, col, height),
                    t(f"settings.{name}"),
                    "\n".join(lines),
                    options,
                    index,
                    action,
                    widget_id=f"select-{name}",
                )
            )
        y = row_y + 2 * 62 + 4
        # Controles: uma linha por ação; ativar captura a próxima tecla.
        layer.line((0, y), (width, y), p.line)
        y += 18
        y = self.section_title(layer, 0, y, "keys", t("settings.bindings"))
        y = (
            layer.paragraph(
                0, y - 10, t("settings.bindings_desc"), 9, p.note, width, line_height=15
            )
            + 8
        )
        rows = (len(ACTIONS) + 1) // 2
        for i, action_name in enumerate(ACTIONS):
            column, row = i % 2, i // 2
            self.group.add(
                BindingRow(
                    pygame.Rect(column * right, y + row * 40, col, 34),
                    t(f"controls.actions.{action_name}"),
                    ui.binding_labels(action_name),
                    partial(self.capture, action_name),
                    capturing=self.capturing == action_name,
                    prompt=t("settings.press_key"),
                    hint=t("settings.press_key_hint"),
                    widget_id=f"bind-{action_name}",
                )
            )
        y += rows * 40 + 6
        self.group.add(
            Button(
                pygame.Rect(0, y, 230, 34),
                t("settings.bindings_reset"),
                self.restore_bindings,
                kind="secondary",
                size=10,
                widget_id="bindings-reset",
            )
        )
        y += 34 + 28
        # Reinício do progresso com confirmação.
        layer.line((0, y - 14), (width, y - 14), p.line)
        layer.text(0, y, t("settings.reset_title"), 11, p.body, bold=True)
        layer.paragraph(0, y + 18, t("settings.reset_desc"), 9, p.note, width - 230, line_height=15)
        self.group.add(
            Button(
                pygame.Rect(width - 200, y, 200, 36),
                t("settings.reset"),
                self.ask_reset,
                kind="danger",
                size=10,
                widget_id="reset",
            )
        )
        y += 56
        if self.confirming:
            lines = style.wrap(t("settings.reset_confirm_desc"), 10, width - 30)
            box_h = 14 + 16 + len(lines) * 15 + 10 + 33 + 15
            layer.box(
                pygame.Rect(0, y, width, box_h), p.confirm_bg, radius=5, border=p.confirm_border
            )
            layer.text(15, y + 14, t("settings.reset_confirm_title"), 10, p.confirm_text, bold=True)
            by = layer.paragraph(
                15,
                y + 30,
                t("settings.reset_confirm_desc"),
                10,
                p.confirm_text,
                width - 30,
                line_height=15,
            )
            self.group.add(
                Button(
                    pygame.Rect(15, by + 10, 160, 33),
                    t("settings.reset_yes"),
                    self.confirm_reset,
                    kind="danger",
                    size=10,
                    widget_id="reset-yes",
                )
            )
            self.group.add(
                Button(
                    pygame.Rect(185, by + 10, 130, 33),
                    t("settings.reset_no"),
                    self.cancel_reset,
                    kind="secondary",
                    size=10,
                    widget_id="reset-no",
                )
            )
            y += box_h + 10
        return y + 2

    # ---------------------------------------------------------------- ações
    def percent(self, value: float) -> str:
        return self.ui.t("settings.percent", value=round(value * 100))

    def _settings(self) -> Settings:
        return self.ui.save.settings.copy()

    def change_volume(self, name: str, value: float) -> None:
        settings = self._settings()
        setattr(settings, name, value)
        self.ui.apply_settings(settings)

    def change_toggle(self, name: str, value: bool) -> None:
        if name == "fullscreen":
            # A janela pertence à aplicação: ela alterna, grava e devolve o estado real.
            self.ui.handlers.toggle_fullscreen()
            widget = self.group.find("toggle-fullscreen")
            if isinstance(widget, Toggle):
                widget.value = self.ui.save.settings.fullscreen
            return
        settings = self._settings()
        setattr(settings, name, value)
        self.ui.apply_settings(settings)

    def change_scale(self, index: int) -> None:
        settings = self._settings()
        settings.scale = SCALE_OPTIONS[index]
        self.ui.apply_settings(settings)

    def change_fps(self, index: int) -> None:
        settings = self._settings()
        settings.fps_limit = FPS_OPTIONS[index]
        self.ui.apply_settings(settings)

    def change_quality(self, index: int) -> None:
        settings = self._settings()
        settings.quality = QUALITY_LEVELS[index]
        self.ui.apply_settings(settings)

    def change_language(self, index: int) -> None:
        settings = self._settings()
        settings.language = LANGUAGES[index]
        self.ui.apply_settings(settings)

    def capture(self, action: str) -> None:
        self.capturing = action
        self.rebuild()
        self.group.focus_id(f"bind-{action}")

    def key_down(self, event: pygame.event.Event) -> bool:
        if self.capturing is None:
            return False
        action = self.capturing
        self.capturing = None
        if event.key != pygame.K_ESCAPE:
            name = pygame.key.name(event.key)
            if name:
                self.assign(action, name)
        self.rebuild()
        self.group.focus_id(f"bind-{action}")
        return True

    def assign(self, action: str, name: str) -> None:
        """Torna ``name`` a tecla principal de ``action``, sem duplicá-la em outra ação."""
        settings = self._settings()
        bindings = settings.bindings
        for other, keys in bindings.items():
            if other != action and name in keys:
                keys.remove(name)
                if not keys:
                    keys.extend(k for k in DEFAULT_BINDINGS.get(other, []) if k != name)
                if not keys:
                    keys.append(name)
        bindings[action] = [name, *[k for k in bindings.get(action, []) if k != name]]
        self.ui.apply_settings(settings)

    def restore_bindings(self) -> None:
        settings = self._settings()
        settings.bindings = {k: list(v) for k, v in DEFAULT_BINDINGS.items()}
        self.ui.apply_settings(settings)
        self.rebuild()

    def ask_reset(self) -> None:
        self.confirming = True
        self.rebuild()
        self.group.focus_id("reset-no")

    def cancel_reset(self) -> None:
        self.confirming = False
        self.rebuild()
        self.group.focus_id("reset")

    def confirm_reset(self) -> None:
        self.confirming = False
        self.ui.handlers.reset()
        self.ui.show("settings")
        self.ui.toast(self.ui.t("events.progress_reset"))

    def back(self) -> None:
        if self.capturing is not None:
            action = self.capturing
            self.capturing = None
            self.rebuild()
            self.group.focus_id(f"bind-{action}")
            return
        if self.confirming:
            self.cancel_reset()
            return
        if self.ui.settings_return == "pause":
            self.ui.show("pause", self.ui.game)
        else:
            self.ui.show("menu")


def _index[T](options: tuple[T, ...], value: T, fallback: int) -> int:
    return options.index(value) if value in options else fallback
