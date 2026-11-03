"""Interface of a world art set and shared helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from ..svg import Svg


@dataclass
class Layer:
    """A parallax layer made of horizontally repeating strips (canvas units)."""

    id: str
    parallax: float  # 0 = fixed to the screen, 1 = moves with the world
    strips: list[str]  # art ids, drawn in sequence and repeated
    strip_width: float
    baseline: float  # canvas y of the strip bottom when the camera sits on the main ground
    vertical: float = 0.25  # vertical parallax factor
    drift: float = 0.0  # extra horizontal drift (canvas units/s), clouds
    foreground: bool = False


@dataclass
class Weather:
    kind: str = "none"  # leaves | petals | sand | snow | spores | embers | bubbles | ash | stars
    density: float = 0.0
    colors: tuple[str, ...] = ()
    wind: float = 0.0


@dataclass
class PropSpec:
    build: Callable[[], Svg]
    pivot: tuple[float, float]


class WorldArt:
    id = "base"
    name = ""
    accent = "#35c9b4"
    terrain_headroom = 12.0
    ambient = (255, 255, 255)  # colour modulation for world sprites (dark worlds dim them)
    vignette = 0.28
    wind_tint = (255, 236, 200)  # colour of the wind-zone streaks (sand by default)

    def sky(self) -> Svg:
        raise NotImplementedError

    def sky_extras(self) -> dict[str, PropSpec]:
        return {}

    def layers(self) -> list[Layer]:
        return []

    def layer_art(self) -> dict[str, PropSpec]:
        return {}

    def terrain(self, style: str, w: float, h: float, seed: int, left: bool, right: bool, top: bool = True, x0: float = 0.0,
                surface: str = "normal") -> Svg:
        raise NotImplementedError

    def block(self, kind: str, w: float, h: float) -> Svg:
        raise NotImplementedError

    def platform(self, kind: str, w: float, h: float, style: str = "") -> Svg:
        raise NotImplementedError

    def pipe(self, w: float, h: float, warp: bool) -> Svg:
        raise NotImplementedError

    def props(self) -> dict[str, PropSpec]:
        return {}

    def auto_decor(self, rng, surface_w: float) -> list[tuple[str, float, float, str]]:
        """Decorations placed automatically along terrain tops: (prop, dx, scale, layer)."""
        return []

    def weather(self) -> Weather:
        return Weather()

    def hazard(self, kind: str, w: float, h: float):
        """World-specific hazard art (e.g. bramble thorns); None = common art."""
        return None

    def gate(self, w: float, h: float):
        """Arena gate (switch platform with style 'gate')."""
        from ..svg import rounded_rect_path

        s = Svg(w, h)
        s.path(rounded_rect_path(0, 0, w, h, 3), fill=s.linear(0, 0, w, 0, [(0, "#5a5f68"), (0.5, "#8a909a"), (1, "#4a4e56")]),
               stroke="#2b1d2c", width=1.4)
        for i in range(1, int(w // 10)):
            s.line(i * 10, 2, i * 10, h - 2, "#3a3e46", 2.0)
        return s

    def interior(self, variant: str):
        """(backdrop Svg builder, layer Svg builder or None) for indoor areas.

        Called with every area ``variant`` of the level (plus "fortress").
        Returning a pair makes that variant indoor: the 960×540 backdrop is
        drawn instead of the sky and parallax layers, and the optional layer
        (900×420) scrolls at 0.45× behind the terrain.  Typical variants:
        "fortress", "underwater", "factory", "mansion", "sanctum".  "cave"
        always uses ``cave_sky()``.
        """
        return None

    def cave_sky(self) -> Svg:
        s = Svg(960, 540)
        s.rect(0, 0, 960, 540, fill=s.linear(0, 0, 0, 540, [(0, "#20283a"), (1, "#0e121c")]))
        return s
