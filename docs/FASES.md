# Lume — desenho e validação das 15 fases

As fases vivem em `data/levels/*.json` (formato `lume-level/1`, índice e temas em `index.json`), carregadas por `game/levels/loader.py` e validadas por `game/levels/validator.py`. A exportação original do TypeScript está congelada em `tests/fixtures/golden/levels/` e serve aos testes diferenciais; `data/levels` evolui com a reconstrução (os cinco guardiões já estão nas arenas). A primeira fase introduz a campanha; o traçado, as rotas altas e os encontros de cada fase são escritos explicitamente.

## Percurso e progressão

| Fase | Nome                 | Largura | Composição e recompensa                                                        | Vãos do caminho principal   | Guardião |
| ---- | -------------------- | ------: | ------------------------------------------------------------------------------ | --------------------------- | ----- |
| 1-1  | Primeiros Passos     |    3200 | Introdução ao salto, blocos luminosos, dois vãos, subida curta e primeiro cano | 100 / 120                   | —     |
| 1-2  | Canais do Vale       |    3500 | Margem elevada, plataforma ascendente e aqueduto com relíquia                  | 100 / 120 / 140             | —     |
| 1-3  | Guardião do Pomar    |    3900 | Pomar, degraus de pedra, ponte frágil e arena aberta                           | 120 / 100 / 100             | Rolão, 3 golpes |
| 2-1  | Dunas ao Vento       |    3800 | Colunas de canos, escada de arenito, primeiro sentinela e espinhos             | 120 / 130 / 130             | —     |
| 2-2  | Pontes do Cânion     |    4100 | Terraços ascendentes e descendentes, rota frágil e chama móvel                 | 120 / 130 / 120 / 120       | —     |
| 2-3  | Templo das Areias    |    4200 | Escadaria arqueológica, inimigo blindado e corredor para o templo              | 110 / 110 / 120             | Oculus, 3 golpes |
| 3-1  | Lago de Cristal      |    3600 | Longas margens de gelo com frenagem, degraus gelados e abrigo central          | 120 / 120 / 120             | —     |
| 3-2  | Escalada Azul        |    4400 | Seis terraços, subida total de 80 px e descida em dois degraus                 | 110 / 120 / 120 / 110 / 120 | —     |
| 3-3  | Coração da Nevasca   |    4600 | Gelo alternado com rocha, relíquia sobre plataforma e arena seca               | 120 / 110 / 120 / 120       | Brumo, 3 golpes |
| 4-1  | Copas Luminosas      |    4000 | Copa frágil de três alturas, rota móvel e chão inferior contínuo por trecho    | 110 / 120 / 120             | —     |
| 4-2  | Ruínas dos Vagalumes |    4500 | Bloco oculto, salão de canos, terraço com chama e segunda escadaria            | 120 / 120 / 120 / 120       | —     |
| 4-3  | A Árvore Ancestral   |    4700 | Duas subidas distintas, sentinela na aproximação e árvore guardiã              | 120 / 120 / 120 / 120       | Lumiá, 4 golpes |
| 5-1  | Pontes de Basalto    |    4300 | Quatro canais de lava, desvio alto da chama e abrigo antes da chegada          | 110 / 120 / 120 / 120       | —     |
| 5-2  | Fornalha dos Ecos    |    4800 | Terraços de fornalha, galeria frágil, chamas e aterrissagens largas            | 120 / 120 / 120 / 120 / 120 | —     |
| 5-3  | A Última Chama       |    5200 | Síntese das mecânicas, relíquias altas, descanso central e arena final         | 120 / 120 / 120 / 120 / 120 | Fornalho, 5 golpes |

Há 572 moedas declaradas, incluindo 29 relíquias, e 49 inimigos, incluindo os cinco guardiões (`rolao`, `oculus`, `brumo`, `lumia`, `fornalho`; ver `docs/CHEFES.md`). A primeira fase tem uma relíquia na sala secreta; as outras têm uma nessa sala e outra em uma rota alta. Recompensas de blocos, itens de chão e dicas variam conforme o trecho. Nenhum salto do caminho principal depende de uma plataforma móvel ou frágil.

## Física e alcance

Os cálculos usam as constantes reais do jogo: gravidade de 1550 px/s², impulso de 590 px/s, corrida de 340 px/s e jogador de 22 × 30 ou 22 × 46 px. Ao manter o botão de salto, a altura teórica é 112,3 px, o tempo de voo até a altura inicial é 0,761 s e o alcance horizontal é 258,8 px. A corrida partindo do repouso precisa de aproximadamente 42 px de pista com aceleração de 1400 px/s².

