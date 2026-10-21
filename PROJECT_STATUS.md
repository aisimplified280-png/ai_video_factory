# AI Simplified Lab — Project Status

Last checkpoint: 2026-10-21 (Milestone: Phase 1 Rendering Pipeline Verified)

## Goal
Build a ₹0 ongoing-cost workflow for creating YouTube Shorts from idea to finished, verified video for AI Simplified Lab (@AISimplifiedLab).

## Non-negotiables
- Zero ongoing cost (no paid APIs, credits, or subscriptions).
- Faceless only — original AI imagery/graphics, motion graphics, code-driven animations, or licensed free assets. Never real people or stock clips with identifiable people.
- Vertical 9:16 (1080x1920) at 30 fps.
- Fast, clean, purposeful visual explanation; no meaningless motion or visual clutter.
- Clear simple international English suitable for YouTube Telugu auto-dubbing.
- Verified deliverables only — no claiming a step works until verified with tools (FFprobe, FFmpeg, frame inspection).
- Safe for Windows 10 Home with ~2.1 GB free RAM.

## Verified Infrastructure
| Component | Version / Location | Status | Notes |
|-----------|--------------------|--------|-------|
| OS | Windows 10 Home (win32 x64) | Confirmed | Node 24.19.0, npm 9.7.2, Git 2.47.1 |
| FFmpeg & FFprobe | 9.0.1 (gyan.dev build) | Confirmed | Full decode and probe verified |
| HyperFrames | 0.8.32 (`.favstash-studio\runtime\node_modules\.bin\hyperframes.cmd`) | **Verified Render** | Portrait 1080x1920, 30fps, 1 worker, low-memory mode renders in 21s without Docker |
| Edge-TTS | 7.3.1 (`edge-tts.exe`) | Confirmed | Generates high-quality voiceover + synchronized VTT subtitles at ₹0 cost |
| Audio SFX & Sync | `sfx-sync.mjs` + 16 curated WAV sound effects | Confirmed | Attack/peak frame alignment and loudness mastering verified |
| Creator Skills | 5 skills in `.agents\skills` & `.favstash-studio\skills-source` | Confirmed | find-ideas, write-script, edit-video, product-motion-ads, text-over-footage |

