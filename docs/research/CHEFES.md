# Chefes dos Mario 2D — engenharia reversa comportamental e proposta dos Cinco Guardiões do Lume

Documento de pesquisa da Etapa 2 (migração do Lume para Python 3.12 + pygame-ce 2.5.8). Objetivo: entender **como a Nintendo constrói, sinaliza, escala e encerra os chefes dos Mario 2D** (Super Mario Bros., Super Mario Bros. 3, Super Mario World, New Super Mario Bros., New Super Mario Bros. Wii, New Super Mario Bros. U e Super Mario Bros. Wonder, com apoio de New Super Mario Bros. 2, Super Mario 3D Land/World e Super Mario Maker 2 quando um chefe só existe lá) para projetar **cinco guardiões originais** coerentes com o motor do Lume (`game/bosses/boss.py`: `BossDefinition` → `Phase` → `Attack` com `telegraph`, `active`, `recover`). Nenhum sprite, ROM, música ou código proprietário foi extraído. Valores obtidos pela comunidade por desmontagem são citados como **documentação comunitária derivada de análise de terceiros**, nunca como valores oficiais.

Classificação usada em todo o texto:

| Rótulo | Significado |
| --- | --- |
| **OFICIAL** | Manual, site de produto ou entrevista publicada pela Nintendo/desenvolvedores (Iwata Asks, Ask the Developer, entrevistas reproduzidas pela Nintendo). Descreve intenção e comportamento; quase nunca dá números. |
| **DOCUMENTADO** | Artigo técnico, página de nível/personagem da Super Mario Wiki com fonte verificável, guia comunitário ou **documentação comunitária derivada de análise de terceiros** (desmontagem, mapas de RAM). Nunca é valor oficial. |
| **OBSERVADO** | Comportamento descrito a partir de gameplay/vídeo por imprensa, guias ou pelo autor, sem medição. |
| **ESTIMADO** | Inferência nossa (cálculo a partir de valores documentados, conversão de escala ou hipótese sem confirmação). |

Convenções: `q` = quadro a 60 Hz; `px/q × 60 = px/s`; `tile` = 16 px nos jogos NES/SNES. O fator de escala corporal do Lume em relação ao Mario pequeno do NES é **1,875** (30 px / 16 px), o mesmo de `FISICA.md`, `MOVIMENTACAO.md` e `PERSONAGENS.md`. Constantes do Lume usadas nos cálculos: gravidade 1550 px/s², impulso de salto 590 px/s (altura 112,3 px, voo 0,761 s), caminhada 220 px/s, corrida 340 px/s (alcance horizontal do salto 258,8 px), jogador 22×30 / 22×46 px, chefe atual 62×64 px, viewport 960×540, passo fixo 1/120 s.

---

## 1. Resumo executivo

1. **"Três golpes" é a gramática da série.** Koopalings (SMB3, SMW, NSMBW, NSMB2, NSMBU), Boom Boom, Bowser Jr. (todas as lutas de NSMB DS, NSMBW e NSMBU), Kamek (NSMBU), Reznor (cada um), Big Boo (3 blocos), Petey Piranha, Mummipokey, Monty Tank, Cheepskipper, Boss Goomba, Lakithunder, Boss Sumo Bro e o Bowser gigante de NSMBU caem com **três acertos na cabeça/ponto fraco** (DOCUMENTADO, seções 3–4). As exceções são contadas em rodadas, não em pontos de vida: Bowser em SMW leva 6 Mechakoopas em **3 rodadas de 2**; Wonder Bowser leva 2 + 2 acertos no interruptor e um toque final; o Bowser de SMB1 é vencido pelo **machado** (ou 5 bolas de fogo), o de SMB3 pelo **chão quebrável** (ou 35 bolas de fogo / 3 martelos).
2. **Dois verbos de vitória coexistem desde 1985**: *derrotar* (pisões) e *contornar* (passar por baixo do chefe e alcançar o machado/interruptor: SMB1, SMB3 por queda, NSMB DS, NSMBW, NSMBU, Wonder). Os finais modernos **encadeiam os dois**: ponte+interruptor → Kamek/Bowser Jr. amplia o chefe → nova mecânica (perseguição em NSMBW/NSMB2, Junior Clown Car sequestrado em NSMBU, plataformas rítmicas em Wonder) (DOCUMENTADO).
3. **Cada acerto muda algo**, nunca só a velocidade: Wendy passa a lançar 2 anéis (NSMBW) ou 3 (NSMBU); Lemmy troca bolas por bombas maiores; Iggy deixa o Chain Chomp mais rápido de forma permanente após o 2.º golpe; Ludwig acrescenta 4 bolas de fogo; Monty Tank ganha um andar e mais torretas; Kamek muda o padrão de feitiços em cada rodada; Boom Boom (SMB3) troca andar → voar/saltar alto → correr "em desespero" (DOCUMENTADO).
4. **A reação ao dano é a janela de "retaliação", não de vulnerabilidade.** Koopalings entram no casco e giram pela sala (dano por contato); Boom Boom cai tonto e levanta em "alguns segundos"; Iggy e Morton (em certas lutas) não entram no casco; o Bowser gigante de NSMBU encolhe no casco e gira e depois faz chover fogo (DOCUMENTADO). A regra é: **o jogador acerta → o chefe fica imune e ataca → volta ao ciclo**.
5. **Telegraph é explícito e frequentemente longo**: Bowser Jr. "must inhale for several moments" antes de cada bola de fogo (NSMBW); Morton tem "very slow casting"; Roy dá "dois pulinhos" antes do próximo tremor e finge sair de canos; Ludwig mostra as pernas por baixo da plataforma onde vai cair; Boss Sumo Bro muda de postura antes do pisão duplo; Wendy gira a varinha; Reznor ruge; a árvore… (DOCUMENTADO). Nos ataques instantâneos (relâmpago de Lakithunder) a wiki não descreve sinal prévio — uma lacuna que o Lume deve preencher por projeto.
6. **A arena é um ator**: chão de tijolos (SMB3), plataformas que sobem/descem (Larry, Ludwig NSMBW), inundação (Wendy NSMBW), canos (Lemmy/Wendy SMW, Roy NSMBW, Iggy NSMBU), lava que sobe (Iggy NSMBU), esteira com interruptor (Lemmy NSMB2), paredes que se fecham (Roy/Morton SMW, Roy NSMB2), cercas elétricas (NSMBW 6-Airship), piso falso de 30 blocos (Kamek NSMBU), piso rítmico (Wonder) (DOCUMENTADO).
7. **Segunda rodada com Kamek** (NSMBW): o mesmo Koopaling é enfrentado na torre e no castelo; no castelo, Kamek "enchanting certain aspects of the battlefield" — bola gigante de Lemmy, Chain Chomp ampliado de Iggy, canos no teto de Roy, inundação de Wendy, pilares de Morton, plataformas de Ludwig e Larry (DOCUMENTADO). O chefe muda pouco; **a arena muda a estratégia**.
8. **Números comunitários do Bowser original** (SMB1, desmontagem): 5 pontos de vida contra bolas de fogo, velocidade 2 px/q (= 120 px/s), raio aleatório de patrulha de 17/33/49/65 px a partir da posição inicial, salto por temporizador aleatório, martelos só a partir do Mundo 6, altura da chama sorteada de uma tabela de três alturas (não mira o Mario), colapso da ponte em 15 passos e tabela de "identidades" dos impostores por mundo (DOCUMENTADO, derivado de análise de terceiros).
9. **Legibilidade é intenção declarada pela Nintendo**: "enemies with thorns that signal damage" e "a visible platform ahead of a drop-off" constroem confiança; o pântano venenoso de NSMBW foi redesenhado para que "anyone who sees them [will] understand immediately what the situation is"; em Wonder os Goombas "have a biting expression the moment they do damage" (OFICIAL, Iwata Asks SMB 25.º aniversário e Ask the Developer Vol. 11).
10. **Recomendação para o Lume** (seção 7): manter **3 golpes por guardião** (4 no quarto mundo, 4 + alavanca no quinto), cada golpe abrindo uma fase que muda **o verbo do jogador** (bater na parede → atrair para a ponte frágil → usar a fruta; placa → previsão de teletransporte → tiros guiados; etc.), telegraph mínimo por mundo de **900 → 450 ms** (nunca abaixo de 400 ms com pista sonora), janelas de vulnerabilidade ≥ **1,0–1,6 s**, no máximo **2 perigos simultâneos**, chefe lendo apenas posição/velocidade observáveis e um **bot de justiça** nos testes (reage 250 ms após o telegraph e nunca pode ser atingido).

---

## 2. Gramática comum dos chefes 2D (padrões transversais)

### 2.1 Contagem de golpes e equivalência de projéteis

| Chefe (jogo) | Golpes para vencer | Equivalente em bolas de fogo | Fonte |
| --- | --- | --- | --- |
| Bowser (SMB1) | machado **ou** 5 bolas de fogo (5000 pts) | 5 | [MW-HistBowser][MW-FakeBowser][TMK-SMB][SMBDIS] DOCUMENTADO |
| Boom Boom (SMB3) | 3 pisões | 5 bolas de fogo ou 5 martelos | [MW-BoomBoom] DOCUMENTADO |
| Koopalings (SMB3) | 3 pisões | — (fogo funciona, contagem não documentada) | [MW-Larry][MW-Iggy][MW-Lemmy] DOCUMENTADO |
| Bowser (SMB3) | queda pelo chão quebrável | 35 bolas de fogo ou 3 martelos | [MW-HistBowser][MW-SMB3Castle] DOCUMENTADO |
| Morton/Roy/Ludwig (SMW) | 3 pisões | 12 bolas de fogo (4 por pisão) | [MW-Morton][MW-Roy][MW-Ludwig] DOCUMENTADO |
| Bowser (SMW) | 6 Mechakoopas em 3 rodadas | — | [MW-FrontDoor][MW-ClownCar] DOCUMENTADO |
| Big Boo (SMW) | 3 Grab Blocks no rosto | — | [MW-DonutSecretHouse] DOCUMENTADO |
| Bowser Jr. (NSMB DS, torres) | 3 pisões (só fora do casco) | fogo e *shell dash* também ferem | [MW-BowserJr] DOCUMENTADO |
| Mummipokey (NSMB DS) | 3 pisões (*ground pound* = 2) | 15 bolas de fogo (5 por pisão) | [MW-Mummipokey] DOCUMENTADO |
| Boss Goomba (NSMB DS) | 3 *ground pounds* (9 em Mini) | fogo funciona | [MW-BossGoomba] DOCUMENTADO |
| Larry (NSMBW torre) | 3 pisões | 18 bolas de fogo (6 por pisão) | [MW-Larry] DOCUMENTADO |
| Boss Sumo Bro (NSMBU) | 3 pisões na barriga | 18 bolas de fogo (6 = 1 pisão) | [MW-BossSumo] DOCUMENTADO |
| Reznor (NSMB2) | 1 acerto por baixo cada | 6 bolas de fogo cada | [MW-Reznor] DOCUMENTADO |
| Pom Pom (3D Land) | 3 pisões/rabo | 15 projéteis (5 por acerto) | [MW-PomPom] DOCUMENTADO |
| Boom Boom (3D World) | 3 acertos | 9 projéteis (3 por acerto) | [MW-BoomBoom] DOCUMENTADO |
| Bowser gigante (NSMBU) | 3 pancadas de Junior Clown Car na cabeça | 180 bolas de fogo (60 por acerto) ou 90 arremessos de Bowser Jr./Bob-ombs | [MW-GiantBowser][MW-NSMBU-Final] DOCUMENTADO |
| Wonder Bowser (Wonder) | 2 + 2 toques no interruptor do queixo, depois o interruptor da cabeça | — | [MW-Wonder-Final][MW-WonderBowser] DOCUMENTADO |

Leitura: a razão "projéteis por pisão" oscila entre **4 e 6** nos jogos 2D principais (SMW 4; NSMB 5; NSMBW/NSMBU 6). Se o Lume ganhar um poder de projétil, **5–6 acertos = 1 golpe** mantém a sensação da série (ESTIMADO a partir dos valores acima).

### 2.2 Os dois verbos de vitória

| Verbo | Títulos e mecanismo | Rótulo |
| --- | --- | --- |
| **Derrotar** (acertar N vezes) | Koopalings/Boom Boom (SMB3), todos os chefes de NSMB DS, torres/castelos de NSMBW/NSMB2/NSMBU, Bowser Jr. em Wonder | DOCUMENTADO |
| **Contornar** (passar por baixo e acionar algo) | SMB1: tocar o machado "cuts the support of the bridge" [MW-Axe]; NSMB DS: "skull switch" substitui o machado [MW-NSMB-W1C]; NSMBW: "wait for Bowser to jump, then slip underneath him and hit the ! Switch" [MW-NSMBW-W8C]; NSMBU: um ! Switch faz o **machado** cortar a ponte [MW-Axe][MW-NSMBU-Final]; Wonder: ! Switch sob o queixo e interruptor na cabeça [MW-Wonder-Final] | DOCUMENTADO |
| **Atrair** (fazer o chefe destruir o próprio apoio) | SMB3: "luring him into stomping through layers of brick floor" [MW-BrickFloor]; SMW: Iggy/Larry empurrados para a lava na plataforma inclinada [MW-Iggy][MW-Larry]; NSMB2: Roy atordoado ao bater na parede [MW-Roy] | DOCUMENTADO |