O maior vão é 140 px. Os demais ficam entre 100 e 130 px. A maior subida em uma única transição do chão é 48 px, ainda deixando cerca de 227 px de alcance no arco descendente. Terrenos de partida e chegada têm pelo menos 520 px de comprimento; as aterrissagens deixam espaço para desacelerar. Degraus opcionais têm desníveis de até 78 px e separações que cabem no alcance descendente. Plataformas móveis opcionais ficam afastadas do ponto de salto obrigatório de cada vão.

## Verificações executadas

- TypeScript com `strict: true`: zero diagnósticos ao resolver os tipos de `src/core/types.ts`.
- Validação geométrica dos 15 mapas: todos os IDs são únicos; os vãos e desníveis respeitam os limites; spawn e checkpoint têm chão seguro; todos os destinos de cano possuem apoio; cada fase tem relíquia; as fases 3 de cada mundo têm exatamente um guardião (`is_boss_kind`).
- Simulação de **440 saltos obrigatórios** com a implementação real de `moveBody`, gravidade real e passo de 1/120 s: 55 vãos × duas alturas de jogador × quatro fases do movimento das plataformas. **440 casos passaram** após deslocar quatro plataformas móveis que inicialmente interrompiam o salto direto. A simulação procurou pontos de impulsão entre 0 e 120 px antes da borda e manteve a corrida e o salto até aterrissar no próximo terreno.
- Os cinco guardiões patrulham arenas de solo contínuo (patrulhas de 580 a 800 px). A bandeira fica dentro ou logo após a arena e a saída só abre com o guardião derrotado (`Game.boss()`). Nenhum guardião, espinho ou canal de lava é colocado no spawn ou no checkpoint.
- As salas ficam em y176, com jogador aparecendo em y126. O cano de saída fica em y144, a 32 px do piso. A volta usa `destination` explícito para o chão principal; `returnPoint` também documenta o retorno. As salas ficam acessíveis exclusivamente pelo cano de entrada, sem exigir uma subida impossível.

## Limites da validação

A simulação de saltos verifica colisões com o cenário e os extremos amostrados do movimento; ela não é uma partida completa. A validação posterior de campanha percorreu as quinze fases com inimigos, perigos e chefes ativos por comandos normais; veja `docs/VALIDACAO.md`. A sensação de controle e leitura visual ainda depende da experiência de jogadores, e rotas opcionais não foram todas percorridas. As passagens principais têm chão para esperar antes dos encontros. As relíquias opcionais em plataformas móveis pressupõem que o jogador observe o ciclo e conserve uma plataforma inferior; nenhuma delas impede terminar a fase.

As coordenadas de spawn/checkpoint/teleporte são o canto superior esquerdo do jogador; `exit.y = 448` é a base da bandeira. O chão alcança abaixo da tela para fechar visualmente o terreno. As câmaras usam a parte superior da tela padrão de 960 × 540, dispensando uma câmera vertical ou níveis mais altos.

## Arenas dos guardiões (ajustes de 3 de novembro de 2026)

Ao trocar o chefe legado (`kind: "boss"`, 62 × 64) pelos guardiões, as arenas das
fases 3 foram abertas para os ataques novos (investidas até a parede, rochas que
entram pelas bordas, clones a 25 %/75 % da patrulha) e limpas de blocos que
ficavam sobre os pontos de salto:

| Fase | Guardião (tamanho) | Patrulha anterior → atual | Outras mudanças |
| --- | --- | --- | --- |
| 1-3 | Rolão 64 × 58 | 3190–3660 → 2950–3700 | tijolo `1-3-brick-4` (3100, y 374) removido da arena |
| 2-3 | Oculus 56 × 80, flutua 4 px | 3440–3980 → 3260–3980 | bloco estrela `2-3-question-4` de x 3200 para 3000 |
| 3-3 | Brumo 92 × 76 | 3870–4370 → 3890–4470 | laje de gelo `3-3-ice-4` de x 3760 para 3620 |
| 4-3 | Lumiá 48 × 64, poleiro a 96 px | 3980–4470 → 3840–4500 | bloco coração `4-3-question-4` de x 3770 para 3700 |
| 5-3 | Fornalho 84 × 88 | 4630–4970 → 4530–5120 | — |

Os guardiões definem a própria vida (`BossDefinition.hp`); o campo `hp` saiu
dessas entradas. As mecânicas de arena da pesquisa (ponte frágil, placas,
buracos no gelo, lava cíclica, corredor com alavanca) continuam pendentes.
