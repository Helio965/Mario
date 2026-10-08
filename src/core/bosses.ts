import type { Game } from "./game";
import type { Enemy } from "./types";
/** Guardians rest with their shell open, then charge, jump and fire. */
export function updateBoss(game: Game, e: Enemy, previousTimer: number) {
  const aggressive = e.health <= (e.hp ?? 4) / 2;
  const period = aggressive ? 3.8 : 4.8;
  const phase = e.timer % period,
    previousPhase = previousTimer % period;
  const vulnerable = phase < (aggressive ? 1.1 : 1.65);
  e.state = vulnerable ? "shell" : "walk";
  e.vx = vulnerable ? 0 : e.facing * (aggressive ? 135 : 85);
  if (phase >= 2 && previousPhase < 2 && e.grounded) e.vy = -400;
  const shots = game.level.world === 5 ? [2.5, 3, 3.4] : [2.7];
  for (const shotTime of shots) {
    if (phase >= shotTime && previousPhase < shotTime) {
      const dir = game.player.x < e.x ? -1 : 1;
      game.projectiles.push({
        x: e.x + e.w / 2,
        y: e.y + 24,
        w: 14,
        h: 14,
        vx: dir * (160 + game.level.world * 15),
        vy: aggressive ? -40 : 0,
        hostile: true,
        life: 4,
        alive: true,
      });
      game.events.push({ type: "shot" });
    }
  }
}
