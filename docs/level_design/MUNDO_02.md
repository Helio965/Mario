# Mundo 2 — Deserto Dourado (`golden_desert`)

> Dunas, cânions, vento e templos. Bioma `desert`, cor de mapa `#e7b45c`, mundo legado 2.
> Plano geral: [`PLANEJAMENTO_60_FASES.md`](PLANEJAMENTO_60_FASES.md) · dados: [`campaign_plan.json`](../../lume/data/plan/campaign_plan.json).

## Identidade

**Reviravolta do mundo.** O vento vira regra — primeiro empurra a favor, depois sopra em rajadas e troca de lado — enquanto a areia esconde emboscadas que culminam no Escaravelho-Rei.

**Paleta**
- areia #e7b45c com cristas #f6d58e e sombras violeta #7a5a8c
- arenito #c98d4f e arenito escuro #8e5a33
- céu turquesa-pálido #9ad7e8 → laranja #f2a65a ao entardecer
- verde-oásis #3fae7a e água #5fc9d8 (decorativa)
- marcas de segredo: glifos de sol em dourado #ffd36e

**Marcos visuais**
- dunas em camadas com cristas sopradas
- cânion estratificado com pontes de corda
- colunas e templos de arenito com glifos originais de sol e lua
- birutas (mangas de vento) que mostram as rajadas
- oásis soterrado com palmeiras e poço
- pirâmide com óculo no topo

**Ambiência.** Calor tremulando no horizonte (camada atmosfera), areia correndo em faixas na direção do vento, tempestade alaranjada em sandstorm_pass, penumbra de tochas no oásis e na pirâmide. Sons de vento, sinos de caravana e areia escorrendo.

**Física.** Física padrão. Vento lateral por zonas wind (force_x ±50 a ±140 u/s, rajadas com period/duty); redemoinhos e térmicas por force_y ≈ −1900 (sobem devagar contra a gravidade). Areia movediça (zona quicksand: anda a 45%, pula a 62% do salto, afunda ~36 u/s e mata ao cobrir Lume) a partir do oásis. Água dos canais é letal, exceto a lagoa do oásis (zona swim, prévia do Mundo 3). Vãos obrigatórios ≤ 150 u, vencíveis sem a rajada a favor (exceção documentada: o vão de 200 u sob vento contínuo de sandstorm_pass).

## Progressão das mecânicas

| Fase | Id | Papel | Foco | Dif. | Ideia própria |
| --- | --- | --- | --- | ---: | --- |
| 2-1 | `windswept_dunes` | apresentação | vento constante a favor (apresentação segura), primeiros inimigos do deserto e espinhos | 2 | o vento aparece primeiro como aliado e um redemoinho leva a um segredo |
| 2-2 | `canyon_bridges` | exploração | pontes frágeis, chama oscilante e térmica opcional no cânion | 3 | o cânion respira: uma térmica sobe do fundo e leva a um ninho |
| 2-3 | `sand_temple` | desafio de movimento | inimigo blindado com ciclo e guardião do templo | 3 | a força de Lume grande abre o teto de tijolos do templo |
| 2-4 | `sandstorm_pass` | mecânica especial | rajadas com período e direção alternada — a mecânica especial do mundo | 3 | no olho da tempestade o vento troca de lado a cada 2 s |
| 2-5 | `sunken_oasis` | desafio avançado | areia movediça, lagoa (prévia do nado) e atirador em arco | 3 | a lagoa do oásis é a primeira água em que se nada — e guarda uma relíquia no fundo |
| 2-6 | `scarab_pyramid` | fortaleza e chefe | armadilhas de pirâmide e chefe de emboscada sob a areia | 3 | a laje sobre a armadilha de areia antecipa o chão que o chefe vai fazer tremer |

## Distribuição de inimigos

★ = estreia da espécie (igual a `introduced_in`); ● = permitida; ◆ = permitida só em sub-área do bioma indicado.

