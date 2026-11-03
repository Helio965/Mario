"""Verify lume/data/plan/campaign_plan.json against campaign.json and enemies.json.
Exit code 1 on any error. Run from anywhere: python3 check.py"""

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
plan = json.load(open(REPO / "lume/data/plan/campaign_plan.json", encoding="utf-8"))
camp = json.load(open(REPO / "lume/data/campaign.json", encoding="utf-8"))
reg = json.load(open(REPO / "lume/data/enemies.json", encoding="utf-8"))
species = {s["id"]: s for s in reg["species"]}

KEYS = ["id", "world", "slot", "name", "origin", "objective", "visual_theme", "main_mechanic",
        "secondary_mechanics", "difficulty", "planned_duration_s", "size", "main_path", "alternate_paths",
        "allowed_enemies", "planned_enemy_count", "obstacles", "items", "secrets", "collectibles",
        "checkpoints", "special_events", "animated_elements", "soundtrack", "completion", "test_criteria",
        "engine_requirements"]
BOSS_KEYS = ["id", "world", "name", "level", "arena", "attacks", "vulnerability", "phases", "defeat", "world_mechanic", "status"]
SUB = {"underground", "fortress", "underwater"}
RANGES = {1: (1, 3), 2: (1, 3), 3: (3, 5), 4: (3, 5), 5: (5, 6), 6: (5, 6), 7: (6, 8), 8: (6, 8), 9: (8, 10), 10: (8, 10)}
AREA_RE = re.compile(r"^(\w+) \[(\w+)\] (\d+),(\d+) (\d+)×(\d+): .+")

errors, warnings = [], []
err, warn = errors.append, warnings.append

# ---------------------------------------------------------------- structure / order
if plan.get("format") != "lume.plan" or plan.get("format_version") != 1:
    err("format/format_version")
expected = []
for wi, w in enumerate(camp["worlds"], 1):
    for si, l in enumerate(w["levels"], 1):
        expected.append((l["id"], w["id"], si, l["name"], wi, w["biome"]))
levels = plan["levels"]
if len(levels) != 60:
    err(f"esperadas 60 fases, há {len(levels)}")
if [e["id"] for e in levels] != [x[0] for x in expected]:
    err("ids/ordem das fases diferem de campaign.json")
order = {x[0]: i for i, x in enumerate(expected)}
meta = {x[0]: x for x in expected}

boss_ids = {b["id"] for b in plan["bosses"]}
for e, (lid, wid, slot, name, wno, biome) in zip(levels, expected):
    if list(e.keys()) != KEYS:
        err(f"{e.get('id')}: chaves diferentes do formato ({set(e) ^ set(KEYS)})")
    if (e["id"], e["world"], e["slot"], e["name"]) != (lid, wid, slot, name):
        err(f"{lid}: world/slot/name não batem com campaign.json")
    lo, hi = RANGES[wno]
    if not (isinstance(e["difficulty"], int) and lo <= e["difficulty"] <= hi):
        err(f"{lid}: dificuldade {e['difficulty']} fora da faixa {lo}–{hi} do mundo {wno}")
    d = e["planned_duration_s"]
    if not (isinstance(d, list) and len(d) == 2 and 0 < d[0] < d[1]):
        err(f"{lid}: planned_duration_s inválido")
    if not (e["origin"] == "nova" or re.fullmatch(r"legada \d+-\d", e["origin"])):
        err(f"{lid}: origin inválido '{e['origin']}'")
    if e["collectibles"].get("relics") != 3:
        err(f"{lid}: relics != 3")
    relic_secrets = [s for s in e["secrets"] if "relíquia" in s["reward"]]
    if len(relic_secrets) != 3:
        err(f"{lid}: {len(relic_secrets)} segredos com relíquia (esperado 3)")
    for s in e["secrets"]:
        if set(s) != {"id", "kind", "clue", "reward"} or s["kind"] not in {"warp_room", "hidden_block", "high_route", "breakable_path", "hidden_area", "optional_challenge"}:
            err(f"{lid}: segredo malformado {s}")
    if len({s['id'] for s in e['secrets']}) != len(e["secrets"]):
        err(f"{lid}: ids de segredo repetidos")
    if not e["alternate_paths"]:
        err(f"{lid}: sem rota opcional")
    if not isinstance(e["checkpoints"], int) or e["checkpoints"] < 1:
        err(f"{lid}: checkpoints inválido")
    pc = e["planned_enemy_count"]
    if set(pc) != {"min", "max"} or pc["min"] > pc["max"]:
        err(f"{lid}: planned_enemy_count inválido")
    st = e["soundtrack"]
    if not st.get("track", "").startswith(wid + "_") and not (lid == "mirror_sanctum"):
        err(f"{lid}: trilha '{st.get('track')}' não começa com o id do mundo")
    # areas
    W, H = e["size"]["width"], e["size"]["height"]
    rects = []
    for a in e["size"]["areas"]:
        m = AREA_RE.match(a)
        if not m:
            err(f"{lid}: área fora do formato '{a}'")
            continue
        aid, tag, x, y, w, h = m.group(1), m.group(2), *map(int, m.groups()[2:])
        if tag != biome and tag not in SUB:
            err(f"{lid}: área '{aid}' com bioma '{tag}' inválido")
        if w < 960 or h < 540:
            err(f"{lid}: área '{aid}' menor que 960×540")
        if x < 0 or y < 0 or x + w > W or y + h > H:
            err(f"{lid}: área '{aid}' fora de {W}×{H}")
        for (bid, bx, by, bw, bh) in rects:
            if x < bx + bw and bx < x + w and y < by + bh and by < y + h:
                err(f"{lid}: áreas '{aid}' e '{bid}' se sobrepõem")
        rects.append((aid, x, y, w, h))
    if rects and rects[0][0] != "main":
        warn(f"{lid}: primeira área não se chama 'main'")
    # checkpoint spacing (path length ~ width + vertical extra)
    path = W + max(0, H - 1240) * (1 if H > 1240 else 0)
    if path / (e["checkpoints"] + 1) > 2700:
        warn(f"{lid}: ~{path / (e['checkpoints'] + 1):.0f} u por trecho entre checkpoints")

