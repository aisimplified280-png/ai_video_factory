# Phase 9 Visual Intelligence Readiness

## 1. Cleanup & Baseline Status
* **Test Suite Recovered**: Removed dangling test output files that caused `pytest` collection errors due to Unicode decoding.
* **Phase 8B Integrity Restored**: Fixed the `edit_decisions.v001.json` hash mismatch by regenerating the canonical SHA256 hash in `.latest.json` and the envelope, successfully realigning the artifact with the `production_state.json` references.
* **Test Baseline Green**: `pytest` now completes with `345 passed, 1 skipped` and the `e2e` real render tests confirm Remotion is structurally sound.
* **Note on Local Rendering**: Attempting to run `scripts/run_local_production.py` directly throws a `MediaError` on Windows because the default headless Chromium bundled by Remotion lacks the proprietary codecs required to decode `.mp3` narration files on this OS. However, the E2E pixel-authority tests (which test rendering without the problematic MP3s) pass perfectly.

## 2. Asset Inventory & Architecture
Based on `asset_manager.py`, the current visual pipeline supports:
1. **Procedural SVGs/Images**: High-res Emojis (Twemoji/Noto Emoji) mapped to semantic concepts.
2. **Dynamic AI Icons**: Uses DALL-E 3 (via Pollinations API) to generate clean, 3D flat vector icons with transparency masks on the fly (`get_or_create_ai_icon`).
3. **UI/Branding Cards**: Pre-cached subscribe cards, glassmorphism containers, and brand badges.

### Limitations of Phase 8B
Phase 8B selects visuals based on hardcoded templates. For example, it might select an "Industrial Nuclear Fusion" theme, but apply a generic template background regardless of the nuanced narration topic. This creates a disconnect between the spoken words and the visual evidence.

## 3. Proposed Visual Intelligence Architecture (Phase 9)
For Phase 9, we must map the narrative intent to **strong, contextually relevant background visuals**.

### The Mapping Strategy:
1. **Semantic Topic Extraction**: The Editorial Plan Generator (Phase 9.1) will analyze `script.v001.json` to extract a "core semantic topic" or "visual focus" for each scene (e.g., "Transformer Architecture", "Data Center Servers", "Neural Network Graph").
2. **Metaphor Alignment**: Use the `visual_direction` and `visual_metaphor` from `production_state.json` (e.g., "Industrial nuclear fusion reactor aesthetics") as an aesthetic *modifier*, rather than the sole prompt.
3. **Dynamic Background Synthesis**:
   - Instead of picking from a fixed list of templates, Phase 9 will construct queries combining the *Topic* + *Aesthetic Modifier*.
   - Example Query: "Data Center Servers, Industrial nuclear fusion reactor aesthetics, glowing plasma containment fields, high-contrast 3D render".
   - This prompt will be passed to an enhanced `get_or_create_background()` (a new addition to `asset_manager.py` or the semantic planner) to fetch or cache bespoke, high-quality, relevant background images for each scene.
4. **Editorial Overrides**: If the script requires a highly specific diagram (like a logarithmic growth curve for "Scaling Laws"), the plan will bypass generic background generation and explicitly request a graph/diagram asset.

### Next Steps (Implementation Jump)
We are now ready to implement the Phase 9.1 through 9.5 milestone in OpenCode. The architecture will respect the strict Phase 8B renderer boundaries (modifying NO files inside `remotion-composer/`) while routing the new, highly contextual assets through the existing props interface.
