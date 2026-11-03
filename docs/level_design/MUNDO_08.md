# Mundo 8 — Pântano Assombrado (`haunted_swamp`)

> Névoa, lanternas e casarões afundados. Bioma `swamp`, cor de mapa `#7d8fb0`, mundo novo.
> Plano geral: [`PLANEJAMENTO_60_FASES.md`](PLANEJAMENTO_60_FASES.md) · dados: [`campaign_plan.json`](../../lume/data/plan/campaign_plan.json).

## Identidade

**Reviravolta do mundo.** A luz vira mecânica: o halo de Lume paralisa as sombras (e encolhe quando ele corre), as lanternas mudam o caminho e, no fim, só duas lanternas acesas tornam a sombra sólida.

**Paleta**
- azul-ardósia #7d8fb0 e noite #2a3148
- verde-lodo #4f6b4a e lodo venenoso roxo #7a4f9a com bolhas
- névoa lilás #b7a9d6
- âmbar de lanterna #ffcf6e (única cor quente: sempre significa segurança)
- branco-fantasma #e8f0ff

**Marcos visuais**
- passarelas de tábuas sobre o brejo com vitórias-régias
- postes de lanterna tortos
- casarão afundado e adernado
- árvores retorcidas com barba-de-velho
- torre do lanterneiro com a grande lanterna no topo

**Ambiência.** Fim de tarde com névoa baixa (L1), crepúsculo com lanternas (L2), interior do casarão à luz de velas (L3), noite fechada (L4), névoa densa e lua (L5) e topo da torre sob lua cheia (L6). Coaxar, rangidos, sinos distantes; névoa em camadas na frente e no fundo.

**Física.** Lodo venenoso (poison) fere sem matar; água funda mata; vitórias-régias balançam (moving eixo y ±16 u); passarelas frágeis; zonas dark com o halo de Lume (máscara já desenhada: 120 u, 64 u correndo; lanternas acendíveis requerem extensão); lodo movediço (quicksand: afunda e mata ao cobrir Lume) no lodaçal. Sombras-Errantes atravessam paredes, derivam na direção de Lume no escuro e paralisam (inofensivas) dentro do halo da lanterna: 120 u andando, 64 u correndo. Vãos obrigatórios ≤ 160 u.

## Progressão das mecânicas

| Fase | Id | Papel | Foco | Dif. | Ideia própria |
| --- | --- | --- | --- | ---: | --- |
| 8-1 | `misty_marsh` | apresentação | névoa, vitórias-régias, lodo venenoso, a sombra que para no halo e o sapo | 6 | o trecho que exige correr encolhe o halo e deixa as sombras chegarem |
| 8-2 | `lantern_bog` | exploração | lanternas como guia, mãos que sobem do lodo e rotas paralelas | 7 | lanternas-boia são o único caminho sobre a poça escura |
| 8-3 | `sunken_mansion` | desafio de movimento | casarão em salas, ossadas que se remontam e salas alagadas | 7 | no salão de baile as ossadas se remontam no compasso da valsa |
| 8-4 | `lights_out` | mecânica especial | escuridão com raio de luz e lanternas acendíveis (mecânica especial) | 7 | o vento apaga todas as lanternas e só as mariposas iluminam |
| 8-5 | `phantom_mire` | desafio avançado | lodo movediço, névoa densa e todos os assombros juntos | 8 | a ponte fantasma só existe enquanto a sombra-guardiã está paralisada no halo |
| 8-6 | `lantern_keep` | fortaleza e chefe | torre vertical, mecanismos e chefe que só se solidifica na luz | 8 | o contrapeso da grande lanterna vira elevador |

## Distribuição de inimigos

★ = estreia da espécie (igual a `introduced_in`); ● = permitida; ◆ = permitida só em sub-área do bioma indicado.

