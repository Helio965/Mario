"""Renderização headless (SDL dummy): fases, cenários do menu, qualidade e desempenho.

Nenhum teste abre janela: ``tests/conftest.py`` define os drivers dummy e as
superfícies são ``pygame.Surface`` comuns de 960 × 540.
"""

from __future__ import annotations

import math
import time
from dataclasses import replace

import numpy as np
import pygame
import pytest

from game.core.game import Game
from game.core.types import InputState, Level
from game.enemies.registry import is_boss_kind
from game.levels.loader import THEMES, level_from_dict, load_levels
from game.rendering.painter import HEIGHT, WIDTH, Painter, Scene, hash01, parse_color, tint
from game.rendering.renderer import QUALITY_PRESETS, Renderer
from tools.screenshot import place_player

pytestmark = pytest.mark.graphics

pygame.init()

LEVELS = load_levels()
LEVEL_IDS = [level.id for level in LEVELS]
MID_X = 1500.0

# Valores calculados com as funções originais em TypeScript (node).
TINT_REFERENCE = {
    ("#88d5ed", 0.5): "#c4eaf6",
    ("#88d5ed", 0.16): "#9bdcf0",
    ("#a97743", -0.15): "#906539",
    ("#a97743", -0.2): "#875f36",
    ("#75bc4b", 0.14): "#88c564",
    ("#302637", 0.21): "#5b5461",
    ("#4c9290", 0.36): "#8cb9b8",
    ("#dea856", -0.35): "#906d38",
    ("#f8ce8a", 0.09): "#f9d295",
    ("#223a49", 0.13): "#3f5461",
    ("#5e91a7", 0.25): "#86adbd",
    ("#438568", -0.09): "#3d795f",
    ("#3f7b5e", -0.14): "#366a51",
    ("#3f7b5e", 0.1): "#52886e",
    ("xyz", 0.5): "xyz",
    ("#abc", 0.3): "#abc",
}
HASH_REFERENCE = {
    0: 0.819311730145273,
    1: 0.10468242550996365,
    2: 0.8001070824393537,
    33: 0.36001080505229766,
    77: 0.6876363986448268,
    120: 0.7878942501283746,
    180: 0.4887988910995773,
    231: 0.8433312449415098,
    500: 0.20639348775148392,
    1983: 0.5376944667877979,
    12345: 0.9311487533414038,
    -3: 0.8861291591347253,
    0.5: 0.6311590766345034,
    7.25: 0.4436307030337048,
}


def new_surface() -> pygame.Surface:
    return pygame.Surface((WIDTH, HEIGHT))


def pixels(surface: pygame.Surface) -> np.ndarray:
    """Cópia ``(altura, largura, 3)`` em uint8 da superfície."""
    return np.transpose(pygame.surfarray.array3d(surface), (1, 0, 2)).copy()


def packed_colors(surface: pygame.Surface) -> set[int]:
    array = pixels(surface).astype(np.uint32)
    packed = (array[:, :, 0] << 16) | (array[:, :, 1] << 8) | array[:, :, 2]
    return set(np.unique(packed).tolist())


def packed(color: str) -> int:
    r, g, b = parse_color(color)
    return (r << 16) | (g << 8) | b


def has_color(surface: pygame.Surface, color: str, tolerance: int = 0) -> bool:
    """Há algum pixel a até ``tolerance`` por canal de ``color``? (a vinheta escurece as bordas)."""
    array = pixels(surface).astype(np.int16)
    target = np.array(parse_color(color), dtype=np.int16)
    return bool(np.any(np.all(np.abs(array - target) <= tolerance, axis=2)))


def mean_difference(a: pygame.Surface, b: pygame.Surface) -> float:
    return float(np.mean(np.abs(pixels(a).astype(np.int16) - pixels(b).astype(np.int16))))


def game_for(level_id: str, x: float | None = None, frame: float = 1.0) -> Game:
    game = Game(LEVELS)
    game.load(LEVEL_IDS.index(level_id))
    if x is not None:
        place_player(game, x)
    game.elapsed = frame
    return game


def render(game: Game, quality: str = "high", effects: bool = True) -> Renderer:
    renderer = Renderer(new_surface())
    renderer.quality = quality
    renderer.effects = effects
    renderer.render(game, 0)
    return renderer


