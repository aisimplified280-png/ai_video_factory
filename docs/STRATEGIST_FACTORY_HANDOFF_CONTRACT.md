# Strategist-to-Factory Agent Handoff Contract

**Status:** Architecture proposal (Phase 0)  
**Producer:** YouTube Strategist / Creator Growth Agent  
**Consumer:** AI Video Factory

## 1. Responsibility boundary

The Strategist decides **what to make and why**. The Factory decides **how to produce it safely and well**.

The Factory must not independently invent factual claims, citations, audience metrics, or a publishing approval. It receives a structured brief, validates it, produces reviewable assets, and returns a manifest. The Strategist remains the control plane for human decisions and YouTube publishing.

## 2. Handoff artifact

The integration should exchange a versioned JSON artifact, not a free-form prompt copied between agents.

Suggested schema:

```json
{
  "schemaVersion": 1,
  "briefId": "brief-unique-id",
  "source": {
    "strategistRunId": "run-id",
    "opportunityId": "opportunity-id",
    "createdAt": "ISO-8601"
  },
  "goal": {
    "format": "short",
    "targetDurationSeconds": 35,
    "viewer": "AI-curious software learners",
    "viewerProblem": "A precise problem to solve",
    "desiredOutcome": "What the viewer should understand or do"
  },
  "topic": {
    "workingTitle": "Topic title",
    "angle": "Distinct editorial angle",
    "hookPromise": "Specific promise supported by evidence"
  },
  "research": {
    "claims": [
      {
        "claim": "Factual statement",
        "sourceUrl": "https://source.example",
        "sourceTitle": "Primary source title",
        "publishedAt": "ISO-8601 or null",
        "checkedAt": "ISO-8601"
      }
    ],
    "unknowns": [],
    "doNotClaim": []
  },
  "script": {
    "language": "simple international English",
    "voiceover": [],
    "onScreenText": [],
    "cta": "Subscribe to AI Simplified Lab"
  },
  "creativeDirection": {
    "directorFreedom": "adaptive",
    "thumbnailDirection": "mixed",
    "selectedStyleId": "chosen-style-id",
    "styleRationale": "Why this style serves this topic",
    "thumbnailConcepts": []
  },
  "constraints": {
    "faceless": true,
    "noIdentifiableRealPeople": true,
    "freeFirst": true,
    "assetRightsMustBeVerified": true,
    "noPublicPublishing": true
  }
}
```

This is a contract example, not a claim that the current CLI already accepts this schema.

## 3. Adaptive creative direction

Do not hard-code one visual template for every topic. The creative director should select from a versioned style library using:
- Topic category and abstraction level.
- Story purpose (news reveal, explanation, tutorial, comparison, myth-busting).
- Viewer promise and emotional tone.
- Evidence density and whether a real interface/demo is needed.
- Existing channel performance and recent creative fatigue, when sufficient data exists.
- Production cost, asset availability, rights status, and low-memory constraints.

Initial style families to evaluate:
1. Purple collage explainer — established AI Simplified Lab signature, not mandatory for every topic.
2. Editorial AI-news collage — sourced headlines, dates, evidence fragments and strong visual hierarchy.
3. Kinetic typography — short, high-clarity statements and fast concept reveals.
4. Technical architecture / data-flow — original diagrams for systems and algorithms.
5. Physical 3D metaphor — tangible object metaphors for abstract mechanisms.
6. Split-screen comparison — before/after, old/new, myth/fact, tool A/tool B.
7. Screen-led tutorial — authentic product UI, terminal or code demonstration.
8. Minimal cinematic concept — one dominant object and a restrained explanatory sequence.

The style library should store a style ID, intended use, layout grammar, motion grammar, typography/palette rules, asset policy, negative constraints, and examples. A selected style is a creative direction, not a fixed scene template; each scene must still be story-led and visually purposeful.

For thumbnails, use a **mixed direction**: choose among editorial collage, large symbolic object, technical visual, split comparison, typography-led, or product/UI proof. Do not force one recurring face or mascot. Never use an identifiable real person.

Do not label a style “best CTR on the internet” without comparable, current evidence. Treat external examples as hypotheses; use the channel's own impression and CTR results to evaluate styles over time, with sample-size caveats.

## 4. Factory processing stages

1. Validate schema, required fields, claim/source mapping, audience and constraints.
2. Select or confirm a style profile and explain the selection.
3. Expand the brief into a story-first storyboard with varied visual modes.
4. Scout assets; reject unknown or incompatible licenses and likeness risks.
5. Prefer original procedural diagrams for abstract technical concepts when stock assets add no explanatory value.
6. Generate voice, exact sentence timings, scene graph and synchronized sound.
7. Render in low-memory mode.
8. Run technical, rights, editorial and policy checks independently.
9. Produce contact sheet, final video, thumbnail concepts, credits and a machine-readable result manifest.
10. Return artifacts to Strategist for human editorial review.

## 5. Result manifest

The Factory should return:
- `briefId` and `factoryRunId`
- `status`: `completed`, `blocked`, or `failed`
- artifact paths and hashes
- selected style ID and rationale
- source/rights ledger and attribution text
- technical QA status and measured FFprobe/FFmpeg evidence
- rights QA status
- editorial review status
- YouTube policy review status
- publish approval status (must remain `false`)
- warnings, unresolved claims and required human decisions

A technically valid render is not automatically editorially approved or publishable. Preserve the existing fail-closed QA gate: missing/unknown checks block release.

## 6. State and safety invariants

- No publishing from the Factory.
- No hidden network calls or paid generation APIs unless explicitly enabled and budgeted.
- No real-person likenesses or identifiable faces.
- No asset enters a render unless its rights status is approved or it is an original procedural asset.
- Every factual claim must map to a source or be labelled as an opinion/illustration.
- No unsupported performance numbers, fake benchmark claims, or invented product UI.
- Every style choice and asset decision is recorded for reproducibility.
- The Factory cannot override the Strategist's human approval state.

## 7. Integration approach

Preferred local-first handoff:
1. Strategist exports a validated brief JSON to a known handoff directory.
2. Factory CLI accepts an explicit `--brief <path>` argument.
3. Factory validates and copies the immutable brief into its project folder.
4. Factory writes `factory-result.json` and a contact sheet alongside the export.
5. Strategist imports the result manifest and surfaces preview/review actions.

If the two applications run on different hosts, replace the shared folder with an authenticated, expiring artifact endpoint. Do not expose the local machine or accept arbitrary filesystem paths from the browser.

## 8. Acceptance criteria

- The same brief produces the same validated inputs and records the selected style profile.
- Unsupported claims or missing sources are surfaced before render.
- Style selection is adaptive and has a rationale; no single style is mandatory.
- Visual diversity lint and rights gate remain mandatory.
- Technical PASS, rights PASS, editorial review and publish approval remain separate.
- The returned manifest never sets `publishApproved: true`.
- No external service or provider is treated as available without a successful capability check.
