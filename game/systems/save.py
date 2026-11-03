"""Salvamento local versionado (port da sanitização de ``src/systems/save.ts``).

Diferenças deliberadas em relação ao navegador:

* o armazenamento é um arquivo JSON no diretório de dados do usuário, escrito
  de forma atômica (arquivo temporário + ``os.replace``);
* a versão atual é ``2`` (configurações ampliadas); arquivos ``version: 1``
  (formato do navegador) são migrados; versões desconhecidas resultam em
  dados novos e seguros, como antes;
* ``import_browser_export`` aceita o JSON exportado do ``localStorage``.
"""

from __future__ import annotations

import contextlib
import json
import math
import os
import re
import sys
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

SAVE_KEY = "lume-save-v1"
SAVE_FILE_NAME = "save.json"
CURRENT_VERSION = 2
MAX_LEVEL_INDEX = 14
MAX_SAFE_INTEGER = 2**53 - 1

ACTIONS: tuple[str, ...] = ("left", "right", "jump", "run", "ability", "down", "pause")
DEFAULT_BINDINGS: dict[str, list[str]] = {
    "left": ["a", "left"],
    "right": ["d", "right"],
    "jump": ["space", "w", "up"],
    "run": ["left shift", "right shift"],
    "ability": ["j"],
    "down": ["s", "down"],
    "pause": ["escape"],
}
QUALITIES: tuple[str, ...] = ("high", "medium", "low")
FPS_LIMITS: tuple[int, ...] = (0, 30, 60, 120, 144)
LANGUAGES: tuple[str, ...] = ("pt-BR", "en-US")
_CONTROL = re.compile(r"[\u0000-\u001f\u007f]")


@dataclass(slots=True)
class Settings:
    music: float = 0.45
    sfx: float = 0.75
    voice: float = 0.8
    ambient: float = 0.6
    effects: bool = True
    touch: bool = False
    fullscreen: bool = False
    scale: int = 0
    fps_limit: int = 60
    show_fps: bool = False
    language: str = "pt-BR"
    quality: str = "high"
    reduced_motion: bool = False
    high_contrast: bool = False
    subtitles: bool = True
    bindings: dict[str, list[str]] = field(
        default_factory=lambda: {k: list(v) for k, v in DEFAULT_BINDINGS.items()}
    )

    def copy(self) -> Settings:
        return Settings(
            music=self.music,
            sfx=self.sfx,
            voice=self.voice,
            ambient=self.ambient,
            effects=self.effects,
            touch=self.touch,
            fullscreen=self.fullscreen,
            scale=self.scale,
            fps_limit=self.fps_limit,
            show_fps=self.show_fps,
            language=self.language,
            quality=self.quality,
            reduced_motion=self.reduced_motion,
            high_contrast=self.high_contrast,
            subtitles=self.subtitles,
            bindings={k: list(v) for k, v in self.bindings.items()},
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "music": self.music,
            "sfx": self.sfx,
            "voice": self.voice,
            "ambient": self.ambient,
            "effects": self.effects,
            "touch": self.touch,
            "fullscreen": self.fullscreen,
            "scale": self.scale,
            "fps_limit": self.fps_limit,
            "show_fps": self.show_fps,
            "language": self.language,
            "quality": self.quality,
            "reduced_motion": self.reduced_motion,
            "high_contrast": self.high_contrast,
            "subtitles": self.subtitles,
            "bindings": {k: list(v) for k, v in self.bindings.items()},
        }


@dataclass(slots=True)
class SaveData:
    version: int = CURRENT_VERSION
    unlocked: int = 0
    completed: list[str] = field(default_factory=list)
    records: dict[str, int] = field(default_factory=dict)
    relics: list[str] = field(default_factory=list)
    achievements: list[str] = field(default_factory=list)
    settings: Settings = field(default_factory=Settings)

    def copy(self) -> SaveData:
        return SaveData(
            version=self.version,
            unlocked=self.unlocked,
            completed=list(self.completed),
            records=dict(self.records),
            relics=list(self.relics),
            achievements=list(self.achievements),
            settings=self.settings.copy(),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "unlocked": self.unlocked,
            "completed": list(self.completed),
            "records": dict(self.records),
            "relics": list(self.relics),
            "achievements": list(self.achievements),
            "settings": self.settings.to_dict(),
        }


