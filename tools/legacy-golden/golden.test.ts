import { it } from "vitest";
import { writeFileSync, mkdirSync } from "node:fs";
import { Game } from "../../src/core/game";
import { EMPTY_INPUT, type InputState } from "../../src/core/types";
import { LEVELS } from "../../src/data/levels";
import { playCampaignRoute } from "../../tests/helpers/route-player";

const OUT = process.env.GOLDEN_OUT ?? "tests/fixtures/golden";
mkdirSync(OUT, { recursive: true });
const mask = (i: InputState) =>
  Number(i.left) | (Number(i.right) << 1) | (Number(i.jump) << 2) | (Number(i.run) << 3) | (Number(i.ability) << 4) | (Number(i.down) << 5);
const r4 = (v: number) => Math.round(v * 10000) / 10000;

function snapshot(g: Game) {
  const p = g.player;
  return {
    x: r4(p.x), y: r4(p.y), vx: r4(p.vx), vy: r4(p.vy), h: p.h, power: p.power,
    grounded: p.grounded, standingOn: p.standingOn, anim: p.animation, inv: r4(p.invulnerable), star: r4(p.star),
    status: g.status, lives: g.lives, score: g.score, coins: g.coinsTotal, time: r4(g.time),
    checkpoint: g.checkpointReached, relic: g.foundRelic, camX: r4(g.camera.x), camY: r4(g.camera.y),
    enemies: g.enemies.filter((e) => e.alive).map((e) => [e.id, r4(e.x), r4(e.y), e.state, e.health, e.facing]),
    items: g.items.length, projectiles: g.projectiles.length, particles: g.particles.length,
    platforms: g.platforms.filter((s) => s.used || !s.alive).map((s) => [s.id, s.used, s.alive]),
    coinsLeft: g.coins.filter((c) => !c.collected).length,
  };
}

/** Record every input passed to Game.update and the resulting state. */
function record(run: () => Game, name: string, every = 4, full = 120) {
  const original = Game.prototype.update;
  const inputs: number[] = [];
  const track: number[] = [];
  const snaps: Record<string, unknown>[] = [];
  const events: [number, string][] = [];
  let tick = 0;
  let eventCursor = 0;
  let game: Game | undefined;
  Game.prototype.update = function (this: Game, dt: number, input: InputState) {
    if (!game) game = this;
    if (this !== game) return original.call(this, dt, input);
    if (Math.abs(dt - 1 / 120) > 1e-12) throw new Error("unexpected dt " + dt);
    inputs.push(mask(input));
    original.call(this, dt, input);
    for (const e of this.events.slice(eventCursor)) events.push([tick, e.type]);
    eventCursor = this.events.length;
    if (tick % every === 0) track.push(r4(this.player.x), r4(this.player.y));
    if (tick % full === 0) snaps.push({ tick, ...snapshot(this) });
    tick++;
  };
  try {
    const g = run();
    if (g !== game) throw new Error("game mismatch");
    snaps.push({ tick, ...snapshot(g) });
    // RLE the input stream.
    const rle: [number, number][] = [];
    for (const m of inputs) {
      if (rle.length && rle[rle.length - 1][0] === m) rle[rle.length - 1][1]++;
      else rle.push([m, 1]);
    }
    const data = { name, level: g.level.id, ticks: tick, every, full, inputs: rle, track, snapshots: snaps, events, final: snapshot(g) };
    writeFileSync(`${OUT}/${name}.json`, JSON.stringify(data));
    return data;
  } finally {
    Game.prototype.update = original;
  }
}

it("records campaign route traces for all fifteen levels", () => {
  const summary: Record<string, unknown>[] = [];
  for (const level of LEVELS) {
    const data = record(() => playCampaignRoute(level, 100, { run: level.id !== "3-2" }).game, `route-${level.id}`);
    summary.push({ level: level.id, ticks: data.ticks, status: data.final.status, lives: data.final.lives, score: data.final.score, events: data.events.length });
  }
  console.log(JSON.stringify(summary));
});

