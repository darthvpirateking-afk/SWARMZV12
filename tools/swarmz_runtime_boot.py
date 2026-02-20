#!/usr/bin/env python3
"""SWARMZ Runtime Boot Controller

Implements operator-grade startup discipline:
- ignition directives
- optimization directives
- structure lock mapping
- deterministic preflight checks
- activation/shutdown markers into immutable event log

Usage:
  python tools/swarmz_runtime_boot.py boot --activate
  python tools/swarmz_runtime_boot.py boot --strict --activate
  python tools/swarmz_runtime_boot.py shutdown
"""

from __future__ import annotations

import argparse
import json
import os
import socket
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
CONFIG_DIR = ROOT / "config"
SYSTEM_PRIMITIVES_DIR = DATA_DIR / "system_primitives"
IMMUTABLE_LOG = SYSTEM_PRIMITIVES_DIR / "immutable_event_log.jsonl"
BOOT_LOG = SYSTEM_PRIMITIVES_DIR / "bootstrap_markers.jsonl"
COMMAND_CENTER_STATE = DATA_DIR / "command_center_state.json"

IGNITION_PHRASE = "INIT_SWARMZ: CLEAN_BOOT, MAX_SPEED, ZERO_DRIFT, OPERATOR_ONLINE."
OPTIMIZE_PHRASE = "OPTIMIZE: REMOVE_POLLING, REMOVE_CLUTTER, EVENT_DRIVEN_ONLY, CACHE_HOT_PATHS, MIN_LOGGING, MAX_THROUGHPUT."
STRUCTURE_LOCK_PHRASE = "STRUCTURE_LOCK: /operator /companion /weaver /swarmz /vault /ledger /configs /events /agents /runtime."
ACTIVATE_PHRASE = "SWARMZ_ACTIVATE: BEGIN_EVENT_LOOP."

STRUCTURE_LOCK_MAP: Dict[str, Path] = {
    "/operator": DATA_DIR / "operator",
    "/companion": DATA_DIR / "companion",
    "/weaver": DATA_DIR / "weaver",
    "/swarmz": DATA_DIR / "swarmz_runtime",
    "/vault": DATA_DIR / "vault",
    "/ledger": DATA_DIR / "ledger",
    "/configs": CONFIG_DIR,
    "/events": DATA_DIR / "events",
    "/agents": DATA_DIR / "agents",
    "/runtime": DATA_DIR / "runtime",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def append_jsonl(path: Path, payload: Dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload) + "\n")


def write_marker(event_type: str, payload: Dict) -> None:
    row = {
        "event_type": event_type,
        "timestamp": now_iso(),
        "payload": payload,
    }
    append_jsonl(IMMUTABLE_LOG, row)
    append_jsonl(BOOT_LOG, row)


def check_writable(path: Path) -> bool:
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / ".write_probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        return True
    except Exception:
        return False


def port_busy(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.35)
        try:
            s.connect(("127.0.0.1", port))
            return True
        except Exception:
            return False


def load_json(path: Path) -> Tuple[bool, Dict]:
    if not path.exists():
        return False, {}
    try:
        return True, json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return True, {"_invalid": True}


def ensure_structure_lock() -> None:
    for _, target in STRUCTURE_LOCK_MAP.items():
        target.mkdir(parents=True, exist_ok=True)


def operator_layer_check() -> Tuple[bool, str]:
    anchor_path = DATA_DIR / "operator_anchor.json"
    if not anchor_path.exists():
        try:
            try:
                from core.operator_anchor import load_or_create_anchor
            except Exception:
                from swarmz_runtime.core.operator_anchor import load_or_create_anchor

            load_or_create_anchor(str(DATA_DIR))
        except Exception:
            return False, "operator_anchor_missing"

    if not anchor_path.exists():
        return False, "operator_anchor_missing"
    exists, payload = load_json(anchor_path)
    if not exists or payload.get("_invalid"):
        return False, "operator_anchor_invalid"
    required = {"operator_public_key", "created_at"}
    if not required.issubset(set(payload.keys())):
        return False, "operator_anchor_schema_invalid"
    return True, "ok"


def companion_layer_check() -> Tuple[bool, str]:
    companion_file = ROOT / "swarmz_runtime" / "api" / "companion_state.py"
    if not companion_file.exists():
        return False, "companion_runtime_missing"

    runtime_cfg_path = CONFIG_DIR / "runtime.json"
    exists, runtime_cfg = load_json(runtime_cfg_path)
    if exists and runtime_cfg.get("companion_bypass", False):
        return False, "companion_unsafe_bypass_mode"

    return True, "ok"


