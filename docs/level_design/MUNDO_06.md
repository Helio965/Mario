# Mundo 6 — Cidade Mecânica (`clockwork_city`)

> Engrenagens, vapor e esteiras. Bioma `city`, cor de mapa `#c58a4a`, mundo novo.
> Plano geral: [`PLANEJAMENTO_60_FASES.md`](PLANEJAMENTO_60_FASES.md) · dados: [`campaign_plan.json`](../../lume/data/plan/campaign_plan.json).

## Identidade

**Reviravolta do mundo.** A cidade é um relógio: tudo se move em compasso — engrenagens, vapor, esteiras, interruptores — e o chefe é vencido com a própria prensa da fábrica.

**Paleta**
- latão #c58a4a e cobre #b5653a
- ferro #5a6470 e fuligem #2e3138
- vapor branco #eef2f5 e luz âmbar #ffcf6e
- interruptores azul #4aa3ff e laranja #ff9a3c
- metal fundido #ff7a2e com brilho #ffe08a

**Marcos visuais**
- engrenagens gigantes nas fachadas
- usina de vapor com chaminés e manômetros
- linha de montagem com esteiras e prensas
- fábrica de interruptores com painel de controle
- torre do relógio com mostrador e campanário
- fundição com caçambas de metal fundido

**Ambiência.** Manhã enfumaçada com luz âmbar (L1), vapor e chiado (L2), barulho ritmado de fábrica (L3), luzes de painel piscando (L4), tique-taque e sinos (L5) e brasa da fundição (L6). Partículas de vapor e fagulhas.

**Física.** Esteiras (conveyor) somam surface_speed ao movimento (±60 a ±240 u/s); engrenagens são plataformas com movimento circular; jatos de vapor são zonas wind verticais (force_y ≈ −1900) ou laterais com período; prensas são crushers de topo seguro; blocos-interruptor (switch) já alternam ao bater num bloco ? com recompensa toggle (Game.toggle_group); interruptores temporizados e ligações a esteiras requerem extensão. Vãos obrigatórios ≤ 160 u, considerando o arrasto da esteira.

## Progressão das mecânicas

| Fase | Id | Papel | Foco | Dif. | Ideia própria |
| --- | --- | --- | --- | ---: | --- |
| 6-1 | `gear_district` | apresentação | engrenagens giratórias, esteiras suaves, robô e canhão (projéteis pisáveis) | 5 | o projétil do canhão vira degrau |
| 6-2 | `steam_works` | exploração | jatos de vapor como elevadores, rede de canos e drone que mergulha | 5 | o vapor deita: jatos laterais empurram para fora das passarelas |
| 6-3 | `conveyor_line` | desafio de movimento | esteiras de várias velocidades e prensas em compasso | 6 | a prensa vira elevador e, no fim, a linha acelera |
| 6-4 | `switch_factory` | mecânica especial | blocos-interruptor azul/laranja, inclusive temporizados (mecânica especial) | 6 | a sala vertical em que cada andar pede a outra cor |
| 6-5 | `clock_tower` | desafio avançado | subida vertical em ritmo sincronizado e ponteiros como pontes | 6 | atravessar o mostrador montado nos ponteiros |
| 6-6 | `iron_foundry` | fortaleza e chefe | metal fundido, esteiras e chefe vencido com prensa + interruptor | 6 | a linha invertida: o interruptor da fundição inverte todas as esteiras |

## Distribuição de inimigos

★ = estreia da espécie (igual a `introduced_in`); ● = permitida; ◆ = permitida só em sub-área do bioma indicado.

| Espécie | 6-1 | 6-2 | 6-3 | 6-4 | 6-5 | 6-6 |
| --- | :---: | :---: | :---: | :---: | :---: | :---: |
| Robô de Ronda (`robo_patrulha`) | ★ | ● | ● | ● | ● | ● |
| Canhão Sentinela (`sentinela_canhao`) | ★ | ● | ● | ● | ● | ● |
| Drone Vigia (`drone_vigia`) |  | ★ | ● | ● | ● | ● |
| Prensa a Vapor (`prensa_vapor`) |  |  | ★ | ● | ● | ● |
| Torreta de Arco (`torreta_arco`) |  |  |  |  | ★ | ● |
| Colosso Fundidor (chefe planejado) (`boss:colosso_fundidor`) |  |  |  |  |  | chefe |

