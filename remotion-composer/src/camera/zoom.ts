import type {CSSProperties} from 'react';

/** expand_scale: decisive zoom from 1.0 to 1.25 on the detail. */
export function zoom(progress: number): CSSProperties {
  const t = Math.min(1, Math.max(0, progress));
  const eased = t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;
  return {transform: `scale(${1 + 0.25 * eased})`, transformOrigin: '50% 50%'};
}
