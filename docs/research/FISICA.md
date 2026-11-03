# Física de salto e queda nos Mario 2D — engenharia reversa comportamental

Documento de pesquisa da Etapa 2 (migração do Lume para Python 3.12 + pygame-ce). Objetivo: entender **como** os jogos oficiais 2D de Mario tratam gravidade, salto, queda, teto, paredes, rampas, plataformas móveis, água, molas e tolerâncias de entrada, para calibrar um modelo **original e coerente** no Lume. Nenhum asset, ROM ou código proprietário foi extraído; os números abaixo vêm de manuais oficiais, entrevistas publicadas pela Nintendo e documentação comunitária (TASVideos, wikis, blogs técnicos) obtida por análise de terceiros.

Classificação usada em todo o texto:

| Rótulo | Significado |
| --- | --- |
| **OFICIAL** | Manual de instruções, site ou entrevista publicada pela Nintendo/desenvolvedores. Descreve comportamento, raramente números. |
| **DOCUMENTADO** | Artigo técnico, wiki ou página de recursos com fonte verificável. Inclui "documentação comunitária derivada de análise de terceiros" (valores obtidos por desmontagem/observação de RAM). Nunca é valor oficial. |
| **OBSERVADO** | Medição de gameplay quadro a quadro publicada por terceiros. |
| **ESTIMADO** | Inferência nossa (cálculo a partir de valores documentados, ou hipótese sem confirmação). |

Convenções: `q` = quadro a 60 Hz (NES/SNES NTSC rodam a ~60,1 Hz; usamos 60). `tile` = bloco de 16 px nos jogos clássicos. Conversões: `px/q × 60 = px/s`; `px/q² × 3600 = px/s²`. Nos jogos NES/SNES a velocidade X costuma ter 16 subunidades por pixel (`1 unidade = 1/16 px/q = 3,75 px/s`); a gravidade do SMB1 usa 1/256 px/q² por unidade (`1 unidade = 14,0625 px/s²`).

---

## 1. O motor atual do Lume (base de comparação)

Valores lidos em `src/core/physics.ts`, `src/core/game.ts` e `game/physics/movement.py` (`MovementProfile`, perfil `LEGACY_PROFILE`):

| Parâmetro | Valor atual | Observação |
| --- | --- | --- |
| Passo fixo | 1/120 s | acumulador em `Game.update` |
| Gravidade | 1550 px/s² | única, igual subindo e caindo |
| Impulso de salto | 590 px/s | sem bônus de corrida |
| Corte do salto (botão solto) | `vy = max(vy, -190)` | corte por velocidade, gravidade inalterada |
| Velocidade terminal | 850 px/s | só é atingida após ~233 px de queda (`v²/2g`) |
| Coyote time / jump buffer | 0,10 s / 0,12 s | 6 e 7 quadros a 60 Hz |
| Teto | `vy = 0` ao bater | sem empurrão para baixo |
| Plataforma móvel | jogador é deslocado por `dx, dy` enquanto `standingOn` | nenhuma herança de velocidade ao saltar |
| Jogador | 22×30 px (pequeno), 22×46 px (crescido) | Mario pequeno clássico tem 16 px: fator de escala corporal **1,875** |

Derivados (fórmulas na seção 11): altura máxima `h = 590²/(2·1550) = 112,3 px` (3,74 corpos pequenos; discretizada a 1/120 s: ≈ 109,8 px), tempo de subida 0,381 s, tempo de descida 0,381 s (arco **simétrico**), tempo total 0,76 s, alcance horizontal correndo `340 × 0,76 ≈ 259 px`, salto mínimo (toque de 1 passo) ≈ 16,5 px (15 % do máximo).

O ponto central desta pesquisa: **todos os Mario 2D clássicos usam arcos assimétricos** (gravidade menor subindo com botão segurado, maior caindo), **saltos que crescem com a velocidade horizontal** e **limites de queda baixos**. O Lume hoje tem arco simétrico, altura fixa e limite de queda praticamente inativo.

---

## 2. Super Mario Bros. (NES, 1985) — gravidade dupla por faixa de velocidade

### 2.1 O que a Nintendo diz (OFICIAL)

- Manual norte-americano (Super Mario Bros. / Duck Hunt, p. 6): "Mario (Luigi) jumps higher if you hold the button down longer"; "The height Mario jumps depends on how long you hold the A button down"; p. 9: "Pushing the B button makes Mario speed up, and when Mario is speeded up he can jump higher" (citado na compilação de perfis de salto da Super Mario Wiki). Ou seja, **altura variável por tempo de botão** e **bônus de corrida** são regras de design declaradas, não acidentes.
- Trampolim (jumping board), manual citado pela Super Mario Wiki: "Pushing the A Button when the jumping board is all the way up makes Mario jump superhigh".
- Shigeru Miyamoto (Iwata Asks, New Super Mario Bros. Wii, Vol. 1, p. 1): o salto nasceu em Donkey Kong como solução para o barril e para subir nos elevadores; "we decided to use the button to allow players to jump and when we made a prototype to try it out, it worked really well". Em Super Mario 3D Land (Iwata Asks, Vol. 2, p. 4), Miyamoto admite que "allowing a jumping Mario to change direction in the air was a no-no" para ele, mas que "it's better to fudge a little rather than stick to realistic 3D movement"; Koichi Hayashida acrescenta que no SMB original "Mario still faced the same way, but starting with Super Mario Bros. 3, you could change direction" (virar o sprite no ar). Princípio: a física serve à legibilidade do pisão, não ao realismo.

### 2.2 Tabela comunitária de forças verticais (DOCUMENTADO — derivada de análise de terceiros)

Fonte principal: página "Movement" da SMBpedia (espelho simplistic6502), confirmada por listagem anotada da desmontagem (6502disassembly.com, tabelas `JumpMForceData`, `FallMForceData`, `PlayerYSpdData`, `InitMForceData`) e pela compilação de constantes da issue "SMB movement and physics constants" (GitHub/Raditron). O índice é escolhido pela velocidade horizontal absoluta (`|vx|` em unidades de 1/16 px/q) no instante do salto:

| Índice | Condição `\|vx\|` (unid.) | `\|vx\|` em px/q | vy inicial (px/q) | Gravidade subindo (A segurado) | Gravidade caindo / A solto |
| --- | --- | --- | --- | --- | --- |
| 0 | < 9 | < 0,5625 | −4 (0xFC) | 0x20 = 0,1250 px/q² | 0x70 = 0,4375 px/q² |
| 1 | 9–15 | 0,56–0,94 | −4 | 0x20 = 0,1250 | 0x70 = 0,4375 |
| 2 | 16–24 | 1,0–1,5 (andando) | −4 | 0x1E = 0,1172 | 0x60 = 0,3750 |
| 3 | 25–27 | 1,56–1,69 | −5 (0xFB) | 0x28 = 0,1563 | 0x90 = 0,5625 |
| 4 | ≥ 28 | ≥ 1,75 (correndo) | −5 | 0x28 = 0,1563 | 0x90 = 0,5625 |
| 5 | nadando | — | −1,5 (0xFE + sub 0x80) | 0x0D = 0,0508 | 0x0A = 0,0391 |
| 6 | redemoinho | — | −1 (0xFF) | 0x04 = 0,0156 | 0x09 = 0,0352 |

Regra de troca (DOCUMENTADO, SMBpedia): a gravidade de queda é copiada para a gravidade ativa quando Mario está no ar **e** (`vy ≥ 0` **ou** A foi solto). Não há corte de velocidade: soltar o botão apenas triplica a gravidade. Limites horizontais: 24 unid. (1,5 px/q = 90 px/s) andando, 40 unid. (2,5 px/q = 150 px/s) correndo; na água 24 (duro) e 16 (chão).

Conversões a 60 Hz e consequências (ESTIMADO por cálculo, fórmulas na seção 11):

