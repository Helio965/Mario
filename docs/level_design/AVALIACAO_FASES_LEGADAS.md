# Avaliação das 15 fases existentes (Etapa 2)

Confirmação do estado encontrado: a edição web tinha **5 mundos, 15 fases e 5 guardiões** (`src/data/levels.ts`). Todas foram preservadas e convertidas para o formato `lume.level` com IDs estáveis (ver `docs/technical/ARQUITETURA_FASES.md`). Na nova campanha de 10 mundos elas ocupam as vagas 1–3 dos mundos Reino Verde (1), Deserto Dourado (2), Montanhas Geladas (4), Floresta Encantada (5) e Fortaleza Vulcânica (9); cada guardião virou o confronto intermediário da vaga 3 do seu mundo.

## Método

- **Métricas objetivas** extraídas dos dados originais (largura, inimigos por tipo, moedas, relíquias, perigos, plataformas, vãos do caminho principal) e da execução real no motor Python (robô de rotas com entradas normais: tempo até a bandeira e mortes).
- **Avaliação qualitativa** por inspeção dos mapas e das capturas da edição web e da edição Python.
- Escala: 1 insuficiente · 2 fraco · 3 adequado · 4 bom · 5 excelente. A coluna "Antes" avalia a fase como estava na edição web; "Agora" descreve o que já mudou nesta entrega.

## Diagnóstico geral (todas as 15)

| Componente | Nota antes | Observação |
| ---------- | ---------- | ---------- |
| Tamanho | 2 | 3.200–5.200 px; o robô termina em 12–38 s — curto diante da meta de ~1 min por fase (pesquisa, `ENGENHARIA_REVERSA_FASES_MARIO.md`) |
| Qualidade gráfica | 2 | pixel art Canvas 960×540 com amostragem por vizinho mais próximo; mesmo terreno recolorido em todos os mundos |
| Dificuldade | 2 | curva quase plana: os vãos do mundo 5 (120 u) são iguais aos do mundo 1 |
| Quantidade de inimigos | 1 | **2 a 5 por fase** (incluindo o chefe) — muito abaixo de um jogo de plataforma moderno |
| Variedade de obstáculos | 2 | 1 faixa de espinhos ou alguns canais de lava; uma chama oscilante em 3 fases |
| Organização | 2 | sempre "chão plano + vão + chão plano"; poucas alturas; nenhuma área vertical |
| Segredos | 3 | 1 sala por cano e 1 relíquia em rota alta (1-1 tinha só a sala); pistas por placa |
| Plataformas | 3 | blocos, tijolos, plataformas frágeis e móveis bem usados, mas com os mesmos padrões |
| Progressão interna | 2 | introdução → desafio → recompensa raramente explícita |
| Objetivos | 3 | bandeira e guardião; sem desafios opcionais com recompensa clara |
| Desempenho | 4 | leve (Canvas), sem problemas |
| Colisões | 4 | física por eixo sólida; nenhuma colisão incorreta encontrada |
| Caminhos impossíveis | 5 | nenhum (440 saltos simulados na edição web; todas concluídas no motor Python) |
| Animações | 2 | sprites em matriz com membros oscilando; sem expressões |
| Compatibilidade inimigo × ambiente | 1 | os mesmos 6 tipos genéricos (andarilho, casco, voador, atirador, blindado, chefe) em todos os mundos |

## Já feito nesta entrega (para todas)

- Inimigos genéricos substituídos por **espécies nativas de cada bioma** com caixa de colisão e ajuste equivalentes, cada uma com máquina de estados própria (ex.: no deserto o andarilho virou o Escaravelho-de-Areia que se enterra em ciclos; nas montanhas, o Pinguim que desliza no gelo; na floresta, o Cogumelo que salta com antecipação; no vulcão, a Brasa imune ao fogo).
- Salas secretas no céu viraram **câmaras subterrâneas** de verdade, com paredes, teto e fundo de caverna.
- Física, colisões e tempos preservados (port fiel); ativação de inimigos por proximidade; nova câmera vertical por área.
- Renderização HD vetorial (dedicada no Reino Verde; mundos 2, 4, 5 e 9 dependem dos conjuntos artísticos em produção — ver matriz).

## Avaliação individual

### 1-1 Primeiros Passos (`first_steps`, Reino Verde 1)
Métricas: 3.200 u · 3 inimigos (2 andarilhos, 1 casco) · 35 moedas · 1 relíquia · 2 canais · vãos 100/120 · robô 12,0 s, 0 mortes.
Antes: boa introdução (blocos, primeiro vão, cano secreto, bloco oculto com estrela), mas curta e com apenas três inimigos. Notas: tamanho 2, inimigos 2, segredos 3, organização 3, gráficos 2.
Agora: canais visíveis com água animada; **3 relíquias** (sala subterrânea, topo da escada de tijolos, rota opcional de galhos sobre o caramujo); arte HD dedicada; Bolota com reação de alerta, Caramujo que sai da casca.
Ainda melhorar: estender com um trecho final que ensine o chute do casco antes da bandeira; mais um andarilho no primeiro terço para reforçar o pisão.

