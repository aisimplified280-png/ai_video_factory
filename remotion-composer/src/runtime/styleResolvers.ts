import type {CSSProperties} from 'react';
import {appear} from '../motion/appear';
import {compare} from '../motion/compare';
import {connect} from '../motion/connect';
import {count} from '../motion/count';
import {focus} from '../motion/focus';
import {grow} from '../motion/grow';
import {move} from '../motion/move';
import {pulse} from '../motion/pulse';
import {reveal} from '../motion/reveal';
import {trace} from '../motion/trace';
import {transform} from '../motion/transform';
import {focusShift} from '../camera/focusShift';
import {pan} from '../camera/pan';
import {pullOut} from '../camera/pullOut';
import {pushIn} from '../camera/pushIn';
import {staticCamera} from '../camera/static';
import {tracking} from '../camera/tracking';
import {zoom} from '../camera/zoom';
import {incomingStyle as blurIn, outgoingStyle as blurOut} from '../transitions/motionBlur';
import {incomingStyle as fadeIn} from '../transitions/fade';
import {incomingStyle as wipeIn} from '../transitions/wipe';
import {incomingStyle as zoomIn, outgoingStyle as zoomOut} from '../transitions/zoom';
import {incomingStyle as objectIn, outgoingStyle as objectOut} from '../transitions/objectTransition';
import {incomingStyle as morphIn, outgoingStyle as morphOut} from '../transitions/shapeMorph';
import {incomingStyle as matchIn, outgoingStyle as matchOut} from '../transitions/matchCut';
import {incomingStyle as slideIn, outgoingStyle as slideOut} from '../transitions/slide';
import {enterState, exitState} from './eventTiming';

/**
 * Resolve every canonical transition intent to its executing module.
 * match_cut executes as a precise hard cut with matched framing; the match
 * itself was decided upstream and is never invented here.
 */
export function transitionModuleFor(intent: string | null): string {
  switch (intent) {
    case 'hard_cut':
      return 'hardCut';
    case 'fade':
    case 'cross_dissolve':
      return 'fade';
    case 'directional_wipe':
      return 'wipe';
    case 'object_transition':
      return 'objectTransition';
    case 'zoom_transition':
      return 'zoom';
    case 'shape_morph':
      return 'shapeMorph';
    case 'light_flash':
      return 'lightFlash';
    case 'motion_blur':
      return 'motionBlur';
    case 'match_cut':
      return 'matchCut';
    case 'slide_transition':
      return 'slide';
    default:
      return 'hardCut';
  }
}

/**
 * Intent resolvers. Every canonical intent maps to exactly one implementation;
 * scene semantics choose the intent, never the component.
 *
 * Static is the default (§5): a missing or unknown intent holds the element
 * perfectly still — it must never fall through to a rise-and-fade reveal.
 */
export function motionStyle(intent: string | null, progress: number): CSSProperties {
  switch (intent) {
    case 'emerge':
      return appear(progress);
    case 'assemble':
    case 'expand':
      return grow(progress);
    case 'collapse':
      return {transform: `scale(${1 - 0.4 * progress})`, opacity: 1 - progress * 0.5};
    case 'connect':
      return connect(progress);
    case 'flow':
    case 'travel':
      return move(progress);
    case 'pulse':
      return pulse(progress);
    case 'transform':
      return transform(progress);
    case 'trace':
      return trace(progress).style;
    case 'count':
      return appear(progress);
    case 'compare':
      return compare(progress, 'left');
    case 'focus':
      return focus(progress);
    case 'reorder':
    case 'reveal':
      return reveal(progress);
    default:
      return {};
  }
}

