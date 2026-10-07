# ARCHITECTURE V2 — AI Simplified Lab Production System

> Design specification for the production-grade, agentic video production system.
> Informed by OpenMontage principles. Original implementation, not a copy.

---

## System Overview

```
TOPIC / BRIEF
    |
    v
[RESEARCH STAGE]
    | research_brief.json
    v
[PROPOSAL STAGE]
    | proposal_packet.json  (2-3 concepts, renderer locked here)
    v
[SCRIPT STAGE]
    | script.json
    v
[ART DIRECTION STAGE]
    | art_direction.json
    v
[SCENE PLAN STAGE]
    | scene_plan.json  (real semantic scenes, not templates)
    v
[ASSET MANIFEST STAGE]
    | asset_manifest.json  (every asset has WHY it exists)
    v
[EDIT DECISIONS STAGE]
    | edit_decisions.json  (complete timeline contract)
    v
[COMPOSITION RUNTIME]
    | Remotion / HyperFrames / FFmpeg (LOCKED at proposal)
    v
[AUDIO / CAPTIONS / CTA]
    | audio_plan.json
    v
[REVIEW + QA]
    | qa_report.json, review_report.json
    v
[FINAL VIDEO]
    final_video.mp4 (validated, audited MP4)
    v
[PUBLISH LOG]
    publish_log.json
```

---

## Canonical Artifact Chain

Every artifact is a contract between stages. Each has:
- **Schema**: JSON Schema file in `schemas/artifacts/`
- **Producer**: The stage that creates it
- **Consumers**: Stages that read it (read-only)
- **Validation**: Pydantic model + jsonschema validation at boundaries
- **Persisted JSON**: Written to `projects/<project_id>/` on creation
- **Status**: `pending | generating | ready | failed | approved | rejected`
- **Provenance**: Which model/provider generated it, at what cost

| Artifact | Producer | Primary Consumers |
|----------|----------|-------------------|
| `research_brief` | research stage | proposal, script |
| `proposal_packet` | proposal stage | art_direction, scene_plan |
| `script` | script stage | scene_plan, audio |
| `art_direction` | art_direction stage | scene_plan, composition |
| `scene_plan` | scene_plan stage | assets, edit |
| `asset_manifest` | assets stage | edit, composition |
| `edit_decisions` | edit stage | composition |
| `render_report` | composition stage | qa |
| `review_report` | review stage | controller |
| `qa_report` | qa stage | controller, publish |
| `publish_log` | publish stage | — |

---

## Production Controller (`production/controller.py`)

The stateful brain of every production.

```python
class ProductionState(BaseModel):
    project_id: str
    pipeline: str                    # e.g. "youtube-short"
    status: ProductionStatus
    current_stage: str
    target_duration: float
    aspect_ratio: str                # "9:16", "16:9"
    platform: str                    # "youtube_shorts"
    budget: BudgetState
    style: str
    artifacts: dict[str, ArtifactState]
    decisions: list[Decision]
    warnings: list[Warning]
    errors: list[Error]
    revision_count: dict[str, int]   # per-stage
    created_at: datetime
    updated_at: datetime
```

### Controller Operations
| Operation | Description |
|-----------|-------------|
| `start(topic, pipeline, options)` | Create new production, run first stage |
| `resume(project_id)` | Resume from last checkpoint |
| `retry_stage(stage_name)` | Re-run one stage without rerunning earlier stages |
| `revise_stage(stage_name, notes)` | Regenerate with human-supplied notes |
| `skip_nonrequired_stage(stage_name)` | Skip optional stages |
| `approve(stage_name)` | Mark stage artifact as approved |
| `reject(stage_name, reason)` | Reject with notes; triggers revision |
| `abort(project_id)` | Cancel production |
| `rerender(project_id)` | Re-run composition from approved edit_decisions |

### Revision Policy
- Max 3 revisions per stage (configurable)
- Failed stage = blocked, not restarted from scratch
- Automatic send-back loop based on reviewer findings

---

## Pipeline Definitions (`pipeline_defs/*.yaml`)

