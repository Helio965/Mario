import { EMPTY_INPUT, type InputState } from '../core/types';
const KEYS: Record<string, keyof InputState> = { KeyA: 'left', ArrowLeft: 'left', KeyD: 'right', ArrowRight: 'right', Space: 'jump', KeyW: 'jump', ArrowUp: 'jump', ShiftLeft: 'run', ShiftRight: 'run', KeyJ: 'ability', KeyS: 'down', ArrowDown: 'down', Escape: 'pause' };
export class Input {
  private keys = new Set<string>();
  private pointers = new Map<number,{action:keyof InputState;button:HTMLButtonElement}>();
  constructor() {
    window.addEventListener('keydown', e => { if (KEYS[e.code] && (e.code==='Escape'||!(e.target instanceof HTMLElement && e.target.closest('input, textarea, select, button')))) { e.preventDefault(); if(!e.repeat)this.keys.add(e.code); } });
    window.addEventListener('keyup', e => this.keys.delete(e.code));
    window.addEventListener('blur', () => this.clear());
    window.addEventListener('pointerup',e=>this.release(e.pointerId));
    window.addEventListener('pointercancel',e=>this.release(e.pointerId));
  }
  bindTouch(root:HTMLElement) {
    root.addEventListener('pointerdown',e=>{
      const button=(e.target as Element).closest<HTMLButtonElement>('[data-touch]');
      const action=button?.dataset.touch as keyof InputState|undefined;
      if(!button||button.disabled||!action||!(action in EMPTY_INPUT)) return;
      e.preventDefault();this.pointers.set(e.pointerId,{action,button});button.classList.add('pressed');
      try {button.setPointerCapture(e.pointerId);} catch { /* Synthetic test pointers have no active capture. */ }
    });
    root.addEventListener('lostpointercapture',e=>this.release(e.pointerId));
  }
  private release(id:number) {
    const pointer=this.pointers.get(id);this.pointers.delete(id);
    if(pointer&&!Array.from(this.pointers.values()).some(p=>p.button===pointer.button)) pointer.button.classList.remove('pressed');
  }
  clear() { this.keys.clear();for(const p of this.pointers.values())p.button.classList.remove('pressed');this.pointers.clear(); }
  read(): InputState {
    const state = { ...EMPTY_INPUT };
    for (const key of this.keys) if (KEYS[key]) state[KEYS[key]] = true;
    for(const p of this.pointers.values()) state[p.action]=true;
    const pads=navigator.getGamepads?.()??[];
    for(const pad of pads) {
      if(!pad||!pad.connected) continue;
      const pressed=(i:number)=>!!pad.buttons[i]?.pressed;
      state.left ||= pad.axes[0]<-0.3||pressed(14);state.right ||= pad.axes[0]>0.3||pressed(15);
      state.jump ||= pressed(0)||pressed(12);state.run ||= pressed(2)||pressed(7);
      state.ability ||= pressed(1);state.down ||= pad.axes[1]>0.5||pressed(13);state.pause ||= pressed(9);
    }
    return state;
  }
}
