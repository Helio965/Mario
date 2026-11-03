# Testes

Estado em 3 de novembro de 2026 (atualizado a cada marco). Executar com o ambiente virtual ativo:

```bash
python -m pytest -q
```

Os testes nunca abrem janela nem dispositivo de áudio: `tests/conftest.py` define `SDL_VIDEODRIVER=dummy` e `SDL_AUDIODRIVER=dummy`.

## Estrutura

| Diretório | Conteúdo |
| --- | --- |
| `tests/unit` | Lógica pura: física (legado e calibrado), colisões, interações, combate, chefes, fases, progressão, salvamento, dados das fases, validador, animação, FSM/percepção, diálogos e **traces de ouro** |
| `tests/gameplay` | Campanha jogada por entradas normais (condutor em `route_player.py`), nos dois perfis de física |
| `tests/integration` | Renderização, áudio e interface em modo headless (produzidos no Marco 3) |
| `tests/performance` | Medições reais impressas com `-s` (sem valores inventados) |
| `tests/fixtures/golden` | 20 gravações do motor TypeScript de referência (entradas tick a tick + posições + eventos) e, em `levels/`, a cópia congelada das 15 fases como exportadas do TypeScript |
| `tests/support` | Robô de justiça dos guardiões (`fairness_bot.py`), partilhado pelos testes de unidade e pelo condutor de campanha |

## Port dos testes originais

Os 88 testes Vitest foram portados um a um (mesmos cenários e asserções):

| Origem (TS) | Destino (Python) | Casos |
| --- | --- | --- |
| `physics.test.ts` | `tests/unit/test_physics.py` | 5 |
| `physics-extra.test.ts` | `tests/unit/test_physics_extra.py` | 8 |
| `interactions.test.ts` | `tests/unit/test_interactions.py` | 4 |
| `combat.test.ts` | `tests/unit/test_combat.py` | 8 |
| `bosses.test.ts` | `tests/unit/test_bosses.py` | 1 + 5 × 4 + 3 |
| `levels.test.ts` | `tests/unit/test_levels.py` | 1 + 15 |
| `progression.test.ts` | `tests/unit/test_progression.py` | 2 |
| `save.test.ts` | `tests/unit/test_save.py` | 4 (+2 novos: arquivo atômico e importação do navegador) |
| `routes.test.ts` | `tests/gameplay/test_first_level_route.py` | 1 |
| `campaign-routes.test.ts` + `route-player.ts` | `tests/gameplay/test_campaign_routes.py` + `route_player.py` | 15 (+ comparação das entradas com o condutor TS) |

Os 15 testes Playwright (menus, teclado, pausa, persistência, áudio, gamepad, toque, produção) são substituídos por testes headless de interface/áudio/aplicação no Marco 3; toque e build web ficam registrados como limitação até a etapa Pygbag.

## Validação diferencial (traces de ouro)

`tests/unit/test_golden_traces.py` reproduz, no motor Python, as entradas gravadas com o motor TypeScript e exige, a cada 4 ticks, posição do jogador igual (tolerância 0,001 px), eventos idênticos (tipo e tick) e instantâneos completos a cada segundo (inimigos, itens, projéteis, blocos usados, moedas, câmera, pontuação, tempo). Cobertura: 15 rotas de campanha, 4 sequências pseudoaleatórias (1-1, 2-2, 3-2, 5-3) e uma arena de combate com todos os tipos de inimigo, itens, gelo, teto, plataforma móvel e frágil. Os traces e o condutor diferencial (`test_campaign_routes.py`) usam a cópia congelada das fases (`tests/fixtures/golden/levels/`), porque `data/levels` já mudou (guardiões nas arenas). O gerador (`tools/legacy-golden/`) existe enquanto o TypeScript existir.

## Testes novos (além do port)

- `test_level_data.py`: totais e ida-e-volta do JSON das fases contra a exportação original.
- `test_level_validator.py`: esquema, suporte, canos, patrulhas e viabilidade dos vãos do caminho principal com a física real (ambos os perfis).
- `test_physics_calibrated.py`: previsões analíticas × simulação discreta, salto mínimo, arrancada, frenagem, derrapagem, sem atrito aéreo, graça da corrida, empurrão de teto, dano sem empurrão.
- `test_animation.py`: máquina de estados de animação dirigida pela física real e por eventos.
- `test_state_machine.py`: FSM declarativa e percepção (tempo de reação, esquecimento, linha de visão, bordas e paredes).
- `test_dialogue.py`: diálogos, máquina de escrever, condições, pular, reações sem repetição.
- `test_profiles_routes.py`: campanha **atual** (com os cinco guardiões) com previsão de pouso nos dois perfis; nas arenas o condutor entrega o controle ao robô de justiça. Uma fase do perfil calibrado (2-3, travessia) é falha esperada documentada em `docs/FISICA.md`.
- `test_guardians.py`: invariantes dos guardiões e combates do robô de justiça (ver `docs/CHEFES.md`).
- `tests/performance/test_simulation_perf.py`: µs por passo com 10/50/200 inimigos e passos/s na fase 5-3.

## Resultado atual

```text
tests/unit + tests/gameplay: ? testes aprovados, 0 xfail (perfil calibrado em 2-3, travessia)
  — a única falha do momento é um teste da família "explosivos/aquáticos" ainda em
    escrita pelo fluxo de arquétipos (0 falha, fora deste commit)
tests/integration: aprovados (renderização, áudio e interface sem janela)
ruff check / ruff format --check: limpos
mypy --strict (pacote game): limpo
```

Guardiões na campanha (condutor + robô de justiça, previsão de pouso):
perfil legado 15/15 fases sem perder vida; perfil calibrado 14/15 (2-3 presa na
travessia antes da arena; 3-3 perde uma vida no gelo, não na arena).

Os totais serão atualizados ao fim de cada marco; nenhum número aqui é projetado.