| Faixa | v0 (px/s) | g_sobe (px/s²) | g_desce (px/s²) | h máx | t_subida | t_descida (com limite 4 px/q) | Razão g_desce/g_sobe |
| --- | --- | --- | --- | --- | --- | --- | --- |
| parado/lento | 240 | 450 | 1575 | 64 px = 4,0 tiles | 32 q = 0,533 s | ≈ 20,6 q = 0,34 s | 3,50 |
| andando | 240 | 422 | 1350 | 68 px = 4,3 tiles | 34 q = 0,57 s | ≈ 22 q = 0,37 s | 3,20 |
| correndo | 300 | 563 | 2025 | 80 px = 5,0 tiles | 32 q = 0,533 s | ≈ 24 q = 0,39 s | 3,60 |

Observações: (a) Nintendo manteve o **tempo de subida em 32 quadros** nas faixas parado e correndo, variando v0 e g juntos — a altura muda, o ritmo não; (b) a razão ≈ 3,5 bate com a afirmação de Steve Swink (*Game Feel*, citado no resumo da palestra de Kyle Pittman) de que "at the apex of the jump, when velocity reaches 0, gravity is raised artificially by a factor of three"; (c) a issue do GitHub, simulando a integração discreta, obtém **≈ 66 px parado e ≈ 82 px correndo** (DOCUMENTADO), coerente com os 4 e 5 tiles conhecidos; (d) salto mínimo (A solto no 2.º quadro): ≈ 21 px = 1,3 tile, ou **33 % do máximo** (ESTIMADO).

### 2.3 Velocidade terminal, teto e medições independentes

- Limite de queda: a rotina de movimento vertical do jogador usa **4 px/q (240 px/s)** como máximo (listagem anotada da desmontagem: "set maximum vertical speed here", DOCUMENTADO). A SMBpedia explica que a checagem do limite é falha (compara inteiro e fração separadamente), então a velocidade observada **oscila entre 4 e ~5 px/q**; o RAM map do Data Crystal registra "Downward: 05 = fastest fall" e uma medição quadro a quadro no fórum TASVideos lista a queda "1, 1, 2, 2, 3, 3, 3, 4, 5, 4, 4, 4, 4, 4, 5, 4, 4, 4" com estimativa de 4,2 px/q (OBSERVADO). Como `v² = 2gh`, o limite de 4 px/q é atingido após apenas **≈ 18 px de queda** — por isso quedas longas no SMB1 têm velocidade quase constante.
- Tempo total de um salto parado: **53 quadros** (≈ 0,88 s) medidos do chão ao chão, com ~6 quadros "parado" no ápice (TASVideos, OBSERVADO). Nossa simulação com a tabela (32 q sobindo + ~21 q caindo) dá 53 q: a tabela comunitária e a medição concordam.
- Teto (DOCUMENTADO, SMBpedia): bater em bloco duro (ou na base de uma plataforma móvel) define `vy = +1 px/q` (60 px/s para baixo); bater em bloco "mole" (tijolo) define `vy = 0` se o bloco sobrevive e `vy = −2 px/q` se ele quebra (Mario continua subindo um pouco). Ejeção lateral de paredes empurra Mario para o lado oposto ao comando (TASVideos).
- Gravidades especiais (DOCUMENTADO): 0x28 (562 px/s²) em transições de tela e 0x18 (338 px/s²) acima do limite superior em áreas aquáticas; a TAS de "mínimo de pressionamentos de A" explora essa gravidade baixa para cruzar vãos sem saltar.

### 2.4 Natação, mola, plataformas, paredes

- Natação (índice 5 da tabela): cada toque em A dá `vy = −1,5 px/q` (−90 px/s); gravidade na água 0,05/0,04 px/q² (183/141 px/s²); velocidade X limitada a 1,5 px/q (duro) e 1,0 px/q andando no fundo. Acima da superfície (`Y < 20`) a velocidade vertical é zerada: **em SMB1 não se sai da água nadando** — o manual do SMB3 é o primeiro a prometer "If you press the A Button at the same time, Mario can jump up out of water" (OFICIAL).
- Mola vermelha (DOCUMENTADO, SMBpedia): `vy = −7 px/q` sem A, `−12 px/q` com A segurado; a gravidade de subida é fixada em 0x70 (a de queda). Alturas: `49/(2·0,4375) = 56 px` (3,5 tiles) e `144/(2·0,4375) ≈ 165 px` (10,3 tiles). A diferença vem da **velocidade**, não da gravidade.
- Elevadores (Super Mario Wiki, DOCUMENTADO): verticais, horizontais, frágeis (descem ao pisar), balança em polia (caem se demorar). Nenhuma fonte documenta herança de velocidade horizontal ao saltar de um elevador no SMB1 — tratamos como **sem herança** (ESTIMADO).
- Paredes (DOCUMENTADO, smb1explained/TASVideos): não existe wall jump intencional; o "walljump" é um glitch que exige `|vx| ≥ 17` unidades e encaixe de 2 px no bloco superior num limite de 16 px.
- Entrada (DOCUMENTADO): o salto exige um **pressionamento novo** com Mario em estado "no chão"; o RAM map distingue os estados 0 (chão), 1 (no ar por salto) e 2 (no ar por ter andado para fora da borda). A smb1explained registra que o salto pode ser "bufferizado" apenas durante a animação de power-up, porque ela zera o estado para 0. Inferência: **SMB1 não tem coyote time nem jump buffer gerais** (ESTIMADO).

---

## 3. Super Mario Bros. 3 (NES, 1988/1990)

### 3.1 OFICIAL (manual norte-americano, 1990)

- "The longer you press the A Button, the higher Mario will jump."
- "Pressing the B Button while walking will make Mario accelerate. When Mario is moving fast, he can jump higher and farther."
- "When the ground slopes, Mario can slide down it (except for Frog Mario.)" — rampas e deslize nascem aqui como regra de controle.
- "In the water, Mario can swim by repeatedly pressing the A Button"; "If you press the A Button at the same time, Mario can jump up out of water."
- Super Jump: "When Mario jumps on an enemy, he can jump very high by pressing the A Button." Jump Block (bloco de nota): "If your timing is right, you can use these to jump very high."

### 3.2 DOCUMENTADO (Data Crystal — notas da desmontagem; TASVideos)

- Velocidades (unidades de 1/16 px/q): andar/nadar 24 (1,5 px/q = 90 px/s), correr sem P 40 (2,5 = 150 px/s), corrida P 56 (3,5 = 210 px/s), deslizar 63 (3,94 = 236 px/s), ejeção de parede 16, voo 23. Aceleração ≈ 1 unidade/q (0,0625 px/q² = 225 px/s²).
- Potência do salto: a velocidade padrão (`$A647`, valor não transcrito) recebe um ajuste da tabela `00,02,04,08` indexada por `|vx|/16` — "a higher horizontal speed means a more powerful jump". O bônus máximo é 8 unidades = 0,5 px/q (30 px/s).
- Gravidade: enquanto A está segurado **e** Mario sobe mais rápido que o limiar `$E0` (−32 unid. = −2 px/q = −120 px/s), aplica-se a "jump gravity" `$01`; caso contrário a "default falling gravity" `$05`. Se as unidades forem 1/16 px/q² (ESTIMADO), isso é 225 vs 1125 px/s² (razão 5). Diferente do SMB1, o abandono do salto acontece **tanto ao soltar quanto ao desacelerar abaixo de 2 px/q**, encurtando a fase "flutuante" perto do ápice.
- Limite de queda: `#$40` (64 unid. = 4 px/q = 240 px/s), com gravidade somada depois do clamp ("effective value is 45" → 4,31 px/q). Mesmo teto prático do SMB1.
- Rampas: descendo, Mario ganha +3 subpixels/q sem que a variável de velocidade mude (TASVideos). Deslize (Super Mario Wiki): "sits and slides down the hill while gaining speed (they go even faster on icy slopes)", "invincible to most enemies while sliding", "vulnerable again upon the character stopping"; dá para "do a midair jump by sliding into midair and jumping". Frog e Hammer Mario não deslizam.
- Walljump glitch: ≥ 33 unid. contra a parede e pés num limite de 16 px; "corner boost" e "ceiling boost" de ~1 px.
- O artigo "Mechanics Automatically Recognized via Interactive Observation: Jumping" (arXiv 1707.03865) aprende os parâmetros de salto por observação e conclui que SMB1 e SMB3 são "very similar" em perfil de salto, com "a period of control, a reset after button release, and a subsequent increased gravity for falling" (DOCUMENTADO).

