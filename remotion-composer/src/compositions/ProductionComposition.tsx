import React from 'react';
import {AbsoluteFill, Sequence, useCurrentFrame} from 'remotion';
import {CaptionTrack} from '../captions/CaptionTrack';
import {BackgroundLayer} from '../primitives/BackgroundLayer';
import {MilestoneTabs} from '../primitives/MilestoneTabs';
import {overlapFrames as blurOverlap} from '../transitions/motionBlur';
import {overlapFrames as fadeOverlap} from '../transitions/fade';
import {overlapFrames as flashOverlap} from '../transitions/lightFlash';
import {overlapFrames as wipeOverlap} from '../transitions/wipe';
import {overlapFrames as zoomOverlap} from '../transitions/zoom';
import {overlapFrames as objectOverlap} from '../transitions/objectTransition';
import {overlapFrames as morphOverlap} from '../transitions/shapeMorph';
import {overlapFrames as matchOverlap} from '../transitions/matchCut';
import {overlapFrames as slideOverlap} from '../transitions/slide';
import {eventFrames} from '../runtime/timeline';
import {placeEvent} from '../runtime/eventTiming';
import {assertValidProps} from '../runtime/validators';
import type {EditEventProps, ProductionCompositionProps} from '../runtime/props';
import {SceneComposition, type PlacedAudio, type PlacedEvent, type SceneBoundaryTransition} from './SceneComposition';
import {transitionModuleFor} from '../runtime/styleResolvers';

/** Overlap borrowed from the outgoing event for an incoming transition. */
export function transitionOverlapFrames(intent: string | null, fps: number): number {
  switch (transitionModuleFor(intent)) {
    case 'fade':
      return fadeOverlap(fps);
    case 'wipe':
      return wipeOverlap(fps);
    case 'zoom':
      return zoomOverlap(fps);
    case 'lightFlash':
      return flashOverlap(fps);
    case 'motionBlur':
      return blurOverlap(fps);
    case 'objectTransition':
      return objectOverlap(fps);
    case 'shapeMorph':
      return morphOverlap(fps);
    case 'matchCut':
      return matchOverlap(fps);
    case 'slide':
      return slideOverlap(fps);
    case 'hardCut':
    default:
      return 0;
  }
}

/**
 * Root timeline executor. Reads placement, timing, layers, camera, motion,
 * transitions, and captions exclusively from edit_decisions; scene_plan
 * supplies semantic meaning; the manifest supplies media. Nothing editorial
 * is decided here.
 */
