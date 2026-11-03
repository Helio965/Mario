# Inimigos nos Mario 2D — engenharia reversa comportamental e biblioteca de arquétipos para o Lume

Documento de pesquisa da Etapa 2 (migração do Lume para Python 3.12 + pygame-ce 2.5.8). Objetivo: entender **como** os inimigos dos jogos oficiais 2D de Mario se movem, percebem o jogador, atacam, reagem a obstáculos e a dano, interagem entre si e sinalizam perigo — para calibrar uma biblioteca de arquétipos **original e coerente** no Lume. Nenhum asset, ROM, sprite, som ou código proprietário foi extraído ou copiado: os números abaixo vêm de manuais oficiais, entrevistas publicadas pela Nintendo e de documentação comunitária (listagens anotadas publicadas por terceiros, wikis) e são citados **como valores de documentação comunitária derivada de análise de terceiros**, nunca como valores oficiais.

Complementa `docs/research/FISICA.md` (salto/queda) e `docs/research/MOVIMENTACAO.md` (movimento horizontal); as convenções de unidades são as mesmas.

## 0. Como ler este documento

| Rótulo | Significado |
| --- | --- |
| **OFICIAL** | Manual de instruções, site ou entrevista publicada pela Nintendo/desenvolvedores (ou material licenciado pela Nintendo citado por wiki, indicado como tal). Descreve comportamento; raramente dá números. |
| **DOCUMENTADO** | Artigo técnico, wiki ou listagem comunitária com fonte verificável. Inclui valores obtidos por desmontagem/análise de terceiros ("documentação comunitária"). Nunca é valor oficial. |
| **OBSERVADO** | Medição ou descrição de gameplay publicada por terceiros (wikis, vídeos) sem acesso ao código. |
| **ESTIMADO** | Inferência nossa: cálculo a partir de valores documentados, ou hipótese sem confirmação. |

As fontes são citadas inline por chave entre colchetes (ex.: [D-SMB1]) e listadas, com URL e tipo, na seção 11.

**Unidades e conversões** (ver também FISICA.md §0): `q` = quadro a 60 Hz (NES/SNES NTSC rodam a ~60,1 Hz; usamos 60). `tile` = bloco de 16 px nos jogos clássicos. Velocidades em SMB1, SMB3 e SMW são armazenadas em **1/16 px/q** por unidade (SMB3 chama isso de "4.4 fixed point": "divide them by 16 for pixels/frame" [D-SMB3]). Portanto `1 unidade = 1/16 px/q = 3,75 px/s`; `$08 = 0,5 px/q = 30 px/s`; `$10 = 1 px/q = 60 px/s`; `$18 = 1,5 px/q = 90 px/s`; `$30 = 3 px/q = 180 px/s`. Acelerações: `1 unidade por quadro = 0,0625 px/q² = 225 px/s²`. Em SMB1, forças verticais de inimigos usam 1/256 px/q² por unidade (`1 unidade = 14,0625 px/s²`). Timers "de intervalo" do SMB1 (`EnemyIntervalTimer`) decrementam **a cada 21 quadros** (o controle `IntervalTimerControl` é recarregado com $14 = 20 e decrementado por quadro) [D-SMB1], logo `1 tick = 0,35 s`.

Siglas dos títulos: SMB1 = Super Mario Bros. (NES, 1985); SMB2 = Super Mario Bros. 2 (NES/EUA, 1988); SMB3 = Super Mario Bros. 3 (NES, 1988/1990); SMW = Super Mario World (SNES, 1990/1991); NSMB = New Super Mario Bros. (DS, 2006); NSMBW = NSMB Wii (2009); NSMBU = NSMB U (2012); SMBW = Super Mario Bros. Wonder (Switch, 2023).

**Base de comparação no Lume** (`src/core/enemies.ts`, `game/enemies/legacy.py`): jogador 22×30 px (pequeno) e 22×46 px (crescido); caminhada 220 px/s, corrida 340 px/s, salto 590 px/s, gravidade 1550 px/s². Inimigos atuais: `walker` 55 + 7·mundo px/s (62–90 px/s), `armored` 44 px/s, `shell` (casco parado → deslizando a 360 px/s, dano 2 em outros inimigos), `flyer` 72 + 6·mundo px/s com senoide vertical de ±38 px e frequência 2,2 rad/s, `shooter` dispara projétil de 180 px/s a cada 2,2 s se |dx| < 650 px, `boss`. Pisão: `vy > 0` e pé do jogador acima de `e.y + min(24, vy·dt + 15)`; rebote −390 px/s; `hitTimer` 0,65 s de invulnerabilidade do inimigo após dano. Detecção de borda: sonda de 2×7 px à frente dos pés (`edge_ahead`), inversão de direção ao bater em parede (`vx` zerado pela colisão). O módulo `game/enemies/perception.py` já define `PerceptionProfile` (alcance, altura, campo de visão atrás, alcance de ataque, tempo de reação, tempo de esquecimento, linha de visão) e `game/enemies/state_machine.py` define os estados IDLE/PATROL/ALERT/CHASE/PREPARE_ATTACK/ATTACK/RECOVER/HURT/STUNNED/RETREAT/DEFEATED + SHELL/SLIDE/FUSE/EXPLODE/HIDDEN/EMERGE/DIVE/LEAP/DROP/RISE/SWIM.

---

## 1. Resumo executivo

1. **A velocidade-base dos inimigos terrestres é constante há três gerações**: Goomba, Koopa, Buzzy, Spiny e Dry Bones andam a `$08` = **0,5 px/q = 30 px/s** em SMB1, SMB3 e SMW — um terço da caminhada de Mario (1,5 px/q em SMB1/SMB3) [D-SMB1][D-SMB3][D-SMW]. Variantes "rápidas" usam 0,75 px/q (segunda volta do SMB1; Koopas azul/amarelo e Bob-omb em SMW). Isso é DOCUMENTADO (derivado de análise de terceiros).
2. **Quase nenhum inimigo clássico "enxerga" de verdade.** A percepção é quase sempre uma **janela horizontal fixa em pixels** (Piranha ±33 px, Bill Blaster ±40 px, Thwomp ≈ ±40 px, Chain Chomp 64 px, Rip Van Fish ±48 px), sem linha de visão e sem tempo de reação — exceto Boo (reage ao **lado para onde o jogador olha**, com 20 q de atraso em SMB3) e Lakitu (escala sua velocidade com a **velocidade do próprio jogador**) [D-SMB1][D-SMB3][D-SMW].
3. **A sinalização de perigo é curta e padronizada**: Lakitu afunda na nuvem 16 q antes de lançar (SMB1) ou ~15 q (SMB3); Thwomp muda a expressão em duas etapas (SMW: "olha" a ±64 px, "fica bravo" a ±40 px); Bob-omb pisca nos últimos 64 q de pavio; o casco de Koopa mostra as pernas nos últimos ~5 ticks (≈1,5 s); Dry Bones "chacoalha" nos últimos 64 q (SMW) ou executa ~50 q de animação de remontagem (SMB3); Chain Chomp pisca a corrente antes de se soltar [D-SMB1][D-SMB3][D-SMW][W-ChainChomp].
4. **Timers de atordoamento ficam entre 4 e 6 s**: casco de Koopa 16 ticks ≈ 5,3–5,6 s (11 ticks ≈ 3,9 s na segunda volta) em SMB1; Galoomba/Buzzy/Bob-omb atordoados 255 q = 4,25 s em SMW; Dry Bones caído ≈ 5,25 s em SMB3; pavio do Bob-omb 255 q = 4,25 s em SMB3 [D-SMB1][D-SMB3][D-SMW].
5. **Inimigos se viram ao colidir entre si** (SMB1, exceto Piranha, Lakitu e Hammer Bro) e **inimigos que caem de uma borda viram-se para o jogador ao pousar** (SMB1, exceto Goomba) — regras baratas que criam a impressão de "intenção" [D-SMB1].
6. **O casco é a arma do jogador**: 3 px/q (180 px/s) em SMB1, 2,875–3,25 px/q em SMW; mata qualquer inimigo que toque (inclusive Bullet Bills vindos de fora da tela e Boos, em SMB3), com pontuação em cadeia; o próprio jogador se machuca se o casco voltar [D-SMB1][D-SMW][W-Bullet][W-Boo].
7. **Imunidades definem a hierarquia de poderes**: Buzzy Beetle é à prova de fogo desde 1985 (manual: "fireballs don't even faze him"); Boo, Thwomp, Dry Bones, Bob-omb, Bullet Bill e Chain Chomp carregam a flag `FIREIMMUNITY` em SMB3; Spiny, Chain Chomp e Spiny Cheep são `NOTSTOMPABLE` (pisar machuca) [M-SMB1][D-SMB3].
8. **A Nintendo declara as intenções em linguagem de personalidade, não de números**: "This turtle is chicken! Very timid, he gets scared easily and runs back and forth a lot" (Koopa vermelho), "Boo is too shy to look anyone in the face. But when you turn around...", "If Mario comes close, Thwomp will try to crush him", "As long as he's walking, Bob-omb seems cute. Be very careful when he starts to flash" [M-SMB1][M-SMB3][M-SMW]. O Goomba foi criado "right at the very end" porque testadores achavam o Koopa "quite tricky to encounter at the very start" (Tezuka, Iwata Asks) [IA-NSMBW][GN].
9. **Wonder moderniza a leitura sem mudar as regras**: "It wasn't possible to completely change the behavior of the well-known enemies [...] without altering the gameplay" (Sato); os Goombas agora olham para o jogador, dormem, entram em pânico e "have a biting expression the moment they do damage" (Hayashida) [ATD-2]. Novos inimigos reagem à **ação** do jogador (Hoppycat pula quando você pula; Konk cai quando você está embaixo e pode ser pisado por cima) [W-Hoppycat][W-Konk].
10. **Para o Lume**: manter um walker-base a ≈ 73 px/s (0,33 × caminhada), casco a ≈ 420 px/s (1,2 × corrida), zonas de percepção escaladas por 1,875 (33 px → 62 px; 40 px → 75 px; 64 px → 120 px), timers de 4–6 s mantidos em segundos, e um catálogo explícito de telegraphing (0,25–1,1 s) por arquétipo — detalhes nas seções 6 e 7.

---

## 2. Regras compartilhadas (o "sistema" de inimigos)

### 2.1 O que a Nintendo diz (OFICIAL)

- Manual do SMB1, p. 10–11: "Bad guys on the ground can be done in by jumping on top of them. If you bump into an enemy from the side or from below, you die." e "When in the water, no matter what direction you hit the bad guys from you die." O casco é descrito como arma: "If you stomp on a Koopa Troopa, he becomes [casco] and stays motionless for a while. During that time, you can kick him and send him flying to knock down other enemies." Fogo: "When Mario has fireballs, use the B button to throw them and fry the enemy." E a existência de imortais: "Some bad guys can't be killed. Look out for these immortal creeps!" [M-SMB1].
- Manual do SMB1, p. 19 ("Secret Tricks"): o casco ricocheteia ("Just look out for ricochets. If the [casco] runs into a [bloco], your attack will backfire") e volta mesmo de fora da tela ("if a kicked [casco] bumps into a [bloco] off the screen, it comes ricocheting back at Mario. If you hear the sound of a ricochet, jump right away") — o **som é o telegraph oficial** do casco [M-SMB1].
- Manual do SMB3: "After you have jumped on a Koopa, you can pick up the shell" (novidade de SMB3: carregar casco) [M-SMB3]. Manual do SMW: "If you jump on a Koopa in this game, it pops out of its shell. And what's worse is that an unshelled Koopa will eventually find its empty shell and climb back in to start all over again. BEWARE! If a Koopa climbs into a yellow shell, he'll become invincible!" [M-SMW].
- Filosofia (Tezuka, Ask the Developer Vol. 11, parte 3): "I felt that 2D Mario games often had the reputation of being unforgiving" e a meta de que "players can conquer the game with their ideas and use their heads, not just their skills" [ATD-3]. Sato (parte 2): as expressões dos inimigos foram ampliadas, mas "It wasn't possible to completely change the behavior of the well-known enemies in this game without altering the gameplay" [ATD-2].

### 2.2 Mecânica compartilhada em SMB1 (DOCUMENTADO — listagem comunitária anotada [D-SMB1])

