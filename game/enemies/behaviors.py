"""Arquétipos modernos de inimigos: base compartilhada + passo comum.

Cada arquétipo (``game/enemies/archetypes/``) declara só os estados
relevantes, suas flags (``ArchetypeFlags``) e os parâmetros nomeados dos
perfis (``game/enemies/profiles.py``). O passo comum (``update_modern``)
cuida de percepção, física, bordas/paredes, limites de patrulha, contato
entre inimigos e com o jogador (pisão, pisão-salto, espinhos, estrela) e
roteia o dano por fonte, mantendo os inimigos legados intocados.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from game.core.interactions import burst
from game.core.types import Enemy, GameEvent, Projectile
from game.enemies.perception import Perception, PerceptionProfile, edge_ahead, wall_ahead
from game.enemies.profiles import FLAGS_DEFAULT, WALKER, ArchetypeFlags
from game.enemies.state_machine import Blackboard, EnemyStateName, State, StateMachine, Transition
from game.physics.collision import move_body, overlaps
from game.physics.movement import GRAVITY

if TYPE_CHECKING:
    from game.core.game import Game

S = EnemyStateName
VIEW_WIDTH = 960
DamageSource = str  # "stomp" | "fire" | "shell" | "star" | "explosion" | "block" | "boss"


@dataclass(slots=True)
class ArchetypeParams:
    """Parâmetros do arquétipo simples ``stalker`` (mantido como referência/teste)."""

    patrol_speed: float = 55.0
    chase_speed: float = 150.0
    alert_time: float = 0.35
    chase_max: float = 2.5
    recover_time: float = 0.6
    hurt_time: float = 0.65
    hp: int = 1
    stompable: bool = True
    turns_at_edges: bool = True
    perception: PerceptionProfile = field(default_factory=PerceptionProfile)


class Behavior:
    """Base: FSM, percepção e quadro-negro; subclasses definem estados, movimento e reações."""

    kind = "base"
    is_boss = False
    flags: ArchetypeFlags = FLAGS_DEFAULT
    params = ArchetypeParams()
    uses_gravity = True  # inimigos voadores/flutuantes desligam
    collides_with_platforms = True
    clamps_patrol = True
    dies_below_level = True
    score = 200

    def __init__(self, enemy: Enemy) -> None:
        self.enemy = enemy
        self.bb = Blackboard(health=enemy.health, max_health=enemy.health)
        self.perception = Perception(self.params.perception)
        self.fsm = StateMachine(self.states(), self.initial())
        self.squash_clock = 0.0
        enemy.stompable = self.flags.stompable
        enemy.anim = self.fsm.current.animation

    # ------------------------------------------------------- a definir
    def states(self) -> dict[EnemyStateName, State]:
        raise NotImplementedError

    def initial(self) -> EnemyStateName:
        return S.PATROL

    def move(self, game: Game, dt: float) -> None:
        """Define ``enemy.vx``/``vy``/``facing`` conforme o estado atual."""
        raise NotImplementedError

    # ------------------------------------------------------------ fatos
    @property
    def state(self) -> EnemyStateName:
        return self.fsm.name

    @property
    def harmless(self) -> bool:
        """Sem contato com o jogador (achatado, pilha de ossos, derrotado)."""
        return self.state == S.DEFEATED

    def observe(self, game: Game, dt: float) -> None:
        e, bb = self.enemy, self.bb
        player = game.player
        facts = self.perception.observe(dt, e, player, e.facing, game.platforms)
        for key, value in facts.items():
            setattr(bb, key, value)
        bb.grounded = e.grounded
        bb.edge_ahead = e.grounded and edge_ahead(e, e.facing, game.platforms)
        bb.wall_ahead = wall_ahead(e, e.facing, game.platforms)
        bb.health = e.health
        bb.hurt = e.hit_timer > 0
        bb.player_speed = abs(player.vx)
        bb.player_grounded = player.grounded
        bb.player_star = player.star > 0
        bb.player_below = bb.player_dy > e.h / 2
        # O jogador "olha" para mim se o sinal de (eu − jogador) coincide com o rosto dele.
        bb.player_looking_at_me = (-bb.player_dx) * player.facing > 0
        bb.on_screen = e.x + e.w >= game.camera.x - 60 and e.x <= game.camera.x + VIEW_WIDTH + 60

    def step(self, game: Game, dt: float) -> None:
        self.observe(game, dt)
        self.fsm.update(dt, self.bb)
        self.enemy.anim = self.fsm.current.animation
        self.enemy.telegraph = self.fsm.current.telegraph
        self.enemy.stompable = self.flags.stompable and self.state != S.DEFEATED
        self.move(game, dt)
        self.bb.just_landed = False
        self.bb.hit_enemy = False
        self.bb.hit_wall = False

    # --------------------------------------------------------------- dano
    def accepts(self, source: DamageSource) -> bool:
        f = self.flags
        if source == "fire" and f.fireproof:
            return False
        if source == "star" and not f.star_kills:
            return False
        if source == "shell" and not f.shell_kills:
            return False
        return not (source == "explosion" and not f.explosion_kills)

    def on_hit(self, game: Game, damage: int, source: DamageSource = "stomp") -> bool:
        """Dano recebido por ``source``. Devolve True se aplicou."""
        e = self.enemy
        if not e.alive or e.hit_timer > 0 or self.state == S.DEFEATED or not self.accepts(source):
            return False
        e.health -= damage
        e.hit_timer = self.params.hurt_time
        burst(game, e.x + e.w / 2, e.y, "#ffdc87")
        if e.health <= 0:
            self.defeat(game, pop=source != "stomp")
        else:
            game.events.append(GameEvent("stomp"))
            if S.HURT in self.fsm.states:
                self.fsm.force(S.HURT, self.bb)
        return True

    def on_stomp(self, game: Game) -> bool:
        """Pisão do jogador (já validado pelo passo comum). Devolve True se houve rebote."""
        return self.on_hit(game, 1, "stomp") or True

    def on_touch(self, game: Game) -> None:
        """Contato lateral/inferior com o jogador."""
        if not self.harmless:
            game.hurt()

    def on_landed(self, game: Game) -> None:
        if self.flags.face_player_on_land:
            self.face_player()

    def defeat(self, game: Game, pop: bool = False, score: int | None = None) -> None:
        """Derrota: achatado (pisão) ou lançado para fora (fogo/casco/estrela/explosão)."""
        e = self.enemy
        game.score += self.score if score is None else score
        game.events.append(GameEvent("stomp"))
        if S.DEFEATED in self.fsm.states:
            self.fsm.force(S.DEFEATED, self.bb)
        e.health = 0
        e.stompable = False
        e.telegraph = False
        self.squash_clock = 0.0
        if pop:
            e.vy = WALKER.knockback_vy
            e.vx = WALKER.knockback_vx * (1 if game.player.x < e.x else -1)
            self.collides_with_platforms = False
            self.clamps_patrol = False
        else:
            e.vx = 0

    def tick_defeated(self, game: Game, dt: float, squash_time: float = WALKER.squash_time) -> None:
        """Achatado some após ``squash_time``; lançado some ao sair da fase."""
        self.squash_clock += dt
        e = self.enemy
        if self.collides_with_platforms and self.squash_clock >= squash_time:
            e.alive = False
        if e.y > game.level.height + 80:
            e.alive = False

    # ---------------------------------------------------------- auxiliares
    def face_player(self) -> None:
        if self.bb.player_dx != 0:
            self.enemy.facing = 1 if self.bb.player_dx > 0 else -1

    def shoot(
        self,
        game: Game,
        vx: float,
        vy: float,
        w: float = 12,
        h: float = 12,
        life: float = 3.5,
        gravity: float = 0.0,
        y_offset: float = 8,
    ) -> Projectile:
        e = self.enemy
        projectile = Projectile(
            x=e.x + e.w / 2 - w / 2,
            y=e.y + y_offset,
            w=w,
            h=h,
            vx=vx,
            vy=vy,
            hostile=True,
            life=life,
            alive=True,
            gravity=gravity,
        )
        game.projectiles.append(projectile)
        game.events.append(GameEvent("shot"))
        return projectile

    def spawn_enemy(
        self,
        game: Game,
        kind: str,
        x: float,
        y: float,
        w: float,
        h: float,
        patrol: tuple[float, float] | None = None,
        hp: int = 1,
    ) -> Enemy:
        child = Enemy(
            id=f"{self.enemy.id}-{kind}-{len(game.enemies)}",
            kind=kind,
            x=x,
            y=y,
            w=w,
            h=h,
            patrol=list(patrol) if patrol else [0.0, game.level.width],
            hp=hp,
            vx=0,
            vy=0,
            alive=True,
            health=hp,
            facing=self.enemy.facing,
            timer=0,
            hit_timer=0,
            state="walk",
            origin_y=y,
            grounded=False,
        )
        child.behavior = create_behavior(child)
        game.enemies.append(child)
        return child


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
            self.face_player()
        elif state == S.CHASE:
            self.face_player()
            e.vx = (
                0
                if (p.turns_at_edges and (bb.edge_ahead or bb.wall_ahead))
                else e.facing * p.chase_speed
            )
        elif state == S.DEFEATED:
            self.tick_defeated(game, dt)
        else:
            e.vx = 0


ARCHETYPES: dict[str, type[Behavior]] = {StalkerBehavior.kind: StalkerBehavior}


def register(cls: type[Behavior]) -> type[Behavior]:
    ARCHETYPES[cls.kind] = cls
    return cls


def create_behavior(enemy: Enemy) -> Behavior | None:
    cls = ARCHETYPES.get(enemy.kind)
    return cls(enemy) if cls is not None else None


def _stomp_window(player: Any, e: Enemy, dt: float) -> bool:
    return bool(player.vy > 0 and player.y + player.h <= e.y + min(24, player.vy * dt + 15))


def update_modern(game: Game, dt: float) -> None:
    """Passo dos inimigos com arquétipo moderno (chamado após o passo legado)."""
    player = game.player
    solids = [s for s in game.platforms if s.kind != "hidden" or s.used]
    for e in list(game.enemies):
        behavior: Any = e.behavior
        if not e.alive or behavior is None:
            continue
        e.timer += dt
        e.hit_timer = max(0, e.hit_timer - dt)
        was_grounded = e.grounded
        behavior.step(game, dt)
        if behavior.uses_gravity:
            e.vy = min(850, e.vy + GRAVITY * dt)
        before = e.vx
        if behavior.collides_with_platforms:
            hit = move_body(e, solids, dt)
            e.grounded = hit.grounded
            if before != 0 and e.vx == 0:
                behavior.bb.hit_wall = True
        else:
            e.x += e.vx * dt
            e.y += e.vy * dt
            e.grounded = False
        if e.grounded and not was_grounded:
            behavior.bb.just_landed = True
            behavior.on_landed(game)
        if behavior.clamps_patrol:
            if e.x < e.patrol[0]:
                e.x = e.patrol[0]
                e.facing = 1
            if e.x + e.w > e.patrol[1]:
                e.x = e.patrol[1] - e.w
                e.facing = -1
        if behavior.dies_below_level and e.y > game.level.height + 80:
            e.alive = False
            continue
        if not e.alive or behavior.harmless:
            continue
        if behavior.flags.turn_on_enemy_contact:
            for other in game.enemies:
                if (
                    other is e
                    or not other.alive
                    or other.behavior is None
                    or other.behavior.harmless
                ):
                    continue
                if not other.behavior.flags.turn_on_enemy_contact or not overlaps(e, other):
                    continue
                if (e.x < other.x) == (e.facing > 0):  # só quem anda em direção ao outro inverte
                    e.facing *= -1
                    behavior.bb.hit_enemy = True
        if not overlaps(player, e):
            continue
        if player.star > 0 and behavior.flags.star_kills:
            behavior.on_hit(game, 2, "star")
            continue
        if _stomp_window(player, e, dt) and (
            behavior.flags.stompable or behavior.flags.stomp_hurts or behavior.flags.blocks_player
        ):
            if behavior.flags.stomp_hurts:
                game.hurt()
                continue
            if behavior.flags.blocks_player and not behavior.flags.stompable:
                player.y = e.y - player.h
                player.vy = 0
                player.grounded = True
                continue
            held = game.last_input.jump
            player.vy = WALKER.stomp_jump_bounce if held else WALKER.stomp_bounce
            player.y = e.y - player.h - 1
            player.grounded = False
            player.standing_on = None
            behavior.on_stomp(game)
        else:
            behavior.on_touch(game)


def sign(value: float) -> int:
    return 1 if value > 0 else -1 if value < 0 else 0


def distance(a: Any, b: Any) -> float:
    return math.hypot((a.x + a.w / 2) - (b.x + b.w / 2), (a.y + a.h / 2) - (b.y + b.h / 2))
