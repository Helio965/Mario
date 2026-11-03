"""Regenerate the data-driven tables of the documentation.

    python tools/gen_docs.py            # writes docs/technical/REGISTRO_INIMIGOS.md tables

Tables are produced from lume/data/enemies.json, the behaviour registry and
the rig registry, so the documentation cannot drift from the data.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from lume.core.behaviors import BEHAVIORS  # noqa: E402
from lume.core.species import load_profiles  # noqa: E402
from lume.levels.campaign import load_campaign  # noqa: E402
from lume.render.enemies import RIGS  # noqa: E402

BEGIN, END = "<!-- tabela:inicio -->", "<!-- tabela:fim -->"


def species_table() -> str:
    campaign = load_campaign()
    used: dict[str, list[str]] = {}
    for level in campaign.levels:
        for e in level.enemies:
            used.setdefault(e.species, [])
            if level.id not in used[e.species]:
                used[e.species].append(level.id)
    rows = ["| ID | Nome | Papel (referência de função) | Habitats | Família | Nível | Fraquezas | Introduzida em | Arte | Em uso |",
            "| -- | ---- | ---------------------------- | -------- | ------- | ----- | --------- | -------------- | ---- | ------ |"]
    for p in load_profiles().values():
        art = "dedicada" if p.animation_set in RIGS else "provisória"
        behaviour = p.behavior if p.behavior in BEHAVIORS else f"{p.behavior} (ausente)"
        rows.append(
            f"| `{p.id}` | {p.name}{' (chefe)' if p.boss else ''} | {p.role_reference} | {', '.join(p.habitats)} | {behaviour} | {p.difficulty_tier} | "
            f"{', '.join(p.weaknesses) or 'indestrutível'} | {p.introduced_in or '—'} | {art} | {len(used.get(p.id, []))} fase(s) |"
        )
    return "\n".join(rows)


def replace_block(path: Path, content: str) -> None:
    text = path.read_text(encoding="utf-8")
    start, end = text.index(BEGIN) + len(BEGIN), text.index(END)
    path.write_text(text[:start] + "\n" + content + "\n" + text[end:], encoding="utf-8")


if __name__ == "__main__":
    replace_block(ROOT / "docs" / "technical" / "REGISTRO_INIMIGOS.md", species_table())
    print("ok")