Quantidade planejada de inimigos (sem chefes): 6-1: 10–14 · 6-2: 12–16 · 6-3: 14–18 · 6-4: 14–18 · 6-5: 16–22 · 6-6: 18–24.

## Chefe do mundo — Colosso Fundidor (`colosso_fundidor`, planejado)

- **Fase:** `iron_foundry`
- **Arena:** Salão do Colosso (1000×1080, fortaleza): esteira em todo o piso (sentido alternável), duas prensas fixas no teto (x≈250 e x≈750 da arena) com marcas de alinhamento no chão, dois blocos-interruptor nas paredes laterais a 96 u do chão e um cadinho de metal fundido no fundo.
- **Ataques:**
  - Vazamento de metal: inclina o cadinho e derrama metal que escorre pela esteira no sentido atual (perigo móvel no chão)
  - Punho-pistão: soco telescópico na altura do chão (aviso: vapor nas juntas por 0,5 s)
  - Inversão da esteira: bate o pé e inverte o sentido da esteira, arrastando Lume
  - Porcas e reforços (fase 2): lança porcas incandescentes em arco e chama dois Robôs de Ronda pela escotilha
- **Janela de vulnerabilidade:** Quando o Colosso passa sob uma prensa, a marca de alinhamento no chão acende. Se Lume bater no interruptor da parede nesse momento, a prensa desce na cabeça dele e abre a escotilha do núcleo por 2 s — pisão no núcleo. Fogo e pisão no corpo não causam dano.
- **Fases e mudança de fase:** Fase 1 (5–3 PV): esteira lenta, uma prensa ativa por vez, vazamentos curtos. Fase 2 (2–1 PV): esteira rápida, o cadinho transborda (metal escorre pelos dois lados), a prensa só desce depois de bater nos dois interruptores e entram porcas e robôs.
- **Derrota (animação):** O Colosso trava, solta vapor por todas as juntas e cai de joelhos; o núcleo se solta, sobe e vira o farol da fundição, que acende a cidade inteira — fronteira 6.
- **Relação com a mecânica do mundo:** Esteiras, interruptores e prensas: o chefe só é vencido usando as máquinas que o mundo ensinou.
- **Implementação:** chefe planejado — nova família de comportamento, entrada `boss: true` no registro (ver seção 6.2 do plano geral), eventos `boss_arena`/`camera_lock` e os requisitos listados na fase `iron_foundry`.

**Fase 3 sem minichefe:** `conveyor_line` termina num teste de movimento próprio (ver resumo abaixo).

## NPC do mundo — Mestre Corda, relojoeiro e zelador das máquinas

**Função.** Explica ritmo e interruptores: dá corda nos mecanismos de cada fase, mostra que as máquinas seguem um compasso (conte com o tique-taque) e, na fábrica, apresenta os blocos azuis e laranja. Aparece no checkpoint e marca com um relógio de bolso os trechos sincronizados.

**Falas-guia**
- “Toda máquina tem compasso. Conte com o tique-taque.”
- “Bateu no interruptor? Azul vira laranja, laranja vira azul.”
- “O ponteiro grande é lento, mas leva longe.”
- “A prensa da fundição obedece aos botões. O colosso, não.”

**Implementação.** Prop animado (relojoeiro com chave de corda) + evento message; o tique-taque é áudio sincronizado ao período das plataformas. Não requer motor novo.

## Resumo por fase

### 6-1 · Distrito das Engrenagens (`gear_district`) — nova

