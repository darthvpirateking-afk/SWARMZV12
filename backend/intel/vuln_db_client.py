from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


@dataclass
class VulnerabilityRecord:
    cve_id: str
    severity: str
    score: float
    package: str = ""
    affected_version: str = ""
    fixed_version: str = ""
    source: str = ""
    summary: str = ""


SEVERITY_ORDER = {
    "critical": 4,
    "high": 3,
    "medium": 2,
    "low": 1,
    "unknown": 0,
}


KNOWN_VULNS: dict[str, list[VulnerabilityRecord]] = {
    "openssl": [
        VulnerabilityRecord(
            cve_id="CVE-2023-5363",
            severity="high",
            score=7.5,
            package="openssl",
            source="local_catalog",
            summary="Potential key exchange downgrade risk in specific handshake paths.",
        )
    ],
    "log4j": [
        VulnerabilityRecord(
            cve_id="CVE-2021-44228",
            severity="critical",
            score=10.0,
            package="log4j",
            source="local_catalog",
            summary="JNDI lookup RCE vulnerability.",
        )
    ],
}


def get_vuln_db_config(curiosity: int, protectiveness: int) -> dict[str, Any]:
    return {
        "enabled": curiosity >= 35,
        "sources": ["NVD", "OSV", "GHSA"],
        "cache_ttl_minutes": 30 if curiosity >= 60 else 120,
        "include_medium": protectiveness < 80,
        "fail_closed": protectiveness >= 70,
    }


def normalize_package_name(name: str) -> str:
    return (name or "").strip().lower().replace("_", "-")


def query_known_vulns(package_name: str) -> list[VulnerabilityRecord]:
    return list(KNOWN_VULNS.get(normalize_package_name(package_name), []))


def search_vulnerabilities(packages: list[str], minimum_severity: str = "low") -> list[dict[str, Any]]:
    threshold = SEVERITY_ORDER.get((minimum_severity or "low").lower(), 1)
    findings: list[VulnerabilityRecord] = []

    for package in packages:
        for record in query_known_vulns(package):
            sev_rank = SEVERITY_ORDER.get(record.severity.lower(), 0)
            if sev_rank >= threshold:
                findings.append(record)

    findings.sort(key=lambda item: item.score, reverse=True)
    return [asdict(item) for item in findings]
