import React from 'react';
import {AbsoluteFill, Audio, Sequence, useCurrentFrame} from 'remotion';
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
import {parallax} from '../camera/parallax';
import {pullOut} from '../camera/pullOut';
import {pushIn} from '../camera/pushIn';
import {staticCamera} from '../camera/static';
import {tracking} from '../camera/tracking';
import {zoom} from '../camera/zoom';
import {incomingStyle as blurIn, outgoingStyle as blurOut} from '../transitions/motionBlur';
import {incomingStyle as fadeIn, outgoingStyle as fadeOut} from '../transitions/fade';
import {flashStyle} from '../transitions/lightFlash';
import {incomingStyle as wipeIn} from '../transitions/wipe';
import {incomingStyle as zoomIn, outgoingStyle as zoomOut} from '../transitions/zoom';
import {ActionLayer} from '../primitives/ActionLayer';
import {BackgroundLayer} from '../primitives/BackgroundLayer';
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
import type {AssetProps, AudioRefProps, EditEventProps, SceneProps, ThemeProps} from '../runtime/props';

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
    case 'object_transition':
      return 'wipe';
    case 'zoom_transition':
    case 'shape_morph':
      return 'zoom';
    case 'light_flash':
      return 'lightFlash';
    case 'motion_blur':
      return 'motionBlur';
    case 'match_cut':
      return 'matchCut';
    default:
      return 'hardCut';
  }
}

export interface PlacedAudio {
  clip: AudioRefProps;
  from: number;
  duration: number;
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

function LayerContent({event, assets, theme, scene, ctaBranding, width, height, progress}: {
  event: EditEventProps;
  assets: AssetProps[];
  theme: ThemeProps;
  scene: SceneProps;
  ctaBranding: string;
  width: number;
  height: number;
  progress: number;
}) {
  const asset = assetById(assets, event.asset_id);
  switch (event.role) {
    case 'primary_visual':
    case 'secondary_visual': {
      if (!asset) {
        throw new Error(`Event ${event.event_id} requires an asset but references none.`);
      }
      const spec = (asset.nativeSpec ?? {}) as {
        nodes?: {id: string; label: string; x: number; y: number}[];
        connectors?: {from: string; to: string}[];
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
            reveal={event.motion_intent === 'assemble' || event.motion_intent === 'connect' ? progress : 1}
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
    case 'diagram': {
      if (!asset) {
        throw new Error(`Diagram event ${event.event_id} references no asset.`);
      }
      const spec = (asset.nativeSpec ?? {}) as {nodes?: {id: string; label: string; x: number; y: number}[]; connectors?: {from: string; to: string}[]};
      return (
        <DiagramLayer
          theme={theme}
          width={width}
          height={height}
          nodes={(spec.nodes ?? []).map((node, index) => ({...node, x: node.x || width / 2, y: node.y || 300 + index * 260}))}
          connectors={spec.connectors ?? []}
          reveal={progress}
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
      return (
        <BackgroundLayer
          theme={theme}
          environment={scene.environment}
          sceneId={scene.scene_id}
          subject={scene.subject}
          visualPurpose={scene.visual_purpose}
          progress={progress}
        />
      );
    case 'caption':
      return null;
    default:
      throw new Error(`Unsupported semantic layer role: ${event.role}`);
  }
}

/** Entrance style for the first `overlap` frames of an event. */
function headStyleFor(intent: string | null, overlap: number, local: number): React.CSSProperties {
  if (overlap <= 0 || local >= overlap) {
    return {};
  }
  const progress = local / Math.max(1, overlap);
  switch (transitionModuleFor(intent)) {
    case 'fade':
      return fadeIn(progress);
    case 'wipe':
      return wipeIn(progress);
    case 'zoom':
      return zoomIn(progress);
    case 'motionBlur':
      return blurIn(progress);
    default:
      return {};
  }
}

/** Exit style while an event lends its tail to the next entrance. */
function tailStyleFor(intent: string | null, tail: number, intoTail: number): React.CSSProperties {
  if (tail <= 0) {
    return {};
  }
  const progress = Math.min(1, Math.max(0, intoTail / Math.max(1, tail)));
  switch (transitionModuleFor(intent)) {
    case 'fade':
      return fadeOut(progress);
    case 'zoom':
      return zoomOut(progress);
    case 'motionBlur':
      return blurOut(progress);
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
}) => {
  const frame = useCurrentFrame();
  const ordered = [...placed].sort((a, b) => a.event.z_index - b.event.z_index);
  const layered = scene.depth_strategy && /background|midground|foreground/i.test(scene.depth_strategy);
  const sceneDurationFrames = Math.max(1, Math.round((scene.end - scene.start) * fps));
  const sceneProgress = Math.min(1, Math.max(0, frame / sceneDurationFrames));
  return (
    <AbsoluteFill>
      <BackgroundLayer
        theme={theme}
        environment={scene.environment}
        sceneId={scene.scene_id}
        subject={scene.subject}
        visualPurpose={scene.visual_purpose}
        progress={sceneProgress}
        isAITopic={isAITopic}
      />

      {ordered.map(({event, from, duration, head, tail, flashFrames}, index) => {
        const total = duration + tail;
        const local = Math.min(Math.max(0, frame - from), Math.max(0, total - 1));
        const progress = total <= 1 ? 1 : local / (total - 1);
        const inTail = local >= duration;
        const next = ordered[index + 1];
        const depth = layered ? (event.z_index >= 20 ? 'foreground' : event.z_index >= 10 ? 'midground' : 'background') : null;
        const style = mergeStyles(
          cameraStyle(event.camera_intent, progress),
          motionStyle(event.motion_intent, progress),
          headStyleFor(event.transition_in, head, local),
          inTail ? tailStyleFor(next?.event.transition_in ?? null, tail, local - duration) : undefined,
          depth ? parallax(progress, depth) : undefined,
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
              />
            </AbsoluteFill>
            {local < flashFrames ? <AbsoluteFill style={flashStyle(flashFrames <= 1 ? 1 : local / (flashFrames - 1))} /> : null}
          </Sequence>
        );
      })}

      <div
        style={{
          width: '100%',
          height: '100%',
          transform: `scale(${1 + sceneProgress * 0.05})`,
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
      {audio
        .filter((item) => item.clip.publicPath !== null)
        .map((item) => {
          return (
            <Sequence key={item.clip.event_id} from={item.from} durationInFrames={item.duration}>
              <Audio src={item.clip.publicPath as string} />
            </Sequence>
          );
        })}
    </AbsoluteFill>
  );
};
