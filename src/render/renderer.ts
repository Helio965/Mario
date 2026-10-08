import type { Game } from '../core/game';
import type { Coin, Enemy, Item, Platform, Player, Theme } from '../core/types';
import { THEMES } from '../data/levels';

const WIDTH = 960;
const HEIGHT = 540;
const INK = '#202c3e';
const GOLD = '#ffd66d';

/** All scenery and sprites are original, drawn in a shared two-pixel vocabulary. */
export class Renderer {
  private readonly ctx: CanvasRenderingContext2D;
  private frame = 0;
  private cameraX = 0;
  private cameraY = 0;
  private world = 1;
  private theme: Theme;

  constructor(private readonly canvas: HTMLCanvasElement) {
    const context = canvas.getContext('2d', { alpha: false });
    if (!context) throw new Error('Seu navegador precisa de Canvas 2D para jogar.');
    this.ctx = context;
    canvas.width = WIDTH;
    canvas.height = HEIGHT;
    context.imageSmoothingEnabled = false;
    this.theme = THEMES[0];
  }

  render(game: Game, now: number): void {
    this.frame = Number.isFinite(game.elapsed) ? game.elapsed : now / 1000;
    this.world = game.level.world;
    this.theme = THEMES[this.world - 1] || THEMES[0];
    this.cameraX = game.camera.x;
    this.cameraY = game.camera.y;
    const c = this.ctx;
    c.setTransform(1, 0, 0, 1, 0, 0);
    c.imageSmoothingEnabled = false;
    this.sky();
    this.landscape();
    this.weather(false);
    c.save();
    const shake = game.shake > 0 ? Math.min(5, game.shake * 22) : 0;
    c.translate(-Math.round(this.cameraX) + Math.round(Math.sin(this.frame * 83) * shake),
      -Math.round(this.cameraY) + Math.round(Math.cos(this.frame * 97) * shake));
    this.landmarks(game);
    for (const platform of game.platforms) {
      if (platform.alive && this.visible(platform.x, platform.y, platform.w, platform.h)) this.platform(platform);
    }
    this.hazards(game);
    for (const coin of game.coins) if (!coin.collected && this.visible(coin.x, coin.y, coin.w, coin.h)) this.coin(coin);
    for (const item of game.items) if (item.alive && this.visible(item.x, item.y, item.w, item.h)) this.item(item);
    for (const enemy of game.enemies) if (enemy.alive && this.visible(enemy.x, enemy.y, enemy.w, enemy.h)) this.enemy(enemy);
    for (const projectile of game.projectiles) {
      if (!projectile.alive) continue;
      const radius = Math.max(4, projectile.w / 2);
      const x = projectile.x + projectile.w / 2;
      const y = projectile.y + projectile.h / 2;
      this.rect(x - radius - 4, y - radius + 2, radius * 2 + 8, radius * 2 - 4, projectile.hostile ? '#732e69' : '#9d493d');
      this.rect(x - radius, y - radius, radius * 2, radius * 2, projectile.hostile ? '#d869af' : '#ff9e55');
      this.rect(x - radius + 2, y - radius + 2, radius * 2 - 4, radius * 2 - 4, '#fff2b6');
      this.rect(x - projectile.vx / 100 - 9, y - 2, 5, 4, projectile.hostile ? '#d98dbc' : GOLD);
    }
    this.player(game.player);
    for (const particle of game.particles) {
      c.globalAlpha = Math.min(1, particle.life * 3);
      this.rect(particle.x, particle.y, particle.size, particle.size, particle.color);
    }
    c.globalAlpha = 1;
    c.restore();
    this.weather(true);
    this.vignette();
  }

  backdrop(world = 1): void {
    this.world = Math.max(1, Math.min(THEMES.length, world));
    this.theme = THEMES[this.world - 1];
    this.frame = 2.4;
    this.cameraX = 0;
    this.cameraY = 0;
    this.ctx.setTransform(1, 0, 0, 1, 0, 0);
    this.sky();
    this.landscape();
    const demo: Platform = { id: 'preview', x: 0, y: 460, w: WIDTH, h: 80, kind: 'ground',
      startX: 0, startY: 460, dx: 0, dy: 0, used: false, alive: true, bump: 0, crumble: 0, respawn: 0 };
    this.platform(demo);
    this.shrub(70, 460, 1);
    this.shrub(816, 460, 2);
    this.weather(true);
    this.vignette();
  }

  private visible(x: number, y: number, w: number, h: number): boolean {
    return x + w > this.cameraX - 60 && x < this.cameraX + WIDTH + 60 &&
      y + h > this.cameraY - 90 && y < this.cameraY + HEIGHT + 90;
  }

  private rect(x: number, y: number, w: number, h: number, color: string): void {
    this.ctx.fillStyle = color;
    this.ctx.fillRect(Math.round(x), Math.round(y), Math.round(w), Math.round(h));
  }

  private polygon(points: number[], color: string): void {
    const c = this.ctx;
    c.fillStyle = color;
    c.beginPath();
    c.moveTo(Math.round(points[0]), Math.round(points[1]));
    for (let index = 2; index < points.length; index += 2) c.lineTo(Math.round(points[index]), Math.round(points[index + 1]));
    c.closePath();
    c.fill();
  }

  private tint(color: string, amount: number): string {
    const hex = color.replace('#', '');
    if (!/^[a-f0-9]{6}$/i.test(hex)) return color;
    const target = amount > 0 ? 255 : 0;
    return '#' + [0, 2, 4].map(offset => {
      const value = parseInt(hex.slice(offset, offset + 2), 16);
      return Math.round(value + (target - value) * Math.abs(amount)).toString(16).padStart(2, '0');
    }).join('');
  }

  private hash(seed: number): number {
    const number = Math.sin(seed * 127.1 + 311.7) * 43758.5453;
    return number - Math.floor(number);
  }

