import type { Coin, Enemy, Item, Player } from '../core/types';
import { GOLD, INK, PixelPainter } from './painter';

/** Handmade matrix sprites with independent animated limbs and silhouettes. */
export class Sprites extends PixelPainter {
  public coin(coin: Coin): void {
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

  public item(item: Item): void {
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

  public player(player: Player): void {
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
      T: '#62ccb9', J: player.power === 'fire' ? '#d98a62' : '#ddc394',
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
    this.limb(6, 17, backLeg, airborne ? 3 : 5, '#355463', '#694e51');
    this.limb(10, 17, frontLeg, airborne ? 6 : 5, '#4f7c86', '#8d6260');
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

  public enemy(enemy: Enemy): void {
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
}
