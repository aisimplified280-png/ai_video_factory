import React from 'react';
import {AbsoluteFill, Sequence} from 'remotion';
import {CaptionTrack} from '../captions/CaptionTrack';
import {overlapFrames as blurOverlap} from '../transitions/motionBlur';
import {overlapFrames as fadeOverlap} from '../transitions/fade';
import {overlapFrames as flashOverlap} from '../transitions/lightFlash';
import {overlapFrames as wipeOverlap} from '../transitions/wipe';
import {overlapFrames as zoomOverlap} from '../transitions/zoom';
import {overlapFrames as objectOverlap} from '../transitions/objectTransition';
import {overlapFrames as morphOverlap} from '../transitions/shapeMorph';
import {overlapFrames as matchOverlap} from '../transitions/matchCut';
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
    case 'objectTransition':
      return objectOverlap(fps);
    case 'shapeMorph':
      return morphOverlap(fps);
    case 'matchCut':
      return matchOverlap(fps);
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
  const byScene = new Map<string, EditEventProps[]>();
  for (const event of [...props.events].sort((a, b) => a.z_index - b.z_index)) {
    const list = byScene.get(event.scene_id) ?? [];
    list.push(event);
    byScene.set(event.scene_id, list);
  }
  const sceneOrder = [...props.scenes].sort((a, b) => a.start - b.start);
  
  // Calculate cross-scene overlap tails: scene i lends tail frames to scene i + 1 entrance
  const sceneTails = new Map<string, number>();
  const eventTails = new Map<string, number>();
  for (let index = 0; index < sceneOrder.length - 1; index += 1) {
    const currScene = sceneOrder[index];
    const nextScene = sceneOrder[index + 1];
    const nextEvents = byScene.get(nextScene.scene_id) ?? [];
    const nextLead = nextEvents.find((e) => e.role === 'midground' || e.role === 'primary_visual') ?? nextEvents[0];
    const overlap = transitionOverlapFrames(nextLead?.transition_in ?? null, fps);
    sceneTails.set(currScene.scene_id, overlap);

    // Apply tail frames to currScene visual events
    const currEvents = byScene.get(currScene.scene_id) ?? [];
    for (const evt of currEvents) {
      if (evt.role === 'midground' || evt.role === 'primary_visual' || evt.role === 'background' || evt.role === 'foreground') {
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
      {sceneOrder.map((scene) => {
        const sceneRange = eventFrames(scene.start, scene.end, fps);
        const sceneTail = sceneTails.get(scene.scene_id) ?? 0;
        const placed: PlacedEvent[] = (byScene.get(scene.scene_id) ?? []).map((event) => {
          const range = eventFrames(event.start, event.end, fps);
          const isVisual = event.role === 'midground' || event.role === 'primary_visual' || event.role === 'background' || event.role === 'foreground';
          const tail = eventTails.get(event.event_id) ?? 0;
          return {
            event,
            from: range.startFrame - sceneRange.startFrame,
            duration: range.frameCount + (isVisual ? tail : 0),
            head: transitionOverlapFrames(event.transition_in, fps),
            tail: tail,
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
            />
          </Sequence>
        );
      })}
      <CaptionTrack theme={props.theme} captions={props.captions} fps={fps} mode="emphasis_words" />
    </AbsoluteFill>
  );
};
