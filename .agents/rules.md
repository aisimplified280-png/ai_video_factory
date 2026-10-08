# Agent Video Engine Rules (Autonomous Video Factory v2 - Phase 18)
1. First-Class Mascot Bot System: Purposeful mascot presence (`ai_simplified_bot` with `CharacterSpec`) integrated into scenes to point to active nodes, monitor telemetry, or interact with technical components. No photorealistic face-cams or generic human stock avatars.
2. Layout standard: 9:16 vertical (1080x1920), top 75% safe-zone for diagrams (y <= 1400), bottom 25% reserved for captions and CTA.
3. Color & Styling: Strict adherence to active style systems (`claude_editorial` with royal blue `#1A5CFF` accent or registered `stripe_motion`), dark/light theme tokens; never hardcode legacy magenta `#E03188`.
4. Multi-Layer Spatial Depth: Strict 4-layer depth architecture (`bg` z=0, `mid` z=10, `char` z=15, `fg` z=20) with non-trivial occupancy and independent parallax displacement. Primary composite is for debug/preview exports only, never rendered simultaneously on the live depth timeline.
5. Zero Boilerplate Templating: Scene IDs must never hardcode visual geometry. Layouts derive dynamically from `subject`, `visual_purpose`, `visual_metaphor`, and `narration` via semantic entity extraction and domain routing, alternating across scene roles (Hero Metric, Flowchart, Comparison Grid, Terminal/Code, Branded Outro).
6. Domain Separation: Physical robotics hardware visuals (kinematic cells, titanium grippers) are strictly segregated from software, AI, and cloud architectures.
7. Transformative Transitions: All scene-boundary transitions must be transformative (`zoom_transition`, `directional_wipe`, `object_transition`, `shape_morph`, `motion_blur`, `match_cut`) with non-zero overlap.
8. Evidence-Based QA: Never trust declared metadata; QA must probe the encoded MP4 container, actual frames, audio stream, and pixel activity. No fake 9.5 default passes.