```yaml
# youtube-short.yaml
name: youtube-short
version: 2.0
description: 30-60 second vertical short for YouTube Shorts
target_duration: 45
platform: youtube_shorts
required_stages:
  - research
  - proposal
  - script
  - art_direction
  - scene_plan
  - assets
  - edit
  - compose
optional_stages:
  - publish
required_artifacts:
  - research_brief
  - proposal_packet
  - script
  - art_direction
  - scene_plan
  - asset_manifest
  - edit_decisions
  - render_report
  - qa_report
quality_gates:
  min_scene_diversity_score: 70
  min_source_count: 3
  max_consecutive_same_type: 2
  cta_required: true
  audio_required: true
approval_policy:
  research: auto          # auto-approve if quality gate passes
  proposal: human         # requires human selection
  script: auto
  art_direction: auto
  scene_plan: auto
  assets: auto
  edit: auto
  compose: human          # requires human review of preview
budget_policy:
  max_image_gen_calls: 20
  max_video_gen_calls: 5
  max_tts_chars: 5000
render_runtime_policy:
  primary: remotion
  fallback: ffmpeg_pil    # only if remotion unavailable, explicit not silent
```

---

## Art Direction System (`production/art_direction.py`)

Produced before scene planning. Never skip this.

```json
{
  "production_id": "proj-abc123",
  "design_read": "Tension between centralized AI power and distributed human agency",
  "visual_metaphor": "Control room becoming a mind — wires becoming neurons",
  "visual_variance": 8,
  "motion_intensity": 6,
  "information_density": 5,
  "palette_discipline": {
    "primary": "#0B0E1A",
    "accent_1": "#7C5CFF",
    "accent_2": "#00D4FF",
    "neutral": "#4A5568",
    "warning": "#F59E0B"
  },
  "typography_personality": "technical-editorial — tight tracking, sharp weight contrast",
  "layout_language": "asymmetric tension — never centered, always in motion",
  "texture_language": "grid substrates, circuit traces, light bloom at key beats",
  "transition_language": "hard cuts with motion blur at peak energy, slow dissolves at reflection",
  "reference_strategy": "Inspired by Kurzgesagt density + Bloomberg terminal palette",
  "signature_device": "Data trails that connect across scenes",
  "anti_patterns": [
    "no floating cards on every scene",
    "no identical rail layout twice",
    "no text-only scenes without visual anchor"
  ],
  "quality_gates": {
    "visual_variance_min": 6,
    "motion_min": 4,
    "must_answer_visual_metaphor": true
  }
}
```

### AI Simplified Lab Default Starting Dials
| Dial | Default | Range |
|------|---------|-------|
| `visual_variance` | 8 | 1-10 |
| `motion_intensity` | 6 | 1-10 |
| `information_density` | 5 | 1-10 |

**Critical rule**: Brand consistency comes from typography, restrained palette, spacing, and audio identity — NOT from using the same card/rail/hero skeleton on every scene.

---

## Scene Plan Design (`stages/scene_plan/scene_planner.py`)

Every scene answers 10 questions before it is accepted:

1. **WHAT does the viewer understand at the end?**
2. **WHY does this visual exist at this moment?**
3. **WHAT exact subject is visible?**
4. **WHAT changes during this scene?**
5. **WHAT moves and how?**
6. **HOW is it framed?**
7. **HOW does the viewer's eye move?**
8. **WHAT asset is required?**
9. **HOW is this scene different from the previous one?**
10. **HOW does it set up the next scene?**

