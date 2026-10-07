import type {CSSProperties} from 'react';

/** fade / cross_dissolve: outgoing fades out while incoming fades in. */
export function overlapFrames(fps: number): number {
  return Math.round(fps * 0.4);
}

export function outgoingStyle(progress: number): CSSProperties {
  return {opacity: 1 - Math.min(1, Math.max(0, progress))};
}

export function incomingStyle(progress: number): CSSProperties {
  return {opacity: Math.min(1, Math.max(0, progress))};
}
