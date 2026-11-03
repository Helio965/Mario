# Arquitetura Python

Estado em 3 de novembro de 2026. Toda a lógica do jogo é Python 3.12; pygame-ce 2.5.8 só aparece nas camadas de apresentação e entrada.

## Camadas

```text
main.py                      ponto de entrada (python main.py / lume)
game/application.py          janela, laço, métricas, integração dos sistemas (pygame)
├── game/core/               simulação pura: Game (passo fixo 1/120 s), tipos, interações
├── game/physics/            perfis de movimento (legado/calibrado), colisões AABB
├── game/characters/         poderes, elenco (deltas/habilidades), máquina de animação
├── game/enemies/            legado (port fiel) + arquétipos modernos (FSM, percepção, registro)
├── game/bosses/             guardião legado + motor genérico de chefes (fases/ataques)
├── game/npc/                diálogos, reações, (rotinas e NPCs: próximos marcos)
├── game/levels/             carregador JSON das fases e validador (esquema + física)
├── game/systems/            salvamento (arquivo atômico v2), progressão, localização,
│                            entrada (teclado/gamepad), áudio sintetizado (pygame)
├── game/rendering/          pintor com transformações, cenários, sprites, compositor (pygame)
└── game/ui/                 menus, mapa, configurações, HUD, telas de estado (pygame)
data/levels/*.json           15 fases (formato lume-level/1) + index.json com temas
data/characters/*.json       elenco
data/dialogues/*.json        roteiros
data/locales/*.json          textos (pt-BR principal, en-US)
tests/                       unit · gameplay · integration · performance · fixtures/golden
tools/                       capturas, áudio exportado, importação do salvamento, gerador legado de traces
```

Regra: `game/core`, `game/physics`, `game/characters`, `game/enemies`, `game/bosses`, `game/npc`, `game/levels` e `game/systems/{save,progression,localization}` **não importam pygame**. Isso mantém a simulação determinística e testável headless, e permite que o condutor de campanha e o validador usem o motor real.

## Fluxo de um quadro

1. `Application.frame(dt)`: processa eventos SDL (sair, foco, F11, UI, entrada), lê `InputState` (com latch de toques curtos).
2. `Game.update(dt, input)`: acumula o tempo real e executa `step(1/120)` quantas vezes couberem (máx. 0,25 s por quadro).
3. `Game.step`: cronômetro, plataformas, atordoamento/agachamento/carga, movimento horizontal (modelo do perfil), salto (coyote/buffer/carga), gravidade (simétrica ou assimétrica, scuttle), flutuação, colisão, limites, interações (blocos/moedas/checkpoint/canos), inimigos legados, arquétipos modernos (percepção → FSM → movimento → física → contato), poderes/itens/projéteis/perigos, saída (bloqueada por chefe vivo), partículas, animação legada e câmera.
4. `Application.drain_events`: eventos → áudio (`effect`), avisos localizados, conquistas, conclusão de fase e salvamento.
5. Renderização em `Surface` 960 × 540 (`Renderer.render` ou `backdrop`), interface por cima (`Interface.draw`), `pygame.SCALED` escala para a janela.

## Decisões técnicas

| Decisão | Motivo |
| --- | --- |
| Port 1:1 do núcleo antes de qualquer melhoria | preservar funcionalidades; validação diferencial com 20 traces do motor TS |
| Perfis de física (`MovementProfile`) em vez de constantes | manter o legado intocado e introduzir o modelo calibrado pela pesquisa sem reescrever o passo |
| Arquétipos modernos como novos `kind` no JSON, legados intocados | sem flags globais; os 15 mapas continuam idênticos; mapas novos usam a IA nova |
| FSM declarativa + percepção observável + tempos de reação | comportamento justo e aprendível; testável sem renderização |
| Chefes por `BossDefinition` com invariantes verificadas | telegraph mínimo, recuperação e fases que mudam o conjunto de ataques são checados por teste |
| Elenco por deltas limitados por envelope | nenhuma fase obrigatória fica impossível (verificado pelo validador com a física real) |
| Salvamento v2 em arquivo com escrita atômica e migração v1 | substituir `localStorage` sem perder progresso; importação manual do navegador |
| Dados em JSON + validador | formato declarativo para o editor; esquema e geometria verificados |
| Síntese de áudio em numpy | nenhum arquivo proprietário; trilhas/efeitos originais gerados em tempo de carga |
| Localização em arquivos | textos fora das classes; `locale.missing` vazio verificado em teste |

## Convenções

- Unidades: px, px/s, px/s², segundos; passo fixo 1/120 s.
- Coordenadas: origem no canto superior esquerdo; `spawn`/`checkpoint`/destinos de cano são o canto superior esquerdo do jogador; `exit.y` é a base da bandeira.
- Eventos (`GameEvent.type`): `jump, coin, relic, block, power, hurt, death, stomp, shot, checkpoint, secret, complete, boss, life, boss_intro, boss_phase`.
- Qualidade: `ruff` (lint + formato, linha 100), `mypy --strict` no pacote `game`, `pytest` com SDL dummy.
- Semântica JS → Python preservada onde importa: `Math.round` → `floor(x + 0.5)`, `%` → `math.fmod`, acumulador de passo fixo idêntico.
