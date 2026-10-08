import { overlaps } from './physics';
import type { Game } from './game';
import type { InputState, Platform } from './types';
export function burst(game: Game, x: number, y: number, color = '#ffe5a0', count = 10) {
  for(let i=0;i<count;i++) game.particles.push({x,y,vx:Math.cos(i*2.4)*85,vy:-50-Math.sin(i*1.7)*90,life:0.5+(i%3)*0.1,color,size:2+(i%2)*2});
}
export function updatePlatforms(game: Game, dt: number) {
  const p = game.player;
  for(const s of game.platforms) {
    s.bump = Math.max(0,s.bump-dt);
    const oldX=s.x,oldY=s.y;
    if(s.motion) {
      const wave=Math.sin(game.elapsed*s.motion.speed+(s.motion.phase??0))*s.motion.range;
      s.x=s.startX+(s.motion.axis==='x'?wave:0); s.y=s.startY+(s.motion.axis==='y'?wave:0);
    }
    s.dx=s.x-oldX; s.dy=s.y-oldY;
    if(p.standingOn===s.id && s.alive) { p.x+=s.dx; p.y+=s.dy; }
    if(s.kind==='crumble') {
      if(s.alive && p.standingOn===s.id) s.crumble+=dt;
      if(s.alive && s.crumble>0.65) { s.alive=false; s.respawn=3; burst(game,s.x+s.w/2,s.y,'#cdaa7c'); }
      if(!s.alive) { s.respawn-=dt; if(s.respawn<=0&&!overlaps(p,s)) {s.alive=true;s.crumble=0;} }
    }
  }
}
export function interactWorld(game: Game, input: InputState, heads: Platform[]) {
  const p=game.player;
  for(const block of heads) {
    if(block.bump>0) continue;
    block.bump=0.18;
    if((block.kind==='question'||block.kind==='hidden')&&!block.used) {
      block.used=true; game.events.push({type:'block',x:block.x,y:block.y});
      if(!block.reward||block.reward==='coin') collectCoin(game,block.x+block.w/2,block.y,false);
      else game.items.push({id:`item-${block.id}`,kind:block.reward,x:block.x+(block.w-24)/2,y:block.y-26,w:24,h:24,vx:55,vy:-100,alive:true});
    } else if(block.kind==='brick'&&p.power!=='small') { block.alive=false; game.score+=50; burst(game,block.x+block.w/2,block.y,'#cf8f60',14); game.events.push({type:'block'}); }
  }
  for(const coin of game.coins) {
    if(!coin.collected&&overlaps(p,coin)) { coin.collected=true; collectCoin(game,coin.x,coin.y,!!coin.special); }
  }
  if(!game.checkpointReached && p.x>=game.level.checkpoint.x && Math.abs(p.y-game.level.checkpoint.y)<100) {
    game.checkpointReached=true; game.events.push({type:'checkpoint',text:'Checkpoint ativado'}); burst(game,p.x,p.y,'#73ffe1');
  }
  if(input.down&&game.pipeCooldown<=0) {
    const pipe=game.platforms.find(s=>s.kind==='pipe'&&s.destination&&p.x+p.w>s.x&&p.x<s.x+s.w&&Math.abs(p.y+p.h-s.y)<10);
    if(pipe?.destination) { p.x=pipe.destination.x; p.y=pipe.destination.y; p.vx=0;p.vy=0; p.standingOn=null; game.pipeCooldown=0.8; game.camera.x=Math.max(0,Math.min(game.level.width-960,p.x-300)); game.camera.y=Math.max(0,Math.min(game.level.height-540,p.y-250)); game.events.push({type:'secret',text:'Uma passagem secreta!'}); burst(game,p.x,p.y,'#73ffe1'); }
  }
}
function collectCoin(game: Game,x:number,y:number,special:boolean) {
  if(special) { game.foundRelic=true; game.score+=1000; game.events.push({type:'relic',text:'Relíquia encontrada!'}); }
  else { game.coinsTotal++;game.score+=100;game.events.push({type:'coin'}); if(game.coinsTotal%100===0) {game.lives++;game.events.push({type:'life',text:'100 moedas: vida extra!'});} }
  burst(game,x,y,special?'#73ffe1':'#ffd36e',special?16:8);
}
