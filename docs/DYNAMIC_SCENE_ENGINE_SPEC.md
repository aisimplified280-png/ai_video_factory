# Dynamic Scene Engine — Technical Specification

**Branch:** `stage1c/dynamic-scene-engine`  
**Applies to:** Every new AI Simplified Lab video project.  
**Creative rule:** This is a scene-based animated video engine, not a slide-deck or card-template renderer.

## 1. Production mode and compatibility

- New projects must set root `productionMode: "dynamic"`.
- Every new scene must carry a complete `sceneDirection`.
- Dynamic mode renders a full-frame composition per scene. There is no recurring title header, logo badge, halftone overlay, global progress bar, ambient glow or fixed caption pill.
- The legacy `cardType` path remains for old projects only. A missing or invalid `sceneDirection` must fail closed; no dynamic-to-card fallback is permitted.
- Scene transitions, branding and outro moments must be directed in the story. Do not put the same chrome around every shot.

## 2. Required scene direction model

Every scene includes `id`, `voiceText` and `sceneDirection`:

- `narrativePurpose`: the viewer question this scene resolves.
- `visualIntent`: what the viewer should understand when muted.
- `visualMetaphor`: a concrete visual mechanism, only when it helps explain the idea.
- `primarySubject`: an element id that exists in the scene.
- `composition`: unique signature, shot type, camera move/target/path, camera animation, depth layers, focal hierarchy, caption-safe negative space and scene environment.
- `visualEvent`: setup, action and payoff.
- `elements`: scene objects with ids, role, purpose, source, normalized geometry, supported appearance primitive and motion role.
- `choreography`: spoken-phrase/timecode triggers, target element, visible change, animation, cause/effect reaction motions and an SFX key/purpose/timing.
- `audio`: exact voice segment, ambience direction, music direction and ducking direction.
- `captions`: timing mode, emphasis, anchor/treatment and an actual per-scene placement/style.
- `transition`: one of the implemented types (`hard-cut`, `cross-dissolve`, or `camera-continuation`) plus the story reason. Unsupported transitions fail validation rather than being silently approximated.

### Composition and camera

`composition.signature` must be unique within the video unless the storyboard explains a deliberate story return to the same object/state. Changing colour, text or image does not make a reused layout unique.

Camera fields:
- `move`, `target`, `path`.
- `animation.from` and `animation.to` must contain numeric transform state (x/y/scale/rotation/opacity).
- `duration` and `ease` describe the camera movement.

Environment can define a scene-specific background and atmosphere description. Any visible environmental element should be represented as a purposeful scene element, not generic decoration.

### Renderable elements

Supported SVG primitives:
`orb`, `ring`, `capsule`, `packet`, `rail`, `beam`, `node`, `panel`, `label`, `particle-field`, and `image`.

Each element requires:
- renderer-safe unique id;
- a role and a specific purpose;
- source type: procedural, original, generated, licensed or captured;
- normalized x/y geometry (0..1);
- `appearance.primitive` and primitive-specific visual properties;
- motion role.

Licensed assets must carry licence evidence and file references must resolve inside approved project asset folders. Product UI or screen footage must be genuine capture, not invented UI.

### Choreography and sound events

Each choreography event requires:
- trigger `spoken-phrase` or `timecode`;
- target element id;
- unique event name and visible path/change;
- positive duration and explicit purpose;
- animation `from`/`to` values;
- `causeAndEffect.reacts` plus matching executable `reactionMotions`;
- purposeful SFX `assetKey`, scene-relative `offsetSeconds` and purpose, or explicit deliberate silence.

Spoken phrases must occur in the narration. The production preflight validates SFX ids against `assets/sfx/manifest.json`. Unknown cues, ungrounded triggers or missing reaction animation block the render.

### Voice, captions and audio

- Each scene's `audio.voiceSegment` must match its narration line.
- Edge-TTS emits actual WordBoundary offsets and durations.
- Those exact word times are the shared clock for caption highlighting and motion triggers. Do not interpolate timing from word count.
- Alignment fails closed if the approved narration and returned TTS word stream do not match.
- SFX are mixed under narration, with scene-relative timing.
- Optional music is a separate local file under `assets/music/` and requires creator-confirmed usage rights plus source URL, licence id and licence URL. It is sidechain-ducked beneath the voice.
- Voice commercial terms are not independently certified by the pipeline. The YouTube package records the voice provider and this limitation.
- A descriptive ambience/music direction does not itself mean an audio asset has been generated. Use an approved bed or deliberate silence until a rights-cleared track exists.

Caption fields:
- `mode`: `word-synced` or `phrase-synced`.
- `placement`: x/y percentages (5..95), align (left/center/right), max width in px.
- `style`: bounded font size/weight, text colour, active highlight colour and transparent or valid active background.
- Every scene can place captions differently to leave the action visible. Do not use a universal caption pill.

## 3. Creative release gate

A dynamic plan fails before provider calls or rendering when:
- scene direction or scene purpose is missing;
- a card/template/slide layout is present;
- scene composition signature repeats without a meaningful story-continuity reason;
- camera direction/animation or visual event is missing;
- the focal hierarchy or depth design is missing;
- an element has no clear role, purpose, source or supported primitive;
- scene choreography has no visible motion or cause-and-effect reaction;
- a spoken trigger does not occur in its voice segment;
- an SFX key is unknown, unlicensed/untracked or un-timed;
- voice segment is missing or captions do not have scene-specific placement/style;
- the transition has no narrative reason.

Technical MP4 validity is not a substitute for this creative gate. Both creative inspection and media QA must pass.

## 4. Rendering and release architecture

1. Read project manifest and validate all dynamic scene directions before TTS or any provider/credit call.
2. Generate narration once and capture true WordBoundary timings.
3. Align words to scene voice segments. Fail instead of silently guessing.
4. Convert the directed scene into a custom full-frame SVG/HTML composition.
5. Animate individual scene objects and camera from explicit states; no default full-screen zoom or ambient template animation.
6. Place captions using each scene's placement and actual word timings.
7. Mix voice, approved SFX and optional rights-cleared/ducked music.
8. Render with HyperFrames, mux to H.264/AAC and verify with FFprobe/FFmpeg.
9. Inspect entrance/action/payoff frames for every scene and listen to the audio. Any slide-like/repetitive scene fails creative review.
10. Generate the upload package, thumbnail and SRT. Publishing remains manual and approval-gated.

## 5. Format policy and rollout

- Current implementation target: vertical Shorts 1080×1920, 30 fps, H.264 MP4, AAC stereo 48 kHz.
- Horizontal 1920×1080 has not yet been implemented in the dynamic renderer; do not claim it is supported until separately tested.
- Legacy projects remain readable through the legacy renderer.
- The first dynamic proof should contain four distinct visual languages and be visually reviewed before it is used to produce a public video.
- No generated provider may be called until cost/credit and rights have been checked.
