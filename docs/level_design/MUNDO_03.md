# Mundo 3 — Costa dos Corais (`coral_coast`)

> Praias, marés e recifes submersos. Bioma `coast`, cor de mapa `#3fb7c4`, mundo novo.
> Plano geral: [`PLANEJAMENTO_60_FASES.md`](PLANEJAMENTO_60_FASES.md) · dados: [`campaign_plan.json`](../../lume/data/plan/campaign_plan.json).

## Identidade

**Reviravolta do mundo.** A água deixa de matar: nadar vira o movimento principal, primeiro raso, depois em correntes, num labirinto e num naufrágio que alaga.

**Paleta**
- turquesa #3fb7c4 e azul-profundo #1d4e7a
- areia clara #f2dfb4 e rochas de recife #8f7f74
- coral #ff7f6b, coral-laranja #ffa94d (marca do caminho certo) e violeta #9a6ad6
- verde-alga #4f9a6a e espuma #ffffff
- madeira de naufrágio #7a5a3a e latão #c9a35b

**Marcos visuais**
- píeres de madeira sobre a lagoa
- piscinas naturais em degraus de rocha
- farol listrado vermelho e branco no recife
- bosque de algas e paredes de coral
- galeão naufragado adernado

**Ambiência.** Sol de praia e espuma nas ondas (L1–L2), ressaca ao entardecer no farol (L3), azul profundo com raios de luz descendo (L4), coral bioluminescente no labirinto (L5) e penumbra esverdeada no galeão (L6). Bolhas, peixes de cardume decorativos e gaivotas.

**Física.** Zonas swim: gravidade 420 u/s², impulso de nado 230 u/s, velocidade máxima 150 u/s, saída da água com 0,85 do salto. Zonas current: empurrão horizontal/vertical com period/duty (marcado por boias com fitas). Quedas fora da área ainda matam; a água em si não. Vãos obrigatórios ≤ 150 u fora d'água.

## Progressão das mecânicas

| Fase | Id | Papel | Foco | Dif. | Ideia própria |
| --- | --- | --- | --- | ---: | --- |
| 3-1 | `shell_beach` | apresentação | nado raso e fundo com saída fácil (a lagoa de sunken_oasis foi só a prévia), píeres semissólidos, peixe que salta | 3 | a gruta das conchas obriga o primeiro mergulho completo |
| 3-2 | `tide_pools` | exploração | piscinas em alturas diferentes, baiacu que infla e moreia que emerge | 3 | a moreia não sai se Lume encostar na toca: a regra vira ferramenta |
| 3-3 | `lighthouse_reef` | desafio de movimento | escalada vertical: boias balançando, conchas-mola e ondas periódicas | 4 | a ressaca ritmada alaga o passadiço e faz as boias subirem |
| 3-4 | `current_depths` | mecânica especial | correntes com período e direção (mecânica especial) e água-viva | 4 | a maré reversa troca a direção da corrente no meio do caminho |
| 3-5 | `coral_maze` | desafio avançado | labirinto submerso com perseguidor (polvo) e válvulas de corrente | 5 | o labirinto desce e a saída fica no alto: fuga ascendente com dois polvos |
| 3-6 | `sunken_galleon` | fortaleza e chefe | naufrágio de compartimentos ar/água e chefe que alaga a arena | 5 | o mastro tombado vira ponte e o casco racha no meio da luta |

## Distribuição de inimigos

★ = estreia da espécie (igual a `introduced_in`); ● = permitida; ◆ = permitida só em sub-área do bioma indicado.

| Espécie | 3-1 | 3-2 | 3-3 | 3-4 | 3-5 | 3-6 |
| --- | :---: | :---: | :---: | :---: | :---: | :---: |
| Caramujo-de-Casca (`caramujo`) | ● | ● | ● |  | ● | ● |
| Caranguejo-Pinça (`caranguejo_pinca`) | ★ | ● | ● | ● | ● | ● |
| Peixe-Saltador (`peixe_saltador`) | ★ | ● | ● | ● | ● | ● |
| Baiacu-Espinho (`baiacu_espinho`) |  | ★ | ● | ● | ● | ● |
| Moreia-da-Toca (`moreia_toca`) |  | ★ | ● | ● | ● | ● |
| Água-Viva Elétrica (`agua_viva`) |  |  |  | ★ | ● | ● |
| Polvo-Tinteiro (`polvo_tinteiro`) |  |  |  |  | ★ | ◆ underwater |
| Ermitão-Âncora (chefe planejado) (`boss:ermitao_ancora`) |  |  |  |  |  | chefe |

