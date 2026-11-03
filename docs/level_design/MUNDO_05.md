# Mundo 5 — Floresta Encantada (`enchanted_forest`)

> Copas luminosas, ruínas e raízes antigas. Bioma `forest`, cor de mapa `#58b98a`, mundo legado 4.
> Plano geral: [`PLANEJAMENTO_60_FASES.md`](PLANEJAMENTO_60_FASES.md) · dados: [`campaign_plan.json`](../../lume/data/plan/campaign_plan.json).

## Identidade

**Reviravolta do mundo.** A floresta se lê em camadas e disfarces: copas, ruínas e raízes escondem blocos, inimigos camuflados e uma lagarta que vira mariposa.

**Paleta**
- verde-esmeralda #58b98a e musgo #3f7a4e
- troncos #6b4a33 e raízes #4a3424
- bioluminescência ciano #73ffe1 e âmbar #ffe27a
- violeta noturno #3a2f5c nas clareiras
- pedra de ruína #9aa39a coberta de hera

**Marcos visuais**
- copas em três alturas com cogumelos luminosos
- ruínas de pedra cobertas de hera e vagalumes
- a Árvore Ancestral, tronco que ocupa várias telas
- pontes de cipó e assentos de cipó balançando sobre a ravina
- clareira dos sussurros com anel de cogumelos
- santuário de raízes em torno de um templo antigo

**Ambiência.** Luz filtrada pelas folhas (L1), entardecer com vagalumes (L2), dia dourado no tronco (L3), névoa na ravina (L4), noite azul na clareira (L5) e brilho de raízes vivas no santuário (L6). Folhas caindo, pólen luminoso, sussurros (áudio posicional).

**Física.** Física padrão. Folhas frágeis (crumble), assentos de cipó (moving eixo x com 60–90 u de alcance), chapéus de cogumelo como molas (spring), raízes e galhos semissólidos. Zonas dark opcionais na clareira (a máscara com o halo de Lume já é desenhada; fungos e lanternas como fontes de luz fixas requerem extensão). Vãos obrigatórios ≤ 150 u.

## Progressão das mecânicas

| Fase | Id | Papel | Foco | Dif. | Ideia própria |
| --- | --- | --- | --- | ---: | --- |
| 5-1 | `glowing_canopy` | apresentação | copas em três alturas, folhas frágeis e quatro moradores apresentados em trechos separados | 5 | Ciranda revela um caminho de blocos ocultos entre as copas |
| 5-2 | `firefly_ruins` | exploração | blocos ocultos marcados por vagalumes, ruínas e o besouro blindado | 5 | a hera esconde um salão inteiro onde os vagalumes entram e não saem |
| 5-3 | `ancestral_tree` | desafio de movimento | duas subidas pelo tronco (blocos e cogumelos-mola) e o guardião da árvore | 6 | a segunda subida pelos cogumelos-mola leva à copa acima de tudo |
| 5-4 | `vine_bridges` | mecânica especial | assentos de cipó e pontes frágeis sobre a ravina (mecânica especial) e o arbusto que investe | 5 | a ponte em espiral desce em volta de um tronco gigante |
| 5-5 | `whispering_hollow` | desafio avançado | descida e subida num tronco oco, aranhas que descem e sussurros que denunciam camuflagem | 6 | descer o tronco oco no escuro e subir de volta pelos chapéus dos cogumelos |
| 5-6 | `root_sanctum` | fortaleza e chefe | raízes que crescem em ritmo e chefe em duas formas (lagarta e mariposa) | 6 | as raízes crescem e recolhem em ritmo como pontes vivas |

## Distribuição de inimigos

★ = estreia da espécie (igual a `introduced_in`); ● = permitida; ◆ = permitida só em sub-área do bioma indicado.