---

## 4. Super Mario World (SNES, 1990/1991)

### 4.1 OFICIAL (manual norte-americano, 1991)

- "Mario will jump high if you hold the B Button down." (p. 11)
- "Mario will also jump a long way if you hold the B Button down as he stomps on an enemy." (p. 11) — quique alto no inimigo é um salto condicionado ao botão.
- B = salto normal; A = Spin Jump (Super Mario Wiki, confirmado pelo RAM map `$140D`).

### 4.2 DOCUMENTADO (RAM map do SMW Central, blog SMW TAS, TASVideos)

Unidade: 1/16 px/q (TASVideos: "subpixels are measured in sixteenths of a pixel").

| Grandeza | Valor (unid.) | px/q | px/s |
| --- | --- | --- | --- |
| Andar pleno (`$7B` = 0x14) | 20 | 1,25 | 75 |
| Correr (oscila 36/35) | 36 | 2,25 | 135 |
| Corrida P / sprint (48/47/49) | 48 | 3,0 | 180 |
| Nadar (15–17) | 16 | 1,0 | 60 |
| Salto normal parado (`$7D` = 0xB3) | −77 | −4,81 | −289 |
| Salto normal, `\|vx\|` 56–63 | −94 | −5,88 | −353 |
| Salto normal "fully running" (0xA4) | −92 | −5,75 | −345 |
| Spin jump parado | −71 | −4,44 | −266 |
| Spin jump, `\|vx\|` 56–63 | −87 | −5,44 | −326 |
| Quique em inimigo com botão / sem botão | −88 / −48 | −5,5 / −3,0 | −330 / −180 |
| Trampolim sem botão / com botão | −80 / −128 | −5,0 / −8,0 | −300 / −480 |
| Limite de queda (0x46) | 70 | 4,375 | 262 |

Tabela completa do blog SMW TAS por faixa de `|vx|` (B = normal, A = spin): 0–7: −77/−71; 8–15: −79/−73; 16–23: −82/−75; 24–31: −84/−77; 32–39: −87/−79; 40–47: −89/−82; 48–55: −92/−84; 56–63: −94/−87. Oito faixas de 8 unidades: a velocidade inicial cresce **22 %** do parado ao sprint. O spin jump é ≈ 8 % mais lento no impulso (≈ 15 % mais baixo), coerente com a Super Mario Wiki ("offers less height than a standard jump"), e permite quicar em Spinies e bolas de lava sem dano, além de quebrar blocos giratórios por cima (Super Mario, DOCUMENTADO).

Gravidade: **não encontramos documentação** dos valores por quadro. Pela altura conhecida de ~4 tiles parado (Reverse Design: "four blocks above the position of his feet"; com um bloco de embalo, cinco; com onze blocos de embalo, "the top of the sixth block"), `g_sobe ≈ v0²/(2h) = 4,81²/128 ≈ 0,18 px/q² ≈ 3/16 px/q² ≈ 650–675 px/s²` (ESTIMADO). A razão de queda não foi confirmada; a Reverse Design observa "only a tiny pause (about 3–4 frames) at the apex" e "rise and fall without real acceleration or deceleration physics" (OBSERVADO), sugerindo arco menos assimétrico que o SMB1.

Outros comportamentos (DOCUMENTADO/OBSERVADO):

- Aceleração a partir do repouso: 0, 1, 3, 4, 6, 7, 9… unidades por quadro; "takeoff meter" de 80 quadros após salto em sprint (TASVideos).
- Rampas: inclinações de 45° funcionam como plataformas de mão única resolvidas pela velocidade vertical (TASVideos); deslize ao agachar; é possível "slide up a hill by crouching while running up one"; rampas extra-íngremes forçam a descida; Koopas azuis sem casco deslizam como Mario (Super Mario Wiki).
- Teto: TASers cancelam o momento vertical pressionando A quando a cabeça toca o teto ("basically kills your vertical momentum"), com janela de 2–4 quadros (OBSERVADO). O valor exato de `vy` após a batida não foi documentado.
- Água: velocidade de nado ~1 px/q; "if you hold up on the d-pad, you will rise significantly faster"; segurando item nada mais rápido (smwspeedruns); flag `$13FA` permite saltar para fora da água quando logo abaixo da superfície (RAM map).
- Plataformas móveis: o "boost" horizontal ao tocar uma plataforma depende de quantos pixels dela cobrem Mario no quadro de contato (TASVideos, glitch). Herança de velocidade ao saltar: não documentada (ESTIMADO: não há).
- Distâncias (Reverse Design, OBSERVADO): sem embalo Mario cruza 5 blocos; antes da corrida plena, 8; em corrida plena, 12.

---

## 5. New Super Mario Bros. (DS, 2006), NSMB Wii (2009) e NSMB U (2012)

### 5.1 OFICIAL

- Manual NSMB (DS) e NSMB Wii (p. 12): "Press [2] to jump. Press and release for short jumps, and press and hold for longer jumps." NSMB 2 (manual eletrônico, p. 7): "The height of your jump depends on how long you press the button."
- Manual NSMB Wii (pp. 13–14, via cópia do manual): salto duplo/triplo — "Jump while dashing, then press again just as Mario touches down to perform a double jump or even higher triple jump"; wall jump — "While sliding down a wall, press in the direction of the wall, then press [2] to kick off the wall and jump upward"; ground pound — "Press down on [control] while in the air to perform a ground pound"; natação — "press and hold left or right on [control], then press [2] to swim".
- Iwata Asks (NSMB Wii): controles "the same controls as the Famicom days" (Wii Remote na horizontal, direcional + 1 e 2); Miyamoto propôs intuitivamente o giro por chacoalhar o controle (Iwata Asks, Mario 25th); "The player will be Luigi, but his jumping ability is the same as Mario's" (Super Guide); filosofia de dificuldade: "nervous excitement in moderation", preferir repetir a parte fácil a multiplicar checkpoints.
- Iwata Asks (NSMB U): botões se adequam melhor às ações de Mario que o toque testado no DS.

### 5.2 DOCUMENTADO (TASVideos DS; guias de speedrun NSMBW)

NSMB DS (TASVideos, posição e velocidade em pixels, ponto fixo 20.12, blocos de 16 px):

- Velocidade de corrida e de salto triplo: **3,0 px/q (180 px/s)**; casco: 2,75 px/q.
- Wall jump: ao iniciar, um timer é posto em **16 quadros (0,27 s)**; novo wall jump só quando zera. Timers de "ação de parede" (um por lado) também valem 16 quadros, armados ao pressionar na direção da parede com as condições: nenhum chão a menos de 16 px abaixo; estar ao menos 19 px abaixo do topo da parede (11 px agachado) e menos de 4 px abaixo da base; estar virado para a parede, movendo-se para ela e não agachado. Métodos: (1) A com o timer de ação ≠ 0; (2) A segurando contra a parede em colisão, sem descer naquele quadro. Se slide e salto ativam no mesmo quadro, o slide vence; o **slide zera a velocidade vertical** e atrasa o salto em 1 quadro.

NSMB Wii (NSMBW Speedrun Guides):

