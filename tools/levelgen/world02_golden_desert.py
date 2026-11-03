"""Deserto Dourado — new levels 2-4, 2-5 and 2-6 (authoring source).

Regenerates lume/data/levels/golden_desert/{sandstorm_pass,sunken_oasis,scarab_pyramid}.json."""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from kit import L, quicksand, save, wind  # noqa: E402,F401

# ----------------------------------------------------------------------------- 2-4 Passagem da Tempestade
l = L(id="sandstorm_pass", name="Passagem da Tempestade", world="golden_desert", role="special", difficulty=3,
      art={"set": "golden_desert", "variant": "storm", "weather": "auto"}, music="golden_desert_main",
      bounds={"width": 5600, "height": 1240}, time_limit=330, spawn={"x": 72, "y": 418},
      exit={"id": "goal", "kind": "flag", "x": 5450, "y": 448})
l.d["areas"] = [{"id": "main", "x": 0, "y": 0, "w": 5600, "h": 540, "variant": "storm"}]
l.ground(0, 1100)
l.plat("question", 480, 340, 40, 28, reward="grow")
wind(l, 300, 600, 80)
l.coins("row", 340, 410, 8, 60)
l.hint(200, "O vento empurra Lume: observe a areia voando antes de saltar.")
l.enemy("escaravelho_areia", 760, 448, 640, 1090)
wind(l, 1100, 900, -120, period=3.6, duty=0.45)
l.ground(1220, 300)
l.ground(1630, 1370)
l.hint(1150, "Rajadas vêm e vão: salte nas calmarias.")
l.coins("arc", 1520, 380, 4, 30, 30)
l.enemy("cacto_sentinela", 1820, 448, 1790, 1850)
l.d["checkpoints"].append({"id": "cp_dunes", "x": 2150, "y": 418})
l.enemy("serpente_duna", 2560, 448, 2200, 2990)
l.hint(2220, "Um rastro de areia se aproxima: pule quando ele tremer.")
l.coins("row", 2300, 410, 6, 70)
wind(l, 3000, 600, 140)
l.relic("relic_gust", 3140, 312)
l.secret("gust_relic", "optional_challenge", "Moedas soltas no ar sobre o vão do vento a favor", ["relic_gust"])
l.coins("diagonal", 3020, 380, 3, 40, 20)
l.ground(3200, 700)
l.enemy("escorpiao_couraca", 3520, 448, 3360, 3700)
l.cave_room(3740, 3780, 5600, reward_item="heart")
wind(l, 3900, 1000, -130, period=3.2, duty=0.5)
l.ground(3990, 510)
l.plat("ledge", 4080, 330, 110, 24, style="ruin")
l.plat("ledge", 4240, 262, 110, 24, style="ruin")
l.relic("relic_ruins", 4282, 216)
l.coins("row", 4096, 296, 3)
l.secret("ruins_route", "high_route", "Colunas caídas formam degraus contra o vento", ["relic_ruins"])
l.enemy("abutre_filhote", 4320, 340, 4100, 4480)
l.ground(4610, 990)
l.enemy("serpente_duna", 4900, 448, 4660, 5200)
l.plat("question", 4720, 340, 40, 28, reward="coin")
l.coins("row", 5220, 410, 5)
l.d["notes"] = "Fase nova (Mundo 2-4): vento em rajadas (contra e a favor) é a mecânica especial; apresenta a Serpente-de-Duna."
save(l.d)

# ----------------------------------------------------------------------------- 2-5 Oásis Soterrado
l = L(id="sunken_oasis", name="Oásis Soterrado", world="golden_desert", role="advanced", difficulty=4,
      art={"set": "golden_desert", "variant": "oasis", "weather": "auto"}, music="golden_desert_main",
      bounds={"width": 6000, "height": 1240}, time_limit=360, spawn={"x": 72, "y": 418},
      exit={"id": "goal", "kind": "flag", "x": 5850, "y": 448})
l.d["areas"] = [{"id": "main", "x": 0, "y": 0, "w": 6000, "h": 540, "variant": "oasis"}]
l.ground(0, 900)
l.plat("question", 380, 340, 40, 28, reward="grow")
l.enemy("escaravelho_areia", 620, 448, 520, 890)
quicksand(l, 900, 80)
l.plat("semisolid", 870, 360, 140, 14, style="palm")
l.hint(800, "Areia movediça: não pare — pule várias vezes para sair.")
l.ground(980, 520)
l.coins("row", 1040, 410, 5)
# oasis pond: swim zone with a low far bank
l.d["zones"].append({"id": "pond", "kind": "swim", "x": 1500, "y": 470, "w": 400, "h": 150})
l.ground(1500, 400, 620, 60, style="terrain", id="pond_bed")
l.coins("arc", 1560, 560, 6, 50, 40)
l.relic("relic_pond", 1690, 586)
l.secret("pond_relic", "hidden_area", "Brilho no fundo da lagoa", ["relic_pond"])
l.hint(1440, "A lagoa é segura: nade e salte para sair do outro lado.")
l.ground(1900, 900)
l.d["checkpoints"].append({"id": "cp_oasis", "x": 2000, "y": 418})
l.enemy("escaravelho_lancador", 2480, 448, 2340, 2700)
l.hint(2200, "O escaravelho ergue a bola de areia antes de arremessar.")
l.plat("question", 2260, 340, 40, 28, reward="fire")
quicksand(l, 2800, 80)
l.ground(2880, 120)
quicksand(l, 3000, 80)
l.ground(3080, 120)
quicksand(l, 3200, 80)
for x, y in ((2820, 360), (3020, 340), (3220, 360)):
    l.plat("semisolid", x, y, 120, 14, style="palm")
