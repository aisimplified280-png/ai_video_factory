---
name: repo-forensics
description: Maps the entire repository architecture, dependencies, artifact lineage, and identifies orphan/dead code before any edits.
---

# repo-forensics

## Purpose
Map the entire repository architecture, dependency graph, execution paths, and contract relationships before any code modifications occur. Prohibit any blind edits.

## Trigger Conditions
- Triggered as the first step before ANY multi-file refactor, architecture update, or bug remediation.
- Triggered whenever an unknown import, missing artifact, or contradictory contract is encountered.
- Triggered when auditing legacy vs canonical execution paths.

## Exact Inspection Targets
1. **Source Code**: Python modules (`production/`, `composition/`, `scripts/`, `schemas/`), TypeScript/TSX components (`remotion-composer/src/`).
2. **Contract Schemas**: `schemas/models/`, `pipeline_defs/`, `profiles/`.
3. **Artifact Flow**: Producers in `production/` vs consumers in `composition/` and `scripts/`.
4. **Configuration & Rules**: `.agents/rules.md`, `pytest.ini`, `.env`, `package.json`.
5. **Execution Entrypoints**: `app.py`, `scripts/factory.py`, `composition/remotion/runtime.py`.

## Commands / Tools to Use
- `grep_search`: Find all usages, import statements, and references.
- `list_dir`: Recursively map active directory structures.
- `python -m compileall -q <dir>`: Ensure all Python files compile cleanly.
- `npm run --prefix remotion-composer build`: Verify TypeScript compilation and export tree.

## Failure Conditions
- Any file is edited without first identifying all upstream producers and downstream consumers.
- Dead, orphan, or unreferenced files exist in the active production execution path.
- Dual execution paths exist where a legacy module duplicates a canonical pipeline stage.

## Evidence Requirements
- Complete list of affected files with inbound and outbound dependency links.
- Verified absence of stale shadow implementations.
- Producer-to-consumer chain verification for all touched fields.

## Output Format
```markdown
### Repo Forensics Report: [Subsystem/Feature]
- **Target Files**: [List of paths]
- **Producers**: [Upstream callers]
- **Consumers**: [Downstream modules]
- **Artifact Dependencies**: [Associated schema/envelope types]
- **Orphan/Dead Code Detected**: [None | List of items]
- **Clearance to Proceed**: YES | NO
```

## Stop Conditions
Halt immediately and report to the engineer if a contradictory contract, circular dependency, or dead shadow implementation is detected.

## Interaction with Other Skills
- Feeds into **architecture-contract-guardian** with the complete dependency map.
- Feeds into **regression-bisector** when identifying historical regressions.