Quantidade planejada de inimigos (sem chefes): 3-1: 8–12 · 3-2: 12–16 · 3-3: 12–16 · 3-4: 14–18 · 3-5: 16–22 · 3-6: 18–24.

## Chefe do mundo — Ermitão-Âncora (`ermitao_ancora`, planejado)

- **Fase:** `sunken_galleon`
- **Arena:** Porão de proa do galeão (sub-área bow_hold, 1100×1620): metade inferior alagada (swim a partir de y420 da arena), três conveses de tábuas semissólidas, uma faixa de piso de metal (onde a pinça não prende), sino do navio pendurado no centro e a âncora presa à corrente.
- **Ataques:**
  - Golpe de pinça: ergue a pinça (aviso de 0,5 s) e martela o convés, gerando onda de choque que corre pelas tábuas (saltar)
  - Âncora pendular: balança a âncora na corrente em arco sobre o porão (perigo móvel)
  - Jato de corrente: suga água e expele 3 s de corrente (força 160) que puxa Lume nadando para as pinças
  - Casco rodopiante (fase 2): recolhe-se na popa e quica entre as paredes como um casco gigante, chamando peixes-saltadores
- **Janela de vulnerabilidade:** Quando o golpe de pinça acerta tábuas de madeira, a pinça fica presa por 1,5 s (madeira lascada brilha): pisão nos olhos-pedúnculo. Se martelar o piso de metal, não prende — Lume precisa atraí-lo para as tábuas. Fogo não funciona contra a concha.
- **Fases e mudança de fase:** Fase 1 (5–4 PV): porão com ar, água até y420; golpes, âncora e jato. Fase 2 (3–1 PV): o casco racha, a água sobe até y260 (luta quase toda nadando), o casco rodopiante entra no ciclo e o jato fica mais forte.
- **Derrota (animação):** O ermitão larga a popa do galeão, troca por uma concha de búzio pequena e foge envergonhado; o galeão se ergue com a maré e a lanterna de popa acende — o farol da fronteira 3.
- **Relação com a mecânica do mundo:** Nado, correntes (o jato) e maré (a água que sobe na fase 2), além dos conveses semissólidos do galeão.
- **Implementação:** chefe planejado — nova família de comportamento, entrada `boss: true` no registro (ver seção 6.2 do plano geral), eventos `boss_arena`/`camera_lock` e os requisitos listados na fase `sunken_galleon`.

**Fase 3 sem minichefe:** `lighthouse_reef` termina num teste de movimento próprio (ver resumo abaixo).

## NPC do mundo — Mestre Búzio, pescador aposentado e guardião das boias

**Função.** Ensina a nadar e a ler correntes: amarra fitas nas boias (a fita aponta a direção e estica com a força) e avisa onde há bolsões de ar. Aparece no primeiro checkpoint de cada fase do mundo; no galeão, empresta a lanterna de popa que marca o checkpoint da antessala.

**Falas-guia**
- “Na água, toque o salto para nadar. Segurar não adianta: o mar gosta de ritmo.”
- “Fita esticada é correnteza forte. Fita mole, pode passar.”
- “Coral laranja aponta a saída do labirinto.”
- “O ermitão só larga a pinça quando ela fica presa na madeira.”

**Implementação.** Prop animado (barco a remo ou píer) + evento message no checkpoint; fitas das boias como decor sincronizado com Game.zone_active. Não requer motor novo.

## Resumo por fase

### 3-1 · Praia das Conchas (`shell_beach`) — nova

