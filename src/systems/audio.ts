import type { GameEvent } from "../core/types";

type Channel = "music" | "sfx";
interface Track {
  bpm: number;
  melody: readonly number[];
  bass: readonly number[];
  color: OscillatorType;
  third: number;
}

// Original 32-step themes; MIDI pitches keep all synthesis local to Web Audio.
const TRACKS: readonly Track[] = [
  {
    bpm: 106,
    color: "triangle",
    third: 4,
    melody: [
      72, 0, 76, 79, 0, 76, 74, 0, 72, 76, 79, 84, 0, 79, 76, 0, 74, 0, 77, 81,
      0, 79, 77, 74, 76, 79, 84, 0, 79, 76, 74, 0,
    ],
    bass: [48, 53, 50, 55],
  },
  {
    bpm: 136,
    color: "square",
    third: 4,
    melody: [
      72, 76, 79, 0, 81, 79, 76, 74, 72, 0, 76, 79, 84, 0, 79, 76, 77, 81, 84,
      0, 86, 84, 81, 79, 76, 0, 79, 83, 86, 83, 79, 0,
    ],
    bass: [48, 45, 53, 55],
  },
  {
    bpm: 118,
    color: "triangle",
    third: 3,
    melody: [
      69, 0, 72, 76, 0, 77, 76, 72, 71, 0, 74, 77, 80, 0, 77, 74, 72, 76, 81, 0,
      79, 76, 72, 0, 71, 74, 76, 80, 0, 76, 71, 0,
    ],
    bass: [45, 50, 53, 52],
  },
  {
    bpm: 112,
    color: "triangle",
    third: 4,
    melody: [
      74, 0, 78, 81, 85, 0, 81, 78, 76, 0, 81, 83, 86, 0, 83, 81, 78, 81, 85,
      88, 0, 85, 81, 78, 76, 78, 81, 85, 0, 81, 78, 0,
    ],
    bass: [50, 57, 55, 52],
  },
  {
    bpm: 124,
    color: "square",
    third: 3,
    melody: [
      71, 74, 78, 0, 81, 78, 74, 0, 73, 76, 80, 0, 83, 80, 76, 0, 74, 78, 81,
      85, 0, 81, 78, 74, 73, 76, 80, 83, 0, 80, 76, 0,
    ],
    bass: [47, 52, 50, 54],
  },
  {
    bpm: 144,
    color: "sawtooth",
    third: 3,
    melody: [
      69, 0, 69, 72, 76, 0, 75, 72, 69, 0, 72, 75, 78, 0, 76, 75, 68, 0, 71, 74,
      77, 0, 74, 71, 68, 71, 74, 77, 80, 77, 74, 0,
    ],
    bass: [45, 41, 44, 40],
  },
];

const BOSS_TRACK: Track = {
  bpm: 164,
  color: "sawtooth",
  third: 3,
  melody: [
    57, 69, 57, 72, 57, 69, 75, 72, 56, 68, 56, 71, 56, 68, 74, 71, 53, 65, 53,
    68, 53, 65, 71, 68, 52, 64, 52, 67, 52, 64, 70, 67,
  ],
  bass: [33, 32, 29, 28],
};

interface Cue {
  notes: readonly number[];
  duration: number;
  wave?: OscillatorType;
  slide?: number;
}
const CUES: Record<GameEvent["type"], Cue> = {
  jump: { notes: [65], duration: 0.13, slide: 14 },
  coin: { notes: [91, 98], duration: 0.055 },
  relic: { notes: [76, 83, 88, 95], duration: 0.1, wave: "triangle" },
  block: { notes: [48], duration: 0.07, slide: -12, wave: "triangle" },
  power: { notes: [60, 64, 67, 72, 76, 79], duration: 0.07 },
  hurt: { notes: [55, 49], duration: 0.13, slide: -7, wave: "sawtooth" },
  death: { notes: [72, 69, 65, 62, 57, 48], duration: 0.15, wave: "triangle" },
  stomp: { notes: [55], duration: 0.085, slide: -19, wave: "triangle" },
  shot: { notes: [77], duration: 0.08, slide: -20 },
  checkpoint: { notes: [72, 76, 79, 84], duration: 0.085, wave: "triangle" },
  secret: { notes: [74, 77, 81, 86, 89], duration: 0.095, wave: "triangle" },
  complete: { notes: [72, 76, 79, 84, 79, 84, 88, 91], duration: 0.12 },
  boss: { notes: [40, 39, 38, 36], duration: 0.14, wave: "sawtooth" },
  life: { notes: [79, 84, 88, 91], duration: 0.09 },
};

