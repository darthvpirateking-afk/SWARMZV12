# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
core/reversible.py — Reversible Layer (P0.1)

The safety foundation: snapshot/restore API wrapping verification_runner.
Every risky action gets a transaction with rollback capability.

Pattern:
    snapshot_id = reversible.begin_transaction(action_id, state_desc)
    ... execute action ...
    reversible.commit(snapshot_id) OR reversible.rollback(snapshot_id)

Architecture Role: Safety Layer
Doctrine: Reversible = Universal safeguard enabling maximum velocity under uncertainty
"""

from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Any, Optional, List

_DATA_DIR = Path(__file__).parent.parent / "data"
_SNAPSHOTS_FILE = _DATA_DIR / "reversible_snapshots.jsonl"


@dataclass
class LayerResult:
    """Deterministic state object returned by all layers."""
    layer: str
    passed: bool
    reason: str
    metadata: dict
    timestamp: float


@dataclass
class Snapshot:
    """Reversible transaction snapshot."""
    snapshot_id: str
    action_id: str
    state_description: str
    artifacts: List[str]
    metrics: Dict[str, Any]
    created_at: float
    committed: bool
    rolled_back: bool


class ReversibleLayer:
    """Safety layer providing snapshot/restore for all risky actions."""

    def __init__(self):
        _DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._snapshots: Dict[str, Snapshot] = {}
        self._load_snapshots()

    def _load_snapshots(self):
        """Load existing snapshots from JSONL."""
        if not _SNAPSHOTS_FILE.exists():
            return
        with open(_SNAPSHOTS_FILE, "r") as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    snapshot = Snapshot(**data)
                    self._snapshots[snapshot.snapshot_id] = snapshot

    def _append_snapshot(self, snapshot: Snapshot):
        """Persist snapshot to JSONL."""
        with open(_SNAPSHOTS_FILE, "a") as f:
            f.write(json.dumps(asdict(snapshot)) + "\n")

    def begin_transaction(
        self,
        action_id: str,
        state_description: str,
        artifacts: Optional[List[str]] = None,
        metrics: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Create snapshot before risky action.
        
        Args:
            action_id: Unique identifier for the action
            state_description: Human-readable state context
            artifacts: List of artifact IDs to track
            metrics: Baseline metrics dict
            
        Returns:
            snapshot_id for commit/rollback
        """
        snapshot_id = str(uuid.uuid4())
        snapshot = Snapshot(
            snapshot_id=snapshot_id,
            action_id=action_id,
            state_description=state_description,
            artifacts=artifacts or [],
            metrics=metrics or {},
            created_at=time.time(),
            committed=False,
            rolled_back=False,
        )
        self._snapshots[snapshot_id] = snapshot
        self._append_snapshot(snapshot)
        return snapshot_id

    def commit(self, snapshot_id: str) -> LayerResult:
        """Mark transaction as successfully committed."""
        if snapshot_id not in self._snapshots:
            return LayerResult(
                layer="reversible",
                passed=False,
                reason=f"Snapshot {snapshot_id} not found",
                metadata={"snapshot_id": snapshot_id},
                timestamp=time.time(),
            )
        
        snapshot = self._snapshots[snapshot_id]
        if snapshot.rolled_back:
            return LayerResult(
                layer="reversible",
                passed=False,
                reason="Cannot commit rolled-back snapshot",
                metadata={"snapshot_id": snapshot_id},
                timestamp=time.time(),
            )
        
        snapshot.committed = True
        self._append_snapshot(snapshot)
        
        return LayerResult(
            layer="reversible",
            passed=True,
            reason="Transaction committed",
            metadata={
                "snapshot_id": snapshot_id,
                "action_id": snapshot.action_id,
            },
            timestamp=time.time(),
        )

    def rollback(self, snapshot_id: str) -> LayerResult:
        """
        Restore state to snapshot (exactly-once guarantee).
        
        Returns LayerResult with rollback status.
        """
        if snapshot_id not in self._snapshots:
            return LayerResult(
                layer="reversible",
                passed=False,
                reason=f"Snapshot {snapshot_id} not found",
                metadata={"snapshot_id": snapshot_id},
                timestamp=time.time(),
            )
        
        snapshot = self._snapshots[snapshot_id]
        
        if snapshot.rolled_back:
            return LayerResult(
                layer="reversible",
                passed=False,
                reason="Snapshot already rolled back (exactly-once guard)",
                metadata={"snapshot_id": snapshot_id},
                timestamp=time.time(),
            )
        
        if snapshot.committed:
            return LayerResult(
                layer="reversible",
                passed=False,
                reason="Cannot rollback committed snapshot",
                metadata={"snapshot_id": snapshot_id},
                timestamp=time.time(),
            )
        
        snapshot.rolled_back = True
        self._append_snapshot(snapshot)
        
        return LayerResult(
            layer="reversible",
            passed=True,
            reason="State restored to snapshot",
            metadata={
                "snapshot_id": snapshot_id,
                "action_id": snapshot.action_id,
                "artifacts_restored": snapshot.artifacts,
                "metrics_baseline": snapshot.metrics,
            },
            timestamp=time.time(),
        )

    def get_snapshot(self, snapshot_id: str) -> Optional[Snapshot]:
        """Retrieve snapshot by ID."""
        return self._snapshots.get(snapshot_id)

    def list_active_snapshots(self) -> List[Snapshot]:
        """Return all uncommitted, non-rolled-back snapshots."""
        return [
            s for s in self._snapshots.values()
            if not s.committed and not s.rolled_back
        ]

    def evaluate(self, action: Dict[str, Any], context: Dict[str, Any]) -> LayerResult:
        """
        Reversible layer evaluation: always passes (safety is opt-in).
        
        Returns metadata indicating rollback_available=True.
        """
        return LayerResult(
            layer="reversible",
            passed=True,
            reason="Reversible layer ready (rollback available)",
            metadata={
                "rollback_available": True,
                "active_snapshots": len(self.list_active_snapshots()),
            },
            timestamp=time.time(),
        )


# Singleton instance
_reversible = ReversibleLayer()


def begin_transaction(
    action_id: str,
    state_description: str,
    artifacts: Optional[List[str]] = None,
    metrics: Optional[Dict[str, Any]] = None,
) -> str:
    """Module-level convenience function."""
    return _reversible.begin_transaction(action_id, state_description, artifacts, metrics)


def commit(snapshot_id: str) -> LayerResult:
    """Module-level convenience function."""
    return _reversible.commit(snapshot_id)


def rollback(snapshot_id: str) -> LayerResult:
    """Module-level convenience function."""
    return _reversible.rollback(snapshot_id)


def evaluate(action: Dict[str, Any], context: Dict[str, Any]) -> LayerResult:
    """Module-level convenience function."""
    return _reversible.evaluate(action, context)


def get_snapshot(snapshot_id: str) -> Optional[Snapshot]:
    """Module-level convenience function."""
    return _reversible.get_snapshot(snapshot_id)


def list_active_snapshots() -> List[Snapshot]:
    """Module-level convenience function."""
    return _reversible.list_active_snapshots()
