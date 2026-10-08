import { Game } from '../../src/core/game';
import { EMPTY_INPUT, type Enemy, type InputState, type Level, type Platform } from '../../src/core/types';

export interface RouteSample { second: number; x: number; y: number; lives: number; power: string; reason: string; boss?: string }
export interface RouteResult { game: Game; samples: RouteSample[]; ticks: number; deaths: number; powers: number; bossHits: number; incidents: string[] }

// This driver has the same authority as a person pressing the controller: it
// only reads the simulation and advances Game.update with ordinary inputs.
// It never writes entity state, grants items, changes lives, or removes hazards.
export function playCampaignRoute(level: Level, seconds = 100, options: { run?: boolean } = {}): RouteResult {
  const game = new Game([level]);
  let jumpHold = 0;
  let jumpCooldown = 0;
  let goal: Platform | undefined;
  let collecting = false;
  let bossMode = false;
  let groundedBefore = false;
  let landingFrame = false;
  let jumpRun = true;
  let ticks = 0;
  let eventCursor = 0;
  const samples: RouteSample[] = [];
  const incidents: string[] = [];
  let deaths = 0, powers = 0, bossHits = 0;
  const step = 1 / 120;
  const running = options.run ?? true;

  const steer = (input: InputState, center: number, run = false) => {
    const p = game.player;
    const projected = p.x + p.w / 2 + p.vx * (p.grounded ? 0.08 : 0.10);
    input.left = projected > center + 5;
    input.right = projected < center - 5;
    input.run = run;
  };
  const jump = (duration = 0.64) => {
    if (jumpCooldown > 0 || landingFrame || jumpHold > 0) return;
    jumpHold = duration;
    jumpCooldown = 0.18;
  };

  for (; ticks < seconds * 120 && game.status !== 'complete' && game.status !== 'gameover'; ticks++) {
    const p = game.player;
    landingFrame = p.grounded && !groundedBefore;
    groundedBefore = p.grounded;
    if (landingFrame) jumpHold = 0;
    jumpHold = Math.max(0, jumpHold - step);
    jumpCooldown = Math.max(0, jumpCooldown - step);
    const input = { ...EMPTY_INPUT, right: true, run: running, ability: true };
    let reason = 'corrida';
    const boss = game.enemies.find(e => e.alive && e.kind === 'boss');
    if (boss && p.x > boss.patrol[0] - 180) bossMode = true;

    if (game.status === 'dead') {
      goal = undefined;
      collecting = false;
      bossMode = false;
      jumpHold = 0;
      jumpCooldown = 0;
    } else if (bossMode && boss) {
      reason = 'chefe';
      fightBoss(game, boss, input, steer, jump);
    } else {
      if (!goal && p.grounded) {
        goal = game.platforms.find(s => s.alive && !s.used && (s.reward === 'grow' && p.power === 'small' || s.reward === 'fire' && p.power !== 'fire') && s.x > p.x - 36 && s.x < p.x + 200);
      }
      if (goal) {
        if (goal.used) collecting = true;
        if (!collecting) {
          reason = `bloco-${goal.reward}`;
          steer(input, goal.x + goal.w / 2);
          if (p.grounded && Math.abs(p.x + p.w / 2 - (goal.x + goal.w / 2)) < 10 && Math.abs(p.vx) < 45) jump();
        } else {
          const reward = game.items.find(i => i.id === `item-${goal!.id}` && i.alive);
          if (reward) { reason = `coleta-${reward.kind}`; steer(input, reward.x + reward.w / 2 + reward.vx * 0.10); }
          else { goal = undefined; collecting = false; }
        }
      }

      const ahead = p.x + p.w;
      const floorAhead = game.platforms.some(s => s.alive && (s.kind !== 'hidden' || s.used) && ahead + 18 >= s.x && ahead + 18 <= s.x + s.w && s.y >= p.y + p.h - 8 && s.y <= p.y + p.h + 80);
      const wall = game.platforms.some(s => s.alive && (s.kind !== 'hidden' || s.used) && s.x >= ahead - 2 && s.x < ahead + 64 && s.y < p.y + p.h - 3 && s.y + s.h > p.y);
      const enemyAhead = game.enemies.some(e => e.alive && e.kind !== 'boss' && e.x + e.w > p.x && e.x < ahead + 120 && e.y < p.y + p.h + 16 && e.y + e.h > p.y - 8);
      const dangerAhead = level.hazards.some(h => {
        const x = h.kind === 'moving' ? h.x + Math.sin(game.elapsed * (h.speed ?? 1)) * (h.range ?? 30) : h.x;
        return x + h.w > p.x && x < ahead + 90 && h.y < p.y + p.h && h.y + h.h > p.y;
      });
      const incoming = game.projectiles.some(s => s.hostile && s.vx < 0 && s.x > ahead && s.x < ahead + 160 && s.y + s.h > p.y && s.y < p.y + p.h);
      const collectingShot = !!goal && game.projectiles.some(s => s.hostile && s.vx < 0 && s.x > ahead && s.x < ahead + 42 && s.y + s.h > p.y && s.y < p.y + p.h);
      if (collectingShot && p.grounded) jump();
      if (p.grounded && (wall || !floorAhead || enemyAhead || dangerAhead || incoming) && !goal) {
        reason = wall ? 'obstáculo' : !floorAhead ? 'vão' : enemyAhead ? 'inimigo' : dangerAhead ? 'perigo' : 'projétil';
        jumpRun = running && !wall && !dangerAhead;
        jump();
      }
      if (jumpHold > 0 && !goal) input.run = jumpRun;
    }

    input.jump = jumpHold > 0 || bossMode && !!boss && !p.grounded;
    const before = `${ticks / 120}s (${Math.round(p.x)},${Math.round(p.y)}) ${p.power} ${reason} ${JSON.stringify(game.projectiles.filter(s => s.hostile && Math.abs(s.x - p.x) < 180).map(s => [Math.round(s.x), Math.round(s.y)]))}`;
    game.update(step, input);
    for (const event of game.events.slice(eventCursor)) {
      if (event.type === 'death') { deaths++; incidents.push(before); }
      if (event.type === 'power') powers++;
      if (event.type === 'stomp' && bossMode) bossHits++;
    }
    eventCursor = game.events.length;
    if (ticks % 120 === 0) samples.push({ second: ticks / 120, x: Math.round(game.player.x), y: Math.round(game.player.y), lives: game.lives, power: game.player.power, reason, ...(boss ? { boss: `${boss.health}/${boss.state}/${Math.round(boss.x)}` } : {}) });
  }
  return { game, samples, ticks, deaths, powers, bossHits, incidents };
}

function fightBoss(
  game: Game, boss: Enemy, input: InputState,
  steer: (input: InputState, center: number, run?: boolean) => void,
  jump: (duration?: number) => void,
) {
  const p = game.player;
  const center = boss.x + boss.w / 2;
  input.run = false;
  if (!p.grounded) {
    steer(input, center + boss.vx * 0.13);
    return;
  }
  // Approach from outside the hitbox, then jump into a vulnerable window.
  const side = p.x + p.w / 2 < center ? -1 : 1;
  const launch = center + side * 125;
  steer(input, launch);
  if (Math.abs(p.x + p.w / 2 - launch) < 20 && boss.state === 'shell' && boss.hitTimer < 0.1) {
    steer(input, center);
    jump(0.74);
  }
}
