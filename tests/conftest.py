"""Fixtures compartilhadas dos testes."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

# Testes nunca abrem janela nem dispositivo de áudio.
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "tests" / "fixtures"


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    return FIXTURES
