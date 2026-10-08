export const SAVE_KEY = "lume-save-v1";

export interface Settings {
  music: number;
  sfx: number;
  effects: boolean;
  touch: boolean;
}

export interface SaveData {
  version: 1;
  unlocked: number;
  completed: string[];
  records: Record<string, number>;
  relics: string[];
  achievements: string[];
  settings: Settings;
}

const DEFAULT_SETTINGS: Settings = {
  music: 0.45,
  sfx: 0.75,
  effects: true,
  touch: false,
};

function freshSave(): SaveData {
  return {
    version: 1,
    unlocked: 0,
    completed: [],
    records: {},
    relics: [],
    achievements: [],
    settings: { ...DEFAULT_SETTINGS },
  };
}

function record(value: unknown): Record<string, unknown> | null {
  return typeof value === "object" && value !== null && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : null;
}

function number(
  value: unknown,
  fallback: number,
  maximum: number,
  integer = false,
): number {
  if (typeof value !== "number" || !Number.isFinite(value)) return fallback;
  const result = Math.min(maximum, Math.max(0, value));
  return integer ? Math.floor(result) : result;
}

function validId(value: unknown): value is string {
  return (
    typeof value === "string" &&
    value.length > 0 &&
    value.length <= 128 &&
    value.trim() === value &&
    !/[\u0000-\u001f\u007f]/.test(value) &&
    value !== "__proto__" &&
    value !== "constructor" &&
    value !== "prototype"
  );
}

function ids(value: unknown): string[] {
  return Array.isArray(value) ? [...new Set(value.filter(validId))] : [];
}

/** Rebuild every field so malformed or partially old local data cannot reach gameplay. */
function sanitize(value: unknown): SaveData {
  const source = record(value);
  if (!source || source.version !== 1) return freshSave();
  const settings = record(source.settings) ?? {};
  const records = record(source.records) ?? {};
  const cleanRecords: Record<string, number> = {};
  for (const [key, score] of Object.entries(records)) {
    if (validId(key) && typeof score === "number" && Number.isFinite(score)) {
      cleanRecords[key] = number(score, 0, Number.MAX_SAFE_INTEGER, true);
    }
  }
  return {
    version: 1,
    unlocked: number(source.unlocked, 0, 14, true),
    completed: ids(source.completed),
    records: cleanRecords,
    relics: ids(source.relics),
    achievements: ids(source.achievements),
    settings: {
      music: number(settings.music, DEFAULT_SETTINGS.music, 1),
      sfx: number(settings.sfx, DEFAULT_SETTINGS.sfx, 1),
      effects:
        typeof settings.effects === "boolean"
          ? settings.effects
          : DEFAULT_SETTINGS.effects,
      touch:
        typeof settings.touch === "boolean"
          ? settings.touch
          : DEFAULT_SETTINGS.touch,
    },
  };
}

function browserStorage(): Storage | undefined {
  try {
    return globalThis.localStorage;
  } catch {
    return undefined;
  }
}

export function loadSave(storage?: Pick<Storage, "getItem">): SaveData {
  try {
    const raw = (storage ?? browserStorage())?.getItem(SAVE_KEY);
    return raw ? sanitize(JSON.parse(raw)) : freshSave();
  } catch {
    return freshSave();
  }
}

export function writeSave(
  data: SaveData,
  storage?: Pick<Storage, "setItem">,
): boolean {
  try {
    const target = storage ?? browserStorage();
    if (!target) return false;
    target.setItem(SAVE_KEY, JSON.stringify(sanitize(data)));
    return true;
  } catch {
    return false;
  }
}

export function resetSave(storage?: Pick<Storage, "removeItem">): SaveData {
  try {
    (storage ?? browserStorage())?.removeItem(SAVE_KEY);
  } catch {
    /* Storage may be blocked. */
  }
  return freshSave();
}

export function completeLevel(
  data: SaveData,
  index: number,
  score: number,
  relic: boolean,
  levelId: string,
): SaveData {
  const next = sanitize(data);
  if (
    !validId(levelId) ||
    !Number.isFinite(index) ||
    index < 0 ||
    index > 14 ||
    !Number.isInteger(index)
  )
    return next;
  next.unlocked = Math.max(next.unlocked, Math.min(14, index + 1));
  next.completed = [...new Set([...next.completed, levelId])];
  next.records[levelId] = Math.max(
    next.records[levelId] ?? 0,
    number(score, 0, Number.MAX_SAFE_INTEGER, true),
  );
  if (relic) next.relics = [...new Set([...next.relics, levelId])];
  return next;
}
