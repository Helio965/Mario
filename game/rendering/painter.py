"""Pintor base sobre ``pygame.Surface`` (port de ``src/render/painter.ts``).

* ``Painter(surface)`` desenha com um estado de cena mutável (``frame``,
  ``camera_x``, ``camera_y``, ``world``, ``theme``, ``effects``).
* Mantém uma pilha de transformações afins equivalente a ``ctx.save /
  translate / scale / rotate / restore`` do Canvas 2D, para que os sprites
  procedurais do TypeScript sejam portados linha a linha. Um retângulo sob
  rotação vira polígono; sob escala negativa espelha.
* ``rect``, ``polygon``, ``sparkle`` e ``sprite`` reproduzem as funções do TS
  (arredondamento com ``js_round``), ``tint`` e ``hash01`` são determinísticos
  e idênticos ao original para preservar a variação visual.
* ``alpha`` global via ``set_alpha``; desenhos com alpha < 1 usam uma camada
  temporária SRCALPHA (cacheada por tamanho) composta sobre a superfície.

Convenção da matriz afim (igual ao Canvas): ``x' = a·x + c·y + e`` e
``y' = b·x + d·y + f``. Três regimes são detectados automaticamente para
manter o caminho quente barato: translação pura (``_simple``), escala sem
rotação (``_axis``) e geral (rotação → polígonos).
"""

from __future__ import annotations

import math
import re
from collections.abc import Sequence
from dataclasses import dataclass

import pygame

from game.core.jsmath import js_round
from game.core.types import Theme
from game.rendering.cache import SurfaceCache, make_surface
from game.settings import VIEW_HEIGHT, VIEW_WIDTH

WIDTH = VIEW_WIDTH
HEIGHT = VIEW_HEIGHT
INK = "#202c3e"
GOLD = "#ffd66d"

Color = tuple[int, int, int]
Transform = tuple[float, float, float, float, float, float]

# Cor visível para strings inválidas: nunca silencia um erro de paleta.
INVALID_COLOR: Color = (255, 0, 255)

_HEX6 = re.compile(r"^[a-f0-9]{6}$", re.IGNORECASE)
_floor = math.floor
_draw_polygon = pygame.draw.polygon

_color_cache: dict[str, Color] = {}
_tint_cache: dict[tuple[str, float], str] = {}


def parse_color(color: str) -> Color:
    """``"#rrggbb"`` → tupla RGB. Cores inválidas resultam em magenta visível."""
    cached = _color_cache.get(color)
    if cached is not None:
        return cached
    hex_part = color[1:] if color.startswith("#") else color
    if _HEX6.match(hex_part):
        parsed: Color = (int(hex_part[0:2], 16), int(hex_part[2:4], 16), int(hex_part[4:6], 16))
    else:
        parsed = INVALID_COLOR
    if len(_color_cache) > 4096:
        _color_cache.clear()
    _color_cache[color] = parsed
    return parsed


def tint(color: str, amount: float) -> str:
    """Mistura ``color`` com branco (``amount > 0``) ou preto (``amount < 0``), como no TS."""
    key = (color, amount)
    cached = _tint_cache.get(key)
    if cached is not None:
        return cached
    hex_part = color.replace("#", "", 1)
    if not _HEX6.match(hex_part):
        return color
    target = 255 if amount > 0 else 0
    strength = abs(amount)
    channels = []
    for offset in (0, 2, 4):
        value = int(hex_part[offset : offset + 2], 16)
        channels.append(f"{js_round(value + (target - value) * strength):02x}")
    result = "#" + "".join(channels)
    if len(_tint_cache) > 4096:
        _tint_cache.clear()
    _tint_cache[key] = result
    return result


def hash01(seed: float) -> float:
    """Pseudoaleatório determinístico em [0, 1): ``frac(sin(seed·127.1 + 311.7)·43758.5453)``."""
    number = math.sin(seed * 127.1 + 311.7) * 43758.5453
    return number - math.floor(number)


@dataclass(slots=True)
class Scene:
    frame: float = 0.0
    camera_x: float = 0.0
    camera_y: float = 0.0
    world: int = 1
    theme: Theme | None = None
    effects: bool = True


