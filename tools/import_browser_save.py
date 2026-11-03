"""Importa o progresso da versão de navegador (localStorage ``lume-save-v1``).

Uso:
    python -m tools.import_browser_save caminho/para/export.json [--merge]

Como obter o arquivo no navegador: abra o jogo antigo, pressione F12 →
Console e execute ``copy(localStorage.getItem("lume-save-v1"))``; cole o
conteúdo em um arquivo .json. Também aceita um objeto ``{"lume-save-v1": ...}``.
A importação nunca é automática: o armazenamento local do navegador não é
acessível diretamente por um programa Python.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from game.systems.save import default_storage, import_browser_export, load_save, write_save


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("file", type=Path, help="JSON exportado do navegador")
    parser.add_argument(
        "--merge", action="store_true", help="mantém o melhor de cada campo em vez de substituir"
    )
    args = parser.parse_args(argv)
    try:
        text = args.file.read_text(encoding="utf-8")
    except OSError as error:
        print(f"Não foi possível ler {args.file}: {error}", file=sys.stderr)
        return 2
    imported = import_browser_export(text)
    if imported is None:
        print(
            "O arquivo não contém um salvamento reconhecível (esperado version 1 ou 2).",
            file=sys.stderr,
        )
        return 1
    storage = default_storage()
    if args.merge:
        current = load_save(storage)
        imported.unlocked = max(current.unlocked, imported.unlocked)
        imported.completed = list(dict.fromkeys([*current.completed, *imported.completed]))
        imported.relics = list(dict.fromkeys([*current.relics, *imported.relics]))
        imported.achievements = list(dict.fromkeys([*current.achievements, *imported.achievements]))
        for level_id, score in current.records.items():
            imported.records[level_id] = max(score, imported.records.get(level_id, 0))
        imported.settings = current.settings
    if not write_save(imported, storage):
        print(f"Falha ao gravar em {storage.path}", file=sys.stderr)
        return 1
    print(
        f"Progresso importado para {storage.path}: {len(imported.completed)} fases concluídas, fase {imported.unlocked + 1} desbloqueada."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
