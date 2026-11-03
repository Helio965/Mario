# Mundo 9 — Fortaleza Vulcânica (`volcanic_fortress`)

> Basalto, brasa e magma ascendente. Bioma `volcano`, cor de mapa `#e5734a`, mundo legado 5.
> Plano geral: [`PLANEJAMENTO_60_FASES.md`](PLANEJAMENTO_60_FASES.md) · dados: [`campaign_plan.json`](../../lume/data/plan/campaign_plan.json).

## Identidade

**Reviravolta do mundo.** O fim da campanha antiga vira o começo do domínio: o fogo de Lume para de funcionar contra quase tudo, o magma passa a subir e o chefe esfria só depois de atacar.

**Paleta**
- basalto #3a3036 e obsidiana #1f1a24
- magma #e5734a / #ffb35c com brilho #ffe08a
- cinza vulcânica #8a8580
- bronze dos sinos #b8863b
- luz de Lume em turquesa #35c9b4 (contraste máximo com o laranja)

**Marcos visuais**
- pontes de basalto sobre canais de lava
- fornalhas com bocas de gárgula
- a cidadela da Última Chama
- forja vertical com marcas de bronze do nível do magma
- corredor de cinzas com abrigos de basalto
- trono de magma sobre um lago incandescente

**Ambiência.** Calor tremulando, brasas subindo (weather embers), estrondos graves, sinos de bronze anunciando o magma, chuva de cinzas no corredor e o lago de magma pulsando no trono.

**Física.** Lava e quedas matam; chamas oscilantes ferem; Brasa Andante, Boca-de-Fornalha e Golem são imunes ao fogo (o fogo de Lume serve só contra o Ermitão-de-Basalto e os morcegos; ossadas só caem com casco ou estrela); magma ascendente (rising_lava: a subida única por evento já existe; etapas com pausa, gatilho por altura e reposição no checkpoint requerem extensão) sobe por etapas anunciadas pelo sino; rajadas de cinza = zonas wind com período. Vãos obrigatórios ≤ 160 u (W9).

## Progressão das mecânicas

| Fase | Id | Papel | Foco | Dif. | Ideia própria |
| --- | --- | --- | --- | ---: | --- |
| 9-1 | `basalt_bridges` | apresentação | canais de lava e quatro moradores resistentes, um por ponte | 8 | a nova ponte levadiça sobre o rio de lava no fim |
| 9-2 | `echo_furnace` | exploração | galerias frágeis, chamas em dupla e morcegos; rota alta dos ecos | 8 | a galeria dos ecos: uma rota alta inteira acima das fornalhas |
| 9-3 | `last_flame` | desafio de movimento | síntese da campanha antiga e guardião de três disparos | 9 | a rota da chama ancestral passa por cima dos dois últimos canais |
| 9-4 | `rising_magma` | mecânica especial | magma que sobe por etapas e Salta-Brasas (mecânica especial) | 8 | o magma recua e é preciso descer antes que volte |
| 9-5 | `ash_gauntlet` | desafio avançado | corredor longo com rajadas de cinza e cascos atravessando a lava | 9 | blocos do Ermitão-de-Basalto chutados por cima da lava limpam a margem de lá |
| 9-6 | `magma_throne` | fortaleza e chefe | lago de magma em ciclos e chefe que esfria depois de atacar | 9 | as ilhas do trono afundam e voltam com a maré de magma |

## Distribuição de inimigos

★ = estreia da espécie (igual a `introduced_in`); ● = permitida; ◆ = permitida só em sub-área do bioma indicado.

| Espécie | 9-1 | 9-2 | 9-3 | 9-4 | 9-5 | 9-6 |
| --- | :---: | :---: | :---: | :---: | :---: | :---: |
| Brasa Andante (`brasa_andante`) | ★ | ● | ● | ● | ● | ● |
| Ermitão-de-Basalto (`tartaruga_basalto`) | ★ | ● | ● | ● | ● | ● |
| Boca-de-Fornalha (`boca_fornalha`) | ★ | ● | ● | ● | ● | ● |
| Golem de Basalto (`golem_basalto`) | ★ | ● | ● | ● | ● | ● |
| Ossada do Pântano (`ossada_pantano`) | ● | ● | ● | ● | ● | ● |
| Morcego-Brasa (`morcego_brasa`) |  | ★ | ● | ● | ● | ● |
| Guardião da Última Chama (`guardiao_chama`) |  |  | ★ |  |  |  |
| Salta-Brasa (`bolha_magma`) |  |  |  | ★ | ● | ● |
| Canhão Sentinela (`sentinela_canhao`) |  |  |  |  |  | ◆ fortress |
| Prensa a Vapor (`prensa_vapor`) |  |  |  |  |  | ◆ fortress |
| Salamandra Caldera (chefe planejado) (`boss:salamandra_caldera`) |  |  |  |  |  | chefe |