def fresh_save() -> SaveData:
    return SaveData()


# ------------------------------------------------------------------ sanitização
def _record(value: object) -> dict[str, Any] | None:
    return value if isinstance(value, dict) else None


def _number(value: object, fallback: float, maximum: float, integer: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float) or not math.isfinite(value):
        return fallback
    result = min(maximum, max(0, value))
    return math.floor(result) if integer else result


def _boolean(value: object, fallback: bool) -> bool:
    return value if isinstance(value, bool) else fallback


def _choice(value: object, options: Iterable[Any], fallback: Any) -> Any:
    return value if value in tuple(options) else fallback


def valid_id(value: object) -> bool:
    return (
        isinstance(value, str)
        and 0 < len(value) <= 128
        and value.strip() == value
        and not _CONTROL.search(value)
        and value not in ("__proto__", "constructor", "prototype")
    )


def _ids(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    seen: list[str] = []
    for item in value:
        if valid_id(item) and item not in seen:
            seen.append(item)
    return seen


def _bindings(value: object) -> dict[str, list[str]]:
    source = _record(value) or {}
    result: dict[str, list[str]] = {}
    for action in ACTIONS:
        keys = source.get(action)
        clean: list[str] = []
        if isinstance(keys, list):
            for key in keys:
                if (
                    isinstance(key, str)
                    and 0 < len(key) <= 32
                    and key.strip() == key
                    and not _CONTROL.search(key)
                    and key not in clean
                ):
                    clean.append(key)
        result[action] = clean or list(DEFAULT_BINDINGS[action])
    return result


def _settings(value: object) -> Settings:
    s = _record(value) or {}
    d = Settings()
    return Settings(
        music=_number(s.get("music"), d.music, 1),
        sfx=_number(s.get("sfx"), d.sfx, 1),
        voice=_number(s.get("voice"), d.voice, 1),
        ambient=_number(s.get("ambient"), d.ambient, 1),
        effects=_boolean(s.get("effects"), d.effects),
        touch=_boolean(s.get("touch"), d.touch),
        fullscreen=_boolean(s.get("fullscreen"), d.fullscreen),
        scale=int(_number(s.get("scale"), d.scale, 4, True)),
        fps_limit=int(_choice(s.get("fps_limit"), FPS_LIMITS, d.fps_limit)),
        show_fps=_boolean(s.get("show_fps"), d.show_fps),
        language=str(_choice(s.get("language"), LANGUAGES, d.language)),
        quality=str(_choice(s.get("quality"), QUALITIES, d.quality)),
        reduced_motion=_boolean(s.get("reduced_motion"), d.reduced_motion),
        high_contrast=_boolean(s.get("high_contrast"), d.high_contrast),
        subtitles=_boolean(s.get("subtitles"), d.subtitles),
        bindings=_bindings(s.get("bindings")),
    )


def sanitize(value: object, level_count: int = MAX_LEVEL_INDEX + 1) -> SaveData:
    """Reconstrói cada campo para que dados malformados nunca alcancem o jogo.

    Aceita ``version`` 1 (navegador) e 2 (atual); qualquer outra resulta em
    dados novos.
    """
    source = _record(value)
    if source is None or source.get("version") not in (1, CURRENT_VERSION):
        return fresh_save()
    records = _record(source.get("records")) or {}
    clean_records: dict[str, int] = {}
    for key, score in records.items():
        if (
            valid_id(key)
            and not isinstance(score, bool)
            and isinstance(score, int | float)
            and math.isfinite(score)
        ):
            clean_records[key] = int(_number(score, 0, MAX_SAFE_INTEGER, True))
    return SaveData(
        version=CURRENT_VERSION,
        unlocked=int(_number(source.get("unlocked"), 0, max(0, level_count - 1), True)),
        completed=_ids(source.get("completed")),
        records=clean_records,
        relics=_ids(source.get("relics")),
        achievements=_ids(source.get("achievements")),
        settings=_settings(source.get("settings")),
    )


# -------------------------------------------------------------- armazenamento
class Storage(Protocol):
    def read(self) -> str | None: ...

    def write(self, text: str) -> None: ...

    def remove(self) -> None: ...


class MemoryStorage:
    """Armazenamento em memória para testes."""

    def __init__(self, text: str | None = None) -> None:
        self.text = text
        self.writes: list[str] = []

    def read(self) -> str | None:
        return self.text

    def write(self, text: str) -> None:
        self.text = text
        self.writes.append(text)

    def remove(self) -> None:
        self.text = None


class FileStorage:
    """Arquivo JSON com escrita atômica (tmp + ``os.replace``)."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)

    def read(self) -> str | None:
        try:
            return self.path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return None

    def write(self, text: str) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_name(self.path.name + ".tmp")
        with open(tmp, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, self.path)

    def remove(self) -> None:
        with contextlib.suppress(FileNotFoundError):
            self.path.unlink()


def user_data_dir(app: str = "Lume") -> Path:
    override = os.environ.get("LUME_SAVE_DIR")
    if override:
        return Path(override)
    platform: str = sys.platform  # alias evita que o mypy marque ramos como inalcançáveis por SO
    if platform == "emscripten":
        # Pygbag: /data/data é o ponto de montagem persistente (IDBFS) do navegador.
        return Path("/data/data") / app.lower()
    if platform.startswith("win"):
        base = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
        return Path(base) / app
    if platform == "darwin":
        return Path.home() / "Library" / "Application Support" / app
    base = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
    return Path(base) / app.lower()


def default_storage() -> FileStorage:
    return FileStorage(user_data_dir() / SAVE_FILE_NAME)


def load_save(storage: Storage | None = None) -> SaveData:
    try:
        raw = (storage or default_storage()).read()
        return sanitize(json.loads(raw)) if raw else fresh_save()
    except Exception:  # qualquer falha de leitura resulta em dados seguros
        return fresh_save()


def write_save(data: SaveData, storage: Storage | None = None) -> bool:
    try:
        target = storage or default_storage()
        target.write(json.dumps(sanitize(data.to_dict()).to_dict(), ensure_ascii=False, indent=1))
        return True
    except Exception:
        return False


def reset_save(storage: Storage | None = None) -> SaveData:
    with contextlib.suppress(Exception):  # o armazenamento pode estar bloqueado
        (storage or default_storage()).remove()
    return fresh_save()


def complete_level(
    data: SaveData,
    index: int,
    score: float,
    relic: bool,
    level_id: str,
    level_count: int = MAX_LEVEL_INDEX + 1,
) -> SaveData:
    """Devolve um novo ``SaveData`` com a fase concluída; a entrada não é alterada."""
    nxt = sanitize(data.to_dict(), level_count)
    last = max(0, level_count - 1)
    if (
        not valid_id(level_id)
        or isinstance(index, bool)
        or not isinstance(index, int | float)
        or not math.isfinite(index)
        or index < 0
        or index > last
        or int(index) != index
    ):
        return nxt
    index = int(index)
    nxt.unlocked = max(nxt.unlocked, min(last, index + 1))
    if level_id not in nxt.completed:
        nxt.completed.append(level_id)
    nxt.records[level_id] = max(
        nxt.records.get(level_id, 0), int(_number(score, 0, MAX_SAFE_INTEGER, True))
    )
    if relic and level_id not in nxt.relics:
        nxt.relics.append(level_id)
    return nxt


def import_browser_export(text: str) -> SaveData | None:
    """Importa o JSON copiado do ``localStorage`` da versão de navegador (chave ``lume-save-v1``).

    Aceita tanto o valor da chave quanto um objeto ``{"lume-save-v1": "..."}``.
    Devolve ``None`` quando o texto não contém um salvamento reconhecível.
    """
    try:
        parsed = json.loads(text)
    except (TypeError, ValueError):
        return None
    if isinstance(parsed, dict) and SAVE_KEY in parsed:
        inner = parsed[SAVE_KEY]
        try:
            parsed = json.loads(inner) if isinstance(inner, str) else inner
        except (TypeError, ValueError):
            return None
    if not isinstance(parsed, dict) or parsed.get("version") not in (1, CURRENT_VERSION):
        return None
    return sanitize(parsed)
