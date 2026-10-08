import type { Theme } from '../core/types';

export const WIDTH = 960;
export const HEIGHT = 540;
export const INK = '#202c3e';
export const GOLD = '#ffd66d';

export interface RenderScene {
  ctx: CanvasRenderingContext2D;
  frame: number;
  cameraX: number;
  cameraY: number;
  world: number;
  theme: Theme;
}

/** Shared pixel geometry and deterministic variation for all original artwork. */
export class PixelPainter {
  constructor(protected readonly scene: RenderScene) {}
  protected get ctx(): CanvasRenderingContext2D { return this.scene.ctx; }
  protected get frame(): number { return this.scene.frame; }
  protected set frame(value: number) { this.scene.frame = value; }
  protected get cameraX(): number { return this.scene.cameraX; }
  protected set cameraX(value: number) { this.scene.cameraX = value; }
  protected get cameraY(): number { return this.scene.cameraY; }
  protected set cameraY(value: number) { this.scene.cameraY = value; }
  protected get world(): number { return this.scene.world; }
  protected set world(value: number) { this.scene.world = value; }
  protected get theme(): Theme { return this.scene.theme; }
  protected set theme(value: Theme) { this.scene.theme = value; }

  protected visible(x: number, y: number, w: number, h: number): boolean {
    return x + w > this.cameraX - 60 && x < this.cameraX + WIDTH + 60 &&
      y + h > this.cameraY - 90 && y < this.cameraY + HEIGHT + 90;
  }

  protected rect(x: number, y: number, w: number, h: number, color: string): void {
    this.ctx.fillStyle = color;
    this.ctx.fillRect(Math.round(x), Math.round(y), Math.round(w), Math.round(h));
  }

  protected polygon(points: number[], color: string): void {
    const c = this.ctx;
    c.fillStyle = color;
    c.beginPath();
    c.moveTo(Math.round(points[0]), Math.round(points[1]));
    for (let index = 2; index < points.length; index += 2) c.lineTo(Math.round(points[index]), Math.round(points[index + 1]));
    c.closePath();
    c.fill();
  }

  protected tint(color: string, amount: number): string {
    const hex = color.replace('#', '');
    if (!/^[a-f0-9]{6}$/i.test(hex)) return color;
    const target = amount > 0 ? 255 : 0;
    return '#' + [0, 2, 4].map(offset => {
      const value = parseInt(hex.slice(offset, offset + 2), 16);
      return Math.round(value + (target - value) * Math.abs(amount)).toString(16).padStart(2, '0');
    }).join('');
  }

  protected hash(seed: number): number {
    const number = Math.sin(seed * 127.1 + 311.7) * 43758.5453;
    return number - Math.floor(number);
  }

  protected sparkle(x: number, y: number, radius: number, color: string): void {
    this.polygon([x, y - radius, x + radius * 0.25, y - radius * 0.25, x + radius, y,
      x + radius * 0.25, y + radius * 0.25, x, y + radius, x - radius * 0.25, y + radius * 0.25,
      x - radius, y, x - radius * 0.25, y - radius * 0.25], color);
  }

  protected sprite(rows: string[], palette: Record<string, string>, x: number, y: number, unit = 1): void {
    for (let row = 0; row < rows.length; row++) {
      for (let column = 0; column < rows[row].length; column++) {
        const color = palette[rows[row][column]];
        if (color) this.rect(x + column * unit, y + row * unit, unit, unit, color);
      }
    }
  }
}
