import { LEVELS } from "../data/levels";
export function achievementsFor(
  completed: string[],
  relics: string[],
): string[] {
  const result: string[] = [];
  if (completed.length) result.push("first-clear");
  for (let world = 1; world <= 5; world++)
    if (
      LEVELS.filter((l) => l.world === world).every((l) =>
        completed.includes(l.id),
      )
    )
      result.push(`world-${world}`);
  if (LEVELS.every((l) => completed.includes(l.id))) result.push("all-clear");
  if (LEVELS.every((l) => relics.includes(l.id))) result.push("relic-hunter");
  return result;
}
