# Arquitetura das fases (formato `lume.level`)

Este documento descreve como as fases da edição Python são definidas, carregadas, validadas e executadas. O código citado está em `lume/levels/` e `lume/core/`.

## 1. Princípios

- **Dados, não código.** Cada fase é um arquivo JSON em `lume/data/levels/<mundo>/<fase>.json`. Nenhuma coordenada de fase vive em código Python.
- **Identidade estável.** Fases e mundos são identificados por IDs (`first_steps`, `green_kingdom`), nunca pela posição no menu nem pelo nome do arquivo. A ordem vem de `lume/data/campaign.json`; trocar a ordem dos mundos não altera IDs nem salvamentos.
- **Definições reutilizáveis.** Espécies de inimigos são definidas uma vez em `lume/data/enemies.json` (ver `REGISTRO_INIMIGOS.md`); a fase só referencia a espécie e sua posição.
- **Validação em três níveis.** Sintaxe/tipos (`schema.py`), significado (`validate.py`) e execução real (robô de rotas em `lume/qa/route_bot.py`).

## 2. Registro da campanha (`campaign.json`)

`format: "lume.campaign"`, `format_version: 1`. Lista os 10 mundos (id, nome, subtítulo, bioma, `legacy_world` quando o mundo vem da edição web, cor) e, em cada um, as 6 fases (id, nome). Uma fase listada sem arquivo é **planejada**: aparece no mapa como "em desenvolvimento" e não bloqueia a progressão (o desbloqueio pula vagas não implementadas — `CampaignView.next_after`).

## 3. Formato da fase (`format_version: 1`)

| Campo | Tipo | Observações |
| ----- | ---- | ----------- |
| `id`, `name`, `world` | texto | `id` em snake_case ASCII; `world` deve coincidir com o registro |
| `legacy_ids` | lista | IDs da edição web ("1-1"…"5-3"), usados na migração de salvamentos |
| `role` | enum | presentation, exploration, movement, special, advanced, fortress, secret, bonus |
| `difficulty` | 1–10 | curva da campanha |
| `art` | objeto | `set` (conjunto artístico do mundo), `variant`, `weather` |
| `music` | texto | `<mundo>_main`, `<mundo>_fortress`, `<mundo>_underground`, `boss`, `menu` |
| `bounds` | objeto | `width` (≥ 960), `height` (≥ 540) em unidades de mundo (u) |
| `areas` | lista | sub-áreas com limites de câmera próprios (salas secretas, túneis, interiores); `variant` "cave"/"fortress" troca o fundo |
| `time_limit`, `spawn` | número, ponto | `spawn` = canto superior esquerdo do jogador |
| `checkpoints` | lista | vários por fase; o reaparecimento usa o mais avançado alcançado |
| `exit` | objeto | `kind: flag`; `y` é a base da bandeira; bloqueada enquanto houver chefe vivo |
| `platforms` | lista | `kind`: ground, ledge, brick, question, hidden, moving, crumble, pipe, semisolid, conveyor, spring, switch; `style` escolhe a arte; `surface` ice/normal; `motion` (x, y ou circle); `warp`/`return` para canos; `secret`; `surface_speed`; `bounce`; `group`; `active` |
| `coins` / `coin_groups` | lista | grupos `row`, `arc`, `column`, `grid`, `diagonal` com IDs gerados estáveis (`grupo-1`…) |
| `collectibles` | lista | relíquias (meta: 3 por fase) |
| `items` | lista | grow, fire, star, heart |
| `enemies` | lista | `species`, `x`, `y` (linha dos pés), `patrol`, `hp` e `params` opcionais |
| `hazards` | lista | lava, water, spikes, moving (chama oscilante), thorns, electric, poison |
| `zones` | lista | swim, current, wind (com rajadas `period`/`duty`), dark, quicksand, lowgrav |
| `secrets` | lista | `kind` (warp_room, hidden_block, high_route, breakable_path, hidden_area, optional_challenge), `clue` (pista visual), `rewards`, `entry` |
| `hints` | lista | placas com texto; `y` opcional para áreas empilhadas |
| `decor` | lista | adereços explícitos; sem eles, o conjunto artístico distribui decoração determinística |
| `events` | lista | `boss_arena` (trava a câmera, fecha/abre portões), `camera_lock`, `message`; `rising_lava`, `lights` e `toggle_switch` estão reservados (ver §6) |

