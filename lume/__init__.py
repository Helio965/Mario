"""Lume — As Dez Fronteiras.

Python edition of the original Lume platformer. The simulation in
:mod:`lume.core` is deterministic and independent of the window, so it can be
tested headlessly; :mod:`lume.render` turns it into high-definition vector art.
"""

import os as _os

_os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

__version__ = "2.0.0-dev"
