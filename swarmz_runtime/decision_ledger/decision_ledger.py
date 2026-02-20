# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
DecisionLedger – append-only record of agent decisions for auditability and governance.

Each entry captures the decision context (agent, action, rationale) and a status
so that operators can review what the system chose to do and why.

Entries are persisted to a JSONL file (data/audit_decisions.jsonl by default) so
the history survives restarts.  All public methods are thread-safe.
"""

import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from swarmz_runtime.storage.jsonl_utils import append_jsonl, read_jsonl


class DecisionLedger:
    """
    Append-only ledger that records every decision made by SWARMZ agents.

    Entries are persisted to ``ledger_file`` (JSONL format) and also cached
    in memory for fast in-process queries.  All methods are thread-safe.
    """

    DEFAULT_FILE = Path("data") / "audit_decisions.jsonl"

    def __init__(self, ledger_file: Optional[str | Path] = None):
        self._file = Path(ledger_file) if ledger_file else self.DEFAULT_FILE
        self._lock = threading.Lock()
        # Warm the in-memory cache from disk so queries work after a restart.
        with self._lock:
            self._entries: List[Dict[str, Any]] = list(read_jsonl(self._file))

    def record(
        self,
        agent: str,
        action: str,
        rationale: str = "",
        outcome: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Record a decision.

        Args:
            agent:     Name of the agent that made the decision.
            action:    The action or choice that was decided upon.
            rationale: Human-readable explanation of why this decision was made.
            outcome:   Optional post-hoc outcome tag (e.g. "success", "failed").
            metadata:  Arbitrary extra data to attach to the entry.

        Returns:
            The newly created ledger entry.
        """
        entry: Dict[str, Any] = {
            "timestamp": time.time(),
            "agent": agent,
            "action": action,
            "rationale": rationale,
            "outcome": outcome,
            "metadata": metadata or {},
        }
        with self._lock:
            self._entries.append(entry)
        append_jsonl(self._file, entry)
        return entry

    def get_entries(self) -> List[Dict[str, Any]]:
        """Return all recorded decision entries (read-only copy)."""
        with self._lock:
            return list(self._entries)

    def get_entries_for_agent(self, agent: str) -> List[Dict[str, Any]]:
        """Return all entries recorded for a specific agent."""
        with self._lock:
            return [e for e in self._entries if e["agent"] == agent]

    def __len__(self) -> int:
        with self._lock:
            return len(self._entries)
