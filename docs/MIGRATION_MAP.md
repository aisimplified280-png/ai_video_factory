# MIGRATION MAP — AI Simplified Lab Video Factory → V2 Production System

> **Phase 0 Audit** | Baseline: **26/26 tests passing** (Python 3.13.7, pytest 8.4.2)
> Recorded: 2026-10-05

---

## Legend

| Symbol | Meaning |
|--------|---------|
| KEEP | Preserve as-is; V2 depends on it |
| REFACTOR | Keep the module, reshape its interface |
| REPLACE | New implementation supersedes this; old file deprecated |
| DEPRECATE | Retire after V2 pipeline is stable; keep for legacy compat period |
| NEW | Does not exist yet; must be created |

---

## Entry Points

| File | Current Role | Decision | Why |
|------|-------------|----------|-----|
| `create_short.py` | Monolithic pipeline orchestrator. TTS, scene loop, audio mix, FFmpeg mux all in one 630-line file. | REFACTOR | Split into thin CLI shim that delegates to `production/controller.py`. Keep `run_pipeline()` signature for backwards compatibility with `app.py`. Remove all orchestration logic from here. |
| `app.py` | Flask web UI + job registry (in-memory dict). Calls `run_pipeline()` in background thread. | REFACTOR | Keep the Flask shell. Route new productions through `ProductionController`. Expose new artifact endpoints. Existing UI endpoints remain functional. |

---

## Pipeline Orchestration

| File | Current Role | Decision | Why |
|------|-------------|----------|-----|
| `create_short.py::run_pipeline()` | Single function driving the entire pipeline. Hard-coded scene loop, audio handling, FFmpeg calls. | REPLACE | Becomes a thin wrapper that invokes `production/controller.py::ProductionController`. The actual pipeline stages move to `stages/`. |
| `storyboard.py` | LLM prompt -> raw JSON storyboard. Handles provider fallback (OpenAI -> Gemini -> OpenRouter -> local template). 776 lines. | REFACTOR | Underlying LLM call logic promoted into `stages/research/` + `stages/proposal/`. `generate_storyboard()` retained as legacy entrypoint wrapping new stages for backwards compatibility. |
| `styles.py` | Style registry (`explainer`, `viral_explainer`, etc.) + `auto_detect_style()`. | KEEP | Style names become `pipeline_family` hints. `auto_detect_style()` maps to a pipeline definition. Keep intact; do not scatter style constants. |

---

## Editorial Subsystem (editorial/)

| File | Current Role | Decision | Why |
|------|-------------|----------|-----|
| `editorial/__init__.py` | Re-exports `analyze_narration`, `build_editorial_plan`, `semantic_motion_for`, `write_debug_manifest`, `build_render_qa_report`. | REFACTOR | After V2 migration, re-exports point to new canonical implementations. Keep public surface for test compatibility. |
| `editorial/planner.py` | Converts a scene dict into a `render_plan` (layout_family, primitive, action, shot_plan, motion, camera). Intent-based, not template-based. | REFACTOR | Becomes compatibility wrapper around the new `stages/scene_plan/scene_planner.py`. The scene planner supersedes it for new productions. |
| `editorial/executor.py` | Draws editorial frames using PIL. Dispatches to `network_layout`, `process_layout`, `split_screen_layout`, etc. 472 lines. | KEEP (isolated) | This is the working pixel engine for `editorial_explainer` / `editorial_viral` modes. Preserve completely. New composition runtimes (Remotion, HyperFrames) are additive. |
| `editorial/visual_intent.py` | Keyword-based narration -> intent classifier (30+ intent types). | REFACTOR | Logic moves to `stages/script/intent_classifier.py`. Old module wraps new classifier for test compatibility. |
| `editorial/motion.py` | Maps `primary_intent` + `role` -> motion dict. | REFACTOR | Becomes an entry in `composition/motion.py` semantic action library. |
| `editorial/composition.py` | Resolves layout family -> composition dict (zones, margins, safe areas). | REFACTOR | Absorbed into `profiles/` + `composition/runtime_router.py`. |
| `editorial/shot_planner.py` | Maps intents -> layout family and shot sequence. | REPLACE | The new `stages/scene_plan/scene_planner.py` covers this with proper scene contracts. |

---

## Rendering Subsystem

