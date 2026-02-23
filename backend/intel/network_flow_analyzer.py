from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class NetworkFlow:
    flow_id: str
    src_ip: str
    dst_ip: str
    src_port: int
    dst_port: int
    protocol: str
    start_time: float
    end_time: float | None
    bytes_sent: int
    bytes_recv: int
    payload_preview: str
    flags: list[str]


SUSPICIOUS_PATTERNS: dict[str, dict[str, Any]] = {
    "c2_pattern": {"beacon_interval_s": (20, 120), "small_payload": True},
    "exfil_pattern": {"large_outbound": True, "uncommon_port": True},
    "lateral_move": {"smb_auth": True, "new_host": True},
    "dns_tunneling": {"high_entropy_subdomain": True, "large_txt_record": True},
}


def analyze_flow(flow: NetworkFlow, baseline: dict[str, Any]) -> list[str]:
    flags: list[str] = []
    known_hosts = baseline.get("known_hosts", [])

    if flow.bytes_sent > 10_000_000 and flow.dst_ip not in known_hosts:
        flags.append("exfil_pattern")
    if flow.protocol in ["dns"] and len(flow.payload_preview) > 100:
        flags.append("dns_tunneling")
    if flow.protocol in ["smb", "ldap"] and flow.dst_ip not in known_hosts:
        flags.append("lateral_move")

    return flags


def get_flow_analyzer_config(curiosity: int, protectiveness: int) -> dict[str, Any]:
    return {
        "enabled": curiosity >= 40,
        "capture_during_mission": True,
        "protocol_parsers": ["http", "https", "dns", "smb", "ldap", "ftp"],
        "detect_c2_patterns": protectiveness >= 50,
        "detect_exfil_patterns": protectiveness >= 40,
        "session_reconstruction": curiosity >= 60,
        "pcap_storage": protectiveness >= 50,
        "pcap_path": "/data/captures/{mission_id}.pcap",
        "alert_on_flag": True,
        "replay_in_cockpit": True,
        "baseline_known_hosts": True,
        "retention_hours": 24 if protectiveness < 70 else 6,
    }


def should_store_pcap(protectiveness: int) -> bool:
    return protectiveness >= 50


def should_delete_pcap_after_retention() -> bool:
    return True
