# AI Simplified Lab — Video Factory Roadmap

**Status date:** 6 November 2026  
**Active branch:** `stage1c/dynamic-scene-engine`  
**Repository:** `aisimplified280-png/ai_video_factory`  
**Boundary:** This factory is separate from the YouTube Strategist Streamlit app.

## Factory objective

Turn an approved topic into an upload-ready YouTube Short (9:16) or horizontal video (16:9): research, fact-checking, script, original scenes, voice, music/SFX, captions, editing, final render, QA, thumbnail and YouTube metadata. Reuse project/channel configuration without repeatedly setting it up.

## Non-negotiable creative rules

- This must be a real animated video, never a PowerPoint/slideshow or a stack of card templates.
- Every scene is directed from its narration and question. Composition, camera, environment, objects and visual events are scene-specific.
- Each shot needs a visible setup/action/payoff (or story-motivated stillness), purposeful object-level movement and cause/effect.
- No passive stock wallpaper, repeated layouts, decorative filler or generic ambient motion.
- Every asset and sound event must explain or reinforce something. If an element has no purpose, remove it.
- Voice, captions and visual triggers share the same actual word-timing source.
- Faceless only; no identifiable real people.
- Audience is predominantly Telugu-speaking; use clear, simple English narration unless Telugu is explicitly selected.
- Prefer free, no-watermark and rights-clear providers; unknown cost means stop before generation.
- No YouTube upload or metadata change without explicit approval.

## Stage 1A — Provider inventory and architecture

- [x] Audit available MCP provider integrations and account quotas where exposed.
- [x] Add Porter Metrics research, creative, audio and account-status details.
- [x] Save provider inventory and workflow in the connected Notion workspace.
- [x] Create provider inventory, roadmap and provider-independent video project schema on `stage1/provider-registry`.
- [x] Keep the project separate from YouTube Strategist.

## Stage 1B — Editing and final export proof

- [x] Create a disposable 18-second vertical FFmpeg smoke test using synthetic visuals, synthetic narration and SFX.
- [x] Correct an initial headline-clipping defect by inspecting and revising the rendered frame.
- [x] Verify 1080×1920, H.264, 30 fps, AAC stereo 48 kHz, full decode, no detected black gaps >=0.5 seconds, SRT and cover frame.
- [x] Create an InVideo manual-timeline test project at 1080×1920 / 30 fps.
- [ ] Upload the smoke-test MP4 into InVideo and verify hosted timeline/export. A signed upload slot was issued, but this runtime couldn't PUT its local bytes.
- [ ] Verify AI Producer edit/export from a real uploaded clip. Its live pricing table at audit showed many editing/export actions free temporarily; scene restyles are paid. Recheck before use.
- [ ] Verify Adobe export entitlement from an account-level edit/export test.
- [ ] Compare hosted editing against the deterministic local HyperFrames/FFmpeg route.

**Status:** Local technical smoke test is proven. Hosted third-party editor/export has not yet been proven.

## Stage 1C — Dynamic scene and audio engine

### Implemented on `stage1c/dynamic-scene-engine`

- [x] Add `docs/DYNAMIC_SCENE_CHARTER.md` and update the technical specification.
- [x] Add `dynamic-scene-director` skill; update storyboard, composition and rendered-video-critique skills.
- [x] Add fail-closed `dynamic-scene-gate.mjs` and zero-generation validation CLI.
- [x] Require unique scene compositions, renderable scene elements, camera animation, visual-event setup/action/payoff, object motion, executable cause/effect reactions and motivated transitions.
- [x] Reject card/slide/template fallback for new dynamic projects.
- [x] Add a procedural full-frame SVG scene renderer with scene-specific camera/object choreography.
- [x] Remove recurring global branding/header/progress/halftone/orbs and fixed caption pill from dynamic projects. Legacy projects retain the old rendering path.
- [x] Add per-scene caption placement and typography.
- [x] Switch Edge-TTS alignment to actual WordBoundary timestamps; use these as the shared clock for captions and scene-motion triggers.
- [x] Fail closed when TTS words do not match the approved narration.
- [x] Validate SFX ids against the curated local manifest and require scene-relative cue timing and purpose.
- [x] Preserve SFX cue details through the storyboard, composition and YouTube audio-rights report.
- [x] Add optional local music bed support under `assets/music/`, requiring creator-confirmed rights metadata and sidechain ducking.
- [x] Record voice provider limitations, SFX licence/hash details and optional music source/licence details in the YouTube package.
- [x] Add unit tests for dynamic gate, renderer, word alignment and mismatch handling.
- [x] Add GitHub Actions for syntax, offline tests and dynamic-plan validation.

