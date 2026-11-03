"""Logical input state shared by keyboard, gamepad, tests and the route bot."""

from __future__ import annotations

from dataclasses import dataclass, replace


@dataclass(slots=True)
class InputState:
    left: bool = False
    right: bool = False
    jump: bool = False
    run: bool = False
    ability: bool = False
    down: bool = False
    pause: bool = False
    up: bool = False
    pause_pressed: bool = False

    def copy(self, **changes) -> "InputState":
        return replace(self, **changes)


EMPTY_INPUT = InputState()
