from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

DEFAULT_REGISTRY_PATH = Path("nexusmon/workers/registry.json")


def _normalize_registry(payload: Any) -> Dict[str, Any]:
    if isinstance(payload, list):
        return {"workers": payload}
    if isinstance(payload, dict):
        workers = payload.get("workers", payload.get("entries", []))
        if isinstance(workers, list):
            return {"workers": workers}
    raise ValueError("registry must be a JSON list or object with a workers list")


def load_registry(path: Path | str = DEFAULT_REGISTRY_PATH) -> Dict[str, Any]:
    registry_path = Path(path)
    data = json.loads(registry_path.read_text(encoding="utf-8"))
    return _normalize_registry(data)


def list_workers(path: Path | str = DEFAULT_REGISTRY_PATH) -> List[Dict[str, Any]]:
    return list(load_registry(path)["workers"])


def get_worker(worker_id: str, path: Path | str = DEFAULT_REGISTRY_PATH) -> Dict[str, Any]:
    for worker in list_workers(path):
        if str(worker.get("id", "")).strip() == worker_id:
            return worker
    raise KeyError(f"worker not found: {worker_id}")
