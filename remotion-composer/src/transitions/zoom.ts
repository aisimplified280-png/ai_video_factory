import type {CSSProperties} from 'react';

/** zoom_transition / shape_morph: outgoing pushes past the lens into incoming. */
export function overlapFrames(fps: number): number {
  return Math.round(fps * 0.3);
}

export function outgoingStyle(progress: number): CSSProperties {
  const t = Math.min(1, Math.max(0, progress));
  return {opacity: 1 - t, transform: `scale(${1 + 0.3 * t})`};
}

export function incomingStyle(progress: number): CSSProperties {
  const t = Math.min(1, Math.max(0, progress));
  const eased = 1 - Math.pow(1 - t, 3);
  return {opacity: eased, transform: `scale(${1.2 - 0.2 * eased})`};
}
