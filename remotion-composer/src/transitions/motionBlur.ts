import type {CSSProperties} from 'react';

/** motion_blur: directional smear across the boundary. */
export function overlapFrames(fps: number): number {
  return Math.round(fps * 0.3);
}

export function outgoingStyle(progress: number): CSSProperties {
  const t = Math.min(1, Math.max(0, progress));
  return {opacity: 1 - t * 0.6, transform: `translateX(${-160 * t}px)`, filter: `blur(${14 * t}px)`};
}

export function incomingStyle(progress: number): CSSProperties {
  const t = Math.min(1, Math.max(0, progress));
  return {opacity: 0.4 + 0.6 * t, transform: `translateX(${160 * (1 - t)}px)`, filter: `blur(${14 * (1 - t)}px)`};
}
