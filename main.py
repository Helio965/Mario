"""Ponto de entrada: ``python main.py`` (ou ``lume`` após instalação).

No navegador (Pygbag/Emscripten) o laço precisa ser cooperativo: ``asyncio``
cede o controle ao navegador a cada quadro.
"""

from __future__ import annotations

import asyncio
import sys

from game.application import main, main_async

if __name__ == "__main__":
    if sys.platform == "emscripten":
        asyncio.run(main_async())
    else:
        raise SystemExit(main())
