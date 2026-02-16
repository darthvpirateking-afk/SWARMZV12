from typing import List, Dict, Any
from pathlib import Path
import json

from galileo.storage import ensure_storage, GALILEO_DATA_DIR


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    out: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except Exception:
                continue
    return out


def read_hypotheses() -> List[Dict[str, Any]]:
    ensure_storage()
    return _read_jsonl(GALILEO_DATA_DIR / "hypotheses.jsonl")


def read_experiments() -> List[Dict[str, Any]]:
    ensure_storage()
    return _read_jsonl(GALILEO_DATA_DIR / "experiments.jsonl")


def read_runs() -> List[Dict[str, Any]]:
    ensure_storage()
    return _read_jsonl(GALILEO_DATA_DIR / "runs.jsonl")
