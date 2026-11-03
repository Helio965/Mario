"""Áudio sintetizado (substitui ``src/systems/audio.ts``).

CONTRATO (implementação completa pelo agente de áudio):

* Nenhum arquivo de áudio externo: trilhas e efeitos são sintetizados com
  ``numpy`` (ondas quadrada/triangular/dente de serra, envelopes) e enviados
  ao ``pygame.mixer`` via ``pygame.sndarray``. As seis trilhas de 32 passos,
  a trilha de chefe e os 14 cues de ``src/systems/audio.ts`` devem ser
  portados nota a nota (MIDI → Hz, BPM, timbres).
* Quatro barramentos independentes: ``music``, ``sfx``, ``voice``,
  ``ambient`` (grupos de ``pygame.mixer.Channel`` reservados). Silenciar a
  música nunca silencia os efeitos.
* ``set_world(world, boss=False)`` troca a trilha com crossfade; ``menu()``
  toca a trilha 0; ``pause(True/False)`` pausa/retoma a música.
* Limite de instâncias simultâneas por efeito (evitar sobreposição excessiva).
* Tolerante à ausência de dispositivo de áudio (``SDL_AUDIODRIVER=dummy`` ou
  falha de ``mixer.init``): o jogo continua em silêncio sem exceções.
* ``update(dt)`` é chamado a cada quadro para crossfades e agendamento.

IMPLEMENTAÇÃO:

* A síntese em si (tabelas, osciladores, envelopes) está em ``synth.py``;
  aqui ficam o mixer, os barramentos, o cache de ``Sound`` e o agendamento.
* Cada trilha é renderizada como um loop completo (32 passos) e tocada com
  ``loops=-1`` em um de dois canais de música alternados; a troca faz um
  crossfade linear de 0,4 s. Ambientes usam o mesmo esquema com fade de 1 s.
* Canais reservados: 0-1 música, 2-9 efeitos, 10-11 vozes, 12-13 ambiente.
* Os cues (os 14 do original mais ``boss_intro``, ``boss_phase``, ``talk`` e
  ``npc_say`` dos eventos novos do núcleo Python) são sintetizados no
  ``__init__``; trilhas, ambientes e vozes são renderizados em uma thread de
  fundo (só numpy) e embrulhados em ``Sound`` no thread principal quando
  pedidos. ``prewarm()`` força tudo de uma vez.
* Diferença deliberada do original: efeitos e vozes continuam disponíveis
  com a música pausada (menus de pausa podem soar).
* ``voice(name)`` devolve a chave de localização da legenda
  (``voice.<nome>``) ou ``None`` para nomes desconhecidos; o texto final vem
  da ``Localization`` do chamador.
"""

from __future__ import annotations

import contextlib
import math
import threading
from dataclasses import dataclass
from typing import Any, Final, Literal

import pygame
import pygame.sndarray
from numpy.typing import NDArray

from game.core.types import EventType
from game.systems import synth
from game.systems.synth import BOSS_TRACK, CUES, TRACKS, Track

Bus = Literal["music", "sfx", "voice", "ambient"]
AssetKey = tuple[str, str]

MUSIC_FADE_SECONDS: Final = 0.4
AMBIENT_FADE_SECONDS: Final = 1.0
AMBIENT_LEVEL: Final = 0.6  # atenuação extra do barramento ambiente: fundo discreto
MAX_INSTANCES_PER_EFFECT: Final = 3
MUSIC_CHANNELS: Final = 2
SFX_CHANNELS: Final = 8
VOICE_CHANNELS: Final = 2
AMBIENT_CHANNELS: Final = 2
RESERVED_CHANNELS: Final = MUSIC_CHANNELS + SFX_CHANNELS + VOICE_CHANNELS + AMBIENT_CHANNELS
TOTAL_CHANNELS: Final = RESERVED_CHANNELS + 2
BUSES: Final[tuple[Bus, ...]] = ("music", "sfx", "voice", "ambient")
DEFAULT_VOLUMES: Final[dict[str, float]] = {
    "music": 0.45,
    "sfx": 0.75,
    "voice": 0.8,
    "ambient": 0.6,
}
# Efeitos de maior prioridade não são roubados por efeitos menores quando os 8 canais lotam.
EFFECT_PRIORITY: Final[dict[str, int]] = {
    "death": 5,
    "complete": 5,
    "boss": 4,
    "boss_intro": 4,
    "boss_phase": 4,
    "life": 4,
    "power": 3,
    "hurt": 3,
    "relic": 3,
    "secret": 3,
    "checkpoint": 3,
    "stomp": 2,
    "shot": 1,
    "block": 1,
    "jump": 1,
    "coin": 0,
    "talk": 0,
    "npc_say": 0,
}
VOICE_CAPTION_KEYS: Final[dict[str, str]] = {name: f"voice.{name}" for name in synth.VOICE_NAMES}


