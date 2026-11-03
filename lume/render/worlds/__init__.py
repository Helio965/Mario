"""World art sets. Each world defines its own terrain, background layers,
blocks, props and weather (not recolours of a single set).

Convention: a module ``lume/render/worlds/<world_id>.py`` exporting
``ART_CLASS`` (a :class:`WorldArt` subclass) is picked up automatically.
Worlds without a module fall back to :mod:`generic` (flagged provisional).
"""

from __future__ import annotations

import importlib

from .base import WorldArt


def world_art(world_id: str) -> WorldArt:
    try:
        module = importlib.import_module(f"{__name__}.{world_id}")
    except ModuleNotFoundError as exc:
        if exc.name != f"{__name__}.{world_id}":
            raise
        from .generic import GenericWorld

        return GenericWorld(world_id)
    return module.ART_CLASS()


def has_dedicated_art(world_id: str) -> bool:
    art = world_art(world_id)
    return not getattr(art, "provisional", False)
