import { describe, expect, it } from "vitest";
import { Game } from "../../src/core/game";
import { hitEnemy } from "../../src/core/enemies";
import { FIXED_DT } from "../../src/core/physics";
import { LEVELS } from "../../src/data/levels";
import { EMPTY_INPUT, type InputState, type Level } from "../../src/core/types";

const BOSS_LEVELS = LEVELS.filter((level) =>
  level.enemies.some((enemy) => enemy.kind === "boss"),
);

function ticks(game: Game, count: number, input: Partial<InputState> = {}) {
  for (let i = 0; i < count; i++)
    game.update(FIXED_DT, { ...EMPTY_INPUT, ...input });
}

function arena(source: Level, withPowers = false) {
  const boss = source.enemies.find((enemy) => enemy.kind === "boss")!;
  const offset = boss.patrol[0] - 300;
  const right = boss.patrol[1] - offset;
  const floor = source.platforms.find(
    (platform) =>
      platform.y === boss.y + boss.h &&
      platform.x <= boss.x &&
      platform.x + platform.w >= boss.x + boss.w,
  )!;
  const level: Level = {
    ...source,
    width: right + 200,
    height: 540,
    time: 300,
    spawn: { x: 240, y: 418 },
    checkpoint: { x: 240, y: 418 },
    exit: { x: right + 100, y: 448 },
    platforms: [{ ...floor, id: "arena-floor", x: 0, y: 448, w: right + 200 }],
    enemies: [{ ...boss, x: boss.x - offset, patrol: [300, right] }],
    coins: [],
    hazards: [],
    hints: [],
    items: withPowers
      ? [
          { id: "arena-fire", kind: "fire", x: 240, y: 418, w: 24, h: 24 },
          { id: "arena-star", kind: "star", x: 240, y: 418, w: 24, h: 24 },
        ]
      : [],
  };
  const game = new Game([level]);
  ticks(game, 2);
  return game;
}

describe("cinco guardiões reais da campanha", () => {
  it("encontra exatamente um guardião em cada mundo", () => {
    expect(BOSS_LEVELS.map((level) => level.world)).toEqual([1, 2, 3, 4, 5]);
    expect(
      BOSS_LEVELS.map(
        (level) => level.enemies.find((enemy) => enemy.kind === "boss")!.hp,
      ),
    ).toEqual([3, 4, 5, 6, 7]);
  });

  for (const level of BOSS_LEVELS) {
    describe(`mundo ${level.world}: ${level.name}`, () => {
      it("bloqueia dano fora da abertura e aceita só um golpe durante o intervalo de recuperação", () => {
        const game = arena(level);
        const boss = game.enemies[0];
        const health = boss.health;
        boss.timer = 1.8;
        ticks(game, 1);
        expect(boss.state).toBe("walk");
        expect(hitEnemy(game, boss)).toBe(false);
        expect(boss.health).toBe(health);

        boss.timer = 0.2;
        ticks(game, 1);
        expect(boss.state).toBe("shell");
        expect(hitEnemy(game, boss)).toBe(true);
        expect(boss.health).toBe(health - 1);
        expect(hitEnemy(game, boss)).toBe(false);
        expect(boss.health).toBe(health - 1);
      });

      it("na segunda fase fecha a abertura mais cedo, corre mais rápido e altera o projétil", () => {
        const calm = arena(level);
        const angry = arena(level);
        angry.enemies[0].health = Math.floor(angry.enemies[0].health / 2);
        for (const game of [calm, angry]) game.enemies[0].timer = 1.3;
        ticks(calm, 1);
        ticks(angry, 1);
        expect(calm.enemies[0].state).toBe("shell");
        expect(angry.enemies[0].state).toBe("walk");

        for (const game of [calm, angry]) game.enemies[0].timer = 1.8;
        ticks(calm, 1);
        ticks(angry, 1);
        expect(Math.abs(angry.enemies[0].vx)).toBeGreaterThan(
          Math.abs(calm.enemies[0].vx),
        );

        const attackTime = level.world === 5 ? 2.5 : 2.7;
        for (const game of [calm, angry])
          game.enemies[0].timer = attackTime - FIXED_DT / 2;
        ticks(calm, 1);
        ticks(angry, 1);
        expect(
          calm.projectiles.filter((projectile) => projectile.hostile),
        ).toHaveLength(1);
        expect(
          angry.projectiles.filter((projectile) => projectile.hostile),
        ).toHaveLength(1);
        expect(calm.projectiles[0].vy).toBe(0);
        expect(angry.projectiles[0].vy).toBeLessThan(0);
      });

      it("protege a saída enquanto estiver vivo", () => {
        const game = arena(level);
        game.player.x = game.level.exit.x;
        ticks(game, 1);
        expect(game.status).toBe("playing");
        expect(game.events.some((event) => event.type === "complete")).toBe(
          false,
        );
      });

      it("pode ser derrotado com poder coletado e J, liberando uma conclusão por movimento normal", () => {
        const game = arena(level, true);
        const boss = game.enemies[0];
        expect(game.player.power).toBe("fire");
        expect(game.player.star).toBeGreaterThan(0);
        let jumpRemaining = 0;
        for (
          let i = 0;
          i < 3000 && boss.alive && game.status === "playing";
          i++
        ) {
          const incoming = game.projectiles.some(
            (projectile) =>
              projectile.hostile &&
              projectile.vx < 0 &&
              projectile.x > game.player.x &&
              projectile.x - game.player.x < 145 &&
              projectile.y + projectile.h > game.player.y - 10 &&
              projectile.y < game.player.y + game.player.h,
          );
          if (incoming && game.player.grounded && jumpRemaining === 0)
            jumpRemaining = 28;
          ticks(game, 1, { ability: true, jump: jumpRemaining-- > 0 });
          jumpRemaining = Math.max(0, jumpRemaining);
        }
        expect(game.status).toBe("playing");
        expect(boss.alive).toBe(false);
        expect(
          game.events.filter((event) => event.type === "boss"),
        ).toHaveLength(1);

        for (let i = 0; i < 600 && game.status === "playing"; i++) {
          ticks(game, 1, { right: true, run: true });
        }
        expect(game.status).toBe("complete");
        expect(game.player.animation).toBe("win");
        expect(
          game.events.filter((event) => event.type === "complete"),
        ).toHaveLength(1);
      });
    });
  }
});

