import { expect, it } from "vitest";
import { Game } from "../../src/core/game";
import { EMPTY_INPUT, type Level } from "../../src/core/types";
const base: Level = {
  id: "test",
  name: "test",
  world: 1,
  stage: 1,
  width: 1800,
  height: 540,
  time: 300,
  spawn: { x: 70, y: 414 },
  checkpoint: { x: 900, y: 414 },
  exit: { x: 1700, y: 448 },
  platforms: [{ id: "g", kind: "ground", x: 0, y: 448, w: 1800, h: 100 }],
  coins: [],
  enemies: [],
  items: [],
  hazards: [],
  hints: [],
};
const run = (g: Game, n: number, input = { ...EMPTY_INPUT }) => {
  for (let i = 0; i < n; i++) g.update(1 / 120, input);
};
it("coleta moeda só uma vez e relíquia tem recompensa própria", () => {
  const g = new Game([
    {
      ...base,
      coins: [
        { id: "c", x: 70, y: 418, w: 16, h: 20 },
        { id: "r", x: 90, y: 418, w: 16, h: 20, special: true },
      ],
    },
  ]);
  run(g, 2);
  expect(g.coinsTotal).toBe(1);
  expect(g.score).toBe(1100);
  expect(g.foundRelic).toBe(true);
  run(g, 30);
  expect(g.score).toBe(1100);
});
it("bloco de pergunta é ativado pela cabeça, libera moeda e esgota", () => {
  const g = new Game([
    {
      ...base,
      platforms: [
        ...base.platforms,
        {
          id: "q",
          kind: "question",
          reward: "coin",
          x: 64,
          y: 336,
          w: 32,
          h: 32,
        },
      ],
    },
  ]);
  run(g, 20);
  run(g, 60, { ...EMPTY_INPUT, jump: true });
  expect(g.platforms[1].used).toBe(true);
  expect(g.coinsTotal).toBe(1);
  run(g, 50);
  run(g, 70, { ...EMPTY_INPUT, jump: true });
  expect(g.coinsTotal).toBe(1);
});
it("cano só transporta ao pressionar para baixo e permite retornar", () => {
  const pipe = {
    id: "p",
    kind: "pipe" as const,
    x: 64,
    y: 432,
    w: 48,
    h: 16,
    destination: { x: 600, y: 414 },
  };
  const g = new Game([
    { ...base, spawn: { x: 70, y: 400 }, platforms: [...base.platforms, pipe] },
  ]);
  run(g, 20);
  expect(g.player.x).toBe(70);
  run(g, 1, { ...EMPTY_INPUT, down: true });
  expect(g.player.x).toBe(600);
  expect(g.events.some((e) => e.type === "secret")).toBe(true);
});
it("plataforma móvel transporta o jogador; temporária reaparece", () => {
  const moving = {
    id: "m",
    kind: "moving" as const,
    x: 80,
    y: 400,
    w: 100,
    h: 16,
    motion: { axis: "x" as const, range: 40, speed: 1 },
  };
  const g = new Game([
    {
      ...base,
      spawn: { x: 100, y: 370 },
      platforms: [...base.platforms, moving],
    },
  ]);
  run(g, 10);
  const x = g.player.x;
  run(g, 30);
  expect(g.player.x).toBeGreaterThan(x + 4);
  const c = new Game([
    {
      ...base,
      spawn: { x: 90, y: 370 },
      platforms: [
        ...base.platforms,
        { id: "c", kind: "crumble", x: 80, y: 400, w: 100, h: 16 },
      ],
    },
  ]);
  run(c, 100);
  expect(c.platforms[1].alive).toBe(false);
  run(c, 400);
  expect(c.platforms[1].alive).toBe(true);
});