| File | Current Role | Decision | Why |
|------|-------------|----------|-----|
| `viral_renderer.py` | DO NOT TOUCH. 1262-line deterministic PIL renderer for `VIRAL_SHORT_V2` scenes. All coordinates, depths, transitions, kinetic typography owned here. | KEEP (isolated, frozen) | Legacy viral pipeline must continue working. This file is sealed. No modifications unless a test breaks. |
| `viral_template.py` | Constants, brand theme, zone layout, safe zones, semantic visual plan, template context, QA scorecard. 738 lines. | KEEP (isolated) | Authoritative brand constants and layout primitives for viral pipeline. New productions reference `profiles/` and `creative/` instead, but this file remains untouched. |
| `animation.py` | Core PIL animation engine: element timing, easing, draw functions. 2120 lines. Used by both legacy and editorial renderers. | KEEP | Foundation of the PIL rendering stack. `build_scene()`, `make_scene_frames()`, `render_frame()` called by `create_short.py`. Keep intact. |
| `vo_composition_agent.py` | Layout arranger + VO VTT sync + progressive element sequencing. 340 lines. Bypassed for viral/editorial. | KEEP | Still used for legacy non-viral scenes. Adapts into the new scene composition layer later. |
| `video_encoder.py` | `FFmpegRawVideoEncoder` - streams raw PIL frames to FFmpeg via stdin pipe. | KEEP | Solid, reusable. Remains the local PIL->MP4 encoder. Remote Remotion renders bypass this. |

---

## Provider / Model Abstraction

| File | Current Role | Decision | Why |
|------|-------------|----------|-----|
| `models.py` | Discovers + ranks OpenAI / Gemini / OpenRouter / Ollama models. 317 lines. Caches in `.model_rank.json`. | KEEP | Provider abstraction is already well-designed. V2 wraps it via `tools/selectors/`. Do not duplicate. |
| `envfile.py` | `.env` loader. | KEEP | Tiny utility, no changes needed. |

---

## Asset Management

| File | Current Role | Decision | Why |
|------|-------------|----------|-----|
| `asset_manager.py` | Pre-renders logos, subscribe cards, AI icons (Pollinations API). 265 lines. | REFACTOR | Promoted into `stages/assets/asset_director.py`. `get_or_create_ai_icon()` becomes one entry in the asset fallback chain. Existing caching logic preserved. |
| `assets_library/` | Cached rendered assets (subscribe cards, icons). | KEEP | Reused as the local asset cache. New asset manifest records paths into here. |

---

## Audio / Music

| File | Current Role | Decision | Why |
|------|-------------|----------|-----|
| `create_short.py::generate_tts()` | Calls `edge-tts` CLI to produce MP3 + VTT subtitles. | REFACTOR | Extract to `audio/voice/tts_engine.py`. Interface preserved. |
| `create_short.py::parse_vtt()` | Parses VTT subtitle timestamps. | REFACTOR | Moves to `audio/voice/vtt_parser.py`. |
| `create_short.py` (audio concat + mix) | FFmpeg audio concat + music ducking + SFX mixing. Scattered inline. | REPLACE | Becomes `audio/mixer.py` + `audio/ducking.py` with an `audio_plan.json` contract. |
| `music_catalog.py` | Indexes local music tracks by mood. Smart mood matching. 115 lines. | KEEP | Referenced from new `stages/assets/` + `audio/` layer. |
| `sequence_director.py` | Sequence/outro logic. | REFACTOR | Review and absorb into stage pipeline. |

---

## Legacy Compatibility

| File | Current Role | Decision | Why |
|------|-------------|----------|-----|
| `legacy_adapter.py` | Converts legacy `elements[]` scene dicts into `visual_scene{}` schema. 80 lines. | KEEP -> promote to `compat/legacy_adapter.py` | Still needed. Wrap as `compat/legacy_adapter.py` and keep identical API. |
| `auditor.py` | `audit_thumbnail()` + `auto_heal_scene_blueprint()` - black-frame detection + scene auto-repair. | KEEP | Becomes part of `qa/visual_qa.py` integration. Keep existing implementation; wrap in new QA layer. |
| `reward_system.py` | Reward/scoring for scene quality. | DEPRECATE | Superseded by `review/reviewer.py` + diversity metrics in V2. |
| `refactor_script.py` | One-off migration utility. | DEPRECATE | Not part of production pipeline. |
| `inspect_manifest.py` | CLI tool for inspecting manifests. | KEEP | Still useful for debugging. |
| `check_jobs.py` | CLI for job status. | KEEP | Keep for remote worker monitoring. |
| `submit_job.py` | Remote job submission. | KEEP | Part of remote-first compute layer. |

---

## Scripts (utility)

| File | Current Role | Decision | Why |
|------|-------------|----------|-----|
| `scripts/benchmark_editorial_render.py` | Editorial render benchmark. | REFACTOR | Incorporate into `benchmarks/benchmark_editorial.py`. |
| `scripts/benchmark_render_plan_authority.py` | Render plan authority tests. | REFACTOR | Incorporate into `benchmarks/`. |
| `scripts/generate_and_qa_viral_v2.py` | End-to-end viral generation + QA. | KEEP -> move to `benchmarks/` | Reference implementation for end-to-end test. |
| `scripts/qa_editorial_video.py` | Editorial video QA script. 15K. | REFACTOR | Moves into `qa/` + `benchmarks/`. |
| `scripts/profile_frame.py` | Frame profiling. | KEEP | Performance debugging. |

