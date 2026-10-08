---
name: process-resource-safety
description: Enforces safe process management, OS-allocated ephemeral ports, owned Popen lifecycle termination, and forbids broad netstat/taskkill usage.
---

# process-resource-safety

## Purpose
Enforces safe and reliable process lifecycle management across Windows and POSIX operating systems. Prohibits global destructive commands like `taskkill /F /IM node.exe` or `netstat` scraping that could kill unrelated developer tools.

## Trigger Conditions
- Triggered whenever launching background processes, media servers, or rendering workers.
- Triggered whenever managing port bindings or inter-process communication.
- Triggered during test teardown and cleanup routines.

## Exact Inspection Targets
1. **Port Allocation**: `find_free_ephemeral_port()` in `composition/remotion/runtime.py`.
2. **Process Spawning**: `subprocess.Popen` calls, `server_process` references.
3. **Lifecycle Cleanup**: `try ... finally` blocks with `process.terminate()` and `process.wait(timeout=2)`.
4. **Shell Invocations**: Zero `taskkill /F`, zero `kill -9`, zero blind PID termination.

## Commands / Tools to Use
- `grep_search`: Search for `taskkill`, `netstat`, `pkill`, `killall`.
- `pytest tests/test_safe_port_management.py -v`: Tests ephemeral allocation and owned termination.

## Failure Conditions
- Any code attempts to run `taskkill` or kill processes by binary name.
- Any server binds to a hardcoded port that could conflict with existing system listeners.
- Any child process is launched without guaranteed termination in a `finally` block or context manager.

## Evidence Requirements
- Passing tests in `test_safe_port_management.py`.
- Verified absence of broad process-killing commands in the entire codebase.

## Output Format
```markdown
### Process Resource Safety Audit
- Port Allocation Strategy: OS-assigned Ephemeral (bind to 0) -> VERIFIED
- Owned Subprocess Lifecycle: Tracked Popen with terminate()/wait() -> VERIFIED
- Destructive Process Commands: NONE DETECTED (Zero taskkill/pkill) -> VERIFIED
- Teardown Reliability: Guaranteed in finally blocks -> PASS
```

## Stop Conditions
If any code contains broad system process termination commands, fail the safety audit and refactor to owned process handles immediately.

## Interaction with Other Skills
- Enforces runtime safety for **typescript-remotion-auditor** and **render-truth-auditor**.
- Regulates background tasks spawned by **self-healing-engineer**.
