"""Unified LLM Client for Autonomous Video Factory (Phase 11, 12, 15).

Provides resilient JSON structured generation with multi-provider failover:
1. Google Gemini (gemini-2.5-flash, gemini-flash-latest)
2. OpenRouter (nvidia/nemotron-3.5-lightning:free, meta-llama/llama-3.3-70b-instruct:free)
3. OpenAI (gpt-4o-mini)

Returns parsed Python dict if any provider succeeds, or None if all fail.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from typing import Any, Optional

try:
    import dotenv
    dotenv.load_dotenv()
except Exception:
    pass

import requests

_LLM_CACHE: dict[str, dict] = {}


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
            resp = requests.post(url, json=payload, timeout=6)
            if resp.status_code == 429:
                # Quota exceeded; fail fast to next provider
                break
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


def call_llm_json(prompt: str) -> Optional[dict]:
    """Execute LLM call across active providers with in-memory caching and fail-fast timeouts."""
    cache_key = hashlib.md5(prompt.encode("utf-8")).hexdigest()
    if cache_key in _LLM_CACHE:
        return _LLM_CACHE[cache_key]

    # 1. Try Gemini
    res = _call_gemini_json(prompt)
    if res and isinstance(res, dict):
        _LLM_CACHE[cache_key] = res
        return res

    # 2. Try OpenRouter (reliable free frontier models)
    res = _call_openrouter_json(prompt)
    if res and isinstance(res, dict):
        _LLM_CACHE[cache_key] = res
        return res

    # 3. Try OpenAI
    res = _call_openai_json(prompt)
    if res and isinstance(res, dict):
        _LLM_CACHE[cache_key] = res
        return res

    return None
