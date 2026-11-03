"""Aplicação pygame-ce: janela, laço de passo fixo, integração dos sistemas.

Substitui ``src/main.ts``. A simulação (``Game``) mantém seu próprio
acumulador de passo fixo (1/120 s); aqui só medimos o tempo real, lemos a
entrada, drenamos os eventos para áudio/interface/salvamento e desenhamos.
"""

from __future__ import annotations

import argparse
import contextlib
import os
import sys
import time
from collections import deque
from collections.abc import Sequence
from dataclasses import dataclass, field

import pygame

from game import __version__
from game.core.game import Game
from game.core.types import GameEvent
from game.levels.loader import load_levels
from game.paths import asset_path
from game.rendering.renderer import Renderer
from game.settings import MAX_FRAME_TIME, VIEW_HEIGHT, VIEW_WIDTH, WINDOW_TITLE
from game.systems.audio import AudioSystem
from game.systems.input import Input
from game.systems.localization import Localization
from game.systems.progression import achievements_for
from game.systems.save import (
    SaveData,
    Settings,
    Storage,
    complete_level,
    load_save,
    reset_save,
    write_save,
)
from game.ui.interface import Handlers, Interface

EVENT_TEXT_KEYS: dict[str, str] = {
    "checkpoint": "events.checkpoint",
    "secret": "events.secret",
    "relic": "events.relic",
    "boss": "events.boss",
}


@dataclass(slots=True)
class FrameStats:
    """Medições reais do laço (janela móvel de 120 quadros)."""

    frame_times: deque[float] = field(default_factory=lambda: deque(maxlen=120))
    physics_ms: float = 0.0
    render_ms: float = 0.0
    ui_ms: float = 0.0

    @property
    def fps(self) -> float:
        if not self.frame_times:
            return 0.0
        total = sum(self.frame_times)
        return len(self.frame_times) / total if total > 0 else 0.0

    @property
    def min_fps(self) -> float:
        worst = max(self.frame_times, default=0.0)
        return 1 / worst if worst > 0 else 0.0

    @property
    def frame_ms(self) -> float:
        return (sum(self.frame_times) / len(self.frame_times) * 1000) if self.frame_times else 0.0


@dataclass(slots=True)
class Options:
    level: str | None = None
    windowed: bool = False
    headless_frames: int = 0
    screenshot: str | None = None
    no_audio: bool = False
    storage: Storage | None = None


def parse_args(argv: Sequence[str]) -> Options:
    parser = argparse.ArgumentParser(prog="lume", description="Lume — As Cinco Fronteiras")
    parser.add_argument("--level", help="iniciar diretamente na fase (ex.: 1-2)")
    parser.add_argument("--windowed", action="store_true", help="ignorar tela cheia salva")
    parser.add_argument(
        "--headless-frames", type=int, default=0, help="executa N quadros sem janela e sai (testes)"
    )
    parser.add_argument(
        "--screenshot", help="salva uma captura PNG ao final (com --headless-frames)"
    )
    parser.add_argument("--no-audio", action="store_true", help="não inicializar o mixer")
    parser.add_argument("--version", action="version", version=f"lume {__version__}")
    args = parser.parse_args(list(argv))
    return Options(args.level, args.windowed, args.headless_frames, args.screenshot, args.no_audio)


