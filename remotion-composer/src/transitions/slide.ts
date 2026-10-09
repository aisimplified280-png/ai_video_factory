import type {CSSProperties} from 'react';

/**
 * slide_transition: sliding-physics push (state-machine feel).
 *
 * The incoming scene rises into place like an app switching tabs while the
 * outgoing scene drifts up and dissolves — content moves within one continuous
 * workspace instead of cutting. Used only where the director found the same
 * environment on both sides of the boundary.
 */
export function overlapFrames(fps: number): number {
  return Math.round(fps * 0.35);
}

const clamp01 = (progress: number) => Math.min(1, Math.max(0, progress));

export function incomingStyle(progress: number): CSSProperties {
  const p = clamp01(progress);
  // easeOutCubic: the slide settles quickly, never bounces.
  const eased = 1 - Math.pow(1 - p, 3);
  return {
    opacity: eased,
    transform: `translateY(${(1 - eased) * 54}px)`,
  };
}

export function outgoingStyle(progress: number): CSSProperties {
  const p = clamp01(progress);
  return {
    opacity: 1 - p,
    transform: `translateY(${-p * 26}px)`,
  };
}
