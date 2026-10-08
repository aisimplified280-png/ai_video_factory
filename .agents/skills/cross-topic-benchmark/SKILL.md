---
name: cross-topic-benchmark
description: Proves generative visual diversity across distinct topic domains (AI agents, robotics, finance, biotech, quantum), failing on repeated geometry.
---

# cross-topic-benchmark

## Purpose
Proves that the Video Factory is genuinely generative across different domain verticals, preventing repetitive structural templates. Enforces that unrelated topics generate fundamentally different layouts, environments, and motion styles.

## Trigger Conditions
- Triggered before releasing major updates to `production/phase17/` or `remotion-composer/`.
- Triggered whenever evaluating claims of visual variety.
- Triggered on nightly/weekly regression tests.

## Exact Inspection Targets
1. **Diverse Benchmark Domains**:
   - Topic 1: Physical Robotics ("Six-Axis Industrial Robotic Arm")
   - Topic 2: AI Agents / Software ("Multi-Agent Orchestration with MCP")
   - Topic 3: Cloud / Databases ("Distributed Vector Database Sharding")
   - Topic 4: Biotechnology / Genetics ("CRISPR Sequence Alignment Algorithms")
   - Topic 5: Financial Systems ("High-Frequency Trading Matching Engines")
2. **Generators**: `production/phase17/environment_generator.py`, `production/phase17/multi_layer_generator.py`.
3. **Metric Evaluators**: Cross-topic histogram divergence, layout archetype distribution, primitive usage diversity.

## Commands / Tools to Use
- `pytest tests/test_phase17_visual_language.py -k "test_topic_aligned_environment_generation_5_unrelated_topics" -v`
- `pytest tests/test_phase17_visual_language.py -k "test_structural_difference_between_unrelated_topics" -v`

## Failure Conditions
- Any pair of unrelated topics produces background environments with cross-correlation > 0.85.
- The visual generator assigns the same archetype (e.g. 3-card pipeline) across all 5 benchmark domains.
- Robotics hardware visuals (e.g. titanium gripper) appear in a software or biotech topic.

## Evidence Requirements
- Structural difference matrix showing inter-topic image distance > 0.15 across all pairs.
- Archetype breakdown verifying distinct layout geometries per domain.

## Output Format
```markdown
### Cross-Topic Benchmark Evaluation
- Benchmark Topics Tested: 5
  1. Robotics: KINEMATIC_CELL (Physical gripper, calibration telemetry)
  2. AI Agents: NODE_HUB (Distributed cluster lattice)
  3. Cloud Database: MULTI_STAGE_PIPELINE (Conduit throughput cards)
  4. Biotech: SEQUENTIAL_ALIGNMENT (Nucleotide matrix)
  5. FinTech: VELOCITY_METRIC (Latency benchmark card)
- Inter-Topic Structural Divergence: 0.34 (Threshold >= 0.15) -> PASS
- Visual Repetition Check: ZERO BOILERPLATE DETECTED
```

## Stop Conditions
If any two unrelated topics produce near-identical visual compositions, fail the benchmark and demand archetype diversification.

## Interaction with Other Skills
- Informs **architecture-contract-guardian** on domain categorization rules.
- Validated by **visual-semantic-adversary**.