- Velocidade: "Mario's maximum regular running speed is 3 pixels/frame, or 3 speed"; estrela 4,0; saltar não altera a velocidade; correr e saltar dá salto mais alto que parado.
- Alturas: salto simples ou duplo pleno = **5 blocos**; triplo = **6 blocos**. O duplo exige novo salto **dentro de 8 quadros (≈ 0,13 s)** após o pouso, a velocidade ≥ 3; o triplo repete a regra. Saltar na borda exata da plataforma **reinicia a progressão** (vira salto simples).
- "Hovering": segurar o botão de salto enquanto cai **reduz a aceleração para baixo** — no NSMBW a gravidade continua dependendo do botão mesmo na descida. Giro no ar (Midair Spin) "ekes out more air time" (Super Mario Wiki).
- Wallkick: fixa a velocidade em ≈ **2,25 px/q** imediatamente e é "the fastest way to go from zero to max speed if you are near enough to a wall".
- Plataformas móveis: colinas rolantes, esteiras, montanha-russa de osso e blocos de gelo grandes **carregam sua velocidade para o salto**; plataformas em trilho, blocos giratórios e plataformas flutuantes **não** (saltar devolve 3,0). Ao pousar, a velocidade vira a do chão móvel.
- Rampas: deslizar é mais rápido em rampas abaixo de 45°; em 45° correr e deslizar no fim; subir rampas é lento.
- Água: "Holding 1 accelerates Mario to 3 speed"; para o salto mais alto para fora, subir até o chapéu romper a superfície e segurar 2; Mario pequeno sai 0,5 bloco mais alto.

### 5.3 Spin jump e triplo (DOCUMENTADO, Super Mario Wiki)

- NSMBW: giro por chacoalhar; "functions most similarly to the Spin Jump in Super Mario World, but still no longer protects from stomping otherwise hazardous enemies"; NSMBU mantém e permite spin durante wall jump. O guia Prima descreve "a little extra distance and height out of a regular jump" — conflita com o SMW, onde o spin é mais baixo (ESTIMADO: no NSMBW o giro no ar prolonga o tempo de voo; o impulso inicial não foi medido).
- Triplo: "has to be running at full speed in order to triple-jump" (série NSMB).

Gravidade, velocidade inicial e limite de queda dos NSMB: **não documentados** publicamente nas fontes consultadas (ESTIMADO).

---

## 6. Super Mario Bros. Wonder (Switch, 2023)

- Ask the Developer Vol. 11 (OFICIAL): Shiro Mouri — "some badges alter actions, like jumping higher after crouching"; "We ended up with over 20 different badges. These were the top picks from more than 50 prototypes"; o sistema "kept characters and abilities separate" (antes "Luigi could jump higher, and Peach could float"). Masanobu Sato (arte): manter a confiança de que "we can safely jump on pipes" foi "crucial". Takashi Tezuka: "just one mistimed action can lead to a bigger mistake, since you have fewer options in terms of movement".
- Descrições em jogo dos emblemas de movimento (texto oficial reproduzido na Super Mario Wiki, DOCUMENTADO): Parachute Cap ("open your hat and float slowly downward"), Wall-Climb Jump ("Jump against a wall and then press B Button to jump straight up once"), Dolphin Kick ("brief burst of speed" na água), Floating High Jump ("Jump higher than usual and momentarily float"), Crouching High Jump, Boosting Spin Jump ("gain a little extra altitude" no ar), Timed High Jump ("Time consecutive jumps just right to jump higher than usual"), Spring Feet, Safety Bounce ("Bounce back out of pits… just one time per fall"), Fast Dash, Jet Run, Grappling Vine.
- Spin jump "functioning as in New Super Mario Bros. U"; blocos de nota substituídos pelo Marimba Block, que "bounces the player higher when they jump" (Super Mario Wiki).
- Lição para o Lume: a Nintendo trata variações de física (gravidade de queda, impulso extra, salto em parede, flutuação) como **módulos ligáveis**, cada um com um parâmetro claro. Nenhum número de Wonder foi publicado (ESTIMADO).

---

## 7. Tolerâncias modernas: coyote time e jump buffering existem nos Mario?

| Jogo | Coyote time | Jump buffer | Evidência |
| --- | --- | --- | --- |
| SMB1 | não (ESTIMADO) | não, exceto efeito colateral do power-up (DOCUMENTADO) | estados 0/1/2 no RAM map; smb1explained |
| SMB3, SMW | não encontrado (ESTIMADO) | não encontrado | nenhuma fonte técnica menciona janela após a borda; TAS usam entradas quadro-perfeitas |
| NSMB DS/Wii/U | não documentado; há janela de **8 q após o pouso** para encadear duplo/triplo (DOCUMENTADO) e janela de **16 q** para wall jump após pressionar contra a parede (DOCUMENTADO) | não documentado | NSMBW guides; TASVideos DS |
| Wonder | não documentado | não documentado | — |
| Super Mario Odyssey (3D, fora do escopo, único Mario com coyote time documentado) | **6 quadros**, +5 agachado (até 10); também nas seções 2D | — | smo.wiki, Supper Mario Broth (DOCUMENTADO) |

Referências de projeto fora da Nintendo (DOCUMENTADO): Celeste usa 5 quadros de coyote; guias de game feel recomendam 5–7 quadros ou 100–120 ms de buffer. Conclusão: os clássicos compensavam a ausência de tolerâncias com **arcos lentos no ápice (6 q parados no SMB1, 3–4 q no SMW)** e saltos longos; a Nintendo só documenta tolerância explícita em Odyssey. Para o Lume, manter coyote e buffer é uma escolha moderna legítima, mas as janelas atuais (6 e 7 q) estão no teto do usual.

---

## 8. Molas e blocos de nota — síntese

| Objeto | Jogo | Comportamento | Números | Confiança |
| --- | --- | --- | --- | --- |
| Jumping board | SMB1 | A no ponto de compressão máxima = "superhigh" | −7 px/q (−420 px/s) sem A → 56 px; −12 px/q (−720 px/s) com A → ≈ 165 px; gravidade 0x70 nas duas fases | OFICIAL (regra) / DOCUMENTADO (valores) |
| Trampolim | SMW | pode ser carregado; pode virar no ar | −80 (−300 px/s) sem botão; −128 (−480 px/s) com botão | DOCUMENTADO |
| Jump/Note Block | SMB3 | "If your timing is right, you can use these to jump very high" | sem números | OFICIAL |
| Note Block | SMW/NSMBW/NSMBU | quique automático; mais alto se o salto é pressionado pouco antes do pouso; NSMBU toca nota fixa | sem números | DOCUMENTADO |
| Marimba Block | Wonder | "bounces the player higher when they jump" | sem números | DOCUMENTADO |
| Quique em inimigo | SMW | com botão −88 (−330 px/s), sem botão −48 (−180 px/s); SMB3 "Super Jump" com A | — | DOCUMENTADO / OFICIAL |

Padrão comum: a **velocidade de lançamento** depende do botão no instante do contato (não da gravidade), e segurar o botão depois continua valendo como em qualquer salto.

---

## 9. Tabela consolidada de parâmetros

Valores convertidos a 60 Hz e tiles de 16 px. A coluna "Implementação" indica o que o Lume faz hoje e, quando aplicável, a escala corporal ×1,875 (Mario 16 px → Lume 30 px).

