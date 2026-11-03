# Física do Lume (implementação)

Este documento descreve o que está **implementado e testado** em `game/physics` e `game/core/game.py`. A pesquisa que fundamenta os números está em `docs/research/FISICA.md` e `docs/research/MOVIMENTACAO.md`.

## Arquitetura

| Módulo | Papel |
| --- | --- |
| `game/physics/movement.py` | `MovementProfile` (parâmetros nomeados em px/s, px/s², s) com previsões analíticas (`jump_height`, `rise_time`, `fall_time`, `air_time`, `horizontal_range`, `min_jump_height`, `run_up_distance`, `braking_distance`); perfis `LEGACY_PROFILE` e `CALIBRATED_PROFILE`; `GRAVITY = 1550` é a gravidade do mundo (inimigos, itens, projéteis) e não muda com o perfil. |
| `game/physics/collision.py` | AABB (`overlaps`), `approach` e `move_body` (resolução por eixo X → Y contra plataformas vivas; blocos ocultos só colidem por baixo). |
| `game/core/game.py` | Passo fixo de 1/120 s com acumulador (`Game.update`), passo horizontal por modelo (`_horizontal_legacy` / `_horizontal_calibrated`), salto com coyote time e jump buffer, corte do salto, gravidade (simétrica ou assimétrica), velocidade terminal, empurrão de teto, câmera com antecipação. |

A simulação é Python puro, determinística e independente da taxa de renderização: o teste `test_same_result_at_30_60_and_144_hz` confirma o mesmo resultado a 30, 60 e 144 Hz.

## Perfil legado (padrão atual da campanha)

Reproduz byte a byte o motor TypeScript de referência; é validado pelos 20 traces de ouro (`tests/unit/test_golden_traces.py`) e pelas 15 rotas de campanha.

| Parâmetro | Valor | Observação |
| --- | ---: | --- |
| Caminhada / corrida | 220 / 340 px/s | |
| Aceleração no chão / no ar | 1400 / 1000 px/s² | mesma para arrancar e frear contra a direção |
| Atrito ao soltar (chão / gelo / ar) | 1500 / 180 / 500 px/s² | o atrito aéreo sem entrada encurta saltos ao soltar correr |
| Impulso de salto / corte ao soltar | 590 / −190 px/s | altura 112,3 px; salto mínimo ≈ 15 % do máximo |
| Gravidade / terminal | 1550 / 850 px/s² · px/s | arco simétrico: 0,381 s subida + 0,381 s descida |
| Coyote time / jump buffer | 0,10 / 0,12 s | |
| Dano | empurrão 100 px/s, 2,0 s de invulnerabilidade | |

## Perfil calibrado (novo motor, adoção planejada)

Decisões tomadas a partir da pesquisa, cada uma com o título de origem:

| Comportamento | Origem | Implementação |
| --- | --- | --- |
| Arco assimétrico: subida lenta (0,46 s) e descida firme (0,30 s), **mesma altura (112 px) e mesmo tempo total (0,76 s)** do legado, logo mesmo alcance (258 px a 340 px/s) | SMB1 (gravidade dupla), Swink/Pittman (projeto inverso) | `jump_speed = 487`, `gravity = 1059` (subida com botão), `gravity_fall = 2489` |
| Corte do salto = velocidade **e** gravidade de queda; salto mínimo ≈ 23 % do máximo (SMB1: 33 %) | SMB1 | `jump_cut_speed = 330` |
| Velocidade terminal 760 px/s e empurrão de +100 px/s ao bater a cabeça | SMB1 (+60 px/s escalado) | `terminal_velocity`, `ceiling_bump_speed` |
| Duas velocidades com arrancada mais lenta (0,43 s / 72 px até 340) | SMB1 "two speeds" (oficial), SMW | `walk_acceleration = 700`, `run_acceleration = 800` |
| Derrapagem com atrito dobrado e estado `skidding` visível | SMB1 | `skid_deceleration = 1800`, `skid_turn_speed = 80` |
| "Desacelera mais rápido do que acelera" ao soltar | SMW | `ground_friction = 900` |
| Sem atrito aéreo sem entrada; o teto aéreo preserva a velocidade atual | SMB1 | `air_friction = 0`, `cap = max(cap, min(|vx|, run))` |
| Graça de 0,17 s ao soltar correr | SMB1 `RunningTimer` | `run_release_grace` |
| Gelo reduz a tração (aceleração × 0,35), não só o atrito | SMW/SMB3 (ESTIMADO) | `ice_acceleration_multiplier`, `ice_skid_deceleration` |
| Dano sem empurrão, 2,6 s de invulnerabilidade | SMB1 | `hurt_knockback = 0`, `hurt_invulnerability = 2.6` |
| Coyote 5 quadros, buffer 6 quadros | prática moderna (sem precedente nos Mario) | `coyote_time = 5/60`, `jump_buffer = 6/60` |
| Bônus de corrida no salto | SMB1/SMB3/SMW | `run_jump_speed = None` (desligado) |

