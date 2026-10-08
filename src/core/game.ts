import { LEVELS } from '../data/levels';
import { approach, FIXED_DT, GRAVITY, JUMP_SPEED, moveBody, overlaps } from './physics';
import { burst, interactWorld, updatePlatforms } from './interactions';
import { updateEnemies } from './enemies';
import { updatePowers } from './powers';
import type { Coin, Enemy, GameEvent, GameStatus, InputState, Item, Level, Particle, Platform, Player, Projectile } from './types';
export class Game {
  level!: Level;
  levelIndex = 0;
  player!: Player;
  platforms: Platform[] = [];
  coins: Coin[] = [];
  enemies: Enemy[] = [];
  items: Item[] = [];
  projectiles: Projectile[] = [];
  particles: Particle[] = [];
  events: GameEvent[] = [];
  camera = { x: 0, y: 0 };
  status: GameStatus = 'playing';
  time = 300;
  lives = 5;
  score = 0;
  coinsTotal = 0;
  checkpointReached = false;
  foundRelic = false;
  elapsed = 0;
  shake = 0;
  protected accumulator = 0;
  protected previousJump = false;
  protected transition = 0;
  pipeCooldown = 0;
  constructor(public levels: Level[] = LEVELS) { this.load(0); }
  start(index = 0) { this.lives = 5; this.score = 0; this.coinsTotal = 0; this.load(index); }
  load(index: number) {
    this.levelIndex = Math.max(0, Math.min(index, this.levels.length - 1));
    this.level = this.levels[this.levelIndex];
    this.platforms = this.level.platforms.map(p => ({ ...p, startX: p.x, startY: p.y, dx: 0, dy: 0, used: false, alive: true, bump: 0, crumble: 0, respawn: 0 }));
    this.coins = this.level.coins.map(c => ({ ...c, collected: false }));
    this.items = this.level.items.map(i => ({ ...i, alive: true, vx: 0, vy: 0 }));
    this.enemies = this.level.enemies.map(e => ({ ...e, patrol: [...e.patrol] as [number, number], vx: -60, vy: 0, alive: true, health: e.hp ?? (e.kind === 'armored' ? 2 : e.kind === 'boss' ? 4 : 1), facing: -1, timer: 0, hitTimer: 0, state: 'walk', originY: e.y, grounded: false }));
    this.projectiles = []; this.particles = []; this.events = [];
    this.checkpointReached = false; this.foundRelic = false; this.elapsed = 0; this.time = this.level.time;
    this.status = 'playing'; this.accumulator = 0; this.previousJump = false; this.transition = 0;
    this.spawn(this.level.spawn.x, this.level.spawn.y);
  }
  protected spawn(x: number, y: number) {
    this.player = { x, y, w: 22, h: 30, vx: 0, vy: 0, facing: 1, grounded: false, power: 'small', invulnerable: 1.5, star: 0, coyote: 0, buffer: 0, shootCooldown: 0, standingOn: null, animation: 'idle' };
    this.camera = { x: Math.max(0, x - 240), y: 0 };
  }
  pause() { if (this.status === 'playing') this.status = 'paused'; }
  resume() { if (this.status === 'paused') this.status = 'playing'; }
  update(dt: number, input: InputState) {
    if (this.status === 'paused' || this.status === 'complete' || this.status === 'gameover') return;
    this.accumulator += Math.min(dt, 0.25);
    while (this.accumulator >= FIXED_DT) { this.step(FIXED_DT, input); this.accumulator -= FIXED_DT; }
  }
  protected step(dt: number, input: InputState) {
    this.elapsed += dt;
    if (this.status === 'dead') { this.transition -= dt; if (this.transition <= 0) this.respawn(); return; }
    if (this.status !== 'playing') return;
    this.time = Math.max(0, this.time - dt);
    this.pipeCooldown = Math.max(0,this.pipeCooldown-dt);
    updatePlatforms(this,dt);
    const p = this.player;
    p.invulnerable = Math.max(0, p.invulnerable - dt); p.star = Math.max(0, p.star - dt); p.shootCooldown = Math.max(0, p.shootCooldown - dt);
    this.shake = Math.max(0, this.shake - dt);
    const dir = Number(input.right) - Number(input.left);
    const floor = this.platforms.find(s => s.id === p.standingOn);
    const friction = floor?.kind === 'ice' ? 180 : 1500;
    p.vx = approach(p.vx, dir * (input.run ? 340 : 220), (dir ? p.grounded ? 1400 : 1000 : p.grounded ? friction : 500) * dt);
    if (dir) p.facing = dir;
    if (input.jump && !this.previousJump) p.buffer = 0.12;
    this.previousJump = input.jump;
    p.buffer = Math.max(0, p.buffer - dt);
    p.coyote = p.grounded ? 0.1 : Math.max(0, p.coyote - dt);
    if (p.buffer > 0 && p.coyote > 0) { p.vy = -JUMP_SPEED; p.grounded = false; p.standingOn = null; p.coyote = 0; p.buffer = 0; this.events.push({ type: 'jump' }); }
    if (!input.jump && p.vy < -190) p.vy = -190;
    p.vy = Math.min(850, p.vy + GRAVITY * dt);
    const collision = moveBody(p, this.platforms, dt);
    p.grounded = collision.grounded; p.standingOn = collision.standingOn;
    p.x = Math.max(0, Math.min(p.x, this.level.width - p.w));
    this.interactions(dt, input, collision.heads);
    if (p.y > this.level.height + 100 || this.time <= 0) this.die();
    if(this.status==='playing') p.animation = p.invulnerable > 0 && p.invulnerable<1.2 ? 'hurt' : !p.grounded ? p.vy < 0 ? 'jump' : 'fall' : Math.abs(p.vx) > 260 ? 'run' : Math.abs(p.vx) > 15 ? 'walk' : 'idle';
    const targetX = Math.max(0, Math.min(this.level.width - 960, p.x - 310 + p.vx * 0.15));
    const targetY = Math.max(0, Math.min(this.level.height - 540, p.y - 250));
    this.camera.x += (targetX - this.camera.x) * (1 - Math.exp(-6 * dt));
    this.camera.y += (targetY - this.camera.y) * (1 - Math.exp(-6 * dt));
  }
  protected interactions(dt: number, input: InputState, heads: Platform[]) {
    interactWorld(this,input,heads);
    updateEnemies(this,dt);
    updatePowers(this,dt,input);
    const exit={x:this.level.exit.x-12,y:this.level.exit.y-110,w:44,h:110};
    if(overlaps(this.player,exit)&&!this.enemies.some(e=>e.kind==='boss'&&e.alive)) this.finish();
    for(const particle of this.particles) {particle.life-=dt;particle.x+=particle.vx*dt;particle.y+=particle.vy*dt;particle.vy+=300*dt;}
    this.particles=this.particles.filter(v=>v.life>0);
  }
  hurt() {
    const p=this.player;
    if(this.status!=='playing'||p.invulnerable>0||p.star>0) return;
    this.events.push({type:'hurt'});this.shake=0.12;burst(this,p.x,p.y,'#ef9473');
    if(p.power==='small') {this.die();return;}
    if(p.power==='fire') p.power='grown';
    else {p.power='small';p.y+=p.h-30;p.h=30;}
    p.invulnerable=2;p.vx=-p.facing*100;
  }
  finish() {
    if(this.status!=='playing') return;
    this.status='complete';this.player.animation='win';this.score+=Math.floor(this.time)*10;
    this.events.push({type:'complete',text:'Fase concluída!',value:this.score});
  }
  die() {
    if (this.status !== 'playing') return;
    this.lives--; this.status = 'dead'; this.player.animation = 'dead'; this.transition = 1.1;
    this.events.push({ type: 'death' });
  }
  respawn() {
    if (this.lives <= 0) { this.status = 'gameover'; return; }
    const point = this.checkpointReached ? this.level.checkpoint : this.level.spawn;
    this.spawn(point.x, point.y); this.status = 'playing'; this.time = Math.max(this.time, 90);this.projectiles=[];this.pipeCooldown=0;
  }
}
