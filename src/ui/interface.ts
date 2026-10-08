import type { Game } from "../core/game";
import type { SaveData, Settings } from "../systems/save";
import { LEVELS, THEMES } from "../data/levels";

export interface Handlers {
  play(index: number): void;
  resume(): void;
  restart(): void;
  menu(): void;
  updateSettings(settings: Settings): void;
  reset(): void;
}

type Screen =
  | "menu"
  | "map"
  | "controls"
  | "settings"
  | "credits"
  | "pause"
  | "complete"
  | "gameover";
const icons: Record<string, string> = {
  arrow: '<path d="M5 12h14m-6-6 6 6-6 6"/>',
  play: '<path d="m9 5 10 7-10 7z"/>',
  map: '<path d="m3 6 6-3 6 3 6-3v15l-6 3-6-3-6 3zM9 3v15m6-12v15"/>',
  keys: '<rect x="3" y="6" width="18" height="12" rx="2"/><path d="M6 10h1m3 0h1m3 0h1m3 0h1M6 14h1m3 0h7"/>',
  settings: '<path d="M5 4v16m7-16v16m7-16v16M2 8h6m1 8h6m1-9h6"/>',
  sound: '<path d="m11 5-5 4H3v6h3l5 4zM15 8c3 2 3 6 0 8m3-11c5 4 5 10 0 14"/>',
  mute: '<path d="m11 5-5 4H3v6h3l5 4zM16 9l5 6m0-6-5 6"/>',
  full: '<path d="M8 3H3v5m13-5h5v5M3 16v5h5m13-5v5h-5"/>',
  back: '<path d="M19 12H5m6-6-6 6 6 6"/>',
  lock: '<rect x="6" y="10" width="12" height="10" rx="2"/><path d="M9 10V7a3 3 0 0 1 6 0v3m-3 4v2"/>',
  check: '<path d="m5 12 4 4L19 6"/>',
  star: '<path d="m12 3 2.7 5.5 6.1.9-4.4 4.3 1 6.1-5.4-2.9-5.4 2.9 1-6.1L3.2 9.4l6.1-.9z"/>',
  heart:
    '<path d="M20 5c-3-3-6-1-8 1-2-2-5-4-8-1-5 5 2 10 8 15 6-5 13-10 8-15z"/>',
  coin: '<ellipse cx="12" cy="12" rx="7" ry="9"/><path d="M12 7v10"/>',
  pause: '<path d="M8 5v14m8-14v14"/>',
  trophy:
    '<path d="M8 3h8v7c0 6-8 6-8 0zm0 3H4v3c0 3 2 4 5 4m7-7h4v3c0 3-2 4-5 4m-3 2v5m-4 1h8"/>',
  info: '<circle cx="12" cy="12" r="9"/><path d="M12 11v6m0-10v.1"/>',
};
const icon = (name: string) =>
  `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${icons[name] ?? icons.star}</svg>`;
const escape = (value: string) =>
  value.replace(
    /[&<>"']/g,
    (char) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        char
      ]!,
  );
const score = (value: number) =>
  Math.max(0, Math.round(value)).toLocaleString("pt-BR");
const achievementName = (id: string) =>
  ({
    "first-clear": "Primeira luz",
    "all-clear": "As cinco fronteiras",
    "relic-hunter": "Caçador de relíquias",
    "secret-path": "Caminho secreto",
    "world-1": "Guardião do vale",
    "world-2": "Além das dunas",
    "world-3": "Coração de cristal",
    "world-4": "Luz na floresta",
    "world-5": "A última chama",
  })[id] ?? id.replace(/[-_]/g, " ");

/** Menus and live HUD are DOM-based; all gameplay remains in the canvas engine. */
export class Interface {
  private save: SaveData;
  private screen: Screen | null = null;
  private game?: Game;
  private settingsReturn: "menu" | "pause" = "menu";
  private readonly app: HTMLElement;
  private readonly hud: HTMLElement;
  private readonly notice: HTMLElement;
  private toastTimer = 0;
  private mutedMusic = 0.45;
  private mutedSfx = 0.75;

