# Referências — engenharia reversa de fases (séries 2D de *Super Mario*)

Bibliografia de [`ENGENHARIA_REVERSA_FASES_MARIO.md`](ENGENHARIA_REVERSA_FASES_MARIO.md). Todas as fontes foram consultadas em **2026-11-03**. No texto principal, as citações aparecem como [R#].

## Classes de confiabilidade

| Classe | Uso neste estudo | Peso relativo |
| --- | --- | --- |
| **oficial Nintendo** | Páginas publicadas pela Nintendo: Iwata Asks, Ask the Developer, entrevistas do Nintendo Classic Mini e páginas de produto. | Mais alto para intenção de design e números divulgados pela empresa. |
| **entrevista de desenvolvedor** | Desenvolvedores falando sobre o próprio trabalho, publicados por terceiros ou traduzidos por fãs. | Alto para intenção. A tradução pode introduzir nuances. |
| **documentação técnica comunitária** | Desmontagens, documentação de física, TASVideos, Data Crystal, NESdev e corpus de fases. | Alto para valores de código e de memória. Pode haver erro de interpretação. |
| **wiki de fãs** | Super Mario Wiki. | Médio. Útil para contagens e listas. Verificado contra fontes oficiais quando possível. |
| **análise de terceiros** | Imprensa, vídeos analíticos, artigos acadêmicos e enciclopédia colaborativa. | Médio para interpretação. Resumos de imprensa servem apenas para o que citam. |
| **fonte interna do projeto** | Código e documentação do Lume. | Fonte primária para o Lume. Não fala dos jogos estudados. |

As publicações em inglês da Nintendo UK não mostram a data da versão traduzida. Nesses casos, informamos o ano de lançamento da série. O site `iwataasks.nintendo.com` respondeu HTTP 503 durante a pesquisa, e todas as entrevistas *Iwata Asks* foram lidas no espelho oficial `nintendo.com/en-gb`, com o texto integral.

---

## A. Oficial Nintendo: entrevistas *Iwata Asks* e *Ask the Developer*

**[R1]** Nintendo (Nintendo UK). *Iwata Asks: New Super Mario Bros. Wii*, Vol. 1, §4 "Letting Everyone Know It Was A Good Mushroom", com Satoru Iwata e Shigeru Miyamoto. Ano: 2009.
URL: https://www.nintendo.com/en-gb/Iwata-Asks/Iwata-Asks-New-Super-Mario-Bros-Wii/Volume-1/4-Letting-Everyone-Know-It-Was-A-Good-Mushroom/4-Letting-Everyone-Know-It-Was-A-Good-Mushroom-210863.html
Sustenta: no início de *Super Mario Bros.* (SMB), o jogador aprende a pular sobre o primeiro Goomba e descobre o pisão ao errar. O cogumelo volta ao bater no cano e força o contato, o que ensina que ele é bom. O desenvolvimento foi feito por tentativa e erro.
Classe: oficial Nintendo / entrevista de desenvolvedor.

**[R2]** Nintendo (Nintendo UK). *Iwata Asks: NSMB Wii*, Vol. 1, §5 "Allowing Novices To See the Ending Too". Ano: 2009.
URL: https://www.nintendo.com/en-gb/Iwata-Asks/Iwata-Asks-New-Super-Mario-Bros-Wii/Volume-1/5-Allowing-Novices-To-See-the-Ending-Too/5-Allowing-Novices-To-See-the-Ending-Too-210912.html
Sustenta: a fase precisa ter o objetivo à direita e não pode ser longa demais. A repetição deve transmitir a sensação de melhora. Uma única dificuldade não agrada a todos. Apresenta o conceito do Super Guide.
Classe: oficial Nintendo / entrevista de desenvolvedor.

**[R3]** Nintendo (Nintendo UK). *Iwata Asks: NSMB Wii*, Vol. 1, §6 "A Medal for Skilled Players". Ano: 2009.
URL: https://www.nintendo.com/en-gb/Iwata-Asks/Iwata-Asks-New-Super-Mario-Bros-Wii/Volume-1/6-A-Medal-for-Skilled-Players/6-A-Medal-for-Skilled-Players-210961.html
Sustenta: o bloco de dica aparece após 8 vidas perdidas. Os valores 3, 5 e 10 foram discutidos. Há 3 Star Coins por fase. O Mundo 9 é desbloqueado por Star Coins, e há medalhas para quem não usa ajuda.
Classe: oficial Nintendo / entrevista de desenvolvedor.

**[R4]** Nintendo (Nintendo UK). *Iwata Asks: NSMB Wii*, Vol. 1, §7 "A Block Floating In Mid-Air Is Unnatural". Ano: 2009.
URL: https://www.nintendo.com/en-gb/Iwata-Asks/Iwata-Asks-New-Super-Mario-Bros-Wii/Volume-1/7-A-Block-Floating-In-Mid-Air-Is-Unnatural/7-A-Block-Floating-In-Mid-Air-Is-Unnatural-211017.html
Sustenta: regras devem parecer naturais e fáceis de entender. Há consistência entre elementos (fogo na água, inimigos congelados).
Classe: oficial Nintendo / entrevista de desenvolvedor.

**[R5]** Nintendo (Nintendo UK). *Iwata Asks: NSMB Wii*, Vol. 1, §9 "The Correct Way to Enjoy An Action Game". Ano: 2009.
URL: https://www.nintendo.com/en-gb/Iwata-Asks/Iwata-Asks-New-Super-Mario-Bros-Wii/Volume-1/9-The-Correct-Way-to-Enjoy-An-Action-Game/9-The-Correct-Way-to-Enjoy-An-Action-Game-211131.html
Sustenta: Miyamoto prefere que o jogador repita trechos fáceis a ter muitos checkpoints. Jogar sempre no limite não é prazeroso, e a tensão deve ser moderada.
Classe: oficial Nintendo / entrevista de desenvolvedor.

**[R6]** Nintendo (Nintendo UK). *Iwata Asks: NSMB Wii*, Vol. 2, §4 "Adjusting the Map in a Daily Cycle", com Iwata, Tezuka e Nakago. Ano: 2009.
URL: https://www.nintendo.com/en-gb/Iwata-Asks/Iwata-Asks-New-Super-Mario-Bros-Wii/Volume-2/4-Adjusting-the-Map-in-a-Daily-Cycle/4-Adjusting-the-Map-in-a-Daily-Cycle-233027.html
Sustenta: a meta de cerca de 1 minuto por fase em SMB. As fases tinham cerca de 12 telas, e a mais longa tinha 32. Usava-se papel quadriculado e ciclo diário de ajustes. Os mundos 3 e 5 foram criados primeiro, e os elementos fáceis foram levados ao início. O 1-1 foi feito por último, com simulação do caminho do jogador no papel.
Classe: oficial Nintendo / entrevista de desenvolvedor.

**[R7]** Nintendo (Nintendo UK). *Iwata Asks: NSMB Wii*, Vol. 2, §5 "Applying A Single Idea To Both Land And Sky". Ano: 2009.
URL: https://www.nintendo.com/en-gb/Iwata-Asks/Iwata-Asks-New-Super-Mario-Bros-Wii/Volume-2/5-Applying-A-Single-Idea-To-Both-Land-And-Sky/5-Applying-A-Single-Idea-To-Both-Land-And-Sky-233080.html
Sustenta: moedas no ar foram usadas para induzir o salto de descida. Nakago resume o princípio de não trair as expectativas do jogador. O Goomba foi criado porque o Koopa exigia dois passos para ser vencido.
Classe: oficial Nintendo / entrevista de desenvolvedor.

**[R8]** Nintendo (Nintendo UK). *Iwata Asks: NSMB Wii*, Vol. 2, §8 "Coming Up With Ideas Together". Ano: 2009.
URL: https://www.nintendo.com/en-gb/Iwata-Asks/Iwata-Asks-New-Super-Mario-Bros-Wii/Volume-2/8-Coming-Up-With-Ideas-Together/8-Coming-Up-With-Ideas-Together-233243.html
Sustenta: o vento é visto como negativo, e por isso foram adicionadas moedas carregadas pelo vento como compensação positiva.
Classe: oficial Nintendo / entrevista de desenvolvedor.

**[R9]** Nintendo (Nintendo UK). *Iwata Asks: NSMB Wii*, Vol. 2, §10 "New Things To Discover". Ano: 2009.
URL: https://www.nintendo.com/en-gb/Iwata-Asks/Iwata-Asks-New-Super-Mario-Bros-Wii/Volume-2/10-New-Things-To-Discover/10-New-Things-To-Discover-233368.html
Sustenta: o jogo ficou um pouco mais difícil que a versão de DS e foi projetado supondo que as fases seriam rejogadas.
Classe: oficial Nintendo / entrevista de desenvolvedor.

**[R10]** Nintendo (Nintendo UK). *Iwata Asks: NSMB Wii*, Vol. 3, §4 "The Peer-Evaluated Super Guide". Ano: 2009.
URL: https://www.nintendo.com/en-gb/Iwata-Asks/Iwata-Asks-New-Super-Mario-Bros-Wii/Volume-3/4-The-Peer-Evaluated-Super-Guide/4-The-Peer-Evaluated-Super-Guide-219590.html
Sustenta: jogadores abandonam o jogo em chefes difíceis. As demonstrações foram gravadas por cerca de 20 pessoas e avaliadas por pares, com jogo calmo e sem truques.
Classe: oficial Nintendo / entrevista de desenvolvedor.

**[R11]** Nintendo (Nintendo UK). *Iwata Asks: NSMB Wii*, Vol. 3, §5 "New Courses Two Weeks Before Deadline". Ano: 2009.
URL: https://www.nintendo.com/en-gb/Iwata-Asks/Iwata-Asks-New-Super-Mario-Bros-Wii/Volume-3/5-New-Courses-Two-Weeks-Before-Deadline/5-New-Courses-Two-Weeks-Before-Deadline-219635.html
Sustenta: o Mario Club fazia testes e depuração. O jogo final tem 65 vídeos de "Super Skills", e cinco cursos extras foram feitos por um projetista cada.
Classe: oficial Nintendo / entrevista de desenvolvedor.

**[R12]** Nintendo (Nintendo UK). *Iwata Asks: NSMB Wii*, Vol. 3, §7 "Finding Your Own Way To Play". Ano: 2009.
URL: https://www.nintendo.com/en-gb/Iwata-Asks/Iwata-Asks-New-Super-Mario-Bros-Wii/Volume-3/7-Finding-Your-Own-Way-To-Play/7-Finding-Your-Own-Way-To-Play-219744.html
Sustenta: todo curso normal permite ganhar uma vida no topo do mastro final, o que exige técnica variada.
Classe: oficial Nintendo / entrevista de desenvolvedor.

**[R13]** Nintendo (Nintendo UK). *Iwata Asks: Super Mario Bros. 25th Anniversary*, Vol. 3, §5 "Keep Moving Right to Reach the Goal". Ano: 2010.
URL: https://www.nintendo.com/en-gb/Iwata-Asks/Super-Mario-Bros-25th-Anniversary/Vol-3-The-Developers-1-/5-Keep-Moving-Right-to-Reach-the-Goal/5-Keep-Moving-Right-to-Reach-the-Goal-222252.html
Sustenta: mover-se para a direita é um elemento fundamental e dá alívio ao jogador. O mastro premia a altura do agarre. A sensação de distância do salto foi ajustada ao longo da série.
Classe: oficial Nintendo / entrevista de desenvolvedor.

**[R14]** Nintendo (Nintendo UK). *Iwata Asks: Super Mario Bros. 25th Anniversary*, Vol. 4, §6 "Playing and Making Super Mario Bros.". Ano: 2010.
URL: https://www.nintendo.com/en-gb/Iwata-Asks/Super-Mario-Bros-25th-Anniversary/Vol-4-The-Developers-2-/6-Playing-and-Making-Super-Mario-Bros-/6-Playing-and-Making-Super-Mario-Bros-209904.html
Sustenta: o perigo deve ser legível de imediato (o pântano venenoso ficou roxo). Inimigos que causam dano têm espinhos, e uma plataforma deve estar visível à frente de um desnível. O esforço deve ser recompensado.
Classe: oficial Nintendo / entrevista de desenvolvedor.

**[R15]** Nintendo (Nintendo UK). *Iwata Asks: Super Mario Bros. 25th Anniversary*, Vol. 5, §4 "Designing Levels Together", com Miyamoto, Tezuka e Nakago. Ano: 2010.
URL: https://www.nintendo.com/en-gb/Iwata-Asks/Super-Mario-Bros-25th-Anniversary/Vol-5-Original-Super-Mario-Developers/4-Designing-Levels-Together/4-Designing-Levels-Together-212908.html
Sustenta: só Miyamoto e Tezuka desenharam as fases de SMB. O jogo era revisado no papel porque só se via uma versão jogável por dia, e o posicionamento de inimigos foi deliberado.
Classe: oficial Nintendo / entrevista de desenvolvedor.

**[R16]** Nintendo (Nintendo UK). *Iwata Asks: New Super Luigi U*, §4 "One More Time". Ano: 2013.
URL: https://www.nintendo.com/en-gb/Iwata-Asks/Iwata-Asks-New-Super-Luigi-U/New-Super-Luigi-U/4-One-More-Time-/4-One-More-Time--786963.html
Sustenta: 82 cursos refeitos com limite de 100 contagens, regra que começou como diretriz interna. Cada contagem foi alongada, e os cursos são curtos e densos. Houve teste com avaliadores jogando como iniciantes.
Classe: oficial Nintendo / entrevista de desenvolvedor.

**[R17]** Nintendo of America. *Ask the Developer Vol. 11, Super Mario Bros. Wonder — Part 1*, com Tezuka, Mouri, Hayashida, Sato e Kondo. Data: 2023-10-17.
URL: https://www.nintendo.com/us/whatsnew/ask-the-developer-vol-11-super-mario-bros-wonder-part-1/
Sustenta: tema da transformação. Uma sessão de ideias reuniu mais de 2.000 notas adesivas, seguida de protótipos. A equipe levou ideias ao extremo antes de ajustá-las e buscou ao menos um elemento de surpresa por curso. Contraste com os 2D anteriores, baseados em variações que escalam em dificuldade.
Classe: oficial Nintendo / entrevista de desenvolvedor.

**[R18]** Nintendo of America. *Ask the Developer Vol. 11, Super Mario Bros. Wonder — Part 2*. Data: 2023-10-17.
URL: https://www.nintendo.com/us/whatsnew/ask-the-developer-vol-11-super-mario-bros-wonder-part-2/
Sustenta: a animação comunica o estado do personagem. A expressão de mordida do Goomba sinaliza o dano. O Mario Elefante nasceu de objetivos de jogabilidade, e vãos foram projetados para inimigos ficarem presos.
Classe: oficial Nintendo / entrevista de desenvolvedor.

**[R19]** Nintendo of America. *Ask the Developer Vol. 11, Super Mario Bros. Wonder — Part 3*. Data: 2023-10-17.
URL: https://www.nintendo.com/us/whatsnew/ask-the-developer-vol-11-super-mario-bros-wonder-part-3/
Sustenta: há liberdade na ordem dos cursos e dificuldade indicada para cada um. Wonder Seeds podem ser compradas, e mais de 20 insígnias foram escolhidas entre mais de 50 protótipos. Cita o testador que caía repetidamente num vão no início de um curso e o curso rítmico (salto a cada quatro tempos).
Classe: oficial Nintendo / entrevista de desenvolvedor.

**[R20]** Nintendo of America. *Ask the Developer Vol. 11, Super Mario Bros. Wonder — Part 4*. Data: 2023-10-17.
URL: https://www.nintendo.com/us/whatsnew/ask-the-developer-vol-11-super-mario-bros-wonder-part-4/
Sustenta: conexão online casual ("a casual connection"), vidas compartilhadas no cooperativo local e Yoshi e Nabbit sem dano, recomendados para iniciantes.
Classe: oficial Nintendo / entrevista de desenvolvedor.

## B. Oficial Nintendo: outras páginas

**[R21]** Nintendo (Nintendo UK). *Nintendo Classic Mini: NES — special interview Volume 3: Super Mario Bros.*, com Miyamoto, Tezuka e Kondo, entrevista de Akinori Sao. Data: 2016-11-18.
URL: https://www.nintendo.com/en-gb/News/2016/November/Nintendo-Classic-Mini-NES-special-interview-Volume-3-Super-Mario-Bros-1157085.html
Sustenta: Mario pequeno permite enxergar mais adiante. SMB3 abandonou a vista isométrica porque era preciso ver se os pés tocavam o chão, e seus cursos são cheios de elementos. Informa os tamanhos das equipes.
Classe: oficial Nintendo / entrevista de desenvolvedor.

**[R22]** Nintendo (Nintendo UK). *Nintendo Classic Mini: SNES developer interview — Volume 5: Super Mario World and Super Mario World 2: Yoshi's Island*. Data: 2017-10-11.
URL: https://www.nintendo.com/en-gb/News/2017/October/Nintendo-Classic-Mini-SNES-developer-interview-Volume-5-Super-Mario-World-and-Super-Mario-World-2-Yoshi-s-Island-1290850.html
Sustenta: Hideki Konno foi diretor de mapas de *Super Mario World* (SMW). Contexto de design do SMW e da sequência.
Classe: oficial Nintendo / entrevista de desenvolvedor.

**[R23]** Nintendo of America. Página de produto *New Super Mario Bros. U Deluxe*.
URL: https://www.nintendo.com/us/store/products/new-super-mario-bros-u-deluxe-switch/
Sustenta: 164 cursos nos dois modos principais. Nabbit e Toadette jogáveis, e personagens pensados para jogadores menos experientes ("optimized for younger and less-experienced players").
Classe: oficial Nintendo.

**[R24]** Nintendo of America. Página de produto *Super Mario Bros. Wonder*.
URL: https://www.nintendo.com/us/store/products/super-mario-bros-wonder-switch/
Sustenta: Wonder Flowers mudam a jogabilidade, há insígnias, e Nabbit e Yoshi são indicados para iniciantes.
Classe: oficial Nintendo.

## C. Entrevistas de desenvolvedor (fora dos sites da Nintendo)

**[R25]** Christian Nutt. "The Structure of Fun: Learning from *Super Mario 3D Land*'s Director", entrevista com Koichi Hayashida. Gamasutra, hoje Game Developer. Data: 2012-04-13.
URL: https://www.gamedeveloper.com/design/the-structure-of-fun-learning-from-i-super-mario-3d-land-i-s-director
Sustenta: estrutura *kishōtenketsu* (introduzir, desenvolver, reviravolta, conclusão) aplicada a fases. Um conceito central por fase. Miyamoto planeja a surpresa da terceira etapa. Assistências para jogadores com dificuldade.
Classe: entrevista de desenvolvedor. Ressalva: trata de um jogo 3D.

**[R26]** Martin Robinson (Eurogamer). "Video: Miyamoto on how Nintendo made Mario's most iconic level", com Miyamoto e Tezuka sobre o World 1-1. Data: 2015-09-07. Vídeo: https://www.youtube.com/watch?v=zRGRJRUWafY
Sustenta: fonte primária da explicação do 1-1. **Não assistido diretamente.** O conteúdo foi verificado pelos resumos [R28]–[R31].
Classe: entrevista de desenvolvedor.

**[R27]** Shmuplations (tradução). "Super Mario Bros. – 2015 Developer Interview". Original: *Sankei Shinbun*, 2015-11-30, entrevista com Takashi Tezuka.
URL: https://shmuplations.com/?p=22080
Sustenta: fases desenhadas em papel quadriculado e corrigidas em papel vegetal, com versão jogável no dia seguinte. As fases quase nunca funcionavam na primeira tentativa, e projetistas tendem a fazê-las difíceis demais. O 1-1 foi criado no fim. O objetivo era um fluxo de corrida pontuado por saltos.
Classe: entrevista de desenvolvedor (tradução de fã).

## D. Análise de terceiros: imprensa, vídeo, enciclopédia e academia

**[R28]** Chris Kerr. "How Miyamoto built *Super Mario Bros.*' legendary World 1-1". Game Developer. Data: 2015-09-08.
URL: https://www.gamedeveloper.com/design/how-miyamoto-built-i-super-mario-bros-i-legendary-world-1-1
Sustenta: resumo de [R26]. O 1-1 é um tutorial para compreensão gradual e natural ("gradually and naturally understand"), e o jogador passa a jogar com liberdade depois de entender.
Classe: análise de terceiros.

**[R29]** Matt Gerardi. "Shigeru Miyamoto explains the making of *Super Mario Bros.*' first level". The A.V. Club. Data: 2015-09-08.
URL: https://www.avclub.com/shigeru-miyamoto-explains-the-making-of-super-mario-bro-1798284041
Sustenta: resumo de [R26]. O primeiro inimigo é um Goomba, e não um Koopa. Uma duplicata segura de um obstáculo aparece antes de um salto arriscado.
Classe: análise de terceiros.

**[R30]** Philip Kendall. Artigo sobre o vídeo do World 1-1. SoraNews24. Data: 2015-09-09.
URL: https://soranews24.com/2015/09/09/super-mario-bros-creator-explains-how-and-why-he-designed-world-1-1-of-the-8-bit-classic-%E3%80%90video%E3%80%91/amp/
Sustenta: resumo de [R26]. Moedas em blocos reforçam o hábito de bater neles. Blocos acima do primeiro cogumelo levam ao contato. Um buraco vazio prepara o jogador para o seguinte.
Classe: análise de terceiros.

**[R31]** Wikipedia (colaborativa). "World 1-1".
URL: https://en.wikipedia.org/wiki/World_1-1
Sustenta: compila [R26] e Jeremy Parish (1UP.com, 2012). Quatro canos de alturas diferentes ensinam o salto variável. Há buracos com fundo e um cano atalho para veteranos, além de um bloco escondido com vida extra.
Classe: análise de terceiros (enciclopédia).

**[R32]** Wikipedia (colaborativa). "Super Mario Bros. 3".
URL: https://en.wikipedia.org/wiki/Super_Mario_Bros._3
Sustenta: cita *Nintendo Power*, "The Making of Super Mario Bros. 3" (jan./fev. 1990): os primeiros mundos têm mais moedas e vidas bônus, e os posteriores são mais complexos. **A fonte primária não foi consultada.**
Classe: análise de terceiros (enciclopédia).

**[R33]** Mark Brown. "Super Mario 3D World's 4 Step Level Design". Game Maker's Toolkit, YouTube. Data: 2015-03-16.
URL: https://www.youtube.com/watch?v=dBmIkEvEBtA
Sustenta: estrutura de quatro etapas (introdução, desenvolvimento, reviravolta, conclusão). **Não assistido.** Os subtítulos (Amara) retornaram 403, e o conteúdo foi verificado por [R34].
Classe: análise de terceiros.

**[R34]** Damien McFerran. "Video: Nintendo's Four Step Stage Design...". Nintendo Life. Data: 2015-03-17.
URL: https://www.nintendolife.com/news/2015/03/video_nintendos_four_step_stage_design_is_why_you_love_super_mario_games_so_much
Sustenta: resumo de [R33]. A introdução acontece em cenário seguro, sem perder vidas, seguida de desenvolvimento, reviravolta e conclusão.
Classe: análise de terceiros.

**[R35]** Gillian Smith, Mike Treanor, Jim Whitehead e Michael Mateas. "Rhythm-Based Level Generation for 2D Platformers". *Proceedings of FDG 2009*.
URL: https://expressiveintelligence.github.io/papers/smith-fdg-09.pdf
Sustenta: grupos rítmicos (*rhythm groups*) de 5, 10, 15 ou 20 s, com densidade baixa, média ou alta e batidas regulares, aleatórias ou em *swing*, ligados por áreas de descanso. Moedas aparecem em plataformas longas, só de deslocamento.
Classe: análise de terceiros (acadêmica).

**[R36]** Steve Dahlskog e Julian Togelius. "Patterns and Procedural Content Generation: Revisiting Mario in World 1 Level 1". *DPG '12 — First Workshop on Design Patterns in Games*, ACM. Data: 2012-06-29.
URL: http://julian.togelius.com/Dahlskog2012Patterns.pdf (registro: https://researcher.itu.dk/en/publications/patterns-and-procedural-content-generation/)
Sustenta: 23 padrões de fase de SMB em 5 grupos: inimigos, vãos, vales, caminhos múltiplos e escadas, incluindo "Risk and Reward".
Classe: análise de terceiros (acadêmica).

**[R37]** Adam Summerville, Sam Snodgrass, Michael Mateas e Santiago Ontañón. "The VGLC: The Video Game Level Corpus". arXiv:1606.07487, em *Proceedings of the 7th Workshop on PCG*. Data: 2016.
URL: https://arxiv.org/abs/1606.07487
Sustenta: origem e propósito do corpus usado nas medições próprias.
Classe: análise de terceiros (acadêmica) / documentação técnica comunitária.

## E. Documentação técnica comunitária

**[R38]** TheVGLC (repositório). Arquivos `Super Mario Bros/Processed/mario-*.txt` e a legenda `Super Mario Bros/smb.json`.
URL: https://github.com/TheVGLC/TheVGLC (lido via `raw.githubusercontent.com`)
Sustenta: 15 das 32 fases de SMB (1-1, 1-2, 1-3, 2-1, 3-1, 3-3, 4-1, 4-2, 5-1, 5-3, 6-1, 6-2, 6-3, 7-1, 8-1), só as áreas principais, sem plataformas móveis. Foram usadas apenas para estatísticas agregadas próprias, e **nenhum mapa é reproduzido**.
Classe: documentação técnica comunitária.

**[R39]** slither (silverslither). "Movement — SMBpedia". Atualizado em 2025-02-08.
URL: https://simplistic6502.github.io/smb1_tll/smbpedia_movement.html
Sustenta: velocidades máximas de SMB (±24 e ±40 subpixels/quadro). Os índices de salto dependem da velocidade horizontal (limiares 9, 16, 25 e 28). A gravidade de subida e de queda vem das tabelas, e a de queda vale quando o botão é solto ou a velocidade vertical é ≥ 0.
Classe: documentação técnica comunitária.

**[R40]** doppelganger. *SMBDIS.ASM — A Comprehensive Super Mario Bros. Disassembly* (cópia em *gist*).
URL: https://gist.github.com/1wErt3r/4048722
Sustenta: tabelas `JumpMForceData`, `FallMForceData`, `PlayerYSpdData` e `MaxRightXSpdData`. A velocidade vertical máxima do jogador é 4 px/quadro. A rolagem começa com o jogador a 80 px na tela e é total a partir de 112 px.
Classe: documentação técnica comunitária.

**[R41]** TASVideos. "Game Resources — NES Super Mario Bros.".
URL: https://tasvideos.org/GameResources/NES/SuperMarioBros
Sustenta: blocos com fronteira a cada 16 px e 16 subpixels por pixel.
Classe: documentação técnica comunitária.

**[R42]** TASVideos. "Game Resources — SNES Super Mario World".
URL: https://tasvideos.org/GameResources/SNES/SuperMarioWorld
Sustenta: subpixel de 1/16. Velocidades oscilantes de corrida (cerca de 36), disparada (cerca de 48) e voo (máximo de 51) em subpixels/quadro. O P-meter tem pico de 112.
Classe: documentação técnica comunitária.

**[R43]** Data Crystal (TCRF). "Super Mario Bros.:Notes".
URL: https://datacrystal.tcrf.net/wiki/Super_Mario_Bros.:Notes
Sustenta: corrobora a gravidade mais fraca na subida e mais forte na queda. **Página parcialmente lida**: o acesso direto foi bloqueado por desafio anti-robô, e a leitura foi indireta pela ferramenta de busca.
Classe: documentação técnica comunitária.

**[R44]** NESdev Wiki. "PPU rendering".
URL: https://www.nesdev.org/wiki/PPU_rendering
Sustenta: a imagem do NES tem 256 × 240 pixels.
Classe: documentação técnica comunitária.

## F. Wiki de fãs: Super Mario Wiki (revisão corrente em 2026-11-03)

URL base: `https://www.mariowiki.com/`. O texto bruto foi lido via `index.php?title=<página>&action=raw`.

| ID | Página | O que sustenta |
| --- | --- | --- |
| **[R45]** | `Super_Mario_Bros.` | 8 mundos × 4 fases. Tipos de fase: 13 de superfície, 7 *athletic*, 2 subterrâneas, 2 aquáticas e 8 castelos. O castelo fica sempre na fase 4, com falso Bowser nos mundos 1 a 7. Checkpoints invisíveis. Timer de 400 contagens = 160 s. O 1-3 é versão mais fácil do 5-3. Variações de mundo apenas estéticas. Transições por cano nas fases subterrâneas e aquáticas. |
| **[R46]** | `Super_Mario_Bros._3` | 8 mundos e nomes, com os nomes NTSC originais entre parênteses. Total de 88 fases. Mapa com casas de Toad, painéis Spade e cursos de inimigos. Fortaleza no meio do mundo e aeronave no fim. O manual japonês compara o mapa a um jogo de tabuleiro. |
| **[R47]** | `Super_Mario_World` | 9 mundos e 73 fases (76 por outra contagem). 24 fases com saída secreta e 96 saídas registradas (96 a 100 conforme a contagem). Quatro fases regulares por mundo mais segredos. Switch Palaces, Star World e Special Zone (mais difícil e sem Midway Gate). Paleta "Fall". Midway Gate restaura o tamanho. Mapa conectado com múltiplos caminhos. |
| **[R48]** | `New_Super_Mario_Bros.` | 8 mundos. Mundos 4 e 7 acessados como Mini Mario. Canhões do Mundo 1 ao 5 e do 5 ao 8. Placas de 5 Star Coins. Star Coins por mundo (24, 27, 27, 30, 30, 33, 33, 36). Modo Challenge sem rolagem para trás. |
| **[R49]** | `New_Super_Mario_Bros._Wii` | 9 mundos. 77 cursos no jogo principal, 14 com saída secreta, somando 91 saídas. Com o Mundo 9 são 85 fases e 99 saídas. Super Guide após 8 falhas. Mapas alternam horizontal e vertical. Star Coins por mundo. |
| **[R50]** | `New_Super_Mario_Bros._U` | Mapa contínuo e nomes das áreas. Primeiro 2D com nomes únicos para cada fase. Sem canhões de atalho, substituídos por saídas secretas. Nabbit em uma fase de cada um dos sete primeiros mundos. Star Coins por área. |
| **[R51]** | `New_Super_Luigi_U` | 82 cursos novos sobre o mesmo mapa. Início com 100 s. Cursos mais curtos e densos. |
| **[R52]** | `New_Super_Mario_Bros._U_Deluxe` | Toadette (Peachette), Nabbit, +100 s para esses personagens, menor escorregamento e um quique para fora do vão. |
| **[R53]** | `Super_Mario_Bros._Wonder` | 6 mundos numerados, Petal Isles e Special World. Tipos de curso. Dificuldade de 1 a 5 estrelas por curso. Sem timer nem pontuação. Tabela de cursos por mundo, base das contagens próprias. Edição de Switch 2 (2026) com conteúdo extra. |
| **[R54]** | `Time_Limit` | Duração da contagem e limites padrão em cada jogo (SMB 0,4 s; SMB3 0,68 s; SMW 41 quadros; NSMB 0,75 s; NSLU 1 s). No NSMB Wii, multiplayer dá +100 e o *respawn* no checkpoint tira 200. Wonder não tem timer. |
| **[R55]** | `Star_Coin` | 240 Star Coins (80 fases) no NSMB, 231 no NSMB Wii e 246 no NSMB U. Desbloqueio do Mundo 9 e da Superstar Road. |
| **[R56]** | `Wonder_Seed` | 225 sementes. Pelo menos 2 por curso padrão e 3 com saída secreta. Royal Seed no fim de cada mundo. |
| **[R57]** | `10-flower_coin` | 3 por curso e 306 no total. |
| **[R58]** | `Wonder_Flower` | Uma Wonder Flower por curso principal, cada uma levando a uma Wonder Seed. Cerca de 2.000 sugestões, segundo a Wired. |
| **[R59]** | `Secret_exit` | SMW tem 24 de 96 saídas secretas, NSMB tem 16, NSMB Wii 14 e NSMB U 12. Em Wonder, o mastro vermelho dá a terceira semente. Cita fases cuja saída normal faz um laço. |
| **[R60]** | `Warp_Zone` | 3 Warp Zones em SMB. A Warp Zone de SMB3 só é acessível com os 3 apitos. |
| **[R61]** | `Checkpoint` | Checkpoints invisíveis em SMB. SMB3 não tem checkpoint, por ter fases curtas. SMW introduziu o objeto de checkpoint. |
| **[R62]** | `Checkpoint_Flag` | Bandeira desde o NSMB. Alguns castelos e as casas fantasmas não têm bandeira. No Super Mario Maker, o curso precisa ser vencido também a partir do checkpoint para ser publicado, com um checkpoint por área. |
| **[R63]** | `Midway_Gate` | No SMW, o Midway Gate fica perto do meio de muitos cursos. Não aparece em fases com rolagem automática, aquáticas, da Star World e da Special Zone. Concede Super Mario. |
| **[R64]** | `Switch_Palace` | 4 palácios em SMW. Transformam blocos pontilhados em sólidos em todo o jogo. Três exigem saída secreta. |
| **[R65]** | `Keyhole` | Saída secreta por chave e buraco de fechadura em SMW. |
| **[R66]** | `Ghost_House` | Casas fantasmas em SMW, NSMB, NSMB Wii, NSMB U e Wonder. Na série NSMB, todas têm saída secreta e nenhuma tem checkpoint. |
| **[R67]** | `Tower` | Torres no meio do mundo, com Bowser Jr. no NSMB, Koopalings no NSMB Wii e Boom Boom no NSMB U. |
| **[R68]** | `Fortress` | Fortalezas no meio do mundo em SMB3, com Boom Boom, abrindo portas trancadas. Quatro fortalezas em SMW, só uma no meio de um mundo. |
| **[R69]** | `Castle` | Castelos no fim dos mundos em cada jogo. Em Wonder, palácios encerram 4 mundos, com Bowser Jr. e Royal Seed. |
| **[R70]** | `Airship` | Aeronave como última fase dos mundos 1 a 7 em SMB3. Aeronaves do NSMB Wii e do NSMB U. Em Wonder, "flying battleships" em 3 áreas. |
| **[R71]** | `Water_tide` | Marés de água: SMB3 3-3 e 3-8, SMW Mondo, NSMB 2-3, 6-2 e 8-2, NSMB Wii 6-3 e 6-5, e um curso de Wonder. |
| **[R72]** | `Lava_tide` | Marés de lava: NSMB 4-Tower e 8-6, NSMB Wii 8-6, e "Rising Tides of Lava" no NSMB U. |
| **[R73]** | `Dragon_Coin` | Em SMW, a maioria das fases tem pelo menos 5 Dragon Coins, e 5 dão uma vida extra. Ausentes em castelos, casas fantasmas e fortalezas. |
| **[R74]** | `Yamamura%27s_Dojo` | Transcrição das lições oficiais de criação de fases de *Super Mario Maker 2* (2019): checkpoints, direção, justiça, moedas, dificuldade, testes, paredes e segredos. |

Classe de [R45]–[R74]: **wiki de fãs**. [R74] transcreve conteúdo oficial exibido no jogo.

## G. Fonte interna do projeto

**[R75]** Repositório Lume (este repositório): `src/core/physics.ts` (gravidade 1550, impulso 590, passo de 1/120 s), `src/core/game.ts` (corrida 340, caminhada 220, aceleração 1400/1000, atrito 1500 ou 180 no gelo, corte do salto em −190 u/s, *coyote* 0,1 s, *buffer* 0,12 s, queda máxima 850 u/s, câmera com alvo `x − 310 + 0,15·vx` e `y − 250`, *respawn* com tempo ≥ 90 s), `src/data/levels.ts` (tempo-limite `260 + largura/30`), `src/core/types.ts`, `docs/FASES.md` e `tests/unit/levels.test.ts`.
Sustenta: todos os parâmetros do Lume e os valores derivados na §5.
Classe: fonte interna do projeto.

---

## Fontes tentadas e não utilizadas

| Fonte | Situação |
| --- | --- |
| `iwataasks.nintendo.com` | HTTP 503 e falha de TLS. Substituído pelo espelho oficial `nintendo.com/en-gb`. |
| `web.archive.org` | Bloqueado no ambiente de pesquisa. |
| HowLongToBeat | Domínio inacessível. Durações médias de jogo **não verificadas**. |
| Amara (legendas dos vídeos do Game Maker's Toolkit) | HTTP 403. |
| The Cutting Room Floor | Não foi necessário; nenhuma afirmação depende dele. |
| Documento de física de SMB de "jdaster64" | Original não localizado. Substituído por [R39] e [R40], que trazem os valores do código. |
