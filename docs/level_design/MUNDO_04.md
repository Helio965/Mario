# Mundo 4 — Montanhas Geladas (`frozen_peaks`)

> Lagos de cristal, encostas e nevascas. Bioma `snow`, cor de mapa `#9fd3ef`, mundo legado 3.
> Plano geral: [`PLANEJAMENTO_60_FASES.md`](PLANEJAMENTO_60_FASES.md) · dados: [`campaign_plan.json`](../../lume/data/plan/campaign_plan.json).

## Identidade

**Reviravolta do mundo.** O gelo tira o freio: primeiro escorrega, depois vira encosta de embalo, avalanche e, no fim, a pista onde o casco de cristal derrota a morsa.

**Paleta**
- azul-gelo #9fd3ef e azul-profundo #3b5f8f
- branco-neve #f4fbff com sombras lavanda #b9c3e6
- granito #6d7b8c e pedra escura #48525e
- pinheiros #2f6b5a
- acentos de aurora verde #7ef0c0 e violeta #a98cf0 nas cavernas e na cidadela

**Marcos visuais**
- lago congelado com cabana de pesca no gelo
- terraços azuis com pinheiros e pilhas de pedra (marcos)
- abrigos de pedra contra a nevasca
- encostas longas com trilhas de trenó
- cumeeiras com cornijas de neve e cavernas de cristal
- cidadela de geada com vitrais de gelo

**Ambiência.** Manhã clara no lago (L1), céu limpo nos terraços (L2), nevasca horizontal (L3), sol baixo e brilho nas encostas (L4), céu cinzento com estrondos de avalanche (L5) e aurora sobre a cidadela (L6). Neve caindo (weather snow), vapor da respiração, estalos de gelo.

**Física.** Gelo: atrito 180 u/s² (frenagem de 321 u a partir da corrida, contra 38 u no chão normal); regra de ≥ 330 u entre pouso no gelo e o próximo perigo ou uma parede de contenção. Nevasca por zonas wind (−90 u/s, período 4 s) só sobre chão contínuo. Encostas são degraus descendentes de 12 u com arte contínua (o motor não tem rampas). Pingentes (crusher) têm topo seguro.

## Progressão das mecânicas

| Fase | Id | Papel | Foco | Dif. | Ideia própria |
| --- | --- | --- | --- | ---: | --- |
| 4-1 | `crystal_lake` | apresentação | frenagem no gelo e primeiros habitantes do frio | 4 | a patinação vira desafio: parar na ponta do píer congelado |
| 4-2 | `blue_ascent` | exploração | terraços de gelo e rocha, atirador reto (boneco de neve), rota do cume | 4 | uma rota do cume acima dos seis terraços |
| 4-3 | `blizzard_heart` | desafio de movimento | nevasca em rajadas, investidor que bate na pedra e guardião | 5 | a pedra vira abrigo e arma: o carneiro bate nela e fica tonto |
| 4-4 | `slippery_slopes` | mecânica especial | encostas de embalo (mecânica especial), atirador em arco e cascos ricocheteando | 4 | a encosta invertida: subir degraus de gelo que empurram de volta |
| 4-5 | `avalanche_ridge` | desafio avançado | pingentes que despencam, bolas de neve rolando e cornijas frágeis | 5 | o corredor da avalanche: quatro bolas gigantes em fases diferentes e abrigos entre elas |
| 4-6 | `frost_citadel` | fortaleza e chefe | síntese em fortaleza e chefe vencido com casco no gelo | 5 | no salão dos vitrais a luz colorida marca o gelo que não escorrega |

## Distribuição de inimigos

★ = estreia da espécie (igual a `introduced_in`); ● = permitida; ◆ = permitida só em sub-área do bioma indicado.

