---
name: video-renderer
description: Previews or dry-runs Video Factory rendering and frame inspection.
---
# Instructions
When checking UI card animations or rendering progress:
- Run `python create_short.py --topic "Test Generation" --duration 12` to run a headless test frame inspection.
- Check the generated assets inside the `output/` subfolders or the root to verify dot grid, card alignments, and safe zones.
- If you need a quick visual frame to verify coordinates, utilize `python -c "from animation import *; ..."` to draw to a static image and inspect.