# ---------------------------------------------------------------- bosses
if len(plan["bosses"]) != 10:
    err(f"esperados 10 chefes, há {len(plan['bosses'])}")
for b, w in zip(plan["bosses"], camp["worlds"]):
    if list(b.keys()) != BOSS_KEYS:
        err(f"chefe {b.get('id')}: chaves diferentes")
    if b["world"] != w["id"] or b["level"] != w["levels"][5]["id"]:
        err(f"chefe {b['id']}: mundo/fase incorretos")
    if len(b["attacks"]) < 3:
        err(f"chefe {b['id']}: menos de 3 ataques")
    registered = set(re.findall(r'@register\("([a-z_]+)"\)', "".join(p.read_text(encoding="utf-8") for p in (REPO / "lume/core/behaviors").glob("*.py"))))
    in_reg = b["id"] in species and species[b["id"]]["boss"]
    impl = in_reg and species[b["id"]]["behavior"] in registered
    if b["status"] != ("implementado" if impl else "planejado"):
        err(f"chefe {b['id']}: status '{b['status']}' (registro: {'existe' if impl else 'não existe'})")
    if in_reg and species[b["id"]]["introduced_in"] != b["level"]:
        err(f"chefe {b['id']}: introduced_in difere da fase do chefe")
    fortress = next(e for e in levels if e["id"] == b["level"])
    ref = b["id"] if in_reg else f"boss:{b['id']}"
    if ref not in fortress["allowed_enemies"]:
        err(f"{b['level']}: chefe {ref} ausente de allowed_enemies")

# ---------------------------------------------------------------- species rules
first_seen = {}
new_per_level = {}
for e in levels:
    lid = e["id"]
    wno, biome = meta[lid][4], meta[lid][5]
    tags = set(re.findall(r"\[(\w+)\]", " ".join(e["size"]["areas"])))
    if len(set(e["allowed_enemies"])) != len(e["allowed_enemies"]):
        err(f"{lid}: espécie repetida em allowed_enemies")
    for sid in e["allowed_enemies"]:
        if sid.startswith("boss:"):
            if sid[5:] not in boss_ids:
                err(f"{lid}: '{sid}' não corresponde a um chefe da lista bosses")
            continue
        sp = species.get(sid)
        if sp is None:
            err(f"{lid}: espécie '{sid}' não existe no registro")
            continue
        first_seen.setdefault(sid, lid)
        hab = set(sp["habitats"])
        if biome not in hab:
            extra = hab & SUB
            if not (extra & tags):
                err(f"{lid}: '{sid}' fora do habitat ({', '.join(sp['habitats'])}) e sem sub-área compatível (tags {sorted(tags)})")
for sid, sp in species.items():
    intro = sp["introduced_in"]
    if intro not in order:
        warn(f"{sid}: introduced_in '{intro}' não está na campanha")
        continue
    seen = first_seen.get(sid)
    if seen is None:
        err(f"{sid}: nunca aparece no plano (deveria estrear em '{intro}')")
    elif seen != intro:
        err(f"{sid}: primeira aparição em '{seen}', mas introduced_in = '{intro}'")
    new_per_level.setdefault(intro, []).append(sid)
exceptions = {lid: sids for lid, sids in new_per_level.items() if len(sids) > 2}

# ---------------------------------------------------------------- report
print(f"fases: {len(levels)} | chefes: {len(plan['bosses'])} | espécies verificadas: {len(species)}")
print("exceções à regra de ≤ 2 estreias (vêm do registro; ver 'Ajustes propostos'):")
for lid, sids in exceptions.items():
    print(f"  {lid}: {', '.join(sids)}")
for w in warnings:
    print("AVISO:", w)
for e in errors:
    print("ERRO:", e)
print("RESULTADO:", "OK" if not errors else f"{len(errors)} erro(s)")
sys.exit(1 if errors else 0)
