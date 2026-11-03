"""Condutor de campanha (port fiel de ``tests/helpers/route-player.ts``).

Este condutor tem a mesma autoridade que uma pessoa segurando o controle: ele
apenas lê a simulação e avança ``Game.update`` com entradas normais. Nunca
escreve estado de entidades, concede itens, altera vidas ou remove perigos.
"""

from __future__ import annotations

import copy
import json
import math
from dataclasses import dataclass, field

from game.core.game import Game
from game.core.types import Enemy, InputState, Level
from game.physics.movement import LEGACY_PROFILE, MovementProfile

STEP = 1 / 120


@dataclass(slots=True)
class RouteSample:
    second: float
    x: int
    y: int
    lives: int
    power: str
    reason: str
    boss: str | None = None


@dataclass(slots=True)
class RouteResult:
    game: Game
    samples: list[RouteSample]
    ticks: int
    deaths: int
    powers: int
    boss_hits: int
    incidents: list[str]
    inputs: list[int] = field(default_factory=list)


def input_mask(i: InputState) -> int:
    return (
        int(i.left)
        | (int(i.right) << 1)
        | (int(i.jump) << 2)
        | (int(i.run) << 3)
        | (int(i.ability) << 4)
        | (int(i.down) << 5)
    )


def _js_round(value: float) -> int:
    return math.floor(value + 0.5)


