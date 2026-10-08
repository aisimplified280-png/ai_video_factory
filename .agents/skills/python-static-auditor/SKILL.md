---
name: python-static-auditor
description: Finds Python runtime hazards, missing imports, swallowed failures, platform assumptions, and dead paths.
---
# Python Static Auditor

Audit every production Python file.

Check:
- undefined names/missing imports
- unreachable branches
- circular imports
- broad exception swallowing
- silent pass in production paths
- subprocess lifecycle
- path/platform assumptions
- unsafe shell/process operations
- version hardcoding
- schema/model mismatches
- stale imports
- direct calls that bypass StageRunner contracts

Run compile/static checks where available and supplement them with source-level inspection.

Every finding must include file, line, symptom, severity, and runtime consequence.
