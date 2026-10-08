import { expect,it } from 'vitest';
import { Game } from '../../src/core/game';
import { LEVELS } from '../../src/data/levels';
import { achievementsFor } from '../../src/core/progression';
it('próxima fase exige vitória e preserva vidas, moedas e pontuação da campanha',()=>{
 const g=new Game();expect(g.next()).toBe(false);g.score=500;g.coinsTotal=5;g.lives=4;g.finish();const score=g.score;expect(g.next()).toBe(true);expect(g.levelIndex).toBe(1);expect(g.score).toBe(score);expect(g.levelStartScore).toBe(score);expect(g.coinsTotal).toBe(5);expect(g.lives).toBe(4);
 g.load(14);g.finish();expect(g.next()).toBe(false);
});
it('conquistas são derivadas de fases concluídas e relíquias reais',()=>{
 expect(achievementsFor([],[])).toEqual([]);expect(achievementsFor(['1-1'],[])).toEqual(['first-clear']);expect(achievementsFor(['1-1','1-2','1-3'],[])).toContain('world-1');
 const ids=LEVELS.map(l=>l.id);const achievements=achievementsFor(ids,ids);expect(achievements).toContain('all-clear');expect(achievements).toContain('relic-hunter');expect(achievements).toHaveLength(8);
});
