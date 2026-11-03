"""Semantic validation of levels and of the whole campaign.

Structural parsing lives in :mod:`schema`; this module checks meaning:
references, biome/species compatibility, teaching order of species, safe
spawn/checkpoints, reachable warp targets, exit on solid ground, and mandatory
jumps simulated with the real physics (``move_body``).

Passing these checks proves the geometry is *traversable*; it does not prove a
level is fun or balanced (see docs/technical/TESTES_CAMPANHA.md).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

from ..core import constants as C
from ..core.entities import Platform
from ..core.physics import CollisionIndex, move_body
from ..core.species import EnemyProfile
from .errors import Problem
from .schema import LevelSpec

ROLE_ORDER = ["presentation", "exploration", "movement", "special", "advanced", "fortress"]
EXTRA_BIOMES = {"underground", "fortress", "underwater"}


@dataclass
class Gap:
    left: Platform
    right: Platform
    width: float
    rise: float  # positive = next surface is higher

    def describe(self) -> str:
        return f"vão {self.left.id}→{self.right.id} ({self.width:.0f} u, desnível {self.rise:+.0f} u)"


def _platforms(level: LevelSpec) -> list[Platform]:
    from ..core.entities import Motion

    out = []
    for s in level.platforms:
        out.append(
            Platform(
                id=s.id, kind=s.kind, x=s.x, y=s.y, w=s.w, h=s.h, surface=s.surface,
                motion=Motion(s.motion.axis, s.motion.range, s.motion.speed, s.motion.phase) if s.motion else None,
            )
        )
    return out


def main_path_gaps(level: LevelSpec) -> list[Gap]:
    """Gaps between consecutive terrain bodies of the main area (y < 540)."""
    main = level.areas[0]
    ground = sorted(
        (p for p in _platforms(level) if p.kind == "ground" and main.y <= p.y < main.y + main.h and p.w >= 120),
        key=lambda p: p.x,
    )
    # Keep only the top surface per x interval (ignore walls/pillars under other ground).
    gaps: list[Gap] = []
    for a, b in zip(ground, ground[1:]):
        width = b.x - (a.x + a.w)
        if width > 0:
            gaps.append(Gap(a, b, width, a.y - b.y))
    return gaps


class _Body:
    __slots__ = ("x", "y", "w", "h", "vx", "vy")

    def __init__(self, x, y, w, h):
        self.x, self.y, self.w, self.h, self.vx, self.vy = x, y, w, h, 0.0, 0.0


def jump_reaches(index: CollisionIndex, start: Platform, target: Platform, height: float, takeoff: float,
                 run: bool = True, hold: float = 0.6) -> bool:
    """Simulate a running jump from ``takeoff`` u before the edge of ``start``."""
    body = _Body(start.x + start.w - C.PLAYER_WIDTH - takeoff, start.y - height, C.PLAYER_WIDTH, height)
    body.vx = C.RUN_SPEED if run else C.WALK_SPEED
    body.vy = 0.0
    grounded = True
    jumped = False
    t = 0.0
    for _ in range(int(3.0 / C.FIXED_DT)):
        t += C.FIXED_DT
        if grounded and body.x + body.w >= start.x + start.w - 1 and not jumped:
            body.vy = -C.JUMP_SPEED
            jumped = True
            grounded = False
        if jumped and t > hold + 0.5 and body.vy < C.JUMP_CUT_SPEED:
            body.vy = C.JUMP_CUT_SPEED
        body.vy = min(C.MAX_FALL_SPEED, body.vy + C.GRAVITY * C.FIXED_DT)
        result = move_body(body, index, C.FIXED_DT)
        if result.grounded:
            grounded = True
            if jumped and result.standing_on is not None and result.standing_on.id == target.id:
                return True
            if jumped and result.standing_on is not None and result.standing_on.id != start.id:
                return result.standing_on.x >= start.x + start.w  # landed on an intermediate platform ahead
            if jumped and result.standing_on is start:
                return False
        if body.y > target.y + 400:
            return False
    return False


def simulate_gap(level: LevelSpec, gap: Gap) -> dict[str, bool]:
    platforms = _platforms(level)
    index = CollisionIndex([p for p in platforms if p.motion is None])
    by_id = {p.id: p for p in index.platforms}
    left, right = by_id[gap.left.id], by_id[gap.right.id]
    out = {}
    for label, height in (("pequeno", C.PLAYER_SMALL_HEIGHT), ("grande", C.PLAYER_BIG_HEIGHT)):
        out[label] = any(jump_reaches(index, left, right, height, takeoff) for takeoff in (2, 8, 16, 24, 40))
    return out


def _floor_under(level: LevelSpec, x: float, y: float, w: float, depth: float = 140) -> bool:
    for p in level.platforms:
        if p.kind in ("hidden",):
            continue
        if x + w > p.x and x < p.x + p.w and y <= p.y <= y + depth:
            return True
    return False


def validate_level(level: LevelSpec, profiles: dict[str, EnemyProfile], *, world_biome: Optional[str] = None,
                   simulate: bool = True) -> list[Problem]:
    from ..core.behaviors import BEHAVIORS

    src = level.source or level.id
    problems: list[Problem] = []

    def err(path: str, msg: str) -> None:
        problems.append(Problem(src, path, msg))

    def warn(path: str, msg: str) -> None:
        problems.append(Problem(src, path, msg, "warning"))

    ids = {p.id: p for p in level.platforms}
    collectible_ids = {c.id for c in level.collectibles}
    item_ids = {i.id for i in level.items}
    # --- species
    for i, e in enumerate(level.enemies):
        profile = profiles.get(e.species)
        if profile is None:
            err(f"enemies[{i}].species", f"espécie '{e.species}' não registrada")
            continue
        if profile.behavior not in BEHAVIORS:
            err(f"enemies[{i}].species", f"comportamento '{profile.behavior}' sem implementação")
        if world_biome:
            area = level.area_at(e.x, e.y - 1)
            allowed = set(profile.habitats)
            biome_ok = world_biome in allowed or (area is not level.areas[0] and allowed & EXTRA_BIOMES)
            if not biome_ok:
                err(f"enemies[{i}].species", f"'{e.species}' não habita o bioma '{world_biome}' ({', '.join(profile.habitats)})")
        if not (e.patrol[0] <= e.x <= e.patrol[1] - profile.w + 0.01) and profile.movement_type not in ("air", "ghost"):
            warn(f"enemies[{i}].patrol", f"posição inicial x={e.x:.0f} fora da patrulha {e.patrol}")
        sx, sy = level.spawn.x, level.spawn.y
        if abs(e.x - sx) < 160 and abs((e.y - profile.h) - sy) < 120 and not profile.boss:
            err(f"enemies[{i}]", "inimigo próximo demais do ponto de partida")
    # --- references
    for i, s in enumerate(level.secrets):
        for reward in s.rewards:
            if reward not in collectible_ids and reward not in item_ids:
                err(f"secrets[{i}].rewards", f"recompensa '{reward}' não existe")
        if s.entry and s.entry not in ids:
            err(f"secrets[{i}].entry", f"entrada '{s.entry}' não existe")
    for i, p in enumerate(level.platforms):
        if p.warp:
            if not (0 <= p.warp.x < level.width and 0 <= p.warp.y < level.height):
                err(f"platforms[{i}].warp", "destino fora dos limites da fase")
            elif not _floor_under(level, p.warp.x, p.warp.y + C.PLAYER_SMALL_HEIGHT, C.PLAYER_WIDTH, 100):
                err(f"platforms[{i}].warp", "destino sem chão de apoio")
            if p.kind != "pipe":
                err(f"platforms[{i}].warp", "apenas canos podem ter destino")
        if p.secret and p.secret not in {s.id for s in level.secrets}:
            warn(f"platforms[{i}].secret", f"segredo '{p.secret}' não descrito em secrets")
        if p.x < -200 or p.x + p.w > level.width + 200 or p.y + p.h > level.height + 200:
            err(f"platforms[{i}]", "plataforma fora dos limites da fase")
    # --- areas
    for i, a in enumerate(level.areas):
        if a.x < 0 or a.y < 0 or a.x + a.w > level.width + 0.01 or a.y + a.h > level.height + 0.01:
            err(f"areas[{i}]", "área fora dos limites declarados em bounds")
    # --- exit
    ex = level.exit
    if not any(p.x <= ex.x and p.x + p.w >= ex.x and abs(p.y - ex.y) < 0.01 for p in level.platforms if p.kind in ("ground", "ledge")):
        err("exit", "a bandeira precisa estar apoiada em terreno")
    if level.role == "fortress" and not any(profiles.get(e.species) and profiles[e.species].boss for e in level.enemies):
        err("role", "fortaleza sem chefe")
    if not level.collectibles:
        err("collectibles", "toda fase precisa de ao menos uma relíquia")
    if not level.checkpoints and level.width > 2400:
        warn("checkpoints", "fase longa sem checkpoint")
    # --- hazards at spawn/checkpoints
    points = [("spawn", level.spawn.x, level.spawn.y)] + [(f"checkpoint {c.id}", c.x, c.y) for c in level.checkpoints]
    for label, x, y in points:
        for h in level.hazards:
            if h.kind == "moving":
                hx0, hx1 = h.x - h.range, h.x + h.w + h.range
            else:
                hx0, hx1 = h.x, h.x + h.w
            if x + C.PLAYER_WIDTH > hx0 - 40 and x < hx1 + 40 and y + 60 > h.y and y - 60 < h.y + h.h:
                err(label, f"perigo '{h.id}' muito próximo")
    if simulate:
        problems.extend(_simulate_points(level, profiles, points))
        for gap in main_path_gaps(level):
            result = simulate_gap(level, gap)
            if not all(result.values()):
                failed = [k for k, ok in result.items() if not ok]
                err("platforms", f"{gap.describe()} não pode ser atravessado (jogador {', '.join(failed)})")
    return problems


def _simulate_points(level: LevelSpec, profiles, points) -> list[Problem]:
    from ..core.game import Game
    from ..core.input import EMPTY_INPUT
    from dataclasses import replace

    problems = []
    for label, x, y in points:
        spec = replace(level, spawn=type(level.spawn)(x, y), enemies=())
        game = Game([spec], profiles=profiles)
        for _ in range(90):
            game.update(C.FIXED_DT, EMPTY_INPUT)
        if game.lives != C.LIVES_START or not game.player.grounded:
            problems.append(Problem(level.source or level.id, label, "ponto de partida inseguro (não aterrissa com segurança)"))
    return problems


def validate_campaign(campaign, profiles: dict[str, EnemyProfile], simulate: bool = True) -> list[Problem]:
    problems: list[Problem] = []
    first_seen: dict[str, str] = {}
    biomes = {w.id: w.biome for w in campaign.worlds}
    order = {e.id: e.order for e in campaign.entries}
    for level in campaign.levels:
        problems.extend(validate_level(level, profiles, world_biome=biomes.get(level.world), simulate=simulate))
        entry = campaign.entry(level.id)
        expected_role = ROLE_ORDER[entry.slot - 1] if entry.slot <= len(ROLE_ORDER) else None
        if expected_role and level.role != expected_role:
            problems.append(Problem(level.source, "$.role", f"papel '{level.role}' difere do planejado '{expected_role}' para a posição {entry.slot}", "warning"))
        for e in level.enemies:
            first_seen.setdefault(e.species, level.id)
    for species, level_id in first_seen.items():
        profile = profiles.get(species)
        if profile and profile.introduced_in and profile.introduced_in in order and level_id in order:
            if order[level_id] < order[profile.introduced_in]:
                problems.append(Problem("enemies.json", species,
                                        f"aparece em '{level_id}' antes da fase de introdução '{profile.introduced_in}'"))
    return problems


def errors(problems: Iterable[Problem]) -> list[Problem]:
    return [p for p in problems if p.severity == "error"]
