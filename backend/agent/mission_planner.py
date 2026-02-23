from __future__ import annotations

from backend.entity.mood_modifiers import apply_numeric_modifier, apply_override
from backend.intelligence.feature_store import Feature, prefetch_features, set_feature
from backend.memory.why_layer import WhyEntry, log_why, suggest_next_step
from backend.observability.mission_debugger import get_debugger_config
from backend.runner.vpn_provisioner import get_vpn_config


_FEATURE_STORE: dict[str, dict[str, Feature]] = {}


def get_autonomy_mode(autonomy: int, aggression: int, mood: str | None = "calm") -> dict:
    mode = {
        "step_confirmation_required": autonomy < 40,
        "auto_escalate_privileges": aggression > 70,
        "max_auto_steps": int((autonomy / 100) * 20),
        "abort_on_anomaly": autonomy < 30,
    }
    mode["max_auto_steps"] = int(max(0, apply_numeric_modifier(mode["max_auto_steps"], "max_auto_steps", mood)))
    mode["auto_escalate_privileges"] = bool(
        apply_override(mode["auto_escalate_privileges"], "auto_escalate_privileges", mood)
    )
    mode["abort_on_anomaly"] = bool(
        apply_override(mode["abort_on_anomaly"], "abort_on_anomaly", mood)
    )
    if mode["max_auto_steps"] == 0:
        mode["step_confirmation_required"] = True
    return mode


def get_mission_guidance(
    current_phase: str,
    findings_count: int,
    protectiveness: int,
    mission_id: str = "",
) -> str:
    guidance = suggest_next_step(
        current_phase=current_phase,
        findings_count=findings_count,
        protectiveness=protectiveness,
    )
    if mission_id:
        log_why(
            WhyEntry(
                mission_id=mission_id,
                decision="planner_guidance",
                rationale=guidance,
                context={
                    "current_phase": current_phase,
                    "findings_count": findings_count,
                    "protectiveness": protectiveness,
                },
            )
        )
    return guidance


def build_setup_context(
    target_id: str,
    autonomy: int,
    protectiveness: int,
    patience: int,
    curiosity: int,
) -> dict:
    cached = prefetch_features(target_id, _FEATURE_STORE)
    if not cached:
        baseline = Feature(
            name="osint_enriched",
            value=False,
            target_id=target_id,
            ttl_hours=48,
            source="planner_prefetch",
        )
        set_feature(target_id, baseline, _FEATURE_STORE)
        cached = prefetch_features(target_id, _FEATURE_STORE)

    return {
        "target_id": target_id,
        "prefetched_features": list(cached.keys()),
        "vpn": get_vpn_config(protectiveness=protectiveness, autonomy=autonomy),
        "debugger": get_debugger_config(patience=patience, protectiveness=protectiveness),
        "feature_prefetch_enabled": patience >= 50 and curiosity >= 35,
    }
