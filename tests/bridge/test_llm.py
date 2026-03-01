from __future__ import annotations

from typing import Any

import pytest

from swarmz_runtime.bridge import llm


class _LiteLLMStub:
    def __init__(
        self,
        responses: dict[str, str],
        failing_models: set[str] | None = None,
    ) -> None:
        self.responses = responses
        self.failing_models = failing_models or set()
        self.calls: list[str] = []

    def completion(self, **kwargs: Any) -> dict[str, Any]:
        model = str(kwargs["model"])
        self.calls.append(model)
        if model in self.failing_models:
            raise RuntimeError(f"forced failure: {model}")
        content = self.responses.get(model, "")
        return {"choices": [{"message": {"content": content}}]}

    async def acompletion(self, **kwargs: Any) -> dict[str, Any]:
        return self.completion(**kwargs)


def test_primary_success(monkeypatch) -> None:
    stub = _LiteLLMStub({"openai/gpt-4o": "ok-cortex"})
    monkeypatch.setattr(
        llm,
        "get_fallback_chain",
        lambda _: [{"provider": "openai", "model": "gpt-4o"}],
    )
    monkeypatch.setattr(llm, "_get_litellm_module", lambda: stub)
    monkeypatch.setattr(llm, "resolve_provider_api_key", lambda *_: None)

    assert llm.call("hello", tier="cortex", system="sys") == "ok-cortex"
    assert stub.calls == ["openai/gpt-4o"]


def test_fallback_primary_to_groq(monkeypatch) -> None:
    stub = _LiteLLMStub(
        {"groq/llama-3.1-70b-versatile": "ok-reflex"},
        failing_models={"openai/gpt-4o"},
    )
    monkeypatch.setattr(
        llm,
        "get_fallback_chain",
        lambda _: [
            {"provider": "openai", "model": "gpt-4o"},
            {"provider": "groq", "model": "llama-3.1-70b-versatile"},
        ],
    )
    monkeypatch.setattr(llm, "_get_litellm_module", lambda: stub)
    monkeypatch.setattr(llm, "resolve_provider_api_key", lambda *_: None)

    assert llm.call("route", tier="cortex") == "ok-reflex"
    assert stub.calls == ["openai/gpt-4o", "groq/llama-3.1-70b-versatile"]


def test_fallback_primary_to_groq_to_openai(monkeypatch) -> None:
    stub = _LiteLLMStub(
        {"openai/gpt-4o": "ok-openai"},
        failing_models={"groq/llama-3.1-70b-versatile"},
    )
    monkeypatch.setattr(
        llm,
        "get_fallback_chain",
        lambda _: [
            {"provider": "vllm", "model": "local"},
            {"provider": "groq", "model": "llama-3.1-70b-versatile"},
            {"provider": "openai", "model": "gpt-4o"},
        ],
    )
    monkeypatch.setattr(llm, "_get_litellm_module", lambda: stub)
    monkeypatch.setattr(llm, "resolve_provider_api_key", lambda *_: None)

    assert llm.call("route", tier="fallback") == "ok-openai"
    assert stub.calls == ["groq/llama-3.1-70b-versatile", "openai/gpt-4o"]


def test_unknown_provider_path(monkeypatch) -> None:
    stub = _LiteLLMStub({})
    monkeypatch.setattr(
        llm,
        "get_fallback_chain",
        lambda _: [{"provider": "unknown-provider", "model": "x"}],
    )
    monkeypatch.setattr(llm, "_get_litellm_module", lambda: stub)
    monkeypatch.setattr(llm, "resolve_provider_api_key", lambda *_: None)

    with pytest.raises(RuntimeError, match="Unknown provider"):
        llm.call("nope", tier="cortex")
