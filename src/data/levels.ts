import type {
  EnemyKind,
  ItemKind,
  Level,
  PlatformKind,
  Theme,
} from "../core/types";

export const THEMES: Theme[] = [
  {
    name: "Reino Verde",
    subtitle: "Colinas, canais e pomares",
    sky: "#88d5ed",
    far: "#70ad91",
    near: "#438568",
    ground: "#a97743",
    top: "#75bc4b",
    accent: "#ffda6b",
    weather: "none",
  },
  {
    name: "Deserto Dourado",
    subtitle: "Dunas e templos sob o sol",
    sky: "#f8ce8a",
    far: "#daae77",
    near: "#bb8b60",
    ground: "#be8652",
    top: "#edbc6e",
    accent: "#79d2c2",
    weather: "sand",
  },
  {
    name: "Montanhas Geladas",
    subtitle: "Encostas, pontes e neve",
    sky: "#b9d9ef",
    far: "#92b2cc",
    near: "#6989aa",
    ground: "#7f95ac",
    top: "#e0f7ff",
    accent: "#ffd775",
    weather: "snow",
  },
  {
    name: "Floresta Encantada",
    subtitle: "Copas luminosas e ruínas",
    sky: "#223a49",
    far: "#2e5260",
    near: "#24564b",
    ground: "#705847",
    top: "#66b887",
    accent: "#dcc178",
    weather: "spores",
  },
  {
    name: "Fortaleza Vulcânica",
    subtitle: "Basalto, brasa e a última luz",
    sky: "#302637",
    far: "#594050",
    near: "#7b4742",
    ground: "#53424b",
    top: "#a37666",
    accent: "#ffb45d",
    weather: "embers",
  },
];

// Coordinates describe solid surfaces. Spawn, checkpoint and pipe destinations
// describe the player's top-left; exit.y is the bottom of the exit flag.
// Maps are deliberately composed below, while these helpers only avoid repeating
// the shape of a rectangle, a row of coins, or an enemy declaration.
const counts = new Map<string, number>();
const uid = (l: Level, kind: string) => {
  const key = `${l.id}-${kind}`;
  const n = (counts.get(key) ?? 0) + 1;
  counts.set(key, n);
  return `${key}-${n}`;
};
const make = (
  world: number,
  stage: number,
  name: string,
  width: number,
  checkpointX: number,
  checkpointY = 414,
): Level => ({
  id: `${world}-${stage}`,
  world,
  stage,
  name,
  width,
  height: 540,
  time: 260 + Math.round(width / 30),
  spawn: { x: 72, y: 414 },
  checkpoint: { x: checkpointX, y: checkpointY },
  exit: { x: width - 150, y: 448 },
  platforms: [],
  coins: [],
  enemies: [],
  items: [],
  hazards: [],
  hints: [],
});
const p = (
  l: Level,
  kind: PlatformKind,
  x: number,
  y: number,
  w = 40,
  h = 24,
  reward?: ItemKind | "coin",
) => {
  const platform = {
    id: uid(l, kind),
    kind,
    x,
    y,
    w,
    h,
    ...(reward ? { reward } : {}),
  };
  l.platforms.push(platform);
  return platform;
};
const g = (
  l: Level,
  x: number,
  w: number,
  y = 448,
  kind: "ground" | "ice" = "ground",
) => p(l, kind, x, y, w, 540 - y + 60);
const row = (l: Level, x: number, y: number, count: number, spacing = 34) => {
  for (let i = 0; i < count; i++)
    l.coins.push({ id: uid(l, "coin"), x: x + i * spacing, y, w: 16, h: 20 });
};
const arc = (l: Level, x: number, y: number, count = 5, spacing = 30) => {
  for (let i = 0; i < count; i++)
    l.coins.push({
      id: uid(l, "coin"),
      x: x + i * spacing,
      y: y - Math.sin((Math.PI * i) / (count - 1)) * 32,
      w: 16,
      h: 20,
    });
};
const relic = (l: Level, x: number, y: number) =>
  l.coins.push({ id: uid(l, "relic"), x, y, w: 22, h: 24, special: true });
