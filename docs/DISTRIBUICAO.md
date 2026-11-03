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

```bash
python -m tools.build_web          # empacota build/web-src/lume/build/web (index.html + lume.apk)
python -m tools.build_web --serve  # idem e serve em http://localhost:8000 com o servidor do Pygbag
```

`tools/build_web.py` copia só `main.py`, `game/`, `data/` e `assets/` para uma
pasta limpa antes de chamar o Pygbag: empacotar a raiz do repositório arrastava
`.venv` e `node_modules` (110 MB); a pasta limpa gera um `lume.apk` de 217 KB.

| Verificação | Resultado |
| --- | --- |
| `pygbag` 0.9.x instalado no ambiente de desenvolvimento | sim |
| `python -m tools.build_web` (build) | concluído: `index.html`, `lume.apk` (217 KB), `lume.tar.gz`; o modelo e o ícone vêm da CDN `pygame-web.github.io/cdn/0.9.3/` (precisa de rede) |
| Abertura em Chromium sem janela (Playwright, via o proxy de rede desta sessão) | o runtime (`pythons.js`, `cpython312/main.wasm`) carrega e busca `lume.tar.gz`; `browserfs.min.js` responde 404 na CDN (sem sistema de arquivos persistente) e, em 8 minutos, o interpretador não chegou a imprimir a importação do pygame — **execução no navegador não confirmada** nesta sessão (rede lenta/intermediada) |
| Execução em navegador com rede normal | **não verificada** — passo a passo: `python -m tools.build_web --serve`, abrir `http://localhost:8000`, clicar para liberar o áudio |

Limitações conhecidas do alvo web, a confirmar quando a execução for possível:
`numpy` precisa existir como roda wasm na CDN do Pygbag (o áudio procedural usa
`numpy`); se faltar, o áudio deve ser desligado no navegador. O salvamento
depende do BrowserFS/IndexedDB do runtime.

## Registro

- 2026-11-03: PyInstaller no Linux — build e fumaça sem janela concluídos (82 MB).
- 2026-11-03: Pygbag — build limpo (217 KB) com `tools/build_web.py`; runtime carrega em Chromium sem janela, mas o interpretador não iniciou em 8 min através do proxy; `browserfs.min.js` 404 na CDN 0.9.3.
