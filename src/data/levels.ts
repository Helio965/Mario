import type { EnemyKind, ItemKind, Level, PlatformKind, Theme } from '../core/types';

export const THEMES: Theme[] = [
  { name: 'Reino Verde', subtitle: 'Colinas, canais e pomares', sky: '#88d5ed', far: '#70ad91', near: '#438568', ground: '#a97743', top: '#75bc4b', accent: '#ffda6b', weather: 'none' },
  { name: 'Deserto Dourado', subtitle: 'Dunas e templos sob o sol', sky: '#f8ce8a', far: '#daae77', near: '#bb8b60', ground: '#be8652', top: '#edbc6e', accent: '#79d2c2', weather: 'sand' },
  { name: 'Montanhas Geladas', subtitle: 'Encostas, pontes e neve', sky: '#b9d9ef', far: '#92b2cc', near: '#6989aa', ground: '#7f95ac', top: '#e0f7ff', accent: '#ffd775', weather: 'snow' },
  { name: 'Floresta Encantada', subtitle: 'Copas luminosas e ruínas', sky: '#223a49', far: '#2e5260', near: '#24564b', ground: '#705847', top: '#66b887', accent: '#dcc178', weather: 'spores' },
  { name: 'Fortaleza Vulcânica', subtitle: 'Basalto, brasa e a última luz', sky: '#302637', far: '#594050', near: '#7b4742', ground: '#53424b', top: '#a37666', accent: '#ffb45d', weather: 'embers' },
];

// Coordinates describe solid surfaces. Spawn, checkpoint and pipe destinations
// describe the player's top-left; exit.y is the bottom of the exit flag.
// Maps are deliberately composed below, while these helpers only avoid repeating
// the shape of a rectangle, a row of coins, or an enemy declaration.
const counts = new Map<string, number>();
const uid = (l: Level, kind: string) => {
  const key = `${l.id}-${kind}`;
  const n = (counts.get(key) ?? 0) + 1;
  counts.set(key, n);
  return `${key}-${n}`;
};
const make = (world: number, stage: number, name: string, width: number, checkpointX: number, checkpointY = 414): Level => ({
  id: `${world}-${stage}`, world, stage, name, width, height: 540,
  time: 260 + Math.round(width / 30), spawn: { x: 72, y: 414 },
  checkpoint: { x: checkpointX, y: checkpointY }, exit: { x: width - 150, y: 448 },
  platforms: [], coins: [], enemies: [], items: [], hazards: [], hints: [],
});
const p = (l: Level, kind: PlatformKind, x: number, y: number, w = 40, h = 24, reward?: ItemKind | 'coin') => {
  const platform = { id: uid(l, kind), kind, x, y, w, h, ...(reward ? { reward } : {}) };
  l.platforms.push(platform);
  return platform;
};
const g = (l: Level, x: number, w: number, y = 448, kind: 'ground' | 'ice' = 'ground') => p(l, kind, x, y, w, 540 - y + 60);
const row = (l: Level, x: number, y: number, count: number, spacing = 34) => {
  for (let i = 0; i < count; i++) l.coins.push({ id: uid(l, 'coin'), x: x + i * spacing, y, w: 16, h: 20 });
};
const arc = (l: Level, x: number, y: number, count = 5, spacing = 30) => {
  for (let i = 0; i < count; i++) l.coins.push({ id: uid(l, 'coin'), x: x + i * spacing, y: y - Math.sin(Math.PI * i / (count - 1)) * 32, w: 16, h: 20 });
};
const relic = (l: Level, x: number, y: number) => l.coins.push({ id: uid(l, 'relic'), x, y, w: 22, h: 24, special: true });
const enemy = (l: Level, kind: EnemyKind, x: number, groundY: number, left: number, right: number, hp?: number) => {
  const w = kind === 'boss' ? 62 : kind === 'armored' ? 34 : 28;
  const h = kind === 'boss' ? 64 : kind === 'flyer' ? 24 : kind === 'armored' ? 32 : 28;
  l.enemies.push({ id: uid(l, kind), kind, x, y: groundY - h, w, h, patrol: [left, right], ...(hp ? { hp } : {}) });
};
const item = (l: Level, kind: ItemKind, x: number, y = 420) => l.items.push({ id: uid(l, kind), kind, x, y, w: 24, h: 24 });
const moving = (l: Level, x: number, y: number, w: number, axis: 'x' | 'y', range: number, speed: number, phase = 0) => {
  const platform = p(l, 'moving', x, y, w, 18);
  Object.assign(platform, { motion: { axis, range, speed, phase } });
};
const spike = (l: Level, x: number, w = 48, groundY = 448) => l.hazards.push({ kind: 'spikes', x, y: groundY - 14, w, h: 14 });
const lava = (l: Level, x: number, w: number) => l.hazards.push({ kind: 'lava', x, y: 474, w, h: 66 });
const orbit = (l: Level, x: number, y: number, range: number, speed: number) => l.hazards.push({ kind: 'moving', x, y, w: 26, h: 26, range, speed });
const hint = (l: Level, x: number, text: string) => l.hints.push({ x, text });
const secret = (l: Level, entryX: number, roomX: number, reward: ItemKind = 'heart') => {
  // The chamber is entered and left by pipes; no unreachable climb is required.
  const enter = p(l, 'pipe', entryX, 400, 56, 48);
  const back = { x: entryX + 72, y: 402 };
  Object.assign(enter, { destination: { x: roomX + 24, y: 126 }, returnPoint: back });
  p(l, 'brick', roomX, 176, 298, 20);
  const leave = p(l, 'pipe', roomX + 226, 144, 56, 32);
  Object.assign(leave, { destination: back, returnPoint: { x: roomX + 24, y: 126 } });
  row(l, roomX + 64, 132, 4, 34);
  relic(l, roomX + 178, 130);
  item(l, reward, roomX + 128, 146);
};

// WORLD 1 — gentle gaps first; route choice and block discovery follow.
const meadow = make(1, 1, 'Primeiros Passos', 3200, 1510);
g(meadow, 0, 1040); g(meadow, 1140, 780); g(meadow, 2040, 1160);
row(meadow, 200, 410, 6); arc(meadow, 1010, 374, 5, 32); arc(meadow, 1900, 374, 6, 30);
p(meadow, 'question', 410, 350, 40, 28, 'grow'); p(meadow, 'brick', 450, 350, 40, 28);
p(meadow, 'question', 490, 350, 40, 28, 'coin'); p(meadow, 'question', 570, 350, 40, 28, 'heart');
p(meadow, 'brick', 780, 382, 92, 22); row(meadow, 796, 347, 2);
enemy(meadow, 'walker', 700, 448, 650, 900); enemy(meadow, 'walker', 1250, 448, 1220, 1390);
p(meadow, 'brick', 1680, 374, 100, 22); p(meadow, 'brick', 1830, 306, 112, 22);
row(meadow, 1700, 340, 3); row(meadow, 1840, 270, 3);
secret(meadow, 2250, 2500, 'heart'); p(meadow, 'hidden', 2460, 344, 40, 24, 'star');
enemy(meadow, 'shell', 2640, 448, 2590, 2800); row(meadow, 2840, 410, 6);
hint(meadow, 120, 'Ande, pule e siga as moedas.'); hint(meadow, 470, 'Bata por baixo nos blocos com luz.');
hint(meadow, 1000, 'Corra para cruzar o vão.'); hint(meadow, 2190, 'Sobre o cano, pressione ↓ para explorar.');

export const LEVELS: Level[] = [meadow];
