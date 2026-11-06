---
name: composition-builder
description: "Implement 100% offline HTML5, CSS and GSAP 9:16 compositions for HyperFrames with the AI Simplified Lab Purple Collage Explainer aesthetic, kinetic active captions, and safe-zone enforcement."
---

# Composition Builder (AI Simplified Lab Purple Collage Explainer)

Build high-performance, deterministic 9:16 portrait video compositions using HyperFrames and GSAP.

## Aesthetic Identity (AI Simplified Lab Purple Collage)

- **Canvas Background**: Deep atmospheric ink purple (`#0b0518` to `#241147`) with a tactile halftone dot-matrix pattern (`radial-gradient(rgba(192, 132, 252, 0.13) 1.5px, transparent 1.5px)` on 26px grid).
- **Accents**: High-contrast electric chartreuse (`#a3e635`), vibrant lavender (`#c084fc`, `#e9d5ff`), and crisp white (`#ffffff`).
- **Typography**: Bold, oversized sans-serif with high contrast for mobile viewing.
- **Layering & Depth**: Editorial collage staging, subtle glassmorphic backdrops, glowing borders (`rgba(192, 132, 252, 0.35)`), and soft layered drop shadows (`0 24px 60px rgba(0, 0, 0, 0.55)`).
- **Kinetic Subtitles**: Bottom safe-zone pill (`background: rgba(14, 7, 28, 0.88)`), slate body words, with current spoken word active highlight in glowing neon chartreuse (`#a3e635` on `rgba(163, 230, 53, 0.18)`).

## Composition Capabilities (Beyond Uniform Cards)

1. **Full-Frame Visual Hooks**: Oversized bold titles, pulsating neon badge, and surreal dimensional collage icon.
2. **Prominent Architecture Frames**: Large illuminated glass container for verified SVG diagrams, with high-visibility caption strip and license tag.
3. **Physical Metaphor Stages**: Concrete hardware and data-flow physical representations (e.g. multi-layer graph highway, pinned RAM conveyor belt, memory vaults).
4. **Editorial Syntax Terminals**: Sleek dark code editor with purple/lavender chrome and active line highlighting.
5. **Asymmetric Comparisons**: Split visual blocks contrasting legacy friction against structured optimization.

## Safe Zone Constraints (1080x1920)

- Top Margins: Y=0 to Y=240px contains top track and channel brand (`AI SIMPLIFIED LAB`).
- Stage Area: Bound between Y=250px and Y=1420px.
- Bottom Safe Zone: Y=1440px to Y=1620px houses the kinetic subtitle pill, safely above YouTube Shorts title/description and right-side action buttons.

## Offline Vendoring & Zero-CDN Rule

- Never import scripts or fonts from unverified CDNs (`unpkg`, `cdnjs`, `jsdelivr`).
- Local `pipeline/vendor/gsap.min.js` is copied directly to `./assets/vendor/gsap.min.js`.
- Escape all dynamic text inputs (`escapeHtml`) before inserting into DOM templates.

## Observable Completion Criteria

- `index.html` contains zero remote script or stylesheet URLs.
- Composition passes `hyperframes lint` without errors.
- All visual elements and text stay strictly within 1080x1920 safe-zone coordinates.


## Stage 1C — No Template / No Slide Rule (mandatory for new projects)

This tool is a motion-scene renderer, not a PowerPoint generator. The old `cardType` branches remain only to reproduce legacy projects. New projects must use `productionMode: "dynamic"` and a scene-specific `sceneDirection` as defined in `docs/DYNAMIC_SCENE_ENGINE_SPEC.md`.

Build a unique visual stage per scene from its own geometry, focal object, depth layers, camera path, and action sequence. A scene cannot be only a title, badge, paragraph, rounded rectangle or image placed on a static background. Every scene needs a visible event with object-level motion or an explicitly motivated stillness beat, and every visual asset must have a stated narrative role.

Never reuse a composition as a template with changed copy. Use continuity only when the same subject genuinely carries across a transition. Motion, transitions, captions and SFX must be timed to the spoken narration; do not apply decorative effects by default.

Before render, validate:
- unique scene composition signature;
- visual event setup/action/payoff;
- focal subject and purposeful elements;
- object-level motion and cause/effect;
- meaningful camera move;
- voice/caption synchronization;
- scene-specific sound design or documented deliberate silence;
- aspect-safe placement.

Do not silently fall back to a card layout when dynamic direction is missing. Stop and report the incomplete scene direction.
