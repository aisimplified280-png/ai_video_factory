import type {CSSProperties} from 'react';

/** transform: scale plus quarter-turn across the middle 60% of the event. */
export function transform(progress: number): CSSProperties {
  const t = Math.min(1, Math.max(0, (progress - 0.2) / 0.6));
  const eased = t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;
  return {transform: `scale(${1 + 0.12 * eased}) rotate(${8 * eased}deg)`};
}
