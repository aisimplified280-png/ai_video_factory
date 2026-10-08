# Phase 18 Repository Audit — 2026-10-08

Repository: aisimplified280-png/ai_video_factory
Audited head: 709387f40d0beabc7b66c626935972a7da91f36d

## Inventory

Current tree contains 397 entries:
- 338 files
- 59 directories
- 222 Python files
- 35 TypeScript files
- 15 TSX files
- 23 JSON files
- 22 Markdown files
- 4 YAML files
- 1 Colab notebook

Primary execution areas:
production/, stages/, composition/, remotion-composer/, scripts/, schemas/, tests/, pipeline_defs/, docs/, .agents/

## Release-blocking findings

### P0 — Latest audio patch has a missing import
composition/remotion/props_builder.py now reads os.environ for the media port but the module does not import os.

### P0 — Phase 17 sync can overwrite richer canonical scene planning
production/phase17/sync.py creates a new reduced scene_plan after edit_decisions exist. It replaces rich scene fields with defaults and an environment label such as "Phase 17 Environment Stage N".

### P0 — Phase 17 transitions are computed and discarded
phase17/sync.py calls assign_transformative_transitions() but does not use the returned transitions. scripts/factory.py still writes transition_out as hard_cut for every scene.

### P0 — The production factory bypasses the canonical stage authority
scripts/factory.py directly invokes phase-specific functions and render/QA commands rather than driving the configured PipelineLoader + StageRunner + StageRegistry contracts end-to-end.

### P0 — Failed technical QA does not block release
scripts/factory.py logs a warning when cmd_qa() fails and continues copying the MP4 into the final release package. The completion path can still report release readiness.

### P0 — Visual rendering still contains scene-ID mega-templates
remotion-composer/src/primitives/ActionLayer.tsx is over 2,100 lines and branches on scene_01/02/etc with fixed geometry and text.
BackgroundLayer.tsx also branches on scene IDs and global isAITopic heuristics.

### P0 — Global AI mode can force unrelated scenes through the same rendering path
ProductionComposition.tsx calculates one isAITopic boolean for the production and passes it into every scene.

### P0 — Current visual QA is not an independent visual judge
Phase 15 and Phase 16 contain keyword/metadata-based grounding. Phase 17 improves frame evidence but still uses metadata for portions of environment/depth/transition evaluation.

## P1 — Reliability / contract findings

### P1 — render_report version is hardcoded
scripts/run_local_production.py writes render_report artifact_version=1 instead of using ArtifactStore versioning.

### P1 — audio stream detection is too weak
cmd_qa() treats stream count > 1 as audio_present. It should inspect ffprobe codec_type=audio.

### P1 — Active pipeline definitions still mention ffmpeg_pil
pipeline_defs/*.yaml and schemas/models/pipeline.py describe a legacy runtime that current Remotion runtime code refuses to execute.

### P1 — Scene planner and transition planner still encode forbidden/legacy transition defaults
stages/scene_plan/scene_planner.py and stages/edit/transition_planner.py contain cut/fade/cross-dissolve defaults that conflict with the active transformative-transition contract.

### P1 — Phase 17 environment selection is still partly scene-index-driven
environment_generator.py routes within a domain using scene index, which can repeat archetypes for equivalent scene positions across topics.

### P1 — Asset manifest does not represent actual bg/mid/fg layer assets
phase17/sync.py registers only a primary composite asset even though the Phase 17 generator supports separate layer images.

### P1 — Stage/test ecosystem contains legacy assumptions
Several tests still exercise ffmpeg_pil and hardcoded scene IDs; many are valid unit fixtures, but they must not be mistaken for proof of current production behavior.

## Stale instruction problems

The following still describe obsolete behavior:
- .agents/rules.md was previously forbidding characters and enforcing legacy dotted-grid/magenta styling; Phase 18 updates it.
- json-to-pydantic previously rejected character fields; Phase 18 updates it.
- video-renderer and whisper-aligner previously referenced create_short.py and the old PIL path; Phase 18 updates them.
- README.md describes create_short.py, Pillow, 720x1280 output, and local PIL rendering.
- docs/ARCHITECTURE_V2.md and docs/MIGRATION_MAP.md still contain active-looking legacy runtime references.
- pipeline definitions retain ffmpeg_pil compatibility language.

Historical documents may remain, but they must be clearly historical and cannot be used as current agent instructions.

## Phase 18 target architecture

The canonical creative contract is:

script
→ semantic scene plan
→ mascot/character plan
→ semantic environment decision
→ layer/asset manifest
→ edit decisions
→ Remotion props
→ Remotion composition
→ encoded MP4
→ independent visual judge ensemble
→ technical/render report
→ release gate

Visual truth is the encoded MP4.

The new agent skills enforce:
repo forensics, contract tracing, render truth, semantic grounding, diversity, temporal motion, depth/parallax, transitions, composition, cinematic quality, captions/safe zones, continuity, character behavior, camera execution, adversarial QA, cross-topic benchmarking, regression isolation, process safety, dependency/security, documentation consistency, and self-healing.

## Important evidence rule

A metadata field can describe intent. It cannot prove the viewer saw that intent.

Every visual quality claim should have frame/timestamp evidence from the encoded output.
