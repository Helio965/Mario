# Auditoria inicial do projeto original (TypeScript)

**Commit de referência auditado:** `b40c39ca77026de4101817b8a8f7198f6e870ab9` (branch `main`, 8 de outubro de 2026, "docs: registrar validação remota e requisito de habilitar Pages").
**Branch de desenvolvimento da migração:** `claude/focused-pascal-hg2kgb` (criada a partir desse commit; o histórico é preservado e a branch `main` permanece intacta como cópia de segurança).
**Data da auditoria:** 3 de novembro de 2026.
**Ambiente usado:** Node 22.23.4 (o README pede Node 24, mas `engines` aceita ≥ 22.12 e tudo executou), npm 10.9.9, Python 3.12.3, pygame-ce 2.5.8.

## 1. Resumo executivo

O repositório contém **Lume — As Cinco Fronteiras**, um jogo de plataforma 2D para navegador com 6.873 linhas de TypeScript (3.620 em `src/`, 2.000 em testes, o restante em configuração). A simulação (`src/core`) é independente do DOM e bem testada; renderização (Canvas 2D), áudio (Web Audio), entrada (DOM/Gamepad API), interface (HTML/CSS) e salvamento (`localStorage`) dependem exclusivamente do navegador.

Resultados verificados nesta auditoria, no commit de referência:

| Verificação | Resultado |
| --- | --- |
| `npm ci --ignore-scripts` | OK (lockfile íntegro) |
| `npm run typecheck` (`tsc --noEmit`, `strict`) | 0 diagnósticos |
| `npm test` (Vitest) | **88/88 testes passaram** em 10 arquivos (2,4 s) |
| `npm run test:e2e` (Playwright, 15 testes) | **Não executado** nesta sessão: exige servidores Vite nas portas 5173/4173 e Chromium; a validação remota em `docs/VALIDACAO.md` registra 15/15 na execução de CI |
| Publicação no GitHub Pages | **Pendente/falha registrada** (HTTP 403 em `configure-pages`; o site nunca foi publicado) |
| Rotas de campanha (condutor por entradas normais) | 15/15 fases concluídas; 13 sem morte, 4-2 com duas mortes e 5-3 com uma (reproduzido localmente ao gerar os traces de ouro) |

O jogo **funciona** e é **completável**, mas o que existe é um protótipo sólido, não um jogo de qualidade comercial: inimigos de uma única função com `if/else`, cinco chefes com o mesmo padrão numérico, animação derivada da velocidade sem máquina de estados, arte procedural por retângulos e polígonos, sem diálogos, sem NPCs, sem localização, sem editor e sem medição de desempenho.

## 2. Como o jogo funciona hoje

1. `src/main.ts` instancia `Game`, `Input`, `AudioSystem`, `Renderer` e `Interface`, e roda um laço `requestAnimationFrame`.
2. A cada quadro, `Input.read()` produz um `InputState` (teclado + gamepad + toque, com "taps" retidos entre quadros para não perder pressionamentos curtos).
3. `Game.update(dt, input)` acumula o tempo real (limitado a 0,25 s) e executa `step(1/120)` quantas vezes couberem (passo fixo, simulação determinística).
4. Cada `step`: cronômetro, plataformas móveis/frágeis (`updatePlatforms`), movimento do jogador (`approach` para aceleração, corte de salto variável, gravidade, `moveBody` com resolução por eixo), interações (`interactWorld`: blocos, moedas, checkpoint, canos), inimigos (`updateEnemies` + `updateBoss`), poderes/itens/projéteis/perigos (`updatePowers`), saída de fase, partículas, animação e câmera.
5. `Game.events` acumula eventos (`jump`, `coin`, `hurt`…) que `main.ts` drena para o áudio, os avisos (toasts) e o salvamento.
6. `Renderer.render` desenha céu, paisagem em parallax, clima, plataformas, perigos, moedas, itens, inimigos, projéteis, jogador e partículas no canvas 960 × 540; a interface DOM mostra HUD, menus, mapa e configurações.

## 3. Inventário por componente

Estados: **Funcional**, **Parcialmente funcional**, **Incompleto**, **Inexistente**.

### 3.1 Núcleo da simulação (`src/core`, 1.003 linhas)

