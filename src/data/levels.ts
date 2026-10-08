import type { Level, Theme } from '../core/types';
export const THEMES: Theme[] = [{ name: 'Reino Verde', subtitle: 'O início da jornada', sky: '#73c9dd', far: '#73ac99', near: '#3b936a', ground: '#946a4e', top: '#8ed05a', accent: '#ffe5a0', weather: 'none' }];
export const LEVELS: Level[] = [{
  id: '1-1', name: 'Laboratório de movimento', world: 1, stage: 1, width: 2400, height: 540, time: 300,
  spawn: { x: 64, y: 414 }, checkpoint: { x: 1100, y: 414 }, exit: { x: 2280, y: 448 },
  platforms: [{ id: 'floor', kind: 'ground', x: 0, y: 448, w: 2400, h: 92 }, { id: 'step', kind: 'brick', x: 480, y: 368, w: 128, h: 32 }],
  coins: [], enemies: [], items: [], hazards: [], hints: [{ x: 80, text: 'A / D para andar · Espaço para saltar · Shift para correr' }],
}];
