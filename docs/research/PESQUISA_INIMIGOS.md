# Pesquisa de inimigos e chefes — referência para o Lume

> Documento de pesquisa do projeto **Lume** (jogo de plataforma 2D original). Estudamos os jogos 2D oficiais de Super Mario para entender **como** inimigos, chefes e ambientes são projetados. Nada aqui autoriza copiar personagens, nomes, aparência, sprites, mapas ou músicas da Nintendo. Na seção 5, os conceitos do Lume são **originais** e só se inspiram na **função de jogo** (papel) dos inimigos estudados.

## 0. Escopo, método e convenções

**Jogos estudados:** *Super Mario Bros.* (SMB, 1985), *Super Mario Bros. 3* (SMB3), *Super Mario World* (SMW), *New Super Mario Bros.* (NSMB, DS), *New Super Mario Bros. Wii* (NSMB Wii), *New Super Mario Bros. U* / *U Deluxe* (NSMBU) e *Super Mario Bros. Wonder* (Wonder). Quando um inimigo pedido não aparece nesses jogos, isso é dito.

**Método.** (1) Entrevistas oficiais de desenvolvedores para intenção de design. (2) Desmontagens comunitárias do código de SMB, SMB3 e SMW e páginas da TASVideos para valores numéricos. (3) Super Mario Wiki para ocorrência por fase e comportamento descrito. (4) Imprensa e guias só para contexto ou para registrar divergências. Data Crystal [E16] e The Cutting Room Floor [E17] foram consultados, mas recusaram acesso automatizado (HTTP 403) em 03/11/2026. Os dados equivalentes de RAM e ROM vieram das desmontagens. As páginas oficiais *Iwata Asks* responderam HTTP 503. Os trechos usados foram conferidos em reprodução de imprensa e estão marcados assim.

**Etiquetas (aplicadas a cada linha das tabelas):**

| Etiqueta | Significado |
|---|---|
| **Fato confirmado** | Afirmação sustentada pela fonte citada. A confiabilidade depende da classe da fonte (ver Referências). |
| **Observação** | Descrição qualitativa ou leitura de design feita nesta pesquisa a partir das fontes, sem medição própria. |
| **Estimativa** | Valor aproximado, calculado a partir de dados técnicos (o cálculo é indicado) ou estimado qualitativamente, sem medição. |
| **não verificado** | Nenhuma fonte acessada confirmou o dado. Não use como requisito. |

**Unidades de velocidade.** SMB, SMB3 e SMW guardam velocidades em 1/16 de pixel por quadro ("subpixels"). O nibble alto é o pixel inteiro e o baixo é a fração [E11][E12][E13][E14]. Os jogos NTSC rodam a cerca de 60 quadros/s. Logo, 1 px/quadro ≈ 60 px/s na resolução original (256 px de largura).

**Velocidades de referência do jogador (para comparar):**

| Jogo | Caminhada máx. | Corrida máx. | Outros | Classificação |
|---|---|---|---|---|
| SMB | $18 = 1,5 px/quadro | $28 = 2,5 px/quadro | — | Fato confirmado [E11] |
| SMB3 | $18 = 1,5 | $28 = 2,5 | "P-speed" $38 = 3,5; máximo $40 = 4,0 | Fato confirmado [E13] |
| SMW | não verificado | 36 subpx = 2,25 | arrancada 48 subpx = 3,0; natação ~16 subpx = 1,0 | Fato confirmado [E15] |
| Lume (atual) | 220 px/s | 340 px/s | inimigo comum 55 + 7×mundo px/s; casco 360 px/s | Fato confirmado (código do projeto, `src/core/game.ts` e `src/core/enemies.ts`) |

---

## 1. Visão geral do elenco

