"""Áudio sintetizado com o driver ``dummy`` (nunca abre dispositivo real)."""

from __future__ import annotations

import os
from collections.abc import Iterator

import numpy as np
import pygame
import pytest

from game.core.types import EVENT_TYPES
from game.systems import synth
from game.systems.audio import (
    AMBIENT_CHANNELS,
    MAX_INSTANCES_PER_EFFECT,
    MUSIC_CHANNELS,
    RESERVED_CHANNELS,
    SFX_CHANNELS,
    VOICE_CHANNELS,
    AudioSystem,
)

SR = synth.SAMPLE_RATE


@pytest.fixture
def audio() -> Iterator[AudioSystem]:
    system = AudioSystem(background=False)
    yield system
    system.dispose()


def settle(system: AudioSystem, seconds: float = 1.0, dt: float = 1 / 60) -> None:
    """Avança o sistema em quadros de 1/60 s, como o laço do jogo faria."""
    steps = round(seconds / dt)
    for _ in range(steps):
        system.update(dt)


# ------------------------------------------------------------------- síntese
def test_dummy_driver_is_active_and_init_does_not_raise(audio: AudioSystem) -> None:
    assert os.environ.get("SDL_AUDIODRIVER") == "dummy"
    assert audio.available is True
    assert pygame.mixer.get_init() is not None
    assert pygame.mixer.get_num_channels() >= RESERVED_CHANNELS
    assert MUSIC_CHANNELS + SFX_CHANNELS + VOICE_CHANNELS + AMBIENT_CHANNELS == RESERVED_CHANNELS
    assert len(audio.bus_channels("music")) == 2
    assert len(audio.bus_channels("sfx")) == 8
    assert len(audio.bus_channels("voice")) == 2
    assert len(audio.bus_channels("ambient")) == 2