function volume(value: number): number {
  return Number.isFinite(value) ? Math.max(0, Math.min(1, value)) : 0;
}

function frequency(midi: number): number {
  return 440 * 2 ** ((midi - 69) / 12);
}

/** Gesture-gated synthesis: one scheduler, two independent volume buses, no external assets. */
export class AudioSystem {
  private context: AudioContext | null = null;
  private musicBus: GainNode | null = null;
  private sfxBus: GainNode | null = null;
  private timer: ReturnType<typeof setInterval> | null = null;
  private voices = new Map<
    AudioScheduledSourceNode,
    { envelope: GainNode; channel: Channel }
  >();
  private track: Track = TRACKS[0];
  private step = 0;
  private nextBeat = 0;
  private musicVolume = 0.45;
  private sfxVolume = 0.75;
  private paused = false;
  private disposed = false;

  unlock(): void {
    if (this.disposed) return;
    if (!this.context) {
      const Context =
        globalThis.AudioContext ??
        (
          globalThis as typeof globalThis & {
            webkitAudioContext?: typeof AudioContext;
          }
        ).webkitAudioContext;
      if (!Context) return;
      try {
        this.context = new Context();
        this.musicBus = this.context.createGain();
        this.sfxBus = this.context.createGain();
        this.musicBus.gain.value = this.musicVolume;
        this.sfxBus.gain.value = this.sfxVolume;
        this.musicBus.connect(this.context.destination);
        this.sfxBus.connect(this.context.destination);
      } catch {
        this.context = null;
        return;
      }
    }
    const context = this.context;
    void context
      .resume()
      .then(() => {
        if (this.context === context && !this.disposed && !this.paused)
          this.startScheduler();
      })
      .catch(() => {
        /* A browser may decline audio; gameplay still works. */
      });
  }

  setVolumes(music: number, sfx: number): void {
    this.musicVolume = volume(music);
    this.sfxVolume = volume(sfx);
    const now = this.context?.currentTime ?? 0;
    this.musicBus?.gain.setTargetAtTime(this.musicVolume, now, 0.025);
    this.sfxBus?.gain.setTargetAtTime(this.sfxVolume, now, 0.025);
  }

  setWorld(world: number, boss = false): void {
    const index = Number.isFinite(world)
      ? Math.max(1, Math.min(5, Math.floor(world)))
      : 1;
    this.changeTrack(boss ? BOSS_TRACK : TRACKS[index]);
  }

  menu(): void {
    this.changeTrack(TRACKS[0]);
  }

  pause(paused: boolean): void {
    if (this.paused === paused) return;
    this.paused = paused;
    if (paused) {
      this.stopScheduler();
      this.stopVoices();
    } else if (this.context && !this.disposed) {
      this.startScheduler();
    }
  }

  effect(type: GameEvent["type"]): void {
    if (
      !this.context ||
      this.context.state !== "running" ||
      this.paused ||
      this.disposed ||
      this.sfxVolume === 0
    )
      return;
    const cue = CUES[type];
    if (!cue) return;
    const now = this.context.currentTime + 0.003;
    cue.notes.forEach((note, index) => {
      this.tone(
        note,
        now + index * cue.duration,
        cue.duration * 0.95,
        cue.wave ?? "square",
        0.12,
        "sfx",
        cue.slide,
      );
    });
  }

