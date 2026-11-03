"""Graphics tests: real frames rendered by the HD pipeline (SDL software
renderer under the dummy video driver — no GPU in CI). They check that every
implemented level renders at 720p, 1080p and 4K without errors, that textures
are rasterized at the output density (never upscaled), and report which
species still use the provisional creature art."""

import os

import pygame
import pytest

from lume.core.game import Game
from lume.core.species import load_profiles
from lume.levels.campaign import load_campaign
from lume.render.display import Display
from lume.render.enemies import RIGS
from lume.render.scene import Scene

pytestmark = pytest.mark.graphics
CAMPAIGN = load_campaign()


@pytest.fixture(scope="module")
def display_720():
    d = Display((1280, 720), hidden=True)
    yield d
    d.close()


def frame(display, level, x=None, zoom=1.3):
    scene = Scene(display, zoom=zoom)
    game = Game([level])
    if x is not None:
        game.player.x = x
        game.camera.snap(game)
    for e in game.enemies:
        e.active = True
    for _ in range(30):
        game.update(1 / 120, __import__("lume.core.input", fromlist=["InputState"]).InputState())
    scene.render(game, 1 / 60)
    return scene, display.screenshot()


def variance(surface: pygame.Surface) -> float:
    small = pygame.transform.smoothscale(surface, (64, 36))
    values = [sum(small.get_at((x, y))[:3]) for x in range(64) for y in range(36)]
    mean = sum(values) / len(values)
    return sum((v - mean) ** 2 for v in values) / len(values)


@pytest.mark.parametrize("level", CAMPAIGN.levels, ids=lambda lvl: lvl.id)
def test_every_level_renders_at_720p(display_720, level):
    scene, shot = frame(display_720, level)
    assert shot.get_size() == (1280, 720)
    assert variance(shot) > 200, "quadro sem conteúdo"
    assert scene.stats["draws"] > 8


@pytest.mark.parametrize("res", [(1280, 720), (1920, 1080), (3840, 2160)])
def test_first_level_renders_at_reference_resolutions(res):
    display = Display(res, hidden=True)
    try:
        scene, shot = frame(display, CAMPAIGN.level("first_steps"), 400)
        assert shot.get_size() == res
        assert variance(shot) > 200
        # textures are rasterized for the output density: a coin (22 u wide art)
        coin = scene.store.get("coin.0")
        expected = 22 * display.scale * scene.zoom
        assert abs(coin.tex.width - expected) <= 2, (coin.tex.width, expected)
        # Lume's head part (52 du * 0.40 u/du)
        head = scene.store.get("lume.head")
        assert abs(head.tex.width - 52 * 0.40 * display.scale * scene.zoom) <= 2
    finally:
        display.close()


def test_letterbox_keeps_aspect_ratio_on_ultrawide():
    display = Display((2560, 1080), hidden=True)
    try:
        assert display.scale == 2.0 and display.offset_x == 320
        scene, shot = frame(display, CAMPAIGN.level("first_steps"))
        assert shot.get_at((10, 540))[:3] == (0, 0, 0)  # letterbox bar
    finally:
        display.close()


def test_rig_coverage_report():
    """Every species has a rig; species drawn with the provisional creature are
    listed so the quality matrix can report them (no silent placeholders)."""
    profiles = load_profiles()
    provisional = sorted(s for s, p in profiles.items() if p.animation_set not in RIGS)
    w1 = {"bolota", "caramujo", "besouro_alado", "besouro", "flor_mordedora", "ourico_espinho", "javali_espinheiro", "guardiao_pomar"}
    assert not (w1 & set(provisional)), "Reino Verde não pode usar arte provisória"
    os.makedirs("artifacts", exist_ok=True)
    with open("artifacts/provisional_species.txt", "w", encoding="utf-8") as fh:
        fh.write("\n".join(provisional) + "\n")


def test_character_sheet_states_all_draw():
    from lume.core.entities import Player
    from lume.render.characters.lume import LumeAnimator

    display = Display((640, 360), hidden=True)
    try:
        scene = Scene(display)
        for state in ("idle", "walk", "run", "skid", "jump", "fall", "land", "crouch", "swim", "hurt", "dead", "win", "transform"):
            anim = LumeAnimator()
            p = Player(0, 0)
            cmds, du = anim.commands(p, state, 1 / 60)
            assert cmds and all(scene.store.get(c.part) is not None for c in cmds), state
    finally:
        display.close()