### Canonical Scene Schema
```json
{
  "id": "scene_03",
  "type": "animation",
  "start_seconds": 14.2,
  "end_seconds": 19.8,
  "script_section_id": "section_2",
  "description": "Neurons firing across a synthetic brain — the model's attention mechanism visualized",
  "shot_intent": "Make the viewer feel the scale of computation",
  "narrative_role": "proof",
  "information_role": "visual_metaphor",
  "subject": "neural attention pattern",
  "subject_action": "activation spreading outward from prompt token",
  "environment": "dark infinite space, grid substrate",
  "composition": "radial — center activation point, rings expanding outward",
  "spatial_framing": "close to medium — intimate then expanding",
  "depth_layers": ["background_grid", "midground_nodes", "foreground_glow"],
  "camera": {
    "type": "push_in",
    "movement": "slow_push_toward_center",
    "start_distance": "medium",
    "end_distance": "close"
  },
  "shot_size": "medium_to_close",
  "lighting": "internal_glow",
  "color_temperature": "cool_blue_purple",
  "depth_of_field": "mid_foreground_sharp",
  "motion": {
    "primary": "radial_expand",
    "secondary": "pulse",
    "timing": "synced_to_narration_beat"
  },
  "animation_sequence": [
    {"at": 0.0, "action": "appear", "subject": "center_node"},
    {"at": 0.3, "action": "trace", "subject": "connection_lines"},
    {"at": 0.7, "action": "pulse", "subject": "outer_nodes"}
  ],
  "transition_in": "hard_cut",
  "transition_out": "motion_blur_dissolve",
  "overlays": [],
  "captions": {"style": "word_highlight", "safe_zone": "bottom_third"},
  "required_assets": [
    {
      "asset_id": "anim_neural_spread",
      "type": "animation",
      "source": "native_composition",
      "purpose": "core visual metaphor for attention mechanism"
    }
  ],
  "texture_keywords": ["circuit", "neural", "glow", "dark_space"],
  "reference_strategy": "Inspired by 3Blue1Brown neural net visualizations but motion-based"
}
```

### Scene Type Vocabulary
| Type | Description |
|------|-------------|
| `talking_head` | Human/avatar presenter |
| `broll` | Cinematic or stock footage |
| `animation` | Native programmatic animation |
| `character_scene` | Character-driven narrative |
| `diagram` | Explanatory diagram / chart |
| `text_card` | Typography-dominant |
| `transition` | Purely transitional |
| `generated` | AI-generated image/video asset |
| `screen_recording` | Software demo |

---

## Visual Technique Library (`creative/techniques/`)

Each technique is knowledge, not a template.

| Technique | Use When |
|-----------|----------|
| `diagram_reveal` | Explaining system architecture |
| `analogy_visualization` | Abstract concept needs concrete anchor |
| `stat_punch` | Single critical number needs emphasis |
| `data_dashboard` | Multiple metrics simultaneously |
| `before_after` | Transformation comparison |
| `timeline_progression` | Historical sequence |
| `zoom_and_focus` | Detail reveal within a system |
| `code_walkthrough` | Software explanation |
| `network_build` | Relationship emergence |
| `system_explosion` | Architecture layer reveal |
| `system_assembly` | Parts combining into whole |
| `kinetic_typography` | Quote, definition, or key phrase |
| `visual_metaphor` | Concept grounded in physical metaphor |
| `cinematic_broll` | Emotional texture / pacing reset |
| `cause_effect` | Two-phase reveal |
| `comparison` | Side-by-side contrast |
| `evidence_wall` | Multiple sources/facts simultaneously |
| `scale_transition` | Zoom-out to reveal scale |
| `object_transformation` | Thing becomes different thing |

**Rule**: A scene planner chooses a technique based on content. The same technique must not appear more than twice in a 45-second video without narrative justification.

---

## Visual Variety Governor (`creative/variety.py`)

Hard constraints enforced before scene plan is approved:

| Rule | Threshold |
|------|-----------|
| No consecutive same `scene.type` | Max 2 |
| No consecutive same composition geometry | Max 2 |
| No repeated hero component (unless intentionally marked) | 0 |
| No identical motion pattern across all scenes | 0 |
| No identical transition on every cut (when variance >= 4) | 0 |
| Scene families must visibly diverge (when variance >= 6) | Required |
| A 30-60s video must contain multiple visual modes | Min 3 |

---

## Asset Manifest (`stages/assets/asset_manifest.py`)

Every asset must justify its existence:

