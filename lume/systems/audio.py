"""Original music and sound effects synthesized locally with numpy.

The six 32-step themes and the boss theme of the web edition (MIDI pitches
from src/systems/audio.ts) are preserved and re-orchestrated (soft lead,
bass, chord stabs, drums, echo). New worlds get new original themes with the
same structure; fortress and underground variants derive from each world.
Tracks are rendered once on demand (a few tens of milliseconds) and looped
by the mixer. No external audio files are used.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

try:  # numpy is a runtime dependency, but audio must never crash the game
    import numpy as np
except Exception:  # pragma: no cover
    np = None  # type: ignore[assignment]

RATE = 44100


@dataclass(frozen=True)
class Track:
    bpm: float
    melody: tuple[int, ...]
    bass: tuple[int, ...]
    lead: str = "triangle"
    third: int = 4
    drums: str = "light"  # light | march | none | heavy | shuffle
    pad: bool = True
    echo: float = 0.18
    transpose: int = 0


# --------------------------------------------------------------------------- legacy themes (web edition)
LEGACY = [
    Track(106, (72, 0, 76, 79, 0, 76, 74, 0, 72, 76, 79, 84, 0, 79, 76, 0, 74, 0, 77, 81, 0, 79, 77, 74, 76, 79, 84, 0, 79, 76, 74, 0),
          (48, 53, 50, 55), "triangle", 4, "light"),
    Track(136, (72, 76, 79, 0, 81, 79, 76, 74, 72, 0, 76, 79, 84, 0, 79, 76, 77, 81, 84, 0, 86, 84, 81, 79, 76, 0, 79, 83, 86, 83, 79, 0),
          (48, 45, 53, 55), "square", 4, "march"),
    Track(118, (69, 0, 72, 76, 0, 77, 76, 72, 71, 0, 74, 77, 80, 0, 77, 74, 72, 76, 81, 0, 79, 76, 72, 0, 71, 74, 76, 80, 0, 76, 71, 0),
          (45, 50, 53, 52), "triangle", 3, "shuffle"),
    Track(112, (74, 0, 78, 81, 85, 0, 81, 78, 76, 0, 81, 83, 86, 0, 83, 81, 78, 81, 85, 88, 0, 85, 81, 78, 76, 78, 81, 85, 0, 81, 78, 0),
          (50, 57, 55, 52), "bell", 4, "light"),
    Track(124, (71, 74, 78, 0, 81, 78, 74, 0, 73, 76, 80, 0, 83, 80, 76, 0, 74, 78, 81, 85, 0, 81, 78, 74, 73, 76, 80, 83, 0, 80, 76, 0),
          (47, 52, 50, 54), "pluck", 3, "light"),
    Track(144, (69, 0, 69, 72, 76, 0, 75, 72, 69, 0, 72, 75, 78, 0, 76, 75, 68, 0, 71, 74, 77, 0, 74, 71, 68, 71, 74, 77, 80, 77, 74, 0),
          (45, 41, 44, 40), "saw", 3, "heavy"),
]
BOSS = Track(164, (57, 69, 57, 72, 57, 69, 75, 72, 56, 68, 56, 71, 56, 68, 74, 71, 53, 65, 53, 68, 53, 65, 71, 68, 52, 64, 52, 67, 52, 64, 70, 67),
             (33, 32, 29, 28), "saw", 3, "heavy", pad=False)
# New original themes (same 32-step grammar)
NEW = {
    "coral_coast": Track(98, (76, 0, 79, 81, 0, 79, 76, 74, 72, 0, 74, 76, 0, 79, 81, 0, 84, 0, 81, 79, 0, 76, 79, 81, 79, 0, 76, 74, 72, 0, 74, 0),
                         (48, 52, 45, 50), "bell", 4, "shuffle", echo=0.32),
    "clockwork_city": Track(128, (67, 67, 74, 0, 72, 70, 67, 0, 65, 65, 72, 0, 70, 69, 65, 0, 67, 70, 74, 79, 0, 77, 74, 70, 72, 0, 70, 69, 67, 0, 62, 0),
                            (43, 41, 39, 38), "square", 3, "march", echo=0.1),
    "sky_archipelago": Track(116, (79, 0, 84, 0, 83, 79, 76, 0, 77, 0, 81, 0, 79, 76, 72, 0, 74, 77, 81, 84, 0, 83, 81, 77, 79, 0, 76, 79, 0, 72, 74, 0),
                             (53, 55, 52, 57), "triangle", 4, "light", echo=0.36),
    "haunted_swamp": Track(92, (64, 0, 0, 67, 66, 0, 64, 0, 63, 0, 0, 66, 64, 0, 59, 0, 60, 0, 63, 67, 0, 66, 63, 0, 62, 0, 59, 0, 0, 58, 59, 0),
                           (40, 39, 36, 35), "pluck", 3, "none", echo=0.42),
    "star_citadel": Track(132, (76, 79, 83, 88, 0, 86, 83, 79, 78, 81, 85, 90, 0, 88, 85, 81, 79, 83, 86, 91, 0, 90, 86, 83, 81, 85, 88, 93, 0, 88, 85, 0),
                          (52, 50, 48, 47), "bell", 4, "march", echo=0.28),
}
WORLD_TRACK = {
    "green_kingdom": LEGACY[1], "golden_desert": LEGACY[2], "frozen_peaks": LEGACY[3], "enchanted_forest": LEGACY[4],
    "volcanic_fortress": LEGACY[5], **NEW,
}


def track_for(track_id: str) -> Track:
    """Resolve ids like 'green_kingdom_main', '<world>_fortress', '<world>_underground', 'boss', 'menu'."""
    if track_id == "menu":
        return LEGACY[0]
    if track_id == "boss":
        return BOSS
    for world, base in WORLD_TRACK.items():
        if track_id.startswith(world):
            if track_id.endswith("_fortress"):
                return Track(base.bpm * 0.92, base.melody, tuple(b - 1 for b in base.bass), "saw", 3, "heavy", False, 0.22, -1)
            if track_id.endswith("_underground"):
                return Track(base.bpm * 0.8, base.melody, base.bass, "pluck", base.third, "none", True, 0.45, -5)
            return base
    return LEGACY[0]


def midi_hz(m: float) -> float:
    return 440.0 * 2 ** ((m - 69) / 12)


# --------------------------------------------------------------------------- synthesis
def _osc(kind: str, freq: float, n: int, phase0: float = 0.0):
    t = np.arange(n) / RATE
    ph = 2 * math.pi * freq * t + phase0
    if kind == "triangle":
        return 2 / math.pi * np.arcsin(np.sin(ph))
    if kind == "square":  # soft square: odd harmonics with roll-off
        return (np.sin(ph) + np.sin(3 * ph) / 3.2 + np.sin(5 * ph) / 6.5 + np.sin(7 * ph) / 11) * 0.8
    if kind == "saw":
        return sum(np.sin(k * ph) / k for k in range(1, 9)) * 0.55
    if kind == "bell":  # simple FM bell
        return np.sin(ph + 1.6 * np.exp(-t * 6) * np.sin(ph * 3.5))
    if kind == "pluck":
        return np.sin(ph) * 0.7 + np.sin(2 * ph) * 0.25 * np.exp(-t * 9) + np.sin(3 * ph) * 0.12 * np.exp(-t * 14)
    if kind == "sine":
        return np.sin(ph)
    return np.sin(ph)


def _env(n: int, attack: float = 0.006, decay: float = 0.08, sustain: float = 0.7, release: float = 0.05, kind: str = "adsr"):
    t = np.arange(n) / RATE
    dur = n / RATE
    if kind == "perc":
        return np.exp(-t / max(1e-3, decay)) * np.minimum(1, t / max(1e-4, attack))
    env = np.ones(n) * sustain
    a = t < attack
    env[a] = t[a] / attack
    d = (t >= attack) & (t < attack + decay)
    env[d] = 1 - (1 - sustain) * (t[d] - attack) / decay
    r = t > dur - release
    env[r] *= np.maximum(0, (dur - t[r]) / release)
    return env


def _note(kind: str, midi: float, dur: float, vol: float, slide: float = 0.0):
    n = max(1, int(dur * RATE))
    if slide:
        t = np.arange(n) / RATE
        f = midi_hz(midi) * 2 ** (slide / 12 * t / dur)
        ph = 2 * math.pi * np.cumsum(f) / RATE
        wave = np.sin(ph) if kind != "square" else (np.sin(ph) + np.sin(3 * ph) / 3.2) * 0.85
    else:
        wave = _osc(kind, midi_hz(midi), n)
    env = _env(n, decay=0.12 if kind in ("bell", "pluck") else 0.06, sustain=0.35 if kind in ("bell", "pluck") else 0.7,
               release=min(0.06, dur * 0.4))
    return wave * env * vol


def _noise(dur: float, vol: float, decay: float, seed: int = 1, tone: float = 0.0):
    n = int(dur * RATE)
    rng = np.random.default_rng(seed)
    w = rng.uniform(-1, 1, n)
    if tone:
        w = w * 0.4 + np.sin(2 * math.pi * tone * np.arange(n) / RATE) * 0.6
    return w * np.exp(-np.arange(n) / RATE / decay) * vol


def render_track(track: Track, loops: int = 2) -> "np.ndarray":
    step = 60.0 / track.bpm / 4
    steps = len(track.melody) * loops
    total = int(steps * step * RATE) + int(RATE * 0.5)
    left = np.zeros(total)
    right = np.zeros(total)

    def put(buf, start: float, data, pan: float = 0.0):
        i = int(start * RATE)
        j = min(total, i + len(data))
        if j <= i:
            return
        left[i:j] += data[: j - i] * (1 - max(0.0, pan))
        right[i:j] += data[: j - i] * (1 + min(0.0, pan))

    tr = track.transpose
    for s in range(steps):
        pos = s % len(track.melody)
        loop = s // len(track.melody)
        when = s * step
        mel = track.melody[pos]
        root = track.bass[(pos // 8) % len(track.bass)] + tr
        if mel:
            m = mel + tr + (12 if loop % 2 == 1 and pos % 8 == 4 else 0)
            put(None, when, _note(track.lead, m, step * 0.9, 0.16), -0.15)
        if pos % 4 == 0:
            put(None, when, _note("triangle", root, step * 2.4, 0.28), 0.0)
        if track.pad and pos % 8 == 0:
            for k, iv in enumerate((0, track.third, 7)):
                put(None, when, _note("sine", root + 24 + iv, step * 7.6, 0.035), 0.3 if k % 2 else -0.3)
        if pos % 2 == 1:
            iv = track.third if pos % 4 == 1 else 7
            put(None, when, _note("triangle", root + 12 + iv, step * 0.7, 0.07), 0.25)
        d = track.drums
        if d != "none":
            if pos % 8 == 0 or (d in ("march", "heavy") and pos % 4 == 0):
                put(None, when, _note("sine", 36 + tr, 0.12, 0.42, slide=-14), 0.0)
            if pos % 8 == 4:
                put(None, when, _noise(0.12, 0.18, 0.05, s, tone=180), 0.05)
            if pos % 2 == 0 or d == "heavy":
                put(None, when, _noise(0.04, 0.05 if d != "heavy" else 0.07, 0.012, s + 99), 0.3)
            if d == "shuffle" and pos % 4 == 3:
                put(None, when, _noise(0.05, 0.05, 0.02, s + 7), -0.3)
    if track.echo:
        delay = int(step * 3 * RATE)
        for buf in (left, right):
            buf[delay:] += buf[:-delay] * track.echo
    mix = np.stack([left, right], axis=1)
    peak = np.max(np.abs(mix)) or 1.0
    mix = np.tanh(mix / peak * 1.2) * 0.85
    loop_len = int(steps * step * RATE)
    return (mix[:loop_len] * 32767).astype(np.int16)


SFX = {
    "jump": [("square", 65, 0.13, 0.25, 14)],
    "coin": [("bell", 91, 0.06, 0.25, 0), ("bell", 98, 0.16, 0.25, 0)],
    "relic": [("bell", 76, 0.1, 0.25, 0), ("bell", 83, 0.1, 0.25, 0), ("bell", 88, 0.1, 0.25, 0), ("bell", 95, 0.3, 0.25, 0)],
    "block": [("triangle", 48, 0.08, 0.35, -12)],
    "bump": [("triangle", 45, 0.07, 0.3, -6)],
    "brick": [("noise", 0, 0.2, 0.35, 0)],
    "sprout": [("triangle", 60, 0.06, 0.25, 0), ("triangle", 67, 0.06, 0.25, 0), ("triangle", 72, 0.1, 0.25, 0)],
    "power": [("square", n, 0.07, 0.2, 0) for n in (60, 64, 67, 72, 76, 79)],
    "hurt": [("saw", 55, 0.13, 0.25, -7), ("saw", 49, 0.18, 0.25, -7)],
    "death": [("triangle", n, 0.15, 0.3, 0) for n in (72, 69, 65, 62, 57, 48)],
    "stomp": [("triangle", 55, 0.09, 0.4, -19)],
    "kick": [("square", 62, 0.07, 0.25, 10), ("noise", 0, 0.06, 0.2, 0)],
    "shot": [("square", 77, 0.08, 0.18, -20)],
    "checkpoint": [("bell", n, 0.085, 0.25, 0) for n in (72, 76, 79, 84)],
    "secret": [("bell", n, 0.095, 0.22, 0) for n in (74, 77, 81, 86, 89)],
    "complete": [("square", n, 0.12, 0.2, 0) for n in (72, 76, 79, 84, 79, 84, 88, 91)],
    "boss": [("saw", n, 0.14, 0.3, 0) for n in (40, 39, 38, 36)],
    "life": [("bell", n, 0.09, 0.25, 0) for n in (79, 84, 88, 91)],
    "spring": [("sine", 55, 0.22, 0.4, 24)],
    "swim": [("sine", 67, 0.1, 0.18, 7)],
    "crash": [("noise", 0, 0.35, 0.45, 0), ("sine", 33, 0.3, 0.5, -10)],
    "crumble": [("noise", 0, 0.25, 0.25, 0)],
    "land": [("sine", 40, 0.06, 0.25, -8)],
    "deflect": [("square", 84, 0.05, 0.15, -12)],
    "charge": [("saw", 45, 0.25, 0.25, 12)],
    "boss_intro": [("saw", n, 0.2, 0.3, 0) for n in (36, 43, 48, 47)],
    "wings_lost": [("triangle", 70, 0.08, 0.25, -12)],
    "collapse": [("noise", 0, 0.2, 0.3, 0)],
    "warp": [("sine", 60, 0.3, 0.3, -12)],
    "enemy_jump": [("triangle", 52, 0.08, 0.12, 8)],
    "splash": [("noise", 0, 0.25, 0.2, 0)],
}


def render_sfx(name: str):
    parts = SFX.get(name)
    if not parts:
        return None
    chunks = []
    for kind, midi, dur, vol, slide in parts:
        if kind == "noise":
            chunks.append(_noise(dur, vol, dur / 3, seed=hash(name) % 1000))
        else:
            chunks.append(_note(kind, midi, dur, vol, slide))
    data = np.concatenate(chunks)
    data = np.tanh(data * 1.4) * 0.8
    stereo = np.stack([data, data], axis=1)
    return (stereo * 32767).astype(np.int16)


class AudioSystem:
    """Two volume buses (music, effects); silently disabled if no device."""

    def __init__(self, music: float = 0.45, sfx: float = 0.75) -> None:
        self.music_volume, self.sfx_volume = music, sfx
        self.enabled = False
        self.current: Optional[str] = None
        self.sounds: dict[str, object] = {}
        self.tracks: dict[str, object] = {}
        self.channel = None
        self.paused = False
        if np is None:
            return
        try:
            import pygame

            if not pygame.mixer.get_init():
                pygame.mixer.init(RATE, -16, 2, 512)
            pygame.mixer.set_num_channels(24)
            self.pygame = pygame
            self.channel = pygame.mixer.Channel(0)
            pygame.mixer.set_reserved(1)
            self.enabled = True
        except Exception:
            self.enabled = False

    def set_volumes(self, music: float, sfx: float) -> None:
        self.music_volume, self.sfx_volume = max(0.0, min(1.0, music)), max(0.0, min(1.0, sfx))
        if self.channel is not None:
            self.channel.set_volume(self.music_volume)

    def play_music(self, track_id: str) -> None:
        if not self.enabled or track_id == self.current:
            return
        self.current = track_id
        snd = self.tracks.get(track_id)
        if snd is None:
            snd = self.pygame.sndarray.make_sound(render_track(track_for(track_id)))
            self.tracks[track_id] = snd
        self.channel.play(snd, loops=-1, fade_ms=400)
        self.channel.set_volume(self.music_volume)

    def pause(self, paused: bool) -> None:
        if not self.enabled or paused == self.paused:
            return
        self.paused = paused
        if paused:
            self.channel.pause()
        else:
            self.channel.unpause()

    def effect(self, name: str) -> None:
        if not self.enabled or self.sfx_volume <= 0:
            return
        snd = self.sounds.get(name)
        if snd is None:
            data = render_sfx(name)
            if data is None:
                return
            snd = self.pygame.sndarray.make_sound(data)
            self.sounds[name] = snd
        snd.set_volume(self.sfx_volume)
        snd.play()

    def stop(self) -> None:
        if self.enabled:
            self.channel.stop()
            self.current = None
