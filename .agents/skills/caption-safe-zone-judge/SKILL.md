---
name: caption-safe-zone-judge
description: Verifies captions and CTA remain readable without covering important visual content.
---
# Caption & Safe-Zone Judge

Check representative frames across every caption interval.

Verify:
- captions stay inside the configured safe region
- CTA does not collide with captions
- captions do not cover the main subject
- character action remains visible
- line wrapping is readable on a mobile frame
- karaoke highlighting does not create visual jitter
- top/bottom composition remains balanced

Use actual encoded frames. Do not accept declared y-coordinates as evidence.