  private sky(): void {
    const t = this.theme;
    for (let y = 0; y < HEIGHT; y += 18) this.rect(0, y, WIDTH, 18, this.tint(t.sky, y / HEIGHT * 0.16));
    const x = 770 - this.cameraX * 0.035;
    const y = 116 - this.cameraY * 0.025;
    const night = this.world >= 4;
    this.rect(x - 38, y - 18, 76, 36, this.tint(t.sky, night ? 0.09 : 0.19));
    this.rect(x - 28, y - 28, 56, 56, this.tint(t.sky, night ? 0.13 : 0.25));
    this.polygon([x - 18, y - 28, x + 18, y - 28, x + 28, y - 18, x + 28, y + 18,
      x + 18, y + 28, x - 18, y + 28, x - 28, y + 18, x - 28, y - 18], night ? '#d7e7d4' : '#ffe5a0');
    if (night) {
      this.rect(x + 5, y - 10, 9, 6, '#adcac2');
      this.rect(x - 15, y + 10, 6, 6, '#adcac2');
      for (let i = 0; i < 54; i++) {
        const starX = this.hash(i + 77) * WIDTH;
        const starY = this.hash(i + 180) * 290;
        this.ctx.globalAlpha = 0.4 + Math.sin(this.frame * 0.8 + i) * 0.22;
        this.rect(starX, starY, i % 7 === 0 ? 3 : 2, 2, '#dce6db');
        if (i % 11 === 0) this.rect(starX + 1, starY - 2, 1, 6, '#dce6db');
      }
      this.ctx.globalAlpha = 1;
    }
    const cloudColor = this.world === 5 ? '#6c5560' : this.world === 4 ? '#5a7b8b' : this.tint(t.sky, 0.5);
    for (let i = -1; i < 7; i++) {
      const offset = ((this.cameraX * 0.12 + this.frame * 3) % 270 + 270) % 270;
      const cx = i * 270 - offset;
      const cy = 73 + this.hash(i + 120) * 98 - this.cameraY * 0.045;
      this.cloud(cx, cy, 0.7 + this.hash(i + 50) * 0.55, cloudColor);
    }
    this.rect(0, 386 - this.cameraY * 0.08, WIDTH, 85, this.tint(t.sky, 0.21));
  }

  private cloud(x: number, y: number, scale: number, color: string): void {
    this.rect(x + 20 * scale, y, 34 * scale, 12 * scale, color);
    this.rect(x + 10 * scale, y + 8 * scale, 65 * scale, 20 * scale, color);
    this.rect(x, y + 18 * scale, 96 * scale, 18 * scale, color);
    this.rect(x + 10 * scale, y + 36 * scale, 78 * scale, 6 * scale, this.tint(color, -0.04));
  }

  private landscape(): void {
    const base = 450 - this.cameraY * 0.11;
    const far = this.theme.far;
    const near = this.theme.near;
    // Wide mountain layers keep the route readable while the world moves at different speeds.
    for (let layer = 0; layer < 2; layer++) {
      const step = layer ? 340 : 450;
      const parallax = layer ? 0.2 : 0.085;
      const offset = this.cameraX * parallax;
      const first = Math.floor(offset / step) - 1;
      for (let i = first; i < first + 5; i++) {
        const x = i * step - offset;
        const peak = base - (layer ? 130 : 235) - this.hash(i + layer * 50) * 70;
        const color = layer ? near : far;
        if (this.world === 1) {
          this.polygon([x - 30, base, x + 16, peak + 108, x + 46, peak + 62,
            x + 90, peak + 38, x + 122, peak + 30, x + 156, peak + 40,
            x + 198, peak + 84, x + 232, peak + 124, x + step, base], color);
          if (!layer) this.polygon([x + 50, peak + 83, x + 91, peak + 41, x + 121, peak + 32,
            x + 156, peak + 45, x + 186, peak + 70, x + 141, peak + 60, x + 108, peak + 64], this.tint(color, 0.1));
        } else if (this.world === 2) {
          this.polygon([x - 20, base, x + 30, peak + 70, x + 60, peak + 70, x + 60, peak + 20,
            x + 170, peak + 20, x + 170, peak + 46, x + 213, peak + 46, x + 267, base], color);
          this.rect(x + 62, peak + 30, 107, 7, this.tint(color, 0.1));
          this.rect(x + 29, peak + 99, 170, 5, this.tint(color, -0.08));
          this.rect(x + 88, peak + 50, 6, 62, this.tint(color, -0.09));
        } else if (this.world === 3) {
          this.polygon([x - 25, base, x + 116, peak, x + 150, peak + 52, x + 183, peak + 19, x + step, base], color);
          this.polygon([x + 81, peak + 62, x + 116, peak, x + 150, peak + 52, x + 130, peak + 45,
            x + 119, peak + 61, x + 109, peak + 37, x + 100, peak + 70], layer ? '#c8e9ee' : '#b2d6df');
          this.polygon([x + 160, peak + 58, x + 183, peak + 19, x + 218, peak + 62, x + 184, peak + 48], '#bbdce7');
        } else if (this.world === 4) {
          this.rect(x + 89, peak + 80, 30, base - peak, color);
          this.polygon([x + 18, peak + 140, x + 56, peak + 78, x + 56, peak + 49, x + 93, peak + 10,
            x + 130, peak + 24, x + 154, peak + 65, x + 151, peak + 90, x + 182, peak + 140], color);
          this.rect(x + 106, peak + 180, 5, 76, this.tint(color, 0.09));
          this.polygon([x + 111, peak + 196, x + 143, peak + 176, x + 140, peak + 188, x + 114, peak + 211], color);
        } else {
          this.polygon([x - 30, base, x + 75, peak + 20, x + 123, peak + 20, x + 146, peak + 32,
            x + 185, peak + 19, x + step, base], color);
          this.polygon([x + 83, peak + 31, x + 116, peak + 31, x + 145, peak + 45,
            x + 159, peak + 30, x + 177, peak + 29, x + 157, peak + 70, x + 152, peak + 139,
            x + 128, peak + 84], layer ? '#b65450' : '#8d4c53');
          this.rect(x + 133, peak + 51, 8, 33, '#e88963');
        }
      }
    }
    // Ancient little silhouettes tie all five frontiers together.
    const offset = this.cameraX * 0.32;
    for (let i = Math.floor(offset / 620) - 1; i < Math.floor(offset / 620) + 3; i++) {
      const x = i * 620 + 205 - offset;
      const y = base - 49;
      const color = this.tint(near, -0.09);
      this.rect(x, y - 18, 48, 95, color);
      this.rect(x - 5, y - 25, 60, 11, color);
      this.rect(x + 7, y - 35, 8, 12, color);
      this.rect(x + 32, y - 35, 8, 12, color);
      this.rect(x + 18, y + 11, 12, 26, this.tint(color, -0.14));
      this.rect(x + 20, y + 14, 3, 15, this.tint(color, 0.1));
      if (this.world === 4) this.mushroom(x + 71, base + 18, 0.8, '#75868b', '#4b737a');
      if (this.world === 1 || this.world === 3) this.pine(x + 91, base + 24, 0.75, color);
    }
  }

