# Áudio e diálogos

## Áudio (`game/systems/audio.py`, `game/systems/synth.py`)

Nenhum arquivo de áudio externo: trilhas, efeitos, vozes e ambientes são sintetizados com numpy e entregues ao `pygame.mixer` por `pygame.sndarray`. Pesquisa de referência: `docs/research/AUDIO.md` (timbres do APU do NES, princípios de Koji Kondo, música dinâmica dos NSMB, vozes de personagens).

### Conteúdo portado da versão original

- Seis trilhas de 32 passos (menu/mundo 1 a 5) e a trilha de chefe, nota a nota (MIDI → Hz, BPM, timbre, terça), com o mesmo agendamento: melodia por passo, baixo a cada 4 passos (duração 2,4×), harmonia nos passos ímpares (terça no passo `%4 == 1`, quinta nos demais, +12), "hat" no passo `%4 == 2`.
- Os 14 cues de evento (`jump, coin, relic, block, power, hurt, death, stomp, shot, checkpoint, secret, complete, boss, life`) com notas, durações, timbres e *slides* originais; envelopes com ataque ≤ 8 ms e decaimento exponencial.

### Arquitetura

| Elemento | Implementação |
| --- | --- |
| Barramentos | `music`, `sfx`, `voice`, `ambient` com volume próprio por canal; silenciar a música **não** altera efeitos (testado) |
| Canais | 16 no mixer, 14 reservados: 0–1 música (crossfade de 0,4 s entre dois canais), 2–9 efeitos, 10–11 vozes, 12–13 ambiente |
| Música | cada trilha renderizada como loop completo (`loops=-1`); `set_world(world, boss)` troca com crossfade e inverte a direção do fade se a trilha alvo voltar (chefe a < 800 px); `pause(True/False)` |
| Efeitos | pré-sintetizados no início; limite de 3 instâncias por efeito e 8 por barramento; o efeito novo substitui o mais antigo do mesmo tipo |
| Vozes | vocalizações **originais** por síntese aditiva com formantes (vogais morfando, contorno de altura, sílabas, sopro) — nenhuma imitação de pessoa real; `voice(name)` devolve a chave de legenda `voice.<nome>` |
| Ambiente | loops de 8 s por mundo (vento, areia, neve, floresta noturna, lava) por ruído filtrado em FFT circular (sem costura), volume baixo e fade de 1 s |
| Robustez | `pygame.mixer.init` sempre tentado; falha → `available = False` e todas as chamadas são inofensivas; com `SDL_AUDIODRIVER=dummy` funciona em CI |
| Desempenho | trilhas/ambientes/vozes renderizados em thread de fundo (só numpy) e embrulhados em `Sound` sob demanda; `prewarm()` força tudo; `background=False` para testes determinísticos e para o navegador (Pygbag não suporta threads) |

Ferramenta: `python tools/render_audio.py` exporta trilhas e cues para `build/audio/*.wav` para audição.

Diferença deliberada em relação ao original: efeitos e vozes continuam disponíveis com a música pausada (menus podem soar).

### Testes

`tests/integration/test_audio.py` (driver dummy): inicialização, síntese com tamanho correto, sem silêncio e sem clipping, cobertura dos 14 cues, volumes independentes, limite de instâncias, troca de trilha/pausa/update seguros, mixer indisponível.

## Diálogos e reações (`game/npc/dialogue.py`)

| Elemento | Implementação |
| --- | --- |
| Roteiros | `data/dialogues/*.json`: `id`, `skippable`, `auto_advance`, `on_end` (flag), linhas com `speaker`, `expression`, `gesture`, `voice`, `duration` opcional, condição `if` por flag, texto por chave de localização (`key`) ou por idioma (`text`) |
| Execução | `DialogueRunner`: máquina de escrever (38 caracteres/s), `advance()` (revela tudo, depois avança), `skip()` (se permitido), avanço automático por duração calculada, `talking` para animar a boca, `on_voice` para disparar a vocalização |
| Reações | `ReactionBank` por personagem em `data/locales/<idioma>.json` (`reactions.<personagem>.<contexto>`): falas curtas sem repetição imediata para `jump, hurt, stomp, coin_streak, relic, checkpoint, secret, power_*, boss_intro, boss_hit, boss_defeated, victory, defeat, world_unlock, idle_long` |
| Conteúdo | falas iniciais do Lume em português brasileiro (`dialogues.intro_1-1`), 17 contextos de reação com 3 variantes cada |
| Sincronização | o estado de animação `TALK` (máquina de animação) e `talking` do runner permitem boca/gestos; legendas via `Interface.subtitle` (etapa de interface) |

### Pendências

- Ligar as reações aos eventos do jogo na aplicação (`drain_events`) com legenda e vocalização (`voice_pitch` por personagem).
- Falas dos guardiões e de NPCs dependem das fichas de `docs/research/CHEFES.md` e das rotinas de NPC (próximos marcos).
- Vozes gravadas autorizadas não existem; a arquitetura aceita arquivos externos via `Sound` sem mudar a API.