| Componente | Arquivo | Estado | Observações |
| --- | --- | --- | --- |
| Tipos e dados | `types.ts` (191) | Funcional | Interfaces planas; `Player.animation` com 8 estados; `GameEvent` com 14 tipos |
| Física básica | `physics.ts` (49) | Funcional | AABB, `approach`, `moveBody` resolve X e depois Y contra todas as plataformas vivas; blocos ocultos colidem só por baixo |
| Laço de jogo e jogador | `game.ts` (303) | Funcional | Passo fixo 1/120 s, coyote 0,1 s, buffer 0,12 s, salto variável por corte de `vy` a −190, gravidade 1550, impulso 590, terminal 850, câmera com antecipação `vx·0,15` e suavização exponencial |
| Interações | `interactions.ts` (144) | Funcional | Blocos `?`/ocultos (moeda ou item), tijolo quebra se não for pequeno, moedas/relíquias, checkpoint, canos com `destination`, plataformas móveis (seno) e frágeis (0,65 s / respawn 3 s) |
| Inimigos | `enemies.ts` (150) | Parcialmente funcional | Uma função com cadeia de `if` para 6 tipos; sem percepção real (atirador só testa |dx| < 650 px), sem estados além de `walk/shell/slide`, sem sinalização de ataque; casco deslizante atinge outros inimigos (bom) |
| Chefes | `bosses.ts` (31) | Parcialmente funcional | Os cinco guardiões usam **o mesmo** ciclo temporal (4,8 s → 3,8 s abaixo de metade da vida, abertura de 1,65 s → 1,1 s, carga 85 → 135 px/s, salto na fase 2 s, tiro em 2,7 s; mundo 5 dispara três vezes). Diferenças reais: PV (3–7) e desenho. Sem arenas próprias, telegraph, cinemáticas ou diálogos |
| Poderes | `powers.ts` (117) | Funcional | Crescimento, flor (projétil 450 px/s que quica), estrela 12 s, coração; itens com física; perigos (lava/água matam; espinhos/chama ferem); crescimento seguro sob teto |
| Progressão | `progression.ts` (18) | Funcional | 9 conquistas derivadas de fases concluídas e relíquias |

### 3.2 Dados (`src/data/levels.ts`, 732 linhas)

| Componente | Estado | Observações |
| --- | --- | --- |
| 15 fases, 5 temas | Funcional | 238 plataformas, 572 moedas (29 relíquias), 49 inimigos (5 chefes), 21 itens, 40 perigos, 46 dicas. Construídas por helpers (`g`, `p`, `row`, `arc`, `secret`…) com IDs sequenciais por fase. Canais de água do mundo 1 são gerados por código entre os trechos de chão |
| Formato declarativo | Incompleto | Dados vivem em código TS; não há JSON, esquema ou validador. **Nesta auditoria os dados foram exportados sem alteração para `data/levels/*.json`** usando o próprio módulo TS, o que elimina o risco de transcrição manual |

### 3.3 Renderização (`src/render`, 1.702 linhas)

| Componente | Arquivo | Estado | Observações |
| --- | --- | --- | --- |
| Pintor base | `painter.ts` (152) | Funcional | `rect`, `polygon`, `tint`, `hash`, `sparkle`, `sprite` (matriz de caracteres) sobre Canvas 2D |
| Sprites | `sprites.ts` (557) | Parcialmente funcional | Jogador = matriz 16 × 18 escalada por `h/25` + membros rotacionados proceduralmente; inimigos e itens por polígonos. **Qualidade:** silhuetas legíveis, mas sem quadros de animação reais: a "animação" é seno aplicado a membros; sem antecipação, aterrissagem, derrapagem, agachamento, expressões |
| Cenário | `background.ts` (481) | Funcional | Céu com gradiente em faixas, sol/lua, estrelas, nuvens, 2 camadas de montanhas por mundo (parallax 0,085 e 0,2), ruínas, arbustos, clima (areia/neve/esporos/brasas), vinheta |
| Compositor | `renderer.ts` (512) | Funcional | Culling por visibilidade, tremor de câmera, marcos (placas, checkpoint, saída), plataformas por tipo, perigos (lava/água/espinhos/chama orbital) |

### 3.4 Sistemas (`src/systems`, 666 linhas)

