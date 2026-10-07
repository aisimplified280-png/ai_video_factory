import React from 'react';
import {AbsoluteFill, Sequence} from 'remotion';
import {CaptionTrack} from '../captions/CaptionTrack';
import {overlapFrames as blurOverlap} from '../transitions/motionBlur';
import {overlapFrames as fadeOverlap} from '../transitions/fade';
import {overlapFrames as flashOverlap} from '../transitions/lightFlash';
import {overlapFrames as wipeOverlap} from '../transitions/wipe';
import {overlapFrames as zoomOverlap} from '../transitions/zoom';
import {eventFrames} from '../runtime/timeline';
import {assertValidProps} from '../runtime/validators';
import type {EditEventProps, ProductionCompositionProps} from '../runtime/props';
import {SceneComposition, transitionModuleFor, type PlacedAudio, type PlacedEvent} from './SceneComposition';

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
    case 'matchCut':
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
  const primaries = [...props.events]
    .filter((event) => event.role === 'primary_visual')
    .sort((a, b) => a.start - b.start);
  const byScene = new Map<string, EditEventProps[]>();
  for (const event of [...props.events].sort((a, b) => a.z_index - b.z_index)) {
    const list = byScene.get(event.scene_id) ?? [];
    list.push(event);
    byScene.set(event.scene_id, list);
  }
  const sceneOrder = [...props.scenes].sort((a, b) => a.start - b.start);
  // Tail frames: each primary event lends its tail to the next event's entrance.
  const tails = new Map<string, number>();
  for (let index = 0; index < primaries.length - 1; index += 1) {
    tails.set(primaries[index].event_id, transitionOverlapFrames(primaries[index + 1].transition_in, fps));
  }
  const flashes = new Map<string, number>();
  for (const event of primaries) {
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
      {sceneOrder.map((scene) => {
        // Each scene owns exactly its own time range: backgrounds and events
        // from one scene can never cover another scene's content. Event
        // placement below is scene-relative; the wrapping Sequence restores
        // absolute timing.
        const sceneRange = eventFrames(scene.start, scene.end, fps);
        const placed: PlacedEvent[] = (byScene.get(scene.scene_id) ?? []).map((event) => {
          const range = eventFrames(event.start, event.end, fps);
          return {
            event,
            from: range.startFrame - sceneRange.startFrame,
            duration: range.frameCount,
            head: transitionOverlapFrames(event.transition_in, fps),
            tail: tails.get(event.event_id) ?? 0,
            flashFrames: flashes.get(event.event_id) ?? 0,
          };
        });
        const sceneAudio: PlacedAudio[] = props.audio
          .filter((clip) =>
            placed.some((item) => item.event.audio_ref === clip.event_id || clip.event_id.endsWith(scene.scene_id)),
          )
          .map((clip) => {
            const range = eventFrames(clip.start, clip.end, fps);
            return {clip, from: range.startFrame - sceneRange.startFrame, duration: range.frameCount};
          });
        const lastPrimary = [...placed].reverse().find((item) => item.event.role === 'primary_visual');
        const sceneDuration = sceneRange.frameCount + (lastPrimary ? tails.get(lastPrimary.event.event_id) ?? 0 : 0);
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
            />
          </Sequence>
        );
      })}
      <CaptionTrack theme={props.theme} captions={props.captions} fps={fps} mode="emphasis_words" />
    </AbsoluteFill>
  );
};
