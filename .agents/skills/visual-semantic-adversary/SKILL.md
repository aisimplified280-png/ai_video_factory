---
name: visual-semantic-adversary
description: Creates adversarial test cases attacking the visual system to guarantee that QA rejects mismatches, boilerplate reuse, and templated visuals.
---

# visual-semantic-adversary

## Purpose
Adversarially attacks the visual generation and QA systems to ensure that "PowerPoint with different text" and visual-script mismatches are reliably caught and rejected. Verifies that visual QA is not a rubber stamp.

## Trigger Conditions
- Triggered whenever updating visual generation logic, layout algorithms, or QA scoring gates.
- Triggered to validate that new QA checks genuinely fail on bad inputs.
- Triggered on PR or major release verification.

## Exact Inspection Targets
1. **Adversarial Test Suite**: `tests/test_phase17_visual_language.py`, `tests/test_visual_semantic_adversary.py`.
2. **Failure Modes Tested**:
   - Correct narration + completely unrelated visual (e.g., enterprise software audio + robotic gripper arm).
   - Identical visual layout + different topic metadata.
   - Fake depth layers (transparent PNG with tiny decorative pixels < 5% occupancy).
   - Frozen scene motion disguised with varying subtitle text.
   - 5 unrelated topics generating the same background grid geometry.
3. **Visual QA Gate**: `production/phase17/visual_qa.py::evaluate_visual_language`.

## Commands / Tools to Use
- `pytest tests/test_phase17_visual_language.py -v`: Tests adversarial detection.
- Adversarial frame generation testing with artificial static frames.

## Failure Conditions
- Visual QA awards a passing score to a static video where geometry does not move.
- Visual QA fails to detect a robotics visual placed in a cloud software video.
- QA passes a scene where layer occupancy is trivial (< 0.05).
- QA evaluates a video using only metadata rather than inspecting rendered frames.

## Evidence Requirements
- Proof of test failure when feed-in frames are deliberately static or mismatched.
- Proof of test pass only when frames demonstrate real movement and topic alignment.

## Output Format
```markdown
### Visual Semantic Adversary Report
- Test: Static Frames Detection -> PASSED (Correctly Rejected with score < 3.0)
- Test: Robotic Arm on Cloud Software -> PASSED (Domain Mismatch Caught)
- Test: Fake Depth (< 5% occupancy) -> PASSED (Occupancy Gate Triggered)
- QA Rigor Score: ADVERSARIAL PASS
```

## Stop Conditions
If any adversarial test passes when it should have failed, fail the QA system immediately as non-defensive.

## Interaction with Other Skills
- Challenges **render-truth-auditor** and **architecture-contract-guardian**.
- Pairs with **cross-topic-benchmark** to enforce authentic generative diversity.
