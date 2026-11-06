# Stage 1 — Foundation and Provider Validation

Status date: 2026-11-06

## Goal
Make the existing ai_video_factory repository the durable orchestration layer for upload-ready Shorts and horizontal YouTube videos. Keep it separate from youtube-strategist.

## Stage 1A — Inventory and architecture
- [x] Audit connected app/tool catalogues and live balances where available.
- [x] Add Porter research, creative profiles, audio actions and account status.
- [x] Save persistent inventory in Notion.
- [x] Add initial provider inventory, roadmap and provider-independent project schema on branch stage1/provider-registry.

## Stage 1B — Assembly proof
- [x] Build a disposable deterministic FFmpeg smoke test using synthetic visuals, synthetic voice and a quiet audio bed.
- [x] Render four sequential scenes into an 18-second 1080x1920 MP4.
- [x] Verify H.264, 30fps, AAC stereo 48kHz, full decode, no black segments >=0.5s, SRT and cover frame.
- [ ] Import the local smoke-test MP4 into InVideo and verify hosted timeline/export. Project and 1080x1920/30fps timeline created; upload slot issued. Runtime could not PUT local bytes to signed upload endpoint; use InVideo project UI to upload the attached/downloaded MP4.
- [ ] Confirm AI Producer export from an actual uploaded clip; account price table shows most generation/editing pipeline actions free for a limited time, export free, and scene restyles paid at 6 credits per generated second. No projects existed at inspection.
- [ ] Confirm Adobe export entitlement from an actual account workflow.
- [ ] Compare local FFmpeg/HyperFrames assembly against the existing pipeline.
- [ ] Retrieve, play and inspect final hosted MP4.

## Stage 1C — Scene and audio
- [ ] Test PREVIS scene export and file handoff.
- [ ] Check cost/credits before Porter, Pollo, ImagineArt, Clipwave or other generation.
- [ ] Check commercial rights and cost before TTS.
- [ ] Use YouTube Audio Library for final music unless another commercial licence is verified.
- [ ] Store asset provenance and licence evidence per scene.

## Stage 1D — Quality and packaging
- [x] Define technical target: 1080x1920 vertical or 1920x1080 horizontal; H.264 MP4, AAC stereo 48kHz, 30fps.
- [x] Produce SRT and cover frame in smoke test.
- [ ] Add black-frame, clipping, missing media, subtitle drift and watermark checks to final QA.
- [ ] Generate final thumbnail, title, description, hashtags and tags.
- [ ] Keep publishing manual/private until explicit approval.

## Stage 2 — Research engine
- [ ] Score channel fit, outlier evidence, freshness, search demand, retention potential and production feasibility.
- [ ] Separate explanatory topics from screen-recording/demo topics.
- [ ] Record primary sources, claims, dates and fact-check status.
- [ ] Learn from full-channel performance, not only recent uploads.

## Project invariants
- AI Simplified Lab; faceless AI education/news/tutorials.
- Predominantly Telugu-speaking audience; simple English narration unless Telugu is selected.
- Topic-specific visuals; avoid generic repetitive slides and static templates.
- No identifiable real faces.
- Choose format per story.
- Unknown generation cost means stop and ask.
- Never commit credentials.
- No auto-publish or metadata mutation without approval.
