# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
Persistent Memory Boundaries â€” small JSON stores for the commander/verifier loop.

  skills.json, failures.json, preferences.json
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from addons.config_ext import get_config

_STORES = ("skills", "failures", "preferences")


def _memory_dir() -> Path:
    cfg = get_config()
    d = Path(cfg.get("memory_dir", "addons/data/memory"))
    d.mkdir(parents=True, exist_ok=True)
    return d


def _store_path(store: str) -> Path:
    if store not in _STORES:
        raise ValueError(f"Unknown store: {store}. Must be one of {_STORES}")
    return _memory_dir() / f"{store}.json"


def _load_store(store: str) -> Dict[str, Any]:
    p = _store_path(store)
    if p.exists():
        try:
            return json.loads(p.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {"entries": {}}


def _save_store(store: str, data: Dict[str, Any]) -> None:
    _store_path(store).write_text(json.dumps(data, indent=2))


def put(store: str, key: str, value: Any) -> Dict[str, Any]:
    data = _load_store(store)
    data["entries"][key] = {
        "value": value,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    _save_store(store, data)
    return {"status": "ok", "store": store, "key": key}


def get(store: str, key: str) -> Optional[Any]:
    data = _load_store(store)
    entry = data.get("entries", {}).get(key)
    return entry["value"] if entry else None


def list_keys(store: str) -> List[str]:
    data = _load_store(store)
    return list(data.get("entries", {}).keys())


def delete(store: str, key: str) -> Dict[str, Any]:
    data = _load_store(store)
    if key in data.get("entries", {}):
        del data["entries"][key]
        _save_store(store, data)
        return {"status": "deleted", "store": store, "key": key}
    return {"status": "not_found"}


def dump_store(store: str) -> Dict[str, Any]:
    return _load_store(store)
