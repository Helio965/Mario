"""Text rendered with the bundled Inter fonts (OFL) at native pixel size."""

from __future__ import annotations

from collections import OrderedDict
from pathlib import Path

import pygame

FONT_DIR = Path(__file__).resolve().parent.parent / "assets" / "fonts"
FONTS = {"display": FONT_DIR / "InterDisplay-ExtraBold.otf", "ui": FONT_DIR / "Inter-SemiBold.otf"}


class TextCache:
    def __init__(self, display, capacity: int = 256) -> None:
        if not pygame.font.get_init():
            pygame.font.init()
        self.display = display
        self.fonts: dict[tuple[str, int], pygame.font.Font] = {}
        self.cache: "OrderedDict[tuple, tuple]" = OrderedDict()
        self.capacity = capacity

    def _font(self, face: str, px: int) -> pygame.font.Font:
        key = (face, px)
        font = self.fonts.get(key)
        if font is None:
            path = FONTS.get(face, FONTS["ui"])
            font = pygame.font.Font(str(path) if path.exists() else None, px)
            self.fonts[key] = font
        return font

    def get(self, text: str, size: float, color=(255, 255, 255), face: str = "ui", outline: tuple | None = None):
        px = max(6, int(round(size * self.display.scale)))
        key = (text, px, color, face, outline, self.display.scale)
        hit = self.cache.get(key)
        if hit is not None:
            self.cache.move_to_end(key)
            return hit
        font = self._font(face, px)
        surf = font.render(text, True, color)
        if outline:
            o = max(1, px // 14)
            back = font.render(text, True, outline)
            w, h = surf.get_width() + 2 * o, surf.get_height() + 2 * o
            canvas = pygame.Surface((w, h), pygame.SRCALPHA)
            for dx in range(-o, o + 1):
                for dy in range(-o, o + 1):
                    if dx * dx + dy * dy <= o * o + 1:
                        canvas.blit(back, (o + dx, o + dy))
            canvas.blit(surf, (o, o))
            surf = canvas
        tex = self.display.texture(surf)
        entry = (tex, surf.get_width() / self.display.scale, surf.get_height() / self.display.scale)
        self.cache[key] = entry
        while len(self.cache) > self.capacity:
            self.cache.popitem(last=False)
        return entry

    def draw(self, text: str, x: float, y: float, size: float, color=(255, 255, 255), face: str = "ui", align: str = "left",
             outline: tuple | None = None, alpha: float = 1.0) -> float:
        tex, w, h = self.get(text, size, color, face, outline)
        if align == "center":
            x -= w / 2
        elif align == "right":
            x -= w
        self.display.draw(tex, x, y, w, h, alpha=alpha)
        return w