l.coins("row", 2840, 320, 9, 48)
l.ground(3280, 920)
l.enemy("serpente_duna", 3620, 448, 3320, 4190)
l.enemy("escaravelho_areia", 3950, 448, 3860, 4190)
l.ground(4200, 400, 400)
l.enemy("escaravelho_lancador", 4420, 400, 4260, 4590)
l.ground(4600, 700)
l.enemy("tatu_bola", 4760, 448, 4640, 4980)
l.enemy("abutre_filhote", 4980, 340, 4800, 5200)
for x, y in ((4650, 330), (4800, 270), (4950, 220)):
    l.plat("semisolid", x, y, 110, 14, style="palm")
l.relic("relic_palms", 4990, 172)
l.secret("palm_route", "high_route", "Copas de palmeiras em escada", ["relic_palms"])
l.ground(5300, 700)
l.cave_room(5420, 5040, 6000, reward_item="star")
l.d["notes"] = ("Fase nova (Mundo 2-5): desafio avançado — areia movediça, lagoa do oásis com saída por salto, "
                "palmeiras como plataformas de mão única e o Escaravelho Lançador (apresentado aqui).")
save(l.d)

# ----------------------------------------------------------------------------- 2-6 Pirâmide do Escaravelho
l = L(id="scarab_pyramid", name="Pirâmide do Escaravelho", world="golden_desert", role="fortress", difficulty=4,
      art={"set": "golden_desert", "variant": "fortress", "weather": "none"}, music="golden_desert_fortress",
      bounds={"width": 4600, "height": 1240}, time_limit=320, spawn={"x": 72, "y": 418},
      exit={"id": "goal", "kind": "flag", "x": 4400, "y": 448})
l.d["areas"] = [{"id": "main", "x": 0, "y": 0, "w": 4600, "h": 540, "variant": "fortress"}]
F = "fortress"
l.ground(0, 700, style=F)
l.plat("question", 260, 340, 40, 28, reward="grow")
l.hazard("spikes", 420, 434, 48, 14)
l.hazard("moving", 600, 356, 26, 26, range=50, speed=1.5)
l.coins("row", 140, 410, 4)
l.plat("crumble", 712, 448, 96, 20)
l.hazard("spikes", 700, 520, 120, 14)
l.ground(820, 180, style=F)                         # 820..1000, then the quicksand trap
quicksand(l, 1000, 80)
l.ground(1080, 520, style=F)
l.relic("relic_trap", 1030, 330)
l.plat("ledge", 990, 372, 100, 22, style="ruin")
l.secret("trap_relic", "optional_challenge", "Laje sobre a armadilha de areia", ["relic_trap"])
l.enemy("escorpiao_couraca", 1300, 448, 1180, 1500)
l.enemy("escaravelho_lancador", 1520, 448, 1420, 1590)
l.d["checkpoints"].append({"id": "cp_hall", "x": 1650, "y": 418})
l.ground(1600, 1360, style=F)
l.plat("question", 1760, 340, 40, 28, reward="fire")
l.enemy("tatu_bola", 1960, 448, 1840, 2200)
l.hazard("moving", 2260, 352, 26, 26, range=46, speed=1.7)
for i, (x, y) in enumerate(((2400, 372), (2520, 304), (2640, 236))):
    l.plat("brick", x, y, 80, 22)
l.relic("relic_gallery", 2672, 190)
l.secret("gallery", "high_route", "Escada de tijolos sobe até a galeria", ["relic_gallery"])
l.enemy("escaravelho_areia", 2760, 448, 2700, 2950)
l.cave_room(2860, 2470, 4600, reward_item="heart")
# boss arena
l.ground(3000, 880, style=F)
l.plat("switch", 3000, 300, 40, 148, id="gate_left", style="gate", active=False)
l.ground(3000, 40, 0, 300, style=F, id="arena_pillar_left")
l.plat("switch", 3840, 300, 40, 148, id="gate_right", style="gate", active=True)
l.ground(3840, 40, 0, 300, style=F, id="arena_pillar_right")
l.ground(3880, 720, style=F)
l.enemy("escaravelho_rei", 3460, 448, 3040, 3840)
l.d["events"].append({"id": "arena", "kind": "boss_arena", "x": 3090,
                      "params": {"lock": [2960, 0, 960, 540], "close": ["gate_left"], "open": ["gate_right"],
                                 "text": "O Escaravelho-Rei emerge da areia!"}})
l.hint(2950, "Quando ele cair de costas, é a hora de pisar.")
l.coins("row", 3920, 410, 6)
l.d["notes"] = ("Fase nova (Mundo 2-6): interior da pirâmide com armadilhas de areia, chamas oscilantes, galeria de tijolos "
                "e a arena do Escaravelho-Rei (emboscada subterrânea, janela de pisão quando ele cai de costas).")
save(l.d)
print("ok")