### 2.3 Ciclo canônico de um chefe moderno (NSMB → Wonder)

```
porta fecha → reação do chefe (surpresa/raiva, 1–2 s) → ciclo { telegraph → ataque → recuperação (vulnerável) }
→ golpe → retaliação (casco gira / tonto) → mudança (arena ou ataque) → … → 3.º golpe → cai da tela → chave / bandeira
```

- **Porta que fecha**: "the door closes behind him once he reaches Bowser" (NSMBW) [MW-NSMBW-W8C]; "Doors close both ends of the room before the fight starts" (NSMBU) [MW-NSMBU-Final]; em SMB3 a porta de saída **aparece** após Boom Boom deixar a bola mágica [MW-BoomBoom] (DOCUMENTADO).
- **Reação de entrada**: Larry "reacts with shock and rage"; Iggy "feigns shock… then taunts him by slapping his rear with the wand"; Wendy "throws her wand up, twirls, and catches it"; Morton "stamps his foot and growls"; Roy "roars"; Reznor "roar when the battle starts"; Boss Goomba começa como Goomba comum que cresce "making a sound similar to touching a Mega Mushroom" [MW-Larry][MW-Iggy][MW-Wendy][MW-Morton][MW-Roy][MW-Reznor][MW-BossGoomba] (DOCUMENTADO).
- **Derrota**: Koopalings "fall off-screen"; em NSMB DS a **chave** aparece (Petey "vanishes, revealing the key"; Boss Goomba "releases the key to World 5"); em NSMBU o chefe de torre "is briefly shown atop the tower… then toppled and replaced with a flag"; Boom Boom (SMB3) solta a bola mágica que destrói a fortaleza; Bowser gigante (NSMBU) "becomes dazed, roars, goes unconscious, and falls off the battlefield"; Wonder Bowser "lose[s] all Wonder Power and fall[s] to the ground" (DOCUMENTADO).
- **Após o golpe final o relógio ainda corre ~1 s** em NSMBU ("a player with one second left can still get Time's Up!") [MW-NSMBU-Final] — detalhe de implementação a evitar no Lume.

### 2.4 Sinalização (telegraph) documentada por chefe

| Chefe | Sinal antes do ataque | Fonte |
| --- | --- | --- |
| Bowser Jr. (NSMBW) | "must inhale for several moments before each shot" | [MW-Flame] DOCUMENTADO |
| Morton (NSMBW torre) | "His casting is very slow"; bate o pé antes da luta | [MW-Morton] DOCUMENTADO |
| Roy (NSMBW torre/castelo) | "hops twice before the next ground pound"; "fakes emerging [from a pipe], and retreats. He then emerges directly above Mario" | [MW-Roy] DOCUMENTADO |
| Ludwig (NSMBW castelo) | "His visible legs show where he'll land" | [MW-Ludwig] DOCUMENTADO |
| Ludwig (NSMBU) | o verdadeiro dispara 3 bolas (clones 2), tem olhos abertos, cai por último e ri; "Mario always looks at the real one" | [MW-Ludwig] DOCUMENTADO |
| Boss Sumo Bro (NSMBU) | pisão duplo precedido de "a brief change in stance" | [MW-BossSumo] DOCUMENTADO |
| Wendy (NSMBW) | "slow, graceful jumps"; "the spinning sound starts only after she moves within [the shell]" (NSMBU) | [MW-Wendy] DOCUMENTADO |
| Iggy (NSMB2) | "Dust clouds appear when he enters or exits" | [MW-Iggy] DOCUMENTADO |
| Petey (NSMB DS) | voa alto antes de cair "using a move similar to a Ground Pound" | [MW-Petey] DOCUMENTADO |
| Pom Pom (3D World) | gesto com a mão antes de teletransportar; fumaça rosa | [MW-PomPom] DOCUMENTADO |
| Bowser (SMB3) | "After two or three fireballs, he jumps and tries to land on the player's position" — ritmo previsível | [MW-SMB3Castle] DOCUMENTADO |
| Bowser (SMB1) | chamas "slow, but their timing and placement are unpredictable" | [MW-Flame] DOCUMENTADO |

### 2.5 Mudança por golpe e por rodada (escalada)

| Chefe | Após o 1.º golpe | Após o 2.º golpe | Fonte |
| --- | --- | --- | --- |
| Boom Boom (SMB3) | corre/salta alto **ou** voa (asas aparecem na animação de dano) | anda "much faster… stops crouching, and loses any wings" | [MW-BoomBoom] |
| Wendy (NSMBW torre) | — | "jumps faster and higher and casts two rings at once" | [MW-Wendy] |
| Wendy (NSMBU) | 2 anéis | 3 anéis | [MW-Wendy] |
| Lemmy (NSMBU) | — | bombas maiores | [MW-Lemmy] |
| Larry (NSMBU) | — | "casts two fireballs in quick succession" | [MW-Larry] |
| Iggy (NSMBW castelo) | Chain Chomp fica vermelho, inverte e acelera por pouco tempo | "stays faster for the rest of the fight" | [MW-Iggy] |
| Ludwig (NSMBW castelo) | — | "fires four more fireballs after his first set" | [MW-Ludwig] |
| Ludwig (NSMBU) | clones passam a permanecer | todos atiram mais rápido e trocam de posição | [MW-Ludwig] |
| Monty Tank (NSMB DS) | +1 andar, +torretas; gira e corre com alarme | idem | [MW-MontyTank] |
| Petey (NSMB DS) | — | "attacks by jumping from side to side" | [MW-Petey] |
| Kamek (NSMBU) | 3 teletransportes acima da sala + feitiços que viram blocos em Donut Blocks | 4 feitiços, depois 5 | [MW-SlideLift] |
| Bowser Jr. (NSMBW W8) | — | "the Koopa Clown Car starts dropping larger bombs" | [MW-NSMBW-W8A] |
| Bowser Jr. (NSMBU Cannonship) | rajada de 6 Torpedo Teds horizontais | rajada de 8 verticais | [MW-Cannonship] |
| Wonder Bowser Jr. (Fluff-Puff) | plataformas viram gelo | viram mel (lento); depois gelo que volta a mel; convoca Goombas | [MW-FluffPuff] |

Todos DOCUMENTADO. Observe que **nenhuma** dessas mudanças é "só mais rápido": a Nintendo adiciona um elemento ou troca o estado da arena.

---

## 3. Fichas: Bowser

### 3.1 Super Mario Bros. (1985) — a ponte e o machado

- **Estrutura**: Bowser (ou um impostor nos Mundos 1–7) espera numa ponte sobre lava; em 8-4 o jogador enfrenta antes um Hammer Bro e um Podoboo [MW-W84]. Tocar o machado "cuts the support of the bridge", e Bowser cai; se já foi derrotado por bolas de fogo, "the bridge-collapse animation does not play" [MW-Axe] (DOCUMENTADO).
- **Ataques**: "jumps, throws hammers, and spits fireballs"; derrotado "if either the ax is touched on the other side or if he is hit by five fireballs" [MW-HistBowser]. Martelos "beginning from 6-4" [TASV-SMB]; os impostores dos Mundos 6 e 7 só usam martelos e os dos Mundos 1–5 só fogo; o Bowser real (8) usa ambos [MW-FakeBowser][MW-Flame] (DOCUMENTADO).
- **Impostores** revelados por 5 bolas de fogo: Goomba (1), Koopa verde (2), Buzzy Beetle (3), Spiny (4), Lakitu (5), Blooper (6), Hammer Bro (7) [MW-FakeBowser]; a tabela `BowserIdentities` da desmontagem confirma a ordem e a premiação de **5000 pontos** [SMBDIS][TMK-SMB] (DOCUMENTADO).
- **Chamas**: começam a aparecer "from offscreen as Mario reaches the midpoint of castles"; "slow, but their timing and placement are unpredictable" [MW-Flame] (DOCUMENTADO).
- **IA interna (documentação comunitária derivada da desmontagem de doppelganger [SMBDIS])**:

| Parâmetro | Valor bruto | Conversão (60 q/s) | Em escala Lume (×1,875) |
| --- | --- | --- | --- |
| Pontos de vida contra fogo (`BowserHitPoints`) | 5 | — | — |
| Velocidade horizontal (`BowserMovementSpeed`) | 2 px/q | 120 px/s | ≈225 px/s (≈ caminhada do Lume, 220) |
| Raio máximo a partir da posição inicial (`MaxRangeFromOrigin`, sorteado) | $11/$21/$31/$41 = 17/33/49/65 px | — | 32/62/92/122 px |
| Reavaliação de direção | a cada 16 q | 0,27 s | — |
| Avanço máximo à direita | até X = $C8 (200 px) | — | — |
| Salto | temporizador aleatório quando Y ≥ $80; impulso vertical $FE | unidade interna; conversão não verificada | ESTIMADO |
| Altura da chama (`FlameYPosData`) | $90/$80/$70/$90 (144/128/112 px do topo) | 3 fileiras com 16 px de intervalo; a mais baixa com 50 % de chance | fileiras a 30 px |
| Martelos | só `WorldNumber` ≥ 6; checagem a cada 4 q | — | — |
| Chamas | Mundo 8 sempre; Mundos 6–7 nunca; Mundos 1–5 quando o temporizador de sopro expira; "secondary hard mode" encurta o temporizador | — | — |
| Colapso da ponte (`BridgeCollapseData`) | 15 passos: machado, corrente, depois os tijolos; som a cada passo | — | — |
| Fim | Bowser derrotado abaixo de Y = $E0 → música silencia, todos os inimigos removidos | — | — |

  Conclusão de projeto: a chama **não mira o jogador** — ela sorteia uma de três alturas; a imprevisibilidade percebida vem do sorteio do temporizador e da altura, enquanto a esquiva é sempre possível por **saltar ou agachar** (OBSERVADO + DOCUMENTADO). O raio de patrulha curto (≤ 65 px) e a velocidade igual à caminhada explicam por que "passar por baixo" é viável.

- **Variações**: Lost Levels adiciona um "Fake Bowser (Blue)" antes do verdadeiro em 8-4 [MW-Bowser]; em Super Mario Advance 4 o falso Bowser anda e o real "only leaps"; em Super Mario Run os falsos "walk back and forth on their bridge" [MW-FakeBowser] (DOCUMENTADO). Em Super Mario Maker o machado é a meta de castelo e "every enemy on screen falls into the lava" [MW-Axe].

### 3.2 Super Mario Bros. 3 (1988) — o chão quebrável

- **Castelo**: 400 s de limite; estátuas que disparam lasers, elevador invisível, Donut Lifts, Roto-Discs, Thwomp deslizante; **duas versões da sala final** — a rota do Thwomp leva a uma sala "with fewer bricks to break", mais fácil [MW-SMB3Castle] (DOCUMENTADO).
- **Comportamento**: "Bowser constantly hops throughout the battle"; dá um salto longo até o lado oposto se o jogador se afasta; "breathes two fireballs, then leaps and performs a Ground Pound, destroying the blocks upon impact" [MW-HistBowser]; fogo "at different heights, so the player must jump or crouch" [MW-SMB3Castle] (DOCUMENTADO). "Each landing breaks the two bricks beneath him" [Thonky-SMB3] (OBSERVADO/guia).
- **Vitória**: atrair Bowser para cair "on the same section two or three times, depending on which room version"; ou 35 bolas de fogo; ou ≥ 3 martelos [MW-SMB3Castle][MW-HistBowser] (DOCUMENTADO). O chão de tijolos "act[s] as an interactive element separate from ordinary ground only in the final battle" [MW-BrickFloor].
- **Lição**: a derrota é consequência do **próprio ataque do chefe**; o jogador controla *onde* ele cai posicionando-se. É o modelo mais puro de "o chefe usa apenas informação observável" — ele mira a posição do jogador no instante do salto.

### 3.3 Super Mario World (1990) — Koopa Clown Car em três rodadas

