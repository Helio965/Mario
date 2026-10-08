import { expect, it } from 'vitest';
import { Game } from '../../src/core/game';
import { EMPTY_INPUT } from '../../src/core/types';
import { LEVELS } from '../../src/data/levels';
// Drives the same public input path as the browser; never teleports the player.
it('percorre a primeira fase usando corrida e saltos reais',()=>{
 const g=new Game([LEVELS[0]]);let hold=0,cooldown=0;
 for(let tick=0;tick<120*70&&g.status!=='complete';tick++) {
  hold=Math.max(0,hold-1/120);cooldown=Math.max(0,cooldown-1/120);const p=g.player;
  if(p.grounded&&cooldown===0) {
   const wall=g.platforms.some(s=>s.alive&&s.kind!=='hidden'&&s.x>=p.x+p.w-2&&s.x<p.x+p.w+74&&s.y<p.y+p.h-3&&s.y+s.h>p.y);
   const groundAhead=g.platforms.some(s=>s.alive&&s.kind!=='hidden'&&p.x+p.w+12>=s.x&&p.x+p.w+12<=s.x+s.w&&s.y>=p.y+p.h-8&&s.y<=p.y+p.h+80);
   if(wall||!groundAhead) {hold=0.4;cooldown=0.55;}
  }
  g.update(1/120,{...EMPTY_INPUT,right:true,run:true,jump:hold>0});
 }
 expect(g.status,`parou em x=${g.player.x} vidas=${g.lives}`).toBe('complete');expect(g.lives).toBe(5);expect(g.coinsTotal).toBeGreaterThan(0);expect(g.checkpointReached).toBe(true);
});
