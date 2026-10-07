---
name: json-to-pydantic
description: Validates storyboard JSON schema strictly before code executes.
---
# Instructions
When checking JSON output from the AI models:
- Verify that the output strictly adheres to the UI primitives specified in the Agent Video Engine Rules (e.g. `mac_window`, `decision_card`, `comparison_grid`).
- Check that no legacy types (e.g. `avatar`, `character`) exist.
- Ensure that `width`, `height`, and `enter_start` fields are correctly typed as `float` matching the schema before the procedural engine crashes.
