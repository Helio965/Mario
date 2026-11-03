# Personagens (implementação)

Pesquisa de referência: `docs/research/PERSONAGENS.md` (fichas de Mario, Luigi, Peach, Daisy, Toad, Toadette, Yoshi, Rosalina, Wario, Waluigi, Donkey Kong e Nabbit; linha do tempo das abordagens de elenco; envelopes numéricos). Este documento descreve o que está **implementado e testado**.

## Modelo escolhido: núcleo compartilhado + variações por envelope + habilidades

Decisão da pesquisa (§10.1), adotada integralmente:

1. Todos os personagens compartilham `MovementProfile`, hitboxes (22 × 30 / 22 × 46) e o modelo de dano. As 15 fases e os traces de ouro continuam válidos.
2. Cada personagem aplica um `CharacterDelta` limitado por envelope: altura do salto 0,85–1,21×, corrida 0,93–1,12×, atrito 0,6–1,3× (`game/characters/roster.py`, `within_envelope()`).
3. Habilidades que mudam o alcance são limitadas em tempo e velocidade e nunca são exigidas por rotas obrigatórias.
4. Um personagem invencível a inimigos para iniciantes (modelo Nabbit/Yoshi), com as mesmas regras de poço, lava e tempo.
5. Regra de ouro verificada por teste: os vãos do caminho principal das 15 fases são transponíveis por **todos** os personagens (validador com a física real, perfis legado e calibrado).

## Elenco original

| Personagem | Arquétipo estudado | Delta (sobre o perfil base) | Habilidade | Dano | Desbloqueio |
| --- | --- | --- | --- | --- | --- |
| **Lume** | Mario "all-rounder" | nenhum | fogo | padrão | início |
| **Vento** | Luigi (Lost Levels / NSLU / 3D World) | salto ×1,10 em velocidade (altura ×1,21), atrito ×0,60, gelo ×0,75, aceleração ×0,90 | *scuttle*: gravidade de queda ×0,7 segurando o salto | padrão | mundo 2 |
| **Fagulha** | Toad (SMB2 / 3D World) | salto ×0,92 (altura ×0,85), corrida ×1,12, caminhada ×1,11, arrancada ×1,20 | salto carregado: agachada parada por 0,5 s → impulso ×1,175 (SMB2 *Power Squat*); mover cancela | padrão | mundo 3 |
| **Aurora** | Peach (SMB2 / 3D World) com limites | corrida ×0,93, arrancada ×1,10 | flutuação: após o ápice, segurando o salto, até 0,8 s, uma vez por salto, teto horizontal 220 px/s (alcance extra ≤ 180 px) | padrão | mundo 4 |
| **Pirilampo** | Nabbit / Yoshi (NSLU / NSMBU Deluxe / Wonder) | atrito ×1,30, gelo ×2,2 | nenhuma (não dispara) | **invencível a inimigos**: empurrão 160 px/s + 0,3 s sem controle; poderes viram +250 pts e 1 moeda; +100 s por fase; poço/lava/água/tempo matam | início |

Dados declarativos em `data/characters/*.json` (nome por idioma, paleta, delta, habilidades, modelo de dano, bônus de tempo, desbloqueio, clipes de animação e tom de voz). Descrições em `data/locales/pt-BR.json` (`characters.*`).

## Verificação

| Teste | Resultado |
| --- | --- |
| `test_roster.py`: envelopes, perfis derivados sem alterar o base, violações reportadas | aprovado |
| `test_abilities.py`: Lume idêntico ao base; scuttle alonga a queda; salto carregado após 0,5 s e cancelado ao mover; flutuação limitada e única por salto; Pirilampo empurrado sem perder vida/poder, sem projéteis, morre em lava; +100 s | aprovado |
| `test_roster_levels.py`: vãos do caminho principal transponíveis por cada personagem (validador com física real) | aprovado, nos perfis legado e calibrado (alturas de salto 95–136 px, alcances 240–285 px) |
| Traces de ouro com `Game([level])` (Lume) | idênticos |
| Condutor de campanha com previsão de pouso, perfil legado | Fagulha 15/15, Pirilampo 15/15, Vento 14/15 (5-2 fica preso; o condutor não considera o atrito menor ao parar), Aurora 13/15 (2-3 e 5-2: a flutuação acionada pelo tempo de salto do condutor altera o pouso previsto) |

As duas últimas linhas mostram limitação do **condutor automático**, não das fases: o validador geométrico confirma que todo vão obrigatório é transponível por todos. Um condutor ciente do personagem (frenagem antecipada para Vento, flutuação controlada para Aurora) está previsto junto com a reconstrução das fases.

## Animação e expressividade

A máquina de estados de animação (`game/characters/animation.py`) é compartilhada; `ClipSpec` por personagem vem do JSON (`clips`). Estados específicos previstos pela pesquisa para a etapa de sprites: `FLOAT` (Aurora, capa aberta), `CHARGE` (Fagulha piscando após 0,5 s), `SCUTTLE` (Vento substituindo `FALL` ao segurar o salto) e `BUMP` (Pirilampo em vez de `HURT`). Voz: vocalizações sintetizadas com tom por personagem (`voice_pitch`), nunca dublagem imitada.

## Limitações atuais

- Os sprites dos quatro personagens novos ainda não existem; o pipeline de spritesheets é a próxima etapa (direção artística em `docs/research/GRAFICOS.md`/`ANIMACOES.md`).
- Seleção de personagem na interface e desbloqueio por mundo serão ligados ao salvamento (`settings.character`) na etapa de interface.
- Rampas, natação e agachamento físico não existem no núcleo; o agachamento atual é apenas estado (carga do salto e animação).
