import type { Rect, Platform } from './types';
export const FIXED_DT = 1 / 120;
export const GRAVITY = 1550;
export const JUMP_SPEED = 590;
export const overlaps = (a: Rect, b: Rect): boolean => a.x < b.x + b.w && a.x + a.w > b.x && a.y < b.y + b.h && a.y + a.h > b.y;
export function approach(value: number, target: number, amount: number): number {
  return value < target ? Math.min(value + amount, target) : Math.max(value - amount, target);
}
export function moveBody(body: Rect & { vx: number; vy: number }, platforms: Platform[], dt: number) {
  let grounded = false;
  let standingOn: string | null = null;
  const heads: Platform[] = [];
  const solids = platforms.filter(p => p.alive);
  body.x += body.vx * dt;
  for (const p of solids) {
    if (p.kind === 'hidden' && !p.used) continue;
    if (!overlaps(body, p)) continue;
    if (body.vx > 0) body.x = p.x - body.w;
    else if (body.vx < 0) body.x = p.x + p.w;
    body.vx = 0;
  }
  const vy = body.vy;
  body.y += vy * dt;
  for (const p of solids) {
    if (p.kind === 'hidden' && !p.used && vy >= 0) continue;
    if (!overlaps(body, p)) continue;
    if (vy > 0) { body.y = p.y - body.h; grounded = true; standingOn = p.id; }
    else if (vy < 0) { body.y = p.y + p.h; heads.push(p); }
    body.vy = 0;
  }
  return { grounded, standingOn, heads };
}
