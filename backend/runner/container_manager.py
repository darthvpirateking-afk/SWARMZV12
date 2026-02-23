from __future__ import annotations

from backend.entity.mood_modifiers import apply_override
from backend.intel.network_flow_analyzer import (
    get_flow_analyzer_config,
    should_store_pcap,
)

MISSION_IMAGE_MAP = {
    "web": "pentagi/web:latest",
    "network": "pentagi/network:latest",
    "exploit": "pentagi/metasploit:latest",
    "osint": "pentagi/osint:latest",
    "custom": None,
}


def get_isolation_level(protectiveness: int, mood: str | None = "calm") -> str:
    if protectiveness >= 80:
        isolation = "full_network_block"
    elif protectiveness >= 50:
        isolation = "restricted_egress"
    else:
        isolation = "monitored_open"
    return apply_override(isolation, "isolation_level", mood)


def get_container_image(
    mission_type: str,
    creativity: int,
    autonomy: int,
    mood: str | None = "calm",
) -> str:
    if creativity >= 80 and autonomy >= 70:
        return "dynamic_build"
    selected = MISSION_IMAGE_MAP.get(mission_type, "pentagi/general:latest")
    tool_tier = apply_override(None, "tool_tier", mood)
    if tool_tier == "aggressive" and mission_type == "exploit":
        return "pentagi/metasploit:latest"
    return selected or "pentagi/general:latest"


def get_mission_capture_plan(
    mission_id: str, curiosity: int, protectiveness: int
) -> dict:
    cfg = get_flow_analyzer_config(curiosity=curiosity, protectiveness=protectiveness)
    pcap_enabled = should_store_pcap(protectiveness)
    return {
        "mission_id": mission_id,
        "capture_enabled": bool(
            cfg.get("enabled") and cfg.get("capture_during_mission")
        ),
        "pcap_storage": bool(cfg.get("pcap_storage") and pcap_enabled),
        "pcap_path": cfg.get("pcap_path", "/data/captures/{mission_id}.pcap").format(
            mission_id=mission_id
        ),
        "retention_hours": cfg.get("retention_hours", 24),
    }
