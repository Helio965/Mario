# Mundo 1 — Reino Verde (`green_kingdom`)

> Colinas, canais, moinhos e pomares. Bioma `grassland`, cor de mapa `#5fb25a`, mundo legado 1.
> Plano geral: [`PLANEJAMENTO_60_FASES.md`](PLANEJAMENTO_60_FASES.md) · dados: [`campaign_plan.json`](../../lume/data/plan/campaign_plan.json).

## Identidade

**Reviravolta do mundo.** Fundamentos com dois andares: o chão esconde tocas e o ar esconde blocos; termina num javali que só para ao bater na muralha.

**Paleta**
- verde-capim #5fbf47 com topo #9fe064 e sombra #3a8a36
- solo listrado #99613a / #c48a50 com pedrinhas e raízes
- céu #4aa6e8 → #dff4f4 com sol à direita
- flores creme #fff3c4, rosa #ffd1e3 e amarelo #ffe27a
- luz de Lume e marcas de segredo em turquesa #35c9b4
- fortaleza: pedra #8a8f9c e espinheiro roxo #5b3a5e

**Marcos visuais**
- moinhos de pedra com pás de lona (props windmill / windmill_blades)
- aqueduto em arcos, eclusas e roda d'água
- pomar de macieiras redondas com cestos e escadas
- tocas de coelho emolduradas por raízes e sebes de espinheiro
- fortaleza de pedra tomada pelo espinheiro, com pátio de toras

**Ambiência.** Manhã clara (L1–L2), meio-dia no pomar (L3), vento forte na colina (L4), fim de tarde nas tocas (L5) e entardecer alaranjado na fortaleza (L6). Partículas de folhas e pétalas (weather leaves), pássaros, água corrente; nas tocas, vagalumes e terra caindo.

**Física.** Física padrão (gravidade 1550 u/s², salto 590 u/s, corrida 340 u/s). Água dos canais é letal (não há nado no Mundo 1). Molas de feno ≈ 900 u/s (0,82× sem segurar o salto). Vãos obrigatórios ≤ 125 u (fases 1–2 vencíveis andando: alcance andando 168 u). Espinheiro fere sem matar.

## Progressão das mecânicas

| Fase | Id | Papel | Foco | Dif. | Ideia própria |
| --- | --- | --- | --- | ---: | --- |
| 1-1 | `first_steps` | apresentação | corrida, salto variável, blocos, pisão, cano secreto e bloco oculto | 1 | o ar guarda segredos: bloco oculto e galhos semissólidos |
| 1-2 | `valley_canals` | exploração | margens em desnível e plataformas móveis ainda opcionais; voador que perde as asas | 1 | a margem elevada esconde três rotas opcionais (alta, ponte e cano) |
| 1-3 | `orchard_guardian` | desafio de movimento | plataformas frágeis e leitura da abertura de um chefe intermediário | 2 | o primeiro chefe ensina a esperar a abertura luminosa |
| 1-4 | `windmill_heights` | mecânica especial | molas obrigatórias, pás circulares sobre água e plantas emergentes | 2 | as pás do moinho viram pontes giratórias sobre o canal |
| 1-5 | `meadow_burrows` | desafio avançado | dois andares (túnel obrigatório), semissólidos verticais, topo espinhoso + fogo/casco | 3 | a sebe fecha a superfície e o túnel vira o único caminho |
| 1-6 | `bramble_fortress` | fortaleza e chefe | espinheiros e chamas oscilantes, síntese do mundo e chefe de investida | 3 | três ritmos ao mesmo tempo antes de um chefe que se vence pela parede |

## Distribuição de inimigos

★ = estreia da espécie (igual a `introduced_in`); ● = permitida; ◆ = permitida só em sub-área do bioma indicado.