  private pine(x: number, y: number, scale: number, color: string): void {
    this.rect(x - 4 * scale, y - 53 * scale, 8 * scale, 53 * scale, '#6b6557');
    for (let i = 0; i < 3; i++) {
      const top = y - (100 - i * 26) * scale;
      const width = (20 + i * 12) * scale;
      this.polygon([x, top, x + width, top + 44 * scale, x - width, top + 44 * scale], color);
      if (this.world === 3) this.polygon([x, top, x + width * 0.5, top + 23 * scale,
        x + 4 * scale, top + 19 * scale, x - width * 0.54, top + 23 * scale], '#b2dbe2');
    }
  }

  private mushroom(x: number, y: number, scale: number, cap: string, stem: string): void {
    this.rect(x - 4 * scale, y - 24 * scale, 8 * scale, 24 * scale, stem);
    this.polygon([x - 30 * scale, y - 22 * scale, x - 25 * scale, y - 40 * scale,
      x - 9 * scale, y - 50 * scale, x + 13 * scale, y - 50 * scale,
      x + 29 * scale, y - 34 * scale, x + 31 * scale, y - 22 * scale], cap);
    this.rect(x - 17 * scale, y - 36 * scale, 6 * scale, 4 * scale, this.tint(cap, 0.2));
    this.rect(x + 7 * scale, y - 43 * scale, 5 * scale, 5 * scale, this.tint(cap, 0.2));
  }

  private landmarks(game: Game): void {
    const { level } = game;
    const start = Math.floor((this.cameraX - 100) / 190);
    for (let i = start; i < start + 7; i++) {
      const x = i * 190 + 22 + this.hash(i + 33) * 55;
      const ground = game.platforms.find(platform => platform.kind === 'ground' && x >= platform.x + 14 && x < platform.x + platform.w - 26);
      if (ground && ground.alive) this.shrub(x, ground.y, i);
    }
    if (this.visible(level.checkpoint.x, level.checkpoint.y - 110, 50, 110)) {
      const x = level.checkpoint.x;
      const ground = game.platforms.find(p => p.kind === 'ground' && x >= p.x && x < p.x + p.w);
      const y = ground?.y ?? level.checkpoint.y + 30;
      this.rect(x - 8, y - 4, 34, 5, '#384558');
      this.rect(x + 4, y - 101, 5, 97, '#d3d7c2');
      this.rect(x + 9, y - 96, 28, 24, game.checkpointReached ? '#6ee2bf' : '#8fa19d');
      this.rect(x + 9, y - 96, 28, 3, game.checkpointReached ? '#c2f9d8' : '#b4c1b3');
      this.rect(x + 22, y - 90, 3, 12, '#264f57');
      this.rect(x + 17, y - 85, 13, 3, '#264f57');
      if (game.checkpointReached) this.sparkle(x + 6, y - 103, 5, '#eeffc9');
    }
    if (this.visible(level.exit.x - 40, level.exit.y - 230, 250, 320)) this.exit(level.exit.x, level.exit.y, level.world);
    for (const hint of level.hints) {
      if (hint.x < this.cameraX - 30 || hint.x > this.cameraX + WIDTH + 30) continue;
      const platform = game.platforms.find(p => p.kind === 'ground' && hint.x >= p.x && hint.x < p.x + p.w);
      if (!platform) continue;
      this.rect(hint.x + 9, platform.y - 29, 4, 29, '#77634f');
      this.rect(hint.x - 4, platform.y - 44, 30, 21, '#3a505d');
      this.rect(hint.x - 2, platform.y - 42, 26, 17, '#e4c894');
      this.rect(hint.x + 9, platform.y - 39, 3, 7, '#43555b');
      this.rect(hint.x + 9, platform.y - 29, 3, 3, '#43555b');
    }
  }

  private shrub(x: number, y: number, seed: number): void {
    if (this.world === 1) {
      const color = seed % 2 ? '#407f69' : '#4e9570';
      this.rect(x, y - 10, 27, 10, color);
      this.rect(x + 5, y - 17, 14, 7, color);
      this.rect(x - 6, y - 5, 40, 5, this.tint(color, -0.13));
      for (let i = 0; i < 4; i++) {
        this.rect(x + i * 7, y - 9 - i % 2 * 4, 3, 3, i % 2 ? '#f4a793' : '#eadba0');
      }
      if (seed % 5 === 0) this.pine(x - 40, y, 0.75, '#326e60');
    } else if (this.world === 2) {
      this.rect(x + 7, y - 39, 12, 39, '#537d67');
      this.rect(x + 3, y - 34, 20, 24, '#537d67');
      this.rect(x - 6, y - 26, 9, 16, '#537d67');
      this.rect(x - 6, y - 28, 9, 5, '#a4b283');
      this.rect(x + 22, y - 35, 8, 18, '#537d67');
      this.rect(x + 9, y - 35, 3, 30, '#80a783');
      this.rect(x + 19, y - 6, 16, 6, '#7c7761');
    } else if (this.world === 3) {
      if (seed % 3 === 0) this.pine(x + 10, y, 0.85, '#458894');
      else {
        this.polygon([x, y, x + 7, y - 15, x + 25, y - 14, x + 33, y], '#a3cbd7');
        this.rect(x + 7, y - 15, 18, 4, '#e3f5ee');
        this.rect(x + 16, y - 8, 8, 4, '#86afc1');
      }
    } else if (this.world === 4) {
      this.mushroom(x + 10, y, 0.4 + this.hash(seed) * 0.3, '#75b5ad', '#578291');
      this.mushroom(x + 31, y, 0.3, '#ac80a8', '#67828b');
      this.rect(x - 4, y - 5, 48, 5, '#356967');
    } else {
      this.polygon([x, y, x + 4, y - 11, x + 13, y - 19, x + 23, y - 15, x + 34, y], '#5e5260');
      this.rect(x + 11, y - 14, 5, 9, '#d37664');
      this.rect(x + 21, y - 8, 8, 4, '#8c5d63');
    }
  }

