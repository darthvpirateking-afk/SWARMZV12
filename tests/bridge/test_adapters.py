from __future__ import annotations

from typing import Any

from swarmz_runtime.bridge import llm


class _LiteLLMStub:
    def __init__(self, response_text: str) -> None:
        self.response_text = response_text
        self.calls: list[dict[str, Any]] = []

    def completion(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(kwargs)
        return {"choices": [{"message": {"content": self.response_text}}]}

    async def acompletion(self, **kwargs: Any) -> dict[str, Any]:
        return self.completion(**kwargs)


def test_litellm_call_shape_from_public_bridge(monkeypatch) -> None:
    stub = _LiteLLMStub("NEXUSMON ONLINE")

    monkeypatch.setattr(
        llm,
        "get_fallback_chain",
        lambda _: [{"provider": "openai", "model": "gpt-4o"}],
    )
    monkeypatch.setattr(llm, "_get_litellm_module", lambda: stub)
    monkeypatch.setattr(llm, "resolve_provider_api_key", lambda *_: "test-key")

    result = llm.call("test prompt", tier="cortex", system="sys")

    assert result == "NEXUSMON ONLINE"
    kwargs = stub.calls[0]
    assert kwargs["model"] == "openai/gpt-4o"
    assert kwargs["messages"][0] == {"role": "system", "content": "sys"}
    assert kwargs["messages"][1] == {"role": "user", "content": "test prompt"}
    assert kwargs["api_key"] == "test-key"
