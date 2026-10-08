import type {CSSProperties} from 'react';

/**
 * match_cut: Continuous subject-matched focal punch & seamless kinetic handoff.
 * Outgoing hero subject undergoes a rapid focal push & scale punch (1.0 -> 1.14),
 * while incoming scene catches the exact focal anchor (1.14 -> 1.0) with rapid opacity ramp.
 * Strictly non-static, non-cut transformative transition with dedicated overlap.
 */
export function overlapFrames(fps: number): number {
  return Math.round(fps * 0.25);
}

export function outgoingStyle(progress: number): CSSProperties {
  const t = Math.min(1, Math.max(0, progress));
  const easeIn = t * t * (3 - 2 * t);
  return {
    opacity: t > 0.8 ? Math.max(0, (1 - t) / 0.2) : 1,
    transform: `scale(${1 + 0.14 * easeIn})`,
    filter: `contrast(${1 + 0.12 * easeIn}) brightness(${1 + 0.08 * easeIn})`,
  };
}

export function incomingStyle(progress: number): CSSProperties {
  const t = Math.min(1, Math.max(0, progress));
  const easeOut = 1 - Math.pow(1 - t, 3);
  return {
    opacity: Math.min(1, easeOut * 2.5),
    transform: `scale(${1.14 - 0.14 * easeOut})`,
    filter: `contrast(${1.12 - 0.12 * easeOut}) brightness(${1.08 - 0.08 * easeOut})`,
  };
}

