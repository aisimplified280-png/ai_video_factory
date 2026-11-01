---
name: data-visualization
description: "Turn verified datasets and statistics into accurate animated charts, comparisons and data transformations. Use for AI market figures, benchmarks, adoption, costs, performance and trend stories."
---

# Data Visualization — Let the Numbers Tell the Story

> Source inspiration: Lemo-Opuscar dataviz — https://github.com/lemomo-ai/lemo-opuscar/blob/main/styles/dataviz/STYLE.md

## Use this skill when
- A video makes a quantitative claim or compares measured values.
- A trend, distribution, ranking, relationship or flow is central to the story.
- A chart can reveal a surprising change more clearly than text.

## Directing and implementation rules
- Start from a source-backed dataset. Store values, units, time periods, source URL and relevant caveats alongside the visual data.
- Choose the encoding that matches the question: bars for categories, lines for time, scatter for relationships, histograms for distributions, slope/dumbbell for before-and-after, Sankey for flow and maps only for geographic data.
- Do not change values to improve composition. Axis ranges, baselines, category order and missing data must be explicit and truthful.
- Build the chart incrementally so each new mark answers the current narration beat. Use transformations only when the same data remains traceable before and after.
- Use annotations to explain important points, not to add unsupported causal claims. Every numeric highlight must resolve to a dataset record.

## Workflow
1. Collect and normalize the dataset; verify dates, units, source and whether values are estimates, forecasts or reported results.
2. Write the single question the chart must answer, then select the simplest suitable chart type.
3. Create a static correctness frame and validate labels, scale, units, legend and source note before animating.
4. Animate marks, axes and callouts on the narrative timeline; use a consistent semantic palette.
5. Check every displayed value against the source data after rendering.

## Do not
- Invented metrics, unsupported percentages, cropped axes that exaggerate differences or missing unit labels.
- A dashboard full of charts when one carefully staged chart answers the story.
- Animating a number in a way that makes it appear more precise than the underlying source.
- Decorative sonification or visual flourishes that imply a data relationship that does not exist.

## Factory integration
- Use native SVG/Canvas and GSAP; no external chart service, paid API or heavy notebook runtime.
- Preserve exact values in structured data rather than hard-coding rounded labels in the composition.
- When the source is uncertain or not independently checked, mark the claim for editorial review rather than treating it as verified.

## Acceptance check
- Every visible number, unit, date and comparison is traceable to the supplied data.
- The chart remains understandable at phone size and in a paused frame.
- No axis, scale or annotation changes the apparent meaning of the data.
