# Mundo 10 — Cidadela das Estrelas (`star_citadel`)

> Constelações, gravidade e o eclipse final. Bioma `citadel`, cor de mapa `#b79cff`, mundo novo.
> Plano geral: [`PLANEJAMENTO_60_FASES.md`](PLANEJAMENTO_60_FASES.md) · dados: [`campaign_plan.json`](../../lume/data/plan/campaign_plan.json).

## Identidade

**Reviravolta do mundo.** Síntese: a gravidade afrouxa, as constelações viram pontes, os espelhos refletem mundos anteriores e o eclipse apaga tudo — o último chefe usa as dez fronteiras.

**Paleta**
- violeta #b79cff e azul-noite #1b1840
- dourado-estelar #ffd36e e branco-estrela #ffffff
- prata #c8d0e0 dos espelhos
- preto-eclipse #0a0a14 com coroa laranja #ff9a3c
- cores das dez fronteiras como acentos nos faróis reacesos

**Marcos visuais**
- portão estelar com escadaria de luz
- trilhas de constelações sobre o vazio
- salões de gravidade com relógios de areia flutuantes
- santuário de espelhos-poça que refletem outros mundos
- bastião do eclipse com dez faróis apagados
- trono do eclipse sob um sol negro

**Ambiência.** Noite estrelada parada (L1), céu girando lentamente (L2), silêncio com eco (L3), reflexos iridescentes (L4), escuridão crescente do eclipse (L5) e o sol negro com coroa de fogo (L6). Partículas de poeira estelar e um zumbido grave que cresce até o fim.

**Física.** Bolsões de baixa gravidade (lowgrav: gravidade × 0,55 → salto de ~204 u de altura e arco mais longo; subidas obrigatórias dentro deles até 116 u, vãos obrigatórios mantidos ≤ 160 u). Blocos ocultos em forma de constelação. Espelhos-poça são canos de passagem para sub-áreas de outros biomas (underwater, underground, fortress), onde os inimigos daqueles mundos voltam pela regra de habitat. O eclipse escurece usando a máscara de escuridão já desenhada (o raio progressivo e os faróis como luz requerem extensão) e a chama estelar ascendente do chefe usa rising_lava com gatilho pelo chefe (extensão).

## Progressão das mecânicas

| Fase | Id | Papel | Foco | Dif. | Ideia própria |
| --- | --- | --- | --- | ---: | --- |
| 10-1 | `starlit_gate` | apresentação | baixa gravidade demonstrada e sentinela de elite (leque de três) | 8 | o último bolsão de baixa gravidade cobre o vazio entre duas torres |
| 10-2 | `constellation_path` | exploração | constelações de blocos ocultos reveladas em cadeia e cometas | 9 | revelar a ponte em cadeia: cada estrela revelada é o degrau para bater na próxima |
| 10-3 | `gravity_halls` | desafio de movimento | faixas de gravidade alternada, vento solar e o Guardião da Constelação | 9 | vento solar dentro da baixa gravidade leva Lume longe demais |
| 10-4 | `mirror_sanctum` | mecânica especial | espelhos que levam a reflexos da costa, das cavernas e das fortalezas (mecânica especial) | 9 | os espelhos do segundo átrio misturam dois mundos na mesma sala |
| 10-5 | `eclipse_bastion` | desafio avançado | dez fronteiras em sequência sob o eclipse que escurece | 10 | cada farol reaceso devolve um pouco de luz ao bastião que escurece |
| 10-6 | `throne_of_eclipse` | fortaleza e chefe | chefe final em três fases com espelhos, apagão e chama estelar | 10 | a luz do próprio Eclipse, refletida num espelho, abre o seu núcleo |

## Distribuição de inimigos

★ = estreia da espécie (igual a `introduced_in`); ● = permitida; ◆ = permitida só em sub-área do bioma indicado.