const enemy = (
  l: Level,
  kind: EnemyKind,
  x: number,
  groundY: number,
  left: number,
  right: number,
  hp?: number,
) => {
  const w = kind === "boss" ? 62 : kind === "armored" ? 34 : 28;
  const h =
    kind === "boss" ? 64 : kind === "flyer" ? 24 : kind === "armored" ? 32 : 28;
  l.enemies.push({
    id: uid(l, kind),
    kind,
    x,
    y: groundY - h,
    w,
    h,
    patrol: [left, right],
    ...(hp ? { hp } : {}),
  });
};
const item = (l: Level, kind: ItemKind, x: number, y = 420) =>
  l.items.push({ id: uid(l, kind), kind, x, y, w: 24, h: 24 });
const moving = (
  l: Level,
  x: number,
  y: number,
  w: number,
  axis: "x" | "y",
  range: number,
  speed: number,
  phase = 0,
) => {
  const platform = p(l, "moving", x, y, w, 18);
  Object.assign(platform, { motion: { axis, range, speed, phase } });
};
const spike = (l: Level, x: number, w = 48, groundY = 448) =>
  l.hazards.push({ kind: "spikes", x, y: groundY - 14, w, h: 14 });
const lava = (l: Level, x: number, w: number) =>
  l.hazards.push({ kind: "lava", x, y: 474, w, h: 66 });
const orbit = (l: Level, x: number, y: number, range: number, speed: number) =>
  l.hazards.push({ kind: "moving", x, y, w: 26, h: 26, range, speed });
const hint = (l: Level, x: number, text: string) => l.hints.push({ x, text });
const secret = (
  l: Level,
  entryX: number,
  roomX: number,
  reward: ItemKind = "heart",
) => {
  // The chamber is entered and left by pipes; no unreachable climb is required.
  const enter = p(l, "pipe", entryX, 400, 56, 48);
  const back = { x: entryX + 72, y: 402 };
  Object.assign(enter, {
    destination: { x: roomX + 24, y: 126 },
    returnPoint: back,
  });
  p(l, "brick", roomX, 176, 298, 20);
  const leave = p(l, "pipe", roomX + 226, 144, 56, 32);
  Object.assign(leave, {
    destination: back,
    returnPoint: { x: roomX + 24, y: 126 },
  });
  row(l, roomX + 64, 132, 4, 34);
  relic(l, roomX + 178, 130);
  item(l, reward, roomX + 128, 146);
};

// WORLD 1 — gentle gaps first; route choice and block discovery follow.
const meadow = make(1, 1, "Primeiros Passos", 3200, 1510);
g(meadow, 0, 1040);
g(meadow, 1140, 780);
g(meadow, 2040, 1160);
row(meadow, 200, 410, 6);
arc(meadow, 1010, 374, 5, 32);
arc(meadow, 1900, 374, 6, 30);
p(meadow, "question", 410, 350, 40, 28, "grow");
p(meadow, "brick", 450, 350, 40, 28);
p(meadow, "question", 490, 350, 40, 28, "coin");
p(meadow, "question", 570, 350, 40, 28, "heart");
p(meadow, "brick", 780, 382, 92, 22);
row(meadow, 796, 347, 2);
enemy(meadow, "walker", 700, 448, 650, 900);
enemy(meadow, "walker", 1250, 448, 1220, 1390);
p(meadow, "brick", 1680, 374, 100, 22);
p(meadow, "brick", 1830, 306, 112, 22);
row(meadow, 1700, 340, 3);
row(meadow, 1840, 270, 3);
secret(meadow, 2250, 2500, "heart");
p(meadow, "hidden", 2460, 344, 40, 24, "star");
enemy(meadow, "shell", 2640, 448, 2590, 2800);
row(meadow, 2840, 410, 6);
hint(meadow, 120, "Ande, pule e siga as moedas.");
hint(meadow, 470, "Bata por baixo nos blocos com luz.");
hint(meadow, 1000, "Corra para cruzar o vão.");
hint(meadow, 2190, "Sobre o cano, pressione ↓ para explorar.");

