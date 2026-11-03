# Desempenho

Ferramenta: `python tools/profile_level.py <fase> --res 1920x1080 --seconds 14 --json artifacts/perf/<fase>_1920x1080.json`. O robô de rotas joga a fase enquanto cada quadro é renderizado a 60 Hz de tempo simulado; mede-se atualização da simulação, submissão dos comandos de desenho (Python), tempo de quadro completo **incluindo `present()`** (o SDL acumula comandos e só rasteriza no `present`), chamadas de desenho, entidades vivas e memória de texturas.

## Ambiente das medições

Contêiner de nuvem com 4 vCPUs Intel Xeon 2,8 GHz, **sem GPU**, Python 3.13, pygame-ce 2.5.8, SDL 2.32.10. Sem GPU, o SDL usa o renderizador **por software**: os tempos de quadro abaixo são um limite superior pessimista e **não representam** uma máquina com aceleração gráfica. Nenhum número de GPU foi medido (não há como medir aqui) — não há afirmação de 60 FPS em GPU neste relatório.

## Resultados medidos (renderizador por software)

Tabela gerada por `python tools/gen_docs.py` a partir de `artifacts/perf/*.json` (não editar à mão).

<!-- desempenho:inicio -->
| Mundo | Fase | Resolução | Simulação (ms, média / p95) | Submissão Python (ms) | Quadro completo (ms, média / p95 / máx.) | FPS equivalente | Desenhos (média / máx.) | Texturas (MB) | Pré-carga (ms) | Carga da máquina |
| ----- | ---- | --------- | --------------------------- | --------------------- | ----------------------------------------- | --------------- | ----------------------- | ------------- | -------------- | ---------------- |
| 1 | 1 · Primeiros Passos | 1280×720 | 0,65 / 0,95 | 2,25 | 12,3 / 16,4 / 33,6 | ≈ 82 | 68 / 111 | 31,4 | 390 | não registrada |
| 1 | 1 · Primeiros Passos | 1920×1080 | 0,66 / 1,12 | 2,36 | 29,6 / 42,5 / 58,0 | ≈ 34 | 68 / 111 | 69,8 | 753 | não registrada |
| 1 | 1 · Primeiros Passos | 3840×2160 | 0,66 / 1,07 | 2,58 | 124,0 / 153,7 / 196,1 | ≈ 8 | 68 / 113 | 285,7 | 2.619 | não registrada |
| 1 | 2 · Canais do Vale | 1920×1080 | 0,85 / 1,43 | 2,46 | 31,7 / 43,3 / 62,9 | ≈ 32 | 71 / 140 | 85,8 | 875 | não registrada |
| 1 | 3 · Guardião do Pomar | 1920×1080 | 0,72 / 1,30 | 2,42 | 33,8 / 51,6 / 74,6 | ≈ 30 | 70 / 137 | 87,2 | 899 | não registrada |
| 1 | 4 · Colina dos Moinhos | 1920×1080 | 0,83 / 1,40 | 2,54 | 34,4 / 48,3 / 64,4 | ≈ 29 | 65 / 107 | 95,8 | 1.039 | não registrada |
| 1 | 5 · Tocas do Prado | 1920×1080 | 0,77 / 1,37 | 2,16 | 28,5 / 40,4 / 53,8 | ≈ 35 | 56 / 97 | 119,0 | 1.544 | não registrada |
| 1 | 6 · Fortaleza do Espinheiro | 1920×1080 | 0,82 / 1,58 | 2,11 | 12,4 / 19,8 / 35,1 | ≈ 80 | 38 / 75 | 91,2 | 1.045 | não registrada |
| 2 | 1 · Dunas ao Vento | 1920×1080 | 0,69 / 1,23 | 2,76 | 49,6 / 73,5 / 91,2 | ≈ 20 | 74 / 122 | 78,6 | 391 | 1,19/4 CPUs |
| 2 | 2 · Pontes do Cânion | 1920×1080 | 0,86 / 1,42 | 2,89 | 50,2 / 71,0 / 101,2 | ≈ 20 | 87 / 138 | 82,1 | 390 | 1,1/4 CPUs |
| 2 | 3 · Templo das Areias | 1920×1080 | 0,69 / 1,06 | 2,74 | 49,4 / 60,2 / 88,8 | ≈ 20 | 75 / 125 | 81,7 | 430 | 1,1/4 CPUs |
| 2 | 4 · Passagem da Tempestade | 1920×1080 | 0,77 / 1,37 | 3,01 | 52,8 / 72,5 / 108,3 | ≈ 19 | 76 / 128 | 87,2 | 400 | 1,33/4 CPUs |
| 2 | 5 · Oásis Soterrado | 1920×1080 | 0,73 / 1,25 | 2,71 | 50,3 / 64,3 / 103,0 | ≈ 20 | 71 / 125 | 89,7 | 424 | 1,38/4 CPUs |
| 2 | 6 · Pirâmide do Escaravelho | 1920×1080 | 0,82 / 1,45 | 2,12 | 30,3 / 36,0 / 77,1 | ≈ 33 | 35 / 75 | 96,8 | 1.411 | 1,39/4 CPUs |
| 4 | 1 · Lago de Cristal | 1920×1080 | 0,63 / 1,05 | 2,84 | 54,3 / 73,1 / 102,1 | ≈ 18 | 82 / 130 | 73,2 | 1.925 | 1,57/4 CPUs |
| 4 | 2 · Escalada Azul | 1920×1080 | 0,77 / 1,20 | 2,78 | 54,1 / 71,8 / 104,2 | ≈ 18 | 83 / 136 | 78,5 | 1.112 | 1,72/4 CPUs |
| 4 | 3 · Coração da Nevasca | 1920×1080 | 0,92 / 1,55 | 2,99 | 54,4 / 71,2 / 117,7 | ≈ 18 | 85 / 150 | 78,1 | 1.109 | 1,44/4 CPUs |
| 4 | 4 · Encostas Escorregadias | 1920×1080 | 0,96 / 1,68 | 3,33 | 53,1 / 65,3 / 97,8 | ≈ 19 | 83 / 153 | 86,0 | 1.580 | 1,22/4 CPUs |
| 4 | 5 · Cume da Avalanche | 1920×1080 | 0,87 / 1,52 | 3,27 | 57,6 / 74,6 / 107,3 | ≈ 17 | 82 / 134 | 89,4 | 1.550 | 1,3/4 CPUs |
| 4 | 6 · Cidadela de Geada | 1920×1080 | 0,95 / 1,68 | 2,76 | 42,4 / 68,4 / 113,8 | ≈ 24 | 56 / 106 | 119,3 | 3.002 | 1,89/4 CPUs |
| 5 | 1 · Copas Luminosas | 1920×1080 | 0,96 / 1,52 | 2,82 | 71,1 / 93,4 / 131,6 | ≈ 14 | 77 / 138 | 97,7 | 1.339 | 1,67/4 CPUs |
| 5 | 2 · Ruínas dos Vagalumes | 1920×1080 | 0,71 / 1,13 | 2,68 | 69,5 / 92,9 / 156,3 | ≈ 14 | 76 / 130 | 101,2 | 1.274 | 2,05/4 CPUs |
| 5 | 3 · A Árvore Ancestral | 1920×1080 | 0,94 / 1,54 | 2,79 | 69,6 / 88,7 / 138,8 | ≈ 14 | 78 / 134 | 100,5 | 1.495 | 2,25/4 CPUs |
| 9 | 1 · Pontes de Basalto | 1920×1080 | 0,87 / 1,30 | 2,86 | 48,9 / 58,1 / 85,3 | ≈ 20 | 89 / 148 | 74,5 | 1.505 | 2,19/4 CPUs |
| 9 | 2 · Fornalha dos Ecos | 1920×1080 | 0,98 / 1,54 | 2,93 | 51,0 / 62,5 / 99,9 | ≈ 20 | 90 / 140 | 77,6 | 1.096 | 1,85/4 CPUs |
| 9 | 3 · A Última Chama | 1920×1080 | 0,89 / 1,59 | 3,04 | 49,0 / 63,9 / 95,7 | ≈ 20 | 76 / 129 | 78,9 | 1.128 | 1,87/4 CPUs |
<!-- desempenho:fim -->

