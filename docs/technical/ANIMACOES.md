# Animações

## Princípios adotados

- **FPS de renderização ≠ quadros de animação.** A simulação roda a 120 Hz; o desenho acompanha a taxa do monitor; as poses são funções contínuas do tempo e do estado físico, não folhas com N quadros. Em 30, 60 ou 144 Hz a animação é a mesma, só mais ou menos amostrada.
- **Movimento dirigido pela física**: a cadência dos passos vem da velocidade horizontal real, o arco do salto da velocidade vertical, o achatamento da aterrissagem do impacto medido (`land_impact`), a derrapagem da inversão de direção no chão (`skid`).
- **Antecipação, continuidade e movimento secundário**: agachar antes de saltar (criaturas), molas amortecidas para cachecol, lanterna e chapéu, inclinação do tronco acompanhando aceleração.

## Lume (`lume/render/characters/lume.py`)

Rig: raiz nos pés → pelve → tronco → pescoço → cabeça → chapéu; ombros → braço → antebraço/mão; quadris → coxa → canela/bota; lanterna presa ao cinto; cachecol em duas pontas. Altura da pelve calculada para que o pé mais baixo toque o chão (sem deslizar no idle). Formas pequena (0,36 u/du, ≈ 34 u de altura para caixa de 30 u) e grande (0,40 u/du, ≈ 47 u para 46 u); paleta normal e de fogo.

| Estado | Duração/frequência | Pose e expressão |
| ------ | ------------------ | ---------------- |
| idle | respiração 2,6 rad/s; olhar ao redor a cada 7 s | sorriso, piscar irregular 3,1–4,5 s |
| walk | ciclo 0,9 + v/100 Hz (≈ 3,1 Hz a 220 u/s) | passada 26°, braços opostos 24°, balanço 2 du |
| run | ciclo 0,9 + v/95 Hz (≈ 4,5 Hz a 340 u/s) | passada 36°, joelhos até 68°, braços 46°, inclinação 13°, poeira |
| skid | enquanto `skid` > 0 (0,16 s) | perna da frente estendida, tronco para trás, boca contraída, poeira |
| jump | subida em 0,12 s | braço da frente para cima, joelhos dobrados, esticamento 12% decaindo em 0,25 s, boca aberta |
| fall | contínuo | braços abertos oscilando 13 rad/s, boca em "o" |
| land | 0,08–0,16 s | achatamento até 16% e joelhos dobrados, olhos fechados |
| crouch | segurando baixo parado | joelhos dobrados, olhar para baixo |
| swim | braçada 5 rad/s | pernada e braçada alternadas |
| hurt | 0,45 s após dano | recuo, olhos apertados, piscar por 2 s depois |
| dead | 1,1 s | salto e queda, olhos atordoados, boca triste |
| win | ao concluir | pulos de comemoração, punho erguido, olhos felizes |
| transform | 0,6 s | alternância de forma a 16 Hz |
| disparo | 0,18 s | braço estendido à frente |

Folha de referência: `python tools/render_character_sheet.py saida.png` (todos os estados, forma grande, espelhado).

## Criaturas

Cada espécie tem um `CreatureRig` próprio com partes vetoriais e pose por estado da família de comportamento, olhos que piscam e acompanham o jogador quando a espécie tem olhos, achatamento no pisão, tombo de cabeça para baixo quando derrotada por fogo/casco/estrela e clarão ao receber dano. Exemplos do Reino Verde: Bolota (pausa e salto de alerta ao notar Lume), Caramujo (corpo que estica e contrai, olhos em pedúnculos, casco girando ao deslizar, tremor antes de acordar), Besouro-Asa (asas translúcidas batendo, pernas), Flor-Mordedora (toca que treme antes de subir, caule que balança, mandíbulas que mordem), Ouriço-Espinho (espinhos que eriçam no alerta), Javali Espinheiro (raspar a pata, investida, tontura com estrelas, recuo após dano, tombo de derrota).

## Limitações

Rotação de partes é rígida; não há deformação de malha (mesh skinning). O achatamento é aplicado por escala de partes e posições, suficiente para os ±16% usados.
