# Mundo 7 — Arquipélago Celeste (`sky_archipelago`)

> Ilhas suspensas, nuvens e vendavais. Bioma `sky`, cor de mapa `#8fc8ff`, mundo novo.
> Plano geral: [`PLANEJAMENTO_60_FASES.md`](PLANEJAMENTO_60_FASES.md) · dados: [`campaign_plan.json`](../../lume/data/plan/campaign_plan.json).

## Identidade

**Reviravolta do mundo.** O vazio deixa de ser só morte: saltar para dentro de uma corrente de ar ou de uma cachoeira que sobe é o caminho — até a grifa, vencida por quem fica acima dela.

**Paleta**
- azul-céu #8fc8ff e azul-alto #5a9be0
- branco-nuvem #ffffff com sombra #d6e4f5
- rosa de pôr do sol #ffb3c7 e dourado #ffd36e
- verde-ilha #7ccf8a e pedra flutuante #b8a99a
- tempestade: chumbo #4b5468 e raio #e6f0ff

**Marcos visuais**
- cais de nuvens com dirigíveis ancorados
- ilhas-jardim com raízes pendentes
- cachoeiras que correm para cima
- pontes de corda entre torres de ancoragem
- agulha de pedra com para-raios na tempestade
- ninho de galhos gigantes no topo do arquipélago

**Ambiência.** Manhã luminosa (L1), tarde de jardim com pólen (L2), arco-íris nas cachoeiras (L3), vendaval com nuvens rápidas (L4), tempestade com relâmpagos (L5) e pôr do sol dourado no ninho (L6). Vento constante no áudio, sinos de vento e asas.

**Física.** Correntes ascendentes = zonas wind com force_y entre −1900 e −2000 (sobem devagar contra a gravidade; soltando o salto a subida fica limitada a ~190 u/s pelo corte do salto, segurando ela acelera); vendavais = wind lateral ±180 u/s com período; nuvens semissólidas e nuvens frágeis (crumble); nuvens-mola (spring, bounce até 1100); cachoeiras ascendentes = swim + current force_y ≈ −700 (precisa vencer a gravidade da água, 420 u/s²; subida limitada a ~276 u/s). Queda no vazio mata, mas toda corrente sobre o vazio é sinalizada (fitas e moedas em coluna). Vãos obrigatórios ≤ 160 u.

## Progressão das mecânicas

| Fase | Id | Papel | Foco | Dif. | Ideia própria |
| --- | --- | --- | --- | ---: | --- |
| 7-1 | `cloud_harbor` | apresentação | nuvens semissólidas, correntes ascendentes e o pássaro que mergulha | 6 | saltar no vazio de propósito para pegar a corrente |
| 7-2 | `floating_gardens` | exploração | exploração vertical, nuvem que persegue e semeia espinhos | 7 | subir por baixo das ilhas pelas raízes pendentes |
| 7-3 | `updraft_falls` | desafio de movimento | cachoeiras que sobem (nado vertical) e revoada final | 7 | pular de uma cachoeira que sobe para outra que desce |
| 7-4 | `gale_bridges` | mecânica especial | vendavais alternados sobre pontes e balões que derivam (mecânica especial) | 7 | o vendaval cruzado: duas rajadas em fases opostas sobre um vão de 160 u |
| 7-5 | `storm_spire` | desafio avançado | tempestade: corrente central intermitente, para-raios e nuvens frágeis | 8 | a corrente central só liga entre os trovões |
| 7-6 | `griffin_aerie` | fortaleza e chefe | ninho vertical e chefe vencido de cima | 8 | a grifa só é vencida por quem está acima dela |

## Distribuição de inimigos

★ = estreia da espécie (igual a `introduced_in`); ● = permitida; ◆ = permitida só em sub-área do bioma indicado.

