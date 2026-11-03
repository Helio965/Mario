"""Elenco de personagens: núcleo compartilhado + variações por envelope + habilidades.

Modelo híbrido escolhido na pesquisa (docs/research/PERSONAGENS.md §10):
todos compartilham ``MovementProfile``, hitboxes e modelo de dano; cada
personagem aplica um ``CharacterDelta`` limitado por envelope (altura de
salto 0,85–1,21×, corrida 0,93–1,12×, atrito 0,6–1,3×) para que nenhuma fase
obrigatória fique impossível; habilidades que mudam o alcance são limitadas
no tempo e na velocidade. Os dados ficam em ``data/characters/*.json``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, replace
from functools import lru_cache
from pathlib import Path
from typing import Any

from game.paths import data_path
from game.physics.movement import MovementProfile

JUMP_HEIGHT_ENVELOPE = (0.85, 1.21)  # razão de altura (∝ mul²)
RUN_SPEED_ENVELOPE = (0.93, 1.12)
FRICTION_ENVELOPE = (0.6, 1.3)
ENVELOPE_TOLERANCE = 1e-3  # arredondamento das razões da pesquisa (0,92² ≈ 0,85; 1,10² = 1,21)
KNOWN_ABILITIES: tuple[str, ...] = ("scuttle", "charged_jump", "float", "fire", "none")
DAMAGE_MODELS: tuple[str, ...] = ("standard", "invincible")

# Parâmetros das habilidades (px/s, s) — origem: PERSONAGENS.md §10.3
SCUTTLE_FALL_GRAVITY_MUL = 0.70
CHARGED_JUMP_HOLD = 0.50
CHARGED_JUMP_SPEED_MUL = 1.175
FLOAT_MAX_DURATION = 0.80
FLOAT_FALL_SPEED = 60.0
FLOAT_AIR_SPEED_CAP = 220.0
INVINCIBLE_KNOCKBACK = 160.0
INVINCIBLE_STUN = 0.30


@dataclass(slots=True, frozen=True)
class CharacterDelta:
    jump_speed_mul: float = 1.0
    run_speed_mul: float = 1.0
    walk_speed_mul: float = 1.0
    ground_accel_mul: float = 1.0
    ground_friction_mul: float = 1.0
    ice_friction_mul: float = 1.0
    air_accel_mul: float = 1.0
    abilities: tuple[str, ...] = ()
    damage_model: str = "standard"
    time_bonus: float = 0.0

    def jump_height_ratio(self) -> float:
        return self.jump_speed_mul * self.jump_speed_mul

    def within_envelope(self) -> list[str]:
        problems: list[str] = []
        tol = ENVELOPE_TOLERANCE
        lo, hi = JUMP_HEIGHT_ENVELOPE
        if not lo - 5 * tol <= self.jump_height_ratio() <= hi + tol:
            problems.append(f"altura do salto {self.jump_height_ratio():.2f}× fora de [{lo}, {hi}]")
        lo, hi = RUN_SPEED_ENVELOPE
        if not lo - tol <= self.run_speed_mul <= hi + tol:
            problems.append(f"corrida {self.run_speed_mul:.2f}× fora de [{lo}, {hi}]")
        lo, hi = FRICTION_ENVELOPE
        if not lo - tol <= self.ground_friction_mul <= hi + tol:
            problems.append(f"atrito {self.ground_friction_mul:.2f}× fora de [{lo}, {hi}]")
        for ability in self.abilities:
            if ability not in KNOWN_ABILITIES:
                problems.append(f"habilidade desconhecida {ability!r}")
        if self.damage_model not in DAMAGE_MODELS:
            problems.append(f"modelo de dano desconhecido {self.damage_model!r}")
        return problems


@dataclass(slots=True, frozen=True)
class Character:
    id: str
    names: dict[str, str]
    palette: dict[str, str]
    delta: CharacterDelta
    unlock_world: int = 1
    description_key: str = ""
    voice_pitch: float = 1.0
    clips: dict[str, dict[str, Any]] = field(default_factory=dict)

    def name(self, language: str = "pt-BR") -> str:
        return self.names.get(language) or self.names.get("pt-BR") or self.id

    def profile(self, base: MovementProfile) -> MovementProfile:
        """Aplica o delta ao perfil base (legado ou calibrado) sem alterar o próprio base."""
        d = self.delta
        return replace(
            base,
            jump_speed=base.jump_speed * d.jump_speed_mul,
            run_speed=base.run_speed * d.run_speed_mul,
            walk_speed=base.walk_speed * d.walk_speed_mul,
            ground_acceleration=base.ground_acceleration * d.ground_accel_mul,
            walk_acceleration=base.walk_acceleration * d.ground_accel_mul,
            run_acceleration=base.run_acceleration * d.ground_accel_mul,
            air_acceleration=base.air_acceleration * d.air_accel_mul,
            ground_friction=base.ground_friction * d.ground_friction_mul,
            skid_deceleration=base.skid_deceleration * d.ground_friction_mul,
            ice_friction=base.ice_friction * d.ice_friction_mul,
            ice_skid_deceleration=base.ice_skid_deceleration * d.ice_friction_mul,
            run_jump_speed=None
            if base.run_jump_speed is None
            else base.run_jump_speed * d.jump_speed_mul,
        )


def character_from_dict(d: dict[str, Any]) -> Character:
    raw = d.get("delta", {})
    delta = CharacterDelta(
        jump_speed_mul=float(raw.get("jump_speed_mul", 1.0)),
        run_speed_mul=float(raw.get("run_speed_mul", 1.0)),
        walk_speed_mul=float(raw.get("walk_speed_mul", 1.0)),
        ground_accel_mul=float(raw.get("ground_accel_mul", 1.0)),
        ground_friction_mul=float(raw.get("ground_friction_mul", 1.0)),
        ice_friction_mul=float(raw.get("ice_friction_mul", 1.0)),
        air_accel_mul=float(raw.get("air_accel_mul", 1.0)),
        abilities=tuple(d.get("abilities", [])),
        damage_model=str(d.get("damage_model", "standard")),
        time_bonus=float(d.get("time_bonus", 0.0)),
    )
    return Character(
        id=str(d["id"]),
        names=dict(d.get("name", {})),
        palette=dict(d.get("palette", {})),
        delta=delta,
        unlock_world=int(d.get("unlock", {}).get("world", 1)),
        description_key=str(d.get("description_key", "")),
        voice_pitch=float(d.get("voice_pitch", 1.0)),
        clips=dict(d.get("clips", {})),
    )


def characters_dir() -> Path:
    return data_path("characters")


@lru_cache(maxsize=1)
def load_roster() -> dict[str, Character]:
    roster: dict[str, Character] = {}
    for path in sorted(characters_dir().glob("*.json")):
        with open(path, encoding="utf-8") as handle:
            character = character_from_dict(json.load(handle))
        roster[character.id] = character
    return roster


def get_character(character_id: str) -> Character:
    roster = load_roster()
    return roster.get(character_id) or roster["lume"]


def minimum_profiles(base: MovementProfile) -> dict[str, MovementProfile]:
    """Perfis mínimos (menor salto, menor alcance) para validar rotas obrigatórias."""
    roster = load_roster()
    lowest_jump = min(roster.values(), key=lambda c: c.delta.jump_speed_mul)
    slowest = min(roster.values(), key=lambda c: c.delta.run_speed_mul)
    return {"menor_salto": lowest_jump.profile(base), "menor_corrida": slowest.profile(base)}
