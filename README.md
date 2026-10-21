# AI Video Factory — AI Simplified Lab (@AISimplifiedLab)

> Automated, zero-cost, high-CTR YouTube Shorts generation engine powered by code-driven motion graphics (HyperFrames + GSAP) and neural speech synthesis.

[![YouTube Shorts](https://img.shields.io/badge/YouTube-Shorts%209%3A16-red.svg)](https://youtube.com/@AISimplifiedLab)
[![Aesthetic](https://img.shields.io/badge/Aesthetic-Claude%20%28Anthropic%29-d97757.svg)](https://anthropic.com)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](#)

---

## ⚡ Highlights

- **₹0 Ongoing Cost**: Runs locally using headless browser rendering (`hyperframes`), `ffmpeg`, and `edge-tts`. Zero cloud GPU or API subscriptions needed.
- **High-CTR Retention Architecture**:
  - **Hook Impact Formula (0.0s – 1.2s)**: Frame 0 transient attack SFX, glowing badge, and curiosity gap headline to maximize the Viewed vs. Swiped Away ratio.
  - **Kinetic Word-by-Word Active Captions**: Words dynamically highlight in Claude Terracotta (`#d97757`) with micro-scale pops as they are spoken.
  - **Safe-Zone Mastery**: 1080×1920 layout strictly respects YouTube mobile UI safe zones (margins: top 240px, bottom 380px, right 160px).
  - **Seamless Loop Design**: Video payoffs loop seamlessly back into the hook for >100% Average Percentage Viewed (APV).
- **YouTube Policy Compliant**: 100% original code-generated animations—no low-effort stock video scrapers or reused content flags.
- **Lightweight**: Optimized for consumer machines (~2.1 GB RAM envelope) using single-worker low-memory streaming capture.

---

## 🎨 Visual Aesthetics (Claude / Anthropic Design System)

- **Background**: Warm Ivory paper (`#fbfaf7` / `#f3ede2`) with a subtle technical paper grid.
- **Palette**: Signature Claude Terracotta (`#d97757`), Warm Amber (`#e09f3e`), Leaf Green (`#16a34a`), and Deep Charcoal Ink (`#1c1917`).
- **Interactive UI Artifacts**:
  - Shimmering laser rim hero cards
  - Syntax-highlighted code terminal with live typing cursor
  - Animated SVG circular progress gauges
  - Comparison cards (Traditional vs. AI Simplified)

---

## 🚀 Quick Start

### Prerequisites
- **Node.js**: v20+ or v24+
- **Python**: 3.10+ with `edge-tts` (`pip install edge-tts`)
- **FFmpeg & FFprobe**: Installed and available in system PATH

### Generate a Short with One Command

#### 1. From a Topic / Prompt:
```bash
node pipeline/make-short.mjs --topic "Claude AI Workflows"
```

#### 2. From a Custom Script:
```bash
node pipeline/make-short.mjs --script path/to/script.json
```

### Outputs Generated
Each run outputs to `projects/<short-id>/`:
- `exports/final.mp4`: Verified 1080×1920 @ 30fps portrait Short (mastered at -14 LUFS).
- `exports/cover-frame.png`: High-CTR thumbnail cover frame extracted at the hook peak.
- `exports/youtube-package.json`: Title, SEO description, hashtags, and YouTube policy compliance checklist.

---

## 📁 Repository Structure

```text
├── pipeline/
│   ├── config.mjs                  # Central engine configuration
│   ├── audio-generator.mjs         # Edge-TTS voice synthesis & SFX aligner
│   ├── composition-generator.mjs   # HTML5 / GSAP / Claude aesthetic synthesizer
│   ├── render-and-mux.mjs          # HyperFrames render, FFmpeg mux & QA checks
│   └── make-short.mjs              # Master CLI orchestrator
├── projects/                       # Generated Shorts production directories
├── .agents/skills/                 # Creator skills (find-ideas, write-script, edit-video)
├── PROJECT_STATUS.md               # Current engineering status & verified milestones
└── PROGRESS_LOG.md                 # Execution log & command history
```

---

## 📜 License
Apache-2.0
