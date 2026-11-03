# Testes da campanha

Executar tudo: `python -m pytest` (≈ 13 s; usa os drivers SDL "dummy", sem janela nem som). CI: `.github/workflows/python.yml`. A versão web mantém sua própria suíte (`npm test`, `npm run test:e2e`).

## Suítes

| Arquivo | O que verifica |
| ------- | -------------- |
| `test_physics.py` | port da suíte TS: colisões, salto variável, coyote time, buffer, controle aéreo, teto, paredes finas, queda em velocidade terminal, gelo, checkpoints e reaparecimento; novos: plataformas de mão única, molas, esteiras, natação, vento |
| `test_interactions.py` | moedas e relíquias, blocos, canos e segredos, plataformas móveis e frágeis, blocos ocultos, grupos de moedas, múltiplos checkpoints |
| `test_combat.py` | pisão, dano lateral, poderes, crescimento sob teto, cascos, armadura, fogo, imunidade ao fogo, estrela, atiradores, água/lava, asas que caem, topo espinhoso |
| `test_behaviors.py` | famílias novas: notar o jogador, planta emergente (e timidez), saltador com antecipação, investida e tontura, deslize no gelo, escaravelho que se enterra, cauda periódica, ossada que se remonta, sombra que reage à luz, ativação por proximidade |
| `test_bosses.py` | os cinco guardiões (janela de dano, segunda fase, saída bloqueada, derrota com poderes coletados) e o Javali Espinheiro (ciclo, colisão com parede, espinhos fora da janela, três pisões, segunda fase) |
| `test_levels.py` | 10 mundos e 60 IDs únicos; fases legadas preservadas; validação da campanha sem erros; estrutura individual de cada fase implementada; simulação detecta vão impossível; mensagens de erro com caminho JSON; bioma incompatível rejeitado |
| `test_campaign_routes.py` | **cada fase implementada** é concluída pelo robô com entradas normais, inimigos e perigos ativos, checkpoint alcançado, chefes derrotados, dentro do orçamento de mortes (`lume/qa/budgets.py`) e sem alterar os dados da fase |
| `test_save.py` | formato 2, migração sem perdas do formato web, cópia de segurança de arquivos corrompidos, escrita atômica, importação de exportação do navegador, saneamento, conquistas derivadas |
| `test_graphics.py` | quadros reais: todas as fases em 720p; primeira fase em 720p, 1080p e 4K com verificação de densidade de textura (moeda e cabeça do Lume rasterizadas no tamanho exato); barras laterais em 21:9; todas as sub-áreas (salas secretas, túneis); todos os estados do Lume; relatório de espécies com arte provisória |

## O robô de rotas (`lume/qa/route_bot.py`)

Tem a mesma autoridade de uma pessoa com controle: lê o estado e chama `Game.update` com entradas comuns; nunca teleporta, concede itens, altera vidas ou remove perigos. Capacidades: corrida e saltos em vãos, paredes, inimigos, perigos e projéteis; busca de blocos de poder; **previsão de pouso** contra as posições futuras de plataformas móveis (espera na borda e salta quando o arco termina em algo sólido); uso de molas; escalada de plataformas de mão única; descida por buracos que levam a chão seguro (abismos nunca); espera da Flor-Mordedora recolher; controle aéreo por simulação quando a trajetória termina em abismo; táticas para guardiões e para o Javali.

O robô encontrou problemas reais de projeto que foram corrigidos: mola longe do penhasco (o jogador ficava preso), túnel que podia ser evitado, mola enterrada no terreno, besouro voando na altura da cabeça antes de um ouriço, plataforma frágil sobre o salto obrigatório do Cânion, chefe que voltava a atacar sem dar espaço depois do pisão.

## Limites (importante)

Uma rota concluída prova que a fase é **atravessável** com a física real — não prova que é divertida, legível ou bem balanceada, nem que todas as rotas opcionais funcionam. O robô não substitui testes com pessoas. Testes gráficos usam o renderizador por software (sem GPU) e conferem que o quadro existe e tem conteúdo e densidade corretos; a qualidade estética foi avaliada por inspeção das capturas.

## Matriz de qualidade

`python tools/quality_matrix.py --render` calcula a matriz das 60 fases a partir dessas verificações (nada é preenchido à mão). "Concluída" exige: estrutura sem erros, arte dedicada (mundo e todas as espécies), rota concluída, renderização ok, desempenho medido, 3 relíquias e ficha no plano. O resultado atual está em `docs/RELATORIO_EXPANSAO.md`.
