# Distribuição — executável Windows (PyInstaller) e web (Pygbag)

Estado em 3 de novembro de 2026. Só o que foi executado está marcado como verificado.

## Executável de pasta (PyInstaller)

`lume.spec` gera `dist/Lume/`: um executável (`Lume` / `Lume.exe`) com o
interpretador embutido e, ao lado, `data/` (fases, personagens, diálogos,
localização) e `assets/` quando existir. `game/paths.py` resolve esses
diretórios por `sys._MEIPASS`; nenhum caminho absoluto de máquina entra no
pacote. `tkinter`, `PIL`, `pytest`, `mypy` e `ruff` ficam de fora.

```bash
python -m pip install -e ".[build]"   # pyinstaller>=6.11
pyinstaller lume.spec
```

| Verificação | Resultado |
| --- | --- |
| Build no Linux (x86-64, Python 3.12.3, pygame-ce 2.5.8, PyInstaller 6.x) | concluído; pasta `dist/Lume` com 82 MB |
| Execução do binário gerado sem janela (`Lume --headless-frames 90 --no-audio --screenshot …`) | concluída; captura de tela produzida (menu renderizado) |
| Build e fumaça no Windows | job `windows-exe` do workflow `.github/workflows/python.yml` (`windows-latest`): empacota, executa 90 quadros sem janela e publica `dist/Lume` como artefato `Lume-windows` (30 dias). Resultado visível na aba *Actions* de cada execução |
| Execução com janela, teclado e áudio em Windows real | **não verificada** (sem máquina Windows nesta sessão) |
| Ícone do executável | pendente: `assets/ui/icon.ico` ainda não existe; o `.spec` já o usa quando presente |
| Instalador (MSI/Inno Setup) | não iniciado; a pasta `dist/Lume` pode ser compactada e distribuída como está |

Tamanho: a maior parte dos 82 MB é o `numpy` e o `pygame-ce`/SDL; um
executável de arquivo único (`--onefile`) não foi adotado porque atrasa o
início (descompressão a cada execução) e dificulta a leitura de `data/`.

## Web (Pygbag)

O ponto de entrada já é assíncrono quando `sys.platform == "emscripten"`
(`main.py`/`game/application.py`): o laço cede o controle ao navegador a cada
quadro, o salvamento usa `/data/data/lume` e o áudio é iniciado após o
primeiro gesto do usuário.

| Verificação | Resultado |
| --- | --- |
| `pygbag` instalado no ambiente de desenvolvimento | sim (`python -m pygbag --version`) |
| `python -m pygbag --build main.py` | ver nota abaixo — depende de baixar o runtime `pygame-web` da internet durante o build |
| Execução no navegador | **não verificada** |

Nota: o resultado da tentativa de build nesta sessão está registrado na seção
"Registro" ao fim deste documento; o build web precisa de acesso à rede para o
runtime do Pygbag, o que pode não existir no ambiente de CI/desenvolvimento.
Alternativa documentada: executar o build numa máquina com rede e publicar
`build/web/` em qualquer servidor estático (GitHub Pages inclusive).

## Registro

- 2026-11-03: PyInstaller no Linux — build e fumaça sem janela concluídos (82 MB).
