import { describe, expect, it } from "vitest";
import { Game } from "../../src/core/game";
import { FIXED_DT } from "../../src/core/physics";
import { EMPTY_INPUT, type InputState, type Level } from "../../src/core/types";

const ARENA: Level = {
  id: "physics-extra",
  name: "Arena de física",
  world: 1,
  stage: 1,
  width: 2400,
  height: 540,
  time: 300,
  spawn: { x: 64, y: 418 },
  checkpoint: { x: 1100, y: 418 },
  exit: { x: 2300, y: 448 },
  platforms: [{ id: "floor", kind: "ground", x: 0, y: 448, w: 2400, h: 92 }],
  coins: [],
  enemies: [],
  items: [],
  hazards: [],
  hints: [],
};

function ticks(game: Game, count: number, input: Partial<InputState> = {}) {
  for (let i = 0; i < count; i++)
    game.update(FIXED_DT, { ...EMPTY_INPUT, ...input });
}

function walkOffLedge() {
  const game = new Game([
    {
      ...ARENA,
      spawn: { x: 200, y: 418 },
      platforms: [{ ...ARENA.platforms[0], w: 240 }],
    },
  ]);
  ticks(game, 2);
  expect(game.player.grounded).toBe(true);
  for (let i = 0; i < 120 && game.player.grounded; i++) {
    ticks(game, 1, { right: true, run: true });
  }
  expect(game.player.grounded).toBe(false);
  expect(game.player.x).toBeGreaterThanOrEqual(240);
  return game;
}