class Application:
    def __init__(self, options: Options | None = None) -> None:
        self.options = options or Options()
        if self.options.headless_frames:
            os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
            os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
        pygame.init()
        self.save: SaveData = load_save(self.options.storage)
        self.settings: Settings = self.save.settings
        self.locale = Localization(self.settings.language)
        self.levels = load_levels()
        self.level_ids = [level.id for level in self.levels]
        self.window = self._open_window()
        self.canvas = pygame.Surface((VIEW_WIDTH, VIEW_HEIGHT))
        self.game = Game(self.levels)
        self.input = Input(self.settings.bindings)
        self.audio = AudioSystem(enabled=not self.options.no_audio)
        self.renderer = Renderer(self.canvas)
        self.ui = Interface(self.save, self._handlers(), self.locale)
        self.clock = pygame.time.Clock()
        self.stats = FrameStats()
        self.active = False
        self.pause_held = False
        self.last_status = self.game.status
        self.shown_hints: set[str] = set()
        self.persistence_warning = False
        self.running = True
        self.frame_count = 0
        self.apply_settings(self.settings, persist=False)
        self.audio.menu()
        if self.options.level and self.options.level in self.level_ids:
            self.play(self.level_ids.index(self.options.level), force=True)

    # ------------------------------------------------------------- janela
    def _open_window(self) -> pygame.Surface:
        flags = pygame.SCALED | pygame.RESIZABLE
        if (
            self.settings.fullscreen
            and not self.options.windowed
            and not self.options.headless_frames
        ):
            flags |= pygame.FULLSCREEN
        scale = self.settings.scale or 1
        size = (VIEW_WIDTH * scale, VIEW_HEIGHT * scale)
        pygame.display.set_caption(WINDOW_TITLE)
        icon = asset_path("ui", "icon.png")
        if icon.exists():
            with contextlib.suppress(pygame.error):
                pygame.display.set_icon(pygame.image.load(str(icon)))
        return pygame.display.set_mode(size, flags, vsync=0 if self.options.headless_frames else 1)

    def _handlers(self) -> Handlers:
        return Handlers(
            play=self.play,
            resume=self.resume,
            restart=self.restart,
            menu=self.menu,
            update_settings=self.apply_settings,
            reset=self.reset,
            quit=self.quit,
            toggle_fullscreen=self.toggle_fullscreen,
        )

    # ------------------------------------------------------------ persistência
    def persist(self) -> None:
        self.save.settings = self.settings
        if not write_save(self.save, self.options.storage) and not self.persistence_warning:
            self.persistence_warning = True
            self.ui.toast(self.locale.t("events.save_blocked"))
        self.ui.set_save(self.save)

    def apply_settings(self, settings: Settings, persist: bool = True) -> None:
        previous = self.settings
        self.settings = settings
        self.save.settings = settings
        self.renderer.effects = settings.effects and not settings.reduced_motion
        self.renderer.quality = settings.quality
        self.audio.set_volumes(settings.music, settings.sfx, settings.voice, settings.ambient)
        self.input.set_bindings(settings.bindings)
        if settings.language != self.locale.language:
            self.locale.load(settings.language)
        if (
            settings.fullscreen != previous.fullscreen or settings.scale != previous.scale
        ) and not self.options.headless_frames:
            self._reopen_window()
        if persist:
            self.persist()

    def _reopen_window(self) -> None:
        flags = pygame.SCALED | pygame.RESIZABLE
        if self.settings.fullscreen and not self.options.windowed:
            flags |= pygame.FULLSCREEN
        scale = self.settings.scale or 1
        try:
            self.window = pygame.display.set_mode(
                (VIEW_WIDTH * scale, VIEW_HEIGHT * scale), flags, vsync=1
            )
        except pygame.error:
            self.window = pygame.display.set_mode(
                (VIEW_WIDTH, VIEW_HEIGHT), pygame.SCALED | pygame.RESIZABLE
            )

    def toggle_fullscreen(self) -> None:
        self.apply_settings(
            self.settings.copy().__class__(
                **{**self.settings.to_dict(), "fullscreen": not self.settings.fullscreen}
            )
        )

    # ------------------------------------------------------------- navegação
    def play(self, index: int, force: bool = False) -> None:
        if index < 0 or (index > self.save.unlocked and not force):
            return
        if self.active and self.game.status == "complete" and index == self.game.level_index + 1:
            self.game.next()
        else:
            self.game.start(index)
        self.active = True
        self.input.clear()
        self.audio.pause(False)
        self.audio.set_world(self.game.level.world)
        self.audio.ambient(f"world-{self.game.level.world}")
        self.pause_held = False
        self.last_status = self.game.status
        self.shown_hints.clear()
        self.ui.hide()

    def resume(self) -> None:
        self.game.resume()
        self.input.clear()
        self.ui.hide()

    def restart(self) -> None:
        self.game.start(self.game.level_index)
        self.active = True
        self.input.clear()
        self.shown_hints.clear()
        self.last_status = self.game.status
        self.ui.hide()

    def menu(self) -> None:
        self.active = False
        self.input.clear()
        self.game.pause()
        self.audio.pause(False)
        self.audio.menu()
        self.audio.ambient(None)

    def reset(self) -> None:
        self.menu()
        self.save = reset_save(self.options.storage)
        self.apply_settings(self.save.settings)

    def quit(self) -> None:
        self.running = False

    # ------------------------------------------------------------------ laço
    def run(self) -> int:
        previous = time.perf_counter()
        while self.running:
            limit = self.settings.fps_limit
            self.clock.tick(limit) if limit else self.clock.tick()
            now = time.perf_counter()
            dt = min(now - previous, MAX_FRAME_TIME)
            previous = now
            self.frame(dt, now)
            if self.options.headless_frames and self.frame_count >= self.options.headless_frames:
                if self.options.screenshot:
                    pygame.image.save(self.canvas, self.options.screenshot)
                self.running = False
        self.shutdown()
        return 0

    def shutdown(self) -> None:
        self.persist()
        self.audio.dispose()
        pygame.quit()

    def frame(self, dt: float, now: float) -> None:
        self.frame_count += 1
        self.stats.frame_times.append(dt)
        for event in pygame.event.get():
            self.handle_event(event)
        state = self.input.read()
        if self.active:
            if state.pause_pressed or (state.pause and not self.pause_held):
                if self.game.status == "paused" and self.ui.screen == "pause":
                    self.resume()
                elif self.game.status == "playing":
                    self.game.pause()
                    self.ui.show("pause", self.game)
            self.pause_held = state.pause
            t0 = time.perf_counter()
            self.game.update(dt, state)
            self.stats.physics_ms = (time.perf_counter() - t0) * 1000
            self.drain_events()
            if self.game.status == "gameover" and self.last_status != "gameover":
                self.ui.show("gameover", self.game)
            if self.game.status == "playing":
                for hint in self.game.level.hints:
                    key = f"{hint.x}:{hint.text}"
                    if abs(self.game.player.x - hint.x) < 70 and key not in self.shown_hints:
                        self.shown_hints.add(key)
                        self.ui.toast(hint.text)
            self.last_status = self.game.status
            self.audio.pause(self.game.status == "paused")
            boss = self.game.boss()
            self.audio.set_world(
                self.game.level.world, boss is not None and abs(boss.x - self.game.player.x) < 800
            )
        self.audio.update(dt)
        t0 = time.perf_counter()
        if self.active:
            self.renderer.render(self.game, now)
        else:
            self.renderer.backdrop(self.levels[min(self.save.unlocked, len(self.levels) - 1)].world)
        self.stats.render_ms = (time.perf_counter() - t0) * 1000
        t0 = time.perf_counter()
        self.ui.update(self.game if self.active else None, dt)
        self.ui.draw(
            self.canvas,
            self.game if self.active else None,
            self.stats.fps if self.settings.show_fps else None,
        )
        self.stats.ui_ms = (time.perf_counter() - t0) * 1000
        self.window.blit(self.canvas, (0, 0))
        pygame.display.flip()

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.QUIT:
            self.running = False
            return
        if event.type == pygame.WINDOWFOCUSLOST:
            self.suspend()
            return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
            self.toggle_fullscreen()
            return
        if self.ui.screen is not None and self.ui.handle_event(event):
            return
        self.input.handle_event(event)

    def suspend(self) -> None:
        self.input.clear()
        if self.active and self.game.status == "playing":
            self.game.pause()
            self.ui.show("pause", self.game)

    def drain_events(self) -> None:
        events: list[GameEvent] = self.game.events[:]
        del self.game.events[:]
        for event in events:
            self.audio.effect(event.type)
            if event.type in EVENT_TEXT_KEYS:
                self.ui.toast(self.locale.t(EVENT_TEXT_KEYS[event.type]))
            elif event.type == "life":
                self.ui.toast(
                    self.locale.t(
                        "events.life_heart"
                        if event.text == "Uma vida extra!"
                        else "events.life_coins"
                    )
                )
            elif event.type == "power" and event.text:
                key = {
                    "Mais forte!": "events.power_grow",
                    "12 segundos de invencibilidade": "events.power_star",
                }.get(event.text)
                if key:
                    self.ui.toast(self.locale.t(key))
                else:
                    ability = self.settings.bindings.get("ability", ["j"])[0].upper()
                    self.ui.toast(self.locale.t("events.power_fire", button=ability))
            if event.type == "secret" and "secret-path" not in self.save.achievements:
                self.save.achievements = [*self.save.achievements, "secret-path"]
                self.persist()
            if event.type == "complete":
                self.save = complete_level(
                    self.save,
                    self.game.level_index,
                    int(event.value or 0),
                    self.game.found_relic,
                    self.game.level.id,
                    len(self.levels),
                )
                self.save.settings = self.settings
                merged = list(self.save.achievements)
                for achievement in achievements_for(
                    self.save.completed, self.save.relics, self.levels
                ):
                    if achievement not in merged:
                        merged.append(achievement)
                self.save.achievements = merged
                self.persist()
                self.ui.show("complete", self.game)


def main(argv: Sequence[str] | None = None) -> int:
    options = parse_args(sys.argv[1:] if argv is None else argv)
    app = Application(options)
    return app.run()
