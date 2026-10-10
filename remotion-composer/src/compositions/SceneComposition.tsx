import React from 'react';
import {AbsoluteFill, Audio, Sequence, staticFile, useCurrentFrame} from 'remotion';
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
import {flashStyle} from '../transitions/lightFlash';
import {incomingStyle as wipeIn} from '../transitions/wipe';
import {incomingStyle as zoomIn, outgoingStyle as zoomOut} from '../transitions/zoom';
import {incomingStyle as objectIn, outgoingStyle as objectOut} from '../transitions/objectTransition';
import {incomingStyle as morphIn, outgoingStyle as morphOut} from '../transitions/shapeMorph';
import {incomingStyle as matchIn, outgoingStyle as matchOut} from '../transitions/matchCut';
import {incomingStyle as slideIn, outgoingStyle as slideOut} from '../transitions/slide';
import {ActionLayer} from '../primitives/ActionLayer';
import {CharacterLayer} from '../primitives/CharacterLayer';
import {ChartLayer} from '../primitives/ChartLayer';
import {DiagramLayer} from '../primitives/DiagramLayer';
import {ImageLayer} from '../primitives/ImageLayer';
import {LineLayer} from '../primitives/LineLayer';
import {MetricLayer} from '../primitives/MetricLayer';
import {ShapeLayer} from '../primitives/ShapeLayer';
import {SvgLayer} from '../primitives/SvgLayer';
import {TextLayer} from '../primitives/TextLayer';
import {VideoLayer} from '../primitives/VideoLayer';
import {assetById, requireAssetUrl} from '../runtime/loader';
import type {AssetProps, AudioRefProps, CharacterSpec, EditEventProps, SceneProps, ThemeProps} from '../runtime/props';
import {enterState, exitState, frameState, type PlacedTiming} from '../runtime/eventTiming';
import {ownsOwnMotion} from '../runtime/motionOwnership';

/** True when this scene is the closing call-to-action scene. */
export function isCtaScene(scene: SceneProps): boolean {
  return scene.narrative_role?.toLowerCase() === 'cta' || Boolean(scene.scene_id?.toLowerCase().includes('cta'));
}

/**
 * Canvas anchor of the subscribe control inside the CTA card.
 * Must stay in sync with the CTA card layout rendered in SceneComposition.
 */
export function ctaSubscribeAnchor(width: number, height: number): {x: number; y: number} {
  return {x: width * 0.5, y: height * 0.854};
}

/**
 * On the CTA the mascot performs exactly one deliberate tap on the subscribe control
 * and then holds still. The target is the real rendered control, not a generic point.
 */
export function ctaMascotSpec(spec: CharacterSpec, width: number, height: number): CharacterSpec {
  return {
    ...spec,
    pose: 'point_tap_subscribe',
    action: 'tapping the subscribe control',
    target: 'subscribe control',
    target_anchor: ctaSubscribeAnchor(width, height),
    tool_held: null,
    motion: 'interact',
    emotion: 'celebrate',
    z_index: 120,
  };
}

export interface PlacedEvent {
  event: EditEventProps;
  from: number;
  duration: number;
  /** Entrance overlap frames borrowed from the previous event. */
  head: number;
  /** Extra tail frames lent to the next event's entrance. */
  tail: number;
  flashFrames: number;
}

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

export interface PlacedAudio {
  clip: AudioRefProps;
  from: number;
  duration: number;
}

export interface SceneBoundaryTransition {
  from_scene: string;
  to_scene: string;
  intent: string;
  overlap_frames: number;
  outgoing_motion: string;
  incoming_motion: string;
}

export interface SceneCompositionProps {
  scene: SceneProps;
  placed: PlacedEvent[];
  assets: AssetProps[];
  audio: PlacedAudio[];
  theme: ThemeProps;
  fps: number;
  width: number;
  height: number;
  ctaBranding: string;
  isAITopic?: boolean;
  boundaryTransition?: SceneBoundaryTransition | null;
}

