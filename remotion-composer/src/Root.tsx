import React from 'react';
import {Composition, getInputProps} from 'remotion';
import {ProductionComposition} from './compositions/ProductionComposition';
import {totalFrames} from './runtime/timeline';
import {assertValidProps} from './runtime/validators';
import type {ProductionCompositionProps} from './runtime/props';

/**
 * Dev-only placeholder props so `npm run dev` opens. Every real render
 * passes --props with materialized production props; calculateMetadata
 * derives duration, FPS, and dimensions from those props, never from
 * constants here.
 */
const DEV_PLACEHOLDER = {
  productionId: 'dev-placeholder',
  editArtifactVersion: 0,
  editArtifactHash: 'sha256:' + '0'.repeat(64),
  lock: {
    renderer_family: 'explainer',
    render_runtime: 'remotion',
    composition_mode: 'atelier',
    locked_concept_id: 'concept_01',
    proposal_artifact_version: 1,
    proposal_artifact_hash: 'sha256:' + '0'.repeat(64),
  },
  platform: {
    profile: 'profiles/youtube_short.json',
    resolution: {width: 1080, height: 1920},
    fps: 30,
    duration_constraints: {minimum_seconds: 10, maximum_seconds: 180},
    safe_zones: {caption: 'lower_center_safe', cta: 'center_safe', brand: 'bottom_safe'},
  },
  theme: {
    background: '#0F172A',
    surface: '#16213A',
    text: '#F8F7F2',
    mutedText: '#9AA6B2',
    accent: '#38BDF8',
    accentSecondary: '#F4A261',
    fontFamily: 'Arial, Helvetica, sans-serif',
    headlineSize: 64,
    bodySize: 34,
    lineWeight: 3,
    cornerRadius: 20,
    motion: {stiffness: 176, damping: 14, mass: 1},
  },
  scenes: [],
  assets: [],
  events: [],
  captions: [],
  audio: [],
  cta: {scene_id: 'scene_cta', start: 0, end: 1, branding: 'AI Simplified Lab'},
} satisfies ProductionCompositionProps;

export const Root: React.FC = () => {
  return (
    <Composition
      id="Production"
      component={ProductionComposition}
      durationInFrames={30}
      fps={30}
      width={1080}
      height={1920}
      defaultProps={DEV_PLACEHOLDER}
      calculateMetadata={({props}) => {
        const input = (Object.keys(props).length > 0 ? props : getInputProps()) as unknown as ProductionCompositionProps;
        assertValidProps(input);
        return {
          durationInFrames: totalFrames(input.events.length ? Math.max(...input.events.map((event) => event.end)) : 1, input.platform.fps),
          fps: input.platform.fps,
          width: input.platform.resolution.width,
          height: input.platform.resolution.height,
          props: input,
        };
      }}
    />
  );
};
