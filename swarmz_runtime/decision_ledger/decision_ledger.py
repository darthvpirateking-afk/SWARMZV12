# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
DecisionLedger – append-only record of agent decisions for auditability and governance.

Each entry captures the decision context (agent, action, rationale) and a status
so that operators can review what the system chose to do and why.
"""

import time
from typing import Any, Dict, List, Optional


class DecisionLedger:
    """
    Append-only ledger that records every decision made by SWARMZ agents.

    Entries are kept in-memory and exposed via :meth:`get_entries`.
    The ledger is intentionally write-once per entry to preserve audit integrity.
    """

    def __init__(self):
        self._entries: List[Dict[str, Any]] = []

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
        self._entries.append(entry)
        return entry

    def get_entries(self) -> List[Dict[str, Any]]:
        """Return all recorded decision entries (read-only copy)."""
        return list(self._entries)

    def get_entries_for_agent(self, agent: str) -> List[Dict[str, Any]]:
        """Return all entries recorded for a specific agent."""
        return [e for e in self._entries if e["agent"] == agent]

    def __len__(self) -> int:
        return len(self._entries)
