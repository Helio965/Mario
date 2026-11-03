"""Valida as fases de ``data/levels`` (esquema + geometria + saltos com a física real).

Uso:
    python -m tools.validate_levels [--profile legacy|calibrated] [--character lume] [--no-jumps] [ids...]

Sai com código 1 se houver erros. Avisos não falham.
"""

from __future__ import annotations

import argparse
import json
import sys

from game.characters.roster import get_character
from game.levels.loader import level_from_dict, levels_dir, load_index
from game.levels.validator import errors, validate_level, validate_level_dict
from game.physics.movement import PROFILES


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("ids", nargs="*", help="ids das fases (padrão: todas)")
    parser.add_argument("--profile", choices=sorted(PROFILES), default="legacy")
    parser.add_argument("--character", default="lume")
    parser.add_argument("--no-jumps", action="store_true", help="não simular os vãos")
    args = parser.parse_args(argv)
    profile = get_character(args.character).profile(PROFILES[args.profile])
    failed = False
    for entry in load_index()["levels"]:
        if args.ids and entry["id"] not in args.ids:
            continue
        with open(levels_dir() / entry["file"], encoding="utf-8") as handle:
            raw = json.load(handle)
        issues = validate_level_dict(raw)
        if not errors(issues):
            issues += validate_level(level_from_dict(raw), profile, check_jumps=not args.no_jumps)
        bad = errors(issues)
        failed = failed or bool(bad)
        status = "ERRO" if bad else "ok"
        print(f"{entry['id']:4} {status:4} {len(bad)} erro(s), {len(issues) - len(bad)} aviso(s)")
        for issue in issues:
            print(f"      {issue}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