| Espécie | 5-1 | 5-2 | 5-3 | 5-4 | 5-5 | 5-6 |
| --- | :---: | :---: | :---: | :---: | :---: | :---: |
| Bolota (`bolota`) | ● | ● | ● | ● | ● | ● |
| Caramujo-de-Casca (`caramujo`) | ● | ● | ● | ● | ● | ● |
| Besouro-Asa (`besouro_alado`) | ● | ● | ● | ● | ● | ● |
| Besouro (`besouro`) | ● | ● | ● | ● | ● | ● |
| Cogumelo Saltitante (`cogumelo_saltitante`) | ★ | ● | ● | ● | ● | ● |
| Caracol-Musgo (`caracol_musgo`) | ★ | ● | ● | ● | ● | ● |
| Mariposa-Lume (`mariposa_lume`) | ★ | ● | ● | ● | ● | ● |
| Planta-de-Esporos (`planta_esporos`) | ★ | ● | ● | ● | ● | ● |
| Besouro-Casca (`besouro_casca`) |  | ★ | ● | ● | ● | ● |
| Ouriço-Espinho (`ourico_espinho`) |  | ● | ● | ● | ● | ● |
| Guardião da Árvore (`guardiao_arvore`) |  |  | ★ |  |  |  |
| Flor-Mordedora (`flor_mordedora`) |  |  |  | ● | ● | ● |
| Arbusto-Espreita (`arbusto_espreita`) |  |  |  | ★ | ● | ● |
| Aranha-do-Cipó (`aranha_cipo`) |  |  |  |  | ★ | ● |
| Imperatriz Mariposa (chefe planejado) (`boss:imperatriz_mariposa`) |  |  |  |  |  | chefe |

Quantidade planejada de inimigos (sem chefes): 5-1: 6–8 · 5-2: 9–11 · 5-3: 9–12 · 5-4: 16–22 · 5-5: 18–24 · 5-6: 18–24.

## Chefe do mundo — Imperatriz Mariposa (`imperatriz_mariposa`, planejado)

- **Fase:** `root_sanctum`
- **Arena:** Santuário circular dentro do tronco ancestral (1000×1080, fortaleza): três níveis de raízes semissólidas (y448, y336, y224 da arena), parede de raízes ao fundo com buracos, e três flores-lanterna (blocos) nos cantos do nível médio e alto.
- **Ataques:**
  - Rastejo em espiral (forma lagarta): percorre os três níveis; os segmentos laterais são espinhosos
  - Chuva de casulos (lagarta): sacode o teto e derruba casulos que eclodem em mariposas-lume
  - Mordida da raiz (lagarta): emerge de um buraco na parede (folhas tremendo como aviso de 0,6 s)
  - Pó de luz (mariposa): bate as asas e espalha pó luminoso em leque (projéteis lentos em arco)
  - Rasante (mariposa): mergulha em arco sobre o nível do meio
  - Vendaval de asas (mariposa): rajada horizontal de 1,5 s
- **Janela de vulnerabilidade:** Forma lagarta: um segmento-lanterna brilha em sequência ao longo do corpo; pisá-lo quando passa no nível de baixo causa dano. Forma mariposa: ela pousa numa flor-lanterna acesa para beber luz (2 s de asas fechadas) — pisão no dorso; Lume pode apagar duas das três flores batendo nelas por baixo para escolher onde ela pousa.
- **Fases e mudança de fase:** Fase 1 — lagarta (6–4 PV): rastejo, casulos e mordidas. Transição: com 3 PV sobe ao teto e forma um casulo (6 s de pausa com mariposas comuns). Fase 2 — mariposa (3–1 PV): pó de luz, rasantes e vendaval; pousos cada vez mais curtos.
- **Derrota (animação):** A mariposa se desfaz em mil vagalumes que sobem pelo tronco e reacendem as copas da floresta; as raízes se abrem revelando a saída e o farol da fronteira 5 brota como uma flor de luz.
- **Relação com a mecânica do mundo:** Verticalidade em camadas, luz que revela e camuflagem/metamorfose — o mundo inteiro ensinou a ler o que parece outra coisa.
- **Implementação:** chefe planejado — nova família de comportamento, entrada `boss: true` no registro (ver seção 6.2 do plano geral), eventos `boss_arena`/`camera_lock` e os requisitos listados na fase `root_sanctum`.

**Minichefe da fase 3:** Guardião da Árvore (família `guardian`, implementado): avança, salta e dispara; abre a guarda periodicamente (janela de pisão), mais rápido na segunda metade.

## NPC do mundo — Ciranda, vaga-lume anciã das copas

**Função.** Explica os segredos: vagalumes se reúnem onde há blocos ocultos e passagens escondidas. Depois de cada checkpoint ela voa até a área do segredo mais próximo e pousa ali por alguns segundos; nas ruínas, ensina que 'onde a luz se junta, há chão invisível'.

