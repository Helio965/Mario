"""Application: window, main loop and screens.

Screens: title → world map → play (pause / settings) → results or game over.
The simulation runs in fixed 1/120 s steps inside :class:`Game`; rendering
uses the HD scene at the window's native resolution.
"""

from __future__ import annotations

import math
import os
import time
from dataclasses import dataclass, field
from typing import Optional

import pygame

from .core.constants import FIXED_DT
from .core.game import Game
from .core.input import InputState
from .core.progression import achievements_for
from .levels.campaign import Campaign, load_campaign
from .render.display import Display, choose_resolution
from .render.scene import Scene
from .systems.audio import AudioSystem
from .systems.input import InputSystem
from .systems import save as savemod
from .ui.widgets import button, panel

SOUND_FOR = {"jump": "jump", "coin": "coin", "relic": "relic", "block": "block", "bump": "bump", "brick": "brick",
             "sprout": "sprout", "power": "power", "hurt": "hurt", "death": "death", "stomp": "stomp", "kick": "kick",
             "shot": "shot", "checkpoint": "checkpoint", "secret": "secret", "complete": "complete", "boss": "boss",
             "life": "life", "spring": "spring", "swim": "swim", "crash": "crash", "crumble": "crumble", "land": "land",
             "deflect": "deflect", "charge": "charge", "boss_intro": "boss_intro", "wings_lost": "wings_lost",
             "collapse": "collapse", "warp": "warp", "enemy_jump": "enemy_jump", "splash": "splash"}
QUALITY_NAMES = {"auto": "Automática", "high": "Alta", "medium": "Média", "low": "Baixa"}


@dataclass
class Toast:
    text: str
    life: float = 2.4


@dataclass
class AppOptions:
    resolution: Optional[str] = None
    fullscreen: Optional[bool] = None
    level: Optional[str] = None
    hidden: bool = False
    max_frames: int = 0
    screenshot: Optional[str] = None
    import_save: Optional[str] = None
    show_fps: bool = False


