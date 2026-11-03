"""Mapa da aventura: progresso, relíquias, cinco cartões de mundo com as cores
do tema e três nós de fase cada (bloqueado, disponível, atual, concluído),
recordes, relíquias por fase e conquistas desbloqueadas.
"""

from __future__ import annotations

import math
from functools import partial
from typing import Literal

import pygame

from game.settings import VIEW_WIDTH
from game.systems.progression import ACHIEVEMENT_IDS
from game.ui.screens import MARGIN, PanelScreen
from game.ui.theme import RGB, Style, mix, rgb
from game.ui.widgets import Layer, Widget

NodeState = Literal["locked", "available", "current", "completed"]
NODE_HEIGHT = 44
NODE_GAP = 5
ART_HEIGHT = 62
CARD_GAP = 12


def _fit(style: Style, text: str, size: int, bold: bool, max_width: int) -> str:
    """Corta ``text`` com reticências para caber em ``max_width``."""
    if style.measure(text, size, bold)[0] <= max_width:
        return text
    while len(text) > 1 and style.measure(text + "…", size, bold)[0] > max_width:
        text = text[:-1]
    return text.rstrip() + "…"


def _rotated(cx: float, cy: float, w: float, h: float, degrees: float) -> list[tuple[int, int]]:
    angle = math.radians(degrees)
    cos, sin = math.cos(angle), math.sin(angle)
    points = []
    for dx, dy in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)):
        points.append((round(cx + dx * cos - dy * sin), round(cy + dx * sin + dy * cos)))
    return points


class StageNode(Widget):
    """Nó de fase dentro de um cartão de mundo."""

    def __init__(
        self,
        rect: pygame.Rect,
        number: str,
        title: str,
        subtitle: str,
        state: NodeState,
        relic: bool,
        on_activate: partial[None],
        *,
        widget_id: str,
    ) -> None:
        super().__init__(rect, on_activate, widget_id=widget_id, enabled=state != "locked")
        self.focusable = state != "locked"
        self.number = number
        self.title = title
        self.subtitle = subtitle
        self.state: NodeState = state
        self.relic = relic

    def draw(
        self,
        surface: pygame.Surface,
        style: Style,
        origin: tuple[int, int],
        focused: bool,
        hovered: bool,
    ) -> None:
        p = style.palette
        r = self.rect.move(origin)
        locked = self.state == "locked"

        def fade(color: RGB) -> RGB:
            return mix(color, p.card, 0.56) if locked else color

        fills: dict[NodeState, RGB] = {
            "locked": p.node,
            "available": p.node,
            "current": p.node_current,
            "completed": p.node_cleared,
        }
        fill = fills[self.state]
        border: RGB | None = p.node_current_border if self.state == "current" else None
        if (hovered or focused) and self.enabled:
            fill = p.node_hover
            border = p.node_hover_border
        style.round_rect(surface, r, fade(fill), 4, border=fade(border) if border else None)
        box = pygame.Rect(r.x + 5, r.centery - 13, 26, 27)
        if self.state == "current":
            style.round_rect(surface, box, p.node_number_current, 4)
            number = style.text(self.number, 10, p.knob, True)
            surface.blit(number, number.get_rect(center=box.center))
        else:
            style.round_rect(surface, box, fade(p.node_number), 4)
            if self.state == "completed":
                icon = style.icon("check", 14, p.node_number_text)
                surface.blit(icon, icon.get_rect(center=box.center))
            elif locked:
                icon = style.icon("lock", 14, fade(p.node_number_text))
                surface.blit(icon, icon.get_rect(center=box.center))
            else:
                number = style.text(self.number, 10, p.node_number_text, True)
                surface.blit(number, number.get_rect(center=box.center))
        tx = box.right + 6
        max_w = r.right - 24 - tx
        title = style.text(_fit(style, self.title, 9, True, max_w), 9, fade(p.node_text), True)
        sub = style.text(_fit(style, self.subtitle, 8, False, max_w), 8, fade(p.node_sub))
        top = r.centery - (title.get_height() + sub.get_height() + 2) // 2
        surface.blit(title, (tx, top))
        surface.blit(sub, (tx, top + title.get_height() + 2))
        relic = style.icon("sparkle", 13, fade(p.relic_found if self.relic else p.relic_missing))
        surface.blit(relic, relic.get_rect(center=(r.right - 12, r.centery)))
        if focused:
            style.focus_ring(surface, r, 4)


