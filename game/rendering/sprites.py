"""Sprites procedurais (port de ``src/render/sprites.ts``).

``Sprites(painter)`` com ``coin(coin)``, ``item(item)``, ``player(player)``,
``enemy(enemy)`` (incluindo ``boss``) reproduzindo o desenho original —
membros animados, cachecol, poses aéreas, barra de vida do guardião e
variantes por mundo. Aceita as dataclasses de ``game.core.types``.

Arquétipos modernos (``game/enemies``): um inimigo é guardião quando
``kind == "boss"`` ou quando seu ``behavior.is_boss`` é verdadeiro
(ex.: ``"guardian"``); qualquer outro tipo sem desenho próprio (ex.:
``"stalker"``) usa o corpo do andarilho, nunca o guardião com barra de vida.
``enemy.telegraph`` (ataque iminente) mostra um "!" pulsando sobre a cabeça.

Toda a geometria é expressa no espaço local do sprite e levada à tela pela
pilha de transformações do ``Painter`` (translate + scale espelhando pelo
``facing`` + rotate quando morto), exatamente como o Canvas original.
"""

from __future__ import annotations

import math

from game.core.jsmath import js_round
from game.core.types import Coin, Enemy, Item, Player
from game.rendering.painter import GOLD, INK, Painter

STAR_COLORS = ("#8be9d0", "#ffe396", "#dba4d8", "#c8e8ff")

# Matriz 16 × 18 do tronco e cabeça; pernas, braço e cachecol são membros à parte.
PLAYER_UPPER = (
    ".......KKK......",
    "......KHHHK.....",
    ".....KHHHHHK....",
    "....KHHLLHHHK...",
    "...KHHHHHHHHHK..",
    "..KKKKKKKKKKKK..",
    "....KRRRSSSK....",
    "....KRSSSESK....",
    ".....KSSSSSSK...",
    ".....KRSSSSK....",
    "....KTTTTTTTK...",
    "...KTTTTATTTTK..",
    "..KBJJTTTJJJBK..",
    "..KBJJJJJJJJBK..",
    "...KJJJWWJJJK...",
    "...KJJBBJJJJK...",
    "....KDDDDDDK....",
    ".....KDDDDK.....",
)

_BASE_PALETTE = {
    "K": INK,
    "H": "#dda66a",
    "L": "#f4d391",
    "R": "#b96458",
    "S": "#f3b99a",
    "E": "#203643",
    "T": "#62ccb9",
    "B": "#a57c68",
    "D": "#466b79",
    "W": "#ffdfb0",
    "A": "#a0e5d0",
}
PLAYER_PALETTE = {**_BASE_PALETTE, "J": "#ddc394"}
PLAYER_PALETTE_FIRE = {**_BASE_PALETTE, "J": "#d98a62"}

# (armadura, painel, friso, rosto, gema) por mundo; fora da faixa usa o último.
BOSS_PALETTES = (
    ("#527e68", "#719582", "#c7bc8b", "#9dbe8e", "#f1cc6f"),
    ("#b88b61", "#d0aa75", "#f4d49a", "#dec3a0", "#72dac5"),
    ("#6f9cac", "#a3cbd4", "#d4f1ed", "#c1dce0", "#d9a4d7"),
    ("#826e9f", "#a38aaa", "#c5aec9", "#b8a5bc", "#9de0b8"),
    ("#8b6979", "#aa7e84", "#ce9a8c", "#b58b83", "#71cfbf"),
)
BOSS_PALETTE_DEFAULT = ("#8b6979", "#aa7e84", "#ce9a8c", "#b58b83", "#71cfbf")

# Marcador "!" do telegraph (preparação visível de ataque) dos arquétipos modernos.
TELEGRAPH_MARK = (".##.", "#oo#", "#oo#", "#oo#", "#oo#", ".##.", ".##.", "#oo#", ".##.")
TELEGRAPH_PALETTE = {"#": INK, "o": "#ffe5a0"}


