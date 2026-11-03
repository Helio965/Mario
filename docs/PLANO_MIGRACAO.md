# Plano de migração TypeScript → Python

Referência: commit `b40c39ca77026de4101817b8a8f7198f6e870ab9`. Branch de trabalho: `claude/focused-pascal-hg2kgb`.

## Princípios

1. O código TypeScript é a **especificação executável** até a conclusão: nada é apagado antes de a versão Python passar nos testes equivalentes e nos traces de ouro.
2. Lógica de jogo em Python puro (`game/core`, `game/physics`, `game/enemies`, `game/bosses`, `game/characters`, `game/systems/save.py`, `game/systems/progression.py`) **sem importar pygame**, para manter a simulação testável e determinística.
3. pygame-ce só em `game/application.py`, `game/rendering`, `game/systems/{input,audio}.py` e `game/ui`.
4. Dados declarativos em `data/` (JSON validado); textos em `data/locales/`.
5. Cada marco tem testes próprios e commit próprio.

## Tecnologia

| Papel | Escolha | Justificativa |
| --- | --- | --- |
| Linguagem | Python 3.12 (verificado 3.12.3; compatível com 3.13) | Estável, tipagem moderna, `match`, dataclasses com `slots` |
| Motor | pygame-ce 2.5.8 | SDL2, `pygame.SCALED`, `Surface.blits`, `freetype`, `sndarray`, joystick; comunidade ativa e documentação atual |
| Áudio | `numpy` + `pygame.sndarray` | Síntese chiptune original em tempo de carga, sem arquivos proprietários |
| Imagens | Pillow (ferramentas) | Pipeline reproduzível de spritesheets |
| Testes | pytest (+ `SDL_VIDEODRIVER=dummy`, `SDL_AUDIODRIVER=dummy`) | Headless em CI |
| Qualidade | ruff, mypy | Lint/format e tipagem |
| Empacotamento | PyInstaller (Windows) | Investigação Pygbag para navegador |

## Correspondência dos sistemas

| Origem (TS) | Destino (Python) | Estratégia |
| --- | --- | --- |
| `src/core/types.ts` | `game/core/entity.py`, `game/core/types.py` | dataclasses com `slots`; enums como `Literal`/`StrEnum` |
| `src/core/physics.ts` | `game/physics/collision.py`, `game/physics/constants.py` | port 1:1 (`overlaps`, `approach`, `move_body`) |
| `src/core/game.ts` | `game/core/game.py`, `game/core/camera.py` | port 1:1 do passo; câmera extraída |
| `src/core/interactions.ts` | `game/core/interactions.py` | port 1:1 |
| `src/core/enemies.ts` | `game/enemies/legacy.py` → depois `game/enemies/{enemy,behaviors,perception,state_machine}.py` | port 1:1 primeiro; FSM na etapa 6 |
| `src/core/bosses.ts` | `game/bosses/legacy.py` → depois `game/bosses/{boss,phases,attacks}.py` | idem |
| `src/core/powers.ts` | `game/characters/abilities.py` | port 1:1 |
| `src/core/progression.ts` | `game/systems/progression.py` | port 1:1 |
| `src/data/levels.ts` | `data/levels/*.json` + `game/levels/{loader,validator}.py` | exportado pelo TS; validador de esquema |
| `src/render/*` | `game/rendering/{painter,sprites,backgrounds,renderer,particles}.py` | reescrita em pygame, preservando a direção visual; pré-render de camadas |
| `src/systems/audio.ts` | `game/systems/audio.py` | síntese numpy + mixer, 4 barramentos |
| `src/systems/input.ts` | `game/systems/input.py` | eventos pygame + joystick; latch de taps |
| `src/systems/save.ts` | `game/systems/save.py` | sanitização portada; backend em arquivo atômico; v2 com migração |
| `src/systems/touch.ts` | — | sem equivalente desktop (registrado) |
| `src/ui/interface.ts`, `style.css` | `game/ui/{menu,world_map,settings,hud,screens}.py` | reescrita em pygame |
| `src/main.ts` | `main.py`, `game/application.py` | laço com passo fixo e renderização independente |
| `tests/unit/*.test.ts` | `tests/unit/*.py` | port 1:1 dos 88 testes |
| `tests/helpers/route-player.ts` | `tests/gameplay/route_player.py` | port 1:1 do condutor |
| `tests/browser/*` | `tests/integration/*` | fluxos equivalentes headless |
| `.github/workflows/pages.yml` | `.github/workflows/python.yml` | pytest + ruff + mypy |

## Etapas e critérios de conclusão

| Etapa | Entrega | Critério objetivo |
| --- | --- | --- |
| M1 Auditoria | `docs/AUDITORIA_INICIAL.md`, este plano, `data/levels/*.json`, traces de ouro | documentos escritos; 15 JSON com totais iguais ao TS |
| M2 Núcleo Python | `game/core`, `game/physics`, port dos sistemas de lógica | 88 testes portados passando; traces de ouro reproduzidos (posição do jogador ≤ 0,01 px em todos os ticks amostrados) |
| M3 Aplicação | `main.py`, renderização, áudio, entrada, UI, salvamento | campanha jogável de ponta a ponta sem Node; testes headless passando |
| Limpeza | remoção do TS, README, CI | `rg -l "\\.ts$"` vazio fora de `.git`; `python main.py` inicia; suíte completa verde |
| M4+ | evolução (física calibrada, animação, IA, chefes, arte, áudio, UI, desempenho, distribuição) | testes dedicados por marco |

## Semântica JS → Python a observar

- `Math.round(x)` arredonda 0,5 para +∞: usar `math.floor(x + 0.5)`.
- `%` do JS é resto com sinal do dividendo: usar `math.fmod` onde valores negativos forem possíveis.
- `Math.min(dt, 0.25)` com `NaN` retorna `NaN`; em Python `min` não. Validar `dt` finito.
- Acumulador de passo fixo: mesma sequência de operações em `float` para manter o teste de 30/60/144 Hz.
- `Number.isFinite`, `Number.MAX_SAFE_INTEGER` → `math.isfinite`, `2**53 − 1`.
- Ordem de iteração de arrays/`Map` é preservada com listas/dicts.
- `Array.prototype.find` → próximo `next((... ), None)`.