- Bowser "sits inside of the Koopa Clown Car during the entire battle"; tocar a hélice fere, tocar o resto só repele [MW-HistBowser][MW-FrontDoor] (DOCUMENTADO).
- **Rodada 1**: voa no topo e lança Mechakoopas; pisar e arremessar um Mechakoopa contra o carro = 1 acerto; após **2 acertos** ele sai da tela e "drops Flames from the sky"; Peach lança um Super Mushroom. **Rodada 2**: paira sobre o jogador e solta **duas Big Steelies**, depois 2 Mechakoopas (2 acertos), novas chamas, segundo cogumelo. **Rodada 3**: "Bowser and the Clown Car bounce on the ground, trying to crush the player", 2 Mechakoopas finais — **6 acertos no total**; o HUD fica oculto na versão SNES [MW-FrontDoor] (DOCUMENTADO). "He can only be hurt by a jumped-on Mechakoopa thrown at him as he sticks his head out" [MW-ClownCar].
- Chamas estacionárias quando ele voa para fora; o Spin Jump quica nelas com segurança [MW-Flame] (DOCUMENTADO).
- **Lição**: a munição é dada pelo chefe (Mechakoopas) — vulnerabilidade **condicionada a um recurso** que o jogador precisa capturar e usar na hora certa; a Nintendo intercala **pausas de cura** (cogumelos) entre rodadas.

### 3.4 New Super Mario Bros. (DS, 2006) — interruptor de crânio, Dry Bowser e Bowser 1,5×

- **Mundo 1-Castelo**: ponte pequena sobre lava com "skull switch" numa ponta; contornar ou vencer com fogo; 500 s; ao cair na lava Bowser vira **Dry Bowser** [MW-NSMB-W1C] (DOCUMENTADO). Fogo laranja "shot forward, sometimes while jumping, similar to in Super Mario Bros." [MW-Flame].
- **Mundo 8-Castelo (Dry Bowser)**: "drops from the ceiling, falls apart, then reassembles"; ataques: "small flames", **ossos arremessados**, "high jumps"; esquiva: esperar o salto alto e correr por baixo (mais fácil com Mini Mushroom); "fireproof, so Fire Mario's fireballs do not have any effect"; vitória pelo interruptor, por Mega Mushroom ou por **3 shell dashes** [MW-DryBowser] (DOCUMENTADO).
- **Mundo 8-Castelo do Bowser (final)**: Bowser Jr. joga os ossos num caldeirão; sai um Bowser "only about one and a half times larger than normal" [MW-GiantBowser]; **fase 1** — Bowser Jr. lança cascos enquanto Bowser cospe fogo azul teleguiado; 3 pisões em Bowser Jr., que cai no fosso; **fase 2** — Bowser cospe "three homing blue fireballs or five orange fireballs", e "after a few fireballs, he jumps high, which lets Mario pass under him to reach the skull switch" [MW-NSMB-W8BC][MW-Flame] (DOCUMENTADO).
- **Lição**: dois chefes simultâneos com papéis distintos (um mira, outro bloqueia); o salto alto do bloqueador **é a janela** do verbo "contornar".

### 3.5 New Super Mario Bros. Wii (2009) — interruptor, Kamek-Peach e o Bowser gigante

- **Fase 1**: corredor de bolas de fogo antes do chefe; a porta fecha; Bowser cospe fogo ("usually fires diagonally downward or uses the five-fireball sequence"); "Mario must wait for Bowser to jump, then slip underneath him and hit the ! Switch" [MW-NSMBW-W8C][MW-Flame] (DOCUMENTADO). Em NSMBW "lava does not defeat him" [MW-Bowser].
- **Virada**: a "Peach" na jaula é **Kamek disfarçado**, que amplia Bowser (Super Bowser), que o atira para longe e ruge [MW-NSMBW-W8C].
- **Fase 2 (perseguição)**: labirinto de estruturas e plataformas sobre lava; Super Bowser cospe bolas de fogo enormes ("massive fireballs that ice cannot stop… destroy structures on contact and explode after a few moments"), destrói paredes e "stomps in the lava to create hazardous lava swells"; Propeller Mushroom e Fire Flower ajudam; o **! Switch grande** sob a jaula de Peach faz a lava baixar levando Bowser [MW-NSMBW-W8C][MW-GiantBowser][MW-Flame] (DOCUMENTADO). A duração da perseguição não é documentada.
- **Lição**: o final troca o verbo de "contornar" para **"correr"**; os perigos (bolas de fogo que explodem após alguns instantes, ondas de lava) são lentos e grandes — legíveis à distância.

### 3.6 New Super Mario Bros. 2 (3DS, 2012) — breve

Bowser é derrotado como em NSMBW; os Koopalings o ampliam com as varinhas; Mario sobe em elevadores de osso enquanto Super Bowser ataca do fundo (garras que destroem plataformas, jatos de fogo, estátuas que cospem, fogo roxo teleguiado) até um interruptor sob Peach; **Big Dry Bowser** (World Star) é "faster", com fogo azul, ossos em vez de marretas, plataformas menores e sem Peach [MW-GiantBowser][MW-DryBowser][MW-Flame] (DOCUMENTADO). Os Koopalings no Koopa Clown Car tentam petrificar Mario "by 'flashing' its eyes", evitado atrás de barreiras do cenário [MW-ClownCar].

### 3.7 New Super Mario Bros. U (2012) — The Final Battle

- **Aproximação**: Bowser Jr. persegue no Junior Clown Car "dropping onto players' heads and sometimes pushing them toward the lava"; sua cúpula de vidro o torna inatingível aqui; 13 Lava Bubbles e 6 Bony Beetles; checkpoint; Fire Flower e Ice Flower em blocos ocultos; corredor de fogo; portas fecham [MW-NSMBU-Final] (DOCUMENTADO).
- **Fase 1**: espelha NSMBW; o interruptor faz um **machado** cortar a ponte [MW-Axe]. Bowser Jr. chega com Kamek desacordado e **ele mesmo** lança o feitiço de ampliação [MW-NSMBU-Final][MW-GiantBowser].
- **Fase 2 (pátio, Peach numa torre)**: ataques do Bowser gigante — bolas de fogo (3 Ice Balls para apagar cada), pisões, saltos, "up to five fireballs at once", jatos, garras; **após cada acerto** "he curls into his shell and spins around the arena, then breathes fire that rains down" [MW-GiantBowser]. Bowser Jr. joga Bob-ombs e faz *ground pound* no carro; pisar nele e **sequestrar o Junior Clown Car**, pairar (toques rápidos de salto) e girar para cair na cabeça de Bowser; ser atingido só derruba Mario do carro, sem dano; alternativas: arremessar Bowser Jr. no pai, fogo, Bob-ombs, Synchro Ground-Pounds em multijogador [MW-GiantBowser][MW-NSMBU-Final].
- **Números**: 3 acertos de carro, 180 bolas de fogo ou 90 arremessos; 700 s (800 com Toadette/Nabbit, 500 a partir do checkpoint); a jaula/pátio tem um gerador infinito de "big" Bowser's Flame (meteoros) [MW-NSMBU-Final][MW-GiantBowser] (DOCUMENTADO).
- **Lição**: a arma do chefe-auxiliar vira a arma do jogador; o erro **não custa vida** (cair do carro), só tempo — redução de punição no clímax.

### 3.8 Super Mario Bros. Wonder (2023) — Castle Bowser / Wonder Bowser

- **Contexto**: Bowser toca uma Wonder Flower e se funde ao Koopa Clown Car e ao castelo de Florian [MW-CastleBowser][MW-ClownCar]; o nível final é cinco estrelas e seu Wonder Effect "is a combination of past Wonder Effects" [MW-CastleBowser] (DOCUMENTADO).
- **Forma**: cabeça de pedra flutuante, olhos verdes, duas mãos de fumaça com hexágonos roxos; **! Switch sob o queixo**; "The arena is a rhythm platform that activates on the beat" e "Jumping on the beat can also destroy the floating hands, but they regenerate" [MW-Wonder-Final][MW-WonderBowser] (DOCUMENTADO).
- **Fases**: (1) mãos disparam Fiery Note Piranhas; o Big Fiery Note Piranha se divide em 4; braços esmagam; **após 2 toques** vai para o fundo e atira dos dois lados; (2) o piso se divide em duas metades, a direita "activates four beats after the left"; ganha a 3.ª mão que protege o interruptor ("hovers above his hands for protection"); o Big Piranha divide em 6; (3) padrões alternados, 4.ª mão, Spike-Balls prateadas "that resemble disco balls"; divide em 8; **após 2 toques** o cabelo quebra e expõe um **Bowser Switch** na cabeça; (4) plataformas aéreas, mãos patrulham, "smoke balls that bounce you away" (sem dano); apertar o interruptor derrota [MW-Wonder-Final][MW-WonderBowser] (DOCUMENTADO).
- **Lição**: a "vulnerabilidade" é um **interruptor acessível por plataforma rítmica** — o desafio está em *chegar*, não em acertar; o último toque é sem perigo letal (fumaça só repele) — fechamento generoso. A wiki aponta semelhança com Andross (Star Fox 64) ao expor o núcleo [MW-WonderBowser].

---

## 4. Fichas: os demais chefes

### 4.1 Bowser Jr.

| Jogo / luta | Veículo | Ataques | Como ferir | Golpes | Mudança por golpe | Fonte |
| --- | --- | --- | --- | --- | --- | --- |
| NSMB DS, torre de cada mundo | a pé | bandana solta → "jumps and charges"; bandana na boca → "throws a Koopa Shell and ducks into his shell when Mario is close" | pisão **só fora do casco**; fogo; shell dash | 3 | nos Mundos 2, 3, 5 e 8 "jumps high after two hits"; arenas variam (areia movediça, água, lava, plataformas inclinadas sobre espinhos) | [MW-BowserJr] |
| NSMB DS, final (com Bowser) | a pé | lança cascos | pisão | 3 | — | [MW-NSMB-W8BC] |
| NSMBW 4-Airship | Junior Clown Car | bolas de fogo que "set the ground ablaze" (deixam fogueiras); inspira antes de cada tiro | Propeller Blocks (arremesso = 1 pisão) ou pisão com hélice | 3 | — | [MW-BowserJr][MW-NSMBW-W4A][MW-Flame] |
| NSMBW 6-Airship | Junior Clown Car danificado vs **Remote-Controlled Clown Car** do jogador | tenta empurrar Mario na cerca elétrica | empurrá-lo contra a cerca; pisão só com Propeller Suit | 3 | carro intacto se o 4-Airship foi pulado por canhão | [MW-NSMBW-W6A] |
| NSMBW 8-Airship | expulso para o **Koopa Clown Car** | bolas de fogo múltiplas e teleguiadas; Giant Spiked Balls pelo canhão da boca | Ground Pound no chão lança a bomba de volta | 3 bombas | "After the second hit, the Koopa Clown Car starts dropping larger bombs" | [MW-NSMBW-W8A][MW-ClownCar] |
| NSMBU The Mighty Cannonship | Junior Clown Car **submarino** | Targeting Teds; correntes dos canos empurram para baixo | guiar os Targeting Teds contra o submarino | 3 | rajada de 6 Torpedo Teds horizontais, depois 8 verticais; a sala drena | [MW-Cannonship] |
| NSMBU Boarding the Airship | Junior Clown Car com **luvas de boxe** | destrói os blocos de aço onde o jogador pisa; joga Bob-ombs | devolver as Bob-ombs | 3 | — ; derrota: a Mecha Hand fura a nau | [MW-Boarding] |
| NSMBU The Final Battle | Junior Clown Car | Bob-ombs, pisões de carro | pisar e **sequestrar o carro** → cabeça de Bowser | (3 em Bowser) | Bowser Jr. "can be stunned", arremessado | [MW-NSMBU-Final] |
| Wonder, 4 palácios | a pé → **Wonder Bowser Jr.** após o 1.º golpe | gira no casco, bolas de fogo; pode saltar até plataformas altas | pisão quando para de girar | 4 (implícito) | Pipe-Rock: tamanhos trocam (jogador grande/ele pequeno, depois o inverso; gigante "takes less damage", ground pound vale mais); Fluff-Puff: plataformas viram gelo → mel → gelo que vira mel, Goombas; Sunbaked: baixa a água, Water Balls, "mouth" teleguiado, espinhos no chão; Deep Magma: fundo de fogo + plataformas-silhueta com olhos, depois 2 clones cinza "spin more slowly", depois clones + fogo | [MW-WonderJr][MW-PipeRock][MW-FluffPuff][MW-Sunbaked][MW-DeepMagma] |

Personalidade documentada: "energetic, precocious, driven, and mischievous, with a lonely side… wants to make his father proud… mechanically gifted" [MW-BowserJr] (DOCUMENTADO). Nota de conflito de fontes: a página de Bowser Jr. diz que as rajadas do Cannonship têm "three from the sides or four from the ceiling and floor"; a página do nível diz 6 e 8 — registrado na seção 9.

### 4.2 Kamek

