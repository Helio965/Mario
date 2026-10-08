import { EMPTY_INPUT, type InputState } from '../core/types';
const KEYS: Record<string, keyof InputState> = { KeyA: 'left', ArrowLeft: 'left', KeyD: 'right', ArrowRight: 'right', Space: 'jump', KeyW: 'jump', ArrowUp: 'jump', ShiftLeft: 'run', ShiftRight: 'run', KeyJ: 'ability', KeyS: 'down', ArrowDown: 'down', Escape: 'pause' };
export class Input {
  private keys = new Set<string>();
  constructor() {
    window.addEventListener('keydown', e => { if (KEYS[e.code] && !(e.target instanceof HTMLInputElement)) { e.preventDefault(); this.keys.add(e.code); } });
    window.addEventListener('keyup', e => this.keys.delete(e.code));
    window.addEventListener('blur', () => this.clear());
  }
  clear() { this.keys.clear(); }
  read(): InputState {
    const state = { ...EMPTY_INPUT };
    for (const key of this.keys) if (KEYS[key]) state[KEYS[key]] = true;
    return state;
  }
}
