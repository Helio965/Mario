"""Quality matrix of the 60 levels, computed from real checks (never typed by hand).

    python tools/quality_matrix.py [--render] [--profile] [--check] [--markdown out.md] [--json out.json]

Columns (docs/technical/TESTES_CAMPANHA.md):
  Estrutura  validator without errors (schema, references, geometry, biome, teaching order)
  Arte HD    "dedicada" only if the world has its own art set and every species in the
             level has a dedicated rig; "provisória" otherwise
  Inimigos   behaviours registered and dedicated rigs for every species
  Gameplay   route bot completes the level with ordinary inputs within the death budget
  Gráficos   frames render at 720p (spawn and every sub-area) when --render is used
  Desempenho artifacts/perf/<id>_1920x1080.json exists (measured; --profile measures it)
  Estado     Concluída only when every criterion passes; Parcial when implemented but
             something is missing; Planejada when only the design exists.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from lume.core.species import load_profiles  # noqa: E402
from lume.levels.campaign import load_campaign  # noqa: E402
from lume.levels.validate import errors, validate_level  # noqa: E402
from lume.qa.budgets import DEATH_BUDGET  # noqa: E402
from lume.qa.route_bot import play_route  # noqa: E402
from lume.render.enemies import RIGS  # noqa: E402
from lume.render.worlds import world_art  # noqa: E402
from lume.systems.audio import track_for, LEGACY  # noqa: E402

PERF_DIR = ROOT / "artifacts" / "perf"
PLAN = ROOT / "lume" / "data" / "plan" / "campaign_plan.json"


def compute(render: bool = False, profile: bool = False) -> list[dict]:
    campaign = load_campaign()
    profiles = load_profiles()
    biomes = {w.id: w.biome for w in campaign.worlds}
    planned = set()
    plan_by_id: dict[str, dict] = {}
    if PLAN.exists():
        try:
            plan_by_id = {lvl["id"]: lvl for lvl in json.loads(PLAN.read_text(encoding="utf-8")).get("levels", [])}
            planned = set(plan_by_id)
        except (ValueError, KeyError):
            planned = set()
    dedicated_world = {w.id: not getattr(world_art(w.id), "provisional", False) for w in campaign.worlds}
    rows = []
    display = None
    for entry in campaign.entries:
        world = campaign.world(entry.world)
        row = {"world": world.number, "world_id": world.id, "slot": entry.slot, "id": entry.id, "name": entry.name,
               "planned": entry.id in planned, "implemented": entry.implemented}
        if not entry.implemented:
            row.update(structure="pendente", art="pendente", enemies="pendente", gameplay="pendente", graphics="pendente",
                       performance="pendente", relics=0, plan="pendente", audio="pendente",
                       documented="sim" if row["planned"] else "não",
                       state="Planejada" if row["planned"] else "Não iniciada", notes=[])
            rows.append(row)
            continue
        level = campaign.level(entry.id)
        notes: list[str] = []
        probs = errors(validate_level(level, profiles, world_biome=biomes[level.world]))
        row["structure"] = "ok" if not probs else "erro"
        if probs:
            notes.append(f"{len(probs)} erro(s) estruturais")
        species = sorted({e.species for e in level.enemies})
        provisional = [s for s in species if profiles[s].animation_set not in RIGS]
        row["enemies"] = "ok" if not provisional else "parcial"
        art_ok = dedicated_world[level.world] and not provisional
        row["art"] = "dedicada" if art_ok else "provisória"
        if not dedicated_world[level.world]:
            notes.append("conjunto artístico do mundo provisório")
        if provisional:
            notes.append("rigs provisórios: " + ", ".join(provisional))
        result = play_route(level, 150, run=level.id != "blue_ascent")
        budget = DEATH_BUDGET.get(level.id, 0)
        ok = result.completed and result.deaths <= budget and not result.game.bosses_alive()
        row["gameplay"] = "ok" if ok else "falha"
        row["route"] = {"seconds": round(result.ticks / 120, 1), "deaths": result.deaths, "coins": result.game.coins_total}
        if not ok:
            notes.append(f"rota: {result.game.status}, {result.deaths} morte(s)")
        row["relics"] = len(level.collectibles)
        if row["relics"] < 3:
            notes.append(f"{row['relics']} relíquia(s) (meta 3)")
        row["audio"] = "ok" if track_for(level.music) is not LEGACY[0] or level.music == "menu" else "faixa genérica"
        if row["audio"] != "ok":
            notes.append("áudio: faixa genérica")
        # conformance with the level's sheet in the 60-level plan (criteria 5, 10, 11)
        plan = plan_by_id.get(level.id)
        gaps = []
        if plan is not None:
            regular = [e for e in level.enemies if not profiles[e.species].boss]
            want = int(plan.get("planned_enemy_count", {}).get("min", 0))
            if len(regular) < want:
                gaps.append(f"inimigos {len(regular)}/{want}")
            want_cp = int(plan.get("checkpoints", 0))
            if len(level.checkpoints) < want_cp:
                gaps.append(f"checkpoints {len(level.checkpoints)}/{want_cp}")
            want_secrets = len(plan.get("secrets", []))
            if len(level.secrets) < want_secrets:
                gaps.append(f"segredos {len(level.secrets)}/{want_secrets}")
        row["plan"] = "ok" if plan is not None and not gaps else ("sem plano" if plan is None else "parcial")
        if gaps:
            notes.append("abaixo do plano: " + ", ".join(gaps))
        if render:
            from lume.core.game import Game
            from lume.render.display import Display
            from lume.render.scene import Scene

            display = display or Display((1280, 720), hidden=True)
            try:
                for area in level.areas:
                    scene = Scene(display)
                    game = Game([level])
                    if area is not level.areas[0]:
                        floor = min((p.y for p in level.platforms if p.kind in ("ground", "ledge") and area.x <= p.x + p.w / 2 < area.x + area.w
                                     and area.y < p.y < area.y + area.h), default=area.y + area.h - 100)
                        game.player.x, game.player.y = area.x + area.w / 2, floor - game.player.h - 1
                        game.camera.snap(game)
                    scene.render(game, 1 / 60)
                row["graphics"] = "ok"
            except Exception as exc:  # pragma: no cover - reported in the matrix
                row["graphics"] = "erro"
                notes.append(f"render: {exc}")
        else:
            row["graphics"] = "não executado"
        perf = PERF_DIR / f"{level.id}_1920x1080.json"
        if profile and not perf.exists():
            from tools_profile import profile as run_profile  # type: ignore

            PERF_DIR.mkdir(parents=True, exist_ok=True)
            perf.write_text(json.dumps(run_profile(level.id, (1920, 1080), 12), indent=1), encoding="utf-8")
        row["performance"] = "medido (software)" if perf.exists() else "não medido"
        row["documented"] = "sim" if row["planned"] else "não"
        if not row["planned"]:
            notes.append("sem ficha no plano de 60 fases")
        complete = all([
            row["structure"] == "ok", row["art"] == "dedicada", row["enemies"] == "ok", row["gameplay"] == "ok",
            row["graphics"] == "ok", row["performance"].startswith("medido"), row["relics"] >= 3, row["planned"],
            row["plan"] == "ok", row["audio"] == "ok",
        ])
        row["state"] = "Concluída" if complete else "Parcial"
        row["notes"] = notes
        rows.append(row)
    if display is not None:
        display.close()
    return rows


def markdown(rows: list[dict]) -> str:
    out = ["| Mundo | Fase | Nome | Estrutura | Arte HD | Inimigos | Gameplay | Gráficos | Desempenho | Relíquias | Plano | Áudio | Documentada | Estado |",
           "| ----- | ---- | ---- | --------- | ------- | -------- | -------- | -------- | ---------- | --------- | ----- | ----- | ----------- | ------ |"]
    for r in rows:
        out.append(f"| {r['world']} | {r['slot']} | {r['name']} | {r['structure']} | {r['art']} | {r['enemies']} | {r['gameplay']} | "
                   f"{r['graphics']} | {r['performance']} | {r['relics']} | {r.get('plan', '-')} | {r.get('audio', '-')} | "
                   f"{r['documented']} | {r['state']} |")
    counts: dict[str, int] = {}
    for r in rows:
        counts[r["state"]] = counts.get(r["state"], 0) + 1
    out.append("")
    out.append("Resumo: " + ", ".join(f"{k}: {v}" for k, v in sorted(counts.items())))
    notes = [r for r in rows if r.get("notes")]
    if notes:
        out.append("")
        out.append("Pendências por fase (geradas pelas verificações):")
        out.append("")
        for r in notes:
            out.append(f"- `{r['id']}`: " + "; ".join(r["notes"]))
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--render", action="store_true")
    ap.add_argument("--profile", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--markdown")
    ap.add_argument("--json")
    ap.add_argument("--from-json", help="reuse rows computed earlier instead of recomputing")
    ap.add_argument("--update-report", action="store_true",
                    help="replace the matrix block in docs/RELATORIO_EXPANSAO.md")
    a = ap.parse_args()
    if a.profile:
        sys.path.insert(0, str(ROOT / "tools"))
        import importlib

        sys.modules["tools_profile"] = importlib.import_module("profile_level")
    if a.from_json:
        rows = json.loads(Path(a.from_json).read_text(encoding="utf-8"))
    else:
        rows = compute(render=a.render, profile=a.profile)
    md = markdown(rows)
    if a.update_report:
        report = ROOT / "docs" / "RELATORIO_EXPANSAO.md"
        text = report.read_text(encoding="utf-8")
        begin, end = "<!-- matriz:inicio -->", "<!-- matriz:fim -->"
        start, stop = text.index(begin) + len(begin), text.index(end)
        report.write_text(text[:start] + "\n" + md + "\n" + text[stop:], encoding="utf-8")
    print(md)
    if a.markdown:
        Path(a.markdown).write_text(md + "\n", encoding="utf-8")
    if a.json:
        Path(a.json).write_text(json.dumps(rows, indent=1, ensure_ascii=False), encoding="utf-8")
    if a.check:
        bad = [r for r in rows if r["implemented"] and (r["structure"] != "ok" or r["gameplay"] != "ok")]
        for r in bad:
            print("FALHA:", r["id"], r["notes"], file=sys.stderr)
        return 1 if bad else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
