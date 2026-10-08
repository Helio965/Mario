export interface Vec { x: number; y: number }
export interface Rect extends Vec { w: number; h: number }
export type PlatformKind = 'ground' | 'brick' | 'question' | 'hidden' | 'moving' | 'crumble' | 'pipe' | 'ice';
export type Power = 'small' | 'grown' | 'fire';
export type ItemKind = 'grow' | 'fire' | 'star' | 'heart';
export type EnemyKind = 'walker' | 'shell' | 'flyer' | 'shooter' | 'armored' | 'boss';
export interface PlatformSpec extends Rect {
  id: string; kind: PlatformKind; reward?: ItemKind | 'coin';
  motion?: { axis: 'x' | 'y'; range: number; speed: number; phase?: number };
  destination?: Vec; returnPoint?: Vec;
}
export interface Platform extends PlatformSpec {
  startX: number; startY: number; dx: number; dy: number; used: boolean; alive: boolean;
  bump: number; crumble: number; respawn: number;
}
export interface Coin extends Rect { id: string; special?: boolean; collected: boolean }
export interface EnemySpec extends Rect { id: string; kind: EnemyKind; patrol: [number, number]; hp?: number }
export interface Enemy extends EnemySpec {
  vx: number; vy: number; alive: boolean; health: number; facing: number;
  timer: number; hitTimer: number; state: 'walk' | 'shell' | 'slide'; originY: number; grounded: boolean;
}
export interface Item extends Rect { id: string; kind: ItemKind; vx: number; vy: number; alive: boolean }
export interface Projectile extends Rect { vx: number; vy: number; hostile: boolean; life: number; alive: boolean }
export interface Particle extends Vec { vx: number; vy: number; life: number; color: string; size: number }
export interface Hazard extends Rect { kind: 'lava' | 'water' | 'spikes' | 'moving'; range?: number; speed?: number }
export interface Level {
  id: string; name: string; world: number; stage: number; width: number; height: number; time: number;
  spawn: Vec; checkpoint: Vec; exit: Vec; platforms: PlatformSpec[];
  coins: Omit<Coin, 'collected'>[]; enemies: EnemySpec[]; items: Omit<Item, 'alive' | 'vx' | 'vy'>[];
  hazards: Hazard[]; hints: { x: number; text: string }[];
}
export interface Theme { name: string; subtitle: string; sky: string; far: string; near: string; ground: string; top: string; accent: string; weather: 'none' | 'sand' | 'snow' | 'spores' | 'embers' }
export interface Player extends Rect {
  vx: number; vy: number; facing: number; grounded: boolean; power: Power;
  invulnerable: number; star: number; coyote: number; buffer: number; shootCooldown: number;
  standingOn: string | null; animation: 'idle' | 'walk' | 'run' | 'jump' | 'fall' | 'hurt' | 'dead' | 'win';
}
export interface InputState { left: boolean; right: boolean; jump: boolean; run: boolean; ability: boolean; down: boolean; pause: boolean }
export const EMPTY_INPUT: InputState = { left: false, right: false, jump: false, run: false, ability: false, down: false, pause: false };
export type GameStatus = 'playing' | 'paused' | 'dead' | 'gameover' | 'complete';
export interface GameEvent { type: 'jump' | 'coin' | 'relic' | 'block' | 'power' | 'hurt' | 'death' | 'stomp' | 'shot' | 'checkpoint' | 'secret' | 'complete' | 'boss' | 'life'; x?: number; y?: number; text?: string; value?: number }
