---
name: documentation-contract-auditor
description: Keeps README, architecture docs, schemas, YAML, agent rules, and executable code synchronized.
---
# Documentation Contract Auditor

Audit:
- README.md
- docs/**
- .agents/rules.md
- .agents/skills/**
- pipeline_defs/**
- schemas/**
- runtime code
- tests

Flag contradictions such as:
- legacy create_short.py instructions when it is no longer canonical
- ffmpeg_pil described as active when Remotion is locked
- forbidden characters when topic-aware fictional mascots are now allowed
- old palette/grid rules
- claims that a renderer is unchanged when it has changed
- docs describing fields that the active renderer ignores

Every production rule needs one authoritative source.

Historical phase reports may remain as history, but must be clearly labeled historical and must not be presented as current instructions.
