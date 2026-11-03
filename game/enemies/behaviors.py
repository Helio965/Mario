"""Arquétipos modernos de inimigos: FSM + percepção + física compartilhada.

Cada arquétipo declara seus estados (apenas os relevantes), parâmetros
numéricos nomeados e reações a pisão/dano. O passo comum (``update_modern``)
cuida de percepção, física, limites de patrulha e colisão com o jogador,
mantendo os inimigos legados intocados.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from game.core.interactions import burst
from game.core.types import Enemy, GameEvent
from game.enemies.perception import Perception, PerceptionProfile, edge_ahead, wall_ahead
from game.enemies.state_machine import Blackboard, EnemyStateName, State, StateMachine, Transition
from game.physics.collision import move_body, overlaps
from game.physics.movement import GRAVITY

if TYPE_CHECKING:
    from game.core.game import Game

S = EnemyStateName


@dataclass(slots=True)
class ArchetypeParams:
    patrol_speed: float = 55.0
    chase_speed: float = 150.0
    alert_time: float = 0.35  # telegraph antes de perseguir
    chase_max: float = 2.5
    recover_time: float = 0.6
    hurt_time: float = 0.65
    hp: int = 1
    stompable: bool = True
    turns_at_edges: bool = True
    perception: PerceptionProfile = field(default_factory=PerceptionProfile)


class Behavior:
    """Base: guarda FSM, percepção e quadro-negro; subclasses definem estados e movimento."""

    kind = "base"
    params = ArchetypeParams()

    def __init__(self, enemy: Enemy) -> None:
        self.enemy = enemy
        self.bb = Blackboard(health=enemy.health, max_health=enemy.health)
        self.perception = Perception(self.params.perception)
        self.fsm = StateMachine(self.states(), self.initial())
        enemy.stompable = self.params.stompable
        enemy.anim = self.fsm.current.animation

    # ------------------------------------------------------- a definir
    def states(self) -> dict[EnemyStateName, State]:
        raise NotImplementedError

    def initial(self) -> EnemyStateName:
        return S.PATROL

    def move(self, game: Game, dt: float) -> None:
        """Define ``enemy.vx``/``facing`` conforme o estado atual."""
        raise NotImplementedError

    # ------------------------------------------------------------ comum
    @property
    def state(self) -> EnemyStateName:
        return self.fsm.name

    def observe(self, game: Game, dt: float) -> None:
        e = self.enemy
        facts = self.perception.observe(dt, e, game.player, e.facing, game.platforms)
        for key, value in facts.items():
            setattr(self.bb, key, value)
        self.bb.grounded = e.grounded
        self.bb.edge_ahead = e.grounded and edge_ahead(e, e.facing, game.platforms)
        self.bb.wall_ahead = wall_ahead(e, e.facing, game.platforms)
        self.bb.health = e.health
        self.bb.hurt = e.hit_timer > 0

    def step(self, game: Game, dt: float) -> None:
        self.observe(game, dt)
        self.fsm.update(dt, self.bb)
        self.enemy.anim = self.fsm.current.animation
        self.enemy.telegraph = self.fsm.current.telegraph
        self.move(game, dt)

    def on_hit(self, game: Game, damage: int) -> bool:
        """Dano recebido (pisão, projétil, casco, estrela). Devolve True se aplicou."""
        e = self.enemy
        if e.hit_timer > 0:
            return False
        e.health -= damage
        e.hit_timer = self.params.hurt_time
        burst(game, e.x + e.w / 2, e.y, "#ffdc87")
        if e.health <= 0:
            e.alive = False
            game.score += 200
            game.events.append(GameEvent("stomp"))
            self.fsm.force(S.DEFEATED, self.bb)
        else:
            game.events.append(GameEvent("stomp"))
            if S.HURT in self.fsm.states:
                self.fsm.force(S.HURT, self.bb)
        return True

    def on_touch(self, game: Game) -> None:
        """Contato lateral com o jogador: fere, salvo arquétipos inofensivos."""
        game.hurt()


class StalkerBehavior(Behavior):
    """Inimigo terrestre que patrulha, avisa (para e encara) e persegue por pouco tempo.

    Inspiração comportamental: Koopa Troopa vermelho (não cai de bordas) e
    perseguição curta "à Boo" em terra; design original do Lume.
    """

    kind = "stalker"
    params = ArchetypeParams(
        patrol_speed=55.0,
        chase_speed=140.0,
        alert_time=0.35,
        chase_max=2.2,
        recover_time=0.7,
        perception=PerceptionProfile(
            sight_range=300,
            sight_height=90,
            field_of_view_behind=20,
            attack_range=60,
            reaction_time=0.2,
            forget_time=1.0,
        ),
    )

    def states(self) -> dict[EnemyStateName, State]:
        p = self.params
        return {
            S.PATROL: State(
                S.PATROL,
                [Transition(S.ALERT, lambda bb: bb.player_visible, "avistou")],
                animation="walk",
            ),
            S.ALERT: State(
                S.ALERT,
                [],
                max_time=p.alert_time,
                timeout_to=S.CHASE,
                animation="alert",
                telegraph=True,
            ),
            S.CHASE: State(
                S.CHASE,
                [Transition(S.RECOVER, lambda bb: not bb.player_visible, "perdeu de vista")],
                min_time=0.3,
                max_time=p.chase_max,
                timeout_to=S.RECOVER,
                animation="run",
            ),
            S.RECOVER: State(
                S.RECOVER, [], max_time=p.recover_time, timeout_to=S.PATROL, animation="idle"
            ),
            S.HURT: State(S.HURT, [], max_time=p.hurt_time, timeout_to=S.PATROL, animation="hurt"),
            S.DEFEATED: State(S.DEFEATED, animation="defeated"),
        }

    def move(self, game: Game, dt: float) -> None:
        e, bb, p = self.enemy, self.bb, self.params
        state = self.state
        if state == S.PATROL:
            if bb.edge_ahead or bb.wall_ahead:
                e.facing *= -1
            e.vx = e.facing * p.patrol_speed
        elif state == S.ALERT:
            e.vx = 0
            if bb.player_dx != 0:
                e.facing = 1 if bb.player_dx > 0 else -1
        elif state == S.CHASE:
            if bb.player_dx != 0:
                e.facing = 1 if bb.player_dx > 0 else -1
            if p.turns_at_edges and (bb.edge_ahead or bb.wall_ahead):
                e.vx = 0
            else:
                e.vx = e.facing * p.chase_speed
        else:
            e.vx = 0


ARCHETYPES: dict[str, type[Behavior]] = {StalkerBehavior.kind: StalkerBehavior}


def create_behavior(enemy: Enemy) -> Behavior | None:
    cls = ARCHETYPES.get(enemy.kind)
    return cls(enemy) if cls is not None else None


def update_modern(game: Game, dt: float) -> None:
    """Passo dos inimigos com arquétipo moderno (chamado após o passo legado)."""
    player = game.player
    for e in game.enemies:
        behavior: Any = e.behavior
        if not e.alive or behavior is None:
            continue
        e.timer += dt
        e.hit_timer = max(0, e.hit_timer - dt)
        behavior.step(game, dt)
        e.vy = min(850, e.vy + GRAVITY * dt)
        before = e.vx
        hit = move_body(e, [s for s in game.platforms if s.kind != "hidden" or s.used], dt)
        e.grounded = hit.grounded
        if before != 0 and e.vx == 0 and behavior.state == S.PATROL:
            e.facing *= -1
        if e.x < e.patrol[0]:
            e.x = e.patrol[0]
            e.facing = 1
        if e.x + e.w > e.patrol[1]:
            e.x = e.patrol[1] - e.w
            e.facing = -1
        if e.y > game.level.height + 80:
            e.alive = False
            continue
        if not overlaps(player, e):
            continue
        if player.star > 0:
            behavior.on_hit(game, 2)
            continue
        stomp = player.vy > 0 and player.y + player.h <= e.y + min(24, player.vy * dt + 15)
        if stomp and e.stompable:
            player.vy = -390
            player.y = e.y - player.h - 1
            player.grounded = False
            player.standing_on = None
            behavior.on_hit(game, 1)
        else:
            behavior.on_touch(game)
