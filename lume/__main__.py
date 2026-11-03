"""Command line entry point: ``python -m lume``."""

from __future__ import annotations

import argparse
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="lume", description="Lume — As Dez Fronteiras (edição Python)")
    parser.add_argument("--res", help="resolução da janela, ex.: 1920x1080 (padrão: configuração salva/automática)")
    parser.add_argument("--fullscreen", action="store_true", help="abrir em tela cheia")
    parser.add_argument("--windowed", action="store_true", help="abrir em janela")
    parser.add_argument("--level", help="iniciar diretamente uma fase pelo id (ex.: first_steps)")
    parser.add_argument("--import-save", help="importar progresso exportado da edição web (lume-save-v1)")
    parser.add_argument("--show-fps", action="store_true", help="mostrar FPS e chamadas de desenho")
    parser.add_argument("--validate", action="store_true", help="validar a campanha e sair")
    parser.add_argument("--frames", type=int, default=0, help="encerrar após N quadros (testes)")
    parser.add_argument("--screenshot", help="salvar o último quadro em PNG (com --frames)")
    args = parser.parse_args(argv)
    if args.validate:
        from .core.species import load_profiles
        from .levels.campaign import load_campaign
        from .levels.validate import errors, validate_campaign

        problems = validate_campaign(load_campaign(), load_profiles())
        for p in problems:
            print(p)
        return 1 if errors(problems) else 0
    from .app import App, AppOptions

    fullscreen = True if args.fullscreen else False if args.windowed else None
    App(AppOptions(resolution=args.res, fullscreen=fullscreen, level=args.level, max_frames=args.frames,
                   screenshot=args.screenshot, import_save=args.import_save, show_fps=args.show_fps)).run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
