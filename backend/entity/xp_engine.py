from __future__ import annotations

from backend.entity.mood_modifiers import apply_override


XP_EVENTS = {
    "mission_complete": 50,
    "template_mission_complete": 60,
    "novel_vulnerability_found": 30,
    "tool_chain_success": 20,
    "report_generated": 15,
    "delegation_success": 25,
    "web_intel_new_entity": 10,
    "new_target_fingerprinted": 15,
    "experience_pattern_matched": 15,
    "graph_contradiction_resolved": 25,
    "memory_self_update": 10,
    "operator_approval_earned": 5,
    "command_threat_blocked": 20,
    "dry_run_validated": 20,
    "rollback_recovery": 30,
    "phase_pipeline_clean_run": 25,
    "error_pattern_resolved": 35,
    "trait_proposal_accepted": 30,
    "tool_registry_discovery": 10,
    "playbook_idempotency_hit": 5,
    "automation_rule_triggered": 10,
    "automation_rule_created": 15,
    "cve_lookup_hit": 20,
    "default_credential_confirmed": 25,
    "shell_lint_blocked": 15,
    "experiment_logged": 10,
    "why_decision_recorded": 8,
    "osint_target_enriched": 12,
    "intel_archive_written": 8,
    "resource_budget_respected": 10,
    "mission_changelog_generated": 10,
    "js_app_surface_mapped": 30,
    "hidden_api_discovered": 25,
    "c2_pattern_detected_on_target": 45,
    "exfil_caught_in_flight": 50,
    "secret_discovered_in_target": 50,
    "api_idor_confirmed": 45,
    "api_spec_reconstructed": 20,
    "cheat_technique_applied": 10,
    "feature_store_hit": 5,
    "drift_self_corrected": 25,
    "vpn_node_clean_destroy": 10,
    "mission_debugged_to_root_cause": 35,
}

FORM_ORDER = ["ROOKIE", "CHAMPION", "ULTIMATE", "MEGA", "SOVEREIGN"]
FORM_THRESHOLDS = {
    "ROOKIE": 1000.0,
    "CHAMPION": 5000.0,
    "ULTIMATE": 20000.0,
    "MEGA": 100000.0,
}


def check_form_evolution(xp: float) -> str:
    if xp >= FORM_THRESHOLDS["MEGA"]:
        return "SOVEREIGN"
    if xp >= FORM_THRESHOLDS["ULTIMATE"]:
        return "MEGA"
    if xp >= FORM_THRESHOLDS["CHAMPION"]:
        return "ULTIMATE"
    if xp >= FORM_THRESHOLDS["ROOKIE"]:
        return "CHAMPION"
    return "ROOKIE"


def calculate_xp_pct(xp: float, form: str) -> float:
    form_key = str(form or "ROOKIE").upper()
    if form_key == "SOVEREIGN":
        return 100.0
    threshold = FORM_THRESHOLDS.get(form_key, FORM_THRESHOLDS["ROOKIE"])
    lower = 0.0
    if form_key == "CHAMPION":
        lower = FORM_THRESHOLDS["ROOKIE"]
    elif form_key == "ULTIMATE":
        lower = FORM_THRESHOLDS["CHAMPION"]
    elif form_key == "MEGA":
        lower = FORM_THRESHOLDS["ULTIMATE"]

    denom = max(1.0, threshold - lower)
    pct = ((xp - lower) / denom) * 100.0
    return max(0.0, min(100.0, round(pct, 1)))


def award_xp(event_key: str, entity: dict, mood: str | None = "calm") -> dict:
    gain = float(XP_EVENTS.get(event_key, 0))
    multiplier = apply_override(1.0, "xp_multiplier", mood)
    if isinstance(multiplier, (int, float)):
        gain *= float(multiplier)

    current_xp = float(entity.get("xp") or entity.get("evolution_xp") or 0.0)
    new_xp = current_xp + gain

    entity["xp"] = round(new_xp, 2)
    entity["evolution_xp"] = round(new_xp, 2)
    entity["form"] = check_form_evolution(new_xp)
    entity["current_form"] = entity["form"]
    entity["xp_pct"] = calculate_xp_pct(new_xp, entity["form"])
    return entity
