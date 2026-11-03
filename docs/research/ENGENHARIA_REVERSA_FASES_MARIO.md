# Engenharia reversa de fases — séries 2D de *Super Mario* (estudo para o Lume)

> Documento de pesquisa · versão 1.0 · 2026-11-03.
> Escopo: estrutura de mundos e engenharia de fases de oito jogos 2D oficiais, e regras derivadas para as **60 fases originais do Lume** (10 mundos × 6 fases).
> Bibliografia e classes de confiabilidade: [`REFERENCIAS_OFICIAIS.md`](REFERENCIAS_OFICIAIS.md). Citações no formato [R#].

**Aviso de originalidade.** O Lume é um jogo independente. Este estudo descreve *como* as fases oficiais são construídas: estrutura, ritmo, curva de dificuldade e métricas agregadas. Não reproduz mapas, sprites, músicas nem trechos longos de texto. Nomes de mundos, fases, itens e personagens da Nintendo aparecem só como referência de pesquisa e **não** devem ir para o jogo. As medições sobre fases de *Super Mario Bros.* são estatísticas agregadas (larguras, contagens, distribuições); nenhum layout é transcrito.

## 0. Legenda de classificação

| Marcação | Significado |
| --- | --- |
| **Fato confirmado** | Verificado em fonte citada: oficial Nintendo, entrevista, documentação técnica ou wiki de fãs. A classe de cada fonte está na bibliografia; wiki de fãs vale menos que fonte oficial. |
| **Observação** | Contagem, medição ou leitura de padrão feita por esta pesquisa sobre dados de terceiros (corpus VGLC, tabelas do Super Mario Wiki). É reproduzível, mas os autores dos jogos não a declararam. |
| **Estimativa** | Valor obtido por cálculo, simulação ou inferência, com o método indicado. |
| **Decisão do projeto** | Regra adotada para o Lume. Não é afirmação sobre os jogos estudados. |
| *não verificado* | Não confirmado em fonte acessível. Não deve sustentar regra. |

Unidades: **bloco** = 16 px em *Super Mario Bros.* [R41]. **u** = unidade de mundo do Lume. Os quadros são a 60 Hz (NTSC). **R_corr** e **R_and** são o alcance horizontal do salto do Lume correndo e andando, definidos na §5.1.

Siglas dos jogos: **SMB** = *Super Mario Bros.*, **SMB3** = *Super Mario Bros. 3*, **SMW** = *Super Mario World*, **NSMB** = *New Super Mario Bros.*, **NSMBW** = *New Super Mario Bros. Wii*, **NSMBU** = *New Super Mario Bros. U*, **NSLU** = *New Super Luigi U*.

## 1. Escopo e método

**Jogos estudados:** SMB (NES, 1985), SMB3 (NES, 1988), SMW (SNES, 1990), NSMB (DS, 2006), NSMBW (Wii, 2009), NSMBU (Wii U, 2012) com NSLU (2013), *NSMBU Deluxe* (Switch, 2019) e *Super Mario Bros. Wonder* (Switch, 2023).

**Procedimento:**

1. **Intenção de design** vem de entrevistas oficiais: *Iwata Asks*, *Ask the Developer* e entrevistas do Nintendo Classic Mini. O site `iwataasks.nintendo.com` respondeu HTTP 503; usamos o espelho oficial da Nintendo UK, com texto integral [R1]–[R16].
2. **Contagens** de mundos, fases, timers e colecionáveis vêm do Super Mario Wiki [R45]–[R74]. As divergências entre fontes estão marcadas.
3. **Física** vem de documentação técnica comunitária: SMBpedia, a desmontagem de SMB, TASVideos e NESdev [R39]–[R44].
4. **Medições próprias** usam 15 das 32 fases de SMB do corpus acadêmico VGLC [R37], [R38]. O corpus traz só as áreas principais, sem plataformas móveis nem sub-áreas; por isso as quatro fases *athletic* ficam fora das estatísticas de vãos. Também tabulamos os cursos de *Wonder* a partir do wiki [R53].
5. **Parâmetros do Lume** foram lidos do código [R75].

**Limitações:** não houve captura de gameplay. A duração real das fases dos jogos modernos não foi medida, porque o HowLongToBeat estava inacessível (ver §6).

## 2. Síntese: o que mais importa para as 60 fases

1. **Uma ideia por fase, ensinada em etapas** (**Fato confirmado**). Primeiro o conceito aparece em situação segura, depois se desenvolve, sofre uma reviravolta e por fim é testado [R25], [R34]. *Wonder* acrescenta pelo menos uma surpresa por curso [R17].
2. **Errar cedo deve sair barato.** No 1-1 de SMB, os primeiros saltos exigentes são canos de altura crescente, sem nenhum vão letal (**Observação**, [R38]). O cogumelo é desenhado para alcançar o jogador de qualquer jeito (**Fato confirmado**, [R1], [R6]).
3. **A dificuldade cresce em dente de serra.** Ela sobe entre mundos, mas oscila dentro de cada um (**Observação**, notas de *Wonder* [R53]). Os desenvolvedores de SMB criavam fases difíceis e depois levavam os elementos fáceis para o começo (**Fato confirmado**, [R6]).
4. **Meio do mundo com chefe intermediário, fim com chefe principal** (**Observação**). É a regra desde SMB3: fortaleza no meio e aeronave no fim [R46]. Na série NSMB, o meio do mundo tem uma torre e o fim tem um castelo [R67], [R69]. Isso corresponde às fases 3 e 6 do Lume.
5. **Fases curtas, com meta de cerca de 1 minuto** (**Fato confirmado**). Miyamoto pediu esse alvo em SMB [R6]. As fases de NSLU cabem em 100 s [R16]. Uma fase do Lume com 3.200 u dura hoje 9,4 s de corrida pura, contra cerca de 21,5 s do 1-1 de SMB (**Estimativa**, §3.2.8).
6. **Um checkpoint perto do meio, em chão seguro** (**Observação**). Rejogar trechos fáceis é desejável [R5]. O checkpoint deve ficar fora da rota de inimigos [R74], e o curso precisa ser vencível a partir dele [R62].
7. **Moedas guiam e nunca enganam** (**Fato confirmado**). Elas foram inventadas como isca para saltos de descida [R7]. Moedas inalcançáveis são proibidas [R74].
8. **Vãos obrigatórios usam fração do alcance.** Em SMB, a mediana é de 2 blocos e o máximo de 6 blocos, isto é, cerca de 23–68% do alcance correndo (**Observação** + **Estimativa**, §3.2.2).
9. **Segredos em 15–33% das fases e sempre opcionais** (**Observação**). Os jogos usam saídas secretas e rotas alternativas [R47], [R49], [R55], [R59].
10. **Assistência sem rebaixar a experiência** (**Fato confirmado**). Os jogos oferecem Super Guide após 8 falhas [R3], personagens que não sofrem dano [R20], [R52] e insígnias de dificuldade [R19].

## 3.1 Estrutura de mundos por jogo

### 3.1.1 Visão comparada

| Jogo | Mundos | Fases | Fases por mundo | Chefes e posição | Segredos e atalhos | Colecionáveis e eventos |
| --- | --- | --- | --- | --- | --- | --- |
| SMB | 8 [R45] | 32 [R45] | 4, sempre | Castelo na fase 4 de cada mundo [R45] | 3 Warp Zones [R60] e salas bônus [R45] | Moedas e vidas. Sem eventos de ambiente. |
| SMB3 | 8, mais a Warp Zone [R46], [R60] | 88 [R46] | 8–14 (**Observação**) | Fortaleza no meio (Boom Boom) e aeronave no fim (Koopaling) [R46], [R68], [R70] | Mapa com rotas e 3 apitos [R60] | Casas de Toad e painéis Spade [R46]. Marés de água [R71]. |
| SMW | 9: 7 + Star World + Special Zone [R47] | 73, ou 76 por outra contagem; 96 saídas [R47] | Cerca de 4 regulares + segredos [R47] | 7 castelos no fim e 4 fortalezas, uma no meio [R68], [R69] | 24 fases com saída secreta e fechaduras [R47], [R65] | 5 Dragon Coins na maioria das fases [R73]. Switch Palaces [R64]. Paleta "Fall" [R47]. |
| NSMB (DS) | 8 [R48] | 80 [R55] | 8–12 (**Observação**) | Torre no meio e castelo no fim [R67], [R69] | Mundos 4 e 7 secretos, canhões e 16 saídas secretas [R48], [R59] | 3 Star Coins por fase [R55]. Marés de água e lava [R71], [R72]. |
| NSMBW | 9 [R49] | 85, sendo 77 + 8; 99 saídas [R49] | 8–10 (**Observação**) | Torre e castelo com o mesmo Koopaling; aeronave nos mundos 4, 6 e 8 [R67], [R70] | 14 saídas secretas e canhões [R49], [R59] | 231 Star Coins, que abrem o Mundo 9 [R55] |
| NSMBU / NSLU | 8 + Superstar Road [R50] | 82 + 82 [R51], [R55] | 6–12 (**Observação**) | Torre (Boom Boom) e castelo seguido de aeronave [R67], [R69] | 12 saídas secretas, sem canhões [R59] | 246 Star Coins [R55]. Marés de lava [R72]. |
| NSMBU Deluxe | Igual ao NSMBU | 164 cursos [R23] | Igual ao NSMBU | Igual ao NSMBU | Igual ao NSMBU | Personagens assistidos [R23], [R52] |
| *Wonder* | 6 + Petal Isles + Special World [R53] | Cerca de 130 entradas (**Observação**) | 11–21 entradas (**Observação**) | Palácio em 4 mundos e aeronaves em 3 áreas [R69], [R70] | Mastro vermelho [R59] | 225 Wonder Seeds e 306 moedas de 10 flores [R56], [R57]. Wonder Flower em cada curso principal [R58]. |

### 3.1.2 *Super Mario Bros.* (1985)

- **Fato confirmado.** São 13 fases de superfície, 7 *athletic* (plataformas suspensas), 2 subterrâneas, 2 aquáticas e 8 castelos. A quarta fase é sempre um castelo, com falso Bowser nos mundos 1–7 [R45].
- **Observação.** O mundo 1 segue superfície → subterrâneo → *athletic* → castelo. É a lógica apresentação → variação → teste de movimento → chefe das fases 1, 2, 3 e 6 do Lume.
- **Fato confirmado.** As diferenças entre mundos (noite, plantas brancas) são apenas estéticas [R45]. **Observação:** a identidade vem dos inimigos e da mistura de obstáculos.
- **Fato confirmado.** O 1-3 é uma versão mais fácil do 5-3 [R45], ou seja, um remix para escalar a dificuldade. As Warp Zones ficam no 1-2 e no 4-2 [R60]. Canos e trepadeiras levam a salas bônus [R45]. O 1-1 tem um cano-atalho e uma vida escondida [R31]. Os checkpoints são invisíveis [R61].
- **Fato confirmado.** Só Miyamoto e Tezuka desenharam as fases, no papel, com uma versão jogável por dia [R6], [R15], [R27]. Os mundos 3 ou 5 vieram primeiro. Diante das dificuldades de iniciantes, os elementos fáceis foram para o começo, e o 1-1 foi feito por último [R6].

### 3.1.3 *Super Mario Bros. 3* (1988)

- **Fato confirmado.** São 8 mundos e uma Warp Zone ("Mundo 9"), acessível só com um dos 3 apitos [R60]. O wiki usa os nomes Grass Land, Desert Land, Water Land, Giant Land, Sky Land, Ice Land, Pipe Land e Dark Land. Os nomes do lançamento NTSC original eram *Desert Hill*, *Ocean Side*, *Big Island*, *The Sky*, *Iced Land*, *Pipe Maze* e *Castle of Koopa* [R46]. **Divergência de nomes:** "Desert Hill" e "Ocean Side" são os nomes NTSC originais; os remakes e o wiki usam "Desert Land" e "Water Land".
- **Fato confirmado.** O total é de 88 fases [R46]. **Observação:** a tabela do wiki dá 8, 9, 12, 9, 13, 14, 14 e 9 entradas por mundo, com 1, 1, 2, 2, 2, 3, 2 e 1 fortalezas. Separar as três "Hand Traps" do Mundo 8 daria 90 (*não verificado em fonte*).
- **Fato confirmado.** O mapa tem caminhos, casas de Toad e cursos de inimigos, e o manual japonês o compara a um tabuleiro [R46]. A fortaleza do meio do mundo, com Boom Boom, abre portas trancadas [R68]. Os mundos 1–7 terminam na aeronave do Koopaling [R70]. Não há checkpoints, porque as fases são curtas [R61].
- **Fato confirmado.** Marés de água sobem e descem no 3-3 e no 3-8 [R71]. A vista isométrica foi abandonada porque era preciso ver se os pés de Mario tocavam o chão [R21]. Os cursos são cheios de elementos e admitem estratégias diferentes [R21]. Segundo a *Nintendo Power* (1990), via [R32], os primeiros mundos têm mais moedas e vidas bônus; a fonte primária não foi consultada.

### 3.1.4 *Super Mario World* (1990)

- **Fato confirmado.** Os mundos são Yoshi's Island, Donut Plains, Vanilla Dome, Twin Bridges, Forest of Illusion, Chocolate Island, Valley of Bowser, Star World e Special Zone. Quase todo mundo tem 4 fases regulares e pelo menos uma secreta. O jogo registra 96 saídas; outras contagens chegam a 100 [R47].
- **Fato confirmado.** O mapa é conectado, com vários caminhos após cada fase [R47]. Há 7 castelos de Koopalings, 4 fortalezas com Reznor (uma no meio de um mundo) e 6 casas fantasmas [R66], [R68], [R69]. Hideki Konno foi o diretor de mapas [R22].
- **Fato confirmado.** As saídas secretas são um segundo portal ou uma chave levada a uma fechadura. Elas abrem palácios, atalhos e fases secretas [R59], [R65]. Os 4 Switch Palaces transformam blocos pontilhados em sólidos **em todo o jogo** [R64]. A Special Zone é mais difícil e não tem Midway Gate, e concluí-la muda a paleta do mapa ("Fall") [R47]. O Midway Gate fica perto do meio de muitos cursos e transforma o Mario pequeno em grande [R63].
- **Observação.** Na Forest of Illusion há saídas normais que fazem laço, e só a saída secreta avança [R59]. A "ilusão" do nome vira mecânica de mapa.

### 3.1.5 *New Super Mario Bros.* (DS, 2006)

- **Fato confirmado.** As 240 Star Coins correspondem a 80 fases [R55]. **Observação:** por mundo, são 8, 9, 9, 10, 10, 11, 11 e 12 fases [R48], uma progressão monotônica.
- **Fato confirmado.** O caminho se ramifica. O Mundo 4 só abre para quem vence o chefe do 2 como Mini Mario [R48], [R59]. O 7 abre do mesmo modo pelo chefe do 5, ou pelo canhão do Mundo 4. Canhões também levam do Mundo 1 ao 5 e do 5 ao 8 [R48]. As 16 saídas secretas são opcionais [R59], e placas de 5 Star Coins bloqueiam caminhos [R48].
- **Fato confirmado.** O meio do mundo tem uma torre com Bowser Jr. (duas nos mundos 6 e 8) e o fim, um castelo [R67], [R69]. As 4 casas fantasmas têm saída secreta e nenhum checkpoint [R66]. Há marés de água e lava [R71], [R72].

### 3.1.6 *New Super Mario Bros. Wii* (2009)

- **Fato confirmado.** O jogo principal tem 77 cursos, 14 com saída secreta. Com o Mundo 9 são 85 fases e 99 saídas [R49]. Juntar todas as Star Coins de um mundo abre a fase correspondente do Mundo 9 [R55].
- **Fato confirmado.** Mundos ímpares avançam na horizontal e pares na vertical [R49]. **Observação:** a orientação do mapa vira assinatura do mundo.
- **Fato confirmado.** O Koopaling da torre foge para uma revanche no castelo. Bowser Jr. é enfrentado na aeronave nos mundos 4 e 6, e de novo numa aeronave do Mundo 8, antes do castelo de Bowser [R67], [R69], [R70]. O castelo do Mundo 2 e as casas fantasmas não têm bandeira de meio de fase [R62], [R66].
- **Fato confirmado.** O Super Guide aparece após **8 falhas**; antes da decisão foram discutidos 3, 5 e 10 [R3], [R49].
- **Fato confirmado.** O jogo foi feito supondo que as fases seriam rejogadas e ficou mais difícil que o de DS [R9]. O vento, sentido como negativo, ganhou moedas carregadas pelo ar [R8]. Há marés de água no 6-3 e no 6-5, e de lava no 8-6 [R71], [R72].

### 3.1.7 *NSMBU* (2012), *NSLU* (2013) e *NSMBU Deluxe* (2019)

- **Fato confirmado.** O mapa é contínuo, com as áreas Acorn Plains, Layer-Cake Desert, Sparkling Waters, Frosted Glacier, Soda Jungle, Rock-Candy Mines, Meringue Clouds, Peach's Castle e Superstar Road. Foi o primeiro 2D da série com nome único para cada fase [R50]. **Observação:** pelas Star Coins [R55], são 8, 9, 9, 9, 12, 10, 10, 6 e 9 fases por área.
- **Fato confirmado.** Sem canhões de atalho, as 12 saídas secretas abrem fases ocultas e atalhos [R50], [R59]. Boom Boom guarda a maioria das torres [R67]. Do castelo, um canhão leva à aeronave do Koopaling [R69], [R70]. As casas fantasmas não têm checkpoint [R66]. Nabbit foge com um item em uma fase de cada um dos sete primeiros mundos [R50].
- **Fato confirmado (NSLU).** São 82 cursos novos sobre o mesmo mapa, com 100 s e contagens de 1 s; a porta do chefe dá mais 100 s [R51], [R54]. Os 100 s começaram como diretriz interna. Em vez de cortar conteúdo, a equipe alongou cada contagem, e alguns cursos mal cabem no limite. Avaliadores veteranos jogaram como iniciantes [R16].
- **Fato confirmado (Deluxe).** São 164 cursos. Toadette e Nabbit são pensados para jogadores menos experientes [R23]. Eles recebem mais 100 s e escorregam menos, e Peachette escapa uma vez de um vão [R52].

### 3.1.8 *Super Mario Bros. Wonder* (2023)

- **Fato confirmado.** O jogo tem 6 mundos numerados: Pipe-Rock Plateau, Fluff-Puff Peaks, Shining Falls, Sunbaked Desert, Fungi Mines e Deep Magma Bog. Há ainda as Petal Isles (área central) e o Special World [R53]. **Divergência:** fontes falam em 6, 7 ou 8 "mundos" conforme contem o hub e o Special World. A edição de Switch 2 (2026) acrescenta conteúdo **não coberto aqui** [R53].
- **Observação.** A tabela do wiki tem 132 linhas, com 20, 18, 12, 21, 12, 17, 21 e 11 por área. Incluem cursos curtos de bônus, como desafios de insígnia, arenas, pausas e caças a objetos. Pela nossa classificação, cada área tem de 5 a 12 cursos regulares [R53].
- **Fato confirmado.** Cada curso principal tem uma Wonder Flower que transforma o curso e leva a uma Wonder Seed [R58]. Os cursos padrão dão pelo menos 2 sementes, e 3 quando há saída secreta [R56]. São 225 sementes e 3 moedas de 10 flores por curso, num total de 306 [R56], [R57]. A dificuldade é indicada de 1 a 5 estrelas [R19], [R53]. O jogo não tem timer nem pontuação [R53], [R54].
- **Fato confirmado.** Há palácios com Bowser Jr. e Royal Seed no fim de 4 mundos, e "flying battleships" em 3 áreas [R69], [R70]. O jogo tem uma única casa fantasma [R66]. A saída secreta é marcada por um mastro vermelho [R59].
- **Observação.** A média de estrelas dos cursos regulares por área é a seguinte. A sequência é não monotônica, com mínimos e máximos dentro de cada mundo:

| Área | Mundo 1 | Mundo 2 | Mundo 3 | Mundo 4 | Mundo 5 | Mundo 6 | Petal Isles | Special |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Média (n) | 2,0 (11) | 2,4 (8) | 2,8 (5) | 2,3 (9) | 2,3 (6) | 3,2 (6) | 2,75 (12) | 5,0 (8) |
| Faixa | 1–4 | 1–4 | 2–4 | 1–4 | 1–3 | 2–4 | 2–4 | 5 |

### 3.1.9 Padrões transversais

- **Observação. O tamanho dos mundos cresce:** 4 fases fixas em SMB, 8–12 na série NSMB e 11–21 entradas em *Wonder*. As 6 fases do Lume ficam entre SMB e NSMB.
- **Observação. Chefe no meio e no fim.** Desde SMB3 há chefe intermediário, em fortaleza ou torre [R67], [R68]. Até a série NSMB, o fim de mundo é sempre castelo ou aeronave [R69], [R70]. *Wonder* quebra o padrão: só 4 de 6 mundos terminam em palácio [R53], [R69]. O desenho do Lume, com minichefe em L3 e chefe em L6, segue a linha principal.
- **Observação. Identidade de mundo** combina tema, nome, inimigos, música e **uma mecânica-assinatura**. Exemplos: marés no mundo aquático de SMB3 [R71], laços na floresta de SMW [R59], mapa vertical no NSMBW [R49] e cores próprias por mundo em *Wonder* [R56], [R58]. O contraexemplo é SMB, com mundos só estéticos [R45].
- **Observação. Fases com saída secreta:** cerca de 33% em SMW (24 de 73), 20% no NSMB (16 de 80), 16% no NSMBW (14 de 85) e 15% no NSMBU (12 de 82) [R47], [R49], [R55], [R59]. Em *Wonder*, **não verificado**.
- **Observação. Colecionáveis:** os jogos convergem para 3 grandes moedas por fase [R55], [R57], ligadas a portões de progressão como placas, Mundo 9 e Superstar Road [R55], [R56]. Em SMW, eram 5 Dragon Coins na maioria das fases [R73].
- **Observação. Três escalas de evento ambiental:** *global e persistente* (Switch Palaces, paleta Fall [R47], [R64]), *local à fase* (Wonder Flower [R58]) e *dinâmica* (marés [R71], [R72]).

## 3.2 Engenharia de level design

### 3.2.1 O ciclo de ensino documentado

**a) O 1-1 de SMB.**

