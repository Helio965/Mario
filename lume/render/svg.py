"""Tiny SVG builder used by all original artwork.

The art is authored in Python as vector shapes (paths, ellipses, gradients) and
rasterized by SDL_image/nanosvg at the exact output resolution, so every asset
stays sharp from 720p to 4K. nanosvg ignores gradients in objectBoundingBox
units, therefore every gradient here is emitted in ``userSpaceOnUse`` with
absolute coordinates (see docs/technical/SISTEMA_GRAFICO.md).
"""

from __future__ import annotations

import colorsys
import math
from contextlib import contextmanager
from typing import Iterable, Iterator, Optional, Sequence

Stop = tuple[float, str] | tuple[float, str, float]


def _f(v: float) -> str:
    s = f"{v:.3f}".rstrip("0").rstrip(".")
    return s if s not in ("-0", "") else "0"


def hex_to_rgb(color: str) -> tuple[float, float, float]:
    c = color.lstrip("#")
    return tuple(int(c[i : i + 2], 16) / 255 for i in (0, 2, 4))  # type: ignore[return-value]


def rgb_to_hex(r: float, g: float, b: float) -> str:
    return "#" + "".join(f"{max(0, min(255, round(v * 255))):02x}" for v in (r, g, b))


def mix(a: str, b: str, t: float) -> str:
    ra, ga, ba = hex_to_rgb(a)
    rb, gb, bb = hex_to_rgb(b)
    return rgb_to_hex(ra + (rb - ra) * t, ga + (gb - ga) * t, ba + (bb - ba) * t)


def shade(color: str, amount: float) -> str:
    """amount > 0 lightens toward white, < 0 darkens toward black."""
    return mix(color, "#ffffff" if amount > 0 else "#000000", abs(amount))


def hue_shift(color: str, degrees: float, sat: float = 1.0, light: float = 1.0) -> str:
    r, g, b = hex_to_rgb(color)
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    r, g, b = colorsys.hls_to_rgb((h + degrees / 360) % 1, min(1, l * light), min(1, s * sat))
    return rgb_to_hex(r, g, b)


