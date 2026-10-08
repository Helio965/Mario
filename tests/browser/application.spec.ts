import {
  test,
  expect,
  type Page,
  type Locator,
  type CDPSession,
} from "@playwright/test";
import type { Game } from "../../src/core/game";
import type { InputState } from "../../src/core/types";

type Settings = {
  music: number;
  sfx: number;
  effects: boolean;
  touch: boolean;
};
type Save = {
  unlocked: number;
  completed: string[];
  records: Record<string, number>;
  relics: string[];
  settings: Settings;
};
type AudioProbe = {
  context: AudioContext | null;
  musicBus: GainNode | null;
  sfxBus: GainNode | null;
};
type VirtualPad = {
  connected: boolean;
  axes: number[];
  buttons: { pressed: boolean; value: number; touched: boolean }[];
};
declare global {
  interface Window {
    __lume: {
      game: Game;
      input: { read(): InputState };
      save: Save;
      audio: AudioProbe;
    };
    __virtualPad: VirtualPad;
  }
}

const SAVE_KEY = "lume-save-v1";
const browserErrors = new WeakMap<Page, string[]>();

test.beforeEach(async ({ page }) => {
  const errors: string[] = [];
  browserErrors.set(page, errors);
  page.on("pageerror", (error) => errors.push(error.message));
  page.on("console", (message) => {
    if (message.type() === "error")
      errors.push(`${message.text()} (${message.location().url})`);
  });
});

test.afterEach(async ({ page }) => {
  expect(
    browserErrors.get(page),
    "erros relevantes no console/navegador",
  ).toEqual([]);
});

async function open(page: Page) {
  await page.goto("./");
  await expect(page.locator("#app")).toHaveAttribute("data-view", "menu");
  await page.waitForFunction(() => Boolean(window.__lume));
}

async function play(page: Page) {
  await page.locator('[data-action="play"]').click();
  await expect(page.locator("#app")).toHaveAttribute("data-view", "playing");
  await page.locator("#game").focus();
  await expect
    .poll(() => page.evaluate(() => window.__lume.game.player.grounded))
    .toBe(true);
}

async function snapshot(page: Page) {
  return page.evaluate(() => {
    const game = window.__lume.game;
    return {
      x: game.player.x,
      y: game.player.y,
      vy: game.player.vy,
      time: game.time,
      status: game.status,
      coins: game.coinsTotal,
      cameraX: game.camera.x,
      levelIndex: game.levelIndex,
    };
  });
}

async function pauseWithKeyboard(page: Page) {
  await page.keyboard.down("Escape");
  try {
    await expect(page.locator("#app")).toHaveAttribute("data-view", "pause");
  } finally {
    await page.keyboard.up("Escape");
  }
}

async function slider(locator: Locator, value: number) {
  await locator.evaluate((element, next) => {
    const input = element as HTMLInputElement;
    input.value = String(next);
    input.dispatchEvent(new Event("input", { bubbles: true }));
  }, value);
}

async function completeFixture(page: Page) {
  // This tests the engine-event → UI → localStorage integration, not a playable route.
  await page.evaluate(() => window.__lume.game.finish());
  await expect(page.locator("#app")).toHaveAttribute("data-view", "complete");
  await expect
    .poll(() => page.evaluate(() => window.__lume.save.completed))
    .toEqual(["1-1"]);
}

test("menu real apresenta cinco mundos, controles, configurações e créditos", async ({
  page,
}) => {
  await open(page);
  await expect(
    page.getByRole("heading", { name: "LUME", exact: false }).first(),
  ).toBeVisible();
  await expect(page.locator('[data-action="play"]')).toBeVisible();
  await expect(page.locator("#game")).toBeVisible();
  await page.locator('[data-action="map"]').click();
  await expect(page.locator(".world-card")).toHaveCount(5);
  await expect(page.locator(".stage-node")).toHaveCount(15);
  await expect(
    page.locator('[data-action="level"][data-level="0"]'),
  ).toBeEnabled();
  await expect(page.locator(".stage-node:disabled")).toHaveCount(14);
  await page.locator('[data-action="back"]').click();
  await page.locator('[data-action="controls"]').click();
  await expect(page.locator("#app")).toHaveAttribute("data-view", "controls");
  await expect(page.getByText("Teclado", { exact: true })).toBeVisible();
  await expect(
    page.getByText("Gamepad & celular", { exact: true }),
  ).toBeVisible();
  await page.locator('[data-action="back"]').click();
  await page.locator('[data-action="settings"]').click();
  await expect(page.locator('[data-setting="music"]')).toBeVisible();
  await expect(page.locator('[data-setting="sfx"]')).toBeVisible();
  await page.locator('[data-action="back"]').click();
  await page.locator('[data-action="credits"]').click();
  await expect(page.locator("#app")).toHaveAttribute("data-view", "credits");
  await expect(
    page.getByText(/Código e recursos originais sob licença MIT/),
  ).toBeVisible();
  await expect(
    page.getByText(/Projeto independente, não oficial/),
  ).toBeVisible();
  await page.locator('[data-action="back"]').click();
  await expect(page.locator("#app")).toHaveAttribute("data-view", "menu");
});

