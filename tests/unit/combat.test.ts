import { expect, it } from 'vitest';
import { Game } from '../../src/core/game';
import { grantPower } from '../../src/core/powers';
import { EMPTY_INPUT, type EnemyKind, type Level } from '../../src/core/types';
const arena=(kind:EnemyKind='walker',hp=1):Level=>({id:'test',name:'arena',world:1,stage:1,width:1800,height:540,time:300,spawn:{x:64,y:414},checkpoint:{x:900,y:414},exit:{x:1700,y:448},platforms:[{id:'g',kind:'ground',x:0,y:448,w:1800,h:100}],coins:[],enemies:[{id:'e',kind,x:180,y:420,w:28,h:28,patrol:[160,600],hp}],items:[],hazards:[],hints:[]});
const run=(g:Game,n:number,ability=false)=>{for(let i=0;i<n;i++)g.update(1/120,{...EMPTY_INPUT,ability});};
const stomp=(g:Game)=>{const e=g.enemies[0];g.player.x=e.x-3;g.player.y=e.y-g.player.h-2;g.player.vy=400;g.player.grounded=false;run(g,2);};
it('contato lateral causa derrota; pisão vindo de cima derrota inimigo',()=>{
 const g=new Game([arena()]);g.player.invulnerable=0;g.player.x=176;run(g,1);expect(g.status).toBe('dead');expect(g.lives).toBe(4);
 const h=new Game([arena()]);stomp(h);expect(h.enemies[0].alive).toBe(false);expect(h.player.vy).toBeLessThan(0);
});
it('poder absorve dano e invulnerabilidade evita dano repetido',()=>{
 const g=new Game([arena()]);grantPower(g,'grow');expect(g.player.h).toBe(46);g.player.invulnerable=0;g.hurt();expect(g.player.power).toBe('small');expect(g.lives).toBe(5);g.hurt();expect(g.lives).toBe(5);
});
it('crescimento adia expansão física enquanto há um teto baixo',()=>{
 const l=arena();l.platforms.push({id:'roof',kind:'brick',x:50,y:375,w:90,h:32});const g=new Game([l]);run(g,20);grantPower(g,'grow');expect(g.player.power).toBe('grown');expect(g.player.h).toBe(30);g.player.x=250;run(g,2);expect(g.player.h).toBe(46);expect(g.player.y+g.player.h).toBe(448);
});
it('casco recolhe, desliza e atinge outro inimigo',()=>{
 const l=arena('shell');l.enemies.push({id:'other',kind:'walker',x:280,y:420,w:28,h:28,patrol:[270,600]});const g=new Game([l]);stomp(g);expect(g.enemies[0].state).toBe('shell');g.player.x=70;run(g,100);stomp(g);expect(g.enemies[0].state).toBe('slide');g.player.x=70;run(g,80);expect(g.enemies[1].alive).toBe(false);
});
it('armadura resiste ao primeiro pisão',()=>{
 const g=new Game([arena('armored',2)]);stomp(g);expect(g.enemies[0].health).toBe(1);expect(g.enemies[0].alive).toBe(true);g.player.x=70;run(g,100);stomp(g);expect(g.enemies[0].alive).toBe(false);
});
it('flor permite projéteis que derrotam inimigos e expiram',()=>{
 const g=new Game([arena()]);grantPower(g,'fire');run(g,55,true);expect(g.enemies[0].alive).toBe(false);run(g,400);expect(g.projectiles).toHaveLength(0);
});
it('estrela dá imunidade temporária e pausa preserva duração',()=>{
 const g=new Game([arena()]);grantPower(g,'star');g.player.invulnerable=0;g.hurt();expect(g.lives).toBe(5);g.player.x=180;run(g,1);expect(g.enemies[0].alive).toBe(false);const star=g.player.star;g.pause();run(g,100);expect(g.player.star).toBe(star);g.resume();run(g,1500);expect(g.player.star).toBe(0);
});
it('atirador dispara ao detectar jogador na região',()=>{
 const g=new Game([arena('shooter')]);run(g,270);expect(g.projectiles.some(s=>s.hostile)).toBe(true);expect(g.events.some(e=>e.type==='shot')).toBe(true);
});
