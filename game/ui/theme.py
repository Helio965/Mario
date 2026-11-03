"""Tema visual da interface: paletas, fontes, cache de texto e ícones vetoriais.

* ``Palette``: cores RGB da interface (versão normal e de alto contraste),
  afinadas pelo tema do mundo atual (``accent``).
* ``Fonts``: resolve uma família de sistema (Inter, Segoe UI, DejaVu…) com
  retorno garantido à fonte padrão do pygame (``freesansbold``).
* ``Style``: contexto de desenho compartilhado — paleta ativa, fontes, cache de
  superfícies de texto, ícones desenhados com ``pygame.draw`` (rasterizados em
  2× e reduzidos para suavizar), retângulos arredondados com alpha e sombras.

Nenhuma string visível nasce aqui: o módulo só desenha o que recebe.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass

import pygame

from game.core.types import Theme
from game.rendering.painter import parse_color, tint

RGB = tuple[int, int, int]

FONT_CANDIDATES: tuple[str, ...] = (
    "inter",
    "segoeui",
    "dejavusans",
    "liberationsans",
    "arial",
    "helvetica",
    "freesans",
)
TEXT_CACHE_LIMIT = 4096
ICON_CACHE_LIMIT = 512
FILL_CACHE_LIMIT = 192


def rgb(color: str) -> RGB:
    """``"#rrggbb"`` → tupla RGB (cores inválidas viram magenta visível)."""
    return parse_color(color)


def mix(a: RGB, b: RGB, amount: float) -> RGB:
    """Mistura linear ``a → b`` (``amount`` em [0, 1])."""
    amount = max(0.0, min(1.0, amount))
    return (
        round(a[0] + (b[0] - a[0]) * amount),
        round(a[1] + (b[1] - a[1]) * amount),
        round(a[2] + (b[2] - a[2]) * amount),
    )


@dataclass(slots=True)
class Palette:
    """Cores da interface. ``*_alpha`` são opacidades (0–255) usadas à parte."""

    ink: RGB
    muted: RGB
    cream: RGB
    line: RGB
    accent: RGB
    accent_soft: RGB
    accent_dark: RGB
    eyebrow: RGB
    body: RGB
    note: RGB
    panel: RGB
    backdrop: RGB
    backdrop_alpha: int
    shadow: RGB
    focus: RGB
    focus_width: int
    primary: RGB
    primary_hover: RGB
    primary_text: RGB
    primary_shadow: RGB
    primary_sub: RGB
    secondary: RGB
    secondary_hover: RGB
    secondary_border: RGB
    secondary_text: RGB
    text_button: RGB
    text_button_hover: RGB
    danger: RGB
    danger_bg: RGB
    danger_border: RGB
    link: RGB
    link_hover: RGB
    kbd_bg: RGB
    kbd_border: RGB
    kbd_text: RGB
    section_icon: RGB
    tip_bg: RGB
    tip_text: RGB
    tip_title: RGB
    track: RGB
    track_fill: RGB
    knob: RGB
    toggle_off: RGB
    toggle_on: RGB
    chip: RGB
    chip_text: RGB
    card: RGB
    card_border: RGB
    node: RGB
    node_hover: RGB
    node_hover_border: RGB
    node_current: RGB
    node_current_border: RGB
    node_cleared: RGB
    node_number: RGB
    node_number_text: RGB
    node_number_current: RGB
    node_text: RGB
    node_sub: RGB
    relic_found: RGB
    relic_missing: RGB
    confirm_bg: RGB
    confirm_border: RGB
    confirm_text: RGB
    stat_value: RGB
    stat_label: RGB
    state_icon_bg: RGB
    state_icon: RGB
    hud: RGB
    hud_alpha: int
    hud_border: RGB
    hud_text: RGB
    hud_label: RGB
    hud_sub: RGB
    hud_icon: RGB
    hud_badge: RGB
    time_low: RGB
    boss_track: RGB
    boss_fill: RGB
    boss_text: RGB
    toast: RGB
    toast_border: RGB
    toast_text: RGB
    subtitle_bg: RGB
    subtitle_text: RGB
    scene_label: RGB
    scene_label_alpha: int
    scene_text: RGB
    scene_dot: RGB
    menu_fade: RGB
    mark_body: RGB
    mark_cap: RGB


def default_palette(theme: Theme | None = None) -> Palette:
    """Paleta clara da identidade Lume (creme, verde-petróleo, dourado), afinada pelo tema."""
    accent = rgb(theme.near) if theme else rgb("#438568")
    accent_soft = rgb(tint(theme.near, 0.55)) if theme else rgb("#b7d592")
    accent_dark = rgb(tint(theme.near, -0.3)) if theme else rgb("#2f5d49")
    return Palette(
        ink=rgb("#183f42"),
        muted=rgb("#73827b"),
        cream=rgb("#f4f1e8"),
        line=rgb("#d9dfd3"),
        accent=accent,
        accent_soft=accent_soft,
        accent_dark=accent_dark,
        eyebrow=rgb("#758679"),
        body=rgb("#607957"),
        note=rgb("#909982"),
        panel=rgb("#f6f3e9"),
        backdrop=rgb("#133d38"),
        backdrop_alpha=168,
        shadow=rgb("#102b32"),
        focus=rgb("#da9b39"),
        focus_width=3,
        primary=rgb("#214d49"),
        primary_hover=rgb("#316457"),
        primary_text=rgb("#eff5e9"),
        primary_shadow=rgb("#133b37"),
        primary_sub=rgb("#b7cbbb"),
        secondary=rgb("#e9eddf"),
        secondary_hover=rgb("#dfe8d4"),
        secondary_border=rgb("#d6dece"),
        secondary_text=rgb("#183f42"),
        text_button=rgb("#6b7c6c"),
        text_button_hover=rgb("#e9eddf"),
        danger=rgb("#a45244"),
        danger_bg=rgb("#f7e7d8"),
        danger_border=rgb("#e6c6af"),
        link=rgb("#476858"),
        link_hover=rgb("#183f42"),
        kbd_bg=rgb("#fffdf5"),
        kbd_border=rgb("#cfd6c6"),
        kbd_text=rgb("#4f694e"),
        section_icon=rgb("#829a72"),
        tip_bg=rgb("#e9eddd"),
        tip_text=rgb("#819070"),
        tip_title=rgb("#58754a"),
        track=rgb("#e0e5d7"),
        track_fill=rgb("#688b53"),
        knob=rgb("#faf9f1"),
        toggle_off=rgb("#ced6c2"),
        toggle_on=rgb("#799b62"),
        chip=rgb("#e6eed9"),
        chip_text=rgb("#657c52"),
        card=rgb("#fffdf5"),
        card_border=rgb("#dde1d1"),
        node=rgb("#f3f5e9"),
        node_hover=rgb("#e6efda"),
        node_hover_border=rgb("#a9c397"),
        node_current=rgb("#e9f2dc"),
        node_current_border=rgb("#94b180"),
        node_cleared=rgb("#e8f0df"),
        node_number=rgb("#e1e8d4"),
        node_number_text=rgb("#678255"),
        node_number_current=rgb("#597d48"),
        node_text=rgb("#4a6650"),
        node_sub=rgb("#88927c"),
        relic_found=rgb("#bb9945"),
        relic_missing=rgb("#ced5bf"),
        confirm_bg=rgb("#f5e5d7"),
        confirm_border=rgb("#e4c5a9"),
        confirm_text=rgb("#8d6651"),
        stat_value=rgb("#51724a"),
        stat_label=rgb("#959b84"),
        state_icon_bg=rgb("#e7edda"),
        state_icon=rgb("#72925c"),
        hud=rgb("#183f42"),
        hud_alpha=237,
        hud_border=mix(rgb("#183f42"), accent, 0.35),
        hud_text=rgb("#edf5dc"),
        hud_label=rgb("#a2bda0"),
        hud_sub=rgb("#b2cba3"),
        hud_icon=rgb("#e0c78a"),
        hud_badge=rgb("#2c5355"),
        time_low=rgb("#f1a483"),
        boss_track=rgb("#6a504f"),
        boss_fill=rgb("#f0b584"),
        boss_text=rgb("#e9d7bb"),
        toast=rgb("#254e49"),
        toast_border=rgb("#3f6b5b"),
        toast_text=rgb("#eff4df"),
        subtitle_bg=rgb("#0f2426"),
        subtitle_text=rgb("#f6f3e9"),
        scene_label=rgb("#f6f3e8"),
        scene_label_alpha=230,
        scene_text=rgb("#85917a"),
        scene_dot=rgb("#f4f1e8"),
        menu_fade=rgb("#f4f1e8"),
        mark_body=rgb("#d7ae65"),
        mark_cap=rgb("#b5d78e"),
    )


def high_contrast_palette(theme: Theme | None = None) -> Palette:
    """Paleta de alto contraste: fundos sólidos, preto/branco e foco amarelo."""
    black = (0, 0, 0)
    white = (255, 255, 255)
    yellow = (255, 214, 0)
    gray = (64, 64, 64)
    light = (230, 230, 230)
    accent = rgb(tint(theme.near, -0.45)) if theme else (0, 72, 60)
    return Palette(
        ink=black,
        muted=gray,
        cream=white,
        line=black,
        accent=accent,
        accent_soft=light,
        accent_dark=black,
        eyebrow=gray,
        body=black,
        note=gray,
        panel=white,
        backdrop=black,
        backdrop_alpha=220,
        shadow=black,
        focus=yellow,
        focus_width=4,
        primary=black,
        primary_hover=(40, 40, 40),
        primary_text=white,
        primary_shadow=gray,
        primary_sub=light,
        secondary=white,
        secondary_hover=light,
        secondary_border=black,
        secondary_text=black,
        text_button=black,
        text_button_hover=light,
        danger=(170, 0, 0),
        danger_bg=white,
        danger_border=(170, 0, 0),
        link=black,
        link_hover=(0, 0, 160),
        kbd_bg=white,
        kbd_border=black,
        kbd_text=black,
        section_icon=black,
        tip_bg=light,
        tip_text=black,
        tip_title=black,
        track=light,
        track_fill=black,
        knob=white,
        toggle_off=(150, 150, 150),
        toggle_on=(0, 110, 40),
        chip=light,
        chip_text=black,
        card=white,
        card_border=black,
        node=white,
        node_hover=light,
        node_hover_border=black,
        node_current=(255, 250, 205),
        node_current_border=black,
        node_cleared=(220, 240, 220),
        node_number=light,
        node_number_text=black,
        node_number_current=black,
        node_text=black,
        node_sub=gray,
        relic_found=(150, 100, 0),
        relic_missing=(170, 170, 170),
        confirm_bg=(255, 240, 230),
        confirm_border=(170, 0, 0),
        confirm_text=black,
        stat_value=black,
        stat_label=gray,
        state_icon_bg=light,
        state_icon=black,
        hud=black,
        hud_alpha=255,
        hud_border=white,
        hud_text=white,
        hud_label=light,
        hud_sub=light,
        hud_icon=yellow,
        hud_badge=(50, 50, 50),
        time_low=(255, 120, 80),
        boss_track=(90, 90, 90),
        boss_fill=yellow,
        boss_text=white,
        toast=black,
        toast_border=white,
        toast_text=white,
        subtitle_bg=black,
        subtitle_text=white,
        scene_label=white,
        scene_label_alpha=255,
        scene_text=black,
        scene_dot=white,
        menu_fade=white,
        mark_body=yellow,
        mark_cap=white,
    )


class Fonts:
    """Fontes por tamanho/peso, com retorno à fonte padrão do pygame."""

    def __init__(self) -> None:
        if not pygame.font.get_init():
            pygame.font.init()
        self._regular = self._find(False)
        self._bold = self._find(True)
        self._cache: dict[tuple[int, bool], pygame.font.Font] = {}

    @staticmethod
    def _find(bold: bool) -> str | None:
        for name in FONT_CANDIDATES:
            try:
                path = pygame.font.match_font(name, bold=bold)
            except (OSError, pygame.error, TypeError):  # pragma: no cover - sistema sem fontes
                path = None
            if path:
                return str(path)
        return None

    @property
    def system(self) -> bool:
        """Verdadeiro quando uma fonte do sistema foi encontrada (senão: freesansbold)."""
        return self._regular is not None or self._bold is not None

    def get(self, size: int, bold: bool = False) -> pygame.font.Font:
        key = (size, bold)
        font = self._cache.get(key)
        if font is None:
            path = (self._bold if bold else self._regular) or self._regular or self._bold
            try:
                font = pygame.font.Font(path, size) if path else pygame.font.Font(None, size)
            except (OSError, pygame.error):  # pragma: no cover - arquivo de fonte corrompido
                font = pygame.font.Font(None, size)
            self._cache[key] = font
        return font


IconDrawer = Callable[[pygame.Surface, RGB, float, int], None]


def _pt(k: float, x: float, y: float) -> tuple[int, int]:
    return (round(x * k), round(y * k))


def _lines(
    surface: pygame.Surface, color: RGB, k: float, w: int, points: list[tuple[float, float]]
) -> None:
    pygame.draw.lines(surface, color, False, [_pt(k, x, y) for x, y in points], w)


def _draw_arrow(s: pygame.Surface, c: RGB, k: float, w: int) -> None:
    pygame.draw.line(s, c, _pt(k, 5, 12), _pt(k, 19, 12), w)
    _lines(s, c, k, w, [(13, 6), (19, 12), (13, 18)])


def _draw_back(s: pygame.Surface, c: RGB, k: float, w: int) -> None:
    pygame.draw.line(s, c, _pt(k, 19, 12), _pt(k, 5, 12), w)
    _lines(s, c, k, w, [(11, 6), (5, 12), (11, 18)])


def _draw_play(s: pygame.Surface, c: RGB, k: float, w: int) -> None:
    pygame.draw.polygon(s, c, [_pt(k, 8, 5), _pt(k, 19, 12), _pt(k, 8, 19)])


def _draw_map(s: pygame.Surface, c: RGB, k: float, w: int) -> None:
    outline = [(3, 6), (9, 3), (15, 6), (21, 3), (21, 18), (15, 21), (9, 18), (3, 21)]
    pygame.draw.polygon(s, c, [_pt(k, x, y) for x, y in outline], w)
    pygame.draw.line(s, c, _pt(k, 9, 3), _pt(k, 9, 18), w)
    pygame.draw.line(s, c, _pt(k, 15, 6), _pt(k, 15, 21), w)


def _draw_keys(s: pygame.Surface, c: RGB, k: float, w: int) -> None:
    pygame.draw.rect(s, c, pygame.Rect(_pt(k, 3, 6), _pt(k, 18, 12)), w, border_radius=round(2 * k))
    for x in (6.5, 10.5, 14.5, 18.5):
        pygame.draw.circle(s, c, _pt(k, x, 10), max(1, round(0.9 * k)))
    pygame.draw.circle(s, c, _pt(k, 6.5, 14), max(1, round(0.9 * k)))
    pygame.draw.line(s, c, _pt(k, 10, 14), _pt(k, 17, 14), w)


def _draw_settings(s: pygame.Surface, c: RGB, k: float, w: int) -> None:
    for x, knob in ((5, 8), (12, 16), (19, 7)):
        pygame.draw.line(s, c, _pt(k, x, 4), _pt(k, x, 20), w)
        pygame.draw.circle(s, c, _pt(k, x, knob), round(2.4 * k))


def _speaker(s: pygame.Surface, c: RGB, k: float) -> None:
    pygame.draw.polygon(
        s,
        c,
        [_pt(k, 3, 9), _pt(k, 6, 9), _pt(k, 11, 5), _pt(k, 11, 19), _pt(k, 6, 15), _pt(k, 3, 15)],
    )


def _draw_sound(s: pygame.Surface, c: RGB, k: float, w: int) -> None:
    _speaker(s, c, k)
    for radius in (3.5, 6.5):
        box = pygame.Rect(0, 0, round(radius * 2 * k), round(radius * 2 * k))
        box.center = _pt(k, 13, 12)
        pygame.draw.arc(s, c, box, -0.9, 0.9, w)


def _draw_mute(s: pygame.Surface, c: RGB, k: float, w: int) -> None:
    _speaker(s, c, k)
    pygame.draw.line(s, c, _pt(k, 15.5, 9), _pt(k, 21, 15), w)
    pygame.draw.line(s, c, _pt(k, 21, 9), _pt(k, 15.5, 15), w)


def _draw_full(s: pygame.Surface, c: RGB, k: float, w: int) -> None:
    _lines(s, c, k, w, [(3, 8), (3, 3), (8, 3)])
    _lines(s, c, k, w, [(16, 3), (21, 3), (21, 8)])
    _lines(s, c, k, w, [(3, 16), (3, 21), (8, 21)])
    _lines(s, c, k, w, [(21, 16), (21, 21), (16, 21)])


def _draw_lock(s: pygame.Surface, c: RGB, k: float, w: int) -> None:
    pygame.draw.rect(
        s, c, pygame.Rect(_pt(k, 6, 10), _pt(k, 12, 10)), w, border_radius=round(2 * k)
    )
    pygame.draw.line(s, c, _pt(k, 9, 10), _pt(k, 9, 7), w)
    pygame.draw.line(s, c, _pt(k, 15, 10), _pt(k, 15, 7), w)
    pygame.draw.arc(s, c, pygame.Rect(_pt(k, 9, 4), _pt(k, 6, 6)), 0, math.pi, w)
    pygame.draw.line(s, c, _pt(k, 12, 13.5), _pt(k, 12, 16), w)


def _draw_check(s: pygame.Surface, c: RGB, k: float, w: int) -> None:
    _lines(s, c, k, w, [(5, 12), (9, 16), (19, 6)])


_STAR = [
    (12, 3),
    (14.7, 8.5),
    (20.8, 9.4),
    (16.4, 13.7),
    (17.4, 19.8),
    (12, 16.9),
    (6.6, 19.8),
    (7.6, 13.7),
    (3.2, 9.4),
    (9.3, 8.5),
]


def _draw_star(s: pygame.Surface, c: RGB, k: float, w: int) -> None:
    pygame.draw.polygon(s, c, [_pt(k, x, y) for x, y in _STAR], w)


def _draw_star_fill(s: pygame.Surface, c: RGB, k: float, w: int) -> None:
    pygame.draw.polygon(s, c, [_pt(k, x, y) for x, y in _STAR])


def _draw_sparkle(s: pygame.Surface, c: RGB, k: float, w: int) -> None:
    """Marca ✦ (estrela de quatro pontas) usada como emblema."""
    pygame.draw.polygon(
        s,
        c,
        [
            _pt(k, 12, 2),
            _pt(k, 14.2, 9.8),
            _pt(k, 22, 12),
            _pt(k, 14.2, 14.2),
            _pt(k, 12, 22),
            _pt(k, 9.8, 14.2),
            _pt(k, 2, 12),
            _pt(k, 9.8, 9.8),
        ],
    )


def _heart_points() -> list[tuple[float, float]]:
    raw = []
    for i in range(40):
        t = 2 * math.pi * i / 40
        x = 16 * math.sin(t) ** 3
        y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        raw.append((x, -y))
    xs = [p[0] for p in raw]
    ys = [p[1] for p in raw]
    sx = 18 / (max(xs) - min(xs))
    sy = 17 / (max(ys) - min(ys))
    scale = min(sx, sy)
    cx = (max(xs) + min(xs)) / 2
    cy = (max(ys) + min(ys)) / 2
    return [(12 + (x - cx) * scale, 12 + (y - cy) * scale) for x, y in raw]


_HEART = _heart_points()


def _draw_heart(s: pygame.Surface, c: RGB, k: float, w: int) -> None:
    pygame.draw.polygon(s, c, [_pt(k, x, y) for x, y in _HEART], w)


def _draw_coin(s: pygame.Surface, c: RGB, k: float, w: int) -> None:
    pygame.draw.ellipse(s, c, pygame.Rect(_pt(k, 5, 3), _pt(k, 14, 18)), w)
    pygame.draw.line(s, c, _pt(k, 12, 7), _pt(k, 12, 17), w)


def _draw_pause(s: pygame.Surface, c: RGB, k: float, w: int) -> None:
    pygame.draw.line(s, c, _pt(k, 8, 5), _pt(k, 8, 19), w + 1)
    pygame.draw.line(s, c, _pt(k, 16, 5), _pt(k, 16, 19), w + 1)


def _draw_trophy(s: pygame.Surface, c: RGB, k: float, w: int) -> None:
    _lines(s, c, k, w, [(8, 3), (16, 3), (16, 10), (14, 14), (10, 14), (8, 10), (8, 3)])
    _lines(s, c, k, w, [(8, 6), (4, 6), (4, 9), (6, 12), (8, 12)])
    _lines(s, c, k, w, [(16, 6), (20, 6), (20, 9), (18, 12), (16, 12)])
    pygame.draw.line(s, c, _pt(k, 12, 14), _pt(k, 12, 19), w)
    pygame.draw.line(s, c, _pt(k, 8, 20), _pt(k, 16, 20), w)


def _draw_info(s: pygame.Surface, c: RGB, k: float, w: int) -> None:
    pygame.draw.circle(s, c, _pt(k, 12, 12), round(9 * k), w)
    pygame.draw.line(s, c, _pt(k, 12, 11), _pt(k, 12, 17), w)
    pygame.draw.circle(s, c, _pt(k, 12, 7.5), max(1, round(1.1 * k)))


def _draw_dot(s: pygame.Surface, c: RGB, k: float, w: int) -> None:
    pygame.draw.rect(s, c, pygame.Rect(_pt(k, 7, 7), _pt(k, 10, 10)))


def _draw_bullet(s: pygame.Surface, c: RGB, k: float, w: int) -> None:
    pygame.draw.circle(s, c, _pt(k, 12, 12), max(1, round(5 * k)))


def _draw_chevron_left(s: pygame.Surface, c: RGB, k: float, w: int) -> None:
    _lines(s, c, k, w, [(15, 5), (8, 12), (15, 19)])


def _draw_chevron_right(s: pygame.Surface, c: RGB, k: float, w: int) -> None:
    _lines(s, c, k, w, [(9, 5), (16, 12), (9, 19)])


def _draw_gamepad(s: pygame.Surface, c: RGB, k: float, w: int) -> None:
    pygame.draw.rect(s, c, pygame.Rect(_pt(k, 2, 8), _pt(k, 20, 10)), w, border_radius=round(5 * k))
    pygame.draw.line(s, c, _pt(k, 7, 11), _pt(k, 7, 15), w)
    pygame.draw.line(s, c, _pt(k, 5, 13), _pt(k, 9, 13), w)
    pygame.draw.circle(s, c, _pt(k, 16, 12), max(1, round(1.2 * k)))
    pygame.draw.circle(s, c, _pt(k, 18.5, 14.5), max(1, round(1.2 * k)))


ICONS: dict[str, IconDrawer] = {
    "arrow": _draw_arrow,
    "back": _draw_back,
    "play": _draw_play,
    "map": _draw_map,
    "keys": _draw_keys,
    "settings": _draw_settings,
    "sound": _draw_sound,
    "mute": _draw_mute,
    "full": _draw_full,
    "lock": _draw_lock,
    "check": _draw_check,
    "star": _draw_star,
    "star_fill": _draw_star_fill,
    "sparkle": _draw_sparkle,
    "heart": _draw_heart,
    "coin": _draw_coin,
    "pause": _draw_pause,
    "trophy": _draw_trophy,
    "info": _draw_info,
    "dot": _draw_dot,
    "bullet": _draw_bullet,
    "chevron_left": _draw_chevron_left,
    "chevron_right": _draw_chevron_right,
    "gamepad": _draw_gamepad,
}


class Style:
    """Contexto de desenho: paleta ativa, fontes, caches e relógio de animação."""

    def __init__(self, fonts: Fonts | None = None) -> None:
        self.fonts = fonts or Fonts()
        self.palette: Palette = default_palette(None)
        self.high_contrast = False
        self.motion = True
        self.time = 0.0
        self._text_cache: dict[tuple[int, bool, int, RGB, str], pygame.Surface] = {}
        self._icon_cache: dict[tuple[str, int, RGB], pygame.Surface] = {}
        self._fill_cache: dict[tuple[int, int, RGB, int, int, RGB | None, int], pygame.Surface] = {}

    # ------------------------------------------------------------- estado
    def apply(self, theme: Theme | None, high_contrast: bool, motion: bool) -> None:
        self.high_contrast = high_contrast
        self.motion = motion
        self.palette = high_contrast_palette(theme) if high_contrast else default_palette(theme)

    def pulse(self, period: float = 1.6, low: float = 0.0, high: float = 1.0) -> float:
        """Oscilação suave em [low, high]; constante (``high``) com redução de movimento."""
        if not self.motion:
            return high
        phase = (math.sin(self.time * 2 * math.pi / period) + 1) / 2
        return low + (high - low) * phase

    # -------------------------------------------------------------- texto
    def font(self, size: int, bold: bool = False) -> pygame.font.Font:
        return self.fonts.get(size, bold)

    def text(
        self, text: str, size: int, color: RGB, bold: bool = False, spacing: int = 0
    ) -> pygame.Surface:
        """Superfície de texto cacheada (``spacing`` = espaçamento extra entre letras)."""
        key = (size, bold, spacing, color, text)
        surface = self._text_cache.get(key)
        if surface is not None:
            return surface
        font = self.fonts.get(size, bold)
        if not text:
            surface = pygame.Surface((1, font.get_height()), pygame.SRCALPHA)
        elif spacing == 0 or len(text) == 1:
            surface = font.render(text, True, color)
        else:
            glyphs = [font.render(char, True, color) for char in text]
            width = sum(g.get_width() for g in glyphs) + spacing * (len(glyphs) - 1)
            surface = pygame.Surface((max(1, width), font.get_height()), pygame.SRCALPHA)
            x = 0
            for glyph in glyphs:
                surface.blit(glyph, (x, 0))
                x += glyph.get_width() + spacing
        if len(self._text_cache) >= TEXT_CACHE_LIMIT:
            self._text_cache.clear()
        self._text_cache[key] = surface
        return surface

    def measure(
        self, text: str, size: int, bold: bool = False, spacing: int = 0
    ) -> tuple[int, int]:
        return self.text(text, size, self.palette.ink, bold, spacing).get_size()

    def wrap(self, text: str, size: int, max_width: int, bold: bool = False) -> list[str]:
        """Quebra ``text`` em linhas que cabem em ``max_width`` (``\\n`` força quebra)."""
        font = self.fonts.get(size, bold)
        lines: list[str] = []
        for paragraph in text.split("\n"):
            line = ""
            for word in paragraph.split(" "):
                trial = word if not line else f"{line} {word}"
                if not line or font.size(trial)[0] <= max_width:
                    line = trial
                else:
                    lines.append(line)
                    line = word
            lines.append(line)
        return lines

    # ------------------------------------------------------------- formas
    def round_rect(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        color: RGB,
        radius: int = 0,
        alpha: int = 255,
        border: RGB | None = None,
        width: int = 1,
    ) -> None:
        """Retângulo arredondado; com ``alpha < 255`` usa uma camada SRCALPHA cacheada."""
        rect = pygame.Rect(rect)
        if rect.w <= 0 or rect.h <= 0:
            return
        if alpha >= 255:
            pygame.draw.rect(surface, color, rect, border_radius=radius)
            if border is not None:
                pygame.draw.rect(surface, border, rect, width, border_radius=radius)
            return
        key = (rect.w, rect.h, color, radius, alpha, border, width)
        layer = self._fill_cache.get(key)
        if layer is None:
            layer = pygame.Surface(rect.size, pygame.SRCALPHA)
            pygame.draw.rect(layer, (*color, alpha), layer.get_rect(), border_radius=radius)
            if border is not None:
                pygame.draw.rect(
                    layer,
                    (*border, min(255, alpha + 30)),
                    layer.get_rect(),
                    width,
                    border_radius=radius,
                )
            if len(self._fill_cache) >= FILL_CACHE_LIMIT:
                self._fill_cache.clear()
            self._fill_cache[key] = layer
        surface.blit(layer, rect.topleft)

    def shadow(self, surface: pygame.Surface, rect: pygame.Rect, radius: int = 10) -> None:
        """Sombra suave abaixo de um painel (três anéis de alpha decrescente)."""
        color = self.palette.shadow
        for spread, alpha in ((12, 18), (6, 26), (2, 40)):
            self.round_rect(
                surface,
                rect.inflate(spread * 2, spread * 2).move(0, 8),
                color,
                radius + spread,
                alpha,
            )

    def focus_ring(self, surface: pygame.Surface, rect: pygame.Rect, radius: int = 6) -> None:
        """Contorno de foco visível (3 px, deslocado 3 px), pulsando levemente com animação."""
        p = self.palette
        width = p.focus_width
        ring = pygame.Rect(rect).inflate(6 + width, 6 + width)
        alpha = round(255 * self.pulse(1.4, 0.7, 1.0))
        layer_key = (ring.w, ring.h, p.focus, radius + 4, alpha, p.focus, width)
        layer = self._fill_cache.get(layer_key)
        if layer is None:
            layer = pygame.Surface(ring.size, pygame.SRCALPHA)
            pygame.draw.rect(
                layer, (*p.focus, alpha), layer.get_rect(), width, border_radius=radius + 4
            )
            if len(self._fill_cache) >= FILL_CACHE_LIMIT:
                self._fill_cache.clear()
            self._fill_cache[layer_key] = layer
        surface.blit(layer, ring.topleft)

    # ------------------------------------------------------------- ícones
    def icon(self, name: str, size: int, color: RGB) -> pygame.Surface:
        """Ícone vetorial ``name`` em ``size`` px, rasterizado em 2× e reduzido (suavizado)."""
        key = (name, size, color)
        surface = self._icon_cache.get(key)
        if surface is not None:
            return surface
        drawer = ICONS.get(name, _draw_star)
        big = max(2, size * 2)
        canvas = pygame.Surface((big, big), pygame.SRCALPHA)
        drawer(canvas, color, big / 24, max(1, round(big / 13)))
        surface = pygame.transform.smoothscale(canvas, (max(1, size), max(1, size)))
        if len(self._icon_cache) >= ICON_CACHE_LIMIT:
            self._icon_cache.clear()
        self._icon_cache[key] = surface
        return surface

    def kbd(
        self, surface: pygame.Surface, x: int, y: int, label: str, size: int = 9
    ) -> pygame.Rect:
        """Desenha uma "tecla" (chip com borda) e devolve seu retângulo."""
        p = self.palette
        text = self.text(label, size, p.kbd_text, True, 1)
        rect = pygame.Rect(x, y, text.get_width() + 12, text.get_height() + 6)
        pygame.draw.rect(surface, p.kbd_bg, rect, border_radius=3)
        pygame.draw.rect(surface, p.kbd_border, rect, 1, border_radius=3)
        pygame.draw.line(
            surface, p.kbd_border, (rect.x + 2, rect.bottom), (rect.right - 3, rect.bottom)
        )
        surface.blit(text, (rect.x + 6, rect.y + 3))
        return rect