  private exit(x: number, y: number, world: number): void {
    const color = world === 5 ? '#8e6170' : '#bac3b8';
    this.rect(x + 81, y - 116, 69, 116, '#354753');
    this.rect(x + 75, y - 125, 82, 10, color);
    this.rect(x + 75, y - 116, 13, 116, color);
    this.rect(x + 144, y - 116, 13, 116, color);
    for (let i = 0; i < 4; i++) this.rect(x + 75 + i * 23, y - 136, 13, 12, color);
    this.rect(x + 99, y - 61, 33, 61, '#263540');
    this.rect(x + 105, y - 71, 21, 12, '#263540');
    this.rect(x + 108, y - 56, 4, 50, '#435d60');
    this.rect(x + 100, y - 108, 12, 15, '#5c8180');
    this.rect(x + 127, y - 108, 12, 15, '#5c8180');
    this.rect(x - 8, y - 4, 42, 4, '#344f58');
    this.rect(x + 9, y - 177, 6, 173, '#d4d7b9');
    this.rect(x + 15, y - 177, 3, 172, '#809aa0');
    this.sparkle(x + 12, y - 184, 5, '#f7dda2');
    const wave = Math.round(Math.sin(this.frame * 5) * 3);
    this.polygon([x + 18, y - 169, x + 61, y - 167 + wave, x + 70, y - 154 + wave,
      x + 59, y - 138 + wave, x + 18, y - 141], '#e7ad65');
    this.rect(x + 20, y - 166, 4, 22, '#ffe3a3');
    this.sparkle(x + 41, y - 153, 7, '#fef7cb');
    for (let i = 0; i < 3; i++) this.rect(x + 82, y - 70 + i * 22, 7, 3, '#8eaba6');
  }

  private platform(p: Platform): void {
    if (p.kind === 'hidden' && !p.used) return;
    const x = p.x;
    const y = p.y - Math.sin(Math.max(0, p.bump) * Math.PI) * 8;
    const t = this.theme;
    if (p.kind === 'ground' || p.kind === 'ice') {
      const ice = p.kind === 'ice';
      this.rect(x, y, p.w, p.h, ice ? '#84bacd' : t.ground);
      this.rect(x, y, p.w, 9, ice ? '#d3f6f1' : t.top);
      this.rect(x, y + 9, p.w, 5, ice ? '#a8dce4' : this.tint(t.ground, -0.15));
      if (ice) {
        for (let i = Math.max(0, Math.floor((this.cameraX - x) / 44)); i * 44 < p.w && x + i * 44 < this.cameraX + WIDTH + 44; i++) {
          const ix = x + i * 44;
          this.polygon([ix + 4, y + 19, ix + 19, y + 19, ix + 7, y + 30], '#b5e5e9');
          this.rect(ix + 30, y + 38, 4, 6, '#669fb9');
        }
      } else {
        const first = Math.max(0, Math.floor((this.cameraX - x - 32) / 32));
        const last = Math.min(Math.ceil(p.w / 32), Math.ceil((this.cameraX + WIDTH - x + 32) / 32));
        for (let i = first; i < last; i++) {
          const tx = x + i * 32;
          const right = Math.min(32, x + p.w - tx);
          this.rect(tx + 2, y + 2, Math.max(0, right - 4), 3, this.tint(t.top, 0.14));
          this.rect(tx + 5, y + 9, 7, 6, t.top);
          if (this.world === 3) this.polygon([tx + 18, y + 9, tx + 22, y + 21, tx + 26, y + 9], '#b7e2e6');
          for (let row = 0; row * 28 + 23 < p.h; row++) {
            const px = tx + 4 + this.hash(i * 33 + row) * 17;
            const py = y + 22 + row * 28;
            const rock = this.hash(i + row * 54);
            if (rock > 0.32) this.rect(px, py, 6 + rock * 7, 3, this.tint(t.ground, -0.16));
            if (rock > 0.65) this.rect(px + 3, py + 5, 5, 2, this.tint(t.ground, 0.09));
          }
        }
      }
      this.rect(x, y + p.h - 4, p.w, 4, ice ? '#6195ab' : this.tint(t.ground, -0.2));
      return;
    }
    if (p.kind === 'pipe') {
      const base = this.world === 2 ? '#638b83' : this.world === 5 ? '#855e75' : '#4c9290';
      this.rect(x + 5, y + 10, p.w - 10, p.h - 10, '#283f50');
      this.rect(x + 9, y + 10, p.w - 19, p.h - 10, base);
      this.rect(x + 12, y + 15, 5, p.h - 15, this.tint(base, 0.25));
      this.rect(x + p.w - 18, y + 15, 6, p.h - 15, this.tint(base, -0.16));
      this.rect(x, y, p.w, 18, '#283f50');
      this.rect(x + 2, y + 2, p.w - 4, 13, base);
      this.rect(x + 4, y + 3, p.w - 8, 3, this.tint(base, 0.36));
      this.rect(x + p.w - 12, y + 5, 5, 8, this.tint(base, -0.18));
      this.rect(x + 4, y + 10, 3, 3, '#d2d4ab');
      this.rect(x + p.w - 7, y + 10, 3, 3, '#d2d4ab');
      if (p.destination) {
        this.rect(x + p.w / 2 - 6, y + 22, 12, 3, '#9de3c4');
        this.polygon([x + p.w / 2 - 5, y + 28, x + p.w / 2 + 5, y + 28, x + p.w / 2, y + 34], '#9de3c4');
      }
      return;
    }
    if (p.kind === 'moving' || p.kind === 'crumble') {
      const crumble = p.kind === 'crumble';
      const offset = crumble && p.crumble > 0 ? Math.sin(this.frame * 50) * 2 : 0;
      const color = crumble ? '#a58c8a' : '#5e91a7';
      this.rect(x + offset, y, p.w, p.h, INK);
      this.rect(x + 2 + offset, y + 2, p.w - 4, p.h - 5, color);
      this.rect(x + 3 + offset, y + 2, p.w - 6, 4, this.tint(color, 0.25));
      for (let i = 9; i < p.w - 4; i += 18) {
        this.rect(x + i + offset, y + 8, 3, 3, crumble ? '#6c606d' : '#c2e4cf');
        if (crumble) this.polygon([x + i, y + 5, x + i + 3, y + 5, x + i, y + 10, x + i + 4, y + 14, x + i + 1, y + 13, x + i - 3, y + 9], '#695a65');
      }
      if (!crumble) this.rect(x + 5, y + p.h - 4, p.w - 10, 2, '#34667d');
      return;
    }
    const used = p.used;
    const question = p.kind === 'question' || p.kind === 'hidden';
    const fill = question ? used ? '#7c888b' : '#dea856' : this.world === 3 ? '#8fbdcc' : '#ba7968';
    for (let localX = 0; localX < p.w; localX += 40) {
      const width = Math.min(40, p.w - localX);
      const bx = x + localX;
      this.rect(bx, y, width, p.h, '#38414b');
      this.rect(bx + 2, y + 2, width - 4, p.h - 4, fill);
      this.rect(bx + 3, y + 3, width - 6, 3, this.tint(fill, 0.25));
      this.rect(bx + width - 5, y + 5, 2, p.h - 7, this.tint(fill, -0.2));
      this.rect(bx + 3, y + p.h - 5, width - 6, 2, this.tint(fill, -0.18));
      if (question) {
        this.rect(bx + 4, y + 9, 2, 2, this.tint(fill, -0.35));
        this.rect(bx + width - 6, y + p.h - 11, 2, 2, this.tint(fill, -0.35));
        if (!used) {
          const bob = Math.round(Math.sin(this.frame * 4) * 1);
          this.sprite(['.###.', '#...#', '....#', '..##.', '..#..', '.....', '..#..'], { '#': '#fff0bd' }, bx + width / 2 - 5, y + p.h / 2 - 7 + bob, 2);
        } else this.rect(bx + width / 2 - 2, y + p.h / 2 - 2, 4, 4, '#aab7ad');
      } else {
        this.rect(bx + 2, y + Math.floor(p.h / 2), width - 4, 2, '#815b5b');
        this.rect(bx + 15, y + 6, 2, p.h / 2 - 6, '#815b5b');
        this.rect(bx + 8, y + p.h / 2 + 2, 2, p.h / 2 - 6, '#815b5b');
      }
    }
  }