- **Fato confirmado.** O primeiro inimigo virou o Goomba porque o Koopa exigia dois passos para ser vencido [R7]. O jogador aprende a pular sobre o Goomba e, ao errar o salto, descobre que pisar o derrota [R1]. O cogumelo se afasta, bate no cano e volta, forçando o contato: Mario cresce justo quando o jogador acha que perdeu [R1]. A posição do primeiro cano foi escolhida simulando no papel as alternativas do jogador [R6].
- **Fato confirmado.** Moedas nos blocos reforçam o hábito de bater neles, e os blocos acima do cogumelo aumentam a chance de contato [R30]. Os resumos do vídeo de 2015 citam buracos com fundo e uma duplicata segura antes de um salto arriscado [R29], [R31]. Quatro canos de alturas diferentes ensinam o salto variável, e há um cano-atalho para veteranos [R31].
- **Observação (VGLC [R38]).** No 1-1, o primeiro inimigo está a 21 blocos do início e os quatro primeiros canos têm 2, 3, 4 e 4 blocos de altura. O **primeiro vão letal** só surge no bloco 69, depois de todo o treino sem risco, após cerca de 12 s de caminhada (**Estimativa**).
- **Fato confirmado.** Miyamoto descreve o 1-1 como uma fase feita para o jogador entender de forma gradual e natural o que faz, e depois jogar com liberdade [R26], [R28].
- **Fato confirmado.** Para Tezuka, projetistas tendem a fazer fases difíceis demais, e as fases quase nunca funcionavam de primeira. O alvo era um fluxo de corrida pontuado por saltos [R27].

