import type {CSSProperties} from 'react';

/** reveal_space / approach_subject: slow push from 1.0 to `amount`. */
export function pushIn(progress: number, amount = 0.12): CSSProperties {
  const t = Math.min(1, Math.max(0, progress));
  const eased = 1 - Math.pow(1 - t, 2);
  return {transform: `scale(${1 + amount * eased})`, transformOrigin: '50% 55%'};
}