| Espécie | 1-1 | 1-2 | 1-3 | 1-4 | 1-5 | 1-6 |
| --- | :---: | :---: | :---: | :---: | :---: | :---: |
| Bolota (`bolota`) | ★ | ● | ● | ● | ● | ● |
| Caramujo-de-Casca (`caramujo`) | ★ | ● | ● | ● | ● | ● |
| Besouro-Asa (`besouro_alado`) |  | ★ | ● | ● | ● | ● |
| Besouro (`besouro`) |  | ★ | ● | ● | ● | ● |
| Guardião do Pomar (`guardiao_pomar`) |  |  | ★ |  |  |  |
| Flor-Mordedora (`flor_mordedora`) |  |  |  | ★ | ● | ● |
| Ouriço-Espinho (`ourico_espinho`) |  |  |  |  | ★ | ● |
| Javali Espinheiro (`javali_espinheiro`) |  |  |  |  |  | ★ |

Quantidade planejada de inimigos (sem chefes): 1-1: 4–5 · 1-2: 4–5 · 1-3: 4–6 · 1-4: 8–10 · 1-5: 12–14 · 1-6: 9–11.

## Chefe do mundo — Javali Espinheiro (`javali_espinheiro`, implementado)

- **Fase:** `bramble_fortress`
- **Arena:** Pátio do Espinheiro: 840 u de chão contínuo (x3200–4040) entre duas muralhas de toras (pilares de terreno + portões switch), teto de galhos alto de onde caem bolotas-espinho na fase 2; sem vãos nem degraus.
- **Ataques:**
  - Espreita: caminha na direção de Lume (70 u/s; 95 u/s irritado) por 1,2 s (0,8 s na fase 2)
  - Investida: raspa o chão (aviso de 0,7 s; 0,45 s na fase 2) e corre a 330 u/s (400 u/s na fase 2) até bater na muralha
  - Chuva de bolotas-espinho (fase 2): após cada batida, três bolotas caem do teto em x de Lume −90, 0 e +90
  - Crina de espinheiro: o dorso fere em qualquer contato fora do atordoamento (topo espinhoso)
- **Janela de vulnerabilidade:** Atordoado depois de bater na muralha (1,8 s; 1,35 s na fase 2): pisão na cabeça. Bola de fogo também fere durante o aviso (enquanto raspa o chão). Depois de cada golpe recua para o centro da arena por 1,1 s, intangível.
- **Fases e mudança de fase:** Despertar: dorme até Lume chegar a 430 u e faz uma introdução de 1,3 s. Fase 1 (3→2 PV): espreita longa e aviso de 0,7 s. Fase 2 (≤ metade da vida): aviso de 0,45 s, investida a 400 u/s e chuva de bolotas-espinho a cada batida.
- **Derrota (animação):** Desaba de lado com um bufo, a crina de espinheiro murcha e solta flores brancas; o portão direito sobe, o espinheiro da fortaleza floresce e o lampião da saída acende.
- **Relação com a mecânica do mundo:** Usa o fundamento do Reino Verde — ler o aviso e saltar no tempo certo — e transforma as muralhas (o 'chão seguro' do mundo) na arma contra o chefe; as bolotas-espinho retomam o inimigo-base do mundo.
- **Implementação:** família `thorn_boar` em `lume/core/behaviors/bosses.py` (implementada, entrada `javali_espinheiro` no registro); a fase `bramble_fortress` já declara `boss_arena` com portões `gate_left`/`gate_right`.

**Minichefe da fase 3:** Guardião do Pomar (família `guardian`, implementado): avança, salta e dispara; abre a guarda periodicamente (janela de pisão), mais rápido na segunda metade.

## NPC do mundo — Vovó Candeia, acendedora de lampiões do Reino Verde

**Função.** Explica os checkpoints: cada lampião que Lume toca é aceso por ela e vira o ponto de retorno. Aparece no primeiro checkpoint de cada fase do mundo (evento message) e, na fortaleza, acende o lampião da antessala do chefe. Também anuncia a regra da fase quando ela muda (molas, túnel, javali).

**Falas-guia**
- “Cada lampião aceso guarda seu caminho. Se cair, você volta aqui.”
- “As pás sobem e descem: pule quando estiverem no alto da volta.”
- “Por baixo da terra também há lampiões.”
- “O javali só para quando bate na muralha. Espere o tranco.”

