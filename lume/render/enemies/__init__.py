"""Enemy rigs. Each species maps its behaviour's animation state to poses.

Every module in this package is imported automatically, so a new world's
creatures only need a new file using ``@register("<animation_set>")``.
"""

from __future__ import annotations

import importlib
import pkgutil

from .base import CreatureRig, RIGS, rig_for  # noqa: F401

for _info in pkgutil.iter_modules(__path__):
    if _info.name != "base":
        importlib.import_module(f"{__name__}.{_info.name}")
