from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any
import json


@dataclass
class CheatEntry:
    tool: str
    title: str
    command: str
    tags: list[str]
    context: str
    notes: str = ""


CHEAT_DB = [
    CheatEntry(
        tool="nmap",
        title="Service version + script scan",
        command="nmap -sV -sC -p {ports} {target}",
        tags=["recon", "network", "service"],
        context="After discovering open ports, enumerate versions",
    ),
    CheatEntry(
        tool="sqlmap",
        title="POST parameter injection with tamper",
        command="sqlmap -u {url} --data='{post_data}' --tamper=space2comment -v 3",
        tags=["web", "sqli", "bypass", "waf"],
        context="When WAF blocks basic sqlmap, use tamper bypasses.",
    ),
    CheatEntry(
        tool="ffuf",
        title="Directory fuzzing with common wordlist",
        command="ffuf -w /usr/share/wordlists/common.txt -u {target}/FUZZ -mc 200,301,302",
        tags=["web", "fuzz", "recon"],
        context="Fast directory discovery",
    ),
]


def get_relevant_cheats(context: dict[str, Any], curiosity: int, patience: int) -> list[CheatEntry]:
    active_tags = context.get("services", []) + [context.get("phase", "")] + context.get("open_ports_labels", [])

    relevant = [entry for entry in CHEAT_DB if any(tag in active_tags for tag in entry.tags)]

    if curiosity >= 65:
        relevant = CHEAT_DB + [item for item in relevant if item not in CHEAT_DB]

    limit = 3 if patience < 40 else 8 if patience < 70 else 20
    return relevant[:limit]


def get_cheatsheet_config(curiosity: int, patience: int) -> dict[str, Any]:
    return {
        "enabled": curiosity >= 25,
        "auto_surface_on_tool": curiosity >= 40,
        "surface_in_cockpit": True,
        "operator_can_add": True,
        "nexusmon_can_add": curiosity >= 65,
        "context_aware": True,
        "max_suggestions": 3 if patience < 40 else 8,
        "cheatsheet_dir": "/data/cheatsheets",
    }


def load_operator_cheatsheet(path: str = "data/cheatsheets/custom.json") -> list[CheatEntry]:
    source = Path(path)
    if not source.exists():
        return []
    rows = json.loads(source.read_text(encoding="utf-8"))
    return [CheatEntry(**row) for row in rows if isinstance(row, dict)]


def cheats_as_dict(entries: list[CheatEntry]) -> list[dict[str, Any]]:
    return [asdict(entry) for entry in entries]