class Svg:
    """Accumulates shapes in a ``w × h`` user space (world or art units)."""

    def __init__(self, w: float, h: float) -> None:
        self.w, self.h = float(w), float(h)
        self._defs: list[str] = []
        self._body: list[str] = []
        self._n = 0

    # -- paint servers -----------------------------------------------------------------
    def _stops(self, stops: Sequence[Stop]) -> str:
        out = []
        for s in stops:
            offset, color = s[0], s[1]
            opacity = s[2] if len(s) > 2 else 1.0  # type: ignore[misc]
            op = f' stop-opacity="{_f(opacity)}"' if opacity < 1 else ""
            out.append(f'<stop offset="{_f(offset)}" stop-color="{color}"{op}/>')
        return "".join(out)

    def linear(self, x1: float, y1: float, x2: float, y2: float, stops: Sequence[Stop]) -> str:
        self._n += 1
        gid = f"g{self._n}"
        self._defs.append(
            f'<linearGradient id="{gid}" gradientUnits="userSpaceOnUse" x1="{_f(x1)}" y1="{_f(y1)}" '
            f'x2="{_f(x2)}" y2="{_f(y2)}">{self._stops(stops)}</linearGradient>'
        )
        return f"url(#{gid})"

    def radial(self, cx: float, cy: float, r: float, stops: Sequence[Stop], fx: Optional[float] = None,
               fy: Optional[float] = None) -> str:
        self._n += 1
        gid = f"g{self._n}"
        focus = f' fx="{_f(fx)}" fy="{_f(fy)}"' if fx is not None and fy is not None else ""
        self._defs.append(
            f'<radialGradient id="{gid}" gradientUnits="userSpaceOnUse" cx="{_f(cx)}" cy="{_f(cy)}" r="{_f(r)}"{focus}>'
            f"{self._stops(stops)}</radialGradient>"
        )
        return f"url(#{gid})"

    def vgrad(self, y1: float, y2: float, top: str, bottom: str, x: float = 0.0) -> str:
        return self.linear(x, y1, x, y2, [(0, top), (1, bottom)])

    # -- shapes ---------------------------------------------------------------------------
    @staticmethod
    def _paint(fill: Optional[str], stroke: Optional[str], width: float, opacity: float, join: str, cap: str,
               fill_opacity: float = 1.0) -> str:
        attrs = [f'fill="{fill or "none"}"']
        if fill_opacity < 1:
            attrs.append(f'fill-opacity="{_f(fill_opacity)}"')
        if stroke:
            attrs.append(f'stroke="{stroke}" stroke-width="{_f(width)}" stroke-linejoin="{join}" stroke-linecap="{cap}"')
        if opacity < 1:
            attrs.append(f'opacity="{_f(opacity)}"')
        return " ".join(attrs)

    def path(self, d: str, fill: Optional[str] = None, stroke: Optional[str] = None, width: float = 1.0,
             opacity: float = 1.0, join: str = "round", cap: str = "round", fill_opacity: float = 1.0) -> None:
        self._body.append(f'<path d="{d}" {self._paint(fill, stroke, width, opacity, join, cap, fill_opacity)}/>')

    def ellipse(self, cx: float, cy: float, rx: float, ry: float, fill: Optional[str] = None,
                stroke: Optional[str] = None, width: float = 1.0, opacity: float = 1.0) -> None:
        self._body.append(
            f'<ellipse cx="{_f(cx)}" cy="{_f(cy)}" rx="{_f(rx)}" ry="{_f(ry)}" '
            f'{self._paint(fill, stroke, width, opacity, "round", "round")}/>'
        )

    def circle(self, cx: float, cy: float, r: float, fill: Optional[str] = None, stroke: Optional[str] = None,
               width: float = 1.0, opacity: float = 1.0) -> None:
        self.ellipse(cx, cy, r, r, fill, stroke, width, opacity)

    def rect(self, x: float, y: float, w: float, h: float, fill: Optional[str] = None, stroke: Optional[str] = None,
             width: float = 1.0, rx: float = 0.0, opacity: float = 1.0) -> None:
        r = f' rx="{_f(rx)}" ry="{_f(rx)}"' if rx else ""
        self._body.append(
            f'<rect x="{_f(x)}" y="{_f(y)}" width="{_f(w)}" height="{_f(h)}"{r} '
            f'{self._paint(fill, stroke, width, opacity, "round", "round")}/>'
        )

    def polygon(self, points: Iterable[tuple[float, float]], fill: Optional[str] = None, stroke: Optional[str] = None,
                width: float = 1.0, opacity: float = 1.0) -> None:
        pts = " ".join(f"{_f(x)},{_f(y)}" for x, y in points)
        self._body.append(f'<polygon points="{pts}" {self._paint(fill, stroke, width, opacity, "round", "round")}/>')

    def line(self, x1: float, y1: float, x2: float, y2: float, stroke: str, width: float = 1.0, opacity: float = 1.0) -> None:
        self.path(f"M{_f(x1)} {_f(y1)}L{_f(x2)} {_f(y2)}", None, stroke, width, opacity)

    @contextmanager
    def group(self, transform: str = "", opacity: float = 1.0) -> Iterator[None]:
        attrs = []
        if transform:
            attrs.append(f'transform="{transform}"')
        if opacity < 1:
            attrs.append(f'opacity="{_f(opacity)}"')
        self._body.append(f"<g {' '.join(attrs)}>")
        try:
            yield
        finally:
            self._body.append("</g>")

    def raw(self, markup: str) -> None:
        self._body.append(markup)

    def to_bytes(self) -> bytes:
        head = (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {_f(self.w)} {_f(self.h)}" '
            f'width="{_f(self.w)}" height="{_f(self.h)}">'
        )
        defs = f"<defs>{''.join(self._defs)}</defs>" if self._defs else ""
        return (head + defs + "".join(self._body) + "</svg>").encode("utf-8")


