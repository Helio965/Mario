export function createTouchControls():HTMLElement {
  const root=document.createElement('div');root.id='touch-controls';root.className='touch-controls';root.hidden=true;
  root.setAttribute('aria-label','Controles de toque');
  const button=(action:string,icon:string,label:string)=>`<button type="button" data-touch="${action}" aria-label="${label}"><span aria-hidden="true">${icon}</span><small>${label}</small></button>`;
  root.innerHTML=`<div>${button('left','◀','Esquerda')}${button('right','▶','Direita')}${button('down','↓','Cano')}</div><div>${button('run','»','Correr')}${button('ability','✦','Habilidade')}${button('jump','↑','Pular')}</div>`;
  const app=document.querySelector('#app')!;
  app.insertBefore(root,app.querySelector('.site-footer'));
  return root;
}
