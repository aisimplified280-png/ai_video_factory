---
name: documentation-contract-auditor
description: Audits documentation, rules, README, and skills against live code, eliminating contradictory architectural instructions and outdated guidelines.
---

# documentation-contract-auditor

## Purpose
Prevents documentation drift and contradictory guidelines. Guarantees that `.agents/rules.md`, `.agents/skills/`, `README.md`, and architecture docs accurately reflect active code contracts, so AI agents never reintroduce obsolete patterns.

## Trigger Conditions
- Triggered whenever modifying core architectural contracts (e.g. style systems, render engines, transitions).
- Triggered whenever updating skills or repository rules.
- Triggered during release readiness audits.

## Exact Inspection Targets
1. **Agent Guidelines**: `.agents/rules.md`, `.agents/skills/`.
2. **Project Documentation**: `README.md`, `docs/`, `profiles/`.
3. **Contradiction Auditing**:
   - Verify README mentions the Remotion engine, not deleted PIL renderers.
   - Verify rules specify royal blue (`#1A5CFF`) or Claude Editorial themes, not obsolete colors.
   - Verify transition guidelines match active code (e.g. non-zero overlap for match cuts).
   - Verify skill files refer to active entry points (`scripts/factory.py`, `app.py`), not deleted files (`create_short.py`, `animation.py`).

## Commands / Tools to Use
- `grep_search`: Scan docs and skills for deleted module names (`create_short`, `viral_renderer`, `animation.py`).
- Cross-reference rule statements against test assertions.

## Failure Conditions
- A documentation file or skill instructs the developer/agent to run a deleted or deprecated command.
- An agent rule contradicts a test in `tests/`.
- A design doc claims a feature exists that was never wired into `props_builder.py` or Remotion.

## Evidence Requirements
- Zero references to deleted legacy modules across all active skills and rules.
- Complete alignment between documented CLI commands and `argparse` options in `scripts/factory.py`.

## Output Format
```markdown
### Documentation Contract Audit
- Skills Accuracy: 100% (No references to legacy/deleted scripts)
- README Parity: Up-to-date with Autonomous Video Factory v2 & Remotion
- Rule Consistency: Confirmed aligned with active Phase 17 contracts
- Contract Drift Detected: NONE
```

## Stop Conditions
If documentation drift or contradictory agent instructions are found, update the documentation/skills immediately before proceeding with code changes.

## Interaction with Other Skills
- Feeds into **repo-forensics** and **self-healing-engineer**.
- Validates the guidelines referenced by all other skills.