**Implementação.** Prop animado (camada mid) ao lado do lampião + evento message no x do checkpoint. Não requer motor novo.

## Resumo por fase

### 1-1 · Primeiros Passos (`first_steps`) — legada 1-1

- **Ideia própria:** o ar guarda segredos: bloco oculto e galhos semissólidos.
- **Objetivo:** Ensinar andar, correr, saltar com altura variável, bater em blocos e pisar inimigos; o primeiro vão letal só aparece depois de dois exercícios de salto sem risco, e a fase termina com a primeira descoberta de segredo.
- **Mecânica principal:** Corrida e salto variável (segurar = até 112 u de altura; correndo, alcance de 259 u)
- **Dificuldade / duração / tamanho:** 1/10 · 40–100 s · 3200×1240 u · 1 checkpoint(s)
- **Estreias:** Bolota, Caramujo-de-Casca
- **Relíquias:** relíquia relic_room (x2678, y850), coração e 4 moedas — pista: Cano verde com seta luminosa e placa 'Sobre o cano, pressione ↓' em x2190; relíquia relic_high (x1886, y232) — pista: Trilha de moedas sobe pelos tijolos x1680 e x1830; relíquia relic_branch (x2780, y246) — pista: Galhos da macieira formam degraus acima do caramujo; maçã brilhante no galho de cima
- **Requisitos de motor:** nenhum
- Seção completa: [`PLANEJAMENTO_60_FASES.md`](PLANEJAMENTO_60_FASES.md#1-1--primeiros-passos-first_steps)

### 1-2 · Canais do Vale (`valley_canals`) — legada 1-2

- **Ideia própria:** a margem elevada esconde três rotas opcionais (alta, ponte e cano).
- **Objetivo:** Desenvolver o salto entre margens de alturas diferentes, apresentar plataformas móveis ainda opcionais e o voador que perde as asas; premiar a exploração com três rotas que reencontram o caminho principal.
- **Mecânica principal:** Plataformas móveis (eixos y e x) e margens em desnível de ±32 u
- **Dificuldade / duração / tamanho:** 1/10 · 45–110 s · 3500×1240 u · 1 checkpoint(s)
- **Estreias:** Besouro-Asa, Besouro
- **Relíquias:** relíquia relic_room (x3038, y850) e crescer — pista: Cano com seta luminosa e dica 'Há luz dentro deste cano' (x2620); relíquia relic_high (x2147, y252) — pista: Trilha de moedas sobe pelos blocos e pela plataforma horizontal; relíquia relic_bridge (x2300, y288) — pista: Ponte de tábuas sobre o último canal com moedas em arco
- **Requisitos de motor:** nenhum
- Seção completa: [`PLANEJAMENTO_60_FASES.md`](PLANEJAMENTO_60_FASES.md#1-2--canais-do-vale-valley_canals)

### 1-3 · Guardião do Pomar (`orchard_guardian`) — legada 1-3

- **Ideia própria:** o primeiro chefe ensina a esperar a abertura luminosa.
- **Objetivo:** Primeira grande prova: escadas de tijolo e pedra frágil, voador sobre chão firme e o Guardião do Pomar (3 PV) como chefe intermediário numa arena aberta.
- **Mecânica principal:** Plataformas frágeis (cedem 0,65 s após o pouso e voltam em 3 s) e leitura da guarda aberta do guardião
- **Dificuldade / duração / tamanho:** 2/10 · 60–130 s · 3900×1240 u · 1 checkpoint(s)
- **Estreias:** Guardião do Pomar
- **Relíquias:** relíquia relic_room (x2518, y850) e estrela — pista: Cano com seta luminosa e dica próxima; relíquia relic_high (x1482, y257) — pista: Trilha de moedas sobe pelos blocos até a pedra frágil; relíquia relic_canopy (x2600, y252) — pista: Galhos sob o voo do besouro levam à copa; maçã dourada no topo
- **Requisitos de motor:** nenhum
- Seção completa: [`PLANEJAMENTO_60_FASES.md`](PLANEJAMENTO_60_FASES.md#1-3--guardião-do-pomar-orchard_guardian)

### 1-4 · Colina dos Moinhos (`windmill_heights`) — nova

- **Ideia própria:** as pás do moinho viram pontes giratórias sobre o canal.
- **Objetivo:** Apresentar a mecânica especial do Reino Verde — molas de feno e pás de moinho giratórias — e a Flor-Mordedora, culminando em travessias de canal apoiadas nas pás.
- **Mecânica principal:** Pás de moinho: plataformas com movimento circular (motion axis circle) + molas de feno (spring, ≈900 u/s)
- **Dificuldade / duração / tamanho:** 2/10 · 70–150 s · 5600×1240 u · 2 checkpoint(s)
- **Estreias:** Flor-Mordedora
- **Relíquias:** relíquia relic_mill (x2263, y206) — pista: Beiral estreito entre as duas pás do canal; moedas sobem do topo da volta da pá; relíquia relic_high (x4210, y176) — pista: Mola de feno diante de beirais flutuantes; moedas em diagonal; relíquia relic_room (x5188, y850) e coração — pista: Cano com seta luminosa no prado final
- **Requisitos de motor:** nenhum
- Seção completa: [`PLANEJAMENTO_60_FASES.md`](PLANEJAMENTO_60_FASES.md#1-4--colina-dos-moinhos-windmill_heights)

### 1-5 · Tocas do Prado (`meadow_burrows`) — nova

- **Ideia própria:** a sebe fecha a superfície e o túnel vira o único caminho.
- **Objetivo:** Desafio avançado do Reino Verde: combinar molas, pedras frágeis, flores e o Ouriço-Espinho (topo espinhoso) num prado de dois andares — superfície e tocas — com saída vertical por raízes semissólidas.
- **Mecânica principal:** Dois andares: túnel subterrâneo obrigatório (sub-área burrows) com saída vertical por raízes semissólidas
- **Dificuldade / duração / tamanho:** 3/10 · 80–170 s · 6000×1240 u · 2 checkpoint(s)
- **Estreias:** Ouriço-Espinho
- **Relíquias:** relíquia relic_crumble (x1716, y208) — pista: Mola ao pé de tábuas rachadas com moedas em escada; relíquia relic_burrow (x2346, y816) — pista: Tijolos rachados no teto do túnel com terra escorrendo e brilho de quartzo acima; relíquia relic_high (x5050, y200) — pista: Galhos acima da mola x4800 com borboletas pousadas
- **Requisitos de motor:** nenhum
- Seção completa: [`PLANEJAMENTO_60_FASES.md`](PLANEJAMENTO_60_FASES.md#1-5--tocas-do-prado-meadow_burrows)

### 1-6 · Fortaleza do Espinheiro (`bramble_fortress`) — nova

- **Ideia própria:** três ritmos ao mesmo tempo antes de um chefe que se vence pela parede.
- **Objetivo:** Fortaleza final do Reino Verde: atravessar a fortaleza de pedra tomada por espinheiros usando tudo do mundo (cascos contra ouriços, molas, pedras frágeis, flores) e derrotar o Javali Espinheiro.
- **Mecânica principal:** Espinheiros (thorns: ferem sem matar) e chamas oscilantes (perigo móvel) em corredores de fortaleza
- **Dificuldade / duração / tamanho:** 3/10 · 110–220 s · 4400×1240 u · 2 checkpoint(s)
- **Estreias:** Javali Espinheiro
- **Relíquias:** relíquia relic_gallery (x1500, y186) — pista: Mola no fim do salão leva à galeria; estandarte dourado visível no alto; relíquia relic_flame (x2880, y250) — pista: Plataforma acima da chama oscilante com moedas no ritmo do ciclo; relíquia relic_room (x2698, y850) e coração — pista: Cano com seta luminosa entre as tochas
- **Requisitos de motor:** nenhum
- Seção completa: [`PLANEJAMENTO_60_FASES.md`](PLANEJAMENTO_60_FASES.md#1-6--fortaleza-do-espinheiro-bramble_fortress)
