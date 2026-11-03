# Licenças e recursos

## Código e conteúdo do projeto

- Licença do repositório: **MIT** (arquivo `LICENSE`, © 2026 Hélio), preservada da versão original.
- Todo o conteúdo criativo é **original** e nasce no repositório: personagens (Lume, Vento, Fagulha, Aurora, Pirilampo), cenários dos cinco mundos, inimigos, guardiões, ícone, textos, diálogos, trilhas e efeitos sonoros.
- Arte e som são **produzidos por código** (pixel art procedural e síntese numpy). Não há sprites, gravações, músicas, modelos ou código extraídos de jogos comerciais; nenhuma ROM foi usada.
- O projeto **não é afiliado nem endossado pela Nintendo**. Super Mario e os personagens citados na pesquisa (`docs/research/`) pertencem aos seus titulares e foram estudados apenas como referência de design, a partir de fontes públicas legítimas listadas em `docs/research/REFERENCIAS.md`.

## Dependências de execução (verificadas pelos metadados instalados)

| Pacote | Versão verificada | Licença | Uso |
| --- | --- | --- | --- |
| pygame-ce | 2.5.8 | LGPL v2.1 | janela, renderização, entrada, mixer (ligação dinâmica; sem modificação da biblioteca) |
| numpy | 2.5.4 | BSD-3-Clause (com partes 0BSD, MIT, Zlib, CC0-1.0) | síntese de áudio |

## Dependências de desenvolvimento e ferramentas

| Pacote | Versão verificada | Licença | Uso |
| --- | --- | --- | --- |
| pytest / pytest-cov | 9.2.0 / 7.1.0 | MIT | testes |
| ruff | 0.17.3 | MIT | lint e formatação |
| mypy | 2.4.1 | MIT | tipagem |
| Pillow | 13.0.0 | MIT-CMU | pipeline de spritesheets (ferramentas) |
| pygbag | 0.9.3 | MIT | investigação de distribuição para navegador |
| PyInstaller | a instalar com `.[build]` | GPL-2.0 com exceção para o bootloader (o executável gerado não herda a GPL) | executável Windows |

Nenhuma dependência de execução é enviada em forma modificada; os avisos de licença das bibliotecas devem acompanhar o executável distribuído (PyInstaller inclui os metadados dos pacotes em `dist/Lume/_internal`).

## Fontes tipográficas

A interface usa a fonte padrão embutida do pygame-ce (`freesansbold.ttf`, licença do pacote). Fontes adicionais em `assets/fonts/` deverão ter licença permissiva (OFL/MIT) registrada aqui antes de entrar no repositório.

## Recursos ainda não existentes

`assets/` será preenchido pelo pipeline de sprites (PNG + JSON gerados por `tools/`); cada conjunto gerado deve ser registrado nesta página com origem (script gerador) e licença (MIT do repositório).

## Política

- Não incorporar material protegido sem autorização escrita; se houver autorização para personagens licenciados no futuro, os sistemas (elenco por JSON, localização, diálogos) já permitem conteúdo alternativo sem alterar o código.
- Nenhuma clonagem de voz de pessoas reais; vocalizações são sintetizadas.
- Capturas em `docs/images/` são do próprio jogo.
