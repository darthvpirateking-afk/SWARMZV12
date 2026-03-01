"""Runtime config accessors for bridge model routing."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Final, Literal

Tier = Literal["cortex", "reflex", "fallback"]

logger = logging.getLogger("swarmz.bridge.config")

_DEFAULTS: Final[dict[Tier, dict[str, Any]]] = {
    "cortex": {
        "provider": "openai",
        "model": "gpt-4o",
        "purpose": "deep reasoning, codegen, mission engine, evolution",
    },
    "reflex": {
        "provider": "groq",
        "model": "llama-3.1-70b-versatile",
        "purpose": "swarm routing, planning, fast ops, agent chatter",
    },
    "fallback": {
        "provider": "vllm",
        "model": "local",
        "enabled": False,
        "base_url": "http://localhost:8000/v1",
        "purpose": "sovereign / air-gapped / community deployments",
    },
}

_DEFAULT_ROUTING: Final[dict[str, str]] = {
    "default_tier": "cortex",
    "swarm_tier": "reflex",
    "offline_tier": "fallback",
}

_CONFIG: dict[str, Any] | None = None
_WARNED_LEGACY = False
_FALLBACK_TIERS: Final[tuple[Tier, Tier]] = ("reflex", "cortex")
_PROVIDER_ENV_DEFAULTS: Final[dict[str, str]] = {
    "openai": "OPENAI_API_KEY",
    "groq": "GROQ_API_KEY",
}


def _runtime_config_path() -> Path:
    return Path(__file__).resolve().parents[2] / "config" / "runtime.json"


def _load_config() -> dict[str, Any]:
    global _CONFIG, _WARNED_LEGACY

    if _CONFIG is not None:
        return _CONFIG

    cfg_path = _runtime_config_path()
    config: dict[str, Any] = {}
    if cfg_path.exists():
        try:
            config = json.loads(cfg_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            logger.warning(
                "[NEXUSMON WARN] runtime.json is invalid JSON at %s; using defaults.",
                cfg_path,
            )
            config = {}
    else:
        logger.warning(
            "[NEXUSMON WARN] runtime.json missing at %s; using defaults.",
            cfg_path,
        )

    version = int(config.get("config_version", 1))
    if version < 2 and not _WARNED_LEGACY:
        logger.warning(
            "[NEXUSMON WARN] runtime.json is v1; llm block missing, using bridge defaults.",
        )
        _WARNED_LEGACY = True

    _CONFIG = config
    return _CONFIG


def get_tier(tier: Tier) -> dict[str, Any]:
    """Return merged tier config from runtime.json llm block plus defaults."""

    cfg = _load_config()
    llm_cfg = cfg.get("llm")
    base = dict(_DEFAULTS[tier])

    if isinstance(llm_cfg, dict):
        raw_tier_cfg = llm_cfg.get(tier)
        if isinstance(raw_tier_cfg, dict):
            base.update(raw_tier_cfg)

    return base


def get_routing() -> dict[str, str]:
    """Return routing block merged with routing defaults."""

    cfg = _load_config()
    routing = dict(_DEFAULT_ROUTING)
    raw_routing = cfg.get("routing")
    if isinstance(raw_routing, dict):
        for key in ("default_tier", "swarm_tier", "offline_tier"):
            value = raw_routing.get(key)
            if isinstance(value, str) and value:
                routing[key] = value
    return routing


def build_litellm_model(provider: str, model: str) -> str:
    """Build a provider-prefixed model id for LiteLLM."""

    normalized_provider = provider.strip().lower()
    normalized_model = model.strip()
    if not normalized_model:
        raise ValueError("Missing model name for LiteLLM routing")

    if normalized_provider == "openai":
        return f"openai/{normalized_model}"
    if normalized_provider == "groq":
        return f"groq/{normalized_model}"
    raise ValueError(f"Unknown provider: {provider}")


def resolve_provider_api_key(
    provider: str,
    tier_cfg: dict[str, Any],
    runtime_cfg: dict[str, Any] | None = None,
) -> str | None:
    """Resolve provider API key from env using tier/runtime hints."""

    cfg = runtime_cfg if runtime_cfg is not None else _load_config()
    normalized_provider = provider.strip().lower()

    env_candidates: list[str] = []

    for key_name in (
        "apiKeyEnv",
        "api_key_env",
        "apiKeyEnvVar",
        "api_key_env_var",
    ):
        value = tier_cfg.get(key_name)
        if isinstance(value, str) and value.strip():
            env_candidates.append(value.strip())

    for container_key in ("api_keys", "llm_api_keys"):
        container = cfg.get(container_key)
        if isinstance(container, dict):
            value = container.get(normalized_provider)
            if isinstance(value, str) and value.strip():
                env_candidates.append(value.strip())

    llm_cfg = cfg.get("llm")
    if isinstance(llm_cfg, dict):
        llm_api_keys = llm_cfg.get("api_keys")
        if isinstance(llm_api_keys, dict):
            value = llm_api_keys.get(normalized_provider)
            if isinstance(value, str) and value.strip():
                env_candidates.append(value.strip())

    default_env = _PROVIDER_ENV_DEFAULTS.get(normalized_provider)
    if default_env:
        env_candidates.append(default_env)

    seen_env: set[str] = set()
    for env_name in env_candidates:
        if env_name in seen_env:
            continue
        seen_env.add(env_name)
        resolved = os.getenv(env_name)
        if resolved:
            return resolved

    return None


def get_fallback_chain(primary_tier: Tier) -> list[dict[str, Any]]:
    """Build fallback chain with fixed order: primary -> reflex -> cortex."""

    ordered_tiers: list[Tier] = [primary_tier]
    for fallback_tier in _FALLBACK_TIERS:
        if fallback_tier not in ordered_tiers:
            ordered_tiers.append(fallback_tier)

    runtime_cfg = _load_config()
    chain: list[dict[str, Any]] = []
    seen_signatures: set[str] = set()

    for tier_name in ordered_tiers:
        tier_cfg = dict(get_tier(tier_name))
        provider = str(tier_cfg.get("provider", "")).strip().lower()
        model = str(tier_cfg.get("model", "")).strip()
        signature = f"{provider}:{model}"

        if signature in seen_signatures:
            continue
        seen_signatures.add(signature)

        tier_cfg["tier"] = tier_name
        api_key = resolve_provider_api_key(provider, tier_cfg, runtime_cfg)
        if api_key:
            tier_cfg["api_key"] = api_key
        chain.append(tier_cfg)

    return chain


def reset_cache() -> None:
    """Reset cached runtime config (test helper)."""

    global _CONFIG, _WARNED_LEGACY
    _CONFIG = None
    _WARNED_LEGACY = False