```json
{
  "asset_id": "img_openai_office_2019",
  "scene_id": "scene_02",
  "purpose": "Establish the intimate startup atmosphere before the scale reveal",
  "type": "image",
  "source": "generated",
  "provider": "stability-ai",
  "model": "sd3-large",
  "prompt": "Small office, 5 people at computers, warm light, 2019 startup atmosphere, photorealistic",
  "negative_prompt": "corporate, glass tower, large crowds",
  "reference_assets": [],
  "expected_duration": 5.2,
  "quality_requirements": {
    "min_resolution": "1080x1920",
    "style_match": "cinematic_warm"
  },
  "fallback_chain": ["pexels_stock", "generated_placeholder"],
  "file_path": "projects/proj-abc123/assets/images/img_openai_office_2019.png",
  "status": "ready",
  "cost_usd": 0.04
}
```

---

## Edit Decisions (`stages/edit/edit_director.py`)

The complete timeline contract. Once produced, the renderer executes this exactly.

```json
{
  "production_id": "proj-abc123",
  "total_duration": 47.3,
  "platform_profile": "youtube_short",
  "render_runtime": "remotion",
  "renderer_family": "explainer",
  "composition_mode": "atelier",
  "tracks": {
    "video": [
      {
        "scene_id": "scene_01",
        "in": 0.0,
        "out": 6.5,
        "asset_id": "anim_hook_kinetic",
        "transition_out": {"type": "hard_cut"}
      }
    ],
    "narration": [
      {"in": 0.0, "out": 47.3, "asset_id": "vo_main", "volume": 1.0}
    ],
    "music": [
      {"in": 0.0, "out": 47.3, "asset_id": "bgm_tech_ambient", "volume": 0.08,
       "ducking": [{"start": 0.0, "end": 47.3, "target_volume": 0.04}]}
    ],
    "captions": [
      {"in": 0.0, "out": 47.3, "asset_id": "captions_main", "style": "word_highlight"}
    ],
    "sfx": []
  },
  "validation": {
    "no_gaps": true,
    "no_overlaps": true,
    "all_assets_resolved": true,
    "duration_covered": true,
    "audio_valid": true,
    "captions_valid": true,
    "cta_present": true,
    "renderer_locked": true
  }
}
```

---

## Composition Runtime Router (`composition/runtime_router.py`)

Runtime is **locked** at proposal stage. No silent swaps.

| Runtime | Use When |
|---------|---------|
| `remotion` | Primary. Any composition. React/TypeScript. |
| `hyperframes` | HTML/CSS/GSAP kinetic typography, complex SVG motion, motion-graphics-heavy |
| `ffmpeg_pil` | Legacy viral/editorial pipeline. Concat, trim, mux, post-processing. |

**If HyperFrames is locked but unavailable**: return a blocker. Do NOT silently fall back to Remotion.

---

## Camera System (`composition/camera.py`)

```python
CAMERA_BEHAVIORS = {
    "static": StaticCamera,
    "push_in": PushInCamera,       # Ken Burns inward on stills
    "pull_out": PullOutCamera,     # Ken Burns outward on stills
    "pan": PanCamera,              # horizontal sweep
    "tilt": TiltCamera,            # vertical sweep
    "tracking": TrackingCamera,    # follows subject
    "orbit": OrbitCamera,          # circular around subject
    "parallax": ParallaxCamera,    # depth layers at different speeds
    "rack_focus": RackFocusCamera, # blur shift between depth layers
    "zoom": ZoomCamera,            # optical zoom
    "whip": WhipTransitionCamera,  # fast directional transition
    "focus_shift": FocusShift,     # attention relocation
}
```

All behaviors must produce actual visual output. Decorative-only camera metadata is rejected.

---

## Atelier Mode (`composition/atelier/`)

For each atelier production:
- `art-direction.md` — prose description of the visual treatment
- `composition-plan.json` — how each shot is authored

The atelier renderer allows:
- Custom geometry per scene
- Custom timing relationships
- Custom layer compositions
- Custom motion choreography
- Custom visual metaphors
- Custom typography placement
- Custom camera movement

The signature visual device appears in **1-2 key beats only**, not every scene.

---

## Audio Pipeline (`audio/`)

