/**
 * Canonical Remotion input props. This is a validated projection of the
 * canonical artifacts — scene_plan, asset_manifest, edit_decisions,
 * art_direction — plus the platform profile. It is a transfer format, not a
 * competing creative plan: every timing, asset choice, and ordering decision
 * must already exist upstream.
 */

export interface PlatformProfileProps {
  profile: string;
  resolution: {width: number; height: number};
  fps: number;
  duration_constraints: {minimum_seconds: number; maximum_seconds: number};
  safe_zones: {caption: string; cta: string; brand: string};
}

export interface RuntimeLockProps {
  renderer_family: string;
  render_runtime: string;
  composition_mode: string;
  locked_concept_id: string;
  proposal_artifact_version: number;
  proposal_artifact_hash: string;
}

export interface ThemeProps {
  background: string;
  surface: string;
  text: string;
  mutedText: string;
  accent: string;
  accentSecondary: string;
  fontFamily: string;
  headlineSize: number;
  bodySize: number;
  lineWeight: number;
  cornerRadius: number;
  motion: {stiffness: number; damping: number; mass: number};
}

export interface AssetProps {
  asset_id: string;
  scene_id: string;
  kind: string;
  source: string;
  /** Path relative to the composer's public/ directory. */
  publicPath: string | null;
  /** Declared native representation for native/diagram assets. */
  nativeSpec: unknown;
  purpose: string;
  subject: string | null;
}

export interface CaptionProps {
  event_id: string;
  scene_id: string;
  start: number;
  end: number;
  audio_duration?: number;
  textReference: string;
  emphasisWords: string[];
}

export interface AudioRefProps {
  event_id: string;
  track: 'narration' | 'music' | 'sfx';
  start: number;
  end: number;
  /** Null when the requirement is deferred (no audio file exists yet). */
  publicPath: string | null;
  requirement: unknown;
}

export interface CharacterSpec {
  identity: string;
  role: string;
  pose: string;
  action: string;
  target: string;
  scale: number;
  depth_plane: string;
  position: { x: number; y: number };
  target_anchor?: { x: number; y: number } | null;
  motion: string;
  emotion: string;
  tool_held?: string | null;
}

export interface EditEventProps {
  event_id: string;
  scene_id: string;
  shot_id: string | null;
  track_id: string;
  role: string;
  asset_id: string | null;
  start: number;
  end: number;
  duration: number;
  z_index: number;
  parallax_factor?: number;
  purpose: string;
  framing: string | null;
  camera_intent: string | null;
  motion_intent: string | null;
  transition_in: string | null;
  transition_out: string | null;
  caption_ref: string | null;
  audio_ref: string | null;
  overlay_disabled?: boolean;
  character_spec?: CharacterSpec | null;
}

export interface SceneProps {
  scene_id: string;
  narrative_role: string;
  subject: string;
  visual_purpose: string;
  visual_metaphor: string;
  environment: string | null;
  depth_strategy: string | null;
  signature_device_usage: string;
  start: number;
  end: number;
  character_spec?: CharacterSpec | null;
}

export type ProductionCompositionProps = {
  productionId: string;
  editArtifactVersion: number;
  editArtifactHash: string;
  lock: RuntimeLockProps;
  platform: PlatformProfileProps;
  theme: ThemeProps;
  scenes: SceneProps[];
  assets: AssetProps[];
  events: EditEventProps[];
  captions: CaptionProps[];
  audio: AudioRefProps[];
  cta: {scene_id: string; start: number; end: number; branding: string};
  previewMode?: boolean;
  debugMode?: boolean;
}