def assert_not_blank(surface: pygame.Surface, minimum_colors: int = 40) -> None:
    array = pixels(surface)
    assert int(np.ptp(array)) > 0, "superfície uniforme"
    assert len(packed_colors(surface)) >= minimum_colors


# painter --------------------------------------------------------------------------


def test_tint_matches_typescript_reference() -> None:
    for (color, amount), expected in TINT_REFERENCE.items():
        assert tint(color, amount) == expected


def test_hash01_matches_typescript_reference() -> None:
    for seed, expected in HASH_REFERENCE.items():
        assert hash01(seed) == pytest.approx(expected, abs=1e-9)
        assert 0 <= hash01(seed) < 1


def test_parse_color_handles_invalid_strings_visibly() -> None:
    assert parse_color("#ffd66d") == (255, 214, 109)
    assert parse_color("FFD66D") == (255, 214, 109)
    assert parse_color("rgba(1,2,3,0.5)") == (255, 0, 255)
    assert parse_color("#12") == (255, 0, 255)


def test_painter_transform_stack_matches_canvas_semantics() -> None:
    painter = Painter(new_surface(), Scene())
    painter.translate(10, 20)
    painter.scale(2, -1)
    painter.rotate(math.pi / 2)
    x, y = painter.to_device(1, 0)
    # (1, 0) → rotate → (0, 1) → scale → (0, -1) → translate → (10, 19)
    assert (round(x, 6), round(y, 6)) == (10, 19)
    painter.save()
    painter.translate(5, 5)
    assert painter.to_device(0, 0) != (10, 20)
    painter.restore()
    assert tuple(round(v, 6) for v in painter.to_device(0, 0)) == (10, 20)
    painter.reset()
    assert painter.transform == (1, 0, 0, 1, 0, 0)


def test_rect_mirrors_under_negative_scale_and_rounds_like_js() -> None:
    surface = new_surface()
    surface.fill((0, 0, 0))
    painter = Painter(surface, Scene())
    painter.translate(100, 100)
    painter.scale(-1, 1)
    painter.rect(2.5, 0, 3, 4, "#ffffff")  # Math.round(2.5) = 3 → x ∈ [-6, -3) espelhado
    lit = {x for x in range(90, 110) if surface.get_at((x, 101))[:3] == (255, 255, 255)}
    assert lit == {94, 95, 96}
    assert surface.get_at((100, 101))[:3] == (0, 0, 0)


def test_rect_under_rotation_becomes_polygon() -> None:
    surface = new_surface()
    surface.fill((0, 0, 0))
    painter = Painter(surface, Scene())
    painter.translate(200, 200)
    painter.rotate(math.pi / 4)
    painter.rect(-20, -4, 40, 8, "#ff0000")
    assert surface.get_at((200, 200))[:3] == (255, 0, 0)
    assert surface.get_at((210, 210))[:3] == (255, 0, 0)  # ao longo da diagonal
    assert surface.get_at((210, 190))[:3] == (0, 0, 0)  # fora da haste girada


def test_alpha_blends_rects_and_polygons() -> None:
    surface = new_surface()
    surface.fill((0, 0, 0))
    painter = Painter(surface, Scene())
    painter.set_alpha(0.5)
    painter.rect(10, 10, 20, 20, "#ffffff")
    painter.polygon([50, 10, 90, 10, 90, 50, 50, 50], "#ffffff")
    painter.set_alpha(1)
    painter.rect(100, 10, 5, 5, "#ffffff")
    assert all(abs(channel - 128) <= 2 for channel in surface.get_at((15, 15))[:3])
    assert all(abs(channel - 128) <= 2 for channel in surface.get_at((70, 30))[:3])
    assert surface.get_at((102, 12))[:3] == (255, 255, 255)


def test_sprite_matrix_scales_by_unit() -> None:
    surface = new_surface()
    surface.fill((0, 0, 0))
    painter = Painter(surface, Scene())
    painter.sprite(("#.", ".#"), {"#": "#00ff00"}, 10, 10, 3)
    assert surface.get_at((11, 11))[:3] == (0, 255, 0)
    assert surface.get_at((14, 11))[:3] == (0, 0, 0)
    assert surface.get_at((14, 14))[:3] == (0, 255, 0)


