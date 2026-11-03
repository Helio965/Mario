"""Motor genérico de chefes com fases, ataques sinalizados e janelas de vulnerabilidade.

Princípios (docs/research/CHEFES.md §6–§7):

* todo ataque tem **telegraph** (preparação visível) com piso por mundo
  (900/750/650/550/450 ms, piso absoluto 400 ms), fase ativa ≤ 1,6 s e
  recuperação; recuperação e espera são janelas de vulnerabilidade;
* as fases são definidas por fração de vida e trocam o **conjunto** de
  ataques (um verbo novo por fase); a troca é anunciada por uma pausa;
* o chefe só usa informação observável: a posição/velocidade do jogador é
  lida no **primeiro quadro do telegraph e congelada** (``target``);
* após sofrer um golpe o chefe fica imune 0,65 s e pode **retaliar** com um
  ataque sinalizado (``Phase.retaliation``);
* perigos simultâneos limitados por fase (``Phase.max_hazards``);
* a derrota tem tempo de animação antes de o chefe deixar de existir.

O ``GuardianBehavior`` é um arquétipo moderno (``game/enemies/behaviors.py``)
e usa o mesmo passo físico dos demais inimigos. As cinco definições
originais do Lume estão em ``game/bosses/guardians.py``.
"""

from __future__ import annotations

import itertools
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
MIN_TELEGRAPH = 0.3  # chefes genéricos (world 0)
MIN_TELEGRAPH_BY_WORLD: dict[int, float] = {1: 0.9, 2: 0.75, 3: 0.65, 4: 0.55, 5: 0.45}
MIN_TELEGRAPH_FLOOR = 0.4
MAX_ACTIVE = 1.6
PHASE3_TELEGRAPH_REDUCTION = 0.85

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
    counter: str = (
        "jump"  # contramedida documentada: jump | run_away | move_away | stay | jump_wave
    )
    hazards: int = 1  # perigos simultâneos que este ataque cria
    ends_on_wall: bool = False  # investidas: termina ao bater numa parede


@dataclass(slots=True)
class Phase:
    name: str
    enter_below: float  # fase ativa quando vida/máx <= este valor (1.0 = desde o início)
    attacks: list[Attack]
    idle_time: float = 0.9
    speed_multiplier: float = 1.0
    intro_time: float = 0.8
    dialogue: str | None = None
    retaliation: Attack | None = None
    max_hazards: int = 1
    stompable: bool = True
    vulnerable_sources: frozenset[str] = field(
        default_factory=lambda: frozenset({"stomp", "fire", "shell", "star"})
    )
    always_vulnerable_to: frozenset[str] = field(
        default_factory=frozenset
    )  # ex.: casco deslizante em qualquer estado
    darkness: bool = False  # arena escurece (silhuetas); a renderização lê ``behavior.darkness``


