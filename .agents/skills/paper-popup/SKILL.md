---
name: paper-popup
description: "Create tactile cut-paper objects, hinged set pieces and layered paper transitions with shadows and folds. Use selectively for metaphors, object reveals and transitions—not as a default full-video template."
---

# Paper Pop-up — Selective Layered Paper Depth

> Source inspiration: Lemo-Opuscar paper-popup — https://github.com/lemomo-ai/lemo-opuscar/blob/main/styles/paper-popup/STYLE.md

## Use this skill when
- A concept benefits from a tactile object metaphor or layered miniature stage.
- A fold, page turn, tab or pop-up can become a meaningful transition.
- The visual needs depth without a heavy 3D scene.

## Directing and implementation rules
- Build depth from flat layers with clear front-to-back ordering, edge thickness, soft contact shadows and slight material variation.
- Hinged pieces rotate around a physical fold line. Their path should communicate opening, revealing, connecting or separating.
- Let the object cast a shadow that changes as its elevation or angle changes; keep shadows soft and consistent with one light source.
- Use cut-paper borders and texture only where they help distinguish material layers. A page turn should reveal a new idea, not hide a cut.
- Keep paper as a local technique or scene language; do not force it across the full video.

## Workflow
1. Choose one focal object or metaphor and identify which parts are page, backdrop, hinge and moving layer.
2. Build the layers as SVG groups or DOM elements with explicit transform origins.
3. Animate fold and lift using the hinge as the pivot, then match contact shadow and occlusion to the motion.
4. Use page turns or pop-up reveals only at story beats that need a reveal or transition.
5. Inspect for z-order pops, shadow drift, clipping and paper layers that look like generic cards.

## Do not
- A full 3D or WebGL renderer for a simple paper fold.
- Unmotivated page turns, constant parallax, excessive grain or dozens of floating cut-outs.
- Rounded glossy UI cards being described as paper without visible material cues.
- A paper-book overhaul of the existing ELI5 studio or technical notebook stage.

## Factory integration
- Prefer SVG transforms, CSS perspective and GSAP; no new 3D dependency or high-memory render path.
- Respect the established palette and design system; paper technique does not impose cream backgrounds.
- Keep all object motion deterministic and derived from timeline time.

## Acceptance check
- A viewer can infer which layers are above or below the page.
- Hinges, folds and shadows remain physically coherent through the motion.
- Every pop-up or page turn advances the story.