const canals = make(1, 2, "Canais do Vale", 3500, 1640);
g(canals, 0, 640);
g(canals, 740, 640, 416);
g(canals, 1500, 700);
g(canals, 2340, 1160);
row(canals, 230, 410, 5);
p(canals, "question", 470, 350, 40, 28, "grow");
arc(canals, 604, 363, 5, 34);
p(canals, "pipe", 1020, 368, 58, 48);
p(canals, "question", 1150, 320, 40, 28, "coin");
p(canals, "brick", 1190, 320, 40, 28);
enemy(canals, "walker", 870, 416, 800, 975);
enemy(canals, "shell", 1200, 416, 1130, 1300);
moving(canals, 1360, 356, 90, "y", 30, 1.6);
arc(canals, 1350, 336, 5, 32);
p(canals, "brick", 1810, 376, 98, 22);
moving(canals, 1950, 312, 100, "x", 34, 1.1);
p(canals, "brick", 2110, 290, 110, 22);
relic(canals, 2147, 252);
arc(canals, 2150, 362, 7, 30);
p(canals, "question", 2490, 350, 40, 28, "fire");
secret(canals, 2670, 2860, "grow");
enemy(canals, "flyer", 2950, 352, 2830, 3160);
row(canals, 3180, 410, 5);
hint(canals, 120, "As pontes também escondem caminhos altos.");
hint(canals, 1380, "A plataforma sobe e desce. Espere o momento.");
hint(canals, 2620, "Há luz dentro deste cano.");

const orchard = make(1, 3, "Guardião do Pomar", 3900, 1990);
g(orchard, 0, 880);
g(orchard, 1000, 650);
g(orchard, 1750, 930);
g(orchard, 2780, 1120);
p(orchard, "question", 330, 350, 40, 28, "grow");
p(orchard, "question", 410, 350, 40, 28, "coin");
row(orchard, 530, 410, 5);
enemy(orchard, "shell", 720, 448, 600, 830);
arc(orchard, 860, 368, 6, 30);
p(orchard, "brick", 1130, 378, 100, 22);
p(orchard, "brick", 1280, 310, 104, 22);
p(orchard, "crumble", 1450, 294, 100, 20);
relic(orchard, 1482, 257);
row(orchard, 1288, 275, 3);
enemy(orchard, "walker", 1510, 448, 1430, 1590);
arc(orchard, 1630, 364, 5, 32);
secret(orchard, 2170, 2340, "star");
p(orchard, "question", 2580, 350, 40, 28, "fire");
enemy(orchard, "flyer", 2590, 330, 2410, 2630);
arc(orchard, 2640, 370, 6, 30);
item(orchard, "heart", 2970);
p(orchard, "brick", 3100, 374, 100, 22);
enemy(orchard, "boss", 3460, 448, 3190, 3660, 3);
row(orchard, 3730, 410, 3);
hint(orchard, 140, "O pomar guarda sua primeira grande prova.");
hint(orchard, 1430, "Blocos frágeis cedem após alguns instantes.");
hint(orchard, 3000, "Pule sobre o guardião quando ele baixar a guarda.");

// WORLD 2 — narrow columns, sandstone terraces and timed hazards.
const dunes = make(2, 1, "Dunas ao Vento", 3800, 2040);
g(dunes, 0, 1000);
g(dunes, 1120, 650);
g(dunes, 1900, 900);
g(dunes, 2930, 870);
p(dunes, "question", 330, 350, 40, 28, "grow");
row(dunes, 150, 410, 4);
p(dunes, "pipe", 550, 400, 62, 48);
p(dunes, "pipe", 690, 376, 62, 72);
row(dunes, 562, 365, 2);
enemy(dunes, "shell", 840, 448, 805, 970);
arc(dunes, 980, 368, 6, 30);
p(dunes, "brick", 1200, 380, 80, 24);
p(dunes, "brick", 1330, 316, 80, 24);
p(dunes, "question", 1460, 290, 40, 28, "star");
p(dunes, "brick", 1500, 290, 80, 28);
relic(dunes, 1530, 252);
enemy(dunes, "walker", 1530, 448, 1450, 1670);
arc(dunes, 1750, 365, 6, 30);
spike(dunes, 2280, 48);
p(dunes, "question", 2200, 350, 40, 28, "fire");
enemy(dunes, "shooter", 2510, 448, 2480, 2600);
p(dunes, "brick", 2620, 376, 96, 20);
arc(dunes, 2780, 365, 6, 30);
secret(dunes, 3130, 3290, "heart");
row(dunes, 3560, 410, 4);
hint(dunes, 160, "Corra entre as dunas; observe onde pousar.");
hint(dunes, 2230, "Espinhos são vencidos com um salto preciso.");
hint(dunes, 2470, "O sentinela dispara em intervalos.");

