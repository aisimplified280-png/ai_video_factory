# Dynamic Scene Engine — Technical Specification

**Branch:** stage1c/dynamic-scene-engine  
**Purpose:** Replace template-first composition decisions with scene-specific directed events.

## Data model

Each storyboard beat in a new dynamic project must carry a `sceneDirection` object. The renderer consumes this object to build the scene. The legacy `cardType` path is retained only for opening older projects; it must not be used for new production.

```json
{
  "sceneDirection": {
    "version": 1,
    "narrativePurpose": "What question this scene resolves",
    "visualIntent": "What the viewer should understand with audio muted",
    "visualMetaphor": "The concrete visual mechanism, if a metaphor helps",
    "composition": {
      "signature": "unique-scene-specific-id",
      "shotType": "wide | medium | macro | overhead | tracking | orbit | split-space | freeform",
      "camera": {
        "move": "dolly | orbit | pan | tilt | crane | tracking | locked-with-subject-motion | handheld-simulated | custom",
        "target": "the focal subject",
        "path": "described path and why it supports the idea"
      },
      "depthLayers": ["background environment", "interactive midground", "focal foreground"],
      "focalHierarchy": ["primary subject", "secondary reaction", "supporting context"],
      "negativeSpace": "where captions or labels can appear without hiding the action",
      "aspectSafeArea": "format-aware safe placement"
    },
    "visualEvent": {
      "setup": "initial state",
      "action": "what changes and why",
      "payoff": "resulting state / viewer insight"
    },
    "elements": [
      {
        "id": "unique-element-id",
        "role": "focal subject | environment | mechanism | data | context | label",
        "purpose": "what it explains or how it participates",
        "source": "procedural | generated | licensed | captured | original",
        "geometry": {"x": 0.5, "y": 0.5, "scale": 1},
        "appearance": {"form": "subject-specific visual description", "material": "optional", "palette": "scene-specific"},
        "motionRole": "how it moves or reacts"
      }
    ],
    "choreography": [
      {
        "trigger": {"type": "spoken-phrase | timecode | sound-event", "anchor": "exact phrase or time"},
        "target": "element-id",
        "event": "unique action",
        "duration": 1.2,
        "pathOrChange": "trajectory / transformation / value change",
        "causeAndEffect": {"reacts": ["element-id"], "reaction": "visible response"},
        "soundCue": {"type": "whoosh | impact | tick | reveal | texture | deliberate-silence", "purpose": "why it is heard"}
      }
    ],
    "audio": {
      "voiceSegment": "exact narration for this scene",
      "ambience": "scene-specific bed or deliberate silence",
      "musicCue": "emotional role and mix instruction",
      "ducking": "music and ambience under dialogue"
    },
    "captions": {
      "mode": "word-synced | phrase-synced",
      "emphasis": ["words that deserve emphasis"],
      "anchor": "safe position relative to the action",
      "treatment": "scene-specific caption treatment"
    },
    "transition": {
      "type": "match-cut | morph | camera-continuation | sound-bridge | hard-cut | custom",
      "continuityReason": "why it links the ideas"
    }
  }
}
```

## Validation rules

A dynamic project must fail the creative gate when:

- `sceneDirection` is missing.
- `composition.signature` repeats elsewhere without an explicit continuity reason.
- visual intent or narrative purpose is empty or generic.
- focal hierarchy or visual event is missing.
- no meaningful motion/choreography is present (except an explicit, story-motivated stillness beat with its own camera/sound direction).
- an element is missing its purpose or motion role.
- a generated/licensed/captured asset has no provenance and rights record.
- a sound cue has no purpose, or a scene uses silence without saying why.
- voice segment is missing or caption timing does not map to speech.
- the scene is primarily a text block/card or slide.

## Rendering architecture

1. Parse the project manifest and validate sceneDirection before any provider call.
2. Build each scene as a scene-specific composition from its elements, geometry, visual event and camera plan; do not select a card layout.
3. Bind every choreography event to transcript timing or an explicit timecode.
4. Render motion as object-level transformations, not whole-slide pans.
5. Mix scene audio (voice, score, ambience and SFX) on separate tracks; apply ducking and loudness controls.
6. Generate captions from the same transcript timing used by motion triggers.
7. Use motivated transitions and record continuity metadata.
8. Run creative lint and media QA separately. Both must pass.
9. Inspect entrance, action and payoff frames for every scene and listen to the final mix.

## Rollout

- Legacy projects can continue to render through their existing `cardType` path.
- New projects must declare `productionMode: "dynamic"` and use the sceneDirection schema.
- Do not silently fall back from dynamic mode to a card or slide if validation fails; stop and report the missing direction.
- The first dynamic-engine proof should be an explanatory Short with at least four genuinely different scene compositions, not four variants of one card.
