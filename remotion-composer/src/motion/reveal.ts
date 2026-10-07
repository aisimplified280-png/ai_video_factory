import type {CSSProperties} from 'react';

/** reveal: vertical wipe-in combined with fade across the first 30%. */
export function reveal(progress: number): CSSProperties {
  const t = Math.min(1, Math.max(0, progress / 0.3));
  const eased = 1 - Math.pow(1 - t, 3);
  return {opacity: eased, transform: `translateY(${(1 - eased) * 60}px)`};
}
