"""Model discovery + automatic ranking across OpenAI / Gemini / Ollama.

`best_model_order()` returns [(provider, model), ...] ranked best-first:
  1. Explicit user pins (OPENAI_MODELS / GEMINI_MODELS / OLLAMA_MODELS) win.
  2. Otherwise live discovery (provider model-list APIs + Ollama tags),
     each candidate probed with a tiny JSON task and ranked by
     valid-JSON success first, latency second, cheap/fast tier third.
  3. Results cached 24h in .model_rank.json so runs stay instant.

Run `python models.py` to see (and refresh) the ranking table.
"""
from __future__ import annotations

import envfile
envfile.load_dotenv()

import json
import os
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CACHE = ROOT / ".model_rank.json"
CACHE_TTL = 24 * 3600
PROBE_TIMEOUT = 25
MAX_CANDIDATES = 6


def _get_json(url: str, headers: dict | None = None, timeout: int = 20):
    req = urllib.request.Request(url, headers=headers or {}, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.load(resp)


def _post_json(url: str, body: dict, headers: dict | None = None, timeout: int = 25):
    data = json.dumps(body).encode()
    h = {"Content-Type": "application/json"}
    h.update(headers or {})
    req = urllib.request.Request(url, data, headers=h, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.load(resp)


# ── Discovery ────────────────────────────────────────────────────────────
def discover_openai() -> list[str]:
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        return []
    data = _get_json("https://api.openai.com/v1/models",
                     {"Authorization": f"Bearer {key}"})
    out = []
    for m in data.get("data", []):
        mid = m.get("id", "")
        if "gpt" not in mid:
            continue
        if any(bad in mid for bad in ("realtime", "audio", "image", "embedding",
                                      "tts", "whisper", "transcribe", "moderation")):
            continue
        out.append(mid)
    return sorted(set(out), key=_openai_pref)


def _openai_pref(mid: str) -> tuple:
    m = mid.lower()
    tier = 0 if "mini" in m else (1 if ("4o" in m or "4.1" in m) else 2)
    return (tier, mid)


def discover_gemini() -> list[str]:
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        return []
    data = _get_json(f"https://generativelanguage.googleapis.com/v1beta/models?key={key}")
    out = []
    for m in data.get("models", []):
        methods = m.get("supportedGenerationMethods", [])
        if "generateContent" not in methods:
            continue
        name = m.get("name", "").split("/")[-1]
        if not name or "embedding" in name or "aqa" in name:
            continue
        out.append(name)
    return sorted(set(out), key=_gemini_pref)


def _gemini_pref(name: str) -> tuple:
    n = name.lower()
    # Preview / image / TTS / search variants are unreliable for JSON work —
    # probe stable text models first so good ones never get cut off by the cap.
    penalty = 10 if any(bad in n for bad in ("preview", "image", "tts", "search", "aqa")) else 0
    tier = 0 if "flash" in n else (1 if "pro" in n else 2)
    stable = 0 if any(s in n for s in ("2.0-flash", "1.5-flash", "2.5-flash", "3.8-flash")) else 1
    return (penalty, tier, stable, name)


def discover_openrouter() -> list[str]:
    key = os.getenv("OPENROUTER_API_KEY")
    if not key:
        return []
    data = _get_json("https://openrouter.ai/api/v1/models",
                     {"Authorization": f"Bearer {key}"})
    free, cheap = [], []
    for m in data.get("data", []):
        mid = m.get("id", "")
        if not mid or "moderat" in mid:
            continue
        if mid.endswith(":free"):
            free.append(mid)
            continue
        ml = mid.lower()
        if any(keep in ml for keep in ("deepseek-chat", "qwen-2.5", "qwen2.5", "llama-3",
                                       "gemma-3", "mistral-small", "haiku", "gpt-4o-mini",
                                       "gemini-2.0-flash", "phi-4")):
            try:
                price = float((m.get("pricing") or {}).get("prompt") or 9)
            except (TypeError, ValueError):
                price = 9
            if price < 1.0:  # under $1/M prompt tokens
                cheap.append((price, mid))
    cheap.sort()
    return (sorted(set(free)) + [mid for _, mid in cheap])[:MAX_CANDIDATES * 2]


def discover_ollama() -> list[str]:
    host = os.getenv("OLLAMA_HOST")
    if not host:
        return []
    data = _get_json(f"{host.rstrip('/')}/api/tags", timeout=10)
    return [m.get("name", "") for m in data.get("models", []) if m.get("name")]


# ── Probe: tiny JSON task, measures working-ness + latency ───────────────
_PROBE_INSTRUCTION = 'Reply with JSON only: {"ok": true}'


def _probe_openai(model: str) -> tuple[bool, float, str]:
    key = os.getenv("OPENAI_API_KEY", "")
    t = time.time()
    try:
        payload = _post_json(
            "https://api.openai.com/v1/responses",
            {"model": model, "input": _PROBE_INSTRUCTION, "store": False,
             "text": {"format": {"type": "json_object"}}, "max_output_tokens": 30},
            {"Authorization": f"Bearer {key}"}, timeout=PROBE_TIMEOUT)
        text = payload.get("output_text", "") or "".join(
            p.get("text", "") for i in payload.get("output", [])
            for p in i.get("content", []) if p.get("type") == "output_text")
        ok = json.loads(text.strip()).get("ok") is True
        return ok, time.time() - t, f"model {model}"
    except Exception as exc:
        return False, time.time() - t, f"{type(exc).__name__}: {str(exc)[:120]}"


def _probe_gemini(model: str) -> tuple[bool, float, str]:
    key = os.getenv("GEMINI_API_KEY", "")
    t = time.time()
    try:
        payload = _post_json(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            {"contents": [{"parts": [{"text": _PROBE_INSTRUCTION}]}],
             "generationConfig": {"response_mime_type": "application/json", "temperature": 0.0,
                                  "maxOutputTokens": 60}},
            {"x-goog-api-key": key}, timeout=PROBE_TIMEOUT)
        candidates = payload.get("candidates", [])
        if not candidates:
            return False, time.time() - t, "No candidates returned"
        parts = candidates[0].get("content", {}).get("parts", [])
        text_parts = [p.get("text", "") for p in parts if "text" in p and not p.get("thought", False)]
        if not text_parts:
            text_parts = [p.get("text", "") for p in parts if "text" in p]
        text = "".join(text_parts)
        ok = json.loads(text.strip()).get("ok") is True
        return ok, time.time() - t, f"model {model}"
    except Exception as exc:
        return False, time.time() - t, f"{type(exc).__name__}: {str(exc)[:120]}"


def _probe_openrouter(model: str) -> tuple[bool, float, str]:
    key = os.getenv("OPENROUTER_API_KEY", "")
    t = time.time()
    try:
        payload = _post_json(
            "https://openrouter.ai/api/v1/chat/completions",
            {"model": model,
             "messages": [{"role": "user", "content": _PROBE_INSTRUCTION}],
             "response_format": {"type": "json_object"}, "max_tokens": 30,
             "temperature": 0.0},
            {"Authorization": f"Bearer {key}",
             "HTTP-Referer": "http://localhost:5000",
             "X-Title": "AI SIMPLIFIED LAB Video Factory"},
            timeout=PROBE_TIMEOUT)
        text = payload["choices"][0]["message"]["content"]
        ok = json.loads(text.strip()).get("ok") is True
        return ok, time.time() - t, f"model {model}"
    except Exception as exc:
        return False, time.time() - t, f"{type(exc).__name__}: {str(exc)[:120]}"


def _probe_ollama(model: str) -> tuple[bool, float, str]:
    host = os.getenv("OLLAMA_HOST", "")
    t = time.time()
    try:
        payload = _post_json(
            f"{host.rstrip('/')}/api/generate",
            {"model": model, "prompt": _PROBE_INSTRUCTION, "stream": False,
             "format": "json", "options": {"num_predict": 30}},
            timeout=PROBE_TIMEOUT)
        ok = json.loads(payload.get("response", "").strip()).get("ok") is True
        return ok, time.time() - t, f"model {model}"
    except Exception as exc:
        return False, time.time() - t, f"{type(exc).__name__}: {str(exc)[:120]}"


PROBES = {"openai": _probe_openai, "gemini": _probe_gemini,
          "openrouter": _probe_openrouter, "ollama": _probe_ollama}
DISCOVER = {"openai": discover_openai, "gemini": discover_gemini,
            "openrouter": discover_openrouter, "ollama": discover_ollama}
ENV_PIN = {"openai": "OPENAI_MODELS", "gemini": "GEMINI_MODELS",
           "openrouter": "OPENROUTER_MODELS", "ollama": "OLLAMA_MODELS"}
PROVIDERS = ("openai", "gemini", "openrouter", "ollama")


def _pinned(provider: str) -> list[str]:
    raw = os.getenv(ENV_PIN[provider], "")
    return [x.strip() for x in raw.split(",") if x.strip()]


def rank_models(force: bool = False, verbose: bool = True) -> list[dict]:
    """Probe every candidate and return ranked rows.

    Row: {provider, model, ok, ms, detail}. Working models first by latency.
    User-pinned models are probed too so pins stay verified, not blind.
    """
    rows: list[dict] = []
    for provider in PROVIDERS:
        pinned = _pinned(provider)
        if pinned:
            candidates = pinned[:MAX_CANDIDATES]
            source = "pin"
        else:
            try:
                candidates = DISCOVER[provider]()[:MAX_CANDIDATES]
            except Exception as exc:
                if verbose:
                    print(f"[{provider}] discovery failed: {exc}")
                continue
            source = "discovered"
        if not candidates and verbose:
            print(f"[{provider}] no candidates ({'not configured' if source == 'discovered' else 'empty pin'})")
        for model in candidates:
            if verbose:
                print(f"[{provider}] probing {model} ({source})...", flush=True)
            try:
                ok, secs, detail = PROBES[provider](model)
            except Exception as exc:  # never let one probe kill ranking
                ok, secs, detail = False, PROBE_TIMEOUT, f"{type(exc).__name__}"
            rows.append({"provider": provider, "model": model, "ok": ok,
                         "ms": int(secs * 1000), "detail": detail, "source": source})
            if verbose:
                print(f"[{provider}] {model}: {'OK' if ok else 'FAIL'} in {secs:.1f}s - {_safe(detail)}")
    rows.sort(key=lambda r: (not r["ok"], r["ms"]))
    try:
        CACHE.write_text(json.dumps({"ts": time.time(), "rows": rows}, indent=2), encoding="utf-8")
    except OSError:
        pass
    return rows


def load_cache() -> list[dict]:
    try:
        data = json.loads(CACHE.read_text(encoding="utf-8"))
        if time.time() - data.get("ts", 0) < CACHE_TTL:
            return data.get("rows", [])
    except (OSError, ValueError):
        pass
    return []


def best_model_order(verbose: bool = False) -> list[tuple[str, str]]:
    """Ranked (provider, model) pairs, working models first.

    Never raises — returns [] when nothing is configured, letting the
    caller fall back to built-in defaults.
    """
    rows = load_cache()
    if not rows:
        try:
            rows = rank_models(verbose=verbose)
        except Exception:
            return []
    return [(r["provider"], r["model"]) for r in rows if r["ok"]]


def best_label() -> str:
    """One-line label for the UI. Cache file only — never probes (request-safe)."""
    rows = load_cache()
    ok = [r for r in rows if r["ok"]]
    if not ok:
        return "unranked — local template"
    return f"{ok[0]['provider']}/{ok[0]['model']} (auto-ranked)"


def _safe(text: str) -> str:
    return str(text).encode("ascii", errors="replace").decode()


def _clean_json_str(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        import re
        t = re.sub(r"^```(?:json)?\s*", "", t)
        t = re.sub(r"\s*```$", "", t)
    return t.strip()


def call_llm_json(
    prompt: str,
    system: str | None = None,
    provider: str | None = None,
    model: str | None = None,
    timeout: int = 60,
) -> tuple[dict, str, str, int]:
    """Call an LLM provider and parse the response as JSON.

    Returns:
        (parsed_dict, provider_name, model_name, estimated_tokens)

    Raises:
        RuntimeError if all candidates fail or no providers are configured.
    """
    candidates: list[tuple[str, str]] = []
    if provider and model:
        candidates.append((provider, model))
    elif provider:
        ranked = [m for (p, m) in best_model_order() if p == provider]
        if ranked:
            for m in ranked:
                candidates.append((provider, m))
        else:
            pinned = _pinned(provider)
            for m in (pinned or ["default"]):
                candidates.append((provider, m))
    else:
        candidates = best_model_order()

    if not candidates:
        # Fallback to defaults if keys are present
        if os.getenv("GEMINI_API_KEY"):
            candidates.append(("gemini", "gemini-2.0-flash"))
        if os.getenv("OPENAI_API_KEY"):
            candidates.append(("openai", "gpt-4o-mini"))
        if os.getenv("OPENROUTER_API_KEY"):
            candidates.append(("openrouter", "google/gemini-2.0-flash-001"))
        if os.getenv("OLLAMA_HOST"):
            candidates.append(("ollama", "qwen2.5:0.5b"))

    if not candidates:
        raise RuntimeError(
            "No LLM providers configured or available. Please set OPENAI_API_KEY, "
            "GEMINI_API_KEY, OPENROUTER_API_KEY, or OLLAMA_HOST in the environment."
        )

    last_error: Exception | None = None

    for prov, mdl in candidates:
        try:
            if prov == "gemini":
                key = os.getenv("GEMINI_API_KEY", "")
                if not key:
                    continue
                body: dict = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"response_mime_type": "application/json", "temperature": 0.2},
                }
                if system:
                    body["systemInstruction"] = {"parts": [{"text": system}]}
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{mdl}:generateContent"
                payload = _post_json(url, body, {"x-goog-api-key": key}, timeout=timeout)
                candidates_out = payload.get("candidates", [])
                if not candidates_out:
                    continue
                parts = candidates_out[0].get("content", {}).get("parts", [])
                text_parts = [p.get("text", "") for p in parts if "text" in p and not p.get("thought", False)]
                if not text_parts:
                    text_parts = [p.get("text", "") for p in parts if "text" in p]
                text = "".join(text_parts)
                tokens = payload.get("usageMetadata", {}).get("totalTokenCount", 0)
                parsed = json.loads(_clean_json_str(text))
                return parsed, prov, mdl, tokens

            elif prov == "openai":
                key = os.getenv("OPENAI_API_KEY", "")
                if not key:
                    continue
                messages = []
                if system:
                    messages.append({"role": "system", "content": system})
                messages.append({"role": "user", "content": prompt})
                url = "https://api.openai.com/v1/chat/completions"
                body = {
                    "model": mdl,
                    "messages": messages,
                    "response_format": {"type": "json_object"},
                    "temperature": 0.2,
                }
                payload = _post_json(url, body, {"Authorization": f"Bearer {key}"}, timeout=timeout)
                text = payload["choices"][0]["message"]["content"]
                tokens = payload.get("usage", {}).get("total_tokens", 0)
                parsed = json.loads(_clean_json_str(text))
                return parsed, prov, mdl, tokens

            elif prov == "openrouter":
                key = os.getenv("OPENROUTER_API_KEY", "")
                if not key:
                    continue
                messages = []
                if system:
                    messages.append({"role": "system", "content": system})
                messages.append({"role": "user", "content": prompt})
                url = "https://openrouter.ai/api/v1/chat/completions"
                body = {
                    "model": mdl,
                    "messages": messages,
                    "response_format": {"type": "json_object"},
                    "temperature": 0.2,
                }
                headers = {
                    "Authorization": f"Bearer {key}",
                    "HTTP-Referer": "http://localhost:5000",
                    "X-Title": "AI SIMPLIFIED LAB Video Factory",
                }
                payload = _post_json(url, body, headers, timeout=timeout)
                text = payload["choices"][0]["message"]["content"]
                tokens = payload.get("usage", {}).get("total_tokens", 0)
                parsed = json.loads(_clean_json_str(text))
                return parsed, prov, mdl, tokens

            elif prov == "ollama":
                host = os.getenv("OLLAMA_HOST", "")
                if not host:
                    continue
                url = f"{host.rstrip('/')}/api/generate"
                body = {
                    "model": mdl,
                    "prompt": prompt,
                    "system": system or "",
                    "stream": False,
                    "format": "json",
                }
                payload = _post_json(url, body, timeout=timeout)
                text = payload.get("response", "")
                tokens = payload.get("prompt_eval_count", 0) + payload.get("eval_count", 0)
                parsed = json.loads(_clean_json_str(text))
                return parsed, prov, mdl, tokens

        except Exception as exc:
            last_error = exc
            continue

    raise RuntimeError(
        f"Failed to generate structured JSON from any configured LLM. Last error: {last_error}"
    )


if __name__ == "__main__":
    import sys
    rows = rank_models(force="--refresh" in sys.argv)
    print("\n---- Model ranking (best first) ----")
    for i, r in enumerate(rows, 1):
        mark = "[OK]" if r["ok"] else "[FAIL]"
        print(f"{i:2d}. {mark} {r['provider']:10s} {_safe(r['model'])[:40]:40s} {r['ms']:6d}ms  {_safe(r['detail'])[:70]}")
    if not rows:
        print("No providers configured. Add keys to .env (OPENROUTER_API_KEY, GEMINI_API_KEY, ...) to start.")