  private hazards(game: Game): void {
    for (const hazard of game.level.hazards) {
      let x = hazard.x;
      let y = hazard.y;
      if (hazard.kind === 'moving') {
        x += Math.sin(game.elapsed * (hazard.speed || 1)) * (hazard.range || 60);
        y += Math.cos(game.elapsed * (hazard.speed || 1) * 1.4) * 9;
      }
      if (!this.visible(x, y, hazard.w, hazard.h)) continue;
      if (hazard.kind === 'lava') {
        this.rect(x, y + 6, hazard.w, hazard.h - 6, '#bd4e4b');
        for (let i = 0; i < hazard.w; i += 16) {
          const offset = Math.round(Math.sin(this.frame * 3 + i / 21) * 3);
          this.rect(x + i, y + offset, Math.min(16, hazard.w - i), 8, '#ffc176');
          this.rect(x + i + 2, y + 9 + offset, Math.min(12, hazard.w - i - 2), 6, '#ec7957');
          if (i % 48 === 0) this.rect(x + i + 5, y + 27 + Math.sin(this.frame + i) * 4, 7, 4, '#ec8e5f');
        }
      } else if (hazard.kind === 'spikes') {
        this.rect(x, y + hazard.h - 5, hazard.w, 5, '#53616c');
        for (let i = 0; i < hazard.w; i += 16) {
          this.polygon([x + i, y + hazard.h - 4, x + i + 8, y + 1, x + i + 16, y + hazard.h - 4], '#d0d5d0');
          this.polygon([x + i + 8, y + 3, x + i + 8, y + hazard.h - 4, x + i + 15, y + hazard.h - 4], '#8899a7');
        }
      } else {
        this.ctx.save();
        this.ctx.translate(x + hazard.w / 2, y + hazard.h / 2);
        this.ctx.rotate(this.frame * 3);
        for (let i = 0; i < 8; i++) {
          this.ctx.save();
          this.ctx.rotate(i * Math.PI / 4);
          this.polygon([-5, -hazard.h * 0.28, 0, -hazard.h * 0.52, 7, -hazard.h * 0.34], '#ccd5cf');
          this.ctx.restore();
        }
        this.rect(-hazard.w * 0.26, -hazard.h * 0.26, hazard.w * 0.52, hazard.h * 0.52, '#78899a');
        this.rect(-5, -5, 10, 10, '#ecc174');
        this.ctx.restore();
      }
    }
  }

  private coin(coin: Coin): void {
    const phase = this.frame * 6 + coin.x / 45;
    const x = coin.x + coin.w / 2;
    const y = coin.y + coin.h / 2 + Math.sin(this.frame * 2 + coin.x / 90) * 2;
    if (coin.special) {
      const float = Math.sin(this.frame * 3) * 2;
      this.rect(x - 17, y - 6 + float, 34, 12, '#596b79');
      this.polygon([x - 17, y - 6 + float, x - 25, y - 12 + float, x - 21, y + 4 + float, x - 8, y + 8 + float], '#a5d7c2');
      this.polygon([x + 17, y - 6 + float, x + 25, y - 12 + float, x + 21, y + 4 + float, x + 8, y + 8 + float], '#a5d7c2');
      this.polygon([x, y - 19 + float, x + 13, y + float, x, y + 19 + float, x - 13, y + float], '#253b51');
      this.polygon([x, y - 16 + float, x + 10, y + float, x, y + 16 + float, x - 10, y + float], '#62dfc1');
      this.polygon([x, y - 12 + float, x + 5, y + float, x, y + 5 + float, x - 5, y + float], '#ddffe0');
      this.rect(x - 2, y + 8 + float, 4, 4, '#36a9a5');
      this.sparkle(x + Math.sin(phase / 2) * 25, y + Math.cos(phase / 2) * 21, 3, '#dcf7c9');
      return;
    }
    const half = Math.max(2, Math.round(Math.abs(Math.cos(phase)) * Math.max(5, coin.w / 2)));
    this.polygon([x - half + 2, y - 9, x + half - 2, y - 9, x + half, y - 6,
      x + half, y + 6, x + half - 2, y + 9, x - half + 2, y + 9, x - half, y + 6, x - half, y - 6], '#b28044');
    this.rect(x - half + 1, y - 6, Math.max(2, half * 2 - 2), 12, GOLD);
    if (half > 3) {
      this.rect(x - half + 2, y - 5, 2, 9, '#fff1b8');
      this.rect(x + 1, y - 4, 2, 8, '#d6a052');
    }
  }

