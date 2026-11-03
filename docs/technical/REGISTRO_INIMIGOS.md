# Registro de inimigos

Fonte de verdade: `lume/data/enemies.json` (`format: lume.enemies`). Código: `lume/core/species.py` (perfil tipado e validação), `lume/core/behaviors/` (famílias de comportamento) e `lume/render/enemies/` (rigs de animação).

## Perfil tipado

Cada espécie é um `EnemyProfile` imutável e validado ao carregar:

| Campo | Significado |
| ----- | ----------- |
| `id`, `name` | identificador estável e nome exibido |
| `role_reference` | papel de jogo comparável nos jogos de referência (apenas a função; nunca aparência ou nome) |
| `description` | conceito original da criatura |
| `habitats` | biomas permitidos (grassland, desert, coast, underwater, snow, forest, city, sky, swamp, volcano, citadel, underground, fortress) |
| `movement_type` | ground, air, water, burrow, stationary, ghost, hopper, ceiling |
| `difficulty_tier` | 1–6, usado na curva de dificuldade |
| `behavior` | família implementada em código (máquina de estados) |
| `abilities`, `weaknesses` | habilidades (casco, projétil, espinhos, imune ao fogo…) e formas de derrota (stomp, fire, shell, star, bump, explosion) |
| `size`, `hp`, `speed`, `score`, `params` | caixa de colisão e ajuste fino; `params` alimenta a família |
| `animation_set`, `animation_states` | rig de arte e estados que ele precisa desenhar (sempre inclui `defeat`) |
| `introduced_in` | fase em que a espécie aparece pela primeira vez (verificado automaticamente) |
| `boss` | chefes bloqueiam a saída enquanto vivos |

Uma fase só referencia `species` e posição; parâmetros por instância (`params`, `hp`) sobrescrevem os da espécie quando necessário.

## Famílias de comportamento (`lume/core/behaviors`)

Cada família é uma máquina de estados própria que publica `enemy.anim` para o rig:

| Família | Estados | Ideia |
| ------- | ------- | ----- |
| walker | walk, alert, burrow, emerge | patrulha; pode notar Lume (pausa expressiva) ou se enterrar em ciclos |
| shell | walk, shell, slide, wake | recolhe-se ao ser pisado; casco chutável derruba inimigos; acorda após `recover_time` |
| armored | walk, guard | vários golpes; crista/cauda periódica torna o topo perigoso |
| hopper | idle, crouch, jump, fall, land | antecipação visível antes de cada salto |
| charger | walk, alert, charge, stunned, recover | avisa, investe, fica tonto ao bater na parede |
| slider | walk, slide | desliza de barriga sobre gelo |
| bones | walk, pile, reassemble | desmonta ao ser pisado e se remonta |
| burrower | underground, surface, walk, dig | viaja sob a areia e emerge com aviso |
| emerger | hidden, rise, out, bite, retreat | planta/criatura de toca; não emerge com Lume encostado |
| shy_ghost | chase, freeze | **mecânica própria**: paralisa no halo da lanterna de Lume; o halo encolhe quando ele corre |
| crusher | wait, shake, fall, rest, rise | prensa/pingente; topo seguro |
| swimmer | swim, leap, chase | nada em onda, salta da água, persegue quem nada |
| lava_jumper | submerged, bubble, jump, fall | salta da lava em ritmo anunciado |
| puffer | idle, inflate, spiky, deflate | infla espinhos quando Lume se aproxima |
| flyer | fly | onda senoidal; opcionalmente perde as asas no primeiro pisão |
| swooper | perch, alert, dive, climb | espera, mergulha em arco e volta |
| floater | drift | obstáculo vivo flutuante |
| cloud_rider | float, throw | segue Lume do alto e solta sementes que viram andarilhos |
| shooter | idle, charge, fire | sentinela fixa com carga visível antes do disparo |
| thrower | step, windup, throw, jump | arremessos em arco com preparação |
| cannon | idle, charge, fire | lançador indestrutível; projéteis podem ser pisados |
| guardian | walk, shell, jump | os cinco guardiões da edição web (confrontos intermediários) |
| thorn_boar | intro, stalk, telegraph, charge, stunned, hurt, recover | chefe do Reino Verde |

## Distribuição por bioma

A validação impede espécies fora de seus habitats e espécies avançadas antes da fase de introdução. Reaparições em outros mundos são permitidas quando o habitat inclui o bioma (por exemplo, `flor_mordedora` em grassland, forest e swamp). Três conceitos foram revistos após a pesquisa (`docs/research/PESQUISA_INIMIGOS.md`, seção 5.11) para evitar semelhança com personagens conhecidos: `bolha_magma` exibido como "Salta-Brasa", `tartaruga_basalto` redesenhado como "Ermitão-de-Basalto" e `assombracao_timida` ("Sombra-Errante") com comportamento baseado em luz. Os IDs internos permanecem estáveis.

