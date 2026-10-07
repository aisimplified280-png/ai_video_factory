import type {CSSProperties} from 'react';

/** light_flash: brief white flash bridging the cut. */
export function overlapFrames(fps: number): number {
  return Math.round(fps * 0.25);
}

/** 0..1 flash intensity peaking mid-transition. */
export function flashIntensity(progress: number): number {
  const t = Math.min(1, Math.max(0, progress));
  return Math.sin(t * Math.PI);
}

export function flashStyle(progress: number): CSSProperties {
  return {opacity: flashIntensity(progress) * 0.9, backgroundColor: '#FFFFFF'};
}
