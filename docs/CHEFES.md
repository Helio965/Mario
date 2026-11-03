# Chefes — os Cinco Guardiões do Lume (estado real da implementação)

Este documento descreve o que **existe no código** para os chefes: o motor de
chefes dirigido por dados (`game/bosses/boss.py`), as cinco definições dos
guardiões (`game/bosses/guardians.py`) e a validação automática de justiça
(`tests/unit/test_guardians.py`). A pesquisa que fundamenta os valores está em
`docs/research/CHEFES.md` (fichas dos chefes da série Mario 2D, §6 "Proposta:
os Cinco Guardiões"). Tudo o que ainda não foi feito está listado na seção 7.

## 1. Motor de chefes (`game/bosses/boss.py`)

Um chefe é uma `BossDefinition` interpretada por `GuardianBehavior`, um
arquétipo da máquina de estados comum aos inimigos (`game/enemies/state_machine.py`).

| Peça | O que define |
| --- | --- |
| `BossDefinition` | `kind`, `hp` (golpes), `world` (piso de telegraph), `hurt_time` (0,65 s imune após o golpe), `defeat_time`, `intro_distance` (520 px), `contact_hurts`, `floats`, `vulnerable_states` (padrão `IDLE`, `RECOVER`, `HURT`), `score` (5000), `size`, `name_key` |
| `Phase` | nome, limiar `enter_below` (fração de vida), lista de `Attack`, `idle_time`, `intro_time`, `dialogue`, `retaliation` (ataque imune após o golpe), `max_hazards` (perigos simultâneos), `stompable`, `vulnerable_sources`, `always_vulnerable_to`, `darkness` |
| `Attack` | `telegraph` (aviso), `active`, `recover`, ganchos `start`/`tick`/`end`, `animation`, `counter` (contramedida documentada: `jump`, `run_away`, `move_away`, `stay`, `jump_wave`), `hazards` criados, `ends_on_wall` |

Ciclo de estados: `HIDDEN` (espera o jogador a ≤ 520 px) → `EMERGE` (entrada,
evento `boss_intro`) → `IDLE` → `PREPARE_ATTACK` (telegraph; evento
`boss_telegraph` com o nome do ataque) → `ATTACK` → `RECOVER` → `IDLE`…
Um golpe leva a `HURT` (0,65 s imune) e, se a fase tem retaliação, a um
`PREPARE_ATTACK` de retaliação; se a vida cruzou o limiar da fase seguinte,
leva a `STUNNED` (troca anunciada, evento `boss_phase` no 1.º quadro) e a fase
nova vale ao fim do atordoamento. `DEFEATED` mantém o chefe em cena por
`defeat_time` e só então libera a saída da fase (`Game.boss()` usa `is_boss`).

Invariantes de justiça, verificadas por `BossDefinition.validate()` e por teste:

* **Telegraph mínimo por mundo**: 900 / 750 / 650 / 550 / 450 ms (mundos 1–5);
  na 3.ª fase pode cair 15 %, nunca abaixo de 400 ms (`MIN_TELEGRAPH_BY_WORLD`,
  `MIN_TELEGRAPH_FLOOR`). Chefes genéricos (mundo 0) usam 300 ms.
* **Alvo congelado**: posição, altura e velocidade do jogador são lidas no 1.º
  quadro do telegraph (`_choose_attack`) e nunca mais; nenhum ataque lê a
  entrada do jogador. A mira "prevista" da fase 3 de Oculus usa só
  `x + vx × 0,4 s` observados no aviso.
* **Fase ativa** ≤ 1,6 s, exceto investidas que terminam na parede.
* **Janela de recuperação** obrigatória após todo ataque; retaliação só após o
  golpe e sempre telegrafada.
* **Orçamento de perigos**: `GuardianBehavior.launch()` recusa criar projéteis
  além de `Phase.max_hazards` (projéteis levam `owner` = id do chefe); a fase 1
  admite 1 perigo. O teste de combate verifica o orçamento a cada passo.
* **Fases distintas**: cada fase acrescenta pelo menos um verbo (ataque) novo.
* **Dano**: todo ataque vale 1 nível de poder; contato com o corpo fere, pisão
  por cima não. Fontes de dano aceitas por fase (`stomp`, `fire`, `shell`,
  `star`); `always_vulnerable_to` permite ferir fora da janela (casco de Brumo).

## 2. Os cinco guardiões (`game/bosses/guardians.py`)

| Guardião | Fase (mundo) | Golpes | Tamanho | Fases (verbo) | Flutua |
| --- | --- | --- | --- | --- | --- |
| Rolão, o Tatu-Canastra | 1-3 | 3 | 64×58 | parede (atrair) · ponte (posicionar) · fruta (sincronizar) | não |
| Oculus, a Sentinela | 2-3 | 3 | 56×80 | placa (aprender) · previsão (antecipar) · tempestade (administrar) | sim |
| Brumo, a Morsa-Avalanche | 3-3 | 3 | 92×76 | tremor (estar no ar) · buraco (atrair) · cascos (usar projétil) | não |
| Lumiá, a Guardiã das Copas | 4-3 | 4 | 48×64 | mergulho (tempo) · identificação (distinguir) · penumbra (ler a luz) | sim |
| Fornalho, o Forjador | 5-3 | 5 | 84×88 | ponte (saltar o tremor) · plataformas (gerenciar o chão) · a última chama (correr) | não |

Ataques (telegraph / ativo / recuperação em segundos; contramedida):

* **Rolão** — `roll` investida 230 px/s até a parede (0,9 / ≤ 2,2 / 1,8; correr),
  `leap` quique (0,9 / 0,9 / 0,8; afastar-se), `roll_brake` (0,9 / 1,4 / 1,0),
  `pounce` salto parabólico até a posição observada (0,9 / 1,0 / 1,2; afastar-se),
  `roll_endless` (0,77 / 1,5 / 0,6), `seed` semente em arco (0,77 / 0,25 / 0,7),
  `fruit` fruta que cai na coluna observada e **não fere**: se atinge Rolão ele
  fica tonto 1,6 s (`RolaoBehavior`). Retaliação `shake` (anel de 40 px).
* **Oculus** — `dart` (0,75 / 0,2 / 2,0; saltar): dardo baixo pelos pés, dardo
  alto acima da cabeça de quem está em pé; em rajadas o alto vem primeiro e o
  baixo 0,45 s depois (`double_dart`, `predicted_dart` com mira prevista);
  `teleport` entre três pontos, sempre para longe do jogador (0,75 / 0,1 / 0,9;
  ficar); `boulder` rocha que entra pelo lado oposto a 260 px/s (0,9 / 0,3 / 1,0;
  saltar). Retaliação `sand_pulse` (60 px).
* **Brumo** — `flipper_slam` onda de choque rasteira a 320 px/s (0,7 / 0,3 / 1,6;
  saltar a onda), `slide` deslize 280 px/s até a parede (0,8 / ≤ 1,4 / 0,9–2,0;
  correr), `stalactite` queda na coluna observada (0,9 / 0,2 / 0,8; afastar-se),
  `double_slam` (0,56), `snowball` 220 px/s (0,56), `ice_shell` solta um Cascudo
  pelo cano mais distante do jogador (máx. 1 vivo). Na 3.ª fase Brumo **não é
  pisável**: só o casco deslizante fere (`vulnerable_sources = {shell}`,
  `always_vulnerable_to = {shell}`). Retaliação `spin` (50 px, 1,2 s).
* **Lumiá** — `dive` mergulho a 520 px/s até a posição observada e descanso no
  chão 1,6 s (0,7 / 0,9 / 1,6; afastar-se), `clone_dives` dois clones cinzentos
  (`lumia_clone`, sem vagalumes) mergulham antes dela, com 0,6 s de intervalo e
  telegraph próprio de 0,7 s; pisar num clone o dissolve sem dano; `spore_drift`
  dois esporos lentos (gravidade 120) para onde o jogador estava; `relocate`
  teletransporte. Na 3.ª fase a arena escurece (`behavior.darkness`) e a luz
  volta 3 s após cada golpe; após o golpe os clones trocam de lado. Só é
  vulnerável em `RECOVER`/`HURT` (no poleiro, não).
* **Fornalho** — `hammer_slam` onda a 300 px/s (0,6 / 0,3 / 1,2; saltar),
  `magma_drop` gota em arco para a posição observada (0,65 / 0,25 / 1,0),
  `platform_leap` salto (0,7 / 0,9 / 1,0), `sparks` três fagulhas em arco (0,6),
  `magma_wave` avanço a 270 px/s = 0,8× a corrida até a parede, onde fica preso
  2,2 s (1,2 / ≤ 6,0 / 2,2; correr), `hammer_slam` rápido (0,45 — o piso do
  mundo 5 na fase 3 é 0,4). Retaliação `chains` (60 px, 1,3 s).

Todos os valores de telegraph respeitam o piso do mundo em todas as fases
(`test_definition_respects_fairness_invariants_and_world_floors`).

## 3. Validação de justiça: o robô de combate

`tests/unit/test_guardians.py` constrói uma arena plana de 900 px para cada
guardião e o enfrenta com um agente (`FairnessBot`) que só usa informação que
um jogador vê: os avisos (`boss_telegraph`), a posição/velocidade de corpos e
projéteis e a própria posição no instante do aviso. Ele reage ao aviso após um
tempo de reação (0,25–0,30 s; variante lenta 0,40 s) com a contramedida
documentada no `Attack.counter`, mantém "zonas de perigo" observáveis (onde um
arremesso vai cair, o trecho baixo da trajetória de um mergulho, o raio da
retaliação, o corpo do chefe), salta perigos rasteiros pelo tempo até o contato
e só pisa o chefe entrando na coluna dele por cima, depois do ápice do salto.

Resultados (determinísticos, passo fixo de 1/120 s):

| Teste | Resultado |
| --- | --- |
| Robô (reação 0,25 s, 3 sementes) derrota os cinco guardiões sem perder poder | 15/15 |
| Robô lento (reação 0,40 s) derrota os cinco sem perder vida | 5/5 |
| Ataques iniciados antes do telegraph declarado | 0 em todos os combates |
| Perigos simultâneos acima de `max_hazards` | 0 em todos os combates |
| Duração dos combates do robô | Rolão 27 s · Oculus 20 s · Brumo 29 s · Lumiá 35 s · Fornalho 28–34 s |

O teste também cobre: três fases por guardião com conjuntos de ataques
distintos, golpes 3/3/3/4/5, Brumo ferido só por casco na 3.ª fase, Lumiá e
Oculus flutuantes, 1 perigo na 1.ª fase.

## 4. Ajustes feitos em relação à proposta da pesquisa (e por quê)

* Rajada dupla de Oculus: o dardo **alto vem antes do baixo** e o intervalo
  passou de 0,30 s para 0,45 s. Com o baixo primeiro, quem saltava era apanhado
  no ar pelo alto 0,3 s depois — um golpe sem defesa possível; a ordem inversa
  mantém a leitura de alturas (ficar / saltar) sem o conflito.
* `magma_wave` de Fornalho: recuperação de 1,0 s → **2,2 s** ("preso na parede",
  como a investida de Rolão). A alavanca/corredor da pesquisa ainda não existe;
  sem a janela longa o avanço de até 6 s não oferecia nenhuma abertura.
* Contramedida das investidas (`charge_attack`, `magma_wave`): **correr**
  (340 px/s) em vez de saltar; saltar sobre corpos de 76–88 px é inviável com o
  salto de 112 px e os chefes param na parede.
* `IDLE` conta como janela vulnerável (padrão da pesquisa: recuperação + espera).

## 5. Eventos e integração

* Eventos emitidos: `boss_intro`, `boss_telegraph` (texto = ataque),
  `boss_phase` (valor = fase, texto = nome), `boss` (derrota), `impact`,
  `telegraph`, `shot`, `stomp`. Todos têm cue no áudio procedural
  (`game/systems/audio.py`).
* Renderização: guardiões usam o desenho genérico de chefe
  (`game/rendering/sprites.py`, `is_boss`) com o marcador "!" durante o
  telegraph; `enemy.anim` recebe o nome da animação do estado/ataque (`idle`,
  `intro`, `prepare`, `attack`, `recover`, `hurt`, `phase_change`, `defeated`,
  `pounce`, `slam`, `shoot`, `throw`, `call`, `teleport`, `dive`, `wave`,
  `charge`, `leap`, `retaliate`) para o futuro atlas de sprites.
* O validador de fases exige exatamente um guardião na 3.ª fase de cada mundo
  (`is_boss_kind`, `game/levels/validator.py`) e dispensa chão sob guardiões
  flutuantes (`floats`).
* **Campanha**: os cinco guardiões estão nas fases 1-3, 2-3, 3-3, 4-3 e 5-3
  (`data/levels`), com as arenas ajustadas (ver `docs/FASES.md`). O condutor de
  campanha (`tests/gameplay/route_player.py`) entrega o controle ao robô de
  justiça ao pisar no chão da arena e o retoma quando o guardião cai. Resultado
  com previsão de pouso: perfil legado 5/5 fases concluídas sem perder vida;
  perfil calibrado 4/5 (2-3 fica presa na travessia antes da arena; 3-3 perde
  uma vida no gelo antes da arena, não no combate). Tempo total das rotas de
  guardião no legado: 1-3 46 s · 2-3 34 s · 3-3 113 s · 4-3 49 s · 5-3 33 s.

## 6. Como ajustar

Valores de tempo, velocidade e fases vivem nas fábricas de ataques e nas
`BossDefinition` de `game/bosses/guardians.py`. Após mudar qualquer número:

```bash
python -m pytest tests/unit/test_guardians.py -q
```

Falhas de `validate()` apontam o ataque e o piso violado; falhas do robô
indicam a semente e a fase em que levou dano ou não venceu em 150 s.

## 7. Pendente (não implementado)

* **Mecânicas de arena** da pesquisa: ponte frágil (Rolão), placas e pilares
  (Oculus), buracos no gelo e laje central (Brumo), copas que balançam (Lumiá),
  ponte de basalto, lava cíclica, corredor e alavanca (Fornalho). Hoje estão
  substituídas por janelas de vulnerabilidade equivalentes e marcadas como
  PENDENTE nos comentários do módulo.
* **Encenação da arena**: câmera travada na arena, portão que fecha, placa com o
  nome e cinemáticas de entrada/derrota (os guardiões já estão nas fases, mas a
  arena ainda é o chão contínuo original com a patrulha alargada).
* **Sprites e animações** próprias, **falas** (`bosses.*.intro`, `bosses.*.name`
  nos arquivos de localização) e cinemáticas de entrada/derrota.
* Atordoamento de 0,5–0,6 s de quem está no chão quando a onda de choque passa
  (proposta da pesquisa) — a onda hoje fere como projétil comum.