@pytest.mark.parametrize("level", [lvl for lvl in CAMPAIGN.levels if len(lvl.areas) > 1], ids=lambda lvl: lvl.id)
def test_every_sub_area_renders(display_720, level):
    """Secret rooms, tunnels and other sub-areas render too (not only the spawn view)."""
    for area in level.areas[1:]:
        scene = Scene(display_720)
        game = Game([level])
        floor = min((p.y for p in level.platforms if p.kind in ("ground", "ledge")
                     and area.x <= p.x + p.w / 2 < area.x + area.w and area.y < p.y < area.y + area.h), default=area.y + area.h - 100)
        game.player.x = area.x + area.w / 2
        game.player.y = floor - game.player.h - 1
        game.camera.snap(game)
        scene.render(game, 1 / 60)
        assert variance(display_720.screenshot()) > 100, area.id


def test_dark_zone_draws_lantern_halo(display_720):
    from .conftest import level as make_level

    lvl = make_level(zones=[{"id": "dark", "kind": "dark", "x": 0, "y": 0, "w": 2400, "h": 540}])
    scene = Scene(display_720)
    game = Game([lvl])
    scene.render(game, 1 / 60)
    shot = display_720.screenshot()
    far = sum(shot.get_at((1200, 420))[:3])  # far right: outside the halo and the HUD
    lit_scene = Scene(display_720)
    lit_game = Game([make_level()])
    lit_scene.render(lit_game, 1 / 60)
    lit = sum(display_720.screenshot().get_at((1200, 420))[:3])
    assert game.darkness() > 0 and far < lit * 0.35  # 85% darkness away from the lantern


def test_decor_and_terrain_layout_is_identical_across_processes():
    """Seeds must not depend on the per-process ``hash()`` salt: the layout of
    decor and terrain detail (and the raster disk cache keys) must be stable."""
    import subprocess
    import sys

    code = (
        "import os; os.environ['SDL_VIDEODRIVER']='dummy'\n"
        "from lume.core.game import Game\n"
        "from lume.levels.campaign import load_campaign\n"
        "from lume.render.display import Display\n"
        "from lume.render.scene import Scene\n"
        "lvl = load_campaign().level('first_steps')\n"
        "scene = Scene(Display((640, 360), hidden=True))\n"
        "scene.prepare(Game([lvl]))\n"
        "print([(d.art, round(d.x, 2)) for d in scene.decor][:40])\n"
    )
    outputs = set()
    for salt in ("1", "2"):
        env = {**os.environ, "PYTHONHASHSEED": salt, "SDL_VIDEODRIVER": "dummy", "SDL_AUDIODRIVER": "dummy"}
        run = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env, cwd=os.getcwd(), timeout=120)
        assert run.returncode == 0, run.stderr
        outputs.add(run.stdout.strip().splitlines()[-1])
    assert len(outputs) == 1


def test_world_art_receives_the_level_art_variant(display_720):
    """World art sets can vary per level: Scene.prepare hands them art.variant
    and rebuilds world-level art when the variant changes within a world."""
    a = CAMPAIGN.level("windswept_dunes")
    b = CAMPAIGN.level("sunken_oasis")
    scene = Scene(display_720)
    scene.prepare(Game([a]))
    assert scene.world.variant == (a.art_variant or "default")
    scene.store.get(f"{scene.world.id}.sky")
    assert scene.store.cache, "sky should be cached"
    scene.prepare(Game([b]))
    assert scene.world.variant == (b.art_variant or "default")
    assert a.art_variant != b.art_variant
    assert f"{scene.world.id}.sky" not in scene.store.cache  # rebuilt for the new variant


def test_outdoor_auto_decor_stays_out_of_indoor_areas(display_720):
    """Trees and lamp posts must not sprout inside fortress halls or mansions."""
    level = CAMPAIGN.level("frost_citadel")
    scene = Scene(display_720)
    scene.prepare(Game([level]))
    indoor = [a for a in level.areas if a.variant in ("fortress", "throne")]
    assert indoor
    for d in scene.decor:
        for a in indoor:
            assert not (a.x <= d.x < a.x + a.w and a.y <= d.y - 1 < a.y + a.h), (d.art, d.x)