| Regra | Valor na listagem | Conversão |
| --- | --- | --- |
| Velocidade de andar (Goomba, Koopas, Buzzy, Spiny) | `NormalXSpdData = $F8/$F4` (−8 / −12 unid.) | 0,5 px/q = **30 px/s**; 0,75 px/q = **45 px/s** no modo difícil (`PrimaryHardMode`, 2.ª volta) |
| Direção inicial | `Enemy_MovingDir = 2` (esquerda) | todos nascem andando para a esquerda, em direção ao jogador |
| Casco chutado | `KickedShellXSpdData = $30/$D0` | **3 px/q = 180 px/s** (Mario corre a 2,5 px/q = 150 px/s) |
| Rebote do pisão | `Player_Y_Speed = $FC` (Koopa/Buzzy/Goomba/Paratroopa) ou `$FD` (Bullet Bill, Cheep voador, Hammer Bro, Lakitu, Bloober) | −4 px/q = −240 px/s (igual ao v0 do salto parado) ou −3 px/q = −180 px/s |
| Casco/Goomba pisado: timer | `RevivalRateData = $10/$0B` ticks de 21 q | **5,3–5,6 s** normal; **3,9 s** na 2.ª volta |
| Goomba achatado desaparece | quando o timer passa de `$0E` | 2 ticks ≈ **0,35–0,7 s** achatado |
| Casco "mostra as pernas" | quadros animados quando `EnemyIntervalTimer < 5` | ≈ **1,5–1,75 s** antes de reviver (telegraph) |
| Casco revive | `RevivedXSpeed = $08/$F8` (normal) `$0C/$F4` (difícil), direção = bit 0 do `FrameCounter` | 0,5 px/q; direção pseudoaleatória |
| Paratroopa pisado vira Koopa | `Enemy_ID & 1`, velocidade `DemotedKoopaXSpdData = $08/$F8`, 400 pts | Paratroopa vermelho ($0F) vira ID **$01**, um Koopa vermelho **sem** a regra de borda (só o ID $03 vira na borda) — bug conhecido |
| Batida de bloco por baixo / casco / estrela (`SetStun`) | `vy = $FD` (−3 px/q) em terra, `$FF` na água; `vx = ±$10` para longe do jogador; Goomba morre (100 pts) | pop-up de **−180 px/s** e **±60 px/s** horizontais; Koopas ficam de cabeça para baixo (estado "flipped") |
| Inimigo bate em inimigo | `EnemyTurnAround`: ambos invertem a direção; exceções: Piranha, Lakitu, Hammer Bro | regra barata de "trânsito" |
| Inimigo pousa após queda | `ProcEnemyDirection`: Koopas/Buzzy viram-se para o lado do jogador; Spiny idem em 7/8 dos casos; **Goomba nunca** | emulação de "intenção" sem IA |
| Fogo | `FireballEnemyCollision`: Buzzy Beetle ignora ("buzzy beetles fireproof"); Bowser leva 5 bolas; demais morrem (200 pts; Goomba 100) | — |
| Estrela | contato chama `ShellOrBlockDefeat` para qualquer inimigo (Hammer Bro 1000 pts) | — |
| Pontos de pisão em cadeia | `StompChainCounter` incrementa a cada pisão sem pousar | 100 → 200 → 400 → 500 → 800 → 1000 → 2000 → 4000 → 5000 → 8000 → 1-UP (OBSERVADO, [W-Koopa]) |
| Casco acerta inimigos em cadeia | `ShellChainCounter` + 4 como índice de pontos; o casco não morre | 500 → 800 → 1000 → 2000 → 4000 → 5000 → 8000 (OBSERVADO) |

### 2.3 Flags de atributo em SMB3 (DOCUMENTADO [D-SMB3])

A listagem de SMB3 expõe uma tabela de atributos por objeto que é, na prática, uma **biblioteca de arquétipos** embutida: `OAT_FIREIMMUNITY` (imune a fogo: Thwomp, Boo, Bullet Bill, Bob-omb, Dry Bones, Buzzy, Chain Chomp, Chain Chomp solto), `OA3_NOTSTOMPABLE` ("If the Player tries to stomp this enemy, he will be HURT!": Spiny, Spiny Cheep, Chain Chomp, Dry Bones usa rotina própria), `OA3_TAILATKIMMUNE` (imune ao rabo de guaxinim: Boo, Dry Bones, Chain Chomp), `OA2_NOSHELLORSQUASH` (não entra em casco nem achata ao ser pisado: Lakitu, Hammer Bro, Bullet Bill, Chain Chomp), `OAT_BOUNCEOFFOTHERS` (quica em outros objetos: Buzzy, Dry Bones), `OA3_DIESHELLED` ("dies into shell": Buzzy). O Lume deve ter o equivalente: um conjunto de flags por arquétipo em vez de `if kind == ...` espalhados (seção 7).

### 2.4 Propriedades por sprite em SMW (DOCUMENTADO [D-SMW])

Os sprites $00–$13 (Koopas sem casco, Koopas, Paratroopas, Bob-omb, Galoomba, Buzzy, Spiny) compartilham uma rotina ("Spr0to13") com uma tabela de propriedades por sprite: bit 0 = **rápido** (0,75 px/q em vez de 0,5: Koopas azul e amarelo, Bob-omb), bit 2 = **segue Mario** (Koopa amarelo, Bob-omb), bit 6 = tem casco, bit 4 = voa, bit 5 = tipo Galoomba (achata/tomba em vez de entrar no casco). Velocidades: `Spr0to13SpeedX = $08,$F8,$0C,$F4`. Casco chutado: `ShellSpeedX = $D2,$2E,$CC,$34` (NTSC) → **2,875 px/q = 172,5 px/s** e **3,25 px/q = 195 px/s**; a versão PAL usa $C9/$37/$C2/$3E (3,44 e 3,875 px/q) para compensar os 50 Hz — exemplo claro de que a equipe calibrava **velocidade por segundo**, não por quadro. Timer de atordoamento (`SetStunnedTimer`): **$FF = 255 q = 4,25 s** para Galoomba, Buzzy Beetle, Mechakoopa e Bob-omb; o Galoomba tombado acelera a animação nos últimos $30 = 48 q (0,8 s) e dá um pulinho (`vy = $D8` = −2,5 px/q) quando faltam 8 q — telegraph de "vai levantar". Gelo: com `LevelIsSlippery`, a desaceleração do Koopa sem casco cai de 2 para 1 unidade por quadro (escorrega o dobro).

---
## 3. Fichas por inimigo

Cada ficha segue a mesma grade: movimento · percepção · ataque · obstáculos e bordas · derrota e reação ao dano · interações · animação/som/telegraphing · ambiente · diferenças por título.

### 3.1 Goomba (e Galoomba)

- **OFICIAL** — Manual SMB1 (p. 10): "A mushroom who betrayed the Mushroom Kingdom. One stomp and he dies... 100 PTS." [M-SMB1]. Origem (Tezuka, Iwata Asks NSMB Wii Vol. 2, reproduzido por GoNintendo): só existia o Koopa, "when we got people to play the game, they would say that it was quite tricky to encounter Koopa Troopas at the very start" (Iwata: derrotar um Koopa "is a two-step process"); "So we decided that we should make an enemy that you could easily squash with a single blow [...] Then right at the very end, we made the Goomba"; Nakago: "we had hardly any bytes remaining" [IA-NSMBW][GN]. Wonder (Hayashida): "You can see Goombas greeting each other as they meet or sleeping peacefully"; "Goombas have a biting expression the moment they do damage"; Sato: "It's because the Goombas bite him" (resposta de Miyamoto à pergunta de por que o Goomba machuca) [ATD-2].
- **Movimento (DOCUMENTADO)**: SMB1 0,5 px/q (30 px/s), 0,75 px/q na 2.ª volta; nasce andando para a esquerda; SMB3 `GroundTroop_XVel = ±$08` (0,5 px/q; 0,375/0,3125 contra esteiras); SMW `Spr0to13SpeedX` 0,5 px/q [D-SMB1][D-SMB3][D-SMW].
- **Percepção**: nenhuma em SMB1/SMB3/SMW (não vira para o jogador nem ao pousar — é a única exceção explícita em `ProcEnemyDirection`) [D-SMB1]. Wonder (OBSERVADO [W-Goomba]): "will shift their eyes to look at a player if one is in front of them", "visibly panic if they notice potential threats"; Goombas dormindo "wake up when something is right in front of them or if the Goomba is touched by the player" e tocar um Goomba dormindo não machuca ("knocks the Goomba back"); presos em vãos de 1 bloco "stop pacing back and forth and instead watch the player character".
- **Obstáculos e bordas**: inverte ao bater em parede ou em outro inimigo; **cai de bordas** (SMB1/SMB3/SMW) [D-SMB1][W-Koopa].
- **Derrota**: pisão (achata; 100 pts; some em ≈0,35–0,7 s), fogo, casco, estrela, bloco por baixo (100 pts) [D-SMB1]. SMW: Galoomba substitui o Goomba e "cannot be defeated in a single jump": o pisão o **tomba** por 255 q = 4,25 s, pode ser carregado/arremessado ("Running into or jumping on a flipped Galoomba kicks it around, but unlike shells, it doesn't ricochet"); spin jump, fogo e Yoshi matam; capa só tomba [D-SMW][W-Galoomba]. NSMB: Goomba gigante divide-se em dois Hefty Goombas, que dividem em dois Goombas [W-Goomba]. NSMBU: "they now jump at every vocal riff in the background music" (Kondo, Wonder: "the most I could do was make Goombas jump in time with the background music") [W-Goomba][ATD-3].
- **Telegraphing/som**: SMB1 usa o som de pisão (`Sfx_EnemyStomp`, compartilhado com a braçada de natação) [D-SMB1]. Galoomba tombado: animação acelera nos últimos 0,8 s e dá um pulinho quando faltam 8 q [D-SMW].
- **Ambiente**: Goomba não nada; Galoomba tombado na água segue a física de sprite atordoado (não extraído).
- **Para o Lume**: é o arquétipo "terrestre" (§6.1): sem percepção, cai de bordas, morre num pisão; variante "tombável" (Galoomba) usa STUNNED de 4,25 s.

### 3.2 Koopa Troopa (verde × vermelho)

- **OFICIAL** — Manual SMB1 (p. 10–11): verde: "Soldier of the Turtle Empire, his orders are to find and destroy Mario. Jump on him and he stops moving for a while."; vermelho: "This turtle is chicken! Very timid, he gets scared easily and runs back and forth a lot. Jump on him and he stops moving for a while." [M-SMB1][W-KoopaProf]. Cartão colecionável licenciado de NSMBW: "Green-shelled Troopas will walk off of ledges, but red Troopas will double back." [W-KoopaProf]. Manual SMW: pisão tira o Koopa do casco; ele volta ao casco; casco amarelo o torna invencível [M-SMW].
- **Movimento (DOCUMENTADO)**: 0,5 px/q em SMB1/SMB3/SMW (0,75 px/q na 2.ª volta de SMB1; Koopas azul/amarelo "rápidos" em SMW) [D-SMB1][D-SMB3][D-SMW].
- **Percepção/bordas — a regra do vermelho**: em SMB1 só o ID `$03` em estado normal (no chão) é verificado em `ChkForRedKoopa`: quando a sonda "bottom middle (8,18)" do sprite não encontra bloco sólido, o Koopa vermelho inverte a direção; o verde entra no estado "caindo" ($01) e, ao pousar, **vira-se para o lado do jogador** (`ProcEnemyDirection`) [D-SMB1]. SMB3: há comentário explícito sobre "red shell koopa troopas that otherwise turn away at an edge" e correção para descer rampas sem virar [D-SMB3]. SMW: propriedade por sprite (bit de "virar na borda" nos vermelhos/azuis; bit 2 "segue Mario" no amarelo — "Yellow-shelled Koopas tend to chase Mario") [D-SMW][W-Koopa]. NSMBW: "green Koopas walk straight until they reach a wall, while red Koopas turn around at drops" [W-Koopa].
- **Derrota e reação ao dano**: SMB1 pisão → casco parado por 16 ticks (≈5,3–5,6 s; 3,9 s na 2.ª volta), pernas aparecem nos últimos ~5 ticks ("the Koopa moves its legs before re-emerging", [W-Koopa]); tocar o casco parado o chuta a 3 px/q (180 px/s) na direção oposta ao jogador (som `Sfx_EnemySmack`); pisar o casco em movimento o para; batida por baixo/casco/estrela vira-o de cabeça para baixo e ele se endireita depois ("A Koopa hit from below or stomped while falling has its shell flipped upside down, and it upright itself after some time") [D-SMB1][W-Koopa]. SMB3: casco pode ser pegado, carregado e lançado (manual) [M-SMB3]. SMW: pisão **expulsa** o Koopa do casco (fica atordoado brevemente, exceto o azul); o Koopa sem casco volta para o casco; Koopa azul sem casco chuta cascos que encontrar; amarelo sem casco solta moeda; casco amarelo + Koopa = casco piscante invencível (só spin jump) [W-Koopa][D-SMW]. NSMB: pisão em cima (ground pound) manda o casco deslizando; spin jump e ground pound matam [W-Koopa].
- **Interações**: casco deslizante mata outros inimigos em cadeia (SMB1 500→8000 pts), quica em paredes ("bump" `Sfx_Bump`), mata Bullet Bills vindos de fora da tela, Boos em SMB3; o próprio jogador se machuca se tocado pelo casco em movimento [D-SMB1][W-Bullet][W-Boo]. Truque dos degraus (3-1): cadeia infinita de pisões/chutes [W-Koopa].
- **Som/telegraph**: SMB1 chute = `Sfx_EnemySmack` (mesmo bit do "blast"); ricochete = `Sfx_Bump` (o manual manda pular ao ouvi-lo) [D-SMB1][M-SMB1]; SMB3 chute = `SND_PLAYERKICK`; o Koopa "acorda" chacoalhando (SMB3+) [D-SMB3][W-Buzzy].
- **Ambiente**: SMW gelo dobra o escorregão do Koopa sem casco [D-SMW]; Paratroopa verde pulante em SMB3 pula a −3 px/q em terra e −1,5 px/q na água [D-SMB3].
- **Diferenças por título**: Wonder: Koopas "have a hunched posture and show an angry expression when the player is close" e "faced you when you bumped into them from behind" (Tezuka) [W-Koopa][ATD-2]; novas variantes Rolla Koopa (patins) [ATD-2].
- **Para o Lume**: arquétipo "com casco" (§6.2): PATROL ↔ SHELL (5 s, pernas em 1,5 s) ↔ SLIDE (≈420 px/s). Adotar a correção óbvia do bug de SMB1: Paratroopa vermelho pisado deve manter a regra de borda.

### 3.3 Koopa Paratroopa (verde × vermelho)

