"""Constantes de apresentação e utilidades de configuração.

A simulação roda em um mundo de 960 × 540 "pixels de jogo"; a janela escala
essa superfície (``pygame.SCALED``) para qualquer resolução, inclusive 1080p.
"""

from __future__ import annotations

VIEW_WIDTH = 960
VIEW_HEIGHT = 540
WINDOW_TITLE = "Lume — As Cinco Fronteiras"
TARGET_FPS = 60
MAX_FRAME_TIME = 0.25

QUALITY_LEVELS = ("high", "medium", "low")
SCALE_OPTIONS = (0, 1, 2, 3, 4)  # 0 = ajustar à janela
FPS_OPTIONS = (30, 60, 120, 144, 0)  # 0 = sem limite
