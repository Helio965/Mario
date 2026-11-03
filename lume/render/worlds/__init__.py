"""World art sets. Each world defines its own terrain, background layers,
blocks, props and weather (not recolours of a single set)."""

from __future__ import annotations

from .base import WorldArt


def world_art(world_id: str) -> WorldArt:
    from . import green_kingdom, generic

    sets = {"green_kingdom": green_kingdom.GreenKingdom}
    cls = sets.get(world_id)
    if cls is None:
        return generic.GenericWorld(world_id)
    return cls()
