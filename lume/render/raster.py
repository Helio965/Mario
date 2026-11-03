"""Rasterize :class:`Svg` documents at an exact pixel size, with a disk cache.

Rasterization happens once per asset and output scale (load time), never per
frame. The disk cache (``LUME_CACHE_DIR`` or the platform cache folder) keeps
PNGs keyed by a hash of the SVG markup and size, so later launches skip the
vector rasterizer entirely.
"""

from __future__ import annotations

import hashlib
import io
import os
import sys
from pathlib import Path
from typing import Optional

import pygame

from .svg import Svg

_STATS = {"rasterized": 0, "disk_hits": 0, "pixels": 0}


def cache_dir() -> Optional[Path]:
    if os.environ.get("LUME_NO_DISK_CACHE"):
        return None
    override = os.environ.get("LUME_CACHE_DIR")
    if override:
        return Path(override)
    if sys.platform.startswith("win"):
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        return base / "Lume" / "cache"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Caches" / "Lume"
    return Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "lume"


def rasterize(svg: Svg, scale: float, *, min_px: int = 1) -> pygame.Surface:
    """Return a per-pixel-alpha Surface of ``svg`` at ``scale`` pixels per unit."""
    width = max(min_px, int(round(svg.w * scale)))
    height = max(min_px, int(round(svg.h * scale)))
    data = svg.to_bytes()
    folder = cache_dir()
    key = hashlib.sha1(data + f"|{width}x{height}|v1".encode()).hexdigest()
    if folder is not None:
        path = folder / "raster" / key[:2] / f"{key}.png"
        if path.exists():
            try:
                surface = pygame.image.load(str(path))
                _STATS["disk_hits"] += 1
                return surface
            except (pygame.error, OSError):
                pass
    surface = pygame.image.load_sized_svg(io.BytesIO(data), (width, height))
    _STATS["rasterized"] += 1
    _STATS["pixels"] += width * height
    if folder is not None:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            # unique temporary name: several processes may share the cache folder
            tmp = path.with_name(f"{path.stem}.{os.getpid()}.{id(surface):x}.tmp.png")
            pygame.image.save(surface, str(tmp))
            os.replace(tmp, path)
        except (OSError, pygame.error):
            pass
    return surface


def stats() -> dict[str, int]:
    return dict(_STATS)
