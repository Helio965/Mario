"""Interface do jogo (substitui ``src/ui/interface.ts`` + ``style.css``).

CONTRATO (implementação completa pelo agente de interface):

* ``Interface(save, handlers, locale)`` gerencia as telas ``menu``, ``map``,
  ``controls``, ``settings``, ``credits``, ``pause``, ``complete``,
  ``gameover`` e o HUD em jogo (vidas, pontos, moedas, mundo/fase, tempo,
  poder ativo, barra do guardião) e avisos (``toast``).
* Navegação por mouse, teclado (setas/Enter/Esc) e gamepad (eixos/botões).
* ``handle_event(event)`` consome eventos pygame enquanto uma tela está
  visível; ``draw(surface, game)`` desenha o HUD ou a tela atual sobre a
  cena 960 × 540; ``update(game, dt)`` atualiza animações e toasts.
* Textos SEMPRE via ``locale.t(...)``; nada fixo em português no código.
* Configurações: volumes (música, efeitos, vozes, ambiente), efeitos
  visuais, tela cheia, escala, limite de FPS, exibir FPS, idioma, qualidade,
  redução de movimento, alto contraste, legendas, remapeamento de teclas e
  reinício de progresso com confirmação.

IMPLEMENTAÇÃO:

* As telas vivem em ``menu.py``, ``world_map.py``, ``settings.py`` e
  ``screens.py`` (pausa, conclusão, fim de jogo, controles, créditos); o HUD,
  toast, legendas e FPS em ``hud.py``; widgets/foco em ``widgets.py``; paleta,
  fontes e ícones em ``theme.py``.
* Cada tela pré-renderiza seu conteúdo estático numa camada (``Layer``) ao
  entrar ou quando algo muda (salvamento, idioma, contraste, movimento, mundo);
  por quadro só os widgets e as animações são desenhados.
* O menu é mostrado no construtor, como no original. ``show("settings", game)``
  com o jogo pausado faz "Voltar" retornar à pausa.
* Teclas: setas/WASD navegam, Tab/Shift+Tab percorrem, Enter/Espaço ativam,
  Esc volta (na pausa, continua), M silencia/restaura o áudio. Gamepad: eixo
  esquerdo/direcional, A confirma, B volta, Start continua/joga, LB/RB
  percorrem. ``handle_event`` devolve ``True`` quando consumiu o evento.
* A tela cheia é alternada pela aplicação (``handlers.toggle_fullscreen``);
  as demais configurações chamam ``handlers.update_settings`` a cada mudança.
* ``subtitle(text, seconds)`` mostra uma legenda quando as legendas estão
  ativas; a aplicação pode usá-la com as vozes sintetizadas.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from itertools import pairwise
from typing import Literal

import pygame

from game.core.game import Game
from game.core.types import Enemy, Level, Theme
from game.levels.loader import THEMES, load_levels
from game.settings import VIEW_HEIGHT, VIEW_WIDTH
from game.systems.localization import Localization
from game.systems.save import DEFAULT_BINDINGS, SaveData, Settings
from game.ui.hud import Hud
from game.ui.menu import MenuScreen
from game.ui.screens import (
    CompleteScreen,
    ControlsScreen,
    CreditsScreen,
    GameOverScreen,
    NavAction,
    PauseScreen,
)
from game.ui.screens import Screen as ScreenView
from game.ui.settings import SettingsScreen
from game.ui.theme import RGB, Style
from game.ui.world_map import MapScreen

Screen = (
    str  # "menu" | "map" | "controls" | "settings" | "credits" | "pause" | "complete" | "gameover"
)

SCREENS: tuple[str, ...] = (
    "menu",
    "map",
    "controls",
    "settings",
    "credits",
    "pause",
    "complete",
    "gameover",
)
TOAST_SECONDS = 4.2
AXIS_THRESHOLD = 0.5
JOY_CONFIRM: tuple[int, ...] = (0,)
JOY_BACK: tuple[int, ...] = (1,)
JOY_START: tuple[int, ...] = (7, 9, 6)
JOY_PREV: tuple[int, ...] = (4,)
JOY_NEXT: tuple[int, ...] = (5,)
KEY_ACTIONS: dict[int, NavAction] = {
    pygame.K_UP: "up",
    pygame.K_w: "up",
    pygame.K_DOWN: "down",
    pygame.K_s: "down",
    pygame.K_LEFT: "left",
    pygame.K_a: "left",
    pygame.K_RIGHT: "right",
    pygame.K_d: "right",
    pygame.K_RETURN: "confirm",
    pygame.K_KP_ENTER: "confirm",
    pygame.K_SPACE: "confirm",
    pygame.K_ESCAPE: "back",
    pygame.K_BACKSPACE: "back",
}
MENU_FADE_STOPS: tuple[tuple[float, float], ...] = (
    (0.0, 1.0),
    (0.27, 0.96),
    (0.42, 0.855),
    (0.53, 0.44),
    (0.67, 0.0),
)


@dataclass(slots=True)
class Handlers:
    play: Callable[[int], None]
    resume: Callable[[], None]
    restart: Callable[[], None]
    menu: Callable[[], None]
    update_settings: Callable[[Settings], None]
    reset: Callable[[], None]
    quit: Callable[[], None]
    toggle_fullscreen: Callable[[], None]


class Interface:
    def __init__(
        self,
        save: SaveData,
        handlers: Handlers,
        locale: Localization,
        levels: Sequence[Level] | None = None,
    ) -> None:
        if not pygame.font.get_init():
            pygame.font.init()
        self.save = save
        self.handlers = handlers
        self.locale = locale
        self.levels: list[Level] = list(levels) if levels is not None else load_levels()
        self.themes: list[Theme] = THEMES
        self.style = Style()
        self.hud = Hud(self)
        self.game: Game | None = None
        self.settings_return: Literal["menu", "pause"] = "menu"
        self._screens: dict[str, ScreenView] = {
            "menu": MenuScreen(self),
            "map": MapScreen(self),
            "controls": ControlsScreen(self),
            "settings": SettingsScreen(self),
            "credits": CreditsScreen(self),
            "pause": PauseScreen(self),
            "complete": CompleteScreen(self),
            "gameover": GameOverScreen(self),
        }
        self._current: ScreenView | None = None
        self._toast: str | None = None
        self._toast_timer = 0.0
        self._toast_age = 0.0
        self._subtitle: str | None = None
        self._subtitle_timer = 0.0
        self._signature: tuple[str, bool, bool, int] | None = None
        self._backdrop: pygame.Surface | None = None
        self._backdrop_alpha = -1
        self._menu_fade: tuple[RGB, pygame.Surface] | None = None
        self._axis = [0, 0]
        self._muted = (0.45, 0.75)
        self._refresh_style(rebuild=False)
        self.show("menu")

    # ------------------------------------------------------------- contrato
    @property
    def screen(self) -> Screen | None:
        return self._current.name if self._current is not None else None

    def set_save(self, save: SaveData) -> None:
        self.save = save
        self._refresh_style(rebuild=False)
        if self._current is not None:
            self._current.rebuild()

    def show(self, screen: Screen, game: Game | None = None) -> None:
        if screen not in self._screens:
            raise ValueError(f"tela desconhecida: {screen!r}")
        self.game = game
        if screen == "settings":
            self.settings_return = (
                "pause" if game is not None and game.status == "paused" else "menu"
            )
        self._current = self._screens[screen]
        self._refresh_style(rebuild=False)
        self._current.enter()

    def hide(self) -> None:
        self._current = None

    def handle_event(self, event: pygame.event.Event) -> bool:
        current = self._current
        if current is None:
            return False
        kind = event.type
        if kind == pygame.KEYDOWN:
            if current.key_down(event):
                return True
            if event.key == pygame.K_TAB:
                current.nav("prev" if event.mod & pygame.KMOD_SHIFT else "next")
                return True
            if event.key == pygame.K_m:
                self.toggle_sound()
                return True
            action = KEY_ACTIONS.get(event.key)
            if action is not None:
                current.nav(action)
            return True
        if kind == pygame.KEYUP:
            return True
        if kind == pygame.MOUSEMOTION:
            buttons = getattr(event, "buttons", (0, 0, 0))
            current.mouse_move(event.pos, bool(buttons[0]))
            return True
        if kind == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                current.mouse_down(event.pos)
            elif event.button == 4:
                current.wheel(1)
            elif event.button == 5:
                current.wheel(-1)
            return True
        if kind == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                current.mouse_up(event.pos)
            return True
        if kind == pygame.MOUSEWHEEL:
            current.wheel(int(event.y))
            return True
        if kind == pygame.JOYAXISMOTION:
            self._axis_motion(current, int(event.axis), float(event.value))
            return True
        if kind == pygame.JOYHATMOTION:
            hx, hy = event.value
            if hx:
                current.nav("left" if hx < 0 else "right")
            if hy:
                current.nav("up" if hy > 0 else "down")
            return True
        if kind == pygame.JOYBUTTONDOWN:
            button = int(event.button)
            if button in JOY_CONFIRM:
                current.nav("confirm")
            elif button in JOY_BACK:
                current.nav("back")
            elif button in JOY_START:
                current.nav("start")
            elif button in JOY_PREV:
                current.nav("prev")
            elif button in JOY_NEXT:
                current.nav("next")
            return True
        return kind == pygame.JOYBUTTONUP

    def update(self, game: Game | None, dt: float) -> None:
        if game is not None:
            self.game = game
        dt = max(0.0, dt)
        self.style.time += dt
        if self._toast is not None:
            self._toast_timer -= dt
            self._toast_age += dt
            if self._toast_timer <= 0:
                self._toast = None
        if self._subtitle is not None:
            self._subtitle_timer -= dt
            if self._subtitle_timer <= 0:
                self._subtitle = None
        self._refresh_style()
        if self._current is not None:
            self._current.update(dt)
        self.hud.update(game, dt)

    def draw(self, surface: pygame.Surface, game: Game | None, fps: float | None = None) -> None:
        if self._current is None:
            if game is not None:
                self.hud.draw(surface, game)
        else:
            self._current.draw(surface)
        self.hud.draw_overlays(surface, fps)

    def toast(self, message: str) -> None:
        self._toast = message
        self._toast_timer = TOAST_SECONDS
        self._toast_age = 0.0

    # ------------------------------------------------------------ extensões
    def subtitle(self, text: str, seconds: float = 2.0) -> None:
        """Legenda temporária (só quando ``settings.subtitles`` está ativo)."""
        if not self.save.settings.subtitles:
            return
        self._subtitle = text
        self._subtitle_timer = max(0.1, seconds)

    @property
    def toast_text(self) -> str | None:
        return self._toast

    @property
    def toast_age(self) -> float:
        return self._toast_age

    @property
    def toast_remaining(self) -> float:
        return max(0.0, self._toast_timer) if self._toast is not None else 0.0

    @property
    def subtitle_text(self) -> str | None:
        return self._subtitle

    @property
    def current_screen(self) -> ScreenView | None:
        return self._current

    def apply_settings(self, settings: Settings) -> None:
        """Grava, avisa a aplicação e recarrega o idioma/paleta se preciso."""
        self.save.settings = settings
        self.handlers.update_settings(settings)
        if settings.language != self.locale.language:
            self.locale.load(settings.language)
        self._refresh_style()

    def toggle_sound(self) -> None:
        """Silencia (ou restaura) música e efeitos, como o botão de som do original."""
        settings = self.save.settings
        muted = settings.music == 0 and settings.sfx == 0
        if not muted:
            self._muted = (settings.music, settings.sfx)
        updated = settings.copy()
        updated.music, updated.sfx = self._muted if muted else (0.0, 0.0)
        self.apply_settings(updated)
        current = self._current
        if current is not None and current.name == "settings":
            current.rebuild()
        self.toast(self.t("events.audio_on" if muted else "events.audio_off"))

    # ------------------------------------------------------------ consultas
    def t(self, key: str, **params: object) -> str:
        return self.locale.t(key, **params)

    def level_name(self, level: Level) -> str:
        key = f"levels.{level.id}"
        return self.locale.t(key) if self.locale.has(key) else level.name

    def theme_for_world(self, world: int) -> Theme:
        return self.themes[max(0, min(world - 1, len(self.themes) - 1))]

    def theme_name(self, world: int) -> str:
        key = f"themes.{world}.name"
        return self.locale.t(key) if self.locale.has(key) else self.theme_for_world(world).name

    def theme_subtitle(self, world: int) -> str:
        key = f"themes.{world}.subtitle"
        return self.locale.t(key) if self.locale.has(key) else self.theme_for_world(world).subtitle

    def achievement_name(self, achievement: str) -> str:
        key = f"achievements.{achievement}"
        return (
            self.locale.t(key)
            if self.locale.has(key)
            else achievement.replace("-", " ").replace("_", " ")
        )

    def key_label(self, name: str) -> str:
        key = f"keys.{name}"
        return self.locale.t(key) if self.locale.has(key) else name.upper()

    def binding_labels(self, action: str) -> list[str]:
        keys = self.save.settings.bindings.get(action) or DEFAULT_BINDINGS.get(action, [])
        return [self.key_label(name) for name in keys]

    def primary_key(self, action: str) -> str:
        keys = self.save.settings.bindings.get(action) or DEFAULT_BINDINGS.get(action, [])
        return keys[0] if keys else action

    def format_score(self, value: float) -> str:
        separator = self.t("format.thousands")
        return f"{max(0, round(value)):,}".replace(",", separator)

    def nearby_boss(self, game: Game) -> Enemy | None:
        return self.hud.nearby_boss(game)

    def current_world(self) -> int:
        if self.game is not None:
            return self.game.level.world
        if not self.levels:
            return 1
        return self.levels[max(0, min(self.save.unlocked, len(self.levels) - 1))].world

    # -------------------------------------------------------------- visual
    def _refresh_style(self, rebuild: bool = True) -> None:
        settings = self.save.settings
        world = self.current_world()
        signature = (self.locale.language, settings.high_contrast, settings.reduced_motion, world)
        if signature == self._signature:
            return
        self._signature = signature
        self.style.apply(
            self.theme_for_world(world), settings.high_contrast, not settings.reduced_motion
        )
        self._backdrop = None
        self._menu_fade = None
        if rebuild and self._current is not None:
            self._current.rebuild()

    def backdrop(self, alpha: int) -> pygame.Surface:
        """Véu escuro de tela inteira atrás dos painéis (uma superfície reutilizada)."""
        if self._backdrop is None:
            self._backdrop = pygame.Surface((VIEW_WIDTH, VIEW_HEIGHT))
            self._backdrop.fill(self.style.palette.backdrop)
            self._backdrop_alpha = -1
        if alpha != self._backdrop_alpha:
            self._backdrop.set_alpha(max(0, min(255, alpha)))
            self._backdrop_alpha = alpha
        return self._backdrop

    def menu_fade(self) -> pygame.Surface:
        """Gradiente horizontal creme → transparente do menu (pré-renderizado)."""
        color = self.style.palette.menu_fade
        if self._menu_fade is None or self._menu_fade[0] != color:
            surface = pygame.Surface((VIEW_WIDTH, VIEW_HEIGHT), pygame.SRCALPHA)
            for x in range(VIEW_WIDTH):
                alpha = _interpolate(MENU_FADE_STOPS, x / VIEW_WIDTH)
                pygame.draw.line(surface, (*color, round(alpha * 255)), (x, 0), (x, VIEW_HEIGHT))
            self._menu_fade = (color, surface)
        return self._menu_fade[1]

    # ------------------------------------------------------------- gamepad
    def _axis_motion(self, current: ScreenView, axis: int, value: float) -> None:
        if axis not in (0, 1):
            return
        direction = -1 if value < -AXIS_THRESHOLD else 1 if value > AXIS_THRESHOLD else 0
        previous = self._axis[axis]
        self._axis[axis] = direction
        if direction == 0 or direction == previous:
            return
        if axis == 0:
            current.nav("left" if direction < 0 else "right")
        else:
            current.nav("up" if direction < 0 else "down")


def _interpolate(stops: tuple[tuple[float, float], ...], u: float) -> float:
    if u <= stops[0][0]:
        return stops[0][1]
    for (u0, a0), (u1, a1) in pairwise(stops):
        if u <= u1:
            return a0 + (a1 - a0) * (u - u0) / (u1 - u0)
    return stops[-1][1]