def play_campaign_route(
    level: Level,
    seconds: float = 100,
    run: bool = True,
    record_inputs: bool = False,
    profile: MovementProfile = LEGACY_PROFILE,
    smart_air: bool = False,
) -> RouteResult:
    """``smart_air`` liga a previsão de pouso: no ar, o condutor freia ou acelera para cair em chão."""
    game = Game([level], profile)
    state = {"jump_hold": 0.0, "jump_cooldown": 0.0, "landing_frame": False}
    goal = None
    collecting = False
    boss_mode = False
    grounded_before = False
    jump_run = True
    ticks = 0
    event_cursor = 0
    samples: list[RouteSample] = []
    incidents: list[str] = []
    inputs: list[int] = []
    deaths = powers = boss_hits = 0
    running = run
    plan: dict[str, object] = {}

    def steer(inp: InputState, center: float, run_now: bool = False) -> None:
        p = game.player
        projected = p.x + p.w / 2 + p.vx * (0.08 if p.grounded else 0.1)
        inp.left = projected > center + 5
        inp.right = projected < center - 5
        inp.run = run_now

    def jump(duration: float = 0.64) -> None:
        if state["jump_cooldown"] > 0 or state["landing_frame"] or state["jump_hold"] > 0:
            return
        state["jump_hold"] = duration
        state["jump_cooldown"] = 0.18

    while ticks < seconds * 120 and game.status != "complete" and game.status != "gameover":
        p = game.player
        state["landing_frame"] = p.grounded and not grounded_before
        grounded_before = p.grounded
        if state["landing_frame"]:
            state["jump_hold"] = 0.0
            plan.clear()
        state["jump_hold"] = max(0.0, state["jump_hold"] - STEP)
        state["jump_cooldown"] = max(0.0, state["jump_cooldown"] - STEP)
        inp = InputState(right=True, run=running, ability=True)
        reason = "corrida"
        boss: Enemy | None = next((e for e in game.enemies if e.alive and e.kind == "boss"), None)
        if boss is not None and p.x > boss.patrol[0] - 180:
            boss_mode = True

        if game.status == "dead":
            goal = None
            collecting = False
            boss_mode = False
            state["jump_hold"] = 0.0
            state["jump_cooldown"] = 0.0
        elif boss_mode and boss is not None:
            reason = "chefe"
            _fight_boss(game, boss, inp, steer, jump)
        else:
            if goal is None and p.grounded:
                goal = next(
                    (
                        s
                        for s in game.platforms
                        if s.alive
                        and not s.used
                        and (
                            (s.reward == "grow" and p.power == "small")
                            or (s.reward == "fire" and p.power != "fire")
                        )
                        and s.x > p.x - 36
                        and s.x < p.x + 200
                    ),
                    None,
                )
            if goal is not None:
                if goal.used:
                    collecting = True
                if not collecting:
                    reason = f"bloco-{goal.reward}"
                    steer(inp, goal.x + goal.w / 2)
                    if (
                        p.grounded
                        and abs(p.x + p.w / 2 - (goal.x + goal.w / 2)) < 10
                        and abs(p.vx) < 45
                    ):
                        jump()
                else:
                    reward = next(
                        (i for i in game.items if i.id == f"item-{goal.id}" and i.alive), None
                    )
                    if reward is not None:
                        reason = f"coleta-{reward.kind}"
                        steer(inp, reward.x + reward.w / 2 + reward.vx * 0.1)
                    else:
                        goal = None
                        collecting = False

            ahead = p.x + p.w
            floor_ahead = any(
                s.alive
                and (s.kind != "hidden" or s.used)
                and ahead + 18 >= s.x
                and ahead + 18 <= s.x + s.w
                and s.y >= p.y + p.h - 8
                and s.y <= p.y + p.h + 80
                for s in game.platforms
            )
            wall = any(
                s.alive
                and (s.kind != "hidden" or s.used)
                and s.x >= ahead - 2
                and s.x < ahead + 64
                and s.y < p.y + p.h - 3
                and s.y + s.h > p.y
                for s in game.platforms
            )
            enemy_ahead = any(
                e.alive
                and e.kind != "boss"
                and e.x + e.w > p.x
                and e.x < ahead + 120
                and e.y < p.y + p.h + 16
                and e.y + e.h > p.y - 8
                for e in game.enemies
            )

            def hazard_x(h: object) -> float:
                if h.kind == "moving":  # type: ignore[attr-defined]
                    return h.x + math.sin(
                        game.elapsed * (h.speed if h.speed is not None else 1)
                    ) * (h.range if h.range is not None else 30)  # type: ignore[attr-defined]
                return h.x  # type: ignore[attr-defined]

            danger_ahead = any(
                hazard_x(h) + h.w > p.x
                and hazard_x(h) < ahead + 90
                and h.y < p.y + p.h
                and h.y + h.h > p.y
                for h in level.hazards
            )
            incoming = any(
                s.hostile
                and s.vx < 0
                and s.x > ahead
                and s.x < ahead + 160
                and s.y + s.h > p.y
                and s.y < p.y + p.h
                for s in game.projectiles
            )
            collecting_shot = goal is not None and any(
                s.hostile
                and s.vx < 0
                and s.x > ahead
                and s.x < ahead + 42
                and s.y + s.h > p.y
                and s.y < p.y + p.h
                for s in game.projectiles
            )
            if collecting_shot and p.grounded:
                jump()
            if (
                p.grounded
                and (wall or not floor_ahead or enemy_ahead or danger_ahead or incoming)
                and goal is None
            ):
                if wall:
                    reason = "obstáculo"
                elif not floor_ahead:
                    reason = "vão"
                elif enemy_ahead:
                    reason = "inimigo"
                elif danger_ahead:
                    reason = "perigo"
                else:
                    reason = "projétil"
                jump_run = running and not wall and not danger_ahead
                jump()
            if state["jump_hold"] > 0 and goal is None:
                inp.run = jump_run

        inp.jump = state["jump_hold"] > 0 or (boss_mode and boss is not None and not p.grounded)
        if (
            smart_air
            and not boss_mode
            and goal is None
            and not p.grounded
            and game.status == "playing"
        ):
            _plan_landing(game, inp, state["jump_hold"], jump_run, plan, ticks)
        nearby = [
            [_js_round(s.x), _js_round(s.y)]
            for s in game.projectiles
            if s.hostile and abs(s.x - p.x) < 180
        ]
        before = f"{ticks / 120}s ({_js_round(p.x)},{_js_round(p.y)}) {p.power} {reason} {json.dumps(nearby, separators=(',', ':'))}"
        if record_inputs:
            inputs.append(input_mask(inp))
        game.update(STEP, inp)
        for event in game.events[event_cursor:]:
            if event.type == "death":
                deaths += 1
                incidents.append(before)
            if event.type == "power":
                powers += 1
            if event.type == "stomp" and boss_mode:
                boss_hits += 1
        event_cursor = len(game.events)
        if ticks % 120 == 0:
            samples.append(
                RouteSample(
                    second=ticks / 120,
                    x=_js_round(game.player.x),
                    y=_js_round(game.player.y),
                    lives=game.lives,
                    power=game.player.power,
                    reason=reason,
                    boss=f"{boss.health}/{boss.state}/{_js_round(boss.x)}"
                    if boss is not None
                    else None,
                )
            )
        ticks += 1
    return RouteResult(game, samples, ticks, deaths, powers, boss_hits, incidents, inputs)


