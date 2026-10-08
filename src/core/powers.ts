import type { Game } from './game';
import type { InputState, ItemKind } from './types';
import { GRAVITY, moveBody, overlaps } from './physics';
import { burst } from './interactions';
import { hitEnemy } from './enemies';
export function grantPower(game:Game,kind:ItemKind) {
  const p=game.player;
  if(kind==='grow'&&p.power==='small') p.power='grown';
  else if(kind==='fire') p.power='fire';
  else if(kind==='star') p.star=12;
  else if(kind==='heart') {game.lives=Math.min(99,game.lives+1);game.events.push({type:'life',text:'Uma vida extra!'});}
  game.score+=250;game.events.push({type:'power',text:kind==='grow'?'Mais forte!':kind==='fire'?'Chama ativa — pressione J':kind==='star'?'12 segundos de invencibilidade':undefined});burst(game,p.x,p.y,'#73ffe1');
  growSafely(game);
}
function growSafely(game:Game) {
  const p=game.player;
  if(p.power==='small'||p.h===46) return;
  const big={x:p.x,y:p.y-(46-p.h),w:p.w,h:46};
  if(!game.platforms.some(s=>s.alive&&(s.kind!=='hidden'||s.used)&&overlaps(big,s))) {p.y=big.y;p.h=46;}
}
export function updatePowers(game:Game,dt:number,input:InputState) {
  const p=game.player;growSafely(game);
  for(const i of game.items) {
    if(!i.alive) continue;
    i.vy=Math.min(700,i.vy+GRAVITY*dt); const before=i.vx; moveBody(i,game.platforms,dt);
    if(before&&i.vx===0) i.vx=-before;
    if(i.y>game.level.height+80) i.alive=false;
    if(overlaps(p,i)) {i.alive=false;grantPower(game,i.kind);}
  }
  if(input.ability&&p.power==='fire'&&p.shootCooldown<=0) {
    game.projectiles.push({x:p.x+(p.facing>0?p.w:-10),y:p.y+p.h*0.4,w:10,h:10,vx:p.facing*450,vy:-90,hostile:false,life:2.4,alive:true});
    p.shootCooldown=0.3;game.events.push({type:'shot'});
  }
  for(const s of game.projectiles) {
    if(!s.alive) continue;
    s.life-=dt;if(s.life<=0) {s.alive=false;continue;}
    if(!s.hostile) s.vy+=600*dt;
    const before=s.vx; const collision=moveBody(s,game.platforms,dt);
    if(before!==0&&s.vx===0) s.alive=false;
    if(collision.grounded) {if(s.hostile)s.alive=false;else s.vy=-200;}
    if(s.hostile) {if(overlaps(s,p)) {game.hurt();s.alive=false;}}
    else for(const e of game.enemies) if(e.alive&&overlaps(s,e)) {hitEnemy(game,e);s.alive=false;burst(game,s.x,s.y,'#ffb35c',5);break;}
  }
  game.items=game.items.filter(i=>i.alive);game.projectiles=game.projectiles.filter(s=>s.alive);
  for(const h of game.level.hazards) {
    const hazard=h.kind==='moving'?{...h,x:h.x+Math.sin(game.elapsed*(h.speed??1))*(h.range??30)}:h;
    if(overlaps(p,hazard)) {if(h.kind==='lava'||h.kind==='water')game.die();else game.hurt();}
  }
}
