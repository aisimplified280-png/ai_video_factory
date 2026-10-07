import type {CSSProperties} from 'react';

/** compare: split-slide from center — left half exits left, right half exits
 * right — across the first 30%. Applied per side via the `side` argument. */
export function compare(progress: number, side: 'left' | 'right'): CSSProperties {
  const t = Math.min(1, Math.max(0, progress / 0.3));
  const eased = 1 - Math.pow(1 - t, 3);
  const direction = side === 'left' ? -1 : 1;
  return {opacity: eased, transform: `translateX(${direction * (1 - eased) * 140}px)`};
}