Quantidade planejada de inimigos (sem chefes): 9-1: 12–16 · 9-2: 14–18 · 9-3: 14–18 · 9-4: 14–20 · 9-5: 24–30 · 9-6: 22–28.

## Chefe do mundo — Salamandra Caldera (`salamandra_caldera`, planejado)

- **Fase:** `magma_throne`
- **Arena:** Sala do trono (1000×1080, fortaleza): lago de magma com cinco ilhas de basalto (três fixas, duas que afundam na maré), o trono ao fundo e correntes do teto com argolas como plataformas altas.
- **Ataques:**
  - Onda de magma: mergulha e levanta uma onda que corre pelo lago e cobre as ilhas baixas
  - Sopro de brasas: cospe três projéteis em arco (aviso: garganta brilhando por 0,6 s)
  - Chicote da cauda: varre uma ilha inteira (aviso: cauda erguida)
  - Convocação: chama dois Salta-Brasas nas bordas do lago
  - Maré permanente (fase 2): o magma sobe 120 u e as ilhas viram plataformas móveis
- **Janela de vulnerabilidade:** Depois de cada sopro de brasas a pele esfria e vira crosta de basalto por 2 s (fica escura e para de brilhar): pisão na cabeça. Um bloco de Ermitão-de-Basalto chutado também acerta. Fogo não causa dano.
- **Fases e mudança de fase:** Fase 1 (7–4 PV): ondas, sopros, chicotes e convocações, com o lago em maré baixa. Fase 2 (3–1 PV): maré permanente, ilhas móveis, sopro com cinco projéteis e janela de resfriamento de 1,5 s.
- **Derrota (animação):** A crosta se fecha por inteiro e a salamandra vira estátua de obsidiana com uma chama no peito; a chama sobe pelo teto e acende o farol do vulcão — fronteira 9.
- **Relação com a mecânica do mundo:** Magma que sobe e desce, lava como corredor para cascos e o fogo de Lume inútil contra o vulcão: a única arma é o tempo de resfriamento.
- **Implementação:** chefe planejado — nova família de comportamento, entrada `boss: true` no registro (ver seção 6.2 do plano geral), eventos `boss_arena`/`camera_lock` e os requisitos listados na fase `magma_throne`.

**Minichefe da fase 3:** Guardião da Última Chama (família `guardian`, implementado): avança, salta e dispara; abre a guarda periodicamente (janela de pisão), mais rápido na segunda metade.

## NPC do mundo — Brônzio, sineiro das forjas

**Função.** Avisa o magma: toca o sino 2 s antes de cada subida (o som é o telégrafo do evento rising_lava) e pinta faixas de bronze nas paredes marcando a altura segura. Também explica que o fogo de Lume não fere os moradores de brasa e basalto. Aparece no checkpoint e no alto de cada etapa da forja.

**Falas-guia**
- “Ouviu o sino? Suba até a faixa de bronze.”
- “Brasa não queima brasa. Pise ou chute um casco.”
- “O bloco do ermitão atravessa a lava. Chute com vontade.”
- “A salamandra esfria depois de cuspir fogo. É a sua hora.”

**Implementação.** Prop animado (sineiro com martelo) + evento message; o toque do sino é emitido pelo próprio evento rising_lava. Não requer motor novo além do magma.

## Resumo por fase

### 9-1 · Pontes de Basalto (`basalt_bridges`) — legada 5-1

