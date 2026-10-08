import type { Game } from '../core/game';
import type { Platform } from '../core/types';
import { THEMES } from '../data/levels';
import { Background } from './background';
import { HEIGHT, INK, PixelPainter, WIDTH, GOLD } from './painter';
import { Sprites } from './sprites';

/** Compose the scrolling world in a fixed 960 × 540 pixel-art viewport. */
export class Renderer extends PixelPainter {
  effects = true;
  private readonly background: Background;
  private readonly sprites: Sprites;

  constructor(canvas: HTMLCanvasElement) {
    const context = canvas.getContext('2d', { alpha: false });
    if (!context) throw new Error('Seu navegador precisa de Canvas 2D para jogar.');
    super({ ctx: context, frame: 0, cameraX: 0, cameraY: 0, world: 1, theme: THEMES[0], effects: true });
    canvas.width = WIDTH;
    canvas.height = HEIGHT;
    context.imageSmoothingEnabled = false;
    this.background = new Background(this.scene);
    this.sprites = new Sprites(this.scene);
  }

  public render(game: Game, now: number): void {
    this.scene.effects = this.effects;
    this.frame = Number.isFinite(game.elapsed) ? game.elapsed : now / 1000;
    this.world = game.level.world;
    this.theme = THEMES[this.world - 1] || THEMES[0];
    this.cameraX = game.camera.x;
    this.cameraY = game.camera.y;
    const c = this.ctx;
    c.setTransform(1, 0, 0, 1, 0, 0);
    c.imageSmoothingEnabled = false;
    this.background.sky();
    this.background.landscape();
    if (this.effects) this.background.weather(false);
    c.save();
    const shake = this.effects && game.shake > 0 ? Math.min(5, game.shake * 22) : 0;
    c.translate(-Math.round(this.cameraX) + Math.round(Math.sin(this.frame * 83) * shake),
      -Math.round(this.cameraY) + Math.round(Math.cos(this.frame * 97) * shake));
    this.landmarks(game);
    for (const platform of game.platforms) {
      if (platform.alive && this.visible(platform.x, platform.y, platform.w, platform.h)) this.platform(platform);
    }
    this.hazards(game);
    for (const coin of game.coins) if (!coin.collected && this.visible(coin.x, coin.y, coin.w, coin.h)) this.sprites.coin(coin);
    for (const item of game.items) if (item.alive && this.visible(item.x, item.y, item.w, item.h)) this.sprites.item(item);
    for (const enemy of game.enemies) if (enemy.alive && this.visible(enemy.x, enemy.y, enemy.w, enemy.h)) this.sprites.enemy(enemy);
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
    this.sprites.player(game.player);
    if (this.effects) {
      for (const particle of game.particles) {
        c.globalAlpha = Math.min(1, particle.life * 3);
        this.rect(particle.x, particle.y, particle.size, particle.size, particle.color);
      }
    }
    c.globalAlpha = 1;
    c.restore();
    if (this.effects) this.background.weather(true);
    this.background.vignette();
  }

  public backdrop(world = 1): void {
    this.scene.effects = this.effects;
    this.world = Math.max(1, Math.min(THEMES.length, world));
    this.theme = THEMES[this.world - 1];
    this.frame = 2.4;
    this.cameraX = 0;
    this.cameraY = 0;
    this.ctx.setTransform(1, 0, 0, 1, 0, 0);
    this.background.sky();
    this.background.landscape();
    const demo: Platform = { id: 'preview', x: 0, y: 460, w: WIDTH, h: 80, kind: 'ground',
      startX: 0, startY: 460, dx: 0, dy: 0, used: false, alive: true, bump: 0, crumble: 0, respawn: 0 };
    this.platform(demo);
    this.background.shrub(70, 460, 1);
    this.background.shrub(816, 460, 2);
    if (this.effects) this.background.weather(true);
    this.background.vignette();
  }

  private landmarks(game: Game): void {
    const { level } = game;
    const start = Math.floor((this.cameraX - 100) / 190);
    for (let i = start; i < start + 7; i++) {
      const x = i * 190 + 22 + this.hash(i + 33) * 55;
      const ground = game.platforms.find(platform => platform.kind === 'ground' && x >= platform.x + 14 && x < platform.x + platform.w - 26);
      if (ground && ground.alive) this.background.shrub(x, ground.y, i);
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
        x += Math.sin(game.elapsed * (hazard.speed || 1)) * (hazard.range || 30);
      }
      if (!this.visible(x, y, hazard.w, hazard.h)) continue;
      if (hazard.kind === 'lava' || hazard.kind === 'water') {
        const water=hazard.kind==='water';
        this.rect(x, y + 6, hazard.w, hazard.h - 6, water?'#347b94':'#bd4e4b');
        for (let i = 0; i < hazard.w; i += 16) {
          const offset = Math.round(Math.sin(this.frame * 3 + i / 21) * 3);
          this.rect(x + i, y + offset, Math.min(16, hazard.w - i), 8, water?'#b4edf3':'#ffc176');
          this.rect(x + i + 2, y + 9 + offset, Math.min(12, hazard.w - i - 2), 6, water?'#62b7cd':'#ec7957');
          if (i % 48 === 0) this.rect(x + i + 5, y + 27 + Math.sin(this.frame + i) * 4, 7, 4, water?'#8dcbd5':'#ec8e5f');
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
}
