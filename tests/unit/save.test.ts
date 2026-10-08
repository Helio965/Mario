import { describe, expect, it } from 'vitest';
import { completeLevel, loadSave, resetSave, SAVE_KEY, writeSave } from '../../src/systems/save';

function reading(value: unknown) {
  return { getItem: () => JSON.stringify(value) };
}

describe('local progress', () => {
  it('returns fresh independent defaults for unavailable, malformed, or incompatible saves', () => {
    const initial = loadSave({ getItem: () => { throw new Error('Denied'); } });
    expect(initial.unlocked).toBe(0);
    expect(loadSave({ getItem: () => '{broken' })).toEqual(initial);
    expect(loadSave(reading({ version: 2, unlocked: 14 }))).toEqual(initial);
    initial.completed.push('mutated');
    initial.settings.music = 0;
    const another = loadSave({ getItem: () => null });
    expect(another.completed).toEqual([]);
    expect(another.settings.music).toBeGreaterThan(0);
  });

  it('sanitizes every persisted field without accepting unsafe property names', () => {
    const data = loadSave(reading({
      version: 1,
      unlocked: 99.5,
      completed: ['1-1', null, '1-1', '', ' line ', '__proto__'],
      records: JSON.parse('{"1-1":9.8,"1-2":-2,"bad":"999","__proto__":8}'),
      relics: ['1-1', 33, '1-1'],
      achievements: ['first-clear', 'first-clear', false],
      settings: { music: 5, sfx: -2, effects: 'false', touch: true },
    }));
    expect(data.unlocked).toBe(14);
    expect(data.completed).toEqual(['1-1']);
    expect(data.records).toEqual({ '1-1': 9, '1-2': 0 });
    expect(data.relics).toEqual(['1-1']);
    expect(data.achievements).toEqual(['first-clear']);
    expect(data.settings).toEqual({ music: 1, sfx: 0, effects: true, touch: true });
  });

  it('unlocks at most the last stage, retains the best score, and leaves the input unchanged', () => {
    const original = loadSave({ getItem: () => null });
    const first = completeLevel(original, 0, 950, true, '1-1');
    expect(first.unlocked).toBe(1);
    expect(first.completed).toEqual(['1-1']);
    expect(first.relics).toEqual(['1-1']);
    expect(original.completed).toEqual([]);
    expect(original.records).toEqual({});
    expect(first.settings).not.toBe(original.settings);
    const replay = completeLevel(first, 0, 10, true, '1-1');
    expect(replay.records['1-1']).toBe(950);
    expect(replay.completed).toHaveLength(1);
    expect(replay.relics).toHaveLength(1);
    expect(completeLevel(replay, 14, 100, false, '5-3').unlocked).toBe(14);
    expect(completeLevel(replay, -1, 100, false, 'bad')).toEqual(replay);
  });

  it('handles storage denial and clears only the game key on reset', () => {
    const data = loadSave({ getItem: () => null });
    expect(writeSave(data, { setItem: () => { throw new Error('Quota'); } })).toBe(false);
    let saved: [string, string] | undefined;
    expect(writeSave(data, { setItem: (key, value) => { saved = [key, value]; } })).toBe(true);
    expect(saved?.[0]).toBe(SAVE_KEY);
    expect(JSON.parse(saved![1])).toEqual(data);
    let removed: string | undefined;
    expect(resetSave({ removeItem: key => { removed = key; } })).toEqual(data);
    expect(removed).toBe(SAVE_KEY);
    expect(resetSave({ removeItem: () => { throw new Error('Denied'); } })).toEqual(data);
  });
});