### Verificação matemática (tests/unit/test_physics_calibrated.py)

- Altura discreta ≈ `v0²/(2g) − v0·dt/2`, tempo até o ápice e tempo no ar dentro de 2–3 passos da previsão, nos dois perfis.
- Altura e tempo de voo do calibrado iguais ao legado (±1 px, ±0,01 s); razão de gravidades 2,35.
- Salto mínimo: legado 12–20 % do máximo; calibrado 20–30 %.
- Arrancada: distância ≈ 340²/(2·800) = 72 px em 0,40–0,46 s; frenagem ao soltar ≈ 64 px; derrapagem ≈ 32 px com `skidding` sinalizado.
- Sem atrito aéreo, graça da corrida e empurrão de teto verificados na simulação real.

### Estado da adoção

O perfil calibrado **não é o padrão** ainda. As 15 fases foram desenhadas para o legado e o condutor automático de campanha (`tests/gameplay/route_player.py`) foi calibrado para ele.

| Condutor | Perfil | Resultado |
| --- | --- | --- |
| Original (port fiel do TS) | legado | 15/15 concluídas (4-2 com duas mortes, 5-3 com uma) — entradas idênticas às do condutor TS |
| Com previsão de pouso (`smart_air`, simulação-sombra para escolher acelerar/soltar/frear no ar) | legado | **15/15 concluídas sem perder vidas** |
| Com previsão de pouso | calibrado | 14/15 (3-3 com uma vida perdida no gelo); pendente 2-3 — o condutor fica preso na travessia antes da arena. Nas arenas o controle passa ao robô de justiça, que prevê a trajetória com a gravidade e a aceleração aérea do perfil em uso |

Plano: adotar o calibrado como padrão junto com a reconstrução das fases (Marco 8), quando a travessia de 2-3 for revalidada. A opção de perfil fica exposta em `Game(levels, profile)`.

## Colisões

- Hitbox do jogador 22 × 30 (pequeno) / 22 × 46 (crescido); crescimento adiado sob teto baixo (`grow_safely`).
- Deslocamento máximo por passo (7,1 px vertical a 850 px/s; 2,8 px horizontal) é menor que qualquer espessura de plataforma (≥ 18 px), portanto não há tunelamento nas velocidades atuais. Um subpasso adicional será exigido se velocidades maiores forem introduzidas (mola, vento forte).
- Pisão: `vy > 0` e pé do jogador acima de `inimigo.y + min(24, vy·dt + 15)`.
- Perigos: lava e água matam mesmo invencível; espinhos e chamas ferem; perigo "moving" descreve um círculo senoidal.
- Plataformas móveis carregam o jogador por deslocamento (`dx`, `dy`) antes do passo; frágeis cedem após 0,65 s e voltam após 3 s se o jogador não estiver sobre elas.

## Limitações conhecidas

- Sem rampas, natação (água é perigo), agachamento físico, interação com paredes e vento: previstos como módulos opcionais do perfil (ver `docs/research/FISICA.md` §10.4) e dependentes de fases que os usem.
- A resolução de colisão segue a ordem de declaração das plataformas; quinas entre duas plataformas adjacentes podem escolher a segunda. Não houve caso observado nas 15 fases.
