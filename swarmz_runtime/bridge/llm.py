"""
NEXUSMON LLM Bridge - canonical model routing layer.
All LLM calls pass through this module.
Operator-configurable via config/runtime.json.
"""

from __future__ import annotations

import importlib
import logging
from typing import Any

from .config import (
    Tier,
    build_litellm_model,
    get_fallback_chain,
    resolve_provider_api_key,
)

logger = logging.getLogger("swarmz.bridge.llm")
_LITELLM_MODULE: Any | None = None


def _get_litellm_module() -> Any:
    global _LITELLM_MODULE
    if _LITELLM_MODULE is None:
        _LITELLM_MODULE = importlib.import_module("litellm")
    return _LITELLM_MODULE


def _build_messages(prompt: str, system: str | None) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    return messages


def _extract_content(response: Any) -> str:
    if isinstance(response, dict):
        choices = response.get("choices")
        if isinstance(choices, list) and choices:
            first = choices[0]
            if isinstance(first, dict):
                message = first.get("message")
                if isinstance(message, dict):
                    content = message.get("content")
                    if isinstance(content, str):
                        return content

    choices = getattr(response, "choices", None)
    if isinstance(choices, list) and choices:
        message = getattr(choices[0], "message", None)
        content = getattr(message, "content", None)
        if isinstance(content, str):
            return content

    return ""


def _candidate_label(candidate: dict[str, Any]) -> str:
    provider = str(candidate.get("provider", "unknown")).strip().lower()
    model = str(candidate.get("model", "unknown")).strip()
    return f"{provider}/{model}"


def _completion_attempt(
    candidate: dict[str, Any],
    messages: list[dict[str, str]],
    max_tokens: int,
    temperature: float,
    kwargs: dict[str, Any],
) -> str:
    provider = str(candidate.get("provider", "")).strip().lower()
    model = str(candidate.get("model", "")).strip()
    if not provider:
        raise ValueError("Missing provider in tier configuration")
    if not model:
        raise ValueError("Missing model in tier configuration")

    litellm_model = build_litellm_model(provider, model)
    api_key = resolve_provider_api_key(provider, candidate)
    if not api_key:
        api_key = candidate.get("api_key")
        if api_key is not None:
            api_key = str(api_key)

    call_kwargs = dict(kwargs)
    if api_key:
        call_kwargs.setdefault("api_key", api_key)

    response = _get_litellm_module().completion(
        model=litellm_model,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
        **call_kwargs,
    )
    return _extract_content(response)


async def _acompletion_attempt(
    candidate: dict[str, Any],
    messages: list[dict[str, str]],
    max_tokens: int,
    temperature: float,
    kwargs: dict[str, Any],
) -> str:
    provider = str(candidate.get("provider", "")).strip().lower()
    model = str(candidate.get("model", "")).strip()
    if not provider:
        raise ValueError("Missing provider in tier configuration")
    if not model:
        raise ValueError("Missing model in tier configuration")

    litellm_model = build_litellm_model(provider, model)
    api_key = resolve_provider_api_key(provider, candidate)
    if not api_key:
        api_key = candidate.get("api_key")
        if api_key is not None:
            api_key = str(api_key)

    call_kwargs = dict(kwargs)
    if api_key:
        call_kwargs.setdefault("api_key", api_key)

    response = await _get_litellm_module().acompletion(
        model=litellm_model,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
        **call_kwargs,
    )
    return _extract_content(response)


def _call_with_fallback(
    prompt: str,
    tier: Tier,
    system: str | None,
    max_tokens: int,
    temperature: float,
    kwargs: dict[str, Any],
) -> str:
    messages = _build_messages(prompt, system)
    failures: list[str] = []

    for candidate in get_fallback_chain(tier):
        label = _candidate_label(candidate)
        try:
            content = _completion_attempt(
                candidate=candidate,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                kwargs=kwargs,
            )
            if content:
                return content
            failures.append(f"{label} (empty content)")
        except Exception as exc:  # pragma: no cover - exercised in fallback tests
            logger.warning("[NEXUSMON WARN] LLM attempt failed for %s: %s", label, exc)
            failures.append(f"{label} ({exc})")

    details = "; ".join(failures) if failures else "no candidates available"
    raise RuntimeError(f"LLM call failed after fallback chain: {details}")


async def _acall_with_fallback(
    prompt: str,
    tier: Tier,
    system: str | None,
    max_tokens: int,
    temperature: float,
    kwargs: dict[str, Any],
) -> str:
    messages = _build_messages(prompt, system)
    failures: list[str] = []

    for candidate in get_fallback_chain(tier):
        label = _candidate_label(candidate)
        try:
            content = await _acompletion_attempt(
                candidate=candidate,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                kwargs=kwargs,
            )
            if content:
                return content
            failures.append(f"{label} (empty content)")
        except Exception as exc:  # pragma: no cover - exercised in fallback tests
            logger.warning("[NEXUSMON WARN] LLM attempt failed for %s: %s", label, exc)
            failures.append(f"{label} ({exc})")

    details = "; ".join(failures) if failures else "no candidates available"
    raise RuntimeError(f"LLM call failed after fallback chain: {details}")


def call(
    prompt: str,
    tier: Tier = "cortex",
    system: str | None = None,
    max_tokens: int = 2048,
    temperature: float = 0.3,
    **kwargs: Any,
) -> str:
    """Route a prompt to the configured provider chain for the requested tier."""

    result = _call_with_fallback(
        prompt=prompt,
        tier=tier,
        system=system,
        max_tokens=max_tokens,
        temperature=temperature,
        kwargs=dict(kwargs),
    )
    return str(result or "")
