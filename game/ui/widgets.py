"""Widgets e gerenciamento de foco da interface.

* ``Widget`` e derivados (``Button``, ``Slider``, ``Toggle``, ``Selector``,
  ``BindingRow``) guardam retângulos em coordenadas do conteúdo da tela e
  desenham o próprio estado (valor, foco, passagem do mouse).
* ``Layer`` grava desenhos estáticos (textos, caixas, ícones) e os rasteriza
  uma única vez numa superfície SRCALPHA reutilizada a cada quadro.
* ``WidgetGroup`` gerencia foco (navegação espacial por setas, Tab cíclico),
  rolagem do conteúdo, passagem do mouse, cliques, arrasto e a barra de
  rolagem. Coordenadas de tela = conteúdo + ``origin`` (janela − rolagem).
"""

from __future__ import annotations

import math
from collections.abc import Callable
from typing import Literal

import pygame

from game.settings import VIEW_HEIGHT, VIEW_WIDTH
from game.ui.theme import RGB, Style, mix

Direction = Literal["up", "down", "left", "right"]
ButtonKind = Literal["primary", "secondary", "text", "danger", "link", "close"]
Anchor = Literal[
    "topleft", "topright", "midtop", "midleft", "midright", "center", "bottomleft", "bottomright"
]
Op = Callable[[pygame.Surface], None]

SCROLL_STEP = 48


class Widget:
    """Elemento interativo; ``rect`` em coordenadas do conteúdo."""

    focusable: bool = True

    def __init__(
        self,
        rect: pygame.Rect,
        on_activate: Callable[[], None] | None = None,
        *,
        widget_id: str = "",
        enabled: bool = True,
    ) -> None:
        self.rect = pygame.Rect(rect)
        self.on_activate = on_activate
        self.id = widget_id
        self.enabled = enabled

    def activate(self) -> None:
        if self.enabled and self.on_activate is not None:
            self.on_activate()

    def nav(self, direction: Direction) -> bool:
        """Trata uma seta com o foco neste widget; ``True`` quando consumida."""
        return False

    def press(self, x: int, y: int) -> None:
        """Clique em coordenadas locais do widget."""
        self.activate()

    def drag(self, x: int, y: int) -> None:
        """Arrasto com o botão pressionado (coordenadas locais)."""

    def release(self) -> None:
        """Botão do mouse solto."""

    def draw(
        self,
        surface: pygame.Surface,
        style: Style,
        origin: tuple[int, int],
        focused: bool,
        hovered: bool,
    ) -> None:
        raise NotImplementedError


