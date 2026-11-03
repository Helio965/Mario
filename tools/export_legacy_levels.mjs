// Exports the TypeScript campaign (src/data/levels.ts) exactly as the web build
// sees it, so the Python edition can convert it without retyping coordinates.
// Usage: node --experimental-strip-types tools/export_legacy_levels.mjs > out.json
const { LEVELS, THEMES } = await import("../src/data/levels.ts");
process.stdout.write(JSON.stringify({ themes: THEMES, levels: LEVELS }, null, 1));
