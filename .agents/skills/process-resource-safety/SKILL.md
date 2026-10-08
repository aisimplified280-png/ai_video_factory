---
name: process-resource-safety
description: Audits ports, subprocesses, servers, FFmpeg, Node, Chromium, temp files, and concurrent production runs.
---
# Process & Resource Safety

Every production process must have explicit ownership and lifecycle.

Audit:
- ephemeral ports
- media servers
- subprocess PIDs/handles
- Node/npm/Chromium
- FFmpeg/ffprobe
- temporary directories
- concurrent runs
- cleanup on success and failure

Never terminate a process merely because it owns a known port. Track the process started by the current run and terminate only that owned process.

Detect port release/rebind races and leaked workers.
