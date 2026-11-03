"""Rotas da campanha com o condutor que prevê o pouso, nos dois perfis de física.

* Perfil legado + previsão de pouso: as 15 fases são concluídas sem perder vidas.
* Perfil calibrado: estado real registrado — 14 fases concluídas (3-3 com uma
  vida perdida na travessia do gelo); 2-3 fica presa antes da arena e é marcada
  como falha esperada até o condutor aprender aquele trecho.

Nas fases 1-3 … 5-3 o condutor entrega o controle ao robô de justiça
(``tests/support/fairness_bot.py``) ao pisar no chão da arena, e o retoma quando
o guardião cai.
"""

from __future__ import annotations

import pytest

from game.levels.loader import load_levels
from game.physics.movement import CALIBRATED_PROFILE, LEGACY_PROFILE
from tests.gameplay.route_player import play_campaign_route

LEVELS = load_levels()


def budget(level) -> float:  # type: ignore[no-untyped-def]
    """Segundos simulados: as fases de guardião somam a travessia e um combate de três fases."""
    return 180.0 if level.stage == 3 else 100.0


CALIBRATED_PENDING = {
    "2-3": "condutor fica preso na travessia antes da arena (não chega ao guardião)",
}


@pytest.mark.gameplay
@pytest.mark.parametrize("level", LEVELS, ids=[lvl.id for lvl in LEVELS])
def test_legacy_profile_with_landing_prediction_finishes_without_deaths(level) -> None:
    route = play_campaign_route(
        level, budget(level), run=level.id != "3-2", profile=LEGACY_PROFILE, smart_air=True
    )
    assert route.game.status == "complete", route.incidents
    assert route.deaths == 0, route.incidents


@pytest.mark.gameplay
@pytest.mark.parametrize("level", LEVELS, ids=[lvl.id for lvl in LEVELS])
def test_calibrated_profile_routes(level) -> None:
    if level.id in CALIBRATED_PENDING:
        pytest.xfail(CALIBRATED_PENDING[level.id])
    route = play_campaign_route(
        level, budget(level), run=level.id != "3-2", profile=CALIBRATED_PROFILE, smart_air=True
    )
    assert route.game.status == "complete", route.incidents
    assert route.game.lives > 0