| Espécie | 8-1 | 8-2 | 8-3 | 8-4 | 8-5 | 8-6 |
| --- | :---: | :---: | :---: | :---: | :---: | :---: |
| Flor-Mordedora (`flor_mordedora`) | ● | ● | ● | ● | ● | ● |
| Cogumelo Saltitante (`cogumelo_saltitante`) | ● | ● | ● | ● | ● | ● |
| Mariposa-Lume (`mariposa_lume`) | ● | ● | ● | ● | ● | ● |
| Planta-de-Esporos (`planta_esporos`) | ● | ● | ● | ● | ● | ● |
| Aranha-do-Cipó (`aranha_cipo`) | ● | ● | ● | ● | ● | ● |
| Sombra-Errante (`assombracao_timida`) | ★ | ● | ● | ● | ● | ● |
| Sapo-do-Lodo (`sapo_lodo`) | ★ | ● | ● | ● | ● | ● |
| Mão-do-Lodo (`mao_lodo`) |  | ★ | ● | ● | ● | ● |
| Ossada do Pântano (`ossada_pantano`) |  |  | ★ | ● | ● | ● |
| Canhão Sentinela (`sentinela_canhao`) |  |  |  |  |  | ◆ fortress |
| Prensa a Vapor (`prensa_vapor`) |  |  |  |  |  | ◆ fortress |
| Vulto Apagador (chefe planejado) (`boss:vulto_apagador`) |  |  |  |  |  | chefe |

Quantidade planejada de inimigos (sem chefes): 8-1: 12–16 · 8-2: 16–20 · 8-3: 16–22 · 8-4: 14–20 · 8-5: 20–26 · 8-6: 20–26.

## Chefe do mundo — Vulto Apagador (`vulto_apagador`, planejado)

- **Fase:** `lantern_keep`
- **Arena:** Sala da grande lanterna (1000×1080, fortaleza): sala circular escura com quatro lanternas em pedestais (acendem quando Lume bate nelas por baixo), escada em caracol semissólida em volta, janelas com luar e a grande lanterna apagada no centro.
- **Ataques:**
  - Sopro apagador: varre a sala e apaga as lanternas acesas (aviso: chamas se inclinam por 0,6 s)
  - Mãos de sombra: mãos-do-lodo de sombra surgem do chão nas áreas escuras
  - Investida fantasma: atravessa paredes e cruza a sala na direção de Lume
  - Três sombras (fase 2): divide-se em três; só a verdadeira projeta sombra na parede quando há lanterna acesa
- **Janela de vulnerabilidade:** Com duas lanternas acesas ao mesmo tempo, o vulto fica sólido e atordoado pela luz por 2 s — pisão (ou fogo) nesse estado. Com uma lanterna ele só recua.
- **Fases e mudança de fase:** Fase 1 (6–4 PV): sopro, mãos e investidas; as lanternas ficam acesas 8 s. Fase 2 (3–1 PV): três sombras, lanternas acesas por 5 s e o sopro passa a apagar duas por vez.
- **Derrota (animação):** A sombra é sugada pela grande lanterna central, que acende e ilumina o pântano inteiro; a névoa recua, Lírio recupera a torre do mestre e o farol da fronteira 8 brilha em âmbar.
- **Relação com a mecânica do mundo:** Luz e olhar: o mundo ensinou que a luz âmbar é segura, que fantasmas reagem à visão e que lanternas mudam o que existe — o chefe só fica sólido na luz.
- **Implementação:** chefe planejado — nova família de comportamento, entrada `boss: true` no registro (ver seção 6.2 do plano geral), eventos `boss_arena`/`camera_lock` e os requisitos listados na fase `lantern_keep`.

**Fase 3 sem minichefe:** `sunken_mansion` termina num teste de movimento próprio (ver resumo abaixo).

## NPC do mundo — Lírio, aprendiz de lanterneiro

**Função.** Explica luz e fantasmas: acende o lampião do checkpoint, ensina que a Sombra-Errante paralisa dentro do halo da lanterna de Lume (que encolhe quando ele corre) e que a luz âmbar sempre marca chão seguro. Seu mestre perdeu a torre para o Vulto Apagador; Lírio acompanha Lume até a antessala do chefe e lhe entrega a primeira lanterna acesa.

**Falas-guia**
- “Ande devagar perto das sombras: dentro da sua luz elas param. Correndo, a luz encolhe.”
- “Luz âmbar é chão seguro. Sempre.”
- “Mão de lodo não gosta de fogo.”
- “Duas lanternas acesas e a sombra fica de carne e osso.”

**Implementação.** Prop animado (menino com vara de acender lampiões) + evento message; a lanterna entregue é só narrativa. Não requer motor novo.

## Resumo por fase

### 8-1 · Brejo da Névoa (`misty_marsh`) — nova

