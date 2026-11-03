"""On-demand texture store for vector art.

Art is registered as *builders* (functions returning :class:`Svg`) grouped by
world/category. A texture is rasterized the first time it is drawn at the
current pixel density and kept in an LRU bounded by a memory budget; switching
worlds unloads the previous world's group. Nothing is loaded up front.
"""

from __future__ import annotations

import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Callable, Optional

from .raster import rasterize
from .svg import Svg


@dataclass
class ArtSpec:
    id: str
    build: Callable[[], Svg]
    unit: float = 1.0  # world units per svg unit
    pivot: tuple[float, float] = (0.0, 0.0)  # svg units
    group: str = "common"
    quality_floor: float = 1.0  # backgrounds may be rasterized at lower density on low presets


@dataclass
class TextureEntry:
    tex: object
    w: float  # svg units
    h: float
    pivot: tuple[float, float]
    unit: float
    bytes: int
    group: str


class ArtStore:
    def __init__(self, display, px_per_world: float, budget_mb: float = 768.0, background_density: float = 1.0) -> None:
        self.display = display
        self.px_per_world = px_per_world
        self.specs: dict[str, ArtSpec] = {}
        self.cache: "OrderedDict[str, TextureEntry]" = OrderedDict()
        self.budget = budget_mb * 1024 * 1024
        self.used = 0
        self.background_density = background_density
        self.stats = {"loads": 0, "evictions": 0, "load_ms": 0.0}
        self._svg_cache: dict[str, Svg] = {}

    def register(self, spec: ArtSpec) -> None:
        self.specs[spec.id] = spec

    def register_many(self, specs) -> None:
        for spec in specs:
            self.register(spec)

    def has(self, art_id: str) -> bool:
        return art_id in self.specs

    def set_density(self, px_per_world: float) -> None:
        if abs(px_per_world - self.px_per_world) > 1e-6:
            self.px_per_world = px_per_world
            self.clear()

    def clear(self, group: Optional[str] = None) -> None:
        for key in list(self.cache):
            if group is None or self.cache[key].group == group:
                self.used -= self.cache.pop(key).bytes

    def get(self, art_id: str) -> Optional[TextureEntry]:
        entry = self.cache.get(art_id)
        if entry is not None:
            self.cache.move_to_end(art_id)
            return entry
        spec = self.specs.get(art_id)
        if spec is None:
            return None
        start = time.perf_counter()
        svg = spec.build()
        density = self.px_per_world * spec.unit
        if spec.quality_floor < 1.0:
            density *= max(spec.quality_floor, self.background_density)
        surface = rasterize(svg, density)
        tex = self.display.texture(surface)
        entry = TextureEntry(tex, svg.w, svg.h, spec.pivot, spec.unit, surface.get_width() * surface.get_height() * 4, spec.group)
        self.cache[art_id] = entry
        self.used += entry.bytes
        self.stats["loads"] += 1
        self.stats["load_ms"] += (time.perf_counter() - start) * 1000
        while self.used > self.budget and len(self.cache) > 1:
            _, old = self.cache.popitem(last=False)
            self.used -= old.bytes
            self.stats["evictions"] += 1
        return entry

    def preload(self, ids) -> None:
        for art_id in ids:
            self.get(art_id)

    def rig_entry(self, art_id: str):
        """Adapter for :class:`RigDrawer`: (texture, w, h, pivot) in svg units."""
        e = self.get(art_id)
        if e is None:
            return None
        return e.tex, e.w, e.h, e.pivot
