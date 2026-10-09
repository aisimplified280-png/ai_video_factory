import type {CSSProperties} from 'react';

/**
 * grow/assemble/expand: the element is on screen almost immediately — the
 * narration never waits for an animation. Opacity is full within ~3% of the
 * scene (~0.15s); the scale settles with a light overshoot across the first
 * 10% (~0.5s).
 */
export function grow(progress: number): CSSProperties {
  const t = Math.min(1, Math.max(0, progress / 0.1));
  const overshoot = 1 + 2.7 * Math.pow(t - 1, 3) + 1.7 * Math.pow(t - 1, 2);
  const scale = 0.6 + 0.4 * Math.min(1.06, Math.max(0, overshoot));
  return {opacity: Math.min(1, t * 3), transform: `scale(${scale})`};
}