const canyon = make(2, 2, "Pontes do Cânion", 4100, 2180, 382);
g(canyon, 0, 620);
g(canyon, 740, 550, 416);
g(canyon, 1420, 680, 384);
g(canyon, 2220, 520, 416);
g(canyon, 2860, 1240);
row(canyon, 170, 410, 4);
p(canyon, "question", 430, 350, 40, 28, "grow");
arc(canyon, 600, 348, 6, 30);
p(canyon, "crumble", 890, 338, 90, 18);
p(canyon, "crumble", 1040, 288, 96, 18);
relic(canyon, 1074, 250);
enemy(canyon, "shell", 1120, 416, 1060, 1220);
arc(canyon, 1270, 319, 6, 30);
p(canyon, "question", 1590, 288, 40, 28, "coin");
p(canyon, "question", 1670, 288, 40, 28, "fire");
enemy(canyon, "shooter", 1840, 384, 1770, 1980);
moving(canyon, 1960, 307, 92, "x", 32, 1.3);
arc(canyon, 2080, 302, 6, 30);
spike(canyon, 2470, 52, 416);
moving(canyon, 2550, 308, 110, "y", 27, 1.25);
arc(canyon, 2710, 335, 6, 30);
secret(canyon, 3130, 3260, "star");
orbit(canyon, 3500, 361, 40, 1.6);
enemy(canyon, "flyer", 3690, 338, 3570, 3820);
row(canyon, 3830, 410, 4);
// The checkpoint rests on the broad y384 terrace, before its encounter.
canyon.checkpoint = { x: 1480, y: 350 };
hint(canyon, 140, "O cânion tem terraços e atalhos acima.");
hint(canyon, 810, "Salte outra vez antes de a ponte ceder.");
hint(canyon, 3430, "Espere a chama se afastar para passar.");

const temple = make(2, 3, "Templo das Areias", 4200, 2190);
g(temple, 0, 770);
g(temple, 880, 670);
g(temple, 1660, 1140);
g(temple, 2920, 1280);
row(temple, 190, 410, 4);
p(temple, "question", 420, 350, 40, 28, "grow");
p(temple, "pipe", 610, 400, 64, 48);
arc(temple, 740, 367, 6, 30);
p(temple, "brick", 1010, 382, 86, 24);
p(temple, "brick", 1130, 320, 90, 24);
p(temple, "brick", 1270, 268, 104, 24);
row(temple, 1278, 233, 3);
relic(temple, 1332, 220);
enemy(temple, "armored", 1400, 448, 1340, 1500);
arc(temple, 1520, 365, 6, 30);
spike(temple, 1810, 48);
p(temple, "question", 1980, 350, 40, 28, "fire");
p(temple, "question", 2060, 350, 40, 28, "coin");
secret(temple, 2380, 2510, "heart");
enemy(temple, "shooter", 2650, 448, 2600, 2730);
arc(temple, 2770, 365, 6, 30);
p(temple, "brick", 3070, 375, 100, 24);
p(temple, "question", 3200, 350, 40, 28, "star");
item(temple, "heart", 3340);
enemy(temple, "boss", 3700, 448, 3440, 3980, 4);
row(temple, 4030, 410, 3);
hint(temple, 170, "As ruínas têm degraus para quem procura relíquias.");
hint(temple, 1360, "A armadura resiste; procure espaço para saltar.");
hint(temple, 3280, "A arena está adiante. Guarde sua luz.");

