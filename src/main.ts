import { Game } from './core/game';
import { Input } from './systems/input';
import { Renderer } from './render/renderer';
const game = new Game();
const input = new Input();
const renderer = new Renderer(document.querySelector<HTMLCanvasElement>('#game')!);
const ui = document.querySelector<HTMLElement>('#ui')!;
ui.innerHTML = '<h1>Lume — As Cinco Fronteiras</h1><p>A/D: andar · Espaço: saltar · Shift: correr · Esc: pausar</p>';
let previous = performance.now(), pauseHeld = false;
function frame(now: number) {
  const state = input.read();
  if(state.pause && !pauseHeld) game.status === 'paused' ? game.resume() : game.pause();
  pauseHeld = state.pause;
  game.update((now-previous)/1000,state); previous=now;
  renderer.render(game,now/1000); requestAnimationFrame(frame);
}
requestAnimationFrame(frame);