**b) *Kishōtenketsu* (Koichi Hayashida, *Super Mario 3D Land*).**

- **Fato confirmado.** Hayashida: "I do think it's really important to decide on a core concept in level design" [R25]. A habilidade segue quatro passos: aprender a mecânica, usá-la num cenário um pouco mais complicado, enfrentar algo inesperado que obriga a pensá-la de outro modo e demonstrar domínio. Ele compara isso ao *kishōtenketsu* dos quadrinhos de quatro quadros e diz que Miyamoto sempre buscou a surpresa do terceiro passo [R25].
- **Ressalva.** A entrevista trata de um jogo 3D. A aplicação ao 2D é uma leitura analítica: o vídeo do Game Maker's Toolkit descreve a introdução como cenário seguro, sem perder vidas [R33], [R34].

***c) Wonder: uma surpresa por curso e uma caixa de ideias.***

- **Fato confirmado.** Para Mouri, os 2D anteriores ofereciam variações de desafios que escalavam em dificuldade, e *Wonder* priorizou um grande número de surpresas: "I wanted to include at least one element in each course that would surprise or delight players" [R17].
- **Fato confirmado.** A equipe inteira escreveu ideias em mais de 2.000 notas adesivas e fez protótipos na hora. Reuniões de protótipo selecionaram as ideias, levadas ao extremo antes de ajustar [R17]. Um testador que caía sempre num vão no início de um curso levou o time a dar mais liberdade de escolha [R19].

