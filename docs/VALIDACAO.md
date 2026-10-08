# Validação de Lume

Verificações no ambiente de nuvem em 8 de outubro de 2026, com Node 24 e Chromium 151. Build sob `/Mario/`, sem buscar sprites, músicas ou serviços externos.

## Lógica

88 testes em dez arquivos Vitest. Colisões reais no chão/parede/teto, salto variável, coyote time, buffering, controle aéreo, pausa, resultado a 30/60/144 Hz, gelo, checkpoint; moedas, blocos, canos, plataformas; dano, casco, armadura, tiro, duração da estrela, crescimento sob teto, lava/água; progressão e recuperação de dados corrompidos.

Cinco guardiões exercitados com dados reais em arenas isoladas: vulnerabilidade, cooldown, ataques, segunda fase e saída bloqueada. Na derrota dessas arenas, poderes são itens coletados no spawn da fixture; o teste de campanha usa os itens dos mapas completos.

## Campanha inteira

`tests/helpers/route-player.ts` lê a simulação e envia comandos normais para `Game.update`. Não teleporta, altera HP/vidas, concede poderes, desativa perigos ou remove inimigos. Os quinze testes usam mapas intactos, coleta natural de poderes e vidas iniciais padrão; verificam bandeira, checkpoint, moedas e ausência de chefes vivos.

Todas as quinze fases concluídas. Treze sem morte; Ruínas dos Vagalumes com duas e A Última Chama com uma. Cinco chefes derrotados. Isso demonstra uma rota funcional em cada mapa; não prova exploração de todas as estratégias ou rotas opcionais. O condutor ajusta corrida no gelo e observa ataques.

## Navegador

Quinze testes Playwright em Chromium: menus, mapa, teclado, salto, moedas, câmera, pausa/reinício/menu, configuração e persistência, confirmação de reset, recuperação de dados inválidos, WebAudio, gamepad virtual, dois dedos simultâneos, cancelamento/perda de foco e produção sob `/Mario/`. Guards verificam console e exceções sem ignorar erros. Pressionamentos rápidos de Esc e salto são retidos entre quadros; os dois casos de regressão passaram em cinco repetições cada antes da suíte completa de quinze testes.

Integração conclusão→localStorage usa `game.finish()` como fixture explícita. Travessia real é validada separadamente nos quinze testes de campanha. Produção usa build real sem a ponte `__lume` e coleta moedas pelo teclado.

WebAudio fica sem contexto antes de gesto e inicia após clique. Música/efeitos são silenciados independentemente. Isso verifica o grafo de áudio; mixagem final não foi avaliada por audição humana.

Gamepad usa `navigator.getGamepads` simulado. Toque usa eventos Chrome DevTools em viewport com capacidade de toque. Não foram usados controles ou celulares físicos; Firefox/Safari não executados.

## Entrega e limites externos

Typecheck, build, instalação com lockfile e reinício do fluxo foram verificados. Capturas em `docs/images` mostram o jogo renderizado no Chromium.

Workflow Pages preparado e acesso à API verificado. Ainda não há confirmação de workflow remoto ou endereço público funcional. Publicar o ambiente de nuvem é uma ação separada nas configurações do ambiente.