| Componente | Arquivo | Estado | Observações |
| --- | --- | --- | --- |
| Áudio | `audio.ts` (367) | Funcional (navegador) | 6 trilhas de 32 passos + trilha de chefe, 14 efeitos; dois barramentos (música/efeitos); síntese em tempo real com osciladores. Sem canal de vozes/ambiente, sem limite de instâncias, sem crossfade |
| Entrada | `input.ts` (115) | Funcional (navegador) | Teclado, gamepad padrão, toque; latch de taps |
| Salvamento | `save.ts` (171) | Funcional (navegador) | `localStorage` chave `lume-save-v1`, sanitização robusta (testada), `completeLevel` imutável. Limite fixo de 15 fases (`unlocked ≤ 14`) |
| Toque | `touch.ts` (13) | Funcional (navegador) | Botões DOM |

### 3.5 Interface (`src/ui/interface.ts`, 486 linhas)

| Componente | Estado | Observações |
| --- | --- | --- |
| Menu, mapa, controles, configurações, créditos, pausa, conclusão, fim de jogo, HUD, toasts, barra de chefe | Funcional (navegador) | Inteiramente em HTML/CSS (`style.css`, ~1.000 linhas). Textos em pt-BR fixos no código. Sem seleção de resolução, limite de FPS, exibição de FPS, idioma, remapeamento ou volume de vozes |

### 3.6 Testes, build e CI

| Componente | Estado | Observações |
| --- | --- | --- |
| 88 testes Vitest (10 arquivos) | Funcional | Física (12), interações (4), combate (8), chefes (26), fases (16), rotas (1 + 15 campanha), progressão (2), salvamento (4) |
| Condutor de campanha `tests/helpers/route-player.ts` | Funcional | Joga por entradas normais; é a prova de completabilidade e **precisa ser portado** |
| 15 testes Playwright | Funcional em CI | Menus, teclado, pausa, persistência, áudio, gamepad virtual, toque, produção |
| `pages.yml` | Parcialmente funcional | Build e testes passam; deploy do Pages falha (site não habilitado) |

### 3.7 Inexistente (exigido pelo novo escopo)

Máquina de estados de animação; spritesheets reais; percepção/FSM de inimigos; arquétipos (furtivo, explosivo, aquático, lançador com preparação); chefes com fases que mudam estratégia; arenas; NPCs; diálogos; vozes/legendas; localização; câmera vertical e enquadramento de batalha; agachamento, rampas, natação, interação com paredes; vento; editor de fases; configurações de resolução/FPS/idioma/remapeamento; medição de desempenho; empacotamento desktop; execução Python.

## 4. Respostas às perguntas da auditoria

