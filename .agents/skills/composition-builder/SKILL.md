---
name: composition-builder
description: "Implement 100% offline HTML5, CSS and GSAP 9:16 compositions for HyperFrames with Claude warm ivory/terracotta aesthetics, kinetic active captions, and safe-zone enforcement."
---

# Composition Builder

Build high-performance, deterministic 9:16 portrait video compositions using HyperFrames and GSAP.

## Aesthetic Identity (Claude Editorial Style)

- **Canvas Background**: Warm ivory paper tone (`#fbfaf7` / `#faf8f5`) with subtle 50px grid lines (`rgba(140, 120, 100, 0.08)`).
- **Cards**: Clean elevated white paper cards (`#ffffff`) with subtle warm borders (`#e7ded4`) and soft layered drop shadows (`0 24px 48px -12px rgba(60, 45, 30, 0.12)`).
- **Accents**: Anthropic terracotta coral (`#d97757`) and warm amber (`#e09f3e`).
- **Typography**: Apple System / Segoe UI / Roboto, dark charcoal text (`#1c1917` / `#292524`).
- **Kinetic Subtitles**: Word-by-word active highlight (`#d97757` on pill background) positioned in the bottom safe zone.

## Safe Zone Constraints (1080x1920)

- Top Margins: Safe from Y=240px downwards (avoids YouTube channel info & top controls).
- Bottom Margins: Safe up to Y=1540px (leaves 380px at bottom for Shorts UI, like buttons, titles).
- Main Stage: Bound between Y=250px and Y=1380px.

## Offline Vendoring & Zero-CDN Rule

- Never import scripts or fonts from unverified CDNs (`unpkg`, `cdnjs`, `jsdelivr`).
- Copy local `pipeline/vendor/gsap.min.js` directly to `./assets/vendor/gsap.min.js`.
- Escape all dynamic text inputs (`escapeHtml`) before inserting into DOM templates.

## Observable Completion Criteria

- `index.html` has zero remote script or stylesheet tags.
- Composition passes `hyperframes lint`.
- All text and cards stay strictly within 1080x1920 safe-zone coordinates.