  private item(item: Item): void {
    const c = this.ctx;
    c.save();
    c.translate(Math.round(item.x + item.w / 2), Math.round(item.y + item.h / 2));
    const scale = Math.min(item.w, item.h) / 24;
    c.scale(scale, scale);
    if (item.kind === 'grow') {
      this.polygon([-11, -3, -7, -8, 6, -9, 11, -4, 10, 7, 5, 11, -6, 11, -11, 5], '#253d4d');
      this.polygon([-8, -3, -5, -6, 5, -6, 8, -2, 7, 7, 3, 9, -5, 8, -8, 4], '#e8877b');
      this.rect(-5, -3, 3, 5, '#ffbf94');
      this.rect(3, 2, 3, 5, '#b45868');
      this.rect(0, -12, 3, 7, '#558977');
      this.polygon([2, -9, 7, -13, 11, -11, 6, -8], '#a0d190');
    } else if (item.kind === 'fire') {
      this.rect(-8, -7, 16, 17, '#304151');
      this.rect(-6, -5, 12, 13, '#d58f52');
      this.rect(-3, 9, 6, 3, '#725763');
      this.polygon([-3, 5, -5, 0, -2, -7, 0, -4, 3, -13, 6, -3, 5, 3, 2, 6], '#ffd277');
      this.rect(-1, 1, 3, 5, '#fff3b4');
      this.rect(-9, -8, 18, 3, '#92b19c');
      this.rect(-7, -13, 3, 6, '#92b19c');
      this.rect(4, -13, 3, 6, '#92b19c');
      this.rect(-4, -14, 8, 3, '#92b19c');
    } else if (item.kind === 'star') {
      this.sparkle(0, 0, 12, '#ae8755');
      this.sparkle(0, -1, 9, '#ffe5a0');
      this.sparkle(-1, -2, 4, '#fffbd7');
    } else {
      this.polygon([-11, -6, -6, -10, -1, -8, 1, -8, 6, -10, 11, -6, 11, 0, 0, 12, -11, 0], '#613a53');
      this.polygon([-8, -5, -5, -7, 0, -3, 5, -7, 8, -5, 8, -1, 0, 8, -8, -1], '#f58b8d');
      this.rect(-5, -5, 3, 3, '#ffd2b0');
    }
    c.restore();
  }

  private sparkle(x: number, y: number, radius: number, color: string): void {
    this.polygon([x, y - radius, x + radius * 0.25, y - radius * 0.25, x + radius, y,
      x + radius * 0.25, y + radius * 0.25, x, y + radius, x - radius * 0.25, y + radius * 0.25,
      x - radius, y, x - radius * 0.25, y - radius * 0.25], color);
  }

  private player(player: Player): void {
    if (player.invulnerable > 0 && player.star <= 0 && Math.floor(this.frame * 15) % 2 === 0) return;
    const c = this.ctx;
    const running = player.animation === 'run';
    const moving = player.animation === 'walk' || running;
    const airborne = player.animation === 'jump' || player.animation === 'fall';
    const stride = moving ? Math.sin(this.frame * (running ? 24 : 15)) : 0;
    const unit = player.h / 25;
    c.save();
    c.translate(Math.round(player.x + player.w / 2), Math.round(player.y + player.h));
    if (player.animation === 'dead') c.rotate(Math.sin(this.frame * 8) * 0.2);
    c.scale(player.facing < 0 ? -unit : unit, unit);
    c.translate(-8, -25 + (moving ? Math.abs(stride) * -0.6 : 0));
    if (player.star > 0) {
      const color = ['#8be9d0', '#ffe396', '#dba4d8', '#c8e8ff'][Math.floor(this.frame * 8) % 4];
      c.globalAlpha = 0.28;
      this.rect(1, 2, 15, 20, color);
      c.globalAlpha = 1;
      this.sparkle(18 + Math.sin(this.frame * 11) * 3, 8 + Math.cos(this.frame * 11) * 7, 2, color);
      this.sparkle(-2, 13 + Math.sin(this.frame * 8) * 6, 2, color);
    }
    const palette: Record<string, string> = {
      K: INK, H: '#dda66a', L: '#f4d391', R: '#b96458', S: '#f3b99a', E: '#203643',
      T: player.power === 'fire' ? '#f2c177' : '#62ccb9', J: player.power === 'fire' ? '#d98a62' : '#ddc394',
      B: '#a57c68', D: '#466b79', W: '#ffdfb0', A: '#a0e5d0',
    };
    const upper = [
      '.......KKK......',
      '......KHHHK.....',
      '.....KHHHHHK....',
      '....KHHLLHHHK...',
      '...KHHHHHHHHHK..',
      '..KKKKKKKKKKKK..',
      '....KRRRSSSK....',
      '....KRSSSESK....',
      '.....KSSSSSSK...',
      '.....KRSSSSK....',
      '....KTTTTTTTK...',
      '...KTTTTATTTTK..',
      '..KBJJTTTJJJBK..',
      '..KBJJJJJJJJBK..',
      '...KJJJWWJJJK...',
      '...KJJBBJJJJK...',
      '....KDDDDDDK....',
      '.....KDDDDK.....',
    ];
    this.sprite(upper, palette, 0, 0, 1);
    // The scarf, arms and feet move independently, including distinct airborne poses.
    const scarfY = 11 + Math.sin(this.frame * 11) * 0.5;
    this.polygon([4, 10, -2 - (running ? 3 : 0), scarfY, -3 - (running ? 3 : 0), scarfY + 3, 3, 12], palette.T);
    this.rect(-2 - (running ? 3 : 0), scarfY + 1, 2, 1, palette.A);
    if (player.power === 'fire') {
      this.rect(-3 - (running ? 3 : 0), scarfY - 1, 2, 2, '#fff1a3');
    }
    const backLeg = airborne ? -3 : stride * 3;
    const frontLeg = airborne ? 3 : -stride * 3;
    this.limb(6, 18, backLeg, airborne ? 3 : 6, '#355463', '#694e51');
    this.limb(10, 18, frontLeg, airborne ? 6 : 6, '#4f7c86', '#8d6260');
    if (player.animation === 'win') {
      this.limb(12, 12, 4, -7, '#ddc394', '#f3b99a');
      this.sparkle(17, 4, 2, GOLD);
    } else if (player.animation === 'hurt' || player.animation === 'dead') {
      this.limb(12, 12, 5, -3, palette.J, palette.S);
    } else if (airborne) {
      this.limb(12, 12, 2, player.animation === 'jump' ? -4 : 2, palette.J, palette.S);
    } else {
      this.limb(12, 12, -stride * 2, 4, palette.J, palette.S);
    }
    this.rect(8, 6, 3, 1, palette.W);
    c.restore();
    if (player.grounded && Math.abs(player.vx) > 210 && Math.floor(this.frame * 12) % 2 === 0) {
      this.ctx.globalAlpha = 0.45;
      this.rect(player.x + (player.facing > 0 ? -7 : player.w + 4), player.y + player.h - 4, 6, 3, '#d5cab5');
      this.ctx.globalAlpha = 1;
    }
  }