def test_visible_uses_camera_margins() -> None:
    painter = Painter(new_surface(), Scene(camera_x=1000, camera_y=0))
    assert painter.visible(950, 100, 10, 10)
    assert not painter.visible(900, 100, 10, 10)
    assert painter.visible(1000 + WIDTH + 50, 100, 10, 10)
    assert not painter.visible(1000 + WIDTH + 70, 100, 10, 10)


# fases ------------------------------------------------------------------------------


@pytest.mark.parametrize("level_id", LEVEL_IDS)
def test_level_renders_at_spawn_and_midpoint(level_id: str) -> None:
    for x in (None, MID_X):
        renderer = render(game_for(level_id, x))
        assert_not_blank(renderer.surface)
        stats = renderer.stats
        assert set(stats) >= {"sky", "scenery", "entities", "overlay", "total"}
        assert stats["total"] > 0


def test_render_is_deterministic() -> None:
    first = render(game_for("2-1", MID_X)).surface
    second = render(game_for("2-1", MID_X)).surface
    assert mean_difference(first, second) == 0


def test_worlds_produce_different_images() -> None:
    surfaces = [render(game_for(f"{world}-1")).surface for world in range(1, 6)]
    for i, a in enumerate(surfaces):
        for b in surfaces[i + 1 :]:
            assert mean_difference(a, b) > 5
        # Faixa do céu fora da vinheta (y = 126…143): cor exata do gradiente do tema.
        expected = parse_color(tint(THEMES[i].sky, (126 / HEIGHT) * 0.16))
        band = pixels(a)[126:144, :, :]
        assert np.any(np.all(band == np.array(expected, dtype=np.uint8), axis=2))


def test_first_level_draws_expected_elements() -> None:
    colors = packed_colors(render(game_for("1-1")).surface)
    assert packed("#dea856") in colors  # bloco de interrogação
    assert packed("#ffd66d") in colors  # moeda
    assert packed("#f3b99a") in colors  # pele do jogador
    assert packed("#c78076") in colors  # casco do andarilho
    assert packed("#e4c894") in colors  # placa de dica
    assert packed(THEMES[0].top) in colors  # grama


def test_boss_levels_draw_guardian_with_health_bar() -> None:
    for world in range(1, 6):
        level = LEVELS[LEVEL_IDS.index(f"{world}-3")]
        boss = next(enemy for enemy in level.enemies if is_boss_kind(enemy.kind))
        game = game_for(level.id, boss.x - 200)
        colors = packed_colors(render(game).surface)
        assert packed("#e6a07d") in colors, f"barra de vida do guardião ausente em {level.id}"
        assert packed("#253744") in colors


def test_exit_portal_and_checkpoint_render() -> None:
    level = LEVELS[0]
    game = game_for(level.id, level.exit.x - 300)
    colors = packed_colors(render(game).surface)
    assert packed("#e7ad65") in colors  # bandeira
    assert packed("#d4d7b9") in colors  # mastro
    game = game_for(level.id, level.checkpoint.x - 100)
    game.checkpoint_reached = True
    colors = packed_colors(render(game).surface)
    assert packed("#6ee2bf") in colors  # bandeira do checkpoint ativada


def test_hazards_ice_and_special_platforms_render() -> None:
    hazard_level = next(level for level in LEVELS if any(h.kind == "moving" for h in level.hazards))
    hazard = next(h for h in hazard_level.hazards if h.kind == "moving")
    colors = packed_colors(render(game_for(hazard_level.id, hazard.x - 100)).surface)
    assert packed("#ecc174") in colors  # núcleo da chama orbital
    lava_level = next(level for level in LEVELS if any(h.kind == "lava" for h in level.hazards))
    lava = next(h for h in lava_level.hazards if h.kind == "lava")
    surface = render(game_for(lava_level.id, lava.x - 200)).surface
    assert has_color(surface, "#bd4e4b", tolerance=24)  # lava fica sob a vinheta inferior
    assert has_color(surface, "#ffc176", tolerance=24)
    ice_level = next(level for level in LEVELS if any(p.kind == "ice" for p in level.platforms))
    ice = next(p for p in ice_level.platforms if p.kind == "ice")
    colors = packed_colors(render(game_for(ice_level.id, ice.x + 20)).surface)
    assert packed("#d3f6f1") in colors


