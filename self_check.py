#!/usr/bin/env python3
"""
SWARMZ Self-Check — deterministic validation that returns exit code 0 when healthy.

Validates: imports, core system, addons modules, config, schema version,
and runs a quick smoke test of key addon features.
"""

import json
import os
import sys
import traceback
from pathlib import Path

# Ensure repo root is on path
sys.path.insert(0, str(Path(__file__).parent))

CHECKS_PASSED = 0
CHECKS_FAILED = 0


def check(name: str, fn):
    global CHECKS_PASSED, CHECKS_FAILED
    try:
        result = fn()
        if result:
            print(f"  [PASS] {name}")
            CHECKS_PASSED += 1
        else:
            print(f"  [FAIL] {name}")
            CHECKS_FAILED += 1
    except Exception as e:
        print(f"  [FAIL] {name}: {e}")
        CHECKS_FAILED += 1


def main() -> int:
    global CHECKS_PASSED, CHECKS_FAILED
    print("=" * 60)
    print("SWARMZ Self-Check")
    print("=" * 60)

    # ── 1. Core imports ──────────────────────────────────────────
    print("\n[1] Core imports")
    check("import swarmz", lambda: __import__("swarmz") is not None)
    check("import swarmz_cli", lambda: __import__("swarmz_cli") is not None)

    # ── 2. Core system ───────────────────────────────────────────
    print("\n[2] Core system")
    from swarmz import SwarmzCore
    core = SwarmzCore()
    check("SwarmzCore init", lambda: core is not None)
    check("echo task", lambda: core.execute("echo", message="selfcheck") == "Echo: selfcheck")
    check("system_info", lambda: "platform" in core.execute("system_info"))
    check("capabilities", lambda: len(core.list_capabilities()) >= 3)
    check("audit log", lambda: isinstance(core.get_audit_log(), list))

    # ── 3. Addon imports ─────────────────────────────────────────
    print("\n[3] Addon imports")
    addon_modules = [
        "addons.config_ext",
        "addons.auth_gate",
        "addons.rate_limiter",
        "addons.schema_version",
        "addons.encrypted_storage",
        "addons.backup",
        "addons.replay",
        "addons.quarantine",
        "addons.budget",
        "addons.causal_ledger",
        "addons.strategy_registry",
        "addons.drift_scanner",
        "addons.entropy_budget",
        "addons.operator_contract",
        "addons.approval_queue",
        "addons.pack_artifacts",
        "addons.swarm_protocol",
        "addons.memory_boundaries",
        "addons.golden_run",
        "addons.guardrails",
    ]
    for mod in addon_modules:
        check(f"import {mod}", lambda m=mod: __import__(m) is not None)

    # ── 4. Config ────────────────────────────────────────────────
    print("\n[4] Config")
    from addons.config_ext import load_addon_config
    cfg = load_addon_config()
    check("config loads", lambda: isinstance(cfg, dict))
    check("schema_version default", lambda: cfg.get("schema_version") == 1)
    check("rate_limit default", lambda: cfg.get("rate_limit_per_minute") == 120)

    # ── 5. Schema version ────────────────────────────────────────
    print("\n[5] Schema versioning")
    from addons.schema_version import CURRENT_SCHEMA_VERSION
    check("schema version defined", lambda: CURRENT_SCHEMA_VERSION >= 1)

    # ── 6. Encrypted storage ─────────────────────────────────────
    print("\n[6] Encrypted storage")
    from addons.encrypted_storage import encrypt_blob, decrypt_blob
    blob = encrypt_blob(b"hello swarmz", "testkey")
    check("encrypt+decrypt roundtrip", lambda: decrypt_blob(blob, "testkey") == b"hello swarmz")

    # ── 7. Swarm protocol ────────────────────────────────────────
    print("\n[7] Swarm protocol")
    from addons.swarm_protocol import SwarmPacket, PacketBus
    pkt = SwarmPacket("agent_a", "agent_b", "intent", intent="test")
    bus = PacketBus()
    bus.send(pkt)
    check("packet roundtrip", lambda: len(bus.receive("agent_b")) == 1)
    check("packet type validation", lambda: pkt.packet_type == "intent")

    # ── 8. Memory boundaries ─────────────────────────────────────
    print("\n[8] Memory boundaries")
    from addons.memory_boundaries import put, get, list_keys
    put("skills", "_selfcheck", "ok")
    check("memory put+get", lambda: get("skills", "_selfcheck") == "ok")
    check("memory list_keys", lambda: "_selfcheck" in list_keys("skills"))

    # ── 9. Budget ────────────────────────────────────────────────
    print("\n[9] Budget")
    from addons.budget import get_budget, simulate_burn
    check("budget loads", lambda: isinstance(get_budget(), dict))
    sim = simulate_burn(1.0)
    check("burn sim", lambda: "would_breach" in sim)

    # ── 10. Operator contract ────────────────────────────────────
    print("\n[10] Operator contract")
    from addons.operator_contract import get_active_contract, validate_action
    contract = get_active_contract()
    check("contract loads", lambda: "version" in contract)
    check("action validation", lambda: validate_action("create_mission").get("allowed") is True)

    # ── 11. Quarantine ───────────────────────────────────────────
    print("\n[11] Quarantine")
    from addons.quarantine import get_quarantine_status
    check("quarantine status", lambda: "quarantined" in get_quarantine_status())

    # ── 12. Guardrails ───────────────────────────────────────────
    print("\n[12] Guardrails (Bucket B)")
    from addons.guardrails import (
        record_baseline, record_pressure, record_interference,
        stability_check, record_silence, should_avoid
    )
    check("baseline recording", lambda: "delta" in record_baseline("test", 1.0, 1.5))
    check("pressure recording", lambda: "pressure_score" in record_pressure("test", 100.0, 200.0))
    check("interference recording", lambda: "effect" in record_interference("A", "B", -0.5))
    check("stability check", lambda: "stable" in stability_check("test", {"a": 1}, [{"a": 1}, {"a": 1}]))
    check("silence recording", lambda: "signal" in record_silence("week1", "revenue"))
    check("negative zone avoidance", lambda: isinstance(should_avoid("test_zone"), bool))

    # ── 13. Red-team basic ───────────────────────────────────────
    print("\n[13] Red-team basics")
    check("reject unknown task", lambda: _expect_error(lambda: core.execute("nonexistent_task")))
    check("encrypted tamper detection", lambda: _expect_error(
        lambda: decrypt_blob(encrypt_blob(b"data", "key1"), "wrong_key")
    ))

    # ── Summary ──────────────────────────────────────────────────
    total = CHECKS_PASSED + CHECKS_FAILED
    print("\n" + "=" * 60)
    print(f"Self-Check: {CHECKS_PASSED}/{total} passed, {CHECKS_FAILED} failed")
    print("=" * 60)

    if CHECKS_FAILED == 0:
        print("STATUS: HEALTHY ✓")
        return 0
    else:
        print("STATUS: UNHEALTHY ✗")
        return 1


def _expect_error(fn) -> bool:
    try:
        fn()
        return False
    except Exception:
        return True


if __name__ == "__main__":
    sys.exit(main())
