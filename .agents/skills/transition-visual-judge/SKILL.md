---
name: transition-visual-judge
description: Verifies that every scene boundary visibly executes the intended transformative transition.
---
# Transition Visual Judge

For N scenes require exactly N-1 meaningful scene-boundary transitions.

For every boundary:
- identify outgoing final frames
- identify incoming first frames
- inspect overlap window
- verify specified transition semantics from actual pixels
- verify incoming/outgoing focal relationship
- verify no accidental hard cut or plain fade
- verify transition duration is non-zero

A transition counts only when the viewer can see it.

Examples:
- match_cut must visibly align/morph a focal subject or geometry
- object_transition must transfer a visible object/focal anchor
- shape_morph must visibly transform a shape
- zoom_transition must visibly push through scale
- motion_blur must visibly move through the boundary
- directional_wipe must visibly sweep the frame

Reject metadata-only transition claims.