  constructor(
    private readonly root: HTMLElement,
    save: SaveData,
    private readonly handlers: Handlers,
  ) {
    this.save = save;
    this.app = root.closest<HTMLElement>("#app") ?? root.parentElement!;
    this.app.classList.add("lume-app");
    const canvas = this.app.querySelector<HTMLCanvasElement>("#game")!;
    const stage = document.createElement("div");
    stage.className = "stage";
    stage.innerHTML = `<div class="stage-top"><span class="stage-caption"><i class="status-light"></i> LUME <span>/</span> AS CINCO FRONTEIRAS</span><div class="stage-actions"><button type="button" data-shell="sound" aria-label="Desligar áudio" title="Ativar ou desativar áudio">${icon("sound")}</button><button type="button" data-shell="fullscreen" aria-label="Tela cheia" title="Tela cheia">${icon("full")}</button></div></div><div class="stage-display"></div>`;
    this.app.insertBefore(stage, canvas);
    const display = stage.querySelector<HTMLElement>(".stage-display")!;
    display.append(canvas, root);
    root.className = "game-interface";
    root.setAttribute("aria-live", "off");
    this.hud = document.createElement("div");
    this.hud.className = "game-hud";
    this.hud.hidden = true;
    this.hud.innerHTML = `<div class="hud-main"><div class="hud-player"><span class="pixel-mark" aria-hidden="true"></span><div><b>LUME</b><span data-hud="power">Explorador</span></div></div><div class="hud-stat">${icon("heart")}<span><small>VIDAS</small><b data-hud="lives">5</b></span></div><div class="hud-stat"><span><small>PONTOS</small><b data-hud="score">0</b></span></div><div class="hud-stat">${icon("coin")}<span><small>MOEDAS</small><b data-hud="coins">0</b></span></div><div class="hud-stat hud-stage"><span><small>MUNDO / FASE</small><b data-hud="stage">1 — 1</b></span></div><div class="hud-stat hud-time"><span><small>TEMPO</small><b data-hud="time">300</b></span></div><button type="button" class="hud-pause" aria-label="Pausar jogo" title="Pausar (Esc)">${icon("pause")}</button></div><div class="boss-hud" hidden><span>GUARDIÃO</span><div class="boss-track"><i></i></div><b></b></div>`;
    display.append(this.hud);
    this.hud.querySelector("button")!.addEventListener("click", () => {
      if (this.game?.status === "playing") {
        this.game.pause();
        this.show("pause", this.game);
      }
    });
    const header = document.createElement("header");
    header.className = "site-header";
    header.innerHTML = `<button type="button" class="brand" data-shell="menu" aria-label="Lume, menu principal"><span class="brand-icon" aria-hidden="true">✦</span><span>LUME<span class="brand-sub">AS CINCO FRONTEIRAS</span></span></button><nav aria-label="Navegação principal"><button type="button" data-shell="menu" class="nav-active">A aventura</button><button type="button" data-shell="controls">Como jogar</button><button type="button" data-shell="settings">Ajustes</button></nav><button type="button" class="progress-pill" data-shell="map">${icon("map")}<span>Seu progresso <b data-progress-count>0 / 15</b></span></button>`;
    this.app.prepend(header);
    const intro = document.createElement("div");
    intro.className = "page-intro";
    intro.innerHTML = `<div><span class="eyebrow">UM CLÁSSICO, UMA NOVA LUZ</span><h2>Pequenos saltos.<br>Grandes aventuras.</h2></div><p>Um mundo de caminhos secretos,<br>pequenas descobertas e grandes desafios.<br><span>Sua próxima aventura começa aqui.</span></p><span class="intro-stamp" aria-hidden="true">✦<small>FEITO PARA<br>EXPLORAR</small></span>`;
    this.app.insertBefore(intro, stage);
    const mobileMenu = document.createElement("nav");
    mobileMenu.className = "mobile-menu-nav";
    mobileMenu.setAttribute("aria-label", "Menu da aventura no celular");
    mobileMenu.innerHTML = `<button type="button" data-shell="map">${icon("map")}Mundos</button><button type="button" data-shell="controls">${icon("keys")}Controles</button><button type="button" data-shell="settings">${icon("settings")}Ajustes</button><button type="button" data-shell="credits">${icon("info")}Créditos</button>`;
    this.app.insertBefore(mobileMenu, stage.nextSibling);
    const footer = document.createElement("footer");
    footer.className = "site-footer";
    footer.innerHTML = `<div class="quick-controls"><span class="footer-label">PRONTO PARA AVENTURAR?</span><div><kbd>←</kbd><kbd>→</kbd><span>Mover</span><kbd>ESPAÇO</kbd><span>Pular</span><kbd>SHIFT</kbd><span>Correr</span><kbd>ESC</kbd><span>Pausar</span></div></div><div class="journey-summary"><span class="footer-label">CADA DESCOBERTA CONTA</span><div><span>${icon("check")} <b data-completed>0</b> / 15 fases</span><span>${icon("star")} <b data-relics>0</b> / 15 relíquias</span></div></div>`;
    this.app.append(footer);
    const colophon = document.createElement("div");
    colophon.className = "colophon";
    colophon.innerHTML =
      '<span>Uma aventura original. Um espírito clássico.</span><button type="button" data-shell="credits">Créditos &amp; licenças <span aria-hidden="true">↗</span></button><span>DESENVOLVIDO COM CURIOSIDADE ✦</span>';
    this.app.append(colophon);
    this.notice = document.createElement("div");
    this.notice.className = "toast";
    this.notice.setAttribute("role", "status");
    this.notice.hidden = true;
    this.app.append(this.notice);
    this.app.addEventListener("click", (event) => {
      const button = (event.target as Element).closest<HTMLButtonElement>(
        "[data-shell]",
      );
      if (!button) return;
      const action = button.dataset.shell;
      if (action === "fullscreen") {
        this.fullscreen();
        return;
      }
      if (action === "sound") {
        this.toggleSound();
        return;
      }
      this.handlers.menu();
      this.show(action as Screen);
    });
    this.root.addEventListener("click", (event) => {
      const button = (event.target as Element).closest<HTMLButtonElement>(
        "button[data-action]",
      );
      if (button && !button.disabled)
        this.action(button.dataset.action!, button.dataset.level);
    });
    this.root.addEventListener("input", (event) => {
      const input = event.target as HTMLInputElement;
      const name = input.dataset.setting as keyof Settings | undefined;
      if (!name) return;
      const next = {
        ...this.save.settings,
        [name]:
          input.type === "checkbox" ? input.checked : Number(input.value) / 100,
      };
      this.save.settings = next;
      this.handlers.updateSettings(next);
      const output = this.root.querySelector<HTMLOutputElement>(
        `output[for="setting-${name}"]`,
      );
      if (output) output.value = `${input.value}%`;
      this.paintProgress();
    });
    this.paintProgress();
    this.show("menu");
  }