  private limb(x: number, y: number, dx: number, dy: number, cloth: string, end: string): void {
    const c = this.ctx;
    c.save();
    c.translate(x, y);
    c.rotate(-Math.atan2(dx, dy));
    this.rect(-2, 0, 4, Math.abs(dy) + 1, INK);
    this.rect(-1, 0, 2, Math.abs(dy), cloth);
    this.rect(-2, Math.abs(dy) - 1, 6, 3, INK);
    this.rect(-1, Math.abs(dy) - 1, 4, 2, end);
    c.restore();
  }

  private sprite(rows: string[], palette: Record<string, string>, x: number, y: number, unit = 1): void {
    for (let row = 0; row < rows.length; row++) {
      for (let column = 0; column < rows[row].length; column++) {
        const color = palette[rows[row][column]];
        if (color) this.rect(x + column * unit, y + row * unit, unit, unit, color);
      }
    }
  }

  private enemy(enemy: Enemy): void {
    const c = this.ctx;
    c.save();
    c.translate(Math.round(enemy.x + enemy.w / 2), Math.round(enemy.y + enemy.h));
    c.scale(enemy.facing < 0 ? -1 : 1, 1);
    const s = Math.min(enemy.w / 28, enemy.h / 26);
    if (enemy.kind !== 'boss') c.scale(s, s);
    if (enemy.hitTimer > 0 && Math.floor(this.frame * 18) % 2 === 0) c.globalAlpha = 0.45;
    const gait = Math.sin(this.frame * 12 + enemy.x);
    if (enemy.kind === 'walker') {
      for (let i = -1; i <= 1; i++) {
        this.rect(i * 8 - 4 + gait * i, -5, 5, 5, '#493648');
        this.rect(i * 8 - 3 + gait * i, -3, 6, 3, '#624b5a');
      }
      this.polygon([-14, -9, -13, -18, -7, -24, 5, -24, 11, -19, 13, -9], '#403545');
      this.polygon([-11, -10, -10, -17, -5, -21, 4, -21, 9, -17, 10, -10], '#c78076');
      this.rect(-7, -18, 6, 3, '#e8ab85');
      this.rect(-1, -19, 2, 11, '#884f67');
      this.rect(7, -13, 8, 8, '#dbb297');
      this.rect(10, -13, 3, 4, '#28394b');
      this.rect(10, -14, 3, 1, '#fae2b6');
      this.rect(13, -8, 4, 2, '#433245');
      this.rect(-9, -25, 2, 4, '#2e404a');
      this.rect(5, -25, 2, 4, '#2e404a');
    } else if (enemy.kind === 'shell') {
      if (enemy.state === 'walk') {
        this.rect(-10 + gait, -4, 7, 4, '#614b50');
        this.rect(6 - gait, -4, 7, 4, '#614b50');
        this.rect(6, -14, 9, 8, '#cfa987');
        this.rect(11, -14, 3, 3, '#293a43');
        this.rect(15, -10, 4, 3, '#cfa987');
      }
      this.polygon([-14, -5, -14, -14, -8, -24, 3, -27, 10, -22, 13, -10, 11, -5], '#343c49');
      this.polygon([-11, -7, -11, -14, -6, -21, 2, -24, 8, -20, 10, -10, 8, -7], '#b99868');
      for (let i = 0; i < 3; i++) {
        this.rect(-8 + i * 6, -19 - (i === 1 ? 3 : 0), 2, 11 + (i === 1 ? 3 : 0), '#7d6a63');
        this.rect(-6 + i * 6, -18, 2, 3, '#ead3a0');
      }
      if (enemy.state === 'slide') {
        this.rect(-20, -8, 5, 2, '#e6c891');
        this.rect(-24, -4, 8, 2, '#bfa887');
      }
    } else if (enemy.kind === 'flyer') {
      const flap = Math.sin(this.frame * 16) * 6;
      this.polygon([-5, -12, -10, -24 + flap, -21, -29 + flap, -19, -11 + flap, -11, -8, -6, -4], '#41374f');
      this.polygon([-7, -12, -11, -21 + flap, -18, -23 + flap, -16, -12 + flap], '#ac7aa4');
      this.polygon([4, -13, 13, -24 + flap, 22, -29 + flap, 20, -12 + flap, 13, -7, 5, -4], '#41374f');
      this.polygon([7, -12, 13, -21 + flap, 18, -23 + flap, 17, -12 + flap], '#b786ad');
      this.rect(-5, -18, 11, 14, '#766083');
      this.rect(-5, -22, 3, 5, '#41374f');
      this.rect(3, -22, 3, 5, '#41374f');
      this.rect(-3, -14, 3, 4, '#ffe5a0');
      this.rect(3, -14, 3, 4, '#ffe5a0');
      this.rect(-2, -13, 1, 2, '#373547');
      this.rect(4, -13, 1, 2, '#373547');
      this.rect(0, -8, 3, 3, '#d5a3a4');
    } else if (enemy.kind === 'shooter') {
      this.rect(-11, -5, 22, 5, '#3b4f4d');
      this.rect(-8, -23, 16, 22, '#3c7064');
      this.rect(-6, -21, 4, 17, '#739e77');
      this.rect(1, -21, 3, 16, '#285c59');
      this.rect(-14, -17, 6, 9, '#3c7064');
      this.rect(-15, -21, 6, 5, '#769e7a');
      this.rect(7, -16, 7, 5, '#537e65');
      this.rect(12, -18, 5, 9, '#233d49');
      this.rect(13, -16, 4, 5, '#c9b386');
      this.polygon([-10, -24, -8, -30, -2, -27, 1, -33, 5, -27, 10, -29, 11, -23], '#d48799');
      this.rect(-7, -24, 17, 5, '#a76583');
      this.rect(3, -20, 3, 3, '#f5d99d');
    } else if (enemy.kind === 'armored') {
      this.rect(-11 + gait, -5, 8, 5, '#3e4754');
      this.rect(4 - gait, -5, 8, 5, '#3e4754');
      this.polygon([-15, -6, -15, -18, -9, -29, 5, -31, 14, -21, 15, -6], '#303f50');
      this.polygon([-11, -8, -12, -17, -7, -26, 4, -27, 11, -19, 11, -8], '#8c9eaa');
      this.rect(-8, -23, 9, 4, '#bec2b5');
      this.rect(-2, -19, 2, 10, '#697c8d');
      this.rect(4, -18, 8, 3, '#344a58');
      this.rect(5, -17, 5, 2, '#f6c776');
      this.polygon([-9, -26, -10, -34, -4, -30, 2, -34, 5, -29], '#b9bdae');
      this.rect(-16, -13, 5, 9, '#667e8b');
    } else {
      this.boss(enemy, gait);
    }
    c.restore();
  }

