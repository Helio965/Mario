"""Os Cinco Guardiões do Lume (docs/research/CHEFES.md §6).

Cada guardião é uma ``BossDefinition`` com três fases que trocam o conjunto
de ataques (um verbo novo por fase), telegraph com piso por mundo
(900/750/650/550/450 ms), alvo congelado no início do aviso, retaliação
imune após o golpe e janelas de vulnerabilidade ≥ 1,0–1,6 s.

Mecânicas de arena que exigem entidades de fase (ponte frágil, placas e
pilares, buracos no gelo, lava cíclica, alavanca/corredor) ficam para a
reconstrução das fases; aqui estão marcadas como PENDENTE nos comentários
e substituídas por janelas de vulnerabilidade equivalentes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from game.bosses.boss import (
    Attack,
    BossDefinition,
    GuardianBehavior,
    Phase,
    charge_attack,
    leap_attack,
    register_guardian,
)
from game.core.types import Enemy, GameEvent
from game.enemies.behaviors import Behavior, register
from game.enemies.state_machine import EnemyStateName, State, Transition
from game.physics.collision import overlaps
from game.physics.movement import GRAVITY

if TYPE_CHECKING:
    from game.core.game import Game

S = EnemyStateName
ARENA_TOP = 60.0  # altura de onde caem frutas, estalactites e esporos (acima do chefe)


# ------------------------------------------------------------- utilidades
def _target_direction(boss: GuardianBehavior, e: Enemy) -> int:
    return 1 if boss.target_x > e.x else -1


def _floor_y(e: Enemy) -> float:
    return e.y + e.h


# ------------------------------------------------------------ ataques novos
def pounce_attack(
    flight: float = 0.9, telegraph: float = 0.9, recover: float = 0.6, name: str = "pounce"
) -> Attack:
    """Salto parabólico até a posição observada do jogador (sombra no chão durante o voo)."""

    def start(game: Game, e: Enemy, boss: GuardianBehavior) -> None:
        e.facing = _target_direction(boss, e)
        dx = boss.target_x - e.x
        boss.data["pounce_vx"] = dx / flight
        e.vy = -GRAVITY * flight / 2

    def tick(game: Game, e: Enemy, boss: GuardianBehavior, dt: float) -> None:
        e.vx = boss.data.get("pounce_vx", 0.0)
        if e.grounded and boss.attack_clock > 0.2:
            e.vx = 0

    def end(game: Game, e: Enemy, boss: GuardianBehavior) -> None:
        e.vx = 0
        game.events.append(GameEvent("impact"))

    return Attack(
        name,
        telegraph,
        flight + 0.1,
        recover,
        start=start,
        tick=tick,
        end=end,
        animation="pounce",
        counter="move_away",
    )


def shockwave_attack(
    speed: float = 320.0,
    height: float = 24.0,
    telegraph: float = 0.7,
    recover: float = 1.6,
    name: str = "shockwave",
    life: float = 2.6,
) -> Attack:
    """Bate no chão: uma onda baixa percorre o solo na direção do jogador (saltável)."""

    def start(game: Game, e: Enemy, boss: GuardianBehavior) -> None:
        direction = _target_direction(boss, e)
        e.facing = direction
        game.events.append(GameEvent("impact"))
        game.shake = 0.15
        boss.launch(
            game,
            direction * speed,
            0.0,
            w=28,
            h=height,
            life=life,
            x=e.x + e.w / 2 + direction * e.w / 2,
            y=_floor_y(e) - height,
        )

    def tick(game: Game, e: Enemy, boss: GuardianBehavior, dt: float) -> None:
        e.vx = 0

    return Attack(
        name, telegraph, 0.3, recover, start=start, tick=tick, animation="slam", counter="jump_wave"
    )


def dart_attack(
    speed: float = 240.0,
    telegraph: float = 0.75,
    recover: float = 0.9,
    count: int = 1,
    gap: float = 0.3,
    predict: float = 0.0,
    name: str = "dart",
) -> Attack:
    """Dardo(s) na direção do jogador em duas alturas observadas: baixa (saltar) ou alta (ficar parado)."""

    def start(game: Game, e: Enemy, boss: GuardianBehavior) -> None:
        boss.data["darts_fired"] = 0

    def tick(game: Game, e: Enemy, boss: GuardianBehavior, dt: float) -> None:
        e.vx = 0
        fired = int(boss.data.get("darts_fired", 0))
        if fired < count and boss.attack_clock >= fired * gap:
            aim_x = (
                boss.target_x + boss.target_vx * predict
            )  # mira prevista só com dados observáveis
            direction = 1 if aim_x > e.x else -1
            e.facing = direction
            # Altura congelada: o dardo baixo passa pelos pés do jogador (saltar); o alto, acima da
            # cabeça de quem está em pé (ficar parado). Em rajadas o alto vem primeiro: assim quem
            # saltou o baixo não é apanhado no ar pelo seguinte.
            low = fired % 2 == 1 if count > 1 else True
            y = boss.target_y + 16 if low else boss.target_y - 30
            boss.launch(game, direction * speed, 0.0, w=14, h=14, life=4.0, x=e.x + e.w / 2, y=y)
            boss.data["darts_fired"] = fired + 1

    hold = gap * max(0, count - 1) + 0.2
    return Attack(
        name,
        telegraph,
        hold,
        recover,
        start=start,
        tick=tick,
        animation="shoot",
        counter="jump",
        hazards=count,
    )


def lob_attack(
    count: int = 1,
    flight: float = 1.1,
    telegraph: float = 0.65,
    recover: float = 1.0,
    gravity: float = 600.0,
    spread: float = 30.0,
    name: str = "lob",
) -> Attack:
    """Projéteis em arco que caem onde o jogador ESTAVA (alvo congelado)."""

    def start(game: Game, e: Enemy, boss: GuardianBehavior) -> None:
        e.facing = _target_direction(boss, e)
        for i in range(count):
            offset = (i - (count - 1) / 2) * spread
            dx = boss.target_x + offset - (e.x + e.w / 2)
            boss.launch(
                game,
                dx / flight,
                -gravity * flight / 2 + (_floor_y(e) - (boss.target_y + 30)) / flight,
                gravity=gravity,
                life=flight + 0.3,
            )

    def tick(game: Game, e: Enemy, boss: GuardianBehavior, dt: float) -> None:
        e.vx = 0

    return Attack(
        name,
        telegraph,
        0.25,
        recover,
        start=start,
        tick=tick,
        animation="throw",
        counter="move_away",
        hazards=count,
    )


def drop_attack(
    fall_speed: float = 420.0,
    telegraph: float = 0.9,
    recover: float = 0.8,
    hostile: bool = True,
    name: str = "drop",
    w: float = 24,
    h: float = 24,
) -> Attack:
    """Objeto que cai do alto na coluna observada do jogador (fruta, estalactite)."""

    def start(game: Game, e: Enemy, boss: GuardianBehavior) -> None:
        boss.launch(
            game,
            0.0,
            fall_speed,
            w=w,
            h=h,
            life=3.0,
            x=boss.target_x,
            y=max(0.0, _floor_y(e) - 420.0),
            hostile=hostile,
        )

    def tick(game: Game, e: Enemy, boss: GuardianBehavior, dt: float) -> None:
        e.vx = 0

    return Attack(
        name, telegraph, 0.2, recover, start=start, tick=tick, animation="call", counter="move_away"
    )


def ground_roller_attack(
    speed: float = 260.0,
    telegraph: float = 0.9,
    recover: float = 1.0,
    name: str = "roller",
    size: float = 32.0,
) -> Attack:
    """Rocha/bola de neve que entra pelo lado oposto ao jogador e cruza a arena (saltável)."""

    def start(game: Game, e: Enemy, boss: GuardianBehavior) -> None:
        left, right = e.patrol[0], e.patrol[1]
        from_left = boss.target_x > (left + right) / 2
        x = left if from_left else right - size
        direction = 1 if from_left else -1
        boss.launch(
            game,
            direction * speed,
            0.0,
            w=size,
            h=size,
            life=(right - left) / speed + 0.5,
            x=x,
            y=_floor_y(e) - size,
        )
        game.events.append(GameEvent("impact"))

    def tick(game: Game, e: Enemy, boss: GuardianBehavior, dt: float) -> None:
        e.vx = 0

    return Attack(
        name, telegraph, 0.3, recover, start=start, tick=tick, animation="call", counter="jump"
    )


def teleport_attack(
    telegraph: float = 0.75, recover: float = 0.9, name: str = "teleport"
) -> Attack:
    """Some e reaparece em outro ponto da arena; o redemoinho no destino é o aviso."""

    def start(game: Game, e: Enemy, boss: GuardianBehavior) -> None:
        left, right = e.patrol[0], e.patrol[1] - e.w
        spots = [left, (left + right) / 2, right]
        current = min(range(3), key=lambda i: abs(spots[i] - e.x))
        far_from_player = max(
            (i for i in range(3) if i != current), key=lambda i: abs(spots[i] - boss.target_x)
        )
        e.x = spots[far_from_player]
        boss.data["teleport_target"] = e.x

    def tick(game: Game, e: Enemy, boss: GuardianBehavior, dt: float) -> None:
        e.vx = 0

    return Attack(
        name,
        telegraph,
        0.1,
        recover,
        start=start,
        tick=tick,
        animation="teleport",
        counter="stay",
        hazards=0,
    )


def dive_attack(
    speed: float = 520.0, telegraph: float = 0.7, recover: float = 1.6, name: str = "dive"
) -> Attack:
    """Mergulho (chefe flutuante) até a posição observada; descansa no chão depois (vulnerável)."""

    def start(game: Game, e: Enemy, boss: GuardianBehavior) -> None:
        dx = boss.target_x - e.x
        dy = (boss.target_y + 30 - e.h) - e.y
        length = max(1.0, (dx * dx + dy * dy) ** 0.5)
        boss.data["dive_vx"] = speed * dx / length
        boss.data["dive_vy"] = speed * max(0.2, dy / length)
        e.facing = 1 if dx > 0 else -1

    def tick(game: Game, e: Enemy, boss: GuardianBehavior, dt: float) -> None:
        if e.grounded:
            e.vx = 0
            e.vy = 0
        else:
            e.vx = boss.data.get("dive_vx", 0.0)
            e.vy = boss.data.get("dive_vy", speed)

    def end(game: Game, e: Enemy, boss: GuardianBehavior) -> None:
        e.vx = 0
        e.vy = 0
        game.events.append(GameEvent("impact"))

    return Attack(
        name,
        telegraph,
        0.9,
        recover,
        start=start,
        tick=tick,
        end=end,
        animation="dive",
        counter="move_away",
    )


def spawn_shell_attack(
    telegraph: float = 0.65, recover: float = 0.8, name: str = "ice_shell"
) -> Attack:
    """Um casco congelado sai do cano mais distante do jogador (máx. 1 vivo)."""

    def start(game: Game, e: Enemy, boss: GuardianBehavior) -> None:
        alive = [
            x
            for x in game.enemies
            if x.alive and x.kind == "shell" and x.id.startswith(f"{e.id}-shell")
        ]
        if alive:
            return
        left, right = e.patrol[0], e.patrol[1]
        x = left + 4 if boss.target_x > (left + right) / 2 else right - 32
        shell = Enemy(
            id=f"{e.id}-shell-{len(game.enemies)}",
            kind="shell",
            x=x,
            y=_floor_y(e) - 28,
            w=28,
            h=28,
            patrol=[left, right],
            hp=None,
            vx=0,
            vy=0,
            alive=True,
            health=1,
            facing=1 if x < e.x else -1,
            timer=0,
            hit_timer=0,
            state="walk",
            origin_y=_floor_y(e) - 28,
            grounded=False,
        )
        game.enemies.append(shell)
        game.events.append(GameEvent("telegraph"))

    def tick(game: Game, e: Enemy, boss: GuardianBehavior, dt: float) -> None:
        e.vx = 0

    return Attack(
        name,
        telegraph,
        0.2,
        recover,
        start=start,
        tick=tick,
        animation="call",
        counter="stay",
        hazards=0,
    )


def clone_dives_attack(
    count: int,
    telegraph: float = 0.7,
    gap: float = 0.6,
    recover: float = 0.6,
    name: str = "clone_dives",
) -> Attack:
    """Clones sem vagalumes mergulham antes da verdadeira (a verdadeira é sempre a última)."""

    def start(game: Game, e: Enemy, boss: GuardianBehavior) -> None:
        clones = [
            x
            for x in game.enemies
            if x.alive and x.kind == "lumia_clone" and x.behavior is not None
        ]
        left, right = e.patrol[0], e.patrol[1] - e.w
        while len(clones) < count:
            index = len(clones)
            x = left + (right - left) * (0.25 if index % 2 == 0 else 0.75)
            clone = boss.spawn_enemy(
                game, "lumia_clone", x, e.y, e.w, e.h, patrol=(e.patrol[0], e.patrol[1])
            )
            clones.append(clone)
        for index, clone in enumerate(clones):
            clone.behavior.command_dive(boss.target_x, boss.target_y, delay=index * gap)

    def tick(game: Game, e: Enemy, boss: GuardianBehavior, dt: float) -> None:
        e.vx = 0
        e.vy = 0

    return Attack(
        name,
        telegraph,
        0.2 + gap * count,
        recover,
        start=start,
        tick=tick,
        animation="call",
        counter="move_away",
        hazards=0,
    )


def wave_attack(
    speed: float = 270.0, telegraph: float = 1.2, recover: float = 2.2, name: str = "magma_wave"
) -> Attack:
    """Onda de magma: atravessa a arena a 0,8× a corrida e fica presa na parede (janela longa);
    PENDENTE corredor/alavanca (reconstrução)."""

    def start(game: Game, e: Enemy, boss: GuardianBehavior) -> None:
        e.facing = _target_direction(boss, e)
        game.events.append(GameEvent("impact"))

    def tick(game: Game, e: Enemy, boss: GuardianBehavior, dt: float) -> None:
        e.vx = e.facing * speed

    def end(game: Game, e: Enemy, boss: GuardianBehavior) -> None:
        e.vx = 0

    return Attack(
        name,
        telegraph,
        6.0,
        recover,
        start=start,
        tick=tick,
        end=end,
        animation="wave",
        counter="run_away",
        ends_on_wall=True,
    )


def retaliation(name: str, telegraph: float, radius: float, active: float = 0.3) -> Attack:
    """Retaliação imune após o golpe: pulso/anel ao redor do chefe (afastar-se)."""

    def start(game: Game, e: Enemy, boss: GuardianBehavior) -> None:
        game.events.append(GameEvent("impact"))

    def tick(game: Game, e: Enemy, boss: GuardianBehavior, dt: float) -> None:
        e.vx = 0
        p = game.player
        if (
            abs((p.x + p.w / 2) - (e.x + e.w / 2)) < radius + p.w / 2
            and abs((p.y + p.h / 2) - (e.y + e.h / 2)) < radius
        ):
            game.hurt()

    return Attack(
        name,
        telegraph,
        active,
        0.4,
        start=start,
        tick=tick,
        animation="retaliate",
        counter="move_away",
        hazards=0,
    )


# --------------------------------------------------------------- Rolão (M1)
class RolaoBehavior(GuardianBehavior):
    """Tatu-canastra: a fruta que cai (fase 3) o deixa tonto se o atingir."""

    def step(self, game: Game, dt: float) -> None:
        super().step(game, dt)
        e = self.enemy
        for s in game.projectiles:
            if s.alive and not s.hostile and s.owner == e.id and overlaps(s, e):
                s.alive = False
                self.dizzy(game, 1.6)


ROLAO = BossDefinition(
    kind="rolao",
    hp=3,
    world=1,
    name_key="bosses.rolao.name",
    size=(64.0, 58.0),
    defeat_time=2.2,
    phases=[
        Phase(
            "parede",  # verbo: atrair — a investida termina tonta na parede
            1.0,
            [
                charge_attack(
                    speed=230,
                    telegraph=0.9,
                    active=2.2,
                    recover=1.8,
                    name="roll",
                    ends_on_wall=True,
                ),
                leap_attack(telegraph=0.9, recover=0.8),
            ],
            idle_time=1.0,
            intro_time=1.3,
            dialogue="bosses.rolao.intro",
            retaliation=retaliation("shake", 0.9, 40.0),
        ),
        Phase(
            "ponte",  # verbo: posicionar — PENDENTE ponte frágil; o salto parabólico abre a janela
            0.67,
            [
                charge_attack(speed=200, telegraph=0.9, active=1.4, recover=1.0, name="roll_brake"),
                pounce_attack(telegraph=0.9, recover=1.2),
            ],
            idle_time=0.9,
            max_hazards=2,
            retaliation=retaliation("shake", 0.9, 40.0),
        ),
        Phase(
            "fruta",  # verbo: sincronizar — rola sem parar; a fruta observável derruba a bola
            0.34,
            [
                charge_attack(
                    speed=210,
                    telegraph=0.77,
                    active=1.5,
                    recover=0.6,
                    name="roll_endless",
                    ends_on_wall=True,
                ),
                lob_attack(count=1, flight=1.0, telegraph=0.77, recover=0.7, name="seed"),
                drop_attack(
                    fall_speed=420, telegraph=0.8, recover=0.6, hostile=False, name="fruit"
                ),
            ],
            idle_time=0.6,
            max_hazards=2,
            speed_multiplier=1.0,
        ),
    ],
)


# -------------------------------------------------------------- Oculus (M2)
OCULUS = BossDefinition(
    kind="oculus",
    hp=3,
    world=2,
    floats=True,
    name_key="bosses.oculus.name",
    size=(56.0, 80.0),
    defeat_time=2.2,
    phases=[
        Phase(
            "placa",  # verbo: aprender — PENDENTE placas/pilares; o olho apaga 2 s após cada rajada
            1.0,
            [dart_attack(speed=240, telegraph=0.75, recover=2.0, count=1)],
            idle_time=1.0,
            intro_time=1.4,
            dialogue="bosses.oculus.intro",
            retaliation=retaliation("sand_pulse", 0.75, 60.0),
        ),
        Phase(
            "previsão",  # verbo: antecipar — teletransporte sinalizado + rajada dupla
            0.67,
            [
                teleport_attack(telegraph=0.75, recover=0.9),
                dart_attack(
                    speed=240, telegraph=0.75, recover=2.0, count=2, gap=0.45, name="double_dart"
                ),
            ],
            idle_time=0.9,
            max_hazards=2,
            retaliation=retaliation("sand_pulse", 0.75, 60.0),
        ),
        Phase(
            "tempestade",  # verbo: administrar — rocha a cada ciclo + mira prevista (x + vx·0,4)
            0.34,
            [
                ground_roller_attack(speed=260, telegraph=0.9, recover=1.0, name="boulder"),
                dart_attack(
                    speed=240,
                    telegraph=0.64,
                    recover=2.0,
                    count=2,
                    gap=0.45,
                    predict=0.4,
                    name="predicted_dart",
                ),
                teleport_attack(telegraph=0.7, recover=0.9),
            ],
            idle_time=0.8,
            max_hazards=2,
        ),
    ],
)


# --------------------------------------------------------------- Brumo (M3)
BRUMO = BossDefinition(
    kind="brumo",
    hp=3,
    world=3,
    name_key="bosses.brumo.name",
    size=(92.0, 76.0),
    defeat_time=2.4,
    phases=[
        Phase(
            "tremor",  # verbo: estar no ar — onda de choque saltável; cabeça baixa 1,6 s
            1.0,
            [
                shockwave_attack(speed=320, telegraph=0.7, recover=1.6, name="flipper_slam"),
                charge_attack(
                    speed=280,
                    telegraph=0.8,
                    active=1.4,
                    recover=0.9,
                    name="slide",
                    ends_on_wall=True,
                ),
            ],
            idle_time=1.0,
            intro_time=1.5,
            dialogue="bosses.brumo.intro",
            retaliation=retaliation("spin", 0.65, 50.0, active=1.2),
        ),
        Phase(
            "buraco",  # verbo: atrair — PENDENTE gelo quebrável; estalactite na coluna observada
            0.67,
            [
                shockwave_attack(speed=320, telegraph=0.7, recover=1.2, name="flipper_slam"),
                charge_attack(
                    speed=280,
                    telegraph=0.8,
                    active=1.4,
                    recover=2.0,
                    name="slide_trap",
                    ends_on_wall=True,
                ),
                drop_attack(fall_speed=520, telegraph=0.9, recover=0.8, name="stalactite"),
            ],
            idle_time=0.9,
            max_hazards=2,
            retaliation=retaliation("spin", 0.65, 50.0, active=1.2),
        ),
        Phase(
            "cascos",  # verbo: usar projétil — só o casco deslizante fere; batida dupla e bola de neve
            0.34,
            [
                shockwave_attack(speed=320, telegraph=0.56, recover=0.8, name="double_slam"),
                ground_roller_attack(speed=220, telegraph=0.56, recover=0.9, name="snowball"),
                spawn_shell_attack(telegraph=0.56, recover=0.8),
            ],
            idle_time=0.8,
            max_hazards=2,
            stompable=False,
            vulnerable_sources=frozenset({"shell"}),
            always_vulnerable_to=frozenset({"shell"}),
        ),
    ],
)


# --------------------------------------------------------------- Lumiá (M4)
@register
class LumiaCloneBehavior(Behavior):
    """Clone cinza (sem vagalumes): mergulha quando comandado; pisão o dissolve sem dano."""

    kind = "lumia_clone"
    uses_gravity = False
    collides_with_platforms = True
    clamps_patrol = True
    score = 0
    params = GuardianBehavior.params

    def __init__(self, enemy: Enemy) -> None:
        self.perch_y = enemy.y
        self.delay = 0.0
        self.target = (enemy.x, enemy.y)
        self.vel = (0.0, 0.0)
        super().__init__(enemy)

    def states(self) -> dict[EnemyStateName, State]:
        return {
            S.IDLE: State(
                S.IDLE,
                [
                    Transition(
                        S.PREPARE_ATTACK, lambda bb: bb.timer("dive") > 0 and bb.timer("delay") <= 0
                    )
                ],
                animation="hover",
            ),
            S.PREPARE_ATTACK: State(
                S.PREPARE_ATTACK,
                [],
                max_time=0.7,
                timeout_to=S.DIVE,
                animation="glow",
                telegraph=True,
            ),
            S.DIVE: State(
                S.DIVE,
                [Transition(S.RISE, lambda bb: bb.grounded)],
                max_time=1.2,
                timeout_to=S.RISE,
                animation="dive",
            ),
            S.RISE: State(
                S.RISE,
                [Transition(S.IDLE, lambda bb: bb.flags.get("at_perch", False))],
                animation="hover",
            ),
            S.DEFEATED: State(S.DEFEATED, animation="dissolve"),
        }

    def initial(self) -> EnemyStateName:
        return S.IDLE

    @property
    def harmless(self) -> bool:
        return self.state in (S.DEFEATED, S.IDLE, S.RISE)

    def command_dive(self, target_x: float, target_y: float, delay: float = 0.0) -> None:
        self.target = (target_x, target_y)
        self.bb.set_timer("dive", 5.0)
        self.bb.set_timer("delay", delay)

    def move(self, game: Game, dt: float) -> None:
        e, bb = self.enemy, self.bb
        if self.state == S.IDLE:
            e.vx = 0
            e.vy = 0
        elif self.state == S.PREPARE_ATTACK:
            e.vx = e.vy = 0
            if bb.time_in_state < dt * 1.5:
                game.events.append(GameEvent("telegraph"))
                dx = self.target[0] - e.x
                dy = (self.target[1] + 30 - e.h) - e.y
                length = max(1.0, (dx * dx + dy * dy) ** 0.5)
                self.vel = (520 * dx / length, 520 * max(0.2, dy / length))
                bb.set_timer("dive", 0.0)
        elif self.state == S.DIVE:
            e.vx, e.vy = self.vel
        elif self.state == S.RISE:
            e.vx = 0
            e.vy = -160.0
            if e.y <= self.perch_y:
                e.y = self.perch_y
                e.vy = 0
                bb.flags["at_perch"] = True
        elif self.state == S.DEFEATED:
            e.vx = e.vy = 0
            self.tick_defeated(game, dt, squash_time=0.35)
        if self.state != S.RISE:
            bb.flags["at_perch"] = False

    def on_stomp(self, game: Game) -> bool:
        if self.state != S.DEFEATED:
            self.defeat(game, pop=False, score=0)
        return True

    def on_hit(self, game: Game, damage: int, source: str = "stomp") -> bool:
        if self.state == S.DEFEATED:
            return False
        self.defeat(game, pop=False, score=0)
        return True


class LumiaBehavior(GuardianBehavior):
    """Mariposa guardiã: volta ao poleiro entre mergulhos; os clones somem com ela."""

    def move(self, game: Game, dt: float) -> None:
        e = self.enemy
        if self.state == S.IDLE and e.y > self.origin_y + 1:
            e.vx = 0
            e.vy = -160.0
            if e.y + e.vy * dt <= self.origin_y:
                e.vy = 0
                e.y = self.origin_y
            return
        super().move(game, dt)

    def on_hit(self, game: Game, damage: int, source: str = "stomp") -> bool:
        applied = super().on_hit(game, damage, source)
        if applied:
            for other in game.enemies:  # os clones trocam de lugar após o golpe
                if other.alive and other.kind == "lumia_clone":
                    other.x = self.enemy.patrol[1] - self.enemy.w - (other.x - self.enemy.patrol[0])
            if self.state == S.DEFEATED:
                for other in game.enemies:
                    if other.alive and other.kind == "lumia_clone":
                        other.alive = False
        return applied


LUMIA = BossDefinition(
    kind="lumia",
    hp=4,
    world=4,
    floats=True,
    name_key="bosses.lumia.name",
    size=(48.0, 64.0),
    defeat_time=2.3,
    vulnerable_states=frozenset({S.RECOVER, S.HURT}),
    phases=[
        Phase(
            "mergulho",  # verbo: tempo — mergulha até a posição observada e descansa 1,6 s
            1.0,
            [dive_attack(speed=520, telegraph=0.7, recover=1.6)],
            idle_time=1.0,
            intro_time=1.5,
            dialogue="bosses.lumia.intro",
        ),
        Phase(
            "identificação",  # verbo: distinguir — dois clones mergulham antes da verdadeira
            0.75,
            [
                clone_dives_attack(2, telegraph=0.7),
                dive_attack(speed=520, telegraph=0.7, recover=1.6),
                lob_attack(
                    count=2,
                    flight=1.6,
                    telegraph=0.7,
                    recover=0.8,
                    gravity=120.0,
                    spread=160.0,
                    name="spore_drift",
                ),
            ],
            idle_time=0.9,
            max_hazards=2,
        ),
        Phase(
            "penumbra",  # verbo: ler a luz — silhuetas; só os vagalumes da verdadeira ficam visíveis
            0.5,
            [
                clone_dives_attack(2, telegraph=0.6, gap=0.6),
                dive_attack(speed=520, telegraph=0.6, recover=1.4),
                teleport_attack(telegraph=0.6, recover=0.5, name="relocate"),
            ],
            idle_time=0.8,
            max_hazards=2,
            darkness=True,
        ),
    ],
)


# ------------------------------------------------------------ Fornalho (M5)
FORNALHO = BossDefinition(
    kind="fornalho",
    hp=5,
    world=5,
    name_key="bosses.fornalho.name",
    size=(84.0, 88.0),
    defeat_time=2.5,
    phases=[
        Phase(
            "ponte",  # verbo: saltar o tremor — martelo preso 1,2 s = vulnerável
            1.0,
            [
                shockwave_attack(speed=300, telegraph=0.6, recover=1.2, name="hammer_slam"),
                lob_attack(count=1, flight=1.1, telegraph=0.65, recover=1.0, name="magma_drop"),
            ],
            idle_time=0.9,
            intro_time=1.5,
            dialogue="bosses.fornalho.intro",
            retaliation=retaliation("chains", 0.45, 60.0, active=1.3),
        ),
        Phase(
            "plataformas",  # verbo: gerenciar o chão — PENDENTE lava cíclica/plataformas que afundam
            0.6,
            [
                pounce_attack(flight=0.8, telegraph=0.7, recover=1.0, name="platform_leap"),
                shockwave_attack(speed=300, telegraph=0.6, recover=1.0, name="hammer_slam"),
                lob_attack(
                    count=3,
                    flight=0.9,
                    telegraph=0.6,
                    recover=0.8,
                    gravity=800.0,
                    spread=40.0,
                    name="sparks",
                ),
            ],
            idle_time=0.8,
            max_hazards=3,
            retaliation=retaliation("chains", 0.45, 60.0, active=1.3),
        ),
        Phase(
            "a última chama",  # verbo: correr — onda de magma a 0,8× a corrida; PENDENTE corredor + alavanca
            0.2,
            [
                wave_attack(speed=270, telegraph=1.2, recover=2.2),
                shockwave_attack(speed=300, telegraph=0.45, recover=0.9, name="hammer_slam"),
            ],
            idle_time=0.7,
            max_hazards=2,
        ),
    ],
)

GUARDIANS: list[BossDefinition] = [ROLAO, OCULUS, BRUMO, LUMIA, FORNALHO]


def register_all() -> None:
    register_guardian(ROLAO, RolaoBehavior)
    register_guardian(OCULUS)
    register_guardian(BRUMO)
    register_guardian(LUMIA, LumiaBehavior)
    register_guardian(FORNALHO)


register_all()
