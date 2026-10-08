import { describe, expect, it } from 'vitest';
import { Game } from '../../src/core/game';
import { EMPTY_INPUT, type InputState, type Level } from '../../src/core/types';
const ARENA: Level = {id:'test',name:'arena',world:1,stage:1,width:2400,height:540,time:300,spawn:{x:64,y:414},checkpoint:{x:1100,y:414},exit:{x:2280,y:448},platforms:[{id:'floor',kind:'ground',x:0,y:448,w:2400,h:92},{id:'wall',kind:'brick',x:480,y:368,w:128,h:80}],coins:[],enemies:[],items:[],hazards:[],hints:[]};
const arena = () => new Game([ARENA]);
const run = (g: Game, seconds: number, input: Partial<InputState> = {}) => { for(let i=0;i<Math.round(seconds*120);i++) g.update(1/120, { ...EMPTY_INPUT, ...input }); };
describe('movimentação em passo fixo', () => {
  it('aterra sem atravessar o solo e colide com a parede', () => {
    const g = arena(); run(g, 1); expect(g.player.y+g.player.h).toBe(448);
    run(g, 3, { right: true, run: true }); expect(g.player.x+g.player.w).toBeLessThanOrEqual(480); expect(g.player.grounded).toBe(true);
  });
  it('salto pressionado alcança maior altura que toque breve', () => {
    const heights = [0.025,0.5].map(hold => { const g = arena(); run(g,0.1); let min=g.player.y; for(let i=0;i<90;i++) { g.update(1/120,{...EMPTY_INPUT,jump:i/120<hold}); min=Math.min(min,g.player.y); } return min; });
    expect(heights[1]).toBeLessThan(heights[0]-40);
  });
  it('mantém o mesmo resultado a 30, 60 e 144 Hz', () => {
    const positions = [30,60,144].map(hz => { const g=arena(); for(let i=0;i<hz*1;i++) g.update(1/hz,{...EMPTY_INPUT,right:true}); return g.player.x; });
    expect(Math.max(...positions)-Math.min(...positions)).toBeLessThan(2);
  });
  it('pausa congela posição e cronômetro', () => {
    const g=arena(); run(g,0.5); const t=g.time; const x=g.player.x; g.pause(); run(g,2,{right:true}); expect(g.player.x).toBe(x); expect(g.time).toBe(t);
  });
  it('faz buffer de salto antes de tocar o chão', () => {
    const level: Level={...ARENA,spawn:{x:64,y:400}}; const g=new Game([level]);
    g.player.vy=240; g.update(1/120,{...EMPTY_INPUT,jump:true}); run(g,0.15,{jump:true}); expect(g.player.vy).toBeLessThan(0);
  });
});