test("teclado controla salto, movimento, coleta de moedas e câmera", async ({
  page,
}) => {
  await open(page);
  await play(page);
  const before = await snapshot(page);
  await page.keyboard.down("Space");
  await expect
    .poll(() => page.evaluate(() => window.__lume.game.player.vy))
    .toBeLessThan(-150);
  await page.keyboard.up("Space");
  await expect
    .poll(() => page.evaluate(() => window.__lume.game.player.grounded))
    .toBe(true);
  await page.keyboard.down("Shift");
  await page.keyboard.down("ArrowRight");
  try {
    await expect
      .poll(() => page.evaluate(() => window.__lume.game.player.x), {
        intervals: [50],
      })
      .toBeGreaterThan(500);
  } finally {
    await page.keyboard.up("ArrowRight");
    await page.keyboard.up("Shift");
  }
  const after = await snapshot(page);
  expect(after.x).toBeGreaterThan(before.x + 400);
  expect(after.coins).toBeGreaterThanOrEqual(4);
  expect(after.cameraX).toBeGreaterThan(30);
  await expect(page.locator('[data-hud="coins"]')).toHaveText(
    String(after.coins),
  );
  expect(after.status).toBe("playing");
});

test("pausa congela física e tempo, configurações retornam à pausa, continuar/reiniciar/menu funcionam", async ({
  page,
}) => {
  await open(page);
  await play(page);
  await page.keyboard.down("ArrowRight");
  try {
    await expect
      .poll(() => page.evaluate(() => window.__lume.game.player.x), {
        intervals: [50],
      })
      .toBeGreaterThan(170);
  } finally {
    await page.keyboard.up("ArrowRight");
  }
  await pauseWithKeyboard(page);
  const paused = await snapshot(page);
  await page.waitForTimeout(350);
  const frozen = await snapshot(page);
  expect(frozen.x).toBe(paused.x);
  expect(frozen.y).toBe(paused.y);
  expect(frozen.time).toBe(paused.time);
  await page.locator('[data-action="pause-settings"]').click();
  await expect(page.locator("#app")).toHaveAttribute("data-view", "settings");
  await page.locator('[data-action="back"]').click();
  await expect(page.locator("#app")).toHaveAttribute("data-view", "pause");
  await page.locator('[data-action="resume"]').click();
  await expect(page.locator("#app")).toHaveAttribute("data-view", "playing");
  await expect
    .poll(() => page.evaluate(() => window.__lume.game.time))
    .toBeLessThan(paused.time - 0.1);
  await pauseWithKeyboard(page);
  await page.locator('[data-action="restart"]').click();
  await expect(page.locator("#app")).toHaveAttribute("data-view", "playing");
  expect((await snapshot(page)).x).toBeLessThan(90);
  expect((await snapshot(page)).coins).toBe(0);
  await pauseWithKeyboard(page);
  await page.locator('[data-action="menu"]').click();
  await expect(page.locator("#app")).toHaveAttribute("data-view", "menu");
});

test("Escape também retoma a partida com foco no botão do menu de pausa", async ({
  page,
}) => {
  await open(page);
  await play(page);
  await pauseWithKeyboard(page);
  await page.locator('[data-action="resume"]').focus();
  await page.keyboard.down("Escape");
  try {
    await expect(page.locator("#app")).toHaveAttribute("data-view", "playing");
  } finally {
    await page.keyboard.up("Escape");
  }
});