| Espécie | 7-1 | 7-2 | 7-3 | 7-4 | 7-5 | 7-6 |
| --- | :---: | :---: | :---: | :---: | :---: | :---: |
| Abutrinho (`abutre_filhote`) | ● | ● | ● | ● | ● | ● |
| Drone Vigia (`drone_vigia`) | ● | ● | ● | ● | ● | ● |
| Pássaro-Rajada (`passaro_rajada`) | ★ | ● | ● | ● | ● | ● |
| Nuvem Marota (`nuvem_marota`) |  | ★ | ● | ● | ● | ● |
| Semente-Espinho (`semente_espinho`) |  | ★ | ● | ● | ● | ● |
| Balão-Espinho (`balao_espinho`) |  |  |  | ★ | ● | ● |
| Grifa Ventania (chefe planejado) (`boss:grifa_ventania`) |  |  |  |  |  | chefe |

Quantidade planejada de inimigos (sem chefes): 7-1: 12–16 · 7-2: 14–20 · 7-3: 14–18 · 7-4: 16–22 · 7-5: 20–26 · 7-6: 18–24.

## Chefe do mundo — Grifa Ventania (`grifa_ventania`, planejado)

- **Fase:** `griffin_aerie`
- **Arena:** Ninho vertical (1000×1620, fortaleza): três plataformas de galhos semissólidos em alturas diferentes, duas colunas de corrente ascendente entre elas, nuvens-mola nas bordas e o poleiro da grifa no ponto mais alto (que sobe na fase 2).
- **Ataques:**
  - Rasante em arco cruzando o ninho de uma borda à outra (aviso: grito e sombra no chão por 0,7 s)
  - Ciclone de asas: rajadas horizontais alternadas de 2 s
  - Penas-dardo: atira três penas em leque
  - Arremetida por baixo (fase 2): sobe por baixo das nuvens e as desfaz (viram frágeis)
- **Janela de vulnerabilidade:** Só pode ser pisada no dorso. Depois de cada rasante pousa no poleiro mais alto por 2 s para se recompor; Lume precisa subir por uma corrente ascendente ou mola e cair sobre ela. Fogo a atordoa por 0,5 s mas não causa dano.
- **Fases e mudança de fase:** Fase 1 (6–4 PV): rasantes, ciclone e penas; poleiro a meia altura. Fase 2 (3–1 PV): o vento muda de lado a cada 4 s, as nuvens se desfazem com a arremetida e o poleiro sobe para a altura que só a corrente ascendente alcança.
- **Derrota (animação):** A grifa perde as penas da cauda, que planam pelo céu; ela se aninha cansada e entrega uma pena dourada que sobe e acende o farol do arquipélago — fronteira 7.
- **Relação com a mecânica do mundo:** Correntes ascendentes e vendavais: o mundo ensinou a usar o vazio e o vento para ganhar altura, e a única abertura da grifa é por cima.
- **Implementação:** chefe planejado — nova família de comportamento, entrada `boss: true` no registro (ver seção 6.2 do plano geral), eventos `boss_arena`/`camera_lock` e os requisitos listados na fase `griffin_aerie`.

**Fase 3 sem minichefe:** `updraft_falls` termina num teste de movimento próprio (ver resumo abaixo).

## NPC do mundo — Biruta, aeronauta e cartógrafa dos ventos

**Função.** Ensina a ler o ar: fitas nos postes mostram a direção da corrente, colunas de moedas sobre o vazio marcam correntes ascendentes seguras, e o balão dela (plataforma móvel) aparece como carona em trechos opcionais. Aparece no checkpoint de cada fase do mundo.

**Falas-guia**
- “Moedas em coluna sobre o vazio? Pode pular: tem vento te esperando.”
- “Fita esticada é rajada. Fita caída, atravessa.”
- “A cachoeira daqui corre para cima. Nade com ela.”
- “A grifa só abaixa a guarda quando está por baixo de você.”

**Implementação.** Prop animado (balão e cesto) + evento message; o balão opcional é uma plataforma móvel comum. Não requer motor novo.

