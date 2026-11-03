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
        if p.x > state.get("progress_x", -1e9) + 4 or game.status != "playing":
            state["progress_x"] = p.x
            state["stuck"] = 0.0
        else:
            state["stuck"] = state.get("stuck", 0.0) + step
        stuck = state.get("stuck", 0.0) > 1.2
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
                        and s.y + s.h <= p.y + 2  # the block must be above Lume
                        and id(s) not in state.get("skip_goal", set())
                    ),
                    None,
                )
            if goal is not None and not goal.used and not collecting:
                state["goal_time"] = state.get("goal_time", 0.0) + step
                on_top = p.standing_on == goal.id or p.y + p.h <= goal.y + 2
                if on_top or state["goal_time"] > 5.0:
                    # a person standing on the block walks off and moves on
                    goal, collecting = None, False
                    state["goal_time"] = 0.0
                    state["skip_goal"] = state.get("skip_goal", set()) | {id(game.platform_by_id.get(p.standing_on or "", None))}
            if goal is not None:
                if goal.used:
                    collecting = True
                    state["goal_time"] = 0.0
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
                for e in game.enemies if e.memory.get("family") != "emerger"
            )
            plant_out = next((e for e in game.enemies if e.alive and e.active and e.memory.get("family") == "emerger"
                              and e.state != "hidden" and e.x - (ahead) < 150 and e.x + e.w > p.x - 10
                              and abs((e.memory.get("base_y", e.y) + e.h) - (p.y + p.h)) < 40), None)
            if plant_out is not None and p.grounded and goal is None and p.power != "fire":
                # wait outside the bite until the flower retreats, then walk past
                reason = "esperando flor"
                inp.right = False
                inp.run = False
                if p.x + p.w > plant_out.x - 50:
                    inp.left = True
            danger_ahead = False
            wide_danger = False
            for h in game.hazards:
                hx, hy = h.position(game.elapsed)
                if hx + h.w > p.x and hx < ahead + 90 and hy < p.y + p.h and hy + h.h > p.y:
                    danger_ahead = True
                    wide_danger = h.w > 56 and h.kind != "moving"
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
            look = 18 + max(0.0, p.vx) * 0.14
            gap_soon = not floor_ahead or not any(
                solid(s) and s.x <= ahead + look <= s.x + s.w and p.y + p.h - 8 <= s.y <= p.y + p.h + 80
                for s in game.index.query(ahead, ahead + look + 2)
            )
            movers_ahead = gap_soon and any(
                s.motion is not None and s.alive and ahead - 40 < s.x + s.w and s.x < ahead + 420 for s in game.platforms
            )
            high_wall = wall and any(
                solid(s) and s.kind != "semisolid" and ahead - 2 <= s.x < ahead + 64 and s.y < p.y + p.h - 120
                for s in game.index.query(ahead - 2, ahead + 64)
            )
            spring = None
            if high_wall:
                spring = min((s for s in game.platforms if s.kind == "spring" and p.x - 320 < s.x < p.x + 60),
                             key=lambda s: abs(s.x - p.x), default=None)
            climb = None
            riding_now = game.platform_by_id.get(p.standing_on or "")
            climbing = state.get("climbing", False)
            if (climbing or (high_wall and spring is None and stuck)) and p.grounded and not (
                    riding_now is not None and riding_now.motion is not None):
                feet = p.y + p.h
                cx = p.x + p.w / 2
                best = None
                for c in game.platforms:
                    if not solid(c) or c.motion is not None or c.kind in ("spring",):
                        continue
                    top = c.y
                    if not (feet - 106 <= top <= feet - 24):
                        continue
                    tx = min(max(cx, c.x + 14), c.x + c.w - 14)
                    if abs(tx - cx) > 320:
                        continue
                    if best is None or top < best[0] - 1 or (abs(top - best[0]) < 1 and abs(tx - cx) < abs(best[1] - cx)):
                        best = (top, tx, c)
                if best is not None:
                    climb = best
                    state["climbing"] = True
                else:
                    state["climbing"] = False
            hole = None
            if high_wall and spring is None and climb is None and state.get("climb") is None and stuck:
                feet = p.y + p.h
                for back in range(0, 420, 8):
                    hx = p.x + p.w / 2 - back
                    # a hole has no surface from 30 u above the feet to 60 u below (steps up are not holes)
                    if _floor_below(game, hx - 12, feet - 30, 90) is None and _floor_below(game, hx + 12, feet - 30, 90) is None:
                        # only a hole with safe ground below is a route (pits in legacy levels are deadly)
                        below = _floor_below(game, hx, feet + 60, 900)
                        if below is not None and game.level.area_at(hx, below.y - 1) is not game.level.area_at(hx, feet - 1):
                            hole = hx
                        break
            if hole is not None:
                state["descend"] = (hole, p.y + p.h, 8.0)
            descend = state.get("descend")
            if descend is not None:
                hx, surface, left_t = descend
                if p.y > surface + 40 or left_t <= 0:
                    state["descend"] = None
                else:
                    state["descend"] = (hx, surface, left_t - step)
                    hole = hx
            if climb is not None and goal is None:
                state["climb"] = (climb[1], climb[0], 3.0)
            pending = state.get("climb")
            if pending is not None:
                tx, top, left_t = pending
                if (p.grounded and p.y + p.h <= top + 1) or left_t <= 0 or (p.grounded and state["climb"][2] < 1.6):
                    state["climb"] = None
                else:
                    state["climb"] = (tx, top, left_t - step)
            if state.get("climb") is not None and goal is None and hole is None:
                tx, top, _ = state["climb"]
                reason = "escalada"
                cx = p.x + p.w / 2
                under = p.grounded and abs(cx - tx) < 40
                if p.grounded:
                    steer(inp, tx)
                    inp.run = False
                    if under or abs(cx - tx) < 110:
                        jump(0.6)
                else:
                    steer(inp, tx)
            elif hole is not None and goal is None:
                reason = "toca"
                if p.grounded:
                    steer(inp, hole)
                    inp.run = False
                else:
                    inp.left = inp.right = False
                state["hold"] = 0.0
            elif spring is not None and p.grounded and goal is None and state.get("climb") is None:
                reason = "mola"
                target = spring.x + spring.w / 2
                steer(inp, target)
                if abs(p.x + p.w / 2 - target) < 34:
                    jump(0.3)
            elif p.grounded and movers_ahead and goal is None and not wall and hole is None and state.get("climb") is None:
                # wait at the edge for the moving platform, then jump when the arc lands on something solid
                landing = predict_landing(game, run=True)
                state["wait"] = state.get("wait", 0.0) + step
                if landing is not None and landing is not game.platform_by_id.get(p.standing_on or ""):
                    reason = "plataforma móvel"
                    jump_run = True
                    jump(0.6)
                    state["wait"] = 0.0
                elif state["wait"] < 6.0:
                    reason = "esperando plataforma"
                    inp.right = False
                    inp.run = False
                    if p.vx > 20:
                        inp.left = True
                else:
                    jump()
                    state["wait"] = 0.0
            elif p.grounded and (wall or not floor_ahead or enemy_ahead or danger_ahead or incoming) and goal is None and hole is None \
                    and state.get("climb") is None:
                reason = (
                    "obstáculo" if wall else "vão" if not floor_ahead else "inimigo" if enemy_ahead
                    else "perigo" if danger_ahead else "projétil"
                )
                jump_run = run and not wall and (not danger_ahead or wide_danger)
                jump()
            riding = game.platform_by_id.get(p.standing_on or "")
            if riding is not None and riding.motion is not None and goal is None:
                inp.right = False
                inp.run = False
                center = riding.x + riding.w / 2
                if abs(p.x + p.w / 2 - center) > 10:
                    steer(inp, center)
                landing = predict_landing(game, run=True)
                if landing is not None and landing is not riding and landing.x + landing.w > p.x + 40:
                    inp.right, inp.left = True, False
                    jump(0.6)
                    jump_run = True
            if state["hold"] > 0 and goal is None:
                inp.run = jump_run
            if p.swimming:
                inp.jump = int(game.elapsed * 3) % 2 == 0
        if not p.swimming or boss_mode:
            inp.jump = state["hold"] > 0 or (boss_mode and boss is not None and not p.grounded)
        in_sand = any(z.kind == "quicksand" and z.x <= p.x + p.w / 2 < z.x + z.w and z.y - 4 <= p.y + p.h <= z.y + z.h + 4
                      for z in game.zones)
        if in_sand:
            # quicksand: keep moving and hop repeatedly to climb out
            inp.right, inp.left = True, False
            inp.jump = int(game.elapsed * 6) % 2 == 0
        if p.swimming and not boss_mode:
            # swim toward the far bank: one stroke per press (release once the
            # stroke is spent) and keep holding while rising, so breaking the
            # surface with jump held hops onto the bank
            inp.right, inp.left = True, False
            inp.jump = p.vy < -40 or not game.previous_jump
            state["surfacing"] = 0.5
        elif state.get("surfacing", 0.0) > 0 and not boss_mode:
            state["surfacing"] = 0.0 if p.grounded else state["surfacing"] - step
            if p.vy < 0 and not p.grounded:
                inp.jump = True
                inp.right, inp.left = True, False
        if p.launched:
            inp.jump = True
            inp.right, inp.left = True, False
        elif not p.grounded and p.vy > 0 and not boss_mode and game.status == "playing" and not p.swimming:
            # air control: if the arc ends in a pit, steer toward a trajectory that lands
            current = 1 if inp.right else (-1 if inp.left else 0)
            if simulate_air(game, current)[1] == "pit":
                for alternative in (0, -current if current else -1, 1):
                    if alternative != current and simulate_air(game, alternative)[1] == "land":
                        inp.right, inp.left = alternative > 0, alternative < 0
                        break
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


