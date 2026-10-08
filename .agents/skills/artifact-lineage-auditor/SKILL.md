---
name: artifact-lineage-auditor
description: Verifies immutable artifact progression, versioning, SHA-256 hash integrity, and strict active-version authority across the production pipeline.
---

# artifact-lineage-auditor

## Purpose
Enforces the immutable, verifiable artifact chain:
`research -> proposal -> script -> art_direction -> scene_plan -> asset_manifest -> edit_decisions -> composition -> render_report -> review -> qa -> publish`.
Prevents stale or unapproved artifacts from leaking into production renders.

## Trigger Conditions
- Triggered whenever pipeline stages transition or state envelopes are saved.
- Triggered when verifying pipeline re-runs or caching behavior.
- Triggered before generating release packages in `output/<slug>/`.

## Exact Inspection Targets
1. **Artifact Store**: `production/artifact_store.py` (`projects/<production_id>/...`).
2. **State Store**: `production/state_store.py` (`production_state.json`).
3. **Envelope Metadata**: `artifact_type`, `version`, `content_hash` (`sha256:`), `producer`, `approval_status`.
4. **Active Version Pointers**: State store `active_versions` mapping to valid approved artifacts.

## Commands / Tools to Use
- `pytest tests/test_artifact_store.py -v`: Tests artifact hash determinism and version immutability.
- `pytest tests/test_production_controller.py -v`: Tests stage transitions and lineage tracking.
- Direct JSON inspection of `projects/<id>/edit/edit_decisions.v*.json` and `scene_plan.v*.json`.

## Failure Conditions
- A downstream stage consumes an artifact version that was not approved.
- Content hash of a loaded artifact does not match its stored `sha256:` envelope digest.
- An approved artifact file is mutated in place without creating a new version.
- A legacy unversioned file overrides a canonical versioned artifact.

## Evidence Requirements
- Log of verified artifact versions and hashes for the production run.
- Proof that `state.active_versions` points exclusively to approved envelopes.

## Output Format
```markdown
### Artifact Lineage Audit Report: [Production ID]
- Script: v001 (Approved, Hash Verified)
- Proposal Packet: v001 (Approved, Hash Verified)
- Edit Decisions: v001 (Approved, Hash Verified)
- Asset Manifest: v001 (Approved, Hash Verified)
- Lineage Integrity: 100% UNBROKEN
```

## Stop Conditions
Halt immediately if any corrupted JSON, hash mismatch, or unapproved artifact is detected in the active pipeline path.

## Interaction with Other Skills
- Enforces data integrity for **architecture-contract-guardian**.
- Supplies ground truth to **render-truth-auditor**.
