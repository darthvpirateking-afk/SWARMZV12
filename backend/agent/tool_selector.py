from __future__ import annotations

from backend.entity.mood_modifiers import apply_override
from backend.intel.api_attack_engine import APIEndpoint, fuzz_endpoint
from backend.intel.browser_recon import BrowserReconResult, extract_attack_surface
from backend.intel.cheatsheet_engine import cheats_as_dict, get_relevant_cheats
from backend.intel.default_creds import get_default_credentials
from backend.intel.osint_enricher import enrich_target
from backend.intel.vuln_db_client import search_vulnerabilities
from backend.memory.why_layer import WhyEntry, log_why


TOOL_TIERS = {
    "passive": ["nmap -sn", "whois", "dig", "curl"],
    "active": ["nmap -sV", "nikto", "gobuster", "sqlmap"],
    "aggressive": ["metasploit", "hydra", "john", "burpsuite"],
}


def select_tool_tier(aggression: int, mood: str | None = "calm") -> list[str]:
    if aggression >= 66:
        selected = TOOL_TIERS["passive"] + TOOL_TIERS["active"] + TOOL_TIERS["aggressive"]
    elif aggression >= 31:
        selected = TOOL_TIERS["passive"] + TOOL_TIERS["active"]
    else:
        selected = TOOL_TIERS["passive"]

    mood_tier = apply_override(None, "tool_tier", mood)
    if mood_tier == "aggressive":
        return TOOL_TIERS["passive"] + TOOL_TIERS["active"] + TOOL_TIERS["aggressive"]
    return selected


def allow_tool_chaining(creativity: int, mood: str | None = "calm") -> bool:
    enabled = creativity >= 60
    return bool(apply_override(enabled, "tool_chain_enabled", mood))


def build_pre_attack_intel(
    target: str,
    packages: list[str] | None = None,
    services: list[str] | None = None,
    minimum_severity: str = "medium",
    mission_id: str = "",
) -> dict:
    package_list = packages or []
    service_list = services or []

    vuln_hits = search_vulnerabilities(package_list, minimum_severity=minimum_severity)
    creds: dict[str, list[dict[str, str]]] = {}
    for service in service_list:
        creds[service] = get_default_credentials(service)

    intel = {
        "target": target,
        "osint": enrich_target(target),
        "vulnerabilities": vuln_hits,
        "default_credentials": creds,
        "attack_surface": {},
        "api_fuzz_preview": [],
        "cheats": [],
    }

    recon_result = BrowserReconResult(url=target, dom_snapshot="", network_calls=[], ws_endpoints=[])
    intel["attack_surface"] = extract_attack_surface(recon_result, aggression=40)

    fuzz_results = fuzz_endpoint(
        APIEndpoint(path="/", method="GET", parameters=[], auth="none", schema={}),
        strategy="idor",
        aggression=40,
    )
    intel["api_fuzz_preview"] = [
        {
            "test_type": item.test_type,
            "status_code": item.status_code,
            "anomaly": item.anomaly,
        }
        for item in fuzz_results[:3]
    ]

    cheat_entries = get_relevant_cheats(
        context={"services": service_list, "phase": "recon", "open_ports_labels": []},
        curiosity=60,
        patience=60,
    )
    intel["cheats"] = cheats_as_dict(cheat_entries)

    if mission_id:
        log_why(
            WhyEntry(
                mission_id=mission_id,
                decision="pre_attack_intel",
                rationale="Generated V4 intel package before tool dispatch.",
                context={
                    "target": target,
                    "vuln_count": len(vuln_hits),
                    "services": service_list,
                    "cheat_count": len(cheat_entries),
                },
            )
        )

    return intel
