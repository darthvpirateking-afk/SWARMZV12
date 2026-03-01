"""
Governor (P0.4)

A central controller to enforce global limits on action frequency and concurrency.

Responsibilities:
- Rate-limit actions by category (e.g., max 1 `DEPLOY_MODEL` per minute).
- Limit the total number of concurrent `RUNNING` missions.
- Provide a simple, in-memory store for tracking timestamps and counts,
  potentially backed by a file for persistence across restarts.
"""

import time
from typing import Dict, List, Any, Optional
import json
from pathlib import Path


class Governor:
    """Enforces rate limits and concurrency controls."""

    def __init__(
        self, config_path: Optional[Path] = None, state_path: Optional[Path] = None
    ):
        self.rate_limits: Dict[str, Dict[str, int]] = {
            "default": {"limit": 10, "period": 60}  # Default: 10 actions per minute
        }
        self.concurrency_limit: int = 5

        # In-memory state
        self.action_timestamps: Dict[str, List[float]] = {}
        self.running_missions: int = 0

        self.state_path = state_path
        if config_path and config_path.exists():
            self._load_config(config_path)
        if self.state_path and self.state_path.exists():
            self._load_state()

    def _load_config(self, path: Path):
        """Load rate limit and concurrency rules from a JSON file."""
        try:
            config = json.loads(path.read_text())
            self.rate_limits.update(config.get("rate_limits", {}))
            self.concurrency_limit = config.get(
                "concurrency_limit", self.concurrency_limit
            )
        except (json.JSONDecodeError, FileNotFoundError):
            # Use defaults if config is invalid or not found
            pass

    def _load_state(self):
        """Load action timestamps from a state file for persistence."""
        if not self.state_path:
            return
        try:
            state = json.loads(self.state_path.read_text())
            self.action_timestamps = state.get("action_timestamps", {})
        except (json.JSONDecodeError, FileNotFoundError):
            self.action_timestamps = {}

    def _save_state(self):
        """Save the current action timestamps to the state file."""
        if not self.state_path:
            return
        try:
            state = {"action_timestamps": self.action_timestamps}
            self.state_path.write_text(json.dumps(state, indent=2))
        except IOError:
            # Fail silently if state cannot be saved
            pass

    def admit_action(self, action: Dict[str, Any]) -> bool:
        """
        Check if an action is allowed based on rate limits.

        Args:
            action: The action dictionary, which should have a 'type' key.

        Returns:
            True if the action is within limits, False otherwise.
        """
        action_type = action.get("type", "default")
        rule = self.rate_limits.get(action_type, self.rate_limits["default"])
        limit = rule["limit"]
        period = rule["period"]

        current_time = time.monotonic()

        # Get timestamps for this action type, creating entry if it doesn't exist
        timestamps = self.action_timestamps.setdefault(action_type, [])

        # Remove timestamps older than the defined period
        timestamps = [t for t in timestamps if current_time - t < period]

        # Check if the number of recent actions is below the limit
        if len(timestamps) < limit:
            timestamps.append(current_time)
            self.action_timestamps[action_type] = timestamps
            self._save_state()
            return True
        else:
            return False

    def check_concurrency(self, current_running: int) -> bool:
        """
        Check if a new mission can start based on the concurrency limit.

        Args:
            current_running: The current number of missions in the 'RUNNING' state.

        Returns:
            True if a new mission can start, False otherwise.
        """
        return current_running < self.concurrency_limit

    def mission_started(self):
        """Placeholder for more complex concurrency tracking if needed."""
        pass

    def mission_finished(self):
        """Placeholder for more complex concurrency tracking if needed."""
        pass


# Global instance for easy access, can be configured on startup.
governor = Governor()