| Espécie | 10-1 | 10-2 | 10-3 | 10-4 | 10-5 | 10-6 |
| --- | :---: | :---: | :---: | :---: | :---: | :---: |
| Canhão Sentinela (`sentinela_canhao`) | ● | ● | ● | ● | ● | ● |
| Sombra-Errante (`assombracao_timida`) | ● | ● | ● | ● | ● | ● |
| Sentinela Estelar (`sentinela_estelar`) | ★ | ● | ● | ● | ● | ● |
| Cometa Errante (`cometa_errante`) |  | ★ | ● | ● | ● | ● |
| Guardião da Constelação (`guardiao_constelacao`) |  |  | ★ | ● | ● | ● |
| Baiacu-Espinho (`baiacu_espinho`) |  |  |  | ◆ underwater |  |  |
| Moreia-da-Toca (`moreia_toca`) |  |  |  | ◆ underwater |  |  |
| Água-Viva Elétrica (`agua_viva`) |  |  |  | ◆ underwater | ◆ underwater |  |
| Polvo-Tinteiro (`polvo_tinteiro`) |  |  |  | ◆ underwater | ◆ underwater |  |
| Morcego-Brasa (`morcego_brasa`) |  |  |  | ◆ underground |  | ◆ fortress |
| Pingente de Gelo (`pingente_queda`) |  |  |  | ◆ underground |  |  |
| Prensa a Vapor (`prensa_vapor`) |  |  |  | ◆ fortress | ◆ fortress | ◆ fortress |
| Boca-de-Fornalha (`boca_fornalha`) |  |  |  | ◆ fortress | ◆ fortress | ◆ fortress |
| Golem de Basalto (`golem_basalto`) |  |  |  | ◆ fortress | ◆ fortress |  |
| Ossada do Pântano (`ossada_pantano`) |  |  |  | ◆ fortress | ◆ fortress | ◆ fortress |
| Brasa Andante (`brasa_andante`) |  |  |  |  | ◆ fortress |  |
| Salta-Brasa (`bolha_magma`) |  |  |  |  | ◆ fortress |  |
| Eclipse Devorador (chefe planejado) (`boss:eclipse_devorador`) |  |  |  |  |  | chefe |

Quantidade planejada de inimigos (sem chefes): 10-1: 14–18 · 10-2: 16–22 · 10-3: 16–22 · 10-4: 22–30 · 10-5: 26–34 · 10-6: 20–28.

## Chefe do mundo — Eclipse Devorador (`eclipse_devorador`, planejado)

- **Fase:** `throne_of_eclipse`
- **Arena:** Arena do trono (1300×2700, cidadela): plataforma circular de 1100 u com anéis de baixa gravidade, quatro espelhos gigantes nas bordas (plataformas atrás das quais Lume se protege) e o sol negro no centro; na fase 3 o trono desmorona em plataformas flutuantes que sobem até o topo.
- **Ataques:**
  - Raios de constelação: linhas de estrelas se acendem (aviso de 0,8 s) e disparam em linha reta
  - Reflexos: cria duas cópias espelhadas de Lume que repetem seus movimentos com 1 s de atraso (tocar fere)
  - Maré de gravidade: os anéis de baixa gravidade giram e mudam de lugar
  - Apagão (fase 2): absorve a luz; só relíquias, estrelas e o núcleo brilham, e cometas caem do teto
  - Chama estelar (fase 3): fogo branco sobe por baixo enquanto as plataformas do trono flutuam para cima
- **Janela de vulnerabilidade:** O núcleo (sol negro) só abre quando um raio de constelação é refletido de volta: Lume fica atrás de um espelho no momento do disparo e o raio volta para o núcleo, que se abre por 2 s — pisão no núcleo. Na fase 3 o núcleo fica exposto no topo da subida por 2 s a cada ciclo.
- **Fases e mudança de fase:** Fase 1 — Reflexos (9–7 PV): raios, cópias e maré de gravidade. Fase 2 — Apagão (6–4 PV): escuridão total, cometas, raios mais rápidos; os espelhos brilham levemente para serem achados. Fase 3 — Chama estelar (3–1 PV): o trono desmorona, plataformas sobem com a chama embaixo e o núcleo espera no topo.
- **Derrota (animação):** O sol negro se parte; as dez luzes das fronteiras saem do núcleo, voam até os faróis do mundo e formam no céu a constelação de Lume; amanhece sobre a cidadela e começam os créditos.
- **Relação com a mecânica do mundo:** Síntese: baixa gravidade, constelações, espelhos (Santuário dos Reflexos), escuridão (Pântano) e chama ascendente (Vulcão) num único combate.
- **Implementação:** chefe planejado — nova família de comportamento, entrada `boss: true` no registro (ver seção 6.2 do plano geral), eventos `boss_arena`/`camera_lock` e os requisitos listados na fase `throne_of_eclipse`.

**Minichefe da fase 3:** Guardião da Constelação (elite `charger`, 3 golpes) no salão do mosaico de `gravity_halls`.

## NPC do mundo — Astra, cartógrafa de estrelas

**Função.** Mostra os mapas: projeta no céu o desenho de cada constelação (pista dos blocos ocultos), conta as relíquias de toda a campanha e, com todas as 180, abre a Galeria das Dez Luzes (desafio extra). Narra o prólogo de cada fase e o epílogo depois do Eclipse.