class MapScreen(PanelScreen):
    name = "map"
    label_key = "screens.map.label"
    title_key = "screens.map.title"
    max_width = VIEW_WIDTH - 2 * MARGIN
    pad_x = 23
    pad_y = 23

    def content(self, layer: Layer, width: int, y: int) -> int:
        ui = self.ui
        style = self.style
        p = style.palette
        t = ui.t
        save = ui.save
        levels = ui.levels
        total = max(1, len(levels))
        done = len([level for level in levels if level.id in save.completed])
        percent = math.floor(done / total * 100 + 0.5)
        # Resumo: porcentagem, trilha de progresso e relíquias.
        progress = layer.text(0, y, t("map.progress", percent=percent), 10, p.body, bold=True)
        relics = t("map.relics", count=len(save.relics), total=total)
        relics_w = style.measure(relics, 10)[0]
        track = pygame.Rect(progress.right + 18, y + 6, width - progress.w - relics_w - 76, 5)
        layer.box(track, p.track, radius=3)
        layer.box(
            pygame.Rect(track.x, track.y, round(track.w * percent / 100), 5), p.track_fill, radius=3
        )
        layer.icon(track.right + 16, y + 8, "star", 14, p.section_icon, anchor="midleft")
        layer.text(width, y, relics, 10, p.body, anchor="topright")
        y += 26
        # Cartões de mundo.
        worlds = sorted({level.world for level in levels})
        count = max(1, len(worlds))
        card_w = (width - CARD_GAP * (count - 1)) // count
        bottom = y
        for column, world in enumerate(worlds):
            x = column * (card_w + CARD_GAP)
            bottom = max(bottom, self.card(layer, x, y, card_w, world))
        y = bottom + 17
        # Conquistas.
        layer.line((0, y), (width, y), p.line)
        y += 14
        layer.icon(0, y + 8, "trophy", 14, p.section_icon, anchor="midleft")
        header = layer.text(20, y + 2, t("map.achievements"), 8, p.eyebrow, bold=True, spacing=1)
        counter = t(
            "map.achievements_count", count=len(save.achievements), total=len(ACHIEVEMENT_IDS)
        )
        count_rect = layer.text(header.right + 6, y + 1, counter, 9, p.chip_text, bold=True)
        x = count_rect.right + 20
        if save.achievements:
            row_y = y
            for achievement in save.achievements:
                name = ui.achievement_name(achievement)
                chip_w = 7 + 11 + 4 + style.measure(name, 8)[0] + 7
                if x + chip_w > width and x > count_rect.right + 20:
                    x = count_rect.right + 20
                    row_y += 22
                layer.box(pygame.Rect(x, row_y, chip_w, 18), p.chip, radius=3)
                layer.icon(x + 7, row_y + 9, "check", 11, p.chip_text, anchor="midleft")
                layer.text(x + 22, row_y + 9, name, 8, p.chip_text, anchor="midleft")
                x += chip_w + 5
            y = row_y + 18
        else:
            layer.text(x, y + 1, t("map.no_achievements"), 9, p.note)
            y += 18
        return y + 6

    def card(self, layer: Layer, x: int, y: int, w: int, world: int) -> int:
        ui = self.ui
        style = self.style
        p = style.palette
        t = ui.t
        save = ui.save
        theme = ui.theme_for_world(world)
        stages = [(index, level) for index, level in enumerate(ui.levels) if level.world == world]
        first_index = stages[0][0] if stages else 0
        world_locked = first_index > save.unlocked
        subtitle_lines = style.wrap(ui.theme_subtitle(world), 9, w - 22)[:2]
        text_h = 13 + 16 + max(2, len(subtitle_lines)) * 13 + 8
        nodes_h = len(stages) * (NODE_HEIGHT + NODE_GAP) + 2
        card = pygame.Rect(x, y, w, ART_HEIGHT + text_h + nodes_h)
        layer.box(card, p.card, radius=7, border=p.card_border)
        # Arte do mundo: céu do tema, duas formas inclinadas e o sol/acento.
        art = pygame.Rect(x + 1, y + 1, w - 2, ART_HEIGHT)
        sky = rgb(theme.sky)
        near = rgb(theme.near)
        accent = rgb(theme.accent)
        if style.high_contrast:
            sky = mix(sky, (255, 255, 255), 0.3)
        layer.clip(art)
        layer.box(art, sky, radius=6)
        layer.polygon(
            _rotated(art.x + art.w * 0.3, art.bottom + 4, art.w * 0.75, art.h * 0.8, -24),
            mix(near, sky, 0.4),
        )
        layer.polygon(
            _rotated(art.right - art.w * 0.25, art.bottom - 2, art.w * 0.75, art.h * 0.8, 29), near
        )
        layer.circle((art.x + round(art.w * 0.54), art.y + 20), 10, mix(accent, sky, 0.2))
        layer.clip(None)
        layer.text(
            art.x + 11,
            art.y + 9,
            t("map.world_number", world=world),
            11,
            mix((255, 255, 255), sky, 0.15),
            bold=True,
            spacing=2,
        )
        layer.icon(
            art.right - 12,
            art.bottom - 11,
            "lock" if world_locked else "star",
            18,
            accent if not style.high_contrast else p.ink,
            anchor="bottomright",
        )
        ty = art.bottom + 13
        layer.text(
            x + 11, ty, _fit(style, ui.theme_name(world), 12, True, w - 22), 12, p.ink, bold=True
        )
        ty += 16
        for line in subtitle_lines:
            layer.text(x + 11, ty, line, 9, p.note)
            ty += 13
        ny = y + ART_HEIGHT + text_h
        for index, level in stages:
            unlocked = index <= save.unlocked
            completed = level.id in save.completed
            if not unlocked:
                state: NodeState = "locked"
            elif completed:
                state = "completed"
            elif index == save.unlocked:
                state = "current"
            else:
                state = "available"
            record = save.records.get(level.id, 0)
            if record:
                subtitle = t("map.node.record", score=ui.format_score(record))
            elif state == "current":
                subtitle = t("map.node.next")
            elif unlocked:
                subtitle = t("map.node.again")
            else:
                subtitle = t("map.node.locked_hint")
            self.group.add(
                StageNode(
                    pygame.Rect(x + 7, ny, w - 14, NODE_HEIGHT),
                    f"{level.world}-{level.stage}",
                    ui.level_name(level),
                    subtitle,
                    state,
                    level.id in save.relics,
                    partial(self.select, index),
                    widget_id=f"level-{index}",
                )
            )
            ny += NODE_HEIGHT + NODE_GAP
        return card.bottom

    def select(self, index: int) -> None:
        if 0 <= index <= self.ui.save.unlocked:
            self.ui.handlers.play(index)