### 1-2 Canais do Vale (`valley_canals`, Reino Verde 2)
Métricas: 3.500 u · 3 inimigos · 31 moedas · 2 relíquias · 3 canais · vãos 100/120/**140** · 12,3 s, 0 mortes.
Antes: boa ideia de margem elevada e plataforma ascendente; o vão de 140 u no início da campanha contraria a regra de vão máximo do mundo 1 (≈ 0,5 do alcance). Notas: dificuldade 2 (pico injusto), segredos 3.
Agora: vão reduzido para 125 u; terceira relíquia sobre uma ponte de tábuas (rota alta opcional); canais visíveis.
Ainda melhorar: transformar os canais em rotas de tábuas e passarelas (identidade "canal"), adicionar um segundo Besouro-Asa em altura de pisão.

### 1-3 Guardião do Pomar (`orchard_guardian`, Reino Verde 3)
Métricas: 3.900 u · 4 inimigos (guardião com 3 PV) · 32 moedas · 2 relíquias · vãos 120/100/100 · 18,8 s, 0 mortes.
Antes: confronto final do mundo na edição web; arena aberta e justa, mas o restante da fase é curto. Notas: chefe 3, inimigos 2.
Agora: o guardião é o **confronto intermediário** do mundo 1 (o chefe principal é o Javali Espinheiro na fortaleza); terceira relíquia na copa via galhos sob o voo do besouro.
Ainda melhorar: pomar com árvores-plataforma (galhos de mão única) também no caminho principal; frutas como coletáveis decorativos.

### 2-1 Dunas ao Vento (`windswept_dunes`, Deserto Dourado 1)
Métricas: 3.800 u · 3 inimigos · 32 moedas · 2 relíquias · 1 faixa de espinhos · vãos 120/130/130 · 14,6 s, 0 mortes.
Antes: colunas de canos e escada de arenito interessantes; "vento" só no nome (nenhuma mecânica de vento). Notas: compatibilidade 1, mecânica do mundo 1.
Agora: Escaravelho-de-Areia (enterra-se), Tatu-Bola, Cacto Sentinela.
Ainda melhorar: **zonas de vento** (já suportadas pelo motor) num trecho seguro de demonstração; dunas com subidas e descidas; terceira relíquia.

### 2-2 Pontes do Cânion (`canyon_bridges`, Deserto Dourado 2)
Métricas: 4.100 u · 3 inimigos · 36 moedas · 2 relíquias · espinhos + chama oscilante · vãos 120/130/120/120 · 14,8 s, 0 mortes (após correção).
Antes: terraços em várias alturas e rota frágil — a fase mais vertical da edição web. **Problema encontrado**: plataforma frágil logo acima do inimigo antes do vão de 130 u fazia o salto sobre o inimigo bater no teto e cair no vão (o robô morria 2–3 vezes ali). Notas: colisões/composição 2 nesse trecho.
Agora: plataformas frágeis deslocadas para fora da patrulha do Tatu-Bola (0 mortes).
Ainda melhorar: pontes de corda reais entre terraços (identidade "pontes"), Abutrinho em altura de pisão, terceira relíquia.

### 2-3 Templo das Areias (`sand_temple`, Deserto Dourado 3)
Métricas: 4.200 u · 3 inimigos (guardião 4 PV) · 32 moedas · 2 relíquias · vãos 110/110/120 · 25,0 s, 0 mortes.
Antes: escadaria arqueológica e primeiro blindado bem apresentados; templo sem interior. Notas: organização 3, inimigos 1.
Agora: Escorpião-Couraça com cauda periódica (janela de pisão), guardião do templo como confronto intermediário.
Ainda melhorar: trecho interior de templo (área com variante fortaleza), armadilhas de areia, terceira relíquia.

### 3-1 Lago de Cristal (`crystal_lake`, Montanhas Geladas 1)
Métricas: 3.600 u · 3 inimigos · 35 moedas · 2 relíquias · vãos 120/120/120 · 11,7 s, 0 mortes.
Antes: boa apresentação do gelo com espaço para frear depois de cada salto. Notas: física do mundo 4, inimigos 1.
Agora: Pinguim Patrulheiro que mergulha de barriga no gelo, Caracol-de-Cristal, Coruja Nevada.
Ainda melhorar: lago congelado de verdade (superfície de gelo longa com reflexo), terceira relíquia, mais inimigos.

### 3-2 Escalada Azul (`blue_ascent`, Montanhas Geladas 2)
Métricas: 4.400 u · **2 inimigos** · 45 moedas · 2 relíquias · 5 vãos · 21,0 s, 0 mortes (robô caminha, sem correr, nos terraços de gelo).
Antes: seis terraços com subida de 80 u — "escalada" tímida (a fase quase não sobe). Notas: inimigos 1, organização 3.
Ainda melhorar: subida vertical real (área mais alta que 540 u com câmera vertical), Boneco de Neve no topo, terceira relíquia.

### 3-3 Coração da Nevasca (`blizzard_heart`, Montanhas Geladas 3)
Métricas: 4.600 u · 4 inimigos (guardião 5 PV) · 35 moedas · 2 relíquias · vãos 110–120 · 25,1 s, 0 mortes.
Antes: alternância gelo/rocha e arena seca bem pensadas. Notas: chefe 3, clima só visual.
Agora: Carneiro Glacial (investida com aviso e tontura) no lugar do blindado genérico.
Ainda melhorar: rajadas de nevasca (vento com período) no trecho final, terceira relíquia.

### 4-1 Copas Luminosas (`glowing_canopy`, Floresta Encantada 1)
Métricas: 4.000 u · 3 inimigos · 36 moedas · 2 relíquias · 1 espinho · 13,8 s, 0 mortes.
Antes: copa frágil em três alturas — rota alta interessante; chão inferior monótono. Notas: organização 3.
Agora: Cogumelo Saltitante, Caracol-Musgo camuflado, Mariposa-Lume, Planta-de-Esporos.
Ainda melhorar: copas como plataformas de mão única (galhos), vagalumes como guia de rota, terceira relíquia.

### 4-2 Ruínas dos Vagalumes (`firefly_ruins`, Floresta Encantada 2)
Métricas: 4.500 u · 3 inimigos · 39 moedas · 2 relíquias · chama oscilante · 15,5 s, 0 mortes (a edição web aceitava 2 mortes).
Antes: bloco invisível sinalizado por luzes e salão de canos — boa ideia de segredo. Notas: segredos 4.
Ainda melhorar: interior das ruínas como área própria, mais blocos ocultos com pistas de vagalumes, terceira relíquia.

### 4-3 A Árvore Ancestral (`ancestral_tree`, Floresta Encantada 3)
Métricas: 4.700 u · 4 inimigos (guardião 6 PV) · 35 moedas · 2 relíquias · 29,6 s, 0 mortes.
Antes: duas subidas distintas para a mesma relíquia — melhor uso de rotas alternativas da edição web. Notas: rotas 4.
Ainda melhorar: subir **pela** árvore (tronco e raízes como estrutura), terceira relíquia.

### 5-1 Pontes de Basalto (`basalt_bridges`, Fortaleza Vulcânica 1)
Métricas: 4.300 u · 3 inimigos · 36 moedas · 2 relíquias · 4 canais de lava, chama, espinhos · 15,1 s, 0 mortes.
Antes: final de uma campanha de 15 fases; agora é a fase 49 de 60 e **ficou fácil demais** para o mundo 9. Notas: dificuldade relativa 1.
Ainda melhorar: subir para a dificuldade do mundo 9 (bolhas de lava, mais blindados, vãos de 150–180 u), pontes que desabam, terceira relíquia.

### 5-2 Fornalha dos Ecos (`echo_furnace`, Fortaleza Vulcânica 2)
Métricas: 4.800 u · 3 inimigos · 41 moedas · 2 relíquias · 5 canais de lava, 2 chamas, 2 espinhos · 16,7 s, 0 mortes.
Antes: a fase com mais perigos; boa galeria frágil. Mesma ressalva de dificuldade relativa.
Ainda melhorar: interior de fornalha (variante fortaleza), prensas e jatos de fogo, terceira relíquia.

### 5-3 A Última Chama (`last_flame`, Fortaleza Vulcânica 3)
Métricas: 5.200 u · 5 inimigos (guardião 7 PV com três disparos) · 43 moedas · 2 relíquias · 38,3 s, 1 morte (orçamento herdado da suíte web).
Antes: síntese das mecânicas e o guardião mais difícil — bom fechamento da edição web. Na nova campanha é o confronto intermediário do mundo 9.
Ainda melhorar: descanso central mantido; aumentar densidade de inimigos e adicionar terceira relíquia.

## Prioridades derivadas

1. Densidade e variedade de inimigos (todas): de 2–5 para 8–20 por fase, com ensino antes do teste.
2. Terceira relíquia e pelo menos uma rota opcional real em cada fase (feito no mundo 1).
3. Mecânica do mundo presente já nas fases legadas (vento no deserto, nevasca nas montanhas, galhos na floresta).
4. Reequilíbrio das fases do vulcão para a posição de mundo 9.
5. Conjuntos artísticos dedicados para os mundos 2, 4, 5 e 9 (em produção; a matriz indica o estado real).