@dataclass(slots=True)
class BossDefinition:
    kind: str
    hp: int
    phases: list[Phase]
    world: int = 0
    hurt_time: float = 0.65
    defeat_time: float = 1.6
    intro_distance: float = 520.0  # começa quando o jogador se aproxima
    contact_hurts: bool = True
    floats: bool = False  # sem gravidade (sentinelas, mariposa)
    vulnerable_states: frozenset[EnemyStateName] = field(
        default_factory=lambda: frozenset({S.IDLE, S.RECOVER, S.HURT})
    )
    score: int = 5000
    name_key: str = ""
    size: tuple[float, float] = (62.0, 64.0)

    def telegraph_floor(self, phase_index: int = 0) -> float:
        base = MIN_TELEGRAPH_BY_WORLD.get(self.world, MIN_TELEGRAPH)
        if self.world and phase_index >= 2:
            base = max(MIN_TELEGRAPH_FLOOR, base * PHASE3_TELEGRAPH_REDUCTION)
        return base

    def validate(self) -> list[str]:
        """Invariantes de justiça: telegraph por mundo, recuperação, fases ordenadas e distintas."""
        problems: list[str] = []
        if not self.phases:
            return ["sem fases"]
        last = 1.01
        for index, phase in enumerate(self.phases):
            if phase.enter_below > last:
                problems.append(f"fase {phase.name}: limiar {phase.enter_below} fora de ordem")
            last = phase.enter_below
            if not phase.attacks:
                problems.append(f"fase {phase.name}: sem ataques")
            floor = self.telegraph_floor(index)
            for attack in [*phase.attacks, *([phase.retaliation] if phase.retaliation else [])]:
                if attack.telegraph + 1e-9 < floor:
                    problems.append(
                        f"{phase.name}/{attack.name}: telegraph {attack.telegraph:.2f} s < piso {floor:.2f} s"
                    )
                if attack.recover <= 0 and attack is not phase.retaliation:
                    problems.append(f"{phase.name}/{attack.name}: sem janela de recuperação")
                if attack.active <= 0:
                    problems.append(f"{phase.name}/{attack.name}: fase ativa vazia")
                if attack.active > MAX_ACTIVE + 1e-9 and not attack.ends_on_wall:
                    problems.append(
                        f"{phase.name}/{attack.name}: fase ativa {attack.active:.2f} s > {MAX_ACTIVE} s"
                    )
                if attack.hazards > phase.max_hazards:
                    problems.append(
                        f"{phase.name}/{attack.name}: cria {attack.hazards} perigos > máximo {phase.max_hazards}"
                    )
            if index == 0 and phase.max_hazards > 1:
                problems.append("fase 1 deve ter no máximo 1 perigo simultâneo")
        names = [tuple(a.name for a in phase.attacks) for phase in self.phases]
        if len(names) > 1 and len(set(names)) == 1:
            problems.append("as fases têm exatamente os mesmos ataques (só velocidade não basta)")
        for a, b in itertools.pairwise(names):
            if set(b) <= set(a):
                problems.append(f"a fase seguinte a {a} não acrescenta nenhum ataque novo")
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
        self.retaliating = False
        self.target_x = 0.0
        self.target_y = 0.0
        self.target_vx = 0.0
        self.darkness = False
        self.light_timer = 0.0
        self.origin_x = enemy.x
        self.origin_y = enemy.y
        self.data: dict[str, float] = {}  # memória livre dos ataques (contadores, posições)
        self._pending_start = False
        self._pending_end = False
        enemy.health = self.definition.hp
        enemy.hp = self.definition.hp
        super().__init__(enemy)
        self.uses_gravity = not self.definition.floats

    # ------------------------------------------------------------ estados
    def initial(self) -> EnemyStateName:
        return S.HIDDEN  # "esperando" o jogador chegar à arena

    @property
    def phase(self) -> Phase:
        return self.definition.phases[self.phase_index]

    @property
    def vulnerable(self) -> bool:
        return self.state in self.definition.vulnerable_states and not self.retaliating

    @property
    def harmless(self) -> bool:
        return self.state in (S.HIDDEN, S.DEFEATED)

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
            S.HURT: State(
                S.HURT,
                [
                    Transition(S.PREPARE_ATTACK, self._hurt_done_retaliate),
                    Transition(S.IDLE, self._hurt_done),
                ],
                animation="hurt",
            ),
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
        attack = self.current_attack
        if attack is None:
            return True
        if attack.ends_on_wall and bb.time_in_state > 0.1:
            e = self.enemy
            at_edge = e.x <= e.patrol[0] + 1 or e.x + e.w >= e.patrol[1] - 1
            if bb.hit_wall or at_edge:
                return True
        return bb.time_in_state >= attack.active

    def _recover_done(self, bb: Blackboard) -> bool:
        return self.current_attack is not None and bb.time_in_state >= self.current_attack.recover

    def _hurt_done_retaliate(self, bb: Blackboard) -> bool:
        return bb.time_in_state >= self.definition.hurt_time and self.phase.retaliation is not None

    def _hurt_done(self, bb: Blackboard) -> bool:
        return bb.time_in_state >= self.definition.hurt_time

    def _choose_attack(self, bb: Blackboard) -> None:
        attacks = self.phase.attacks
        if self.retaliating and self.phase.retaliation is not None:
            self.current_attack = self.phase.retaliation
        else:
            chosen: Attack | None = None
            for _ in range(len(attacks)):
                attack = attacks[self.attack_index % len(attacks)]
                self.attack_index += 1
                if attack.min_distance <= bb.player_distance <= attack.max_distance:
                    chosen = attack
                    break
            self.current_attack = chosen or attacks[(self.attack_index - 1) % len(attacks)]
        # Alvo congelado no 1.º quadro do telegraph (informação observável).
        self.target_x = self._player_x
        self.target_y = self._player_y
        self.target_vx = self._player_vx
        self._game.events.append(GameEvent("boss_telegraph", text=self.current_attack.name))

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
            self.darkness = self.phase.darkness

    # --------------------------------------------------------------- passo
    _game: Game
    _player_x: float = 0.0
    _player_y: float = 0.0
    _player_vx: float = 0.0

    def step(self, game: Game, dt: float) -> None:
        e = self.enemy
        self._game = game
        self._player_x, self._player_y, self._player_vx = (
            game.player.x,
            game.player.y,
            game.player.vx,
        )
        self.observe(game, dt)
        previous = self.state
        self.fsm.update(dt, self.bb)
        e.anim = self.fsm.current.animation
        e.telegraph = self.fsm.current.telegraph
        e.stompable = self.vulnerable and self.phase.stompable
        e.state = (
            "shell" if self.vulnerable else "walk"
        )  # compatibilidade com HUD/renderização legadas
        if self.light_timer > 0:
            self.light_timer = max(0.0, self.light_timer - dt)
            self.darkness = False if self.light_timer > 0 else self.phase.darkness
        if self.state == S.EMERGE and previous == S.HIDDEN:
            self.started = True
            game.events.append(GameEvent("boss_intro", text=self.phase.dialogue))
        if self.state != S.PREPARE_ATTACK and self.state != S.ATTACK and self.state != S.RECOVER:
            self.retaliating = False
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
        self.bb.just_landed = False
        self.bb.hit_enemy = False
        self.bb.hit_wall = False

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
            if self.definition.floats:
                e.vy = 0
            if self.bb.player_dx != 0 and self.state != S.HURT:
                e.facing = 1 if self.bb.player_dx > 0 else -1

    # ---------------------------------------------------------- perigos
    def active_hazards(self, game: Game) -> int:
        return sum(1 for s in game.projectiles if s.alive and s.owner == self.enemy.id)

    def hazard_budget(self, game: Game) -> int:
        return max(0, self.phase.max_hazards - self.active_hazards(game))

    def launch(
        self,
        game: Game,
        vx: float,
        vy: float,
        w: float = 14,
        h: float = 14,
        life: float = 4.0,
        gravity: float = 0.0,
        x: float | None = None,
        y: float | None = None,
        hostile: bool = True,
    ) -> Projectile | None:
        """Projétil do chefe, contado no orçamento de perigos da fase."""
        if self.hazard_budget(game) <= 0:
            return None
        e = self.enemy
        projectile = Projectile(
            x=e.x + e.w / 2 - w / 2 if x is None else x,
            y=e.y + 24 if y is None else y,
            w=w,
            h=h,
            vx=vx,
            vy=vy,
            hostile=hostile,
            life=life,
            alive=True,
            gravity=gravity,
            owner=e.id,
        )
        game.projectiles.append(projectile)
        game.events.append(GameEvent("shot"))
        return projectile

    # ---------------------------------------------------------------- dano
    def accepts(self, source: str) -> bool:
        return source in self.phase.vulnerable_sources or source in self.phase.always_vulnerable_to

    def on_hit(self, game: Game, damage: int, source: str = "stomp") -> bool:
        e = self.enemy
        if not e.alive or e.hit_timer > 0 or self.state == S.DEFEATED or not self.accepts(source):
            return False
        if source not in self.phase.always_vulnerable_to and not self.vulnerable:
            return False
        if source == "stomp" and not self.phase.stompable:
            return False
        e.health -= 1  # todo golpe vale um ponto (equivalência de projétil fica no chamador)
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
            if index > self.phase_index and fraction <= phase.enter_below + 1e-9:
                self.pending_phase = index
        if self.pending_phase is not None:
            upcoming = self.definition.phases[self.pending_phase]
            game.events.append(
                GameEvent("boss_phase", value=self.pending_phase + 1, text=upcoming.name)
            )
            self.fsm.force(
                S.STUNNED, self.bb
            )  # troca anunciada: a fase nova vale ao fim do atordoamento
        else:
            self.retaliating = self.phase.retaliation is not None
            self.fsm.force(S.HURT, self.bb)
        if self.phase.darkness and self.light_timer == 0:
            self.light_timer = 3.0  # a luz volta por 3 s após um golpe (penumbra)
        return True

    def on_stomp(self, game: Game) -> bool:
        return self.on_hit(game, 1, "stomp")

    def on_touch(self, game: Game) -> None:
        if self.definition.contact_hurts and not self.harmless:
            game.hurt()

    def dizzy(self, game: Game, seconds: float) -> None:
        """Interrompe o ataque atual e abre uma janela de vulnerabilidade (fruta, buraco, casco)."""
        if self.state in (S.DEFEATED, S.HIDDEN, S.STUNNED):
            return
        self.retaliating = False
        self.current_attack = Attack("dizzy", 0.0, 0.0, seconds, counter="stay")
        self.fsm.force(S.RECOVER, self.bb)
        self.enemy.vx = 0
        game.events.append(GameEvent("impact"))