- **OFICIAL** — Manual SMB1 (p. 11): verde: "A bit out of control, he wings around aimlessly and comes at you all of a sudden. Stomp on him and he loses his wings. 400 PTS."; vermelho: "This turtle is under control, but likes to take it easy. Stomp on him and he loses his wings. 400 PTS." [M-SMB1][W-ParaProf].
- **Movimento (DOCUMENTADO)**: três objetos em SMB1: verde **pulante** ($0E: anda a 0,5 px/q e, ao pousar, recebe `vy = $FD` = −3 px/q = −180 px/s com gravidade `$1C/256` ≈ 0,109 px/q² → saltos de ≈41 px ≈ 2,6 tiles — ESTIMADO), vermelho **vertical** ($0F: oscila em torno de um centro 48 px abaixo/32 px acima do ponto inicial com aceleração 3/256 px/q² e limite 2 px/q → percurso ≈96 px, pico ≈1,06 px/q, período ≈6 s — ESTIMADO a partir das constantes) e verde **horizontal** ($10: contador triangular máx. $13 com ondulação vertical de ±1 px a cada 4 q, invertendo a cada 64 q) [D-SMB1]. SMB3: voador vermelho acelera 1/16 px/q a cada 4 q até um limite e inverte com pausa de $30 q; verde pulante −3 px/q (−1,5 na água) com "float" (−1 em `vy` por quadro no ar) [D-SMB3]. SMW: verde pula "at varying heights or fly in one direction"; vermelho "programmed left to right pattern or continuously in either direction"; amarelo anda, "jump over shells in front of them, and chase the player" [W-Para].
- **Percepção**: nenhuma em SMB1; o verde pulante vira-se para o jogador ao pousar (regra geral) [D-SMB1]; o amarelo de SMW persegue [W-Para].
- **Derrota**: pisão remove as asas → vira Koopa (400 pts; velocidade 0,5 px/q; direção virada para o jogador por `EnemyFacePlayer`); fogo/estrela/casco matam direto [D-SMB1]. **Bug SMB1**: o vermelho pisado vira ID `$01` e passa a cair de bordas [D-SMB1]. NSMBW: ground pound mata direto; Yoshi pisando tira as asas (em SMW Yoshi matava) [W-Para].
- **Interações**: casco em movimento mata; demotado herda as regras do Koopa.
- **Ambiente**: SMB3 reduz o pulo na água [D-SMB3].
- **Para o Lume**: arquétipo "voador" (§6.3) com duas rotas: `hop` (pulante) e `oscillate` (vertical/horizontal). Já existe `flyer` com senoide ±38 px.

### 3.4 Buzzy Beetle

- **OFICIAL** — Manual SMB1 (p. 11): "Quite the toughy, fireballs don't even faze him. 100 PTS." [M-SMB1][W-BuzzyProf]; manual SMB3: "He's back again. This time he can walk on the ceiling." [M-SMB3]; cartão NSMBW: "infamous for crawling across the ceiling and falling right on you" [W-BuzzyProf].
- **Movimento**: 0,5 px/q; "walk off of ledges, like with green Koopa Troopas" [D-SMB1][W-Buzzy].
- **Percepção**: nenhuma no chão; a variante de **teto** (SMB3+) "attack by dropping from there" quando o jogador se aproxima/passa embaixo, depois "spin along the ground toward the player" [W-Buzzy]; NSMBW: "walk along the ceiling in World 6-3 but drop when approached" [W-Buzzy]. A janela exata de disparo não foi localizada na listagem de SMB3 (§10).
- **Derrota**: pisão → casco (mesmos timers do Koopa); **imune a fogo** (`ChkBuzzyBeetle` → "buzzy beetles fireproof"; `OAT_FIREIMMUNITY` em SMB3); casco chutável a 3 px/q; estrela/casco/bloco por baixo [D-SMB1][D-SMB3]. SMW: Yoshi pode engolir ("unlike Koopa Shells") [W-Buzzy]. Wonder: "able to swim in lava" [W-Buzzy].
- **Telegraphing**: SMB1 "Buzzy Beetles do not indicate when they are about to emerge"; SMB3 adiciona o chacoalhar antes de sair do casco; SMW após o Special Zone os cascos saem "without shaking" (OBSERVADO) [W-Buzzy].
- **Para o Lume**: arquétipo "blindado" (§6.5) na variante **casco à prova de fogo**; o atual `armored` (44 px/s, 2 de vida) pode virar isto. Variante de teto = HIDDEN → DROP → SLIDE.

### 3.5 Piranha Plant (e Venus Fire Trap)

- **OFICIAL** — Manual SMB1 (p. 13): "Man-eating plants that live in the flower-pots. They show their faces quickly and without warning, so watch out!" [M-SMB1][W-PiranhaProf] (a frase "It's kind of shy, so it won't come out if you're nearby" é do caderno de Super Mario Run, não do SMB1 [W-PiranhaProf]). Manual SMB3: Venus Fire Trap "emits fireballs. They come in different sizes and are very dangerous"; "Walking Piranas: These small flowers jump up when Mario gets close" [M-SMB3]. Cartão NSMBW: "pop out every couple of seconds looking for lunch" [W-PiranhaProf].
- **Ciclo e percepção em SMB1 (DOCUMENTADO [D-SMB1])**: a planta sobe/desce **1 px a cada 2 quadros (0,5 px/q = 30 px/s)**, percorre `$18` = 24 px (48 q = 0,8 s), espera `$40` = 64 q (1,07 s) em cada extremo. Antes de subir, `MovePiranhaPlant` compara |dx| entre planta e jogador com `$21` = **33 px**: se o jogador está a menos de 33 px (≈2 tiles), ela **não sai** (a verificação só existe no ponto baixo; a descida não é bloqueada). Ciclo completo ≈ 224 q ≈ 3,7 s. Contato sempre fere (`InjurePlayer` direto, sem teste de pisão); fogo/estrela/casco matam (o casco empurra o sprite 24 px para baixo antes de "morrer"); "They do not flip upside-down when defeated, simply disappearing" [W-Piranha]. Lost Levels: vermelha mais rápida e "still emerges from its pipe if the player character stands by it", mas não se ele estiver em cima; invertidas emergem sempre [W-Piranha].
- **SMB3 (DOCUMENTADO [D-SMB3])**: estados HIDE → EMERGE (−1 px/q = 60 px/s) → ATTACK (espera) → RETRACT (+1 px/q). Tempo de espera `$30` = 48 q (0,8 s) para verde/vermelha e `$60` = 96 q (1,6 s) para as que cospem fogo; ao terminar a espera **dentro do cano**, se `−27 ≤ dx < 28` (≈ ±27 px, 1,7 tile) a planta não sai e espera de novo (só as não invertidas). Venus Fire Trap cospe quando o timer vale `$40` e `$10` (2 bolas por saída; no Mundo 1 apenas 1, em `$28`), mirando para cima ou para baixo conforme o jogador ("generally spit two times in a row before receding" [W-Venus]).
- **SMW (DOCUMENTADO [D-SMW])**: `PiranTimeInState = $20,$30,$20,$30` (32 q dentro, 48 q subindo a 1 px/q, 32 q fora, 48 q descendo); ao fim da espera dentro do cano, se `−27 ≤ dx < 28` ela marca-se como "em cano com Mario perto": não é desenhada nem interage ("Don't draw the sprite if in pipe and Mario nearby") até a próxima troca de estado. A wiki descreve como "retreat into their pipe whenever the player character is nearby" [W-Piranha]. Jumping Piranha "come madly whirling out of the pipes" [M-SMW].
- **NSMB/Wii/U**: "retain their attack pattern introduced in Super Mario Bros., but with an added chomping sound effect" (DS); o som foi removido no Wii; congeláveis com Ice Flower; Venus no Wii "spits a fireball and briefly retreats"; variante de 3 bolas (9-7); "can no longer go through solid walls"; NSMBU "always face up while not spitting" [W-Piranha][W-Venus]. Wonder: "Trottin' Piranha Plants, which can leave their pipes and move around"; Venus "can spit multiple fireballs at once" [W-Piranha][W-Venus].
- **Telegraphing**: a própria subida lenta (0,8 s) é o aviso; em NSMB o som de mordida; a Venus vira a cabeça para o lado do jogador antes de cuspir (`Piranha_FacePlayerFlip`) [D-SMB3].
- **Para o Lume**: arquétipo "lançador" na variante **emboscada** (§6.4): HIDDEN (espera 1,07 s; só emerge se |dx| ≥ 62 px) → EMERGE (0,8 s) → ATTACK (1,07 s; opcional 1–2 projéteis mirados) → RETREAT.

### 3.6 Boo

- **OFICIAL** — Manual SMB3: "Boo is too shy to look anyone in the face. But when you turn around..." [M-SMB3]; manual SMW: "If you look at them, they act shy and turn away. Cute, aren't they? But watch it... they're dangerous!" [M-SMW]; cartão NSMBW: "Don't turn your back on this ghost [...] Boo will not make a move when you look at it" [W-BooProf]. Origem: Miyamoto baseou a dualidade tímido/agressivo na esposa de Tezuka (OBSERVADO, [W-Boo]).
- **Percepção = direção do olhar do jogador (DOCUMENTADO [D-SMB3])**: `Boo_CheckPlayerSight` compara o sinal grosso de dx com `Player_FlipBits`; se o jogador está **de frente** para o Boo, o contador de perseguição é zerado; se não, incrementa por quadro e a perseguição começa quando chega a `$14` = **20 q (0,33 s)**. Não há alcance máximo nem linha de visão.
- **Movimento (DOCUMENTADO)**: SMB3: acelera **1/16 px/q por quadro** (0,0625 px/q² = 225 px/s²) em X e em Y até **±$10 = 1 px/q = 60 px/s** (zona morta vertical de 4 px); ao ser olhado, velocidade zerada **instantaneamente** [D-SMB3]. SMW: decide a cada `$20` = 32 q; perseguindo, acelera 1/16 px/q a cada 8 q (≈28 px/s²) até **±$08 = 0,5 px/q = 30 px/s** em X e Y; olhado, desacelera 1 unidade a cada 2 q e cobre o rosto (frame 3); ao trocar de lado usa um "turning timer" de `$1F` = 31 q; dentro de ±10 px horizontais mantém o estado anterior [D-SMW]. A wiki confirma "Boo Buddies move slower than before" [W-Boo].
- **Derrota**: não pode ser pisado (`Player_GetHurt` como rotina de colisão); imune a fogo e rabo (`FIREIMMUNITY`, `TAILATKIMMUNE`) [D-SMB3]; SMB3 "defeated only from either the effects of a Hammer Suit or a Starman, or from a Koopa shell"; SMW só estrela; NSMB casco/estrela/Mega/Blue Shell; NSMBW só estrela; NSMB2 variante que não é tímida e empurra paredes; Wonder "defeated upon contact with rays of light" [W-Boo].
- **Interações**: Boo Buddies em círculo não param quando olhados (SMW) [W-Boo].
- **Telegraphing**: o frame "cobrindo o rosto" (SMB3 frame 0 vs 1; SMW frame 3) e, em SMW, o giro lento de 31 q ao mudar de lado [D-SMB3][D-SMW].
- **Para o Lume**: arquétipo "furtivo" (§6.6): IDLE (rosto coberto) ↔ CHASE, gatilho = `player_looking_at_me` falso por ≥ 0,33 s; sem pisão; morre só com estrela/explosão/"luz".

### 3.7 Shy Guy