  setSave(save: SaveData): void {
    this.save = save;
    this.paintProgress();
  }

  show(screen: Screen, game?: Game): void {
    this.screen = screen;
    this.game = game;
    if (screen === "settings")
      this.settingsReturn = game?.status === "paused" ? "pause" : "menu";
    this.app.dataset.view = screen;
    this.root.hidden = false;
    this.hud.hidden = true;
    this.root.setAttribute(
      "aria-label",
      {
        menu: "Menu principal",
        map: "Mapa dos mundos",
        controls: "Controles",
        settings: "Configurações",
        credits: "Créditos",
        pause: "Jogo pausado",
        complete: "Fase concluída",
        gameover: "Fim de jogo",
      }[screen],
    );
    this.root.innerHTML =
      screen === "menu" ? this.menu() : this.panel(screen, game);
    this.app
      .querySelectorAll(
        '[data-shell="menu"], [data-shell="controls"], [data-shell="settings"]',
      )
      .forEach((button) => {
        button.classList.toggle(
          "nav-active",
          (button as HTMLElement).dataset.shell === screen,
        );
      });
    if (screen !== "menu")
      requestAnimationFrame(() =>
        this.root
          .querySelector<HTMLButtonElement>(
            ".panel-close, button:not(:disabled)",
          )
          ?.focus({ preventScroll: true }),
      );
  }

  hide(): void {
    this.screen = null;
    this.root.hidden = true;
    this.root.innerHTML = "";
    this.hud.hidden = false;
    this.app.dataset.view = "playing";
  }

