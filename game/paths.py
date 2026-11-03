"""Localização de recursos (dados, assets) independente do diretório atual.

Funciona no checkout do repositório e dentro de um executável PyInstaller
(``sys._MEIPASS``). Nenhum caminho absoluto de máquina é usado.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def project_root() -> Path:
    bundled = getattr(sys, "_MEIPASS", None)
    if bundled:
        return Path(bundled)
    override = os.environ.get("LUME_ROOT")
    if override:
        return Path(override)
    return Path(__file__).resolve().parent.parent


def data_path(*parts: str) -> Path:
    return project_root().joinpath("data", *parts)


def asset_path(*parts: str) -> Path:
    return project_root().joinpath("assets", *parts)
