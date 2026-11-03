"""Keyboard and gamepad input mapped to :class:`InputState`.

Presses that start and end between two frames are latched so a quick tap of
jump/pause is never lost (same guarantee as the web edition).
"""

from __future__ import annotations

import pygame

from ..core.input import InputState

KEYS = {
    pygame.K_a: "left", pygame.K_LEFT: "left",
    pygame.K_d: "right", pygame.K_RIGHT: "right",
    pygame.K_SPACE: "jump", pygame.K_w: "jump", pygame.K_UP: "jump", pygame.K_z: "jump",
    pygame.K_LSHIFT: "run", pygame.K_RSHIFT: "run", pygame.K_x: "run",
    pygame.K_j: "ability", pygame.K_c: "ability",
    pygame.K_s: "down", pygame.K_DOWN: "down",
    pygame.K_ESCAPE: "pause", pygame.K_p: "pause",
}
MENU_KEYS = {
    pygame.K_UP: "up", pygame.K_w: "up", pygame.K_DOWN: "down", pygame.K_s: "down",
    pygame.K_LEFT: "left", pygame.K_a: "left", pygame.K_RIGHT: "right", pygame.K_d: "right",
    pygame.K_RETURN: "confirm", pygame.K_KP_ENTER: "confirm", pygame.K_SPACE: "confirm",
    pygame.K_ESCAPE: "back", pygame.K_BACKSPACE: "back",
}


class InputSystem:
    def __init__(self) -> None:
        self.held: set[str] = set()
        self.taps: set[str] = set()
        self.menu: list[str] = []
        self.pads: dict[int, object] = {}
        try:
            pygame.joystick.init()
            for i in range(pygame.joystick.get_count()):
                self._add_pad(i)
        except pygame.error:
            pass

    def _add_pad(self, index: int) -> None:
        try:
            pad = pygame.joystick.Joystick(index)
            self.pads[pad.get_instance_id()] = pad
        except pygame.error:
            pass

    def handle(self, event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key in MENU_KEYS:
                self.menu.append(MENU_KEYS[event.key])
            action = KEYS.get(event.key)
            if action and action not in self.held:
                self.held.add(action)
                if action in ("jump", "pause", "ability"):
                    self.taps.add(action)
        elif event.type == pygame.KEYUP:
            action = KEYS.get(event.key)
            if action:
                # keep the action held only if another key for it is down
                still = any(pygame.key.get_pressed()[k] for k, a in KEYS.items() if a == action and k != event.key)
                if not still:
                    self.held.discard(action)
        elif event.type == pygame.JOYDEVICEADDED:
            self._add_pad(event.device_index)
        elif event.type == pygame.JOYDEVICEREMOVED:
            self.pads.pop(event.instance_id, None)
        elif event.type == pygame.JOYBUTTONDOWN:
            mapping = {0: "confirm", 1: "back", 7: "back"}
            if event.button in mapping:
                self.menu.append(mapping[event.button])
            if event.button == 0:
                self.taps.add("jump")
            if event.button in (7, 9):
                self.taps.add("pause")
                self.menu.append("pause")
        elif event.type == pygame.JOYHATMOTION:
            x, y = event.value
            if y > 0:
                self.menu.append("up")
            elif y < 0:
                self.menu.append("down")
            if x < 0:
                self.menu.append("left")
            elif x > 0:
                self.menu.append("right")

    def clear(self) -> None:
        self.held.clear()
        self.taps.clear()
        self.menu.clear()

    def menu_actions(self) -> list[str]:
        out, self.menu = self.menu, []
        return out

    def read(self) -> InputState:
        st = InputState()
        for a in self.held | self.taps:
            if hasattr(st, a):
                setattr(st, a, True)
        st.pause_pressed = "pause" in self.taps
        self.taps.clear()
        for pad in self.pads.values():
            try:
                ax = pad.get_axis(0) if pad.get_numaxes() > 0 else 0.0
                ay = pad.get_axis(1) if pad.get_numaxes() > 1 else 0.0
                hat = pad.get_hat(0) if pad.get_numhats() > 0 else (0, 0)
                btn = lambda i: i < pad.get_numbuttons() and pad.get_button(i)  # noqa: E731
                st.left |= ax < -0.3 or hat[0] < 0
                st.right |= ax > 0.3 or hat[0] > 0
                st.jump |= bool(btn(0))
                st.run |= bool(btn(2)) or (pad.get_numaxes() > 5 and pad.get_axis(5) > 0.3)
                st.ability |= bool(btn(1))
                st.down |= ay > 0.5 or hat[1] < 0
            except pygame.error:
                continue
        return st
