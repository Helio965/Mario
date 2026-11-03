# Catálogo de personagens dos Mario 2D — estudo para o elenco original do Lume

Documento de pesquisa da Etapa 2 (migração do Lume para Python 3.12 + pygame-ce 2.5.8). Objetivo: entender **como a Nintendo constrói, diferencia e equilibra personagens jogáveis** nos Mario 2D (SMB, Lost Levels, SMB2 USA, SMB3, SMW, NSMB, NSMB Wii, NSMBU/Luigi U/Deluxe, Wonder, com apoio de Super Mario Run e 3D World quando documentam diferenças numéricas de personagem) para projetar um elenco **original** com a mesma profundidade técnica. Nenhum sprite, ROM, voz ou código proprietário foi extraído; todos os números vêm de manuais oficiais, entrevistas publicadas pela Nintendo, páginas oficiais de produto e documentação comunitária (Super Mario Wiki, TASVideos, The Mushroom Kingdom) obtida por análise de terceiros.

Classificação usada em todo o texto:

| Rótulo | Significado |
| --- | --- |
| **OFICIAL** | Manual, site de produto, cartão/dica de carregamento ou entrevista publicada pela Nintendo/desenvolvedores (Iwata Asks, Ask the Developer, entrevistas Famitsu reproduzidas pela imprensa). Descreve comportamento; raramente dá números. |
| **DOCUMENTADO** | Artigo técnico ou wiki com fonte verificável. Inclui "documentação comunitária derivada de análise de terceiros" (valores de RAM/desmontagem, dimensões de sprites). Nunca é valor oficial. |
| **OBSERVADO** | Comportamento descrito por imprensa/guias a partir de gameplay, sem medição. |
| **ESTIMADO** | Inferência nossa (cálculo a partir de valores documentados ou hipótese sem confirmação). |

Convenções: `q` = quadro a 60 Hz; `tile`/`bloco` = 16 px nos jogos NES/SNES. Conversões: `px/q × 60 = px/s`; `subpixel (1/16 px) por q × 3,75 = px/s`. O fator de escala corporal do Lume em relação ao Mario pequeno do NES é **1,875** (30 px / 16 px), o mesmo usado em `FISICA.md` e `MOVIMENTACAO.md`.

---

## 1. Resumo executivo

1. **Dois modelos coexistem na série.** O modelo *arquétipos* (SMB2 USA 1988, Lost Levels 1986, Super Mario Advance, 3D World 2013, Super Mario Run 2016, New Super Luigi U 2013) dá a cada personagem física própria: Luigi salta mais alto e escorrega, Toad é rápido e salta pouco, Peach flutua, Mario é "o mais equilibrado". O modelo *paridade* (SMB 1985 na versão de 2 jogadores, SMB3, SMW no SNES, NSMB Wii/U, Super Mario Maker 2, Super Mario Bros. Wonder) faz todos os personagens jogarem **exatamente igual** e diferencia só por silhueta, cor, som e animação.
2. A escolha pela paridade é **decisão declarada** da Nintendo, não acidente: Miyamoto, em 2009, sobre NSMB Wii — *"With this game we wanted every character to play the same way"*; Peach ficou de fora porque *"would have to be able to fly with her skirt"* (Famitsu via 1UP/Vooks, **OFICIAL**). Em 2023, o diretor de Wonder, Shiro Mouri, repete o argumento: nos jogos anteriores *"Luigi could jump higher, and Peach could float"*, o que tornava certas ações exclusivas de um personagem; Wonder separa **personagem** de **habilidade** por meio dos *badges* (Ask the Developer Vol. 11, **OFICIAL**).
3. O **acesso para iniciantes** migrou de "personagem fácil" (Nabbit em New Super Luigi U e NSMBU Deluxe, rótulos "Easier"/"Easiest", +100 unidades de tempo) para "personagem invencível + badges" (Yoshi e Nabbit em Wonder: *"won't transform with power-ups, but they also don't take damage from enemies"*, site oficial, **OFICIAL**).
4. Os únicos números oficiais de diferença entre personagens são qualitativos ou de manual: Peach flutua *"about 1.5 seconds"* (manual de Super Mario Advance, **OFICIAL**); Luigi *"can leap higher than any other character, but he descends slowly"* (manual SMB2 no Wii VC, **OFICIAL**); Toad *"has the shortest jump height of all characters, but he makes up for it with his strength"* (**OFICIAL**). O guia de Super Mario All-Stars (Nintendo Power) quantifica Lost Levels: salto 4 blocos (Mario) × 5,5 blocos (Luigi); derrapagem 2 × 4 blocos (**DOCUMENTADO**).
5. A documentação comunitária de SMB2 USA (TASVideos) indica que a **velocidade máxima é a mesma para os quatro** (andar 1,5 px/q, correr 2,25 px/q) e que a diferença de Toad aparece ao carregar itens pesados (2,69 px/q); isso contradiz a leitura popular "Toad é o mais rápido" e mostra que diferenças "de velocidade" podem viver na aceleração e no manuseio de itens, não no teto de velocidade (**DOCUMENTADO**, com lacuna registrada na seção 11).
6. **Legibilidade dirige o desenho visual.** Miyamoto explica boné (evita animar cabelo, fixa os olhos), bigode (dispensa boca), macacão (braços de cor diferente do corpo para ler o balanço) e luvas brancas (*"to make his movements easier to spot when he jumped"*) como soluções para 3 quadros de animação (Iwata Asks NSMB Wii, **OFICIAL**). Em Wonder, Sato relata que o time **revisitou as poses da era pixel** (braços estendidos no salto, parada brusca após a corrida) e que o rosto fica sempre visível mesmo com o corpo virado para a direção do movimento (**OFICIAL**).
7. **Proporções documentadas**: Mario pequeno do NES ocupa um quadro de 16×16 px (desenho de 12×16 em pé, 16×16 saltando) e o Super Mario 16×32 px — relação exata de **2:1**, confirmada pela Mario Wiki ("two blocks tall, twice as tall as Small Mario") (**DOCUMENTADO**). Em SMB3 o Mario pequeno é 16×16 e o Raccoon 24×32; em SMW o pequeno andando tem 15×21 e o grande olhando para cima 15×27 (**DOCUMENTADO**). O Lume hoje usa 22×30 / 22×46 (relação 1,53).
8. **Reação a dano** é estável há 40 anos: forma superior → Super → pequeno → perde vida; ao encolher há *invencibilidade de misericórdia* com piscar (SMB: "flashes for eight game seconds", TMK, **DOCUMENTADO**); a morte congela o mundo, vira o personagem para a câmera, dá um pulo e o deixa cair para fora da tela (SMB, repetido em SMB2/3/World) (**DOCUMENTADO**). Em Wonder, Yoshi e Nabbit **não encolhem**, mas Yoshi *"do take knockback"* (**DOCUMENTADO**) e Nabbit *"does not flinch"* (**DOCUMENTADO**).
9. **Som por personagem é regra em Wonder**: Koji Kondo afirma que *cada personagem tem um som de salto distinto* e que o som muda com o tipo de salto; o do Mario é um ukulele elétrico de abeto de Yezo (**OFICIAL**). Vozes: Charles Martinet (Mario de *Mario Teaches Typing* a *Mario + Rabbids Sparks of Hope*; "Mario Ambassador" em 21/08/2023) → Kevin Afghani (Mario e Luigi desde Wonder, 2023; Wario desde *WarioWare: Move It!*, Waluigi desde *Super Mario Party Jamboree*, 2024) (**DOCUMENTADO**, com confirmação da Nintendo à imprensa).
10. **Recomendação para o Lume** (seção 10): elenco de cinco personagens originais com **núcleo de física compartilhado** (modelo Wonder/NSMB) e **variações limitadas por envelope** (≤ ±15 % em altura de salto, ≤ ±12 % em velocidade, ≤ ×0,6 em atrito), um **personagem invencível para iniciantes** (modelo Nabbit/Yoshi) e habilidades opcionais tratadas como *badges*, com validação automática de que **toda fase obrigatória é concluível com o perfil mínimo**.

---

## 2. Linha do tempo das abordagens de elenco (o que cada título decidiu)

| Ano | Título | Jogáveis em plataforma 2D | Diferenças de física | Rótulo | Fonte |
| --- | --- | --- | --- | --- | --- |
| 1983 | Mario Bros. | Mario, Luigi | Nenhuma: Luigi nasce como *palette swap* inspirado no 2.º jogador de *Joust* | DOCUMENTADO | [MW-Luigi] |
| 1985 | Super Mario Bros. | Mario (1P), Luigi (2P) | Nenhuma: "Exactly like Mario in every way, except for his color scheme" | DOCUMENTADO | [TMK-SMB] |
| 1986 | SMB: The Lost Levels | Mario ou Luigi | Luigi: salto 5,5 blocos vs 4; com corrida 6 vs 5; derrapagem 4 vs 2 blocos; "slippery traction" | DOCUMENTADO (guia All-Stars) | [MW-LostLevels] |
| 1988 | Super Mario Bros. 2 (USA) | Mario, Luigi, Toad, Princesa | Quatro arquétipos (ver 3.x); Peach flutua ~1,5 s; Toad salto mais baixo; Luigi desce devagar | OFICIAL (manuais) | [MW-PerfisLuigi][MW-PerfisPeach][MW-PerfisToad] |
| 1988 | Super Mario Bros. 3 | Mario, Luigi (alternados) | Nenhuma documentada no NES; formas compartilham sprites | DOCUMENTADO | [MW-SMB3] |
| 1990 | Super Mario World | Mario, Luigi (2P) | "Mario and Luigi have identical mechanics"; Yoshi como montaria | DOCUMENTADO | [MW-SMW] |
| 2001–2003 | Super Mario Advance 1/2/4 (GBA) | Mario, Luigi (+Toad, Peach no SMA1) | Luigi recupera salto alto, pouca tração e *scuttle* (pernas batendo) | DOCUMENTADO | [MW-Luigi][MW-Scuttle] |
| 2006 | New Super Mario Bros. (DS) | Mario (Luigi via código) | Não documentada | — | — |
| 2009 | New Super Mario Bros. Wii | Mario, Luigi, Toad Amarelo, Toad Azul | **Nenhuma, por decisão**: "we wanted every character to play the same way" (Miyamoto) | OFICIAL | [Vooks-NSMBW] |
| 2012 | New Super Mario Bros. U | Mario, Luigi, 2 Toads, Mii | "Luigi has the same physics and moves as Mario"; Toads idem | DOCUMENTADO | [MW-NSMBU] |
| 2013 | New Super Luigi U | Luigi, 2 Toads, Mii, **Nabbit** | Todos herdam a física de Luigi (salto alto, menos tração); *Luigi Block* restaura a física de NSMBU após terminar o jogo; Nabbit não sofre dano de inimigos | DOCUMENTADO (+ Tezuka via Siliconera) | [MW-NSLU][Siliconera-NSLU] |
| 2013 | Super Mario 3D World (3D, referência) | Mario, Luigi, Peach, Toad, Rosalina | Arquétipos retomados (Luigi alto/escorregadio, Peach flutua, Toad rápido/baixo, Rosalina giro) | DOCUMENTADO + OFICIAL | [MW-3DW][MW-PerfisToad] |
| 2016 | Super Mario Run | Mario, Luigi, Peach, Toad, Toadette, Yoshi, Daisy | Luigi salta mais alto + *scuttle*; Peach flutua; Toad mais rápido; Yoshi *flutter*; Daisy pulo duplo; Toadette neutra | DOCUMENTADO + OFICIAL | [MW-Run][MW-PerfisDaisy] |
| 2019 | NSMBU Deluxe | + **Toadette**, Nabbit nos dois jogos | Toadette "Easier"/Nabbit "Easiest": +100 unidades de tempo, "less slippery", nadam como Penguin Mario; Peachette (Super Crown) flutua, pulo duplo, quica uma vez fora do abismo | DOCUMENTADO + OFICIAL ("optimized for younger and less-experienced players") | [MW-NSMBUD][NOA-NSMBUD] |
| 2019 | Super Mario Maker 2 | Mario, Luigi, Toad, Toadette | Idênticos (nos estilos SMB/SMB3 Luigi volta a ser *palette swap*) | DOCUMENTADO | [MW-Toadette][MW-Luigi] |
| 2023 | Super Mario Bros. Wonder | 12 (Mario, Luigi, Peach, Daisy, 2 Toads, Toadette, 4 Yoshis, Nabbit) | Mario/Luigi/Peach/Daisy/Toads/Toadette **idênticos**; Yoshis e Nabbit sem dano e sem transformação; diferenças vão para os *badges* | OFICIAL | [NOA-Wonder][ATD-Wonder3] |

