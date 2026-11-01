---
name: circuit-board
description: "Represent a real system as meaningful traces, nodes and components, with a moving signal that reveals how data, power or control passes through it. Use for chips, networks, AI infrastructure and system internals."
---

# Circuit Board — Show the Signal Moving

> Source inspiration: Lemo-Opuscar circuit-board — https://github.com/lemomo-ai/lemo-opuscar/blob/main/styles/circuit-board/STYLE.md

## Use this skill when
- The explanation is about connected components, routing, data flow or hardware.
- A signal path is the clearest way to show the system's operation.
- The story moves between system-level architecture and component-level detail.

## Directing and implementation rules
- Define what each node, connection and signal represents before drawing it. Every trace must correspond to a real relationship or an explicitly labelled abstraction.
- Use simple orthogonal or 45-degree routes with clear junctions and component pads. A path's geometry should help the viewer understand direction and dependency.
- The signal reveal is the action: light runs along a trace, reaches a node and triggers a visible response.
- Move between system and component scale using one camera transform. Keep line weight and label size readable across zoom levels.
- Differentiate physical hardware, logical data flow and conceptual metaphor in the labels; do not depict an abstract model as a literal PCB.

## Workflow
1. Extract components and relationships from the verified technical source or architecture description.
2. Create a node-and-edge map and label the semantic meaning of every important edge.
3. Draw only the relevant board region; reveal a signal route and show downstream effects as the signal arrives.
4. Add focused callouts for the component that matters, then return to the full system.
5. Check that the animation order matches the actual flow or dependency order.

## Do not
- Decorative traces, random blinking LEDs, arbitrary chip labels or circuit-city scenery.
- Calling a conceptual diagram a real chip layout, PCB or hardware photograph.
- Excessive glow, tiny labels or a camera move that turns the board into visual noise.
- Showing parallel branches as sequential when the underlying system works concurrently.

## Factory integration
- Use SVG paths, circles and GSAP for efficient 2D animation; use no shader or 3D pipeline by default.
- Keep a machine-readable node/edge model where possible so diagrams can be linted and checked.
- Preserve the purple collage palette when this is a technique inside the channel's established look.

## Acceptance check
- Every highlighted path has a defensible technical meaning and correct direction.
- Arrival at a node creates an understandable response or state change.
- A viewer can trace the important route at both overview and close-up scales.
