# Stage 1C — Windows / Antigravity Local Render Proof

**Branch:** `stage1c/dynamic-scene-engine`  
**Purpose:** Render the five-scene dynamic proof locally without consuming any AI video/image-generation credits.

## 1. Switch to the tested branch

From the existing `ai_video_factory` repository folder:

```powershell
git fetch origin
git checkout stage1c/dynamic-scene-engine
git pull --ff-only
```

Do not merge this branch into `main` yet.

## 2. Run preflight checks (no media generation)

```powershell
node --check pipeline/audio-generator.mjs
node --check pipeline/composition-generator.mjs
node --check pipeline/dynamic-scene-gate.mjs
node --check pipeline/dynamic-scene-renderer.mjs
node --check pipeline/make-short.mjs
node --check pipeline/render-and-mux.mjs
node --check pipeline/storyboard-planner.mjs
node --check pipeline/visual-linter.mjs
python -m py_compile pipeline/tts-exact-aligner.py
node --test tests/*.test.mjs
node pipeline/validate-dynamic-scene.mjs examples/dynamic-scene-proof.json
```

The validator is offline and does not call any provider. It checks five distinct compositions, object-level animation, phrase triggers, reaction motion, SFX keys, per-scene captions, audio direction and transitions.

## 3. Render the dynamic proof (local tools only)

First ensure the existing local prerequisites are available:
- Node.js and the repository's installed HyperFrames runtime.
- FFmpeg and FFprobe.
- Python with the existing `edge-tts` dependency.
- The curated `assets/sfx` library and manifest.

Then run:

```powershell
node pipeline/make-short.mjs --script examples/dynamic-scene-proof.json --id short-dynamic-prompt-cache-proof-local
```

This uses:
- local Edge-TTS for narration and exact WordBoundary timing;
- the existing bundled SFX library;
- original procedural SVG scenes and GSAP motion;
- local HyperFrames + FFmpeg for the MP4;
- the existing FFprobe/decode/black-frame/rights QA and packaging stages.

The proof contains four different explanatory scenes plus a bespoke animated subscribe outro. No third-party video-generation API is required.

## 4. Inspect the result

Expected project folder:

`projects/short-dynamic-prompt-cache-proof-local/`

Review:
- `exports/final.mp4` — final rendered video.
- `exports/contact-sheet.png` — scene overview.
- `exports/motion-contact-sheet.png` and `exports/frames/` — entrance/action/payoff frames.
- `exports/youtube-package.json` — title, description, tags, source and rights QA.
- `speech-words.json` and `speech-timings.json` — actual word/scene timing.
- `voice.mp3`, `audio-mix.wav`, `sfx-cues.json` — audio outputs.
- `exports/cover-frame.png` and generated VTT/SRT — cover and captions.

Check the whole video, not only the contact sheet:
1. Every scene must explain its spoken idea visually, even when muted.
2. There must be no card/slide sequence, repeated layout or decorative filler.
3. Each element must have a purpose; camera and object motion must be motivated.
4. SFX must land on the intended action, not randomly at scene starts.
5. Captions must not obscure the main action.
6. Voice must remain clear above SFX/music; no clipping or drift.
7. Confirm the real export is 1080×1920, 30 fps, H.264, AAC stereo 48 kHz, fully decodable and free of black gaps/watermarks.

## 5. Important limitations

- The example's narration is a technical test script, not a final research-checked public video.
- Edge-TTS commercial terms are not independently certified by the factory; review the provider terms before monetized publishing.
- The proof has no background-music file attached. The optional music path requires a real local track plus source/licence metadata; no music generation credits are spent.
- The dynamic renderer currently targets vertical 1080×1920. Horizontal 1920×1080 needs a separate tested canvas/safe-zone profile.
- A passing automated test does not certify visual quality. The actual MP4 must be watched and its audio heard before release.
