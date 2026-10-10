/**
 * Pure timing math for event placement, entrance and exit windows.
 *
 * Single source of truth shared by ProductionComposition (placement) and
 * SceneComposition (per-frame state), and behavior-tested end-to-end by
 * tests/test_remotion_transition_timing.py (compiled with tsc, executed by node).
 *
 * Invariant: an event's `duration` is its TRUE length. The transition overlap
 * is applied exactly once — when the rendered sequence length is computed —
 * never in the placement itself. That guarantees an outgoing element's exit
 * runs during real, visible frames before its parent scene unmounts.
 */

export interface PlacedTiming {
  /** Event start relative to its parent scene's first frame. */
  from: number;
  /** True event length in frames (NO overlap added). */
  duration: number;
  /** Entrance overlap length (frames). */
  head: number;
  /** Exit overlap length (frames); 0 = hard cut, no exit window. */
  tail: number;
}

export interface FrameState {
  /** Rendered sequence length: duration + tail (overlap counted once). */
  total: number;
  /** Frame index inside the event, clamped to [0, total - 1]. */
  local: number;
  /** 0..1 progress across the whole rendered lifetime. */
  progress: number;
  /** True while the exit window is active (local >= duration). */
  inTail: boolean;
  /** Frames into the exit window (0 when not in tail). */
  intoTail: number;
  /** True while the entrance window is active (local < head). */
  entering: boolean;
}

/** Place an event inside its scene. Duration stays true — overlap is NOT added. */
export function placeEvent(
  range: {startFrame: number; frameCount: number},
  sceneStartFrame: number,
  head: number,
  tail: number,
): PlacedTiming {
  return {
    from: range.startFrame - sceneStartFrame,
    duration: range.frameCount,
    head,
    tail,
  };
}

/** Rendered length of an event's Sequence: true duration + one overlap tail. */
export function renderedLength(timing: PlacedTiming): number {
  return timing.duration + timing.tail;
}

/** Rendered length of a scene's Sequence: scene length + one overlap tail. */
export function sceneLength(sceneFrameCount: number, sceneTail: number): number {
  return sceneFrameCount + sceneTail;
}

/** Per-frame state for one placed event. */
export function frameState(frame: number, timing: PlacedTiming): FrameState {
  const total = renderedLength(timing);
  const local = Math.min(Math.max(0, frame - timing.from), Math.max(0, total - 1));
  const progress = total <= 1 ? 1 : local / (total - 1);
  const inTail = timing.tail > 0 && local >= timing.duration;
  const intoTail = inTail ? local - timing.duration : 0;
  return {
    total,
    local,
    progress,
    inTail,
    intoTail,
    entering: local < timing.head,
  };
}

/** Entrance stagger: content leads, then mascot, then details. */
export function enterDelayFor(role: string): number {
  switch (role) {
    case 'midground':
    case 'primary_visual':
      return 0;
    case 'character':
      return 3;
    case 'foreground':
      return 5;
    default:
      return 2;
  }
}

/** Exit stagger (reverse order): details leave first, content holds longest. */
export function exitLeadFor(role: string): number {
  switch (role) {
    case 'foreground':
      return 0;
    case 'diagram':
    case 'overlay':
      return 2;
    case 'character':
      return 3;
    case 'midground':
    case 'primary_visual':
      return 5;
    default:
      return 3;
  }
}

export interface EntranceState {
  /** Element is waiting its stagger turn — must render fully hidden. */
  hidden: boolean;
  /** 0..1 entrance progress; reaches 1 on the LAST entrance frame. */
  p: number;
}

/**
 * Entrance progress for a frame inside the head window.
 * Completes exactly at local = head - 1 so the incoming element reaches its
 * stable layout while the entrance window is still visible.
 */
export function enterState(local: number, head: number, role: string): EntranceState {
  if (head <= 0) {
    return {hidden: false, p: 1};
  }
  const delay = Math.min(enterDelayFor(role), Math.max(0, head - 1));
  if (local >= head) {
    return {hidden: false, p: 1};
  }
  if (local < delay) {
    return {hidden: true, p: 0};
  }
  const span = Math.max(1, head - 1 - delay);
  return {hidden: false, p: Math.min(1, Math.max(0, (local - delay) / span))};
}

export interface ExitState {
  /** Exit styling is active for this frame. */
  active: boolean;
  /** 0..1 exit progress; reaches 1 on the LAST visible frame of the event. */
  q: number;
}

/**
 * Exit progress for a frame inside the tail window.
 * Completes exactly at intoTail = tail - 1 (the event's final visible frame),
 * so the outgoing element finishes its exit BEFORE its parent scene unmounts —
 * it never sits at full opacity and vanishes at the boundary.
 */
export function exitState(intoTail: number, tail: number, role: string): ExitState {
  if (tail <= 0) {
    return {active: false, q: 0};
  }
  const delay = Math.min(exitLeadFor(role), Math.max(0, tail - 1));
  if (intoTail < delay) {
    // Stagger turn not reached: element holds at full opacity.
    return {active: false, q: 0};
  }
  const span = Math.max(1, tail - 1 - delay);
  return {active: true, q: Math.min(1, Math.max(0, (intoTail - delay) / span))};
}
