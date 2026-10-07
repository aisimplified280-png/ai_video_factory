# Phase 1: Artifact & Pipeline Contract Infrastructure

> AI Simplified Lab Video Factory V2 — Foundation Infrastructure Specification
> Architectural Benchmark: [OpenMontage](https://github.com/calesthio/OpenMontage)

---

## 1. Overview & Architecture

Phase 1 establishes the contract and persistence infrastructure upon which all subsequent production stages (Phase 2+) depend. Rather than template-centric rendering with ad-hoc metadata, the factory is organized around:

1. **Typed Artifact Contracts**: Strict Pydantic V2 models and JSON Schemas governing stage outputs.
2. **Standardized Artifact Envelope**: Universal packaging containing provenance, versioning, deterministic hashing, and lifecycle status.
3. **Atomic Persistence (`ArtifactStore`)**: A single authoritative I/O boundary guaranteeing atomic writes, content hashing, immutability, and schema validation.
4. **Pipeline Definitions (`pipeline_defs/*.yaml`)**: Machine-validated topology defining stage order, inputs, outputs, quality gates, and runtime policies.
5. **State Management (`ProductionState` & `StateStore`)**: Deterministic lifecycle state with active artifact version tracking and audit logs.

```
       ProductionState
              │
              ▼
      Pipeline Definition
              │
              ▼
   ┌──────────────────────┐
   │    Stage Contract    │
   └──────────┬───────────┘
              │
      ┌───────┴───────┐
      ▼               ▼
ArtifactStore    PipelineValidator
      │
      ▼
Persisted Artifact (.v001.json)
```

---

## 2. Standard Artifact Envelope

Every artifact persisted in the factory wraps its domain payload inside `schemas/artifact_envelope.schema.json`.

### Envelope Structure

```json
{
  "artifact_type": "scene_plan",
  "schema_version": "2.0",
  "artifact_version": 1,
  "production_id": "proj_1234abcd",
  "stage": "scene_plan",
  "status": "ready",
  "created_at": "2026-10-05T14:30:00Z",
  "updated_at": "2026-10-05T14:30:00Z",
  "producer": {
    "kind": "llm",
    "provider": "gemini",
    "model": "gemini-2.0-flash",
    "estimated_cost": 0.002
  },
  "content_hash": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "parent_artifacts": [
    {
      "artifact_type": "script",
      "version": 1,
      "content_hash": "sha256:4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
    }
  ],
  "warnings": [],
  "metadata": {},
  "data": { ... }
}
```

### Required Fields
- `artifact_type`: Canonical snake_case name (e.g., `research_brief`, `scene_plan`).
- `schema_version`: Contract version (fixed at `"2.0"` for V2).
- `artifact_version`: Sequential integer (`1, 2, 3...`).
- `production_id`: Unique identifier for the production run.
- `stage`: Name of the pipeline stage that generated the artifact.
- `status`: Lifecycle state (`pending`, `generating`, `ready`, `failed`, `approved`, `rejected`).
- `created_at` / `updated_at`: ISO-8601 UTC timestamps.
- `producer`: Typed `ProducerInfo` recording kind (`system`, `human`, `llm`, `tool`, `provider`), provider, model, and costs.
- `content_hash`: Deterministic `sha256:` hash of the `data` payload.
- `data`: Domain payload validated against the artifact's specific schema.

---

## 3. Deterministic Content Hashing

Artifact integrity and lineage are guaranteed via deterministic SHA-256 hashing implemented in `ArtifactStore.compute_hash()`:

- **Canonical JSON formatting**: `sort_keys=True`, `separators=(',', ':')`, `ensure_ascii=False`.
- Whitespace and key order changes produce the exact same hash.
- Data modifications produce a different hash.
- Stored in the format: `sha256:<64-hex-characters>`.

---

## 4. Immutability & Versioning Rules

- **Approved artifacts are immutable**: Once an artifact version reaches status `approved`, it can never be overwritten with different data.
- **Revision workflow**: To modify an approved artifact, a new version is created (`v001` -> `v002`).
- **Auditability**: Rejected and previous versions remain on disk for inspection and debugging.
- **Failures**: If a stage fails (`failed`), the failed version is preserved, and a corrected version is generated with an incremented version number.

---

## 5. ArtifactStore (`production/artifact_store.py`)

`ArtifactStore` is the **single persistence abstraction** for the entire factory. Direct file writes to artifact folders are strictly prohibited.

### Public API
- `create(artifact_type, production_id, stage, data, producer, ...)`: Builds an `ArtifactEnvelope` with incremented version and computed hash.
- `save(envelope)`: Atomically writes the envelope to disk (`write .tmp` -> `fsync` -> `rename`), validates against JSON Schema, and updates `.latest.json`.
- `load(artifact_type, production_id, version=None)`: Loads artifact by version, or the latest version if omitted.
- `exists(artifact_type, production_id, version=None)`: Checks existence.
- `list_versions(artifact_type, production_id)`: Returns sorted list of integer versions on disk.
- `latest(artifact_type, production_id)`: Retrieves the active/latest envelope.
- `approve(artifact_type, production_id, version, actor="")`: Marks version as approved.
- `reject(artifact_type, production_id, version, reason="")`: Marks version as rejected.
- `mark_failed(artifact_type, production_id, version)`: Marks version as failed.
- `validate(envelope)`: Validates envelope and payload against schemas.

---

## 6. Directory Layout

Every production stores artifacts in a deterministic directory tree under `projects/<production_id>/`:

```
projects/<production_id>/
  production_state.json
  brief/
    brief.json
  research/
    research_brief.v001.json
    research_brief.latest.json
  proposal/
    proposal_packet.v001.json
    proposal_packet.latest.json
  script/
    script.v001.json
    script.latest.json
  direction/
    art_direction.v001.json
    art_direction.latest.json
  scenes/
    scene_plan.v001.json
    scene_plan.latest.json
  assets/
    asset_manifest.v001.json
    asset_manifest.latest.json
  edit/
    edit_decisions.v001.json
    edit_decisions.latest.json
  composition/
    render_report.v001.json
    render_report.latest.json
  review/
    review_report.v001.json
    review_report.latest.json
  publish/
    publish_log.v001.json
    publish_log.latest.json
```

---

## 7. Pipeline Definitions & Stage Contracts

Pipelines are declared in machine-validated YAML files under `pipeline_defs/`:

### Standard Pipelines
1. `youtube-short.yaml`: 30-60s vertical shorts (primary runtime: Remotion).
2. `animated-explainer.yaml`: 60-90s animated explainers (primary runtime: HyperFrames).
3. `ai-news-short.yaml`: 30-45s rapid-fire AI news breakdown (primary runtime: Remotion).
4. `tutorial-short.yaml`: 45-60s instructional short (primary runtime: FFmpeg/PIL).

### Stage Contract Rules
Each stage defines:
- `produces`: List of artifact types output by the stage.
- `consumes`: List of upstream artifact types required before the stage can run.
- `approval`: Approval policy (`auto`, `human`, `always_auto`).
- `max_revisions`: Maximum automated retry/revision loops allowed.
- `quality_gates`: Typed validation checks (`min`, `max`, `bool`, `presence`, `regex`).

---

## 8. PipelineLoader & PipelineValidator

- `PipelineLoader` (`production/pipeline_loader.py`): The single parser for pipeline YAML definitions with in-memory caching.
- `PipelineValidator` (`production/pipeline_validator.py`): Performs structural validation:
  - Stage name uniqueness.
  - Required stage existence.
  - Upstream artifact dependency resolution.
  - Circular dependency prevention using Kahn's topological sort algorithm.
  - Quality gate threshold and pattern integrity.
  - Runtime policy validity (`remotion`, `hyperframes`, `ffmpeg_pil`).
  - Budget policy constraints.

---

## 9. ProductionState (`production/state.py`)

`ProductionState` is the single source of truth for the ongoing lifecycle of a production. It records:
- `project_id`, `pipeline`, `pipeline_version`, `run_mode`.
- `status` (`created`, `running`, `waiting_approval`, `blocked`, `completed`, `failed`, `aborted`).
- `current_stage`.
- `active_artifact_versions`: Explicit mapping (e.g., `{"research_brief": 1, "proposal_packet": 2}`).
- `budget`: `BudgetState` tracking `budget_cap`, `estimated_cost`, `actual_cost`, and `remaining_budget`.
- `revision_count`: Per-stage counters to enforce max revisions.
- `decisions`, `warnings`, `errors`: Full auditable event trail.

`StateStore` manages reading and writing `ProductionState` to disk with atomic file updates.

---

## 10. CLI Usage

The production infrastructure provides a unified command line interface:

```bash
# Validate pipeline definition
python -m production validate-pipeline youtube-short

# Inspect stage topology and contracts
python -m production inspect-pipeline youtube-short

# List available pipelines
python -m production list-pipelines

# Validate an artifact JSON file
python -m production artifact-validate tests/fixtures/sample_production/research/research_brief.v001.json

# Compute canonical deterministic hash
python -m production artifact-hash tests/fixtures/sample_production/research/research_brief.v001.json
```