**d) NSMBW: repetição, ajuda e domínio.**

- **Fato confirmado.** Para Miyamoto, o objetivo fica à direita, a fase não pode ser longa demais e a repetição deve dar sensação de melhora [R2]. Ele prefere rejogar trechos fáceis a ter muitos checkpoints [R5]. Nakago resume: "We can't betray the players' expectations" [R7]. As demonstrações do Super Guide foram gravadas de forma calma, sem truques [R10]. O Mario Club, empresa que testa e depura jogos para a Nintendo, gravou os vídeos de técnicas avançadas (65 na versão final) [R11]. Avançar para a direita é um fundamento que tranquiliza o jogador, e o mastro final premia a altura do agarre [R13].

**e) *Super Mario Maker 2*: lições oficiais no jogo** (transcritas em [R74]).

- **Fato confirmado.** O checkpoint vai depois de um trecho difícil ou logo antes dele, nunca na rota de um inimigo. O próximo passo fica sempre visível. Ataques surpresa e blocos escondidos que matam são injustos, e essa é a lição mais importante. A dificuldade se regula pelo número, tipo e espaçamento de inimigos e pela largura das plataformas. Moedas atraem, mas em excesso perdem valor. Testar desde o início, com olhos frescos, revela rotas imprevistas [R74].

**f) O ciclo em 8 etapas proposto para o Lume.** Cada etapa traz evidências do estudo; a sequência é uma **Decisão do projeto**.

| Etapa | Função | Evidência | Exemplo estudado |
| --- | --- | --- | --- |
| 1. Introdução | Mostrar o elemento sem exigir nada | *Ki* [R25] | Bloco e moeda no 1-1 [R30] |
| 2. Demonstração segura | Primeiro uso sem penalidade de morte | Introdução segura [R34] | Canos de 2→3→4 blocos, sem vão (**Observação**, [R38]) |
| 3. Primeiro desafio simples | Exigir o uso, com falha barata | Goomba isolado [R1], [R7] | Buraco com fundo [R31] |
| 4. Escalada | Mais exigência e menos margem | *Shō* [R25] | Vãos maiores, que levam a descobrir a corrida [R31] |
| 5. Combinação | Misturar com mecânicas anteriores | Padrões compostos [R36] | Vale com inimigos e teto [R36] |
| 6. Reviravolta | Mudar a leitura do elemento | *Ten* [R25]; surpresa por curso [R17] | Wonder Flower [R58] |
| 7. Teste final | Demonstrar domínio | *Ketsu* [R25] | Escada e vão antes do mastro (**Observação**, [R36], [R38]) |
| 8. Recompensa e encerramento | Fechar com prêmio e respiro | Recompensar o esforço [R14] | Vida no topo do mastro [R12] |

### 3.2.2 Física, distâncias e alturas

- **Fato confirmado (SMB).** A velocidade horizontal tem teto de ±24 subpixels/quadro andando e ±40 correndo, em unidades de 1/16 px [R39], [R41]. Isso dá 1,5 e 2,5 px/quadro, cerca de 90 e 150 px/s. O impulso do salto é de −4 px/quadro ou −5 px/quadro, conforme a velocidade horizontal (limiares 9, 16, 25 e 28) [R39], [R40]. A gravidade na subida com o botão segurado vale 0x20, 0x1E ou 0x28/256 px/quadro². Com o botão solto ou na descida, vale 0x70, 0x60 ou 0x90 [R39], [R40]. A velocidade vertical máxima é de 4 px/quadro, com implementação imperfeita [R39], [R40]. O Data Crystal corrobora a assimetria entre subida e queda [R43].
- **Fato confirmado (câmera de SMB).** A tela tem 256 × 240 px [R44]. A rolagem começa quando o jogador passa de 80 px na tela e acompanha totalmente a partir de 112 px [R40]. **Estimativa:** correndo, o jogador vê cerca de 128 px à frente, ou 8 blocos, perto de um alcance de salto. Miyamoto conta que a equipe buscava um jeito de ver mais longe no curso, e Nakago propôs então um Mario pequeno [R21].
- **Estimativa (SMB, integração a 60 Hz com as constantes acima, erro de ±2 px).** Os saltos ficam assim:

| Salto | Altura máxima | Tempo de voo (mesma altura) | Alcance horizontal |
| --- | --- | --- | --- |
| Parado | ≈ 66 px (4,1 blocos) | ≈ 0,90 s | — |
| Andando | ≈ 70 px (4,4 blocos) | ≈ 0,98 s | ≈ 88 px (5,5 blocos) |
| Correndo | ≈ 82 px (5,2 blocos) | ≈ 0,95 s | ≈ 142 px (8,9 blocos) |

- **Observação (VGLC, 11 fases que não são *athletic*).** Os "vãos puros", sem nenhum sólido acima, somam n = 49. A mediana é de 2 blocos e o máximo de 6, no 8-1; a distribuição é de 21 vãos de 1 bloco, 15 de 2, 9 de 3, 2 de 4, 1 de 5 e 1 de 6. No 1-1 os vãos têm 2–3 blocos. **Estimativa:** isso equivale a 23–34% do alcance correndo e 36–55% do alcance andando. O maior vão do jogo, de 6 blocos, equivale a cerca de 68% do alcance correndo e exige corrida.
- **Observação.** Os degraus de chão de 1 bloco dominam (128 casos), seguidos de 2–4 blocos. Os canos têm em geral de 2 a 4 blocos de altura (69 de 85 casos), com alguns de 5 a 7. **Estimativa:** os canos de 4 blocos do 1-1 pedem cerca de 97% do salto parado. São exigentes, mas a falha só faz bater no cano e não mata.
- **Fato confirmado (SMW).** A corrida oscila em torno de 36, a disparada em torno de 48 e o voo chega a 51 subpixels/quadro. O P-meter tem pico de 112 [R42]. As alturas de salto do SMW **não foram verificadas**. As constantes de física de NSMB e *Wonder* também **não foram verificadas** em fonte técnica.

### 3.2.3 Obstáculos, inimigos e zonas seguras

- **Fato confirmado.** Dahlskog e Togelius catalogam 23 padrões em 5 grupos [R36]:
  - **inimigos:** isolado, hordas de 2, 3 e 4, e inimigos sob um teto;
  - **vãos:** simples, múltiplos, variáveis, com inimigo no ar e com pilares;
  - **vales:** com canos, vazio, com inimigos e com teto;
  - **caminhos múltiplos:** de 2 e de 3 rotas, e *Risk and Reward*;
  - **escadas:** de subida e de descida, e vales entre escadas vazios, com inimigos ou com vão.

  A horda de 4 inimigos existe para forçar o salto longo de quem já o domina [R36].
- **Fato confirmado.** Smith et al. modelam a fase como *rhythm groups* de 5 a 20 s. Cada grupo tem densidade baixa, média ou alta e batidas regulares, aleatórias ou em *swing*. Os grupos são ligados por plataformas de descanso [R35].
- **Observação (VGLC).** Consideramos zona de descanso uma faixa de 8 ou mais blocos de chão sem inimigo nem vão. Os trechos de desafio entre duas zonas têm mediana de 6 blocos, percentil 75 de 16 e máximo de 119. No 1-1 e no 1-2 o máximo é de 11–19 blocos; em fases posteriores, como 2-1, 5-1 e 6-2, chega a 87–119. **A densidade cresce pelo alongamento dos trechos sem respiro.**
- **Observação (VGLC).** A distância entre colunas consecutivas de inimigos tem mediana de 4 blocos (de 2 a 9). As fases que não são *athletic* têm em geral 1,1–2,7 inimigos fixos por tela, com mediana de cerca de 2,2. O 1-1 tem 1,19. O 4-1 e o 6-1 têm contagem baixa porque usam um inimigo que gera outros.
- **Observação (VGLC).** A primeira ameaça (inimigo ou vão) aparece entre os blocos 10 e 21, isto é, a 0,6–1,3 tela do início.
- **Fato confirmado. Legibilidade do perigo.** O pântano venenoso ficou roxo, com bolhas, para parecer perigoso num relance. Inimigos que causam dano têm espinhos [R14]. Em *Wonder*, o Goomba faz expressão de mordida ao causar dano [R18]. Miyamoto defende regras que pareçam naturais e fáceis de entender, e coerentes entre si, como o comportamento do fogo na água [R4].

### 3.2.4 Checkpoints

- **Fato confirmado.** A evolução foi esta:
  - SMB usa pontos invisíveis [R45].
  - SMB3 não tem checkpoint, por ter fases curtas [R61].
  - SMW criou o Midway Gate, perto do meio de muitos cursos, que restaura o tamanho de Mario [R63].
  - A série NSMB usa bandeiras e omite o checkpoint em casas fantasmas e em alguns castelos [R62], [R66].
  - No NSMBW, reaparecer no checkpoint custa 200 contagens [R54], e o bloco do Super Guide surge no início ou no checkpoint [R49].
- **Fato confirmado.** No *Super Mario Maker*, uma fase com checkpoint só pode ser publicada se for vencível a partir dele [R62]. As lições do SMM2 dizem que o checkpoint não deve deixar o jogador na rota de um inimigo que chega e cabe antes de um desafio difícil [R74].
- **Observação.** Miyamoto prefere poucos checkpoints, porque repetir o fácil treina [R5]. As lições oficiais o colocam depois de um trecho difícil ou logo antes dele, sempre em local seguro [R74]. A síntese é **um** checkpoint seguro, perto do meio. A frequência exata por fase na série NSMB **não foi contada**.

### 3.2.5 Rotas, desafios opcionais, segredos e recompensas

- **Fato confirmado.** Há caminhos múltiplos e o padrão *Risk and Reward*, em que um caminho tem prêmio e risco [R36]. O cano do 1-1 encurta a fase [R31]. Há Star Coins à vista e escondidas em canos e trepadeiras [R48]. No NSMBW, todo curso normal permite ganhar uma vida no topo do mastro, com técnicas variadas [R12].
- **Fato confirmado.** Pelas lições oficiais, larguras diferentes induzem a escolha de caminho e um bloco "?" transforma uma plataforma em destino. Moedas e blocos nunca ficam inalcançáveis. Um bloco escondido deve ser sugerido, por exemplo por uma moeda, e um caminho oculto exige pista [R74].
- **Fato confirmado.** Para Tezuka, quem se esforçou até ali merece alguma ajuda [R7], e o esforço deve ser recompensado [R14].

### 3.2.6 Moedas como guia, ritmo visual e legibilidade

- **Fato confirmado.** Em SMB, as moedas no ar foram criadas para induzir o salto de descida das fases no céu. O jogador confia que uma moeda no ar é segura [R7]. No NSMBW, moedas levadas pelo vento compensam uma mecânica sentida como negativa [R8]. Smith et al. põem moedas nas plataformas de descanso [R35].
- **Fato confirmado.** No NSMB, inimigos saltam no ritmo da música [R48]. Em *Wonder*, um curso faz o personagem saltar a cada quatro tempos, e a ideia virou a insígnia de salto rítmico [R19].
- **Observação.** O ritmo visual nasce da alternância de batidas, como corrida, salto e espera [R35]. Também ajuda a repetir com variação um mesmo elemento, como os canos de altura crescente do 1-1 [R38].

### 3.2.7 Transições de cena

- **Fato confirmado.** As fases subterrâneas e aquáticas de SMB começam e terminam com um cano [R45]. No Coin Heaven do SMW, cair não mata e devolve o jogador à fase [R47]. No NSLU, a porta do chefe soma 100 s [R54]. Paredes de cima a baixo escondem o que vem depois e criam salas [R74].
- **Observação.** As transições servem de respiro e de recompensa, como a sala bônus que fecha uma subseção, e marcam mudanças de regra, como a porta do chefe.

### 3.2.8 Duração típica