```json
{
  "production_id": "proj-abc123",
  "narration": {
    "asset_id": "vo_main",
    "provider": "edge-tts",
    "voice": "en-US-ChristopherNeural",
    "duration": 44.8,
    "file": "audio/voice/vo_main.mp3",
    "captions": "audio/voice/vo_main.vtt"
  },
  "music": {
    "asset_id": "bgm_tech_ambient",
    "track": "Pulsar - The Grey Room.mp3",
    "volume": 0.08,
    "duration_required": 47.3
  },
  "sfx": [],
  "ducking": {
    "strategy": "narration_priority",
    "music_during_speech": 0.04,
    "music_during_silence": 0.08,
    "fade_ms": 200
  },
  "mix_levels": {
    "narration": 1.0,
    "music": 0.08,
    "sfx": 0.5
  },
  "validation": {
    "voice_exists": true,
    "voice_duration_valid": true,
    "music_exists": true,
    "music_does_not_overpower": true,
    "final_audio_stream_exists": true,
    "final_mux_has_audio": true
  }
}
```

---

## Caption System (`composition/captions/`)

Modes:
- `sentence` — full sentence at a time
- `word_highlight` — sentence with active word highlighted
- `karaoke` — word-by-word
- `emphasis_words` — key words larger/colored

Safe zones enforced for:
- YouTube Shorts UI overlays (top + bottom controls)
- Channel CTA zone
- Caption zone (bottom third)

---

## CTA as a Real Scene

The CTA scene is always the final planned scene, never an afterthought.

```json
{
  "id": "scene_cta",
  "type": "animation",
  "script_section_id": "section_cta",
  "spoken_text": "Subscribe to AI Simplified Lab for more AI breakdowns like this.",
  "visual_treatment": "brand_lockup_with_motion",
  "text": "Subscribe to AI Simplified Lab",
  "motion": "hero_reveal",
  "camera": "slow_push",
  "audio": {
    "voice": true,
    "music": true,
    "music_volume": 0.12
  }
}
```

CTA QA checks:
- CTA scene present in scene_plan
- CTA voice line rendered
- CTA visual present in final video frames at T > 90% of duration
- CTA audio present in final mux

---

## Reviewer System (`review/`)

Every stage gets a reviewer pass. Reviewers produce structured findings:

```json
{
  "stage": "scene_plan",
  "status": "rejected",
  "findings": [
    {
      "finding": "Scenes 2, 3, 4 all use identical centered text card layout",
      "evidence": "scene_02.composition == scene_03.composition == scene_04.composition == 'centered_hero'",
      "severity": "critical",
      "impact": "Video will appear as repetitive PowerPoint slides",
      "recommended_correction": "scene_03 must use a different composition family; suggest diagram or split"
    }
  ]
}
```

No vague findings. Every finding must cite artifact fields or sampled frame evidence.

---

## Visual QA (`qa/`)

Automatically samples final video frames at:
0%, 10%, 20%, 30%, 40%, 50%, 60%, 70%, 80%, 90%, 100%

Checks:
- Black frames (> 1% of frames)
- Frozen frames (hash equality)
- Text overflow (outside safe zones)
- Safe-zone violations
- Visual repetition (high frame similarity)
- Scene repetition (layout_diversity score)
- Caption collisions
- Low visual activity
- CTA presence (final 10%)
- Audio presence
- Duration match vs edit_decisions
- Codec/container validation

Produces `qa_report.json` with pass/fail per check.

---

## Diversity Metrics (`qa/diversity_metrics.py`)

| Metric | Target |
|--------|--------|
| `scene_type_diversity` | > 0.6 (at least 3 types in 6 scenes) |
| `layout_diversity` | > 0.5 |
| `composition_diversity` | > 0.6 |
| `motion_diversity` | > 0.5 |
| `asset_type_diversity` | > 0.4 |
| `transition_diversity` | > 0.3 |
| `text_density` | < 0.6 (not text-dominated) |
| `visual_activity` | > 0.4 |

A video that renders correctly but scores below threshold on 3+ metrics is **REJECTED** and sent back to scene_plan stage.

---

## Cost Governance (`governance/cost_tracker.py`)

