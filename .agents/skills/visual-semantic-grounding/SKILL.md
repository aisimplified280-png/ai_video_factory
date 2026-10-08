---
name: visual-semantic-grounding
description: Independently judges whether the actual pixels communicate the intended narration and scene subject/action.
---
# Visual Semantic Grounding

For every scene:

1. Inspect actual rendered frames first.
2. Write an independent visual observation without reading the expected answer.
3. Identify visible subjects, actions, environment, relationships, and focal point.
4. Only then compare the observation with the intended narration and scene contract.

Example failure:
Expected: industrial robot moving a pallet.
Observed: generic blue neural network with glowing nodes.
Result: FAIL regardless of matching metadata.

Score separately:
- subject visibility
- action visibility
- environment/domain correctness
- relationship correctness
- narrative relevance
- misleading/contradictory content

Do not convert narration keywords into visual evidence.

A scene may be acceptable as an intentional metaphor, but the metaphor must be explicit in the scene contract and visually understandable.

Store evidence as frame path + timestamp + observation + expected semantics + score.
