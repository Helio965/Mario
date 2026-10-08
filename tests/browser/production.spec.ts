import { test, expect } from "@playwright/test";
test.use({ baseURL: "http://127.0.0.1:4173/Mario/" });
test("build de produção carrega sob /Mario/ e permite jogar sem ponte de teste", async ({
  page,
}) => {
  const errors: string[] = [],
    assets: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  page.on("console", (m) => {
    if (m.type() === "error") errors.push(m.text());
  });
  page.on("response", (r) => {
    if (r.status() >= 400) errors.push(`${r.status()} ${r.url()}`);
    if (r.url().includes("/Mario/assets/")) assets.push(r.url());
  });
  await page.goto("./");
  await expect(page.locator("h1")).toContainText("LUME");
  expect(await page.evaluate(() => "__lume" in window)).toBe(false);
  expect(assets.length).toBeGreaterThanOrEqual(2);
  const icon = await page.request.get("favicon.svg");
  expect(icon.ok()).toBe(true);
  expect(icon.headers()["content-type"]).toContain("image/svg+xml");
  await page.locator('[data-action="play"]').click();
  await expect(page.locator(".game-hud")).toBeVisible();
  await page.keyboard.down("KeyD");
  await expect
    .poll(
      async () =>
        Number(await page.locator('[data-hud="coins"]').textContent()),
      { timeout: 2500 },
    )
    .toBeGreaterThan(0);
  await page.keyboard.up("KeyD");
  await page.keyboard.press("Escape");
  await expect(page.locator("#app")).toHaveAttribute("data-view", "pause");
  expect(errors).toEqual([]);
});