### Validation status

- [x] GitHub Actions run **42174748496** passed on the branch after the dynamic scene test fixture was corrected: 62 offline tests passed and the one-scene example validated.
- [ ] Run the enhanced CI that also checks JavaScript/Python syntax and validates the four-scene proof.
- [ ] Run the dynamic proof locally in the user's Windows/Antigravity environment, render it with HyperFrames and inspect actual entrance/action/payoff frames and audio.
- [ ] Run a four-scene visual critique and technical QA before treating dynamic rendering as production-ready.
- [ ] Verify caption/action synchronization in an actual rendered MP4.
- [ ] Add and test a rights-cleared music file; optional local music mix is implemented but has not yet been tested with a real licensed track.
- [ ] Verify scene ambience design is rendered as audio, not merely stored as descriptive direction.

### Current limitations

- The dynamic renderer currently targets vertical 1080×1920 / 30 fps. Horizontal 1920×1080 requires a separate format-aware canvas, safe-zone and render-QA implementation.
- No actual four-scene dynamic MP4 has been rendered and visually approved yet.
- The WordBoundary alignment and renderer have automated unit tests; local Windows/Antigravity execution is still required for final validation.
- Edge-TTS commercial terms are not independently certified by this pipeline.
- Optional music requires a local audio asset plus source/licence evidence; no generated or stock music has been assumed free.

## Stage 1D — Final production quality and packaging

- [x] Define target vertical technical profile: 1080×1920, H.264 MP4, 30 fps, AAC stereo 48 kHz.
- [x] Generate SRT and cover frame in the local smoke-test pipeline.
- [ ] Add final QA checks for subtitle drift, loudness/true peak, clipping, missing assets, black frames, watermarks and licence ledger.
- [ ] Inspect all scene entrance/action/payoff frames; technical QA alone does not approve creative quality.
- [ ] Add vertical thumbnail/cover generation and safe-zone checks.
- [ ] Generate title, description, complete tags, hashtags and SRT from the approved script/package.
- [ ] Verify final MP4 exists, decodes and plays before presenting it as complete.
- [ ] Keep publishing manual and approval-gated.

## Stage 2 — Research and topic selection

- [ ] Combine Windsor channel performance, ChannelzIQ catalogue/content gaps, vidIQ outliers, Ubersuggest search demand, Porter/Firecrawl/YouTube SERP and primary sources.
- [ ] Score channel fit, outlier evidence, novelty, freshness, search demand, audience-retention potential and production feasibility.
- [ ] Classify each topic as explanatory, cinematic, hybrid or screen-demo. A demo topic is eligible only when genuine capture is available.
- [ ] Save evidence, source URLs, publication dates and claim verification.
- [ ] Learn from the whole channel catalogue, not only recent uploads.

## Stage 3 — Full reusable factory

- [ ] Provider capability/quota registry with preflight and user approval for unknown or paid actions.
- [ ] Reusable channel profile, visual identity, voice settings, subtitle safe zones and export profiles.
- [ ] Scene planner that chooses a distinct visual approach for each narration segment (3D, procedural SVG/canvas, data visualization, diagrams in motion, licensed B-roll, genuine screen capture, etc.).
- [ ] Separate voice, SFX, ambience and music tracks with per-scene timing and ducking.
- [ ] Provider-independent edit timeline so providers can be replaced.
- [ ] One-command build from approved topic/script to final MP4, SRT, thumbnail and YouTube package.
- [ ] Persist project state, assets, licences, timelines, QA reports and revisions.
- [ ] Human review before publishing.

## Project invariants

- AI Simplified Lab; faceless AI education, AI news, AI tools and tutorials.
- Predominantly Telugu-speaking audience; simple English voiceover unless Telugu is selected.
- No templates or slide-deck output for new projects.
- No identifiable real people.
- Topic-specific visuals; no generic filler.
- Unknown generation cost means stop and ask.
- Never commit credentials to Git.
- No automatic YouTube publishing or metadata mutation without approval.