- **Fato confirmado.** O alvo de SMB era de cerca de 1 minuto por fase. Miyamoto disse a Nakago: "Make it so that a single level lasts about one minute" [R6]. As fases usaram cerca de 12 telas; a mais longa teve 32 [R6]. No NSLU, os cursos cabem em 100 s [R16]. No NSMBW, a fase não pode ser longa demais [R2].
- **Observação (VGLC).** As áreas principais de SMB têm de 149 a 222 blocos, ou 9,3–13,9 telas. O 8-1 tem 373 blocos (23,3 telas). **Divergência:** as "32 telas" de [R6] não aparecem no corpus, que omite sub-áreas; a fase citada **não foi identificada**.
- **Estimativa.** A travessia pura do 1-1 leva cerca de 21,5 s correndo (202 blocos × 16 px ÷ 150 px/s) ou 36 s andando. A meta de 1 minuto dá um fator de cerca de 2,8 entre tempo esperado e corrida pura. As outras fases de SMB levariam de 16 a 24 s de corrida pura, e o 8-1 cerca de 40 s.
- **Fato confirmado.** O timer de SMB é de 160 s, e os dos NSMB vão de 225 a 525 s [R54]. **Estimativa:** o timer de SMB equivale a cerca de 2,7 vezes a meta de 1 minuto. Os tempos reais de conclusão por fase **não foram verificados**.

## 4. Medidas e tempos estimados

| Métrica | Valor | Fonte ou método | Classificação |
| --- | --- | --- | --- |
| Bloco de SMB | 16 px | [R41] | Fato confirmado |
| Imagem do NES | 256 × 240 px | [R44] | Fato confirmado |
| Velocidade máxima andando / correndo (SMB) | 24 / 40 subpx/quadro, isto é, 1,5 / 2,5 px/quadro ou ≈ 90 / 150 px/s | [R39], [R40]; conversão a 60 Hz | Fato confirmado |
| Impulso do salto (SMB) | −4 px/quadro, ou −5 se a velocidade for ≥ 25 subpx/quadro | [R39], [R40] | Fato confirmado |
| Gravidade na subida / na queda (SMB) | 0x20–0x28 / 0x60–0x90 ÷ 256 px/quadro² | [R39], [R40] | Fato confirmado |
| Altura do salto parado / correndo (SMB) | ≈ 4,1 / ≈ 5,2 blocos | Integração própria | Estimativa |
| Alcance do salto andando / correndo (SMB) | ≈ 5,5 / ≈ 8,9 blocos | Integração própria | Estimativa |
| Tempo de voo (SMB) | ≈ 0,9–1,0 s | Integração própria | Estimativa |
| Visão à frente correndo (SMB) | ≈ 8 blocos (rolagem a partir de 112 px) | [R40] mais cálculo | Estimativa |
| Vãos puros (SMB, 11 fases) | Mediana 2, máximo 6 blocos; no 1-1, até 2–3 | VGLC [R38] | Observação |
| Vão máximo ÷ alcance correndo (SMB) | 1-1: ≈ 23–34%; jogo todo: ≈ 68% | Razão própria | Estimativa |
| Primeira ameaça (SMB) | Blocos 10–21 (0,6–1,3 tela) | VGLC | Observação |
| 1-1: primeiro inimigo / primeiro vão letal | Bloco 21 (≈ 3,7 s andando) / bloco 69 (≈ 12 s andando) | VGLC mais cálculo | Observação + Estimativa |
| Espaçamento entre inimigos (SMB) | Mediana de 4 blocos (de 2 a 9) | VGLC | Observação |
| Trecho de desafio entre descansos (SMB) | Mediana 6, p75 16, máximo 119 blocos | VGLC | Observação |
| Largura das fases (SMB) | 149–222 blocos; 8-1 com 373 | VGLC | Observação |
| Meta de duração (SMB) | ≈ 1 min; ≈ 12 telas; máximo de 32 | [R6] | Fato confirmado |
| Travessia pura do 1-1 | ≈ 21,5 s correndo / ≈ 36 s andando | Cálculo | Estimativa |
| Timer de SMB | 0,4 s/contagem; 400 = 160 s; 300 = 120 s | [R54] | Fato confirmado |
| Timer de SMB3 / SMW | 0,68 s / 41 quadros; 300 ≈ 204 s | [R54] | Fato confirmado |
| Timer de NSMB / NSMBW / NSMBU | 0,75 s; 300–700 contagens (225–525 s) | [R54] | Fato confirmado |
| Timer do NSLU | 100 s, com +100 s na porta do chefe | [R16], [R54] | Fato confirmado |
| Timer de *Wonder* | Sem limite de tempo | [R53], [R54] | Fato confirmado |
| Velocidades do SMW | Corrida ≈ 36, disparada ≈ 48, voo 51 subpx/quadro | [R42] | Fato confirmado |
| Gatilho do Super Guide (NSMBW) | 8 falhas | [R3], [R49] | Fato confirmado |
| Dificuldade média por mundo (*Wonder*) | 2,0 → 3,2; Special World com 5,0 | Tabela de [R53] | Observação |
| Física de NSMB e *Wonder* | — | — | não verificado |
| Duração média real por fase (jogos modernos) | — | Fonte inacessível | não verificado |

## 5. Princípios aplicáveis ao Lume

### 5.1 Parâmetros físicos do Lume (base dos limiares)

**Fato confirmado** para as constantes do código [R75]. **Estimativa** para os valores derivados por cálculo.

| Parâmetro | Valor |
| --- | --- |
| Jogador pequeno / grande | 22 × 30 u / 22 × 46 u |
| Gravidade / impulso / queda máxima | 1550 u/s² / 590 u/s / 850 u/s |
| Altura máxima segurando o salto (H) | 112,3 u, com ápice em 0,381 s |
| Salto mínimo (corte em −190 u/s) | ≈ 16,6 u |
| Tempo de voo até a mesma altura | 0,761 s |
| Alcance correndo, R_corr (340 u/s) | 258,8 u |
| Alcance andando, R_and (220 u/s) | 167,5 u |
| Pista para atingir a corrida a partir do repouso | ≈ 41 u (0,24 s) |
| Frenagem desde a corrida: chão / gelo / ar sem comando | 38,5 u / 321 u / 116 u |
| *Coyote* / *buffer* | 0,10 s (34 u correndo) / 0,12 s |
| Visão à frente: parado / andando / correndo | ≈ 628 / 661 / 679 u |
| Janela vertical | 250 u acima da cabeça; ≈ 260 u abaixo dos pés (pequeno) |
| Tempo-limite atual | 260 + largura/30 s; *respawn* com pelo menos 90 s |

**Alcance horizontal conforme o desnível** (**Estimativa**; Δh positivo quando o pouso fica acima da decolagem; arco completo, sem *coyote*):

| Δh (u) | +96 | +80 | +64 | +48 | +32 | 0 | −32 | −64 | −96 | −160 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Correndo (u) | 179 | 199 | 214 | 227 | 239 | 259 | 276 | 292 | 306 | 331 |
| Andando (u) | 116 | 129 | 139 | 147 | 155 | 168 | 179 | 189 | 198 | 214 |

**Observação comparativa.** Medido em "corpos", o alcance do Lume correndo (259 u ÷ 30 u ≈ 8,6) é parecido com o de SMB (≈ 8,9 blocos). Já a altura relativa é menor: 3,7 corpos no Lume contra 5,2 em SMB. **Distâncias de SMB podem ser traduzidas por razão de alcance, mas alturas não.** O Lume também mostra cerca de 2,5 alcances à frente, contra cerca de 1 em SMB. O risco de "salto às cegas" fica sobretudo na vertical.