it("o guardião final dispara três vezes por ciclo, enquanto os demais disparam uma", () => {
  const shots = BOSS_LEVELS.map((level) => {
    // Keep the observation alive through the complete cycle without attacking.
    const game = arena(level, true);
    ticks(game, 430);
    return game.events.filter((event) => event.type === "shot").length;
  });
  expect(shots).toEqual([1, 1, 1, 1, 3]);
});

it("inimigo voador patrulha horizontalmente e oscila em torno da altura original", () => {
  const source = LEVELS.find((level) =>
    level.enemies.some((enemy) => enemy.kind === "flyer"),
  )!;
  const flyer = source.enemies.find((enemy) => enemy.kind === "flyer")!;
  const level: Level = {
    ...source,
    spawn: { x: 72, y: 418 },
    platforms: [
      { id: "floor", kind: "ground", x: 0, y: 448, w: source.width, h: 92 },
    ],
    enemies: [{ ...flyer, patrol: [...flyer.patrol] }],
    items: [],
    coins: [],
    hazards: [],
    hints: [],
  };
  const game = new Game([level]);
  const enemy = game.enemies[0];
  const initialX = enemy.x;
  let minY = enemy.y,
    maxY = enemy.y;
  for (let i = 0; i < 480; i++) {
    ticks(game, 1);
    minY = Math.min(minY, enemy.y);
    maxY = Math.max(maxY, enemy.y);
    expect(enemy.x).toBeGreaterThanOrEqual(flyer.patrol[0]);
    expect(enemy.x + enemy.w).toBeLessThanOrEqual(flyer.patrol[1]);
  }
  expect(enemy.x).not.toBe(initialX);
  expect(maxY - minY).toBeGreaterThan(70);
  expect(minY).toBeGreaterThanOrEqual(flyer.y - 38);
  expect(maxY).toBeLessThanOrEqual(flyer.y + 38);
});

it("projétil hostil causa dano real e desaparece ao atingir o jogador", () => {
  const game = arena(BOSS_LEVELS[0], true);
  game.enemies = [];
  game.player.star = 0;
  game.player.invulnerable = 0;
  game.projectiles.push({
    x: game.player.x + 40,
    y: game.player.y + 10,
    w: 12,
    h: 12,
    vx: -180,
    vy: 0,
    hostile: true,
    life: 3,
    alive: true,
  });
  ticks(game, 20);
  expect(game.player.power).toBe("grown");
  expect(game.lives).toBe(5);
  expect(game.projectiles).toHaveLength(0);
  expect(game.events.filter((event) => event.type === "hurt")).toHaveLength(1);
});
