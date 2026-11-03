"""PROVISIONAL art set for worlds whose own art set is not built yet.

It reuses the Reino Verde construction with a biome palette so legacy levels
remain playable and readable in HD. It is flagged ``provisional`` and the
quality matrix reports those levels as "arte HD provisória" — it is not the
final art of those worlds (each world must get its own shapes and props).
"""

from __future__ import annotations

from .green_kingdom import PALETTE, GreenKingdom
from .base import Weather

PALETTES = {
    "golden_desert": {
        "grass_top": "#f6d58a", "grass": "#e6b664", "grass_dark": "#b9843e", "grass_light": "#fff0c0",
        "soil_top": "#e0a868", "soil": "#c07a44", "soil_deep": "#7a4628",
        "sky": ("#5aa7e0", "#a9d6ee", "#f7e3bf", "#fbe7c4"), "sun": "#fff2c0",
        "mountain": ("#e8b98a", "#f2d2aa"), "far_hill": ("#e6c08a", "#f0d4a6"),
        "mid_hill": ("#e2b070", "#d49a5a", "#c48a4a"), "foliage": ("#a6c86a", "#6a9a4a", "#4a7a3a"),
        "near": ("#d8a05a", "#b8804a", "#9a6a3a"), "flowers": ("#fff1c0", "#f7c1a0", "#ffd27a"),
    },
    "frozen_peaks": {
        "grass_top": "#ffffff", "grass": "#e4f3fb", "grass_dark": "#a8c8de", "grass_light": "#ffffff",
        "soil_top": "#9ab2c8", "soil": "#7a8ea8", "soil_deep": "#4a5a74",
        "sky": ("#7ab4e0", "#b6daf2", "#e6f4fb", "#f2f8fc"), "sun": "#ffffff",
        "mountain": ("#c8dcef", "#e2eef8"), "far_hill": ("#d2e4f2", "#e6f0f8"),
        "mid_hill": ("#e2eef8", "#c8dcee", "#b0c8e0"), "foliage": ("#6aa8a0", "#3a7a7a", "#2a5a5e"),
        "near": ("#d8e8f4", "#b4cce0", "#98b4cc"), "flowers": ("#ffffff", "#d6ecff", "#bfe8ff"),
    },
    "enchanted_forest": {
        "grass_top": "#7ad8a0", "grass": "#3fa878", "grass_dark": "#24704e", "grass_light": "#b8f7c8",
        "soil_top": "#8a6a5a", "soil": "#6a4e44", "soil_deep": "#3a2a2a",
        "sky": ("#14243a", "#22405a", "#2e5a66", "#3a6a5e"), "sun": "#d8fff0",
        "mountain": ("#2a4a5a", "#36606a"), "far_hill": ("#2e5a5e", "#3a6a64"),
        "mid_hill": ("#2f6a5a", "#24574a", "#1c463c"), "foliage": ("#5ac88a", "#2f8a64", "#1f6448"),
        "near": ("#2a7058", "#1c5442", "#143a30"), "flowers": ("#c8fff0", "#ffe9a0", "#e0c0ff"),
    },
    "volcanic_fortress": {
        "grass_top": "#d88a6a", "grass": "#a65a48", "grass_dark": "#6a3030", "grass_light": "#ffc08a",
        "soil_top": "#6a5050", "soil": "#4a3a40", "soil_deep": "#241c22",
        "sky": ("#1e1420", "#3a1e26", "#6a2e26", "#a2482a"), "sun": "#ffb070",
        "mountain": ("#4a2e34", "#5e3a3a"), "far_hill": ("#5a3434", "#6e4038"),
        "mid_hill": ("#4e3036", "#3e262c", "#2e1c22"), "foliage": ("#8a4a3a", "#5e2e2a", "#3e1e1e"),
        "near": ("#3e2228", "#2c181e", "#1e1014"), "flowers": ("#ffb070", "#ff8a4a", "#ffd27a"),
    },
}
WEATHER = {
    "golden_desert": Weather("sand", 0.5, ("soft",), wind=90.0),
    "frozen_peaks": Weather("snow", 0.6, ("soft",), wind=25.0),
    "enchanted_forest": Weather("spores", 0.45, ("soft",), wind=8.0),
    "volcanic_fortress": Weather("embers", 0.5, ("soft",), wind=-15.0),
}


class GenericWorld(GreenKingdom):
    provisional = True

    def __init__(self, world_id: str) -> None:
        super().__init__()
        self.id = world_id
        self.c = dict(PALETTE)
        self.c.update(PALETTES.get(world_id, {}))

    def weather(self) -> Weather:
        return WEATHER.get(self.id, Weather())