| Espécie | 4-1 | 4-2 | 4-3 | 4-4 | 4-5 | 4-6 |
| --- | :---: | :---: | :---: | :---: | :---: | :---: |
| Pinguim Patrulheiro (`pinguim_patrulha`) | ★ | ● | ● | ● | ● | ● |
| Caracol-de-Cristal (`caracol_cristal`) | ★ | ● | ● | ● | ● | ● |
| Coruja Nevada (`coruja_nevada`) | ★ | ● | ● | ● | ● | ● |
| Boneco de Neve (`boneco_neve`) |  | ★ | ● | ● | ● | ● |
| Carneiro Glacial (`carneiro_glacial`) |  |  | ★ | ● | ● | ● |
| Guardião da Nevasca (`guardiao_nevasca`) |  |  | ★ |  |  |  |
| Yeti-Mirim (`yeti_mirim`) |  |  |  | ★ | ● | ● |
| Pingente de Gelo (`pingente_queda`) |  |  |  |  | ★ | ● |
| Morsa Gelomar (`morsa_gelomar`) |  |  |  |  |  | ★ |

Quantidade planejada de inimigos (sem chefes): 4-1: 5–6 · 4-2: 6–8 · 4-3: 7–9 · 4-4: 14–18 · 4-5: 18–24 · 4-6: 18–24.

## Chefe do mundo — Morsa Gelomar (`morsa_gelomar`, planejado)

- **Fase:** `frost_citadel`
- **Arena:** Salão do trono (1000×1080, fortaleza): piso de gelo espelhado contínuo entre duas paredes (a barrigada termina nelas), buracos no gelo de onde sai um caracol-de-cristal a cada ciclo (param holes), teto de onde caem pingentes (param ceiling) e janelas altas por onde pode entrar a nevasca (zona wind com período, só dados).
- **Ataques:**
  - Barrigada: bate as nadadeiras (aviso de 0,6 s; 0,45 s na fase 2) e desliza pelo salão a 320 u/s (400 u/s na fase 2) até a parede
  - Pancada das presas: empina (aviso de 0,55 s; 0,4 s na fase 2) e três pingentes caem em Lume −110, 0 e +110 u
  - Caracóis-de-cristal: a cada ciclo um caracol sai de um buraco no gelo (munição para o jogador e obstáculo)
  - Bolas de neve (fase 2): depois da pancada, duas bolas de neve em arco (±260 u/s); a barrigada ricocheteia uma vez a mais
- **Janela de vulnerabilidade:** Elmo de gelo espinhoso: pisões ricocheteiam. Um casco de caracol-de-cristal chutado contra ela (ou três bolas de fogo) racha o elmo — atordoada por 2 s, pisão na cabeça. Bater na parede ao fim da barrigada também a deixa tonta por 0,9 s (janela curta de pisão). Só pisão causa dano.
- **Fases e mudança de fase:** Despertar: dorme até Lume chegar a 460 u e faz uma introdução de 1,2 s. Fase 1 (5–3 PV): ciclo barrigada/pancada com avisos longos. Fase 2 (≤ 2 PV): avisos curtos, barrigada mais rápida que ricocheteia, bolas de neve depois da pancada.
- **Derrota (animação):** Planejado para a arte: o elmo se parte em cristais, a morsa escorrega para fora do salão por um buraco no gelo com um bufo; o gelo do trono derrete e revela a fonte que acende o farol da fronteira 4.
- **Relação com a mecânica do mundo:** Gelo (o casco vai longe e a morsa desliza), pingentes e o caracol-de-cristal apresentado no primeiro nível do mundo; a nevasca pelas janelas é uma melhoria só de dados.
- **Implementação:** chefe planejado — nova família de comportamento, entrada `boss: true` no registro (ver seção 6.2 do plano geral), eventos `boss_arena`/`camera_lock` e os requisitos listados na fase `frost_citadel`.

**Minichefe da fase 3:** Guardião da Nevasca (família `guardian`, implementado): avança, salta e dispara; abre a guarda periodicamente (janela de pisão), mais rápido na segunda metade.

## NPC do mundo — Tio Nevasco, guia de montanha e pastor de carneiros

**Função.** Ensina a frear no gelo ('solte a corrida antes de pousar') e marca os abrigos de pedra onde a nevasca e as avalanches não chegam; sua corneta toca 1 s antes de cada avalanche em avalanche_ridge. Aparece no checkpoint de cada fase do mundo.

**Falas-guia**
- “No gelo, solte a corrida antes de pousar. O freio vem depois.”
- “Carneiro bravo bate na pedra e fica tonto. Fique em cima da pedra.”
- “Ouviu a corneta? Procure a pedra grande.”
- “A morsa tem elmo de gelo. Casco de cristal, ou três chamas, racha aquilo.”

