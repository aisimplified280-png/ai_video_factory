# OPENMONTAGE COMPARISON

> Analysis of OpenMontage architectural principles vs AI Simplified Lab current state.
> Implementation decisions for V2.
> Reference: https://github.com/calesthio/OpenMontage

---

## Overview

OpenMontage is an open-source automated video production system built around:
- Declarative scene grammar separate from rendering runtime
- Explicit stage-gate architecture with artifact contracts
- Runtime locking at composition time (no silent swaps)
- Stage-by-stage review gates (not just final review)
- Atelier composition mode for custom visual authorship

This comparison identifies gaps and documents implementation decisions.
We are NOT copying OpenMontage code. We are implementing original solutions
that address the same architectural problems.

---

## Capability Comparison Table

| OpenMontage Capability | AI Simplified Lab Current | Gap | Implementation Decision |
|------------------------|--------------------------|-----|------------------------|
| **Artifact chain with typed contracts** | Multiple competing sources: `visual_plan`, `render_plan`, `semantic_visual_plan`, `storyboard`, `template_context` | Critical: no single source of truth | Create canonical 9-artifact chain (research_brief → publish_log). All artifacts are Pydantic models with JSON schema validation. Old plans become legacy provenance only. |
| **Production controller with stateful stages** | `run_pipeline()` monolith (630 lines). Single function, no checkpointing. | Critical: entire pipeline reruns on failure | Create `production/controller.py` with `ProductionState`. Each stage checkpointed independently. Retry/revise single stages. |
| **Pipeline definitions as config** | Pipeline behavior hard-coded in `create_short.py`. Style = `auto_detect_style()` choice. | Major: cannot change pipeline without code change | Create YAML pipeline definitions in `pipeline_defs/`. Pipeline is data, not code. |
| **Research stage with real sources** | No research stage. LLM generates content from topic string alone. | Critical: all content is hallucinated | Create `stages/research/research_director.py`. For AI news: web search required. Quality gate: 5 sources, 3 facts, 3 angles. |
| **Proposal with 2-3 distinct creative concepts** | Storyboard generated directly. One concept only. No creative choice step. | Major: no creative selection, no renderer lock | Create `stages/proposal/proposal_director.py`. 2-3 genuinely different concepts with renderer locked at approval. |
| **Explicit art direction before scene planning** | No art direction stage. Visual style derived from `style_name` string only. Same palette/layout across all productions. | Critical: visual homogeneity | Create `production/art_direction.py`. Art direction persisted as `art_direction.json` before scene planning begins. |
| **Semantic scene planning (not template selection)** | `editorial/planner.py` produces `layout_family` + `primitive` + `action`. Template-centric. | Critical: scenes are layout choices, not narrative choices | Redesign scene planner around 10-question scene contract. Every field maps to execution. `scene_plan.json` is the authoritative creative brief for composition. |
| **Runtime locking at proposal** | Runtime selection scattered: `viral_renderer.py` vs `editorial/executor.py` vs `animation.py`. Selected by type-checking scene dicts at render time. | Major: runtime can change unexpectedly | Runtime locked in proposal packet. `composition_mode` field in `edit_decisions.json` cannot be overridden. |
| **Stage-by-stage review gates** | No review gates. QA only via optional `--visual-debug` flag writing `render_qa.json`. | Major: errors compound through pipeline | Create `review/reviewer.py` with stage-specific reviewers. Each reviewer produces structured `finding/evidence/severity/impact/correction`. |
| **Automatic send-back loop** | No send-back. Pipeline runs linearly. Failed stage = abort. | Major: entire pipeline must restart on any failure | Controller tracks `revision_count` per stage. Auto-sends back to stage that produced bad artifact. Max 3 revisions. |
| **Visual variety governor** | No variety enforcement. Scenes can be visually identical. | Major: repetitive video output is accepted | Create `creative/variety.py`. Hard constraints before scene plan approval. |
| **Visual technique library** | No technique library. Layout family (`network`, `process_flow`, etc.) is the only vocabulary. | Major: limited expressive range | Create `creative/techniques/` with 20+ named techniques that inform scene planning without being templates. |
| **Asset manifest with WHY field** | Assets created on-demand during scene loop. No record of why an asset exists. | Major: cannot audit asset purpose, no fallback chain | Create `stages/assets/asset_manifest.py`. Every asset has `purpose`, `source`, `fallback_chain`, `status`. |
| **Provider selectors (ranked, not hard-coded)** | `models.py` ranks text models. No selectors for image/video/TTS/music/diagram. | Moderate: image provider selection is implicit | Create `tools/selectors/` with capability-aware selectors for each asset type. |
| **Atelier composition mode** | No atelier mode. Every video uses same component library (TextCard, StatCard, etc.) with different content. | Critical: visual identity of each video is identical | Create `composition/atelier/`. Atelier productions have `art-direction.md` + `composition-plan.json`. Custom geometry, timing, layer relationships per production. |
| **Remotion as primary composition runtime** | PIL + FFmpeg only. No web-native composition. | Major: limited composition expressiveness | Create `remotion-composer/` with React/TypeScript/Remotion. `ProductionComposition` reads `edit_decisions.json` and executes it. Components are engine primitives, not creative templates. |
| **HyperFrames for motion graphics** | Not present. | Minor (optional runtime) | Create optional `composition/hyperframes/` integration. Locked at proposal. Hard blocker if unavailable when locked. No silent Remotion fallback. |
| **Camera system (executable)** | Camera behavior labels exist in `render_plan.camera` but are metadata only. `edit_reader/executor.py` implements partial camera effects. | Major: camera labels not reliably executed | Create `composition/camera.py` with executable camera behaviors. PIL: Ken Burns/parallax implemented. Remotion: actual camera transforms. |
| **Motion system (semantic actions)** | `editorial/motion.py` maps intent to motion labels. Some executed in `executor.py`. | Moderate: action labels partially executed | Create `composition/motion.py` with 20+ semantic actions that have actual visual implementations. |
| **Caption system (first-class timeline)** | Captions via VTT sync baked into frame render. Safe zones not always enforced. | Moderate: captions not independent timeline track | Create `composition/captions/` with independent caption timeline. Word-highlight and karaoke modes. Safe zones enforced. |
| **CTA as planned scene** | CTA appended as conditional afterthought in `run_pipeline()`. Not always present. | Major: CTA can be missing or malformed | CTA is always the final planned scene in scene_plan. Verified present in QA. |
| **Audio pipeline with plan artifact** | Audio mixed inline in `run_pipeline()`. No audio plan artifact. | Moderate: audio decisions are implicit | Create `audio/` module + `audio_plan.json`. All mix decisions explicit before rendering. |
| **Visual QA on encoded MP4** | Basic `audit_thumbnail()` on PIL frames. `render_qa.json` checks scene dict fields, not pixels. | Major: QA does not validate final MP4 | Create `qa/visual_qa.py` that samples actual encoded MP4 frames. Frame sampler + black/freeze/diversity detectors. |
| **Cost governance** | No budget tracking. Provider calls can be unlimited. | Moderate: production costs uncontrolled | Create `governance/cost_tracker.py`. Budget cap enforced. Expensive generation requires available budget. |
| **Remote-first rendering** | Existing: `submit_job.py`, `check_jobs.py`, `SharedDriveStorage`. Works. | KEEP: already well-designed | Extend existing remote worker system to support Remotion render jobs. No architectural change needed. |
| **Reference video analysis** | Not present. | Minor (optional feature) | Create `analysis/video_reference.py`. Optional input. Produces `reference_analysis.json` (pacing, composition, shot duration, etc.). New concept inspired by structure, not copied. |
| **Media profiles** | Resolution/FPS constants scattered: `viral_template.py` (W=1080, H=1920, FPS=24), `create_short.py` (FPS from animation). | Minor: constants could diverge | Create `profiles/youtube_short.json`. All platform settings from profile. |
| **Legacy compatibility layer** | `legacy_adapter.py` converts old elements. Works but is thin. | KEEP: already handles core case | Promote to `compat/legacy_adapter.py`. After conversion, new artifacts are authoritative. Legacy viral/editorial renderers remain isolated. |
| **Benchmark suite** | Scripts in `scripts/`. Not structured as benchmarks. | Moderate: no systematic benchmark | Create `benchmarks/` with 5 topic benchmarks. Each produces full artifact chain + contact sheet from representative frames. |
| **End-to-end acceptance test** | No single automated E2E test that validates final MP4. | Major: system correctness not verified end-to-end | Create `benchmarks/benchmark_end_to_end.py`. Must produce playable MP4 with correct duration, codec, narration, captions, CTA, QA pass. |