test("música e efeitos têm volumes independentes e configurações persistem ao recarregar", async ({
  page,
}) => {
  await open(page);
  await page.locator('[data-action="settings"]').click();
  await slider(page.locator('[data-setting="music"]'), 0);
  expect(await page.evaluate(() => window.__lume.save.settings.sfx)).toBe(0.75);
  await slider(page.locator('[data-setting="sfx"]'), 23);
  await page
    .getByRole("checkbox", { name: "Efeitos visuais", exact: true })
    .uncheck();
  await page.reload();
  await expect(page.locator("#app")).toHaveAttribute("data-view", "menu");
  expect(await page.evaluate(() => window.__lume.save.settings)).toEqual({
    music: 0,
    sfx: 0.23,
    effects: false,
    touch: false,
  });
  await page.locator('[data-action="settings"]').click();
  await expect(page.locator('[data-setting="music"]')).toHaveValue("0");
  await expect(page.locator('[data-setting="sfx"]')).toHaveValue("23");
  await expect(
    page.getByRole("checkbox", { name: "Efeitos visuais", exact: true }),
  ).not.toBeChecked();
  await page.locator('[data-shell="sound"]').click();
  await expect(page.locator('[data-shell="sound"]')).toHaveAttribute(
    "aria-label",
    "Ativar áudio",
  );
  expect(
    await page.evaluate(() => ({
      music: window.__lume.save.settings.music,
      sfx: window.__lume.save.settings.sfx,
    })),
  ).toEqual({ music: 0, sfx: 0 });
  await page.reload();
  await expect(page.locator('[data-shell="sound"]')).toHaveAttribute(
    "aria-label",
    "Ativar áudio",
  );
});

test("JSON corrompido do salvamento inicia jornada válida", async ({
  page,
}) => {
  await page.addInitScript(
    (key) => localStorage.setItem(key, "{invalid json"),
    SAVE_KEY,
  );
  await open(page);
  expect(
    await page.evaluate(() => ({
      unlocked: window.__lume.save.unlocked,
      completed: window.__lume.save.completed,
    })),
  ).toEqual({ unlocked: 0, completed: [] });
  await play(page);
  expect((await snapshot(page)).status).toBe("playing");
});

test("versão de salvamento desconhecida usa valores padrão", async ({
  page,
}) => {
  await page.addInitScript(
    (key) =>
      localStorage.setItem(
        key,
        JSON.stringify({ version: 99, unlocked: 14, completed: ["5-3"] }),
      ),
    SAVE_KEY,
  );
  await open(page);
  expect(
    await page.evaluate(() => ({
      unlocked: window.__lume.save.unlocked,
      completed: window.__lume.save.completed,
    })),
  ).toEqual({ unlocked: 0, completed: [] });
  await page.locator('[data-action="map"]').click();
  await expect(page.locator(".stage-node:disabled")).toHaveCount(14);
});

test("fixture explícita de conclusão valida evento, salvamento, recarga e fase desbloqueada", async ({
  page,
}) => {
  await open(page);
  await play(page);
  await completeFixture(page);
  expect(await page.evaluate(() => window.__lume.save.unlocked)).toBe(1);
  expect(
    await page.evaluate(() => window.__lume.save.records["1-1"]),
  ).toBeGreaterThan(0);
  const stored = await page.evaluate(
    (key) => JSON.parse(localStorage.getItem(key)!),
    SAVE_KEY,
  );
  expect(stored.completed).toEqual(["1-1"]);
  expect(stored.unlocked).toBe(1);
  await page.reload();
  await expect(page.locator('[data-action="play"]')).toContainText(
    "Continuar · 1-2",
  );
  await page.locator('[data-action="map"]').click();
  await expect(page.locator('[data-level="0"]')).toHaveClass(/cleared/);
  await expect(page.locator('[data-level="1"]')).toBeEnabled();
  await expect(page.locator('[data-level="2"]')).toBeDisabled();
  await page.locator('[data-level="1"]').click();
  await expect(page.locator("#app")).toHaveAttribute("data-view", "playing");
  expect((await snapshot(page)).levelIndex).toBe(1);
});

test("apagar progresso exige confirmação e cancelar preserva a jornada", async ({
  page,
}) => {
  await open(page);
  await play(page);
  await completeFixture(page);
  await page.locator('[data-action="menu"]').click();
  await page.locator('[data-action="settings"]').click();
  await page.locator('[data-action="reset"]').click();
  await expect(page.locator(".reset-confirm")).toBeVisible();
  expect(await page.evaluate(() => window.__lume.save.completed)).toEqual([
    "1-1",
  ]);
  await page.locator('[data-action="reset-no"]').click();
  await expect(page.locator(".reset-confirm")).toBeHidden();
  await page.reload();
  expect(await page.evaluate(() => window.__lume.save.completed)).toEqual([
    "1-1",
  ]);
  await page.locator('[data-action="settings"]').click();
  await page.locator('[data-action="reset"]').click();
  await page.locator('[data-action="reset-yes"]').click();
  expect(
    await page.evaluate(() => ({
      unlocked: window.__lume.save.unlocked,
      completed: window.__lume.save.completed,
    })),
  ).toEqual({ unlocked: 0, completed: [] });
  await expect(page.locator(".reset-confirm")).toBeHidden();
  await page.reload();
  await page.locator('[data-action="map"]').click();
  await expect(page.locator(".stage-node:disabled")).toHaveCount(14);
});

