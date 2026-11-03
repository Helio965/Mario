"""Os Cinco Guardiões: invariantes de justiça, fases e robô de justiça (docs/research/CHEFES.md §6–§7)."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Any

import pytest

from game.bosses.boss import MIN_TELEGRAPH_BY_WORLD, Attack, BossDefinition
from game.bosses.guardians import BRUMO, FORNALHO, GUARDIANS, LUMIA, OCULUS, ROLAO
from game.characters.abilities import grant_power
from game.core.game import Game
from game.core.types import InputState
from game.enemies.state_machine import EnemyStateName as S
from tests.unit.helpers import STEP, level

FLOOR = 448.0
ARENA_LEFT, ARENA_RIGHT = 400.0, 1300.0


def arena_for(definition: BossDefinition, player_x: float = 200.0) -> Game:
    w, h = definition.size
    y = FLOOR - h - (4 if definition.floats else 0)
    if definition.kind == "lumia":
        y = FLOOR - 96 - h  # poleiro: copa a 96 px
    lvl = level(
        width=1700,
        spawn={"x": player_x, "y": FLOOR - 30},
        checkpoint={"x": 100, "y": FLOOR - 30},
        exit={"x": 1600, "y": FLOOR},
        platforms=[{"id": "floor", "kind": "ground", "x": 0, "y": FLOOR, "w": 1700, "h": 152}],
        enemies=[
            {
                "id": definition.kind,
                "kind": definition.kind,
                "x": 900,
                "y": y,
                "w": w,
                "h": h,
                "patrol": [ARENA_LEFT, ARENA_RIGHT],
            }
        ],
    )
    g = Game([lvl])
    g.player.invulnerable = 0
    return g


def attacks_by_name(definition: BossDefinition) -> dict[str, Attack]:
    out: dict[str, Attack] = {}
    for phase in definition.phases:
        for attack in phase.attacks:
            out[attack.name] = attack
        if phase.retaliation is not None:
            out[phase.retaliation.name] = phase.retaliation
    out["dizzy"] = Attack("dizzy", 0, 0, 1, counter="stay")
    return out


@dataclass
class FairnessBot:
    """Agente que reage ao aviso (``boss_telegraph``) após ``reaction`` s com a contramedida documentada.

    Só usa informação observável por um jogador: os avisos, a posição e a velocidade
    de corpos e projéteis, e a própria posição no instante do aviso (alvo congelado).
    Mantém "zonas de perigo" (onde um arremesso vai cair, o trecho baixo de um mergulho,
    o raio da retaliação, o corpo do chefe) e salta sobre perigos rasteiros pelo tempo
    até o contato; o pisão só entra na coluna do chefe por cima, depois do ápice do salto.
    """

    game: Game
    definition: BossDefinition
    reaction: float = 0.25
    seed: int = 0
    time: float = 0.0
    cursor: int = 0
    jump_hold: float = 0.0
    jump_request: float = 0.0
    prev_jump: bool = False
    need_release: bool = False
    engaging: bool = False
    engage_side: int = 1
    telegraphs: int = 0
    attack_starts: int = 0
    violations: list[str] = field(default_factory=list)
    last_telegraph_time: float = -1.0
    last_telegraph_name: str = ""
    frozen_x: float = 0.0  # centro do robô no instante do último aviso (alvo congelado observável)

    def __post_init__(self) -> None:
        self.rng = random.Random(self.seed)
        self.reaction += self.rng.uniform(0.0, 0.05)
        table = attacks_by_name(self.definition)
        self.counters = {name: a.counter for name, a in table.items()}
        self.telegraphs_by_name = {name: a.telegraph for name, a in table.items()}

    @property
    def boss(self) -> Any:
        return next(e for e in self.game.enemies if e.kind == self.definition.kind)

    # ------------------------------------------------------------ percepção
    def observe_events(self) -> None:
        p = self.game.player
        for ev in self.game.events[self.cursor :]:
            if ev.type == "boss_telegraph" and ev.text:
                self.telegraphs += 1
                self.last_telegraph_time = self.time
                self.last_telegraph_name = ev.text
                self.frozen_x = p.x + p.w / 2
        self.cursor = len(self.game.events)

    def request_jump(self, hold: float) -> None:
        """Pede um salto; só é executado com os pés no chão (nunca um pulinho de buffer)."""
        self.jump_request = max(self.jump_request, hold)

    def _landing_x(self, s: Any) -> float:
        drop = max(0.0, FLOOR - (s.y + s.h))
        if s.gravity > 0:
            t = (-s.vy + math.sqrt(s.vy * s.vy + 2 * s.gravity * drop)) / s.gravity
        else:
            t = drop / s.vy if s.vy > 0 else 0.0
        return s.x + s.w / 2 + s.vx * t

    def _dive_zone(self, diver: Any, target_x: float, target_y: float) -> tuple[float, float]:
        """Trecho da trajetória reta em que o corpo mergulhador fica à altura de quem está em pé."""
        p = self.game.player
        x0, y0 = diver.x + diver.w / 2, diver.y
        yt = target_y + 30 - diver.h
        head = FLOOR - p.h - 20
        fraction = 0.0 if yt <= y0 + 1 else max(0.0, min(1.0, (head - (y0 + diver.h)) / (yt - y0)))
        x_low = x0 + (target_x - x0) * fraction
        lo, hi = sorted((x_low, target_x))
        margin = diver.w / 2 + p.w / 2 + 30
        return (lo - margin, hi + margin)

    def zones(self) -> list[tuple[float, float]]:
        g, p, e = self.game, self.game.player, self.boss
        b = e.behavior
        out: list[tuple[float, float]] = []
        center = e.x + e.w / 2
        reacted = self.time >= self.last_telegraph_time + self.reaction
        if not self.engaging and not b.harmless:
            out.append((e.x - p.w / 2 - 26, e.x + e.w + p.w / 2 + 26))
        if (
            b.state == S.HURT
            or b.state == S.STUNNED
            or (b.retaliating and b.state in (S.PREPARE_ATTACK, S.ATTACK))
        ):
            out.append((center - 110, center + 110))
        attack = b.current_attack
        if attack is not None and b.state in (S.PREPARE_ATTACK, S.ATTACK) and reacted:
            if attack.animation == "dive":
                out.append(self._dive_zone(e, b.target_x, b.target_y))
            elif self.counters.get(attack.name) == "move_away":
                out.append((self.frozen_x - 130, self.frozen_x + 130))
        for s in g.projectiles:
            if s.alive and s.hostile and (s.gravity > 0 or s.vy > 50):
                landing = self._landing_x(s)
                margin = s.w / 2 + p.w / 2 + 34
                out.append((landing - margin, landing + margin))
        for x in g.enemies:
            if not x.alive or x is e or x.behavior is None:
                continue
            target = getattr(x.behavior, "target", None)
            if target is not None and x.behavior.state in (S.PREPARE_ATTACK, S.DIVE):
                out.append(self._dive_zone(x, target[0], target[1]))
        for x in g.enemies:
            if x.alive and x.kind == "shell" and x is not e and x.state == "walk":
                out.append((x.x - p.w / 2 - 12, x.x + x.w + p.w / 2 + 12))
        return out

    def low_threats(self) -> list[tuple[float, Any]]:
        """Perigos rasteiros que se aproximam horizontalmente: (tempo até o contato, corpo)."""
        p = self.game.player
        pc = p.x + p.w / 2
        bodies: list[Any] = [
            s
            for s in self.game.projectiles
            if s.alive and s.hostile and s.gravity == 0 and abs(s.vy) < 50
        ]
        bodies += [
            x for x in self.game.enemies if x.alive and x.kind == "shell" and x.state == "slide"
        ]
        out: list[tuple[float, Any]] = []
        for s in bodies:
            dx = s.x + s.w / 2 - pc
            toward = -1 if dx > 0 else 1  # sentido em que o perigo precisa ir para me atingir
            if s.vx * toward <= 0:
                continue
            if s.y + s.h <= p.y + 4:
                continue  # passa acima da cabeça de quem está em pé: não saltar
            closing = abs(s.vx) - p.vx * toward
            if closing <= 0:
                continue
            gap = abs(dx) - s.w / 2 - p.w / 2
            out.append((max(0.0, gap) / closing, s))
        return sorted(out, key=lambda item: item[0])

    def high_threat_near(self) -> bool:
        """Dardo alto a caminho: saltar agora seria entrar nele."""
        p = self.game.player
        pc = p.x + p.w / 2
        for s in self.game.projectiles:
            if (
                not (s.alive and s.hostile)
                or s.gravity > 0
                or s.y + s.h > p.y + 4
                or s.y + s.h < p.y - 60
            ):
                continue
            dx = s.x + s.w / 2 - pc
            overhead = abs(dx) < s.w / 2 + p.w / 2 + 8
            if overhead or ((dx > 0 > s.vx or dx < 0 < s.vx) and abs(dx) < 300):
                return True
        return False

    def window_remaining(self) -> float:
        b = self.boss.behavior
        if b.state == S.RECOVER and b.current_attack is not None:
            remaining = b.current_attack.recover - b.bb.time_in_state
            if S.IDLE in self.definition.vulnerable_states:
                remaining += b.phase.idle_time
            return remaining
        if b.state == S.IDLE and S.IDLE in self.definition.vulnerable_states:
            return b.phase.idle_time - b.bb.time_in_state
        return 0.0

    # --------------------------------------------------------------- decisão
    def update(self) -> InputState:
        g, p, e = self.game, self.game.player, self.boss
        self.time += STEP
        self.observe_events()
        b = e.behavior
        if b.state == S.ATTACK and b.bb.time_in_state < STEP * 0.5:
            self.attack_starts += 1
            declared = self.telegraphs_by_name.get(self.last_telegraph_name, 0.0)
            elapsed = self.time - self.last_telegraph_time
            if self.last_telegraph_time < 0 or elapsed + 1e-6 < declared:
                self.violations.append(
                    f"{self.last_telegraph_name} atacou após {elapsed:.2f} s (< {declared:.2f})"
                )
        inp = InputState()
        center = e.x + e.w / 2
        pc = p.x + p.w / 2
        away = -1 if pc < center else 1
        reacted = self.time >= self.last_telegraph_time + self.reaction
        attack = b.current_attack
        counter = (
            self.counters.get(attack.name)
            if attack is not None and reacted and b.state in (S.PREPARE_ATTACK, S.ATTACK)
            else None
        )
        threats = self.low_threats()
        nearest = threats[0][0] if threats else math.inf
        jump_locked = self.high_threat_near()
        if p.grounded and (self.jump_hold <= 0 or not self.engaging):
            self.engaging = False
        shells = [x for x in g.enemies if x.alive and x.kind == "shell" and x is not e]
        needs_shell = "shell" in b.phase.always_vulnerable_to and not e.stompable
        zones = self.zones()
        if b.state == S.HIDDEN and abs(pc - center) > 400:
            self._move(inp, -away)  # entra na arena para começar o combate
        elif counter == "run_away":
            self._move(inp, away)  # investida: é mais rápido correr do que o chefe
            inp.run = True
        elif needs_shell and shells and nearest > 1.0:
            self._use_shell(inp, shells[0], center)
        elif counter == "jump_wave" and not threats:
            self._move(inp, away)  # abrir espaço antes de a onda aparecer
        elif self.engaging or self._can_engage(zones, nearest, jump_locked):
            self._stomp(inp)
        elif not b.harmless:
            standoff = center + away * (e.w / 2 + 70)
            if abs(pc - standoff) > 12:
                self._steer(inp, standoff)
        if not self.engaging:
            self._enforce_zones(inp, zones, pc)
        if threats and nearest < 1.0 and p.grounded and not self._inside(zones, pc):
            inp.left = inp.right = False  # salto parado, cronometrado pelo perigo
        for ttc, _ in threats:
            if ttc <= 0.27 and not jump_locked:
                self.request_jump(0.45)
                break
        if self.jump_request > 0 and p.grounded and self.jump_hold <= 0:
            self.jump_hold = self.jump_request
            self.jump_request = 0.0
            self.need_release = self.prev_jump
        if self.need_release:
            inp.jump = False
            self.need_release = False
        else:
            inp.jump = self.jump_hold > 0
        self.prev_jump = inp.jump
        self.jump_hold = max(0.0, self.jump_hold - STEP)
        return inp

    def _inside(self, zones: list[tuple[float, float]], x: float) -> bool:
        return any(lo < x < hi for lo, hi in zones)

    def _hold_x(self, side: int) -> float:
        p, e = self.game.player, self.boss
        return e.x + e.w / 2 + side * (e.w / 2 + p.w / 2 + 12)

    def _can_engage(
        self, zones: list[tuple[float, float]], nearest: float, jump_locked: bool
    ) -> bool:
        p, e = self.game.player, self.boss
        b = e.behavior
        if (
            not (b.vulnerable and e.stompable)
            or b.retaliating
            or b.state not in (S.RECOVER, S.IDLE)
        ):
            return False
        if not p.grounded or jump_locked or nearest < 1.2:
            return False
        pc = p.x + p.w / 2
        side = -1 if pc < e.x + e.w / 2 else 1
        hold_x = self._hold_x(side)
        body = (e.x - p.w / 2 - 26, e.x + e.w + p.w / 2 + 26)
        if any(lo < hold_x < hi for lo, hi in zones if (lo, hi) != body):
            return False
        travel = abs(pc - hold_x) / 220 + 0.15
        if self.window_remaining() < 0.62 + travel:
            return False
        self.engaging = True
        self.engage_side = side
        return True

    def _stomp(self, inp: InputState) -> None:
        """Pisão: espera no ponto de salto ao lado do chefe, salta reto e só entra na coluna dele descendo."""
        p, e = self.game.player, self.boss
        b = e.behavior
        pc = p.x + p.w / 2
        center = e.x + e.w / 2
        if p.grounded:
            self.engage_side = -1 if pc < center else 1
            hold_x = self._hold_x(self.engage_side)
            if abs(pc - hold_x) <= 6 and abs(p.vx) <= 45:
                self.request_jump(0.75)
            else:
                self._steer(inp, hold_x)
                inp.run = abs(pc - hold_x) > 120
            return
        hold_x = self._hold_x(self.engage_side)
        if b.state in (S.HURT, S.STUNNED, S.DEFEATED) or b.retaliating or not b.vulnerable:
            self._steer(
                inp, center + self.engage_side * (e.w / 2 + 130)
            )  # golpe dado (ou janela fechada): afastar-se
        elif p.y + p.h <= e.y - 2 and p.vy >= 0:
            self._steer(inp, center)  # acima do topo e já descendo: entrar na coluna do chefe
        else:
            self._steer(inp, hold_x)

    def _enforce_zones(self, inp: InputState, zones: list[tuple[float, float]], pc: float) -> None:
        inside = [z for z in zones if z[0] < pc < z[1]]
        if inside:
            lo = min(z[0] for z in inside)
            hi = max(z[1] for z in inside)
            changed = True
            while changed:
                changed = False
                for z in zones:
                    if z[1] > lo and z[0] < hi and (z[0] < lo or z[1] > hi):
                        lo, hi = min(lo, z[0]), max(hi, z[1])
                        changed = True
            direction = -1 if pc - lo <= hi - pc else 1
            if lo < ARENA_LEFT - 280:
                direction = 1
            if hi > ARENA_RIGHT + 280:
                direction = -1
            inp.left = inp.right = False
            self._move(inp, direction)
            inp.run = True
            return
        direction = 1 if inp.right else -1 if inp.left else 0
        if direction and self._inside(zones, pc + direction * 24):
            inp.left = inp.right = False

    def _use_shell(self, inp: InputState, shell: Any, boss_center: float) -> None:
        """Contramedida 'casco': espera o casco vir até si, pisa-o ao descer e o chuta rumo ao chefe."""
        p, boss = self.game.player, self.boss
        pc = p.x + p.w / 2
        sc = shell.x + shell.w / 2
        far_side = 1 if pc > boss_center else -1
        if shell.state == "walk":
            if not p.grounded:
                if p.vy >= 0:
                    self._steer(inp, sc + shell.vx * 0.15)  # descendo: cair sobre o casco
                return
            near_boss = abs(sc - boss_center) < boss.w / 2 + 100
            toward_me = (sc - pc) * shell.vx < 0
            if near_boss or not toward_me:
                # esperar longe do chefe, no caminho do casco (ele patrulha entre as bordas)
                self._steer(inp, boss_center + far_side * (boss.w / 2 + 190))
                return
            inp.left = inp.right = False  # ficar parado no caminho dele
            if abs(sc - pc) <= 60 and abs(p.vx) <= 45:
                # ≈1 s a 62 px/s: o casco só chega debaixo de mim depois do ápice (pisão ao descer)
                self.request_jump(0.75)
        elif shell.state == "shell":
            self._steer(inp, sc)  # encostar chuta o casco para o lado oposto ao meu
            inp.run = abs(pc - sc) > 120
        else:
            self._move(inp, -1 if sc > pc else 1)

    def _move(self, inp: InputState, direction: int) -> None:
        p = self.game.player
        if direction < 0 and p.x > ARENA_LEFT - 300:
            inp.left, inp.right = True, False
        elif direction > 0 and p.x + p.w < ARENA_RIGHT + 300:
            inp.right, inp.left = True, False

    def _steer(self, inp: InputState, target_x: float) -> None:
        p = self.game.player
        projected = p.x + p.w / 2 + p.vx * 0.08
        inp.left = projected > target_x + 5
        inp.right = projected < target_x - 5


def fight(
    definition: BossDefinition, reaction: float = 0.25, seed: int = 0, max_seconds: float = 150.0
) -> tuple[Game, FairnessBot]:
    g = arena_for(definition)
    grant_power(g, "fire")
    bot = FairnessBot(g, definition, reaction, seed)
    boss = bot.boss
    for _ in range(int(max_seconds * 120)):
        g.update(STEP, bot.update())
        behavior = boss.behavior
        if behavior.state not in (S.HIDDEN, S.DEFEATED):
            assert behavior.active_hazards(g) <= behavior.phase.max_hazards, (
                "orçamento de perigos excedido"
            )
        if not boss.alive or g.status != "playing":
            break
    return g, bot


@pytest.mark.parametrize("definition", GUARDIANS, ids=[g.kind for g in GUARDIANS])
def test_definition_respects_fairness_invariants_and_world_floors(
    definition: BossDefinition,
) -> None:
    assert definition.validate() == []
    assert len(definition.phases) == 3
    floor = MIN_TELEGRAPH_BY_WORLD[definition.world]
    for index, phase in enumerate(definition.phases):
        expected = floor if index < 2 else max(0.4, floor * 0.85)
        for attack in phase.attacks:
            assert attack.telegraph >= expected - 1e-9, (definition.kind, phase.name, attack.name)
    verbs = [tuple(a.name for a in p.attacks) for p in definition.phases]
    assert len(set(verbs)) == 3


def test_hit_counts_follow_research() -> None:
    assert [g.hp for g in GUARDIANS] == [3, 3, 3, 4, 5]
    assert [g.world for g in GUARDIANS] == [1, 2, 3, 4, 5]
    assert LUMIA.floats and OCULUS.floats and not ROLAO.floats
    assert BRUMO.phases[2].vulnerable_sources == frozenset({"shell"})
    assert FORNALHO.phases[0].max_hazards == 1


@pytest.mark.parametrize("definition", GUARDIANS, ids=[g.kind for g in GUARDIANS])
@pytest.mark.parametrize("seed", [0, 1, 2])
def test_fairness_bot_wins_without_losing_health(definition: BossDefinition, seed: int) -> None:
    g, bot = fight(definition, reaction=0.25, seed=seed)
    boss = bot.boss
    assert bot.violations == [], bot.violations[:3]
    assert not boss.alive or boss.behavior.state == S.DEFEATED, (
        f"{definition.kind}: não derrotado em 150 s (fase {boss.behavior.phase_index + 1}, vida {boss.health})"
    )
    assert g.lives == 5
    assert g.player.power == "fire", f"{definition.kind}: o robô levou dano"
    assert bot.telegraphs >= bot.attack_starts > 0


@pytest.mark.parametrize("definition", GUARDIANS, ids=[g.kind for g in GUARDIANS])
def test_slow_bot_still_wins_with_at_most_two_hits(definition: BossDefinition) -> None:
    g, bot = fight(definition, reaction=0.4, seed=7)
    boss = bot.boss
    assert not boss.alive or boss.behavior.state == S.DEFEATED
    assert g.lives == 5, "duas falhas custam poder, nunca a vida"