## Tabela gerada a partir dos dados

Gerada por `python tools/gen_docs.py`. "Arte provisória" significa que a espécie ainda é desenhada pela criatura provisória genérica (marcada como tal na matriz de qualidade).

<!-- tabela:inicio -->
| ID | Nome | Papel (referência de função) | Habitats | Família | Nível | Fraquezas | Introduzida em | Arte | Em uso |
| -- | ---- | ---------------------------- | -------- | ------- | ----- | --------- | -------------- | ---- | ------ |
| `bolota` | Bolota | patrulheiro básico (papel análogo ao Goomba) | grassland, forest | walker | 1 | stomp, fire, shell, star | first_steps | dedicada | 6 fase(s) |
| `caramujo` | Caramujo-de-Casca | criatura de casco (papel análogo ao Koopa Troopa) | grassland, forest, coast | shell | 2 | stomp, fire, shell, star | first_steps | dedicada | 6 fase(s) |
| `besouro_alado` | Besouro-Asa | voador em onda (papel análogo ao Paratroopa) | grassland, forest | flyer | 2 | stomp, fire, shell, star | valley_canals | dedicada | 4 fase(s) |
| `besouro` | Besouro | forma terrestre do Besouro-Asa | grassland, forest | walker | 1 | stomp, fire, shell, star | valley_canals | dedicada | 1 fase(s) |
| `flor_mordedora` | Flor-Mordedora | planta hostil emergente (papel análogo à Piranha Plant) | grassland, forest, swamp | emerger | 2 | fire, shell, star | windmill_heights | dedicada | 3 fase(s) |
| `ourico_espinho` | Ouriço-Espinho | inimigo com topo espinhoso (papel análogo ao Spiny) | grassland, forest, desert | walker | 3 | fire, shell, star | meadow_burrows | dedicada | 2 fase(s) |
| `guardiao_pomar` | Guardião do Pomar (chefe) | guardião intermediário (legado 1-3) | grassland | guardian | 3 | stomp, fire, shell | orchard_guardian | dedicada | 1 fase(s) |
| `javali_espinheiro` | Javali Espinheiro (chefe) | chefe de mundo com investida (papel de chefe de fortaleza) | grassland, fortress | thorn_boar | 4 | stomp, fire | bramble_fortress | dedicada | 1 fase(s) |
| `escaravelho_areia` | Escaravelho-de-Areia | patrulheiro do deserto que se enterra | desert | walker | 2 | stomp, fire, shell, star | windswept_dunes | dedicada | 6 fase(s) |
| `tatu_bola` | Tatu-Bola | criatura de casco do deserto | desert | shell | 2 | stomp, fire, shell, star | windswept_dunes | dedicada | 5 fase(s) |
| `abutre_filhote` | Abutrinho | voador do deserto | desert, sky | flyer | 2 | stomp, fire, shell, star | canyon_bridges | dedicada | 4 fase(s) |
| `cacto_sentinela` | Cacto Sentinela | sentinela que dispara (papel análogo a lançadores) | desert | shooter | 2 | stomp, fire, shell, star | windswept_dunes | dedicada | 5 fase(s) |
| `escorpiao_couraca` | Escorpião-Couraça | inimigo blindado com cauda periódica | desert | armored | 3 | stomp, fire, shell, star | sand_temple | dedicada | 4 fase(s) |
| `guardiao_templo` | Guardião do Templo (chefe) | guardião intermediário (legado 2-3) | desert | guardian | 3 | stomp, fire, shell | sand_temple | dedicada | 1 fase(s) |
| `pinguim_patrulha` | Pinguim Patrulheiro | deslizante do gelo | snow | slider | 2 | stomp, fire, shell, star | crystal_lake | dedicada | 6 fase(s) |
| `caracol_cristal` | Caracol-de-Cristal | criatura de casco do gelo | snow | shell | 2 | stomp, fire, shell, star | crystal_lake | dedicada | 6 fase(s) |
| `coruja_nevada` | Coruja Nevada | voadora adaptada ao frio | snow | flyer | 2 | stomp, fire, shell, star | crystal_lake | dedicada | 6 fase(s) |
| `boneco_neve` | Boneco de Neve | sentinela que arremessa bolas de neve | snow | shooter | 2 | stomp, fire, shell, star | blue_ascent | dedicada | 4 fase(s) |
| `carneiro_glacial` | Carneiro Glacial | investidor resistente | snow | charger | 3 | stomp, fire, shell, star | blizzard_heart | dedicada | 3 fase(s) |
| `guardiao_nevasca` | Guardião da Nevasca (chefe) | guardião intermediário (legado 3-3) | snow | guardian | 4 | stomp, fire, shell | blizzard_heart | dedicada | 1 fase(s) |
| `cogumelo_saltitante` | Cogumelo Saltitante | saltador com antecipação | forest, swamp | hopper | 2 | stomp, fire, shell, star | glowing_canopy | dedicada | 0 fase(s) |
| `caracol_musgo` | Caracol-Musgo | criatura de casco camuflada | forest | shell | 2 | stomp, fire, shell, star | glowing_canopy | dedicada | 1 fase(s) |
| `mariposa_lume` | Mariposa-Lume | voadora luminosa | forest, swamp | flyer | 2 | stomp, fire, shell, star | glowing_canopy | dedicada | 3 fase(s) |
| `planta_esporos` | Planta-de-Esporos | sentinela vegetal | forest, swamp | shooter | 2 | stomp, fire, shell, star | glowing_canopy | dedicada | 3 fase(s) |
| `besouro_casca` | Besouro-Casca | blindado da floresta | forest | armored | 3 | stomp, fire, shell, star | firefly_ruins | dedicada | 2 fase(s) |
| `guardiao_arvore` | Guardião da Árvore (chefe) | guardião intermediário (legado 4-3) | forest | guardian | 4 | stomp, fire, shell | ancestral_tree | dedicada | 1 fase(s) |
| `brasa_andante` | Brasa Andante | patrulheiro resistente ao fogo | volcano, fortress | walker | 3 | stomp, shell, star | basalt_bridges | dedicada | 0 fase(s) |
| `tartaruga_basalto` | Ermitão-de-Basalto | criatura de casco chutável (casco de rocha vulcânica) | volcano, fortress | shell | 3 | stomp, fire, shell, star | basalt_bridges | dedicada | 2 fase(s) |
| `morcego_brasa` | Morcego-Brasa | voador das cavernas de lava | volcano, fortress, underground | flyer | 3 | stomp, fire, shell, star | echo_furnace | dedicada | 2 fase(s) |
| `boca_fornalha` | Boca-de-Fornalha | sentinela de fortaleza | volcano, fortress | shooter | 3 | stomp, shell, star | basalt_bridges | dedicada | 3 fase(s) |
| `golem_basalto` | Golem de Basalto | blindado de fortaleza | volcano, fortress | armored | 4 | stomp, shell, star | basalt_bridges | dedicada | 3 fase(s) |
| `guardiao_chama` | Guardião da Última Chama (chefe) | guardião intermediário (legado 5-3) | volcano | guardian | 5 | stomp, fire, shell | last_flame | dedicada | 1 fase(s) |
| `serpente_duna` | Serpente-de-Duna | emboscador que viaja sob a areia (papel análogo ao Monty Mole) | desert | burrower | 3 | stomp, fire, shell, star | sandstorm_pass | dedicada | 2 fase(s) |
| `escaravelho_lancador` | Escaravelho Lançador | atirador em arco (papel análogo ao Hammer Bro) | desert | thrower | 4 | stomp, fire, shell, star | sunken_oasis | dedicada | 2 fase(s) |
| `caranguejo_pinca` | Caranguejo-Pinça | criatura blindada com pinças periódicas | coast, underwater | armored | 2 | stomp, fire, shell, star | shell_beach | dedicada | 0 fase(s) |
| `peixe_saltador` | Peixe-Saltador | peixe hostil que salta da água (papel análogo ao Cheep Cheep) | coast, underwater | swimmer | 2 | stomp, fire, shell, star | shell_beach | dedicada | 0 fase(s) |
| `baiacu_espinho` | Baiacu-Espinho | criatura que infla espinhos (papel análogo ao Porcupuffer/Urchin) | coast, underwater | puffer | 3 | stomp, fire, shell, star | tide_pools | dedicada | 0 fase(s) |
| `agua_viva` | Água-Viva Elétrica | obstáculo vivo flutuante | coast, underwater | floater | 3 | fire, star | current_depths | dedicada | 0 fase(s) |
| `moreia_toca` | Moreia-da-Toca | emboscador de tocas (papel análogo ao Unagi/Piranha) | coast, underwater | emerger | 3 | fire, shell, star | tide_pools | dedicada | 0 fase(s) |
| `polvo_tinteiro` | Polvo-Tinteiro | perseguidor aquático em impulsos (papel análogo ao Blooper) | underwater | swimmer | 4 | stomp, fire, shell, star | coral_maze | dedicada | 0 fase(s) |
| `yeti_mirim` | Yeti-Mirim | atirador em arco do gelo | snow | thrower | 4 | stomp, fire, shell, star | slippery_slopes | dedicada | 3 fase(s) |
| `pingente_queda` | Pingente de Gelo | perigo que desaba (papel análogo ao Thwomp) | snow, underground | crusher | 3 | indestrutível | avalanche_ridge | dedicada | 2 fase(s) |
| `arbusto_espreita` | Arbusto-Espreita | criatura camuflada que investe | forest | charger | 3 | stomp, fire, shell, star | vine_bridges | dedicada | 0 fase(s) |
| `aranha_cipo` | Aranha-do-Cipó | inimigo que desce das copas (papel análogo ao Swoop/Scuttlebug) | forest, swamp | swooper | 3 | stomp, fire, shell, star | whispering_hollow | dedicada | 0 fase(s) |
| `robo_patrulha` | Robô de Ronda | autômato patrulheiro | city | walker | 2 | stomp, fire, shell, star | gear_district | dedicada | 0 fase(s) |
| `sentinela_canhao` | Canhão Sentinela | lançador de projéteis retos (papel análogo ao Bill Blaster) | city, fortress, citadel | cannon | 3 | indestrutível | gear_district | dedicada | 0 fase(s) |
| `drone_vigia` | Drone Vigia | voador mergulhador mecânico | city, sky | swooper | 3 | stomp, fire, shell, star | steam_works | dedicada | 0 fase(s) |
| `prensa_vapor` | Prensa a Vapor | prensa que esmaga (papel análogo ao Thwomp) | city, fortress | crusher | 3 | indestrutível | conveyor_line | dedicada | 0 fase(s) |
| `torreta_arco` | Torreta de Arco | atirador mecânico em arco | city | thrower | 4 | stomp, fire, shell, star | clock_tower | dedicada | 0 fase(s) |
| `nuvem_marota` | Nuvem Marota | perseguidor aéreo que arremessa (papel análogo ao Lakitu) | sky | cloud_rider | 4 | stomp, fire, star | floating_gardens | provisória | 0 fase(s) |
| `semente_espinho` | Semente-Espinho | andarilho espinhoso (papel análogo ao Spiny) | sky, grassland | walker | 3 | fire, shell, star | floating_gardens | provisória | 0 fase(s) |
| `passaro_rajada` | Pássaro-Rajada | voador que mergulha com o vento | sky | swooper | 3 | stomp, fire, shell, star | cloud_harbor | provisória | 0 fase(s) |
| `balao_espinho` | Balão-Espinho | obstáculo flutuante levado pelo vento | sky | floater | 3 | fire, star | gale_bridges | provisória | 0 fase(s) |
| `assombracao_timida` | Sombra-Errante | criatura furtiva que reage à luz (mecânica própria do Lume) | swamp, citadel | shy_ghost | 3 | star, fire | misty_marsh | dedicada | 0 fase(s) |
| `sapo_lodo` | Sapo-do-Lodo | saltador do pântano | swamp | hopper | 2 | stomp, fire, shell, star | misty_marsh | dedicada | 0 fase(s) |
| `mao_lodo` | Mão-do-Lodo | emboscador que surge do chão | swamp | emerger | 3 | fire, star | lantern_bog | dedicada | 0 fase(s) |
| `ossada_pantano` | Ossada do Pântano | esqueleto que se remonta (papel análogo ao Dry Bones) | swamp, fortress, volcano | bones | 4 | shell, star, explosion | sunken_mansion | dedicada | 0 fase(s) |
| `bolha_magma` | Salta-Brasa | saltador de lava em ritmo fixo (papel de obstáculo rítmico) | volcano, fortress | lava_jumper | 3 | star | rising_magma | dedicada | 0 fase(s) |
| `sentinela_estelar` | Sentinela Estelar | atirador de elite | citadel | shooter | 5 | stomp, fire, shell, star | starlit_gate | provisória | 0 fase(s) |
| `cometa_errante` | Cometa Errante | mergulhador de elite | citadel | swooper | 5 | stomp, fire, shell, star | constellation_path | provisória | 0 fase(s) |
| `guardiao_constelacao` | Guardião da Constelação | investidor de elite blindado | citadel | charger | 6 | stomp, fire, star | gravity_halls | provisória | 0 fase(s) |
| `escaravelho_rei` | Escaravelho-Rei (chefe) | chefe de mundo com emboscada subterrânea | desert, fortress | scarab_king | 4 | stomp | scarab_pyramid | dedicada | 1 fase(s) |
| `morsa_gelomar` | Morsa Gelomar (chefe) | chefe de mundo com armadura removível | snow, fortress | ice_walrus | 5 | stomp | frost_citadel | dedicada | 1 fase(s) |
<!-- tabela:fim -->
