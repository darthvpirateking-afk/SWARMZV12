# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
from typing import Dict, Any
from datetime import datetime, timedelta


class CadenceEngine:
    def __init__(self):
        self.intervals = [3600, 21600, 86400, 259200, 604800, 2592000]

    def calculate_next_interval(self, mission: Dict[str, Any], success: bool) -> int:
        current_interval = mission.get("revisit_interval", 3600)

        if success:
            current_index = self._get_interval_index(current_interval)
            next_index = min(current_index + 1, len(self.intervals) - 1)
            return self.intervals[next_index]
        else:
            return 3600

    def _get_interval_index(self, interval: int) -> int:
        for i, val in enumerate(self.intervals):
            if interval <= val:
                return i
        return len(self.intervals) - 1

    def schedule_next_run(self, mission: Dict[str, Any], success: bool) -> datetime:
        next_interval = self.calculate_next_interval(mission, success)
        return datetime.now() + timedelta(seconds=next_interval)
