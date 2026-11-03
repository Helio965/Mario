"""Build web (Pygbag): copia só o que o jogo precisa para uma pasta limpa e empacota.

Uso:
    python -m tools.build_web [--serve]

O Pygbag empacota a pasta inteira do ``main.py``; rodar na raiz do repositório
arrastaria ``.venv``, ``node_modules`` e ``build``. Este script monta
``build/web-src/lume`` com ``main.py``, ``game/``, ``data/`` e ``assets/`` e chama
``python -m pygbag --build`` lá dentro. O resultado fica em
``build/web-src/lume/build/web`` (``index.html`` + ``lume.apk``); o runtime do
pygame-web é baixado da CDN na primeira execução (precisa de rede).
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STAGE = ROOT / "build" / "web-src" / "lume"
INCLUDE = ("main.py", "game", "data", "assets")
SKIP_DIRS = {"__pycache__", ".mypy_cache", ".ruff_cache"}


def stage() -> Path:
    if STAGE.exists():
        shutil.rmtree(STAGE)
    STAGE.mkdir(parents=True)
    for name in INCLUDE:
        source = ROOT / name
        if not source.exists():
            continue
        if source.is_file():
            shutil.copy2(source, STAGE / name)
        else:
            shutil.copytree(
                source,
                STAGE / name,
                ignore=shutil.ignore_patterns(*SKIP_DIRS, "*.pyc"),
            )
    return STAGE


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--serve", action="store_true", help="além de empacotar, servir em http://localhost:8000"
    )
    parser.add_argument("--app-name", default="Lume")
    args = parser.parse_args(argv)
    folder = stage()
    command = [sys.executable, "-m", "pygbag", "--app_name", args.app_name]
    if not args.serve:
        command.append("--build")
    command.append(str(folder / "main.py"))
    print(" ".join(command))
    return subprocess.call(command, cwd=folder)


if __name__ == "__main__":
    raise SystemExit(main())