### 5.2 Regras numeradas

Todas as regras desta seção são **Decisão do projeto**. Os limiares derivam da §5.1 e das evidências citadas. As fases são chamadas "L1"–"L6" dentro de cada mundo.

**A. Alcance e geometria** — **Decisão do projeto**

1. **Vão obrigatório máximo**, medido de borda a borda e com pouso na mesma altura:
   - W1: ≤ 0,50 R_corr (≤ 129 u);
   - W2–W5: ≤ 0,60 R_corr (≤ 155 u);
   - W6–W9: ≤ 0,70 R_corr (≤ 181 u);
   - W10: ≤ 0,75 R_corr (≤ 194 u);
   - nunca acima de 0,85 R_corr (220 u), nem mesmo em rotas opcionais.

   Base: em SMB, a mediana é de 23% e o máximo de 68% do alcance correndo (§3.2.2).
2. **W1-L1 e W1-L2 vencíveis sem correr:** os vãos obrigatórios dessas fases ficam em ≤ 0,75 R_and (≤ 125 u). O vão de 140 u de "Canais do Vale" em `docs/FASES.md` [R75] violaria esta regra; deve ser reduzido ou movido para L3+.
3. **Vão com desnível:** o vão deve ser ≤ fator do mundo × alcance para aquele Δh (tabela da §5.1). Por exemplo, uma subida de 64 u em W2 permite no máximo 0,60 × 214 ≈ 128 u.
4. **Subida obrigatória:**
   - Sobre chão seguro, sem vão nem inimigo embaixo, pode chegar a 0,90 H (≤ 101 u) já em W1, como os canos de altura crescente do 1-1 [R31], [R38].
   - Acima de um vão letal: ≤ 0,70 H (≤ 79 u) em W1–W3 e ≤ 0,80 H (≤ 90 u) depois.
5. **Pouso e frenagem:**
   - A plataforma de pouso obrigatória tem pelo menos 96 u em W1–W5 e pelo menos 64 u em W6+.
   - No gelo, deixar pelo menos 330 u entre o pouso e o próximo perigo, ou pôr uma parede de contenção (frenagem de 321 u).
6. **Pista de corrida:** antes de um vão maior que 0,80 R_and (134 u), deixar pelo menos 96 u de chão plano sem inimigos.
7. **Simulação sem margens do jogador:** saltos obrigatórios são validados decolando na borda, sem *coyote* nem *buffer*, nas duas alturas do jogador. A prática atual de [R75] é estendida assim.
8. **Plataformas móveis ou frágeis** só entram no caminho obrigatório a partir do mundo cuja mecânica-assinatura as introduz, e sempre depois de uma demonstração segura (regra 12).

**B. Câmera, visibilidade e justiça** — **Decisão do projeto**

9. **Pouso visível na decolagem:** o ponto de pouso de todo salto obrigatório deve estar na tela quando o jogador decola. Isso significa Δx ≤ 560 u e Δy entre −200 u (acima) e +220 u (abaixo dos pés) [R74], [R14].
10. **Quedas cegas:** quedas obrigatórias de mais de 220 u exigem trilha de moedas até um chão de pelo menos 160 u de largura [R7], [R74].
11. **Tempo de reação:** uma ameaça que entra na tela no caminho obrigatório deve dar pelo menos 0,8 s antes do contato a 340 u/s. Projéteis acima de cerca de 450 u/s precisam de aviso prévio de pelo menos 0,5 s, visual ou sonoro [R74].

**C. Ensino e ritmo** — **Decisão do projeto**

12. **Toda mecânica nova** (plataforma, inimigo ou elemento de ambiente) estreia sem penalidade de morte. Isso exige chão a no máximo 96 u abaixo, nenhum vão letal num raio de 200 u e nenhum inimigo num raio de 400 u. A mecânica reaparece pelo menos mais 2 vezes na mesma fase, com escalada [R1], [R31], [R34].
13. **Ciclo de 8 etapas (§3.2.1f).** Cada fase declara metadados, como `concept`, `introduces` e `beats`, com faixas de x. As etapas devem aparecer em ordem, e o teste final deve ocupar os últimos 30% da fase [R25].
14. **Uma ideia central por fase** [R25], [R17]. W1–W3 introduzem no máximo 1 mecânica por fase; W4–W10, no máximo 2.
15. **Uma reviravolta por fase**, inspirada em [R17]: um momento que muda a leitura da ideia central, marcado como `beat: "twist"`.
16. **Primeira ameaça:**
    - Nas fases L1, nenhuma ameaça letal a menos de 600 u do *spawn*.
    - O primeiro inimigo surge em chão plano, com pelo menos 300 u de aproximação visível.
    - Em W1-L1, o primeiro vão letal só aparece depois de pelo menos 2 exercícios de salto sem risco.

    Base: o 1-1 tem o primeiro inimigo a 3,7 s e o primeiro vão a 12 s de caminhada (§3.2.1).
17. **Zonas de descanso:** são trechos de pelo menos 200 u planos, sem inimigos nem perigos. A distância máxima entre duas zonas no caminho principal é:
    - W1–W2: 1.200 u;
    - W3–W5: 1.800 u;
    - W6–W8: 2.400 u;
    - W9–W10: 3.000 u.

    Base: os trechos de SMB crescem de 11–19 para mais de 100 blocos [R38], e os *rhythm groups* duram de 5 a 20 s [R35].
18. **Hordas** (3 ou mais inimigos em menos de 250 u) só a partir de W2-L3. Antes disso, deixar pelo menos 160 u entre inimigos no caminho principal [R36].

**D. Checkpoints** — **Decisão do projeto**

19. **Quantidade:**
    - Exatamente 1 em fases com largura de 3.500 u ou mais.
    - Nenhum em fases com menos de 2.500 u.
    - Opcional entre 2.500 e 3.500 u.
    - Em L6, o checkpoint fica antes da antessala do chefe [R5], [R62].
20. **Posição:** entre 40% e 65% da largura [R63], logo depois de um trecho exigente e antes do trecho mais difícil [R74].
21. **Zona segura do checkpoint:** chão plano contínuo de x − 96 a x + 192. Nenhum inimigo que alcance o intervalo [x − 160, x + 320] em até 3 s, nenhum projétil na linha de fogo e nenhum perigo [R74].
22. **Vencível a partir do checkpoint:** a rota automática de teste precisa concluir a fase partindo dele [R62]. O *respawn* devolve o tamanho grande [R63] e mantém pelo menos 90 s no relógio, como já faz [R75].

**E. Rotas, segredos e recompensas** — **Decisão do projeto**

23. **Rota opcional:** a partir de W1-L2, cada fase tem pelo menos 1 rota alta ou baixa que reencontra o caminho principal. O caminho principal nunca depende dela [R36], [R74].
24. **Três relíquias por fase:** uma visível e exigente no caminho, uma na rota opcional e uma na área secreta [R55], [R57]. Juntar todas as relíquias de um mundo abre conteúdo extra [R55].
25. **Segredos sugeridos:** todo bloco oculto ou passagem secreta tem pista, como moeda, rachadura ou som. Nenhum segredo causa morte [R74].
26. **Saída secreta:** 1 por mundo, em L2 ou L5. São 10 no total, cerca de 17% das fases, na faixa de 15–20% da série NSMB [R59]. A saída leva a conteúdo opcional ou atalho e nunca é obrigatória.
27. **Moedas honestas:** toda moeda é alcançável, o que a simulação verifica. Trilhas de moedas sempre terminam em chão seguro. Moedas nunca servem de isca para a morte [R7], [R74].

