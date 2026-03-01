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
        raise CommandGuardBlocked("Command blocked by shell linter")

    guard_verdict = evaluate_command(
        command=command,
        protectiveness=protectiveness,
        operator_approved=operator_approved,
        mood=mood,
    )
    if guard_verdict.get("action") in {"BLOCK", "HOLD"}:
        reason = guard_verdict.get("reason", "Command blocked by command guard")
        raise CommandGuardBlocked(reason)

    return subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
        check=False,
    )
