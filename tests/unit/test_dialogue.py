"""Diálogos: carregamento, máquina de escrever, avanço, pular, condições e reações."""

from __future__ import annotations

from game.npc.dialogue import Dialogue, DialogueRunner, Line, ReactionBank, load_dialogue
from game.systems.localization import Localization


def test_load_intro_dialogue_and_run_with_typewriter() -> None:
    locale = Localization("pt-BR")
    voices: list[str] = []
    runner = DialogueRunner(locale, on_voice=voices.append)
    dialogue = load_dialogue("intro_1-1")
    assert dialogue.id == "intro_1-1"
    assert len(dialogue.lines) == 3
    runner.start(dialogue)
    assert voices == ["hello"]
    assert runner.line is not None and runner.line.speaker == "lume"
    full = runner.full_text()
    assert "luz" in full
    assert runner.visible_text == ""
    assert runner.talking
    runner.update(0.5)
    assert 0 < len(runner.visible_text) < len(full)
    runner.advance()  # revela tudo
    assert runner.visible_text == full
    assert not runner.talking
    runner.advance()  # próxima linha
    assert runner.line is not None and runner.line.expression == "happy"
    runner.advance()
    runner.advance()
    assert runner.line is not None and runner.line.expression == "determined"
    assert voices == ["hello", "surprise"]
    runner.advance()
    runner.advance()
    assert runner.finished
    assert runner.flags["intro_seen"] is True
    assert locale.missing == []


def test_skip_auto_advance_conditions_and_text_fallback() -> None:
    locale = Localization("pt-BR")
    runner = DialogueRunner(locale)
    dialogue = Dialogue(
        "t",
        [
            Line("a", text={"pt-BR": "Olá", "en-US": "Hello"}),
            Line("b", text={"pt-BR": "Só se tiver a chave"}, condition="has_key"),
            Line("c", text={"en-US": "Only english"}, duration=0.2),
        ],
        auto_advance=True,
    )
    runner.start(dialogue)
    assert runner.full_text() == "Olá"
    for _ in range(30):
        runner.update(0.1)
    # A linha condicional foi pulada; a terceira usa o primeiro idioma disponível.
    assert runner.finished or runner.full_text() == "Only english"
    runner.flags["has_key"] = True
    runner.start(dialogue)
    runner.advance()
    runner.advance()
    assert runner.full_text() == "Só se tiver a chave"
    runner.skip()
    assert runner.finished
    locked = Dialogue("l", [Line("a", text={"pt-BR": "x"})], skippable=False)
    runner.start(locked)
    runner.skip()
    assert not runner.finished
    assert runner.line_duration() >= 1.2


def test_reaction_bank_cycles_without_immediate_repetition() -> None:
    locale = Localization("pt-BR")
    bank = ReactionBank.from_locale(locale, "lume")
    assert {"hurt", "relic", "boss_intro", "victory", "defeat"} <= set(bank.contexts())
    seen = [bank.next("hurt") for _ in range(6)]
    assert all(seen[i] != seen[i + 1] for i in range(5))
    assert len(set(seen)) == len(bank.reactions["hurt"])
    assert bank.next("unknown") is None
    assert ReactionBank({}).next("x") is None
