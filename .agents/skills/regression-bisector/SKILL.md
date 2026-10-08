---
name: regression-bisector
description: Identifies the first commit that introduced a production regression instead of patching symptoms blindly.
---
# Regression Bisector

When a failure appears after a change:
- identify the first known-good commit
- compare it with the first known-bad commit
- isolate changed files and behavioral contracts
- reproduce the regression on the smallest real fixture
- fix the root cause rather than reverting unrelated improvements

For visual regressions compare actual frame evidence, not only metadata diffs.

Record commit SHA, changed files, symptom, reproduction command, first bad revision, root cause, and verification evidence.
