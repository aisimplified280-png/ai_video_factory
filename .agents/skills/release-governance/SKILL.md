---
name: release-governance
description: "Audit truthfulness, claim integrity, license provenance, and technical standards to determine whether a YouTube Short is eligible for release or blocked."
---

# Release Governance & Truthful Quality Gate

Quality gates must report reality, not an optimistic pass. An unmeasured check must be marked `UNKNOWN` or `UNASSESSED`, not `PASS`.

## Status Categories

- **`PASS`**: Measured, tested, and satisfies strict technical / editorial requirements.
- **`FAIL`**: Measured and violates standards (e.g., missing streams, decode errors, black frames).
- **`REVIEW_REQUIRED`**: Flags third-party likeness, trademarks, or complex terms requiring human review.
- **`UNKNOWN` / `UNASSESSED`**: Not automatically verifiable (e.g., subjective YouTube policy compliance).

## Release Eligibility Rules

A short is marked `releaseEligible = true` only if:
1. Media stream integrity is `PASS` (1080x1920, 30fps, valid AAC).
2. Decode error count is 0.
3. Black frame detection is `PASS`.
4. Script and audio timing sync is `PASS`.
5. Offline asset vendoring is `PASS`.
6. Rights audit is `PASS` or `APPROVED_WITH_ATTRIBUTION`.

If any mandatory check fails or remains in `REVIEW_REQUIRED`, `releaseEligible` MUST be `false` and blockers must be listed explicitly in `youtube-package.json`.

## Observable Completion Criteria

- `youtube-package.json` contains a segregated `verificationReport`.
- YouTube policy review is explicitly listed as `UNASSESSED (Requires Human / Creator Review)`.
- Release eligibility accurately reflects all blockers.
