---
name: artifact-lineage-auditor
description: Proves artifact versions, hashes, parents, approvals, and active pointers remain coherent through production and release.
---
# Artifact Lineage Auditor

Trace:
proposal_packet
→ art_direction
→ script
→ scene_plan
→ asset_manifest
→ edit_decisions
→ render_report
→ review/QA
→ publish/release

Check:
- every artifact has correct producer
- parent hashes are valid
- active version matches consumed version
- no rich artifact is silently replaced by a reduced version
- generated assets are registered
- report versions are never hardcoded
- latest pointers are updated atomically
- release files correspond to the passing artifact versions

A release cannot be considered valid when artifact lineage is inconsistent even if the MP4 happens to render.