- **Ideia própria:** o trecho que exige correr encolhe o halo e deixa as sombras chegarem.
- **Objetivo:** Apresentar o pântano: passarelas e vitórias-régias sobre lodo venenoso e água funda, o Sapo-do-Lodo e a Sombra-Errante, que deriva na direção de Lume no escuro e paralisa dentro do halo da lanterna.
- **Mecânica principal:** Halo da lanterna: a Sombra-Errante paralisa (e fica inofensiva) dentro do halo de Lume — 120 u andando, 64 u correndo
- **Dificuldade / duração / tamanho:** 6/10 · 90–180 s · 5400×1080 u · 2 checkpoint(s)
- **Estreias:** Sombra-Errante, Sapo-do-Lodo
- **Relíquias:** relíquia relic_tree — pista: Barba-de-velho forma uma escada até uma coruja de pedra no topo da árvore; relíquia relic_boat e coração — pista: Casco de barco virado com uma lanterna acesa dentro; relíquia relic_lily — pista: Oito vitórias-régias floridas em fila sobre água funda
- **Requisitos de motor:** nenhum
- Seção completa: [`PLANEJAMENTO_60_FASES.md`](PLANEJAMENTO_60_FASES.md#8-1--brejo-da-névoa-misty_marsh)

### 8-2 · Charco das Lanternas (`lantern_bog`) — nova

- **Ideia própria:** lanternas-boia são o único caminho sobre a poça escura.
- **Objetivo:** Explorar o charco seguindo lanternas: o caminho principal é marcado por luz âmbar, as rotas paralelas por lanternas apagadas; conhecer a Mão-do-Lodo, que sobe de poças escuras.
- **Mecânica principal:** Lanternas como guia (luz âmbar = chão seguro) e rotas paralelas em dois níveis
- **Dificuldade / duração / tamanho:** 7/10 · 110–220 s · 5800×1620 u · 2 checkpoint(s)
- **Estreias:** Mão-do-Lodo
- **Relíquias:** relíquia relic_willow e estrela — pista: Lanterna apagada pendurada num salgueiro; galhos formam degraus acima dela; relíquia relic_cellar — pista: Alçapão sob uma cabana de palafita com luz âmbar pelas frestas; relíquia relic_hands — pista: Cinco poças em fila com mãos em ritmo crescente e moedas sobre cada poça
- **Requisitos de motor:** lights (extensão): a máscara de escuridão das zonas dark com o halo de Lume (120 u; 64 u correndo) já é desenhada; faltam lanternas fixas e acendíveis com raio e duração e o evento lights global (apagar/acender) (opcional: sem a máscara a fase fica jogável e mais clara)
- Seção completa: [`PLANEJAMENTO_60_FASES.md`](PLANEJAMENTO_60_FASES.md#8-2--charco-das-lanternas-lantern_bog)

### 8-3 · Casarão Afundado (`sunken_mansion`) — nova

- **Ideia própria:** no salão de baile as ossadas se remontam no compasso da valsa.
- **Objetivo:** Desafio de movimento dentro de um casarão meio afundado: salas ligadas por portas, pisos frágeis, salas alagadas e a Ossada do Pântano, que desmonta com o pisão e se remonta.
- **Mecânica principal:** Ossadas que se remontam (pisão só desmonta por 4 s) em salas de piso frágil
- **Dificuldade / duração / tamanho:** 7/10 · 120–240 s · 5600×2160 u · 2 checkpoint(s)
- **Estreias:** Ossada do Pântano
- **Relíquias:** relíquia relic_portrait — pista: Um retrato pisca quando o halo da lanterna de Lume o ilumina; relíquia relic_chandelier — pista: Lustres apagados com uma vela ainda acesa no mais alto; relíquia relic_cellar e estrela — pista: Bolhas sobem entre as tábuas do hall onde o piso é mais escuro
- **Requisitos de motor:** nenhum
- Seção completa: [`PLANEJAMENTO_60_FASES.md`](PLANEJAMENTO_60_FASES.md#8-3--casarão-afundado-sunken_mansion)

### 8-4 · Apagão no Pântano (`lights_out`) — nova

- **Ideia própria:** o vento apaga todas as lanternas e só as mariposas iluminam.
- **Objetivo:** Mecânica especial do Pântano Assombrado: atravessar a noite fechada com a pequena luz de Lume, acendendo lanternas que ampliam a visão por tempo limitado e paralisam as sombras.
- **Mecânica principal:** Escuridão com raio de visão (zonas dark) e lanternas acendíveis por toque (evento lights, 15–20 s de luz)
- **Dificuldade / duração / tamanho:** 7/10 · 110–220 s · 5400×1620 u · 2 checkpoint(s)
- **Estreias:** —
- **Relíquias:** relíquia relic_lantern — pista: Uma lanterna verde (diferente das âmbar) pisca no alto, fora do caminho; relíquia relic_den e estrela — pista: Cano coberto de musgo com luz verde saindo; relíquia relic_dark — pista: Placa de Lírio: 'feche os olhos e escute'; coaxar marca o caminho
- **Requisitos de motor:** lights (extensão): a máscara de escuridão das zonas dark com o halo de Lume (120 u; 64 u correndo) já é desenhada; faltam lanternas fixas e acendíveis com raio e duração e o evento lights global (apagar/acender)
- Seção completa: [`PLANEJAMENTO_60_FASES.md`](PLANEJAMENTO_60_FASES.md#8-4--apagão-no-pântano-lights_out)

### 8-5 · Lodaçal Fantasma (`phantom_mire`) — nova

- **Ideia própria:** a ponte fantasma só existe enquanto a sombra-guardiã está paralisada no halo.
- **Objetivo:** Desafio avançado: atravessar o lodaçal combinando lodo movediço, névoa densa, sombras-errantes, mãos, ossadas e trechos escuros.
- **Mecânica principal:** Lodo movediço (quicksand: afunda devagar, pulo reduzido) entre ilhas de troncos
- **Dificuldade / duração / tamanho:** 8/10 · 130–260 s · 6200×1620 u · 2 checkpoint(s)
- **Estreias:** —
- **Relíquias:** relíquia relic_tomb — pista: A lápide mais alta tem uma lanterna âmbar e moedas em diagonal; relíquia relic_crypt e estrela — pista: Portão de cripta entreaberto com cano escuro e luz azul; relíquia relic_logs — pista: Troncos afundando em sequência sobre o lodo com moedas em cima
- **Requisitos de motor:** toggle_switch (extensão): a alternância por bloco 'toggle' já existe (Game.toggle_group); faltam o evento toggle_switch por gatilho, o interruptor temporizado e a ligação do grupo a outros sistemas (esteiras, plataformas fantasmas) (ponte fantasma ligada ao estado 'freeze' da sombra-guardiã); lights (extensão): a máscara de escuridão das zonas dark com o halo de Lume (120 u; 64 u correndo) já é desenhada; faltam lanternas fixas e acendíveis com raio e duração e o evento lights global (apagar/acender) (opcional)
- Seção completa: [`PLANEJAMENTO_60_FASES.md`](PLANEJAMENTO_60_FASES.md#8-5--lodaçal-fantasma-phantom_mire)

### 8-6 · Torre do Lanterneiro (`lantern_keep`) — nova

- **Ideia própria:** o contrapeso da grande lanterna vira elevador.
- **Objetivo:** Fortaleza do Pântano Assombrado: subir a torre do lanterneiro tomada pelas sombras, usando os mecanismos de contrapeso, e derrotar o Vulto Apagador acendendo duas lanternas ao mesmo tempo.
- **Mecânica principal:** Escada em caracol vertical com mecanismos de contrapeso (plataformas móveis) e lanternas que iluminam por tempo
- **Dificuldade / duração / tamanho:** 8/10 · 170–330 s · 5200×3240 u · 3 checkpoint(s)
- **Estreias:** —
- **Relíquias:** relíquia relic_balcony — pista: Uma janela aberta deixa entrar o luar sobre degraus do lado de fora; relíquia relic_maps e estrela — pista: Cano atrás de um mapa enrolado com a marca de uma lanterna; relíquia relic_weights — pista: Contrapesos com faixas âmbar marcando a ordem de subida
- **Requisitos de motor:** comportamento do chefe planejado Vulto Apagador (vulto_apagador): família nova em lume/core/behaviors/bosses.py; lights (extensão): a máscara de escuridão das zonas dark com o halo de Lume (120 u; 64 u correndo) já é desenhada; faltam lanternas fixas e acendíveis com raio e duração e o evento lights global (apagar/acender)
- Seção completa: [`PLANEJAMENTO_60_FASES.md`](PLANEJAMENTO_60_FASES.md#8-6--torre-do-lanterneiro-lantern_keep)
