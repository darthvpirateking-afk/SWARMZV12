"""Mood overlays for capability gating.

Trait logic remains primary; mood modifiers stack on top.
"""

from __future__ import annotations

from typing import Any


MOOD_MODIFIERS: dict[str, dict[str, Any]] = {
    "focused": {
        "max_auto_steps": +5,
        "report_depth": +1,
        "phase_timeout_multiplier": 1.5,
        "rules_engine_priority": "high",
        "shell_lint_strict": True,
        "api_fuzz_rate_limit": "high",
        "debugger_depth": "max",
    },
    "alert": {
        "isolation_level": "full_network_block",
        "log_level": "debug",
        "dcg_sensitivity": +20,
        "dry_run_required": True,
        "log_include_payload": True,
        "cve_min_severity": "high",
        "debugger_auto_on": True,
        "drift_check_frequency": "every_tool",
    },
    "triumphant": {
        "xp_multiplier": 1.25,
        "memory_decay_rate": 0.98,
        "template_xp_multiplier": 1.5,
    },
    "curious": {
        "crawl_max_depth": +2,
        "cross_mission_recall": True,
        "graph_expansion_depth": +1,
        "fingerprint_deep": True,
        "osint_enrichment_depth": "deep",
        "browser_recon_enabled": True,
        "feature_store_prefetch": "deep",
        "cheatsheet_depth": "max",
    },
    "aggressive": {
        "tool_tier": "aggressive",
        "auto_escalate_privileges": True,
        "dcg_sensitivity": -10,
        "skip_dry_run": False,
        "api_fuzz_strategies": "all",
        "vpn_bypass": False,
    },
    "protective": {
        "require_operator_approval": True,
        "abort_on_anomaly": True,
        "dcg_sensitivity": +30,
        "require_dry_run": True,
        "phase_rollback_on_any_warn": True,
        "archive_raw_payloads": False,
        "vpn_required": True,
        "drift_tolerance": -0.10,
        "secret_scan_on_every_file": True,
    },
    "dormant": {
        "max_auto_steps": 0,
        "delegation_enabled": False,
        "rules_engine_enabled": False,
        "phase_pipeline_paused": True,
        "browser_recon": False,
        "vpn_auto": False,
        "debugger": False,
    },
    "contemplative": {
        "report_sections": ["historical_comparison", "attack_chain_diagram"],
        "context_engine_depth": "deep",
        "trait_proposal_auto_review": True,
        "why_layer_depth": "max",
        "drift_detection_window": +10,
        "trace_capture_variables": True,
    },
    "patient": {
        "vm_provisioning_allowed": True,
        "feature_ttl_multiplier": 2.0,
    },
    "restless": {
        "max_concurrent_agents": +2,
        "kanban_parallel_tasks": +3,
        "parallel_environments": +1,
        "automation_rules_max": +10,
    },
    "charged": {
        "xp_multiplier": 1.15,
        "tool_chain_enabled": True,
        "search_providers": +2,
    },
    "calm": {},
}


def normalize_mood(mood: str | None) -> str:
    if not mood:
        return "calm"
    return str(mood).strip().lower()


def get_mood_modifiers(mood: str | None) -> dict[str, Any]:
    return MOOD_MODIFIERS.get(normalize_mood(mood), {})


def apply_numeric_modifier(base: int | float, key: str, mood: str | None) -> int | float:
    mod = get_mood_modifiers(mood).get(key)
    if isinstance(mod, (int, float)):
        return base + mod
    return base


def apply_override(value: Any, key: str, mood: str | None) -> Any:
    mods = get_mood_modifiers(mood)
    if key in mods:
        return mods[key]
    return value
