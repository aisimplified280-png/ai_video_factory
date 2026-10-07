/** count: how many of `total` countable items are visible at progress. */
export function count(progress: number, total: number): number {
  const t = Math.min(1, Math.max(0, progress));
  return Math.max(1, Math.round(total * t));
}
