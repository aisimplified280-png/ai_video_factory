# Phase 15 Visual Pipeline Audit Report

**Date**: 2026-10-07  
**System**: AI Simplified Video Factory  
**Topic Under Test**: `"GPT-6 Astra controls robots"`

---

## 1. Runtime Path Trace
```text
Topic
  ↓
research_pack.json (Phase 10: multi-provider live facts)
  ↓
script.v006.json (Phase 11: 5-section narrative script)
  ↓
plan.v001.json (Phase 15: semantic visual plan)
  ↓
edit_decisions.v006.json (Phase 9.2: timeline mapping)
  ↓
Remotion Props (props_builder.py: asset paths, events, framing, camera_intent)
  ↓
Remotion Composition (SceneComposition.tsx, ImageLayer.tsx, camera/motion modules)
  ↓
Render (remotion render via headless Chromium)
  ↓
Final MP4 (output/<slug>/video.mp4)
  ↓
Frame-Level QA (frame extraction & pairwise histogram correlation)
```

---

## 2. Detailed Findings on the 12 Inspection Points

### 1. Where scene concepts are created
Scene concepts are created in `production/phase9/planner.py` via `generate_plan()` -> `production/phase15/engine.py:generate_phase15_plan()`.

### 2. Where prompts are created
Prompts are synthesized in `production/phase15/shot_director.py` by compiling `SUBJECT + ACTION + ENVIRONMENT + SHOT + CAMERA + COMPOSITION + LIGHTING + NEGATIVE_CONSTRAINTS`.

### 3. Whether prompts actually influence rendering
**Audit Finding**: Historically, prompts were sent to `https://image.pollinations.ai`. However, Pollinations recently enabled an account payment requirement (HTTP 402), which silently failed and fell back to generating rudimentary 2D flat geometric lines via PIL. Because of this, prompts had almost zero photographic effect on the rendered video!

### 4. Whether scene metadata survives into rendering
**Audit Finding**: Partially. `plan.v001.json` generated rich metadata (`camera_motion`, `composition`, `shot_type`, `visual_mode`), but in `production/phase9/mapper.py`, `composition` was only coarsely mapped to `event["crop"]`, which `props_builder.py` placed into `event["framing"]`. But in `SceneComposition.tsx`, `event.framing` was **never passed to `<ImageLayer>`**.

### 5. Whether all scenes use the same composition component
**Audit Finding**: YES. All scenes execute through `SceneComposition.tsx`. Every primary visual layer was rendered via `<ImageLayer src={url} />` with static `objectFit: "cover"`, ignoring shot scale, crop, and framing.

### 6. Whether camera information is actually implemented
**Audit Finding**: In `remotion-composer/src/compositions/SceneComposition.tsx`, `cameraStyle(intent)` only had cases for `reveal_space`, `approach_subject`, `expand_scale`, `follow_subject`, `shift_focus`, `cross_system`, and `observe_static`.
When the planner output intents like `fast_push_in`, `pull_out`, `dolly_through`, `overhead_track`, or `crane_pull_out`, Remotion hit `default: return staticCamera()`! Thus, the camera stayed completely static for several scenes. Furthermore, `pullOut.ts` existed in `remotion-composer/src/camera/` but was never imported or used.

### 7. Whether motion information is actually implemented
**Audit Finding**: `motionStyle(intent)` supports 13 motion styles (`emerge`, `grow`, `pulse`, `flow`, etc.), but `motion_intensity` from art direction (0–10) was not scaling the motion transforms.

### 8. Whether visual modes are actually implemented
**Audit Finding**: Visual modes existed only as a metadata field in `plan.v001.json`. Remotion had no concept of whether a layer was `detail`, `metaphor`, `demonstration`, `scale`, or `brand_cta`.

### 9. Whether scene-specific assets are actually used
**Audit Finding**: Scene assets are mapped to `ast_{scene_id}_primary.png` and staged in `projects/<prod>/assets/`. However, each shot within a scene reused the exact same uncropped image.

### 10. Whether the anti-repetition system is real or only textual
**Audit Finding**: The previous anti-repetition check existed in `shot_director.py`, but without weighted penalties and without forcing alternative concept generation across the 15 visual modes.

### 11. Whether the learning engine influences visual generation
**Audit Finding**: `production/phase14/learning_engine.py` scored titles and retention, but its historical visual direction insights were disconnected from the `ShotDirector`.

### 12. Whether visual QA evaluates actual frames or only metadata
**Audit Finding**: `frame_qa.py` implemented histogram correlation, but in `scripts/factory.py`, only technical QA (`cmd_qa`: file existence, duration, audio levels) was gating production. Frame-level QA was not wired to automatically re-plan and re-render weak or repetitive videos.

---

## 3. Targeted Solution Architecture
1. **Canonical Visual Scene Model**: Upgrade to all 22 required fields and 15 visual modes.
2. **Shot Director with Visual Memory & Weighted Penalties**: Mode (-2), Shot (-2), Camera (-2), Composition (-2), Environment (-1), Subject (-1).
3. **Renderer Integration**: Wire `pullOut`, all camera intents, and `framing` directly into `SceneComposition.tsx` and `ImageLayer.tsx`.
4. **Cinematic Asset Generator**: Render rich, atmospheric, high-fidelity composite frames with depth of field, volumetric lighting, and technical telemetry for each visual mode.
5. **Frame-Level QA & Automatic Replanning Gate**: If visual diversity score < 7.0 or similarity > threshold, automatically re-direct and re-render up to 3 attempts.
