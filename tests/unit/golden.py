"""Reprodução dos traces de ouro gravados com o motor TypeScript de referência.

Cada fixture contém as entradas tick a tick (RLE), a posição do jogador a cada
``every`` ticks, instantâneos completos a cada ``full`` ticks e todos os eventos.
O port Python precisa reproduzir exatamente a mesma trajetória.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from game.core.game import Game
from game.core.types import InputState, Level
from game.levels.loader import level_from_dict, load_levels
from game.physics.movement import FIXED_DT

TOLERANCE = 1e-3

ARENA: dict[str, Any] = {
    "id": "arena",
    "name": "arena",
    "world": 1,
    "stage": 1,
    "width": 2400,
    "height": 540,
    "time": 300,
    "spawn": {"x": 64, "y": 414},
    "checkpoint": {"x": 1100, "y": 414},
    "exit": {"x": 2280, "y": 448},
    "platforms": [
        {"id": "floor", "kind": "ground", "x": 0, "y": 448, "w": 2400, "h": 92},
        {"id": "wall", "kind": "brick", "x": 480, "y": 368, "w": 128, "h": 80},
        {"id": "ceiling", "kind": "brick", "x": 700, "y": 330, "w": 140, "h": 16},
        {"id": "ice", "kind": "ice", "x": 1000, "y": 400, "w": 400, "h": 48},
        {"id": "q", "kind": "question", "reward": "grow", "x": 1500, "y": 336, "w": 40, "h": 28},
        {
            "id": "mov",
            "kind": "moving",
            "x": 1700,
            "y": 380,
            "w": 100,
            "h": 18,
            "motion": {"axis": "y", "range": 40, "speed": 1.5},
        },
        {"id": "crumb", "kind": "crumble", "x": 1900, "y": 380, "w": 100, "h": 20},
    ],
    "coins": [
        {"id": "c1", "x": 300, "y": 418, "w": 16, "h": 20},
        {"id": "r1", "x": 340, "y": 418, "w": 22, "h": 24, "special": True},
    ],
    "enemies": [
        {"id": "w", "kind": "walker", "x": 900, "y": 420, "w": 28, "h": 28, "patrol": [850, 1000]},
        {"id": "s", "kind": "shell", "x": 1300, "y": 420, "w": 28, "h": 28, "patrol": [1200, 1450]},
        {
            "id": "a",
            "kind": "armored",
            "x": 2000,
            "y": 416,
            "w": 34,
            "h": 32,
            "patrol": [1950, 2200],
            "hp": 2,
        },
        {
            "id": "sh",
            "kind": "shooter",
            "x": 2100,
            "y": 420,
            "w": 28,
            "h": 28,
            "patrol": [2080, 2150],
        },
        {"id": "f", "kind": "flyer", "x": 600, "y": 300, "w": 28, "h": 24, "patrol": [500, 800]},
    ],
    "items": [{"id": "fire", "kind": "fire", "x": 200, "y": 420, "w": 24, "h": 24}],
    "hazards": [
        {"kind": "spikes", "x": 1600, "y": 434, "w": 48, "h": 14},
        {"kind": "moving", "x": 1150, "y": 300, "w": 26, "h": 26, "range": 40, "speed": 1.6},
    ],
    "hints": [],
}


def input_from_mask(mask: int) -> InputState:
    return InputState(
        left=bool(mask & 1),
        right=bool(mask & 2),
        jump=bool(mask & 4),
        run=bool(mask & 8),
        ability=bool(mask & 16),
        down=bool(mask & 32),
    )


def expand_inputs(rle: list[list[int]]) -> list[int]:
    out: list[int] = []
    for mask, count in rle:
        out.extend([mask] * count)
    return out


def r4(value: float) -> float:
    return round(value * 10000) / 10000


def snapshot(game: Game) -> dict[str, Any]:
    p = game.player
    return {
        "x": r4(p.x),
        "y": r4(p.y),
        "vx": r4(p.vx),
        "vy": r4(p.vy),
        "h": p.h,
        "power": p.power,
        "grounded": p.grounded,
        "standingOn": p.standing_on,
        "anim": p.animation,
        "inv": r4(p.invulnerable),
        "star": r4(p.star),
        "status": game.status,
        "lives": game.lives,
        "score": game.score,
        "coins": game.coins_total,
        "time": r4(game.time),
        "checkpoint": game.checkpoint_reached,
        "relic": game.found_relic,
        "camX": r4(game.camera.x),
        "camY": r4(game.camera.y),
        "enemies": [
            [e.id, r4(e.x), r4(e.y), e.state, e.health, e.facing] for e in game.enemies if e.alive
        ],
        "items": len(game.items),
        "projectiles": len(game.projectiles),
        "particles": len(game.particles),
        "platforms": [[s.id, s.used, s.alive] for s in game.platforms if s.used or not s.alive],
        "coinsLeft": sum(1 for c in game.coins if not c.collected),
    }


@dataclass(slots=True)
class Divergence:
    tick: int
    field: str
    expected: Any
    actual: Any

    def __str__(self) -> str:
        return f"tick {self.tick}: {self.field} esperado={self.expected!r} obtido={self.actual!r}"


def _close(a: Any, b: Any) -> bool:
    if isinstance(a, bool) or isinstance(b, bool):
        return a == b
    if isinstance(a, int | float) and isinstance(b, int | float):
        return abs(float(a) - float(b)) <= TOLERANCE
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(_close(x, y) for x, y in zip(a, b, strict=True))
    return bool(a == b)


def level_for(fixture: dict[str, Any]) -> Level:
    if fixture["level"] == "arena":
        return level_from_dict(ARENA)
    level = next((lvl for lvl in load_levels() if lvl.id == fixture["level"]), None)
    assert level is not None, fixture["level"]
    return level


def replay(
    fixture: dict[str, Any], game: Game | None = None, stop_at_first: bool = True
) -> list[Divergence]:
    """Reproduz as entradas e devolve as divergências encontradas (vazio = fiel)."""
    if game is None:
        game = Game([level_for(fixture)])
    inputs = expand_inputs(fixture["inputs"])
    track = fixture["track"]
    snaps = {s["tick"]: s for s in fixture["snapshots"]}
    every, full = fixture["every"], fixture["full"]
    divergences: list[Divergence] = []
    expected_events = fixture["events"]
    event_cursor = 0
    seen_events = 0
    for tick, mask in enumerate(inputs):
        game.update(FIXED_DT, input_from_mask(mask))
        new_events = game.events[seen_events:]
        seen_events = len(game.events)
        for event in new_events:
            if event_cursor < len(expected_events):
                exp_tick, exp_type = expected_events[event_cursor]
                if exp_tick != tick or exp_type != event.type:
                    divergences.append(
                        Divergence(tick, "event", [exp_tick, exp_type], [tick, event.type])
                    )
            else:
                divergences.append(Divergence(tick, "event", None, [tick, event.type]))
            event_cursor += 1
        if tick % every == 0:
            i = (tick // every) * 2
            if i + 1 < len(track):
                ex, ey = track[i], track[i + 1]
                if abs(ex - game.player.x) > TOLERANCE or abs(ey - game.player.y) > TOLERANCE:
                    divergences.append(
                        Divergence(tick, "pos", [ex, ey], [r4(game.player.x), r4(game.player.y)])
                    )
        if tick % full == 0 and tick in snaps:
            got = snapshot(game)
            for key, value in snaps[tick].items():
                if key == "tick":
                    continue
                if not _close(value, got.get(key)):
                    divergences.append(Divergence(tick, key, value, got.get(key)))
        if divergences and stop_at_first:
            break
    if not divergences:
        if event_cursor != len(expected_events):
            divergences.append(
                Divergence(
                    len(inputs),
                    "events-missing",
                    expected_events[event_cursor : event_cursor + 3],
                    None,
                )
            )
        got = snapshot(game)
        for key, value in fixture["final"].items():
            if not _close(value, got.get(key)):
                divergences.append(Divergence(len(inputs), f"final.{key}", value, got.get(key)))
    return divergences


def load_fixture(path: Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as handle:
        data: dict[str, Any] = json.load(handle)
    return data
