import type {CSSProperties} from 'react';

/** emerge/appear: fade in over the first 15% of the event. */
export function appear(progress: number): CSSProperties {
  const t = Math.min(1, Math.max(0, progress)) / 0.15;
  return {opacity: Math.min(1, Math.max(0, t))};
}