- **NSMBW**: não é enfrentado como chefe; "aids the Koopalings by enchanting certain aspects of the battlefield" nos castelos (bola gigante de Lemmy, Chain Chomp de Iggy, canos de Roy, inundação de Wendy, pilares de Morton, plataformas de Larry/Ludwig), disfarça-se de Peach ("Can imitate Peach's voice") e amplia Bowser; sobrevive a ser jogado na lava [MW-Kamek][MW-Lemmy][MW-Iggy][MW-Roy][MW-Wendy][MW-Morton][MW-Ludwig][MW-Larry] (DOCUMENTADO).
- **NSMBU, Slide Lift Tower (Meringue Clouds; a wiki lista o chefe como "Magikoopa")**: sala com **30 blocos geométricos** formando piso falso sobre o abismo; Kamek enche a sala com plataformas mágicas em posições aleatórias, algumas com inimigos (Goombas, Koopas, Paratroopas, Mini Goombas, Monty Moles, Bob-ombs), teletransporta-se algumas vezes, derruba as plataformas soltando os inimigos e reconstrói a sala; **1.º pisão** → 3 teletransportes acima da sala, um feitiço após cada um, "Solid blocks hit by the spells become Donut Blocks", sala preenchida com blocos de vidro; **2.º pisão** → 4 feitiços e depois 5; **3.º pisão** → cai, Donut Blocks revertem; 500 s [MW-SlideLift] (DOCUMENTADO).
- **NSMBU final**: chega desacordado; Bowser Jr. lança o feitiço [MW-NSMBU-Final]. Personalidade: "Outwardly polite but often condescending and sarcastic" [MW-Kamek].
- **Lição**: Kamek é o chefe que **reescreve a arena** a cada rodada; a vulnerabilidade acontece entre ciclos de reconstrução, e a aleatoriedade está na *disposição*, não no *tempo* dos ataques.

### 4.3 Koopalings (sete padrões distintos)

| Koopaling | SMB3 (navio) | SMW (castelo) | NSMBW torre → castelo (Kamek) | NSMB2 | NSMBU | Fonte |
| --- | --- | --- | --- | --- | --- | --- |
| **Larry** | salta e dispara pela varinha; 3 pisões | plataforma inclinada sobre lava com 3 Lava Bubbles; imune, é empurrado | bolas azuis e saltos altos; casco gira; 3 pisões ou 18 bolas de fogo → castelo: plataformas sobem/descem, "Larry can become stuck between platforms" | tiros que ricocheteiam; 2 pilares em 4 buracos | gêiseres de água o impulsionam no casco; após 2 pisões, 2 bolas seguidas | [MW-Larry] |
| **Morton** | salta/varinha (sem tremor) | anda nas paredes e teto e cai sobre Mario; 3 pisões/12 fogo | Skewers nas pontas; fogo mirado em qualquer direção; tremor curto; "casting is very slow"; casco rápido → castelo: chão abaixado, pisão **ergue as plataformas laterais até o teto** (esmagamento = morte instantânea); sem tremor e sem magia | bolas de espinhos; tremor atordoa | ponte sobre areia movediça; Pokey de 5 segmentos lançado com **martelo** (3 segmentos, depois 2) | [MW-Morton] |
| **Wendy** | investidas e anéis (até 3); salta mais alto após pisão | sai de cano aleatório com 2 iscas; 3 pisões | gira a varinha; anéis que quicam e se dissolvem; saltos lentos; após 2.º pisão "two rings at once" → castelo: **inundação** periódica, "Water slows players, Wendy, and the rings alike" | sala subaquática, assovia Cheep Cheeps | patins no gelo; 2 → 3 anéis | [MW-Wendy] |
| **Iggy** | salta sobre Mario, varinha; entra no casco e **salta** antes de sair | plataforma-casco sobre lava; só é empurrado | 3 plataformas móveis; bolas verdes "among the fastest"; casco "much faster" → castelo: carruagem num **Chain Chomp ampliado**; atacar por trás; cada golpe: fica vermelho, inverte, acelera; "collapses and flails" (sem casco) | grade de trilhos; Chain Chomp menor; nuvens de poeira sinalizam entrada/saída | lava no chão, 4 canos por parede, anda no teto; 3 bolas por rajada (verdes + orbes vermelhos que viram Magmaarghs) | [MW-Iggy] |
| **Roy** | saltos com **tremor** e varinha | paredes e teto; "walls steadily close in"; 3 pisões/12 fogo | areia movediça; tremor atordoa se no chão; "hops twice" entre tremores → castelo: 5 canos no teto, finta e cai "directly above Mario" | investida; **atordoa ao bater na parede**; paredes se fecham a cada pisão | ninho de gávea; canhão de Bullet Bills; plataformas paralelas; tremor dispara Bullet Bills dos dois lados (sem atordoar) | [MW-Roy] |
| **Lemmy** | em cima de uma bola; invoca bolas que ficam; fica parado no casco; depois corre errático; 3 pisões | 2 iscas em canos; 3 pisões | bolas que podem impulsionar; após 2 bolas atravessa a sala; cada pisão: bola cai, casco gira, nova bola → castelo: bola **gigante**; após 4 bolas quica para o outro lado; cresce após 2 pisões | esteira com interruptor no teto | **bombas** à mão; maiores após 2 pisões | [MW-Lemmy] |
| **Ludwig** | tremor ao pousar, varinha | 3 bolas de fogo seguidas, casco e saltos; 3 pisões/12 fogo | bola teleguiada e **flutter jump** → castelo: 3 plataformas que sobem/descem; bola que se divide em 4; "visible legs show where he'll land"; após 2 golpes, mais 4 bolas | correntes no teto e 5 canhões | **2 clones** (real atira 3, clones 2; cai por último e ri); após 2.º pisão trocam de posição | [MW-Ludwig] |

Todos DOCUMENTADO. Personalidades (Super Mario Wiki): Larry trapaceiro e esportista; Morton falastrão e forte; Wendy mimada e temperamental; Iggy hiperativo e "inventor louco"; Roy valentão de óculos; Lemmy inocente e circense; Ludwig o mais velho, compositor e por vezes o mais cruel; desenhados a partir da equipe de SMB3 e nomeados pela Nintendo of America em homenagem a músicos; Miyamoto declarou que não são filhos de Bowser [MW-Koopalings] (DOCUMENTADO, com uma entrevista citada pela wiki).

### 4.4 Boom Boom e Pom Pom

- **Boom Boom (SMB3)**: "Walks toward Mario while flailing his arms, occasionally crouches to show his spikes"; 3 pisões; 5 bolas de fogo ou 5 martelos; **após o 1.º golpe** corre e salta alto **ou** voa (a partir da 1.ª fortaleza de Water Land; asas aparecem na animação de dano e somem quando ele agacha); **após o 2.º** "walks left and right much faster, possibly as a desperation tactic, stops crouching, and loses any wings"; **após o 3.º** solta a bola mágica que destrói a fortaleza [MW-BoomBoom] (DOCUMENTADO).
- **Boom Boom (NSMBU, torres)**: antes de quase todas as lutas um Magikoopa lhe dá um poder: spin jump (Layer-Cake Desert, mantido em Sparkling Waters, Frosted Glacier e Soda Jungle), saltos "SMB3-style", tamanho maior (Soda Jungle), **asas** (Rock-Candy Mines); ao ser atingido "flops dizzily to the ground and gets back up after a few seconds" [MW-BoomBoom] (DOCUMENTADO; a wiki não dá a contagem de pisões em NSMBU — a convenção de 3 é OBSERVADO).
- **Boom Boom (3D Land / 3D World)**: gira os braços → fica tonto e vulnerável; 3 acertos ou 9 projéteis em 3D World; em Bullet Bill Brigade fica quase **invisível** após cada golpe; em Bob-omb Brigade teletransporta com cópias de casco [MW-BoomBoom] (DOCUMENTADO).
- **Pom Pom**: 3D Land — até 2 bumerangues (3 no Mundo 7) e salta; ao ser atingida "hides in her shell and hovers, trying to land on Mario"; 3 pisões ou 15 projéteis. 3D World — shurikens e **clones translúcidos** (2 → 3 → 5; 5/7/8 na revanche); a real "has a hair bow and a pink shuriken with a red bow"; não entra no casco; teletransporte com fumaça rosa. Super Mario Maker 2 (estilo 3D World, visão lateral): 1 clone, depois 2 e 3. **Não há aparição 2D clássica** [MW-PomPom] (DOCUMENTADO). Personalidade: "wants to seem refined and elegant but often loses her temper".

### 4.5 Reznor — correção de escopo: SMW e **NSMB2** (não NSMBU)

- **SMW**: quatro Reznors em plataformas presas a uma roda de tábuas giratória; cospem bolas de fogo; cada um cai ao ser atingido **por baixo**; "After two fall, the bridge starts collapsing from the sides", e o jogador pode subir numa plataforma vazia [MW-Reznor] (DOCUMENTADO).
- **NSMB2 (torres)**: plataformas viram Long ? Blocks de 3 blocos; 2 ou 4 Reznors em 1 ou 2 rodas (configurações por mundo listadas na wiki); rugem no início; "attack less often, and their fireballs move slower"; na metade "they roar and stomp their blocks, collapsing the room's bridges" mais devagar que em SMW; 6 bolas de fogo cada ou 1 bola dourada [MW-Reznor] (DOCUMENTADO). Nome em homenagem a Trent Reznor (Dayvv Brooks).
- **Lição**: chefe-coletivo cuja **metade** da vida dispara a mudança da arena.

### 4.6 Big Boo (SMW, Donut Secret House)

Chefe oculto: "does not hide when Mario or Luigi faces it. Instead, it periodically changes from invisible to visible"; atirar **Grab Blocks** no rosto enquanto visível; **3 acertos**; é inofensivo, mas dois Boos comuns acompanham; cuidado para não abrir um buraco no chão; recompensa: caminho para a Star World; refazível em todas as versões [MW-BigBoo][MW-DonutSecretHouse] (DOCUMENTADO). O manual de SMW diz dos Big Boos: "act shy and turn away" quando olhados, "watch it… they're dangerous!" [MW-BigBoo] (OFICIAL, via transcrição da wiki).

### 4.7 Chefes de New Super Mario Bros. (DS)

| Chefe (mundo) | Padrão | Vulnerabilidade | Mudança | Alternativas | Fonte |
| --- | --- | --- | --- | --- | --- |
| **Mummipokey** (2) | emerge do chão em vários pontos com 2–5 segmentos ("The more segments it exposes, the longer it stays surfaced"); cospe bolas | pisão na cabeça; 3 pisões (ground pound = 2) | — (não documentada) | 15 bolas de fogo; Mega: 1 pisão; Mini: só ground pound; vencer em Mini abre o Mundo 4 | [MW-Mummipokey] |
| **Cheepskipper** (3) | sobe da água à direita, "hops across the bridge, and leaves on the left"; Cheep-Cheeps pulam junto | só fora da água; 3 pisões | — | — | [MW-Cheepskipper] |
| **Boss Goomba** (4) | Goomba comum que cresce; avança | 3 ground pounds (9 em Mini) via ? Switch que ergue plataformas verdes ou wall jump | — | Mega, shell dash, fogo | [MW-BossGoomba] |
| **Petey Piranha** (5) | dorme até Bowser Jr. pular nele; voa alto e cai como ground pound | "The floor is icy, so after his attack he slips and falls, leaving him open" | após 2 golpes "attacks by jumping from side to side" | Mini: ground pound; vencer em Mini abre o Mundo 7 | [MW-Petey] |
| **Monty Tank** (6) | tanque invencível com a cabeça escondida; torretas em várias alturas; Monty sai para jogar Bob-ombs | 3 pisões na cabeça exposta; Bob-ombs devolvidas | cada golpe "adds one level to the tank, making it taller and adding turrets"; gira e corre com alarme | Mega; ground pound = 2 | [MW-MontyTank] |
| **Lakithunder** (7) | mergulhos, Spinies e ovos que quicam, raios "that hit the ground beneath him" | 3 pisões "while he's swooping low" | — | — | [MW-Lakithunder] |
| **Dry Bowser** (8) / **Bowser 1,5× + Bowser Jr.** (8 final) | ver 3.4 | interruptor de crânio | — | — | [MW-DryBowser][MW-NSMB-W8BC] |

