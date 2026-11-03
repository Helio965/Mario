# Movimentação horizontal nos Mario 2D — engenharia reversa comportamental

Documento de pesquisa do projeto **Lume — As Cinco Fronteiras** (jogo original, não oficial, sem assets Nintendo).
Objetivo: entender **como** os sete títulos oficiais de Mario 2D tratam velocidade de caminhada/corrida, aceleração,
desaceleração, atrito, inércia, derrapagem (skid), controle no ar, gelo, vento, plataformas móveis e recuperação após dano,
para calibrar um modelo de movimentação **coerente e original** no motor Python 3.12 + pygame-ce 2.5.8.

Títulos cobertos: Super Mario Bros. (SMB1, NES 1985), Super Mario Bros. 3 (SMB3, NES 1988), Super Mario World (SMW, SNES 1990),
New Super Mario Bros. (NSMB, DS 2006), New Super Mario Bros. Wii (NSMBW, 2009), New Super Mario Bros. U (NSMBU, 2012) e
Super Mario Bros. Wonder (SMBW, Switch 2023).

## 0. Como ler este documento

| Etiqueta | Significado |
|---|---|
| **OFICIAL** | Dito pela Nintendo ou por seus desenvolvedores (Iwata Asks, Ask the Developer, texto do jogo citado por fonte secundária). |
| **DOCUMENTADO** | Artigo técnico, wiki ou recurso comunitário com valor verificável. Valores obtidos por análise de terceiros (RAM watch, desmontagem) são **documentação comunitária (derivada de análise de terceiros)**, nunca "valores oficiais". |
| **OBSERVADO** | Comportamento descrito a partir de gameplay/vídeo/notas de speedrun, sem valor numérico confirmado. |
| **ESTIMADO** | Inferência nossa (interpolação, conversão com hipótese, escolha de design). Nunca apresentado como oficial. |

Propriedade intelectual: nenhuma ROM, sprite, música ou código proprietário foi extraído. Os números do NES/SNES vêm de páginas
públicas da comunidade (TASVideos, Data Crystal, SMBPedia, desmontagem comentada publicada em HTML) e são citados apenas como
constantes de comportamento, para calibrar um modelo **próprio**.

## 1. Resumo executivo

1. Todos os Mario 2D clássicos têm **duas velocidades de chão (andar/correr)** e, a partir de SMB3, uma **terceira camada "P"**
   (sprint) alcançada só depois de correr continuamente. A ideia das duas velocidades está na especificação original de 1985:
   "Press the D-pad left and right to control Mario at two speeds" (OFICIAL, Iwata Asks 25º aniversário, Vol. 5 §1).
2. SMB1 (DOCUMENTADO/comunitário): andar 1,5 px/quadro (90 px/s), correr 2,5 px/quadro (150 px/s); acelerações de
   0,037–0,056 px/quadro² (134–200 px/s²); derrapagem = **dobro** do atrito; vira de lado só quando |v| < 11/16 px/quadro.
3. SMB3 (DOCUMENTADO): andar 24, correr 40, P-speed 56 (1,5 / 2,5 / 3,5 px/quadro); aceleração ≈ 1/16 px/quadro² com
   "regra do 8º quadro"; P-meter sobe uma seta a cada 8 quadros a 2,5 px/quadro e perde uma a cada 24 quadros.
4. SMW (DOCUMENTADO): correr oscila 35–37 e sprint 47–49 (≈ 2,25 e 3,0 px/quadro); acelera em média 1,5/16 px/quadro²
   (sequência 0,1,3,4,6,7,9…); "desacelera mais rápido do que acelera"; P-meter 0→112 em passos de 2 (≈ 56 quadros).
5. NSMB DS / NSMBW (DOCUMENTADO): velocidade de corrida plena **3,0 px/quadro** (180 px/s); casco azul 2,75; estrela 4,0–4,5;
   pinguim 4,0; plataformas "tipo chão" transferem velocidade ao pulo, plataformas de trilho não.
6. NSMBU: sem números públicos; mesma família de motor "New" (ESTIMADO). SMBW: motor novo (OFICIAL), movimento "notavelmente
   parecido com NSMBU" com inércia entre SMW e SMB3 (OBSERVADO, Digital Foundry via Nintendo Life).
7. No ar, SMB1 **não aplica atrito sem entrada** (velocidade preservada) e permite acelerar até a velocidade de corrida sem B
   se |v| ≥ 25/16 px/quadro (DOCUMENTADO).
8. Dano: em SMB1 o personagem encolhe, pisca por 8 × 21 quadros ≈ 2,8 s e **não há empurrão** (DOCUMENTADO); nos demais o padrão
   "sem knockback, com invencibilidade temporária" é OBSERVADO.
9. Gelo: SMB3 traz um "fator de atrito" por fase (DOCUMENTADO), SMW tem fases escorregadias onde a aceleração muda (DOCUMENTADO),
   NSMBW/NSMBU/SMBW aplicam gelo por trecho; SMBW avisa "You can't stop quickly on frozen surfaces" (OFICIAL via MarioWiki).
10. Para o Lume: manter 220/340 px/s como teto, **reduzir a aceleração de chão (1400 → 700–800 px/s²)**, criar estado de
    derrapagem com desaceleração dobrada (SMB1), remover o atrito aéreo sem entrada (SMB1), remover o knockback ao sofrer dano e
    adicionar gelo/vento/sprint como parâmetros opcionais. Detalhes na §13.

## 2. Unidades e conversões

