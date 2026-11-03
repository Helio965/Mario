# Desempenho

Todos os números abaixo foram **medidos** nesta máquina de desenvolvimento (contêiner Linux, 4 vCPUs, Python 3.12.3, pygame-ce 2.5.8) com `python -m pytest tests/performance -s`. Nenhum valor é projetado; onde não houve medição, está escrito "pendente".

## Simulação (sem renderização)

| Cenário | Custo por passo (1/120 s) | Fração do orçamento |
| --- | ---: | ---: |
| 10 inimigos, 20 plataformas | 71 µs | 0,9 % |
| 50 inimigos, 60 plataformas | 524 µs | 6,3 % |
| 200 inimigos, 120 plataformas | 3 330 µs | 40 % |
| Fase 5-3 real (7 inimigos) | 70 µs → 14 300 passos/s (119× tempo real) | 0,8 % |

Leitura: a campanha atual (≤ 7 inimigos por fase) usa menos de 1 % do orçamento por passo. O custo cresce com o quadrado do número de inimigos (colisão casco × inimigos e sonda de plataformas por inimigo). Partição espacial só se justificará em fases com dezenas de inimigos simultâneos.

## Renderização

Medições do compositor pygame (`Renderer.stats`, `tests/integration/test_rendering.py::performance`): **pendente** nesta revisão — os números do agente de renderização serão registrados aqui após a revisão adversarial do módulo.

## Laço da aplicação

`Application` mantém uma janela móvel de 120 quadros com FPS médio, FPS mínimo, tempo por quadro e custo de física/renderização/interface (`FrameStats`), exibidos no HUD quando `show_fps` está ativo. Limite de FPS configurável (30/60/120/144/sem limite) via `Clock.tick`. Medições com janela real: **pendente** (ambiente sem tela; a execução headless com `--headless-frames` mede apenas CPU).

## Método

- `tests/performance/test_simulation_perf.py`: aquecimento de 60 passos, medição de 600 passos com `time.perf_counter`.
- Comparações entre máquinas devem repetir o comando; CI apenas verifica sanidade (passo < 90 % do orçamento).
