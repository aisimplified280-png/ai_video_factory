import type {CSSProperties} from 'react';

/** pan / tilt / cross_system: lateral (or vertical) sweep across the event. */
export function pan(progress: number, axis: 'x' | 'y' = 'x', distance = 90): CSSProperties {
  const t = Math.min(1, Math.max(0, progress));
  const eased = t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;
  const offset = -distance / 2 + distance * eased;
  return {transform: axis === 'x' ? `translateX(${offset}px)` : `translateY(${offset}px)`};
}
