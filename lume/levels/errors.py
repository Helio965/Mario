"""Error reporting for data files: every problem carries its JSON path."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Problem:
    source: str  # file or logical source
    path: str  # JSON path such as platforms[3].w
    message: str
    severity: str = "error"  # error | warning

    def __str__(self) -> str:
        return f"{self.severity.upper()} {self.source}:{self.path}: {self.message}"


class DataError(Exception):
    """Raised when a data file cannot be parsed into a valid structure."""

    def __init__(self, problems: list[Problem]):
        self.problems = problems
        lines = "\n".join(str(p) for p in problems[:30])
        more = f"\n... e mais {len(problems) - 30} problemas" if len(problems) > 30 else ""
        super().__init__(f"{len(problems)} problema(s) nos dados:\n{lines}{more}")


class Reader:
    """Typed accessors over decoded JSON that accumulate problems instead of failing fast."""

    def __init__(self, source: str):
        self.source = source
        self.problems: list[Problem] = []

    def error(self, path: str, message: str) -> None:
        self.problems.append(Problem(self.source, path, message))

    def warn(self, path: str, message: str) -> None:
        self.problems.append(Problem(self.source, path, message, "warning"))

    def obj(self, value, path: str) -> dict:
        if not isinstance(value, dict):
            self.error(path, "deveria ser um objeto")
            return {}
        return value

    def arr(self, value, path: str) -> list:
        if value is None:
            return []
        if not isinstance(value, list):
            self.error(path, "deveria ser uma lista")
            return []
        return value

    def string(self, data: dict, key: str, path: str, default: str | None = None, *, required: bool = True) -> str:
        value = data.get(key, default)
        if value is None:
            if required:
                self.error(f"{path}.{key}", "campo obrigatório ausente")
            return default or ""
        if not isinstance(value, str) or not value.strip():
            self.error(f"{path}.{key}", "deveria ser texto não vazio")
            return default or ""
        return value

    def number(
        self,
        data: dict,
        key: str,
        path: str,
        default: float | None = None,
        *,
        minimum: float | None = None,
        maximum: float | None = None,
        required: bool = True,
    ) -> float:
        value = data.get(key, default)
        if value is None:
            if required:
                self.error(f"{path}.{key}", "campo numérico obrigatório ausente")
            return float(default or 0)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            self.error(f"{path}.{key}", "deveria ser número")
            return float(default or 0)
        if value != value or value in (float("inf"), float("-inf")):
            self.error(f"{path}.{key}", "número não finito")
            return float(default or 0)
        if minimum is not None and value < minimum:
            self.error(f"{path}.{key}", f"deve ser >= {minimum}")
        if maximum is not None and value > maximum:
            self.error(f"{path}.{key}", f"deve ser <= {maximum}")
        return float(value)

    def integer(self, data: dict, key: str, path: str, default: int | None = None, **limits) -> int:
        value = self.number(data, key, path, default, **limits)
        if isinstance(data.get(key), float) and not float(data[key]).is_integer():
            self.error(f"{path}.{key}", "deveria ser inteiro")
        return int(value)

    def boolean(self, data: dict, key: str, path: str, default: bool = False) -> bool:
        value = data.get(key, default)
        if not isinstance(value, bool):
            self.error(f"{path}.{key}", "deveria ser verdadeiro/falso")
            return default
        return value

    def choice(self, data: dict, key: str, path: str, options, default: str | None = None) -> str:
        value = self.string(data, key, path, default, required=default is None)
        if value and value not in options:
            self.error(f"{path}.{key}", f"valor '{value}' inválido; use um de: {', '.join(sorted(options))}")
        return value

    def unknown_keys(self, data: dict, allowed: set[str], path: str) -> None:
        for key in data:
            if key not in allowed:
                self.error(f"{path}.{key}", "campo desconhecido (erro de digitação?)")
