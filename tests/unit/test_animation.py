"""Máquina de estados de animação: transições, retenções e camadas."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from game.characters.animation import (
    HURT_TIME,
    LAND_HARD_TIME,
    LAND_TIME,
    LOOK_AROUND_AFTER,
    AnimationController,
    AnimState,
)
from game.core.game import Game
from game.core.types import InputState
from tests.unit.helpers import STEP, level


@dataclass
class Body:
    vx: float = 0.0
    vy: float = 0.0
    grounded: bool = True
    facing: int = 1
    invulnerable: float = 0.0
    star: float = 0.0


def advance(
    controller: AnimationController, body: Body, seconds: float, direction: int = 0
) -> AnimState:
    state = controller.state
    for _ in range(round(seconds * 120)):
        state = controller.update(STEP, body, direction)
    return state


def test_idle_then_look_around_after_inactivity() -> None:
    c = AnimationController()
    body = Body()
    assert advance(c, body, 1.0) == AnimState.IDLE
    assert advance(c, body, LOOK_AROUND_AFTER) == AnimState.LOOK_AROUND
    assert c.frame >= 0


def test_walk_run_accelerate_and_decelerate() -> None:
    c = AnimationController()
    body = Body(vx=60)
    assert advance(c, body, 0.05, direction=1) == AnimState.ACCELERATE
    body.vx = 180
    assert advance(c, body, 0.3, direction=1) == AnimState.WALK
    body.vx = 330
    assert advance(c, body, 0.1, direction=1) == AnimState.RUN
    frames = {advance(c, body, 1 / 16, direction=1) and c.frame for _ in range(6)}
    assert len(frames) > 1, "a corrida alterna quadros"
    assert advance(c, body, 0.05, direction=0) == AnimState.DECELERATE
    body.vx = 0
    assert advance(c, body, 0.05) == AnimState.IDLE


def test_skid_when_input_opposes_velocity() -> None:
    c = AnimationController()
    body = Body(vx=300, facing=-1)
    advance(c, body, 0.1, direction=1)
    assert advance(c, body, 0.05, direction=-1) == AnimState.SKID
    body.vx = -100
    assert advance(c, body, 0.05, direction=-1) in (AnimState.WALK, AnimState.ACCELERATE)


def test_turn_when_changing_facing_at_low_speed() -> None:
    c = AnimationController()
    body = Body(vx=40, facing=1)
    advance(c, body, 0.2, direction=1)
    body.facing = -1
    body.vx = -30
    assert advance(c, body, STEP, direction=-1) == AnimState.TURN
    assert advance(c, body, 0.2, direction=-1) in (AnimState.WALK, AnimState.ACCELERATE)


def test_jump_prep_launch_rise_apex_fall_and_landing() -> None:
    c = AnimationController()
    body = Body()
    advance(c, body, 0.1)
    c.notify("jump")
    assert advance(c, body, STEP) == AnimState.JUMP_PREP
    body.grounded = False
    body.vy = -590
    assert advance(c, body, 0.06) == AnimState.JUMP_LAUNCH
    assert advance(c, body, 0.1) == AnimState.RISE
    assert c.squash_y > 1.0 or c.squash_x < 1.0
    body.vy = 0
    assert advance(c, body, 0.05) == AnimState.APEX
    body.vy = 300
    assert advance(c, body, 0.05) == AnimState.FALL
    body.grounded = True
    body.vy = 0
    assert advance(c, body, STEP) == AnimState.LAND
    assert c.squash_y < 1.0
    assert advance(c, body, LAND_TIME + 0.02) == AnimState.IDLE


def test_hard_landing_from_terminal_velocity() -> None:
    c = AnimationController()
    body = Body(grounded=False, vy=850)
    advance(c, body, 0.1)
    body.grounded = True
    body.vy = 0
    assert advance(c, body, STEP) == AnimState.LAND_HARD
    assert advance(c, body, LAND_HARD_TIME - 0.05) == AnimState.LAND_HARD
    assert advance(c, body, 0.1) == AnimState.IDLE


def test_hurt_attack_transform_win_dead_and_pipe() -> None:
    c = AnimationController()
    body = Body()
    c.notify("hurt")
    assert advance(c, body, STEP) == AnimState.HURT
    assert advance(c, body, HURT_TIME) == AnimState.IDLE
    c.notify("shot")
    assert advance(c, body, STEP) == AnimState.ATTACK
    advance(c, body, 0.3)
    c.notify("power", power_changed=True)
    assert advance(c, body, STEP) == AnimState.TRANSFORM
    advance(c, body, 0.6)
    c.notify("secret")
    assert advance(c, body, STEP) == AnimState.PIPE_ENTER
    assert advance(c, body, 0.36) == AnimState.PIPE_EXIT
    assert advance(c, body, 0.4) == AnimState.IDLE
    c.notify("complete")
    assert advance(c, body, 2.0) == AnimState.WIN
    assert not c.clips[AnimState.WIN].loop
    d = AnimationController()
    d.notify("death")
    assert advance(d, body, 5.0) == AnimState.DEAD


def test_overlays_blink_flicker_and_star() -> None:
    c = AnimationController()
    body = Body(invulnerable=1.0)
    seen_flicker = set()
    for _ in range(30):
        c.update(STEP, body)
        seen_flicker.add(c.overlays.invincible_flicker)
    assert seen_flicker == {True, False}
    body.invulnerable = 0
    body.star = 5
    c.update(STEP, body)
    assert c.overlays.star_aura
    assert not c.overlays.invincible_flicker
    body.star = 0
    blinked = False
    for _ in range(4 * 120):
        c.update(STEP, body)
        blinked = blinked or c.overlays.blink
    assert blinked


def test_swim_and_crouch_and_talk() -> None:
    c = AnimationController()
    body = Body(grounded=False, vy=100)
    c.set_underwater(True)
    assert advance(c, body, 0.1) == AnimState.SWIM
    c.set_underwater(False)
    body.grounded = True
    body.vy = 0
    advance(c, body, 0.2)
    c.set_crouching(True)
    assert advance(c, body, 0.1) == AnimState.CROUCH
    c.set_crouching(False)
    c.notify("talk")
    assert advance(c, body, 1.0) == AnimState.TALK
    c.notify("talk_end")
    assert advance(c, body, 0.1) == AnimState.IDLE


@pytest.mark.parametrize("hold", [0.02, 0.5])
def test_driven_by_real_simulation(hold: float) -> None:
    """A máquina acompanha a física real: salto curto e longo passam pelos mesmos estados."""
    g = Game([level()])
    c = AnimationController()
    seen: list[AnimState] = []
    cursor = 0
    for i in range(240):
        state = InputState(jump=i / 120 < hold)
        g.update(STEP, state)
        for event in g.events[cursor:]:
            c.notify(event.type)
        cursor = len(g.events)
        s = c.update(STEP, g.player, int(state.right) - int(state.left))
        if not seen or seen[-1] != s:
            seen.append(s)
    assert AnimState.JUMP_PREP in seen
    after_jump = seen[seen.index(AnimState.JUMP_PREP) :]
    assert after_jump[:2] == [AnimState.JUMP_PREP, AnimState.JUMP_LAUNCH]
    # O salto curto (toque) já está perto do ápice quando a pose de impulso termina.
    assert after_jump[2] in (AnimState.RISE, AnimState.APEX)
    assert AnimState.FALL in after_jump
    assert AnimState.LAND in after_jump
    assert seen[-1] in (AnimState.IDLE, AnimState.LAND)