- **OFICIAL** — Manual SMB2 (EUA): vermelho: "A member of the '8 bits' (a club from evil dreams). He wears a mask because he's shy."; rosa: "He moves back and forth on the hills. Carefully avoid him." [W-ShyProf]. Manual Super Mario Advance: "If you topple a giant Red Shy Guy, a heart will appear" [W-ShyProf].
- **Movimento/bordas (OBSERVADO [W-ShyGuy])**: SMB2: "Shyguys damage the player character on contact"; o **vermelho cai de bordas** e o **rosa dá meia-volta** ("moves back and forth") — a mesma dicotomia verde/vermelho dos Koopas, com cores trocadas. Yoshi's Island: "They either walk or hop in a direction, as well as sometimes look left or right" [W-ShyGuy].
- **Percepção**: nenhuma (o "olhar para os lados" de Yoshi's Island é animação). Legenda de manual removido de Doki Doki Panic: "slow but steady as they pursue the player" (OBSERVADO) [W-ShyGuy].
- **Derrota**: em SMB2 o pisão **não mata**: Mario fica em pé sobre ele e pode **pegá-lo e arremessá-lo** em outros inimigos, ou acertá-lo com um objeto arremessado [W-ShyGuy]; em Yoshi's Island, pisão ou engolir [W-ShyGuy]. Não aparece como inimigo comum nos Mario 2D listados (SMB1/3/SMW/NSMB/Wonder); em Super Mario Maker é só fantasia [W-ShyGuy].
- **Para o Lume**: variante do "terrestre" (§6.1) com `turn_at_edges=True` e `stompable=False` (plataforma viva que pode ser carregada se o Lume ganhar "pegar/arremessar"). Sem numéricos originais disponíveis: velocidades ESTIMADAS iguais às do Goomba.

### 3.8 Hammer Bro (Boomerang/Fire/Sledge)

- **OFICIAL** — Manual SMB1: "These wily twin-brother turtles come at you throwing hammers. 1000 PTS." [M-SMB1]; manual SMB3: Boomerang Bros "can throw two boomerangs at once"; Fire Bros "shoot balls of fire"; Sledge Bros "shake the earth when they jump. [...] Try to jump up when the Sledge Brothers hit the ground. If you don't, Mario will lose his footing." [M-SMB3]; cartão NSMBW: "cream-of-the-crop of Bowser's army" [W-HammerProf].
- **SMB1 (DOCUMENTADO [D-SMB1])**: anda "shimmy" ±`$04` (0,25 px/q = 15 px/s) invertendo a cada 64 q (bit 6 do `FrameCounter`); sempre **vira-se para o jogador** (`PlayerEnemyDiff`). **Salto**: `HammerBroJumpTimer` = aleatório | $C0 → **192–255 q (3,2–4,25 s)** entre saltos; `vy = $FA` (−6 px/q) por padrão ou `$FD` (−3 px/q) conforme a metade da tela/aleatório; durante `HammerBroJumpLData` ($20 ou $37 q) ignora plataformas (atravessa fileiras de tijolos). **Arremesso**: `HammerThrowTmrData = $30/$1C` → a cada **48 q (0,8 s)** normal / **28 q (0,47 s)** a partir de 5-3 (`SecondaryHardMode`), condicionado a um slot livre escolhido por LFSR (`SpawnHammerObj`); o martelo nasce 10 px acima e 2 px à direita, com `vx = ±$10` (1 px/q = 60 px/s), `vy = $FE` (−2 px/q = −120 px/s), gravidade `$10/256` (0,0625 px/q² = 225 px/s²), queda máx. 4 px/q → ápice ≈32 px (2 tiles) e voo ≈1,1 s (ESTIMADO). **Avanço**: `HBroWalkingTimerData = $80/$50` ticks de 21 q → após ≈ **44,8 s** (normal) / **28 s** (difícil) passa a andar a 0,5 px/q em direção ao jogador, **mas só se o jogador estiver à esquerda** (`MoveHammerBroXDir`). A wiki fala em "100 time units (about 50 seconds)" e confirma "If the player is to its right, it does not give chase" [W-Hammer]; Lost Levels a partir do Mundo 7 "always pursue" [W-Hammer]. Derrota: pisão (1000), fogo, casco, estrela, bloco por baixo; não entra em casco; pisão dá rebote −3 px/q [D-SMB1][W-Hammer].
- **SMB3 (DOCUMENTADO [D-SMB3])**: anda ±`$06` (0,375 px/q = 22,5 px/s) invertendo a cada 64 q, sempre de frente para o jogador; salta quando `Timer3` (aleatório **$C0–$FF = 192–255 q**) expira, com `vy = −$30` (−3 px/q) ou `−$60` (−6 px/q) escolhido pela metade da tela/aleatório; arremessa quando `(Var6 & $1F) == $1F` no chão (≈ a cada 37 q = 0,6 s, pois `Var6` incrementa em 7 de 8 quadros) ou `& $3F` no ar (≈ 73 q), com `Objects_Timer` = 15 q de intervalo mínimo. Em SMB3 "no longer chase after the player after some time" [W-Hammer]; Sledge Bro: terremoto ao pousar imobiliza o jogador no chão [W-Hammer].
- **NSMBW**: "attack by throwing two hammers aimed at Mario, before leaping elsewhere and repeating" (OBSERVADO, [W-Hammer]); Yoshi pode engolir e cuspir o martelo de volta [W-Hammer]; Ice Bro congela [W-Hammer].
- **Telegraphing**: SMB1 usa um frame de braço levantado (`Enemy_State` bit 3 "hammer throw") no quadro do arremesso [D-SMB1]; o salto aleatório **não** é telegrafado. O Sledge Bro telegrafa o terremoto pelo próprio salto (manual).
- **Para o Lume**: arquétipo "lançador" na variante **arremessador saltador** (§6.4): PATROL (shimmy) → PREPARE_ATTACK (0,25 s de braço levantado — adição do Lume) → ATTACK → RECOVER; LEAP a cada 3,2–4,25 s; avanço após N s opcional.

### 3.9 Bullet Bill e Bill Blaster

- **OFICIAL** — Manual SMB1: "Chases after Mario slowly but steadily. You can kill him by jumping onto him from above. 200 PTS." [M-SMB1][W-BulletProf]; cartão NSMBW: "one of Bowser's fastest minions [...] Some are fired from off-screen cannons" [W-BulletProf].
- **Canhão em SMB1 (DOCUMENTADO [D-SMB1])**: `ProcessCannons` roda por slot de inimigo livre (3 slots), escolhe um canhão por LFSR mascarado (`CannonBitMasks = $0F/$07`; só índices < 6 contam) e decrementa `Cannon_Timer` (recarga `$0E`); quando zera, cria um Bullet Bill (variante de canhão `$33`) 8 px acima do canhão. **Zona morta**: em `BulletBillHandler`, se `dx + 40 < 80` (jogador a menos de **40 px = 2,5 tiles** de qualquer lado) o projétil é descartado — o canhão não atira com o jogador perto; a wiki acrescenta "They will not fire if the player is directly above one or completely within a sprite box next to one" [W-BillBlaster]. Direção: sempre **para o lado do jogador**. Velocidade `BulletBillXSpdData = $18/$E8` → **1,5 px/q = 90 px/s** (exatamente a caminhada de Mario). Som `Sfx_Blast` ("fireworks/gunfire") e `EnemyFrameTimer = $0A` (10 q) no disparo. Cadência (ESTIMADO): 14 decrementos com probabilidade ≈3/16 por quadro (3 slots livres) → ≈75 q ≈ 1,25 s por canhão no modo normal; ≈37 q no difícil; mais lento com slots ocupados. Projéteis "frenzy" (8-2 etc.) nascem fora da tela a uma altura aleatória (`Enemy17YPosData`), um por vez, a 1,5 px/q para a esquerda, com ≥32 q entre lançamentos.
- **Derrota/interações**: pisão (200 pts, sem bônus em cadeia; rebote −3 px/q), estrela; **imune a fogo**; casco só mata os vindos de fora da tela ("not from Turtle Cannons"); tocar a bandeira apaga os Bullet Bills [W-Bullet][D-SMB1]. Em SMB3 `OAT_FIREIMMUNITY` e `OA2_NOSHELLORSQUASH` [D-SMB3].
- **SMB3 (DOCUMENTADO [D-SMB3])**: acelera 1/16 px/q a cada 2 q (≈112 px/s²) até `±$18` = 1,5 px/q; o **Missile Bill** (teleguiado) inverte e volta ao errar ("turn around and fly back towards Mario if it misses" [W-Bullet]).
- **SMW (DOCUMENTADO [D-SMW])**: `BulletSpeedX = $20` → **2 px/q = 120 px/s** horizontal; diagonais 1,5/1,5 px/q; vertical 2 px/q; Torpedo Ted e Banzai Bill como variantes [W-Bullet].
- **NSMB/Wii/U/Wonder**: "Bill Blasters also briefly expand when shooting Bullet Bills" (telegraph visual, Wii); congeláveis; NSMBU pisados "fall offscreen without tumbling"; Wonder: Seeker Bullet Bills "stick onto surfaces and fly towards the players on contact"; Missile Megs servem de plataforma [W-Bullet][W-BillBlaster].
- **Para o Lume**: arquétipo "lançador" na variante **torre** (§6.4) — é o atual `shooter` (650 px de alcance, 2,2 s, 180 px/s). Ajustes: zona morta 75 px, não atirar com o jogador em cima, projétil a 220 px/s (= caminhada), pisável e à prova de fogo, "flash" de 0,17 s + som no disparo.

### 3.10 Bob-omb

- **OFICIAL** — Manual SMB2: "He has a terrible temper. When he gets angry, he explodes." [W-BobProf]; manual SMB3: "As long as he's walking, Bob-omb seems cute. Be very careful when he starts to flash. He will explode destroying everything around him." [M-SMB3]; manual SMW: "These explode and scatter stars after a set time. Some of the Bob-ombs use parachutes to drop from the sky." [M-SMW].
- **SMB3 (DOCUMENTADO [D-SMB3])**: nasce andando **para o lado do jogador** (`BobOmb_StartXVel`); anda a ±`$10`?/`$08` com pulinhos de `vy = −$20` ao tocar o chão (animação de passos de 8 em 8 q); inverte em paredes. **Pisão**: `Var5 = 1`, `Objects_Timer = $FF` → **255 q = 4,25 s** de pavio; `BobOmb_FlashToExplode` alterna frames e o objeto "pisca cores" quando o timer é **< $40 (64 q = 1,07 s)**; rebote do jogador −3 px/q. Pisado, pode ser **chutado** (`BobombKickXVel = ±$28` = 2,5 px/q = 150 px/s, + metade da velocidade do jogador se no mesmo sentido; `vy = −$20` = −2 px/q) ou carregado; a cada 64 q "March toward Player" (reorienta). **Explosão**: estado 2, dura `$28` = 40 q (0,67 s), som "Ba-boom", fere o jogador e mata inimigos; em SMB3 "it will not destroy Brick Blocks" [W-Bobomb]; imune a fogo (`OAT_FIREIMMUNITY`); Kuribo's Shoe mata direto; variante sem chave acende sozinha e "Stomping them makes them take longer to explode" [W-Bobomb].
- **SMW (DOCUMENTADO [D-SMW])**: sprite "rápido" (0,75 px/q = 45 px/s) com bit "segue Mario"; ao fim do seu timer de caminhada torna-se **atordoado** (status 9, carregável) com `$40` = 64 q até explodir; som `SFX_KAPOW`; manual: "walk quickly back and forth before they flash and then explode"; capa/pisão o deixam carregável; entrar em cano carregando-o desarma pela fase [W-Bobomb].
- **NSMB/Wii/U/Wonder**: pisão ou **bola de fogo** acendem o pavio ("simply ignites and immobilizes it"); explosões "can destroy almost all types of blocks"; lava/chama = explosão instantânea; congelável; Wonder: Babooms soltam fogos [W-Bobomb]. SMB2: "They chase the player for a short while before exploding" [W-Bobomb].
- **Telegraphing**: piscar nos últimos 64 q (SMB3/SMW), som de pavio/explosão.
- **Para o Lume**: arquétipo "explosivo" (§6.7): PATROL (rápido) → FUSE (4,25 s, pisca no último 1,07 s; pisão/fogo acendem; chutável) → EXPLODE (0,67 s, raio ≈56 px, quebra tijolos, fere jogador e inimigos) → DEFEATED.

### 3.11 Lakitu (e Spiny)

- **OFICIAL** — Manual SMB1 (p. 11–13): "The mysterious turtle who controls the clouds. He chases after Mario and drops Spiny's eggs on top of him. 800 PTS."; Spiny: "Lakitu's pet, but a wild fighter. You can't kill him by jumping on top of him."; ovos: "You can't destroy them by jumping on them." [M-SMB1][W-LakituProf][W-SpinyEgg].
- **Perseguição em SMB1 (DOCUMENTADO [D-SMB1])**: `PlayerLakituDiff` limita |dx| a `$3C` = **60 px**; se Lakitu está além disso **e se afastando**, desacelera 1 unidade/q até zero e inverte. `ChkPSpeed` escolhe a velocidade-base por **estado do jogador**: `LakituDiffAdj = $15,$30,$40` → **21 unid. (1,31 px/q = 79 px/s)** com o jogador parado, **48 (3 px/q = 180 px/s)** andando com a tela rolando, **64 (4 px/q = 240 px/s)** correndo (`Player_X_Speed ≥ $19`) com rolagem ≥ 2; de cada base subtrai-se `(|dx| & $3C)/4` (até 15 unid.). Ou seja, Lakitu só é mais rápido que Mario (2,5 px/q correndo) quando Mario corre — para conseguir passar à frente. Ao ser derrotado, reaparece quando `LakituReappearTimer` chega a 7 (incrementado a cada 128 q) ≈ **15 s**; sai da tela a 1 px/q quando o nível o desativa; "moves offscreen whenever the player character is about to activate the flagpole" [W-Lakitu].
- **Arremesso em SMB1 (DOCUMENTADO [D-SMB1])**: `LakituAndSpinyHandler` roda quando `FrenzyEnemyTimer` expira e o recarrega com `$80` = **128 q (2,13 s)**; não lança se o jogador estiver acima de `Player_Y_Position < $2C` (44 px do topo) nem se Lakitu não estiver no estado normal. **Telegraph**: o desenhador usa o frame alternativo "escondido na nuvem" quando `FrenzyEnemyTimer < $10`, isto é, nos **16 q (0,27 s)** anteriores ao lançamento (a wiki fala em "about one second" — divergência, §10). O ovo nasce 8 px acima da nuvem com `vy = −3 px/q` e cai com gravidade `$20/256` (0,125 px/q² = 450 px/s², máx. 3 px/q); a velocidade horizontal calculada por `PRDiffAdjustData` é **perdida** ("set horizontal speed to zero because previous contents of A were lost") — o ovo cai reto; a wiki registra que "code leftovers suggest the eggs were meant to move horizontally" [W-SpinyEgg]. Spiny eclodido: 0,5 px/q, vira-se para o jogador em 7/8 dos pousos, não pisável (`EnemyStomped` → `InjurePlayer`), morre com fogo/estrela/casco/bloco por baixo [D-SMB1][W-Spiny]. Limite prático: com 4 Spinies em tela, Lakitu para de lançar (5 slots) [W-Spiny].
- **SMB3 (DOCUMENTADO [D-SMB3])**: acelera 1/16 px/q a cada 2 q (≈112 px/s²) até `±$20` = **2 px/q = 120 px/s** na direção do jogador (foge quando um objeto de evento o desativa); acompanha a rolagem da tela; lançamento: a cada **64 q** (128 q em fases com rampas) o timer recebe `$1F` = 31 q e o inimigo é lançado quando chega a 1; entre 31 e 16 o sprite **afunda na nuvem** (~15 q de telegraph); fases com rampas usam "ovo verde" inofensivo que rola ("throw at half the rate of the red-throwing ones" [W-Lakitu]); com ~4 Spinies/ovos presentes "it will stop throwing new ones, but continue to mime doing so" [W-Lakitu]. Derrotado, cai e respawna "two screens behind".
- **SMW**: "Lakitus follow the player character directly"; derrotá-lo com projétil deixa a nuvem utilizável; Lakitus em canos emergem como Piranhas e não saem com Mario em cima do cano [W-Lakitu]. Spiny Eggs e Spinies podem ser pisados com spin jump [W-SpinyEgg][W-Spiny].
- **NSMB/Wii/U/Wonder**: cuidar da nuvem (1000 pts no DS); no Wii o pisão pode deixar a nuvem; alguns jogam moedas; U: Piranha Pods; Wonder: trio numa nuvem jogando moedas/1-UPs [W-Lakitu]. Spiny no DS vira ovo na água [W-Spiny].
- **Para o Lume**: "lançador aéreo" (§6.4): CHASE em X com velocidade escalonada pelo estado do jogador (parado/andando/correndo) e teto de distância; ATTACK a cada ~2,1 s com PREPARE_ATTACK de ≈0,27 s (afundar). Ovos devem ter leve componente horizontal (intenção original).

### 3.12 Thwomp (e Konk)

- **OFICIAL** — Manual SMB3: "If Mario comes close, Thwomp will try to crush him. Since Thwomp is covered with thorns, Mario can't touch him." [M-SMB3]; manual SMW: "A nasty stone ghost that guards the castles and fortresses for the Koopas. If Mario comes close, Thwomp will try to crush him. The trouble is, if you don't pass it, you can't go on." [M-SMW]; cartão NSMBW: "These killer crushers don't have a sense of humor" [W-ThwompProf].
- **SMB3 (DOCUMENTADO [D-SMB3])**: máquina de 3 estados. `Thwomp_WaitForPlayer`: exige todos os sprites **em tela** e `dx + $24 < $50` → **−36 ≤ dx < 44 px** (≈ ±40 px = 2,5 tiles, assimetria de 4 px porque o X foi centrado com +4). `Thwomp_FallToGround`: `vy += 4` unid./q (0,25 px/q² = **900 px/s²**) até `$70` = **7 px/q = 420 px/s**; ao tocar o chão: `Level_Vibration = $18` (tremor de 24 q), som `SND_LEVELBABOOM`, timer `$40` = **64 q (1,07 s)**. `Thwomp_ReturnToOrigin`: sobe a `−$10` = **1 px/q = 60 px/s** até o Y original e volta a esperar. Flags: `FIREIMMUNITY`; contato sempre fere (`Player_HitEnemy` sem pisão). Variantes deslizantes (esquerda/direita, vertical, diagonal). Derrota: estrela, martelo (Hammer Suit), estátua Tanooki [W-Thwomp].
- **SMW (DOCUMENTADO [D-SMW])**: mesma máquina com **duas zonas**: `dx + $40 < $80` (≈ **±64 px**) muda a expressão para "olhando para baixo" (`$1528 = 1`) e `dx + $24 < $50` (≈ **±40 px**) dispara a queda com a expressão "bravo" (`$1528 = 2`); queda `vy += 4` até `$3E` = **3,875 px/q = 232 px/s** (metade do SMB3); impacto: `ScreenShakeTimer = $18`, `SFX_KAPOW`, espera `$40` = 64 q; subida `$F0` = −1 px/q. A wiki descreve: "peer down at the player's character when he approaches" e "enraged expression when falling" [W-Thwomp]. Pode-se dar spin jump em cima [W-Thwomp].
- **NSMB/Wii/U**: "act as in SMB3"; Big Thwomps quebram blocos; NSMBW "can only be defeated by the Star power-up or a Simultaneous Ground Pound" [W-Thwomp]. Super Mario Maker: param na altura em que foram colocados [W-Thwomp]. Wonder: **Konk** "function very similarly to Thwomps, as their main form of attack is dropping downwards when the player is beneath them"; Konk azul "attack from below, flying upwards when the player is above them"; "Both colors are also capable of moving left and right"; "They can be stood on or touched by their sides without taking damage" [W-Konk].
- **Telegraphing**: SMW em dois estágios (olhar a ±64 px, raiva a ±40 px); SMB3 só a queda; o tremor + som no impacto são o aviso de "pode passar agora" (1,07 s de janela).
- **Para o Lume**: arquétipo "blindado" na variante **esmagador** (§6.5): IDLE → ALERT (|dx| < 120 px: muda a cara) → ATTACK/DROP (|dx| < 75 px; 880 px/s², teto 700 px/s) → RECOVER (tremor 0,4 s + espera 1,07 s) → RISE (112 px/s). Opção Konk: superfície segura em cima/laterais.

### 3.13 Dry Bones

- **OFICIAL** — Manual SMB3: "A mummified turtle? No matter how many times you jump on it, it'll come back to life." [M-SMB3]; cartão NSMBW: "These boney Koopas will pace back and forth endlessly" [W-DryProf].
- **SMB3 (DOCUMENTADO [D-SMB3])**: anda a `$08` = 0,5 px/q (`$0A` contra esteira); `OAT_BOUNCEOFFOTHERS`, `FIREIMMUNITY`, `TAILATKIMMUNE`. **Pisão** (`ObjHit_DryBones`): `Var5 = 9`, `vx = 0`, rebote −4 px/q, som `SND_LEVELCRUMBLE` (o mesmo de quebrar tijolo, [W-DryBones]) e conta como abate. **Remontagem**: `Var5` decresce com `DryBones_ReassembleTimers = $10,$0A,$06,$06,$06,$06,$FF,$0A` → frame "desmontando" por 10 q, **pilha de ossos por 255 q (4,25 s)**, 4×6 q de "chacoalhar" (cabeça sobe e desce — `DryBones_HeadYOff`), 10 q, 16 q de levantar → total ≈ **315 q ≈ 5,25 s**, dos quais os últimos ≈50 q (0,8 s) são a animação-telegraph; ao levantar, **vira-se para o jogador** (`Object_CalcCoarseXDiff`). Derrota: estrela ou martelos [W-DryBones].
- **SMW (DOCUMENTADO [D-SMW])**: 0,5 px/q; "turns around at ledges, like Red Koopa Troopas" [W-DryBones]; caído, o sprite **treme horizontalmente nos últimos $40 = 64 q** antes de levantar e então `FaceMario`; variantes jogam ossos; Bony Beetle usa a mesma rotina com ciclo de espinhos de `$A0` = 160 q. Derrota: estrela ou capa [W-DryBones].
- **NSMB/Wii/U/2/Run/Wonder**: a cabeça se separa; se cai em lava/poço "takes longer to revive"; no Wii um Dry Bones em recuperação pode ser pisado; NSMBU "flash a red glare" ao remontar; derrota por Mega Mushroom, estrela, Blue Shell, POW, casco, Ice Ball; Wonder: tromba de elefante derrota permanentemente [W-DryBones].
- **Para o Lume**: "blindado" na variante **esqueleto** (§6.5): PATROL (vira na borda) → stomp → STUNNED (4,4 s + 0,8 s de remontagem com tremor) → PATROL virado para o jogador; imune a fogo; só estrela/explosão matam.

### 3.14 Cheep Cheep (e parentes aquáticos)

- **OFICIAL** — Manual SMB1 (p. 13): "Usually found in the water, but also sprouts wings and flies so you have to be careful in the air too. Can't be killed from above while she's in the water. 200 PTS." [M-SMB1][W-CheepProf]; manual SMW (Rip Van Fish): "This little fellow is always taking a nap, but when Mario comes along, he wakes up, and sets off in hot pursuit." [M-SMW].
- **SMB1 nadadora (DOCUMENTADO [D-SMB1])**: `SwimCCXMoveData = $40/$80` subtraídos da força horizontal por quadro → cinza **0,25 px/q = 15 px/s**, vermelha **0,5 px/q = 30 px/s**, sempre para a esquerda; onda vertical de **0,125 px/q (7,5 px/s)** invertendo a **±15 px** do Y original (período ≈ 8 s — ESTIMADO); os dois primeiros slots nadam reto; bit do LFSR decide se começa subindo ou descendo. Em área aquática **qualquer contato fere** (`AreaType == 0 → InjurePlayer`); fogo/estrela matam [D-SMB1]. Wiki: "swim towards the player character in either a straight line or a wavy pattern"; vermelhas "move moderately fast", cinzas "move slower" [W-Cheep].
- **SMB1 voadora (DOCUMENTADO [D-SMB1])**: `InitFlyingCheepCheep` só com `FrenzyEnemyTimer` expirado (recarga aleatória `$10,$60,$20,$48` = 16–96 q), máx. 3 em tela (4 a partir de 5-3); `vy = $FB` = **−5 px/q = −300 px/s** com gravidade `$0D/256` = 0,0508 px/q² (183 px/s²) e teto 5 px/q → ápice ≈ 246 px = a tela inteira (ESTIMADO); `FlyCCXSpeedData` 0,31–0,875 px/q (19–52 px/s) sorteados e enviesados pela velocidade do jogador; pisável (200 pts); aparecem em 2-3, 7-3 e 8-4 [W-Cheep].
- **SMB3 (DOCUMENTADO [D-SMB3])**: Spiny Cheep: nasce a ±8 unid. (0,5 px/q) **em direção ao jogador**, patrulha 96 px (origem −48…+48), onda vertical acelerando 1/16 a cada 8 q até ±0,5 px/q, inverte em paredes; `NOTSTOMPABLE`. "Chargin'" Cheep (Big Bertha): acelera 1/16 por q até 2 ou 6 px/q, inverte nos limites grossos 16/112, **salta** (`vy = −$28` = −2,5 px/q) quando a ≤ 6 unidades grossas (≈96 px) horizontais e ≤ 24 px verticais do jogador. Cheep de poça em poça: `vx = ±1 px/q`, `vy = −3,4/−4,4/−3,9 px/q`. Wiki: vermelhas "swim before leaping from the water to hit Mario" [W-Cheep].
- **SMW (DOCUMENTADO [D-SMW])**: `InitFish` dá **±$10 = 1 px/q = 60 px/s** para o lado do jogador; variante vertical vira-se para Mario; fora da água, pulos aleatórios. **Rip Van Fish**: dorme até `−48 ≤ dx < 48` **e** `−48 ≤ dy < 48` (ou apito do Chargin' Chuck); perseguindo, acelera 1/16 a cada 8 q (≈28 px/s²) em X e Y até **±1 px/q (60 px/s)**; a perseguição dura um contador de `$FF` decrementado a cada 2 q → **≈510 q ≈ 8,5 s**, depois volta a dormir (a wiki descreve como "once Mario swims a far enough distance [...] goes back to sleep" [W-RipVan]); com estrela, as velocidades são **invertidas** (foge) [D-SMW][W-RipVan]. Fora da água cai a 1 px/q.
- **NSMB/Wii/U/Wonder**: Deep Cheep "swim toward Mario or Luigi" e "give up pursuing [...] if they swim behind or far enough from them"; no Wii as Cheep Cheeps "can now collide with each other and can push one another"; Wonder: "can be defeated by stomping, 'unlike previous appearances'" debaixo d'água, mas ferem pelos lados/baixo [W-Cheep][W-DeepCheep].
- **Para o Lume**: **a água do Lume é letal** ("Água, lava e quedas custam uma vida", README), então o arquétipo "aquático" (§6.8) tem duas formas: **saltador** (Cheep voadora: LEAP de baixo da tela, pisável) e, para uma eventual fase nadável, **nadador/perseguidor** (Rip Van Fish/Deep Cheep: SWIM ↔ CHASE 8,5 s).

### 3.15 Chain Chomp

- **OFICIAL** — Manual SMB3: "Although tied to a block by a chain, Chain Chomp is quite a tough enemy. Only invincible Mario is able to defeat him." [M-SMB3]; cartão NSMBW: "Chain Chomps act much like bad-tempered dogs on leashes." [W-ChompProf].
- **SMB3 (DOCUMENTADO [D-SMB3])**: 3 estados. `ChainChomp_ChooseLunge`: com o timer zerado, calcula |dx|; se **< 64 px**, o índice é `|dx|/16` (0–3) e a investida usa `ChainChomp_ChaseXVel = $50,$30,$40,$20` (5, 3, 4, 2 px/q = 300, 180, 240, 120 px/s) e `ChaseYVel = −$20,−$40,−$30,−$50` (−2, −4, −3, −5 px/q) — **quanto mais perto o jogador, mais rasa e rápida a investida**; se ≥ 64 px, índice aleatório ("just sort of dart about randomly"); timer `$28` = **40 q (0,67 s)**; `Var1++` e, ao chegar a `$32` = **50 investidas**, `ChainChomp_BreakFree`. `ChainChomp_DoMove`: ao fim do timer, espera aleatória `$20–$3F` (32–63 q), zera `vy` e volta ao X do poste a ±0,5 px/q; a corrente (4 elos) limita X/Y (`Var10/Var11/Var12`). Flags: `FIREIMMUNITY`, `NOTSTOMPABLE`, `TAILATKIMMUNE`, `NOSHELLORSQUASH`. Solto, "hop forward along the ground" com `Chomp_JumpYVels = −4/−6 px/q` e `Chomp_XVels = ±3 px/q`. A wiki: "A Chain Chomp can break free after 160 seconds, though it sometimes takes longer" e "When about to break free, their chains begin flashing" — coerente com 50 × (0,67 + 0,5–1,05 s + investida) ≈ 150–170 s (ESTIMADO) [W-ChainChomp]. Derrota: estrela, casco, martelo, estátua [W-ChainChomp].
- **NSMB/Wii/U/2**: "Their post can now be ground-pounded to release them and drop three coins" (DS: 3 golpes; U: "need only one ground-pound"); solto, destrói tijolos e pode ferir outros jogadores (Wii); NSMB2 "Only Invincible Mario or Gold Mario can defeat" [W-ChainChomp]. SMW: só em dados não usados [W-ChainChomp].
- **Telegraphing**: pausa de 0,5–1 s entre investidas, "chomping" constante, corrente piscando antes de soltar [W-ChainChomp].
- **Para o Lume**: variante **acorrentado** do arquétipo "blindado" (§6.5): IDLE (volta ao poste) → PREPARE_ATTACK (0,2 s) → ATTACK/LEAP (tabela por distância) → RECOVER (0,53–1,05 s); corrente de ≈90 px; opcional soltar-se após N investidas ou ao bater no poste 3×.

---
## 4. Tabela consolidada de parâmetros (DOCUMENTADO, derivados de análise de terceiros; conversões ESTIMADAS a 60 Hz)

| Parâmetro | Título | Valor bruto | Conversão | Fonte |
| --- | --- | --- | --- | --- |
| Velocidade de andar (Goomba/Koopa/Buzzy/Spiny/Dry Bones) | SMB1, SMB3, SMW | `$08` (1/16 px/q) | 0,5 px/q = 30 px/s | [D-SMB1][D-SMB3][D-SMW] |
| Andar "rápido" (2.ª volta SMB1; Koopa azul/amarelo, Bob-omb SMW) | SMB1, SMW | `$0C` | 0,75 px/q = 45 px/s | [D-SMB1][D-SMW] |
| Hammer Bro "shimmy" | SMB1 / SMB3 | `±$04` / `±$06`, inverte a cada 64 q | 15 px/s / 22,5 px/s | [D-SMB1][D-SMB3] |
| Casco chutado | SMB1 / SMW | `$30` / `$2E`,`$34` | 180 px/s / 172,5 e 195 px/s (PAL 206/232) | [D-SMB1][D-SMW] |
| Bob-omb chutado | SMB3 | `±$28` (+½ vx do jogador) ; `vy = −$20` | 150 px/s ; −120 px/s | [D-SMB3] |
| Bullet Bill | SMB1 / SMB3 / SMW | `$18` / `$18` (acel. 1 a cada 2 q) / `$20` | 90 / 90 / 120 px/s | [D-SMB1][D-SMB3][D-SMW] |
| Zona morta do canhão | SMB1 | `dx + 40 < 80` | ±40 px (2,5 tiles) | [D-SMB1] |
| Piranha: zona de "não sair" | SMB1 / SMB3 / SMW | `|dx| < $21` / `dx + $1B < $37` / idem | ±33 px / −27…+28 px / −27…+28 px | [D-SMB1][D-SMB3][D-SMW] |
| Piranha: velocidade e percurso | SMB1 / SMB3 / SMW | 1 px a cada 2 q, 24 px / `$10` / `$10` | 30 px/s (0,8 s) / 60 px/s / 60 px/s (48 q) | idem |
| Piranha: espera nos extremos | SMB1 / SMB3 / SMW | `$40` / `$30` (`$60` fogo) / `$20` dentro, `$20` fora | 1,07 s / 0,8 s (1,6 s) / 0,53 s | idem |
| Thwomp: gatilho de queda | SMB3 / SMW | `dx + $24 < $50` | −36…+44 px (≈ ±40 px) | [D-SMB3][D-SMW] |
| Thwomp: gatilho de "olhar" | SMW | `dx + $40 < $80` | ≈ ±64 px | [D-SMW] |
| Thwomp: aceleração / teto de queda | SMB3 / SMW | +4 unid./q ; `$70` / `$3E` | 900 px/s² ; 420 / 232 px/s | [D-SMB3][D-SMW] |
| Thwomp: tremor, espera, subida | SMB3 / SMW | `$18` q, `$40` q, `−$10` | 0,4 s, 1,07 s, 60 px/s | [D-SMB3][D-SMW] |
| Boo: atraso para perseguir | SMB3 | `$14` q sem ser olhado | 0,33 s | [D-SMB3] |
| Boo: aceleração / máx. | SMB3 / SMW | 1 unid./q, `$10` / 1 unid. por 8 q, `$08` | 225 px/s², 60 px/s / 28 px/s², 30 px/s | [D-SMB3][D-SMW] |
| Boo: decisão / giro | SMW | a cada `$20` q ; giro `$1F` q | 0,53 s ; 0,52 s | [D-SMW] |
| Lakitu: velocidade-base por estado do jogador | SMB1 | 21 / 48 / 64 unid. − |dx|/4 (teto 60 px) | 79 / 180 / 240 px/s | [D-SMB1] |
| Lakitu: acel. e máx. | SMB3 | 1 unid. a cada 2 q até `$20` | 112 px/s², 120 px/s | [D-SMB3] |
| Lakitu: intervalo de lançamento / telegraph | SMB1 / SMB3 | 128 q / 16 q ; 64 q (128 em rampas) / ~15 q | 2,13 s / 0,27 s ; 1,07 s / 0,25 s | [D-SMB1][D-SMB3] |
| Lakitu: reaparecimento | SMB1 | 7 × 128 q | ≈ 15 s | [D-SMB1] |
| Spiny egg: `vy`, gravidade | SMB1 | `−3 px/q`, `$20/256`, teto 3 px/q | −180 px/s, 450 px/s² | [D-SMB1] |
| Hammer Bro: entre saltos / `vy` | SMB1 e SMB3 | aleatório `$C0–$FF` q ; `−6` ou `−3 px/q` | 3,2–4,25 s ; −360 / −180 px/s | [D-SMB1][D-SMB3] |
| Hammer Bro: entre martelos | SMB1 / SMB3 | `$30` (`$1C` difícil) / ≈37 q chão, ≈73 q ar | 0,8 s (0,47 s) / 0,6 s, 1,2 s | [D-SMB1][D-SMB3] |
| Martelo: `vx`, `vy`, gravidade, teto | SMB1 | `$10`, `$FE`, `$10/256`, 4 px/q | 60 px/s, −120 px/s, 225 px/s², 240 px/s | [D-SMB1] |
| Hammer Bro: começa a avançar | SMB1 | `$80` (`$50`) ticks × 21 q | 44,8 s (28 s); só se jogador à esquerda | [D-SMB1] |
| Casco pisado: revive | SMB1 | `$10` (`$0B`) ticks × 21 q ; pernas quando < 5 ticks | 5,3–5,6 s (3,9 s) ; ≈1,5 s antes | [D-SMB1] |
| Goomba achatado | SMB1 | timer de `$10` até `$0E` | ≈0,35–0,7 s | [D-SMB1] |
| Atordoamento (Galoomba/Buzzy/Mechakoopa/Bob-omb) | SMW | `$FF` q (acelera animação < `$30`, pulinho em 8) | 4,25 s (telegraph 0,8 s) | [D-SMW] |
| Dry Bones: caído / remontagem | SMB3 / SMW | ≈315 q (255 de pilha + ≈50 de animação) / tremor nos últimos `$40` q | 5,25 s (0,8 s) / 1,07 s de tremor | [D-SMB3][D-SMW] |
| Bob-omb: pavio / piscar / explosão | SMB3 / SMW | `$FF` q / < `$40` / `$28` q ; `$40` q | 4,25 s / 1,07 s / 0,67 s ; 1,07 s | [D-SMB3][D-SMW] |
| Chain Chomp: zona de mira / investida / espera / soltar | SMB3 | 64 px ; `$28` q ; `$20–$3F` q ; 50 investidas | 0,67 s ; 0,53–1,05 s ; ≈150–170 s | [D-SMB3] |
| Chain Chomp: investida (vx, vy) por faixa de 16 px | SMB3 | (5,−2) (3,−4) (4,−3) (2,−5) px/q | (300,−120) (180,−240) (240,−180) (120,−300) px/s | [D-SMB3] |
| Cheep nadadora | SMB1 / SMW | `$40`/`$80` de força ; onda 0,125 px/q ±15 px / `$10` | 15 / 30 px/s ; 7,5 px/s / 60 px/s | [D-SMB1][D-SMW] |
| Cheep voadora | SMB1 | `vy = −5 px/q`, g `$0D/256`, vx 5–14 unid., 16–96 q, máx. 3 | −300 px/s, 183 px/s², 19–52 px/s | [D-SMB1] |
| Rip Van Fish: zona de despertar / acel. / máx. / duração | SMW | ±48 px (X e Y) / 1 unid. por 8 q / `$10` / `$FF` a cada 2 q | 90 px → ; 28 px/s² ; 60 px/s ; 8,5 s | [D-SMW] |
| Chargin' Cheep: zona de salto | SMB3 | 6 unid. grossas (16 px) horiz., 24 px vert.; `vy = −$28` | ≈96 px ; −150 px/s | [D-SMB3] |
| Paratroopa verde pulante | SMB1 / SMB3 | `vy = −3 px/q` (SMB3: −1,5 na água) | −180 px/s (−90 na água) | [D-SMB1][D-SMB3] |
| Rebote do pisão | SMB1 / SMB3 | `−4`/`−3 px/q` / `−$40`,`−$30` | −240/−180 px/s / −240, −180 px/s | [D-SMB1][D-SMB3] |
| Pop-up ao ser batido por baixo/casco | SMB1 | `vy = −3 px/q`, `vx = ±1 px/q` | −180 px/s, ±60 px/s | [D-SMB1] |

---

## 5. Padrões transversais

### 5.1 Seis tipos de percepção (todos sem linha de visão)

| Tipo | Quem usa | Como funciona | Rótulo |
| --- | --- | --- | --- |
| **Nenhuma** | Goomba, Koopa, Buzzy, Shy Guy, Cheep nadadora, Spiny | só paredes, bordas e outros inimigos mudam a direção | DOCUMENTADO [D-SMB1] |
| **Janela horizontal fixa** | Piranha (±33/±27 px), Bill Blaster (±40 px), Thwomp (±40 px; SMW +±64 px), Chain Chomp (64 px), Hoppycat ("gets in range") | comparação de `|dx|` com uma constante; a janela vertical raramente existe (Thwomp exige só "em tela") | DOCUMENTADO [D-SMB1][D-SMB3][D-SMW] |
| **Janela X e Y** | Rip Van Fish (±48 px nos dois eixos), Chargin' Cheep (96 px × 24 px), Konk (jogador "beneath") | caixa em torno do inimigo | DOCUMENTADO [D-SMW][D-SMB3]; OBSERVADO [W-Konk] |
| **Direção do olhar do jogador** | Boo (e Big Boo); negado em Boo Buddies/NSMB2 | compara `sign(dx)` com `player.facing`; atraso de 20 q (SMB3) ou decisão a cada 32 q (SMW) | DOCUMENTADO [D-SMB3][D-SMW] |
| **Lado do jogador** | Hammer Bro, Bullet Bill, Venus, Dry Bones ao reviver, Koopas ao pousar, Bob-omb ao nascer, Spiny Cheep ao nascer | `EnemyFacePlayer`/`Level_ObjCalcXDiffs`: vira-se para o jogador em momentos discretos (nascer, pousar, reviver, atirar) | DOCUMENTADO [D-SMB1][D-SMB3] |
| **Estado do jogador** | Lakitu (velocidade escalonada por `Player_X_Speed` e rolagem), Cheep voadora (vx enviesado pela velocidade do jogador), Hoppycat (pula quando o jogador pula), Rip Van Fish (foge com estrela) | lê a entrada/velocidade do jogador, não a posição | DOCUMENTADO [D-SMB1][D-SMW]; OBSERVADO [W-Hoppycat] |

Consequência de design: as "inteligências" dos Mario 2D são **previsíveis e simétricas** — a mesma distância produz sempre a mesma reação — e por isso aprendíveis. O `PerceptionProfile` atual do Lume (linha de visão amostrada, campo de visão atrás, tempo de reação e esquecimento) é mais rico do que qualquer inimigo clássico; a recomendação (§7) é manter a infraestrutura, mas configurar os perfis clássicos com `needs_line_of_sight=False`, `field_of_view_behind=∞` e `reaction_time` ∈ {0; 0,33 s}.

### 5.2 Catálogo de telegraphing (o que avisa, quanto antes)

| Inimigo | Sinal | Antecedência | Fonte |
| --- | --- | --- | --- |
| Koopa pisado | pernas saem do casco | ≈1,5–1,75 s (SMB1) | [D-SMB1][W-Koopa] |
| Buzzy pisado | nenhum (SMB1); chacoalha (SMB3+) | — / ~0,5 s (OBSERVADO) | [W-Buzzy] |
| Galoomba tombado | animação 2× mais rápida, pulinho | 0,8 s | [D-SMW] |
| Lakitu | afunda na nuvem | 0,27 s (SMB1), ≈0,25 s (SMB3) | [D-SMB1][D-SMB3] |
| Thwomp | olhar para baixo (±64 px), cara brava (±40 px), tremor + som no impacto | ~0,1–0,5 s dependendo da aproximação; janela de 1,07 s | [D-SMW][D-SMB3] |
| Bob-omb | piscar | 1,07 s | [D-SMB3] |
| Dry Bones | ossos chacoalham / cabeça sobe e desce / "red glare" (NSMBU) | 0,8 s (SMB3), 1,07 s (SMW) | [D-SMB3][D-SMW][W-DryBones] |
| Chain Chomp | pausa + mordidas; corrente pisca antes de soltar | 0,53–1,05 s por investida | [D-SMB3][W-ChainChomp] |
| Piranha | subida lenta visível; som de mordida (NSMB) | 0,8 s | [D-SMB1][W-Piranha] |
| Bill Blaster | som "blast" + flash de 10 q; canhão "expande" (NSMBW) | ≈0,17 s | [D-SMB1][W-BillBlaster] |
| Hammer Bro | braço levantado no quadro do arremesso | 0 s (SMB1) | [D-SMB1] |
| Boo | rosto coberto ↔ aberto; giro de 31 q (SMW) | 0,33–0,5 s | [D-SMB3][D-SMW] |
| Casco em movimento | som de ricochete ("If you hear the sound of a ricochet, jump right away") | o tempo de o casco voltar | [M-SMB1] |
| Goombas (Wonder) | olhar, pânico, bocejo/sono; mordida no momento do dano | contínuo | [W-Goomba][ATD-2] |

### 5.3 Interações entre inimigos e com o cenário

- **Casco como projétil universal**: SMB1 mata todo inimigo tocado (cadeia 500→8000), quica em paredes, mata até Bullet Bills de fora da tela; SMB3 mata Boos e Chain Chomps; SMW cascos de Koopa amarelo invencíveis, Koopa azul chuta cascos, Paratroopa amarelo pula cascos [D-SMB1][W-Boo][W-ChainChomp][W-Koopa][W-Para].
- **Trânsito**: inimigos se viram ao colidir (SMB1 `EnemyTurnAround`; SMB3 `OAT_BOUNCEOFFOTHERS` em Buzzy/Dry Bones; NSMBW Cheep Cheeps "push one another") [D-SMB1][D-SMB3][W-Cheep].
- **Blocos**: bater no bloco sob o inimigo mata Goomba e vira Koopas/Buzzies de cabeça para baixo (SMB1); explosões de Bob-omb quebram tijolos a partir de NSMB (não em SMB3); Thwomps grandes quebram blocos (NSMB); Chain Chomp solto quebra tijolos (NSMBW) [D-SMB1][W-Bobomb][W-Thwomp][W-ChainChomp].
- **Imunidades cruzadas**: fogo não afeta Buzzy (SMB1), nem Boo/Thwomp/Dry Bones/Bob-omb/Bullet Bill/Chain Chomp (SMB3); fogo **acende** o Bob-omb em NSMBW; gelo congela quase tudo em NSMBW (Spiny fica congelado até quebrar) [D-SMB1][D-SMB3][W-Bobomb][W-Spiny].
- **Pontuação como reforço**: 100 (Goomba) → 200 (padrão) → 400 (asas) → 800 (Lakitu) → 1000 (Hammer Bro, casco em cadeia) [D-SMB1].

### 5.4 Ambiente

- **Água**: em SMB1 qualquer toque em área aquática fere (não há pisão); Spiny vira ovo na água (NSMB); Paratroopa pulante salta a −1,5 px/q na água (SMB3); Lakitu derrotado "na água" não acelera a queda (SMB3); Rip Van Fish fora da água cai a 1 px/q (SMW) [D-SMB1][W-Spiny][D-SMB3][D-SMW].
- **Lava/fogo**: Bob-omb explode na hora (NSMBW); Buzzy nada em lava (Wonder); Dry Bones não é afetado por lava (NSMBU) [W-Bobomb][W-Buzzy][W-DryBones].
- **Gelo**: SMW halves a desaceleração de Koopas sem casco em fases escorregadias; NSMBW congela inimigos em blocos de gelo carregáveis [D-SMW][W-Piranha].
- **Esteiras/rampas**: SMB3 ajusta a velocidade dos terrestres contra esteiras (0,375/0,3125 px/q; Dry Bones 0,625) e corrige o "virar na borda" dos Koopas vermelhos ao descer rampas [D-SMB3].
- **Tela**: Thwomp (SMB3) e Boo só agem com os sprites em tela; Lakitu (SMB3) renasce 2 telas atrás; Bullet Bills de fora da tela nascem na borda direita [D-SMB3][D-SMB1].

---
## 6. Biblioteca de arquétipos para o Lume

### 6.0 Método de conversão (ESTIMADO — decisão nossa, não valor oficial)

Os originais são 16 px de altura (Mario pequeno) e andam a 90 px/s; o Lume tem 30 px (pequeno) e anda a 220 px/s. Em vez de um fator único, usamos três, porque o que importa para a jogabilidade é a **razão** entre inimigo e jogador:

| Grandeza | Fator | Justificativa |
| --- | --- | --- |
| Distâncias (zonas de percepção, amplitudes, correntes) | **× 1,875** (16 → 30 px) | igual ao fator corporal usado em FISICA.md |
| Velocidades horizontais | **× 2,44** (90 → 220 px/s de caminhada) | preserva "o Goomba anda a 1/3 do jogador", "o casco é 1,2× a corrida" |
| Velocidades verticais de impulso | **× 2,46** (240 → 590 px/s de salto) | preserva "o rebote do pisão ≈ salto" |
| Tempos (timers, telegraphs, cadências) | **× 1** | ritmo é percebido em segundos, não em pixels (a Nintendo recalibrou os cascos PAL para manter px/s [D-SMW]) |
| Acelerações de queda de objetos | pela razão com a gravidade do jogador | SMB1 Mario cai a ~1575 px/s², Lume 1550: aplicar a mesma razão (ex.: Thwomp 900/1575 = 0,57 → 880 px/s²) |

Nomes dos arquétipos do Lume são originais (nenhum nome, forma ou sprite da Nintendo): **Trotador** (terrestre), **Casqueiro** (com casco), **Planador** (voador), **Arremessador** (lançador), **Sentinela** (blindado), **Sombra** (furtivo), **Faísca** (explosivo), **Saltador-do-lago** (aquático). Todos usam a `StateMachine`/`Blackboard` de `game/enemies/state_machine.py`; abaixo só os estados que **fazem sentido** para cada um. Novos fatos de `Blackboard` necessários: `player_looking_at_me` (sign(dx) oposto a `player.facing`), `player_speed` (|vx| do jogador), `player_below`/`player_above`, `on_screen`, `in_zone(lo, hi)` (janela assimétrica em dx), `player_star`, `player_grounded`.

Flags por arquétipo (equivalente das tabelas `OAT_/OA2_/OA3_` de SMB3 [D-SMB3]): `stompable` (pisar derrota/atordoa), `stomp_hurts` (pisar fere — espinhos), `fireproof`, `star_kills`, `shell_kills`, `explosion_kills`, `turn_at_edges`, `turn_on_enemy_contact`, `face_player_on_land`, `blocks_player` (pode-se ficar em cima — Konk/Shy Guy), `carryable` (se o Lume ganhar "pegar").

### 6.1 Trotador (terrestre) — originais: Goomba (SMB1/SMB3), Galoomba (SMW), Shy Guy (SMB2), Dry Bones sem a imortalidade

```
PATROL ──(parede | inimigo | borda se turn_at_edges)──▶ PATROL (inverte)
PATROL ──(pisão, stompable)──▶ DEFEATED (achatado 0,5 s, remove)          # Goomba
PATROL ──(pisão, variante tombável)──▶ STUNNED (4,25 s; animação 2× nos últimos 0,8 s) ──▶ PATROL (virado para o jogador)
STUNNED ──(toque lateral)──▶ SLIDE (sem ricochete, 0,5 s) ──▶ STUNNED
PATROL/STUNNED ──(fogo | casco | estrela | bloco por baixo | explosão)──▶ DEFEATED (pop-up −440 px/s, ±146 px/s)
```

| Parâmetro | Original | Lume proposto | Confiança |
| --- | --- | --- | --- |
| `walk_speed` | 0,5 px/q = 30 px/s (SMB1/3/SMW) | **72 px/s** + 6 px/s por mundo (hoje 55 + 7·mundo) | DOCUMENTADO → ESTIMADO |
| `fast_walk_speed` (variante) | 0,75 px/q = 45 px/s | **110 px/s** | DOCUMENTADO → ESTIMADO |
| `turn_at_edges` | Goomba não; Shy Guy rosa sim | parâmetro por instância; sonda atual de 2×7 px à frente dos pés (manter) | DOCUMENTADO |
| `face_player_on_land` | Koopas sim, Goomba não (SMB1) | padrão `False` para o Trotador | DOCUMENTADO |
| `squash_time` | ≈0,35–0,7 s | **0,5 s** | DOCUMENTADO → ESTIMADO |
| `stun_time` (tombável) | 255 q = 4,25 s | **4,25 s**, telegraph nos últimos **0,8 s** | DOCUMENTADO |
| `stomp_bounce` | −240 px/s (= salto parado SMB1) | manter **−390 px/s**; se o botão de salto estiver pressionado no instante do pisão, usar **−590 px/s** (pisão-salto) | ESTIMADO (design) |
| `knockback_on_hit` | vy −180 px/s, vx ±60 px/s | **−440 px/s**, **±146 px/s** | DOCUMENTADO → ESTIMADO |
| Expressão (Wonder) | olhar/pânico/sono | opcional: `ALERT` puramente visual quando |dx| < 150 px (não altera movimento) | OFICIAL [ATD-2] → ESTIMADO |

### 6.2 Casqueiro (com casco) — originais: Koopa Troopa verde/vermelho (SMB1), Buzzy Beetle (casco à prova de fogo)

```
PATROL ──(borda & red)──▶ PATROL (inverte)      PATROL ──(borda & green)──▶ FALL ──(pousa)──▶ PATROL (virado para o jogador)
PATROL ──(pisão)──▶ SHELL (timer 5,5 s; pernas em 1,5 s) ──(timer)──▶ PATROL (direção pseudoaleatória)
SHELL ──(toque do jogador)──▶ SLIDE (420 px/s para longe do jogador; quica em paredes; mata inimigos em cadeia; fere o jogador)
SLIDE ──(pisão)──▶ SHELL           SLIDE ──(parede)──▶ SLIDE (inverte, som "ricochete")
PATROL/SHELL/SLIDE ──(bloco por baixo | casco | estrela)──▶ STUNNED_FLIPPED (de cabeça para baixo, 5,5 s) ──▶ PATROL
PATROL ──(fogo, se não fireproof)──▶ DEFEATED
```

| Parâmetro | Original | Lume proposto | Confiança |
| --- | --- | --- | --- |
| `walk_speed` | 30 px/s | **72 px/s** | DOCUMENTADO → ESTIMADO |
| `shell_speed` | 180 px/s (SMB1: 1,2× a corrida de 150) ; 172–195 px/s (SMW) | **420 px/s** (1,24× a corrida de 340; hoje 360) | DOCUMENTADO → ESTIMADO |
| `shell_revive_time` | 5,3–5,6 s (3,9 s na 2.ª volta) | **5,5 s** nos mundos 1–3, **4,0 s** nos mundos 4–5 | DOCUMENTADO |
| `shell_legs_telegraph` | ≈1,5–1,75 s | **1,5 s** (frame com pernas) | DOCUMENTADO |
| `slide_kick_offset` | o casco nasce já em movimento | manter o deslocamento de 14 px do código atual | — |
| `shell_hits_player` | sim, sempre que em movimento | sim | OFICIAL [M-SMB1] |
| `demote_paratroopa_keeps_edge_rule` | não (bug do ID $01) | **sim** | DOCUMENTADO → decisão |
| `fireproof` (variante Buzzy) | sim | sim; o `armored` atual (44 px/s, 2 HP) vira esta variante | OFICIAL/DOCUMENTADO |
| `ceiling_variant` (Buzzy de teto) | cai quando o jogador se aproxima (janela não extraída) | HIDDEN no teto → DROP quando |dx| < 60 px e jogador abaixo → SLIDE a 420 px/s em direção ao jogador | OBSERVADO → ESTIMADO |
| Pontos | 100 → cadeia | manter 200 por abate, cadeia ×2 até 1600 | ESTIMADO |

Variante SMW ("sai do casco") fica fora do escopo: dobra a quantidade de estados e exige "pegar/carregar".

### 6.3 Planador (voador) — originais: Paratroopa vermelho (vertical), verde pulante, verde horizontal (SMB1); Cheep voadora pertence ao §6.8

```
FLY_OSCILLATE (senoide vertical ou horizontal; sem percepção) ──(pisão)──▶ demote → Casqueiro.PATROL (virado para o jogador)
HOP (anda 72 px/s; ao pousar, salta) ──(pisão)──▶ demote
FLY/HOP ──(fogo | casco | estrela)──▶ DEFEATED
```

| Parâmetro | Original | Lume proposto | Confiança |
| --- | --- | --- | --- |
| Oscilação vertical: percurso / velocidade de pico / período | ≈96 px / ≈1,06 px/q (64 px/s) / ≈6 s (SMB1, ESTIMADO) | **±90 px** em torno do centro, pico **160 px/s**, período **6 s**; hoje ±38 px a 2,2 rad/s (período 2,9 s) — alargar | ESTIMADO |
| Oscilação horizontal | contador triangular máx. $13 + ondulação ±1 px/4 q | **±120 px**, período **4 s**, ondulação vertical ±4 px | ESTIMADO |
| Pulo do verde pulante | vy −3 px/q = −180 px/s (≈41 px de altura) | **−440 px/s** (≈62 px = 2 corpos pequenos); gravidade do jogador | DOCUMENTADO → ESTIMADO |
| Pulo na água (SMB3) | −1,5 px/q | não se aplica (água letal) | — |
| `face_player_on_land` (pulante) | sim | sim | DOCUMENTADO |
| Demote | pisão tira as asas; 400 pts | pisão → Casqueiro (mantém cor/regra de borda) | DOCUMENTADO |

### 6.4 Arremessador (lançador) — quatro variantes

**(a) Torre** — original: Bill Blaster/Bullet Bill (SMB1); é o `shooter` atual.

```
IDLE ──(timer ≥ intervalo & |dx| ≥ zona morta & jogador não acima & |dx| < alcance)──▶ ATTACK (flash 0,17 s + som) ──▶ IDLE
Projétil: PATROL reto a 220 px/s para o lado do jogador; pisável (rebote −390); fireproof; morre em casco só se "externo"; vida = 1 largura de tela
```

| Parâmetro | Original | Lume | Confiança |
| --- | --- | --- | --- |
| Zona morta | ±40 px | **±75 px**; e não atirar com o jogador diretamente acima | DOCUMENTADO/OBSERVADO → ESTIMADO |
| Velocidade do projétil | 90 px/s (= caminhada) | **220 px/s** (= caminhada; hoje 180) | DOCUMENTADO → ESTIMADO |
| Intervalo | ≈1,25 s + aleatório (SMB1 ESTIMADO) | **2,0–2,6 s** aleatório (hoje 2,2 fixo) | ESTIMADO |
| Alcance | tela | **650 px** (manter) | — |

**(b) Emboscada** — original: Piranha Plant (SMB1/SMB3/SMW), Venus Fire Trap.

```
HIDDEN (1,07 s) ──(|dx| ≥ 62 px)──▶ EMERGE (0,8 s, 56 px/s) ──▶ ATTACK (1,07 s parado; variante cuspidora: 2 projéteis mirados em 0,53 s e 1,33 s) ──▶ RETREAT (0,8 s) ──▶ HIDDEN
HIDDEN ──(|dx| < 62 px)──▶ HIDDEN (re-espera)        * contato sempre fere; sem pisão; fogo/casco/estrela derrotam
```

| Parâmetro | Original | Lume | Confiança |
| --- | --- | --- | --- |
| Zona de "não sair" | ±33 px (SMB1); −27…+28 (SMB3/SMW) | **±62 px** | DOCUMENTADO → ESTIMADO |
| Velocidade/percurso | 30 px/s × 0,8 s = 24 px (SMB1); 60 px/s (SMB3/SMW) | **56 px/s × 0,8 s = 45 px** (altura do sprite do Lume) | DOCUMENTADO → ESTIMADO |
| Espera dentro/fora | 1,07 s / 1,07 s (SMB1); 0,8 / 0,8 (SMB3); 0,53 / 0,53 (SMW) | **1,07 s / 1,07 s** nos mundos iniciais, 0,8 nos finais | DOCUMENTADO |
| Projétil (Venus) | 2 bolas/saída, mira cima/baixo | **150 px/s** diagonal, vida 2 s | OBSERVADO → ESTIMADO |

**(c) Arremessador saltador** — original: Hammer Bro (SMB1/SMB3).

```
PATROL (shimmy ±37 px/s invertendo a cada 1,07 s; sempre de frente para o jogador)
  ──(timer_throw)──▶ PREPARE_ATTACK (0,25 s braço levantado) ──▶ ATTACK (martelo) ──▶ RECOVER (0,2 s) ──▶ PATROL
  ──(timer_jump 3,2–4,25 s)──▶ LEAP (−520 ou −760 px/s; atravessa plataformas por 0,5 s) ──▶ PATROL
  ──(após 20 s em tela)──▶ CHASE (72 px/s, só se o jogador estiver do lado "de fuga")
  ──(pisão | fogo | casco | estrela | bloco por baixo)──▶ DEFEATED (não entra em casco)
```

| Parâmetro | Original | Lume | Confiança |
| --- | --- | --- | --- |
| Shimmy | 15 px/s (SMB1) / 22,5 px/s (SMB3), inverte a cada 64 q | **37 px/s**, inverte a cada **1,07 s** | DOCUMENTADO → ESTIMADO |
| Cadência de arremesso | 0,8 s (0,47 s difícil) / ≈0,6 s | **0,8 s** (0,5 s no mundo 5) + telegraph **0,25 s** (adição) | DOCUMENTADO → ESTIMADO |
| Martelo | vx 60 px/s, vy −120 px/s, g 225 px/s² → ápice 32 px, ≈1,1 s de voo, alcance ≈4 tiles | **vx ±120 px/s, vy −230 px/s, g 430 px/s²** → ápice 60 px, voo 1,1 s, alcance ≈130 px | DOCUMENTADO → ESTIMADO |
| Entre saltos | 192–255 q | **3,2–4,25 s** aleatório | DOCUMENTADO |
| Impulso do salto | −3 ou −6 px/q (−180/−360 px/s) | **−520 / −760 px/s** | DOCUMENTADO → ESTIMADO |
| Avanço | 44,8 s (SMB1) | **20 s** (fases do Lume são curtas); opcional | DOCUMENTADO → ESTIMADO |

**(d) Arremessador aéreo** — original: Lakitu (SMB1/SMB3).

```
CHASE_X (altura fixa; alvo = x do jogador; velocidade-base escolhida pelo estado do jogador; desacelera e inverte se passar de 112 px)
  ──(timer 2,1 s)──▶ PREPARE_ATTACK (0,27 s afundando) ──▶ ATTACK (solta ovo: vy −300 px/s, vx 60 px/s para o lado do jogador) ──▶ CHASE_X
  ──(pisão | fogo | casco | estrela)──▶ DEFEATED ──(15 s)──▶ respawn fora da tela
Ovo: cai; ao pousar vira Trotador com stomp_hurts=True (espinhos), 72 px/s, vira-se para o jogador em 7/8 dos pousos
```

| Parâmetro | Original | Lume | Confiança |
| --- | --- | --- | --- |
| Velocidade-base parado / andando / correndo | 79 / 180 / 240 px/s − (|dx| & 60)/4 unid. | **190 / 440 / 590 px/s** − 0,8·|dx| (px/s, |dx| ≤ 112) | DOCUMENTADO → ESTIMADO |
| Teto de distância | 60 px | **112 px** | DOCUMENTADO → ESTIMADO |
| Intervalo / telegraph | 2,13 s / 0,27 s (SMB1); 1,07 s / 0,25 s (SMB3) | **2,1 s / 0,27 s** | DOCUMENTADO |
| Limite de "filhotes" | 4 (5 slots) | **3** por Arremessador aéreo | DOCUMENTADO → ESTIMADO |
| Não lançar se jogador no topo | y < 44 px | jogador acima do Arremessador | DOCUMENTADO → ESTIMADO |

### 6.5 Sentinela (blindado) — três variantes com `fireproof=True`

**(a) Esmagador** — originais: Thwomp (SMB3/SMW), Konk (Wonder).

```
IDLE (flutua no teto/origem)
  ──(|dx| < 120 px & on_screen)──▶ ALERT (muda a cara; sem movimento)       ──(|dx| ≥ 120)──▶ IDLE
  ──(−68 ≤ dx < 83 px, i.e. ≈ ±75 px & on_screen)──▶ DROP (acel. 880 px/s², teto 700 px/s; cara brava)
DROP ──(chão)──▶ RECOVER (tremor 0,4 s + som; espera 1,07 s)  ──▶ RISE (112 px/s até a origem) ──▶ IDLE
Contato lateral/inferior fere; em cima: fere (espinhos) ou `blocks_player` (Konk); só estrela/explosão derrotam
```

| Parâmetro | Original | Lume | Confiança |
| --- | --- | --- | --- |
| Zona de alerta / de queda | ±64 px / −36…+44 px (SMW); só queda em SMB3 | **±120 px / −68…+83 px** (assimetria preservada) | DOCUMENTADO → ESTIMADO |
| Aceleração / teto | 900 px/s² ; 232 (SMW) ou 420 (SMB3) px/s | **880 px/s² ; 700 px/s** (entre as duas, ×2,44 ≈ 566–1025) | DOCUMENTADO → ESTIMADO |
| Tremor / espera / subida | 0,4 s / 1,07 s / 60 px/s | **0,4 s / 1,07 s / 112 px/s** | DOCUMENTADO |
| Variante Konk | anda esq./dir.; azul sobe quando o jogador está acima; superfície segura | parâmetros `patrol_speed` (37 px/s), `inverted`, `blocks_player=True` | OBSERVADO → ESTIMADO |

**(b) Esqueleto** — original: Dry Bones (SMB3/SMW).

```
PATROL (72 px/s; turn_at_edges=True; bounce em outros inimigos)
  ──(pisão)──▶ STUNNED (pilha de ossos 4,4 s; sem colisão hostil; som de "desmontar")
  ──(últimos 0,8 s)──▶ RECOVER (remontagem com tremor) ──▶ PATROL (virado para o jogador)
  ──(estrela | explosão | casco pesado)──▶ DEFEATED        * fogo e projéteis comuns: imune
```

| Parâmetro | Original | Lume | Confiança |
| --- | --- | --- | --- |
| Tempo caído total | ≈5,25 s (SMB3) | **5,2 s** = 4,4 s de pilha + 0,8 s de remontagem | DOCUMENTADO |
| Telegraph | cabeça sobe/desce 4×6 q (SMB3); tremor de 64 q (SMW) | tremor de **0,8 s** | DOCUMENTADO |
| Pisável durante a remontagem | sim (NSMBW) | sim: reinicia o timer | OBSERVADO |
| Vira-se para o jogador ao levantar | sim | sim | DOCUMENTADO |

**(c) Acorrentado** — original: Chain Chomp (SMB3/NSMB).

```
IDLE (volta ao poste a 72 px/s; mordidas constantes) ──(timer 0,53–1,05 s)──▶ PREPARE_ATTACK (0,2 s recuo)
PREPARE_ATTACK ──▶ LEAP (se |dx| < 120 px: faixa = |dx|/30 → (vx,vy) ∈ {(600,−290),(360,−590),(480,−440),(240,−740)}; senão faixa aleatória; corrente de 90 px limita)
LEAP ──(0,67 s)──▶ RECOVER (0,53–1,05 s) ──▶ IDLE
IDLE ──(50 investidas | poste golpeado 3×)──▶ FREE (Trotador pulante: vx ±290 px/s, vy −440/−590 px/s, corrente piscando 2 s antes)
Pisão fere; fogo imune; só estrela/casco/explosão derrotam
```

| Parâmetro | Original | Lume | Confiança |
| --- | --- | --- | --- |
| Zona de mira | 64 px (4 faixas de 16 px) | **120 px** (4 faixas de 30 px) | DOCUMENTADO → ESTIMADO |
| Investidas (vx, vy) | (300,−120) (180,−240) (240,−180) (120,−300) px/s | ×2,44 / ×2,46 → tabela acima (teto 600 px/s por legibilidade) | DOCUMENTADO → ESTIMADO |
| Investida / espera | 0,67 s / 0,53–1,05 s | iguais | DOCUMENTADO |
| Corrente | ≈4 elos (SMB3) | **90 px** de raio | ESTIMADO |
| Soltar-se | 50 investidas (≈160 s) | **50** ou 3 golpes no poste; corrente pisca 2 s antes | DOCUMENTADO/OBSERVADO |

### 6.6 Sombra (furtivo) — original: Boo (SMB3/SMW)

```
IDLE (rosto coberto; para suavemente: −300 px/s²)
  ──(not player_looking_at_me por ≥ 0,33 s)──▶ CHASE (acel. 550 px/s² em X e Y até 130 px/s; zona morta vertical 8 px)
CHASE ──(player_looking_at_me)──▶ IDLE (SMB3: parada instantânea; Lume: desaceleração suave estilo SMW)
Troca de lado: giro de 0,5 s antes de inverter o sprite; |dx| < 19 px mantém o estado (evita pisca-pisca)
Sem pisão (atravessa); fogo imune; derrota só com estrela/explosão/"luz" (Wonder)
```

| Parâmetro | Original | Lume | Confiança |
| --- | --- | --- | --- |
| Atraso de reação | 20 q = 0,33 s (SMB3) ; decisão a cada 32 q (SMW) | **0,33 s** (`reaction_time` do `PerceptionProfile`) | DOCUMENTADO |
| Aceleração / máx. | 225 px/s², 60 px/s (SMB3) ; 28 px/s², 30 px/s (SMW) | **550 px/s², 130 px/s** (0,6 × caminhada, como SMB3) | DOCUMENTADO → ESTIMADO |
| Zona morta | 4 px vertical (SMB3); 10 px horizontal (SMW) | **8 px vertical, 19 px horizontal** | DOCUMENTADO → ESTIMADO |
| Giro | 31 q | **0,5 s** | DOCUMENTADO |
| `needs_line_of_sight` | não | **False**; `sight_range` ilimitado dentro da tela | DOCUMENTADO |

### 6.7 Faísca (explosivo) — original: Bob-omb (SMB3/SMW/NSMB)

```
PATROL (110 px/s; `face_player_on_spawn`; reorienta para o jogador a cada 1,07 s; pulinhos de passo)
  ──(pisão | bola de fogo)──▶ FUSE (4,25 s; chutável: SLIDE 365 px/s + ½ vx do jogador, vy −300 px/s; pisca nos últimos 1,07 s)
FUSE ──(timer | lava/fogo do cenário: imediato)──▶ EXPLODE (0,67 s; raio 56 px; fere jogador; derrota inimigos — inclusive Sentinelas; quebra `brick`)
EXPLODE ──▶ DEFEATED        * estrela/casco: explode na hora
```

| Parâmetro | Original | Lume | Confiança |
| --- | --- | --- | --- |
| Velocidade | 0,75 px/q = 45 px/s (SMW rápido) ; SMB3 1 px/q ao nascer | **110 px/s** | DOCUMENTADO → ESTIMADO |
| Pavio / piscar / explosão | 4,25 s / 1,07 s / 0,67 s (SMB3) ; 1,07 s (SMW) | **4,25 s / 1,07 s / 0,67 s** | DOCUMENTADO |
| Chute | 150 px/s + ½ vx ; vy −120 px/s | **365 px/s + ½ vx ; vy −300 px/s** | DOCUMENTADO → ESTIMADO |
| Raio da explosão | ≈1,5 tile (OBSERVADO) | **56 px** | ESTIMADO |
| Quebra tijolos | não (SMB3) / sim (NSMB) | **sim** (`brick`), não `question`/`ground` | OBSERVADO → decisão |

### 6.8 Saltador-do-lago (aquático) — originais: Cheep voadora (SMB1), Chargin' Cheep (SMB3), Rip Van Fish/Deep Cheep (SMW/NSMB)

Como a água do Lume é um perigo letal (README: "Água, lava e quedas custam uma vida"), a forma principal é a **saltadora**; a forma **nadadora/perseguidora** fica parametrizada para uma eventual fase com água navegável.

```
Saltador:  HIDDEN (abaixo da água/tela; spawn 0,27–1,6 s aleatório; máx. 3) ──▶ LEAP (vy −550 px/s, g 300 px/s², vx 45–130 px/s enviesado pela vx do jogador) ──(sai da tela)──▶ remove
           LEAP ──(pisão)──▶ DEFEATED (rebote −390)        fogo/estrela derrotam
Nadador:   SWIM (37–73 px/s reto ou senoide ±28 px, período 8 s; qualquer contato fere) ──(fogo | estrela)──▶ DEFEATED
Perseguidor: IDLE (dorme) ──(|dx| < 90 & |dy| < 90)──▶ ALERT (0,2 s) ──▶ CHASE (acel. 70 px/s², máx. 146 px/s em X e Y; 8,5 s ou jogador atrás) ──▶ RETREAT (desacelera) ──▶ IDLE ; player_star → foge
```

| Parâmetro | Original | Lume | Confiança |
| --- | --- | --- | --- |
| Salto | vy −300 px/s, g 183 px/s² → ápice ≈ tela (240 px), ≈3,3 s de voo | **vy −550, g 300** → ápice ≈ 500 px (tela de 540), voo 3,7 s | DOCUMENTADO → ESTIMADO |
| Spawn / máximo | 16–96 q / 3 (4 difícil) | **0,27–1,6 s / 3** | DOCUMENTADO |
| vx do saltador | 19–52 px/s, enviesado pela vx do jogador | **45–130 px/s**, +25 % se o jogador corre | DOCUMENTADO → ESTIMADO |
| Nadadora | 15 / 30 px/s; onda 7,5 px/s ±15 px | **37 / 73 px/s; ±28 px, 8 s** | DOCUMENTADO → ESTIMADO |
| Perseguidora: zona / acel. / máx. / duração | ±48 px (X,Y) / 28 px/s² / 60 px/s / 8,5 s | **±90 px / 70 px/s² / 146 px/s / 8,5 s** | DOCUMENTADO → ESTIMADO |
| Pisável debaixo d'água | não (SMB1/3/SMW), sim (Wonder) | **não** (coerente com água letal) | OFICIAL [M-SMB1] → decisão |

---