  update(game: Game): void {
    this.game = game;
    if (this.screen !== null) return;
    const values: Record<string, string> = {
      lives: String(game.lives),
      score: score(game.score),
      coins: String(game.coinsTotal),
      stage: `${game.level.world} — ${game.level.stage}`,
      time: String(Math.ceil(game.time)),
      power:
        game.player.star > 0
          ? `Invencível · ${Math.ceil(game.player.star)}s`
          : { small: "Explorador", grown: "Crescimento", fire: "Flor de fogo" }[
              game.player.power
            ],
    };
    for (const [name, value] of Object.entries(values)) {
      const node = this.hud.querySelector<HTMLElement>(`[data-hud="${name}"]`)!;
      if (node.textContent !== value) node.textContent = value;
    }
    this.hud
      .querySelector(".hud-time")!
      .classList.toggle("time-low", game.time <= 30);
    const boss = game.enemies.find(
      (enemy) =>
        enemy.kind === "boss" &&
        enemy.alive &&
        Math.abs(enemy.x - game.player.x) < 850,
    );
    const bar = this.hud.querySelector<HTMLElement>(".boss-hud")!;
    bar.hidden = !boss;
    if (boss) {
      bar.querySelector<HTMLElement>("i")!.style.width =
        `${(100 * boss.health) / (boss.hp ?? 4)}%`;
      bar.querySelector("b")!.textContent = `${boss.health} / ${boss.hp ?? 4}`;
    }
  }

  toast(message: string): void {
    clearTimeout(this.toastTimer);
    this.notice.textContent = message;
    this.notice.hidden = false;
    this.toastTimer = window.setTimeout(() => {
      this.notice.hidden = true;
    }, 4200);
  }

  private paintProgress(): void {
    this.app.querySelectorAll("[data-progress-count]").forEach((node) => {
      node.textContent = `${this.save.completed.length} / 15`;
    });
    this.app.querySelectorAll("[data-completed]").forEach((node) => {
      node.textContent = String(this.save.completed.length);
    });
    this.app.querySelectorAll("[data-relics]").forEach((node) => {
      node.textContent = String(this.save.relics.length);
    });
    const muted =
      this.save.settings.music === 0 && this.save.settings.sfx === 0;
    const sound = this.app.querySelector<HTMLButtonElement>(
      '[data-shell="sound"]',
    );
    if (sound) {
      sound.innerHTML = icon(muted ? "mute" : "sound");
      sound.setAttribute(
        "aria-label",
        muted ? "Ativar áudio" : "Desligar áudio",
      );
      sound.setAttribute("aria-pressed", String(!muted));
    }
  }

  private menu(): string {
    const level = LEVELS[this.save.unlocked];
    return `<div class="menu-scene"><div class="hero-copy"><span class="hero-eyebrow"><i></i> AVENTURA DE PLATAFORMA 2D</span><h1>LUME<span class="title-star" aria-hidden="true">✦</span></h1><span class="hero-subtitle">AS CINCO FRONTEIRAS</span><p>Há uma luz além de cada horizonte.<br>Salte, explore e encontre a sua.</p><button type="button" class="button button-primary play-button" data-action="play">${icon("play")}<span>JOGAR<small>${this.save.completed.length ? `Continuar · ${level.world}-${level.stage}` : "Sua jornada começa aqui"}</small></span>${icon("arrow")}</button><div class="menu-links"><button type="button" data-action="map">${icon("map")} Selecionar mundo</button><button type="button" data-action="controls">${icon("keys")} Controles</button><button type="button" data-action="settings">${icon("settings")} Configurações</button><button type="button" data-action="credits">${icon("info")} Créditos</button></div><span class="save-note"><i></i> Seu progresso é salvo neste navegador.</span></div><div class="scene-label"><span>SEU PRIMEIRO DESTINO</span><b>O Reino Verde</b><small>Entre colinas, canais e caminhos secretos.</small></div><div class="scene-worlds" aria-label="Cinco mundos"><i class="active"></i><i></i><i></i><i></i><i></i><span>01 / 05</span></div></div>`;
  }