def test_tone_has_expected_size_envelope_and_no_clipping() -> None:
    signal = synth.tone(69, 0.25, "square", 0.8)
    assert len(signal) == round(0.25 * SR)
    assert synth.peak(signal) > 0.5
    assert synth.peak(signal) <= 1.0
    assert signal[0] == 0.0  # ataque começa em zero
    assert abs(signal[-1]) < 1e-3  # borda final suavizada
    attack_end = round(0.008 * SR)
    assert synth.peak(signal[: attack_end // 2]) < synth.peak(signal[attack_end : attack_end * 3])
    # decaimento exponencial: a segunda metade é bem mais baixa que a primeira
    assert synth.rms(signal[len(signal) // 2 :]) < 0.3 * synth.rms(signal[: len(signal) // 2])


@pytest.mark.parametrize("wave", ["square", "triangle", "sawtooth", "sine"])
def test_every_waveform_is_bounded_and_periodic(wave: str) -> None:
    frequency = np.full(SR // 10, 441.0)
    signal = synth.oscillator(frequency, wave)  # type: ignore[arg-type]
    assert signal.shape == (SR // 10,)
    assert synth.peak(signal) <= 1.0 + 1e-9
    assert synth.rms(signal) > 0.4
    period = SR // 441
    assert np.allclose(signal[period : 2 * period], signal[2 * period : 3 * period], atol=0.05)


def test_portamento_slides_exponentially_by_semitones() -> None:
    signal = synth.tone(69, 1.0, "sine", 1.0, slide=12)

    def crossings(segment: np.ndarray) -> int:
        return int(np.sum((segment[:-1] < 0) & (segment[1:] >= 0)))

    first = crossings(signal[: SR // 10])
    last = crossings(signal[-SR // 10 :])
    assert 40 <= first <= 48  # ~440 Hz no início
    assert 80 <= last <= 90  # ~880 Hz no fim (uma oitava acima)
    ramp = synth.frequency_ramp(100.0, 400.0, 4)
    assert np.allclose(ramp, [100.0, 100.0 * 4**0.25, 200.0, 100.0 * 4**0.75])


def test_adsr_shape() -> None:
    env = synth.adsr(1000, 0.001, 0.002, 0.5, 0.003, sample_rate=100_000)
    assert len(env) == 1000
    assert env[0] == 0.0
    assert env[100] == pytest.approx(1.0, abs=0.02)
    assert env[500] == pytest.approx(0.5)
    assert env[-1] < 0.01
    assert len(synth.adsr(10, 1.0, 1.0, 0.5, 1.0)) == 10


def test_synth_edge_cases_do_not_raise() -> None:
    # envelopes mais curtos que uma amostra por fase (sons minúsculos, taxas baixas)
    for samples in range(1, 12):
        assert len(synth.adsr(samples, 0.004, 0.0, 1.0, 0.0072)) == samples
        assert len(synth.adsr(samples, 0.001, 1.0, 0.5, 0.001)) == samples
    assert synth.adsr(1, 0.01, 0.01, 0.5, 0.01).tolist() == [0.0]
    # nível zero/negativo é silêncio, não divisão por zero no decaimento exponencial
    assert synth.peak(synth.tone(69, 0.1, loudness=0.0)) == 0.0
    assert synth.peak(synth.tone(69, 0.1, loudness=-1.0)) == 0.0
    assert synth.envelope_ad(0, 0.008, 0.5).size == 0
    # rampa exponencial com ponta em zero cai para linear
    assert synth.frequency_ramp(0.0, 100.0, 4).tolist() == [0.0, 25.0, 50.0, 75.0]
    assert np.all(np.isfinite(synth.frequency_ramp(100.0, 0.0, 4)))
    # taxas de amostragem alternativas do mixer continuam coerentes
    for sample_rate in (22050, 48000):
        loop = synth.render_track(synth.BOSS_TRACK, sample_rate)
        assert len(loop) == round(synth.BOSS_TRACK.loop_duration * sample_rate)
        assert len(synth.render_ambient("lava", sample_rate, 1.0)) == sample_rate
        assert synth.peak(synth.render_voice(synth.VOICES["jump"], sample_rate)) > 0.1


def test_mix_at_wraps_around_loop_boundary() -> None:
    target = np.zeros(10)
    synth.mix_at(target, np.ones(4), 8)
    assert target.tolist() == [1, 1, 0, 0, 0, 0, 0, 0, 1, 1]
    linear = np.zeros(10)
    synth.mix_at(linear, np.ones(4), 8, wrap=False)
    assert linear.tolist() == [0, 0, 0, 0, 0, 0, 0, 0, 1, 1]


def test_track_tables_match_original_and_render_full_loops() -> None:
    assert len(synth.TRACKS) == 6
    assert [track.bpm for track in synth.TRACKS] == [106, 136, 118, 112, 124, 144]
    assert [track.color for track in synth.TRACKS] == [
        "triangle",
        "square",
        "triangle",
        "triangle",
        "square",
        "sawtooth",
    ]
    assert synth.BOSS_TRACK.bpm == 164
    assert synth.BOSS_TRACK.bass == (33, 32, 29, 28)
    for track in synth.ALL_TRACKS:
        assert len(track.melody) == 32
        assert len(track.bass) == 4
        loop = synth.render_track(track)
        assert len(loop) == round(32 * (60 / track.bpm / 4) * SR)
        assert 0.3 < synth.peak(loop) < 1.0
        assert synth.rms(loop) > 0.03
        assert abs(loop[0]) < 0.05  # fronteira do loop sem degrau
        stereo = synth.to_stereo_int16(loop)
        assert stereo.shape == (len(loop), 2)
        assert stereo.dtype == np.int16
        assert stereo.flags["C_CONTIGUOUS"]
        assert np.array_equal(stereo[:, 0], stereo[:, 1])


def test_cues_cover_all_event_types() -> None:
    assert set(synth.CUES) == set(EVENT_TYPES)
    assert len(synth.CUES) == len(EVENT_TYPES)  # 14 cues originais + 4 dos eventos novos
    assert len(synth.PORTED_CUE_NAMES) == 14
    assert all(synth.CUES[name].gain == 1.0 for name in synth.PORTED_CUE_NAMES)
    assert synth.CUES["jump"].slide == 14
    assert synth.CUES["hurt"].wave == "sawtooth"
    assert synth.CUES["complete"].notes == (72, 76, 79, 84, 79, 84, 88, 91)
    for name, cue in synth.CUES.items():
        rendered = synth.render_cue(cue)
        assert len(rendered) == round(cue.total_duration * SR), name
        assert 0.1 < synth.peak(rendered) < 1.0, name
        assert synth.rms(rendered) > 0.02, name
    # blips de fala são mais discretos que os efeitos de jogo
    assert synth.peak(synth.render_cue(synth.CUES["talk"])) < synth.peak(
        synth.render_cue(synth.CUES["coin"])
    )


def test_default_mix_leaves_headroom_for_sdl_mixer_sum() -> None:
    """O SDL_mixer satura a soma dos canais: com os volumes padrão, música + ambiente +
    um efeito + uma voz com picos alinhados precisam caber em 1,0."""
    music = max(synth.peak(synth.render_track(track)) for track in synth.ALL_TRACKS) * 0.45
    cue = max(synth.peak(synth.render_cue(cue)) for cue in synth.CUES.values()) * 0.75
    voice = max(synth.peak(synth.render_voice(spec)) for spec in synth.VOICES.values()) * 0.8
    ambient = synth.AMBIENT_PEAK * 0.6 * 0.6
    assert music + ambient + cue + voice < 1.0
    assert music > 0.1 and cue > 0.1  # mas não a ponto de ficar inaudível


def test_voices_and_ambients_render_non_silent_without_clipping() -> None:
    assert set(synth.VOICES) == {"jump", "hurt", "victory", "defeat", "hello", "surprise"}
    for name, spec in synth.VOICES.items():
        rendered = synth.render_voice(spec)
        assert len(rendered) == round(spec.duration * SR), name
        assert synth.peak(rendered) == pytest.approx(spec.loudness, abs=1e-6)
        assert synth.rms(rendered) > 0.05, name
    for name in synth.AMBIENT_NAMES:
        loop = synth.render_ambient(name, seconds=2.0)
        assert len(loop) == 2 * SR
        assert synth.peak(loop) == pytest.approx(synth.AMBIENT_PEAK, abs=1e-6)
        assert synth.rms(loop) > 0.02, name
    assert synth.resolve_ambient("world-3") == "snow"
    assert synth.resolve_ambient(" LAVA ") == "lava"
    assert synth.resolve_ambient("unknown") is None
    assert synth.resolve_ambient(None) is None
    with pytest.raises(KeyError):
        synth.render_ambient("unknown")


def test_mixer_array_conversion_matches_requested_format() -> None:
    mono = np.linspace(-2.0, 2.0, 5)  # fora da faixa: deve ser recortado
    signed = synth.to_mixer_array(mono, -16, 2)
    assert signed.dtype == np.int16
    assert signed.shape == (5, 2)
    assert signed[0, 0] == -32767
    assert signed[-1, 1] == 32767
    assert synth.to_mixer_array(mono, 16, 1).dtype == np.uint16
    assert synth.to_mixer_array(mono, 16, 1).shape == (5,)
    assert synth.to_mixer_array(mono, -8, 2).dtype == np.int8
    assert synth.to_mixer_array(mono, 8, 2).dtype == np.uint8
    assert synth.to_mixer_array(mono, 32, 2).dtype == np.float32
    assert synth.clamp01(float("nan")) == 0.0
    assert synth.clamp01(7.0) == 1.0
    assert synth.midi_to_hz(69) == 440.0


# ---------------------------------------------------------------- AudioSystem
def test_cues_are_presynthesized_and_effects_play_on_sfx_bus(audio: AudioSystem) -> None:
    for kind in EVENT_TYPES:
        assert audio.has_sound("cue", kind), kind
    audio.effect("coin")
    assert audio.active_effects("coin") == 1
    assert any(channel.get_busy() for channel in audio.bus_channels("sfx"))
    assert not any(channel.get_busy() for channel in audio.bus_channels("music"))
    audio.effect("not-a-cue")  # ignorado em silêncio
    assert audio.active_effects() == 1
    # eventos novos do núcleo (chefe com fases, NPCs) também soam
    for kind in ("boss_intro", "boss_phase", "talk", "npc_say"):
        audio.effect(kind)
        assert audio.active_effects(kind) == 1, kind
    assert audio.active_effects() == 5


class _BrokenChannel:
    """Canal que falha ao ajustar volume: simula o mixer caindo durante o jogo."""

    def __init__(self, channel: pygame.mixer.Channel) -> None:
        self._channel = channel

    def set_volume(self, _volume: float) -> None:
        raise pygame.error("device lost")

    def __getattr__(self, name: str) -> object:
        return getattr(self._channel, name)


def test_loop_slot_is_released_when_channel_fails(audio: AudioSystem) -> None:
    audio.menu()
    settle(audio, 1.0)
    audio.set_world(4)  # crossfade em andamento nos dois canais
    assert audio.fading
    for slot in audio._music:
        slot.channel = _BrokenChannel(slot.channel)  # type: ignore[assignment]
    settle(audio, 1.0)  # set_volume falha → os dois slots são liberados, nada fica preso
    assert not audio.fading
    assert audio.music_weights == (0.0, 0.0)
    audio.set_world(2)  # a nova trilha também falha ao iniciar: liberada, sem exceção
    assert not audio.fading
    assert audio.music_weights == (0.0, 0.0)
    assert audio.track is not None
    assert audio.track.name == "world-2"
    audio.set_volumes(0.5, 0.5)  # ajustes de volume continuam inofensivos
    audio.pause(True)
    audio.pause(False)


def test_bus_volumes_are_independent(audio: AudioSystem) -> None:
    audio.menu()
    settle(audio, 1.0)
    audio.set_volumes(0.0, 0.75, 0.5, 0.25)
    assert audio.volumes == {"music": 0.0, "sfx": 0.75, "voice": 0.5, "ambient": 0.25}
    for channel in audio.bus_channels("music"):
        assert channel.get_volume() == 0.0
    audio.effect("jump")
    sfx = next(channel for channel in audio.bus_channels("sfx") if channel.get_busy())
    assert sfx.get_volume() == pytest.approx(0.75, abs=0.01)
    for channel in audio.bus_channels("voice"):
        assert channel.get_volume() == pytest.approx(0.5, abs=0.01)
    audio.set_volumes(1.0, 0.0)
    active = next(channel for channel in audio.bus_channels("music") if channel.get_busy())
    assert active.get_volume() == pytest.approx(1.0, abs=0.01)
    assert sfx.get_volume() == 0.0
    audio.set_volumes(float("nan"), 2.0)
    assert audio.volumes["music"] == 0.0
    assert audio.volumes["sfx"] == 1.0


def test_effect_instances_are_limited_per_kind_and_per_bus(audio: AudioSystem) -> None:
    for _ in range(MAX_INSTANCES_PER_EFFECT + 4):
        audio.effect("coin")
    assert audio.active_effects("coin") == MAX_INSTANCES_PER_EFFECT
    for kind in ("jump", "jump", "stomp", "stomp", "block", "block", "shot", "shot", "power"):
        audio.effect(kind)
    assert audio.active_effects() <= SFX_CHANNELS
    assert audio.active_effects("power") == 1
    # canais lotados: o efeito mais importante não é roubado por uma moeda
    for _ in range(SFX_CHANNELS):
        audio.effect("death")
    assert audio.active_effects("death") == MAX_INSTANCES_PER_EFFECT
    audio.effect("coin")
    assert audio.active_effects() <= SFX_CHANNELS
    assert audio.active_effects("death") == MAX_INSTANCES_PER_EFFECT  # morte não cede à moeda


def test_set_world_crossfades_between_two_music_channels(audio: AudioSystem) -> None:
    audio.menu()
    assert audio.track is not None
    assert audio.track.name == "menu"
    settle(audio, 1.0)
    assert audio.music_weights in ((1.0, 0.0), (0.0, 1.0))
    busy = [channel.get_busy() for channel in audio.bus_channels("music")]
    assert busy.count(True) == 1
    audio.set_world(2)
    assert audio.track.name == "world-2"
    assert all(channel.get_busy() for channel in audio.bus_channels("music"))
    settle(audio, 0.2)
    assert audio.fading
    weights = audio.music_weights
    assert sum(weights) == pytest.approx(1.0, abs=0.1)
    assert all(0.2 < weight < 0.8 for weight in weights)
    settle(audio, 0.5)
    assert not audio.fading
    assert [channel.get_busy() for channel in audio.bus_channels("music")].count(True) == 1
    audio.set_world(2)  # mesma trilha: nenhuma mudança
    assert not audio.fading
    audio.set_world(2, boss=True)
    assert audio.track.name == "boss"
    settle(audio, 0.1)
    audio.set_world(2, boss=False)  # volta antes do fim do fade: inverte a direção
    assert audio.track.name == "world-2"
    settle(audio, 1.0)
    assert [channel.get_busy() for channel in audio.bus_channels("music")].count(True) == 1
    audio.set_world(99)
    assert audio.track.name == "world-5"
    audio.set_world(-3)
    assert audio.track.name == "world-1"


def test_pause_and_resume_music_and_update_are_safe(audio: AudioSystem) -> None:
    audio.set_world(1)
    settle(audio, 1.0)
    audio.pause(True)
    assert audio.paused
    weights = audio.music_weights
    audio.set_world(3)
    settle(audio, 1.0)  # pausado: o fade não avança
    assert audio.music_weights == weights or audio.fading
    audio.pause(False)
    settle(audio, 1.0)
    assert not audio.fading
    audio.pause(False)  # idempotente
    audio.update(float("nan"))
    audio.update(-1.0)
    audio.update(0.0)
    audio.update(10.0)
    audio.effect("coin")  # efeitos seguem disponíveis com a música pausada
    audio.pause(True)
    audio.effect("coin")
    assert audio.active_effects("coin") >= 1


def test_voice_returns_caption_key_and_plays_on_voice_bus(audio: AudioSystem) -> None:
    assert audio.voice("jump") == "voice.jump"
    assert audio.active_voices() == 1
    assert any(channel.get_busy() for channel in audio.bus_channels("voice"))
    assert audio.voice("Hurt") == "voice.hurt"
    assert audio.voice("victory") == "voice.victory"
    assert audio.active_voices() <= VOICE_CHANNELS
    assert audio.voice("unknown") is None
    assert audio.active_voices() <= VOICE_CHANNELS
    audio.set_volumes(0.5, 0.5, 0.0)
    assert audio.voice("defeat") == "voice.defeat"  # legenda mesmo com vozes mudas
    for name in ("hello", "surprise"):
        assert audio.voice(name) == f"voice.{name}"


def test_ambient_loops_by_world_with_fade(audio: AudioSystem) -> None:
    for world in range(1, 6):
        audio.ambient(f"world-{world}")
        assert audio.ambient_name == synth.AMBIENT_ALIASES[f"world-{world}"]
        settle(audio, 0.5)
    assert any(channel.get_busy() for channel in audio.bus_channels("ambient"))
    settle(audio, 1.5)
    assert [channel.get_busy() for channel in audio.bus_channels("ambient")].count(True) == 1
    active = next(channel for channel in audio.bus_channels("ambient") if channel.get_busy())
    assert 0.0 < active.get_volume() < 0.6  # volume baixo
    audio.ambient("wind")
    settle(audio, 0.3)
    assert audio.fading
    audio.ambient(None)
    assert audio.ambient_name is None
    settle(audio, 1.5)
    assert not any(channel.get_busy() for channel in audio.bus_channels("ambient"))
    audio.ambient("unknown")  # ignorado
    assert audio.ambient_name is None


def test_prewarm_in_background_thread_fills_the_cache() -> None:
    system = AudioSystem()
    try:
        assert system.available
        system.prewarm(wait=True, timeout=30.0)
        for track in synth.ALL_TRACKS:
            assert system.has_sound("track", track.name)
        for name in synth.AMBIENT_NAMES:
            assert system.has_sound("ambient", name)
        for name in synth.VOICE_NAMES:
            assert system.has_sound("voice", name)
        system.set_world(5, boss=True)
        system.ambient("lava")
        settle(system, 0.5)
        assert any(channel.get_busy() for channel in system.bus_channels("music"))
    finally:
        system.dispose()
    assert not system.available
    system.menu()  # após dispose tudo é inofensivo
    system.effect("coin")
    system.update(0.1)
    system.dispose()


def test_disabled_system_is_silent_and_safe() -> None:
    system = AudioSystem(enabled=False)
    assert system.available is False
    system.set_volumes(1.0, 1.0, 1.0, 1.0)
    system.menu()
    system.set_world(3, boss=True)
    system.pause(True)
    system.pause(False)
    system.effect("coin")
    assert system.voice("jump") == "voice.jump"
    system.ambient("world-2")
    system.update(1 / 60)
    system.prewarm()
    system.dispose()
    assert system.track is not None
    assert system.track.name == "boss"


def test_mixer_failure_makes_system_unavailable_but_safe(monkeypatch: pytest.MonkeyPatch) -> None:
    pygame.mixer.quit()

    def broken_init(*_args: object, **_kwargs: object) -> None:
        raise pygame.error("No available audio device")

    monkeypatch.setattr(pygame.mixer, "init", broken_init)
    system = AudioSystem()
    assert system.available is False
    assert pygame.mixer.get_init() is None
    system.set_volumes(0.3, 0.3, 0.3, 0.3)
    system.menu()
    system.set_world(2)
    system.set_world(2, boss=True)
    system.pause(True)
    system.pause(False)
    for kind in EVENT_TYPES:
        system.effect(kind)
    assert system.voice("hello") == "voice.hello"
    assert system.voice("nothing") is None
    system.ambient("world-4")
    system.ambient(None)
    for _ in range(10):
        system.update(1 / 60)
    assert system.active_effects() == 0
    assert system.bus_channels("sfx") == []
    system.prewarm()
    system.dispose()
    system.dispose()
