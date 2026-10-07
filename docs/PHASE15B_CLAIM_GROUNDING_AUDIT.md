# Phase 15B: Claim-Grounded Visual Relevance Audit

**Target Production Run:** `GPT-6 Astra controls robots` (`proj_3e27bd7a`)  
**Audited Artifacts:** `script.v007.json`, `projects/proj_3e27bd7a/edit/plan.v001.json`, `edit_decisions.v007.json`, `contact_sheet.png`, `video.mp4`.

---

## Executive Summary of Failure

While Phase 15 successfully solved **visual diversity** (achieving 10.0/10.0 diversity with distinct color palettes, angles, and camera styles across 5 scenes), it revealed a critical defect: **the scenes were visually diverse but failed semantic visual relevance to the spoken claims.**

The root cause:
1. `semantic_analyzer.py` mapped narrative sections to visual modes using keywords and defaulted to generic visual metaphors (e.g., mapping `"control"` + `"neural"` $\to$ abstract cyan data streams in a black void).
2. `shot_director.py` relied on static mode presets (`DIRECTORIAL_PALETTES`) rather than constructing scenes from the factual claims, entities, and actions extracted from the script and research pack.
3. No intermediate **ClaimVisualPlan** existed to define required visual evidence, entity constraints, or unacceptable visuals.
4. The QA gate evaluated RGB histogram diversity and keyword overlap, but never audited whether the visual literally demonstrated the claim being spoken.

---

## Scene-by-Scene Audit

### Scene 01 (Hook)
- **Narration:** *"Warehouse robots are getting smarter fast."*
- **Exact Factual Claim:** Physical warehouse robotic machines are rapidly gaining intelligence and speed.
- **Currently Shown:** Extreme macro close-up of high-speed mechanical gripper clamping onto a component with zero play.
- **Direct Demonstration?** Partially illustrative of robotic speed/precision, but misses the warehouse context and intelligence leap.
- **Is it a Generic Metaphor?** It is a generic industrial macro shot that could belong to any factory video.
- **Could it belong to 100 other AI stories?** Yes (any video mentioning hardware, robotics, or sensors).
- **What a Viewer Needs to See:** High-speed warehouse robot mechanism executing a complex, intelligent pick-and-sort task with telemetry indicating rapid decision-making.

### Scene 02 (Lead Story / Reveal) — CRITICAL FAILURE
- **Narration:** *"Advanced neural networks can now directly control physical robots with real-time sensor feedback."*
- **Exact Factual Claim:** An AI model/neural network directly issues low-level motor commands to physical robots and receives real-time sensory feedback.
- **Currently Shown:** Abstract visualization of glowing electric synaptic data streams bridging from AI network into robotic motor bus (cyan lines and glowing tensor nodes in a dark void).
- **Direct Demonstration?** **NO. Complete failure of relevance.** The robot itself is absent. The physical control action is absent. Sensor feedback is invisible. It is a 100% abstract metaphor.
- **Is it a Generic Metaphor?** Yes. Pure generic AI "synapse / data stream" sci-fi visual.
- **Could it belong to 100 other AI stories?** Yes. It could be used for LLM inference, autonomous driving, drug discovery, or crypto.
- **What a Viewer Needs to See:** A direct split/composite or close-up showing the AI neural control interface (model output tokens / motor bus telemetry) actively driving a multi-axis physical robotic arm with sensor feedback lines looping back into the system.

### Scene 03 (Escalation / Mechanism) — CRITICAL FAILURE
- **Narration:** *"Instead of rigid pre-programmed routines, these machines adapt dynamically to moving obstacles and inventory shifts."*
- **Exact Factual Claim:** Autonomous machines dynamically detect unforeseen moving obstacles/inventory shifts and adapt their trajectory in real time instead of freezing or following static paths.
- **Currently Shown:** Overhead tracking shot of 4 autonomous logistics rovers driving across a warehouse floor grid.
- **Direct Demonstration?** **NO.** It shows rovers driving, but **there is NO obstacle**, NO detection cone, and NO adapted trajectory! It shows normal pre-programmed movement, not dynamic adaptation!
- **Is it a Generic Metaphor?** It is a generic warehouse floor visual.
- **Could it belong to 100 other AI stories?** Yes. Any story mentioning logistics or Amazon Kiva robots.
- **What a Viewer Needs to See:** An autonomous machine encountering an unexpected obstacle in its path, an active sensor cone detecting the obstruction, and a visible dynamic vector path recalculation curving around the obstacle in real time.

### Scene 04 (Implication / Scale)
- **Narration:** *"That means facilities can move inventory faster, with fewer delays and less human intervention."*
- **Exact Factual Claim:** Industrial automation delivers accelerated inventory throughput, drastic reduction in logistical delays, and elimination of manual bottlenecks.
- **Currently Shown:** Vast multi-tier distribution mega-facility with high-bay shelving and amber warning beacons.
- **Direct Demonstration?** Partially illustrative of a large facility, but fails to visualize *faster* movement, *fewer delays*, or *bottleneck reduction*. It is a static architectural view.
- **Is it a Generic Metaphor?** Generic distribution warehouse backdrop.
- **Could it belong to 100 other AI stories?** Yes.
- **What a Viewer Needs to See:** Visual evidence of speed and throughput contrast: high-speed multi-lane inventory flow with green throughput velocity readouts and bottleneck reduction indicators.

### Scene 05 (CTA)
- **Narration:** *"And this is just the beginning. Subscribe to AI Simplified Lab for daily frontier AI briefings."*
- **Exact Factual Claim:** Channel branding callout and invitation to subscribe.
- **Currently Shown:** Clean minimalist dark obsidian architectural studio with polished floor and glowing channel badge.
- **Direct Demonstration?** Yes. Clean branded studio environment matches narrative CTA requirements without clutter.

---

## Architectural Corrective Action Plan (Phase 15B)

1. **Claim Extraction & Evidence Planning:**
   Implement `ClaimVisualPlan` with explicit extraction of `entities`, `action`, `object`, `environment`, `relationship`, `required_visual_evidence`, and `unacceptable_visuals`.
2. **Mandatory Evidence Thresholds:**
   Require all core scenes to attain `grounding_level >= 3.0` (Level 3: strong illustrative or Level 4: direct evidence) and `claim_coverage >= 80%`.
3. **Preserve Entities & Actions:**
   Forbid replacing named entities (e.g. GPT-6 Astra, industrial robotic arm) with generic sci-fi tropes (abstract brain, server room).
4. **Directorial Candidate Scoring:**
   Grounding score (35%) and claim coverage (25%) must dominate over diversity (10%).
5. **Semantic Asset Rendering:**
   Upgrade procedural rendering so capability, adaptation, and throughput scenes literally depict the required entities, control loops, obstacle detection, and flow acceleration.
6. **Frame-Level Claim QA:**
   Audit every frame for required evidence, entity matching, and contradiction detection, rendering detailed claim annotations on `contact_sheet.png`.