def test_player_states_and_enemy_variants_render() -> None:
    game = game_for("1-1", 300)
    renderer = Renderer(new_surface())
    player = game.player
    for animation in ("idle", "walk", "run", "jump", "fall", "hurt", "dead", "win"):
        player.animation = animation
        for facing in (1, -1):
            player.facing = facing
            renderer.render(game, 0)
    player.animation = "run"
    player.vx = 320
    player.grounded = True
    player.star = 3
    player.power = "fire"
    player.h = 46
    renderer.render(game, 0)
    assert_not_blank(renderer.surface)
    player.star = 0
    player.invulnerable = 1
    game.elapsed = 0.0  # floor(frame·15) par → jogador piscando (invisível)
    renderer.render(game, 0)
    assert packed("#f3b99a") not in packed_colors(renderer.surface)
    for enemy in game.enemies:
        enemy.hit_timer = 0.3
        enemy.state = "slide"
    game.elapsed = 1.0
    renderer.render(game, 0)
    for platform in game.platforms:
        platform.used = True
        platform.bump = 0.5
        platform.crumble = 0.4
    renderer.render(game, 0)
    assert_not_blank(renderer.surface)


def test_rendering_after_simulation_with_particles_and_projectiles() -> None:
    game = game_for("1-2", 400, frame=0.0)
    renderer = Renderer(new_surface())
    for tick in range(600):
        game.update(1 / 120, InputState(right=True, run=True, jump=tick % 90 < 20, ability=True))
        if tick % 60 == 0:
            renderer.render(game, tick)
    game.hurt()
    renderer.render(game, 0)
    game.die()
    renderer.render(game, 0)
    assert_not_blank(renderer.surface)


def test_custom_level_without_ground_or_hints_renders() -> None:
    base = LEVELS[0]
    level = Level(
        id="empty",
        name="vazio",
        world=3,
        stage=1,
        width=1200,
        height=540,
        time=100,
        spawn=base.spawn,
        checkpoint=base.checkpoint,
        exit=base.exit,
    )
    game = Game([level])
    game.elapsed = 0.5
    renderer = render(game)
    assert_not_blank(renderer.surface, minimum_colors=10)
    stage = replace(level, platforms=list(base.platforms), hints=list(base.hints))
    render(Game([stage]))


# menu, qualidade e efeitos ---------------------------------------------------------------


def test_backdrop_for_each_world_and_clamped_values() -> None:
    surfaces = []
    for world in range(1, 6):
        renderer = Renderer(new_surface())
        renderer.backdrop(world)
        assert_not_blank(renderer.surface)
        surfaces.append(renderer.surface)
    for i, a in enumerate(surfaces):
        for b in surfaces[i + 1 :]:
            assert mean_difference(a, b) > 5
    low = Renderer(new_surface())
    low.backdrop(0)
    high = Renderer(new_surface())
    high.backdrop(99)
    assert mean_difference(low.surface, surfaces[0]) == 0
    assert mean_difference(high.surface, surfaces[-1]) == 0


@pytest.mark.parametrize("quality", sorted(QUALITY_PRESETS))
def test_quality_levels_render(quality: str) -> None:
    renderer = render(game_for("2-1", MID_X), quality=quality)
    assert_not_blank(renderer.surface)
    assert renderer.preset is QUALITY_PRESETS[quality]


def test_low_quality_draws_fewer_weather_particles() -> None:
    high = render(game_for("3-1", MID_X), quality="high").surface
    low = render(game_for("3-1", MID_X), quality="low").surface
    assert mean_difference(high, low) > 0
    assert mean_difference(high, render(game_for("3-1", MID_X), quality="high").surface) == 0


def test_effects_toggle_only_changes_weather_particles_and_shake() -> None:
    calm_on = render(game_for("1-1"), effects=True).surface
    calm_off = render(game_for("1-1"), effects=False).surface
    assert mean_difference(calm_on, calm_off) == 0  # mundo 1 sem clima nem partículas
    game = game_for("2-1", MID_X)
    game.shake = 0.1
    stormy_on = render(game, effects=True).surface
    stormy_off = render(game, effects=False).surface
    assert mean_difference(stormy_on, stormy_off) > 0


def test_unknown_quality_falls_back_to_high() -> None:
    renderer = Renderer(new_surface())
    renderer.quality = "ultra"
    assert renderer.preset is QUALITY_PRESETS["high"]
    renderer.render(game_for("1-1"), 0)


