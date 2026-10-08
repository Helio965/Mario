import { describe, expect, it } from 'vitest';
import { LEVELS } from '../../src/data/levels';
import { playCampaignRoute } from '../helpers/route-player';

describe('travessia da campanha por entradas normais', () => {
  for (const level of LEVELS) {
    it(`${level.id} ${level.name}: chega à saída com inimigos e perigos ativos`, () => {
      const originalMap = JSON.stringify(level);
      // Walking on the mountain's slippery terraces leaves braking distance.
      const route = playCampaignRoute(level, 100, { run: level.id !== '3-2' });
      const details = JSON.stringify({ status: route.game.status, lives: route.game.lives, deaths: route.deaths, powers: route.powers, bossHits: route.bossHits, incidents: route.incidents, tail: route.samples.slice(-16) }, null, 2);
      expect(route.game.status, details).toBe('complete');
      expect(route.game.checkpointReached, details).toBe(true);
      expect(route.game.enemies.filter(e => e.kind === 'boss' && e.alive), details).toHaveLength(0);
      expect(route.game.lives, details).toBeGreaterThan(0);
      expect(route.game.coinsTotal, details).toBeGreaterThan(0);
      expect(route.powers, details).toBeGreaterThan(0);
      // These two harder routes exercise ordinary checkpoint respawns. Every
      // other route currently finishes without spending a life.
      const deathBudget = level.id === '4-2' ? 2 : level.id === '5-3' ? 1 : 0;
      expect(route.deaths, details).toBeLessThanOrEqual(deathBudget);
      expect(JSON.stringify(level), 'o condutor preserva todos os dados do mapa').toBe(originalMap);
    });
  }
});
