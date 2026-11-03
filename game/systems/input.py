"""Entrada: teclado (remapeável), gamepad e latch de toques (substitui ``input.ts``).

Pressionamentos curtos de pulo, pausa e habilidade entre dois quadros não se
perdem: ``handle_event`` registra o toque e ``read`` o entrega uma vez.
"""

from __future__ import annotations

import contextlib
from collections.abc import Mapping

import pygame

from game.core.types import InputState
from game.systems.save import ACTIONS, DEFAULT_BINDINGS

TAP_ACTIONS = frozenset({"jump", "pause", "ability"})
AXIS_DEADZONE = 0.3
AXIS_DOWN = 0.5

# Índices de botões no layout mais comum (Xbox/SDL); também aceitamos o
# mapeamento alternativo de "start" para controles que usam 9.
JOY_BUTTONS: dict[str, tuple[int, ...]] = {
    "jump": (0,),
    "ability": (1,),
    "run": (2, 5, 7),
    "pause": (7, 9, 6),
}


def key_code(name: str) -> int | None:
    """Nome de tecla (``pygame.key.name``) → código; ``None`` se desconhecido."""
    try:
        code = pygame.key.key_code(name)
    except (ValueError, pygame.error):
        return None
    return int(code) if code else None


class Input:
    def __init__(
        self, bindings: Mapping[str, list[str]] | None = None, joysticks: bool = True
    ) -> None:
        self._held: set[int] = set()
        self._taps: set[str] = set()
        self._key_to_action: dict[int, str] = {}
        self._joy_axes: dict[int, float] = {}
        self._joy_hat: tuple[int, int] = (0, 0)
        self._joy_buttons: set[int] = set()
        self._joysticks: list[pygame.joystick.JoystickType] = []
        self.set_bindings(bindings or DEFAULT_BINDINGS)
        if joysticks:
            self.init_joysticks()

    # ----------------------------------------------------------- configuração
    def set_bindings(self, bindings: Mapping[str, list[str]]) -> None:
        self._key_to_action = {}
        for action in ACTIONS:
            for name in bindings.get(action, DEFAULT_BINDINGS[action]):
                code = key_code(name)
                if code is not None:
                    self._key_to_action[code] = action

    def init_joysticks(self) -> None:
        with contextlib.suppress(pygame.error):
            if not pygame.joystick.get_init():
                pygame.joystick.init()
            self._joysticks = [
                pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())
            ]

    # --------------------------------------------------------------- eventos
    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            action = self._key_to_action.get(event.key)
            if action is None:
                return
            if event.key not in self._held:
                self._held.add(event.key)
                if action in TAP_ACTIONS:
                    self._taps.add(action)
        elif event.type == pygame.KEYUP:
            self._held.discard(event.key)
        elif event.type == pygame.JOYAXISMOTION:
            self._joy_axes[event.axis] = event.value
        elif event.type == pygame.JOYHATMOTION:
            self._joy_hat = (int(event.value[0]), int(event.value[1]))
            if event.value[1] > 0:
                self._taps.add("jump")
        elif event.type == pygame.JOYBUTTONDOWN:
            self._joy_buttons.add(event.button)
            for action, buttons in JOY_BUTTONS.items():
                if event.button in buttons and action in TAP_ACTIONS:
                    self._taps.add(action)
        elif event.type == pygame.JOYBUTTONUP:
            self._joy_buttons.discard(event.button)
        elif event.type in (pygame.JOYDEVICEADDED, pygame.JOYDEVICEREMOVED):
            self.init_joysticks()

    def clear(self) -> None:
        self._held.clear()
        self._taps.clear()
        self._joy_axes.clear()
        self._joy_hat = (0, 0)
        self._joy_buttons.clear()

    # ---------------------------------------------------------------- leitura
    def read(self) -> InputState:
        state = InputState()
        for code in self._held:
            action = self._key_to_action.get(code)
            if action is not None:
                setattr(state, action, True)
        state.pause_pressed = "pause" in self._taps
        # Keep a complete press/release between frames for one sample.
        for action in self._taps:
            setattr(state, action, True)
        self._taps.clear()
        axis_x = self._joy_axes.get(0, 0.0)
        axis_y = self._joy_axes.get(1, 0.0)
        hat_x, hat_y = self._joy_hat
        state.left = state.left or axis_x < -AXIS_DEADZONE or hat_x < 0
        state.right = state.right or axis_x > AXIS_DEADZONE or hat_x > 0
        state.jump = (
            state.jump or any(b in self._joy_buttons for b in JOY_BUTTONS["jump"]) or hat_y > 0
        )
        state.run = state.run or any(b in self._joy_buttons for b in JOY_BUTTONS["run"])
        state.ability = state.ability or any(b in self._joy_buttons for b in JOY_BUTTONS["ability"])
        state.down = state.down or axis_y > AXIS_DOWN or hat_y < 0
        state.pause = state.pause or any(b in self._joy_buttons for b in JOY_BUTTONS["pause"])
        return state
