"""Exporta trilhas, cues, vozes e ambientes sintetizados para ``.wav`` (audição e inspeção).

Uso::

    .venv/bin/python tools/render_audio.py [--out build/audio] [--ambient-seconds 8]

Não usa o mixer: só numpy e o módulo ``wave`` da biblioteca padrão. Para cada
arquivo imprime duração, pico e RMS e sai com código 1 se algum deles for
silencioso (RMS = 0) ou saturar (pico >= 1,0). ``build/`` é ignorado pelo git.
"""

from __future__ import annotations

import argparse
import sys
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from game.systems import synth  # noqa: E402
from game.systems.synth import FloatArray  # noqa: E402


def write_wav(path: Path, mono: FloatArray, sample_rate: int) -> None:
    """Grava ``mono`` (float em [-1, 1]) como WAV estéreo int16."""
    data = synth.to_stereo_int16(mono)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(2)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        handle.writeframes(data.tobytes())


def render_all(sample_rate: int, ambient_seconds: float) -> dict[str, FloatArray]:
    assets: dict[str, FloatArray] = {}
    for track in synth.ALL_TRACKS:
        assets[f"track-{track.name}"] = synth.render_track(track, sample_rate)
    for name, cue in synth.CUES.items():
        assets[f"cue-{name}"] = synth.render_cue(cue, sample_rate)
    for name, spec in synth.VOICES.items():
        assets[f"voice-{name}"] = synth.render_voice(spec, sample_rate)
    for name in synth.AMBIENT_NAMES:
        assets[f"ambient-{name}"] = synth.render_ambient(name, sample_rate, ambient_seconds)
    return assets


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[:1] or None)
    parser.add_argument("--out", default=str(ROOT / "build" / "audio"), help="diretório de saída")
    parser.add_argument("--sample-rate", type=int, default=synth.SAMPLE_RATE)
    parser.add_argument("--ambient-seconds", type=float, default=synth.AMBIENT_SECONDS)
    args = parser.parse_args(argv)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    assets = render_all(args.sample_rate, args.ambient_seconds)
    print(f"{'arquivo':<28}{'segundos':>9}{'pico':>8}{'RMS':>9}")
    failures: list[str] = []
    for name, mono in assets.items():
        path = out / f"{name}.wav"
        write_wav(path, mono, args.sample_rate)
        peak = synth.peak(mono)
        level = synth.rms(mono)
        print(f"{path.name:<28}{len(mono) / args.sample_rate:>9.3f}{peak:>8.3f}{level:>9.4f}")
        if level <= 0.0:
            failures.append(f"{name}: silencioso")
        if peak >= 1.0:
            failures.append(f"{name}: pico {peak:.3f} >= 1.0")
    print(f"{len(assets)} arquivos em {out}")
    for failure in failures:
        print(f"FALHA {failure}", file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
