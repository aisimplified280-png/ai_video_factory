---
name: typescript-remotion-auditor
description: Audits the Remotion React TypeScript bundle, enforcing prop contract parity, sequence timing, audio loading, and zero compile errors.
---

# typescript-remotion-auditor

## Purpose
Validates the Remotion composition pipeline: TypeScript type-checking, React component lifecycles, Remotion sequence frame timing, audio playback resolution, and transition overlap contracts.

## Trigger Conditions
- Triggered whenever modifying any file in `remotion-composer/`.
- Triggered whenever changing props generation in `composition/remotion/props_builder.py`.
- Triggered whenever rendering fails inside Node / Chromium (`npx remotion render`).

## Exact Inspection Targets
1. **Remotion Composition**: `remotion-composer/src/compositions/SceneComposition.tsx`, `Root.tsx`.
2. **Primitives**: `ActionLayer.tsx`, `BackgroundLayer.tsx`, `DiagramLayer.tsx`, `MetricLayer.tsx`.
3. **Props Schema**: `remotion-composer/src/runtime/props.ts` vs `composition/remotion/props_builder.py`.
4. **Media & Audio Resolution**: `remotion-composer/src/runtime/loader.ts`, `staticFile()` vs HTTP URLs.
5. **Transitions & Overlaps**: Overlap frames, match cut, zoom, fade transitions.

## Commands / Tools to Use
- `npm run --prefix remotion-composer build`: Type-checks all TSX files and builds the production bundle.
- `npx remotion compositions remotion-composer/src/index.ts`: Inspects registered compositions.
- Real render invocation via `pytest tests/e2e/test_remotion_real_render.py -v`.

## Failure Conditions
- `tsc` or `npm build` emits any type error or unresolved module import.
- Remotion props schema in TypeScript disagrees with `props_builder.py` output.
- `<Audio />` or `<Img />` references an unreachable URL or missing file without fallback.
- Overlapping transitions cause visual black frames or undefined layout states.

## Evidence Requirements
- Successful build log from `npm run --prefix remotion-composer build`.
- Zero type errors reported by TypeScript compiler.
- Successful execution of an end-to-end real Remotion render producing a playable MP4.

## Output Format
```markdown
### TypeScript / Remotion Audit Report
- TS Compilation: PASS | FAIL
- Props Parity: In Sync | Diverged
- Audio Source Resolution: Verified (HTTP + staticFile fallback)
- Transition Timing: Valid (All overlaps non-zero)
- Real Render Verification: PASS | FAIL
```

## Stop Conditions
Halt immediately if TypeScript compilation fails or if Remotion throws an unhandled React runtime error.

## Interaction with Other Skills
- Works in tandem with **architecture-contract-guardian** to ensure props match React component inputs.
- Validated downstream by **render-truth-auditor**.