- **Ideia própria:** o projétil do canhão vira degrau.
- **Objetivo:** Apresentar a cidade: esteiras suaves, engrenagens que giram como plataformas, o Robô de Ronda e o Canhão Sentinela, cujos projéteis lentos podem ser pisados.
- **Mecânica principal:** Engrenagens-plataforma (motion circle) e esteiras suaves (conveyor ±80 u/s)
- **Dificuldade / duração / tamanho:** 5/10 · 85–170 s · 5000×1240 u · 2 checkpoint(s)
- **Estreias:** Robô de Ronda, Canhão Sentinela
- **Relíquias:** relíquia relic_gear — pista: Uma engrenagem dourada maior gira acima da rua com moedas no topo da volta; relíquia relic_sewer e estrela — pista: Bueiro com vapor e luz turquesa saindo pela grade; relíquia relic_billboard — pista: Lâmpada do cartaz pisca em código sobre um ponto vazio da rua
- **Requisitos de motor:** nenhum
- Seção completa: [`PLANEJAMENTO_60_FASES.md`](PLANEJAMENTO_60_FASES.md#6-1--distrito-das-engrenagens-gear_district)

### 6-2 · Usina de Vapor (`steam_works`) — nova

- **Ideia própria:** o vapor deita: jatos laterais empurram para fora das passarelas.
- **Objetivo:** Explorar a usina subindo por jatos de vapor, escolher caminhos numa rede de canos com quatro saídas e conhecer o Drone Vigia, que mira e mergulha em diagonal.
- **Mecânica principal:** Jatos de vapor ascendentes (zonas wind force_y ≈ −1900) contínuos e intermitentes (período 3 s, duty 0,5)
- **Dificuldade / duração / tamanho:** 5/10 · 100–200 s · 5400×2160 u · 2 checkpoint(s)
- **Estreias:** Drone Vigia
- **Relíquias:** relíquia relic_valve e estrela — pista: Cano azul com placa de válvula e vapor frio (azulado) saindo; relíquia relic_chimney — pista: Uma chaminé sem fumaça, com fuligem formando degraus; relíquia relic_gauge — pista: Um manômetro sem cano aponta para cima, para um ponto vazio
- **Requisitos de motor:** nenhum
- Seção completa: [`PLANEJAMENTO_60_FASES.md`](PLANEJAMENTO_60_FASES.md#6-2--usina-de-vapor-steam_works)

### 6-3 · Linha de Montagem (`conveyor_line`) — nova

- **Ideia própria:** a prensa vira elevador e, no fim, a linha acelera.
- **Objetivo:** Desafio de movimento: atravessar a linha de montagem com esteiras de velocidades e sentidos diferentes e prensas a vapor em compasso; terminar na 'linha acelerada'.
- **Mecânica principal:** Esteiras com velocidades e sentidos diferentes (±60 a ±240 u/s) somadas ao salto
- **Dificuldade / duração / tamanho:** 6/10 · 100–200 s · 5600×1240 u · 2 checkpoint(s)
- **Estreias:** Prensa a Vapor
- **Relíquias:** relíquia relic_crate — pista: Uma caixa dourada passa na linha de cima; moedas sobre as vigas; relíquia relic_storage e estrela — pista: Caixa com seta pintada e etiqueta 'NÃO ABRIR'; relíquia relic_press — pista: Três prensas com luzes verdes acesas em sequência
- **Requisitos de motor:** nenhum
- Seção completa: [`PLANEJAMENTO_60_FASES.md`](PLANEJAMENTO_60_FASES.md#6-3--linha-de-montagem-conveyor_line)

### 6-4 · Fábrica dos Interruptores (`switch_factory`) — nova

- **Ideia própria:** a sala vertical em que cada andar pede a outra cor.
- **Objetivo:** Mecânica especial da Cidade Mecânica: atravessar a fábrica alternando blocos azuis e laranja com blocos-interruptor (incluindo interruptores temporizados) e ligar o painel que acende a esteira principal da fundição.
- **Mecânica principal:** Blocos-interruptor (switch) azul/laranja alternados por bloco-interruptor e por temporizador
- **Dificuldade / duração / tamanho:** 6/10 · 110–220 s · 5400×1620 u · 2 checkpoint(s)
- **Estreias:** —
- **Relíquias:** relíquia relic_orange — pista: Contorno tracejado laranja de uma escada que só aparece com a cor laranja; relíquia relic_broken — pista: Pilha de interruptores quebrados soltando faíscas sob um ponto vazio; relíquia relic_ticktock — pista: Relógio de parede com ponteiro vermelho sobre um interruptor de 4 s
- **Requisitos de motor:** toggle_switch (extensão): a alternância por bloco 'toggle' já existe (Game.toggle_group); faltam o evento toggle_switch por gatilho, o interruptor temporizado e a ligação do grupo a outros sistemas (esteiras, plataformas fantasmas) — a alternância básica já funciona; bloqueia só os trechos temporizados (etapas 4 e 7 e o desafio do tique-taque)
- Seção completa: [`PLANEJAMENTO_60_FASES.md`](PLANEJAMENTO_60_FASES.md#6-4--fábrica-dos-interruptores-switch_factory)

### 6-5 · Torre do Relógio (`clock_tower`) — nova

- **Ideia própria:** atravessar o mostrador montado nos ponteiros.
- **Objetivo:** Desafio avançado: subir a torre do relógio com plataformas sincronizadas a um compasso de 2 s, pêndulos, ponteiros como pontes giratórias e a Torreta de Arco, que lança porcas incandescentes em arco.
- **Mecânica principal:** Plataformas sincronizadas a um compasso único (mesmo período, fases 0, π/2, π) e ponteiros do relógio como pontes giratórias (circle, alcance 200)
- **Dificuldade / duração / tamanho:** 6/10 · 120–240 s · 4800×2700 u · 3 checkpoint(s)
- **Estreias:** Torreta de Arco
- **Relíquias:** relíquia relic_cuckoo e estrela — pista: Porta do cuco abre e fecha a cada hora (a cada 10 s) mostrando luz dourada; relíquia relic_second — pista: Moedas presas ao ponteiro dos segundos dão uma volta inteira; relíquia relic_beam — pista: Uma janela quebrada do mostrador deixa ver uma viga externa com moedas
- **Requisitos de motor:** nenhum
- Seção completa: [`PLANEJAMENTO_60_FASES.md`](PLANEJAMENTO_60_FASES.md#6-5--torre-do-relógio-clock_tower)

### 6-6 · Fundição de Ferro (`iron_foundry`) — nova

- **Ideia própria:** a linha invertida: o interruptor da fundição inverte todas as esteiras.
- **Objetivo:** Fortaleza da Cidade Mecânica: atravessar a fundição sobre metal fundido, caçambas e esteiras, e derrotar o Colosso Fundidor atraindo-o para baixo da prensa e acionando o interruptor no momento certo.
- **Mecânica principal:** Metal fundido (perigo lava) atravessado por caçambas suspensas (moving eixo x) e esteiras
- **Dificuldade / duração / tamanho:** 6/10 · 150–300 s · 6400×1620 u · 2 checkpoint(s)
- **Estreias:** —
- **Relíquias:** relíquia relic_bucket — pista: Uma caçamba dourada parada no fim do trilho do teto; relíquia relic_mold e estrela — pista: Molde em forma de estrela com vapor frio saindo; relíquia relic_reverse — pista: Placa com setas em sentidos opostos sobre o interruptor
- **Requisitos de motor:** comportamento do chefe planejado Colosso Fundidor (colosso_fundidor): família nova em lume/core/behaviors/bosses.py; toggle_switch (extensão): a alternância por bloco 'toggle' já existe (Game.toggle_group); faltam o evento toggle_switch por gatilho, o interruptor temporizado e a ligação do grupo a outros sistemas (esteiras, plataformas fantasmas)
- Seção completa: [`PLANEJAMENTO_60_FASES.md`](PLANEJAMENTO_60_FASES.md#6-6--fundição-de-ferro-iron_foundry)
