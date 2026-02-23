from __future__ import annotations

import subprocess

from backend.security.command_guard import evaluate_command
from backend.security.shell_linter import lint_shell_command, should_block


class CommandGuardBlocked(RuntimeError):
    pass


def run_shell_command(
    command: str,
    protectiveness: int,
    operator_approved: bool,
    mood: str | None = "calm",
    timeout_seconds: int = 120,
) -> subprocess.CompletedProcess:
    lint_findings = lint_shell_command(command)
    if should_block(lint_findings):
        reason = "; ".join(
            item.get("message", "Shell lint block") for item in lint_findings
        )
        raise CommandGuardBlocked(reason)

    if protectiveness >= 75 and not operator_approved:
        has_warning = any(item.get("severity") == "warning" for item in lint_findings)
        if has_warning:
            raise CommandGuardBlocked(
                "Awaiting operator approval due to shell lint warnings"
            )

    guard = evaluate_command(
        command=command,
        protectiveness=protectiveness,
        operator_approved=operator_approved,
        mood=mood,
    )

    action = guard.get("action")
    if action in {"BLOCK", "HOLD"}:
        raise CommandGuardBlocked(guard.get("reason", "Blocked by command guard"))

    return subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
        check=False,
    )