# --------------------------------------------------------------------------- path helpers
def blob(cx: float, cy: float, rx: float, ry: float, wobble: float = 0.0, points: int = 12, seed: float = 0.0,
         squash_top: float = 1.0) -> str:
    """Smooth closed organic shape (Catmull-Rom through perturbed ellipse points)."""
    pts = []
    for i in range(points):
        a = 2 * math.pi * i / points
        k = 1 + wobble * math.sin(a * 3 + seed) * math.cos(a * 2 - seed * 1.7)
        y = math.sin(a) * ry * k
        if y < 0:
            y *= squash_top
        pts.append((cx + math.cos(a) * rx * k, cy + y))
    return smooth_closed(pts)


def smooth_closed(pts: Sequence[tuple[float, float]], tension: float = 1.0) -> str:
    n = len(pts)
    d = [f"M{_f(pts[0][0])} {_f(pts[0][1])}"]
    for i in range(n):
        p0, p1, p2, p3 = pts[(i - 1) % n], pts[i], pts[(i + 1) % n], pts[(i + 2) % n]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6 * tension, p1[1] + (p2[1] - p0[1]) / 6 * tension)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6 * tension, p2[1] - (p3[1] - p1[1]) / 6 * tension)
        d.append(f"C{_f(c1[0])} {_f(c1[1])} {_f(c2[0])} {_f(c2[1])} {_f(p2[0])} {_f(p2[1])}")
    return "".join(d) + "Z"


def smooth_open(pts: Sequence[tuple[float, float]], tension: float = 1.0) -> str:
    n = len(pts)
    d = [f"M{_f(pts[0][0])} {_f(pts[0][1])}"]
    for i in range(n - 1):
        p0 = pts[i - 1] if i > 0 else pts[i]
        p1, p2 = pts[i], pts[i + 1]
        p3 = pts[i + 2] if i + 2 < n else pts[i + 1]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6 * tension, p1[1] + (p2[1] - p0[1]) / 6 * tension)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6 * tension, p2[1] - (p3[1] - p1[1]) / 6 * tension)
        d.append(f"C{_f(c1[0])} {_f(c1[1])} {_f(c2[0])} {_f(c2[1])} {_f(p2[0])} {_f(p2[1])}")
    return "".join(d)


def star_points(cx: float, cy: float, outer: float, inner: float, n: int, rotation: float = -90.0) -> list[tuple[float, float]]:
    pts = []
    for i in range(n * 2):
        r = outer if i % 2 == 0 else inner
        a = math.radians(rotation + i * 180 / n)
        pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    return pts


def rounded_rect_path(x: float, y: float, w: float, h: float, r: float) -> str:
    r = min(r, w / 2, h / 2)
    return (
        f"M{_f(x + r)} {_f(y)}H{_f(x + w - r)}Q{_f(x + w)} {_f(y)} {_f(x + w)} {_f(y + r)}"
        f"V{_f(y + h - r)}Q{_f(x + w)} {_f(y + h)} {_f(x + w - r)} {_f(y + h)}H{_f(x + r)}"
        f"Q{_f(x)} {_f(y + h)} {_f(x)} {_f(y + h - r)}V{_f(y + r)}Q{_f(x)} {_f(y)} {_f(x + r)} {_f(y)}Z"
    )


class Rand:
    """Deterministic pseudo-random numbers so procedural art never flickers."""

    def __init__(self, seed: float) -> None:
        self.state = (int(seed * 9973) ^ 0x5DEECE66D) & 0xFFFFFFFF or 1

    def next(self) -> float:
        x = self.state
        x ^= (x << 13) & 0xFFFFFFFF
        x ^= x >> 17
        x ^= (x << 5) & 0xFFFFFFFF
        self.state = x & 0xFFFFFFFF
        return self.state / 0xFFFFFFFF

    def uniform(self, a: float, b: float) -> float:
        return a + (b - a) * self.next()

    def choice(self, seq):
        return seq[int(self.next() * len(seq)) % len(seq)]