export const ProductionComposition: React.FC<ProductionCompositionProps> = (props) => {
  assertValidProps(props);
  const fps = props.platform.fps;
  const frame = useCurrentFrame();
  // The milestone bar is a chapter guide — it fades OUT as the CTA begins so
  // the ending has one clear focal point (no active chapter bar over the CTA).
  const ctaStartFrame = Math.round((props.cta.start ?? Number.MAX_SAFE_INTEGER) * fps);
  const tabsOpacity = frame >= ctaStartFrame ? Math.max(0, 1 - (frame - ctaStartFrame) / 8) : 1;
  const byScene = new Map<string, EditEventProps[]>();
  for (const event of [...props.events].sort((a, b) => a.z_index - b.z_index)) {
    const list = byScene.get(event.scene_id) ?? [];
    list.push(event);
    byScene.set(event.scene_id, list);
  }
  const sceneOrder = [...props.scenes].sort((a, b) => a.start - b.start);
  
  // Calculate first-class scene boundary transitions & cross-scene overlap tails
  const sceneTails = new Map<string, number>();
  const eventTails = new Map<string, number>();
  const boundaryMap = new Map<string, SceneBoundaryTransition>();
  for (let index = 0; index < sceneOrder.length - 1; index += 1) {
    const currScene = sceneOrder[index];
    const nextScene = sceneOrder[index + 1];
    const nextEvents = byScene.get(nextScene.scene_id) ?? [];
    const nextLead = nextEvents.find((e) => e.role === 'midground' || e.role === 'primary_visual') ?? nextEvents[0];
    const intent = nextLead?.transition_in ?? 'fade';
    const overlap = transitionOverlapFrames(intent, fps);
    const boundary: SceneBoundaryTransition = {
      from_scene: currScene.scene_id,
      to_scene: nextScene.scene_id,
      intent,
      overlap_frames: overlap,
      outgoing_motion: 'outgoing',
      incoming_motion: 'incoming',
    };
    boundaryMap.set(currScene.scene_id, boundary);
    sceneTails.set(currScene.scene_id, overlap);

    // Apply tail frames to currScene visual events (the mascot crossfades too).
    // The background never participates: the canvas is constant for the whole video.
    const currEvents = byScene.get(currScene.scene_id) ?? [];
    for (const evt of currEvents) {
      if (evt.role === 'midground' || evt.role === 'primary_visual' || evt.role === 'foreground' || evt.role === 'character') {
        eventTails.set(evt.event_id, overlap);
      }
    }
  }

  const flashes = new Map<string, number>();
  for (const event of props.events) {
    if (transitionModuleFor(event.transition_in) === 'lightFlash') {
      flashes.set(event.event_id, flashOverlap(fps));
    }
  }
  const isAITopic =
    props.productionId.toLowerCase().includes('ai') ||
    props.scenes.some(
      (s) =>
        /token|embedding|attention|transformer|nlp|language|neural|llm|deep learning|artificial intelligence/i.test(
          s.subject + ' ' + s.visual_purpose,
        ),
    ) ||
    props.captions.some((c) =>
      /token|embedding|attention|transformer|nlp|language model|prompt/i.test(c.textReference),
    );

  return (
    <AbsoluteFill style={{backgroundColor: isAITopic ? '#F8FAFC' : (props.theme.background || '#F8FAFC')}}>
      {/* One constant engineered canvas for the entire video — scenes never wipe it. */}
      <BackgroundLayer theme={props.theme} />
      {sceneOrder.map((scene) => {
        const sceneRange = eventFrames(scene.start, scene.end, fps);
        const sceneTail = sceneTails.get(scene.scene_id) ?? 0;
        const placed: PlacedEvent[] = (byScene.get(scene.scene_id) ?? []).map((event) => {
          const range = eventFrames(event.start, event.end, fps);
          const tail = eventTails.get(event.event_id) ?? 0;
          // TRUE event duration: the transition overlap is applied exactly once,
          // when the rendered sequence length is computed (renderedLength) —
          // never here. Adding it twice pushed exits past the parent's lifetime.
          const timing = placeEvent(
            range,
            sceneRange.startFrame,
            transitionOverlapFrames(event.transition_in, fps),
            tail,
          );
          return {event, ...timing, flashFrames: flashes.get(event.event_id) ?? 0};
        });
        const sceneAudio: PlacedAudio[] = props.audio
          .filter((clip) =>
            placed.some((item) => item.event.audio_ref === clip.event_id || clip.event_id.endsWith(scene.scene_id)),
          )
          .map((clip) => {
            const range = eventFrames(clip.start, clip.end, fps);
            return {clip, from: range.startFrame - sceneRange.startFrame, duration: range.frameCount};
          });
        const sceneDuration = sceneRange.frameCount + sceneTail;
        return (
          <Sequence key={scene.scene_id} from={sceneRange.startFrame} durationInFrames={sceneDuration} name={scene.scene_id}>
            <SceneComposition
              scene={scene}
              placed={placed}
              assets={props.assets}
              audio={sceneAudio}
              theme={props.theme}
              fps={fps}
              width={props.platform.resolution.width}
              height={props.platform.resolution.height}
              ctaBranding={props.cta.branding}
              isAITopic={isAITopic}
              boundaryTransition={boundaryMap.get(scene.scene_id) ?? null}
            />
          </Sequence>
        );
      })}
      {props.milestones && props.milestones.length >= 2 && tabsOpacity > 0 ? (
        <AbsoluteFill style={{opacity: tabsOpacity}}>
          <MilestoneTabs
            milestones={props.milestones}
            theme={props.theme}
            fps={fps}
            width={props.platform.resolution.width}
          />
        </AbsoluteFill>
      ) : null}
      <CaptionTrack
        theme={props.theme}
        captions={props.captions}
        fps={fps}
        mode="emphasis_words"
        ctaStart={props.cta.start ?? undefined}
      />
    </AbsoluteFill>
  );
};