// WORLD 3 — slippery landings always have enough safe runway.
const lake = make(3, 1, "Lago de Cristal", 3600, 2040);
g(lake, 0, 920);
g(lake, 1040, 820, 448, "ice");
g(lake, 1980, 640);
g(lake, 2740, 860, 448, "ice");
p(lake, "question", 400, 350, 40, 28, "grow");
row(lake, 160, 410, 5);
enemy(lake, "shell", 700, 448, 620, 860);
arc(lake, 900, 367, 6, 30);
p(lake, "ice", 1220, 382, 100, 20);
p(lake, "ice", 1380, 314, 106, 20);
row(lake, 1232, 345, 3);
relic(lake, 1418, 278);
p(lake, "question", 1570, 350, 40, 28, "coin");
enemy(lake, "flyer", 1580, 324, 1480, 1750);
arc(lake, 1830, 367, 6, 30);
spike(lake, 2240, 44);
secret(lake, 2370, 2470, "fire");
arc(lake, 2590, 365, 6, 30);
p(lake, "question", 2940, 350, 40, 28, "star");
enemy(lake, "walker", 3160, 448, 3070, 3300);
row(lake, 3310, 410, 5);
hint(lake, 140, "No gelo, solte a corrida antes de pousar.");
hint(lake, 1120, "A trilha de cima leva a uma relíquia.");
hint(lake, 2810, "Há espaço para frear depois de cada salto.");

const summit = make(3, 2, "Escalada Azul", 4400, 2280, 366);
g(summit, 0, 600);
g(summit, 710, 560, 416, "ice");
g(summit, 1390, 710, 368);
g(summit, 2220, 620, 400, "ice");
g(summit, 2950, 560, 432);
g(summit, 3630, 770);
row(summit, 180, 410, 4);
p(summit, "question", 380, 350, 40, 28, "grow");
arc(summit, 575, 348, 6, 30);
p(summit, "ice", 910, 350, 90, 20);
p(summit, "ice", 1060, 286, 104, 20);
relic(summit, 1094, 248);
enemy(summit, "shell", 1100, 416, 1010, 1230);
arc(summit, 1250, 295, 6, 30);
p(summit, "question", 1560, 270, 40, 28, "fire");
p(summit, "question", 1640, 270, 40, 28, "coin");
enemy(summit, "shooter", 1850, 368, 1760, 1980);
arc(summit, 2080, 296, 6, 30);
moving(summit, 2430, 321, 104, "x", 30, 1.2);
p(summit, "ice", 2630, 286, 108, 20);
row(summit, 2638, 248, 3);
arc(summit, 2820, 321, 6, 30);
spike(summit, 3230, 48, 432);
p(summit, "question", 3360, 335, 40, 28, "heart");
arc(summit, 3480, 352, 6, 30);
secret(summit, 3770, 3890, "star");
row(summit, 4130, 410, 4);
hint(summit, 150, "A subida é feita em terraços seguros.");
hint(summit, 1710, "Use os blocos para ganhar altura.");
hint(summit, 3150, "Pouse antes dos espinhos e salte de novo.");

const blizzard = make(3, 3, "Coração da Nevasca", 4600, 2270);
g(blizzard, 0, 780);
g(blizzard, 900, 650, 416, "ice");
g(blizzard, 1660, 850);
g(blizzard, 2630, 730, 416, "ice");
g(blizzard, 3480, 1120);
row(blizzard, 170, 410, 4);
p(blizzard, "question", 430, 350, 40, 28, "grow");
enemy(blizzard, "armored", 660, 448, 575, 725);
arc(blizzard, 750, 349, 6, 30);
p(blizzard, "ice", 1060, 340, 94, 20);
moving(blizzard, 1240, 277, 104, "x", 28, 1.45);
relic(blizzard, 1278, 238);
enemy(blizzard, "flyer", 1430, 320, 1320, 1500);
arc(blizzard, 1510, 330, 6, 30);
spike(blizzard, 1860, 48);
p(blizzard, "question", 2040, 350, 40, 28, "fire");
secret(blizzard, 2360, 2440, "heart");
arc(blizzard, 2480, 345, 6, 30);
enemy(blizzard, "shooter", 2870, 416, 2810, 2970);
p(blizzard, "question", 3090, 318, 40, 28, "star");
moving(blizzard, 3180, 320, 96, "y", 26, 1.5);
arc(blizzard, 3320, 341, 6, 30);
item(blizzard, "heart", 3650);
p(blizzard, "ice", 3760, 376, 106, 20);
enemy(blizzard, "boss", 4110, 448, 3870, 4370, 5);
row(blizzard, 4420, 410, 3);
hint(blizzard, 140, "A neve esconde rotas altas, não o caminho seguro.");
hint(blizzard, 3240, "Observe a plataforma antes de atravessar.");
hint(blizzard, 3660, "A rocha protege uma última arena de gelo.");

