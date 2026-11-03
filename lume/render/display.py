"""Window, GPU renderer and the coordinate system of the HD pipeline.

Everything is laid out on a 960 × 540 *reference canvas* (16:9). The window
can have any size: ``scale`` = physical pixels per canvas unit (2.0 at
1920×1080, 4.0 at 3840×2160) and other aspect ratios are letterboxed.
Textures are rasterized at ``scale`` (times the camera zoom for world art), so
they are drawn 1:1 on screen — nothing is rendered small and enlarged.
"""

from __future__ import annotations

import gc
import os
from dataclasses import dataclass
from typing import Optional

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
os.environ.setdefault("SDL_RENDER_SCALE_QUALITY", "1")  # bilinear texture filtering

import pygame
from pygame._sdl2 import video

CANVAS_W = 960.0
CANVAS_H = 540.0
PRESETS = {
    "1280x720": (1280, 720),
    "1600x900": (1600, 900),
    "1920x1080": (1920, 1080),
    "2560x1440": (2560, 1440),
    "3840x2160": (3840, 2160),
}


@dataclass
class DisplayInfo:
    driver: str
    accelerated: bool
    size: tuple[int, int]
    scale: float
    max_texture: int


_LINGERING: list = []  # closed displays: renderers outlive every texture made from them


class Display:
    """Owns the SDL window/renderer and converts canvas units to pixels."""

    def __init__(self, size: tuple[int, int] = (1280, 720), *, title: str = "Lume", fullscreen: bool = False,
                 vsync: bool = True, hidden: bool = False, software: bool = False) -> None:
        if not pygame.get_init():
            pygame.init()
        flags = {}
        self.window = video.Window(title, size=size, resizable=True, hidden=hidden, fullscreen_desktop=fullscreen)
        self.software = software or os.environ.get("SDL_VIDEODRIVER") == "dummy"
        accelerated = 0 if self.software else -1
        try:
            self.renderer = video.Renderer(self.window, accelerated=accelerated, vsync=vsync and not self.software)
        except Exception:  # pragma: no cover - fallback on machines without GPU drivers
            self.renderer = video.Renderer(self.window, accelerated=0, vsync=False)
            self.software = True
        self.renderer.draw_blend_mode = 1  # SDL_BLENDMODE_BLEND
        self._configure(self.window.size)
        del flags

    # ------------------------------------------------------------------ geometry
    def _configure(self, size: tuple[int, int]) -> None:
        w, h = size
        self.pixel_size = (w, h)
        self.scale = min(w / CANVAS_W, h / CANVAS_H)
        self.offset_x = (w - CANVAS_W * self.scale) / 2
        self.offset_y = (h - CANVAS_H * self.scale) / 2

    def resized(self) -> bool:
        if tuple(self.window.size) != self.pixel_size:
            self._configure(tuple(self.window.size))
            return True
        return False

    def info(self) -> DisplayInfo:
        return DisplayInfo("software" if self.software else "gpu", not self.software, self.pixel_size, self.scale, 16384)

    def to_px(self, x: float, y: float) -> tuple[float, float]:
        return self.offset_x + x * self.scale, self.offset_y + y * self.scale

    # ------------------------------------------------------------------ textures
    def texture(self, surface: pygame.Surface) -> video.Texture:
        tex = video.Texture.from_surface(self.renderer, surface)
        tex.blend_mode = 1
        return tex

    # ------------------------------------------------------------------ drawing
    def clear(self, color=(0, 0, 0)) -> None:
        self.renderer.draw_color = (*color[:3], 255)
        self.renderer.clear()

    def draw(self, tex: video.Texture, x: float, y: float, w: float, h: float, *, angle: float = 0.0,
             origin: Optional[tuple[float, float]] = None, flip_x: bool = False, flip_y: bool = False,
             alpha: float = 1.0, tint: Optional[tuple[int, int, int]] = None, additive: bool = False,
             src: Optional[tuple[float, float, float, float]] = None) -> None:
        """Draw ``tex`` into the canvas rectangle (x, y, w, h); ``origin`` in canvas units relative to it.
        ``src`` = (u0, v0, u1, v1) draws only that fraction of the texture (clipping, not squashing)."""
        s = self.scale
        dst = pygame.FRect(self.offset_x + x * s, self.offset_y + y * s, w * s, h * s)
        if src is not None:
            tw, th = tex.width, tex.height
            u0, v0, u1, v1 = src
            tex.draw(srcrect=pygame.FRect(u0 * tw, v0 * th, (u1 - u0) * tw, (v1 - v0) * th), dstrect=dst)
            return
        tex.alpha = max(0, min(255, int(alpha * 255)))
        if tint is not None:
            tex.color = tint
        if additive:
            tex.blend_mode = 2
        if angle or origin is not None:
            o = (origin[0] * s, origin[1] * s) if origin is not None else None
            tex.draw(dstrect=dst, angle=angle, origin=o, flip_x=flip_x, flip_y=flip_y)
        else:
            tex.draw(dstrect=dst, flip_x=flip_x, flip_y=flip_y)
        if tint is not None:
            tex.color = (255, 255, 255)
        if additive:
            tex.blend_mode = 1
        tex.alpha = 255

    def fill_rect(self, x: float, y: float, w: float, h: float, color, alpha: float = 1.0) -> None:
        s = self.scale
        self.renderer.draw_color = (*color[:3], int(255 * alpha))
        self.renderer.fill_rect(pygame.FRect(self.offset_x + x * s, self.offset_y + y * s, w * s, h * s))

    def letterbox(self) -> None:
        w, h = self.pixel_size
        self.renderer.draw_color = (0, 0, 0, 255)
        if self.offset_x > 0.5:
            self.renderer.fill_rect(pygame.FRect(0, 0, self.offset_x, h))
            self.renderer.fill_rect(pygame.FRect(w - self.offset_x, 0, self.offset_x + 1, h))
        if self.offset_y > 0.5:
            self.renderer.fill_rect(pygame.FRect(0, 0, w, self.offset_y))
            self.renderer.fill_rect(pygame.FRect(0, h - self.offset_y, w, self.offset_y + 1))

    def present(self) -> None:
        self.renderer.present()

    def screenshot(self) -> pygame.Surface:
        return self.renderer.to_surface()

    def close(self) -> None:
        """Hide the window; the renderer stays alive until the process exits.

        Destroying the renderer while any texture created from it is still
        referenced (an ArtStore, a scene held by a caller) makes SDL free
        those textures against a dead renderer, which corrupted memory and
        crashed later inside unrelated garbage collection. Hidden displays are
        cheap; SDL releases them at exit."""
        gc.collect()
        try:
            self.window.hide()
        except Exception:  # pragma: no cover
            pass
        _LINGERING.append(self)


def choose_resolution(setting: str, desktop: tuple[int, int]) -> tuple[int, int]:
    """Pick the window size: explicit preset, or the largest 16:9 preset that fits
    80% of the desktop ('auto'). 4K is only chosen when the desktop is 4K."""
    if setting in PRESETS:
        return PRESETS[setting]
    dw, dh = desktop
    best = PRESETS["1280x720"]
    for w, h in PRESETS.values():
        if w <= dw * 0.9 and h <= dh * 0.9:
            best = (w, h)
    return best