class Painter:
    """Primitivas de pixel art com transformações afins sobre uma ``Surface``."""

    def __init__(self, surface: pygame.Surface, scene: Scene | None = None) -> None:
        self._surface = surface
        self._fill = surface.fill
        self._scene = scene if scene is not None else Scene()
        # Matriz afim corrente e deslocamento inteiro pré-calculado (modo simples).
        self._a = 1.0
        self._b = 0.0
        self._c = 0.0
        self._d = 1.0
        self._e = 0.0
        self._f = 0.0
        self._ie = 0
        self._if = 0
        self._alpha = 1.0
        self._simple = True
        self._axis = True
        self._stack: list[tuple[float, float, float, float, float, float, float]] = []
        self._scratch: SurfaceCache[tuple[int, int]] = SurfaceCache(limit=192)

    # estado de cena ---------------------------------------------------------
    @property
    def surface(self) -> pygame.Surface:
        return self._surface

    @surface.setter
    def surface(self, value: pygame.Surface) -> None:
        self._surface = value
        self._fill = value.fill

    @property
    def scene(self) -> Scene:
        return self._scene

    @property
    def alpha(self) -> float:
        return self._alpha

    @property
    def transform(self) -> Transform:
        """Matriz corrente ``(a, b, c, d, e, f)``."""
        return (self._a, self._b, self._c, self._d, self._e, self._f)

    # transformações (equivalentes ao Canvas 2D) ------------------------------
    def reset(self) -> None:
        """``setTransform(1, 0, 0, 1, 0, 0)`` + alpha 1 e pilha vazia (início de quadro)."""
        self._a = 1.0
        self._b = 0.0
        self._c = 0.0
        self._d = 1.0
        self._e = 0.0
        self._f = 0.0
        self._alpha = 1.0
        self._stack.clear()
        self._classify()

    def save(self) -> None:
        self._stack.append((self._a, self._b, self._c, self._d, self._e, self._f, self._alpha))

    def restore(self) -> None:
        if not self._stack:
            return
        self._a, self._b, self._c, self._d, self._e, self._f, self._alpha = self._stack.pop()
        self._classify()

    def translate(self, dx: float, dy: float) -> None:
        self._e += self._a * dx + self._c * dy
        self._f += self._b * dx + self._d * dy
        if self._simple:
            self._ie = _floor(self._e + 0.5)
            self._if = _floor(self._f + 0.5)

    def scale(self, sx: float, sy: float) -> None:
        self._a *= sx
        self._b *= sx
        self._c *= sy
        self._d *= sy
        self._classify()

    def rotate(self, radians: float) -> None:
        cos = math.cos(radians)
        sin = math.sin(radians)
        a, b, c, d = self._a, self._b, self._c, self._d
        self._a = a * cos + c * sin
        self._b = b * cos + d * sin
        self._c = c * cos - a * sin
        self._d = d * cos - b * sin
        self._classify()

    def set_alpha(self, alpha: float) -> None:
        self._alpha = 0.0 if alpha < 0 else 1.0 if alpha > 1 else alpha

    def _classify(self) -> None:
        self._axis = self._b == 0.0 and self._c == 0.0
        self._simple = self._axis and self._a == 1.0 and self._d == 1.0
        if self._simple:
            self._ie = _floor(self._e + 0.5)
            self._if = _floor(self._f + 0.5)

    def to_device(self, x: float, y: float) -> tuple[float, float]:
        """Aplica a matriz corrente a um ponto do espaço do usuário."""
        return (self._a * x + self._c * y + self._e, self._b * x + self._d * y + self._f)

    # primitivas -----------------------------------------------------------
    def visible(self, x: float, y: float, w: float, h: float) -> bool:
        scene = self._scene
        return (
            x + w > scene.camera_x - 60
            and x < scene.camera_x + WIDTH + 60
            and y + h > scene.camera_y - 90
            and y < scene.camera_y + HEIGHT + 90
        )

    def rect(self, x: float, y: float, w: float, h: float, color: str) -> None:
        """``fillRect(round(x), round(y), round(w), round(h))`` sob a transformação corrente."""
        rx = _floor(x + 0.5)
        ry = _floor(y + 0.5)
        rw = _floor(w + 0.5)
        rh = _floor(h + 0.5)
        # Canvas normaliza larguras negativas (preenche "para trás").
        if rw < 0:
            rx += rw
            rw = -rw
        if rh < 0:
            ry += rh
            rh = -rh
        if rw == 0 or rh == 0:
            return
        rgb = _color_cache.get(color)
        if rgb is None:
            rgb = parse_color(color)
        if self._simple:
            if self._alpha >= 1.0:
                self._fill(rgb, (rx + self._ie, ry + self._if, rw, rh))
            else:
                self._alpha_rect(rx + self._ie, ry + self._if, rw, rh, rgb)
            return
        if self._axis:
            # Escala sem rotação: o retângulo continua alinhado aos eixos.
            x0 = self._a * rx + self._e
            x1 = self._a * (rx + rw) + self._e
            y0 = self._d * ry + self._f
            y1 = self._d * (ry + rh) + self._f
            if x1 < x0:
                x0, x1 = x1, x0
            if y1 < y0:
                y0, y1 = y1, y0
            left = _floor(x0 + 0.5)
            right = _floor(x1 + 0.5)
            top = _floor(y0 + 0.5)
            bottom = _floor(y1 + 0.5)
            # Traços finos (< 1 px após a escala) continuam visíveis com 1 px.
            if right <= left:
                right = left + 1
            if bottom <= top:
                bottom = top + 1
            if self._alpha >= 1.0:
                self._fill(rgb, (left, top, right - left, bottom - top))
            else:
                self._alpha_rect(left, top, right - left, bottom - top, rgb)
            return
        # Rotação: os quatro cantos viram um polígono.
        self._draw_polygon(
            self._map_points((rx, ry, rx + rw, ry, rx + rw, ry + rh, rx, ry + rh)), rgb
        )

    def polygon(self, points: Sequence[float], color: str) -> None:
        """Polígono preenchido; cada coordenada é arredondada no espaço do usuário como no TS."""
        count = len(points) - len(points) % 2
        if count < 6:
            return
        rgb = _color_cache.get(color)
        if rgb is None:
            rgb = parse_color(color)
        if self._simple:
            ie = self._ie
            jf = self._if
            device = [
                (_floor(points[i] + 0.5) + ie, _floor(points[i + 1] + 0.5) + jf)
                for i in range(0, count, 2)
            ]
        else:
            device = self._map_points(
                [_floor(points[i] + 0.5) for i in range(count)],
            )
        self._draw_polygon(device, rgb)

    def sparkle(self, x: float, y: float, radius: float, color: str) -> None:
        self.polygon(
            [
                x,
                y - radius,
                x + radius * 0.25,
                y - radius * 0.25,
                x + radius,
                y,
                x + radius * 0.25,
                y + radius * 0.25,
                x,
                y + radius,
                x - radius * 0.25,
                y + radius * 0.25,
                x - radius,
                y,
                x - radius * 0.25,
                y - radius * 0.25,
            ],
            color,
        )

    def sprite(
        self, rows: Sequence[str], palette: dict[str, str], x: float, y: float, unit: float = 1
    ) -> None:
        """Matriz de caracteres → células ``unit × unit`` coloridas pela paleta."""
        rect = self.rect
        for row_index, row in enumerate(rows):
            cell_y = y + row_index * unit
            for column, key in enumerate(row):
                color = palette.get(key)
                if color:
                    rect(x + column * unit, cell_y, unit, unit, color)

    # auxiliares -----------------------------------------------------------
    def _map_points(self, flat: Sequence[float]) -> list[tuple[int, int]]:
        """Transforma uma lista plana ``[x0, y0, x1, y1, ...]`` para pixels da superfície."""
        a, b, c, d, e, f = self._a, self._b, self._c, self._d, self._e, self._f
        return [
            (
                _floor(a * flat[i] + c * flat[i + 1] + e + 0.5),
                _floor(b * flat[i] + d * flat[i + 1] + f + 0.5),
            )
            for i in range(0, len(flat) - 1, 2)
        ]

    def _draw_polygon(self, points: list[tuple[int, int]], rgb: Color) -> None:
        if len(points) < 3:
            return
        if self._alpha >= 1.0:
            _draw_polygon(self._surface, rgb, points)
            return
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        width, height = self._surface.get_size()
        x0 = max(min(xs), 0)
        y0 = max(min(ys), 0)
        x1 = min(max(xs) + 1, width)
        y1 = min(max(ys) + 1, height)
        if x1 <= x0 or y1 <= y0:
            return
        scratch = self._scratch_surface(x1 - x0, y1 - y0)
        scratch.fill((0, 0, 0, 0))
        color = (rgb[0], rgb[1], rgb[2], int(self._alpha * 255 + 0.5))
        _draw_polygon(scratch, color, [(px - x0, py - y0) for px, py in points])
        self._surface.blit(scratch, (x0, y0))

    def _alpha_rect(self, x: int, y: int, w: int, h: int, rgb: Color) -> None:
        """Retângulo translúcido em pixels da superfície (recortado à superfície)."""
        width, height = self._surface.get_size()
        x0 = x if x > 0 else 0
        y0 = y if y > 0 else 0
        x1 = min(x + w, width)
        y1 = min(y + h, height)
        if x1 <= x0 or y1 <= y0:
            return
        scratch = self._scratch_surface(x1 - x0, y1 - y0)
        scratch.fill((rgb[0], rgb[1], rgb[2], int(self._alpha * 255 + 0.5)))
        self._surface.blit(scratch, (x0, y0))

    def _scratch_surface(self, w: int, h: int) -> pygame.Surface:
        return self._scratch.get((w, h), lambda: make_surface((w, h), alpha=True))