# ------------------------------------------------------------ ataques base
def charge_attack(
    speed: float = 170.0,
    telegraph: float = 0.45,
    active: float = 1.1,
    recover: float = 0.9,
    name: str = "charge",
    ends_on_wall: bool = False,
) -> Attack:
    """Investida: encara, agacha (telegraph) e avança na direção do jogador."""

    def start(game: Game, e: Enemy, boss: GuardianBehavior) -> None:
        e.facing = 1 if boss.target_x > e.x else -1

    def tick(game: Game, e: Enemy, boss: GuardianBehavior, dt: float) -> None:
        e.vx = e.facing * speed * boss.phase.speed_multiplier

    def end(game: Game, e: Enemy, boss: GuardianBehavior) -> None:
        e.vx = 0

    return Attack(
        name,
        telegraph,
        active,
        recover,
        start=start,
        tick=tick,
        end=end,
        animation="charge",
        counter="run_away",
        ends_on_wall=ends_on_wall,
    )


def shoot_attack(
    count: int = 1,
    speed: float = 190.0,
    telegraph: float = 0.5,
    recover: float = 0.7,
    spread: float = 0.0,
    name: str = "shoot",
) -> Attack:
    """Disparo(s) na direção observada do jogador; a quantidade e o leque mudam por fase."""

    def start(game: Game, e: Enemy, boss: GuardianBehavior) -> None:
        direction = 1 if boss.target_x > e.x else -1
        e.facing = direction
        for i in range(count):
            vy = -spread * (i - (count - 1) / 2) if count > 1 else 0.0
            boss.launch(game, direction * speed * boss.phase.speed_multiplier, vy)

    def tick(game: Game, e: Enemy, boss: GuardianBehavior, dt: float) -> None:
        e.vx = 0

    return Attack(
        name,
        telegraph,
        0.25,
        recover,
        start=start,
        tick=tick,
        animation="shoot",
        counter="jump",
        hazards=count,
    )