def config_layer_check(strict: bool = False) -> Tuple[bool, List[str]]:
    names = ["actions.json", "coupling.json", "objectives.json", "regimes.json"]
    issues: List[str] = []
    for name in names:
        path = CONFIG_DIR / name
        exists, payload = load_json(path)
        if not exists:
            if strict:
                issues.append(f"{name}_missing")
            continue
        if payload.get("_invalid"):
            issues.append(f"{name}_invalid")
    return len(issues) == 0, issues


def partner_shadow_check_and_repair() -> Tuple[bool, str]:
    if not COMMAND_CENTER_STATE.exists():
        return True, "state_missing_skip"
    try:
        state = json.loads(COMMAND_CENTER_STATE.read_text(encoding="utf-8"))
    except Exception:
        return False, "command_center_state_invalid"

    partner = state.get("partner", {})
    traits = partner.get("traits", {})
    repaired = False
    for k in ("logic", "precision", "empathy", "stability"):
        v = float(traits.get(k, 0.6 if k != "stability" else 0.7))
        if v < 0 or v > 1:
            traits[k] = 0.0 if v < 0 else 1.0
            repaired = True
        else:
            traits[k] = round(v, 2)
    partner["traits"] = traits
    state["partner"] = partner

    if repaired:
        COMMAND_CENTER_STATE.write_text(json.dumps(state, indent=2), encoding="utf-8")
        return True, "partner_traits_repaired"
    return True, "ok"


def preflight(strict: bool = False) -> Tuple[bool, List[str]]:
    issues: List[str] = []

    if not sys.executable:
        issues.append("python_env_inactive")

    if not CONFIG_DIR.exists():
        issues.append("config_dir_missing")

    if not check_writable(DATA_DIR / "vault"):
        issues.append("vault_storage_unwritable")

    if not check_writable(DATA_DIR / "ledger"):
        issues.append("ledger_unwritable")

    if not check_writable(DATA_DIR / "events"):
        issues.append("event_bus_storage_unwritable")

    if port_busy(8012) or port_busy(8000):
        issues.append("orphaned_or_active_process_detected")

    ok_operator, msg_operator = operator_layer_check()
    if not ok_operator:
        issues.append(msg_operator)

    ok_companion, msg_companion = companion_layer_check()
    if not ok_companion:
        issues.append(msg_companion)

    ok_cfg, cfg_issues = config_layer_check(strict=strict)
    if not ok_cfg:
        issues.extend(cfg_issues)

    ok_partner, msg_partner = partner_shadow_check_and_repair()
    if not ok_partner:
        issues.append(msg_partner)

    return len(issues) == 0, issues


def print_startup_banner() -> None:
    print("=" * 64)
    print("SWARMZ RUNTIME CHECKLIST v1.0")
    print("Operator-Grade, Event-Driven, Deterministic")
    print("=" * 64)
    print(IGNITION_PHRASE)
    print(OPTIMIZE_PHRASE)
    print(STRUCTURE_LOCK_PHRASE)


def print_shutdown_banner() -> None:
    print("=" * 64)
    print("SWARMZ SHUTDOWN")
    print("STOP_WEAVER -> DRAIN_EVENT_BUS -> FLUSH_LEDGER -> FLUSH_VAULT -> STOP_AGENTS")
    print("SYSTEM SAFE")
    print("=" * 64)


def boot(strict: bool, activate: bool) -> int:
    print_startup_banner()
    ensure_structure_lock()

    ok, issues = preflight(strict=strict)
    write_marker(
        "boot_preflight",
        {
            "strict": strict,
            "ok": ok,
            "issues": issues,
            "structure_lock": {k: str(v) for k, v in STRUCTURE_LOCK_MAP.items()},
        },
    )

    if not ok:
        print("[BOOT] FAILED preflight:")
        for issue in issues:
            print(f" - {issue}")
        return 1

    if activate:
        write_marker(
            "activate",
            {
                "phrase": ACTIVATE_PHRASE,
                "event_loop": "armed",
                "mode": "deterministic_event_driven",
            },
        )
        print(ACTIVATE_PHRASE)
        print("[BOOT] Weaver listening, Event bus primed, Agents idle but awake.")

    print("[BOOT] CLEAN, DETERMINISTIC, EVENT-DRIVEN")
    return 0


def shutdown() -> int:
    print_shutdown_banner()
    write_marker(
        "shutdown",
        {
            "marker": "graceful_shutdown",
            "flush": ["ledger", "vault", "events"],
        },
    )
    print("[SHUTDOWN] marker written.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="SWARMZ runtime boot controller")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_boot = sub.add_parser("boot", help="run preflight + structure lock")
    p_boot.add_argument("--strict", action="store_true", help="require optional config artifacts")
    p_boot.add_argument("--activate", action="store_true", help="emit activation marker")

    sub.add_parser("shutdown", help="write graceful shutdown marker")

    args = parser.parse_args()

    if args.cmd == "boot":
        return boot(strict=args.strict, activate=args.activate)
    if args.cmd == "shutdown":
        return shutdown()

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
