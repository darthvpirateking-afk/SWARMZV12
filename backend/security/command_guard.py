from __future__ import annotations

from backend.entity.mood_modifiers import apply_numeric_modifier

ALWAYS_BLOCK = [
    "rm -rf /",
    "dd if=",
    ":(){:|:&};:",
    "git push --force origin main",
    "DROP TABLE",
    "TRUNCATE",
    "format",
    "mkfs",
    "shred",
]

WARN_AND_CONFIRM = [
    "rm -rf",
    "git reset --hard",
    "git clean -fd",
    "chmod 777",
    "sudo rm",
    "truncate",
]


def evaluate_command(
    command: str,
    protectiveness: int,
    operator_approved: bool,
    mood: str | None = "calm",
) -> dict:
    for pattern in ALWAYS_BLOCK:
        if pattern in command:
            return {
                "action": "BLOCK",
                "reason": f"Hard block: '{pattern}'",
                "override": False,
            }

    sensitivity = int(apply_numeric_modifier(0, "dcg_sensitivity", mood))
    effective_protectiveness = max(0, min(100, protectiveness + sensitivity))

    for pattern in WARN_AND_CONFIRM:
        if pattern in command:
            if effective_protectiveness >= 60 and not operator_approved:
                return {
                    "action": "HOLD",
                    "reason": f"Awaiting approval: '{pattern}'",
                }
            if effective_protectiveness >= 85:
                return {
                    "action": "BLOCK",
                    "reason": "protectiveness too high",
                }

    return {"action": "ALLOW"}
