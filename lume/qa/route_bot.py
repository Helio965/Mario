"""Automated player used by the campaign tests.

Port of ``tests/helpers/route-player.ts``. The bot has the same authority as a
person holding a controller: it reads the simulation and calls
``Game.update`` with ordinary inputs. It never teleports, grants items,
changes lives or removes enemies/hazards. Extended for the species added in
the Python edition (spiked tops, emerging plants, chargers, swimming).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

from ..core.constants import FIXED_DT
from ..core.entities import Enemy, Platform
from ..core.game import Game
from ..core.input import InputState
from ..levels.schema import LevelSpec


@dataclass
class RouteResult:
    game: Game
    ticks: int
    deaths: int
    powers: int
    boss_hits: int
    samples: list[dict] = field(default_factory=list)
    incidents: list[str] = field(default_factory=list)

    @property
    def completed(self) -> bool:
        return self.game.status == "complete"

    def summary(self) -> str:
        g = self.game
        tail = self.samples[-12:]
        return (
            f"status={g.status} lives={g.lives} deaths={self.deaths} powers={self.powers} boss_hits={self.boss_hits} "
            f"x={g.player.x:.0f} y={g.player.y:.0f}\nincidents={self.incidents[-6:]}\ntail={tail}"
        )


def play_route(level: LevelSpec, seconds: float = 100.0, *, run: bool = True, game: Optional[Game] = None) -> RouteResult:
    game = game or Game([level])
    step = FIXED_DT
    state = {"hold": 0.0, "cooldown": 0.0, "landing": False}
    goal: Optional[Platform] = None
    collecting = False
    boss_mode = False
    grounded_before = False
    jump_run = True
    deaths = powers = boss_hits = 0
    samples: list[dict] = []
    incidents: list[str] = []
    cursor = 0
    ticks = 0

    def steer(inp: InputState, center: float, running: bool = False) -> None:
        p = game.player
        projected = p.x + p.w / 2 + p.vx * (0.08 if p.grounded else 0.1)
        inp.left = projected > center + 5
        inp.right = projected < center - 5
        inp.run = running

    def jump(duration: float = 0.64) -> None:
        if state["cooldown"] > 0 or state["landing"] or state["hold"] > 0:
            return
        state["hold"] = duration
        state["cooldown"] = 0.18

    def solid(s: Platform) -> bool:
        return s.alive and (s.kind != "hidden" or s.used) and (s.kind != "switch" or s.active)

    while ticks < seconds * 120 and game.status not in ("complete", "gameover"):
        p = game.player
        state["landing"] = p.grounded and not grounded_before
        grounded_before = p.grounded
        if state["landing"]:
            state["hold"] = 0.0
        state["hold"] = max(0.0, state["hold"] - step)
        state["cooldown"] = max(0.0, state["cooldown"] - step)
        inp = InputState(right=True, run=run, ability=True)
        reason = "corrida"
        boss = next((e for e in game.enemies if e.alive and game.profiles[e.species].boss), None)
        if boss and p.x > boss.patrol[0] - 180:
            boss_mode = True
        if game.status == "dead":
            goal, collecting, boss_mode = None, False, False
            state["hold"] = state["cooldown"] = 0.0
        elif boss_mode and boss:
            reason = "chefe"
            _fight_boss(game, boss, inp, steer, jump)
        else:
            if goal is None and p.grounded:
                goal = next(
                    (
                        s for s in game.platforms
                        if s.alive and not s.used
                        and ((s.reward == "grow" and p.power == "small") or (s.reward == "fire" and p.power != "fire"))
                        and p.x - 36 < s.x < p.x + 200
                    ),
                    None,
                )
            if goal is not None:
                if goal.used:
                    collecting = True
                if not collecting:
                    reason = f"bloco-{goal.reward}"
                    steer(inp, goal.x + goal.w / 2)
                    if p.grounded and abs(p.x + p.w / 2 - (goal.x + goal.w / 2)) < 10 and abs(p.vx) < 45:
                        jump()
                else:
                    reward = next((i for i in game.items if i.id == f"item-{goal.id}" and i.alive), None)
                    if reward is not None:
                        reason = f"coleta-{reward.kind}"
                        steer(inp, reward.x + reward.w / 2 + reward.vx * 0.1)
                    else:
                        goal, collecting = None, False
            ahead = p.x + p.w
            floor_ahead = any(
                solid(s) and s.x <= ahead + 18 <= s.x + s.w and p.y + p.h - 8 <= s.y <= p.y + p.h + 80
                for s in game.index.query(ahead, ahead + 20)
            )
            wall = any(
                solid(s) and s.kind != "semisolid" and ahead - 2 <= s.x < ahead + 64 and s.y < p.y + p.h - 3 and s.y + s.h > p.y
                for s in game.index.query(ahead - 2, ahead + 64)
            )
            enemy_ahead = any(
                _threat(game, e) and e.x + e.w > p.x and e.x < ahead + 120 and e.y < p.y + p.h + 16 and e.y + e.h > p.y - 8
                for e in game.enemies
            )
            danger_ahead = False
            for h in game.hazards:
                hx, hy = h.position(game.elapsed)
                if hx + h.w > p.x and hx < ahead + 90 and hy < p.y + p.h and hy + h.h > p.y:
                    danger_ahead = True
                    break
            incoming = any(
                s.hostile and s.vx < 0 and ahead < s.x < ahead + 160 and s.y + s.h > p.y and s.y < p.y + p.h
                for s in game.projectiles
            )
            collecting_shot = goal is not None and any(
                s.hostile and s.vx < 0 and ahead < s.x < ahead + 42 and s.y + s.h > p.y and s.y < p.y + p.h
                for s in game.projectiles
            )
            if collecting_shot and p.grounded:
                jump()
            if p.grounded and (wall or not floor_ahead or enemy_ahead or danger_ahead or incoming) and goal is None:
                reason = (
                    "obstáculo" if wall else "vão" if not floor_ahead else "inimigo" if enemy_ahead
                    else "perigo" if danger_ahead else "projétil"
                )
                jump_run = run and not wall and not danger_ahead
                jump()
            if state["hold"] > 0 and goal is None:
                inp.run = jump_run
            if p.swimming:
                inp.jump = int(game.elapsed * 3) % 2 == 0
        if not p.swimming or boss_mode:
            inp.jump = state["hold"] > 0 or (boss_mode and boss is not None and not p.grounded)
        before = f"{ticks / 120:.2f}s ({p.x:.0f},{p.y:.0f}) {p.power} {reason}"
        game.update(step, inp)
        for event in game.events[cursor:]:
            if event.type in ("stomp", "kick") and game.player.vy < 0 and not boss_mode:
                # A person keeps the button held through a stomp bounce.
                state["hold"] = max(state["hold"], 0.4)
            if event.type == "death":
                deaths += 1
                incidents.append(before)
            elif event.type == "power":
                powers += 1
            elif event.type == "stomp" and boss_mode:
                boss_hits += 1
        cursor = len(game.events)
        if ticks % 120 == 0:
            sample = {"t": ticks // 120, "x": round(game.player.x), "y": round(game.player.y), "lives": game.lives,
                      "power": game.player.power, "reason": reason}
            if boss is not None:
                sample["boss"] = f"{boss.health}/{boss.state}/{round(boss.x)}"
            samples.append(sample)
        ticks += 1
    return RouteResult(game, ticks, deaths, powers, boss_hits, samples, incidents)


def _floor_below(game: Game, x: float, y: float, depth: float):
    for s in game.index.query(x - 1, x + 1):
        if not s.alive or (s.kind == "hidden" and not s.used):
            continue
        if s.x <= x <= s.x + s.w and y - 4 <= s.y <= y + depth:
            return s
    return None


def _threat(game: Game, e: Enemy) -> bool:
    if not e.alive or not e.active or game.profiles[e.species].boss:
        return False
    behavior = game.behaviors[e.species]
    return behavior.tangible(game, e) or e.memory.get("family") in ("emerger", "burrower")


def _fight_boss(game: Game, boss: Enemy, inp: InputState, steer, jump) -> None:
    p = game.player
    center = boss.x + boss.w / 2
    inp.run = False
    behavior = game.behaviors[boss.species]
    if not p.grounded:
        steer(inp, center + boss.vx * 0.13)
        return
    side = -1 if p.x + p.w / 2 < center else 1
    launch = center + side * 125
    steer(inp, launch)
    window = behavior.stompable(game, boss) and not behavior.spiked(game, boss)
    if abs(p.x + p.w / 2 - launch) < 20 and window and boss.hit_timer < 0.1:
        steer(inp, center)
        jump(0.74)
    elif boss.memory.get("family") == "thorn_boar" and boss.state == "charge":
        if math.copysign(1, center - (p.x + p.w / 2)) == -boss.facing and abs(center - p.x) < 170:
            jump(0.7)
