---
name: transit-map
description: "Show networks, pipelines and multi-stage systems as a coherent route map with meaningful nodes, connections and branching paths. Use for model pipelines, agent systems, data movement and dependencies."
---

# Transit Map — Explain a Network as a Route

> Source inspiration: Lemo-Opuscar transit-map — https://github.com/lemomo-ai/lemo-opuscar/blob/main/styles/transit-map/STYLE.md

## Use this skill when
- The subject is a network, multi-step pipeline, dependency graph or flow of information.
- The audience needs to understand the order, branching or convergence of a process.
- A single route can lead the viewer through a complex system.

## Directing and implementation rules
- Define nodes, edges, direction and junction semantics. Each line must represent a real dependency, route or deliberately simplified relationship.
- Reveal a connection only as the explanation reaches it. A node or interchange becomes active when the route actually arrives.
- Use a small number of distinct line styles or colors to separate categories. Keep the mapping stable throughout the video.
- Move between local and global scale while preserving the viewer's location on the map.
- Use schematic geometry to simplify shape, not to falsify topology, ordering or direction.

## Workflow
1. Convert the source explanation into a graph with typed nodes and edges.
2. Select the critical path and decide which branches can be omitted without changing the conclusion.
3. Lay out the map for vertical mobile viewing with readable node spacing and clear route direction.
4. Animate the route, active stops and branch outcomes in sync with narration.
5. Check every connection and transition against the real process or cited system description.

## Do not
- Fake geographic routes, arbitrary connections, decorative station names or ambiguous line crossings.
- Showing every node at once when a progressive route would teach more clearly.
- A map that becomes too dense to read on a phone.
- Using a transit map for unrelated categories or a dataset that requires a true chart.

## Factory integration
- Use SVG paths and GSAP; keep the node/edge source data separate from visual styling.
- Prefer 2D schematics over 3D map rendering or external map services.
- Retain the channel palette and label all conceptual simplifications.

## Acceptance check
- Every visible connection has a defined meaning and direction.
- The viewer can follow the primary route without losing context.
- Network topology remains accurate when the map is simplified.
