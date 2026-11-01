---
name: blueprint
description: "Explain a machine, architecture or technical structure through precise line drawings, callouts and layered construction. Use for system architecture, components, mechanisms and engineering explainers."
---

# Blueprint — Reveal the System in Drafting Order

> Source inspiration: Lemo-Opuscar blueprint — https://github.com/lemomo-ai/lemo-opuscar/blob/main/styles/blueprint/STYLE.md

## Use this skill when
- The subject has a physical or logical structure that benefits from a technical drawing.
- The explanation requires exploded views, layers, dimensions or component relationships.
- The viewer must see how a system is assembled or organized.

## Directing and implementation rules
- Use a consistent drawing grammar: outer contours, internal details, hidden lines, centre lines, leaders and numbered callouts have distinct weights or dash patterns.
- Reveal the design in the order the explanation unfolds. A dimension or callout should appear only when it becomes relevant.
- Use orthographic or simple oblique views where they explain structure. Keep projection changes explicit and consistent.
- Treat the camera as an eye reading the same sheet; pan and zoom to details, then pull back to show the whole system.
- Only show dimensions or specifications supported by a source. Use unscaled callouts for illustrative concepts.

## Workflow
1. Define the object or system boundary and list the few parts the audience needs to understand.
2. Choose one view per explanatory purpose: overall, cutaway, exploded, sequence or detail.
3. Set line hierarchy, drawing order and annotation vocabulary before animation.
4. Animate construction, separation or internal flow in sync with the spoken explanation.
5. Validate all labels and numerical dimensions against the source material.

## Do not
- Fake measurements, fabricated patent marks, arbitrary technical jargon or faux engineering detail.
- A full-screen blueprint texture that does not contribute to the explanation.
- Changing projection mid-shot without a transition that helps the viewer reorient.
- Using the blueprint technique when a real UI walkthrough or data chart is clearer.

## Factory integration
- Implement with SVG strokes, masks, simple shapes and GSAP; avoid full 3D CAD imports unless explicitly required.
- Keep the established style palette and typography; blueprint describes drawing grammar, not mandatory colors.
- Use canonical safe zones and responsive dimensions from the current factory.

## Acceptance check
- Every line and label clarifies a real structural relationship.
- The drawing order matches the explanation and is readable on a phone.
- No unverified dimension or false engineering precision appears.
