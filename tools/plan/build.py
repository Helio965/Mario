"""Build lume/data/plan/campaign_plan.json and docs/level_design/*.md from the
world modules (single source of truth). Run: python3 build.py"""

from __future__ import annotations

import importlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from common import GAP_LIMIT, generic_tests  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
CAMPAIGN = json.loads((REPO / "lume/data/campaign.json").read_text(encoding="utf-8"))
REGISTRY = json.loads((REPO / "lume/data/enemies.json").read_text(encoding="utf-8"))
SPECIES = {s["id"]: s for s in REGISTRY["species"]}

KEYS = [
    "id", "world", "slot", "name", "origin", "objective", "visual_theme", "main_mechanic",
    "secondary_mechanics", "difficulty", "planned_duration_s", "size", "main_path", "alternate_paths",
    "allowed_enemies", "planned_enemy_count", "obstacles", "items", "secrets", "collectibles",
    "checkpoints", "special_events", "animated_elements", "soundtrack", "completion", "test_criteria",
    "engine_requirements",
]
BOSS_KEYS = ["id", "world", "name", "level", "arena", "attacks", "vulnerability", "phases", "defeat", "world_mechanic", "status"]
NONBLOCK_MARKERS = ("opcional", "só para o segredo", "só na sala opcional", "desejado", "mesmo sem ele")
WORLD_RANGES = {1: (1, 3), 2: (1, 3), 3: (3, 5), 4: (3, 5), 5: (5, 6), 6: (5, 6), 7: (6, 8), 8: (6, 8), 9: (8, 10), 10: (8, 10)}

MODULES = [importlib.import_module(f"w{n:02d}") for n in range(1, 11)]
REGISTERED = set(re.findall(r'@register\("([a-z_]+)"\)', "".join(p.read_text(encoding="utf-8") for p in (REPO / "lume/core/behaviors").glob("*.py"))))


def boss_implemented(bid: str) -> bool:
    sp = SPECIES.get(bid)
    return bool(sp and sp.get("boss") and sp.get("behavior") in REGISTERED)


def debut_map() -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for s in REGISTRY["species"]:
        out.setdefault(s["introduced_in"], []).append(s["id"])
    return out


DEBUTS = debut_map()


def species_name(sid: str, bosses: dict) -> str:
    if sid.startswith("boss:"):
        b = bosses.get(sid[5:])
        return f"{b['name']} (chefe planejado)" if b else sid
    s = SPECIES.get(sid)
    return s["name"] if s else sid


def main_path_text(L: dict) -> str:
    parts = [f"{b['n']}. {b['label']} ({b['range']}): {b['text']}" for b in L["beats"]]
    text = " ".join(parts)
    if L.get("improvements"):
        label = "Plano de melhoria da fase legada" if L["origin"].startswith("legada") else "Ajustes sobre a implementação inicial"
        text += f" {label}: " + " ".join(f"({chr(97 + i)}) {t}" for i, t in enumerate(L["improvements"]))
    return text


def level_tests(L: dict, world_no: int) -> list[str]:
    tests = generic_tests(world_no, L["checkpoints"])
    debuts = [s for s in DEBUTS.get(L["id"], []) if not SPECIES[s]["boss"]]
    if debuts:
        names = ", ".join(SPECIES[s]["name"] for s in debuts)
        tests.append(f"estreias ({names}) em chão plano com ≥ 300 u de aproximação visível, recuo livre e nenhum vão letal a 200 u")
    tests.append("teto sobre patrulha: nenhum sólido não semissólido com base entre y_chão−158 e y_chão−30 sobre a patrulha de inimigo terrestre a menos de 160 u de um vão obrigatório")
    tests.append("zona segura de cada checkpoint: chão plano de x−96 a x+192 e nenhum inimigo comum alcança [x−160, x+320] em 3 s de simulação")
    tests.extend(L["tests"])
    return tests


def build_entry(L: dict, world: dict, slot: int) -> dict:
    world_no = CAMPAIGN["worlds"].index(world) + 1
    e = {
        "id": L["id"],
        "world": world["id"],
        "slot": slot,
        "name": L["name"],
        "origin": L["origin"],
        "objective": L["objective"],
        "visual_theme": L["visual_theme"],
        "main_mechanic": L["main_mechanic"],
        "secondary_mechanics": L["secondary_mechanics"],
        "difficulty": L["difficulty"],
        "planned_duration_s": L["planned_duration_s"],
        "size": L["size"],
        "main_path": main_path_text(L),
        "alternate_paths": L["alternate_paths"],
        "allowed_enemies": [sid[5:] if sid.startswith("boss:") and sid[5:] in SPECIES else sid for sid in L["allowed_enemies"]],
        "planned_enemy_count": L["planned_enemy_count"],
        "obstacles": L["obstacles"],
        "items": L["items"],
        "secrets": L["secrets"],
        "collectibles": L["collectibles"],
        "checkpoints": L["checkpoints"],
        "special_events": L["special_events"],
        "animated_elements": L["animated_elements"],
        "soundtrack": L["soundtrack"],
        "completion": L["completion"],
        "test_criteria": level_tests(L, world_no),
        "engine_requirements": [r for r in L["engine_requirements"]
                                if not any(r.startswith("comportamento do chefe planejado") and f"({bid})" in r and boss_implemented(bid)
                                           for bid in SPECIES)],
    }
    assert list(e) == KEYS
    return e


def is_blocking(req: str) -> bool:
    return not any(m in req for m in NONBLOCK_MARKERS)


def req_key(req: str) -> str:
    return req.split(":")[0].split(" (")[0].strip()


# ---------------------------------------------------------------------------- assemble
levels, bosses, worlds_data = [], [], []
for module, world in zip(MODULES, CAMPAIGN["worlds"]):
    assert module.WORLD["id"] == world["id"], (module.WORLD["id"], world["id"])
    assert [L["id"] for L in module.LEVELS] == [l["id"] for l in world["levels"]], world["id"]
    for slot, (L, cl) in enumerate(zip(module.LEVELS, world["levels"]), 1):
        assert L["slot"] == slot and L["name"] == cl["name"], (L["id"], L["name"], cl["name"])
        levels.append(build_entry(L, world, slot))
    b = dict(module.BOSS)
    assert list(b) == BOSS_KEYS, b["id"]
    b["status"] = "implementado" if boss_implemented(b["id"]) else "planejado"
    bosses.append(b)
    worlds_data.append((world, module))