- **Ideia própria:** a nova ponte levadiça sobre o rio de lava no fim.
- **Objetivo:** Abrir o Mundo 9 com o traçado legado endurecido: quatro canais de lava (dois alargados para 150 u), chamas sobre os saltos e quatro moradores resistentes ao fogo, um por ponte; nova seção final de ponte levadiça.
- **Mecânica principal:** Saltos sobre canais de lava com chamas oscilantes cronometrando a decolagem
- **Dificuldade / duração / tamanho:** 8/10 · 90–180 s · 5200×1240 u · 2 checkpoint(s)
- **Estreias:** Brasa Andante, Ermitão-de-Basalto, Boca-de-Fornalha, Golem de Basalto
- **Relíquias:** relíquia relic_high (x2074, y220) — pista: A rota alta contorna a chama (dica legada); moedas na plataforma móvel; relíquia relic_obsidian — pista: Pilares de obsidiana com veios dourados acima da ponte levadiça; relíquia relic_room (x3828, y850) e coração — pista: Cano com seta luminosa entre colunas hexagonais
- **Requisitos de motor:** nenhum
- Seção completa: [`PLANEJAMENTO_60_FASES.md`](PLANEJAMENTO_60_FASES.md#9-1--pontes-de-basalto-basalt_bridges)

### 9-2 · Fornalha dos Ecos (`echo_furnace`) — legada 5-2

- **Ideia própria:** a galeria dos ecos: uma rota alta inteira acima das fornalhas.
- **Objetivo:** Explorar a fornalha em terraços, com galerias frágeis, chamas em dupla e o Morcego-Brasa; somar a galeria dos ecos, uma rota alta contínua, e endurecer os saltos para o mundo 9.
- **Mecânica principal:** Terraços de fornalha com galerias frágeis e chamas em dupla (duas chamas fora de fase)
- **Dificuldade / duração / tamanho:** 8/10 · 100–200 s · 4800×1240 u · 1 checkpoint(s)
- **Estreias:** Morcego-Brasa
- **Relíquias:** relíquia relic_high (x2063, y226) — pista: No alto, avance antes que a pedra se desfaça (dica legada); moedas na galeria; relíquia relic_echo (x3880, y140) — pista: Um sino de bronze toca sozinho no alto quando Lume passa embaixo; relíquia relic_room (x2988, y850) e estrela — pista: Cano com seta luminosa entre gárgulas
- **Requisitos de motor:** nenhum
- Seção completa: [`PLANEJAMENTO_60_FASES.md`](PLANEJAMENTO_60_FASES.md#9-2--fornalha-dos-ecos-echo_furnace)

### 9-3 · A Última Chama (`last_flame`) — legada 5-3

- **Ideia própria:** a rota da chama ancestral passa por cima dos dois últimos canais.
- **Objetivo:** Síntese da campanha antiga elevada ao mundo 9: seis trechos de cidadela com todos os moradores do vulcão e o Guardião da Última Chama (7 PV, três disparos), agora com dois checkpoints e uma rota alta final.
- **Mecânica principal:** Síntese: canais de lava, pedra frágil, plataformas e chamas em sequência sem respiro longo
- **Dificuldade / duração / tamanho:** 9/10 · 120–240 s · 5200×1240 u · 2 checkpoint(s)
- **Estreias:** Guardião da Última Chama
- **Relíquias:** relíquia relic_high (x1420, y220) — pista: Trilha de moedas pela pedra frágil e pela plataforma móvel; relíquia relic_ancestral (x4300, y150) — pista: Um braseiro apagado no alto com fumaça azul; pedras frágeis com veios dourados; relíquia relic_room (x2928, y850) e estrela — pista: Cano com seta luminosa sob um estandarte chamuscado
- **Requisitos de motor:** nenhum
- Seção completa: [`PLANEJAMENTO_60_FASES.md`](PLANEJAMENTO_60_FASES.md#9-3--a-última-chama-last_flame)

### 9-4 · Magma Ascendente (`rising_magma`) — nova

- **Ideia própria:** o magma recua e é preciso descer antes que volte.
- **Objetivo:** Mecânica especial da Fortaleza Vulcânica: escalar a forja vertical enquanto o magma sobe por etapas anunciadas pelo sino de Brônzio, e conhecer a Salta-Brasa, que salta da lava em ritmo fixo.
- **Mecânica principal:** Magma ascendente (rising_lava) em etapas: sino 2 s antes, subida até a próxima faixa de bronze e pausa
- **Dificuldade / duração / tamanho:** 8/10 · 110–220 s · 4200×3240 u · 3 checkpoint(s)
- **Estreias:** Salta-Brasa
- **Relíquias:** relíquia relic_niche — pista: Uma faixa de bronze pintada acima do normal, com moedas brilhando atrás de uma coluna; relíquia relic_escape e estrela — pista: Cano de bronze na parede da câmara de fuga com sino pequeno tocando; relíquia relic_nonstop — pista: Placa de Brônzio: 'sem parar na etapa cinco'
- **Requisitos de motor:** rising_lava (extensão): a subida única de um perigo por evento já existe (hazard/to/speed, gatilho por x); faltam ciclos de subida e descida, gatilho por altura, tempo ou chefe, aviso sonoro, etapas com pausa, reposição no checkpoint e a variante com zona swim (maré)
- Seção completa: [`PLANEJAMENTO_60_FASES.md`](PLANEJAMENTO_60_FASES.md#9-4--magma-ascendente-rising_magma)

### 9-5 · Corredor de Cinzas (`ash_gauntlet`) — nova

- **Ideia própria:** blocos do Ermitão-de-Basalto chutados por cima da lava limpam a margem de lá.
- **Objetivo:** Desafio avançado: atravessar o longo corredor vulcânico sob rajadas de cinza, com abrigos de basalto, todos os moradores do vulcão e trechos em que o único jeito de limpar a outra margem é chutar cascos por cima da lava.
- **Mecânica principal:** Rajadas de cinza (wind lateral com período) sobre trechos de lava, com abrigos de basalto entre elas
- **Dificuldade / duração / tamanho:** 9/10 · 140–280 s · 6800×1620 u · 3 checkpoint(s)
- **Estreias:** —
- **Relíquias:** relíquia relic_tubes e estrela — pista: Fumaça saindo de uma rachadura no chão de um abrigo; relíquia relic_wall — pista: Ameias de uma muralha antiga aparecem por trás da cinza com moedas; relíquia relic_combo — pista: Fileira de 5 inimigos alinhados além da lava e um Ermitão-de-Basalto sozinho na margem
- **Requisitos de motor:** lights (extensão): a máscara de escuridão das zonas dark com o halo de Lume (120 u; 64 u correndo) já é desenhada; faltam lanternas fixas e acendíveis com raio e duração e o evento lights global (apagar/acender) (opcional: nuvens de cinza)
- Seção completa: [`PLANEJAMENTO_60_FASES.md`](PLANEJAMENTO_60_FASES.md#9-5--corredor-de-cinzas-ash_gauntlet)

### 9-6 · Trono de Magma (`magma_throne`) — nova

- **Ideia própria:** as ilhas do trono afundam e voltam com a maré de magma.
- **Objetivo:** Fortaleza da Fortaleza Vulcânica: atravessar o palácio sobre o lago de magma, cuja maré sobe e desce em ciclos, e derrotar a Salamandra Caldera pisando sua cabeça quando ela esfria depois de cuspir fogo.
- **Mecânica principal:** Maré de magma em ciclos (rising_lava sobe e desce) sobre ilhas de basalto
- **Dificuldade / duração / tamanho:** 9/10 · 170–340 s · 6400×2160 u · 2 checkpoint(s)
- **Estreias:** —
- **Relíquias:** relíquia relic_bell — pista: Sino de bronze dourado no alto de uma torre, tocando fora do ritmo; relíquia relic_treasure e estrela — pista: Cano de obsidiana com veios dourados atrás de uma coluna; relíquia relic_tide — pista: Correntes do teto com argolas e moedas acima do lago
- **Requisitos de motor:** comportamento do chefe planejado Salamandra Caldera (salamandra_caldera): família nova em lume/core/behaviors/bosses.py; rising_lava (extensão): a subida única de um perigo por evento já existe (hazard/to/speed, gatilho por x); faltam ciclos de subida e descida, gatilho por altura, tempo ou chefe, aviso sonoro, etapas com pausa, reposição no checkpoint e a variante com zona swim (maré)
- Seção completa: [`PLANEJAMENTO_60_FASES.md`](PLANEJAMENTO_60_FASES.md#9-6--trono-de-magma-magma_throne)