  private panel(screen: Exclude<Screen, "menu">, game?: Game): string {
    const titles = {
      map: "Escolha seu horizonte.",
      controls: "Um salto de cada vez.",
      settings: "Do seu jeito.",
      credits: "Uma nova luz.",
      pause: "Respire. A aventura espera.",
      complete:
        game?.levelIndex === 14
          ? "Você iluminou as cinco fronteiras!"
          : "Mais um horizonte alcançado!",
      gameover: "Toda aventura tem recomeços.",
    };
    const labels = {
      map: "MAPA DA AVENTURA",
      controls: "CONTROLES",
      settings: "CONFIGURAÇÕES",
      credits: "CRÉDITOS & LICENÇAS",
      pause: "JOGO PAUSADO",
      complete: "FASE CONCLUÍDA",
      gameover: "FIM DE JOGO",
    };
    const isGame =
      screen === "pause" || screen === "complete" || screen === "gameover";
    let content = "";
    if (screen === "map") content = this.map();
    if (screen === "controls") content = this.controls();
    if (screen === "settings") content = this.settings();
    if (screen === "credits")
      content = `<div class="credits-content"><div class="credits-emblem" aria-hidden="true">✦</div><h3>Lume · As Cinco Fronteiras</h3><p>Uma aventura original de plataforma, feita para celebrar a exploração e o prazer de um salto preciso.</p><div class="credits-grid"><div><span>ARTE & PERSONAGENS</span><p>Pixel art original desenhada no Canvas. Cinco mundos, quinze caminhos e uma identidade própria.</p></div><div><span>MÚSICA & EFEITOS</span><p>Trilhas e efeitos originais sintetizados com Web Audio, sem arquivos de áudio proprietários.</p></div></div><p class="credits-license">Código e recursos originais sob licença MIT.<br>Projeto independente, não oficial e sem afiliação com a Nintendo. Super Mario Bros. pertence aos seus respectivos titulares.</p></div>`;
    if (screen === "pause")
      content = `<p class="state-description">${escape(game?.level.name ?? "Sua jornada")} · Mundo ${game?.level.world ?? 1}, fase ${game?.level.stage ?? 1}</p><div class="state-buttons"><button class="button button-primary" data-action="resume">${icon("play")} Continuar ${icon("arrow")}</button><button class="button button-secondary" data-action="restart">Reiniciar fase</button><button class="button button-secondary" data-action="pause-settings">Configurações</button><button class="button button-text" data-action="menu">Voltar ao menu</button></div><p class="state-footnote">Pressione <kbd>ESC</kbd> para continuar.</p>`;
    if (screen === "gameover")
      content = `<p class="state-description">A luz continua aqui. Tente uma nova rota.</p><div class="result-stats"><div><span>PONTUAÇÃO</span><b>${score(game?.score ?? 0)}</b></div><div><span>MOEDAS</span><b>${game?.coinsTotal ?? 0}</b></div></div><div class="state-buttons"><button class="button button-primary" data-action="restart">${icon("play")} Tentar novamente ${icon("arrow")}</button><button class="button button-text" data-action="menu">Voltar ao menu</button></div>`;
    if (screen === "complete")
      content = `<p class="state-description">${escape(game?.level.name ?? "")}${game?.levelIndex === 14 ? "<br>A última chama está acesa. A jornada é sua." : "<br>Seu próximo caminho já está desbloqueado."}</p><div class="result-stats"><div><span>PONTUAÇÃO</span><b>${score(game?.score ?? 0)}</b></div><div><span>MOEDAS</span><b>${game?.coinsTotal ?? 0}</b></div><div><span>RELÍQUIA</span><b class="result-relic">${game?.foundRelic ? "✦ Encontrada" : "A explorar"}</b></div></div><div class="state-buttons"><button class="button button-primary" data-action="next">${icon(game?.levelIndex === 14 ? "map" : "play")}${game?.levelIndex === 14 ? "Explorar o mapa" : "Próxima fase"}${icon("arrow")}</button><button class="button button-secondary" data-action="map">Mapa dos mundos</button><button class="button button-text" data-action="menu">Voltar ao menu</button></div>`;
    return `<div class="panel-backdrop"><section class="panel panel-${screen}${isGame ? " state-panel" : ""}" aria-labelledby="panel-title"><div class="panel-heading"><div><span class="eyebrow">${labels[screen]}</span><h2 id="panel-title">${titles[screen]}</h2></div>${isGame ? `<span class="state-icon">${icon(screen === "complete" ? "trophy" : screen === "pause" ? "pause" : "heart")}</span>` : `<button class="panel-close" type="button" data-action="back" aria-label="${this.settingsReturn === "pause" && screen === "settings" ? "Voltar à pausa" : "Voltar ao menu"}">${icon("back")}<span>Voltar</span></button>`}</div>${content}</section></div>`;
  }