Leitura: a Nintendo alterna entre os dois modelos conforme o objetivo do jogo — **arquétipos** quando o jogo quer rejogabilidade e expressão (SMB2, 3D World, Run), **paridade** quando quer multijogador justo e fases desenhadas para um único envelope de movimento (NSMB Wii, Wonder). O Lume precisa escolher conscientemente (seção 10).

---

## 3. Fichas dos personagens principais

### 3.1 Mario

| Campo | Conteúdo | Rótulo |
| --- | --- | --- |
| Papel | Protagonista e "faz-tudo" da série. Manual SMB2 (Wii VC): *"Mario has an average jump. When carrying an item, Mario suffers only a minor reduction to his speed and jump height."* Booklet SMA: *"His skills are the most balanced of the characters."* Site 3D World (UK): *"a great all-rounder with boundless energy and a nose for adventure"*. Site Wonder: *"always ready to help a friend, take on a new challenge, or jump on a Koopa's head!"* | OFICIAL [MW-PerfisMario] |
| Personalidade | Alegre, corajoso, poucas palavras; a Nintendo mantém o passado simples para ele caber em qualquer gênero ("jack of all trades"). Dica de carregamento de Wonder: *"Mario works as a plumber with his little brother Luigi."* | DOCUMENTADO/OFICIAL [MW-Mario][MW-PerfisMario] |
| Origem do visual | Miyamoto (Iwata Asks NSMB Wii, vol. 1, p. 2): boné porque *"you can't fully draw hair"* e *"you can have the eyes directly beneath it"*; bigode porque *"if you draw a nose then a moustache, you don't really know if it's a mouth or a moustache, and it saves pixels"*; macacão porque com apenas **três quadros** de animação era preciso *"make his arms and his body different colours"* — *"Overalls were the only option!"*; luvas brancas *"to make his movements easier to spot when he jumped"*. Iwata resume: *"the entire design was a case of form being dictated by function."* O nome veio de alguém da Nintendo of America; Miyamoto o chamava de "Mr. Video". | OFICIAL [IA-Overalls] |
| Proporções (sprites) | SMB: pequeno 12×16 (em pé) e 16×16 (saltando), Super/Fire 16×32, agachado 16×22, nadando 16×29, morte 14×14. SMB3: pequeno 16×16, Fire 16×32, Raccoon 24×32 (cauda). SMW: pequeno andando 15×21, grande olhando para cima 15×27, morte 16×24. Mario pequeno cabe em 1 bloco; Super Mario tem *"two blocks tall, twice as tall as Small Mario"*. | DOCUMENTADO [MW-AssetsSMB][MW-AssetsSMB3][MW-AssetsSMW][MW-SuperForm] |
| Proporção cabeça/corpo | Na era pixel, a cabeça (boné + bigode) ocupa ~metade do Mario pequeno (8 de 16 px) e ~1/3 do Super Mario; Koji Kondo brincou em Wonder com um *"eight-heads-tall, life-sized, live-action Mario"* que nunca foi usado — a proporção canônica é intencionalmente *chibi*. SMW foi o primeiro jogo em que *"Mario's eyes have a white part"*, e Hino manteve os olhos do Mario pequeno pretos "porque tinham caráter" (SMB3). | ESTIMADO (medida) + OFICIAL (citações) [ATD-Wonder1][NUK-SNESYoshi] |
| Movimentação | Andar/correr com aceleração, salto variável, pisão; em 3D World é o "equilibrado" sem vantagem nem desvantagem. Ver `MOVIMENTACAO.md` e `FISICA.md` para os números de SMB/SMB3/SMW/NSMB. | DOCUMENTADO [MW-3DW] |
| Habilidades | Salto, pisão, agachar, nadar, carregar itens (SMB2/SMW), *spin jump* (SMW), *wall jump*, *ground pound*, salto triplo (NSMB). Power-ups: Super Mushroom, Fire Flower, Super Star (SMB), Super Leaf (SMB3), Cape (SMW), Elephant/Bubble/Drill (Wonder). | DOCUMENTADO [MW-Mario][MW-SMBW] |
| Animações características | SMB: 3 quadros de caminhada, pose de salto com braço estendido, derrapagem, nado; Wonder revisita *"the arms-extended jump and the sudden stop after running"* e dobra o número de juntas (12) e animações; o corpo vira para a direção do movimento, mas o rosto permanece visível ("to the entire body", Sato). | OFICIAL [ATD-Wonder2] |
| Reação a dano | Super/Fire atingido → encolhe e pisca; SMB: *"flashes for eight game seconds"* com invencibilidade a inimigos; pequeno atingido → perde vida. Em SMB/Lost Levels/SMW original, forma superior cai **direto para pequeno**; a partir de SMB3 (internacional) e NSMB, cai para Super. Poços, lava e tempo matam em qualquer forma. | DOCUMENTADO [TMK-SMB][MW-SuperForm][MW-SmallMario] |
| Morte | Mundo congela; Mario vira de frente para a tela ("breaks the fourth wall"), dá um pulo e cai para fora da tela; mesmo padrão em SMB2, SMB3 e SMW. Nenhuma entrevista localizada explica a origem. | DOCUMENTADO [TToOVG-Death] |
| Sons e voz | Charles Martinet: audição em 1990 (pediram sotaque italiano), "Mario in Real Time" em feiras, primeiro jogo *Mario Teaches Typing* (CD-ROM), voz padronizada em *Super Mario 64*; em 21/08/2023 a Nintendo o nomeou **Mario Ambassador**; último jogo com Mario: *Mario + Rabbids Sparks of Hope*. Kevin Afghani desde *Super Mario Bros. Wonder* (2023), confirmado pela Nintendo à imprensa. Frases: "It's-a me, Mario!", "Let's-a go!", "Yahoo!", "Mamma mia!". Wonder: som de salto = ukulele elétrico de abeto de Yezo, variando com o tipo de salto; grito de transformação "wowie zowie" é novo. | DOCUMENTADO [MW-Martinet][Wiki-Afghani][Gizmodo-Afghani] + OFICIAL [ATD-Wonder2] |
| Relações | Luigi (irmão gêmeo mais novo e mais alto), Peach (resgatada; romance implícito), Yoshi e Toad (amigos), Bowser (nêmesis), Wario (arquirrival), Donkey Kong (ex-inimigo). | DOCUMENTADO [MW-Mario] |

### 3.2 Luigi

