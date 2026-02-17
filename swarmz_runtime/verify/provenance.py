# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
import json
import hashlib
import os
from pathlib import Path
from typing import Dict, Any, Tuple

AUDIT_FILE = Path(__file__).resolve().parents[2] / "data" / "audit.jsonl"
SEAL_KEY_ENV = "SWARMZ_SEAL_KEY"


def _last_hash(path: Path = AUDIT_FILE) -> str:
    if not path.exists():
        return "0" * 64
    try:
        with path.open("r", encoding="utf-8") as f:
            last = None
            for line in f:
                if line.strip():
                    last = line
            if not last:
                return "0" * 64
            obj = json.loads(last)
            return obj.get("hash", "0" * 64)
    except Exception:
        return "0" * 64


def _hash_entry(entry: Dict[str, Any], prev_hash: str) -> str:
    body = dict(entry)
    body["prev_hash"] = prev_hash
    raw = json.dumps(body, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def append_audit(event: str, details: Dict[str, Any] | None = None, path: Path = AUDIT_FILE) -> Dict[str, Any]:
    details = details or {}
    path.parent.mkdir(parents=True, exist_ok=True)
    prev = _last_hash(path)
    entry = {
        "event": event,
        "details": details,
    }
    h = _hash_entry(entry, prev)
    seal_key = os.getenv(SEAL_KEY_ENV)
    if seal_key:
        entry["seal"] = hashlib.sha256((seal_key + h).encode("utf-8")).hexdigest()
    entry["prev_hash"] = prev
    entry["hash"] = h
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, separators=(",", ":")) + "\n")
    return entry


def verify_chain(path: Path = AUDIT_FILE) -> Tuple[bool, int]:
    if not path.exists():
        return True, 0
    count = 0
    prev = "0" * 64
    try:
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                obj = json.loads(line)
                expected = _hash_entry({k: v for k, v in obj.items() if k not in {"hash", "prev_hash", "seal"}}, prev)
                if obj.get("hash") != expected or obj.get("prev_hash") != prev:
                    return False, count
                prev = obj.get("hash", prev)
                count += 1
    except Exception:
        return False, count
    return True, count

