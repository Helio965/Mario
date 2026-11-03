"""Síntese procedural com numpy (sem pygame): ondas, envelopes, trilhas, cues, vozes e ambientes.

Port nota a nota das tabelas de ``src/systems/audio.ts``: seis trilhas de 32
passos, a trilha de chefe e os 14 cues. Tudo aqui é Python puro + numpy, para
que a síntese possa ser testada e exportada (``tools/render_audio.py``) sem
mixer. A conversão para ``pygame.mixer.Sound`` fica em ``audio.py``.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Final, Literal

import numpy as np
from numpy.typing import NDArray

SAMPLE_RATE: Final = 44100
Waveform = Literal["square", "triangle", "sawtooth", "sine"]
FloatArray = NDArray[np.float64]

# Níveis do mix original (Web Audio). MASTER_GAIN levanta música e efeitos juntos
# (o original era muito baixo) preservando o equilíbrio relativo entre eles. O valor
# deixa folga para a soma do SDL_mixer, que satura: com os volumes padrão (música 0,45,
# efeitos 0,75, voz 0,8, ambiente 0,6×0,6), música + ambiente + um cue + uma voz com
# picos alinhados ficam abaixo de 1,0 (medido em ``tests/integration/test_audio.py``).
MELODY_LEVEL: Final = 0.058
BASS_LEVEL: Final = 0.13
HARMONY_LEVEL: Final = 0.045
HAT_LEVEL: Final = 0.07
CUE_LEVEL: Final = 0.12
MASTER_GAIN: Final = 2.4
ENVELOPE_FLOOR: Final = 0.001
EDGE_FADE_SECONDS: Final = 0.002


# ------------------------------------------------------------------ dados
@dataclass(frozen=True, slots=True)
class Track:
    """Tema de 32 passos: ``melody`` em MIDI (0 = pausa), ``bass`` por trecho de 8 passos."""

    name: str
    bpm: int
    color: Waveform
    third: int
    melody: tuple[int, ...]
    bass: tuple[int, ...]

    @property
    def step_duration(self) -> float:
        return 60 / self.bpm / 4

    @property
    def loop_duration(self) -> float:
        return self.step_duration * len(self.melody)


TRACKS: Final[tuple[Track, ...]] = (
    Track(
        name="menu",
        bpm=106,
        color="triangle",
        third=4,
        melody=(
            *(72, 0, 76, 79, 0, 76, 74, 0, 72, 76, 79, 84, 0, 79, 76, 0),
            *(74, 0, 77, 81, 0, 79, 77, 74, 76, 79, 84, 0, 79, 76, 74, 0),
        ),
        bass=(48, 53, 50, 55),
    ),
    Track(
        name="world-1",
        bpm=136,
        color="square",
        third=4,
        melody=(
            *(72, 76, 79, 0, 81, 79, 76, 74, 72, 0, 76, 79, 84, 0, 79, 76),
            *(77, 81, 84, 0, 86, 84, 81, 79, 76, 0, 79, 83, 86, 83, 79, 0),
        ),
        bass=(48, 45, 53, 55),
    ),
    Track(
        name="world-2",
        bpm=118,
        color="triangle",
        third=3,
        melody=(
            *(69, 0, 72, 76, 0, 77, 76, 72, 71, 0, 74, 77, 80, 0, 77, 74),
            *(72, 76, 81, 0, 79, 76, 72, 0, 71, 74, 76, 80, 0, 76, 71, 0),
        ),
        bass=(45, 50, 53, 52),
    ),
    Track(
        name="world-3",
        bpm=112,
        color="triangle",
        third=4,
        melody=(
            *(74, 0, 78, 81, 85, 0, 81, 78, 76, 0, 81, 83, 86, 0, 83, 81),
            *(78, 81, 85, 88, 0, 85, 81, 78, 76, 78, 81, 85, 0, 81, 78, 0),
        ),
        bass=(50, 57, 55, 52),
    ),
    Track(
        name="world-4",
        bpm=124,
        color="square",
        third=3,
        melody=(
            *(71, 74, 78, 0, 81, 78, 74, 0, 73, 76, 80, 0, 83, 80, 76, 0),
            *(74, 78, 81, 85, 0, 81, 78, 74, 73, 76, 80, 83, 0, 80, 76, 0),
        ),
        bass=(47, 52, 50, 54),
    ),
    Track(
        name="world-5",
        bpm=144,
        color="sawtooth",
        third=3,
        melody=(
            *(69, 0, 69, 72, 76, 0, 75, 72, 69, 0, 72, 75, 78, 0, 76, 75),
            *(68, 0, 71, 74, 77, 0, 74, 71, 68, 71, 74, 77, 80, 77, 74, 0),
        ),
        bass=(45, 41, 44, 40),
    ),
)

BOSS_TRACK: Final = Track(
    name="boss",
    bpm=164,
    color="sawtooth",
    third=3,
    melody=(
        *(57, 69, 57, 72, 57, 69, 75, 72, 56, 68, 56, 71, 56, 68, 74, 71),
        *(53, 65, 53, 68, 53, 65, 71, 68, 52, 64, 52, 67, 52, 64, 70, 67),
    ),
    bass=(33, 32, 29, 28),
)

ALL_TRACKS: Final[tuple[Track, ...]] = (*TRACKS, BOSS_TRACK)
TRACKS_BY_NAME: Final[dict[str, Track]] = {track.name: track for track in ALL_TRACKS}


@dataclass(frozen=True, slots=True)
class Cue:
    """Efeito sonoro: sequência de notas MIDI, uma a cada ``duration`` segundos.

    ``gain`` multiplica ``CUE_LEVEL`` (1,0 nos 14 cues portados do original).
    """

    notes: tuple[int, ...]
    duration: float
    wave: Waveform = "square"
    slide: float = 0.0
    gain: float = 1.0

    @property
    def total_duration(self) -> float:
        return self.duration * len(self.notes)


CUES: Final[dict[str, Cue]] = {
    "jump": Cue(notes=(65,), duration=0.13, slide=14),
    "coin": Cue(notes=(91, 98), duration=0.055),
    "relic": Cue(notes=(76, 83, 88, 95), duration=0.1, wave="triangle"),
    "block": Cue(notes=(48,), duration=0.07, slide=-12, wave="triangle"),
    "power": Cue(notes=(60, 64, 67, 72, 76, 79), duration=0.07),
    "hurt": Cue(notes=(55, 49), duration=0.13, slide=-7, wave="sawtooth"),
    "death": Cue(notes=(72, 69, 65, 62, 57, 48), duration=0.15, wave="triangle"),
    "stomp": Cue(notes=(55,), duration=0.085, slide=-19, wave="triangle"),
    "shot": Cue(notes=(77,), duration=0.08, slide=-20),
    "checkpoint": Cue(notes=(72, 76, 79, 84), duration=0.085, wave="triangle"),
    "secret": Cue(notes=(74, 77, 81, 86, 89), duration=0.095, wave="triangle"),
    "complete": Cue(notes=(72, 76, 79, 84, 79, 84, 88, 91), duration=0.12),
    "boss": Cue(notes=(40, 39, 38, 36), duration=0.14, wave="sawtooth"),
    "life": Cue(notes=(79, 84, 88, 91), duration=0.09),
    # Eventos novos do motor Python (chefes com fases, NPCs e diálogos) — timbres originais.
    # Os blips de fala são mais discretos (gain) para não cobrir a voz nem a música.
    "boss_intro": Cue(notes=(36, 43, 48), duration=0.18, slide=-5, wave="sawtooth"),
    "boss_phase": Cue(notes=(50, 57, 62, 69), duration=0.1, slide=6),
    "talk": Cue(notes=(84, 91), duration=0.05, wave="triangle", gain=0.7),
    "npc_say": Cue(notes=(88,), duration=0.08, slide=9, wave="triangle", gain=0.7),
}
PORTED_CUE_NAMES: Final[tuple[str, ...]] = tuple(CUES)[:14]  # os 14 de ``audio.ts``


# ------------------------------------------------------------- utilidades
def clamp01(value: float) -> float:
    """``volume()`` do original: NaN/inf viram 0; demais valores ficam em [0, 1]."""
    return max(0.0, min(1.0, value)) if math.isfinite(value) else 0.0


def midi_to_hz(midi: float) -> float:
    return 440.0 * 2 ** ((midi - 69) / 12)


def frequency_ramp(start_hz: float, end_hz: float, samples: int) -> FloatArray:
    """Rampa exponencial de frequência (portamento), uma amostra por ponto.

    Com uma das pontas em zero (ou negativa) a rampa exponencial não existe; cai
    para linear em vez de dividir por zero.
    """
    if samples <= 0:
        return np.zeros(0)
    if end_hz == start_hz:
        return np.full(samples, start_hz)
    if start_hz <= 0.0 or end_hz <= 0.0:
        return np.linspace(start_hz, end_hz, samples, endpoint=False)
    return start_hz * (end_hz / start_hz) ** (np.arange(samples) / samples)


def _poly_blep(t: FloatArray, dt: FloatArray) -> FloatArray:
    """Correção PolyBLEP de 2 pontos para suavizar descontinuidades (menos aliasing)."""
    out = np.zeros_like(t)
    start = t < dt
    if np.any(start):
        x = t[start] / dt[start]
        out[start] = x + x - x * x - 1.0
    end = t > 1.0 - dt
    if np.any(end):
        x = (t[end] - 1.0) / dt[end]
        out[end] = x * x + x + x + 1.0
    return out


def oscillator(frequency: FloatArray, wave: Waveform, sample_rate: int = SAMPLE_RATE) -> FloatArray:
    """Oscilador com frequência por amostra; fase começa em zero (sem clique inicial)."""
    increment = frequency / sample_rate
    phase = np.cumsum(increment) - increment
    t = np.mod(phase, 1.0)
    if wave == "sine":
        return np.sin(2 * np.pi * phase)
    if wave == "triangle":
        return 1.0 - 4.0 * np.abs(np.mod(t + 0.25, 1.0) - 0.5)
    if wave == "sawtooth":
        return (2.0 * t - 1.0) - _poly_blep(t, increment)
    square: FloatArray = np.where(t < 0.5, 1.0, -1.0)
    return square + _poly_blep(t, increment) - _poly_blep(np.mod(t + 0.5, 1.0), increment)


def envelope_ad(
    samples: int, attack: float, loudness: float, sample_rate: int = SAMPLE_RATE
) -> FloatArray:
    """Ataque linear até ``loudness`` e decaimento exponencial até 0,001 (como no original).

    Termina com um fade curto até zero exato para não deixar degrau na borda.
    ``loudness <= 0`` é silêncio (o decaimento exponencial exige nível positivo).
    """
    if samples <= 0:
        return np.zeros(0)
    if loudness <= 0.0:
        return np.zeros(samples)
    attack_samples = min(samples, max(1, round(attack * sample_rate)))
    env = np.empty(samples)
    env[:attack_samples] = np.linspace(0.0, 1.0, attack_samples, endpoint=False) * loudness
    decay_samples = samples - attack_samples
    if decay_samples > 0:
        floor = min(ENVELOPE_FLOOR, loudness * 0.5)
        env[attack_samples:] = loudness * np.exp(
            np.linspace(0.0, math.log(floor / loudness), decay_samples)
        )
    fade = min(samples, max(1, round(EDGE_FADE_SECONDS * sample_rate)))
    env[samples - fade :] *= np.linspace(1.0, 0.0, fade, endpoint=False)
    return env


def adsr(
    samples: int,
    attack: float,
    decay: float,
    sustain: float,
    release: float,
    sample_rate: int = SAMPLE_RATE,
) -> FloatArray:
    """Envelope ADSR linear simples ocupando exatamente ``samples`` amostras."""
    if samples <= 0:
        return np.zeros(0)
    a = max(1, round(attack * sample_rate))
    d = max(0, round(decay * sample_rate))
    r = max(1, round(release * sample_rate))
    total = a + d + r
    if total > samples:  # encurta proporcionalmente quando o som é mais curto que o envelope
        scale = samples / total
        a = min(samples, max(1, int(a * scale)))
        d = min(samples - a, int(d * scale))
        r = samples - a - d  # pode ser 0 em sons de uma ou duas amostras
    s = max(0, samples - a - d - r)
    parts = [
        np.linspace(0.0, 1.0, a, endpoint=False),
        np.linspace(1.0, sustain, d, endpoint=False),
        np.full(s, sustain),
        np.linspace(sustain, 0.0, r, endpoint=False),
    ]
    env: FloatArray = np.concatenate(parts)
    return env[:samples]


def tone(
    midi: float,
    duration: float,
    wave: Waveform = "square",
    loudness: float = 1.0,
    slide: float = 0.0,
    sample_rate: int = SAMPLE_RATE,
) -> FloatArray:
    """Nota única: ``slide`` em semitons é um portamento exponencial até o fim da nota."""
    samples = max(1, round(duration * sample_rate))
    frequency = frequency_ramp(midi_to_hz(midi), midi_to_hz(midi + slide), samples)
    signal = oscillator(frequency, wave, sample_rate)
    attack = min(0.008, duration / 4)
    return signal * envelope_ad(samples, attack, loudness, sample_rate)


def mix_at(target: FloatArray, source: FloatArray, start: int, wrap: bool = True) -> None:
    """Soma ``source`` em ``target`` a partir de ``start``; com ``wrap`` o excesso volta ao início."""
    size = len(target)
    if size == 0 or len(source) == 0:
        return
    index = start % size if wrap else max(0, start)
    if index >= size:
        return
    end = index + len(source)
    if end <= size:
        target[index:end] += source
        return
    first = size - index
    target[index:] += source[:first]
    if not wrap:
        return
    rest = source[first:]
    while len(rest) > 0:
        chunk = min(size, len(rest))
        target[:chunk] += rest[:chunk]
        rest = rest[chunk:]


def peak(signal: FloatArray) -> float:
    return float(np.max(np.abs(signal))) if len(signal) else 0.0


def rms(signal: FloatArray) -> float:
    return float(np.sqrt(np.mean(np.square(signal)))) if len(signal) else 0.0


def normalize(signal: FloatArray, target_peak: float) -> FloatArray:
    current = peak(signal)
    return signal * (target_peak / current) if current > 0 else signal


# ------------------------------------------------------------------ música
def render_track(track: Track, sample_rate: int = SAMPLE_RATE) -> FloatArray:
    """Um loop completo (32 passos) com o agendador do original.

    Melodia em todo passo; baixo a cada 4 passos (duração 2,4×); harmonia nos
    passos ímpares (terça em ``%4==1``, quinta nos demais, +12); "hat" (nota 34
    com slide −14, 35 ms) no passo ``%4==2``. Notas que passam do fim voltam ao
    início, por isso o loop é contínuo.
    """
    step = track.step_duration
    samples = round(track.loop_duration * sample_rate)
    out = np.zeros(samples)
    for position, note in enumerate(track.melody):
        when = round(position * step * sample_rate)
        root = track.bass[(position // 8) % len(track.bass)]
        if note:
            mix_at(out, tone(note, step * 0.83, track.color, MELODY_LEVEL, 0.0, sample_rate), when)
        if position % 4 == 0:
            mix_at(out, tone(root, step * 2.4, "triangle", BASS_LEVEL, 0.0, sample_rate), when)
        if position % 2 == 1:
            interval = track.third if position % 4 == 1 else 7
            harmony = tone(
                root + 12 + interval, step * 0.72, "triangle", HARMONY_LEVEL, 0.0, sample_rate
            )
            mix_at(out, harmony, when)
        if position % 4 == 2:
            mix_at(out, tone(34, 0.035, "triangle", HAT_LEVEL, -14, sample_rate), when)
    return out * MASTER_GAIN


def render_cue(cue: Cue, sample_rate: int = SAMPLE_RATE) -> FloatArray:
    """Efeito: notas em sequência, cada uma soando 95% do intervalo (como no original)."""
    samples = max(1, round(cue.total_duration * sample_rate))
    out = np.zeros(samples)
    for index, note in enumerate(cue.notes):
        start = round(index * cue.duration * sample_rate)
        mix_at(
            out,
            tone(note, cue.duration * 0.95, cue.wave, CUE_LEVEL, cue.slide, sample_rate),
            start,
            wrap=False,
        )
    return out * (MASTER_GAIN * cue.gain)


# ------------------------------------------------------------------- vozes
# Formantes (F1, F2, F3) aproximados de vogais; a escala torna a "criatura" pequena.
VOWELS: Final[dict[str, tuple[float, float, float]]] = {
    "a": (730.0, 1090.0, 2440.0),
    "e": (530.0, 1840.0, 2480.0),
    "i": (270.0, 2290.0, 3010.0),
    "o": (570.0, 840.0, 2410.0),
    "u": (300.0, 870.0, 2240.0),
    "x": (500.0, 1500.0, 2500.0),  # vogal neutra
}
FORMANT_SCALE: Final = 1.2
FORMANT_LEVELS: Final = (1.0, 0.65, 0.3)
FORMANT_GRID_STEP: Final = 64


@dataclass(frozen=True, slots=True)
class VoiceSpec:
    """Vocalização original: contorno de altura (Hz), trajeto de vogais e sílabas."""

    duration: float
    pitch: tuple[float, ...]
    vowels: tuple[str, ...]
    syllables: int = 1
    vibrato: float = 0.0
    breath: float = 0.02
    brightness: float = 0.6
    loudness: float = 0.42  # pico; ver a folga de mix em MASTER_GAIN
    seed: int = 1


VOICES: Final[dict[str, VoiceSpec]] = {
    "jump": VoiceSpec(0.16, (330.0, 420.0, 640.0), ("u", "a"), brightness=0.7, seed=11),
    "hurt": VoiceSpec(
        0.28, (480.0, 300.0, 230.0), ("a", "u"), breath=0.07, brightness=0.5, seed=12
    ),
    "victory": VoiceSpec(0.55, (330.0, 440.0, 550.0, 660.0), ("i", "a", "e"), 2, 0.02, seed=13),
    "defeat": VoiceSpec(0.7, (380.0, 330.0, 250.0, 200.0), ("o", "o", "u"), 2, 0.015, seed=14),
    "hello": VoiceSpec(0.42, (330.0, 420.0, 380.0), ("e", "o"), 2, 0.01, seed=15),
    "surprise": VoiceSpec(0.3, (300.0, 340.0, 650.0), ("a", "x"), brightness=0.65, seed=16),
}
VOICE_NAMES: Final[tuple[str, ...]] = tuple(VOICES)


def _interp_log(u: FloatArray, values: tuple[float, ...]) -> FloatArray:
    knots = np.linspace(0.0, 1.0, len(values))
    return np.exp(np.interp(u, knots, np.log(np.asarray(values))))


def render_voice(spec: VoiceSpec, sample_rate: int = SAMPLE_RATE) -> FloatArray:
    """Síntese por formantes aditivos: harmônicos de f0 ponderados por três ressonâncias."""
    samples = max(1, round(spec.duration * sample_rate))
    rng = np.random.default_rng(spec.seed)
    t = np.arange(samples) / sample_rate
    u = t / spec.duration
    f0 = _interp_log(u, spec.pitch)
    f0 = f0 * (1.0 + 0.012 * np.sin(2 * np.pi * 1.7 * t + 0.4))  # leve instabilidade natural
    if spec.vibrato:
        f0 = f0 * (1.0 + spec.vibrato * np.sin(2 * np.pi * 5.5 * t))
    phase = np.cumsum(f0) / sample_rate
    harmonics = int(max(1, min(48, (sample_rate * 0.45) // float(np.max(f0)))))
    k = np.arange(1, harmonics + 1, dtype=np.float64)[:, None]
    # Os formantes variam devagar: a ponderação é calculada numa grade decimada e expandida.
    grid = u[::FORMANT_GRID_STEP]
    freqs = k * f0[None, ::FORMANT_GRID_STEP]
    amp = np.zeros_like(freqs)
    for index, level in enumerate(FORMANT_LEVELS):
        centers = _interp_log(grid, tuple(VOWELS[v][index] * FORMANT_SCALE for v in spec.vowels))
        bandwidth = centers * 0.12 + 40.0
        amp += level / (1.0 + np.square((freqs - centers[None, :]) / bandwidth[None, :]))
    amp *= k ** (-spec.brightness)
    amp = np.repeat(amp, FORMANT_GRID_STEP, axis=1)[:, :samples]
    offsets = rng.uniform(0.0, 2 * np.pi, harmonics)[:, None]
    wave = np.sum(amp * np.sin(2 * np.pi * k * phase[None, :] + offsets), axis=0)
    wave = normalize(wave, 1.0)
    wave += rng.standard_normal(samples) * spec.breath
    env = adsr(samples, 0.012, 0.05, 0.8, min(0.08, spec.duration * 0.3), sample_rate)
    if spec.syllables > 1:
        hump = 0.5 - 0.5 * np.cos(2 * np.pi * spec.syllables * u)
        env *= 0.15 + 0.85 * hump
    return normalize(wave * env, spec.loudness)


# ---------------------------------------------------------------- ambiente
AMBIENT_NAMES: Final[tuple[str, ...]] = ("wind", "sand", "snow", "forest", "lava")
AMBIENT_ALIASES: Final[dict[str, str]] = {
    "world-1": "wind",
    "world-2": "sand",
    "world-3": "snow",
    "world-4": "forest",
    "world-5": "lava",
    "none": "wind",
    "spores": "forest",
    "embers": "lava",
}
AMBIENT_SECONDS: Final = 8.0
AMBIENT_PEAK: Final = 0.4  # pico do loop; o barramento ainda aplica AMBIENT_LEVEL


def resolve_ambient(name: str | None) -> str | None:
    if name is None:
        return None
    key = name.strip().lower()
    if key in AMBIENT_NAMES:
        return key
    return AMBIENT_ALIASES.get(key)


def _shaped_noise(
    samples: int,
    sample_rate: int,
    rng: np.random.Generator,
    shape: Callable[[FloatArray], FloatArray],
) -> FloatArray:
    """Ruído com envelope espectral; a filtragem por FFT é circular, logo o loop é contínuo."""
    spectrum = np.fft.rfft(rng.standard_normal(samples))
    freqs = np.fft.rfftfreq(samples, 1.0 / sample_rate)
    spectrum *= shape(freqs)
    noise: FloatArray = np.fft.irfft(spectrum, samples)
    return normalize(noise, 1.0)


def _lfo(samples: int, cycles: int, phase: float = 0.0) -> FloatArray:
    """Senoide com número inteiro de ciclos: fecha exatamente no fim do loop."""
    return np.sin(2 * np.pi * cycles * np.arange(samples) / samples + phase)


def _bandpass(center: float, width: float, tilt: float = 0.0) -> Callable[[FloatArray], FloatArray]:
    def shape(freqs: FloatArray) -> FloatArray:
        gain = 1.0 / (1.0 + np.square((freqs - center) / width))
        return gain * np.power(np.maximum(freqs, 20.0) / center, -tilt)

    return shape


def _lowpass(cutoff: float, order: float = 2.0) -> Callable[[FloatArray], FloatArray]:
    def shape(freqs: FloatArray) -> FloatArray:
        return 1.0 / (1.0 + np.power(freqs / cutoff, 2 * order))

    return shape


def _highpass(cutoff: float, order: float = 2.0) -> Callable[[FloatArray], FloatArray]:
    def shape(freqs: FloatArray) -> FloatArray:
        ratio = np.power(np.maximum(freqs, 1e-6) / cutoff, 2 * order)
        return ratio / (1.0 + ratio)

    return shape


def _blip(
    start_hz: float,
    end_hz: float,
    duration: float,
    sample_rate: int,
    wave: Waveform = "sine",
) -> FloatArray:
    samples = max(1, round(duration * sample_rate))
    signal = oscillator(frequency_ramp(start_hz, end_hz, samples), wave, sample_rate)
    return signal * adsr(samples, 0.004, 0.0, 1.0, duration * 0.6, sample_rate)


def _scatter(
    out: FloatArray, rng: np.random.Generator, count: int, make: Callable[[], FloatArray]
) -> None:
    """Espalha eventos curtos em posições aleatórias do loop (com wrap)."""
    for _ in range(count):
        mix_at(out, make(), int(rng.integers(0, len(out))))


def render_ambient(
    name: str, sample_rate: int = SAMPLE_RATE, seconds: float = AMBIENT_SECONDS
) -> FloatArray:
    """Loop ambiente suave por mundo: vento, areia, neve, floresta noturna ou lava."""
    key = resolve_ambient(name)
    if key is None:
        msg = f"ambiente desconhecido: {name!r}"
        raise KeyError(msg)
    samples = max(1, round(seconds * sample_rate))
    rng = np.random.default_rng(AMBIENT_NAMES.index(key) + 101)
    out = np.zeros(samples)
    if key == "wind":
        gusts = 0.65 + 0.35 * _lfo(samples, 3) * (0.6 + 0.4 * _lfo(samples, 7, 1.0))
        out += _shaped_noise(samples, sample_rate, rng, _bandpass(420.0, 500.0, 0.4)) * gusts
        out += _shaped_noise(samples, sample_rate, rng, _lowpass(140.0)) * 0.5

        def chirp() -> FloatArray:
            return _blip(3200.0, 3900.0, 0.06, sample_rate) * 0.12

        _scatter(out, rng, 3, chirp)
    elif key == "sand":
        gusts = 0.55 + 0.45 * _lfo(samples, 5) * (0.5 + 0.5 * _lfo(samples, 11, 2.0))
        out += _shaped_noise(samples, sample_rate, rng, _bandpass(2600.0, 2200.0, 0.2)) * gusts
        out += _shaped_noise(samples, sample_rate, rng, _bandpass(350.0, 400.0)) * 0.6
    elif key == "snow":
        drift = 0.7 + 0.3 * _lfo(samples, 2, 0.5)
        out += _shaped_noise(samples, sample_rate, rng, _highpass(1500.0, 1.5)) * 0.45 * drift
        out += _shaped_noise(samples, sample_rate, rng, _bandpass(220.0, 160.0)) * 0.5 * drift

        def sparkle() -> FloatArray:
            return _blip(7000.0 + float(rng.uniform(0, 2000)), 6500.0, 0.03, sample_rate) * 0.1

        _scatter(out, rng, 5, sparkle)
    elif key == "forest":
        out += _shaped_noise(samples, sample_rate, rng, _lowpass(180.0)) * 0.55
        for tone_hz, rate, cycles, phase in ((4200.0, 6.0, 2, 0.0), (3600.0, 4.5, 3, 2.1)):
            pulses = np.clip(_lfo(samples, round(rate * seconds)) * 4.0, 0.0, 1.0)
            train = np.clip(_lfo(samples, cycles, phase) * 3.0, 0.0, 1.0)
            cricket = oscillator(np.full(samples, tone_hz), "sine", sample_rate) * pulses * train
            out += cricket * 0.12

        def owl() -> FloatArray:
            return _blip(330.0, 310.0, 0.32, sample_rate) * 0.2

        _scatter(out, rng, 2, owl)
    else:  # lava
        swell = 0.75 + 0.25 * _lfo(samples, 2)
        out += _shaped_noise(samples, sample_rate, rng, _lowpass(120.0, 1.5)) * swell
        out += _shaped_noise(samples, sample_rate, rng, _bandpass(900.0, 700.0)) * 0.12

        def bloop() -> FloatArray:
            return _blip(300.0 + float(rng.uniform(-80, 80)), 110.0, 0.12, sample_rate) * 0.35

        def crackle() -> FloatArray:
            return _blip(1800.0, 600.0, 0.012, sample_rate, "triangle") * 0.2

        _scatter(out, rng, 10, bloop)
        _scatter(out, rng, 24, crackle)
    return normalize(out, AMBIENT_PEAK)


# -------------------------------------------------------------- conversão
def to_stereo_int16(mono: FloatArray) -> NDArray[np.int16]:
    """Converte mono em [-1, 1] para ``(n, 2)`` int16 contíguo, com clip de segurança."""
    return to_mixer_array(mono, -16, 2).astype(np.int16, copy=False)


def to_mixer_array(mono: FloatArray, size: int, channels: int) -> NDArray[Any]:
    """Ajusta o sinal ao formato do mixer: ``size`` (-16, 16, -8, 8, 32) e número de canais."""
    clipped = np.clip(mono, -1.0, 1.0)
    data: NDArray[Any]
    if size == -16:
        data = (clipped * 32767.0).astype(np.int16)
    elif size == 16:
        data = (clipped * 32767.0 + 32768.0).astype(np.uint16)
    elif size == -8:
        data = (clipped * 127.0).astype(np.int8)
    elif size == 8:
        data = (clipped * 127.0 + 128.0).astype(np.uint8)
    else:
        data = clipped.astype(np.float32)
    if channels <= 1:
        return np.ascontiguousarray(data)
    return np.ascontiguousarray(np.repeat(data[:, None], channels, axis=1))
