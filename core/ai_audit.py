# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
core/ai_audit.py â€” Structured AI audit trail for SWARMZ.

Two appendâ€‘only JSONL files:
  data/audit_ai.jsonl        â€” every model_router call (provider, tokens, latency, ok/err)
  data/audit_decisions.jsonl â€” every strategic decision (companion advice, mission plan, strategy pick)

Each entry carries a monotonic sequence number so ordering is unambiguous.
"""

import json
import threading
from pathlib import Path
from typing import Any, Dict, Optional

from core.time_source import now

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
AI_AUDIT_FILE = DATA_DIR / "audit_ai.jsonl"
DECISION_AUDIT_FILE = DATA_DIR / "audit_decisions.jsonl"

_seq_lock = threading.Lock()
_seq = 0


def _next_seq() -> int:
    global _seq
    with _seq_lock:
        _seq += 1
        return _seq


def _append(path: Path, obj: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(obj, separators=(",", ":"), default=str) + "\n"
    with open(path, "a", encoding="utf-8") as f:
        f.write(line)


def log_model_call(
    *,
    provider: str,
    model: str,
    ok: bool,
    latency_ms: int = 0,
    input_tokens: int = 0,
    output_tokens: int = 0,
    error: Optional[str] = None,
    context: str = "",
) -> None:
    """Record a modelâ€‘router call in data/audit_ai.jsonl."""
    _append(AI_AUDIT_FILE, {
        "seq": _next_seq(),
        "timestamp": now(),
        "event": "model_call",
        "provider": provider,
        "model": model,
        "ok": ok,
        "latency_ms": latency_ms,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "error": error,
        "context": context,
    })


def log_decision(
    *,
    decision_type: str,
    mission_id: str = "",
    strategy: str = "",
    inputs_hash: str = "",
    rationale: str = "",
    confidence: float = 0.0,
    source: str = "",
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    """Record a strategic decision in data/audit_decisions.jsonl."""
    entry: Dict[str, Any] = {
        "seq": _next_seq(),
        "timestamp": now(),
        "event": "decision",
        "decision_type": decision_type,
        "mission_id": mission_id,
        "strategy": strategy,
        "inputs_hash": inputs_hash,
        "rationale": rationale[:500],
        "confidence": round(confidence, 4),
        "source": source,
    }
    if extra:
        entry["extra"] = extra
    _append(DECISION_AUDIT_FILE, entry)


def tail_ai(limit: int = 50) -> list:
    """Return last *limit* entries from audit_ai.jsonl."""
    return _tail(AI_AUDIT_FILE, limit)


def tail_decisions(limit: int = 50) -> list:
    """Return last *limit* entries from audit_decisions.jsonl."""
    return _tail(DECISION_AUDIT_FILE, limit)


def _tail(path: Path, limit: int) -> list:
    if not path.exists():
        return []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except Exception:
        return []
    entries = []
    for line in lines[-limit:]:
        if not line.strip():
            continue
        try:
            entries.append(json.loads(line))
        except Exception:
            pass
    return entries