// WORLD 4 — optional canopy routes reward confident movement.
const canopy = make(4, 1, "Copas Luminosas", 4000, 1950);
g(canopy, 0, 980);
g(canopy, 1090, 960);
g(canopy, 2170, 640);
g(canopy, 2930, 1070);
row(canopy, 170, 410, 4);
p(canopy, "question", 350, 350, 40, 28, "grow");
p(canopy, "brick", 580, 376, 104, 24);
p(canopy, "crumble", 750, 310, 102, 20);
p(canopy, "crumble", 916, 258, 100, 20);
row(canopy, 762, 273, 3);
relic(canopy, 949, 220);
enemy(canopy, "shell", 840, 448, 760, 920);
arc(canopy, 950, 366, 6, 30);
enemy(canopy, "shooter", 1320, 448, 1260, 1410);
p(canopy, "question", 1490, 350, 40, 28, "fire");
p(canopy, "brick", 1600, 374, 108, 22);
moving(canopy, 1770, 310, 106, "x", 28, 1.4);
row(canopy, 1780, 272, 3);
arc(canopy, 2020, 365, 6, 30);
spike(canopy, 2400, 52);
enemy(canopy, "flyer", 2580, 318, 2450, 2710);
arc(canopy, 2780, 365, 6, 30);
secret(canopy, 3160, 3330, "star");
p(canopy, "question", 3560, 350, 40, 28, "heart");
row(canopy, 3730, 410, 4);
hint(canopy, 150, "Siga o chão ou aventure-se pelas copas.");
hint(canopy, 690, "As folhas frágeis pedem saltos sem demora.");
hint(canopy, 2390, "Ouça o ritmo dos sentinelas e avance.");

const ruins = make(4, 2, "Ruínas dos Vagalumes", 4500, 2320);
g(ruins, 0, 620);
g(ruins, 740, 710, 416);
g(ruins, 1570, 1070);
g(ruins, 2760, 520, 400);
g(ruins, 3400, 1100);
p(ruins, "question", 350, 350, 40, 28, "grow");
row(ruins, 160, 410, 4);
arc(ruins, 590, 350, 6, 30);
p(ruins, "brick", 900, 344, 100, 24);
p(ruins, "hidden", 1040, 280, 40, 24, "star");
p(ruins, "brick", 1110, 276, 104, 24);
relic(ruins, 1142, 238);
enemy(ruins, "armored", 1250, 416, 1200, 1380);
arc(ruins, 1420, 330, 6, 30);
secret(ruins, 1790, 1980, "fire");
p(ruins, "question", 2220, 350, 40, 28, "coin");
p(ruins, "question", 2300, 350, 40, 28, "heart");
p(ruins, "crumble", 2500, 376, 90, 20);
arc(ruins, 2610, 330, 6, 30);
enemy(ruins, "shooter", 2990, 400, 2910, 3090);
orbit(ruins, 3190, 318, 35, 1.25);
moving(ruins, 3120, 306, 110, "x", 30, 1.25);
arc(ruins, 3260, 320, 6, 30);
p(ruins, "brick", 3590, 376, 94, 24);
p(ruins, "crumble", 3750, 310, 98, 20);
p(ruins, "brick", 3910, 268, 96, 24);
row(ruins, 3918, 232, 3);
enemy(ruins, "flyer", 4110, 337, 4030, 4270);
row(ruins, 4270, 410, 4);
hint(ruins, 140, "Há blocos invisíveis onde as luzes se reúnem.");
hint(ruins, 1720, "O cano revela um salão entre as ruínas.");
hint(ruins, 3130, "A chama descreve um ciclo. Cruze após sua passagem.");

