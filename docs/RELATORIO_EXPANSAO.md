# Relatório da expansão — Lume: As Dez Fronteiras

Branch `claude/sweet-keller-c291m7` · PR [Helio965/Mario#1](https://github.com/Helio965/Mario/pull/1) · edição Python em `lume/` (a edição web em `src/` continua intacta).

Este relatório separa **o que existe e foi verificado** do que **está planejado**. A matriz da seção 4 é
gerada por `python tools/quality_matrix.py --render --profile --update-report` a partir de verificações
automáticas; nenhuma célula é preenchida à mão.

## 1. Resumo

- A campanha tem **10 mundos e 60 fases** com IDs estáveis (`lume/data/campaign.json`) e **60 fichas de
  planejamento individuais** (24 campos cada) em [`level_design/PLANEJAMENTO_60_FASES.md`](level_design/PLANEJAMENTO_60_FASES.md).
- **Fases jogáveis:** as 15 fases da edição original (preservadas, convertidas e revisadas) + as fases novas
  listadas na seção 3. Cada fase jogável é concluída pelo robô de rotas com entradas normais, inimigos e
  perigos ativos, sem mortes — exceto `last_flame` (legada; morte no início, x≈858) e `bramble_fortress`
  (morte na luta contra o Javali), que têm orçamento de 1 morte registrado em `lume/qa/budgets.py` e
  continuam como pendência.
- **Mundos completos** (6 fases, arte HD dedicada, criaturas com rigs próprios e chefe exclusivo):
  **Reino Verde**, **Deserto Dourado** e **Montanhas Geladas**.
- "Concluída" na matriz exige todos os critérios verificáveis (estrutura, arte dedicada, rigs, rota,
  renderização de todas as áreas, desempenho medido, ≥ 3 relíquias, ficha no plano, inimigos/checkpoints/
  segredos ≥ ficha, trilha própria). Fases que ainda não atingem a ficha do plano aparecem como **Parcial**
  com a pendência exata listada abaixo da matriz.

## 2. Marcos

| Marco | Situação | Evidência |
| ----- | -------- | --------- |
| A — Auditoria e pesquisa | concluído | `docs/research/` (5 documentos com fontes; fatos, observações, estimativas e decisões separados), avaliação das 15 fases em [`level_design/AVALIACAO_FASES_LEGADAS.md`](level_design/AVALIACAO_FASES_LEGADAS.md), plano das 60 fases e `MUNDO_01..10.md` |
| B — Sistema técnico | concluído | núcleo Python portado com testes de paridade, formato `lume.level` v1 + carregador + validador semântico, registro tipado de 63 espécies, pipeline gráfico HD, salvamento v2 com migração do `lume-save-v1`, ferramentas (`tools/`) |
| C — Fase modelo em HD | concluído | `first_steps`: Lume articulado em HD, cenário em camadas, inimigos próprios, segredos, áudio, interface e testes (renderização testada em 1280×720, 1920×1080 e 3840×2160) |
| D — Primeiro mundo completo | concluído | Reino Verde: 6 fases + Javali Espinheiro |
| E — Expansão dos mundos | **em andamento** | ver seção 3 |
| F — Integração | não iniciado (depende das 60 fases) | salvamento/progressão já cobrem 60 IDs; migração testada |
| G — Polimento final | não iniciado | — |

## 3. Estado por mundo

| # | Mundo | Fases jogáveis | Arte HD do mundo | Criaturas | Chefe do mundo |
| - | ----- | -------------- | ---------------- | --------- | -------------- |
| 1 | Reino Verde | 6/6 | dedicada | rigs dedicados | Javali Espinheiro (implementado) |
| 2 | Deserto Dourado | 6/6 | dedicada (inclui interior da pirâmide) | rigs dedicados | Escaravelho-Rei (implementado) |
| 3 | Costa dos Corais | 0/6 (6 em produção) | em produção | em produção | Ermitão-Âncora (em produção) |
| 4 | Montanhas Geladas | 6/6 | dedicada (inclui cidadela e salão do trono) | rigs dedicados | Morsa Gelomar (implementado) |
| 5 | Floresta Encantada | 3/6 (3 em produção) | dedicada | rigs dedicados | Imperatriz Mariposa (em produção) |
| 6 | Cidade Mecânica | 0/6 | em produção | em produção | Colosso Fundidor (planejado) |
| 7 | Arquipélago Celeste | 0/6 | em produção | em produção | Grifa Ventania (planejado) |
| 8 | Pântano Assombrado | 0/6 | em produção | em produção | Vulto Apagador (planejado) |
| 9 | Fortaleza Vulcânica | 3/6 (3 em produção) | dedicada | rigs dedicados | Salamandra Caldera (em produção) |
| 10 | Cidadela das Estrelas | 0/6 | em produção | em produção | Eclipse Devorador (planejado) |

"Em produção" = trabalho iniciado nesta execução e ainda não integrado ao branch; não conta como pronto.
Os guardiões legados dos mundos 1, 2, 4, 5 e 9 permanecem como minichefes das fases 3.

## 4. Matriz de qualidade (gerada)

<!-- matriz:inicio -->
| Mundo | Fase | Nome | Estrutura | Arte HD | Inimigos | Gameplay | Gráficos | Desempenho | Relíquias | Plano | Áudio | Documentada | Estado |
| ----- | ---- | ---- | --------- | ------- | -------- | -------- | -------- | ---------- | --------- | ----- | ----- | ----------- | ------ |
| 1 | 1 | Primeiros Passos | ok | dedicada | ok | ok | ok | medido (software) | 3 | ok | ok | sim | Concluída |
| 1 | 2 | Canais do Vale | ok | dedicada | ok | ok | ok | medido (software) | 3 | ok | ok | sim | Concluída |
| 1 | 3 | Guardião do Pomar | ok | dedicada | ok | ok | ok | medido (software) | 3 | ok | ok | sim | Concluída |
| 1 | 4 | Colina dos Moinhos | ok | dedicada | ok | ok | ok | medido (software) | 3 | ok | ok | sim | Concluída |
| 1 | 5 | Tocas do Prado | ok | dedicada | ok | ok | ok | medido (software) | 4 | ok | ok | sim | Concluída |
| 1 | 6 | Fortaleza do Espinheiro | ok | dedicada | ok | ok | ok | medido (software) | 3 | parcial | ok | sim | Parcial |
| 2 | 1 | Dunas ao Vento | ok | dedicada | ok | ok | ok | medido (software) | 3 | ok | ok | sim | Concluída |
| 2 | 2 | Pontes do Cânion | ok | dedicada | ok | ok | ok | medido (software) | 3 | ok | ok | sim | Concluída |
| 2 | 3 | Templo das Areias | ok | dedicada | ok | ok | ok | medido (software) | 3 | ok | ok | sim | Concluída |
| 2 | 4 | Passagem da Tempestade | ok | dedicada | ok | ok | ok | medido (software) | 3 | ok | ok | sim | Concluída |
| 2 | 5 | Oásis Soterrado | ok | dedicada | ok | ok | ok | medido (software) | 3 | ok | ok | sim | Concluída |
| 2 | 6 | Pirâmide do Escaravelho | ok | dedicada | ok | ok | ok | medido (software) | 3 | ok | ok | sim | Concluída |
| 3 | 1 | Praia das Conchas | pendente | pendente | pendente | pendente | pendente | pendente | 0 | pendente | pendente | sim | Planejada |
| 3 | 2 | Piscinas da Maré | pendente | pendente | pendente | pendente | pendente | pendente | 0 | pendente | pendente | sim | Planejada |
| 3 | 3 | Recife do Farol | pendente | pendente | pendente | pendente | pendente | pendente | 0 | pendente | pendente | sim | Planejada |
| 3 | 4 | Correntes Profundas | pendente | pendente | pendente | pendente | pendente | pendente | 0 | pendente | pendente | sim | Planejada |
| 3 | 5 | Labirinto de Coral | pendente | pendente | pendente | pendente | pendente | pendente | 0 | pendente | pendente | sim | Planejada |
| 3 | 6 | Galeão Submerso | pendente | pendente | pendente | pendente | pendente | pendente | 0 | pendente | pendente | sim | Planejada |
| 4 | 1 | Lago de Cristal | ok | dedicada | ok | ok | ok | medido (software) | 3 | ok | ok | sim | Concluída |
| 4 | 2 | Escalada Azul | ok | dedicada | ok | ok | ok | medido (software) | 3 | ok | ok | sim | Concluída |
| 4 | 3 | Coração da Nevasca | ok | dedicada | ok | ok | ok | medido (software) | 3 | ok | ok | sim | Concluída |
| 4 | 4 | Encostas Escorregadias | ok | dedicada | ok | ok | ok | medido (software) | 3 | ok | ok | sim | Concluída |
| 4 | 5 | Cume da Avalanche | ok | dedicada | ok | ok | ok | medido (software) | 3 | ok | ok | sim | Concluída |
| 4 | 6 | Cidadela de Geada | ok | dedicada | ok | ok | ok | medido (software) | 3 | ok | ok | sim | Concluída |
| 5 | 1 | Copas Luminosas | ok | dedicada | ok | ok | ok | medido (software) | 2 | parcial | ok | sim | Parcial |
| 5 | 2 | Ruínas dos Vagalumes | ok | dedicada | ok | ok | ok | medido (software) | 2 | parcial | ok | sim | Parcial |
| 5 | 3 | A Árvore Ancestral | ok | dedicada | ok | ok | ok | medido (software) | 2 | parcial | ok | sim | Parcial |
| 5 | 4 | Pontes de Cipó | pendente | pendente | pendente | pendente | pendente | pendente | 0 | pendente | pendente | sim | Planejada |
| 5 | 5 | Clareira dos Sussurros | pendente | pendente | pendente | pendente | pendente | pendente | 0 | pendente | pendente | sim | Planejada |
| 5 | 6 | Santuário das Raízes | pendente | pendente | pendente | pendente | pendente | pendente | 0 | pendente | pendente | sim | Planejada |
| 6 | 1 | Distrito das Engrenagens | pendente | pendente | pendente | pendente | pendente | pendente | 0 | pendente | pendente | sim | Planejada |
| 6 | 2 | Usina de Vapor | pendente | pendente | pendente | pendente | pendente | pendente | 0 | pendente | pendente | sim | Planejada |
| 6 | 3 | Linha de Montagem | pendente | pendente | pendente | pendente | pendente | pendente | 0 | pendente | pendente | sim | Planejada |
| 6 | 4 | Fábrica dos Interruptores | pendente | pendente | pendente | pendente | pendente | pendente | 0 | pendente | pendente | sim | Planejada |
| 6 | 5 | Torre do Relógio | pendente | pendente | pendente | pendente | pendente | pendente | 0 | pendente | pendente | sim | Planejada |
| 6 | 6 | Fundição de Ferro | pendente | pendente | pendente | pendente | pendente | pendente | 0 | pendente | pendente | sim | Planejada |
| 7 | 1 | Porto das Nuvens | pendente | pendente | pendente | pendente | pendente | pendente | 0 | pendente | pendente | sim | Planejada |
| 7 | 2 | Jardins Flutuantes | pendente | pendente | pendente | pendente | pendente | pendente | 0 | pendente | pendente | sim | Planejada |
| 7 | 3 | Cachoeiras Ascendentes | pendente | pendente | pendente | pendente | pendente | pendente | 0 | pendente | pendente | sim | Planejada |
| 7 | 4 | Pontes do Vendaval | pendente | pendente | pendente | pendente | pendente | pendente | 0 | pendente | pendente | sim | Planejada |
| 7 | 5 | Agulha da Tempestade | pendente | pendente | pendente | pendente | pendente | pendente | 0 | pendente | pendente | sim | Planejada |
| 7 | 6 | Ninho do Grifo | pendente | pendente | pendente | pendente | pendente | pendente | 0 | pendente | pendente | sim | Planejada |
| 8 | 1 | Brejo da Névoa | pendente | pendente | pendente | pendente | pendente | pendente | 0 | pendente | pendente | sim | Planejada |
| 8 | 2 | Charco das Lanternas | pendente | pendente | pendente | pendente | pendente | pendente | 0 | pendente | pendente | sim | Planejada |
| 8 | 3 | Casarão Afundado | pendente | pendente | pendente | pendente | pendente | pendente | 0 | pendente | pendente | sim | Planejada |
| 8 | 4 | Apagão no Pântano | pendente | pendente | pendente | pendente | pendente | pendente | 0 | pendente | pendente | sim | Planejada |
| 8 | 5 | Lodaçal Fantasma | pendente | pendente | pendente | pendente | pendente | pendente | 0 | pendente | pendente | sim | Planejada |
| 8 | 6 | Torre do Lanterneiro | pendente | pendente | pendente | pendente | pendente | pendente | 0 | pendente | pendente | sim | Planejada |
| 9 | 1 | Pontes de Basalto | ok | dedicada | ok | ok | ok | medido (software) | 2 | parcial | ok | sim | Parcial |
| 9 | 2 | Fornalha dos Ecos | ok | dedicada | ok | ok | ok | medido (software) | 2 | parcial | ok | sim | Parcial |
| 9 | 3 | A Última Chama | ok | dedicada | ok | ok | ok | medido (software) | 2 | parcial | ok | sim | Parcial |
| 9 | 4 | Magma Ascendente | pendente | pendente | pendente | pendente | pendente | pendente | 0 | pendente | pendente | sim | Planejada |
| 9 | 5 | Corredor de Cinzas | pendente | pendente | pendente | pendente | pendente | pendente | 0 | pendente | pendente | sim | Planejada |
| 9 | 6 | Trono de Magma | pendente | pendente | pendente | pendente | pendente | pendente | 0 | pendente | pendente | sim | Planejada |
| 10 | 1 | Portão Estrelado | pendente | pendente | pendente | pendente | pendente | pendente | 0 | pendente | pendente | sim | Planejada |
| 10 | 2 | Trilha das Constelações | pendente | pendente | pendente | pendente | pendente | pendente | 0 | pendente | pendente | sim | Planejada |
| 10 | 3 | Salões da Gravidade | pendente | pendente | pendente | pendente | pendente | pendente | 0 | pendente | pendente | sim | Planejada |
| 10 | 4 | Santuário dos Reflexos | pendente | pendente | pendente | pendente | pendente | pendente | 0 | pendente | pendente | sim | Planejada |
| 10 | 5 | Bastião do Eclipse | pendente | pendente | pendente | pendente | pendente | pendente | 0 | pendente | pendente | sim | Planejada |
| 10 | 6 | Trono do Eclipse | pendente | pendente | pendente | pendente | pendente | pendente | 0 | pendente | pendente | sim | Planejada |

Resumo: Concluída: 17, Parcial: 7, Planejada: 36

Pendências por fase (geradas pelas verificações):

- `bramble_fortress`: abaixo do plano: inimigos 8/9
- `glowing_canopy`: 2 relíquia(s) (meta 3); abaixo do plano: inimigos 3/6, segredos 2/3
- `firefly_ruins`: 2 relíquia(s) (meta 3); abaixo do plano: inimigos 3/9, checkpoints 1/2, segredos 3/4
- `ancestral_tree`: 2 relíquia(s) (meta 3); abaixo do plano: inimigos 3/9, checkpoints 1/2, segredos 2/3
- `basalt_bridges`: 2 relíquia(s) (meta 3); abaixo do plano: inimigos 3/12, checkpoints 1/2, segredos 2/3
- `echo_furnace`: 2 relíquia(s) (meta 3); abaixo do plano: inimigos 3/14, segredos 2/3
- `last_flame`: 2 relíquia(s) (meta 3); abaixo do plano: inimigos 4/14, checkpoints 1/2, segredos 2/3
<!-- matriz:fim -->

Colunas: **Estrutura** = validador sem erros; **Arte HD** = conjunto do mundo dedicado e todas as espécies da
fase com rig próprio; **Inimigos** = rigs dedicados para todas as espécies; **Gameplay** = robô de rotas
conclui a fase dentro do orçamento de mortes e derrota o chefe; **Gráficos** = todas as áreas renderizam
em 1280×720 sem erro; **Desempenho** = medição em `artifacts/perf/`; **Plano** = inimigos, checkpoints e
segredos ≥ ficha do plano; **Áudio** = trilha própria do mundo.

## 5. O que foi construído

- **Núcleo** (`lume/core`): simulação em passo fixo de 1/120 s portada fielmente da edição web; índice
  espacial; câmera por área; zonas (natação, correntes, vento com rajadas e fase, areia movediça, escuridão
  com halo da lanterna, baixa gravidade); lava/magma que sobe; blocos-interruptor e portões de arena;
  plataformas móveis, frágeis (que relaxam e se refazem), molas, esteiras; 25 famílias de comportamento
  (incluindo 3 chefes de mundo; a família `guardian` cobre os 5 guardiões legados).
- **Dados** (`lume/data`, `lume/levels`): fases declarativas validadas (esquema com caminhos JSON nos erros,
  referências, bioma/habitat, ordem de introdução das espécies, vãos e subidas simulados com a física real,
  checkpoints seguros, plataformas enterradas); registro de campanha; plano das 60 fases como dados.
- **Gráficos** (`lume/render`): arte vetorial gerada por código (SVG) rasterizada na densidade exata da saída
  (720p a 4K, nunca ampliada), cache em disco com sementes estáveis, LRU com orçamento, pré-carga por fase,
  terreno em blocos sem emendas, parallax em várias camadas, interiores por variante de área, vinheta por
  mundo, rigs recortados com poses por estado para Lume, criaturas e chefes. Ver
  [`technical/SISTEMA_GRAFICO.md`](technical/SISTEMA_GRAFICO.md) e [`technical/ANIMACOES.md`](technical/ANIMACOES.md).
- **Salvamento**: formato v2 com migração sem perdas do `lume-save-v1` da edição web
  ([`technical/MIGRACAO_SALVAMENTOS.md`](technical/MIGRACAO_SALVAMENTOS.md)).
- **QA**: robô de rotas (pula vãos, sobe paredes, espera bolas rolando e passa no vão seguro, nada, sai da
  areia movediça, luta contra cada chefe), validador, matriz de qualidade, capturas, perfil de desempenho,
  gerador do plano (`tools/plan/`), kit de autoria de fases (`tools/levelgen/`), vitrine de arte por mundo
  (`tools/art_showcase.py`).

## 6. Testes

`python -m pytest tests/python -q` — física e paridade com a edição web, comportamentos e chefes (ciclos,
avisos, janelas de vulnerabilidade, derrota, fase 2), interações, fases (esquema, validador, geometria),
**rotas completas de todas as fases jogáveis**, salvamento/migração, gráficos (todas as fases e sub-áreas em
720p; fase modelo em 720p/1080p/4K; letterbox; estabilidade das sementes entre processos). A CI do GitHub
(`.github/workflows/python.yml`) roda a mesma suíte. A edição web mantém `npm test` e `npm run test:e2e`.

## 7. Desempenho

Medições em [`technical/PERFORMANCE.md`](technical/PERFORMANCE.md) (tabela gerada de `artifacts/perf/`).
Este ambiente **não tem GPU**: o SDL usa o renderizador por software, então os tempos de quadro em 1080p/4K
são limites superiores; a simulação (< 1 ms) e a submissão de desenho em Python (≈ 2–3 ms) são os números
que valem para máquinas com GPU. Cada linha registra a carga da máquina no momento da medição; linhas
marcadas com contenção foram medidas com outros processos ativos e precisam ser refeitas com a máquina
ociosa. **Medição em hardware com GPU (1080p e 4K) ainda não foi feita.**

## 8. Desvios e limitações conhecidas

- **Sem rampas no motor**: as "encostas" do plano são terraços descendentes de 12–16 u (registrado nas
  notas de `slippery_slopes`).
- **Variante de arte por fase**: `art.variant` ainda não chega ao conjunto do mundo; fases do mesmo mundo
  compartilham o mesmo céu/parallax (o terreno, os adereços e os interiores variam).
- **Renderização sem GPU** neste ambiente (ver seção 7).
- **Fases legadas abaixo da ficha**: as fichas do plano pedem mais inimigos, checkpoints e segredos para
  várias fases antigas; a matriz lista cada diferença. Não foram marcadas como concluídas.
- O robô de rotas é um jogador cuidadoso, não um humano: completar a rota prova que o caminho é possível e
  justo para as regras simuladas, não substitui testes de jogo com pessoas.
- Correção deliberada em relação à edição web: plataformas frágeis acumulavam "estresse" para sempre (uma
  ponte atravessada uma vez caía sob o jogador na volta); agora o estresse relaxa e é zerado ao reaparecer.

## 9. Instruções para a próxima execução

Ordem recomendada: integrar o que estiver em produção (mundos 3, 5, 6, 8 e 9), depois mundos 7 e 10,
depois os ajustes das fases legadas apontados pela matriz, depois Marco F e G.

Para cada mundo (padrão usado nos mundos 2 e 4):

1. **Arte** — criar `lume/render/worlds/<mundo>.py` (`WorldArt`, exportado como `ART_CLASS`) e
   `lume/render/enemies/<mundo>.py` (rigs com `@register("<animation_set>")`), seguindo
   `green_kingdom.py`/`frozen_peaks.py`: céu, camadas, terreno contínuo entre blocos (função de x do
   mundo), blocos, plataformas, canos, adereços, clima, `interior(variante)` e `gate()`; para cada espécie
   todos os `animation_states` de `enemies.json`, as duas derrotas e o lampejo de dano. Revisar com
   `python tools/art_showcase.py <mundo> /tmp/s.json` + `python tools/capture_level.py /tmp/s.json /tmp --at 300,1300,2300`.
   Originalidade: nenhum design da Nintendo (ver notas "evitar" nas fichas de espécies).
2. **Fases** — escrever `tools/levelgen/world0N_<mundo>.py` com o kit (`tools/levelgen/kit.py`) seguindo as
   fichas de `docs/level_design/MUNDO_0N.md`; gerar o JSON; `python -m lume --validate` sem ERROR.
3. **Rotas** — `python -m pytest tests/python/test_campaign_routes.py -k <fase>`; corrigir geometria
   injusta (vãos no fim de rampas, inimigos sobre pontos de pouso, pockets estreitos) em vez de mexer no
   robô; melhorias no robô só quando ele passa a agir como um jogador cuidadoso.
4. **Chefe** — nova família em `lume/core/behaviors/bosses.py` (avisos legíveis, janela clara de pisão,
   fase 2), entrada `boss: true` em `enemies.json`, rig em `lume/render/enemies/<mundo>_boss.py`, testes em
   `tests/python/test_bosses.py` e rotina no robô (`_fight_<chefe>`).
5. **Verificar e registrar** — suíte completa verde; `python tools/quality_matrix.py --render --profile --update-report`;
   `python tools/gen_docs.py`; atualizar a seção 3 deste relatório e o README; commit por mundo.

Requisitos de motor ainda pendentes (das fichas): extensão de `rising_lava` com etapas e recuo
(`rising_magma`, `magma_throne`, `sunken_galleon`), luzes acendíveis (`lights_out`, `lantern_keep`),
interruptores temporizados/grupos (`switch_factory`, `iron_foundry`, `phantom_mire`) e as 7 famílias de
chefe planejadas (seção 6.2 do plano).
