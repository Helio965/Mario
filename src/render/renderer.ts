import type { Game } from '../core/game';
export class Renderer {
  private ctx: CanvasRenderingContext2D;
  constructor(canvas: HTMLCanvasElement) { this.ctx = canvas.getContext('2d')!; }
  backdrop() { this.ctx.fillStyle = '#73c9dd'; this.ctx.fillRect(0, 0, 960, 540); }
  render(game: Game, _now: number) {
    this.backdrop(); const c = this.ctx; c.save(); c.translate(-game.camera.x, -game.camera.y);
    for (const p of game.platforms) { if (!p.alive) continue; c.fillStyle = '#5a7852'; c.fillRect(p.x,p.y,p.w,p.h); }
    c.fillStyle = '#e68a61'; c.fillRect(game.player.x,game.player.y,game.player.w,game.player.h); c.restore();
  }
}