**Falas-guia**
- “O céu desenha o caminho. Bata onde a estrela falta.”
- “Aqui o chão puxa menos. Solte o salto mais cedo.”
- “Cada espelho lembra um lugar por onde você passou.”
- “O Eclipse devolve a luz que reflete. Fique atrás do espelho.”

**Implementação.** Prop animado (cartógrafa com astrolábio) + evento message; os desenhos de constelação são decor na camada back. O contador de relíquias usa o save (Game.found por fase). Não requer motor novo.

## Resumo por fase

### 10-1 · Portão Estrelado (`starlit_gate`) — nova

- **Ideia própria:** o último bolsão de baixa gravidade cobre o vazio entre duas torres.
- **Objetivo:** Apresentar a cidadela: escadarias de luz, bolsões de baixa gravidade demonstrados sobre chão e depois sobre o vazio, canhões e a Sentinela Estelar, que dispara três projéteis em leque.
- **Mecânica principal:** Bolsões de baixa gravidade (zona lowgrav, gravidade × 0,55)
- **Dificuldade / duração / tamanho:** 8/10 · 100–200 s · 5600×1620 u · 2 checkpoint(s)
- **Estreias:** Sentinela Estelar
- **Relíquias:** relíquia relic_tower — pista: Constelação em forma de seta gravada na torre aponta para cima; moedas no bolsão; relíquia relic_observatory e estrela — pista: Cano com um telescópio de latão por cima, apontado para uma estrela piscando; relíquia relic_fan — pista: Três sentinelas alinhadas com uma faixa de moedas entre elas
- **Requisitos de motor:** nenhum
- Seção completa: [`PLANEJAMENTO_60_FASES.md`](PLANEJAMENTO_60_FASES.md#10-1--portão-estrelado-starlit_gate)

### 10-2 · Trilha das Constelações (`constellation_path`) — nova

- **Ideia própria:** revelar a ponte em cadeia: cada estrela revelada é o degrau para bater na próxima.
- **Objetivo:** Explorar trilhas no vazio onde as pontes são constelações de blocos ocultos: o desenho no céu indica onde bater; conhecer o Cometa Errante, que espera no céu e mergulha deixando rastro.
- **Mecânica principal:** Constelações de blocos ocultos: o desenho no céu mostra onde bater; cada bloco revelado vira plataforma
- **Dificuldade / duração / tamanho:** 9/10 · 120–240 s · 6000×2160 u · 3 checkpoint(s)
- **Estreias:** Cometa Errante
- **Relíquias:** relíquia relic_hidden — pista: Uma única estrela pisca fora de qualquer desenho do céu; relíquia relic_planetarium e estrela — pista: Cano com anéis de planeta girando em volta; relíquia relic_low — pista: Rastro de um cometa antigo aponta para baixo, para ilhas menores
- **Requisitos de motor:** nenhum
- Seção completa: [`PLANEJAMENTO_60_FASES.md`](PLANEJAMENTO_60_FASES.md#10-2--trilha-das-constelações-constellation_path)

### 10-3 · Salões da Gravidade (`gravity_halls`) — nova

- **Ideia própria:** vento solar dentro da baixa gravidade leva Lume longe demais.
- **Objetivo:** Desafio de movimento: atravessar salões com faixas de gravidade baixa e normal alternadas, colunas de baixa gravidade como escadas e vento solar, e vencer o Guardião da Constelação no salão final.
- **Mecânica principal:** Faixas alternadas de gravidade baixa e normal (lowgrav) que mudam o arco no meio do salto
- **Dificuldade / duração / tamanho:** 9/10 · 120–240 s · 5600×2160 u · 3 checkpoint(s)
- **Estreias:** Guardião da Constelação
- **Relíquias:** relíquia relic_hourglass — pista: Um relógio de areia flutuante com a areia subindo; relíquia relic_still e estrela — pista: Cano com poeira totalmente parada em volta; relíquia relic_bands — pista: Seis faixas douradas com uma moeda no meio de cada
- **Requisitos de motor:** nenhum
- Seção completa: [`PLANEJAMENTO_60_FASES.md`](PLANEJAMENTO_60_FASES.md#10-3--salões-da-gravidade-gravity_halls)

### 10-4 · Santuário dos Reflexos (`mirror_sanctum`) — nova

- **Ideia própria:** os espelhos do segundo átrio misturam dois mundos na mesma sala.
- **Objetivo:** Mecânica especial da Cidadela das Estrelas: avançar pelo santuário entrando em espelhos-poça que levam a reflexos de mundos anteriores — costa submersa, cavernas e fortalezas — e devolvem Lume do outro lado de abismos intransponíveis.
- **Mecânica principal:** Espelhos-poça (canos de passagem) que levam a salas-reflexo de outros biomas e devolvem Lume adiante
- **Dificuldade / duração / tamanho:** 9/10 · 150–300 s · 6400×2700 u · 3 checkpoint(s)
- **Estreias:** —
- **Relíquias:** relíquia relic_meadow e estrela — pista: Um espelho rachado mostra o céu azul do Reino Verde e flores; relíquia relic_columns — pista: Reflexos das colunas mostram moedas que não existem no chão — estão no topo; relíquia relic_mixed — pista: Placa de Astra: 'sem tomar ar' sobre a sala-reflexo mista
- **Requisitos de motor:** nenhum
- Seção completa: [`PLANEJAMENTO_60_FASES.md`](PLANEJAMENTO_60_FASES.md#10-4--santuário-dos-reflexos-mirror_sanctum)

### 10-5 · Bastião do Eclipse (`eclipse_bastion`) — nova

- **Ideia própria:** cada farol reaceso devolve um pouco de luz ao bastião que escurece.
- **Objetivo:** Desafio avançado final: atravessar o bastião onde o eclipse escurece tudo aos poucos, com dez trechos que combinam em pares as mecânicas das dez fronteiras, reacendendo um farol em cada um.
- **Mecânica principal:** Dez trechos de remix em pares de mecânicas (uma por fronteira) sob escuridão crescente
- **Dificuldade / duração / tamanho:** 10/10 · 160–320 s · 7200×2160 u · 3 checkpoint(s)
- **Estreias:** —
- **Relíquias:** relíquia relic_beacon — pista: Um farol sem cor atrás da muralha; uma estrela pisca fora das constelações; relíquia relic_cistern e estrela — pista: Bolhas subindo num canto escuro da cisterna; relíquia relic_flawless — pista: Os faróis acesos piscam em sequência quando Lume não sofre dano
- **Requisitos de motor:** lights (extensão): a máscara de escuridão das zonas dark com o halo de Lume (120 u; 64 u correndo) já é desenhada; faltam lanternas fixas e acendíveis com raio e duração e o evento lights global (apagar/acender) (desejado: sem a máscara a fase fica jogável e perde a escuridão crescente)
- Seção completa: [`PLANEJAMENTO_60_FASES.md`](PLANEJAMENTO_60_FASES.md#10-5--bastião-do-eclipse-eclipse_bastion)

### 10-6 · Trono do Eclipse (`throne_of_eclipse`) — nova

- **Ideia própria:** a luz do próprio Eclipse, refletida num espelho, abre o seu núcleo.
- **Objetivo:** Fortaleza final: subir a escadaria do trono pelos dez faróis acesos e derrotar o Eclipse Devorador em três fases — reflexos, apagão e chama estelar — devolvendo a luz das dez fronteiras.
- **Mecânica principal:** Escadaria final com todos os sistemas e arena com espelhos que refletem raios
- **Dificuldade / duração / tamanho:** 10/10 · 200–400 s · 6800×2700 u · 3 checkpoint(s)
- **Estreias:** —
- **Relíquias:** relíquia relic_balcony — pista: Dez faróis em fila na varanda, cada um com um pedestal para tocar; relíquia relic_astra e estrela — pista: Cano com astrolábio dourado girando; relíquia relic_stair — pista: Faróis da escadaria piscam em ouro enquanto Lume não sofre dano
- **Requisitos de motor:** comportamento do chefe planejado Eclipse Devorador (eclipse_devorador): família nova em lume/core/behaviors/bosses.py; lights (extensão): a máscara de escuridão das zonas dark com o halo de Lume (120 u; 64 u correndo) já é desenhada; faltam lanternas fixas e acendíveis com raio e duração e o evento lights global (apagar/acender); rising_lava (extensão): a subida única de um perigo por evento já existe (hazard/to/speed, gatilho por x); faltam ciclos de subida e descida, gatilho por altura, tempo ou chefe, aviso sonoro, etapas com pausa, reposição no checkpoint e a variante com zona swim (maré) (variante chama estelar na fase 3)
- Seção completa: [`PLANEJAMENTO_60_FASES.md`](PLANEJAMENTO_60_FASES.md#10-6--trono-do-eclipse-throne_of_eclipse)
