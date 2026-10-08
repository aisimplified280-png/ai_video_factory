---
name: dependency-security-auditor
description: Audits project dependencies, environment variables, secrets handling, subprocess command construction, and external URLs for security vulnerabilities.
---

# dependency-security-auditor

## Purpose
Monitors package manifests, environment configurations, and external calls to prevent secret leakage, untrusted code execution, shell injection, or supply-chain degradation.

## Trigger Conditions
- Triggered whenever modifying `requirements.txt`, `package.json`, or `.env`.
- Triggered whenever adding new external API calls, HTTP downloads, or LLM prompt integrations.
- Triggered during pre-commit and release audits.

## Exact Inspection Targets
1. **Node Dependencies**: `remotion-composer/package.json` vs `package-lock.json`.
2. **Python Dependencies**: `requirements.txt`.
3. **Environment & Secrets**: `.env`, `envfile.py`, API key references (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`).
4. **Subprocess Calls**: Ensuring `shell=False` is used everywhere; avoiding string interpolation into command lines.
5. **Colab / Worker**: `colab/remotion_worker.ipynb` public tunnels and secret handling.

## Commands / Tools to Use
- `grep_search`: Look for `shell=True`, hardcoded keys, or plain-text secrets.
- `npm audit --prefix remotion-composer`: Checks Node vulnerability advisories.

## Failure Conditions
- Any secret or API key is committed into source files or test fixtures.
- Any subprocess invocation uses `shell=True` with user or external input strings.
- Package versions diverge between manifest and lockfile.

## Evidence Requirements
- Zero API keys found in tracked git files (`git grep -i "key="`).
- Verified use of structured argv lists across all `subprocess.run` and `subprocess.Popen` calls.

## Output Format
```markdown
### Dependency & Security Audit Report
- Secrets Exposure Check: Clean (Zero tracked keys) -> PASS
- Subprocess Shell Injection Check: Clean (All shell=False argv arrays) -> PASS
- Node Dependencies: Validated against package-lock.json -> PASS
- Python Runtime Dependencies: Consistent -> PASS
```

## Stop Conditions
If any secret leakage or shell injection risk is found, halt immediately and purge/sanitize before proceeding.

## Interaction with Other Skills
- Complements **python-static-auditor** and **process-resource-safety**.
- Protects the execution environment of **self-healing-engineer**.
