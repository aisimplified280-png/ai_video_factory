# Phase 2: ProductionController & Stage Orchestration Infrastructure

> AI Simplified Lab Video Factory V2 — Orchestration & Lifecycle Specification
> Architectural Benchmark: [OpenMontage](https://github.com/calesthio/OpenMontage)

---

## 1. Overview & Separation of Concerns

Phase 2 establishes the stateful orchestration layer. Crucially, **the controller only orchestrates; it does not implement domain work**.

```
                         ProductionController
                                  │
         ┌───────────────┬────────┴───────┬───────────────┐
         ▼               ▼                ▼               ▼
   PipelineLoader    StateStore     ArtifactStore    StageRunner
         │               │                │               │
  pipeline_defs/*.yaml   │                │        ┌──────┴──────┐
                         ▼                ▼        ▼             ▼
                 ProductionState   ArtifactEnvelope StageRegistry Dependencies
```

### Core Tenet
`controller.py` does not replace `create_short.py` with another monolithic script. It is an orchestration engine that drives stage transitions according to declarative YAML pipeline contracts, persists checkpoints at every boundary, tracks active artifact versions, and delegates domain generation to isolated handlers via `StageRunner`.

---

## 2. ProductionController (`production/controller.py`)

The central state machine controlling production lifecycles.

### Operations
| Operation | Description |
|-----------|-------------|
| `start(topic, pipeline, options)` | Creates unique `project_id`, initializes seed `brief/brief.json`, persists `ProductionState`, writes first checkpoint and audit log. |
| `resume(project_id)` | Loads state from disk, validates active artifacts, detects any stale downstream dependencies, and resumes at the next runnable stage without restarting completed work. |
| `status(project_id)` | Returns complete production telemetry: pipeline, status, active versions, stale artifacts, budget, revisions, and last checkpoint. |
| `run_next_stage(project_id)` | Executes the current runnable stage via `StageRunner`, evaluates approval policies, advances state idempotently. |
| `run_until_blocked(project_id)` | Sequentially executes runnable stages until blocked, waiting approval, completed, or failed. |
| `retry_stage(project_id, stage)` | Re-attempts a failed stage with identical inputs, incrementing revision counter. |
| `revise_stage(project_id, stage, notes)` | Re-runs stage with human/reviewer revision feedback, invalidating downstream artifacts. |
| `approve(project_id, stage)` | Marks artifact as approved in `ArtifactStore`, records decision, advances pipeline. |
| `reject(project_id, stage, reason)` | Marks artifact as rejected, records reason, increments revision count, invalidates downstream dependencies. |
| `abort(project_id, reason)` | Aborts production, halts future executions, preserves all state, artifacts, and history. |
| `rerender(project_id)` | Validates whether approved `edit_decisions` exists and is non-stale for rendering without invoking renderers. |

---

## 3. StageRunner & StageRegistry (`production/stage_runner.py`, `production/stage_registry.py`)

### Separation of Execution from Orchestration
`StageRunner` manages the lifecycle of executing a single stage:
1. **Pre-execution validation**: Verifies stage exists, production is not aborted, revision limit is not exceeded, and budget cap is not breached.
2. **Dependency resolution**: Locks exact active input versions and content hashes via `resolve_dependencies()`.
3. **Registry delegation**: Looks up the registered `StageHandler`.
   - In Phase 2: **No fake production handlers are registered**. Any unregistered stage returns explicit status `NOT_IMPLEMENTED`.
4. **Execution & Quality Gates**: If a handler runs, evaluates quality gates defined in `pipeline_defs/`.
5. **Persistence**: Creates `ArtifactEnvelope` with locked `parent_artifacts`, computes SHA-256 hash, and saves via `ArtifactStore`.
6. **Typed Result**: Returns structured [StageResult](file:///c:/Users/USER/Desktop/Youtube-AI_Simplified/AI-Simplified-Video-Factory/production/stage_runner.py#L29-L43) (`ready`, `waiting_approval`, `blocked`, `failed`, `not_implemented`).

---

## 4. Artifact Dependency Locking & Staleness Detection (`production/dependencies.py`)

Artifact lineage is strictly locked to prevent silent mutation:

```
research_brief v1 (sha256:aaa...)
       │
       ▼
proposal_packet v1 (parent_artifacts: [{type: research_brief, version: 1, hash: sha256:aaa...}])
```

If `research_brief v2` (`sha256:bbb...`) is later produced:
- `proposal_packet v1` on disk is **never modified or deleted** (preserving audit history).
- `is_artifact_stale(proposal_packet v1)` evaluates to `True` because parent locked version/hash no longer matches active `research_brief`.
- `invalidate_downstream()` removes stale artifacts from `state.active_artifact_versions`, ensuring stale data cannot be used as an input to downstream stages.

---

## 5. Checkpoints & Crash Recovery (`production/checkpoint.py`)

Every state transition writes an atomic checkpoint snapshot to `projects/<production_id>/checkpoints/chk_{seq:04d}_{event_type}.json`:
- `sequence`: Sequential integer (1, 2, 3...).
- `event_type`: `production_created`, `stage_started`, `stage_completed`, `artifact_approved`, `artifact_rejected`, etc.
- `state_hash`: Deterministic SHA-256 hash of `ProductionState`.
- `artifact_versions`: Active artifact versions at that moment.

### Crash Recovery
If a process terminates unexpectedly:
1. `controller.resume(project_id)` loads `production_state.json`.
2. Inspects last checkpoint and verifies artifact integrity on disk.
3. Downstream stale dependencies are cleaned up.
4. Identifies the next uncompleted stage.
5. Does **not** restart already-approved stages.

---

## 6. Audit Logging (`production/audit.py`)

Chronological audit events are appended to `projects/<production_id>/audit_log.jsonl`:
- Record format: `event_id`, `timestamp`, `event_type`, `stage`, `actor` (`system`, `human`, `llm`, `tool`), `severity`, `details`, `message`.

---

## 7. CLI Usage

All controller operations are accessible via `python -m production`:

```bash
# Start a production
python -m production start --pipeline youtube-short --topic "How AI Agents Work"

# Check production status
python -m production status <project_id>

# Run next stage (or all runnable stages until blocked)
python -m production run <project_id>
python -m production run <project_id> --until-blocked

# Resume after crash
python -m production resume <project_id>

# Human approval / rejection
python -m production approve <project_id> --stage proposal
python -m production reject <project_id> --stage proposal --reason "Need stronger hook"

# Retry / revise
python -m production retry <project_id> --stage research
python -m production revise <project_id> --stage proposal --notes "Emphasize multi-agent coordination"

# Abort
python -m production abort <project_id> --reason "User cancelled"

# Inspect rerender plan
python -m production rerender <project_id>
```