/**
 * Intent resolvers. Every canonical intent maps to exactly one implementation;
 * scene semantics choose the intent, never the component.
 */
export function motionStyle(intent: string | null, progress: number): React.CSSProperties {
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
    default:
      return reveal(progress);
  }
}

export function cameraStyle(intent: string | null, progress: number): React.CSSProperties {
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
export function mergeStyles(...styles: (React.CSSProperties | undefined)[]): React.CSSProperties {
  const merged: React.CSSProperties = {};
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

function LayerContent({event, assets, theme, scene, ctaBranding, width, height, progress, isAITopic}: {
  event: EditEventProps;
  assets: AssetProps[];
  theme: ThemeProps;
  scene: SceneProps;
  ctaBranding: string;
  width: number;
  height: number;
  progress: number;
  isAITopic?: boolean;
}) {
  const asset = assetById(assets, event.asset_id);
  switch (event.role) {
    case 'primary_visual':
    case 'primary_composite':
    case 'midground':
    case 'secondary_visual': {
      if (!asset) {
        throw new Error(`Event ${event.event_id} requires an asset but references none.`);
      }
      const spec = (asset.nativeSpec ?? {}) as {
        nodes?: {id: string; label: string; x: number; y: number; details?: string[]; primary?: boolean; w?: number; h?: number; node_type?: string; shape_style?: string; icon?: string}[];
        connectors?: {from: string; to: string; label?: string; relationship?: string}[];
        bars?: {label: string; value: number}[];
        shapes?: {shape: 'circle' | 'rect' | 'line'; x: number; y: number; size: number; length?: number; color: string}[];
        path?: string;
      };
      if (asset.kind === 'video') {
        return <VideoLayer src={requireAssetUrl(asset)} />;
      }
      if (asset.kind === 'image-still') {
        // Declared video, delivered still: full camera motion, no playback.
        return <ImageLayer src={requireAssetUrl(asset)} framing={event.framing} />;
      }
      if (asset.kind === 'svg') {
        return <SvgLayer src={requireAssetUrl(asset)} />;
      }
      if (asset.kind === 'diagram' || spec.nodes) {
        return (
          <DiagramLayer
            theme={theme}
            width={width}
            height={height}
            nodes={(spec.nodes ?? []).map((node, index) => ({...node, x: node.x || width / 2, y: node.y || 300 + index * 260}))}
            connectors={spec.connectors ?? []}
            /* Element entrance completes within the first ~12% of the scene (~0.6s):
             * visuals are on screen while the narrator is already saying them. */
            reveal={event.motion_intent === 'assemble' || event.motion_intent === 'connect' ? Math.min(1, progress / 0.12) : 1}
          />
        );
      }
      if (asset.kind === 'chart' || spec.bars) {
        const bars = spec.bars ?? [];
        return <ChartLayer theme={theme} bars={bars} reveal={count(progress, Math.max(1, bars.length)) / Math.max(1, bars.length)} />;
      }
      if (spec.shapes) {
        return <ShapeLayer width={width} height={height} shapes={spec.shapes} />;
      }
      if (spec.path || event.motion_intent === 'trace') {
        return <LineLayer width={width} height={height} reveal={trace(progress).reveal} color={theme.accent} path={spec.path} />;
      }
      return <ImageLayer src={requireAssetUrl(asset)} framing={event.framing} />;
    }
    case 'character': {
      const baseSpec = event.character_spec ?? scene.character_spec;
      const charSpec = baseSpec && isCtaScene(scene) ? ctaMascotSpec(baseSpec, width, height) : baseSpec;
      if (charSpec) {
        return (
          <CharacterLayer
            spec={charSpec}
            progress={progress}
            width={width}
            height={height}
            theme={theme}
          />
        );
      }
      if (asset) {
        return <ImageLayer src={requireAssetUrl(asset)} framing={event.framing} />;
      }
      return null;
    }
    case 'foreground': {
      if (asset) {
        return <ImageLayer src={requireAssetUrl(asset)} framing={event.framing} />;
      }
      return null;
    }
    case 'diagram': {
      if (!asset) {
        throw new Error(`Diagram event ${event.event_id} references no asset.`);
      }
      const spec = (asset.nativeSpec ?? {}) as {nodes?: {id: string; label: string; x: number; y: number; details?: string[]; primary?: boolean; w?: number; h?: number}[]; connectors?: {from: string; to: string; label?: string}[]};
      return (
        <DiagramLayer
          theme={theme}
          width={width}
          height={height}
          nodes={(spec.nodes ?? []).map((node, index) => ({...node, x: node.x || width / 2, y: node.y || 300 + index * 260}))}
          connectors={spec.connectors ?? []}
          reveal={Math.min(1, progress / 0.4)}
        />
      );
    }
    case 'metric':
      return null;
    case 'brand':
      return null;
    case 'overlay':
      return null;
    case 'background':
      // The canvas is constant for the whole video (rendered globally) —
      // background events never paint per scene.
      return null;
    case 'caption':
      return null;
    default:
      throw new Error(`Unsupported semantic layer role: ${event.role}`);
  }
}

/**
 * Entrance style for the first `overlap` frames of an event.
 * Each element waits its stagger turn (enterState), then enters with a
 * role-specific move (content rises, details scale in) — never the whole
 * frame sliding as one unit. The progress reaches 1 on the last visible
 * entrance frame, so the incoming element is stable while still on screen.
 */
function headStyleFor(intent: string | null, overlap: number, local: number, role = ''): React.CSSProperties {
  if (overlap <= 0 || local >= overlap) {
    return {};
  }
  const state = enterState(local, overlap, role);
  if (state.hidden) {
    return {opacity: 0};
  }
  const p = state.p;
  const base = (() => {
    switch (transitionModuleFor(intent)) {
      case 'fade':
        return fadeIn(p);
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
 */
function tailStyleFor(intent: string | null, tail: number, intoTail: number, role = ''): React.CSSProperties {
  if (tail <= 0) {
    return {};
  }
  const state = exitState(intoTail, tail, role);
  if (!state.active) {
    return {};
  }
  const q = state.q;
  if (transitionModuleFor(intent) === 'fade') {
    if (role === 'foreground' || role === 'diagram' || role === 'overlay') {
      return {opacity: 1 - q, transform: `scale(${(1 - 0.07 * q).toFixed(4)})`};
    }
    if (role === 'character') {
      return {opacity: 1 - q};
    }
    return {opacity: 1 - q, transform: `translateY(${(-30 * q).toFixed(1)}px)`};
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

/** Executes one scene's placed events in z-order. Multi-layer by construction. */
export const SceneComposition: React.FC<SceneCompositionProps> = ({
  scene,
  placed,
  assets,
  audio,
  theme,
  fps,
  width,
  height,
  ctaBranding,
  isAITopic = false,
  boundaryTransition = null,
}) => {
  const frame = useCurrentFrame();
  const ordered = [...placed].sort((a, b) => a.event.z_index - b.event.z_index);
  const sceneDurationFrames = Math.max(1, Math.round((scene.end - scene.start) * fps));
  const sceneProgress = Math.min(1, Math.max(0, frame / sceneDurationFrames));

  // §17 CTA choreography — one short deliberate sequence, then a stable branded ending:
  // 0.00–0.125 composition appears | 0.12–0.32 mascot taps the control | 0.30–0.40 control responds | 0.40+ settles.
  const ctaScene = isCtaScene(scene);
  const ctaAppear = Math.min(1, sceneProgress / 0.08);
  const ctaPress =
    ctaScene && sceneProgress >= 0.3 && sceneProgress < 0.4
      ? sceneProgress < 0.35
        ? (sceneProgress - 0.3) / 0.05
        : 1 - (sceneProgress - 0.35) / 0.05
      : 0;
  const ctaSubscribed = ctaScene && sceneProgress >= 0.4;
  const ctaButtonScale = 1 - 0.08 * ctaPress;
  // YouTube-red affordance pre-click (universal recognition), green resolved state.
  const ctaButtonBg = ctaSubscribed ? '#16A34A' : ctaPress > 0 ? '#CC0000' : '#FF0000';
  const ctaMascotSpecResolved =
    scene.character_spec && ctaScene ? ctaMascotSpec(scene.character_spec, width, height) : scene.character_spec;

  // §26 upgraded ending choreography — one energetic but deterministic sequence,
  // everything settled by ~0.76 so the final hold is a clean branded still.
  const clamp01 = (v: number) => Math.min(1, Math.max(0, v));
  const ctaSettle = 1 + 0.05 * Math.sin(Math.PI * clamp01(sceneProgress / 0.14));
  const cursorT = clamp01((sceneProgress - 0.16) / 0.12);
  const cursorVisible = ctaScene && sceneProgress >= 0.16 && sceneProgress < 0.46;
  const cursorPress = sceneProgress >= 0.3 && sceneProgress < 0.4 ? 1 - Math.abs(sceneProgress - 0.35) / 0.05 : 0;
  const cursorFade = sceneProgress >= 0.4 ? clamp01((sceneProgress - 0.4) / 0.06) : 0;
  const ripple = ctaScene && sceneProgress >= 0.34 && sceneProgress <= 0.66 ? (sceneProgress - 0.34) / 0.32 : -1;
  const confettiT = ctaScene && sceneProgress >= 0.4 && sceneProgress <= 0.9 ? (sceneProgress - 0.4) / 0.5 : -1;
  const bellSwing =
    ctaScene && sceneProgress >= 0.42 && sceneProgress <= 0.68
      ? 18 * Math.sin((sceneProgress - 0.42) * 52) * Math.max(0, 1 - (sceneProgress - 0.42) * 5.5)
      : 0;
  const bellPop = ctaScene && sceneProgress >= 0.42 && sceneProgress < 0.54 ? Math.sin(((sceneProgress - 0.42) / 0.12) * Math.PI) : 0;
  const underlineT = clamp01((sceneProgress - 0.55) / 0.18);
  const buttonGlow = ctaSubscribed && sceneProgress < 0.62 ? clamp01((sceneProgress - 0.4) / 0.05) * (1 - clamp01((sceneProgress - 0.5) / 0.12)) : 0;
  const ctaAnchor = ctaSubscribeAnchor(width, height);
  const cursorTipX = ctaAnchor.x + 10 + (1 - cursorT) * 170;
  const cursorTipY = ctaAnchor.y + 4 + (1 - cursorT) * 210;

  return (
    <AbsoluteFill>
      {ordered.map(({event, from, duration, head, tail, flashFrames}, index) => {
        // Placement math lives in runtime/eventTiming (behavior-tested): the
        // rendered length is duration + ONE tail, and the exit window starts
        // at the event's true end so it is fully visible before unmount.
        const timing: PlacedTiming = {from, duration, head, tail};
        const {total, local, progress, inTail, intoTail} = frameState(frame, timing);
        const next = ordered[index + 1];
        // One motion owner per element (§5): ownsOwnMotion() is the decision —
        // the mascot owns all of its motion and a native diagram owns its own
        // reveal, so their wrappers receive only entrance/exit styling.
        // Everything else is static unless a canonical intent says otherwise.
        const selfOwned = ownsOwnMotion(event.role, assetById(assets, event.asset_id));
        const style = mergeStyles(
          selfOwned ? undefined : cameraStyle(event.camera_intent, progress),
          selfOwned ? undefined : motionStyle(event.motion_intent, progress),
          headStyleFor(event.transition_in, head, local, event.role),
          inTail ? tailStyleFor(boundaryTransition?.intent ?? next?.event.transition_in ?? null, tail, intoTail, event.role) : undefined,
        );
        return (
          <Sequence key={event.event_id} from={from} durationInFrames={total} name={event.event_id}>
            <AbsoluteFill style={style}>
              <LayerContent
                event={event}
                assets={assets}
                theme={theme}
                scene={scene}
                ctaBranding={ctaBranding}
                width={width}
                height={height}
                progress={progress}
                isAITopic={isAITopic}
              />
            </AbsoluteFill>
            {local < flashFrames ? <AbsoluteFill style={flashStyle(flashFrames <= 1 ? 1 : local / (flashFrames - 1))} /> : null}
          </Sequence>
        );
      })}

      {ctaMascotSpecResolved && !ordered.some((item) => item.event.role === 'character') && (
        <CharacterLayer
          spec={ctaMascotSpecResolved}
          progress={sceneProgress}
          width={width}
          height={height}
          theme={theme}
        />
      )}

      {!ordered.some((item) => (item.event.role === 'primary_visual' || item.event.role === 'midground') && Boolean(item.event.asset_id) && !item.event.overlay_disabled) && (
        <div
          style={{
            width: '100%',
            height: '100%',
            // No default page-level zoom: camera motion is decided per scene by
            // camera_intent; element motion lives inside the layers themselves.
            transform: 'none',
            transformOrigin: '50% 45%',
            pointerEvents: 'none',
          }}
        >
          <ActionLayer
            sceneId={scene.scene_id}
            subject={scene.subject}
            visualPurpose={scene.visual_purpose}
            progress={sceneProgress}
            width={width}
            height={height}
            theme={theme}
            isAITopic={isAITopic}
          />
        </div>
      )}

      {/* Channel brand lockup — logo mark + full channel name, set large above the
          subscribe card so the ending reads as a proper branded CTA. */}
      {ctaScene && (
        <div
          style={{
            position: 'absolute',
            bottom: 470,
            left: 0,
            right: 0,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 22,
            opacity: ctaAppear,
            transform: `translateY(${(1 - ctaAppear) * 24}px)`,
            zIndex: 100,
            pointerEvents: 'none',
          }}
        >
          <svg width={64} height={64} viewBox="0 0 46 46" aria-hidden>
            <defs>
              <linearGradient id="ctaWordmarkGrad" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stopColor="#3B82F6" />
                <stop offset="100%" stopColor="#1D4ED8" />
              </linearGradient>
            </defs>
            <rect x="1" y="1" width="44" height="44" rx="13" fill="url(#ctaWordmarkGrad)" />
            <rect x="1" y="1" width="44" height="44" rx="13" fill="none" stroke="rgba(255,255,255,0.25)" strokeWidth="2" />
            <path d="M11 33 L18.5 13 L23 13 L30.5 33" stroke="#FFFFFF" strokeWidth="4" strokeLinecap="round" strokeLinejoin="round" fill="none" />
            <path d="M14.6 26.5 H26.9" stroke="#FFFFFF" strokeWidth="4" strokeLinecap="round" />
            <circle cx="35.5" cy="14.5" r="4" fill="#F59E0B" />
          </svg>
          <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
            {/* Wordmark builds letter-by-letter AFTER the subscribe moment. */}
            <span
              style={{
                display: 'flex',
                fontFamily: theme.fontFamily,
                fontSize: 60,
                fontWeight: 800,
                letterSpacing: '0.13em',
                color: '#0F172A',
              }}
            >
              {ctaBranding.toUpperCase().split('').map((ch, i) => {
                const lp = clamp01((sceneProgress - (0.42 + i * 0.015)) / 0.12);
                return (
                  <span
                    key={`${i}-${ch}`}
                    style={{
                      display: 'inline-block',
                      whiteSpace: 'pre',
                      opacity: lp,
                      transform: `translateY(${((1 - lp) * 18).toFixed(1)}px) scale(${(0.8 + 0.2 * lp).toFixed(3)})`,
                    }}
                  >
                    {ch}
                  </span>
                );
              })}
            </span>
            {/* Underline sweep in brand colors — draws once, then holds. */}
            <div
              style={{
                height: 6,
                width: 620,
                maxWidth: '80vw',
                borderRadius: 3,
                marginTop: 10,
                background: 'linear-gradient(90deg, #3B82F6, #F59E0B)',
                transform: `scaleX(${underlineT.toFixed(3)})`,
                transformOrigin: 'left center',
                opacity: underlineT > 0 ? 1 : 0,
              }}
            />
          </div>
        </div>
      )}

      {ctaScene && (
        <div
          style={{
            position: 'absolute',
            bottom: 220,
            left: 80,
            right: 80,
            padding: '36px 44px',
            backgroundColor: 'rgba(15, 23, 42, 0.94)',
            borderRadius: 28,
            border: '2px solid rgba(59, 130, 246, 0.5)',
            boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.6)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 22,
            zIndex: 100,
            transform: `translateY(${(1 - ctaAppear) * 50}px) scale(${ctaSettle.toFixed(3)})`,
            opacity: ctaAppear,
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 14,
            }}
          >
            {/* Channel logo mark — rounded-square monogram with the brand's blue/amber accents. */}
            <svg width={46} height={46} viewBox="0 0 46 46" aria-hidden>
              <defs>
                <linearGradient id="ctaLogoGrad" x1="0" y1="0" x2="1" y2="1">
                  <stop offset="0%" stopColor="#3B82F6" />
                  <stop offset="100%" stopColor="#1D4ED8" />
                </linearGradient>
              </defs>
              <rect x="1" y="1" width="44" height="44" rx="13" fill="url(#ctaLogoGrad)" />
              <rect x="1" y="1" width="44" height="44" rx="13" fill="none" stroke="rgba(255,255,255,0.25)" strokeWidth="2" />
              <path d="M11 33 L18.5 13 L23 13 L30.5 33" stroke="#FFFFFF" strokeWidth="4" strokeLinecap="round" strokeLinejoin="round" fill="none" />
              <path d="M14.6 26.5 H26.9" stroke="#FFFFFF" strokeWidth="4" strokeLinecap="round" />
              <circle cx="35.5" cy="14.5" r="4" fill="#F59E0B" />
            </svg>
            <span
              style={{
                fontFamily: theme.fontFamily,
                fontSize: 26,
                fontWeight: 800,
                letterSpacing: '0.12em',
                color: '#F8FAFC',
                textTransform: 'uppercase',
              }}
            >
              {ctaBranding || 'AI SIMPLIFIED LAB'}
            </span>
          </div>

          {/* One deliberate response to the mascot tap, then a stable branded ending. */}
          <div
            style={{
              marginTop: 6,
              padding: '12px 36px',
              backgroundColor: ctaButtonBg,
              borderRadius: 999,
              color: '#FFFFFF',
              fontFamily: theme.fontFamily,
              fontSize: 22,
              fontWeight: 700,
              letterSpacing: '0.06em',
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              boxShadow: `0 8px 24px rgba(37, 99, 235, 0.45), 0 0 ${Math.round(34 * buttonGlow)}px rgba(74, 221, 128, ${(0.85 * buttonGlow).toFixed(2)})`,
              transform: `scale(${ctaButtonScale})`,
              transformOrigin: 'center center',
            }}
          >
            <span>{ctaSubscribed ? 'SUBSCRIBED' : 'SUBSCRIBE'}</span>
            <span style={{fontSize: 18}}>{ctaSubscribed ? '✓' : '▶'}</span>
          </div>
        </div>
      )}

      {/* Cursor click — arrives, presses with the button, then leaves. */}
      {ctaScene && cursorVisible && (
        <svg
          width="48"
          height="48"
          viewBox="0 0 24 24"
          style={{
            position: 'absolute',
            left: cursorTipX - 4,
            top: cursorTipY - 2,
            zIndex: 130,
            opacity: 1 - cursorFade,
            transform: `scale(${(1 - 0.18 * cursorPress).toFixed(3)})`,
            transformOrigin: '2px 2px',
            pointerEvents: 'none',
            filter: 'drop-shadow(0 4px 8px rgba(15, 23, 42, 0.45))',
          }}
        >
          <path d="M4 2 L20 12 L12.5 13.5 L9 21 Z" fill="#FFFFFF" stroke="#0F172A" strokeWidth="1.6" strokeLinejoin="round" />
        </svg>
      )}

      {/* Click ripple — two green rings from the control at the press moment. */}
      {ctaScene && ripple >= 0 && (
        <div style={{position: 'absolute', left: ctaAnchor.x, top: ctaAnchor.y, zIndex: 125, pointerEvents: 'none'}}>
          {[0, 0.16].map((off, k) => {
            const rt = Math.min(1, Math.max(0, (ripple - off) / 0.84));
            if (rt <= 0 || rt >= 1) {
              return null;
            }
            const size = 70 + rt * 420;
            return (
              <div
                key={k}
                style={{
                  position: 'absolute',
                  width: size,
                  height: size,
                  marginLeft: -size / 2,
                  marginTop: -size / 2,
                  borderRadius: '50%',
                  border: `4px solid rgba(22, 163, 74, ${(0.55 * (1 - rt)).toFixed(2)})`,
                }}
              />
            );
          })}
        </div>
      )}

      {/* Confetti burst — deterministic one-shot spray when the button flips green. */}
      {ctaScene && confettiT >= 0 && (
        <div style={{position: 'absolute', left: ctaAnchor.x, top: ctaAnchor.y, zIndex: 125, pointerEvents: 'none'}}>
          {Array.from({length: 16}).map((_, i) => {
            const angle = i * 2.3999632;
            const dist = 150 + (i % 5) * 48;
            const x = Math.cos(angle) * dist * confettiT;
            const y = Math.sin(angle) * dist * confettiT * 0.7 + 170 * confettiT * confettiT;
            const colors = ['#3B82F6', '#F59E0B', '#16A34A', '#1D4ED8', '#F8FAFC'];
            const op = confettiT < 0.6 ? 1 : Math.max(0, (1 - confettiT) / 0.4);
            return (
              <div
                key={i}
                style={{
                  position: 'absolute',
                  width: 10 + (i % 3) * 4,
                  height: 14 + (i % 4) * 4,
                  backgroundColor: colors[i % 5],
                  borderRadius: 3,
                  opacity: op * 0.95,
                  transform: `translate(${x.toFixed(1)}px, ${y.toFixed(1)}px) rotate(${i * 47 + confettiT * 430}deg)`,
                }}
              />
            );
          })}
        </div>
      )}

      {/* Notification bell — pops in at subscribe, rings once, then holds. */}
      {ctaScene && sceneProgress >= 0.42 && (
        <svg
          width="46"
          height="46"
          viewBox="0 0 24 24"
          style={{
            position: 'absolute',
            left: ctaAnchor.x + 148,
            top: ctaAnchor.y - 22,
            zIndex: 126,
            transform: `rotate(${bellSwing.toFixed(2)}deg) scale(${(1 + 0.25 * bellPop).toFixed(3)})`,
            pointerEvents: 'none',
            filter: 'drop-shadow(0 3px 6px rgba(15, 23, 42, 0.3))',
          }}
        >
          <path d="M12 3a6 6 0 0 0-6 6v3.6L4.4 16.4h15.2L18 12.6V9a6 6 0 0 0-6-6z" fill="#F59E0B" stroke="#B45309" strokeWidth="1.5" strokeLinejoin="round" />
          <path d="M10 18.6a2 2 0 0 0 4 0" stroke="#B45309" strokeWidth="1.5" fill="none" strokeLinecap="round" />
        </svg>
      )}
      {audio
        .filter((item) => item.clip.publicPath !== null)
        .map((item) => {
          const raw = item.clip.publicPath as string;
          const src = raw.startsWith('http://') || raw.startsWith('https://')
            ? raw
            : staticFile(raw);
          return (
            <Sequence key={item.clip.event_id} from={item.from} durationInFrames={item.duration}>
              <Audio src={src} />
            </Sequence>
          );
        })}
    </AbsoluteFill>
  );
};
