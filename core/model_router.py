# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
SWARMZ Model Router â€” calls Anthropic Claude OR OpenAI via their HTTP APIs.

Returns normalised response: {text, usage, provider, model, latencyMs, error}
Never crashes server; returns clear errors.

Config source: config/runtime.json â†’ "models" section.
Env var OFFLINE_MODE=true disables all calls.
"""

import json
import os
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, Any, Optional, List

try:
    from core.otel_tracing import trace_llm_call
except ImportError:
    # Fallback if tracing not available
    from contextlib import contextmanager
    @contextmanager
    def trace_llm_call(*args, **kwargs):
        yield None

ROOT = Path(__file__).resolve().parent.parent
CONFIG_FILE = ROOT / "config" / "runtime.json"

# â”€â”€ Config helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


def _load_config() -> Dict[str, Any]:
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def is_offline() -> bool:
    """Return True when OFFLINE_MODE is active (env or config)."""
    env = os.environ.get("OFFLINE_MODE", "").strip().lower()
    if env in ("1", "true", "yes"):
        return True
    cfg = _load_config()
    return bool(cfg.get("offlineMode", False))


def get_model_config() -> Dict[str, Any]:
    """Return the 'models' section from runtime.json, merged with env overrides."""
    cfg = _load_config()
    models = dict(cfg.get("models", {}))
    # env overrides
    provider_env = os.environ.get("MODEL_PROVIDER")
    if provider_env:
        models["provider"] = provider_env
    return models


def _get_api_key(provider_cfg: Dict[str, Any]) -> Optional[str]:
    """Resolve API key from env var named in config."""
    env_name = provider_cfg.get("apiKeyEnv", "")
    return os.environ.get(env_name) if env_name else None


# â”€â”€ Normalised response â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


def _ok_response(
    text: str, usage: Dict, provider: str, model: str, latency_ms: int
) -> Dict[str, Any]:
    return {
        "ok": True,
        "text": text,
        "usage": usage,
        "provider": provider,
        "model": model,
        "latencyMs": latency_ms,
        "error": None,
    }


def _err_response(
    error: str, provider: str = "", model: str = "", latency_ms: int = 0
) -> Dict[str, Any]:
    return {
        "ok": False,
        "text": "",
        "usage": {},
        "provider": provider,
        "model": model,
        "latencyMs": latency_ms,
        "error": error,
    }


# â”€â”€ Anthropic (Messages API) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


def _call_anthropic(
    messages: List[Dict[str, str]],
    system: str,
    model: str,
    api_key: str,
    timeout_ms: int,
    max_tokens: int,
) -> Dict[str, Any]:
    with trace_llm_call(
        provider="anthropic",
        model=model,
        operation="messages.create",
        max_tokens=max_tokens,
        message_count=len(messages),
        system_prompt=system if system else None,
    ) as span:
        url = "https://api.anthropic.com/v1/messages"
        body = json.dumps(
            {
                "model": model,
                "max_tokens": max_tokens,
                "system": system,
                "messages": messages,
            }
        ).encode("utf-8")

        req = urllib.request.Request(url, data=body, method="POST")
        req.add_header("Content-Type", "application/json")
        req.add_header("x-api-key", api_key)
        req.add_header("anthropic-version", "2023-06-01")

        t0 = time.monotonic()
        try:
            timeout_s = max(timeout_ms / 1000, 5)
            resp = urllib.request.urlopen(req, timeout=timeout_s)
            data = json.loads(resp.read().decode("utf-8"))
            latency = int((time.monotonic() - t0) * 1000)

            text = ""
            for block in data.get("content", []):
                if block.get("type") == "text":
                    text += block.get("text", "")

            usage = {
                "input": data.get("usage", {}).get("input_tokens", 0),
                "output": data.get("usage", {}).get("output_tokens", 0),
            }

            # Add tracing attributes for response
            if span:
                span.set_attribute("llm.usage.input_tokens", usage["input"])
                span.set_attribute("llm.usage.output_tokens", usage["output"])
                span.set_attribute("llm.latency_ms", latency)

            return _ok_response(text, usage, "anthropic", model, latency)

        except urllib.error.HTTPError as e:
            latency = int((time.monotonic() - t0) * 1000)
            detail = ""
            try:
                detail = e.read().decode("utf-8")[:500]
            except Exception:
                pass
            return _err_response(
                f"Anthropic HTTP {e.code}: {detail}", "anthropic", model, latency
            )
        except Exception as e:
            latency = int((time.monotonic() - t0) * 1000)
            return _err_response(f"Anthropic error: {str(e)}", "anthropic", model, latency)


# â”€â”€ OpenAI (Chat Completions API) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


def _call_openai(
    messages: List[Dict[str, str]],
    system: str,
    model: str,
    api_key: str,
    timeout_ms: int,
    max_tokens: int,
) -> Dict[str, Any]:
    with trace_llm_call(
        provider="openai",
        model=model,
        operation="chat.completions.create",
        max_tokens=max_tokens,
        message_count=len(messages) + (1 if system else 0),
        has_system_prompt=bool(system),
    ) as span:
        url = "https://api.openai.com/v1/chat/completions"

        full_messages = [{"role": "system", "content": system}] + messages
        body = json.dumps(
            {
                "model": model,
                "max_tokens": max_tokens,
                "messages": full_messages,
            }
        ).encode("utf-8")

        req = urllib.request.Request(url, data=body, method="POST")
        req.add_header("Content-Type", "application/json")
        req.add_header("Authorization", f"Bearer {api_key}")

        t0 = time.monotonic()
        try:
            timeout_s = max(timeout_ms / 1000, 5)
            resp = urllib.request.urlopen(req, timeout=timeout_s)
            data = json.loads(resp.read().decode("utf-8"))
            latency = int((time.monotonic() - t0) * 1000)

            text = ""
            choices = data.get("choices", [])
            if choices:
                text = choices[0].get("message", {}).get("content", "")

            usage = {
                "input": data.get("usage", {}).get("prompt_tokens", 0),
                "output": data.get("usage", {}).get("completion_tokens", 0),
            }

            # Add tracing attributes for response
            if span:
                span.set_attribute("llm.usage.input_tokens", usage["input"])
                span.set_attribute("llm.usage.output_tokens", usage["output"])
                span.set_attribute("llm.latency_ms", latency)

            return _ok_response(text, usage, "openai", model, latency)

        except urllib.error.HTTPError as e:
            latency = int((time.monotonic() - t0) * 1000)
            detail = ""
            try:
                detail = e.read().decode("utf-8")[:500]
            except Exception:
                pass
            return _err_response(
                f"OpenAI HTTP {e.code}: {detail}", "openai", model, latency
            )
        except Exception as e:
            latency = int((time.monotonic() - t0) * 1000)
            return _err_response(f"OpenAI error: {str(e)}", "openai", model, latency)


# -- Ollama provider --


def _call_ollama(
    messages: List[Dict[str, str]],
    system: str,
    model: str,
    endpoint: str,
    timeout_ms: int,
    max_tokens: int,
) -> Dict[str, Any]:
    with trace_llm_call(
        provider="ollama",
        model=model,
        operation="chat",
        max_tokens=max_tokens,
        message_count=len(messages) + (1 if system else 0),
        has_system_prompt=bool(system),
    ) as span:
        url = f"{endpoint}/api/chat"
        full_messages = ([{"role": "system", "content": system}] + messages) if system else messages
        body = json.dumps({
            "model": model,
            "messages": full_messages,
            "stream": False,
        }).encode("utf-8")
        req = urllib.request.Request(url, data=body, method="POST")
        req.add_header("Content-Type", "application/json")
        t0 = time.monotonic()
        try:
            timeout_s = max(timeout_ms / 1000, 5)
            resp = urllib.request.urlopen(req, timeout=timeout_s)
            data = json.loads(resp.read().decode("utf-8"))
            latency = int((time.monotonic() - t0) * 1000)
            text = data.get("message", {}).get("content", "")
            usage = {"input": 0, "output": 0}
            if span:
                span.set_attribute("llm.latency_ms", latency)
            return _ok_response(text, usage, "ollama", model, latency)
        except urllib.error.HTTPError as e:
            latency = int((time.monotonic() - t0) * 1000)
            detail = ""
            try:
                detail = e.read().decode("utf-8")[:500]
            except Exception:
                pass
            return _err_response(f"Ollama HTTP {e.code}: {detail}", "ollama", model, latency)
        except Exception as e:
            latency = int((time.monotonic() - t0) * 1000)
            return _err_response(f"Ollama error: {str(e)}", "ollama", model, latency)


# â”€â”€ Public interface â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€



# -- Google Gemini (generateContent REST API) --
# Add-ons: Google Search grounding, function/tool calling, long context


def _call_gemini(
    messages: list,
    system: str,
    model: str,
    api_key: str,
    endpoint: str,
    timeout_ms: int,
    max_tokens: int,
    tools: Optional[List[Dict]] = None,
    grounding: bool = False,
) -> dict:
    """
    Call Gemini generateContent.

    Add-ons:
      grounding=True   -- enables Google Search grounding (live web results)
      tools=[...]      -- function declarations for tool/function calling
                          e.g. [{"name":"get_weather","description":"...","parameters":{...}}]
    """
    with trace_llm_call(
        provider="gemini",
        model=model,
        operation="generateContent",
        max_tokens=max_tokens,
        message_count=len(messages) + (1 if system else 0),
        has_system_prompt=bool(system),
    ) as span:
        url = f"{endpoint}/models/{model}:generateContent?key={api_key}"

        # Convert messages: Gemini uses "model" instead of "assistant"
        contents = []
        for m in messages:
            role = "model" if m.get("role") == "assistant" else "user"
            contents.append({"role": role, "parts": [{"text": m.get("content", "")}]})

        body_dict: Dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "maxOutputTokens": max_tokens,
                "temperature": 1.0,
            },
        }
        if system:
            body_dict["systemInstruction"] = {"parts": [{"text": system}]}

        # -- Add-on: Google Search grounding --
        # Injects live web search results as context before generating
        gemini_tools = []
        if grounding:
            gemini_tools.append({"google_search": {}})

        # -- Add-on: Function/tool calling --
        # Allows Gemini to call back into your code with structured args
        if tools:
            gemini_tools.append({"function_declarations": tools})

        if gemini_tools:
            body_dict["tools"] = gemini_tools

        body = json.dumps(body_dict).encode("utf-8")
        req = urllib.request.Request(url, data=body, method="POST")
        req.add_header("Content-Type", "application/json")

        t0 = time.monotonic()
        try:
            timeout_s = max(timeout_ms / 1000, 5)
            resp = urllib.request.urlopen(req, timeout=timeout_s)
            data = json.loads(resp.read().decode("utf-8"))
            latency = int((time.monotonic() - t0) * 1000)

            text = ""
            tool_calls = []
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                for p in parts:
                    if "text" in p:
                        text += p["text"]
                    # Capture function call responses
                    if "functionCall" in p:
                        tool_calls.append(p["functionCall"])

            # Append grounding sources to text if present
            grounding_meta = data.get("groundingMetadata", {})
            sources = grounding_meta.get("groundingChunks", [])
            if sources:
                refs = []
                for s in sources:
                    web = s.get("web", {})
                    if web.get("uri"):
                        refs.append(f"[{web.get('title', web['uri'])}]({web['uri']})")
                if refs:
                    text += "\n\n**Sources:** " + " | ".join(refs)

            usage_meta = data.get("usageMetadata", {})
            usage = {
                "input": usage_meta.get("promptTokenCount", 0),
                "output": usage_meta.get("candidatesTokenCount", 0),
            }

            if span:
                span.set_attribute("llm.usage.input_tokens", usage["input"])
                span.set_attribute("llm.usage.output_tokens", usage["output"])
                span.set_attribute("llm.latency_ms", latency)
                if grounding:
                    span.set_attribute("gemini.grounding", True)
                if tool_calls:
                    span.set_attribute("gemini.tool_calls", len(tool_calls))

            result = _ok_response(text, usage, "gemini", model, latency)
            if tool_calls:
                result["tool_calls"] = tool_calls
            return result

        except urllib.error.HTTPError as e:
            latency = int((time.monotonic() - t0) * 1000)
            detail = ""
            try:
                detail = e.read().decode("utf-8")[:500]
            except Exception:
                pass
            return _err_response(f"Gemini HTTP {e.code}: {detail}", "gemini", model, latency)
        except Exception as e:
            latency = int((time.monotonic() - t0) * 1000)
            return _err_response(f"Gemini error: {str(e)}", "gemini", model, latency)

def call(
    messages: List[Dict[str, str]],
    system: str = "",
    provider: Optional[str] = None,
    model: Optional[str] = None,
    max_tokens: Optional[int] = None,
    timeout_ms: Optional[int] = None,
    tools: Optional[List[Dict]] = None,
    grounding: Optional[bool] = None,
) -> Dict[str, Any]:
    """
    Route a chat request to the configured provider.

    Args:
        messages:   List of {"role":"user"|"assistant", "content":"..."}.
        system:     System prompt text.
        provider:   Override provider; else from config.
        model:      Override model name; else from config.
        max_tokens: Override; else from config (default 1500).
        timeout_ms: Override; else from config (default 60000).
        tools:      [Gemini] List of function declarations for tool calling.
        grounding:  [Gemini] Enable Google Search grounding (True/False).

    Returns:
        Normalised dict: {ok, text, usage, provider, model, latencyMs, error}
        For Gemini tool calls: also includes "tool_calls" list.
    """
    if is_offline():
        return _err_response("OFFLINE_MODE active â€” model calls disabled")

    cfg = get_model_config()
    prov = (provider or cfg.get("provider", "ollama")).lower()
    tout = timeout_ms or cfg.get("timeoutMs", 60000)
    mtok = max_tokens or cfg.get("maxTokens", 1500)

    prov_cfg = cfg.get(prov, {})
    mdl = model or prov_cfg.get("model", "")
    api_key = _get_api_key(prov_cfg)

    if not api_key and prov not in ("ollama",):
        env_name = prov_cfg.get("apiKeyEnv", f"{prov.upper()}_API_KEY")
        return _err_response(
            f"No API key â€” set env var {env_name}",
            prov,
            mdl,
            0,
        )

    if not mdl:
        return _err_response(f"No model configured for provider '{prov}'", prov, "", 0)

    if prov == "anthropic":
        return _call_anthropic(messages, system, mdl, api_key, tout, mtok)
    elif prov == "openai":
        return _call_openai(messages, system, mdl, api_key, tout, mtok)
    elif prov == "ollama":
        endpoint = prov_cfg.get("endpoint", "http://localhost:11434")
        return _call_ollama(messages, system, mdl, endpoint, tout, mtok)
    elif prov == "gemini":
        endpoint = prov_cfg.get("endpoint", "https://generativelanguage.googleapis.com/v1beta")
        use_grounding = grounding if grounding is not None else prov_cfg.get("grounding", False)
        fn_tools = tools if tools is not None else prov_cfg.get("tools", None)
        return _call_gemini(messages, system, mdl, api_key, endpoint, tout, mtok,
                            tools=fn_tools, grounding=use_grounding)
    else:
        return _err_response(f"Unknown provider: {prov}", prov, mdl, 0)


# â”€â”€ Status helper (used by /v1/ai/status) â”€â”€â”€â”€â”€â”€â”€â”€

_last_call_timestamp: Optional[str] = None
_last_call_error: Optional[str] = None


def record_call(timestamp: str, error: Optional[str] = None):
    """Called after each model invocation to track last-call metadata."""
    global _last_call_timestamp, _last_call_error
    _last_call_timestamp = timestamp
    _last_call_error = error


def get_status() -> Dict[str, Any]:
    """Return AI subsystem status for /v1/ai/status."""
    cfg = get_model_config()
    prov = cfg.get("provider", "anthropic")
    prov_cfg = cfg.get(prov, {})
    mdl = prov_cfg.get("model", "")
    has_key = bool(_get_api_key(prov_cfg))

    return {
        "offlineMode": is_offline(),
        "provider": prov,
        "model": mdl,
        "apiKeySet": has_key,
        "lastCallTimestamp": _last_call_timestamp,
        "lastError": _last_call_error,
    }