  dispose(): void {
    if (this.disposed) return;
    this.disposed = true;
    this.stopScheduler();
    this.stopVoices();
    this.musicBus?.disconnect();
    this.sfxBus?.disconnect();
    const context = this.context;
    this.context = null;
    this.musicBus = null;
    this.sfxBus = null;
    if (context) void context.close().catch(() => {});
  }

  private changeTrack(track: Track): void {
    if (track === this.track || this.disposed) return;
    this.track = track;
    this.step = 0;
    this.stopVoices("music");
    this.nextBeat = (this.context?.currentTime ?? 0) + 0.02;
  }

  private startScheduler(): void {
    if (this.timer !== null || !this.context || this.paused || this.disposed)
      return;
    this.nextBeat = this.context.currentTime + 0.025;
    this.schedule();
    this.timer = setInterval(() => this.schedule(), 50);
  }

  private stopScheduler(): void {
    if (this.timer !== null) clearInterval(this.timer);
    this.timer = null;
  }

  private schedule(): void {
    const context = this.context;
    if (!context || context.state !== "running" || this.paused || this.disposed)
      return;
    const duration = 60 / this.track.bpm / 4;
    // Recover from a suspended tab without enqueueing its missed minutes of notes.
    if (this.nextBeat < context.currentTime - duration)
      this.nextBeat = context.currentTime + 0.01;
    while (this.nextBeat < context.currentTime + 0.14) {
      if (this.musicVolume > 0) {
        const position = this.step % this.track.melody.length;
        const melody = this.track.melody[position];
        const root =
          this.track.bass[Math.floor(position / 8) % this.track.bass.length];
        if (melody)
          this.tone(
            melody,
            this.nextBeat,
            duration * 0.83,
            this.track.color,
            0.058,
            "music",
          );
        if (position % 4 === 0)
          this.tone(
            root,
            this.nextBeat,
            duration * 2.4,
            "triangle",
            0.13,
            "music",
          );
        if (position % 2 === 1) {
          const interval = position % 4 === 1 ? this.track.third : 7;
          this.tone(
            root + 12 + interval,
            this.nextBeat,
            duration * 0.72,
            "triangle",
            0.045,
            "music",
          );
        }
        if (position % 4 === 2)
          this.tone(34, this.nextBeat, 0.035, "triangle", 0.07, "music", -14);
      }
      this.step++;
      this.nextBeat += duration;
    }
  }

  private tone(
    midi: number,
    when: number,
    duration: number,
    wave: OscillatorType,
    loudness: number,
    channel: Channel,
    slide?: number,
  ): void {
    const context = this.context;
    const bus = channel === "music" ? this.musicBus : this.sfxBus;
    if (!context || !bus) return;
    const oscillator = context.createOscillator();
    const envelope = context.createGain();
    oscillator.type = wave;
    oscillator.frequency.setValueAtTime(frequency(midi), when);
    if (slide)
      oscillator.frequency.exponentialRampToValueAtTime(
        frequency(midi + slide),
        when + duration,
      );
    envelope.gain.setValueAtTime(0, when);
    envelope.gain.linearRampToValueAtTime(
      loudness,
      when + Math.min(0.008, duration / 4),
    );
    envelope.gain.exponentialRampToValueAtTime(0.001, when + duration);
    envelope.gain.setValueAtTime(0, when + duration + 0.005);
    oscillator.connect(envelope);
    envelope.connect(bus);
    this.voices.set(oscillator, { envelope, channel });
    oscillator.onended = () => {
      oscillator.disconnect();
      envelope.disconnect();
      this.voices.delete(oscillator);
    };
    oscillator.start(when);
    oscillator.stop(when + duration + 0.008);
  }

  private stopVoices(channel?: Channel): void {
    for (const [source, voice] of this.voices) {
      if (channel && voice.channel !== channel) continue;
      source.onended = null;
      try {
        source.stop();
      } catch {
        /* An already ended node needs only disconnection. */
      }
      source.disconnect();
      voice.envelope.disconnect();
      this.voices.delete(source);
    }
  }
}
