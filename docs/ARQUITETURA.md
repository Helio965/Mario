# Plano técnico

Lume — As Cinco Fronteiras é um jogo independente de plataforma para navegador. A licença MIT existente é preservada. Arte e áudio serão produzidos por código original; nenhum arquivo Nintendo será usado.

## Estrutura

- `src/core`: tipos, física AABB em passos fixos de 1/120 s e simulação testável sem DOM.
- `src/data`: mapas declarativos de 15 fases em cinco mundos.
- `src/render`: pixel art Canvas, animações, partículas e parallax em resolução 960 × 540.
- `src/systems`: entrada de teclado/toque/gamepad, Web Audio e persistência versionada.
- `src/ui`: menus, HUD, mapa, pausa e configurações acessíveis.
- `tests`: verificações de lógica e fluxos reais em Chromium.

Canvas 2D evita dependências de runtime; Vite e TypeScript cuidam de desenvolvimento e build. A colisão usa deslocamentos pequenos em passo fixo, com resolução por eixo, tolerância de salto e buffering. A progressão libera uma fase por vez e guarda recordes e relíquias localmente.

## Etapas e validação

1. Estrutura: instalação, typecheck, servidor e build.
2. Motor: chão, paredes, salto, câmera e controles.
3. Interações: moedas, blocos e passagens.
4. Primeira fase: rota completa testada.
5. Inimigos e poderes: dano, projéteis e transformações.
6. Mapas: três composições distintas por mundo e dificuldade crescente.
7. Chefes: vulnerabilidade, ataques, vitória e progressão.
8. Interface: menus, configurações e recuperação de salvamento inválido.
9. Extras: som original, toque simultâneo, gamepad e partículas.
10. Entrega: testes completos, documentação e GitHub Actions para Pages.

Cada etapa terá commit próprio. A implementação do jogo é autorizada pelo pedido enviado em `Texto colado.txt`; ela é um trabalho de desenvolvimento além da configuração do ambiente. Publicação será declarada apenas depois de verificarmos acesso e resposta do site.
