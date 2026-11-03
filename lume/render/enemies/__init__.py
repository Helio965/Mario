"""Enemy rigs. Each species maps its behaviour's animation state to poses."""

from __future__ import annotations

from .base import CreatureRig, RIGS, rig_for  # noqa: F401
from . import green, guardians, provisional  # noqa: F401  (registration)
