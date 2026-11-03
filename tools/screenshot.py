"""Captura de tela headless do renderizador (sem janela, sem áudio).

Exemplos::

    .venv/bin/python tools/screenshot.py --level 1-1 --x 1500 --out build/shot.png
    .venv/bin/python tools/screenshot.py --menu 3 --out build/menu-3.png
    .venv/bin/python tools/screenshot.py --all build/screenshots --mid 1500

``--all DIR`` gera as 15 fases no spawn (``level-<id>.png``), opcionalmente
num ponto intermediário (``level-<id>-mid.png`` com ``--mid X``) e os cinco
cenários do menu (``menu-<mundo>.png``).
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# O renderizador nunca precisa de janela nem de áudio nesta ferramenta.
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pygame

from game.core.game import Game
from game.levels.loader import THEMES, load_levels
from game.rendering.renderer import Renderer
from game.settings import VIEW_HEIGHT, VIEW_WIDTH


def place_player(game: Game, x: float) -> None:
    """Posiciona o jogador sobre o chão mais alto que contém ``x`` e enquadra a câmera.

    Usa a mesma regra de alvo da câmera do laço de jogo (``x − 310``,
    ``y − 250``) com saturação aos limites da fase.
    """
    level = game.level
    player = game.player
    x = max(0.0, min(float(x), level.width - player.w))
    center = x + player.w / 2
    grounds = [
        p for p in game.platforms if p.kind in ("ground", "ice") and p.x <= center < p.x + p.w
    ]
    if grounds:
        floor = min(grounds, key=lambda p: p.y)
        player.y = floor.y - player.h
        player.grounded = True
        player.standing_on = floor.id
    player.x = x
    player.vx = 0
    player.vy = 0
    player.animation = "idle"
    game.camera.x = max(0.0, min(level.width - VIEW_WIDTH, x - 310))
    game.camera.y = max(0.0, min(level.height - VIEW_HEIGHT, player.y - 250))


def make_renderer(quality: str = "high", effects: bool = True) -> Renderer:
    surface = pygame.Surface((VIEW_WIDTH, VIEW_HEIGHT))
    renderer = Renderer(surface)
    renderer.quality = quality
    renderer.effects = effects
    return renderer


def render_level(
    level_id: str,
    x: float | None = None,
    frame: float = 1.0,
    quality: str = "high",
    effects: bool = True,
) -> pygame.Surface:
    """Renderiza a fase ``level_id`` (ex.: ``"1-1"``) no spawn ou em ``x`` e devolve a superfície."""
    levels = load_levels()
    index = next((i for i, level in enumerate(levels) if level.id == level_id), None)
    if index is None:
        raise SystemExit(f"fase desconhecida: {level_id!r} (use 1-1 … 5-3)")
    game = Game(levels)
    game.load(index)
    if x is not None:
        place_player(game, x)
    game.elapsed = frame
    renderer = make_renderer(quality, effects)
    renderer.render(game, frame)
    return renderer.surface


def render_backdrop(world: int, quality: str = "high", effects: bool = True) -> pygame.Surface:
    renderer = make_renderer(quality, effects)
    renderer.backdrop(world)
    return renderer.surface


def save(surface: pygame.Surface, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pygame.image.save(surface, str(path))


def render_all(
    directory: Path, mid: float | None, frame: float, quality: str, effects: bool
) -> list[Path]:
    written: list[Path] = []
    for level in load_levels():
        path = directory / f"level-{level.id}.png"
        save(render_level(level.id, None, frame, quality, effects), path)
        written.append(path)
        if mid is not None:
            path = directory / f"level-{level.id}-mid.png"
            save(render_level(level.id, mid, frame, quality, effects), path)
            written.append(path)
    for world in range(1, len(THEMES) + 1):
        path = directory / f"menu-{world}.png"
        save(render_backdrop(world, quality, effects), path)
        written.append(path)
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Captura headless do renderizador do Lume.")
    parser.add_argument("--level", default="1-1", help="id da fase (1-1 … 5-3)")
    parser.add_argument(
        "--x", type=float, default=None, help="posição x do jogador (padrão: spawn)"
    )
    parser.add_argument("--frame", type=float, default=1.0, help="tempo da animação em segundos")
    parser.add_argument(
        "--menu", type=int, default=None, help="renderiza o cenário do menu do mundo N"
    )
    parser.add_argument("--out", type=Path, default=Path("build/screenshot.png"))
    parser.add_argument(
        "--all", type=Path, default=None, metavar="DIR", help="gera todas as capturas em DIR"
    )
    parser.add_argument(
        "--mid", type=float, default=None, help="com --all: também captura cada fase em x=MID"
    )
    parser.add_argument("--quality", choices=("high", "medium", "low"), default="high")
    parser.add_argument(
        "--no-effects", action="store_true", help="desliga clima, partículas e tremor"
    )
    args = parser.parse_args(argv)
    effects = not args.no_effects
    pygame.init()
    try:
        if args.all is not None:
            for path in render_all(args.all, args.mid, args.frame, args.quality, effects):
                print(path)
            return 0
        if args.menu is not None:
            surface = render_backdrop(args.menu, args.quality, effects)
        else:
            surface = render_level(args.level, args.x, args.frame, args.quality, effects)
        save(surface, args.out)
        print(args.out)
        return 0
    finally:
        pygame.quit()


if __name__ == "__main__":
    raise SystemExit(main())
