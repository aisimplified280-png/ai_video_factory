# Phase 6 — Editorial Edit Decisions

Phase 6 is the authoritative editorial layer. It makes a renderer-neutral decision about
when each planned visual appears, in what semantic layer, with which framing, transition,
camera intent, motion intent, caption reference, and audio reference. It does not render.

## Contract

`edit_decisions` contains the locked renderer family/runtime/composition mode inherited
from the approved proposal, a shot-level `timeline`, named `video_tracks`, deferred
`audio_tracks`, a `caption_track`, validation flags, a final CTA plan, rhythm analysis,
asset utilization, and a concrete edit review.

The primary visual track is continuous and is validated for gaps and overlaps. Supporting
tracks (`graphics`, `overlays`, `video_secondary`) are intentionally sparse. Their events
are semantic instructions for the future composition runtime, not rendering coordinates.

## Editorial proof

Phase 6 does not render pixels, but it must prove that its timeline is executable and
coherent. Every primary shot preserves its upstream `shot_id`, binds the matching script
caption and narration events, and resolves to an asset from the approved manifest in the
planned scene. Hook-impact and CTA-resolve SFX positions are reserved as deferred audio
requirements. Transition boundaries avoid immediate repetition while preserving semantic
match cuts. The canonical YouTube Short profile locks resolution, frame rate, safe zones,
and duration constraints; the smoke benchmark additionally verifies that every referenced
manifest file exists on disk.

## Running the smoke benchmark

Run the complete pipeline through edit:

```powershell
python scripts/smoke_phase6.py --topic "How OpenAI Built An Empire"
```

To validate an existing real Phase 5 production without generating upstream work again:

```powershell
python scripts/smoke_phase6.py --reuse-production <production-id>
```

The edit stage stores `edit_decisions.vNNN.json` via `ArtifactStore` under the project’s
`edit/` directory and writes derived inspection files beside it: `edit_summary.md`,
`edit_review_report.json`, `asset_utilization_report.json`, and `edit_generation_report.json`.
