# Phase 18 Upgrade Backlog

## P0

1. Fix missing os import in composition/remotion/props_builder.py.
2. Make phase17 synchronization additive and contract-safe; never overwrite richer scene_plan data.
3. Make Phase 17 generated bg/mid/fg assets canonical manifest entries and wire them into props/render.
4. Apply N-1 transformative transitions to edit_decisions and Remotion; remove hard_cut/fade fallbacks from the active path.
5. Replace ActionLayer and BackgroundLayer scene-ID mega-templates with semantic composition resolvers.
6. Remove the global isAITopic renderer switch; pass scene-level domain and semantic context.
7. Replace Phase 15/16 metadata/keyword grounding with independent encoded-frame semantic visual judgment.
8. Make technical + visual QA blocking before release, with an explicit repair loop.
9. Introduce a topic-aware fictional mascot contract end-to-end and render meaningful mascot interactions.

## P1

10. Use ArtifactStore versioning for render_report.
11. Detect audio streams by codec_type=audio.
12. Reconcile ffmpeg_pil references in active schemas/pipelines.
13. Remove legacy transition defaults in stage planners.
14. Replace scene-index environment selection with semantic novelty routing.
15. Expand visual regression tests to cover actual MP4 pixels.
16. Add cross-topic structural diversity benchmarks.
17. Add adversarial visual tests designed to fool metadata-driven QA.
18. Reconcile README/docs with the current Remotion-first architecture.
19. Run regression bisecting against the known visual-template failure commits.

## Acceptance gates

A Phase 18 production is releasable only when:
- no P0 remains
- technical QA passes
- semantic visual QA passes
- no severe structural repetition is detected
- meaningful motion is present
- depth is visually demonstrated
- all N-1 transitions execute
- mascot interactions are topic-grounded
- artifact lineage is coherent
- final release MP4 is exactly the passing encoded artifact
