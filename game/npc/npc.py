"""NPCs: rotinas declarativas, observação do jogador e início de diálogos.

Um NPC executa uma rotina (andar até x, esperar, olhar, expressar, dizer uma
fala curta) em loop; quando o jogador se aproxima, para e o observa; quando o
jogador interage (↓ sobre o NPC), o jogo congela o mundo e emite o evento
``talk`` com o id do diálogo — a interface executa o ``DialogueRunner`` e
chama ``Game.end_talk()`` ao terminar. Python puro, sem pygame.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from game.core.types import GameEvent, Npc, Rect
from game.physics.collision import move_body, overlaps
from game.physics.movement import GRAVITY

if TYPE_CHECKING:
    from game.core.game import Game

ARRIVAL_TOLERANCE = 2.0
BUBBLE_SECONDS = 2.5
INTERACT_MARGIN = 14.0


def interaction_zone(npc: Npc) -> Rect:
    return Rect(npc.x - INTERACT_MARGIN, npc.y - 8, npc.w + 2 * INTERACT_MARGIN, npc.h + 8)


def update_npcs(game: Game, dt: float) -> None:
    player = game.player
    for npc in game.npcs:
        npc.bubble_time = max(0.0, npc.bubble_time - dt)
        if npc.bubble_time <= 0:
            npc.bubble = None
        if npc.state == "talk":
            npc.vx = 0
            _face_player(npc, player)
            npc.anim = "talk"
        else:
            dx = (player.x + player.w / 2) - (npc.x + npc.w / 2)
            dy = (player.y + player.h / 2) - (npc.y + npc.h / 2)
            near = abs(dx) <= npc.observe_distance and abs(dy) <= 60
            if near and npc.state != "done":
                npc.state = "observe"
                npc.vx = 0
                _face_player(npc, player)
                npc.expression = "attentive"
                npc.anim = "idle"
            else:
                if npc.state == "observe":
                    npc.state = "routine"
                    npc.expression = "neutral"
                if npc.state == "routine":
                    _run_routine(game, npc, dt)
                else:  # done: rotina terminada sem loop
                    npc.vx = 0
                    npc.anim = "idle"
        npc.vy = min(850, npc.vy + GRAVITY * dt)
        hit = move_body(npc, [s for s in game.platforms if s.kind != "hidden" or s.used], dt)
        npc.grounded = hit.grounded


def _face_player(npc: Npc, player: object) -> None:
    px = player.x + player.w / 2  # type: ignore[attr-defined]
    npc.facing = 1 if px >= npc.x + npc.w / 2 else -1


def _run_routine(game: Game, npc: Npc, dt: float) -> None:
    if not npc.routine:
        npc.vx = 0
        npc.anim = "idle"
        return
    step = npc.routine[npc.step_index]
    npc.step_clock += dt
    advance = False
    if step.action == "walk":
        target = step.x
        center = npc.x
        if abs(target - center) <= ARRIVAL_TOLERANCE:
            npc.x = target
            npc.vx = 0
            advance = True
        else:
            npc.facing = 1 if target > center else -1
            npc.vx = npc.facing * step.speed
            npc.anim = "walk"
    elif step.action == "wait":
        npc.vx = 0
        npc.anim = "idle"
        advance = npc.step_clock >= step.seconds
    elif step.action == "look":
        npc.vx = 0
        npc.facing = step.facing
        advance = True
    elif step.action == "emote":
        npc.vx = 0
        npc.expression = step.expression
        npc.anim = "emote"
        advance = npc.step_clock >= step.seconds
        if advance:
            npc.expression = "neutral"
    elif step.action == "say":
        npc.vx = 0
        npc.bubble = step.reaction
        npc.bubble_time = BUBBLE_SECONDS
        game.events.append(GameEvent("npc_say", text=f"{npc.reactions or npc.id}:{step.reaction}"))
        advance = True
    else:
        advance = True
    if advance:
        npc.step_clock = 0.0
        npc.step_index += 1
        if npc.step_index >= len(npc.routine):
            npc.step_index = 0
            if not npc.loop:
                npc.state = "done"


def try_interact(game: Game) -> bool:
    """↓ sobre um NPC com diálogo: congela o mundo e emite ``talk``. Devolve True se iniciou."""
    player = game.player
    for npc in game.npcs:
        if npc.dialogue is None or (npc.talk_once and npc.talked) or npc.state == "talk":
            continue
        if overlaps(player, interaction_zone(npc)):
            npc.state = "talk"
            npc.talked = True
            game.talking_npc = npc
            game.talking = True
            game.events.append(GameEvent("talk", text=npc.dialogue))
            return True
    return False
