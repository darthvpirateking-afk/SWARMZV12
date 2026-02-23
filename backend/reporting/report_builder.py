from __future__ import annotations

from backend.intel.browser_recon import BrowserReconResult, extract_attack_surface
from backend.entity.mood_modifiers import apply_numeric_modifier, apply_override, get_mood_modifiers
from backend.intel.vuln_db_client import search_vulnerabilities


def get_cve_report_section(packages: list[str], minimum_severity: str = "medium") -> dict:
    findings = search_vulnerabilities(packages, minimum_severity=minimum_severity)
    return {
        "section": "cve_intelligence",
        "count": len(findings),
        "findings": findings,
    }


def get_attack_surface_section(result: BrowserReconResult, aggression: int) -> dict:
    surface = extract_attack_surface(result=result, aggression=aggression)
    return {
        "section": "attack_surface",
        "count_endpoints": len(surface.get("endpoints", [])),
        "count_ws": len(surface.get("ws_targets", [])),
        "surface": surface,
    }


def get_report_sections(
    patience: int,
    protectiveness: int,
    aggression: int,
    creativity: int,
    curiosity: int,
    mood: str | None = "calm",
) -> list[str]:
    active = ["executive_summary", "vulnerability_list"]
    if curiosity >= 45 and creativity >= 50:
        active.append("attack_surface")
    if curiosity >= 35:
        active.append("cve_intelligence")
    if patience >= 40:
        active.append("cvss_scoring")
    if aggression >= 50:
        active.append("exploitation_guide")
    if protectiveness >= 50:
        active.append("remediation_steps")
    if creativity >= 60:
        active.append("attack_chain_diagram")
    if patience >= 70 and curiosity >= 60:
        active.append("historical_comparison")

    report_depth = int(apply_numeric_modifier(0, "report_depth", mood))
    if report_depth > 0 and "cvss_scoring" not in active:
        active.append("cvss_scoring")

    mood_sections = apply_override([], "report_sections", mood)
    if isinstance(mood_sections, list):
        for section in mood_sections:
            if section not in active:
                active.append(section)

    mods = get_mood_modifiers(mood)
    if mods.get("context_engine_depth") == "deep" and "historical_comparison" not in active:
        active.append("historical_comparison")
    return active