class Button(Widget):
    """Botão com rótulo, subtítulo opcional e ícones à esquerda/direita."""

    def __init__(
        self,
        rect: pygame.Rect,
        label: str,
        on_activate: Callable[[], None] | None = None,
        *,
        kind: ButtonKind = "primary",
        icon: str | None = None,
        trailing: str | None = None,
        sublabel: str | None = None,
        size: int = 12,
        bold: bool = True,
        spacing: int = 0,
        align: Literal["left", "center"] = "center",
        widget_id: str = "",
        enabled: bool = True,
    ) -> None:
        super().__init__(rect, on_activate, widget_id=widget_id, enabled=enabled)
        self.label = label
        self.kind: ButtonKind = kind
        self.icon = icon
        self.trailing = trailing
        self.sublabel = sublabel
        self.size = size
        self.bold = bold
        self.spacing = spacing
        self.align = align

    def _colors(self, style: Style, active: bool) -> RGB:
        p = style.palette
        if self.kind == "primary":
            return p.primary_text
        if self.kind == "secondary":
            return p.secondary_text
        if self.kind == "danger":
            return p.danger
        if self.kind == "text":
            return p.link_hover if active else p.text_button
        if self.kind == "close":
            return p.text_button
        return p.link_hover if active else p.link

    def draw(
        self,
        surface: pygame.Surface,
        style: Style,
        origin: tuple[int, int],
        focused: bool,
        hovered: bool,
    ) -> None:
        p = style.palette
        r = self.rect.move(origin)
        active = (focused or hovered) and self.enabled
        radius = 6
        if self.kind == "primary":
            style.round_rect(surface, r.move(0, 4), p.primary_shadow, radius)
            style.round_rect(surface, r, p.primary_hover if active else p.primary, radius)
        elif self.kind == "secondary":
            fill = p.secondary_hover if active else p.secondary
            style.round_rect(surface, r, fill, radius, border=p.secondary_border)
        elif self.kind == "danger":
            fill = mix(p.danger_bg, p.danger_border, 0.4) if active else p.danger_bg
            style.round_rect(surface, r, fill, radius, border=p.danger_border)
        elif self.kind == "text":
            if active:
                style.round_rect(surface, r, p.text_button_hover, radius)
        elif self.kind == "close":
            radius = 5
            style.round_rect(surface, r, p.secondary_hover if active else p.secondary, radius)
        color = self._colors(style, active)
        if not self.enabled:
            color = mix(color, p.panel, 0.5)
        label = style.text(self.label, self.size, color, self.bold, self.spacing)
        sub = (
            style.text(
                self.sublabel,
                max(8, self.size - 3),
                p.primary_sub if self.kind == "primary" else p.note,
            )
            if self.sublabel
            else None
        )
        icon_size = self.size + 6 if self.kind == "primary" else self.size + 4
        pad = {"primary": 16, "secondary": 14, "danger": 14, "text": 10, "close": 10}.get(
            self.kind, 0
        )
        gap = 9 if self.kind != "link" else 6
        block_w = max(label.get_width(), sub.get_width() if sub else 0)
        total = block_w + (icon_size + gap if self.icon else 0)
        x = r.x + pad if self.align == "left" else r.centerx - total // 2
        if self.icon:
            icon = style.icon(self.icon, icon_size, color)
            surface.blit(icon, (x, r.centery - icon_size // 2))
            x += icon_size + gap
        if sub is not None:
            top = r.centery - (label.get_height() + sub.get_height() + 2) // 2
            surface.blit(label, (x, top))
            surface.blit(sub, (x, top + label.get_height() + 2))
        else:
            surface.blit(label, (x, r.centery - label.get_height() // 2))
            if self.kind == "link" and active:
                y = r.centery + label.get_height() // 2 + 1
                pygame.draw.line(surface, color, (x, y), (x + label.get_width(), y))
        if self.trailing:
            icon = style.icon(self.trailing, icon_size, color)
            surface.blit(icon, (r.right - pad - icon_size, r.centery - icon_size // 2))
        if focused:
            style.focus_ring(surface, r, radius)


class Slider(Widget):
    """Controle deslizante 0–1 (setas ±5 %, clique/arrasto na trilha)."""

    def __init__(
        self,
        rect: pygame.Rect,
        label: str,
        value: float,
        on_change: Callable[[float], None],
        fmt: Callable[[float], str],
        *,
        widget_id: str = "",
        step: float = 0.05,
    ) -> None:
        super().__init__(rect, None, widget_id=widget_id)
        self.label = label
        self.value = max(0.0, min(1.0, value))
        self.on_change = on_change
        self.fmt = fmt
        self.step = step
        self._dragging = False

    def set(self, value: float) -> None:
        value = max(0.0, min(1.0, round(value * 100) / 100))
        if value != self.value:
            self.value = value
            self.on_change(value)

    def nav(self, direction: Direction) -> bool:
        if direction == "left":
            self.set(self.value - self.step)
            return True
        if direction == "right":
            self.set(self.value + self.step)
            return True
        return False

    def activate(self) -> None:
        self.set(0.0 if self.value >= 1.0 else self.value + self.step)

    def _from_x(self, x: int) -> None:
        self.set(x / max(1, self.rect.w))

    def press(self, x: int, y: int) -> None:
        self._dragging = True
        self._from_x(x)

    def drag(self, x: int, y: int) -> None:
        if self._dragging:
            self._from_x(x)

    def release(self) -> None:
        self._dragging = False

    def draw(
        self,
        surface: pygame.Surface,
        style: Style,
        origin: tuple[int, int],
        focused: bool,
        hovered: bool,
    ) -> None:
        p = style.palette
        r = self.rect.move(origin)
        label = style.text(self.label, 11, p.body)
        surface.blit(label, (r.x, r.y))
        value = style.text(self.fmt(self.value), 10, p.link)
        surface.blit(value, (r.right - value.get_width(), r.y + 1))
        track = pygame.Rect(r.x, r.bottom - 10, r.w, 7)
        style.round_rect(surface, track, p.track, 4)
        fill_w = round(track.w * self.value)
        if fill_w > 0:
            style.round_rect(
                surface, pygame.Rect(track.x, track.y, fill_w, track.h), p.track_fill, 4
            )
        knob = (track.x + fill_w, track.centery)
        pygame.draw.circle(surface, p.knob, knob, 8)
        pygame.draw.circle(
            surface, p.track_fill if (focused or hovered) else p.toggle_off, knob, 8, 2
        )
        if focused:
            style.focus_ring(surface, r, 6)


class Toggle(Widget):
    """Interruptor booleano com descrição (``\\n`` separa linhas já quebradas)."""

    SWITCH_W = 38
    SWITCH_H = 22

    def __init__(
        self,
        rect: pygame.Rect,
        label: str,
        description: str,
        value: bool,
        on_change: Callable[[bool], None],
        *,
        widget_id: str = "",
    ) -> None:
        super().__init__(rect, None, widget_id=widget_id)
        self.label = label
        self.description = description
        self.value = value
        self.on_change = on_change

    def activate(self) -> None:
        if self.enabled:
            self.value = not self.value
            self.on_change(self.value)

    def _switch(self, r: pygame.Rect) -> pygame.Rect:
        return pygame.Rect(r.right - self.SWITCH_W, r.y + 1, self.SWITCH_W, self.SWITCH_H)

    def draw(
        self,
        surface: pygame.Surface,
        style: Style,
        origin: tuple[int, int],
        focused: bool,
        hovered: bool,
    ) -> None:
        p = style.palette
        r = self.rect.move(origin)
        if hovered or focused:
            style.round_rect(surface, r.inflate(12, 8), p.text_button_hover, 6, 120)
        label = style.text(self.label, 11, p.body, True)
        surface.blit(label, (r.x, r.y + 3))
        y = r.y + 3 + label.get_height() + 4
        for line in self.description.split("\n"):
            if not line:
                continue
            text = style.text(line, 9, p.note)
            surface.blit(text, (r.x, y))
            y += text.get_height() + 2
        switch = self._switch(r)
        style.round_rect(surface, switch, p.toggle_on if self.value else p.toggle_off, 11)
        knob_x = switch.x + 11 + (self.SWITCH_W - 22 if self.value else 0)
        pygame.draw.circle(surface, p.knob, (knob_x, switch.centery), 8)
        if focused:
            style.focus_ring(surface, switch, 11)


class Selector(Widget):
    """Seletor cíclico de opções (setas ‹ ›, clique nas setas ou Enter avança)."""

    BOX_W = 170
    BOX_H = 28
    ARROW_W = 28

    def __init__(
        self,
        rect: pygame.Rect,
        label: str,
        description: str,
        options: list[str],
        index: int,
        on_change: Callable[[int], None],
        *,
        widget_id: str = "",
    ) -> None:
        super().__init__(rect, None, widget_id=widget_id)
        self.label = label
        self.description = description
        self.options = list(options)
        self.index = max(0, min(index, len(self.options) - 1))
        self.on_change = on_change

    def step(self, delta: int) -> None:
        if not self.options or not self.enabled:
            return
        index = (self.index + delta) % len(self.options)
        if index != self.index:
            self.index = index
            self.on_change(index)

    def nav(self, direction: Direction) -> bool:
        if direction == "left":
            self.step(-1)
            return True
        if direction == "right":
            self.step(1)
            return True
        return False

    def activate(self) -> None:
        self.step(1)

    def _box_local(self) -> pygame.Rect:
        return pygame.Rect(self.rect.w - self.BOX_W, 0, self.BOX_W, self.BOX_H)

    def press(self, x: int, y: int) -> None:
        box = self._box_local()
        if box.collidepoint(x, y) and x < box.x + self.ARROW_W:
            self.step(-1)
        else:
            self.step(1)

    def draw(
        self,
        surface: pygame.Surface,
        style: Style,
        origin: tuple[int, int],
        focused: bool,
        hovered: bool,
    ) -> None:
        p = style.palette
        r = self.rect.move(origin)
        if hovered or focused:
            style.round_rect(surface, r.inflate(12, 8), p.text_button_hover, 6, 120)
        label = style.text(self.label, 11, p.body, True)
        surface.blit(label, (r.x, r.y + 3))
        y = r.y + 3 + label.get_height() + 4
        for line in self.description.split("\n"):
            if not line:
                continue
            text = style.text(line, 9, p.note)
            surface.blit(text, (r.x, y))
            y += text.get_height() + 2
        box = self._box_local().move(r.topleft)
        active = focused or hovered
        style.round_rect(
            surface, box, p.secondary_hover if active else p.secondary, 6, border=p.secondary_border
        )
        chevron = 14
        left = style.icon("chevron_left", chevron, p.link)
        right = style.icon("chevron_right", chevron, p.link)
        surface.blit(left, (box.x + 7, box.centery - chevron // 2))
        surface.blit(right, (box.right - 7 - chevron, box.centery - chevron // 2))
        if self.options:
            text = style.text(self.options[self.index], 10, p.ink, True)
            surface.blit(
                text, (box.centerx - text.get_width() // 2, box.centery - text.get_height() // 2)
            )
        if focused:
            style.focus_ring(surface, box, 6)


class BindingRow(Widget):
    """Linha de atalho: ação à esquerda, teclas (chips) à direita; captura ao ativar."""

    def __init__(
        self,
        rect: pygame.Rect,
        label: str,
        keys: list[str],
        on_activate: Callable[[], None],
        *,
        capturing: bool = False,
        prompt: str = "",
        hint: str = "",
        widget_id: str = "",
    ) -> None:
        super().__init__(rect, on_activate, widget_id=widget_id)
        self.label = label
        self.keys = list(keys)
        self.capturing = capturing
        self.prompt = prompt
        self.hint = hint

    def draw(
        self,
        surface: pygame.Surface,
        style: Style,
        origin: tuple[int, int],
        focused: bool,
        hovered: bool,
    ) -> None:
        p = style.palette
        r = self.rect.move(origin)
        if self.capturing:
            style.round_rect(surface, r, p.confirm_bg, 5, border=p.focus)
        elif hovered or focused:
            style.round_rect(surface, r, p.text_button_hover, 5)
        label = style.text(self.label, 11, p.body)
        surface.blit(label, (r.x + 10, r.centery - label.get_height() // 2))
        if self.capturing:
            prompt = style.text(self.prompt, 10, p.focus, True)
            hint = style.text(self.hint, 8, p.note)
            x = r.right - 10 - hint.get_width()
            surface.blit(hint, (x, r.centery - hint.get_height() // 2))
            x -= 10 + prompt.get_width()
            surface.blit(prompt, (x, r.centery - prompt.get_height() // 2))
        else:
            widths = [style.measure(key, 9, True, 1)[0] + 12 for key in self.keys]
            x = r.right - 10 - sum(widths) - 4 * max(0, len(widths) - 1)
            for key, width in zip(self.keys, widths, strict=True):
                style.kbd(surface, x, r.centery - 9, key)
                x += width + 4
        if focused:
            style.focus_ring(surface, r, 5)


class Layer:
    """Gravador de desenho estático rasterizado uma vez (``render``)."""

    def __init__(self, width: int, style: Style) -> None:
        self.width = max(1, width)
        self.style = style
        self._ops: list[Op] = []
        self.bottom = 0

    def _grow(self, y: int) -> None:
        self.bottom = max(self.bottom, y)

    def text(
        self,
        x: int,
        y: int,
        text: str,
        size: int,
        color: RGB,
        *,
        bold: bool = False,
        spacing: int = 0,
        anchor: Anchor = "topleft",
    ) -> pygame.Rect:
        surface = self.style.text(text, size, color, bold, spacing)
        rect = surface.get_rect(**{anchor: (x, y)})
        pos = rect.topleft

        def op(target: pygame.Surface) -> None:
            target.blit(surface, pos)

        self._ops.append(op)
        self._grow(rect.bottom)
        return rect

    def paragraph(
        self,
        x: int,
        y: int,
        text: str,
        size: int,
        color: RGB,
        max_width: int,
        *,
        line_height: int = 0,
        bold: bool = False,
        align: Literal["left", "center"] = "left",
    ) -> int:
        """Texto com quebra automática; devolve o ``y`` logo abaixo da última linha."""
        step = line_height or round(size * 1.7)
        for line in self.style.wrap(text, size, max_width, bold):
            if align == "center":
                self.text(x + max_width // 2, y, line, size, color, bold=bold, anchor="midtop")
            else:
                self.text(x, y, line, size, color, bold=bold)
            y += step
        return y

    def box(
        self,
        rect: pygame.Rect,
        color: RGB,
        *,
        radius: int = 0,
        alpha: int = 255,
        border: RGB | None = None,
        width: int = 1,
    ) -> None:
        rect = pygame.Rect(rect)

        def op(target: pygame.Surface) -> None:
            self.style.round_rect(target, rect, color, radius, alpha, border, width)

        self._ops.append(op)
        self._grow(rect.bottom)

    def icon(
        self, x: int, y: int, name: str, size: int, color: RGB, anchor: Anchor = "topleft"
    ) -> pygame.Rect:
        surface = self.style.icon(name, size, color)
        rect = surface.get_rect(**{anchor: (x, y)})
        pos = rect.topleft

        def op(target: pygame.Surface) -> None:
            target.blit(surface, pos)

        self._ops.append(op)
        self._grow(rect.bottom)
        return rect

    def line(
        self, start: tuple[int, int], end: tuple[int, int], color: RGB, width: int = 1
    ) -> None:
        def op(target: pygame.Surface) -> None:
            pygame.draw.line(target, color, start, end, width)

        self._ops.append(op)
        self._grow(max(start[1], end[1]))

    def circle(self, center: tuple[int, int], radius: int, color: RGB, width: int = 0) -> None:
        def op(target: pygame.Surface) -> None:
            pygame.draw.circle(target, color, center, radius, width)

        self._ops.append(op)
        self._grow(center[1] + radius)

    def polygon(self, points: list[tuple[int, int]], color: RGB, width: int = 0) -> None:
        def op(target: pygame.Surface) -> None:
            pygame.draw.polygon(target, color, points, width)

        self._ops.append(op)
        self._grow(max(point[1] for point in points))

    def kbd(self, x: int, y: int, label: str, size: int = 9) -> pygame.Rect:
        text_w, text_h = self.style.measure(label, size, True, 1)
        rect = pygame.Rect(x, y, text_w + 12, text_h + 6)

        def op(target: pygame.Surface) -> None:
            self.style.kbd(target, x, y, label, size)

        self._ops.append(op)
        self._grow(rect.bottom + 1)
        return rect

    def clip(self, rect: pygame.Rect | None) -> None:
        """Limita os desenhos seguintes a ``rect`` (``None`` remove o recorte)."""
        area = pygame.Rect(rect) if rect is not None else None

        def op(target: pygame.Surface) -> None:
            target.set_clip(area)

        self._ops.append(op)

    def blit(self, surface: pygame.Surface, pos: tuple[int, int]) -> None:
        def op(target: pygame.Surface) -> None:
            target.blit(surface, pos)

        self._ops.append(op)
        self._grow(pos[1] + surface.get_height())

    def render(self, height: int) -> pygame.Surface:
        surface = pygame.Surface((self.width, max(1, height)), pygame.SRCALPHA)
        for op in self._ops:
            op(surface)
        return surface


class WidgetGroup:
    """Foco, rolagem e eventos de mouse de um conjunto de widgets."""

    def __init__(self) -> None:
        self.widgets: list[Widget] = []
        self.focus = -1
        self.hover = -1
        self.scroll = 0
        self.viewport = pygame.Rect(0, 0, VIEW_WIDTH, VIEW_HEIGHT)
        self.content_height = 0
        self._pressed: Widget | None = None

    # ------------------------------------------------------------ conjunto
    def add[W: Widget](self, widget: W) -> W:
        self.widgets.append(widget)
        return widget

    def clear(self) -> None:
        self.widgets = []
        self.focus = -1
        self.hover = -1
        self._pressed = None

    @property
    def origin(self) -> tuple[int, int]:
        return (self.viewport.x, self.viewport.y - self.scroll)

    @property
    def current(self) -> Widget | None:
        if 0 <= self.focus < len(self.widgets):
            return self.widgets[self.focus]
        return None

    @property
    def focused_id(self) -> str:
        current = self.current
        return current.id if current is not None else ""

    def find(self, widget_id: str) -> Widget | None:
        return next((w for w in self.widgets if w.id == widget_id), None)

    def _candidates(self) -> list[int]:
        return [i for i, w in enumerate(self.widgets) if w.enabled and w.focusable]

    # ---------------------------------------------------------------- foco
    def set_focus(self, index: int, reveal: bool = True) -> None:
        if 0 <= index < len(self.widgets):
            widget = self.widgets[index]
            if widget.enabled and widget.focusable:
                self.focus = index
                if reveal:
                    self.ensure_visible(widget)

    def focus_id(self, widget_id: str) -> bool:
        for i, widget in enumerate(self.widgets):
            if widget.id == widget_id and widget.enabled and widget.focusable:
                self.set_focus(i)
                return True
        return False

    def focus_first(self) -> None:
        candidates = self._candidates()
        self.focus = candidates[0] if candidates else -1
        self.scroll = 0

    def move(self, direction: Direction) -> bool:
        """Navegação espacial: o candidato mais próximo na direção, alinhado de preferência."""
        candidates = self._candidates()
        if not candidates:
            return False
        if self.focus not in candidates:
            self.set_focus(candidates[0])
            return True
        cur = self.widgets[self.focus].rect
        best = -1
        best_score = math.inf
        for i in candidates:
            if i == self.focus:
                continue
            r = self.widgets[i].rect
            # Distância entre bordas na direção pedida; o candidato precisa começar
            # depois da borda do widget atual (tolerância de 2 px). ``gap`` penaliza
            # desalinhamento no eixo perpendicular (0 quando há sobreposição).
            if direction == "down":
                primary = r.top - cur.bottom
                gap = max(0, r.left - cur.right, cur.left - r.right)
            elif direction == "up":
                primary = cur.top - r.bottom
                gap = max(0, r.left - cur.right, cur.left - r.right)
            elif direction == "right":
                primary = r.left - cur.right
                gap = max(0, r.top - cur.bottom, cur.top - r.bottom)
            else:
                primary = cur.left - r.right
                gap = max(0, r.top - cur.bottom, cur.top - r.bottom)
            if primary < -2:
                continue
            score = max(0, primary) + 2.5 * gap
            if score < best_score:
                best_score = score
                best = i
        if best < 0:
            if direction == "down":
                best = min(candidates, key=lambda i: self.widgets[i].rect.centery)
            elif direction == "up":
                best = max(candidates, key=lambda i: self.widgets[i].rect.centery)
            else:
                return False
        self.set_focus(best)
        return True

    def tab(self, delta: int) -> bool:
        candidates = self._candidates()
        if not candidates:
            return False
        if self.focus in candidates:
            position = (candidates.index(self.focus) + delta) % len(candidates)
        else:
            position = 0
        self.set_focus(candidates[position])
        return True

    def activate(self) -> bool:
        current = self.current
        if current is None or not current.enabled:
            return False
        current.activate()
        return True

    def nav(self, direction: Direction) -> bool:
        current = self.current
        if current is not None and current.enabled and current.nav(direction):
            return True
        return self.move(direction)

    # ------------------------------------------------------------- rolagem
    def max_scroll(self) -> int:
        return max(0, self.content_height - self.viewport.h)

    def scroll_to(self, value: int) -> None:
        self.scroll = max(0, min(self.max_scroll(), value))

    def scroll_by(self, delta: int) -> None:
        self.scroll_to(self.scroll + delta)

    def ensure_visible(self, widget: Widget) -> None:
        margin = 10
        if widget.rect.top - margin < self.scroll:
            self.scroll_to(widget.rect.top - margin)
        elif widget.rect.bottom + margin > self.scroll + self.viewport.h:
            self.scroll_to(widget.rect.bottom + margin - self.viewport.h)

    def wheel(self, steps: int) -> None:
        self.scroll_by(-steps * SCROLL_STEP)

    # --------------------------------------------------------------- mouse
    def to_content(self, pos: tuple[int, int]) -> tuple[int, int]:
        ox, oy = self.origin
        return (pos[0] - ox, pos[1] - oy)

    def widget_at(self, pos: tuple[int, int]) -> int:
        if not self.viewport.collidepoint(pos):
            return -1
        cx, cy = self.to_content(pos)
        for i in range(len(self.widgets) - 1, -1, -1):
            widget = self.widgets[i]
            if widget.enabled and widget.rect.collidepoint(cx, cy):
                return i
        return -1

    def mouse_move(self, pos: tuple[int, int], pressed: bool) -> None:
        if self._pressed is not None and pressed:
            cx, cy = self.to_content(pos)
            self._pressed.drag(cx - self._pressed.rect.x, cy - self._pressed.rect.y)
            return
        index = self.widget_at(pos)
        self.hover = index
        if index >= 0 and self.widgets[index].focusable:
            self.focus = index

    def mouse_down(self, pos: tuple[int, int]) -> bool:
        index = self.widget_at(pos)
        if index < 0:
            return False
        widget = self.widgets[index]
        if widget.focusable:
            self.focus = index
        cx, cy = self.to_content(pos)
        self._pressed = widget
        widget.press(cx - widget.rect.x, cy - widget.rect.y)
        return True

    def mouse_up(self, pos: tuple[int, int]) -> None:
        if self._pressed is not None:
            self._pressed.release()
            self._pressed = None

    # ------------------------------------------------------------- desenho
    def draw(self, surface: pygame.Surface, style: Style, layer: pygame.Surface | None) -> None:
        previous = surface.get_clip()
        surface.set_clip(self.viewport)
        ox, oy = self.origin
        if layer is not None:
            area = pygame.Rect(0, self.scroll, self.viewport.w, self.viewport.h)
            surface.blit(layer, self.viewport.topleft, area)
        for i, widget in enumerate(self.widgets):
            r = widget.rect.move(ox, oy)
            if r.bottom < self.viewport.y - 8 or r.top > self.viewport.bottom + 8:
                continue
            widget.draw(surface, style, (ox, oy), i == self.focus, i == self.hover)
        surface.set_clip(previous)
        limit = self.max_scroll()
        if limit > 0:
            p = style.palette
            track = pygame.Rect(self.viewport.right + 10, self.viewport.y, 4, self.viewport.h)
            style.round_rect(surface, track, p.track, 2)
            thumb_h = max(24, round(self.viewport.h * self.viewport.h / self.content_height))
            thumb_y = track.y + round((track.h - thumb_h) * self.scroll / limit)
            style.round_rect(surface, pygame.Rect(track.x, thumb_y, 4, thumb_h), p.muted, 2)