| Espécie | 2-1 | 2-2 | 2-3 | 2-4 | 2-5 | 2-6 |
| --- | :---: | :---: | :---: | :---: | :---: | :---: |
| Escaravelho-de-Areia (`escaravelho_areia`) | ★ | ● | ● | ● | ● | ● |
| Tatu-Bola (`tatu_bola`) | ★ | ● | ● | ● | ● | ● |
| Cacto Sentinela (`cacto_sentinela`) | ★ | ● | ● | ● | ● | ● |
| Abutrinho (`abutre_filhote`) |  | ★ | ● | ● | ● | ● |
| Ouriço-Espinho (`ourico_espinho`) |  | ● | ● | ● | ● | ● |
| Escorpião-Couraça (`escorpiao_couraca`) |  |  | ★ | ● | ● | ● |
| Guardião do Templo (`guardiao_templo`) |  |  | ★ |  |  |  |
| Serpente-de-Duna (`serpente_duna`) |  |  |  | ★ | ● | ● |
| Escaravelho Lançador (`escaravelho_lancador`) |  |  |  |  | ★ | ● |
| Escaravelho-Rei (`escaravelho_rei`) |  |  |  |  |  | ★ |

Quantidade planejada de inimigos (sem chefes): 2-1: 5–6 · 2-2: 6–8 · 2-3: 5–7 · 2-4: 10–14 · 2-5: 12–16 · 2-6: 7–10.

## Chefe do mundo — Escaravelho-Rei (`escaravelho_rei`, implementado)

- **Fase:** `scarab_pyramid`
- **Arena:** Câmara da pirâmide entre os pilares x3000 e x3880 (840 u de chão de areia contínuo), portões de pedra (switch gate_left/gate_right) fechados pelo evento boss_arena e câmera travada em [2960, 0, 960, 540]; sem vãos.
- **Ataques:**
  - Nado sob a areia: intangível, segue Lume a até 180 u/s por 1,3 s (0,9 s na fase 2)
  - Irrupção: jato de areia sob Lume como aviso (0,65 s; 0,45 s na fase 2) e salto para fora (impulso 640 u/s) com carapaça espinhosa
  - Rolamento: depois de se recompor, enrola-se e rola a 300 u/s (380 na fase 2), ricocheteando numa parede; para após duas batidas
  - Bolas de areia (fase 2): ao irromper, lança três bolas de areia em arco (−200, 0, +200 u/s)
- **Janela de vulnerabilidade:** Depois de cada irrupção cai de costas, atordoado, por 1,6 s (1,1 s na fase 2): única janela de pisão (fraqueza só a pisão). Após cada golpe é empurrado para o centro da arena (0,9 s, intangível) e volta a nadar sob a areia.
- **Fases e mudança de fase:** Despertar: dorme até Lume chegar a 420 u e faz uma introdução de 1,2 s. Fase 1 (3→2 PV): nado longo, aviso de 0,65 s, rolamento a 300 u/s. Fase 2 (≤ metade da vida): nado curto, aviso de 0,45 s, rolamento a 380 u/s e três bolas de areia por irrupção.
- **Derrota (animação):** Planejado para a arte: a carapaça dourada racha em placas, o escaravelho afunda na areia deixando só um escaravelho comum que foge; o portão direito sobe e um feixe de sol atravessa o topo da pirâmide (farol da fronteira 2).
- **Relação com a mecânica do mundo:** Areia do Deserto Dourado: o ritmo rastro → aviso → irrupção ensinado pelo Escaravelho-de-Areia e pela Serpente-de-Duna vira a leitura do chefe; o rolamento retoma o casco do Tatu-Bola.
- **Implementação:** família `scarab_king` em `lume/core/behaviors/bosses.py` (implementada, entrada `escaravelho_rei` no registro); a fase `scarab_pyramid` já declara `boss_arena` com portões `gate_left`/`gate_right`.

**Minichefe da fase 3:** Guardião do Templo (família `guardian`, implementado): avança, salta e dispara; abre a guarda periodicamente (janela de pisão), mais rápido na segunda metade.

## NPC do mundo — Mestra Sálvia, arqueóloga do Deserto Dourado

**Função.** Explica as relíquias: cada fase guarda três, e cada uma tem uma marca (glifo de sol, tijolo rachado, manilha com fitas). Ela aparece no checkpoint com um caderno que mostra quantas relíquias da fase já foram achadas e comenta a pista mais próxima. Em sandstorm_pass ensina a ler a biruta.

**Falas-guia**
- “Toda relíquia deixa uma marca. Procure o sol gravado na pedra.”
- “Tijolos rachados cedem a quem tem força.”
- “Leia a biruta: cheia é rajada, murcha é calmaria.”
- “Ele nada na areia como os escaravelhos pequenos: siga o jato de areia.”