class _Ghost:
    __slots__ = ("x", "y", "w", "h", "vx", "vy")

    def __init__(self, x, y, w, h, vx, vy):
        self.x, self.y, self.w, self.h, self.vx, self.vy = x, y, w, h, vx, vy


def predict_landing(game: Game, run: bool = True, hold: float = 0.6, horizon: float = 1.6):
    """Simulate a jump from the player's current state against the *future*
    positions of moving platforms. Returns the platform landed on, or None if
    the arc ends in a pit or hazard. Read-only: the real game is untouched."""
    import math as _m

    from ..core import constants as C
    from ..core.physics import move_body

    p = game.player
    body = _Ghost(p.x, p.y, p.w, p.h, p.vx, -C.JUMP_SPEED)
    movers = [s for s in game.platforms if s.motion is not None]
    saved = [(s, s.x, s.y) for s in movers]
    t = 0.0
    landed = None
    try:
        for i in range(int(horizon / C.FIXED_DT)):
            t += C.FIXED_DT
            for s in movers:
                m = s.motion
                ang = (game.elapsed + t) * m.speed + m.phase
                if m.axis == "circle":
                    s.x, s.y = s.start_x + _m.cos(ang) * m.range, s.start_y + _m.sin(ang) * m.range
                else:
                    wave = _m.sin(ang) * m.range
                    s.x = s.start_x + (wave if m.axis == "x" else 0.0)
                    s.y = s.start_y + (wave if m.axis == "y" else 0.0)
            target = C.RUN_SPEED if run else C.WALK_SPEED
            body.vx = min(target, body.vx + C.AIR_ACCEL * C.FIXED_DT)
            if t > hold and body.vy < C.JUMP_CUT_SPEED:
                body.vy = C.JUMP_CUT_SPEED
            body.vy = min(C.MAX_FALL_SPEED, body.vy + C.GRAVITY * C.FIXED_DT)
            hit = move_body(body, game.index, C.FIXED_DT)
            for h in game.hazards:
                hx, hy = h.position(game.elapsed + t)
                if body.x < hx + h.w and body.x + body.w > hx and body.y < hy + h.h and body.y + body.h > hy:
                    return None
            if hit.grounded and t > 0.05:
                landed = hit.standing_on
                break
            if body.y > game.level.height or body.y > p.y + 420:
                break
    finally:
        for s, x, y in saved:
            s.x, s.y = x, y
    return landed