test("Web Audio aguarda gesto real e os canais de música e efeitos podem ser silenciados independentemente", async ({
  page,
}) => {
  await open(page);
  expect(await page.evaluate(() => window.__lume.audio.context === null)).toBe(
    true,
  );
  await page.locator('[data-action="settings"]').click();
  await expect
    .poll(() => page.evaluate(() => window.__lume.audio.context?.state))
    .toBe("running");
  await slider(page.locator('[data-setting="music"]'), 0);
  await expect
    .poll(() => page.evaluate(() => window.__lume.audio.musicBus!.gain.value))
    .toBeLessThan(0.001);
  expect(
    await page.evaluate(() => window.__lume.audio.sfxBus!.gain.value),
  ).toBeCloseTo(0.75, 2);
  await slider(page.locator('[data-setting="sfx"]'), 0);
  await slider(page.locator('[data-setting="music"]'), 70);
  await expect
    .poll(() => page.evaluate(() => window.__lume.audio.sfxBus!.gain.value))
    .toBeLessThan(0.001);
  await expect
    .poll(() => page.evaluate(() => window.__lume.audio.musicBus!.gain.value))
    .toBeGreaterThan(0.69);
  expect(await page.evaluate(() => window.__lume.audio.context?.state)).toBe(
    "running",
  );
});

test("gamepad virtual: navigator.getGamepads simulado move, pula, corre e alterna a pausa", async ({
  page,
}) => {
  // The browser mapping is tested with a virtual device; this does not verify physical hardware.
  await page.addInitScript(() => {
    window.__virtualPad = {
      connected: true,
      axes: [0, 0],
      buttons: Array.from({ length: 17 }, () => ({
        pressed: false,
        value: 0,
        touched: false,
      })),
    };
    Object.defineProperty(navigator, "getGamepads", {
      configurable: true,
      value: () => [window.__virtualPad],
    });
  });
  await open(page);
  await play(page);
  const initial = (await snapshot(page)).x;
  await page.evaluate(() => {
    window.__virtualPad.axes[0] = 0.8;
  });
  await expect
    .poll(() => page.evaluate(() => window.__lume.game.player.x), {
      intervals: [50],
    })
    .toBeGreaterThan(initial + 40);
  await page.evaluate(() => {
    window.__virtualPad.axes[0] = 0;
    window.__virtualPad.buttons[0].pressed = true;
  });
  await expect
    .poll(() => page.evaluate(() => window.__lume.game.player.vy))
    .toBeLessThan(-150);
  await page.evaluate(() => {
    window.__virtualPad.buttons[0].pressed = false;
  });
  await expect
    .poll(() => page.evaluate(() => window.__lume.game.player.grounded))
    .toBe(true);
  await page.evaluate(() => {
    window.__virtualPad.axes[0] = 0.8;
    window.__virtualPad.buttons[2].pressed = true;
  });
  await expect
    .poll(() => page.evaluate(() => window.__lume.game.player.vx), {
      intervals: [50],
    })
    .toBeGreaterThan(260);
  await page.evaluate(() => {
    window.__virtualPad.axes[0] = 0;
    window.__virtualPad.buttons[2].pressed = false;
    window.__virtualPad.buttons[14].pressed = true;
  });
  expect(
    await page.evaluate(() => ({
      left: window.__lume.input.read().left,
      right: window.__lume.input.read().right,
    })),
  ).toEqual({ left: true, right: false });
  await page.evaluate(() => {
    window.__virtualPad.buttons[14].pressed = false;
    window.__virtualPad.buttons[9].pressed = true;
  });
  await expect(page.locator("#app")).toHaveAttribute("data-view", "pause");
  await page.evaluate(() => {
    window.__virtualPad.buttons[9].pressed = false;
  });
  await page.evaluate(
    () =>
      new Promise<void>((resolve) =>
        requestAnimationFrame(() => requestAnimationFrame(() => resolve())),
      ),
  );
  await page.evaluate(() => {
    window.__virtualPad.buttons[9].pressed = true;
  });
  await expect(page.locator("#app")).toHaveAttribute("data-view", "playing");
  await page.evaluate(() => {
    window.__virtualPad.buttons[9].pressed = false;
  });
});