- **Ideia própria:** a gruta das conchas obriga o primeiro mergulho completo.
- **Objetivo:** Apresentar o nado com segurança (piscina rasa → lagoa funda → gruta curta), os píeres semissólidos e os dois primeiros habitantes da costa: o caranguejo de pinças periódicas e o peixe que salta da água.
- **Mecânica principal:** Nado (zonas swim) introduzido sem risco: toque no salto para impulsionar, saída da água com 0,85 do salto
- **Dificuldade / duração / tamanho:** 3/10 · 80–160 s · 4600×1240 u · 2 checkpoint(s)
- **Estreias:** Caranguejo-Pinça, Peixe-Saltador
- **Relíquias:** relíquia relic_pearl — pista: Bolhas sobem de baixo de uma rocha no fundo da lagoa; brilho perolado; relíquia relic_tower e coração — pista: Caixotes empilhados até a torre do salva-vidas; bandeira vermelha tremulando no alto; relíquia relic_grotto e estrela — pista: Manilha de pedra na areia com água borbulhando e estrela-do-mar desenhada
- **Requisitos de motor:** nenhum
- Seção completa: [`PLANEJAMENTO_60_FASES.md`](PLANEJAMENTO_60_FASES.md#3-1--praia-das-conchas-shell_beach)

### 3-2 · Piscinas da Maré (`tide_pools`) — nova

- **Ideia própria:** a moreia não sai se Lume encostar na toca: a regra vira ferramenta.
- **Objetivo:** Explorar piscinas naturais em alturas diferentes, ligadas por túneis e quedas d'água, com rotas por cima das rochas ou por dentro da água; apresentar o baiacu que infla e a moreia que emerge da toca.
- **Mecânica principal:** Piscinas em alturas diferentes ligadas por túneis submersos e quedas d'água (current force_y +)
- **Dificuldade / duração / tamanho:** 3/10 · 90–180 s · 5000×1240 u · 2 checkpoint(s)
- **Estreias:** Baiacu-Espinho, Moreia-da-Toca
- **Relíquias:** relíquia relic_starfish e coração — pista: Estrela-do-mar dourada no topo de um pilar de rocha; pedras soltas em degraus; relíquia relic_tide e estrela — pista: Marca de maré (faixa de cracas) na entrada de uma gruta e água pingando do teto; relíquia relic_waterfall — pista: Moedas aparecem e somem atrás da queda d'água central; o respingo desvia num ponto vazio
- **Requisitos de motor:** rising_lava (extensão): a subida única de um perigo por evento já existe (hazard/to/speed, gatilho por x); faltam ciclos de subida e descida, gatilho por altura, tempo ou chefe, aviso sonoro, etapas com pausa, reposição no checkpoint e a variante com zona swim (maré) — só na sala opcional; a fase é jogável sem
- Seção completa: [`PLANEJAMENTO_60_FASES.md`](PLANEJAMENTO_60_FASES.md#3-2--piscinas-da-maré-tide_pools)

### 3-3 · Recife do Farol (`lighthouse_reef`) — nova

- **Ideia própria:** a ressaca ritmada alaga o passadiço e faz as boias subirem.
- **Objetivo:** Desafio de movimento vertical: subir do recife ao topo do farol durante a ressaca, com boias que balançam, conchas-mola, ondas periódicas e peixes saltando.
- **Mecânica principal:** Escalada vertical com boias balançando (moving axis y) e conchas-mola (spring)
- **Dificuldade / duração / tamanho:** 4/10 · 100–200 s · 4800×2700 u · 2 checkpoint(s)
- **Estreias:** —
- **Relíquias:** relíquia relic_nest — pista: Gaivota circulando sobre uma saliência externa; penas caindo marcam as molas; relíquia relic_cistern e estrela — pista: Ralo de bronze na base do farol com água correndo para dentro; relíquia relic_buoy — pista: Uma boia sem corda balança sob um ponto onde moedas cintilam no ar
- **Requisitos de motor:** nenhum
- Seção completa: [`PLANEJAMENTO_60_FASES.md`](PLANEJAMENTO_60_FASES.md#3-3--recife-do-farol-lighthouse_reef)

### 3-4 · Correntes Profundas (`current_depths`) — nova

- **Ideia própria:** a maré reversa troca a direção da corrente no meio do caminho.
- **Objetivo:** Mecânica especial da Costa dos Corais: nadar no mar aberto usando e evitando correntes com período e direção, e conhecer a Água-Viva Elétrica, que não pode ser pisada.
- **Mecânica principal:** Correntes subaquáticas (zonas current) com força, período e duty; direção reversível por zonas em fase oposta
- **Dificuldade / duração / tamanho:** 4/10 · 110–210 s · 5400×1620 u · 2 checkpoint(s)
- **Estreias:** Água-Viva Elétrica
- **Relíquias:** relíquia relic_trumpet — pista: Concha-trompa brilhando num bolsão lateral, contra uma corrente fraca marcada por fita mole; relíquia relic_kelp e estrela — pista: Peixes de cardume entram na cortina de algas e não saem do outro lado; relíquia relic_express — pista: Placa do Mestre Búzio: 'Trinta moedas numa só correnteza'
- **Requisitos de motor:** nenhum
- Seção completa: [`PLANEJAMENTO_60_FASES.md`](PLANEJAMENTO_60_FASES.md#3-4--correntes-profundas-current_depths)

### 3-5 · Labirinto de Coral (`coral_maze`) — nova

- **Ideia própria:** o labirinto desce e a saída fica no alto: fuga ascendente com dois polvos.
- **Objetivo:** Desafio avançado: atravessar um labirinto submerso de coral com três ramificações, válvulas de corrente de mão única e o Polvo-Tinteiro, que persegue quem está nadando; o coral laranja aponta o caminho certo.
- **Mecânica principal:** Navegação em labirinto submerso com válvulas de corrente (passagens de mão única) e perseguidor (polvo)
- **Dificuldade / duração / tamanho:** 5/10 · 130–260 s · 5600×1620 u · 2 checkpoint(s)
- **Estreias:** Polvo-Tinteiro
- **Relíquias:** relíquia relic_pearls — pista: Pérolas cintilando no fim de um corredor de coral violeta; relíquia relic_coral — pista: Coral esbranquiçado e rachado no teto do salão central, com bolhas escapando; relíquia relic_octopus — pista: Placa de pedra com desenho de polvo e seta circular na entrada de uma volta estreita
- **Requisitos de motor:** nenhum
- Seção completa: [`PLANEJAMENTO_60_FASES.md`](PLANEJAMENTO_60_FASES.md#3-5--labirinto-de-coral-coral_maze)

### 3-6 · Galeão Submerso (`sunken_galleon`) — nova

- **Ideia própria:** o mastro tombado vira ponte e o casco racha no meio da luta.
- **Objetivo:** Fortaleza da Costa dos Corais: atravessar o galeão naufragado de compartimentos ora secos, ora alagados, e derrotar o Ermitão-Âncora, que usa a popa do navio como concha.
- **Mecânica principal:** Compartimentos alternando ar e água (zonas swim parciais) com conveses semissólidos inclinados em degraus
- **Dificuldade / duração / tamanho:** 5/10 · 150–290 s · 6000×1620 u · 2 checkpoint(s)
- **Estreias:** —
- **Relíquias:** relíquia relic_figurehead — pista: Gaivota pousada na figura de proa; cordas do gurupés com moedas; relíquia relic_chest — pista: Mapa na parede da cabine com um X sobre um ponto vazio do teto; relíquia relic_treasure e estrela — pista: Escotilha de canhão aberta com bolhas e luz dourada saindo
- **Requisitos de motor:** comportamento do chefe planejado Ermitão-Âncora (ermitao_ancora): família nova em lume/core/behaviors/bosses.py; rising_lava (extensão): a subida única de um perigo por evento já existe (hazard/to/speed, gatilho por x); faltam ciclos de subida e descida, gatilho por altura, tempo ou chefe, aviso sonoro, etapas com pausa, reposição no checkpoint e a variante com zona swim (maré) (variante água na fase 2 do chefe)
- Seção completa: [`PLANEJAMENTO_60_FASES.md`](PLANEJAMENTO_60_FASES.md#3-6--galeão-submerso-sunken_galleon)
