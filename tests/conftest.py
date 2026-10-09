"""Shared pytest configuration.

Unit tests must never depend on a live local model: with Ollama running, the
scriptwriter would otherwise synthesize real narration inside tests, making
them slow and nondeterministic. Cloud providers still fail fast (no keys).
"""
import os

os.environ.setdefault("AI_FACTORY_DISABLE_LOCAL_LLM", "1")
