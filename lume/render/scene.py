"""Frame composition for gameplay (Marco C pipeline).

Layer order (docs/technical/SISTEMA_GRAFICO.md): sky → atmosphere (clouds) →
far/mid/near parallax → back props → terrain → blocks/pipes/platforms → mid
props → signs, checkpoints, goal → collectibles → enemies → player →
projectiles → particles → liquids → weather → vignette → HUD.

World units are converted to the 960×540 canvas with a camera zoom; every
texture is rasterized for exactly that density, so nothing is upscaled.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional

from ..core.constants import VIEW_HEIGHT, VIEW_WIDTH
from .art import common
from .art.lume_parts import all_parts as lume_parts
from .assets import ArtSpec, ArtStore
from .characters.lume import LumeAnimator
from .enemies import rig_for
from .fx import Fx, FxSystem
from .rig import DrawCommand, RigDrawer, Xf
from .svg import Rand, Svg
from .text import TextCache
from .worlds import world_art
from .worlds.base import WorldArt

CHUNK = 320.0


@dataclass
class TerrainPiece:
    art: str
    x: float
    y: float  # top of the art (surface - headroom)
    w: float
    h: float


@dataclass
class Decor:
    art: str
    x: float
    y: float
    scale: float
    flip: bool
    layer: str


def _hex(color: str) -> tuple[int, int, int]:
    c = color.lstrip("#")
    return int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)


class Scene:
    def __init__(self, display, *, zoom: float = 1.3, effects: bool = True, quality: str = "high") -> None:
        self.display = display
        self.zoom = zoom
        self.effects = effects
        self.quality = quality
        bg = {"high": 1.0, "medium": 0.75, "low": 0.6}.get(quality, 1.0)
        self.store = ArtStore(display, display.scale * zoom, background_density=bg)
        self.text = TextCache(display)
        self.fx = FxSystem(600 if effects else 120)
        self.lume = LumeAnimator()
        self.level_id: Optional[str] = None
        self.world: Optional[WorldArt] = None
        self.rigs: dict[str, object] = {}
        self.time = 0.0
        self.view = (0.0, 0.0)
        self.terrain: list[TerrainPiece] = []
        self.decor: list[Decor] = []
        self.weather_seeded = False
        self._register_static()
        self.stats = {"draws": 0}

    # ------------------------------------------------------------------ registration
    def _register_static(self) -> None:
        self.store.register_many(common.specs())
        for part in lume_parts():
            self.store.register(ArtSpec(part.id, (lambda p=part: p.svg), 0.40, part.pivot, "lume"))

    def _canvas_spec(self, art_id: str, build, pivot=(0, 0), group="world", floor=1.0) -> None:
        # canvas-space art: density = display.scale (world density / zoom)
        self.store.register(ArtSpec(art_id, build, 1.0 / self.zoom, pivot, group, floor))

    def resize(self) -> None:
        self.store.set_density(self.display.scale * self.zoom)
        self.text.cache.clear()

    def prepare(self, game) -> None:
        level = game.level
        if self.level_id == level.id:
            return
        previous = self.world.id if self.world else None
        self.level_id = level.id
        self.world = world_art(level.art_set or level.world)
        if previous and previous != self.world.id:
            self.store.clear("world")
        self.store.clear("level")
        w = self.world
        self._canvas_spec(f"{w.id}.sky", w.sky, group="world", floor=0.5)
        self._canvas_spec(f"{w.id}.cave_sky", w.cave_sky, group="world", floor=0.5)
        interior = w.interior("fortress")
        if interior is not None:
            back, layer = interior
            self._canvas_spec(f"{w.id}.interior.fortress", back, group="world", floor=0.5)
            if layer is not None:
                self._canvas_spec(f"{w.id}.interior.fortress.layer", layer, group="world", floor=0.5)
        for art_id, prop in {**w.sky_extras(), **w.layer_art()}.items():
            self._canvas_spec(art_id, prop.build, prop.pivot, "world", floor=0.5)
        for name, prop in w.props().items():
            self.store.register(ArtSpec(f"{w.id}.prop.{name}", prop.build, 1.0, prop.pivot, "world"))
        self.store.register(ArtSpec("goal", lambda: common.goal(w.accent), 1.0, (21, 220), "world"))
        self._build_terrain(level)
        self._build_decor(level)
        self.rigs = {}
        for e in game.enemies:
            self._rig(e.species, game)
        self.lume = LumeAnimator()
        self.fx.items.clear()
        self.weather_seeded = False

    def preload(self, game) -> int:
        """Rasterize everything this level can show, so gameplay never stalls
        on first use (called behind the level card / loading screen)."""
        before = self.store.stats["loads"]
        w = self.world
        ids = [a.id for a in common.specs()] + [p.id for p in lume_parts()]
        ids += [f"{w.id}.sky", f"{w.id}.cave_sky", "goal"] + list(w.sky_extras()) + list(w.layer_art())
        ids += [t.art for t in self.terrain] + [d.art for d in self.decor]
        if any(d.art.endswith("windmill") for d in self.decor):
            ids.append(f"{w.id}.prop.windmill_blades")
        for s in game.platforms:
            if s.kind in ("question", "hidden"):
                ids += [self._block_art("question", s.w, s.h), self._block_art("used", s.w, s.h)]
            elif s.kind == "brick":
                ids.append(self._block_art("brick", s.w, s.h))
            elif s.kind == "pipe":
                ids.append(self._pipe_art(s.w, s.h, s.destination is not None and s.secret is not None))
            elif s.kind not in ("ground",):
                ids.append(self._platform_art(s.kind, s.w, s.h, s.style))
        for h in game.hazards:
            if h.kind == "spikes":
                ids.append(self._spikes_art(h.w))
        ids += [a for a in (f"{w.id}.interior.fortress", f"{w.id}.interior.fortress.layer") if self.store.has(a)]
        for species in {e.species for e in game.enemies}:
            rig = self._rig(species, game)
            ids += [rig.part_id(n) for n in rig.parts()]
        for form in ("big",):
            del form
        for art in ids:
            self.store.get(art)
        return self.store.stats["loads"] - before

    def _rig(self, species: str, game):
        rig = self.rigs.get(species)
        if rig is None:
            profile = game.profiles[species]
            rig = rig_for(profile.animation_set, species)
            for name, (build, pivot) in rig.parts().items():
                art_id = rig.part_id(name)
                if not self.store.has(art_id):
                    self.store.register(ArtSpec(art_id, build, rig.du, pivot, "enemies"))
            self.rigs[species] = rig
        return rig

    def _build_terrain(self, level) -> None:
        w = self.world
        self.terrain = []
        grounds = [p for p in level.platforms if p.kind in ("ground",)]
        for p in grounds:
            style = "cave" if p.style == "cave" else (p.style or "terrain")
            n = max(1, math.ceil(p.w / CHUNK))
            cw = p.w / n
            for i in range(n):
                cx0, cx1 = p.x + i * cw, p.x + (i + 1) * cw
                # a chunk loses its grass top only where another body sits flush on most of it
                cover = sum(max(0.0, min(cx1, o.x + o.w) - max(cx0, o.x)) for o in grounds
                            if o is not p and abs((o.y + o.h) - p.y) < 2)
                covered = cover > cw * 0.6
                art = f"terrain.{level.id}.{p.id}.{i}"
                seed = abs(hash((level.id, p.id, i))) % 100000
                left, right = i == 0, i == n - 1
                gx = p.x + i * cw
                # chunks overlap by 1.5 u so texture filtering never shows a seam
                aw = cw + (1.5 if not right else 0.0)
                self.store.register(
                    ArtSpec(art, (lambda st=style, aw=aw, h=p.h, sd=seed, l=left, r=right, top=not covered, gx=gx, sf=p.surface:
                                  w.terrain(st, aw, h, sd, l, r, top, gx, sf)), 1.0, (0, 0), "level")
                )
                self.terrain.append(TerrainPiece(art, gx, p.y - w.terrain_headroom, aw, p.h + w.terrain_headroom))

    def _build_decor(self, level) -> None:
        w = self.world
        self.decor = []
        props = w.props()
        main = level.areas[0]
        for d in level.decor:
            if d.prop in props:
                self.decor.append(Decor(f"{w.id}.prop.{d.prop}", d.x, d.y, d.scale, d.flip, d.layer))
        if level.decor:
            return
        rng = Rand(abs(hash(level.id)) % 99991)
        blocked = [(p.x - 30, p.x + p.w + 30) for p in level.platforms if p.kind == "pipe"]
        blocked += [(c.x - 40, c.x + 60) for c in level.checkpoints]
        blocked += [(level.exit.x - 60, level.exit.x + 180)]
        blocked += [(h.x - 20, h.x + 40) for h in level.hints]
        blocked += [(level.spawn.x - 60, level.spawn.x + 90)]
        for p in level.platforms:
            if p.kind != "ground" or p.style == "cave" or not (main.y <= p.y < main.y + main.h):
                continue
            if p.style in ("fortress",):
                continue
            for prop, dx, scale, layer in w.auto_decor(rng, p.w):
                x = p.x + dx
                if any(a <= x <= b for a, b in blocked):
                    continue
                if any(o.kind in ("brick", "question", "pipe") and o.x - 20 < x < o.x + o.w + 20 and o.y < p.y and o.y > p.y - 90
                       for o in level.platforms):
                    if layer == "back" and prop.startswith("tree"):
                        continue
                self.decor.append(Decor(f"{w.id}.prop.{prop}", x, p.y + 2, scale, rng.next() < 0.5, layer))

    # ------------------------------------------------------------------ coordinates
    def compute_view(self, game) -> tuple[float, float]:
        cam = game.camera
        z = self.zoom
        vw, vh = VIEW_WIDTH / z, VIEW_HEIGHT / z
        p = game.player
        # Zoom around the player: keep the player's relative position from the
        # (smoothed) simulation camera, so framing and look-ahead are preserved.
        px, py = p.x + p.w / 2, p.y + p.h
        x = px - (px - cam.x) * (vw / VIEW_WIDTH)
        y = py - (py - cam.y) * (vh / VIEW_HEIGHT)
        if cam.lock is not None:
            ax, ay, aw, ah = cam.lock
        else:
            area = game.level.area_at(p.x + p.w / 2, min(p.y + p.h / 2, game.level.height - 1))
            ax, ay, aw, ah = area.x, area.y, area.w, area.h
        x = max(ax, min(ax + aw - vw, x))
        y = max(ay, min(ay + ah - vh, y))
        return x, y

    def w2c(self, x: float, y: float) -> tuple[float, float]:
        vx, vy = self.view
        return (x - vx) * self.zoom, (y - vy) * self.zoom

    def visible(self, x: float, y: float, w: float, h: float, margin: float = 40) -> bool:
        vx, vy = self.view
        vw, vh = VIEW_WIDTH / self.zoom, VIEW_HEIGHT / self.zoom
        return x + w > vx - margin and x < vx + vw + margin and y + h > vy - margin and y < vy + vh + margin

    def draw_art(self, art_id: str, x: float, y: float, *, scale: float = 1.0, angle: float = 0.0, flip: bool = False,
                 alpha: float = 1.0, tint=None, additive: bool = False, w: Optional[float] = None, h: Optional[float] = None,
                 pivot: bool = True) -> None:
        """Draw world-space art with its pivot at (x, y) world units."""
        e = self.store.get(art_id)
        if e is None:
            return
        z = self.zoom
        ww = (w if w is not None else e.w * e.unit) * scale
        hh = (h if h is not None else e.h * e.unit) * scale
        px, py = (e.pivot[0] * e.unit * scale, e.pivot[1] * e.unit * scale) if pivot else (0.0, 0.0)
        if flip:
            px = ww - px
        cx, cy = self.w2c(x, y)
        self.display.draw(e.tex, cx - px * z, cy - py * z, ww * z, hh * z, angle=angle,
                          origin=(px * z, py * z) if angle else None, flip_x=flip, alpha=alpha, tint=tint, additive=additive)
        self.stats["draws"] += 1

    def draw_canvas(self, art_id: str, x: float, y: float, w: float, h: float, alpha: float = 1.0, flip: bool = False,
                    tint=None, additive: bool = False, angle: float = 0.0) -> None:
        e = self.store.get(art_id)
        if e is not None:
            self.display.draw(e.tex, x, y, w, h, alpha=alpha, flip_x=flip, tint=tint, additive=additive, angle=angle,
                              origin=(w / 2, h / 2) if angle else None)
            self.stats["draws"] += 1

    def _block_art(self, kind: str, w: float, h: float) -> str:
        art = f"{self.world.id}.block.{kind}.{w:g}x{h:g}"
        if not self.store.has(art):
            self.store.register(ArtSpec(art, lambda: self.world.block(kind, w, h), 1.0, (0, 0), "world"))
        return art

    def _platform_art(self, kind: str, w: float, h: float, style: str) -> str:
        art = f"{self.world.id}.plat.{kind}.{style}.{w:g}x{h:g}"
        if not self.store.has(art):
            self.store.register(ArtSpec(art, lambda: self.world.platform(kind, w, h, style), 1.0, (0, 0), "world"))
        return art

    def _pipe_art(self, w: float, h: float, warp: bool) -> str:
        art = f"{self.world.id}.pipe.{w:g}x{h:g}.{int(warp)}"
        if not self.store.has(art):
            self.store.register(ArtSpec(art, lambda: self.world.pipe(w, h, warp), 1.0, (0, 0), "world"))
        return art

    def _spikes_art(self, w: float) -> str:
        art = f"spikes.{w:g}"
        if not self.store.has(art):
            self.store.register(ArtSpec(art, lambda: common.spikes(w), 1.0, (0, 0), "common"))
        return art

    # ------------------------------------------------------------------ frame
    def handle_events(self, game, events) -> None:
        p = game.player
        for ev in events:
            t = ev.type
            if t == "land" and self.effects:
                self.fx.dust(p.x + p.w / 2, p.y + p.h, 7, 55)
            elif t == "jump" and self.effects:
                self.fx.dust(p.x + p.w / 2, p.y + p.h, 4, 25, up=12)
            elif t in ("coin",) and ev.x is not None:
                self.fx.sparkle(ev.x + 8, ev.y + 10, 5)
            elif t == "relic" and ev.x is not None:
                self.fx.sparkle(ev.x + 11, ev.y + 12, 12, (170, 255, 236))
            elif t in ("stomp", "kick", "wings_lost", "collapse") and ev.x is not None:
                self.fx.stars(ev.x + 14, ev.y)
                self.fx.dust(ev.x + 14, ev.y + 26, 4, 50)
            elif t in ("crash",) and ev.x is not None:
                self.fx.dust(ev.x, ev.y, 10, 90, up=70)
            elif t == "checkpoint" and ev.x is not None:
                self.fx.sparkle(ev.x + 20, ev.y - 60, 10, (255, 230, 150))
            elif t == "power":
                self.fx.sparkle(p.x + p.w / 2, p.y + p.h / 2, 12, (180, 255, 236))
            elif t == "spring" and ev.x is not None:
                self.fx.dust(ev.x, ev.y, 6, 60)

    def render(self, game, dt: float, hud: bool = True) -> None:
        self.prepare(game)
        self.time += dt
        self.stats["draws"] = 0
        d = self.display
        level = game.level
        self.view = self.compute_view(game)
        p = game.player
        area = level.area_at(p.x + p.w / 2, min(p.y + p.h / 2, level.height - 1))
        indoor = area.variant in ("cave", "fortress")
        outdoor = not indoor
        shake_x = shake_y = 0.0
        if self.effects and game.shake > 0:
            amp = min(6.0, game.shake * 26)
            shake_x, shake_y = math.sin(self.time * 83) * amp, math.cos(self.time * 97) * amp
            self.view = (self.view[0] + shake_x / self.zoom, self.view[1] + shake_y / self.zoom)
        d.clear((10, 12, 18))
        w = self.world
        if outdoor:
            self.draw_canvas(f"{w.id}.sky", 0, 0, 960, 540)
            self._clouds()
            self._layers(level)
        elif area.variant == "fortress" and self.store.has(f"{w.id}.interior.fortress"):
            self.draw_canvas(f"{w.id}.interior.fortress", 0, 0, 960, 540)
            if self.store.has(f"{w.id}.interior.fortress.layer"):
                off = (self.view[0] * self.zoom * 0.45) % 900
                for k in range(-1, 2):
                    self.draw_canvas(f"{w.id}.interior.fortress.layer", k * 900 - off, 120, 900, 420)
        else:
            self.draw_canvas(f"{w.id}.cave_sky", 0, 0, 960, 540)
        self._decor("back")
        self._terrain()
        self._platforms(game)
        self._decor("mid")
        self._landmarks(game)
        self._hazards(game, liquids=False)
        self._collectibles(game)
        self._enemies(game, dt)
        self._player(game, dt)
        self._projectiles(game)
        self._particles(game, dt)
        self._hazards(game, liquids=True)
        self._decor("front")
        darkness = game.darkness() if hasattr(game, "darkness") else 0.0
        if darkness > 0:
            self._darkness(game, darkness)
        if outdoor and self.effects:
            self._weather(dt)
        d.letterbox()
        if hud:
            self.hud(game)

    # ------------------------------------------------------------------ layers
    def _clouds(self) -> None:
        vx, vy = self.view
        clouds = [a for a in self.world.sky_extras() if ".cloud." in a]
        for i, art in enumerate(clouds * 2):
            e = self.store.get(art)
            if e is None:
                continue
            cw, ch = e.w, e.h
            speed = 4 + i * 1.7
            span = 960 + cw + 200
            x = ((i * 397 + 120 - vx * self.zoom * (0.03 + 0.01 * i) + self.time * speed) % span) - cw
            y = 30 + (i * 53) % 150 - (vy * self.zoom) * 0.02
            self.draw_canvas(art, x, y, cw * (0.8 + 0.1 * (i % 3)), ch * (0.8 + 0.1 * (i % 3)), alpha=0.95)

    def _ground_line(self, level) -> float:
        main = level.areas[0]
        tops = [p.y for p in level.platforms if p.kind == "ground" and main.y <= p.y < main.y + main.h and p.w >= 200]
        return max(set(tops), key=tops.count) if tops else main.y + main.h - 92

    def _layers(self, level) -> None:
        vx, vy = self.view
        z = self.zoom
        ground = self._ground_line(level)
        ref_vy = ground - 455 / z
        for layer in self.world.layers():
            e0 = self.store.get(layer.strips[0])
            if e0 is None:
                continue
            sh = e0.h
            offset = vx * z * layer.parallax
            bottom = (ground - ref_vy) * z + layer.baseline - (vy - ref_vy) * z * layer.vertical
            start = math.floor(offset / layer.strip_width)
            x = start * layer.strip_width - offset
            i = start
            while x < 960:
                art = layer.strips[i % len(layer.strips)]
                self.draw_canvas(art, x, bottom - sh, layer.strip_width + 0.5, sh)
                x += layer.strip_width
                i += 1

    def _terrain(self) -> None:
        for piece in self.terrain:
            if self.visible(piece.x, piece.y, piece.w, piece.h):
                self.draw_art(piece.art, piece.x, piece.y, pivot=False)

    def _decor(self, layer: str) -> None:
        for dec in self.decor:
            if dec.layer != layer or not self.visible(dec.x - 120, dec.y - 220, 240, 240):
                continue
            sway = 0.0
            if "tree" in dec.art or "bush" in dec.art:
                sway = math.sin(self.time * 1.3 + dec.x * 0.01) * 1.5
            self.draw_art(dec.art, dec.x, dec.y, scale=dec.scale, flip=dec.flip, angle=sway)
            if dec.art.endswith("windmill"):
                self.draw_art(f"{self.world.id}.prop.windmill_blades", dec.x, dec.y - 104 * dec.scale, scale=dec.scale,
                              angle=(self.time * 40) % 360)

    def _platforms(self, game) -> None:
        for s in game.platforms:
            if not s.alive or not self.visible(s.x, s.y - 20, s.w, s.h + 40):
                continue
            bump = -math.sin(max(0.0, s.bump) / 0.18 * math.pi) * 6 if s.kind in ("question", "brick", "hidden") else 0.0
            if s.kind == "ground":
                continue
            if s.kind in ("question", "hidden"):
                if s.kind == "hidden" and not s.used:
                    continue
                art = self._block_art("used" if s.used or s.kind == "hidden" else "question", s.w, s.h)
                self.draw_art(art, s.x, s.y + bump, pivot=False)
                if not s.used and self.effects:
                    glow = 0.25 + 0.2 * math.sin(self.time * 4 + s.x)
                    self.draw_art("particle.soft", s.x + s.w / 2, s.y + s.h / 2 + bump, scale=s.w / 10, alpha=glow,
                                  tint=(255, 220, 140), additive=True)
            elif s.kind == "brick":
                self.draw_art(self._block_art("brick", s.w, s.h), s.x, s.y + bump, pivot=False)
            elif s.kind == "pipe":
                self.draw_art(self._pipe_art(s.w, s.h, s.destination is not None and s.secret is not None), s.x, s.y, pivot=False)
            elif s.kind == "switch":
                if not s.active:
                    continue
                art = f"{self.world.id}.gate.{s.w:g}x{s.h:g}"
                if not self.store.has(art):
                    self.store.register(ArtSpec(art, (lambda gw=s.w, gh=s.h: self.world.gate(gw, gh)), 1.0, (0, 0), "world"))
                drop = -math.sin(min(1.0, s.bump / 0.3) * math.pi / 2) * 20 if s.bump > 0 else 0.0
                self.draw_art(art, s.x, s.y + drop, pivot=False)
            elif s.kind == "ledge":
                art = self._platform_art("ledge", s.w, s.h, s.style)
                self.draw_art(art, s.x, s.y - self.world.terrain_headroom, pivot=False)
            else:
                shake = math.sin(self.time * 60) * 1.5 if s.kind == "crumble" and s.crumble > 0 else 0.0
                art = self._platform_art(s.kind, s.w, s.h, s.style)
                self.draw_art(art, s.x + shake, s.y, pivot=False)

    def _landmarks(self, game) -> None:
        level = game.level
        for hint in level.hints:
            floor = self._floor_y(game, hint.x, hint.y)
            if floor is not None and self.visible(hint.x - 20, floor - 50, 40, 50):
                self.draw_art("sign", hint.x + 10, floor + 1)
        for cp in game.checkpoints:
            floor = self._floor_y(game, cp.x + 10, cp.y)
            if floor is not None and self.visible(cp.x - 20, floor - 120, 60, 120):
                self.draw_art("checkpoint.on" if cp.reached else "checkpoint.off", cp.x + 10, floor + 1)
                if cp.reached and self.effects:
                    self.draw_art("particle.soft", cp.x + 22, floor - 75, scale=4.2, alpha=0.45 + 0.1 * math.sin(self.time * 5),
                                  tint=(255, 220, 140), additive=True)
        ex = level.exit
        if self.visible(ex.x - 40, ex.y - 230, 160, 240):
            self.draw_art("goal", ex.x + 10, ex.y + 1)

    def _floor_y(self, game, x: float, y: Optional[float] = None) -> Optional[float]:
        """Top of the nearest ground at x below height y (or the highest one)."""
        best = None
        for s in game.index.query(x - 1, x + 1):
            if s.kind in ("ground", "ledge") and s.x <= x < s.x + s.w and s.y < game.level.height:
                if y is not None and s.y < y - 2:
                    continue
                if best is None or s.y < best:
                    best = s.y
        return best

    def _hazards(self, game, liquids: bool) -> None:
        for h in game.hazards:
            hx, hy = h.position(game.elapsed)
            if not self.visible(hx - 40, hy - 20, h.w + 80, h.h + 40):
                continue
            if h.kind in ("water", "lava", "poison"):
                if not liquids:
                    continue
                alpha = 0.86 if h.kind == "water" else 1.0
                self.draw_art(f"liquid.{h.kind}.body", hx, hy + 6, w=h.w, h=h.h + 120, pivot=False, alpha=alpha)
                strip = 64.0
                off = (self.time * (18 if h.kind == "water" else 9)) % strip
                x = hx - off
                while x < hx + h.w:
                    self.draw_art(f"liquid.{h.kind}.surface", x, hy - 2, pivot=False, alpha=alpha)
                    x += strip
                if h.kind == "lava" and self.effects:
                    self.draw_art("particle.soft", hx + h.w / 2, hy, scale=h.w / 12, alpha=0.35, tint=(255, 140, 60), additive=True)
            elif liquids:
                continue
            elif h.kind == "spikes":
                self.draw_art(self._spikes_art(h.w), hx, hy - 2, pivot=False)
            elif h.kind == "thorns":
                art = f"{self.world.id}.thorns.{h.w:g}x{h.h:g}"
                if not self.store.has(art):
                    built = self.world.hazard("thorns", h.w, h.h)
                    if built is None:
                        art = self._spikes_art(h.w)
                    else:
                        self.store.register(ArtSpec(art, (lambda hw=h.w, hh=h.h: self.world.hazard("thorns", hw, hh)), 1.0, (0, 0), "world"))
                self.draw_art(art, hx, hy - 4, pivot=False)
            elif h.kind == "moving":
                cx, cy = hx + h.w / 2, hy + h.h / 2
                if self.effects:
                    self.draw_art("particle.soft", cx, cy, scale=5.0, alpha=0.5, tint=(255, 150, 60), additive=True)
                self.draw_art("flame_orb", cx, cy, scale=h.w / 26, angle=(self.time * 200) % 360)

    def _collectibles(self, game) -> None:
        t = self.time
        for c in game.coins:
            if c.collected or not self.visible(c.x, c.y, c.w, c.h):
                continue
            if c.special:
                bob = math.sin(t * 2.6 + c.x) * 2.5
                if self.effects:
                    self.draw_art("particle.soft", c.x + c.w / 2, c.y + c.h / 2 + bob, scale=4.0, alpha=0.5, tint=(120, 255, 230), additive=True)
                self.draw_art("relic", c.x + c.w / 2, c.y + c.h / 2 + bob, scale=0.62)
                a = t * 2.2 + c.x
                self.draw_art("particle.sparkle", c.x + c.w / 2 + math.cos(a) * 16, c.y + c.h / 2 + math.sin(a) * 12 + bob,
                              scale=0.5, angle=(t * 180) % 360, additive=True)
            else:
                frame = int(t * 12 + c.x / 37) % 16
                frame = frame if frame < 8 else 15 - frame
                self.draw_art(f"coin.{frame}", c.x + c.w / 2, c.y + c.h / 2 + math.sin(t * 2 + c.x / 90) * 1.5, scale=0.86)
        for item in game.items:
            if item.alive and self.visible(item.x, item.y, item.w, item.h):
                if self.effects:
                    self.draw_art("particle.soft", item.x + 12, item.y + 12, scale=3.4, alpha=0.4, tint=(255, 240, 180), additive=True)
                angle = math.sin(t * 6) * 8 if item.kind == "star" else 0.0
                self.draw_art(f"item.{item.kind}", item.x + item.w / 2, item.y + item.h / 2, scale=0.95, angle=angle)

    def _shadow(self, game, x: float, feet: float, width: float) -> None:
        floor = None
        for s in game.index.query(x - 1, x + 1):
            if s.alive and s.kind not in ("hidden",) and s.x <= x < s.x + s.w and s.y >= feet - 2:
                if floor is None or s.y < floor:
                    floor = s.y
        if floor is None or floor - feet > 160:
            return
        k = max(0.25, 1 - (floor - feet) / 160)
        self.draw_art("particle.soft", x, floor, scale=width / 14 * k, alpha=0.35 * k, tint=(30, 24, 40), h=4.0, w=16.0)

    def _enemies(self, game, dt: float) -> None:
        for e in game.enemies:
            if not (e.alive or e.defeated > 0) or not self.visible(e.x - 40, e.y - 60, e.w + 80, e.h + 80):
                continue
            if not e.alive and e.defeated <= 0:
                continue
            rig = self._rig(e.species, game)
            if e.alive:
                self._shadow(game, e.x + e.w / 2, e.y + e.h, e.w * 1.1)
            cmds = rig.commands(e, game.elapsed + e.origin_x * 0.01)
            drawer = RigDrawer(self.store.rig_entry, self.w2c, self.zoom)
            alpha = 1.0 if e.alive else max(0.0, min(1.0, e.defeated / 0.25))
            drawer.draw(self.display, cmds, e.x + e.w / 2, e.y + e.h, rig.du, e.facing, alpha=alpha)

    def _player(self, game, dt: float) -> None:
        p = game.player
        anim = p.animation
        if game.status == "complete":
            anim = "win"
        elif game.status == "dead":
            anim = "dead"
        if game.status == "playing" and p.damage_blink > 0 and p.star <= 0 and int(self.time * 18) % 2 == 0 and anim != "hurt":
            alpha = 0.4
        else:
            alpha = 1.0
        form_override = None
        if anim == "transform":
            form_override = "big" if int(self.time * 16) % 2 == 0 else "small"
        x, feet = p.x + p.w / 2, p.y + p.h
        if game.status == "dead":
            t = 1.1 - game.transition
            feet = p.y + p.h - 260 * t + 600 * t * t
        if game.status != "dead":
            self._shadow(game, x, feet, 26)
        cmds, du = self.lume.commands(p, anim, dt, form_override=form_override)
        if p.skid > 0 and self.effects and int(self.time * 30) % 3 == 0:
            self.fx.dust(x + p.facing * 10, feet, 1, 20, up=10)
        if anim == "run" and p.grounded and self.effects and int(self.time * 12) % 4 == 0:
            self.fx.dust(x - p.facing * 8, feet, 1, 10, up=6)
        tint = None
        if p.star > 0:
            hue = int(self.time * 8) % 4
            tint = [(255, 240, 170), (190, 255, 236), (255, 200, 240), (210, 230, 255)][hue]
            if self.effects:
                self.draw_art("particle.soft", x, feet - 20, scale=5.0, alpha=0.45, tint=tint, additive=True)
        drawer = RigDrawer(self.store.rig_entry, self.w2c, self.zoom)
        drawer.draw(self.display, cmds, x, feet, du, p.facing, alpha=alpha, tint=tint)
        if p.power == "fire" and self.effects:
            self.draw_art("particle.soft", x + p.facing * 10, feet - 20, scale=1.6, alpha=0.35, tint=(255, 190, 90), additive=True)

    def _projectiles(self, game) -> None:
        for s in game.projectiles:
            if not s.alive or not self.visible(s.x, s.y, s.w, s.h):
                continue
            art = f"shot.{s.kind}" if self.store.has(f"shot.{s.kind}") else "shot.orb"
            if self.effects and s.kind in ("fireball", "guardian_orb", "orb"):
                self.draw_art("particle.soft", s.x + s.w / 2, s.y + s.h / 2, scale=s.w / 5, alpha=0.5,
                              tint=(255, 170, 80) if s.kind == "fireball" else (200, 120, 255), additive=True)
            self.draw_art(art, s.x + s.w / 2, s.y + s.h / 2, scale=max(0.5, s.w / 14), angle=(s.age * 600) % 360)

    def _particles(self, game, dt: float) -> None:
        if not self.effects:
            return
        for v in game.particles:
            alpha = max(0.0, min(1.0, v.life * 3))
            art = {"debris": "particle.debris", "glint": "particle.sparkle"}.get(v.kind, "particle.soft")
            self.draw_art(art, v.x, v.y, scale=max(0.25, v.size / 6), alpha=alpha, tint=_hex(v.color), additive=v.kind != "debris")
        self.fx.update(dt)
        for f in self.fx.items:
            if f.screen:
                continue
            k = f.life / f.max_life
            self.draw_art(f.art, f.x, f.y, scale=f.size / 12, angle=f.rot, alpha=f.alpha * min(1.0, k * 1.6), tint=f.tint, additive=f.additive)

    def _weather(self, dt: float) -> None:
        wthr = self.world.weather()
        if wthr.kind == "none" or wthr.density <= 0:
            return
        target = int(40 * wthr.density) if self.quality != "low" else int(14 * wthr.density)
        current = [f for f in self.fx.items if f.screen]
        r = self.fx.rand
        arts = [f"particle.{a}" for a in wthr.colors] or ["particle.soft"]
        while len(current) < target:
            kind = wthr.kind
            f = Fx(r.choice(arts), r.uniform(-40, 1000), r.uniform(-40, 540) if not self.weather_seeded else -20,
                   wthr.wind + r.uniform(-15, 15), r.uniform(18, 45) if kind != "embers" else -r.uniform(15, 40),
                   r.uniform(8, 14), 14.0, r.uniform(4, 8), rot=r.uniform(0, 360), vrot=r.uniform(-90, 90), screen=True,
                   tint={"snow": (255, 255, 255), "sand": (240, 210, 150), "embers": (255, 150, 70), "spores": (170, 255, 220)}
                   .get(kind, (255, 255, 255)), alpha=0.8, additive=kind in ("embers", "spores"))
            if kind == "embers":
                f.y = 560
            self.fx.items.append(f)
            current.append(f)
        self.weather_seeded = True
        for f in current:
            f.x += math.sin(self.time * 1.7 + f.rot * 0.05) * 12 * dt
            if f.x > 1010:
                f.x = -30
            if f.x < -40:
                f.x = 990
            if f.y > 560 or f.y < -60:
                f.life = 0
            k = min(1.0, f.life / 2)
            self.draw_canvas(f.art, f.x, f.y, f.size, f.size, alpha=f.alpha * k, tint=f.tint, additive=f.additive, angle=f.rot)

    def _darkness(self, game, level: float) -> None:
        """Dark zones: everything is dimmed except the halo of Lume's lantern
        (same radius the light-shy shadows react to). One smooth gradient
        texture, large enough to cover the screen from any player position."""
        if getattr(self, "_halo_tex", None) is None:
            from .raster import rasterize

            halo = Svg(2048, 2048)
            halo.rect(0, 0, 2048, 2048, fill=halo.radial(1024, 1024, 1024, [
                (0, "#05060c", 0.0), (0.05, "#05060c", 0.0), (0.075, "#05060c", 0.55), (0.1, "#05060c", 1.0), (1, "#05060c", 1.0)]))
            self._halo_tex = self.display.texture(rasterize(halo, 0.5))  # smooth gradient: fixed 1024 px
        p = game.player
        cx, cy = self.w2c(p.x + p.w / 2, p.y + p.h / 2)
        radius = game.lantern_radius() * self.zoom * 1.6  # canvas units where darkness is complete
        size = 2048 * radius / 204.8
        self.display.draw(self._halo_tex, cx - size / 2, cy - size / 2, size, size, alpha=min(1.0, level))
        self.draw_art("particle.soft", p.x + p.w / 2 + p.facing * 9, p.y + p.h * 0.62, scale=2.4, alpha=0.6,
                      tint=(255, 214, 140), additive=True)

    # ------------------------------------------------------------------ HUD
    def hud(self, game) -> None:
        d = self.display
        t = self.text
        self._panel(14, 12, 380, 46)
        e = self.store.get("coin.0")
        if e is not None:
            d.draw(e.tex, 28, 21, 22, 26)
        t.draw(f"{game.coins_total:03d}", 56, 20, 22, (255, 240, 200), "display", outline=(30, 20, 30))
        relics = [c for c in game.coins if c.special]
        x = 124
        rel = self.store.get("relic")
        for c in relics:
            if rel is not None:
                d.draw(rel.tex, x, 17, 26, 29, alpha=1.0 if c.collected else 0.28)
            x += 30
        head = self.store.get("lume.head")
        hat = self.store.get("lume.hat.normal")
        if head is not None and hat is not None:
            d.draw(head.tex, 300, 22, head.w * 0.62, head.h * 0.62)
            d.draw(hat.tex, 294, 10, hat.w * 0.62, hat.h * 0.62)
        t.draw(f"× {game.lives}", 336, 20, 22, (255, 255, 255), "display", outline=(30, 20, 30))
        self._panel(686, 12, 260, 46)
        t.draw(f"{game.score:07d}", 700, 20, 22, (255, 255, 255), "display", outline=(30, 20, 30))
        t.draw(f"{int(game.time):03d}", 932, 20, 22, (255, 220, 150) if game.time > 60 else (255, 120, 100), "display",
               align="right", outline=(30, 20, 30))

    def _panel(self, x: float, y: float, w: float, h: float) -> None:
        art = f"ui.panel.{w:g}x{h:g}"
        if not self.store.has(art):
            def build(w=w, h=h):
                from .svg import rounded_rect_path
                s = Svg(w, h)
                s.path(rounded_rect_path(1, 1, w - 2, h - 2, h / 2.6), fill=s.linear(0, 0, 0, h, [(0, "#2a3a58", 0.78), (1, "#141c2c", 0.82)]),
                       stroke="#ffffff", width=1.4, fill_opacity=1.0)
                return s
            self._canvas_spec(art, build, group="ui")
        self.draw_canvas(art, x, y, w, h)