**NES e SNES (SMB1, SMB3, SMW).** Posição = pixel + subpixel; **16 subpixels = 1 pixel**. A velocidade é armazenada em
"subpixels por quadro": valor 16 = 1 px/quadro; valor 40 = 2,5 px/quadro ([TASVideos SMB3](https://tasvideos.org/GameResources/NES/SuperMarioBros3),
[TASVideos SMW](https://tasvideos.org/GameResources/SNES/SuperMarioWorld), [TASVideos SMB1](https://tasvideos.org/GameResources/NES/SuperMarioBros)).
Em SMB1 a aceleração é acumulada num byte fracionário (`Player_X_MoveForce`): o valor de atrito/aceleração é somado a esse byte
a cada quadro e o "vai-um" incrementa a velocidade em 1 unidade ([SMBPedia](https://simplistic6502.github.io/smb1_tll/smbpedia_movement.html);
[desmontagem comentada em HTML](https://6502disassembly.com/nes-smb/SuperMarioBros.html)). Logo:

- velocidade (px/quadro) = unidades / 16; velocidade (px/s a 60 Hz) = unidades × 60 / 16 = unidades × 3,75;
- aceleração (px/quadro²) = valor / (256 × 16) = valor / 4096; aceleração (px/s²) = valor / 4096 × 3600.

**DS/Wii.** NSMB usa ponto fixo 20.12 (TASVideos) e a comunidade já expressa as velocidades em px/quadro (3,0 = "3 speed").

**Escala para o Lume.** Mario pequeno mede 16 px; o jogador pequeno do Lume mede 22 × 30 px, ou seja **1,875×** a altura.
Para comparar "sensação" usamos também **alturas de personagem por segundo (h/s)**: SMB1 anda a 5,6 h/s e corre a 9,4 h/s;
o Lume hoje anda a 7,3 h/s e corre a 11,3 h/s.

| Valor NES (subpx/quadro) | px/quadro | px/s (60 Hz) | h/s (Mario 16 px) | × 1,875 (px/s, escala Lume) |
|---:|---:|---:|---:|---:|
| 11 (limiar de giro na derrapagem, SMB1) | 0,6875 | 41,25 | 2,6 | 77 |
| 16 (teto no chão da água, SMB1) | 1,00 | 60 | 3,75 | 112,5 |
| 24 (andar SMB1/SMB3) | 1,50 | 90 | 5,6 | 168,75 |
| 36 (correr SMW) | 2,25 | 135 | 8,4 | 253 |
| 40 (correr SMB1/SMB3) | 2,50 | 150 | 9,4 | 281 |
| 48 (sprint P, SMW) | 3,00 | 180 | 11,25 | 337,5 |
| 56 (P-speed SMB3) | 3,50 | 210 | 13,1 | 394 |

## 3. Super Mario Bros. (NES, 1985)

### 3.1 Fontes
Desmontagem comunitária de doppelganger publicada em HTML ([6502disassembly.com](https://6502disassembly.com/nes-smb/SuperMarioBros.html)) e sua
documentação em prosa ([SMBPedia — movement](https://simplistic6502.github.io/smb1_tll/smbpedia_movement.html)), complementadas por
[TASVideos (recursos SMB1)](https://tasvideos.org/GameResources/NES/SuperMarioBros), [texto de submissão TAS](https://tasvideos.org/Forum/Posts/538365),
[análise de física no fórum](https://tasvideos.org/Forum/Posts/467106), [SMB1 Explained](https://negative-seven.github.io/smb1explained/) e
[Data Crystal](https://datacrystal.tcrf.net/wiki/Super_Mario_Bros./Notes). Tudo DOCUMENTADO/comunitário (derivado de análise de terceiros).

### 3.2 Tabelas de velocidade e aceleração (DOCUMENTADO)

| Tabela | Índice 0 | Índice 1 | Índice 2 | (3) |
|---|---:|---:|---:|---:|
| Velocidade máxima (subpx/quadro) | 40 = 2,5 px/q (correr) | 24 = 1,5 px/q (andar / água) | 16 = 1,0 px/q (chão na água) | 12 = 0,75 px/q (entrada de cano) |
| Aceleração/atrito (1/256 subpx por quadro) | 0xE4 = 228 | 0x98 = 152 | 0xD0 = 208 | — |
| → px/quadro² | 0,0557 | 0,0371 | 0,0508 | — |
| → px/s² (60 Hz) | 200,4 | 133,6 | 182,8 | — |
| Dobrado (derrapagem) → px/s² | 400,8 | 267,2 | 365,6 | — |

Seleção dos índices (rotina de física do jogador; descrita em prosa na SMBPedia e visível nos comentários da desmontagem):

| Situação | Teto | Aceleração | Observação |
|---|---|---|---|
| Chão, segurando a direção do movimento **com B** | 40 | 0xE4 (200 px/s²) | arma `RunningTimer` = 10 quadros |
| Chão, mesma direção, **sem B mas com `RunningTimer` > 0** | 40 | 0xE4 | 10 quadros de "graça" após soltar B |
| Chão, mesma direção, sem B, timer zerado, lento (|v| < 33 e flag de corrida limpa) | 24 | 0x98 (134 px/s²) | caminhada |
| Chão, mesma direção, sem B, **rápido** (|v| ≥ 33 ou flag `RunningSpeed`) | 24 | 0xD0 (183 px/s²) | **se v > teto, a velocidade é cravada no teto no mesmo quadro** (soft cap) |
| Chão, direção oposta ou nenhuma | como acima (24) | 0x98 ou 0xD0 | e **dobra** se `PlayerFacingDir ≠ Player_MovingDir` (derrapagem) |
| Ar, |v| ≥ 25 | 40 | 0xE4 | B é irrelevante no ar |
| Ar, |v| < 25 | 24 | 0x98 (ou 0xD0 se a flag de corrida ainda estiver armada) | |
| Água | 24 sempre; 16 no chão | índice +1 | |

Regras adicionais confirmadas na desmontagem/SMBPedia:
- **Sem entrada no ar não há atrito**: a sub-rotina de atrito só é chamada em voo se esquerda/direita estiver pressionada
  (comentário "if not pressing any, skip" em `LRAir`). No chão, sem entrada, o atrito age sempre.
- **Derrapagem (skid)**: ao pressionar a direção oposta no chão, o sprite vira na hora (`PlayerFacingDir` recebe o botão) e a
  desaceleração dobra. Enquanto |v| ≥ 11 o jogo mantém a direção de movimento antiga; quando |v| < 11 (0,69 px/q) a velocidade
  é **zerada** e a direção de movimento passa a ser a do rosto (rotina `ProcSkid`). Com velocidade < 11 e qualquer botão que não
  seja a direção de viagem, velocidade e sub-velocidade zeram (SMBPedia).
- **Soltar tudo no chão**: o atrito desacelera e, por não haver zeragem sem botões, a velocidade oscila ±1 em torno de zero
  ("moonwalk" 1, 255, 1, 255 descrito na página TASVideos). O jogador não percebe porque 1/16 px por quadro não acumula pixel inteiro.
- **Esquerda+Direita**: grava 3 na direção do rosto, força derrapagem perpétua e cai para 1 px/quadro
  ([SMB1 Explained](https://negative-seven.github.io/smb1explained/)); "freia instantaneamente para velocidade de caminhada"
  ([TASVideos](https://tasvideos.org/GameResources/NES/SuperMarioBros)).
- **Acelerar virado para o lado oposto** dobra a aceleração também na direção de ida (truque de TAS) — a flag de direção do rosto
  não muda no ar, então ao inverter a velocidade em voo a aceleração nova vem dobrada ([fórum TASVideos](https://tasvideos.org/Forum/Posts/467106)).
- **Timer de corrida**: 10 quadros (0,167 s) a cada quadro com B no chão; ao soltar B, Mario segue com teto 40 por até 10 quadros
  e só então o teto cai para 24 (SMBPedia).
- **Pulo depende da velocidade horizontal**: limiares 9, 16, 25 e 28 escolhem tabelas de impulso/gravidade (`cmp #$09/$10/$19/$1c`
  na desmontagem; SMBPedia). Por isso "correr antes de um vão" dá salto mais longo e um pouco mais alto.

### 3.3 Animação (DOCUMENTADO)
`PlayerAnimTmrData = {2, 4, 7}`: com |v| ≥ 28 cada quadro da caminhada dura 2 quadros; com |v| ≥ 14, 4 quadros; abaixo, 7 quadros
(ciclo de 3 quadros → 6/12/21 quadros por ciclo). A flag `RunningSpeed` (|v| ≥ 28) é a mesma usada na seleção de atrito.
Tabela de poses do jogador (grande e pequeno): **parado, andando (3 quadros), derrapando, pulando, nadando (3), escalando (2),
agachado, arremesso de bola de fogo**, mais "quadro intermediário de crescimento" ([desmontagem](https://6502disassembly.com/nes-smb/SuperMarioBros.html)).
Não existe pose distinta de "queda" em SMB1 — a pose de pulo serve para subida e descida (ESTIMADO a partir da tabela).

### 3.4 Dano (DOCUMENTADO)
A rotina de ferimento muda o status para pequeno, arma `InjuryTimer = 8` e toca o som; não há escrita na velocidade horizontal
no trecho visível, isto é, **nenhum empurrão**. `InjuryTimer` é um "timer longo" decrementado a cada 21 quadros
([Set Side B — framerules](https://setsideb.com/?p=9145)), logo a invulnerabilidade dura 148–168 quadros (≈ 2,5–2,8 s, variando
em até 1/3 s conforme a fase do ciclo). A TMK descreve "pisca por oito segundos de jogo" ([smb_breakdown](https://themushroomkingdom.net/smb_breakdown.shtml));
a diferença entre "8 unidades de 21 quadros" e "8 segundos do relógio do jogo" fica registrada na §15.

### 3.5 Números derivados (ESTIMADO a partir dos valores DOCUMENTADOS)

| Manobra | Fórmula | Resultado |
|---|---|---|
| 0 → 40 correndo (0xE4) | t = 40 / (228/256) ; d = v²/2a | 44,9 quadros = 0,75 s ; 56 px = 3,5 tiles |
| 0 → 24 andando (0x98) | idem | 40,4 quadros = 0,67 s ; 30 px = 1,9 tiles |
| 40 → 0 soltando (0xD0) | idem | 49 quadros = 0,82 s ; 61,5 px = 3,85 tiles |
| 40 → 11 derrapando (2 × 0xD0) | t = 29 / 1,625 | 17,8 quadros = 0,30 s ; ≈ 28 px |
| 40 → 0 derrapando | idem | 24,6 quadros = 0,41 s ; 31 px |

Conclusão de sensação: SMB1 é **lento para arrancar, escorregadio ao soltar e rápido ao frear com a direção oposta**
(razão derrapagem/soltar = 2,0). Esse "trio" é a assinatura que vale preservar.

## 4. Super Mario Bros. 3 (NES, 1988)

Fontes: [TASVideos — recursos SMB3](https://tasvideos.org/GameResources/NES/SuperMarioBros3) (tabela de tetos; RAM $BD = velocidade),
[Data Crystal — notas](https://datacrystal.tcrf.net/wiki/Super_Mario_Bros._3:Notes) (tetos em hex, P-timer, fator de atrito),
[notas de TAS de narfman0](https://narfman0.github.io/angry-sun/pages/tas-notes.html) (regra do 8º quadro, P-meter),
[fórum TASVideos](https://tasvideos.org/Forum/Posts/476242), [MarioWiki — P-Meter](https://www.mariowiki.com/P_Meter) e
[Iwata Asks NSMBW Vol. 2 §6](https://www.nintendo.com/en-gb/Iwata-Asks/Iwata-Asks-New-Super-Mario-Bros-Wii/Volume-2/6-No-Rest-After-Completing-Super-Mario-Bros-/6-No-Rest-After-Completing-Super-Mario-Bros-233134.html) (OFICIAL).

| Estado (SMB3) | subpx/quadro | px/quadro | px/s | Fonte / confiança |
|---|---:|---:|---:|---|
| Ejeção de parede | 16 | 1,0 | 60 | TASVideos — DOCUMENTADO |
| Andar / nadar | 24 ($18) | 1,5 | 90 | TASVideos, Data Crystal — DOCUMENTADO |
| Correr sem P | 40 ($28) | 2,5 | 150 | idem |
| Correr com P (P-speed) | 56 ($38) | 3,5 | 210 | idem |
| Descida de rampa andando / correndo / P | 26–27 / 42–43 / 58–59 | — | — | narfman0 — DOCUMENTADO |
| Deslizar (agachado em rampa) | 63–64 | ≈ 4,0 | 236–240 | TASVideos, narfman0 — DOCUMENTADO |
| Teto com Esq+Dir (All-Stars) | 64 | 4,0 | 240 | submissão TAS — DOCUMENTADO (glitch) |

Regras:
- **Aceleração** ≈ 1 subpx/quadro por quadro, idêntica para andar, correr e dash (Data Crystal, marcada "TODO" quanto ao valor
  exato), mas **"a cada 8º quadro não é possível aumentar a velocidade"** (narfman0). Efetivo: 7/8 unidade/quadro ≈ 0,0547 px/q²
  ≈ **197 px/s²**; sem a regra seriam 225 px/s². De 0 a 40: ≈ 46 quadros (0,76 s, 57 px); de 40 a 56 com P: ≈ 18 quadros.
- **Desaceleração**: sequência observada 40, 38, 36, 35, 36, 37… (−2/quadro ao perder, +1/quadro ao recuperar) — OBSERVADO
  (narfman0); não está claro se o −2 corresponde a soltar ou a inverter a direção.
- **P-meter**: começa a subir quando |v| ≥ 40 no chão com B; o P-timer "cicla a partir de 7" (8 quadros) e cada ciclo acrescenta
  uma seta (valores 1, 3, 7, 15, 31, 63, 127); fora da condição, um timer de 24 quadros ("cicla a partir de 23") remove uma seta.
  Logo encher leva ≈ 7 × 8 = **56 quadros (0,93 s)**, ou ≈ 140 px (8,75 tiles) a 2,5 px/quadro — coerente com a legenda oficial
  "He needs to run at least eight times the width of his sprite before he can take off" (OFICIAL) e com a "pista de decolagem"
  descrita por Nakago. Esvaziar tudo leva ≈ 7 × 24 = 168 quadros (2,8 s) — ESTIMADO.
- **O que esvazia o P-meter**: agachar, virar-se ou bater na parede; pular correndo mantém cheio (exceto Guaxinim/Tanooki)
  (MarioWiki — DOCUMENTADO). Ao pular com P cheio, um timer de 256 (decrementado a cada 2 quadros) mantém a velocidade 56 no ar
  mesmo com o medidor zerando (narfman0).
- **Impulso de pulo depende da velocidade**: a rotina divide |v| por 16 e subtrai de uma tabela {0, 2, 4, 8} (Data Crystal) —
  mesmo princípio de SMB1.
- **Gelo**: o cabeçalho de cada fase traz um **fator de atrito** (Data Crystal; valor não publicado). MarioWiki: o gelo de Ice Land
  "reduz a tração" e é menos escorregadio que os Ice Blocks ([MarioWiki — Ice](https://www.mariowiki.com/Ice)).
- **Vento**: não há vento como mecânica em SMB3 — a MarioWiki lista apenas o tornado do deserto ([MarioWiki — Wind](https://www.mariowiki.com/Wind)).

## 5. Super Mario World (SNES, 1990)

Fontes: [TASVideos — recursos SMW](https://tasvideos.org/GameResources/SNES/SuperMarioWorld), fóruns TASVideos
([154457](https://tasvideos.org/Forum/Posts/154457), [136217](https://tasvideos.org/Forum/Posts/136217), [134164](https://tasvideos.org/Forum/Posts/134164)),
[Mario Mayhem](https://mariomayhem.com/consoles/glitches_n_tricks/smw_tricks/super_mario_world_glitches.php),
[página de P-speed de cyborgape78](https://cyborgape78.github.io/Mechanics/Other%20Games/Pspeed.html), [MarioWiki — SMW](https://www.mariowiki.com/Super_Mario_World).

| Estado (SMW) | subpx/quadro | px/quadro | px/s | Confiança |
|---|---:|---:|---:|---|
| Andar (sem X/Y) | ≈ 20 (19–21?) | ≈ 1,25 | ≈ 75 | **ESTIMADO** (não confirmado; ver §15) |
| Correr (X/Y, P-meter < 112) | 36, 35, 36, 35, 37 | ≈ 2,24 | ≈ 134 | DOCUMENTADO |
| Sprint (P-meter = 112) | 48, 47, 48, 47, 49 | ≈ 2,99 | ≈ 179 | DOCUMENTADO |
| Voo de capa (teto) | 51 | 3,19 | 191 | DOCUMENTADO |
| Nadar | 15–17 | ≈ 1,0 | 60 | DOCUMENTADO |
| Canhão / glitch Esq+Dir | 64 / 52 | 4,0 / 3,25 | 240 / 195 | DOCUMENTADO (casos especiais) |

Regras:
- **A velocidade máxima não é constante**: oscila em ciclos de 5 quadros (…47, 48, 47, 49). Soltar a direção congela o valor do
  quadro atual — base do truque "6/5" (6 quadros soltos a 49, 5 segurando para recarregar o P-meter) e do "hop glitch".
- **Aceleração a partir do repouso**: 0, 1, 3, 4, 6, 7, 9… → média de **1,5 subpx/quadro²** = 0,094 px/q² ≈ **337 px/s²**
  (0→36 em 24 quadros = 0,4 s; 0→48 em 32 quadros = 0,53 s, mas o sprint exige o medidor cheio).
- **Virar**: o truque "−1" (0, −2, 3, 5, 6, 8, 9…) mostra um salto de −2 para +3 em um quadro; a página afirma que Mario
  "desacelera mais rápido do que acelera" e que o truque **não funciona em fases escorregadias**. Inferimos desaceleração de
  inversão ≈ 5 subpx/quadro² (0,31 px/q² ≈ 1125 px/s²) — ESTIMADO.
- **P-meter** (RAM $7E13E4): conta de 0 a 112 "pulando um número a cada quadro" (+2/quadro → 56 quadros ≈ 0,93 s) enquanto corre
  no chão; "não se relaciona diretamente com a velocidade"; a 112 Mario estica os braços e sprinta (fórum 134164, Mario Mayhem).
  Outra fonte cita 108 "na tela" (fórum 154457) — provavelmente artefato de leitura com atraso de 2 quadros.
- Sobe enquanto corre no chão, **cai no ar ou ao virar**; não cai nadando/escalando; pular com P cheio mantém o medidor se
  segurar a direção (cyborgape78, fórum 134164).
- **Gelo**: cinco fases com gelo reduzem a tração de Mario e Yoshi; há gelo semissólido e em rampas (MarioWiki — Ice).
- **Movimentos/estados**: andar, dash (X/Y mantido), carregar item, pular, pulo giratório, agachar, olhar para cima, escalar,
  nadar, deslizar em rampa, voar com capa ([MarioWiki — SMW](https://www.mariowiki.com/Super_Mario_World)).

## 6. New Super Mario Bros. (DS, 2006)

Fontes: [TASVideos — recursos NSMB](https://tasvideos.org/GameResources/DS/NewSuperMarioBros), [submissão TAS 8739S](https://tasvideos.org/8739S),
[MarioWiki — NSMB](https://www.mariowiki.com/New_Super_Mario_Bros.).

| Estado (NSMB DS) | px/quadro | px/s (60 Hz) | Confiança |
|---|---:|---:|---|
| Correr / pulo triplo (teto normal) | 3,0 | 180 | DOCUMENTADO |
| Casco azul | 2,75 (≈ 2,95 sem direção) | 165 | DOCUMENTADO |
| Estrela no chão / no ar | 4,5 / 3,0 | 270 / 180 | DOCUMENTADO (nota de TAS) |
| Andar | não publicado | — | **ESTIMADO** 1,0–1,5 px/q |

- Velocidade e posição em ponto fixo **20.12** (RAM `021B6A90` = X speed; `021B6A94` = "current max speed" — ou seja, o motor
  guarda um teto corrente que muda conforme o estado, como SMB1 faz com `MaximumRightSpeed`).
- Wall slide / wall jump exigem ter se movido horizontalmente no quadro atual e no anterior (mesmo que a parede empurre de volta).
- Mini Mario "corre por cima da água" (MarioWiki) — há, portanto, um estado de corrida plena reconhecido pelo jogo
  (P-run oculto, braços para trás) — OBSERVADO; sem número público de tempo de carga.
- Controles: dois modos de botões para dash; Fire Flower e casco azul **revertem para Super Mario** ao sofrer dano, não para pequeno
  (MarioWiki — DOCUMENTADO).
- Gelo: trechos específicos; "enemies do not slip on the ice" (MarioWiki — Ice).

## 7. New Super Mario Bros. Wii (2009)

Fontes comunitárias: [NSMBW Speedrun Guides — Speed](https://nsmbwcommunity.github.io/NSMBW-Speedrun-Guides/movement/speed/),
[Moving Platforms](https://nsmbwcommunity.github.io/NSMBW-Speedrun-Guides/movement/moving-platforms/), [Slopes](https://nsmbwcommunity.github.io/NSMBW-Speedrun-Guides/movement/slopes/),
[fórum TASVideos 523410](https://tasvideos.org/Forum/Posts/523410), [MarioWiki — Wind](https://www.mariowiki.com/Wind), [MarioWiki — Ice](https://www.mariowiki.com/Ice).
Oficiais: Iwata Asks NSMBW [Vol. 1 §9](https://www.nintendo.com/en-gb/Iwata-Asks/Iwata-Asks-New-Super-Mario-Bros-Wii/Volume-1/9-The-Correct-Way-to-Enjoy-An-Action-Game/9-The-Correct-Way-to-Enjoy-An-Action-Game-211131.html),
[Vol. 1 §8](https://www.nintendo.com/en-gb/Iwata-Asks/Iwata-Asks-New-Super-Mario-Bros-Wii/Volume-1/8-Capturing-That-Mario-Esque-Smell/8-Capturing-That-Mario-Esque-Smell-211077.html),
[Vol. 2 §10](https://www.nintendo.com/en-gb/Iwata-Asks/Iwata-Asks-New-Super-Mario-Bros-Wii/Volume-2/10-New-Things-To-Discover/10-New-Things-To-Discover-233368.html).

| Estado (NSMBW) | px/quadro ("speed") | px/s | Confiança |
|---|---:|---:|---|
| Correr (teto regular) | 3,0 | 180 | DOCUMENTADO |
| Pular (teto no ar) | 3,0 | 180 | DOCUMENTADO |
| Estrela | 4,0 | 240 | DOCUMENTADO |
| Deslize de pinguim | 4,0 (= corrida + 1 ao iniciar) | 240 | DOCUMENTADO |
| "Hyperspeed" em rampa íngreme | até 4,32 | 259 | DOCUMENTADO |
| Hélice subindo / caindo | 2,5 / 1,5 | 150 / 90 | DOCUMENTADO |
| Andar / aceleração | não publicados | — | ESTIMADO |

- Guia: "segure sempre 1 (dash) ao se mover"; "descidas ajudam a acelerar"; "subir rampa correndo é lento".
- **Plataformas móveis**: morros rolantes, esteiras, bone coaster e blocos de gelo grandes **transferem a velocidade ao pular**;
  plataformas de trilho, blocos giratórios e plataformas flutuantes alteram a velocidade enquanto se corre sobre elas, mas **o pulo
  volta a 3,0**; ao pousar, a velocidade volta à do chão (ou 3,0 em chão normal). Chão andando para trás reduz a velocidade.
- **Vento** (Mundo 2-4): empurra para a direita, agachar permite ficar parado, areia visível, moedas voam, inimigos param
  (MarioWiki — Wind).
- **Gelo**: por trechos; Penguin Mario não escorrega e desliza de barriga (MarioWiki — Ice).
- OFICIAL: Miyamoto — Wii Remote na horizontal, +Control Pad e botões 1/2, "os mesmos controles da era Famicom" (Iwata); o jogador
  "precisa dominar o B Button Dash" (botão 1). Miyamoto: "the actual feel when you press a button differs… we have to redo it for
  each and every game" (a resposta ao botão é reajustada em cada título). Iwata: NSMBW é "evolução em linha reta" do 2D desde SMW.

## 8. New Super Mario Bros. U (2012)

Fontes: [Iwata Asks NSMBU §1](https://www.nintendo.com/en-gb/Iwata-Asks/Iwata-Asks-New-Super-Mario-Bros-U/New-Super-Mario-Bros-U/1-What-Should-Be-New-/1-What-Should-Be-New--686442.html) (OFICIAL),
[MarioWiki — Ice](https://www.mariowiki.com/Ice), [Nintendo Life / Digital Foundry](https://www.nintendolife.com/news/2023/10/video-digital-foundrys-technical-analysis-of-super-mario-bros-wonder).

- OFICIAL: Takemoto — "If you just used it to move Mario, touch controls would be inferior to the Wii Remote"; Iwata — "Button
  controls are better suited to Mario's actions"; Takemoto — "the basic gameplay won't change", o foco foi acrescentar elementos.
- Nenhum valor numérico público de velocidade foi encontrado. Como o diretor Hayashida descreve SMBW como ruptura com "o motor da
  série New Super Mario Bros." ([Ask the Developer Vol. 11 parte 1](https://www.nintendo.com/us/whatsnew/ask-the-developer-vol-11-super-mario-bros-wonder-part-1/)),
  assumimos que NSMBU compartilha a família de motor de NSMBW (teto de corrida ≈ 3,0 px/quadro) — **ESTIMADO**.
- Gelo: grandes seções escorregadias para todos os personagens; o Penguin Suit só surge em Superstar Road; no Deluxe, Nabbit e
  Toadette não escorregam (MarioWiki — Ice, DOCUMENTADO).
- Digital Foundry (OBSERVADO): o movimento de Wonder é "remarkably similar to that of New Super Mario Bros. U" — útil como
  referência cruzada de sensação.

## 9. Super Mario Bros. Wonder (Switch, 2023)

Fontes OFICIAIS: Ask the Developer Vol. 11 [parte 1](https://www.nintendo.com/us/whatsnew/ask-the-developer-vol-11-super-mario-bros-wonder-part-1/),
[parte 2](https://www.nintendo.com/us/whatsnew/ask-the-developer-vol-11-super-mario-bros-wonder-part-2/), [parte 3](https://www.nintendo.com/us/whatsnew/ask-the-developer-vol-11-super-mario-bros-wonder-part-3/),
[parte 4](https://www.nintendo.com/us/whatsnew/ask-the-developer-vol-11-super-mario-bros-wonder-part-4/). DOCUMENTADO: [MarioWiki — Badge (SMBW)](https://www.mariowiki.com/Badge_(Super_Mario_Bros._Wonder)),
[MarioWiki — Fast Dash](https://www.mariowiki.com/Fast_Dash), [MarioWiki — Ice](https://www.mariowiki.com/Ice), [MarioWiki — Wind](https://www.mariowiki.com/Wind).
OBSERVADO: [Nintendo Life / Digital Foundry](https://www.nintendolife.com/news/2023/10/video-digital-foundrys-technical-analysis-of-super-mario-bros-wonder).

- **Motor novo** (Hayashida), pensado como base para futuros 2D; Sato: manter "a confiança" nas regras (canos sólidos etc.).
- **Animação** (Sato): resgate de poses clássicas, "a jump with arms extended and a sudden stop after running" — a **derrapagem
  volta como pose explícita**; 12 articulações, mais que o dobro de animações; o corpo olha para a direção de viagem e o rosto para
  a câmera.
- **Correr antes de pular aumenta a distância do salto** e o som do pulo muda com a forma de pular (Kondo) — confirma o
  acoplamento corrida→pulo dos títulos antigos.
- **Tolerância** (Tezuka): o 2D era visto como implacável porque "one mistimed action can lead to a bigger mistake, since you have
  fewer options in terms of movement"; Mouri: personagens não têm mais atributos distintos ("se queria pular mais alto, tinha que
  escolher Luigi") — as diferenças migraram para **emblemas**.
- **Emblemas que alteram a movimentação horizontal** (MarioWiki, descrições do jogo): *Jet Run* (Expert) — "Dash continuously at
  incredible speed. If you run off an edge, you'll also have a short window where you can jump in midair" (Mouri chama de "a badge
  that makes you run nonstop"); *Fast Dash* (Action) — "Dash a little faster than usual. You'll walk a little faster too, even across
  sandy areas!", eleva os tetos de andar e correr **depois de andar/correr por um tempo**, braços abertos "como no P-Meter", nome
  interno `ExActPDash`; *Dolphin Kick* (impulso na água); *Parachute Cap*, *Wall-Climb Jump*, *Floating/Crouching/Timed High Jump*,
  *Boosting Spin Jump*, *Spring Feet*, *Grappling Vine* (verticais).
- Inferência (ESTIMADO): o jogo-base tem **duas camadas** (andar, dash) e o Fast Dash acrescenta a terceira camada "P" dos títulos
  antigos; Jet Run fixa a velocidade no teto e troca a frenagem por uma "janela de pulo" após sair da borda.
- **Gelo**: três fases de Fluff-Puff Peaks; dica de carregamento "You can't stop quickly on frozen surfaces" (OFICIAL via MarioWiki);
  Toadette e Nabbit escorregam.
- **Vento**: só em "Ludwig's Showdown!", "behaves the same way as in Super Mario Maker 2"; a forma Broca ignora o vento quando
  enterrada (MarioWiki — Wind).
- Digital Foundry (OBSERVADO): movimento parecido com NSMBU, mas a inércia é "a cross between the precise platforming found in
  Super Mario World and the slightly heavier feeling in Super Mario Bros. 3"; 60 fps quase travados.

## 10. Síntese comparativa

| Título | Andar | Correr | Camada P / sprint | Correr ÷ andar | Aceleração (px/s²) | Como é a P |
|---|---:|---:|---:|---:|---:|---|
| SMB1 | 90 px/s | 150 | — | 1,67 | 134 (andar) / 200 (correr) | não existe; 10 quadros de graça ao soltar B |
| SMB3 | 90 | 150 | 210 | 1,67 (P: 2,33) | ≈ 197 (7/8 un./q) | medidor visível, 56 q para encher, 24 q por seta ao esvaziar |
| SMW | ≈ 75 (EST.) | ≈ 134 | ≈ 179 | ≈ 1,8 (P: 2,4) | ≈ 337 | oculto, 0→112 em ≈ 56 q; braços para trás |
| NSMB DS | ? | 180 | (P-run oculto, OBS.) | — | ? | arms-back; Mini corre na água |
| NSMBW | ? | 180 | (idem) | — | ? | idem |
| NSMBU | ? | ≈ 180 (EST.) | (idem) | — | ? | idem |
| SMBW | ? | ? | só com Fast Dash | — | ? | "P-Dash" como emblema; Jet Run = teto fixo |

Leitura: a razão correr/andar fica entre 1,67 e 1,8 em todos os títulos com números; a camada P acrescenta 33–40 % sobre a corrida;
o tempo para "ganhar a P" converge para **≈ 0,9 s de corrida contínua** em SMB3 e SMW.

## 11. Tópicos transversais

### 11.1 Tempo de resposta dos controles
SMB1 lê o joypad e aplica a física no mesmo quadro (a rotina de chão chama `GetPlayerAnimSpeed`, grava a direção do rosto a partir
dos botões e só então `ImposeFriction`/`MovePlayerHorizontally`) — latência de software de **1 quadro (16,7 ms)** entre entrada e
deslocamento (DOCUMENTADO). Em todos os títulos a direção do rosto muda no primeiro quadro de entrada; o que "demora" é a velocidade.
Miyamoto: a resposta ao botão é retunada em cada jogo (OFICIAL, §7). Para o Lume: amostrar a entrada a cada passo de física (120 Hz)
com `pygame.key.get_pressed()` e usar `pygame.key.get_just_pressed()` (pygame-ce ≥ 2.4) para o buffer de pulo
([docs pygame-ce — key](https://pyga.me/docs/ref/key.html)); `Clock.tick()` devolve ms e "não é preciso em toda plataforma"
([docs pygame-ce — time](https://pyga.me/docs/ref/time.html)), por isso o acumulador de passo fixo deve ter teto de passos por quadro.

### 11.2 Controle horizontal no ar
- SMB1: aceleração igual à do chão, teto 40 se |v| ≥ 25 (sem precisar de B) e 24 se mais lento; **sem atrito quando não há entrada**;
  inversão de direção no ar vem com aceleração dobrada (DOCUMENTADO).
- SMB3/SMW: velocidade mantida no ar; o P-meter cai no ar em SMW, mas a P-speed de SMB3 fica retida por um timer (DOCUMENTADO).
- NSMBW: teto no ar = 3,0, igual ao chão; plataformas "tipo chão" somam velocidade ao pulo (DOCUMENTADO).
- Wonder: pulo mais longo correndo (OFICIAL) e Jet Run dá "janela de pulo" após a borda (OFICIAL/DOCUMENTADO) — equivalente ao
  coyote time já existente no Lume.

### 11.3 Gelo e superfícies escorregadias
SMB1 não tem gelo. SMB3: fator de atrito por fase (DOCUMENTADO, valor não público). SMW: fases inteiras escorregadias; a aceleração
muda (o truque −1 falha). NSMB/NSMBW/NSMBU/SMBW: gelo por trecho; só o jogador escorrega (inimigos não, em NSMB); "não dá para parar
rápido" (SMBW). Nenhuma fonte publica o multiplicador — qualquer número é ESTIMADO.

### 11.4 Vento
Mecânica horizontal apenas em NSMBW (2-4: empurrão para a direita, agachar anula), SMM2 (direção e frequência por estilo) e SMBW
(Ludwig). Não existe em SMB1, SMB3 e SMW como mecânica de movimentação (MarioWiki — Wind). Sem valores numéricos públicos.

### 11.5 Plataformas móveis
SMB1: elevadores verticais contínuos, horizontais de vai-e-vem, "flimsy" que caem ao pisar, balanças que quebram; lifts são
sólidos (não dá para atravessar por baixo) ([MarioWiki — Lift](https://www.mariowiki.com/Lift)). SMB3: rail lifts em trilhos;
SMW: swing lifts, pulley lifts, skull rafts. NSMBW (DOCUMENTADO): dois comportamentos — chão móvel (esteira, morro rolante)
transfere velocidade ao pulo; plataforma de trilho/flutuante não, e o pulo reseta para 3,0.

### 11.6 Recuperação após dano
SMB1: encolhe, 148–168 quadros invulnerável, sem empurrão, controle mantido (DOCUMENTADO). NSMB: formas com poder revertem para
Super, não para pequeno (DOCUMENTADO). Nos demais títulos o padrão "sem knockback, invencibilidade curta com piscar" é OBSERVADO
em gameplay, sem fonte textual com duração — tratar como ESTIMADO ao parametrizar.

### 11.7 Estados de animação de movimento (lista consolidada)

| Estado | SMB1 | SMB3 | SMW | NSMB/NSMBW/NSMBU | SMBW | Lume hoje |
|---|---|---|---|---|---|---|
| Parado | ✔ | ✔ | ✔ | ✔ | ✔ | idle |
| Andar (ciclo 3 quadros, ritmo por velocidade) | ✔ (7/4/2 q) | ✔ | ✔ | ✔ | ✔ | walk |
| Correr | (mesmo ciclo, mais rápido) | ✔ | ✔ | ✔ | ✔ | run |
| Sprint P (braços abertos/para trás) | — | ✔ | ✔ | ✔ (OBS.) | só Fast Dash | — |
| Derrapar | ✔ | ✔ | ✔ | ✔ | ✔ ("sudden stop") | — |
| Pular / cair | ✔ (uma pose) | ✔ | ✔ | ✔ | ✔ | jump / fall |
| Agachar / deslizar | ✔ (agachar) | ✔ (deslizar em rampa) | ✔ | ✔ (ground pound, wall slide) | ✔ | — |
| Virar (turnaround) | instantâneo | instantâneo | instantâneo | instantâneo | instantâneo | instantâneo |
| Dano (encolher) | ✔ | ✔ | ✔ | ✔ | ✔ | hurt |
| Morte / vitória | ✔ | ✔ | ✔ | ✔ | ✔ | dead / win |

## 12. Tabela obrigatória de parâmetros

| Parâmetro | Referência (título) | Valor estimado | Fonte | Confiança | Implementação proposta no Lume |
|---|---|---|---|---|---|
| Velocidade de caminhada | SMB1/SMB3 | 24/16 px/q = 90 px/s (5,6 h/s) | TASVideos, SMBPedia, Data Crystal | DOCUMENTADO | `WALK_SPEED = 220` (7,3 h/s; mantém fases) ou preset fiel 170 |
| Velocidade de corrida | SMB1/SMB3 | 40/16 = 150 px/s (9,4 h/s) | idem | DOCUMENTADO | `RUN_SPEED = 340` (11,3 h/s) ou preset fiel 280 |
| Velocidade de corrida | SMW | 36 (35–37) ≈ 134 px/s | TASVideos SMW | DOCUMENTADO | referência da razão 1,8 |
| Velocidade de corrida | NSMB DS/NSMBW | 3,0 px/q = 180 px/s | TASVideos NSMB, NSMBW guides | DOCUMENTADO | referência "moderna" |
| Camada P / sprint | SMB3 / SMW | 56 → 210 px/s / 48 → 180 px/s (+33–40 %) | TASVideos | DOCUMENTADO | `SPRINT_SPEED = 380` opcional (+12 %), `SPRINT_CHARGE = 0.9 s` |
| Tempo para encher a P | SMB3 / SMW | 56 quadros ≈ 0,93 s | narfman0, fórum 134164 | DOCUMENTADO (mecanismo) / ESTIMADO (soma) | `SPRINT_CHARGE = 0.9` |
| Esvaziamento da P | SMB3 | 1 seta / 24 q; total ≈ 2,8 s | narfman0, Data Crystal | DOCUMENTADO / ESTIMADO | `SPRINT_DECAY = 2.5 s` até zerar |
| Aceleração correndo (chão) | SMB1 | 0xE4 → 200 px/s² (×1,875 = 376) | desmontagem, SMBPedia | DOCUMENTADO | `ACCEL_RUN = 800` (0,43 s até 340) |
| Aceleração andando (chão) | SMB1 | 0x98 → 134 px/s² (×1,875 = 250) | idem | DOCUMENTADO | `ACCEL_WALK = 700` (0,31 s até 220) |
| Aceleração | SMW | 1,5 un./q² → 337 px/s² (×1,875 = 633) | TASVideos SMW | DOCUMENTADO | justifica `ACCEL_RUN` entre 630 e 800 |
| Aceleração | SMB3 | 7/8 un./q² → 197 px/s² | Data Crystal, narfman0 | DOCUMENTADO (regra) / ESTIMADO (valor) | — |
| Desaceleração ao soltar | SMB1 | 0xD0 → 183 px/s² (×1,875 = 343) | desmontagem, SMBPedia | DOCUMENTADO | `DECEL_RELEASE = 900` (para de 340 em 0,38 s / 64 px) |
| Desaceleração de derrapagem | SMB1 | 2 × 0xD0 = 366 px/s² (×1,875 = 686) | idem | DOCUMENTADO | `DECEL_SKID = 1800` (= 2 × release) |
| Limiar de giro na derrapagem | SMB1 | 11 un. = 41 px/s (×1,875 = 77) | desmontagem (`ProcSkid`) | DOCUMENTADO | `SKID_TURN_SPEED = 80` (fim do estado skid) |
| Inversão em um quadro | SMW | ≈ 5 un./q² → 1125 px/s² | TASVideos SMW (truque −1) | ESTIMADO | teto superior para `DECEL_SKID` |
| Graça ao soltar o botão de correr | SMB1 | 10 quadros = 0,167 s | SMBPedia | DOCUMENTADO | `RUN_RELEASE_GRACE = 0.17` |
| Limiar "rápido" para atrito forte | SMB1 | 33 un. (ou flag ≥ 28) | desmontagem | DOCUMENTADO | `FAST_THRESHOLD = 0.8 × RUN_SPEED` |
| Teto no ar | SMB1 | 40 se |v| ≥ 25, senão 24 | SMBPedia | DOCUMENTADO | teto aéreo = max(teto por botão, |vx| atual) |
| Atrito no ar sem entrada | SMB1 | 0 | desmontagem (`LRAir`) | DOCUMENTADO | `AIR_DRAG = 0` (hoje 500) |
| Aceleração no ar | SMB1 / NSMBW | igual ao chão / teto 3,0 igual ao chão | SMBPedia, NSMBW guides | DOCUMENTADO | `ACCEL_AIR = 700` |
| Ritmo da animação de andar | SMB1 | 7/4/2 quadros por pose em |v| < 14 / < 28 / ≥ 28 | desmontagem | DOCUMENTADO | duração da pose = 0,117 / 0,067 / 0,033 s em |vx| < 0,35 / < 0,7 / ≥ 0,7 × RUN |
| Pulo acoplado à velocidade | SMB1 / SMB3 / SMBW | limiares 9/16/25/28; tabela {0,2,4,8}; "correr aumenta a distância" | SMBPedia, Data Crystal, Ask the Developer p. 2 | DOCUMENTADO / OFICIAL | manter: distância cresce com vx; opcional +4 % impulso com sprint |
| Gelo — aceleração | SMB3/SMW/SMBW | "menos tração", "não para rápido" | MarioWiki Ice, TASVideos SMW | OBSERVADO | `ICE_ACCEL_MULT = 0.35` (ESTIMADO) |
| Gelo — desaceleração | idem | — | idem | ESTIMADO | `ICE_DECEL_RELEASE = 220`, `ICE_DECEL_SKID = 500` |
| Vento | NSMBW 2-4 / SMM2 / SMBW | empurra lateralmente; agachar anula | MarioWiki Wind | DOCUMENTADO (comportamento) | `WIND_ACCEL = 300`, `WIND_MAX = 120`, agachado × 0 |
| Plataforma móvel — carregar | SMB1…SMBW | jogador acompanha a plataforma | MarioWiki Lift, NSMBW guides | DOCUMENTADO | manter `p.x += s.dx` (já existe) |
| Plataforma móvel — herdar vx no pulo | NSMBW | esteira/morro: sim; trilho/flutuante: não (volta a 3,0) | NSMBW guides | DOCUMENTADO | `PLATFORM_CARRY_ON_JUMP` por tipo: `moving`=0, `conveyor`=1 |
| Dano — knockback | SMB1 | nenhum | desmontagem (`InjurePlayer`) | DOCUMENTADO | `HURT_KNOCKBACK = 0` (hoje 100 px/s) |
| Dano — invulnerabilidade | SMB1 | 8 × 21 q = 2,5–2,8 s | desmontagem, Set Side B | DOCUMENTADO | `HURT_INVULN = 2.6` (hoje 2,0) |
| Latência de entrada | SMB1 | 1 quadro | desmontagem | DOCUMENTADO | amostrar entrada a cada passo de 1/120 s |

## 13. Implicações para o Lume

### 13.1 Decisões de design (com a origem de cada mecânica)
1. **Duas camadas de velocidade + sprint opcional.** Andar/correr vêm de SMB1 (espec. "two speeds", OFICIAL). A terceira camada
   "P" é importada de **SMB3/SMW** como *feature flag* `SPRINT_ENABLED = False` até que as fases sejam revalidadas; quando ligada,
   enche em 0,9 s de corrida contínua no chão, cai ao virar/agachar/bater na parede (regra de SMB3) e **não cai ao pular** (SMB3).
2. **Arrancada mais lenta que hoje, derrapagem forte.** O Lume acelera em 0,24 s até 340 px/s (1,4 alturas); SMB1 leva 0,75 s
   (3,5 tiles) e SMW 0,4–0,5 s. Proposta: 0,43 s e 2,4 alturas (`ACCEL_RUN = 800`), com `DECEL_SKID = 2 × DECEL_RELEASE`
   (assinatura de SMB1) e estado `skid` visível (pose "sudden stop" de SMBW/SMB1).
3. **Sem atrito aéreo sem entrada** e teto aéreo que preserva a velocidade atual (SMB1). Hoje o Lume freia 500 px/s² no ar sem
   entrada e trava o teto pelo botão de correr; isso encurta saltos iniciados correndo quando o jogador solta Shift.
4. **Virar o rosto instantaneamente** (todos os títulos), manter `skid` enquanto `sign(vx) ≠ dir` e |vx| > 80 px/s.
5. **Graça de 0,17 s ao soltar correr** (SMB1 `RunningTimer`) e, depois dela, decaimento suave até 220 (em vez do corte seco do NES).
6. **Gelo afeta aceleração, não só atrito** (SMW: a aceleração muda em fases escorregadias). Hoje o Lume só reduz o atrito.
7. **Vento** como campo de aceleração horizontal por fase (NSMBW/SMM2), anulado agachado, 100 % no ar.
8. **Plataformas móveis**: manter o carregamento por deslocamento; herdar vx no pulo apenas em esteiras (regra NSMBW).
9. **Dano sem empurrão** (SMB1), invulnerabilidade 2,6 s, controle mantido; o encolhimento é só animação.
10. **Camera lookahead** continua proporcional a vx (já é `vx × 0,15`) — compatível com a leitura de "inércia" de SMW/SMB3.

### 13.2 Constantes propostas (Python, px/s, px/s², s)

```python
# lume/core/tuning.py — valores para 1/120 s de passo fixo; comentários indicam a referência
WALK_SPEED = 220.0          # mantém fases atuais (preset fiel: 170 = 90 px/s × 1,875, SMB1)
RUN_SPEED = 340.0           # (preset fiel: 280 = 150 px/s × 1,875, SMB1/SMB3)
SPRINT_SPEED = 380.0        # camada P (SMB3/SMW); só com SPRINT_ENABLED
SPRINT_ENABLED = False
SPRINT_CHARGE = 0.9         # s de corrida contínua no chão (SMB3: 56 q; SMW: 112/2 q)
SPRINT_DECAY = 2.5          # s para esvaziar (SMB3 ≈ 7 × 24 q)
ACCEL_WALK = 700.0          # SMB1 0x98 = 134 px/s² × 1,875 = 250; SMW 337 × 1,875 = 633 → escolhido 700
ACCEL_RUN = 800.0           # SMB1 0xE4 = 200 × 1,875 = 376 (fiel) → 800 (moderno, 0,43 s até 340)
ACCEL_AIR = 700.0           # SMB1: igual ao chão; NSMBW: teto aéreo igual ao chão
AIR_DRAG = 0.0              # SMB1: sem atrito aéreo sem entrada (hoje 500)
DECEL_RELEASE = 900.0       # SMB1 0xD0 = 183 × 1,875 = 343 (fiel) → 900 ("desacelera mais rápido que acelera", SMW)
DECEL_SKID = 1800.0         # SMB1: 2 × atrito ao soltar
SKID_TURN_SPEED = 80.0      # SMB1: 11/16 px/q = 41 px/s × 1,875
RUN_RELEASE_GRACE = 0.17    # SMB1 RunningTimer = 10 quadros
FAST_THRESHOLD = 0.8 * RUN_SPEED   # SMB1: 33/40
ICE_ACCEL_MULT = 0.35       # ESTIMADO (SMW/SMB3/SMBW: "menos tração")
ICE_DECEL_RELEASE = 220.0   # hoje 180
ICE_DECEL_SKID = 500.0
WIND_ACCEL = 300.0          # NSMBW 2-4 / SMM2 — ESTIMADO
WIND_MAX = 120.0            # acréscimo máximo ao teto na direção do vento
WIND_CROUCH_MULT = 0.0      # NSMBW: agachar permite ficar parado
PLATFORM_CARRY_ON_JUMP = {"moving": 0.0, "conveyor": 1.0}   # NSMBW: trilho não herda, esteira herda
HURT_KNOCKBACK = 0.0        # SMB1: sem empurrão (hoje 100)
HURT_INVULN = 2.6           # SMB1: 148–168 quadros
ANIM_WALK_FRAME = (0.117, 0.067, 0.033)   # SMB1: 7/4/2 quadros em |v| < 0,35 / < 0,7 / ≥ 0,7 × RUN
```

### 13.3 Pseudocódigo do passo horizontal (1/120 s)

```python
def step_horizontal(p, inp, dt, surface, wind):
    dir = int(inp.right) - int(inp.left)
    if dir: p.facing = dir                                   # todos os títulos: rosto vira na hora
    ice = surface.kind == "ice"
    a_mult = ICE_ACCEL_MULT if ice else 1.0
    # teto: correr, graça ao soltar (SMB1), sprint opcional
    if inp.run and p.grounded: p.run_grace = RUN_RELEASE_GRACE
    else: p.run_grace = max(0.0, p.run_grace - dt)
    cap = RUN_SPEED if (inp.run or p.run_grace > 0) else WALK_SPEED
    if SPRINT_ENABLED and p.sprint >= SPRINT_CHARGE: cap = SPRINT_SPEED
    if not p.grounded: cap = max(cap, min(abs(p.vx), RUN_SPEED))   # SMB1: ar preserva velocidade ≥ limiar
    moving_against = dir != 0 and p.vx != 0 and (dir > 0) != (p.vx > 0)
    if dir and not moving_against:                           # acelerar
        a = (ACCEL_RUN if cap > WALK_SPEED else ACCEL_WALK) if p.grounded else ACCEL_AIR
        p.vx = approach(p.vx, dir * cap, a * a_mult * dt)   # approach também traz vx acima do teto de volta ao teto
    elif moving_against:                                     # derrapagem (SMB1: atrito dobrado)
        d = (ICE_DECEL_SKID if ice else DECEL_SKID) if p.grounded else ACCEL_AIR
        p.vx = approach(p.vx, 0.0, d * dt)
        p.skid = p.grounded and abs(p.vx) > SKID_TURN_SPEED
    else:                                                    # soltou tudo
        d = (ICE_DECEL_RELEASE if ice else DECEL_RELEASE) if p.grounded else AIR_DRAG
        p.vx = approach(p.vx, 0.0, d * dt)
    if wind: p.vx = approach(p.vx, p.vx + wind.dir * WIND_MAX, WIND_ACCEL * (WIND_CROUCH_MULT if inp.down and p.grounded else 1.0) * dt)
    # sprint (SMB3): enche correndo no chão no teto; zera ao virar/agachar/bater; não cai ao pular
    if SPRINT_ENABLED:
        if p.grounded and inp.run and abs(p.vx) >= RUN_SPEED - 1: p.sprint = min(SPRINT_CHARGE, p.sprint + dt)
        elif moving_against or inp.down or p.hit_wall: p.sprint = 0.0
        elif p.grounded: p.sprint = max(0.0, p.sprint - dt * SPRINT_CHARGE / SPRINT_DECAY)
```

Estados de animação derivados: `skid` (prioridade sobre walk/run), `sprint` quando `cap == SPRINT_SPEED` e |vx| ≥ 0,95 × cap
(braços abertos — SMB3/SMW), `walk`/`run` por fração de `RUN_SPEED`, `jump`/`fall` por sinal de vy, `hurt` só por tempo.

### 13.4 Entrada e temporização no pygame-ce
- Loop: `pygame.event.pump()` ou `for e in pygame.event.get()` uma vez por quadro renderizado; depois `keys = pygame.key.get_pressed()`
  e `pygame.key.get_just_pressed()` para o buffer de pulo (ambos documentados em [pyga.me/docs/ref/key.html](https://pyga.me/docs/ref/key.html)).
- Passo fixo 1/120 s com acumulador e teto (ex.: 8 passos) porque `Clock.tick()` "não é preciso em toda plataforma" e
  `tick_busy_loop()` gasta CPU ([pyga.me/docs/ref/time.html](https://pyga.me/docs/ref/time.html)).
- Reamostrar `get_pressed()` em cada passo não traz informação nova (o estado só muda ao processar eventos), então a latência
  mínima de software é 1 quadro renderizado — igual à do NES.

## 14. Testes matemáticos propostos

Notação: v = velocidade-alvo (px/s), a = aceleração (px/s²), dt = 1/120 s. O `approach` linear produz exatamente as fórmulas
cinemáticas abaixo quando v/a é múltiplo de dt; caso contrário o erro é ≤ a·dt em velocidade e ≤ v·dt em distância.

| Teste | Fórmula | Valor esperado (preset moderno) | Valor-referência (título) |
|---|---|---|---|
| Tempo até correr | t = RUN/ACCEL_RUN | 340/800 = 0,425 s (51 passos) | SMB1 0,75 s; SMW 0,53 s |
| Distância até correr | d = RUN²/(2·ACCEL_RUN) | 72,3 px = 2,4 alturas | SMB1 56 px = 3,5 tiles |
| Tempo/distância até andar | t = WALK/ACCEL_WALK ; d = WALK²/(2·ACCEL_WALK) | 0,314 s ; 34,6 px | SMB1 0,67 s ; 30 px |
| Frenagem ao soltar (corrida) | d = RUN²/(2·DECEL_RELEASE) | 64,2 px ; 0,378 s | SMB1 61,5 px ; 0,82 s |
| Frenagem ao soltar (andar) | d = WALK²/(2·DECEL_RELEASE) | 26,9 px ; 0,244 s | — |
| Derrapagem até parar | d = RUN²/(2·DECEL_SKID) | 32,1 px ; 0,189 s | SMB1 31 px ; 0,41 s |
| Derrapagem até o giro | t = (RUN − SKID_TURN)/DECEL_SKID | (340 − 80)/1800 = 0,144 s | SMB1 0,30 s |
| Inversão completa (−RUN → +RUN) | t = RUN/DECEL_SKID + RUN/ACCEL_RUN | 0,189 + 0,425 = 0,61 s | SMW ≈ 0,16 + 0,53 s |
| Gelo: parar de 340 | d = RUN²/(2·ICE_DECEL_RELEASE) | 263 px ; 1,55 s | hoje 321 px ; 1,89 s |
| Gelo: derrapar de 340 | d = RUN²/(2·ICE_DECEL_SKID) | 116 px ; 0,68 s | — |
| Preservação aérea | pular a 340, soltar tudo, pousar após 0,76 s | vx final = 340 ± 0 | SMB1: sem atrito aéreo |
| Sprint | correr 0,9 s no chão → cap 380 | atinge 380 em +0,05 s | SMB3/SMW ≈ 0,93 s |
| Graça de corrida | soltar Shift a 340 no chão | cap = 340 por 0,17 s, depois decai a 900 px/s² até 220 em 0,133 s | SMB1 10 q + corte seco |
| Vento | parado, vento +1, 2 s | vx → min(WIND_MAX, WIND_ACCEL·t) = 120 px/s em 0,4 s | NSMBW 2-4 (qualitativo) |
| Dano | atingir a 340 | vx inalterado; invulnerável 2,6 s | SMB1: sem empurrão, 2,5–2,8 s |

Testes diferenciais sugeridos (`tests/test_movement.py`): (a) simular N passos e comparar com as fórmulas acima com tolerância de
1 passo; (b) oráculo em **unidades inteiras do NES** (1/16 px, acumulador de 1/256) reproduzindo a tabela da §3.2 para validar que a
versão contínua escalada preserva as razões derrapagem/soltar = 2 e correr/andar ≈ 1,55–1,67; (c) propriedade: |vx| nunca excede o
teto corrente, exceto por herança de plataforma/vento, e nunca muda de sinal sem passar pelo estado `skid` no chão.

## 15. Lacunas e incertezas

1. **SMW — velocidade de caminhada** (≈ 20 subpx/q) não foi confirmada; a página TASVideos define "walking" sem número e a RAM map
   do SMW Central não pôde ser lida (aviso de direitos autorais). Marcar ESTIMADO até medição.
2. **SMW — desaceleração ao soltar e ao inverter**: só há a frase "decelera mais rápido do que acelera" e a sequência do truque −1;
   o valor de 5 un./q² é inferência.
3. **SMB3 — aceleração exata e desaceleração**: Data Crystal marca "TODO"; o −2/quadro observado não distingue soltar de inverter.
   O fator de atrito do cabeçalho de fase (gelo) não tem valor publicado.
4. **NSMB DS, NSMBW, NSMBU — velocidade de caminhada, aceleração, duração do P-run oculto**: nenhuma fonte pública; apenas o teto
   de corrida 3,0 px/q. NSMBU inteiro é estimado por família de motor.
5. **SMBW — números**: nenhum; a inferência "jogo-base com duas camadas, Fast Dash como terceira" vem da descrição do emblema e
   do nome interno `ExActPDash`.
6. **Dano em títulos pós-SMB1**: ausência de knockback e duração da invencibilidade são OBSERVADOS, sem fonte textual.
7. **Discrepância TMK × desmontagem** sobre a duração do piscar em SMB1 ("oito segundos de jogo" vs 8 × 21 quadros).
8. **Iwata Asks**: o espelho iwataasks.nintendo.com respondeu 503 durante a pesquisa; usamos as páginas equivalentes em
   nintendo.com/en-gb. A citação "control Mario at two speeds" foi lida no Vol. 5 §1 (en-gb).
9. **Vento e gelo**: todos os multiplicadores do Lume são escolhas de design (ESTIMADO); recomenda-se playtest com as fases de
   gelo (mundo de neve) antes de fixar.
10. **Escala**: usamos 1,875 (altura 30/16). Pela largura (22/16 = 1,375) ou pelo tile os números fiéis mudam; a §13 prefere manter
    os tetos atuais e calibrar acelerações, justamente para não depender da escala.
11. **Interação sprint × fases**: ligar `SPRINT_ENABLED` exige revalidar vãos máximos (docs/VALIDACAO.md) — o teto sobe 12 %.

## 16. Fontes

**OFICIAL (Nintendo / desenvolvedores)**
1. Ask the Developer Vol. 11 — Super Mario Bros. Wonder, parte 1: https://www.nintendo.com/us/whatsnew/ask-the-developer-vol-11-super-mario-bros-wonder-part-1/
2. Idem, parte 2 (animação, "sudden stop after running", som do pulo): https://www.nintendo.com/us/whatsnew/ask-the-developer-vol-11-super-mario-bros-wonder-part-2/
3. Idem, parte 3 (tolerância, emblemas, personagens sem atributos): https://www.nintendo.com/us/whatsnew/ask-the-developer-vol-11-super-mario-bros-wonder-part-3/
4. Idem, parte 4 (Jet Run, Yoshi/Nabbit): https://www.nintendo.com/us/whatsnew/ask-the-developer-vol-11-super-mario-bros-wonder-part-4/
5. Iwata Asks — NSMB Wii Vol. 1 §1 "Mario Couldn't Jump At First": https://www.nintendo.com/en-gb/Iwata-Asks/Iwata-Asks-New-Super-Mario-Bros-Wii/Volume-1/1-Mario-Couldn-t-Jump-At-First/1-Mario-Couldn-t-Jump-At-First-210699.html
6. Iwata Asks — NSMB Wii Vol. 1 §8 "Capturing That Mario-Esque Smell": https://www.nintendo.com/en-gb/Iwata-Asks/Iwata-Asks-New-Super-Mario-Bros-Wii/Volume-1/8-Capturing-That-Mario-Esque-Smell/8-Capturing-That-Mario-Esque-Smell-211077.html
7. Iwata Asks — NSMB Wii Vol. 1 §9 "The Correct Way to Enjoy An Action Game": https://www.nintendo.com/en-gb/Iwata-Asks/Iwata-Asks-New-Super-Mario-Bros-Wii/Volume-1/9-The-Correct-Way-to-Enjoy-An-Action-Game/9-The-Correct-Way-to-Enjoy-An-Action-Game-211131.html
8. Iwata Asks — NSMB Wii Vol. 2 §1 "It All Began In 1984": https://www.nintendo.com/en-gb/Iwata-Asks/Iwata-Asks-New-Super-Mario-Bros-Wii/Volume-2/1-It-All-Began-In-1984/1-It-All-Began-In-1984-232825.html
9. Iwata Asks — NSMB Wii Vol. 2 §3 "It Started With A Square Object Moving": https://www.nintendo.com/en-gb/Iwata-Asks/Iwata-Asks-New-Super-Mario-Bros-Wii/Volume-2/3-It-Started-With-A-Square-Object-Moving/3-It-Started-With-A-Square-Object-Moving-232967.html
10. Iwata Asks — NSMB Wii Vol. 2 §6 "No Rest After Completing Super Mario Bros." (pista de decolagem, 8× a largura): https://www.nintendo.com/en-gb/Iwata-Asks/Iwata-Asks-New-Super-Mario-Bros-Wii/Volume-2/6-No-Rest-After-Completing-Super-Mario-Bros-/6-No-Rest-After-Completing-Super-Mario-Bros-233134.html
11. Iwata Asks — NSMB Wii Vol. 2 §10 "New Things To Discover": https://www.nintendo.com/en-gb/Iwata-Asks/Iwata-Asks-New-Super-Mario-Bros-Wii/Volume-2/10-New-Things-To-Discover/10-New-Things-To-Discover-233368.html
12. Iwata Asks — SMB 25º aniversário Vol. 5 §1 "Using the D-pad to Jump" ("two speeds"): https://www.nintendo.com/en-gb/Iwata-Asks/Super-Mario-Bros-25th-Anniversary/Vol-5-Original-Super-Mario-Developers/1-Using-the-D-pad-to-Jump/1-Using-the-D-pad-to-Jump-212727.html
13. Iwata Asks — SMB 25º aniversário Vol. 3 §3 "Giving Super Mario the Mario Essence": https://www.nintendo.com/en-gb/Iwata-Asks/Super-Mario-Bros-25th-Anniversary/Vol-3-The-Developers-1-/3-Giving-Super-Mario-the-Mario-Essence/3-Giving-Super-Mario-the-Mario-Essence-222146.html
14. Iwata Asks — New Super Mario Bros. U §1 "What Should Be New": https://www.nintendo.com/en-gb/Iwata-Asks/Iwata-Asks-New-Super-Mario-Bros-U/New-Super-Mario-Bros-U/1-What-Should-Be-New-/1-What-Should-Be-New--686442.html

**DOCUMENTADO — técnico / comunitário (derivado de análise de terceiros)**
15. Desmontagem comentada de SMB (doppelganger) em HTML: https://6502disassembly.com/nes-smb/SuperMarioBros.html
16. SMBPedia — Movement (SMB1 / Lost Levels): https://simplistic6502.github.io/smb1_tll/smbpedia_movement.html
17. TASVideos — Game Resources: Super Mario Bros.: https://tasvideos.org/GameResources/NES/SuperMarioBros
18. TASVideos — texto de submissão SMB1 (tetos 24/40, subpixels): https://tasvideos.org/Forum/Posts/538365
19. TASVideos — análise de física SMB1 (três acelerações, dobro ao virar): https://tasvideos.org/Forum/Posts/467106
20. SMB1 Explained (negative-seven): https://negative-seven.github.io/smb1explained/
21. Data Crystal — Super Mario Bros.: Notes: https://datacrystal.tcrf.net/wiki/Super_Mario_Bros./Notes
22. Set Side B — framerules de 21 quadros: https://setsideb.com/?p=9145
23. TASVideos — Game Resources: Super Mario Bros. 3: https://tasvideos.org/GameResources/NES/SuperMarioBros3
24. Data Crystal — Super Mario Bros. 3: Notes: https://datacrystal.tcrf.net/wiki/Super_Mario_Bros._3:Notes
25. narfman0 — SMB3 TAS notes (regra do 8º quadro, P-meter): https://narfman0.github.io/angry-sun/pages/tas-notes.html
26. TASVideos — fórum SMB3 (limiares 33+/49+): https://tasvideos.org/Forum/Posts/476242
27. TASVideos — Game Resources: Super Mario World: https://tasvideos.org/GameResources/SNES/SuperMarioWorld
28. TASVideos — fórum SMW (P-meter, RAM $7E007B/$7E13E4): https://tasvideos.org/Forum/Posts/154457
29. TASVideos — fórum SMW (oscilação 49-48-47): https://tasvideos.org/Forum/Posts/136217
30. TASVideos — fórum SMW small-only (P-meter 0→112 pulando números): https://tasvideos.org/Forum/Posts/134164
31. Mario Mayhem — SMW glitches & tricks (112, voo 51): https://mariomayhem.com/consoles/glitches_n_tricks/smw_tricks/super_mario_world_glitches.php
32. cyborgape78 — P-speed (SMW): https://cyborgape78.github.io/Mechanics/Other%20Games/Pspeed.html
33. TASVideos — Game Resources: New Super Mario Bros. (DS): https://tasvideos.org/GameResources/DS/NewSuperMarioBros
34. TASVideos — submissão NSMB DS warpless (3,0 / 2,75 px/q): https://tasvideos.org/8739S
35. TASVideos — fórum NSMBW (3 speed, pinguim 4, hyperspeed 4,32): https://tasvideos.org/Forum/Posts/523410
36. NSMBW Speedrun Guides — Speed: https://nsmbwcommunity.github.io/NSMBW-Speedrun-Guides/movement/speed/
37. NSMBW Speedrun Guides — Moving Platforms: https://nsmbwcommunity.github.io/NSMBW-Speedrun-Guides/movement/moving-platforms/
38. NSMBW Speedrun Guides — Slopes: https://nsmbwcommunity.github.io/NSMBW-Speedrun-Guides/movement/slopes/
39. Super Mario Wiki — P-Meter: https://www.mariowiki.com/P_Meter
40. Super Mario Wiki — Dash: https://www.mariowiki.com/Dash
41. Super Mario Wiki — Ice: https://www.mariowiki.com/Ice
42. Super Mario Wiki — Wind: https://www.mariowiki.com/Wind
43. Super Mario Wiki — Lift: https://www.mariowiki.com/Lift
44. Super Mario Wiki — Fast Dash: https://www.mariowiki.com/Fast_Dash
45. Super Mario Wiki — Badge (Super Mario Bros. Wonder): https://www.mariowiki.com/Badge_(Super_Mario_Bros._Wonder)
46. Super Mario Wiki — New Super Mario Bros.: https://www.mariowiki.com/New_Super_Mario_Bros.
47. Super Mario Wiki — Super Mario World: https://www.mariowiki.com/Super_Mario_World
48. The Mushroom Kingdom — SMB breakdown (dano, distâncias de salto): https://themushroomkingdom.net/smb_breakdown.shtml
49. GlitterBerri — Mario Development Notes (tradução das notas do livro do 25º aniversário): https://glitterberri.com/super-mario-bros/mario-development-notes/
50. pygame-ce — pygame.key: https://pyga.me/docs/ref/key.html
51. pygame-ce — pygame.time: https://pyga.me/docs/ref/time.html

**OBSERVADO — análise de vídeo / gameplay**
52. Nintendo Life — resumo da análise técnica da Digital Foundry (SMBW vs NSMBU, inércia): https://www.nintendolife.com/news/2023/10/video-digital-foundrys-technical-analysis-of-super-mario-bros-wonder
