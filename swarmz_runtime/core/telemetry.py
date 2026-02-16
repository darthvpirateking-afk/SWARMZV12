import json
import os
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, List

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

TELEMETRY_FILE = DATA_DIR / "telemetry.jsonl"
RUNTIME_METRICS_FILE = DATA_DIR / "runtime_metrics.jsonl"

_verbose = os.getenv("SWARMZ_VERBOSE", "0") not in {"0", "false", "False", None}
_lock = threading.Lock()


def set_verbose(enabled: bool) -> None:
    global _verbose
    _verbose = bool(enabled)


def verbose_log(*args: Any) -> None:
    if _verbose:
        print("[telemetry]", *args)


def _append(path: Path, obj: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(obj, separators=(",", ":"))
    with _lock:
        with path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")


def record_event(name: str, payload: Optional[Dict[str, Any]] = None) -> None:
    evt = {
        "ts": datetime.utcnow().isoformat() + "Z",
        "type": name,
        "payload": payload or {},
    }
    _append(TELEMETRY_FILE, evt)
    verbose_log("event", name, payload)


def record_duration(name: str, duration_ms: float, context: Optional[Dict[str, Any]] = None) -> None:
    evt = {
        "ts": datetime.utcnow().isoformat() + "Z",
        "type": name,
        "duration_ms": round(duration_ms, 3),
        "context": context or {},
    }
    _append(RUNTIME_METRICS_FILE, evt)
    verbose_log("duration", name, f"{duration_ms:.3f}ms", context)


def record_failure(name: str, error: str, context: Optional[Dict[str, Any]] = None) -> None:
    evt = {
        "ts": datetime.utcnow().isoformat() + "Z",
        "type": name,
        "error": error,
        "context": context or {},
    }
    _append(TELEMETRY_FILE, evt)
    verbose_log("failure", name, error, context)


def last_event() -> Optional[Dict[str, Any]]:
    if not TELEMETRY_FILE.exists():
        return None
    try:
        with TELEMETRY_FILE.open("rb") as f:
            f.seek(0, os.SEEK_END)
            pos = f.tell()
            buf = b""
            while pos > 0:
                pos -= 1
                f.seek(pos)
                ch = f.read(1)
                if ch == b"\n" and buf:
                    break
                buf = ch + buf
            if buf:
                return json.loads(buf.decode("utf-8"))
    except Exception:
        return None
    return None


def avg_duration(name: str, max_samples: int = 100) -> Optional[float]:
    if not RUNTIME_METRICS_FILE.exists():
        return None
    durations: List[float] = []
    try:
        with RUNTIME_METRICS_FILE.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    obj = json.loads(line)
                    if obj.get("type") == name and "duration_ms" in obj:
                        durations.append(float(obj["duration_ms"]))
                except Exception:
                    continue
                if len(durations) >= max_samples:
                    break
        if durations:
            return sum(durations) / len(durations)
    except Exception:
        return None
    return None
