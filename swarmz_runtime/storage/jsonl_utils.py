"""
jsonl_utils.py – Robust JSONL read/write utilities for SWARMZ storage.

Guarantees:
  * Blank/whitespace-only lines are silently skipped on read.
  * Malformed JSON lines are quarantined (logged, never crash).
  * Missing files are treated as empty collections (never crash).
  * Writes always end with a newline.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List


def read_jsonl(path: str | Path) -> List[Dict[str, Any]]:
    """Read a JSONL file, skipping blank lines and quarantining bad rows.

    Returns a list of successfully parsed dicts.
    Never raises on missing file or malformed content.
    """
    path = Path(path)
    if not path.exists():
        return []

    records: List[Dict[str, Any]] = []
    quarantined_lines: List[str] = []

    try:
        with open(path, "r", encoding="utf-8") as fh:
            for lineno, raw in enumerate(fh, start=1):
                line = raw.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except (json.JSONDecodeError, ValueError):
                    quarantined_lines.append(f"line {lineno}: {line}")
    except OSError:
        return []

    if quarantined_lines:
        _quarantine_log(path, quarantined_lines)

    return records


def write_jsonl(path: str | Path, records: List[Dict[str, Any]]) -> None:
    """Overwrite a JSONL file with *records* (one JSON object per line).

    Creates parent directories if needed.  Never raises on missing dirs.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, default=str) + "\n")


def append_jsonl(path: str | Path, record: Dict[str, Any]) -> None:
    """Append a single record to a JSONL file.

    Creates parent directories and the file if needed.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, default=str) + "\n")


def _quarantine_log(path: Path, lines: List[str]) -> None:
    """Log quarantined lines to a sidecar .quarantine file."""
    q_path = path.with_suffix(path.suffix + ".quarantine")
    try:
        with open(q_path, "a", encoding="utf-8") as fh:
            fh.write(f"Skipped {len(lines)} malformed line(s) in {path}:\n")
            for entry in lines:
                fh.write(f"  {entry}\n")
    except OSError:
        pass  # best-effort
