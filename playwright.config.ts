import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "./tests/browser",
  workers: 2,
  use: {
    baseURL: "http://127.0.0.1:5173/Mario/",
    headless: true,
    launchOptions: {
      ...(process.env.CHROMIUM_PATH
        ? { executablePath: process.env.CHROMIUM_PATH }
        : process.env.CI
          ? {}
          : { executablePath: "/usr/bin/chromium" }),
      args: ["--no-sandbox"],
    },
  },
  webServer: [
    {
      command: "npm run dev",
      url: "http://127.0.0.1:5173/Mario/",
      reuseExistingServer: !process.env.CI,
    },
    {
      command: "npm run build && npm run preview -- --port 4173 --strictPort",
      url: "http://127.0.0.1:4173/Mario/",
      reuseExistingServer: !process.env.CI,
    },
  ],
});
