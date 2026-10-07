import type {CSSProperties} from 'react';

/** pullOut: slow retreat from 1.12 to 1.0, revealing context. */
export function pullOut(progress: number, amount = 0.12): CSSProperties {
  const t = Math.min(1, Math.max(0, progress));
  const eased = 1 - Math.pow(1 - t, 2);
  return {transform: `scale(${1 + amount - amount * eased})`, transformOrigin: '50% 45%'};
}
