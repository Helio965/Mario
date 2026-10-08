import './style.css';
import { Game } from './core/game';
import { achievementsFor } from './core/progression';
import { Input } from './systems/input';
import { AudioSystem } from './systems/audio';
import { createTouchControls } from './systems/touch';
import { loadSave, writeSave, resetSave, completeLevel, type Settings } from './systems/save';
import { Renderer } from './render/renderer';
import { Interface } from './ui/interface';
import { LEVELS } from './data/levels';
const game = new Game();
const input = new Input();
const audio=new AudioSystem();
const canvas=document.querySelector<HTMLCanvasElement>('#game')!;
canvas.tabIndex=0;
const renderer = new Renderer(canvas);
let save=loadSave(), active=false, pauseHeld=false, lastStatus=game.status;
let persistenceWarning=false;
const shownHints=new Set<string>();
function persist() {
  if(!writeSave(save)&&!persistenceWarning) {persistenceWarning=true;ui.toast('O navegador bloqueou o salvamento. Seu progresso vale nesta sessão.');}
  ui.setSave(save);
}
function applySettings(settings:Settings) {
  save={...save,settings};renderer.effects=settings.effects;audio.setVolumes(settings.music,settings.sfx);persist();
}
function menu() {active=false;input.clear();game.pause();audio.pause(false);audio.menu();renderer.backdrop(LEVELS[save.unlocked].world);}
const ui = new Interface(document.querySelector<HTMLElement>('#ui')!,save,{
  play(index) {
    if(index<0||index>save.unlocked) return;
    if(active&&game.status==='complete'&&index===game.levelIndex+1) game.next();else game.start(index);
    active=true;input.clear();audio.unlock();audio.pause(false);audio.setWorld(game.level.world);pauseHeld=false;lastStatus=game.status;shownHints.clear();ui.hide();ui.update(game);canvas.focus({preventScroll:true});
  },
  resume() {game.resume();input.clear();ui.hide();canvas.focus({preventScroll:true});},
  restart() {game.start(game.levelIndex);active=true;input.clear();shownHints.clear();lastStatus=game.status;ui.hide();canvas.focus({preventScroll:true});},
  menu,
  updateSettings:applySettings,
  reset() {menu();save=resetSave();renderer.effects=save.settings.effects;audio.setVolumes(save.settings.music,save.settings.sfx);persist();},
});
renderer.effects=save.settings.effects;
audio.setVolumes(save.settings.music,save.settings.sfx);
const touch=createTouchControls();input.bindTouch(touch);
const touchDevice=matchMedia('(pointer: coarse)').matches||navigator.maxTouchPoints>0;
window.addEventListener('pointerdown',()=>audio.unlock(),{passive:true});
window.addEventListener('keydown',()=>audio.unlock());
window.addEventListener('pagehide',e=>{if(!e.persisted)audio.dispose();else audio.pause(true);});
if(import.meta.env.DEV) Object.assign(window,{__lume:{game,input,ui,audio,get save(){return save;}}});
function suspend() {
  input.clear();
  if(active&&game.status==='playing') {game.pause();ui.show('pause',game);}
}
window.addEventListener('blur',suspend);
document.addEventListener('visibilitychange',()=>{if(document.hidden)suspend();});
let previous=performance.now();
function frame(now:number) {
  const dt=Math.min((now-previous)/1000,0.25);previous=now;
  const state=input.read();
  if(active) {
    if(state.pause&&!pauseHeld) {
      if(game.status==='paused') {game.resume();ui.hide();canvas.focus({preventScroll:true});}
      else if(game.status==='playing') {game.pause();ui.show('pause',game);}
    }
    pauseHeld=state.pause;
    game.update(dt,state);
    for(const event of game.events.splice(0)) {
      audio.effect(event.type);
      if(event.text) ui.toast(event.text);
      if(event.type==='secret'&&!save.achievements.includes('secret-path')) {save={...save,achievements:[...save.achievements,'secret-path']};persist();}
      if(event.type==='complete') {
        save=completeLevel(save,game.levelIndex,event.value??0,game.foundRelic,game.level.id);
        save.achievements=[...new Set([...save.achievements,...achievementsFor(save.completed,save.relics)])];persist();ui.show('complete',game);
      }
    }
    if(game.status==='gameover'&&lastStatus!=='gameover') ui.show('gameover',game);
    if(game.status==='playing') for(const hint of game.level.hints) {
      const key=`${hint.x}:${hint.text}`;
      if(Math.abs(game.player.x-hint.x)<70&&!shownHints.has(key)) {shownHints.add(key);ui.toast(hint.text);}
    }
    lastStatus=game.status;
    audio.pause(game.status==='paused');
    audio.setWorld(game.level.world,game.enemies.some(e=>e.kind==='boss'&&e.alive&&Math.abs(e.x-game.player.x)<800));
    renderer.render(game,now/1000);ui.update(game);
  } else renderer.backdrop(LEVELS[save.unlocked].world);
  touch.hidden=!active||game.status!=='playing'||!(touchDevice||save.settings.touch);
  touch.querySelector<HTMLButtonElement>('[data-touch="ability"]')!.disabled=game.player.power!=='fire';
  requestAnimationFrame(frame);
}
requestAnimationFrame(frame);
