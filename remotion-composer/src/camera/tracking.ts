import type {CSSProperties} from 'react';

/** follow_subject: push-in combined with a lateral track. */
export function tracking(progress: number): CSSProperties {
  const t = Math.min(1, Math.max(0, progress));
  const eased = 1 - Math.pow(1 - t, 2);
  return {transform: `scale(${1 + 0.1 * eased}) translateX(${-50 + 100 * eased}px)`};
}
