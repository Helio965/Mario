"""Every implemented level is completed by the route bot using ordinary inputs
with enemies and hazards active (port of campaign-routes.test.ts)."""

import json

import pytest

from lume.levels.campaign import load_campaign
from lume.qa.route_bot import play_route

CAMPAIGN = load_campaign()
from lume.qa.budgets import DEATH_BUDGET  # noqa: E402


@pytest.mark.parametrize("lvl", CAMPAIGN.levels, ids=lambda lvl: lvl.id)
def test_route_reaches_exit(lvl):
    snapshot = json.dumps([p.x for p in lvl.platforms])
    result = play_route(lvl, 120, run=lvl.id != "blue_ascent")
    g = result.game
    assert g.status == "complete", result.summary()
    assert g.checkpoint_reached, result.summary()
    assert not g.bosses_alive(), result.summary()
    assert g.lives > 0 and g.coins_total > 0 and result.powers > 0, result.summary()
    assert result.deaths <= DEATH_BUDGET.get(lvl.id, 0), result.summary()
    assert json.dumps([p.x for p in lvl.platforms]) == snapshot
