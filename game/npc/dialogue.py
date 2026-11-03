"""Sistema de diálogos, legendas e reações contextuais.

* ``Dialogue``/``Line``: roteiros declarativos (``data/dialogues/*.json``) com
  falante, expressão, gesto, voz opcional e texto localizado (chave do
  arquivo de localização ou texto por idioma).
* ``DialogueRunner``: avança linha a linha com efeito de máquina de escrever,
  avanço automático opcional, pular, sincronização com animação (``talking``)
  e legenda ativa.
* ``ReactionBank``: falas curtas por contexto (dano, pisão, relíquia, vitória…)
  escolhidas sem repetição imediata, para personagens expressivos.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from game.paths import data_path
from game.systems.localization import Localization

CHARS_PER_SECOND = 38.0
MIN_LINE_SECONDS = 1.2
SECONDS_PER_CHAR_AFTER = 0.045


@dataclass(slots=True)
class Line:
    speaker: str
    key: str | None = None
    text: dict[str, str] | None = None
    expression: str = "neutral"
    gesture: str | None = None
    voice: str | None = None
    duration: float | None = None  # auto quando None
    condition: str | None = None  # nome de flag que precisa ser verdadeira


@dataclass(slots=True)
class Dialogue:
    id: str
    lines: list[Line]
    skippable: bool = True
    auto_advance: bool = False
    on_end: str | None = None  # flag marcada ao terminar


def line_from_dict(d: dict[str, Any]) -> Line:
    return Line(
        speaker=str(d["speaker"]),
        key=d.get("key"),
        text=d.get("text"),
        expression=str(d.get("expression", "neutral")),
        gesture=d.get("gesture"),
        voice=d.get("voice"),
        duration=d.get("duration"),
        condition=d.get("if"),
    )


def dialogue_from_dict(d: dict[str, Any]) -> Dialogue:
    return Dialogue(
        id=str(d["id"]),
        lines=[line_from_dict(line) for line in d.get("lines", [])],
        skippable=bool(d.get("skippable", True)),
        auto_advance=bool(d.get("auto_advance", False)),
        on_end=d.get("on_end"),
    )


def load_dialogue(name: str, base: Path | None = None) -> Dialogue:
    path = (base or data_path("dialogues")) / f"{name}.json"
    with open(path, encoding="utf-8") as handle:
        return dialogue_from_dict(json.load(handle))


@dataclass(slots=True)
class DialogueRunner:
    locale: Localization
    flags: dict[str, bool] = field(default_factory=dict)
    on_voice: Callable[[str], None] | None = None
    dialogue: Dialogue | None = None
    index: int = -1
    elapsed: float = 0.0
    revealed: float = 0.0
    finished: bool = True

    # ------------------------------------------------------------- controle
    def start(self, dialogue: Dialogue) -> None:
        self.dialogue = dialogue
        self.index = -1
        self.finished = False
        self._next_line()

    def _visible_lines(self) -> list[Line]:
        assert self.dialogue is not None
        return [
            line
            for line in self.dialogue.lines
            if line.condition is None or self.flags.get(line.condition, False)
        ]

    def _next_line(self) -> None:
        lines = self._visible_lines()
        self.index += 1
        self.elapsed = 0.0
        self.revealed = 0.0
        if self.index >= len(lines):
            self._finish()
            return
        line = lines[self.index]
        if line.voice and self.on_voice is not None:
            self.on_voice(line.voice)

    def _finish(self) -> None:
        self.finished = True
        if self.dialogue is not None and self.dialogue.on_end:
            self.flags[self.dialogue.on_end] = True

    @property
    def line(self) -> Line | None:
        if self.finished or self.dialogue is None:
            return None
        lines = self._visible_lines()
        return lines[self.index] if 0 <= self.index < len(lines) else None

    def full_text(self) -> str:
        line = self.line
        if line is None:
            return ""
        if line.key:
            return self.locale.t(line.key)
        if line.text:
            return (
                line.text.get(self.locale.language)
                or line.text.get("pt-BR")
                or next(iter(line.text.values()), "")
            )
        return ""

    @property
    def visible_text(self) -> str:
        text = self.full_text()
        return text[: int(self.revealed)]

    @property
    def talking(self) -> bool:
        """Verdadeiro enquanto o texto ainda está sendo revelado (boca animada)."""
        return not self.finished and self.revealed < len(self.full_text())

    def line_duration(self) -> float:
        line = self.line
        if line is None:
            return 0.0
        if line.duration is not None:
            return line.duration
        text = self.full_text()
        return max(
            MIN_LINE_SECONDS, len(text) / CHARS_PER_SECOND + len(text) * SECONDS_PER_CHAR_AFTER
        )

    def advance(self) -> None:
        """Confirmar: revela tudo se ainda digitando; senão vai à próxima linha."""
        if self.finished:
            return
        if self.talking:
            self.revealed = float(len(self.full_text()))
            return
        self._next_line()

    def skip(self) -> None:
        if self.finished or self.dialogue is None:
            return
        if self.dialogue.skippable:
            self._finish()

    def update(self, dt: float) -> None:
        if self.finished or self.dialogue is None:
            return
        self.elapsed += dt
        self.revealed = min(float(len(self.full_text())), self.revealed + CHARS_PER_SECOND * dt)
        if self.dialogue.auto_advance and self.elapsed >= self.line_duration():
            self._next_line()


@dataclass(slots=True)
class ReactionBank:
    """Falas curtas por contexto, sem repetição imediata."""

    reactions: dict[str, list[str]]
    cursor: dict[str, int] = field(default_factory=dict)

    @classmethod
    def from_locale(cls, locale: Localization, character: str) -> ReactionBank:
        node = (
            locale._lookup(locale._strings, f"reactions.{character}")
            or locale._lookup(locale._fallback, f"reactions.{character}")
            or {}
        )
        return cls(
            {context: list(lines) for context, lines in node.items() if isinstance(lines, list)}
        )

    def next(self, context: str) -> str | None:
        lines = self.reactions.get(context)
        if not lines:
            return None
        i = self.cursor.get(context, -1)
        i = (i + 1) % len(lines)
        self.cursor[context] = i
        return lines[i]

    def contexts(self) -> list[str]:
        return sorted(self.reactions)