export function cameraStyle(intent: string | null, progress: number): CSSProperties {
  switch (intent) {
    case 'pull_out':
    case 'pullOut':
    case 'crane_pull_out':
      return pullOut(progress, 0.03);
    case 'reveal_space':
    case 'approach_subject':
    case 'pushIn':
    case 'fast_push_in':
    case 'push_in':
      return pushIn(progress, 0.03);
    case 'expand_scale':
    case 'zoom':
    case 'dolly_through':
      return pushIn(progress, 0.04);
    case 'follow_subject':
    case 'tracking':
    case 'overhead_track':
      return tracking(progress);
    case 'shift_focus':
    case 'focusShift':
    case 'focus_shift':
      return focusShift(progress);
    case 'cross_system':
    case 'pan':
    case 'lateral_pan':
    case 'lateral_tracking':
      return pan(progress, 'x', 24);
    case 'tilt':
    case 'crane_down':
    case 'crane_up':
      return pan(progress, 'y', 24);
    case 'observe_static':
    case 'steady_breathing':
    case 'static':
    default:
      return staticCamera();
  }
}

/** Camera, motion, transition, and depth transforms combine; none overwrites another. */
export function mergeStyles(...styles: (CSSProperties | undefined)[]): CSSProperties {
  const merged: CSSProperties = {};
  for (const style of styles) {
    if (!style) {
      continue;
    }
    const {transform, ...rest} = style;
    Object.assign(merged, rest);
    if (transform) {
      merged.transform = merged.transform ? `${merged.transform} ${transform}` : String(transform);
    }
  }
  return merged;
}

/**
 * Entrance style for the first `overlap` frames of an event.
 * Each element waits its stagger turn (enterState), then enters with a
 * role-specific move (content rises, details scale in) — never the whole
 * frame sliding as one unit. The progress reaches 1 on the last visible
 * entrance frame, so the incoming element is stable while still on screen.
 *
 * The default cross-dissolve (fade module) is opacity-only on every role:
 * vertical movement and scale are reserved for explicitly selected
 * slide_transition boundaries.
 */
export function headStyleFor(intent: string | null, overlap: number, local: number, role = ''): CSSProperties {
  if (overlap <= 0 || local >= overlap) {
    return {};
  }
  const state = enterState(local, overlap, role);
  if (state.hidden) {
    return {opacity: 0};
  }
  const p = state.p;
  if (transitionModuleFor(intent) === 'fade') {
    return {opacity: p};
  }
  const base = (() => {
    switch (transitionModuleFor(intent)) {
      case 'wipe':
        return wipeIn(p);
      case 'zoom':
        return zoomIn(p);
      case 'objectTransition':
        return objectIn(p);
      case 'shapeMorph':
        return morphIn(p);
      case 'motionBlur':
        return blurIn(p);
      case 'matchCut':
        return matchIn(p);
      case 'slide':
        return slideIn(p);
      default:
        return {};
    }
  })();
  const opacity = base.opacity ?? p;
  if (base.transform) {
    return {...base, opacity};
  }
  if (role === 'character') {
    // The mascot's spring entrance owns its motion — fade only.
    return {opacity};
  }
  if (role === 'foreground' || role === 'diagram' || role === 'overlay') {
    return {opacity, transform: `scale(${(0.93 + 0.07 * p).toFixed(4)})`};
  }
  return {opacity, transform: `translateY(${((1 - p) * 46).toFixed(1)}px)`};
}

/**
 * Exit style while an event lends its tail to the next entrance.
 * exitState guarantees progress reaches 1 on the event's LAST visible frame,
 * so the outgoing element finishes its exit before its parent scene unmounts
 * (no full-opacity hold followed by an abrupt boundary cut).
 *
 * The default cross-dissolve (fade module) is a matched opacity-only fade on
 * both sides — no upward drift, no scale, no asymmetry.
 */
export function tailStyleFor(intent: string | null, tail: number, intoTail: number, role = ''): CSSProperties {
  if (tail <= 0) {
    return {};
  }
  const state = exitState(intoTail, tail, role);
  if (!state.active) {
    return {};
  }
  const q = state.q;
  if (transitionModuleFor(intent) === 'fade') {
    return {opacity: 1 - q};
  }
  switch (transitionModuleFor(intent)) {
    case 'zoom':
      return zoomOut(q);
    case 'objectTransition':
      return objectOut(q);
    case 'shapeMorph':
      return morphOut(q);
    case 'motionBlur':
      return blurOut(q);
    case 'matchCut':
      return matchOut(q);
    case 'slide':
      return slideOut(q);
    default:
      return {};
  }
}
