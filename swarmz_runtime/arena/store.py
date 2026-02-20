"""
arena/store.py – JSONL-backed storage for arena runs and candidates.

Uses the same robust JSONL utilities as the rest of SWARMZ.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, List, Optional

from swarmz_runtime.storage.jsonl_utils import read_jsonl, append_jsonl, write_jsonl


class ArenaStore:
    """Persist arena runs and candidates to JSONL files."""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.runs_file = self.data_dir / "arena_runs.jsonl"
        self.candidates_file = self.data_dir / "arena_candidates.jsonl"

    # ── Runs ─────────────────────────────────────────────────────────

    def save_run(self, run: Dict[str, Any]) -> None:
        append_jsonl(self.runs_file, run)

    def update_run(self, run_id: str, updates: Dict[str, Any]) -> None:
        runs = read_jsonl(self.runs_file)
        for r in runs:
            if isinstance(r, dict) and r.get("id") == run_id:
                r.update(updates)
        write_jsonl(self.runs_file, runs)

    def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        for r in read_jsonl(self.runs_file):
            if isinstance(r, dict) and r.get("id") == run_id:
                return r
        return None

    def list_runs(self, limit: int = 50) -> List[Dict[str, Any]]:
        runs = read_jsonl(self.runs_file)
        rows = [row for row in runs if isinstance(row, dict)]
        return rows[-limit:]

    # ── Candidates ───────────────────────────────────────────────────

    def save_candidate(self, candidate: Dict[str, Any]) -> None:
        append_jsonl(self.candidates_file, candidate)

    def update_candidate(self, candidate_id: str, updates: Dict[str, Any]) -> None:
        cands = read_jsonl(self.candidates_file)
        for c in cands:
            if isinstance(c, dict) and c.get("id") == candidate_id:
                c.update(updates)
        write_jsonl(self.candidates_file, cands)

    def get_candidates_for_run(self, run_id: str) -> List[Dict[str, Any]]:
        return [
            c for c in read_jsonl(self.candidates_file)
            if isinstance(c, dict) and c.get("run_id") == run_id
        ]

    def get_candidate(self, candidate_id: str) -> Optional[Dict[str, Any]]:
        for c in read_jsonl(self.candidates_file):
            if isinstance(c, dict) and c.get("id") == candidate_id:
                return c
        return None