| Campo | Conteúdo | Rótulo |
| --- | --- | --- |
| Papel | Irmão gêmeo, 2.º jogador por origem; herói relutante. Site Wonder: *"Mario's 'little' brother. When these bros team up, there's nothing they can't achieve!"* Cartão Wonder: *"always ready, if sometimes reluctant, to jump into action."* | OFICIAL [MW-PerfisLuigi] |
| Origem | Criado para *Mario Bros.* (1983) como *palette swap* para um segundo jogador cooperativo/competitivo, inspirado em *Joust*; o nome é lido como eco de 類似 *ruiji* ("similar"), explicação popular, não confirmada pela Nintendo. | DOCUMENTADO [MW-Luigi][Wiki-Luigi] |
| Visual | Mais alto e magro que Mario, verde com macacão azul; ganhou sprites próprios em *Super Mario Kart* (1992). Em *All-Stars + SMW* salta com as pernas para trás e ajoelha ao deslizar; em SMB2 o salto é a animação de caminhada acelerada ("pernas batendo"). | DOCUMENTADO [MW-Luigi] |
| Personalidade | Cauteloso, desastrado, medroso (especialmente de fantasmas), bondoso e heroico quando precisa; chora fácil; site 3D World (UK): *"might occasionally tremble in the face of danger, but when the chips are down he always gets the job done"*; Run: *"shy and easily scared, but that won't keep him from jumping a little higher!"* Em Wonder, Blue Toad se agacha de medo "como Luigi faria". | OFICIAL/DOCUMENTADO [MW-PerfisLuigi][MW-ToadsCor] |
| Física — Lost Levels | Guia All-Stars (1 unidade = 1 bloco): salto Mario 4 / Luigi **5,5**; corrida+salto 5 / **6**; derrapagem 2 / **4**. "Slippery traction": escorrega mais e cai em buracos com mais facilidade; quica mais alto ao pisar em inimigos; às vezes passa por cima do mastro final. Fontes qualitativas acrescentam aceleração e desaceleração mais lentas. | DOCUMENTADO [MW-LostLevels][Wiki-LostLevels] |
| Física — SMB2 USA | Manual (Wii VC): *"Luigi can leap higher than any other character, but he descends slowly from his jumps."* Booklet SMA: *"He's got loads of jump ability, but he's rather slow."* Tabela comunitária (5 estrelas): velocidade 3, salto 5, força 3. Fórum TASVideos descreve "slower acceleration but lower gravity". | OFICIAL + DOCUMENTADO [MW-PerfisLuigi][MW-SMB2][TAS-SMB2] |
| *Scuttle* | Pernas batendo no ar que **desaceleram a descida** (não propulsionam, ao contrário do *flutter* de Yoshi); SMB2 e remakes, SM64 DS (segurar B; onde ganhou o nome), 3D World (pernas batem durante **todo** o salto, reduzindo velocidade na subida e na descida), Run, New Super Luigi U/NSMBU Deluxe (também para Toads, Nabbit, Mii, Toadette); em Wonder vira o badge *Floating High Jump*, disponível a qualquer personagem. | DOCUMENTADO [MW-Scuttle] |
| Física — NSMB Wii/U | NSMB Wii: igual a Mario por decisão (Miyamoto). NSMBU: *"Luigi has the same physics and moves as Mario"*; substitui Mario no Super Guide. | OFICIAL + DOCUMENTADO [Vooks-NSMBW][MW-NSMBU] |
| Física — New Super Luigi U | Todos os jogáveis herdam o salto alto e a tração menor de Lost Levels; fases de **100 unidades de tempo**, 82 fases redesenhadas; *Luigi Block* (após terminar) devolve a física de NSMBU ("lower jumps and better traction"); Tezuka: *"when we switched to Luigi, we realized we also needed to change the actions"* e *"places that had been difficult weren't so much anymore"* — o tique do relógio foi alongado para calibrar a dificuldade. | DOCUMENTADO + OFICIAL (via Siliconera) [MW-NSLU][Siliconera-NSLU] |
| Física — 3D World | Salta mais alto, tração baixa ("slippery"), começa a correr mais tarde que Mario, *scuttle* cobre mais chão. | DOCUMENTADO [MW-3DW] |
| Física — Run / Wonder | Run: salta mais alto que Mario e faz *scuttle*. Wonder: idêntico a Mario (decisão de Mouri). | DOCUMENTADO + OFICIAL [MW-Run][ATD-Wonder3] |
| Expressões | "Luigi's Death Stare" (olhar fixo em *Mario Kart 8*) virou meme adotado pela Nintendo; medo e tremor são parte do vocabulário visual (Luigi's Mansion). | DOCUMENTADO [MW-Luigi] |
| Voz | Charles Martinet de *Mario Kart 64* (1996) a *Sparks of Hope*; Kevin Afghani desde Wonder (2023), "muito similar, um pouco mais agudo". | DOCUMENTADO [MW-Luigi] |
| Relações | Mario (irmão, rivalidade leve), Peach (amiga), Daisy (interesse romântico recíproco, estátua em *Mario Kart Wii*), Waluigi (rival). | DOCUMENTADO [MW-Luigi][MW-Daisy] |

### 3.3 Princesa Peach

| Campo | Conteúdo | Rótulo |
| --- | --- | --- |
| Papel | Governante do Reino dos Cogumelos, vítima de sequestro recorrente e, desde SMB2 USA, heroína jogável; protagonista em *Super Princess Peach* (2005) e *Princess Peach: Showtime!* (2024). Site Wonder: *"always ready to jump into action."* Mouri: *"No one has to fight over who gets to be the princess this time"* (Peach e Daisy jogáveis). | OFICIAL [MW-PerfisPeach][ATD-Wonder4] |
| Visual | Miyamoto concebeu; Yoichi Kotabe finalizou com olhos "de gato"; cabelo castanho-avermelhado nos sprites NES, loiro a partir de SMW; vestido rosa a partir do SMB2 ocidental; seis cílios. Em Wonder, *"Super Mario and Super Peach are about the same height"* — a altura foi normalizada ao hitbox comum. | DOCUMENTADO [MW-Peach] |
| Personalidade | Gentil, educada, otimista, "classy", mas ativa contra seus captores; "Vibe powers" (Gloom/Rage/Calm/Joy) em *Super Princess Peach*; 12 transformações em Showtime. | DOCUMENTADO [MW-Peach] |
| Física — SMB2 USA | Manual (Wii VC): *"Princess Toadstool has the unique ability to float in the air for a moment when you hold down [botão]"*; *"Her jump is greatly reduced when she's holding an item."* Booklet SMA: *"She can float on air for about 1.5 seconds when you hold the A Button down."* Estrelas: velocidade 2, salto 3, força 2. Mecânica: paira **a uma altura fixa** por tempo limitado ("briefly hover at a certain height"). | OFICIAL + DOCUMENTADO [MW-PerfisPeach][MW-SMB2][MW-FloatingJump] |
| Física — 3D World | Site US: *"Her special floating ability helps her across any obstacle"*; site UK: *"her mid-air float helps her land safely and dodge danger for a few extra seconds"*. Wiki: corre mais devagar, mas começa a correr mais cedo; cai mais devagar; tempo de planeio *"much shorter"* que em SMB2. | OFICIAL + DOCUMENTADO [MW-PerfisPeach][MW-3DW][MW-FloatingJump] |
| Física — Run | "Travel great distances with a floaty jump"; em Run o float **reduz muito a velocidade de queda** enquanto a tela é segurada e pode ser ativado várias vezes no mesmo salto. | OFICIAL + DOCUMENTADO [MW-PerfisPeach][MW-FloatingJump] |
| Física — Wonder | Idêntica a Mario; a flutuação foi deliberadamente removida do personagem e transferida ao badge *Parachute Cap*/outros. | OFICIAL [ATD-Wonder3] |
| Por que ficou fora de NSMB Wii | Miyamoto (Famitsu, 2009): o time queria paridade e *"Peach would have to be able to fly with her skirt"* — a flutuação quebra o envelope de distância de salto das fases. | OFICIAL [Vooks-NSMBW] |
| Animações | Pose de flutuação com a saia/vestido abrindo (SMB2) ou guarda-chuva; cabelo encurta na forma pequena em SMB2 remakes/3D World/Run, mas **não** em Wonder. | DOCUMENTADO [MW-Peach][MW-SmallMario] |
| Voz | Leslie Swan (*SM64*, 1996), Asako Kozuki (JP), Jen Taylor (*Mario Golf* N64 → *Mario Kart DS*), Nicole Mills (*Strikers* 2005), Samantha Kelly (*Mario Strikers Charged* 2007 → *Brothership*; Showtime 2024), Courtney Lin (*Mario Kart World*, 2025–). Kelly soube da recontratação um dia após o lançamento (06/2025). | DOCUMENTADO [MW-Peach][Siliconera-Kelly][OpenCritic-MKW] |
| Relações | Mario (interesse romântico, amiga de infância), Luigi (amigo), Daisy (melhor amiga), Toad (servo leal), Bowser (raptor). | DOCUMENTADO [MW-Peach] |

### 3.4 Princesa Daisy

| Campo | Conteúdo | Rótulo |
| --- | --- | --- |
| Papel | Princesa de Sarasaland, resgatada em *Super Mario Land* (1989: *"Daisy is being held captive by Tatanga. Mario must rescue her."*); jogável em Run (2016, atualização) e em Wonder (2023), *"the first Daisy playable in a Nintendo console Super Mario platformer"*. | OFICIAL + DOCUMENTADO [MW-PerfisDaisy][MW-Daisy] |
| Visual | Vestido amarelo com detalhes laranja, coroa dourada, cabelo laranja-escuro com pontas viradas (padrão desde *Mario Party 4*); na forma pequena de Run o cabelo encurta mantendo as pontas. | DOCUMENTADO [MW-Daisy][MW-SmallMario] |
| Personalidade | Site japonês de SML: "a tomboyish, full-of-spirit princess" (tradução da wiki); Wonder: *"always chipper, cheerful, and lively!"*; cartão: *"totally down to earth—and always ready for a challenge!"*; MK7: *"outstanding acceleration"*; *Fortune Street*: *"Just because I'm a princess doesn't mean I won't fight dirty!"* Frase-assinatura "Hi, I'm Daisy!" (*Mario Kart: Double Dash!!*, repetida na bio de MK8 em caixa alta). | OFICIAL + DOCUMENTADO [MW-PerfisDaisy][MW-Daisy] |
| Física — Run | *"She can reach great heights with her double jump"* — um segundo salto curto no ar que substitui o giro aéreo. | OFICIAL + DOCUMENTADO [MW-PerfisDaisy][MW-Run] |
| Física — Wonder | Idêntica a Mario; usa Fire, Elephant, Bubble, Drill. | DOCUMENTADO [MW-Daisy] |
| Voz | Kate Fleming (original, segundo a wiki), Jen Taylor (*Mario Party 3–5*), Deanna Mustard (*Mario Party 6* → antes de Wonder; ~2003/2004–2022), Giselle Fernandez (Wonder, 2023–). | DOCUMENTADO [MW-Daisy][NE-WonderCast] |
| Relações | Luigi (interesse romântico), Peach (melhor amiga), Birdo (amiga), Waluigi (rival), Bowser (hostil). | DOCUMENTADO [MW-Daisy] |

### 3.5 Toad (e Toads Amarelo/Azul)

| Campo | Conteúdo | Rótulo |
| --- | --- | --- |
| Papel | Servo e amigo leal de Peach, cidadão-tipo do Reino dos Cogumelos; tutorial/anfitrião (Toad Houses em SMB3); NSMBUD: *"A stalwart resident of the Mushroom Kingdom, Toad's always happy to lend a hand."* | OFICIAL + DOCUMENTADO [MW-Toad][MW-PerfisToad] |
| Visual | Chapéu-cogumelo com pintas vermelhas (um produtor de *Odyssey* afirmou que é parte da cabeça), colete azul, calças brancas largas, braços finos, pernas raramente visíveis. Toads Amarelo e Azul: mesma silhueta, cor do colete/pintas; vozes trocadas entre NSMB Wii, NSMBU e Wonder (um agudo, outro grave). | DOCUMENTADO [MW-Toad][MW-ToadsCor] |
| Personalidade | Alegre, excitável, propenso a pânico; covarde às vezes, mas corajoso quando importa. Em Wonder, Toad Amarelo pula na frente de Peach para protegê-la, Toad Azul se agacha de medo. | DOCUMENTADO [MW-Toad][MW-ToadsCor] |
| Física — SMB2 USA | Manual: *"Toad has the shortest jump height of all characters, but he makes up for it with his strength."* SMA: *"He has the weakest jump but lots of power."* Puxa vegetais e carrega itens mais rápido; "relies heavily on the charged jump" (Power Squat Jump). Estrelas: velocidade 5, salto 2, força 5. **TASVideos**: andar 24 e correr 36 subpx/q para todos; Toad correndo **com item pesado** = 43 subpx/q (os demais perdem velocidade com itens) — a vantagem de Toad é no transporte, não no teto de velocidade livre. | OFICIAL + DOCUMENTADO [MW-PerfisToad][MW-SMB2][TAS-SMB2] |
| Física — NSMB Wii/U | Toads Amarelo e Azul têm *"the same moves and physics as Mario and Luigi"*; multijogador apenas (sozinho só Mario); em Luigi U também fazem *scuttle*. | DOCUMENTADO [MW-NSMBU][MW-ToadsCor] |
| Física — 3D World | Site UK: *"Toad is the fastest of the four friends, so he's the best bet in situations where speed is essential."* US: *"extra-fast running speed"*. Wiki: salta mais baixo, cai mais rápido, começa a correr mais tarde (empatado com Luigi). | OFICIAL + DOCUMENTADO [MW-PerfisToad][MW-3DW] |
| Física — Run / Wonder | Run: *"faithfully serves Princess Peach with impressive speed"* — corre mais rápido que Mario. Wonder: idêntico. | OFICIAL + DOCUMENTADO [MW-PerfisToad][MW-Run] |
| Captain Toad | Variante exploradora (mochila); as fontes oficiais divergem sobre ser o mesmo personagem; a ausência de salto do Captain Toad é amplamente descrita, mas não foi verificada nesta pesquisa. | DOCUMENTADO/ESTIMADO [MW-Toad] |
| Voz | Jen Taylor (1999–2006), Samantha Kelly (2007–2024), recontratação em *Mario Kart World* (2025): a imprensa (Game Rant/OpenCritic) nomeia **Paul Castro Jr.**; a Mario Wiki lista **Laila Berzins** — divergência registrada. Keegan-Michael Key nos filmes. | DOCUMENTADO [MW-Toad][OpenCritic-MKW] |

### 3.6 Toadette

| Campo | Conteúdo | Rótulo |
| --- | --- | --- |
| Papel | Estreia como parceira de Toad em *Mario Kart: Double Dash!!* (2003); co-protagonista de *Captain Toad: Treasure Tracker*; "Chief" no modo história de *Super Mario Maker 2*; jogável em Run, NSMBU Deluxe, SMM2 e Wonder. | DOCUMENTADO [MW-Toadette] |
| Visual | Chapéu rosa com pintas brancas, tranças que balançam ao se mover, vestido rosa sem mangas sobre colete vermelho; chapéu ligeiramente mais baixo que o de Toad. Cartão Wonder: *"spunky and knows how to have fun!"* | DOCUMENTADO + OFICIAL [MW-Toadette][MW-PerfisToadette] |
| Física — NSMBU Deluxe | Rótulo **"Easier"**; loja Nintendo: personagens *"optimized for younger and less-experienced players"*; +100 unidades de tempo (sem acúmulo no multi); *"Toadette and Nabbit are less slippery than Mario, Luigi, and Toad"* (para e resiste ao gelo melhor); nada como Penguin Mario; blocos de 1-Up dão 3-Up Moons. **Peachette** (Super Crown): site NOA *"With the help of a Super Crown, Toadette can magically transform into the super-powered Peachette"* — pulo duplo e flutuação; quica **uma vez** fora do abismo; não se agarra a paredes como o Flying Squirrel. Em Luigi U herda a física de Luigi. | OFICIAL + DOCUMENTADO [NOA-NSMBUD][MW-NSMBUD][MW-Toadette][MW-PerfisToadette] |
| Física — Run | Mais alta que Mario, quebra tijolos sem cogumelo (até 3.0.4 era derrotada em um golpe), velocidade/tração/salto médios; árbitra do Toad Rally e converte Toads. | DOCUMENTADO [MW-Toadette][MW-Run] |
| Física — SMM2 / Wonder | Idêntica aos demais. | DOCUMENTADO [MW-Toadette] |
| Voz | Samantha Kelly (até Wonder); Laura Stahl desde *Mario Kart World* (2025). | DOCUMENTADO [MW-Toadette][NE-WonderCast] |

### 3.7 Yoshi (personagem e montaria)

| Campo | Conteúdo | Rótulo |
| --- | --- | --- |
| Origem | Tezuka: *"Shigeru Miyamoto said he wanted Mario to ride a horse!"* (desenho na parede durante SMB3); Hino: *"The first keyword was horse, so I imagined something rather large and first drew up a creature like a large lizard"*; Tezuka: *"It was like a crocodile"*, *"It felt out of place to have a reptile suddenly appear in Mario's world"*; Hino poliu o esboço de Tezuka; a sela foi defendida como "concha" (*"It's related to turtles"*). Shigefumi Hino é o criador creditado. | OFICIAL [NUK-SNESYoshi][MW-Yoshi] |
| Visual/som | Nariz redondo, cristas laranja, sapatos laranja, sela em forma de concha; antes de *Yoshi's Story* a "voz" era dois *orchestra hits* com *pitch bend*; Kazumi Totaka o dubla desde 1997 (diz o próprio nome, grunhidos). Em Wonder, o rosto dos Yoshis **fica vermelho** ao fazer *flutter*. | DOCUMENTADO [MW-Yoshi][MW-FlutterJump] |
| Montaria — SMW | Mario monta pulando em cima; língua come inimigos (cada um vale uma moeda) e carrega cascos (verde cospe; vermelho = 3 bolas de fogo; amarelo = nuvens de areia; azul = voo); segurar casco demais → engole e perde o efeito; pular fora dá *Yoshi Boost* (salto extra); **se Yoshi é atingido, foge e Mario precisa alcançá-lo**; não entra em castelos, fortalezas e casas de fantasmas. Hino: a animação em que "Mario hits Yoshi on the head" foi reinterpretada como Mario dizendo "Go!" para o jogador não sentir pena. | DOCUMENTADO + OFICIAL [MW-SMW][MW-Yoshi][NUK-SNESYoshi] |
| Montaria — NSMB Wii/U | Booklet NSMB Wii (UK): *"When riding Yoshi, the actions available to Mario will change."* Manual NSMBU: *"If Yoshi takes damage, he will run away, but you can ride on him again if you manage to catch up with him."* *Flutter Jump* segurando o botão de salto; come quase tudo (até outros jogadores); 5 frutas → ovo com item; pisa em Spinies/Piranhas sem dano; **não pode sair da fase** (fica no final). Baby Yoshis (NSMBU): carregados, não montados (balão/bolha/luz). | OFICIAL + DOCUMENTADO [MW-PerfisYoshi][MW-NSMBW][MW-NSMBU][MW-FlutterJump] |
| Jogável — Wonder | Site oficial: *"Nabbit and Yoshis won't transform with power-ups, but they also don't take damage from enemies"*, *"perfect for players who are just starting out"*; *"they can all eat enemies, spit out stuff"*, *flutter*, carregam outros jogadores (Hayashida: útil para pais e filhos). Wiki: *"do not take damage from most enemies and obstacles, but they do take knockback"*; imprensa relata atordoamento breve. O sorteio aleatório de personagem **exclui** Yoshis e Nabbit. Tezuka testou Yoshi atirando ovos: *"it became hard to control, and to let first-time-players have fun, we decided the current way was the best."* Mouri recomenda Yoshi/Nabbit a novatos. | OFICIAL + DOCUMENTADO + OBSERVADO [NOA-Wonder][NMY-Wonder][MW-SMBW][NE-WonderRoster][ATD-Wonder4] |
| Jogável — Run | *"He can Flutter Jump, and he's got no fear of spikes!"*: pousa em Spinies/Grinders sem dano, anda sobre espinhos e Munchers; o *flutter* não pode ser usado deslizando; no modo fácil a altura resultante é um pouco menor que um salto normal. | OFICIAL + DOCUMENTADO [MW-PerfisYoshi][MW-Run][MW-FlutterJump] |
| *Flutter Jump* | Introduzido como mecânica central em *Yoshi's Island* (SMW não tem *flutter*; tem o *Yoshi Boost*); em YI pode ser repetido indefinidamente sem subir mais que o primeiro; em NSMBU/Wonder/Run ativa-se segurando o salto no ar. | DOCUMENTADO [MW-FlutterJump] |

---

## 4. Fichas complementares

### 4.1 Rosalina

- **Origem**: *Super Mario Galaxy* (2007); criada por Yoshiaki Koizumi, que escreveu o *Rosalina's Storybook* "tarde da noite" e em segredo; o time chegou a cogitar parentesco com Peach (**DOCUMENTADO** [Wiki-Rosalina][MW-Rosalina][SG-Rosalina]).
- **Visual/personalidade**: alta, loiro-platinado com franja cobrindo o olho direito, vestido água-marinha, broche-estrela, varinha; "wise, kind, and mature", figura materna dos Lumas, voz monótona em Galaxy; manual Galaxy: *"This keeper of the Comet Observatory floats through the cosmos with curious star creatures called Lumas."* (**OFICIAL** [MW-PerfisRosalina]).
- **Física — 3D World**: desbloqueada após World Star-2; trailer US: *"use her signature spin attack"*; corre mais devagar (empata com Peach), começa a correr mais cedo, tração normal; a wiki do personagem diz "very high jump", a tabela do jogo não lista diferença — divergência registrada; perde o giro com a maioria dos power-ups (**DOCUMENTADO/OFICIAL** [MW-3DW][MW-Rosalina][MW-PerfisRosalina]).
- **Wonder – Switch 2 Edition (2026)**: dica de carregamento *"Rosalina is traveling together with Luma, a star child, through the universe."* (**OFICIAL** [MW-PerfisRosalina]).
- **Voz**: Mercedes Rose (Galaxy, MK Wii, Galaxy 2), Kerri Kane (MK7, 2011), Laura Faye Smith (3D World 2013–) (**DOCUMENTADO** [MW-Rosalina]).

### 4.2 Wario

- **Origem**: antagonista de *Super Mario Land 2: 6 Golden Coins* (1992), protagonista a partir de *Wario Land*; criado por Hiroji Kiyotake com arte final de Yoichi Kotabe (referências: Bluto e Stromboli); nome = *warui* ("mau") + Mario. Guia Nintendo de 1993: *"Wario has always envied Mario for his bravery and good fortune."* (**DOCUMENTADO** + **OFICIAL** [MW-Wario][MW-PerfisWario]).
- **Visual**: boné amarelo com "W", camisa amarela, macacão roxo (originalmente rosa), sapatos verdes, bigode em zigue-zague, corpo atarracado — a inversão caricata de Mario (**DOCUMENTADO** [MW-Wario]).
- **Personalidade**: ganancioso, vaidoso, esquentado; site WarioWare: *"Here I am, your favorite dreamboat and all-around smart and cool guy!"*; Shake It!: *"Good guy? Not me!"* (**OFICIAL** [MW-PerfisWario]).
- **Movimentação (Wario Land)**: *Dash Attack* (ombrada) e *Ground Pound* desde a estreia; em *Wario Land II* **não morre** (*"No matter how much damage I take, I am immortal!"*): ser atingido empurra alguns passos e custa moedas; inimigos aplicam "reações" (Flat, Fat, Zombie, Hot, Puffy, Tiny…) que mudam a física e abrem caminhos; chefes "vencem" expulsando-o da arena (**DOCUMENTADO** [MW-Wario][MW-WL2]). É o precedente direto do modelo "sem morte por inimigo" de Nabbit.
- **Fora de NSMB Wii**: Miyamoto citou que Wario exigiria uma habilidade de pum, incompatível com a paridade (**OFICIAL** [Vooks-NSMBW]).
- **Voz**: Thomas Spindler (JP, MK64 → MKSC), Charles Martinet (1993/MK64 ocidental → *Strikers: Battle League*), Kevin Afghani (*WarioWare: Move It!*, 2023–; mais grave a partir de *Jamboree*) (**DOCUMENTADO** [MW-Wario][Wiki-Afghani]).

### 4.3 Waluigi

- **Origem**: *Mario Tennis* (N64, 2000); criado por Fumihide Aoki (Camelot) para dar a Wario um parceiro de duplas e a Luigi um rival; nome = *warui* + Luigi (**DOCUMENTADO** [MW-Waluigi][Wiki-Waluigi]).
- **Visual/personalidade**: muito alto e magro, queixo pontudo, nariz e bigode afilados, roxo com macacão índigo e sapatos laranja, emblema Γ (L invertido); fanfarrão, autopiedoso, trapaceiro que acusa os outros (**DOCUMENTADO** [MW-Waluigi]).
- **Plataforma**: **nunca foi jogável** em um Mario de plataforma principal; aparece como traje (*Super Mario Maker*, *Odyssey*) e decoração (Wonder S2 via amiibo) (**DOCUMENTADO** [MW-Waluigi]).
- **Voz**: Charles Martinet (2000–2022), Kevin Afghani (*Super Mario Party Jamboree*, 2024–) (**DOCUMENTADO** [MW-Waluigi][Wiki-Afghani]).

### 4.4 Donkey Kong

- **Origem**: antagonista do arcade *Donkey Kong* (1981), criado por Miyamoto (relação "amigável", DK como animal de estimação de Mario); redesenho da Rare em *Donkey Kong Country* (1994, Kevin Bayliss), gravata com "DK" desde o *Donkey Kong* de Game Boy (1994); design de 2025 segue o filme (**DOCUMENTADO** [MW-DK]).
- **Personalidade**: bravo, amigável, protetor da pilha de bananas, de pavio curto em *Mario vs. Donkey Kong*; "the strongest of the Kongs" (**DOCUMENTADO** [MW-DK]).
- **Diferenças de personagem em DKC** (modelo "dois personagens, dois envelopes"): DK mais forte e pesado (derrota Krusha azul e Army com um pulo; *Hand Slap* revela itens; joga barris por cima da cabeça, um pouco mais longe), Diddy mais rápido e ágil (não derrota inimigos fortes; segura o barril à frente como escudo); ambos rolam/cambalhotam e fazem *roll-jump*; **sistema de vida por dupla**: o Kong atingido foge e o outro assume; sem Kong reserva, perde-se a vida (**DOCUMENTADO** [MW-DKC]).
- **Voz**: Grant Kirkhope (DK64 1999–2001, clipes reutilizados até 2013), Takashi Nagasako (2004–2025, desde *Mario Power Tennis*), Seth Rogen (filme) (**DOCUMENTADO** [MW-DK]).

### 4.5 Nabbit

- **Origem/visual**: *New Super Mario Bros. U* (2012); coelho roxo com orelhas longas, membros pretos, lenço branco com boca desenhada, sapatos laranja, sempre com um saco; fala de estreia *"I'm Nabbit. I'm fast. Faster than you."*; site NSMBUD: *"Enemies never seem to notice this sticky-fingered thief, who can sneak past the bad guys to snag items, which he stuffs into his sack!"* (**DOCUMENTADO** + **OFICIAL** [MW-Nabbit][MW-PerfisNabbit]).
- **Como inimigo (NSMBU)**: perseguição de **100 unidades de tempo**; pegá-lo dá um P-Acorn; três falhas o fazem sumir; aparece em um estágio por mundo nos sete primeiros (**DOCUMENTADO** [MW-Nabbit][MW-NSMBU]).
- **Jogável — New Super Luigi U**: imune a inimigos (anda por cima deles e de espinhos), mas sofre *knockback* de inimigos fortes e chefes; morre em poços, lava, veneno, esmagamento, Cheep Chomp, cinzas e tempo; não usa power-ups (exceto Super Star), não carrega itens nem monta Yoshi; itens coletados saem como 1-Ups no fim (até 8 por fase) (**DOCUMENTADO** [MW-Nabbit][MW-NSLU]).
- **Jogável — NSMBU Deluxe**: rótulo **"Easiest"** ("Very Easy" no inglês britânico); +100 unidades de tempo; agora carrega itens e Baby Yoshis; quica em Yoshi (não monta); nado tipo Penguin; "less slippery"; power-ups valem 1.000 pontos; fases concluídas marcadas em roxo; fora do Challenge Mode (**DOCUMENTADO** [MW-Nabbit][MW-NSMBUD]).
- **Jogável — Wonder**: dica oficial *"Running into enemies won't bother Nabbit in the least."*; não recua nem pisca ao tocar inimigos; power-ups viram **flower coins** (*"can turn any extra power-ups he finds into flower coins"*, site); pode montar Yoshi; ainda encolhe sob efeitos Wonder específicos (Hoppycat, Wubba); morre em poços/lava/veneno (**OFICIAL** + **DOCUMENTADO** [MW-PerfisNabbit][NOA-Wonder][MW-Nabbit]).
- **Voz/som**: Natsuko Yokoyama (2012–2020, citação pendente na wiki), Dawn M. Bennett (2023–); em *Super Mario Maker* o salto tem "a short squeaky noise" (**DOCUMENTADO** [MW-Nabbit][NE-WonderCast]).

---

## 5. Síntese: o que cada título faz com cada personagem

| Personagem | SMB2 USA (1988) | NSMB Wii (2009) | New Super Luigi U (2013) | 3D World (2013) | Run (2016) | NSMBU Deluxe (2019) | Wonder (2023) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Mario | equilibrado (OFICIAL) | base | ausente | equilibrado | precisa de cogumelo para crescer | base | base |
| Luigi | salto maior, desce devagar, lento (OFICIAL) | = Mario (OFICIAL) | salto maior + menos tração (DOC) | salto maior, escorrega, *scuttle* (DOC) | salto maior + *scuttle* (DOC) | = Mario; em Luigi U física de Luigi | = Mario (OFICIAL) |
| Peach | flutua ~1,5 s, salto cai muito com item (OFICIAL) | excluída por flutuar (OFICIAL) | — | flutua "few extra seconds", mais lenta, cai devagar (OFICIAL/DOC) | queda lenta reativável (DOC) | — | = Mario (OFICIAL) |
| Daisy | — | — | — | — | pulo duplo (OFICIAL) | — | = Mario (DOC) |
| Toad | salto mais baixo, força (OFICIAL); 43 vs 36 subpx/q com item (DOC) | 2 Toads = Mario (OFICIAL) | física de Luigi | mais rápido, salto baixo, cai rápido (OFICIAL/DOC) | mais rápido (OFICIAL) | = Mario | = Mario |
| Toadette | — | — | — | — | neutra, quebra tijolos (DOC) | "Easier": menos escorregadia, +100 t, Peachette (DOC/OFICIAL) | = Mario (DOC) |
| Yoshi | — | montaria: *flutter*, come, fica na fase (OFICIAL/DOC) | montaria | — | *flutter*, imune a espinhos (OFICIAL) | montaria + Baby Yoshis | jogável: sem dano, *knockback*, sem power-up, carrega (OFICIAL/DOC) |
| Nabbit | — | — | sem dano, sem power-up, itens → 1-Up (DOC) | — | — | "Easiest", +100 t (DOC) | sem dano, sem recuo, power-up → flower coin (OFICIAL) |
| Rosalina | — | — | — | giro, mais lenta (OFICIAL/DOC) | — | — | S2 Edition (OFICIAL) |

---

## 6. Tabela de parâmetros numéricos conhecidos e conversões

| Parâmetro | Valor documentado | Conversão / leitura | Rótulo | Fonte |
| --- | --- | --- | --- | --- |
| Mario pequeno (NES) | 12×16 px desenhado em célula 16×16; saltando 16×16 | hitbox ≈ 1 bloco | DOCUMENTADO | [MW-AssetsSMB] |
| Super Mario (NES) | 16×32 px; agachado 16×22 | 2 blocos; relação 2:1 | DOCUMENTADO | [MW-AssetsSMB][MW-SuperForm] |
| Mario pequeno/Raccoon (SMB3) | 16×16 / 24×32 | cauda acrescenta 8 px de largura visual | DOCUMENTADO | [MW-AssetsSMB3] |
| Mario pequeno/grande (SMW) | 15×21 / 15×27 (olhando para cima) | ~1,3 / ~1,7 blocos | DOCUMENTADO | [MW-AssetsSMW] |
| Lost Levels: salto Mario / Luigi | 4 / 5,5 blocos | 64 / 88 px; razão **1,375** → razão de velocidade inicial √1,375 = 1,173 | DOCUMENTADO | [MW-LostLevels] |
| Lost Levels: salto correndo | 5 / 6 blocos | 80 / 96 px; razão 1,2 | DOCUMENTADO | idem |
| Lost Levels: derrapagem | 2 / 4 blocos | 32 / 64 px; razão **2,0** → atrito de Luigi ≈ metade (d = v²/2a) | DOCUMENTADO + ESTIMADO | idem |
| SMB2 USA: andar | 24 subpx/q = 1,5 px/q | 90 px/s (×1,875 → 169 px/s) | DOCUMENTADO | [TAS-SMB2] |
| SMB2 USA: correr | 36 subpx/q = 2,25 px/q | 135 px/s (×1,875 → 253 px/s) | DOCUMENTADO | idem |
| SMB2 USA: Toad correndo com item pesado | 43 subpx/q = 2,69 px/q | 161 px/s (+19 %) | DOCUMENTADO | idem |
| SMB2 USA: flutuação de Peach | "about 1.5 seconds" | 90 q | OFICIAL (manual SMA) | [MW-PerfisPeach] |
| SMB2 USA: HP | 2 pontos iniciais; pequeno a 1 HP; até 4 (5 no SMA) | modelo de vida alternativo ao encolher | DOCUMENTADO | [MW-SmallMario] |
| SMB: invencibilidade pós-dano | "flashes for eight game seconds" | unidade do cronômetro ≠ segundo; ≈3,2 s se 0,4 s/unid. (SMB1, documentação comunitária) ou 4,8–5,6 s se 0,6–0,7 s/unid. (regra geral citada pela Mario Wiki) | DOCUMENTADO + ESTIMADO | [TMK-SMB][MW-TimeLimit] |
| SMB: Super Star | "about 30 game seconds" | ≈12 s a 0,4 s/unid. (coincide com os 12 s do Lume) | DOCUMENTADO + ESTIMADO | [TMK-SMB] |
| Aviso de tempo | ≤100 unidades: jingle + música acelera (SMW: 100 s reais) | dica de "perigo" sonora, não visual | DOCUMENTADO | [MW-TimeLimit] |
| NSLU: tempo por fase | 100 unidades (torres/castelos +100 após a porta do chefe) | tique alongado para calibrar (Tezuka) | DOCUMENTADO/OFICIAL | [MW-NSLU][Siliconera-NSLU] |
| NSMBUD: bônus de tempo Toadette/Nabbit | +100 unidades | acessibilidade por personagem | DOCUMENTADO | [MW-NSMBUD] |
| Wonder: elenco e badges | 12 personagens; >20 badges de >50 protótipos | acessibilidade por equipamento | OFICIAL | [ATD-Wonder3] |
| Wonder: juntas do modelo | 12 juntas; animações "more than doubled" vs NSMBU | expressividade facial por personagem | OFICIAL | [ATD-Wonder2] |
| Run: hits antes de perder | 2 para todos a partir da 3.0.4 (forma pequena para todos) | paridade de dano | DOCUMENTADO | [MW-Run] |

---

## 7. Padrões transversais

### 7.1 Silhueta antes de tudo
Todo o elenco segue a lógica "forma dita função" do Mario de 1981: cores de alto contraste entre braço e tronco (macacão), cabeça grande com chapéu que fixa os olhos, nenhum cabelo animado nos pequenos. As variações de elenco são **desvios controlados de uma silhueta-base**: Luigi = mais alto/fino, Wario = mais largo/baixo, Waluigi = exagero vertical de Luigi, Toads = cabeça-cogumelo em cores, Yoshis = quatro cores da mesma malha, Peach e Daisy = mesma altura do Mario crescido em Wonder (**OFICIAL**/**DOCUMENTADO**, seções 3–4). Para o jogador, a cor diz **quem** e o formato diz **o que faz**.

### 7.2 Paridade × arquétipos (argumentos documentados)
- A favor dos arquétipos: rejogabilidade e expressão (SMB2 USA; Tezuka: trocar para Luigi tornou fases difíceis "not so much anymore", logo mudou o desenho das fases) (**OFICIAL** via Siliconera).
- Contra: certas ações viram **exclusividade** (Mouri) e o envelope de alcance de salto de uma princesa que flutua invalida a métrica das fases (Miyamoto) (**OFICIAL**).
- Solução intermediária da própria Nintendo: (a) *Luigi Block* liga/desliga a física especial (NSLU); (b) personagem "fácil" com tempo extra e sem dano (NSMBUD); (c) habilidades em badges separadas do personagem (Wonder).

### 7.3 Acessibilidade escalonada
Super Guide (Luigi joga por você após 8 falhas, NSMB Wii), Nabbit/Toadette com rótulos de dificuldade e +100 de tempo (NSMBUD), Yoshi/Nabbit sem dano + badges de segurança (*Safety Bounce* que "automatically bounces the character out of pits") + lojas de sementes para quem não termina fases (Wonder) (**OFICIAL**/**DOCUMENTADO** [MW-NSMBW][MW-NSMBUD][ATD-Wonder3]). O personagem invencível **nunca** é imune a poços, lava e tempo.

### 7.4 Dano, perigo e morte (modelo comum)
1. Forma superior → Super → pequeno → perder vida (SMB/Lost Levels/SMW original pulam a etapa Super). 2. Ao encolher: piscar + invencibilidade curta (SMB ≈ "8 game seconds"). 3. Yoshi montado funciona como "golpe extra": o montador cai e Yoshi foge (SMW, NSMBU). 4. Perigo comunicado por som (jingle dos 100) e por animação (Yoshi fica vermelho ao *flutter*; Goombas de Wonder "mordem com um sorriso"; Luigi treme). 5. Morte: congela o mundo, pose frontal, pulo, queda para fora da tela (SMB→SMW). Observação: animações de equilíbrio na borda ("teeter") e de ociosidade em 2D **não foram localizadas em fontes verificáveis** nesta pesquisa (ver seção 11).

### 7.5 Som por personagem
Kondo (Wonder): *cada personagem tem um som de salto distinto*, e o som muda conforme o tipo de salto — primeira vez na série (**OFICIAL** [ATD-Wonder2]). Toads Amarelo/Azul têm registros agudo/grave trocados entre jogos; Nabbit salta com "squeak"; Yoshi diz "Yoshi!". Vozes humanas são uma camada **separada** da identidade sonora dos saltos — algo que o Lume (chiptune, sem dubladores) pode reproduzir com timbres.

---

## 8. Como os jogos resolvem "fases obrigatórias não podem ficar impossíveis"

| Estratégia | Onde | Como funciona | Rótulo |
| --- | --- | --- | --- |
| Envelope único | NSMB Wii, Wonder | Todos têm a mesma física; diferenças são cosméticas ou vão para badges opcionais | OFICIAL |
| Envelope mínimo + compensador | SMB2 USA | Toad tem o salto mais baixo, mas o *Power Squat Jump* (carregar agachado "until your character starts to flash") existe para **todos** e é ensinado pela fase 1-1 | DOCUMENTADO/OFICIAL [MW-PowerSquat][TAS-SMB2] |
| Redesenhar o mundo para o novo envelope | New Super Luigi U | 82 fases novas para a física de Luigi; 100 unidades de tempo; física antiga disponível via Luigi Block | DOCUMENTADO/OFICIAL |
| Personagem invencível | NSLU/NSMBUD/Wonder | Sem dano de inimigos, mas poços/lava matam → o desenho de plataformas continua válido | OFICIAL/DOCUMENTADO |
| Excluir habilidade que quebra a métrica | NSMB Wii (Peach), Wonder (float de Peach) | A flutuação muda o alcance horizontal; ou se exclui o personagem ou se move a habilidade para um badge | OFICIAL |
| Dupla com envelopes diferentes + vida compartilhada | Donkey Kong Country | DK forte e Diddy ágil; o Kong atingido foge e o outro assume; fases concluíveis com qualquer um | DOCUMENTADO [MW-DKC] |

---

## 9. Fontes de inspiração legítimas (o que **não** fazer)

- Não copiar silhuetas, paletas (vermelho/azul + boné com inicial, verde/azul, rosa + coroa), nomes, frases ("It's-a me"), timbres de voz ou sons reconhecíveis. O Lume já é um personagem próprio em um mundo próprio ("As Cinco Fronteiras"); o elenco deve nascer do **mesmo método** (função → forma), não das mesmas respostas.
- Usar apenas os **princípios** documentados: três quadros legíveis, contraste braço/tronco, cabeça grande, cores como identificador, pose de salto com braços abertos, parada brusca, pisca ao sofrer dano, morte frontal com pulo.

---

## 10. Implicações para o Lume — decisões e parâmetros

### 10.1 Decisão central: núcleo compartilhado + variações por envelope + habilidades destacáveis

**Decisão**: adotar o modelo híbrido (c) da seção 7.2.

1. **Todos os personagens compartilham `MovementProfile` base, hitboxes (22×30 / 22×46) e o modelo de dano**, como em NSMB Wii/Wonder. Isso preserva as 15 fases já desenhadas (`data/levels/*.json`) e os *traces* de ouro.
2. **Cada personagem recebe um `CharacterDelta` limitado por envelope** (SMB2/3D World/NSLU): altura de salto entre 0,85× e 1,21× da base; velocidade de corrida entre 0,93× e 1,12×; atrito no chão entre 0,6× e 1,3×. Os limites vêm das razões documentadas (Lost Levels 1,375 em salto e 2,0 em derrapagem foram **reduzidos** porque o Lume não terá fases redesenhadas por personagem como NSLU).
3. **Habilidades que mudam o alcance horizontal** (flutuar, pulo duplo) são **equipáveis** (modelo *badge* de Wonder) ou, quando nativas de um personagem, **limitadas em tempo e velocidade** para que nenhum caminho obrigatório dependa delas e nenhum atalho obrigatório seja aberto só por elas.
4. **Um personagem invencível a inimigos** para iniciantes (modelo Nabbit/Yoshi), com as mesmas regras de poço/lava/tempo.
5. **Regra de ouro verificada por teste**: toda rota obrigatória da campanha é concluída pelo **perfil mínimo** (menor salto sem carregar, menor velocidade, maior atrito) no condutor de rotas (`tests/gameplay/route_player.py`), e nenhuma relíquia é alcançável **somente** por flutuação ou pulo duplo (há sempre rota alternativa, como em Wonder os blocos ocultos por personagem são apenas cosméticos).

### 10.2 Elenco original proposto (nomes provisórios, temática de luz e vento das Cinco Fronteiras)

| Personagem | Arquétipo estudado (origem) | Papel narrativo | Silhueta (mesmo hitbox) | Cor-identidade |
| --- | --- | --- | --- | --- |
| **Lume** | Mario "all-rounder" (SMB2/SMA/3D World) | protagonista, portador da luz | cabeça grande, lanterna no cinto, braços em cor contrastante | âmbar/azul-noite |
| **Vento** | Luigi (Lost Levels/NSLU/3D World) | irmão mais alto e tímido, salta mais e escorrega | mais alto dentro do hitbox, cachecol que marca a direção no ar | verde-folha |
| **Fagulha** | Toad (SMB2/3D World) | rápida, salto curto, salto carregado | baixa, capuz esférico, pernas curtas visíveis correndo | laranja-brasa |
| **Aurora** | Peach (SMB2/3D World) com limites | planadora de recuperação | capa que abre ao flutuar | lilás-madrugada |
| **Pirilampo** | Nabbit/Yoshi (NSLU/NSMBUD/Wonder) | personagem para iniciantes, sem dano de inimigos, sem poderes | corpo arredondado luminoso, olhos grandes | verde-lima brilhante |

### 10.3 Constantes propostas (Python, px/s, px/s², s; passo 1/120 s)

Base = `CALIBRATED_PROFILE` atual (`walk 220`, `run 340`, `jump 590`, `g 1550`, `ground_friction 1500`, `ice_friction 180`, `hurt_invulnerability 2.0`). Alturas e tempos calculados com `h = v²/2g`, `t = v/g` (arco simétrico; com o preset B assimétrico de `FISICA.md` os valores absolutos mudam, as razões não).

```python
# game/characters/roster.py — deltas aplicados sobre o MovementProfile base
# Rótulos: OFICIAL/DOCUMENTADO indicam a origem da RAZÃO; os valores absolutos são ESTIMADOS.
from dataclasses import dataclass, field

@dataclass(slots=True, frozen=True)
class CharacterDelta:
    jump_speed_mul: float = 1.0        # altura ∝ mul²
    run_speed_mul: float = 1.0
    walk_speed_mul: float = 1.0
    ground_accel_mul: float = 1.0
    ground_friction_mul: float = 1.0   # <1 escorrega mais (Lost Levels: derrapagem 2×)
    ice_friction_mul: float = 1.0
    air_accel_mul: float = 1.0
    abilities: tuple[str, ...] = ()
    damage_model: str = "standard"     # "standard" | "invincible"
    time_bonus: float = 0.0            # s extra por fase (NSMBUD: +100 unidades)

ROSTER = {
    "lume":      CharacterDelta(),
    # Luigi-like: salto ×1,21 em altura (jump 590 → 650), derrapagem ×1,67 (atrito 1500 → 900),
    # aceleração menor (Lost Levels/SMB2 "rather slow"); scuttle só reduz a queda, não propulsiona.
    "vento":     CharacterDelta(jump_speed_mul=1.10, ground_friction_mul=0.60, ice_friction_mul=0.75,
                                ground_accel_mul=0.90, air_accel_mul=0.90, abilities=("scuttle",)),
    # Toad-like: corre +12 % (340 → 380), anda +11 % (220 → 245), arranca +20 %, salto ×0,85 em altura
    # (590 → 545); compensador = salto carregado agachado (SMB2 Power Squat): jump ×1,085 em v (→ 640).
    "fagulha":   CharacterDelta(jump_speed_mul=0.92, run_speed_mul=1.12, walk_speed_mul=1.11,
                                ground_accel_mul=1.20, abilities=("charged_jump",)),
    # Peach-like: corre −7 % (340 → 315) mas arranca antes (+10 %); flutuação limitada (ver 10.4).
    "aurora":    CharacterDelta(run_speed_mul=0.93, ground_accel_mul=1.10, abilities=("float",)),
    # Nabbit/Yoshi-like: física base, sem dano de inimigos, sem power-ups, +100 s de tempo.
    "pirilampo": CharacterDelta(damage_model="invincible", time_bonus=100.0,
                                ground_friction_mul=1.30, ice_friction_mul=2.2),  # "less slippery" (NSMBUD)
}

# Habilidades (parâmetros em segundos e px/s)
SCUTTLE_FALL_GRAVITY_MUL = 0.70   # Vento: gravidade de queda ×0,7 enquanto segura o salto na descida (SMB2 "descends slowly")
CHARGED_JUMP_HOLD = 0.50          # Fagulha: agachada parada por 0,5 s → pisca (SMB2 "until your character starts to flash")
CHARGED_JUMP_SPEED_MUL = 1.175    # sobre o jump da própria Fagulha (545 → 640 px/s; altura 96 → 132 px)
FLOAT_MAX_DURATION = 0.80         # Aurora: 3D World "much shorter" que os 1,5 s de SMB2 (OFICIAL) → 0,8 s (ESTIMADO)
FLOAT_FALL_SPEED = 60.0           # vy limitado a +60 px/s durante o float (quase paira, como em SMB2)
FLOAT_AIR_SPEED_CAP = 220.0       # velocidade horizontal limitada ao andar durante o float (limita o alcance extra)
FLOAT_ONCE_PER_AIRTIME = True     # regra de Melee/SMB2: um float por salto
INVINCIBLE_KNOCKBACK = 160.0      # Pirilampo: empurrão ao tocar inimigo (Wonder Yoshi "do take knockback")
INVINCIBLE_STUN = 0.30            # s sem controle após o toque (OBSERVADO em Wonder; ESTIMADO)
```

### 10.4 Verificação numérica dos envelopes (ESTIMADO, arco simétrico g = 1550)

| Personagem | v salto (px/s) | altura (px) | tempo no ar (s) | alcance correndo (px) | distância de parada de 340 px/s (px) |
| --- | --- | --- | --- | --- | --- |
| Lume (base) | 590 | 112,3 | 0,761 | 259 | 38,5 |
| Vento | 649 | 135,9 (×1,21) | 0,837 | 285 (+10 %) | 64,2 (×1,67) |
| Fagulha | 543 | 95,1 (×0,85) | 0,700 | 267 (run 380) | 48,1 (run maior) |
| Fagulha carregada | 638 | 131,2 | 0,823 | 313 | — |
| Aurora | 590 | 112,3 | 0,761 (+0,80 de float) | 241 (run 315) + ≤176 de float | 33,0 |
| Pirilampo | 590 | 112,3 | 0,761 | 259 | 29,6 (atrito ×1,3) |

Consequências para o desenho de fases (regras a codificar no validador de níveis `game/levels/validator.py`):
- **Degrau vertical obrigatório ≤ 88 px** (Fagulha sem carregar, com margem de 7 px); degraus de 89–120 px só em rotas opcionais ou após o tutorial do salto carregado (como SMB2 ensina o *Power Squat* em 1-1).
- **Vão horizontal obrigatório ≤ 230 px** com pista de corrida ≥ 2 s (perfil mínimo de alcance é Aurora correndo, 241 px, com margem).
- **Teto baixo obrigatório ≥ 136 px acima do piso** nos trechos em que Vento precise saltar (seu salto maior não pode bater a cabeça onde Lume passa).
- **Nada obrigatório atrás de um float**: o alcance extra de Aurora (≤176 px) e a carga de Fagulha abrem **apenas** atalhos e relíquias com rota alternativa.
- **Gelo**: Vento com `ice_friction` 135 px/s² precisa de 428 px para parar de 340 px/s — plataformas de gelo com borda em rota obrigatória devem ter ≥ 450 px ou guarda-corpo; para Pirilampo o gelo quase não existe (regra de acessibilidade, como "less slippery" em NSMBUD).

### 10.5 Dano, perigo e morte por personagem

| Evento | Lume/Vento/Fagulha/Aurora | Pirilampo | Origem |
| --- | --- | --- | --- |
| Toque em inimigo | fogo → crescido → pequeno → perde vida; `hurt_invulnerability` 2,0 s (SMB ≈ 3 s; manter 2,0 e piscar a 8 Hz — ESTIMADO) | `knockback` 160 px/s, `stun` 0,3 s, sem encolher, sem piscar (Nabbit "does not flinch"; Yoshi "knockback") | DOCUMENTADO |
| Poço, lava, água, tempo | perde vida (já implementado em `Game.die`) | **perde vida** (Nabbit/Yoshi morrem em poços e lava) | OFICIAL/DOCUMENTADO |
| Power-up | efeito normal | vira pontuação/moeda (Wonder: flower coins; NSMBUD: 1.000 pts) — propor **+250 pts e +1 moeda** | OFICIAL |
| Estrela | 12 s de invencibilidade (SMB1 ≈ 30 unidades ≈ 12 s) | permitida (Nabbit usa Super Star em NSLU) | DOCUMENTADO |
| Morte | congelar o mundo 0,25 s → pose frontal → `vy = −420 px/s` → cair até sair da tela → reiniciar em 1,5 s (padrão SMB→SMW) | idem | DOCUMENTADO (qualitativo) + ESTIMADO (números) |
| Aviso de tempo | aos 100 s: jingle + música 1,25× (SMB/SMB3/SMW/NSMB) | idem | DOCUMENTADO |
| Expressão de perigo | Vento: tremer parado ao lado de um abismo ou chefe (3D World "tremble"); Aurora: capa fecha ao cair rápido; Fagulha: olhos arregalados ao derrapar | Pirilampo: pisca os olhos ao ser empurrado | OFICIAL (traço) + ESTIMADO (aplicação) |

### 10.6 Animação e som por personagem (sobre `game/characters/animation.py`)

- Manter a **máquina de estados compartilhada** (`AnimState`) e permitir `ClipSpec` por personagem (`DEFAULT_CLIPS` já é "ajustável por personagem"). Estados novos: `FLOAT` (Aurora), `CHARGE` (Fagulha, com piscar após 0,5 s), `SCUTTLE` (Vento, substitui `FALL` enquanto segura o salto), `BUMP` (Pirilampo, substitui `HURT`).
- Poses herdadas do método Nintendo: salto com braços abertos (**OFICIAL**), parada brusca com derrapagem (**OFICIAL**), rosto sempre visível mesmo de costas para a câmera (**OFICIAL**), olhar para cima ao segurar ↑ (SMW, **DOCUMENTADO**).
- **Som**: um timbre de salto por personagem (Kondo, **OFICIAL**): Lume onda quadrada com *sweep* curto; Vento onda triangular mais longa (salto mais alto); Fagulha clique de ruído curto; Aurora seno suave com cauda; Pirilampo "squeak" agudo (Nabbit em SMM, **DOCUMENTADO**). Variar o som por tipo de salto (normal, carregado, de inimigo), como em Wonder. Vozes: **nenhuma dublagem**; "vocábulos" sintetizados com altura distinta por personagem (Lume médio, Vento grave, Fagulha agudo).

### 10.7 Dados declarativos

```json
// data/characters/vento.json (esboço)
{
  "id": "vento",
  "name": { "pt-BR": "Vento" },
  "palette": { "primary": "#3fa34d", "secondary": "#1d3557", "accent": "#f1faee" },
  "delta": { "jump_speed_mul": 1.10, "ground_friction_mul": 0.60, "ice_friction_mul": 0.75,
             "ground_accel_mul": 0.90, "air_accel_mul": 0.90 },
  "abilities": ["scuttle"],
  "damage_model": "standard",
  "clips": { "fall": { "frames": 4, "fps": 14, "loop": true, "state": "scuttle" } },
  "sfx": { "jump": { "wave": "triangle", "f0": 440, "f1": 880, "dur": 0.16 } },
  "unlock": { "world": 2 }
}
```

### 10.8 Testes propostos (pytest, Python puro)

1. `test_roster_envelopes`: para cada personagem, `0.85 ≤ h/h_base ≤ 1.21`, `0.93 ≤ run/run_base ≤ 1.12`, `0.6 ≤ atrito/atrito_base ≤ 1.3`.
2. `test_mandatory_routes_min_profile`: as rotas de `tests/gameplay/test_campaign_routes.py` passam com **Fagulha sem carga** e com **Aurora sem float** (perfis mínimos de altura e alcance).
3. `test_float_reach_bound`: alcance extra do float ≤ 180 px em qualquer entrada.
4. `test_invincible_rules`: Pirilampo nunca muda `power`, nunca entra em `HURT`, morre em poço/lava/tempo, recebe `knockback` de 160 px/s.
5. `test_level_validator_geometry`: nenhum degrau obrigatório > 88 px; nenhum vão obrigatório > 230 px; tetos ≥ 136 px onde há salto obrigatório.
6. `test_charged_jump_timing`: carga completa em 0,5 s parado; mover cancela (SMB2).

---

## 11. Lacunas e incertezas

1. **Entrevista Iwata Asks de New Super Luigi U** (iwataasks.nintendo.com) retornou 503 em todas as tentativas; as citações de Tezuka vieram da cobertura da Siliconera. A justificativa oficial para a física de Luigi e para Nabbit deve ser conferida na fonte primária quando o site voltar.
2. **Páginas oficiais de personagens** (mario.nintendo.com/characters, supermario3dworld.nintendo.com/play-together, supermariorun.com/characters) estavam indisponíveis (503/404); as bios oficiais foram tomadas da compilação "List of … profiles and statistics" da Super Mario Wiki, que transcreve manuais e sites — verificar contra os originais antes de citar como texto da Nintendo.
3. **Valores numéricos de personagem** só existem para Lost Levels (guia All-Stars, em blocos) e SMB2 USA (TASVideos, velocidades). Não há dados para a altura de salto de Luigi em NSLU/3D World/Run, nem para a gravidade reduzida de Luigi em SMB2 (só relato de fórum), nem para a duração do float de Peach em 3D World/Run.
4. A **contradição Toad "mais rápido"** (estrelas/manuais) × **velocidade máxima igual** (TASVideos) sugere que a diferença de SMB2 está na aceleração, no manuseio de itens ou na percepção — não foi possível confirmar sem desmontagem (e desmontagem não é fonte admissível aqui).
5. **Animações de ociosidade e de equilíbrio na borda** em NSMB/NSMB Wii/U/Wonder não foram encontradas em fontes verificáveis; a wiki "Sleep" só documenta jogos 3D e *Super Paper Mario*. Tratar como OBSERVADO/ESTIMADO até haver fonte.
6. **Dubladores de 2025**: a imprensa (Game Rant/OpenCritic) nomeia Paul Castro Jr. para Toad em *Mario Kart World*; a Super Mario Wiki lista Laila Berzins. Não resolvido.
7. **Unidade do cronômetro**: TMK dá valores em "game seconds"; a Mario Wiki fala em 0,6–0,7 s por unidade "na maioria dos jogos", enquanto a documentação comunitária do SMB1 costuma indicar ~0,4 s. As conversões da seção 6 são intervalos ESTIMADOS.
8. **Hitbox × silhueta**: não há fonte sobre se Luigi (mais alto) tem hitbox diferente em NSMB; a proposta de hitbox único para o elenco do Lume é ESTIMADA, embasada na paridade declarada e na altura igual de Peach/Mario em Wonder.
9. **Captain Toad não pular** e **Yoshi atordoado em Wonder** são relatos de guias/imprensa (OBSERVADO), não confirmados em fonte oficial.
10. **Rosalina em 3D World**: a página do personagem diz "very high jump"; a tabela do jogo não lista diferença de salto. Sem resolução.

---

## 12. Fontes

Tipos: **oficial** (Nintendo/desenvolvedores), **docs** (wiki/compilação com fonte), **técnico** (documentação comunitária derivada de análise), **entrevista** (reproduzida pela imprensa), **comunitário** (imprensa/análise de gameplay).

| Tag | Tipo | Título | URL |
| --- | --- | --- | --- |
| [IA-Overalls] | oficial | Iwata Asks: New Super Mario Bros. Wii, Vol. 1, "The Reason Mario Wears Overalls" | https://www.nintendo.com/en-gb/Iwata-Asks/Iwata-Asks-New-Super-Mario-Bros-Wii/Volume-1/2-The-Reason-Mario-Wears-Overalls/2-The-Reason-Mario-Wears-Overalls-210759.html |
| [NUK-SNESYoshi] | oficial | Nintendo Classic Mini SNES developer interview Vol. 5 – Super Mario World & Yoshi's Island | https://www.nintendo.com/en-gb/News/2017/October/Nintendo-Classic-Mini-SNES-developer-interview-Volume-5-Super-Mario-World-and-Super-Mario-World-2-Yoshi-s-Island-1290850.html |
| [ATD-Wonder1] | oficial | Ask the Developer Vol. 11, Super Mario Bros. Wonder — Part 1 | https://www.nintendo.com/us/whatsnew/ask-the-developer-vol-11-super-mario-bros-wonder-part-1/ |
| [ATD-Wonder2] | oficial | Ask the Developer Vol. 11 — Part 2 | https://www.nintendo.com/us/whatsnew/ask-the-developer-vol-11-super-mario-bros-wonder-part-2/ |
| [ATD-Wonder3] | oficial | Ask the Developer Vol. 11 — Part 3 | https://www.nintendo.com/us/whatsnew/ask-the-developer-vol-11-super-mario-bros-wonder-part-3/ |
| [ATD-Wonder4] | oficial | Ask the Developer Vol. 11 — Part 4 | https://www.nintendo.com/us/whatsnew/ask-the-developer-vol-11-super-mario-bros-wonder-part-4/ |
| [NOA-Wonder] | oficial | Super Mario Bros. Wonder — página de produto Nintendo (US) | https://www.nintendo.com/us/store/products/super-mario-bros-wonder-switch/ |
| [NMY-Wonder] | oficial | Super Mario Bros. Wonder — página oficial (Nintendo MY) | https://www.nintendo.com/my/games/feature/mario-wonder/index.html |
| [NOA-NSMBUD] | oficial | New Super Mario Bros. U Deluxe — página de produto Nintendo (US) | https://www.nintendo.com/us/store/products/new-super-mario-bros-u-deluxe-switch/ |
| [Vooks-NSMBW] | entrevista | Additional characters omitted in NSMBW due to ability differences (Miyamoto/Famitsu via 1UP, 2009) | https://www.vooks.net/additional-characters-omitted-in-nsmbw-due-to-ability-differences/ |
| [NE-WonderRoster] | entrevista | Nintendo on how Mario Wonder characters were decided, scrapped Yoshi mechanic (Famitsu, 2023) | https://nintendoeverything.com/?p=824190 |
| [Siliconera-NSLU] | entrevista | How Luigi got his own game with New Super Luigi U (resumo do Iwata Asks) | https://www.siliconera.com/how-luigi-got-his-own-game-with-new-super-luigi-u/ |
| [Gizmodo-Afghani] | comunitário | Nintendo finally confirms Mario's new voice actor | https://gizmodo.com/nintendo-finally-confirms-marios-new-voice-actor-1850926459 |
| [NE-WonderCast] | comunitário | Full list of new Super Mario Bros. Wonder voice actors | https://nintendoeverything.com/super-mario-bros-wonder-voice-cast-new-actors/ |
| [Siliconera-Kelly] | comunitário | Samantha Kelly doesn't voice Peach and Toad in Mario Kart World | https://www.siliconera.com/samantha-kelly-doesnt-voice-peach-and-toad-in-mario-kart-world/ |
| [OpenCritic-MKW] | comunitário | Mario Kart World voice actors for Peach and Toad revealed | https://opencritic.com/news/19097/mario-kart-world-voice-actors-for-peach-and-toad-revealed |
| [NL-Kelly] | comunitário | Princess Peach's voice actor has been replaced after 18 years | https://www.nintendolife.com/news/2025/06/princess-peachs-voice-actor-has-been-replaced-after-18-years |
| [Destructoid-Wonder] | comunitário | How do Yoshi and Nabbit work in Super Mario Bros. Wonder | https://www.destructoid.com/how-do-yoshi-and-nabbit-work-in-super-mario-bros-wonder/ |
| [TToOVG-Death] | comunitário | The Origin of Mario's Trademark Death Animation | https://www.thrillingtalesofoldvideogames.com/blog/mario-death-animation-origin |
| [TMK-SMB] | técnico | The Mushroom Kingdom — Super Mario Bros. breakdown | https://themushroomkingdom.net/smb_breakdown.shtml |
| [TAS-SMB2] | técnico | TASVideos — Super Mario Bros. 2 (NES) Game Resources | https://tasvideos.org/GameResources/NES/SuperMarioBros2 |
| [MW-Mario] | docs | Super Mario Wiki — Mario | https://www.mariowiki.com/Mario |
| [MW-Luigi] | docs | Super Mario Wiki — Luigi | https://www.mariowiki.com/Luigi |
| [MW-Peach] | docs | Super Mario Wiki — Princess Peach | https://www.mariowiki.com/Princess_Peach |
| [MW-Daisy] | docs | Super Mario Wiki — Princess Daisy | https://www.mariowiki.com/Princess_Daisy |
| [MW-Toad] | docs | Super Mario Wiki — Toad | https://www.mariowiki.com/Toad |
| [MW-ToadsCor] | docs | Super Mario Wiki — Yellow Toad and Blue Toad | https://www.mariowiki.com/Yellow_Toad_(character) |
| [MW-Toadette] | docs | Super Mario Wiki — Toadette | https://www.mariowiki.com/Toadette |
| [MW-Yoshi] | docs | Super Mario Wiki — Yoshi | https://www.mariowiki.com/Yoshi |
| [MW-Rosalina] | docs | Super Mario Wiki — Rosalina | https://www.mariowiki.com/Rosalina |
| [MW-Wario] | docs | Super Mario Wiki — Wario | https://www.mariowiki.com/Wario |
| [MW-Waluigi] | docs | Super Mario Wiki — Waluigi | https://www.mariowiki.com/Waluigi |
| [MW-DK] | docs | Super Mario Wiki — Donkey Kong | https://www.mariowiki.com/Donkey_Kong |
| [MW-Nabbit] | docs | Super Mario Wiki — Nabbit | https://www.mariowiki.com/Nabbit |
| [MW-Martinet] | docs | Super Mario Wiki — Charles Martinet | https://www.mariowiki.com/Charles_Martinet |
| [MW-PerfisMario] | docs | Super Mario Wiki — List of Mario profiles and statistics | https://www.mariowiki.com/List_of_Mario_profiles_and_statistics |
| [MW-PerfisLuigi] | docs | Super Mario Wiki — List of Luigi profiles and statistics | https://www.mariowiki.com/List_of_Luigi_profiles_and_statistics |
| [MW-PerfisPeach] | docs | Super Mario Wiki — List of Princess Peach profiles and statistics | https://www.mariowiki.com/List_of_Princess_Peach_profiles_and_statistics |
| [MW-PerfisDaisy] | docs | Super Mario Wiki — List of Princess Daisy profiles and statistics | https://www.mariowiki.com/List_of_Princess_Daisy_profiles_and_statistics |
| [MW-PerfisToad] | docs | Super Mario Wiki — List of Toad profiles and statistics | https://www.mariowiki.com/List_of_Toad_profiles_and_statistics |
| [MW-PerfisToadette] | docs | Super Mario Wiki — List of Toadette profiles and statistics | https://www.mariowiki.com/List_of_Toadette_profiles_and_statistics |
| [MW-PerfisYoshi] | docs | Super Mario Wiki — List of Yoshi profiles and statistics | https://www.mariowiki.com/List_of_Yoshi_profiles_and_statistics |
| [MW-PerfisRosalina] | docs | Super Mario Wiki — List of Rosalina profiles and statistics | https://www.mariowiki.com/List_of_Rosalina_profiles_and_statistics |
| [MW-PerfisWario] | docs | Super Mario Wiki — List of Wario profiles and statistics | https://www.mariowiki.com/List_of_Wario_profiles_and_statistics |
| [MW-PerfisNabbit] | docs | Super Mario Wiki — List of Nabbit profiles and statistics | https://www.mariowiki.com/List_of_Nabbit_profiles_and_statistics |
| [MW-SMB2] | docs | Super Mario Wiki — Super Mario Bros. 2 | https://www.mariowiki.com/Super_Mario_Bros._2 |
| [MW-LostLevels] | docs | Super Mario Wiki — Super Mario Bros.: The Lost Levels | https://www.mariowiki.com/Super_Mario_Bros.:_The_Lost_Levels |
| [MW-SMB3] | docs | Super Mario Wiki — Super Mario Bros. 3 | https://www.mariowiki.com/Super_Mario_Bros._3 |
| [MW-SMW] | docs | Super Mario Wiki — Super Mario World | https://www.mariowiki.com/Super_Mario_World |
| [MW-NSMBW] | docs | Super Mario Wiki — New Super Mario Bros. Wii | https://www.mariowiki.com/New_Super_Mario_Bros._Wii |
| [MW-NSMBU] | docs | Super Mario Wiki — New Super Mario Bros. U | https://www.mariowiki.com/New_Super_Mario_Bros._U |
| [MW-NSLU] | docs | Super Mario Wiki — New Super Luigi U | https://www.mariowiki.com/New_Super_Luigi_U |
| [MW-NSMBUD] | docs | Super Mario Wiki — New Super Mario Bros. U Deluxe | https://www.mariowiki.com/New_Super_Mario_Bros._U_Deluxe |
| [MW-3DW] | docs | Super Mario Wiki — Super Mario 3D World | https://www.mariowiki.com/Super_Mario_3D_World |
| [MW-Run] | docs | Super Mario Wiki — Super Mario Run | https://www.mariowiki.com/Super_Mario_Run |
| [MW-SMBW] | docs | Super Mario Wiki — Super Mario Bros. Wonder | https://www.mariowiki.com/Super_Mario_Bros._Wonder |
| [MW-SMM2] | docs | Super Mario Wiki — Super Mario Maker 2 | https://www.mariowiki.com/Super_Mario_Maker_2 |
| [MW-SmallMario] | docs | Super Mario Wiki — Small Mario | https://www.mariowiki.com/Small_Mario |
| [MW-SuperForm] | docs | Super Mario Wiki — Super Mario (form) | https://www.mariowiki.com/Super_Mario_(form) |
| [MW-Scuttle] | docs | Super Mario Wiki — Scuttle | https://www.mariowiki.com/Scuttle |
| [MW-FlutterJump] | docs | Super Mario Wiki — Flutter Jump | https://www.mariowiki.com/Flutter_Jump |
| [MW-FloatingJump] | docs | Super Mario Wiki — Floating Jump | https://www.mariowiki.com/Floating_Jump |
| [MW-PowerSquat] | docs | Super Mario Wiki — Power Squat Jump | https://www.mariowiki.com/Power_Squat_Jump |
| [MW-TimeLimit] | docs | Super Mario Wiki — Time Limit | https://www.mariowiki.com/Time_Limit |
| [MW-WL2] | docs | Super Mario Wiki — Wario Land II | https://www.mariowiki.com/Wario_Land_II |
| [MW-DKC] | docs | Super Mario Wiki — Donkey Kong Country | https://www.mariowiki.com/Donkey_Kong_Country |
| [MW-AssetsSMB] | técnico | Super Mario Wiki — Category: Super Mario Bros. assets (dimensões de arquivos) | https://www.mariowiki.com/Category:Super_Mario_Bros._assets |
| [MW-AssetsSMB3] | técnico | Super Mario Wiki — Category: Super Mario Bros. 3 assets | https://www.mariowiki.com/Category:Super_Mario_Bros._3_assets |
| [MW-AssetsSMW] | técnico | Super Mario Wiki — Category: Super Mario World assets | https://www.mariowiki.com/Category:Super_Mario_World_assets |
| [Wiki-Afghani] | docs | Wikipedia — Kevin Afghani | https://en.wikipedia.org/wiki/Kevin_Afghani |
| [Wiki-Luigi] | docs | Wikipedia — Luigi (character) | https://en.wikipedia.org/wiki/Luigi_(character) |
| [Wiki-LostLevels] | docs | Wikipedia — Super Mario Bros.: The Lost Levels | https://en.wikipedia.org/wiki/Super_Mario_Bros.:_The_Lost_Levels |
| [Wiki-Rosalina] | docs | Wikipedia — Rosalina (Mario) | https://en.wikipedia.org/wiki/Rosalina_(Mario) |
| [Wiki-Waluigi] | docs | Wikipedia — Waluigi | https://en.wikipedia.org/wiki/Waluigi |
| [SG-Rosalina] | comunitário | Source Gaming — New Content Approaching: Rosalina (entrevista Koizumi/Nintendo Power) | https://sourcegaming.info/2017/03/14/new-content-approaching-rosalina/ |
| [Siliconera-Yoshi] | entrevista | Yoshi originally crocodile-like; created from idea of Mario riding a horse | https://www.siliconera.com/yoshi-originally-crocodile-like-created-idea-mario-riding-horse/ |
| [IA-NSLU] | oficial (indisponível: 503) | Iwata Asks: New Super Luigi U | https://iwataasks.nintendo.com/interviews/wiiu/new-super-luigi-u/0/1 |
