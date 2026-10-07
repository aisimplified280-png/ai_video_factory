"""Minimal .env loader (stdlib only, no dependencies).

Reads KEY=VALUE lines from the project .env file and injects any keys
that are not already set in the real environment (real env always wins).
Import this FIRST in every entry point (app.py, create_short.py, models.py).
"""
from __future__ import annotations

import os
from pathlib import Path


def load_dotenv(path: str | Path | None = None) -> bool:
    p = Path(path) if path else Path(__file__).resolve().parent / ".env"
    if not p.is_file():
        return False
    try:
        text = p.read_text(encoding="utf-8")
    except OSError:
        return False
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        if key and key not in os.environ:
            os.environ[key] = value
    return True