**Implementação.** Prop animado (tenda e caderno) + evento message no checkpoint; o contador de relíquias usa Game.found. Não requer motor novo.

## Resumo por fase

### 2-1 · Dunas ao Vento (`windswept_dunes`) — legada 2-1

- **Ideia própria:** o vento aparece primeiro como aliado e um redemoinho leva a um segredo.
- **Objetivo:** Apresentar o deserto: correr entre dunas com vento a favor, conhecer os primeiros habitantes (bola que rola, escaravelho que se enterra, cacto que dispara) e os espinhos, e descobrir que o vento também levanta.
- **Mecânica principal:** Vento lateral constante a favor (zona wind sem período) e leitura de inimigos do deserto
- **Dificuldade / duração / tamanho:** 2/10 · 55–120 s · 3800×1240 u · 1 checkpoint(s)
- **Estreias:** Escaravelho-de-Areia, Tatu-Bola, Cacto Sentinela
- **Relíquias:** relíquia relic_high (x1530, y220 após o ajuste) — pista: Trilha de moedas sobe pela escada de arenito; glifo de sol no tijolo do topo; relíquia relic_devil (x3330, y160) na duna alta — pista: Coluna de areia rodopiando com moedas em coluna dentro dela; penas subindo; relíquia relic_room (x3468, y850) e coração — pista: Cano com seta luminosa e fitas de pano
- **Requisitos de motor:** nenhum
- Seção completa: [`PLANEJAMENTO_60_FASES.md`](PLANEJAMENTO_60_FASES.md#2-1--dunas-ao-vento-windswept_dunes)

### 2-2 · Pontes do Cânion (`canyon_bridges`) — legada 2-2

- **Ideia própria:** o cânion respira: uma térmica sobe do fundo e leva a um ninho.
- **Objetivo:** Explorar o cânion em terraços que sobem e descem, com pontes frágeis, a primeira chama oscilante e o voador do deserto; corrigir o salto sobre o tatu que batia a cabeça e somar uma rota térmica opcional.
- **Mecânica principal:** Terraços em desnível (±32 u) ligados por pontes frágeis e plataformas móveis
- **Dificuldade / duração / tamanho:** 3/10 · 65–140 s · 4100×1240 u · 2 checkpoint(s)
- **Estreias:** Abutrinho
- **Relíquias:** relíquia relic_high (x954, y250) — pista: Trilha de moedas sobe pelas pedras frágeis; glifo de sol na parede; relíquia relic_nest (x2780, y180) — pista: Penas e grãos de areia sobem em espiral no vão x2740–2860; moedas em coluna; relíquia relic_room (x3438, y850) e estrela — pista: Cano com seta luminosa
- **Requisitos de motor:** nenhum
- Seção completa: [`PLANEJAMENTO_60_FASES.md`](PLANEJAMENTO_60_FASES.md#2-2--pontes-do-cânion-canyon_bridges)

### 2-3 · Templo das Areias (`sand_temple`) — legada 2-3

- **Ideia própria:** a força de Lume grande abre o teto de tijolos do templo.
- **Objetivo:** Desafio de movimento no templo: escadaria arqueológica, o primeiro inimigo blindado com ciclo (escorpião) e o Guardião do Templo (4 PV); a terceira relíquia exige quebrar tijolos rachados.
- **Mecânica principal:** Inimigo blindado com janela periódica (cauda erguida 35% do ciclo de 3 s) e guardião do templo
- **Dificuldade / duração / tamanho:** 3/10 · 70–150 s · 4200×1240 u · 2 checkpoint(s)
- **Estreias:** Escorpião-Couraça, Guardião do Templo
- **Relíquias:** relíquia relic_high (x1332, y220) — pista: Trilha de moedas sobe pela escadaria; glifo de sol no último degrau; relíquia relic_sun (x2500, y160) — pista: Tijolos com rachaduras em forma de sol e areia escorrendo entre eles; Mestra Sálvia: 'tijolos rachados cedem a quem tem força'; relíquia relic_room (x2688, y850) e coração — pista: Cano com seta luminosa
- **Requisitos de motor:** nenhum
- Seção completa: [`PLANEJAMENTO_60_FASES.md`](PLANEJAMENTO_60_FASES.md#2-3--templo-das-areias-sand_temple)

### 2-4 · Passagem da Tempestade (`sandstorm_pass`) — nova

- **Ideia própria:** no olho da tempestade o vento troca de lado a cada 2 s.
- **Objetivo:** Mecânica especial do Deserto Dourado: atravessar a passagem durante a tempestade lendo o vento — trechos de vento constante a favor e rajadas contrárias com período — e conhecer a Serpente-de-Duna, que viaja sob a areia.
- **Mecânica principal:** Vento lateral por zonas wind: constante a favor (+80/+140 u/s) e rajadas contrárias com período (−120/−130 u/s; 3,6 s/0,45 e 3,2 s/0,5)
- **Dificuldade / duração / tamanho:** 3/10 · 85–170 s · 5600×1240 u · 2 checkpoint(s)
- **Estreias:** Serpente-de-Duna
- **Relíquias:** relíquia relic_gust (x3140, y312) — pista: Moedas soltas no ar sobre o vão do vento a favor; relíquia relic_ruins (x4282, y216) — pista: Colunas caídas formam degraus contra o vento; relíquia relic_room (x3958, y850) e coração — pista: Manilha com seta luminosa e fitas de tecido tremulando
- **Requisitos de motor:** nenhum
- Seção completa: [`PLANEJAMENTO_60_FASES.md`](PLANEJAMENTO_60_FASES.md#2-4--passagem-da-tempestade-sandstorm_pass)

### 2-5 · Oásis Soterrado (`sunken_oasis`) — nova

- **Ideia própria:** a lagoa do oásis é a primeira água em que se nada — e guarda uma relíquia no fundo.
- **Objetivo:** Desafio avançado do deserto: atravessar o oásis soterrado combinando poças de areia movediça, palmeiras como plataformas de mão única, uma lagoa onde se nada e o Escaravelho Lançador, que arremessa bolas de areia em arco.
- **Mecânica principal:** Poças de areia movediça (zonas quicksand de 80 u sobre leito a −72 u) que exigem sair saltando
- **Dificuldade / duração / tamanho:** 3/10 · 95–190 s · 6000×1240 u · 2 checkpoint(s)
- **Estreias:** Escaravelho Lançador
- **Relíquias:** relíquia relic_pond (x1690, y586) — pista: Brilho no fundo da lagoa entre juncos; relíquia relic_palms (x4990, y172) — pista: Copas de palmeiras em escada com moedas; relíquia relic_room (x5218, y850) e estrela — pista: Cano com seta luminosa junto às palmeiras verdes
- **Requisitos de motor:** nenhum
- Seção completa: [`PLANEJAMENTO_60_FASES.md`](PLANEJAMENTO_60_FASES.md#2-5--oásis-soterrado-sunken_oasis)

### 2-6 · Pirâmide do Escaravelho (`scarab_pyramid`) — nova

- **Ideia própria:** a laje sobre a armadilha de areia antecipa o chão que o chefe vai fazer tremer.
- **Objetivo:** Fortaleza do Deserto Dourado: atravessar o interior da pirâmide com armadilhas de areia, chamas oscilantes e uma galeria de tijolos, e derrotar o Escaravelho-Rei, que nada sob a areia e só pode ser pisado quando cai de costas.
- **Mecânica principal:** Armadilhas de pirâmide (fosso de espinhos sob ponte frágil, poça de areia, chamas oscilantes) antes de um chefe de emboscada subterrânea
- **Dificuldade / duração / tamanho:** 3/10 · 120–240 s · 4600×1240 u · 2 checkpoint(s)
- **Estreias:** Escaravelho-Rei
- **Relíquias:** relíquia relic_trap (x1030, y330) — pista: Laje sobre a armadilha de areia com moedas; relíquia relic_gallery (x2672, y190) — pista: Escada de tijolos sobe até a galeria; glifo de sol no último degrau; relíquia relic_room (x2648, y850) e coração — pista: Cano com seta luminosa entre tochas
- **Requisitos de motor:** nenhum
- Seção completa: [`PLANEJAMENTO_60_FASES.md`](PLANEJAMENTO_60_FASES.md#2-6--pirâmide-do-escaravelho-scarab_pyramid)