| Parâmetro | Referência | Valor estimado | Fonte | Confiança | Implementação |
| --- | --- | --- | --- | --- | --- |
| Impulso de salto parado | SMB1 | 240 px/s (4 px/q) | SMBpedia / desmontagem | DOCUMENTADO | Lume 590 px/s (≈ 562 se SMB1 ×1,875 correndo) |
| Impulso de salto correndo | SMB1 | 300 px/s (5 px/q) | SMBpedia | DOCUMENTADO | Lume não tem bônus |
| Impulso parado / sprint | SMW | 289 / 345–353 px/s | RAM map + blog TAS | DOCUMENTADO | idem |
| Bônus de corrida no impulso | SMB3 | +0,5 px/q (30 px/s) no máximo | Data Crystal | DOCUMENTADO | idem |
| Gravidade subindo (botão) | SMB1 | 450 / 422 / 563 px/s² | SMBpedia | DOCUMENTADO | Lume 1550 (única) |
| Gravidade caindo / solto | SMB1 | 1575 / 1350 / 2025 px/s² | SMBpedia | DOCUMENTADO | Lume 1550 |
| Razão g_desce/g_sobe | SMB1 | 3,2–3,6 | cálculo | ESTIMADO | Lume 1,0 |
| Gravidade subindo / caindo | SMB3 | 225 / 1125 px/s² se unid. 1/16 | Data Crystal | ESTIMADO (unidade não confirmada) | — |
| Limiar de abandono do salto | SMB3 | vy > −120 px/s → gravidade normal | Data Crystal | DOCUMENTADO | Lume corta para −190 px/s ao soltar |
| Gravidade subindo | SMW | ≈ 650–675 px/s² | derivado de h = 4 tiles | ESTIMADO | — |
| Altura salto parado | SMB1 / SMW / NSMBW | 64–66 px (4 tiles) / ~64 px / 80 px (5 blocos) | SMBpedia, Reverse Design, NSMBW guides | DOCUMENTADO | Lume 112 px = 3,74 corpos |
| Altura salto correndo | SMB1 / SMW / NSMBW triplo | 80–82 px / ≈ 88–96 px / 96 px | idem | DOCUMENTADO | — |
| Tempo de subida | SMB1 | 32 q = 0,533 s | cálculo sobre tabela | ESTIMADO | Lume 0,381 s |
| Tempo total salto parado | SMB1 | 53 q = 0,88 s | TASVideos | OBSERVADO | Lume 0,76 s |
| Pausa no ápice | SMB1 / SMW | ~6 q / 3–4 q | TASVideos / Reverse Design | OBSERVADO | — |
| Salto mínimo / máximo | SMB1 | ≈ 21 px / 64 px (33 %) | cálculo | ESTIMADO | Lume 16,5 / 112 px (15 %) |
| Velocidade terminal | SMB1 / SMB3 / SMW | 240 (oscila até ~300) / 240–259 / 262 px/s | desmontagem, Data Crystal, RAM map | DOCUMENTADO | Lume 850 px/s (≈ 450–490 escalado) |
| Distância até o limite de queda | SMB1 | ≈ 18 px | cálculo | ESTIMADO | Lume ≈ 233 px |
| Teto: bloco duro | SMB1 | vy = +60 px/s | SMBpedia | DOCUMENTADO | Lume vy = 0 |
| Teto: tijolo quebrado | SMB1 | vy = −120 px/s (continua subindo) | SMBpedia | DOCUMENTADO | — |
| Velocidade andar / correr | SMB1 | 90 / 150 px/s | SMBpedia | DOCUMENTADO | Lume 220 / 340 (≈ 169 / 281 escalado) |
| Velocidade andar / correr / P | SMB3 | 90 / 150 / 210 px/s | TASVideos | DOCUMENTADO | — |
| Velocidade andar / correr / sprint | SMW | 75 / 135 / 180 px/s | RAM map, TASVideos | DOCUMENTADO | — |
| Velocidade de corrida | NSMB DS/Wii | 180 px/s (3 px/q) | TASVideos, guias | DOCUMENTADO | — |
| Wall jump: lockout | NSMB DS | 16 q = 0,27 s | TASVideos | DOCUMENTADO | Lume não tem |
| Wall jump: janela após pressionar contra a parede | NSMB DS | 16 q | TASVideos | DOCUMENTADO | — |
| Wall slide: condições | NSMB DS | sem chão a < 16 px abaixo; ≥ 19 px abaixo do topo (11 agachado); < 4 px abaixo da base; virado e movendo para a parede | TASVideos | DOCUMENTADO | — |
| Wall slide: vy ao iniciar | NSMB DS | 0 | TASVideos | DOCUMENTADO | — |
| Wallkick: velocidade | NSMBW | 135 px/s (2,25 px/q) | guias | DOCUMENTADO | — |
| Duplo/triplo: janela | NSMBW | 8 q após pouso, vx ≥ 3 px/q | guias | DOCUMENTADO | — |
| Gravidade reduzida ao segurar na descida | NSMBW | existe ("hovering") | guias | DOCUMENTADO | — |
| Rampa: ganho em descida | SMB3 | +3 subpx/q (+11 px/s) | TASVideos | DOCUMENTADO | Lume não tem rampas |
| Rampa: deslize mais rápido | NSMBW | abaixo de 45° | guias | DOCUMENTADO | — |
| Herança de plataforma móvel | NSMBW | só chão "que carrega" (esteiras, colinas); trilhos não | guias | DOCUMENTADO | Lume: sem herança |
| Natação: impulso por toque | SMB1 | −90 px/s | SMBpedia | DOCUMENTADO | Lume: água mata |
| Natação: gravidade | SMB1 | 183 (subindo) / 141 (caindo) px/s² | SMBpedia | DOCUMENTADO | — |
| Natação: limite X | SMB1 / SMW | 90 / ~60 px/s | SMBpedia / TASVideos | DOCUMENTADO | — |
| Sair da água saltando | SMB3+ | sim | manual SMB3; RAM map SMW | OFICIAL / DOCUMENTADO | — |
| Mola | SMB1 | −420 / −720 px/s (sem/com A) | SMBpedia | DOCUMENTADO | Lume não tem |
| Trampolim | SMW | −300 / −480 px/s | blog TAS | DOCUMENTADO | — |
| Coyote time | 2D Mario | não encontrado; Odyssey 6 q | smo.wiki | ESTIMADO | Lume 6 q |
| Jump buffer | 2D Mario | não encontrado | — | ESTIMADO | Lume 7 q |
| Virar o sprite no ar | SMB3+ | sim (SMB1 não) | Iwata Asks 3D Land | OFICIAL | Lume vira |

---

## 10. Modelo de salto proposto para o Lume

### 10.1 Fórmulas

Para gravidade constante por fase (sem limite de queda):

- altura máxima: `h = v0² / (2·g_sobe)`
- tempo de subida: `t_sobe = v0 / g_sobe`
- tempo de descida: `t_desce = sqrt(2h / g_desce)`; velocidade de pouso `v_pouso = g_desce · t_desce`
- alcance horizontal: `d = vx · (t_sobe + t_desce)`
- com limite `v_t` atingido antes do chão (`v_t² < 2·g_desce·h`): `t_desce = v_t/g_desce + (h − v_t²/(2·g_desce)) / v_t`
- salto mínimo (botão solto no instante `t_r`, corte para `v_c`): `h_min = y(t_r) + min(v(t_r), v_c)² / (2·g_desce)`
- projeto inverso (Pittman, GDC 2016 "Building a Better Jump"; Winter 2017): escolhendo altura `H` e tempo até o ápice `T`, `v0 = 2H/T` e `g_sobe = 2H/T²`; escolhendo o tempo de descida `T'`, `g_desce = 2H/T'²`.
- integração discreta (Euler semi-implícito, velocidade antes da posição, como o motor atual): a altura efetiva é `h − v0·dt/2 + O(dt²)`; a 1/120 s com v0 = 590 isso vale ≈ 2,5 px. Testes dourados devem usar a fórmula discreta.

### 10.2 Comparação numérica