**Implementação.** Prop animado (guia com cajado e corneta) + evento message; a corneta é um som disparado pelo mesmo temporizador das bolas de neve. Não requer motor novo.

## Resumo por fase

### 4-1 · Lago de Cristal (`crystal_lake`) — legada 3-1

- **Ideia própria:** a patinação vira desafio: parar na ponta do píer congelado.
- **Objetivo:** Apresentar o gelo — margens longas onde frear exige antecipação — e três habitantes do frio, cada um num trecho separado; a terceira relíquia pede uma parada precisa no gelo.
- **Mecânica principal:** Superfície de gelo (atrito baixo: frenagem de ~321 u a partir da corrida)
- **Dificuldade / duração / tamanho:** 4/10 · 60–130 s · 3600×1240 u · 1 checkpoint(s)
- **Estreias:** Pinguim Patrulheiro, Caracol-de-Cristal, Coruja Nevada
- **Relíquias:** relíquia relic_high (x1418, y278) — pista: Trilha de moedas sobe pelos degraus de gelo; relíquia relic_pier (x1840, y320) — pista: Placa do Tio Nevasco 'pare aqui' e marcas de patins no gelo; relíquia relic_room (x2648, y850) e fogo — pista: Cano com seta luminosa coberto de geada
- **Requisitos de motor:** nenhum
- Seção completa: [`PLANEJAMENTO_60_FASES.md`](PLANEJAMENTO_60_FASES.md#4-1--lago-de-cristal-crystal_lake)

### 4-2 · Escalada Azul (`blue_ascent`) — legada 3-2

- **Ideia própria:** uma rota do cume acima dos seis terraços.
- **Objetivo:** Explorar a subida em seis terraços alternando gelo e rocha, conhecer o Boneco de Neve (atirador reto) e encontrar a rota do cume, acima do caminho principal.
- **Mecânica principal:** Terraços alternando gelo e rocha com subidas de até 48 u e descidas de 32 u
- **Dificuldade / duração / tamanho:** 4/10 · 70–150 s · 4400×1240 u · 1 checkpoint(s)
- **Estreias:** Boneco de Neve
- **Relíquias:** relíquia relic_high (x1094, y248) — pista: Trilha de moedas sobe pelos beirais de gelo; relíquia relic_summit (x2980, y120) — pista: Pinheiro mais alto com estrela de neve no topo; pegadas de coruja nos beirais; relíquia relic_room (x4068, y850) e estrela — pista: Cano com seta luminosa coberto de geada
- **Requisitos de motor:** nenhum
- Seção completa: [`PLANEJAMENTO_60_FASES.md`](PLANEJAMENTO_60_FASES.md#4-2--escalada-azul-blue_ascent)

### 4-3 · Coração da Nevasca (`blizzard_heart`) — legada 3-3

- **Ideia própria:** a pedra vira abrigo e arma: o carneiro bate nela e fica tonto.
- **Objetivo:** Desafio de movimento sob nevasca: rajadas contrárias sobre chão contínuo, gelo alternado com rocha, o Carneiro Glacial que investe e o Guardião da Nevasca (5 PV) numa arena seca.
- **Mecânica principal:** Rajadas de nevasca (wind −90 u/s, período 4 s, duty 0,4) sobre chão contínuo, alternando gelo e rocha
- **Dificuldade / duração / tamanho:** 5/10 · 80–170 s · 4600×1240 u · 2 checkpoint(s)
- **Estreias:** Carneiro Glacial, Guardião da Nevasca
- **Relíquias:** relíquia relic_high (x1278, y238) — pista: Trilha de moedas pela plataforma móvel e pelo beiral de gelo; relíquia relic_core (x2360, y260) — pista: Flocos de neve giram em volta de um ponto parado no ar, mesmo durante a rajada; relíquia relic_room (x2618, y850) e coração — pista: Cano com seta luminosa num abrigo de pedra
- **Requisitos de motor:** nenhum
- Seção completa: [`PLANEJAMENTO_60_FASES.md`](PLANEJAMENTO_60_FASES.md#4-3--coração-da-nevasca-blizzard_heart)

### 4-4 · Encostas Escorregadias (`slippery_slopes`) — nova

- **Ideia própria:** a encosta invertida: subir degraus de gelo que empurram de volta.
- **Objetivo:** Mecânica especial das Montanhas Geladas: descer encostas de gelo longas sem poder frear, usando o embalo para saltar vãos no fim de cada rampa, e conhecer o Yeti-Mirim, que arremessa bolas de neve em arco.
- **Mecânica principal:** Encostas de gelo descendentes (degraus de 12 u com arte de rampa contínua) onde não é possível frear; salto no fim da rampa
- **Dificuldade / duração / tamanho:** 4/10 · 90–180 s · 5600×1240 u · 2 checkpoint(s)
- **Estreias:** Yeti-Mirim
- **Relíquias:** relíquia relic_pine (x1478, y150) — pista: Dois pinheiros iguais no topo de uma rampa, um com fita vermelha; relíquia relic_sled (x1188, y850) e estrela — pista: Trilhas de trenó que entram num cano coberto de neve e somem; relíquia relic_slalom (x5150, y220) — pista: Bandeiras de slalom vermelhas e azuis com moedas entre elas
- **Requisitos de motor:** nenhum
- Seção completa: [`PLANEJAMENTO_60_FASES.md`](PLANEJAMENTO_60_FASES.md#4-4--encostas-escorregadias-slippery_slopes)

### 4-5 · Cume da Avalanche (`avalanche_ridge`) — nova

- **Ideia própria:** o corredor da avalanche: quatro bolas gigantes em fases diferentes e abrigos entre elas.
- **Objetivo:** Desafio avançado: atravessar o cume combinando pingentes que despencam (e cujo topo é seguro), bolas de neve gigantes rolando nos vales, cornijas frágeis sob rajadas e todos os inimigos do frio.
- **Mecânica principal:** Pingentes de gelo (crusher: tremem, despencam, viram degrau e se refazem)
- **Dificuldade / duração / tamanho:** 5/10 · 110–220 s · 6000×1240 u · 2 checkpoint(s)
- **Estreias:** Pingente de Gelo
- **Relíquias:** relíquia relic_icicle (x690, y228) — pista: Moedas num nicho do teto, só alcançável usando o pingente caído como degrau; relíquia relic_crystal (x3878, y850) e estrela — pista: Brilho azul atravessando rachaduras perto de um cano coberto de geada; relíquia relic_avalanche (x4500, y170) — pista: Beirais estreitos com a bandeira do Tio Nevasco acima do corredor
- **Requisitos de motor:** nenhum
- Seção completa: [`PLANEJAMENTO_60_FASES.md`](PLANEJAMENTO_60_FASES.md#4-5--cume-da-avalanche-avalanche_ridge)

### 4-6 · Cidadela de Geada (`frost_citadel`) — nova

- **Ideia própria:** no salão dos vitrais a luz colorida marca o gelo que não escorrega.
- **Objetivo:** Fortaleza das Montanhas Geladas: atravessar a cidadela de gelo combinando gelo, pingentes, nevasca pelas janelas e pontes frágeis que se refazem, e derrotar a Morsa Gelomar chutando cascos de cristal no gelo.
- **Mecânica principal:** Pisos alternando gelo e rocha marcados por luz de vitral (rocha = faixas coloridas no chão)
- **Dificuldade / duração / tamanho:** 5/10 · 150–300 s · 6400×1620 u · 2 checkpoint(s)
- **Estreias:** Morsa Gelomar
- **Relíquias:** relíquia relic_window — pista: Um vitral com o desenho de uma estrela aponta para o telhado; moedas brilham através do vidro; relíquia relic_crypt e estrela — pista: Gelo rachado com bolhas de ar presas formando uma seta; relíquia relic_bell — pista: Sino de gelo tocando sozinho no alto da torre
- **Requisitos de motor:** breakable walls: paredes quebráveis por casco, fogo ou investida (segredos) (só para o segredo da cripta)
- Seção completa: [`PLANEJAMENTO_60_FASES.md`](PLANEJAMENTO_60_FASES.md#4-6--cidadela-de-geada-frost_citadel)
