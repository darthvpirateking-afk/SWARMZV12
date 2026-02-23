from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


@dataclass
class ShellLintFinding:
    code: str
    severity: str
    message: str


HIGH_RISK_TOKENS = {
    "SL001": "rm -rf /",
    "SL002": "curl | sh",
    "SL003": "wget | sh",
    "SL004": "mkfs",
    "SL005": "dd if=",
}

WARN_TOKENS = {
    "SL101": "sudo",
    "SL102": "chmod 777",
    "SL103": "--force",
}


def lint_shell_command(command: str) -> list[dict[str, Any]]:
    findings: list[ShellLintFinding] = []
    cmd = command or ""

    for code, token in HIGH_RISK_TOKENS.items():
        if token in cmd:
            findings.append(ShellLintFinding(code=code, severity="error", message=f"High-risk token detected: {token}"))

    for code, token in WARN_TOKENS.items():
        if token in cmd:
            findings.append(ShellLintFinding(code=code, severity="warning", message=f"Risky token detected: {token}"))

    if " && " in cmd:
        findings.append(ShellLintFinding(code="SL201", severity="warning", message="Command chaining can hide failing segments."))

    return [asdict(item) for item in findings]


def should_block(findings: list[dict[str, Any]]) -> bool:
    return any(item.get("severity") == "error" for item in findings)