## Resumo por fase

### 7-1 · Porto das Nuvens (`cloud_harbor`) — nova

- **Ideia própria:** saltar no vazio de propósito para pegar a corrente.
- **Objetivo:** Apresentar o céu: nuvens semissólidas, correntes ascendentes demonstradas sobre chão e depois sobre o vazio, nuvens-mola e o Pássaro-Rajada, que mergulha de poleiros.
- **Mecânica principal:** Correntes ascendentes (wind force_y ≈ −1900) e nuvens semissólidas
- **Dificuldade / duração / tamanho:** 6/10 · 90–180 s · 5400×1620 u · 2 checkpoint(s)
- **Estreias:** Pássaro-Rajada
- **Relíquias:** relíquia relic_mast — pista: Bandeira dourada no mastro do dirigível mais alto; relíquia relic_cargo e estrela — pista: Escotilha no convés com seta luminosa e caixotes; relíquia relic_cloud — pista: Fitas de Biruta somem dentro de uma nuvem densa; penas subindo
- **Requisitos de motor:** nenhum
- Seção completa: [`PLANEJAMENTO_60_FASES.md`](PLANEJAMENTO_60_FASES.md#7-1--porto-das-nuvens-cloud_harbor)

### 7-2 · Jardins Flutuantes (`floating_gardens`) — nova

- **Ideia própria:** subir por baixo das ilhas pelas raízes pendentes.
- **Objetivo:** Explorar jardins suspensos em três camadas, com muitas rotas para cima e para baixo, enquanto a Nuvem Marota persegue Lume do alto e semeia Sementes-Espinho que viram andarilhos.
- **Mecânica principal:** Exploração vertical entre três camadas de ilhas (correntes ascendentes, quedas guiadas e raízes semissólidas pendentes)
- **Dificuldade / duração / tamanho:** 7/10 · 110–220 s · 5600×2160 u · 2 checkpoint(s)
- **Estreias:** Nuvem Marota, Semente-Espinho
- **Relíquias:** relíquia relic_rose — pista: Rosas douradas no topo de uma treliça com moedas entre as flores; relíquia relic_greenhouse e estrela — pista: Regador gigante deitado com água brilhando dentro; relíquia relic_low — pista: Pétalas caem em espiral sobre o vazio marcando uma ilha baixa fora da tela
- **Requisitos de motor:** nenhum
- Seção completa: [`PLANEJAMENTO_60_FASES.md`](PLANEJAMENTO_60_FASES.md#7-2--jardins-flutuantes-floating_gardens)

### 7-3 · Cachoeiras Ascendentes (`updraft_falls`) — nova

- **Ideia própria:** pular de uma cachoeira que sobe para outra que desce.
- **Objetivo:** Desafio de movimento vertical: subir por cachoeiras que correm para cima (colunas de nado com corrente ascendente), saindo delas no tempo certo para ilhas, nuvens frágeis e poleiros; terminar com a revoada de pássaros.
- **Mecânica principal:** Cachoeiras ascendentes: colunas swim com current force_y ≈ −700 (nado vertical) e colunas intermitentes
- **Dificuldade / duração / tamanho:** 7/10 · 110–220 s · 4800×2700 u · 3 checkpoint(s)
- **Estreias:** —
- **Relíquias:** relíquia relic_cave e estrela — pista: A cachoeira central se abre em volta de algo atrás dela; brilho dourado; relíquia relic_rainbow — pista: Um arco-íris com moedas nas faixas de cor; relíquia relic_column — pista: Coluna intermitente com marcações de altura e placa de Biruta
- **Requisitos de motor:** nenhum
- Seção completa: [`PLANEJAMENTO_60_FASES.md`](PLANEJAMENTO_60_FASES.md#7-3--cachoeiras-ascendentes-updraft_falls)

### 7-4 · Pontes do Vendaval (`gale_bridges`) — nova

- **Ideia própria:** o vendaval cruzado: duas rajadas em fases opostas sobre um vão de 160 u.
- **Objetivo:** Mecânica especial do Arquipélago Celeste: atravessar pontes de corda entre torres de ancoragem sob vendavais fortes que mudam de lado, enquanto Balões-Espinho derivam com o vento.
- **Mecânica principal:** Vendavais laterais fortes (wind ±180 u/s, período 4 s, duty 0,35) que alternam de lado entre pontes
- **Dificuldade / duração / tamanho:** 7/10 · 110–220 s · 6000×1080 u · 2 checkpoint(s)
- **Estreias:** Balão-Espinho
- **Relíquias:** relíquia relic_vane — pista: Cata-vento dourado girando ao contrário dos outros no topo de uma torre; relíquia relic_under e estrela — pista: Cordas pendem da ponte principal até uma ponte escondida nas nuvens baixas; relíquia relic_gale — pista: Bandeira rasgada com moedas alinhadas contra o vento
- **Requisitos de motor:** nenhum
- Seção completa: [`PLANEJAMENTO_60_FASES.md`](PLANEJAMENTO_60_FASES.md#7-4--pontes-do-vendaval-gale_bridges)

### 7-5 · Agulha da Tempestade (`storm_spire`) — nova

- **Ideia própria:** a corrente central só liga entre os trovões.
- **Objetivo:** Desafio avançado: escalar a agulha de pedra durante a tempestade combinando correntes ascendentes, vendavais, para-raios eletrificados, nuvens frágeis e todos os habitantes do céu.
- **Mecânica principal:** Corrente ascendente central intermitente (período 5 s, duty 0,4) sincronizada com os trovões
- **Dificuldade / duração / tamanho:** 8/10 · 130–260 s · 4800×3240 u · 3 checkpoint(s)
- **Estreias:** —
- **Relíquias:** relíquia relic_nest — pista: Penas brancas presas na chuva apontam para a face norte da agulha; relíquia relic_rod e estrela — pista: Cano de cobre faiscando com seta luminosa; relíquia relic_lightning — pista: Trecho sem luz com moedas que só brilham nos relâmpagos
- **Requisitos de motor:** lights (extensão): a máscara de escuridão das zonas dark com o halo de Lume (120 u; 64 u correndo) já é desenhada; faltam lanternas fixas e acendíveis com raio e duração e o evento lights global (apagar/acender) (opcional: só o desafio do relâmpago)
- Seção completa: [`PLANEJAMENTO_60_FASES.md`](PLANEJAMENTO_60_FASES.md#7-5--agulha-da-tempestade-storm_spire)

### 7-6 · Ninho do Grifo (`griffin_aerie`) — nova

- **Ideia própria:** a grifa só é vencida por quem está acima dela.
- **Objetivo:** Fortaleza do Arquipélago Celeste: subir as muralhas de galhos do ninho combinando tudo do céu e derrotar a Grifa Ventania usando correntes ascendentes para ficar acima dela.
- **Mecânica principal:** Muralhas de galhos semissólidos e correntes ascendentes entre plataformas, em arena vertical
- **Dificuldade / duração / tamanho:** 8/10 · 160–320 s · 6000×2160 u · 2 checkpoint(s)
- **Estreias:** —
- **Relíquias:** relíquia relic_eggs — pista: Brilho de ovos dourados numa ameia, com penas apontando; relíquia relic_throne e estrela — pista: Arco quebrado com cano coberto de hera celeste e luz dourada; relíquia relic_feathers — pista: Cinco penas douradas caindo devagar de um ninho vazio
- **Requisitos de motor:** comportamento do chefe planejado Grifa Ventania (grifa_ventania): família nova em lume/core/behaviors/bosses.py
- Seção completa: [`PLANEJAMENTO_60_FASES.md`](PLANEJAMENTO_60_FASES.md#7-6--ninho-do-grifo-griffin_aerie)
