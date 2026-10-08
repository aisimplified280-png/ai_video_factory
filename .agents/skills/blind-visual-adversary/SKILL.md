---
name: blind-visual-adversary
description: Attempts to fool visual QA with correct metadata, misleading semantics, repetition, fake motion, and fake depth.
---
# Blind Visual Adversary

Construct adversarial test cases where declared metadata is correct but pixels are wrong.

Minimum cases:
- expected robot, render generic AI grid
- expected biotech, render cloud architecture
- expected action, render a static subject
- correct z-index metadata, flattened visual
- correct transition metadata, hard cut
- different scene metadata, identical composition
- correct caption timing, caption obscures focal subject
- different colors/text, same structural template
- character metadata says interacting, character visibly idle

The visual judge must fail these cases.

Also construct inverse cases:
- metadata is imperfect but pixels clearly communicate the intended scene
- judge should diagnose metadata mismatch without falsely claiming visual failure

Never weaken production gates just to make adversarial tests pass.