type TouchPoint = { x: number; y: number; id: number };
async function point(locator: Locator, id: number): Promise<TouchPoint> {
  await expect(locator).toBeVisible();
  const box = await locator.boundingBox();
  if (!box) throw new Error("Controle de toque sem área visível");
  return { x: box.x + box.width / 2, y: box.y + box.height / 2, id };
}

async function touch(
  session: CDPSession,
  type: "touchStart" | "touchEnd" | "touchCancel",
  touchPoints: TouchPoint[],
) {
  await session.send("Input.dispatchTouchEvent", { type, touchPoints });
}

test("comandos de salto e pausa entre dois quadros não se perdem", async ({
  page,
}) => {
  await open(page);
  await play(page);
  const quick = async (code: string) =>
    page.evaluate((key) => {
      const target = document.querySelector("#game")!;
      target.dispatchEvent(
        new KeyboardEvent("keydown", { code: key, bubbles: true }),
      );
      target.dispatchEvent(
        new KeyboardEvent("keyup", { code: key, bubbles: true }),
      );
    }, code);
  await quick("Space");
  await expect
    .poll(() => page.evaluate(() => window.__lume.game.player.vy))
    .toBeLessThan(0);
  await quick("Escape");
  await expect(page.locator("#app")).toHaveAttribute("data-view", "pause");
  await quick("Escape");
  await expect(page.locator("#app")).toHaveAttribute("data-view", "playing");
});
test.describe("celular horizontal com eventos reais de toque", () => {
  test.use({
    viewport: { width: 844, height: 390 },
    isMobile: true,
    hasTouch: true,
  });

  test("direção e salto podem ser pressionados simultaneamente com dois dedos", async ({
    page,
  }) => {
    await open(page);
    await play(page);
    const session = await page.context().newCDPSession(page);
    const right = await point(page.locator('[data-touch="right"]'), 1);
    const jump = await point(page.locator('[data-touch="jump"]'), 2);
    const initialX = (await snapshot(page)).x;
    await touch(session, "touchStart", [right]);
    await expect
      .poll(() => page.evaluate(() => window.__lume.game.player.x))
      .toBeGreaterThan(initialX + 10);
    await touch(session, "touchStart", [right, jump]);
    await expect
      .poll(() =>
        page.evaluate(() => {
          const input = window.__lume.input.read();
          return input.right && input.jump;
        }),
      )
      .toBe(true);
    await expect
      .poll(() => page.evaluate(() => window.__lume.game.player.vy))
      .toBeLessThan(-150);
    expect((await snapshot(page)).x).toBeGreaterThan(initialX + 10);
    await touch(session, "touchEnd", []);
    await expect
      .poll(() =>
        page.evaluate(() => {
          const input = window.__lume.input.read();
          return input.right || input.jump;
        }),
      )
      .toBe(false);
  });

  test("cancelamento e perda de foco limpam controles sem deixar direção presa", async ({
    page,
  }) => {
    await open(page);
    await play(page);
    const session = await page.context().newCDPSession(page);
    const left = await point(page.locator('[data-touch="left"]'), 1);
    const run = await point(page.locator('[data-touch="run"]'), 2);
    await touch(session, "touchStart", [left, run]);
    await expect
      .poll(() =>
        page.evaluate(() => {
          const input = window.__lume.input.read();
          return input.left && input.run;
        }),
      )
      .toBe(true);
    await touch(session, "touchCancel", []);
    await expect
      .poll(() =>
        page.evaluate(() => {
          const input = window.__lume.input.read();
          return input.left || input.run;
        }),
      )
      .toBe(false);
    await expect
      .poll(() => page.evaluate(() => window.__lume.game.player.vx))
      .toBe(0);
    const right = await point(page.locator('[data-touch="right"]'), 3);
    await touch(session, "touchStart", [right]);
    await expect
      .poll(() => page.evaluate(() => window.__lume.input.read().right))
      .toBe(true);
    await page.evaluate(() => window.dispatchEvent(new Event("blur")));
    await expect(page.locator("#app")).toHaveAttribute("data-view", "pause");
    expect(
      await page.evaluate(() =>
        Object.values(window.__lume.input.read()).some(Boolean),
      ),
    ).toBe(false);
    await touch(session, "touchCancel", []);
  });
});
