"""Enemy behaviour families. Importing this package registers all families."""

from .base import BEHAVIORS, Behavior, behavior_for  # noqa: F401
from . import ground, air, ranged, special, bosses  # noqa: F401  (registration side effects)