1. **Como funciona:** ver seção 2. Simulação determinística em passo fixo, renderização e UI acopladas ao navegador.
2. **Sistemas implementados:** física AABB, salto variável com tolerâncias, blocos/moedas/canos/plataformas móveis e frágeis, 6 tipos de inimigos, chefe único parametrizado, 4 poderes, perigos, progressão/conquistas, salvamento, áudio sintetizado, entrada tripla, UI completa de menus.
3. **Limitações reais:** ver seção 5 (tabela de problemas). Em resumo: profundidade de IA, animação, chefes e arte muito abaixo do objetivo; ausência de diálogos, localização e ferramentas.
4. **Migráveis diretamente (lógica 1:1):** `physics.ts`, `game.ts`, `interactions.ts`, `enemies.ts`, `bosses.ts`, `powers.ts`, `progression.ts`, a sanitização de `save.ts`, `levels.ts` (como JSON) e os 88 testes.
5. **Precisam ser reescritos:** `renderer/painter/sprites/background` (Canvas → Surfaces pygame, com pré-renderização para desempenho), `audio.ts` (Web Audio → síntese numpy + `pygame.mixer`), `input.ts` (eventos DOM → eventos pygame + joystick), `interface.ts`/`style.css` (DOM → widgets pygame), `main.ts` (rAF → laço pygame), `touch.ts` (sem equivalente desktop), testes de navegador (→ testes headless com `SDL_VIDEODRIVER=dummy`).
6. **Melhorias de arquitetura:** entidades como classes com responsabilidade única, comportamentos de inimigos como classes com FSM e percepção, chefes com fases declarativas, barramento de eventos, dados em JSON validado por esquema, câmera e partículas como módulos, localização em arquivos externos, configurações versionadas, pipeline de sprites reproduzível, separação hitbox física/ataque/percepção.
7. **Qualidade atual das animações:** funcional porém rudimentar — poses derivadas de `vx`/`vy`, membros oscilando por seno, sem quadros-chave, sem aterrissagem/derrapagem/agachamento/expressões; inimigos com um "gait" senoidal. A direção visual é coerente (paleta por mundo, silhuetas limpas), o que vale preservar como ponto de partida.
8. **Padrões dos inimigos:** `walker` patrulha e inverte em paredes/bordas; `armored` igual com 2 PV e mais lento; `shell` recolhe no pisão, desliza ao ser tocado/pisado de novo e atinge outros; `flyer` patrulha em seno vertical (±38 px, 2,2 rad/s); `shooter` parado, vira para o jogador e atira a cada 2,2 s se |dx| < 650; limites de patrulha fixos.
9. **Decisões dos chefes:** puramente temporais (`timer % período`): abertura (vulnerável, parado) → carga para o lado que encara → salto em 2 s → tiro(s) direcionado(s) ao jogador. Única informação observada: o lado do jogador para o tiro. Fase 2 (≤ metade dos PV) apenas acelera o ciclo e inclina o projétil.
10. **Colisões:** AABB com desigualdades estritas; movimento integrado por eixo (X, depois Y) e empurrado para fora de cada plataforma sobreposta em ordem de declaração; pisão em inimigo exige `vy > 0` e pé acima de `e.y + min(24, vy·dt + 15)`; deslocamentos máximos por passo (7,1 px vertical, 2,8 px horizontal) são menores que qualquer espessura (≥ 18 px), portanto não há tunelamento nas velocidades atuais.
11. **Mapas:** helpers imperativos em TS compõem cada fase; chão com altura `540 − y + 60` para fechar visualmente; salas secretas em y = 176 ligadas por canos; água gerada entre chãos no mundo 1.
12. **Dependentes do navegador:** `main.ts`, `render/*` (Canvas 2D), `systems/audio.ts` (Web Audio), `systems/input.ts` (DOM, Gamepad API), `systems/touch.ts`, `systems/save.ts` (`localStorage`), `ui/interface.ts`, `style.css`, `index.html`, testes Playwright.
13. **Substituições Python:** Canvas → `pygame.Surface`/`pygame.draw` + superfícies pré-renderizadas; Web Audio → `numpy` + `pygame.sndarray`/`pygame.mixer` (4 canais); `localStorage` → arquivo JSON versionado no diretório do usuário com escrita atômica; DOM UI → módulo `game/ui`; rAF → `pygame.time.Clock` com acumulador; Gamepad API → `pygame.joystick`; `matchMedia`/toque → não aplicável no desktop (previsto para Pygbag).
14. **Testes a preservar:** todos os 88 de lógica (portar para pytest com os mesmos cenários e asserções) e o condutor de campanha; dos 15 de navegador, preservar a intenção (fluxos de menu/pausa/configurações/salvamento/áudio/gamepad) como testes headless pygame; toque e build web ficam registrados como limitação até a etapa Pygbag.
15. **Riscos de regressão:** (a) sensação de controle — qualquer diferença na ordem das operações do passo altera as rotas; (b) semântica de ponto flutuante JS × Python (`Math.round` arredonda 0,5 para cima, `round()` do Python para o par; `%` do JS é resto com sinal do dividendo); (c) acumulador de passo fixo (o teste 30/60/144 Hz depende dele); (d) fidelidade dos dados de fase; (e) temporização de chefes por divisão inteira de `timer`; (f) ordem dos eventos (áudio/UI); (g) sanitização do salvamento; (h) completabilidade das 15 fases pelo condutor.

## 5. Problemas encontrados

Gravidade: **Alta** (bloqueia o objetivo), **Média** (limita qualidade), **Baixa** (polimento).

