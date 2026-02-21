# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
import hashlib
import json
import platform
import secrets
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any
from zoneinfo import ZoneInfo

ANCHOR_FILENAME = "operator_anchor.json"


def _safe_run(cmd):
    try:
        return (
            subprocess.check_output(
                cmd, shell=True, stderr=subprocess.DEVNULL, timeout=2
            )
            .decode()
            .strip()
        )
    except Exception:
        return ""


def compute_machine_fingerprint() -> str:
    parts = []
    parts.append(platform.node())
    parts.append(platform.platform())
    parts.append(str(uuid.getnode()))
    parts.append(platform.uname().processor or "")
    env_cpu = [
        "PROCESSOR_IDENTIFIER",
        "PROCESSOR_ARCHITECTURE",
        "NUMBER_OF_PROCESSORS",
    ]
    import os  # local import to avoid heavy deps

    for key in env_cpu:
        parts.append(os.getenv(key, ""))

    disk_serial = _safe_run("wmic diskdrive get SerialNumber /value") or _safe_run(
        "lsblk -no SERIAL"
    )
    os_guid = _safe_run("wmic csproduct get UUID /value") or _safe_run(
        "cat /etc/machine-id"
    )
    parts.append(disk_serial)
    parts.append(os_guid)
    raw = "|".join(str(p) for p in parts if p is not None)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _generate_keys() -> Dict[str, str]:
    private_key = secrets.token_hex(32)
    public_key = hashlib.sha256(private_key.encode("utf-8")).hexdigest()
    return {"operator_private_key": private_key, "operator_public_key": public_key}


def load_or_create_anchor(data_dir: str = "data") -> Dict[str, Any]:
    path = Path(data_dir) / ANCHOR_FILENAME
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    data_dir_path = Path(data_dir)
    data_dir_path.mkdir(parents=True, exist_ok=True)
    keys = _generate_keys()
    anchor = {
        "machine_fingerprint": compute_machine_fingerprint(),
        "birth_timestamp": datetime.now(timezone.utc).isoformat() + "Z",
        **keys,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(anchor, f, indent=2)
    return anchor


def verify_fingerprint(anchor: Dict[str, Any]) -> bool:
    stored = anchor.get("machine_fingerprint")
    current = compute_machine_fingerprint()
    return bool(stored) and stored == current


def compute_record_hash(payload: Dict[str, Any], previous_hash: str) -> str:
    body = dict(payload)
    body["previous_hash"] = previous_hash
    raw = json.dumps(body, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def sign_record(private_key: str, record_hash: str) -> str:
    return hashlib.sha256((private_key + record_hash).encode("utf-8")).hexdigest()


def verify_signature(private_key: str, record_hash: str, signature: str) -> bool:
    expected = sign_record(private_key, record_hash)
    return secrets.compare_digest(expected, signature)
