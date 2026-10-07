import type {CSSProperties} from 'react';

/** connect: two-sided slide-in converging on center across the first 35%. */
export function connect(progress: number): CSSProperties {
  const t = Math.min(1, Math.max(0, progress / 0.35));
  const eased = 1 - Math.pow(1 - t, 3);
  return {opacity: eased, transform: `scale(${0.85 + 0.15 * eased})`};
}
