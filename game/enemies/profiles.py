"""Perfis numéricos e flags dos arquétipos de inimigos.

Valores de ``docs/research/INIMIGOS.md`` §6–§7: originais DOCUMENTADOS
(análise comunitária de SMB1/SMB3/SMW) convertidos para a escala do Lume
(distâncias × 1,875; velocidades horizontais × 2,44; impulsos verticais
× 2,46; tempos × 1). As conversões são ESTIMADAS (decisão de design).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ArchetypeFlags:
    """Equivalente das tabelas de atributo de SMB3 (OAT_/OA2_/OA3_)."""

    stompable: bool = True  # pisar derrota/atordoa
    stomp_hurts: bool = False  # espinhos: pisar fere (Thwomp, filhote do aéreo)
    fireproof: bool = False  # Buzzy (SMB1); Boo/Thwomp/Dry Bones/Bob-omb/Chomp (SMB3)
    star_kills: bool = True
    shell_kills: bool = True
    explosion_kills: bool = True
    turn_at_edges: bool = False  # Koopa vermelho, Dry Bones (SMW), Shy Guy rosa
    turn_on_enemy_contact: bool = (
        True  # SMB1 EnemyTurnAround (exceções: emboscada, aéreo, arremessador)
    )
    face_player_on_land: bool = False  # SMB1 ProcEnemyDirection (Koopas sim, Goomba não)
    blocks_player: bool = False  # pode-se ficar em cima (Konk, Shy Guy)


@dataclass(frozen=True, slots=True)
class WalkerProfile:
    walk_speed: float = 72.0  # 0,5 px/q = 30 px/s × 2,44
    fast_speed: float = 110.0  # 0,75 px/q = 45 px/s × 2,44
    world_bonus: float = 6.0  # +6 px/s por mundo (hoje 55 + 7·mundo no legado)
    squash_time: float = 0.5  # Goomba achatado ≈ 0,35–0,7 s
    stun_time: float = 4.25  # SMW $FF quadros
    stun_telegraph: float = 0.8  # SMW < $30 quadros
    shell_speed: float = 420.0  # 3 px/q = 180 px/s × 2,44 (1,24 × corrida)
    shell_revive_time: float = 5.5  # SMB1 16 ticks × 21 q
    shell_revive_time_hard: float = 4.0  # SMB1 11 ticks (mundos 4–5)
    shell_legs_telegraph: float = 1.5  # SMB1 timer < 5 ticks
    kick_offset: float = 14.0
    knockback_vy: float = -440.0  # SMB1 −3 px/q × 2,46
    knockback_vx: float = 146.0  # SMB1 ±1 px/q × 2,44
    stomp_bounce: float = -390.0  # atual
    stomp_jump_bounce: float = -590.0  # pisão-salto (salto pressionado no quadro do pisão)


@dataclass(frozen=True, slots=True)
class ZoneProfile:
    """Janelas de percepção (px); assimetrias preservadas dos originais."""

    piranha_hide: float = 62.0  # SMB1 33 px × 1,875
    blaster_dead_zone: float = 75.0  # SMB1 40 px × 1,875
    crusher_alert: float = 120.0  # SMW ±64 px × 1,875
    crusher_drop: tuple[float, float] = (-68.0, 83.0)  # SMB3/SMW −36…+44 px × 1,875
    chomp_target: float = 120.0  # SMB3 64 px × 1,875
    chomp_chain: float = 90.0
    fish_wake: float = 90.0  # SMW ±48 px × 1,875 (X e Y)
    boo_dead_zone_x: float = 19.0  # SMW 10 px × 1,875
    boo_dead_zone_y: float = 8.0  # SMB3 4 px × 1,875
    lakitu_distance_cap: float = 112.0  # SMB1 60 px × 1,875
    turret_range: float = 650.0


@dataclass(frozen=True, slots=True)
class TimingProfile:
    """Segundos (× 1: o ritmo é percebido em tempo, não em pixels)."""

    thrower_interval: float = 0.8  # SMB1 48 q (0,47 difícil)
    thrower_interval_hard: float = 0.5
    thrower_telegraph: float = 0.25  # adição do Lume (SMB1 = 0)
    thrower_jump_interval: tuple[float, float] = (3.2, 4.25)  # SMB1/SMB3 $C0–$FF q
    thrower_shimmy_flip: float = 1.07  # 64 q
    thrower_advance_after: float = 20.0
    aerial_interval: float = 2.1  # SMB1 128 q
    aerial_telegraph: float = 0.27  # SMB1 16 q
    turret_interval: tuple[float, float] = (2.0, 2.6)
    turret_flash: float = 0.17  # SMB1 10 q
    ambush_wait: float = 1.07  # SMB1 64 q (SMB3 0,8; SMW 0,53)
    ambush_wait_hard: float = 0.8
    ambush_travel: float = 0.8  # SMB1 48 q
    crusher_wait: float = 1.07  # SMB3/SMW 64 q
    crusher_shake: float = 0.4  # SMB3/SMW 24 q
    boo_reaction: float = 0.33  # SMB3 20 q
    boo_turn: float = 0.5  # SMW 31 q
    fuse_time: float = 4.25  # SMB3 255 q
    fuse_flash: float = 1.07  # SMB3 < 64 q
    explosion_time: float = 0.67  # SMB3 40 q
    bones_down: float = 4.4  # SMB3 ≈ 315 q total − 0,8 s
    bones_rebuild: float = 0.8
    chomp_lunge: float = 0.67  # SMB3 40 q
    chomp_rest: tuple[float, float] = (0.53, 1.05)  # SMB3 $20–$3F q
    chomp_free_after: int = 50  # SMB3 $32 investidas
    fish_chase: float = 8.5  # SMW $FF × 2 q
    leaper_spawn: tuple[float, float] = (0.27, 1.6)  # SMB1 16–96 q


@dataclass(frozen=True, slots=True)
class MotionProfile:
    """px/s e px/s²."""

    crusher_accel: float = 880.0  # 900 px/s² × (1550/1575)
    crusher_max_fall: float = 700.0  # entre SMW 232 e SMB3 420 px/s × 2,44
    crusher_rise: float = 112.0  # 60 px/s × 1,875
    boo_accel: float = 550.0  # SMB3 225 px/s² × 2,44
    boo_max: float = 130.0  # SMB3 60 px/s × 2,44 (0,6 × caminhada)
    boo_stop_decel: float = 300.0  # parada suave (SMW)
    hammer_vx: float = 120.0
    hammer_vy: float = -230.0
    hammer_gravity: float = 430.0  # ápice 60 px, voo ≈ 1,1 s
    turret_bullet: float = 220.0  # = caminhada (SMB1: 1,5 px/q = andar)
    lakitu_base: tuple[float, float, float] = (190.0, 440.0, 590.0)  # parado / andando / correndo
    lakitu_distance_slope: float = 0.8  # px/s por px de distância
    lakitu_egg_vy: float = -300.0
    lakitu_egg_vx: float = 60.0
    lakitu_children: int = 3
    chomp_lunges: tuple[tuple[float, float], ...] = (
        (600, -290),
        (360, -590),
        (480, -440),
        (240, -740),
    )
    chomp_return_speed: float = 72.0
    bomb_speed: float = 110.0
    bomb_kick_vx: float = 365.0
    bomb_kick_vy: float = -300.0
    bomb_radius: float = 56.0
    leaper_vy: float = -550.0
    leaper_gravity: float = 300.0
    leaper_vx: tuple[float, float] = (45.0, 130.0)
    leaper_max: int = 3
    fish_accel: float = 70.0
    fish_max: float = 146.0
    hop_vy: float = -440.0  # Planador pulante: SMB1 −3 px/q × 2,46
    glide_vertical_amplitude: float = 90.0
    glide_vertical_period: float = 6.0
    glide_horizontal_amplitude: float = 120.0
    glide_horizontal_period: float = 4.0
    ambush_speed: float = 56.0  # 56 px/s × 0,8 s = 45 px (altura do sprite)
    venus_shot_speed: float = 150.0
    shimmy_speed: float = 37.0
    thrower_leap: tuple[float, float] = (-520.0, -760.0)
    thrower_chase_speed: float = 72.0


FLAGS_DEFAULT = ArchetypeFlags()
WALKER = WalkerProfile()
ZONES = ZoneProfile()
TIMING = TimingProfile()
MOTION = MotionProfile()


def walk_speed_for_world(world: int, profile: WalkerProfile = WALKER) -> float:
    """Trotador: 72 px/s + 6 px/s por mundo (mundos 4–5 usam a variante rápida)."""
    if world >= 4:
        return profile.fast_speed
    return profile.walk_speed + profile.world_bonus * (world - 1)


def is_hard_world(world: int) -> bool:
    return world >= 4
