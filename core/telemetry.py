import logging
import time
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List
from threading import Lock

# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.

"""
core/telemetry.py — Metadata-heavy logging system for NEXUSMON.

This module provides a unified logging interface that captures rich metadata
for every system event, facilitating audit trails and Sovereign integration.
"""


@dataclass
class LogEntry:
    """Represents a single telemetry event with rich metadata."""

    timestamp: float
    level: str  # INFO, WARNING, ERROR, CRITICAL
    component: str
    message: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert entry to a dictionary for JSON serialization."""
        return asdict(self)


class TelemetrySystem:
    """
    Main telemetry engine for NEXUSMON.

    Wraps the standard logging module to ensure metadata is captured.
    Stores recent logs in a JSON-serializable list and persists to disk.
    """

    def __init__(
        self, max_recent_logs: int = 500, persist_path: str = "data/telemetry.jsonl"
    ):
        self.max_recent_logs = max_recent_logs
        self.recent_logs: List[LogEntry] = []
        self.persist_path = Path(persist_path)
        self._lock = Lock()

        # Ensure data directory exists
        self.persist_path.parent.mkdir(parents=True, exist_ok=True)

        # Configure standard logging to integrate with TelemetrySystem
        self.logger = logging.getLogger("NEXUSMON.telemetry")
        self.logger.setLevel(logging.INFO)

    def log_action(self, level: str, component: str, message: str, **metadata):
        """
        Log an action with full metadata context.
        """
        entry = LogEntry(
            timestamp=time.time(),
            level=level.upper(),
            component=component,
            message=message,
            metadata=metadata,
        )

        # Thread-safe storage for cockpit consumption
        with self._lock:
            self.recent_logs.append(entry)
            if len(self.recent_logs) > self.max_recent_logs:
                self.recent_logs.pop(0)

        # Persist to JSONL for audit trail
        try:
            import json

            with open(self.persist_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry.to_dict()) + "\n")
        except Exception:
            pass

        # Map string level to logging constants
        log_level_map = {
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
        }
        numeric_level = log_level_map.get(level.upper(), logging.INFO)

        # Standard Logging Integration
        self.logger.log(
            numeric_level,
            f"[{component}] {message}",
            extra={"component": component, "metadata": metadata},
        )

    def log_escalation(self, component: str, rule_name: str, reason: str, **metadata):
        """
        Specialized escalation logging for Sovereign integration.

        This method ensures high-priority visibility for governance overrides and
        policy escalations.
        """
        escalation_metadata = {
            "rule_name": rule_name,
            "reason": reason,
            "integration_layer": "SovereignCore",
            "escalation_event": True,
            **metadata,
        }
        self.log_action(
            "CRITICAL",
            component,
            f"GOVERNANCE ESCALATION: Rule '{rule_name}' triggered. Reason: {reason}",
            **escalation_metadata,
        )

    def get_recent_logs(self) -> List[Dict[str, Any]]:
        """Return the current log cache as a list of dictionaries for JSON serialization."""
        with self._lock:
            return [log.to_dict() for log in self.recent_logs]

    def clear(self):
        """Wipe the in-memory log buffer."""
        with self._lock:
            self.recent_logs.clear()


# Default singleton instance for global access within the NEXUSMON workspace
telemetry = TelemetrySystem()