Todos DOCUMENTADO. Padrão NSMB DS: **a vulnerabilidade é pós-ataque** (Petey escorrega, Cheepskipper fora d'água, Lakithunder baixo, Monty fora do tanque) e o **Mini Mushroom** abre rotas alternativas pelo chefe — ideia reaproveitável como "vitória condicional" no Lume.

### 4.8 Outros chefes de torre: Boss Sumo Bro (NSMBU) e Big Chain Chomp (NSMBW)

- **Boss Sumo Bro (Screwtop Tower)**: Kamek amplia um Sumo Bro "to twice his size"; três plataformas e **quatro Note Blocks**; pisa uma vez, ou duas "after a brief change in stance"; faíscas que atravessam todo o chão e **tremor que atordoa quem está no chão**; cabeça com espinho → bater a plataforma **por baixo** (Note Blocks, Flying Squirrel, Peachette) para virá-lo de casco; 3 pisões na barriga ou 18 bolas de fogo (6 = 1 pisão) [MW-BossSumo] (DOCUMENTADO).
- **Big Chain Chomp**: é o castelo de Iggy em NSMBW (4.3).

---

## 5. Síntese analítica: o que a Nintendo faz de forma consistente

1. **Ritmo de três** (pisões ou rodadas) com **duração-alvo de 1–3 minutos**: limites de tempo dos níveis de chefe documentados — 400 s (SMB3 final), 500 s (NSMB 1-Castelo, Slide Lift Tower), 600 s (NSMBW 1-Tower), 700 s (NSMBU final) — incluem o percurso; os chefes ocupam uma fração (ESTIMADO).
2. **Vulnerabilidade pós-ataque** (recuperação) é a regra: Petey, Boss Sumo Bro, Boom Boom (tonto), Bowser SMB3 (pousa), Roy NSMB2 (parede), Ludwig/Bowser Jr. Wonder (quando para de girar). A janela é **criada pelo próprio ataque** do chefe.
3. **Retaliação após o golpe**: casco giratório (quase todos os Koopalings), fogo que cai (Bowser SMW/NSMBU), reconstrução (Kamek). Função: impedir *stun-lock* e dar ritmo; dura "alguns segundos" (DOCUMENTADO qualitativo).
4. **Escalada aditiva**: +1 projétil, +1 clone, +1 andar, +1 mão (Wonder), arena alterada; a velocidade sobe pouco e raramente é a única variável.
5. **Informação observável**: Bowser SMB3 mira a posição atual; Bowser SMB1 **não mira** (tabela); fogo teleguiado só aparece em clímaces (NSMB final, NSMBW W8-Airship, NSMB2) e é lento; Roy (NSMBW castelo) cai "directly above Mario" — mira a posição no instante do mergulho.
6. **Duplo caminho de dano** (pisão **ou** projétil), com equivalência de 4–6 projéteis por pisão (2.1).
7. **Erros baratos no clímax**: cair do Junior Clown Car não fere (NSMBU); fumaça de Wonder Bowser só empurra; Big Boo é inofensivo.
8. **Entrada e saída coreografadas**: porta fecha, reação do chefe, queda para fora da tela, chave/bandeira, destruição do castelo. Em NSMBU o chefe aparece no topo da torre e é derrubado no mapa.
9. **Exceções a evitar no Lume**: morte instantânea por esmagamento (Morton NSMBW castelo), relâmpago sem sinal documentado (Lakithunder), imprevisibilidade de temporizador (chamas SMB1), repetição do mesmo chefe quatro vezes (Bowser Jr. em Wonder — a variação vem só do Wonder Effect).

### 5.1 Fundamentos de justiça (teoria de design e tempo de reação)

| Fonte | Afirmação usada | Rótulo |
| --- | --- | --- |
| Stout, *Boss Battle Design and Structure* (2010) [GD-Stout2010] | chefe = "a test of skills the player has learned" + "a story with a beginning, middle, and end"; oito compassos: Build-Up, Intro, Business as Usual, Escalation, Midpoint, It's ON!, Kill, Victory; dar "enough time, space, and safety" para aprender | DOCUMENTADO (artigo técnico) |
| Stout, *Enemy Attacks and Telegraphing* (2015) [GD-Stout2015] | "We want to communicate exactly what the enemy is going to do so the player knows exactly what to do to avoid it"; "Before the attack, we need a small delay"; projéteis sinalizados por som + VFX de carga | DOCUMENTADO |
| Birkhead, *Boss Design – Tips From a Combat Designer* (2011) [GD-Birkhead] | "it is not enough to have clean reads. You must make sure that your reads do not overlap"; telegraphs ajudam só até ≈ **2 s**; janela de acerto ≥ "one full combo" + deslocamento; "prove to the player how awesome they are" | DOCUMENTADO |
| Kubodera, *Designing for Difficulty: Readability in ARPGs* (2022) [GD-Kubodera] | "Readability can be broken down into telegraphing (what happens before) and expectations (what happens after)"; "arguably has the largest impact on frustration"; chunking: "off-loading learned patterns"; espera proporcional à recompensa | DOCUMENTADO |
| Zhang, *Anatomy of an Enemy Attack in Dark Souls 3* (2022) [GD-Zhang] | fases Opening Pose → Attack Signal → Attack (hitbox ativa 2–4 q) → End Pose → Return; sinal + ataque "at least 340ms"; recuperação ≥ 170–240 ms; orçamento humano ≈ 100 ms perceber + 70 pensar + 70 agir + 60–100 ms de latência de entrada | DOCUMENTADO |
| Jain et al. 2015 [PMC-Jain]; BioNumbers/Kosinski [BioNum]; Wikipedia *Mental chronometry* [Wiki-RT] | tempo de reação simples ≈ **190 ms (visual)** e **160 ms (auditivo)** em adultos jovens (faixas 180–200 / 140–160 ms); estímulo auditivo chega ao cérebro em 8–10 ms vs 20–40 ms visual; reação de **escolha** é maior que a simples (Donders, Hick) | DOCUMENTADO |
| Iwata Asks, SMB 25.º aniversário [IA-SMB25] | Amano: "enemies with thorns that signal damage", "a visible platform ahead of a drop-off", "imagine the players playing the game as they make it"; Nishimura: imagens que permitam "understand immediately what the situation is"; Iwata: recompensar quem se esforça | OFICIAL |
| Entrevista NES Classic Mini Vol. 3 [NES-Mini] | Miyamoto: a visão diagonal foi abandonada porque "players need to tell whether Mario's feet have touched the ground" | OFICIAL |
| Ask the Developer Vol. 11 (Wonder) [ATD-W1][ATD-W2][ATD-W3] | Sato: "broaden the range of expressions that enemies had"; Hayashida: "Goombas have a biting expression the moment they do damage"; Tezuka: Koopas "turn around" ao morder; Kondo: "the entire course come alive like a musical"; Mouri: badges permitem "varying difficulty levels"; Tezuka: "use their heads, not just their skills" | OFICIAL |

**Orçamento de reação adotado (ESTIMADO, derivado das fontes acima)**: percepção/decisão de **escolha** ≈ 250 ms (acima do simples de 190 ms porque o jogador escolhe entre saltar, agachar e correr) + latência de entrada/exibição ≈ 60–100 ms + execução da esquiva (início do salto: 0 ms; andar 48 px a 220 px/s: 220 ms). Logo **≥ 400 ms** entre o início do telegraph e o primeiro quadro perigoso é o piso absoluto; valores confortáveis para aprendizado ficam em **600–900 ms**, e acima de **2 s** o sinal deixa de ajudar (Birkhead).

---

## 6. Proposta: os Cinco Guardiões do Lume

### 6.1 Princípios comuns (mapeados ao motor)

| Regra | Valor proposto | Origem na série | Onde vive no código |
| --- | --- | --- | --- |
| Golpes por guardião | **3** (Reino Verde, Deserto, Montanhas), **4** (Floresta), **4 + alavanca** (Fortaleza) | convenção dos três pisões; finais em rodadas (SMW, NSMBU, Wonder) | `BossDefinition.hp`; `Phase.enter_below` (1,0 / 0,67 / 0,34 para 1 golpe por fase) |
| Fases | 3 por guardião, cada uma com **conjunto de ataques diferente e um verbo novo** | Boom Boom SMB3; Kamek NSMBU; Wonder Bowser Jr. | `BossDefinition.validate()` já rejeita fases com ataques idênticos |
| Telegraph mínimo por mundo | 900 / 750 / 650 / 550 / 450 ms (piso duro 400 ms); pista sonora no 1.º quadro do telegraph; na fase 3 reduzir ≤ 15 %, nunca abaixo do piso | Bowser Jr. inspira (NSMBW); Morton lento; orçamento 5.1 | `Attack.telegraph`; elevar `MIN_TELEGRAPH` por mundo (hoje 0,30 s global) |
| Fase ativa | ≤ 1,2 s; hitbox ativa só na fase ativa | Zhang; Bowser SMB3 (um salto) | `Attack.active` |
| Janela de vulnerabilidade (recuperação + espera) | ≥ 1,6 s (M1) → ≥ 1,0 s (M5); ≥ tempo de corrida até o chefe (meia arena 350 px / 340 px/s = 1,03 s) + 0,38 s de subida do salto | Birkhead: "one full combo" + deslocamento; Boom Boom "a few seconds" | `Attack.recover` + `Phase.idle_time`; `vulnerable_states = {IDLE, RECOVER, HURT}` |
| Retaliação após golpe | estado `HURT` 0,65 s **imune** seguido de um ataque de retaliação telegrafado (giro/lamento) de 1,0–1,5 s | casco giratório dos Koopalings; fogo que cai (NSMBU) | adicionar `Phase.retaliation: Attack | None` executado ao sair de `HURT` |
| Perigos simultâneos | fase 1: 1; fases 2–3: 2 (+ perigo de arena com ciclo ≥ 4 s e aviso ≥ 1 s) | Wendy (anéis + inundação); Boss Sumo Bro (faíscas + salto) | contador em `GuardianBehavior.step` + teste |
| Informação usada pelo chefe | `player.x, y, vx, grounded`, distância — **lidos no 1.º quadro do telegraph e congelados**; sem leitura de entradas; teleguiado só na fase 3 com curvatura ≤ 120 px/s² | Bowser SMB3 mira posição; fogo azul lento (NSMB) | `Blackboard` (já expõe `player_distance`, `player_dx`); congelar alvo em `Attack.start` |
| Dano | todo ataque = 1 PV do jogador; **nunca** morte instantânea; contato com o corpo fere exceto por cima (pisão) | Lume atual; evitar Morton NSMBW | `contact_hurts`; `stompable` |
| Erro barato | cair da plataforma de arena → volta pela borda com 0,8 s de i-frames, sem perder PV, exceto lava (M5, fase 3) | NSMBU (cair do carro) | arena hooks |
| Entrada | câmera trava na arena (largura ≤ 960 px), porta/portão fecha, placa com o nome, reação do guardião 1,2–1,5 s | NSMBW/NSMBU portas; reações dos Koopalings | `Phase.intro_time` (hoje 0,8 s), evento `boss_intro` |
| Derrota | 2,0–2,5 s: tonto → ruge → cai para fora da tela → relíquia/chave aparece → bandeira acessível | Koopalings; NSMB DS chave; NSMBU torre tomba | `defeat_time` (hoje 1,6 s), evento `boss` |
| Pontuação | 5000 (coincide com o Bowser de SMB1) | [TMK-SMB][SMBDIS] | `score` |
| Checkpoint | sempre antes da arena | NSMBU final | dados de nível (já há checkpoints) |

Tamanhos propostos (ESTIMADO, referência Petey ≈ 6× Mario, Bowser gigante NSMB 1,5×, Boss Sumo Bro 2×): guardiões de **1,4× a 1,9× a altura do jogador crescido (46 px)** = 64–88 px, com fase gigante do M5 a 3× (138 px), cabendo sempre no viewport de 540 px.

### 6.2 Reino Verde — **Rolão, o Tatu-Canastra do Pomar** (1-3 "Guardião do Pomar")

- **Identidade**: tatu redondo e bonachão, casca em placas verde-musgo, olhos pequenos; **3 golpes** (hp 3, mantido). Personalidade: guarda zeloso que "pede desculpas" no fim (texto de HUD). Tamanho 64×58 px (1,4×).
- **Arena** (reaproveita a composição de 1-3: pomar, degraus, **ponte frágil**, arena aberta): 720 px de largura fechada por dois troncos; chão sólido com uma **ponte frágil** de 160 px no centro (quebra após 2 impactos de Rolão, reaparece após 6 s) e uma **árvore frutífera** cuja copa cobre 240 px à esquerda.
- **Fase 1 — "Parede"** (verbo: *atrair*): `charge` (investida rolando a 230 px/s): telegraph 900 ms (encolhe, treme, som de folhas), ativo até bater num tronco (≤ 2,2 s), **recuperação 1,8 s desenrolado e tonto** = vulnerável (Roy em NSMB2 e Boom Boom tonto). `leap` (quique curto, vy −430, vx 120) telegraph 800 ms, ativo 0,9 s, recuperação 0,8 s. Contramedida: pular a investida (altura da bola 58 px < 112 px de salto) ou subir nos degraus; descer para pisar quando ele bate na parede.
- **Fase 2 — "Ponte"** (verbo: *posicionar*): Rolão **freia antes dos troncos** (sem mais tontura na parede); novo ataque `pounce` (salto parabólico até a posição observada do jogador, sombra no chão): telegraph 750 ms, voo 0,9 s, recuperação 0,6 s. Se ele cai na **ponte frágil** ela cede no 2.º impacto e ele fica preso 2,0 s (vulnerável) — Bowser de SMB3 por atração. Investida mantida, mais lenta (200 px/s). Máx. 2 perigos.
- **Fase 3 — "Fruta"** (verbo: *sincronizar*): ponte desaparece (vão com rede abaixo: cair custa 0,8 s, não PV). Rolão rola **sem parar** (210 px/s, inverte nos troncos sem tontura) e cospe 1 semente parabólica a cada 3 s (telegraph 600 ms). A árvore sacode 800 ms antes de soltar **uma fruta na coluna x do jogador** (informação observável); a fruta cai a 420 px/s e, se atinge Rolão, ele desenrola tonto por 1,6 s. O jogador precisa ficar sob a copa e sair no último instante para que a fruta encontre a bola.
- **Reação a dano**: `HURT` 0,65 s → retaliação "sacode a casca" (anel de folhas de 40 px de raio, telegraph 500 ms, ativo 0,3 s). **Cinemáticas**: entra rolando pelo tronco direito e desenrola (1,3 s); derrota: gira como pião, desaba, pede desculpas, a relíquia brota da árvore.
- **Justiça**: investida é a pior esquiva — 900 ms de telegraph + distância mínima de 120 px (0,52 s a 230 px/s) = **1,4 s** de aviso ≫ 400 ms; o salto do jogador (0,76 s de voo) cobre a bola. Fruta: 800 ms de aviso + 0,25 s de queda; sair 48 px exige 0,22 s de caminhada. Tudo ≥ 2× o orçamento.

### 6.3 Deserto Dourado — **Oculus, a Sentinela de Arenito** (2-3 "Templo das Areias")

- **Identidade**: estátua-sentinela de pedra dourada com um único olho de vidro; flutua 4 px sobre pilares (origem do arquétipo `shooter` do Lume). **3 golpes** (hp atual 4 → 3; alternativa: 4 com dois golpes na fase 3). Personalidade: solene, fala em enigmas. 56×80 px (1,7×).
- **Arena**: templo fechado de 800 px; **3 pilares** (esq., centro, dir.) de 96 px de altura; **duas placas de pressão** no chão, nas extremidades. Pisar numa placa faz o pilar **mais próximo da placa** afundar por 2,0 s (Boss Sumo Bro: virar o chefe; Boss Goomba: interruptor que cria acesso).
- **Fase 1 — "Placa"** (verbo: *aprender o mecanismo*): Oculus fica no pilar central e dispara `sand_dart` (1 dardo a 240 px/s) **na altura do jogador no 1.º quadro do telegraph**, com 3 alturas discretas (chão, cintura, cabeça — SMB3: saltar ou agachar), telegraph 750 ms (o olho acende e emite nota), recuperação 0,9 s. Tocar a placa afunda o pilar central: 2,0 s de cabeça exposta.
- **Fase 2 — "Previsão"** (verbo: *antecipar*): `teleport` entre pilares: redemoinho de areia no pilar de destino durante 700 ms antes de aparecer (Kamek NSMBU, Pom Pom 3D World); rajadas de **2 dardos** (alturas diferentes, 300 ms de intervalo). A placa agora afunda **o pilar do lado dela**, então o jogador precisa ler o redemoinho e correr para a placa correspondente antes do fim da recuperação (0,9 s + 2,0 s).
- **Fase 3 — "Tempestade"** (verbo: *administrar*): `boulder` — uma rocha rola de um lado da arena a cada 5 s (estrondo + poeira 900 ms antes, velocidade 260 px/s, saltável). Oculus passa a **mirar a posição prevista** (`x + vx × 0,4 s`, só com dados observáveis), o que recompensa parar ou mudar de direção após o telegraph. As placas afundam o pilar mais devagar (1,2 s de atraso), exigindo pisar **antes** do teletransporte terminar. Máx. 2 perigos (dardo + rocha).
- **Reação a dano**: cai do pilar e rasteja de volta 1,2 s (imune) — retaliação: pulso de areia radial 60 px (telegraph 500 ms). **Cinemáticas**: olho acende no escuro, pilares sobem da areia (1,4 s); derrota: racha, areia escorre, revela o fragmento dourado.
- **Justiça**: dardo a 240 px/s de 250 px de distância = 1,04 s de voo + 750 ms de telegraph; o jogador escolhe agachar (altura 30 px) ou saltar; a altura é fixada no telegraph (sem perseguição). Rocha: 900 ms + 0,96 s de travessia até o centro.

### 6.4 Montanhas Geladas — **Brumo, a Morsa-Avalanche** (3-3 "Coração da Nevasca")

- **Identidade**: morsa colossal de pelagem azul-gelo, presas de cristal; move-se com impulsos pesados. **3 golpes** (hp atual 5 → 3). Personalidade: teimosa, dorme no início (Petey dorme até ser acordado). 92×76 px (1,65×).
- **Arena**: 760 px de **gelo** (atrito 180) com duas **ilhas de rocha** (atrito normal) de 96 px; **teto com estalactites**; dois canos nas paredes.
- **Fase 1 — "Tremor"** (verbo: *estar no ar*): `flipper_slam` — levanta as nadadeiras 700 ms (telegraph) e bate; **onda de choque** de 24 px de altura percorre o gelo a 320 px/s (< corrida de 340, saltável) e **atordoa 0,6 s quem está no chão** (Roy/Morton NSMBW, Boss Sumo Bro); recuperação 1,6 s com a cabeça baixa = vulnerável. `slide` — desliza 2 arenas/s… não: desliza a 280 px/s após agachar 800 ms; para nas paredes sem tontura.
- **Fase 2 — "Buraco"** (verbo: *atrair*): cada `flipper_slam` agora **quebra o gelo** no ponto do impacto (buraco de 64 px com água; cair = 0,8 s de lentidão, sem PV); se Brumo **desliza sobre um buraco**, cai e fica preso 2,0 s (vulnerável) — único modo de ferir nesta fase (SMB3: o chefe destrói o próprio apoio). O gelo recongela após 10 s. Estalactites caem **na coluna do jogador** com sombra 900 ms antes (1 perigo extra; mantém o teto de 2).
- **Fase 3 — "Cascos"** (verbo: *usar projétil*): Brumo sobe numa **laje central** elevada (fora do alcance do pisão) e alterna `flipper_slam` duplo (postura muda 500 ms antes do 2.º golpe — Boss Sumo Bro) e `snowball` (bola de neve rolante a 220 px/s). Dos canos saem **Cascudos** (os `shell` do Lume congelados) a cada 6 s; o jogador pisa e chuta o casco (360 px/s, já causa 2 de dano a inimigos no motor) contra a laje: Brumo escorrega, cai e fica tonto 1,8 s — Mechakoopas em SMW; `hitEnemy` do casco deslizante conta como golpe só nesse estado.
- **Reação a dano**: ruge e **rodopia** 1,2 s (imune, dano por contato) — casco giratório dos Koopalings. **Cinemáticas**: ronca sob a neve; o jogador se aproxima e ela desaba de um bloco de gelo (1,5 s); derrota: desliza para fora da tela de barriga e as estalactites caem sem perigo, revelando a relíquia.
- **Justiça**: onda de choque a 320 px/s a partir de 200 px = 0,62 s + 700 ms de telegraph = 1,3 s; saltar a tempo exige começar o salto antes da onda chegar (altura necessária 24 px alcançada em 0,04 s). Estalactite: 900 ms de sombra; andar 64 px = 0,29 s. Casco: o Cascudo surge sempre do cano **mais distante** do jogador para não nascer sobre ele.

### 6.5 Floresta Encantada — **Lumiá, a Guardiã das Copas** (4-3 "A Árvore Ancestral")

- **Identidade**: espírito-mariposa com asas de vitral e um **enxame de vagalumes** que a segue (o *tell* oficial). **4 golpes** (hp atual 6 → 4): 1 na fase 1, 1 na fase 2, 2 na fase 3. Personalidade: curiosa, brincalhona, protege a Árvore Ancestral por engano. 48×64 px (1,4×), mas com asas abertas 110 px.
- **Arena**: clareira de 880 px; chão + **três copas** (plataformas) a 96, 160 e 224 px de altura; luz ambiente controlável.
- **Fase 1 — "Mergulho"** (verbo: *tempo*): Lumiá paira sobre uma copa; `dive` — brilha 700 ms (telegraph) e mergulha a 520 px/s até a **posição observada**; pousa e descansa **1,6 s** (vulnerável) — Lakithunder/Petey; um **clone cinza sem vagalumes** aparece parado para introduzir o conceito (não ataca).
- **Fase 2 — "Identificação"** (verbo: *distinguir*): **2 clones** que também mergulham (telegraph 700 ms; ferem); pisar num clone o dissolve em esporos **inofensivos** (Ludwig NSMBU: clones somem ao pisar). Só a verdadeira tem vagalumes e é a **última a mergulhar** (Ludwig: "the real one drops last"). `spore_drift` — 3 esporos luminosos caem lentamente (90 px/s) de posições fixas.
- **Fase 3 — "Penumbra"** (verbo: *ler a luz*): a clareira escurece — todos viram **silhuetas** (Deep Magma Bog Palace); os vagalumes permanecem visíveis, tornando-se a única informação; as copas **balançam** (±32 px, período 4 s); mergulhos de 2 clones + verdadeira em sequência (intervalos de 600 ms); são necessários **2 golpes**. Após o 1.º golpe da fase a luz volta por 3 s (Boom Boom 3D World invisível/visível) e os clones trocam de lugar (Ludwig NSMBU).
- **Reação a dano**: explode em pó luminoso 1,0 s (imune) e reaparece em outra copa (Kamek: teletransporte). **Cinemáticas**: a árvore acende folha a folha; Lumiá desce "achando" que o jogador é intruso (1,5 s); derrota: percebe o erro, a árvore floresce e entrega a relíquia.
- **Justiça**: mergulho de 200 px a 520 px/s = 0,38 s + 700 ms = 1,08 s de aviso; o pouso **nunca** acontece sobre uma copa ocupada pelo jogador se ele se moveu ≥ 48 px após o telegraph (alvo congelado). Clones têm cor e **timbre** diferentes (Birkhead: leituras que não se sobrepõem). Pisar num clone não custa PV — só tempo.

### 6.6 Fortaleza Vulcânica — **Fornalho, o Forjador de Basalto** (5-3 "A Última Chama")

- **Identidade**: golem-ferreiro de basalto com veias de magma e um **martelo de obsidiana**; na fase final superaquece até o branco. **4 golpes + alavanca** (hp atual 7 → 5: a alavanca conta como o 5.º). Personalidade: orgulhoso artesão que forjou as correntes dos outros guardiões. 84×88 px (1,9×); fase 3 como onda de magma de 3× (138 px).
- **Arena**: **ponte de basalto** de 480 px sobre lava com uma **alavanca** no extremo direito (SMB1 machado / NSMB interruptor); além dela, 4 plataformas de basalto; mais 900 px de corredor para a fase 3 (exige alargar a arena de 5-3, hoje com patrulha de 340 px).
- **Fase 1 — "Ponte"** (verbo: *saltar o tremor*, 2 golpes): `hammer_slam` — martelo brilha 600 ms, bate (onda de choque 300 px/s pela ponte; atordoa 0,5 s no chão); o martelo **fica preso 1,2 s** = vulnerável. `magma_drops` — 2 gotas em arco para a posição observada (telegraph 650 ms, voo ≈ 1,1 s). A alavanca está bloqueada pelo corpo dele (passar por baixo quando ele salta — "contornar" — é possível mas só derruba a ponte **depois** dos 2 golpes, para preservar o ritmo de três).
- **Fase 2 — "Plataformas"** (verbo: *gerenciar o chão*, 2 golpes): ao 2.º golpe ele destrói a ponte (roteiro, 1,5 s). Na área de 4 plataformas, a **lava sobe e desce num ciclo de 6 s** (brilho + bolhas 1,2 s antes; sobe 48 px — Wendy inundação/Iggy lava); Fornalho salta de plataforma em plataforma (sombra 700 ms) e seu `hammer_slam` **afunda a plataforma** onde pousa por 4 s; ele fica 1,0 s vulnerável enquanto ela afunda (Bowser SMB3). Máx. 2 perigos (lava + gota ou salto).
- **Fase 3 — "A Última Chama"** (verbo: *correr*): após o 4.º golpe ele mergulha na lava e **ressurge como onda de magma** de 138 px que avança da esquerda a **270 px/s** (0,8× a corrida) — NSMBW/NSMB2 perseguição; plataformas emergem 1,0 s antes de serem necessárias (telegraph luminoso) e **nunca** exigem vão > 120 px (limite de `FASES.md`); garras de lava saem do fundo nos pontos marcados 800 ms antes. No fim do corredor, a **alavanca** derruba a comporta: a lava escoa e Fornalho se apaga. Cair na lava custa 1 PV e recoloca o jogador na última plataforma (checkpoint de fase).
- **Reação a dano**: encolhe e **gira as correntes** 1,3 s (raio 60 px, imune) — casco giratório; na fase 2 solta 3 fagulhas que caem (fogo que cai, SMW/NSMBU). **Cinemáticas**: martela uma barra incandescente de costas, vira-se e a atira na lava (1,5 s); derrota: a onda esfria em pedra com o rosto dele, a relíquia final flutua na comporta.
- **Justiça**: onda 300 px/s em 480 px de ponte ≈ 1,6 s para atravessar, telegraph 600 ms — jogador tem ≥ 0,9 s para o salto no pior caso; gotas de magma caem onde o jogador **estava** (alvo congelado), 0,65 + 1,1 s de aviso; lava sobe 48 px em 1,2 s de aviso (saltar basta); perseguição a 0,8× da corrida garante que correr sem parar vence com margem de 70 px/s; fase 3 sem leitura de entradas — a onda tem velocidade constante e as plataformas são determinísticas.

### 6.7 Resumo numérico da proposta (ESTIMADO, para `data/levels/*.json` e `BossDefinition`)

| Guardião | hp | Fases (verbo) | Telegraph min (ms) | Ativo máx (s) | Janela vulnerável (s) | Velocidade máx. chefe (px/s) | Perigos simultâneos |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Rolão (M1) | 3 | parede / ponte / fruta | 900 (fase 3: 600 na semente) | 2,2 (investida) | 1,8 / 2,0 / 1,6 | 230 | 1 / 2 / 2 |
| Oculus (M2) | 3 | placa / previsão / tempestade | 750 (700 redemoinho) | 0,3 (tiro) | 2,0 / 2,0 / 2,0 (pilar afundado) | — (teleporte) ; dardo 240 | 1 / 2 / 2 |
| Brumo (M3) | 3 | tremor / buraco / cascos | 700 (500 na 2.ª batida) | 1,0 | 1,6 / 2,0 / 1,8 | 280 (deslize); onda 320 | 1 / 2 / 2 |
| Lumiá (M4) | 4 | mergulho / identificação / penumbra | 700 | 0,4 (mergulho) | 1,6 / 1,6 / 1,4 | 520 (mergulho, vertical) | 1 / 2 / 2 |
| Fornalho (M5) | 5 | ponte / plataformas / corrida | 600 (1,2 s para a lava) | 1,6 (onda) | 1,2 / 1,0 / — | 300 (onda); 270 (perseguição) | 1 / 2 / 2 |

---

## 7. Implicações para o Lume (decisões e parâmetros ajustáveis)

1. **Um `BossDefinition` por guardião**, registrado com `register_guardian()` e referenciado no JSON por `kind` ("rolao", "oculus", "brumo", "lumia", "fornalho"); hoje `GuardianBehavior.__init__` sobrescreve `enemy.health` com `definition.hp` e ignora o `hp` do JSON (3–7) — remover o campo `hp` dos JSON de chefe ou fazê-lo apenas informativo.
2. **Piso de telegraph por mundo**: trocar `MIN_TELEGRAPH = 0.3` por tabela `{1: 0.9, 2: 0.75, 3: 0.65, 4: 0.55, 5: 0.45}` aplicada em `validate()`; piso absoluto 0,40 s; emitir `GameEvent("boss_telegraph", value=attack.name)` no 1.º quadro de `PREPARE_ATTACK` para a pista sonora (reação auditiva ~160 ms vs visual ~190 ms [PMC-Jain][BioNum]).
3. **Alvo congelado**: em `Attack.start`, copiar `player.x, player.y, player.vx` para o ataque; `tick` não relê o jogador (exceto ataques marcados `homing=True`, só na fase 3, com curvatura ≤ 120 px/s²).
4. **Retaliação**: novo campo `Phase.retaliation` executado ao sair de `HURT`; durante ela o chefe não é `vulnerable`; duração 1,0–1,5 s.
5. **Perigos simultâneos**: registrar projéteis/ondas/arena ativos por chefe e falhar o teste se exceder 1 (fase 1) ou 2 (fases 2–3).
6. **Ganchos de arena** (`start/tick/end` já existem em `Attack`): ponte frágil, placas e pilares, buracos no gelo, luz ambiente, lava cíclica, plataformas que afundam — modelados como entidades de nível com estado, acionadas pelos hooks; a perseguição do M5 exige `patrol` de ≈ 1 400 px em 5-3 e câmera que segue (hoje a arena tem 340 px).
7. **Intro/derrota**: `intro_time` 1,2–1,5 s com porta/portão (`platforms` do tipo `gate`) e trava de câmera; `defeat_time` 2,0–2,5 s; o cronômetro/pontuação de fase deve **parar no golpe final** (evitar o "Time's Up!" tardio de NSMBU).
8. **Equivalência de projétil** (se houver poder de disparo): 5–6 acertos = 1 golpe, com o chefe só aceitando dano de projétil nos mesmos estados vulneráveis.
9. **Tamanhos**: 64×58, 56×80, 92×76, 48×64 (asas 110), 84×88 (+ onda 138) px; hitbox da cabeça para pisão = 24 px superiores (regra atual de `stomp`), nunca espinhos no topo salvo quando a mecânica for "virar o chefe" (Boss Sumo Bro) — não usada nesta proposta.
10. **Conversões de referência** (SMB1 → Lume): 1 px/q = 60 px/s; × 1,875 = 112,5 px/s por px/q; a velocidade do Bowser original (2 px/q) equivale a 225 px/s, o que valida a faixa 200–280 px/s dos guardiões terrestres frente à corrida de 340 px/s do jogador.
11. **Timer**: manter o passo fixo de 1/120 s acumulando `Clock.tick()` em milissegundos ("Times in pygame-ce are represented in milliseconds") e usar `get_rawtime()` para medir carga sem contar a espera [PG-Time]; todos os tempos de `Attack` em segundos (float), convertidos de ms na tabela 6.7.
12. **Bot de justiça nos testes** (`tests/`): agente que, a cada ataque, espera 250 ms após `boss_telegraph` (+ 1 quadro de 1/60 s) e executa a contramedida documentada (saltar, agachar, andar para a ilha, chutar casco); a suíte roda cada guardião 30 vezes com sementes distintas e exige **0 PV perdido** e vitória em ≤ 180 s; variante "bot lento" (400 ms) deve vencer com ≤ 2 PV perdidos (critério de generosidade).
13. **Acessibilidade** (Wonder/NSMBU Deluxe): opção "sinalização estendida" que multiplica todos os telegraphs por 1,3 e reduz a velocidade dos chefes em 10 % (equivalente ao Luigi Block/Nabbit sem alterar o chefe).

### 7.1 Tabela de mecânicas emprestadas e sua origem (para nunca misturar sem citar)

| Mecânica no Lume | Origem (título) | Rótulo |
| --- | --- | --- |
| Investida que atordoa na parede (Rolão F1) | Roy Koopa, New Super Mario Bros. 2 [MW-Roy] | DOCUMENTADO |
| Chefe destrói o próprio apoio ao cair (Rolão F2, Fornalho F2) | Bowser, Super Mario Bros. 3 [MW-SMB3Castle][MW-BrickFloor] | DOCUMENTADO |
| Perigo ambiental vira arma (fruta, casco) | Mechakoopas, Super Mario World [MW-FrontDoor]; Bob-ombs/Targeting Teds, NSMBU [MW-Boarding][MW-Cannonship] | DOCUMENTADO |
| Projétil em três alturas; saltar ou agachar (Oculus) | Bowser, SMB1/SMB3 [SMBDIS][MW-SMB3Castle] | DOCUMENTADO |
| Teletransporte sinalizado e arena reescrita (Oculus F2) | Kamek, NSMBU [MW-SlideLift]; Pom Pom, 3D World [MW-PomPom] | DOCUMENTADO |
| Pisão com onda de choque que atordoa no chão (Brumo, Fornalho) | Roy/Morton, NSMBW [MW-Roy][MW-Morton]; Boss Sumo Bro, NSMBU [MW-BossSumo] | DOCUMENTADO |
| Chefe dorme até ser acordado; escorrega após atacar (Brumo) | Petey Piranha, NSMB DS [MW-Petey] | DOCUMENTADO |
| Mergulho até a posição do jogador e descanso (Lumiá) | Lakithunder, NSMB DS [MW-Lakithunder]; Petey [MW-Petey] | DOCUMENTADO |
| Clones com *tell* observável (Lumiá) | Ludwig, NSMBU [MW-Ludwig]; Pom Pom, 3D World/SMM2 [MW-PomPom] | DOCUMENTADO |
| Silhuetas/penumbra (Lumiá F3) | Deep Magma Bog Palace, Wonder [MW-DeepMagma] | DOCUMENTADO |
| Ponte + alavanca; passar por baixo (Fornalho) | machado de SMB1 [MW-Axe]; interruptor de NSMB/NSMBW/NSMBU [MW-NSMB-W1C][MW-NSMBW-W8C][MW-NSMBU-Final] | DOCUMENTADO |
| Lava/água que sobe em ciclo sinalizado (Fornalho F2) | Wendy, NSMBW castelo [MW-Wendy]; Iggy, NSMBU [MW-Iggy] | DOCUMENTADO |
| Perseguição final por um gigante lento (Fornalho F3) | Super Bowser, NSMBW/NSMB2 [MW-NSMBW-W8C][MW-GiantBowser] | DOCUMENTADO |
| Erro barato no clímax (cair sem perder PV) | cair do Junior Clown Car, NSMBU [MW-GiantBowser] | DOCUMENTADO |
| Retaliação imune após o golpe | casco giratório dos Koopalings [MW-Larry] etc.; fogo que cai [MW-GiantBowser] | DOCUMENTADO |

---

## 8. Lacunas e incertezas

1. **Nenhum valor numérico oficial** de velocidade, tempo de telegraph ou janela de vulnerabilidade foi encontrado para qualquer chefe; todos os números da seção 6 são ESTIMADOS a partir de princípios (5.1) e das constantes do Lume.
2. **SMB1**: a conversão do impulso vertical de salto do Bowser ($FE) e os valores de `FlameTimerData` não foram lidos; a velocidade da chama também não. O Data Crystal (mapa de RAM) retornou 403.
3. **SMB3**: número de camadas de tijolos por versão de sala ("two or three") e a cadência exata "duas ou três bolas de fogo" divergem entre a página de nível e a de história; o guia Thonky ("two bricks beneath him") é comunitário.
4. **Boom Boom em NSMBU**: a wiki não dá a contagem de pisões (assumido 3 por convenção, OBSERVADO).
5. **Bowser Jr. em NSMBU (Cannonship)**: conflito entre "3/4" (página do personagem) e "6/8" (página do nível) Torpedo Teds por rajada.
6. **Wonder**: as páginas dos palácios não afirmam explicitamente a contagem de golpes (inferidos 4); a ordem dos Wonder Effects de Sunbaked Desert e Deep Magma Bog diverge entre a página "Wonder Effect" e as páginas dos níveis.
7. **Lakithunder**: nenhum sinal prévio do relâmpago documentado; mantido como exemplo a *não* seguir.
8. **Duração da perseguição** de NSMBW e **tempo de retaliação** dos Koopalings ("a few seconds") não quantificados.
9. **Fontes indisponíveis na coleta** (3/11/2026): Iwata Asks NSMBW (iwataasks.nintendo.com, 503), revisão de Kosinski (Clemson, 503), artigo original de Kubodera no Medium (403; usada a republicação em gamedeveloper.com), estatísticas de Human Benchmark (página dinâmica). A entrevista de Wonder parte 4 não foi lida.
10. **Reação humana**: os 190/160 ms são médias de adultos jovens em laboratório; crianças e jogadores novatos reagem mais devagar (variação com idade, [Wiki-RT]); por isso o piso de 400 ms e a opção de sinalização estendida.
11. **Implementação**: a perseguição do M5 e os ganchos de arena exigem mudanças de nível (5-3) e de câmera ainda não existentes; o bot de justiça depende de um controlador programável nos testes.
12. **Pom Pom e Boom Boom 3D**: só aparecem em 2D no estilo 3D World de Super Mario Maker 2; usados apenas como referência de clones/tontura.

---

## 9. Fontes

| ID | Tipo | Título | URL |
| --- | --- | --- | --- |
| [IA-SMB25] | oficial | Iwata Asks — Super Mario Bros. 25th Anniversary, Vol. 4, 6 "Playing and Making Super Mario Bros." | https://www.nintendo.com/en-gb/Iwata-Asks/Super-Mario-Bros-25th-Anniversary/Vol-4-The-Developers-2-/6-Playing-and-Making-Super-Mario-Bros-/6-Playing-and-Making-Super-Mario-Bros-209904.html |
| [NES-Mini] | oficial | Nintendo Classic Mini: NES special interview — Volume 3: Super Mario Bros. | https://www.nintendo.com/en-gb/News/2016/November/Nintendo-Classic-Mini-NES-special-interview-Volume-3-Super-Mario-Bros-1157085.html |
| [ATD-W1] | oficial | Ask the Developer Vol. 11, Super Mario Bros. Wonder — Part 1 | https://www.nintendo.com/ph/interview/aqmx/index.html |
| [ATD-W2] | oficial | Ask the Developer Vol. 11, Super Mario Bros. Wonder — Part 2 | https://www.nintendo.com/us/whatsnew/ask-the-developer-vol-11-super-mario-bros-wonder-part-2/ |
| [ATD-W3] | oficial | Ask the Developer Vol. 11, Super Mario Bros. Wonder — Part 3 | https://www.nintendo.com/us/whatsnew/ask-the-developer-vol-11-super-mario-bros-wonder-part-3/ |
| [MW-Bowser] | docs | Super Mario Wiki — Bowser | https://www.mariowiki.com/Bowser |
| [MW-HistBowser] | docs | Super Mario Wiki — History of Bowser | https://www.mariowiki.com/History_of_Bowser |
| [MW-FakeBowser] | docs | Super Mario Wiki — Fake Bowser | https://www.mariowiki.com/Fake_Bowser |
| [MW-W84] | docs | Super Mario Wiki — World 8-4 (Super Mario Bros.) | https://www.mariowiki.com/World_8-4_(Super_Mario_Bros.) |
| [MW-Axe] | docs | Super Mario Wiki — Axe | https://www.mariowiki.com/Axe |
| [MW-Flame] | docs | Super Mario Wiki — Bowser's Flame | https://www.mariowiki.com/Bowser%27s_Flame |
| [MW-BrickFloor] | docs | Super Mario Wiki — Brick floor | https://www.mariowiki.com/Brick_floor |
| [MW-SMB3Castle] | docs | Super Mario Wiki — World 8-Bowser's Castle (Super Mario Bros. 3) | https://www.mariowiki.com/World_8-Bowser%27s_Castle_(Super_Mario_Bros._3) |
| [Thonky-SMB3] | comunitário | Thonky — Super Mario Bros. 3: World 8 Bowser's Castle | https://thonky.com/super-mario-bros-3/world-8-bowsers-castle |
| [MW-FrontDoor] | docs | Super Mario Wiki — Front Door | https://www.mariowiki.com/Front_Door |
| [MW-ClownCar] | docs | Super Mario Wiki — Koopa Clown Car | https://www.mariowiki.com/Koopa_Clown_Car |
| [MW-NSMB-W1C] | docs | Super Mario Wiki — World 1-Castle (New Super Mario Bros.) | https://www.mariowiki.com/World_1-Castle_(New_Super_Mario_Bros.) |
| [MW-NSMB-W8BC] | docs | Super Mario Wiki — World 8-Bowser's Castle (New Super Mario Bros.) | https://www.mariowiki.com/World_8-Bowser%27s_Castle_(New_Super_Mario_Bros.) |
| [MW-DryBowser] | docs | Super Mario Wiki — Dry Bowser | https://www.mariowiki.com/Dry_Bowser |
| [MW-GiantBowser] | docs | Super Mario Wiki — Giant Bowser | https://www.mariowiki.com/Giant_Bowser |
| [MW-NSMBW-W8C] | docs | Super Mario Wiki — World 8-Bowser's Castle (New Super Mario Bros. Wii) | https://www.mariowiki.com/World_8-Bowser%27s_Castle_(New_Super_Mario_Bros._Wii) |
| [MW-NSMBU-Final] | docs | Super Mario Wiki — The Final Battle (New Super Mario Bros. U) | https://www.mariowiki.com/The_Final_Battle_(New_Super_Mario_Bros._U) |
| [MW-Wonder-Final] | docs | Super Mario Wiki — The Final Battle! Bowser's Rage Stage | https://www.mariowiki.com/The_Final_Battle!_Bowser%27s_Rage_Stage |
| [MW-WonderBowser] | docs | Super Mario Wiki — Wonder Bowser | https://www.mariowiki.com/Wonder_Bowser |
| [MW-CastleBowser] | docs | Super Mario Wiki — Castle Bowser | https://www.mariowiki.com/Castle_Bowser |
| [MW-BowserJr] | docs | Super Mario Wiki — Bowser Jr. | https://www.mariowiki.com/Bowser_Jr. |
| [MW-NSMBW-W4A] | docs | Super Mario Wiki — World 4-Airship (New Super Mario Bros. Wii) | https://www.mariowiki.com/World_4-Airship_(New_Super_Mario_Bros._Wii) |
| [MW-NSMBW-W6A] | docs | Super Mario Wiki — World 6-Airship (New Super Mario Bros. Wii) | https://www.mariowiki.com/World_6-Airship_(New_Super_Mario_Bros._Wii) |
| [MW-NSMBW-W8A] | docs | Super Mario Wiki — World 8-Airship (New Super Mario Bros. Wii) | https://www.mariowiki.com/World_8-Airship_(New_Super_Mario_Bros._Wii) |
| [MW-Cannonship] | docs | Super Mario Wiki — The Mighty Cannonship | https://www.mariowiki.com/The_Mighty_Cannonship |
| [MW-Boarding] | docs | Super Mario Wiki — Boarding the Airship | https://www.mariowiki.com/Boarding_the_Airship |
| [MW-WonderJr] | docs | Super Mario Wiki — Wonder Bowser Jr. | https://www.mariowiki.com/Wonder_Bowser_Jr. |
| [MW-PipeRock] | docs | Super Mario Wiki — Pipe-Rock Plateau Palace | https://www.mariowiki.com/Pipe-Rock_Plateau_Palace |
| [MW-FluffPuff] | docs | Super Mario Wiki — Fluff-Puff Peaks Palace | https://www.mariowiki.com/Fluff-Puff_Peaks_Palace |
| [MW-Sunbaked] | docs | Super Mario Wiki — Sunbaked Desert Palace | https://www.mariowiki.com/Sunbaked_Desert_Palace |
| [MW-DeepMagma] | docs | Super Mario Wiki — Deep Magma Bog Palace | https://www.mariowiki.com/Deep_Magma_Bog_Palace |
| [MW-Kamek] | docs | Super Mario Wiki — Kamek | https://www.mariowiki.com/Kamek |
| [MW-SlideLift] | docs | Super Mario Wiki — Slide Lift Tower | https://www.mariowiki.com/Slide_Lift_Tower |
| [MW-Koopalings] | docs | Super Mario Wiki — Koopalings | https://www.mariowiki.com/Koopalings |
| [MW-Larry] | docs | Super Mario Wiki — Larry Koopa | https://www.mariowiki.com/Larry_Koopa |
| [MW-Morton] | docs | Super Mario Wiki — Morton Koopa Jr. | https://www.mariowiki.com/Morton_Koopa_Jr. |
| [MW-Wendy] | docs | Super Mario Wiki — Wendy O. Koopa | https://www.mariowiki.com/Wendy_O._Koopa |
| [MW-Iggy] | docs | Super Mario Wiki — Iggy Koopa | https://www.mariowiki.com/Iggy_Koopa |
| [MW-Roy] | docs | Super Mario Wiki — Roy Koopa | https://www.mariowiki.com/Roy_Koopa |
| [MW-Lemmy] | docs | Super Mario Wiki — Lemmy Koopa | https://www.mariowiki.com/Lemmy_Koopa |
| [MW-Ludwig] | docs | Super Mario Wiki — Ludwig von Koopa | https://www.mariowiki.com/Ludwig_von_Koopa |
| [MW-NSMBW-W1T] | docs | Super Mario Wiki — World 1-Tower (New Super Mario Bros. Wii) | https://www.mariowiki.com/World_1-Tower_(New_Super_Mario_Bros._Wii) |
| [MW-BoomBoom] | docs | Super Mario Wiki — Boom Boom | https://www.mariowiki.com/Boom_Boom |
| [MW-PomPom] | docs | Super Mario Wiki — Pom Pom | https://www.mariowiki.com/Pom_Pom |
| [MW-Reznor] | docs | Super Mario Wiki — Reznor | https://www.mariowiki.com/Reznor |
| [MW-BigBoo] | docs | Super Mario Wiki — Big Boo | https://www.mariowiki.com/Big_Boo |
| [MW-DonutSecretHouse] | docs | Super Mario Wiki — Donut Secret House | https://www.mariowiki.com/Donut_Secret_House |
| [MW-Petey] | docs | Super Mario Wiki — Petey Piranha | https://www.mariowiki.com/Petey_Piranha |
| [MW-Mummipokey] | docs | Super Mario Wiki — Mummipokey | https://www.mariowiki.com/Mummipokey |
| [MW-MontyTank] | docs | Super Mario Wiki — Monty Tank | https://www.mariowiki.com/Monty_Tank |
| [MW-Cheepskipper] | docs | Super Mario Wiki — Cheepskipper | https://www.mariowiki.com/Cheepskipper |
| [MW-BossGoomba] | docs | Super Mario Wiki — Boss Goomba | https://www.mariowiki.com/Boss_Goomba |
| [MW-Lakithunder] | docs | Super Mario Wiki — Lakithunder | https://www.mariowiki.com/Lakithunder |
| [MW-BossSumo] | docs | Super Mario Wiki — Boss Sumo Bro | https://www.mariowiki.com/Boss_Sumo_Bro |
| [MW-Boss] | docs | Super Mario Wiki — Boss | https://www.mariowiki.com/Boss |
| [TMK-SMB] | docs | The Mushroom Kingdom — Mariopedia: Super Mario Bros. (lista completa) | https://themushroomkingdom.net/mariopedia/game/smb/full |
| [TASV-SMB] | técnico | TASVideos — Game Resources: NES Super Mario Bros. | https://tasvideos.org/GameResources/NES/SuperMarioBros |
| [SMBDIS] | técnico (documentação comunitária derivada de desmontagem) | doppelganger — Super Mario Bros. comprehensive disassembly (smbdis.asm, gist) | https://gist.github.com/1wErt3r/4048722 |
| [6502-SMB] | técnico | 6502disassembly.com — Super Mario Bros. (porte SourceGen da mesma desmontagem) | https://6502disassembly.com/nes-smb/ |
| [GD-Stout2010] | técnico | Mike Stout — Boss Battle Design and Structure (Game Developer) | https://www.gamedeveloper.com/design/boss-battle-design-and-structure |
| [GD-Stout2015] | técnico | Mike Stout — Enemy Attacks and Telegraphing (Game Developer) | https://www.gamedeveloper.com/design/enemy-attacks-and-telegraphing |
| [GD-Birkhead] | técnico | Mike Birkhead — Opinion: Boss Design – Tips From A Combat Designer (Game Developer) | https://www.gamedeveloper.com/design/opinion-boss-design---tips-from-a-combat-designer |
| [GD-Kubodera] | técnico | Alex Kubodera — Designing for Difficulty: Readability in ARPGs (Game Developer) | https://www.gamedeveloper.com/game-platforms/designing-for-difficulty-readability-in-arpgs |
| [GD-Zhang] | técnico | Jerry Zhang — Anatomy of an Enemy Attack in Dark Souls 3 (Game Developer) | https://www.gamedeveloper.com/game-platforms/anatomy-of-an-enemy-attack-in-dark-souls-3 |
| [PMC-Jain] | técnico | Jain, Bansal, Kumar, Singh (2015) — A comparative study of visual and auditory reaction times… (Int J Appl Basic Med Res) | https://pmc.ncbi.nlm.nih.gov/articles/PMC4456887 |
| [BioNum] | técnico | BioNumbers — Reaction times to sound, light and touch (citando Kosinski, Clemson) | https://bionumbers.hms.harvard.edu/bionumber.aspx?id=110800 |
| [Wiki-RT] | docs | Wikipedia — Mental chronometry | https://en.wikipedia.org/wiki/Mental_chronometry |
| [PG-Time] | docs | pygame-ce — pygame.time | https://pyga.me/docs/ref/time.html |
| [IA-NSMBW] | oficial (indisponível: 503 na coleta) | Iwata Asks — New Super Mario Bros. Wii, Vol. 2 | https://iwataasks.nintendo.com/interviews/wii/nsmb/1/5 |
| [Kosinski] | técnico (indisponível: 503 na coleta) | Robert J. Kosinski — A Literature Review on Reaction Time (Clemson) | https://www.cognaction.org/cogs105/readings/clemson.rt.pdf |