it("records pseudo-random input traces on three levels", () => {
  for (const id of ["1-1", "2-2", "3-2", "5-3"]) {
    const level = LEVELS.find((l) => l.id === id)!;
    record(() => {
      const g = new Game([level]);
      let seed = 1234567 + id.charCodeAt(0) * 7919;
      const rnd = () => { seed = (seed * 1103515245 + 12345) % 2147483648; return seed / 2147483648; };
      let input = { ...EMPTY_INPUT };
      for (let t = 0; t < 120 * 60 && g.status !== "gameover"; t++) {
        if (t % 9 === 0) {
          const r = rnd();
          input = { ...EMPTY_INPUT, right: r < 0.7, left: r >= 0.7 && r < 0.85, jump: rnd() < 0.45, run: rnd() < 0.5, ability: rnd() < 0.2, down: rnd() < 0.08 };
        }
        g.update(1 / 120, input);
      }
      return g;
    }, `random-${id}`);
  }
});

it("records arena traces: physics, ice, ceiling, combat", () => {
  const ARENA = {
    id: "arena", name: "arena", world: 1, stage: 1, width: 2400, height: 540, time: 300,
    spawn: { x: 64, y: 414 }, checkpoint: { x: 1100, y: 414 }, exit: { x: 2280, y: 448 },
    platforms: [
      { id: "floor", kind: "ground" as const, x: 0, y: 448, w: 2400, h: 92 },
      { id: "wall", kind: "brick" as const, x: 480, y: 368, w: 128, h: 80 },
      { id: "ceiling", kind: "brick" as const, x: 700, y: 330, w: 140, h: 16 },
      { id: "ice", kind: "ice" as const, x: 1000, y: 400, w: 400, h: 48 },
      { id: "q", kind: "question" as const, reward: "grow" as const, x: 1500, y: 336, w: 40, h: 28 },
      { id: "mov", kind: "moving" as const, x: 1700, y: 380, w: 100, h: 18, motion: { axis: "y" as const, range: 40, speed: 1.5 } },
      { id: "crumb", kind: "crumble" as const, x: 1900, y: 380, w: 100, h: 20 },
    ],
    coins: [{ id: "c1", x: 300, y: 418, w: 16, h: 20 }, { id: "r1", x: 340, y: 418, w: 22, h: 24, special: true }],
    enemies: [
      { id: "w", kind: "walker" as const, x: 900, y: 420, w: 28, h: 28, patrol: [850, 1000] as [number, number] },
      { id: "s", kind: "shell" as const, x: 1300, y: 420, w: 28, h: 28, patrol: [1200, 1450] as [number, number] },
      { id: "a", kind: "armored" as const, x: 2000, y: 416, w: 34, h: 32, patrol: [1950, 2200] as [number, number], hp: 2 },
      { id: "sh", kind: "shooter" as const, x: 2100, y: 420, w: 28, h: 28, patrol: [2080, 2150] as [number, number] },
      { id: "f", kind: "flyer" as const, x: 600, y: 300, w: 28, h: 24, patrol: [500, 800] as [number, number] },
    ],
    items: [{ id: "fire", kind: "fire" as const, x: 200, y: 420, w: 24, h: 24 }],
    hazards: [{ kind: "spikes" as const, x: 1600, y: 434, w: 48, h: 14 }, { kind: "moving" as const, x: 1150, y: 300, w: 26, h: 26, range: 40, speed: 1.6 }],
    hints: [],
  };
  record(() => {
    const g = new Game([ARENA]);
    let seed = 42;
    const rnd = () => { seed = (seed * 1103515245 + 12345) % 2147483648; return seed / 2147483648; };
    let input = { ...EMPTY_INPUT };
    for (let t = 0; t < 120 * 90 && g.status !== "gameover"; t++) {
      if (t % 7 === 0) {
        const r = rnd();
        input = { ...EMPTY_INPUT, right: r < 0.65, left: r >= 0.65 && r < 0.85, jump: rnd() < 0.4, run: rnd() < 0.6, ability: rnd() < 0.3, down: rnd() < 0.05 };
      }
      g.update(1 / 120, input);
    }
    return g;
  }, "arena-random");
});
