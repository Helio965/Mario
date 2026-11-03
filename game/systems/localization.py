"""Localização: textos em ``data/locales/<idioma>.json`` (pt-BR principal).

CONTRATO: ``Localization(language)`` com ``t(key, **params)``; chaves
ausentes retornam a própria chave (visível, nunca exceção) e são registradas
em ``missing`` para os testes. ``available_languages()`` lista os arquivos.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from game.paths import data_path

DEFAULT_LANGUAGE = "pt-BR"


class Localization:
    def __init__(self, language: str = DEFAULT_LANGUAGE) -> None:
        self.language = language
        self.missing: list[str] = []
        self._strings: dict[str, Any] = {}
        self._fallback: dict[str, Any] = {}
        self.load(language)

    @staticmethod
    def available_languages() -> list[str]:
        return sorted(p.stem for p in data_path("locales").glob("*.json"))

    def load(self, language: str) -> None:
        self.language = language
        self._fallback = self._read(DEFAULT_LANGUAGE)
        self._strings = self._fallback if language == DEFAULT_LANGUAGE else self._read(language)

    @staticmethod
    def _read(language: str) -> dict[str, Any]:
        path: Path = data_path("locales", f"{language}.json")
        try:
            with open(path, encoding="utf-8") as handle:
                data: dict[str, Any] = json.load(handle)
            return data
        except (OSError, ValueError):
            return {}

    def has(self, key: str) -> bool:
        """Verdadeiro se a chave existe no idioma atual ou no padrão (sem registrar em ``missing``)."""
        return (
            self._lookup(self._strings, key) is not None
            or self._lookup(self._fallback, key) is not None
        )

    def t(self, key: str, **params: Any) -> str:
        value = self._lookup(self._strings, key)
        if value is None:
            value = self._lookup(self._fallback, key)
        if value is None:
            if key not in self.missing:
                self.missing.append(key)
            return key
        try:
            return str(value).format(**params) if params else str(value)
        except (KeyError, IndexError, ValueError):
            return str(value)

    @staticmethod
    def _lookup(strings: dict[str, Any], key: str) -> Any:
        node: Any = strings
        for part in key.split("."):
            if not isinstance(node, dict) or part not in node:
                return None
            node = node[part]
        return node
