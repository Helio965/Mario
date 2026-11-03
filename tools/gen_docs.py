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


def load_note(d: dict) -> str:
    load, cpus = d.get("load_avg_1m"), d.get("cpus")
    if load is None:
        return "não registrada"
    busy = cpus and load > cpus * 0.75
    return f"{str(load).replace('.', ',')}/{cpus} CPUs" + (" (contenção: tempos inflados)" if busy else "")


def perf_table() -> str:
    """Measured frame costs from artifacts/perf/*.json (tools/profile_level.py)."""
    import json

    def num(v: float, digits: int = 1) -> str:
        return f"{v:,.{digits}f}".replace(",", "X").replace(".", ",").replace("X", ".")

    campaign = load_campaign()
    names = {e.id: (campaign.world(e.world).number, e.slot, e.name) for e in campaign.entries}
    rows = ["| Mundo | Fase | Resolução | Simulação (ms, média / p95) | Submissão Python (ms) | Quadro completo (ms, média / p95 / máx.) "
            "| FPS equivalente | Desenhos (média / máx.) | Texturas (MB) | Pré-carga (ms) | Carga da máquina |",
            "| ----- | ---- | --------- | --------------------------- | --------------------- | ----------------------------------------- "
            "| --------------- | ----------------------- | ------------- | -------------- | ---------------- |"]
    files = sorted((ROOT / "artifacts" / "perf").glob("*.json"))
    def key(path):
        data = json.loads(path.read_text(encoding="utf-8"))
        world, slot, _ = names.get(data["level"], (99, 99, data["level"]))
        w, h = map(int, data["resolution"].split("x"))
        return (world, slot, w * h)
    for path in sorted(files, key=key):
        d = json.loads(path.read_text(encoding="utf-8"))
        world, slot, name = names.get(d["level"], ("?", "?", d["level"]))
        fps = 1000.0 / d["frame_ms"]["avg"] if d["frame_ms"]["avg"] else 0
        rows.append(
            f"| {world} | {slot} · {name} | {d['resolution'].replace('x', '×')} | {num(d['update_ms']['avg'], 2)} / {num(d['update_ms']['p95'], 2)} "
            f"| {num(d['submit_ms']['avg'], 2)} | {num(d['frame_ms']['avg'])} / {num(d['frame_ms']['p95'])} / {num(d['frame_ms']['max'])} "
            f"| ≈ {fps:.0f} | {num(d['draw_calls']['avg'], 0)} / {d['draw_calls']['max']} | {num(d['texture_mb'])} | {num(d['preload_ms'], 0)} "
            f"| {load_note(d)} |")
    return "\n".join(rows)


def replace_block(path: Path, content: str, begin: str = BEGIN, end: str = END) -> None:
    text = path.read_text(encoding="utf-8")
    start, stop = text.index(begin) + len(begin), text.index(end)
    path.write_text(text[:start] + "\n" + content + "\n" + text[stop:], encoding="utf-8")


if __name__ == "__main__":
    replace_block(ROOT / "docs" / "technical" / "REGISTRO_INIMIGOS.md", species_table())
    replace_block(ROOT / "docs" / "technical" / "PERFORMANCE.md", perf_table(),
                  "<!-- desempenho:inicio -->", "<!-- desempenho:fim -->")
    print("ok")
