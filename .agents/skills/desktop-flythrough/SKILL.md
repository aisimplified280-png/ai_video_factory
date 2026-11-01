---
name: desktop-flythrough
description: "Stage a multi-step software or process explanation as connected surfaces in one shared environment, with an object or signal guiding the camera between them. Use for workflows, pipelines and multi-tool processes."
---

# Desktop Flythrough — One Connected Workflow World

> Source inspiration: Lemo-Opuscar desktop-flythrough — https://github.com/lemomo-ai/lemo-opuscar/blob/main/styles/desktop-flythrough/STYLE.md

## Use this skill when
- The story crosses several screens, tools, stages or workstations.
- A single moving object can connect steps more clearly than repeated cuts.
- A workflow should feel like one connected journey.

## Directing and implementation rules
- Treat each UI surface or process station as a place in one coherent world. Define how the viewer travels from one station to the next.
- Use a persistent token, document, packet, cursor or artifact as the visual guide. It must physically or graphically travel between stages and retain identity.
- Use layered surfaces, perspective and contact shadows to suggest depth. Prefer CSS transforms and SVG layering over full 3D.
- Give each station one observable action and result. The camera should arrive because the persistent object has moved there.
- Maintain a clear wide view of the workflow so the audience can understand how the local step fits into the whole.

## Workflow
1. Map the workflow as ordered stations with inputs, actions and outputs.
2. Choose one persistent visual object that can travel through each stage without changing its meaning.
3. Build stations as readable HTML/SVG surfaces with measured depth and restrained shadow.
4. Animate travel, camera focus and the station's cause-and-effect response from a single timeline.
5. Review the whole route and each close-up; ensure the camera never arrives before the object's action.

## Do not
- A sequence of unrelated floating cards with no shared space or continuity.
- A continuous camera move that obscures text or becomes movement for movement's sake.
- Full 3D desk scenes, voxel characters or high-cost lighting when 2D depth conveys the same idea.
- Replacing the Technical Notebook's existing 25/75 split-canvas identity with an unrelated scene.

## Factory integration
- Use HTML/CSS/SVG and GSAP within the existing HyperFrames composition pipeline.
- Keep perspective and shadows lightweight for the 8 GB Windows environment and low-memory rendering.
- For technical-notebook-explainer, apply only the needed camera and depth techniques within its established split canvas.

## Acceptance check
- The same focal object can be followed from the first stage to the last.
- Each station visibly receives an input and produces an output.
- Text and UI remain crisp and readable during camera movement.
