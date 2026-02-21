# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
core/cold_start.py â€” Ensure minimum data files exist.

Called once at server startup.  Creates safe defaults for every data file
the engine layer expects.  NEVER overwrites a file that already contains
valid data â€” only fills gaps.
"""

import json
import hashlib
import platform
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _safe_write_json(path: Path, default: Dict[str, Any]) -> None:
    """Write *default* only if *path* is missing or empty / corrupt."""
    if path.exists():
        try:
            content = path.read_text(encoding="utf-8").strip()
            if content and json.loads(content):
                return  # already valid â€” do NOT overwrite
        except Exception:
            pass  # corrupt â€” overwrite with default
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(default, indent=2), encoding="utf-8")


def _safe_touch_jsonl(path: Path) -> None:
    """Create the JSONL file (empty) if it does not exist."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text("", encoding="utf-8")


def _safe_touch_text(path: Path, default_text: str = "") -> None:
    """Create a text file if it does not exist."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(default_text, encoding="utf-8")


def _safe_mkdir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


# â”€â”€ System identity â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


def _machine_fingerprint() -> str:
    """Bestâ€‘effort machine fingerprint (hash of platform info)."""
    parts = [
        platform.node(),
        platform.machine(),
        platform.system(),
        platform.processor(),
        os.environ.get("COMPUTERNAME", ""),
        os.environ.get("USERNAME", ""),
    ]
    return hashlib.sha256("|".join(parts).encode()).hexdigest()[:32]


def _ensure_system_identity() -> None:
    p = DATA_DIR / "system_identity.txt"
    if p.exists() and p.read_text(encoding="utf-8").strip():
        return
    lines = [
        f"birth_timestamp: {_now()}",
        f"machine_fingerprint: {_machine_fingerprint()}",
        f"platform: {platform.system()} {platform.release()}",
        f"python: {platform.python_version()}",
        "swarmz_version: 1.0.0",
        "operator_public_key: (pending anchor)",
    ]
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")


# â”€â”€ Ensure directories â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


def _ensure_dirs() -> None:
    for d in [
        DATA_DIR,
        DATA_DIR / "memory" / "hot",
        DATA_DIR / "memory" / "warm",
        DATA_DIR / "memory" / "cold",
        DATA_DIR / "memory" / "archive",
        DATA_DIR / "epochs",
        DATA_DIR / "galileo",
        ROOT / "prepared_actions",
        ROOT / "prepared_actions" / "messages",
        ROOT / "prepared_actions" / "schedules",
        ROOT / "prepared_actions" / "commands",
        ROOT / "prepared_actions" / "purchases",
        ROOT / "prepared_actions" / "preemptive",
        ROOT / "packs",
        ROOT / "config",
    ]:
        _safe_mkdir(d)


# â”€â”€ Ensure JSON data files â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


def _ensure_json_files() -> None:
    _safe_write_json(
        DATA_DIR / "state.json",
        {
            "mode": "COMPANION",
            "updated_at": _now(),
            "version": 1,
        },
    )
    _safe_write_json(
        DATA_DIR / "personality_vector.json",
        {
            "risk_tolerance": 0.5,
            "speed_preference": 0.5,
            "exploration_bias": 0.5,
            "retry_patience": 0.5,
        },
    )
    _safe_write_json(
        DATA_DIR / "companion_state.json",
        {
            "last_active_mission": None,
            "preferred_strategies": {},
            "recent_failures": [],
            "confidence_level": 0.5,
        },
    )
    _safe_write_json(
        DATA_DIR / "companion_memory.json",
        {
            "sessionId": "main_companion",
            "summary": "No interactions yet.",
            "preferences": {},
            "mission_outcomes": [],
            "learned_constraints": [],
            "version": 1,
            "updated_at": _now(),
        },
    )
    _safe_write_json(
        DATA_DIR / "companion_master.json",
        {
            "identity": "MASTER_SWARMZ",
            "personality_anchor": "calm_analytical",
            "created_at": _now(),
            "epochs_completed": 0,
            "total_missions_witnessed": 0,
            "last_insight": None,
        },
    )
    _safe_write_json(
        DATA_DIR / "future_state.json",
        {
            "north_star_description": "Reliable, adaptive operator companion",
            "time_horizon_days": 90,
            "priority_axes": {
                "stability": 0.7,
                "growth": 0.6,
                "optionality": 0.5,
                "recovery_capacity": 0.7,
            },
            "drift_tolerance": 0.1,
            "last_updated": _now(),
        },
    )
    _safe_write_json(
        DATA_DIR / "current_state.json",
        {
            "throughput": 0.0,
            "failure_rate": 0.0,
            "latency": 0.0,
            "resource_usage": 0.0,
            "strategy_variance": 0.0,
            "recent_trend_vector": 0.0,
        },
    )
    _safe_write_json(
        DATA_DIR / "state_of_life.json",
        {
            "time_allocation": {},
            "active_projects": 0,
            "financial_flow": {},
            "commitment_load": 0.0,
            "recent_outputs": 0,
            "idle_vs_execution_ratio": 0.0,
            "strategy_variance": 0.0,
            "trend_vector": 0.0,
            "last_updated": _now(),
        },
    )
    _safe_write_json(DATA_DIR / "commitments.json", {})
    _safe_write_json(
        DATA_DIR / "phase_patterns.json",
        {
            "failure_clusters": {"count": 0, "confidence": 0.0, "recent": []},
            "abandoned": {"count": 0, "confidence": 0.0, "recent": []},
            "slowdowns": {"count": 0, "confidence": 0.0, "recent": []},
            "recoveries": {"count": 0, "confidence": 0.0, "recent": []},
            "bursts": {"count": 0, "confidence": 0.0, "recent": []},
        },
    )
    _safe_write_json(DATA_DIR / "strategy_reliability.json", {})
    _safe_write_json(
        DATA_DIR / "uncertainty_profile.json",
        {
            "exploration_bias": 0.5,
            "confidence_level": 0.5,
            "uncertainty_weight": 0.5,
        },
    )


# â”€â”€ Ensure JSONL files â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


def _ensure_jsonl_files() -> None:
    for name in [
        "missions.jsonl",
        "audit.jsonl",
        "audit_ai.jsonl",
        "audit_decisions.jsonl",
        "perf_ledger.jsonl",
        "evolution_history.jsonl",
        "phase_history.jsonl",
        "phase_interventions.jsonl",
        "divergence_log.jsonl",
        "entropy_log.jsonl",
        "value_ledger.jsonl",
        "counterfactual_log.jsonl",
        "decision_snapshots.jsonl",
        "drift_log.jsonl",
        "lessons.jsonl",
        "runtime_metrics.jsonl",
        "telemetry.jsonl",
    ]:
        _safe_touch_jsonl(DATA_DIR / name)


# â”€â”€ Ensure text files â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


def _ensure_text_files() -> None:
    _safe_touch_text(DATA_DIR / "daily_brief.txt", "No daily brief yet.\n")
    _safe_touch_text(DATA_DIR / "reflection.txt", "No reflections yet.\n")
    _safe_touch_text(DATA_DIR / "phase_report.txt", "No phase report yet.\n")
    _safe_touch_text(DATA_DIR / "cognitive_load.txt", "No cognitive load data yet.\n")
    _safe_touch_text(
        DATA_DIR / "decision_quality_report.txt", "No decision quality report yet.\n"
    )


# â”€â”€ Public entry point â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


def ensure_cold_start() -> Dict[str, Any]:
    """Run all coldâ€‘start checks. Returns a summary dict.

    Safe to call multiple times â€” never overwrites valid data.
    """
    _ensure_dirs()
    _ensure_system_identity()
    _ensure_json_files()
    _ensure_jsonl_files()
    _ensure_text_files()

    return {
        "ok": True,
        "data_dir": str(DATA_DIR),
        "system_identity": str(DATA_DIR / "system_identity.txt"),
        "timestamp": _now(),
    }
