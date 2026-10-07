import type {CSSProperties} from 'react';

/** Per-depth-layer transform. Background moves least, foreground most. */
export function parallax(progress: number, depth: 'background' | 'midground' | 'foreground' = 'midground'): CSSProperties {
  const t = Math.min(1, Math.max(0, progress));
  const rate = depth === 'background' ? 20 : depth === 'foreground' ? 90 : 50;
  return {transform: `translateY(${-rate / 2 + rate * t}px) scale(${depth === 'foreground' ? 1.04 : 1})`};
}