def _fight_boss(game: Game, boss: Enemy, inp: InputState, steer: object, jump: object) -> None:
    p = game.player
    center = boss.x + boss.w / 2
    inp.run = False
    if not p.grounded:
        steer(inp, center + boss.vx * 0.13)  # type: ignore[operator]
        return
    # Approach from outside the hitbox, then jump into a vulnerable window.
    side = -1 if p.x + p.w / 2 < center else 1
    launch = center + side * 125
    steer(inp, launch)  # type: ignore[operator]
    if abs(p.x + p.w / 2 - launch) < 20 and boss.state == "shell" and boss.hit_timer < 0.1:
        steer(inp, center)  # type: ignore[operator]
        jump(0.74)  # type: ignore[operator]


def _shadow(game: Game) -> Game:
    """Cópia rasa do jogo com entidades mutáveis duplicadas: a "imaginação" do condutor."""
    g = copy.copy(game)
    g.player = copy.copy(game.player)
    g.platforms = [copy.copy(s) for s in game.platforms]
    g.enemies = [copy.copy(e) for e in game.enemies]
    g.items = [copy.copy(i) for i in game.items]
    g.projectiles = [copy.copy(s) for s in game.projectiles]
    g.particles = []
    g.events = []
    g.camera = copy.copy(game.camera)
    return g


def _policy_input(policy: str, t: float, remaining_hold: float, jump_run: bool) -> InputState:
    jump = t < remaining_hold
    if policy == "A":
        return InputState(right=True, run=jump_run, jump=jump)
    if policy == "B":
        return InputState(right=True, run=True, jump=jump)
    if policy == "C":
        return InputState(right=True, run=False, jump=jump)
    if policy == "D":
        return InputState(left=t < 0.25, right=t >= 0.25, run=False, jump=jump)
    return InputState(left=True, run=False, jump=jump)


def _simulate(
    game: Game, policy: str, remaining_hold: float, jump_run: bool, horizon: float = 1.3
) -> bool:
    shadow = _shadow(game)
    steps = int(horizon * 120)
    for i in range(steps):
        shadow.update(STEP, _policy_input(policy, i * STEP, remaining_hold, jump_run))
        if shadow.status != "playing":
            return False
        if shadow.player.grounded:
            return True
    return False


def _plan_landing(
    game: Game,
    inp: InputState,
    remaining_hold: float,
    jump_run: bool,
    plan: dict[str, object],
    tick: int,
) -> None:
    """Replaneja a cada 6 ticks: se seguir em frente leva à morte, tenta acelerar, soltar a corrida ou frear."""
    chosen = plan.get("policy")
    since = tick - int(plan.get("tick", -99))
    if chosen is None or since >= 6:
        chosen = "A"
        if not _simulate(game, "A", remaining_hold, jump_run):
            for policy in ("B", "C", "D", "E"):
                if _simulate(game, policy, remaining_hold, jump_run):
                    chosen = policy
                    break
        plan["policy"] = chosen
        plan["tick"] = tick
        plan["start"] = tick if chosen != "A" else plan.get("start", tick)
    if chosen == "A":
        return
    t = (tick - int(plan.get("start", tick))) * STEP
    override = _policy_input(str(chosen), t, remaining_hold, jump_run)
    inp.left, inp.right, inp.run = override.left, override.right, override.run