class Sprites:
    """Sprites de matriz feitos à mão, com membros animados independentes."""

    def __init__(self, painter: Painter) -> None:
        self._painter = painter

    # moedas e relíquias -------------------------------------------------------
    def coin(self, coin: Coin) -> None:
        painter = self._painter
        frame = painter.scene.frame
        rect = painter.rect
        polygon = painter.polygon
        phase = frame * 6 + coin.x / 45
        x = coin.x + coin.w / 2
        y = coin.y + coin.h / 2 + math.sin(frame * 2 + coin.x / 90) * 2
        if coin.special:
            lift = math.sin(frame * 3) * 2
            rect(x - 17, y - 6 + lift, 34, 12, "#596b79")
            polygon(
                [
                    x - 17,
                    y - 6 + lift,
                    x - 25,
                    y - 12 + lift,
                    x - 21,
                    y + 4 + lift,
                    x - 8,
                    y + 8 + lift,
                ],
                "#a5d7c2",
            )
            polygon(
                [
                    x + 17,
                    y - 6 + lift,
                    x + 25,
                    y - 12 + lift,
                    x + 21,
                    y + 4 + lift,
                    x + 8,
                    y + 8 + lift,
                ],
                "#a5d7c2",
            )
            polygon(
                [x, y - 19 + lift, x + 13, y + lift, x, y + 19 + lift, x - 13, y + lift], "#253b51"
            )
            polygon(
                [x, y - 16 + lift, x + 10, y + lift, x, y + 16 + lift, x - 10, y + lift], "#62dfc1"
            )
            polygon(
                [x, y - 12 + lift, x + 5, y + lift, x, y + 5 + lift, x - 5, y + lift], "#ddffe0"
            )
            rect(x - 2, y + 8 + lift, 4, 4, "#36a9a5")
            painter.sparkle(
                x + math.sin(phase / 2) * 25, y + math.cos(phase / 2) * 21, 3, "#dcf7c9"
            )
            return
        half = max(2, js_round(abs(math.cos(phase)) * max(5, coin.w / 2)))
        polygon(
            [
                x - half + 2,
                y - 9,
                x + half - 2,
                y - 9,
                x + half,
                y - 6,
                x + half,
                y + 6,
                x + half - 2,
                y + 9,
                x - half + 2,
                y + 9,
                x - half,
                y + 6,
                x - half,
                y - 6,
            ],
            "#b28044",
        )
        rect(x - half + 1, y - 6, max(2, half * 2 - 2), 12, GOLD)
        if half > 3:
            rect(x - half + 2, y - 5, 2, 9, "#fff1b8")
            rect(x + 1, y - 4, 2, 8, "#d6a052")

    # itens -------------------------------------------------------------------
    def item(self, item: Item) -> None:
        painter = self._painter
        rect = painter.rect
        polygon = painter.polygon
        painter.save()
        painter.translate(js_round(item.x + item.w / 2), js_round(item.y + item.h / 2))
        scale = min(item.w, item.h) / 24
        painter.scale(scale, scale)
        if item.kind == "grow":
            polygon([-11, -3, -7, -8, 6, -9, 11, -4, 10, 7, 5, 11, -6, 11, -11, 5], "#253d4d")
            polygon([-8, -3, -5, -6, 5, -6, 8, -2, 7, 7, 3, 9, -5, 8, -8, 4], "#e8877b")
            rect(-5, -3, 3, 5, "#ffbf94")
            rect(3, 2, 3, 5, "#b45868")
            rect(0, -12, 3, 7, "#558977")
            polygon([2, -9, 7, -13, 11, -11, 6, -8], "#a0d190")
        elif item.kind == "fire":
            rect(-8, -7, 16, 17, "#304151")
            rect(-6, -5, 12, 13, "#d58f52")
            rect(-3, 9, 6, 3, "#725763")
            polygon([-3, 5, -5, 0, -2, -7, 0, -4, 3, -13, 6, -3, 5, 3, 2, 6], "#ffd277")
            rect(-1, 1, 3, 5, "#fff3b4")
            rect(-9, -8, 18, 3, "#92b19c")
            rect(-7, -13, 3, 6, "#92b19c")
            rect(4, -13, 3, 6, "#92b19c")
            rect(-4, -14, 8, 3, "#92b19c")
        elif item.kind == "star":
            painter.sparkle(0, 0, 12, "#ae8755")
            painter.sparkle(0, -1, 9, "#ffe5a0")
            painter.sparkle(-1, -2, 4, "#fffbd7")
        else:
            polygon(
                [-11, -6, -6, -10, -1, -8, 1, -8, 6, -10, 11, -6, 11, 0, 0, 12, -11, 0], "#613a53"
            )
            polygon([-8, -5, -5, -7, 0, -3, 5, -7, 8, -5, 8, -1, 0, 8, -8, -1], "#f58b8d")
            rect(-5, -5, 3, 3, "#ffd2b0")
        painter.restore()

    # jogador -------------------------------------------------------------------
    def player(self, player: Player) -> None:
        painter = self._painter
        scene = painter.scene
        frame = scene.frame
        if player.invulnerable > 0 and player.star <= 0 and math.floor(frame * 15) % 2 == 0:
            return
        rect = painter.rect
        running = player.animation == "run"
        moving = player.animation == "walk" or running
        airborne = player.animation == "jump" or player.animation == "fall"
        stride = math.sin(frame * (24 if running else 15)) if moving else 0.0
        unit = player.h / 25
        painter.save()
        painter.translate(js_round(player.x + player.w / 2), js_round(player.y + player.h))
        if player.animation == "dead":
            painter.rotate(math.sin(frame * 8) * 0.2)
        painter.scale(-unit if player.facing < 0 else unit, unit)
        painter.translate(-8, -25 + (abs(stride) * -0.6 if moving else 0))
        if player.star > 0:
            color = STAR_COLORS[math.floor(frame * 8) % 4]
            painter.set_alpha(0.28)
            rect(1, 2, 15, 20, color)
            painter.set_alpha(1)
            painter.sparkle(18 + math.sin(frame * 11) * 3, 8 + math.cos(frame * 11) * 7, 2, color)
            painter.sparkle(-2, 13 + math.sin(frame * 8) * 6, 2, color)
        palette = PLAYER_PALETTE_FIRE if player.power == "fire" else PLAYER_PALETTE
        painter.sprite(PLAYER_UPPER, palette, 0, 0, 1)
        # Cachecol, braços e pés se movem de forma independente, com poses aéreas próprias.
        scarf_y = 11 + math.sin(frame * 11) * 0.5
        run_offset = 3 if running else 0
        painter.polygon(
            [4, 10, -2 - run_offset, scarf_y, -3 - run_offset, scarf_y + 3, 3, 12], palette["T"]
        )
        rect(-2 - run_offset, scarf_y + 1, 2, 1, palette["A"])
        if player.power == "fire":
            rect(-3 - run_offset, scarf_y - 1, 2, 2, "#fff1a3")
        back_leg = -3 if airborne else stride * 3
        front_leg = 3 if airborne else -stride * 3
        self.limb(6, 17, back_leg, 3 if airborne else 5, "#355463", "#694e51")
        self.limb(10, 17, front_leg, 6 if airborne else 5, "#4f7c86", "#8d6260")
        if player.animation == "win":
            self.limb(12, 12, 4, -7, "#ddc394", "#f3b99a")
            painter.sparkle(17, 4, 2, GOLD)
        elif player.animation == "hurt" or player.animation == "dead":
            self.limb(12, 12, 5, -3, palette["J"], palette["S"])
        elif airborne:
            self.limb(
                12, 12, 2, -4 if player.animation == "jump" else 2, palette["J"], palette["S"]
            )
        else:
            self.limb(12, 12, -stride * 2, 4, palette["J"], palette["S"])
        rect(8, 6, 3, 1, palette["W"])
        painter.restore()
        if (
            scene.effects
            and player.grounded
            and abs(player.vx) > 210
            and math.floor(frame * 12) % 2 == 0
        ):
            painter.set_alpha(0.45)
            rect(
                player.x + (-7 if player.facing > 0 else player.w + 4),
                player.y + player.h - 4,
                6,
                3,
                "#d5cab5",
            )
            painter.set_alpha(1)

    def limb(self, x: float, y: float, dx: float, dy: float, cloth: str, end: str) -> None:
        """Membro articulado: haste com contorno e extremidade (pé/mão) na ponta."""
        painter = self._painter
        painter.save()
        painter.translate(x, y)
        painter.rotate(-math.atan2(dx, dy))
        length = abs(dy)
        painter.rect(-2, 0, 4, length + 1, INK)
        painter.rect(-1, 0, 2, length, cloth)
        painter.rect(-2, length - 1, 6, 3, INK)
        painter.rect(-1, length - 1, 4, 2, end)
        painter.restore()

    # inimigos ------------------------------------------------------------------
    def enemy(self, enemy: Enemy) -> None:
        painter = self._painter
        frame = painter.scene.frame
        rect = painter.rect
        polygon = painter.polygon
        # Guardião: tipo legado "boss" ou arquétipo moderno marcado como chefe (``is_boss``).
        is_boss = enemy.kind == "boss" or bool(getattr(enemy.behavior, "is_boss", False))
        painter.save()
        painter.translate(js_round(enemy.x + enemy.w / 2), js_round(enemy.y + enemy.h))
        painter.scale(-1 if enemy.facing < 0 else 1, 1)
        s = min(enemy.w / 28, enemy.h / 26)
        if not is_boss:
            painter.scale(s, s)
        if enemy.hit_timer > 0 and math.floor(frame * 18) % 2 == 0:
            painter.set_alpha(0.45)
        gait = math.sin(frame * 12 + enemy.x)
        if is_boss:
            self.boss(enemy, gait)
        elif enemy.kind == "shell":
            if enemy.state == "walk":
                rect(-10 + gait, -4, 7, 4, "#614b50")
                rect(6 - gait, -4, 7, 4, "#614b50")
                rect(6, -14, 9, 8, "#cfa987")
                rect(11, -14, 3, 3, "#293a43")
                rect(15, -10, 4, 3, "#cfa987")
            polygon([-14, -5, -14, -14, -8, -24, 3, -27, 10, -22, 13, -10, 11, -5], "#343c49")
            polygon([-11, -7, -11, -14, -6, -21, 2, -24, 8, -20, 10, -10, 8, -7], "#b99868")
            for i in range(3):
                rect(
                    -8 + i * 6, -19 - (3 if i == 1 else 0), 2, 11 + (3 if i == 1 else 0), "#7d6a63"
                )
                rect(-6 + i * 6, -18, 2, 3, "#ead3a0")
            if enemy.state == "slide":
                rect(-20, -8, 5, 2, "#e6c891")
                rect(-24, -4, 8, 2, "#bfa887")
        elif enemy.kind == "flyer":
            flap = math.sin(frame * 16) * 6
            polygon(
                [-5, -12, -10, -24 + flap, -21, -29 + flap, -19, -11 + flap, -11, -8, -6, -4],
                "#41374f",
            )
            polygon([-7, -12, -11, -21 + flap, -18, -23 + flap, -16, -12 + flap], "#ac7aa4")
            polygon(
                [4, -13, 13, -24 + flap, 22, -29 + flap, 20, -12 + flap, 13, -7, 5, -4], "#41374f"
            )
            polygon([7, -12, 13, -21 + flap, 18, -23 + flap, 17, -12 + flap], "#b786ad")
            rect(-5, -18, 11, 14, "#766083")
            rect(-5, -22, 3, 5, "#41374f")
            rect(3, -22, 3, 5, "#41374f")
            rect(-3, -14, 3, 4, "#ffe5a0")
            rect(3, -14, 3, 4, "#ffe5a0")
            rect(-2, -13, 1, 2, "#373547")
            rect(4, -13, 1, 2, "#373547")
            rect(0, -8, 3, 3, "#d5a3a4")
        elif enemy.kind == "shooter":
            rect(-11, -5, 22, 5, "#3b4f4d")
            rect(-8, -23, 16, 22, "#3c7064")
            rect(-6, -21, 4, 17, "#739e77")
            rect(1, -21, 3, 16, "#285c59")
            rect(-14, -17, 6, 9, "#3c7064")
            rect(-15, -21, 6, 5, "#769e7a")
            rect(7, -16, 7, 5, "#537e65")
            rect(12, -18, 5, 9, "#233d49")
            rect(13, -16, 4, 5, "#c9b386")
            polygon([-10, -24, -8, -30, -2, -27, 1, -33, 5, -27, 10, -29, 11, -23], "#d48799")
            rect(-7, -24, 17, 5, "#a76583")
            rect(3, -20, 3, 3, "#f5d99d")
        elif enemy.kind == "armored":
            rect(-11 + gait, -5, 8, 5, "#3e4754")
            rect(4 - gait, -5, 8, 5, "#3e4754")
            polygon([-15, -6, -15, -18, -9, -29, 5, -31, 14, -21, 15, -6], "#303f50")
            polygon([-11, -8, -12, -17, -7, -26, 4, -27, 11, -19, 11, -8], "#8c9eaa")
            rect(-8, -23, 9, 4, "#bec2b5")
            rect(-2, -19, 2, 10, "#697c8d")
            rect(4, -18, 8, 3, "#344a58")
            rect(5, -17, 5, 2, "#f6c776")
            polygon([-9, -26, -10, -34, -4, -30, 2, -34, 5, -29], "#b9bdae")
            rect(-16, -13, 5, 9, "#667e8b")
        else:
            # "walker" e qualquer arquétipo terrestre sem desenho próprio (ex.: "stalker").
            self._walker(gait)
        painter.restore()
        if enemy.telegraph:
            self._telegraph(enemy, frame, is_boss)

    def _walker(self, gait: float) -> None:
        """Andarilho: três patas animadas, casco em duas camadas, cabeça e antenas."""
        painter = self._painter
        rect = painter.rect
        polygon = painter.polygon
        for i in (-1, 0, 1):
            rect(i * 8 - 4 + gait * i, -5, 5, 5, "#493648")
            rect(i * 8 - 3 + gait * i, -3, 6, 3, "#624b5a")
        polygon([-14, -9, -13, -18, -7, -24, 5, -24, 11, -19, 13, -9], "#403545")
        polygon([-11, -10, -10, -17, -5, -21, 4, -21, 9, -17, 10, -10], "#c78076")
        rect(-7, -18, 6, 3, "#e8ab85")
        rect(-1, -19, 2, 11, "#884f67")
        rect(7, -13, 8, 8, "#dbb297")
        rect(10, -13, 3, 4, "#28394b")
        rect(10, -14, 3, 1, "#fae2b6")
        rect(13, -8, 4, 2, "#433245")
        rect(-9, -25, 2, 4, "#2e404a")
        rect(5, -25, 2, 4, "#2e404a")

    def _telegraph(self, enemy: Enemy, frame: float, is_boss: bool) -> None:
        """Sinal de ataque iminente: "!" dourado pulsando acima da cabeça (e da barra de vida).

        Desenhado no espaço da câmera (sem espelho nem escala do corpo) para
        ficar sempre legível; guardiões recebem o marcador em dobro.
        """
        unit = 2 if is_boss else 1
        bob = js_round(math.sin(frame * 10))
        x = enemy.x + enemy.w / 2 - 2 * unit
        y = enemy.y - 14 * unit - 8 + bob
        self._painter.sprite(TELEGRAPH_MARK, TELEGRAPH_PALETTE, x, y, unit)

    def boss(self, enemy: Enemy, gait: float) -> None:
        """Guardião: corpo escalado para ``w × h`` sobre a base 76 × 84 e barra de vida."""
        painter = self._painter
        world = painter.scene.world
        rect = painter.rect
        polygon = painter.polygon
        armor, panel, trim, face, gem = (
            BOSS_PALETTES[world - 1] if 1 <= world <= len(BOSS_PALETTES) else BOSS_PALETTE_DEFAULT
        )
        painter.save()
        painter.scale(enemy.w / 76, enemy.h / 84)
        rect(-25 + gait * 2, -10, 18, 10, "#263b4c")
        rect(13 - gait * 2, -10, 19, 10, "#263b4c")
        rect(-22 + gait * 2, -7, 14, 4, trim)
        rect(17 - gait * 2, -7, 14, 4, trim)
        polygon([-34, -17, -34, -49, -23, -66, 15, -69, 32, -53, 37, -22, 27, -13], "#293746")
        polygon([-29, -20, -28, -48, -19, -60, 13, -62, 28, -51, 31, -24, 24, -18], armor)
        rect(-20, -55, 11, 30, panel)
        rect(-5, -58, 11, 32, panel)
        rect(10, -55, 11, 30, panel)
        rect(-21, -51, 41, 4, trim)
        rect(-24, -24, 50, 5, "#504a61")
        rect(-11, -37, 24, 13, "#514761")
        painter.sparkle(1, -33, 8, gem)
        painter.sparkle(1, -34, 4, "#e4ffe0")
        polygon(
            [
                -24, -57, -28, -77, -19, -73, -13, -84, -8, -76, 13, -76, 20, -84, 22, -71, 31,
                -77, 30, -58,
            ],
            "#293746",
        )  # fmt: skip
        rect(-15, -73, 35, 24, face)
        rect(-10, -68, 13, 4, "#4c4058")
        rect(9, -68, 12, 4, "#4c4058")
        rect(-7, -66, 8, 3, "#ffe3a2")
        rect(11, -66, 7, 3, "#ffe3a2")
        rect(1, -63, 9, 9, armor)
        rect(-7, -53, 26, 4, "#433e51")
        rect(-4, -53, 4, 3, "#dfd6b6")
        rect(12, -53, 4, 3, "#dfd6b6")
        rect(-39, -49, 13, 28, "#574b63")
        rect(-38, -46, 10, 6, panel)
        rect(28, -46, 15, 26, "#574b63")
        rect(32, -42, 9, 9, face)
        for i in range(3):
            rect(30 + i * 4, -23, 3, 6, "#e0c29c")
        if world == 1:
            polygon([-26, -61, -34, -72, -30, -83, -21, -74], "#9dc191")
            polygon([25, -61, 33, -74, 27, -84, 20, -72], "#9dc191")
        elif world == 2:
            rect(-23, -76, 50, 5, trim)
            for i in range(4):
                rect(-19 + i * 12, -71, 4, 12, armor)
        elif world == 3:
            polygon([-37, -49, -40, -63, -31, -58, -23, -69, -24, -48], trim)
            polygon([26, -46, 26, -64, 34, -57, 41, -64, 43, -46], trim)
        elif world == 4:
            painter.sparkle(-30, -69, 5, gem)
            painter.sparkle(30, -73, 6, gem)
        else:
            polygon([-24, -71, -26, -81, -21, -94, -18, -85, -13, -90, -13, -75], "#e99a69")
            polygon([18, -74, 19, -86, 24, -94, 26, -84, 30, -88, 29, -72], "#e99a69")
        painter.restore()
        painter.save()
        painter.scale(-1 if enemy.facing < 0 else 1, 1)
        rect(-enemy.w / 2, -enemy.h - 15, enemy.w, 5, "#253744")
        rect(
            -enemy.w / 2 + 1,
            -enemy.h - 14,
            max(0, ((enemy.w - 2) * enemy.health) / (enemy.hp or 8)),
            3,
            "#e6a07d",
        )
        painter.restore()
