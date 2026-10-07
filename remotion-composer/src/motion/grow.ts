import type {CSSProperties} from 'react';

/** grow/assemble/expand: scale from 0.6 to 1 with overshoot across the first 40%. */
export function grow(progress: number): CSSProperties {
  const t = Math.min(1, Math.max(0, progress / 0.4));
  const overshoot = 1 + 2.7 * Math.pow(t - 1, 3) + 1.7 * Math.pow(t - 1, 2);
  const scale = 0.6 + 0.4 * Math.min(1.06, Math.max(0, overshoot));
  return {opacity: Math.min(1, t * 2), transform: `scale(${scale})`};
}
