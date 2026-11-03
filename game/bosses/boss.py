"""Motor genérico de chefes com fases, ataques sinalizados e janelas de vulnerabilidade.

Princípios (docs/research/CHEFES.md, requisitos do projeto):

* todo ataque tem **telegraph** (preparação visível ≥ 0,3 s), fase ativa e
  recuperação; a recuperação e a espera são janelas de vulnerabilidade;
* as fases são definidas por fração de vida e trocam o **conjunto** de
  ataques (não só a velocidade); a troca é anunciada por uma pausa;
* o chefe só usa informação observável (posição do jogador, distância) e os
  ataques são escolhidos em sequência fixa por fase, para serem aprendíveis;
* a derrota tem tempo de animação antes de o chefe deixar de existir.

O ``GuardianBehavior`` é um arquétipo moderno (``game/enemies/behaviors.py``)
e usa o mesmo passo físico dos demais inimigos.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from game.core.interactions import burst
from game.core.types import Enemy, GameEvent, Projectile
from game.enemies.behaviors import ArchetypeParams, Behavior
from game.enemies.perception import PerceptionProfile
from game.enemies.state_machine import Blackboard, EnemyStateName, State, Transition

if TYPE_CHECKING:
    from game.core.game import Game

S = EnemyStateName
MIN_TELEGRAPH = 0.3

AttackHook = Callable[["Game", Enemy, "GuardianBehavior"], None]
AttackTick = Callable[["Game", Enemy, "GuardianBehavior", float], None]


@dataclass(slots=True)
class Attack:
    name: str
    telegraph: float
    active: float
    recover: float
    start: AttackHook | None = None
    tick: AttackTick | None = None
    end: AttackHook | None = None
    min_distance: float = 0.0
    max_distance: float = float("inf")
    animation: str = "attack"


@dataclass(slots=True)
class Phase:
    name: str
    enter_below: float  # fase ativa quando vida/máx <= este valor (1.0 = desde o início)
    attacks: list[Attack]
    idle_time: float = 0.9
    speed_multiplier: float = 1.0
    intro_time: float = 0.8
    dialogue: str | None = None


@dataclass(slots=True)
class BossDefinition:
    kind: str
    hp: int
    phases: list[Phase]
    hurt_time: float = 0.65
    defeat_time: float = 1.6
    intro_distance: float = 520.0  # começa quando o jogador se aproxima
    contact_hurts: bool = True
    vulnerable_states: frozenset[EnemyStateName] = field(
        default_factory=lambda: frozenset({S.IDLE, S.RECOVER, S.HURT})
    )
    score: int = 5000

    def validate(self) -> list[str]:
        """Invariantes de justiça: telegraph mínimo, recuperação, fases ordenadas e distintas."""
        problems: list[str] = []
        if not self.phases:
            return ["sem fases"]
        last = 1.01
        for phase in self.phases:
            if phase.enter_below > last:
                problems.append(f"fase {phase.name}: limiar {phase.enter_below} fora de ordem")
            last = phase.enter_below
            if not phase.attacks:
                problems.append(f"fase {phase.name}: sem ataques")
            for attack in phase.attacks:
                if attack.telegraph < MIN_TELEGRAPH:
                    problems.append(
                        f"{phase.name}/{attack.name}: telegraph {attack.telegraph:.2f} s < {MIN_TELEGRAPH} s"
                    )
                if attack.recover <= 0:
                    problems.append(f"{phase.name}/{attack.name}: sem janela de recuperação")
                if attack.active <= 0:
                    problems.append(f"{phase.name}/{attack.name}: fase ativa vazia")
        names = [tuple(a.name for a in phase.attacks) for phase in self.phases]
        if len(names) > 1 and len(set(names)) == 1:
            problems.append("as fases têm exatamente os mesmos ataques (só velocidade não basta)")
        return problems


class GuardianBehavior(Behavior):
    """Arquétipo de chefe dirigido por ``BossDefinition``."""

    kind = "guardian"
    is_boss = True
    definition: BossDefinition
    params = ArchetypeParams(
        stompable=True,
        hp=4,
        perception=PerceptionProfile(
            sight_range=900,
            sight_height=400,
            field_of_view_behind=900,
            needs_line_of_sight=False,
            reaction_time=0.0,
            forget_time=5.0,
        ),
    )

    def __init__(self, enemy: Enemy, definition: BossDefinition | None = None) -> None:
        self.definition = definition or DEFAULT_GUARDIAN
        self.phase_index = 0
        self.attack_index = 0
        self.current_attack: Attack | None = None
        self.attack_clock = 0.0
        self.defeat_clock = 0.0
        self.started = False
        self.pending_phase: int | None = None
        enemy.health = self.definition.hp
        enemy.hp = self.definition.hp
        super().__init__(enemy)

    # ------------------------------------------------------------ estados
    def initial(self) -> EnemyStateName:
        return S.HIDDEN  # "esperando" o jogador chegar à arena

    @property
    def phase(self) -> Phase:
        return self.definition.phases[self.phase_index]

    @property
    def vulnerable(self) -> bool:
        return self.state in self.definition.vulnerable_states

    def states(self) -> dict[EnemyStateName, State]:
        d = self.definition
        return {
            S.HIDDEN: State(
                S.HIDDEN,
                [
                    Transition(
                        S.EMERGE,
                        lambda bb: bb.player_distance <= d.intro_distance,
                        "jogador chegou",
                    )
                ],
                animation="idle",
            ),
            S.EMERGE: State(
                S.EMERGE,
                [],
                max_time=d.phases[0].intro_time,
                timeout_to=S.IDLE,
                animation="intro",
                telegraph=True,
            ),
            S.IDLE: State(
                S.IDLE,
                [Transition(S.PREPARE_ATTACK, self._idle_done, "próximo ataque")],
                animation="idle",
            ),
            S.PREPARE_ATTACK: State(
                S.PREPARE_ATTACK,
                [Transition(S.ATTACK, self._telegraph_done)],
                animation="prepare",
                telegraph=True,
                on_enter=self._choose_attack,
            ),
            S.ATTACK: State(
                S.ATTACK,
                [Transition(S.RECOVER, self._attack_done)],
                animation="attack",
                on_enter=self._start_attack,
                on_exit=self._end_attack,
            ),
            S.RECOVER: State(
                S.RECOVER, [Transition(S.IDLE, self._recover_done)], animation="recover"
            ),
            S.HURT: State(S.HURT, [], max_time=d.hurt_time, timeout_to=S.IDLE, animation="hurt"),
            S.STUNNED: State(
                S.STUNNED,
                [],
                max_time=d.phases[0].intro_time,
                timeout_to=S.IDLE,
                animation="phase_change",
                telegraph=True,
                on_exit=self._apply_phase,
            ),
            S.DEFEATED: State(S.DEFEATED, animation="defeated"),
        }

    # ------------------------------------------------------- transições
    def _idle_done(self, bb: Blackboard) -> bool:
        return bb.time_in_state >= self.phase.idle_time

    def _telegraph_done(self, bb: Blackboard) -> bool:
        return self.current_attack is not None and bb.time_in_state >= self.current_attack.telegraph

    def _attack_done(self, bb: Blackboard) -> bool:
        return self.current_attack is not None and bb.time_in_state >= self.current_attack.active

    def _recover_done(self, bb: Blackboard) -> bool:
        return self.current_attack is not None and bb.time_in_state >= self.current_attack.recover

    def _choose_attack(self, bb: Blackboard) -> None:
        attacks = self.phase.attacks
        for _ in range(len(attacks)):
            attack = attacks[self.attack_index % len(attacks)]
            self.attack_index += 1
            if attack.min_distance <= bb.player_distance <= attack.max_distance:
                self.current_attack = attack
                return
        self.current_attack = attacks[(self.attack_index - 1) % len(attacks)]

    def _start_attack(self, bb: Blackboard) -> None:
        self.attack_clock = 0.0
        self._pending_start = True

    def _end_attack(self, bb: Blackboard) -> None:
        self._pending_end = True

    def _apply_phase(self, bb: Blackboard) -> None:
        if self.pending_phase is not None:
            self.phase_index = self.pending_phase
            self.pending_phase = None
            self.attack_index = 0

    # --------------------------------------------------------------- passo
    _pending_start: bool = False
    _pending_end: bool = False

    def step(self, game: Game, dt: float) -> None:
        e = self.enemy
        self.observe(game, dt)
        previous = self.state
        self.fsm.update(dt, self.bb)
        e.anim = self.fsm.current.animation
        e.telegraph = self.fsm.current.telegraph
        e.stompable = self.vulnerable
        e.state = (
            "shell" if self.vulnerable else "walk"
        )  # compatibilidade com HUD/renderização legadas
        if self.state == S.EMERGE and previous == S.HIDDEN:
            self.started = True
            game.events.append(GameEvent("boss_intro", text=self.phase.dialogue))
        if self._pending_start and self.current_attack is not None:
            self._pending_start = False
            if self.current_attack.start is not None:
                self.current_attack.start(game, e, self)
        if self._pending_end and self.current_attack is not None:
            self._pending_end = False
            if self.current_attack.end is not None:
                self.current_attack.end(game, e, self)
        if self.state == S.ATTACK and self.current_attack is not None:
            self.attack_clock += dt
            if self.current_attack.tick is not None:
                self.current_attack.tick(game, e, self, dt)
        elif self.state == S.DEFEATED:
            e.vx = 0
            self.defeat_clock += dt
            if self.defeat_clock >= self.definition.defeat_time:
                e.alive = False
        else:
            self.move(game, dt)

    def move(self, game: Game, dt: float) -> None:
        e = self.enemy
        if self.state in (
            S.IDLE,
            S.PREPARE_ATTACK,
            S.RECOVER,
            S.HURT,
            S.STUNNED,
            S.EMERGE,
            S.HIDDEN,
        ):
            e.vx = 0
            if self.bb.player_dx != 0 and self.state != S.HURT:
                e.facing = 1 if self.bb.player_dx > 0 else -1

    # ---------------------------------------------------------------- dano
    def on_hit(self, game: Game, damage: int, source: str = "stomp") -> bool:
        e = self.enemy
        if not e.alive or e.hit_timer > 0 or not self.vulnerable or self.state == S.DEFEATED:
            return False
        e.health -= damage
        e.hit_timer = self.definition.hurt_time
        burst(game, e.x + e.w / 2, e.y, "#ffdc87")
        if e.health <= 0:
            e.health = 0
            game.score += self.definition.score
            game.shake = 0.3
            burst(game, e.x, e.y, "#73ffe1", 30)
            game.events.append(GameEvent("boss", text="Guardião derrotado!"))
            self.fsm.force(S.DEFEATED, self.bb)
            return True
        game.events.append(GameEvent("stomp"))
        fraction = e.health / self.definition.hp
        for index, phase in enumerate(self.definition.phases):
            if index > self.phase_index and fraction <= phase.enter_below:
                self.pending_phase = index
        if self.pending_phase is not None:
            game.events.append(GameEvent("boss_phase", value=self.pending_phase + 1))
            self.fsm.force(S.STUNNED, self.bb)
        else:
            self.fsm.force(S.HURT, self.bb)
        return True

    def on_touch(self, game: Game) -> None:
        if self.definition.contact_hurts and self.state != S.DEFEATED:
            game.hurt()


# ------------------------------------------------------------ ataques base
def charge_attack(
    speed: float = 170.0, telegraph: float = 0.45, active: float = 1.1, recover: float = 0.9
) -> Attack:
    """Investida: encara, agacha (telegraph) e avança na direção do jogador."""

    def start(game: Game, e: Enemy, boss: GuardianBehavior) -> None:
        e.facing = 1 if game.player.x > e.x else -1

    def tick(game: Game, e: Enemy, boss: GuardianBehavior, dt: float) -> None:
        e.vx = e.facing * speed * boss.phase.speed_multiplier

    def end(game: Game, e: Enemy, boss: GuardianBehavior) -> None:
        e.vx = 0

    return Attack(
        "charge", telegraph, active, recover, start=start, tick=tick, end=end, animation="charge"
    )


def shoot_attack(
    count: int = 1,
    speed: float = 190.0,
    telegraph: float = 0.5,
    recover: float = 0.7,
    spread: float = 0.0,
) -> Attack:
    """Disparo(s) na direção observada do jogador; a quantidade e o leque mudam por fase."""

    def start(game: Game, e: Enemy, boss: GuardianBehavior) -> None:
        direction = 1 if game.player.x > e.x else -1
        e.facing = direction
        for i in range(count):
            vy = -spread * (i - (count - 1) / 2) if count > 1 else 0.0
            game.projectiles.append(
                Projectile(
                    x=e.x + e.w / 2,
                    y=e.y + 24,
                    w=14,
                    h=14,
                    vx=direction * speed * boss.phase.speed_multiplier,
                    vy=vy,
                    hostile=True,
                    life=4,
                    alive=True,
                )
            )
        game.events.append(GameEvent("shot"))

    def tick(game: Game, e: Enemy, boss: GuardianBehavior, dt: float) -> None:
        e.vx = 0

    return Attack("shoot", telegraph, 0.25, recover, start=start, tick=tick, animation="shoot")


def leap_attack(
    vy: float = -430.0,
    vx: float = 120.0,
    telegraph: float = 0.4,
    active: float = 0.9,
    recover: float = 0.8,
) -> Attack:
    """Salto em arco na direção do jogador (evitável passando por baixo)."""

    def start(game: Game, e: Enemy, boss: GuardianBehavior) -> None:
        e.facing = 1 if game.player.x > e.x else -1
        if e.grounded:
            e.vy = vy

    def tick(game: Game, e: Enemy, boss: GuardianBehavior, dt: float) -> None:
        e.vx = e.facing * vx * boss.phase.speed_multiplier

    def end(game: Game, e: Enemy, boss: GuardianBehavior) -> None:
        e.vx = 0

    return Attack(
        "leap", telegraph, active, recover, start=start, tick=tick, end=end, animation="leap"
    )


DEFAULT_GUARDIAN = BossDefinition(
    kind="guardian",
    hp=6,
    phases=[
        Phase(
            "apresentação",
            1.0,
            [charge_attack(), shoot_attack()],
            idle_time=1.0,
            speed_multiplier=1.0,
        ),
        Phase(
            "combinação",
            0.67,
            [charge_attack(active=0.9), shoot_attack(count=2, spread=60), leap_attack()],
            idle_time=0.8,
            speed_multiplier=1.15,
        ),
        Phase(
            "fúria",
            0.34,
            [
                leap_attack(),
                charge_attack(telegraph=0.35, active=0.8),
                shoot_attack(count=3, spread=70, telegraph=0.4),
            ],
            idle_time=0.6,
            speed_multiplier=1.3,
        ),
    ],
)


def register_guardian(definition: BossDefinition = DEFAULT_GUARDIAN) -> None:
    """Registra o arquétipo ``definition.kind`` para uso em fases (``kind`` no JSON)."""
    from game.enemies.behaviors import ARCHETYPES

    class _Bound(GuardianBehavior):
        kind = definition.kind

        def __init__(self, enemy: Enemy) -> None:
            super().__init__(enemy, definition)

    ARCHETYPES[definition.kind] = _Bound


def definitions() -> dict[str, BossDefinition]:
    return {DEFAULT_GUARDIAN.kind: DEFAULT_GUARDIAN}


register_guardian(DEFAULT_GUARDIAN)