| # | Gravidade | Arquivo | Problema | Solução planejada |
| --- | --- | --- | --- | --- |
| 1 | Alta | toda a base | Lógica e apresentação em TypeScript/navegador; nada executa em Python | Migração completa (plano em `docs/PLANO_MIGRACAO.md`), preservando o TS como referência até os testes Python passarem |
| 2 | Alta | `bosses.ts` | Cinco chefes com um único padrão; sem fases que alterem estratégia, sem telegraph, arenas ou derrota cinemática | Reconstruir como classes com fases declarativas (3 fases), ataques com preparação/recuperação, arena e vulnerabilidades próprias; testes por padrão |
| 3 | Alta | `enemies.ts` | Sem percepção, estados, reação ou sinalização; tipos genéricos | Sistema de arquétipos com FSM (`PATROL/ALERT/PREPARE_ATTACK/ATTACK/RECOVER/…`), percepção por distância/visão, tempo de reação, animações por decisão |
| 4 | Alta | `sprites.ts` | Sem quadros de animação; poses por seno; sem aterrissagem/derrapagem/agachamento/expressões | Máquina de estados de animação + spritesheets PNG produzidas por pipeline reproduzível (Pillow) com metadados JSON |
| 5 | Alta | `interface.ts`, `style.css` | Interface inteiramente DOM | Reescrever em pygame com widgets próprios, HUD, mapa, configurações (resolução, tela cheia, FPS, volumes, idioma, remapeamento) |
| 6 | Alta | `save.ts` | `localStorage`; limite rígido de 15 fases; sem migração de versão | Arquivo JSON versionado (`version: 2`) em diretório do usuário, escrita atômica (tmp + rename), importação opcional do JSON do navegador, migração v1 → v2 |
| 7 | Média | `game.ts` | Sem agachamento, rampas, natação (água mata), paredes, vento; câmera sem controle vertical real | Motor de física ampliado por etapas após a migração, mantendo os testes do comportamento base |
| 8 | Média | `physics.ts` | Resolução em ordem de declaração pode "puxar" o corpo para a plataforma errada em quinas; sem detecção contínua | Resolver por eixo com a plataforma de menor penetração; limitar deslocamento por subpasso quando a velocidade exceder a menor espessura |
| 9 | Média | `audio.ts` | Dois barramentos; sem vozes/ambiente, limite de instâncias, crossfade ou ducking | Mixer com 4 barramentos, cache de sons sintetizados, limite por efeito, crossfade |
| 10 | Média | `levels.ts` | Dados em código, sem esquema/validador; sem editor | JSON por fase + validador + testes comparativos; editor após estabilização |
| 11 | Média | `interface.ts` | Textos pt-BR fixos no código; sem localização | `data/locales/pt-BR.json` + sistema de localização |
| 12 | Média | — | Sem NPCs, diálogos, vozes, legendas | Sistema de diálogo (JSON), vocalizações originais, legendas |
| 13 | Média | — | Sem medição de desempenho, limite de FPS, resoluções | Métricas no laço (FPS médio/mínimo, tempo de física/render), configurações |
| 14 | Baixa | `background.ts`, `renderer.ts` | Desenho procedural por quadro (centenas de `fillRect`) — caro em Python | Pré-renderizar camadas estáticas em Surfaces; só animar o necessário |
| 15 | Baixa | `README.md`, `pages.yml` | Publicação Pages nunca concluída; instruções Node | Atualizar documentação; workflow Python; estratégia web via Pygbag investigada separadamente |
| 16 | Baixa | `game.ts` | `hurt()` reduz `h` ao encolher sem testar teto; `respawn()` zera projéteis mas não itens | Preservar na migração (comportamento de referência) e corrigir na etapa de física com teste |

## 6. Riscos e mitigação adotada

- **Fidelidade dos dados:** os 15 mapas foram exportados pelo próprio TS para `data/levels/*.json` (`index.json` registra o commit de origem). Um teste comparativo em Python confere totais e IDs.
- **Fidelidade da simulação:** foram gravados **traces de ouro** (`tests/fixtures/golden/*.json`) com o motor TS: entradas tick a tick do condutor de campanha nas 15 fases, 4 sequências pseudoaleatórias e uma arena de combate, com posição do jogador a cada 4 ticks, instantâneos completos a cada segundo e todos os eventos. O port Python reproduz as mesmas entradas e precisa coincidir. O gerador fica em `tools/legacy-golden/` até a remoção do TypeScript.
- **Perda de funcionalidades:** nenhum arquivo TS será removido antes de a suíte Python correspondente passar.
- **Dependências:** `pygame-ce` (motor), `numpy` (síntese de áudio, justificada por desempenho), `Pillow` (pipeline de sprites, dev/ferramentas), `pytest`, `ruff`, `mypy` (dev). Nada mais sem justificativa registrada.

## 7. Licença e créditos

Licença MIT de Hélio (2026) preservada. Lume, arte, cenários, lógica e composições são originais do repositório; o projeto não é afiliado à Nintendo. A pesquisa comportamental usa apenas fontes legítimas e não incorpora assets proprietários.