## Milestone Log
- [x] Checkpoint 1 (2026-10-20): Discovery and environment audit.
- [x] Checkpoint 2 (2026-10-21): **Phase 1 Rendering Pipeline Proven**.
  - Created `.favstash-studio\setup-check\` minimal valid portrait composition.
  - Passed `hyperframes lint` with 0 errors and 0 warnings.
  - Executed render: 90 frames, 3.0s, 1080x1920 @ 30fps MP4.
  - Verified with FFprobe (stream parameters), FFmpeg (full decode test), frame extraction (1.0s and 2.5s PNGs), and blackdetect/signalstats tests.
  - Verified local `edge-tts` for voiceover and subtitles, and `sfx-sync.mjs` for cue sync.
- [x] Checkpoint 3 (2026-10-21): **Phase 2 End-to-End Automated Shorts Pipeline Operational**.
  - Built `pipeline/make-short.mjs`, `pipeline/audio-generator.mjs`, `pipeline/composition-generator.mjs`, and `pipeline/render-and-mux.mjs`.
  - Pushed initial release to `aisimplified280-png/ai_video_factory`.
- [x] Checkpoint 4 (2026-10-21): **Phase 3 Deep Quality, Evidence & Exact Timing Hardening**.
  - **Eliminated Fake Metrics & Pseudo-Code**: Hardcoded "10x", "80%", and `new Studio()` removed. Substituted with authentic commands and cited documentation.
  - **Exact SentenceBoundary Timing Engine**: Created `pipeline/tts-exact-aligner.py` extracting true speech boundaries directly from Edge-TTS stream.
  - **100% Offline Vendored Builds**: Vendored GSAP into `pipeline/vendor/gsap.min.js`, eliminating external CDN dependency.
  - **Modular Semantic Storyboards**: Implemented Data-Flow Architecture Diagrams, Step-Process lists, authentic syntax terminals, and cited concept explainers.
  - **Truthful Segregated QA Manifest**: Separated media engineering checks (`automatedMediaQA: PASS`) from editorial oversight (`youtubePolicyReview: UNASSESSED`).
  - Rendered and verified `projects/short-2324-claude-prompt-caching` (26.23s, 787 frames @ 30fps).
- [x] Checkpoint 5 (2026-10-21): **Asset-Aware Video Engine, License Gate & Programmatic QA Verified**.
  - **Asset Scout & Rights Ledger**: Built `pipeline/rights-gate.mjs`, `pipeline/asset-scout/registry.mjs`, and provider adapters (`FixtureProvider`, `OpenverseProvider`, `PexelsProvider`). Enforces commercial use, checks no-derivatives, flags likeness/trademarks to `REVIEW_REQUIRED`, computes SHA-256 hashes, and records manifests in `assets/rights-ledger.json`.
  - **Story-First Semantic Storyboard**: Built `pipeline/storyboard-planner.mjs` generating editable intermediate representation `storyboard.json` with narrative purposes, viewer questions, visual modes, exact timestamps, and verified asset IDs.
  - **Scouted Asset Rendering**: Updated `pipeline/composition-generator.mjs` to copy and embed verified scouted diagrams/graphics inside Claude-styled cards with GSAP entrance scaling.
  - **Programmatic QA & Release Governance**: Implemented `pipeline/qa-gate.mjs` replacing hardcoded results with actual FFmpeg `blackdetect` parsing, stream parameter checks, chronological script alignment, and `evaluateReleaseEligibility()`.
  - **Contact Sheet Generation**: Updated `pipeline/render-and-mux.mjs` to extract scene midpoint frames and compile `exports/contact-sheet.png` for instant visual diversity evaluation.
  - **5 Antigravity Project Skills**: Created `asset-scout-rights`, `storyboard-director`, `composition-builder`, `rendered-video-critique`, and `release-governance` under `.agents/skills/`.
  - **Verified Test Suite**: 13/13 unit tests passing in ~170ms with 0 API keys required.
  - **End-to-End Proven Short**: Generated, linted, rendered, muxed, and packaged `short-6501-claude-prompt-caching` (26.23s, 787 frames @ 30fps, 1080x1920) with verified CC0 SVG diagram and `releaseEligible: true`.

- [x] Checkpoint 6 (2026-10-21): **Engine Hardening & Creative Direction Upgrade (AI Simplified Lab Purple Collage Explainer)**.
  - **Fail-Closed Release Gate**: Completely closed all fail-open pathways. `evaluateReleaseEligibility` strictly blocks release on any `UNKNOWN`, missing, or non-`PASS` checks (including unexecuted black frame detectors or malformed probe data). Segregated `technicalChecksPassed`, `rightsApproved`, `editorialReviewStatus: UNASSESSED`, and `publishApproved: false`.
  - **Strict Rights Gate & Asset Filtering**: `REVIEW_REQUIRED` and `REJECTED` assets are strictly prevented from returning as approved assets or entering composition code. Validated URLs, hashes, and licenses without assuming default licenses.
  - **Provider Hierarchy & Openverse Normalization**: Online providers (`Pexels`, `Openverse`) are searched before fallback fixtures. Explicit license normalization for Openverse (`normalizeLicenseId`) mapping `by`, `by-nc`, `cc0`, `pdm`, etc., with zero assumptions.
  - **Unified Credits & Attribution Output**: Unified schema (`youtubeDescriptionText`, `reportText`, `creditsText`) between rights-gate, renderer, and YouTube manifest. Approved CC-BY assets automatically embed full creator, license identifier, license link, and source page in the generated YouTube description and QA ledger.
  - **Exact Speech Timing Validation**: Strict 1-to-1 match enforced between script beats and extracted `SentenceBoundary` ticks without silent fallback.
  - **Brand Identity — AI Simplified Lab Purple Collage Explainer**:
    - Replaced the hardcoded Claude warm-ivory/terracotta cards with AI Simplified Lab's brand identity.
    - Deep violet/ink textured background (`#0d0819` to `#241147`) with halftone dot-matrix pattern overlay (`rgba(192, 132, 252, 0.13)` on 26px grid).
    - Bold modern typography, glowing status badges, illuminated diagram frames, authentic code syntax, and kinetic active-caption pills.
    - Narrative-driven compositions: physical metaphors (conveyor belts, express multi-layer graph highways), architecture flow diagrams, and authentic code syntax terminals.
  - **Visual Diversity Linter**: Built `pipeline/visual-linter.mjs` to deterministically flag consecutive mode repetitions and overused layouts (>50%).
  - **Updated Antigravity Skills**: Upgraded `storyboard-director`, `composition-builder`, and `rendered-video-critique` to enforce the AI Simplified Lab Purple Collage design system.
  - **19/19 Passing Unit Tests**: Fast deterministic suite running offline in ~180ms.
  - **Two Distinct Proven Shorts Rendered & Verified**:
    1. `short-7584-claude-prompt-caching` (26.23s, 787 frames): Verified CC0 diagram, authentic syntax (`claude-3-5-sonnet-latest`, 5-min/1-hr TTL context), and 0 black frames.
    2. `short-3325-vector-database-indexing` (27.83s, 835 frames): Verified CC-BY-2.0 scouted asset, multi-layer graph highway metaphor, full credit attribution in YouTube package, and 0 black frames.

## Resume Instruction
The hardened asset-aware video factory with the AI Simplified Lab Purple Collage Explainer design system is 100% operational offline.

