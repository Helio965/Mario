# -*- mode: python ; coding: utf-8 -*-
"""Empacotamento com PyInstaller (``pyinstaller lume.spec``).

Gera ``dist/Lume/`` (pasta com executável e recursos). ``data/`` e ``assets/``
são copiados ao lado do executável e localizados em tempo de execução por
``game/paths.py`` (``sys._MEIPASS``). Nenhum caminho absoluto de máquina.
"""

from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules

ROOT = Path(SPECPATH)

datas = [(str(ROOT / "data"), "data")]
if (ROOT / "assets").exists():
    datas.append((str(ROOT / "assets"), "assets"))

hiddenimports = collect_submodules("game") + ["numpy", "pygame"]

a = Analysis(
    [str(ROOT / "main.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=["tkinter", "PIL", "pytest", "mypy", "ruff"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Lume",
    debug=False,
    strip=False,
    upx=False,
    console=False,
    icon=str(ROOT / "assets" / "ui" / "icon.ico") if (ROOT / "assets" / "ui" / "icon.ico").exists() else None,
)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name="Lume")
