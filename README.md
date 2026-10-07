# ExplainShort Factory

> The production pipeline now includes a Phase 6 renderer-neutral editorial edit plan.
> See [Phase 6 Edit Decisions](docs/PHASE_6_EDIT_DECISIONS.md) for the artifact contract
> and the smoke benchmark. It deliberately does not render or compose the final video.

Create vertical, visual-first explainer Shorts in the style of the supplied hashing reference: bright diagram cards, large readable labels, arrows, a dark "practical payoff" scene, and an editable voice-over script. The output contains no narration or music.

## What it creates

For every topic it creates a self-contained folder under `output/`:

- `visual_only.mp4` — a 720 × 1280, 9:16, no-audio video ready to stitch
- `vo_script.txt` — timed narration script
- `manifest.json` — scene order, timing, visual direction, and text
- `scenes/*.png` — every editable visual card as a separate asset

## Requirements

- Python 3.10+ with Pillow (`pip install Pillow`)
- FFmpeg on your PATH

Optional: add `--ai` and set `OPENAI_API_KEY` to have a model write a genuinely topic-specific six-scene storyboard. Without `--ai` the generator is entirely local, using a clear generic explainer structure based on the topic.

## Run

```powershell
python create_short.py --topic "How does a VPN work?"
```

## One-topic browser UI (recommended)

```powershell
python app.py
```

Open `http://127.0.0.1:5000`. Enter only a topic. The UI tries configured OpenAI models, then Gemini models, then a local Ollama host, and always finishes with the offline storyboard fallback. It displays key/provider availability only—never key values.

Configure an alternative model order with comma-separated environment variables, for example `OPENAI_MODELS=gpt-5-mini,gpt-5.2` or `GEMINI_MODELS=gemini-3.8-flash,gemini-2.0-flash`. Add `OLLAMA_HOST=http://localhost:11434` to enable the local Ollama option.

Add context if needed:

```powershell
python create_short.py --topic "What is Docker?" --notes "Audience: beginner developers. Mention containers versus virtual machines."
```

For a topic-specific AI storyboard (optional network call):

```powershell
$env:OPENAI_API_KEY = "your-key"
python create_short.py --topic "How does a VPN work?" --ai
```

The renderer uses only local Pillow drawing and FFmpeg. The optional storyboard call is the only network operation. It never uploads your generated images or videos.

## Editing / stitching

Open `scenes/` in any editor, or use `manifest.json` as a shot list. `visual_only.mp4` has no audio track, so it can be dropped under your own voice-over without removing anything first. Match your narration to the time ranges printed in `vo_script.txt`.

## Style controls

Use `--duration 30` (default) to change total length. The six-scene rhythm deliberately mirrors the reference:

1. Question / hook
2. The thing or problem
3. Step one
4. Step two / flow
5. Dark practical payoff
6. Call to action

This creates original diagrams and copy rather than copying the reference footage or its watermark.
