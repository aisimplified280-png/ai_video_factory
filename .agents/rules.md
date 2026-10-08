# Agent Video Engine Rules (Autonomous Video Factory v2)
1. Never import or introduce character models, avatars, or face-cams.
2. Layout standard: 9:16 vertical (1080x1920), top 75% safe-zone for diagrams (y <= 1400), bottom 25% reserved for captions and CTA.
3. Color & Styling: Strict adherence to active style systems (`claude_editorial` with royal blue `#1A5CFF` accent or registered `stripe_motion`), dark/light theme tokens; never hardcode legacy magenta `#E03188`.
4. Multi-Layer Spatial Depth: Strict 3-layer architecture (`bg`, `mid`, `fg`) with non-trivial occupancy (mid >= 0.08, fg >= 0.05) and 3D parallax displacement.
5. Zero Boilerplate Templating: Scene IDs must never hardcode visual geometry. Layouts derive dynamically from `subject`, `visual_purpose`, `visual_metaphor`, and `narration` via semantic entity extraction and domain routing.
6. Domain Separation: Physical robotics hardware visuals (kinematic cells, titanium grippers) are strictly segregated from software, AI, and cloud architectures.
7. Transformative Transitions: All transitions (including `match_cut`) must specify non-zero overlap and distinctive entrance/exit dynamics.
8. Evidence-Based QA: Never trust declared metadata; QA must probe the encoded MP4 container, actual frames, audio stream, and pixel activity.

