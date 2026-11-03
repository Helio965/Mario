"""Validação de fases: esquema do JSON e viabilidade geométrica com a física real.

Usado pelos testes de dados, pelo carregador em modo estrito e pelo editor.
As verificações de salto repetem o método da validação original (docs/FASES.md):
simular a corrida e o salto do jogador a partir de vários pontos de impulsão
antes de cada vão do caminho principal, nas duas alturas do personagem e em
fases diferentes do movimento das plataformas, usando ``Game`` de verdade.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass, replace
from typing import Any

from game.core.game import Game
from game.core.types import (
    HAZARD_KINDS,
    ITEM_KINDS,
    PLATFORM_KINDS,
    InputState,
    Level,
    PlatformSpec,
    Rect,
)
from game.enemies.registry import known_enemy_kinds
from game.physics.collision import overlaps
from game.physics.movement import FIXED_DT, LEGACY_PROFILE, MovementProfile

MAIN_GROUND_MIN_HEIGHT = 100.0
TAKEOFF_OFFSETS = (0, 20, 40, 60, 80, 100, 120)
PLATFORM_PHASES = (0.0, 0.8, 1.6, 2.4)
SMALL_HEIGHT = 30.0
BIG_HEIGHT = 46.0


@dataclass(slots=True, frozen=True)
class Issue:
    severity: str  # "error" | "warning"
    code: str
    message: str
    ref: str | None = None

    def __str__(self) -> str:
        where = f" [{self.ref}]" if self.ref else ""
        return f"{self.severity}:{self.code}{where} {self.message}"


# ------------------------------------------------------------------ esquema
def _num(value: Any) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool)


def _rect_ok(d: dict[str, Any]) -> bool:
    return all(_num(d.get(k)) for k in ("x", "y", "w", "h")) and d["w"] > 0 and d["h"] > 0


def validate_level_dict(d: Any) -> list[Issue]:
    """Confere a estrutura do JSON antes de construir a ``Level``."""
    issues: list[Issue] = []
    if not isinstance(d, dict):
        return [Issue("error", "schema", "a fase precisa ser um objeto JSON")]
    for key in (
        "id",
        "name",
        "world",
        "stage",
        "width",
        "height",
        "time",
        "spawn",
        "checkpoint",
        "exit",
    ):
        if key not in d:
            issues.append(Issue("error", "schema", f"campo obrigatório ausente: {key}"))
    if issues:
        return issues
    if not isinstance(d["id"], str) or not d["id"]:
        issues.append(Issue("error", "schema", "id deve ser texto não vazio"))
    for key in ("width", "height", "time"):
        if not _num(d[key]) or d[key] <= 0:
            issues.append(Issue("error", "schema", f"{key} deve ser número positivo"))
    for key in ("spawn", "checkpoint", "exit"):
        point = d[key]
        if not isinstance(point, dict) or not _num(point.get("x")) or not _num(point.get("y")):
            issues.append(Issue("error", "schema", f"{key} deve ter x e y numéricos"))
    seen: set[str] = set()
    for p in d.get("platforms", []):
        ref = str(p.get("id"))
        if p.get("kind") not in PLATFORM_KINDS:
            issues.append(
                Issue("error", "platform.kind", f"tipo desconhecido {p.get('kind')!r}", ref)
            )
        if not _rect_ok(p):
            issues.append(Issue("error", "platform.rect", "x, y, w, h numéricos com w, h > 0", ref))
        if ref in seen:
            issues.append(Issue("error", "id.duplicate", "id repetido", ref))
        seen.add(ref)
        motion = p.get("motion")
        if motion is not None and (
            motion.get("axis") not in ("x", "y")
            or not _num(motion.get("range"))
            or not _num(motion.get("speed"))
        ):
            issues.append(
                Issue("error", "platform.motion", "motion precisa de axis x|y, range e speed", ref)
            )
        if p.get("reward") is not None and p["reward"] not in (*ITEM_KINDS, "coin"):
            issues.append(
                Issue("error", "platform.reward", f"recompensa desconhecida {p['reward']!r}", ref)
            )
    for c in d.get("coins", []):
        ref = str(c.get("id"))
        if not _rect_ok(c):
            issues.append(Issue("error", "coin.rect", "moeda sem retângulo válido", ref))
        if ref in seen:
            issues.append(Issue("error", "id.duplicate", "id repetido", ref))
        seen.add(ref)
    for e in d.get("enemies", []):
        ref = str(e.get("id"))
        if e.get("kind") not in known_enemy_kinds():
            issues.append(Issue("error", "enemy.kind", f"tipo desconhecido {e.get('kind')!r}", ref))
        if not _rect_ok(e):
            issues.append(Issue("error", "enemy.rect", "inimigo sem retângulo válido", ref))
        patrol = e.get("patrol")
        if (
            not isinstance(patrol, list)
            or len(patrol) != 2
            or not all(_num(v) for v in patrol)
            or patrol[0] >= patrol[1]
        ):
            issues.append(
                Issue(
                    "error",
                    "enemy.patrol",
                    "patrol deve ser [esquerda, direita] com esquerda < direita",
                    ref,
                )
            )
        if ref in seen:
            issues.append(Issue("error", "id.duplicate", "id repetido", ref))
        seen.add(ref)
    for i in d.get("items", []):
        ref = str(i.get("id"))
        if i.get("kind") not in ITEM_KINDS:
            issues.append(Issue("error", "item.kind", f"tipo desconhecido {i.get('kind')!r}", ref))
        if not _rect_ok(i):
            issues.append(Issue("error", "item.rect", "item sem retângulo válido", ref))
        if ref in seen:
            issues.append(Issue("error", "id.duplicate", "id repetido", ref))
        seen.add(ref)
    for n, h in enumerate(d.get("hazards", [])):
        if h.get("kind") not in HAZARD_KINDS:
            issues.append(
                Issue("error", "hazard.kind", f"tipo desconhecido {h.get('kind')!r}", f"hazard#{n}")
            )
        if not _rect_ok(h):
            issues.append(
                Issue("error", "hazard.rect", "perigo sem retângulo válido", f"hazard#{n}")
            )
    for n, hint in enumerate(d.get("hints", [])):
        if not _num(hint.get("x")) or not isinstance(hint.get("text"), str):
            issues.append(Issue("error", "hint", "dica precisa de x numérico e text", f"hint#{n}"))
    return issues


# --------------------------------------------------------------- geometria
def _support_below(
    x: float, y: float, w: float, platforms: list[PlatformSpec], reach: float = 100.0
) -> PlatformSpec | None:
    """Plataforma sólida cujo topo está entre o pé do retângulo e ``reach`` px abaixo."""
    best: PlatformSpec | None = None
    for p in platforms:
        if p.kind == "hidden":
            continue
        if (
            x + w > p.x
            and x < p.x + p.w
            and y + SMALL_HEIGHT - 1 <= p.y <= y + SMALL_HEIGHT + reach
            and (best is None or p.y < best.y)
        ):
            best = p
    return best


def main_grounds(level: Level) -> list[PlatformSpec]:
    grounds = [
        p for p in level.platforms if p.kind in ("ground", "ice") and p.h >= MAIN_GROUND_MIN_HEIGHT
    ]
    return sorted(grounds, key=lambda p: p.x)


def geometry_level(level: Level) -> Level:
    """Cópia da fase só com cenário (sem inimigos, perigos, itens e moedas)."""
    return replace(level, enemies=[], hazards=[], items=[], coins=[], hints=[])


def runway_start(
    level: Level, source: PlatformSpec, takeoff: float, height: float, runway: float = 260.0
) -> float:
    """Início da corrida: depois do último obstáculo que bloquearia o corpo sobre ``source``."""
    band = Rect(source.x, source.y - height, max(1.0, takeoff - source.x), height - 1)
    start = max(source.x + 2, takeoff - runway)
    for p in level.platforms:
        if p.kind == "hidden" or p.id == source.id or not overlaps(band, p):
            continue
        start = max(start, p.x + p.w + 2)
    return start


def jump_gap_feasible(
    level: Level,
    source: PlatformSpec,
    target: PlatformSpec,
    profile: MovementProfile = LEGACY_PROFILE,
    big: bool = False,
    phase: float = 0.0,
    offsets: tuple[int, ...] = TAKEOFF_OFFSETS,
) -> int | None:
    """Simula correr e saltar do fim de ``source`` ao início de ``target``.

    Devolve a distância de impulsão (px antes da borda) que funcionou ou ``None``.
    """
    geometry = geometry_level(level)
    edge = source.x + source.w
    height = BIG_HEIGHT if big else SMALL_HEIGHT
    for offset in offsets:
        takeoff = edge - offset
        start = runway_start(level, source, takeoff, height)
        if start >= takeoff - 10:
            continue
        game = Game([geometry], profile)
        game.elapsed = phase
        game.spawn(start, source.y - (BIG_HEIGHT if big else SMALL_HEIGHT))
        if big:
            game.player.power = "grown"
            game.player.h = BIG_HEIGHT
        game.player.invulnerable = 0
        jumped = False
        for _ in range(120 * 6):
            p = game.player
            if not jumped and p.grounded and p.x + p.w >= takeoff:
                jumped = True
            game.update(FIXED_DT, InputState(right=True, run=True, jump=jumped))
            if game.status != "playing":
                break
            if jumped and p.grounded and p.standing_on == target.id:
                return offset
            if jumped and p.grounded and p.x >= target.x:
                return offset
            if jumped and p.x + p.w >= target.x + target.w:
                break
    return None


def validate_level(
    level: Level, profile: MovementProfile = LEGACY_PROFILE, check_jumps: bool = True
) -> list[Issue]:
    """Verificações semânticas e físicas sobre uma ``Level`` já construída."""
    issues: list[Issue] = []
    platforms = level.platforms
    if not platforms:
        return [Issue("error", "empty", "a fase não tem plataformas")]
    ids = (
        [p.id for p in platforms]
        + [c.id for c in level.coins]
        + [e.id for e in level.enemies]
        + [i.id for i in level.items]
    )
    if len(ids) != len(set(ids)):
        issues.append(
            Issue(
                "error",
                "id.duplicate",
                "há ids repetidos entre plataformas, moedas, inimigos e itens",
            )
        )
    for name, point in (("spawn", level.spawn), ("checkpoint", level.checkpoint)):
        if not (0 <= point.x < level.width):
            issues.append(Issue("error", f"{name}.bounds", "fora da largura da fase"))
        if _support_below(point.x, point.y, 22, platforms) is None:
            issues.append(Issue("error", f"{name}.support", "não há chão até 100 px abaixo"))
        box = Rect(point.x, point.y, 22, SMALL_HEIGHT)
        for h in level.hazards:
            if overlaps(box, h):
                issues.append(Issue("error", f"{name}.hazard", f"sobre um perigo ({h.kind})"))
        for e in level.enemies:
            if e.patrol[0] <= point.x <= e.patrol[1] and abs(e.y - point.y) < 60:
                issues.append(Issue("warning", f"{name}.enemy", f"dentro da patrulha de {e.id}"))
    if not any(p.x <= level.exit.x <= p.x + p.w and p.y == level.exit.y for p in platforms):
        issues.append(
            Issue(
                "error",
                "exit.support",
                "a base da bandeira não coincide com o topo de uma plataforma",
            )
        )
    if not any(c.special for c in level.coins):
        issues.append(Issue("warning", "relic.missing", "a fase não tem relíquia"))
    for p in platforms:
        if p.destination is not None:
            if not (0 <= p.destination.x < level.width):
                issues.append(Issue("error", "pipe.destination", "destino fora da fase", p.id))
            elif _support_below(p.destination.x, p.destination.y, 22, platforms) is None:
                issues.append(
                    Issue(
                        "error",
                        "pipe.destination.support",
                        "destino sem chão até 100 px abaixo",
                        p.id,
                    )
                )
        if p.x < 0 or p.x + p.w > level.width:
            issues.append(
                Issue("warning", "platform.bounds", "plataforma ultrapassa a largura da fase", p.id)
            )
    bosses = [e for e in level.enemies if e.kind == "boss"]
    if level.stage == 3 and len(bosses) != 1:
        issues.append(
            Issue(
                "warning",
                "boss.count",
                f"fase 3 deveria ter exatamente um guardião (tem {len(bosses)})",
            )
        )
    if level.stage != 3 and bosses:
        issues.append(Issue("warning", "boss.stage", "guardião fora da terceira fase"))
    for e in level.enemies:
        if not (e.patrol[0] <= e.x and e.x + e.w <= e.patrol[1]):
            issues.append(Issue("error", "enemy.patrol", "posição inicial fora da patrulha", e.id))
        if e.kind != "flyer" and _support_below(e.x, e.y, e.w, platforms, reach=4) is None:
            issues.append(
                Issue(
                    "warning",
                    "enemy.support",
                    "inimigo terrestre sem chão imediatamente abaixo",
                    e.id,
                )
            )
    if check_jumps:
        grounds = main_grounds(level)
        for source, target in itertools.pairwise(grounds):
            gap = target.x - (source.x + source.w)
            if gap <= 0:
                continue
            for big in (False, True):
                ok = any(
                    jump_gap_feasible(level, source, target, profile, big, phase) is not None
                    for phase in PLATFORM_PHASES
                )
                if not ok:
                    issues.append(
                        Issue(
                            "error",
                            "gap.unreachable",
                            f"vão de {gap:.0f} px (desnível {target.y - source.y:+.0f}) intransponível {'crescido' if big else 'pequeno'}",
                            f"{source.id}->{target.id}",
                        )
                    )
    return issues


def errors(issues: list[Issue]) -> list[Issue]:
    return [i for i in issues if i.severity == "error"]
