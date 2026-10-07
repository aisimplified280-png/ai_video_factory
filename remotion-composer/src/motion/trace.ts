import type {CSSProperties} from 'react';

/** trace: left-to-right clip reveal across the whole event. Drives LineLayer. */
export function trace(progress: number): {reveal: number; style: CSSProperties} {
  const t = Math.min(1, Math.max(0, progress));
  return {
    reveal: t,
    style: {clipPath: `inset(0 ${100 - t * 100}% 0 0)`, opacity: t > 0 ? 1 : 0},
  };
}
