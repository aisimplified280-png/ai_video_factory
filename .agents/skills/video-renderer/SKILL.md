---
name: video-renderer
description: Previews or dry-runs Video Factory rendering and frame inspection.
---
# Instructions
When checking Video Factory rendering progress or frame inspection:
- Run `python scripts/factory.py produce --topic "Test Generation"` or `python scripts/run_local_production.py --production <id> --validate --render --qa` for end-to-end Remotion renders.
- Inspect rendered MP4 and frame samples in `projects/<id>/qa/` or `output/<slug>/`.
- Validate technical and visual QA reports in `output/<slug>/visual_language_qa_report.json` and `claim_visual_qa_report.json`.
