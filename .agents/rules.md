# Agent Video Engine Rules — Autonomous Video Factory v3

1. Fictional topic-aware mascots are allowed; real people, face-cams, influencer avatars, and identifiable likenesses are forbidden. A mascot must have a semantic role and meaningful action.
2. The active platform profile is authoritative for resolution/aspect ratio/safe zones. Never hardcode 9:16 values when a profile is available.
3. The active registered style system is authoritative for palette, typography, theme, motion, and anti-patterns. Never resurrect legacy magenta or stale card/grid styling.
4. Every scene is semantic-first: subject + action + visual_purpose + visual_metaphor + domain + environment + camera + motion + character_role/action.
5. Scene IDs are identifiers only. Never branch visual geometry on scene_01/02/etc.
6. Domain separation is mandatory: robotics/hardware, software/AI/cloud, biotech, finance, cybersecurity, and other domains must use domain-appropriate worlds and interactions.
7. Every scene owns real bg/mid/fg spatial layers. Depth must be visible through occlusion, scale, perspective, and relative motion; metadata is not evidence.
8. Transformative transitions must have non-zero overlap and executable entrance/exit behavior. No silent hard-cut/fade fallback in an active Phase 17/18 production.
9. Visual QA trusts encoded pixels first. Metadata, asset names, planner text, narration keywords, and declared scores are supporting evidence only.
10. The visual judge must describe what is visibly present before comparing it with the intended narration.
11. Character continuity means visual identity may persist while pose, action, placement, scale, environment, camera relationship, and interaction vary by scene.
12. A scene must communicate the narration without requiring the viewer to read metadata or hidden labels.
13. Technical QA failure, visual semantic failure, or asset-lineage failure blocks release or enters the repair loop.
14. The canonical pipeline/artifact chain is authoritative. Ad-hoc factory paths must not silently bypass stage contracts, validators, or runtime locks.
15. All production fixes require targeted tests plus a real render plus encoded-video QA. Green unit tests alone never prove a visual fix.
16. Never use unsafe process termination. Only terminate processes owned by the current run using tracked PIDs/handles.