def test_non_finite_elapsed_uses_clock_in_seconds() -> None:
    game = game_for("1-1")
    game.elapsed = math.nan
    renderer = Renderer(new_surface())
    renderer.render(game, 2.4)  # Application.frame passa time.perf_counter() (segundos)
    assert renderer.scene.frame == pytest.approx(2.4)
    game.elapsed = math.inf
    renderer.render(game, math.nan)  # nenhum relógio finito: quadro 0 em vez de ValueError
    assert renderer.scene.frame == 0.0
    assert_not_blank(renderer.surface)


def arena_level(enemy: dict[str, object]) -> Level:
    """Fase mínima do mundo 1 com um único inimigo (mesmo formato dos testes de lógica)."""
    return level_from_dict(
        {
            "id": "arena",
            "name": "arena",
            "world": 1,
            "stage": 1,
            "width": 2400,
            "height": 540,
            "time": 300,
            "spawn": {"x": 64, "y": 414},
            "checkpoint": {"x": 1100, "y": 414},
            "exit": {"x": 2280, "y": 448},
            "platforms": [{"id": "floor", "kind": "ground", "x": 0, "y": 448, "w": 2400, "h": 92}],
            "enemies": [enemy],
        }
    )


def test_modern_ground_archetype_uses_walker_body_not_guardian() -> None:
    stage = arena_level(
        {"id": "s", "kind": "stalker", "x": 400, "y": 420, "w": 28, "h": 28, "patrol": [100, 1100]}
    )
    game = Game([stage])
    game.elapsed = 1.0
    colors = packed_colors(render(game).surface)
    assert packed("#c78076") in colors  # casco do andarilho
    assert packed("#e6a07d") not in colors  # sem barra de vida de guardião
    assert packed("#253744") not in colors


def test_modern_guardian_archetype_draws_boss_with_health_bar() -> None:
    stage = arena_level(
        {
            "id": "g",
            "kind": "guardian",
            "x": 700,
            "y": 384,
            "w": 62,
            "h": 64,
            "patrol": [400, 1300],
            "hp": 6,
        }
    )
    game = Game([stage])
    game.elapsed = 1.0
    colors = packed_colors(render(game).surface)
    assert packed("#e6a07d") in colors and packed("#253744") in colors  # barra de vida
    assert packed("#c78076") not in colors  # não é o andarilho


def test_telegraph_marker_appears_above_enemy_head_only_when_flagged() -> None:
    stage = arena_level(
        {"id": "s", "kind": "stalker", "x": 400, "y": 420, "w": 28, "h": 28, "patrol": [100, 1100]}
    )
    game = Game([stage])
    game.elapsed = 1.0
    enemy = game.enemies[0]
    enemy.telegraph = False
    calm = pixels(render(game).surface).astype(np.int16)
    enemy.telegraph = True
    alert = pixels(render(game).surface).astype(np.int16)
    changed = np.argwhere(np.any(calm != alert, axis=2))
    assert len(changed) > 0
    ys, xs = changed[:, 0], changed[:, 1]
    # Marcador acima da cabeça, dentro da largura do inimigo (câmera em x = 0).
    assert enemy.x - 4 <= xs.min() and xs.max() <= enemy.x + enemy.w + 4
    assert enemy.y - 40 <= ys.min() and ys.max() < enemy.y
    enemy.alive = False
    dead = pixels(render(game).surface).astype(np.int16)
    assert np.any(dead != calm)  # corpo some
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    assert np.array_equal(dead[y0:y1, x0:x1], calm[y0:y1, x0:x1])  # marcador some junto


# desempenho ------------------------------------------------------------------------------


@pytest.mark.performance
def test_render_time_is_reasonable() -> None:
    results: dict[str, float] = {}
    for label, x in (("spawn", None), ("x=1500", MID_X)):
        game = game_for("1-1", x)
        renderer = Renderer(new_surface())
        for _ in range(10):
            renderer.render(game, 0)
        started = time.perf_counter()
        frames = 60
        for i in range(frames):
            game.elapsed = 1 + i / 60
            renderer.render(game, 0)
        results[label] = (time.perf_counter() - started) / frames * 1000
    print("render 1-1 médio (ms):", {k: round(v, 2) for k, v in results.items()})
    for value in results.values():
        assert value < 50
