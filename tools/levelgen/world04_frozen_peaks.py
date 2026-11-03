"""Montanhas Geladas — new levels 4-4, 4-5 and 4-6 (authoring source).

Regenerates lume/data/levels/frozen_peaks/{slippery_slopes,avalanche_ridge,frost_citadel}.json.
Plans: docs/level_design/MUNDO_04.md.  The engine has no slopes, so the
"encostas" are descending ice terraces (12–16 u drops) — documented in the
level notes and in the expansion report.
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from kit import L, save, terraces, wind  # noqa: E402


def stairs_up(l, x, y, steps, step_w=64, rise=40, **kw):
    """Rock steps going up (normal friction).  Returns (end_x, top_y)."""
    for k in range(steps):
        l.ground(x + k * step_w, step_w, y - (k + 1) * rise, **kw)
    return x + steps * step_w, y - steps * rise


# ----------------------------------------------------------------------------- 4-4 Encostas Escorregadias
l = L(id="slippery_slopes", name="Encostas Escorregadias", world="frozen_peaks", role="special", difficulty=4,
      art={"set": "frozen_peaks", "variant": "slopes", "weather": "auto"}, music="frozen_peaks_main",
      bounds={"width": 5600, "height": 1240}, time_limit=360, spawn={"x": 72, "y": 338},
      exit={"id": "goal", "kind": "flag", "x": 5500, "y": 448})
l.d["areas"] = [{"id": "main", "x": 0, "y": 0, "w": 5600, "h": 540, "variant": "slopes"}]
# 1. introduction: a short ice descent that ends on rock (rock brakes, ice does not)
l.ground(0, 380, 368)
l.plat("question", 220, 250, 40, 28, reward="grow")
l.coins("row", 120, 330, 4)
l.hint(150, "No gelo inclinado não há freio: o chão de pedra no fim da descida segura Lume.")
x, y = terraces(l, 380, 384, 5, 64, 16)
l.coins("arc", 400, 330, 5, 50, 30)
l.ground(x, 360)                                   # rock plateau at 448 (700..1060)
l.enemy("pinguim_patrulha", 900, 448, 760, 1050)
# 2. safe demonstration: climb rock steps, descend a longer ice run into a soft snow wall
x, top = stairs_up(l, 1060, 448, 3, 64, 40)        # up to y 328 (1060..1252)
l.coins("column", 1210, 250, 3, 34)
x, y = terraces(l, x, 344, 7, 64, 16)              # 1252..1700, y 344..440
l.ground(1700, 300)                                # flat rock 1700..2000 (y 448)
l.ground(1700, 40, 384, id="snow_wall")            # soft wall (64 high): stops the slide, hop over it
l.hint(1240, "A parede de neve no fim da encosta segura você. Depois, salte por cima.")
# twin-pine high route: jump at the top of the ramp onto pine-top ledges
l.plat("ledge", 1290, 236, 90, 24, style="floating")
l.plat("ledge", 1440, 190, 90, 24, style="floating")
l.relic("relic_pine", 1478, 150)
l.coins("row", 1300, 200, 3, 26)
l.secret("twin_pine", "high_route", "Dois pinheiros iguais no topo da rampa; um tem fita vermelha", ["relic_pine"])
# 3. first challenge: the yeti cub on flat rock, with boulders as shelters
l.ground(2000, 560)                                # 2000..2560 flat (checkpoint zone)
l.plat("ledge", 1780, 400, 40, 48, style="floating", id="shelter_a")
l.enemy("yeti_mirim", 1880, 412, 1840, 1990)
l.hint(1760, "O Yeti-Mirim ergue a bola de neve antes de arremessar: espere atrás da pedra.")
l.d["checkpoints"].append({"id": "cp_slopes", "x": 2140, "y": 418})
l.d["events"].append({"id": "msg_guide", "kind": "message", "x": 2140,
                      "params": {"text": "Tio Nevasco: na encosta não tem freio. Escolha onde pular antes de descer."}})
l.coins("row", 2300, 410, 5)
l.plat("question", 2260, 330, 40, 28, reward="fire")   # power back after the yeti
# 4. escalation: ramps that end in gaps (take off from the last step); penguins slide uphill toward Lume
x, top = stairs_up(l, 2560, 448, 2, 64, 40)        # to 368 (2560..2688)
x, y = terraces(l, x, 384, 5, 64, 12, last_w=176)  # 2688..3120, y 384..432 (take-off step 176 u)
l.enemy("pinguim_patrulha", 2780, 408, 2700, 2860)
l.coins("arc", 3130, 380, 4, 30, 30)
l.ground(3248, 270)                                # after a 128 u gap: 3248..3518 (y 448)
l.enemy("caracol_cristal", 3460, 448, 3390, 3512)
l.hint(3150, "Chute o casco de cristal: no gelo ele vai longe e derruba quem estiver na frente.")
# 5. combination: yetis over an ice run, crystal snails to kick down the slope
x, top = stairs_up(l, 3518, 448, 2, 64, 40)        # to 368 (3518..3646)
x, y = terraces(l, x, 384, 6, 64, 12)              # 3646..4030, y 384..444
l.enemy("caracol_cristal", 3760, 396, 3660, 4020)
l.enemy("pinguim_patrulha", 3950, 444, 3800, 4020)
l.ground(4030, 270)                                # 4030..4300 rock (y 448)
l.enemy("yeti_mirim", 4200, 412, 4150, 4290)
l.coins("row", 3700, 330, 6, 48)
# 6. twist: the inverted slope — climb slippery ice ledges, jumping again before sliding off
for k, (lx, ly) in enumerate(((4330, 404), (4440, 364), (4550, 324), (4660, 284))):
    # the last ledge runs into the ridge, so sliding off its end carries Lume onto the top
    l.plat("ledge", lx, ly, 120 if k == 3 else 96, 24, style="ice_ledge", surface="ice")
    l.coins("row", lx + 30, ly - 30, 2, 30)
l.ground(4300, 520)                                # floor under the ledges (4300..4820) — falling only costs time
l.ground(4780, 140, 284, id="ridge_top")           # top of the inverted slope (4780..4920)
l.d["checkpoints"].append({"id": "cp_final", "x": 4800, "y": 254})
l.plat("question", 4840, 170, 40, 28, reward="heart")
# 7. final run: long descent with gaps, yeti and penguins, ending with a ramp jump
x, y = terraces(l, 4920, 300, 8, 44, 16, last_w=112)  # 4920..5340, y 300..412 (take-off step 112 u)
l.enemy("pinguim_patrulha", 5200, 400, 5000, 5300)
l.enemy("boneco_neve", 5060, 304, 5040, 5080)
l.coins("row", 4960, 250, 6, 48)
# slalom relic: high above the final descent (jump at the right moment)
l.relic("relic_slalom", 5150, 220)
l.secret("slalom", "optional_challenge", "Bandeiras de slalom com moedas entre elas", ["relic_slalom"])
# 8. reward: the chalet plateau after a ramp jump
l.ground(5460, 140)                                # gap 5340..5460 (120 u, landing 36 u lower)
# lost sled cave (pipe on the rock plateau of section 1)
l.cave_room(820, 1010, 5600, reward_item="star", relic_id="relic_sled", secret_id="lost_sled",
            secret_kind="hidden_area", clue="Trilhas de trenó entram num cano coberto de neve")
l.enemy("coruja_nevada", 2400, 320, 2300, 2520)
l.enemy("boneco_neve", 2480, 416, 2460, 2500)
l.enemy("caracol_cristal", 950, 448, 900, 1050)        # rock plateau of section 1 (kick practice)
l.enemy("pinguim_patrulha", 4180, 448, 4100, 4290)     # rock shelf before the inverted slope
l.enemy("coruja_nevada", 880, 300, 740, 1040)
l.d["notes"] = ("Fase nova (Mundo 4-4): mecânica especial — encostas de gelo como terraços descendentes "
                "(o motor não tem rampas), vãos no fim das rampas, escada de gelo invertida; estreia do Yeti-Mirim.")
save(l.d)
print("ok")


# ----------------------------------------------------------------------------- 4-5 Cume da Avalanche
def icicle(l, x, ceiling_bottom, rest=1.4, telegraph=0.45):
    """A falling icicle hanging under a ceiling whose bottom is at ``ceiling_bottom``."""
    l.enemy("pingente_queda", x, ceiling_bottom + 40, x - 4, x + 38, params={"rest": rest, "telegraph": telegraph})


def snowball(l, x, y, rng, speed=1.1, phase=0.0, size=56):
    """Giant snowball rolling back and forth (moving hazard, centre at x)."""
    l.hazard("moving", x - size / 2, y - size, size, size, range=rng, speed=speed, phase=phase, style="snowball")


l = L(id="avalanche_ridge", name="Cume da Avalanche", world="frozen_peaks", role="advanced", difficulty=5,
      art={"set": "frozen_peaks", "variant": "ridge", "weather": "auto"}, music="frozen_peaks_main",
      bounds={"width": 6000, "height": 1240}, time_limit=380, spawn={"x": 72, "y": 418},
      exit={"id": "goal", "kind": "flag", "x": 5850, "y": 448})
l.d["areas"] = [{"id": "main", "x": 0, "y": 0, "w": 6000, "h": 540, "variant": "ridge"}]
# 1. introduction: the falling icicle over a flat, safe stretch of the ridge trail
l.ground(0, 1300)
l.plat("question", 260, 330, 40, 28, reward="grow")
l.ground(520, 220, 0, 200, id="overhang_a")        # rock overhang (ceiling bottom y 200)
icicle(l, 600, 200)
l.hint(420, "O pingente treme antes de cair. Depois de cair, o topo dele é um degrau seguro.")
l.enemy("pinguim_patrulha", 400, 448, 330, 500)
l.coins("row", 560, 410, 4, 30)
# icicle niche: coins above the icicle; the fallen icicle is the step up to the niche
l.relic("relic_icicle", 690, 228)
l.plat("ledge", 670, 252, 60, 16, style="floating", id="niche_ledge")
l.secret("icicle_niche", "hidden_area", "Moedas num nicho do teto, só alcançável usando o pingente caído como degrau", ["relic_icicle"])
# 2. demonstration: a row of three icicles in a corridor with room to escape
l.ground(860, 360, 0, 210, id="overhang_b")
for k, x in enumerate((900, 1010, 1120)):
    icicle(l, x, 210)
l.coins("row", 880, 410, 9, 34)
l.enemy("pinguim_patrulha", 1220, 448, 1180, 1290)
# 3. first valley: a giant snowball rolls across the valley floor
l.ground(1300, 400, 512, id="valley_1")            # valley floor 64 u lower (1300..1700)
snowball(l, 1500, 512, 150, 1.1, 0.0)
l.ground(1700, 300)                                # 1700..2000 back up at 448
l.hint(1240, "Espere a bola gigante subir a outra encosta e passe atrás dela.")
l.coins("arc", 1420, 380, 5, 40, 40)
l.enemy("caracol_cristal", 1850, 448, 1760, 1990)
l.enemy("coruja_nevada", 1880, 300, 1760, 1990)
# 4. escalation: checkpoint in a stone shelter; brittle cornices over the abyss in gusts
l.ground(2000, 360)
l.ground(2040, 60, 340, 108, id="shelter_wall")
l.d["checkpoints"].append({"id": "cp_shelter", "x": 2160, "y": 418})
l.d["events"].append({"id": "msg_horn", "kind": "message", "x": 2160,
                      "params": {"text": "Tio Nevasco: ouviu a corneta? Procure a pedra grande. As cornijas se refazem depois de cair."}})
l.plat("question", 2260, 330, 40, 28, reward="fire")
for k, x in enumerate((2360, 2480, 2600, 2720, 2840)):
    l.plat("crumble", x, 448, 120, 20)               # brittle cornices level with the trail: keep running
l.coins("row", 2400, 400, 12, 40)
wind(l, 2360, 600, -60, period=3.5, duty=0.35)
l.ground(2960, 520)                                # 2960..3480
# 5. combination: an ice tunnel with icicles, penguins and crystal snails
l.ground(3000, 480, 0, 230, id="tunnel_roof")      # tunnel ceiling (3000..3480)
icicle(l, 3100, 230)
icicle(l, 3330, 230)
l.enemy("caracol_cristal", 3220, 448, 3170, 3290)
l.ground(3480, 400, surface="ice")                 # icy floor 3480..3880
l.ground(3880, 120)                                # rock again before the corridor: a place to stop
l.enemy("caracol_cristal", 3930, 448, 3885, 3995)
l.enemy("pinguim_patrulha", 3760, 448, 3640, 3900)
l.enemy("carneiro_glacial", 5940, 448, 5900, 5995)  # guards the summit marker on open ground
l.coins("row", 3520, 410, 6, 40)
# crystal cave (secret): a frosted pipe in the icy floor
l.cave_room(3560, 3700, 6000, reward_item="star", relic_id="relic_crystal", secret_id="crystal_cave",
            secret_kind="hidden_area", clue="Brilho azul atravessando rachaduras perto de um cano coberto de geada")
# 6. twist: the avalanche corridor — four giant snowballs in different phases, safe pockets between them
l.ground(4000, 1000)                               # 4000..5000
for k, (x, ph) in enumerate(((4140, 0.0), (4380, 1.6), (4620, 3.2), (4860, 4.8))):
    snowball(l, x, 448, 45, 1.3, ph, 52)             # ~100 u safe pockets between the balls
l.hint(3960, "Corredor da avalanche: espere no vão entre duas bolas e avance logo atrás da próxima.")
# avalanche relic: narrow ledges above the corridor
l.plat("ledge", 4300, 250, 60, 16, style="floating")
l.plat("ledge", 4480, 210, 60, 16, style="floating")
l.relic("relic_avalanche", 4500, 170)
l.secret("avalanche_ledges", "high_route", "Beirais estreitos com a bandeira do Tio Nevasco acima do corredor", ["relic_avalanche"])
# 7. final test: checkpoint, climb to the summit under icicles, yetis and an owl
l.d["checkpoints"].append({"id": "cp_summit", "x": 5120, "y": 418})
l.ground(5000, 300)                                # 5000..5300
l.plat("question", 5200, 330, 40, 28, reward="heart")
l.ground(5300, 100, 408)                           # steps up
l.ground(5400, 100, 368)
l.ground(5500, 200, 328)                           # 5500..5700 summit shelf
l.ground(5530, 140, 0, 160, id="summit_roof")
icicle(l, 5570, 160)
l.enemy("yeti_mirim", 5650, 328, 5610, 5695)
l.enemy("coruja_nevada", 5250, 250, 5150, 5350)
l.enemy("boneco_neve", 5420, 368, 5405, 5440)
# 8. reward: the summit marker overlooking the Frost Citadel
l.ground(5700, 300, 448)
l.coins("arc", 5720, 380, 5, 34, 40)
l.d["notes"] = ("Fase nova (Mundo 4-5): desafio avançado — pingentes (estreia), bolas de neve gigantes (perigo "
                "móvel com estilo snowball), cornijas frágeis sob rajadas, túnel de gelo e corredor da avalanche.")
save(l.d)
print("ok 4-5")


# ----------------------------------------------------------------------------- 4-6 Cidadela de Geada
F = "fortress"
l = L(id="frost_citadel", name="Cidadela de Geada", world="frozen_peaks", role="fortress", difficulty=5,
      art={"set": "frozen_peaks", "variant": "citadel", "weather": "auto"}, music="frozen_peaks_main",
      bounds={"width": 6800, "height": 1240}, time_limit=400, spawn={"x": 72, "y": 418},
      exit={"id": "goal", "kind": "flag", "x": 6560, "y": 448})
l.d["areas"] = [{"id": "main", "x": 0, "y": 0, "w": 1400, "h": 540, "variant": "citadel_gate"},
                {"id": "hall", "x": 1400, "y": 0, "w": 3900, "h": 540, "variant": "fortress"},
                {"id": "throne", "x": 5300, "y": 0, "w": 1500, "h": 540, "variant": "throne"}]
# 1. introduction: the citadel gate — a brittle ice drawbridge over a shallow frozen moat (no death)
l.ground(0, 520)
l.plat("question", 300, 330, 40, 28, reward="grow")
l.enemy("pinguim_patrulha", 430, 448, 370, 515)
l.ground(520, 360, 520, 80, id="moat_floor", surface="ice")   # shallow moat: falling only costs time
for k, x in enumerate((520, 640, 760)):
    l.plat("crumble", x, 448, 120, 20)            # brittle ice drawbridge
l.plat("ledge", 836, 486, 40, 16, style="floating", id="moat_step")   # climb back out of the moat
l.ground(880, 520)                                 # 880..1400
l.enemy("carneiro_glacial", 1150, 448, 1040, 1390)
l.ground(1240, 50, 384, 64, id="granite_block")    # the ram stuns itself on the granite block
l.hint(960, "O carneiro investe e fica tonto ao bater no bloco de granito: pise nele nessa hora.")
# 2. demonstration: courtyard with an icicle chandelier over rock floor
l.ground(1400, 800, style=F)                       # 1400..2200 (rock)
l.ground(1520, 460, 0, 190, style=F, id="chandelier_beam")
for x in (1560, 1680, 1800, 1930):
    icicle(l, x, 190)
l.enemy("caracol_cristal", 1960, 448, 1880, 2040)
l.coins("row", 1540, 410, 9, 36)
# 3. first challenge: stained-glass hall — rock bands (light) between ice floors
l.d["checkpoints"].append({"id": "cp_hall", "x": 2260, "y": 418})
l.ground(2200, 200, style=F)                       # 2200..2400 rock (checkpoint)
l.plat("question", 2330, 330, 40, 28, reward="fire")
l.ground(2400, 240, style=F, surface="ice")        # ice
l.ground(2640, 120, style=F)                       # rock band
l.ground(2760, 240, style=F, surface="ice")        # ice
l.ground(3000, 120, style=F)                       # rock band
l.enemy("pinguim_patrulha", 2560, 448, 2420, 2630)
l.enemy("caracol_cristal", 2880, 448, 2780, 2990)
l.enemy("coruja_nevada", 2700, 300, 2600, 2900)
l.hint(2400, "Onde a luz do vitral pinta o chão, é pedra: ali dá para parar.")
# 4. escalation: window corridor — alternating gusts over brittle ice bridges
l.ground(3120, 160, style=F)                       # 3120..3280
l.enemy("caracol_cristal", 3200, 448, 3130, 3275)
for k, x in enumerate((3280, 3400, 3520, 3640)):
    l.plat("crumble", x, 448, 120, 20)
l.ground(3760, 300, style=F)                       # 3760..4060
wind(l, 3280, 480, 70, period=4.0, duty=0.4)
wind(l, 3280, 480, -70, period=4.0, duty=0.4, phase=2.0)
l.coins("row", 3300, 400, 10, 44)
l.enemy("coruja_nevada", 3900, 300, 3800, 4040)
l.enemy("pinguim_patrulha", 3960, 448, 3800, 4055)
# 5. combination: the tower — ledges with a yeti on the landing, icicles under the roof
l.ground(4060, 100, 408, style=F)
l.ground(4160, 100, 368, style=F)
l.ground(4260, 240, 328, style=F)                  # tower landing 4260..4500
l.ground(4300, 160, 0, 150, style=F, id="tower_roof")
icicle(l, 4340, 150)
l.enemy("yeti_mirim", 4440, 328, 4400, 4495)
l.ground(4500, 100, 368, style=F)
l.ground(4600, 100, 408, style=F)
# 6. twist: the ice dungeon — a lower corridor with rolling snowballs and a ram at the bars
l.ground(4700, 500, 512, style=F, id="dungeon_floor")   # 4700..5200, 64 u lower
snowball(l, 4880, 512, 60, 1.2, 0.0, 48)
l.ground(4960, 60, 300, 120, style=F, id="dungeon_bar")   # hanging bars (head clearance 92 u)
l.enemy("carneiro_glacial", 5100, 512, 5040, 5195)
# 7. final test: antechamber with checkpoint, heart and the guide's warning
l.ground(5200, 160, style=F)                       # 5200..5360 back up
l.d["checkpoints"].append({"id": "cp_ante", "x": 5240, "y": 418})
l.plat("question", 5300, 330, 40, 28, reward="heart")
l.d["events"].append({"id": "msg_helmet", "kind": "message", "x": 5240,
                      "params": {"text": "Tio Nevasco: a morsa usa elmo de gelo. Casco de cristal chutado (ou três bolas de fogo) racha o elmo!"}})
# 8. the throne room: Morsa Gelomar
ax = 5360                                          # arena 5360..6200 (lock 5300..6260)
l.plat("switch", ax, 300, 40, 148, style="gate", id="gate_left", active=False)
l.ground(ax, 240, style=F)                         # rock under the gate and beside the left wall
l.ground(ax + 240, 440, style=F, surface="ice")    # mirror-ice floor in the middle
l.ground(ax + 680, 200, style=F)                   # rock beside the right wall and under its gate
l.plat("switch", ax + 800, 300, 40, 148, style="gate", id="gate_right", active=True)
l.ground(ax - 60, 960, 0, 120, style=F, id="throne_ceiling")
l.plat("ledge", ax + 60, 352, 80, 20, style="fortress", id="throne_ledge_l")
l.plat("ledge", ax + 700, 352, 80, 20, style="fortress", id="throne_ledge_r")
l.enemy("morsa_gelomar", ax + 560, 448, ax + 40, ax + 800,
        params={"holes": [[ax + 70, 420], [ax + 740, 420]], "ceiling": 130, "wake_range": 520})
l.d["events"].append({"id": "arena", "kind": "boss_arena", "x": ax + 120,
                      "params": {"lock": [ax - 60, 0, 960, 540], "close": ["gate_left"], "open": ["gate_right"],
                                 "text": "A Morsa Gelomar guarda o salão do trono!"}})
l.ground(ax + 880, 6800 - (ax + 880), style=F)     # exit hall after the right gate (the fountain-beacon)
l.coins("arc", ax + 1000, 380, 6, 34, 40)
l.enemy("pinguim_patrulha", ax + 1040, 448, ax + 940, ax + 1140)
# secrets
l.relic("relic_window", 3460, 300)
l.secret("window_relic", "high_route", "Um vitral com uma estrela aponta para o alto do corredor das janelas", ["relic_window"])
l.cave_room(2050, 2160, 6800, reward_item="star", relic_id="relic_crypt", secret_id="crypt",
            secret_kind="hidden_area", clue="Gelo rachado com bolhas de ar formando uma seta", variant="cave")
l.relic("relic_bell", 4380, 240)
l.secret("bell_relic", "high_route", "Sino de gelo tocando sozinho no alto da torre", ["relic_bell"])
l.d["notes"] = ("Fase nova (Mundo 4-6): fortaleza — ponte levadiça de gelo, lustre de pingentes, salão dos vitrais "
                "(pedra marcada pela luz), corredor das janelas com rajadas alternadas, torre, masmorra com bolas "
                "de neve e salão do trono com a Morsa Gelomar.")
save(l.d)
print("ok 4-6")
