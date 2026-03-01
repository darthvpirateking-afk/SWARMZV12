from __future__ import annotations

import json
from pathlib import Path

import pytest

from swarmz_runtime.bridge import config as bridge_config


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_get_tier_defaults_for_legacy_config(monkeypatch, tmp_path, caplog) -> None:
    runtime_path = tmp_path / "runtime.json"
    _write_json(runtime_path, {"offlineMode": False})

    monkeypatch.setattr(bridge_config, "_runtime_config_path", lambda: runtime_path)
    bridge_config.reset_cache()
    caplog.set_level("WARNING")

    tier = bridge_config.get_tier("cortex")

    assert tier["provider"] == "openai"
    assert tier["model"] == "gpt-4o"
    assert "runtime.json is v1" in caplog.text


def test_get_tier_merges_runtime_values(monkeypatch, tmp_path) -> None:
    runtime_path = tmp_path / "runtime.json"
    _write_json(
        runtime_path,
        {
            "config_version": 2,
            "llm": {
                "reflex": {
                    "provider": "groq",
                    "model": "llama-3.1-8b-instant",
                    "purpose": "fast path",
                }
            },
        },
    )

    monkeypatch.setattr(bridge_config, "_runtime_config_path", lambda: runtime_path)
    bridge_config.reset_cache()

    tier = bridge_config.get_tier("reflex")

    assert tier["provider"] == "groq"
    assert tier["model"] == "llama-3.1-8b-instant"
    assert tier["purpose"] == "fast path"


def test_get_routing_uses_defaults(monkeypatch, tmp_path) -> None:
    runtime_path = tmp_path / "runtime.json"
    _write_json(runtime_path, {"config_version": 2})

    monkeypatch.setattr(bridge_config, "_runtime_config_path", lambda: runtime_path)
    bridge_config.reset_cache()

    routing = bridge_config.get_routing()

    assert routing["default_tier"] == "cortex"
    assert routing["swarm_tier"] == "reflex"
    assert routing["offline_tier"] == "fallback"


def test_build_litellm_model_prefix_mapping() -> None:
    assert bridge_config.build_litellm_model("openai", "gpt-4o") == "openai/gpt-4o"
    assert (
        bridge_config.build_litellm_model("groq", "llama-3.1-70b-versatile")
        == "groq/llama-3.1-70b-versatile"
    )

    with pytest.raises(ValueError, match="Unknown provider"):
        bridge_config.build_litellm_model("vllm", "local")


def test_get_fallback_chain_order_and_dedupe(monkeypatch) -> None:
    tiers: dict[bridge_config.Tier, dict[str, object]] = {
        "fallback": {"provider": "groq", "model": "llama-3.1-70b-versatile"},
        "reflex": {"provider": "groq", "model": "llama-3.1-70b-versatile"},
        "cortex": {"provider": "openai", "model": "gpt-4o"},
    }
    monkeypatch.setattr(bridge_config, "get_tier", lambda tier: dict(tiers[tier]))
    monkeypatch.setattr(
        bridge_config,
        "resolve_provider_api_key",
        lambda *_: None,
    )

    chain = bridge_config.get_fallback_chain("fallback")

    assert [entry["tier"] for entry in chain] == ["fallback", "cortex"]
    assert [entry["provider"] for entry in chain] == ["groq", "openai"]