Leitura:

- **A lógica do jogo cabe folgada**: simulação de 2 passos de 1/120 s por quadro custa < 1 ms em média e < 1,6 ms no p95, com até 104 entidades vivas (inimigos ativos, projéteis e partículas).
- **O custo Python de desenhar** um quadro é ~2,1–2,6 ms em qualquer resolução (≈ 60–140 chamadas). Isso deixa margem para 60 FPS em 1080p e 4K quando a rasterização é feita pela GPU.
- **No software**, o gargalo é rasterizar camadas de tela cheia com transparência (céu, três parallax, nuvens): ≈ 30 ms em 1080p ao ar livre e ≈ 12 ms em interiores. Por isso, sem GPU, a resolução automática fica em 1280 × 720 (≈ 81 FPS).
- **Sem travadas de carregamento durante o jogo**: o pior quadro (máx.) após a pré-carga vem de picos de partículas, não de rasterização; antes da pré-carga havia quadros de 180–340 ms.
- **Memória de texturas**: 31 MB (720p), 70–119 MB (1080p) e 286 MB (4K) por fase, limitada por orçamento LRU (768 MB) e descarregamento por mundo/fase.

## Otimizações implementadas

- Índice espacial de colisões por colunas de 256 u (`CollisionIndex`), testando só plataformas próximas e mantendo a ordem de resolução original.
- Ativação de inimigos perto da vista (ninguém se move fora da tela antes de ser visto).
- Recorte por visibilidade de terreno, adereços, moedas, perigos e criaturas.
- Rasterização uma vez por densidade, cache em disco, pré-carga por fase, descarregamento por grupo, LRU com orçamento.
- Partículas com limite (600 com efeitos, 120 sem) e clima reduzido na qualidade Baixa.
- Predefinições de qualidade: Alta (tudo em densidade total), Média (fundos distantes a 75%), Baixa (fundos a 60%, menos clima). Personagens, terreno, objetos e HUD nunca perdem densidade.

## Pendências

- Medir em máquinas com GPU (Windows/macOS/Linux) em 1080p e 4K e registrar os resultados aqui.
- Se o 4K em GPUs integradas ficar abaixo de 60 FPS, avaliar atlas de texturas para os adereços e um caminho ModernGL para as camadas de fundo.
