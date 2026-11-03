"""O port Python reproduz os traces gravados com o motor TypeScript de referência."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.unit.golden import load_fixture, replay

GOLDEN = Path(__file__).resolve().parent.parent / "fixtures" / "golden"
FIXTURES = sorted(GOLDEN.glob("*.json"))


@pytest.mark.parametrize("path", FIXTURES, ids=[p.stem for p in FIXTURES])
def test_golden_trace(path: Path) -> None:
    fixture = load_fixture(path)
    divergences = replay(fixture)
    assert not divergences, "\n".join(str(d) for d in divergences[:10])
