---
name: self-healing-engineer
description: Master autonomous orchestrator driving the full cycle: Observe -> Map -> Reproduce -> Root Cause -> Patch -> Test -> Real Render -> Encoded QA -> Adversarial QA -> Re-Audit -> Commit.
---

# self-healing-engineer

## Purpose
Acts as the principal autonomous orchestrator for the entire Video Factory repository. Never simply patches a file in isolation. Drives the complete, disciplined engineering lifecycle:
`OBSERVE -> MAP -> REPRODUCE -> ROOT CAUSE -> MINIMAL PATCH -> TARGETED TEST -> INTEGRATION TEST -> FULL TEST SUITE -> REAL RENDER -> ENCODED MP4 QA -> ADVERSARIAL QA -> REGRESSION CHECK -> DOCUMENT CONTRACT -> COMMIT -> RE-AUDIT`.

## Golden Rule
A green test suite does NOT mean the system is fixed. A fix is complete only when:
`Root cause solved AND Regression test added AND Integration path verified AND Real render verified AND Encoded MP4 verified AND QA verified AND Zero new regressions detected`.

## Trigger Conditions
- Triggered for every bug fix, GitHub issue remediation, or architectural upgrade.
- Triggered whenever an autonomous video production run fails.
- Triggered as the master loop when resolving the backlog (#11 through #15).

## Exact Inspection Targets
1. **Repository Health**: All 12 subordinate skills.
2. **Issue Under Investigation**: Full root-cause trace from symptom to underlying defect.
3. **End-to-End Pipeline**: `scripts/factory.py`, `app.py`, `production/`, `composition/`, `remotion-composer/`.

## Execution Workflow
1. **OBSERVE & REPO FORENSICS**:
   - Invoke **repo-forensics** to map all related files, schemas, and contracts.
2. **REPRODUCE**:
   - Write a minimal failing test that deterministically reproduces the defect.
   - Run the test to confirm it fails with the exact expected error.
3. **ROOT CAUSE ANALYSIS**:
   - Use **regression-bisector** if a recent regression, or **architecture-contract-guardian** if a contract disconnect.
4. **MINIMAL SURGICAL PATCH**:
   - Apply the targeted fix. Run **python-static-auditor** and/or **typescript-remotion-auditor** immediately to ensure clean compilation.
5. **TARGETED & INTEGRATION TESTS**:
   - Run the reproduction test; verify it now passes.
   - Run surrounding integration tests.
6. **REAL RENDER & ENCODED MP4 AUDIT**:
   - Trigger a real Remotion render.
   - Invoke **render-truth-auditor** to verify ffprobe properties, audio streams, frame activity, and deciles.
7. **ADVERSARIAL QA & BENCHMARKS**:
   - Invoke **visual-semantic-adversary** to confirm the fix cannot be gamed.
   - Invoke **cross-topic-benchmark** to ensure visual diversity is preserved.
8. **DOCUMENTATION PARITY**:
   - Invoke **documentation-contract-auditor** to keep docs and agent rules in sync.
9. **COMMIT & AUDIT**:
   - Commit with structured commit message linking the issue number.
   - Push to `origin main`.
   - Re-audit for any side-effects.

## Failure Conditions
- Skipping any stage in the workflow because "unit tests passed".
- Declaring an issue fixed without verifying the actual rendered MP4 output.
- Introducing a regression in any previously passing test.

## Output Format
```markdown
### Self-Healing Engineer Release Gate Report
- **Issue**: #[Number] - [Title]
- **Root Cause**: [Detailed explanation of defect mechanism]
- **Reproduction Test**: [Path to added test file & test function]
- **Surgical Patch**: [Files modified with key changes]
- **Static & Type Checks**: Clean (Python AST compile + TS build passed)
- **Targeted Tests**: [N passed / 0 failed]
- **Real Remotion Render**: SUCCESS (Rendered MP4: [path], Duration: [Xs], Size: [Y MB])
- **Render Truth Audit**: VERIFIED (ffprobe confirmed [codec], [resolution], [fps], [audio])
- **Adversarial QA**: PASSED
- **Contract Drift**: ZERO DRIFT
- **Status**: ISSUE FULLY RESOLVED & VERIFIED
```

## Stop Conditions
Stop only when all 9 validation gates pass without a single warning or regression.