| Preset | v0 | g_sobe | g_desce | v_t | corte | h | t_sobe | t_desce | total | alcance @340 | v_pouso | h_min (razão) | g_desce/g_sobe |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Atual (LEGACY) | 590 | 1550 | 1550 | 850 | −190 | 112,3 | 0,381 | 0,381 | 0,761 | 259 | 590 | 16,5 (15 %) | 1,00 |
| A — SMB1 ×1,875 | 450 | 844 | 2953 | 450 | sem corte | 120 | 0,533 | 0,343 | 0,876 | 298 | 450 | 37 (31 %) | 3,50 |
| **B — assimétrico moderado (recomendado)** | **487** | **1059** | **2489** | **760** | **−330** | **112,0** | **0,460** | **0,300** | **0,760** | **258** | **747** | **26 (23 %)** | **2,35** |
| C — leve | 520 | 1210 | 2000 | 800 | −250 | 111,7 | 0,430 | 0,334 | 0,764 | 260 | 669 | 20 (18 %) | 1,65 |
| B + bônus de corrida (opcional) | 516 (se `\|vx\|` ≥ 300) | 1122 | 2489 | 760 | −330 | 118,7 | 0,460 | 0,309 | 0,769 | 261 | 760 | 26 (22 %) | 2,22 |

Leitura: o preset A reproduz o ritmo do SMB1, mas alonga o voo em 15 % (0,88 s) e o alcance para 298 px — invalidaria o ajuste de vãos das 15 fases (o README exige preservar aterrissagens). O preset **B preserva altura (112 px) e tempo total (0,76 s)**, portanto preserva o alcance horizontal e a geometria das fases, mas redistribui o tempo: subida 0,46 s com "pausa" perceptível no ápice e descida 0,30 s mais firme, como nos clássicos; o salto mínimo sobe de 15 % para 23 % do máximo (SMB1: 33 %), o que reduz saltos "cortados" acidentais sem tirar o controle fino. O bônus de corrida mantém `t_sobe` (como a Nintendo fez no SMB1) e dá +6 % de altura; fica **desligado por padrão** até os testes de rota confirmarem que nenhum teto obrigatório é alcançado indevidamente.

### 10.3 Perfil `MovementProfile` proposto (unidades px/s, px/s², s)

Campos novos ou alterados em `game/physics/movement.py`; o perfil `LEGACY_PROFILE` permanece intocado para os testes diferenciais, e um `CALIBRATED_PROFILE` recebe os valores abaixo.

| Campo | LEGACY | CALIBRATED (proposta) | Origem |
| --- | --- | --- | --- |
| `jump_speed` | 590 | 487 | h = 112 px mantida |
| `run_jump_speed` (novo; usado se `\|vx\|` ≥ `run_jump_threshold`) | 590 | 516 (opção; 487 = desligado) | SMB1/SMB3/SMW escalam com vx |
| `run_jump_threshold` (novo) | — | 300 | SMB1 troca de faixa a 1,56–1,75 px/q ≈ 88 % da corrida |
| `gravity_rise` (novo; botão segurado e vy < 0) | 1550 | 1059 (1122 com bônus) | razão 2,35 inspirada em SMB1 (3,2–3,6) e Swink ("×3") |
| `gravity_fall` (novo; vy ≥ 0 ou botão solto) | 1550 | 2489 | idem |
| `jump_cut_speed` | 190 | 330 | soltar = `vy = max(vy, −330)` **e** troca para `gravity_fall` |
| `terminal_velocity` | 850 | 760 | v_pouso do salto máximo; SMB1 escalado seria 450 |
| `coyote_time` | 0,10 | 0,083 (5 q) | sem precedente nos Mario; usual em 2D moderno |
| `jump_buffer` | 0,12 | 0,10 (6 q) | NSMBW usa janela de 8 q para encadear saltos |
| `ceiling_bump_speed` (novo) | 0 | +100 | SMB1: +60 px/s em bloco duro (×1,875 ≈ 112) |
| `apex_hang_threshold` (novo, opcional) | — | 40 | abaixo de `\|vy\|` < 40 aplicar `gravity_rise` por até 3 q, imitando a pausa no ápice (OBSERVADO SMB1/SMW) |
| `world_gravity` (novo, entidades) | 1550 | 1550 | inimigos/itens continuam usando a constante atual (`abilities.py`, `enemies/legacy.py`) |

Pseudocódigo do passo vertical (substitui as duas linhas de salto/gravidade em `Game.step`):

```python
rising = p.vy < 0
holding = input_state.jump
if not holding and p.vy < -prof.jump_cut_speed:
    p.vy = -prof.jump_cut_speed
g = prof.gravity_rise if (rising and holding) else prof.gravity_fall
p.vy = min(prof.terminal_velocity, p.vy + g * dt)
# teto (em move_body): if hit_head: p.vy = prof.ceiling_bump_speed
```

### 10.4 Módulos opcionais (ligados por perfil, desligados no LEGACY)

| Módulo | Parâmetros propostos | Base |
| --- | --- | --- |
| Mola | `spring_speed = 760` px/s; com `gravity_rise` (segurando) h ≈ 273 px (2,4 saltos); soltando, `gravity_fall` dá ≈ 116 px (≈ 1 salto). Alternativa fiel ao SMB1: velocidade 500/760 conforme o botão no contato (razão de alturas 2,9) | SMB1 −7/−12 px/q; SMW −80/−128 |
| Bloco de nota | quique automático `note_speed = 420` (h 35–83 px conforme botão); salto pressionado até 6 q antes do contato → `jump_speed × 1,14 ≈ 555` (h ≈ 145 px, 1,3 salto) | SMB3 "jump very high"; Super Mario Wiki |
| Wall slide / wall jump ("Fronteira" opcional) | slide se vy > 0, pressionando contra a parede, sem chão a < 30 px abaixo: `wall_slide_speed = 200` px/s; `wall_jump_vx = 260`, `wall_jump_vy = −487`; `wall_jump_lockout = 16/60`; `wall_action_window = 16/60`; o slide zera vy ao começar | NSMB DS timers e condições (×1,875 nas distâncias) |
| Giro no ar | sem impulso extra (como o spin do SMW é mais baixo, não vale copiar); opção: multiplicar `gravity_fall` por 0,6 durante 0,25 s | NSMBW Midair Spin; Wonder Boosting Spin Jump |
| Natação (se a água deixar de ser perigo) | `swim_stroke = −170` px/s por toque; `swim_gravity_rise = 343`, `swim_gravity_fall = 264` px/s²; `swim_max_x = 170`; `swim_sink_max = 150` (ESTIMADO); saltar para fora com `jump_speed` quando a cabeça rompe a superfície | SMB1 índice 5 ×1,875; SMB3/SMW/NSMBW saída da água |
| Plataformas | manter deslocamento por `dx, dy` sem herança; flag `carries_velocity` por plataforma (esteiras futuras) soma `vx` da plataforma ao saltar | NSMBW: só chão "que carrega" transfere |
| Rampas | fora do escopo do núcleo (colisão AABB). Se entrarem: deslize ao agachar, +11 px/s em descida ×1,875 ≈ +20 px/s, invulnerabilidade a inimigos frágeis enquanto desliza | SMB3/SMW/NSMBW |

---

## 11. Implicações para o Lume — decisões concretas

