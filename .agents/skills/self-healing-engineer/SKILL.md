---
name: self-healing-engineer
description: Autonomous repair loop for the video factory; reproduces failures, patches root causes, and proves the fix with real renders.
---
# Self-Healing Engineer

Operate this loop:

OBSERVE
→ REPO FORENSICS
→ CONTRACT TRACE
→ REPRODUCE
→ ROOT CAUSE
→ MINIMAL PATCH
→ TARGETED TEST
→ FULL TEST
→ REAL RENDER
→ ENCODED MP4 QA
→ VISUAL JUDGE ENSEMBLE
→ ADVERSARIAL QA
→ CROSS-TOPIC BENCHMARK
→ REGRESSION CHECK
→ DOCUMENTATION CONTRACT
→ RE-AUDIT CURRENT MAIN

Never stop at "tests pass".

For every failure record:
- exact symptom
- first failing layer
- root cause
- files changed
- why the patch fixes the root cause
- tests run
- render evidence
- remaining risk

Never:
- weaken or delete a failing test without proving it was invalid
- replace real visual QA with metadata
- silently route around a locked runtime
- kill arbitrary processes
- restore deleted legacy engines simply to make a test pass
- release a failed artifact

Before finalizing, re-fetch the current branch/main state and ensure no concurrent change invalidated the patch.
