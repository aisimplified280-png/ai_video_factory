---
name: regression-bisector
description: Diagnoses and bisects historical commits when a regression appears, establishing the exact commit, cause, and minimal reproduction.
---

# regression-bisector

## Purpose
Prevents blind patching of HEAD when a regression appears. Traces backward through git history to identify the exact commit that introduced the bug, inspects the delta, and creates a minimal reproduction test.

## Trigger Conditions
- Triggered whenever a previously passing test fails or a previously working feature breaks.
- Triggered when diagnosing unexpected behavior after a sequence of rapid commits.

## Exact Inspection Targets
1. **Git Commit History**: `git log -n 10 --oneline`, `git diff HEAD~1`.
2. **Specific File Evolution**: `git log -p -n 5 <path/to/file>`.
3. **Blame Tracking**: `git blame -L <start>,<end> <path/to/file>`.

## Commands / Tools to Use
- `git log --graph --oneline -n 15`
- `git diff <commit>^..<commit> -- <file>`
- `git bisect start`, `git bisect bad`, `git bisect good`

## Failure Conditions
- A patch is applied to HEAD without identifying which commit introduced the regression and why.
- A bug fix is declared without adding a regression test preventing its return.

## Evidence Requirements
- Identified commit hash and commit message of the regression point.
- Precise diff explanation showing the introduced flaw.
- Minimal isolated reproduction test reproducing the exact failure.

## Output Format
```markdown
### Regression Bisector Analysis
- Defect: [Description of bug]
- Regressing Commit: [commit hash] - [commit subject]
- Cause: [Explanation of bad diff line]
- Files Affected: [List of files]
- Minimal Reproduction Test: [Path to added test]
- Remediation Plan: [Precise surgical fix]
```

## Stop Conditions
Halt and document findings before applying fixes to ensure the root cause is understood.

## Interaction with Other Skills
- Directly consumed by **self-healing-engineer** to structure the fix.
- Pairs with **python-static-auditor** and **typescript-remotion-auditor**.
