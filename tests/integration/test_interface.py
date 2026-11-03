"""Interface em pygame com o driver ``dummy``: telas, navegação, configurações,
HUD, avisos e localização. Nenhum teste abre janela.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pygame
import pytest

from game.core.game import Game
from game.enemies.registry import is_boss_kind
from game.levels.loader import load_levels
from game.paths import data_path
from game.rendering.painter import parse_color
from game.settings import VIEW_HEIGHT, VIEW_WIDTH
from game.systems.localization import Localization
from game.systems.progression import ACHIEVEMENT_IDS
from game.systems.save import DEFAULT_BINDINGS, SaveData, Settings
from game.ui.interface import SCREENS, TOAST_SECONDS, Handlers, Interface
from game.ui.settings import SettingsScreen
from game.ui.widgets import Button, Toggle

pytestmark = pytest.mark.graphics

pygame.init()

LEVELS = load_levels()
LEVEL_IDS = [level.id for level in LEVELS]
MOUSE_MOVE_KW = {"rel": (0, 0), "buttons": (0, 0, 0)}


@dataclass
class Recorder:
    """Handlers que só registram as chamadas."""

    calls: list[tuple[str, Any]] = field(default_factory=list)
    settings: list[Settings] = field(default_factory=list)

    def handlers(self) -> Handlers:
        return Handlers(
            play=lambda index: self.calls.append(("play", index)),
            resume=lambda: self.calls.append(("resume", None)),
            restart=lambda: self.calls.append(("restart", None)),
            menu=lambda: self.calls.append(("menu", None)),
            update_settings=self._update_settings,
            reset=lambda: self.calls.append(("reset", None)),
            quit=lambda: self.calls.append(("quit", None)),
            toggle_fullscreen=lambda: self.calls.append(("toggle_fullscreen", None)),
        )

    def _update_settings(self, settings: Settings) -> None:
        self.calls.append(("update_settings", settings))
        self.settings.append(settings)

    def names(self) -> list[str]:
        return [name for name, _ in self.calls]


def new_surface() -> pygame.Surface:
    surface = pygame.Surface((VIEW_WIDTH, VIEW_HEIGHT))
    surface.fill((96, 150, 180))
    return surface


def pixels(surface: pygame.Surface) -> np.ndarray:
    return np.transpose(pygame.surfarray.array3d(surface), (1, 0, 2)).copy()


def packed_colors(surface: pygame.Surface) -> set[int]:
    array = pixels(surface).astype(np.uint32)
    packed = (array[:, :, 0] << 16) | (array[:, :, 1] << 8) | array[:, :, 2]
    return set(np.unique(packed).tolist())


def packed(color: str) -> int:
    r, g, b = parse_color(color)
    return (r << 16) | (g << 8) | b


def assert_drawn(surface: pygame.Surface, minimum_colors: int = 24) -> None:
    array = pixels(surface)
    assert int(np.ptp(array)) > 0, "superfície uniforme"
    assert float(array.mean()) < 248, "superfície praticamente branca"
    assert len(packed_colors(surface)) >= minimum_colors


def mean_difference(a: pygame.Surface, b: pygame.Surface) -> float:
    return float(np.mean(np.abs(pixels(a).astype(np.int16) - pixels(b).astype(np.int16))))


def key(code: int, mod: int = 0) -> pygame.event.Event:
    return pygame.event.Event(pygame.KEYDOWN, key=code, mod=mod, unicode="", scancode=0)


def press(ui: Interface, *codes: int) -> None:
    for code in codes:
        assert ui.handle_event(key(code))
        assert ui.handle_event(pygame.event.Event(pygame.KEYUP, key=code, mod=0))


def click(ui: Interface, pos: tuple[int, int]) -> None:
    ui.handle_event(pygame.event.Event(pygame.MOUSEMOTION, pos=pos, **MOUSE_MOVE_KW))
    ui.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=pos, button=1))
    ui.handle_event(pygame.event.Event(pygame.MOUSEBUTTONUP, pos=pos, button=1))


def widget_center(ui: Interface, widget_id: str) -> tuple[int, int]:
    screen = ui.current_screen
    assert screen is not None
    widget = screen.group.find(widget_id)
    assert widget is not None, widget_id
    ox, oy = screen.group.origin
    return (widget.rect.centerx + ox, widget.rect.centery + oy)


def focus(ui: Interface, widget_id: str) -> None:
    screen = ui.current_screen
    assert screen is not None
    assert screen.group.focus_id(widget_id), widget_id


def make_ui(
    save: SaveData | None = None, language: str = "pt-BR"
) -> tuple[Interface, Recorder, Localization]:
    recorder = Recorder()
    locale = Localization(language)
    save = save or SaveData()
    save.settings.language = language
    ui = Interface(save, recorder.handlers(), locale, LEVELS)
    return ui, recorder, locale


def place(game: Game, x: float) -> None:
    """Coloca o jogador sobre o chão em ``x`` e enquadra a câmera."""
    player = game.player
    center = x + player.w / 2
    grounds = [p for p in game.platforms if p.kind == "ground" and p.x <= center < p.x + p.w]
    if grounds:
        floor = min(grounds, key=lambda p: p.y)
        player.y = floor.y - player.h
        player.grounded = True
    player.x = x
    game.camera.x = max(0.0, min(game.level.width - VIEW_WIDTH, x - 310))


def game_at(level_id: str, x: float | None = None) -> Game:
    game = Game(LEVELS)
    game.load(LEVEL_IDS.index(level_id))
    if x is not None:
        place(game, x)
    return game


def boss_game(near: bool = True) -> Game:
    game = game_at("1-3")
    boss = next(enemy for enemy in game.enemies if is_boss_kind(enemy.kind))
    place(game, boss.x - 200 if near else 60)
    return game


def screen_states(ui: Interface) -> list[tuple[str, Game | None]]:
    """Todas as telas com um jogo coerente para as de estado."""
    paused = game_at("2-1")
    paused.pause()
    complete = game_at("1-1")
    complete.status = "complete"
    complete.found_relic = True
    complete.score = 12345
    final = game_at("5-3")
    final.status = "complete"
    over = game_at("3-2")
    over.lives = 0
    over.status = "gameover"
    return [
        ("menu", None),
        ("map", None),
        ("controls", None),
        ("settings", None),
        ("credits", None),
        ("pause", paused),
        ("complete", complete),
        ("complete", final),
        ("gameover", over),
    ]


def rich_save() -> SaveData:
    save = SaveData(unlocked=7, completed=["1-1", "1-2", "1-3", "2-1", "2-2", "2-3", "3-1"])
    save.records = {"1-1": 4200, "1-2": 9800, "2-1": 15300}
    save.relics = ["1-1", "2-2"]
    save.achievements = ["first-clear", "world-1", "secret-path"]
    return save


def draw_all(ui: Interface, frames: int = 3) -> list[pygame.Surface]:
    surfaces = []
    for screen, game in screen_states(ui):
        ui.show(screen, game)
        assert ui.screen == screen
        surface = new_surface()
        for _ in range(frames):
            ui.update(game, 1 / 60)
            ui.draw(surface, game)
        assert_drawn(surface)
        surfaces.append(surface)
    return surfaces


# telas -------------------------------------------------------------------------------


def test_contract_screens_and_initial_menu() -> None:
    ui, _, _ = make_ui()
    assert set(SCREENS) == {
        "menu",
        "map",
        "controls",
        "settings",
        "credits",
        "pause",
        "complete",
        "gameover",
    }
    assert ui.screen == "menu"
    ui.hide()
    assert ui.screen is None
    with pytest.raises(ValueError):
        ui.show("inventory")


def test_every_screen_draws_without_exception_and_without_missing_texts() -> None:
    ui, _, locale = make_ui(rich_save())
    surfaces = draw_all(ui)
    assert locale.missing == []
    # Telas diferentes produzem imagens diferentes.
    for i, a in enumerate(surfaces):
        for b in surfaces[i + 1 :]:
            assert mean_difference(a, b) > 0.5


def test_every_screen_draws_with_fresh_save_high_contrast_and_reduced_motion() -> None:
    for high_contrast, reduced_motion in ((True, False), (False, True), (True, True)):
        save = SaveData()
        save.settings.high_contrast = high_contrast
        save.settings.reduced_motion = reduced_motion
        ui, _, locale = make_ui(save)
        assert ui.style.high_contrast is high_contrast
        assert ui.style.motion is not reduced_motion
        draw_all(ui)
        assert locale.missing == []


def test_high_contrast_changes_the_rendering_and_reduced_motion_skips_animation() -> None:
    ui, _, _ = make_ui(rich_save())
    ui.show("map")
    normal = new_surface()
    ui.update(None, 0.5)
    ui.draw(normal, None)
    settings = ui.save.settings.copy()
    settings.high_contrast = True
    ui.apply_settings(settings)
    contrast = new_surface()
    ui.update(None, 0.5)
    ui.draw(contrast, None)
    assert mean_difference(normal, contrast) > 2
    settings = settings.copy()
    settings.reduced_motion = True
    ui.apply_settings(settings)
    ui.show("credits")
    screen = ui.current_screen
    assert screen is not None
    assert screen.appear() == 1.0
    settings = settings.copy()
    settings.reduced_motion = False
    ui.apply_settings(settings)
    ui.show("credits")
    assert screen.appear() == 0.0
    ui.update(None, 0.3)
    assert screen.appear() == 1.0


def test_menu_shows_next_destination_and_continue_label() -> None:
    ui, _, _ = make_ui()
    screen = ui.current_screen
    assert screen is not None
    play = screen.group.find("play")
    assert isinstance(play, Button)
    assert play.sublabel == ui.t("menu.start_here")
    save = rich_save()
    ui.set_save(save)
    play = ui.current_screen.group.find("play") if ui.current_screen else None
    assert isinstance(play, Button)
    assert play.sublabel == ui.t("menu.continue", world=3, stage=2)
    assert ui.current_world() == 3


# navegação ---------------------------------------------------------------------------


def test_keyboard_navigation_to_play_calls_play_with_unlocked_index() -> None:
    save = rich_save()
    ui, recorder, _ = make_ui(save)
    press(ui, pygame.K_DOWN, pygame.K_DOWN, pygame.K_UP, pygame.K_UP)
    screen = ui.current_screen
    assert screen is not None
    assert screen.group.focused_id == "play"
    press(ui, pygame.K_RETURN)
    assert recorder.calls == [("play", save.unlocked)]
    # Tab percorre e Enter abre o mapa (handlers.menu + tela).
    press(ui, pygame.K_TAB, pygame.K_RETURN)
    assert ui.screen == "map"
    assert recorder.names() == ["play", "menu"]
    press(ui, pygame.K_ESCAPE)
    assert ui.screen == "menu"
    press(ui, pygame.K_TAB, pygame.K_TAB, pygame.K_SPACE)
    assert ui.screen == "controls"
    press(ui, pygame.K_ESCAPE)
    press(ui, pygame.K_TAB, pygame.K_TAB, pygame.K_TAB, pygame.K_TAB, pygame.K_TAB, pygame.K_RETURN)
    assert recorder.names()[-1] == "quit"


def test_mouse_hover_and_click_activate_buttons() -> None:
    ui, recorder, _ = make_ui()
    pos = widget_center(ui, "credits")
    ui.handle_event(pygame.event.Event(pygame.MOUSEMOTION, pos=pos, **MOUSE_MOVE_KW))
    screen = ui.current_screen
    assert screen is not None
    assert screen.group.focused_id == "credits"
    click(ui, pos)
    assert ui.screen == "credits"
    click(ui, widget_center(ui, "back"))
    assert ui.screen == "menu"
    click(ui, widget_center(ui, "play"))
    assert recorder.calls == [("play", 0)]
    # Clique fora de qualquer widget não faz nada e também é consumido.
    assert ui.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(900, 100), button=1))
    assert recorder.calls == [("play", 0)]


def test_gamepad_axes_hat_and_buttons_navigate() -> None:
    ui, recorder, _ = make_ui()
    screen = ui.current_screen
    assert screen is not None
    assert ui.handle_event(pygame.event.Event(pygame.JOYAXISMOTION, joy=0, axis=1, value=1.0))
    assert screen.group.focused_id == "map"
    # Manter o eixo inclinado não repete o movimento; voltar ao centro rearma.
    ui.handle_event(pygame.event.Event(pygame.JOYAXISMOTION, joy=0, axis=1, value=0.9))
    assert screen.group.focused_id == "map"
    ui.handle_event(pygame.event.Event(pygame.JOYAXISMOTION, joy=0, axis=1, value=0.0))
    ui.handle_event(pygame.event.Event(pygame.JOYAXISMOTION, joy=0, axis=1, value=-1.0))
    assert screen.group.focused_id == "play"
    ui.handle_event(pygame.event.Event(pygame.JOYHATMOTION, joy=0, hat=0, value=(0, -1)))
    ui.handle_event(pygame.event.Event(pygame.JOYHATMOTION, joy=0, hat=0, value=(1, 0)))
    assert screen.group.focused_id == "controls"
    ui.handle_event(pygame.event.Event(pygame.JOYBUTTONDOWN, joy=0, button=0))
    assert ui.screen == "controls"
    ui.handle_event(pygame.event.Event(pygame.JOYBUTTONDOWN, joy=0, button=1))
    assert ui.screen == "menu"
    ui.handle_event(pygame.event.Event(pygame.JOYBUTTONDOWN, joy=0, button=7))
    assert recorder.calls == [("play", 0)]


def test_handle_event_consumes_only_while_a_screen_is_visible() -> None:
    ui, _, _ = make_ui()
    ui.hide()
    assert not ui.handle_event(key(pygame.K_RETURN))
    assert not ui.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(10, 10), button=1))
    ui.show("menu")
    assert ui.handle_event(key(pygame.K_F5))
    assert not ui.handle_event(pygame.event.Event(pygame.QUIT))


def test_mouse_wheel_scrolls_the_settings_panel() -> None:
    ui, _, _ = make_ui()
    ui.show("settings")
    screen = ui.current_screen
    assert screen is not None
    assert screen.group.max_scroll() > 0
    ui.handle_event(pygame.event.Event(pygame.MOUSEWHEEL, x=0, y=-3, flipped=False))
    assert screen.group.scroll > 0
    ui.handle_event(pygame.event.Event(pygame.MOUSEWHEEL, x=0, y=30, flipped=False))
    assert screen.group.scroll == 0
    # Foco por teclado rola o painel para manter o widget visível.
    focus(ui, "reset")
    assert screen.group.scroll > 0


# mapa ----------------------------------------------------------------------------------


def test_map_blocks_locked_levels_and_opens_unlocked_ones() -> None:
    save = SaveData(unlocked=1, completed=["1-1"], records={"1-1": 3200})
    ui, recorder, _ = make_ui(save)
    ui.show("map")
    screen = ui.current_screen
    assert screen is not None
    locked = screen.group.find("level-2")
    assert locked is not None and not locked.enabled and not locked.focusable
    assert not screen.group.focus_id("level-2")
    click(ui, widget_center(ui, "level-2"))
    assert recorder.calls == []
    focus(ui, "level-1")
    press(ui, pygame.K_RETURN)
    assert recorder.calls == [("play", 1)]
    click(ui, widget_center(ui, "level-0"))
    assert recorder.calls == [("play", 1), ("play", 0)]
    # Navegação espacial: para a direita entra no próximo mundo, bloqueado → nada.
    focus(ui, "level-0")
    press(ui, pygame.K_DOWN)
    assert screen.group.focused_id == "level-1"


def test_map_reflects_progress_relics_and_achievements() -> None:
    ui, _, locale = make_ui(rich_save())
    ui.show("map")
    surface = new_surface()
    ui.update(None, 1 / 60)
    ui.draw(surface, None)
    assert_drawn(surface)
    assert locale.missing == []
    for achievement in ACHIEVEMENT_IDS:
        assert ui.achievement_name(achievement) != achievement
    assert ui.achievement_name("unknown-badge") == "unknown badge"


# configurações ---------------------------------------------------------------------------


def changed_fields(before: Settings, after: Settings) -> set[str]:
    return {name for name, value in after.to_dict().items() if value != before.to_dict()[name]}


def test_settings_slider_toggle_and_selector_call_update_settings_with_changed_field() -> None:
    ui, recorder, _ = make_ui()
    before = ui.save.settings.copy()
    ui.show("settings")
    focus(ui, "slider-music")
    press(ui, pygame.K_RIGHT)
    assert recorder.names() == ["update_settings"]
    assert recorder.settings[-1].music == pytest.approx(0.5)
    assert changed_fields(before, recorder.settings[-1]) == {"music"}
    press(ui, pygame.K_LEFT, pygame.K_LEFT)
    assert recorder.settings[-1].music == pytest.approx(0.4)
    focus(ui, "toggle-effects")
    press(ui, pygame.K_RETURN)
    assert recorder.settings[-1].effects is False
    assert changed_fields(before, recorder.settings[-1]) == {"music", "effects"}
    focus(ui, "select-quality")
    press(ui, pygame.K_RIGHT)
    assert recorder.settings[-1].quality == "medium"
    focus(ui, "select-fps_limit")
    press(ui, pygame.K_LEFT)
    assert recorder.settings[-1].fps_limit == 30
    focus(ui, "select-scale")
    press(ui, pygame.K_RIGHT, pygame.K_RIGHT)
    assert recorder.settings[-1].scale == 2
    assert ui.save.settings is recorder.settings[-1]
    # Clique na trilha do controle deslizante.
    screen = ui.current_screen
    assert screen is not None
    slider = screen.group.find("slider-sfx")
    assert slider is not None
    ox, oy = screen.group.origin
    click(ui, (slider.rect.x + ox + slider.rect.w // 2, slider.rect.bottom + oy - 6))
    assert recorder.settings[-1].sfx == pytest.approx(0.5, abs=0.02)


def test_fullscreen_toggle_delegates_to_the_application() -> None:
    ui, recorder, _ = make_ui()
    ui.show("settings")
    focus(ui, "toggle-fullscreen")
    press(ui, pygame.K_RETURN)
    assert recorder.names() == ["toggle_fullscreen"]
    screen = ui.current_screen
    assert screen is not None
    toggle = screen.group.find("toggle-fullscreen")
    assert isinstance(toggle, Toggle)
    assert toggle.value is False  # a aplicação não mudou o salvamento


def test_remapping_a_key_changes_bindings_and_escape_cancels() -> None:
    ui, recorder, _ = make_ui()
    ui.show("settings")
    screen = ui.current_screen
    assert isinstance(screen, SettingsScreen)
    focus(ui, "bind-jump")
    press(ui, pygame.K_RETURN)
    assert screen.capturing == "jump"
    assert ui.handle_event(key(pygame.K_k))
    assert screen.capturing is None
    bindings = recorder.settings[-1].bindings
    assert bindings["jump"][0] == "k"
    assert bindings["jump"][1:] == DEFAULT_BINDINGS["jump"]
    assert ui.binding_labels("jump")[0] == "K"
    # A tecla de outra ação muda de dono.
    focus(ui, "bind-run")
    press(ui, pygame.K_RETURN)
    ui.handle_event(key(pygame.K_k))
    bindings = recorder.settings[-1].bindings
    assert bindings["run"][0] == "k"
    assert "k" not in bindings["jump"]
    # Esc cancela a captura sem alterar nada.
    count = len(recorder.settings)
    focus(ui, "bind-down")
    press(ui, pygame.K_RETURN)
    assert screen.capturing == "down"
    press(ui, pygame.K_ESCAPE)
    assert screen.capturing is None
    assert ui.screen == "settings"
    assert len(recorder.settings) == count
    assert screen.group.focused_id == "bind-down"
    focus(ui, "bindings-reset")
    press(ui, pygame.K_RETURN)
    assert recorder.settings[-1].bindings == DEFAULT_BINDINGS


def test_reset_requires_confirmation_and_cancel_preserves_progress() -> None:
    ui, recorder, _ = make_ui(rich_save())
    ui.show("settings")
    screen = ui.current_screen
    assert isinstance(screen, SettingsScreen)
    focus(ui, "reset")
    press(ui, pygame.K_RETURN)
    assert screen.confirming is True
    assert "reset" not in recorder.names()
    assert screen.group.focused_id == "reset-no"
    press(ui, pygame.K_RETURN)
    assert screen.confirming is False
    assert "reset" not in recorder.names()
    assert screen.group.find("reset-yes") is None
    press(ui, pygame.K_ESCAPE)
    assert ui.screen == "menu"
    ui.show("settings")
    focus(ui, "reset")
    press(ui, pygame.K_RETURN)
    focus(ui, "reset-yes")
    press(ui, pygame.K_RETURN)
    assert recorder.names().count("reset") == 1
    assert ui.screen == "settings"
    assert ui.toast_text == ui.t("events.progress_reset")


def test_language_change_reloads_locale_and_rebuilds_texts() -> None:
    ui, recorder, locale = make_ui()
    ui.show("settings")
    focus(ui, "select-language")
    press(ui, pygame.K_RIGHT)
    assert recorder.settings[-1].language == "en-US"
    assert locale.language == "en-US"
    assert ui.t("screens.settings.title") == "Your way."
    screen = ui.current_screen
    assert screen is not None
    assert screen.group.focused_id == "select-language"
    surface = new_surface()
    ui.update(None, 1 / 60)
    ui.draw(surface, None)
    assert_drawn(surface)
    assert locale.missing == []


def test_mute_shortcut_toggles_music_and_sfx() -> None:
    ui, recorder, _ = make_ui()
    press(ui, pygame.K_m)
    assert recorder.settings[-1].music == 0 and recorder.settings[-1].sfx == 0
    assert ui.toast_text == ui.t("events.audio_off")
    press(ui, pygame.K_m)
    assert recorder.settings[-1].music == pytest.approx(0.45)
    assert recorder.settings[-1].sfx == pytest.approx(0.75)


# telas de estado --------------------------------------------------------------------------


def test_pause_escape_resumes_and_settings_return_to_pause() -> None:
    ui, recorder, _ = make_ui()
    game = game_at("1-1")
    game.pause()
    ui.show("pause", game)
    press(ui, pygame.K_ESCAPE)
    assert recorder.calls == [("resume", None)]
    ui.show("pause", game)
    focus(ui, "settings")
    press(ui, pygame.K_RETURN)
    assert ui.screen == "settings" and ui.settings_return == "pause"
    press(ui, pygame.K_ESCAPE)
    assert ui.screen == "pause"
    ui.show("settings")
    assert ui.settings_return == "menu"
    press(ui, pygame.K_ESCAPE)
    assert ui.screen == "menu"
    ui.show("pause", game)
    focus(ui, "restart")
    press(ui, pygame.K_RETURN)
    focus(ui, "menu")
    press(ui, pygame.K_RETURN)
    assert recorder.names()[-2:] == ["restart", "menu"]
    assert ui.screen == "menu"


def test_complete_next_plays_following_level_or_opens_map_on_final() -> None:
    ui, recorder, _ = make_ui()
    game = game_at("1-2")
    game.status = "complete"
    ui.show("complete", game)
    press(ui, pygame.K_RETURN)
    assert recorder.calls == [("play", 2)]
    final = game_at("5-3")
    final.status = "complete"
    ui.show("complete", final)
    assert ui.t("screens.complete.title_final") in [
        ui.current_screen.title() if ui.current_screen else ""  # type: ignore[attr-defined]
    ]
    press(ui, pygame.K_RETURN)
    assert recorder.names()[-1] == "menu"
    assert ui.screen == "map"
    over = game_at("1-1")
    over.status = "gameover"
    ui.show("gameover", over)
    press(ui, pygame.K_RETURN)
    assert recorder.names()[-1] == "restart"


# HUD, toast e legendas -------------------------------------------------------------------


def test_hud_draws_stats_and_shows_guardian_bar_only_when_a_boss_is_near() -> None:
    ui, _, locale = make_ui()
    ui.hide()
    near = boss_game(near=True)
    surface = new_surface()
    ui.update(near, 1 / 60)
    ui.draw(surface, near)
    assert_drawn(surface)
    colors = packed_colors(surface)
    assert packed("#f0b584") in colors, "barra do guardião ausente"
    far = boss_game(near=False)
    surface = new_surface()
    ui.update(far, 1 / 60)
    ui.draw(surface, far)
    assert packed("#f0b584") not in packed_colors(surface)
    assert locale.missing == []
    # Tempo baixo fica em destaque; poder e estrela têm rótulos.
    far.time = 12
    far.player.star = 4.2
    low = new_surface()
    ui.draw(low, far)
    assert packed("#f1a483") in packed_colors(low)
    assert ui.hud.power_label(far) == ui.t("hud.power_star", seconds=5)
    far.player.star = 0
    far.player.power = "fire"
    assert ui.hud.power_label(far) == ui.t("hud.power_fire")
    with_fps = new_surface()
    ui.draw(with_fps, far, fps=59.6)
    without_fps = new_surface()
    ui.draw(without_fps, far)
    assert mean_difference(with_fps, without_fps) > 0


def test_toast_is_visible_for_4_2_seconds_and_drawn_over_screens() -> None:
    ui, _, _ = make_ui()
    ui.hide()
    ui.toast("Checkpoint!")
    assert ui.toast_text == "Checkpoint!"
    ui.update(None, 2.0)
    game = game_at("1-1")
    with_toast = new_surface()
    ui.draw(with_toast, game)
    assert packed("#254e49") in packed_colors(with_toast)
    ui.update(None, TOAST_SECONDS - 2.1)
    assert ui.toast_text == "Checkpoint!"
    fading = new_surface()
    ui.draw(fading, game)  # esmaecendo: ainda desenha, com alpha
    assert mean_difference(fading, new_surface()) > 0
    ui.update(None, 0.2)
    assert ui.toast_text is None
    without = new_surface()
    ui.draw(without, game)
    assert packed("#254e49") not in packed_colors(without)
    ui.show("menu")
    ui.toast("Olá")
    ui.update(None, 0.5)
    over_menu = new_surface()
    ui.draw(over_menu, None)
    assert packed("#254e49") in packed_colors(over_menu)


def test_subtitles_follow_the_setting() -> None:
    ui, _, _ = make_ui()
    ui.hide()
    ui.subtitle("Uma relíquia!", 1.0)
    assert ui.subtitle_text == "Uma relíquia!"
    ui.update(None, 0.5)
    assert ui.subtitle_text == "Uma relíquia!"
    ui.update(None, 0.6)
    assert ui.subtitle_text is None
    ui.save.settings.subtitles = False
    ui.subtitle("Silêncio", 1.0)
    assert ui.subtitle_text is None


# localização -------------------------------------------------------------------------------


def leaves(node: Any, prefix: str = "") -> set[str]:
    if isinstance(node, dict):
        result: set[str] = set()
        for key_name, value in node.items():
            result |= leaves(value, f"{prefix}{key_name}.")
        return result
    return {prefix.rstrip(".")}


def test_en_us_locale_has_exactly_the_keys_of_pt_br() -> None:
    with open(data_path("locales", "pt-BR.json"), encoding="utf-8") as handle:
        pt = json.load(handle)
    with open(data_path("locales", "en-US.json"), encoding="utf-8") as handle:
        en = json.load(handle)
    assert leaves(pt) == leaves(en)
    assert "en-US" in Localization.available_languages()
    english = Localization("en-US")
    assert english.t("menu.play") == "PLAY"
    assert english.t("hud.power_star", seconds=3) == "Invincible · 3s"
    assert english.missing == []


def test_every_screen_in_english_has_no_missing_texts_and_formats_numbers() -> None:
    ui, _, locale = make_ui(rich_save(), language="en-US")
    assert ui.t("menu.play") == "PLAY"
    assert ui.format_score(1234567) == "1,234,567"
    draw_all(ui)
    ui.hide()
    game = boss_game()
    surface = new_surface()
    ui.update(game, 1 / 60)
    ui.draw(surface, game, fps=60)
    assert locale.missing == []
    portuguese, _, _ = make_ui(rich_save())
    assert portuguese.format_score(1234567) == "1.234.567"
    assert portuguese.level_name(LEVELS[0]) == "Primeiros Passos"
    assert ui.level_name(LEVELS[0]) == "First Steps"
    assert ui.theme_name(1) == "Green Realm"


# desempenho --------------------------------------------------------------------------------


@pytest.mark.performance
def test_ui_draw_time_is_reasonable() -> None:
    ui, _, _ = make_ui(rich_save())
    results: dict[str, float] = {}
    frames = 60
    game = boss_game()
    ui.hide()
    surface = new_surface()
    for _ in range(5):
        ui.update(game, 1 / 60)
        ui.draw(surface, game, fps=60)
    started = time.perf_counter()
    for _ in range(frames):
        ui.update(game, 1 / 60)
        ui.draw(surface, game, fps=60)
    results["hud"] = (time.perf_counter() - started) / frames * 1000
    for screen, state in screen_states(ui)[:7]:
        ui.show(screen, state)
        for _ in range(5):
            ui.update(state, 1 / 60)
            ui.draw(surface, state)
        started = time.perf_counter()
        for _ in range(frames):
            ui.update(state, 1 / 60)
            ui.draw(surface, state)
        results[screen] = (time.perf_counter() - started) / frames * 1000
    print("interface média por quadro (ms):", {k: round(v, 2) for k, v in results.items()})
    for value in results.values():
        assert value < 16
