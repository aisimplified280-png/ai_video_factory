import type {CSSProperties} from 'react';

/** shift_focus: lateral attention relocation with a brightness lift. */
export function focusShift(progress: number): CSSProperties {
  const t = Math.min(1, Math.max(0, progress / 0.5));
  const eased = 1 - Math.pow(1 - t, 3);
  return {transform: `translateX(${-70 + 140 * eased}px) scale(${1 + 0.05 * eased})`};
}
