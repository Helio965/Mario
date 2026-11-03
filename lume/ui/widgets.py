"""Small immediate-mode UI helpers on the 960×540 canvas."""

from __future__ import annotations

from ..render.svg import Svg, rounded_rect_path, shade


def panel(scene, x: float, y: float, w: float, h: float, color: str = "#22304a", alpha: float = 0.86, border: str = "#ffffff",
          glow: bool = False) -> None:
    art = f"ui.panel2.{w:g}x{h:g}.{color}.{border}.{int(glow)}"
    if not scene.store.has(art):
        def build(w=w, h=h, color=color, border=border, glow=glow):
            s = Svg(w + 16, h + 16)
            if glow:
                s.path(rounded_rect_path(2, 2, w + 12, h + 12, 18), fill=None, stroke="#ffe27a", width=5, opacity=0.55)
            s.path(rounded_rect_path(8, 8, w, h, 14), fill=s.linear(0, 8, 0, h + 8, [(0, shade(color, 0.12)), (1, shade(color, -0.25))]),
                   stroke=border, width=1.6, opacity=1.0)
            s.path(rounded_rect_path(10, 10, w - 4, h * 0.42, 12), fill="#ffffff", opacity=0.06)
            return s
        scene._canvas_spec(art, build, group="ui")
    scene.draw_canvas(art, x - 8, y - 8, w + 16, h + 16, alpha=alpha)


def button(scene, label: str, x: float, y: float, w: float, h: float, selected: bool, enabled: bool = True,
           sub: str = "") -> None:
    color = "#2f6f9a" if selected else "#24324c"
    panel(scene, x, y, w, h, color, 0.95 if enabled else 0.55, "#ffe9a8" if selected else "#9fb4cc", glow=selected)
    tc = (255, 255, 255) if enabled else (150, 160, 175)
    scene.text.draw(label, x + w / 2, y + h / 2 - (13 if sub else 11), 20 if not sub else 18, tc, "display", "center")
    if sub:
        scene.text.draw(sub, x + w / 2, y + h / 2 + 6, 12, (200, 214, 230) if enabled else (140, 150, 160), "ui", "center")
