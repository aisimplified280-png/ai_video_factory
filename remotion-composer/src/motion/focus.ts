import type {CSSProperties} from 'react';

/** focus/shift_focus: push toward the subject while dimming surroundings. */
export function focus(progress: number): CSSProperties {
  const t = Math.min(1, Math.max(0, progress / 0.35));
  const eased = 1 - Math.pow(1 - t, 3);
  return {transform: `scale(${1 + 0.08 * eased})`, filter: `brightness(${1 + 0.12 * eased})`};
}
