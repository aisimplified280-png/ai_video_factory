---
name: architecture-contract-guardian
description: Verifies that every important creative and runtime decision travels from source to pixels and release without being overwritten or bypassed.
---
# Architecture Contract Guardian

For every production, trace these contracts:

script
→ scene_plan
→ character_plan
→ visual/environment decision
→ asset_manifest
→ edit_decisions
→ Remotion props
→ composition
→ encoded MP4
→ visual QA
→ render report
→ release package

For each important field, record:
- producer
- artifact/version/hash
- consumer
- transformation
- whether it changes rendered pixels
- evidence

Required fields include subject, action, visual_purpose, visual_metaphor, domain, environment, camera_intent, motion_intent, character_role, character_action, depth_strategy, transition intent, asset IDs, audio refs, and timing.

Fail the audit when:
- a later artifact silently replaces a richer earlier artifact
- Phase 17 creates a stripped-down scene_plan after edit decisions already exist
- edit decisions describe transitions that are discarded before render
- generated bg/mid/fg assets are not canonical manifest entries
- renderer uses different defaults than the artifact contract
- QA evaluates one artifact while release copies another
- report versions are hardcoded
- release succeeds despite failed blocking QA

Do not accept metadata existence as proof that a field affects pixels.