Exemplo mínimo: `tests/python/conftest.py` (`BASE_LEVEL`). Exemplo completo: `lume/data/levels/green_kingdom/bramble_fortress.json`.

### Unidades e física

1 u = 2 px em 1920×1080 antes do zoom de câmera (1,3). Constantes em `lume/core/constants.py`, preservadas da edição web: gravidade 1550 u/s², impulso 590 u/s (≈ 112 u de altura segurando o botão), corrida 340 u/s, alcance de salto correndo ≈ 259 u, jogador 22 × 30 u (pequeno) ou 22 × 46 u (grande).

## 4. Carregamento e erros

`load_campaign()` lê o registro, carrega cada arquivo existente e reúne **todos** os problemas antes de falhar (`DataError` com lista de `Problem(source, path, message)`). Cada problema indica o caminho JSON exato, por exemplo `levels/green_kingdom/windmill_heights.json:platforms[12].motion.axis: valor 'z' inválido`. Campos desconhecidos são erro (pegam erros de digitação).

## 5. Validação semântica (`lume/levels/validate.py`)

- referências: espécies existentes e com comportamento implementado; recompensas e entradas de segredos existentes; destinos de canos dentro dos limites e com chão;
- **bioma**: cada espécie só aparece em mundos cujo bioma está nos seus `habitats` (sub-áreas underground/fortress/underwater aceitam espécies desses biomas);
- **ordem de ensino**: a primeira aparição de cada espécie na ordem da campanha deve ser exatamente a fase `introduced_in` do registro;
- segurança: inimigos longe do ponto de partida; perigos longe de spawn/checkpoints; simulação de 90 passos a partir de cada ponto de partida;
- saída apoiada em terreno; fortaleza com chefe; ao menos uma relíquia; plataformas interativas não podem estar enterradas no terreno;
- **vãos do caminho principal** simulados com a física real (`move_body`) para jogador pequeno e grande e cinco pontos de impulso; vãos atravessados por plataformas móveis ou intermediárias são delegados à rota automatizada (aviso registrado).

Executar: `python -m lume --validate`.

## 6. Execução (`lume/core/game.py`)

Passo fixo de 1/120 s, mesma ordem de operações da edição web: plataformas → jogador (entrada, coyote time, buffer de salto, corte de salto, gravidade, colisão por eixo) → interações (blocos, moedas, checkpoints, canos, eventos) → inimigos → poderes/projéteis/perigos → saída → partículas → câmera. Extensões: índice espacial de colisões, ativação de inimigos perto da vista, natação, deriva de vento/correntes/esteiras, molas (sem corte de salto até o ápice), portões de arena, reinício do chefe quando Lume morre na arena.

Recursos **reservados no formato e ainda não implementados no motor**: `rising_lava`, `lights` (máscara de escuridão) e `toggle_switch` (blocos liga/desliga por interruptor), física de `quicksand`, paredes quebráveis lateralmente. O planejamento das fases marca essas dependências em `engine_requirements`.

## 7. Fases legadas

`tools/export_legacy_levels.mjs` exporta `src/data/levels.ts` exatamente como a versão web o vê; `tools/convert_legacy_levels.py` converte para o formato acima: IDs estáveis com `legacy_ids`, tipos genéricos de inimigo trocados por espécies nativas de cada bioma com a mesma caixa de colisão e ajuste, salas secretas no céu transformadas em câmaras subterrâneas (+720 u) com paredes, piso e teto, moedas reagrupadas em `coin_groups`. Revisões posteriores são feitas diretamente no JSON e registradas em `notes`.

## 8. Como criar uma fase

1. Adicionar o ID no mundo em `campaign.json` (ou usar uma vaga planejada).
2. Criar o JSON seguindo a ficha em `docs/level_design/PLANEJAMENTO_60_FASES.md`.
3. `python -m lume --validate` até não haver erros.
4. `python -m pytest tests/python -k <id>` (estrutura, rota, renderização) e `python tools/capture_level.py <id> artifacts/shots --res 1920x1080 --at 300,1500` para revisão visual.
5. `python tools/profile_level.py <id> --json artifacts/perf/<id>_1920x1080.json` e `python tools/quality_matrix.py --render`.