class App:
    def __init__(self, options: AppOptions | None = None) -> None:
        self.opts = options or AppOptions()
        pygame.init()
        self.campaign: Campaign = load_campaign()
        self.view = savemod.CampaignView.from_campaign(self.campaign)
        self.save, notices = savemod.load_save(self.view)
        if self.opts.import_save:
            data, more = savemod.import_legacy_file(__import__("pathlib").Path(self.opts.import_save), self.view)
            if data.migrated_from:
                data.settings = self.save.settings
                self.save = data
            notices += more
        st = self.save.settings
        desktop = pygame.display.get_desktop_sizes()[0] if pygame.display.get_init() and pygame.display.get_desktop_sizes() else (1920, 1080)
        res = choose_resolution(self.opts.resolution or st.resolution, desktop)
        fullscreen = self.opts.fullscreen if self.opts.fullscreen is not None else st.fullscreen
        self.display = Display(res, title="Lume — As Dez Fronteiras", fullscreen=fullscreen, vsync=st.vsync, hidden=self.opts.hidden)
        quality = st.quality if st.quality != "auto" else ("medium" if self.display.software else "high")
        self.scene = Scene(self.display, effects=st.effects, quality=quality)
        self.audio = AudioSystem(st.music, st.sfx)
        self.input = InputSystem()
        self.toasts: list[Toast] = [Toast(n, 4.0) for n in notices]
        self.screen = "title"
        self.cursor = 0
        self.world_cursor = 0
        self.level_cursor = 0
        self.in_world = False
        self.settings_from = "title"
        self.confirm_reset = False
        self.game: Optional[Game] = None
        self.demo = Game([self.campaign.levels[0]])
        self.running = True
        self.fps = 0.0
        self.frames = 0
        self.level_card = 0.0
        self.result: dict = {}
        self.show_fps = self.opts.show_fps or st.show_fps
        self._persist()
        if self.opts.level:
            self.start_level(self.opts.level)

    # ------------------------------------------------------------------ persistence
    def _persist(self) -> None:
        self.save.achievements = sorted(set(self.save.achievements) | set(achievements_for(self.save, self.campaign)))
        if not savemod.write_save(self.save, self.view):
            self.toast("Não foi possível gravar o progresso nesta pasta; ele vale só nesta sessão.")

    def toast(self, text: str) -> None:
        if text and not any(t.text == text for t in self.toasts):
            self.toasts.append(Toast(text))

    # ------------------------------------------------------------------ flow
    def playable_index(self, level_id: str) -> int:
        return [lvl.id for lvl in self.campaign.levels].index(level_id)

    def continue_level(self) -> str:
        for lvl in self.campaign.levels:
            if lvl.id in self.save.unlocked and lvl.id not in self.save.completed:
                return lvl.id
        unlocked = [lvl.id for lvl in self.campaign.levels if lvl.id in self.save.unlocked]
        return unlocked[-1] if unlocked else self.campaign.levels[0].id

    def start_level(self, level_id: str, keep_stats: bool = False) -> None:
        index = self.playable_index(level_id)
        if self.game is None:
            self.game = Game(self.campaign.levels)
        if keep_stats:
            self.game.load(index)
        else:
            self.game.start(index)
        self.screen = "play"
        self.level_card = 3.0
        self.input.clear()
        self.audio.pause(False)
        self.audio.play_music(self.game.level.music)
        entry = self.campaign.entry(level_id)
        world = self.campaign.world(entry.world)
        self.card_text = (f"Mundo {world.number}-{entry.slot}", self.game.level.name, world.name)

    def finish_level(self) -> None:
        g = self.game
        assert g is not None
        level = g.level
        record_before = self.save.records.get(level.id, 0)
        gained = g.score - g.level_start_score
        savemod.complete_level(self.save, self.view, level.id, gained, sorted(g.found), sorted(g.secrets_found))
        self._persist()
        nxt = self.view.next_after(level.id)
        self.result = {
            "name": level.name, "score": gained, "coins": g.coins_total, "relics": len(g.found),
            "relics_total": len([c for c in g.coins if c.special]), "secrets": len(g.secrets_found),
            "record": gained > record_before, "next": nxt,
        }
        self.screen = "results"
        self.cursor = 0

    # ------------------------------------------------------------------ main loop
    def run(self) -> None:
        clock = pygame.time.Clock()
        last = time.perf_counter()
        fps_t, fps_n = last, 0
        while self.running:
            now = time.perf_counter()
            dt = min(0.25, now - last)
            last = now
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.WINDOWCLOSE):
                    self.running = False
                elif event.type in (pygame.WINDOWRESIZED, pygame.WINDOWSIZECHANGED):
                    if self.display.resized():
                        self.scene.resize()
                elif event.type == pygame.WINDOWFOCUSLOST and self.screen == "play":
                    self.screen = "pause"
                    self.cursor = 0
                    self.audio.pause(True)
                self.input.handle(event)
            self.update(dt)
            self.render(dt)
            self.display.present()
            self.frames += 1
            fps_n += 1
            if now - fps_t >= 0.5:
                self.fps = fps_n / (now - fps_t)
                fps_t, fps_n = now, 0
            if self.opts.max_frames and self.frames >= self.opts.max_frames:
                if self.opts.screenshot:
                    pygame.image.save(self.display.screenshot(), self.opts.screenshot)
                self.running = False
            if self.display.software:
                clock.tick(60)
        self.audio.stop()
        pygame.quit()

    def update(self, dt: float) -> None:
        for t in self.toasts:
            t.life -= dt
        self.toasts = [t for t in self.toasts if t.life > 0][-4:]
        actions = self.input.menu_actions()
        if self.screen == "play":
            self._update_play(dt)
        elif self.screen == "title":
            self._menu(actions, 4, self._title_select)
            self.audio.play_music("menu")
        elif self.screen == "map":
            self._update_map(actions)
        elif self.screen == "pause":
            if "pause" in actions:
                self._resume()
                return
            self._menu(actions, 5, self._pause_select, back=self._resume)
        elif self.screen == "results":
            self._menu(actions, 2, self._results_select)
            if self.game:
                self.game.update(dt, InputState())
        elif self.screen == "gameover":
            self._menu(actions, 2, self._gameover_select)
        elif self.screen == "settings":
            self._update_settings(actions)
        if self.screen in ("title", "map", "settings") and self.demo is not None:
            self.demo.camera.x = (self.demo.camera.x + dt * 40) % max(1.0, self.demo.level.width - 960)

    def _menu(self, actions, count: int, select, back=None) -> None:
        for a in actions:
            if a == "up":
                self.cursor = (self.cursor - 1) % count
            elif a == "down":
                self.cursor = (self.cursor + 1) % count
            elif a == "confirm":
                self.audio.effect("coin")
                select(self.cursor)
            elif a == "back" and back:
                back()

    def _title_select(self, i: int) -> None:
        if i == 0:
            self.start_level(self.continue_level())
        elif i == 1:
            self.screen, self.in_world, self.cursor = "map", False, 0
        elif i == 2:
            self.settings_from, self.screen, self.cursor = "title", "settings", 0
        else:
            self.running = False

    def _pause_select(self, i: int) -> None:
        g = self.game
        if i == 0:
            self._resume()
        elif i == 1 and g:
            self.start_level(g.level.id)
        elif i == 2:
            self.settings_from, self.screen, self.cursor = "pause", "settings", 0
        elif i == 3:
            self.screen, self.in_world, self.cursor = "map", False, 0
            self.audio.pause(False)
        else:
            self.screen, self.cursor = "title", 0
            self.audio.pause(False)

    def _resume(self) -> None:
        self.screen = "play"
        self.input.clear()
        self.audio.pause(False)

    def _results_select(self, i: int) -> None:
        nxt = self.result.get("next")
        if i == 0 and nxt:
            self.start_level(nxt, keep_stats=True)
        else:
            self.screen, self.in_world, self.cursor = "map", False, 0

    def _gameover_select(self, i: int) -> None:
        if i == 0 and self.game:
            self.start_level(self.game.level.id)
        else:
            self.screen, self.in_world, self.cursor = "map", False, 0

    def _update_play(self, dt: float) -> None:
        g = self.game
        assert g is not None
        state = self.input.read()
        if state.pause_pressed and g.status == "playing":
            g.pause()
            self.screen = "pause"
            self.cursor = 0
            self.audio.pause(True)
            return
        if g.status == "paused":
            g.resume()
        before = len(g.events)
        g.update(dt, state)
        events = g.events[before:]
        self.scene.handle_events(g, events)
        for ev in events:
            sound = SOUND_FOR.get(ev.type)
            if sound:
                self.audio.effect(sound)
            if ev.text and ev.type not in ("complete",):
                self.toast(ev.text)
            if ev.type == "complete":
                self.finish_level()
        if len(g.events) > 400:
            del g.events[:-50]
        boss_near = any(e.alive and g.profiles[e.species].boss and abs(e.x - g.player.x) < 700 for e in g.enemies)
        self.audio.play_music("boss" if boss_near else g.level.music)
        for hint in g.level.hints:
            key = (g.level.id, hint.x)
            if abs(g.player.x - hint.x) < 70 and key not in getattr(self, "_hints_seen", set()):
                self._hints_seen = getattr(self, "_hints_seen", set()) | {key}
                self.toast(hint.text)
        if g.status == "gameover":
            self.screen, self.cursor = "gameover", 0
        self.level_card = max(0.0, self.level_card - dt)

    # ------------------------------------------------------------------ world map
    def _update_map(self, actions) -> None:
        worlds = self.campaign.worlds
        for a in actions:
            if not self.in_world:
                if a == "left":
                    self.world_cursor = (self.world_cursor - 1) % len(worlds)
                elif a == "right":
                    self.world_cursor = (self.world_cursor + 1) % len(worlds)
                elif a == "up":
                    self.world_cursor = (self.world_cursor - 5) % len(worlds)
                elif a == "down":
                    self.world_cursor = (self.world_cursor + 5) % len(worlds)
                elif a == "confirm":
                    self.in_world, self.level_cursor = True, 0
                    self.audio.effect("coin")
                elif a == "back":
                    self.screen, self.cursor = "title", 0
            else:
                entries = worlds[self.world_cursor].entries
                if a == "up":
                    self.level_cursor = (self.level_cursor - 1) % len(entries)
                elif a == "down":
                    self.level_cursor = (self.level_cursor + 1) % len(entries)
                elif a == "back":
                    self.in_world = False
                elif a == "confirm":
                    entry = entries[self.level_cursor]
                    if entry.implemented and entry.id in self.save.unlocked:
                        self.start_level(entry.id)
                    else:
                        self.audio.effect("bump")

    # ------------------------------------------------------------------ settings
    SETTINGS = ("music", "sfx", "effects", "quality", "resolution", "fullscreen", "vsync", "show_fps", "reset", "back")

    def _update_settings(self, actions) -> None:
        st = self.save.settings
        n = len(self.SETTINGS)
        for a in actions:
            key = self.SETTINGS[self.cursor]
            if a == "up":
                self.cursor = (self.cursor - 1) % n
                self.confirm_reset = False
            elif a == "down":
                self.cursor = (self.cursor + 1) % n
                self.confirm_reset = False
            elif a in ("left", "right", "confirm"):
                step = -1 if a == "left" else 1
                if key in ("music", "sfx"):
                    setattr(st, key, round(max(0.0, min(1.0, getattr(st, key) + 0.1 * (step if a != "confirm" else 1))), 2))
                    self.audio.set_volumes(st.music, st.sfx)
                    self.audio.effect("coin")
                elif key in ("effects", "fullscreen", "vsync", "show_fps"):
                    setattr(st, key, not getattr(st, key))
                    self.scene.effects = st.effects
                    self.show_fps = st.show_fps
                    if key in ("fullscreen", "vsync"):
                        self.toast("A alteração vale na próxima abertura do jogo.")
                elif key == "quality":
                    options = list(savemod.QUALITY)
                    st.quality = options[(options.index(st.quality) + step) % len(options)]
                    self.toast("Qualidade aplicada na próxima fase carregada.")
                elif key == "resolution":
                    options = list(savemod.RESOLUTIONS)
                    st.resolution = options[(options.index(st.resolution) + step) % len(options)]
                    self.toast("Resolução aplicada na próxima abertura do jogo.")
                elif key == "reset" and a == "confirm":
                    if self.confirm_reset:
                        settings = self.save.settings
                        self.save = savemod.reset_save(self.view)
                        self.save.settings = settings
                        self.toast("Progresso reiniciado (cópia de segurança mantida).")
                        self.confirm_reset = False
                    else:
                        self.confirm_reset = True
                elif key == "back" and a == "confirm":
                    self.screen, self.cursor = self.settings_from, 0
                self._persist()
            elif a == "back":
                self._persist()
                self.screen, self.cursor = self.settings_from, 0

    # ------------------------------------------------------------------ rendering
    def render(self, dt: float) -> None:
        sc = self.scene
        if self.screen in ("play", "pause", "results", "gameover") and self.game is not None:
            sc.render(self.game, dt if self.screen == "play" else 0.0, hud=True)
            if self.screen == "play":
                self._overlays(dt)
            elif self.screen == "pause":
                self._dim()
                self._list("Pausa", ["Continuar", "Reiniciar fase", "Configurações", "Mapa dos mundos", "Menu principal"])
            elif self.screen == "results":
                self._dim(0.35)
                self._results()
            else:
                self._dim()
                self._list("Fim de jogo", ["Tentar novamente", "Mapa dos mundos"])
        else:
            sc.render(self.demo, dt * 0.5, hud=False)
            self._dim(0.25)
            if self.screen == "title":
                self._title()
            elif self.screen == "map":
                self._map()
            elif self.screen == "settings":
                self._settings()
        self._toasts()
        if self.show_fps:
            sc.text.draw(f"{self.fps:5.1f} FPS · {sc.stats['draws']} desenhos", 12, 520, 12, (255, 255, 255), outline=(0, 0, 0))

    def _dim(self, alpha: float = 0.5) -> None:
        self.display.fill_rect(0, 0, 960, 540, (8, 10, 18), alpha)

    def _title(self) -> None:
        t = self.scene.text
        t.draw("Lume", 480, 92, 92, (255, 236, 170), "display", "center", outline=(40, 24, 30))
        t.draw("As Dez Fronteiras", 480, 196, 26, (230, 245, 255), "display", "center", outline=(20, 30, 45))
        labels = ["Jogar", "Mapa dos mundos", "Configurações", "Sair"]
        for i, label in enumerate(labels):
            sub = ""
            if i == 0:
                entry = self.campaign.entry(self.continue_level())
                sub = f"{self.campaign.world(entry.world).name} · {entry.name}"
            button(self.scene, label, 360, 250 + i * 62, 240, 50, self.cursor == i, sub=sub)
        t.draw("Projeto independente e original · sem vínculo com a Nintendo", 480, 516, 11, (210, 220, 235), "ui", "center")

    def _map(self) -> None:
        sc, t = self.scene, self.scene.text
        t.draw("Mapa dos mundos", 480, 26, 30, (255, 240, 200), "display", "center", outline=(30, 20, 30))
        worlds = self.campaign.worlds
        if not self.in_world:
            for i, w in enumerate(worlds):
                cx, cy = 60 + (i % 5) * 172, 96 + (i // 5) * 196
                done = sum(1 for e in w.entries if e.id in self.save.completed)
                playable = sum(1 for e in w.entries if e.implemented)
                relics = sum(len(self.save.relics.get(e.id, [])) for e in w.entries)
                panel(sc, cx, cy, 156, 172, w.color, 0.92, "#ffe9a8" if i == self.world_cursor else "#ffffff", glow=i == self.world_cursor)
                t.draw(f"Mundo {w.number}", cx + 78, cy + 14, 14, (255, 255, 255), "ui", "center", outline=(20, 20, 30))
                t.draw(w.name, cx + 78, cy + 40, 17, (255, 255, 255), "display", "center", outline=(20, 20, 30))
                t.draw(f"{done}/6 concluídas", cx + 78, cy + 96, 13, (255, 255, 255), "ui", "center", outline=(20, 20, 30))
                t.draw(f"{playable}/6 disponíveis", cx + 78, cy + 116, 12, (235, 240, 250), "ui", "center", outline=(20, 20, 30))
                t.draw(f"{relics} relíquias", cx + 78, cy + 136, 12, (190, 255, 236), "ui", "center", outline=(20, 20, 30))
            t.draw("←/→ escolher · Enter abrir · Esc voltar", 480, 508, 12, (220, 230, 240), "ui", "center")
        else:
            w = worlds[self.world_cursor]
            panel(sc, 150, 70, 660, 420, "#1e2a40", 0.93)
            t.draw(f"Mundo {w.number} · {w.name}", 480, 82, 22, (255, 240, 200), "display", "center")
            t.draw(w.subtitle, 480, 112, 13, (200, 214, 230), "ui", "center")
            for i, e in enumerate(w.entries):
                y = 140 + i * 56
                unlocked = e.id in self.save.unlocked
                status = "concluída" if e.id in self.save.completed else ("disponível" if unlocked and e.implemented else
                          "em desenvolvimento" if not e.implemented else "bloqueada")
                rec = self.save.records.get(e.id)
                relics = len(self.save.relics.get(e.id, []))
                sub = f"{status}" + (f" · recorde {rec}" if rec else "") + (f" · {relics} relíquia(s)" if relics else "")
                button(sc, f"{w.number}-{e.slot}  {e.name}", 190, y, 580, 48, i == self.level_cursor, e.implemented and unlocked, sub)
            t.draw("↑/↓ escolher · Enter jogar · Esc voltar", 480, 508, 12, (220, 230, 240), "ui", "center")

    def _list(self, title: str, labels: list[str]) -> None:
        self.scene.text.draw(title, 480, 120, 34, (255, 240, 200), "display", "center", outline=(30, 20, 30))
        for i, label in enumerate(labels):
            button(self.scene, label, 360, 180 + i * 58, 240, 46, self.cursor == i)

    def _results(self) -> None:
        r, t = self.result, self.scene.text
        panel(self.scene, 250, 90, 460, 330, "#1e2a40", 0.93)
        t.draw("Fase concluída!", 480, 104, 30, (255, 236, 170), "display", "center")
        t.draw(r.get("name", ""), 480, 146, 16, (220, 235, 250), "ui", "center")
        rows = [("Pontos", f"{r.get('score', 0)}" + ("  · novo recorde!" if r.get("record") else "")),
                ("Moedas", str(r.get("coins", 0))), ("Relíquias", f"{r.get('relics', 0)}/{r.get('relics_total', 0)}"),
                ("Segredos", str(r.get("secrets", 0)))]
        for i, (k, v) in enumerate(rows):
            t.draw(k, 290, 186 + i * 30, 16, (190, 205, 225), "ui")
            t.draw(v, 670, 186 + i * 30, 16, (255, 255, 255), "display", "right")
        labels = ["Próxima fase" if r.get("next") else "Campanha disponível concluída", "Mapa dos mundos"]
        for i, label in enumerate(labels):
            button(self.scene, label, 280 + i * 210, 340, 190, 46, self.cursor == i, i == 1 or bool(r.get("next")))

    def _settings(self) -> None:
        st, t = self.save.settings, self.scene.text
        panel(self.scene, 220, 50, 520, 450, "#1e2a40", 0.94)
        t.draw("Configurações", 480, 62, 26, (255, 240, 200), "display", "center")
        names = {"music": "Música", "sfx": "Efeitos sonoros", "effects": "Efeitos visuais", "quality": "Qualidade",
                 "resolution": "Resolução", "fullscreen": "Tela cheia", "vsync": "Sincronia vertical", "show_fps": "Mostrar FPS",
                 "reset": "Apagar progresso", "back": "Voltar"}
        for i, key in enumerate(self.SETTINGS):
            y = 104 + i * 38
            selected = i == self.cursor
            if selected:
                self.display.fill_rect(236, y - 4, 488, 34, (60, 110, 160), 0.6)
            t.draw(names[key], 250, y, 16, (255, 255, 255) if selected else (205, 215, 230), "ui")
            value = ""
            if key in ("music", "sfx"):
                value = f"{int(getattr(st, key) * 100)}%"
            elif key in ("effects", "fullscreen", "vsync", "show_fps"):
                value = "ligado" if getattr(st, key) else "desligado"
            elif key == "quality":
                value = QUALITY_NAMES.get(st.quality, st.quality)
            elif key == "resolution":
                value = "automática" if st.resolution == "auto" else st.resolution.replace("x", " × ")
            elif key == "reset":
                value = "Enter de novo para confirmar" if self.confirm_reset else "Enter"
            t.draw(value, 710, y, 16, (255, 236, 170), "display", "right")
        info = self.display.info()
        t.draw(f"Renderizador: {'GPU' if info.accelerated else 'software'} · {info.size[0]}×{info.size[1]} · escala {info.scale:.2f}",
               480, 486, 11, (190, 200, 215), "ui", "center")

    def _overlays(self, dt: float) -> None:
        t = self.scene.text
        if self.level_card > 0 and self.game is not None:
            a = min(1.0, self.level_card / 0.6)
            panel(self.scene, 300, 200, 360, 120, "#1e2a40", 0.9 * a)
            t.draw(self.card_text[0], 480, 214, 16, (190, 255, 236), "ui", "center", alpha=a)
            t.draw(self.card_text[1], 480, 238, 30, (255, 240, 200), "display", "center", alpha=a)
            t.draw(self.card_text[2], 480, 284, 14, (220, 230, 245), "ui", "center", alpha=a)

    def _toasts(self) -> None:
        for i, toast in enumerate(self.toasts[-3:]):
            a = min(1.0, toast.life / 0.4)
            y = 470 - i * 40
            w = min(700, 30 + len(toast.text) * 8.4)
            panel(self.scene, 480 - w / 2, y, w, 30, "#1e2a40", 0.88 * a)
            self.scene.text.draw(toast.text, 480, y + 6, 15, (255, 255, 255), "ui", "center", alpha=a)
