---
name: json-to-pydantic
description: Validates structured production JSON without rejecting the new topic-aware mascot system.
---
# JSON / Pydantic Contract Validation

When validating AI-generated production JSON:

- validate against the active schema, not stale examples
- preserve unknown-field detection unless explicitly versioned
- verify scene IDs are identifiers, never visual-template selectors
- validate subject, action, visual_purpose, visual_metaphor, domain, environment, camera, motion, depth, transition, character role/action, and asset references when required
- fictional topic-aware characters are valid; real-person likenesses and face-cams are not
- verify width/height/timing fields against the active platform profile
- reject legacy renderer/runtime values when the active pipeline has retired them
- ensure schema validation does not accidentally strip semantic fields before rendering

Never use historical create_short.py schemas or UI-primitives as the current source of truth.
