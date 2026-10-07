import type {CSSProperties} from 'react';

/** move/flow/travel: steady horizontal drift across the whole event. */
export function move(progress: number, distance = 120): CSSProperties {
  const t = Math.min(1, Math.max(0, progress));
  return {transform: `translateX(${-distance / 2 + distance * t}px)`};
}