  private map(): string {
    const progress = Math.round(
      (this.save.completed.length / LEVELS.length) * 100,
    );
    return `<div class="map-summary"><span><b>${progress}%</b> da jornada</span><div class="progress-track" role="progressbar" aria-label="Progresso da campanha" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${progress}"><i style="width:${progress}%"></i></div><span>${icon("star")} ${this.save.relics.length} / 15 relíquias</span></div><div class="world-grid">${THEMES.map(
      (theme, world) =>
        `<section class="world-card" style="--world-color:${theme.near};--world-sky:${theme.sky};--world-accent:${theme.accent}"><div class="world-art"><i></i><span>0${world + 1}</span>${icon(world * 3 > this.save.unlocked ? "lock" : "star")}</div><h3>${escape(theme.name)}</h3><p>${escape(theme.subtitle)}</p><div class="stage-nodes">${LEVELS.slice(
          world * 3,
          world * 3 + 3,
        )
          .map((level, stage) => {
            const index = world * 3 + stage,
              unlocked = index <= this.save.unlocked,
              completed = this.save.completed.includes(level.id),
              relic = this.save.relics.includes(level.id);
            return `<button type="button" class="stage-node${completed ? " cleared" : ""}${index === this.save.unlocked && !completed ? " current" : ""}" data-action="level" data-level="${index}" ${unlocked ? "" : "disabled"} aria-label="${level.world}-${level.stage}: ${escape(level.name)}. ${unlocked ? (completed ? "Concluída" : "Disponível") : "Bloqueada"}. ${relic ? "Relíquia encontrada." : ""} Recorde: ${score(this.save.records[level.id] ?? 0)}"><span class="node-number">${unlocked ? (completed ? icon("check") : `${level.world}-${level.stage}`) : icon("lock")}</span><span class="node-title">${escape(level.name)}<small>${this.save.records[level.id] ? `${score(this.save.records[level.id])} pts` : unlocked ? (index === this.save.unlocked ? "Próximo destino" : "Explore de novo") : "Complete a anterior"}</small></span><span class="node-relic${relic ? " found" : ""}" title="${relic ? "Relíquia encontrada" : "Relíquia a encontrar"}">✦</span></button>`;
          })
          .join("")}</div></section>`,
    ).join(
      "",
    )}</div><div class="map-achievements"><span>${icon("trophy")} CONQUISTAS <b>${this.save.achievements.length} / 9</b></span><div>${this.save.achievements.length ? this.save.achievements.map((id) => `<span class="achievement">${icon("check")}${escape(achievementName(id))}</span>`).join("") : "<p>Sua primeira conquista espera no fim da primeira fase.</p>"}</div></div>`;
  }

  private controls(): string {
    return `<div class="controls-grid"><section><h3>${icon("keys")} Teclado</h3><dl><div><dt>Mover</dt><dd><kbd>A</kbd><kbd>D</kbd> ou <kbd>←</kbd><kbd>→</kbd></dd></div><div><dt>Pular</dt><dd><kbd>ESPAÇO</kbd> / <kbd>W</kbd> / <kbd>↑</kbd></dd></div><div><dt>Correr</dt><dd><kbd>SHIFT</kbd></dd></div><div><dt>Habilidade</dt><dd><kbd>J</kbd> com flor de fogo</dd></div><div><dt>Entrar em canos</dt><dd><kbd>S</kbd> / <kbd>↓</kbd></dd></div><div><dt>Pausar</dt><dd><kbd>ESC</kbd></dd></div></dl></section><section><h3>${icon("play")} Gamepad & celular</h3><dl><div><dt>Mover</dt><dd>Direcional / analógico esquerdo</dd></div><div><dt>Pular</dt><dd>Botão A / ✕</dd></div><div><dt>Correr</dt><dd>Botão X / □ ou gatilho direito</dd></div><div><dt>Habilidade</dt><dd>Botão B / ○</dd></div><div><dt>Pausar</dt><dd>Start / Options</dd></div></dl><p class="mobile-help">No celular, use os botões na tela. Ative-os também em <button data-action="settings" type="button">Configurações</button>. A orientação horizontal dá mais espaço para explorar.</p></section></div><div class="control-tip">${icon("star")}<p><b>O segredo está no salto.</b> Segure para saltar mais alto e solte para um salto curto. Corra antes de um vão. Sobre um cano com passagem, pressione para baixo.</p></div>`;
  }

