---
name: python-static-auditor
description: Performs rigorous static analysis on Python files, catching missing imports, NameErrors, swallowed exceptions, and unsafe subprocess calls before runtime.
---

# python-static-auditor

## Purpose
Prevent runtime crashes caused by static coding bugs such as missing imports, undefined variables (`NameError`), shadowed names, unhandled exceptions, and unsafe subprocess invocations.

## Trigger Conditions
- Triggered before committing ANY Python code change.
- Triggered whenever a new import or environment variable access is introduced.
- Triggered on PR review or release gate verification.

## Exact Inspection Targets
1. **Module Imports**: All standard library imports (`os`, `sys`, `json`, `re`, `shutil`, `subprocess`, `pathlib`) must be present at file top.
2. **Variable Bindings**: No unbound references or misspelled local/global variables.
3. **Exception Handling**: No bare `except:` blocks or exception swallowing that hides production crashes.
4. **Subprocess Calls**: Explicit argument lists (`argv`), no unsafe shell strings (`shell=True`), timeout parameters present, owned PID tracking.
5. **Path Manipulation**: Strict `Path` object usage, cross-platform separators (no hardcoded `/` or `\` in strings), no outside-workspace traversal.

## Commands / Tools to Use
- `python -m compileall -q <target_file>`: Validates Python syntax and bytecode compilation.
- `python -c "import <module>"`: Ensures module imports cleanly without unresolved global names.
- AST inspection / static check scripts.

## Failure Conditions
- Any Python file fails bytecode compilation.
- Any reference to `os`, `sys`, `re`, or other modules occurs without an explicit import.
- A production exception is caught and silently dropped without logging or failure propagation.

## Evidence Requirements
- Terminal execution output showing `python -m compileall` exited with code 0.
- Clean import verification output (`python -c "import ..."`).

## Output Format
```markdown
### Python Static Audit: [Target Files]
- Compilation Status: PASS | FAIL
- Missing Imports: None | [List]
- NameError Risks: None | [List]
- Exception Swallowing: None | [Line numbers]
- Subprocess Safety: Compliant | Violations detected
```

## Stop Conditions
If any syntax, missing import, or compile error is found, halt and fix the error before running integration tests or rendering.

## Interaction with Other Skills
- Invoked by **self-healing-engineer** immediately after editing any Python file.
- Complements **process-resource-safety** for subprocess checks.
