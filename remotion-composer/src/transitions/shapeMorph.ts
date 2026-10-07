import type {CSSProperties} from 'react';

/**
 * shape_morph: Dynamic geometric morph and aperture transformation.
 * Outgoing scene morphs inward toward an organic rounded aperture/pill,
 * and the incoming scene expands seamlessly outward from the morph geometry.
 */
export function overlapFrames(fps: number): number {
  return Math.round(fps * 0.35);
}

export function outgoingStyle(progress: number): CSSProperties {
  const t = Math.min(1, Math.max(0, progress));
  const easeIn = t * t;
  const radius = easeIn * 50; // Inset to circular boundary
  return {
    opacity: 1 - easeIn,
    transform: `scale(${1 - 0.25 * easeIn})`,
    borderRadius: `${radius}%`,
    clipPath: `inset(${easeIn * 15}% round ${radius}%)`,
  };
}

export function incomingStyle(progress: number): CSSProperties {
  const t = Math.min(1, Math.max(0, progress));
  const easeOut = 1 - Math.pow(1 - t, 3);
  const inv = 1 - easeOut;
  return {
    opacity: Math.min(1, easeOut * 1.8),
    transform: `scale(${0.88 + 0.12 * easeOut})`,
    borderRadius: `${inv * 40}%`,
    clipPath: `inset(${inv * 12}% round ${inv * 40}%)`,
  };
}