**Falas-guia**
- “Onde a luz se junta, há chão invisível.”
- “O arbusto que pisca não é arbusto.”
- “Escute: quem sussurra está escondido perto.”
- “A lagarta brilha onde dói. A mariposa pousa para beber luz.”

**Implementação.** Partícula/prop animado que segue um caminho até a coordenada do segredo + evento message. Não requer motor novo.

## Resumo por fase

### 5-1 · Copas Luminosas (`glowing_canopy`) — legada 4-1

- **Ideia própria:** Ciranda revela um caminho de blocos ocultos entre as copas.
- **Objetivo:** Apresentar a floresta em camadas — chão contínuo por trechos e copas de folhas frágeis — e quatro moradores, cada um em seu trecho; a terceira relíquia ensina a seguir os vagalumes.
- **Mecânica principal:** Copas de folhas frágeis em três alturas (crumble) acima de um chão contínuo por trechos
- **Dificuldade / duração / tamanho:** 5/10 · 70–150 s · 4000×1240 u · 1 checkpoint(s)
- **Estreias:** Cogumelo Saltitante, Caracol-Musgo, Mariposa-Lume, Planta-de-Esporos
- **Relíquias:** relíquia relic_high (x949, y220) — pista: Trilha de moedas sobe pelas folhas frágeis; relíquia relic_firefly (x2360, y260) — pista: Vagalumes se reúnem num ponto vazio sobre o chão em x2300 (Ciranda pousa ali depois do checkpoint); relíquia relic_room (x3508, y850) e estrela — pista: Cano com seta luminosa entre samambaias
- **Requisitos de motor:** nenhum
- Seção completa: [`PLANEJAMENTO_60_FASES.md`](PLANEJAMENTO_60_FASES.md#5-1--copas-luminosas-glowing_canopy)

### 5-2 · Ruínas dos Vagalumes (`firefly_ruins`) — legada 4-2

- **Ideia própria:** a hera esconde um salão inteiro onde os vagalumes entram e não saem.
- **Objetivo:** Explorar ruínas cobertas de musgo onde os vagalumes marcam blocos ocultos, enfrentar o Besouro-Casca (blindado, 2 golpes) em chão aberto e achar três segredos de tipos diferentes.
- **Mecânica principal:** Blocos ocultos marcados por vagalumes e escadarias de ruína
- **Dificuldade / duração / tamanho:** 5/10 · 80–170 s · 4500×1240 u · 2 checkpoint(s)
- **Estreias:** Besouro-Casca
- **Relíquias:** relíquia relic_high (x1142, y238) — pista: Trilha de moedas sobe pelos tijolos; relíquia relic_ivy — pista: Vagalumes entram na cortina de hera e não saem do outro lado; relíquia relic_room (x2158, y850) e fogo — pista: O cano revela um salão entre as ruínas (dica existente)
- **Requisitos de motor:** nenhum
- Seção completa: [`PLANEJAMENTO_60_FASES.md`](PLANEJAMENTO_60_FASES.md#5-2--ruínas-dos-vagalumes-firefly_ruins)

### 5-3 · A Árvore Ancestral (`ancestral_tree`) — legada 4-3

- **Ideia própria:** a segunda subida pelos cogumelos-mola leva à copa acima de tudo.
- **Objetivo:** Desafio de movimento: duas subidas distintas pela Árvore Ancestral — blocos e plataformas na primeira, chapéus de cogumelo-mola na segunda, até a copa — e o Guardião da Árvore (6 PV).
- **Mecânica principal:** Subidas verticais curtas por blocos, plataformas móveis e chapéus de cogumelo-mola (spring)
- **Dificuldade / duração / tamanho:** 6/10 · 90–180 s · 4700×1240 u · 2 checkpoint(s)
- **Estreias:** Guardião da Árvore
- **Relíquias:** relíquia relic_high (x2232, y224) — pista: Ganhe altura para alcançar a relíquia (dica existente); moedas pelos blocos; relíquia relic_crown (x2700, y110) — pista: Cogumelos de chapéu vermelho com pintas brilhantes formam uma escada até a copa; relíquia relic_room (x2908, y850) e estrela — pista: Cano entre raízes com seta luminosa
- **Requisitos de motor:** nenhum
- Seção completa: [`PLANEJAMENTO_60_FASES.md`](PLANEJAMENTO_60_FASES.md#5-3--a-árvore-ancestral-ancestral_tree)

### 5-4 · Pontes de Cipó (`vine_bridges`) — nova

- **Ideia própria:** a ponte em espiral desce em volta de um tronco gigante.
- **Objetivo:** Mecânica especial da Floresta Encantada: atravessar uma ravina por assentos de cipó que balançam e pontes de tábuas frágeis, e conhecer o Arbusto-Espreita, que parece um arbusto até abrir os olhos.
- **Mecânica principal:** Assentos de cipó balançando (moving eixo x, alcance 60–90 u, velocidade 1,2) e pontes de tábuas frágeis que se refazem
- **Dificuldade / duração / tamanho:** 5/10 · 100–200 s · 5800×2160 u · 2 checkpoint(s)
- **Estreias:** Arbusto-Espreita
- **Relíquias:** relíquia relic_nest — pista: Ninho com ovo dourado no cipó mais alto, visível no topo do balanço; relíquia relic_trunk e estrela — pista: Nó do tronco em forma de olho com vagalumes saindo; relíquia relic_bridge — pista: Placa de madeira: 'Quem não para, não cai' e moedas ao longo de 600 u de tábuas
- **Requisitos de motor:** nenhum
- Seção completa: [`PLANEJAMENTO_60_FASES.md`](PLANEJAMENTO_60_FASES.md#5-4--pontes-de-cipó-vine_bridges)

### 5-5 · Clareira dos Sussurros (`whispering_hollow`) — nova

- **Ideia própria:** descer o tronco oco no escuro e subir de volta pelos chapéus dos cogumelos.
- **Objetivo:** Desafio avançado: descer por dentro de um tronco oco e subir de volta, combinando aranhas que descem do teto, inimigos camuflados denunciados por sussurros e cogumelos-mola, com pouca luz.
- **Mecânica principal:** Descida e subida vertical dentro de um tronco oco (semissólidos de fungo, cogumelos-mola) sob ameaça de cima
- **Dificuldade / duração / tamanho:** 6/10 · 110–220 s · 5800×2160 u · 2 checkpoint(s)
- **Estreias:** Aranha-do-Cipó
- **Relíquias:** relíquia relic_ring — pista: Anel de 7 cogumelos que acendem um por vez numa sequência; relíquia relic_hollow — pista: Vagalumes de Ciranda pousam num ponto vazio no escuro do fundo do oco; relíquia relic_nest e estrela — pista: Raiz oca com teia brilhante na entrada
- **Requisitos de motor:** lights (extensão): a máscara de escuridão das zonas dark com o halo de Lume (120 u; 64 u correndo) já é desenhada; faltam lanternas fixas e acendíveis com raio e duração e o evento lights global (apagar/acender) (opcional: sem a máscara a fase fica jogável e mais clara)
- Seção completa: [`PLANEJAMENTO_60_FASES.md`](PLANEJAMENTO_60_FASES.md#5-5--clareira-dos-sussurros-whispering_hollow)

### 5-6 · Santuário das Raízes (`root_sanctum`) — nova

- **Ideia própria:** as raízes crescem e recolhem em ritmo como pontes vivas.
- **Objetivo:** Fortaleza da Floresta Encantada: atravessar o templo envolvido por raízes vivas que crescem em ritmo, usar tudo da floresta e derrotar a Imperatriz Mariposa em suas duas formas.
- **Mecânica principal:** Raízes vivas como plataformas que sobem e descem em ritmo (moving eixo y com fases encadeadas)
- **Dificuldade / duração / tamanho:** 6/10 · 150–300 s · 6400×1620 u · 2 checkpoint(s)
- **Estreias:** —
- **Relíquias:** relíquia relic_roof — pista: Raízes com flores-lanterna formam degraus até o teto do salão; relíquia relic_altar e estrela — pista: Raízes secas e quebradiças com luz ciano vazando entre elas; relíquia relic_cocoon — pista: Casulos dormindo com 'zzz' de pólen; placa de Ciranda: 'não acorde ninguém'
- **Requisitos de motor:** comportamento do chefe planejado Imperatriz Mariposa (imperatriz_mariposa): família nova em lume/core/behaviors/bosses.py; breakable walls: paredes quebráveis por casco, fogo ou investida (segredos) (só para o segredo do altar)
- Seção completa: [`PLANEJAMENTO_60_FASES.md`](PLANEJAMENTO_60_FASES.md#5-6--santuário-das-raízes-root_sanctum)