plan = {"format": "lume.plan", "format_version": 1, "levels": levels, "bosses": bosses}
out_json = REPO / "lume/data/plan/campaign_plan.json"
out_json.parent.mkdir(parents=True, exist_ok=True)
out_json.write_text(json.dumps(plan, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

BOSS_BY_ID = {b["id"]: b for b in bosses}
LEVEL_BY_ID = {e["id"]: e for e in levels}
SRC_BY_ID = {L["id"]: L for _, m in worlds_data for L in m.LEVELS}
SNAPSHOT = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
NEW_EXISTING = [e["id"] for e in levels if e["origin"] == "nova" and (REPO / "lume/data/levels" / e["world"] / f"{e['id']}.json").exists()]


# ---------------------------------------------------------------------------- markdown helpers
def md_list(items, indent="") -> str:
    return "\n".join(f"{indent}- {i}" for i in items) if items else f"{indent}- —"


def code_ids(ids) -> str:
    return ", ".join(f"`{i}`" for i in ids) if ids else "—"


def world_no(world_id: str) -> int:
    return [w["id"] for w in CAMPAIGN["worlds"]].index(world_id) + 1


def level_label(e: dict) -> str:
    return f"{world_no(e['world'])}-{e['slot']}"


def new_species(level_id: str) -> list[str]:
    return DEBUTS.get(level_id, [])


def boss_of_level(e: dict) -> str:
    for sid in e["allowed_enemies"]:
        if sid.startswith("boss:"):
            return BOSS_BY_ID[sid[5:]]["name"] + " (planejado)"
        s = SPECIES.get(sid)
        if s and s["boss"] and s["introduced_in"] == e["id"]:
            kind = "chefe" if e["slot"] == 6 else "minichefe"
            state = "implementado" if s["behavior"] in REGISTERED else "registro criado, comportamento pendente"
            return f"{s['name']} ({kind}, {state})"
    if e["id"] == "gravity_halls":
        return "Guardião da Constelação (elite em papel de minichefe)"
    return "—"


def blocking_reqs(e: dict) -> list[str]:
    return [r for r in e["engine_requirements"] if is_blocking(r)]


def level_section(e: dict) -> str:
    L = SRC_BY_ID[e["id"]]
    w = next(w for w in CAMPAIGN["worlds"] if w["id"] == e["world"])
    out = [f"### {level_label(e)} · {e['name']} (`{e['id']}`)", ""]
    out.append(f"*Ideia própria:* {L['twist']}.")
    out.append("")
    out.append(f"- **Identificador:** `{e['id']}`")
    out.append(f"- **Nome:** {e['name']}")
    out.append(f"- **Mundo:** {w['name']} (`{w['id']}`, bioma `{w['biome']}`), fase {e['slot']} de 6 — origem: {e['origin']}")
    out.append(f"- **Objetivo:** {e['objective']}")
    out.append(f"- **Tema visual:** {e['visual_theme']}")
    out.append(f"- **Mecânica principal:** {e['main_mechanic']}")
    out.append("- **Mecânicas secundárias:**")
    out.append(md_list(e["secondary_mechanics"], "  "))
    out.append(f"- **Dificuldade:** {e['difficulty']}/10")
    d = e["planned_duration_s"]
    out.append(f"- **Duração planejada:** {d[0]}–{d[1]} s (primeira travessia → exploração completa)")
    s = e["size"]
    out.append(f"- **Tamanho do cenário:** {s['width']} × {s['height']} u")
    out.append(md_list([f"`{a.split(' ')[0]}` {a[len(a.split(' ')[0]) + 1:]}" for a in s["areas"]], "  "))
    out.append("- **Caminho principal** (sequência de ensino):")
    for b in L["beats"]:
        out.append(f"  {b['n']}. **{b['label']}** ({b['range']}) — {b['text']}")
    out.append("- **Caminhos alternativos:**")
    out.append(md_list(e["alternate_paths"], "  "))
    debut = new_species(e["id"])
    allowed = [f"`{sid}` ({species_name(sid, BOSS_BY_ID)}{' — estreia' if sid in debut else ''})" for sid in e["allowed_enemies"]]
    out.append("- **Inimigos permitidos:** " + ", ".join(allowed))
    c = e["planned_enemy_count"]
    out.append(f"- **Quantidade planejada de inimigos:** {c['min']}–{c['max']} (chefes não contados)")
    out.append("- **Obstáculos:**")
    out.append(md_list(e["obstacles"], "  "))
    out.append("- **Itens disponíveis:**")
    out.append(md_list(e["items"], "  "))
    out.append("- **Segredos:**")
    for sc in e["secrets"]:
        out.append(f"  - `{sc['id']}` ({sc['kind']}) — pista: {sc['clue']}; recompensa: {sc['reward']}")
    col = e["collectibles"]
    out.append(f"- **Colecionáveis:** ~{col['coins']} moedas e {col['relics']} relíquias")
    out.append(f"- **Checkpoints:** {e['checkpoints']}")
    out.append("- **Eventos especiais:**")
    out.append(md_list(e["special_events"], "  "))
    out.append("- **Elementos animados:**")
    out.append(md_list(e["animated_elements"], "  "))
    st = e["soundtrack"]
    sub = f" (sub-áreas: {code_ids(st['sub_tracks'])})" if st.get("sub_tracks") else ""
    out.append(f"- **Trilha sonora:** `{st['track']}` — {st['mood']}{sub}")
    out.append(f"- **Condição de conclusão:** {e['completion']}")
    out.append("- **Critérios de teste:**")
    out.append(md_list(e["test_criteria"], "  "))
    out.append("- **Requisitos de motor:** " + ("nenhum (implementável com o motor atual)" if not e["engine_requirements"] else ""))
    if e["engine_requirements"]:
        out.append(md_list([("**bloqueia** — " if is_blocking(r) else "não bloqueia — ") + r for r in e["engine_requirements"]], "  "))
    if L.get("improvements"):
        title = "Plano de melhoria da fase legada" if e["origin"].startswith("legada") else "Ajustes sobre a implementação inicial já existente"
        out.append(f"- **{title}:**")
        out.append(md_list(L["improvements"], "  "))
    out.append("")
    return "\n".join(out)


# ---------------------------------------------------------------------------- registry adjustments text
ADJUSTMENTS_TEMPLATE = """## 6. Ajustes propostos ao registro de inimigos

O plano **segue o registro atual** (`lume/data/enemies.json`): toda espécie estreia exatamente na fase do seu `introduced_in` e só aparece em mundos do seu habitat (ou em sub-áreas `underground`/`fortress`/`underwater` quando listadas). Nada foi editado no registro. Os ajustes abaixo resolvem conflitos entre o registro e as regras do plano; nenhum é necessário para implementar as fases como estão.

### 6.1 Conflito com a regra de no máximo 2 espécies novas por fase

Quatro fases recebem 3 ou 4 estreias pelo registro atual. O plano as mantém (para cumprir `introduced_in`), separa cada estreia num trecho próprio e propõe:

| Fase | Estreias hoje | Ajuste proposto | Resultado | Justificativa |
| --- | --- | --- | --- | --- |
| `windswept_dunes` (2-1) | escaravelho_areia, tatu_bola, cacto_sentinela | `tatu_bola.introduced_in`: `windswept_dunes` → `canyon_bridges` | 2-1: escaravelho + cacto; 2-2: abutrinho + tatu | O casco já foi ensinado com o caramujo (Mundo 1); `canyon_bridges` já tem um tatu (x1120). O tatu de x840 em 2-1 vira um segundo escaravelho. |
| `crystal_lake` (4-1) | pinguim_patrulha, caracol_cristal, coruja_nevada | `coruja_nevada.introduced_in`: `crystal_lake` → `blue_ascent` | 4-1: pinguim + caracol; 4-2: boneco + coruja | O voador em onda já é conhecido; `blue_ascent` tem só 2 inimigos e ganha a coruja planejada. A coruja de x1580 em 4-1 vira um segundo caracol. |
| `glowing_canopy` (5-1) | cogumelo_saltitante, caracol_musgo, mariposa_lume, planta_esporos | `planta_esporos.introduced_in` → `firefly_ruins`; `cogumelo_saltitante.introduced_in` → `ancestral_tree` | 5-1: caracol-musgo + mariposa; 5-2: besouro-casca + planta; 5-3: guardião + cogumelo | `firefly_ruins` já tem uma planta (x2990). Só a planta de x1320 em 5-1 precisa ser trocada; com o ajuste, retirar o cogumelo de 5-1 e 5-2 no plano. |
| `basalt_bridges` (9-1) | brasa_andante, tartaruga_basalto, boca_fornalha, golem_basalto | `boca_fornalha.introduced_in` → `echo_furnace`; `tartaruga_basalto.introduced_in` → `last_flame` | 9-1: brasa + golem; 9-2: boca + morcego; 9-3: Ermitão-de-Basalto + guardião | `echo_furnace` já tem boca (x1000) e `last_flame` já tem o ermitão (x650); só a boca (x2720) e o ermitão (x3900) de 9-1 mudam. São variantes de famílias conhecidas, então a exceção pesa menos no Mundo 9. |

{BOSS_REGISTRY_TABLE}
### 6.3 Observações (sem mudança obrigatória)

- `polvo_tinteiro` tem só o habitat `underwater`: no Mundo 3 o plano o restringe às sub-áreas submersas (`coral_maze`, `sunken_galleon`) e, depois, aos reflexos do Mundo 10. Opcional: acrescentar `coast` permitiria usá-lo em mar aberto de `current_depths` sem sub-área.
- `semente_espinho` lista `grassland`, mas estreia em `floating_gardens` (Mundo 7), depois do único mundo de campina; o habitat é inócuo. Se o objetivo for reaproveitá-la, `citadel` ou `fortress` seriam úteis no Mundo 10.
- `guardiao_constelacao` tem `boss: false`: no plano ele cumpre o papel de minichefe de `gravity_halls`, mas não bloqueia a bandeira. Se a luta tiver de ser obrigatória, é preciso um portão (switch + `boss_arena`) ou marcá-lo como chefe.
- O registro redesenhou três espécies durante a redação (ids mantidos): `tartaruga_basalto` virou **Ermitão-de-Basalto** (caranguejo-ermitão num bloco de basalto chutável), `assombracao_timida` virou **Sombra-Errante** (paralisa no halo da lanterna de Lume em vez de reagir ao olhar) e `bolha_magma` virou **Salta-Brasa**. O plano já usa os nomes e regras novos. Como o chefe planejado do Mundo 3 também é um caranguejo-ermitão (Ermitão-Âncora), manter silhuetas bem distintas (popa de galeão × bloco de basalto) ou renomear o chefe se a semelhança incomodar.
- A família `emerger` tem timidez padrão (`shy_radius` 42): `mao_lodo` e `moreia_toca` também não emergem com Lume encostado, como `flor_mordedora`. O plano usa isso como ferramenta (corredor de moreias de `tide_pools`); vale registrar na descrição.
"""


BOSS_PLAN = {
    "ermitao_ancora": ("anchor_hermit", "coast, underwater", 5),
    "morsa_gelomar": ("ice_walrus", "snow, fortress", 5),
    "imperatriz_mariposa": ("moth_empress", "forest, fortress", 6),
    "colosso_fundidor": ("foundry_colossus", "city, fortress", 5),
    "grifa_ventania": ("gale_griffin", "sky, fortress", 6),
    "vulto_apagador": ("lantern_shade", "swamp, fortress", 6),
    "salamandra_caldera": ("caldera_salamander", "volcano, fortress", 7),
    "eclipse_devorador": ("eclipse", "citadel", 9),
}


def boss_registry_table() -> str:
    done = [b for b in bosses if b["id"] in SPECIES and b["id"] != "javali_espinheiro"]
    pending = [b for b in bosses if b["id"] not in SPECIES]
    out = ["### 6.2 Registro dos chefes de mundo", ""]
    if done:
        out.append("Já entraram no registro durante a redação (o plano os adota): " + "; ".join(
            f"`{b['id']}` (família `{SPECIES[b['id']]['behavior']}`, {SPECIES[b['id']]['hp']} PV, "
            f"{'implementada' if SPECIES[b['id']]['behavior'] in REGISTERED else 'comportamento pendente'})" for b in done) + ".")
        out.append("")
    out.append(f"Os {len(pending)} chefes ainda planejados precisam de entradas `boss: true` (o motor bloqueia a saída enquanto houver chefe vivo):")
    out.append("")
    out.append("| id proposto | Nome | `behavior` novo | `habitats` | `introduced_in` | PV |")
    out.append("| --- | --- | --- | --- | --- | ---: |")
    for b in pending:
        beh, hab, hp = BOSS_PLAN[b["id"]]
        out.append(f"| `{b['id']}` | {b['name']} | `{beh}` | {hab} | `{b['level']}` | {hp} |")
    out.append("")
    return "\n".join(out)


def engine_section() -> str:
    reqs: dict[str, dict[str, list[str]]] = {}
    for e in levels:
        for r in e["engine_requirements"]:
            k = req_key(r)
            d = reqs.setdefault(k, {"bloqueia": [], "não bloqueia": []})
            d["bloqueia" if is_blocking(r) else "não bloqueia"].append(e["id"])
    names = {
        "toggle_switch": "Extensão de interruptores: evento `toggle_switch` por gatilho, interruptor temporizado, ligação de grupos a esteiras/plataformas",
        "rising_lava": "Extensão de `rising_lava`: ciclos de subida e descida, gatilho por altura/tempo/chefe, etapas com aviso, reposição no checkpoint, variante com zona swim",
        "lights": "Extensão de luz: lanternas fixas e acendíveis (raio e duração) e evento `lights` global",
        "breakable walls": "Paredes quebráveis (segredos `breakable_path` além dos tijolos)",
    }
    out = ["## 7. Requisitos de motor e fases bloqueadas", ""]
    out.append("O briefing listava como \"só dados\" a alternância de interruptores, `rising_lava`, a máscara de escuridão, a física de areia movediça, `camera_lock`/`boss_arena` e as paredes quebráveis. **Durante a redação outros agentes implementaram parte disso** (estado conferido em `lume/core/game.py`, `lume/levels/schema.py` e `lume/render/scene.py`):")
    out.append("")
    out.append("| Recurso | Estado no snapshot | O que o plano ainda pede |")
    out.append("| --- | --- | --- |")
    out.append("| `boss_arena` / `camera_lock` | implementado (`Game._events`: trava de câmera, portões `close`/`open`, reabertura com a vitória) | nada; as fases de chefe só declaram o evento |")
    out.append("| Areia movediça (`quicksand`) | implementado (`Game._quicksand`: anda a 45%, pulo a 62%, afunda e mata ao cobrir Lume) | nada; os testes das fases pedem saída em ≤ 2 pulos |")
    out.append("| Interruptores | parcial: bloco `?` com recompensa `toggle` alterna os blocos `switch` do grupo (`Game.toggle_group`); o evento `toggle_switch` ainda não é tratado | interruptor temporizado, gatilho por evento, ligação a esteiras e a plataformas condicionais |")
    out.append("| `rising_lava` | parcial: subida única de um perigo até `to` com `speed`, disparada por x (`Game._update_rising`) | ciclos, gatilho por altura/tempo/chefe, aviso sonoro, etapas, reposição no checkpoint, variante água (zona swim) |")
    out.append("| Escuridão (`dark` + `lights`) | parcial: máscara desenhada com o halo de Lume (120 u; 64 u correndo) em `Scene._darkness`; o evento `lights` ainda não é tratado | lanternas fixas/acendíveis com raio e duração, apagão global, raio progressivo |")
    out.append("| Paredes quebráveis | não implementado | só segredos (os tijolos existentes servem de alternativa) |")
    impl = [b for b in bosses if b["status"] == "implementado"]
    out.append(f"| Chefes de mundo | {len(impl)} de 10 implementados ({', '.join('`' + SPECIES[b['id']]['behavior'] + '`' for b in impl)}) | {10 - len(impl)} famílias novas |")
    out.append("")
    out.append("Uma fase é **bloqueada** quando a experiência principal depende de um item ainda pendente; **não bloqueada** quando o item só afeta um segredo, uma sala opcional ou degrada com elegância (ex.: sem lanternas a fase fica jogável com o halo de Lume).")
    out.append("")
    out.append("| Requisito pendente | Fases bloqueadas | Fases que só se beneficiam |")
    out.append("| --- | --- | --- |")
    boss_levels = []
    for k, d in reqs.items():
        if k.startswith("comportamento do chefe"):
            boss_levels.extend(d["bloqueia"])
            continue
        out.append(f"| {names.get(k, k)} | {code_ids(d['bloqueia'])} | {code_ids(d['não bloqueia'])} |")
    out.append(f"| Comportamentos dos {len(boss_levels)} chefes planejados (`lume/core/behaviors/bosses.py`) | {code_ids(boss_levels)} | — |")
    out.append("")
    blocked = [e["id"] for e in levels if blocking_reqs(e)]
    free = [e["id"] for e in levels if not blocking_reqs(e)]
    out.append(f"**Fases bloqueadas ({len(blocked)}):** {code_ids(blocked)}. Em `switch_factory` o bloqueio é parcial (só os trechos com interruptor temporizado).")
    out.append("")
    out.append(f"**Fases implementáveis com o motor atual ({len(free)}):** {code_ids(free)}.")
    out.append("")
    cam = [e["id"] for e in levels if any("camera_lock" in s and "opcional" in s for s in e["special_events"])]
    out.append(f"Usos opcionais de `camera_lock` para enquadramento (já suportado): {code_ids(cam)}.")
    out.append("")
    out.append("Renderização de zonas (partículas de vento, correntes, volumes de água, birutas sincronizadas com `Game.zone_active`) é tarefa de arte/render e não aparece como requisito de motor; está descrita em *Elementos animados* de cada fase.")
    out.append("")
    return "\n".join(out)


LEGACY_FIX = """## 8. Correções das fases legadas e das implementações iniciais

Varredura feita sobre os arquivos atuais (`lume/data/levels/**`): para cada inimigo terrestre, procurou-se sólido não semissólido com base entre `y_chão−158` e `y_chão−30` sobre a patrulha (a cabeça bate ao saltar por cima) e mediu-se a distância até o próximo vão. Também se conferiu a zona segura dos checkpoints. Correções planejadas (detalhes na seção de cada fase):

| Fase | Problema encontrado | Correção planejada |
| --- | --- | --- |
| `canyon_bridges` | **Problema conhecido:** pedra frágil `crumble02` (x1040, y288, base 306) sobre o tatu-bola `[1060, 1220]`, 70 u antes do vão x1290→1420: o salto sobre o tatu batia a cabeça e caía no vão. | **Já corrigido no arquivo durante a redação** (pedras frágeis movidas para x770 e x920, relíquia alta em x954). O plano mantém a correção, acrescenta o teste de regressão nas duas alturas e a regra geral *teto sobre patrulha*; alternativa equivalente: tornar a pedra semissólida. |
| `orchard_guardian` | Bolota `[1430, 1590]` sob a pedra frágil x1450–1550, 60 u antes do vão. | Bolota para `[2240, 2400]`; checkpoint x1990 → x1900. |
| `glowing_canopy` | Caracol-musgo `[760, 920]` sob folha frágil x750–852, 60 u antes do vão. | Caracol para `[3250, 3450]`; cogumelo saltitante novo em `[420, 560]`. |
| `firefly_ruins` | Besouro-casca (estreia) `[1200, 1380]` sob tijolo x1110–1214, 70 u antes do vão. | Besouro para `[1860, 2060]` (chão aberto). |
| `sand_temple` | Escorpião (estreia) `[1340, 1500]` sob tijolo x1270–1374, 50 u antes do vão. | Escorpião para `[470, 600]` (entre o bloco ? e o cano). |
| `blue_ascent` | Caracol-de-cristal `[1010, 1230]` sob beirais x910 e x1060, 40 u antes do vão. | Beirais `ledge01`/`ledge02` viram semissólidos de gelo. |
| `windswept_dunes` | Escaravelho `[1450, 1670]` sob ?02 e tijolo03 (base y318), 100 u antes do vão. | ?02 e tijolo03 sobem 32 u (y258); patrulha `[1600, 1700]`. |
| `valley_canals` | Caramujo `[1130, 1300]` sob ?02/tijolo01 (base y348), 80 u antes do vão. | Caramujo para `[260, 420]`. |
| `first_steps` | Bolota 1 `[650, 900]` sob tijolo x780–872 (base y404); bolota 2 alcança a zona do checkpoint x1510. | Bolota 1 em `[640, 775]`; checkpoint x1510 → x1600. |
| `ancestral_tree` | Planta `[3240, 3420]` sob a plataforma vertical x3380, 110 u antes do vão. | Planta para x3200. |
| `echo_furnace` | Golem `[3360, 3530]` sob a plataforma vertical x3600 (base até y366). | Golem para `[3260, 3420]`; espinhos x4490 → x4560 sob a estreia do morcego. |
| `crystal_lake` | Pinguim `[3070, 3300]` com visão 280 alcança o pouso no gelo (x2740) antes da frenagem. | Pinguim `[3200, 3400]`, visão 220. |
| `blizzard_heart` | Carneiro (estreia) `[575, 725]` sem parede: a investida não termina em batida. | Bloco de granito x540–580 e patrulha `[580, 740]`. |
| `windmill_heights` | 1 checkpoint em 5600 u; toca da flor x2900 dentro da zona do checkpoint x2700; canal de 220 u com uma pá. | 2º checkpoint x4600; checkpoint x2620 e flor x2960; pás do canal largo já em fases opostas; no canal de 220 u (pá de raio 50) exigir pouso ≤ 125 u em ≥ 40% do ciclo ou acrescentar o apoio de pedra x4400. |
| `meadow_burrows` | Três patrulhas cruzam a zona do checkpoint do túnel; ouriço na zona do checkpoint de superfície; `surface_after` cobre o perigo `hz_water02` (x4400–4560); 4 relíquias. | Checkpoint do túnel x2700 com patrulhas recuadas; ouriço `[3940, 4140]`; cortar o terreno ou remover o perigo; padronizar em 3 relíquias. |
| `sandstorm_pass` | Vão x3000→3200 de 200 u (acima de 150 u) só vencível com o vento contínuo +140; 1 checkpoint em 5600 u; serpente de estreia cruza a zona do checkpoint x2150. | Reduzir o vão para 150 u ou manter como exceção testada; 2º checkpoint x3300 (zona a favor encurtada para x3000–3220); serpente `[2500, 2990]`. |
| `sunken_oasis` | Dificuldade 4 (faixa do Mundo 2 é 1–3); 1 checkpoint em 6000 u; lançador de estreia alcança o checkpoint; a física de areia movediça (implementada durante a redação) mata ao cobrir Lume. | Dificuldade 3; 2º checkpoint x3380; lançador `[2560, 2780]`; conferir saída de cada poça com o pulo reduzido; poça longa com apoios no fim. |
| `scarab_pyramid` | Dificuldade 4; 1 checkpoint antes de um chefe; 14 moedas. | Dificuldade 3; 2º checkpoint x2620 na antessala (escaravelho recuado para `[2160, 2380]`); ~60 moedas. |
| `bramble_fortress` | Fosso x900–1040 sem chão (letal) apesar de o mundo ensinar espinheiro não letal; flores na zona do checkpoint; 1 checkpoint antes de um chefe de 3 PV. | Fundo de espinheiro em y540 com degraus; flores x2560/x2720; 2º checkpoint na antessala x3080. |

Para os três níveis vulcânicos legados (agora Mundo 9), o plano mantém o traçado e eleva a dificuldade com: canais alargados até 150 u (limite do Mundo 9 = 160 u), chamas duplas sobre saltos obrigatórios, densidade de 3–5 para 12–18 inimigos (inclusive ossadas, de habitat `volcano`), plataformas móveis obrigatórias, dicas mais curtas, um checkpoint extra onde o trecho passa de 2500 u e uma rota opcional nova com a terceira relíquia; `basalt_bridges` ganha uma seção final (ponte levadiça) e a bandeira passa a x5050.
"""


def intro() -> str:
    return f"""# Lume — As Dez Fronteiras · Planejamento individual das 60 fases

> Documento de planejamento que orienta a implementação. Fonte de verdade em dados: [`lume/data/plan/campaign_plan.json`](../../lume/data/plan/campaign_plan.json) (mesmos valores deste texto). Documentos por mundo: {", ".join(f"[`MUNDO_{n:02d}.md`](MUNDO_{n:02d}.md)" for n in range(1, 11))}.
> Estado dos dados consultados: {SNAPSHOT} — `campaign.json`, `enemies.json` ({len(REGISTRY['species'])} espécies), `levels/schema.py`, `levels/validate.py`, `core/game.py`, `core/behaviors/*`, as 15 fases legadas e as {len(NEW_EXISTING)} fases novas que outros agentes criaram durante a redação ({code_ids(NEW_EXISTING)}), além dos chefes {code_ids([b['id'] for b in bosses if b['status'] == 'implementado' and b['id'] != 'javali_espinheiro'])} adicionados ao registro.

## 1. Método

1. **Ids e ordem** vêm de `lume/data/campaign.json` e não foram alterados; nomes de exibição são os do registro.
2. **Inimigos** vêm de `lume/data/enemies.json`: cada espécie estreia exatamente na fase do seu `introduced_in` e só aparece em mundos do seu habitat; espécies de `underground`, `fortress` ou `underwater` só entram em outros mundos dentro de sub-áreas marcadas com esse bioma (a marca aparece entre colchetes na lista de áreas de cada fase, ex.: `maze [underwater]`). Os chefes planejados aparecem como `boss:<id>`.
3. **Geometria** usa a física real (`lume/core/constants.py`): gravidade 1550 u/s², impulso 590 u/s (altura ≈ 112 u segurando), corrida 340 u/s (alcance ≈ 259 u), coyote 0,1 s, buffer 0,12 s, pisão 390 u/s, jogador 22×30 / 22×46 u, câmera de ≈ 738×415 u com Lume a ~1/3 da largura.
4. **Ciclo de ensino em 8 etapas** (pesquisa `docs/research/ENGENHARIA_REVERSA_FASES_MARIO.md`, §3.2.1f): introdução → demonstração segura → primeiro desafio → escalada → combinação → reviravolta → teste final → recompensa. O *Caminho principal* de cada fase é escrito nessas 8 etapas, com faixas de x (ou de andar, nas fases verticais).
5. **Uma ideia própria por fase**: cada seção abre com a reviravolta que diferencia a fase das demais do mundo.
6. **Fases que já existem** (15 legadas + as fases novas criadas durante a redação, algumas a partir deste próprio plano) são preservadas: o plano descreve o traçado atual e lista melhorias concretas (posições, correções, terceira relíquia, arte). Onde o arquivo diverge de uma regra do plano (dificuldade fora da faixa, vão acima do limite, checkpoint escasso), a divergência é apontada no item *Ajustes sobre a implementação inicial*. A avaliação qualitativa das 15 fases legadas, feita por outro agente, está em [`AVALIACAO_FASES_LEGADAS.md`](AVALIACAO_FASES_LEGADAS.md); as melhorias deste plano são compatíveis com ela.
7. **Verificação automática** (rodada antes da entrega): JSON válido; 60 fases na ordem de `campaign.json`; chaves exatas; estreia = `introduced_in` para todas as espécies; habitat por mundo ou sub-área; sub-áreas dentro dos limites e sem sobreposição; 3 segredos com relíquia por fase; dificuldade dentro da faixa do mundo.

## 2. Curva de dificuldade

| Mundo | Faixa | Fases (1→6) | Papel |
| --- | --- | --- | --- |
""" + "\n".join(
        f"| {n}. {w['name']} | {WORLD_RANGES[n][0]}–{WORLD_RANGES[n][1]} | {' · '.join(str(LEVEL_BY_ID[l['id']]['difficulty']) for l in w['levels'])} | "
        + ["introdução", "introdução", "novas condições físicas", "novas condições físicas", "combinações e inimigos especializados",
           "combinações e inimigos especializados", "movimento e percepção avançados", "movimento e percepção avançados", "domínio e final", "domínio e final"][n - 1] + " |"
        for n, w in enumerate(CAMPAIGN["worlds"], 1)
    ) + """

Dentro de cada mundo a curva é em dente de serra (pesquisa, §2 item 3): a fase 4 (mecânica especial) costuma recuar um ponto em relação à 3, porque apresenta uma regra nova; as fases 5 e 6 voltam a subir.

## 3. Regras de projeto aplicadas a todas as fases

- **Vãos obrigatórios** (borda a borda, mesma altura): Mundo 1 ≤ 125 u (fases 1–2 vencíveis andando: alcance andando 168 u); Mundos 2–5 ≤ 150 u; Mundos 6–10 ≤ 160 u (teto do projeto). Com desnível, usar a tabela de alcance da pesquisa (§5.1). Rotas opcionais nunca acima de 200 u.
- **Subidas obrigatórias** ≤ 64 u num salto (até 96 u só em rota opcional sobre chão seguro); acima disso, mola, corrente ascendente, plataforma móvel ou baixa gravidade (nos bolsões de gravidade × 0,55 a subida equivalente é ≤ 116 u).
- **Checkpoints** a cada ~1500–2500 u de caminho (vertical conta como caminho); em fases de chefe, um na antessala. Zona segura: chão plano de x−96 a x+192 e nenhum inimigo comum alcançando [x−160, x+320] em 3 s; chefes ficam confinados à arena.
- **Primeiro encontro** de cada espécie: chão plano, ≥ 300 u de aproximação visível, recuo livre, nenhum vão letal a 200 u. No máximo 2 espécies novas por fase (exceções do registro na seção 6); variantes avançadas só depois da família-base.
- **Teto sobre patrulha** (regra nova, nascida do problema de `canyon_bridges`): nenhum sólido não semissólido com base entre `y_chão−158` e `y_chão−30` sobre a patrulha de um inimigo terrestre que esteja a menos de 160 u de um vão obrigatório. Tetos que precisam ficar ali viram semissólidos.
- **Pouso no gelo**: ≥ 330 u livres depois do pouso ou parede de contenção (frenagem de 321 u).
- **Três relíquias por fase**, cada uma num segredo próprio com pista visual: em geral uma visível e exigente, uma numa rota opcional e uma numa área secreta. Nenhum segredo causa morte; moedas nunca levam a morte e toda queda maior que 220 u tem trilha de moedas até chão de ≥ 160 u.
- **Pelo menos uma rota opcional** por fase, que reencontra o caminho principal; o caminho principal nunca depende dela.
- **Geometria do bioma**: campina com moinhos, tocas e cercas; deserto com dunas, cânions e templos; costa com correntes, píeres e áreas submersas; neve com rampas (degraus descendentes de 12 u com arte contínua), cavernas e pontes; floresta com troncos, galhos e raízes; cidade com engrenagens e esteiras; céu com nuvens e correntes; pântano com passarelas e lanternas; vulcão com basalto e lava; cidadela com cristal, constelações e espelhos.
- **Saídas secretas** (regra 26 da pesquisa) ficam fora do plano porque a campanha é linear; os desafios opcionais e as salas secretas ocupam esse papel.
- **NPC por mundo**: um personagem original com função de jogo (checkpoints, relíquias, nado, gelo, segredos, ritmo, vento, luz, magma, mapas), implementado como prop animado + evento `message`.

## 4. Critérios de teste comuns

Toda fase tem, além dos critérios próprios: `validate_level`/`validate_campaign` sem erros; `route_bot` concluindo a partir do spawn e de cada checkpoint com inimigos e perigos ativos; vãos e subidas simulados nas duas alturas sem coyote nem buffer; relíquias e moedas alcançáveis; estreias em chão plano; *teto sobre patrulha*; zona segura dos checkpoints. Esses itens aparecem parametrizados no campo *Critérios de teste* de cada fase.
"""


def summary_table() -> str:
    out = ["## 5. Tabela-resumo das 60 fases", "",
           "| Fase | Id | Nome | Origem | Dif. | Tamanho (u) | Ideia própria | Estreias | Chefe | Bloqueio |",
           "| --- | --- | --- | --- | ---: | --- | --- | --- | --- | --- |"]
    for e in levels:
        L = SRC_BY_ID[e["id"]]
        deb = [s for s in new_species(e["id"]) if not SPECIES[s]["boss"]]
        out.append(
            f"| {level_label(e)} | `{e['id']}` | {e['name']} | {e['origin']} | {e['difficulty']} | {e['size']['width']}×{e['size']['height']} | {L['twist']} | "
            f"{', '.join(SPECIES[s]['name'] for s in deb) or '—'} | {boss_of_level(e)} | {'sim' if blocking_reqs(e) else '—'} |"
        )
    out.append("")
    return "\n".join(out)


def bosses_table() -> str:
    out = ["## 10. Chefes de mundo", "", "| Mundo | Chefe | Fase | PV | Vulnerabilidade (resumo) | Estado |", "| --- | --- | --- | ---: | --- | --- |"]
    hp = {"javali_espinheiro": 3, "escaravelho_rei": 3, "ermitao_ancora": 5, "morsa_gelomar": 5, "imperatriz_mariposa": 6,
          "colosso_fundidor": 5, "grifa_ventania": 6, "vulto_apagador": 6, "salamandra_caldera": 7, "eclipse_devorador": 9}
    hp.update({bid: SPECIES[bid]["hp"] for bid in list(hp) if bid in SPECIES})
    for b in bosses:
        n = world_no(b["world"])
        out.append(f"| {n} | {b['name']} (`{b['id']}`) | `{b['level']}` | {hp[b['id']]} | {b['vulnerability'].split('.')[0]}. | {b['status']} |")
    out.append("")
    out.append("O desenho completo de cada chefe (arena, ataques, vulnerabilidade, fases, derrota e relação com a mecânica do mundo) está no documento do respectivo mundo e na lista `bosses` do JSON. Minichefes legados (fase 3): Guardião do Pomar, do Templo, da Nevasca, da Árvore e da Última Chama (família `guardian`, implementados); no Mundo 10 o Guardião da Constelação (elite) ocupa esse papel.")
    out.append("")
    return "\n".join(out)


def main_doc() -> str:
    parts = [intro(), summary_table(), ADJUSTMENTS_TEMPLATE.replace("{BOSS_REGISTRY_TABLE}", boss_registry_table()), engine_section(), LEGACY_FIX, "## 9. Fases", ""]
    for world, module in worlds_data:
        n = world_no(world["id"])
        parts.append(f"## Mundo {n} — {world['name']} (`{world['id']}`)")
        parts.append("")
        parts.append(f"{world['subtitle']}. {module.WORLD['twist']} Detalhes do mundo em [`MUNDO_{n:02d}.md`](MUNDO_{n:02d}.md).")
        parts.append("")
        for l in world["levels"]:
            parts.append(level_section(LEVEL_BY_ID[l["id"]]))
    parts.append(bosses_table())
    return "\n".join(parts)


def world_doc(world: dict, module) -> str:
    n = world_no(world["id"])
    W = module.WORLD
    B = module.BOSS
    ids = [l["id"] for l in world["levels"]]
    out = [f"# Mundo {n} — {world['name']} (`{world['id']}`)", ""]
    out.append(f"> {world['subtitle']}. Bioma `{world['biome']}`, cor de mapa `{world['color']}`" + (f", mundo legado {world['legacy_world']}" if world.get("legacy_world") else ", mundo novo") + ".")
    out.append(f"> Plano geral: [`PLANEJAMENTO_60_FASES.md`](PLANEJAMENTO_60_FASES.md) · dados: [`campaign_plan.json`](../../lume/data/plan/campaign_plan.json).")
    out.append("")
    out.append("## Identidade")
    out.append("")
    out.append(f"**Reviravolta do mundo.** {W['twist']}")
    out.append("")
    out.append("**Paleta**")
    out.append(md_list(W["palette"]))
    out.append("")
    out.append("**Marcos visuais**")
    out.append(md_list(W["landmarks"]))
    out.append("")
    out.append(f"**Ambiência.** {W['ambience']}")
    out.append("")
    out.append(f"**Física.** {W['physics']}")
    out.append("")
    out.append("## Progressão das mecânicas")
    out.append("")
    out.append("| Fase | Id | Papel | Foco | Dif. | Ideia própria |")
    out.append("| --- | --- | --- | --- | ---: | --- |")
    roles = ["apresentação", "exploração", "desafio de movimento", "mecânica especial", "desafio avançado", "fortaleza e chefe"]
    for (lid, focus), slot in zip(W["progression"], range(1, 7)):
        e = LEVEL_BY_ID[lid]
        out.append(f"| {n}-{slot} | `{lid}` | {roles[slot - 1]} | {focus} | {e['difficulty']} | {SRC_BY_ID[lid]['twist']} |")
    out.append("")
    # enemy distribution
    out.append("## Distribuição de inimigos")
    out.append("")
    out.append("★ = estreia da espécie (igual a `introduced_in`); ● = permitida; ◆ = permitida só em sub-área do bioma indicado.")
    out.append("")
    species_order = []
    for lid in ids:
        for sid in LEVEL_BY_ID[lid]["allowed_enemies"]:
            if sid not in species_order:
                species_order.append(sid)
    out.append("| Espécie | " + " | ".join(f"{n}-{i}" for i in range(1, 7)) + " |")
    out.append("| --- | " + " | ".join(":---:" for _ in range(6)) + " |")
    for sid in species_order:
        row = []
        for lid in ids:
            e = LEVEL_BY_ID[lid]
            if sid not in e["allowed_enemies"]:
                row.append("")
                continue
            if sid.startswith("boss:"):
                row.append("chefe")
                continue
            sp = SPECIES[sid]
            if sp["introduced_in"] == lid:
                row.append("★")
            elif world["biome"] in sp["habitats"]:
                row.append("●")
            else:
                tags = [t for t in re.findall(r"\[(\w+)\]", " ".join(e["size"]["areas"])) if t in sp["habitats"]]
                row.append("◆ " + (tags[0] if tags else "?"))
        label = species_name(sid, BOSS_BY_ID)
        out.append(f"| {label} (`{sid}`) | " + " | ".join(row) + " |")
    out.append("")
    counts = " · ".join(f"{n}-{i}: {LEVEL_BY_ID[l]['planned_enemy_count']['min']}–{LEVEL_BY_ID[l]['planned_enemy_count']['max']}" for i, l in enumerate(ids, 1))
    out.append(f"Quantidade planejada de inimigos (sem chefes): {counts}.")
    out.append("")
    # boss
    out.append(f"## Chefe do mundo — {B['name']} (`{B['id']}`, {B['status']})")
    out.append("")
    out.append(f"- **Fase:** `{B['level']}`")
    out.append(f"- **Arena:** {B['arena']}")
    out.append("- **Ataques:**")
    out.append(md_list(B["attacks"], "  "))
    out.append(f"- **Janela de vulnerabilidade:** {B['vulnerability']}")
    out.append(f"- **Fases e mudança de fase:** {B['phases']}")
    out.append(f"- **Derrota (animação):** {B['defeat']}")
    out.append(f"- **Relação com a mecânica do mundo:** {B['world_mechanic']}")
    if B["status"] == "planejado":
        out.append(f"- **Implementação:** chefe planejado — nova família de comportamento, entrada `boss: true` no registro (ver seção 6.2 do plano geral), eventos `boss_arena`/`camera_lock` e os requisitos listados na fase `{B['level']}`.")
    else:
        beh = SPECIES[B["id"]]["behavior"] if B["id"] in SPECIES else "?"
        out.append(f"- **Implementação:** família `{beh}` em `lume/core/behaviors/bosses.py` (implementada, entrada `{B['id']}` no registro); a fase `{B['level']}` já declara `boss_arena` com portões `gate_left`/`gate_right`.")
    mid = [sid for sid in LEVEL_BY_ID[ids[2]]["allowed_enemies"] if SPECIES.get(sid, {}).get("boss")]
    if mid:
        out.append("")
        out.append(f"**Minichefe da fase 3:** {', '.join(SPECIES[m]['name'] for m in mid)} (família `guardian`, implementado): avança, salta e dispara; abre a guarda periodicamente (janela de pisão), mais rápido na segunda metade.")
    elif ids[2] == "gravity_halls":
        out.append("")
        out.append("**Minichefe da fase 3:** Guardião da Constelação (elite `charger`, 3 golpes) no salão do mosaico de `gravity_halls`.")
    else:
        out.append("")
        out.append(f"**Fase 3 sem minichefe:** `{ids[2]}` termina num teste de movimento próprio (ver resumo abaixo).")
    out.append("")
    # NPC
    npc = W["npc"]
    out.append(f"## NPC do mundo — {npc['name']}, {npc['role']}")
    out.append("")
    out.append(f"**Função.** {npc['function']}")
    out.append("")
    out.append("**Falas-guia**")
    out.append(md_list(npc["lines"]))
    out.append("")
    out.append(f"**Implementação.** {npc['implementation']}")
    out.append("")
    # per-level summaries
    out.append("## Resumo por fase")
    out.append("")
    for slot, lid in enumerate(ids, 1):
        e = LEVEL_BY_ID[lid]
        L = SRC_BY_ID[lid]
        deb = [SPECIES[s]["name"] for s in new_species(lid)]
        out.append(f"### {n}-{slot} · {e['name']} (`{lid}`) — {e['origin']}")
        out.append("")
        out.append(f"- **Ideia própria:** {L['twist']}.")
        out.append(f"- **Objetivo:** {e['objective']}")
        out.append(f"- **Mecânica principal:** {e['main_mechanic']}")
        out.append(f"- **Dificuldade / duração / tamanho:** {e['difficulty']}/10 · {e['planned_duration_s'][0]}–{e['planned_duration_s'][1]} s · {e['size']['width']}×{e['size']['height']} u · {e['checkpoints']} checkpoint(s)")
        out.append(f"- **Estreias:** {', '.join(deb) if deb else '—'}")
        out.append(f"- **Relíquias:** " + "; ".join(f"{s['reward']} — pista: {s['clue']}" for s in e["secrets"] if "relíquia" in s["reward"]))
        out.append(f"- **Requisitos de motor:** " + ("; ".join(e["engine_requirements"]) if e["engine_requirements"] else "nenhum"))
        out.append(f"- Seção completa: [`PLANEJAMENTO_60_FASES.md`](PLANEJAMENTO_60_FASES.md#{anchor(e)})")
        out.append("")
    return "\n".join(out)


def anchor(e: dict) -> str:
    title = f"{level_label(e)} · {e['name']} ({e['id']})"
    a = title.lower()
    a = re.sub(r"[^\w\- ]", "", a, flags=re.UNICODE)
    return a.replace(" ", "-")


docs = REPO / "docs/level_design"
docs.mkdir(parents=True, exist_ok=True)
(docs / "PLANEJAMENTO_60_FASES.md").write_text(main_doc(), encoding="utf-8")
for world, module in worlds_data:
    (docs / f"MUNDO_{world_no(world['id']):02d}.md").write_text(world_doc(world, module), encoding="utf-8")

print(f"ok: {len(levels)} fases, {len(bosses)} chefes -> {out_json}")
print("bloqueadas:", [e["id"] for e in levels if blocking_reqs(e)])
