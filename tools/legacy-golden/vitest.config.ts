import { defineConfig } from "vitest/config";
// Generates deterministic simulation traces from the original TypeScript engine.
// Run: npx vitest run --config tools/legacy-golden/vitest.config.ts
export default defineConfig({
  test: { include: ["tools/legacy-golden/*.test.ts"], maxWorkers: 1, testTimeout: 600000 },
});
