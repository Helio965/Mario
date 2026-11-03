# Lume — As Dez Fronteiras · Planejamento individual das 60 fases

> Documento de planejamento que orienta a implementação. Fonte de verdade em dados: [`lume/data/plan/campaign_plan.json`](../../lume/data/plan/campaign_plan.json) (mesmos valores deste texto). Documentos por mundo: [`MUNDO_01.md`](MUNDO_01.md), [`MUNDO_02.md`](MUNDO_02.md), [`MUNDO_03.md`](MUNDO_03.md), [`MUNDO_04.md`](MUNDO_04.md), [`MUNDO_05.md`](MUNDO_05.md), [`MUNDO_06.md`](MUNDO_06.md), [`MUNDO_07.md`](MUNDO_07.md), [`MUNDO_08.md`](MUNDO_08.md), [`MUNDO_09.md`](MUNDO_09.md), [`MUNDO_10.md`](MUNDO_10.md).
> Estado dos dados consultados: 2026-11-03 04:24 UTC — `campaign.json`, `enemies.json` (63 espécies), `levels/schema.py`, `levels/validate.py`, `core/game.py`, `core/behaviors/*`, as 15 fases legadas e as 8 fases novas que outros agentes criaram durante a redação (`windmill_heights`, `meadow_burrows`, `bramble_fortress`, `sandstorm_pass`, `sunken_oasis`, `scarab_pyramid`, `slippery_slopes`, `avalanche_ridge`), além dos chefes `escaravelho_rei`, `morsa_gelomar` adicionados ao registro.

## 1. Método

1. **Ids e ordem** vêm de `lume/data/campaign.json` e não foram alterados; nomes de exibição são os do registro.
2. **Inimigos** vêm de `lume/data/enemies.json`: cada espécie estreia exatamente na fase do seu `introduced_in` e só aparece em mundos do seu habitat; espécies de `underground`, `fortress` ou `underwater` só entram em outros mundos dentro de sub-áreas marcadas com esse bioma (a marca aparece entre colchetes na lista de áreas de cada fase, ex.: `maze [underwater]`). Os chefes planejados aparecem como `boss:<id>`.
3. **Geometria** usa a física real (`lume/core/constants.py`): gravidade 1550 u/s², impulso 590 u/s (altura ≈ 112 u segurando), corrida 340 u/s (alcance ≈ 259 u), coyote 0,1 s, buffer 0,12 s, pisão 390 u/s, jogador 22×30 / 22×46 u, câmera de ≈ 738×415 u com Lume a ~1/3 da largura.
4. **Ciclo de ensino em 8 etapas** (pesquisa `docs/research/ENGENHARIA_REVERSA_FASES_MARIO.md`, §3.2.1f): introdução → demonstração segura → primeiro desafio → escalada → combinação → reviravolta → teste final → recompensa. O *Caminho principal* de cada fase é escrito nessas 8 etapas, com faixas de x (ou de andar, nas fases verticais).
5. **Uma ideia própria por fase**: cada seção abre com a reviravolta que diferencia a fase das demais do mundo.
6. **Fases que já existem** (15 legadas + as fases novas criadas durante a redação, algumas a partir deste próprio plano) são preservadas: o plano descreve o traçado atual e lista melhorias concretas (posições, correções, terceira relíquia, arte). Onde o arquivo diverge de uma regra do plano (dificuldade fora da faixa, vão acima do limite, checkpoint escasso), a divergência é apontada no item *Ajustes sobre a implementação inicial*. A avaliação qualitativa das 15 fases legadas, feita por outro agente, está em [`AVALIACAO_FASES_LEGADAS.md`](AVALIACAO_FASES_LEGADAS.md); as melhorias deste plano são compatíveis com ela.
7. **Verificação automática** (rodada antes da entrega): JSON válido; 60 fases na ordem de `campaign.json`; chaves exatas; estreia = `introduced_in` para todas as espécies; habitat por mundo ou sub-área; sub-áreas dentro dos limites e sem sobreposição; 3 segredos com relíquia por fase; dificuldade dentro da faixa do mundo.

## 2. Curva de dificuldade

| Mundo | Faixa | Fases (1→6) | Papel |
| --- | --- | --- | --- |
| 1. Reino Verde | 1–3 | 1 · 1 · 2 · 2 · 3 · 3 | introdução |
| 2. Deserto Dourado | 1–3 | 2 · 3 · 3 · 3 · 3 · 3 | introdução |
| 3. Costa dos Corais | 3–5 | 3 · 3 · 4 · 4 · 5 · 5 | novas condições físicas |
| 4. Montanhas Geladas | 3–5 | 4 · 4 · 5 · 4 · 5 · 5 | novas condições físicas |
| 5. Floresta Encantada | 5–6 | 5 · 5 · 6 · 5 · 6 · 6 | combinações e inimigos especializados |
| 6. Cidade Mecânica | 5–6 | 5 · 5 · 6 · 6 · 6 · 6 | combinações e inimigos especializados |
| 7. Arquipélago Celeste | 6–8 | 6 · 7 · 7 · 7 · 8 · 8 | movimento e percepção avançados |
| 8. Pântano Assombrado | 6–8 | 6 · 7 · 7 · 7 · 8 · 8 | movimento e percepção avançados |
| 9. Fortaleza Vulcânica | 8–10 | 8 · 8 · 9 · 8 · 9 · 9 | domínio e final |
| 10. Cidadela das Estrelas | 8–10 | 8 · 9 · 9 · 9 · 10 · 10 | domínio e final |

Dentro de cada mundo a curva é em dente de serra (pesquisa, §2 item 3): a fase 4 (mecânica especial) costuma recuar um ponto em relação à 3, porque apresenta uma regra nova; as fases 5 e 6 voltam a subir.

## 3. Regras de projeto aplicadas a todas as fases

- **Vãos obrigatórios** (borda a borda, mesma altura): Mundo 1 ≤ 125 u (fases 1–2 vencíveis andando: alcance andando 168 u); Mundos 2–5 ≤ 150 u; Mundos 6–10 ≤ 160 u (teto do projeto). Com desnível, usar a tabela de alcance da pesquisa (§5.1). Rotas opcionais nunca acima de 200 u.
- **Subidas obrigatórias** ≤ 64 u num salto (até 96 u só em rota opcional sobre chão seguro); acima disso, mola, corrente ascendente, plataforma móvel ou baixa gravidade (nos bolsões de gravidade × 0,55 a subida equivalente é ≤ 116 u).
- **Checkpoints** a cada ~1500–2500 u de caminho (vertical conta como caminho); em fases de chefe, um na antessala. Zona segura: chão plano de x−96 a x+192 e nenhum inimigo comum alcançando [x−160, x+320] em 3 s; chefes ficam confinados à arena.
- **Primeiro encontro** de cada espécie: chão plano, ≥ 300 u de aproximação visível, recuo livre, nenhum vão letal a 200 u. No máximo 2 espécies novas por fase (exceções do registro na seção 6); variantes avançadas só depois da família-base.
- **Teto sobre patrulha** (regra nova, nascida do problema de `canyon_bridges`): nenhum sólido não semissólido com base entre `y_chão−158` e `y_chão−30` sobre a patrulha de um inimigo terrestre que esteja a menos de 160 u de um vão obrigatório. Tetos que precisam ficar ali viram semissólidos.
- **Pouso no gelo**: ≥ 330 u livres depois do pouso ou parede de contenção (frenagem de 321 u).
- **Três relíquias por fase**, cada uma num segredo próprio com pista visual: em geral uma visível e exigente, uma numa rota opcional e uma numa área secreta. Nenhum segredo causa morte; moedas nunca levam a morte e toda queda maior que 220 u tem trilha de moedas até chão de ≥ 160 u.
- **Pelo menos uma rota opcional** por fase, que reencontra o caminho principal; o caminho principal nunca depende dela.
- **Geometria do bioma**: campina com moinhos, tocas e cercas; deserto com dunas, cânions e templos; costa com correntes, píeres e áreas submersas; neve com rampas (degraus descendentes de 12 u com arte contínua), cavernas e pontes; floresta com troncos, galhos e raízes; cidade com engrenagens e esteiras; céu com nuvens e correntes; pântano com passarelas e lanternas; vulcão com basalto e lava; cidadela com cristal, constelações e espelhos.
- **Saídas secretas** (regra 26 da pesquisa) ficam fora do plano porque a campanha é linear; os desafios opcionais e as salas secretas ocupam esse papel.
- **NPC por mundo**: um personagem original com função de jogo (checkpoints, relíquias, nado, gelo, segredos, ritmo, vento, luz, magma, mapas), implementado como prop animado + evento `message`.

## 4. Critérios de teste comuns

Toda fase tem, além dos critérios próprios: `validate_level`/`validate_campaign` sem erros; `route_bot` concluindo a partir do spawn e de cada checkpoint com inimigos e perigos ativos; vãos e subidas simulados nas duas alturas sem coyote nem buffer; relíquias e moedas alcançáveis; estreias em chão plano; *teto sobre patrulha*; zona segura dos checkpoints. Esses itens aparecem parametrizados no campo *Critérios de teste* de cada fase.

## 5. Tabela-resumo das 60 fases

| Fase | Id | Nome | Origem | Dif. | Tamanho (u) | Ideia própria | Estreias | Chefe | Bloqueio |
| --- | --- | --- | --- | ---: | --- | --- | --- | --- | --- |
| 1-1 | `first_steps` | Primeiros Passos | legada 1-1 | 1 | 3200×1240 | o ar guarda segredos: bloco oculto e galhos semissólidos | Bolota, Caramujo-de-Casca | — | — |
| 1-2 | `valley_canals` | Canais do Vale | legada 1-2 | 1 | 3500×1240 | a margem elevada esconde três rotas opcionais (alta, ponte e cano) | Besouro-Asa, Besouro | — | — |
| 1-3 | `orchard_guardian` | Guardião do Pomar | legada 1-3 | 2 | 3900×1240 | o primeiro chefe ensina a esperar a abertura luminosa | — | Guardião do Pomar (minichefe, implementado) | — |
| 1-4 | `windmill_heights` | Colina dos Moinhos | nova | 2 | 5600×1240 | as pás do moinho viram pontes giratórias sobre o canal | Flor-Mordedora | — | — |
| 1-5 | `meadow_burrows` | Tocas do Prado | nova | 3 | 6000×1240 | a sebe fecha a superfície e o túnel vira o único caminho | Ouriço-Espinho | — | — |
| 1-6 | `bramble_fortress` | Fortaleza do Espinheiro | nova | 3 | 4400×1240 | três ritmos ao mesmo tempo antes de um chefe que se vence pela parede | — | Javali Espinheiro (chefe, implementado) | — |
| 2-1 | `windswept_dunes` | Dunas ao Vento | legada 2-1 | 2 | 3800×1240 | o vento aparece primeiro como aliado e um redemoinho leva a um segredo | Escaravelho-de-Areia, Tatu-Bola, Cacto Sentinela | — | — |
| 2-2 | `canyon_bridges` | Pontes do Cânion | legada 2-2 | 3 | 4100×1240 | o cânion respira: uma térmica sobe do fundo e leva a um ninho | Abutrinho | — | — |
| 2-3 | `sand_temple` | Templo das Areias | legada 2-3 | 3 | 4200×1240 | a força de Lume grande abre o teto de tijolos do templo | Escorpião-Couraça | Guardião do Templo (minichefe, implementado) | — |
| 2-4 | `sandstorm_pass` | Passagem da Tempestade | nova | 3 | 5600×1240 | no olho da tempestade o vento troca de lado a cada 2 s | Serpente-de-Duna | — | — |
| 2-5 | `sunken_oasis` | Oásis Soterrado | nova | 3 | 6000×1240 | a lagoa do oásis é a primeira água em que se nada — e guarda uma relíquia no fundo | Escaravelho Lançador | — | — |
| 2-6 | `scarab_pyramid` | Pirâmide do Escaravelho | nova | 3 | 4600×1240 | a laje sobre a armadilha de areia antecipa o chão que o chefe vai fazer tremer | — | Escaravelho-Rei (chefe, implementado) | — |
| 3-1 | `shell_beach` | Praia das Conchas | nova | 3 | 4600×1240 | a gruta das conchas obriga o primeiro mergulho completo | Caranguejo-Pinça, Peixe-Saltador | — | — |
| 3-2 | `tide_pools` | Piscinas da Maré | nova | 3 | 5000×1240 | a moreia não sai se Lume encostar na toca: a regra vira ferramenta | Baiacu-Espinho, Moreia-da-Toca | — | — |
| 3-3 | `lighthouse_reef` | Recife do Farol | nova | 4 | 4800×2700 | a ressaca ritmada alaga o passadiço e faz as boias subirem | — | — | — |
| 3-4 | `current_depths` | Correntes Profundas | nova | 4 | 5400×1620 | a maré reversa troca a direção da corrente no meio do caminho | Água-Viva Elétrica | — | — |
| 3-5 | `coral_maze` | Labirinto de Coral | nova | 5 | 5600×1620 | o labirinto desce e a saída fica no alto: fuga ascendente com dois polvos | Polvo-Tinteiro | — | — |
| 3-6 | `sunken_galleon` | Galeão Submerso | nova | 5 | 6000×1620 | o mastro tombado vira ponte e o casco racha no meio da luta | — | Ermitão-Âncora (planejado) | sim |
| 4-1 | `crystal_lake` | Lago de Cristal | legada 3-1 | 4 | 3600×1240 | a patinação vira desafio: parar na ponta do píer congelado | Pinguim Patrulheiro, Caracol-de-Cristal, Coruja Nevada | — | — |
| 4-2 | `blue_ascent` | Escalada Azul | legada 3-2 | 4 | 4400×1240 | uma rota do cume acima dos seis terraços | Boneco de Neve | — | — |
| 4-3 | `blizzard_heart` | Coração da Nevasca | legada 3-3 | 5 | 4600×1240 | a pedra vira abrigo e arma: o carneiro bate nela e fica tonto | Carneiro Glacial | Guardião da Nevasca (minichefe, implementado) | — |
| 4-4 | `slippery_slopes` | Encostas Escorregadias | nova | 4 | 5600×1240 | a encosta invertida: subir degraus de gelo que empurram de volta | Yeti-Mirim | — | — |
| 4-5 | `avalanche_ridge` | Cume da Avalanche | nova | 5 | 6000×1240 | o corredor da avalanche: quatro bolas gigantes em fases diferentes e abrigos entre elas | Pingente de Gelo | — | — |
| 4-6 | `frost_citadel` | Cidadela de Geada | nova | 5 | 6400×1620 | no salão dos vitrais a luz colorida marca o gelo que não escorrega | — | Morsa Gelomar (chefe, implementado) | — |
| 5-1 | `glowing_canopy` | Copas Luminosas | legada 4-1 | 5 | 4000×1240 | Ciranda revela um caminho de blocos ocultos entre as copas | Cogumelo Saltitante, Caracol-Musgo, Mariposa-Lume, Planta-de-Esporos | — | — |
| 5-2 | `firefly_ruins` | Ruínas dos Vagalumes | legada 4-2 | 5 | 4500×1240 | a hera esconde um salão inteiro onde os vagalumes entram e não saem | Besouro-Casca | — | — |
| 5-3 | `ancestral_tree` | A Árvore Ancestral | legada 4-3 | 6 | 4700×1240 | a segunda subida pelos cogumelos-mola leva à copa acima de tudo | — | Guardião da Árvore (minichefe, implementado) | — |
| 5-4 | `vine_bridges` | Pontes de Cipó | nova | 5 | 5800×2160 | a ponte em espiral desce em volta de um tronco gigante | Arbusto-Espreita | — | — |
| 5-5 | `whispering_hollow` | Clareira dos Sussurros | nova | 6 | 5800×2160 | descer o tronco oco no escuro e subir de volta pelos chapéus dos cogumelos | Aranha-do-Cipó | — | — |
| 5-6 | `root_sanctum` | Santuário das Raízes | nova | 6 | 6400×1620 | as raízes crescem e recolhem em ritmo como pontes vivas | — | Imperatriz Mariposa (planejado) | sim |
| 6-1 | `gear_district` | Distrito das Engrenagens | nova | 5 | 5000×1240 | o projétil do canhão vira degrau | Robô de Ronda, Canhão Sentinela | — | — |
| 6-2 | `steam_works` | Usina de Vapor | nova | 5 | 5400×2160 | o vapor deita: jatos laterais empurram para fora das passarelas | Drone Vigia | — | — |
| 6-3 | `conveyor_line` | Linha de Montagem | nova | 6 | 5600×1240 | a prensa vira elevador e, no fim, a linha acelera | Prensa a Vapor | — | — |
| 6-4 | `switch_factory` | Fábrica dos Interruptores | nova | 6 | 5400×1620 | a sala vertical em que cada andar pede a outra cor | — | — | sim |
| 6-5 | `clock_tower` | Torre do Relógio | nova | 6 | 4800×2700 | atravessar o mostrador montado nos ponteiros | Torreta de Arco | — | — |
| 6-6 | `iron_foundry` | Fundição de Ferro | nova | 6 | 6400×1620 | a linha invertida: o interruptor da fundição inverte todas as esteiras | — | Colosso Fundidor (planejado) | sim |
| 7-1 | `cloud_harbor` | Porto das Nuvens | nova | 6 | 5400×1620 | saltar no vazio de propósito para pegar a corrente | Pássaro-Rajada | — | — |
| 7-2 | `floating_gardens` | Jardins Flutuantes | nova | 7 | 5600×2160 | subir por baixo das ilhas pelas raízes pendentes | Nuvem Marota, Semente-Espinho | — | — |
| 7-3 | `updraft_falls` | Cachoeiras Ascendentes | nova | 7 | 4800×2700 | pular de uma cachoeira que sobe para outra que desce | — | — | — |
| 7-4 | `gale_bridges` | Pontes do Vendaval | nova | 7 | 6000×1080 | o vendaval cruzado: duas rajadas em fases opostas sobre um vão de 160 u | Balão-Espinho | — | — |
| 7-5 | `storm_spire` | Agulha da Tempestade | nova | 8 | 4800×3240 | a corrente central só liga entre os trovões | — | — | — |
| 7-6 | `griffin_aerie` | Ninho do Grifo | nova | 8 | 6000×2160 | a grifa só é vencida por quem está acima dela | — | Grifa Ventania (planejado) | sim |
| 8-1 | `misty_marsh` | Brejo da Névoa | nova | 6 | 5400×1080 | o trecho que exige correr encolhe o halo e deixa as sombras chegarem | Sombra-Errante, Sapo-do-Lodo | — | — |
| 8-2 | `lantern_bog` | Charco das Lanternas | nova | 7 | 5800×1620 | lanternas-boia são o único caminho sobre a poça escura | Mão-do-Lodo | — | — |
| 8-3 | `sunken_mansion` | Casarão Afundado | nova | 7 | 5600×2160 | no salão de baile as ossadas se remontam no compasso da valsa | Ossada do Pântano | — | — |
| 8-4 | `lights_out` | Apagão no Pântano | nova | 7 | 5400×1620 | o vento apaga todas as lanternas e só as mariposas iluminam | — | — | sim |
| 8-5 | `phantom_mire` | Lodaçal Fantasma | nova | 8 | 6200×1620 | a ponte fantasma só existe enquanto a sombra-guardiã está paralisada no halo | — | — | sim |
| 8-6 | `lantern_keep` | Torre do Lanterneiro | nova | 8 | 5200×3240 | o contrapeso da grande lanterna vira elevador | — | Vulto Apagador (planejado) | sim |
| 9-1 | `basalt_bridges` | Pontes de Basalto | legada 5-1 | 8 | 5200×1240 | a nova ponte levadiça sobre o rio de lava no fim | Brasa Andante, Ermitão-de-Basalto, Boca-de-Fornalha, Golem de Basalto | — | — |
| 9-2 | `echo_furnace` | Fornalha dos Ecos | legada 5-2 | 8 | 4800×1240 | a galeria dos ecos: uma rota alta inteira acima das fornalhas | Morcego-Brasa | — | — |
| 9-3 | `last_flame` | A Última Chama | legada 5-3 | 9 | 5200×1240 | a rota da chama ancestral passa por cima dos dois últimos canais | — | Guardião da Última Chama (minichefe, implementado) | — |
| 9-4 | `rising_magma` | Magma Ascendente | nova | 8 | 4200×3240 | o magma recua e é preciso descer antes que volte | Salta-Brasa | — | sim |
| 9-5 | `ash_gauntlet` | Corredor de Cinzas | nova | 9 | 6800×1620 | blocos do Ermitão-de-Basalto chutados por cima da lava limpam a margem de lá | — | — | — |
| 9-6 | `magma_throne` | Trono de Magma | nova | 9 | 6400×2160 | as ilhas do trono afundam e voltam com a maré de magma | — | Salamandra Caldera (planejado) | sim |
| 10-1 | `starlit_gate` | Portão Estrelado | nova | 8 | 5600×1620 | o último bolsão de baixa gravidade cobre o vazio entre duas torres | Sentinela Estelar | — | — |
| 10-2 | `constellation_path` | Trilha das Constelações | nova | 9 | 6000×2160 | revelar a ponte em cadeia: cada estrela revelada é o degrau para bater na próxima | Cometa Errante | — | — |
| 10-3 | `gravity_halls` | Salões da Gravidade | nova | 9 | 5600×2160 | vento solar dentro da baixa gravidade leva Lume longe demais | Guardião da Constelação | Guardião da Constelação (elite em papel de minichefe) | — |
| 10-4 | `mirror_sanctum` | Santuário dos Reflexos | nova | 9 | 6400×2700 | os espelhos do segundo átrio misturam dois mundos na mesma sala | — | — | — |
| 10-5 | `eclipse_bastion` | Bastião do Eclipse | nova | 10 | 7200×2160 | cada farol reaceso devolve um pouco de luz ao bastião que escurece | — | — | — |
| 10-6 | `throne_of_eclipse` | Trono do Eclipse | nova | 10 | 6800×2700 | a luz do próprio Eclipse, refletida num espelho, abre o seu núcleo | — | Eclipse Devorador (planejado) | sim |

## 6. Ajustes propostos ao registro de inimigos

O plano **segue o registro atual** (`lume/data/enemies.json`): toda espécie estreia exatamente na fase do seu `introduced_in` e só aparece em mundos do seu habitat (ou em sub-áreas `underground`/`fortress`/`underwater` quando listadas). Nada foi editado no registro. Os ajustes abaixo resolvem conflitos entre o registro e as regras do plano; nenhum é necessário para implementar as fases como estão.

### 6.1 Conflito com a regra de no máximo 2 espécies novas por fase

Quatro fases recebem 3 ou 4 estreias pelo registro atual. O plano as mantém (para cumprir `introduced_in`), separa cada estreia num trecho próprio e propõe:

| Fase | Estreias hoje | Ajuste proposto | Resultado | Justificativa |
| --- | --- | --- | --- | --- |
| `windswept_dunes` (2-1) | escaravelho_areia, tatu_bola, cacto_sentinela | `tatu_bola.introduced_in`: `windswept_dunes` → `canyon_bridges` | 2-1: escaravelho + cacto; 2-2: abutrinho + tatu | O casco já foi ensinado com o caramujo (Mundo 1); `canyon_bridges` já tem um tatu (x1120). O tatu de x840 em 2-1 vira um segundo escaravelho. |
| `crystal_lake` (4-1) | pinguim_patrulha, caracol_cristal, coruja_nevada | `coruja_nevada.introduced_in`: `crystal_lake` → `blue_ascent` | 4-1: pinguim + caracol; 4-2: boneco + coruja | O voador em onda já é conhecido; `blue_ascent` tem só 2 inimigos e ganha a coruja planejada. A coruja de x1580 em 4-1 vira um segundo caracol. |
| `glowing_canopy` (5-1) | cogumelo_saltitante, caracol_musgo, mariposa_lume, planta_esporos | `planta_esporos.introduced_in` → `firefly_ruins`; `cogumelo_saltitante.introduced_in` → `ancestral_tree` | 5-1: caracol-musgo + mariposa; 5-2: besouro-casca + planta; 5-3: guardião + cogumelo | `firefly_ruins` já tem uma planta (x2990). Só a planta de x1320 em 5-1 precisa ser trocada; com o ajuste, retirar o cogumelo de 5-1 e 5-2 no plano. |
| `basalt_bridges` (9-1) | brasa_andante, tartaruga_basalto, boca_fornalha, golem_basalto | `boca_fornalha.introduced_in` → `echo_furnace`; `tartaruga_basalto.introduced_in` → `last_flame` | 9-1: brasa + golem; 9-2: boca + morcego; 9-3: Ermitão-de-Basalto + guardião | `echo_furnace` já tem boca (x1000) e `last_flame` já tem o ermitão (x650); só a boca (x2720) e o ermitão (x3900) de 9-1 mudam. São variantes de famílias conhecidas, então a exceção pesa menos no Mundo 9. |

### 6.2 Registro dos chefes de mundo

Já entraram no registro durante a redação (o plano os adota): `escaravelho_rei` (família `scarab_king`, 3 PV, implementada); `morsa_gelomar` (família `ice_walrus`, 5 PV, implementada).

Os 7 chefes ainda planejados precisam de entradas `boss: true` (o motor bloqueia a saída enquanto houver chefe vivo):

| id proposto | Nome | `behavior` novo | `habitats` | `introduced_in` | PV |
| --- | --- | --- | --- | --- | ---: |
| `ermitao_ancora` | Ermitão-Âncora | `anchor_hermit` | coast, underwater | `sunken_galleon` | 5 |
| `imperatriz_mariposa` | Imperatriz Mariposa | `moth_empress` | forest, fortress | `root_sanctum` | 6 |
| `colosso_fundidor` | Colosso Fundidor | `foundry_colossus` | city, fortress | `iron_foundry` | 5 |
| `grifa_ventania` | Grifa Ventania | `gale_griffin` | sky, fortress | `griffin_aerie` | 6 |
| `vulto_apagador` | Vulto Apagador | `lantern_shade` | swamp, fortress | `lantern_keep` | 6 |
| `salamandra_caldera` | Salamandra Caldera | `caldera_salamander` | volcano, fortress | `magma_throne` | 7 |
| `eclipse_devorador` | Eclipse Devorador | `eclipse` | citadel | `throne_of_eclipse` | 9 |

### 6.3 Observações (sem mudança obrigatória)

- `polvo_tinteiro` tem só o habitat `underwater`: no Mundo 3 o plano o restringe às sub-áreas submersas (`coral_maze`, `sunken_galleon`) e, depois, aos reflexos do Mundo 10. Opcional: acrescentar `coast` permitiria usá-lo em mar aberto de `current_depths` sem sub-área.
- `semente_espinho` lista `grassland`, mas estreia em `floating_gardens` (Mundo 7), depois do único mundo de campina; o habitat é inócuo. Se o objetivo for reaproveitá-la, `citadel` ou `fortress` seriam úteis no Mundo 10.
- `guardiao_constelacao` tem `boss: false`: no plano ele cumpre o papel de minichefe de `gravity_halls`, mas não bloqueia a bandeira. Se a luta tiver de ser obrigatória, é preciso um portão (switch + `boss_arena`) ou marcá-lo como chefe.
- O registro redesenhou três espécies durante a redação (ids mantidos): `tartaruga_basalto` virou **Ermitão-de-Basalto** (caranguejo-ermitão num bloco de basalto chutável), `assombracao_timida` virou **Sombra-Errante** (paralisa no halo da lanterna de Lume em vez de reagir ao olhar) e `bolha_magma` virou **Salta-Brasa**. O plano já usa os nomes e regras novos. Como o chefe planejado do Mundo 3 também é um caranguejo-ermitão (Ermitão-Âncora), manter silhuetas bem distintas (popa de galeão × bloco de basalto) ou renomear o chefe se a semelhança incomodar.
- A família `emerger` tem timidez padrão (`shy_radius` 42): `mao_lodo` e `moreia_toca` também não emergem com Lume encostado, como `flor_mordedora`. O plano usa isso como ferramenta (corredor de moreias de `tide_pools`); vale registrar na descrição.

## 7. Requisitos de motor e fases bloqueadas

O briefing listava como "só dados" a alternância de interruptores, `rising_lava`, a máscara de escuridão, a física de areia movediça, `camera_lock`/`boss_arena` e as paredes quebráveis. **Durante a redação outros agentes implementaram parte disso** (estado conferido em `lume/core/game.py`, `lume/levels/schema.py` e `lume/render/scene.py`):

| Recurso | Estado no snapshot | O que o plano ainda pede |
| --- | --- | --- |
| `boss_arena` / `camera_lock` | implementado (`Game._events`: trava de câmera, portões `close`/`open`, reabertura com a vitória) | nada; as fases de chefe só declaram o evento |
| Areia movediça (`quicksand`) | implementado (`Game._quicksand`: anda a 45%, pulo a 62%, afunda e mata ao cobrir Lume) | nada; os testes das fases pedem saída em ≤ 2 pulos |
| Interruptores | parcial: bloco `?` com recompensa `toggle` alterna os blocos `switch` do grupo (`Game.toggle_group`); o evento `toggle_switch` ainda não é tratado | interruptor temporizado, gatilho por evento, ligação a esteiras e a plataformas condicionais |
| `rising_lava` | parcial: subida única de um perigo até `to` com `speed`, disparada por x (`Game._update_rising`) | ciclos, gatilho por altura/tempo/chefe, aviso sonoro, etapas, reposição no checkpoint, variante água (zona swim) |
| Escuridão (`dark` + `lights`) | parcial: máscara desenhada com o halo de Lume (120 u; 64 u correndo) em `Scene._darkness`; o evento `lights` ainda não é tratado | lanternas fixas/acendíveis com raio e duração, apagão global, raio progressivo |
| Paredes quebráveis | não implementado | só segredos (os tijolos existentes servem de alternativa) |
| Chefes de mundo | 3 de 10 implementados (`thorn_boar`, `scarab_king`, `ice_walrus`) | 7 famílias novas |

Uma fase é **bloqueada** quando a experiência principal depende de um item ainda pendente; **não bloqueada** quando o item só afeta um segredo, uma sala opcional ou degrada com elegância (ex.: sem lanternas a fase fica jogável com o halo de Lume).

| Requisito pendente | Fases bloqueadas | Fases que só se beneficiam |
| --- | --- | --- |
| Extensão de `rising_lava`: ciclos de subida e descida, gatilho por altura/tempo/chefe, etapas com aviso, reposição no checkpoint, variante com zona swim | `sunken_galleon`, `rising_magma`, `magma_throne`, `throne_of_eclipse` | `tide_pools` |
| Paredes quebráveis (segredos `breakable_path` além dos tijolos) | — | `frost_citadel`, `root_sanctum` |
| Extensão de luz: lanternas fixas e acendíveis (raio e duração) e evento `lights` global | `lights_out`, `lantern_keep`, `throne_of_eclipse` | `whispering_hollow`, `storm_spire`, `lantern_bog`, `phantom_mire`, `ash_gauntlet`, `eclipse_bastion` |
| Extensão de interruptores: evento `toggle_switch` por gatilho, interruptor temporizado, ligação de grupos a esteiras/plataformas | `switch_factory`, `iron_foundry`, `phantom_mire` | — |
| Comportamentos dos 7 chefes planejados (`lume/core/behaviors/bosses.py`) | `sunken_galleon`, `root_sanctum`, `iron_foundry`, `griffin_aerie`, `lantern_keep`, `magma_throne`, `throne_of_eclipse` | — |

**Fases bloqueadas (11):** `sunken_galleon`, `root_sanctum`, `switch_factory`, `iron_foundry`, `griffin_aerie`, `lights_out`, `phantom_mire`, `lantern_keep`, `rising_magma`, `magma_throne`, `throne_of_eclipse`. Em `switch_factory` o bloqueio é parcial (só os trechos com interruptor temporizado).

**Fases implementáveis com o motor atual (49):** `first_steps`, `valley_canals`, `orchard_guardian`, `windmill_heights`, `meadow_burrows`, `bramble_fortress`, `windswept_dunes`, `canyon_bridges`, `sand_temple`, `sandstorm_pass`, `sunken_oasis`, `scarab_pyramid`, `shell_beach`, `tide_pools`, `lighthouse_reef`, `current_depths`, `coral_maze`, `crystal_lake`, `blue_ascent`, `blizzard_heart`, `slippery_slopes`, `avalanche_ridge`, `frost_citadel`, `glowing_canopy`, `firefly_ruins`, `ancestral_tree`, `vine_bridges`, `whispering_hollow`, `gear_district`, `steam_works`, `conveyor_line`, `clock_tower`, `cloud_harbor`, `floating_gardens`, `updraft_falls`, `gale_bridges`, `storm_spire`, `misty_marsh`, `lantern_bog`, `sunken_mansion`, `basalt_bridges`, `echo_furnace`, `last_flame`, `ash_gauntlet`, `starlit_gate`, `constellation_path`, `gravity_halls`, `mirror_sanctum`, `eclipse_bastion`.

Usos opcionais de `camera_lock` para enquadramento (já suportado): `lighthouse_reef`, `avalanche_ridge`, `clock_tower`, `updraft_falls`, `sunken_mansion`, `gravity_halls`.

Renderização de zonas (partículas de vento, correntes, volumes de água, birutas sincronizadas com `Game.zone_active`) é tarefa de arte/render e não aparece como requisito de motor; está descrita em *Elementos animados* de cada fase.

## 8. Correções das fases legadas e das implementações iniciais

Varredura feita sobre os arquivos atuais (`lume/data/levels/**`): para cada inimigo terrestre, procurou-se sólido não semissólido com base entre `y_chão−158` e `y_chão−30` sobre a patrulha (a cabeça bate ao saltar por cima) e mediu-se a distância até o próximo vão. Também se conferiu a zona segura dos checkpoints. Correções planejadas (detalhes na seção de cada fase):

| Fase | Problema encontrado | Correção planejada |
| --- | --- | --- |
| `canyon_bridges` | **Problema conhecido:** pedra frágil `crumble02` (x1040, y288, base 306) sobre o tatu-bola `[1060, 1220]`, 70 u antes do vão x1290→1420: o salto sobre o tatu batia a cabeça e caía no vão. | **Já corrigido no arquivo durante a redação** (pedras frágeis movidas para x770 e x920, relíquia alta em x954). O plano mantém a correção, acrescenta o teste de regressão nas duas alturas e a regra geral *teto sobre patrulha*; alternativa equivalente: tornar a pedra semissólida. |
| `orchard_guardian` | Bolota `[1430, 1590]` sob a pedra frágil x1450–1550, 60 u antes do vão. | Bolota para `[2240, 2400]`; checkpoint x1990 → x1900. |
| `glowing_canopy` | Caracol-musgo `[760, 920]` sob folha frágil x750–852, 60 u antes do vão. | Caracol para `[3250, 3450]`; cogumelo saltitante novo em `[420, 560]`. |
| `firefly_ruins` | Besouro-casca (estreia) `[1200, 1380]` sob tijolo x1110–1214, 70 u antes do vão. | Besouro para `[1860, 2060]` (chão aberto). |
| `sand_temple` | Escorpião (estreia) `[1340, 1500]` sob tijolo x1270–1374, 50 u antes do vão. | Escorpião para `[470, 600]` (entre o bloco ? e o cano). |
| `blue_ascent` | Caracol-de-cristal `[1010, 1230]` sob beirais x910 e x1060, 40 u antes do vão. | Beirais `ledge01`/`ledge02` viram semissólidos de gelo. |
| `windswept_dunes` | Escaravelho `[1450, 1670]` sob ?02 e tijolo03 (base y318), 100 u antes do vão. | ?02 e tijolo03 sobem 32 u (y258); patrulha `[1600, 1700]`. |
| `valley_canals` | Caramujo `[1130, 1300]` sob ?02/tijolo01 (base y348), 80 u antes do vão. | Caramujo para `[260, 420]`. |
| `first_steps` | Bolota 1 `[650, 900]` sob tijolo x780–872 (base y404); bolota 2 alcança a zona do checkpoint x1510. | Bolota 1 em `[640, 775]`; checkpoint x1510 → x1600. |
| `ancestral_tree` | Planta `[3240, 3420]` sob a plataforma vertical x3380, 110 u antes do vão. | Planta para x3200. |
| `echo_furnace` | Golem `[3360, 3530]` sob a plataforma vertical x3600 (base até y366). | Golem para `[3260, 3420]`; espinhos x4490 → x4560 sob a estreia do morcego. |
| `crystal_lake` | Pinguim `[3070, 3300]` com visão 280 alcança o pouso no gelo (x2740) antes da frenagem. | Pinguim `[3200, 3400]`, visão 220. |
| `blizzard_heart` | Carneiro (estreia) `[575, 725]` sem parede: a investida não termina em batida. | Bloco de granito x540–580 e patrulha `[580, 740]`. |
| `windmill_heights` | 1 checkpoint em 5600 u; toca da flor x2900 dentro da zona do checkpoint x2700; canal de 220 u com uma pá. | 2º checkpoint x4600; checkpoint x2620 e flor x2960; pás do canal largo já em fases opostas; no canal de 220 u (pá de raio 50) exigir pouso ≤ 125 u em ≥ 40% do ciclo ou acrescentar o apoio de pedra x4400. |
| `meadow_burrows` | Três patrulhas cruzam a zona do checkpoint do túnel; ouriço na zona do checkpoint de superfície; `surface_after` cobre o perigo `hz_water02` (x4400–4560); 4 relíquias. | Checkpoint do túnel x2700 com patrulhas recuadas; ouriço `[3940, 4140]`; cortar o terreno ou remover o perigo; padronizar em 3 relíquias. |
| `sandstorm_pass` | Vão x3000→3200 de 200 u (acima de 150 u) só vencível com o vento contínuo +140; 1 checkpoint em 5600 u; serpente de estreia cruza a zona do checkpoint x2150. | Reduzir o vão para 150 u ou manter como exceção testada; 2º checkpoint x3300 (zona a favor encurtada para x3000–3220); serpente `[2500, 2990]`. |
| `sunken_oasis` | Dificuldade 4 (faixa do Mundo 2 é 1–3); 1 checkpoint em 6000 u; lançador de estreia alcança o checkpoint; a física de areia movediça (implementada durante a redação) mata ao cobrir Lume. | Dificuldade 3; 2º checkpoint x3380; lançador `[2560, 2780]`; conferir saída de cada poça com o pulo reduzido; poça longa com apoios no fim. |
| `scarab_pyramid` | Dificuldade 4; 1 checkpoint antes de um chefe; 14 moedas. | Dificuldade 3; 2º checkpoint x2620 na antessala (escaravelho recuado para `[2160, 2380]`); ~60 moedas. |
| `bramble_fortress` | Fosso x900–1040 sem chão (letal) apesar de o mundo ensinar espinheiro não letal; flores na zona do checkpoint; 1 checkpoint antes de um chefe de 3 PV. | Fundo de espinheiro em y540 com degraus; flores x2560/x2720; 2º checkpoint na antessala x3080. |

Para os três níveis vulcânicos legados (agora Mundo 9), o plano mantém o traçado e eleva a dificuldade com: canais alargados até 150 u (limite do Mundo 9 = 160 u), chamas duplas sobre saltos obrigatórios, densidade de 3–5 para 12–18 inimigos (inclusive ossadas, de habitat `volcano`), plataformas móveis obrigatórias, dicas mais curtas, um checkpoint extra onde o trecho passa de 2500 u e uma rota opcional nova com a terceira relíquia; `basalt_bridges` ganha uma seção final (ponte levadiça) e a bandeira passa a x5050.

## 9. Fases

## Mundo 1 — Reino Verde (`green_kingdom`)

Colinas, canais, moinhos e pomares. Fundamentos com dois andares: o chão esconde tocas e o ar esconde blocos; termina num javali que só para ao bater na muralha. Detalhes do mundo em [`MUNDO_01.md`](MUNDO_01.md).

### 1-1 · Primeiros Passos (`first_steps`)

*Ideia própria:* o ar guarda segredos: bloco oculto e galhos semissólidos.

- **Identificador:** `first_steps`
- **Nome:** Primeiros Passos
- **Mundo:** Reino Verde (`green_kingdom`, bioma `grassland`), fase 1 de 6 — origem: legada 1-1
- **Objetivo:** Ensinar andar, correr, saltar com altura variável, bater em blocos e pisar inimigos; o primeiro vão letal só aparece depois de dois exercícios de salto sem risco, e a fase termina com a primeira descoberta de segredo.
- **Tema visual:** Campina ensolarada de manhã: colinas azul-esverdeadas em camadas, moinho distante (camada back), cercas de madeira, carvalhos redondos e flores silvestres; canais de água cristalina nos dois vãos; lampião do checkpoint com Vovó Candeia.
- **Mecânica principal:** Corrida e salto variável (segurar = até 112 u de altura; correndo, alcance de 259 u)
- **Mecânicas secundárias:**
  - blocos ? e tijolos batidos por baixo
  - pisão em inimigos e casco chutável
  - cano de passagem (↓) para câmara secreta
  - bloco oculto sugerido por moedas
  - galhos semissólidos (atravessáveis por baixo) como rota opcional
- **Dificuldade:** 1/10
- **Duração planejada:** 40–100 s (primeira travessia → exploração completa)
- **Tamanho do cenário:** 3200 × 1240 u
  - `main` [grassland] 0,0 3200×540: campina com dois canais (100 u e 120 u)
  - `pipe_room_area` [underground] 2169,700 960×540: câmara secreta do cano
- **Caminho principal** (sequência de ensino):
  1. **Introdução** (0–400 u) — Spawn em x72 sobre chão largo; fila de 6 moedas (x200) ensina a andar; nenhuma ameaça a menos de 600 u.
  2. **Demonstração segura** (400–640 u) — Fileira de blocos em y350 (? crescer x410, tijolo, ? moeda, ? coração x570): bater por baixo sem risco; o cogumelo rola sobre chão contínuo e alcança quem fica parado.
  3. **Primeiro desafio** (640–1040 u) — Primeira bolota em chão plano (patrulha proposta [640, 775]), 568 u depois do spawn: saltar por cima ou pisar; o tijolo baixo x780 vira degrau.
  4. **Escalada** (1040–1920 u) — Primeiro canal (100 u) só depois dos dois exercícios; segunda bolota; tijolos em escada (x1680 y374 → x1830 y306) com a relíquia alta; checkpoint (proposto em x1600).
  5. **Combinação** (1920–2300 u) — Canal de 120 u com pista livre antes da borda; cano da câmara secreta em x2250 com dica ↓.
  6. **Reviravolta** (2300–2560 u) — O arco de moedas aponta para o bloco oculto (x2460, estrela): o jogo revela que o ar também guarda coisas; bolota nova em [2330, 2440] para o par casco→bolota.
  7. **Teste final** (2560–2900 u) — Caramujo sob galhos semissólidos (x2560 e x2730): pisar, chutar o casco para a direita (derruba a bolota) e subir pelos galhos até a relíquia.
  8. **Recompensa** (2900–3200 u) — Fila de moedas até a bandeira (x3050) em chão plano; fanfarra curta.
- **Caminhos alternativos:**
  - Trilha dos tijolos x1680 → x1830 (relíquia alta), reencontra o chão antes do canal de 120 u.
  - Galhos semissólidos x2560 → x2730 sobre o caramujo (relíquia do galho), reencontra o chão em x2850.
  - Cano x2250 → câmara subterrânea (moedas, coração, relíquia) → retorno em x2322.
- **Inimigos permitidos:** `bolota` (Bolota — estreia), `caramujo` (Caramujo-de-Casca — estreia)
- **Quantidade planejada de inimigos:** 4–5 (chefes não contados)
- **Obstáculos:**
  - 2 canais de água letal (100 u em x1040; 120 u em x1920)
  - tijolos baixos que servem de degrau e de teto (bater por baixo)
- **Itens disponíveis:**
  - crescer: bloco ? x410
  - moeda: bloco ? x490
  - coração: bloco ? x570
  - estrela: bloco oculto x2460
  - coração: câmara secreta x2628
- **Segredos:**
  - `pipe_room` (warp_room) — pista: Cano verde com seta luminosa e placa 'Sobre o cano, pressione ↓' em x2190; recompensa: relíquia relic_room (x2678, y850), coração e 4 moedas
  - `high_route` (high_route) — pista: Trilha de moedas sobe pelos tijolos x1680 e x1830; recompensa: relíquia relic_high (x1886, y232)
  - `branch_route` (optional_challenge) — pista: Galhos da macieira formam degraus acima do caramujo; maçã brilhante no galho de cima; recompensa: relíquia relic_branch (x2780, y246)
  - `hidden_hidden01` (hidden_block) — pista: Arco de moedas e vagalumes convergem para um ponto vazio em x2460; recompensa: estrela (12 s de invencibilidade)
- **Colecionáveis:** ~45 moedas e 3 relíquias
- **Checkpoints:** 1
- **Eventos especiais:**
  - message (x1600): Vovó Candeia acende o lampião — “Cada lampião aceso guarda seu caminho. Se cair, você volta aqui.”
  - message (x2190): dica do cano (já existente como hint)
- **Elementos animados:**
  - pás do moinho distante girando (windmill_blades)
  - capim e flores balançando com o vento
  - água dos canais com brilho e reflexo
  - lampião acendendo quando o checkpoint é ativado
  - folhas e pétalas ao vento (weather leaves)
- **Trilha sonora:** `green_kingdom_main` — manhã alegre: flauta, violão dedilhado e percussão leve (sub-áreas: `green_kingdom_underground`)
- **Condição de conclusão:** Tocar a bandeira em x3050 (base y448).
- **Critérios de teste:**
  - validate_level e validate_campaign sem erros (schema, espécies, bioma, ordem de introdução, warps com chão)
  - route_bot conclui a fase partindo do spawn e de cada um dos 1 checkpoint(s), com inimigos e perigos ativos
  - vãos obrigatórios ≤ 125 u na mesma altura e subidas obrigatórias ≤ 64 u, simulados nas duas alturas do jogador sem coyote nem buffer
  - as 3 relíquias e todas as moedas são alcançáveis (rota de teste dedicada por relíquia; nenhuma moeda leva a morte)
  - estreias (Bolota, Caramujo-de-Casca) em chão plano com ≥ 300 u de aproximação visível, recuo livre e nenhum vão letal a 200 u
  - teto sobre patrulha: nenhum sólido não semissólido com base entre y_chão−158 e y_chão−30 sobre a patrulha de inimigo terrestre a menos de 160 u de um vão obrigatório
  - zona segura de cada checkpoint: chão plano de x−96 a x+192 e nenhum inimigo comum alcança [x−160, x+320] em 3 s de simulação
  - nenhuma ameaça letal a menos de 600 u do spawn; primeiro canal só depois de 2 exercícios de salto (blocos x410–610 e tijolo x780)
  - teto sobre patrulha: nenhum sólido com base entre y_chão−158 e y_chão−30 sobre a patrulha da bolota 1
  - zona segura do checkpoint (x1600) livre de inimigos em simulação de 3 s
  - o cogumelo de crescer de x410 alcança o jogador parado em ≤ 4 s
- **Requisitos de motor:** nenhum (implementável com o motor atual)
- **Plano de melhoria da fase legada:**
  - Manter traçado (3 chãos, canais de 100/120 u, blocos e câmara do cano) e as três relíquias já presentes: câmara (x2678, y850), trilha dos tijolos (x1886, y232) e galho (x2780, y246).
  - Bolota 1: patrulha [650, 900] → [640, 775]; hoje o tijolo x780–872 (base y404) cobre a patrulha e impede saltar por cima dela.
  - Checkpoint x1510 → x1600: a bolota de [1220, 1390] alcança a zona segura [x−160, x+320]; em x1600 a zona [1440, 1920] fica livre e o chão x1504–1792 é plano.
  - Acrescentar 1 bolota em [2330, 2440] (entre o cano e o bloco oculto) para a lição casco→inimigo antes da bandeira.
  - Arte: moinho distante (windmill, camada back, x300 e x2600), cerca (x120–360), carvalhos/arbustos automáticos, placas de madeira nas dicas e o lampião de Vovó Candeia.

### 1-2 · Canais do Vale (`valley_canals`)

*Ideia própria:* a margem elevada esconde três rotas opcionais (alta, ponte e cano).

- **Identificador:** `valley_canals`
- **Nome:** Canais do Vale
- **Mundo:** Reino Verde (`green_kingdom`, bioma `grassland`), fase 2 de 6 — origem: legada 1-2
- **Objetivo:** Desenvolver o salto entre margens de alturas diferentes, apresentar plataformas móveis ainda opcionais e o voador que perde as asas; premiar a exploração com três rotas que reencontram o caminho principal.
- **Tema visual:** Vale de canais e eclusas: margens de pedra com musgo, aqueduto em arcos ao fundo, pontes de tábuas, roda d'água junto à plataforma vertical, patos de madeira e comportas; tarde clara.
- **Mecânica principal:** Plataformas móveis (eixos y e x) e margens em desnível de ±32 u
- **Mecânicas secundárias:**
  - Besouro-Asa: o primeiro pisão arranca as asas e ele segue como Besouro
  - rota alta por tijolos e plataforma móvel
  - ponte semissólida sobre o último canal
  - cano de passagem
- **Dificuldade:** 1/10
- **Duração planejada:** 45–110 s (primeira travessia → exploração completa)
- **Tamanho do cenário:** 3500 × 1240 u
  - `main` [grassland] 0,0 3500×540: vale com três canais (100, 120 e 125 u)
  - `pipe_room_area` [underground] 2529,700 960×540: câmara secreta
- **Caminho principal** (sequência de ensino):
  1. **Introdução** (0–640 u) — Margem plana; ? de crescer em x470; caramujo em chão plano (patrulha proposta [260, 420]) antes do bloco.
  2. **Demonstração segura** (640–1020 u) — Canal de 100 u subindo 32 u até a margem elevada (y416): salto curto e seguro; bolota em [800, 975] que vira no cano x1020.
  3. **Primeiro desafio** (1020–1380 u) — Cano baixo como degrau e blocos x1150–1230 sem inimigo embaixo; plataforma móvel vertical (x1360, ±30 u) sobre o canal de 120 u — opcional: o salto direto alcança.
  4. **Escalada** (1380–2200 u) — Descida de 32 u; checkpoint em x1640; tijolo x1810 → plataforma horizontal x1950 → tijolo x2110 com a relíquia alta.
  5. **Combinação** (2200–2700 u) — Canal final de 125 u (já corrigido) com a ponte semissólida x2236–2386 por cima; ? de fogo em x2490; cano da câmara em x2670.
  6. **Reviravolta** (2700–3000 u) — Besouro-Asa (estreia) em voo ondulado sobre chão plano [2830, 3160]: o pisão arranca as asas — o inimigo muda de regra no meio do encontro.
  7. **Teste final** (3000–3250 u) — Segundo Besouro-Asa mais alto (proposto, y300): escolher entre passar por baixo do voo ou pisar duas vezes.
  8. **Recompensa** (3250–3500 u) — Bandeira em x3350 entre arcos de moedas.
- **Caminhos alternativos:**
  - Rota alta: tijolo x1810 → plataforma móvel x1950 → tijolo x2110 (relíquia alta), reencontra a margem em x2220.
  - Ponte semissólida x2236–2386 em y336 sobre o último canal (relíquia da ponte).
  - Cano x2670 → câmara subterrânea (relíquia e crescer) → retorno em x2742.
- **Inimigos permitidos:** `bolota` (Bolota), `caramujo` (Caramujo-de-Casca), `besouro_alado` (Besouro-Asa — estreia), `besouro` (Besouro — estreia)
- **Quantidade planejada de inimigos:** 4–5 (chefes não contados)
- **Obstáculos:**
  - 3 canais de água letal (100, 120 e 125 u)
  - margem elevada +32 u e descida −32 u
  - plataformas móveis opcionais (y ±30 u; x ±34 u)
- **Itens disponíveis:**
  - crescer: bloco ? x470
  - moeda: bloco ? x1150
  - fogo: bloco ? x2490
  - crescer: câmara secreta x2988
- **Segredos:**
  - `pipe_room` (warp_room) — pista: Cano com seta luminosa e dica 'Há luz dentro deste cano' (x2620); recompensa: relíquia relic_room (x3038, y850) e crescer
  - `high_route` (high_route) — pista: Trilha de moedas sobe pelos blocos e pela plataforma horizontal; recompensa: relíquia relic_high (x2147, y252)
  - `bridge_route` (high_route) — pista: Ponte de tábuas sobre o último canal com moedas em arco; recompensa: relíquia relic_bridge (x2300, y288)
- **Colecionáveis:** ~45 moedas e 3 relíquias
- **Checkpoints:** 1
- **Eventos especiais:**
  - message (x1640): Vovó Candeia — “As pontes e as rodas d'água levam a caminhos altos.”
- **Elementos animados:**
  - roda d'água girando junto à plataforma vertical
  - plataformas móveis com engrenagem visível
  - água dos canais correndo e cascatinha do aqueduto
  - Besouro-Asa batendo os élitros; asas caindo ao ser pisado
- **Trilha sonora:** `green_kingdom_main` — tarde fluvial: mesma melodia com marimba e sons de água (sub-áreas: `green_kingdom_underground`)
- **Condição de conclusão:** Tocar a bandeira em x3350.
- **Critérios de teste:**
  - validate_level e validate_campaign sem erros (schema, espécies, bioma, ordem de introdução, warps com chão)
  - route_bot conclui a fase partindo do spawn e de cada um dos 1 checkpoint(s), com inimigos e perigos ativos
  - vãos obrigatórios ≤ 125 u na mesma altura e subidas obrigatórias ≤ 64 u, simulados nas duas alturas do jogador sem coyote nem buffer
  - as 3 relíquias e todas as moedas são alcançáveis (rota de teste dedicada por relíquia; nenhuma moeda leva a morte)
  - estreias (Besouro-Asa, Besouro) em chão plano com ≥ 300 u de aproximação visível, recuo livre e nenhum vão letal a 200 u
  - teto sobre patrulha: nenhum sólido não semissólido com base entre y_chão−158 e y_chão−30 sobre a patrulha de inimigo terrestre a menos de 160 u de um vão obrigatório
  - zona segura de cada checkpoint: chão plano de x−96 a x+192 e nenhum inimigo comum alcança [x−160, x+320] em 3 s de simulação
  - vãos obrigatórios ≤ 125 u e vencíveis andando (alcance andando 168 u) — regra 2 da pesquisa para W1-L1/L2
  - o Besouro-Asa pisado vira Besouro e continua patrulhando o chão (transform_enemy)
  - teto sobre patrulha: caramujo e bolota sem sólido a menos de 142 u acima da patrulha
  - as plataformas móveis nunca são necessárias: rota do bot que não as toca conclui a fase
- **Requisitos de motor:** nenhum (implementável com o motor atual)
- **Plano de melhoria da fase legada:**
  - Mantidos: 4 margens, vão final já reduzido de 140 para 125 u, ponte semissólida e relíquia relic_bridge (x2300, y288).
  - Caramujo: patrulha [1130, 1300] → [260, 420]; hoje fica sob o bloco ?02/tijolo01 (base y348) a 80 u do canal de 120 u e o salto por cima bate a cabeça.
  - Acrescentar 1 Besouro-Asa em [3000, 3200] (y300) para a revisão do voador antes da bandeira.
  - Arte: roda d'água animada em x1360 (justifica a plataforma vertical), aqueduto em arcos (camada back, x1500–2400), patos de madeira e comporta decorativa no canal final.
  - Evento message no checkpoint (Vovó Candeia).

### 1-3 · Guardião do Pomar (`orchard_guardian`)

*Ideia própria:* o primeiro chefe ensina a esperar a abertura luminosa.

- **Identificador:** `orchard_guardian`
- **Nome:** Guardião do Pomar
- **Mundo:** Reino Verde (`green_kingdom`, bioma `grassland`), fase 3 de 6 — origem: legada 1-3
- **Objetivo:** Primeira grande prova: escadas de tijolo e pedra frágil, voador sobre chão firme e o Guardião do Pomar (3 PV) como chefe intermediário numa arena aberta.
- **Tema visual:** Pomar de macieiras redondas em fileiras, cestos de maçã, escadas de madeira encostadas, muro de pedra baixo; arena cercada de estacas e espantalhos; meio-dia.
- **Mecânica principal:** Plataformas frágeis (cedem 0,65 s após o pouso e voltam em 3 s) e leitura da guarda aberta do guardião
- **Mecânicas secundárias:**
  - escada de tijolos
  - galhos semissólidos (rota da copa)
  - voador sobre chão firme
  - chefe intermediário guardiao_pomar (salta e dispara)
- **Dificuldade:** 2/10
- **Duração planejada:** 60–130 s (primeira travessia → exploração completa)
- **Tamanho do cenário:** 3900 × 1240 u
  - `main` [grassland] 0,0 3900×540: pomar com três canais (120/100/100 u) e arena aberta x3190–3660
  - `pipe_room_area` [underground] 2009,700 960×540: câmara secreta
- **Caminho principal** (sequência de ensino):
  1. **Introdução** (0–600 u) — Blocos ? (crescer x330, moeda x410); dica 'O pomar guarda sua primeira grande prova'.
  2. **Demonstração segura** (600–1000 u) — Caramujo em [600, 830] e canal de 120 u: revisão do mundo.
  3. **Primeiro desafio** (1000–1650 u) — Escada tijolo x1130 → tijolo x1280 → pedra frágil x1450 (relíquia alta): a pedra cede 0,65 s após o pouso — lição de 'não parar', com chão contínuo embaixo (falha barata).
  4. **Escalada** (1650–2240 u) — Canal de 100 u; checkpoint (proposto x1900); cano da câmara x2170.
  5. **Combinação** (2240–2780 u) — Bolota (proposta [2240, 2400]) e Besouro-Asa baixo em [2410, 2630] sob os galhos semissólidos da copa: primeira combinação chão + ar; ? de fogo em x2580.
  6. **Reviravolta** (2780–3190 u) — Antessala com coração no chão (x2970) e tijolo x3100: respiro antes do chefe.
  7. **Teste final** (3190–3660 u) — Arena: o guardião avança, salta aos 2 s do ciclo e dispara uma esfera aos 2,7 s; a guarda abre por 1,65 s a cada 4,8 s (1,1 s a cada 3,8 s na segunda metade).
  8. **Recompensa** (3660–3900 u) — Bandeira em x3750 liberada pela derrota do guardião.
- **Caminhos alternativos:**
  - Rota alta pelos tijolos e pela pedra frágil (relíquia alta), reencontra o chão antes do canal de 100 u.
  - Rota da copa pelos galhos semissólidos x2430 → x2560 (relíquia da copa).
  - Cano x2170 → câmara (relíquia, estrela).
- **Inimigos permitidos:** `bolota` (Bolota), `caramujo` (Caramujo-de-Casca), `besouro_alado` (Besouro-Asa), `besouro` (Besouro), `guardiao_pomar` (Guardião do Pomar — estreia)
- **Quantidade planejada de inimigos:** 4–6 (chefes não contados)
- **Obstáculos:**
  - 3 canais de água letal (120/100/100 u)
  - pedra frágil x1450 (rota alta)
  - esferas do guardião (projéteis retos)
- **Itens disponíveis:**
  - crescer: ? x330
  - moeda: ? x410
  - fogo: ? x2580
  - estrela: câmara x2468
  - coração: chão x2970 (antessala)
- **Segredos:**
  - `pipe_room` (warp_room) — pista: Cano com seta luminosa e dica próxima; recompensa: relíquia relic_room (x2518, y850) e estrela
  - `high_route` (high_route) — pista: Trilha de moedas sobe pelos blocos até a pedra frágil; recompensa: relíquia relic_high (x1482, y257)
  - `canopy_route` (optional_challenge) — pista: Galhos sob o voo do besouro levam à copa; maçã dourada no topo; recompensa: relíquia relic_canopy (x2600, y252)
- **Colecionáveis:** ~45 moedas e 3 relíquias
- **Checkpoints:** 1
- **Eventos especiais:**
  - message (x1900): Vovó Candeia — “Pedras rachadas cedem: atravesse sem parar.”
  - message (x3000): “Pule sobre o guardião quando ele baixar a guarda.” (dica existente)
  - boss_arena opcional (x3190): lock [3140, 0, 960, 540] — melhoria visual; a bandeira já espera a derrota
- **Elementos animados:**
  - macieiras com maçãs balançando
  - espantalhos girando ao vento
  - guardião abrindo a guarda (brilho turquesa)
  - pedra frágil tremendo antes de ceder e reaparecendo
- **Trilha sonora:** `green_kingdom_main` — pomar ao meio-dia; na arena a percussão dobra numa camada de tensão (sub-áreas: `green_kingdom_underground`)
- **Condição de conclusão:** Derrotar o Guardião do Pomar (3 pisões com a guarda aberta) e tocar a bandeira em x3750.
- **Critérios de teste:**
  - validate_level e validate_campaign sem erros (schema, espécies, bioma, ordem de introdução, warps com chão)
  - route_bot conclui a fase partindo do spawn e de cada um dos 1 checkpoint(s), com inimigos e perigos ativos
  - vãos obrigatórios ≤ 125 u na mesma altura e subidas obrigatórias ≤ 64 u, simulados nas duas alturas do jogador sem coyote nem buffer
  - as 3 relíquias e todas as moedas são alcançáveis (rota de teste dedicada por relíquia; nenhuma moeda leva a morte)
  - teto sobre patrulha: nenhum sólido não semissólido com base entre y_chão−158 e y_chão−30 sobre a patrulha de inimigo terrestre a menos de 160 u de um vão obrigatório
  - zona segura de cada checkpoint: chão plano de x−96 a x+192 e nenhum inimigo comum alcança [x−160, x+320] em 3 s de simulação
  - o guardião só recebe dano com a guarda aberta e a bandeira só conclui após a derrota (bosses_alive)
  - teto sobre patrulha: a bolota não fica sob a pedra frágil x1450–1550
  - pedra frágil cede em 0,65 s e só reaparece sem sobrepor o jogador
  - arena de chão contínuo: nenhum vão entre x3190 e x3660
- **Requisitos de motor:** nenhum (implementável com o motor atual)
- **Plano de melhoria da fase legada:**
  - Mantidos: traçado, guardião com 3 PV em [3190, 3660] e as três relíquias (alta x1482, câmara, copa x2600).
  - Bolota: patrulha [1430, 1590] → [2240, 2400]; hoje fica sob a pedra frágil x1450–1550 (base y314) a 60 u do canal.
  - Checkpoint x1990 → x1900 para que a nova patrulha da bolota fique fora da zona segura ([1740, 2220]).
  - Arte: macieiras com maçãs, espantalhos que marcam o ciclo do guardião, cerca de estacas na arena.
  - Evento message no checkpoint (Vovó Candeia) e camera_lock opcional na arena (não obrigatório: o guardião já bloqueia a bandeira).

### 1-4 · Colina dos Moinhos (`windmill_heights`)

*Ideia própria:* as pás do moinho viram pontes giratórias sobre o canal.

- **Identificador:** `windmill_heights`
- **Nome:** Colina dos Moinhos
- **Mundo:** Reino Verde (`green_kingdom`, bioma `grassland`), fase 4 de 6 — origem: nova
- **Objetivo:** Apresentar a mecânica especial do Reino Verde — molas de feno e pás de moinho giratórias — e a Flor-Mordedora, culminando em travessias de canal apoiadas nas pás.
- **Tema visual:** Colina dos moinhos ao vento: moinhos de pedra com pás de lona, campos de trigo dourado, fardos de feno (molas), canal largo ao pé da colina e nuvens rápidas de fim de manhã.
- **Mecânica principal:** Pás de moinho: plataformas com movimento circular (motion axis circle) + molas de feno (spring, ≈900 u/s)
- **Mecânicas secundárias:**
  - Flor-Mordedora: sobe da toca, morde e recua; não sai com Lume encostado
  - planalto (+148 u) acessível só pela mola
  - rota alta de beirais
  - cano para a câmara secreta
- **Dificuldade:** 2/10
- **Duração planejada:** 70–150 s (primeira travessia → exploração completa)
- **Tamanho do cenário:** 5600 × 1240 u
  - `main` [grassland] 0,0 5600×540: colina com planalto (x1180–1700, y300) e três canais (560, 120 e 220 u) cruzados por pás
  - `pipe_room_area` [underground] 4640,700 960×540: câmara secreta
- **Caminho principal** (sequência de ensino):
  1. **Introdução** (0–600 u) — Pá-demonstração (moving01, círculo em x270) sobre chão firme e ? em x380: subir na pá e descer sem risco.
  2. **Demonstração segura** (600–1180 u) — Mola de feno x600 sob o beiral x660–810 (y250): quicar e segurar o salto; bolota em [830, 1170] em chão plano.
  3. **Primeiro desafio** (1140–1700 u) — Mola x1140 é o único acesso ao planalto (+148 u): uso obrigatório em chão seguro; Besouro-Asa sobre o planalto.
  4. **Escalada** (1700–2560 u) — Canal largo (560 u) cruzado por duas pás (x2095 e x2345, fases opostas) com o beiral x2252 de descanso (relíquia do moinho): primeira travessia obrigatória sobre água.
  5. **Combinação** (2560–3420 u) — Checkpoint (proposto x2620); Flor-Mordedora (estreia) em tocas no chão plano (propostas x2960 e x3150): esperar recolher ou saltar; tijolo x3100; canal de 120 u.
  6. **Reviravolta** (3420–4300 u) — Caramujo, mola x3880 → beirais x3950/x4150 (relíquia alta) e flor entre tijolos (x4060): a mola agora é rota opcional e arriscada.
  7. **Teste final** (4300–4560 u) — Travessia final do canal de 220 u na pá x4365 (com apoio de pedra proposto em x4400); 2º checkpoint proposto em x4600.
  8. **Recompensa** (4560–5600 u) — Prado final: bloco oculto com estrela (x4700, arco de moedas), cano da câmara (x4900), Besouro-Asa e bandeira em x5450.
- **Caminhos alternativos:**
  - Beiral x660–810 pela mola x600 (moedas).
  - Mola x3880 → beiral x3950 → beiral x4150 (relíquia alta).
  - Cano x4900 → câmara secreta (relíquia e coração).
- **Inimigos permitidos:** `bolota` (Bolota), `caramujo` (Caramujo-de-Casca), `besouro_alado` (Besouro-Asa), `besouro` (Besouro), `flor_mordedora` (Flor-Mordedora — estreia)
- **Quantidade planejada de inimigos:** 8–10 (chefes não contados)
- **Obstáculos:**
  - canal de 560 u atravessado por 2 pás circulares
  - canal de 120 u
  - canal de 220 u com 1 pá (+ apoio proposto)
  - planalto +148 u acessível só pela mola
- **Itens disponíveis:**
  - crescer: ? x380
  - fogo: ? x3480 (para as flores)
  - estrela: bloco oculto x4700
  - coração: câmara x5138
- **Segredos:**
  - `mill_ledge` (optional_challenge) — pista: Beiral estreito entre as duas pás do canal; moedas sobem do topo da volta da pá; recompensa: relíquia relic_mill (x2263, y206)
  - `high_route` (high_route) — pista: Mola de feno diante de beirais flutuantes; moedas em diagonal; recompensa: relíquia relic_high (x4210, y176)
  - `pipe_room` (warp_room) — pista: Cano com seta luminosa no prado final; recompensa: relíquia relic_room (x5188, y850) e coração
  - `hidden_star` (hidden_block) — pista: Arco de moedas se curva para o vazio em x4700 (dica em x4620); recompensa: estrela
- **Colecionáveis:** ~60 moedas e 3 relíquias
- **Checkpoints:** 2
- **Eventos especiais:**
  - message (x2620): Vovó Candeia — “As pás sobem e descem: pule quando estiverem no alto da volta.”
- **Elementos animados:**
  - pás dos moinhos girando em sincronia com as plataformas circulares
  - fardos de feno comprimindo ao quicar
  - trigo ondulando
  - Flor-Mordedora subindo da toca com terra voando
  - água do canal
- **Trilha sonora:** `green_kingdom_main` — variação ventosa: acordeão e assobios, compasso 3/4 lembrando o giro das pás (sub-áreas: `green_kingdom_underground`)
- **Condição de conclusão:** Tocar a bandeira em x5450.
- **Critérios de teste:**
  - validate_level e validate_campaign sem erros (schema, espécies, bioma, ordem de introdução, warps com chão)
  - route_bot conclui a fase partindo do spawn e de cada um dos 2 checkpoint(s), com inimigos e perigos ativos
  - vãos obrigatórios ≤ 125 u na mesma altura e subidas obrigatórias ≤ 64 u, simulados nas duas alturas do jogador sem coyote nem buffer
  - as 3 relíquias e todas as moedas são alcançáveis (rota de teste dedicada por relíquia; nenhuma moeda leva a morte)
  - estreias (Flor-Mordedora) em chão plano com ≥ 300 u de aproximação visível, recuo livre e nenhum vão letal a 200 u
  - teto sobre patrulha: nenhum sólido não semissólido com base entre y_chão−158 e y_chão−30 sobre a patrulha de inimigo terrestre a menos de 160 u de um vão obrigatório
  - zona segura de cada checkpoint: chão plano de x−96 a x+192 e nenhum inimigo comum alcança [x−160, x+320] em 3 s de simulação
  - as pás de cada canal oferecem pouso a ≤ 125 u das margens durante ≥ 40% do ciclo (simulação por fase)
  - a mola x1140 leva o jogador pequeno e grande ao planalto y300 segurando ou não o salto (0,82× do impulso)
  - a Flor-Mordedora não emerge com Lume encostado na toca (shy_radius 40)
  - zona segura dos dois checkpoints sem toca de flor
- **Requisitos de motor:** nenhum (implementável com o motor atual)
- **Ajustes sobre a implementação inicial já existente:**
  - Plano sobre a implementação inicial já existente (5600 u, 8 inimigos, 3 relíquias).
  - Acrescentar 2º checkpoint em x4600: com um único checkpoint (x2700) sobram 2900 u sem salvamento.
  - Checkpoint x2700 → x2620 e primeira flor x2900 → x2960, para que a toca fique fora da zona segura [x−160, x+320].
  - Canal de 220 u com uma só pá: garantir pouso ≤ 125 u de cada margem durante ≥ 40% do ciclo ou acrescentar o apoio de pedra x4400 (y400).
  - Canal de 560 u: pás x2095/x2345 em fases opostas (π) para que sempre exista uma pá em posição de pouso.
  - Arte: moinhos com pás animadas alinhadas às plataformas circulares (x1450, x2220, x4365), trigo dourado, fardos de feno com textura de mola.

### 1-5 · Tocas do Prado (`meadow_burrows`)

*Ideia própria:* a sebe fecha a superfície e o túnel vira o único caminho.

- **Identificador:** `meadow_burrows`
- **Nome:** Tocas do Prado
- **Mundo:** Reino Verde (`green_kingdom`, bioma `grassland`), fase 5 de 6 — origem: nova
- **Objetivo:** Desafio avançado do Reino Verde: combinar molas, pedras frágeis, flores e o Ouriço-Espinho (topo espinhoso) num prado de dois andares — superfície e tocas — com saída vertical por raízes semissólidas.
- **Tema visual:** Prado de fim de tarde com tocas de coelho e toupeira, sebes de espinheiro (anunciando a fortaleza), raízes expostas, cogumelinhos e vagalumes nas tocas; túnel de terra listrada com quartzos.
- **Mecânica principal:** Dois andares: túnel subterrâneo obrigatório (sub-área burrows) com saída vertical por raízes semissólidas
- **Mecânicas secundárias:**
  - Ouriço-Espinho (não pisável: fogo, casco ou estrela)
  - tijolos no teto do túnel quebráveis por Lume grande
  - pedras frágeis alcançadas por mola
  - Flor-Mordedora no túnel
- **Dificuldade:** 3/10
- **Duração planejada:** 80–170 s (primeira travessia → exploração completa)
- **Tamanho do cenário:** 6000 × 1240 u
  - `main` [grassland] 0,0 6000×540: prado com a sebe que fecha a superfície (x2080)
  - `burrows` [underground] 1880,540 1860×540: tocas com chão em y1000/960/980 e saída por raízes x3330–3536
  - `pipe_room_area` [underground] 4769,700 960×540: câmara secreta
- **Caminho principal** (sequência de ensino):
  1. **Introdução** (0–640 u) — ? de fogo em x420 e dica: 'Espinhos dourados não podem ser pisados'.
  2. **Demonstração segura** (640–1100 u) — Ouriço-Espinho (estreia) em chão plano [640, 1090], 570 u após o spawn e com a chama já em mãos; saltar por cima também vale.
  3. **Primeiro desafio** (1100–1900 u) — Canal de 120 u; mola x1440 → pedras frágeis x1520/x1680 (relíquia frágil); flor x1620.
  4. **Escalada** (1880–2600 u) — A sebe (x2080) fecha a superfície: descer pela toca; flor (x2160), bolota e tijolos no teto (x2300) que Lume grande quebra (relíquia da toca).
  5. **Combinação** (2600–3300 u) — Checkpoint do túnel (proposto x2700, y920); caramujo e ouriço depois dele: chutar o casco contra o ouriço.
  6. **Reviravolta** (3300–3740 u) — Subida vertical por raízes semissólidas (y880 → y530): o túnel vira escada.
  7. **Teste final** (3540–5000 u) — Checkpoint de superfície (x3600); ouriço, flor e bolota em sequência; mola x4800 → galhos semissólidos (relíquia alta x5050, y200).
  8. **Recompensa** (5000–6000 u) — Besouro-Asa, ouriço e caramujo finais; cano da câmara (x5560) e bandeira em x5850.
- **Caminhos alternativos:**
  - Pedras frágeis pela mola x1440 (relíquia frágil).
  - Bolsão acima dos tijolos do teto do túnel x2300 (Lume grande; relíquia da toca).
  - Galhos semissólidos pela mola x4800 (relíquia alta).
  - Cano x5560 → câmara secreta (crescer, coração, moedas).
- **Inimigos permitidos:** `bolota` (Bolota), `caramujo` (Caramujo-de-Casca), `besouro_alado` (Besouro-Asa), `besouro` (Besouro), `flor_mordedora` (Flor-Mordedora), `ourico_espinho` (Ouriço-Espinho — estreia)
- **Quantidade planejada de inimigos:** 12–14 (chefes não contados)
- **Obstáculos:**
  - canal de 120 u (x1100)
  - sebe de espinheiro (parede x2080) que força o túnel
  - pedras frágeis
  - teto baixo do túnel
- **Itens disponíveis:**
  - fogo: ? x420
  - moeda: ? x5000
  - crescer: câmara x5228
- **Segredos:**
  - `crumble_route` (optional_challenge) — pista: Mola ao pé de tábuas rachadas com moedas em escada; recompensa: relíquia relic_crumble (x1716, y208)
  - `burrow_pocket` (breakable_path) — pista: Tijolos rachados no teto do túnel com terra escorrendo e brilho de quartzo acima; recompensa: relíquia relic_burrow (x2346, y816)
  - `high_route` (high_route) — pista: Galhos acima da mola x4800 com borboletas pousadas; recompensa: relíquia relic_high (x5050, y200)
  - `pipe_room` (warp_room) — pista: Cano com seta luminosa; recompensa: crescer, coração e 20 moedas
- **Colecionáveis:** ~60 moedas e 3 relíquias
- **Checkpoints:** 2
- **Eventos especiais:**
  - message (x3600): Vovó Candeia — “Por baixo da terra também há lampiões.”
  - message (x1960): dica da sebe (já existente como hint)
- **Elementos animados:**
  - coelhos entrando e saindo das tocas (decor)
  - raízes balançando quando atravessadas
  - vagalumes no túnel
  - terra caindo ao quebrar tijolos
- **Trilha sonora:** `green_kingdom_main` — superfície ensolarada; nas tocas a mesma melodia em marimba abafada e contrabaixo (sub-áreas: `green_kingdom_underground`)
- **Condição de conclusão:** Tocar a bandeira em x5850.
- **Critérios de teste:**
  - validate_level e validate_campaign sem erros (schema, espécies, bioma, ordem de introdução, warps com chão)
  - route_bot conclui a fase partindo do spawn e de cada um dos 2 checkpoint(s), com inimigos e perigos ativos
  - vãos obrigatórios ≤ 125 u na mesma altura e subidas obrigatórias ≤ 64 u, simulados nas duas alturas do jogador sem coyote nem buffer
  - as 3 relíquias e todas as moedas são alcançáveis (rota de teste dedicada por relíquia; nenhuma moeda leva a morte)
  - estreias (Ouriço-Espinho) em chão plano com ≥ 300 u de aproximação visível, recuo livre e nenhum vão letal a 200 u
  - teto sobre patrulha: nenhum sólido não semissólido com base entre y_chão−158 e y_chão−30 sobre a patrulha de inimigo terrestre a menos de 160 u de um vão obrigatório
  - zona segura de cada checkpoint: chão plano de x−96 a x+192 e nenhum inimigo comum alcança [x−160, x+320] em 3 s de simulação
  - o túnel é obrigatório: com a sebe x2080 não existe rota de superfície (o bot só conclui pelo túnel)
  - raízes semissólidas atravessáveis por baixo e sólidas por cima nas duas alturas do jogador
  - tijolos do teto só quebram com Lume grande e o bolsão não prende o jogador pequeno
  - zona segura dos 2 checkpoints livre de inimigos; nenhum perigo coberto por terreno
- **Requisitos de motor:** nenhum (implementável com o motor atual)
- **Ajustes sobre a implementação inicial já existente:**
  - Plano sobre a implementação inicial já existente (6000 u, 13 inimigos, 4 relíquias, 2 checkpoints).
  - Padronizar em 3 relíquias: frágil (visível), toca (segredo de tijolos) e alta (rota opcional); a câmara do cano passa a guardar crescer, coração e moedas.
  - Checkpoint do túnel x2640 → x2700 com bolota [2300, 2500], caramujo [3030, 3200] e ouriço [3060, 3290]: hoje três patrulhas cruzam a zona segura.
  - Ouriço de superfície [3800, 4140] → [3940, 4140] (zona do checkpoint x3600 = [3440, 3920]).
  - Canal x4400–4560: o terreno surface_after (x3540–6000) cobre o perigo hz_water02 — cortar o terreno (vão ≤ 125 u com a pedra frágil x4440 como atalho) ou remover o perigo.
  - Moedas: de 25 para ~60, com trilhas descendo pelas tocas e subindo pelas raízes.

### 1-6 · Fortaleza do Espinheiro (`bramble_fortress`)

*Ideia própria:* três ritmos ao mesmo tempo antes de um chefe que se vence pela parede.

- **Identificador:** `bramble_fortress`
- **Nome:** Fortaleza do Espinheiro
- **Mundo:** Reino Verde (`green_kingdom`, bioma `grassland`), fase 6 de 6 — origem: nova
- **Objetivo:** Fortaleza final do Reino Verde: atravessar a fortaleza de pedra tomada por espinheiros usando tudo do mundo (cascos contra ouriços, molas, pedras frágeis, flores) e derrotar o Javali Espinheiro.
- **Tema visual:** Fortaleza de pedra cinza tomada por espinheiro roxo-escuro, estandartes rasgados, tochas, pátio interno com muralhas de toras; entardecer alaranjado, sem clima.
- **Mecânica principal:** Espinheiros (thorns: ferem sem matar) e chamas oscilantes (perigo móvel) em corredores de fortaleza
- **Mecânicas secundárias:**
  - pedra frágil sobre fosso
  - casco contra ouriços
  - mola para o salão elevado (+148 u)
  - arena com portões (switch) fechados pelo evento boss_arena
- **Dificuldade:** 3/10
- **Duração planejada:** 110–220 s (primeira travessia → exploração completa)
- **Tamanho do cenário:** 4400 × 1240 u
  - `main` [grassland] 0,0 4400×540: fortaleza (variant fortress) com arena x3200–4040 entre pilares
  - `pipe_room_area` [underground] 2189,700 960×540: masmorra do cano
- **Caminho principal** (sequência de ensino):
  1. **Introdução** (0–600 u) — Portão da fortaleza; ? em x300; primeiro espinheiro (x520, 48 u) ao lado de moedas: tocar fere, não mata.
  2. **Demonstração segura** (600–900 u) — Chama oscilante (x760) sobre chão firme: ler o ciclo antes de passar.
  3. **Primeiro desafio** (900–1040 u) — Fosso de 140 u com pedra frágil no nível do chão: atravessar sem parar (proposta: fundo de espinheiro não letal em y540 com degraus de saída).
  4. **Escalada** (1040–1800 u) — Salão: caramujo + dois ouriços (chutar o casco, dica x1100); galeria alta (relíquia) pela mola x1760.
  5. **Combinação** (1760–2400 u) — Mola obrigatória para o salão elevado (x1800–2100, y300) e descida; Besouro-Asa proposto; checkpoint x2200; ? de fogo x2320; cano da masmorra x2400.
  6. **Reviravolta** (2400–3080 u) — Corredor de três ritmos: flores (propostas x2560 e x2720), bolota entre elas e chama oscilante sob o beiral x2840 (relíquia da chama).
  7. **Teste final** (3080–3200 u) — Antessala com 2º checkpoint proposto (x3080) e coração; Vovó Candeia acende o último lampião do mundo.
  8. **Recompensa** (3200–4400 u) — Arena (boss_arena x3290: portão esquerdo fecha, câmera trava): Javali Espinheiro (3 PV); a vitória abre o portão direito; bandeira em x4250.
- **Caminhos alternativos:**
  - Galeria alta (x1380–1640, y230) pela mola x1760 (relíquia da galeria).
  - Beiral sobre a chama (x2840, y300) — desafio opcional (relíquia da chama).
  - Cano x2400 → masmorra (relíquia, coração).
- **Inimigos permitidos:** `bolota` (Bolota), `caramujo` (Caramujo-de-Casca), `besouro_alado` (Besouro-Asa), `besouro` (Besouro), `flor_mordedora` (Flor-Mordedora), `ourico_espinho` (Ouriço-Espinho), `javali_espinheiro` (Javali Espinheiro — estreia)
- **Quantidade planejada de inimigos:** 9–11 (chefes não contados)
- **Obstáculos:**
  - espinheiros (thorns) no chão e no fosso
  - chamas oscilantes em x760 e x2880
  - fosso de 140 u com pedra frágil
  - salão elevado +148 u (mola)
  - arena fechada por portões
- **Itens disponíveis:**
  - crescer: ? x300
  - fogo: ? x2320 (o javali leva dano de fogo durante o aviso)
  - coração: masmorra x2648
  - coração: antessala (proposto x3120)
- **Segredos:**
  - `gallery` (high_route) — pista: Mola no fim do salão leva à galeria; estandarte dourado visível no alto; recompensa: relíquia relic_gallery (x1500, y186)
  - `flame_ledge` (optional_challenge) — pista: Plataforma acima da chama oscilante com moedas no ritmo do ciclo; recompensa: relíquia relic_flame (x2880, y250)
  - `pipe_room` (warp_room) — pista: Cano com seta luminosa entre as tochas; recompensa: relíquia relic_room (x2698, y850) e coração
- **Colecionáveis:** ~50 moedas e 3 relíquias
- **Checkpoints:** 2
- **Eventos especiais:**
  - boss_arena (x3290): lock [3140, 0, 960, 540], close gate_left, open gate_right, texto 'O Javali Espinheiro guarda a saída!' (já declarado)
  - message (x2200 e x3080): Vovó Candeia — “O javali só para quando bate na muralha. Espere o tranco.”
  - message (x3060): dica do javali (já existente como hint)
- **Elementos animados:**
  - javali raspando o chão antes da investida
  - portões de toras descendo e subindo
  - tochas e estandartes
  - espinheiro murchando e florescendo na vitória
  - bolotas-espinho caindo do teto na fase 2
- **Trilha sonora:** `green_kingdom_fortress` — tambores graves e cordas em ostinato; na arena entra o tema do chefe com metais (sub-áreas: `green_kingdom_underground`, `green_kingdom_boss`)
- **Condição de conclusão:** Derrotar o Javali Espinheiro (3 pisões na cabeça enquanto atordoado); o portão direito abre e a bandeira em x4250 conclui a fase.
- **Critérios de teste:**
  - validate_level e validate_campaign sem erros (schema, espécies, bioma, ordem de introdução, warps com chão)
  - route_bot conclui a fase partindo do spawn e de cada um dos 2 checkpoint(s), com inimigos e perigos ativos
  - vãos obrigatórios ≤ 125 u na mesma altura e subidas obrigatórias ≤ 64 u, simulados nas duas alturas do jogador sem coyote nem buffer
  - as 3 relíquias e todas as moedas são alcançáveis (rota de teste dedicada por relíquia; nenhuma moeda leva a morte)
  - teto sobre patrulha: nenhum sólido não semissólido com base entre y_chão−158 e y_chão−30 sobre a patrulha de inimigo terrestre a menos de 160 u de um vão obrigatório
  - zona segura de cada checkpoint: chão plano de x−96 a x+192 e nenhum inimigo comum alcança [x−160, x+320] em 3 s de simulação
  - arena: o portão esquerdo fecha ao entrar sem prender o jogador e o direito abre só com o chefe derrotado
  - o javali sempre bate numa muralha ao investir (chão contínuo x3240–4040)
  - bolotas-espinho da fase 2 caem dentro da arena e somem ao tocar o chão
  - o bot vence o chefe partindo do checkpoint da antessala
- **Requisitos de motor:** nenhum (implementável com o motor atual)
- **Ajustes sobre a implementação inicial já existente:**
  - Plano sobre a implementação inicial já existente (4400 u, arena com portões e evento boss_arena).
  - 2º checkpoint na antessala (x3080): perder para o javali repete só a arena.
  - Flores x2500/x2700 → x2560/x2720 (zona do checkpoint x2200 = [2040, 2520]) e bolota [2960, 3160] → [2590, 2700] (fora da zona da antessala [2920, 3400]).
  - Fosso x900–1040: hoje é letal (sem chão) e só tem espinheiro decorativo; o plano recomenda chão de espinheiro em y540 com degraus de saída — o mundo ensina que espinheiro fere sem matar.
  - Mais 2–3 inimigos (Besouro-Asa no salão elevado, ouriço no corredor) e moedas de 11 para ~50.
  - Arte: muralhas de toras nos pilares x3200/x4040 (o javali bate nelas), teto de galhos de onde caem as bolotas-espinho, espinheiro que murcha e floresce na vitória.

## Mundo 2 — Deserto Dourado (`golden_desert`)

Dunas, cânions, vento e templos. O vento vira regra — primeiro empurra a favor, depois sopra em rajadas e troca de lado — enquanto a areia esconde emboscadas que culminam no Escaravelho-Rei. Detalhes do mundo em [`MUNDO_02.md`](MUNDO_02.md).

### 2-1 · Dunas ao Vento (`windswept_dunes`)

*Ideia própria:* o vento aparece primeiro como aliado e um redemoinho leva a um segredo.

- **Identificador:** `windswept_dunes`
- **Nome:** Dunas ao Vento
- **Mundo:** Deserto Dourado (`golden_desert`, bioma `desert`), fase 1 de 6 — origem: legada 2-1
- **Objetivo:** Apresentar o deserto: correr entre dunas com vento a favor, conhecer os primeiros habitantes (bola que rola, escaravelho que se enterra, cacto que dispara) e os espinhos, e descobrir que o vento também levanta.
- **Tema visual:** Dunas douradas em camadas com cristas sopradas, colunas de canos de barro, escada de arenito, palmeiras-tamareiras, estátuas de camelo de pedra e o acampamento da Mestra Sálvia no checkpoint; meio da manhã com calor tremulando.
- **Mecânica principal:** Vento lateral constante a favor (zona wind sem período) e leitura de inimigos do deserto
- **Mecânicas secundárias:**
  - espinhos no chão (saltar com precisão)
  - projéteis retos do cacto sentinela
  - escaravelho que se enterra (intocável) em ritmo
  - redemoinho (wind force_y) que levanta até um segredo
- **Dificuldade:** 2/10
- **Duração planejada:** 55–120 s (primeira travessia → exploração completa)
- **Tamanho do cenário:** 3800 × 1240 u
  - `main` [desert] 0,0 3800×540: dunas com três vãos (120, 130 e 130 u)
  - `pipe_room_area` [underground] 2840,700 960×540: câmara secreta
- **Caminho principal** (sequência de ensino):
  1. **Introdução** (0–550 u) — Dunas planas; zona de vento a favor (force_x +50, contínua) de x100 a x900 com bandeirolas: o jogador sente o empurrão sem nada a perder; ? de crescer em x330.
  2. **Demonstração segura** (550–1000 u) — Colunas de canos (x550 h48, x690 h72) como degraus; tatu-bola (estreia) em chão plano [770, 880]: pisar e chutar a bola, que rola mais rápido que o casco e cai no vão.
  3. **Primeiro desafio** (1000–1770 u) — Vão de 120 u; escada de arenito (x1200 → x1330 → x1500) com ? de estrela; escaravelho-de-areia (estreia) em [1600, 1700]: esperar ele se enterrar e passar.
  4. **Escalada** (1770–2400 u) — Vão de 130 u; checkpoint x2040 com a Mestra Sálvia; ? de fogo x2200; espinhos x2280 (salto preciso em chão firme).
  5. **Combinação** (2400–2800 u) — Cacto Sentinela (estreia) em x2510 virado para Lume: incha e dispara a cada 2,2 s; tijolo x2620 como abrigo do espinho; vão de 130 u.
  6. **Reviravolta** (2930–3400 u) — Redemoinho de areia (wind force_y −1900, contínuo) visível em x3300: quem entra sobe até a duna alta da relíquia; quem ignora segue no chão.
  7. **Teste final** (3100–3500 u) — Cano da câmara secreta (x3130) e segundo escaravelho + cacto juntos: ritmo de enterrar + ritmo de disparo.
  8. **Recompensa** (3500–3800 u) — Bandeira em x3650 entre palmeiras.
- **Caminhos alternativos:**
  - Escada de arenito → tijolo03 (relíquia alta, agora em y220).
  - Redemoinho x3300 → duna alta (relíquia do redemoinho), desce de volta em x3420.
  - Cano x3130 → câmara secreta (relíquia, coração).
- **Inimigos permitidos:** `escaravelho_areia` (Escaravelho-de-Areia — estreia), `tatu_bola` (Tatu-Bola — estreia), `cacto_sentinela` (Cacto Sentinela — estreia)
- **Quantidade planejada de inimigos:** 5–6 (chefes não contados)
- **Obstáculos:**
  - 3 vãos (120/130/130 u) sobre areia do fundo do vale (queda letal)
  - espinhos x2280 (48 u)
  - espinhos do cacto (projétil reto)
- **Itens disponíveis:**
  - crescer: ? x330
  - estrela: ? x1460
  - fogo: ? x2200
  - coração: câmara x3418
- **Segredos:**
  - `high_route` (high_route) — pista: Trilha de moedas sobe pela escada de arenito; glifo de sol no tijolo do topo; recompensa: relíquia relic_high (x1530, y220 após o ajuste)
  - `dust_devil` (hidden_area) — pista: Coluna de areia rodopiando com moedas em coluna dentro dela; penas subindo; recompensa: relíquia relic_devil (x3330, y160) na duna alta
  - `pipe_room` (warp_room) — pista: Cano com seta luminosa e fitas de pano; recompensa: relíquia relic_room (x3468, y850) e coração
- **Colecionáveis:** ~48 moedas e 3 relíquias
- **Checkpoints:** 1
- **Eventos especiais:**
  - message (x2040): Mestra Sálvia — “Toda relíquia deixa uma marca. Procure o sol gravado na pedra.”
- **Elementos animados:**
  - bandeirolas e biruta indicando o vento a favor
  - redemoinho de areia girando (partículas subindo)
  - escaravelho mergulhando e emergindo com nuvem de areia
  - cacto inchando antes do disparo
  - calor tremulando no horizonte
- **Trilha sonora:** `golden_desert_main` — caravana ao vento: alaúde, palmas e flauta de cana em escala modal (sub-áreas: `golden_desert_underground`)
- **Condição de conclusão:** Tocar a bandeira em x3650.
- **Critérios de teste:**
  - validate_level e validate_campaign sem erros (schema, espécies, bioma, ordem de introdução, warps com chão)
  - route_bot conclui a fase partindo do spawn e de cada um dos 1 checkpoint(s), com inimigos e perigos ativos
  - vãos obrigatórios ≤ 150 u na mesma altura e subidas obrigatórias ≤ 64 u, simulados nas duas alturas do jogador sem coyote nem buffer
  - as 3 relíquias e todas as moedas são alcançáveis (rota de teste dedicada por relíquia; nenhuma moeda leva a morte)
  - estreias (Escaravelho-de-Areia, Tatu-Bola, Cacto Sentinela) em chão plano com ≥ 300 u de aproximação visível, recuo livre e nenhum vão letal a 200 u
  - teto sobre patrulha: nenhum sólido não semissólido com base entre y_chão−158 e y_chão−30 sobre a patrulha de inimigo terrestre a menos de 160 u de um vão obrigatório
  - zona segura de cada checkpoint: chão plano de x−96 a x+192 e nenhum inimigo comum alcança [x−160, x+320] em 3 s de simulação
  - a zona de vento inicial não cobre nenhum vão nem o spawn; com e sem vento o salto de 120 u é vencível
  - teto sobre patrulha: escaravelho sem sólido com base acima de y290 sobre [1600, 1700] após o ajuste
  - o redemoinho leva o jogador pequeno e grande da base até y≤200 em ≤ 2,5 s e solta sobre chão
  - os espinhos do cacto não alcançam a zona segura do checkpoint x2040
- **Requisitos de motor:** nenhum (implementável com o motor atual)
- **Plano de melhoria da fase legada:**
  - Mantidos: traçado de 4 dunas, vãos de 120/130/130 u, escada de arenito e câmara do cano.
  - Vento: zona contínua a favor x100–900 (apresentação) — sem vãos dentro dela.
  - Escaravelho: hoje [1450, 1670] sob ?02/tijolo03 (base y318) a 100 u do vão; subir ?02 e tijolo03 em 32 u (y258, base 286; degrau de 58 u a partir do tijolo02) e encurtar a patrulha para [1600, 1700]; relíquia alta vai para (1530, 220).
  - Tatu-bola: patrulha [805, 970] → [770, 880] (120 u livres antes da borda x1000).
  - Terceira relíquia no redemoinho (x3300 → duna alta x3260–3400, y200).
  - Arte: birutas, camelos de pedra, tenda da Mestra Sálvia, palmeiras e areia correndo na direção do vento.

### 2-2 · Pontes do Cânion (`canyon_bridges`)

*Ideia própria:* o cânion respira: uma térmica sobe do fundo e leva a um ninho.

- **Identificador:** `canyon_bridges`
- **Nome:** Pontes do Cânion
- **Mundo:** Deserto Dourado (`golden_desert`, bioma `desert`), fase 2 de 6 — origem: legada 2-2
- **Objetivo:** Explorar o cânion em terraços que sobem e descem, com pontes frágeis, a primeira chama oscilante e o voador do deserto; corrigir o salto sobre o tatu que batia a cabeça e somar uma rota térmica opcional.
- **Tema visual:** Cânion de paredes estratificadas (vermelho, ocre, creme), pontes de corda e tábuas, cactos em vasos de pedra, ninhos de abutre nas saliências; sol forte com sombras longas.
- **Mecânica principal:** Terraços em desnível (±32 u) ligados por pontes frágeis e plataformas móveis
- **Mecânicas secundárias:**
  - chama oscilante (perigo móvel) com ciclo legível
  - térmica do cânion (wind force_y) opcional
  - Abutrinho em voo ondulado
  - pedras frágeis afastadas da patrulha do tatu (correção do salto que batia a cabeça)
- **Dificuldade:** 3/10
- **Duração planejada:** 65–140 s (primeira travessia → exploração completa)
- **Tamanho do cenário:** 4100 × 1240 u
  - `main` [desert] 0,0 4100×540: cânion com 5 terraços (y448/416/384/416/448) e quatro vãos de 120–130 u
  - `pipe_room_area` [underground] 2929,700 960×540: câmara secreta
- **Caminho principal** (sequência de ensino):
  1. **Introdução** (0–740 u) — Terraço baixo; ? de crescer x430; dica 'O cânion tem terraços e atalhos acima'.
  2. **Demonstração segura** (740–1290 u) — Subida de 32 u; pedras frágeis x770 → x920 (já afastadas da patrulha) com a relíquia alta x954; tatu-bola em [1060, 1220] sem teto acima.
  3. **Primeiro desafio** (1290–1420 u) — Vão de 130 u subindo 32 u — corrigido: o salto sobre o tatu não bate mais a cabeça antes do vão.
  4. **Escalada** (1420–2100 u) — Checkpoint (proposto x1520); blocos ? x1590/x1670; Cacto Sentinela (proposto x1900, fora da linha do checkpoint); plataforma móvel x1960.
  5. **Combinação** (2100–2860 u) — Descida de 32 u; espinhos x2470; plataforma vertical x2550; vão de 120 u com a térmica opcional no fundo (x2740–2860).
  6. **Reviravolta** (2740–2900 u) — Térmica (wind force_y −1900) sobe do fundo do vão: quem salta nela é levado ao ninho do abutre (x2780, y180); quem não salta atravessa normalmente. 2º checkpoint proposto em x2950.
  7. **Teste final** (2860–3700 u) — Cano da câmara x3130; chama oscilante x3500 sobre chão firme — esperar o ciclo.
  8. **Recompensa** (3570–4100 u) — Abutrinho (estreia) planando em ondas largas sobre chão plano [3570, 3820]; bandeira em x3950.
- **Caminhos alternativos:**
  - Rota alta: pedra frágil x770 → pedra frágil x920 (relíquia alta x954, y250), desce antes do vão.
  - Térmica no vão x2740–2860 → ninho do abutre (relíquia do ninho), desce em ground05.
  - Cano x3130 → câmara (relíquia, estrela).
- **Inimigos permitidos:** `escaravelho_areia` (Escaravelho-de-Areia), `tatu_bola` (Tatu-Bola), `cacto_sentinela` (Cacto Sentinela), `abutre_filhote` (Abutrinho — estreia), `ourico_espinho` (Ouriço-Espinho)
- **Quantidade planejada de inimigos:** 6–8 (chefes não contados)
- **Obstáculos:**
  - 4 vãos (120–130 u) com desnível ±32 u
  - pedras frágeis x770 e x920 (rota alta)
  - espinhos x2470
  - chama oscilante x3500
  - espinhos do cacto
- **Itens disponíveis:**
  - crescer: ? x430
  - moeda: ? x1590
  - fogo: ? x1670
  - estrela: câmara x3388
- **Segredos:**
  - `high_route` (high_route) — pista: Trilha de moedas sobe pelas pedras frágeis; glifo de sol na parede; recompensa: relíquia relic_high (x954, y250)
  - `vulture_nest` (hidden_area) — pista: Penas e grãos de areia sobem em espiral no vão x2740–2860; moedas em coluna; recompensa: relíquia relic_nest (x2780, y180)
  - `pipe_room` (warp_room) — pista: Cano com seta luminosa; recompensa: relíquia relic_room (x3438, y850) e estrela
- **Colecionáveis:** ~50 moedas e 3 relíquias
- **Checkpoints:** 2
- **Eventos especiais:**
  - message (x1520): Mestra Sálvia — “O cânion respira: onde a areia sobe, o vento te leva.”
- **Elementos animados:**
  - pontes de corda balançando
  - térmica com penas e areia em espiral
  - chama oscilante com rastro
  - Abutrinho planando com sombra no chão
- **Trilha sonora:** `golden_desert_main` — eco do cânion: alaúde com reverberação longa e tambor de moldura (sub-áreas: `golden_desert_underground`)
- **Condição de conclusão:** Tocar a bandeira em x3950.
- **Critérios de teste:**
  - validate_level e validate_campaign sem erros (schema, espécies, bioma, ordem de introdução, warps com chão)
  - route_bot conclui a fase partindo do spawn e de cada um dos 2 checkpoint(s), com inimigos e perigos ativos
  - vãos obrigatórios ≤ 150 u na mesma altura e subidas obrigatórias ≤ 64 u, simulados nas duas alturas do jogador sem coyote nem buffer
  - as 3 relíquias e todas as moedas são alcançáveis (rota de teste dedicada por relíquia; nenhuma moeda leva a morte)
  - estreias (Abutrinho) em chão plano com ≥ 300 u de aproximação visível, recuo livre e nenhum vão letal a 200 u
  - teto sobre patrulha: nenhum sólido não semissólido com base entre y_chão−158 e y_chão−30 sobre a patrulha de inimigo terrestre a menos de 160 u de um vão obrigatório
  - zona segura de cada checkpoint: chão plano de x−96 a x+192 e nenhum inimigo comum alcança [x−160, x+320] em 3 s de simulação
  - regressão do problema conhecido: saltar sobre o tatu-bola em [1060, 1220] e cruzar o vão 1290→1420 nas duas alturas sem colisão de cabeça
  - teto sobre patrulha: nenhum sólido não semissólido com base entre y258 e y386 sobre [1040, 1240]
  - a térmica nunca é necessária: o bot conclui sem entrar nela; quem entra é solto sobre chão
  - a zona segura dos 2 checkpoints fica fora da mira do cacto
- **Requisitos de motor:** nenhum (implementável com o motor atual)
- **Plano de melhoria da fase legada:**
  - Problema conhecido (pedra frágil crumble02 em x1040, y288, sobre o tatu-bola logo antes do vão x1290→1420): a correção já foi aplicada no arquivo durante a redação — crumble01 em x770 e crumble02 em x920, fora da patrulha [1060, 1220], relíquia alta em (954, 250). O plano mantém a correção e acrescenta o teste de regressão; alternativa equivalente seria tornar a pedra semissólida.
  - Checkpoint x1480 → x1520 (chão plano x1424–1712) e cacto x1840 → x1900 com alcance de mira ≤ 360 u, para que a zona segura fique fora da linha de fogo.
  - 2º checkpoint em x2950: do primeiro checkpoint até a bandeira há 2470 u.
  - Terceira relíquia: térmica no vão x2740–2860 até o ninho (x2780, y180).
  - Arte: pontes de corda, estratos, ninhos e penas; a térmica com grãos e penas subindo em espiral.

### 2-3 · Templo das Areias (`sand_temple`)

*Ideia própria:* a força de Lume grande abre o teto de tijolos do templo.

- **Identificador:** `sand_temple`
- **Nome:** Templo das Areias
- **Mundo:** Deserto Dourado (`golden_desert`, bioma `desert`), fase 3 de 6 — origem: legada 2-3
- **Objetivo:** Desafio de movimento no templo: escadaria arqueológica, o primeiro inimigo blindado com ciclo (escorpião) e o Guardião do Templo (4 PV); a terceira relíquia exige quebrar tijolos rachados.
- **Tema visual:** Templo de arenito com colunas, glifos originais de sol e lua, tochas, areia escorrendo pelas frestas e estátuas de escaravelho; interior em penumbra quente.
- **Mecânica principal:** Inimigo blindado com janela periódica (cauda erguida 35% do ciclo de 3 s) e guardião do templo
- **Mecânicas secundárias:**
  - escadaria de tijolos
  - tijolos rachados quebráveis por Lume grande
  - espinhos e cacto sentinela
  - chefe intermediário guardiao_templo
- **Dificuldade:** 3/10
- **Duração planejada:** 70–150 s (primeira travessia → exploração completa)
- **Tamanho do cenário:** 4200 × 1240 u
  - `main` [desert] 0,0 4200×540: templo com três vãos (110, 110 e 120 u), câmara alta selada sobre x2440–2560 e arena x3440–3980
  - `pipe_room_area` [underground] 2179,700 960×540: câmara secreta
- **Caminho principal** (sequência de ensino):
  1. **Introdução** (0–470 u) — Pátio do templo; ? de crescer x420; dica 'As ruínas têm degraus para quem procura relíquias'.
  2. **Demonstração segura** (470–674 u) — Escorpião-Couraça (estreia) em chão plano [470, 600] entre o bloco ? e o cano x610: observar a cauda (erguida = não pisar), recuo livre até o spawn.
  3. **Primeiro desafio** (674–1550 u) — Vão de 110 u; escadaria de tijolos x1010 → x1130 → x1270 (relíquia alta) — agora sem inimigo embaixo.
  4. **Escalada** (1550–2380 u) — Vão de 110 u; espinhos x1810; ? de fogo x1980 (fogo vence o escorpião); checkpoint x2190; cano da câmara x2380.
  5. **Combinação** (2380–2800 u) — Teto de tijolos rachados em x2440–2560 (y300): Lume grande os quebra e sobe à câmara selada (relíquia do sol); Cacto Sentinela em x2650 abaixo.
  6. **Reviravolta** (2800–3020 u) — Vão de 120 u; 2º checkpoint proposto em x3020 com coração; segundo escorpião antes da arena (proposto [3120, 3300]).
  7. **Teste final** (3440–3980 u) — Arena: Guardião do Templo (4 PV) avança, salta e dispara; abre a guarda por 1,65 s a cada 4,8 s (1,1 s a cada 3,8 s na metade final).
  8. **Recompensa** (3980–4200 u) — Bandeira em x4050 liberada pela derrota do guardião.
- **Caminhos alternativos:**
  - Escadaria de tijolos → topo (relíquia alta x1332, y220).
  - Teto de tijolos rachados → câmara selada (relíquia do sol), só com Lume grande.
  - Cano x2380 → câmara (relíquia, coração).
- **Inimigos permitidos:** `escaravelho_areia` (Escaravelho-de-Areia), `tatu_bola` (Tatu-Bola), `cacto_sentinela` (Cacto Sentinela), `abutre_filhote` (Abutrinho), `escorpiao_couraca` (Escorpião-Couraça — estreia), `ourico_espinho` (Ouriço-Espinho), `guardiao_templo` (Guardião do Templo — estreia)
- **Quantidade planejada de inimigos:** 5–7 (chefes não contados)
- **Obstáculos:**
  - 3 vãos (110/110/120 u)
  - espinhos x1810
  - escorpião com cauda periódica
  - esferas do guardião
- **Itens disponíveis:**
  - crescer: ? x420
  - fogo: ? x1980
  - moeda: ? x2060
  - estrela: ? x3200
  - coração: câmara x2638
  - coração: chão x3340
- **Segredos:**
  - `high_route` (high_route) — pista: Trilha de moedas sobe pela escadaria; glifo de sol no último degrau; recompensa: relíquia relic_high (x1332, y220)
  - `sun_chamber` (breakable_path) — pista: Tijolos com rachaduras em forma de sol e areia escorrendo entre eles; Mestra Sálvia: 'tijolos rachados cedem a quem tem força'; recompensa: relíquia relic_sun (x2500, y160)
  - `pipe_room` (warp_room) — pista: Cano com seta luminosa; recompensa: relíquia relic_room (x2688, y850) e coração
- **Colecionáveis:** ~48 moedas e 3 relíquias
- **Checkpoints:** 2
- **Eventos especiais:**
  - message (x2190): Mestra Sálvia — “Tijolos rachados cedem a quem tem força.”
  - message (x3280): “A arena está adiante. Guarde sua luz.” (dica existente)
- **Elementos animados:**
  - tochas tremulando
  - areia escorrendo pelas frestas
  - cauda do escorpião subindo e descendo (ciclo de 3 s)
  - guardião de arenito abrindo a guarda
- **Trilha sonora:** `golden_desert_main` — interior do templo: drone grave, alaúde lento e sinos; percussão sobe na arena (sub-áreas: `golden_desert_underground`)
- **Condição de conclusão:** Derrotar o Guardião do Templo (4 PV) e tocar a bandeira em x4050.
- **Critérios de teste:**
  - validate_level e validate_campaign sem erros (schema, espécies, bioma, ordem de introdução, warps com chão)
  - route_bot conclui a fase partindo do spawn e de cada um dos 2 checkpoint(s), com inimigos e perigos ativos
  - vãos obrigatórios ≤ 150 u na mesma altura e subidas obrigatórias ≤ 64 u, simulados nas duas alturas do jogador sem coyote nem buffer
  - as 3 relíquias e todas as moedas são alcançáveis (rota de teste dedicada por relíquia; nenhuma moeda leva a morte)
  - estreias (Escorpião-Couraça) em chão plano com ≥ 300 u de aproximação visível, recuo livre e nenhum vão letal a 200 u
  - teto sobre patrulha: nenhum sólido não semissólido com base entre y_chão−158 e y_chão−30 sobre a patrulha de inimigo terrestre a menos de 160 u de um vão obrigatório
  - zona segura de cada checkpoint: chão plano de x−96 a x+192 e nenhum inimigo comum alcança [x−160, x+320] em 3 s de simulação
  - o escorpião só pode ser pisado com a cauda baixa e leva 2 golpes; o fogo o derrota
  - a câmara selada só é acessível quebrando os tijolos com Lume grande; Lume pequeno não fica preso
  - estreia do escorpião em chão plano com ≥ 300 u de aproximação visível e recuo livre
  - a bandeira só conclui depois da derrota do guardião
- **Requisitos de motor:** nenhum (implementável com o motor atual)
- **Plano de melhoria da fase legada:**
  - Escorpião: patrulha [1340, 1500] → [470, 600]; hoje ele estreia sob o tijolo03 (base y292) a 50 u do vão — a estreia deve ser em chão plano com recuo.
  - 2º checkpoint em x3020 (chão plano x2924–3212) para repetir só a arena.
  - Terceira relíquia: câmara selada sobre o teto de tijolos rachados x2440–2560 (breakable_path com tijolos já suportados pelo motor).
  - Segundo escorpião em [3120, 3300] para revisar o ciclo antes do chefe.
  - Arte: tochas, glifos, areia escorrendo das frestas, estátuas de escaravelho anunciando a pirâmide.

### 2-4 · Passagem da Tempestade (`sandstorm_pass`)

*Ideia própria:* no olho da tempestade o vento troca de lado a cada 2 s.

- **Identificador:** `sandstorm_pass`
- **Nome:** Passagem da Tempestade
- **Mundo:** Deserto Dourado (`golden_desert`, bioma `desert`), fase 4 de 6 — origem: nova
- **Objetivo:** Mecânica especial do Deserto Dourado: atravessar a passagem durante a tempestade lendo o vento — trechos de vento constante a favor e rajadas contrárias com período — e conhecer a Serpente-de-Duna, que viaja sob a areia.
- **Tema visual:** Desfiladeiro de dunas sob tempestade alaranjada: faixas de areia correndo na direção do vento, birutas em postes, rochas-abrigo com sombra azulada, colunas caídas de uma ruína, céu escurecendo e clareando no fim (pôr do sol).
- **Mecânica principal:** Vento lateral por zonas wind: constante a favor (+80/+140 u/s) e rajadas contrárias com período (−120/−130 u/s; 3,6 s/0,45 e 3,2 s/0,5)
- **Mecânicas secundárias:**
  - Serpente-de-Duna (rastro de areia, tremor de aviso, emboscada)
  - rochas-abrigo e calmarias para esperar
  - rota das colunas caídas contra o vento
  - olho da tempestade: zonas sobrepostas em fases opostas (proposta)
- **Dificuldade:** 3/10
- **Duração planejada:** 85–170 s (primeira travessia → exploração completa)
- **Tamanho do cenário:** 5600 × 1240 u
  - `main` [desert] 0,0 5600×540: passagem com seis trechos de duna e vãos de 90–200 u
  - `pipe_room_area` [underground] 3449,700 960×540: caravana soterrada (sala secreta)
- **Caminho principal** (sequência de ensino):
  1. **Introdução** (0–1100 u) — Dunas com vento constante a favor (+80, x300–900) sobre chão sem vãos: sentir o empurrão; ? de crescer x480; escaravelho em [640, 1090].
  2. **Demonstração segura** (1100–1630 u) — Primeira rajada contrária (−120, período 3,6 s, duty 0,45) sobre os vãos de 120 e 110 u: saltar nas calmarias (dica 'Rajadas vêm e vão').
  3. **Primeiro desafio** (1630–3000 u) — Cacto sentinela em x1820 dentro da rajada; checkpoint x2150; Serpente-de-Duna (estreia, patrulha proposta [2500, 2990]) em chão largo: rastro, tremor e irrupção.
  4. **Escalada** (3000–3220 u) — Vão do vento a favor: rajada constante +140 leva Lume por cima do vão; moedas soltas no ar marcam o arco (relíquia da rajada).
  5. **Combinação** (3220–3900 u) — 2º checkpoint proposto x3300; cano da caravana soterrada x3740; escorpião-couraça (proposto [4000, 4200], já sob a rajada).
  6. **Reviravolta** (3900–4500 u) — Olho da tempestade (proposta): zona contrária −130 (3,2 s/0,5) somada a uma zona +130 em fase oposta — o vento troca de lado a cada 1,6 s; colunas caídas (beirais x4080/x4240) contra o vento levam à relíquia das ruínas.
  7. **Teste final** (4500–5200 u) — Abutrinho planando na rajada e segunda serpente (proposta [4660, 4920]); vão de 110 u.
  8. **Recompensa** (5200–5600 u) — A tempestade cessa no fim das zonas, pôr do sol e bandeira em x5450.
- **Caminhos alternativos:**
  - Rota das colunas caídas (beirais x4080 → x4240) contra o vento até a relíquia das ruínas.
  - Cano x3740 → caravana soterrada (relíquia e coração) → retorno em x4006.
  - Arco alto do vão do vento a favor, pelas moedas soltas (relíquia da rajada).
- **Inimigos permitidos:** `escaravelho_areia` (Escaravelho-de-Areia), `tatu_bola` (Tatu-Bola), `cacto_sentinela` (Cacto Sentinela), `abutre_filhote` (Abutrinho), `escorpiao_couraca` (Escorpião-Couraça), `ourico_espinho` (Ouriço-Espinho), `serpente_duna` (Serpente-de-Duna — estreia)
- **Quantidade planejada de inimigos:** 10–14 (chefes não contados)
- **Obstáculos:**
  - rajadas contrárias com período e vento constante a favor
  - vãos de 90–200 u (o de 200 u só com vento a favor)
  - espinhos do cacto dentro da rajada
  - irrupções da serpente
- **Itens disponíveis:**
  - crescer: ? x480
  - moeda: ? x4720
  - coração: caravana soterrada x3908
  - estrela: ? proposto no olho da tempestade
- **Segredos:**
  - `gust_relic` (optional_challenge) — pista: Moedas soltas no ar sobre o vão do vento a favor; recompensa: relíquia relic_gust (x3140, y312)
  - `ruins_route` (high_route) — pista: Colunas caídas formam degraus contra o vento; recompensa: relíquia relic_ruins (x4282, y216)
  - `pipe_room` (warp_room) — pista: Manilha com seta luminosa e fitas de tecido tremulando; recompensa: relíquia relic_room (x3958, y850) e coração
- **Colecionáveis:** ~70 moedas e 3 relíquias
- **Checkpoints:** 2
- **Eventos especiais:**
  - message (x2150): Mestra Sálvia — “Leia a biruta: cheia é rajada, murcha é calmaria.”
  - message (x5200): “A tempestade passou.”
- **Elementos animados:**
  - birutas sincronizadas com cada zona (Game.zone_active)
  - areia em faixas na direção do vento
  - rastros e tremores da Serpente-de-Duna
  - céu escurecendo no olho e clareando no pôr do sol
- **Trilha sonora:** `golden_desert_main` — tempestade: ostinato de cordas graves que cresce a cada rajada; no fim, melodia limpa ao pôr do sol (sub-áreas: `golden_desert_underground`)
- **Condição de conclusão:** Tocar a bandeira em x5450.
- **Critérios de teste:**
  - validate_level e validate_campaign sem erros (schema, espécies, bioma, ordem de introdução, warps com chão)
  - route_bot conclui a fase partindo do spawn e de cada um dos 2 checkpoint(s), com inimigos e perigos ativos
  - vãos obrigatórios ≤ 150 u na mesma altura e subidas obrigatórias ≤ 64 u, simulados nas duas alturas do jogador sem coyote nem buffer
  - as 3 relíquias e todas as moedas são alcançáveis (rota de teste dedicada por relíquia; nenhuma moeda leva a morte)
  - estreias (Serpente-de-Duna) em chão plano com ≥ 300 u de aproximação visível, recuo livre e nenhum vão letal a 200 u
  - teto sobre patrulha: nenhum sólido não semissólido com base entre y_chão−158 e y_chão−30 sobre a patrulha de inimigo terrestre a menos de 160 u de um vão obrigatório
  - zona segura de cada checkpoint: chão plano de x−96 a x+192 e nenhum inimigo comum alcança [x−160, x+320] em 3 s de simulação
  - todo vão obrigatório de até 150 u é vencível com a rajada contrária ativa decolando na borda
  - o vão de 200 u só existe sob zona contínua a favor (sem período) que cobre todo o arco do salto
  - nenhuma zona de vento cobre os checkpoints
  - a Serpente-de-Duna emite tremor antes de surgir e nunca surge na zona segura do checkpoint
- **Requisitos de motor:** nenhum (implementável com o motor atual)
- **Ajustes sobre a implementação inicial já existente:**
  - Plano sobre a implementação inicial já existente (5600 u, 4 zonas de vento, 6 inimigos, 3 relíquias, 1 checkpoint).
  - Vão x3000→3200 (200 u) só é vencível com o vento constante +140: hoje funciona porque a zona não tem período, mas excede a regra de 150 u do Mundo 2 — reduzir para 150 u ou manter como exceção documentada com teste dedicado (zona sem período cobrindo todo o arco).
  - 2º checkpoint em x3300 (fora do vento): encurtar a zona a favor de x3000–3600 para x3000–3220 e mover o escorpião para [4000, 4200]; com um único checkpoint (x2150) sobram 3300 u.
  - Serpente de estreia [2200, 2990] → [2500, 2990]: hoje cruza a zona segura do checkpoint x2150 ([1990, 2470]).
  - Olho da tempestade: acrescentar uma zona +130 em fase oposta sobre x4100–4500 (reviravolta da fase, implementável só com dados).
  - Densidade de 6 para 10–14 inimigos (tatu rolando a favor do vento, segundo cacto num abrigo, ouriço); moedas de 33 para ~70.
  - Arte: birutas e partículas de areia sincronizadas com Game.zone_active (sem isso as rajadas ficam ilegíveis).

### 2-5 · Oásis Soterrado (`sunken_oasis`)

*Ideia própria:* a lagoa do oásis é a primeira água em que se nada — e guarda uma relíquia no fundo.

- **Identificador:** `sunken_oasis`
- **Nome:** Oásis Soterrado
- **Mundo:** Deserto Dourado (`golden_desert`, bioma `desert`), fase 5 de 6 — origem: nova
- **Objetivo:** Desafio avançado do deserto: atravessar o oásis soterrado combinando poças de areia movediça, palmeiras como plataformas de mão única, uma lagoa onde se nada e o Escaravelho Lançador, que arremessa bolas de areia em arco.
- **Tema visual:** Oásis engolido pela areia: palmeiras (copas semissólidas), poças de areia movediça entre lajes de arenito, lagoa turquesa cercada de juncos, ruínas de muros e um terraço elevado; luz quente de fim de tarde.
- **Mecânica principal:** Poças de areia movediça (zonas quicksand de 80 u sobre leito a −72 u) que exigem sair saltando
- **Mecânicas secundárias:**
  - Escaravelho Lançador (ergue a bola antes de arremessar em arco)
  - lagoa com nado (zona swim) e saída por salto — prévia do Mundo 3
  - copas de palmeira semissólidas
  - terraço elevado com lançador
- **Dificuldade:** 3/10
- **Duração planejada:** 95–190 s (primeira travessia → exploração completa)
- **Tamanho do cenário:** 6000 × 1240 u
  - `main` [desert] 0,0 6000×540: oásis com poças de areia movediça (x900, x2800, x3000, x3200), lagoa x1500–1900 e terraço x4200–4600
  - `pipe_room_area` [underground] 4709,700 960×540: câmara secreta
- **Caminho principal** (sequência de ensino):
  1. **Introdução** (0–900 u) — Dunas; ? de crescer x380; escaravelho em [520, 890]; dica 'Areia movediça: não pare — pule várias vezes para sair'.
  2. **Demonstração segura** (870–1500 u) — Primeira poça de areia movediça (80 u) com a copa de palmeira semissólida x870 por cima: atravessar pelo alto ou afundar e sair saltando.
  3. **Primeiro desafio** (1500–1900 u) — Lagoa do oásis (swim): nadar e saltar para sair do outro lado; brilho no fundo marca a relíquia da lagoa.
  4. **Escalada** (1900–2800 u) — Checkpoint x2000; ? de fogo x2260; Escaravelho Lançador (estreia, patrulha proposta [2560, 2780], fora do alcance de 520 u do checkpoint) em chão plano com colunas-abrigo.
  5. **Combinação** (2800–3280 u) — Três poças de areia movediça seguidas, cada uma com uma copa de palmeira acima (x2820, x3020, x3220): ritmo de pulos curtos.
  6. **Reviravolta** (3280–4200 u) — 2º checkpoint proposto x3380; serpente (proposta [3720, 4190]) e escaravelho sob a areia no mesmo trecho — dois ritmos de emboscada.
  7. **Teste final** (4200–5300 u) — Terraço elevado (+48 u) com lançador arremessando para baixo; copas de palmeira em escada (relíquia das palmeiras); tatu-bola e Abutrinho.
  8. **Recompensa** (5300–6000 u) — O oásis vivo: palmeiras verdes, cano da câmara x5420 e bandeira em x5850.
- **Caminhos alternativos:**
  - Copas de palmeira por cima das poças (sem tocar a areia).
  - Copas de palmeira em escada x4650 → x4800 → x4950 (relíquia das palmeiras).
  - Fundo da lagoa (relíquia da lagoa) e cano x5420 → câmara (relíquia, estrela).
- **Inimigos permitidos:** `escaravelho_areia` (Escaravelho-de-Areia), `tatu_bola` (Tatu-Bola), `cacto_sentinela` (Cacto Sentinela), `abutre_filhote` (Abutrinho), `escorpiao_couraca` (Escorpião-Couraça), `ourico_espinho` (Ouriço-Espinho), `serpente_duna` (Serpente-de-Duna), `escaravelho_lancador` (Escaravelho Lançador — estreia)
- **Quantidade planejada de inimigos:** 12–16 (chefes não contados)
- **Obstáculos:**
  - poças de areia movediça (afundar por completo mata)
  - lagoa (não letal) com saída por salto
  - bolas de areia em arco
  - emboscadas sob a areia
- **Itens disponíveis:**
  - crescer: ? x380
  - fogo: ? x2260
  - estrela: câmara x5168
- **Segredos:**
  - `pond_relic` (hidden_area) — pista: Brilho no fundo da lagoa entre juncos; recompensa: relíquia relic_pond (x1690, y586)
  - `palm_route` (high_route) — pista: Copas de palmeiras em escada com moedas; recompensa: relíquia relic_palms (x4990, y172)
  - `pipe_room` (warp_room) — pista: Cano com seta luminosa junto às palmeiras verdes; recompensa: relíquia relic_room (x5218, y850) e estrela
- **Colecionáveis:** ~80 moedas e 3 relíquias
- **Checkpoints:** 2
- **Eventos especiais:**
  - message (x2000): Mestra Sálvia — “Na areia funda, não pare: salte de novo antes de afundar.”
- **Elementos animados:**
  - areia movediça borbulhando e engolindo grãos
  - superfície da lagoa com reflexos
  - Escaravelho Lançador erguendo a bola antes do arremesso
  - palmeiras balançando
- **Trilha sonora:** `golden_desert_main` — oásis: alaúde e percussão de barro; na lagoa, filtro abafado e harpa (sub-áreas: `golden_desert_underground`)
- **Condição de conclusão:** Tocar a bandeira em x5850.
- **Critérios de teste:**
  - validate_level e validate_campaign sem erros (schema, espécies, bioma, ordem de introdução, warps com chão)
  - route_bot conclui a fase partindo do spawn e de cada um dos 2 checkpoint(s), com inimigos e perigos ativos
  - vãos obrigatórios ≤ 150 u na mesma altura e subidas obrigatórias ≤ 64 u, simulados nas duas alturas do jogador sem coyote nem buffer
  - as 3 relíquias e todas as moedas são alcançáveis (rota de teste dedicada por relíquia; nenhuma moeda leva a morte)
  - estreias (Escaravelho Lançador) em chão plano com ≥ 300 u de aproximação visível, recuo livre e nenhum vão letal a 200 u
  - teto sobre patrulha: nenhum sólido não semissólido com base entre y_chão−158 e y_chão−30 sobre a patrulha de inimigo terrestre a menos de 160 u de um vão obrigatório
  - zona segura de cada checkpoint: chão plano de x−96 a x+192 e nenhum inimigo comum alcança [x−160, x+320] em 3 s de simulação
  - de cada poça de areia movediça sai-se em ≤ 2 pulos reduzidos (0,62×) a partir de qualquer ponto antes de afundar por completo (≈ 1 s parado)
  - a lagoa tem saída por salto nas duas bordas e nenhum inimigo dentro
  - o lançador só arremessa com Lume a ≤ 520 u e as colunas-abrigo bloqueiam o arco
  - o bot conclui partindo dos 2 checkpoints
- **Requisitos de motor:** nenhum (implementável com o motor atual)
- **Ajustes sobre a implementação inicial já existente:**
  - Plano sobre a implementação inicial já existente (6000 u, 5 zonas de areia/lagoa, 7 inimigos, 3 relíquias, 1 checkpoint).
  - Dificuldade declarada 4 no arquivo; a faixa do Mundo 2 é 1–3 — o plano fixa 3 (ajustar o campo ou suavizar a densidade do terraço final).
  - A física de areia movediça foi implementada durante a redação (afunda ~36 u/s e mata ao cobrir Lume): conferir que cada poça de 80 u sobre leito a −72 u permite sair com o pulo reduzido e acrescentar uma poça longa (160–240 u) com apoios como teste final.
  - 2º checkpoint em x3380 (chão plano x3284–3572) com a serpente recuada para [3720, 4190]; lançador de estreia para [2560, 2780] (o arco de 520 u não alcança o checkpoint x2000).
  - Densidade de 7 para 12–16 inimigos e moedas de 24 para ~80 (trilhas sobre as copas e na lagoa).
  - A lagoa (swim) antecipa o nado do Mundo 3: manter rasa, sem inimigos e com saída a ≤ 70 u acima da superfície.

### 2-6 · Pirâmide do Escaravelho (`scarab_pyramid`)

*Ideia própria:* a laje sobre a armadilha de areia antecipa o chão que o chefe vai fazer tremer.

- **Identificador:** `scarab_pyramid`
- **Nome:** Pirâmide do Escaravelho
- **Mundo:** Deserto Dourado (`golden_desert`, bioma `desert`), fase 6 de 6 — origem: nova
- **Objetivo:** Fortaleza do Deserto Dourado: atravessar o interior da pirâmide com armadilhas de areia, chamas oscilantes e uma galeria de tijolos, e derrotar o Escaravelho-Rei, que nada sob a areia e só pode ser pisado quando cai de costas.
- **Tema visual:** Interior de pirâmide em arenito dourado: corredores com glifos de sol, armadilha de espinhos sob uma ponte frágil, poço de areia, galeria de tijolos em escada, tochas; a arena entre dois pilares com portões de pedra.
- **Mecânica principal:** Armadilhas de pirâmide (fosso de espinhos sob ponte frágil, poça de areia, chamas oscilantes) antes de um chefe de emboscada subterrânea
- **Mecânicas secundárias:**
  - escada de tijolos até a galeria
  - laje sobre a armadilha de areia (desafio opcional)
  - inimigos de todo o mundo em sequência
  - arena com portões (boss_arena já declarado)
- **Dificuldade:** 3/10
- **Duração planejada:** 120–240 s (primeira travessia → exploração completa)
- **Tamanho do cenário:** 4600 × 1240 u
  - `main` [desert] 0,0 4600×540: interior da pirâmide (variant fortress) com arena x3000–3880 entre pilares
  - `pipe_room_area` [underground] 2139,700 960×540: câmara secreta
- **Caminho principal** (sequência de ensino):
  1. **Introdução** (0–700 u) — Entrada; ? de crescer x260; espinhos x420 e chama oscilante x600 sobre chão firme.
  2. **Demonstração segura** (700–1080 u) — Ponte frágil x712 sobre o fosso de espinhos (x700–820); poça de areia x1000 com a laje x990 por cima (relíquia da armadilha).
  3. **Primeiro desafio** (1080–1600 u) — Escorpião-couraça e Escaravelho Lançador juntos: cauda periódica + arco.
  4. **Escalada** (1600–2400 u) — Checkpoint x1650; ? de fogo x1760; tatu-bola rolando no corredor; chama oscilante x2260.
  5. **Combinação** (2400–2720 u) — Escada de tijolos x2400 → x2520 → x2640 até a galeria (relíquia da galeria); cano da câmara x2860.
  6. **Reviravolta** (2520–2960 u) — Antessala: 2º checkpoint proposto x2620 (escaravelho-de-areia recuado para [2160, 2380]) e coração proposto.
  7. **Teste final** (3000–3880 u) — Arena (boss_arena x3090: portão esquerdo fecha, câmera trava): Escaravelho-Rei (3 PV) segue Lume sob a areia, irrompe após o jato de areia e cai de costas.
  8. **Recompensa** (3880–4600 u) — Portão direito abre com a vitória; bandeira em x4400.
- **Caminhos alternativos:**
  - Laje x990 sobre a poça de areia (relíquia da armadilha).
  - Escada de tijolos até a galeria (relíquia da galeria x2672, y190).
  - Cano x2860 → câmara (relíquia, coração).
- **Inimigos permitidos:** `escaravelho_areia` (Escaravelho-de-Areia), `tatu_bola` (Tatu-Bola), `cacto_sentinela` (Cacto Sentinela), `abutre_filhote` (Abutrinho), `escorpiao_couraca` (Escorpião-Couraça), `ourico_espinho` (Ouriço-Espinho), `serpente_duna` (Serpente-de-Duna), `escaravelho_lancador` (Escaravelho Lançador), `escaravelho_rei` (Escaravelho-Rei — estreia)
- **Quantidade planejada de inimigos:** 7–10 (chefes não contados)
- **Obstáculos:**
  - fosso de espinhos sob ponte frágil
  - poça de areia
  - chamas oscilantes x600 e x2260
  - espinhos x420
  - irrupções e rolamento do chefe
- **Itens disponíveis:**
  - crescer: ? x260
  - fogo: ? x1760 (o chefe só leva dano de pisão)
  - coração: câmara x2598
  - coração: antessala (proposto)
- **Segredos:**
  - `trap_relic` (optional_challenge) — pista: Laje sobre a armadilha de areia com moedas; recompensa: relíquia relic_trap (x1030, y330)
  - `gallery` (high_route) — pista: Escada de tijolos sobe até a galeria; glifo de sol no último degrau; recompensa: relíquia relic_gallery (x2672, y190)
  - `pipe_room` (warp_room) — pista: Cano com seta luminosa entre tochas; recompensa: relíquia relic_room (x2648, y850) e coração
- **Colecionáveis:** ~60 moedas e 3 relíquias
- **Checkpoints:** 2
- **Eventos especiais:**
  - boss_arena (x3090): lock [2960, 0, 960, 540], close gate_left, open gate_right, texto 'O Escaravelho-Rei emerge da areia!' (já declarado)
  - message (x2950): “Quando ele cair de costas, é a hora de pisar.” (dica existente)
  - message (x2620): Mestra Sálvia — “Ele nada na areia como os escaravelhos pequenos: siga o jato de areia.”
- **Elementos animados:**
  - jato de areia sob Lume antes da irrupção
  - Escaravelho-Rei de costas agitando as patas
  - rolamento com poeira e batida na parede
  - portões de pedra descendo e subindo
- **Trilha sonora:** `golden_desert_fortress` — pirâmide: tambores rituais, coro grave e alaúde; na arena, tema do chefe com metais e palmas (sub-áreas: `golden_desert_underground`, `golden_desert_boss`)
- **Condição de conclusão:** Derrotar o Escaravelho-Rei (3 pisões enquanto está de costas); o portão direito abre e a bandeira em x4400 conclui a fase.
- **Critérios de teste:**
  - validate_level e validate_campaign sem erros (schema, espécies, bioma, ordem de introdução, warps com chão)
  - route_bot conclui a fase partindo do spawn e de cada um dos 2 checkpoint(s), com inimigos e perigos ativos
  - vãos obrigatórios ≤ 150 u na mesma altura e subidas obrigatórias ≤ 64 u, simulados nas duas alturas do jogador sem coyote nem buffer
  - as 3 relíquias e todas as moedas são alcançáveis (rota de teste dedicada por relíquia; nenhuma moeda leva a morte)
  - teto sobre patrulha: nenhum sólido não semissólido com base entre y_chão−158 e y_chão−30 sobre a patrulha de inimigo terrestre a menos de 160 u de um vão obrigatório
  - zona segura de cada checkpoint: chão plano de x−96 a x+192 e nenhum inimigo comum alcança [x−160, x+320] em 3 s de simulação
  - o chefe só é tangível fora dos estados burrow/telegraph/hurt e só leva dano quando dazed
  - o jato de areia aparece ≥ 0,45 s antes de cada irrupção, também na fase 2
  - arena: portão esquerdo fecha sem prender o jogador e o direito abre só com a vitória
  - o bot vence o chefe partindo do checkpoint da antessala
- **Requisitos de motor:** nenhum (implementável com o motor atual)
- **Ajustes sobre a implementação inicial já existente:**
  - Plano sobre a implementação inicial já existente (4600 u, arena com portões, chefe Escaravelho-Rei implementado, 3 relíquias, 1 checkpoint).
  - Dificuldade declarada 4 no arquivo; o plano fixa 3 (faixa do Mundo 2).
  - 2º checkpoint na antessala (x2620, chão plano x2524–2812) com o escaravelho-de-areia de [2700, 2950] recuado para [2160, 2380]: perder para o chefe repete só a arena.
  - Moedas de 14 para ~60 (trilha da escada de tijolos, arco sobre a ponte frágil) e 2–3 inimigos a mais (cacto, serpente na poça).
  - Melhoria de arena só com dados: duas pequenas plataformas semissólidas a 96 u do chão para escapar do rolamento.

## Mundo 3 — Costa dos Corais (`coral_coast`)

Praias, marés e recifes submersos. A água deixa de matar: nadar vira o movimento principal, primeiro raso, depois em correntes, num labirinto e num naufrágio que alaga. Detalhes do mundo em [`MUNDO_03.md`](MUNDO_03.md).

### 3-1 · Praia das Conchas (`shell_beach`)

*Ideia própria:* a gruta das conchas obriga o primeiro mergulho completo.

- **Identificador:** `shell_beach`
- **Nome:** Praia das Conchas
- **Mundo:** Costa dos Corais (`coral_coast`, bioma `coast`), fase 1 de 6 — origem: nova
- **Objetivo:** Apresentar o nado com segurança (piscina rasa → lagoa funda → gruta curta), os píeres semissólidos e os dois primeiros habitantes da costa: o caranguejo de pinças periódicas e o peixe que salta da água.
- **Tema visual:** Praia de areia clara com conchas gigantes, guarda-sóis de folha de palmeira, barracas de pescador, píer de madeira sobre a lagoa turquesa, rochas com cracas; manhã de sol e espuma.
- **Mecânica principal:** Nado (zonas swim) introduzido sem risco: toque no salto para impulsionar, saída da água com 0,85 do salto
- **Mecânicas secundárias:**
  - píeres semissólidos sobre a água
  - Caranguejo-Pinça (pinças erguidas = perigo por cima)
  - Peixe-Saltador (arco periódico para fora d'água)
  - gruta submersa curta
- **Dificuldade:** 3/10
- **Duração planejada:** 80–160 s (primeira travessia → exploração completa)
- **Tamanho do cenário:** 4600 × 1240 u
  - `main` [coast] 0,0 4600×540: praia, lagoa (swim y≥360) e rochedo final
  - `grotto` [underwater] 3300,540 1000×700: gruta das conchas e manilha secreta
- **Caminho principal** (sequência de ensino):
  1. **Introdução** (0–600 u) — Areia e conchas; piscina rasa de 60 u de profundidade e 300 u de largura com moedas no fundo; dica 'Na água, toque o salto para nadar'; sem inimigos.
  2. **Demonstração segura** (600–1200 u) — Lagoa funda (200 u) com fundo de areia e coluna de moedas; sair nadando para cima e saltando para a margem.
  3. **Primeiro desafio** (1200–1900 u) — Caranguejo-Pinça (estreia) em areia plana larga: pinças erguidas (45% do ciclo de 2,6 s) ferem por cima; pisar com pinças baixas.
  4. **Escalada** (1900–2600 u) — Píer semissólido (tábuas) sobre a lagoa; Peixe-Saltador (estreia) salta a cada 3,2 s em arco sobre o píer; checkpoint x2200 na cabana do Mestre Búzio.
  5. **Combinação** (2600–3300 u) — Escolha: correr no píer com caranguejos ou nadar entre as estacas por baixo (peixes); ambas se reencontram em x3300.
  6. **Reviravolta** (3300–3900 u) — Gruta das conchas: o único caminho é um mergulho de 240 u sob um arco de rocha, com moedas guiando e saída para um bolsão de ar.
  7. **Teste final** (3900–4300 u) — Rochedo final: pedras em vãos de 110 u sobre água rasa (cair = nadar de volta), caranguejos nas pedras e peixes saltando entre elas; 2º checkpoint em x3950.
  8. **Recompensa** (4300–4600 u) — Bandeira-concha gigante em x4450 com arco de moedas.
- **Caminhos alternativos:**
  - Rota por baixo do píer entre as estacas (moedas, peixes) — reencontra a areia em x3300.
  - Torre do salva-vidas por caixotes (tijolos) até a relíquia do mirante.
  - Manilha na areia x3500 → gruta submersa secreta (relíquia).
- **Inimigos permitidos:** `caramujo` (Caramujo-de-Casca), `caranguejo_pinca` (Caranguejo-Pinça — estreia), `peixe_saltador` (Peixe-Saltador — estreia)
- **Quantidade planejada de inimigos:** 8–12 (chefes não contados)
- **Obstáculos:**
  - lagoa funda (não letal) com saída exigindo salto
  - pinças periódicas do caranguejo
  - arcos do peixe sobre o píer
  - pedras com vãos de 110 u sobre água rasa
- **Itens disponíveis:**
  - crescer: ? x450
  - fogo: ? x2500
  - estrela: gruta secreta
  - coração: mirante
- **Segredos:**
  - `pool_pearl` (hidden_area) — pista: Bolhas sobem de baixo de uma rocha no fundo da lagoa; brilho perolado; recompensa: relíquia relic_pearl
  - `lifeguard_tower` (high_route) — pista: Caixotes empilhados até a torre do salva-vidas; bandeira vermelha tremulando no alto; recompensa: relíquia relic_tower e coração
  - `drain_grotto` (warp_room) — pista: Manilha de pedra na areia com água borbulhando e estrela-do-mar desenhada; recompensa: relíquia relic_grotto e estrela
- **Colecionáveis:** ~75 moedas e 3 relíquias
- **Checkpoints:** 2
- **Eventos especiais:**
  - message (x2200): Mestre Búzio — “Na água, toque o salto para nadar. Segurar não adianta.”
- **Elementos animados:**
  - ondas e espuma na beira
  - volume de água com superfície ondulando e raios de sol
  - peixe saltando com respingo
  - caranguejo erguendo e baixando as pinças
  - gaivotas e cardumes decorativos
- **Trilha sonora:** `coral_coast_main` — praia ensolarada: ukulele, steel drum suave e ondas (sub-áreas: `coral_coast_underwater`)
- **Condição de conclusão:** Tocar a bandeira-concha em x4450.
- **Critérios de teste:**
  - validate_level e validate_campaign sem erros (schema, espécies, bioma, ordem de introdução, warps com chão)
  - route_bot conclui a fase partindo do spawn e de cada um dos 2 checkpoint(s), com inimigos e perigos ativos
  - vãos obrigatórios ≤ 150 u na mesma altura e subidas obrigatórias ≤ 64 u, simulados nas duas alturas do jogador sem coyote nem buffer
  - as 3 relíquias e todas as moedas são alcançáveis (rota de teste dedicada por relíquia; nenhuma moeda leva a morte)
  - estreias (Caranguejo-Pinça, Peixe-Saltador) em chão plano com ≥ 300 u de aproximação visível, recuo livre e nenhum vão letal a 200 u
  - teto sobre patrulha: nenhum sólido não semissólido com base entre y_chão−158 e y_chão−30 sobre a patrulha de inimigo terrestre a menos de 160 u de um vão obrigatório
  - zona segura de cada checkpoint: chão plano de x−96 a x+192 e nenhum inimigo comum alcança [x−160, x+320] em 3 s de simulação
  - toda água é swim (não letal) e toda saída da água tem borda a ≤ 70 u acima da superfície
  - estreia do caranguejo em areia plana com ≥ 300 u de aproximação e recuo livre
  - o peixe-saltador nunca salta sobre o checkpoint x2200
  - a gruta de 240 u é atravessável nadando em ≤ 4 s sem correntes
- **Requisitos de motor:** nenhum (implementável com o motor atual)

### 3-2 · Piscinas da Maré (`tide_pools`)

*Ideia própria:* a moreia não sai se Lume encostar na toca: a regra vira ferramenta.

- **Identificador:** `tide_pools`
- **Nome:** Piscinas da Maré
- **Mundo:** Costa dos Corais (`coral_coast`, bioma `coast`), fase 2 de 6 — origem: nova
- **Objetivo:** Explorar piscinas naturais em alturas diferentes, ligadas por túneis e quedas d'água, com rotas por cima das rochas ou por dentro da água; apresentar o baiacu que infla e a moreia que emerge da toca.
- **Tema visual:** Costão rochoso com piscinas naturais em degraus, anêmonas, cracas e estrelas-do-mar, quedas d'água entre piscinas, túneis de rocha escura; maré baixa no fim da manhã.
- **Mecânica principal:** Piscinas em alturas diferentes ligadas por túneis submersos e quedas d'água (current force_y +)
- **Mecânicas secundárias:**
  - Baiacu-Espinho (infla quando Lume se aproxima; murcho pode ser pisado)
  - Moreia-da-Toca (emerge e morde; não sai com Lume encostado)
  - rochas soltas (pedras frágeis)
  - sala opcional da maré cheia
- **Dificuldade:** 3/10
- **Duração planejada:** 90–180 s (primeira travessia → exploração completa)
- **Tamanho do cenário:** 5000 × 1240 u
  - `main` [coast] 0,0 5000×1240: costão com piscinas em três alturas (y≈300, 650 e 950)
- **Caminho principal** (sequência de ensino):
  1. **Introdução** (0–700 u) — Primeira piscina com um baiacu flutuando calmo; o jogador vê de cima ele inflar quando chega perto — sem precisar entrar.
  2. **Demonstração segura** (700–1300 u) — Moreia-da-Toca (estreia) numa fenda acima d'água ao lado de chão largo: encostar na toca a mantém dentro (placa do Mestre Búzio).
  3. **Primeiro desafio** (1300–2000 u) — Piscina com dois baiacus: contornar quando inflados, pisar quando murchos; túnel curto até a piscina de baixo.
  4. **Escalada** (2000–2800 u) — Checkpoint x2100; piscinas em escada ligadas por quedas d'água que empurram para baixo (current force_y +300); moreias nas paredes dos canais.
  5. **Combinação** (2800–3600 u) — Rotas paralelas: rochas altas com pedras frágeis e caranguejos ou túneis com baiacus e peixes saltando entre piscinas.
  6. **Reviravolta** (3600–4200 u) — Corredor de moreias alternadas: encostar numa toca segura a passagem enquanto a outra recolhe — a regra de timidez vira ferramenta.
  7. **Teste final** (4200–4700 u) — 2º checkpoint x4150; poço vertical de nado com moreias dos dois lados e baiacus no meio.
  8. **Recompensa** (4700–5000 u) — Saída para a rocha mais alta ao sol e bandeira em x4850.
- **Caminhos alternativos:**
  - Rota alta das rochas (pedras frágeis, estrela-do-mar no pilar) — reencontra em x3600.
  - Rota dos túneis submersos (mais moedas, baiacus).
  - Gruta da Maré: sala opcional onde a água sobe em ciclos (requer rising_lava variante água; versão estática enquanto não houver).
- **Inimigos permitidos:** `caramujo` (Caramujo-de-Casca), `caranguejo_pinca` (Caranguejo-Pinça), `peixe_saltador` (Peixe-Saltador), `baiacu_espinho` (Baiacu-Espinho — estreia), `moreia_toca` (Moreia-da-Toca — estreia)
- **Quantidade planejada de inimigos:** 12–16 (chefes não contados)
- **Obstáculos:**
  - quedas d'água que empurram para baixo
  - baiacus inflados (espinhos)
  - mordidas da moreia
  - pedras frágeis sobre piscinas
- **Itens disponíveis:**
  - crescer: ? x400
  - fogo: ? x2300
  - estrela: Gruta da Maré
  - coração: pilar da estrela-do-mar
- **Segredos:**
  - `starfish_pillar` (high_route) — pista: Estrela-do-mar dourada no topo de um pilar de rocha; pedras soltas em degraus; recompensa: relíquia relic_starfish e coração
  - `tide_grotto` (optional_challenge) — pista: Marca de maré (faixa de cracas) na entrada de uma gruta e água pingando do teto; recompensa: relíquia relic_tide e estrela
  - `waterfall_blocks` (hidden_block) — pista: Moedas aparecem e somem atrás da queda d'água central; o respingo desvia num ponto vazio; recompensa: relíquia relic_waterfall
- **Colecionáveis:** ~85 moedas e 3 relíquias
- **Checkpoints:** 2
- **Eventos especiais:**
  - message (x2100): Mestre Búzio — “Encoste na toca e a moreia fica quietinha.”
  - rising_lava (variante água, opcional): maré da Gruta da Maré sobe 160 u e baixa a cada 10 s
- **Elementos animados:**
  - quedas d'água com espuma
  - anêmonas balançando
  - baiacu inflando e murchando
  - moreia espiando da fenda antes de morder
- **Trilha sonora:** `coral_coast_main` — maré baixa: marimba e guitarra limpa; nas piscinas, filtro abafado (sub-áreas: `coral_coast_underwater`)
- **Condição de conclusão:** Tocar a bandeira em x4850.
- **Critérios de teste:**
  - validate_level e validate_campaign sem erros (schema, espécies, bioma, ordem de introdução, warps com chão)
  - route_bot conclui a fase partindo do spawn e de cada um dos 2 checkpoint(s), com inimigos e perigos ativos
  - vãos obrigatórios ≤ 150 u na mesma altura e subidas obrigatórias ≤ 64 u, simulados nas duas alturas do jogador sem coyote nem buffer
  - as 3 relíquias e todas as moedas são alcançáveis (rota de teste dedicada por relíquia; nenhuma moeda leva a morte)
  - estreias (Baiacu-Espinho, Moreia-da-Toca) em chão plano com ≥ 300 u de aproximação visível, recuo livre e nenhum vão letal a 200 u
  - teto sobre patrulha: nenhum sólido não semissólido com base entre y_chão−158 e y_chão−30 sobre a patrulha de inimigo terrestre a menos de 160 u de um vão obrigatório
  - zona segura de cada checkpoint: chão plano de x−96 a x+192 e nenhum inimigo comum alcança [x−160, x+320] em 3 s de simulação
  - a moreia nunca emerge com Lume encostado na toca (shy_radius) — teste nas duas alturas
  - o baiacu inflado fere em qualquer contato; murcho pode ser pisado
  - toda queda d'água deixa nadar contra ela ou sair por uma borda lateral
  - a Gruta da Maré é opcional e, sem o evento, funciona como sala estática
- **Requisitos de motor:** 
  - não bloqueia — rising_lava (extensão): a subida única de um perigo por evento já existe (hazard/to/speed, gatilho por x); faltam ciclos de subida e descida, gatilho por altura, tempo ou chefe, aviso sonoro, etapas com pausa, reposição no checkpoint e a variante com zona swim (maré) — só na sala opcional; a fase é jogável sem

### 3-3 · Recife do Farol (`lighthouse_reef`)

*Ideia própria:* a ressaca ritmada alaga o passadiço e faz as boias subirem.

- **Identificador:** `lighthouse_reef`
- **Nome:** Recife do Farol
- **Mundo:** Costa dos Corais (`coral_coast`, bioma `coast`), fase 3 de 6 — origem: nova
- **Objetivo:** Desafio de movimento vertical: subir do recife ao topo do farol durante a ressaca, com boias que balançam, conchas-mola, ondas periódicas e peixes saltando.
- **Tema visual:** Recife ao entardecer com farol listrado vermelho e branco, passadiço de madeira, boias coloridas, conchas gigantes, ondas quebrando; o facho do farol varre o céu.
- **Mecânica principal:** Escalada vertical com boias balançando (moving axis y) e conchas-mola (spring)
- **Mecânicas secundárias:**
  - ondas periódicas (current force_x com período 4 s) no passadiço alagado
  - andaimes semissólidos
  - rochas frágeis
  - rajadas no balcão do farol (vento já conhecido)
- **Dificuldade:** 4/10
- **Duração planejada:** 100–200 s (primeira travessia → exploração completa)
- **Tamanho do cenário:** 4800 × 2700 u
  - `main` [coast] 0,0 4800×2160: recife (y≈1900) até o balcão do farol (y≈300)
  - `cistern` [underwater] 3800,2160 1000×540: cisterna secreta sob a base do farol
- **Caminho principal** (sequência de ensino):
  1. **Introdução** (0–600 u (y≈1900)) — Recife plano: concha-mola sobre areia firme com moedas acima (subir e cair sem risco).
  2. **Demonstração segura** (600–1200 u) — Boias balançando (±24 u) sobre água rasa: cair = nadar até uma escada de corda.
  3. **Primeiro desafio** (1200–2000 u) — Cadeia de boias sobre água funda com peixes saltando entre elas (arcos de 3,2 s); checkpoint x2000 na rocha do recife.
  4. **Escalada** (2000–2800 u (sobe a y≈1200)) — Esporão de rocha: conchas-mola levando a andaimes semissólidos, rochas frágeis e caranguejos nas saliências.
  5. **Combinação** (2800–3600 u) — Base do farol: passadiço alagado onde uma onda (current +160, período 4 s, duty 0,35) atravessa e as boias sobem; pular nas boias entre ondas.
  6. **Reviravolta** (3600–4200 u (sobe a y≈500)) — Subida em espiral pelo exterior do farol: andaimes, molas e o facho passando (ilumina moedas); 2º checkpoint na galeria intermediária.
  7. **Teste final** (4200–4600 u (y≈300)) — Balcão do topo: rajadas de vento (já conhecidas) e tábuas frágeis em volta da lanterna.
  8. **Recompensa** (4600–4800 u) — Sala da lanterna: portão/bandeira em x4700 e vista panorâmica da costa.
- **Caminhos alternativos:**
  - Ninho de gaivota na saliência externa do farol, por molas encadeadas (relíquia).
  - Ralo na base do farol → cisterna submersa (relíquia, estrela).
  - Rota baixa nadando sob o passadiço (sem ondas, mais longa, com moreias).
- **Inimigos permitidos:** `caramujo` (Caramujo-de-Casca), `caranguejo_pinca` (Caranguejo-Pinça), `peixe_saltador` (Peixe-Saltador), `baiacu_espinho` (Baiacu-Espinho), `moreia_toca` (Moreia-da-Toca)
- **Quantidade planejada de inimigos:** 12–16 (chefes não contados)
- **Obstáculos:**
  - boias balançando sobre água funda
  - ondas periódicas no passadiço
  - rochas e tábuas frágeis
  - rajadas no balcão
  - peixes saltando nas boias
- **Itens disponíveis:**
  - crescer: ? no recife
  - fogo: ? na base do farol
  - estrela: cisterna
  - coração: galeria intermediária
- **Segredos:**
  - `gull_nest` (high_route) — pista: Gaivota circulando sobre uma saliência externa; penas caindo marcam as molas; recompensa: relíquia relic_nest
  - `cistern` (warp_room) — pista: Ralo de bronze na base do farol com água correndo para dentro; recompensa: relíquia relic_cistern e estrela
  - `buoy_block` (hidden_block) — pista: Uma boia sem corda balança sob um ponto onde moedas cintilam no ar; recompensa: relíquia relic_buoy
- **Colecionáveis:** ~90 moedas e 3 relíquias
- **Checkpoints:** 2
- **Eventos especiais:**
  - message (x2000): Mestre Búzio — “A onda vem a cada quatro batidas. Conte e pule.”
  - camera_lock vertical (opcional) na espiral do farol para manter a lanterna em quadro
- **Elementos animados:**
  - facho do farol girando (decorativo)
  - boias balançando com fitas
  - ondas atravessando o passadiço
  - conchas-mola abrindo e fechando
- **Trilha sonora:** `coral_coast_main` — ressaca ao entardecer: cordas em crescendo e sino de boia marcando a onda (sub-áreas: `coral_coast_underwater`)
- **Condição de conclusão:** Chegar à sala da lanterna e tocar a bandeira em x4700 (y≈300).
- **Critérios de teste:**
  - validate_level e validate_campaign sem erros (schema, espécies, bioma, ordem de introdução, warps com chão)
  - route_bot conclui a fase partindo do spawn e de cada um dos 2 checkpoint(s), com inimigos e perigos ativos
  - vãos obrigatórios ≤ 150 u na mesma altura e subidas obrigatórias ≤ 64 u, simulados nas duas alturas do jogador sem coyote nem buffer
  - as 3 relíquias e todas as moedas são alcançáveis (rota de teste dedicada por relíquia; nenhuma moeda leva a morte)
  - teto sobre patrulha: nenhum sólido não semissólido com base entre y_chão−158 e y_chão−30 sobre a patrulha de inimigo terrestre a menos de 160 u de um vão obrigatório
  - zona segura de cada checkpoint: chão plano de x−96 a x+192 e nenhum inimigo comum alcança [x−160, x+320] em 3 s de simulação
  - toda queda durante a escalada cai em água ou em plataforma a ≤ 260 u abaixo (nenhuma queda cega acima de 220 u sem trilha de moedas)
  - a onda tem aviso de 1 s (fita da boia esticando e som de sino)
  - subidas obrigatórias ≤ 64 u ou feitas por mola/boia
  - o bot conclui partindo dos 2 checkpoints
- **Requisitos de motor:** nenhum (implementável com o motor atual)

### 3-4 · Correntes Profundas (`current_depths`)

*Ideia própria:* a maré reversa troca a direção da corrente no meio do caminho.

- **Identificador:** `current_depths`
- **Nome:** Correntes Profundas
- **Mundo:** Costa dos Corais (`coral_coast`, bioma `coast`), fase 4 de 6 — origem: nova
- **Objetivo:** Mecânica especial da Costa dos Corais: nadar no mar aberto usando e evitando correntes com período e direção, e conhecer a Água-Viva Elétrica, que não pode ser pisada.
- **Tema visual:** Mar profundo azul com raios de luz descendo, paredões de recife, bosques de algas, bolhas e boias de sinalização com fitas; fundo arenoso com ouriços-do-mar (espinhos).
- **Mecânica principal:** Correntes subaquáticas (zonas current) com força, período e duty; direção reversível por zonas em fase oposta
- **Mecânicas secundárias:**
  - Água-Viva Elétrica (topo eletrificado; só fogo ou estrela)
  - bolsões de ar com chão de rocha
  - corrente descendente rumo a ouriços-do-mar (espinhos)
  - gêiser ascendente final
- **Dificuldade:** 4/10
- **Duração planejada:** 110–210 s (primeira travessia → exploração completa)
- **Tamanho do cenário:** 5400 × 1620 u
  - `main` [coast] 0,0 5400×1620: mar aberto (swim de y≈260 a y≈1560) com bolsões de ar
- **Caminho principal** (sequência de ensino):
  1. **Introdução** (0–700 u) — Mergulho de uma rocha; corrente constante suave (+60) em mar aberto com moedas no fluxo.
  2. **Demonstração segura** (700–1300 u) — Correnteza expressa (+180) dentro de um túnel largo, sem inimigos nem perigos: o jogador é levado e coleta moedas.
  3. **Primeiro desafio** (1300–2000 u) — Água-Viva (estreia): três águas-vivas em água parada, subindo e descendo devagar (±60 u); contornar.
  4. **Escalada** (2000–2800 u) — Checkpoint x2000 num bolsão de ar; corrente descendente pulsante (force_y +120, período 3 s, duty 0,5) empurra para ouriços-do-mar: subir nas pausas.
  5. **Combinação** (2800–3800 u) — Túnel de correnteza com águas-vivas à deriva, baiacus e moreias nas paredes.
  6. **Reviravolta** (3800–4500 u) — Maré reversa: duas zonas sobrepostas em fases opostas (+150/−150, período 4 s); a fita das boias mostra a fase; avançar só com a corrente a favor.
  7. **Teste final** (4500–5100 u) — 2º checkpoint x4500; gêiser ascendente (force_y −600 em água) leva à superfície atravessando um campo de águas-vivas.
  8. **Recompensa** (5100–5400 u) — Banco de areia à superfície e bandeira em x5250.
- **Caminhos alternativos:**
  - Bolsão lateral contra uma corrente fraca até a concha-trompa (relíquia).
  - Bosque de algas: cortina de algas (decor front) esconde uma passagem (relíquia).
  - Correnteza expressa cronometrada: 30 moedas em uma passada (relíquia).
- **Inimigos permitidos:** `caranguejo_pinca` (Caranguejo-Pinça), `peixe_saltador` (Peixe-Saltador), `baiacu_espinho` (Baiacu-Espinho), `moreia_toca` (Moreia-da-Toca), `agua_viva` (Água-Viva Elétrica — estreia)
- **Quantidade planejada de inimigos:** 14–18 (chefes não contados)
- **Obstáculos:**
  - correntes horizontais e verticais com período
  - ouriços-do-mar no fundo (spikes)
  - águas-vivas de topo elétrico
  - túneis estreitos com moreias
- **Itens disponíveis:**
  - fogo: ? no primeiro bolsão (contra águas-vivas)
  - crescer: ? x1200
  - estrela: bosque de algas
  - coração: bolsão do checkpoint 2
- **Segredos:**
  - `trumpet_shell` (hidden_area) — pista: Concha-trompa brilhando num bolsão lateral, contra uma corrente fraca marcada por fita mole; recompensa: relíquia relic_trumpet
  - `kelp_curtain` (hidden_area) — pista: Peixes de cardume entram na cortina de algas e não saem do outro lado; recompensa: relíquia relic_kelp e estrela
  - `express_run` (optional_challenge) — pista: Placa do Mestre Búzio: 'Trinta moedas numa só correnteza'; recompensa: relíquia relic_express
- **Colecionáveis:** ~100 moedas e 3 relíquias
- **Checkpoints:** 2
- **Eventos especiais:**
  - message (x2000): Mestre Búzio — “Fita esticada é correnteza forte. Fita mole, pode passar.”
- **Elementos animados:**
  - fitas das boias sincronizadas com as correntes
  - partículas de corrente (bolhas e areia em fluxo)
  - águas-vivas pulsando com brilho elétrico
  - raios de luz e algas balançando
- **Trilha sonora:** `coral_coast_underwater` — profundezas: pads líquidos, harpa e baixo pulsante no ritmo das correntes (sub-áreas: `coral_coast_main`)
- **Condição de conclusão:** Emergir no banco de areia e tocar a bandeira em x5250.
- **Critérios de teste:**
  - validate_level e validate_campaign sem erros (schema, espécies, bioma, ordem de introdução, warps com chão)
  - route_bot conclui a fase partindo do spawn e de cada um dos 2 checkpoint(s), com inimigos e perigos ativos
  - vãos obrigatórios ≤ 150 u na mesma altura e subidas obrigatórias ≤ 64 u, simulados nas duas alturas do jogador sem coyote nem buffer
  - as 3 relíquias e todas as moedas são alcançáveis (rota de teste dedicada por relíquia; nenhuma moeda leva a morte)
  - estreias (Água-Viva Elétrica) em chão plano com ≥ 300 u de aproximação visível, recuo livre e nenhum vão letal a 200 u
  - teto sobre patrulha: nenhum sólido não semissólido com base entre y_chão−158 e y_chão−30 sobre a patrulha de inimigo terrestre a menos de 160 u de um vão obrigatório
  - zona segura de cada checkpoint: chão plano de x−96 a x+192 e nenhum inimigo comum alcança [x−160, x+320] em 3 s de simulação
  - nenhuma corrente obrigatória excede a velocidade de nado (150 u/s) sem uma pausa de duty ≤ 0,6
  - a fita das boias muda ≥ 0,5 s antes da troca de fase da maré reversa
  - a água-viva nunca pode ser pisada e o fogo funciona debaixo d'água
  - nenhuma corrente empurra para dentro de espinhos sem bolsão de fuga a ≤ 200 u
- **Requisitos de motor:** nenhum (implementável com o motor atual)

### 3-5 · Labirinto de Coral (`coral_maze`)

*Ideia própria:* o labirinto desce e a saída fica no alto: fuga ascendente com dois polvos.

- **Identificador:** `coral_maze`
- **Nome:** Labirinto de Coral
- **Mundo:** Costa dos Corais (`coral_coast`, bioma `coast`), fase 5 de 6 — origem: nova
- **Objetivo:** Desafio avançado: atravessar um labirinto submerso de coral com três ramificações, válvulas de corrente de mão única e o Polvo-Tinteiro, que persegue quem está nadando; o coral laranja aponta o caminho certo.
- **Tema visual:** Labirinto de coral bioluminescente (laranja = caminho, violeta = beco com prêmio), cavernas azul-escuras, cardumes, ossos de baleia decorativos; superfície de recife no início e no fim.
- **Mecânica principal:** Navegação em labirinto submerso com válvulas de corrente (passagens de mão única) e perseguidor (polvo)
- **Mecânicas secundárias:**
  - Polvo-Tinteiro (persegue em impulsos só quando Lume nada; habitat underwater)
  - bolsões de ar como refúgio
  - blocos de coral quebradiço (tijolos)
  - moreias nas junções e águas-vivas nos poços
- **Dificuldade:** 5/10
- **Duração planejada:** 130–260 s (primeira travessia → exploração completa)
- **Tamanho do cenário:** 5600 × 1620 u
  - `main` [coast] 0,0 5600×540: recife de superfície (entrada x0–1200 e saída x4600–5600)
  - `maze` [underwater] 1200,540 3400×1080: labirinto submerso com três ramos
- **Caminho principal** (sequência de ensino):
  1. **Introdução** (0–1200 u) — Recife raso com caranguejos e peixes; fenda de coral laranja (cano) leva ao labirinto.
  2. **Demonstração segura** (Labirinto: 1º salão) — Polvo-Tinteiro (estreia) num salão aberto com um bolsão de ar ao lado: ele só persegue quem nada (até 260 u); sair da água o faz desistir.
  3. **Primeiro desafio** (Corredores 1–2) — Junções com moreias e válvulas de corrente (+200) que só deixam passar num sentido: aprender que o labirinto tem mão única.
  4. **Escalada** (Checkpoint no bolsão central) — Checkpoint num bolsão de ar; três ramos: laranja (saída), violeta (relíquia) e azul (moedas e volta).
  5. **Combinação** (Poço das águas-vivas) — Poço vertical com águas-vivas e baiacus, polvo entrando pela lateral.
  6. **Reviravolta** (Coração do coral) — Depois de descer o labirinto inteiro, a saída é uma corrente ascendente no coração do coral — fuga para cima com dois polvos no encalço.
  7. **Teste final** (Saída (x4600–5200)) — 2º checkpoint na superfície; recife final com moreias e peixes saltando sobre pedras.
  8. **Recompensa** (5200–5600 u) — Lagoa calma e bandeira em x5450.
- **Caminhos alternativos:**
  - Ramo violeta: beco das pérolas (relíquia).
  - Coral quebradiço (tijolos) acima do salão central — Lume grande abre (relíquia).
  - Anel de corrida contra o polvo: volta estreita com dois polvos (relíquia).
- **Inimigos permitidos:** `caramujo` (Caramujo-de-Casca), `caranguejo_pinca` (Caranguejo-Pinça), `peixe_saltador` (Peixe-Saltador), `baiacu_espinho` (Baiacu-Espinho), `moreia_toca` (Moreia-da-Toca), `agua_viva` (Água-Viva Elétrica), `polvo_tinteiro` (Polvo-Tinteiro — estreia)
- **Quantidade planejada de inimigos:** 16–22 (chefes não contados)
- **Obstáculos:**
  - válvulas de corrente de mão única
  - perseguição do polvo
  - moreias em junções
  - águas-vivas em poços verticais
- **Itens disponíveis:**
  - fogo: ? no recife de entrada
  - crescer: bolsão central
  - estrela: ramo azul
  - coração: 2º checkpoint
- **Segredos:**
  - `pearl_alley` (hidden_area) — pista: Pérolas cintilando no fim de um corredor de coral violeta; recompensa: relíquia relic_pearls
  - `brittle_coral` (breakable_path) — pista: Coral esbranquiçado e rachado no teto do salão central, com bolhas escapando; recompensa: relíquia relic_coral
  - `octopus_loop` (optional_challenge) — pista: Placa de pedra com desenho de polvo e seta circular na entrada de uma volta estreita; recompensa: relíquia relic_octopus
- **Colecionáveis:** ~110 moedas e 3 relíquias
- **Checkpoints:** 2
- **Eventos especiais:**
  - message (entrada): Mestre Búzio — “Coral laranja aponta a saída do labirinto.”
- **Elementos animados:**
  - coral bioluminescente pulsando (laranja e violeta)
  - polvo impulsionando-se com jato de bolhas
  - válvulas de corrente com partículas de mão única
  - cardumes desviando do jogador
- **Trilha sonora:** `coral_coast_underwater` — labirinto: arpejos de celesta em espiral e contrabaixo tenso quando o polvo persegue (sub-áreas: `coral_coast_main`)
- **Condição de conclusão:** Sair do labirinto pela corrente ascendente e tocar a bandeira em x5450.
- **Critérios de teste:**
  - validate_level e validate_campaign sem erros (schema, espécies, bioma, ordem de introdução, warps com chão)
  - route_bot conclui a fase partindo do spawn e de cada um dos 2 checkpoint(s), com inimigos e perigos ativos
  - vãos obrigatórios ≤ 150 u na mesma altura e subidas obrigatórias ≤ 64 u, simulados nas duas alturas do jogador sem coyote nem buffer
  - as 3 relíquias e todas as moedas são alcançáveis (rota de teste dedicada por relíquia; nenhuma moeda leva a morte)
  - estreias (Polvo-Tinteiro) em chão plano com ≥ 300 u de aproximação visível, recuo livre e nenhum vão letal a 200 u
  - teto sobre patrulha: nenhum sólido não semissólido com base entre y_chão−158 e y_chão−30 sobre a patrulha de inimigo terrestre a menos de 160 u de um vão obrigatório
  - zona segura de cada checkpoint: chão plano de x−96 a x+192 e nenhum inimigo comum alcança [x−160, x+320] em 3 s de simulação
  - o polvo só aparece na sub-área underwater (regra de habitat) e desiste quando Lume sai da água
  - todo ramo do labirinto tem volta: nenhum beco prende o jogador atrás de válvula de mão única
  - o caminho laranja é contínuo do salão 1 até a saída
  - o bot conclui o labirinto em ≤ 140 s partindo do checkpoint central
- **Requisitos de motor:** nenhum (implementável com o motor atual)

### 3-6 · Galeão Submerso (`sunken_galleon`)

*Ideia própria:* o mastro tombado vira ponte e o casco racha no meio da luta.

- **Identificador:** `sunken_galleon`
- **Nome:** Galeão Submerso
- **Mundo:** Costa dos Corais (`coral_coast`, bioma `coast`), fase 6 de 6 — origem: nova
- **Objetivo:** Fortaleza da Costa dos Corais: atravessar o galeão naufragado de compartimentos ora secos, ora alagados, e derrotar o Ermitão-Âncora, que usa a popa do navio como concha.
- **Tema visual:** Galeão adernado sobre o recife: conveses inclinados de madeira escura, vigias redondas, barris, velas rasgadas, lanternas de latão, mastro tombado coberto de algas; penumbra esverdeada.
- **Mecânica principal:** Compartimentos alternando ar e água (zonas swim parciais) com conveses semissólidos inclinados em degraus
- **Mecânicas secundárias:**
  - correntes de água entrando por vigias quebradas (com período)
  - mastro tombado como ponte com correnteza
  - barris (tijolos) e baús
  - chefe planejado Ermitão-Âncora
- **Dificuldade:** 5/10
- **Duração planejada:** 150–290 s (primeira travessia → exploração completa)
- **Tamanho do cenário:** 6000 × 1620 u
  - `main` [coast] 0,0 4900×1080: recife externo e conveses do galeão
  - `hold` [underwater] 1800,1080 2400×540: porão alagado
  - `bow_hold` [underwater] 4900,0 1100×1620: porão de proa (arena)
- **Caminho principal** (sequência de ensino):
  1. **Introdução** (0–700 u) — Recife externo: o casco adernado; entrada por um rombo no costado.
  2. **Demonstração segura** (700–1400 u) — Primeiro compartimento meio alagado: conveses em degraus semissólidos e bolsões de ar — nadar e sair da água em ritmo.
  3. **Primeiro desafio** (1400–2200 u) — Porão de carga: barris (tijolos), caranguejos no convés e moreias nas vigias.
  4. **Escalada** (2200–3000 u) — Checkpoint x2200; corredores alagados com jatos d'água pelas vigias (current com período 3 s) e águas-vivas na cabine do capitão.
  5. **Combinação** (3000–3800 u) — Porão alagado (sub-área underwater): polvo, baiacus e peixes saltando entre conveses pelos rombos.
  6. **Reviravolta** (3800–4500 u) — O mastro tombado vira ponte horizontal com correnteza ao longo dele e velas semissólidas.
  7. **Teste final** (4500–4900 u) — Antessala: checkpoint x4600 com a lanterna de popa do Mestre Búzio e coração.
  8. **Recompensa** (4900–6000 u) — Porão de proa: Ermitão-Âncora (5 PV); na fase 2 a água sobe; vitória ergue o galeão na maré; bandeira em x5850.
- **Caminhos alternativos:**
  - Gurupés externo (proa) por fora do casco até a figura de proa (relíquia).
  - Cabine do capitão: bloco oculto revela passagem para o baú (relíquia).
  - Escotilha de canhão (cano) → sala do tesouro (relíquia, estrela).
- **Inimigos permitidos:** `caramujo` (Caramujo-de-Casca), `caranguejo_pinca` (Caranguejo-Pinça), `peixe_saltador` (Peixe-Saltador), `baiacu_espinho` (Baiacu-Espinho), `moreia_toca` (Moreia-da-Toca), `agua_viva` (Água-Viva Elétrica), `polvo_tinteiro` (Polvo-Tinteiro), `boss:ermitao_ancora` (Ermitão-Âncora (chefe planejado))
- **Quantidade planejada de inimigos:** 18–24 (chefes não contados)
- **Obstáculos:**
  - jatos d'água periódicos pelas vigias
  - conveses inclinados em degraus
  - porão alagado com perseguidor
  - correnteza ao longo do mastro
- **Itens disponíveis:**
  - crescer: ? no primeiro compartimento
  - fogo: ? no porão de carga
  - estrela: sala do tesouro
  - coração: antessala
- **Segredos:**
  - `figurehead` (high_route) — pista: Gaivota pousada na figura de proa; cordas do gurupés com moedas; recompensa: relíquia relic_figurehead
  - `captain_chest` (hidden_block) — pista: Mapa na parede da cabine com um X sobre um ponto vazio do teto; recompensa: relíquia relic_chest
  - `cannon_hatch` (warp_room) — pista: Escotilha de canhão aberta com bolhas e luz dourada saindo; recompensa: relíquia relic_treasure e estrela
- **Colecionáveis:** ~100 moedas e 3 relíquias
- **Checkpoints:** 2
- **Eventos especiais:**
  - boss_arena (x4900): trava a câmera no porão de proa e fecha a antepara
  - rising_lava variante água (fase 2 do chefe): a água sobe de y420 para y260 na arena
  - message (x4600): Mestre Búzio — “O ermitão só larga a pinça quando ela fica presa na madeira.”
- **Elementos animados:**
  - velas rasgadas ondulando na água
  - jatos pelas vigias
  - lanternas de latão balançando
  - galeão se erguendo na maré na vitória
- **Trilha sonora:** `coral_coast_fortress` — naufrágio: rangidos de madeira, órgão de vento e percussão de casco; tema do chefe com tambores de guerra marinhos (sub-áreas: `coral_coast_underwater`, `coral_coast_boss`)
- **Condição de conclusão:** Derrotar o Ermitão-Âncora (5 PV) e tocar a bandeira em x5850.
- **Critérios de teste:**
  - validate_level e validate_campaign sem erros (schema, espécies, bioma, ordem de introdução, warps com chão)
  - route_bot conclui a fase partindo do spawn e de cada um dos 2 checkpoint(s), com inimigos e perigos ativos
  - vãos obrigatórios ≤ 150 u na mesma altura e subidas obrigatórias ≤ 64 u, simulados nas duas alturas do jogador sem coyote nem buffer
  - as 3 relíquias e todas as moedas são alcançáveis (rota de teste dedicada por relíquia; nenhuma moeda leva a morte)
  - teto sobre patrulha: nenhum sólido não semissólido com base entre y_chão−158 e y_chão−30 sobre a patrulha de inimigo terrestre a menos de 160 u de um vão obrigatório
  - zona segura de cada checkpoint: chão plano de x−96 a x+192 e nenhum inimigo comum alcança [x−160, x+320] em 3 s de simulação
  - o polvo só aparece nas sub-áreas underwater
  - cada compartimento alagado tem bolsão de ar a ≤ 400 u de nado
  - na fase 2 o nível d'água sobe sem prender o jogador sob o teto (folga ≥ 80 u)
  - o bot vence o chefe partindo do checkpoint da antessala
- **Requisitos de motor:** 
  - **bloqueia** — comportamento do chefe planejado Ermitão-Âncora (ermitao_ancora): família nova em lume/core/behaviors/bosses.py
  - **bloqueia** — rising_lava (extensão): a subida única de um perigo por evento já existe (hazard/to/speed, gatilho por x); faltam ciclos de subida e descida, gatilho por altura, tempo ou chefe, aviso sonoro, etapas com pausa, reposição no checkpoint e a variante com zona swim (maré) (variante água na fase 2 do chefe)

## Mundo 4 — Montanhas Geladas (`frozen_peaks`)

Lagos de cristal, encostas e nevascas. O gelo tira o freio: primeiro escorrega, depois vira encosta de embalo, avalanche e, no fim, a pista onde o casco de cristal derrota a morsa. Detalhes do mundo em [`MUNDO_04.md`](MUNDO_04.md).

### 4-1 · Lago de Cristal (`crystal_lake`)

*Ideia própria:* a patinação vira desafio: parar na ponta do píer congelado.

- **Identificador:** `crystal_lake`
- **Nome:** Lago de Cristal
- **Mundo:** Montanhas Geladas (`frozen_peaks`, bioma `snow`), fase 1 de 6 — origem: legada 3-1
- **Objetivo:** Apresentar o gelo — margens longas onde frear exige antecipação — e três habitantes do frio, cada um num trecho separado; a terceira relíquia pede uma parada precisa no gelo.
- **Tema visual:** Lago congelado com reflexos, margens de rocha nevada, pinheiros, cabana de pesca no gelo e buracos de pesca, montanhas azuladas ao fundo; manhã clara com brilho na neve.
- **Mecânica principal:** Superfície de gelo (atrito baixo: frenagem de ~321 u a partir da corrida)
- **Mecânicas secundárias:**
  - degraus de gelo (rota alta)
  - casco de cristal que ricocheteia
  - voadora de ondas curtas
  - pinguim que mergulha de barriga no gelo
- **Dificuldade:** 4/10
- **Duração planejada:** 60–130 s (primeira travessia → exploração completa)
- **Tamanho do cenário:** 3600 × 1240 u
  - `main` [snow] 0,0 3600×540: lago com margens de gelo (x1040–1860 e x2740–3600) e rocha entre elas
  - `pipe_room_area` [underground] 2139,700 960×540: câmara secreta
- **Caminho principal** (sequência de ensino):
  1. **Introdução** (0–920 u) — Margem de rocha (atrito normal); ? de crescer x400; dica 'No gelo, solte a corrida antes de pousar'; Caracol-de-Cristal (estreia) em [620, 860] em chão normal.
  2. **Demonstração segura** (920–1300 u) — Vão de 120 u para a primeira margem de gelo longa (820 u): pousar e sentir o deslize sem nada adiante por 330 u.
  3. **Primeiro desafio** (1300–1860 u) — Degraus de gelo (x1220 y382 → x1380 y314) com a relíquia alta; Coruja Nevada (estreia) voando em ondas sobre o gelo [1480, 1750]: passar por baixo do voo.
  4. **Escalada** (1860–2620 u) — Vão de 120 u para rocha; checkpoint x2040 com o Tio Nevasco; espinhos x2240 em chão normal; cano da câmara x2370.
  5. **Combinação** (2620–3100 u) — Vão de 120 u para a segunda margem de gelo: frear antes do Pinguim Patrulheiro (estreia, proposto [3200, 3400] com visão 220).
  6. **Reviravolta** (1700–1860 u (desafio)) — Píer congelado: três beirais de gelo decrescentes (96 → 64 u) sobre a margem; quem passa do ponto cai na neve fofa abaixo (sem dano) — parar na ponta dá a relíquia.
  7. **Teste final** (3100–3400 u) — Pinguim deslizando de barriga na sua direção no gelo — saltar no tempo certo ou pisar (vale pisar deslizando).
  8. **Recompensa** (3400–3600 u) — Bandeira em x3450 com arco de moedas sobre gelo.
- **Caminhos alternativos:**
  - Degraus de gelo x1220 → x1380 (relíquia alta).
  - Píer congelado x1700–1860 (relíquia do píer).
  - Cano x2370 → câmara (relíquia, fogo).
- **Inimigos permitidos:** `pinguim_patrulha` (Pinguim Patrulheiro — estreia), `caracol_cristal` (Caracol-de-Cristal — estreia), `coruja_nevada` (Coruja Nevada — estreia)
- **Quantidade planejada de inimigos:** 5–6 (chefes não contados)
- **Obstáculos:**
  - margens de gelo longas (frenagem de ~321 u)
  - 3 vãos de 120 u
  - espinhos x2240
  - barrigada do pinguim
- **Itens disponíveis:**
  - crescer: ? x400
  - moeda: ? x1570
  - estrela: ? x2940
  - fogo: câmara x2598
- **Segredos:**
  - `high_route` (high_route) — pista: Trilha de moedas sobe pelos degraus de gelo; recompensa: relíquia relic_high (x1418, y278)
  - `frozen_pier` (optional_challenge) — pista: Placa do Tio Nevasco 'pare aqui' e marcas de patins no gelo; recompensa: relíquia relic_pier (x1840, y320)
  - `pipe_room` (warp_room) — pista: Cano com seta luminosa coberto de geada; recompensa: relíquia relic_room (x2648, y850) e fogo
- **Colecionáveis:** ~48 moedas e 3 relíquias
- **Checkpoints:** 1
- **Eventos especiais:**
  - message (x2040): Tio Nevasco — “No gelo, solte a corrida antes de pousar. O freio vem depois.”
- **Elementos animados:**
  - reflexo do céu no gelo
  - neve caindo (weather snow)
  - faíscas de gelo ao derrapar
  - pinguim deslizando de barriga
- **Trilha sonora:** `frozen_peaks_main` — lago calmo: celesta, cordas em harmônicos e sinos de vento (sub-áreas: `frozen_peaks_underground`)
- **Condição de conclusão:** Tocar a bandeira em x3450.
- **Critérios de teste:**
  - validate_level e validate_campaign sem erros (schema, espécies, bioma, ordem de introdução, warps com chão)
  - route_bot conclui a fase partindo do spawn e de cada um dos 1 checkpoint(s), com inimigos e perigos ativos
  - vãos obrigatórios ≤ 150 u na mesma altura e subidas obrigatórias ≤ 64 u, simulados nas duas alturas do jogador sem coyote nem buffer
  - as 3 relíquias e todas as moedas são alcançáveis (rota de teste dedicada por relíquia; nenhuma moeda leva a morte)
  - estreias (Pinguim Patrulheiro, Caracol-de-Cristal, Coruja Nevada) em chão plano com ≥ 300 u de aproximação visível, recuo livre e nenhum vão letal a 200 u
  - teto sobre patrulha: nenhum sólido não semissólido com base entre y_chão−158 e y_chão−30 sobre a patrulha de inimigo terrestre a menos de 160 u de um vão obrigatório
  - zona segura de cada checkpoint: chão plano de x−96 a x+192 e nenhum inimigo comum alcança [x−160, x+320] em 3 s de simulação
  - ≥ 330 u entre cada pouso obrigatório no gelo e o próximo perigo (regra 5 da pesquisa)
  - a barrigada do pinguim só começa com o jogador fora da faixa de frenagem
  - falhar o píer congelado nunca causa dano nem morte
  - as três estreias ocorrem em chão onde o jogador consegue recuar
- **Requisitos de motor:** nenhum (implementável com o motor atual)
- **Plano de melhoria da fase legada:**
  - Mantidos: traçado de 4 margens (duas de gelo), vãos de 120 u, degraus de gelo e câmara.
  - Exceção do registro: três estreias (caracol, coruja, pinguim) — mantidas em trechos separados por ≥ 800 u; ver ajuste proposto (coruja para blue_ascent).
  - Pinguim: [3070, 3300] → [3200, 3400] com visão 220, para que a barrigada só comece depois da frenagem completa (pouso em x2740 + 321 u).
  - Terceira relíquia: desafio do píer congelado (beirais de gelo x1700–1860, y360).
  - Arte: cabana de pesca no gelo, buracos de pesca com bandeirinhas, pinheiros e reflexos no lago.

### 4-2 · Escalada Azul (`blue_ascent`)

*Ideia própria:* uma rota do cume acima dos seis terraços.

- **Identificador:** `blue_ascent`
- **Nome:** Escalada Azul
- **Mundo:** Montanhas Geladas (`frozen_peaks`, bioma `snow`), fase 2 de 6 — origem: legada 3-2
- **Objetivo:** Explorar a subida em seis terraços alternando gelo e rocha, conhecer o Boneco de Neve (atirador reto) e encontrar a rota do cume, acima do caminho principal.
- **Tema visual:** Encosta em terraços de gelo azul e rocha, pinheiros nevados, pilhas de pedra (marcos) e bandeirolas de lã, céu limpo e cumes ao fundo.
- **Mecânica principal:** Terraços alternando gelo e rocha com subidas de até 48 u e descidas de 32 u
- **Mecânicas secundárias:**
  - Boneco de Neve (bolas de neve em linha reta)
  - beirais de gelo semissólidos (correção)
  - plataforma móvel sobre o vão
  - rota do cume
- **Dificuldade:** 4/10
- **Duração planejada:** 70–150 s (primeira travessia → exploração completa)
- **Tamanho do cenário:** 4400 × 1240 u
  - `main` [snow] 0,0 4400×540: seis terraços (y448→416→368→400→432→448)
  - `pipe_room_area` [underground] 3440,700 960×540: câmara secreta
- **Caminho principal** (sequência de ensino):
  1. **Introdução** (0–600 u) — Base da encosta; ? de crescer x380; dica 'A subida é feita em terraços seguros'.
  2. **Demonstração segura** (600–1270 u) — Primeiro terraço de gelo (+32 u); caracol em [1010, 1230] sob beirais agora semissólidos (o salto não bate a cabeça); beirais levam à relíquia alta.
  3. **Primeiro desafio** (1270–2100 u) — Subida de 48 u para rocha; blocos ? x1560/x1640; Boneco de Neve (estreia) em [1760, 1980]: gira o corpo e lança bolas em linha reta — saltar ou pisar.
  4. **Escalada** (2100–2840 u) — Checkpoint x2280; terraço de gelo com plataforma móvel x2430 e beiral x2630 (início da rota do cume); coruja proposta sobre o gelo.
  5. **Combinação** (2840–3510 u) — Descida de 32 u; pinguim proposto num trecho de gelo curto com parede de neve de contenção; espinhos x3230; ? de coração x3360.
  6. **Reviravolta** (2630–3000 u (rota do cume)) — Beirais de gelo em y220 e y160 acima dos terraços levam ao pinheiro mais alto (relíquia do cume) — vista de todo o caminho percorrido.
  7. **Teste final** (3510–4100 u) — Último vão de 120 u (−16 u); cano da câmara x3770; segundo boneco de neve proposto disparando ao longo do terraço final.
  8. **Recompensa** (4100–4400 u) — Bandeira em x4250 ao pé de um marco de pedras.
- **Caminhos alternativos:**
  - Beirais semissólidos x910 → x1060 (relíquia alta).
  - Rota do cume a partir do beiral x2630 (relíquia do cume), desce no terraço 5.
  - Cano x3770 → câmara (relíquia, estrela).
- **Inimigos permitidos:** `pinguim_patrulha` (Pinguim Patrulheiro), `caracol_cristal` (Caracol-de-Cristal), `coruja_nevada` (Coruja Nevada), `boneco_neve` (Boneco de Neve — estreia)
- **Quantidade planejada de inimigos:** 6–8 (chefes não contados)
- **Obstáculos:**
  - 5 vãos de 110–120 u com desníveis de −32 a +48 u
  - terraços de gelo
  - bolas de neve em linha reta
  - espinhos x3230
- **Itens disponíveis:**
  - crescer: ? x380
  - fogo: ? x1560
  - moeda: ? x1640
  - coração: ? x3360
  - estrela: câmara x4018
- **Segredos:**
  - `high_route` (high_route) — pista: Trilha de moedas sobe pelos beirais de gelo; recompensa: relíquia relic_high (x1094, y248)
  - `summit_route` (high_route) — pista: Pinheiro mais alto com estrela de neve no topo; pegadas de coruja nos beirais; recompensa: relíquia relic_summit (x2980, y120)
  - `pipe_room` (warp_room) — pista: Cano com seta luminosa coberto de geada; recompensa: relíquia relic_room (x4068, y850) e estrela
- **Colecionáveis:** ~60 moedas e 3 relíquias
- **Checkpoints:** 1
- **Eventos especiais:**
  - message (x2280): Tio Nevasco — “Do cume se vê o caminho inteiro. E um pinheiro brilhando.”
- **Elementos animados:**
  - bandeirolas de lã ao vento
  - neve escorrendo dos pinheiros
  - boneco girando o corpo antes de lançar
  - plataforma móvel com cristais
- **Trilha sonora:** `frozen_peaks_main` — subida luminosa: flauta andina original em escala maior, harpa e passos ritmados (sub-áreas: `frozen_peaks_underground`)
- **Condição de conclusão:** Tocar a bandeira em x4250.
- **Critérios de teste:**
  - validate_level e validate_campaign sem erros (schema, espécies, bioma, ordem de introdução, warps com chão)
  - route_bot conclui a fase partindo do spawn e de cada um dos 1 checkpoint(s), com inimigos e perigos ativos
  - vãos obrigatórios ≤ 150 u na mesma altura e subidas obrigatórias ≤ 64 u, simulados nas duas alturas do jogador sem coyote nem buffer
  - as 3 relíquias e todas as moedas são alcançáveis (rota de teste dedicada por relíquia; nenhuma moeda leva a morte)
  - estreias (Boneco de Neve) em chão plano com ≥ 300 u de aproximação visível, recuo livre e nenhum vão letal a 200 u
  - teto sobre patrulha: nenhum sólido não semissólido com base entre y_chão−158 e y_chão−30 sobre a patrulha de inimigo terrestre a menos de 160 u de um vão obrigatório
  - zona segura de cada checkpoint: chão plano de x−96 a x+192 e nenhum inimigo comum alcança [x−160, x+320] em 3 s de simulação
  - teto sobre patrulha: o caracol [1010, 1230] não tem sólido não semissólido acima ao alcance do salto
  - todo pouso obrigatório no gelo tem ≥ 330 u livres ou parede de contenção
  - a rota do cume reencontra o terraço 5 sem queda cega > 220 u
  - as bolas de neve do boneco não alcançam a zona segura do checkpoint
- **Requisitos de motor:** nenhum (implementável com o motor atual)
- **Plano de melhoria da fase legada:**
  - Mantidos: seis terraços, vãos de 110–120 u, plataforma móvel e câmara.
  - Beirais ledge01/ledge02 (x910 e x1060) viram semissólidos de gelo: hoje ficam sobre a patrulha do caracol [1010, 1230] a 40 u do vão de 120 u e o salto bate a cabeça.
  - Densidade: de 2 para 6–8 inimigos (coruja sobre o terraço 4, pinguim no terraço 5 com parede de contenção, segundo boneco, segundo caracol).
  - Terceira relíquia: rota do cume (beirais y220 e y160 a partir de x2630; relíquia em x2980, y120).
  - Arte: marcos de pedra, bandeirolas de lã, pinheiros com neve escorrendo.

### 4-3 · Coração da Nevasca (`blizzard_heart`)

*Ideia própria:* a pedra vira abrigo e arma: o carneiro bate nela e fica tonto.

- **Identificador:** `blizzard_heart`
- **Nome:** Coração da Nevasca
- **Mundo:** Montanhas Geladas (`frozen_peaks`, bioma `snow`), fase 3 de 6 — origem: legada 3-3
- **Objetivo:** Desafio de movimento sob nevasca: rajadas contrárias sobre chão contínuo, gelo alternado com rocha, o Carneiro Glacial que investe e o Guardião da Nevasca (5 PV) numa arena seca.
- **Tema visual:** Nevasca horizontal com visibilidade reduzida (névoa branca em camadas), rochas negras, gelo azul, abrigos de pedra, guardião de gelo e granito numa arena de rocha seca.
- **Mecânica principal:** Rajadas de nevasca (wind −90 u/s, período 4 s, duty 0,4) sobre chão contínuo, alternando gelo e rocha
- **Mecânicas secundárias:**
  - Carneiro Glacial (raspa o casco, investe, bate na pedra e fica tonto)
  - bloco de granito como abrigo
  - plataformas móveis
  - chefe intermediário guardiao_nevasca
- **Dificuldade:** 5/10
- **Duração planejada:** 80–170 s (primeira travessia → exploração completa)
- **Tamanho do cenário:** 4600 × 1240 u
  - `main` [snow] 0,0 4600×540: cinco trechos (gelo/rocha) e arena seca x3870–4370
  - `pipe_room_area` [underground] 2109,700 960×540: câmara secreta
- **Caminho principal** (sequência de ensino):
  1. **Introdução** (0–580 u) — Rocha; ? de crescer x430; dica 'A neve esconde rotas altas, não o caminho seguro'.
  2. **Demonstração segura** (540–780 u) — Carneiro Glacial (estreia) em [580, 740] com bloco de granito (x540–580, h48) à esquerda: subir no bloco, deixar o carneiro bater e pisar quando tonto (2 golpes).
  3. **Primeiro desafio** (780–1550 u) — Vão de 120 u para gelo; beiral de gelo x1060 e plataforma móvel x1240 (relíquia alta); coruja em [1320, 1500].
  4. **Escalada** (1550–2510 u) — Vão para rocha; primeira faixa de nevasca (x1700–2500) só sobre chão contínuo: andar contra a rajada, esperar a pausa; ? de fogo x2040; checkpoint x2270; espinhos x1860 fora da nevasca.
  5. **Combinação** (2510–3360 u) — Gelo com boneco de neve em [2810, 2970] e plataforma vertical x3180 (? de estrela): bolas de neve + gelo + rajada fraca.
  6. **Reviravolta** (2300 u (segredo)) — No meio da rajada, flocos giram em volta de um ponto parado: bloco oculto que revela um degrau até o coração da nevasca (relíquia).
  7. **Teste final** (3360–3870 u) — Vão de 120 u; segunda faixa de nevasca (x3500–3840) sobre a rocha; 2º checkpoint proposto x3580 com coração; o guardião fica restrito à arena.
  8. **Recompensa** (3870–4600 u) — Arena seca: Guardião da Nevasca (5 PV); vitória libera a bandeira em x4450.
- **Caminhos alternativos:**
  - Beiral de gelo x1060 + plataforma móvel x1240 (relíquia alta).
  - Bloco oculto da nevasca x2300 (relíquia do coração).
  - Cano x2360 → câmara (relíquia, coração).
- **Inimigos permitidos:** `pinguim_patrulha` (Pinguim Patrulheiro), `caracol_cristal` (Caracol-de-Cristal), `coruja_nevada` (Coruja Nevada), `boneco_neve` (Boneco de Neve), `carneiro_glacial` (Carneiro Glacial — estreia), `guardiao_nevasca` (Guardião da Nevasca — estreia)
- **Quantidade planejada de inimigos:** 7–9 (chefes não contados)
- **Obstáculos:**
  - rajadas de nevasca sobre chão contínuo
  - 4 vãos de 110–120 u com desnível ±32 u
  - investida do carneiro
  - bolas de neve
  - espinhos x1860
- **Itens disponíveis:**
  - crescer: ? x430
  - fogo: ? x2040
  - estrela: ? x3090
  - coração: câmara x2568
  - coração: chão x3650
- **Segredos:**
  - `high_route` (high_route) — pista: Trilha de moedas pela plataforma móvel e pelo beiral de gelo; recompensa: relíquia relic_high (x1278, y238)
  - `blizzard_core` (hidden_block) — pista: Flocos de neve giram em volta de um ponto parado no ar, mesmo durante a rajada; recompensa: relíquia relic_core (x2360, y260)
  - `pipe_room` (warp_room) — pista: Cano com seta luminosa num abrigo de pedra; recompensa: relíquia relic_room (x2618, y850) e coração
- **Colecionáveis:** ~50 moedas e 3 relíquias
- **Checkpoints:** 2
- **Eventos especiais:**
  - message (x2270): Tio Nevasco — “Carneiro bravo bate na pedra e fica tonto. Fique em cima da pedra.”
  - message (x3660): “A rocha protege uma última arena de gelo.” (dica existente)
- **Elementos animados:**
  - nevasca em camadas (partículas horizontais) sincronizada com as rajadas
  - carneiro raspando o casco e ficando tonto (estrelinhas de gelo)
  - guardião abrindo a guarda
  - flocos girando no ponto do bloco oculto
- **Trilha sonora:** `frozen_peaks_main` — nevasca: vento sintetizado, cordas tremolo e tambor grave a cada rajada (sub-áreas: `frozen_peaks_underground`)
- **Condição de conclusão:** Derrotar o Guardião da Nevasca (5 PV) e tocar a bandeira em x4450.
- **Critérios de teste:**
  - validate_level e validate_campaign sem erros (schema, espécies, bioma, ordem de introdução, warps com chão)
  - route_bot conclui a fase partindo do spawn e de cada um dos 2 checkpoint(s), com inimigos e perigos ativos
  - vãos obrigatórios ≤ 150 u na mesma altura e subidas obrigatórias ≤ 64 u, simulados nas duas alturas do jogador sem coyote nem buffer
  - as 3 relíquias e todas as moedas são alcançáveis (rota de teste dedicada por relíquia; nenhuma moeda leva a morte)
  - estreias (Carneiro Glacial) em chão plano com ≥ 300 u de aproximação visível, recuo livre e nenhum vão letal a 200 u
  - teto sobre patrulha: nenhum sólido não semissólido com base entre y_chão−158 e y_chão−30 sobre a patrulha de inimigo terrestre a menos de 160 u de um vão obrigatório
  - zona segura de cada checkpoint: chão plano de x−96 a x+192 e nenhum inimigo comum alcança [x−160, x+320] em 3 s de simulação
  - nenhuma zona de nevasca cobre vão, espinho ou checkpoint
  - o carneiro em investida sempre encontra o bloco de granito e fica tonto
  - com a rajada ativa o jogador ainda avança (força 90 < corrida) e pode parar em pé
  - a bandeira só conclui após a derrota do guardião
- **Requisitos de motor:** nenhum (implementável com o motor atual)
- **Plano de melhoria da fase legada:**
  - Mantidos: cinco trechos, vãos de 110–120 u, guardião com 5 PV na arena seca e câmara.
  - Carneiro: patrulha [575, 725] → [580, 740] com bloco de granito x540–580 (h48): a estreia ensina a investida com batida na pedra, como o javali do Mundo 1.
  - Nevasca: duas zonas wind (−90 u/s, período 4 s, duty 0,4) em x1700–2500 e x3500–3840, nunca sobre vãos (o vento já foi ensinado no Mundo 2).
  - 2º checkpoint em x3580 (chão plano x3484–3772) com coração.
  - Terceira relíquia: bloco oculto no meio da nevasca (x2300, y340) → degrau → relíquia (x2360, y260).
  - Densidade: de 4 para 7–9 inimigos (pinguim no gelo de x900–1550 após 330 u, caracol no gelo x2630–3360).

### 4-4 · Encostas Escorregadias (`slippery_slopes`)

*Ideia própria:* a encosta invertida: subir degraus de gelo que empurram de volta.

- **Identificador:** `slippery_slopes`
- **Nome:** Encostas Escorregadias
- **Mundo:** Montanhas Geladas (`frozen_peaks`, bioma `snow`), fase 4 de 6 — origem: nova
- **Objetivo:** Mecânica especial das Montanhas Geladas: descer encostas de gelo longas sem poder frear, usando o embalo para saltar vãos no fim de cada rampa, e conhecer o Yeti-Mirim, que arremessa bolas de neve em arco.
- **Tema visual:** Encostas brancas brilhantes ao sol baixo, trilhas de trenó, bandeiras de slalom, pinheiros na beira da pista, chalé com fonte termal no fim; montanhas rosadas ao fundo.
- **Mecânica principal:** Encostas de gelo descendentes (degraus de 12 u com arte de rampa contínua) onde não é possível frear; salto no fim da rampa
- **Mecânicas secundárias:**
  - Yeti-Mirim (arremesso em arco com aviso: ergue a bola acima da cabeça)
  - paredes de neve de contenção
  - cascos de cristal ricocheteando encosta abaixo
  - pinguins deslizando na encosta
- **Dificuldade:** 4/10
- **Duração planejada:** 90–180 s (primeira travessia → exploração completa)
- **Tamanho do cenário:** 5600 × 1240 u
  - `main` [snow] 0,0 5600×540: encostas em terraços descendentes de gelo com platôs de rocha entre elas
  - `pipe_room_area` [underground] 679,700 960×540: caverna do trenó perdido (segredo)
- **Caminho principal** (sequência de ensino):
  1. **Introdução** (0–700 u) — Encosta suave curta com moedas, terminando num platô de rocha (atrito normal) que freia: aprender que no gelo inclinado não se para.
  2. **Demonstração segura** (700–1300 u) — Encosta mais longa terminando numa parede de neve fofa (sem dano): 'você não para no gelo — a parede para você'.
  3. **Primeiro desafio** (1300–2000 u) — Yeti-Mirim (estreia) num platô de rocha plano lançando bolas em arco sobre chão normal com abrigos (pedras).
  4. **Escalada** (2000–2800 u) — Checkpoint x2000; encostas com vãos de 120–140 u no fim de cada rampa (decolar no último degrau) e pinguins deslizando na direção de Lume.
  5. **Combinação** (2800–3600 u) — Yetis arremessando sobre a encosta + caracóis de cristal: chutar um casco encosta abaixo derruba os pinguins da frente.
  6. **Reviravolta** (3600–4300 u) — Encosta invertida: subir uma escada de beirais de gelo (degraus de 48 u) onde cada pouso desliza para a borda — saltar de novo antes de escorregar.
  7. **Teste final** (4300–5200 u) — Checkpoint x4300; a pista final: descida longa com vãos, yetis e pinguins, terminando num salto de rampa até o platô do chalé.
  8. **Recompensa** (5200–5600 u) — Chalé com fonte termal fumegando e bandeira em x5450.
- **Caminhos alternativos:**
  - Pinheiro gêmeo acima da segunda encosta (relíquia), alcançado saltando no topo da rampa.
  - Trilhas de trenó entram num cano coberto de neve: caverna do trenó perdido (relíquia, estrela).
  - Slalom: passar por 6 portões de moedas numa encosta sem tocar as bordas (relíquia).
- **Inimigos permitidos:** `pinguim_patrulha` (Pinguim Patrulheiro), `caracol_cristal` (Caracol-de-Cristal), `coruja_nevada` (Coruja Nevada), `boneco_neve` (Boneco de Neve), `carneiro_glacial` (Carneiro Glacial), `yeti_mirim` (Yeti-Mirim — estreia)
- **Quantidade planejada de inimigos:** 14–18 (chefes não contados)
- **Obstáculos:**
  - encostas onde não se freia
  - vãos de 120–140 u no fim das rampas
  - bolas de neve em arco
  - pinguins e cascos deslizando
  - escada de gelo invertida
- **Itens disponíveis:**
  - crescer: ? x400
  - fogo: ? x1900 (contra yetis)
  - estrela: caverna do trenó
  - coração: chalé intermediário x4300
- **Segredos:**
  - `twin_pine` (high_route) — pista: Dois pinheiros iguais no topo de uma rampa, um com fita vermelha; recompensa: relíquia relic_pine (x1478, y150)
  - `lost_sled` (hidden_area) — pista: Trilhas de trenó que entram num cano coberto de neve e somem; recompensa: relíquia relic_sled (x1188, y850) e estrela
  - `slalom` (optional_challenge) — pista: Bandeiras de slalom vermelhas e azuis com moedas entre elas; recompensa: relíquia relic_slalom (x5150, y220)
- **Colecionáveis:** ~90 moedas e 3 relíquias
- **Checkpoints:** 2
- **Eventos especiais:**
  - message (x2000): Tio Nevasco — “Na encosta não tem freio. Escolha onde pular antes de começar a descer.”
- **Elementos animados:**
  - faíscas de neve nos pés durante a descida
  - Yeti erguendo a bola antes do arremesso
  - bandeiras de slalom tremulando
  - vapor da fonte termal
- **Trilha sonora:** `frozen_peaks_main` — descida: ritmo acelerado de sinos de trenó, baixo saltitante e assobios (sub-áreas: `frozen_peaks_underground`)
- **Condição de conclusão:** Tocar a bandeira em x5450.
- **Critérios de teste:**
  - validate_level e validate_campaign sem erros (schema, espécies, bioma, ordem de introdução, warps com chão)
  - route_bot conclui a fase partindo do spawn e de cada um dos 2 checkpoint(s), com inimigos e perigos ativos
  - vãos obrigatórios ≤ 150 u na mesma altura e subidas obrigatórias ≤ 64 u, simulados nas duas alturas do jogador sem coyote nem buffer
  - as 3 relíquias e todas as moedas são alcançáveis (rota de teste dedicada por relíquia; nenhuma moeda leva a morte)
  - estreias (Yeti-Mirim) em chão plano com ≥ 300 u de aproximação visível, recuo livre e nenhum vão letal a 200 u
  - teto sobre patrulha: nenhum sólido não semissólido com base entre y_chão−158 e y_chão−30 sobre a patrulha de inimigo terrestre a menos de 160 u de um vão obrigatório
  - zona segura de cada checkpoint: chão plano de x−96 a x+192 e nenhum inimigo comum alcança [x−160, x+320] em 3 s de simulação
  - cada vão no fim de rampa é vencível decolando no último degrau com qualquer velocidade ≥ 220 u/s
  - nenhum perigo a menos de 330 u depois do fim de uma encosta sem parede de contenção
  - a encosta invertida é vencível nas duas alturas (degraus ≤ 48 u)
  - o arco do yeti nunca cai sobre um checkpoint
- **Requisitos de motor:** nenhum (implementável com o motor atual)
- **Ajustes sobre a implementação inicial já existente:**
  - Implementação inicial criada a partir deste plano durante a redação (5600×1240, 12 inimigos, checkpoints x2140 e x4800, relíquias relic_pine/relic_slalom/relic_sled).
  - Diferenças aceitas: encostas como terraços descendentes dentro de 540 u de altura (sem área vertical) e caverna do trenó como sala de cano.
  - Pendências do plano: densidade de 12 para 14–18 inimigos (carneiro e segundo yeti na pista final), moedas de 48 para ~90 (trilhas nas rampas e nos portões do slalom) e paredes de neve de contenção ao fim de cada encosta.

### 4-5 · Cume da Avalanche (`avalanche_ridge`)

*Ideia própria:* o corredor da avalanche: quatro bolas gigantes em fases diferentes e abrigos entre elas.

- **Identificador:** `avalanche_ridge`
- **Nome:** Cume da Avalanche
- **Mundo:** Montanhas Geladas (`frozen_peaks`, bioma `snow`), fase 5 de 6 — origem: nova
- **Objetivo:** Desafio avançado: atravessar o cume combinando pingentes que despencam (e cujo topo é seguro), bolas de neve gigantes rolando nos vales, cornijas frágeis sob rajadas e todos os inimigos do frio.
- **Tema visual:** Cumeeira estreita sob céu cinzento, cornijas de neve, cavernas de gelo com pingentes azuis, rochas expostas, bandeiras do Tio Nevasco nos abrigos; estrondos e neve em pó.
- **Mecânica principal:** Pingentes de gelo (crusher: tremem, despencam, viram degrau e se refazem)
- **Mecânicas secundárias:**
  - bolas de neve gigantes rolando (perigo móvel horizontal)
  - cornijas frágeis (crumble) sob rajadas
  - abrigos de pedra
  - todos os inimigos do frio
- **Dificuldade:** 5/10
- **Duração planejada:** 110–220 s (primeira travessia → exploração completa)
- **Tamanho do cenário:** 6000 × 1240 u
  - `main` [snow] 0,0 6000×540: cumeeira, vales com bolas de neve e túnel de gelo
  - `pipe_room_area` [underground] 3369,700 960×540: caverna de cristais (segredo)
- **Caminho principal** (sequência de ensino):
  1. **Introdução** (0–700 u) — Trilha da cumeeira; Pingente de Gelo (estreia) sobre uma saliência plana e segura: treme (0,45 s), despenca, vira degrau por 1,4 s e volta a se formar.
  2. **Demonstração segura** (700–1300 u) — Fileira de três pingentes num corredor com espaço de fuga; usar um pingente caído como degrau até um beiral com moedas.
  3. **Primeiro desafio** (1300–2000 u) — Primeiro vale: bola de neve gigante rolando (perigo móvel, alcance 160 u, velocidade 1,1) — passar no momento em que ela sobe a outra encosta.
  4. **Escalada** (2000–2800 u) — Checkpoint x2000 num abrigo; cornijas frágeis sobre o abismo com rajadas laterais (−100 u/s, período 3,5 s).
  5. **Combinação** (2600–4000 u) — Túnel de gelo: pingentes em teto baixo + pinguins deslizando + caracóis de cristal; luz azul dos cristais.
  6. **Reviravolta** (4000–4700 u) — Corredor da avalanche: encosta longa com quatro bolas gigantes em fases diferentes; a corneta do Tio Nevasco toca 1 s antes de cada uma; abrigos de pedra a cada 200 u.
  7. **Teste final** (4700–5600 u) — Checkpoint x4700; subida ao cume sob pingentes, com yetis arremessando de cima e coruja nas rajadas.
  8. **Recompensa** (5600–6000 u) — Marco do cume com vista da Cidadela de Geada e bandeira em x5850.
- **Caminhos alternativos:**
  - Topo de um pingente refeito leva a um nicho no teto (relíquia do pingente).
  - Cano coberto de geada junto a uma parede rachada com brilho azul → caverna de cristais (relíquia, estrela).
  - Rota alta sobre o corredor da avalanche, por beirais estreitos (relíquia).
- **Inimigos permitidos:** `pinguim_patrulha` (Pinguim Patrulheiro), `caracol_cristal` (Caracol-de-Cristal), `coruja_nevada` (Coruja Nevada), `boneco_neve` (Boneco de Neve), `carneiro_glacial` (Carneiro Glacial), `yeti_mirim` (Yeti-Mirim), `pingente_queda` (Pingente de Gelo — estreia)
- **Quantidade planejada de inimigos:** 18–24 (chefes não contados)
- **Obstáculos:**
  - pingentes que despencam
  - bolas de neve gigantes (perigo móvel)
  - cornijas frágeis sobre o abismo
  - rajadas laterais
  - arremessos em arco
- **Itens disponíveis:**
  - crescer: ? x500
  - fogo: ? x2100
  - estrela: caverna secreta
  - coração: abrigo do checkpoint 2
- **Segredos:**
  - `icicle_niche` (hidden_area) — pista: Moedas num nicho do teto, só alcançável usando o pingente caído como degrau; recompensa: relíquia relic_icicle (x690, y228)
  - `crystal_cave` (hidden_area) — pista: Brilho azul atravessando rachaduras perto de um cano coberto de geada; recompensa: relíquia relic_crystal (x3878, y850) e estrela
  - `avalanche_ledges` (high_route) — pista: Beirais estreitos com a bandeira do Tio Nevasco acima do corredor; recompensa: relíquia relic_avalanche (x4500, y170)
- **Colecionáveis:** ~95 moedas e 3 relíquias
- **Checkpoints:** 2
- **Eventos especiais:**
  - message (x2000): Tio Nevasco — “Ouviu a corneta? Procure a pedra grande.”
  - camera_lock (opcional) no corredor da avalanche para mostrar as quatro bolas
- **Elementos animados:**
  - pingentes tremendo e se refazendo
  - bolas de neve rolando com rastro de pó
  - cornijas desmoronando
  - cristais pulsando na caverna
- **Trilha sonora:** `frozen_peaks_main` — tensão no cume: ostinato de cordas, tímpanos nos estrondos e corneta como aviso (sub-áreas: `frozen_peaks_underground`)
- **Condição de conclusão:** Tocar a bandeira em x5850.
- **Critérios de teste:**
  - validate_level e validate_campaign sem erros (schema, espécies, bioma, ordem de introdução, warps com chão)
  - route_bot conclui a fase partindo do spawn e de cada um dos 2 checkpoint(s), com inimigos e perigos ativos
  - vãos obrigatórios ≤ 150 u na mesma altura e subidas obrigatórias ≤ 64 u, simulados nas duas alturas do jogador sem coyote nem buffer
  - as 3 relíquias e todas as moedas são alcançáveis (rota de teste dedicada por relíquia; nenhuma moeda leva a morte)
  - estreias (Pingente de Gelo) em chão plano com ≥ 300 u de aproximação visível, recuo livre e nenhum vão letal a 200 u
  - teto sobre patrulha: nenhum sólido não semissólido com base entre y_chão−158 e y_chão−30 sobre a patrulha de inimigo terrestre a menos de 160 u de um vão obrigatório
  - zona segura de cada checkpoint: chão plano de x−96 a x+192 e nenhum inimigo comum alcança [x−160, x+320] em 3 s de simulação
  - o topo de cada pingente é seguro (safe_top) e nenhum pingente cai sobre um checkpoint
  - cada bola de neve gigante tem aviso sonoro ≥ 1 s e abrigo a ≤ 200 u
  - estreia do pingente em chão plano sem vão em 200 u
  - o bot conclui a fase partindo dos 2 checkpoints
- **Requisitos de motor:** nenhum (implementável com o motor atual)
- **Ajustes sobre a implementação inicial já existente:**
  - Implementação inicial criada a partir deste plano durante a redação (6000×1240, 16 inimigos, checkpoints x2160 e x4930, rajada x2360–2960 com período 3,5 s, cinco bolas de neve gigantes como perigos móveis, relíquias relic_icicle/relic_crystal/relic_avalanche).
  - Diferenças aceitas: caverna de cristais como sala de cano (sem área vertical) e túnel de gelo na área principal.
  - Pendências do plano: aviso sonoro (corneta) ≥ 1 s antes de cada bola de neve do corredor, abrigos de pedra a cada 200 u no corredor da avalanche e moedas de 46 para ~95.

### 4-6 · Cidadela de Geada (`frost_citadel`)

*Ideia própria:* no salão dos vitrais a luz colorida marca o gelo que não escorrega.

- **Identificador:** `frost_citadel`
- **Nome:** Cidadela de Geada
- **Mundo:** Montanhas Geladas (`frozen_peaks`, bioma `snow`), fase 6 de 6 — origem: nova
- **Objetivo:** Fortaleza das Montanhas Geladas: atravessar a cidadela de gelo combinando gelo, pingentes, nevasca pelas janelas e pontes frágeis que se refazem, e derrotar a Morsa Gelomar chutando cascos de cristal no gelo.
- **Tema visual:** Cidadela de gelo translúcido e granito com vitrais de gelo colorido, lustres de pingentes, estandartes azuis congelados, aurora boreal visível pelas janelas; salão do trono com piso de gelo espelhado.
- **Mecânica principal:** Pisos alternando gelo e rocha marcados por luz de vitral (rocha = faixas coloridas no chão)
- **Mecânicas secundárias:**
  - nevasca entrando pelas janelas (wind com período)
  - pontes de gelo frágeis que se refazem
  - lustres de pingentes (crusher)
  - carneiros investindo no gelo
  - chefe planejado Morsa Gelomar
- **Dificuldade:** 5/10
- **Duração planejada:** 150–300 s (primeira travessia → exploração completa)
- **Tamanho do cenário:** 6400 × 1620 u
  - `main` [snow] 0,0 1400×540: portão e ponte levadiça de gelo
  - `citadel` [fortress] 1400,0 4000×1620: salões, torres e masmorras de gelo
  - `throne` [fortress] 5400,0 1000×1080: salão do trono (arena)
- **Caminho principal** (sequência de ensino):
  1. **Introdução** (0–700 u) — Portão da cidadela: ponte levadiça de gelo (plataformas frágeis que se refazem) sobre fosso congelado raso (sem morte), carneiro de guarda com bloco de granito.
  2. **Demonstração segura** (700–1400 u) — Pátio: lustre de pingentes sobre chão de rocha (demonstração do perigo vindo de cima no novo ambiente).
  3. **Primeiro desafio** (1400–2200 u) — Salão dos vitrais: faixas de luz colorida marcam onde o piso é rocha; o resto é gelo; pinguins e caracóis.
  4. **Escalada** (2200–3000 u) — Checkpoint x2200; corredor das janelas: rajadas de nevasca alternadas (lado esquerdo/direito) sobre pontes de gelo frágeis.
  5. **Combinação** (3000–3800 u) — Torre vertical: subir por beirais com yetis nos patamares e corujas; pingentes no teto da torre.
  6. **Reviravolta** (3800–4600 u) — Masmorra de gelo: descer por poços com bolas de neve gigantes rolando em corredores e carneiros que batem nas grades.
  7. **Teste final** (4600–5400 u) — Checkpoint x4700 na antessala com coração; o Tio Nevasco avisa sobre o elmo da morsa.
  8. **Recompensa** (5400–6400 u) — Salão do trono: Morsa Gelomar (5 PV); vitória derrete o gelo do trono e revela a fonte-farol; bandeira em x6250.
- **Caminhos alternativos:**
  - Rota dos telhados: beirais sobre o salão dos vitrais (relíquia do vitral).
  - Cripta atrás de gelo rachado (requer paredes quebráveis; alternativa com tijolos) (relíquia).
  - Torre do sino: desafio cronometrado com pontes frágeis (relíquia).
- **Inimigos permitidos:** `pinguim_patrulha` (Pinguim Patrulheiro), `caracol_cristal` (Caracol-de-Cristal), `coruja_nevada` (Coruja Nevada), `boneco_neve` (Boneco de Neve), `carneiro_glacial` (Carneiro Glacial), `yeti_mirim` (Yeti-Mirim), `pingente_queda` (Pingente de Gelo), `morsa_gelomar` (Morsa Gelomar — estreia)
- **Quantidade planejada de inimigos:** 18–24 (chefes não contados)
- **Obstáculos:**
  - gelo e rocha alternados
  - rajadas pelas janelas
  - pontes frágeis
  - lustres de pingentes
  - bolas de neve gigantes
- **Itens disponíveis:**
  - crescer: ? x500
  - fogo: ? x2300
  - estrela: cripta
  - coração: antessala x4750
- **Segredos:**
  - `stained_roof` (high_route) — pista: Um vitral com o desenho de uma estrela aponta para o telhado; moedas brilham através do vidro; recompensa: relíquia relic_window
  - `ice_crypt` (breakable_path) — pista: Gelo rachado com bolhas de ar presas formando uma seta; recompensa: relíquia relic_crypt e estrela
  - `bell_tower` (optional_challenge) — pista: Sino de gelo tocando sozinho no alto da torre; recompensa: relíquia relic_bell
- **Colecionáveis:** ~95 moedas e 3 relíquias
- **Checkpoints:** 2
- **Eventos especiais:**
  - boss_arena (x5400): trava a câmera no salão do trono e fecha o portão de gelo
  - message (x4700): Tio Nevasco — “A morsa tem elmo de gelo. Casco de cristal, ou três chamas, racha aquilo.”
- **Elementos animados:**
  - vitrais projetando luz colorida no chão
  - aurora pelas janelas
  - lustres de pingentes balançando
  - elmo de gelo da morsa rachando
- **Trilha sonora:** `frozen_peaks_fortress` — cidadela: órgão de vidro, coro distante e tímpanos; tema do chefe em valsa sombria (sub-áreas: `frozen_peaks_underground`, `frozen_peaks_boss`)
- **Condição de conclusão:** Derrotar a Morsa Gelomar (5 PV) e tocar a bandeira em x6250.
- **Critérios de teste:**
  - validate_level e validate_campaign sem erros (schema, espécies, bioma, ordem de introdução, warps com chão)
  - route_bot conclui a fase partindo do spawn e de cada um dos 2 checkpoint(s), com inimigos e perigos ativos
  - vãos obrigatórios ≤ 150 u na mesma altura e subidas obrigatórias ≤ 64 u, simulados nas duas alturas do jogador sem coyote nem buffer
  - as 3 relíquias e todas as moedas são alcançáveis (rota de teste dedicada por relíquia; nenhuma moeda leva a morte)
  - teto sobre patrulha: nenhum sólido não semissólido com base entre y_chão−158 e y_chão−30 sobre a patrulha de inimigo terrestre a menos de 160 u de um vão obrigatório
  - zona segura de cada checkpoint: chão plano de x−96 a x+192 e nenhum inimigo comum alcança [x−160, x+320] em 3 s de simulação
  - as faixas de luz coincidem exatamente com os trechos de rocha (surface normal)
  - a arena sempre oferece um caracol de cristal disponível em ≤ 6 s
  - o bot vence o chefe partindo do checkpoint da antessala
  - nenhuma rajada cobre vão sem plataforma de apoio a ≤ 150 u
- **Requisitos de motor:** 
  - não bloqueia — breakable walls: paredes quebráveis por casco, fogo ou investida (segredos) (só para o segredo da cripta)

## Mundo 5 — Floresta Encantada (`enchanted_forest`)

Copas luminosas, ruínas e raízes antigas. A floresta se lê em camadas e disfarces: copas, ruínas e raízes escondem blocos, inimigos camuflados e uma lagarta que vira mariposa. Detalhes do mundo em [`MUNDO_05.md`](MUNDO_05.md).

### 5-1 · Copas Luminosas (`glowing_canopy`)

*Ideia própria:* Ciranda revela um caminho de blocos ocultos entre as copas.

- **Identificador:** `glowing_canopy`
- **Nome:** Copas Luminosas
- **Mundo:** Floresta Encantada (`enchanted_forest`, bioma `forest`), fase 1 de 6 — origem: legada 4-1
- **Objetivo:** Apresentar a floresta em camadas — chão contínuo por trechos e copas de folhas frágeis — e quatro moradores, cada um em seu trecho; a terceira relíquia ensina a seguir os vagalumes.
- **Tema visual:** Floresta clara com copas em três alturas, cogumelos luminosos, flores-lanterna penduradas, samambaias gigantes e raios de sol entre as folhas; vagalumes em pleno dia.
- **Mecânica principal:** Copas de folhas frágeis em três alturas (crumble) acima de um chão contínuo por trechos
- **Mecânicas secundárias:**
  - Cogumelo Saltitante (agacha antes de saltar)
  - Planta-de-Esporos (nuvem em linha reta)
  - Mariposa-Lume (voo em ondas rápidas)
  - Caracol-Musgo (recolhido parece pedra musgosa)
  - blocos ocultos marcados por vagalumes
- **Dificuldade:** 5/10
- **Duração planejada:** 70–150 s (primeira travessia → exploração completa)
- **Tamanho do cenário:** 4000 × 1240 u
  - `main` [forest] 0,0 4000×540: chão em quatro trechos (vãos de 110–120 u) e copas acima
  - `pipe_room_area` [underground] 2999,700 960×540: câmara secreta
- **Caminho principal** (sequência de ensino):
  1. **Introdução** (0–420 u) — Chão de folhas; ? de crescer x350; dica 'Siga o chão ou aventure-se pelas copas'.
  2. **Demonstração segura** (420–980 u) — Cogumelo Saltitante (estreia, proposto [420, 560]): agacha visivelmente e salta na direção de Lume; folhas frágeis x750/x916 (relíquia alta) sobre chão contínuo.
  3. **Primeiro desafio** (980–1600 u) — Vão de 110 u; Planta-de-Esporos (estreia) em x1320, 230 u depois do pouso: incha e cospe esporos em linha reta — saltar a nuvem ou pisar a planta; ? de fogo x1490.
  4. **Escalada** (1600–2170 u) — Tijolo x1600, plataforma móvel x1770; checkpoint x1950; vão de 120 u.
  5. **Combinação** (2170–2810 u) — Bloco oculto marcado por vagalumes (x2300) → degrau → relíquia de Ciranda; espinhos x2400; Mariposa-Lume (estreia) em voo rápido [2450, 2710].
  6. **Reviravolta** (2930–3450 u) — Caracol-Musgo (estreia, proposto [3250, 3450]): recolhido parece uma pedra musgosa — o jogador aprende que 'pedra' pode ser casco e o chuta.
  7. **Teste final** (3160–3700 u) — Cano da câmara x3160; ? de coração x3560; mariposa + cogumelo juntos antes da chegada.
  8. **Recompensa** (3700–4000 u) — Bandeira em x3850 sob um arco de cogumelos luminosos.
- **Caminhos alternativos:**
  - Copas de folhas frágeis x750 → x916 (relíquia alta x949, y220).
  - Blocos ocultos de Ciranda x2300 (relíquia dos vagalumes).
  - Cano x3160 → câmara (relíquia, estrela).
- **Inimigos permitidos:** `bolota` (Bolota), `caramujo` (Caramujo-de-Casca), `besouro_alado` (Besouro-Asa), `besouro` (Besouro), `cogumelo_saltitante` (Cogumelo Saltitante — estreia), `caracol_musgo` (Caracol-Musgo — estreia), `mariposa_lume` (Mariposa-Lume — estreia), `planta_esporos` (Planta-de-Esporos — estreia)
- **Quantidade planejada de inimigos:** 6–8 (chefes não contados)
- **Obstáculos:**
  - folhas frágeis
  - 3 vãos de 110–120 u
  - espinhos x2400
  - esporos em linha reta
- **Itens disponíveis:**
  - crescer: ? x350
  - fogo: ? x1490
  - coração: ? x3560
  - estrela: câmara x3458
- **Segredos:**
  - `high_route` (high_route) — pista: Trilha de moedas sobe pelas folhas frágeis; recompensa: relíquia relic_high (x949, y220)
  - `firefly_steps` (hidden_block) — pista: Vagalumes se reúnem num ponto vazio sobre o chão em x2300 (Ciranda pousa ali depois do checkpoint); recompensa: relíquia relic_firefly (x2360, y260)
  - `pipe_room` (warp_room) — pista: Cano com seta luminosa entre samambaias; recompensa: relíquia relic_room (x3508, y850) e estrela
- **Colecionáveis:** ~50 moedas e 3 relíquias
- **Checkpoints:** 1
- **Eventos especiais:**
  - message (x1950): Ciranda — “Onde a luz se junta, há chão invisível.”
- **Elementos animados:**
  - folhas frágeis tremendo e caindo em espiral
  - cogumelos luminosos pulsando
  - vagalumes seguindo Ciranda até o segredo
  - raios de sol varrendo devagar
- **Trilha sonora:** `enchanted_forest_main` — copas: harpa, flauta doce e sinos de madeira em compasso leve (sub-áreas: `enchanted_forest_underground`)
- **Condição de conclusão:** Tocar a bandeira em x3850.
- **Critérios de teste:**
  - validate_level e validate_campaign sem erros (schema, espécies, bioma, ordem de introdução, warps com chão)
  - route_bot conclui a fase partindo do spawn e de cada um dos 1 checkpoint(s), com inimigos e perigos ativos
  - vãos obrigatórios ≤ 150 u na mesma altura e subidas obrigatórias ≤ 64 u, simulados nas duas alturas do jogador sem coyote nem buffer
  - as 3 relíquias e todas as moedas são alcançáveis (rota de teste dedicada por relíquia; nenhuma moeda leva a morte)
  - estreias (Cogumelo Saltitante, Caracol-Musgo, Mariposa-Lume, Planta-de-Esporos) em chão plano com ≥ 300 u de aproximação visível, recuo livre e nenhum vão letal a 200 u
  - teto sobre patrulha: nenhum sólido não semissólido com base entre y_chão−158 e y_chão−30 sobre a patrulha de inimigo terrestre a menos de 160 u de um vão obrigatório
  - zona segura de cada checkpoint: chão plano de x−96 a x+192 e nenhum inimigo comum alcança [x−160, x+320] em 3 s de simulação
  - as quatro estreias ficam em trechos separados por ≥ 600 u e cada uma em chão plano com recuo
  - teto sobre patrulha: nenhum inimigo terrestre sob folha frágil a menos de 160 u de um vão
  - o bloco oculto de x2300 só é sugerido por vagalumes (pista visível em qualquer resolução)
  - folhas frágeis nunca são necessárias para o caminho principal
- **Requisitos de motor:** nenhum (implementável com o motor atual)
- **Plano de melhoria da fase legada:**
  - Mantidos: quatro trechos de chão, folhas frágeis em três alturas, plataforma móvel e câmara.
  - Exceção do registro: quatro estreias (cogumelo, planta, mariposa, caracol-musgo) — o plano as separa em trechos de ≥ 600 u; ver ajuste proposto (planta para firefly_ruins e cogumelo para ancestral_tree).
  - Caracol-Musgo: [760, 920] → [3250, 3450]; hoje fica sob a folha frágil x750–852 (base y330) a 60 u do vão.
  - Cogumelo Saltitante: nova patrulha [420, 560] (primeiro inimigo, 348 u após o spawn).
  - Terceira relíquia: bloco oculto marcado por vagalumes (x2300, y340) → degrau → relíquia (x2360, y260).
  - Arte: cogumelos luminosos, flores-lanterna, samambaias, raios de sol (camada atmosfera).

### 5-2 · Ruínas dos Vagalumes (`firefly_ruins`)

*Ideia própria:* a hera esconde um salão inteiro onde os vagalumes entram e não saem.

- **Identificador:** `firefly_ruins`
- **Nome:** Ruínas dos Vagalumes
- **Mundo:** Floresta Encantada (`enchanted_forest`, bioma `forest`), fase 2 de 6 — origem: legada 4-2
- **Objetivo:** Explorar ruínas cobertas de musgo onde os vagalumes marcam blocos ocultos, enfrentar o Besouro-Casca (blindado, 2 golpes) em chão aberto e achar três segredos de tipos diferentes.
- **Tema visual:** Ruínas de pedra cinza-esverdeada com colunas tombadas, arcos cobertos de hera, escadarias quebradas, salão de canos antigos e vagalumes ao entardecer.
- **Mecânica principal:** Blocos ocultos marcados por vagalumes e escadarias de ruína
- **Mecânicas secundárias:**
  - Besouro-Casca (blindado, 2 golpes, lento)
  - folhas frágeis e chama oscilante
  - plataforma móvel
  - cortina de hera (decor frontal) escondendo passagem
- **Dificuldade:** 5/10
- **Duração planejada:** 80–170 s (primeira travessia → exploração completa)
- **Tamanho do cenário:** 4500 × 1240 u
  - `main` [forest] 0,0 4500×540: ruínas em cinco trechos (vãos de 120 u, desníveis ±32/±48 u)
  - `pipe_room_area` [underground] 1649,700 960×540: salão de canos
- **Caminho principal** (sequência de ensino):
  1. **Introdução** (0–740 u) — Pátio da ruína; ? de crescer x350; dica 'Há blocos invisíveis onde as luzes se reúnem'; cogumelo proposto em [400, 560].
  2. **Demonstração segura** (740–1450 u) — Subida de 32 u; tijolos x900 → x1110 e bloco oculto x1040 (estrela) onde os vagalumes se reúnem — a demonstração do mundo.
  3. **Primeiro desafio** (1570–2160 u) — Descida de 32 u; Besouro-Casca (estreia, proposto [1860, 2060]) em chão aberto depois do cano: dois pisões ou fogo.
  4. **Escalada** (2160–2760 u) — Checkpoint x2320; blocos ? x2220/x2300; folha frágil x2500; vão de 120 u subindo 48 u.
  5. **Combinação** (2760–3400 u) — Terraço com Planta-de-Esporos em x2990 e plataforma móvel x3120 com chama oscilante x3190: esporos + chama + plataforma.
  6. **Reviravolta** (3400–3520 u) — Cortina de hera: vagalumes entram nela e não saem do outro lado — atrás há um salão escondido (relíquia).
  7. **Teste final** (3500–4300 u) — 2º checkpoint proposto x3500; tijolos x3590/x3910 e folha frágil x3750; mariposa e besouro alado no alto.
  8. **Recompensa** (4300–4500 u) — Bandeira em x4350 diante de um arco de pedra iluminado.
- **Caminhos alternativos:**
  - Tijolos x900 → x1110 (relíquia alta x1142, y238).
  - Salão atrás da cortina de hera x3400–3520 (relíquia da hera).
  - Cano x1790 → salão de canos (relíquia, fogo).
- **Inimigos permitidos:** `bolota` (Bolota), `caramujo` (Caramujo-de-Casca), `besouro_alado` (Besouro-Asa), `besouro` (Besouro), `cogumelo_saltitante` (Cogumelo Saltitante), `caracol_musgo` (Caracol-Musgo), `mariposa_lume` (Mariposa-Lume), `planta_esporos` (Planta-de-Esporos), `besouro_casca` (Besouro-Casca — estreia), `ourico_espinho` (Ouriço-Espinho)
- **Quantidade planejada de inimigos:** 9–11 (chefes não contados)
- **Obstáculos:**
  - 4 vãos de 120 u com desníveis ±32/±48 u
  - folhas frágeis
  - chama oscilante x3190
  - esporos
- **Itens disponíveis:**
  - crescer: ? x350
  - moeda: ? x2220
  - coração: ? x2300
  - estrela: bloco oculto x1040
  - fogo: salão de canos x2108
- **Segredos:**
  - `high_route` (high_route) — pista: Trilha de moedas sobe pelos tijolos; recompensa: relíquia relic_high (x1142, y238)
  - `ivy_hall` (hidden_area) — pista: Vagalumes entram na cortina de hera e não saem do outro lado; recompensa: relíquia relic_ivy
  - `pipe_room` (warp_room) — pista: O cano revela um salão entre as ruínas (dica existente); recompensa: relíquia relic_room (x2158, y850) e fogo
  - `hidden_hidden01` (hidden_block) — pista: Moedas e luzes convergem para um ponto vazio no ar (x1040); recompensa: estrela
- **Colecionáveis:** ~55 moedas e 3 relíquias
- **Checkpoints:** 2
- **Eventos especiais:**
  - message (x2320): Ciranda — “Siga as luzes: elas sabem onde o chão se esconde.”
- **Elementos animados:**
  - vagalumes em enxame convergindo
  - hera balançando em primeiro plano
  - chama oscilante com faíscas
  - besouro-casca soltando lascas a cada golpe
- **Trilha sonora:** `enchanted_forest_main` — entardecer nas ruínas: celesta, coro sem palavras e pizzicato (sub-áreas: `enchanted_forest_underground`)
- **Condição de conclusão:** Tocar a bandeira em x4350.
- **Critérios de teste:**
  - validate_level e validate_campaign sem erros (schema, espécies, bioma, ordem de introdução, warps com chão)
  - route_bot conclui a fase partindo do spawn e de cada um dos 2 checkpoint(s), com inimigos e perigos ativos
  - vãos obrigatórios ≤ 150 u na mesma altura e subidas obrigatórias ≤ 64 u, simulados nas duas alturas do jogador sem coyote nem buffer
  - as 3 relíquias e todas as moedas são alcançáveis (rota de teste dedicada por relíquia; nenhuma moeda leva a morte)
  - estreias (Besouro-Casca) em chão plano com ≥ 300 u de aproximação visível, recuo livre e nenhum vão letal a 200 u
  - teto sobre patrulha: nenhum sólido não semissólido com base entre y_chão−158 e y_chão−30 sobre a patrulha de inimigo terrestre a menos de 160 u de um vão obrigatório
  - zona segura de cada checkpoint: chão plano de x−96 a x+192 e nenhum inimigo comum alcança [x−160, x+320] em 3 s de simulação
  - estreia do Besouro-Casca em chão plano com ≥ 300 u de aproximação e recuo
  - a cortina de hera nunca esconde perigo nem o jogador por mais de 1 s fora do segredo
  - teto sobre patrulha corrigido no trecho x1110–1450
  - zona segura dos 2 checkpoints livre
- **Requisitos de motor:** nenhum (implementável com o motor atual)
- **Plano de melhoria da fase legada:**
  - Mantidos: cinco trechos, bloco oculto x1040, salão de canos, plataforma móvel e chama.
  - Besouro-Casca: [1200, 1380] → [1860, 2060]; hoje estreia sob o tijolo02 (base y300) a 70 u do vão — a estreia de um blindado precisa de chão aberto.
  - 2º checkpoint em x3500 (chão plano x3404–3692).
  - Densidade: de 3 para 9–11 inimigos (cogumelos, caracol-musgo, bolota, besouro-asa).
  - Terceira relíquia: salão atrás da cortina de hera (x3400–3520).
  - Arte: colunas tombadas, hera em primeiro plano (camada front com alfa limitado), vagalumes.

### 5-3 · A Árvore Ancestral (`ancestral_tree`)

*Ideia própria:* a segunda subida pelos cogumelos-mola leva à copa acima de tudo.

- **Identificador:** `ancestral_tree`
- **Nome:** A Árvore Ancestral
- **Mundo:** Floresta Encantada (`enchanted_forest`, bioma `forest`), fase 3 de 6 — origem: legada 4-3
- **Objetivo:** Desafio de movimento: duas subidas distintas pela Árvore Ancestral — blocos e plataformas na primeira, chapéus de cogumelo-mola na segunda, até a copa — e o Guardião da Árvore (6 PV).
- **Tema visual:** Tronco colossal com casca em placas, raízes em arco formando pontes, cogumelos de prateleira, cristais nas raízes, luz dourada; guardião de raízes e cristais.
- **Mecânica principal:** Subidas verticais curtas por blocos, plataformas móveis e chapéus de cogumelo-mola (spring)
- **Mecânicas secundárias:**
  - folha frágil
  - plataformas móveis (x e y)
  - rota da copa
  - chefe intermediário guardiao_arvore
- **Dificuldade:** 6/10
- **Duração planejada:** 90–180 s (primeira travessia → exploração completa)
- **Tamanho do cenário:** 4700 × 1240 u
  - `main` [forest] 0,0 4700×540: cinco trechos ao pé da árvore, copa em y≈100–220 e arena x3980–4470
  - `pipe_room_area` [underground] 2399,700 960×540: câmara entre as raízes
- **Caminho principal** (sequência de ensino):
  1. **Introdução** (0–820 u) — Raízes externas; ? de crescer x340; tijolo x510 e folha frágil x680 (primeira subida curta).
  2. **Demonstração segura** (940–1630 u) — Besouro-Casca em [1040, 1250]; ? de fogo x1290 e moeda x1370.
  3. **Primeiro desafio** (1750–2790 u) — Primeira subida: tijolo x1850 → plataforma móvel x2010 → tijolo x2190 (relíquia alta); mariposa em [2020, 2330]; checkpoint x2460; cano x2590.
  4. **Escalada** (1750–2790 u (copa)) — Segunda subida: cogumelos-mola (propostos em x1800, x2050, x2300) levam a galhos semissólidos em y220 → y160 até a copa (relíquia da copa).
  5. **Combinação** (2910–3530 u) — Espinhos x3100, planta (proposta x3200, fora da sombra da plataforma móvel) e plataforma vertical x3380.
  6. **Reviravolta** (3530–3650 u) — Vão de 120 u entre raízes; cogumelos saltitantes na raiz-ponte.
  7. **Teste final** (3650–3980 u) — 2º checkpoint proposto x3760 com coração (? x3770); dica 'Observe o guardião e escolha sua abertura'.
  8. **Recompensa** (3980–4700 u) — Arena: Guardião da Árvore (6 PV); vitória libera a bandeira em x4550.
- **Caminhos alternativos:**
  - Primeira subida pelos blocos (relíquia alta x2232, y224).
  - Segunda subida pelos cogumelos-mola até a copa (relíquia da copa).
  - Cano x2590 → câmara (relíquia, estrela).
- **Inimigos permitidos:** `bolota` (Bolota), `caramujo` (Caramujo-de-Casca), `besouro_alado` (Besouro-Asa), `besouro` (Besouro), `cogumelo_saltitante` (Cogumelo Saltitante), `caracol_musgo` (Caracol-Musgo), `mariposa_lume` (Mariposa-Lume), `planta_esporos` (Planta-de-Esporos), `besouro_casca` (Besouro-Casca), `ourico_espinho` (Ouriço-Espinho), `guardiao_arvore` (Guardião da Árvore — estreia)
- **Quantidade planejada de inimigos:** 9–12 (chefes não contados)
- **Obstáculos:**
  - 4 vãos de 120 u
  - espinhos x3100
  - folha frágil
  - esporos e esferas do guardião
- **Itens disponíveis:**
  - crescer: ? x340
  - fogo: ? x1290
  - moeda: ? x1370
  - coração: ? x3770
  - estrela: câmara x2858
  - fogo: chão x3870
- **Segredos:**
  - `high_route` (high_route) — pista: Ganhe altura para alcançar a relíquia (dica existente); moedas pelos blocos; recompensa: relíquia relic_high (x2232, y224)
  - `crown_route` (high_route) — pista: Cogumelos de chapéu vermelho com pintas brilhantes formam uma escada até a copa; recompensa: relíquia relic_crown (x2700, y110)
  - `pipe_room` (warp_room) — pista: Cano entre raízes com seta luminosa; recompensa: relíquia relic_room (x2908, y850) e estrela
- **Colecionáveis:** ~55 moedas e 3 relíquias
- **Checkpoints:** 2
- **Eventos especiais:**
  - message (x2460): Ciranda — “A árvore oferece dois caminhos para a mesma luz.”
- **Elementos animados:**
  - folhas da copa balançando
  - cogumelos-mola comprimindo
  - cristais nas raízes pulsando
  - guardião de raízes abrindo a guarda
- **Trilha sonora:** `enchanted_forest_main` — tronco ancestral: violoncelo, marimba de madeira e coro; percussão de tambor de toras na arena (sub-áreas: `enchanted_forest_underground`)
- **Condição de conclusão:** Derrotar o Guardião da Árvore (6 PV) e tocar a bandeira em x4550.
- **Critérios de teste:**
  - validate_level e validate_campaign sem erros (schema, espécies, bioma, ordem de introdução, warps com chão)
  - route_bot conclui a fase partindo do spawn e de cada um dos 2 checkpoint(s), com inimigos e perigos ativos
  - vãos obrigatórios ≤ 150 u na mesma altura e subidas obrigatórias ≤ 64 u, simulados nas duas alturas do jogador sem coyote nem buffer
  - as 3 relíquias e todas as moedas são alcançáveis (rota de teste dedicada por relíquia; nenhuma moeda leva a morte)
  - teto sobre patrulha: nenhum sólido não semissólido com base entre y_chão−158 e y_chão−30 sobre a patrulha de inimigo terrestre a menos de 160 u de um vão obrigatório
  - zona segura de cada checkpoint: chão plano de x−96 a x+192 e nenhum inimigo comum alcança [x−160, x+320] em 3 s de simulação
  - as duas subidas reencontram o caminho principal sem queda cega > 220 u
  - os cogumelos-mola funcionam com e sem segurar o salto
  - teto sobre patrulha: planta e besouro sem sólido baixo perto de vãos
  - a bandeira só conclui após a derrota do guardião
- **Requisitos de motor:** nenhum (implementável com o motor atual)
- **Plano de melhoria da fase legada:**
  - Mantidos: cinco trechos, vãos de 120 u, guardião com 6 PV e câmara.
  - Planta-de-Esporos: x3290 → x3200, fora da sombra da plataforma vertical x3380 (o salto sobre ela batia na plataforma a 110 u do vão).
  - Segunda subida pela copa com cogumelos-mola (spring) e galhos semissólidos; relíquia da copa (x2700, y110).
  - 2º checkpoint em x3760 (o guardião fica restrito à arena a partir de x3980).
  - Densidade: de 4 para 9–12 inimigos (cogumelos, caracol-musgo, besouro-asa, ouriço).

### 5-4 · Pontes de Cipó (`vine_bridges`)

*Ideia própria:* a ponte em espiral desce em volta de um tronco gigante.

- **Identificador:** `vine_bridges`
- **Nome:** Pontes de Cipó
- **Mundo:** Floresta Encantada (`enchanted_forest`, bioma `forest`), fase 4 de 6 — origem: nova
- **Objetivo:** Mecânica especial da Floresta Encantada: atravessar uma ravina por assentos de cipó que balançam e pontes de tábuas frágeis, e conhecer o Arbusto-Espreita, que parece um arbusto até abrir os olhos.
- **Tema visual:** Ravina profunda com névoa, pontes de cipó e tábuas, assentos de cipó pendurados de galhos enormes, troncos com escadas de fungos, vila de casas na árvore no fim; luz verde-dourada.
- **Mecânica principal:** Assentos de cipó balançando (moving eixo x, alcance 60–90 u, velocidade 1,2) e pontes de tábuas frágeis que se refazem
- **Mecânicas secundárias:**
  - Arbusto-Espreita (camuflado; olhos amarelos, sacode e investe após 0,6 s)
  - pontes semissólidas que balançam (moving eixo y pequeno)
  - fosso de musgo raso (não letal) nas demonstrações
  - flores-mordedoras em vasos nos postes
- **Dificuldade:** 5/10
- **Duração planejada:** 100–200 s (primeira travessia → exploração completa)
- **Tamanho do cenário:** 5800 × 2160 u
  - `main` [forest] 0,0 5800×1620: ravina com pontes em y≈450, espiral descendente até y≈1200 e subida final
  - `trunk_room` [underground] 3200,1620 960×540: sala interna do tronco gigante (warp pelo nó)
- **Caminho principal** (sequência de ensino):
  1. **Introdução** (0–700 u) — Borda da floresta; um assento de cipó balançando sobre chão firme (pular nele e descer sem risco).
  2. **Demonstração segura** (700–1300 u) — Dois assentos sobre um fosso de musgo raso (não letal: cair leva a degraus de saída).
  3. **Primeiro desafio** (1300–2000 u) — Arbusto-Espreita (estreia) entre arbustos decorativos em chão plano: olhos abrem, folhas sacodem (0,6 s) e ele investe — pular e pisar fora da investida.
  4. **Escalada** (2000–2800 u) — Checkpoint x2000; ponte de tábuas frágeis sobre a ravina (letal) alternando com assentos de cipó.
  5. **Combinação** (2800–3600 u) — Assentos + mariposas + flores-mordedoras nos vasos dos postes: ritmo de balanço + emergência.
  6. **Reviravolta** (3600–4300 u) — Ponte em espiral descendente em volta de um tronco gigante: cada volta passa sob a anterior; arbustos-espreita nas tábuas.
  7. **Teste final** (4300–5300 u) — Checkpoint x4300; cadeia longa de assentos em fases alternadas sobre a ravina com besouros-asa.
  8. **Recompensa** (5300–5800 u) — Vila de casas na árvore e bandeira em x5650.
- **Caminhos alternativos:**
  - Ninho no cipó mais alto, saltando do topo do balanço (relíquia).
  - Oco do tronco gigante por um nó (cano) → sala interna (relíquia).
  - A ponte inteira: 600 u de tábuas frágeis sem parar, com rede de segurança abaixo (relíquia).
- **Inimigos permitidos:** `bolota` (Bolota), `caramujo` (Caramujo-de-Casca), `besouro_alado` (Besouro-Asa), `besouro` (Besouro), `flor_mordedora` (Flor-Mordedora), `ourico_espinho` (Ouriço-Espinho), `cogumelo_saltitante` (Cogumelo Saltitante), `caracol_musgo` (Caracol-Musgo), `mariposa_lume` (Mariposa-Lume), `planta_esporos` (Planta-de-Esporos), `besouro_casca` (Besouro-Casca), `arbusto_espreita` (Arbusto-Espreita — estreia)
- **Quantidade planejada de inimigos:** 16–22 (chefes não contados)
- **Obstáculos:**
  - assentos de cipó balançando sobre a ravina
  - tábuas frágeis
  - investida do arbusto
  - flores nos vasos
  - ravina letal
- **Itens disponíveis:**
  - crescer: ? x400
  - fogo: ? x2100
  - estrela: sala do tronco
  - coração: checkpoint 2
- **Segredos:**
  - `vine_nest` (high_route) — pista: Ninho com ovo dourado no cipó mais alto, visível no topo do balanço; recompensa: relíquia relic_nest
  - `trunk_knot` (warp_room) — pista: Nó do tronco em forma de olho com vagalumes saindo; recompensa: relíquia relic_trunk e estrela
  - `whole_bridge` (optional_challenge) — pista: Placa de madeira: 'Quem não para, não cai' e moedas ao longo de 600 u de tábuas; recompensa: relíquia relic_bridge
- **Colecionáveis:** ~95 moedas e 3 relíquias
- **Checkpoints:** 2
- **Eventos especiais:**
  - message (x2000): Ciranda — “O arbusto que pisca não é arbusto.”
- **Elementos animados:**
  - assentos de cipó balançando com cordas animadas
  - tábuas caindo na névoa e se refazendo
  - arbusto abrindo olhos amarelos
  - névoa da ravina em camadas
- **Trilha sonora:** `enchanted_forest_main` — ravina: violão percussivo, flautas e um balanço em 6/8 (sub-áreas: `enchanted_forest_underground`)
- **Condição de conclusão:** Tocar a bandeira em x5650.
- **Critérios de teste:**
  - validate_level e validate_campaign sem erros (schema, espécies, bioma, ordem de introdução, warps com chão)
  - route_bot conclui a fase partindo do spawn e de cada um dos 2 checkpoint(s), com inimigos e perigos ativos
  - vãos obrigatórios ≤ 150 u na mesma altura e subidas obrigatórias ≤ 64 u, simulados nas duas alturas do jogador sem coyote nem buffer
  - as 3 relíquias e todas as moedas são alcançáveis (rota de teste dedicada por relíquia; nenhuma moeda leva a morte)
  - estreias (Arbusto-Espreita) em chão plano com ≥ 300 u de aproximação visível, recuo livre e nenhum vão letal a 200 u
  - teto sobre patrulha: nenhum sólido não semissólido com base entre y_chão−158 e y_chão−30 sobre a patrulha de inimigo terrestre a menos de 160 u de um vão obrigatório
  - zona segura de cada checkpoint: chão plano de x−96 a x+192 e nenhum inimigo comum alcança [x−160, x+320] em 3 s de simulação
  - cada assento de cipó obrigatório fica a ≤ 150 u do apoio anterior em algum ponto do ciclo, e o ciclo é ≤ 5,5 s
  - estreia do arbusto em chão plano, sem vão em 200 u
  - a espiral descendente nunca exige queda cega > 220 u
  - o bot conclui partindo dos 2 checkpoints
- **Requisitos de motor:** nenhum (implementável com o motor atual)

### 5-5 · Clareira dos Sussurros (`whispering_hollow`)

*Ideia própria:* descer o tronco oco no escuro e subir de volta pelos chapéus dos cogumelos.

- **Identificador:** `whispering_hollow`
- **Nome:** Clareira dos Sussurros
- **Mundo:** Floresta Encantada (`enchanted_forest`, bioma `forest`), fase 5 de 6 — origem: nova
- **Objetivo:** Desafio avançado: descer por dentro de um tronco oco e subir de volta, combinando aranhas que descem do teto, inimigos camuflados denunciados por sussurros e cogumelos-mola, com pouca luz.
- **Tema visual:** Clareira noturna azul com anel de cogumelos, tronco oco gigantesco com interior de madeira escura, fungos luminosos, teias com orvalho; sussurros visualizados como ondas suaves de luz.
- **Mecânica principal:** Descida e subida vertical dentro de um tronco oco (semissólidos de fungo, cogumelos-mola) sob ameaça de cima
- **Mecânicas secundárias:**
  - Aranha-do-Cipó (nota Lume abaixo e desce em arco)
  - sussurros (áudio posicional) antes de camuflados agirem
  - pouca luz com fungos luminosos (zonas dark opcionais)
  - todos os moradores da floresta
- **Dificuldade:** 6/10
- **Duração planejada:** 110–220 s (primeira travessia → exploração completa)
- **Tamanho do cenário:** 5800 × 2160 u
  - `main` [forest] 0,0 5800×2160: clareira (y≈450), interior do tronco oco (x1800–4200, descendo até y≈2000) e subida
- **Caminho principal** (sequência de ensino):
  1. **Introdução** (0–700 u) — Clareira com anel de cogumelos; Aranha-do-Cipó (estreia) pendurada sobre chão plano: nota Lume embaixo e desce em arco — afastar-se ou pisar.
  2. **Demonstração segura** (700–1300 u) — Duas aranhas em sequência sobre chão com cobertura (galhos semissólidos acima para se abrigar).
  3. **Primeiro desafio** (1300–1800 u) — Primeiro sussurro: um arbusto-espreita entre arbustos comuns — o som vem do lado certo antes da investida.
  4. **Escalada** (1800–2800 u) — Entrada do tronco oco (checkpoint x1900); descida por fungos semissólidos com aranhas no teto e caracóis-musgo nos patamares; moedas guiam cada queda.
  5. **Combinação** (2800–3600 u) — Fundo do oco (y≈2000): salão escuro com fungos luminosos, cogumelos saltitantes e planta-de-esporos; sussurros indicam quem está camuflado.
  6. **Reviravolta** (3600–4200 u) — A subida usa os chapéus de cogumelo-mola em cadeia — o que era fundo vira trampolim; aranhas agora acima e abaixo.
  7. **Teste final** (4200–5200 u) — Checkpoint x4200 na boca superior do tronco; travessia das copas noturnas com mariposas, aranhas e arbustos.
  8. **Recompensa** (5200–5800 u) — Anel de cogumelos final acende e bandeira em x5650.
- **Caminhos alternativos:**
  - Anel de fadas: pisar os 7 cogumelos do anel na ordem do brilho (relíquia).
  - Bloco oculto de vagalumes no fundo do oco (relíquia).
  - Ninho da aranha (cano de raiz) → sala secreta (relíquia, estrela).
- **Inimigos permitidos:** `bolota` (Bolota), `caramujo` (Caramujo-de-Casca), `besouro_alado` (Besouro-Asa), `besouro` (Besouro), `flor_mordedora` (Flor-Mordedora), `ourico_espinho` (Ouriço-Espinho), `cogumelo_saltitante` (Cogumelo Saltitante), `caracol_musgo` (Caracol-Musgo), `mariposa_lume` (Mariposa-Lume), `planta_esporos` (Planta-de-Esporos), `besouro_casca` (Besouro-Casca), `arbusto_espreita` (Arbusto-Espreita), `aranha_cipo` (Aranha-do-Cipó — estreia)
- **Quantidade planejada de inimigos:** 18–24 (chefes não contados)
- **Obstáculos:**
  - aranhas descendo
  - camuflados (arbusto, caracol-musgo)
  - quedas guiadas dentro do oco
  - pouca luz
  - esporos
- **Itens disponíveis:**
  - crescer: ? x400
  - fogo: ? no fundo do oco
  - estrela: sala do ninho
  - coração: checkpoint 2
- **Segredos:**
  - `fairy_ring` (optional_challenge) — pista: Anel de 7 cogumelos que acendem um por vez numa sequência; recompensa: relíquia relic_ring
  - `hollow_light` (hidden_block) — pista: Vagalumes de Ciranda pousam num ponto vazio no escuro do fundo do oco; recompensa: relíquia relic_hollow
  - `spider_nest` (warp_room) — pista: Raiz oca com teia brilhante na entrada; recompensa: relíquia relic_nest e estrela
- **Colecionáveis:** ~100 moedas e 3 relíquias
- **Checkpoints:** 2
- **Eventos especiais:**
  - message (x1900): Ciranda — “Escute: quem sussurra está escondido perto.”
  - lights (x1800–4200): fungos e vagalumes como fontes de luz no oco (raio ~180 u)
- **Elementos animados:**
  - aranhas descendo em fio
  - ondas de luz dos sussurros
  - fungos luminosos pulsando
  - anel de cogumelos acendendo
- **Trilha sonora:** `enchanted_forest_underground` — noite no oco: sussurros, sinos graves e harpa em tom menor; na clareira volta enchanted_forest_main em versão noturna (sub-áreas: `enchanted_forest_main`)
- **Condição de conclusão:** Tocar a bandeira em x5650.
- **Critérios de teste:**
  - validate_level e validate_campaign sem erros (schema, espécies, bioma, ordem de introdução, warps com chão)
  - route_bot conclui a fase partindo do spawn e de cada um dos 2 checkpoint(s), com inimigos e perigos ativos
  - vãos obrigatórios ≤ 150 u na mesma altura e subidas obrigatórias ≤ 64 u, simulados nas duas alturas do jogador sem coyote nem buffer
  - as 3 relíquias e todas as moedas são alcançáveis (rota de teste dedicada por relíquia; nenhuma moeda leva a morte)
  - estreias (Aranha-do-Cipó) em chão plano com ≥ 300 u de aproximação visível, recuo livre e nenhum vão letal a 200 u
  - teto sobre patrulha: nenhum sólido não semissólido com base entre y_chão−158 e y_chão−30 sobre a patrulha de inimigo terrestre a menos de 160 u de um vão obrigatório
  - zona segura de cada checkpoint: chão plano de x−96 a x+192 e nenhum inimigo comum alcança [x−160, x+320] em 3 s de simulação
  - toda queda dentro do oco tem trilha de moedas até chão de ≥ 160 u
  - cada camuflado emite sussurro ≥ 1 s antes de agir e o som vem do lado correto
  - sem a máscara de luz a fase continua completável (degrada para visível)
  - aranhas nunca descem sobre checkpoints
- **Requisitos de motor:** 
  - não bloqueia — lights (extensão): a máscara de escuridão das zonas dark com o halo de Lume (120 u; 64 u correndo) já é desenhada; faltam lanternas fixas e acendíveis com raio e duração e o evento lights global (apagar/acender) (opcional: sem a máscara a fase fica jogável e mais clara)

### 5-6 · Santuário das Raízes (`root_sanctum`)

*Ideia própria:* as raízes crescem e recolhem em ritmo como pontes vivas.

- **Identificador:** `root_sanctum`
- **Nome:** Santuário das Raízes
- **Mundo:** Floresta Encantada (`enchanted_forest`, bioma `forest`), fase 6 de 6 — origem: nova
- **Objetivo:** Fortaleza da Floresta Encantada: atravessar o templo envolvido por raízes vivas que crescem em ritmo, usar tudo da floresta e derrotar a Imperatriz Mariposa em suas duas formas.
- **Tema visual:** Templo de pedra antiga engolido por raízes vivas que pulsam em ciano, altares com flores-lanterna, colunas rachadas, casulos pendurados; santuário circular dentro do tronco ancestral.
- **Mecânica principal:** Raízes vivas como plataformas que sobem e descem em ritmo (moving eixo y com fases encadeadas)
- **Mecânicas secundárias:**
  - pontes de cipó e assentos (do L4)
  - camuflados e aranhas
  - flores-lanterna que podem ser apagadas batendo por baixo (usadas pelo chefe)
  - chefe planejado Imperatriz Mariposa
- **Dificuldade:** 6/10
- **Duração planejada:** 150–300 s (primeira travessia → exploração completa)
- **Tamanho do cenário:** 6400 × 1620 u
  - `main` [forest] 0,0 1400×540: portal de raízes
  - `temple` [fortress] 1400,0 4000×1620: salões do templo envolvidos por raízes
  - `sanctum` [fortress] 5400,0 1000×1080: santuário circular (arena)
- **Caminho principal** (sequência de ensino):
  1. **Introdução** (0–700 u) — Portal: uma raiz-plataforma sobe e desce sobre chão firme (ritmo de 3 s) — demonstração.
  2. **Demonstração segura** (700–1400 u) — Três raízes em sequência com fases encadeadas sobre fosso de musgo raso.
  3. **Primeiro desafio** (1400–2200 u) — Salão das colunas: raízes sobre abismo + aranhas no teto + arbustos-espreita nas plataformas.
  4. **Escalada** (2200–3000 u) — Checkpoint x2200; corredor de casulos: casulos caem e eclodem mariposas (spawn) — passar entre eles.
  5. **Combinação** (3000–3800 u) — Escadaria de raízes vertical com cogumelos-mola, besouros-casca e flores-mordedoras em vasos.
  6. **Reviravolta** (3800–4600 u) — As raízes recolhem todas juntas a cada 6 s — atravessar o salão inteiro dentro de uma janela, usando assentos de cipó como apoio.
  7. **Teste final** (4600–5400 u) — Checkpoint x4700 na antessala com coração; Ciranda explica a lagarta e a mariposa.
  8. **Recompensa** (5400–6400 u) — Santuário: Imperatriz Mariposa (6 PV, duas formas); vitória abre as raízes; bandeira em x6250.
- **Caminhos alternativos:**
  - Telhado de raízes acima do salão das colunas (relíquia).
  - Altar escondido atrás de raízes secas (paredes quebráveis; alternativa com tijolos) (relíquia).
  - Desafio dos casulos: atravessar o corredor sem acordar nenhum (relíquia).
- **Inimigos permitidos:** `bolota` (Bolota), `caramujo` (Caramujo-de-Casca), `besouro_alado` (Besouro-Asa), `besouro` (Besouro), `flor_mordedora` (Flor-Mordedora), `ourico_espinho` (Ouriço-Espinho), `cogumelo_saltitante` (Cogumelo Saltitante), `caracol_musgo` (Caracol-Musgo), `mariposa_lume` (Mariposa-Lume), `planta_esporos` (Planta-de-Esporos), `besouro_casca` (Besouro-Casca), `arbusto_espreita` (Arbusto-Espreita), `aranha_cipo` (Aranha-do-Cipó), `boss:imperatriz_mariposa` (Imperatriz Mariposa (chefe planejado))
- **Quantidade planejada de inimigos:** 18–24 (chefes não contados)
- **Obstáculos:**
  - raízes em ritmo sobre abismo
  - casulos que eclodem
  - aranhas e camuflados
  - janela de 6 s do salão das raízes
- **Itens disponíveis:**
  - crescer: ? x500
  - fogo: ? x2300
  - estrela: altar escondido
  - coração: antessala x4750
- **Segredos:**
  - `root_roof` (high_route) — pista: Raízes com flores-lanterna formam degraus até o teto do salão; recompensa: relíquia relic_roof
  - `dry_altar` (breakable_path) — pista: Raízes secas e quebradiças com luz ciano vazando entre elas; recompensa: relíquia relic_altar e estrela
  - `cocoon_run` (optional_challenge) — pista: Casulos dormindo com 'zzz' de pólen; placa de Ciranda: 'não acorde ninguém'; recompensa: relíquia relic_cocoon
- **Colecionáveis:** ~100 moedas e 3 relíquias
- **Checkpoints:** 2
- **Eventos especiais:**
  - boss_arena (x5400): trava a câmera no santuário e fecha o portal de raízes
  - message (x4700): Ciranda — “A lagarta brilha onde dói. A mariposa pousa para beber luz.”
- **Elementos animados:**
  - raízes pulsando em ciano ao subir e descer
  - casulos balançando e eclodindo
  - flores-lanterna acendendo e apagando
  - metamorfose da lagarta em mariposa
- **Trilha sonora:** `enchanted_forest_fortress` — templo vivo: tambores de madeira, coro em uníssono e harpa grave; tema do chefe com cordas em espiral (sub-áreas: `enchanted_forest_underground`, `enchanted_forest_boss`)
- **Condição de conclusão:** Derrotar a Imperatriz Mariposa (6 PV) e tocar a bandeira em x6250.
- **Critérios de teste:**
  - validate_level e validate_campaign sem erros (schema, espécies, bioma, ordem de introdução, warps com chão)
  - route_bot conclui a fase partindo do spawn e de cada um dos 2 checkpoint(s), com inimigos e perigos ativos
  - vãos obrigatórios ≤ 150 u na mesma altura e subidas obrigatórias ≤ 64 u, simulados nas duas alturas do jogador sem coyote nem buffer
  - as 3 relíquias e todas as moedas são alcançáveis (rota de teste dedicada por relíquia; nenhuma moeda leva a morte)
  - teto sobre patrulha: nenhum sólido não semissólido com base entre y_chão−158 e y_chão−30 sobre a patrulha de inimigo terrestre a menos de 160 u de um vão obrigatório
  - zona segura de cada checkpoint: chão plano de x−96 a x+192 e nenhum inimigo comum alcança [x−160, x+320] em 3 s de simulação
  - as raízes do salão de 6 s sempre permitem a travessia na janela com corrida (largura ≤ 6 s × 340 u/s × 0,7)
  - a arena tem três níveis alcançáveis por salto (≤ 64 u) ou mola
  - o bot vence o chefe partindo do checkpoint da antessala
  - nenhum casulo cai sobre checkpoint
- **Requisitos de motor:** 
  - **bloqueia** — comportamento do chefe planejado Imperatriz Mariposa (imperatriz_mariposa): família nova em lume/core/behaviors/bosses.py
  - não bloqueia — breakable walls: paredes quebráveis por casco, fogo ou investida (segredos) (só para o segredo do altar)

## Mundo 6 — Cidade Mecânica (`clockwork_city`)

Engrenagens, vapor e esteiras. A cidade é um relógio: tudo se move em compasso — engrenagens, vapor, esteiras, interruptores — e o chefe é vencido com a própria prensa da fábrica. Detalhes do mundo em [`MUNDO_06.md`](MUNDO_06.md).

### 6-1 · Distrito das Engrenagens (`gear_district`)

*Ideia própria:* o projétil do canhão vira degrau.

- **Identificador:** `gear_district`
- **Nome:** Distrito das Engrenagens
- **Mundo:** Cidade Mecânica (`clockwork_city`, bioma `city`), fase 1 de 6 — origem: nova
- **Objetivo:** Apresentar a cidade: esteiras suaves, engrenagens que giram como plataformas, o Robô de Ronda e o Canhão Sentinela, cujos projéteis lentos podem ser pisados.
- **Tema visual:** Ruas de paralelepípedo com fachadas de tijolo e latão, engrenagens gigantes nas paredes, postes a gás, cartazes iluminados, chaminés ao fundo; manhã enfumaçada com luz âmbar.
- **Mecânica principal:** Engrenagens-plataforma (motion circle) e esteiras suaves (conveyor ±80 u/s)
- **Mecânicas secundárias:**
  - Robô de Ronda (para e varre com o farol; a luz não fere)
  - Canhão Sentinela (indestrutível; projéteis lentos e pisáveis)
  - engrenagens em fase oposta
  - bueiro de passagem para o esgoto
- **Dificuldade:** 5/10
- **Duração planejada:** 85–170 s (primeira travessia → exploração completa)
- **Tamanho do cenário:** 5000 × 1240 u
  - `main` [city] 0,0 5000×540: ruas e praças com dois vãos de engrenagens
  - `sewer` [underground] 2600,700 1400×540: esgoto (sala secreta)
- **Caminho principal** (sequência de ensino):
  1. **Introdução** (0–700 u) — Rua plana; esteira a favor (+80) com moedas: sentir o arrasto; dica do Mestre Corda.
  2. **Demonstração segura** (700–1300 u) — Engrenagem (raio 60, 1 rad/s) sobre chão firme: subir no dente mais alto e descer.
  3. **Primeiro desafio** (1300–2000 u) — Robô de Ronda (estreia) numa rua plana: para, varre com o farol e segue — pisar por trás.
  4. **Escalada** (2000–2700 u) — Checkpoint x2000; duas engrenagens em fase oposta sobre um vão de 140 u: sempre há um dente em posição.
  5. **Combinação** (2700–3500 u) — Canhão Sentinela (estreia) num pedestal no fim de uma rua plana: projéteis a 160 u/s a cada 3,2 s; pisar um projétil dá impulso até um beiral com moedas.
  6. **Reviravolta** (3500–4200 u) — Esteira contra (−120) sob engrenagens — o arrasto encurta o salto; usar a engrenagem que sobe.
  7. **Teste final** (4200–4700 u) — Checkpoint x4200; esteiras contrárias + canhões + robôs juntos.
  8. **Recompensa** (4700–5000 u) — Praça do relógio com chafariz de vapor e bandeira em x4850.
- **Caminhos alternativos:**
  - Engrenagem dourada: relíquia no topo da volta de uma engrenagem alta.
  - Bueiro x2600 → esgoto (relíquia, estrela).
  - Cartaz piscando esconde blocos ocultos sobre a rua (relíquia).
- **Inimigos permitidos:** `robo_patrulha` (Robô de Ronda — estreia), `sentinela_canhao` (Canhão Sentinela — estreia)
- **Quantidade planejada de inimigos:** 10–14 (chefes não contados)
- **Obstáculos:**
  - vãos de 140 u com engrenagens
  - esteiras contrárias
  - projéteis do canhão
- **Itens disponíveis:**
  - crescer: ? x400
  - fogo: ? x1800
  - estrela: esgoto
  - coração: praça x4300
- **Segredos:**
  - `golden_gear` (optional_challenge) — pista: Uma engrenagem dourada maior gira acima da rua com moedas no topo da volta; recompensa: relíquia relic_gear
  - `sewer` (warp_room) — pista: Bueiro com vapor e luz turquesa saindo pela grade; recompensa: relíquia relic_sewer e estrela
  - `billboard` (hidden_block) — pista: Lâmpada do cartaz pisca em código sobre um ponto vazio da rua; recompensa: relíquia relic_billboard
- **Colecionáveis:** ~80 moedas e 3 relíquias
- **Checkpoints:** 2
- **Eventos especiais:**
  - message (x2000): Mestre Corda — “Toda máquina tem compasso. Conte com o tique-taque.”
- **Elementos animados:**
  - engrenagens das fachadas girando junto com as plataformas
  - rolos das esteiras
  - farol do robô varrendo
  - fumaça do canhão antes do disparo
- **Trilha sonora:** `clockwork_city_main` — cidade acordando: metais leves, xilofone e caixinha de música em compasso marcado (sub-áreas: `clockwork_city_underground`)
- **Condição de conclusão:** Tocar a bandeira em x4850.
- **Critérios de teste:**
  - validate_level e validate_campaign sem erros (schema, espécies, bioma, ordem de introdução, warps com chão)
  - route_bot conclui a fase partindo do spawn e de cada um dos 2 checkpoint(s), com inimigos e perigos ativos
  - vãos obrigatórios ≤ 160 u na mesma altura e subidas obrigatórias ≤ 64 u, simulados nas duas alturas do jogador sem coyote nem buffer
  - as 3 relíquias e todas as moedas são alcançáveis (rota de teste dedicada por relíquia; nenhuma moeda leva a morte)
  - estreias (Robô de Ronda, Canhão Sentinela) em chão plano com ≥ 300 u de aproximação visível, recuo livre e nenhum vão letal a 200 u
  - teto sobre patrulha: nenhum sólido não semissólido com base entre y_chão−158 e y_chão−30 sobre a patrulha de inimigo terrestre a menos de 160 u de um vão obrigatório
  - zona segura de cada checkpoint: chão plano de x−96 a x+192 e nenhum inimigo comum alcança [x−160, x+320] em 3 s de simulação
  - engrenagens em fase oposta: em qualquer instante há um dente a ≤ 160 u de cada margem
  - o projétil do canhão é pisável nas duas alturas e dá o impulso de pisão (390 u/s)
  - estreias de robô e canhão em rua plana com ≥ 300 u de aproximação
  - o arrasto das esteiras está incluído na simulação dos vãos obrigatórios
- **Requisitos de motor:** nenhum (implementável com o motor atual)

### 6-2 · Usina de Vapor (`steam_works`)

*Ideia própria:* o vapor deita: jatos laterais empurram para fora das passarelas.

- **Identificador:** `steam_works`
- **Nome:** Usina de Vapor
- **Mundo:** Cidade Mecânica (`clockwork_city`, bioma `city`), fase 2 de 6 — origem: nova
- **Objetivo:** Explorar a usina subindo por jatos de vapor, escolher caminhos numa rede de canos com quatro saídas e conhecer o Drone Vigia, que mira e mergulha em diagonal.
- **Tema visual:** Usina de tijolos e ferro com caldeiras, manômetros de ponteiro, canos coloridos por função, passarelas de grade, chaminés e nuvens de vapor branco iluminadas de âmbar.
- **Mecânica principal:** Jatos de vapor ascendentes (zonas wind force_y ≈ −1900) contínuos e intermitentes (período 3 s, duty 0,5)
- **Mecânicas secundárias:**
  - Drone Vigia (paira, mira e mergulha em diagonal)
  - rede de canos com quatro destinos (warps)
  - jatos laterais (force_x ±160)
  - manômetros como aviso dos jatos
- **Dificuldade:** 5/10
- **Duração planejada:** 100–200 s (primeira travessia → exploração completa)
- **Tamanho do cenário:** 5400 × 2160 u
  - `main` [city] 0,0 5400×1620: pátio, poço vertical, salão de canos e chaminés
  - `valve_room` [underground] 2400,1620 960×540: sala da válvula mestra (cano azul)
- **Caminho principal** (sequência de ensino):
  1. **Introdução** (0–700 u) — Pátio da usina: jato contínuo sobre chão firme — subir no vapor até uma passarela e descer.
  2. **Demonstração segura** (700–1300 u) — Jatos intermitentes com manômetro (ponteiro no vermelho = jato ligado): esperar o ponteiro subir.
  3. **Primeiro desafio** (1300–2000 u) — Drone Vigia (estreia) sobre um pátio plano com cobertura: mergulha quando Lume passa embaixo — esperar o mergulho e pisar na subida.
  4. **Escalada** (2000–2800 u) — Checkpoint x2000; poço vertical subindo por jatos alternados com drones nas paredes.
  5. **Combinação** (2800–3600 u) — Salão de canos: quatro canos com placas de cor — vermelho (atalho), azul (relíquia), verde (moedas), amarelo (volta ao salão).
  6. **Reviravolta** (3600–4200 u) — Jatos laterais (±160, período 2,5 s) empurram para fora das passarelas; abrigos atrás das caldeiras.
  7. **Teste final** (4200–5000 u) — Checkpoint x4300; subida pelas chaminés com drones, robôs e canhões nos telhados.
  8. **Recompensa** (5000–5400 u) — Telhado da usina com vista da torre do relógio; bandeira em x5250.
- **Caminhos alternativos:**
  - Cano vermelho: atalho que pula o poço vertical (sem relíquia).
  - Cano azul: sala da válvula mestra (relíquia).
  - Chaminé apagada: subida opcional sem vapor, só com saltos precisos (relíquia).
- **Inimigos permitidos:** `robo_patrulha` (Robô de Ronda), `sentinela_canhao` (Canhão Sentinela), `drone_vigia` (Drone Vigia — estreia)
- **Quantidade planejada de inimigos:** 12–16 (chefes não contados)
- **Obstáculos:**
  - jatos intermitentes
  - jatos laterais
  - mergulhos de drone
  - projéteis de canhão nos telhados
- **Itens disponíveis:**
  - crescer: ? x500
  - fogo: ? x2100
  - estrela: sala da válvula
  - coração: checkpoint 2
- **Segredos:**
  - `master_valve` (warp_room) — pista: Cano azul com placa de válvula e vapor frio (azulado) saindo; recompensa: relíquia relic_valve e estrela
  - `cold_chimney` (optional_challenge) — pista: Uma chaminé sem fumaça, com fuligem formando degraus; recompensa: relíquia relic_chimney
  - `gauge_block` (hidden_block) — pista: Um manômetro sem cano aponta para cima, para um ponto vazio; recompensa: relíquia relic_gauge
- **Colecionáveis:** ~95 moedas e 3 relíquias
- **Checkpoints:** 2
- **Eventos especiais:**
  - message (x2000): Mestre Corda — “Ponteiro no vermelho, vapor ligado. Espere subir.”
- **Elementos animados:**
  - jatos de vapor sincronizados com Game.zone_active
  - ponteiros dos manômetros
  - hélice do drone e mira vermelha
  - caldeiras tremendo
- **Trilha sonora:** `clockwork_city_main` — usina: percussão metálica, chiado de vapor no tempo forte e tuba (sub-áreas: `clockwork_city_underground`)
- **Condição de conclusão:** Tocar a bandeira em x5250.
- **Critérios de teste:**
  - validate_level e validate_campaign sem erros (schema, espécies, bioma, ordem de introdução, warps com chão)
  - route_bot conclui a fase partindo do spawn e de cada um dos 2 checkpoint(s), com inimigos e perigos ativos
  - vãos obrigatórios ≤ 160 u na mesma altura e subidas obrigatórias ≤ 64 u, simulados nas duas alturas do jogador sem coyote nem buffer
  - as 3 relíquias e todas as moedas são alcançáveis (rota de teste dedicada por relíquia; nenhuma moeda leva a morte)
  - estreias (Drone Vigia) em chão plano com ≥ 300 u de aproximação visível, recuo livre e nenhum vão letal a 200 u
  - teto sobre patrulha: nenhum sólido não semissólido com base entre y_chão−158 e y_chão−30 sobre a patrulha de inimigo terrestre a menos de 160 u de um vão obrigatório
  - zona segura de cada checkpoint: chão plano de x−96 a x+192 e nenhum inimigo comum alcança [x−160, x+320] em 3 s de simulação
  - cada jato intermitente tem aviso visual (ponteiro) ≥ 0,6 s antes de ligar
  - jatos laterais nunca empurram para vão sem abrigo a ≤ 120 u
  - os quatro canos do salão têm volta e nenhum prende o jogador
  - o drone nunca mergulha sobre checkpoint
- **Requisitos de motor:** nenhum (implementável com o motor atual)

### 6-3 · Linha de Montagem (`conveyor_line`)

*Ideia própria:* a prensa vira elevador e, no fim, a linha acelera.

- **Identificador:** `conveyor_line`
- **Nome:** Linha de Montagem
- **Mundo:** Cidade Mecânica (`clockwork_city`, bioma `city`), fase 3 de 6 — origem: nova
- **Objetivo:** Desafio de movimento: atravessar a linha de montagem com esteiras de velocidades e sentidos diferentes e prensas a vapor em compasso; terminar na 'linha acelerada'.
- **Tema visual:** Galpão de fábrica com esteiras de borracha, caixas de latão, braços mecânicos decorativos, prensas com vapor, luzes de aviso âmbar e faixas pretas e amarelas.
- **Mecânica principal:** Esteiras com velocidades e sentidos diferentes (±60 a ±240 u/s) somadas ao salto
- **Mecânicas secundárias:**
  - Prensa a Vapor (solta vapor 0,4 s e desce; topo seguro)
  - prensa como elevador
  - robôs carregados pela esteira
  - canhão ao longo da linha
- **Dificuldade:** 6/10
- **Duração planejada:** 100–200 s (primeira travessia → exploração completa)
- **Tamanho do cenário:** 5600 × 1240 u
  - `main` [city] 0,0 5600×540: galpão com esteiras em três alturas
  - `storage` [underground] 3400,700 960×540: depósito secreto
- **Caminho principal** (sequência de ensino):
  1. **Introdução** (0–700 u) — Esteira lenta (+60) com moedas; braços mecânicos decorativos.
  2. **Demonstração segura** (700–1300 u) — Prensa a Vapor (estreia) sobre chão firme: vapor (0,4 s), descida, descanso (0,9 s) e subida — o topo é seguro; subir nela quando está embaixo.
  3. **Primeiro desafio** (1300–2000 u) — Duas prensas alternadas sobre esteira contra (−80): passar no intervalo.
  4. **Escalada** (2000–2800 u) — Checkpoint x2000; esteiras em sequência (+120, −120, +200) sobre vãos de 140 u — o arrasto muda o alcance.
  5. **Combinação** (2800–3600 u) — Prensas + robôs carregados pela esteira + canhão disparando ao longo da linha.
  6. **Reviravolta** (3600–4300 u) — Escada rolante (esteiras em degraus descendentes) e uma prensa que serve de elevador até a linha de cima.
  7. **Teste final** (4300–5200 u) — Checkpoint x4300; 'a linha acelera': esteiras a 240 u/s com prensas em compasso rápido.
  8. **Recompensa** (5200–5600 u) — Expedição: caixas prontas e bandeira em x5450.
- **Caminhos alternativos:**
  - Linha de cima (vigas e braços mecânicos) com moedas e a relíquia da caixa dourada.
  - Caixa marcada com seta (cano) → depósito secreto (relíquia, estrela).
  - Desafio da prensa tripla: ficar sobre três prensas em sequência (relíquia).
- **Inimigos permitidos:** `robo_patrulha` (Robô de Ronda), `sentinela_canhao` (Canhão Sentinela), `drone_vigia` (Drone Vigia), `prensa_vapor` (Prensa a Vapor — estreia)
- **Quantidade planejada de inimigos:** 14–18 (chefes não contados)
- **Obstáculos:**
  - esteiras de várias velocidades
  - prensas em compasso
  - vãos de 140 u com arrasto
  - projéteis ao longo da linha
- **Itens disponíveis:**
  - crescer: ? x400
  - fogo: ? x1900
  - estrela: depósito
  - coração: checkpoint 2
- **Segredos:**
  - `golden_crate` (high_route) — pista: Uma caixa dourada passa na linha de cima; moedas sobre as vigas; recompensa: relíquia relic_crate
  - `storage` (warp_room) — pista: Caixa com seta pintada e etiqueta 'NÃO ABRIR'; recompensa: relíquia relic_storage e estrela
  - `triple_press` (optional_challenge) — pista: Três prensas com luzes verdes acesas em sequência; recompensa: relíquia relic_press
- **Colecionáveis:** ~90 moedas e 3 relíquias
- **Checkpoints:** 2
- **Eventos especiais:**
  - message (x2000): Mestre Corda — “A prensa tem topo seguro. Suba quando ela descansar.”
- **Elementos animados:**
  - rolos das esteiras na velocidade real
  - vapor das prensas antes de descer
  - luzes de aviso girando
  - caixas passando nas esteiras (decorativas)
- **Trilha sonora:** `clockwork_city_main` — fábrica: groove de metal batido, baixo de esteira e apito a cada compasso; acelera no fim (sub-áreas: `clockwork_city_underground`)
- **Condição de conclusão:** Tocar a bandeira em x5450.
- **Critérios de teste:**
  - validate_level e validate_campaign sem erros (schema, espécies, bioma, ordem de introdução, warps com chão)
  - route_bot conclui a fase partindo do spawn e de cada um dos 2 checkpoint(s), com inimigos e perigos ativos
  - vãos obrigatórios ≤ 160 u na mesma altura e subidas obrigatórias ≤ 64 u, simulados nas duas alturas do jogador sem coyote nem buffer
  - as 3 relíquias e todas as moedas são alcançáveis (rota de teste dedicada por relíquia; nenhuma moeda leva a morte)
  - estreias (Prensa a Vapor) em chão plano com ≥ 300 u de aproximação visível, recuo livre e nenhum vão letal a 200 u
  - teto sobre patrulha: nenhum sólido não semissólido com base entre y_chão−158 e y_chão−30 sobre a patrulha de inimigo terrestre a menos de 160 u de um vão obrigatório
  - zona segura de cada checkpoint: chão plano de x−96 a x+192 e nenhum inimigo comum alcança [x−160, x+320] em 3 s de simulação
  - simulação dos vãos inclui surface_speed da esteira de decolagem (a favor e contra)
  - o topo das prensas é seguro e elas não esmagam contra o teto sem aviso
  - a linha acelerada é vencível pelo bot partindo do checkpoint 2
  - estreia da prensa sobre chão firme e longe de vãos
- **Requisitos de motor:** nenhum (implementável com o motor atual)

### 6-4 · Fábrica dos Interruptores (`switch_factory`)

*Ideia própria:* a sala vertical em que cada andar pede a outra cor.

- **Identificador:** `switch_factory`
- **Nome:** Fábrica dos Interruptores
- **Mundo:** Cidade Mecânica (`clockwork_city`, bioma `city`), fase 4 de 6 — origem: nova
- **Objetivo:** Mecânica especial da Cidade Mecânica: atravessar a fábrica alternando blocos azuis e laranja com blocos-interruptor (incluindo interruptores temporizados) e ligar o painel que acende a esteira principal da fundição.
- **Tema visual:** Fábrica de painéis com blocos translúcidos azuis e laranja, contornos tracejados nos blocos desligados, cabos coloridos pelas paredes, painéis de luzes e o grande painel de controle no fim.
- **Mecânica principal:** Blocos-interruptor (switch) azul/laranja alternados por bloco-interruptor e por temporizador
- **Mecânicas secundárias:**
  - interruptor temporizado (volta em 6 s com tique-taque)
  - robôs cujo caminho muda com a cor
  - prensas e drones
  - contorno tracejado mostra o bloco desligado
- **Dificuldade:** 6/10
- **Duração planejada:** 110–220 s (primeira travessia → exploração completa)
- **Tamanho do cenário:** 5400 × 1620 u
  - `main` [city] 0,0 5400×1620: salões com pontes de blocos e sala vertical (x3600–4300)
- **Caminho principal** (sequência de ensino):
  1. **Introdução** (0–700 u) — Portaria: um bloco-interruptor e uma fileira de blocos azuis/laranja sobre chão firme — bater troca qual cor é sólida; nada a perder.
  2. **Demonstração segura** (700–1300 u) — Ponte de blocos laranja sobre um fosso raso com escada de volta.
  3. **Primeiro desafio** (1300–2000 u) — O interruptor fica sob uma plataforma azul: ao trocar, ela some e Lume cai na laranja que surgiu — a ordem das ações importa.
  4. **Escalada** (2000–2800 u) — Checkpoint x2000; interruptores temporizados (6 s com tique-taque): correr pela ponte antes de ela sumir.
  5. **Combinação** (2800–3600 u) — Interruptores + robôs + prensas: a troca de cor também abre e fecha o caminho dos robôs.
  6. **Reviravolta** (3600–4300 u) — Sala vertical em que cada andar exige a cor oposta — subir alternando, com um interruptor por andar.
  7. **Teste final** (4300–5000 u) — Checkpoint x4300; teste final com interruptor temporizado, drones e canhão.
  8. **Recompensa** (5000–5400 u) — Sala de controle: o painel gigante liga a esteira da fundição; bandeira em x5250.
- **Caminhos alternativos:**
  - Desvio laranja: rota alta disponível só com a cor laranja ativa (relíquia).
  - Depósito de interruptores quebrados (bloco oculto) (relíquia).
  - Corrida do tique-taque: interruptor temporizado de 4 s com ponte longa (relíquia).
- **Inimigos permitidos:** `robo_patrulha` (Robô de Ronda), `sentinela_canhao` (Canhão Sentinela), `drone_vigia` (Drone Vigia), `prensa_vapor` (Prensa a Vapor)
- **Quantidade planejada de inimigos:** 14–18 (chefes não contados)
- **Obstáculos:**
  - pontes que somem ao trocar a cor
  - interruptores temporizados
  - prensas e drones
  - fossos (rasos na demonstração, letais depois)
- **Itens disponíveis:**
  - crescer: ? x400
  - fogo: ? x2100
  - estrela: depósito
  - coração: checkpoint 2
- **Segredos:**
  - `orange_detour` (high_route) — pista: Contorno tracejado laranja de uma escada que só aparece com a cor laranja; recompensa: relíquia relic_orange
  - `broken_switches` (hidden_block) — pista: Pilha de interruptores quebrados soltando faíscas sob um ponto vazio; recompensa: relíquia relic_broken
  - `ticktock_run` (optional_challenge) — pista: Relógio de parede com ponteiro vermelho sobre um interruptor de 4 s; recompensa: relíquia relic_ticktock
- **Colecionáveis:** ~95 moedas e 3 relíquias
- **Checkpoints:** 2
- **Eventos especiais:**
  - blocos ? com recompensa toggle alternam os grupos 'azul' e 'laranja' (já suportado); interruptores temporizados: toggle_switch com params {group, duration: 6} (extensão)
  - message (x2000): Mestre Corda — “Bateu no interruptor? Azul vira laranja, laranja vira azul.”
- **Elementos animados:**
  - blocos acendendo/apagando com contorno tracejado
  - relógio do interruptor temporizado
  - cabos coloridos pulsando ao trocar a cor
  - painel gigante acendendo no fim
- **Trilha sonora:** `clockwork_city_main` — fábrica de luzes: sintetizador analógico e caixa de música; o arranjo troca de timbre a cada mudança de cor
- **Condição de conclusão:** Ligar o painel e tocar a bandeira em x5250.
- **Critérios de teste:**
  - validate_level e validate_campaign sem erros (schema, espécies, bioma, ordem de introdução, warps com chão)
  - route_bot conclui a fase partindo do spawn e de cada um dos 2 checkpoint(s), com inimigos e perigos ativos
  - vãos obrigatórios ≤ 160 u na mesma altura e subidas obrigatórias ≤ 64 u, simulados nas duas alturas do jogador sem coyote nem buffer
  - as 3 relíquias e todas as moedas são alcançáveis (rota de teste dedicada por relíquia; nenhuma moeda leva a morte)
  - teto sobre patrulha: nenhum sólido não semissólido com base entre y_chão−158 e y_chão−30 sobre a patrulha de inimigo terrestre a menos de 160 u de um vão obrigatório
  - zona segura de cada checkpoint: chão plano de x−96 a x+192 e nenhum inimigo comum alcança [x−160, x+320] em 3 s de simulação
  - ao trocar a cor, nenhum bloco ativado surge sobrepondo o jogador ou um inimigo (expulsão segura)
  - todo interruptor temporizado dá ≥ 1,5 s de folga para o bot
  - nenhum estado de cor deixa o jogador sem saída (sempre há interruptor alcançável)
  - o checkpoint restaura o estado de cor definido no checkpoint
- **Requisitos de motor:** 
  - **bloqueia** — toggle_switch (extensão): a alternância por bloco 'toggle' já existe (Game.toggle_group); faltam o evento toggle_switch por gatilho, o interruptor temporizado e a ligação do grupo a outros sistemas (esteiras, plataformas fantasmas) — a alternância básica já funciona; bloqueia só os trechos temporizados (etapas 4 e 7 e o desafio do tique-taque)

### 6-5 · Torre do Relógio (`clock_tower`)

*Ideia própria:* atravessar o mostrador montado nos ponteiros.

- **Identificador:** `clock_tower`
- **Nome:** Torre do Relógio
- **Mundo:** Cidade Mecânica (`clockwork_city`, bioma `city`), fase 5 de 6 — origem: nova
- **Objetivo:** Desafio avançado: subir a torre do relógio com plataformas sincronizadas a um compasso de 2 s, pêndulos, ponteiros como pontes giratórias e a Torreta de Arco, que lança porcas incandescentes em arco.
- **Tema visual:** Interior de torre com engrenagens enormes, pêndulo dourado, escadas de ferro, mostrador gigante translúcido visto por dentro e por fora, campanário com sinos; noite com lua atrás do mostrador.
- **Mecânica principal:** Plataformas sincronizadas a um compasso único (mesmo período, fases 0, π/2, π) e ponteiros do relógio como pontes giratórias (circle, alcance 200)
- **Mecânicas secundárias:**
  - Torreta de Arco (2 golpes; levanta o canhão antes de lançar)
  - pêndulo (moving eixo x)
  - prensas e esteiras nos patamares
  - drones no poço
- **Dificuldade:** 6/10
- **Duração planejada:** 120–240 s (primeira travessia → exploração completa)
- **Tamanho do cenário:** 4800 × 2700 u
  - `main` [city] 0,0 4800×2700: torre vertical do térreo (y≈2550) ao campanário (y≈200)
- **Caminho principal** (sequência de ensino):
  1. **Introdução** (Térreo (y≈2550)) — Pêndulo gigante (alcance 120) sobre chão: subir, balançar e descer.
  2. **Demonstração segura** (Andar 1) — Plataformas do tique-taque (período 2 s, fases 0/π/2/π) com som marcando o compasso.
  3. **Primeiro desafio** (Andar 2) — Torreta de Arco (estreia) num patamar plano: ergue o canhão (aviso) e lança porcas em arco; abrigar-se atrás de engrenagem.
  4. **Escalada** (Andar 3 (checkpoint 1)) — Esteiras nos patamares levando a vãos de 140 u e engrenagens em fase.
  5. **Combinação** (Poço das prensas) — Prensas em compasso + torretas + drones subindo pelo poço.
  6. **Reviravolta** (Mostrador (checkpoint 2)) — Atravessar o mostrador pelos ponteiros (o grande lento, o pequeno rápido) com a cidade lá embaixo.
  7. **Teste final** (Mecanismo do sino (checkpoint 3)) — Teste final com todos os mecanismos no mesmo compasso e duas torretas.
  8. **Recompensa** (Campanário (y≈200)) — Sinos tocam; bandeira em x4600 no campanário.
- **Caminhos alternativos:**
  - Engrenagem do cuco: porta do cuco (cano) → sala do mecanismo (relíquia).
  - Ponteiro dos segundos: volta inteira no ponteiro mais rápido (relíquia).
  - Viga externa do mostrador, por fora da torre (relíquia).
- **Inimigos permitidos:** `robo_patrulha` (Robô de Ronda), `sentinela_canhao` (Canhão Sentinela), `drone_vigia` (Drone Vigia), `prensa_vapor` (Prensa a Vapor), `torreta_arco` (Torreta de Arco — estreia)
- **Quantidade planejada de inimigos:** 16–22 (chefes não contados)
- **Obstáculos:**
  - plataformas sincronizadas
  - ponteiros giratórios
  - porcas em arco
  - prensas no poço
  - quedas verticais
- **Itens disponíveis:**
  - crescer: ? térreo
  - fogo: ? andar 2
  - estrela: sala do cuco
  - coração: mostrador
- **Segredos:**
  - `cuckoo_room` (warp_room) — pista: Porta do cuco abre e fecha a cada hora (a cada 10 s) mostrando luz dourada; recompensa: relíquia relic_cuckoo e estrela
  - `second_hand` (optional_challenge) — pista: Moedas presas ao ponteiro dos segundos dão uma volta inteira; recompensa: relíquia relic_second
  - `outer_beam` (high_route) — pista: Uma janela quebrada do mostrador deixa ver uma viga externa com moedas; recompensa: relíquia relic_beam
- **Colecionáveis:** ~110 moedas e 3 relíquias
- **Checkpoints:** 3
- **Eventos especiais:**
  - message (andar 3): Mestre Corda — “O ponteiro grande é lento, mas leva longe.”
  - camera_lock vertical (opcional) no mostrador para enquadrar os ponteiros
- **Elementos animados:**
  - engrenagens internas sincronizadas ao compasso
  - pêndulo dourado
  - ponteiros girando
  - sinos balançando no fim
- **Trilha sonora:** `clockwork_city_main` — torre: tique-taque como metrônomo, cordas em staccato e sinos; arranjo cresce a cada andar
- **Condição de conclusão:** Chegar ao campanário e tocar a bandeira em x4600 (y≈200).
- **Critérios de teste:**
  - validate_level e validate_campaign sem erros (schema, espécies, bioma, ordem de introdução, warps com chão)
  - route_bot conclui a fase partindo do spawn e de cada um dos 3 checkpoint(s), com inimigos e perigos ativos
  - vãos obrigatórios ≤ 160 u na mesma altura e subidas obrigatórias ≤ 64 u, simulados nas duas alturas do jogador sem coyote nem buffer
  - as 3 relíquias e todas as moedas são alcançáveis (rota de teste dedicada por relíquia; nenhuma moeda leva a morte)
  - estreias (Torreta de Arco) em chão plano com ≥ 300 u de aproximação visível, recuo livre e nenhum vão letal a 200 u
  - teto sobre patrulha: nenhum sólido não semissólido com base entre y_chão−158 e y_chão−30 sobre a patrulha de inimigo terrestre a menos de 160 u de um vão obrigatório
  - zona segura de cada checkpoint: chão plano de x−96 a x+192 e nenhum inimigo comum alcança [x−160, x+320] em 3 s de simulação
  - todas as plataformas da torre compartilham o mesmo período (2 s ou múltiplos) — verificação dos dados
  - nenhuma queda vertical maior que 220 u sem trilha de moedas até chão de ≥ 160 u
  - a torreta não tem linha de arco sobre os checkpoints
  - o bot conclui partindo dos 3 checkpoints
- **Requisitos de motor:** nenhum (implementável com o motor atual)

### 6-6 · Fundição de Ferro (`iron_foundry`)

*Ideia própria:* a linha invertida: o interruptor da fundição inverte todas as esteiras.

- **Identificador:** `iron_foundry`
- **Nome:** Fundição de Ferro
- **Mundo:** Cidade Mecânica (`clockwork_city`, bioma `city`), fase 6 de 6 — origem: nova
- **Objetivo:** Fortaleza da Cidade Mecânica: atravessar a fundição sobre metal fundido, caçambas e esteiras, e derrotar o Colosso Fundidor atraindo-o para baixo da prensa e acionando o interruptor no momento certo.
- **Tema visual:** Fundição escura com rios de metal fundido laranja, caçambas penduradas em trilhos, moldes, torres de resfriamento com vapor, fagulhas e grades; luz vermelha e âmbar.
- **Mecânica principal:** Metal fundido (perigo lava) atravessado por caçambas suspensas (moving eixo x) e esteiras
- **Mecânicas secundárias:**
  - interruptor que inverte as esteiras (toggle)
  - torres de resfriamento (vapor ascendente)
  - prensas, torretas, canhões e drones
  - chefe planejado Colosso Fundidor
- **Dificuldade:** 6/10
- **Duração planejada:** 150–300 s (primeira travessia → exploração completa)
- **Tamanho do cenário:** 6400 × 1620 u
  - `main` [city] 0,0 1400×540: pátio da fundição
  - `foundry` [fortress] 1400,0 4000×1620: salões de fundição, caçambas e moldes
  - `casting_hall` [fortress] 5400,0 1000×1080: salão do Colosso (arena)
- **Caminho principal** (sequência de ensino):
  1. **Introdução** (0–700 u) — Pátio: canal de metal fundido com ponte de vigas larga; brilho e fagulhas avisam o perigo.
  2. **Demonstração segura** (700–1400 u) — Caçambas suspensas (alcance 100 u) sobre metal fundido com chão de apoio entre elas.
  3. **Primeiro desafio** (1400–2200 u) — Esteiras levando para o metal com prensas: ritmo e arrasto em cima do perigo.
  4. **Escalada** (2200–3000 u) — Checkpoint x2200; torres de resfriamento com vapor ascendente para subir aos trilhos.
  5. **Combinação** (3000–3800 u) — Salão dos moldes: torretas + robôs + canhões + drones.
  6. **Reviravolta** (3800–4600 u) — Um interruptor inverte todas as esteiras do salão — o caminho de ida vira volta; usar a inversão para escapar das prensas.
  7. **Teste final** (4600–5400 u) — Checkpoint x4700 na antessala com coração; Mestre Corda explica a prensa.
  8. **Recompensa** (5400–6400 u) — Salão do Colosso Fundidor (5 PV); vitória transforma o núcleo no farol da fundição; bandeira em x6250.
- **Caminhos alternativos:**
  - Trilho das caçambas no teto (relíquia da caçamba).
  - Molde em forma de estrela (cano) → câmara de resfriamento (relíquia, estrela).
  - Corrida da inversão: atravessar o salão enquanto as esteiras invertem duas vezes (relíquia).
- **Inimigos permitidos:** `robo_patrulha` (Robô de Ronda), `sentinela_canhao` (Canhão Sentinela), `drone_vigia` (Drone Vigia), `prensa_vapor` (Prensa a Vapor), `torreta_arco` (Torreta de Arco), `boss:colosso_fundidor` (Colosso Fundidor (chefe planejado))
- **Quantidade planejada de inimigos:** 18–24 (chefes não contados)
- **Obstáculos:**
  - metal fundido (letal)
  - caçambas suspensas
  - esteiras invertidas
  - prensas e porcas em arco
- **Itens disponíveis:**
  - crescer: ? x500
  - fogo: ? x2300
  - estrela: câmara de resfriamento
  - coração: antessala x4750
- **Segredos:**
  - `bucket_rail` (high_route) — pista: Uma caçamba dourada parada no fim do trilho do teto; recompensa: relíquia relic_bucket
  - `star_mold` (warp_room) — pista: Molde em forma de estrela com vapor frio saindo; recompensa: relíquia relic_mold e estrela
  - `reverse_run` (optional_challenge) — pista: Placa com setas em sentidos opostos sobre o interruptor; recompensa: relíquia relic_reverse
- **Colecionáveis:** ~100 moedas e 3 relíquias
- **Checkpoints:** 2
- **Eventos especiais:**
  - toggle_switch (x3800–4600): inverte surface_speed de todas as esteiras do grupo 'linha'
  - boss_arena (x5400): trava a câmera no salão do Colosso e fecha a comporta
  - message (x4700): Mestre Corda — “A prensa da fundição obedece aos botões. O colosso, não.”
- **Elementos animados:**
  - metal fundido borbulhando e brilhando
  - caçambas balançando nos trilhos
  - fagulhas e vapor
  - núcleo do colosso pulsando
- **Trilha sonora:** `clockwork_city_fortress` — fundição: martelos em compasso industrial, metais graves e coro; tema do chefe com bigorna (sub-áreas: `clockwork_city_boss`)
- **Condição de conclusão:** Derrotar o Colosso Fundidor (5 PV) e tocar a bandeira em x6250.
- **Critérios de teste:**
  - validate_level e validate_campaign sem erros (schema, espécies, bioma, ordem de introdução, warps com chão)
  - route_bot conclui a fase partindo do spawn e de cada um dos 2 checkpoint(s), com inimigos e perigos ativos
  - vãos obrigatórios ≤ 160 u na mesma altura e subidas obrigatórias ≤ 64 u, simulados nas duas alturas do jogador sem coyote nem buffer
  - as 3 relíquias e todas as moedas são alcançáveis (rota de teste dedicada por relíquia; nenhuma moeda leva a morte)
  - teto sobre patrulha: nenhum sólido não semissólido com base entre y_chão−158 e y_chão−30 sobre a patrulha de inimigo terrestre a menos de 160 u de um vão obrigatório
  - zona segura de cada checkpoint: chão plano de x−96 a x+192 e nenhum inimigo comum alcança [x−160, x+320] em 3 s de simulação
  - todo vão sobre metal fundido tem caçamba ou viga a ≤ 160 u em algum ponto do ciclo
  - a inversão das esteiras nunca joga o jogador direto no metal sem aviso de 1 s
  - o bot vence o chefe partindo do checkpoint da antessala
  - a arena nunca fica sem interruptor alcançável
- **Requisitos de motor:** 
  - **bloqueia** — comportamento do chefe planejado Colosso Fundidor (colosso_fundidor): família nova em lume/core/behaviors/bosses.py
  - **bloqueia** — toggle_switch (extensão): a alternância por bloco 'toggle' já existe (Game.toggle_group); faltam o evento toggle_switch por gatilho, o interruptor temporizado e a ligação do grupo a outros sistemas (esteiras, plataformas fantasmas)

## Mundo 7 — Arquipélago Celeste (`sky_archipelago`)

Ilhas suspensas, nuvens e vendavais. O vazio deixa de ser só morte: saltar para dentro de uma corrente de ar ou de uma cachoeira que sobe é o caminho — até a grifa, vencida por quem fica acima dela. Detalhes do mundo em [`MUNDO_07.md`](MUNDO_07.md).

### 7-1 · Porto das Nuvens (`cloud_harbor`)

*Ideia própria:* saltar no vazio de propósito para pegar a corrente.

- **Identificador:** `cloud_harbor`
- **Nome:** Porto das Nuvens
- **Mundo:** Arquipélago Celeste (`sky_archipelago`, bioma `sky`), fase 1 de 6 — origem: nova
- **Objetivo:** Apresentar o céu: nuvens semissólidas, correntes ascendentes demonstradas sobre chão e depois sobre o vazio, nuvens-mola e o Pássaro-Rajada, que mergulha de poleiros.
- **Tema visual:** Porto de nuvens com cais de madeira clara, dirigíveis coloridos ancorados, faróis de vidro, ilhas pequenas com grama e flores, céu azul luminoso e nuvens fofas em camadas.
- **Mecânica principal:** Correntes ascendentes (wind force_y ≈ −1900) e nuvens semissólidas
- **Mecânicas secundárias:**
  - Pássaro-Rajada (espera no poleiro e mergulha em arco)
  - nuvens-mola (spring)
  - dirigíveis como pontes móveis
  - nuvens frágeis (crumble)
- **Dificuldade:** 6/10
- **Duração planejada:** 90–180 s (primeira travessia → exploração completa)
- **Tamanho do cenário:** 5400 × 1620 u
  - `main` [sky] 0,0 5400×1620: cais e ilhas em y≈600–1200 com correntes sobre o vazio
- **Caminho principal** (sequência de ensino):
  1. **Introdução** (0–700 u) — Cais: nuvens semissólidas sobre a ilha — atravessar por baixo e subir.
  2. **Demonstração segura** (700–1300 u) — Corrente ascendente contínua sobre chão de ilha: subir flutuando até uma nuvem com moedas; cair não machuca.
  3. **Primeiro desafio** (1300–2000 u) — Pássaro-Rajada (estreia) num poleiro sobre ilha larga: nota Lume embaixo e mergulha em arco — esperar e pisar na subida.
  4. **Escalada** (2000–2800 u) — Checkpoint x2000 no cais; nuvens-mola entre ilhas com vãos de 150 u sobre o vazio.
  5. **Combinação** (2800–3600 u) — Dirigíveis (moving eixo x) como pontes + pássaros + Abutrinhos.
  6. **Reviravolta** (3600–4300 u) — Correntes ascendentes sobre o vazio — moedas em coluna convidam a saltar para baixo e ser levado ao alto.
  7. **Teste final** (4300–5000 u) — Checkpoint x4300; nuvens frágeis + correntes + pássaros num só trecho.
  8. **Recompensa** (5000–5400 u) — Farol de nuvens e bandeira em x5250.
- **Caminhos alternativos:**
  - Mastro do dirigível mais alto (relíquia), alcançado pela nuvem-mola.
  - Porão de um dirigível (cano no convés) → sala de carga (relíquia, estrela).
  - Corrente escondida atrás de uma nuvem densa (decor frontal) até uma ilha secreta (relíquia).
- **Inimigos permitidos:** `abutre_filhote` (Abutrinho), `drone_vigia` (Drone Vigia), `passaro_rajada` (Pássaro-Rajada — estreia)
- **Quantidade planejada de inimigos:** 12–16 (chefes não contados)
- **Obstáculos:**
  - vazio entre ilhas (letal)
  - mergulhos do pássaro
  - nuvens frágeis
  - dirigíveis em movimento
- **Itens disponíveis:**
  - crescer: ? x400
  - fogo: ? x2100
  - estrela: sala de carga
  - coração: cais do checkpoint 2
- **Segredos:**
  - `airship_mast` (high_route) — pista: Bandeira dourada no mastro do dirigível mais alto; recompensa: relíquia relic_mast
  - `cargo_hold` (warp_room) — pista: Escotilha no convés com seta luminosa e caixotes; recompensa: relíquia relic_cargo e estrela
  - `hidden_current` (hidden_area) — pista: Fitas de Biruta somem dentro de uma nuvem densa; penas subindo; recompensa: relíquia relic_cloud
- **Colecionáveis:** ~90 moedas e 3 relíquias
- **Checkpoints:** 2
- **Eventos especiais:**
  - message (x2000): Biruta — “Moedas em coluna sobre o vazio? Pode pular: tem vento te esperando.”
- **Elementos animados:**
  - fitas e partículas nas correntes ascendentes
  - dirigíveis com hélices
  - nuvens se desfazendo e voltando
  - pássaro arrepiando as penas antes do mergulho
- **Trilha sonora:** `sky_archipelago_main` — céu aberto: cordas leves, flauta transversa e sinos de vento
- **Condição de conclusão:** Tocar a bandeira em x5250.
- **Critérios de teste:**
  - validate_level e validate_campaign sem erros (schema, espécies, bioma, ordem de introdução, warps com chão)
  - route_bot conclui a fase partindo do spawn e de cada um dos 2 checkpoint(s), com inimigos e perigos ativos
  - vãos obrigatórios ≤ 160 u na mesma altura e subidas obrigatórias ≤ 64 u, simulados nas duas alturas do jogador sem coyote nem buffer
  - as 3 relíquias e todas as moedas são alcançáveis (rota de teste dedicada por relíquia; nenhuma moeda leva a morte)
  - estreias (Pássaro-Rajada) em chão plano com ≥ 300 u de aproximação visível, recuo livre e nenhum vão letal a 200 u
  - teto sobre patrulha: nenhum sólido não semissólido com base entre y_chão−158 e y_chão−30 sobre a patrulha de inimigo terrestre a menos de 160 u de um vão obrigatório
  - zona segura de cada checkpoint: chão plano de x−96 a x+192 e nenhum inimigo comum alcança [x−160, x+320] em 3 s de simulação
  - toda corrente sobre o vazio pega o jogador que cai do ponto sinalizado e o solta sobre plataforma
  - a primeira corrente é demonstrada sobre chão (sem morte possível)
  - estreia do pássaro em ilha larga com recuo
  - o bot conclui partindo dos 2 checkpoints
- **Requisitos de motor:** nenhum (implementável com o motor atual)

### 7-2 · Jardins Flutuantes (`floating_gardens`)

*Ideia própria:* subir por baixo das ilhas pelas raízes pendentes.

- **Identificador:** `floating_gardens`
- **Nome:** Jardins Flutuantes
- **Mundo:** Arquipélago Celeste (`sky_archipelago`, bioma `sky`), fase 2 de 6 — origem: nova
- **Objetivo:** Explorar jardins suspensos em três camadas, com muitas rotas para cima e para baixo, enquanto a Nuvem Marota persegue Lume do alto e semeia Sementes-Espinho que viram andarilhos.
- **Tema visual:** Ilhas-jardim flutuantes com canteiros, treliças de flores, regadores e chafarizes, raízes pendentes sob as ilhas, gazebos; tarde dourada com pólen no ar.
- **Mecânica principal:** Exploração vertical entre três camadas de ilhas (correntes ascendentes, quedas guiadas e raízes semissólidas pendentes)
- **Mecânicas secundárias:**
  - Nuvem Marota (segue do alto e solta até 3 sementes)
  - Semente-Espinho (andarilho espinhoso: fogo, casco ou estrela)
  - raízes pendentes como escadas semissólidas
  - pássaros e drones
- **Dificuldade:** 7/10
- **Duração planejada:** 110–220 s (primeira travessia → exploração completa)
- **Tamanho do cenário:** 5600 × 2160 u
  - `main` [sky] 0,0 5600×2160: três camadas de ilhas (y≈500, 1000 e 1600)
- **Caminho principal** (sequência de ensino):
  1. **Introdução** (0–700 u) — Jardim da primeira ilha; Nuvem Marota (estreia) aparece sobre uma ilha vizinha e solta sementes lá — Lume observa à distância.
  2. **Demonstração segura** (700–1300 u) — Semente-Espinho (estreia) num canteiro plano: espinhosa, não pisável; ? de fogo logo antes.
  3. **Primeiro desafio** (1300–2000 u) — Primeira perseguição: a nuvem segue Lume sobre ilhas e solta até 3 sementes; pisá-la ou acertá-la com fogo a derrota.
  4. **Escalada** (2000–2800 u) — Checkpoint x2000; jardins em três camadas ligados por correntes ascendentes e quedas guiadas por moedas.
  5. **Combinação** (2800–3600 u) — Pássaros + sementes + correntes + drones; escolha de camada (alta: mais moedas; baixa: mais segura).
  6. **Reviravolta** (3600–4300 u) — Subir por baixo das ilhas pelas raízes pendentes semissólidas, longe da nuvem.
  7. **Teste final** (4300–5200 u) — Checkpoint x4300; subida final até a ilha mais alta com duas nuvens marotas.
  8. **Recompensa** (5200–5600 u) — Gazebo do jardim mais alto e bandeira em x5450.
- **Caminhos alternativos:**
  - Treliça de rosas da camada alta (relíquia do jardim).
  - Regador gigante (cano) → estufa secreta (relíquia, estrela).
  - Ilha baixa isolada: só alcançável descendo pela queda guiada mais longa (relíquia).
- **Inimigos permitidos:** `abutre_filhote` (Abutrinho), `drone_vigia` (Drone Vigia), `passaro_rajada` (Pássaro-Rajada), `nuvem_marota` (Nuvem Marota — estreia), `semente_espinho` (Semente-Espinho — estreia)
- **Quantidade planejada de inimigos:** 14–20 (chefes não contados)
- **Obstáculos:**
  - sementes espinhosas caindo
  - perseguição da nuvem
  - vazio entre camadas
  - mergulhos de pássaro
- **Itens disponíveis:**
  - fogo: ? x600 (antes da semente)
  - crescer: ? x1500
  - estrela: estufa
  - coração: gazebo do checkpoint 2
- **Segredos:**
  - `rose_trellis` (high_route) — pista: Rosas douradas no topo de uma treliça com moedas entre as flores; recompensa: relíquia relic_rose
  - `greenhouse` (warp_room) — pista: Regador gigante deitado com água brilhando dentro; recompensa: relíquia relic_greenhouse e estrela
  - `low_island` (hidden_area) — pista: Pétalas caem em espiral sobre o vazio marcando uma ilha baixa fora da tela; recompensa: relíquia relic_low
- **Colecionáveis:** ~110 moedas e 3 relíquias
- **Checkpoints:** 2
- **Eventos especiais:**
  - message (x2000): Biruta — “Aquela nuvem não é minha amiga. Ande por baixo das ilhas.”
- **Elementos animados:**
  - nuvem marota com rosto e risadinha antes de soltar sementes
  - sementes germinando ao tocar o chão
  - chafarizes e pólen
  - raízes pendentes balançando
- **Trilha sonora:** `sky_archipelago_main` — jardim no céu: valsa de cordas e celesta com pássaros
- **Condição de conclusão:** Tocar a bandeira em x5450.
- **Critérios de teste:**
  - validate_level e validate_campaign sem erros (schema, espécies, bioma, ordem de introdução, warps com chão)
  - route_bot conclui a fase partindo do spawn e de cada um dos 2 checkpoint(s), com inimigos e perigos ativos
  - vãos obrigatórios ≤ 160 u na mesma altura e subidas obrigatórias ≤ 64 u, simulados nas duas alturas do jogador sem coyote nem buffer
  - as 3 relíquias e todas as moedas são alcançáveis (rota de teste dedicada por relíquia; nenhuma moeda leva a morte)
  - estreias (Nuvem Marota, Semente-Espinho) em chão plano com ≥ 300 u de aproximação visível, recuo livre e nenhum vão letal a 200 u
  - teto sobre patrulha: nenhum sólido não semissólido com base entre y_chão−158 e y_chão−30 sobre a patrulha de inimigo terrestre a menos de 160 u de um vão obrigatório
  - zona segura de cada checkpoint: chão plano de x−96 a x+192 e nenhum inimigo comum alcança [x−160, x+320] em 3 s de simulação
  - a nuvem nunca mantém mais de 3 sementes vivas (limite do comportamento)
  - toda queda entre camadas tem trilha de moedas até chão de ≥ 160 u
  - estreia da semente em canteiro plano com fogo disponível
  - o bot conclui partindo dos 2 checkpoints
- **Requisitos de motor:** nenhum (implementável com o motor atual)

### 7-3 · Cachoeiras Ascendentes (`updraft_falls`)

*Ideia própria:* pular de uma cachoeira que sobe para outra que desce.

- **Identificador:** `updraft_falls`
- **Nome:** Cachoeiras Ascendentes
- **Mundo:** Arquipélago Celeste (`sky_archipelago`, bioma `sky`), fase 3 de 6 — origem: nova
- **Objetivo:** Desafio de movimento vertical: subir por cachoeiras que correm para cima (colunas de nado com corrente ascendente), saindo delas no tempo certo para ilhas, nuvens frágeis e poleiros; terminar com a revoada de pássaros.
- **Tema visual:** Paredões de pedra flutuantes com cachoeiras que sobem em espiral, arco-íris, névoa luminosa, ilhas com musgo e nuvens; a nascente brilhante no topo.
- **Mecânica principal:** Cachoeiras ascendentes: colunas swim com current force_y ≈ −700 (nado vertical) e colunas intermitentes
- **Mecânicas secundárias:**
  - saída lateral da coluna com salto (0,85 do impulso)
  - colunas descendentes vizinhas
  - nuvens frágeis entre colunas
  - revoada de pássaros-rajada
- **Dificuldade:** 7/10
- **Duração planejada:** 110–220 s (primeira travessia → exploração completa)
- **Tamanho do cenário:** 4800 × 2700 u
  - `main` [sky] 0,0 4800×2700: lago da base (y≈2550) até a nascente (y≈200)
- **Caminho principal** (sequência de ensino):
  1. **Introdução** (Base (y≈2550)) — Lago da base; a primeira cachoeira sobe: entrar e nadar com ela até uma ilha (queda devolve ao lago).
  2. **Demonstração segura** (Ilhas 1–2) — Colunas com saídas laterais: nadar para fora no topo e saltar para a ilha.
  3. **Primeiro desafio** (Ilhas 3–4) — Pássaros pousados nas bordas mergulham quando Lume sai da água.
  4. **Escalada** (Checkpoint 1) — Colunas intermitentes (período 3 s): quando a corrente desliga, Lume afunda devagar — sair antes.
  5. **Combinação** (Paredão central) — Nuvens frágeis entre colunas + drones + nuvem marota no alto.
  6. **Reviravolta** (Checkpoint 2 — espiral) — Coluna que desce ao lado de coluna que sobe — pular de uma para a outra alcança nichos e a continuação.
  7. **Teste final** (Checkpoint 3 — revoada) — Seis pássaros-rajada em poleiros ao longo da última subida.
  8. **Recompensa** (Nascente (y≈200)) — A fonte das cachoeiras nas nuvens; bandeira em x4600.
- **Caminhos alternativos:**
  - Gruta atrás da cachoeira central (relíquia).
  - Arco-íris sólido (semissólidos coloridos) visível só de um ângulo (relíquia).
  - Desafio da coluna intermitente mais longa (relíquia).
- **Inimigos permitidos:** `abutre_filhote` (Abutrinho), `drone_vigia` (Drone Vigia), `passaro_rajada` (Pássaro-Rajada), `nuvem_marota` (Nuvem Marota), `semente_espinho` (Semente-Espinho)
- **Quantidade planejada de inimigos:** 14–18 (chefes não contados)
- **Obstáculos:**
  - colunas intermitentes
  - colunas descendentes
  - nuvens frágeis
  - mergulhos na saída da água
- **Itens disponíveis:**
  - crescer: ? base
  - fogo: ? ilha 3
  - estrela: gruta
  - coração: checkpoint 2
- **Segredos:**
  - `waterfall_cave` (hidden_area) — pista: A cachoeira central se abre em volta de algo atrás dela; brilho dourado; recompensa: relíquia relic_cave e estrela
  - `rainbow_steps` (high_route) — pista: Um arco-íris com moedas nas faixas de cor; recompensa: relíquia relic_rainbow
  - `long_column` (optional_challenge) — pista: Coluna intermitente com marcações de altura e placa de Biruta; recompensa: relíquia relic_column
- **Colecionáveis:** ~110 moedas e 3 relíquias
- **Checkpoints:** 3
- **Eventos especiais:**
  - message (checkpoint 1): Biruta — “A cachoeira daqui corre para cima. Nade com ela.”
  - camera_lock vertical (opcional) na espiral
- **Elementos animados:**
  - água subindo com espuma invertida
  - arco-íris
  - névoa luminosa
  - revoada decolando dos poleiros
- **Trilha sonora:** `sky_archipelago_main` — cachoeiras: harpa em arpejos ascendentes, coro e água
- **Condição de conclusão:** Chegar à nascente e tocar a bandeira em x4600 (y≈200).
- **Critérios de teste:**
  - validate_level e validate_campaign sem erros (schema, espécies, bioma, ordem de introdução, warps com chão)
  - route_bot conclui a fase partindo do spawn e de cada um dos 3 checkpoint(s), com inimigos e perigos ativos
  - vãos obrigatórios ≤ 160 u na mesma altura e subidas obrigatórias ≤ 64 u, simulados nas duas alturas do jogador sem coyote nem buffer
  - as 3 relíquias e todas as moedas são alcançáveis (rota de teste dedicada por relíquia; nenhuma moeda leva a morte)
  - teto sobre patrulha: nenhum sólido não semissólido com base entre y_chão−158 e y_chão−30 sobre a patrulha de inimigo terrestre a menos de 160 u de um vão obrigatório
  - zona segura de cada checkpoint: chão plano de x−96 a x+192 e nenhum inimigo comum alcança [x−160, x+320] em 3 s de simulação
  - toda coluna ascendente leva o jogador até a saída em ≤ 4 s sem input além do nado
  - colunas intermitentes desligam com aviso de 0,6 s (espuma diminui)
  - nenhuma queda cega > 220 u sem trilha de moedas
  - o bot conclui partindo dos 3 checkpoints
- **Requisitos de motor:** nenhum (implementável com o motor atual)

### 7-4 · Pontes do Vendaval (`gale_bridges`)

*Ideia própria:* o vendaval cruzado: duas rajadas em fases opostas sobre um vão de 160 u.

- **Identificador:** `gale_bridges`
- **Nome:** Pontes do Vendaval
- **Mundo:** Arquipélago Celeste (`sky_archipelago`, bioma `sky`), fase 4 de 6 — origem: nova
- **Objetivo:** Mecânica especial do Arquipélago Celeste: atravessar pontes de corda entre torres de ancoragem sob vendavais fortes que mudam de lado, enquanto Balões-Espinho derivam com o vento.
- **Tema visual:** Pontes de corda e tábuas entre torres de pedra com cata-ventos, bandeiras esticadas, nuvens rápidas em faixas, balões de cardo; céu de vendaval com luz recortada.
- **Mecânica principal:** Vendavais laterais fortes (wind ±180 u/s, período 4 s, duty 0,35) que alternam de lado entre pontes
- **Mecânicas secundárias:**
  - Balão-Espinho (deriva no vento; só fogo ou estrela)
  - torres de ancoragem como abrigo
  - pontes frágeis
  - pássaros e drones
- **Dificuldade:** 7/10
- **Duração planejada:** 110–220 s (primeira travessia → exploração completa)
- **Tamanho do cenário:** 6000 × 1080 u
  - `main` [sky] 0,0 6000×1080: pontes em y≈500–700 entre torres e ponte escondida em y≈900
- **Caminho principal** (sequência de ensino):
  1. **Introdução** (0–700 u) — Ponte larga sobre uma ilha (chão embaixo) com uma rajada forte: sentir o vendaval sem risco.
  2. **Demonstração segura** (700–1300 u) — Balão-Espinho (estreia) derivando devagar numa ponte larga: espinhos por todo lado; desviar ou usar fogo.
  3. **Primeiro desafio** (1300–2000 u) — Ponte sobre o vazio com rajada contrária: avançar só na calmaria (cata-vento parado).
  4. **Escalada** (2000–2800 u) — Checkpoint x2000 numa torre; pontes alternadas — rajada da esquerda numa, da direita na seguinte.
  5. **Combinação** (2800–3600 u) — Balões levados no sentido da rajada + pássaros + pontes frágeis.
  6. **Reviravolta** (3600–4300 u) — Vendaval cruzado — duas zonas em fases opostas sobre um vão de 160 u; a rajada a favor encurta o salto; a contra exige esperar.
  7. **Teste final** (4300–5500 u) — Checkpoint x4300; travessia final com balões, drones e nuvem marota.
  8. **Recompensa** (5500–6000 u) — Torre de ancoragem final e bandeira em x5850.
- **Caminhos alternativos:**
  - Cata-vento dourado no topo de uma torre (relíquia).
  - Ponte de baixo (sob a principal), protegida do vento e com balões (relíquia).
  - Desafio do vendaval: atravessar uma ponte inteira durante a rajada contrária (relíquia).
- **Inimigos permitidos:** `abutre_filhote` (Abutrinho), `drone_vigia` (Drone Vigia), `passaro_rajada` (Pássaro-Rajada), `nuvem_marota` (Nuvem Marota), `semente_espinho` (Semente-Espinho), `balao_espinho` (Balão-Espinho — estreia)
- **Quantidade planejada de inimigos:** 16–22 (chefes não contados)
- **Obstáculos:**
  - vendavais alternados
  - balões espinhosos
  - pontes frágeis
  - vazio
- **Itens disponíveis:**
  - fogo: ? x900 (contra balões)
  - crescer: ? x1900
  - estrela: ponte de baixo
  - coração: torre do checkpoint 2
- **Segredos:**
  - `golden_vane` (high_route) — pista: Cata-vento dourado girando ao contrário dos outros no topo de uma torre; recompensa: relíquia relic_vane
  - `under_bridge` (hidden_area) — pista: Cordas pendem da ponte principal até uma ponte escondida nas nuvens baixas; recompensa: relíquia relic_under e estrela
  - `gale_run` (optional_challenge) — pista: Bandeira rasgada com moedas alinhadas contra o vento; recompensa: relíquia relic_gale
- **Colecionáveis:** ~100 moedas e 3 relíquias
- **Checkpoints:** 2
- **Eventos especiais:**
  - message (x2000): Biruta — “Fita esticada é rajada. Fita caída, atravessa.”
- **Elementos animados:**
  - cata-ventos e bandeiras sincronizados com as rajadas
  - pontes ondulando no vento
  - balões de cardo derivando
  - nuvens em faixas rápidas
- **Trilha sonora:** `sky_archipelago_main` — vendaval: cordas em rajadas, metais curtos e assobio de vento no tempo forte
- **Condição de conclusão:** Tocar a bandeira em x5850.
- **Critérios de teste:**
  - validate_level e validate_campaign sem erros (schema, espécies, bioma, ordem de introdução, warps com chão)
  - route_bot conclui a fase partindo do spawn e de cada um dos 2 checkpoint(s), com inimigos e perigos ativos
  - vãos obrigatórios ≤ 160 u na mesma altura e subidas obrigatórias ≤ 64 u, simulados nas duas alturas do jogador sem coyote nem buffer
  - as 3 relíquias e todas as moedas são alcançáveis (rota de teste dedicada por relíquia; nenhuma moeda leva a morte)
  - estreias (Balão-Espinho) em chão plano com ≥ 300 u de aproximação visível, recuo livre e nenhum vão letal a 200 u
  - teto sobre patrulha: nenhum sólido não semissólido com base entre y_chão−158 e y_chão−30 sobre a patrulha de inimigo terrestre a menos de 160 u de um vão obrigatório
  - zona segura de cada checkpoint: chão plano de x−96 a x+192 e nenhum inimigo comum alcança [x−160, x+320] em 3 s de simulação
  - todo vão obrigatório é vencível com a rajada contrária ativa (força 180 vs. corrida 340) ou tem calmaria ≥ 2 s
  - cada rajada tem indicador visual ≥ 1 s antes
  - balões nunca derivam para dentro de um checkpoint
  - o vão de 160 u do vendaval cruzado é vencível sem a rajada a favor
- **Requisitos de motor:** nenhum (implementável com o motor atual)

### 7-5 · Agulha da Tempestade (`storm_spire`)

*Ideia própria:* a corrente central só liga entre os trovões.

- **Identificador:** `storm_spire`
- **Nome:** Agulha da Tempestade
- **Mundo:** Arquipélago Celeste (`sky_archipelago`, bioma `sky`), fase 5 de 6 — origem: nova
- **Objetivo:** Desafio avançado: escalar a agulha de pedra durante a tempestade combinando correntes ascendentes, vendavais, para-raios eletrificados, nuvens frágeis e todos os habitantes do céu.
- **Tema visual:** Agulha de pedra escura em espiral, para-raios de cobre, nuvens de chumbo, chuva oblíqua, relâmpagos iluminando a cena por um instante, ninhos abandonados.
- **Mecânica principal:** Corrente ascendente central intermitente (período 5 s, duty 0,4) sincronizada com os trovões
- **Mecânicas secundárias:**
  - para-raios eletrificados (perigo electric estático)
  - vendavais laterais
  - nuvens frágeis
  - todos os inimigos do céu
- **Dificuldade:** 8/10
- **Duração planejada:** 130–260 s (primeira travessia → exploração completa)
- **Tamanho do cenário:** 4800 × 3240 u
  - `main` [sky] 0,0 4800×3240: espiral externa e poço central da agulha (base y≈3100, topo y≈200)
- **Caminho principal** (sequência de ensino):
  1. **Introdução** (Base) — Rampa da base com para-raios eletrificados ao lado do caminho (sem obrigação de passar perto).
  2. **Demonstração segura** (Volta 1) — Corrente central contínua demonstrada sobre um patamar; relâmpago ilumina o próximo trecho.
  3. **Primeiro desafio** (Volta 2) — Vendaval lateral + para-raios: o vento empurra na direção dos para-raios — esperar a calmaria.
  4. **Escalada** (Checkpoint 1) — Corrente central intermitente: entrar só depois do trovão (som) e sair antes de desligar.
  5. **Combinação** (Volta 3) — Nuvens frágeis + balões + pássaros + drones em sequência densa.
  6. **Reviravolta** (Checkpoint 2 — olho da agulha) — O poço central inteiro com a corrente intermitente; patamares laterais para esperar entre trovões.
  7. **Teste final** (Checkpoint 3 — topo) — Para-raios em espiral, vendaval e nuvem marota.
  8. **Recompensa** (Cume (y≈200)) — O céu abre acima da tempestade; bandeira em x4600.
- **Caminhos alternativos:**
  - Ninho abandonado na face norte (relíquia).
  - Sala do para-raios mestre (cano de cobre) (relíquia, estrela).
  - Desafio do relâmpago: atravessar o trecho escuro só com a luz dos relâmpagos (relíquia).
- **Inimigos permitidos:** `abutre_filhote` (Abutrinho), `drone_vigia` (Drone Vigia), `passaro_rajada` (Pássaro-Rajada), `nuvem_marota` (Nuvem Marota), `semente_espinho` (Semente-Espinho), `balao_espinho` (Balão-Espinho)
- **Quantidade planejada de inimigos:** 20–26 (chefes não contados)
- **Obstáculos:**
  - para-raios eletrificados
  - corrente intermitente
  - vendavais
  - nuvens frágeis
  - inimigos aéreos densos
- **Itens disponíveis:**
  - crescer: ? base
  - fogo: ? volta 1
  - estrela: sala do para-raios
  - coração: checkpoint 2
- **Segredos:**
  - `north_nest` (hidden_area) — pista: Penas brancas presas na chuva apontam para a face norte da agulha; recompensa: relíquia relic_nest
  - `master_rod` (warp_room) — pista: Cano de cobre faiscando com seta luminosa; recompensa: relíquia relic_rod e estrela
  - `lightning_dark` (optional_challenge) — pista: Trecho sem luz com moedas que só brilham nos relâmpagos; recompensa: relíquia relic_lightning
- **Colecionáveis:** ~120 moedas e 3 relíquias
- **Checkpoints:** 3
- **Eventos especiais:**
  - message (checkpoint 1): Biruta — “Depois do trovão a corrente sobe. Conte até dois e entre.”
  - lights (opcional): relâmpagos como flashes de luz no desafio escuro
- **Elementos animados:**
  - relâmpagos e chuva oblíqua
  - faíscas nos para-raios
  - corrente central visível (espiral de gotas)
  - nuvens de chumbo passando
- **Trilha sonora:** `sky_archipelago_storm` — tempestade: percussão pesada, cordas agitadas e trovões no compasso da corrente (sub-áreas: `sky_archipelago_main`)
- **Condição de conclusão:** Chegar ao cume e tocar a bandeira em x4600 (y≈200).
- **Critérios de teste:**
  - validate_level e validate_campaign sem erros (schema, espécies, bioma, ordem de introdução, warps com chão)
  - route_bot conclui a fase partindo do spawn e de cada um dos 3 checkpoint(s), com inimigos e perigos ativos
  - vãos obrigatórios ≤ 160 u na mesma altura e subidas obrigatórias ≤ 64 u, simulados nas duas alturas do jogador sem coyote nem buffer
  - as 3 relíquias e todas as moedas são alcançáveis (rota de teste dedicada por relíquia; nenhuma moeda leva a morte)
  - teto sobre patrulha: nenhum sólido não semissólido com base entre y_chão−158 e y_chão−30 sobre a patrulha de inimigo terrestre a menos de 160 u de um vão obrigatório
  - zona segura de cada checkpoint: chão plano de x−96 a x+192 e nenhum inimigo comum alcança [x−160, x+320] em 3 s de simulação
  - o trovão (áudio + flash) acontece ≥ 0,8 s antes de a corrente central ligar
  - nenhum vendaval empurra para dentro de para-raios sem calmaria ≥ 1,5 s
  - sem a máscara de luz o desafio escuro continua completável
  - o bot conclui partindo dos 3 checkpoints
- **Requisitos de motor:** 
  - não bloqueia — lights (extensão): a máscara de escuridão das zonas dark com o halo de Lume (120 u; 64 u correndo) já é desenhada; faltam lanternas fixas e acendíveis com raio e duração e o evento lights global (apagar/acender) (opcional: só o desafio do relâmpago)

### 7-6 · Ninho do Grifo (`griffin_aerie`)

*Ideia própria:* a grifa só é vencida por quem está acima dela.

- **Identificador:** `griffin_aerie`
- **Nome:** Ninho do Grifo
- **Mundo:** Arquipélago Celeste (`sky_archipelago`, bioma `sky`), fase 6 de 6 — origem: nova
- **Objetivo:** Fortaleza do Arquipélago Celeste: subir as muralhas de galhos do ninho combinando tudo do céu e derrotar a Grifa Ventania usando correntes ascendentes para ficar acima dela.
- **Tema visual:** Ninho colossal de galhos e penas sobre a ilha mais alta, ruínas de uma fortaleza celeste com arcos quebrados, penas douradas ao vento, pôr do sol rosado e dourado.
- **Mecânica principal:** Muralhas de galhos semissólidos e correntes ascendentes entre plataformas, em arena vertical
- **Mecânicas secundárias:**
  - vendavais
  - nuvens-mola e nuvens frágeis
  - inimigos do céu em ninhos
  - chefe planejado Grifa Ventania
- **Dificuldade:** 8/10
- **Duração planejada:** 160–320 s (primeira travessia → exploração completa)
- **Tamanho do cenário:** 6000 × 2160 u
  - `main` [sky] 0,0 1400×1080: ilha de acesso
  - `ramparts` [fortress] 1400,0 3600×2160: muralhas de galhos e ruínas celestes
  - `nest` [fortress] 5000,0 1000×1620: ninho (arena vertical)
- **Caminho principal** (sequência de ensino):
  1. **Introdução** (0–700 u) — Ilha de acesso: corrente ascendente até a primeira muralha de galhos.
  2. **Demonstração segura** (700–1400 u) — Galhos semissólidos em escada com penas soltas caindo (decorativas).
  3. **Primeiro desafio** (1400–2200 u) — Ruínas celestes: pássaros-rajada em ninhos nas ameias e balões.
  4. **Escalada** (2200–3000 u) — Checkpoint x2200; vendavais nos arcos quebrados + nuvens frágeis.
  5. **Combinação** (3000–3800 u) — Torre de ninhos: subir com nuvens-mola enquanto drones e nuvens marotas atacam.
  6. **Reviravolta** (3800–4600 u) — A fortaleza desaba em pedaços flutuantes (plataformas que descem lentamente) — continuar subindo nelas.
  7. **Teste final** (4600–5000 u) — Checkpoint x4700 com coração; Biruta avisa sobre a grifa.
  8. **Recompensa** (5000–6000 u) — Ninho: Grifa Ventania (6 PV); vitória deixa uma pena-farol; bandeira em x5850 (topo).
- **Caminhos alternativos:**
  - Ninho de ovos dourados numa ameia lateral (relíquia).
  - Sala do trono celeste em ruínas (cano) (relíquia, estrela).
  - Desafio das penas: pegar 5 penas douradas caindo antes que sumam (relíquia).
- **Inimigos permitidos:** `abutre_filhote` (Abutrinho), `drone_vigia` (Drone Vigia), `passaro_rajada` (Pássaro-Rajada), `nuvem_marota` (Nuvem Marota), `semente_espinho` (Semente-Espinho), `balao_espinho` (Balão-Espinho), `boss:grifa_ventania` (Grifa Ventania (chefe planejado))
- **Quantidade planejada de inimigos:** 18–24 (chefes não contados)
- **Obstáculos:**
  - vazio vertical
  - vendavais
  - pedaços flutuantes que descem
  - ataques aéreos
- **Itens disponíveis:**
  - crescer: ? x500
  - fogo: ? x2300
  - estrela: sala do trono celeste
  - coração: antessala x4750
- **Segredos:**
  - `golden_eggs` (high_route) — pista: Brilho de ovos dourados numa ameia, com penas apontando; recompensa: relíquia relic_eggs
  - `sky_throne` (warp_room) — pista: Arco quebrado com cano coberto de hera celeste e luz dourada; recompensa: relíquia relic_throne e estrela
  - `feather_catch` (optional_challenge) — pista: Cinco penas douradas caindo devagar de um ninho vazio; recompensa: relíquia relic_feathers
- **Colecionáveis:** ~110 moedas e 3 relíquias
- **Checkpoints:** 2
- **Eventos especiais:**
  - boss_arena (x5000): trava a câmera vertical no ninho e fecha a passagem de galhos
  - message (x4700): Biruta — “A grifa só abaixa a guarda quando está por baixo de você.”
- **Elementos animados:**
  - penas caindo e girando
  - galhos do ninho rangendo
  - pedaços da fortaleza flutuando
  - grifa batendo as asas (rajadas visíveis)
- **Trilha sonora:** `sky_archipelago_fortress` — ninho: fanfarra de metais, tambores e coro aéreo; tema do chefe com cordas em espiral (sub-áreas: `sky_archipelago_boss`)
- **Condição de conclusão:** Derrotar a Grifa Ventania (6 PV) e tocar a bandeira em x5850.
- **Critérios de teste:**
  - validate_level e validate_campaign sem erros (schema, espécies, bioma, ordem de introdução, warps com chão)
  - route_bot conclui a fase partindo do spawn e de cada um dos 2 checkpoint(s), com inimigos e perigos ativos
  - vãos obrigatórios ≤ 160 u na mesma altura e subidas obrigatórias ≤ 64 u, simulados nas duas alturas do jogador sem coyote nem buffer
  - as 3 relíquias e todas as moedas são alcançáveis (rota de teste dedicada por relíquia; nenhuma moeda leva a morte)
  - teto sobre patrulha: nenhum sólido não semissólido com base entre y_chão−158 e y_chão−30 sobre a patrulha de inimigo terrestre a menos de 160 u de um vão obrigatório
  - zona segura de cada checkpoint: chão plano de x−96 a x+192 e nenhum inimigo comum alcança [x−160, x+320] em 3 s de simulação
  - na arena sempre existe corrente ascendente ou mola que coloca Lume acima do poleiro da grifa
  - pedaços flutuantes descem devagar (≤ 40 u/s) e nunca esmagam contra o teto
  - o bot vence o chefe partindo do checkpoint da antessala
  - nenhum vendaval cobre a antessala
- **Requisitos de motor:** 
  - **bloqueia** — comportamento do chefe planejado Grifa Ventania (grifa_ventania): família nova em lume/core/behaviors/bosses.py

## Mundo 8 — Pântano Assombrado (`haunted_swamp`)

Névoa, lanternas e casarões afundados. A luz vira mecânica: o halo de Lume paralisa as sombras (e encolhe quando ele corre), as lanternas mudam o caminho e, no fim, só duas lanternas acesas tornam a sombra sólida. Detalhes do mundo em [`MUNDO_08.md`](MUNDO_08.md).

### 8-1 · Brejo da Névoa (`misty_marsh`)

*Ideia própria:* o trecho que exige correr encolhe o halo e deixa as sombras chegarem.

- **Identificador:** `misty_marsh`
- **Nome:** Brejo da Névoa
- **Mundo:** Pântano Assombrado (`haunted_swamp`, bioma `swamp`), fase 1 de 6 — origem: nova
- **Objetivo:** Apresentar o pântano: passarelas e vitórias-régias sobre lodo venenoso e água funda, o Sapo-do-Lodo e a Sombra-Errante, que deriva na direção de Lume no escuro e paralisa dentro do halo da lanterna.
- **Tema visual:** Brejo enevoado ao fim da tarde: passarelas de tábuas, vitórias-régias gigantes, juncos, árvores retorcidas com barba-de-velho, lampiões âmbar e névoa lilás em camadas.
- **Mecânica principal:** Halo da lanterna: a Sombra-Errante paralisa (e fica inofensiva) dentro do halo de Lume — 120 u andando, 64 u correndo
- **Mecânicas secundárias:**
  - Sapo-do-Lodo (agacha, infla a garganta e salta)
  - vitórias-régias balançando
  - lodo venenoso (fere sem matar) e água funda (letal)
  - passarelas frágeis
- **Dificuldade:** 6/10
- **Duração planejada:** 90–180 s (primeira travessia → exploração completa)
- **Tamanho do cenário:** 5400 × 1080 u
  - `main` [swamp] 0,0 5400×1080: brejo com passarelas em y≈600 e lodo em y≈700
- **Caminho principal** (sequência de ensino):
  1. **Introdução** (0–700 u) — Passarela larga sobre o brejo; lodo venenoso ao lado com bolhas roxas (tocar fere, não mata).
  2. **Demonstração segura** (700–1300 u) — Vitórias-régias balançando sobre lodo raso (cair = dano leve e degraus de saída).
  3. **Primeiro desafio** (1300–2000 u) — Sapo-do-Lodo (estreia) num banco de lama plano: agacha e infla a garganta antes de saltar — pisar.
  4. **Escalada** (2000–2800 u) — Checkpoint x2000 (Lírio acende o lampião); Sombra-Errante (estreia) numa passarela larga e plana: andando, o halo a paralisa a 120 u; passar devagar ao lado dela (ou dissipá-la com fogo).
  5. **Combinação** (2800–3600 u) — Sapos + flores-mordedoras nas moitas + vitórias-régias sobre água funda (letal).
  6. **Reviravolta** (3600–4300 u) — Passarelas frágeis exigem correr, e correr encolhe o halo para 64 u — duas sombras se aproximam enquanto Lume corre; escolher onde andar e onde correr; estrela no meio do trecho.
  7. **Teste final** (4300–5000 u) — Checkpoint x4300; passarelas frágeis + sapos + Sombra-Errante atrás.
  8. **Recompensa** (5000–5400 u) — Ponte coberta iluminada por lanternas e bandeira em x5250.
- **Caminhos alternativos:**
  - Copa de uma árvore retorcida pela barba-de-velho (semissólidos) (relíquia).
  - Barco afundado (cano no casco) → sala submersa sem inimigos (relíquia, estrela).
  - Desafio das vitórias-régias: 8 folhas sobre água funda sem tocar o lodo (relíquia).
- **Inimigos permitidos:** `flor_mordedora` (Flor-Mordedora), `cogumelo_saltitante` (Cogumelo Saltitante), `mariposa_lume` (Mariposa-Lume), `planta_esporos` (Planta-de-Esporos), `aranha_cipo` (Aranha-do-Cipó), `assombracao_timida` (Sombra-Errante — estreia), `sapo_lodo` (Sapo-do-Lodo — estreia)
- **Quantidade planejada de inimigos:** 12–16 (chefes não contados)
- **Obstáculos:**
  - lodo venenoso
  - água funda
  - vitórias-régias balançando
  - passarelas frágeis
  - sombras que se aproximam quando Lume corre
- **Itens disponíveis:**
  - crescer: ? x400
  - fogo: ? x2100
  - estrela: ? x3900 (no trecho das duas sombras)
  - coração: barco afundado
- **Segredos:**
  - `twisted_tree` (high_route) — pista: Barba-de-velho forma uma escada até uma coruja de pedra no topo da árvore; recompensa: relíquia relic_tree
  - `sunken_boat` (warp_room) — pista: Casco de barco virado com uma lanterna acesa dentro; recompensa: relíquia relic_boat e coração
  - `lily_run` (optional_challenge) — pista: Oito vitórias-régias floridas em fila sobre água funda; recompensa: relíquia relic_lily
- **Colecionáveis:** ~85 moedas e 3 relíquias
- **Checkpoints:** 2
- **Eventos especiais:**
  - message (x2000): Lírio — “Ande devagar perto das sombras: dentro da sua luz elas param. Correndo, a luz encolhe.”
- **Elementos animados:**
  - névoa em camadas (fundo e frente) com alfa limitado
  - bolhas roxas no lodo
  - Sombra-Errante congelando em fiapos quando o halo a alcança
  - sapo inflando a garganta
  - vaga-lumes e lampiões
- **Trilha sonora:** `haunted_swamp_main` — brejo: banjo desafinado de leve, sanfona lenta e coaxar no contratempo
- **Condição de conclusão:** Tocar a bandeira em x5250.
- **Critérios de teste:**
  - validate_level e validate_campaign sem erros (schema, espécies, bioma, ordem de introdução, warps com chão)
  - route_bot conclui a fase partindo do spawn e de cada um dos 2 checkpoint(s), com inimigos e perigos ativos
  - vãos obrigatórios ≤ 160 u na mesma altura e subidas obrigatórias ≤ 64 u, simulados nas duas alturas do jogador sem coyote nem buffer
  - as 3 relíquias e todas as moedas são alcançáveis (rota de teste dedicada por relíquia; nenhuma moeda leva a morte)
  - estreias (Sombra-Errante, Sapo-do-Lodo) em chão plano com ≥ 300 u de aproximação visível, recuo livre e nenhum vão letal a 200 u
  - teto sobre patrulha: nenhum sólido não semissólido com base entre y_chão−158 e y_chão−30 sobre a patrulha de inimigo terrestre a menos de 160 u de um vão obrigatório
  - zona segura de cada checkpoint: chão plano de x−96 a x+192 e nenhum inimigo comum alcança [x−160, x+320] em 3 s de simulação
  - a Sombra-Errante paralisa dentro do halo (120 u andando, 64 u correndo) e só fere em movimento
  - lodo venenoso nunca é letal e sempre tem saída a ≤ 120 u
  - estreias do sapo e da Sombra-Errante em chão plano com recuo
  - o bot conclui partindo dos 2 checkpoints
- **Requisitos de motor:** nenhum (implementável com o motor atual)

### 8-2 · Charco das Lanternas (`lantern_bog`)

*Ideia própria:* lanternas-boia são o único caminho sobre a poça escura.

- **Identificador:** `lantern_bog`
- **Nome:** Charco das Lanternas
- **Mundo:** Pântano Assombrado (`haunted_swamp`, bioma `swamp`), fase 2 de 6 — origem: nova
- **Objetivo:** Explorar o charco seguindo lanternas: o caminho principal é marcado por luz âmbar, as rotas paralelas por lanternas apagadas; conhecer a Mão-do-Lodo, que sobe de poças escuras.
- **Tema visual:** Charco ao crepúsculo com postes de lanterna tortos, poças pretas espelhadas, passarelas em dois níveis, cabanas sobre palafitas, salgueiros; lanternas flutuando em boias.
- **Mecânica principal:** Lanternas como guia (luz âmbar = chão seguro) e rotas paralelas em dois níveis
- **Mecânicas secundárias:**
  - Mão-do-Lodo (sobe de poças escuras; só fogo ou estrela)
  - lanternas-boia (plataformas que balançam)
  - aranhas e mariposas na passarela alta
  - zonas dark opcionais
- **Dificuldade:** 7/10
- **Duração planejada:** 110–220 s (primeira travessia → exploração completa)
- **Tamanho do cenário:** 5800 × 1620 u
  - `main` [swamp] 0,0 5800×1620: passarela alta (y≈500) e trilha do lodo (y≈1100)
- **Caminho principal** (sequência de ensino):
  1. **Introdução** (0–700 u) — Charco com postes de lanterna ao longo do caminho; uma lanterna apagada aponta para a trilha de baixo.
  2. **Demonstração segura** (700–1300 u) — Mão-do-Lodo (estreia) numa poça escura isolada em chão firme: sobe (2,0 s escondida / 1,4 s fora), agarra o ar e afunda — contornar ou usar fogo.
  3. **Primeiro desafio** (1300–2000 u) — Passarela entre três poças com mãos em ritmo alternado.
  4. **Escalada** (2000–2800 u) — Checkpoint x2000; bifurcação: passarela alta (aranhas, mariposas, vãos) ou trilha do lodo (mãos, sapos, lodo venenoso); reencontro em x2800.
  5. **Combinação** (2800–3600 u) — Sombras + mãos: esperar o ritmo da mão parado (halo cheio, sombras paralisadas) em vez de correr.
  6. **Reviravolta** (3600–4300 u) — Lanternas-boia (moving eixo y) são o único caminho sobre uma poça escura funda — a luz delas é o chão.
  7. **Teste final** (4300–5300 u) — Checkpoint x4300; teste com as duas rotas fundidas: passarelas frágeis, mãos e sapos.
  8. **Recompensa** (5300–5800 u) — Cabana do lanterneiro sobre palafitas e bandeira em x5650.
- **Caminhos alternativos:**
  - Passarela alta (aranhas, mariposas, mais moedas).
  - Trilha do lodo (mãos, sapos, menos vãos).
  - Lanterna apagada no salgueiro: acima dela, uma rota de galhos (relíquia).
- **Inimigos permitidos:** `flor_mordedora` (Flor-Mordedora), `cogumelo_saltitante` (Cogumelo Saltitante), `mariposa_lume` (Mariposa-Lume), `planta_esporos` (Planta-de-Esporos), `aranha_cipo` (Aranha-do-Cipó), `assombracao_timida` (Sombra-Errante), `sapo_lodo` (Sapo-do-Lodo), `mao_lodo` (Mão-do-Lodo — estreia)
- **Quantidade planejada de inimigos:** 16–20 (chefes não contados)
- **Obstáculos:**
  - mãos em ritmo
  - lodo venenoso
  - poça escura funda (letal)
  - lanternas-boia balançando
- **Itens disponíveis:**
  - fogo: ? x500 (antes da primeira mão)
  - crescer: ? x1500
  - estrela: salgueiro
  - coração: checkpoint 2
- **Segredos:**
  - `willow_route` (high_route) — pista: Lanterna apagada pendurada num salgueiro; galhos formam degraus acima dela; recompensa: relíquia relic_willow e estrela
  - `stilt_cellar` (warp_room) — pista: Alçapão sob uma cabana de palafita com luz âmbar pelas frestas; recompensa: relíquia relic_cellar
  - `hand_dance` (optional_challenge) — pista: Cinco poças em fila com mãos em ritmo crescente e moedas sobre cada poça; recompensa: relíquia relic_hands
- **Colecionáveis:** ~100 moedas e 3 relíquias
- **Checkpoints:** 2
- **Eventos especiais:**
  - message (x2000): Lírio — “Luz âmbar é chão seguro. Sempre.”
  - lights (opcional): lanternas como fontes de luz no trecho das lanternas-boia
- **Elementos animados:**
  - lanternas balançando e chamas tremendo
  - mãos de lodo subindo com respingos
  - reflexos nas poças pretas
  - salgueiros com barba-de-velho
- **Trilha sonora:** `haunted_swamp_main` — crepúsculo: violino solo, sanfona e sinos de vento; percussão de gotas (sub-áreas: `haunted_swamp_underground`)
- **Condição de conclusão:** Tocar a bandeira em x5650.
- **Critérios de teste:**
  - validate_level e validate_campaign sem erros (schema, espécies, bioma, ordem de introdução, warps com chão)
  - route_bot conclui a fase partindo do spawn e de cada um dos 2 checkpoint(s), com inimigos e perigos ativos
  - vãos obrigatórios ≤ 160 u na mesma altura e subidas obrigatórias ≤ 64 u, simulados nas duas alturas do jogador sem coyote nem buffer
  - as 3 relíquias e todas as moedas são alcançáveis (rota de teste dedicada por relíquia; nenhuma moeda leva a morte)
  - estreias (Mão-do-Lodo) em chão plano com ≥ 300 u de aproximação visível, recuo livre e nenhum vão letal a 200 u
  - teto sobre patrulha: nenhum sólido não semissólido com base entre y_chão−158 e y_chão−30 sobre a patrulha de inimigo terrestre a menos de 160 u de um vão obrigatório
  - zona segura de cada checkpoint: chão plano de x−96 a x+192 e nenhum inimigo comum alcança [x−160, x+320] em 3 s de simulação
  - toda lanterna acesa marca chão seguro (nenhuma sobre perigo)
  - a mão não emerge com Lume a ≤ 42 u da poça (timidez padrão da família emerger) e mostra bolhas ≥ 0,5 s antes de subir
  - as duas rotas da bifurcação se reencontram e ambas são completáveis pelo bot
  - o bot conclui partindo dos 2 checkpoints
- **Requisitos de motor:** 
  - não bloqueia — lights (extensão): a máscara de escuridão das zonas dark com o halo de Lume (120 u; 64 u correndo) já é desenhada; faltam lanternas fixas e acendíveis com raio e duração e o evento lights global (apagar/acender) (opcional: sem a máscara a fase fica jogável e mais clara)

### 8-3 · Casarão Afundado (`sunken_mansion`)

*Ideia própria:* no salão de baile as ossadas se remontam no compasso da valsa.

- **Identificador:** `sunken_mansion`
- **Nome:** Casarão Afundado
- **Mundo:** Pântano Assombrado (`haunted_swamp`, bioma `swamp`), fase 3 de 6 — origem: nova
- **Objetivo:** Desafio de movimento dentro de um casarão meio afundado: salas ligadas por portas, pisos frágeis, salas alagadas e a Ossada do Pântano, que desmonta com o pisão e se remonta.
- **Tema visual:** Casarão vitoriano afundado e adernado: papel de parede descascado, retratos cujos olhos seguem Lume, lustres apagados, escadarias quebradas, biblioteca alagada, salão de baile com piano; velas âmbar.
- **Mecânica principal:** Ossadas que se remontam (pisão só desmonta por 4 s) em salas de piso frágil
- **Mecânicas secundárias:**
  - portas entre salas (canos com arte de porta)
  - salas alagadas (swim)
  - sombras-errantes atravessando paredes
  - mãos e sapos nas poças internas
- **Dificuldade:** 7/10
- **Duração planejada:** 120–240 s (primeira travessia → exploração completa)
- **Tamanho do cenário:** 5600 × 2160 u
  - `main` [swamp] 0,0 5600×2160: jardim, três andares do casarão, porão alagado e telhado
- **Caminho principal** (sequência de ensino):
  1. **Introdução** (0–700 u) — Jardim afundado com estátuas e o portão rangendo.
  2. **Demonstração segura** (700–1300 u) — Hall de entrada: piso de tábuas frágeis sobre o porão alagado (cair = nadar, não morrer).
  3. **Primeiro desafio** (1300–2000 u) — Ossada do Pântano (estreia) num corredor largo: o pisão a desmonta por 4 s e ela se remonta; passar enquanto está desmontada (casco ou estrela a derrotam).
  4. **Escalada** (2000–2800 u) — Checkpoint x2000; escadaria em ruínas (vertical) com sombras-errantes atravessando paredes.
  5. **Combinação** (2800–3600 u) — Biblioteca alagada: nado entre estantes semissólidas, mãos nas poças e sapos sobre as mesas.
  6. **Reviravolta** (3600–4300 u) — Salão de baile com piano tocando sozinho — as ossadas se remontam no compasso da valsa; atravessar entre os compassos.
  7. **Teste final** (4300–5100 u) — Checkpoint x4300; sótão com vigas frágeis e sombras-errantes.
  8. **Recompensa** (5100–5600 u) — Telhado com cata-vento torto e bandeira em x5450.
- **Caminhos alternativos:**
  - Retrato que pisca: porta secreta atrás do quadro (cano) (relíquia).
  - Lustre do salão: subir pelos lustres apagados (semissólidos) (relíquia).
  - Porão alagado completo: rota submersa alternativa ao hall (relíquia, estrela).
- **Inimigos permitidos:** `flor_mordedora` (Flor-Mordedora), `cogumelo_saltitante` (Cogumelo Saltitante), `mariposa_lume` (Mariposa-Lume), `planta_esporos` (Planta-de-Esporos), `aranha_cipo` (Aranha-do-Cipó), `assombracao_timida` (Sombra-Errante), `sapo_lodo` (Sapo-do-Lodo), `mao_lodo` (Mão-do-Lodo), `ossada_pantano` (Ossada do Pântano — estreia)
- **Quantidade planejada de inimigos:** 16–22 (chefes não contados)
- **Obstáculos:**
  - pisos frágeis
  - ossadas que voltam
  - salas alagadas
  - sombras-errantes através das paredes
- **Itens disponíveis:**
  - crescer: ? x400
  - fogo: ? x2100
  - estrela: porão alagado
  - coração: sótão
- **Segredos:**
  - `winking_portrait` (warp_room) — pista: Um retrato pisca quando o halo da lanterna de Lume o ilumina; recompensa: relíquia relic_portrait
  - `chandeliers` (high_route) — pista: Lustres apagados com uma vela ainda acesa no mais alto; recompensa: relíquia relic_chandelier
  - `flooded_cellar` (hidden_area) — pista: Bolhas sobem entre as tábuas do hall onde o piso é mais escuro; recompensa: relíquia relic_cellar e estrela
- **Colecionáveis:** ~100 moedas e 3 relíquias
- **Checkpoints:** 2
- **Eventos especiais:**
  - message (x2000): Lírio — “Osso desmontado volta a andar. Passe enquanto ele se procura.”
  - camera_lock (opcional) no salão de baile
- **Elementos animados:**
  - olhos dos retratos seguindo Lume
  - piano tocando sozinho
  - ossada desmontando e se remontando
  - velas tremulando
- **Trilha sonora:** `haunted_swamp_main` — casarão: valsa em caixa de música desafinada, cravo e coro distante (sub-áreas: `haunted_swamp_underground`)
- **Condição de conclusão:** Tocar a bandeira no telhado em x5450.
- **Critérios de teste:**
  - validate_level e validate_campaign sem erros (schema, espécies, bioma, ordem de introdução, warps com chão)
  - route_bot conclui a fase partindo do spawn e de cada um dos 2 checkpoint(s), com inimigos e perigos ativos
  - vãos obrigatórios ≤ 160 u na mesma altura e subidas obrigatórias ≤ 64 u, simulados nas duas alturas do jogador sem coyote nem buffer
  - as 3 relíquias e todas as moedas são alcançáveis (rota de teste dedicada por relíquia; nenhuma moeda leva a morte)
  - estreias (Ossada do Pântano) em chão plano com ≥ 300 u de aproximação visível, recuo livre e nenhum vão letal a 200 u
  - teto sobre patrulha: nenhum sólido não semissólido com base entre y_chão−158 e y_chão−30 sobre a patrulha de inimigo terrestre a menos de 160 u de um vão obrigatório
  - zona segura de cada checkpoint: chão plano de x−96 a x+192 e nenhum inimigo comum alcança [x−160, x+320] em 3 s de simulação
  - a ossada desmontada é intangível e se remonta em 4 s sem prender o jogador
  - salas alagadas têm saída a ≤ 400 u de nado
  - estreia da ossada em corredor largo com recuo
  - o bot conclui partindo dos 2 checkpoints
- **Requisitos de motor:** nenhum (implementável com o motor atual)

### 8-4 · Apagão no Pântano (`lights_out`)

*Ideia própria:* o vento apaga todas as lanternas e só as mariposas iluminam.

- **Identificador:** `lights_out`
- **Nome:** Apagão no Pântano
- **Mundo:** Pântano Assombrado (`haunted_swamp`, bioma `swamp`), fase 4 de 6 — origem: nova
- **Objetivo:** Mecânica especial do Pântano Assombrado: atravessar a noite fechada com a pequena luz de Lume, acendendo lanternas que ampliam a visão por tempo limitado e paralisam as sombras.
- **Tema visual:** Noite sem lua no pântano: só a luz de Lume (raio pequeno), lanternas âmbar, olhos brilhando no escuro, bolhas fosforescentes no lodo e mariposas luminosas.
- **Mecânica principal:** Escuridão com raio de visão (zonas dark) e lanternas acendíveis por toque (evento lights, 15–20 s de luz)
- **Mecânicas secundárias:**
  - moedas e bolhas luminosas como trilha
  - sombras-errantes paralisam no halo de Lume e na luz das lanternas (extensão)
  - mariposas-lume como fontes de luz móveis
  - mãos e ossadas no escuro
- **Dificuldade:** 7/10
- **Duração planejada:** 110–220 s (primeira travessia → exploração completa)
- **Tamanho do cenário:** 5400 × 1620 u
  - `main` [swamp] 0,0 5400×1620: pântano noturno inteiro coberto por zona dark
- **Caminho principal** (sequência de ensino):
  1. **Introdução** (0–700 u) — O pântano escurece; Lume tem luz própria (raio 120 u); primeira lanterna acende ao toque e ilumina 220 u por 20 s.
  2. **Demonstração segura** (700–1300 u) — Moedas e bolhas brilham no escuro como trilha; chão firme e sem inimigos.
  3. **Primeiro desafio** (1300–2000 u) — No escuro, só o halo de Lume (120 u) paralisa as sombras; uma lanterna acesa amplia a área segura — correr encolhe o halo e as sombras avançam.
  4. **Escalada** (2000–2800 u) — Checkpoint x2000 (o lampião do checkpoint fica sempre aceso); lanternas temporizadas de 15 s em sequência ao longo de uma passarela.
  5. **Combinação** (2800–3600 u) — Mãos visíveis só pelo brilho das bolhas e ossadas no escuro.
  6. **Reviravolta** (3600–4300 u) — Um vento apaga todas as lanternas; só as Mariposas-Lume iluminam — seguir (sem tocar) as inimigas como luz.
  7. **Teste final** (4300–5000 u) — Checkpoint x4300; teste final: lanternas espaçadas, sapos e sombras-errantes.
  8. **Recompensa** (5000–5400 u) — Amanhecer: a escuridão se desfaz e bandeira em x5250.
- **Caminhos alternativos:**
  - Lanterna escondida que ilumina permanentemente uma rota alta (relíquia).
  - Toca de vaga-lumes (cano) com luz plena (relíquia, estrela).
  - Desafio da escuridão: trecho sem lanternas guiado só pelo som (relíquia).
- **Inimigos permitidos:** `flor_mordedora` (Flor-Mordedora), `cogumelo_saltitante` (Cogumelo Saltitante), `mariposa_lume` (Mariposa-Lume), `planta_esporos` (Planta-de-Esporos), `aranha_cipo` (Aranha-do-Cipó), `assombracao_timida` (Sombra-Errante), `sapo_lodo` (Sapo-do-Lodo), `mao_lodo` (Mão-do-Lodo), `ossada_pantano` (Ossada do Pântano)
- **Quantidade planejada de inimigos:** 14–20 (chefes não contados)
- **Obstáculos:**
  - escuridão (raio de visão de 120 u)
  - lanternas temporizadas
  - mãos e ossadas no escuro
  - água funda
- **Itens disponíveis:**
  - fogo: ? x500 (a chama também ilumina)
  - crescer: ? x1500
  - estrela: toca de vaga-lumes
  - coração: checkpoint 2
- **Segredos:**
  - `eternal_lantern` (high_route) — pista: Uma lanterna verde (diferente das âmbar) pisca no alto, fora do caminho; recompensa: relíquia relic_lantern
  - `firefly_den` (warp_room) — pista: Cano coberto de musgo com luz verde saindo; recompensa: relíquia relic_den e estrela
  - `dark_run` (optional_challenge) — pista: Placa de Lírio: 'feche os olhos e escute'; coaxar marca o caminho; recompensa: relíquia relic_dark
- **Colecionáveis:** ~90 moedas e 3 relíquias
- **Checkpoints:** 2
- **Eventos especiais:**
  - lights (vários): lanternas acendíveis com params {radius: 220, duration: 15–20}
  - lights (x3600): rajada que apaga todas as lanternas (evento global)
  - message (x2000): Lírio — “A luz da lanterna espanta fantasma. Acenda e corra.”
- **Elementos animados:**
  - máscara de escuridão com borda suave
  - lanternas acendendo e apagando com fumaça
  - olhos brilhando no escuro
  - mariposas deixando rastro de luz
- **Trilha sonora:** `haunted_swamp_dark` — noite fechada: drone grave, sinos esparsos e coro sussurrado; a melodia volta quando uma lanterna acende (sub-áreas: `haunted_swamp_main`)
- **Condição de conclusão:** Tocar a bandeira em x5250 ao amanhecer.
- **Critérios de teste:**
  - validate_level e validate_campaign sem erros (schema, espécies, bioma, ordem de introdução, warps com chão)
  - route_bot conclui a fase partindo do spawn e de cada um dos 2 checkpoint(s), com inimigos e perigos ativos
  - vãos obrigatórios ≤ 160 u na mesma altura e subidas obrigatórias ≤ 64 u, simulados nas duas alturas do jogador sem coyote nem buffer
  - as 3 relíquias e todas as moedas são alcançáveis (rota de teste dedicada por relíquia; nenhuma moeda leva a morte)
  - teto sobre patrulha: nenhum sólido não semissólido com base entre y_chão−158 e y_chão−30 sobre a patrulha de inimigo terrestre a menos de 160 u de um vão obrigatório
  - zona segura de cada checkpoint: chão plano de x−96 a x+192 e nenhum inimigo comum alcança [x−160, x+320] em 3 s de simulação
  - todo salto obrigatório tem o pouso dentro do raio de luz de Lume ou de uma lanterna ativa
  - nenhum inimigo invisível ataca sem aviso sonoro ou brilho
  - o lampião do checkpoint nunca se apaga
  - o bot conclui com a máscara ativa partindo dos 2 checkpoints
- **Requisitos de motor:** 
  - **bloqueia** — lights (extensão): a máscara de escuridão das zonas dark com o halo de Lume (120 u; 64 u correndo) já é desenhada; faltam lanternas fixas e acendíveis com raio e duração e o evento lights global (apagar/acender)

### 8-5 · Lodaçal Fantasma (`phantom_mire`)

*Ideia própria:* a ponte fantasma só existe enquanto a sombra-guardiã está paralisada no halo.

- **Identificador:** `phantom_mire`
- **Nome:** Lodaçal Fantasma
- **Mundo:** Pântano Assombrado (`haunted_swamp`, bioma `swamp`), fase 5 de 6 — origem: nova
- **Objetivo:** Desafio avançado: atravessar o lodaçal combinando lodo movediço, névoa densa, sombras-errantes, mãos, ossadas e trechos escuros.
- **Tema visual:** Lodaçal sob lua minguante com névoa densa, troncos podres, lápides afundadas, ponte fantasmagórica translúcida, fogo-fátuo azul.
- **Mecânica principal:** Lodo movediço (quicksand: afunda devagar, pulo reduzido) entre ilhas de troncos
- **Mecânicas secundárias:**
  - ponte fantasma (plataformas semissólidas visíveis só como contorno)
  - névoa densa em primeiro plano
  - todos os assombros do mundo
  - trechos escuros
- **Dificuldade:** 8/10
- **Duração planejada:** 130–260 s (primeira travessia → exploração completa)
- **Tamanho do cenário:** 6200 × 1620 u
  - `main` [swamp] 0,0 6200×1620: lodaçal com ilhas de troncos e cemitério afundado
- **Caminho principal** (sequência de ensino):
  1. **Introdução** (0–700 u) — Primeira faixa de lodo movediço rasa entre troncos firmes: afundar e sair saltando.
  2. **Demonstração segura** (700–1300 u) — Lodo movediço largo com fundo firme; sapos saltando de tronco em tronco.
  3. **Primeiro desafio** (1300–2000 u) — Mãos subindo do lodo movediço: não ficar parado no lodo nem perto das bolhas.
  4. **Escalada** (2000–2800 u) — Checkpoint x2000; cemitério afundado com ossadas, lápides como degraus e sombras-errantes.
  5. **Combinação** (2800–3600 u) — Névoa densa em primeiro plano + aranhas + lodo: a leitura depende de sombras e sons.
  6. **Reviravolta** (3600–4400 u) — A ponte fantasma é feita de contornos que só ficam sólidos enquanto a sombra que a guarda está paralisada no halo de Lume — atravessar andando, sem correr, mantendo a sombra a ≤ 120 u.
  7. **Teste final** (4400–5700 u) — Checkpoint x4400; teste: lodo, mãos, ossadas e um trecho escuro com fogos-fátuos.
  8. **Recompensa** (5700–6200 u) — Capela em ruínas com a torre do lanterneiro ao fundo; bandeira em x6050.
- **Caminhos alternativos:**
  - Lápide mais alta do cemitério (relíquia).
  - Cripta (cano) → ossário com moedas (relíquia, estrela).
  - Travessia do lodo sem tocar o lodo, pelos troncos que afundam (relíquia).
- **Inimigos permitidos:** `flor_mordedora` (Flor-Mordedora), `cogumelo_saltitante` (Cogumelo Saltitante), `mariposa_lume` (Mariposa-Lume), `planta_esporos` (Planta-de-Esporos), `aranha_cipo` (Aranha-do-Cipó), `assombracao_timida` (Sombra-Errante), `sapo_lodo` (Sapo-do-Lodo), `mao_lodo` (Mão-do-Lodo), `ossada_pantano` (Ossada do Pântano)
- **Quantidade planejada de inimigos:** 20–26 (chefes não contados)
- **Obstáculos:**
  - lodo movediço (afundar por completo mata)
  - névoa densa
  - ponte fantasma condicional
  - mãos, ossadas e sombras-errantes
  - trecho escuro
- **Itens disponíveis:**
  - fogo: ? x500
  - crescer: ? x1700
  - estrela: cripta
  - coração: checkpoint 2
- **Segredos:**
  - `tall_tomb` (high_route) — pista: A lápide mais alta tem uma lanterna âmbar e moedas em diagonal; recompensa: relíquia relic_tomb
  - `crypt` (warp_room) — pista: Portão de cripta entreaberto com cano escuro e luz azul; recompensa: relíquia relic_crypt e estrela
  - `log_crossing` (optional_challenge) — pista: Troncos afundando em sequência sobre o lodo com moedas em cima; recompensa: relíquia relic_logs
- **Colecionáveis:** ~110 moedas e 3 relíquias
- **Checkpoints:** 2
- **Eventos especiais:**
  - message (x2000): Lírio — “Mão de lodo não gosta de fogo.”
  - lights (x4400–5700): trecho escuro com fogos-fátuos como fontes de luz
  - evento da ponte fantasma: plataformas switch ativas só enquanto a sombra-guardiã está no estado 'freeze' (requer ligação comportamento→grupo de switch)
- **Elementos animados:**
  - lodo borbulhando e afundando
  - fogos-fátuos azuis
  - ponte fantasma piscando entre contorno e sólido
  - névoa em primeiro plano
- **Trilha sonora:** `haunted_swamp_main` — lodaçal: contrabaixo arrastado, theremin original e coro grave (sub-áreas: `haunted_swamp_dark`, `haunted_swamp_underground`)
- **Condição de conclusão:** Tocar a bandeira em x6050.
- **Critérios de teste:**
  - validate_level e validate_campaign sem erros (schema, espécies, bioma, ordem de introdução, warps com chão)
  - route_bot conclui a fase partindo do spawn e de cada um dos 2 checkpoint(s), com inimigos e perigos ativos
  - vãos obrigatórios ≤ 160 u na mesma altura e subidas obrigatórias ≤ 64 u, simulados nas duas alturas do jogador sem coyote nem buffer
  - as 3 relíquias e todas as moedas são alcançáveis (rota de teste dedicada por relíquia; nenhuma moeda leva a morte)
  - teto sobre patrulha: nenhum sólido não semissólido com base entre y_chão−158 e y_chão−30 sobre a patrulha de inimigo terrestre a menos de 160 u de um vão obrigatório
  - zona segura de cada checkpoint: chão plano de x−96 a x+192 e nenhum inimigo comum alcança [x−160, x+320] em 3 s de simulação
  - do lodo movediço sai-se em ≤ 2 pulos reduzidos antes de afundar por completo; troncos firmes a ≤ 120 u
  - a ponte fantasma só some com aviso de 0,5 s e nunca derruba o jogador no lodo profundo sem chão
  - a névoa frontal nunca esconde o jogador por mais de 1 s
  - o bot conclui partindo dos 2 checkpoints
- **Requisitos de motor:** 
  - **bloqueia** — toggle_switch (extensão): a alternância por bloco 'toggle' já existe (Game.toggle_group); faltam o evento toggle_switch por gatilho, o interruptor temporizado e a ligação do grupo a outros sistemas (esteiras, plataformas fantasmas) (ponte fantasma ligada ao estado 'freeze' da sombra-guardiã)
  - não bloqueia — lights (extensão): a máscara de escuridão das zonas dark com o halo de Lume (120 u; 64 u correndo) já é desenhada; faltam lanternas fixas e acendíveis com raio e duração e o evento lights global (apagar/acender) (opcional)

### 8-6 · Torre do Lanterneiro (`lantern_keep`)

*Ideia própria:* o contrapeso da grande lanterna vira elevador.

- **Identificador:** `lantern_keep`
- **Nome:** Torre do Lanterneiro
- **Mundo:** Pântano Assombrado (`haunted_swamp`, bioma `swamp`), fase 6 de 6 — origem: nova
- **Objetivo:** Fortaleza do Pântano Assombrado: subir a torre do lanterneiro tomada pelas sombras, usando os mecanismos de contrapeso, e derrotar o Vulto Apagador acendendo duas lanternas ao mesmo tempo.
- **Tema visual:** Torre de pedra escura com escada em caracol, engrenagens de contrapeso, correntes, lanternas apagadas em nichos, janelas com lua cheia, sombras com olhos; no topo, a grande lanterna apagada.
- **Mecânica principal:** Escada em caracol vertical com mecanismos de contrapeso (plataformas móveis) e lanternas que iluminam por tempo
- **Mecânicas secundárias:**
  - prensas de contrapeso e canhões na casa de máquinas (sub-área fortress)
  - escuridão parcial
  - todos os assombros do pântano
  - chefe planejado Vulto Apagador
- **Dificuldade:** 8/10
- **Duração planejada:** 170–330 s (primeira travessia → exploração completa)
- **Tamanho do cenário:** 5200 × 3240 u
  - `main` [swamp] 0,0 1400×1080: pátio da torre no pântano
  - `tower` [fortress] 1400,0 2800×3240: interior da torre e casa de máquinas
  - `lantern_room` [fortress] 4200,0 1000×1080: sala da grande lanterna (arena)
- **Caminho principal** (sequência de ensino):
  1. **Introdução** (Pátio (0–1400 u)) — Pátio enlameado com mãos e sapos; porta da torre iluminada por Lírio.
  2. **Demonstração segura** (Térreo da torre) — Escada em caracol (semissólidos) com sombras-errantes atravessando as paredes da torre.
  3. **Primeiro desafio** (Casa de máquinas) — Contrapesos (plataformas móveis verticais) e Prensas a Vapor como pesos (topo seguro); Canhão Sentinela na escada.
  4. **Escalada** (Checkpoint 1) — Andares escuros: lanternas temporizadas em nichos.
  5. **Combinação** (Biblioteca do lanterneiro) — Ossadas, aranhas e mariposas entre estantes.
  6. **Reviravolta** (Checkpoint 2 — poço do contrapeso) — O contrapeso da grande lanterna vira elevador — subir nele enquanto as sombras apagam as lanternas do poço.
  7. **Teste final** (Checkpoint 3 — antessala) — Lírio entrega a primeira lanterna acesa; coração.
  8. **Recompensa** (Sala da grande lanterna) — Vulto Apagador (6 PV); vitória reacende a grande lanterna; bandeira em x5050 no topo.
- **Caminhos alternativos:**
  - Varanda externa da torre sob a lua (relíquia).
  - Sala de mapas do lanterneiro (cano) (relíquia, estrela).
  - Desafio dos contrapesos: subir só pelos contrapesos sem tocar a escada (relíquia).
- **Inimigos permitidos:** `flor_mordedora` (Flor-Mordedora), `cogumelo_saltitante` (Cogumelo Saltitante), `mariposa_lume` (Mariposa-Lume), `planta_esporos` (Planta-de-Esporos), `aranha_cipo` (Aranha-do-Cipó), `assombracao_timida` (Sombra-Errante), `sapo_lodo` (Sapo-do-Lodo), `mao_lodo` (Mão-do-Lodo), `ossada_pantano` (Ossada do Pântano), `sentinela_canhao` (Canhão Sentinela), `prensa_vapor` (Prensa a Vapor), `boss:vulto_apagador` (Vulto Apagador (chefe planejado))
- **Quantidade planejada de inimigos:** 20–26 (chefes não contados)
- **Obstáculos:**
  - escada em caracol com quedas verticais
  - contrapesos e prensas
  - lanternas temporizadas
  - assombros e projéteis
- **Itens disponíveis:**
  - fogo: ? pátio
  - crescer: ? casa de máquinas
  - estrela: sala de mapas
  - coração: antessala
- **Segredos:**
  - `moon_balcony` (high_route) — pista: Uma janela aberta deixa entrar o luar sobre degraus do lado de fora; recompensa: relíquia relic_balcony
  - `map_room` (warp_room) — pista: Cano atrás de um mapa enrolado com a marca de uma lanterna; recompensa: relíquia relic_maps e estrela
  - `counterweights` (optional_challenge) — pista: Contrapesos com faixas âmbar marcando a ordem de subida; recompensa: relíquia relic_weights
- **Colecionáveis:** ~110 moedas e 3 relíquias
- **Checkpoints:** 3
- **Eventos especiais:**
  - boss_arena (sala da lanterna): trava a câmera e fecha o alçapão
  - lights: lanternas da torre e da arena (o chefe as apaga)
  - message (antessala): Lírio — “Duas lanternas acesas e a sombra fica de carne e osso.”
- **Elementos animados:**
  - engrenagens e correntes dos contrapesos
  - sombras com olhos nas paredes
  - lanternas acendendo/apagando
  - grande lanterna reacendendo na vitória
- **Trilha sonora:** `haunted_swamp_fortress` — torre: órgão, sinos e cordas em ostinato; tema do chefe com coro e badaladas (sub-áreas: `haunted_swamp_dark`, `haunted_swamp_boss`)
- **Condição de conclusão:** Derrotar o Vulto Apagador (6 PV) e tocar a bandeira em x5050.
- **Critérios de teste:**
  - validate_level e validate_campaign sem erros (schema, espécies, bioma, ordem de introdução, warps com chão)
  - route_bot conclui a fase partindo do spawn e de cada um dos 3 checkpoint(s), com inimigos e perigos ativos
  - vãos obrigatórios ≤ 160 u na mesma altura e subidas obrigatórias ≤ 64 u, simulados nas duas alturas do jogador sem coyote nem buffer
  - as 3 relíquias e todas as moedas são alcançáveis (rota de teste dedicada por relíquia; nenhuma moeda leva a morte)
  - teto sobre patrulha: nenhum sólido não semissólido com base entre y_chão−158 e y_chão−30 sobre a patrulha de inimigo terrestre a menos de 160 u de um vão obrigatório
  - zona segura de cada checkpoint: chão plano de x−96 a x+192 e nenhum inimigo comum alcança [x−160, x+320] em 3 s de simulação
  - Canhão Sentinela e Prensa a Vapor aparecem só na sub-área [fortress] (regra de habitat)
  - toda queda dentro da torre cai num patamar a ≤ 260 u ou tem trilha de moedas
  - a arena sempre tem duas lanternas acendíveis alcançáveis
  - o bot vence o chefe partindo do checkpoint da antessala
- **Requisitos de motor:** 
  - **bloqueia** — comportamento do chefe planejado Vulto Apagador (vulto_apagador): família nova em lume/core/behaviors/bosses.py
  - **bloqueia** — lights (extensão): a máscara de escuridão das zonas dark com o halo de Lume (120 u; 64 u correndo) já é desenhada; faltam lanternas fixas e acendíveis com raio e duração e o evento lights global (apagar/acender)

## Mundo 9 — Fortaleza Vulcânica (`volcanic_fortress`)

Basalto, brasa e magma ascendente. O fim da campanha antiga vira o começo do domínio: o fogo de Lume para de funcionar contra quase tudo, o magma passa a subir e o chefe esfria só depois de atacar. Detalhes do mundo em [`MUNDO_09.md`](MUNDO_09.md).

### 9-1 · Pontes de Basalto (`basalt_bridges`)

*Ideia própria:* a nova ponte levadiça sobre o rio de lava no fim.

- **Identificador:** `basalt_bridges`
- **Nome:** Pontes de Basalto
- **Mundo:** Fortaleza Vulcânica (`volcanic_fortress`, bioma `volcano`), fase 1 de 6 — origem: legada 5-1
- **Objetivo:** Abrir o Mundo 9 com o traçado legado endurecido: quatro canais de lava (dois alargados para 150 u), chamas sobre os saltos e quatro moradores resistentes ao fogo, um por ponte; nova seção final de ponte levadiça.
- **Tema visual:** Pontes de basalto escuro sobre canais de lava brilhante, colunas hexagonais, chaminés expelindo brasas ao fundo, céu vermelho-escuro com cinza caindo.
- **Mecânica principal:** Saltos sobre canais de lava com chamas oscilantes cronometrando a decolagem
- **Mecânicas secundárias:**
  - Brasa Andante e Golem de Basalto imunes ao fogo
  - Boca-de-Fornalha (bolas de fogo retas; só pisão ou casco)
  - Ermitão-de-Basalto (pisado, recolhe-se no bloco de basalto, que chutado atravessa a lava)
  - ponte levadiça com plataformas móveis obrigatórias
- **Dificuldade:** 8/10
- **Duração planejada:** 90–180 s (primeira travessia → exploração completa)
- **Tamanho do cenário:** 5200 × 1240 u
  - `main` [volcano] 0,0 5200×540: cinco pontes de basalto, quatro canais (110/120/150/150 u) e rio de lava final
  - `pipe_room_area` [underground] 3319,700 960×540: câmara secreta
- **Caminho principal** (sequência de ensino):
  1. **Introdução** (0–700 u) — Primeira ponte; ? de crescer x350; Brasa Andante (estreia) em [400, 620]: o fogo não a afeta — pisar.
  2. **Demonstração segura** (700–1450 u) — Canal de 110 u com chama oscilante proposta sobre o salto; Golem de Basalto (2 golpes, imune ao fogo) em [930, 1140]; ? de fogo x1190 (útil só contra outros).
  3. **Primeiro desafio** (1450–2400 u) — Canal de 120 u; tijolo x1710 → plataforma móvel x1870 → tijolo x2040 (relíquia alta); chama x2130; checkpoint x2280; ossada nova em [1600, 1700].
  4. **Escalada** (2370–3170 u) — Canal alargado para 150 u; Boca-de-Fornalha (estreia) em x2720 cuspindo bolas de fogo retas sobre a ponte; espinhos x2910.
  5. **Combinação** (3140–4300 u) — Canal alargado para 150 u; cano da câmara x3490; Ermitão-de-Basalto (estreia) em [3830, 4030]: pisar e chutar o bloco por cima da lava da próxima seção.
  6. **Reviravolta** (4300–4900 u) — Nova seção: ponte levadiça — plataformas móveis horizontais obrigatórias sobre um rio de lava de 600 u, com bocas-de-fornalha em pilares.
  7. **Teste final** (3950–4900 u) — 2º checkpoint em x3950 antes da ponte levadiça; teste de chama + plataforma + projétil.
  8. **Recompensa** (4900–5200 u) — Portão da cidadela e bandeira (movida) em x5050.
- **Caminhos alternativos:**
  - Rota alta: tijolo x1710 → plataforma móvel → tijolo x2040 (relíquia alta x2074, y220), contorna a chama.
  - Pilares de obsidiana frágeis acima da ponte levadiça (relíquia da obsidiana).
  - Cano x3490 → câmara (relíquia, coração).
- **Inimigos permitidos:** `brasa_andante` (Brasa Andante — estreia), `tartaruga_basalto` (Ermitão-de-Basalto — estreia), `boca_fornalha` (Boca-de-Fornalha — estreia), `golem_basalto` (Golem de Basalto — estreia), `ossada_pantano` (Ossada do Pântano)
- **Quantidade planejada de inimigos:** 12–16 (chefes não contados)
- **Obstáculos:**
  - 4 canais de lava (110/120/150/150 u) e rio de lava de 600 u
  - chamas oscilantes sobre saltos obrigatórios
  - bolas de fogo retas
  - espinhos x2910
- **Itens disponíveis:**
  - crescer: ? x350
  - fogo: ? x1190
  - estrela: ? x3030
  - coração: câmara x3778
- **Segredos:**
  - `high_route` (high_route) — pista: A rota alta contorna a chama (dica legada); moedas na plataforma móvel; recompensa: relíquia relic_high (x2074, y220)
  - `obsidian_pillars` (optional_challenge) — pista: Pilares de obsidiana com veios dourados acima da ponte levadiça; recompensa: relíquia relic_obsidian
  - `pipe_room` (warp_room) — pista: Cano com seta luminosa entre colunas hexagonais; recompensa: relíquia relic_room (x3828, y850) e coração
- **Colecionáveis:** ~70 moedas e 3 relíquias
- **Checkpoints:** 2
- **Eventos especiais:**
  - message (x2280): Brônzio — “Brasa não queima brasa. Pise ou chute um casco.”
- **Elementos animados:**
  - lava borbulhando com brilho pulsante
  - chamas oscilantes com rastro
  - brasas subindo (weather embers)
  - ponte levadiça rangendo nas correntes
- **Trilha sonora:** `volcanic_fortress_main` — pontes de basalto: tambores graves, metais em fanfarra sombria e coro (sub-áreas: `volcanic_fortress_underground`)
- **Condição de conclusão:** Tocar a bandeira em x5050.
- **Critérios de teste:**
  - validate_level e validate_campaign sem erros (schema, espécies, bioma, ordem de introdução, warps com chão)
  - route_bot conclui a fase partindo do spawn e de cada um dos 2 checkpoint(s), com inimigos e perigos ativos
  - vãos obrigatórios ≤ 160 u na mesma altura e subidas obrigatórias ≤ 64 u, simulados nas duas alturas do jogador sem coyote nem buffer
  - as 3 relíquias e todas as moedas são alcançáveis (rota de teste dedicada por relíquia; nenhuma moeda leva a morte)
  - estreias (Brasa Andante, Ermitão-de-Basalto, Boca-de-Fornalha, Golem de Basalto) em chão plano com ≥ 300 u de aproximação visível, recuo livre e nenhum vão letal a 200 u
  - teto sobre patrulha: nenhum sólido não semissólido com base entre y_chão−158 e y_chão−30 sobre a patrulha de inimigo terrestre a menos de 160 u de um vão obrigatório
  - zona segura de cada checkpoint: chão plano de x−96 a x+192 e nenhum inimigo comum alcança [x−160, x+320] em 3 s de simulação
  - canais de 150 u vencíveis decolando na borda nas duas alturas, com a chama no pior ponto do ciclo dando ≥ 0,4 s de janela
  - as quatro estreias acontecem em pontes diferentes, cada uma com chão plano e recuo
  - o fogo não fere brasa, boca e golem (fire_immune) — teste de regressão
  - o bot conclui partindo dos 2 checkpoints
- **Requisitos de motor:** nenhum (implementável com o motor atual)
- **Plano de melhoria da fase legada:**
  - Mantido o traçado legado (5 pontes x0–4300, canais, blocos, plataforma móvel e câmara); a bandeira passa de x4150 para x5050 por causa da seção nova.
  - Dificuldade de mundo 9: canais 3 e 4 alargados para 150 u (fim das pontes em x2370 e x3140), chamas oscilantes sobre dois saltos obrigatórios, densidade de 3 para 12–16 inimigos (brasas, ossadas, segunda boca), dicas reduzidas.
  - Exceção do registro: quatro estreias (brasa, golem, boca, ermitão) — uma por ponte; todas são variantes de famílias já ensinadas (andarilho, blindado, atirador, casco); ver ajuste proposto.
  - Seção nova x4300–4900: ponte levadiça com plataformas móveis obrigatórias (permitidas a partir do Mundo 2) sobre rio de lava.
  - 2º checkpoint em x3950 (chão plano x3854–4142).
  - Terceira relíquia: pilares de obsidiana frágeis sobre o rio de lava (desafio opcional).

### 9-2 · Fornalha dos Ecos (`echo_furnace`)

*Ideia própria:* a galeria dos ecos: uma rota alta inteira acima das fornalhas.

- **Identificador:** `echo_furnace`
- **Nome:** Fornalha dos Ecos
- **Mundo:** Fortaleza Vulcânica (`volcanic_fortress`, bioma `volcano`), fase 2 de 6 — origem: legada 5-2
- **Objetivo:** Explorar a fornalha em terraços, com galerias frágeis, chamas em dupla e o Morcego-Brasa; somar a galeria dos ecos, uma rota alta contínua, e endurecer os saltos para o mundo 9.
- **Tema visual:** Interior de fornalha com terraços de basalto, bocas de gárgula, correntes e sinos de bronze que ecoam, galerias de pedra frágil no alto, luz laranja vinda de baixo.
- **Mecânica principal:** Terraços de fornalha com galerias frágeis e chamas em dupla (duas chamas fora de fase)
- **Mecânicas secundárias:**
  - Morcego-Brasa (voo ondulado; fogo funciona)
  - galeria dos ecos (rota alta contínua)
  - plataforma vertical
  - moradores imunes ao fogo
- **Dificuldade:** 8/10
- **Duração planejada:** 100–200 s (primeira travessia → exploração completa)
- **Tamanho do cenário:** 4800 × 1240 u
  - `main` [volcano] 0,0 4800×540: seis terraços com cinco canais de 120 u e galeria alta em y≈120–260
  - `pipe_room_area` [underground] 2479,700 960×540: câmara secreta
- **Caminho principal** (sequência de ensino):
  1. **Introdução** (0–780 u) — Entrada; ? de crescer x350; brasas andantes em [450, 620].
  2. **Demonstração segura** (780–1460 u) — Terraço +32 u; Boca-de-Fornalha em [925, 1100]; ? de fogo x1150; chama x1320 em dupla com uma segunda chama proposta fora de fase.
  3. **Primeiro desafio** (1580–2360 u) — Galeria frágil x1870 → x2030 (relíquia alta) e início da galeria dos ecos (pedras frágeis até y≈180); espinhos x2140.
  4. **Escalada** (2360–3240 u) — Checkpoint x2470; cano da câmara x2660; ? de coração x2970; ermitões-de-basalto para chutar por cima do canal.
  5. **Combinação** (3240–3980 u) — Terraço elevado com golem e plataforma vertical x3600 sob chama x3770; ossadas novas.
  6. **Reviravolta** (1600–3900 u (galeria)) — Galeria dos ecos: corredor alto de pedras frágeis, sinos que ecoam e morcegos — reencontra o caminho em x3980.
  7. **Teste final** (3980–4600 u) — Morcego-Brasa (estreia) sobre chão plano [4230, 4480] (espinhos movidos para x4560); ? de fogo x4110.
  8. **Recompensa** (4600–4800 u) — Bandeira em x4650.
- **Caminhos alternativos:**
  - Galeria frágil x1870 → x2030 (relíquia alta x2063, y226).
  - Galeria dos ecos x1600–3900 (relíquia dos ecos).
  - Cano x2660 → câmara (relíquia, estrela).
- **Inimigos permitidos:** `brasa_andante` (Brasa Andante), `tartaruga_basalto` (Ermitão-de-Basalto), `boca_fornalha` (Boca-de-Fornalha), `golem_basalto` (Golem de Basalto), `morcego_brasa` (Morcego-Brasa — estreia), `ossada_pantano` (Ossada do Pântano)
- **Quantidade planejada de inimigos:** 14–18 (chefes não contados)
- **Obstáculos:**
  - 5 canais de lava de 120 u
  - chamas em dupla
  - galerias frágeis
  - espinhos x2140 e x4560
- **Itens disponíveis:**
  - crescer: ? x350
  - fogo: ? x1150
  - coração: ? x2970
  - fogo: ? x4110
  - estrela: câmara x2938
- **Segredos:**
  - `high_route` (high_route) — pista: No alto, avance antes que a pedra se desfaça (dica legada); moedas na galeria; recompensa: relíquia relic_high (x2063, y226)
  - `echo_gallery` (high_route) — pista: Um sino de bronze toca sozinho no alto quando Lume passa embaixo; recompensa: relíquia relic_echo (x3880, y140)
  - `pipe_room` (warp_room) — pista: Cano com seta luminosa entre gárgulas; recompensa: relíquia relic_room (x2988, y850) e estrela
- **Colecionáveis:** ~75 moedas e 3 relíquias
- **Checkpoints:** 1
- **Eventos especiais:**
  - message (x2470): Brônzio — “Duas chamas, dois ritmos. Ouça o eco dos sinos.”
- **Elementos animados:**
  - sinos de bronze balançando e ecoando
  - chamas em dupla fora de fase
  - pedras frágeis rachando com faíscas
  - morcegos com asas incandescentes
- **Trilha sonora:** `volcanic_fortress_main` — fornalha: sinos com eco longo, contrabaixo e percussão de bigorna (sub-áreas: `volcanic_fortress_underground`)
- **Condição de conclusão:** Tocar a bandeira em x4650.
- **Critérios de teste:**
  - validate_level e validate_campaign sem erros (schema, espécies, bioma, ordem de introdução, warps com chão)
  - route_bot conclui a fase partindo do spawn e de cada um dos 1 checkpoint(s), com inimigos e perigos ativos
  - vãos obrigatórios ≤ 160 u na mesma altura e subidas obrigatórias ≤ 64 u, simulados nas duas alturas do jogador sem coyote nem buffer
  - as 3 relíquias e todas as moedas são alcançáveis (rota de teste dedicada por relíquia; nenhuma moeda leva a morte)
  - estreias (Morcego-Brasa) em chão plano com ≥ 300 u de aproximação visível, recuo livre e nenhum vão letal a 200 u
  - teto sobre patrulha: nenhum sólido não semissólido com base entre y_chão−158 e y_chão−30 sobre a patrulha de inimigo terrestre a menos de 160 u de um vão obrigatório
  - zona segura de cada checkpoint: chão plano de x−96 a x+192 e nenhum inimigo comum alcança [x−160, x+320] em 3 s de simulação
  - cada par de chamas deixa janela ≥ 0,4 s para o salto obrigatório
  - a galeria dos ecos reencontra o caminho sem queda cega > 220 u
  - teto sobre patrulha: golem fora da sombra da plataforma vertical
  - o bot conclui partindo do checkpoint
- **Requisitos de motor:** nenhum (implementável com o motor atual)
- **Plano de melhoria da fase legada:**
  - Mantido o traçado de seis terraços, cinco canais de 120 u, galerias frágeis e câmara.
  - Dificuldade de mundo 9: chamas em dupla (fora de fase) nos saltos x1320 e x3770, densidade de 3 para 14–18 inimigos, plataforma vertical x3600 obrigatória (atalho seguro removido).
  - Morcego-Brasa: estreia mantida em x4350, mas os espinhos x4490 vão para x4560 para deixar 250 u de chão livre sob o voo.
  - Terceira relíquia: fim da galeria dos ecos (x3880, y140).
  - Golem fora da sombra da plataforma vertical (x3600, base até y366): patrulha [3360, 3530] → [3260, 3420].

### 9-3 · A Última Chama (`last_flame`)

*Ideia própria:* a rota da chama ancestral passa por cima dos dois últimos canais.

- **Identificador:** `last_flame`
- **Nome:** A Última Chama
- **Mundo:** Fortaleza Vulcânica (`volcanic_fortress`, bioma `volcano`), fase 3 de 6 — origem: legada 5-3
- **Objetivo:** Síntese da campanha antiga elevada ao mundo 9: seis trechos de cidadela com todos os moradores do vulcão e o Guardião da Última Chama (7 PV, três disparos), agora com dois checkpoints e uma rota alta final.
- **Tema visual:** Cidadela de basalto incandescente, estandartes chamuscados, braseiros, a chama ancestral ardendo no topo da torre, arena com piso de obsidiana rachada.
- **Mecânica principal:** Síntese: canais de lava, pedra frágil, plataformas e chamas em sequência sem respiro longo
- **Mecânicas secundárias:**
  - guardião de três disparos (guardiao_chama)
  - rota da chama ancestral
  - ossadas e morcegos adicionais
  - chamas oscilantes duplas
- **Dificuldade:** 9/10
- **Duração planejada:** 120–240 s (primeira travessia → exploração completa)
- **Tamanho do cenário:** 5200 × 1240 u
  - `main` [volcano] 0,0 5200×540: seis trechos com cinco canais de 120 u e arena x4630–4970
  - `pipe_room_area` [underground] 2419,700 960×540: câmara secreta
- **Caminho principal** (sequência de ensino):
  1. **Introdução** (0–930 u) — Portão; ? de crescer x380; Ermitão-de-Basalto em [560, 760]; canal de 120 u.
  2. **Demonstração segura** (930–1780 u) — Tijolo x1040 → pedra frágil x1210 → plataforma móvel x1380 (relíquia alta); golem; canal.
  3. **Primeiro desafio** (1780–3000 u) — ? de fogo x1910 e moeda x1990; chama x2180; boca x2370; checkpoint x2610 ('Recupere o fôlego neste chão seguro'); cano x2680.
  4. **Escalada** (3000–3760 u) — Terraço com tijolo x3140 e pedra frágil x3300; Morcego-Brasa e ossada; canal.
  5. **Combinação** (3760–4470 u) — 2º checkpoint proposto x3900; coração x3890; chama x4080 (dupla proposta) e tijolo x4210; canal.
  6. **Reviravolta** (3640–4470 u (rota alta)) — Rota da chama ancestral: pedras frágeis e uma chama sobre os dois últimos canais até a relíquia (x4300, y150).
  7. **Teste final** (4470–4630 u) — Antessala com fogo (x4520) e coração (x4570).
  8. **Recompensa** (4630–5200 u) — Arena: Guardião da Última Chama (7 PV, três disparos por ciclo); vitória libera a bandeira em x5050.
- **Caminhos alternativos:**
  - Tijolo → pedra frágil → plataforma móvel (relíquia alta x1420, y220).
  - Rota da chama ancestral (relíquia ancestral).
  - Cano x2680 → câmara (relíquia, estrela).
- **Inimigos permitidos:** `brasa_andante` (Brasa Andante), `tartaruga_basalto` (Ermitão-de-Basalto), `boca_fornalha` (Boca-de-Fornalha), `golem_basalto` (Golem de Basalto), `morcego_brasa` (Morcego-Brasa), `ossada_pantano` (Ossada do Pântano), `guardiao_chama` (Guardião da Última Chama — estreia)
- **Quantidade planejada de inimigos:** 14–18 (chefes não contados)
- **Obstáculos:**
  - 5 canais de lava de 120 u
  - pedras frágeis
  - chamas duplas
  - esferas do guardião em leque de três
- **Itens disponíveis:**
  - crescer: ? x380
  - fogo: ? x1910
  - moeda: ? x1990
  - coração: ? x3890
  - estrela: câmara x2878
  - fogo: chão x4520
  - coração: chão x4570
- **Segredos:**
  - `high_route` (high_route) — pista: Trilha de moedas pela pedra frágil e pela plataforma móvel; recompensa: relíquia relic_high (x1420, y220)
  - `ancestral_flame` (optional_challenge) — pista: Um braseiro apagado no alto com fumaça azul; pedras frágeis com veios dourados; recompensa: relíquia relic_ancestral (x4300, y150)
  - `pipe_room` (warp_room) — pista: Cano com seta luminosa sob um estandarte chamuscado; recompensa: relíquia relic_room (x2928, y850) e estrela
- **Colecionáveis:** ~70 moedas e 3 relíquias
- **Checkpoints:** 2
- **Eventos especiais:**
  - message (x2610): Brônzio — “Recupere o fôlego neste chão seguro.” (dica legada)
  - message (x4510): “O último guardião protege a saída. Observe e salte.” (dica legada)
- **Elementos animados:**
  - chama ancestral no topo da torre
  - braseiros e estandartes
  - guardião incandescente abrindo a guarda
  - piso de obsidiana rachando na arena
- **Trilha sonora:** `volcanic_fortress_main` — última chama: tema da campanha antiga reorquestrado com coro e órgão; na arena, metais e tímpanos (sub-áreas: `volcanic_fortress_underground`)
- **Condição de conclusão:** Derrotar o Guardião da Última Chama (7 PV) e tocar a bandeira em x5050.
- **Critérios de teste:**
  - validate_level e validate_campaign sem erros (schema, espécies, bioma, ordem de introdução, warps com chão)
  - route_bot conclui a fase partindo do spawn e de cada um dos 2 checkpoint(s), com inimigos e perigos ativos
  - vãos obrigatórios ≤ 160 u na mesma altura e subidas obrigatórias ≤ 64 u, simulados nas duas alturas do jogador sem coyote nem buffer
  - as 3 relíquias e todas as moedas são alcançáveis (rota de teste dedicada por relíquia; nenhuma moeda leva a morte)
  - teto sobre patrulha: nenhum sólido não semissólido com base entre y_chão−158 e y_chão−30 sobre a patrulha de inimigo terrestre a menos de 160 u de um vão obrigatório
  - zona segura de cada checkpoint: chão plano de x−96 a x+192 e nenhum inimigo comum alcança [x−160, x+320] em 3 s de simulação
  - o guardião dispara três esferas por ciclo e só recebe dano com a guarda aberta
  - a rota da chama ancestral reencontra o caminho antes da antessala
  - o bot vence o guardião partindo do checkpoint 2
  - a bandeira só conclui após a derrota do guardião
- **Requisitos de motor:** nenhum (implementável com o motor atual)
- **Plano de melhoria da fase legada:**
  - Mantido o traçado de seis trechos, cinco canais, guardião com 7 PV e câmara.
  - Dificuldade de mundo 9: densidade de 5 para 14–18 inimigos (brasas, ossadas, segundo morcego, segunda boca), chama dupla em x4080, dicas reduzidas.
  - 2º checkpoint em x3900 (chão plano x3804–4092, a 154 u da chama x4080): perder para o guardião não repete a cidadela inteira.
  - Terceira relíquia: rota da chama ancestral sobre os dois últimos canais (x3640–4470).

### 9-4 · Magma Ascendente (`rising_magma`)

*Ideia própria:* o magma recua e é preciso descer antes que volte.

- **Identificador:** `rising_magma`
- **Nome:** Magma Ascendente
- **Mundo:** Fortaleza Vulcânica (`volcanic_fortress`, bioma `volcano`), fase 4 de 6 — origem: nova
- **Objetivo:** Mecânica especial da Fortaleza Vulcânica: escalar a forja vertical enquanto o magma sobe por etapas anunciadas pelo sino de Brônzio, e conhecer a Salta-Brasa, que salta da lava em ritmo fixo.
- **Tema visual:** Forja vertical colossal com paredes de basalto, faixas de bronze pintadas marcando a altura segura, correntes e plataformas de pedra, magma brilhante subindo; sinos no alto.
- **Mecânica principal:** Magma ascendente (rising_lava) em etapas: sino 2 s antes, subida até a próxima faixa de bronze e pausa
- **Mecânicas secundárias:**
  - Salta-Brasa (salta verticalmente da lava a cada 2,6 s; só estrela)
  - plataformas móveis verticais
  - moradores do vulcão em patamares
  - descida rápida na janela de recuo
- **Dificuldade:** 8/10
- **Duração planejada:** 110–220 s (primeira travessia → exploração completa)
- **Tamanho do cenário:** 4200 × 3240 u
  - `main` [volcano] 0,0 4200×3240: forja vertical da base (y≈3100) à cratera (y≈200)
- **Caminho principal** (sequência de ensino):
  1. **Introdução** (Base) — Forja inferior com magma estável; Salta-Brasa (estreia) numa poça lateral, ao lado de chão largo: borbulhas, salto vertical, queda — ritmo fixo de 2,6 s.
  2. **Demonstração segura** (Etapa 1) — Primeira subida: o sino toca 2 s antes e o magma sobe 200 u até parar logo abaixo da faixa de bronze — subir até a faixa com folga.
  3. **Primeiro desafio** (Etapas 2–3) — Subida por etapas enquanto Lume escala plataformas de basalto; salta-brasas nas poças laterais.
  4. **Escalada** (Checkpoint 1) — Ao reaparecer, o magma volta ao nível desta etapa (reinício seguro).
  5. **Combinação** (Etapas 4–5) — Magma subindo + brasas + morcegos + plataformas verticais.
  6. **Reviravolta** (Câmara de fuga) — O magma recua por 6 s — descer por um poço até uma passagem lateral antes que volte a subir.
  7. **Teste final** (Checkpoints 2 e 3) — Subida final contínua (sem pausas) com salta-brasas e golems nos patamares.
  8. **Recompensa** (Cratera (y≈200)) — Cratera aberta ao céu vermelho e bandeira em x4000.
- **Caminhos alternativos:**
  - Nicho acima da faixa de bronze mais alta de cada etapa (moedas) e um com relíquia.
  - Câmara de fuga alternativa por dentro da parede (cano) (relíquia, estrela).
  - Desafio: subir a etapa 5 sem parar em nenhuma faixa (relíquia).
- **Inimigos permitidos:** `brasa_andante` (Brasa Andante), `tartaruga_basalto` (Ermitão-de-Basalto), `boca_fornalha` (Boca-de-Fornalha), `golem_basalto` (Golem de Basalto), `morcego_brasa` (Morcego-Brasa), `ossada_pantano` (Ossada do Pântano), `bolha_magma` (Salta-Brasa — estreia)
- **Quantidade planejada de inimigos:** 14–20 (chefes não contados)
- **Obstáculos:**
  - magma ascendente
  - salta-brasas
  - plataformas verticais
  - bocas de fornalha nas paredes
- **Itens disponíveis:**
  - crescer: ? base
  - fogo: ? etapa 2
  - estrela: câmara alternativa (única defesa contra salta-brasas)
  - coração: checkpoint 2
- **Segredos:**
  - `bronze_niche` (hidden_area) — pista: Uma faixa de bronze pintada acima do normal, com moedas brilhando atrás de uma coluna; recompensa: relíquia relic_niche
  - `inner_escape` (warp_room) — pista: Cano de bronze na parede da câmara de fuga com sino pequeno tocando; recompensa: relíquia relic_escape e estrela
  - `nonstop_climb` (optional_challenge) — pista: Placa de Brônzio: 'sem parar na etapa cinco'; recompensa: relíquia relic_nonstop
- **Colecionáveis:** ~100 moedas e 3 relíquias
- **Checkpoints:** 3
- **Eventos especiais:**
  - rising_lava (etapas 1–5): sino 2 s antes, subida de 200 u a 60 u/s, pausa de 6 s; recuo de 6 s na câmara de fuga; subida contínua a 45 u/s no fim
  - message (base): Brônzio — “Ouviu o sino? Suba até a faixa de bronze.”
  - enquadramento: a câmera mantém a superfície do magma visível no quadro inferior (parte da implementação de rising_lava)
- **Elementos animados:**
  - superfície do magma ondulando e subindo
  - faixas de bronze pintadas
  - sinos tocando
  - salta-brasas com borbulhas de aviso
- **Trilha sonora:** `volcanic_fortress_magma` — forja: pulsação grave que acelera a cada etapa, sinos e coro; silêncio tenso na pausa (sub-áreas: `volcanic_fortress_main`)
- **Condição de conclusão:** Chegar à cratera e tocar a bandeira em x4000 (y≈200).
- **Critérios de teste:**
  - validate_level e validate_campaign sem erros (schema, espécies, bioma, ordem de introdução, warps com chão)
  - route_bot conclui a fase partindo do spawn e de cada um dos 3 checkpoint(s), com inimigos e perigos ativos
  - vãos obrigatórios ≤ 160 u na mesma altura e subidas obrigatórias ≤ 64 u, simulados nas duas alturas do jogador sem coyote nem buffer
  - as 3 relíquias e todas as moedas são alcançáveis (rota de teste dedicada por relíquia; nenhuma moeda leva a morte)
  - estreias (Salta-Brasa) em chão plano com ≥ 300 u de aproximação visível, recuo livre e nenhum vão letal a 200 u
  - teto sobre patrulha: nenhum sólido não semissólido com base entre y_chão−158 e y_chão−30 sobre a patrulha de inimigo terrestre a menos de 160 u de um vão obrigatório
  - zona segura de cada checkpoint: chão plano de x−96 a x+192 e nenhum inimigo comum alcança [x−160, x+320] em 3 s de simulação
  - a velocidade de subida do magma é ≤ 60% da subida vertical possível do jogador em cada etapa (folga mínima)
  - o sino toca ≥ 2 s antes de cada subida
  - reaparecer num checkpoint reposiciona o magma no nível daquela etapa
  - o bot conclui com o magma ativo partindo dos 3 checkpoints
- **Requisitos de motor:** 
  - **bloqueia** — rising_lava (extensão): a subida única de um perigo por evento já existe (hazard/to/speed, gatilho por x); faltam ciclos de subida e descida, gatilho por altura, tempo ou chefe, aviso sonoro, etapas com pausa, reposição no checkpoint e a variante com zona swim (maré)

### 9-5 · Corredor de Cinzas (`ash_gauntlet`)

*Ideia própria:* blocos do Ermitão-de-Basalto chutados por cima da lava limpam a margem de lá.

- **Identificador:** `ash_gauntlet`
- **Nome:** Corredor de Cinzas
- **Mundo:** Fortaleza Vulcânica (`volcanic_fortress`, bioma `volcano`), fase 5 de 6 — origem: nova
- **Objetivo:** Desafio avançado: atravessar o longo corredor vulcânico sob rajadas de cinza, com abrigos de basalto, todos os moradores do vulcão e trechos em que o único jeito de limpar a outra margem é chutar cascos por cima da lava.
- **Tema visual:** Corredor entre paredões vulcânicos com chuva de cinza, rios de lava paralelos, abrigos de basalto em forma de arco, ruínas de uma muralha antiga, céu escuro com relâmpagos vulcânicos.
- **Mecânica principal:** Rajadas de cinza (wind lateral com período) sobre trechos de lava, com abrigos de basalto entre elas
- **Mecânicas secundárias:**
  - blocos do Ermitão-de-Basalto atravessando corredores de lava
  - salta-brasas nos canais
  - nuvens de cinza que escurecem (zonas dark opcionais)
  - moradores imunes ao fogo em grupos
- **Dificuldade:** 9/10
- **Duração planejada:** 140–280 s (primeira travessia → exploração completa)
- **Tamanho do cenário:** 6800 × 1620 u
  - `main` [volcano] 0,0 6800×1080: corredor com canais e abrigos
  - `lava_tubes` [underground] 3000,1080 1400×540: tubos de lava (atalho e segredo)
- **Caminho principal** (sequência de ensino):
  1. **Introdução** (0–800 u) — Entrada do corredor; primeira rajada de cinza sobre chão firme e um abrigo de basalto em arco.
  2. **Demonstração segura** (800–1500 u) — Rajada contrária sobre canal de lava de 120 u: atravessar só na calmaria; salta-brasas no canal.
  3. **Primeiro desafio** (1500–2300 u) — Primeiro corredor de lava paralelo: Ermitão-de-Basalto na margem de cá, bocas e brasas na de lá — chutar o bloco por cima da lava.
  4. **Escalada** (2300–3000 u) — Checkpoint x2300; grupos de brasas e golems entre abrigos; ossadas.
  5. **Combinação** (3000–4400 u) — Tubos de lava (atalho subterrâneo) ou superfície com nuvens de cinza que escurecem.
  6. **Reviravolta** (4400–5200 u) — Dois corredores de lava paralelos com cascos que ricocheteiam entre muretas — um casco limpa as duas margens se chutado no ângulo certo.
  7. **Teste final** (4600–6300 u) — Checkpoints x4600 e x5800; teste longo: rajadas, salta-brasas, morcegos e bocas.
  8. **Recompensa** (6300–6800 u) — Portão do Trono de Magma; bandeira em x6650.
- **Caminhos alternativos:**
  - Tubos de lava subterrâneos (x3000–4400): mais curtos, com morcegos (relíquia).
  - Muralha antiga por cima (pedras frágeis) (relíquia).
  - Desafio do casco: derrubar 5 inimigos com um único casco (relíquia).
- **Inimigos permitidos:** `brasa_andante` (Brasa Andante), `tartaruga_basalto` (Ermitão-de-Basalto), `boca_fornalha` (Boca-de-Fornalha), `golem_basalto` (Golem de Basalto), `morcego_brasa` (Morcego-Brasa), `ossada_pantano` (Ossada do Pântano), `bolha_magma` (Salta-Brasa)
- **Quantidade planejada de inimigos:** 24–30 (chefes não contados)
- **Obstáculos:**
  - rajadas de cinza sobre lava
  - canais com salta-brasas
  - grupos de moradores imunes ao fogo
  - nuvens de cinza
- **Itens disponíveis:**
  - crescer: ? x500
  - fogo: ? x2400 (para morcegos e ermitões)
  - estrela: tubos de lava
  - coração: checkpoint x4600
- **Segredos:**
  - `lava_tubes` (hidden_area) — pista: Fumaça saindo de uma rachadura no chão de um abrigo; recompensa: relíquia relic_tubes e estrela
  - `old_wall` (high_route) — pista: Ameias de uma muralha antiga aparecem por trás da cinza com moedas; recompensa: relíquia relic_wall
  - `shell_combo` (optional_challenge) — pista: Fileira de 5 inimigos alinhados além da lava e um Ermitão-de-Basalto sozinho na margem; recompensa: relíquia relic_combo
- **Colecionáveis:** ~110 moedas e 3 relíquias
- **Checkpoints:** 3
- **Eventos especiais:**
  - message (x2300): Brônzio — “O bloco do ermitão atravessa a lava. Chute com vontade.”
  - lights (opcional): nuvens de cinza reduzem o raio de visão na superfície x3000–4400
- **Elementos animados:**
  - chuva de cinza em diagonal com as rajadas
  - cascos atravessando a lava com respingos
  - relâmpagos vulcânicos
  - abrigos de basalto com brasas presas
- **Trilha sonora:** `volcanic_fortress_main` — corredor: marcha de tambores, metais graves e vento de cinza no compasso (sub-áreas: `volcanic_fortress_underground`)
- **Condição de conclusão:** Tocar a bandeira em x6650.
- **Critérios de teste:**
  - validate_level e validate_campaign sem erros (schema, espécies, bioma, ordem de introdução, warps com chão)
  - route_bot conclui a fase partindo do spawn e de cada um dos 3 checkpoint(s), com inimigos e perigos ativos
  - vãos obrigatórios ≤ 160 u na mesma altura e subidas obrigatórias ≤ 64 u, simulados nas duas alturas do jogador sem coyote nem buffer
  - as 3 relíquias e todas as moedas são alcançáveis (rota de teste dedicada por relíquia; nenhuma moeda leva a morte)
  - teto sobre patrulha: nenhum sólido não semissólido com base entre y_chão−158 e y_chão−30 sobre a patrulha de inimigo terrestre a menos de 160 u de um vão obrigatório
  - zona segura de cada checkpoint: chão plano de x−96 a x+192 e nenhum inimigo comum alcança [x−160, x+320] em 3 s de simulação
  - nenhuma rajada cobre um salto obrigatório sem calmaria ≥ 1,5 s
  - o casco chutado atravessa a lava (não é destruído) e derruba inimigos na outra margem
  - distância entre zonas de descanso ≤ 3000 u (regra 17 da pesquisa para W9)
  - o bot conclui partindo dos 3 checkpoints
- **Requisitos de motor:** 
  - não bloqueia — lights (extensão): a máscara de escuridão das zonas dark com o halo de Lume (120 u; 64 u correndo) já é desenhada; faltam lanternas fixas e acendíveis com raio e duração e o evento lights global (apagar/acender) (opcional: nuvens de cinza)

### 9-6 · Trono de Magma (`magma_throne`)

*Ideia própria:* as ilhas do trono afundam e voltam com a maré de magma.

- **Identificador:** `magma_throne`
- **Nome:** Trono de Magma
- **Mundo:** Fortaleza Vulcânica (`volcanic_fortress`, bioma `volcano`), fase 6 de 6 — origem: nova
- **Objetivo:** Fortaleza da Fortaleza Vulcânica: atravessar o palácio sobre o lago de magma, cuja maré sobe e desce em ciclos, e derrotar a Salamandra Caldera pisando sua cabeça quando ela esfria depois de cuspir fogo.
- **Tema visual:** Palácio de obsidiana sobre um lago de magma, colunas com veios dourados, correntes gigantes, trono esculpido na rocha incandescente, sinos de Brônzio nas torres.
- **Mecânica principal:** Maré de magma em ciclos (rising_lava sobe e desce) sobre ilhas de basalto
- **Mecânicas secundárias:**
  - salta-brasas
  - canhões e prensas na casa de máquinas do palácio (sub-área fortress)
  - todos os moradores do vulcão
  - chefe planejado Salamandra Caldera
- **Dificuldade:** 9/10
- **Duração planejada:** 170–340 s (primeira travessia → exploração completa)
- **Tamanho do cenário:** 6400 × 2160 u
  - `main` [volcano] 0,0 1400×1080: margem do lago de magma
  - `palace` [fortress] 1400,0 4000×2160: palácio de obsidiana com casa de máquinas
  - `throne_hall` [fortress] 5400,0 1000×1080: sala do trono (arena)
- **Caminho principal** (sequência de ensino):
  1. **Introdução** (0–700 u) — Margem: o magma do lago sobe e desce (ciclo de 8 s) entre ilhas largas; o sino avisa a maré.
  2. **Demonstração segura** (700–1400 u) — Ilhas menores que afundam na maré alta: esperar a maré baixa e atravessar.
  3. **Primeiro desafio** (1400–2200 u) — Palácio: corredores com bocas, golems e salta-brasas nos fossos.
  4. **Escalada** (2200–3000 u) — Checkpoint x2200; casa de máquinas com Prensas a Vapor e Canhões Sentinela (sub-área fortress).
  5. **Combinação** (3000–3800 u) — Escadaria vertical com maré subindo em ciclos e morcegos.
  6. **Reviravolta** (3800–4600 u) — As ilhas do trono afundam e voltam com a maré — o caminho só existe metade do tempo.
  7. **Teste final** (4600–5400 u) — Checkpoint x4700 na antessala com coração; Brônzio explica o resfriamento da salamandra.
  8. **Recompensa** (5400–6400 u) — Sala do trono: Salamandra Caldera (7 PV); vitória vira estátua de obsidiana e acende o farol-vulcão; bandeira em x6250.
- **Caminhos alternativos:**
  - Torre dos sinos de Brônzio (relíquia).
  - Tesouro do trono sob o palácio (cano) (relíquia, estrela).
  - Desafio da maré: cruzar o lago na maré alta pelas correntes do teto (relíquia).
- **Inimigos permitidos:** `brasa_andante` (Brasa Andante), `tartaruga_basalto` (Ermitão-de-Basalto), `boca_fornalha` (Boca-de-Fornalha), `golem_basalto` (Golem de Basalto), `morcego_brasa` (Morcego-Brasa), `ossada_pantano` (Ossada do Pântano), `bolha_magma` (Salta-Brasa), `sentinela_canhao` (Canhão Sentinela), `prensa_vapor` (Prensa a Vapor), `boss:salamandra_caldera` (Salamandra Caldera (chefe planejado))
- **Quantidade planejada de inimigos:** 22–28 (chefes não contados)
- **Obstáculos:**
  - maré de magma em ciclos
  - ilhas que afundam
  - salta-brasas, bocas e canhões
  - prensas
- **Itens disponíveis:**
  - crescer: ? x500
  - fogo: ? x2300
  - estrela: tesouro do trono
  - coração: antessala x4750
- **Segredos:**
  - `bell_tower` (high_route) — pista: Sino de bronze dourado no alto de uma torre, tocando fora do ritmo; recompensa: relíquia relic_bell
  - `throne_treasure` (warp_room) — pista: Cano de obsidiana com veios dourados atrás de uma coluna; recompensa: relíquia relic_treasure e estrela
  - `high_tide` (optional_challenge) — pista: Correntes do teto com argolas e moedas acima do lago; recompensa: relíquia relic_tide
- **Colecionáveis:** ~110 moedas e 3 relíquias
- **Checkpoints:** 2
- **Eventos especiais:**
  - rising_lava (ciclo): maré do lago sobe 120 u e desce a cada 8 s, com sino 1,5 s antes
  - boss_arena (x5400): trava a câmera na sala do trono e fecha o portão
  - message (x4700): Brônzio — “A salamandra esfria depois de cuspir fogo. É a sua hora.”
- **Elementos animados:**
  - lago de magma pulsando
  - ilhas afundando e emergindo
  - correntes gigantes balançando
  - salamandra esfriando (pele escurecendo em crosta)
- **Trilha sonora:** `volcanic_fortress_fortress` — palácio: órgão, coro e tambores; tema do chefe com metais e sinos em fúria (sub-áreas: `volcanic_fortress_magma`, `volcanic_fortress_boss`)
- **Condição de conclusão:** Derrotar a Salamandra Caldera (7 PV) e tocar a bandeira em x6250.
- **Critérios de teste:**
  - validate_level e validate_campaign sem erros (schema, espécies, bioma, ordem de introdução, warps com chão)
  - route_bot conclui a fase partindo do spawn e de cada um dos 2 checkpoint(s), com inimigos e perigos ativos
  - vãos obrigatórios ≤ 160 u na mesma altura e subidas obrigatórias ≤ 64 u, simulados nas duas alturas do jogador sem coyote nem buffer
  - as 3 relíquias e todas as moedas são alcançáveis (rota de teste dedicada por relíquia; nenhuma moeda leva a morte)
  - teto sobre patrulha: nenhum sólido não semissólido com base entre y_chão−158 e y_chão−30 sobre a patrulha de inimigo terrestre a menos de 160 u de um vão obrigatório
  - zona segura de cada checkpoint: chão plano de x−96 a x+192 e nenhum inimigo comum alcança [x−160, x+320] em 3 s de simulação
  - canhões e prensas só aparecem na sub-área [fortress]
  - na maré alta sempre há ilha ou plataforma segura a ≤ 160 u
  - o bot vence o chefe partindo do checkpoint da antessala
  - a maré nunca sobe sobre checkpoints
- **Requisitos de motor:** 
  - **bloqueia** — comportamento do chefe planejado Salamandra Caldera (salamandra_caldera): família nova em lume/core/behaviors/bosses.py
  - **bloqueia** — rising_lava (extensão): a subida única de um perigo por evento já existe (hazard/to/speed, gatilho por x); faltam ciclos de subida e descida, gatilho por altura, tempo ou chefe, aviso sonoro, etapas com pausa, reposição no checkpoint e a variante com zona swim (maré)

## Mundo 10 — Cidadela das Estrelas (`star_citadel`)

Constelações, gravidade e o eclipse final. Síntese: a gravidade afrouxa, as constelações viram pontes, os espelhos refletem mundos anteriores e o eclipse apaga tudo — o último chefe usa as dez fronteiras. Detalhes do mundo em [`MUNDO_10.md`](MUNDO_10.md).

### 10-1 · Portão Estrelado (`starlit_gate`)

*Ideia própria:* o último bolsão de baixa gravidade cobre o vazio entre duas torres.

- **Identificador:** `starlit_gate`
- **Nome:** Portão Estrelado
- **Mundo:** Cidadela das Estrelas (`star_citadel`, bioma `citadel`), fase 1 de 6 — origem: nova
- **Objetivo:** Apresentar a cidadela: escadarias de luz, bolsões de baixa gravidade demonstrados sobre chão e depois sobre o vazio, canhões e a Sentinela Estelar, que dispara três projéteis em leque.
- **Tema visual:** Escadaria de luz e cristal sob céu estrelado parado, torres de pedra violeta com janelas douradas, pontes de cristal, colunas com constelações gravadas, o portão estelar fechado ao fundo.
- **Mecânica principal:** Bolsões de baixa gravidade (zona lowgrav, gravidade × 0,55)
- **Mecânicas secundárias:**
  - Sentinela Estelar (carrega e dispara 3 projéteis em leque; 2 golpes)
  - Canhão Sentinela com projéteis pisáveis
  - pontes de cristal frágeis
  - Sombra-Errante da cidadela (paralisa no halo de Lume)
- **Dificuldade:** 8/10
- **Duração planejada:** 100–200 s (primeira travessia → exploração completa)
- **Tamanho do cenário:** 5600 × 1620 u
  - `main` [citadel] 0,0 5600×1620: escadaria de luz e torres com dois bolsões de baixa gravidade
- **Caminho principal** (sequência de ensino):
  1. **Introdução** (0–700 u) — Escadaria de luz: degraus de cristal semissólidos sob o céu estrelado; Astra apresenta a cidadela.
  2. **Demonstração segura** (700–1300 u) — Primeiro bolsão de baixa gravidade sobre chão largo: saltos de ~204 u de altura com moedas no alto; cair não machuca.
  3. **Primeiro desafio** (1300–2000 u) — Sentinela Estelar (estreia) num terraço plano com colunas: brilho de carga (aviso) e leque de três — abrigar-se atrás da coluna, pisar duas vezes.
  4. **Escalada** (2000–2800 u) — Checkpoint x2000; pontes de cristal frágeis + Canhão Sentinela disparando ao longo da ponte.
  5. **Combinação** (2800–3600 u) — Bolsão de baixa gravidade com sentinelas acima: o arco longo expõe Lume ao leque — cortar o salto cedo.
  6. **Reviravolta** (3600–4300 u) — O bolsão cobre o vazio entre duas torres — dentro dele um vão de 360 u vira um salto longo natural; fora dele, um tropeço é fatal.
  7. **Teste final** (4300–5200 u) — Checkpoint x4300; sombras-errantes entre colunas + sentinelas + canhões.
  8. **Recompensa** (5200–5600 u) — O portão estelar se abre e a bandeira fica em x5450.
- **Caminhos alternativos:**
  - Topo de uma torre pela coluna de baixa gravidade (relíquia).
  - Observatório de Astra (cano com telescópio) (relíquia, estrela).
  - Desafio do leque: atravessar o terraço de três sentinelas sem se abrigar (relíquia).
- **Inimigos permitidos:** `sentinela_canhao` (Canhão Sentinela), `assombracao_timida` (Sombra-Errante), `sentinela_estelar` (Sentinela Estelar — estreia)
- **Quantidade planejada de inimigos:** 14–18 (chefes não contados)
- **Obstáculos:**
  - vazio entre torres
  - leques de projéteis
  - pontes de cristal frágeis
  - projéteis de canhão
- **Itens disponíveis:**
  - crescer: ? x400
  - fogo: ? x1900
  - estrela: observatório
  - coração: checkpoint 2
- **Segredos:**
  - `tower_top` (high_route) — pista: Constelação em forma de seta gravada na torre aponta para cima; moedas no bolsão; recompensa: relíquia relic_tower
  - `observatory` (warp_room) — pista: Cano com um telescópio de latão por cima, apontado para uma estrela piscando; recompensa: relíquia relic_observatory e estrela
  - `fan_run` (optional_challenge) — pista: Três sentinelas alinhadas com uma faixa de moedas entre elas; recompensa: relíquia relic_fan
- **Colecionáveis:** ~100 moedas e 3 relíquias
- **Checkpoints:** 2
- **Eventos especiais:**
  - message (x2000): Astra — “Aqui o chão puxa menos. Solte o salto mais cedo.”
- **Elementos animados:**
  - poeira estelar flutuando mais devagar dentro dos bolsões
  - sentinela brilhando antes do leque
  - portão estelar se abrindo
  - constelações das colunas cintilando
- **Trilha sonora:** `star_citadel_main` — portão estelar: coro etéreo, harpa e sintetizador suave com pulsação lenta
- **Condição de conclusão:** Tocar a bandeira em x5450.
- **Critérios de teste:**
  - validate_level e validate_campaign sem erros (schema, espécies, bioma, ordem de introdução, warps com chão)
  - route_bot conclui a fase partindo do spawn e de cada um dos 2 checkpoint(s), com inimigos e perigos ativos
  - vãos obrigatórios ≤ 160 u na mesma altura e subidas obrigatórias ≤ 64 u, simulados nas duas alturas do jogador sem coyote nem buffer
  - as 3 relíquias e todas as moedas são alcançáveis (rota de teste dedicada por relíquia; nenhuma moeda leva a morte)
  - estreias (Sentinela Estelar) em chão plano com ≥ 300 u de aproximação visível, recuo livre e nenhum vão letal a 200 u
  - teto sobre patrulha: nenhum sólido não semissólido com base entre y_chão−158 e y_chão−30 sobre a patrulha de inimigo terrestre a menos de 160 u de um vão obrigatório
  - zona segura de cada checkpoint: chão plano de x−96 a x+192 e nenhum inimigo comum alcança [x−160, x+320] em 3 s de simulação
  - toda borda de bolsão lowgrav é visível (poeira lenta) e o salto que sai do bolsão não cai em vão sem aviso
  - o vão de 360 u da reviravolta fica inteiro dentro do bolsão e é vencível nas duas alturas
  - estreia da sentinela estelar com coluna-abrigo a ≤ 120 u
  - o bot conclui partindo dos 2 checkpoints
- **Requisitos de motor:** nenhum (implementável com o motor atual)

### 10-2 · Trilha das Constelações (`constellation_path`)

*Ideia própria:* revelar a ponte em cadeia: cada estrela revelada é o degrau para bater na próxima.

- **Identificador:** `constellation_path`
- **Nome:** Trilha das Constelações
- **Mundo:** Cidadela das Estrelas (`star_citadel`, bioma `citadel`), fase 2 de 6 — origem: nova
- **Objetivo:** Explorar trilhas no vazio onde as pontes são constelações de blocos ocultos: o desenho no céu indica onde bater; conhecer o Cometa Errante, que espera no céu e mergulha deixando rastro.
- **Tema visual:** Céu girando lentamente, desenhos de constelações projetados por Astra, ilhas de pedra estelar, pontes de luz que surgem bloco a bloco, cometas com rastro dourado.
- **Mecânica principal:** Constelações de blocos ocultos: o desenho no céu mostra onde bater; cada bloco revelado vira plataforma
- **Mecânicas secundárias:**
  - Cometa Errante (espera no céu e mergulha em arco)
  - baixa gravidade em trechos
  - sentinelas estelares
  - rotas em três alturas
- **Dificuldade:** 9/10
- **Duração planejada:** 120–240 s (primeira travessia → exploração completa)
- **Tamanho do cenário:** 6000 × 2160 u
  - `main` [citadel] 0,0 6000×2160: trilhas em três alturas sobre o vazio
- **Caminho principal** (sequência de ensino):
  1. **Introdução** (0–700 u) — Astra projeta a primeira constelação (5 estrelas) acima de chão firme: bater nos pontos indicados revela blocos — demonstração sem risco.
  2. **Demonstração segura** (700–1300 u) — Constelação sobre um fosso raso: cada bloco revelado vira degrau.
  3. **Primeiro desafio** (1300–2000 u) — Cometa Errante (estreia) espera no céu sobre uma ilha larga e mergulha quando Lume passa embaixo, deixando rastro: esperar e pisar na subida.
  4. **Escalada** (2000–2800 u) — Checkpoint x2000; primeira ponte de constelação sobre o vazio (os pontos mais baixos ficam sobre ilhas).
  5. **Combinação** (2800–3600 u) — Cometas + sentinelas + baixa gravidade: revelar estrelas com ameaça vinda de cima.
  6. **Reviravolta** (3600–4400 u) — A ponte em cadeia — só a primeira estrela é alcançável do chão; cada estrela revelada é o degrau para bater na seguinte, subindo em zigue-zague.
  7. **Teste final** (4400–5600 u) — Checkpoints x4400 e x5200; trilha alta com cometas em sequência e sombras-errantes.
  8. **Recompensa** (5600–6000 u) — Mirante das constelações e bandeira em x5850.
- **Caminhos alternativos:**
  - Constelação escondida (sem desenho no céu, só uma estrela piscando) (relíquia).
  - Planetário (cano) (relíquia, estrela).
  - Trilha de baixo: ilhas menores sem constelações, mais cometas (relíquia).
- **Inimigos permitidos:** `sentinela_canhao` (Canhão Sentinela), `assombracao_timida` (Sombra-Errante), `sentinela_estelar` (Sentinela Estelar), `cometa_errante` (Cometa Errante — estreia)
- **Quantidade planejada de inimigos:** 16–22 (chefes não contados)
- **Obstáculos:**
  - vazio
  - mergulhos de cometa
  - leques de sentinela
  - pontes que só existem depois de reveladas
- **Itens disponíveis:**
  - crescer: ? x400
  - fogo: ? x1900
  - estrela: planetário
  - coração: checkpoint 2
- **Segredos:**
  - `hidden_constellation` (hidden_block) — pista: Uma única estrela pisca fora de qualquer desenho do céu; recompensa: relíquia relic_hidden
  - `planetarium` (warp_room) — pista: Cano com anéis de planeta girando em volta; recompensa: relíquia relic_planetarium e estrela
  - `low_trail` (high_route) — pista: Rastro de um cometa antigo aponta para baixo, para ilhas menores; recompensa: relíquia relic_low
- **Colecionáveis:** ~120 moedas e 3 relíquias
- **Checkpoints:** 3
- **Eventos especiais:**
  - message (x2000): Astra — “O céu desenha o caminho. Bata onde a estrela falta.”
- **Elementos animados:**
  - constelações acendendo no céu
  - blocos ocultos surgindo como estrelas
  - cometas com rastro
  - céu girando devagar
- **Trilha sonora:** `star_citadel_main` — constelações: celesta em arpejos, cordas suaves e um sino por estrela revelada
- **Condição de conclusão:** Tocar a bandeira em x5850.
- **Critérios de teste:**
  - validate_level e validate_campaign sem erros (schema, espécies, bioma, ordem de introdução, warps com chão)
  - route_bot conclui a fase partindo do spawn e de cada um dos 3 checkpoint(s), com inimigos e perigos ativos
  - vãos obrigatórios ≤ 160 u na mesma altura e subidas obrigatórias ≤ 64 u, simulados nas duas alturas do jogador sem coyote nem buffer
  - as 3 relíquias e todas as moedas são alcançáveis (rota de teste dedicada por relíquia; nenhuma moeda leva a morte)
  - estreias (Cometa Errante) em chão plano com ≥ 300 u de aproximação visível, recuo livre e nenhum vão letal a 200 u
  - teto sobre patrulha: nenhum sólido não semissólido com base entre y_chão−158 e y_chão−30 sobre a patrulha de inimigo terrestre a menos de 160 u de um vão obrigatório
  - zona segura de cada checkpoint: chão plano de x−96 a x+192 e nenhum inimigo comum alcança [x−160, x+320] em 3 s de simulação
  - cada constelação obrigatória tem todos os pontos indicados no céu e o primeiro bloco é alcançável de chão firme
  - na ponte em cadeia cada bloco revelado permite bater no seguinte nas duas alturas
  - nenhum cometa mergulha sobre um checkpoint
  - o bot conclui partindo dos 3 checkpoints
- **Requisitos de motor:** nenhum (implementável com o motor atual)

### 10-3 · Salões da Gravidade (`gravity_halls`)

*Ideia própria:* vento solar dentro da baixa gravidade leva Lume longe demais.

- **Identificador:** `gravity_halls`
- **Nome:** Salões da Gravidade
- **Mundo:** Cidadela das Estrelas (`star_citadel`, bioma `citadel`), fase 3 de 6 — origem: nova
- **Objetivo:** Desafio de movimento: atravessar salões com faixas de gravidade baixa e normal alternadas, colunas de baixa gravidade como escadas e vento solar, e vencer o Guardião da Constelação no salão final.
- **Tema visual:** Salões de mármore violeta com relógios de areia flutuantes, faixas de luz dourada marcando a baixa gravidade, poeira suspensa, janelas para o espaço; salão final com mosaico de constelação no piso.
- **Mecânica principal:** Faixas alternadas de gravidade baixa e normal (lowgrav) que mudam o arco no meio do salto
- **Mecânicas secundárias:**
  - Guardião da Constelação (elite: acende as constelações do corpo e investe; 3 golpes)
  - colunas verticais de baixa gravidade
  - vento solar (wind com período) dentro dos bolsões
  - cometas e sentinelas
- **Dificuldade:** 9/10
- **Duração planejada:** 120–240 s (primeira travessia → exploração completa)
- **Tamanho do cenário:** 5600 × 2160 u
  - `main` [citadel] 0,0 5600×2160: seis salões e o salão do guardião (x4700–5400)
- **Caminho principal** (sequência de ensino):
  1. **Introdução** (0–700 u) — Salão 1 todo em baixa gravidade: saltos altos com moedas no teto; sem perigos.
  2. **Demonstração segura** (700–1300 u) — Faixas alternadas: um salto que começa na baixa e termina na normal cai rápido — moedas mostram o arco certo.
  3. **Primeiro desafio** (1300–2000 u) — Vãos com bolsão: cortar o salto (soltar o botão) para não passar do pouso; fosso raso embaixo.
  4. **Escalada** (2000–2800 u) — Checkpoint x2000; colunas verticais de baixa gravidade usadas como escada, com sentinelas nos patamares.
  5. **Combinação** (2800–3600 u) — Cometas mergulhando entre faixas + crumble de cristal.
  6. **Reviravolta** (3600–4400 u) — Vento solar (wind ±120, período 3 s) dentro de bolsões — o empurrão lateral, somado ao arco longo, leva longe demais; usar a calmaria.
  7. **Teste final** (4400–5400 u) — Checkpoints x4400 e x4700; Guardião da Constelação (estreia) no salão do mosaico, em gravidade normal, com muretas para ele bater: pisar 3 vezes fora da investida.
  8. **Recompensa** (5400–5600 u) — Saída do salão e bandeira em x5450.
- **Caminhos alternativos:**
  - Relógio de areia flutuante mais alto (relíquia).
  - Salão secreto de gravidade zero simulada (cano) (relíquia, estrela).
  - Desafio das faixas: atravessar 6 faixas alternadas sem tocar o chão (relíquia).
- **Inimigos permitidos:** `sentinela_canhao` (Canhão Sentinela), `assombracao_timida` (Sombra-Errante), `sentinela_estelar` (Sentinela Estelar), `cometa_errante` (Cometa Errante), `guardiao_constelacao` (Guardião da Constelação — estreia)
- **Quantidade planejada de inimigos:** 16–22 (chefes não contados)
- **Obstáculos:**
  - mudança de gravidade no meio do salto
  - vento solar
  - investida do guardião
  - leques e mergulhos
- **Itens disponíveis:**
  - crescer: ? x400
  - fogo: ? x1900 (o guardião não tem fraqueza a fogo)
  - estrela: salão secreto
  - coração: checkpoint x4700
- **Segredos:**
  - `hourglass` (high_route) — pista: Um relógio de areia flutuante com a areia subindo; recompensa: relíquia relic_hourglass
  - `still_hall` (warp_room) — pista: Cano com poeira totalmente parada em volta; recompensa: relíquia relic_still e estrela
  - `band_run` (optional_challenge) — pista: Seis faixas douradas com uma moeda no meio de cada; recompensa: relíquia relic_bands
- **Colecionáveis:** ~110 moedas e 3 relíquias
- **Checkpoints:** 3
- **Eventos especiais:**
  - camera_lock (opcional) no salão do guardião
  - message (x4700): Astra — “Ele acende as estrelas do corpo antes de correr.”
- **Elementos animados:**
  - faixas de luz dourada nas zonas lowgrav
  - relógios de areia girando
  - constelações do guardião acendendo
  - poeira suspensa
- **Trilha sonora:** `star_citadel_main` — salões: compasso lento e flutuante, sinos graves e baixo que some na baixa gravidade
- **Condição de conclusão:** Derrotar o Guardião da Constelação (3 golpes) no salão do mosaico e tocar a bandeira em x5450.
- **Critérios de teste:**
  - validate_level e validate_campaign sem erros (schema, espécies, bioma, ordem de introdução, warps com chão)
  - route_bot conclui a fase partindo do spawn e de cada um dos 3 checkpoint(s), com inimigos e perigos ativos
  - vãos obrigatórios ≤ 160 u na mesma altura e subidas obrigatórias ≤ 64 u, simulados nas duas alturas do jogador sem coyote nem buffer
  - as 3 relíquias e todas as moedas são alcançáveis (rota de teste dedicada por relíquia; nenhuma moeda leva a morte)
  - estreias (Guardião da Constelação) em chão plano com ≥ 300 u de aproximação visível, recuo livre e nenhum vão letal a 200 u
  - teto sobre patrulha: nenhum sólido não semissólido com base entre y_chão−158 e y_chão−30 sobre a patrulha de inimigo terrestre a menos de 160 u de um vão obrigatório
  - zona segura de cada checkpoint: chão plano de x−96 a x+192 e nenhum inimigo comum alcança [x−160, x+320] em 3 s de simulação
  - subidas obrigatórias ≤ 116 u dentro dos bolsões e ≤ 64 u fora deles
  - o guardião sempre encontra mureta ao investir e não sai do salão
  - o vento solar nunca empurra para o vazio sem calmaria ≥ 1,5 s
  - o bot conclui partindo dos 3 checkpoints
- **Requisitos de motor:** nenhum (implementável com o motor atual)

### 10-4 · Santuário dos Reflexos (`mirror_sanctum`)

*Ideia própria:* os espelhos do segundo átrio misturam dois mundos na mesma sala.

- **Identificador:** `mirror_sanctum`
- **Nome:** Santuário dos Reflexos
- **Mundo:** Cidadela das Estrelas (`star_citadel`, bioma `citadel`), fase 4 de 6 — origem: nova
- **Objetivo:** Mecânica especial da Cidadela das Estrelas: avançar pelo santuário entrando em espelhos-poça que levam a reflexos de mundos anteriores — costa submersa, cavernas e fortalezas — e devolvem Lume do outro lado de abismos intransponíveis.
- **Tema visual:** Santuário de prata e violeta com espelhos-poça no chão que mostram outros lugares, colunas espelhadas, reflexos iridescentes; dentro dos espelhos, versões cristalinas da costa, das cavernas e das fortalezas.
- **Mecânica principal:** Espelhos-poça (canos de passagem) que levam a salas-reflexo de outros biomas e devolvem Lume adiante
- **Mecânicas secundárias:**
  - reflexo da costa (sub-área underwater: nado, baiacus, moreias, águas-vivas, polvo)
  - reflexo das cavernas (sub-área underground: pingentes, morcegos)
  - reflexo das fortalezas (sub-área fortress: prensas, bocas, golems, ossadas)
  - sentinelas, cometas e guardião no santuário
- **Dificuldade:** 9/10
- **Duração planejada:** 150–300 s (primeira travessia → exploração completa)
- **Tamanho do cenário:** 6400 × 2700 u
  - `main` [citadel] 0,0 6400×1080: dois átrios de espelhos separados por abismos
  - `coast_reflection` [underwater] 0,1080 2000×810: reflexo da costa
  - `cave_reflection` [underground] 2000,1080 2200×810: reflexo das cavernas
  - `fortress_reflection` [fortress] 4200,1080 2200×810: reflexo das fortalezas
  - `mixed_reflection` [underwater] 0,1890 6400×810: sala-reflexo mista do segundo átrio (água + fortaleza)
- **Caminho principal** (sequência de ensino):
  1. **Introdução** (Átrio 1 (0–900 u)) — Um espelho-poça mostra um recife; entrar (↓) leva a uma sala submersa curta sem inimigos e voltar — demonstração.
  2. **Demonstração segura** (Reflexo da costa) — Sala de nado com correntes, baiacus, moreias e águas-vivas (remix do Mundo 3); a saída devolve Lume do outro lado do primeiro abismo.
  3. **Primeiro desafio** (900–2000 u) — Santuário com sentinelas estelares; o segundo espelho só é alcançável por uma constelação.
  4. **Escalada** (Checkpoint 1 + reflexo das cavernas) — Pingentes e morcegos num túnel cristalino (remix dos Mundos 4 e 9).
  5. **Combinação** (Reflexo das fortalezas) — Prensas, bocas-de-fornalha, golems e ossadas (remix dos Mundos 6 e 9).
  6. **Reviravolta** (Átrio 2 (checkpoint 2)) — No segundo átrio os espelhos misturam dois mundos — sala submersa com prensas e bocas no teto (o polvo persegue entre elas).
  7. **Teste final** (Corredor dos espelhos (checkpoint 3)) — Teste final no santuário com cometas, sentinelas e o Guardião da Constelação.
  8. **Recompensa** (Santuário central) — O grande espelho mostra o Bastião do Eclipse; bandeira em x6250.
- **Caminhos alternativos:**
  - Espelho rachado escondido que leva a um reflexo do Reino Verde (sala bônus sem inimigos, moedas) (relíquia).
  - Rota alta pelos topos das colunas espelhadas (relíquia).
  - Desafio do reflexo misto: atravessar sem sair da água (relíquia).
- **Inimigos permitidos:** `sentinela_canhao` (Canhão Sentinela), `assombracao_timida` (Sombra-Errante), `sentinela_estelar` (Sentinela Estelar), `cometa_errante` (Cometa Errante), `guardiao_constelacao` (Guardião da Constelação), `baiacu_espinho` (Baiacu-Espinho), `moreia_toca` (Moreia-da-Toca), `agua_viva` (Água-Viva Elétrica), `polvo_tinteiro` (Polvo-Tinteiro), `morcego_brasa` (Morcego-Brasa), `pingente_queda` (Pingente de Gelo), `prensa_vapor` (Prensa a Vapor), `boca_fornalha` (Boca-de-Fornalha), `golem_basalto` (Golem de Basalto), `ossada_pantano` (Ossada do Pântano)
- **Quantidade planejada de inimigos:** 22–30 (chefes não contados)
- **Obstáculos:**
  - abismos só transponíveis pelos reflexos
  - salas submersas com correntes
  - pingentes e prensas
  - leques, mergulhos e investida
- **Itens disponíveis:**
  - crescer: ? átrio 1
  - fogo: ? santuário
  - estrela: reflexo do Reino Verde
  - coração: átrio 2
- **Segredos:**
  - `cracked_mirror` (warp_room) — pista: Um espelho rachado mostra o céu azul do Reino Verde e flores; recompensa: relíquia relic_meadow e estrela
  - `column_tops` (high_route) — pista: Reflexos das colunas mostram moedas que não existem no chão — estão no topo; recompensa: relíquia relic_columns
  - `mixed_run` (optional_challenge) — pista: Placa de Astra: 'sem tomar ar' sobre a sala-reflexo mista; recompensa: relíquia relic_mixed
- **Colecionáveis:** ~140 moedas e 3 relíquias
- **Checkpoints:** 3
- **Eventos especiais:**
  - message (átrio 1): Astra — “Cada espelho lembra um lugar por onde você passou.”
- **Elementos animados:**
  - superfície dos espelhos-poça ondulando com a imagem de outro mundo
  - transição de entrada no espelho (ondulação e brilho)
  - reflexos iridescentes nas colunas
  - versões cristalinas dos mundos antigos
- **Trilha sonora:** `star_citadel_main` — espelhos: o tema da cidadela se funde com o tema de cada mundo refletido (costa, cavernas, fortalezas) (sub-áreas: `coral_coast_underwater`, `frozen_peaks_underground`, `volcanic_fortress_fortress`)
- **Condição de conclusão:** Atravessar os reflexos e tocar a bandeira em x6250.
- **Critérios de teste:**
  - validate_level e validate_campaign sem erros (schema, espécies, bioma, ordem de introdução, warps com chão)
  - route_bot conclui a fase partindo do spawn e de cada um dos 3 checkpoint(s), com inimigos e perigos ativos
  - vãos obrigatórios ≤ 160 u na mesma altura e subidas obrigatórias ≤ 64 u, simulados nas duas alturas do jogador sem coyote nem buffer
  - as 3 relíquias e todas as moedas são alcançáveis (rota de teste dedicada por relíquia; nenhuma moeda leva a morte)
  - teto sobre patrulha: nenhum sólido não semissólido com base entre y_chão−158 e y_chão−30 sobre a patrulha de inimigo terrestre a menos de 160 u de um vão obrigatório
  - zona segura de cada checkpoint: chão plano de x−96 a x+192 e nenhum inimigo comum alcança [x−160, x+320] em 3 s de simulação
  - inimigos de outros biomas aparecem só na sub-área do bioma correspondente (underwater/underground/fortress) — regra de habitat
  - toda sala-reflexo devolve Lume a um ponto com chão e sem inimigo a ≤ 160 u
  - o abismo entre átrios é intransponível sem o reflexo (o mecanismo é obrigatório)
  - o bot conclui partindo dos 3 checkpoints
- **Requisitos de motor:** nenhum (implementável com o motor atual)

### 10-5 · Bastião do Eclipse (`eclipse_bastion`)

*Ideia própria:* cada farol reaceso devolve um pouco de luz ao bastião que escurece.

- **Identificador:** `eclipse_bastion`
- **Nome:** Bastião do Eclipse
- **Mundo:** Cidadela das Estrelas (`star_citadel`, bioma `citadel`), fase 5 de 6 — origem: nova
- **Objetivo:** Desafio avançado final: atravessar o bastião onde o eclipse escurece tudo aos poucos, com dez trechos que combinam em pares as mecânicas das dez fronteiras, reacendendo um farol em cada um.
- **Tema visual:** Bastião de pedra estelar com dez faróis apagados, cada um decorado com o tema de uma fronteira; o céu escurece a cada trecho até restar só a coroa laranja do eclipse.
- **Mecânica principal:** Dez trechos de remix em pares de mecânicas (uma por fronteira) sob escuridão crescente
- **Mecânicas secundárias:**
  - molas e pedras frágeis (Reino Verde)
  - rajadas (Deserto Dourado)
  - nado em corrente (Costa dos Corais, sub-área underwater)
  - gelo (Montanhas Geladas)
  - assentos de cipó (Floresta Encantada)
  - esteiras e prensas (Cidade Mecânica, sub-área fortress)
  - correntes ascendentes (Arquipélago Celeste)
  - escuridão e sombras-errantes (Pântano Assombrado)
  - lava e chamas (Fortaleza Vulcânica, sub-área fortress)
  - baixa gravidade e constelações (Cidadela das Estrelas)
- **Dificuldade:** 10/10
- **Duração planejada:** 160–320 s (primeira travessia → exploração completa)
- **Tamanho do cenário:** 7200 × 2160 u
  - `main` [citadel] 0,0 7200×1080: muralhas do bastião com os dez faróis
  - `flooded_cistern` [underwater] 1400,1080 1800×1080: cisterna inundada (trecho da costa)
  - `forge_wing` [fortress] 4000,1080 3200×1080: ala das forjas (trechos da cidade e do vulcão)
- **Caminho principal** (sequência de ensino):
  1. **Introdução** (0–700 u) — Farol 1 (Reino Verde + Cidadela): molas e pedras frágeis num bolsão de baixa gravidade — o ar ainda claro.
  2. **Demonstração segura** (700–1400 u) — Farol 2 (Deserto + Céu): rajadas laterais sobre correntes ascendentes.
  3. **Primeiro desafio** (1400–2200 u) — Farol 3 (Costa): cisterna inundada com correntes, polvo e águas-vivas.
  4. **Escalada** (2200–3000 u) — Checkpoint x2200; Farol 4 (Gelo + Floresta): assentos de cipó sobre piso de gelo.
  5. **Combinação** (3000–4000 u) — Farol 5 (Pântano): escuridão crescente — só Lume e os faróis acesos iluminam; sombras-errantes e ossadas.
  6. **Reviravolta** (4000–5600 u) — Checkpoint x4000; Faróis 6–8 (Cidade + Vulcão) na ala das forjas: esteiras sobre lava, prensas, bocas e golems; reviravolta: cada farol reaceso devolve um raio de luz ao bastião.
  7. **Teste final** (5600–6800 u) — Checkpoint x5600; Faróis 9–10 (Céu + Cidadela): constelações sobre o vazio com cometas e sentinelas, quase no escuro.
  8. **Recompensa** (6800–7200 u) — Dez faróis acesos iluminam a escadaria do trono; bandeira em x7050.
- **Caminhos alternativos:**
  - Farol secreto 11 (sem tema): constelação escondida atrás da muralha (relíquia).
  - Cisterna profunda (rota longa submersa) (relíquia, estrela).
  - Desafio dos dez faróis sem dano (relíquia, contada só se nenhum dano ocorrer desde o checkpoint 3).
- **Inimigos permitidos:** `sentinela_canhao` (Canhão Sentinela), `assombracao_timida` (Sombra-Errante), `sentinela_estelar` (Sentinela Estelar), `cometa_errante` (Cometa Errante), `guardiao_constelacao` (Guardião da Constelação), `agua_viva` (Água-Viva Elétrica), `polvo_tinteiro` (Polvo-Tinteiro), `prensa_vapor` (Prensa a Vapor), `boca_fornalha` (Boca-de-Fornalha), `golem_basalto` (Golem de Basalto), `ossada_pantano` (Ossada do Pântano), `brasa_andante` (Brasa Andante), `bolha_magma` (Salta-Brasa)
- **Quantidade planejada de inimigos:** 26–34 (chefes não contados)
- **Obstáculos:**
  - escuridão crescente
  - pares de mecânicas de todos os mundos
  - lava e prensas
  - vazio entre muralhas
- **Itens disponíveis:**
  - crescer: ? farol 1
  - fogo: ? farol 4
  - estrela: cisterna profunda
  - coração: checkpoints 2 e 3
- **Segredos:**
  - `eleventh_beacon` (hidden_block) — pista: Um farol sem cor atrás da muralha; uma estrela pisca fora das constelações; recompensa: relíquia relic_beacon
  - `deep_cistern` (hidden_area) — pista: Bolhas subindo num canto escuro da cisterna; recompensa: relíquia relic_cistern e estrela
  - `ten_beacons` (optional_challenge) — pista: Os faróis acesos piscam em sequência quando Lume não sofre dano; recompensa: relíquia relic_flawless
- **Colecionáveis:** ~130 moedas e 3 relíquias
- **Checkpoints:** 3
- **Eventos especiais:**
  - lights (progressivo): o raio de visão cai de 600 u (farol 1) para 160 u (farol 9) e cada farol aceso devolve 40 u
  - message (x2200): Astra — “Cada farol que você acende devolve um pouco do céu.”
- **Elementos animados:**
  - faróis acendendo com a cor de cada fronteira
  - céu escurecendo em etapas
  - coroa do eclipse crescendo
  - remixes cristalinos de cada mundo
- **Trilha sonora:** `star_citadel_eclipse` — bastião: o tema principal recebe a melodia de um mundo por farol aceso, crescendo até um coro completo (sub-áreas: `star_citadel_main`)
- **Condição de conclusão:** Acender os dez faróis e tocar a bandeira em x7050.
- **Critérios de teste:**
  - validate_level e validate_campaign sem erros (schema, espécies, bioma, ordem de introdução, warps com chão)
  - route_bot conclui a fase partindo do spawn e de cada um dos 3 checkpoint(s), com inimigos e perigos ativos
  - vãos obrigatórios ≤ 160 u na mesma altura e subidas obrigatórias ≤ 64 u, simulados nas duas alturas do jogador sem coyote nem buffer
  - as 3 relíquias e todas as moedas são alcançáveis (rota de teste dedicada por relíquia; nenhuma moeda leva a morte)
  - teto sobre patrulha: nenhum sólido não semissólido com base entre y_chão−158 e y_chão−30 sobre a patrulha de inimigo terrestre a menos de 160 u de um vão obrigatório
  - zona segura de cada checkpoint: chão plano de x−96 a x+192 e nenhum inimigo comum alcança [x−160, x+320] em 3 s de simulação
  - inimigos de costa e de vulcão aparecem só nas sub-áreas underwater/fortress
  - sem a máscara de luz a fase continua completável (degrada para visível)
  - distância entre zonas de descanso ≤ 3000 u (regra 17 da pesquisa para W10)
  - o bot conclui partindo dos 3 checkpoints
- **Requisitos de motor:** 
  - não bloqueia — lights (extensão): a máscara de escuridão das zonas dark com o halo de Lume (120 u; 64 u correndo) já é desenhada; faltam lanternas fixas e acendíveis com raio e duração e o evento lights global (apagar/acender) (desejado: sem a máscara a fase fica jogável e perde a escuridão crescente)

### 10-6 · Trono do Eclipse (`throne_of_eclipse`)

*Ideia própria:* a luz do próprio Eclipse, refletida num espelho, abre o seu núcleo.

- **Identificador:** `throne_of_eclipse`
- **Nome:** Trono do Eclipse
- **Mundo:** Cidadela das Estrelas (`star_citadel`, bioma `citadel`), fase 6 de 6 — origem: nova
- **Objetivo:** Fortaleza final: subir a escadaria do trono pelos dez faróis acesos e derrotar o Eclipse Devorador em três fases — reflexos, apagão e chama estelar — devolvendo a luz das dez fronteiras.
- **Tema visual:** Escadaria monumental de pedra estelar sob o sol negro com coroa de fogo, faróis das dez fronteiras acesos nas laterais, trono de obsidiana e prata, espelhos gigantes em volta da arena.
- **Mecânica principal:** Escadaria final com todos os sistemas e arena com espelhos que refletem raios
- **Mecânicas secundárias:**
  - bolsões de baixa gravidade e constelações
  - escuridão (fase 2 do chefe)
  - chama estelar ascendente (fase 3)
  - chefe planejado Eclipse Devorador
- **Dificuldade:** 10/10
- **Duração planejada:** 200–400 s (primeira travessia → exploração completa)
- **Tamanho do cenário:** 6800 × 2700 u
  - `main` [citadel] 0,0 1600×1080: pé da escadaria
  - `stairway` [fortress] 1600,0 3900×2700: escadaria e salões do trono
  - `eclipse_arena` [citadel] 5500,0 1300×2700: arena do Eclipse (vertical na fase 3)
- **Caminho principal** (sequência de ensino):
  1. **Introdução** (0–800 u) — Pé da escadaria: os dez faróis acesos iluminam o caminho; Astra se despede.
  2. **Demonstração segura** (800–1600 u) — Degraus com constelações e bolsões de baixa gravidade; sentinelas nas laterais.
  3. **Primeiro desafio** (1600–2600 u) — Salão dos ecos: sombras de chefes anteriores (silhuetas decorativas) e o Guardião da Constelação.
  4. **Escalada** (2600–3500 u) — Checkpoint x2600; ala das prensas e bocas com cometas acima.
  5. **Combinação** (3500–4500 u) — Checkpoint x4000; escadaria em espiral com sombras-errantes, ossadas e morcegos no escuro parcial.
  6. **Reviravolta** (4500–5300 u) — O caminho para o trono passa por espelhos que refletem os raios de sentinelas — ensina a mecânica do chefe com inimigos comuns.
  7. **Teste final** (5300–5500 u) — Checkpoint x5300 na antessala: coração e estrela; silêncio.
  8. **Recompensa** (5500–6800 u) — Arena: Eclipse Devorador (9 PV, três fases); vitória libera as dez luzes e os créditos; o portão final em x6650 conclui a campanha.
- **Caminhos alternativos:**
  - Varanda dos faróis: tocar os dez faróis em ordem (relíquia).
  - Câmara de Astra (cano) com o mapa de todas as relíquias (relíquia, estrela).
  - Desafio da escadaria sem dano (relíquia).
- **Inimigos permitidos:** `sentinela_canhao` (Canhão Sentinela), `assombracao_timida` (Sombra-Errante), `sentinela_estelar` (Sentinela Estelar), `cometa_errante` (Cometa Errante), `guardiao_constelacao` (Guardião da Constelação), `prensa_vapor` (Prensa a Vapor), `boca_fornalha` (Boca-de-Fornalha), `ossada_pantano` (Ossada do Pântano), `morcego_brasa` (Morcego-Brasa), `boss:eclipse_devorador` (Eclipse Devorador (chefe planejado))
- **Quantidade planejada de inimigos:** 20–28 (chefes não contados)
- **Obstáculos:**
  - escadaria com quedas verticais
  - raios refletidos
  - escuridão parcial
  - prensas e bocas
  - chama estelar na fase 3 do chefe
- **Itens disponíveis:**
  - crescer: ? x500
  - fogo: ? x1700
  - estrela: antessala
  - coração: antessala
- **Segredos:**
  - `beacon_balcony` (optional_challenge) — pista: Dez faróis em fila na varanda, cada um com um pedestal para tocar; recompensa: relíquia relic_balcony
  - `astra_chamber` (warp_room) — pista: Cano com astrolábio dourado girando; recompensa: relíquia relic_astra e estrela
  - `flawless_stair` (optional_challenge) — pista: Faróis da escadaria piscam em ouro enquanto Lume não sofre dano; recompensa: relíquia relic_stair
- **Colecionáveis:** ~120 moedas e 3 relíquias
- **Checkpoints:** 3
- **Eventos especiais:**
  - boss_arena (x5500): trava a câmera na arena e fecha a escadaria
  - lights (fase 2 do chefe): apagão total; só relíquias, estrelas e o núcleo brilham
  - rising_lava variante chama estelar (fase 3): sobe sob as plataformas flutuantes
  - message (x5300): Astra — “O Eclipse devolve a luz que reflete. Fique atrás do espelho.”
  - cena final: dez luzes formam a constelação de Lume; créditos
- **Elementos animados:**
  - sol negro pulsando com coroa de fogo
  - faróis das dez fronteiras
  - espelhos refletindo raios
  - trono desmoronando em plataformas flutuantes
  - constelação final de Lume
- **Trilha sonora:** `star_citadel_fortress` — trono: coro completo e orquestra; no chefe, star_citadel_finale reúne os temas dos dez mundos (sub-áreas: `star_citadel_finale`)
- **Condição de conclusão:** Derrotar o Eclipse Devorador (9 PV) e atravessar o portão final em x6650 — fim da campanha.
- **Critérios de teste:**
  - validate_level e validate_campaign sem erros (schema, espécies, bioma, ordem de introdução, warps com chão)
  - route_bot conclui a fase partindo do spawn e de cada um dos 3 checkpoint(s), com inimigos e perigos ativos
  - vãos obrigatórios ≤ 160 u na mesma altura e subidas obrigatórias ≤ 64 u, simulados nas duas alturas do jogador sem coyote nem buffer
  - as 3 relíquias e todas as moedas são alcançáveis (rota de teste dedicada por relíquia; nenhuma moeda leva a morte)
  - teto sobre patrulha: nenhum sólido não semissólido com base entre y_chão−158 e y_chão−30 sobre a patrulha de inimigo terrestre a menos de 160 u de um vão obrigatório
  - zona segura de cada checkpoint: chão plano de x−96 a x+192 e nenhum inimigo comum alcança [x−160, x+320] em 3 s de simulação
  - a mecânica do espelho é ensinada antes da arena com inimigos comuns (reviravolta x4500–5300)
  - na fase 3 a chama sobe ≤ 50 u/s e sempre há plataforma alcançável acima
  - o bot vence o chefe partindo do checkpoint da antessala
  - a campanha termina: estado de vitória e créditos depois do portão
- **Requisitos de motor:** 
  - **bloqueia** — comportamento do chefe planejado Eclipse Devorador (eclipse_devorador): família nova em lume/core/behaviors/bosses.py
  - **bloqueia** — lights (extensão): a máscara de escuridão das zonas dark com o halo de Lume (120 u; 64 u correndo) já é desenhada; faltam lanternas fixas e acendíveis com raio e duração e o evento lights global (apagar/acender)
  - **bloqueia** — rising_lava (extensão): a subida única de um perigo por evento já existe (hazard/to/speed, gatilho por x); faltam ciclos de subida e descida, gatilho por altura, tempo ou chefe, aviso sonoro, etapas com pausa, reposição no checkpoint e a variante com zona swim (maré) (variante chama estelar na fase 3)

## 10. Chefes de mundo

| Mundo | Chefe | Fase | PV | Vulnerabilidade (resumo) | Estado |
| --- | --- | --- | ---: | --- | --- |
| 1 | Javali Espinheiro (`javali_espinheiro`) | `bramble_fortress` | 3 | Atordoado depois de bater na muralha (1,8 s; 1,35 s na fase 2): pisão na cabeça. | implementado |
| 2 | Escaravelho-Rei (`escaravelho_rei`) | `scarab_pyramid` | 3 | Depois de cada irrupção cai de costas, atordoado, por 1,6 s (1,1 s na fase 2): única janela de pisão (fraqueza só a pisão). | implementado |
| 3 | Ermitão-Âncora (`ermitao_ancora`) | `sunken_galleon` | 5 | Quando o golpe de pinça acerta tábuas de madeira, a pinça fica presa por 1,5 s (madeira lascada brilha): pisão nos olhos-pedúnculo. | planejado |
| 4 | Morsa Gelomar (`morsa_gelomar`) | `frost_citadel` | 5 | Elmo de gelo espinhoso: pisões ricocheteiam. | implementado |
| 5 | Imperatriz Mariposa (`imperatriz_mariposa`) | `root_sanctum` | 6 | Forma lagarta: um segmento-lanterna brilha em sequência ao longo do corpo; pisá-lo quando passa no nível de baixo causa dano. | planejado |
| 6 | Colosso Fundidor (`colosso_fundidor`) | `iron_foundry` | 5 | Quando o Colosso passa sob uma prensa, a marca de alinhamento no chão acende. | planejado |
| 7 | Grifa Ventania (`grifa_ventania`) | `griffin_aerie` | 6 | Só pode ser pisada no dorso. | planejado |
| 8 | Vulto Apagador (`vulto_apagador`) | `lantern_keep` | 6 | Com duas lanternas acesas ao mesmo tempo, o vulto fica sólido e atordoado pela luz por 2 s — pisão (ou fogo) nesse estado. | planejado |
| 9 | Salamandra Caldera (`salamandra_caldera`) | `magma_throne` | 7 | Depois de cada sopro de brasas a pele esfria e vira crosta de basalto por 2 s (fica escura e para de brilhar): pisão na cabeça. | planejado |
| 10 | Eclipse Devorador (`eclipse_devorador`) | `throne_of_eclipse` | 9 | O núcleo (sol negro) só abre quando um raio de constelação é refletido de volta: Lume fica atrás de um espelho no momento do disparo e o raio volta para o núcleo, que se abre por 2 s — pisão no núcleo. | planejado |

O desenho completo de cada chefe (arena, ataques, vulnerabilidade, fases, derrota e relação com a mecânica do mundo) está no documento do respectivo mundo e na lista `bosses` do JSON. Minichefes legados (fase 3): Guardião do Pomar, do Templo, da Nevasca, da Árvore e da Última Chama (família `guardian`, implementados); no Mundo 10 o Guardião da Constelação (elite) ocupa esse papel.