describe("física: tolerâncias, limites e recuperação", () => {
  it("aceita salto após sair da borda dentro do coyote time", () => {
    const game = walkOffLedge();
    ticks(game, 5, { right: true, run: true });
    expect(game.player.vy).toBeGreaterThan(0);
    ticks(game, 1, { right: true, run: true, jump: true });
    expect(game.player.vy).toBeLessThan(-500);
    expect(game.events.filter((event) => event.type === "jump")).toHaveLength(
      1,
    );
  });

  it("recusa salto quando a janela de coyote time já terminou", () => {
    const game = walkOffLedge();
    ticks(game, 15, { right: true, run: true });
    ticks(game, 1, { right: true, run: true, jump: true });
    expect(game.player.vy).toBeGreaterThan(0);
    expect(game.events.filter((event) => event.type === "jump")).toHaveLength(
      0,
    );
  });

  it("permite acelerar e inverter a direção horizontal no ar", () => {
    const game = new Game([ARENA]);
    ticks(game, 2);
    ticks(game, 1, { jump: true });
    ticks(game, 10, { jump: true, right: true });
    const beforeReverse = game.player.x;
    expect(game.player.grounded).toBe(false);
    expect(game.player.vx).toBeGreaterThan(60);
    let furthestRight = beforeReverse;
    for (let i = 0; i < 24; i++) {
      ticks(game, 1, { jump: true, left: true });
      furthestRight = Math.max(furthestRight, game.player.x);
    }
    expect(game.player.grounded).toBe(false);
    expect(game.player.vx).toBeLessThan(-60);
    expect(game.player.x).toBeLessThan(furthestRight - 5);
  });

  it("interrompe a subida ao tocar o teto e volta a aterrissar", () => {
    const ceiling = {
      id: "ceiling",
      kind: "brick" as const,
      x: 40,
      y: 330,
      w: 140,
      h: 16,
    };
    const game = new Game([
      { ...ARENA, platforms: [...ARENA.platforms, ceiling] },
    ]);
    ticks(game, 2);
    ticks(game, 1, { jump: true });
    expect(game.player.vy).toBeLessThan(0);
    let hitCeiling = false;
    for (let i = 0; i < 100; i++) {
      ticks(game, 1, { jump: true });
      expect(game.player.y).toBeGreaterThanOrEqual(ceiling.y + ceiling.h);
      hitCeiling ||=
        game.player.y === ceiling.y + ceiling.h && game.player.vy === 0;
    }
    expect(hitCeiling).toBe(true);
    expect(game.player.grounded).toBe(true);
    expect(game.player.y + game.player.h).toBe(448);
    expect(game.events.filter((event) => event.type === "jump")).toHaveLength(
      1,
    );
  });

  it("não atravessa parede fina à velocidade de corrida de 340 px/s", () => {
    const wall = {
      id: "wall",
      kind: "brick" as const,
      x: 480,
      y: 350,
      w: 16,
      h: 98,
    };
    const game = new Game([
      { ...ARENA, platforms: [...ARENA.platforms, wall] },
    ]);
    ticks(game, 2);
    let fastest = 0;
    for (let i = 0; i < 240; i++) {
      ticks(game, 1, { right: true, run: true });
      fastest = Math.max(fastest, game.player.vx);
      expect(game.player.x + game.player.w).toBeLessThanOrEqual(wall.x);
    }
    expect(fastest).toBe(340);
    expect(game.player.x + game.player.w).toBe(wall.x);
    expect(game.player.grounded).toBe(true);
  });

  it("aterra em plataforma fina com velocidade terminal de queda", () => {
    const game = new Game([
      {
        ...ARENA,
        spawn: { x: 64, y: 20 },
        platforms: [{ ...ARENA.platforms[0], h: 8 }],
      },
    ]);
    game.player.vy = 850;
    game.player.vx = 340;
    for (let i = 0; i < 120 && !game.player.grounded; i++) {
      ticks(game, 1, { right: true, run: true });
      expect(game.player.y + game.player.h).toBeLessThanOrEqual(448);
    }
    expect(game.player.grounded).toBe(true);
    expect(game.player.y + game.player.h).toBe(448);
    expect(game.player.vy).toBe(0);
  });

  it("conserva mais velocidade e desliza mais no gelo ao soltar a direção", () => {
    const games = (["ground", "ice"] as const).map((kind) => {
      const game = new Game([
        { ...ARENA, platforms: [{ ...ARENA.platforms[0], kind }] },
      ]);
      ticks(game, 2);
      ticks(game, 60, { right: true, run: true });
      expect(game.player.vx).toBe(340);
      const startX = game.player.x;
      ticks(game, 12);
      return { velocity: game.player.vx, distance: game.player.x - startX };
    });
    expect(games[1].velocity).toBeGreaterThan(games[0].velocity + 100);
    expect(games[1].distance).toBeGreaterThan(games[0].distance + 5);
  });

  it("ativa checkpoint pelo movimento e reaparece nele após cair no buraco", () => {
    const checkpoint = { x: 400, y: 418 };
    const game = new Game([
      {
        ...ARENA,
        checkpoint,
        platforms: [{ ...ARENA.platforms[0], w: 700 }],
      },
    ]);
    ticks(game, 2);
    for (let i = 0; i < 180 && !game.checkpointReached; i++) {
      ticks(game, 1, { right: true, run: true });
    }
    expect(game.checkpointReached).toBe(true);
    expect(
      game.events.filter((event) => event.type === "checkpoint"),
    ).toHaveLength(1);
    for (let i = 0; i < 360 && game.status === "playing"; i++) {
      ticks(game, 1, { right: true, run: true });
    }
    expect(game.status).toBe("dead");
    expect(game.lives).toBe(4);
    for (let i = 0; i < 180 && game.status === "dead"; i++) ticks(game, 1);
    expect(game.status).toBe("playing");
    expect(game.player.x).toBe(checkpoint.x);
    expect(game.player.y).toBe(checkpoint.y);
    expect(game.player.vx).toBe(0);
    expect(game.player.vy).toBe(0);
    expect(game.checkpointReached).toBe(true);
    expect(game.events.filter((event) => event.type === "death")).toHaveLength(
      1,
    );
    expect(
      game.events.filter((event) => event.type === "checkpoint"),
    ).toHaveLength(1);
  });
});
