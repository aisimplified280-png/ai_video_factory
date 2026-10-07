import type {CSSProperties} from 'react';

/** pulse: continuous breathing scale across the whole event. */
export function pulse(progress: number, beats = 2): CSSProperties {
  const t = Math.min(1, Math.max(0, progress));
  const scale = 1 + 0.04 * Math.sin(t * Math.PI * 2 * beats);
  return {transform: `scale(${scale})`};
}
