"""Famílias de arquétipos de inimigos (uma por módulo), descobertas automaticamente.

Cada módulo registra seus ``kind`` com ``game.enemies.behaviors.register``;
importar este pacote carrega todas as famílias. Para adicionar uma família,
basta criar o módulo aqui — nenhum arquivo compartilhado precisa mudar.
"""

from __future__ import annotations

import importlib
import pkgutil


def load_all() -> list[str]:
    """Importa todos os módulos do pacote e devolve seus nomes (ordem alfabética)."""
    names: list[str] = []
    for module in sorted(m.name for m in pkgutil.iter_modules(__path__)):
        importlib.import_module(f"{__name__}.{module}")
        names.append(module)
    return names


LOADED = load_all()
