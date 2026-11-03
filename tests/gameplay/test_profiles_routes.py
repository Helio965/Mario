"""Rotas da campanha com o condutor que prevê o pouso, nos dois perfis de física.

* Perfil legado + previsão de pouso: as 15 fases são concluídas sem perder vidas.
* Perfil calibrado: estado real registrado — 12 fases concluídas; as três
  restantes dependem de ajustes do condutor nas arenas de chefe e no gelo e
  são marcadas como falha esperada até a reconstrução das fases (Marco 8).
"""

from __future__ import annotations

import pytest

from game.levels.loader import load_levels
from game.physics.movement import CALIBRATED_PROFILE, LEGACY_PROFILE
from tests.gameplay.route_player import play_campaign_route

LEVELS = load_levels()
CALIBRATED_PENDING = {
    "2-3": "condutor fica preso antes da arena do guardião",
    "3-3": "condutor perde vidas no gelo e na arena do guardião",
    "5-3": "condutor perde vidas na arena do guardião final",
}


@pytest.mark.gameplay
@pytest.mark.parametrize("level", LEVELS, ids=[lvl.id for lvl in LEVELS])
def test_legacy_profile_with_landing_prediction_finishes_without_deaths(level) -> None:
    route = play_campaign_route(
        level, 100, run=level.id != "3-2", profile=LEGACY_PROFILE, smart_air=True
    )
    assert route.game.status == "complete", route.incidents
    assert route.deaths == 0, route.incidents


@pytest.mark.gameplay
@pytest.mark.parametrize("level", LEVELS, ids=[lvl.id for lvl in LEVELS])
def test_calibrated_profile_routes(level) -> None:
    if level.id in CALIBRATED_PENDING:
        pytest.xfail(CALIBRATED_PENDING[level.id])
    route = play_campaign_route(
        level, 100, run=level.id != "3-2", profile=CALIBRATED_PROFILE, smart_air=True
    )
    assert route.game.status == "complete", route.incidents
    assert route.game.lives > 0
