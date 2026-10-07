/**
 * Frame-accurate schedule math. Pure functions over edit_decisions timing.
 * Edit decisions remain the timeline authority; this module only converts
 * seconds to frames deterministically.
 */

export interface FrameRange {
  startFrame: number;
  endFrame: number;
  frameCount: number;
}

export function secondsToFrames(seconds: number, fps: number): number {
  return Math.round(seconds * fps);
}

export function eventFrames(start: number, end: number, fps: number): FrameRange {
  const startFrame = secondsToFrames(start, fps);
  const endFrame = secondsToFrames(end, fps);
  return {startFrame, endFrame, frameCount: Math.max(1, endFrame - startFrame)};
}

export function totalFrames(totalDuration: number, fps: number): number {
  return Math.max(1, secondsToFrames(totalDuration, fps));
}

/** Local 0..1 progress of a frame within an event's frame range. */
export function eventProgress(frame: number, range: FrameRange): number {
  if (range.frameCount <= 1) {
    return 1;
  }
  const t = (frame - range.startFrame) / (range.frameCount - 1);
  return Math.min(1, Math.max(0, t));
}
