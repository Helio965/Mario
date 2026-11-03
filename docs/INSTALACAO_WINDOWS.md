# Instalação e execução no Windows

Requisitos: Windows 10/11 de 64 bits, [Python 3.12](https://www.python.org/downloads/windows/) (marque "Add python.exe to PATH" no instalador) e Git. Não há dependência de Node.js, navegador ou serviços externos.

## 1. Obter o código

```powershell
git clone https://github.com/Helio965/Mario.git
cd Mario
```

## 2. Ambiente virtual e dependências

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Se o PowerShell bloquear a ativação, execute uma vez `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` ou use o `cmd`: `.\.venv\Scripts\activate.bat`.

As dependências de execução são apenas `pygame-ce` e `numpy`; `[dev]` adiciona `pytest`, `ruff`, `mypy` e `Pillow` (ferramentas).

## 3. Executar

```powershell
python main.py
```

Opções úteis:

```powershell
python main.py --level 2-1      # começar em uma fase desbloqueada
python main.py --windowed       # ignorar tela cheia salva
python main.py --no-audio       # sem mixer
python main.py --version
```

`F11` alterna tela cheia. O progresso é gravado em `%APPDATA%\Lume\save.json` (escrita atômica; arquivos corrompidos voltam a dados seguros). Para importar o progresso da versão de navegador, veja `python -m tools.import_browser_save --help`.

## 4. Testar e verificar qualidade

```powershell
python -m pytest -q
ruff check game tests tools
ruff format --check game tests tools
mypy
```

## 5. Gerar o executável

```powershell
python -m pip install -e ".[build]"
pyinstaller lume.spec
```

O resultado fica em `dist\Lume\` (ver `docs/DISTRIBUICAO.md`). O executável localiza `data/` e `assets/` por `sys._MEIPASS` (`game/paths.py`); nenhum caminho absoluto é usado.

## Estado da verificação

| Item | Estado |
| --- | --- |
| Instalação com `pip install -e ".[dev]"` | verificada em Linux (CI) e Windows (CI `windows-latest`) quando o workflow for executado |
| Execução local com janela no Windows | **não verificada nesta sessão** (ambiente de desenvolvimento sem Windows nem tela); a execução headless é testada em CI |
| Executável PyInstaller | build e fumaça sem janela verificados no Linux; no Windows o job `windows-exe` do CI empacota e publica `dist/Lume` como artefato (ver `docs/DISTRIBUICAO.md`) |