| Inimigo | Estreia 2D | Jogos-alvo onde aparece | Papel principal |
|---|---|---|---|
| Goomba | SMB | todos (no SMW, só o Galoomba) | caminhante introdutório |
| Koopa Troopa / Paratroopa | SMB | todos | casco-ferramenta / trajetória aérea |
| Piranha Plant / Venus Fire Trap | SMB / SMB3 | Piranha: todos · Venus: SMB3, NSMB, Wii, U, Wonder (no SMW, só em protótipo) | timing / projétil mirado |
| Boo | SMB3 | SMB3, SMW, NSMB, Wii, U, Wonder | direção do olhar |
| Shy Guy | SMB2 (EUA) | **nenhum dos jogos-alvo** | caminhante com regra de cor |
| Hammer Bro | SMB | todos, exceto SMW (lá só o Amazing Flyin' Hammer Brother) | atirador em arco, pressão |
| Bullet Bill / Bill Blaster | SMB | todos | projétil linear / canhão |
| Bob-omb | SMB2 (EUA) | SMB3, SMW, NSMB, Wii, U, Wonder | objeto temporizado |
| Lakitu / Spiny | SMB | todos | perseguidor aéreo / "não pise" |
| Thwomp | SMB3 | SMB3, SMW, NSMB, Wii, U, Wonder | armadilha com antecipação |
| Dry Bones | SMB3 | SMB3, SMW, NSMB, Wii, U, Wonder | derrota temporária |
| Cheep Cheep | SMB | todos | peixe hostil |
| Buzzy Beetle | SMB | todos | casco imune a fogo |
| Chain Chomp | SMB3 | SMB3, NSMB, Wii, U | área de risco delimitada |
| Pokey | SMB2 (EUA) | SMW, NSMB, Wii, U, Wonder | coluna espinhosa de segmentos |
| Blooper | SMB | SMB, SMB3, NSMB, Wii, U | perseguidor em zigue-zague |
| Podoboo / Lava Bubble | SMB | todos | perigo saltando da lava |
| Fire Bar / Roto-Disc | SMB / SMB3 | Fire Bar: SMB, NSMB, Wii, U, Wonder · Roto-Disc: SMB3 | obstáculo rotativo |
| Monty Mole | SMW | SMW, NSMB (chefe), Wii, U | emboscada do solo |
| Wiggler | SMW | SMW, NSMB, Wii, U, Wonder (corrida) | inimigo que enfurece |
| Rex | SMW | SMW | caminhante de dois pisões |
| Chargin' Chuck | SMW | SMW | guardião resistente |
| Fuzzy | SMW | SMW, Wii, U | obstáculo em trilho |
| Urchin | SMW | SMW, Wii, U, Wonder | espinho aquático |
| Porcupuffer | SMW | SMW, Wii, U | perseguidor de superfície |
| Cooligan | NSMB Wii | Wii, U | deslizante |
| Bramball | NSMB Wii | Wii, U | andarilho de pernas espinhosas |
| Spike | SMB3 | SMB3, NSMB (Snow Spike), Wii, U, Wonder | arremessador |
| Swoop | SMW | SMW, NSMB, Wii, U | mergulho do teto |
| Magikoopa | SMW | SMW (inimigo); Wii e U (chefe) | conjurador que teleporta |
| Hoppycat, Bulrush, Maw-Maw, Condart | Wonder | Wonder | ver 2.33–2.36 |

Fontes da tabela: páginas de cada inimigo na Super Mario Wiki [E18]–[E56]. Classificação: **Fato confirmado** (wiki de fãs).

---

## 2. Catálogo detalhado

Cada ficha usa as mesmas linhas: habitat · movimento · ataque · velocidade · reação ao jogador · reação a obstáculos · colisão · resistência · como derrotar · animação e expressões · sons · interação com o ambiente.

### 2.1 Goomba

| Aspecto | Descrição | Classificação |
|---|---|---|
| Habitat | SMB: inimigo mais comum, em quase todas as fases de superfície e de subsolo, começando em 1-1. SMB3: todos os mundos exceto Dark Land. SMW: substituído pelo Galoomba. NSMB, Wii, U e Wonder: mundos iniciais e muitos outros. | Fato confirmado [E18] |
| Movimento | Caminha em linha reta. No SMB, o passo é animado espelhando um único sprite, por falta de memória. | Fato confirmado [E18] |
| Ataque | Só contato. Segundo Miyamoto, o contato representaria uma mordida. No Wonder, faz pose de mordida ao causar dano. | Fato confirmado [E18][E5] |
| Velocidade | SMB e SMB3: 0,5 px/quadro (≈30 px/s; ⅓ da caminhada de Mario). Na 2ª volta do SMB: 0,75 px/quadro. | Fato confirmado [E11][E13] |
| Reação ao jogador | Não persegue. No Wonder, olha para o jogador e entra em pânico diante de bolas de fogo, cascos e predadores. | Fato confirmado [E18] |
| Obstáculos | Cai de beiradas (padrão "verde"). Vira ao bater em paredes. | Fato confirmado [E28] / Observação (paredes) |
| Colisão | Pisável. Vulnerável a fogo, casco, batida no bloco de baixo e Estrela. | Fato confirmado [E18] |
| Resistência | 1 golpe. Galoomba (SMW): o pisão só o vira, e ele pode ser carregado. | Fato confirmado [E18] |
| Como derrotar | Pisão (achata) ou golpe indireto (vira de cabeça para baixo). No SMB, é o único com dois sprites de derrota. | Fato confirmado [E18] |
| Animação / expressões | SMB: sem boca. SMB3 em diante: com boca. Wonder: dorme, cumprimenta outros Goombas e faz cara de "farto" quando preso num vão. | Fato confirmado [E18][E5] |
| Sons | Usa o efeito genérico de pisão (`Sfx_EnemyStomp` no SMB). Em NSMBU, pula nos "riffs" vocais da trilha. | Fato confirmado [E11][E18] |
| Ambiente | SMB troca a paleta por tipo de fase para manter contraste: azul no subsolo, cinza no castelo. Na 2ª volta do SMB, todo Goomba vira Buzzy Beetle. | Fato confirmado [E18][E11] |

### 2.2 Koopa Troopa

| Aspecto | Descrição | Classificação |
|---|---|---|
| Habitat | SMB: superfície, inclusive as escadas do fim de 3-1, e castelos (com paleta escura). SMB3: maioria dos mundos. SMW: cores verde, vermelha, azul e amarela. NSMB a Wonder: geral. No Wonder, há ainda o Rolla Koopa, de patins. | Fato confirmado [E19] |
| Movimento | O verde anda até a parede. O vermelho patrulha sem cair de beiradas. | Fato confirmado [E19] |
| Ataque | Contato. No Wonder, vira para morder o jogador pelas costas, uma brincadeira com uma história do SMB original. | Fato confirmado [E5] |
| Velocidade | SMB: 0,5 px/quadro (0,75 na 2ª volta; o *Lost Levels* é mais rápido, sem valor confirmado). SMB3: 0,5. SMW: verde e vermelho 0,5; azul e amarelo 0,75. | Fato confirmado [E11][E13][E12][E19] |
| Reação ao jogador | Verde e vermelho ignoram o jogador. O amarelo do SMW persegue e se vira cerca de 1 s depois de ficar de costas. No Wonder, fica com cara de raiva quando o jogador se aproxima. | Fato confirmado [E19] |
| Obstáculos | A cor indica a regra de beirada: o verde cai, o vermelho vira. Um casco chutado ricocheteia em paredes. | Fato confirmado [E19][E34] |
| Colisão | O pisão faz o Koopa se recolher no casco, que pode ser chutado. O casco em movimento fere o jogador. No SMB3, o casco pode ser carregado. | Fato confirmado [E19] |
| Resistência | 1 pisão, mas o casco continua em jogo. Deixado parado, o Koopa sai de novo. No SMW, o pisão o tira do casco, e ele corre para recuperá-lo. | Fato confirmado [E19] |
| Como derrotar | Pisão + chute, fogo, Estrela. O golpe por baixo vira o casco, que se desvira com o tempo. | Fato confirmado [E19] |
| Animação / expressões | No SMB, mexe as pernas antes de sair do casco (aviso). No SMW, o Koopa azul sem casco desliza de pé e chuta cascos alheios. | Fato confirmado [E19] |
| Sons | O chute usa `Sfx_EnemySmack` (SMB). Em NSMB e Wii, dança nos vocais "bah" da música. | Fato confirmado [E11][E19] |
| Ambiente | No SMB, o casco chutado vai a 3,0 px/quadro, mais rápido que a corrida máxima de Mario (2,5). Na escada de 3-1, o ricochete repetido dá vidas infinitas. É imune a veneno em NSMB e Wii. | Fato confirmado [E11][E19][E83] |

### 2.3 Koopa Paratroopa

| Aspecto | Descrição | Classificação |
|---|---|---|
| Habitat | SMB: vermelho vertical a partir de 1-3, verde a partir de 2-1. SMB3: desde 1-1. SMW: Yoshi's Island 3. NSMB e Wii: 1-4. NSMBU: Stone-Eye Zone. Wonder: vermelho e verde. | Fato confirmado [E20] |
| Movimento | O verde quica na horizontal ou voa reto. O vermelho voa em trajetória fixa (vertical ou horizontal). O amarelo do SMW anda e salta. | Fato confirmado [E20] |
| Ataque | Contato. | Observação |
| Velocidade | Sem valor técnico consultado. Estimativa: deslocamento lento, da ordem do Koopa terrestre. | Estimativa (qualitativa, não medida) |
| Reação ao jogador | Segue a própria trajetória. No NSMB, alguns quicam em direção ao jogador. | Fato confirmado [E20] |
| Obstáculos | Voadores ignoram beiradas. | Observação |
| Colisão | O pisão remove as asas (vira Koopa comum). No NSMB Wii, o Yoshi também remove as asas. | Fato confirmado [E20] |
| Resistência | 2 golpes de pisão até virar casco: asas, depois casco. | Observação |
| Como derrotar | Pisões. No NSMB Wii, o *Ground Pound* derrota de uma vez. | Fato confirmado [E20] |
| Animação / expressões | Asas batendo. Responde à música a partir do NSMB Wii. | Fato confirmado [E20] |
| Sons | não verificado. | — |
| Ambiente | No SMB3, a asa vira item: a P-Wing enche o medidor de corrida por uma fase. | Fato confirmado [E20] |

### 2.4 Piranha Plant e Venus Fire Trap

| Aspecto | Descrição | Classificação |
|---|---|---|
| Habitat | Piranha: SMB a partir de 1-2, programada para quase todo cano vertical, exceto em 1-1. SMB3: verde e vermelha; Pipe Land tem fases especiais de Piranhas. SMW: a versão normal só em Vanilla Dome 3 (canos invertidos); a Jumping Piranha é a comum. NSMB a Wonder: canos, chão, esteiras e muitas variantes. Venus: SMB3, na maioria dos mundos; NSMB (2-6, 3-B, 6-3); NSMB Wii a partir de 1-3; NSMBU; Wonder. | Fato confirmado [E21][E22] |
| Movimento | Sobe e desce do cano em ciclo. No SMB, a rotina só roda a cada dois quadros. | Fato confirmado [E21][E11] |
| Ataque | Piranha: mordida por contato. Venus: sobe, cospe uma bola de fogo na direção do jogador e desce. Depois de Grass Land, costuma cuspir duas vezes. No Wonder, cospe várias de uma vez. | Fato confirmado [E21][E22] |
| Velocidade | Ciclo vertical. Sem valor em px/quadro consultado. | não verificado |
| Reação ao jogador | SMB: não emerge se o jogador estiver a menos de 33 px ($21) na horizontal ou sobre o cano. SMW: recua quando o jogador está perto. Venus: mira na posição do jogador. | Fato confirmado [E11][E21][E22] |
| Obstáculos | Fixa no cano. Algumas variantes andam (Trottin' Piranha, no Wonder). | Fato confirmado [E21] |
| Colisão | Não pisável (fere quem pisa). Vulnerável a fogo e Estrela. No SMB3, também a casco, martelo e cauda. A Venus só cai com power-ups. | Fato confirmado [E21][E22] |
| Resistência | 1 projétil. | Fato confirmado [E21] |
| Como derrotar | Fogo, Estrela e casco. No NSMB Wii, congela, mas a Piranha congelada não pode ser carregada. | Fato confirmado [E21] |
| Animação / expressões | A boca abre e fecha. No SMB, some ao ser derrotada, sem virar como os outros. A Venus do NSMBU olha para cima quando não está cuspindo. | Fato confirmado [E21][E22] |
| Sons | No NSMB, ganha som de mastigar, removido no NSMB Wii (para as de cano). | Fato confirmado [E21] |
| Ambiente | No SMB, o limite de objetos na tela pode impedir o spawn. No NSMB Wii, o fogo da Venus ilumina cavernas escuras e revela canos secretos, e o Yoshi engole esse fogo. No NSMBU, o fogo derrete moedas congeladas. | Fato confirmado [E21][E22] |

### 2.5 Boo

| Aspecto | Descrição | Classificação |
|---|---|---|
| Habitat | SMB3: fortalezas a partir de World 2-Fortress, mas não só nelas. SMW: só nas Ghost Houses e no Sunken Ghost Ship. NSMB: Ghost Houses e 8-1. NSMB Wii: só Ghost Houses. NSMBU: inclui um *Enemy Course* em Soda Jungle. Wonder: Light-Switch Mansion (Fungi Mines). | Fato confirmado [E23] |
| Movimento | Flutua e persegue o jogador. | Fato confirmado [E23] |
| Ataque | Contato, em geral pelas costas do jogador. | Observação |
| Velocidade | No SMW, é mais lento que no SMB3, e esse padrão se manteve. Sem valor em px/quadro. | Fato confirmado [E23] / não verificado (valor) |
| Reação ao jogador | Cobre o rosto e para quando o jogador olha para ele. Persegue quando o jogador está de costas. | Fato confirmado [E23] |
| Obstáculos | Ignora o terreno e atravessa o cenário. | Observação |
| Colisão | Não pisável. SMB3: só Hammer Suit, Estrela ou casco. SMW: só Estrela. NSMB: casco, Estrela, Mega e Blue Shell. Wonder: derrotado por raios de luz. | Fato confirmado [E23] |
| Resistência | Imune à maioria dos ataques. | Fato confirmado [E23] |
| Como derrotar | Ver colisão. O SMW tem ainda o chefe Big Boo, derrotado com Grab Blocks arremessados. | Fato confirmado [E23][E65] |
| Animação / expressões | Cobre o rosto. No SMW, troca de cara rapidamente se observado por muito tempo, e grupos mostram expressões variadas. NSMB Wii: brilho azul. Wonder: língua para fora. | Fato confirmado [E23] |
| Sons | No NSMB Wii, o Boo do mapa ri quando o jogador entra na Ghost House ou perde uma vida nela. | Fato confirmado [E23] |
| Ambiente | Mora em casas assombradas de quebra-cabeça [E84]. No Wonder, a luz é a arma. A ideia da timidez agressiva vem da esposa de Tezuka. | Fato confirmado [E23]; origem: relato de terceiros [E80][E81], não verificado diretamente |

### 2.6 Shy Guy (fora dos jogos-alvo)

| Aspecto | Descrição | Classificação |
|---|---|---|
| Habitat | **Não aparece** em SMB, SMB3, SMW, NSMB, Wii, U nem Wonder. Na série 2D principal, sua aparição é *Super Mario Bros. 2* (EUA), onde é o inimigo mais comum. Também sai de jarros e monta Autobombs e Ostros. | Fato confirmado [E24] |
| Movimento | Caminha. O vermelho cai de beiradas; o rosa (azul nos remakes) não cai. É a mesma linguagem de cor do Koopa. | Fato confirmado [E24] |
| Ataque | Contato. | Fato confirmado [E24] |
| Velocidade | não verificado. | — |
| Reação ao jogador | Não persegue. | Observação |
| Obstáculos | Ver movimento (regra por cor). | Fato confirmado [E24] |
| Colisão | No SMB2, o jogador pode ficar em cima e erguê-lo. É derrotado por objetos arremessados ou ao ser lançado contra outro inimigo. | Fato confirmado [E24] / Observação (ficar em cima) |
| Resistência | 1 impacto. | Fato confirmado [E24] |
| Como derrotar | Arremessar objetos ou o próprio Shy Guy. | Fato confirmado [E24] |
| Animação / expressões | Máscara fixa e passos curtos. | Observação |
| Sons | não verificado. | — |
| Ambiente | Também serve de plataforma e de munição (o jogador o carrega). | Fato confirmado [E24] |

### 2.7 Hammer Bro

| Aspecto | Descrição | Classificação |
|---|---|---|
| Habitat | SMB: em geral em pares. SMB3: encontros no mapa e em fases. SMW: substituído pelo Amazing Flyin' Hammer Brother. NSMB: 2-4 e no mapa a partir do Mundo 5. NSMB Wii: só 4 indivíduos, em 1-3. NSMBU: Rise of the Piranha Plants (Acorn Plains). Wonder: palácios de Pipe-Rock Plateau e Fluff-Puff Peaks, mais arenas. | Fato confirmado [E25][E73] |
| Movimento | Pula entre o chão e uma ou duas fileiras de tijolos. No SMB, oscila ±0,25 px/quadro, trocando de sentido a cada 64 quadros. | Fato confirmado [E25][E11] |
| Ataque | Arremessa martelos em arco. No SMB, o temporizador de arremesso é de 48 quadros (≈0,8 s) e cai para 28 quadros (≈0,47 s) a partir de 5-3. | Fato confirmado [E11] (valores) / Estimativa (conversão em s) |
| Velocidade | Ao avançar, 0,5 px/quadro ($F8). | Fato confirmado [E11] |
| Reação ao jogador | No SMB, passa a andar em direção ao jogador quando um temporizador expira. O código usa 128 intervalos de 21 quadros (≈45 s), ou 80 a partir de 5-3 (≈28 s). A wiki cita "100 unidades de tempo (~50 s)". **Divergência registrada.** | Fato confirmado [E11] / Estimativa (s) / [E25] |
| Obstáculos | Usa as fileiras de blocos como andares. A batida no bloco de baixo o derruba. | Fato confirmado [E25] |
| Colisão | Pisável. Vulnerável a fogo, casco, batida por baixo e Estrela. | Fato confirmado [E25] |
| Resistência | 1 golpe (vale 1000 pontos no SMB). | Fato confirmado [E25] |
| Como derrotar | Ver colisão. No NSMB Wii, o Yoshi pega o martelo com a língua e o devolve. | Fato confirmado [E25] |
| Animação / expressões | Braço erguido antes de soltar o martelo. | Observação |
| Sons | não verificado. | — |
| Ambiente | Tem variantes por projétil: Boomerang, Fire, Sledge e Ice Bros. Ao aterrissar, o Sledge provoca um pequeno tremor que paralisa o jogador no chão. | Fato confirmado [E25][E87] |

### 2.8 Bullet Bill e Bill Blaster

| Aspecto | Descrição | Classificação |
|---|---|---|
| Habitat | SMB: canhões a partir de 5-1 (também 5-2, 7-1, 8-2 e 8-3) e balas vindas de fora da tela. SMB3: dirigíveis, tanques e barcos (desde World 1-Airship). SMW: Vanilla Dome 4, Sunken Ghost Ship, área do Cheese Bridge (diagonais) e Outrageous. NSMB Wii: Mundos 3, 6 e 7. Wonder: dirigíveis e Castle Bowser. | Fato confirmado [E26][E27] |
| Movimento | Linha reta. O SMW acrescenta disparos diagonais e verticais. | Fato confirmado [E26] |
| Ataque | Projétil de contato. Missile Bill faz a volta; Banzai e King Bill são gigantes. | Fato confirmado [E26] |
| Velocidade | SMB: 1,5 px/quadro, igual à caminhada máxima de Mario. SMW: 2,0 px/quadro na horizontal e 1,5 por eixo na diagonal. | Fato confirmado [E11][E12] |
| Reação ao jogador | O lado do jogador define a direção do disparo. No SMB, o canhão não dispara com o jogador a menos de ~40 px na horizontal. | Fato confirmado [E11][E27] |
| Obstáculos | Segue reto. Sai da tela e é removido. | Observação / Fato confirmado [E11] (remoção) |
| Colisão | Pisável, imune a fogo (SMB). O canhão é invulnerável, exceto pelo Mega no NSMB. | Fato confirmado [E26][E27] |
| Resistência | 1 pisão. | Fato confirmado [E26] |
| Como derrotar | Pisão ou Estrela. No SMB, o casco só derruba balas vindas de fora da tela. No NSMB Wii, a bala congelada pode ser arremessada. | Fato confirmado [E26] |
| Animação / expressões | No NSMB Wii, o canhão "estica" ao disparar (aviso). Rastro de fumaça branca no Wii e chama vermelha no NSMBU. | Fato confirmado [E27][E26] |
| Sons | No SMB, o disparo toca o efeito de "tiro/fogos" (`Sfx_Blast`). | Fato confirmado [E11] |
| Ambiente | A partir de 5-3, a probabilidade de disparo muda (máscara do gerador pseudoaleatório). No Wonder, o canhão sofre gravidade, e variantes coloridas disparam outros projéteis. | Fato confirmado [E11][E74][E27] |

### 2.9 Bob-omb

| Aspecto | Descrição | Classificação |
|---|---|---|
| Habitat | Fora do SMB original (estreou no SMB2 dos EUA). SMB3: com chave de corda; sem chave nas fases de artilharia de Dark Land. SMW: comum. NSMB: 4-5, 7-5 e chefe Monty Tank. NSMB Wii: sai de canos. NSMBU: arremessado por Bowser Jr. Wonder: só no dirigível de Fluff-Puff Peaks. | Fato confirmado [E28] |
| Movimento | Caminha. No SMW, anda rápido e cai de beiradas. | Fato confirmado [E28] |
| Ataque | Explosão depois de acionado. | Fato confirmado [E28] |
| Velocidade | SMW: 0,75 px/quadro, o grupo "rápido" da tabela de velocidades. | Fato confirmado [E12] |
| Reação ao jogador | No SMW, pisca e explode sozinho depois de andar um tempo. | Fato confirmado [E28] |
| Obstáculos | Cai de beiradas (SMW). | Fato confirmado [E28] |
| Colisão | O pisão o aciona e imobiliza. Pode ser carregado e arremessado (SMB3 em diante). | Fato confirmado [E28] |
| Resistência | 1 acionamento. | Fato confirmado [E28] |
| Como derrotar | Deixar explodir longe ou usá-lo como bomba. No NSMB Wii, fogo acende o pavio, e ele explode ao tocar lava ou chama. | Fato confirmado [E28] |
| Animação / expressões | Pisca antes de explodir (aviso). No Wonder, anda de forma mecânica, com a chave girando em passos de 90°. | Fato confirmado [E28] |
| Sons | não verificado. | — |
| Ambiente | No NSMB, a explosão destrói quase todos os blocos e abre caminho para Star Coins. No Wonder, o Baboom solta três fogos de artifício. | Fato confirmado [E28] |

### 2.10 Lakitu

| Aspecto | Descrição | Classificação |
|---|---|---|
| Habitat | SMB: desde 4-1, um de cada vez. SMB3: comum em Sky Land (primeiro em 3-4). SMW: comum. NSMB: 2-2 e 6-A. NSMB Wii: 2-5, 4-5 e *Enemy Courses* do Mundo 7. NSMBU: Blooming Lakitus (Layer-Cake Desert) e Seesaw Shrooms (Meringue Clouds). Wonder: Countdown to Drop Down. | Fato confirmado [E29][E73] |
| Movimento | Cruza o topo da tela numa nuvem. No SMW, segue diretamente o jogador. | Fato confirmado [E29] |
| Ataque | Arremessa ovos de Spiny. No SMB3, o Lakitu de ovos verdes (que rolam) lança com metade da frequência e mais devagar. | Fato confirmado [E29] |
| Velocidade | Sem valor técnico consultado. | não verificado |
| Reação ao jogador | No SMB, esconde-se na nuvem por ~1 s antes de lançar e sai da tela antes do mastro. No SMB3, para de lançar com ~4 projéteis ativos, mas continua o gesto. | Fato confirmado [E29] |
| Obstáculos | Ignora o terreno. | Observação |
| Colisão | Pisável e vulnerável a fogo. No SMW, se derrotado por projétil, deixa a nuvem utilizável. | Fato confirmado [E29] |
| Resistência | 1 golpe, mas volta alguns segundos depois (SMB). | Fato confirmado [E29] |
| Como derrotar | Pisão ou fogo. | Fato confirmado [E29] |
| Animação / expressões | Esconde-se na nuvem antes do arremesso (aviso). | Fato confirmado [E29] |
| Sons | não verificado. | — |
| Ambiente | Fases com Lakitu costumam ter retas longas e poucos abrigos. No NSMB Wii, há nuvens que lançam moedas. | Fato confirmado [E30][E29] |

### 2.11 Spiny

| Aspecto | Descrição | Classificação |
|---|---|---|
| Habitat | SMB: só via Lakitu, desde 4-1. SMB3: também independente a partir de 4-3, inclusive no teto. SMW: independente e via Lakitu. NSMB e Wonder: também caem do teto. | Fato confirmado [E30] |
| Movimento | Caminha. No SMB3, o do teto cai quando o jogador se aproxima e desliza. | Fato confirmado [E30] |
| Ataque | Contato espinhoso. | Fato confirmado [E30] |
| Velocidade | SMW: 0,5 px/quadro. | Fato confirmado [E12] |
| Reação ao jogador | Ignora o jogador. O do teto reage à aproximação. | Fato confirmado [E30] |
| Obstáculos | No NSMB (DS), pula e muda de direção no "bah" da música. | Fato confirmado [E30] |
| Colisão | Espinhoso: o pisão fere. No NSMB, o Spiny de cabeça para baixo pode ser pisado e carregado. | Fato confirmado [E30] |
| Resistência | Imune a pisão. | Fato confirmado [E30] |
| Como derrotar | Fogo, Estrela, martelo e casco. No SMB, a batida por baixo só o empurra para o lado. No Wonder, a forma Drill. | Fato confirmado [E30] |
| Animação / expressões | O ovo eclode ao tocar o chão. | Fato confirmado [E30] |
| Sons | não verificado. | — |
| Ambiente | No NSMB, vira ovo e boia na água. No NSMB Wii, congela e fica congelado até se soltar. | Fato confirmado [E30] |

### 2.12 Thwomp

| Aspecto | Descrição | Classificação |
|---|---|---|
| Habitat | SMB3: fortalezas desde World 2-Fortress. SMW: fortalezas e castelos. NSMB: castelos dos Mundos 4, 7 e 8. NSMB Wii: regularmente só no castelo do Mundo 1, além da luta com o Kamek na torre do Mundo 8. NSMBU: Wendy's Shifting Castle. Wonder: Sunbaked Desert Palace, entre outras. | Fato confirmado [E31] |
| Movimento | Espera no alto, cai quando o jogador passa embaixo e sobe devagar. No SMB3, também ataca pelos lados, e em 8-Fortress há Thwomps diagonais. | Fato confirmado [E31] |
| Ataque | Esmagamento. | Fato confirmado [E31] |
| Velocidade | SMW: acelera +4/16 px por quadro até 3,875 px/quadro. Fica 64 quadros (≈1,07 s) no chão e sobe a 1 px/quadro. | Fato confirmado [E12] / Estimativa (s) |
| Reação ao jogador | SMW: "espia" com o jogador a menos de 64 px e cai com ele entre ≈36 px à esquerda e ≈44 px à direita. A expressão muda de "espiando" para "furioso". | Fato confirmado [E12][E31] |
| Obstáculos | Não se aplica: trajetória fixa. | Observação |
| Colisão | Invulnerável na prática. SMB3: só invencibilidade, martelo ou Estátua. SMW: aceita *spin jump* em cima. NSMB Wii: só Estrela ou *Ground Pound* simultâneo. | Fato confirmado [E31] |
| Resistência | Muito alta. | Fato confirmado [E31] |
| Como derrotar | Ver colisão. | Fato confirmado [E31] |
| Animação / expressões | Face que espia e enfurece (SMW). A tela treme por 24 quadros na queda. | Fato confirmado [E31][E12] |
| Sons | No SMW, toca o efeito "KAPOW" ao bater no chão. | Fato confirmado [E12] |
| Ambiente | O Big Thwomp do NSMB quebra blocos. No NSMB Wii, o Kamek cria Thwomps que atravessam plataformas. No Wonder, o Konk também se move na horizontal (o azul ataca de baixo para cima), e o Shoomp desliza em plataformas que inclinam. | Fato confirmado [E31][E57] |

### 2.13 Dry Bones

| Aspecto | Descrição | Classificação |
|---|---|---|
| Habitat | SMB3: desde World 1-Fortress, sobretudo em fortalezas. SMW: só em fortalezas e castelos. NSMB: torres e castelos. NSMB Wii: 14 fases. NSMBU: 11. Wonder: palácios. | Fato confirmado [E32] |
| Movimento | Caminha. No SMW, vira em beiradas como o Koopa vermelho, e alguns arremessam ossos. | Fato confirmado [E32] |
| Ataque | Contato e, no SMW, ossos arremessados. | Fato confirmado [E32] |
| Velocidade | SMB3: surge andando em direção ao jogador a 0,5 px/quadro. | Fato confirmado [E13] |
| Reação ao jogador | SMB3: entra virado para o jogador. | Fato confirmado [E13] |
| Obstáculos | Vira em beiradas (SMW). | Fato confirmado [E32] |
| Colisão | O pisão o desmonta. No SMB3, é imune a fogo e cauda. | Fato confirmado [E32] |
| Resistência | A derrota é temporária: ele se reconstitui. | Fato confirmado [E32] |
| Como derrotar | Para eliminar de vez: Estrela e Hammer Suit (SMB3); capa (SMW); Estrela, POW, casco e Ice Ball (NSMB Wii); tromba do Elefante (Wonder). | Fato confirmado [E32] |
| Animação / expressões | Vira uma pilha de ossos. No NSMB, a cabeça se solta. No NSMBU, brilha em vermelho enquanto se reconstitui (aviso) e gira a cabeça com os vocais da música. | Fato confirmado [E32] |
| Sons | No SMB3, usa o mesmo som da quebra de tijolo. Os jogos seguintes dão um som próprio. | Fato confirmado [E32] |
| Ambiente | No NSMB, a cabeça que cai na lava ou num abismo demora mais a voltar. No NSMBU, ele não é mais afetado pela lava. | Fato confirmado [E32] |

### 2.14 Cheep Cheep

| Aspecto | Descrição | Classificação |
|---|---|---|
| Habitat | SMB: todas as fases aquáticas (desde 2-2), mais Cheep Cheeps voadores em fases de superfície. SMB3: comum em Water Land; o verde fica na água e o vermelho salta. SMW: água, bolhas em Forest of Illusion e debatendo-se em terra (Vanilla Dome 3, Mondo). NSMB a Wonder: água. | Fato confirmado [E33][E85][E11] |
| Movimento | No SMB, nada reto ou em onda. No SMB3, o verde vai e volta devagar, e o vermelho salta da água para atingir o jogador. | Fato confirmado [E33] |
| Ataque | Contato. | Fato confirmado [E33] |
| Velocidade | No SMB, o vermelho é "moderadamente rápido" e o cinza é mais lento. Sem valor numérico consultado. | Fato confirmado [E33] / não verificado (valor) |
| Reação ao jogador | No SMB, nada em direção ao jogador. No NSMB, os Deep-Cheeps perseguem ao notar o jogador. | Fato confirmado [E33] |
| Obstáculos | No NSMB Wii, colidem entre si e se empurram. | Fato confirmado [E33] |
| Colisão | SMB: não dá para pisar debaixo d'água. Wonder: dá para pisar debaixo d'água. SMW: em terra, morre ao toque. | Fato confirmado [E68][E33] |
| Resistência | 1 golpe. | Fato confirmado [E33] |
| Como derrotar | Fogo, capa e Yoshi (SMW); Estrela. | Fato confirmado [E33] |
| Animação / expressões | Debate-se fora d'água (SMW). | Fato confirmado [E33] |
| Sons | não verificado. | — |
| Ambiente | Em Mondo (SMW), a maré sobe e desce, e os Cheep Cheeps nadam ou se debatem conforme o nível da água. No SMB, a partir de 5-3, até 4 Cheep Cheeps voadores ficam ao mesmo tempo na tela (antes, 3). | Fato confirmado [E85][E11] |

### 2.15 Buzzy Beetle

| Aspecto | Descrição | Classificação |
|---|---|---|
| Habitat | SMB: desde 4-2 (tecnicamente desde 3-4, cujo falso Bowser é um Buzzy disfarçado). Na 2ª volta, substitui todos os Goombas. SMB3, SMW e NSMB: presente. NSMB Wii: teto de 6-3 e beira de lava em 8-1 (16 unidades). NSMBU e Wonder: presente. | Fato confirmado [E34][E11][E77] |
| Movimento | Caminha e cai de beiradas como o Koopa verde (SMB). No SMB3, o do teto se solta e gira pelo chão. | Fato confirmado [E34] |
| Ataque | Contato. | Fato confirmado [E34] |
| Velocidade | SMW: 0,5 px/quadro. No SMB, provavelmente usa a mesma inicialização dos "inimigos normais" (0,5), mas isso não foi conferido no código. | Fato confirmado [E12] / Estimativa (SMB) |
| Reação ao jogador | Ignora o jogador. O do teto cai quando o jogador se aproxima. | Fato confirmado [E34] |
| Obstáculos | No NSMB Wii 8-1, vira ao chegar à lava. | Fato confirmado [E34] |
| Colisão | Pisável. Vira casco chutável que ricocheteia em paredes. **Imune a fogo.** | Fato confirmado [E34] |
| Resistência | 1 pisão. O casco permanece. | Fato confirmado [E34] |
| Como derrotar | Casco, Estrela e pisão + chute. No SMW, o Yoshi engole. | Fato confirmado [E34] |
| Animação / expressões | No SMB, sai do casco **sem aviso**. O SMB3 acrescenta um tremor antes de sair, uma melhoria de legibilidade. | Fato confirmado [E34] |
| Sons | Pula no "paah" da música (NSMB e Wii). | Fato confirmado [E34] |
| Ambiente | No Wonder, nada na lava. Variantes: Spike Top (espinho em cima), Bony Beetle (esqueleto) e Para-Beetle (voa e serve de plataforma). | Fato confirmado [E34] |

### 2.16 Chain Chomp

| Aspecto | Descrição | Classificação |
|---|---|---|
| Habitat | SMB3: desde 2-5. NSMB: só em 6-6 (três). NSMB Wii: 7-2, mais um gigante que puxa o carro de Iggy (5-Castle). NSMBU: Waddlewing's Nest (Rock-Candy Mines). Estava previsto no SMW, segundo uma folha de sprites de protótipo, mas foi cortado. Wonder: as páginas consultadas não o listam. | Fato confirmado [E35][E73][E82] / não verificado (Wonder) |
| Movimento | Preso a uma estaca, anda em volta dela e para em intervalos irregulares, mastigando. No NSMB, pula em vez de deslizar. | Fato confirmado [E35] |
| Ataque | Bote (*lunge*) em direção ao jogador quando ele chega perto, até o limite da corrente. | Fato confirmado [E35] |
| Velocidade | No NSMB, é maior e mais lento que no SMB3. Valores não verificados. | Fato confirmado [E35] / não verificado |
| Reação ao jogador | Detecta proximidade e dá o bote. | Fato confirmado [E35] |
| Obstáculos | A corrente delimita a área de risco. | Observação |
| Colisão | Não pisável. No SMB3, só cai com Estrela, casco, martelo ou Estátua. | Fato confirmado [E35] |
| Resistência | Alta. | Fato confirmado [E35] |
| Como derrotar | Ver colisão. No NSMB, o *Ground Pound* na estaca o solta e rende 3 moedas. | Fato confirmado [E35] |
| Animação / expressões | Mastiga o tempo todo. No SMB3, a corrente **pisca** antes de ele se soltar (depois de ~160 s). Solto, sai pulando. | Fato confirmado [E35] |
| Sons | não verificado. | — |
| Ambiente | No NSMB Wii, quando solto, destrói tijolos e pode ferir outros jogadores. A inspiração foi um cachorro acorrentado que tentou morder Miyamoto. | Fato confirmado [E35]; origem: [E80], não verificado diretamente |

### 2.17 Pokey

| Aspecto | Descrição | Classificação |
|---|---|---|
| Habitat | Estreou no SMB2 (EUA) e não aparece no SMB3. SMW: amarelo. NSMB: só em 2-1 (deserto). NSMB Wii: presente. NSMBU: Perilous Pokey Cave (Layer-Cake Desert); Morton arremessa segmentos gigantes. Wonder: só em Armads on the Roll. | Fato confirmado [E36][E73] |
| Movimento | Coluna de segmentos que avança devagar. | Observação |
| Ataque | Contato espinhoso. | Fato confirmado [E36] |
| Velocidade | Acelera sob o efeito Wonder da fase. Sem valor numérico. | Fato confirmado [E36] / não verificado |
| Reação ao jogador | não verificado. | — |
| Obstáculos | não verificado. | — |
| Colisão | Não pisável. No SMW, casco ou Grab Block remove um segmento, e deslizar numa ladeira derruba o Pokey. | Fato confirmado [E36] |
| Resistência | Por segmentos. No SMW, ganha mais segmentos quando o jogador está montado no Yoshi. | Fato confirmado [E36] |
| Como derrotar | NSMB: fogo em cada segmento (na cabeça, derrota de uma vez), Shell Mario ou Mega. O Yoshi come um segmento por vez. | Fato confirmado [E36] |
| Animação / expressões | No Wonder, continua andando mesmo só com a cabeça. | Fato confirmado [E36] |
| Sons | não verificado. | — |
| Ambiente | Ligado ao deserto (NSMB 2-1; NSMBU). No NSMBU, os segmentos viram frutas para o Yoshi. | Fato confirmado [E36][E73] |

### 2.18 Blooper

| Aspecto | Descrição | Classificação |
|---|---|---|
| Habitat | SMB: fases aquáticas (o falso Bowser de 6-4 é um Blooper). SMB3: água. NSMB: só em 3-3. NSMB Wii: 4-4 e 8-4. NSMBU: Blooper's Secret Lair (Acorn Plains) e Tropical Refresher (Sparkling Waters). | Fato confirmado [E37][E73] |
| Movimento | Zigue-zague em direção ao jogador, sem tocar o chão. | Fato confirmado [E37] |
| Ataque | Contato. | Fato confirmado [E37] |
| Velocidade | No SMB, decide nadar com mais frequência a partir de 5-3 (máscara %00111111 → %00000011). | Fato confirmado [E11] |
| Reação ao jogador | Persegue o tempo todo (SMB). | Fato confirmado [E37] |
| Obstáculos | No SMB, atravessa paredes. A partir do SMB3, não atravessa mais. | Fato confirmado [E37] |
| Colisão | Não pisável debaixo d'água (SMB). Vulnerável a fogo e Estrela. | Fato confirmado [E37][E68] |
| Resistência | 1 projétil. | Fato confirmado [E37] |
| Como derrotar | Fogo ou Estrela. No NSMB Wii, é imune a Ice Ball. | Fato confirmado [E37] |
| Animação / expressões | Contrai o corpo e se impulsiona. | Observação |
| Sons | não verificado. | — |
| Ambiente | SMB3 e NSMB têm Blooper com filhotes. No NSMB Wii, ele se esconde atrás do cenário e dentro de canos. | Fato confirmado [E37] |

### 2.19 Podoboo / Lava Bubble

| Aspecto | Descrição | Classificação |
|---|---|---|
| Habitat | SMB: só em castelos, desde 2-4. SMB3: inclusive de cabeça para baixo em World 5-Fortress 2. SMW: castelos. NSMB, Wii (castelos e Mundo 8) e U: presente. Wonder: só em Pull, Turn, Burn. | Fato confirmado [E38] |
| Movimento | Salta da lava em padrões simples. No SMW, há também os diagonais, que quicam pela sala e afundam ao tocar a lava. | Fato confirmado [E38] |
| Ataque | Contato. | Fato confirmado [E38] |
| Velocidade | não verificado. | — |
| Reação ao jogador | Segue um padrão fixo, sem perseguir. | Observação |
| Obstáculos | Não se aplica. | — |
| Colisão | Invencível no SMB. SMB3: Estátua, martelo, Estrela. NSMB Wii: Ice Ball. | Fato confirmado [E38] |
| Resistência | Invulnerável ou quase. | Fato confirmado [E38] |
| Como derrotar | Ver colisão. | Fato confirmado [E38] |
| Animação / expressões | Ganha olhos no SMW. | Fato confirmado [E38] |
| Sons | O SMW tem um efeito próprio (`SFX_PODOBOO`). | Fato confirmado [E12] |
| Ambiente | No NSMBU, tocar na tela do GamePad o impulsiona para cima. O Wonder tem a variante Lava Blobble. | Fato confirmado [E38] |

### 2.20 Fire Bar e Roto-Disc

| Aspecto | Descrição | Classificação |
|---|---|---|
| Habitat | Fire Bar: SMB só em castelos, desde 1-4. **Não está** nas versões originais de SMB3 e SMW (só no SMB3 do GBA). NSMB a partir de 6-4; NSMB Wii em poucas fases, muitas vezes protegendo Star Coins; NSMBU em torres e no Huge Fire Bar (Fire Bar Cliffs); Wonder. Roto-Disc: SMB3. | Fato confirmado [E39][E69][E70][E40] |
| Movimento | Fire Bar: gira em torno do centro, em sentido horário ou anti-horário. Roto-Disc: orbita esferas, blocos ou um ponto vazio; o Duo-Roto-Disc tem dois discos. | Fato confirmado [E39][E40] |
| Ataque | Contato. | Fato confirmado [E39] |
| Velocidade | SMB: 32 posições angulares e duas velocidades ($28 e $38). Uma volta leva ≈205 ou ≈146 quadros (≈3,4 s / 2,4 s). | Fato confirmado [E11] (dados) / Estimativa (cálculo) |
| Reação ao jogador | Ignora o jogador. | Fato confirmado [E39] |
| Obstáculos | Fixo. | — |
| Colisão | Invulnerável. No SMB, a colisão de inimigos com Mario só é testada a cada dois quadros, **exceto** nas Fire Bars. | Fato confirmado [E14] |
| Resistência | Invulnerável. O Roto-Disc pode ser destruído pela Estátua (SMB3). | Fato confirmado [E40] |
| Como derrotar | Desviar. | — |
| Animação / expressões | Bolas de fogo encadeadas, sem rosto. | Observação |
| Sons | não verificado. | — |
| Ambiente | Foi criada para *The Legend of Zelda*, mas estreou em Mario. | Fato confirmado [E39] (wiki citando entrevistas) |

### 2.21 Monty Mole

| Aspecto | Descrição | Classificação |
|---|---|---|
| Habitat | SMW: só em Yoshi's Island 2 e Cookie Mountain. NSMB: só como piloto do chefe Monty Tank. NSMB Wii: 6-4. NSMBU: Yoshi Hill (Acorn Plains) e Magma-River Cruise (Peach's Castle). | Fato confirmado [E41][E73] |
| Movimento | Sai do chão ou de paredes de terra. Alguns andam e saltam; outros perseguem. | Fato confirmado [E41] |
| Ataque | Investida por contato. | Fato confirmado [E41] |
| Velocidade | Em Cookie Mountain, sai do chão mais rápido que em Yoshi's Island 2. Sem valor numérico. | Fato confirmado [E41] / não verificado |
| Reação ao jogador | Persegue e se vira quando o jogador salta por cima. | Fato confirmado [E41] |
| Obstáculos | Os que só patrulham viram ao bater em paredes. | Fato confirmado [E41] |
| Colisão | Pisável e vulnerável a qualquer ataque. | Fato confirmado [E41] |
| Resistência | 1 golpe. | Fato confirmado [E41] |
| Como derrotar | Qualquer ataque. | Fato confirmado [E41] |
| Animação / expressões | Detalhes da animação de saída não verificados. | não verificado |
| Sons | não verificado. | — |
| Ambiente | Emboscada a partir do terreno. No NSMB Wii, o Kamek transforma plataformas em Monty Moles. | Fato confirmado [E41] |

### 2.22 Wiggler

| Aspecto | Descrição | Classificação |
|---|---|---|
| Habitat | SMW: Forest of Illusion 1 e Outrageous. NSMB: 4-4 e 7-3 (este com um Wiggler gigante). NSMB Wii: 5-2. NSMBU: Soda Jungle. Wonder: só o Racing Wiggler das corridas; o Pokipede é parecido e anda em trilhos. | Fato confirmado [E42] |
| Movimento | Lagarta de segmentos que passeia. | Observação |
| Ataque | Contato. Enfurecido, persegue. | Fato confirmado [E42] |
| Velocidade | Ao ser pisado, fica vermelho e **mais rápido**. Sem valor numérico. | Fato confirmado [E42] / não verificado |
| Reação ao jogador | Calmo, ignora o jogador. Furioso, persegue. | Fato confirmado [E42] |
| Obstáculos | não verificado. | — |
| Colisão | No SMW, pisão e capa não o derrotam, só o enfurecem. No NSMB, o *Ground Pound* o vira por um tempo. | Fato confirmado [E42] |
| Resistência | Alta. | Fato confirmado [E42] |
| Como derrotar | Estrela, objeto arremessado ou Yoshi (SMW). Casco ou Mega (NSMB). | Fato confirmado [E42] |
| Animação / expressões | Muda de cor e de expressão ao se enfurecer. No SMW, desmorona segmento por segmento ao ser derrotado. | Fato confirmado [E42] |
| Sons | No NSMBU, ergue o traseiro nos "bah" da música. | Fato confirmado [E42] |
| Ambiente | O Big Wiggler é imune a power-ups e a veneno (NSMB Wii e U). | Fato confirmado [E42][E83] |

### 2.23 Rex

| Aspecto | Descrição | Classificação |
|---|---|---|
| Habitat | Só no SMW, em pequenos grupos, a partir de Yoshi's Island 1. | Fato confirmado [E43] |
| Movimento | Anda na direção do jogador. | Fato confirmado [E43] |
| Ataque | Contato. | Fato confirmado [E43] |
| Velocidade | Fica um pouco mais rápido depois do 1º pisão. Sem valor numérico. | Fato confirmado [E43] / não verificado |
| Reação ao jogador | Orienta-se para o jogador, sem perseguição ativa. | Fato confirmado [E43] |
| Obstáculos | não verificado. | — |
| Colisão | Pisável. | Fato confirmado [E43] |
| Resistência | 2 pisões. O 1º o encolhe pela metade. | Fato confirmado [E43] |
| Como derrotar | 2 pisões ou 1 golpe de *spin jump*, fogo, capa, Estrela ou Yoshi. | Fato confirmado [E43] |
| Animação / expressões | Achatado "como acordeão" depois do 1º pisão. Tem asas, mas não voa. | Fato confirmado [E43] |
| Sons | não verificado. | — |
| Ambiente | Ensina que um inimigo pode exigir mais de um golpe e mudar depois do primeiro. | Observação |

### 2.24 Chargin' Chuck

| Aspecto | Descrição | Classificação |
|---|---|---|
| Habitat | Só no SMW, comum, muitas vezes perto do portão de chegada. | Fato confirmado [E44] |
| Movimento | Investe contra o jogador. Variantes arremessam bolas de beisebol, chutam bolas, atiram pedras com pá, dividem-se em três, saltam batendo palmas e apitam para chamar inimigos. | Fato confirmado [E44] |
| Ataque | Investida e projéteis, conforme a variante. | Fato confirmado [E44] |
| Velocidade | não verificado. | — |
| Reação ao jogador | Fica mais agressivo quando o jogador está com o Yoshi. Depois de pisados, todos (menos o apitador) passam a investir. | Fato confirmado [E44] |
| Obstáculos | Quebra Rotating Blocks e Grab Blocks. | Fato confirmado [E44] |
| Colisão | Pisável, mas resistente. O Yoshi não consegue comê-lo. | Fato confirmado [E44] |
| Resistência | **3 pisões**, com alguns segundos de invulnerabilidade depois de cada um, como o Boom Boom. Ou 5 bolas de fogo. | Fato confirmado [E44] |
| Como derrotar | Pisões, fogo, 1 golpe de capa ou *Body Press*. Casco, Grab Block, Galoomba ou Bob-omb arremessados o derrotam de uma vez. | Fato confirmado [E44] |
| Animação / expressões | Balança a cabeça ao ser derrotado. | Fato confirmado [E44] |
| Sons | não verificado. | — |
| Ambiente | O apitador acorda Rip Van Fish e chama Super Koopas. | Fato confirmado [E44] |

### 2.25 Fuzzy

| Aspecto | Descrição | Classificação |
|---|---|---|
| Habitat | SMW: raro, a partir de Donut Plains 3, a fase que estreia os ON/OFF. NSMB Wii: Mundos 7 e 9, mais em fases de céu. NSMBU: Fuzzy Clifftop (Rock-Candy Mines). | Fato confirmado [E45][E73] |
| Movimento | Segue trilhos ou circula blocos. | Fato confirmado [E45] |
| Ataque | Não ataca diretamente: só fere se a trajetória cruzar o jogador. | Fato confirmado [E45] |
| Velocidade | não verificado. | — |
| Reação ao jogador | Ignora o jogador. | Fato confirmado [E45] |
| Obstáculos | Preso ao trilho. | Fato confirmado [E45] |
| Colisão | Fere ao toque. | Fato confirmado [E45] |
| Resistência | 1 golpe dos métodos aceitos. | Fato confirmado [E45] |
| Como derrotar | SMW: Yoshi, casco ou *Body Press*. NSMB Wii: fogo, ou congelar e quebrar o gelo. | Fato confirmado [E45] |
| Animação / expressões | Tufo de pelos. | Observação |
| Sons | não verificado. | — |
| Ambiente | Combina com mecanismos de trilho (ON/OFF). | Fato confirmado [E45] |

### 2.26 Urchin

| Aspecto | Descrição | Classificação |
|---|---|---|
| Habitat | SMW: túneis de Forest of Illusion 2. NSMB Wii: presente, com o Big Urchin. NSMBU: Urchin Shoals (Sparkling Waters), sobre gêiseres. Wonder: maior; em terra, rola. | Fato confirmado [E46][E73] |
| Movimento | Sobe e desce, ou vai e volta entre túneis. | Fato confirmado [E46] |
| Ataque | Contato espinhoso. | Fato confirmado [E46] |
| Velocidade | não verificado. | — |
| Reação ao jogador | Segue um padrão fixo. | Observação |
| Obstáculos | Paredes do túnel definem o percurso (SMW). | Fato confirmado [E46] |
| Colisão | Espinhoso e imune a fogo (SMW). O Yoshi quica nele, mas não o come. | Fato confirmado [E46] |
| Resistência | Alta. | Fato confirmado [E46] |
| Como derrotar | Grab Block (SMW). No NSMB Wii, congelado, boia um pouco e depois é nocauteado. | Fato confirmado [E46] |
| Animação / expressões | No NSMBU, fica com cara de raiva ao ser erguido pelos gêiseres. | Fato confirmado [E46] |
| Sons | não verificado. | — |
| Ambiente | No NSMB Wii, congelado pode tapar canos que soltam jatos d'água. | Fato confirmado [E46] |

### 2.27 Porcupuffer

| Aspecto | Descrição | Classificação |
|---|---|---|
| Habitat | SMW: Vanilla Secret 3, uma área secreta de Cookie Mountain e Chocolate Island 1. NSMB Wii: *Enemy Course* do Mundo 4, 6-5 e 9-2. NSMBU: Porcupuffer Falls, que fica em Rock-Candy Mines e não no mundo aquático. | Fato confirmado [E47][E73] |
| Movimento | Nada na superfície em direção ao jogador. No NSMB Wii, salta da água. | Fato confirmado [E47] |
| Ataque | Contato e salto. | Fato confirmado [E47] |
| Velocidade | não verificado. | — |
| Reação ao jogador | Persegue pela superfície. | Fato confirmado [E47] |
| Obstáculos | Fica na linha d'água. | Fato confirmado [E47] |
| Colisão | Espinhoso: o pisão fere, exceto montado no Yoshi (SMW). | Fato confirmado [E47] |
| Resistência | Volta depois de um tempo (NSMB Wii). | Fato confirmado [E47] |
| Como derrotar | Fogo ou capa (SMW). Fogo, Estrela ou casco (NSMB Wii). Congelado, solta-se quase na hora. | Fato confirmado [E47] |
| Animação / expressões | Barbatanas semitransparentes (NSMBU). | Fato confirmado [E47] |
| Sons | não verificado. | — |
| Ambiente | Pressiona o jogador a sair da água ou a nadar fundo. | Observação |

### 2.28 Cooligan

| Aspecto | Descrição | Classificação |
|---|---|---|
| Habitat | NSMB Wii: 3-1 e 9-5. NSMBU: Frosted Glacier (Cooligan Fields e o *Enemy Course*). | Fato confirmado [E48][E73] |
| Movimento | Desliza de barriga e cai em buracos. No NSMBU, também desliza sobre a água. | Fato confirmado [E48] |
| Ataque | Contato. | Fato confirmado [E48] |
| Velocidade | Desliza rápido. Sem valor numérico. | Estimativa (qualitativa) |
| Reação ao jogador | Mantém o deslizamento sem perseguir. | Observação |
| Obstáculos | Cai em buracos em vez de pairar sobre eles. | Fato confirmado [E48] |
| Colisão | Fere ao toque. Se o jogador também estiver deslizando de Penguin Suit, os dois ricocheteiam. | Fato confirmado [E48] |
| Resistência | 2 pisões: o 1º derruba os óculos escuros e o deixa mais lento. | Fato confirmado [E48] |
| Como derrotar | 2 pisões, fogo ou Estrela. Outro Cooligan que bata no lento também o derrota. | Fato confirmado [E48] |
| Animação / expressões | Óculos escuros que caem. | Fato confirmado [E48] |
| Sons | não verificado. | — |
| Ambiente | Combina com pisos de gelo e encostas. | Observação |

### 2.29 Bramball

| Aspecto | Descrição | Classificação |
|---|---|---|
| Habitat | NSMB Wii: só em 5-3. NSMBU: Bramball Woods (Soda Jungle). | Fato confirmado [E49][E73] |
| Movimento | Avança dando "cambalhotas" de mola, plantando os pés. Na borda de uma plataforma ou numa parede, vira. | Fato confirmado [E49] |
| Ataque | Contato com pernas e braços espinhosos. | Fato confirmado [E49] |
| Velocidade | Um passo largo de cada vez. Sem valor numérico. | Fato confirmado [E49] / não verificado |
| Reação ao jogador | Segue um percurso definido. | Fato confirmado [E49] |
| Obstáculos | Vira em bordas e paredes. | Fato confirmado [E49] |
| Colisão | A bola central (cabeça) é pisável. As pernas ferem. | Fato confirmado [E49] |
| Resistência | 1 golpe no ponto fraco. | Fato confirmado [E49] |
| Como derrotar | Pisar no centro. Congelar e dar *Ground Pound*. Fogo ou Estrela. Bater por baixo dá moedas. | Fato confirmado [E49] |
| Animação / expressões | No NSMBU, brota uma folha na cabeça a cada "paah" da música. | Fato confirmado [E49] |
| Sons | Ver acima. | Fato confirmado [E49] |
| Ambiente | Floresta: o jogador pode passar por baixo das pernas. | Fato confirmado [E49] |

### 2.30 Spike

| Aspecto | Descrição | Classificação |
|---|---|---|
| Habitat | SMB3: presente. NSMB: só o Snow Spike, em 5-1. NSMB Wii: com o Stone Spike. NSMBU: Spike's Spouting Sands e Dry Desert Mushrooms (Layer-Cake Desert). Wonder: inclui um vermelho que cospe fogo. | Fato confirmado [E50][E73] |
| Movimento | No SMB3, segue o jogador, se afasta depois de bater na parede algumas vezes e cai de beiradas. No NSMB Wii, fica parado, virado para o jogador. | Fato confirmado [E50] |
| Ataque | Tira da boca uma bola de espinhos e a arremessa, uma ou duas seguidas, e então pausa. O Snow Spike lança bolas de neve que crescem. O Stone Spike lança para baixo. | Fato confirmado [E50] |
| Velocidade | SMB3: surge andando em direção ao jogador a 0,5 px/quadro. | Fato confirmado [E13] |
| Reação ao jogador | Orienta-se para o jogador. | Fato confirmado [E50] |
| Obstáculos | Ver movimento. | Fato confirmado [E50] |
| Colisão | Pisável, mesmo erguendo a bola (SMB3). | Fato confirmado [E50] |
| Resistência | 1 golpe. | Fato confirmado [E50] |
| Como derrotar | Qualquer ataque. | Fato confirmado [E50] |
| Animação / expressões | Gesto de tirar a bola da boca (aviso). | Fato confirmado [E50] |
| Sons | Pula nos "bah" da música (NSMBU). | Fato confirmado [E50] |
| Ambiente | No NSMB Wii, a bola não quebra blocos e sai da tela. No Wonder, há um efeito em que os Spikes cantam e arremessam no ritmo. | Fato confirmado [E50] |

### 2.31 Swoop

| Aspecto | Descrição | Classificação |
|---|---|---|
| Habitat | SMW (Swooper, verde): teto de cavernas, desde Donut Plains 2, sobretudo em Vanilla Dome. NSMB: 2-3 e 5-2. NSMB Wii: 5-2, 6-2 e 6-6. NSMBU: Perilous Pokey Cave, Light Blocks, Dark Tower, entre outras. | Fato confirmado [E51] |
| Movimento | Pendurado no teto, mergulha quando o jogador se aproxima. | Fato confirmado [E51] |
| Ataque | Mergulho por contato. | Fato confirmado [E51] |
| Velocidade | não verificado. | — |
| Reação ao jogador | Ativa-se por proximidade. | Fato confirmado [E51] |
| Obstáculos | não verificado. | — |
| Colisão | Pisável, fácil de derrotar. | Fato confirmado [E51] |
| Resistência | 1 golpe. | Fato confirmado [E51] |
| Como derrotar | Pisão. | Fato confirmado [E51] |
| Animação / expressões | No NSMB Wii e no NSMBU, os olhos brilham no escuro. | Fato confirmado [E51] |
| Sons | não verificado. | — |
| Ambiente | Combina com tetos baixos e escuridão. | Fato confirmado [E51] |

### 2.32 Magikoopa

| Aspecto | Descrição | Classificação |
|---|---|---|
| Habitat | SMW: só em #3 Lemmy's Castle e #7 Larry's Castle. Como chefe: NSMB Wii (torre do Mundo 8) e NSMBU (Slide Lift Tower). | Fato confirmado [E52][E72][E73] |
| Movimento | Some e reaparece (teleporte), sempre em chão sólido. | Fato confirmado [E52] |
| Ataque | Disparo mágico, só quando está visível. A magia transforma Rotating Blocks em inimigos ou itens, como Koopas amarelos. | Fato confirmado [E52][E19] |
| Velocidade | não verificado. | — |
| Reação ao jogador | Mira e dispara no jogador. | Fato confirmado [E52] |
| Obstáculos | A batida no bloco de baixo não o derruba. | Fato confirmado [E52] |
| Colisão | Imune a fogo e capa (SMW). | Fato confirmado [E52] |
| Resistência | Outro Magikoopa surge pouco depois de um ser derrotado, como o Lakitu. | Fato confirmado [E52] |
| Como derrotar | Métodos aceitos no SMW não verificados além das imunidades. Como chefe: 3 pisões (NSMB Wii), ou pisar quando ele para para atacar (NSMBU). | não verificado / Fato confirmado [E72][E73] |
| Animação / expressões | Fica translúcido e depois opaco: o aviso de que vai disparar. | Fato confirmado [E52] |
| Sons | O SMW tem um efeito próprio (`SFX_MAGIC`). | Fato confirmado [E12] |
| Ambiente | Muda o cenário: blocos viram inimigos. | Fato confirmado [E52] |

### 2.33 Hoppycat (Wonder)

| Aspecto | Descrição | Classificação |
|---|---|---|
| Habitat | Sobretudo em Shining Falls, em geral parado. | Fato confirmado [E53] |
| Movimento | Ao ver o jogador, comprime o corpo e o acompanha. **Salta sempre que o jogador salta** e desce devagar. Alguns ficam no teto, com gravidade invertida. | Fato confirmado [E53] |
| Ataque | Contato. Tem espinhos nas costas. | Fato confirmado [E53] |
| Velocidade | Desce devagar depois do salto. Sem valor numérico. | Fato confirmado [E53] / não verificado |
| Reação ao jogador | Espelha a entrada de salto do jogador. | Fato confirmado [E53] |
| Obstáculos | Bate em blocos e os ativa, como o jogador. | Fato confirmado [E53] |
| Colisão | Os espinhos nas costas sugerem que não é pisável por cima. | Observação / não verificado |
| Resistência | não verificado. | — |
| Como derrotar | não verificado. | — |
| Animação / expressões | Compressão antes do salto (aviso). | Fato confirmado [E53] |
| Sons | não verificado. | — |
| Ambiente | A descida lenta abre uma janela para passar por baixo. Uma plataforma lança Hoppycats a cada salto do jogador. | Fato confirmado [E53] |

### 2.34 Bulrush (Wonder)

| Aspecto | Descrição | Classificação |
|---|---|---|
| Habitat | Estreou no Wonder. | Fato confirmado [E54] |
| Movimento | Parado em duas patas. Fica de quatro e investe quando o jogador se aproxima ou o toca. | Fato confirmado [E54] |
| Ataque | Investida. | Fato confirmado [E54] |
| Velocidade | não verificado. | — |
| Reação ao jogador | Não detecta o jogador com o emblema de invisibilidade, a não ser por contato. | Fato confirmado [E54] |
| Obstáculos | Destrói Hard Blocks e blocos quebráveis. Fica atordoado ao bater numa parede indestrutível. | Fato confirmado [E54] |
| Colisão | Pode ser montado. É imune a *Ground Pound*, mesmo atordoado. | Fato confirmado [E54] |
| Resistência | 3 investidas de outro Bulrush, 3 trombadas do Elefante, 3 objetos, 9 bolas de fogo ou 1 golpe de Drill. | Fato confirmado [E54] |
| Como derrotar | Ver resistência. | Fato confirmado [E54] |
| Animação / expressões | Postura de investida (aviso) e atordoamento depois do choque. | Fato confirmado [E54] |
| Sons | não verificado. | — |
| Ambiente | Derrota outros inimigos e fere outros Bulrushes no caminho. | Fato confirmado [E54] |

### 2.35 Maw-Maw (Wonder)

| Aspecto | Descrição | Classificação |
|---|---|---|
| Habitat | Destaque na fase Maw-Maw Mouthful. | Fato confirmado [E55] |
| Movimento | Persegue e come tudo no caminho, inclusive inimigos e power-ups no chão. Uma variante fixa só gira e abre a boca. | Fato confirmado [E55] |
| Ataque | Fere só com a boca. Com o jogador em forma de Goomba (efeito Wonder), engole e mata na hora. | Fato confirmado [E55] |
| Velocidade | não verificado. | — |
| Reação ao jogador | Depois de perseguir um tempo, para ofegante, de língua para fora: a janela. | Fato confirmado [E55] |
| Obstáculos | Ao abrir a boca sob um teto baixo, bate a cabeça e fica atordoado, e o choque ativa ou quebra blocos. | Fato confirmado [E55] |
| Colisão | Pisão atordoa. | Fato confirmado [E55] |
| Resistência | Moderada. | Fato confirmado [E55] |
| Como derrotar | Pisar quando atordoado, *Ground Pound*, Drill, 1 casco ou 9 bolas de fogo. Se estiver de frente para o projétil e sem comer nada, engole e cospe de volta. | Fato confirmado [E55] |
| Animação / expressões | Exaustão (olhos arregalados, língua para fora). | Fato confirmado [E55] |
| Sons | não verificado. | — |
| Ambiente | Interage com o ecossistema da fase: come outros inimigos, e os Goombas entram em pânico. | Fato confirmado [E55][E18] |

### 2.36 Condart (Wonder)

| Aspecto | Descrição | Classificação |
|---|---|---|
| Habitat | Fase Condarts Away!. | Fato confirmado [E56] |
| Movimento | Paira no lugar. Ao ver o jogador, dispara na direção em que olha (horizontal ou para baixo). | Fato confirmado [E56] |
| Ataque | Bicada em linha reta. | Fato confirmado [E56] |
| Velocidade | não verificado. | — |
| Reação ao jogador | Detecção pelo cone de visão (direção do olhar). | Fato confirmado [E56] |
| Obstáculos | Prende o bico em objetos impenetráveis, luta por alguns segundos e volta devagar ao ponto inicial. Quebra tijolos. | Fato confirmado [E56] |
| Colisão | não verificado. | — |
| Resistência | não verificado. | — |
| Como derrotar | não verificado. | — |
| Animação / expressões | Luta para se soltar, empurrando com as asas (janela legível). | Fato confirmado [E56] |
| Sons | não verificado. | — |
| Ambiente | Usa a geometria da fase como armadilha contra si mesmo. | Observação |

**Outros inimigos do Wonder citados:** Konk, parente metálico do Thwomp que também se move na horizontal (o amarelo cai, o azul sobe) [E57]. Rrrumba, que rola ao notar o jogador ou ao descer ladeiras e só é derrotado por *Ground Pound* ou Drill por baixo [E58]. Smackerel, que cava a areia e salta para atacar, destruindo blocos [E59]. Classificação: **Fato confirmado** (wiki de fãs).

---

## 3. Padrões de design de inimigos

### 3.1 Inimigos que ensinam uma mecânica

| Inimigo | O que ensina | Como ensina | Evidência | Classificação |
|---|---|---|---|---|
| Goomba | Pisar | Primeiro inimigo, lento, morre com um pisão e não persegue. Miyamoto: "As long as you stamp on them, you have nothing to fear from Goombas." Iwata: o jogador aprende "in a natural way" que o pisão derrota. | Iwata Asks [E1], conferido em [E3] | Fato confirmado (entrevista) |
| Goomba (origem) | Primeiro contato simples | Foi o **último inimigo criado** no SMB. Antes dele só havia o Koopa, considerado complicado demais para ser o primeiro. Tezuka: "Then right at the very end, we made the Goomba." | [E2][E3][E18] | Fato confirmado (entrevista + wiki) |
| Koopa Troopa | Casco como ferramenta | O pisão não elimina o Koopa: deixa um objeto. Chutado, o casco anda a 3,0 px/quadro (mais que a corrida, 2,5), derruba fileiras de inimigos e volta contra o jogador ao ricochetear. | [E11][E19] | Fato confirmado (código + wiki) |
| Piranha Plant | Timing | Ciclo fixo de subir e descer, com uma regra justa: não emerge com o jogador a menos de 33 px na horizontal. | [E11][E21] | Fato confirmado |
| Boo | Direção do olhar | Para quando é olhado e persegue pelas costas. O jogador controla o inimigo virando o personagem. No Wonder, a luz substitui o olhar. | [E23] | Fato confirmado |
| Thwomp | Leitura de aviso | No SMW, a sequência é: espiar (<64 px), enfurecer e cair (≈40 px), tremer a tela com som, esperar ~1 s e subir devagar. Cada estado anuncia o próximo. | [E12][E31] | Fato confirmado (código + wiki) |
| Rex, Cooligan, Chargin' Chuck | Inimigo de vários golpes | O 1º golpe muda forma e velocidade (Rex encolhe, o Cooligan perde os óculos). O Chuck exige 3 pisões com invulnerabilidade entre eles. | [E43][E48][E44] | Fato confirmado |
| Chain Chomp | Zona de perigo visível | A corrente mostra até onde o bote alcança. Antes de se soltar, a corrente pisca. | [E35] | Fato confirmado |
| Lakitu | Pressão contínua | Gerador infinito de Spinies em fases com retas longas e poucos abrigos. | [E29][E30] | Fato confirmado |
| Dry Bones | "Derrotado" não é "eliminado" | Desmonta e volta. No NSMBU, brilha em vermelho antes de voltar. | [E32] | Fato confirmado |
| Hoppycat | O jogador comanda o inimigo | Salta sempre que o jogador salta. | [E53] | Fato confirmado |

**Princípios declarados pelos desenvolvedores:**

- **Aprender aos poucos.** Miyamoto quer que o jogador "gradually and naturally understand what they're doing" na fase 1-1 [E10]. Classificação: Fato confirmado (entrevista, via terceiros).
- **Quatro tempos (*kishōtenketsu*).** Koichi Hayashida descreve: aprender a mecânica, enfrentar uma situação mais complexa, sofrer uma reviravolta inesperada, demonstrar domínio. Defende ainda **um conceito central por fase**, "carried through absolutely all the way" [E9]. Classificação: Fato confirmado (entrevista).
- **Animação comunica estado.** No Wonder, a equipe trata a animação como meio de "communicating the character's state to the player". Os comportamentos clássicos não mudam, porque isso alteraria a jogabilidade; as novidades vão para expressão e apresentação [E5]. Classificação: Fato confirmado (entrevista oficial).
- **Várias formas de jogar.** Tezuka lembra que o SMB foi feito para se jogar de vários jeitos, "like focusing on defeating all the enemies" [E7]. Classificação: Fato confirmado (entrevista oficial).
- **Errar sem perder tudo.** No SMW, Tezuka buscou ações novas para que iniciantes se divertissem, e um mecanismo que evita perder a vida ao tocar um inimigo, como montar o Yoshi [E8]. Classificação: Fato confirmado (entrevista oficial).
- **Prototipar muitas ideias.** A equipe do Wonder juntou mais de 2.000 ideias em notas adesivas e prototipou várias na hora. Mouri resume: "first, you've got to take everything to the extreme" [E4]. Classificação: Fato confirmado (entrevista oficial).

### 3.2 Telegrafia e antecipação

| Sinal | Exemplos oficiais | Classificação |
|---|---|---|
| Mudança de expressão | Thwomp do SMW: espiando, depois furioso [E31]. Koopa do Wonder fica bravo ao ver o jogador [E19]. | Fato confirmado |
| Tremor antes de agir | Koopa do SMB mexe as pernas antes de sair do casco [E19]. O Buzzy do SMB **não avisava**, e o SMB3 acrescentou o tremor [E34]: a série corrigiu um sinal ausente. | Fato confirmado |
| Piscar | Bob-omb do SMW antes de explodir [E28]. Corrente do Chain Chomp antes de se soltar [E35]. | Fato confirmado |
| Brilho de cor | Dry Bones (NSMBU) brilha em vermelho ao se reconstituir [E32]. | Fato confirmado |
| Postura preparatória | Bulrush fica de quatro [E54]. Hoppycat se comprime [E53]. Spike tira a bola da boca [E50]. Lakitu se esconde na nuvem por ~1 s [E29]. Bill Blaster "estica" no NSMB Wii [E27]. | Fato confirmado |
| Visibilidade | Magikoopa só dispara quando fica opaco [E52]. | Fato confirmado |
| Animação de dano que anuncia a fase seguinte | No SMB3, o Boom Boom já mostra as asas na animação do 1º pisão antes de passar a voar [E61]. | Fato confirmado |
| Tela + som | Thwomp do SMW: 24 quadros de tremor e efeito "KAPOW" [E12]. | Fato confirmado |
| Exaustão / preso (janela) | Maw-Maw ofegante [E55]. Condart com o bico preso [E56]. Bulrush atordoado [E54]. | Fato confirmado |

**Regras justas no código.** Piranhas não emergem com o jogador a menos de 33 px. Canhões não disparam com o jogador a menos de ~40 px [E11]. No SMB, a colisão com inimigos só é testada a cada dois quadros, exceto nas Fire Bars, o que dá uma pequena tolerância [E14]. Classificação: Fato confirmado (documentação técnica).

### 3.3 Silhuetas legíveis

- **Espinho = não pise; liso = pisável.** Spiny, Porcupuffer, Urchin e Pokey ferem quem pisa. Mas o Bramball tem centro liso pisável e pernas espinhosas, e o Spike do SMB3 é pisável mesmo erguendo a bola [E30][E47][E46][E36][E49][E50]. Classificação: Fato confirmado (casos) / Observação (regra geral).
- **Asas = trajetória aérea; perder as asas = rebaixamento** para a versão terrestre [E20]. Classificação: Fato confirmado.
- **Contraste por contexto.** No SMB, o Goomba é azul no subsolo e cinza no castelo, e o Koopa ganha paleta escura nos castelos [E18][E19]. Na escuridão do Wonder, tudo vira silhueta, mas olhos e dentes continuam visíveis [E86]. Os olhos do Swoop brilham no escuro [E51]. Classificação: Fato confirmado.
- **Restrição técnica.** A animação do Goomba é um único sprite espelhado, por falta de espaço [E18]. Classificação: Fato confirmado.
- **Leitura do protagonista.** No Wonder, o corpo de Mario aponta na direção do movimento e o rosto fica virado para o jogador, para que as expressões sejam lidas [E5]. Classificação: Fato confirmado.

### 3.4 Como as variantes aumentam a dificuldade

| Eixo | Exemplos | Efeito no jogo | Classificação |
|---|---|---|---|
| Cor muda a regra | Koopa verde cai e vermelho vira [E19]. Shy Guy vermelho cai e rosa vira [E24]. SMW: azul mais rápido e chuta cascos; amarelo persegue [E19][E12]. Cheep Cheep vermelho mais rápido que o cinza [E33]. Lakitu de ovos verdes, menos agressivo [E29]. Konk amarelo cai e azul sobe [E57]. Spike vermelho do Wonder cospe fogo [E50]. | O jogador aprende uma regra e a cor a altera sem mudar a silhueta. | Fato confirmado |
| Asas | Paratroopa [E20]. Para-Goomba do SMB3, que solta Micro-Goombas [E18]. Para-Beetle, que vira plataforma [E34]. | Novas trajetórias e uso como plataforma. | Fato confirmado |
| Espinhos | Spiny × Buzzy [E30][E34]. Spike Top [E34]. Prickly Goomba [E18]. Spiny Cheep Cheep [E33]. | Proíbe o pisão. | Fato confirmado |
| Esqueleto | Dry Bones, Bony Beetle, Bone Goomba e Bone Piranha [E32][E34][E18][E21]. | Derrota temporária. | Fato confirmado |
| Tamanho | Giant Land do SMB3. No NSMB Wii, o Big Goomba vira dois Hefty, que viram Goombas [E18]. | Mais golpes; divisão em menores. | Fato confirmado |
| Projétil | Hammer, Boomerang, Fire, Sledge e Ice Bros [E25]. | Mesmo corpo, outra trajetória. | Fato confirmado |
| Progressão escondida (SMB) | 2ª volta: Goomba vira Buzzy e inimigos andam a 0,75 px/quadro. A partir de 5-3: martelos mais frequentes, chamas de Bowser 16 quadros antes, até 4 Cheep Cheeps voadores, Blooper mais ativo e outra frequência de canhões. Plataformas móveis usam outra caixa de colisão em castelos e a partir de 5-3. | A dificuldade sobe sem novos inimigos. | Fato confirmado [E11]. Que a caixa das plataformas seja menor é interpretação do código, **não verificado** em jogo. |
| Mudança depois de um golpe | Rex, Wiggler, Cooligan, Chargin' Chuck [E43][E42][E48][E44]. | Força o jogador a reavaliar. | Fato confirmado |

### 3.5 Densidade de inimigos por fase

Contagens das tabelas de inimigos das páginas de fase [E77]:

| Fase | Inimigos | Espécies | Leitura | Classificação |
|---|---|---|---|---|
| SMB 1-1 | 17 (16 Goombas, 1 Koopa) | 2 | Repetição de um único verbo | Fato confirmado [E77] / Observação (leitura) |
| SMB 1-2 | 22 (14 Goombas, 3 Koopas verdes, 1 vermelho, 4 Piranhas) | 3 (+1 variante de cor) | 1 espécie nova (Piranha) e 1 regra nova (vermelho) | Fato confirmado / Observação |
| SMB 4-1 | Lakitu (volta, a partir de 3 pontos), Spinies infinitos, 4 Piranhas | 3 | A densidade vem de um gerador | Fato confirmado / Observação |
| SMB 8-1 | 62 (26 Goombas, 17 Koopas, 3 Paratroopas, 4 Buzzies, 12 Piranhas) | 5 | Só espécies conhecidas, em quantidade | Fato confirmado / Observação |
| SMB3 1-1 (NES) | 14 (4 Goombas, 1 Para-Goomba, 3 Koopas, 3 Paratroopas, 1 Piranha, 2 Venus) | 6 | Supõe que o jogador já conhece o SMB | Fato confirmado / Observação |
| NSMB Wii 1-1 | 27 (21 Goombas, 6 Koopas) | 2 (+variante) | Mesmo padrão do SMB 1-1 | Fato confirmado / Observação |
| NSMB Wii 8-1 | 16 Buzzy Beetles, pedras de lava infinitas e uma nuvem de cinzas que avança | 1 + perigos | No fim do jogo, a pressão vem do ambiente | Fato confirmado [E77] / Observação |

**Limite técnico.** No NES, com 5 ou mais objetos de sprite na tela (incluindo Fire Bars, bolas de fogo e plataformas), alguns objetos deixam de aparecer. A densidade era limitada também por hardware [E14]. Classificação: Fato confirmado.

**Dificuldade ajustável.** No Wonder, a dificuldade de cada fase aparece antes de entrar, e os emblemas mudam a dificuldade de uma mesma fase sem alterar os inimigos. Tezuka diz que o 2D tinha fama de "unforgiving" [E6]. Classificação: Fato confirmado.

**Leitura (Observação).** As fases iniciais usam poucas espécies e muita repetição. As do meio somam uma espécie ou uma regra por vez. As finais aumentam a quantidade de espécies já conhecidas ou trocam inimigos por perigos do ambiente.

---

## 4. Chefes em jogos Mario 2D

### 4.1 Elenco de chefes por jogo

| Jogo | Chefes e local | Condição de vitória | Classificação |
|---|---|---|---|
| SMB | Bowser no 8-4 e sete falsos Bowsers, no salão final do castelo de cada mundo, numa ponte sobre lava. Nos mundos 1–5 cospem fogo, nos mundos 6–7 arremessam martelos, e no 8 o Bowser verdadeiro faz os dois. | Tocar o machado (a ponte some) ou acertar 5 bolas de fogo, que revelam o inimigo disfarçado. O pisão fere o jogador. | Fato confirmado [E68] |
| SMB3 | Boom Boom nas fortalezas. Koopalings na cabine de cada dirigível, depois de atravessar a artilharia e os Rocky Wrenches [E79]. Bowser no último salão. | Boom Boom: 3 pisões, 5 bolas de fogo ou 5 martelos. Koopalings: 3 pisões. Bowser: cair no buraco que ele mesmo abre ao quebrar o chão, ou 35 bolas de fogo, ou 3 martelos. | Fato confirmado [E61][E66][E64][E69] |
| SMW | Grupo de 4 Reznors nas fortalezas. Big Boo (secreto) na Donut Secret House. Koopalings nos castelos. Bowser no telhado, no Koopa Clown Car. | Reznor: golpe por baixo da plataforma. Big Boo: Grab Blocks. Iggy e Larry: empurrar para a lava. Demais: pisões. Bowser: Mechakoopas arremessados nele. | Fato confirmado [E70][E62][E65][E67][E64] |
| NSMB | Bowser Jr. em todas as torres. Castelos com chefes únicos: Bowser (vira esqueleto), Mummipokey, Cheepskipper, Boss Goomba, Petey Piranha, Monty Tank, Lakithunder e Dry Bowser. No final, Bowser gigante com Bowser Jr. | Em geral 3 pisões (o *Ground Pound* conta 2). As três versões de Bowser caem num interruptor de caveira. | Fato confirmado [E71] |
| NSMB Wii | Koopalings nas torres e nos castelos (o segundo encontro tem arena modificada). Bowser Jr. nos dirigíveis. Kamek na torre do Mundo 8. Bowser em duas fases. | 3 pisões. Bowser: interruptor; depois, já gigante, uma perseguição. | Fato confirmado [E72] |
| NSMBU | Boom Boom na maioria das torres, Boss Sumo Bro, Kamek, Koopalings em castelos temáticos, Bowser Jr. nos dirigíveis, Bowser. | Pisões. Interruptor ou fogo no Bowser. | Fato confirmado [E73] |
| Wonder | Bowser Jr., que vira Wonder Bowser Jr., no fim dos palácios (4 lutas). Mecha Maker nos dirigíveis. Wonder Bowser na batalha final. | Jr.: golpes. Mecha Maker: botão vermelho. Wonder Bowser: 6 golpes no interruptor "!" sob o queixo. | Fato confirmado [E74][E63] |
| Wonder (Switch 2 Edition, 26/03/2026) | Koopalings no fim das fases *Brigade Tent*, versões remixadas em que eles atacam durante todo o percurso usando poderes Wonder. | Batalha no fim da fase. | Fato confirmado [E75] (wiki; não verificado em fonte oficial) |

Os Koopalings estrearam no SMB3. Segundo a Super Mario Wiki, foram modelados a partir da equipe do jogo e receberam nomes de músicos na localização norte-americana; o original japonês não os nomeava [E60]. Classificação: Fato confirmado (wiki de fãs).

### 4.2 Como o chefe é anunciado

- **Portas.** No SMW, portas vermelhas grandes marcam a sala do chefe. A partir do NSMB Wii, a porta da torre é vermelha, a do castelo é azul e a do Bowser final é verde [E76]. Classificação: Fato confirmado.
- **Corredor com aviso.** No NSMB Wii, ouve-se Iggy rindo enquanto o jogador anda pelo corredor até a sala dele [E67]. Classificação: Fato confirmado.
- **Cena curta.** No NSMBU, cada luta com Boom Boom começa com uma pequena cena, e o Kamek encanta o chefe antes da luta (crescer, *spin jump*, voar) [E61][E73]. No NSMB Wii, o Kamek transforma a arena ou aumenta obstáculos [E72]. Classificação: Fato confirmado.
- **Entrada física.** No SMB3, a luta com Bowser começa quando ele **cai** no salão [E64]. Classificação: Fato confirmado.
- **Música.** "King of the Koopas", do SMB3, é o primeiro tema associado diretamente a Bowser [E78]. Kondo diz que, no SMB, simplesmente jogou e compôs para acompanhar o jogo [E7]. No Wonder, a arena final tem pisos rítmicos que lançam o jogador quando ele pula no tempo da música [E74]. Classificação: Fato confirmado. Que toda sala de chefe troque a trilha por um tema próprio é **Observação**, sem fonte única que liste todos os casos.

### 4.3 Arenas e interação com o ambiente

| Arena | Exemplo | Classificação |
|---|---|---|
| Ponte sobre lava + machado ou interruptor | SMB; NSMB; NSMB Wii; NSMBU [E68][E71][E72][E73] | Fato confirmado |
| Chão destrutível | No SMB3, o *ground pound* do Bowser quebra blocos, e ele cai no buraco que abriu [E64] | Fato confirmado |
| Ponte que desaba | Reznor (SMW): depois de dois derrotados, a ponte se desfaz das bordas para o centro [E62] | Fato confirmado |
| Plataforma inclinável sobre lava | Iggy e Larry (SMW); a arena de Larry tem 3 Lava Bubbles [E67][E66] | Fato confirmado |
| Interruptor + plataformas temporárias | Boss Goomba (NSMB): o interruptor ergue plataformas para o *Ground Pound* [E71] | Fato confirmado |
| Superfície que vira contra o chefe | Petey Piranha (NSMB) escorrega no gelo e cai de costas [E71] | Fato confirmado |
| Nível d'água variável | Wendy (NSMB Wii): a água sobe e desce por magia do Kamek, e não dá para pisar nela submersa [E85] | Fato confirmado |
| Elementos acoplados | Iggy (NSMB Wii) num carro puxado por um Chain Chomp gigante, que fica vermelho e mais rápido quando Iggy é atingido. NSMBU: gêiseres de Larry, anéis de Wendy que derrubam estalactites, canos e Magmaarghs de Iggy, canhão de Roy em plataformas móveis, segmentos de Pokey de Morton [E35][E73] | Fato confirmado |
| Arena que muda de regra | Wonder Bowser Jr.: tamanho, piso de gelo ou mel, água flutuante, cópias no escuro [E74] | Fato confirmado |

### 4.4 Janelas de vulnerabilidade

| Tipo de janela | Exemplos | Classificação |
|---|---|---|
| Pisão direto, 3 vezes | Koopalings do SMB3 e do NSMB Wii; Boom Boom; maioria dos chefes do NSMB | Fato confirmado [E66][E72][E61][E71] |
| Abertura depois de um ataque | Petey cai de costas; Lakithunder fica vulnerável ao descer; Boss Sumo Bro derrubado da plataforma; Magikoopa (NSMBU) para para atacar | Fato confirmado [E71][E73] |
| Golpe indireto | Reznor por baixo; Big Boo com Grab Blocks; Bowser do SMW com Mechakoopas; Bob-ombs do Bowser Jr. devolvidos (NSMBU); Targeting Teds guiados contra o submarino | Fato confirmado [E62][E65][E64][E63] |
| Empurrar para o perigo | Iggy e Larry (SMW) são imunes e só caem na lava | Fato confirmado [E67][E66] |
| Interruptor na arena | Machado (SMB); caveira (NSMB); "!" e Bowser Switch (Wonder) | Fato confirmado [E68][E71][E74] |
| Invulnerabilidade entre golpes | Boom Boom; Chargin' Chuck | Fato confirmado [E61][E44] |

### 4.5 Mudança de fase

- **Boom Boom (SMB3).** Começa andando e agachando para mostrar os espinhos. Depois do 1º golpe, ou salta alto ou voa (as asas já aparecem na animação de dano). Depois do 2º, anda muito rápido e para de agachar [E61]. Classificação: Fato confirmado.
- **Aceleração por golpe.** O Boss Goomba (NSMB) acelera a cada golpe [E71]. Em alguns mundos, o Bowser Jr. (NSMB) passa a saltar alto depois de 2 golpes [E63]. Classificação: Fato confirmado.
- **Mais projéteis.** No NSMBU, Larry passa a lançar 2 bolas depois de 2 pisões, e Wendy, 3 anéis em vez de 2. Ludwig mantém os clones depois do 1º pisão e, depois do 2º, todos atiram mais rápido e trocam de lugar [E73]. Classificação: Fato confirmado.
- **Troca de forma.** Bowser Jr. vira Wonder Bowser Jr. depois do 1º golpe. Os ataques do Wonder Bowser ficam mais complexos a cada golpe, e a armadura cai no 5º [E74]. No NSMB Wii, Bowser volta gigante numa 2ª fase [E72]. Classificação: Fato confirmado.
- **Hoje no Lume.** Os guardiões já ficam mais rápidos na segunda metade da vida (`src/core/bosses.ts` e README). Classificação: Fato confirmado (código do projeto).

### 4.6 Vitória e animação de derrota

- SMB: o machado faz a ponte sumir e o chefe cair. A bola de fogo revela a criatura disfarçada de Bowser [E68]. Classificação: Fato confirmado.
- SMB3: o Koopaling foge, a varinha volta e o rei se restaura [E66]. O Boom Boom solta uma bola mágica que destrói a fortaleza e abre caminho no mapa [E61]. Classificação: Fato confirmado.
- SMW: o castelo do Koopaling é destruído numa cena [E67]. O Clown Car vira e solta a princesa [E64]. Classificação: Fato confirmado.
- NSMB: Bowser cai na lava e vira esqueleto, e volta mais tarde como Dry Bowser. A derrota de um chefe vira a próxima ameaça [E71]. Classificação: Fato confirmado.
- Wonder: o castelo do vilão volta a ser o castelo do reino [E74]. Classificação: Fato confirmado.

### 4.7 Síntese (Observação)

A estrutura que se repete tem seis passos:

1. Aviso de entrada: porta, corredor ou cena.
2. Arena que contém a mecânica do mundo.
3. Dois a quatro ataques, cada um com aviso.
4. Janela clara logo depois de um ataque.
5. Cerca de três golpes, com mudança de fase.
6. Encerramento visual que transforma o mapa ou o mundo.

---

## 5. Aplicação no Lume (Decisão do projeto)

> Tudo nesta seção é **Decisão do projeto**: são propostas originais para discutir e testar, não fatos sobre os jogos estudados. A coluna "Papel paralelo" cita só a **função** de um inimigo oficial, nunca a aparência. A coluna "Base técnica" indica o tipo atual de `src/core/types.ts` (`walker`, `shell`, `flyer`, `shooter`, `armored`, `boss`) que serviria de ponto de partida.

### 5.0 Regras de criação e calibração

1. **Lista de exclusão visual.** Não usar: tartaruga com casco espinhoso, cogumelo ambulante, fantasma branco redondo de língua para fora, bloco de pedra com rosto, bala com olhos, planta carnívora saindo de cano verde, lagarta de segmentos com flor, Koopa encapuzado com varinha, dinossauro montável. Silhuetas e nomes partem de fauna e flora brasileiras, de objetos do cotidiano e do tema "lume" (luz).
2. **Um verbo por criatura.** Cada espécie ensina uma coisa. Variantes só depois que a base foi ensinada (ver PESQUISA_BIOMAS.md).
3. **Velocidades em proporção ao jogador.** O caminhante do SMB anda a ⅓ da caminhada e ⅕ da corrida de Mario [E11]. Com a caminhada (220 px/s) e a corrida (340 px/s) do Lume, isso dá ≈68–73 px/s. A versão "rápida" do SMB (0,75 px/quadro) é 1,5× a base [E11], o que no Lume daria ≈105–110 px/s. A fórmula atual (55 + 7×mundo) vai de 62 px/s no mundo 1 a 125 px/s no mundo 10. Recomendamos limitá-la a ~110 px/s e usar variantes, não mais velocidade, nos mundos finais.
4. **Casco mais rápido que o jogador.** No SMB, o casco é 1,2× a corrida (3,0 contra 2,5 px/quadro) [E11]. No Lume, é 1,06× (360 contra 340 px/s). Recomendamos 400–410 px/s para que o casco seja de fato perigoso de seguir.
5. **Projéteis lineares na velocidade da caminhada.** No SMB, o projétil linear anda na caminhada do jogador (1,5 px/quadro) [E11]. O Lume usa 180 px/s nos atiradores e 175–235 px/s nos guardiões dos mundos 1–5, perto dos 220 px/s da caminhada. Manter.
6. **Regra justa de disparo.** Atiradores e plantas não agem com o jogador a menos de ~2 larguras do personagem (≈44 px), equivalente aos 33–40 px do SMB [E11]. Hoje o atirador do Lume dispara a cada 2,2 s sempre que o jogador está a menos de 650 px, sem distância mínima. Recomendamos acrescentá-la. Todo ataque tem pelo menos ~0,5 s de aviso visual e sonoro. Esse valor é uma meta de projeto, calibrada pelo ~1 s do Lakitu e pela pausa de ~1 s do Thwomp [E29][E12].
7. **Janela luminosa.** Os guardiões do Lume já mostram uma "abertura luminosa" quando ficam vulneráveis (README). Hoje ela dura 1,65 s num ciclo de 4,8 s, e 1,1 s num ciclo de 3,8 s na metade final (`src/core/bosses.ts`). Toda janela de vulnerabilidade, de inimigo comum ou chefe, usa esse mesmo código visual: brilho quente pulsante e som agudo curto. As janelas "de 2 s" propostas abaixo são **referências iniciais** para testar: até 1,5–2 s na primeira metade da luta, cerca de 1,1 s na fase final.

### 5.1 Reino Verde — caminhantes simples, criaturas de casco, plantas hostis, introdutórios

| Nome | Silhueta | Comportamento | Fraqueza | Papel paralelo | Base técnica |
|---|---|---|---|---|---|
| **Musgote** | Bolinho de musgo baixo e mais largo que alto, broto de duas folhas no topo, pés de raiz | Anda a ~⅓ da caminhada do jogador, vira em paredes, cai de beiradas e ignora o jogador | Pisão (achata e solta esporos de luz), fogo, casco | Caminhante introdutório (Goomba) | `walker` |
| **Rolim** | Tatuzinho-de-jardim de cinco placas arqueadas, antenas curtas. O **verde** cai de beiradas; o **âmbar** vira | Pisado, vira bola; chutado, rola mais rápido que a corrida e ricocheteia. Antes de desenrolar (~5 s), as antenas tremem | Pisão. A bola em movimento fere o jogador | Casco como ferramenta (Koopa Troopa) | `shell` |
| **Sinoreira** | Flor de sino invertido em vasos de barro, pétalas serrilhadas | Ciclo de 3 tempos: sobe, abocanha, recolhe. Não sai com o jogador encostado no vaso | Fogo; casco atirado fecha a flor | Planta de timing (Piranha Plant) | `shooter` sem projétil |
| **Pulapólen** | Tufo de dente-de-leão com dois olhos | Salta em arcos fixos de altura constante. Pisado, perde o tufo e vira uma semente que só anda | 2 pisões | Saltador que perde as "asas" (Koopa Paratroopa) | `flyer` → `walker` |

**Chefe — Grão-Rolim (Guardião do Pomar).** *Arena:* clareira entre duas macieiras, fechada por cercas. *Ataques:* (1) rola de um lado ao outro, girando no lugar por 0,8 s antes; (2) salta e sacode as árvores, derrubando frutos que rolam; (3) cospe três sementes em arco. *Janela:* depois de bater na cerca, cai de costas, tonto, com a barriga luminosa → pisão. *Fase (≤50%):* rola duas vezes seguidas e chama dois Musgotes. *Derrota:* desenrola, espirra pétalas e foge para a toca; a macieira floresce.

### 5.2 Deserto Dourado — adaptados à areia, ataque à distância, saem do chão, resistentes ao calor

| Nome | Silhueta | Comportamento | Fraqueza | Papel paralelo | Base técnica |
|---|---|---|---|---|---|
| **Escaravelho-brasa** | Besouro redondo com fendas incandescentes na carapaça | Alterna dois estados. **Brasa**: fendas vermelhas, pisá-lo fere. **Cinza**: apagado, pisável e vira casco. As fendas pulsam 1 s antes de reacender. Imune a fogo | Pisão no estado cinza; casco | Imune a fogo que alterna pisável e espinhoso (Buzzy Beetle + Spiny) | `armored` |
| **Minhocão-de-duna** | Verme de anéis com coroa de mandíbulas | Viaja sob a areia (montículo e rastro de grãos) e emerge em arco no último ponto onde viu o jogador | Pisão na cabeça enquanto volta a afundar | Emboscada do solo (Monty Mole) | `walker` (novo estado "enterrado") |
| **Mandacaru-arqueiro** | Cacto atarracado de três braços | Infla por 0,5 s e dispara um leque de 3 espinhos de longo alcance. Não dispara com o jogador encostado | Pisão na flor do topo; fogo | Atirador à distância (Venus Fire Trap / Spike) | `shooter` |
| **Feneco-miragem** | Raposinha de orelhas enormes, corpo translúcido nas bordas | Corre em zigue-zague sobre dunas e mergulha na areia movediça sem morrer, reaparecendo adiante. Assusta-se se o jogador correr na direção dele | Pisão em terreno firme | Caminhante rápido adaptado ao terreno (Koopa "rápido" do SMW) | `walker` |

**Chefe — Rainha-Ampulheta (Templo das Areias).** *Arena:* salão com faixas de areia movediça e dois pilares. *Ataques:* (1) mergulha e emerge sob o jogador, com um redemoinho de grãos 1 s antes; (2) rajada de areia em leque disparada pela cauda; (3) varredura das garras que arrasta o jogador para a areia movediça; (4) blocos de arenito que caem, marcados por sombras. *Janela:* ao atacar um pilar, o ferrão prende na pedra e a junta da cauda brilha. *Fase:* a areia movediça sobe aos poucos e ela passa a emergir duas vezes. *Derrota:* o corpo escorre como uma ampulheta virada e revela a relíquia.

### 5.3 Costa dos Corais — peixes hostis, aquáticos, anfíbios, usuários de correnteza

| Nome | Silhueta | Comportamento | Fraqueza | Papel paralelo | Base técnica |
|---|---|---|---|---|---|
| **Agulhão-flecha** | Peixe-agulha fino e comprido | Patrulha devagar. Alinhado na horizontal com o jogador, treme por 0,5 s e dispara em linha reta. Se acertar o coral, prende o bico | Golpe enquanto está preso; fogo fora d'água | Peixe de investida (Cheep Cheep / Condart) | `flyer` (meio aquático) |
| **Medusa-lanterna** | Sino translúcido que emite luz, tentáculos curtos | Pulsa para cima em direção ao jogador e afunda devagar, em ritmo previsível. Ilumina grutas | Tocar o topo quando "apagada", logo depois do pulso; coral atirado | Perseguidor em zigue-zague (Blooper) | `flyer` |
| **Sapo-maré** | Sapo de papo inflável | Na água, nada rente à superfície. Em terra, salta curto. Quando infla o papo (aviso), dá um salto alto entre os dois meios | Pisão em terra; na água fica escorregadio | Anfíbio que alterna meios (Porcupuffer / Cheep Cheep saltador) | `walker` + `flyer` |
| **Ermitão-jato** | Caranguejo-ermitão com concha de búzio em bico | Aspira água e solta um jato que empurra jogador e inimigos. A corrente aparece como uma trilha de bolhas | Golpe por trás; casco | Usuário de correnteza (gêiseres e jatos do NSMB) | `shooter` (empurrão, sem dano) |

**Chefe — Rei-Concha (combate de natação).** *Arena:* recife submerso com correntes laterais. *Ataques:* (1) jato que inverte a corrente; (2) anéis de bolhas que prendem por 1 s (o jogador escapa nadando); (3) golpe de pinça que levanta coral; (4) chama Agulhões. *Janela:* a pinça crava na areia, a concha abre e mostra o núcleo luminoso → o jogador nada até ele e o toca por cima. *Fase:* a corrente alterna a cada ciclo e ele passa a usar dois jatos. *Derrota:* solta uma coluna de bolhas e abandona a concha, que vira plataforma até a saída.

### 5.4 Montanhas Geladas — criaturas de gelo, deslizantes, voadores do frio, modificadores de superfície

| Nome | Silhueta | Comportamento | Fraqueza | Papel paralelo | Base técnica |
|---|---|---|---|---|---|
| **Lontra-trenó** | Lontra de barriga para baixo, cauda achatada | Desliza em linha reta, rápida no gelo e lenta na neve, e cai em buracos. O 1º pisão derruba o gorro de gelo e a deixa mais lenta | 2 pisões; fogo | Deslizante (Cooligan) | `walker` (sem atrito) |
| **Nevoso-rolante** | Bola de neve com olhos | Rola ladeira abaixo e **cresce** até se partir numa parede. No plano, para | Fogo derrete; pisão quando pequeno | Ameaça que cresce (bolas do Snow Spike / Rrrumba) | `shell` |
| **Coruja-geada** | Coruja branca de penas pontudas | Fica no galho e mergulha em diagonal quando o jogador entra no cone de visão (os olhos acendem). Deixa rastro de flocos | Pisão na subida depois do mergulho | Voador de mergulho (Swoop) | `flyer` |
| **Lesma-geleira** | Lesma azul translúcida | Deixa um rastro de gelo que torna o piso escorregadio por alguns segundos. Fogo derrete o rastro | Pisão (o rastro fica) | Modificador de superfície (sem paralelo direto) | `walker` + efeito de piso |

**Chefe — Morsa-Nevasca (Coração da Nevasca).** *Arena:* lago congelado com bordas de rocha aderente e teto de estalactites. *Ataques:* (1) desliza de barriga pela arena inteira; (2) urro que derruba estalactites marcadas por sombras; (3) sopro que congela uma faixa de rocha; (4) batida que abre buracos temporários no gelo. *Janela:* depois do deslize, bate na parede, fica tonta e as presas racham, luminosas. *Fase:* a arena inteira vira gelo e ela desliza duas vezes, quicando. *Derrota:* as presas quebram e ela gira para fora da arena até um monte de neve.

### 5.5 Floresta Encantada — plantas hostis, camuflados, voadores, guardiões vegetais

| Nome | Silhueta | Comportamento | Fraqueza | Papel paralelo | Base técnica |
|---|---|---|---|---|---|
| **Cipó-chicote** | Trepadeira pendurada no dossel, ponta em flor | Desenrola e varre um arco: as folhas tremem e a ponta brilha antes. Depois recolhe | Fogo corta; pisão na flor quando estendida | Planta suspensa (Piranha invertida / Bramball) | `shooter` (golpe corpo a corpo) |
| **Toco-dorminhoco** | Toco musgoso que se confunde com plataforma, só denunciado por uma respiração lenta e um olho entreaberto | Dormindo, serve de plataforma e lança quem o pisa. Acordado, persegue por 3 s e volta a dormir | Fogo ou casco quando acordado | Camuflado, emboscada (Goombas dormindo do Wonder / Monty Mole) | `walker` (estado "sono") |
| **Vaga-lume-vigia** | Vagalume grande de abdômen luminoso | Percorre trilhas fixas em volta de blocos e ilumina áreas escuras. Fere ao toque | Objeto arremessado | Voador de trilho (Fuzzy) com função de luz | `flyer` |
| **Guardião-de-casca** | Bípede de casca de árvore, escudo de folha larga na frente | Imune pela frente e vira devagar. O 1º pisão arranca o escudo, que ele corre para recuperar | Pisão por cima ou por trás; pegar o escudo antes dele | Guardião resistente (Chargin' Chuck / Koopa do SMW que volta ao casco) | `armored` |

**Chefe — Anciã-Raiz (A Árvore Ancestral).** *Arena:* clareira com plataformas de raízes sob um dossel. *Ataques:* (1) raízes que irrompem em sequência, com o chão inchando 0,6 s antes; (2) bombas de sementes que viram Musgotes; (3) cipós-chicote; (4) fecha o dossel e escurece a arena. *Janela:* depois das raízes, o nó do tronco se abre e brilha → pisão a partir de uma raiz alta. *Fase:* com o dossel fechado, só os Vaga-lumes-vigia iluminam, e as raízes vêm em padrão espelhado. *Derrota:* a árvore floresce e solta uma nuvem de vagalumes.

### 5.6 Cidade Mecânica — autômatos, sentinelas, mecânicos, atiradores, sistemas de segurança

| Nome | Silhueta | Comportamento | Fraqueza | Papel paralelo | Base técnica |
|---|---|---|---|---|---|
| **Latoeiro** | Autômato de lata, chave de corda nas costas | Anda até a corda acabar (a chave desacelera) e para. Pisado, vira uma lata carregável que solta molas e engrenagens depois de 3 s | Pisão; arremessar a lata | Objeto temporizado (Bob-omb) | `walker` → item |
| **Farolete** | Poste com olho-holofote giratório | Se o jogador entra no feixe, dispara um alarme que fecha portões ou chama Latoeiros. Desliga-se por interruptor ou golpe por trás | Golpe por trás | Sistema de segurança (gerador como o Lakitu + leitura de direção como o Boo) | `shooter` (feixe) |
| **Rebitadeira** | Torreta quadrada de cano curto | O cano recua (aviso) e dispara rebites em linha reta. Não dispara com o jogador encostado. Invulnerável; os rebites são pisáveis | Desviar; pisar no rebite | Canhão e projétil linear (Bill Blaster / Bullet Bill) | `shooter` |
| **Bate-estaca** | Prensa hidráulica com lâmpadas amarela e vermelha | Cai em ciclo fixo ou quando o jogador entra no corredor. Fica 1 s no chão e sobe devagar | Invulnerável; pode-se subir nela | Armadilha de esmagamento com aviso (Thwomp) | novo perigo `moving` |

**Chefe — Relojoeiro-Colosso.** *Arena:* torre de relógio com esteiras, engrenagens e um pêndulo ao fundo. *Ataques:* (1) pêndulo que varre a arena, com o tique-taque acelerando antes; (2) rajada de rebites saindo dos ponteiros; (3) inversão das esteiras; (4) solta Latoeiros. *Janela:* a cada "hora" (badalada e luz), a porta do cuco abre e mostra a mola luminosa. *Fase:* as engrenagens giram duas vezes mais rápido e as esteiras invertem a cada badalada. *Derrota:* os ponteiros param à meia-noite e o colosso se desmonta peça por peça.

### 5.7 Arquipélago Celeste — voadores, usuários de vento, travessia de plataformas, guardiões aéreos

| Nome | Silhueta | Comportamento | Fraqueza | Papel paralelo | Base técnica |
|---|---|---|---|---|---|
| **Pipa-bico** | Ave em forma de pipa losangular, cauda de fitas | Plana em ondas regulares. Pisada, perde as fitas e passa a descer em linha reta | 2 pisões | Voador de trajetória legível (Koopa Paratroopa) | `flyer` |
| **Fole-nuvem** | Nuvem bochechuda presa a um poste | Inspira (incha por 1 s) e solta uma rajada horizontal que empurra jogador e inimigos. A rajada é visível em traços e folhas | Pisão quando inflada (estoura); fogo | Usuário de vento (o vento do NSMB Wii é ambiental; sem inimigo paralelo direto) | `shooter` (empurrão) |
| **Arraia-balsa** | Arraia larga e chata que flutua | Cruza o vão entre ilhas em rota fixa e serve de plataforma. Pisada duas vezes, inclina e derruba quem estiver em cima | Não é derrotável (é transporte) | Voador que vira plataforma (Para-Beetle) | plataforma `moving` |
| **Gavião-sentinela** | Gavião de asas longas | Circula alto e crava em diagonal quando o jogador salta acima de certa altura (a sombra no chão avisa). Depois pousa por 1 s | Pisão no pouso | Guardião aéreo de mergulho (Swoop / Condart) | `flyer` |

**Chefe — Grifo-Ventania.** *Arena:* três ilhas flutuantes que derivam devagar. *Ataques:* (1) rajada que empurra para fora das ilhas, com folhas mostrando a direção; (2) mergulho diagonal marcado pela sombra; (3) leque de penas; (4) redemoinho que puxa o jogador para o centro. *Janela:* depois do mergulho, pousa e dobra as asas, e a crista brilha. *Fase:* o vento troca de lado a cada ataque e as ilhas derivam mais rápido. *Derrota:* solta uma chuva de penas douradas e plana para fora da tela.

### 5.8 Pântano Assombrado — furtivos, fantasmas originais, aparecer e sumir, reação à luz

| Nome | Silhueta | Comportamento | Fraqueza | Papel paralelo | Base técnica |
|---|---|---|---|---|---|
| **Névoa-viva** | Névoa de contorno irregular com dois olhos ocos | Só se move fora da luz. Iluminada por lanterna, fogo ou vagalume, congela e fica semissólida por alguns segundos, servindo de plataforma | Luz contínua a dissolve | Fantasma que reage a um gatilho (Boo; aqui a luz, não o olhar) | `flyer` |
| **Fogo-fátuo** | Chama azul sem rosto, com uma faísca orbitando | Some e reaparece sobre nenúfares e solta uma faísca lenta ao reaparecer. Faz três aparições e pausa | Pisão ou golpe no quadro em que está materializado | Aparece e some atirando (Magikoopa) | `shooter` |
| **Jacaré-tronco** | Tronco podre flutuante com dois olhos | Parece plataforma. Se o jogador fica parado sobre ele por mais de 1 s, bolhas sobem e ele afunda e morde | Pisão no focinho quando emerge | Furtivo, emboscada temporal (Piranha Plant / Smackerel) | plataforma + `walker` |
| **Sombra-rastejante** | Mancha de sombra no chão, com borda tremulante | Fora da luz, segue a sombra do jogador e fere. Sob luz, vira uma poça sólida que pode ser pisada e dissolvida | Luz + pisão | Furtivo que reage à luz (escuridão do NSMB Wii e do Wonder) | `walker` |

**Chefe — Dama-Névoa.** *Arena:* pântano com quatro lanternas apagadas sobre tocos e água escura. *Ataques:* (1) some e reaparece, com ondulações na água 1 s antes; (2) mãos de névoa saem da água em sequência; (3) sopro que apaga lanternas; (4) enxame de Fogos-fátuos. *Janela:* com as quatro lanternas acesas (por toque ou fogo), ela se solidifica e mostra o coração luminoso. *Fase:* apaga uma lanterna a cada 6 s e as mãos passam a sair em pares. *Derrota:* dissolve-se na luz do amanhecer.

### 5.9 Fortaleza Vulcânica — resistentes ao fogo, blindados, sentinelas, ligados à lava

| Nome | Silhueta | Comportamento | Fraqueza | Papel paralelo | Base técnica |
|---|---|---|---|---|---|
| **Salamandra-magma** | Salamandra de dorso incandescente | Salta da lava em arcos fixos e solta brasas. Fora da lava, esfria e fica cinza e pisável por 1 s | Pisão no estado frio | Perigo ligado à lava (Podoboo), com janela acrescentada | `flyer` (arco) |
| **Tatu-basalto** | Tatu de placas de basalto | Imune a fogo. Pisado, vira uma pedra quente que não pode ser carregada até esfriar (a cor avisa). Depois vira bola chutável | Pisão + espera; casco | Blindado imune a fogo (Buzzy Beetle) | `armored` → `shell` |
| **Forno-vigia** | Fole de pedra nas paredes com um "olho" de brasa | Solta colunas de chama em três tempos (inspira, pausa, sopra). A cor do olho mostra a fase. Invulnerável | Desviar | Sentinela de fortaleza (Fire Bar / queimadores) | perigo novo |
| **Cinzento** | Figura de cinza compactada | Desmorona ao ser pisado e se recompõe em ~4 s, com brilho vermelho de aviso. Água, gelo ou casco espalham as cinzas de vez | Casco; frio | Derrota temporária (Dry Bones) | `walker` (estado "ruína") |

**Chefe — Forjador-de-Magma (A Última Chama).** *Arena:* ponte de basalto sobre lava, com plataformas que afundam. *Ataques:* (1) martelada que levanta ondas de lava nas bordas; (2) chuva de brasas marcada por sombras; (3) gêiseres em sequência; (4) investida que arrasta o martelo e solta faíscas. *Janela:* o martelo esfria e prende na ponte, e o respiradouro do peito abre, luminoso. *Fase:* a lava sobe, duas plataformas afundam e as marteladas passam a ser duplas. *Derrota:* esfria até virar obsidiana, racha e libera a última chama.

### 5.10 Cidadela das Estrelas — variantes avançadas, combinações, guardiões de elite

| Nome | Silhueta | Comportamento | Fraqueza | Papel paralelo | Base técnica |
|---|---|---|---|---|---|
| **Musgote-estelar** | Musgote com coroa de cristal | Pisado, divide-se em dois Musgotes pequenos e rápidos | 3 pisões no total | Variante que se divide (Big e Hefty Goomba) | `walker` |
| **Rolim-cometa** | Rolim de placas cristalinas com cauda de luz | Chutado, faz uma curva leve em direção ao inimigo mais próximo, ou ao jogador se não houver nenhum. A cauda indica o alvo | Pisão; cuidado com o ricochete | Casco que persegue (Koopa amarelo / Missile Bill) | `shell` |
| **Farolete-rebite** | Farolete com cano acoplado | Dispara rebites só na direção do feixe | Golpe por trás | Combinação de sentinela e atirador | `shooter` |
| **Arauto-de-cristal** | Bípede de elite com escudo de cristal | Salta entre plataformas e arremessa estrelas em arco. Exige 3 pisões, com 1 s de invulnerabilidade entre eles, e muda de padrão depois de cada um | 3 pisões | Guardião de elite (Hammer Bro + Chargin' Chuck) | `armored` |

**Chefe final — Eclipse, Devorador do Lume.** *Arena:* anel estelar que muda de "estação" a cada fase. *Ataques:* fase 1 junta rolagem, areia movediça subindo e corrente (mundos 1–3); fase 2 junta piso de gelo, raízes e esteiras invertidas (mundos 4–6); fase 3 junta vento alternado, escuridão com lanternas e lava subindo (mundos 7–9). *Janela:* no fim de cada sequência, o núcleo (uma estrela apagada) fica exposto com a abertura luminosa: 2 golpes por fase, 6 no total. *Mudança:* a combinação muda a cada 2 golpes, e nos dois últimos o núcleo se move. *Derrota:* a estrela reacende e a criatura se desfaz numa constelação.


### 5.11 Relação com o registro existente (`lume/data/enemies.json`)

Enquanto esta pesquisa era feita, o repositório passou a ter um registro de **61 espécies** para os 10 mundos (`lume/data/enemies.json`, com o campo `role_reference`) e uma campanha de 10 mundos × 6 fases (`lume/data/campaign.json`). As propostas acima **não substituem** esse registro. Use-as assim:

- **Mesmo papel que uma espécie já registrada:** fique com o id existente e aproveite daqui só as regras (aviso, regra justa, janela).
- **Papel que falta no registro:** a proposta entra como espécie nova.

| Mundo | Já registrado (ids) | Propostas que se sobrepõem (usar o id existente) | Propostas que preenchem lacunas |
|---|---|---|---|
| Reino Verde | `bolota`, `caramujo`, `besouro_alado`/`besouro`, `flor_mordedora`, `ourico_espinho`; chefes `guardiao_pomar`, `javali_espinheiro` | Musgote → `bolota`; Rolim → `caramujo`; Sinoreira → `flor_mordedora` (aproveitar a regra de não emergir com o jogador encostado); Pulapólen → `besouro_alado` | O Javali Espinheiro já segue o padrão pesquisado (anuncia a investida, bate na parede, fica atordoado). O Grão-Rolim fica como alternativa |
| Deserto Dourado | `escaravelho_areia`, `tatu_bola`, `cacto_sentinela`, `abutre_filhote`, `escorpiao_couraca`, `serpente_duna`, `escaravelho_lancador` | Minhocão → `serpente_duna`; Mandacaru → `cacto_sentinela` | Escaravelho-brasa (alterna pisável e "quente"), Feneco-miragem (areia movediça), chefe Rainha-Ampulheta |
| Costa dos Corais | `caranguejo_pinca`, `peixe_saltador`, `baiacu_espinho`, `moreia_toca`, `agua_viva`, `polvo_tinteiro` | Medusa-lanterna → `agua_viva` | Ermitão-jato (correnteza), Sapo-maré (anfíbio), Agulhão-flecha (bico preso como janela), chefe Rei-Concha |
| Montanhas Geladas | `pinguim_patrulha`, `caracol_cristal`, `coruja_nevada`, `boneco_neve`, `carneiro_glacial`, `yeti_mirim`, `pingente_queda` | Coruja-geada → `coruja_nevada`; Lontra-trenó → `pinguim_patrulha` (ver riscos) | Lesma-geleira (modifica o piso), Nevoso-rolante, chefe Morsa-Nevasca |
| Floresta Encantada | `cogumelo_saltitante`, `caracol_musgo`, `mariposa_lume`, `planta_esporos`, `besouro_casca`, `arbusto_espreita`, `aranha_cipo` | Toco-dorminhoco → `arbusto_espreita`; Guardião-de-casca → `besouro_casca` | Cipó-chicote, Vaga-lume-vigia (trilho + luz), chefe Anciã-Raiz |
| Cidade Mecânica | `robo_patrulha`, `sentinela_canhao`, `drone_vigia`, `prensa_vapor`, `torreta_arco` | Rebitadeira → `sentinela_canhao`; Bate-estaca → `prensa_vapor` | Farolete (segurança), Latoeiro (objeto temporizado), chefe Relojoeiro-Colosso |
| Arquipélago Celeste | `nuvem_marota`, `semente_espinho`, `passaro_rajada`, `balao_espinho` | Gavião-sentinela → `passaro_rajada` | Fole-nuvem (vento), Arraia-balsa (plataforma viva), Pipa-bico, chefe Grifo-Ventania |
| Pântano Assombrado | `assombracao_timida`, `sapo_lodo`, `mao_lodo`, `ossada_pantano` | Jacaré-tronco → `mao_lodo` | Névoa-viva e Sombra-rastejante (luz), Fogo-fátuo, chefe Dama-Névoa |
| Fortaleza Vulcânica | `brasa_andante`, `tartaruga_basalto`, `boca_fornalha`, `golem_basalto`, `morcego_brasa`, `bolha_magma` | Forno-vigia → `boca_fornalha`; Salamandra-magma → `bolha_magma`; Tatu-basalto → variante de `tatu_bola` | Cinzento (regenera), chefe Forjador-de-Magma |
| Cidadela das Estrelas | `sentinela_estelar`, `cometa_errante`, `guardiao_constelacao` | — | Variantes de elite feitas a partir dos ids existentes (por exemplo, uma Bolota que se divide no lugar do Musgote-estelar), chefe Eclipse |

**Riscos de semelhança no registro atual** (Observação; recomendação = Decisão do projeto):

| Espécie registrada | Paralelo oficial | Risco | Motivo | Recomendação |
|---|---|---|---|---|
| `bolha_magma` (Bolha de Magma) | Lava Bubble / Podoboo [E38] | **Alto** | O nome é praticamente a tradução de "Lava Bubble", e o comportamento é o mesmo (salta da lava em ritmo fixo) | Renomear e dar uma janela própria, como a fase "fria" da Salamandra-magma |
| `tartaruga_basalto` (Tartaruga-Basalto) | Koopa Troopa [E19] | **Alto** | Tartaruga com casco chutável é a combinação de espécie e papel do Koopa | Trocar o animal (por exemplo, variante basáltica de `tatu_bola`) |
| `assombracao_timida` (Assombração Tímida) | Boo [E23] | **Alto** | Repete a mecânica-assinatura: aproxima-se pelas costas, cobre o rosto quando encarada, atravessa paredes | Mudar o gatilho para luz (como a Névoa-viva) ou a reação (congelar e virar plataforma) |
| `pinguim_patrulha` (Pinguim Patrulheiro) | Cooligan [E48] | Médio | O Cooligan é uma criatura parecida com pinguim que desliza de barriga | Evitar óculos escuros e a paleta azul e branca, ou trocar por lontra |
| `polvo_tinteiro` (Polvo-Tinteiro) | Blooper [E37] | Médio | Cefalópode que persegue nadando em impulsos | Mudar o padrão de movimento ou trocar de animal |
| `baiacu_espinho` (Baiacu-Espinho) | Porcupuffer [E47] | Médio | Baiacu espinhoso aquático | Manter a regra própria (pisável quando murcho) e diferenciar a silhueta |
| `cogumelo_saltitante` (Cogumelo Saltitante) | Goomba, criado com aparência de cogumelo [E18] | Médio | Inimigo-cogumelo evoca o Goomba | Não usar chapéu de cogumelo com pés; preferir outro fungo ou silhueta de salto |
| `ossada_pantano`, `nuvem_marota` + `semente_espinho` | Dry Bones; Lakitu e Spiny [E32][E29][E30] | Baixo | Só o papel coincide | Evitar esqueleto de tartaruga e "cavaleiro" em nuvem |

---

## 6. Limitações desta pesquisa

- Os valores de velocidade só existem para SMB, SMB3 e SMW, lidos nas desmontagens comunitárias. Para NSMB, NSMB Wii, NSMBU e Wonder não há dado técnico consultado. As menções a velocidade nesses jogos são qualitativas ou **não verificado**.
- As conversões em segundos supõem cerca de 60 quadros/s (NTSC) e são **Estimativas**.
- Data Crystal, The Cutting Room Floor, Iwata Asks e The Guardian recusaram acesso (403, 503 ou bloqueio) em 03/11/2026. Os dados equivalentes vieram de fontes de mesma natureza ou de reproduções, como indicado em cada citação.
- Sons foram descritos a partir de nomes de efeitos no código e de descrições da wiki. Nenhum áudio foi analisado.

---

## Referências

### Oficial Nintendo e entrevistas de desenvolvedor

- **[E1]** Nintendo — *Iwata Asks: New Super Mario Bros. Wii*, trecho sobre o Goomba ensinar o pisão (Miyamoto, Iwata). https://iwataasks.nintendo.com/interviews/wii/nsmb/1/4/ — **entrevista de desenvolvedor (oficial Nintendo)**. O acesso direto deu HTTP 503 em 03/11/2026; o conteúdo foi conferido via [E3].
- **[E2]** Nintendo — *Iwata Asks: New Super Mario Bros. Wii*, trecho sobre a criação tardia do Goomba (Tezuka, Iwata, Nakago). https://iwataasks.nintendo.com/interviews/wii/nsmb/1/5/ — **entrevista de desenvolvedor (oficial Nintendo)**. Mesma observação de acesso; [E3] identifica o trecho como "Vol. 2".
- **[E3]** GoNintendo — reproduções de trechos do Iwata Asks (2009). https://www.gonintendo.com/archives/102481-goombas-the-walking-shiitake-mushrooms-was-created-at-the-very-end-of-super-mario e https://gonintendo.com/archives/100477-miyamoto-explains-how-the-player-is-taught-that-goombas-are-bad-and-mushrooms-are — **análise de terceiros (reprodução de imprensa)**.
- **[E4]** Nintendo — *Ask the Developer Vol. 11, Super Mario Bros. Wonder*, Parte 1. https://www.nintendo.com/ph/interview/aqmx/index.html — **oficial Nintendo / entrevista de desenvolvedor**.
- **[E5]** Nintendo — *Ask the Developer Vol. 11, Super Mario Bros. Wonder*, Parte 2. https://www.nintendo.com/us/whatsnew/ask-the-developer-vol-11-super-mario-bros-wonder-part-2/ — **oficial Nintendo / entrevista de desenvolvedor**.
- **[E6]** Nintendo — *Ask the Developer Vol. 11, Super Mario Bros. Wonder*, Parte 3. https://www.nintendo.com/us/whatsnew/ask-the-developer-vol-11-super-mario-bros-wonder-part-3/ — **oficial Nintendo / entrevista de desenvolvedor**.
- **[E7]** Nintendo UK — *Nintendo Classic Mini: NES special interview Vol. 3 — Super Mario Bros.* (2016). https://www.nintendo.com/en-gb/News/2016/November/Nintendo-Classic-Mini-NES-special-interview-Volume-3-Super-Mario-Bros-1157085.html — **oficial Nintendo / entrevista de desenvolvedor**.
- **[E8]** Nintendo UK — *Nintendo Classic Mini: SNES developer interview Vol. 5 — Super Mario World & Yoshi's Island* (2017). https://www.nintendo.com/en-gb/News/2017/October/Nintendo-Classic-Mini-SNES-developer-interview-Volume-5-Super-Mario-World-and-Super-Mario-World-2-Yoshi-s-Island-1290850.html — **oficial Nintendo / entrevista de desenvolvedor**.
- **[E9]** C. Nutt, "The secret to Mario level design", Game Developer (Gamasutra), 13/04/2012, entrevista com Koichi Hayashida. https://www.gamedeveloper.com/design/the-secret-to-i-mario-i-level-design — **entrevista de desenvolvedor (publicada por terceiros)**.
- **[E10]** C. Kerr, "How Miyamoto built Super Mario Bros.' legendary World 1-1", Game Developer, 08/09/2015, resumo do vídeo da Eurogamer de 07/09/2015. https://gamedeveloper.com/design/how-miyamoto-built-i-super-mario-bros-i-legendary-world-1-1 — **entrevista de desenvolvedor (via terceiros)**.

### Documentação técnica comunitária

- **[E11]** doppelganger, *SMBDIS.ASM — A comprehensive Super Mario Bros. disassembly*. https://gist.github.com/1wErt3r/4048722 — **documentação técnica comunitária**.
- **[E12]** IsoFrieze (Dotsarecool), *SMWDisX — Super Mario World disassembly*, `bank_01.asm`. https://github.com/IsoFrieze/SMWDisX — **documentação técnica comunitária**.
- **[E13]** captainsouthbird, *Super Mario Bros. 3 disassembly* (`smb3.asm`, `PRG/prg000.asm`, `prg002.asm`, `prg004.asm`). https://github.com/captainsouthbird/smb3 — **documentação técnica comunitária**.
- **[E14]** TASVideos — *Game Resources: NES Super Mario Bros.* https://tasvideos.org/GameResources/NES/SuperMarioBros — **documentação técnica comunitária (TASVideos)**.
- **[E15]** TASVideos — *Game Resources: SNES Super Mario World*. https://tasvideos.org/GameResources/SNES/SuperMarioWorld — **documentação técnica comunitária (TASVideos)**.
- **[E16]** Data Crystal — *Super Mario Bros./RAM map*. https://datacrystal.tcrf.net/wiki/Super_Mario_Bros./RAM_map — **documentação técnica comunitária (Data Crystal)**. Acesso recusado (HTTP 403); não foi usado como fonte de dados.
- **[E17]** The Cutting Room Floor — *Super Mario World (SNES)*. https://tcrf.net/Super_Mario_World_(SNES) — **documentação técnica comunitária (TCRF)**. Acesso recusado (HTTP 403); citado apenas indiretamente por [E35].

### Wiki de fãs (Super Mario Wiki) — inimigos

Todas em https://www.mariowiki.com/ (consultadas em 03/11/2026) — **wiki de fãs**.

- [E18] Goomba — https://www.mariowiki.com/Goomba
- [E19] Koopa Troopa — https://www.mariowiki.com/Koopa_Troopa
- [E20] Koopa Paratroopa — https://www.mariowiki.com/Koopa_Paratroopa
- [E21] Piranha Plant — https://www.mariowiki.com/Piranha_Plant
- [E22] Fire Piranha Plant (Venus Fire Trap) — https://www.mariowiki.com/Fire_Piranha_Plant
- [E23] Boo — https://www.mariowiki.com/Boo
- [E24] Shy Guy — https://www.mariowiki.com/Shy_Guy
- [E25] Hammer Bro — https://www.mariowiki.com/Hammer_Bro
- [E26] Bullet Bill — https://www.mariowiki.com/Bullet_Bill
- [E27] Bill Blaster — https://www.mariowiki.com/Bill_Blaster
- [E28] Bob-omb — https://www.mariowiki.com/Bob-omb
- [E29] Lakitu — https://www.mariowiki.com/Lakitu
- [E30] Spiny — https://www.mariowiki.com/Spiny
- [E31] Thwomp — https://www.mariowiki.com/Thwomp
- [E32] Dry Bones — https://www.mariowiki.com/Dry_Bones
- [E33] Cheep Cheep — https://www.mariowiki.com/Cheep_Cheep
- [E34] Buzzy Beetle — https://www.mariowiki.com/Buzzy_Beetle
- [E35] Chain Chomp — https://www.mariowiki.com/Chain_Chomp
- [E36] Pokey — https://www.mariowiki.com/Pokey
- [E37] Blooper — https://www.mariowiki.com/Blooper
- [E38] Lava Bubble — https://www.mariowiki.com/Lava_Bubble
- [E39] Fire Bar — https://www.mariowiki.com/Fire_Bar
- [E40] Roto-Disc — https://www.mariowiki.com/Roto-Disc
- [E41] Monty Mole — https://www.mariowiki.com/Monty_Mole
- [E42] Wiggler — https://www.mariowiki.com/Wiggler
- [E43] Rex — https://www.mariowiki.com/Rex
- [E44] Chargin' Chuck — https://www.mariowiki.com/Chargin%27_Chuck
- [E45] Fuzzy — https://www.mariowiki.com/Fuzzy
- [E46] Urchin — https://www.mariowiki.com/Urchin
- [E47] Porcupuffer — https://www.mariowiki.com/Porcupuffer
- [E48] Cooligan — https://www.mariowiki.com/Cooligan
- [E49] Bramball — https://www.mariowiki.com/Bramball
- [E50] Spike — https://www.mariowiki.com/Spike
- [E51] Swoop — https://www.mariowiki.com/Swoop
- [E52] Magikoopa — https://www.mariowiki.com/Magikoopa
- [E53] Hoppycat — https://www.mariowiki.com/Hoppycat
- [E54] Bulrush — https://www.mariowiki.com/Bulrush
- [E55] Maw-Maw — https://www.mariowiki.com/Maw-Maw
- [E56] Condart — https://www.mariowiki.com/Condart
- [E57] Konk — https://www.mariowiki.com/Konk
- [E58] Rrrumba — https://www.mariowiki.com/Rrrumba
- [E59] Smackerel — https://www.mariowiki.com/Smackerel

### Wiki de fãs (Super Mario Wiki) — chefes, jogos e elementos

- [E60] Koopalings — https://www.mariowiki.com/Koopalings
- [E61] Boom Boom — https://www.mariowiki.com/Boom_Boom
- [E62] Reznor — https://www.mariowiki.com/Reznor
- [E63] Bowser Jr. — https://www.mariowiki.com/Bowser_Jr.
- [E64] History of Bowser — https://www.mariowiki.com/History_of_Bowser
- [E65] Big Boo — https://www.mariowiki.com/Big_Boo
- [E66] Larry — https://www.mariowiki.com/Larry
- [E67] Iggy — https://www.mariowiki.com/Iggy
- [E68] Super Mario Bros. — https://www.mariowiki.com/Super_Mario_Bros.
- [E69] Super Mario Bros. 3 — https://www.mariowiki.com/Super_Mario_Bros._3
- [E70] Super Mario World — https://www.mariowiki.com/Super_Mario_World
- [E71] New Super Mario Bros. — https://www.mariowiki.com/New_Super_Mario_Bros.
- [E72] New Super Mario Bros. Wii — https://www.mariowiki.com/New_Super_Mario_Bros._Wii
- [E73] New Super Mario Bros. U — https://www.mariowiki.com/New_Super_Mario_Bros._U
- [E74] Super Mario Bros. Wonder — https://www.mariowiki.com/Super_Mario_Bros._Wonder
- [E75] Super Mario Bros. Wonder – Nintendo Switch 2 Edition + Meetup in Bellabel Park — https://www.mariowiki.com/Super_Mario_Bros._Wonder_%E2%80%93_Nintendo_Switch_2_Edition_%2B_Meetup_in_Bellabel_Park
- [E76] Door — https://www.mariowiki.com/Door
- [E77] Páginas de fase: World 1-1, 1-2, 4-1 e 8-1 (SMB); World 1-1 (SMB3); World 1-1 e 8-1 (NSMB Wii). https://www.mariowiki.com/World_1-1_(Super_Mario_Bros.) · https://www.mariowiki.com/World_1-2_(Super_Mario_Bros.) · https://www.mariowiki.com/World_4-1_(Super_Mario_Bros.) · https://www.mariowiki.com/World_8-1_(Super_Mario_Bros.) · https://www.mariowiki.com/World_1-1_(Super_Mario_Bros._3) · https://www.mariowiki.com/World_1-1_(New_Super_Mario_Bros._Wii) · https://www.mariowiki.com/World_8-1_(New_Super_Mario_Bros._Wii)
- [E78] Bowser (seção de temas musicais) — https://www.mariowiki.com/Bowser
- [E79] Airship — https://www.mariowiki.com/Airship
- [E83] Poison (obstacle) — https://www.mariowiki.com/Poison_(obstacle)
- [E84] Ghost House — https://www.mariowiki.com/Ghost_House
- [E85] Water tide — https://www.mariowiki.com/Water_tide
- [E86] Dark — https://www.mariowiki.com/Dark
- [E87] Sledge Bro — https://www.mariowiki.com/Sledge_Bro

### Análise de terceiros

- **[E80]** K. Stuart, "Super Mario Bros: 25 Mario facts for the 25th anniversary", *The Guardian*, 13/09/2010. https://www.theguardian.com/technology/gamesblog/2010/sep/13/games-gameculture — **análise de terceiros**. Não acessada (bloqueio de acesso automatizado); citada via [E23] e [E35].
- **[E81]** *Nintendo Power* nº 80, jan. 1996, p. 25 (revista da Nintendo of America). https://archive.org/stream/Nintendo_Power_Issue001-Issue127/Nintendo%20Power%20Issue%20080%20January%201996 — **oficial Nintendo (revista)**. Não verificada diretamente; citada via [E23].
- **[E82]** A. Wawro, "Have a look at Nintendo's early prototype for Yoshi", Gamasutra, 28/09/2017. https://www.gamasutra.com/view/news/306745/Have_a_look_at_Nintendos_early_prototype_for_Yoshi.php — **análise de terceiros**. Não acessada; citada pela página [E35] sobre o Chain Chomp previsto para o SMW.

### Fontes internas do projeto (sem URL pública)

- `README.md` (física, poderes e guardiões); `src/core/game.ts` (caminhada 220 px/s, corrida 340 px/s); `src/core/enemies.ts` (velocidades de inimigos e casco; atirador a cada 2,2 s); `src/core/bosses.ts` (janela de 1,65 s e 1,1 s; guardiões mais rápidos na metade da vida); `src/core/types.ts` (tipos `EnemyKind`); `src/data/levels.ts` (2 a 5 inimigos por fase hoje); `lume/data/enemies.json` (61 espécies com `role_reference`); `lume/data/campaign.json` (10 mundos × 6 fases).
