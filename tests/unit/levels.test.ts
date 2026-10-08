import { expect, it } from "vitest";
import { LEVELS, THEMES } from "../../src/data/levels";
import { Game } from "../../src/core/game";
import { EMPTY_INPUT } from "../../src/core/types";
it("contém cinco mundos com três mapas distintos e um chefe por mundo", () => {
  expect(LEVELS).toHaveLength(15);
  expect(THEMES).toHaveLength(5);
  expect(new Set(LEVELS.map((l) => l.id)).size).toBe(15);
  for (let w = 1; w <= 5; w++) {
    const levels = LEVELS.filter((l) => l.world === w);
    expect(levels).toHaveLength(3);
    expect(levels[2].enemies.filter((e) => e.kind === "boss")).toHaveLength(1);
    expect(
      new Set(
        levels.map((l) =>
          JSON.stringify(l.platforms.map((p) => [p.x, p.y, p.w])),
        ),
      ).size,
    ).toBe(3);
  }
});
for (const level of LEVELS) {
  it(`${level.id}: spawn/checkpoint seguros, segredos retornáveis e saída em terra`, () => {
    for (const point of [level.spawn, level.checkpoint]) {
      const g = new Game([{ ...level, spawn: point }]);
      for (let i = 0; i < 90; i++) g.update(1 / 120, EMPTY_INPUT);
      expect(g.lives).toBe(5);
      expect(g.player.grounded).toBe(true);
    }
    expect(
      level.platforms.some(
        (p) =>
          p.x <= level.exit.x &&
          p.x + p.w >= level.exit.x &&
          p.y === level.exit.y,
      ),
    ).toBe(true);
    expect(level.coins.some((c) => c.special)).toBe(true);
    const pipes = level.platforms.filter((p) => p.destination);
    expect(pipes.length).toBeGreaterThanOrEqual(2);
    for (const pipe of pipes) {
      expect(pipe.destination!.x).toBeGreaterThanOrEqual(0);
      expect(pipe.destination!.x).toBeLessThan(level.width);
      expect(
        level.platforms.some(
          (s) =>
            pipe.destination!.x + 22 > s.x &&
            pipe.destination!.x < s.x + s.w &&
            s.y >= pipe.destination!.y + 30 &&
            s.y <= pipe.destination!.y + 100,
        ),
      ).toBe(true);
    }
  });
}