**F. Duração e tempo** — **Decisão do projeto**

28. **Comprimento-alvo por travessia pura** (largura ÷ 340 u/s):
    - W1: 12–18 s (4.100–6.100 u);
    - W2–W5: 14–22 s;
    - W6–W9: 16–26 s;
    - W10: 18–30 s.

    O L6 soma a arena do chefe.

    Base: SMB tem 16–24 s de corrida pura para cerca de 1 min de jogo [R6] (§3.2.8). As fases atuais do Lume, com 9–15 s, estão no limite inferior. O fator de cerca de 2,8 entre tempo esperado e corrida pura é **Estimativa** e deve ser recalibrado com testes de jogo.
29. **Tempo-limite** de pelo menos o maior valor entre 240 s e 8 × a travessia pura. A fórmula atual de [R75] já cumpre. Depois do *respawn*, pelo menos 90 s.

**G. Acessibilidade e dificuldade** — **Decisão do projeto**

30. **Índice de dificuldade de 1 a 5 por fase**, exibido no mapa como em *Wonder* [R19].
    - Médias por mundo: 1,5 · 2,0 · 2,3 · 2,6 · 2,9 · 3,2 · 3,5 · 3,8 · 4,1 · 4,5.
    - Desvio de cada fase em relação à média: L1 −0,7, L2 −0,4, L3 +0,1, L4 −0,1, L5 +0,5, L6 +0,6.
    - Isso forma um dente de serra, como observado em *Wonder* (§3.1.8), e cumpre o princípio de levar o fácil para o começo [R6].
31. **Ajuda opcional:** depois de 8 falhas na mesma fase, oferecer assistência que não colete relíquias [R3]. Considerar um modo assistido, por personagem ou por opção, como os personagens sem dano indicados a iniciantes [R20], [R24], [R52].

### 5.3 Modelo de mundo de 6 fases

As funções das fases e as mecânicas listadas são do Lume e são **Decisão do projeto**. As analogias com os jogos estudados são **Observação**.

| Fase | Função | Conteúdo | Analogia estudada |
| --- | --- | --- | --- |
| L1 Apresentação | Introduzir e demonstrar a mecânica-assinatura com segurança | Etapas 1–4 do ciclo | X-1 de SMB [R45]; 1-1 [R1] |
| L2 Exploração | Desenvolver a mecânica e trazer rotas e segredos | Saída secreta (regra 26) | Fases com rotas múltiplas [R36], [R47] |
| L3 Desafio de movimento | Escalar a execução; minichefe | Arena curta | Fortaleza de SMB3 [R68]; torre da série NSMB [R67] |
| L4 Mecânica especial | Evento de ambiente do mundo (reviravolta) | Maré, vento, interruptor | Marés [R71], [R72]; Switch Palace [R64]; Wonder Flower [R58] |
| L5 Desafio avançado | Combinar com mecânicas anteriores | Rota de risco e prêmio | Padrões combinados [R36] |
| L6 Fortaleza e chefe | Teste final e chefe que usa a mecânica | Checkpoint antes do chefe | Castelos e aeronaves [R69], [R70] |

Mecânica-assinatura por mundo e evento de L4:

1. **Reino Verde:** fundamentos (corrida, salto variável, blocos). L4 com interruptores simples.
2. **Deserto Dourado:** areia e vento lateral. Nas rajadas, a recompensa deve compensar o incômodo [R8].
3. **Costa dos Corais:** água, com maré que sobe e desce [R71].
4. **Montanhas Geladas:** gelo; respeitar a regra 5.
5. **Floresta Encantada:** vegetação que cresce e exploração vertical. Bom lugar para segredos.
6. **Cidade Mecânica:** engrenagens, com um interruptor de L4 que altera L5–L6. É um análogo local do Switch Palace [R64].
7. **Arquipélago Celeste:** plataformas aéreas e correntes de ar ascendentes.
8. **Pântano Assombrado:** pouca visibilidade e inimigos furtivos. O perigo precisa de sinal claro [R14]. Pode haver enigma com saída secreta [R66], mas o checkpoint fica por acessibilidade.
9. **Fortaleza Vulcânica:** lava, com maré de lava em L4 [R72].
10. **Cidadela das Estrelas:** síntese. Remixes mais difíceis de ideias anteriores, como o 1-3 que reaparece como 5-3 [R45], e fases de dificuldade 5, como a Special Zone e o Special World [R47], [R53].

### 5.4 Validação automatizável

Os testes abaixo são **Decisão do projeto**. Eles complementam `tests/unit/levels.test.ts` [R75].

- **Geometria (regras 1–7):** extrair os vãos e desníveis do caminho principal e comparar com a tabela de alcance. Simular os saltos obrigatórios sem *coyote* e sem *buffer*.
- **Visibilidade (regras 9–11):** para cada salto obrigatório, testar se o pouso cabe na janela da câmera calculada pelo alvo de `game.ts` [R75].
- **Ensino (regras 12–16):** validar os metadados `concept`, `introduces` e `beats`. A primeira ocorrência de cada mecânica deve estar numa zona sem vão e sem inimigo.
- **Ritmo (regra 17):** varrer o eixo x e medir a distância máxima entre zonas de descanso.
- **Checkpoint (regras 19–22):** conferir posição percentual e zona segura. Simular a patrulha dos inimigos por 3 s e rodar a rota de teste a partir do checkpoint.
- **Segredos (regras 23–27):** contar relíquias e saídas secretas por mundo. Verificar o alcance de todas as moedas.
- **Duração (regras 28–29):** calcular largura ÷ 340 e o tempo-limite.

## 6. Divergências, lacunas e itens não verificados

- **Contagens que dependem do método:**
  - SMB3 tem 88 fases pelo wiki; daria 90 separando as Hand Traps, sem fonte para isso [R46].
  - SMW tem 73 ou 76 fases e 96 a 100 saídas [R47].
  - *Wonder* tem 6, 7 ou 8 "mundos" e cerca de 130 entradas, conforme se contem cursos-bônus [R53].
  - O NSMBW tem 77 cursos principais [R49], mas só 69 fases com Star Coins nos mundos 1–8 (**Observação**).
- **Nomes de mundos de SMB3:** os nomes NTSC originais diferem dos de remakes e do wiki [R46].
- **As "32 telas" de [R6]:** a fase não foi identificada no corpus VGLC.
- **Física dos NSMB e de *Wonder***, e alturas de salto do SMW: *não verificadas*.
- **Durações reais por fase nos jogos modernos:** *não verificadas* (HowLongToBeat inacessível). O fator 2,8 entre tempo esperado e corrida pura vem de um único dado de SMB (**Estimativa**).
- **Número de saídas secretas e frequência de checkpoints em *Wonder*:** *não verificados*.
- **Fontes primárias lidas só por resumo:**
  - vídeo da Eurogamer sobre o 1-1 [R26], via [R28]–[R31];
  - vídeo do Game Maker's Toolkit [R33], via [R34];
  - *Nintendo Power* (1990), via [R32];
  - Data Crystal, só parcialmente [R43].
- **Limites do VGLC:** o corpus tem só 15 fases, sem sub-áreas nem plataformas móveis, e com inimigos em posição inicial. As fases *athletic* ficaram fora das estatísticas de vãos.
- **Aplicação do *kishōtenketsu* ao 2D:** é interpretação analítica [R33], [R34]. A entrevista original trata de um jogo 3D [R25].