def _fight_boar(game: Game, boss: Enemy, inp: InputState, steer, jump) -> None:
    """Keep distance, jump over charges, stomp only while it is dizzy, then back off."""
    p = game.player
    center = boss.x + boss.w / 2
    pc = p.x + p.w / 2
    left, right = boss.patrol
    middle = (left + right) / 2
    state = boss.state
    if not p.grounded:
        if state == "stunned":
            steer(inp, center)
        elif state in ("hurt", "recover"):
            steer(inp, middle + (180 if center < middle else -180))
        else:
            steer(inp, pc + (60 if center < pc else -60))
        return
    if state == "stunned":
        side = 1 if center < middle else -1  # approach from the open side (away from the wall)
        launch = center + side * 95
        steer(inp, launch)
        if abs(pc - launch) < 24 and boss.hit_timer < 0.05:
            jump(0.7)
    elif state == "charge":
        toward = (center < pc) == (boss.facing > 0)
        if toward and abs(center - pc) < 150:
            jump(0.75)
    elif state in ("telegraph", "stalk", "intro", "dormant"):
        # stand with room to jump the charge, away from walls
        spot = middle + (140 if center < middle else -140)
        steer(inp, spot)
    else:
        steer(inp, middle + (200 if center < middle else -200))


def simulate_air(game: Game, direction: int, horizon: float = 1.4):
    """Continue the current airborne trajectory steering ``direction`` (-1/0/1).
    Returns (platform or None, outcome) with outcome land | pit | hazard | air."""
    import math as _m

    from ..core import constants as C
    from ..core.geometry import approach
    from ..core.physics import move_body

    p = game.player
    body = _Ghost(p.x, p.y, p.w, p.h, p.vx, p.vy)
    t = 0.0
    for _ in range(int(horizon / C.FIXED_DT)):
        t += C.FIXED_DT
        body.vx = approach(body.vx, direction * C.RUN_SPEED, (C.AIR_ACCEL if direction else C.AIR_DRAG) * C.FIXED_DT)
        body.vy = min(C.MAX_FALL_SPEED, body.vy + C.GRAVITY * C.FIXED_DT)
        hit = move_body(body, game.index, C.FIXED_DT)
        for h in game.hazards:
            hx, hy = h.position(game.elapsed + t)
            if body.x < hx + h.w and body.x + body.w > hx and body.y < hy + h.h and body.y + body.h > hy:
                return None, "hazard"
        if hit.grounded:
            return hit.standing_on, "land"
        area = game.level.area_at(body.x + body.w / 2, min(body.y, game.level.height - 1))
        if body.y > area.y + area.h + 60:
            return None, "pit"
    return None, "air"


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
    family = e.memory.get("family")
    if family == "emerger" and e.state == "hidden":
        # a hidden plant stays hidden while Lume is next to it: walk past
        return False
    return behavior.tangible(game, e) or family == "burrower"


def _fight_boss(game: Game, boss: Enemy, inp: InputState, steer, jump) -> None:
    p = game.player
    center = boss.x + boss.w / 2
    inp.run = False
    behavior = game.behaviors[boss.species]
    if boss.memory.get("family") == "thorn_boar":
        _fight_boar(game, boss, inp, steer, jump)
        return
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
