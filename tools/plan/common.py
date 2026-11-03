"""Shared helpers for the 60-level plan generator (scratchpad only)."""

from __future__ import annotations

BEAT_LABELS = {
    1: "Introdução",
    2: "Demonstração segura",
    3: "Primeiro desafio",
    4: "Escalada",
    5: "Combinação",
    6: "Reviravolta",
    7: "Teste final",
    8: "Recompensa",
}

# Mandatory same-height gap limit per world (u). Task cap = 160 u; research
# (ENGENHARIA_REVERSA §5.2 regra 1) is stricter for early worlds.
GAP_LIMIT = {1: 125, 2: 150, 3: 150, 4: 150, 5: 150, 6: 160, 7: 160, 8: 160, 9: 160, 10: 160}

# Biomes that sub-areas may declare (validate.EXTRA_BIOMES) + world biomes.
SUB_BIOMES = {"underground", "fortress", "underwater"}

# Engine requirement identifiers (keep wording identical everywhere).
REQ_TOGGLE = "toggle_switch (extensão): a alternância por bloco 'toggle' já existe (Game.toggle_group); faltam o evento toggle_switch por gatilho, o interruptor temporizado e a ligação do grupo a outros sistemas (esteiras, plataformas fantasmas)"
REQ_RISING = "rising_lava (extensão): a subida única de um perigo por evento já existe (hazard/to/speed, gatilho por x); faltam ciclos de subida e descida, gatilho por altura, tempo ou chefe, aviso sonoro, etapas com pausa, reposição no checkpoint e a variante com zona swim (maré)"
REQ_LIGHTS = "lights (extensão): a máscara de escuridão das zonas dark com o halo de Lume (120 u; 64 u correndo) já é desenhada; faltam lanternas fixas e acendíveis com raio e duração e o evento lights global (apagar/acender)"
REQ_QUICKSAND = "quicksand: implementado durante a redação (andar a 45%, pulo a 62%, afunda e mata ao cobrir Lume)"
REQ_ARENA = "boss_arena/camera_lock: implementado durante a redação (trava de câmera, portões close/open)"
REQ_BREAKABLE = "breakable walls: paredes quebráveis por casco, fogo ou investida (segredos)"


def boss_req(boss_id: str, name: str) -> str:
    return f"comportamento do chefe planejado {name} ({boss_id}): família nova em lume/core/behaviors/bosses.py"


def beats(*items):
    """items: (n, 'x0–x1', text). Returns list of dicts."""
    out = []
    for n, rng, text in items:
        label = BEAT_LABELS[n]
        for prefix in (label + ": ", label + " — "):
            if text.startswith(prefix):
                text = text[len(prefix)].upper() + text[len(prefix) + 1:]
        out.append({"n": n, "label": label, "range": rng, "text": text})
    return out


def sec(id_, kind, clue, reward):
    return {"id": id_, "kind": kind, "clue": clue, "reward": reward}


def generic_tests(world: int, checkpoints: int, extra_gap: str | None = None):
    gap = GAP_LIMIT[world]
    tests = [
        "validate_level e validate_campaign sem erros (schema, espécies, bioma, ordem de introdução, warps com chão)",
        f"route_bot conclui a fase partindo do spawn e de cada um dos {checkpoints} checkpoint(s), com inimigos e perigos ativos",
        f"vãos obrigatórios ≤ {gap} u na mesma altura e subidas obrigatórias ≤ 64 u, simulados nas duas alturas do jogador sem coyote nem buffer"
        + (f"; {extra_gap}" if extra_gap else ""),
        "as 3 relíquias e todas as moedas são alcançáveis (rota de teste dedicada por relíquia; nenhuma moeda leva a morte)",
    ]
    return tests
