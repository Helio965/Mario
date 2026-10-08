import { HEIGHT, PixelPainter, WIDTH } from './painter';

/** Five frontiers, each with distinct silhouettes, flora and weather. */
export class Background extends PixelPainter {
  public sky(): void {
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

  public landscape(): void {
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

  public shrub(x: number, y: number, seed: number): void {
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

  public weather(foreground: boolean): void {
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

  public vignette(): void {
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