```json
{
  "production_id": "proj-abc123",
  "estimated_cost": 0.85,
  "reserved_cost": 1.20,
  "actual_cost": 0.67,
  "remaining_budget": 3.33,
  "budget_cap": 4.00,
  "breakdown": {
    "research_llm": 0.08,
    "proposal_llm": 0.12,
    "script_llm": 0.09,
    "art_direction_llm": 0.06,
    "scene_plan_llm": 0.14,
    "image_generation": 0.18,
    "tts": 0.00,
    "remotion_render": 0.00
  }
}
```

Before expensive generation, system checks available budget. Over-budget = blocker, not silent skip.

---

## Remote-First Compute Distribution

| Operation | Where |
|-----------|-------|
| Planning (research, proposal, script, scene_plan) | Local |
| Artifact creation + validation | Local |
| Lightweight image generation | Local (Pollinations API, free) |
| Heavy image generation (SD3, etc.) | Remote (Colab / GDrive) |
| Remotion render | Remote (Colab / GitHub Actions) |
| HyperFrames render | Remote |
| Large FFmpeg operations | Remote |
| TTS generation | Local (edge-tts) |
| Final QA analysis | Local |

---

## Production Output Directory Structure

```
projects/<project_id>/
  brief/
    brief.json
  research/
    research_brief.json
  proposal/
    proposal_packet.json
    decision_log.json
  script/
    script.json
    vo_script.txt
  direction/
    art_direction.json
    art-direction.md
    taste_profile.json
  scenes/
    scene_plan.json
    scene_01.json
    scene_02.json
    ...
  assets/
    asset_manifest.json
    images/
    videos/
    diagrams/
    audio/
  edit/
    edit_decisions.json
  composition/
    composition_plan.json
    render_manifest.json
  renders/
    scene_01.mp4
    scene_02.mp4
    final_video.mp4
  review/
    review_report.json
    qa_report.json
  publish/
    publish_log.json
```

---

## Media Profiles (`profiles/`)

```json
{
  "profile": "youtube_short",
  "width": 1080,
  "height": 1920,
  "aspect_ratio": "9:16",
  "fps": 30,
  "codec": "h264",
  "audio_codec": "aac",
  "audio_bitrate": "192k",
  "video_bitrate": "8M",
  "safe_zones": {
    "top": 0.10,
    "bottom": 0.15,
    "left": 0.05,
    "right": 0.05,
    "caption_bottom": 0.20,
    "cta_bottom": 0.25
  }
}
```

All resolution/FPS constants come from profiles. None are scattered in renderer code.

---

## Legacy Compatibility

The `compat/legacy_adapter.py` converts old storyboard JSON into the new artifact chain **at ingestion only**.

After conversion:
- New production artifacts are authoritative
- Legacy fields (`template_context`, `visual_plan`, `render_plan`) are preserved as read-only provenance
- Legacy fields never override `art_direction`, `scene_plan`, `edit_decisions`, `render_runtime`, `composition_mode`

The existing viral renderer (`viral_renderer.py`) and editorial executor (`editorial/executor.py`) remain completely isolated and unchanged.

---

## Engineering Success Criteria

The rebuild is complete only when:

1. A topic enters through one production entry point
2. The production passes through explicit stage artifacts
3. Each stage can be reviewed independently
4. Failed stages can be revised independently (max 3 revisions)
5. Art direction is explicit and persisted
6. Scene planning is semantic and executable (every field maps to visual output)
7. Asset generation is tied to scene purpose (every asset has a WHY)
8. Edit decisions are a real timeline contract
9. Renderer selection is locked at proposal and auditable
10. Atelier mode creates genuinely custom compositions
11. Remotion executes custom compositions from edit_decisions
12. HyperFrames available when selected (no silent fallback)
13. FFmpeg used for post-processing, not as creative engine
14. Captions and audio are first-class timeline elements
15. CTA is a real final scene with verified presence in QA
16. Remote-first rendering still works
17. Local machine does not require GPU inference
18. Existing legacy viral renderer still works (26/26 tests green)
19. Five different subjects produce visibly different visual treatments
20. Final-video QA validates the encoded MP4, not just source frames
21. Benchmark videos are NOT describable as "the same template with different text"
