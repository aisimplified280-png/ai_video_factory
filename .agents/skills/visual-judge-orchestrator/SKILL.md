---
name: visual-judge-orchestrator
description: Combines independent visual judges into a blocking release verdict using actual encoded pixels.
---
# Visual Judge Orchestrator

Run the visual judge ensemble over the encoded MP4:

1. frame-by-frame visual critic
2. semantic grounding
3. diversity detector
4. temporal motion judge
5. depth/parallax judge
6. transition judge
7. composition quality
8. cinematic quality
9. caption sync
10. continuity
11. character visual audit
12. blind adversary

Rules:
- visual observation precedes expectation comparison
- no metadata can override pixel evidence
- one P0 visual failure blocks release
- repeated structural templates are release-blocking
- missing major narrated subjects are release-blocking
- fake depth or fake transitions are release-blocking

Persist:
- frame/timestamp evidence
- observations
- scores
- failure severity
- root-cause hypothesis
- recommended repair

Return one machine-readable verdict:

PASS only when all blocking gates pass.