1. **Adotar arco assimétrico (preset B) como `CALIBRATED_PROFILE`**, mantendo `LEGACY_PROFILE` byte a byte para os testes diferenciais/dourados já portados (`tests/unit/test_physics.py`, `test_golden_traces.py`). A troca de perfil é uma decisão de produto da síntese; o núcleo deve suportar os dois.
2. **Preservar altura (112 px) e tempo total (0,76 s)**: é a condição para não reabrir o desenho das 15 fases. Validar com `campaign-routes`/`routes` em Python antes de qualquer alteração de `jump_speed`.
3. **Corte do salto = velocidade + gravidade**: ao soltar, `vy = max(vy, −330)` e gravidade de queda imediata. Isso aproxima o salto mínimo de 23 % do máximo (SMB1 33 %, Lume hoje 15 %).
4. **Velocidade terminal 760 px/s** e **empurrão de teto +100 px/s**: quedas longas ficam legíveis e bater a cabeça deixa de "grudar".
5. **Bônus de corrida desligado por padrão**, com flag; se ligado, manter `t_sobe` constante ajustando `gravity_rise` (como o SMB1 faz entre faixas).
6. **Coyote 5 q e buffer 6 q**: tolerâncias modernas conscientes (nenhum Mario 2D as documenta), ainda generosas em relação a Celeste (5 q) e dentro das recomendações de 100–120 ms.
7. **Gravidade das entidades separada** (`world_gravity = 1550`): inimigos, itens e projéteis não mudam de comportamento com o perfil do jogador.
8. **Wall jump, giro, mola, bloco de nota e natação como módulos opcionais** com parâmetros nomeados; nenhum entra no Marco 2 sem teste de rota correspondente.
9. **Documentar unidades no código**: px/s e px/s² a 1/120 s; comentários devem citar a origem (SMB1 ×1,875 etc.) para que ajustes futuros não virem "números mágicos" (crítica de Winter 2017).
10. **Testes novos**: altura discreta ≈ `h − v0·dt/2`; `t_sobe`/`t_desce` dentro de ±1 passo; salto mínimo; alcance @340 px/s; teto; terminal; e um teste que compara os dois perfis nas 15 rotas (ambos devem concluir).

---

## 12. Lacunas e incertezas

- **SMW**: gravidade por quadro (segurando vs solto) não foi encontrada em fonte verificável; o valor ≈ 3/16 px/q² é inferência a partir da altura de 4 tiles. Também não há documentação do `vy` após bater no teto nem da herança de velocidade em plataformas.
- **SMB3**: as unidades da "jump gravity" (`$01`/`$05`) e o valor de `$A647` não foram transcritos pelo Data Crystal; as conversões (225/1125 px/s²) são ESTIMADAS. A relação com o limiar `$E0` sugere um arco mais "cortante" que o do SMB1, mas isso não foi medido.
- **SMB1**: o RAM map do Data Crystal lista gravidades (0x30/0x2D/0x38 e 0xA8/0x90/0xD0) 1,5× maiores que as tabelas da SMBpedia/desmontagem (0x20/0x1E/0x28 e 0x70/0x60/0x90). A medição independente de 53 quadros de voo e a altura de 4 tiles só são compatíveis com as tabelas da SMBpedia, que adotamos; a discrepância do RAM map permanece sem explicação.
- **NSMB DS/Wii/U e Wonder**: impulsos, gravidades e limites de queda não têm documentação pública localizada; só velocidades horizontais, alturas em blocos e timers. Os valores do Lume para esses títulos são analogias, não medições.
- **Spin jump no NSMBW**: fontes divergem (SMW: mais baixo; Prima: "extra height"). Não medido.
- **Coyote time/jump buffer**: ausência de evidência não é evidência de ausência; nenhuma análise quadro a quadro dos NSMB ou de Wonder sobre esse ponto foi encontrada.
- **Páginas não lidas na íntegra**: várias páginas da Super Mario Wiki ultrapassam o limite de leitura da ferramenta (Wall Jump, Triple Jump); as seções específicas dos NSMB podem conter detalhes adicionais. O site iwataasks.nintendo.com respondeu 503 durante a pesquisa; usamos os espelhos oficiais nintendo.com/en-gb e de-ch.
- **Frequência**: NES/SNES NTSC rodam a 60,0988 Hz; adotamos 60 Hz, erro < 0,2 %.
- **Escala corporal ×1,875**: é uma convenção nossa (altura do jogador pequeno); o Lume não usa tiles de 16 px, então comparações em "tiles" são aproximadas.

---

## 13. Fontes

Tipo: **oficial** (Nintendo), **entrevista** (desenvolvedores), **tecnico** (análise técnica/comunitária com dados), **comunitario** (wiki/guia), **docs** (literatura de desenvolvimento).