@dataclass(slots=True)
class _LoopSlot:
    """Canal de loop (música ou ambiente) com peso de crossfade em [0, 1]."""

    channel: pygame.mixer.Channel
    key: AssetKey | None = None
    weight: float = 0.0
    target: float = 0.0


@dataclass(slots=True)
class _OneShotSlot:
    """Canal de efeito/voz: ``kind`` em reprodução, ordem de chegada e prioridade."""

    channel: pygame.mixer.Channel
    kind: str | None = None
    serial: int = 0
    priority: int = 0


class AudioSystem:
    def __init__(self, enabled: bool = True, *, background: bool = True) -> None:
        self._enabled = enabled
        self._available = False
        self._owns_mixer = False
        self._disposed = False
        self._paused = False
        self._volumes: dict[str, float] = dict(DEFAULT_VOLUMES)
        self._sample_rate = synth.SAMPLE_RATE
        self._size = -16
        self._channels = 2
        self._lock = threading.Lock()
        self._arrays: dict[AssetKey, NDArray[Any]] = {}
        self._rendered: set[AssetKey] = set()
        self._sounds: dict[AssetKey, pygame.mixer.Sound] = {}
        self._thread: threading.Thread | None = None
        self._music: list[_LoopSlot] = []
        self._ambient: list[_LoopSlot] = []
        self._sfx: list[_OneShotSlot] = []
        self._voice: list[_OneShotSlot] = []
        self._serial = 0
        self._track: Track | None = None
        self._ambient_name: str | None = None
        if not enabled:
            return
        self._available = self._open_mixer()
        if not self._available:
            return
        self._prepare_cues()
        if background:
            self._start_background()

    # -------------------------------------------------------------- consultas
    @property
    def available(self) -> bool:
        return self._available and not self._disposed

    @property
    def sample_rate(self) -> int:
        return self._sample_rate

    @property
    def track(self) -> Track | None:
        """Trilha alvo atual (mesmo sem mixer, para depuração e testes)."""
        return self._track

    @property
    def ambient_name(self) -> str | None:
        return self._ambient_name

    @property
    def paused(self) -> bool:
        return self._paused

    @property
    def volumes(self) -> dict[str, float]:
        return dict(self._volumes)

    @property
    def music_weights(self) -> tuple[float, ...]:
        return tuple(slot.weight for slot in self._music)

    @property
    def fading(self) -> bool:
        return any(slot.weight != slot.target for slot in (*self._music, *self._ambient))

    def bus_channels(self, bus: Bus | str) -> list[pygame.mixer.Channel]:
        if bus == "music":
            return [slot.channel for slot in self._music]
        if bus == "ambient":
            return [slot.channel for slot in self._ambient]
        if bus == "voice":
            return [slot.channel for slot in self._voice]
        return [slot.channel for slot in self._sfx]

    def active_effects(self, kind: str | None = None) -> int:
        """Quantos efeitos soam agora (opcionalmente só de um tipo)."""
        if not self.available:
            return 0
        self._release_finished(self._sfx)
        return sum(1 for slot in self._sfx if slot.kind is not None and kind in (None, slot.kind))

    def active_voices(self) -> int:
        if not self.available:
            return 0
        self._release_finished(self._voice)
        return sum(1 for slot in self._voice if slot.kind is not None)

    def has_sound(self, kind: str, name: str) -> bool:
        return (kind, name) in self._sounds

    # ------------------------------------------------------------- API pública
    def set_volumes(
        self, music: float, sfx: float, voice: float | None = None, ambient: float | None = None
    ) -> None:
        self._volumes["music"] = synth.clamp01(music)
        self._volumes["sfx"] = synth.clamp01(sfx)
        if voice is not None:
            self._volumes["voice"] = synth.clamp01(voice)
        if ambient is not None:
            self._volumes["ambient"] = synth.clamp01(ambient)
        if self.available:
            self._apply_bus_volumes()

    def set_world(self, world: int, boss: bool = False) -> None:
        index = max(1, min(5, math.floor(world))) if math.isfinite(world) else 1
        self._change_track(BOSS_TRACK if boss else TRACKS[index])

    def menu(self) -> None:
        self._change_track(TRACKS[0])

    def pause(self, paused: bool) -> None:
        if self._paused == paused:
            return
        self._paused = paused
        if not self.available:
            return
        for slot in (*self._music, *self._ambient):
            if slot.key is None:
                continue
            try:
                if paused:
                    slot.channel.pause()
                else:
                    slot.channel.unpause()
            except pygame.error:
                self._release_loop_slot(slot)

    def effect(self, kind: EventType | str) -> None:
        if not self.available:
            return
        name = str(kind)
        if name not in CUES or self._volumes["sfx"] <= 0:
            return
        sound = self._sound(("cue", name))
        if sound is None:
            return
        priority = EFFECT_PRIORITY.get(name, 0)
        slot = self._acquire(self._sfx, name, priority, MAX_INSTANCES_PER_EFFECT)
        if slot is not None:
            self._play_one_shot(slot, sound, name, priority, self._volumes["sfx"])

    def voice(self, name: str) -> str | None:
        """Toca uma vocalização e devolve a chave de legenda (``voice.<nome>``) ou ``None``."""
        key = name.strip().lower()
        caption = VOICE_CAPTION_KEYS.get(key)
        if caption is None:
            return None
        if self.available and self._volumes["voice"] > 0:
            sound = self._sound(("voice", key))
            if sound is not None:
                slot = self._acquire(self._voice, key, 0, 1)
                if slot is not None:
                    self._play_one_shot(slot, sound, key, 0, self._volumes["voice"])
        return caption

    def ambient(self, name: str | None) -> None:
        resolved = synth.resolve_ambient(name)
        self._ambient_name = resolved
        if not self.available:
            return
        if resolved is None:
            for slot in self._ambient:
                slot.target = 0.0
            return
        self._switch_loop(self._ambient, ("ambient", resolved))

    def update(self, dt: float) -> None:
        if not self.available or not dt > 0:  # NaN e dt <= 0 não avançam nada
            return
        if self._paused:
            return
        dt = min(dt, 0.25)
        self._advance(self._music, dt / MUSIC_FADE_SECONDS, self._volumes["music"])
        self._advance(
            self._ambient, dt / AMBIENT_FADE_SECONDS, self._volumes["ambient"] * AMBIENT_LEVEL
        )

    def prewarm(self, wait: bool = True, timeout: float | None = None) -> None:
        """Sintetiza trilhas, ambientes e vozes; com ``wait`` bloqueia até tudo estar pronto."""
        if not self.available:
            return
        self._start_background()
        if not wait:
            return
        if self._thread is not None:
            self._thread.join(timeout)
        for key in self._background_keys():
            self._sound(key)

    def dispose(self) -> None:
        if self._disposed:
            return
        self._disposed = True
        if not self._available:
            return
        for slot in (*self._music, *self._ambient):
            self._stop_channel(slot.channel)
            self._release_loop_slot(slot)
        for one_shot in (*self._sfx, *self._voice):
            self._stop_channel(one_shot.channel)
            one_shot.kind = None
        self._sounds.clear()
        with self._lock:
            self._arrays.clear()
        if self._owns_mixer:
            with contextlib.suppress(pygame.error):
                pygame.mixer.quit()
        self._available = False

    # ------------------------------------------------------------------ mixer
    def _open_mixer(self) -> bool:
        """Abre (ou adota) o mixer e reserva os canais; qualquer falha deixa o jogo mudo."""
        try:
            already = pygame.mixer.get_init() is not None
            pygame.mixer.init(frequency=synth.SAMPLE_RATE, size=-16, channels=2, buffer=512)
            info = pygame.mixer.get_init()
            if info is None:
                return False
            self._owns_mixer = not already
            self._sample_rate, self._size, self._channels = int(info[0]), int(info[1]), int(info[2])
            if pygame.mixer.get_num_channels() < TOTAL_CHANNELS:
                pygame.mixer.set_num_channels(TOTAL_CHANNELS)
            pygame.mixer.set_reserved(RESERVED_CHANNELS)
            index = 0
            self._music = [
                _LoopSlot(pygame.mixer.Channel(index + i)) for i in range(MUSIC_CHANNELS)
            ]
            index += MUSIC_CHANNELS
            self._sfx = [_OneShotSlot(pygame.mixer.Channel(index + i)) for i in range(SFX_CHANNELS)]
            index += SFX_CHANNELS
            self._voice = [
                _OneShotSlot(pygame.mixer.Channel(index + i)) for i in range(VOICE_CHANNELS)
            ]
            index += VOICE_CHANNELS
            self._ambient = [
                _LoopSlot(pygame.mixer.Channel(index + i)) for i in range(AMBIENT_CHANNELS)
            ]
        except Exception:  # pygame.error, ValueError... — sem dispositivo, sem som
            self._music, self._sfx, self._voice, self._ambient = [], [], [], []
            return False
        self._available = True
        self._apply_bus_volumes()
        return True

    def _prepare_cues(self) -> None:
        for name in CUES:
            self._sound(("cue", name))

    @staticmethod
    def _background_keys() -> list[AssetKey]:
        keys: list[AssetKey] = [("track", track.name) for track in synth.ALL_TRACKS]
        keys.extend(("ambient", name) for name in synth.AMBIENT_NAMES)
        keys.extend(("voice", name) for name in synth.VOICE_NAMES)
        return keys

    def _start_background(self) -> None:
        if self._thread is not None or self._disposed:
            return
        self._thread = threading.Thread(
            target=self._render_in_background,
            args=(self._background_keys(),),
            name="lume-audio-synth",
            daemon=True,
        )
        self._thread.start()

    def _render_in_background(self, keys: list[AssetKey]) -> None:
        """Só numpy nesta thread: os arrays prontos viram ``Sound`` no thread principal."""
        for key in keys:
            if self._disposed:
                return
            with self._lock:
                done = key in self._rendered
            if done:
                continue
            try:
                array = self._render_array(key)
            except Exception:  # a síntese nunca derruba a thread nem o jogo
                continue
            with self._lock:
                if key not in self._rendered:
                    self._arrays[key] = array
                    self._rendered.add(key)

    def _render_array(self, key: AssetKey) -> NDArray[Any]:
        kind, name = key
        if kind == "track":
            mono = synth.render_track(synth.TRACKS_BY_NAME[name], self._sample_rate)
        elif kind == "cue":
            mono = synth.render_cue(CUES[name], self._sample_rate)
        elif kind == "voice":
            mono = synth.render_voice(synth.VOICES[name], self._sample_rate)
        elif kind == "ambient":
            mono = synth.render_ambient(name, self._sample_rate)
        else:
            raise KeyError(kind)
        return synth.to_mixer_array(mono, self._size, self._channels)

    def _sound(self, key: AssetKey) -> pygame.mixer.Sound | None:
        """Devolve o ``Sound`` em cache; renderiza agora se a thread ainda não o entregou."""
        sound = self._sounds.get(key)
        if sound is not None:
            return sound
        with self._lock:
            array = self._arrays.pop(key, None)
        if array is None:
            try:
                array = self._render_array(key)
            except (KeyError, ValueError):
                return None
            with self._lock:
                self._arrays.pop(key, None)
                self._rendered.add(key)
        try:
            sound = pygame.sndarray.make_sound(array)
        except (pygame.error, ValueError, TypeError):
            return None
        self._sounds[key] = sound
        return sound

    # ------------------------------------------------------------------ loops
    def _change_track(self, track: Track) -> None:
        if self._track is track or self._disposed:
            return
        self._track = track
        if self.available:
            self._switch_loop(self._music, ("track", track.name))

    def _switch_loop(self, slots: list[_LoopSlot], key: AssetKey) -> None:
        """Começa ``key`` no canal livre e marca o outro para desaparecer (crossfade)."""
        current = next((slot for slot in slots if slot.target > 0), None)
        if current is not None and current.key == key:
            return
        returning = next((slot for slot in slots if slot.key == key), None)
        if returning is not None:  # ainda soando em fade-out: inverte a direção
            for slot in slots:
                slot.target = 1.0 if slot is returning else 0.0
            return
        free = next((candidate for candidate in slots if candidate.key is None), None)
        slot = free if free is not None else min(slots, key=lambda candidate: candidate.weight)
        sound = self._sound(key)
        if sound is None:
            return
        try:
            if slot.key is not None:
                slot.channel.stop()
            slot.channel.set_volume(0.0)
            slot.channel.play(sound, loops=-1)
            if self._paused:
                slot.channel.pause()
        except pygame.error:
            self._release_loop_slot(slot)
            return
        slot.key = key
        slot.weight = 0.0
        slot.target = 1.0
        for other in slots:
            if other is not slot:
                other.target = 0.0

    def _advance(self, slots: list[_LoopSlot], step: float, bus_volume: float) -> None:
        for slot in slots:
            if slot.key is None or slot.weight == slot.target:
                continue
            if slot.weight < slot.target:
                slot.weight = min(slot.target, slot.weight + step)
            else:
                slot.weight = max(slot.target, slot.weight - step)
            try:
                slot.channel.set_volume(bus_volume * slot.weight)
                if slot.weight <= 0.0 and slot.target <= 0.0:
                    slot.channel.stop()
                    self._release_loop_slot(slot)
            except pygame.error:
                self._release_loop_slot(slot)

    @staticmethod
    def _release_loop_slot(slot: _LoopSlot) -> None:
        """Canal de loop livre: sem chave e com pesos zerados (``fading`` não fica preso)."""
        slot.key = None
        slot.weight = 0.0
        slot.target = 0.0

    # -------------------------------------------------------------- one-shots
    def _release_finished(self, slots: list[_OneShotSlot]) -> None:
        for slot in slots:
            if slot.kind is None:
                continue
            try:
                busy = slot.channel.get_busy()
            except pygame.error:
                busy = False
            if not busy:
                slot.kind = None

    def _acquire(
        self, slots: list[_OneShotSlot], kind: str, priority: int, max_same: int
    ) -> _OneShotSlot | None:
        """Escolhe o canal: livre; senão o mais antigo do mesmo tipo; senão o mais antigo
        de prioridade não superior (efeitos novos substituem o mais antigo do mesmo tipo)."""
        self._release_finished(slots)
        busy = [slot for slot in slots if slot.kind is not None]
        same = [slot for slot in busy if slot.kind == kind]
        if len(same) >= max_same:
            return min(same, key=lambda slot: slot.serial)
        free = next((slot for slot in slots if slot.kind is None), None)
        if free is not None:
            return free
        candidates = [slot for slot in busy if slot.priority <= priority]
        if not candidates:
            return None
        return min(candidates, key=lambda slot: slot.serial)

    def _play_one_shot(
        self, slot: _OneShotSlot, sound: pygame.mixer.Sound, kind: str, priority: int, volume: float
    ) -> None:
        try:
            slot.channel.set_volume(volume)
            slot.channel.play(sound)
        except pygame.error:
            slot.kind = None
            return
        self._serial += 1
        slot.kind = kind
        slot.serial = self._serial
        slot.priority = priority

    # ---------------------------------------------------------------- volumes
    def _apply_bus_volumes(self) -> None:
        music = self._volumes["music"]
        ambient = self._volumes["ambient"] * AMBIENT_LEVEL
        for slot in self._music:
            self._set_channel_volume(slot.channel, music * slot.weight)
        for slot in self._ambient:
            self._set_channel_volume(slot.channel, ambient * slot.weight)
        for one_shot in self._sfx:
            self._set_channel_volume(one_shot.channel, self._volumes["sfx"])
        for one_shot in self._voice:
            self._set_channel_volume(one_shot.channel, self._volumes["voice"])

    @staticmethod
    def _set_channel_volume(channel: pygame.mixer.Channel, volume: float) -> None:
        with contextlib.suppress(pygame.error):
            channel.set_volume(synth.clamp01(volume))

    @staticmethod
    def _stop_channel(channel: pygame.mixer.Channel) -> None:
        with contextlib.suppress(pygame.error):
            channel.stop()
