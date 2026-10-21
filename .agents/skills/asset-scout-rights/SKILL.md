---
name: asset-scout-rights
description: "Search free stock media, diagrams and public archives (Pexels, Pixabay, Openverse, local fixtures), verify license compatibility and commercial-use rights, calculate SHA-256 hashes, and record verified manifests in rights-ledger.json before rendering."
---

# Asset Scout & Rights Verification

Use this skill to source and license-gate media for YouTube Shorts and explainers. Free to download does NOT mean free to reuse in monetized videos. Every external asset must have verified rights provenance.

## Core Principles

1. **Verify Before Ingesting**: Never download or render an asset without first checking license terms and restrictions.
2. **Deterministic Licensing**:
   - CC0 / Public Domain / Pexels / Pixabay Commercial: Approved.
   - CC-BY: Approved with automatic attribution formatting.
   - Non-Commercial (NC): Strict rejection (`REJECTED`).
   - No-Derivatives (ND): Rejected (`REJECTED`) when visual transformations (cropping, motion) are planned.
   - Recognizable Persons / Trademarks: Route to `REVIEW_REQUIRED`.
3. **Tamper-Proof Provenance**: Compute and store SHA-256 hashes of cached files in `assets/rights-ledger.json`.

## Procedure

1. **Query Formulation**: Match search query to the specific narrative beat (e.g., `"prompt-caching-architecture"`, `"vector-database-diagram"`).
2. **Provider Evaluation**:
   - `FixtureProvider`: Zero API keys, 100% offline deterministic SVG architecture diagrams.
   - `OpenverseProvider`: Filter for `commercial=true` and `modification=true`.
   - `PexelsProvider` / `PixabayProvider`: Access stock footage/photography via verified API endpoints.
3. **Audit Execution**: Run `auditAssetRights(metadata, plannedTransformations = true)`.
4. **Cache & Hash**: Copy or download to `assets/cache/<assetId>.<ext>`, verify SHA-256 hash.
5. **Ledger Commit**: Write the verified manifest into `assets/rights-ledger.json`.
6. **Credit Generation**: Compile attribution strings for the YouTube description and credits card.

## Observable Completion Criteria

- Asset status in `rights-ledger.json` is `APPROVED` or `APPROVED_WITH_ATTRIBUTION`.
- File exists in `assets/cache/` with matching computed SHA-256.
- YouTube description includes formatted attribution when required.
- Zero assets with `REJECTED` status are included in the render pipeline.
