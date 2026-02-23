from __future__ import annotations

import math
import re
from dataclasses import dataclass, asdict
from typing import Any


@dataclass
class SecretFinding:
    file_path: str
    line_number: int
    secret_type: str
    value_preview: str
    confidence: float
    commit_hash: str = ""


SECRET_PATTERNS = {
    "aws_access_key": r"AKIA[0-9A-Z]{16}",
    "private_key": r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----",
    "jwt_secret": r"['\"]secret['\"]:\s*['\"][a-zA-Z0-9+/]{20,}['\"]",
    "db_password": r"(password|passwd|pwd)\s*[=:]\s*['\"][^'\"]{8,}['\"]",
    "github_token": r"ghp_[a-zA-Z0-9]{36}",
    "stripe_key": r"sk_(live|test)_[a-zA-Z0-9]{24,}",
    "generic_api_key": r"(api_key|apikey|api-key)\s*[=:]\s*['\"][a-zA-Z0-9-_]{20,}['\"]",
}


def _preview_only(value: str) -> str:
    if not value:
        return "***"
    if len(value) <= 8:
        return "***"
    return f"{value[:4]}...{value[-4:]}"


def shannon_entropy(s: str) -> float:
    if not s:
        return 0.0
    freq = {c: s.count(c) / len(s) for c in set(s)}
    return -sum(p * math.log2(p) for p in freq.values())


def scan_file(path: str, content: str, curiosity: int, aggression: int) -> list[SecretFinding]:
    findings: list[SecretFinding] = []

    for secret_type, pattern in SECRET_PATTERNS.items():
        for match in re.finditer(pattern, content, re.IGNORECASE):
            value = match.group(0)
            findings.append(
                SecretFinding(
                    file_path=path,
                    line_number=content[: match.start()].count("\n") + 1,
                    secret_type=secret_type,
                    value_preview=_preview_only(value),
                    confidence=0.9,
                )
            )

    if curiosity >= 60:
        for line_num, line in enumerate(content.split("\n"), 1):
            for token in line.split():
                if len(token) >= 20 and shannon_entropy(token) > 4.5:
                    findings.append(
                        SecretFinding(
                            file_path=path,
                            line_number=line_num,
                            secret_type="high_entropy_string",
                            value_preview=_preview_only(token),
                            confidence=0.6,
                        )
                    )

    return findings


def scan_file_dict(path: str, content: str, curiosity: int, aggression: int) -> list[dict[str, Any]]:
    return [asdict(item) for item in scan_file(path, content, curiosity, aggression)]


def get_scanner_config(curiosity: int, aggression: int) -> dict[str, Any]:
    return {
        "enabled": aggression >= 15,
        "scan_on_file_access": True,
        "entropy_analysis": curiosity >= 60,
        "scan_git_history": curiosity >= 70,
        "dep_vuln_scan": curiosity >= 50,
        "immediate_alert": True,
        "feed_to_report": True,
    }