  private settings(): string {
    const settings = this.save.settings;
    return `<div class="settings-grid"><section><h3>${icon("sound")} O som da aventura</h3>${(["music", "sfx"] as const).map((name) => `<div class="range-setting"><label for="setting-${name}">${name === "music" ? "Volume da música" : "Efeitos sonoros"}</label><output for="setting-${name}">${Math.round(settings[name] * 100)}%</output><input id="setting-${name}" data-setting="${name}" type="range" min="0" max="100" value="${Math.round(settings[name] * 100)}" aria-label="${name === "music" ? "Volume da música" : "Volume dos efeitos sonoros"}"/></div>`).join("")}<p class="setting-note">O áudio começa depois da sua primeira interação.</p></section><section><h3>${icon("settings")} Sua experiência</h3><label class="toggle-setting"><span><b>Efeitos visuais</b><small>Partículas, clima e movimento de câmera.</small></span><input type="checkbox" data-setting="effects" ${settings.effects ? "checked" : ""} aria-label="Efeitos visuais"><i aria-hidden="true"></i></label><label class="toggle-setting"><span><b>Controles na tela</b><small>Exibir botões de toque também no computador.</small></span><input type="checkbox" data-setting="touch" ${settings.touch ? "checked" : ""} aria-label="Controles na tela"><i aria-hidden="true"></i></label></section></div><div class="reset-progress"><div><b>Uma nova jornada</b><p>Apague fases concluídas, recordes e relíquias deste navegador.</p></div><button type="button" class="button button-danger" data-action="reset">Reiniciar progresso</button></div><div class="reset-confirm" hidden role="alert"><p><b>Reiniciar todo o progresso?</b> As fases, recordes, relíquias e conquistas salvos serão apagados.</p><button class="button button-danger" data-action="reset-yes">Sim, reiniciar</button><button class="button button-secondary" data-action="reset-no">Cancelar</button></div>`;
  }

  private action(action: string, level?: string): void {
    switch (action) {
      case "play":
        this.handlers.play(this.save.unlocked);
        break;
      case "level":
        if (Number(level) <= this.save.unlocked)
          this.handlers.play(Number(level));
        break;
      case "resume":
        this.handlers.resume();
        break;
      case "restart":
        this.handlers.restart();
        break;
      case "menu":
        this.handlers.menu();
        this.show("menu");
        break;
      case "map":
        this.handlers.menu();
        this.show("map");
        break;
      case "controls":
        this.show("controls");
        break;
      case "settings":
        this.show("settings");
        break;
      case "pause-settings":
        this.show("settings", this.game);
        break;
      case "credits":
        this.show("credits");
        break;
      case "back":
        this.screen === "settings" && this.settingsReturn === "pause"
          ? this.show("pause", this.game)
          : this.show("menu");
        break;
      case "next":
        this.game && this.game.levelIndex < LEVELS.length - 1
          ? this.handlers.play(this.game.levelIndex + 1)
          : (this.handlers.menu(), this.show("map"));
        break;
      case "reset": {
        const confirmation =
          this.root.querySelector<HTMLElement>(".reset-confirm")!;
        confirmation.hidden = false;
        confirmation
          .querySelector<HTMLButtonElement>('[data-action="reset-no"]')!
          .focus();
        break;
      }
      case "reset-no":
        this.root.querySelector<HTMLElement>(".reset-confirm")!.hidden = true;
        break;
      case "reset-yes":
        this.handlers.reset();
        this.show("settings");
        this.toast("Uma nova jornada começa. Progresso reiniciado.");
        break;
    }
  }

  private toggleSound(): void {
    const muted =
      this.save.settings.music === 0 && this.save.settings.sfx === 0;
    if (!muted) {
      this.mutedMusic = this.save.settings.music;
      this.mutedSfx = this.save.settings.sfx;
    }
    const settings = {
      ...this.save.settings,
      music: muted ? this.mutedMusic : 0,
      sfx: muted ? this.mutedSfx : 0,
    };
    this.save.settings = settings;
    this.handlers.updateSettings(settings);
    this.paintProgress();
    if (this.screen === "settings") this.show("settings", this.game);
    this.toast(muted ? "Áudio ativado." : "Áudio desligado.");
  }

  private fullscreen(): void {
    if (document.fullscreenElement) {
      void document
        .exitFullscreen()
        .catch(() => this.toast("Não foi possível sair da tela cheia."));
      return;
    }
    if (!this.app.requestFullscreen) {
      this.toast("Tela cheia indisponível neste navegador.");
      return;
    }
    void this.app
      .requestFullscreen()
      .catch(() => this.toast("Tela cheia indisponível neste navegador."));
  }
}