def leap_attack(
    vy: float = -430.0,
    vx: float = 120.0,
    telegraph: float = 0.4,
    active: float = 0.9,
    recover: float = 0.8,
    name: str = "leap",
) -> Attack:
    """Salto em arco na direção do jogador (evitável passando por baixo)."""

    def start(game: Game, e: Enemy, boss: GuardianBehavior) -> None:
        e.facing = 1 if boss.target_x > e.x else -1
        if e.grounded or boss.definition.floats:
            e.vy = vy

    def tick(game: Game, e: Enemy, boss: GuardianBehavior, dt: float) -> None:
        e.vx = e.facing * vx * boss.phase.speed_multiplier

    def end(game: Game, e: Enemy, boss: GuardianBehavior) -> None:
        e.vx = 0

    return Attack(
        name,
        telegraph,
        active,
        recover,
        start=start,
        tick=tick,
        end=end,
        animation="leap",
        counter="move_away",
    )


DEFAULT_GUARDIAN = BossDefinition(
    kind="guardian",
    hp=6,
    world=0,
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
            max_hazards=2,
        ),
        Phase(
            "fúria",
            0.34,
            [
                leap_attack(),
                charge_attack(telegraph=0.35, active=0.8),
                shoot_attack(
                    count=3, spread=70, telegraph=0.4, name="volley"
                ),  # verbo novo da fase
            ],
            idle_time=0.6,
            speed_multiplier=1.3,
            max_hazards=3,
        ),
    ],
)


def register_guardian(
    definition: BossDefinition = DEFAULT_GUARDIAN, base: type[GuardianBehavior] = GuardianBehavior
) -> None:
    """Registra o arquétipo ``definition.kind`` para uso em fases (``kind`` no JSON)."""
    from game.enemies.behaviors import ARCHETYPES

    class _Bound(base):  # type: ignore[valid-type,misc]
        kind = definition.kind

        def __init__(self, enemy: Enemy) -> None:
            super().__init__(enemy, definition)

    _Bound.definition = definition  # consultável sem instanciar (validador de fases)

    ARCHETYPES[definition.kind] = _Bound


def definitions() -> dict[str, BossDefinition]:
    from game.bosses.guardians import GUARDIANS

    return {DEFAULT_GUARDIAN.kind: DEFAULT_GUARDIAN, **{g.kind: g for g in GUARDIANS}}


register_guardian(DEFAULT_GUARDIAN)
