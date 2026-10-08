---
name: architecture-contract-guardian
description: Traces and enforces end-to-end data lineage from LLM planner through canonical artifacts, props, Remotion composition, to encoded MP4 pixels.
---

# architecture-contract-guardian

## Purpose
Guarantees that no feature is treated as implemented merely because a Python function or TypeScript component exists. Every field and semantic capability must be verified across the unbroken chain:
`LLM/planner -> canonical artifact -> sync -> asset manifest -> edit decisions -> props -> Remotion -> encoded MP4 -> QA`.

## Trigger Conditions
- Triggered whenever adding or modifying a visual, audio, transition, timing, or metadata property.
- Triggered whenever diagnosing why a planned visual or semantic intent failed to appear on screen.
- Triggered during final release gate verification.

## Exact Inspection Targets
1. **Creation**: `production/phase9/`, `production/phase11/`, `production/phase16/`, `production/phase17/`.
2. **Persistence**: `production/artifact_store.py`, `schemas/models/`.
3. **Synchronization**: `production/phase17/sync.py`, `production/phase16/sync.py`.
4. **Projection**: `composition/remotion/props_builder.py`.
5. **Consumption**: `remotion-composer/src/compositions/SceneComposition.tsx`, `remotion-composer/src/primitives/`.
6. **Pixel Verification**: `production/phase17/visual_qa.py`, `production/phase16/human_qa.py`, `scripts/qa_editorial_video.py`.

## Commands / Tools to Use
- `grep_search`: Trace field name across the 7 required architectural stages.
- `python scripts/run_local_production.py --production <id> --validate`: Validate schema contracts.
- `view_file`: Confirm Remotion React components consume the field in JSX.

## Failure Conditions
- A field exists in `scene_plan` or `plan_data` but is omitted in `props_builder.py`.
- A field exists in `props.json` but is ignored or hardcoded in `SceneComposition.tsx`, `ActionLayer.tsx`, or `BackgroundLayer.tsx`.
- A field claims to create visual change but has no corresponding evidence check in visual QA.

## Evidence Requirements
Written trace proving:
1. Field origin in planner/script.
2. Canonical artifact storage & schema validation.
3. Sync propagation into edit decisions/props.
4. Active rendering consumption in Remotion React components.
5. Measured pixel impact in encoded MP4 frames.

## Output Format
```markdown
### Architecture Contract Trace: [Field/Capability]
1. Origin: [File & line]
2. Persisted: [Artifact name & version]
3. Props Built: [props.json key path]
4. Rendered: [React component & JSX line]
5. Pixel Impact: [Measured evidence in frame]
6. Verification Status: UNBROKEN | BROKEN (at step N)
```

## Stop Conditions
If any link in the chain is broken, block the task immediately until the propagation is wired end-to-end.

## Interaction with Other Skills
- Consumes dependencies mapped by **repo-forensics**.
- Feeds requirements into **typescript-remotion-auditor** and **render-truth-auditor**.