---

## Key Architectural Differences from OpenMontage

### 1. Rendering Stack
- **OpenMontage**: Primarily web-native composition
- **AI Simplified Lab V2**: Hybrid — PIL for legacy viral/editorial (preserved), Remotion for new productions, HyperFrames optional

### 2. LLM Provider Strategy
- **OpenMontage**: Specific provider assumptions
- **AI Simplified Lab V2**: Provider-agnostic via existing `models.py` abstraction. Selectors rank by capability + continuity + cost. No hard-coded "Gemini always wins."

### 3. Local vs Remote
- **OpenMontage**: Primarily local execution
- **AI Simplified Lab V2**: Remote-first. Planning local. Heavy generation + rendering routes to Colab/GDrive workers. Local machine never requires GPU.

### 4. Runtime Fallback Policy
- **OpenMontage**: Had issues with silent runtime fallback (noted in spec)
- **AI Simplified Lab V2**: **Stricter than OpenMontage.** If HyperFrames locked + unavailable: hard blocker. No silent substitute.

### 5. Brand Consistency Model
- **OpenMontage**: Component-library consistency
- **AI Simplified Lab V2**: Consistency through typography + palette + spacing + audio identity ONLY. Not through repeated visual skeletons. Every production must have a different visual metaphor.

---

## Gaps Not in OpenMontage (Original Features)

| Feature | Rationale |
|---------|-----------|
| **Visual variety governor** | OpenMontage doesn't explicitly govern scene repetition. AI Simplified Lab needs this because LLM tends to generate repetitive layouts. |
| **Art direction dials (1-10)** | Explicit numeric dials for `visual_variance`, `motion_intensity`, `information_density` — not in OpenMontage. Makes art direction machine-operable. |
| **Channel CTA as first-class scene** | Specific to AI Simplified Lab brand requirements. |
| **edge-tts first-class integration** | Free, high-quality TTS without API cost. Not in OpenMontage. |
| **Existing PIL/FFmpeg renderer preservation** | OpenMontage doesn't have a legacy renderer to preserve. We must coexist. |
| **Remote Colab/GDrive compute** | Specific to AI Simplified Lab deployment constraints (no local GPU). |

---

## Summary: What We Take from OpenMontage

We take **principles**, not code:

1. Artifact contracts as stage boundaries
2. Runtime locking before composition
3. Stage-by-stage review (not just final QA)
4. Atelier mode for custom visual authorship
5. Composition components as engine primitives, not creative templates
6. The `edit_decisions` file as the authoritative timeline contract
7. Strict separation of "what to show" (scene_plan) from "how to render" (composition runtime)

Everything else is original implementation adapted to the AI Simplified Lab constraints.
