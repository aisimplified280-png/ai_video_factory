import type {CSSProperties} from 'react';

/**
 * object_transition: Continuous semantic object transformation and kinetic handoff.
 * The outgoing hero subject undergoes a focal scale & rotational handoff,
 * while the incoming scene seamlessly emerges from the transferred focal center.
 */
export function overlapFrames(fps: number): number {
  return Math.round(fps * 0.35);
}

export function outgoingStyle(progress: number): CSSProperties {
  const t = Math.min(1, Math.max(0, progress));
  const easeOut = t * t * (3 - 2 * t);
  return {
    opacity: 1 - easeOut,
    transform: `scale(${1 - 0.18 * easeOut}) rotate(${-4 * easeOut}deg)`,
    filter: `blur(${easeOut * 4}px)`,
  };
}

export function incomingStyle(progress: number): CSSProperties {
  const t = Math.min(1, Math.max(0, progress));
  // Elastic ease-out for organic physical handoff
  const c4 = (2 * Math.PI) / 3;
  const eased = t === 0 ? 0 : t === 1 ? 1 : Math.pow(2, -10 * t) * Math.sin((t * 10 - 0.75) * c4) + 1;
  return {
    opacity: Math.min(1, t * 1.5),
    transform: `scale(${0.85 + 0.15 * eased}) rotate(${3 * (1 - t)}deg)`,
  };
}