| # | Fonte | Tipo | URL |
| --- | --- | --- | --- |
| 1 | Nintendo — Ask the Developer Vol. 11, Super Mario Bros. Wonder, Part 1 | entrevista/oficial | https://www.nintendo.com/us/whatsnew/ask-the-developer-vol-11-super-mario-bros-wonder-part-1/ |
| 2 | Nintendo — Ask the Developer Vol. 11, Super Mario Bros. Wonder, Part 3 | entrevista/oficial | https://www.nintendo.com/us/whatsnew/ask-the-developer-vol-11-super-mario-bros-wonder-part-3/ |
| 3 | Iwata Asks — New Super Mario Bros. Wii Vol. 1, p. 1 "Mario Couldn't Jump At First" | entrevista/oficial | https://www.nintendo.com/en-gb/Iwata-Asks/Iwata-Asks-New-Super-Mario-Bros-Wii/Volume-1/1-Mario-Couldn-t-Jump-At-First/1-Mario-Couldn-t-Jump-At-First-210699.html |
| 4 | Iwata Asks — NSMB Wii Vol. 1, p. 5 "Allowing Novices To See the Ending Too" | entrevista/oficial | https://www.nintendo.com/en-gb/Iwata-Asks/Iwata-Asks-New-Super-Mario-Bros-Wii/Volume-1/5-Allowing-Novices-To-See-the-Ending-Too/5-Allowing-Novices-To-See-the-Ending-Too-210912.html |
| 5 | Iwata Asks — NSMB Wii Vol. 1, p. 7 "A Block Floating In Mid-Air Is Unnatural" | entrevista/oficial | https://www.nintendo.com/en-gb/Iwata-Asks/Iwata-Asks-New-Super-Mario-Bros-Wii/Volume-1/7-A-Block-Floating-In-Mid-Air-Is-Unnatural/7-A-Block-Floating-In-Mid-Air-Is-Unnatural-211017.html |
| 6 | Iwata Asks — NSMB Wii Vol. 1, p. 9 "The Correct Way to Enjoy An Action Game" | entrevista/oficial | https://www.nintendo.com/en-gb/Iwata-Asks/Iwata-Asks-New-Super-Mario-Bros-Wii/Volume-1/9-The-Correct-Way-to-Enjoy-An-Action-Game/9-The-Correct-Way-to-Enjoy-An-Action-Game-211131.html |
| 7 | Iwata fragt — NSMB Wii Teil 1 (espelho de-ch, índice) | entrevista/oficial | https://www.nintendo.com/de-ch/iwata_asks/interview_16795/16795.html |
| 8 | Iwata Asks — Super Mario 3D Land Vol. 2, p. 4 "What Is Stomping?" | entrevista/oficial | https://www.nintendo.com/en-gb/Iwata-Asks/Iwata-Asks-SUPER-MARIO-3D-LAND/Vol-2-The-producers/4-What-Is-Stomping-/4-What-Is-Stomping-215798.html |
| 9 | Iwata Asks — Super Mario Bros. 25th Anniversary Vol. 1, p. 12 | entrevista/oficial | https://www.nintendo.com/en-gb/Iwata-Asks/Super-Mario-Bros-25th-Anniversary/Vol-1-Itoi-asks-Miyamoto/12-Still-Provocative-25-Years-Later/12-Still-Provocative-25-Years-Later-217701.html |
| 10 | Manual Super Mario Bros. 3 (NES, EUA, 1990) — digitalização em texto | oficial | https://archive.org/download/NESManuals/Super%20Mario%20Bros.%203%20%28USA%29_text.pdf |
| 11 | Manual New Super Mario Bros. Wii (pp. 13–14, cópia hospedada) | oficial | https://manualsonline.com/manuals/mfg/nintendo/nsmbw.html?p=8 |
| 12 | Super Mario Wiki — List of Jump Profiles (1981–1989): citações dos manuais SMB/SMB3 | comunitario (cita oficial) | https://www.mariowiki.com/User:KamekSans/Projects/Lists_of_Jump_Profiles/List_of_Jump_Profiles_(1981-1989) |
| 13 | Super Mario Wiki — List of Jump Profiles (1990–1999): manual SMW | comunitario (cita oficial) | https://www.mariowiki.com/User:KamekSans/Projects/Lists_of_Jump_Profiles/List_of_Jump_Profiles_(1990-1999) |
| 14 | Super Mario Wiki — List of Jump Profiles (2000–2009): manuais NSMB/NSMBW | comunitario (cita oficial) | https://www.mariowiki.com/User:KamekSans/Projects/Lists_of_Jump_Profiles/List_of_Jump_Profiles_(2000-2009) |
| 15 | Super Mario Wiki — List of Jump Profiles (2010–2019): manual NSMB2 | comunitario (cita oficial) | https://www.mariowiki.com/User:KamekSans/Projects/Lists_of_Jump_Profiles/List_of_Jump_Profiles_(2010-2019) |
| 16 | SMBpedia — Movement (espelho simplistic6502): tabelas de salto/gravidade/natação/mola do SMB1 | tecnico | https://simplistic6502.github.io/smb1_tll/smbpedia_movement.html |
| 17 | 6502disassembly.com — listagem anotada de Super Mario Bros. (tabelas `JumpMForceData` etc., limite vertical do jogador) | tecnico | https://6502disassembly.com/nes-smb/SuperMarioBros.html |
| 18 | GitHub — "SMB movement and physics constants" (Raditron, issue #2): constantes e alturas 66/82 px | tecnico | https://github.com/Raditron/super-mario-evolutionary-algorhytm/issues/2 |
| 19 | Data Crystal — Super Mario Bros. RAM map (0x009F, 0x0433, 0x0709, 0x070A, 0x001D) | tecnico | https://datacrystal.tcrf.net/wiki/Super_Mario_Bros./RAM_map |
| 20 | negative-seven — smb1explained (buffer no power-up, walljump glitch) | tecnico | https://negative-seven.github.io/smb1explained |
| 21 | TASVideos — Game Resources NES Super Mario Bros. | tecnico | https://tasvideos.org/GameResources/NES/SuperMarioBros |
| 22 | TASVideos — Fórum "Help with Super Mario War" (medições quadro a quadro, 53 q, 4,2 px/q) | tecnico/observado | https://tasvideos.org/Forum/Posts/39637 |
| 23 | TASVideos — Game Resources NES Super Mario Bros. 3 (velocidades, rampas, walljump) | tecnico | https://tasvideos.org/GameResources/NES/SuperMarioBros3 |
| 24 | Data Crystal — Super Mario Bros. 3 Notes (jump power, gravidade, limite de queda) | tecnico | https://datacrystal.tcrf.net/wiki/Super_Mario_Bros._3/Notes |
| 25 | TASVideos — Game Resources SNES Super Mario World | tecnico | https://tasvideos.org/GameResources/SNES/SuperMarioWorld |
| 26 | SMW TAS blog — "The vertical speed in a jump" (tabela por faixa, A/B, molas, quiques) | tecnico | http://smw-tas.blogspot.com/2013/03/the-vertical-speed-in-jump.html |
| 27 | SMW RAM map (SMW Central, cópia Google Sites): $7B, $7D, $72, $75, $140D, $13FA, $1471 | tecnico | https://sites.google.com/site/smwrammap/ |
| 28 | smwspeedruns.com — Controls | comunitario | https://smwspeedruns.com/Controls |
| 29 | The Game Design Forum — Reverse Design: Super Mario World, parte 3 (alturas e distâncias em blocos) | tecnico/observado | https://www.quaddicted.com/webarchive/thegamedesignforum.com_20160521/features/RD_SMW_3.html |
| 30 | TASVideos — Game Resources DS New Super Mario Bros. (wall jump/slide, timers, 3,0 px/q) | tecnico | https://tasvideos.org/GameResources/DS/NewSuperMarioBros |
| 31 | NSMBW Speedrun Guides — Jumping | comunitario | https://nsmbwcommunity.github.io/NSMBW-Speedrun-Guides/movement/jumping/ |
| 32 | NSMBW Speedrun Guides — Speed | comunitario | https://nsmbwcommunity.github.io/NSMBW-Speedrun-Guides/movement/speed/ |
| 33 | NSMBW Speedrun Guides — Wallkicking | comunitario | https://nsmbwcommunity.github.io/NSMBW-Speedrun-Guides/movement/wallkicking/ |
| 34 | NSMBW Speedrun Guides — Moving Platforms | comunitario | https://nsmbwcommunity.github.io/NSMBW-Speedrun-Guides/movement/moving-platforms |
| 35 | NSMBW Speedrun Guides — Slopes | comunitario | https://nsmbwcommunity.github.io/NSMBW-Speedrun-Guides/movement/slopes/ |
| 36 | NSMBW Speedrun Guides — Swimming | comunitario | https://nsmbwcommunity.github.io/NSMBW-Speedrun-Guides/movement/swimming/ |
| 37 | Super Mario Wiki — Spin Jump | comunitario | https://www.mariowiki.com/Spin_Jump |
| 38 | Super Mario Wiki — Wall Jump | comunitario | https://www.mariowiki.com/Wall_Jump |
| 39 | Super Mario Wiki — Triple Jump | comunitario | https://www.mariowiki.com/Triple_Jump |
| 40 | Super Mario Wiki — Slope | comunitario | https://www.mariowiki.com/Slope |
| 41 | Super Mario Wiki — Slide | comunitario | https://www.mariowiki.com/Slide |
| 42 | Super Mario Wiki — Trampoline (cita manual SMB) | comunitario | https://www.mariowiki.com/Trampoline |
| 43 | Super Mario Wiki — Note Block (cita manual SMB3) | comunitario | https://www.mariowiki.com/Note_Block |
| 44 | Super Mario Wiki — Swim | comunitario | https://www.mariowiki.com/Swim |
| 45 | Super Mario Wiki — Lift | comunitario | https://www.mariowiki.com/Lift |
| 46 | Super Mario Wiki — Badge (Super Mario Bros. Wonder): descrições em jogo | comunitario (cita oficial) | https://www.mariowiki.com/Badge_(Super_Mario_Bros._Wonder) |
| 47 | smo.wiki — Coyote Time (Super Mario Odyssey) | comunitario | https://smo.wiki/Coyote_Time |
| 48 | Supper Mario Broth — coyote time nas seções 2D de Odyssey | comunitario | https://www.suppermariobroth.com/post/818978696362967040/the-2d-segments-of-super-mario-odyssey-feature-a/amp |
| 49 | Summerville et al., "Mechanics Automatically Recognized via Interactive Observation: Jumping" (arXiv 1707.03865) | tecnico/docs | https://arxiv.org/abs/1707.03865 |
| 50 | GDC Vault — Kyle Pittman, "Math for Game Programmers: Building a Better Jump" (2016) | docs | https://gdcvault.com/play/1023148/Math-for-Game-Programmers-Building |
| 51 | Traversing Virtual — resumo da palestra de Pittman e citação de Swink (*Game Feel*) | docs | https://traversingvirtual.blogspot.com/search/label/game%20feel |
| 52 | Alexander Winter, "Creating a jump formula for a platformer game" (2017) | docs | https://winteralexander.github.io/GamePhysicsBuilder/jump_formula.pdf |
| 53 | Lexaloffle BBS — tabela resumida de física do Mario (origem não nomeada; usada só como corroboração) | comunitario | https://www.lexaloffle.com/bbs/?pid=26323 |
| 54 | NESDev — "Super Mario Physics" (variação entre títulos) | tecnico | https://forums.nesdev.org/viewtopic.php?t=10447 |
| 55 | KidsCanCode / GDQuest / bugnet — referências de coyote time e buffer em 2D moderno | docs | https://kidscancode.org/godot_recipes/4.x/2d/coyote_time/index.html |
