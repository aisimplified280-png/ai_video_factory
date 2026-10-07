import type {CSSProperties} from 'react';

/** directional_wipe / object_transition: incoming clip wipes across. */
export function overlapFrames(fps: number): number {
  return Math.round(fps * 0.35);
}

export function incomingStyle(progress: number, direction: 'left' | 'right' = 'left'): CSSProperties {
  const t = Math.min(1, Math.max(0, progress));
  const eased = 1 - Math.pow(1 - t, 3);
  const from = direction === 'left' ? -100 : 100;
  return {transform: `translateX(${from * (1 - eased)}%)`};
}