const guardian = make(4, 3, "A Árvore Ancestral", 4700, 2460);
g(guardian, 0, 820);
g(guardian, 940, 690);
g(guardian, 1750, 1040);
g(guardian, 2910, 620);
g(guardian, 3650, 1050);
row(guardian, 160, 410, 4);
p(guardian, "question", 340, 350, 40, 28, "grow");
p(guardian, "brick", 510, 376, 106, 24);
p(guardian, "crumble", 680, 310, 104, 20);
arc(guardian, 790, 364, 6, 30);
enemy(guardian, "armored", 1140, 448, 1040, 1250);
p(guardian, "question", 1290, 350, 40, 28, "fire");
p(guardian, "question", 1370, 350, 40, 28, "coin");
arc(guardian, 1600, 364, 6, 30);
p(guardian, "brick", 1850, 378, 98, 24);
moving(guardian, 2010, 312, 108, "x", 25, 1.5);
p(guardian, "brick", 2190, 262, 106, 24);
relic(guardian, 2232, 224);
enemy(guardian, "flyer", 2170, 368, 2020, 2330);
secret(guardian, 2590, 2730, "star");
arc(guardian, 2750, 365, 6, 30);
spike(guardian, 3100, 50);
enemy(guardian, "shooter", 3290, 448, 3240, 3420);
moving(guardian, 3380, 315, 96, "y", 27, 1.35);
arc(guardian, 3500, 364, 6, 30);
p(guardian, "question", 3770, 350, 40, 28, "heart");
item(guardian, "fire", 3870);
enemy(guardian, "boss", 4200, 448, 3980, 4470, 6);
row(guardian, 4520, 410, 3);
hint(guardian, 140, "A árvore oferece dois caminhos para a mesma luz.");
hint(guardian, 1830, "Ganhe altura para alcançar a relíquia.");
hint(guardian, 3810, "Observe o guardião e escolha sua abertura.");

// WORLD 5 — lava marks the gaps, while bridges and arenas remain solid.
const basalt = make(5, 1, "Pontes de Basalto", 4300, 2280);
g(basalt, 0, 700);
g(basalt, 810, 640);
g(basalt, 1570, 830);
g(basalt, 2520, 650);
g(basalt, 3290, 1010);
lava(basalt, 700, 110);
lava(basalt, 1450, 120);
lava(basalt, 2400, 120);
lava(basalt, 3170, 120);
row(basalt, 160, 410, 4);
p(basalt, "question", 350, 350, 40, 28, "grow");
arc(basalt, 675, 365, 6, 30);
enemy(basalt, "armored", 1030, 448, 930, 1140);
p(basalt, "question", 1190, 350, 40, 28, "fire");
p(basalt, "brick", 1320, 378, 88, 24);
arc(basalt, 1420, 365, 6, 30);
p(basalt, "brick", 1710, 376, 96, 24);
moving(basalt, 1870, 310, 104, "x", 28, 1.3);
p(basalt, "brick", 2040, 258, 104, 24);
relic(basalt, 2074, 220);
orbit(basalt, 2130, 369, 33, 1.4);
arc(basalt, 2370, 365, 6, 30);
enemy(basalt, "shooter", 2720, 448, 2650, 2800);
spike(basalt, 2910, 48);
p(basalt, "question", 3030, 350, 40, 28, "star");
arc(basalt, 3140, 365, 6, 30);
secret(basalt, 3490, 3650, "heart");
enemy(basalt, "shell", 3900, 448, 3830, 4030);
row(basalt, 4070, 410, 4);
hint(basalt, 140, "Os vãos brilham com lava; as pontes são seguras.");
hint(basalt, 1830, "A rota alta contorna a chama.");
hint(basalt, 2860, "Pouse no trecho livre antes dos espinhos.");

