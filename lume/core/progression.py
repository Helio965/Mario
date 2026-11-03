"""Achievements derived from real progress (never stored as truth)."""

from __future__ import annotations

from ..systems.save import SaveData, has_relic_mark


def achievements_for(data: SaveData, campaign) -> list[str]:
    result: list[str] = []
    if data.completed:
        result.append("first-clear")
    for world in campaign.worlds:
        ids = [e.id for e in world.entries]
        if ids and all(i in data.completed for i in ids):
            result.append(f"world-{world.id}")
    playable = [lvl.id for lvl in campaign.levels]
    if campaign.entries and all(e.id in data.completed for e in campaign.entries):
        result.append("all-clear")
    if playable and all(has_relic_mark(data, i) for i in playable) and len(playable) == len(campaign.entries):
        result.append("relic-hunter")
    if any(data.secrets.values()):
        result.append("secret-path")
    if data.migrated_from:
        result.append("legacy-traveler")
    return result
