"""Unified LLM Client for Autonomous Video Factory (Phase 11, 12, 15).

Provides resilient JSON structured generation with multi-provider failover:
1. Local Ollama (first — free, offline, no quota)
2. Google Gemini (gemini-2.5-flash, gemini-flash-latest)
3. OpenRouter (nvidia/nemotron-3.5-lightning:free, meta-llama/llama-3.3-70b-instruct:free)
4. OpenAI (gpt-4o-mini)

Returns parsed Python dict if any provider succeeds, or None if all fail.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any, Optional

try:
    import dotenv
    dotenv.load_dotenv()
except Exception:
    pass

import requests

_LLM_CACHE: dict[str, dict] = {}
# Persistent memoization: identical prompts (same topic, rules, research context) reuse the
# same synthesis result across processes, so end-to-end runs are reproducible and repeat
# calls never re-pay for the same generation. Delete this file to force fresh synthesis.
_LLM_CACHE_PATH = Path(__file__).resolve().with_name(".llm_cache.json")
_LLM_CACHE_LOADED = False


def _llm_cache_load() -> None:
    global _LLM_CACHE_LOADED
    if _LLM_CACHE_LOADED:
        return
    _LLM_CACHE_LOADED = True
    try:
        if _LLM_CACHE_PATH.is_file():
            data = json.loads(_LLM_CACHE_PATH.read_text("utf-8"))
            if isinstance(data, dict):
                _LLM_CACHE.update({k: v for k, v in data.items() if isinstance(v, dict)})
    except Exception:
        pass


def _llm_cache_store(key: str, value: dict) -> None:
    _LLM_CACHE[key] = value
    try:
        _LLM_CACHE_PATH.write_text(json.dumps(_LLM_CACHE, ensure_ascii=False), "utf-8")
    except Exception:
        pass


def bust_llm_cache(prompt: str) -> None:
    """Drop one prompt's cached response (memory + disk).

    Used when a cached sample fails the pipeline's quality gates: the next
    call for the same prompt must fetch a fresh generation instead of
    re-serving the rejected sample.
    """
    _llm_cache_load()
    cache_key = hashlib.md5(prompt.encode("utf-8")).hexdigest()
    _LLM_CACHE.pop(cache_key, None)
    try:
        if _LLM_CACHE_PATH.is_file():
            data = json.loads(_LLM_CACHE_PATH.read_text("utf-8"))
            if isinstance(data, dict) and cache_key in data:
                data.pop(cache_key, None)
                _LLM_CACHE_PATH.write_text(json.dumps(data, ensure_ascii=False), "utf-8")
    except Exception:
        pass


def _strip_markdown_json(text: str) -> str:
    """Strip markdown code blocks or wrapping text to isolate valid JSON."""
    text = text.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
    if match:
        text = match.group(1).strip()
    else:
        # If wrapped with plain braces somewhere inside text
        first_brace = text.find("{")
        last_brace = text.rfind("}")
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            text = text[first_brace : last_brace + 1]
    return text


def _call_gemini_json(prompt: str) -> Optional[dict]:
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key:
        return None

    models = ["gemini-2.5-flash", "gemini-flash-latest"]
    for model in models:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "response_mime_type": "application/json",
                    "temperature": 0.4,
                },
            }
            resp = requests.post(url, json=payload, timeout=15)
            if resp.status_code == 429:
                # Free-tier quota is per MODEL (see quotaDimensions in the error) — try the
                # next model in this provider before falling through to the next provider.
                continue
            if resp.status_code != 200:
                continue
            data = resp.json()
            candidates = data.get("candidates", [])
            if candidates:
                raw_text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                if raw_text:
                    cleaned = _strip_markdown_json(raw_text)
                    return json.loads(cleaned)
        except Exception:
            continue
    return None


def _call_openrouter_json(prompt: str) -> Optional[dict]:
    key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not key:
        return None

    # Working fast free models on OpenRouter
    models = [
        "liquid/lfm-2.5-2.6b:free",
        "apodex/apodex-1.1-mini:free",
        "nvidia/nemotron-3.5-lightning:free",
        "nvidia/nemotron-3-ultra-550b-a55b:free",
    ]
    for model in models:
        try:
            url = "https://openrouter.ai/api/v1/chat/completions"
            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a professional video scriptwriter and YouTube packaging strategist. You must respond with valid JSON only. Do not output markdown explanation or conversational filler.",
                    },
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.4,
            }
            resp = requests.post(
                url,
                headers={
                    "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=10,
            )
            if resp.status_code == 200:
                data = resp.json()
                choices = data.get("choices", [])
                if choices:
                    raw_text = choices[0].get("message", {}).get("content", "")
                    if raw_text:
                        cleaned = _strip_markdown_json(raw_text)
                        return json.loads(cleaned)
        except Exception:
            continue
    return None


def _call_openai_json(prompt: str) -> Optional[dict]:
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key:
        return None

    try:
        url = "https://api.openai.com/v1/chat/completions"
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "You are a professional video scriptwriter. Reply with valid JSON only."},
                {"role": "user", "content": prompt},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.4,
        }
        resp = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=8,
        )
        if resp.status_code == 200:
            data = resp.json()
            choices = data.get("choices", [])
            if choices:
                raw_text = choices[0].get("message", {}).get("content", "")
                if raw_text:
                    return json.loads(_strip_markdown_json(raw_text))
    except Exception:
        pass
    return None


def _call_ollama_json(prompt: str) -> Optional[dict]:
    """Local Ollama model — free, unlimited, no quota, works offline.

    Tried first so narration synthesis always has a working path even when every
    cloud provider is rate-limited or out of credits (§25 end-to-end validation
    must not silently degrade to the generic fallback template).
    """
    model = _ollama_model()
    if not model:
        return None

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "format": "json",
        "stream": False,
        # Moderate temperature: low values make small models echo the schema example
        # instead of writing content; 0.4 follows the editorial rules with real prose.
        "options": {"temperature": 0.4},
    }
    try:
        resp = requests.post("http://localhost:11434/api/chat", json=payload, timeout=120)
        if resp.status_code == 200:
            raw_text = resp.json().get("message", {}).get("content", "")
            if raw_text:
                cleaned = _strip_markdown_json(raw_text)
                parsed = json.loads(cleaned)
                if isinstance(parsed, dict):
                    return parsed
    except Exception:
        pass
    return None


_OLLAMA_MODEL: Optional[str] = None


def _ollama_model() -> Optional[str]:
    """Resolve the local model once: OLLAMA_MODEL env, else whatever ollama has pulled."""
    global _OLLAMA_MODEL
    if os.getenv("AI_FACTORY_DISABLE_LOCAL_LLM", "").strip().lower() in ("1", "true", "yes"):
        return None
    if _OLLAMA_MODEL is not None:
        return _OLLAMA_MODEL or None
    env_model = os.getenv("OLLAMA_MODEL", "").strip()
    if env_model:
        _OLLAMA_MODEL = env_model
        return env_model
    try:
        resp = requests.get("http://localhost:11434/api/tags", timeout=3)
        models = resp.json().get("models", [])
        _OLLAMA_MODEL = str(models[0].get("name", "")) if models else ""
    except Exception:
        _OLLAMA_MODEL = ""
    return _OLLAMA_MODEL or None


def call_llm_json(prompt: str) -> Optional[dict]:
    """Execute LLM call across active providers with in-memory caching and fail-fast timeouts."""
    _llm_cache_load()
    cache_key = hashlib.md5(prompt.encode("utf-8")).hexdigest()
    if cache_key in _LLM_CACHE:
        return _LLM_CACHE[cache_key]

    # 1. Try local Ollama (no quota, no network dependency)
    res = _call_ollama_json(prompt)
    if res and isinstance(res, dict):
        _llm_cache_store(cache_key, res)
        return res

    # 2. Try Gemini
    res = _call_gemini_json(prompt)
    if res and isinstance(res, dict):
        _llm_cache_store(cache_key, res)
        return res

    # 3. Try OpenRouter (reliable free frontier models)
    res = _call_openrouter_json(prompt)
    if res and isinstance(res, dict):
        _llm_cache_store(cache_key, res)
        return res

    # 4. Try OpenAI
    res = _call_openai_json(prompt)
    if res and isinstance(res, dict):
        _llm_cache_store(cache_key, res)
        return res

    return None