const furnace = make(5, 2, "Fornalha dos Ecos", 4800, 2470);
g(furnace, 0, 660);
g(furnace, 780, 680, 416);
g(furnace, 1580, 660);
g(furnace, 2360, 760);
g(furnace, 3240, 620, 400);
g(furnace, 3980, 820);
lava(furnace, 660, 120);
lava(furnace, 1460, 120);
lava(furnace, 2240, 120);
lava(furnace, 3120, 120);
lava(furnace, 3860, 120);
row(furnace, 160, 410, 4);
p(furnace, "question", 350, 350, 40, 28, "grow");
arc(furnace, 630, 348, 6, 30);
enemy(furnace, "shooter", 1000, 416, 925, 1100);
p(furnace, "question", 1150, 318, 40, 28, "fire");
orbit(furnace, 1320, 327, 35, 1.5);
arc(furnace, 1420, 331, 6, 30);
p(furnace, "brick", 1720, 378, 92, 24);
p(furnace, "crumble", 1870, 312, 96, 20);
p(furnace, "crumble", 2030, 264, 100, 20);
relic(furnace, 2063, 226);
spike(furnace, 2140, 48);
arc(furnace, 2210, 365, 6, 30);
secret(furnace, 2660, 2810, "star");
p(furnace, "question", 2970, 350, 40, 28, "heart");
arc(furnace, 3090, 327, 6, 30);
enemy(furnace, "armored", 3430, 400, 3360, 3530);
moving(furnace, 3600, 323, 104, "y", 25, 1.7);
orbit(furnace, 3770, 310, 35, 1.3);
arc(furnace, 3830, 320, 6, 30);
p(furnace, "question", 4110, 350, 40, 28, "fire");
enemy(furnace, "flyer", 4350, 326, 4230, 4480);
spike(furnace, 4490, 46);
row(furnace, 4590, 410, 3);
hint(furnace, 150, "A fornalha alterna passagens largas e terraços.");
hint(furnace, 1840, "No alto, avance antes que a pedra se desfaça.");
hint(furnace, 3690, "Observe a chama; há chão livre para esperar.");

const citadel = make(5, 3, "A Última Chama", 5200, 2610);
g(citadel, 0, 810);
g(citadel, 930, 730);
g(citadel, 1780, 1100);
g(citadel, 3000, 640, 416);
g(citadel, 3760, 590);
g(citadel, 4470, 730);
lava(citadel, 810, 120);
lava(citadel, 1660, 120);
lava(citadel, 2880, 120);
lava(citadel, 3640, 120);
lava(citadel, 4350, 120);
row(citadel, 170, 410, 4);
p(citadel, "question", 380, 350, 40, 28, "grow");
enemy(citadel, "shell", 650, 448, 560, 760);
arc(citadel, 780, 365, 6, 30);
p(citadel, "brick", 1040, 376, 104, 24);
p(citadel, "crumble", 1210, 310, 104, 20);
moving(citadel, 1380, 258, 110, "x", 25, 1.5);
relic(citadel, 1420, 220);
enemy(citadel, "armored", 1480, 448, 1440, 1570);
arc(citadel, 1630, 365, 6, 30);
p(citadel, "question", 1910, 350, 40, 28, "fire");
p(citadel, "question", 1990, 350, 40, 28, "coin");
orbit(citadel, 2180, 365, 36, 1.4);
enemy(citadel, "shooter", 2370, 448, 2320, 2400);
secret(citadel, 2680, 2750, "star");
arc(citadel, 2850, 347, 6, 30);
p(citadel, "brick", 3140, 344, 102, 24);
p(citadel, "crumble", 3300, 280, 104, 20);
row(citadel, 3308, 242, 3);
enemy(citadel, "flyer", 3470, 310, 3370, 3570);
arc(citadel, 3610, 332, 6, 30);
p(citadel, "question", 3890, 350, 40, 28, "heart");
orbit(citadel, 4080, 360, 34, 1.6);
p(citadel, "brick", 4210, 375, 92, 24);
arc(citadel, 4320, 365, 6, 30);
item(citadel, "fire", 4520);
item(citadel, "heart", 4570);
enemy(citadel, "boss", 4830, 448, 4630, 4970, 7);
row(citadel, 5070, 410, 2);
hint(citadel, 150, "Tudo que aprendeu leva até a última chama.");
hint(citadel, 2600, "Recupere o fôlego neste chão seguro.");
hint(citadel, 4510, "O último guardião protege a saída. Observe e salte.");

export const LEVELS: Level[] = [
  meadow,
  canals,
  orchard,
  dunes,
  canyon,
  temple,
  lake,
  summit,
  blizzard,
  canopy,
  ruins,
  guardian,
  basalt,
  furnace,
  citadel,
];
// Water fills the valley's channels; falling in costs a life, just like lava.
for (const level of LEVELS.filter((l) => l.world === 1)) {
  const grounds = level.platforms
    .filter((p) => p.kind === "ground")
    .sort((a, b) => a.x - b.x);
  for (let i = 1; i < grounds.length; i++) {
    const x = grounds[i - 1].x + grounds[i - 1].w,
      w = grounds[i].x - x;
    if (w > 0) level.hazards.push({ kind: "water", x, y: 500, w, h: 40 });
  }
}
