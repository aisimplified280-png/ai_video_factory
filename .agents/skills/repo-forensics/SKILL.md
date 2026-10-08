---
name: repo-forensics
description: Maps the entire video-factory repository and finds dead, duplicate, conflicting, or bypassed architecture.
---
# Repo Forensics

Scan the complete repository before proposing architectural changes.

Inventory Python, TypeScript/TSX, MJS, YAML, JSON schemas/models, tests, scripts, workers, docs, agent rules, generated assets, and configuration.

Build a dependency map covering:
- production entry points
- stage registry/runner/controller
- research → script → planning → assets → edit → props → Remotion → MP4 → QA → release
- artifact producers and consumers
- runtime locks
- local and remote workers
- visual generators and render primitives
- QA/report/release paths

Detect and report:
- duplicate visual brains
- scene-ID template branches
- stale legacy engines
- unreachable handlers
- direct imports that bypass canonical stages
- documentation/rule contradictions
- schemas that describe fields no active producer writes
- fields produced but never consumed
- assets produced but never registered
- QA reports that are generated but not gating release
- tests that exercise only mocks/fixtures for production-critical behavior

Never delete code solely because it is unused. Classify it as active, compatibility, dead/orphaned, or conflicting and identify evidence.

Output a machine-readable audit with path, category, severity, evidence, root-cause hypothesis, and recommended action.