  private boss(enemy: Enemy, gait: number): void {
    const c = this.ctx;
    c.save();
    c.scale(enemy.w / 76, enemy.h / 84);
    this.rect(-25 + gait * 2, -10, 18, 10, '#263b4c');
    this.rect(13 - gait * 2, -10, 19, 10, '#263b4c');
    this.rect(-22 + gait * 2, -7, 14, 4, '#b58b7c');
    this.rect(17 - gait * 2, -7, 14, 4, '#b58b7c');
    this.polygon([-34, -17, -34, -49, -23, -66, 15, -69, 32, -53, 37, -22, 27, -13], '#293746');
    this.polygon([-29, -20, -28, -48, -19, -60, 13, -62, 28, -51, 31, -24, 24, -18], '#8b6979');
    this.rect(-20, -55, 11, 30, '#aa7e84');
    this.rect(-5, -58, 11, 32, '#aa7e84');
    this.rect(10, -55, 11, 30, '#aa7e84');
    this.rect(-21, -51, 41, 4, '#ce9a8c');
    this.rect(-24, -24, 50, 5, '#504a61');
    this.rect(-11, -37, 24, 13, '#514761');
    this.sparkle(1, -33, 8, '#71cfbf');
    this.sparkle(1, -34, 4, '#e4ffe0');
    this.polygon([-24, -57, -28, -77, -19, -73, -13, -84, -8, -76, 13, -76, 20, -84,
      22, -71, 31, -77, 30, -58], '#293746');
    this.rect(-15, -73, 35, 24, '#b58b83');
    this.rect(-10, -68, 13, 4, '#4c4058');
    this.rect(9, -68, 12, 4, '#4c4058');
    this.rect(-7, -66, 8, 3, '#ffe3a2');
    this.rect(11, -66, 7, 3, '#ffe3a2');
    this.rect(1, -63, 9, 9, '#82636f');
    this.rect(-7, -53, 26, 4, '#433e51');
    this.rect(-4, -53, 4, 3, '#dfd6b6');
    this.rect(12, -53, 4, 3, '#dfd6b6');
    this.rect(-39, -49, 13, 28, '#574b63');
    this.rect(-38, -46, 10, 6, '#aa8185');
    this.rect(28, -46, 15, 26, '#574b63');
    this.rect(32, -42, 9, 9, '#c59887');
    for (let i = 0; i < 3; i++) this.rect(30 + i * 4, -23, 3, 6, '#e0c29c');
    c.restore();
    c.save();
    c.scale(enemy.facing < 0 ? -1 : 1, 1);
    this.rect(-enemy.w / 2, -enemy.h - 15, enemy.w, 5, '#253744');
    this.rect(-enemy.w / 2 + 1, -enemy.h - 14, Math.max(0, (enemy.w - 2) * enemy.health / (enemy.hp || 8)), 3, '#e6a07d');
    c.restore();
  }

  private weather(foreground: boolean): void {
    const type = this.theme.weather;
    if (type === 'none') return;
    const count = foreground ? 26 : 18;
    const c = this.ctx;
    c.globalAlpha = foreground ? 0.6 : 0.35;
    for (let i = 0; i < count; i++) {
      const seed = i + (foreground ? 0 : 500);
      const speed = type === 'snow' ? 14 : type === 'sand' ? 9 : -10;
      const x = ((this.hash(seed) * WIDTH + Math.sin(this.frame * 0.7 + seed) * 20 + this.frame * (type === 'sand' ? -45 : -8)
        - this.cameraX * (foreground ? 0.7 : 0.15)) % WIDTH + WIDTH) % WIDTH;
      const y = ((this.hash(seed + 51) * HEIGHT + this.frame * speed - this.cameraY * 0.1) % HEIGHT + HEIGHT) % HEIGHT;
      const color = type === 'snow' ? '#e4f4f0' : type === 'sand' ? '#d9bf89' : type === 'embers' ? '#f4a476' : '#b6dac0';
      this.rect(x, y, i % 3 === 0 ? 3 : 2, type === 'sand' ? 1 : 2, color);
      if (type === 'spores' && i % 4 === 0) this.rect(x - 1, y + 1, 4, 1, '#74b49b');
    }
    c.globalAlpha = 1;
  }

  private vignette(): void {
    const c = this.ctx;
    const gradient = c.createLinearGradient(0, 0, 0, HEIGHT);
    gradient.addColorStop(0, 'rgba(12,28,40,0.11)');
    gradient.addColorStop(0.22, 'rgba(12,28,40,0)');
    gradient.addColorStop(0.85, 'rgba(12,28,40,0)');
    gradient.addColorStop(1, 'rgba(12,28,40,0.10)');
    c.fillStyle = gradient;
    c.fillRect(0, 0, WIDTH, HEIGHT);
  }
}
