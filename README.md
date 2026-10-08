# AI Simplified Video Factory (v2)

Autonomous, end-to-end video production factory producing 9:16 vertical shorts powered by multi-provider live research, neural voiceover, multi-layer depth generation, and the Remotion React composition engine.

---

## Architecture Overview

The factory executes an autonomous 8-stage production pipeline:
1. **Live Web Research (Phase 10)**: Real-time query retrieval across Brave, Google News, Reddit, and official sources.
2. **Script Intelligence & Neural TTS (Phase 11 & 17)**: Context-grounded tech scripts synthesized into Microsoft Edge JennyNeural audio with measured phoneme timing.
3. **Packaging & Channel Memory (Phase 12 & 14)**: 10 psychological title candidates, curiosity scoring, thumbnail text/prompts, boosted by historical channel analytics.
4. **Editorial Design System & Safe Zones (Phase 16)**: Strict 9:16 vertical layout (1080x1920), top 75% safe-zone for diagrams (y <= 1400), bottom 25% reserved for captions and CTA.
5. **Dynamic Multi-Layer Scene Generation (Phase 17)**: 3-layer architecture (`bg`, `mid`, `fg`) with 3D parallax, topic-domain routing (software vs physical hardware separation), and dynamic entity extraction (zero static boilerplate).
6. **Remotion Composition & Render (Phase 9.3)**: React/TypeScript composition bundle rendered via headless Chromium into broadcast-ready H.264 MP4.
7. **Automated Evidence-Based QA (Phase 16 & 17)**: 12 technical gates (codecs, freeze detection, caption bounds, activity delta) and visual language QA.
8. **Release Packaging**: Self-contained delivery bundles assembled in `output/<topic_slug>/`.

---

## Quick Start

### 1. Web UI (Recommended)
```powershell
python app.py
```
Open **[http://127.0.0.1:5000](http://127.0.0.1:5000)** in your browser. Enter any topic (or paste a custom narration script) and click **Generate Short Video ⚡**.

### 2. Autonomous CLI
```powershell
# Produce a full video end-to-end
python scripts/factory.py produce --topic "Amazon Bedrock Native RAG Architecture"

# Record publication metrics to train the factory memory
python scripts/factory.py record-metrics --production proj_3e27bd7a --topic "..." --title "..." --views 45000 --ctr 8.2 --watch-pct 74.0

# View aggregated channel insights
python scripts/factory.py insights
```

### 3. Local Production Runner
```powershell
# Validate, render, and QA a specific production project
python scripts/run_local_production.py --production <production_id> --validate --render --qa
```

---

## Output Structure

Each completed production produces a release package under `output/<topic_slug>/`:
- `video.mp4` / `final_video.mp4`: 1080 × 1920, 30fps H.264 video with synchronized audio.
- `title.txt`: Optimized YouTube title selected by channel memory.
- `description.txt`: SEO-optimized description with chapters and hashtags.
- `thumbnail_text.txt` & `thumbnail_prompt.txt`: High-CTR thumbnail copy and visual generation prompt.
- `preview.png` / `contact_sheet.png`: 11-frame decile contact sheet verifying visual progression.
- `visual_language_qa_report.json`: Evidence-based visual diversity and motion report.
- `factory_manifest.json`: Full production lineage and QA scorecard.

---

## Requirements

- **Python**: 3.10+ (`pip install -r requirements.txt`)
- **Node.js**: v18+ (`npm install` inside `remotion-composer/`)
- **FFmpeg**: Accessible on system `PATH`
- **API Keys**: Configured in `.env` (`OPENAI_API_KEY`, `GEMINI_API_KEY`, `ANTHROPIC_API_KEY`, `BRAVE_API_KEY`)
