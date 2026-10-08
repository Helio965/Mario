import type { Game } from './game';
import type { Enemy } from './types';
import { GRAVITY, moveBody, overlaps } from './physics';
import { burst } from './interactions';
import { updateBoss } from './bosses';
export function hitEnemy(game: Game, e: Enemy, damage = 1): boolean {
  if(!e.alive||e.hitTimer>0||(e.kind==='boss'&&e.state!=='shell')) return false;
  e.health-=damage; e.hitTimer=0.65; burst(game,e.x+e.w/2,e.y,'#ffdc87');
  if(e.health<=0) {
    e.alive=false; game.score+=e.kind==='boss'?5000:200;
    game.events.push({type:e.kind==='boss'?'boss':'stomp',text:e.kind==='boss'?'Guardião derrotado!':undefined});
    if(e.kind==='boss') {game.shake=0.3;burst(game,e.x,e.y,'#73ffe1',30);}
  } else game.events.push({type:'stomp'});
  return true;
}
export function updateEnemies(game:Game,dt:number) {
  const player=game.player;
  for(const e of game.enemies) {
    if(!e.alive) continue;
    const oldTimer=e.timer; e.timer+=dt; e.hitTimer=Math.max(0,e.hitTimer-dt);
    if(e.kind==='flyer') {
      e.vx=e.facing*(72+game.level.world*6);e.x+=e.vx*dt;e.y=e.originY+Math.sin(e.timer*2.2)*38;
    } else {
      if(e.kind==='boss') {
        updateBoss(game,e,oldTimer);
      } else if(e.kind==='shooter') {
        e.vx=0;e.facing=player.x<e.x?-1:1;
        if(Math.floor(e.timer/2.2)>Math.floor(oldTimer/2.2)&&Math.abs(player.x-e.x)<650) {
          game.projectiles.push({x:e.x+e.w/2,y:e.y+8,w:12,h:12,vx:e.facing*180,vy:0,hostile:true,life:3.5,alive:true});
          game.events.push({type:'shot'});
        }
      } else e.vx=e.state==='shell'?0:e.facing*(e.state==='slide'?360:e.kind==='armored'?44:55+game.level.world*7);
      e.vy=Math.min(850,e.vy+GRAVITY*dt);
      const before=e.vx;
      const hit=moveBody(e,game.platforms.filter(s=>s.kind!=='hidden'||s.used),dt);
      e.grounded=hit.grounded;
      if(before!==0&&e.vx===0) e.facing*=-1;
      if(e.grounded&&e.state!=='slide'&&e.kind!=='boss'&&e.kind!=='shooter') {
        const ahead={x:e.facing>0?e.x+e.w+5:e.x-7,y:e.y+e.h,w:2,h:7};
        if(!game.platforms.some(s=>s.alive&&(s.kind!=='hidden'||s.used)&&overlaps(ahead,s))) e.facing*=-1;
      }
    }
    if(e.x<e.patrol[0]) {e.x=e.patrol[0];e.facing=1;}
    if(e.x+e.w>e.patrol[1]) {e.x=e.patrol[1]-e.w;e.facing=-1;}
    if(e.y>game.level.height+80) {e.alive=false;continue;}
    if(e.state==='slide') {
      for(const other of game.enemies) if(other!==e&&other.alive&&overlaps(e,other)) hitEnemy(game,other,2);
    }
    if(!overlaps(player,e)) continue;
    if(player.star>0) {hitEnemy(game,e,2);continue;}
    const stomp=player.vy>0&&player.y+player.h<=e.y+Math.min(24,player.vy*dt+15);
    if(stomp) {
      player.vy=-390;player.y=e.y-player.h-1;player.grounded=false;player.standingOn=null;
      if(e.kind==='shell') {
        if(e.state==='walk'||e.state==='slide') {e.state='shell';e.vx=0;game.score+=100;game.events.push({type:'stomp'});}
        else {e.state='slide';e.facing=player.x+player.w/2<e.x+e.w/2?1:-1;e.vx=e.facing*360;game.events.push({type:'stomp'});}
      } else hitEnemy(game,e);
    } else if(e.kind==='shell'&&e.state==='shell') {
      e.state='slide';e.facing=player.x<e.x?1:-1;e.x+=e.facing*14;e.vx=e.facing*360;
    } else game.hurt();
  }
}