---

## Tests

| File | Current Role | Decision | Why |
|------|-------------|----------|-----|
| `tests/test_viral_pipeline.py` | **26 tests: all passing.** Covers editorial plan, render plan authority, viral pipeline invariants, brand/CTA contracts, pixel-level change tests. | KEEP + EXPAND | Must not regress. V2 adds new test files alongside. Does not modify this file's existing tests. |

---

## Static / Templates / Output

| Path | Decision | Why |
|------|----------|-----|
| `static/` | KEEP | Web UI assets. |
| `templates/` | KEEP | Flask HTML templates. |
| `output/` | KEEP structure, extend | New productions write to `projects/<id>/` within output. Old flat structure remains for legacy outputs. |
| `AI SIMPLIFIED LAB/` | KEEP | Channel assets (music, logo, intros, outros). Referenced by new audio pipeline. |

---

## New Modules to Create (V2)

### production/
- `controller.py` - stateful production brain
- `state.py` - ProductionState Pydantic model
- `pipeline_loader.py` - loads YAML pipeline definitions
- `checkpoint.py` - stage checkpoint save/resume
- `stage_runner.py` - runs/retries individual stages
- `reviewer.py` - stage review orchestrator
- `artifact_store.py` - reads/writes persisted artifacts
- `art_direction.py` - art direction generation + persistence

### pipeline_defs/
- `youtube-short.yaml`
- `animated-explainer.yaml`
- `ai-news-short.yaml`
- `tutorial-short.yaml`

### schemas/artifacts/
- `research_brief.schema.json`
- `proposal_packet.schema.json`
- `script.schema.json`
- `art_direction.schema.json`
- `scene_plan.schema.json`
- `asset_manifest.schema.json`
- `edit_decisions.schema.json`
- `render_report.schema.json`
- `publish_log.schema.json`
- `review_report.schema.json`

### stages/
- `research/` - research_director.py, research_prompts.py, research_validator.py
- `proposal/` - proposal_director.py
- `script/` - script_director.py, timing.py, voice_performance.py, intent_classifier.py
- `scene_plan/` - scene_planner.py, variety_governor.py
- `assets/` - asset_director.py, asset_selector.py, asset_manifest.py
- `edit/` - edit_director.py

### composition/
- `runtime_router.py`
- `camera.py`
- `motion.py`
- `atelier/`
- `captions/caption_timeline.py`, `caption_renderer.py`
- `remotion/`
- `hyperframes/`
- `ffmpeg/`

### audio/
- `voice/tts_engine.py`, `vtt_parser.py`
- `music/music_selector.py`
- `sfx/sfx_library.py`
- `mixer.py`
- `ducking.py`
- `validator.py`

### tools/selectors/
- `tts_selector.py`, `image_selector.py`, `video_selector.py`
- `music_selector.py`, `diagram_selector.py`, `compose_selector.py`

### creative/
- `techniques/` - Visual technique library
- `variety.py` - Visual variety governor

### analysis/
- `video_reference.py` - Reference video analyzer

### qa/
- `visual_qa.py`, `frame_sampler.py`, `diversity_metrics.py`
- `motion_metrics.py`, `text_density.py`
- `black_frame_detector.py`, `freeze_detector.py`

### review/
- `reviewer.py`, `visual_reviewer.py`, `audio_reviewer.py`, `timeline_reviewer.py`

### governance/
- `cost_tracker.py`

### profiles/
- `youtube_short.json`, `youtube_video.json`

### compat/
- `legacy_adapter.py` (promote existing `legacy_adapter.py`)

### benchmarks/
- `benchmark_editorial.py`, `benchmark_diversity.py`, `benchmark_end_to_end.py`

### remotion-composer/
- Full React/TypeScript/Remotion composition engine

---

## Implementation Order

| Phase | Scope |
|-------|-------|
| **0** | Audit + docs (this document) — COMPLETE |
| **1** | Artifact schemas + production state + pipeline loader |
| **2** | Production controller + checkpoint/revision system |
| **3** | Research + proposal + art-direction stages |
| **4** | Script + scene-plan redesign |
| **5** | Asset manifest + provider selectors |
| **6** | Edit decisions |
| **7** | Composition runtime router |
| **8** | Remotion composition engine |
| **9** | Atelier mode |
| **10** | HyperFrames integration |
| **11** | Audio/caption/CTA integration |
| **12** | Review + QA + diversity metrics |
| **13** | Remote rendering integration |
| **14** | End-to-end benchmarks |
