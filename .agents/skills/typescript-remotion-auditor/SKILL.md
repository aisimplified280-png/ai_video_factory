---
name: typescript-remotion-auditor
description: Audits the complete Remotion renderer for prop parity, timeline math, asset routing, animation, transitions, and pixel correctness.
---
# TypeScript Remotion Auditor

Audit every TS/TSX/MJS file in remotion-composer.

Check:
- props.py ↔ runtime/props.ts parity
- scene/event field consumption
- scene-ID branches
- global flags that override scene semantics
- hardcoded geometry
- hardcoded dimensions where profile data exists
- camera functions actually used
- motion functions actually used
- transition overlap math
- Sequence timing
- audio source handling
- staticFile/HTTP path correctness
- asset URL resolution
- background/action layer ownership
- CTA/caption layering
- render script arguments
- TypeScript compiler errors

Critical rule:
A planner field that is never consumed by the renderer is a broken contract even if tests pass.
