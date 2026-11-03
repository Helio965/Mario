"""Port de ``progression.test.ts``: próxima fase e conquistas."""

from __future__ import annotations

from game.core.game import Game
from game.levels.loader import load_levels
from game.systems.progression import achievements_for

LEVELS = load_levels()


def test_next_level_requires_victory_and_keeps_lives_coins_score() -> None:
    g = Game()
    assert g.next() is False
    g.score = 500
    g.coins_total = 5
    g.lives = 4
    g.finish()
    score = g.score
    assert g.next() is True
    assert g.level_index == 1
    assert g.score == score
    assert g.level_start_score == score
    assert g.coins_total == 5
    assert g.lives == 4
    g.load(14)
    g.finish()
    assert g.next() is False


def test_achievements_derive_from_completed_levels_and_relics() -> None:
    assert achievements_for([], [], LEVELS) == []
    assert achievements_for(["1-1"], [], LEVELS) == ["first-clear"]
    assert "world-1" in achievements_for(["1-1", "1-2", "1-3"], [], LEVELS)
    ids = [lvl.id for lvl in LEVELS]
    achievements = achievements_for(ids, ids, LEVELS)
    assert "all-clear" in achievements
    assert "relic-hunter" in achievements
    assert len(achievements) == 8
